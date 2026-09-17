extends Node2D

# Eight ground waves from Eric's slam. The group is spawned at Eric's scale, so one texel of the
# art is one local unit and the 70x3 hitboxes line up with it. Slams alternate between a
# straight pattern (0 degrees plus 45-degree steps) and a tilted one (22.5 degrees plus 45-degree
# steps) that lands in the straight one's gaps.

const STRAIGHT_TEXTURE := preload("res://Assets/Characters/Eric/eric_quake_projectile.png")
const TILTED_TEXTURE := preload("res://Assets/Characters/Eric/eric_quake_projectile_tilted.png")
const TILTED_OFFSET_DEGREES := 22.5
const FRAME_COUNT := 4
const FRAME_TIME := 0.08
const FADE_TIME := 0.25

@export var earthquake_collision_2: Area2D
@export var earthquake_collision_4: Area2D
@export var earthquake_collision_1: Area2D
@export var earthquake_collision_3: Area2D
@export var earthquake_collision_6: Area2D
@export var earthquake_collision_7: Area2D
@export var earthquake_collision_8: Area2D
@export var earthquake_collision_9: Area2D
# Local units per second; set by the slam from its on-screen speed.
@export var move_speed : float = 383.0
@export var spawn_radius : float = 20.0

# Set by the slam before the group is added.
var tilted := false

#FIGHTING GAME NUMPAD NOTATIONS FOR DIRECTIONS
# Travel angle of each direction in the straight pattern, clockwise from +x (y points down).
const NUMPAD_ANGLES := {
	6: 0.0,
	3: 45.0,
	2: 90.0,
	1: 135.0,
	4: 180.0,
	7: 225.0,
	8: 270.0,
	9: 315.0,
}

var collision_map := {}
var directions := {}
var first_frames := {}

@onready var despawn_earthquakes_timer = $DespawnEarthquakesTimer

var enable_earthquakes = false
var elapsed := 0.0

# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	collision_map = {
		1: earthquake_collision_1,
		2: earthquake_collision_2,
		3: earthquake_collision_3,
		4: earthquake_collision_4,
		6: earthquake_collision_6,
		7: earthquake_collision_7,
		8: earthquake_collision_8,
		9: earthquake_collision_9
	}

	for numpad in collision_map:
		var area: Area2D = collision_map[numpad]
		var degrees: float = NUMPAD_ANGLES[numpad] + (TILTED_OFFSET_DEGREES if tilted else 0.0)
		var dir := Vector2.from_angle(deg_to_rad(degrees))
		directions[numpad] = dir
		area.position = dir * spawn_radius
		# The hitbox's long side lies across the travel direction.
		area.get_node("CollisionShape2D").rotation = deg_to_rad(degrees) + PI / 2.0

		# Each sheet only draws two angles; every other direction is an exact quarter turn of
		# one of them, so the pixel art is never resampled at an odd angle.
		var quarter := floori(degrees / 90.0)
		var sprite: Sprite2D = area.get_node("Sprite2D")
		sprite.texture = TILTED_TEXTURE if tilted else STRAIGHT_TEXTURE
		sprite.rotation = quarter * PI / 2.0
		first_frames[numpad] = 0 if degrees - quarter * 90.0 < 45.0 else FRAME_COUNT

	_update_sprites()
	despawn_earthquakes_timer.start()

func _physics_process(_delta: float) -> void:
	elapsed += _delta
	if enable_earthquakes:
		for numpad in collision_map:
			var col = collision_map[numpad]
			var dir = directions[numpad]

			col.position += dir * move_speed * _delta
	_update_sprites()

func _update_sprites() -> void:
	var step := int(elapsed / FRAME_TIME)
	var alpha := clampf((despawn_earthquakes_timer.wait_time - elapsed) / FADE_TIME, 0.0, 1.0)
	var index := 0
	for numpad in collision_map:
		var sprite: Sprite2D = collision_map[numpad].get_node("Sprite2D")
		# Staggered so the waves don't pulse in sync.
		sprite.frame = first_frames[numpad] + (step + index) % FRAME_COUNT
		sprite.modulate.a = alpha
		index += 1

func enable_earthquake_areas():
	enable_earthquakes = true

func _on_despawn_earthquakes_timeout() -> void:
	queue_free()
