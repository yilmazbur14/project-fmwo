extends RefCounted

# matt_break_only (the Break-only knob): Carter's rule was his on 2026-10-04 (only his Break paid a finisher), and the
# user took it out of every fight but Jordan's kaiju on 2026-10-05. The mode keeps its name and holds both sides of the
# knob, MattScript.daze_in_recover. --fixed-fps 60.
#   window    live: his punish window takes three punches, 1 + 1 + 2, and the POW dazes him for the plain finisher
#   knob      daze_in_recover off: the same three punches, can_be_dazed() false on every step, the finisher never
#             starting
#   Break     a Break's daze opens the tiered mash, and the juggle pays
#   kill      from his full health, two hyped Breaks, each with its three punches and a two-bar mash, kill him
#   gauge     a parry a read: BREAK_READS of them from empty Break him and one fewer don't; a hit takes one back
#   phase     live, his first Break above phase_two_ratio of his health leaves him in phase one; phase_two_at_break on,
#             it starts phase two

const GAUGE_SPEC := "res://art_source/defense_tests/gauge_fights/matt.gd"


static func run(t) -> void:
	await t.load_matt()
	t.hold_break_gauge(t.boss)
	t.track()
	var sm: Node = t.sm
	var boss: Node = t.boss
	var finisher: Node = t.player.get_node("Finisher")
	finisher.min_press_interval = 0.0
	t.player.playerHealth = 1000

	t.log_p("-- his window, live")
	var live_on: bool = boss.daze_in_recover
	var got: Dictionary = await window(t)
	var dazed: bool = await t.wait_until(func(): return finisher.phase == t.FINISHER_DAZED and finisher.prompt_visible, 120)
	t.log_p("live: daze_in_recover %s; dealt %s, charged %s, dazed %s, tiered %s" % [live_on, got.dealt, got.charged, dazed, finisher.tiered])
	t.check(live_on and got.dealt == [1, 1, 2] and got.charged == [false, false, true] and dazed and not finisher.tiered,
		"his window takes three punches, 1 + 1 + 2, and the POW dazes him for the plain finisher")
	await t.mash_finisher()
	await t.wait(90)

	t.log_p("-- the knob off: Break-only")
	boss.daze_in_recover = false
	got = await window(t)
	t.log_p("three punches: dealt %s, charged %s; dazeable on %d steps; the finisher's phase %s" % [got.dealt, got.charged, got.dazeable, got.phases])
	t.check(got.dealt == [1, 1, 2] and got.dazeable == 0 and got.phases.all(func(p): return p == t.FINISHER_OFF),
		"with daze_in_recover off: the same three punches, can_be_dazed() false on every step, no finisher")
	boss.daze_in_recover = true

	t.log_p("-- two hyped Breaks kill him")
	var spec: Dictionary = load(GAUGE_SPEC).SPEC
	await t.reset_gauged(spec.home)
	boss.boss_health = boss.max_health
	var healths := [boss.boss_health]
	var tiers := []
	for k in 2:
		if boss.boss_health <= 0:
			break
		t.player.get_node("Hype")._set_hype(100.0)
		var up: bool = await t.break_into_prompt_fight(spec)
		var tiered: bool = finisher.tiered
		var banked: int = await t.mash_tiered(7)
		await t.wait_until(func(): return finisher.phase == t.FINISHER_OFF, 600)
		await t.wait(30)
		healths.append(boss.boss_health)
		tiers.append([up, tiered])
		if boss.boss_health > 0:
			await keep_health_reset(t, spec.home)
	t.log_p("health %s over two hyped Breaks; [prompt up, tiered] %s; defeated %s" % [healths, tiers, boss.defeated])
	t.check(tiers.size() == 2 and tiers.all(func(x): return x[0] and x[1]), "each Break's daze opens the tiered mash")
	t.check(boss.boss_health <= 0 and healths.size() == 3 and healths[1] > 0, "two hyped Breaks with their punches kill him from full health, and one doesn't (%s)" % [healths])

	t.log_p("-- the gauge")
	await t.load_matt()
	t.player.playerHealth = 1000
	var gauge: Node = t.boss.break_gauge
	var reads: int = t.boss.BREAK_READS
	# The parked modes switch it off themselves: the script's own default is the live game's.
	var fresh: Node = load("res://Scripts/States/Matt/MattStateMachine.gd").new()
	var phase_knob_default: bool = fresh.phase_two_at_break
	fresh.free()
	t.sm.phase_two_at_break = phase_knob_default
	t.sm.phase_two_ratio = 0.5
	t.sm.on_child_transition(t.sm.current_state, "Idle")
	t.sm.beat_timer.stop()
	await t.settle_player(Vector2(600, 760))
	for i in reads - 1:
		await t.parry_once(&"matt_mystic_shot")
		t.clear_iframes()
	var short: float = gauge.value
	var not_yet: bool = t.sm.current_state.name != "Broken"
	# Past the last press's window on the game's clock (a parry's hit-stop holds it), which would parry it.
	await t.wait_until(func(): return t.defense.clock - t.defense.last_press_time > t.defense.parry_window + 0.05, 240)
	var hit_result: int = t.front_hit(&"matt_mystic_shot", t.dummy_source())
	var after_hit: float = gauge.value
	t.log_p("the hit: result %d, the gauge %.2f, %s" % [hit_result, after_hit, t.sm.current_state.name])
	t.clear_iframes()
	await t.wait(70)
	await t.parry_once(&"matt_mystic_shot")
	t.clear_iframes()
	await t.parry_once(&"matt_mystic_shot")
	var broke: bool = await t.wait_until(func(): return t.sm.current_state.name == "Broken", 30)
	t.log_p("%d reads to a Break: %d left it at %.2f (not Broken %s); a hit took it to %.2f; two more parries Broke him %s" % [
		reads, reads - 1, short, not_yet, after_hit, broke])
	t.check(not_yet and is_equal_approx(short, (reads - 1) * gauge.parry_gain) and broke, "%d parries Break him and %d don't" % [reads, reads - 1])
	t.check(is_equal_approx(after_hit, short - gauge.hit_loss), "a hit takes one read back")
	var ratio: float = t.boss.get_health_ratio()
	var live_two: bool = t.sm.in_phase_two()
	t.sm.phase_two_at_break = true
	var knob_two: bool = t.sm.in_phase_two()
	t.log_p("Broken at %.2f of his health, Breaks %d: phase two live %s (phase_two_at_break %s), with it on %s" % [ratio, t.sm.breaks_taken, live_two, phase_knob_default, knob_two])
	t.check(ratio > 0.5 and t.sm.breaks_taken == 1 and not phase_knob_default and not live_two,
		"live, his first Break above half his health leaves him in phase one")
	t.check(knob_two, "and with phase_two_at_break on it starts phase two")


# A fresh window at HOME, three punches from under him: what each dealt, whether each was charged, how many steps he
# could be dazed on and the finisher's phase on each.
static func window(t) -> Dictionary:
	var sm: Node = t.sm
	var boss: Node = t.boss
	for hazard in t.get_nodes_in_group(sm.HAZARD_GROUP):
		hazard.queue_free()
	t.player.combo.reset()
	sm.on_child_transition(sm.current_state, "Idle")
	sm.beat_timer.stop()
	await t.wait(3)
	boss.boss_health = boss.max_health
	sm.on_child_transition(sm.current_state, "Recover")
	sm.recover_timer.stop()
	await t.wait(3)
	t.place_under(boss.get_finisher_hurtbox())
	await t.wait(4)
	var dealt := []
	var charged := []
	var on_landed := func(_target, amount: int, was_charged: bool):
		dealt.append(amount)
		charged.append(was_charged)
	t.player.combo.punch_landed.connect(on_landed)
	var dazeable := 0
	var phases := []
	for i in 3:
		t.tap(KEY_Q)
		for f in 34:
			await t.physics_frame
			if boss.can_be_dazed():
				dazeable += 1
			phases.append(t.player.get_node("Finisher").phase)
		await t.wait(6)
	t.player.combo.punch_landed.disconnect(on_landed)
	return {"dealt": dealt, "charged": charged, "dazeable": dazeable, "phases": phases}


# Back at HOME, idle, gauge empty and open, his health as it is.
static func keep_health_reset(t, home: Vector2) -> void:
	var health: int = t.boss.boss_health
	await t.reset_gauged(home)
	t.boss.boss_health = health
	t.boss._refresh_health_bar()
