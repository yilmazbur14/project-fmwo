extends Node2D

signal finished

const HitInfo := preload("res://Scripts/HitInfo.gd")

const DIVE_FRAME_INTERVAL := 0.08

# The damage area at hit_scale 1: elbow_target_v2.png's oval, 72x40 texels at 3x with its outline on
# the resting frame, so a player just outside the drawn marker is never hit. A polygon rather than a
# capsule, which would bulge past the oval's shoulders.
const HITBOX_SIZE := Vector2(216, 120)
const HITBOX_OVAL_POINTS := 32
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

# Frame size follows from the texture width and the frame count.
const TARGET_TEXTURE := preload("res://Assets/Characters/Mason/elbow_target_v2.png")
const TARGET_FRAMES := 2
const IMPACT_TEXTURE := preload("res://Assets/Characters/Mason/elbow_impact_v2.png")
const IMPACT_FRAMES := 4

@export var target_sprite: Sprite2D
@export var carter_sprite: Sprite2D
@export var impact_sprite: Sprite2D
@export var hitbox_shape: CollisionShape2D
@export var animation_player: AnimationPlayer
@export var slam_sfx: AudioStreamPlayer

# How long the slam hurts, and how long he lies in it before sitting up.
@export var hitbox_active_time := 0.15
@export var landed_time := 0.14
# Mason's elbow_hit_scale, set on the drop before anything is measured off it. The marker, the dust
# and the oval hit area grow together on it, so the hit is always exactly what the marker showed.
@export var hit_scale := 1.0:
	set(value):
		hit_scale = value
		if is_node_ready():
			_apply_hit_scale()

# Set by Mason for the current phase before begin().
var telegraph_time: float
var dive_time: float
var sit_up_time: float
var leap_out_time: float
var gap_between_drops: float
# Set by Mason before begin() when his nugget shower rains on the same mat (MasonNuggetShower). Both
# markers are floor art sorted at their own top edge, so a nugget marker lying across the top of this
# much bigger one would draw mostly under it. Sorted up at this height instead, his marker draws under
# every nugget marker, and still under anyone standing on it. INF leaves it at its top edge.
var marker_sort_y := INF

var target_player: Node2D
var arena_bounds: Rect2
var keep_out: Rect2
var over_mason := false
# What the marker and dust art are authored at, before hit_scale grows them. Their positions grow
# with them: both are drawn from a texture offset that scales, and only the two together keep the
# oval they draw centred on the landing spot.
var art_scale := Vector2.ONE
var target_art_position := Vector2.ZERO
var target_art_offset := Vector2.ZERO
var impact_art_position := Vector2.ZERO


func _ready() -> void:
	hitbox_shape.get_parent().set_meta(HitInfo.META_ATTACK, &"carter_elbow_drop")
	animation_player.animation_finished.connect(_on_animation_player_animation_finished)
	target_sprite.texture = TARGET_TEXTURE
	target_sprite.hframes = TARGET_FRAMES
	impact_sprite.texture = IMPACT_TEXTURE
	impact_sprite.hframes = IMPACT_FRAMES
	art_scale = target_sprite.scale
	target_art_position = target_sprite.position
	target_art_offset = target_sprite.offset
	impact_art_position = impact_sprite.position
	# The shape resource is shared by every drop that comes out of this scene, so each one sizes its
	# own copy.
	hitbox_shape.shape = hitbox_shape.shape.duplicate()
	_apply_hit_scale()


func _apply_hit_scale() -> void:
	var oval := PackedVector2Array()
	for i in HITBOX_OVAL_POINTS:
		oval.append(Vector2.from_angle(TAU * i / HITBOX_OVAL_POINTS) * hit_size() / 2.0)
	(hitbox_shape.shape as ConvexPolygonShape2D).points = oval
	target_sprite.scale = art_scale * hit_scale
	target_sprite.position = target_art_position * hit_scale
	impact_sprite.scale = art_scale * hit_scale
	impact_sprite.position = impact_art_position * hit_scale


func hit_size() -> Vector2:
	return HITBOX_SIZE * hit_scale


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
		sequence.tween_interval(hitbox_active_time)
		sequence.tween_callback(_disable_hitbox)
		sequence.tween_interval(maxf(landed_time - hitbox_active_time, 0.0))
		sequence.tween_callback(carter_sprite.set_frame.bind(SIT_UP_FRAME))
		sequence.tween_interval(sit_up_time)
		sequence.tween_callback(_leap_out)
		sequence.tween_property(carter_sprite, "position", LEAP_OUT_POSITION, leap_out_time).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
		sequence.tween_callback(carter_sprite.hide)
	sequence.tween_callback(_finish)


# When each of begin()'s slams switches its hitbox on, in seconds after begin(). It walks the same
# steps as that tween and must change with it: the shower Mason calls him into times its landings
# around these before he has picked a single spot.
func slam_times(drop_count: int) -> Array[float]:
	var times: Array[float] = []
	var at := 0.0
	for i in drop_count:
		if i > 0:
			at += gap_between_drops
		at += telegraph_time + dive_time
		times.append(at)
		at += hitbox_active_time + maxf(landed_time - hitbox_active_time, 0.0) + sit_up_time + leap_out_time
	return times


func _mark_target() -> void:
	if is_instance_valid(target_player):
		var hurtbox_shape: CollisionShape2D = target_player.hurtBox.get_node("CollisionShape2D")
		var hurtbox := hurtbox_shape.global_transform * hurtbox_shape.shape.get_rect()
		global_position = _landing_spot(target_player.global_position, hurtbox)
	over_mason = keep_out.has_point(global_position)
	target_sprite.z_index = RAISED_MARKER_LAYER if over_mason else 0
	if marker_sort_y != INF:
		_sort_marker_at(marker_sort_y)
	target_sprite.show()
	animation_player.play("pulse")


# The marker's sort point moved to `y` with nothing it draws moving: the offset takes up the difference.
func _sort_marker_at(y: float) -> void:
	var drawn_centre := (target_art_position + target_art_offset * art_scale) * hit_scale
	target_sprite.position.y = y - global_position.y
	target_sprite.offset.y = (drawn_centre.y - target_sprite.position.y) / target_sprite.scale.y


# The bounds keep his landed pose under the back rope, and that alone left a strip along it, and the top
# corners, that no landing reached: a player standing there was never hit (playtest 2026-10-04). A landing
# short of a player above it comes up just far enough to reach MIN_PLAYER_OVERLAP into their hurtbox, the
# reach a landing moved off Mason keeps, and his pose pokes over the rope for it.
func _reach_past_back_rope(spot: Vector2, hurtbox: Rect2) -> Vector2:
	if spot.y <= hurtbox.end.y:
		return spot
	var semi_axes := hit_size() / 2.0 - Vector2.ONE * MIN_PLAYER_OVERLAP
	var across := maxf(0.0, maxf(hurtbox.position.x - spot.x, spot.x - hurtbox.end.x)) / semi_axes.x
	if across >= 1.0:
		return spot
	# A pixel inside the edge the overlap allows, so the reach isn't left to rounding.
	return Vector2(spot.x, minf(spot.y, hurtbox.end.y + semi_axes.y * sqrt(1.0 - across * across) - 1.0))


# The spot nearest the target that's inside the bounds and outside keep_out, pushed straight out through
# one of its edges. Standing right by Mason mustn't make a player safe, so an edge spot that still reaches
# their hurtbox wins, and if there's none Carter lands on them anyway, over Mason.
func _landing_spot(target: Vector2, hurtbox: Rect2) -> Vector2:
	var spot := _reach_past_back_rope(target.clamp(arena_bounds.position, arena_bounds.end), hurtbox)
	if not keep_out.has_point(spot):
		return spot
	# Measured in semi-axes of the oval, shrunk by the overlap it needs: a landing reaches the player when
	# their hurtbox comes within 1 of it.
	var semi_axes := hit_size() / 2.0 - Vector2.ONE * MIN_PLAYER_OVERLAP
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
			var gap := maxf(0.0, maxf(hurtbox.position[axis] - edge, edge - hurtbox.end[axis])) / semi_axes[axis]
			if gap >= 1.0:
				continue
			var spread := semi_axes[across] * sqrt(1.0 - gap * gap)
			var low := maxf(hurtbox.position[across] - spread, arena_bounds.position[across])
			var high := minf(hurtbox.end[across] + spread, arena_bounds.end[across])
			if low > high:
				continue
			candidate[across] = clampf(spot[across], low, high)
			if candidate.distance_to(spot) < reaching.distance_to(spot):
				reaching = candidate
	if reaching != Vector2.INF:
		return reaching
	# Landing over Mason is only worth it if it hits; a player the bounds keep out of reach is pushed out.
	if ((spot.clamp(hurtbox.position, hurtbox.end) - spot) / semi_axes).length() < 1.0:
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
	_fresh_hitbox.call_deferred()


# PlayerDefense judges a parry per hit source and then absorbs that source for blocked_rehit_interval
# (1.0 s). Every slam of a call went off on this one area, and in phase two they come 0.89 s apart, so a
# parried slam swallowed the next one whole: no hit and no parry (playtest 2026-10-04). Each slam gets an
# area of its own, made once the last one is off.
func _fresh_hitbox() -> void:
	var spent: Area2D = hitbox_shape.get_parent()
	var fresh: Area2D = spent.duplicate()
	fresh.set_meta(HitInfo.META_ATTACK, &"carter_elbow_drop")
	spent.add_sibling(fresh)
	hitbox_shape = fresh.get_node(NodePath(hitbox_shape.name))
	spent.queue_free()


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
