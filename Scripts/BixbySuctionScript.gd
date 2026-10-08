extends Node2D

# The air beast Bixby's Inferno drags in while he inhales (BixbyBeastInferno): streaks rushing at his three
# mouths, each at the one nearest where it starts, most of them around the player, where the pull is felt. Only a picture. It spawns and moves
# them in _physics_process, so a freeze holds it; stop() lets the last ones fade and then it frees itself.

const InfernoLayout := preload("res://Scripts/BixbyInfernoArtLayout.gd")

# A streak this often, this share of them within NEAR_RADIUS of the player, flying at SPEED_RATIO times the
# pull, fading out over FADE_TIME and drawn STREAK_SCALE times the art's own scale.
const INTERVAL := 0.02
const NEAR_SHARE := 0.6
const NEAR_RADIUS := 450.0
const SPEED_RATIO := 2.5
const FADE_TIME := 0.5
const STREAK_SCALE := 1.5

# Set by the attack before it enters the tree.
var player: Node2D
var mouths: Array[Vector2] = []
var pull_speed := 495.0
# Where streaks start and what they are drawn as: the Inferno's unless whoever adds it sets its own (Liam's tornados).
var area := InfernoLayout.INFERNO_AREA
var spec: Dictionary = InfernoLayout.FINAL_SUCTION
var use_final := InfernoLayout.USE_FINAL_SUCTION

var clock := 0.0
var spawned := 0
var stopping := false
# [node, velocity, age, the mouth it flies at] per streak in the air.
var streaks: Array = []


# He has stopped inhaling: no new streaks.
func stop() -> void:
	stopping = true


func _physics_process(delta: float) -> void:
	clock += delta
	if not stopping:
		while clock >= spawned * INTERVAL:
			_spawn()
			spawned += 1
	for streak in streaks.duplicate():
		var node: Node2D = streak[0]
		var velocity: Vector2 = streak[1]
		streak[2] += delta
		var step := velocity * delta
		if streak[2] >= FADE_TIME or node.position.distance_to(streak[3]) <= step.length():
			node.queue_free()
			streaks.erase(streak)
			continue
		node.position += step
		node.modulate.a = 1.0 - streak[2] / FADE_TIME
		var sprite := node as Sprite2D
		if sprite:
			var column := int(streak[2] / spec.frame_time) % sprite.hframes
			sprite.frame_coords = Vector2i(column, sprite.frame_coords.y)
	if stopping and streaks.is_empty():
		queue_free()


func _spawn() -> void:
	var from := Vector2(randf_range(area.position.x, area.end.x), randf_range(area.position.y, area.end.y))
	if is_instance_valid(player) and randf() < NEAR_SHARE:
		var offset := Vector2.from_angle(randf() * TAU) * NEAR_RADIUS * sqrt(randf())
		from = (player.global_position + offset).clamp(area.position, area.end)
	var mouth := _nearest_mouth(from)
	if from.distance_to(mouth) < 1.0:
		return
	var direction := (mouth - from).normalized()
	var node := _final_streak(direction) if use_final else _placeholder_streak(direction)
	node.position = from
	add_child(node)
	streaks.append([node, direction * pull_speed * SPEED_RATIO, 0.0, mouth])


func _nearest_mouth(from: Vector2) -> Vector2:
	var nearest: Vector2 = mouths[0]
	for mouth in mouths:
		if from.distance_to(mouth) < from.distance_to(nearest):
			nearest = mouth
	return nearest


func _placeholder_streak(direction: Vector2) -> Node2D:
	var look := InfernoLayout.PLACEHOLDER_SUCTION
	var line := Line2D.new()
	line.points = PackedVector2Array([Vector2.ZERO, -direction * look.length * STREAK_SCALE])
	line.width = look.width * STREAK_SCALE
	line.default_color = look.colour
	return line


# Rows at 0, 45 and 90 degrees on screen (right, down-right, down); the other five directions are flips.
func _final_streak(direction: Vector2) -> Node2D:
	var sprite := Sprite2D.new()
	sprite.texture = load(spec.sheet)
	sprite.hframes = spec.frames
	sprite.vframes = 3
	sprite.scale = Vector2.ONE * InfernoLayout.SCALE * STREAK_SCALE
	var octant := posmod(roundi(direction.angle() / (PI / 4.0)), 8)
	var rows := [0, 1, 2, 1, 0, 1, 2, 1]
	sprite.flip_h = octant >= 3 and octant <= 5
	sprite.flip_v = octant >= 5
	sprite.frame_coords = Vector2i(0, rows[octant])
	return sprite
