extends RefCounted

# liam_tsunami_gate: the Tsunami's pillar opens only as its tsunami_gate_wave-th wave crashes on the bottom rope (the
# first's, the user's pick of 2026-10-04; the fifth's since that day's tuning round). Opened with the first tell, a walk
# straight up just left of the seam punched it 1.15 s in, unhurt: the first wave goes down the player's half (the
# right, from RESET_SPOT) and the second hadn't come out of the row's foot.
# On his test scene, every run from RESET_SPOT, punching only once the pillar is open.
#   open      shielded from the Tsunami's start (a punch from the front spot a second in is refused and counts nothing),
#             then open within a frame of the gate wave's crash on the bottom rope (its spawn, plus (ROPES.end.y - its
#             spawn front) / wave_speed), its shield bursting once (LiamPillar.open_with_burst)
#   straight  the laziest route: straight up to the row's face at x 905..1015, punching from the moment it opens: every
#             one is hit by a wave first
#   routes    the skilled way up still cuts it unhurt: on the row's face left of the seam, out of the right half's waves,
#             a parry of each wave of the left half as it comes out of the row's foot (pressed with its front 50, 80 and
#             110 px over the player's hurtbox, inside the 20..150 px a sweep found clean), then the punch: unhurt, every
#             one of those waves PARRIED

const Common := preload("res://art_source/defense_tests/liam/common.gd")

const STRAIGHT_XS := [905, 925, 945, 960, 975, 995, 1015]
const LEFT_FRONT := Vector2(930, 380)
const PARRY_LEADS := [50.0, 80.0, 110.0]
const PARRY_HOLD := 4
const NEAR := 6.0
const PUNCH_EVERY := 18
# Each trial's longest run: past the gate's opening and the waves after it.
const TRIAL_FRAMES := 60 * 9


static func run(t) -> void:
	await Common.enter(t)
	t.track()
	t.track_parries()
	await open(t)
	await straight(t)
	await routes(t)


static func open(t) -> void:
	t.log_p("-- when the pillar opens")
	await reset(t, t.sm.FRONT_SPOT)
	var keep_safe := func(): t.player.is_invincible = true
	t.physics_frame.connect(keep_safe)
	var tsunami: Node = t.sm.states["Tsunami"]
	var bursts_before: int = t.boss.pillar.bursts
	Common.start(t, "Tsunami")
	await t.wait(1)
	var shut_at_start: bool = t.boss.pillar.shielded
	await t.wait(59)
	var refused: bool = not await Common.punch_pillar(t)
	var still: bool = Common.state(t) == "Tsunami" and t.sm.pillar_hits == 0
	var crashed := [-1]
	var opened := [-1]
	var watch := func():
		var gate: Variant = tsunami.gate_wave
		if crashed[0] < 0 and gate != null and is_instance_valid(gate) and gate.spent:
			crashed[0] = Engine.get_physics_frames()
		if opened[0] < 0 and not t.boss.pillar.shielded:
			opened[0] = Engine.get_physics_frames()
	t.physics_frame.connect(watch)
	await t.wait_until(func(): return opened[0] >= 0, 60 * 10)
	t.physics_frame.disconnect(watch)
	t.physics_frame.disconnect(keep_safe)
	t.player.is_invincible = false
	var index: int = mini(t.sm.tsunami_gate_wave, tsunami.wave_count()) - 1
	var entry: Dictionary = tsunami.spawn_log[index] if index < tsunami.spawn_log.size() else {"t": INF, "front": 0.0}
	var due: float = entry.t + (t.sm.ROPES.end.y - entry.front) / t.sm.wave_speed
	t.log_p("shielded at the start %s, a punch at 1 s refused %s, wave %d crashed on frame %d, the pillar opened on frame %d at %.3f s (due %.3f)" % [shut_at_start, refused, index + 1, crashed[0], opened[0], tsunami.opened_at, due])
	t.check(shut_at_start and refused and still, "shielded from its start: a punch a second in is refused and counts nothing")
	t.check(crashed[0] >= 0 and opened[0] >= crashed[0] and opened[0] - crashed[0] <= 1, "open within a frame of wave %d's crash on the bottom rope" % (index + 1))
	t.check(absf(tsunami.opened_at - due) <= 2.0 / 60.0, "%.3f s in (due %.3f)" % [tsunami.opened_at, due])
	t.check(t.boss.pillar.bursts - bursts_before == 1, "its shield bursts once as it opens (%d)" % (t.boss.pillar.bursts - bursts_before))
	Common.hold(t)


static func straight(t) -> void:
	t.log_p("-- the laziest route: straight up, punching from the moment it opens")
	var unhurt := []
	for x in STRAIGHT_XS:
		var result: Dictionary = await trial(t, Vector2(x, LEFT_FRONT.y), -1.0)
		t.log_p("x %d: cut %.2f s, hits %d" % [x, result.cut, result.hits])
		if result.hits == 0:
			unhurt.append(x)
	t.check(unhurt.is_empty(), "every walk straight up is hit by a wave first (unhurt at %s)" % [unhurt])


static func routes(t) -> void:
	t.log_p("-- the skilled route: parrying the left half's waves on the row's face")
	for lead: float in PARRY_LEADS:
		var result: Dictionary = await trial(t, LEFT_FRONT, lead)
		t.log_p("parries pressed at %.0f px: cut %.2f s, hits %d, %d of the left half's waves came, parried %d" % [lead, result.cut, result.hits, result.pressed, result.parried])
		t.check(result.cut > 0.0 and result.hits == 0 and result.pressed >= 1 and result.parried == result.pressed, "parrying at %.0f px cuts it unhurt, every wave that came parried" % lead)


static func reset(t, at: Vector2) -> void:
	await Common.clear(t)
	t.sm.pillar_hits = 0
	t.sm.round_hits_taken = 0
	t.boss.pillar.show_hits(0)
	await Common.fresh(t, at)


# One run from RESET_SPOT up to `spot` on the row's face, punching once the pillar is open. With `lead` 0 or more, a
# parry pressed as each left-half wave's front comes `lead` px over the player's hurtbox top. The cut's clock (-1 for
# none), the hits, the parries pressed and the parries made.
static func trial(t, spot: Vector2, lead: float) -> Dictionary:
	await reset(t, t.sm.RESET_SPOT)
	var hits_before: int = t.events_of("HIT").size()
	var parries_before: int = t.parries.size()
	var tsunami: Node = t.sm.states["Tsunami"]
	Common.start(t, "Tsunami")
	var pressed := {}
	var release_at := -1
	var last_punch := -PUNCH_EVERY
	for f in TRIAL_FRAMES:
		if Common.state(t) != "Tsunami":
			break
		walk(t, spot)
		var there: bool = absf(t.player.global_position.x - spot.x) <= NEAR and t.player.global_position.y < 400.0
		if lead >= 0.0 and there:
			for i in tsunami.waves.size():
				var wave = tsunami.waves[i]
				if not is_instance_valid(wave) or wave.side != &"left" or wave.collapsing or pressed.has(i):
					continue
				if wave.front_y >= Common.hurtbox_top(t) - lead:
					pressed[i] = true
					t.press(KEY_SHIFT)
					release_at = f + PARRY_HOLD
		if release_at >= 0 and f >= release_at:
			t.release(KEY_SHIFT)
			release_at = -1
		if there and not t.boss.pillar.shielded and f - last_punch >= PUNCH_EVERY:
			t.tap(KEY_Q)
			last_punch = f
		await t.physics_frame
	Common.keys_up(t)
	var result := {"cut": tsunami.clock if t.sm.pillar_hits > 0 else -1.0, "hits": t.events_of("HIT").size() - hits_before,
		"pressed": pressed.size(), "parried": t.parries.size() - parries_before}
	Common.hold(t)
	return result


static func walk(t, to: Vector2) -> void:
	var off: Vector2 = to - t.player.global_position
	var want := {KEY_LEFT: off.x < -NEAR, KEY_RIGHT: off.x > NEAR, KEY_UP: off.y < -NEAR, KEY_DOWN: off.y > NEAR}
	for code in want:
		if want[code]:
			t.press(code)
		else:
			t.release(code)
