extends RefCounted

# matt_echo_rotation (his attacks' order, 2026-10-05): the rotation is Ezreal set, Glass Row, and the Echo Roars come
# chained after the Ezreal set (MattStateMachine.echo_after_ezreal), the two sharing the window after them. --fixed-fps
# 60, the gauge held unless said, his live rotation and phase rule put back over the parked ones.
#   order       each cycle planned by his own start_cycle() and cut short as it begins: Ezreal set, Glass Row, and
#               round again, never a yell in the rows above half his health
#   chain       a real Ezreal set run out: Spent hands over to the Echo Roars, not the window, planned as it hands
#               over - phase one's strings above half his health, phase two's at or under it, an X a string in both
#               only in a phase whose feint knob is on, so none live since 2026-10-06 - and the Echo Roars end in his
#               window
#   phase two   a Break under half his health: the forced Deafening Glass Row next, then the Ezreal set, then the
#               Deafening Glass Row; but straight after a plain Glass Row the opener waits a cycle
#   no repeats  over 9 cycles on 3 seeds, a Break forced on a different cycle each, never two Glass Rows in a row

const ROTATION: Array[String] = ["MysticVolley", "GlassRow"]


static func run(t) -> void:
	await t.load_matt()
	t.hold_break_gauge(t.boss)
	var live: Node = load("res://Scripts/States/Matt/MattStateMachine.gd").new()
	var live_rotation: Array = live.attack_rotation.duplicate()
	var live_chain: bool = live.echo_after_ezreal
	live.free()
	t.log_p("-- the order: the live rotation %s, the Echo Roars chained after the Ezreal set %s" % [live_rotation, live_chain])
	t.check(live_rotation == ["MysticVolley", "GlassRow"] and live_chain, "his rotation is the Ezreal set and the Glass Row, the Echo Roars chained after the set")
	await setup(t)
	var seen := []
	for k in 4:
		seen.append(await cycle(t, false))
	t.log_p("%s" % [seen])
	t.check(seen.map(func(c): return c.attack) == ["MysticVolley", "GlassRow", "MysticVolley", "GlassRow"] and seen.all(func(c): return not c.deafen),
		"phase one: Ezreal set, Glass Row, and round again, no yell in the rows")

	t.log_p("-- the chain")
	for low in [false, true]:
		await t.load_matt()
		t.hold_break_gauge(t.boss)
		await setup(t)
		t.player.playerHealth = 100000
		if low:
			t.boss.boss_health = int(t.boss.max_health * t.sm.phase_two_ratio) - 2
		var watch := {"echo_after_spent": false, "recover_after_echo": false, "strings": -1, "feints": []}
		var last := ""
		t.sm.start_cycle()
		for f in 3600:
			t.clear_iframes()
			var now: String = t.sm.current_state.name
			if now != last:
				if last == "Spent" and now == "EchoRoars":
					watch.echo_after_spent = true
					watch.strings = t.sm.cycle_echo_strings
					watch.feints = t.sm.cycle_echo_feints.duplicate()
				if last == "EchoRoars" and now == "Recover":
					watch.recover_after_echo = true
				last = now
			if watch.recover_after_echo:
				break
			await t.physics_frame
		t.log_p("%s: %s" % ["under half his health" if low else "full health", watch])
		var want_strings: int = t.sm.echo_strings_phase_two if low else t.sm.echo_strings
		var xs_on: bool = t.sm.echo_feints_phase_two if low else t.sm.echo_feints_phase_one
		var feints_ok: bool = watch.feints.all(func(x): return x in [0, 1, 2]) if xs_on else watch.feints.all(func(x): return x == -1)
		t.check(watch.echo_after_spent and watch.recover_after_echo and watch.strings == want_strings and feints_ok,
			"%s: Spent hands over to the Echo Roars (%d strings, %s), and they end in his window" % [
			"under half" if low else "above half", want_strings, "an X a string" if xs_on else "no X"])

	t.log_p("-- phase two")
	await t.load_matt()
	t.hold_break_gauge(t.boss)
	await setup(t)
	seen.clear()
	seen.append(await cycle(t, false))
	seen.append(await cycle(t, false))
	seen.append(await cycle(t, true))
	for k in 3:
		seen.append(await cycle(t, false))
	t.log_p("%s" % [seen])
	var attacks: Array = seen.map(func(c): return c.attack)
	t.check(attacks == ["MysticVolley", "GlassRow", "MysticVolley", "GlassRow", "MysticVolley", "GlassRow"] and seen[3].deafen and seen[5].deafen,
		"a Break under half his health in the Ezreal cycle: the Deafening Glass Row next, then the set, then the Deafening row (%s)" % [attacks])
	await t.load_matt()
	t.hold_break_gauge(t.boss)
	await setup(t)
	seen.clear()
	seen.append(await cycle(t, false))
	seen.append(await cycle(t, true))
	for k in 2:
		seen.append(await cycle(t, false))
	attacks = seen.map(func(c): return c.attack)
	t.log_p("a Break in the plain row's cycle: %s" % [seen])
	t.check(attacks == ["MysticVolley", "GlassRow", "MysticVolley", "GlassRow"] and not seen[1].deafen and seen[3].deafen,
		"straight after a plain Glass Row the opener waits a cycle: the set, then the Deafening row (%s)" % [attacks])

	t.log_p("-- never two Glass Rows in a row")
	var bad := []
	for seed in [11, 22, 33]:
		await t.load_matt()
		t.hold_break_gauge(t.boss)
		t.sm.rng.seed = seed
		await setup(t)
		var break_on: int = {11: 1, 22: 2, 33: 4}[seed]
		var order := []
		for k in 9:
			order.append((await cycle(t, k == break_on)).attack)
		for i in range(1, order.size()):
			if order[i] == "GlassRow" and order[i - 1] == "GlassRow":
				bad.append([seed, order])
				break
		t.log_p("seed %d, a Break on cycle %d: %s" % [seed, break_on + 1, order])
	t.check(bad.is_empty(), "never two Glass Rows in a row over 9 cycles on 3 seeds (%s)" % [bad])


static func setup(t) -> void:
	var sm: Node = t.sm
	sm.attack_rotation = ROTATION.duplicate()
	sm.phase_two_ratio = 0.5
	sm.phase_two_at_break = false
	sm.echo_after_ezreal = true
	sm.on_child_transition(sm.current_state, "Idle")
	sm.beat_timer.stop()
	await t.wait(2)


# One cycle from his start_cycle(), cut short as it begins - by a Break that leaves him under half his health if
# `breaks` - then back to Idle.
static func cycle(t, breaks: bool) -> Dictionary:
	var sm: Node = t.sm
	sm.start_cycle()
	var got := {"attack": sm.last_attack, "deafen": sm.cycle_deafen, "two": sm.in_phase_two()}
	await t.wait(3)
	if breaks:
		t.boss.boss_health = int(t.boss.max_health * sm.phase_two_ratio) - 2
		var gauge: Node = t.boss.break_gauge
		gauge.locked = false
		gauge.add(gauge.max_value)
		await t.wait_until(func(): return sm.current_state.name == "Broken", 30)
		gauge.locked = true
	for hazard in t.get_nodes_in_group(sm.HAZARD_GROUP):
		hazard.queue_free()
	t.player.unlock_actions()
	sm.on_child_transition(sm.current_state, "Idle")
	sm.beat_timer.stop()
	await t.wait(3)
	return got
