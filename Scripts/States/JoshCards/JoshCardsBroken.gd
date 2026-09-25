extends "res://Scripts/BossBroken.gd"

# Josh with his Break gauge full (BossBroken), hunched over his knees in the pose his recovery uses, so
# the box traced off it is the one the player punches. Broken mid-ride, he is dropped off his card: it
# vanishes under him and he falls onto the floor point he slides to, gathering speed as a fall does,
# and lands with his landing thud. His state machine builds this in code (JoshCardsStateMachine).

var start_height := 0.0
var falling := false


# Cut in at once. A finisher's shove still running would go on moving his floor point under the slide.
# Falling, he stays drawn over the ropes until he lands, as he does diving off his card: at floor depth
# the top rope would cross his face as he drops from the top row.
func _pose_in() -> void:
	if body.knock_tween:
		body.knock_tween.kill()
	start_height = body.height
	falling = start_height > 0.0
	body.fly_velocity = Vector2.ZERO
	body.hide_glider()
	body.set_air_draw(falling)
	body.face_player()
	body.play_anim(&"hit", &"recover")


func _feet() -> Vector2:
	return body.ground_position


func _set_feet(point: Vector2, weight: float) -> void:
	body.ground_position = point
	body.height = start_height * (1.0 - weight * weight)
	body.place()
	if falling and weight >= 1.0:
		falling = false
		body.set_air_draw(false)
		body.land_sfx_player.play()


# A slide longer than the drive's beat, from a Break taken as he turns off the side of the screen, goes at
# his dive speed, so he is seen coming in rather than snapping there.
func _slide_time() -> float:
	return maxf(DRIVE_TIME, slide_from.distance_to(slide_to) / state_machine.dive_speed)


# His ground, narrowed so the whole juggle this window pays out is drawn inside the ropes: a Break by a
# rope slides him in off it as he goes down (JoshCardsScript.juggle_x_range).
func _feet_bounds() -> Rect2:
	var ground: Rect2 = body.ground_bounds(0.0)
	var inside: Vector2 = body.juggle_x_range()
	var left := maxf(ground.position.x, inside.x)
	var right := minf(ground.end.x, inside.y)
	return Rect2(left, ground.position.y, right - left, ground.size.y)


func _head_point() -> Vector2:
	return body.get_daze_anchor()


func _time_up() -> void:
	state_machine.start_cycle()


func _on_flinch() -> void:
	body.play_anim(&"hit", &"recover")


# His hurtbox rides on Air, as high as he is drawn, so it comes down the height he falls as well as
# sliding with his feet.
func _hurtbox_shift(from: Vector2, to: Vector2) -> Vector2:
	return to - from + Vector2(0.0, roundf(start_height))
