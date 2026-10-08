extends RefCounted

# matt_echo_disc (E2, the birth disc, and E3, the reach). --fixed-fps 60, a lone ring of each kind at his roar mouth
# at HOME unless said.
#   disc      a player standing on his mouth, and one hugging him under it, is touched on the ring's birth step:
#             there is no pocket on or under him
#   reach     the player at every corner of their floor (player.ring_origins) and on every rope strip's middle and
#             thirds is touched by every kind of ring before it ends; and a whole phase-one instance, the player in
#             the farthest corner, touches them with every ring it has
#   tunnel    the band can't jump over the hurtbox: at 60 and at 30 steps a second, a ring stepped by hand reaches a
#             player on every spot of a 40 px grid over the floor

const Lib := preload("res://art_source/defense_tests/matt/echo_lib.gd")
const GRID := 40.0


static func run(t) -> void:
	await t.load_matt()
	t.hold_break_gauge(t.boss)
	t.track()
	var sm: Node = t.sm
	var boss: Node = t.boss
	await Lib.reset(t)
	boss.global_position = sm.HOME
	var mouth: Vector2 = boss.mouth_point(&"roar")
	var hurt: Rect2 = t.hurtbox_rect()
	var body_to_hurt: Vector2 = hurt.get_center() - t.player.global_position

	t.log_p("-- the disc")
	var disc_spots := {"on his mouth": mouth - body_to_hurt, "under him": mouth + Vector2(0, 40) - body_to_hurt}
	for name in disc_spots:
		for kind in [Lib.RED, Lib.BOOMBURST]:
			t.player.global_position = disc_spots[name]
			t.clear_iframes()
			var ring := Lib.spawn(t, kind)
			var on_birth: bool = ring.answered
			t.log_p("%s, kind %d: touched on its birth step %s" % [name, kind, on_birth])
			t.check(on_birth, "a player %s is touched on the ring's birth step (kind %d)" % [name, kind])
			await t.wait(50)

	t.log_p("-- the reach")
	var floor_rect: Rect2 = t.player.ring_origins
	var spots: Array = [floor_rect.position, Vector2(floor_rect.end.x, floor_rect.position.y), Vector2(floor_rect.position.x, floor_rect.end.y), floor_rect.end]
	for w in [1.0 / 3.0, 0.5, 2.0 / 3.0]:
		spots.append(Vector2(lerpf(floor_rect.position.x, floor_rect.end.x, w), floor_rect.position.y))
		spots.append(Vector2(lerpf(floor_rect.position.x, floor_rect.end.x, w), floor_rect.end.y))
		spots.append(Vector2(floor_rect.position.x, lerpf(floor_rect.position.y, floor_rect.end.y, w)))
		spots.append(Vector2(floor_rect.end.x, lerpf(floor_rect.position.y, floor_rect.end.y, w)))
	var missed := []
	var farthest := 0.0
	var farthest_spot := Vector2.ZERO
	for spot in spots:
		for kind in [Lib.RED, Lib.ECHO, Lib.GHOST, Lib.PUNISH, Lib.BOOMBURST]:
			t.player.global_position = spot
			t.clear_iframes()
			var ring := Lib.spawn(t, kind)
			var touched: bool = await t.wait_until(func():
				t.player.global_position = spot
				return ring.answered or not ring.is_live(), 60)
			if not ring.answered:
				missed.append("%s kind %d" % [spot, kind])
			await t.wait(8)
		var d := mouth.distance_to(spot)
		if d > farthest:
			farthest = d
			farthest_spot = spot
	t.log_p("%d spots x 5 kinds; missed %s; the farthest %s, %.0f px from his mouth" % [spots.size(), missed, farthest_spot, farthest])
	t.check(missed.is_empty(), "every corner and rope strip of the floor is touched by every kind of ring before it ends")
	var echo: Node = await Lib.start(t, false)
	var touches := []
	Lib.watch_touches(echo, touches)
	for f in 1200:
		t.player.global_position = farthest_spot
		t.clear_iframes()
		await t.physics_frame
		if sm.current_state != echo:
			break
	t.log_p("a phase-one instance at %s: %d of %d rings touched" % [farthest_spot, touches.size(), echo.rings_born])
	var all_rings: int = sm.echo_strings * (6 + sm.echo_boombursts)
	t.check(touches.size() == all_rings and echo.rings_born == all_rings, "a whole phase-one instance touches a player in the farthest corner with all %d rings" % all_rings)
	await Lib.reset(t)

	t.log_p("-- no tunnelling")
	for fps in [60.0, 30.0]:
		var gaps := []
		var y := floor_rect.position.y
		while y <= floor_rect.end.y + 0.1:
			var x := floor_rect.position.x
			while x <= floor_rect.end.x + 0.1:
				t.player.global_position = Vector2(x, y)
				var ring := Lib.spawn(t, Lib.RED)
				ring.set_physics_process(false)
				var hit: bool = ring.answered
				while not hit and ring.radius < ring.end_radius:
					ring.elapsed += 1.0 / fps
					ring.radius = minf(ring.start_radius + ring.speed * ring.elapsed, ring.end_radius)
					ring._check()
					hit = ring.answered
				if not hit:
					gaps.append(Vector2(x, y))
				ring.queue_free()
				t.clear_iframes()
				x += GRID
			y += GRID
		await t.wait(2)
		t.log_p("%.0f steps a second: %d spots never touched %s" % [fps, gaps.size(), gaps.slice(0, 6)])
		t.check(gaps.is_empty(), "at %.0f steps a second the band reaches the player on every spot of a %.0f px grid" % [fps, GRID])
	await Lib.reset(t)
