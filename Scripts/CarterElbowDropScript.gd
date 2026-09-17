extends Node2D

signal finished

const DIVE_FRAME_INTERVAL := 0.08
const HITBOX_ACTIVE_TIME := 0.15
const LANDED_TIME := 0.2

# Screen px. The capsule lies flat along the ground under Carter, so it's wider than it is tall.
const HITBOX_RADIUS := 55.0
const HITBOX_LENGTH := 194.0
# How deep a landing moved off Mason has to reach into the hurtbox of a player standing by him, so the
# hit registers reliably rather than by a hair.
const MIN_PLAYER_OVERLAP := 4.0

const DIVE_START_POSITION := Vector2(420, -1000)
const LEAP_OUT_POSITION := Vector2(-300, -1000)

const LANDED_FRAME := 2
const SIT_UP_FRAME := 3
const LEAP_OUT_FRAME := 4

# Carter and his dust draw above the characters, since he comes down out of the sky.
const AIR_LAYER := 2
# Above the characters, so Mason's body can't hide a marker that lands over him.
const RAISED_MARKER_LAYER := 1

# Art swap point: elbow_target_v2.png (2 frames) and elbow_impact_v2.png (4 frames) are being drawn to
# fit the bigger hitbox. Until they're in, the v1 art stays at its native 3x rather than being stretched.
# Frame size follows from the texture width and the frame count.
const TARGET_TEXTURE := preload("res://Assets/Characters/Mason/elbow_target.png")
const TARGET_FRAMES := 2
const IMPACT_TEXTURE := preload("res://Assets/Characters/Mason/elbow_impact.png")
const IMPACT_FRAMES := 4

@export var target_sprite: Sprite2D
@export var carter_sprite: Sprite2D
@export var impact_sprite: Sprite2D
@export var hitbox_shape: CollisionShape2D
@export var animation_player: AnimationPlayer
@export var slam_sfx: AudioStreamPlayer

# Set by Mason for the current phase before begin().
var telegraph_time: float
var dive_time: float
var sit_up_time: float
var leap_out_time: float
var gap_between_drops: float

var target_player: Node2D
var arena_bounds: Rect2
var keep_out: Rect2
var over_mason := false


func _ready() -> void:
	animation_player.animation_finished.connect(_on_animation_player_animation_finished)
	target_sprite.texture = TARGET_TEXTURE
	target_sprite.hframes = TARGET_FRAMES
	impact_sprite.texture = IMPACT_TEXTURE
	impact_sprite.hframes = IMPACT_FRAMES
	var capsule := hitbox_shape.shape as CapsuleShape2D
	capsule.radius = HITBOX_RADIUS
	capsule.height = HITBOX_LENGTH


# Everything a drop covers around its landing spot: Carter's pose, the marker, the dust burst and the
# hitbox. Frames rather than drawn pixels, so it follows an art swap without re-measuring.
func footprint() -> Rect2:
	var covered := _local_rect(hitbox_shape, hitbox_shape.shape.get_rect())
	for sprite: Sprite2D in [carter_sprite, target_sprite, impact_sprite]:
		covered = covered.merge(_local_rect(sprite, sprite.get_rect()))
	return covered


# Where drops can land inside `ropes`: the hitbox, which the marker art is drawn to fit, stays inside
# them and Carter's landed pose stays below the back rope. Not the whole footprint: the square marker and
# dust frames reach well past the flat oval they hold, and would pull the bounds in until a player
# standing against a rope was out of reach.
func landing_bounds(ropes: Rect2) -> Rect2:
	var hitbox := _local_rect(hitbox_shape, hitbox_shape.shape.get_rect())
	var pose := _local_rect(carter_sprite, carter_sprite.get_rect())
	var top_left := Vector2(ropes.position.x - hitbox.position.x, ropes.position.y - pose.position.y)
	return Rect2(top_left, ropes.end - hitbox.end - top_left)


func _local_rect(item: Node2D, rect: Rect2) -> Rect2:
	return global_transform.affine_inverse() * item.global_transform * rect


func begin(drop_count: int, player: Node2D, bounds: Rect2, avoid: Rect2) -> void:
	target_player = player
	arena_bounds = bounds
	keep_out = avoid
	# Every drop lives on one tween so the timings can't drift apart, and the
	# whole attack dies with this node if Mason frees it mid-sequence.
	var sequence := create_tween()
	for i in drop_count:
		if i > 0:
			sequence.tween_interval(gap_between_drops)
		sequence.tween_callback(_mark_target)
		sequence.tween_interval(telegraph_time)
		sequence.tween_callback(_start_dive)
		sequence.tween_property(carter_sprite, "position", Vector2.ZERO, dive_time).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
		sequence.parallel().tween_method(_set_dive_frame, 0.0, dive_time, dive_time)
		sequence.tween_callback(_land)
		sequence.tween_interval(HITBOX_ACTIVE_TIME)
		sequence.tween_callback(_disable_hitbox)
		sequence.tween_interval(LANDED_TIME - HITBOX_ACTIVE_TIME)
		sequence.tween_callback(carter_sprite.set_frame.bind(SIT_UP_FRAME))
		sequence.tween_interval(sit_up_time)
		sequence.tween_callback(_leap_out)
		sequence.tween_property(carter_sprite, "position", LEAP_OUT_POSITION, leap_out_time).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
		sequence.tween_callback(carter_sprite.hide)
	sequence.tween_callback(_finish)


func _mark_target() -> void:
	if is_instance_valid(target_player):
		var hurtbox_shape: CollisionShape2D = target_player.hurtBox.get_node("CollisionShape2D")
		var hurtbox := hurtbox_shape.global_transform * hurtbox_shape.shape.get_rect()
		global_position = _landing_spot(target_player.global_position, hurtbox)
	over_mason = keep_out.has_point(global_position)
	target_sprite.z_index = RAISED_MARKER_LAYER if over_mason else 0
	target_sprite.show()
	animation_player.play("pulse")


# The spot nearest the target that's inside the bounds and outside keep_out, pushed straight out through
# one of its edges. Standing right by Mason mustn't make a player safe, so an edge spot that still reaches
# their hurtbox wins, and if there's none Carter lands on them anyway, over Mason.
func _landing_spot(target: Vector2, hurtbox: Rect2) -> Vector2:
	var spot := target.clamp(arena_bounds.position, arena_bounds.end)
	if not keep_out.has_point(spot):
		return spot
	# The capsule overlaps the hurtbox when its centre is within `reach` of the hurtbox stretched by the
	# capsule's straight middle.
	var half_middle := HITBOX_LENGTH / 2.0 - HITBOX_RADIUS
	var reach_box := hurtbox.grow_individual(half_middle, 0.0, half_middle, 0.0)
	var reach := HITBOX_RADIUS - MIN_PLAYER_OVERLAP
	var pushed := Vector2.INF
	var reaching := Vector2.INF
	for axis in 2:
		var across := 1 - axis
		for edge: float in [keep_out.position[axis] - 1.0, keep_out.end[axis]]:
			if edge < arena_bounds.position[axis] or edge > arena_bounds.end[axis]:
				continue
			var candidate := spot
			candidate[axis] = edge
			if candidate.distance_to(spot) < pushed.distance_to(spot):
				pushed = candidate
			var gap := maxf(0.0, maxf(reach_box.position[axis] - edge, edge - reach_box.end[axis]))
			if gap >= reach:
				continue
			var spread := sqrt(reach * reach - gap * gap)
			var low := maxf(reach_box.position[across] - spread, arena_bounds.position[across])
			var high := minf(reach_box.end[across] + spread, arena_bounds.end[across])
			if low > high:
				continue
			candidate[across] = clampf(spot[across], low, high)
			if candidate.distance_to(spot) < reaching.distance_to(spot):
				reaching = candidate
	if reaching != Vector2.INF:
		return reaching
	# Landing over Mason is only worth it if it hits; a player the bounds keep out of reach is pushed out.
	if spot.distance_to(spot.clamp(reach_box.position, reach_box.end)) < reach:
		return spot
	return spot if pushed == Vector2.INF else pushed


func _start_dive() -> void:
	carter_sprite.position = DIVE_START_POSITION
	carter_sprite.frame = 0
	carter_sprite.z_index = AIR_LAYER
	carter_sprite.show()


func _set_dive_frame(elapsed: float) -> void:
	carter_sprite.frame = int(elapsed / DIVE_FRAME_INTERVAL) % 2


func _land() -> void:
	carter_sprite.frame = LANDED_FRAME
	# On the ground over Mason, Carter and his dust depth-sort with him instead, so a landing behind him
	# goes behind him.
	var layer := 0 if over_mason else AIR_LAYER
	carter_sprite.z_index = layer
	impact_sprite.z_index = layer
	target_sprite.hide()
	# The AnimationPlayer only applies burst's first key on its next update, so
	# without this the previous drop's last dust frame flashes for one frame.
	impact_sprite.frame = 0
	impact_sprite.show()
	animation_player.play("burst")
	hitbox_shape.set_deferred("disabled", false)
	slam_sfx.play()


func _disable_hitbox() -> void:
	hitbox_shape.set_deferred("disabled", true)


# Back above everything as he jumps away: depth-sorted, he'd sink behind the arena floor as he rose.
func _leap_out() -> void:
	carter_sprite.frame = LEAP_OUT_FRAME
	carter_sprite.z_index = AIR_LAYER


func _finish() -> void:
	finished.emit()
	# The final slam is still ringing when the last leap ends. Freeing now cuts
	# it off, so linger until it stops — the hitbox is already off and every
	# sprite is hidden by this point, so the lingering node is harmless.
	if slam_sfx.playing:
		slam_sfx.finished.connect(queue_free, CONNECT_ONE_SHOT)
	else:
		queue_free()


func _on_animation_player_animation_finished(anim_name: StringName) -> void:
	if anim_name == &"burst":
		impact_sprite.hide()
