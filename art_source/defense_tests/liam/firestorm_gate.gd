extends RefCounted

# liam_firestorm_gate: the Firestorm's wall of fire (the user's option A, 2026-10-04). Before it, a walk straight up
# from the reset spot punched his pillar at IGNITION, 1.48 s in, unhurt. Now his blow's downdraft holds the player at the
# bottom while the tornados rise in a line between them and him and catch fire; at RELEASE (IGNITION + wall_release) it
# lets go and the pillar opens, its shield bursting; wall_hold later the line breaks up and the storm roams as before.
# On his test scene, entered straight.
#   hold      holding Up from x 150, 960 and 1770 at y 900, and again dashing up every 0.6 s, unhurt until RELEASE: once
#             his blow's throw is over (launch_time + 0.1 s after it), the player's centre never above y 760 walking, and
#             never above downdraft_launch_above (700) dashing; a player at the front spot or at (400, 520) as it
#             starts is thrown down to RESET_SPOT, sealed, and unhurt
#   open      shielded from its start, and his pillar refuses a hit at 1.5 s; it opens within a frame of RELEASE with
#             its shield bursting once, and the downdraft has stopped by the frame after
#   straight  the laziest route: from (x, 900) for x across the ring, walking at the front spot from RELEASE + 0, 0.4 and
#             0.8 s with no dash, punching once it is open: every run is hit before its punch lands (x 960 at + 0 is
#             logged on its own: the playtester's measure)
#   breakup   the same walk from x 700, 960 and 1217 leaving 0.2 s before BREAK and 0.3, 0.8 and 1.3 s after: each is
#             hit, or doesn't cut it within 2.5 s
#   routes    fair: from RESET_SPOT, walking up 0.20, 0.25 and 0.30 s after RELEASE, stopping (against the pull) with the
#             foot of their hurtbox (what a ring tests) HOVER_MARGIN under the lens beside his front spot (between the
#             two wall tornados round it: the middle one at 4, the one left of the middle tornado at 5), and
#             dashing up through it 0, 3 and 6 frames later: all 9 reach his pillar and cut it within RELEASE + 1.5 s, 7
#             or more unhurt. Logged only: the same up the outermost lenses; walking straight into the lens
#             and dashing on the way, 0, 3 and 6 frames after the foot reaches LENS_MARGIN under it (the tuning sweep
#             of 2026-10-04: clean only within about 2 frames, the pull carrying the walker into the band); and a
#             first-timer doing that 0.25 +- 0.05 s after RELEASE, up to 9 frames late.

const Common := preload("res://art_source/defense_tests/liam/common.gd")
const FirestormLayout := preload("res://Scripts/LiamFirestormLayout.gd")
const FirestormBot := preload("res://art_source/defense_tests/liam/firestorm_bot.gd")

const HOLD_XS := [150.0, 960.0, 1770.0]
const HOLD_TOP := 760.0
const HOLD_TOP_DASHING := 700.0
const LAUNCHED_FROM := [Vector2(960, 402), Vector2(400, 520)]
const STRAIGHT_XS := [150.0, 280.0, 446.0, 703.0, 830.0, 960.0, 1090.0, 1217.0, 1473.0, 1640.0, 1770.0]
const STRAIGHT_LEAVE := [0.0, 0.4, 0.8]
const BREAKUP_XS := [700.0, 960.0, 1217.0]
const BREAKUP_LEAVE := [-0.2, 0.3, 0.8, 1.3]
const BREAKUP_LIMIT := 2.5
const ROUTE_LEAVE := [0.20, 0.25, 0.30]
const ROUTE_LATE := [0, 3, 6]
const ROUTE_LIMIT := 1.5
const ROUTES_CLEAN := 7
const LENS_MARGIN := 10.0
const HOVER_MARGIN := 30.0
const NEAR := 6.0
const PUNCH_EVERY := 18
const START_Y := 900.0


static func run(t) -> void:
	await Common.enter(t)
	t.track()
	await hold(t)
	await open(t)
	await straight(t)
	await breakup(t)
	await routes(t)


static func firestorm(t) -> Node:
	return t.sm.states["Firestorm"]


# RELEASE on the Firestorm's own clock.
static func release_at(t) -> float:
	return t.sm.blow_time + t.sm.ignite_time + t.sm.wall_release


static func reset(t, at: Vector2) -> void:
	await Common.clear(t)
	t.sm.pillar_hits = 0
	t.sm.round_hits_taken = 0
	t.boss.pillar.show_hits(0)
	await Common.fresh(t, at)


static func hold(t) -> void:
	for dashing in [false, true]:
		t.log_p("-- held down by the downdraft%s" % (", dashing up every 0.6 s" if dashing else ""))
		for x: float in HOLD_XS:
			await reset(t, Vector2(x, START_Y))
			var fs: Node = firestorm(t)
			var hits_before: int = t.events_of("HIT").size()
			Common.start(t, "Firestorm")
			t.press(KEY_UP)
			var highest := INF
			var f := 0
			while Common.state(t) == "Firestorm" and fs.clock < release_at(t) - 1.0 / 60.0:
				if fs.clock >= fs.beats.get(&"blow", INF) + t.sm.launch_time + 0.1:
					highest = minf(highest, t.player.global_position.y)
				if dashing and f % 36 == 0:
					t.tap(KEY_W)
				f += 1
				t.player.playerHealth = 1000
				await t.physics_frame
			Common.keys_up(t)
			var hits: int = t.events_of("HIT").size() - hits_before
			var top: float = HOLD_TOP_DASHING if dashing else HOLD_TOP
			t.log_p("from x %.0f: highest %.1f after the blow's throw, hits %d" % [x, highest, hits])
			t.check(highest > top and hits == 0, "from x %.0f%s: held below y %.0f until RELEASE, unhurt" % [x, " dashing" if dashing else "", top])
			Common.hold(t)
	t.log_p("-- a player up the ring as it starts")
	for at: Vector2 in LAUNCHED_FROM:
		await reset(t, at)
		var health: int = t.player.playerHealth
		Common.start(t, "Firestorm")
		var launched: bool = await t.wait_until(func(): return t.sm.is_launching(), 60)
		var sealed: bool = t.player.is_action_locked and t.player.lock_seals_guard
		await t.wait_until(func(): return not t.sm.is_launching(), 90)
		var landed: Vector2 = t.player.global_position
		t.log_p("from %s: launched %s, sealed %s, landed %s, health %d -> %d" % [at, launched, sealed, landed, health, t.player.playerHealth])
		t.check(launched and sealed and landed.distance_to(t.sm.RESET_SPOT) <= 1.0 and t.player.playerHealth == health, "from %s: thrown down to %s, sealed and unhurt" % [at, t.sm.RESET_SPOT])
		Common.hold(t)


static func open(t) -> void:
	t.log_p("-- when the pillar opens")
	await reset(t, t.sm.RESET_SPOT)
	var fs: Node = firestorm(t)
	var keep_safe := func(): t.player.is_invincible = true
	t.physics_frame.connect(keep_safe)
	var bursts_before: int = t.boss.pillar.bursts
	Common.start(t, "Firestorm")
	await t.wait(1)
	var shut_at_start: bool = t.boss.pillar.shielded
	await t.wait_until(func(): return fs.clock >= 1.5, 120)
	var refused: bool = not t.sm.take_pillar_hit()
	var still: bool = Common.state(t) == "Firestorm" and t.sm.pillar_hits == 0
	var opened := [-1.0]
	await t.wait_until(func():
		if opened[0] < 0.0 and not t.boss.pillar.shielded:
			opened[0] = fs.clock
		return opened[0] >= 0.0, 120)
	await t.wait(1)
	var drafting: bool = fs.drafting or is_instance_valid(fs.downdraft_fx)
	t.physics_frame.disconnect(keep_safe)
	t.player.is_invincible = false
	var release: float = fs.beats.get(&"release", -1.0)
	t.log_p("shielded at the start %s, a hit at 1.5 s refused %s, open at %.3f s (RELEASE %.3f, due %.3f), bursts %d, still drafting %s" % [shut_at_start, refused, opened[0], release, release_at(t), t.boss.pillar.bursts - bursts_before, drafting])
	t.check(shut_at_start and refused and still, "shielded from its start: a hit at 1.5 s is refused and counts nothing")
	t.check(release >= 0.0 and absf(opened[0] - release) <= 1.0 / 60.0 + 0.001 and absf(release - release_at(t)) <= 1.0 / 60.0 + 0.001, "open within a frame of RELEASE, %.2f s in" % release_at(t))
	t.check(t.boss.pillar.bursts - bursts_before == 1, "its shield bursts once as it opens")
	t.check(not drafting, "and the downdraft has stopped")
	Common.hold(t)


static func straight(t) -> void:
	t.log_p("-- the laziest route: at the front spot from (x, %.0f), no dash" % START_Y)
	var unhurt := []
	for leave: float in STRAIGHT_LEAVE:
		for x: float in STRAIGHT_XS:
			var result: Dictionary = await trial(t, Vector2(x, START_Y), release_at(t) + leave)
			var line := "x %.0f leaving at RELEASE + %.1f: cut %.2f s, hits %s" % [x, leave, result.cut, result.ids]
			if x == 960.0 and leave == 0.0:
				line = "THE PLAYTESTER'S MEASURE: " + line
			t.log_p(line)
			if result.hits == 0:
				unhurt.append("x %.0f + %.1f" % [x, leave])
	t.check(unhurt.is_empty(), "every walk at the front spot is hit before its punch lands (unhurt: %s)" % [unhurt])


static func breakup(t) -> void:
	t.log_p("-- the same walk as the wall breaks up")
	var free := []
	var brk: float = release_at(t) + t.sm.wall_hold
	for leave: float in BREAKUP_LEAVE:
		for x: float in BREAKUP_XS:
			var result: Dictionary = await trial(t, Vector2(x, START_Y), brk + leave, -1.0, 0, BREAKUP_LIMIT)
			t.log_p("x %.0f leaving at BREAK %+.1f: cut %.2f s, hits %s" % [x, leave, result.cut, result.ids])
			if result.hits == 0 and result.cut > 0.0:
				free.append("x %.0f BREAK %+.1f" % [x, leave])
	t.check(free.is_empty(), "each is hit, or doesn't cut it within %.1f s (cut unhurt: %s)" % [BREAKUP_LIMIT, free])


# How low the lens between the two wall tornados either side of x reaches: WALL_Y plus the deeper of their ring zones'
# half-heights there.
# The middles of the gaps between neighbouring wall tornados, left to right.
static func lens_xs(t) -> Array:
	var spots: Array = FirestormLayout.wall_spots(t.sm.tornado_count)
	var out := []
	for i in spots.size() - 1:
		out.append(((spots[i] as Vector2).x + (spots[i + 1] as Vector2).x) / 2.0)
	return out


static func lens_bottom(t, x: float) -> float:
	var radii := FirestormLayout.zone_radii(t.sm)
	var deepest := 0.0
	for spot: Vector2 in FirestormLayout.wall_spots(t.sm.tornado_count):
		var across := absf(x - spot.x) / radii.x
		if across < 1.0:
			deepest = maxf(deepest, radii.y * sqrt(1.0 - across * across))
	return FirestormLayout.WALL_Y + deepest


static func routes(t) -> void:
	t.log_p("-- the skilled route: up the middle, a stop under the fire and one dash through it")
	var reached := 0
	var clean := 0
	var mids := lens_xs(t)
	var via: float = mids[0]
	for mid: float in mids:
		if absf(mid - t.sm.FRONT_SPOT.x) < absf(via - t.sm.FRONT_SPOT.x) - 0.5:
			via = mid
	var lens: float = lens_bottom(t, via)
	t.log_p("up the lens at x %.0f" % via)
	for leave: float in ROUTE_LEAVE:
		for late: int in ROUTE_LATE:
			var result: Dictionary = await trial(t, t.sm.RESET_SPOT, release_at(t) + leave, lens + HOVER_MARGIN, late, ROUTE_LIMIT + 1.0, true, via)
			var in_time: bool = result.cut > 0.0 and result.cut <= release_at(t) + ROUTE_LIMIT
			t.log_p("leaving at RELEASE + %.2f, the dash %d frames after the stop: cut %.2f s, hits %s" % [leave, late, result.cut, result.ids])
			if in_time:
				reached += 1
				if result.hits == 0:
					clean += 1
	t.check(reached == ROUTE_LEAVE.size() * ROUTE_LATE.size() and clean >= ROUTES_CLEAN, "all %d cut it within RELEASE + %.1f s (%d), %d or more unhurt (%d)" % [ROUTE_LEAVE.size() * ROUTE_LATE.size(), ROUTE_LIMIT, reached, ROUTES_CLEAN, clean])
	for x: float in [mids[0], mids[-1]]:
		var result: Dictionary = await trial(t, Vector2(x, START_Y), release_at(t) + 0.25, lens_bottom(t, x) + HOVER_MARGIN, 0, ROUTE_LIMIT + 1.0, true, x)
		t.log_p("logged: up the side lens at x %.0f, a stop and a dash: cut %.2f s, hits %s" % [x, result.cut, result.ids])
	for late: int in ROUTE_LATE:
		var result: Dictionary = await trial(t, t.sm.RESET_SPOT, release_at(t) + 0.25, lens + LENS_MARGIN, late, ROUTE_LIMIT + 1.0, false, via)
		t.log_p("logged: walking straight in, the dash %d frames late: cut %.2f s, hits %s" % [late, result.cut, result.ids])
	var rng := RandomNumberGenerator.new()
	rng.seed = 1004
	for i in 3:
		var leave := 0.25 + rng.randf_range(-0.05, 0.05)
		var late := rng.randi_range(0, 9)
		var result: Dictionary = await trial(t, t.sm.RESET_SPOT, release_at(t) + leave, lens + LENS_MARGIN, late, ROUTE_LIMIT + 1.0, false, via)
		t.log_p("logged: a first-timer walking straight in at RELEASE + %.2f, the dash %d frames late: cut %.2f s, hits %s" % [leave, late, result.cut, result.ids])


# One Firestorm with the player put at `from`: still until `leave` on its clock, then walking at the front spot (with
# `dash_at` over 0, dashing once, `late` frames after the foot of their hurtbox reaches it, holding still there until
# then with `hover`; up the column at x `via` until the dash, if it is 0 or more) and punching once it is open, for
# `limit` s after leaving. The cut's clock (-1 for none) and the hits.
static func trial(t, from: Vector2, leave: float, dash_at := -1.0, late := 0, limit := 4.0, hover := false, via := -1.0) -> Dictionary:
	await reset(t, from)
	var fs: Node = firestorm(t)
	var hits_before: int = t.events_of("HIT").size()
	Common.start(t, "Firestorm")
	var walking := false
	var dash_frame := -1
	var dashed := false
	var hover_y := INF
	var last_punch := -PUNCH_EVERY
	var f := 0
	while Common.state(t) == "Firestorm" and fs.clock < leave + limit:
		if not walking and fs.clock >= leave:
			walking = true
		if walking:
			var foot: float = t.player.global_position.y + FirestormLayout.HURT_OFFSET.y + FirestormLayout.HURT_HALF.y
			if dash_at > 0.0 and dash_frame < 0 and foot <= dash_at:
				dash_frame = f + late
				hover_y = t.player.global_position.y
			if hover and not dashed and dash_frame >= 0:
				# Holding still under the lens against the pull until the dash.
				lean(t, fs, Vector2(via if via >= 0.0 else t.player.global_position.x, hover_y))
			elif via >= 0.0 and not dashed:
				lean(t, fs, Vector2(via, t.sm.FRONT_SPOT.y))
			elif via >= 0.0:
				lean(t, fs, t.sm.FRONT_SPOT)
			else:
				walk(t, t.sm.FRONT_SPOT)
			if not dashed and dash_frame >= 0 and f >= dash_frame:
				dashed = true
				t.release(KEY_DOWN)
				t.press(KEY_UP)
				t.tap(KEY_W)
			var there: bool = absf(t.player.global_position.x - t.sm.FRONT_SPOT.x) <= NEAR and t.player.global_position.y <= t.sm.FRONT_SPOT.y + 8.0
			if there and not t.boss.pillar.shielded and f - last_punch >= PUNCH_EVERY:
				t.tap(KEY_Q)
				last_punch = f
		t.player.playerHealth = 1000
		f += 1
		await t.physics_frame
	Common.keys_up(t)
	var ids := {}
	for e in t.events_of("HIT").slice(hits_before):
		ids[e.id] = ids.get(e.id, 0) + 1
	var result := {"cut": fs.clock if t.sm.pillar_hits > 0 else -1.0, "hits": t.events_of("HIT").size() - hits_before, "ids": ids}
	Common.hold(t)
	return result


# Walking at `to` leaning into the tornados' pull (liam_firestorm_bot's way), still within NEAR of it.
static func lean(t, fs: Node, to: Vector2) -> void:
	var at: Vector2 = t.player.global_position
	var want: Vector2 = -fs.pull_at(at)
	if at.distance_to(to) > NEAR:
		want += (to - at).normalized() * 600.0
	var keys: Array = FirestormBot.arrows(want) if want.length() > 30.0 else []
	for code in [KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN]:
		if keys.has(code):
			t.press(code)
		else:
			t.release(code)


static func walk(t, to: Vector2) -> void:
	var off: Vector2 = to - t.player.global_position
	var want := {KEY_LEFT: off.x < -NEAR, KEY_RIGHT: off.x > NEAR, KEY_UP: off.y < -NEAR, KEY_DOWN: off.y > NEAR}
	for code in want:
		if want[code]:
			t.press(code)
		else:
			t.release(code)
