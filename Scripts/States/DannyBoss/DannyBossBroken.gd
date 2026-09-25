extends "res://Scripts/BossBroken.gd"

# Danny with his Break gauge full (BossBroken): dazed where the Break caught him, mid-attack if need be
# (DannyBossStateMachine.enter_broken), and open to punches for BREAK.broken_time. A 3-hit combo here starts
# the finisher, and this is the only window that pays its three-bar mash and his juggle. His juggle floor is
# about y 746, far under HOME, so a Break almost always slides him down to it first.

const Layout := preload("res://Scripts/DannyBossArtLayout.gd")


# Cut in at once, rather than through play_state_anim(), which lets a one-shot finish first. Down from the
# air too: show_body() takes his lift off. He faces the player, as every boss's Break does.
func _pose_in() -> void:
	body.show_body()
	body.sprite.position = body.sprite_base_position
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
	return state_machine.WALK_RECT


# His own daze anchor asks whether he is Broken yet, which he isn't until this state's Enter is over.
func _head_point() -> Vector2:
	return body.crown_point(&"broken") - Vector2(0, Layout.DAZE_GAP)


func _on_flinch() -> void:
	body.play_anim(&"hit", &"broken")


func _time_up() -> void:
	state_machine.on_child_transition(self, "Idle")
