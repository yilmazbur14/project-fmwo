extends Node2D

# The damage area: a flat oval the size of the full-grown marker, so a player just outside the drawn
# marker is never hit. A polygon rather than a capsule, which would bulge past the oval's shoulders.
const HIT_SIZE := Vector2(132, 66)
const HIT_OVAL_POINTS := 32
const HITBOX_ACTIVE_TIME := 0.1
const FALL_TIME := 0.3
const FALL_ANGLE_DEGREES := 20.0
# Just above the top of the screen, so the whole fall is in view wherever the nugget lands.
const FALL_START_Y := -80.0
const MARKER_START_SCALE := 0.2
# The marker at full size, in screen px.
const MARKER_SIZE := Vector2(132, 66)

const SHAKE_STEPS := 4
const SHAKE_STEP_TIME := 0.03
const SHAKE_STRENGTH := 4.0

# Art swap point: the marker, meteor and impact are placeholders until nugget_target.png,
# nugget_meteor.png and nugget_impact.png are in. Marker/Growth, Meteor and ImpactSprite keep their
# roles when the art replaces what's inside them.
@export var marker: Node2D
@export var marker_growth: Node2D
@export var meteor: Node2D
@export var impact_sprite: Sprite2D
@export var hitbox_shape: CollisionShape2D
@export var animation_player: AnimationPlayer
@export var impact_sfx: AudioStreamPlayer

# Impacts can land closer together than a shake lasts, and a shake started partway through another
# would take the shaken canvas as its rest position and leave it there. So all nuggets share one.
static var shake: Tween
static var shake_rest: Transform2D


func _ready() -> void:
	animation_player.animation_finished.connect(_on_animation_player_animation_finished)
	var oval := PackedVector2Array()
	for i in HIT_OVAL_POINTS:
		oval.append(Vector2.from_angle(TAU * i / HIT_OVAL_POINTS) * HIT_SIZE / 2.0)
	(hitbox_shape.shape as ConvexPolygonShape2D).points = oval


# What a nugget covers around its landing spot before it lands: the grown marker and the hit area.
static func footprint() -> Rect2:
	return Rect2(-MARKER_SIZE / 2.0, MARKER_SIZE).merge(Rect2(-HIT_SIZE / 2.0, HIT_SIZE))


func drop(warning_time: float) -> void:
	marker_growth.scale = Vector2.ONE * MARKER_START_SCALE
	marker.show()
	create_tween().tween_property(marker_growth, "scale", Vector2.ONE, warning_time)

	var fall_time := minf(FALL_TIME, warning_time)
	var fall_height := global_position.y - FALL_START_Y
	meteor.position = Vector2(fall_height * tan(deg_to_rad(FALL_ANGLE_DEGREES)), -fall_height)
	# Bound to this node like the growth, so freeing a nugget mid-fall stops all of it.
	var sequence := create_tween()
	sequence.tween_interval(warning_time - fall_time)
	sequence.tween_callback(meteor.show)
	sequence.tween_property(meteor, "position", Vector2.ZERO, fall_time)
	sequence.tween_callback(_land)
	sequence.tween_interval(HITBOX_ACTIVE_TIME)
	sequence.tween_callback(_disable_hitbox)


func _land() -> void:
	marker.hide()
	meteor.hide()
	impact_sprite.show()
	animation_player.play("impact")
	hitbox_shape.set_deferred("disabled", false)
	impact_sfx.play()
	_shake_screen()


func _disable_hitbox() -> void:
	hitbox_shape.set_deferred("disabled", true)


# Offsets the canvas instead of moving nodes, so physics bodies and the UI layers stay put.
func _shake_screen() -> void:
	var viewport := get_viewport()
	if shake and shake.is_valid():
		shake.kill()
	else:
		shake_rest = viewport.canvas_transform
	var rest := shake_rest
	# A SceneTree tween, so the canvas is put back even if this nugget is freed mid-shake.
	shake = get_tree().create_tween()
	for i in SHAKE_STEPS:
		var strength := SHAKE_STRENGTH * (1.0 - float(i) / SHAKE_STEPS)
		var offset := Vector2(randf_range(-strength, strength), randf_range(-strength, strength)).round()
		shake.tween_callback(func(): viewport.canvas_transform = rest.translated(offset))
		shake.tween_interval(SHAKE_STEP_TIME)
	shake.tween_callback(func(): viewport.canvas_transform = rest)


func _on_animation_player_animation_finished(anim_name: StringName) -> void:
	if anim_name == &"impact":
		queue_free()
