extends "res://Scripts/BossBroken.gd"

# Liam Broken (BossBroken): his gauge filled in a window on the mat, or a Break he banked on his pillar was cashed as he
# fell. He is already on the floor, where a juggle has its room, so he stays where he lies. The window is his downed pose;
# his time up, he gets up (LiamGetUp).


# His hurtbox stays the one he lies in until he stands (LiamGetUp): a juggle's uppercuts are reached against it.
func _pose_in() -> void:
	body.set_body_box(&"downed")
	body.play_anim(&"downed")


func _feet() -> Vector2:
	return body.global_position


func _set_feet(point: Vector2, _weight: float) -> void:
	body.global_position = point
	body.place()


func _feet_bounds() -> Rect2:
	return state_machine.stand_rect()


func _head_point() -> Vector2:
	return body.pose_point(&"daze", &"downed")


func _time_up() -> void:
	state_machine.window_over(self)


func _on_flinch() -> void:
	body.play_anim(&"downed_hit", &"downed")
