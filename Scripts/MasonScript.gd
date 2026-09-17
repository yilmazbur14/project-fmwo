extends CharacterBody2D

const HitStop := preload("res://Scripts/HitStop.gd")
const FightOutro := preload("res://Scripts/FightOutro.gd")
# What he says once the fight is over, under player_won and player_lost.
const OUTRO_DIALOGUE := "res://Dialogue/MasonOutro.dialogue"

#CONSTANTS
@export var max_health := 10
var boss_health := max_health
const PHASE_TWO_RATIO := 0.5
const MAX_HITS_PER_WINDOW := 3
const PHANTOM_HIT_WINDOW := 0.5

#UI (built at runtime - no new art needed)
var health_bar: ProgressBar
var name_label: Label
var fill_style: StyleBoxFlat

@onready var sprite = $Sprite2D
@onready var animation_player: AnimationPlayer = $AnimationPlayer
@onready var hurtbox: Area2D = $Hurtbox
@onready var state_machine = $StateManager

#AUDIO
@onready var music_player: AudioStreamPlayer = $MusicPlayer
@onready var hit_sfx_player: AudioStreamPlayer = $HitSfxPlayer
@onready var victory_sfx_player: AudioStreamPlayer = $VictorySfxPlayer
@onready var squat_sfx_player: AudioStreamPlayer = $SquatSfxPlayer
@onready var phone_sfx_player: AudioStreamPlayer = $PhoneSfxPlayer
@onready var downed_sfx_player: AudioStreamPlayer = $DownedSfxPlayer
@onready var toss_sfx_player: AudioStreamPlayer = $TossSfxPlayer

var phase_two := false
var defeated := false
var hits_this_window := 0

var fight_clock := 0.0
var last_contact_hit_time := -INF

var sprite_base_position: Vector2


func _ready() -> void:
	add_to_group(FightOutro.BOSS_GROUP)
	hurtbox.area_entered.connect(_on_hurtbox_entered)

	sprite_base_position = sprite.position
	_build_health_bar()

	# Placeholder: Mason has no theme of his own yet.
	music_player.stream = load("res://Assets/Audio/Music/boss_theme.ogg")
	if music_player.stream:
		music_player.stream.loop = true
	hit_sfx_player.stream = load("res://Assets/Audio/SFX/hit_impact.ogg")
	victory_sfx_player.stream = load("res://Assets/Audio/SFX/victory_fanfare.ogg")
	squat_sfx_player.stream = load("res://Assets/Audio/SFX/wrestler_charge.ogg")
	phone_sfx_player.stream = load("res://Assets/Audio/SFX/laser_charge.ogg")
	downed_sfx_player.stream = load("res://Assets/Audio/SFX/downed_stinger.ogg")
	toss_sfx_player.stream = load("res://Assets/Audio/SFX/whirlwind_whoosh.ogg")


func start_music() -> void:
	if music_player and not music_player.playing:
		music_player.play()


func get_health_ratio() -> float:
	return float(boss_health) / float(max_health)


func _physics_process(delta: float) -> void:
	fight_clock += delta


func _on_hurtbox_entered(area: Area2D) -> void:
	if boss_health <= 0 or not area.is_in_group("player attack"):
		return

	# A punch that makes contact the moment its hitbox switches on is reported again, as a
	# phantom, when PlayerPunching switches the hitbox off ~0.4s later. A genuine next punch
	# only reports from a switched-off hitbox at the end of its own swing, two full swings
	# (~0.65s) after that contact. Game time, so hit-stop and frame hitches can't stretch the gap.
	if not area.monitorable and fight_clock - last_contact_hit_time < PHANTOM_HIT_WINDOW:
		return
	if area.get_parent().combo.resolve_punch(self) > 0 and area.monitorable:
		last_contact_hit_time = fight_clock


func take_punch(amount: int) -> int:
	if hits_this_window >= MAX_HITS_PER_WINDOW:
		return 0
	# Phase two can't be skipped: until a phase-two cycle starts, Mason can't drop past the
	# threshold, and a charged punch that would carry past it is cut down to reach it exactly.
	var lowest_health := 0
	if state_machine.cycle_phase == 0:
		lowest_health = floori(max_health * PHASE_TWO_RATIO)
	var dealt := mini(amount, boss_health - lowest_health)
	if dealt <= 0:
		return 0

	hits_this_window += 1
	boss_health -= dealt
	_update_health_bar()
	_hit_feedback()
	hit_sfx_player.play()

	if state_machine.current_state.name == "Eat":
		animation_player.play("hit")
		animation_player.queue("eat")

	if not phase_two and get_health_ratio() <= PHASE_TWO_RATIO:
		phase_two = true

	if boss_health <= 0:
		# area_entered fires mid physics flush; deferring keeps the state Exit/Enter
		# code the defeat sequence runs from having to be flush-safe.
		call_deferred("_on_defeated")
	return dealt


func _on_defeated() -> void:
	defeated = true
	hurtbox.set_deferred("monitoring", false)
	hurtbox.set_deferred("monitorable", false)
	state_machine.enter_defeated()

	# Any bomb, Carter or driver that outlives Mason could still hurt the player after the win.
	for hazard in get_tree().get_nodes_in_group("mason_hazard"):
		hazard.queue_free()

	if music_player.playing:
		music_player.stop()
	victory_sfx_player.play()
	get_tree().call_group("arena_crowd", "cheer", 2.0)
	GameProgress.next_boss_scene = ""
	FightOutro.finish_fight(get_tree(), true)


# Called by FightOutro when the player loses.
func on_player_defeated() -> void:
	state_machine.enter_player_defeated()
	# As after a win, nothing he's sent out may stay live.
	for hazard in get_tree().get_nodes_in_group("mason_hazard"):
		hazard.queue_free()


func _build_health_bar() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)

	name_label = Label.new()
	name_label.text = "MASON"
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
	fill_style.bg_color = Color(0.55, 0.36, 0.2, 1)
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
		fill_style.bg_color = Color(1.0, 0.55, 0.0, 1)
	elif ratio <= 0.6:
		fill_style.bg_color = Color(0.95, 0.75, 0.1, 1)
	else:
		fill_style.bg_color = Color(0.55, 0.36, 0.2, 1)


func _hit_feedback() -> void:
	if not sprite:
		return

	sprite.modulate = Color(3, 3, 3)
	var flash_tween = create_tween()
	flash_tween.tween_property(sprite, "modulate", Color(1, 1, 1), 0.15)

	var shake_tween = create_tween()
	for i in 4:
		var offset = Vector2(randf_range(-5, 5), randf_range(-5, 5))
		shake_tween.tween_property(sprite, "position", sprite_base_position + offset, 0.025)
	shake_tween.tween_property(sprite, "position", sprite_base_position, 0.025)

	HitStop.freeze(get_tree(), 0.06)
