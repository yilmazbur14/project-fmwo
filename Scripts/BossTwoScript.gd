extends Node2D

signal phase_two_reached

const HitStop := preload("res://Scripts/HitStop.gd")
const FightOutro := preload("res://Scripts/FightOutro.gd")
# What Computah and Greyson say once the fight is over, under player_won and player_lost.
const OUTRO_DIALOGUE := "res://Dialogue/GreysonAndComputahOutro.dialogue"
# This fight's place in the order; GameProgress decides what follows it.
const FIGHT_SCENE := "res://Scenes/Bosses/GreysonBossFightScene.tscn"

#CONSTANTS
@export var max_health := 10
var boss_health := max_health
const PHASE_TWO_RATIO := 0.5

#UI (built at runtime - no new art needed)
var health_bar: ProgressBar
var name_label: Label
var fill_style: StyleBoxFlat

@onready var sprite = $Sprite2D

#AUDIO
@onready var music_player: AudioStreamPlayer = $MusicPlayer
@onready var hit_sfx_player: AudioStreamPlayer = $HitSfxPlayer
@onready var victory_sfx_player: AudioStreamPlayer = $VictorySfxPlayer
var defeated := false
var phase_two := false

# The finisher's daze stars circle here, from the sprite's centre: about 34 px over the antenna.
const DAZE_ANCHOR_OFFSET := Vector2(0, -92)
# One finisher daze per Downed window; Downed clears it.
var daze_used := false
# Runs the stagger after a landed finisher, straight into the next attack cycle.
var finisher_stagger_timer: Timer

var sprite_base_position: Vector2

# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	add_to_group(FightOutro.BOSS_GROUP)
	var hurtBox = get_node("Hurtbox")
	hurtBox.area_entered.connect(_on_hurtbox_entered)

	finisher_stagger_timer = Timer.new()
	finisher_stagger_timer.name = "FinisherStaggerTimer"
	finisher_stagger_timer.one_shot = true
	finisher_stagger_timer.timeout.connect($StateManager.resume_attack_cycle)
	add_child(finisher_stagger_timer)

	sprite_base_position = sprite.position
	_build_health_bar()

	music_player.stream = load("res://Assets/Audio/Music/boss2_theme.ogg")
	if music_player.stream:
		music_player.stream.loop = true
	hit_sfx_player.stream = load("res://Assets/Audio/SFX/hit_impact.ogg")
	victory_sfx_player.stream = load("res://Assets/Audio/SFX/victory_fanfare.ogg")


func start_music() -> void:
	if music_player and not music_player.playing:
		music_player.play()


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(_delta: float) -> void:
	if boss_health <= 0 and not defeated:
		defeated = true
		if music_player.playing:
			music_player.stop()
		victory_sfx_player.play()
		GameProgress.next_boss_scene = GameProgress.next_fight_after(FIGHT_SCENE)
		FightOutro.finish_fight(get_tree(), true)


# Called by FightOutro when the player loses. From phase two on, the mech has the attacks to stop.
func on_player_defeated() -> void:
	finisher_stagger_timer.stop()
	if not phase_two:
		$StateManager.end_phase_one()


func get_health_ratio() -> float:
	return float(boss_health) / float(max_health)


func _on_hurtbox_entered(area: Area2D) -> void:
	if area.is_in_group("player attack"):
		area.get_parent().combo.resolve_punch(self)


func take_punch(amount: int) -> int:
	# Computah stops taking hits at the threshold, so a burst of hits can't skip the mech;
	# from then on only the mech's overheat window deals damage, through take_hit().
	# A charged punch that would carry past the threshold is cut down to reach it exactly.
	if phase_two:
		return 0
	var phase_two_health := floori(max_health * PHASE_TWO_RATIO)
	var dealt := take_hit(mini(amount, boss_health - phase_two_health))
	_hit_feedback()
	if get_health_ratio() <= PHASE_TWO_RATIO:
		phase_two = true
		# area_entered fires mid physics flush, and ending phase one toggles hurtbox monitoring.
		call_deferred("_start_phase_two")
	return dealt


func take_hit(amount: int) -> int:
	var dealt := mini(amount, boss_health)
	boss_health -= dealt
	print("Boss health: ", boss_health)
	_update_health_bar()
	hit_sfx_player.play()
	return dealt


# The player's finisher (PlayerFinisher). Only Downed can be dazed, and only while the finisher can
# still take health before the phase-two threshold.
func can_be_dazed() -> bool:
	var state_machine = $StateManager
	return not phase_two and not defeated and boss_health > floori(max_health * PHASE_TWO_RATIO) and not daze_used and state_machine.current_state == state_machine.states.get("Downed")


func enter_daze() -> void:
	daze_used = true


func exit_daze(_finisher_landed: bool) -> void:
	pass


# A finisher that reaches the threshold starts the morph instead.
func end_recovery(stagger_time: float) -> bool:
	if phase_two or defeated:
		return false
	var state_machine = $StateManager
	state_machine.downed_state_timer.stop()
	state_machine.on_child_transition(state_machine.current_state, "Idle")
	# He has no hit frames; staying dazed reads better than snapping back to idle.
	$AnimationPlayer.play("downed")
	finisher_stagger_timer.start(stagger_time)
	return true


# take_punch already cuts it down to the threshold and starts the morph there.
func take_finisher(amount: int) -> int:
	return take_punch(amount)


func get_max_health() -> int:
	return max_health


func get_daze_anchor() -> Vector2:
	return sprite.global_position + DAZE_ANCHOR_OFFSET


func get_finisher_hurtbox() -> Area2D:
	return $Hurtbox


func _start_phase_two() -> void:
	finisher_stagger_timer.stop()
	# The player faces the mech once it has formed; until then there's nothing to face.
	$Hurtbox.remove_from_group("boss_target")
	$StateManager.end_phase_one()
	phase_two_reached.emit()


func _build_health_bar() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)

	name_label = Label.new()
	name_label.text = GameProgress.boss_name(FIGHT_SCENE)
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
	fill_style.bg_color = Color(0.2, 0.6, 0.95, 1)
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
		fill_style.bg_color = Color(0.2, 0.6, 0.95, 1)  # normal "digital" blue


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
