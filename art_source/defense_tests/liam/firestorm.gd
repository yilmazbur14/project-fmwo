extends RefCounted

# liam_firestorm: attack 3 (LiamFirestorm, LiamTornado, LiamFirestormLayout, his fire rings, the melt, the steam), entered
# straight on his test scene. tier= layout, roam or campers runs that one; any other runs them all.
#   layout    LiamFirestormLayout.validate() finds nothing wrong at 4 and 5 tornados (the track inside SPOT_AREA and
#             out of the front keep-out, every start RESET_CLEAR or more from the reset spot and far enough from the
#             next, every spot outside the front calm in some track point's ring zone, and the wall: validate_wall);
#             3, which has no wall, is only logged; the pull is never over tornado_pull_cap on a 16 px grid and is
#             nothing within front_calm_radius of the front spot
#   roam      with tornado_lean 0, every tornado still on its wall spot until BREAK, on its glide out to its roam start
#             through it, then on TRACK from its START_ALONG at tornado_speed (+-1 px a frame); with the lean on and the
#             player at (400, 800), from ROAM none ever leaning more than tornado_lean off its track point (from there
#             only ever pushed straight down out of the front keep-out, which can take it a little further: the
#             furthest is logged), none ever in the front keep-out, and every ring centred where its tornado was as it
#             left (+-1 px), never moving
#   campers   a player placed in each corner at IGNITION + 0.5 s and again at + 4.0 s, standing still: HIT by a ring or
#             a core, or dragged more than 150 px, within 6 s each time (the times are logged)
#   timeline  its beats on its clock: the ignite at blow_time, IGNITION at blow_time + ignite_time, RELEASE wall_release
#             after it, BREAK wall_hold after that and ROAM wall_break_time after that (each +-1 frame of the beat
#             before), tornado i's rings from IGNITION + quake_first + ring_phase(i) quake_interval and every
#             quake_interval after (+-1 frame), the burn-out at IGNITION + firestorm_time and the next attack
#             burnout_time later; at the burn-out the water is gone and the steam at steam_max (+-0.02 s)
#   core      (from RELEASE) a player walking into a core from the side (flung toward the open floor, not the ropes):
#             one hit, and flung out at least 150 px
#   rings     (from RELEASE, the wall held and only tornado 0 ringing) a ring reaching the player's feet is HIT; one
#             dashed through is DODGED (a perfect dodge); a ring stops hurting at quake_max_radius and frees itself
#   melt      (the carousel held still) entered on ice: the player's ice goes off once a melt front passes them, and the
#             ice is gone within 1.5 s
#   round     (from RELEASE) the round's first pillar hit puts every tornado and ring out and holds the steam where it is
#   fall      (from RELEASE) a sixth hit's fall clears the steam

const Common := preload("res://art_source/defense_tests/liam/common.gd")
const FirestormLayout := preload("res://Scripts/LiamFirestormLayout.gd")
const LiamTornado := preload("res://Scripts/LiamTornado.gd")
const LiamFirestorm := preload("res://Scripts/States/Liam/LiamFirestorm.gd")

const FRAME := 1.0 / 60.0
const CORNERS := [Vector2(150, 400), Vector2(1770, 400), Vector2(150, 925), Vector2(1770, 925)]
const CAMPER_TIME := 6.0
const SWEPT := 150.0


static func run(t) -> void:
	await Common.enter(t)
	t.track()
	t.track_dodges()
	var all: bool = not t.tier in ["layout", "roam", "campers"]
	if all or t.tier == "layout":
		layout(t)
	if all or t.tier == "roam":
		await roam(t)
	if all or t.tier == "campers":
		await campers(t)
	if all:
		await timeline(t)
		await core(t)
		await rings(t)
		await melt(t)
		await round_and_fall(t)


# The carousel held still (the wall never breaking up, no roaming, no lean) for a check of what the tornados do where
# they stand: the knobs it had.
static func hold_still(t) -> Array:
	var was := [t.sm.tornado_speed, t.sm.tornado_lean, t.sm.wall_hold]
	t.sm.tornado_speed = 0.0
	t.sm.tornado_lean = 0.0
	t.sm.wall_hold = 60.0
	return was


static func roam_again(t, was: Array) -> void:
	t.sm.tornado_speed = was[0]
	t.sm.tornado_lean = was[1]
	t.sm.wall_hold = was[2]


static func roam(t) -> void:
	t.log_p("-- the carousel, no lean")
	var sm: Node = t.sm
	var lean: float = sm.tornado_lean
	sm.tornado_lean = 0.0
	var fs: Node = await begin(t, sm.FRONT_SPOT, false)
	var starts: Array = FirestormLayout.starts(sm.tornado_count)
	var wall: Array = FirestormLayout.wall_spots(sm.tornado_count)
	var off_wall := [0.0]
	var off_glide := [0.0]
	var off_track := [0.0]
	var watch := func():
		t.player.is_invincible = true
		if fs.bases.is_empty() or fs.beats.has(&"burnout"):
			return
		for i in fs.bases.size():
			var base: Vector2 = fs.bases[i]
			if fs.wall == LiamFirestorm.WallStage.WALL:
				off_wall[0] = maxf(off_wall[0], base.distance_to(wall[i]))
			elif fs.wall == LiamFirestorm.WallStage.BREAK:
				var weight := clampf((fs.clock - fs.break_at) / sm.wall_break_time, 0.0, 1.0)
				var due := FirestormLayout.place(FirestormLayout.glide(wall[i], FirestormLayout.track_point(starts[i]), weight), sm)
				off_glide[0] = maxf(off_glide[0], base.distance_to(due))
			else:
				var due := FirestormLayout.track_point(starts[i] + sm.tornado_speed * (fs.clock - fs.beats[&"roam"]))
				off_track[0] = maxf(off_track[0], base.distance_to(due))
	t.physics_frame.connect(watch)
	await t.wait_until(func(): return fs.beats.has(&"roam"), 60 * 8)
	await t.wait(60 * 3)
	t.physics_frame.disconnect(watch)
	t.log_p("on the wall at most %.3f px off its spots; through the break at most %.3f px off the glide; from ROAM at most %.3f px off TRACK at %.0f px/s" % [off_wall[0], off_glide[0], off_track[0], sm.tornado_speed])
	t.check(fs.beats.has(&"break") and off_wall[0] <= 0.001, "still on the wall's spots until BREAK")
	t.check(off_glide[0] <= 1.0, "through the break, on the glide out to the roam starts (+-1 px)")
	t.check(fs.beats.has(&"roam") and off_track[0] <= 1.0, "from ROAM, round TRACK from START_ALONG at %.0f px/s (+-1 px)" % sm.tornado_speed)
	sm.tornado_lean = lean
	Common.hold(t)

	t.log_p("-- the lean, the player at (400, 800)")
	var at := Vector2(400, 800)
	fs = await begin(t, at)
	var furthest := [0.0]
	var leaned := [0.0]
	var misplaced := [0]
	var kept_out := [true]
	var rings := {}
	var ring_wrong := []
	var watch_lean := func():
		t.player.is_invincible = true
		t.player.playerHealth = 1000
		t.player.global_position = at
		t.player.velocity = Vector2.ZERO
		if fs.beats.has(&"burnout"):
			return
		for i in fs.bases.size():
			if FirestormLayout.ring_reaches_front(fs.bases[i], sm):
				kept_out[0] = false
			if fs.wall != LiamFirestorm.WallStage.ROAM:
				continue
			var on_track := FirestormLayout.track_point(fs.along[i])
			furthest[0] = maxf(furthest[0], (fs.bases[i] as Vector2).distance_to(on_track))
			leaned[0] = maxf(leaned[0], (fs.lean[i] as Vector2).length())
			if (fs.bases[i] as Vector2).distance_to(FirestormLayout.place(on_track + fs.lean[i], sm)) > 0.01:
				misplaced[0] += 1
		for ring in fs.rings:
			if not is_instance_valid(ring):
				continue
			var id: int = ring.get_instance_id()
			if not rings.has(id):
				# Looked up by its name's index: a pair of tornados in phase sends two rings on the same frame.
				var index := int(String(ring.name).trim_prefix("FireQuake"))
				var entry: Array = fs.ring_log[index]
				rings[id] = [ring, ring.global_position]
				if ring.global_position.distance_to(entry[2]) > 1.0:
					ring_wrong.append("ring %d at %s, its tornado at %s" % [index, ring.global_position, entry[2]])
			elif ring.global_position != rings[id][1]:
				ring_wrong.append("ring moved from %s to %s" % [rings[id][1], ring.global_position])
	t.physics_frame.connect(watch_lean)
	await t.wait_until(func(): return fs.beats.has(&"roam"), 60 * 8)
	await t.wait(60 * 6)
	t.physics_frame.disconnect(watch_lean)
	t.player.is_invincible = false
	t.log_p("the most any leaned %.1f px (tornado_lean %.0f), the furthest any stood off its track point %.1f px; %d frames placed other than straight down from the lean; out of the front keep-out %s; %d rings watched, wrong %s" % [leaned[0], sm.tornado_lean, furthest[0], misplaced[0], kept_out[0], rings.size(), ring_wrong])
	t.check(leaned[0] > 0.0 and leaned[0] <= sm.tornado_lean + 0.001 and misplaced[0] == 0, "none ever leans more than %.0f px off its track point, only ever pushed on straight down out of the front keep-out" % sm.tornado_lean)
	t.check(kept_out[0], "none ever in the front keep-out")
	t.check(not rings.is_empty() and ring_wrong.is_empty(), "every ring centred where its tornado was as it left, and never moving")
	Common.hold(t)


# Each corner in its own firestorm: the player put there at IGNITION + 0.5 s, and again at + 4.0 s.
static func campers(t) -> void:
	t.log_p("-- campers in the corners")
	var times := []
	var missed := []
	for corner: Vector2 in CORNERS:
		var fs: Node = await begin(t, t.sm.FRONT_SPOT)
		for placed_at in [0.5, 4.0]:
			await t.wait_until(func(): return fs.clock - fs.ignition >= placed_at, 60 * 6)
			await Common.fresh(t, corner, 0)
			var from: Vector2 = t.player.global_position
			var hits_before: int = t.events_of("HIT", &"liam_fire_quake").size() + t.events_of("HIT", &"liam_fire_tornado").size()
			var started: float = fs.clock
			var swept: bool = await t.wait_until(func():
				t.player.playerHealth = 1000
				var hits: int = t.events_of("HIT", &"liam_fire_quake").size() + t.events_of("HIT", &"liam_fire_tornado").size()
				return hits > hits_before or t.player.global_position.distance_to(from) > SWEPT, roundi(CAMPER_TIME * 60.0))
			var took: float = fs.clock - started
			var how: String = "moved %.0f px" % t.player.global_position.distance_to(from) if t.events_of("HIT", &"liam_fire_quake").size() + t.events_of("HIT", &"liam_fire_tornado").size() == hits_before else "hit"
			times.append("%s at +%.1f: %s after %.2f s" % [corner, placed_at, how if swept else "untouched", took])
			if not swept:
				missed.append("%s at +%.1f" % [corner, placed_at])
		Common.hold(t)
	t.log_p("campers: %s" % [times])
	t.check(missed.is_empty(), "every corner camper hit or dragged off within %.0f s (%s)" % [CAMPER_TIME, missed])


static func firestorm(t) -> Node:
	return t.sm.states["Firestorm"]


# Into the firestorm with the player at `at`, waiting for IGNITION if asked; or for RELEASE, the player then out of any
# throw of the blow's and put back at `at`.
static func begin(t, at: Vector2, to_ignition := true, to_release := false) -> Node:
	await Common.clear(t)
	await Common.fresh(t, at)
	var fs: Node = firestorm(t)
	Common.start(t, "Firestorm")
	if to_ignition:
		await t.wait_until(func(): return fs.beats.has(&"ignition"), 120)
	if to_release:
		await t.wait_until(func(): return fs.beats.has(&"release"), 180)
		t.sm.cancel_launch()
		await Common.fresh(t, at, 0)
	return fs


static func layout(t) -> void:
	t.log_p("-- the layout")
	var count: int = t.sm.tornado_count
	for tornados in [3, 4, 5]:
		t.sm.tornado_count = tornados
		var problems := FirestormLayout.validate(t.sm)
		if tornados == 3:
			t.log_p("3 tornados (no wall), logged only: %s" % [problems])
			continue
		t.check(problems.is_empty(), "%d tornados: validate() finds nothing wrong, every base %.0f px or more from the reset spot (%s)" % [tornados, FirestormLayout.RESET_CLEAR, problems])
		t.log_p("%d tornados, logged only: %d walks straight up through the wall untouched with the pull left out (wall_leaks)" % [tornados, FirestormLayout.wall_leaks(t.sm).size()])
	t.sm.tornado_count = count
	var bases := FirestormLayout.spots(t.sm.tornado_count)
	var worst := 0.0
	var calm_worst := 0.0
	var area := Rect2(123, 390, 1674, 545)
	var y := area.position.y
	while y <= area.end.y:
		var x := area.position.x
		while x <= area.end.x:
			var point := Vector2(x, y)
			var pull := FirestormLayout.pull_field(point, t.sm, bases).length()
			worst = maxf(worst, pull)
			if point.distance_to(t.sm.FRONT_SPOT) <= t.sm.front_calm_radius:
				calm_worst = maxf(calm_worst, pull)
			x += 16.0
		y += 16.0
	t.log_p("the strongest pull on the grid %.1f px/s (cap %.0f), within %.0f px of the front spot %.3f" % [worst, t.sm.tornado_pull_cap, t.sm.front_calm_radius, calm_worst])
	t.check(worst <= t.sm.tornado_pull_cap + 0.01 and calm_worst == 0.0, "the pull never over its cap, and nothing near the front spot")


static func timeline(t) -> void:
	t.log_p("-- a whole firestorm, the player at the front spot")
	await Common.clear(t)
	await Common.fresh(t, t.sm.FRONT_SPOT)
	t.boss.flood.add_water(1.0)
	var sm: Node = t.sm
	var fs: Node = firestorm(t)
	var at_burnout := {}
	var watch := func():
		t.player.is_invincible = true
		if fs.beats.has(&"burnout") and at_burnout.is_empty():
			at_burnout.merge({"coverage": t.boss.flood.coverage, "density": t.boss.steam.density, "clock": fs.clock})
	t.physics_frame.connect(watch)
	Common.start(t, "Firestorm")
	var finished: bool = await t.wait_until(func(): return fs.beats.has(&"done"), 60 * 16)
	t.physics_frame.disconnect(watch)
	t.player.is_invincible = false
	var beats: Dictionary = fs.beats
	var ignition: float = sm.blow_time + sm.ignite_time
	var want := {&"ignite": sm.blow_time, &"ignition": ignition, &"burnout": ignition + sm.firestorm_time,
		&"done": ignition + sm.firestorm_time + sm.burnout_time,
		&"release": beats.get(&"ignition", ignition) + sm.wall_release,
		&"break": beats.get(&"release", ignition + sm.wall_release) + sm.wall_hold,
		&"roam": beats.get(&"break", ignition + sm.wall_release + sm.wall_hold) + sm.wall_break_time}
	var off := []
	for key in want:
		if not beats.has(key) or absf(beats[key] - want[key]) > FRAME + 0.001:
			off.append("%s %.3f (want %.3f)" % [key, beats.get(key, -1.0), want[key]])
	var n: int = fs.bases.size()
	var wrong_rings := []
	var sent := {}
	for entry in fs.ring_log:
		var i: int = entry[0]
		var k: int = sent.get(i, 0)
		sent[i] = k + 1
		var due: float = ignition + sm.quake_first + FirestormLayout.ring_phase(n, i) * sm.quake_interval + k * sm.quake_interval
		if absf(entry[1] - due) > FRAME + 0.001:
			wrong_rings.append("tornado %d ring %d at %.3f (want %.3f)" % [i, k, entry[1], due])
	var every := true
	for i in n:
		var expected := 0
		while ignition + sm.quake_first + FirestormLayout.ring_phase(n, i) * sm.quake_interval + expected * sm.quake_interval < ignition + sm.firestorm_time:
			expected += 1
		every = every and sent.get(i, 0) == expected
	t.log_p("beats %s; %d rings %s; at the burn-out water %.3f, steam %.3f" % [beats, fs.ring_log.size(), sent, at_burnout.get("coverage", -1.0), at_burnout.get("density", -1.0)])
	t.check(finished and off.is_empty(), "the beats: ignite %.1f, IGNITION %.1f, RELEASE + %.1f, BREAK + %.1f, ROAM + %.1f, burn-out %.1f, done %.1f (%s)" % [sm.blow_time, ignition, sm.wall_release, sm.wall_hold, sm.wall_break_time, ignition + sm.firestorm_time, ignition + sm.firestorm_time + sm.burnout_time, off])
	t.check(wrong_rings.is_empty() and every, "each tornado's rings from IGNITION + %.2f + ring_phase(i) %.1f s, every %.1f s (%s)" % [sm.quake_first, sm.quake_interval, sm.quake_interval, wrong_rings])
	t.check(at_burnout.get("coverage", 1.0) <= 0.01 and absf(at_burnout.get("density", 0.0) - sm.steam_max) <= 0.02, "the water boiled off and the steam at %.2f by the burn-out" % sm.steam_max)
	Common.hold(t)


# Its pull switched off: on the wall the tornado stands level with the player, and the pull (on their centre) would
# drag their feet under its core.
static func core(t) -> void:
	t.log_p("-- walking into a core")
	var pull: float = t.sm.tornado_pull
	t.sm.tornado_pull = 0.0
	var fs: Node = await begin(t, t.sm.FRONT_SPOT, true, true)
	var tornado: Node = fs.tornados[2]
	var base: Vector2 = tornado.global_position
	await Common.fresh(t, base + Vector2(-110, 0) - FirestormLayout.FEET, 0)
	var health: int = t.player.playerHealth
	t.press(KEY_RIGHT)
	var touched: bool = await t.wait_until(func(): return not tornado.results.is_empty(), 90)
	t.release(KEY_RIGHT)
	var contact: Vector2 = t.player.global_position
	var farthest := [0.0]
	var watch := func(): farthest[0] = maxf(farthest[0], t.player.global_position.distance_to(contact))
	t.physics_frame.connect(watch)
	await t.wait(roundi((t.sm.tornado_fling_time + 0.1) * 60.0))
	t.physics_frame.disconnect(watch)
	t.log_p("results %s, health %d -> %d, flung %.0f px" % [tornado.results, health, t.player.playerHealth, farthest[0]])
	t.check(touched and tornado.results.size() == 1 and t.player.playerHealth == health - 1, "one hit")
	t.check(farthest[0] >= 150.0, "flung out at least 150 px (%.0f)" % farthest[0])
	t.sm.tornado_pull = pull
	Common.hold(t)


# Tornado 0's rings, its pull switched off so the player can stand in its zone.
static func rings(t) -> void:
	t.log_p("-- the fire rings")
	var carousel := hold_still(t)
	var pull: float = t.sm.tornado_pull
	t.sm.tornado_pull = 0.0
	var fs: Node = await begin(t, t.sm.FRONT_SPOT, true, true)
	for j in range(1, fs.next_rings.size()):
		fs.next_rings[j] = INF
	var base: Vector2 = fs.bases[0]
	# Standing with the feet 200 px across from tornado 0: its next ring reaches them.
	await Common.fresh(t, base + Vector2(200, 0) - FirestormLayout.FEET, 0)
	var hits_before: int = t.events_of("HIT", &"liam_fire_quake").size()
	var hit: bool = await t.wait_until(func(): return t.events_of("HIT", &"liam_fire_quake").size() > hits_before, 60 * 3)
	t.check(hit, "a ring reaching the feet is HIT")
	# Past the perfect-dodge cooldown, then the feet 300 px across, dashing in through the band as it comes.
	await t.wait(100)
	await Common.fresh(t, base + Vector2(300, 0) - FirestormLayout.FEET, 0)
	t.clear_iframes()
	var found := [null]
	var coming: bool = await t.wait_until(func():
		for candidate in fs.rings:
			if is_instance_valid(candidate) and candidate.global_position == base and candidate.radius >= 300.0 - 36.0 - 60.0 and candidate.radius < 300.0 - 36.0 - 50.0:
				found[0] = candidate
				return true
		return false, 60 * 3)
	var ring: Node = found[0]
	var hits_mid: int = t.events_of("HIT", &"liam_fire_quake").size()
	var dodges_before: int = t.dodges.size()
	t.press(KEY_LEFT)
	t.tap(KEY_W)
	await t.wait(6)
	t.release(KEY_LEFT)
	await t.wait(20)
	var dodged: bool = t.dodges.size() > dodges_before and t.dodges[-1].id == &"liam_fire_quake"
	t.log_p("ring coming %s, hits %d -> %d, perfect dodge %s" % [coming, hits_mid, t.events_of("HIT", &"liam_fire_quake").size(), dodged])
	t.check(coming and t.events_of("HIT", &"liam_fire_quake").size() == hits_mid and dodged, "a dash through the band is DODGED, a perfect dodge")
	# A ring at its end: it stops hurting and frees itself.
	# Looked up by id: a lambda that captures the ring itself logs an engine error once the ring frees itself.
	var ring_id: int = ring.get_instance_id() if ring != null else 0
	var ended: bool = await t.wait_until(func(): return ring_id != 0 and (not is_instance_id_valid(ring_id) or instance_from_id(ring_id).dying), 60 * 3)
	var dying_at: float = t.defense.clock
	var freed: bool = await t.wait_until(func(): return not is_instance_id_valid(ring_id), roundi((t.sm.quake_die_time + 0.1) * 60.0))
	t.log_p("the ring dying %s at its end, freed %s %.2f s later" % [ended, freed, t.defense.clock - dying_at])
	t.check(ended and freed, "at quake_max_radius it stops hurting and frees itself within quake_die_time")
	t.sm.tornado_pull = pull
	roam_again(t, carousel)
	Common.hold(t)


static func melt(t) -> void:
	t.log_p("-- the melt, entered on ice")
	var carousel := hold_still(t)
	var pull: float = t.sm.tornado_pull
	t.sm.tornado_pull = 0.0
	await Common.clear(t)
	var at := Vector2(960, 700)
	await Common.fresh(t, at)
	t.boss.flood.add_water(1.0)
	t.boss.flood.freeze_from(t.sm.PERCH, 100000.0)
	await t.wait(2)
	t.sm.set_player_ice(true)
	var fs: Node = firestorm(t)
	Common.start(t, "Firestorm")
	await t.wait_until(func(): return fs.beats.has(&"ignition"), 120)
	var ignition: float = fs.clock
	var off_at := [-1.0]
	var gone_at := [-1.0]
	var watch := func():
		if off_at[0] < 0.0 and not t.player.on_ice:
			off_at[0] = fs.clock
		if gone_at[0] < 0.0 and not t.boss.flood.is_iced():
			gone_at[0] = fs.clock
	t.physics_frame.connect(watch)
	await t.wait_until(func(): return gone_at[0] >= 0.0, 120)
	t.physics_frame.disconnect(watch)
	var nearest := INF
	for base: Vector2 in fs.bases:
		nearest = minf(nearest, t.player.global_position.distance_to(base))
	var due: float = ignition + nearest / t.sm.melt_speed
	t.log_p("ignition %.2f; the player's ice off at %.2f (the front due %.2f); the ice gone at %.2f" % [ignition, off_at[0], due, gone_at[0]])
	t.check(off_at[0] >= 0.0 and absf(off_at[0] - due) <= 3.0 * FRAME, "the player's ice goes off as a melt front passes them")
	t.check(gone_at[0] >= 0.0 and gone_at[0] - ignition <= 1.5, "and the ice is gone within 1.5 s (%.2f)" % (gone_at[0] - ignition))
	t.sm.tornado_pull = pull
	roam_again(t, carousel)
	Common.hold(t)


static func round_and_fall(t) -> void:
	t.log_p("-- the round's first hit")
	var fs: Node = await begin(t, t.sm.FRONT_SPOT, true, true)
	await t.wait(30)
	var tornados: Array = fs.tornados.duplicate()
	var rings: Array = fs.rings.duplicate()
	t.sm.pillar_hits = 0
	var took: bool = await Common.punch_pillar(t)
	await t.wait(2)
	var held: float = t.boss.steam.density
	var all_out: bool = tornados.all(func(tornado): return not is_instance_valid(tornado) or tornado.stage == LiamTornado.Stage.OUT)
	var rings_out: bool = rings.all(func(ring): return not is_instance_valid(ring) or ring.dying)
	await t.wait(30)
	var still: float = t.boss.steam.density
	t.log_p("took %s, now %s; tornados out %s, rings out %s, steam %.3f then %.3f" % [took, Common.state(t), all_out, rings_out, held, still])
	t.check(took and Common.state(t) == "Wobble" and all_out and rings_out, "every tornado and ring put out, into the round")
	t.check(held > 0.0 and absf(still - held) <= 0.0001, "the steam held where it was")
	Common.hold(t)
	await Common.clear(t)

	t.log_p("-- a sixth hit's fall")
	fs = await begin(t, t.sm.FRONT_SPOT, true, true)
	await t.wait(30)
	t.sm.pillar_hits = 5
	var toppled: bool = await Common.punch_pillar(t)
	var cleared: bool = await t.wait_until(func(): return t.boss.steam.density <= 0.001, roundi((t.sm.fall_steam_clear + 0.2) * 60.0))
	t.log_p("toppled %s, now %s, steam %.3f" % [toppled, Common.state(t), t.boss.steam.density])
	t.check(toppled and cleared, "his fall clears the steam within %.1f s" % t.sm.fall_steam_clear)
	await t.wait_until(func(): return Common.state(t) == "Downed", 90)
	Common.hold(t)
