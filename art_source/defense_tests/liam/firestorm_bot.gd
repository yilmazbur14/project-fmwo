extends RefCounted

# liam_firestorm_bot: a bot walking from the bottom of the ring to his front spot through attack 3, logged rather than
# asserted, except that it gets there. From x 240, 960 and 1680 at y 900, from RELEASE on (his downdraft holds it down
# till then, the wall of fire): it walks at the front spot leaning into the pull, and dashes whenever a fire ring's band
# comes within DASH_RANGE px of its feet. It must reach the front spot inside firestorm_time. Entered straight on his test scene (LiamFirestorm isn't in the rotation yet).

const Common := preload("res://art_source/defense_tests/liam/common.gd")
const FirestormLayout := preload("res://Scripts/LiamFirestormLayout.gd")
const CombinedLayout := preload("res://Scripts/BixbyCombinedArtLayout.gd")

const STARTS := [Vector2(240, 900), Vector2(960, 900), Vector2(1680, 900)]
const DASH_RANGE := 60.0
const ARRIVED := 30.0
const WALK := 600.0


static func run(t) -> void:
	await Common.enter(t)
	t.track()
	var all_reached := true
	for start: Vector2 in STARTS:
		var reached: bool = await walk(t, start)
		all_reached = all_reached and reached
	t.check(all_reached, "from every start the bot reaches the front spot inside firestorm_time")
	Common.hold(t)


static func walk(t, start: Vector2) -> bool:
	await Common.clear(t)
	await Common.fresh(t, start)
	var fs: Node = t.sm.states["Firestorm"]
	Common.start(t, "Firestorm")
	await t.wait_until(func(): return fs.beats.has(&"release"), 180)
	var hits_before: int = t.events_of("HIT").size()
	var begun: float = fs.clock
	var dashes := 0
	var dashed_for := {}
	var held: Array = []
	var reached := false
	for i in roundi(t.sm.firestorm_time * 60.0):
		var at: Vector2 = t.player.global_position
		if at.distance_to(t.sm.FRONT_SPOT) <= ARRIVED:
			reached = true
			break
		var want: Vector2 = (t.sm.FRONT_SPOT - at).normalized() * WALK - fs.pull_at(at)
		var keys := arrows(want)
		for code in held:
			if not keys.has(code):
				t.release(code)
		for code in keys:
			if not held.has(code):
				t.press(code)
		held = keys
		var ring: Node2D = coming_ring(fs, at + FirestormLayout.FEET)
		if ring != null and not dashed_for.has(ring.get_instance_id()):
			dashed_for[ring.get_instance_id()] = true
			t.tap(KEY_W)
			dashes += 1
		await t.wait(1)
	Common.keys_up(t)
	var took: Array = t.events_of("HIT").slice(hits_before)
	var ring_hits := took.filter(func(e): return e.id == &"liam_fire_quake").size()
	var core_hits := took.filter(func(e): return e.id == &"liam_fire_tornado").size()
	t.log_p("from %s: %s after %.2f s, %d dashes, %d ring hits, %d core hits" % [start, "reached" if reached else "NOT reached",
		fs.clock - begun, dashes, ring_hits, core_hits])
	Common.hold(t)
	return reached


# The arrow keys nearest `want`: each axis pressed when it is more than 22.5 degrees of the way round.
static func arrows(want: Vector2) -> Array:
	var keys := []
	var along := want.normalized()
	if along.x < -0.38:
		keys.append(KEY_LEFT)
	elif along.x > 0.38:
		keys.append(KEY_RIGHT)
	if along.y < -0.38:
		keys.append(KEY_UP)
	elif along.y > 0.38:
		keys.append(KEY_DOWN)
	return keys


# A live ring whose band is on the feet or coming at them from within DASH_RANGE, on the floor (the flattening undone).
static func coming_ring(fs: Node, feet: Vector2) -> Node2D:
	for ring in fs.rings:
		if not is_instance_valid(ring) or ring.dying:
			continue
		var off: Vector2 = feet - ring.global_position
		var d := Vector2(off.x, off.y / CombinedLayout.FLOOR_FLATTEN).length()
		var half := CombinedLayout.RING_HURT_HALF_WIDTH
		if d > ring.radius - half and d - (ring.radius + half) <= DASH_RANGE:
			return ring
	return null
