extends Node2D

signal finished

const TELEGRAPH_TIME := 0.55
const DIVE_TIME := 0.35
const DIVE_FRAME_INTERVAL := 0.08
const HITBOX_ACTIVE_TIME := 0.15
const LANDED_TIME := 0.2
const SIT_UP_TIME := 0.12
const LEAP_OUT_TIME := 0.4
const GAP_BETWEEN_DROPS := 0.35

const DIVE_START_POSITION := Vector2(420, -1000)
const LEAP_OUT_POSITION := Vector2(-300, -1000)

const LANDED_FRAME := 2
const SIT_UP_FRAME := 3
const LEAP_OUT_FRAME := 4

@export var target_sprite: Sprite2D
@export var carter_sprite: Sprite2D
@export var impact_sprite: Sprite2D
@export var hitbox_shape: CollisionShape2D
@export var animation_player: AnimationPlayer
@export var slam_sfx: AudioStreamPlayer

var target_player: Node2D
var arena_bounds: Rect2
var keep_out: Rect2


func _ready() -> void:
	animation_player.animation_finished.connect(_on_animation_player_animation_finished)


func begin(drop_count: int, player: Node2D, bounds: Rect2, avoid: Rect2) -> void:
	target_player = player
	arena_bounds = bounds
	keep_out = avoid
	# Every drop lives on one tween so the timings can't drift apart, and the
	# whole attack dies with this node if Mason frees it mid-sequence.
	var sequence := create_tween()
	for i in drop_count:
		if i > 0:
			sequence.tween_interval(GAP_BETWEEN_DROPS)
		sequence.tween_callback(_mark_target)
		sequence.tween_interval(TELEGRAPH_TIME)
		sequence.tween_callback(_start_dive)
		sequence.tween_property(carter_sprite, "position", Vector2.ZERO, DIVE_TIME).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
		sequence.parallel().tween_method(_set_dive_frame, 0.0, DIVE_TIME, DIVE_TIME)
		sequence.tween_callback(_land)
		sequence.tween_interval(HITBOX_ACTIVE_TIME)
		sequence.tween_callback(_disable_hitbox)
		sequence.tween_interval(LANDED_TIME - HITBOX_ACTIVE_TIME)
		sequence.tween_callback(carter_sprite.set_frame.bind(SIT_UP_FRAME))
		sequence.tween_interval(SIT_UP_TIME)
		sequence.tween_callback(carter_sprite.set_frame.bind(LEAP_OUT_FRAME))
		sequence.tween_property(carter_sprite, "position", LEAP_OUT_POSITION, LEAP_OUT_TIME).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
		sequence.tween_callback(carter_sprite.hide)
	sequence.tween_callback(_finish)


func _mark_target() -> void:
	if is_instance_valid(target_player):
		global_position = _landing_spot(target_player.global_position)
	target_sprite.show()
	animation_player.play("pulse")


# Nearest spot inside the bounds that is outside keep_out, pushing straight out through one of its edges.
func _landing_spot(target: Vector2) -> Vector2:
	var spot := target.clamp(arena_bounds.position, arena_bounds.end)
	if not keep_out.has_point(spot):
		return spot
	var best := spot
	var best_distance := INF
	for candidate in [
		Vector2(keep_out.position.x - 1.0, spot.y),
		Vector2(keep_out.end.x, spot.y),
		Vector2(spot.x, keep_out.position.y - 1.0),
		Vector2(spot.x, keep_out.end.y),
	]:
		var clamped: Vector2 = candidate.clamp(arena_bounds.position, arena_bounds.end)
		if not keep_out.has_point(clamped) and clamped.distance_to(spot) < best_distance:
			best = clamped
			best_distance = clamped.distance_to(spot)
	return best


func _start_dive() -> void:
	carter_sprite.position = DIVE_START_POSITION
	carter_sprite.frame = 0
	carter_sprite.show()


func _set_dive_frame(elapsed: float) -> void:
	carter_sprite.frame = int(elapsed / DIVE_FRAME_INTERVAL) % 2


func _land() -> void:
	carter_sprite.frame = LANDED_FRAME
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
