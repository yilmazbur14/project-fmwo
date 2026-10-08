extends RefCounted

# matt_deafen_rate (the user: "Matts roar needs to be harder to mash", 2026-09-27, and "even harder", 2026-09-28;
# then on 2026-10-04 every mash in the game was reset round about 6, 8 and 10 a second for the finisher's three
# bars, and RESIST! was set to the second): the press rate the Deafening Yell's RESIST! mash asks, on each tuning
# it has had. Real time (--max-fps 60): MashInput weighs a press against the last one in real seconds.
#   The rates: MashCurve stepped at 60 Hz over deafen_time, a steady rate's presses from the yell's first step,
#   on every tuning in HISTORY and on his live knobs; the rate that wins is the lowest from which every rate up
#   to RATE_SPAN faster wins too, and the rate that loses the highest from which every rate down to RATE_SPAN
#   slower fails. Between the two the yell's last frames decide it. The live rate that wins is under TARGET and
#   within NEAR of it, TARGET wins even a first reaction (LATE) late, SLOW never wins, and FAST does.
#   Then mashed for real, a steady rate's presses on the finisher's pair: on the last tuning's knobs, MARGIN over
#   its rate mashes through and TARGET fails; on the live ones SLOW fails, and so does the new rate that loses;
#   MARGIN over the new rate that wins mashes through, and so do TARGET, TARGET starting LATE after the yell's
#   first step, COMFORTABLE and FAST, each with its time to win.

const MashCurve := preload("res://Scripts/MashCurve.gd")
# His tunings before the live one, oldest first: the date it was replaced, its gain and its drain.
const HISTORY := [
	{"until": "2026-09-27", "gain": 0.107, "drain": 0.14},
	{"until": "2026-09-28", "gain": 0.107, "drain": 0.20},
	{"until": "2026-10-04", "gain": 0.095, "drain": 0.215},
]
const RATE_STEP := 0.01
const RATE_SPAN := 1.5
const MARGIN := 0.1
# The finisher's second bar on the 2026-10-04 mash: about 8 presses a second, which has to win.
const TARGET := 8.0
# The progressive mash's rule: winnable within 10% of its rate, so the rate that wins sits no further under it.
const NEAR := 0.1
# A whole press a second under TARGET: never wins.
const SLOW := 7.0
const COMFORTABLE := 9.0
const FAST := 10.0
# A first reaction to the RESIST! prompt, the model player's: their mashing starts this late.
const LATE := 0.25


static func run(t) -> void:
	await t.load_matt()
	t.player.playerHealth = 1000
	var sm: Node = t.sm

	t.log_p("-- the rates")
	for tuning in HISTORY:
		t.log_p("until %s: gain %.3f, drain %.3f, a steady %.2f presses a second won" % [tuning.until, tuning.gain, tuning.drain,
			needed(tuning.gain, tuning.drain, sm.deafen_time)])
	var last: Dictionary = HISTORY[-1]
	var old_rate := needed(last.gain, last.drain, sm.deafen_time)
	var new_rate := needed(sm.deafen_gain, sm.deafen_drain, sm.deafen_time)
	var lose_rate := losing(sm.deafen_gain, sm.deafen_drain, sm.deafen_time, new_rate)
	var gain: float = sm.deafen_gain
	var drain: float = sm.deafen_drain
	var time: float = sm.deafen_time
	t.log_p("now: gain %.3f, drain %.3f, a steady %.2f a second wins (it was %.2f); %.2f and under never do, and the yell's last frames decide the ones between; %.0f a second wins in %.3f s (%.3f s starting %.2f s late), %.0f in %.3f s, %.0f in %.3f s" % [
		gain, drain, new_rate, old_rate, lose_rate, TARGET, win_time(TARGET, gain, drain, time), win_time(TARGET, gain, drain, time, LATE), LATE,
		COMFORTABLE, win_time(COMFORTABLE, gain, drain, time), FAST, win_time(FAST, gain, drain, time)])
	t.check(new_rate <= TARGET and new_rate >= TARGET * (1.0 - NEAR), "the rate that wins is %.2f a second: under %.0f, the second bar's, and within %.0f%% of it" % [
		new_rate, TARGET, NEAR * 100.0])
	t.check(win_time(TARGET, gain, drain, time, LATE) < INF, "a steady %.0f a second wins even starting %.2f s late" % [TARGET, LATE])
	t.check(lose_rate >= SLOW and not wins(SLOW, gain, drain, time), "%.0f a second never wins (the fastest that never does is %.2f)" % [SLOW, lose_rate])
	t.check(wins(FAST, gain, drain, time), "and a steady %.0f a second wins" % FAST)

	t.log_p("-- mashed for real")
	sm.deafen_gain = last.gain
	sm.deafen_drain = last.drain
	var runs := [await mash(t, old_rate + MARGIN), await mash(t, TARGET)]
	sm.deafen_gain = gain
	sm.deafen_drain = drain
	for rate in [SLOW, lose_rate, new_rate + MARGIN, TARGET, COMFORTABLE, FAST]:
		runs.append(await mash(t, rate))
	runs.append(await mash(t, TARGET, LATE))
	for r in runs:
		t.log_p("%s" % [r])
	t.check(runs[0].passed and not runs[1].passed, "on the last tuning's knobs %.2f a second mashed through and %.0f failed (topped out at %.3f)" % [
		runs[0].rate, TARGET, runs[1].peak])
	t.check(not runs[2].passed, "on the live ones %.0f a second fails (topped out at %.3f)" % [SLOW, runs[2].peak])
	t.check(not runs[3].passed, "%.2f a second, the fastest that never wins, fails (topped out at %.3f)" % [runs[3].rate, runs[3].peak])
	t.check(runs[4].passed, "%.2f a second, just over the rate that wins, mashes through, in %.3f s" % [runs[4].rate, runs[4].won_at])
	t.check(runs[5].passed and runs[8].passed, "%.0f a second mashes through, in %.3f s, and in %.3f s starting %.2f s late" % [
		TARGET, runs[5].won_at, runs[8].won_at, LATE])
	t.check(runs[6].passed and runs[7].passed, "and so do %.0f a second, in %.3f s, and %.0f, in %.3f s" % [COMFORTABLE, runs[6].won_at, FAST, runs[7].won_at])


# Whether a steady `rate`, its first press on the yell's first step, fills the bar inside `time`.
static func wins(rate: float, gain: float, drain: float, time: float) -> bool:
	return win_time(rate, gain, drain, time) < INF


# When a steady `rate`, starting `late` s after the yell's first step, fills the bar, in seconds from that step,
# or INF if not inside `time`.
static func win_time(rate: float, gain: float, drain: float, time: float, late := 0.0) -> float:
	var meter := 0.0
	var pressed := 0
	for step in roundi(time * 60.0):
		var clock := step / 60.0
		while late + pressed / rate <= clock + 0.000001:
			meter = minf(meter + MashCurve.gain(gain, meter), 1.0)
			pressed += 1
			if meter >= 1.0:
				return clock
		meter = maxf(meter - MashCurve.drain(drain, meter) / 60.0, 0.0)
	return INF


# The lowest rate, to RATE_STEP, from which every rate up to RATE_SPAN faster wins.
static func needed(gain: float, drain: float, time: float) -> float:
	var span := roundi(RATE_SPAN / RATE_STEP)
	var at := roundi(1.0 / RATE_STEP)
	while at * RATE_STEP < 20.0:
		var holds := wins(at * RATE_STEP, gain, drain, time)
		var k := 1
		while holds and k <= span:
			holds = wins((at + k) * RATE_STEP, gain, drain, time)
			k += 1
		if holds:
			return at * RATE_STEP
		at += k
	return INF


# The highest rate under `below`, to RATE_STEP, from which every rate down to RATE_SPAN slower fails.
static func losing(gain: float, drain: float, time: float, below: float) -> float:
	var span := roundi(RATE_SPAN / RATE_STEP)
	var at := roundi(below / RATE_STEP) - 1
	while at > span:
		var holds := not wins(at * RATE_STEP, gain, drain, time)
		var k := 1
		while holds and k <= span:
			holds = not wins((at - k) * RATE_STEP, gain, drain, time)
			k += 1
		if holds:
			return at * RATE_STEP
		at -= k
	return 0.0


# A Glass Row with the yell, its RESIST! mashed at a steady `rate` on the finisher's pair from `late` s after the
# yell's first step; over once the yell is. When it mashed through, on the yell's own clock.
static func mash(t, rate: float, late := 0.0) -> Dictionary:
	var sm: Node = t.sm
	var glass: Node = sm.states["GlassRow"]
	sm.on_child_transition(sm.current_state, "Idle")
	sm.beat_timer.stop()
	sm.recover_timer.stop()
	await t.wait(3)
	await t.settle_player(Vector2(700, 800))
	t.glass_row(5, true)
	var pressed := 0
	var peak := 0.0
	var yelled := false
	var won_at := -1.0
	while sm.current_state == glass and not (yelled and glass.beat != glass.Beat.DEAFEN):
		await t.physics_frame
		if glass.beat != glass.Beat.DEAFEN:
			continue
		yelled = true
		if glass.deafen_passed and won_at < 0.0:
			won_at = glass.beat_clock
		while late + pressed / rate <= glass.beat_clock + 0.000001:
			t.tap(t.MASH_KEYS[glass.pair[pressed % 2]])
			pressed += 1
		peak = maxf(peak, glass.meter)
	var result := {"rate": snappedf(rate, 0.01), "late": late, "passed": glass.deafen_passed, "presses": pressed,
		"peak": snappedf(maxf(peak, glass.meter), 0.001), "won_at": snappedf(won_at, 0.001)}
	sm.on_child_transition(sm.current_state, "Idle")
	sm.beat_timer.stop()
	await t.wait(3)
	return result
