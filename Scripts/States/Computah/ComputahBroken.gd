extends "res://Scripts/BossBroken.gd"

# Computah with his Break gauge full (BossBroken): he collapses onto the mat and lies in the drop's
# floor loop, open to one 3-punch combo that starts the three-bar finisher. He opens the way every
# window of his opens (ComputahStateMachine.set_open), so can_be_dazed(), take_punch() and
# end_recovery() read this as one of his windows. ComputahStateMachine builds it in code.
# A punch doesn't stand him up: computah_hit is a standing pose, so the base's flinch does nothing here
# and _hit_feedback()'s flash and jolt land on the floor frame he is on. The stars and the finisher's
# daze then always sit on his downed head.

const Layout := preload("res://Scripts/ComputahArtLayout.gd")


func _pose_in() -> void:
	body.velocity = Vector2.ZERO
	body.set_solid(true)
	body.set_target_active(true)
	body.show_battery(false)
	body.set_body_box(&"down")
	body.begin_window(body.MAX_HITS_PER_WINDOW)
	state_machine.set_open(true)
	body.play_anim(&"collapse", &"down")


func _pose_out() -> void:
	state_machine.set_open(false)
	body.set_body_box(&"idle")


# The finisher's uppercut ends the window early (ComputahStateMachine.end_window hands it here).
func end_window(stagger_time: float) -> bool:
	state_machine.end_break(stagger_time)
	return true


func _time_up() -> void:
	body.play_anim(&"reboot", &"idle")
	state_machine.on_child_transition(self, "Idle")


func _feet() -> Vector2:
	return body.global_position


func _set_feet(point: Vector2, _weight: float) -> void:
	body.global_position = point


func _feet_bounds() -> Rect2:
	return state_machine.runner_bounds()


func _head_point() -> Vector2:
	var texel: Vector2 = Layout.C_DOWN_HEAD
	if body.current_anim == &"collapse":
		texel = Layout.C_COLLAPSE_HEADS.get(body.sprite.frame, texel)
	return body.frame_point(texel) + Vector2(0, -Layout.DAZE_GAP)
