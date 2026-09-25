extends "res://Scripts/BossBroken.gd"

# Beast Bixby Broken (BossBroken). Caught in the air, he falls out of it on his landing's curve onto the
# floor a juggle needs; caught on the ground higher up the arena than that, he is bounced down to it in a
# short hop rather than slid along the mat. Either way he comes down on the landing's impact and slumps
# into his recovery for the window, and takes off into his next cycle when it's over.

const BixbyBeastArtLayout := preload("res://Scripts/BixbyBeastArtLayout.gd")

const HOP_TIME := 0.35
# The top of the hop's arc over the floor, in px.
const HOP_HEIGHT := 60.0
# BixbyBeastLand's impact shake.
const LANDING_SHAKE := 12.0
const LANDING_SHAKE_STEPS := 5
const LANDING_SHAKE_STEP_TIME := 0.028

enum Way { STAY, FALL, HOP }

var way := Way.STAY
var start_height := 0.0
# Whether he has come down, which a punch can't cut short.
var down := false


func _pose_in() -> void:
	start_height = body.height
	body.fly_velocity = Vector2.ZERO
	body.stop_sprite_shake()
	down = false
	if start_height > 0.0:
		way = Way.FALL
		body.play_anim(&"land", &"recover")
	elif _slide_target().distance_to(body.ground_position) >= 1.0:
		way = Way.HOP
		body.play_anim(&"hop")
	else:
		way = Way.STAY
		down = true
		body.play_anim(&"recover")


# Where BossBroken's slide will put his feet, worked out the same way before it starts, since his pose
# depends on whether he moves.
func _slide_target() -> Vector2:
	var to: Vector2 = _feet()
	to.y = maxf(to.y, state_machine.states["Juggled"].floor_y())
	var bounds := _feet_bounds()
	return to.clamp(bounds.position, bounds.end).round()


func _feet() -> Vector2:
	return body.ground_position


func _set_feet(point: Vector2, weight: float) -> void:
	body.ground_position = point
	match way:
		Way.FALL:
			body.height = start_height * (1.0 - weight * weight)
		Way.HOP:
			body.height = 4.0 * HOP_HEIGHT * weight * (1.0 - weight)
	body.place()
	if weight >= 1.0 and not down:
		_touch_down()


func _touch_down() -> void:
	down = true
	if way == Way.HOP:
		body.play_anim(&"land", &"recover", 1)
	body.land_sfx_player.play()
	body.shake_screen(LANDING_SHAKE, LANDING_SHAKE_STEPS, LANDING_SHAKE_STEP_TIME)


func _feet_bounds() -> Rect2:
	return body.ground_bounds(0.0)


func _head_point() -> Vector2:
	return body.get_daze_anchor()


func _time_up() -> void:
	state_machine.on_child_transition(self, "Takeoff")


# The fall's frame 0 lasts as long as the fall, as it does in BixbyBeastLand.
func _slide_time() -> float:
	match way:
		Way.FALL:
			return BixbyBeastArtLayout.time_to_step(&"land", 1)
		Way.HOP:
			return HOP_TIME
	return 0.0


# His hurtbox hangs off Air, which comes down with his height as well as moving with his feet.
func _hurtbox_shift(from: Vector2, to: Vector2) -> Vector2:
	return to - from + Vector2(0.0, start_height)


func _on_flinch() -> void:
	if down:
		body.play_anim(&"hit", &"recover")
