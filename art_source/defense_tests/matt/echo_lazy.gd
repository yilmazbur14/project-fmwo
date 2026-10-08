extends RefCounted

# matt_echo_lazy (no dead zone, no cheese): the laziest routes through a whole phase-one instance, against standing
# still on the smoke spot, counted in rings that hit. --fixed-fps 60, the gauge held, no parry press unless said.
#   walking and standing  circling him at 300 px, hugging every rope strip and corner of the floor, standing on his
#                         feet, walking a diagonal away and turning at the rope: each takes at least WALK_SHARE of
#                         what standing still takes
#   mash                  a parry press every 0.1 s, standing still: at least MASH_SHARE
#   dash spam             a dash every 0.6 s, standing on the spot: at least DASH_SHARE of the red rings

const Lib := preload("res://art_source/defense_tests/matt/echo_lib.gd")
const WALK_SHARE := 0.9
const MASH_SHARE := 0.8
const DASH_SHARE := 0.95


static func run(t) -> void:
	await t.load_matt()
	t.hold_break_gauge(t.boss)
	t.track()
	var sm: Node = t.sm
	var floor_rect: Rect2 = t.player.ring_origins
	var walk: float = t.player.SPEED
	var still: Vector2 = t.SMOKE_SPOTS["matt"]
	var base: Dictionary = await route(t, "stand still", func(_s): return still, false, false)
	var routes := {
		"circle r300": func(s): return sm.HOME + Vector2.from_angle(s * walk / 300.0) * 300.0,
		"hug the ropes": func(s): return perimeter(floor_rect, s * walk),
		"on his feet": func(_s): return sm.HOME,
		"diagonal away and back": func(s): return diagonal(floor_rect, sm.HOME, s * walk),
	}
	var bad := []
	for name in routes:
		var got: Dictionary = await route(t, name, routes[name], false, false)
		if got.hits < WALK_SHARE * base.hits:
			bad.append("%s %d" % [name, got.hits])
	t.check(bad.is_empty(), "every walking or standing route takes at least %.0f%% of standing still's %d hits (%s)" % [WALK_SHARE * 100.0, base.hits, bad])
	var mashed: Dictionary = await route(t, "mash parry", func(_s): return still, true, false)
	t.check(mashed.hits >= MASH_SHARE * base.hits, "mashing parry takes at least %.0f%% of it (%d of %d)" % [MASH_SHARE * 100.0, mashed.hits, base.hits])
	var dashed: Dictionary = await route(t, "dash every 0.6 s", func(_s): return still, false, true)
	t.check(dashed.reds >= DASH_SHARE * 18.0, "dashing every 0.6 s takes at least %.0f%% of the red rings (%d of 18)" % [DASH_SHARE * 100.0, dashed.reds])


# One phase-one instance with the player at `where(seconds)` every step; the rings that hit, all and red.
static func route(t, name: String, where: Callable, mash: bool, dash: bool) -> Dictionary:
	var echo: Node = await Lib.start(t, false, Lib.NO_X)
	var touches := []
	Lib.watch_touches(echo, touches)
	var f := 0
	while f < 1400:
		var s := f / 60.0
		if not dash:
			t.player.global_position = (where.call(s) as Vector2).clamp(t.player.ring_origins.position, t.player.ring_origins.end)
		elif not t.player.is_dodging:
			t.player.global_position = where.call(s)
		t.player.velocity = Vector2.ZERO
		t.clear_iframes()
		if mash and f % 6 == 0:
			t.tap(KEY_SHIFT)
		if dash and f % 36 == 0:
			t.tap(KEY_W)
		await t.physics_frame
		f += 1
		if t.sm.current_state != echo:
			break
	var hits := touches.filter(func(x): return x[1] == Lib.HitInfo.Result.HIT)
	var reds: int = hits.filter(func(x): return x[0] != Lib.BOOMBURST).size()
	t.log_p("%s: %d of %d rings hit, %d of them red" % [name, hits.size(), touches.size(), reds])
	await Lib.reset(t)
	return {"hits": hits.size(), "reds": reds}


# `d` px round the floor's edge from its top-left corner, clockwise.
static func perimeter(r: Rect2, d: float) -> Vector2:
	var around := 2.0 * (r.size.x + r.size.y)
	d = fposmod(d, around)
	if d < r.size.x:
		return r.position + Vector2(d, 0)
	d -= r.size.x
	if d < r.size.y:
		return Vector2(r.end.x, r.position.y + d)
	d -= r.size.y
	if d < r.size.x:
		return Vector2(r.end.x - d, r.end.y)
	d -= r.size.x
	return Vector2(r.position.x, r.end.y - d)


# Out from `from` on the down-right diagonal to the floor's edge and back, `d` px along the way.
static func diagonal(r: Rect2, from: Vector2, d: float) -> Vector2:
	var dir := Vector2(1, 1).normalized()
	var reach := 0.0
	while r.has_point(from + dir * (reach + 1.0)):
		reach += 1.0
	var leg := fposmod(d, 2.0 * reach)
	return from + dir * (leg if leg <= reach else 2.0 * reach - leg)
