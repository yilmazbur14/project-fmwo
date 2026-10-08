extends RefCounted

# The blocker for `blocks fight=danny` (coder B). The blocks mode holds the guard up on one spot for its whole run.
# Since the 2026-09-24 playtest, every landing of Danny's string leaves a puddle under the player that roots feet
# still on it as it arms, and a root in the string seals the guard (DannyBossSlams, DannyBossSlamPuddle). A real
# player blocks, then steps off, and so does this one: whenever a puddle still arming lies under the feet, the spot
# the mode holds walks off it at the player's walking speed to the nearest floor clear of every puddle, and the
# guard takes the next landing there. What the mode checks, how the guard takes his hits while the player isn't
# rooted, is untouched.

const BODY := "Arena/DannyBossScene/DannyBossCharacterBody"
# The player's 600 px/s, a step at a time.
const STEP := 10.0
# How far outside a puddle's trigger the feet step to, and how far inside the ropes they stay.
const CLEAR := 24.0
const ROPE_ROOM := 30.0
# The steps tried, nearest first, in px from the spot held.
const REACHES: Array[float] = [60.0, 90.0, 120.0, 160.0, 200.0, 260.0]
const DIRECTIONS := 16

# His state machine: the mode doesn't set the suite's own.
var sm: Node
# Where the spot is walking to, or INF while it holds.
var target := Vector2.INF
# For the log: how many times it stepped off.
var steps := 0


# The spot to hold this step, `spot` the one held last step.
func next_spot(t, spot: Vector2) -> Vector2:
	if sm == null:
		sm = t.current_scene.get_node(BODY).state_machine
	if target == Vector2.INF and _arming_underfoot():
		target = _clear_spot(t, spot)
		steps += 1
	if target != Vector2.INF:
		spot = spot.move_toward(target, STEP)
		if spot == target:
			target = Vector2.INF
	return spot


# Nothing of his left on the floor for the mode's direction rules, which send their own hits at the player.
func clear_floor(t) -> void:
	if sm == null:
		sm = t.current_scene.get_node(BODY).state_machine
	sm.clear_puddles()


func _arming_underfoot() -> bool:
	var feet: Vector2 = sm.player_feet()
	for puddle in sm.live_puddles():
		if not puddle.armed and puddle.contains_feet(feet):
			return true
	return false


func _clear_spot(t, spot: Vector2) -> Vector2:
	var feet_offset: Vector2 = sm.player_feet() - t.player.global_position
	var inside: Rect2 = sm.ROPES.grow(-ROPE_ROOM)
	var puddles: Array = sm.live_puddles()
	for reach in REACHES:
		for i in DIRECTIONS:
			var to := spot + Vector2.from_angle(TAU * i / DIRECTIONS) * reach
			var feet := to + feet_offset
			if not inside.has_point(feet):
				continue
			var clear := true
			for puddle in puddles:
				var half: Vector2 = puddle.radii + Vector2.ONE * CLEAR
				var d: Vector2 = feet - puddle.global_position
				if pow(d.x / half.x, 2.0) + pow(d.y / half.y, 2.0) <= 1.0:
					clear = false
					break
			if clear:
				return to
	return spot
