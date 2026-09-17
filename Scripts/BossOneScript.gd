extends Node2D

#REFERENCES
var Projectile = preload("res://Scenes/Bosses/BossProjectileScene.tscn")
const HitStop := preload("res://Scripts/HitStop.gd")
const EricArtLayout := preload("res://Scripts/EricArtLayout.gd")
const FightOutro := preload("res://Scripts/FightOutro.gd")
# What he says once the fight is over, under player_won and player_lost.
const OUTRO_DIALOGUE := "res://Dialogue/EricOutro.dialogue"

#CONSTANTS
@export var max_health := 24
var boss_health := max_health

#UI (built at runtime - no new art needed)
var health_bar: ProgressBar
var name_label: Label
var fill_style: StyleBoxFlat

@onready var animationPlayer = $AnimationPlayer
@onready var sprite = $Sprite2D
@onready var state_machine = $StateManager
@export var post_dialogue_pre_fight_timer: Timer

#AUDIO
@onready var music_player: AudioStreamPlayer = $MusicPlayer
@onready var hit_sfx_player: AudioStreamPlayer = $HitSfxPlayer
@onready var victory_sfx_player: AudioStreamPlayer = $VictorySfxPlayer
var defeated := false
# One finisher daze per Downed window; Downed clears it.
var daze_used := false

var sprite_base_position: Vector2

# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	add_to_group(FightOutro.BOSS_GROUP)
	var hurtBox = get_node("Hurtbox")
	hurtBox.area_entered.connect(_on_hurtbox_entered)
	_apply_art_layout()

	sprite_base_position = sprite.position
	_build_health_bar()

	music_player.stream = load("res://Assets/Audio/Music/boss_theme.ogg")
	music_player.stream.loop = true
	hit_sfx_player.stream = load("res://Assets/Audio/SFX/hit_impact.ogg")
	victory_sfx_player.stream = load("res://Assets/Audio/SFX/victory_fanfare.ogg")


func start_music() -> void:
	if music_player and not music_player.playing:
		music_player.play()


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	if boss_health <= 0 and not defeated:
		defeated = true
		state_machine.enter_defeated()
		# Downed opens his hurtbox, but the fight is over: punches still on their way mustn't land.
		$Hurtbox.monitoring = false
		$Hurtbox.monitorable = false
		if music_player.playing:
			music_player.stop()
		victory_sfx_player.play()
		get_tree().call_group("arena_crowd", "cheer", 2.0)
		GameProgress.next_boss_scene = "res://Scenes/Bosses/GreysonBossFightScene.tscn"
		FightOutro.finish_fight(get_tree(), true)


# Called by FightOutro when the player loses.
func on_player_defeated() -> void:
	state_machine.enter_player_defeated()


func get_health_ratio() -> float:
	return float(boss_health) / float(max_health)


# Global position of the centre of a pixel on Eric's sheet frames.
func frame_point(pixel: Vector2) -> Vector2:
	return to_global(EricArtLayout.frame_local(pixel + Vector2(0.5, 0.5)))


func _apply_art_layout() -> void:
	scale = Vector2(EricArtLayout.SCALE, EricArtLayout.SCALE)
	sprite.hframes = EricArtLayout.SHEET_FRAMES
	sprite.offset = EricArtLayout.SPRITE_OFFSET
	_fit_box($CollisionShape2D, EricArtLayout.BODY_BOX)
	_fit_box($Hurtbox/CollisionShape2D, EricArtLayout.BODY_BOX)
	_fit_box($GrabArea2D/CollisionShape2D, EricArtLayout.GRAB_BOX)
	var whirlwind: CollisionShape2D = $WhirlwindArea2D/CollisionShape2D
	whirlwind.position = EricArtLayout.frame_local(EricArtLayout.WHIRLWIND_CENTRE)
	whirlwind.scale = EricArtLayout.WHIRLWIND_RADII / whirlwind.shape.radius


func _fit_box(shape_node: CollisionShape2D, box: Rect2) -> void:
	shape_node.position = EricArtLayout.frame_local(box.get_center())
	shape_node.shape.size = box.size


func _on_hurtbox_entered(area: Area2D) -> void:
	if area.is_in_group("player attack"):
		area.get_parent().combo.resolve_punch(self)


func take_punch(amount: int) -> int:
	var dealt := mini(amount, boss_health)
	boss_health -= dealt
	print("Boss health: ", boss_health)
	_update_health_bar()
	_hit_feedback()
	hit_sfx_player.play()
	return dealt


# The player's finisher (PlayerFinisher). Only the Downed window can be dazed: the bear hug's stumble
# is too short for a three-punch combo.
func can_be_dazed() -> bool:
	return not defeated and boss_health > 0 and not daze_used and state_machine.current_state == state_machine.states.get("Downed")


func enter_daze() -> void:
	daze_used = true


func exit_daze(_finisher_landed: bool) -> void:
	pass


func end_recovery(stagger_time: float) -> bool:
	if defeated or boss_health <= 0:
		return false
	state_machine.downed_state_timer.stop()
	state_machine.start_chain(stagger_time)
	return true


func take_finisher(amount: int) -> int:
	return take_punch(amount)


func get_max_health() -> int:
	return max_health


func get_daze_anchor() -> Vector2:
	return to_global(EricArtLayout.frame_local(EricArtLayout.DAZE_HEAD_PIXEL + Vector2(0.5, 0.5), sprite.flip_h))


func get_finisher_hurtbox() -> Area2D:
	return $Hurtbox


func _build_health_bar() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)

	name_label = Label.new()
	name_label.text = "ERIC"
	name_label.position = Vector2(770, 36)
	name_label.theme = load("res://Assets/UI/ui_theme.tres")
	name_label.add_theme_color_override("font_color", Color(1, 1, 1))
	name_label.add_theme_color_override("font_outline_color", Color(0, 0, 0))
	name_label.add_theme_constant_override("outline_size", 6)
	layer.add_child(name_label)

	health_bar = ProgressBar.new()
	health_bar.min_value = 0
	health_bar.max_value = max_health
	health_bar.value = boss_health
	health_bar.show_percentage = false
	health_bar.size = Vector2(380, 22)
	health_bar.position = Vector2(770, 70)

	var bg := StyleBoxFlat.new()
	bg.bg_color = Color(0.08, 0.08, 0.08, 0.85)
	bg.set_corner_radius_all(3)
	bg.border_width_left = 2
	bg.border_width_right = 2
	bg.border_width_top = 2
	bg.border_width_bottom = 2
	bg.border_color = Color(0, 0, 0)
	health_bar.add_theme_stylebox_override("background", bg)

	fill_style = StyleBoxFlat.new()
	fill_style.bg_color = Color(0.85, 0.16, 0.16, 1)
	fill_style.set_corner_radius_all(3)
	health_bar.add_theme_stylebox_override("fill", fill_style)

	layer.add_child(health_bar)


func _update_health_bar() -> void:
	if not health_bar:
		return
	var tween = create_tween()
	tween.tween_property(health_bar, "value", boss_health, 0.2)

	var ratio := get_health_ratio()
	if ratio <= 0.34:
		fill_style.bg_color = Color(1.0, 0.55, 0.0, 1)  # rage orange
	elif ratio <= 0.6:
		fill_style.bg_color = Color(0.95, 0.75, 0.1, 1)  # caution yellow
	else:
		fill_style.bg_color = Color(0.85, 0.16, 0.16, 1)  # normal red


func _hit_feedback() -> void:
	if not sprite:
		return

	# Flash the boss white for a beat
	sprite.modulate = Color(3, 3, 3)
	var flash_tween = create_tween()
	flash_tween.tween_property(sprite, "modulate", Color(1, 1, 1), 0.15)

	# Small impact shake on the sprite itself (no camera needed)
	var shake_tween = create_tween()
	for i in 4:
		var offset = Vector2(randf_range(-5, 5), randf_range(-5, 5))
		shake_tween.tween_property(sprite, "position", sprite_base_position + offset, 0.025)
	shake_tween.tween_property(sprite, "position", sprite_base_position, 0.025)

	# Brief hit-stop for weight
	HitStop.freeze(get_tree(), 0.06)


func _on_dialogue_ended(dialogue: Object) -> void:
	post_dialogue_pre_fight_timer.start()
