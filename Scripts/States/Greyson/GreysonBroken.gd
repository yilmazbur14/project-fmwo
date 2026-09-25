extends "res://Scripts/BossBroken.gd"

# Greyson with his Break gauge full (BossBroken): dazed where the Break caught him, mid-attack if need be
# (GreysonStateMachine.enter_broken), and open to punches for BREAK.broken_time. A 3-hit combo here starts the
# finisher; once his juggle is on, this is the only window that pays its three-bar mash. He stands on HOME's row
# or below it, under his juggle floor (about 524), so a Break never slides him.

const Layout := preload("res://Scripts/GreysonArtLayout.gd")


# Cut in at once, rather than through play_state_anim(), which lets a one-shot finish first. Whole and visible
# too, since a Break can land mid-teleport. He faces the player, as every boss's Break does.
func _pose_in() -> void:
	body.show_body()
	body.set_body_box(&"idle")
	var player := _player()
	if player:
		body.face_toward(player.global_position)
	body.state_anim = &"broken"
	body.play_anim(&"broken")


func _feet() -> Vector2:
	return body.global_position


func _set_feet(point: Vector2, _weight: float) -> void:
	body.global_position = point.round()


func _feet_bounds() -> Rect2:
	return state_machine.STAND_RECT


# His own daze anchor asks whether he is Broken yet, which he isn't until this state's Enter is over.
func _head_point() -> Vector2:
	return body.crown_point(&"broken") - Vector2(0, Layout.DAZE_GAP)


func _on_flinch() -> void:
	body.play_anim(&"hit", &"broken")


func _time_up() -> void:
	state_machine.on_child_transition(self, "Idle")
