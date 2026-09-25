extends "res://Scripts/BossBroken.gd"

# Matt with his Break gauge full (BossBroken): winded where he stands, in his recover pose, open to
# punches. His origin is his feet. A Break at the Glass Row's station, high up the ring, slides him down
# to his juggle floor (about y 485) before the window opens. MattStateMachine builds it, beside his
# Juggled.

const MattArtLayout := preload("res://Scripts/MattArtLayout.gd")


# Cut in at once, rather than through play_state_anim(), which lets a one-shot finish first: a Break out
# of a Trueshot or a stomp would hold its fire or slam pose, whose last frame is a second long, into the
# window.
func _pose_in() -> void:
	body.show_body()
	body.state_anim = &"recover"
	body.play_anim(&"recover")


func _feet() -> Vector2:
	return body.global_position


func _set_feet(point: Vector2, _weight: float) -> void:
	body.global_position = point


func _feet_bounds() -> Rect2:
	return state_machine.STAND_RECT


func _head_point() -> Vector2:
	return body.global_position + MattArtLayout.daze_offset(&"recover")


func _on_flinch() -> void:
	body.play_anim(&"hit", &"recover")


func _time_up() -> void:
	state_machine.on_child_transition(self, "Idle")
