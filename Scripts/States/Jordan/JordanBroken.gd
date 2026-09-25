extends "res://Scripts/BossBroken.gd"

# Jordan with his Break gauge full (BossBroken): down on one knee by the box he dropped, the defeat's
# kneel held. At his spot his soles are on y 506, already lower than his juggle floor (about 476), so
# the Break's slide leaves him where he is. JordanStateMachine builds it, beside his Juggled.

const JordanArtLayout := preload("res://Scripts/JordanArtLayout.gd")

# The inside edges of the ropes, as every other fight measures them.
const FEET_BOUNDS := Rect2(113, 114, 1692, 853)


# Cut in at once, rather than through play_state_anim(), which lets a one-shot finish first: a Break
# out of the summon would otherwise crouch and punch the air before he went down. A redirected blast
# that fills the gauge has just leaned him back on a rotation tween, which would tip the kneel and
# leave the stars off his head.
func _pose_in() -> void:
	if body.stagger_tween:
		body.stagger_tween.kill()
	body.sprite.rotation = 0.0
	body.state_anim = &"broken"
	body.play_anim(&"broken")


func _feet() -> Vector2:
	return body.to_global(JordanArtLayout.FLOOR_POINT)


func _set_feet(point: Vector2, _weight: float) -> void:
	body.global_position += point - _feet()


func _feet_bounds() -> Rect2:
	return FEET_BOUNDS


func _head_point() -> Vector2:
	return body.global_position + JordanArtLayout.broken_daze_anchor()


func _time_up() -> void:
	state_machine.on_child_transition(self, "Idle")
