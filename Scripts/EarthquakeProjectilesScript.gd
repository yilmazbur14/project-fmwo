extends Node2D

@export var earthquake_collision_2: Area2D
@export var earthquake_collision_4: Area2D
@export var earthquake_collision_1: Area2D
@export var earthquake_collision_3: Area2D
@export var earthquake_collision_6: Area2D
@export var earthquake_collision_7: Area2D
@export var earthquake_collision_8: Area2D
@export var earthquake_collision_9: Area2D
@export var move_speed : float = 250.0

@export var earthquake_distance_from_boss_x : float = 10.0
@export var earthquake_distance_from_boss_y : float = 10.0

@export var x_scale := 15.0
@export var y_scale := 0.5

var directions = {
	7: Vector2(-1, -1).normalized(),
	8: Vector2(0, -1),
	9: Vector2(1, -1).normalized(),

	4: Vector2(-1, 0),
	6: Vector2(1, 0),

	1: Vector2(-1, 1).normalized(),
	2: Vector2(0, 1),
	3: Vector2(1, 1).normalized()
}

var collision_map := {}

@export var collision_shapes : Array[CollisionShape2D]

@onready var despawn_earthquakes_timer = $DespawnEarthquakesTimer

var enable_earthquakes = false
var loop_number = 0

# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	rotation_degrees = randf_range(0, 360)
	# rotation_degrees = 0

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

	var spawn_radius_x := earthquake_distance_from_boss_x
	var spawn_radius_y := earthquake_distance_from_boss_y

	for numpad in collision_map:
		var dir = directions[numpad]

		# ellipse-style spawn (important for your stretched earthquake look)
		collision_map[numpad].position = Vector2(
			dir.x * spawn_radius_x,
			dir.y * spawn_radius_y
		)

	for shape in collision_shapes:
		# shape.scale = Vector2(x_scale, y_scale)
		shape.scale = Vector2.ONE


	
	despawn_earthquakes_timer.start()

# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	pass

func _physics_process(_delta: float) -> void:
	if enable_earthquakes:
		for numpad in collision_map:
			var col = collision_map[numpad]
			var dir = directions[numpad]

			col.position += dir * move_speed * _delta

func enable_earthquake_areas():
	# print("Enabling hitbox")
	enable_earthquakes = true

func _on_despawn_earthquakes_timeout() -> void:
	queue_free()
