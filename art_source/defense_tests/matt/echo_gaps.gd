extends RefCounted

# matt_echo_gaps (E1, the gap): consecutive first touches on the player are at least the parry window and a step apart,
# so one press never parries two rings, a BOOMBURST is never closer than RED_YELLOW to a red, and two BOOMBURSTs in a
# row are at least AttackCatalog.DASH_IMMUNITY_COOLDOWN apart, so the second dash is immune too. --fixed-fps 60.
#   computed  the worst Doppler squeeze, a player walking straight at him on a diagonal (the walk's two axes at
#             PlayerScript.SPEED each): a beat times v / (v + SPEED * sqrt 2), at least the window and a step
#   walked    a phase-one instance with the player walking at that pace toward him from the rope and back, on each
#             of 8 headings: every ring touches, every two touches in a row at least the window and a step apart, red
#             and yellow at least RED_YELLOW, yellow and yellow at least the dash immunity's cooldown
#   standing  the same on a 3 x 3 grid of standing spots over the player's floor
#   one press a press 0.10 s before a ring's touch parries that ring and only it: the next ring, a beat on, is a hit

const Lib := preload("res://art_source/defense_tests/matt/echo_lib.gd")
const RED_YELLOW := 0.6
# How close to his mouth a walk toward him turns back.
const NEAR := 140.0


static func run(t) -> void:
	await t.load_matt()
	t.hold_break_gauge(t.boss)
	t.track()
	t.track_parries()
	var sm: Node = t.sm
	var walk: float = t.player.SPEED
	var window: float = t.defense.parry_window
	var b: float = sm.echo_beat()
	var v: float = sm.echo_ring_speed
	var worst := b * v / (v + walk * sqrt(2.0))
	t.log_p("computed: a beat of %.4f s at %.0f px/s against a %.1f px/s diagonal walk: %.4f s, the window and a step %.4f s" % [b, v, walk * sqrt(2.0), worst, window + 1.0 / 60.0])
	t.check(worst >= window + 1.0 / 60.0, "the worst squeeze, %.4f s, is at least the window and a step" % worst)

	var floor_rect: Rect2 = t.player.ring_origins
	var mouth: Vector2 = sm.HOME + Vector2(t.boss.mouth_point(&"roar") - t.boss.global_position)
	var runs := []
	for k in 8:
		var heading := Vector2.from_angle(k * TAU / 8.0)
		var dir := Vector2(signf(roundf(heading.x * 10.0)), signf(roundf(heading.y * 10.0)))
		runs.append({"name": "walk %s" % dir, "dir": dir})
	for gx in 3:
		for gy in 3:
			var spot := floor_rect.position + floor_rect.size * Vector2(0.1 + 0.4 * gx, 0.1 + 0.4 * gy)
			runs.append({"name": "stand %s" % spot.round(), "spot": spot.round()})
	var worst_gap := INF
	var worst_ry := INF
	var worst_yy := INF
	var bad := []
	var yellow_yellow: float = load("res://Scripts/AttackCatalog.gd").DASH_IMMUNITY_COOLDOWN
	var rings: int = sm.echo_strings * (6 + sm.echo_boombursts)
	for r in runs:
		var touches := []
		var echo: Node = await Lib.start(t, false)
		Lib.watch_touches(echo, touches)
		var pos: Vector2 = r.get("spot", mouth)
		var going_in := true
		if r.has("dir"):
			pos = _rope_point(mouth, -r.dir, floor_rect)
		t.player.global_position = pos
		for f in 1200:
			if r.has("dir"):
				var step: Vector2 = r.dir * walk / 60.0 * (1.0 if going_in else -1.0)
				pos = (pos + step).clamp(floor_rect.position, floor_rect.end)
				if going_in and pos.distance_to(mouth) <= NEAR:
					going_in = false
				elif not going_in and (pos.x <= floor_rect.position.x or pos.x >= floor_rect.end.x or pos.y <= floor_rect.position.y or pos.y >= floor_rect.end.y):
					going_in = true
			t.player.global_position = pos
			t.player.velocity = Vector2.ZERO
			t.clear_iframes()
			await t.physics_frame
			if t.sm.current_state != echo:
				break
		var gap := INF
		var ry := INF
		var yy := INF
		for i in range(1, touches.size()):
			var d: float = touches[i][2] - touches[i - 1][2]
			gap = minf(gap, d)
			if (touches[i][0] == Lib.BOOMBURST) != (touches[i - 1][0] == Lib.BOOMBURST):
				ry = minf(ry, d)
			elif touches[i][0] == Lib.BOOMBURST:
				yy = minf(yy, d)
		worst_gap = minf(worst_gap, gap)
		worst_ry = minf(worst_ry, ry)
		worst_yy = minf(worst_yy, yy)
		if touches.size() != rings or gap < window + 1.0 / 60.0 - 0.0001 or ry < RED_YELLOW or yy < yellow_yellow:
			bad.append("%s: %d touches, gap %.4f, red-yellow %.4f, yellow-yellow %.4f" % [r.name, touches.size(), gap, ry, yy])
		t.log_p("%s: %d touches, closest two %.4f s apart, red and yellow %.4f s, yellow and yellow %.4f s" % [r.name, touches.size(), gap, ry, yy])
	t.check(bad.is_empty(), "walked on 8 headings and stood on 9 spots: all %d rings touch, two in a row at least %.4f s apart (closest %.4f), red and yellow at least %.1f (closest %.4f), yellow and yellow at least %.1f (closest %.4f) %s" % [
		rings, window + 1.0 / 60.0, worst_gap, RED_YELLOW, worst_ry, yellow_yellow, worst_yy, bad])

	t.log_p("-- one press, one ring")
	var echo: Node = await Lib.start(t, false, Lib.NO_X)
	var touches := []
	Lib.watch_touches(echo, touches)
	await t.settle_player(t.SMOKE_SPOTS["matt"])
	t.parries.clear()
	t.events.clear()
	var pressed := -1
	for f in 900:
		t.player.global_position = t.SMOKE_SPOTS["matt"]
		if pressed < 0 and echo.rings.size() >= 3 and is_instance_valid(echo.rings[2]):
			var ring: Node2D = echo.rings[2]
			var due := Lib.contact_in(t, ring)
			if due >= 0.0 and due <= 0.10:
				t.tap(KEY_SHIFT)
				pressed = touches.size()
		await t.physics_frame
		if pressed >= 0 and touches.size() >= pressed + 2:
			break
	var after: Array = touches.slice(pressed, pressed + 2).map(func(x): return x[1])
	t.log_p("pressed 0.10 s before ring 3: it and the next %s; parries %d" % [after, t.parries.size()])
	t.check(after.size() == 2 and after[0] == Lib.HitInfo.Result.PARRIED and after[1] == Lib.HitInfo.Result.HIT and t.parries.size() == 1,
		"a press 0.10 s before a ring's touch parries it and only it: the next ring, a beat on, is a hit")
	await Lib.reset(t)


# Where the line from `from` going `dir` leaves the floor.
static func _rope_point(from: Vector2, dir: Vector2, floor_rect: Rect2) -> Vector2:
	var p := from
	for i in 4000:
		var n := p + dir
		if not floor_rect.has_point(n):
			break
		p = n
	return p
