extends Node2D

# Phase two of the Greyson fight. The mech shares Computah's health pool, health bar and
# victory flow; it only owns its own attacks, hurtbox and hit reactions.
@export var computah : Node2D
@export var greyson : Node2D

const HitStop := preload("res://Scripts/HitStop.gd")
const FightOutro := preload("res://Scripts/FightOutro.gd")

const HAZARD_GROUP := "greyson_mech_hazard"
# Room for a full punch combo in one window.
const MAX_HITS_PER_WINDOW := 3
const PHANTOM_HIT_WINDOW := 0.5
const FRAME_SIZE := 96.0

@onready var body: CharacterBody2D = $MechCharacterBody
@onready var sprite: Sprite2D = $MechCharacterBody/Sprite2D
@onready var hurtbox: Area2D = $MechCharacterBody/Hurtbox
@onready var animation_player: AnimationPlayer = $AnimationPlayer
@onready var state_machine = $StateManager

#AUDIO
@onready var rocket_sfx_player: AudioStreamPlayer = $RocketSfxPlayer
@onready var laser_sfx_player: AudioStreamPlayer = $LaserSfxPlayer
@onready var slam_sfx_player: AudioStreamPlayer = $SlamSfxPlayer
@onready var downed_sfx_player: AudioStreamPlayer = $DownedSfxPlayer

var defeated := false
var hits_this_window := 0

var fight_clock := 0.0
var last_contact_hit_time := -INF


func _ready() -> void:
	# Computah has the outro's lines; the mech only has its attacks to stop.
	add_to_group(FightOutro.BOSS_GROUP)
	hurtbox.area_entered.connect(_on_hurtbox_entered)
	computah.phase_two_reached.connect(_on_phase_two_reached)

	rocket_sfx_player.stream = load("res://Assets/Audio/SFX/rocket_launch.ogg")
	laser_sfx_player.stream = load("res://Assets/Audio/SFX/laser_charge.ogg")
	slam_sfx_player.stream = load("res://Assets/Audio/SFX/earthquake_slam.ogg")
	downed_sfx_player.stream = load("res://Assets/Audio/SFX/downed_stinger.ogg")


func _physics_process(delta: float) -> void:
	fight_clock += delta


func get_health_ratio() -> float:
	return computah.get_health_ratio()


# Global position of a pixel on the mech's 96x96 sheet frames.
func frame_point(pixel: Vector2) -> Vector2:
	return sprite.to_global(pixel + Vector2(0.5, 0.5) - Vector2(FRAME_SIZE, FRAME_SIZE) / 2.0)


func add_hazard(hazard: Node2D, parent: Node2D, spawn_position: Vector2) -> void:
	hazard.add_to_group(HAZARD_GROUP)
	# Positioned before add_child so the hazard's _ready already sees where it spawned.
	hazard.position = parent.to_local(spawn_position)
	parent.add_child(hazard)


func _on_phase_two_reached() -> void:
	state_machine.on_child_transition(state_machine.current_state, "Morph")


func _on_hurtbox_entered(area: Area2D) -> void:
	if defeated or not area.is_in_group("player attack"):
		return

	# Same phantom-hit filter as Mason: a punch that connects as its hitbox switches on is
	# reported again when PlayerPunching switches the hitbox off, which would eat the hit cap.
	if not area.monitorable and fight_clock - last_contact_hit_time < PHANTOM_HIT_WINDOW:
		return
	if area.get_parent().combo.resolve_punch(self) > 0 and area.monitorable:
		last_contact_hit_time = fight_clock


func take_punch(amount: int) -> int:
	if state_machine.current_state != state_machine.states.get("Vulnerable"):
		return 0
	if hits_this_window >= MAX_HITS_PER_WINDOW:
		return 0

	hits_this_window += 1
	var dealt: int = computah.take_hit(amount)
	_hit_feedback()

	if computah.boss_health <= 0:
		# area_entered fires mid physics flush; the defeat sequence toggles hurtbox monitoring.
		call_deferred("_on_defeated")
	else:
		animation_player.play("hit")
		animation_player.queue("vulnerable")
	return dealt


func _on_defeated() -> void:
	defeated = true
	# Leaving Vulnerable shuts the hurtbox.
	state_machine.enter_defeated()

	# Computah's script runs the victory flow once its health hits zero; anything the mech
	# fired that outlives it could still hurt the player after the win.
	for hazard in get_tree().get_nodes_in_group(HAZARD_GROUP):
		hazard.queue_free()

	get_tree().call_group("arena_crowd", "cheer", 2.0)


# Called by FightOutro when the player loses.
func on_player_defeated() -> void:
	state_machine.enter_player_defeated()
	for hazard in get_tree().get_nodes_in_group(HAZARD_GROUP):
		hazard.queue_free()


func _hit_feedback() -> void:
	sprite.modulate = Color(3, 3, 3)
	var flash_tween = create_tween()
	flash_tween.tween_property(sprite, "modulate", Color(1, 1, 1), 0.15)

	HitStop.freeze(get_tree(), 0.06)
