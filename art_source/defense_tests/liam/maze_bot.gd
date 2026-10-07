extends RefCounted

# liam_maze_bot: the stream bot. Attack 2's walls on the ice, played on real inputs (arrow keys only). From x 960 on the
# bottom row, where every attack starts (the reset to the bottom middle), on runs 0-3 (every gap order and round
# again), a bot waits for the heave and then steers by the walls as they stand this frame, a telling one included:
# across its corridor to the gap of the wall above it, up through the gap to just over the wall, and again until no
# wall is over it; then across to x 960 in the front corridor and up to the front spot. Legs are along x or along y; it
# brakes to 300 px/s before turning up a gap, to a stop just over each wall and at the spot, and keeps to the leg's line
# with the keys across it. It must reach the front spot within tremor_time of the heave without a ridge hit. Campers standing still through
# a whole run at (960, 900) and at (150, 900) must be hit at least once (the hits are logged).

const Common := preload("res://art_source/defense_tests/liam/common.gd")
const Patterns := preload("res://Scripts/LiamTremorPatterns.gd")
const LiamTremorBlock := preload("res://Scripts/LiamTremorBlock.gd")

const START_X := 960.0
const RUNS := 4
const CAMPERS := [Vector2(960, 900), Vector2(150, 900)]
const TURN_SPEED := 300.0
# How close along a leg counts as its corner reached, and how close to the spot as there.
const ARRIVE := 8.0
const AT_SPOT := 30.0
# The line across a leg is held to within this, easing back at up to LINE_SPEED.
const LINE_SLACK := 6.0
const LINE_GAIN := 4.0
const LINE_SPEED := 300.0
# A wall counts as got past once the player's centre is this far over its top; through its gap they aim this far over,
# and head up once they are within GAP_SLACK of its centre (the gap is 240 px, the player 36), rather than dithering on
# the ice to stop dead on it.
const CLEARED := 50.0
const OVER := 55.0
const GAP_SLACK := 60.0
# Half the player's body up and down, with room: the most a corridor's line keeps off its walls.
const HALF_BODY := 45.0


static func run(t) -> void:
	await Common.enter(t)
	t.track()
	for run in RUNS:
		var result: Dictionary = await attempt(t, run)
		t.check(result.reached and result.hits == 0, "run %d from x %.0f: at the front spot in %.2f s, %d ridge hits" % [run, START_X, result.time, result.hits])
	for spot: Vector2 in CAMPERS:
		var hits: int = await camp(t, 0, spot)
		t.check(hits >= 1, "a camper standing still at %s through a whole run is hit (%d)" % [spot, hits])


# A whole run with the player standing still at `spot`: the ridge hits it costs.
static func camp(t, run: int, spot: Vector2) -> int:
	await Common.clear(t)
	await Common.fresh(t, spot)
	t.sm.tremor_runs = run
	var hits_before: int = t.events_of("HIT", &"liam_tremor").size()
	Common.start(t, "Tremors")
	var tremors: Node = t.sm.states["Tremors"]
	await t.wait_until(func(): return tremors.beats.has(&"timeout"), 60 * 20)
	var hits: int = t.events_of("HIT", &"liam_tremor").size() - hits_before
	t.log_p("standing still at %s through run %d: %d ridge hits, ended at %s" % [spot, run, hits, t.player.global_position])
	Common.hold(t)
	return hits


# Run `run`, the player waiting on the bottom row at START_X until the heave, then the bot.
static func attempt(t, run: int) -> Dictionary:
	await Common.clear(t)
	await Common.fresh(t, Vector2(START_X, Patterns.BOTTOM_ROW_Y))
	t.sm.tremor_runs = run
	Common.start(t, "Tremors")
	var tremors: Node = t.sm.states["Tremors"]
	await t.wait_until(func(): return tremors.beats.has(&"heave"), 120)
	var result: Dictionary = await drive(t, tremors, roundi(t.sm.tremor_time * 60.0))
	t.log_p("run %d from x %.0f: %s in %.2f s, %d ridge hits, walls %s" % [run, START_X, "at the spot" if result.reached else "NOT at the spot", result.time, result.hits, tremors.walls.map(func(w): return "k%d gap %.0f" % [w.k, w.gap])])
	Common.keys_up(t)
	Common.hold(t)
	return result


# Every wall standing this frame, a telling one too: {top, bottom, gap}.
static func standing(tremors: Node) -> Array:
	var out := []
	for wall in tremors.walls:
		if not wall.has("blocks"):
			continue
		var blocks: Array = wall.blocks.filter(func(b): return is_instance_valid(b) and b.phase != LiamTremorBlock.Phase.CRUMBLE)
		if blocks.is_empty():
			continue
		out.append({top = blocks[0].rect.position.y, bottom = blocks[0].rect.end.y, gap = wall.gap})
	return out


# Where the bot heads this frame from `at`: [target, axis, the speed it may round the corner at].
static func leg(t, walls: Array, at: Vector2) -> Array:
	var next: Variant = null
	for wall: Dictionary in walls:
		if at.y > wall.top - CLEARED and (next == null or wall.top > next.top):
			next = wall
	if next == null:
		if absf(at.x - START_X) > GAP_SLACK:
			return [Vector2(START_X, at.y), Vector2(signf(START_X - at.x), 0.0), TURN_SPEED]
		return [t.sm.FRONT_SPOT, Vector2(0.0, signf(t.sm.FRONT_SPOT.y - at.y)), 0.0]
	if absf(at.x - next.gap) > GAP_SLACK and at.y > next.bottom:
		# Across its corridor: midway between this wall and the one under it (or the bottom of the ring).
		var lower: float = t.sm.march_floor_y
		for wall: Dictionary in walls:
			if wall.top > next.bottom:
				lower = minf(lower, wall.top)
		var line := clampf((next.bottom + lower) / 2.0, next.bottom + HALF_BODY, maxf(lower - HALF_BODY, next.bottom + HALF_BODY))
		return [Vector2(next.gap, line), Vector2(signf(next.gap - at.x), 0.0), TURN_SPEED]
	# Up through it, stopping just over it: coming up at speed on the ice would carry them into the wall above.
	return [Vector2(next.gap, next.top - OVER), Vector2(0.0, -1.0), 0.0]


static func drive(t, tremors: Node, deadline: int) -> Dictionary:
	var hits_before: int = t.events_of("HIT", &"liam_tremor").size()
	var accel: float = t.sm.ice_accel
	var frames := 0
	var spot: Vector2 = t.sm.FRONT_SPOT
	while frames < deadline:
		var at: Vector2 = t.player.global_position
		if at.distance_to(spot) <= AT_SPOT:
			break
		var heading: Array = leg(t, standing(tremors), at)
		var target: Vector2 = heading[0]
		var axis: Vector2 = heading[1]
		if axis == Vector2.ZERO:
			axis = Vector2(0.0, -1.0)
		var along: float = (target - at).dot(axis)
		var speed: float = t.player.velocity.dot(axis)
		var end_speed: float = heading[2]
		var braking: float = (speed * speed - end_speed * end_speed) / (2.0 * accel) if speed > end_speed else 0.0
		var forward := along > braking + speed * 2.0 / 60.0
		_hold(t, axis, 1 if forward else -1)
		var across := Vector2(absf(axis.y), absf(axis.x))
		var off: float = (at - target).dot(across)
		var drift: float = t.player.velocity.dot(across)
		var want: float = clampf(-LINE_GAIN * off, -LINE_SPEED, LINE_SPEED) if absf(off) > LINE_SLACK else 0.0
		_hold(t, across, 1 if drift < want - 30.0 else (-1 if drift > want + 30.0 else 0))
		await t.physics_frame
		frames += 1
	Common.keys_up(t)
	var reached: bool = t.player.global_position.distance_to(spot) <= AT_SPOT
	return {"reached": reached, "time": frames / 60.0, "hits": t.events_of("HIT", &"liam_tremor").size() - hits_before}


# Along `axis` (a unit axis vector): +1 its own key, -1 the opposite one, 0 neither.
static func _hold(t, axis: Vector2, way: int) -> void:
	var plus: int = KEY_RIGHT if axis.x != 0.0 else KEY_DOWN
	var minus: int = KEY_LEFT if axis.x != 0.0 else KEY_UP
	var positive := axis.x > 0.0 or axis.y > 0.0
	var forward_key: int = plus if positive else minus
	var back_key: int = minus if positive else plus
	if way > 0:
		t.release(back_key)
		t.press(forward_key)
	elif way < 0:
		t.release(forward_key)
		t.press(back_key)
	else:
		t.release(forward_key)
		t.release(back_key)
