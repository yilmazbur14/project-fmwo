extends RefCounted

# matt_glass_rows (the user, 2026-09-27): the Glass Row's glass by his health's share - two rows above three
# quarters of it, three above half, four from half down (MattStateMachine.glass_rows_by_share), all of them laid
# by his fury; phase two's stomps lay none. --fixed-fps 60.
#   With his health out of 100, at 100, 76, 75, 51, 50 and 1, a Glass Row started by the cycle and every boom
#   answered: the rows locked at the cycle's top; the rows his fury lays, as the bed - B and A - and any row
#   past it grown on in front, its segments covering exactly those rows and all of it glass by the first boom,
#   and the guides' row lines stopping at its edge; and the rows the glass comes to by the end: 2, 2, 3, 3, 4
#   and 4, the same as it laid, with phase two's two stomps from half down laying nothing. Every boom's window
#   at row F is the same above half his health, and phase_two_charge_extra longer from half down, and so is
#   the time from one boom's birth to the next's.
#   At his real health, 90: 68 is two rows, 67 and 46 three, 45 four.
#   At 75 with no presses: knocked to E and D, and the third miss is the glass in C - one hit of a whole
#   heart, and back to D.
#   Over phase two's four rows, at 50 and at 1: the true arrow a frame after each birth, and the true arrow
#   read in NORMAL_READ, miss nothing; no presses at all reach the glass on the second boom - one hit of a
#   whole heart, back to E, and no third boom; and a person reading each arrow in about 0.375 s
#   (matt_glass_bots' human, on the fight's seed), five rows at each, reaches the glass in at most
#   PERSON_GLASS_ROWS of the ten. One miss is free from row F over four rows of glass, which the user eased
#   with phase two's longer charge (2026-09-27): 1 of the 10 then, where it was 5 of 10 without it.

# His health out of 100, the rows the glass comes to, and the rows the fury lays.
const CASES := [[100, 2, 2], [76, 2, 2], [75, 3, 3], [51, 3, 3], [50, 4, 4], [1, 4, 4]]
const REAL_CASES := [[68, 2], [67, 3], [46, 3], [45, 4]]
const PHASE_TWO_CASES := [50, 1]
# The Glass Row modes' own answer (deafen_row's): 0.3 s after a boom's birth, inside even row F's window.
const NORMAL_READ := 0.3
# Of the person's ten phase-two rows, the most that may reach the glass: what it measured on 2026-09-27.
const PERSON_GLASS_ROWS := 1


static func run(t) -> void:
	await t.load_matt()
	t.track()
	var sm: Node = t.sm
	var boss: Node = t.boss
	var player: Node = t.player
	var glass: Node = sm.states["GlassRow"]
	var rows: int = sm.GLASS_ROW.row_names.size()
	var pinned: Array[String] = ["GlassRow"]
	sm.attack_rotation = pinned
	var real_max: int = boss.max_health

	t.log_p("-- the rows by his health, out of 100")
	boss.max_health = 100
	# Row F's window and the birth-to-birth pace, by phase: [phase one's, phase two's].
	var windows := [[], []]
	var paces := [[], []]
	for c in CASES:
		await reset(t)
		player.playerHealth = 1000
		boss.boss_health = c[0]
		sm.last_attack = ""
		sm.glass_rows_done = 0
		sm.start_cycle()
		var locked: int = sm.cycle_glass_rows
		var seen: Dictionary = await answered_row(t, glass)
		t.log_p("at %d: locked %d, %d sets, %s" % [c[0], locked, sm.cycle_sets, seen])
		var phase := 1 if sm.in_phase_two() else 0
		windows[phase].append(seen.window)
		paces[phase].append(seen.pace)
		t.check(locked == c[1] and seen.laid == c[2] and seen.came_to == c[1],
			"at %d%% the glass comes to %d rows, the fury laying %d (locked %d, laid %d, came to %d)" % [c[0], c[1], c[2], locked, seen.laid, seen.came_to])
		t.check(seen.stomps == sm.cycle_sets - 1, "with %d stomps between its %d sets, none of them laying glass" % [sm.cycle_sets - 1, sm.cycle_sets])
		var bed_rows: int = sm.GLASS_ROW.bed_rows
		t.check(seen.bed == sm.rows_band(rows - bed_rows) and seen.covers == sm.rows_band(rows - c[2])
			and seen.segments == sm.glass_segments * (1 + c[2] - bed_rows) and seen.whole,
			"its segments cover exactly those rows, the bed B and A and a row of them for each row past it, all glass by the first boom")
		t.check(is_equal_approx(seen.guides_to, sm.row_band(rows - c[2]).position.y), "the row guides stop at its edge (y %.0f)" % seen.guides_to)
		t.check(seen.answered == seen.booms and seen.booms == sm.boom_counts_by_tier[sm.tier()] and not seen.glass_hit,
			"and every one of the %d booms answered" % seen.booms)
	boss.max_health = real_max
	t.log_p("row F's window above half %s, from half down %s; birth to birth %s and %s" % [windows[0], windows[1], paces[0], paces[1]])
	var frame := 1.0 / 60.0
	var same := func(values: Array) -> bool: return values.all(func(v): return is_equal_approx(v, values[0]))
	t.check(same.call(windows[0]) and same.call(windows[1]) and same.call(paces[0]) and same.call(paces[1]),
		"the same window and pace at every health on each side of half")
	t.check(absf(windows[1][0] - windows[0][0] - sm.phase_two_charge_extra) <= frame + 0.001
		and absf(paces[1][0] - paces[0][0] - sm.phase_two_charge_extra) <= frame + 0.001,
		"phase two's %.2f s longer: window %.3f against %.3f, birth to birth %.3f against %.3f" % [sm.phase_two_charge_extra,
		windows[1][0], windows[0][0], paces[1][0], paces[0][0]])

	t.log_p("-- at his real health, out of %d" % real_max)
	var got := []
	for c in REAL_CASES:
		got.append(sm.glass_rows_for(float(c[0]) / real_max))
	t.check(got == REAL_CASES.map(func(c): return c[1]), "68, 67, 46 and 45 of %d: %s rows" % [real_max, got])

	t.log_p("-- at 75 with no presses")
	boss.max_health = 100
	var none_at_75: Dictionary = await bot_row(t, 75, func(_i: int, _arrow: StringName) -> Dictionary: return {})
	boss.max_health = real_max
	var hits: Array = t.events_of("HIT", &"matt_glass")
	t.log_p("%s, glass hits %d" % [none_at_75, hits.size()])
	t.check(none_at_75.outcomes == [&"missed", &"missed", &"missed"] and none_at_75.gaps == [sm.row_body_point(1), sm.row_body_point(2)],
		"knocked to E and D, and no fourth boom")
	t.check(none_at_75.glass and hits.size() == 1 and none_at_75.damage == 2 and none_at_75.row == 2,
		"the third miss is the glass in C: one hit of a whole heart, and back to D")

	t.log_p("-- the bots over phase two's four rows")
	boss.max_health = 100
	var true_arrow := func(_i: int, arrow: StringName) -> Dictionary: return {"at": 1.0 / 60.0, "key": t.ARROW_KEYS[arrow]}
	var normal := func(_i: int, arrow: StringName) -> Dictionary: return {"at": NORMAL_READ, "key": t.ARROW_KEYS[arrow]}
	var nothing := func(_i: int, _arrow: StringName) -> Dictionary: return {}
	var bot := RandomNumberGenerator.new()
	bot.seed = t.MATT_SEED
	var person := func(_i: int, arrow: StringName) -> Dictionary:
		return {"at": maxf(bot.randfn(t.MATT_GLASS_REACTION, t.MATT_GLASS_REACTION_SPREAD), 0.25), "key": t.ARROW_KEYS[arrow]}
	var person_glassed := 0
	for health in PHASE_TWO_CASES:
		for read in [[true_arrow, "a frame after each birth"], [normal, "%.2f s after each birth" % NORMAL_READ]]:
			var clean: Dictionary = await bot_row(t, health, read[0])
			t.log_p("at %d, the true arrow %s: %s" % [health, read[1], clean])
			t.check(clean.rows == 4 and clean.stomps == 2 and clean.fails == 0 and not clean.glass and clean.damage == 0,
				"at %d%%: the true arrow %s clears all 15 booms over the four rows" % [health, read[1]])
		var none: Dictionary = await bot_row(t, health, nothing)
		t.log_p("at %d, no presses: %s" % [health, none])
		t.check(none.glass and none.booms == 2 and none.damage == 2 and none.row == 1,
			"no presses reach the glass on the second boom: one hit of a whole heart, back to E, and no third")
		var misses := []
		var glassed := 0
		for n in t.MATT_GLASS_HUMAN_RUNS:
			var run: Dictionary = await bot_row(t, health, person)
			t.log_p("at %d, person %d: %d missed, glass %s; %s" % [health, n, run.fails, run.glass, run])
			misses.append(run.fails)
			glassed += 1 if run.glass else 0
		t.log_p("at %d, a person reading each arrow in about %.3f s: the glass in %d of %d rows, missed per row %s" % [
			health, t.MATT_GLASS_REACTION, glassed, t.MATT_GLASS_HUMAN_RUNS, misses])
		person_glassed += glassed
	var person_rows: int = t.MATT_GLASS_HUMAN_RUNS * PHASE_TWO_CASES.size()
	t.check(person_glassed <= PERSON_GLASS_ROWS, "a person reading each arrow in about %.3f s reaches the glass in at most %d of %d phase-two rows (%d)" % [
		t.MATT_GLASS_REACTION, PERSON_GLASS_ROWS, person_rows, person_glassed])
	boss.max_health = real_max
	await reset(t)


# Out of whatever he was doing, nothing of his left out, the player where the Glass Row modes start them.
static func reset(t) -> void:
	var sm: Node = t.sm
	sm.on_child_transition(sm.current_state, "Idle")
	sm.beat_timer.stop()
	sm.recover_timer.stop()
	for hazard in t.get_nodes_in_group(sm.HAZARD_GROUP):
		hazard.queue_free()
	t.clear_iframes()
	await t.wait(3)
	await t.settle_player(Vector2(700, 800))


# The Glass Row the cycle just started, every boom answered on its birth: its glass at the first boom and
# at the end, row F's window, and the time from one boom's birth to the next's inside a set, the shortest.
static func answered_row(t, glass: Node) -> Dictionary:
	var sm: Node = t.sm
	var rows: int = sm.GLASS_ROW.row_names.size()
	var seen := {"laid": -1, "came_to": -1, "bed": Rect2(), "covers": Rect2(), "segments": 0, "whole": false, "guides_to": -1.0,
		"booms": 0, "answered": 0, "glass_hit": false, "stomps": 0, "window": -1.0, "pace": INF}
	var pressed := {}
	var births := {}
	while sm.current_state == glass:
		await t.physics_frame
		if glass.beat != glass.Beat.BOOMS:
			continue
		if seen.laid < 0:
			var ground: Node = glass.glass_floor
			var rects: Array = ground.segment_rects()
			var union: Rect2 = rects[0]
			for r in rects:
				union = union.merge(r)
			var bed: Rect2 = rects[0]
			for i in sm.glass_segments:
				bed = bed.merge(rects[i])
			seen.laid = rows - glass.glass_top
			seen.bed = bed
			seen.covers = union
			seen.segments = rects.size()
			seen.whole = ground.revealed_count() == rects.size()
			seen.guides_to = ground.guide_spec.glass_top
		if glass.boom != null and not pressed.has(glass.boom_index):
			pressed[glass.boom_index] = true
			births[glass.boom_index] = glass.birth_clock
			t.tap(t.ARROW_KEYS[glass.arrows[glass.boom_index]])
	for i in births:
		if births.has(i + 1):
			seen.pace = minf(seen.pace, snappedf(births[i + 1] - births[i], 0.001))
	seen.came_to = rows - glass.glass_top
	seen.booms = glass.outcomes.size()
	seen.answered = Array(glass.outcomes).count(&"answered")
	seen.glass_hit = glass.glass_hit
	seen.stomps = glass.stomps
	seen.window = snappedf(glass.windows[0], 0.001) if not glass.windows.is_empty() else -1.0
	return seen


# A Glass Row the cycle starts at `health` of his 100, the player on 6 health, with `plan` answering it: handed
# each live boom's index and arrow, it returns {at, key} - a key pressed `at` seconds after the birth - or {} for
# none. What it came to.
static func bot_row(t, health: int, plan: Callable) -> Dictionary:
	var sm: Node = t.sm
	var glass: Node = sm.states["GlassRow"]
	var player: Node = t.player
	await reset(t)
	t.boss.boss_health = health
	player.playerHealth = 6
	player.healthUI.update_health(6)
	sm.last_attack = ""
	sm.glass_rows_done = 0
	sm.start_cycle()
	var planned := {}
	var gaps := []
	var last_phase := -1
	while sm.current_state == glass:
		await t.physics_frame
		if glass.beat != glass.Beat.BOOMS:
			continue
		if glass.boom_phase != last_phase:
			last_phase = glass.boom_phase
			if glass.boom_phase == glass.BoomPhase.GAP:
				gaps.append(player.global_position)
		if glass.boom == null:
			continue
		var i: int = glass.boom_index
		if not planned.has(i):
			planned[i] = plan.call(i, glass.arrows[i])
		var want: Dictionary = planned[i]
		if want.is_empty() or want.get("done", false):
			continue
		if glass.state_clock - glass.birth_clock >= want.at:
			want["done"] = true
			t.tap(want.key)
	return {"rows": sm.GLASS_ROW.row_names.size() - glass.glass_top, "outcomes": Array(glass.outcomes), "fails": glass.fails,
		"glass": glass.glass_hit, "booms": glass.windows.size(), "damage": 6 - player.playerHealth, "row": glass.row,
		"stomps": glass.stomps, "gaps": gaps}
