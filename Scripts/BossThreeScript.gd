extends Node2D

# Coordinator for the Carter & Josh wrestling-duo boss fight.
# Neither wrestler can ever be safely punched (see JoshScript/CarterScript
# - attempting to hit either one always hits the player back instead).
# The only way to damage them is to bait them into charging at the same
# time: both lock onto the player's current position when a cycle fires,
# Josh sweeps the whole arena width at that height, Carter sweeps the
# whole arena height at that horizontal spot, and since both charges are
# time-normalized to arrive at that locked point simultaneously, they
# always collide with each other there unless one of them is stopped
# first - the player's job is just to not be standing there anymore.

#CONSTANTS
@export var max_health := 10
var boss_health := max_health
var damage_per_collision := 2

@export var josh: CharacterBody2D
@export var carter: CharacterBody2D
@export var cycle_timer: Timer
@export var post_dialogue_pre_fight_timer: Timer

#UI (built at runtime - no new art needed)
var health_bar: ProgressBar
var name_label: Label
var fill_style: StyleBoxFlat

#AUDIO
@onready var music_player: AudioStreamPlayer = $MusicPlayer
@onready var charge_sfx_player: AudioStreamPlayer = $ChargeSfxPlayer
@onready var collision_sfx_player: AudioStreamPlayer = $CollisionSfxPlayer
@onready var victory_sfx_player: AudioStreamPlayer = $VictorySfxPlayer

var defeated := false
var collision_locked := false

const BASE_CYCLE := 3.2
const MIN_CYCLE := 1.9
const BASE_ARRIVAL := 0.45
const MIN_ARRIVAL := 0.24


func _ready() -> void:
	_build_health_bar()

	music_player.stream = load("res://Assets/Audio/Music/boss3_theme.ogg")
	if music_player.stream:
		music_player.stream.loop = true
	charge_sfx_player.stream = load("res://Assets/Audio/SFX/wrestler_charge.ogg")
	collision_sfx_player.stream = load("res://Assets/Audio/SFX/wrestler_collision.ogg")
	victory_sfx_player.stream = load("res://Assets/Audio/SFX/victory_fanfare.ogg")

	DialogueManager.show_dialogue_balloon(load("res://Dialogue/CarterAndJoshPreFight.dialogue"), "start")
	DialogueManager.dialogue_ended.connect(_on_dialogue_ended)


func _on_dialogue_ended(dialogue: Object) -> void:
	post_dialogue_pre_fight_timer.start()


func _on_post_dialogue_pre_fight_timer_timeout() -> void:
	if music_player and not music_player.playing:
		music_player.play()
	if cycle_timer:
		cycle_timer.wait_time = BASE_CYCLE
		cycle_timer.start()


func get_health_ratio() -> float:
	return float(boss_health) / float(max_health)


func _on_cycle_timer_timeout() -> void:
	_start_double_charge()


func _start_double_charge() -> void:
	if defeated:
		return
	collision_locked = false

	var ratio := get_health_ratio()
	var rage = clamp(1.0 - ratio, 0.0, 1.0)
	if cycle_timer:
		cycle_timer.wait_time = lerp(BASE_CYCLE, MIN_CYCLE, rage)
	var arrival_time = lerp(BASE_ARRIVAL, MIN_ARRIVAL, rage)

	var player = get_tree().current_scene.get_node_or_null("Arena/MainPlayer/CharacterBody2D")
	if not player:
		return
	var target = player.global_position

	if charge_sfx_player:
		charge_sfx_player.play()

	var j = josh
	var c = carter
	if j and j.has_method("begin_charge"):
		j.begin_charge(target, arrival_time)
	if c and c.has_method("begin_charge"):
		c.begin_charge(target, arrival_time)


func on_wrestler_collision() -> void:
	if collision_locked or defeated:
		return
	collision_locked = true

	boss_health = max(boss_health - damage_per_collision, 0)
	print("Boss health: ", boss_health)
	_update_health_bar()

	if collision_sfx_player:
		collision_sfx_player.play()

	var j = josh
	var c = carter
	if j and j.has_method("interrupt_charge"):
		j.interrupt_charge()
	if c and c.has_method("interrupt_charge"):
		c.interrupt_charge()
	if j and j.has_method("hit_feedback"):
		j.hit_feedback()
	if c and c.has_method("hit_feedback"):
		c.hit_feedback()

	if boss_health <= 0 and not defeated:
		_on_defeated()


func _on_defeated() -> void:
	defeated = true
	if cycle_timer:
		cycle_timer.stop()
	if music_player.playing:
		music_player.stop()
	victory_sfx_player.play()
	GameProgress.next_boss_scene = ""

	if josh and josh.has_method("play_defeated"):
		josh.play_defeated()
	if carter and carter.has_method("play_defeated"):
		carter.play_defeated()

	await get_tree().create_timer(2.2).timeout
	get_tree().change_scene_to_file("res://Scenes/Core/VictoryScene.tscn")


func _build_health_bar() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)

	name_label = Label.new()
	name_label.text = "CARTER & JOSH"
	name_label.position = Vector2(700, 36)
	name_label.add_theme_font_size_override("font_size", 26)
	name_label.add_theme_color_override("font_color", Color(1, 1, 1))
	name_label.add_theme_color_override("font_outline_color", Color(0, 0, 0))
	name_label.add_theme_constant_override("outline_size", 6)
	layer.add_child(name_label)

	health_bar = ProgressBar.new()
	health_bar.min_value = 0
	health_bar.max_value = max_health
	health_bar.value = boss_health
	health_bar.show_percentage = false
	health_bar.size = Vector2(460, 22)
	health_bar.position = Vector2(700, 70)

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
	fill_style.bg_color = Color(0.75, 0.25, 0.65, 1)
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
		fill_style.bg_color = Color(0.75, 0.25, 0.65, 1)  # normal
