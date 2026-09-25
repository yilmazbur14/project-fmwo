extends RefCounted

# danny_slams (coder C): Danny's Sumo Smash string (DannyBossSlams) in his fight, his cycle parked and the
# string started from Idle, answered the same way at all five landings. Since the 2026-09-24 playtest every
# landing but the fifth leaves a worm puddle on its spot that arms 0.40 s later, and a root in the string seals
# the parry, so a good answer moves.
#   parry   a fresh guard press a few frames before each landing, then a step off down and to the right: five
#           PARRIED, his gauge up five reads (62.5), no ring touching them, a clean string, never stuck, and
#           each puddle left behind armed at its grace.
#   step    the least that works: the press, 0.10 s, then 60 px straight down: five PARRIED, unhurt, the feet off
#           each puddle at least 0.10 s before it armed, and all four lying there once the fourth is down.
#   still   the press, standing still: the first PARRIED, then its puddle takes their feet as it arms - STUCK!,
#           no badge for the second, whose press only squelches, and it HITS: PARRIED, HIT, IGNORED, HIT,
#           IGNORED.
#   rooted  rooted as the string starts: STUCK!, no badge for the first landing, a perfect press that only
#           squelches, and a HIT.
#   hit     nothing at all: exactly three HITs, each one's i-frames buying the landing after it.
#   dash    a dash right across the spot as each landing comes, the feet still in his footprint, then on off
#           the puddle it leaves: five DODGED, never stuck.
#   walk    right out of the footprint from each latch: no landing reaches them, no ring touches them sooner than
#           0.25 s after its landing, the fifth ring dashed through, in across its wide side, and never stuck.
# Every tier: the landings at 1.45 s and then every 0.90 s on his own clock, to the frame; the red badge up from
# each latch to its landing unless the player is stuck, and never outside one; never more than eight puddles live;
# then his nap, a player the fifth landing found in his footprint slid out beside him, the floor round him clear,
# and a way from the player to a side of him - his own check, and coder B's open-floor check from danny_spit.

const Spit := preload("res://art_source/defense_tests/danny/spit.gd")
const BODY := "Arena/DannyBossScene/DannyBossCharacterBody"
const RING_SCRIPT := "res://Scripts/DannyBossQuakeRingScript.gd"
const HIT_INFO := "res://Scripts/HitInfo.gd"
const SEED := 20260924
const FRAME := 1.0 / 60.0
const FIRST_LANDING := 1.45
const LANDING_GAP := 0.90
# Where each answer starts, with room for the way it moves.
const STARTS := {
	"parry": Vector2(660, 420), "step": Vector2(700, 480), "still": Vector2(960, 800), "rooted": Vector2(960, 800),
	"hit": Vector2(960, 800), "dash": Vector2(400, 800), "walk": Vector2(360, 800),
}
# How far ahead of each landing the bots move: a guard press inside the parry window, and a dash whose
# immunity covers the landing while the feet are still inside the footprint.
const PARRY_LEAD := 4.0 / 60.0
const DASH_LEAD := 3.0 / 60.0
# The parry answer's step off, and the step answer's wait and its least step.
const PARRY_STEP := 0.20
const STEP_WAIT := 0.10
const STEP_TIME := 0.10
# The least time left on a puddle's grace as the step answer's feet come off it.
const STEP_MARGIN := 0.10
# The walk out of the footprint from each latch, and how many px of the fifth ring's growth its dash goes ahead
# of the band.
const WALK_TIME := 0.45
const RING_DASH_AHEAD := 12.0
const GAUGE_READ := 100.0 / 8.0
# A spit's four and the string's four.
const MOST_PUDDLES := 8
const ANSWERS := ["parry", "step", "still", "rooted", "hit", "dash", "walk"]


static func run(t) -> void:
	var answer: String = "parry" if t.tier == "normal" else t.tier
	if not answer in ANSWERS:
		t.check(false, "tier is one of %s (%s)" % [ANSWERS, answer])
		return
	await enter(t)
	var slams: Node = t.sm.states["Slams"]
	var gauge: Node = t.boss.break_gauge
	gauge.locked = false
	gauge.value = 0.0
	await reset(t, STARTS[answer])
	var health: int = t.player.playerHealth
	var hit_info: GDScript = load(HIT_INFO)
	t.log_p("-- the string, answered: %s" % answer)
	var run: Dictionary = await run_string(t, answer)
	var results: Array = slams.results
	var names: Array = results.map(func(r): return hit_info.Result.keys()[r.result])
	var landed: Array = slams.impact_times
	var armed_after: Array = []
	var off_before: Array = []
	for k in run.puddle_ids.size():
		var id: int = run.puddle_ids[k]
		armed_after.append(snappedf(run.armed_at.get(id, INF) - landed[k], 0.001))
		off_before.append(snappedf(run.armed_at.get(id, INF) - run.off_at.get(id, INF), 0.001))
	t.log_p("landings %s at %s (frames %s); latches %s; ring contacts %s; health %d -> %d; gauge %.1f; clean %s; nudged %s" % [
		names, landed.map(func(x): return snappedf(x, 0.001)), run.impact_frames,
		slams.latch_times.map(func(x): return snappedf(x, 0.001)), run.ring_contacts, health, t.player.playerHealth,
		gauge.value, slams.clean, slams.nudged])
	t.log_p("puddles left %d, armed %s s after their landings, feet off them %s s before; stuck at %s; badges withheld %s; STUCK! %d; squelches %d; most live %d; at the nap: %d cleared round him, string's opened %s, way %s, B's floor %s" % [
		slams.puddles_left.size(), armed_after, off_before, slams.seal_times.map(func(x): return snappedf(x, 0.001)),
		slams.badges_withheld, slams.stuck_words, slams.squelches, run.most_puddles, slams.nap_cleared, slams.way_opened,
		run.way, run.b_floor])

	var on_beat: bool = landed.size() == 5
	for k in landed.size():
		on_beat = on_beat and absf(landed[k] - (FIRST_LANDING + LANDING_GAP * k)) <= FRAME + 0.0001
	t.check(on_beat, "five landings, at 1.45 s and then every 0.90 s, to the frame (%s)" % [landed.map(func(x): return snappedf(x, 0.001))])
	var gaps: Array = run.badge_gaps.filter(func(gap): return not slams.badges_withheld.has(gap[0]))
	t.check(gaps.is_empty(), "the red badge is up from every latch to its landing, unless the player is stuck (%s)" % [gaps])
	t.check(run.stray_badges.is_empty(), "and never outside one (%s)" % [run.stray_badges])
	var squashes: Dictionary = run.squash_steps
	var squash: float = slams.squash_time
	t.check(range(1, 5).all(func(k): return absf(squashes.get(k, -1.0) - squash) <= FRAME + 0.0001),
		"each of the first four landings holds its squash %.2f s, three steps, on his own clock (%s)" % [squash, squashes])
	t.check(slams.puddles_left.size() == 4, "the first four landings each leave a puddle, the fifth none (%d)" % slams.puddles_left.size())
	t.check(run.most_puddles <= MOST_PUDDLES, "never more than %d puddles live (%d)" % [MOST_PUDDLES, run.most_puddles])

	var never_stuck: bool = slams.seal_times.is_empty() and slams.stuck_words == 0 and slams.badges_withheld.is_empty()
	match answer:
		"parry":
			t.check(names == ["PARRIED", "PARRIED", "PARRIED", "PARRIED", "PARRIED"], "five PARRIED (%s)" % [names])
			t.check(is_equal_approx(gauge.value, 5.0 * GAUGE_READ), "his gauge up five reads, 62.5 (%.2f)" % gauge.value)
			t.check(t.player.playerHealth == health and run.ring_contacts.is_empty(), "no ring touches a player whose feet were in the footprint (%s)" % [run.ring_contacts])
			t.check(slams.clean and never_stuck, "a clean string, never stuck")
			t.check(armed_after.all(func(a): return a >= slams.puddle_grace - 0.0001 and a <= slams.puddle_grace + 3.0 * FRAME + 0.0001),
				"each puddle arms %.2f s after its landing (%s)" % [slams.puddle_grace, armed_after])
		"step":
			t.check(names == ["PARRIED", "PARRIED", "PARRIED", "PARRIED", "PARRIED"] and t.player.playerHealth == health and never_stuck,
				"five PARRIED, unhurt, never stuck (%s)" % [names])
			t.check(off_before.size() == 4 and off_before.all(func(m): return m >= STEP_MARGIN),
				"the feet off each puddle at least %.2f s before it arms (%s)" % [STEP_MARGIN, off_before])
			t.check(run.filled == 4, "all four lying there once the fourth is down (%d)" % run.filled)
		"still":
			t.check(names == ["PARRIED", "HIT", "IGNORED", "HIT", "IGNORED"], "PARRIED, then stuck: HIT, IGNORED, HIT, IGNORED (%s)" % [names])
			var first_stuck: float = slams.seal_times[0] - landed[0] if not slams.seal_times.is_empty() else -1.0
			t.check(first_stuck >= slams.puddle_grace - 0.0001 and first_stuck <= slams.puddle_grace + 3.0 * FRAME + 0.0001,
				"the first landing's puddle takes their feet as it arms, %.2f s on (%.3f)" % [slams.puddle_grace, first_stuck])
			t.check(slams.stuck_words == slams.seal_times.size() and slams.stuck_words >= 1, "STUCK! each time (%d)" % slams.stuck_words)
			t.check(slams.badges_withheld.has(2) and run.pressed_sealed.has(2), "no badge for the second landing, and its press only squelches")
			t.check(slams.squelches == run.pressed_sealed.size() and slams.squelches >= 1, "a squelch for every press while stuck (%d of %d)" % [slams.squelches, run.pressed_sealed.size()])
		"rooted":
			t.check(not slams.seal_times.is_empty() and slams.seal_times[0] <= 3.0 * FRAME + 0.0001 and slams.stuck_words >= 1,
				"stuck as the string starts, STUCK! (%s)" % [slams.seal_times])
			t.check(slams.badges_withheld.has(1) and run.pressed_sealed.has(1) and slams.squelches >= 1,
				"no badge for the first landing, and a perfect press only squelches")
			t.check(names.size() > 0 and names[0] == "HIT", "the first landing HITS (%s)" % [names])
		"hit":
			t.check(names == ["HIT", "IGNORED", "HIT", "IGNORED", "HIT"], "a HIT, then one inside its i-frames, three times over (%s)" % [names])
			t.check(health - t.player.playerHealth == 3, "exactly three half-hearts (%d)" % (health - t.player.playerHealth))
			t.check(run.ring_contacts.is_empty() and not slams.clean, "no ring touches them, and the string isn't clean")
		"dash":
			t.check(names == ["DODGED", "DODGED", "DODGED", "DODGED", "DODGED"] and results.all(func(r): return r.feet_inside),
				"five DODGED, the feet inside the footprint every time (%s)" % [names])
			t.check(t.player.playerHealth == health and slams.clean and never_stuck, "unhurt, a clean string, never stuck")
		"walk":
			t.check(results.all(func(r): return not r.feet_inside) and names.all(func(n): return n == "IGNORED"),
				"no landing reaches a player walking out of the footprint from its latch (%s)" % [names])
			var firsts: Array = run.ring_contacts.values()
			t.check(not firsts.is_empty() and firsts.all(func(at): return at >= 0.25 - 0.0001),
				"every ring's first touch at least 0.25 s after its landing (%s)" % [firsts.map(func(x): return snappedf(x, 0.001))])
			t.check(run.ring_dash.get("touched_in_dash", false) and run.ring_dash.get("unhurt", false),
				"the fifth ring, dashed through across its wide side: touched inside the dash's immunity, unhurt (%s)" % [run.ring_dash])
			t.check(never_stuck, "never stuck")

	t.check(t.sm.current_state == t.sm.states["Sleep"], "then his nap (%s)" % t.sm.current_state.name)
	if run.inside_at_settle:
		var box: Rect2 = run.settle_box
		var feet: Vector2 = t.sm.player_feet()
		t.check(slams.nudged and t.player.global_position == t.sm.drive_to and (feet.x <= box.position.x or feet.x >= box.end.x),
			"a player the fifth landing found in his footprint is slid out beside him (%s, box %s)" % [feet, box])
	else:
		t.check(not slams.nudged, "a player outside his footprint is left where they are")
	t.check(run.round_him == 0, "no puddle left on the floor round him (%d)" % run.round_him)
	t.check(run.way and (not run.b_floor.feet_open or run.b_floor.side), "a way from the player to a side of him to punch from (%s, %s)" % [run.way, run.b_floor])
	park(t)


# His fight, loaded past his entrance and the card, parked in Idle with his cycle held off.
static func enter(t) -> void:
	await t.load_fight("danny")
	t.boss = t.current_scene.get_node(BODY)
	t.sm = t.boss.state_machine
	t.sm.rng.seed = SEED
	park(t)


static func park(t) -> void:
	t.sm.on_child_transition(t.sm.current_state, "Idle")
	t.stop_boss_timers()


# At HOME and parked, nothing of his on the mat, the player fresh at `start` with every key up.
static func reset(t, start: Vector2) -> void:
	park(t)
	t.boss.global_position = t.sm.HOME
	t.sm.clear_puddles()
	for hazard in t.get_nodes_in_group(t.sm.HAZARD_GROUP):
		hazard.queue_free()
	for code in [KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN, KEY_SHIFT]:
		t.release(code)
	t.clear_iframes()
	t.player.playerHealth = 100
	t.defense._set_stamina(t.defense.max_stamina)
	await t.settle_player(start)
	await t.wait(40)


# Held for `seconds` of the fight's own time: a parry's hit-stop and slow-down hold the walk with everything else,
# as they do a player's.
static func walk(t, codes: Array, seconds: float) -> void:
	for code in codes:
		t.press(code)
	await game_wait(t, seconds)
	for code in codes:
		t.release(code)


static func game_wait(t, seconds: float) -> void:
	var until: float = t.defense.clock + seconds
	await t.wait_until(func(): return t.defense.clock >= until - 0.0001, 600)


# The string from Idle, each landing answered by `answer`. Every physics step while it runs: whether a badge is
# up and which beat he is in, each ring's first touch on the player, as its age, and each puddle a landing left:
# when it armed and when the feet were first off it.
static func run_string(t, answer: String) -> Dictionary:
	var slams: Node = t.sm.states["Slams"]
	var ring_script: GDScript = load(RING_SCRIPT)
	var watched := {"badge_gaps": [], "stray_badges": [], "ring_contacts": {}, "impact_frames": [], "frame": 0,
		"inside_at_settle": false, "settle_box": Rect2(), "ring_dash": {}, "squash_steps": {}, "squash_from": {},
		"armed_at": {}, "off_at": {}, "most_puddles": 0, "filled": 0, "pressed_sealed": [], "round_him": 0,
		"way": false, "b_floor": {}, "puddle_ids": []}
	var watch := func():
		for ring in t.boss.ring_layer.get_children():
			if ring.get_script() != ring_script or ring.is_queued_for_deletion():
				continue
			var id: int = ring.get_instance_id()
			if not watched.ring_contacts.has(id) and t.defense.sources.has(id):
				watched.ring_contacts[id] = ring.elapsed
		watched.most_puddles = maxi(watched.most_puddles, t.sm.live_puddles().size())
		if t.sm.current_state != slams:
			return
		watched.frame += 1
		var badge: bool = not t.live_tells().is_empty()
		var covered: bool = slams.beat == slams.Beat.LATCH or slams.beat == slams.Beat.DROP
		if covered and not badge:
			watched.badge_gaps.append([slams.slam, snappedf(slams.clock, 0.001)])
		elif badge and not covered:
			watched.stray_badges.append([slams.slam, str(slams.Beat.keys()[slams.beat]), snappedf(slams.clock, 0.001)])
		if watched.impact_frames.size() < slams.impact_times.size():
			watched.impact_frames.append(watched.frame)
		# The squash on his own clock, from the landing's step to the rebound's: a parry's hit-stop stretches it in
		# frames, never in game time.
		if slams.beat == slams.Beat.IMPACT and t.boss.current_anim == &"slam_impact" and not watched.squash_from.has(slams.slam):
			watched.squash_from[slams.slam] = slams.clock
		if slams.beat == slams.Beat.REBOUND and not watched.squash_steps.has(slams.slam) and watched.squash_from.has(slams.slam):
			watched.squash_steps[slams.slam] = snappedf(slams.clock - watched.squash_from[slams.slam], 0.0001)
		var feet: Vector2 = t.sm.player_feet()
		for k in slams.puddles_left.size():
			var puddle = slams.puddles_left[k]
			if not is_instance_valid(puddle):
				continue
			var id: int = puddle.get_instance_id()
			if watched.puddle_ids.size() == k:
				watched.puddle_ids.append(id)
			if not watched.armed_at.has(id) and puddle.armed:
				watched.armed_at[id] = slams.clock
			if not watched.off_at.has(id) and not puddle.contains_feet(feet):
				watched.off_at[id] = slams.clock
	t.sm.on_child_transition(t.sm.current_state, "Slams")
	t.physics_frame.connect(watch)
	if answer == "rooted":
		await t.wait(1)
		t.sm.test_root_player()
	for k in slams.slams:
		var landing: float = _landing_time(slams, k + 1)
		match answer:
			"parry", "step", "still", "rooted":
				await t.wait_until(func(): return t.sm.current_state != slams or slams.clock >= landing - PARRY_LEAD, 400)
				if slams.call("_sealed"):
					watched.pressed_sealed.append(k + 1)
				t.press(KEY_SHIFT)
				await t.wait_until(func(): return t.sm.current_state != slams or slams.results.size() > k, 60)
				t.release(KEY_SHIFT)
				if k < slams.slams - 1 and answer == "parry":
					await walk(t, [KEY_RIGHT, KEY_DOWN], PARRY_STEP)
				elif k < slams.slams - 1 and answer == "step":
					await game_wait(t, STEP_WAIT)
					await walk(t, [KEY_DOWN], STEP_TIME)
					if k == 3:
						watched.filled = slams.puddles_left.filter(func(p): return is_instance_valid(p) and not p.gone).size()
			"dash":
				await t.wait_until(func(): return t.sm.current_state != slams or slams.clock >= landing - DASH_LEAD, 400)
				t.press(KEY_RIGHT)
				t.tap(KEY_W)
				await t.wait_until(func(): return t.sm.current_state != slams or slams.results.size() > k, 60)
				await t.wait_until(func(): return not t.player.is_dodging, 30)
				# On off the puddle the landing left, if the dash ended on it.
				var left = slams.puddles_left[k] if k < slams.puddles_left.size() else null
				await t.wait_until(func(): return left == null or not is_instance_valid(left) or not left.contains_feet(t.sm.player_feet()), 30)
				t.release(KEY_RIGHT)
			"walk":
				await t.wait_until(func(): return t.sm.current_state != slams or slams.latch_times.size() > k, 400)
				await walk(t, [KEY_RIGHT], WALK_TIME)
			"hit":
				await t.wait_until(func(): return t.sm.current_state != slams or slams.results.size() > k, 400)
		if t.sm.current_state != slams:
			break
	await t.wait_until(func(): return t.sm.current_state != slams or slams.beat == slams.Beat.SETTLE, 120)
	if t.sm.current_state == slams:
		watched.inside_at_settle = slams.results.size() == 5 and slams.results[4].feet_inside
		watched.settle_box = t.boss.body_box_rect(&"sleep")
	if answer == "walk":
		watched.ring_dash = await dash_through_last_ring(t)
	await t.wait_until(func(): return t.sm.current_state != slams, 120)
	await t.wait(20)
	t.physics_frame.disconnect(watch)
	# The nap: the floor round him as a spit keeps it, and the way from the player to him.
	var spit: Node = t.sm.states["Spit"]
	var danny: Vector2 = t.boss.global_position
	var around: Vector2 = spit.radii + spit.clear_of_danny
	var live: Array = t.sm.live_puddles()
	watched.round_him = live.filter(func(p): return ((p.global_position - danny) / around).length_squared() < 1.0).size()
	watched.way = slams.way_to_sides(t.sm.player_feet(), danny)
	watched.b_floor = Spit.open_floor(t, spit.radii, live.map(func(p): return p.global_position), t.sm.player_feet(), danny)
	return watched


# When slam `number`'s landing is due, on the state's own clock.
static func _landing_time(slams: Node, number: int) -> float:
	for entry in slams.schedule:
		if entry[1] == slams.Beat.IMPACT and entry[2] == number:
			return entry[0]
	return INF


# The walker is out beside the fifth landing: every other ring is taken away, and as the fifth's band is about to
# reach them they dash in across it, back toward where he landed.
static func dash_through_last_ring(t) -> Dictionary:
	var ring_script: GDScript = load(RING_SCRIPT)
	var rings: Array = t.boss.ring_layer.get_children().filter(func(r): return r.get_script() == ring_script and not r.is_queued_for_deletion())
	if rings.is_empty():
		return {"error": "no ring"}
	var last: Node2D = rings[-1]
	for ring in rings:
		if ring != last:
			ring.queue_free()
	t.clear_iframes()
	var health: int = t.player.playerHealth
	var shape: CollisionShape2D = t.player.hurtBox.get_node("CollisionShape2D")
	var half: float = shape.shape.size.x * shape.global_scale.x / 2.0
	var ring_id: int = last.get_instance_id()
	var reached := func() -> bool:
		if not is_instance_valid(last):
			return true
		var gap: float = absf(t.sm.player_feet().x - last.global_position.x) - half
		return last.radius + 36.0 + RING_DASH_AHEAD >= gap
	await t.wait_until(reached, 120)
	var inward: int = KEY_LEFT if t.sm.player_feet().x > last.global_position.x else KEY_RIGHT
	var untouched: bool = not t.defense.sources.has(ring_id)
	t.press(inward)
	t.tap(KEY_W)
	await t.wait_until(func(): return t.player.is_dodging, 10)
	var dash_at: float = t.defense.dash_start_time
	await t.wait_until(func(): return not t.player.is_dodging, 30)
	t.release(inward)
	await t.wait(20)
	var touched_at: float = t.defense.sources.get(ring_id, {}).get("contact", -INF)
	return {"untouched_before": untouched, "touched_in_dash": untouched and touched_at >= dash_at and touched_at - dash_at <= 0.18,
		"unhurt": t.player.playerHealth == health, "touch_after_dash": snappedf(touched_at - dash_at, 0.001)}
