extends RefCounted

# mash_rates: the tiered mash's rates and what it pays, to the user's table of 2026-10-04 ("breaking a boss always pays
# off, hype always matters, and fast mashing is a bonus rather than a wall"). --fixed-fps 60, on V2 Eric.
#   rates     FinisherTierMeter with the finisher's own numbers, stepped at 60 fps: a press every 11, 10, 8, 7 and 6
#             frames (5.5, 6, 7.5, 8.6 and 10 a second) banks 0, 1, 1, 2 and 3 bars, and the lowest steady rates for
#             bars 1, 2 and 3 are about 6, 8 and 10 a second (RATE_BANDS)
#   jitter    at 8.5 a second with every interval drawn from 15% either side of its own, landing on frames, bar 2
#             comes JITTER_RUNS seeded runs in at least JITTER_FLOOR of them
#   pays      bars 1, 2 and 3 pay 25%, 35% and 50% of his health in all; a full hype meter makes that 1.6 times as
#             much, which is the same SUPERCHARGE_MULTIPLIER the single-bar uppercut's 25% -> 40% is; a boss that
#             counts uppercuts takes one more for the boosted one (uppercut_count)
#   live      a real Break and mash for each bar count, without and then with a full hype meter: what each juggle
#             takes off him in all, against the table (to a rounding), and the hype spent exactly by the hyped ones

# Presses every this many frames, and the bars they bank.
const RATE_TABLE := [[11, 0], [10, 1], [8, 1], [7, 2], [6, 3]]
# The lowest steady rate that banks each bar, in presses a second: the user's 6, 8 and 10, a bar 1 no harder than the
# single-bar finisher's (about 6 a second with a reaction to its prompt) and a bar 3 that a steady 10 makes.
const RATE_BANDS := [[5.6, 6.0], [7.8, 8.2], [9.5, 10.0]]
const JITTER_RATE := 8.5
const JITTER := 0.15
const JITTER_RUNS := 1000
const JITTER_FLOOR := 0.85
const JITTER_SEED := 20261004
# Cumulative, of his max health.
const PAYS := [0.25, 0.35, 0.50]
const MULTIPLIER := 1.6


static func run(t) -> void:
	await t.load_eric_v2()
	t.health_ok()
	var finisher: Node = t.player.get_node("Finisher")
	rates(t, finisher)
	jitter(t, finisher)
	pays(t, finisher)
	await live(t, finisher)


static func rates(t, finisher: Node) -> void:
	t.log_p("-- rates: gain %.3f, drains %s, windows %s" % [finisher.tier_gain, finisher.tier_drains, finisher.tier_windows])
	for row in RATE_TABLE:
		var run: Dictionary = t.model_mash(finisher, row[0])
		t.check(run.tier == row[1], "a press every %d frames (%.1f a second) banks %d (%d, at %s)" % [row[0], 60.0 / row[0], row[1], run.tier, run.banked_at])
	for bar in 3:
		var rate: float = t.threshold_rate(finisher, bar + 1)
		var band: Array = RATE_BANDS[bar]
		t.check(rate >= band[0] and rate <= band[1], "bar %d from %.2f presses a second, inside %s" % [bar + 1, rate, band])


# Each interval 1/rate times 1 +- JITTER, the press landing on the first frame at or after its time, as a key does on
# the next input flush.
static func jitter(t, finisher: Node) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = JITTER_SEED
	var meter_script: GDScript = load("res://Scripts/FinisherTierMeter.gd")
	var counts := [0, 0, 0, 0]
	for i in JITTER_RUNS:
		var meter = meter_script.new(finisher.tier_gain, finisher.tier_drains, finisher.tier_windows, finisher.tier_start_grace, finisher.tier_idle_stop)
		var next_press := rng.randf() / 60.0
		while not meter.resolved and meter.clock < 12.0:
			if meter.clock >= next_press - 1e-9:
				meter.press()
				next_press += (1.0 + rng.randf_range(-JITTER, JITTER)) / JITTER_RATE
			meter.advance(1.0 / 60.0)
		counts[meter.banked] += 1
	var two: float = float(counts[2] + counts[3]) / JITTER_RUNS
	t.log_p("-- jitter: %.1f a second, +-%d%%, %d runs: bars 0/1/2/3 %s" % [JITTER_RATE, roundi(JITTER * 100.0), JITTER_RUNS, counts])
	t.check(two >= JITTER_FLOOR, "bar 2 in %.1f%% of them, at least %d%%" % [two * 100.0, roundi(JITTER_FLOOR * 100.0)])


static func pays(t, finisher: Node) -> void:
	t.log_p("-- pays: shares %s, single-bar %.2f, multiplier %.2f" % [finisher.juggle_shares, finisher.finisher_damage_ratio, finisher.SUPERCHARGE_MULTIPLIER])
	var total := 0.0
	for bar in 3:
		total += finisher.juggle_shares[bar]
		t.check(is_equal_approx(total, PAYS[bar]), "%d bars pay %d%% in all (%.3f)" % [bar + 1, roundi(PAYS[bar] * 100.0), total])
	t.check(is_equal_approx(finisher.SUPERCHARGE_MULTIPLIER, MULTIPLIER) and is_equal_approx(finisher.finisher_damage_ratio * finisher.SUPERCHARGE_MULTIPLIER, 0.40),
		"full hype multiplies by %.1f, the single-bar uppercut's 25%% -> 40%%" % finisher.SUPERCHARGE_MULTIPLIER)
	t.check(finisher.SUPERCHARGE_UPPERCUTS == 1, "and a boss that counts uppercuts takes one more (%d)" % finisher.SUPERCHARGE_UPPERCUTS)
	# The count it hands such a boss, read off the finisher's own state as each contact would leave it.
	var counted := []
	for case in [[false, false, 0, 1], [true, false, 0, 1], [false, true, 2, 3], [true, true, 0, 3], [true, true, 1, 3], [true, true, 2, 3], [true, true, 0, 1]]:
		finisher.supercharged = case[0]
		finisher.tiered = case[1]
		finisher.juggle_index = case[2]
		finisher.juggle_tiers = case[3]
		counted.append(finisher.uppercut_count())
	finisher.supercharged = false
	finisher.tiered = false
	finisher.juggle_index = 0
	finisher.juggle_tiers = 0
	t.check(counted == [1, 2, 1, 1, 1, 2, 2], "counted: 1 plain, 2 hyped; a juggle's 1 each, its last 2 when hyped, a one-bar one too (%s)" % [counted])


static func live(t, finisher: Node) -> void:
	var hype: Node = t.player.get_node("Hype")
	var spends := [0]
	hype.hype_spent.connect(func(): spends[0] += 1)
	var dealt := []
	var on_hit := func(_index: int, _last: bool) -> void:
		dealt.append(t.boss.boss_health)
	finisher.juggle_hit.connect(on_hit)
	for hyped in [false, true]:
		for bar in 3:
			t.boss.boss_health = t.boss.max_health
			hype._set_hype(100.0 if hyped else 0.0)
			var spent_before: int = spends[0]
			dealt.clear()
			if not await t.break_into_prompt():
				t.check(false, "a Break and the opener put up the prompt")
				continue
			# The opener's punches have landed by the prompt: the juggle is what comes off him from here.
			var at_prompt: int = t.boss.boss_health
			var before := at_prompt
			await t.mash_tiered(t.TIER_PASS_FRAMES[bar])
			await t.wait_until(func(): return finisher.phase == t.FINISHER_OFF, 400)
			var took := []
			for health in dealt:
				took.append(before - health)
				before = health
			var total: int = at_prompt - t.boss.boss_health
			var want: float = t.boss.max_health * PAYS[bar] * (MULTIPLIER if hyped else 1.0)
			t.log_p("%s, %d bars: uppercuts %s, %d of %d (%.1f), hype spent %d" % ["hyped" if hyped else "plain", finisher.juggle_tiers, took, total, t.boss.max_health, want, spends[0] - spent_before])
			t.check(finisher.juggle_tiers == bar + 1 and absf(total - want) <= 1.0,
				"%s, %d bars: %d of his %d, %d%% x %.1f (%.1f)" % ["hyped" if hyped else "plain", bar + 1, total, t.boss.max_health, roundi(PAYS[bar] * 100.0), MULTIPLIER if hyped else 1.0, want])
			t.check(spends[0] - spent_before == (1 if hyped else 0), "the hype spent %s" % ("once" if hyped else "never"))
			await t.wait(90)
	finisher.juggle_hit.disconnect(on_hit)
