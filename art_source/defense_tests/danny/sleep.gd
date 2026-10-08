extends RefCounted

# danny_sleep (coder A): his nap after the string, and the window to punish him in (DannyBossSleep), opened by a
# bare transition once the fight has settled into Idle, with 38 of his 120 HP so he has room to heal, and so the
# window (34 at most: 4 from the punches, 30 from the finisher) leaves him up. Real time (--max-fps 60): the
# finisher's mash counts real seconds.
#   afk     nobody touches him: a tick of one HP every 1/(0.05 x max health) s from the 0.5 s settle, each "+N"
#           the HP it healed, about 27 HP back, then he wakes into Idle at 5.0 s.
#   hurry   the player is at him from the start: three punches, the third charged, daze him; the
#           finisher is the single-bar one, and its uppercut ends the nap. Net at least 25 off him.
#   slow    the same, starting 2.5 s into the nap. Net at least 10.
# Those floors were 12 and 6 at his old 48 health and 20 and 8 at 96, and move with it the way the window does:
# the finisher's share grows with it and the punches' 4 doesn't, while the same regen time heals more HP. At 120
# (2026-09-30) the floors and the start went up 25% with his health.
# Every tier: no tick lands in the 0.6 s after a punch, ticks with nothing between them are one tick apart, and the
# "+N" labels are exactly the HP each tick healed.

const BODY := "Arena/DannyBossScene/DannyBossCharacterBody"
const START_HEALTH := 38
# Where the afk player waits, well clear of his nap's box.
const AWAY := Vector2(960, 900)
const SLOW_START := 2.5
# A tick lands on a physics step, so it can be a step either way of its time.
const STEP := 1.0 / 60.0


static func run(t) -> void:
	var tier: String = t.tier if t.tier in ["afk", "hurry", "slow"] else "afk"
	t.log_p("-- his nap, tier %s" % tier)
	await t.load_fight("danny")
	var boss: Node = t.current_scene.get_node(BODY)
	var sm: Node = boss.state_machine
	t.boss = boss
	t.sm = sm
	var player: Node = t.player
	player.playerHealth = 1000
	var finisher: Node = player.get_node("Finisher")
	t.check(await t.wait_until(func(): return sm.current_state.name == "Idle", 240), "the fight settles into Idle")
	boss.boss_health = START_HEALTH
	boss._refresh_health_bar()
	await t.settle_player(AWAY)
	var sleep: Node = sm.states["Sleep"]
	sm.on_child_transition(sm.current_state, "Sleep")
	var h0: int = boss.boss_health
	await t.wait(2)
	t.check(sm.is_sleeping() and sm.is_open() and boss.hurtbox.monitoring and boss.body_box == &"sleep",
		"a bare transition opens the window: asleep, his hurtbox on, the nap's box")

	var report := {"started": false, "dazed": false, "tiered": true, "done": false}
	var punches: Array[float] = []
	var labels := {}
	var label_order: Array[String] = []
	var last_pause := 0.0
	var left_at := -1.0
	for i in 60 * 12:
		# Read before the break: a tick can land on the very step his nap ends, its label with it.
		for label in boss.regen_labels:
			if is_instance_valid(label) and not labels.has(label.get_instance_id()):
				labels[label.get_instance_id()] = label.text
				label_order.append(label.text)
		if not sm.is_sleeping():
			break
		if not report.started and (tier == "hurry" or (tier == "slow" and sleep.clock >= SLOW_START)):
			report.started = true
			punish(t, finisher, report)
		if sleep.pause_left > last_pause + 0.05:
			punches.append(sleep.clock)
		last_pause = sleep.pause_left
		left_at = sleep.clock
		await t.physics_frame
	var h_end: int = boss.boss_health
	var ticks: Array[float] = sleep.tick_times
	var amounts: Array[int] = sleep.tick_amounts
	var tick: float = sleep.tick_seconds()
	var net: int = h0 - h_end
	t.log_p("left the nap at %.3f s into %s; healed %d in %d ticks %s; punches at %s; labels %s; health %d -> %d, net %d"
		% [left_at, sm.current_state.name, sleep.healed, ticks.size(), ticks, punches, label_order, h0, h_end, net])

	var wanted: Array[String] = []
	var healed_sum := 0
	for amount in amounts:
		wanted.append("+%d" % amount)
		healed_sum += amount
	t.check(label_order == wanted and healed_sum == sleep.healed, "each \"+N\" is the HP its tick healed (%s)" % [label_order])
	var in_pause := []
	for punch in punches:
		for at in ticks:
			if at > punch + STEP and at < punch + sleep.hit_pause - STEP:
				in_pause.append(snappedf(at, 0.001))
	t.check(in_pause.is_empty(), "no tick in the %.1f s after a punch %s" % [sleep.hit_pause, in_pause])
	var spacing := []
	for k in range(1, ticks.size()):
		var punched := false
		for punch in punches:
			if punch > ticks[k - 1] and punch <= ticks[k]:
				punched = true
		if not punched and absf(ticks[k] - ticks[k - 1] - tick) > STEP + 0.001:
			spacing.append(snappedf(ticks[k] - ticks[k - 1], 0.001))
	t.check(spacing.is_empty(), "ticks with nothing between them are one tick (%.4f s) apart %s" % [tick, spacing])
	# A tick lands on the first step its time has run out by, so off a step's multiple it lands up to a step late.
	var first_at: float = sleep.settle + ceilf(tick / STEP - 0.001) * STEP
	var first_ok := ticks.is_empty() or (not punches.is_empty() and punches[0] < ticks[0]) \
		or absf(ticks[0] - first_at) <= STEP + 0.001
	t.check(first_ok, "the first tick comes one tick after the %.1f s settle (%s)" % [sleep.settle, ticks.slice(0, 1)])

	match tier:
		"afk":
			t.check(sleep.healed >= 26 and sleep.healed <= 27, "left alone he heals about 27 HP (%d)" % sleep.healed)
			t.check(absf(left_at - sleep.sleep_time) <= 2.0 * STEP and sm.current_state.name == "Idle",
				"and wakes into Idle at %.1f s (%.3f)" % [sleep.sleep_time, left_at])
		"hurry", "slow":
			t.check(report.dazed, "three punches daze him")
			t.check(not report.tiered, "the finisher is the single-bar one: only the Break pays the tiered mash")
			t.check(await t.wait_until(func(): return report.done, 600), "the mash lands its uppercut")
			var floor_net: int = 25 if tier == "hurry" else 10
			t.check(net >= floor_net, "net %d off him for the window, at least %d" % [net, floor_net])
			t.check(sm.current_state.name == "Idle" and left_at < sleep.sleep_time, "the uppercut ended his nap early, into Idle (%.2f s)" % left_at)


# Up to him, three punches for the daze, then the finisher mashed out. Runs beside the watcher above.
static func punish(t, finisher: Node, report: Dictionary) -> void:
	var boss: Node = t.boss
	t.place_under(boss.get_finisher_hurtbox())
	await t.wait(3)
	for i in 3:
		await t.swing_any()
		if i < 2:
			await t.wait(6)
	report.dazed = await t.wait_until(func(): return finisher.phase == 2 and finisher.prompt_visible, 120)
	report.tiered = finisher.tiered
	if report.dazed:
		await t.mash_finisher()
	report.done = true
