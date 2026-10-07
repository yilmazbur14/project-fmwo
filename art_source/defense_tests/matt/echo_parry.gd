extends RefCounted

# matt_echo_parry (E4, one answer a ring): --fixed-fps 60, the gauge held unless said.
#   perfect   a press 0.12 s before every red ring's touch, at 5 spots over a whole phase-one instance: no red ring
#             hits, and each parried ring flies on, whole, past the player
#   late      a press the step after a ring has hit (it lands two steps after, inside echo_rearm_delay) is a late
#             press for that ring: the next ring, a beat on, is still parried by a press on time (the re-arm)
#   mash      a press every 0.1 s through a whole instance, standing still, is hit by at least MASH_HIT of the red rings
#   reads     with the gauge open, each parried ring pays one read; a ghost's touch pays nothing, and a punish's hit
#             costs the gauge's hit_loss

const Lib := preload("res://art_source/defense_tests/matt/echo_lib.gd")
const MASH_HIT := 0.8
const SPOTS := [Vector2(960, 760), Vector2(400, 300), Vector2(1500, 860), Vector2(1600, 300), Vector2(500, 880)]


static func run(t) -> void:
	await t.load_matt()
	t.hold_break_gauge(t.boss)
	t.track()
	t.track_parries()
	await perfect(t)
	await late(t)
	await mash(t)
	await reads(t)


# Presses each red ring of `echo` `lead` s before its touch, once.
static func presser(t, echo: Node, lead: float, pressed: Dictionary) -> Callable:
	return func():
		for ring in echo.rings:
			if not is_instance_valid(ring) or ring.answered or pressed.has(ring.get_instance_id()):
				continue
			if ring.kind != Lib.RED and ring.kind != Lib.ECHO:
				continue
			var due: float = Lib.contact_in(t, ring)
			if due >= 0.0 and due <= lead:
				pressed[ring.get_instance_id()] = true
				t.tap(KEY_SHIFT)


static func perfect(t) -> void:
	var bad := []
	var flew_on := true
	for spot in SPOTS:
		var echo: Node = await Lib.start(t, false, Lib.NO_X)
		var touches := []
		Lib.watch_touches(echo, touches)
		var press := presser(t, echo, 0.12, {})
		t.events.clear()
		for f in 1200:
			t.player.global_position = spot
			t.clear_iframes()
			press.call()
			await t.physics_frame
			for x in touches:
				if x[1] == Lib.HitInfo.Result.PARRIED and is_instance_valid(x[3]) and x[3].is_live() and x[3].radius <= x[3].start_radius:
					flew_on = false
			if t.sm.current_state != echo:
				break
		var reds_hit := touches.filter(func(x): return x[0] != Lib.BOOMBURST and x[1] != Lib.HitInfo.Result.PARRIED).size()
		var parried := touches.filter(func(x): return x[1] == Lib.HitInfo.Result.PARRIED).size()
		t.log_p("perfect at %s: %d of 18 red rings parried, %d hit" % [spot, parried, reds_hit])
		if reds_hit > 0 or parried != 18:
			bad.append(spot)
	t.check(bad.is_empty() and flew_on, "a press 0.12 s before every red ring's touch, at 5 spots: none hits, and each flies on past the player (%s)" % [bad])


static func late(t) -> void:
	var echo: Node = await Lib.start(t, false, Lib.NO_X)
	var touches := []
	Lib.watch_touches(echo, touches)
	var spot := Vector2(960, 760)
	var press_next := false
	var pressed := {}
	for f in 900:
		t.player.global_position = spot
		t.clear_iframes()
		# Ring 3 hits; the step after, the late press.
		if not press_next and touches.size() >= 3:
			t.tap(KEY_SHIFT)
			press_next = true
		if press_next and echo.rings.size() >= 4 and is_instance_valid(echo.rings[3]) and not pressed.has(3):
			var due: float = Lib.contact_in(t, echo.rings[3])
			if due >= 0.0 and due <= 0.12:
				pressed[3] = true
				t.tap(KEY_SHIFT)
		await t.physics_frame
		if touches.size() >= 4:
			break
	var results := touches.slice(2, 4).map(func(x): return x[1])
	t.log_p("ring 3 then a press the step after it hit; ring 4 pressed on time: %s" % [results])
	t.check(results.size() == 2 and results[0] == Lib.HitInfo.Result.HIT and results[1] == Lib.HitInfo.Result.PARRIED,
		"a late press, inside echo_rearm_delay, never locks out the next ring: a press on time parries it")
	await Lib.reset(t)


static func mash(t) -> void:
	var echo: Node = await Lib.start(t, false, Lib.NO_X)
	var touches := []
	Lib.watch_touches(echo, touches)
	var spot := Vector2(960, 760)
	var f := 0
	while f < 1200:
		t.player.global_position = spot
		t.clear_iframes()
		t.defense._set_stamina(t.defense.max_stamina)
		if f % 6 == 0:
			t.tap(KEY_SHIFT)
		await t.physics_frame
		f += 1
		if t.sm.current_state != echo:
			break
	var reds := touches.filter(func(x): return x[0] != Lib.BOOMBURST)
	var hit := reds.filter(func(x): return x[1] == Lib.HitInfo.Result.HIT).size()
	var share := float(hit) / maxf(reds.size(), 1.0)
	t.log_p("mashing every 0.1 s: %d of %d red rings hit (%.0f%%)" % [hit, reds.size(), share * 100.0])
	t.check(reds.size() == 18 and share >= MASH_HIT, "mashing every 0.1 s is hit by at least %.0f%% of the red rings (%.0f%%)" % [MASH_HIT * 100.0, share * 100.0])
	await Lib.reset(t)


static func reads(t) -> void:
	var gauge: Node = t.boss.break_gauge
	gauge.locked = false
	gauge.value = 0.0
	var echo: Node = await Lib.start(t, true, [1, -1, -1, -1])
	var touches := []
	Lib.watch_touches(echo, touches)
	var spot := Vector2(960, 760)
	var pressed := {}
	var press := presser(t, echo, 0.12, pressed)
	var after := []
	var bite_done := false
	for f in 600:
		t.player.global_position = spot
		t.clear_iframes()
		# Rings 1 and 2 parried; then the X's ghost left alone; its echo parried. Stop before the second X.
		if touches.size() < 2 or (touches.size() == 3):
			press.call()
		var count := touches.size()
		await t.physics_frame
		if touches.size() > count:
			after.append([touches.back()[0], touches.back()[1], gauge.value])
		if touches.size() >= 4:
			break
	var read: float = gauge.parry_gain
	t.log_p("gauge after each touch [kind, result, value]: %s; a read is %.3f" % [after, read])
	var values: Array = after.map(func(x): return x[2])
	t.check(after.size() == 4 and is_equal_approx(values[0], read) and is_equal_approx(values[1], 2.0 * read)
		and is_equal_approx(values[2], 2.0 * read) and after[2][0] == Lib.GHOST,
		"each parried ring pays one read and a ghost's touch pays nothing (%s)" % [values])
	# A bitten X: its echo's hit costs hit_loss.
	gauge.value = 3.0 * read
	echo = await Lib.start(t, true, [1, -1, -1, -1])
	touches.clear()
	Lib.watch_touches(echo, touches)
	var bit := false
	var before_punish := -1.0
	var punish_value := -1.0
	pressed.clear()
	press = presser(t, echo, 0.12, pressed)
	for f in 600:
		t.player.global_position = spot
		t.clear_iframes()
		if not bit and echo.xs.size() > 0 and echo.xs[0].prev_touch > 0.0 and t.defense.clock >= echo.xs[0].prev_touch + 0.2:
			t.tap(KEY_SHIFT)
			bit = true
		elif not bit:
			press.call()
		var value: float = gauge.value
		await t.physics_frame
		for x in touches:
			if x[0] == Lib.PUNISH and punish_value < 0.0:
				before_punish = value
				punish_value = gauge.value
		if punish_value >= 0.0:
			break
	t.log_p("a bitten X: bites %d, the gauge %.3f -> %.3f over its punish (hit_loss %.3f)" % [echo.bites, before_punish, punish_value, gauge.hit_loss])
	t.check(echo.bites == 1 and before_punish > 0.0 and is_equal_approx(punish_value, before_punish - gauge.hit_loss),
		"a punish pays nothing: its hit costs the gauge's hit_loss")
	gauge.locked = true
	gauge.value = 0.0
	await Lib.reset(t)
