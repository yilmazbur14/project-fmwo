extends RefCounted

# matt_echo_stamina (E5, the stamina floor): the worst string a player can play - every red ring missed with a press
# the step after it hits, the X bitten, and each of its BOOMBURSTs dashed - starting from the floor itself: no parry
# press and no dash is ever refused, and the bar never ends a step under echo_stamina_floor. Then, the instance over,
# the floor is off. --fixed-fps 60, the gauge held.

const Lib := preload("res://art_source/defense_tests/matt/echo_lib.gd")


static func run(t) -> void:
	await t.load_matt()
	t.hold_break_gauge(t.boss)
	t.track()
	var sm: Node = t.sm
	var echo: Node = await Lib.start(t, true, [1, -1, -1, -1])
	var touches := []
	Lib.watch_touches(echo, touches)
	var refused := [0]
	t.defense.stamina_refused.connect(func(): refused[0] += 1)
	var spot: Vector2 = t.SMOKE_SPOTS["matt"]
	var low := INF
	var presses := 0
	var dashed := {}
	var bit := false
	var seen := 0
	await t.wait_until(func(): return echo.beat == echo.Beat.STRINGS, 60)
	t.defense._set_stamina(sm.echo_stamina_floor)
	for f in 900:
		t.player.global_position = spot
		t.clear_iframes()
		# The step after each red or echo hits, a press.
		if touches.size() > seen:
			for x in touches.slice(seen):
				if x[0] == Lib.RED or x[0] == Lib.ECHO or x[0] == Lib.PUNISH:
					t.tap(KEY_SHIFT)
					presses += 1
			seen = touches.size()
		if not bit and echo.xs.size() > 0 and echo.xs[0].ring != null and is_instance_valid(echo.xs[0].ring):
			var due: float = Lib.contact_in(t, echo.xs[0].ring)
			if due >= 0.0 and due <= 0.12:
				bit = true
				t.tap(KEY_SHIFT)
				presses += 1
		for ring in echo.rings:
			if is_instance_valid(ring) and ring.kind == Lib.BOOMBURST and not ring.answered and not dashed.has(ring.get_instance_id()) \
					and Lib.contact_in(t, ring) <= 0.06:
				dashed[ring.get_instance_id()] = true
				t.tap(KEY_W)
		await t.physics_frame
		if echo.beat == echo.Beat.STRINGS:
			low = minf(low, t.defense.stamina)
		if touches.filter(func(x): return x[0] == Lib.BOOMBURST).size() >= sm.echo_boombursts:
			break
	var boom: Array = touches.filter(func(x): return x[0] == Lib.BOOMBURST)
	t.log_p("the worst string: %d presses, %d dashes, bites %d, the BOOMBURSTs %s; refused %d; the bar's lowest %.2f" % [
		presses, dashed.size(), echo.bites, boom.map(func(x): return x[1]), refused[0], low])
	t.check(presses >= 6 and dashed.size() == sm.echo_boombursts and echo.bites == 1 and refused[0] == 0, "no parry press and no dash refused through the worst string")
	t.check(low >= sm.echo_stamina_floor - 0.001, "the bar never ends a step under the floor, %.0f (lowest %.2f)" % [sm.echo_stamina_floor, low])
	t.check(boom.size() == sm.echo_boombursts and boom.all(func(x): return x[1] == Lib.HitInfo.Result.DODGED),
		"and each dash went through its BOOMBURST (%d)" % sm.echo_boombursts)
	await t.wait_until(func(): return sm.current_state != echo, 1200)
	t.defense._set_stamina(5.0)
	await t.wait(3)
	t.log_p("after the instance: %s, stamina %.1f" % [sm.current_state.name, t.defense.stamina])
	t.check(t.defense.stamina < sm.echo_stamina_floor, "the floor is off once the instance is over")
	await Lib.reset(t)
