extends Node2D

# The damage area: the marker's oval, so a player just outside the drawn marker is never hit. A polygon
# rather than a capsule, which would bulge past the oval's shoulders.
const HIT_SIZE := Vector2(132, 66)
const HIT_OVAL_POINTS := 32
const HITBOX_ACTIVE_TIME := 0.1
const FALL_TIME := 0.3
# Drawn into nugget_meteor.png, so the sprite is never rotated to match it.
const FALL_ANGLE_DEGREES := 20.0
# Just above the top of the screen, so the whole fall is in view wherever the nugget lands.
const FALL_START_Y := -80.0
const METEOR_FRAME_TIME := 0.08
# nugget_target.png's ring, 44x22 texels at 3x on every frame.
const MARKER_SIZE := Vector2(132, 66)
# The marker shows frames 0 and 1 for a quarter of the warning each, then flashes between 2 and 3.
const MARKER_FLASH_TIME := 0.12
# Above the characters, so Mason's body can't hide a marker that lands over him.
const RAISED_MARKER_LAYER := 1

const SHAKE_STEPS := 4
const SHAKE_STEP_TIME := 0.03
const SHAKE_STRENGTH := 4.0

@export var marker: Sprite2D
@export var meteor: Node2D
@export var meteor_sprite: Sprite2D
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


# What a nugget covers around its landing spot before it lands: the marker and the hit area.
static func footprint() -> Rect2:
	return Rect2(-MARKER_SIZE / 2.0, MARKER_SIZE).merge(Rect2(-HIT_SIZE / 2.0, HIT_SIZE))


func drop(warning_time: float, over_mason := false) -> void:
	marker.z_index = RAISED_MARKER_LAYER if over_mason else 0
	marker.frame = 0
	marker.show()
	create_tween().tween_method(_set_marker_frame.bind(warning_time), 0.0, warning_time, warning_time)

	var fall_time := minf(FALL_TIME, warning_time)
	var fall_height := global_position.y - FALL_START_Y
	meteor.position = Vector2(fall_height * tan(deg_to_rad(FALL_ANGLE_DEGREES)), -fall_height)
	# Bound to this node like the marker's, so freeing a nugget mid-fall stops all of it.
	var sequence := create_tween()
	sequence.tween_interval(warning_time - fall_time)
	sequence.tween_callback(meteor.show)
	sequence.tween_property(meteor, "position", Vector2.ZERO, fall_time)
	sequence.parallel().tween_method(_set_meteor_frame, 0.0, fall_time, fall_time)
	sequence.tween_callback(_land)
	sequence.tween_interval(HITBOX_ACTIVE_TIME)
	sequence.tween_callback(_disable_hitbox)


func _set_marker_frame(elapsed: float, warning_time: float) -> void:
	var quarter := warning_time / 4.0
	if elapsed < quarter * 2.0:
		marker.frame = int(elapsed / quarter)
	else:
		marker.frame = 2 + int((elapsed - quarter * 2.0) / MARKER_FLASH_TIME) % 2


func _set_meteor_frame(elapsed: float) -> void:
	meteor_sprite.frame = int(elapsed / METEOR_FRAME_TIME) % meteor_sprite.hframes


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
