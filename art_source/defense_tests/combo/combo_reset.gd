extends RefCounted

# combo_reset [fight=<fight>]: the combo's count lives PlayerCombo.COMBO_RESET_TIME without a punch landing, and
# then starts again (the user, 2026-10-04: "theres a problem where if you hit the boss and he goes for an attack,
# the combo counter transfers over and gets to 3 but no mash? so lets make sure the combo resets after like a
# second of not hitting"). Timed on the combo's own game clock, which a pause stops. In a boss's opening, as
# broken_combo opens it; Eric's parry stagger never dazes, so fight=eric (the suite's default) runs in Burak's
# Taunt instead. --fixed-fps 60.
#   lapse     two punches, then nothing: at 0.9 s the count is still 2 and its 2 HITS up, it starts again
#             COMBO_RESET_TIME after the second punch landed, the counter fades out with it, and a punch at 1.1 s
#             lands as 1 HIT, uncharged, with no finisher.
#   steady    three punches, each landing 0.75 to 0.9 s after the last: the third is the POW, and the finisher's
#             mash opens if he can be dazed then (and no finisher starts if he can't, as in a Break-only fight).
#   paused    two punches, then the pause screen for 2 s half a second after the second: the combo's clock and
#             count hold through it, the counter stays up, and the punch after the resume is the POW.
#   whiffs    one punch, then swings into the air until 1.1 s on: they don't keep it alive, and it starts again
#             COMBO_RESET_TIME after the punch.
#   refusals  the same with punches he refuses, his hurtbox off under the fist.
#   next      the user's report: two punches, his opening over (Idle, as he goes for an attack), and his next
#             opening 1.1 s on: its first punch lands as 1 HIT, not the POW.
#   pow       a POW in an opening with no daze left to give: no finisher, the count 0 at once, its 3 POW! gone by
#             a second on, and the count still 0.
# Matt screams at a whiff or a refusal after a punch short of the POW (broken_combo.SCREAMS), so his run skips
# whiffs and refusals.

const BrokenCombo := preload("res://art_source/defense_tests/combo/broken_combo.gd")
const ComboCounterUI := preload("res://Scripts/ComboCounterUI.gd")

const STEP := 1.0 / 60.0
# Game seconds after a landed punch: the count still up, and past its reset.
const BEFORE := 0.9
const AFTER := 1.1
# The steady case's punches land about this long after the last, pressed that less the time from a press to
# its landing (the arm's way out, about a quarter of a second), and are held to STEADY_FLOOR to BEFORE.
const STEADY_GAP := 0.86
const STEADY_FLOOR := 0.75
# The pause case: pressed this long after the second punch landed, held this many frames.
const PAUSE_AT := 0.5
const PAUSE_FRAMES := 120


static func run(t) -> void:
	var key: String = "burak" if t.fight == "eric" else t.fight
	if not t.PUNISH_WINDOWS.has(key):
		t.check(false, "combo_reset knows no opening for fight=%s" % key)
		return
	await t.load_fight(key, t.STATE_INTROS.has(key))
	await t.clear_intro(key)
	if t.STATE_INTROS.has(key):
		await t.wait_until(func(): return t.vs_card() != null and t.vs_card().is_playing(), t.VS_CARD_WAIT_FRAMES)
		await t.skip_vs_card()
	t.player.playerHealth = 1000
	t.boss = t.current_scene.get_node(t.PUNISH_WINDOWS[key][0])
	t.sm = t.boss.state_machine
	var combo: Node = t.player.combo
	t.log_p("fight=%s, COMBO_RESET_TIME %.2f s" % [key, combo.COMBO_RESET_TIME])
	t.check(is_equal_approx(combo.COMBO_RESET_TIME, 1.0), "the count lives a second without a landed punch (%.2f s)" % combo.COMBO_RESET_TIME)

	# The combo's clock at each landed punch, and at each reset.
	var log := {"landed": [], "resets": []}
	combo.punch_landed.connect(func(_target, _dealt, _charged): log.landed.append(combo.clock))
	combo.combo_changed.connect(func(count: int, _charged: bool):
		if count == 0:
			log.resets.append(combo.clock))

	await lapse(t, key, log)
	await steady(t, key, log)
	await paused(t, key, log)
	if not BrokenCombo.SCREAMS.has(key):
		await lost(t, key, log, "whiffs")
		await lost(t, key, log, "refusals")
	await next_opening(t, key, log)
	await pow_no_daze(t, key, log)


static func lapse(t, key: String, log: Dictionary) -> void:
	t.log_p("-- lapse: two punches, then nothing")
	var combo: Node = t.player.combo
	var counter: Label = BrokenCombo.counter_of(t)
	var finisher: Node = t.player.get_node("Finisher")
	await BrokenCombo.open(t, key)
	var pows := [0]
	var on_pow := func(_target): pows[0] += 1
	combo.charged_hit_landed.connect(on_pow)
	log.resets.clear()
	var first: Dictionary = await BrokenCombo.punch(t, "fresh")
	var second: Dictionary = await BrokenCombo.punch(t, "fresh")
	var landed: float = log.landed[-1]
	await t.wait_until(func(): return combo.clock - landed >= BEFORE, 300)
	var held := {"count": combo.count, "text": counter.text, "alpha": counter.modulate.a}
	await t.wait_until(func(): return combo.clock - landed >= AFTER, 300)
	var reset_after: float = log.resets[0] - landed if log.resets.size() > 0 else -1.0
	await t.wait(ceili(ComboCounterUI.FADE_TIME / STEP) + 2)
	var faded: float = counter.modulate.a
	var third: Dictionary = await BrokenCombo.punch(t, "fresh")
	await t.wait(3)
	combo.charged_hit_landed.disconnect(on_pow)
	t.log_p("dealt %s, counts %s; at %.1f s the count %d, '%s' at %.2f; reset %.3f s after the second landed; the counter at %.2f after its fade; the third punch %d dealt, charged %s, count %d, '%s'" % [
		[first.dealt, second.dealt], [first.count, second.count], BEFORE, held.count, held.text, held.alpha, reset_after, faded, third.dealt, third.charged, third.count, third.counter])
	t.check(first.dealt == 1 and second.dealt == 1 and second.count == 2 and second.counter == "2 HITS", "two punches land: 2 HITS")
	t.check(held.count == 2 and held.text == "2 HITS" and held.alpha > 0.99, "%.1f s on the count is still 2, and the counter still up" % BEFORE)
	t.check(log.resets.size() == 1 and reset_after >= combo.COMBO_RESET_TIME - 0.0001 and reset_after <= combo.COMBO_RESET_TIME + 2.0 * STEP,
		"it starts again %.3f s after the second punch landed, once" % reset_after)
	t.check(is_zero_approx(faded), "and the counter fades out with it (%.2f)" % faded)
	t.check(third.count_before == 0 and third.dealt == 1 and not third.charged and third.count == 1 and third.counter == "1 HIT",
		"a punch %.1f s on lands as 1 HIT, not the POW (%d dealt, charged %s, count %d, '%s')" % [AFTER, third.dealt, third.charged, third.count, third.counter])
	t.check(pows[0] == 0 and not finisher.is_active(), "and no POW, no finisher")
	await BrokenCombo.settle(t)


static func steady(t, key: String, log: Dictionary) -> void:
	t.log_p("-- steady: three punches, each landing up to %.1f s after the last" % BEFORE)
	var combo: Node = t.player.combo
	var finisher: Node = t.player.get_node("Finisher")
	await BrokenCombo.open(t, key)
	log.resets.clear()
	var pressed: float = combo.clock
	var runs := [await BrokenCombo.punch(t, "fresh")]
	var latency: float = log.landed[-1] - pressed
	var gaps := []
	var dazeable := false
	for i in 2:
		var landed: float = log.landed[-1]
		await t.wait_until(func(): return combo.clock - landed >= STEADY_GAP - latency, 300)
		if i == 1:
			dazeable = t.boss.can_be_dazed()
		runs.append(await BrokenCombo.punch(t, "fresh"))
		gaps.append(log.landed[-1] - landed)
	var mashed := false
	if dazeable:
		mashed = await t.wait_until(func(): return finisher.phase == t.FINISHER_DAZED and finisher.prompt_visible, 120)
	t.log_p("a press lands %.3f s on; gaps %s s; dealt %s, charged %s, counts %s, '%s'; %s, the finisher %s" % [latency, gaps.map(func(g): return snappedf(g, 0.001)), runs.map(func(r): return r.dealt),
		runs.map(func(r): return r.charged), runs.map(func(r): return r.count), runs[-1].counter, "he can be dazed" if dazeable else "he can't be dazed",
		"mashing" if mashed else ("running" if finisher.is_active() else "off")])
	t.check(gaps.all(func(g): return g >= STEADY_FLOOR and g <= BEFORE), "each punch landed %.2f to %.1f s after the last (%s)" % [STEADY_FLOOR, BEFORE, gaps])
	t.check(log.resets.is_empty() and runs.map(func(r): return r.count) == [1, 2, 0], "the count never started again on the way: 1, 2, then the POW's 0 (%s)" % [runs.map(func(r): return r.count)])
	t.check(runs[2].charged and runs[2].dealt == combo.charged_damage and runs[2].counter == "3 POW!", "the third is the POW: charged, %d, 3 POW!" % combo.charged_damage)
	if dazeable:
		t.check(mashed, "he could be dazed, and the finisher's mash opens")
	else:
		t.check(not finisher.is_active() and combo.count == 0, "he couldn't be dazed: no finisher starts, and the count is 0")
	await BrokenCombo.settle(t)


static func paused(t, key: String, log: Dictionary) -> void:
	t.log_p("-- paused: two punches, then %d frames of the pause screen %.1f s after the second" % [PAUSE_FRAMES, PAUSE_AT])
	var combo: Node = t.player.combo
	var counter: Label = BrokenCombo.counter_of(t)
	var finisher: Node = t.player.get_node("Finisher")
	var pause: Node = t.pause_menu()
	await BrokenCombo.open(t, key)
	log.resets.clear()
	await BrokenCombo.punch(t, "fresh")
	var second: Dictionary = await BrokenCombo.punch(t, "fresh")
	var landed: float = log.landed[-1]
	await t.wait_until(func(): return combo.clock - landed >= PAUSE_AT, 300)
	# A test scene's pause screen never opens (PauseMenu.can_open: not a ladder fight), so there the tree is
	# paused the way the screen pauses it.
	var by_menu: bool = pause.can_open()
	if by_menu:
		await t.tap_pause()
	else:
		t.paused = true
		await t.wait(3)
	var opened: bool = t.paused and (pause.is_open() or not by_menu)
	var at_pause := {"clock": combo.clock, "count": combo.count, "alpha": counter.modulate.a}
	await t.wait(PAUSE_FRAMES)
	var under := {"clock": combo.clock, "count": combo.count, "alpha": counter.modulate.a, "text": counter.text}
	if by_menu:
		await t.tap_pause()
		# The pause screen's resume grace is real time, which a --fixed-fps run barely spends: dropped, as
		# skip_vs_card drops the card's, so the press after the resume is a press.
		pause.grace_until_msec = 0
	else:
		t.paused = false
		await t.wait(3)
	var resumed := {"clock": combo.clock, "count": combo.count, "closed": not pause.is_open() and not t.paused}
	if not by_menu:
		t.log_p("this scene's pause screen doesn't open: the tree paused by hand")
	var dazeable: bool = t.boss.can_be_dazed()
	var pow: Dictionary = await BrokenCombo.punch(t, "fresh")
	var mashed := false
	if dazeable:
		mashed = await t.wait_until(func(): return finisher.phase == t.FINISHER_DAZED and finisher.prompt_visible, 120)
	t.log_p("paused %s at %.3f s after the second, count %d; %d paused frames on the clock moved %.4f s, count %d, '%s' at %.2f; resumed at %.3f s, count %d; the punch %d dealt, charged %s, '%s'; the finisher %s" % [
		opened, at_pause.clock - landed, at_pause.count, PAUSE_FRAMES, under.clock - at_pause.clock, under.count, under.text, under.alpha, resumed.clock - landed, resumed.count,
		pow.dealt, pow.charged, pow.counter, "mashing" if mashed else ("running" if finisher.is_active() else "off")])
	t.check(second.count == 2 and opened and at_pause.count == 2, "two punches, then the pause screen with the count at 2")
	t.check(is_equal_approx(under.clock, at_pause.clock) and under.count == 2 and log.resets.is_empty(), "%d paused frames don't move the combo's clock or its count" % PAUSE_FRAMES)
	t.check(under.text == "2 HITS" and is_equal_approx(under.alpha, at_pause.alpha), "and the counter holds its 2 HITS through it")
	t.check(resumed.closed and resumed.count == 2 and resumed.clock - landed < combo.COMBO_RESET_TIME, "resumed with the count still 2, %.3f s of its second used" % (resumed.clock - landed))
	t.check(pow.count_before == 2 and pow.charged and pow.counter == "3 POW!", "the punch after the resume is the POW")
	if dazeable:
		t.check(mashed, "and the finisher's mash opens")
	else:
		t.check(not finisher.is_active() and combo.count == 0, "he couldn't be dazed: no finisher, and the count is 0")
	await BrokenCombo.settle(t)


# One punch, then swings that don't land - into the air, or at him with his hurtbox off - until AFTER: none of
# them keeps the count alive.
static func lost(t, key: String, log: Dictionary, how: String) -> void:
	t.log_p("-- %s: one punch, then %s until %.1f s on" % [how, "swings into the air" if how == "whiffs" else "punches he refuses", AFTER])
	var combo: Node = t.player.combo
	await BrokenCombo.open(t, key)
	var spot: Vector2 = t.player.global_position
	var hurtbox: Area2D = t.boss.get_finisher_hurtbox()
	log.resets.clear()
	var missed := [0]
	var refused := [0]
	var on_missed := func(): missed[0] += 1
	var on_refused := func(_target): refused[0] += 1
	combo.punch_missed.connect(on_missed)
	combo.punch_refused.connect(on_refused)
	var first: Dictionary = await BrokenCombo.punch(t, "fresh")
	var landed: float = log.landed[-1]
	var landings: int = log.landed.size()
	if how == "whiffs":
		await t.settle_player(BrokenCombo.whiff_spot(t, spot))
	else:
		hurtbox.set_deferred("monitoring", false)
		hurtbox.set_deferred("monitorable", false)
		await t.wait(3)
	var swings := []
	while combo.clock - landed < AFTER:
		swings.append(await BrokenCombo.punch(t, "fresh"))
	combo.punch_missed.disconnect(on_missed)
	combo.punch_refused.disconnect(on_refused)
	if how != "whiffs":
		hurtbox.set_deferred("monitoring", true)
		hurtbox.set_deferred("monitorable", true)
	await t.wait(3)
	var reset_after: float = log.resets[0] - landed if log.resets.size() > 0 else -1.0
	var lost_count: int = missed[0] if how == "whiffs" else refused[0]
	t.log_p("the punch %d dealt; %d swings after it, %d missed, %d refused, counts %s; reset %.3f s after the punch" % [first.dealt, swings.size(), missed[0], refused[0],
		swings.map(func(s): return s.count), reset_after])
	t.check(first.dealt == 1 and first.count == 1, "%s: the punch lands, the count 1" % how)
	t.check(swings.size() >= 2 and lost_count == swings.size() and log.landed.size() == landings, "%s: %d swings after it, none landing, every one %s" % [how, swings.size(), "missed" if how == "whiffs" else "refused"])
	t.check(log.resets.size() == 1 and reset_after >= combo.COMBO_RESET_TIME - 0.0001 and reset_after <= combo.COMBO_RESET_TIME + 2.0 * STEP and combo.count == 0,
		"%s: they don't keep it alive, and it starts again %.3f s after the punch" % [how, reset_after])
	await t.settle_player(spot)
	await BrokenCombo.settle(t)


# The user's report: two punches, his opening over as he goes for an attack, and his next one.
static func next_opening(t, key: String, log: Dictionary) -> void:
	t.log_p("-- next: two punches, his opening over, and his next one %.1f s on" % AFTER)
	var combo: Node = t.player.combo
	var finisher: Node = t.player.get_node("Finisher")
	await BrokenCombo.open(t, key)
	log.resets.clear()
	await BrokenCombo.punch(t, "fresh")
	var second: Dictionary = await BrokenCombo.punch(t, "fresh")
	var landed: float = log.landed[-1]
	t.sm.on_child_transition(t.sm.current_state, "Idle")
	await t.wait(2)
	for timer in t.boss.find_children("*", "Timer", true, false):
		timer.stop()
	await t.wait_until(func(): return combo.clock - landed >= AFTER, 300)
	var before: int = combo.count
	await BrokenCombo.open(t, key, true)
	var first: Dictionary = await BrokenCombo.punch(t, "fresh")
	await t.wait(3)
	t.log_p("the second %d, count %d; at his next opening the count %d; its first punch %d dealt, charged %s, count %d, '%s'; the finisher %s" % [second.dealt, second.count, before,
		first.dealt, first.charged, first.count, first.counter, "running" if finisher.is_active() else "off"])
	t.check(second.count == 2 and before == 0 and log.resets.size() == 1, "two punches, and by his next opening the count has started again")
	t.check(first.dealt == 1 and not first.charged and first.count == 1 and first.counter == "1 HIT" and not finisher.is_active(),
		"its first punch lands as 1 HIT, not a POW with no mash (%d dealt, charged %s, '%s')" % [first.dealt, first.charged, first.counter])
	await BrokenCombo.settle(t)


# A POW with no daze to give: the count is 0 at once and nothing is left up.
static func pow_no_daze(t, key: String, log: Dictionary) -> void:
	t.log_p("-- pow: three punches in an opening with no daze left to give")
	var combo: Node = t.player.combo
	var counter: Label = BrokenCombo.counter_of(t)
	var finisher: Node = t.player.get_node("Finisher")
	await BrokenCombo.open(t, key)
	# After the window's Enter, which clears it: the POW deals its damage and the opening runs on.
	t.boss.daze_used = true
	var runs := []
	for i in 3:
		runs.append(await BrokenCombo.punch(t, "fresh"))
	await t.wait(2)
	var after_pow := {"count": combo.count, "finisher": finisher.is_active()}
	await t.wait(60)
	var later := {"count": combo.count, "alpha": counter.modulate.a}
	t.log_p("dealt %s, charged %s, '%s'; the count %d right after, the finisher %s; a second on the count %d, the counter at %.2f" % [runs.map(func(r): return r.dealt),
		runs.map(func(r): return r.charged), runs[2].counter, after_pow.count, "running" if after_pow.finisher else "off", later.count, later.alpha])
	t.check(runs[2].charged and runs[2].counter == "3 POW!" and not after_pow.finisher, "the POW, and no finisher")
	t.check(after_pow.count == 0 and later.count == 0, "the count is 0 at once, and stays there")
	t.check(is_zero_approx(later.alpha), "and the 3 POW! is gone a second on (%.2f)" % later.alpha)
	await BrokenCombo.settle(t)
