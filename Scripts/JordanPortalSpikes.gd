extends RefCounted

# The placements of Jordan's attack 3 (JordanComboPortals), as pure functions off the attack's own rng so a test can
# sample them: the spike director's waves and its fairness rules (the build plan's a-e), where a hop and a feint's exit
# bring Eric up, whether a rush feints, and how far a blade may come up under the keep-clears. Every point is a world px
# on the floor: a spike's is its opening's centre, the player's their soles, Eric's his.
#
# THE RULES, as JordanPortalsLayout names them:
#   a  an aimed spike (on the soles) only while AIM_FREE_WAYS of the eight ways out of it stay off every other spike's
#      ellipse, and on the floor, for AIM_ESCAPE; otherwise it goes in as a flank
#   b  only an aimed spike is ever under the player: flanks FLANK_MIN off the soles, portals PORTAL_SPACING apart
#   c  no aimed live window inside AIM_CLEAR of a grab's contact (the attack says so: aim_ok)
#   d  nothing aimed while the player is held, and nothing new within HELD_CLEAR of them (the attack also calls off
#      any spike still in its tell there as the catch lands)
#   e  nothing opens once the phase is over (the attack stops asking)

const Layout := preload("res://Scripts/JordanPortalsLayout.gd")
const GodLayout := preload("res://Scripts/JordanGodLayout.gd")

const DIAGONAL := 0.70710678
const WAYS: Array[Vector2] = [Vector2(1, 0), Vector2(DIAGONAL, DIAGONAL), Vector2(0, 1), Vector2(-DIAGONAL, DIAGONAL),
	Vector2(-1, 0), Vector2(-DIAGONAL, -DIAGONAL), Vector2(0, -1), Vector2(DIAGONAL, -DIAGONAL)]

static var keep_out_rects: Array[Rect2] = []


# Whether the soles box at `soles` is on the opening's ellipse centred on `at`.
static func covers(at: Vector2, soles: Vector2, radii := Layout.SPIKE_OPENING) -> bool:
	var box := Rect2(soles + Layout.SOLES_BOX.position, Layout.SOLES_BOX.size)
	var near := at.clamp(box.position, box.end)
	return ((near - at) / radii).length_squared() <= 1.0


static func keep_clear(rect: Rect2) -> bool:
	if keep_out_rects.is_empty():
		keep_out_rects = Layout.keep_outs()
	for block in keep_out_rects:
		if block.intersects(rect):
			return false
	return true


# The spike portal's drawn frame on `at`: its telegraph.
static func telegraph_rect(at: Vector2) -> Rect2:
	var spec: Dictionary = Layout.PORTALS[&"spike"]
	return Rect2(at - spec.anchor * Layout.SCALE, spec.frame * Layout.SCALE)


static func on_floor(at: Vector2, radii: Vector2) -> bool:
	return GodLayout.FLOOR.encloses(Rect2(at - radii, radii * 2.0))


# Where an aimed spike opens for `soles`: on them, moved in off the floor's edge as far as its opening needs. The soles
# can stand closer to a wall than an opening's radius, and with the spike kept on them exactly, a player standing against
# any wall never had one (playtest 2026-10-04): it still covers them from there.
static func aim_point(soles: Vector2) -> Vector2:
	var radii: Vector2 = Layout.SPIKE_OPENING
	return soles.clamp(GodLayout.FLOOR.position + radii, GodLayout.FLOOR.end - radii).round()


# Where a spike may open: its opening on the floor, its telegraph clear of the keep-clears, PORTAL_SPACING off every
# portal in `taken`, HELD_CLEAR off a held player's soles (`held`, or INF), and HOP_SPIKE_CLEAR off every exit Eric is
# about to come out of (`exits`).
static func placeable(at: Vector2, taken: Array, held: Vector2, exits: Array = []) -> bool:
	if not on_floor(at, Layout.SPIKE_OPENING) or not keep_clear(telegraph_rect(at)):
		return false
	for other: Vector2 in taken:
		if at.distance_to(other) < Layout.PORTAL_SPACING:
			return false
	for exit: Vector2 in exits:
		if at.distance_to(exit) < Layout.HOP_SPIKE_CLEAR:
			return false
	return not held.is_finite() or at.distance_to(held) >= Layout.HELD_CLEAR


# How many of the eight ways out of `soles` stay off every ellipse in `spikes`, with the player's origin on the floor
# (`origins`), for AIM_ESCAPE.
static func free_ways(soles: Vector2, spikes: Array, origins: Rect2) -> int:
	var ways_out := 0
	var steps := ceili(Layout.AIM_ESCAPE / Layout.ESCAPE_STEP)
	# The attack walls these off (JordanComboPortals), so a way into one is no way out.
	var walled := Layout.no_stand_zones()
	for way in WAYS:
		var clear := true
		for k in range(1, steps + 1):
			var at := soles + way * minf(k * Layout.ESCAPE_STEP, Layout.AIM_ESCAPE)
			if origins.has_area() and not origins.grow(0.5).has_point(at - Vector2(0, Layout.SOLES_OVER_ORIGIN)):
				clear = false
			if walled.any(func(zone: Rect2) -> bool: return zone.has_point(at)):
				clear = false
			for other: Vector2 in spikes:
				if covers(other, at):
					clear = false
			if not clear:
				break
		if clear:
			ways_out += 1
	return ways_out


# One wave's spikes, [{at, aimed}], for the player's soles now. `spikes` are the spike portals up and `fixed` the other
# portals a spike keeps its spacing from (the sword's); `room` how many more may open; `aim_ok` whether a grab's contact
# lets an aimed one's live window in (c); `held` a held player's soles, or INF; `exits` the exits showing. The pincer: a
# flank either side,
# PINCER_RANGE off. Aimed: a flank a random side FLANK_RANGE off, and one on the soles, or a second flank the other side
# where a to d won't have it there. Flanks within FLANK_TILT of level. Empty when nothing fits.
static func wave(rng: RandomNumberGenerator, pattern: StringName, soles: Vector2, spikes: Array, fixed: Array, room: int,
		aim_ok: bool, held: Vector2, origins: Rect2, exits: Array = []) -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	if room <= 0:
		return out
	var taken: Array = spikes + fixed
	var hurting: Array = spikes.duplicate()
	var reach: Vector2 = Layout.PINCER_RANGE if pattern == &"pincer" else Layout.FLANK_RANGE
	var side := 1.0 if rng.randf() < 0.5 else -1.0
	var flank := _flank(rng, soles, side, reach, taken, held, exits)
	if flank.is_finite():
		out.append({at = flank, aimed = false})
		taken.append(flank)
		hurting.append(flank)
	if out.size() >= room:
		return out
	var on_soles := aim_point(soles)
	if pattern == &"aimed" and aim_ok and not held.is_finite() and covers(on_soles, soles) \
			and placeable(on_soles, taken, held, exits) and free_ways(soles.round(), hurting, origins) >= Layout.AIM_FREE_WAYS:
		out.append({at = on_soles, aimed = true})
		return out
	var other := _flank(rng, soles, -side, reach, taken, held, exits)
	if other.is_finite():
		out.append({at = other, aimed = false})
	return out


static func _flank(rng: RandomNumberGenerator, soles: Vector2, side: float, reach: Vector2, taken: Array, held: Vector2,
		exits: Array) -> Vector2:
	for attempt in Layout.PLACE_TRIES:
		var tilt := deg_to_rad(rng.randf_range(-Layout.FLANK_TILT, Layout.FLANK_TILT))
		var at := (soles + Vector2(cos(tilt) * side, sin(tilt)) * rng.randf_range(reach.x, reach.y)).round()
		if at.distance_to(soles) >= Layout.FLANK_MIN and placeable(at, taken, held, exits):
			return at
	return Vector2.INF


# Where a hop brings Eric up: HOP_RANGE off the player's soles, in HOP_BAND, HOP_CLEAR off Josh and the sword portal,
# HOP_SPIKE_CLEAR off every spike up, and him and his badge clear of the keep-clears. With nowhere that keeps them all,
# the spot that breaks them least.
static func hop_spot(rng: RandomNumberGenerator, soles: Vector2, spikes: Array) -> Vector2:
	var best := Vector2.INF
	var best_miss := INF
	for attempt in Layout.HOP_TRIES:
		var at: Vector2
		if attempt % 2 == 0:
			at = soles + Vector2.from_angle(rng.randf() * TAU) * rng.randf_range(Layout.HOP_RANGE.x, Layout.HOP_RANGE.y)
		else:
			at = Layout.HOP_BAND.position + Vector2(rng.randf(), rng.randf()) * Layout.HOP_BAND.size
		at = at.round()
		var miss := hop_miss(at, soles, spikes)
		if miss <= 0.0:
			return at
		if miss < best_miss:
			best = at
			best_miss = miss
	return best


# How far `at` is from keeping every hop rule, px; 0 when it keeps them all.
static func hop_miss(at: Vector2, soles: Vector2, spikes: Array) -> float:
	var band: Rect2 = Layout.HOP_BAND
	var miss := maxf(band.position.x - at.x, 0.0) + maxf(at.x - band.end.x, 0.0) + maxf(band.position.y - at.y, 0.0) \
		+ maxf(at.y - band.end.y, 0.0)
	var away := at.distance_to(soles)
	miss += maxf(Layout.HOP_RANGE.x - away, 0.0) + maxf(away - Layout.HOP_RANGE.y, 0.0)
	for fixed: Vector2 in [Layout.JOSH_FEET, Layout.SWORD_PORTAL]:
		miss += maxf(Layout.HOP_CLEAR - at.distance_to(fixed), 0.0)
	for spike: Vector2 in spikes:
		miss += maxf(Layout.HOP_SPIKE_CLEAR - at.distance_to(spike), 0.0)
	for rect in Layout.eric_rects(at):
		if not keep_clear(rect):
			miss += Layout.HOP_CLEAR
	return miss


# Where a feint brings him out: EXIT_RANGE off the player's soles on a new side, EXIT_TURN or more off the way he came
# at them from `eric`, in HOP_BAND, him and his badge clear of the keep-clears. INF when there is nowhere, and then there
# is no feint. Spikes don't keep an exit off: they never touch him, and flanks sit round the player at the exit's range.
static func feint_exit(rng: RandomNumberGenerator, soles: Vector2, eric: Vector2) -> Vector2:
	for attempt in Layout.HOP_TRIES:
		var at := (soles + Vector2.from_angle(rng.randf() * TAU) * rng.randf_range(Layout.EXIT_RANGE.x, Layout.EXIT_RANGE.y)).round()
		if exit_ok(at, soles, eric):
			return at
	return Vector2.INF


static func exit_ok(at: Vector2, soles: Vector2, eric: Vector2) -> bool:
	var band: Rect2 = Layout.HOP_BAND
	if at.x < band.position.x or at.x > band.end.x or at.y < band.position.y or at.y > band.end.y:
		return false
	var away := at.distance_to(soles)
	if away < Layout.EXIT_RANGE.x or away > Layout.EXIT_RANGE.y:
		return false
	var approach := eric - soles
	if approach.length() > 0.001 and absf(rad_to_deg((at - soles).angle_to(approach))) < Layout.EXIT_TURN:
		return false
	for rect in Layout.eric_rects(at):
		if not keep_clear(rect):
			return false
	return true


# Whether the player's soles start the attack clear of every zone (JordanPortalsLayout.start_zones).
static func start_clear(soles: Vector2) -> bool:
	for zone in Layout.start_zones():
		if zone.has_point(soles):
			return false
	return true


# Where the player starts the attack: where they stand, when that is clear; otherwise the nearest clear spot level with
# them or in front of them (never up behind the puppets) with their origin on the floor (`origins`,
# PlayerScript.ring_origins), or START_FALLBACK with none.
static func start_spot(soles: Vector2, origins: Rect2) -> Vector2:
	if start_clear(soles):
		return soles
	for ring in range(1, Layout.START_RINGS + 1):
		for k in Layout.START_ANGLES + 1:
			var at := (soles + Vector2.from_angle(PI * k / Layout.START_ANGLES) * ring * Layout.START_STEP).round()
			var origin := at - Vector2(0, Layout.SOLES_OVER_ORIGIN)
			if start_clear(at) and (not origins.has_area() or origins.grow(0.5).has_point(origin)):
				return at
	return Layout.START_FALLBACK


# Whether rush `index` of the phase feints: FEINT_CHANCE, never the first, never twice running, FEINTS_MAX at most.
static func feint_roll(rng: RandomNumberGenerator, index: int, last_feinted: bool, feints: int) -> bool:
	if index == 0 or last_feinted or feints >= Layout.FEINTS_MAX:
		return false
	return rng.randf() < Layout.FEINT_CHANCE


# How many rows up from `at` a strip `left` texels to its left and `width` wide may come before it reaches a keep-clear,
# `most` at most.
static func clear_rows(at: Vector2, left: float, width: float, most: int) -> int:
	for rows in range(most, 0, -1):
		var strip := Rect2(at.x - left * Layout.SCALE, at.y - rows * Layout.SCALE, width * Layout.SCALE, rows * Layout.SCALE)
		if keep_clear(strip):
			return rows
	return 0


# The blade (the drawn one's 33 texels, the wider of the two) and the smear.
static func blade_rows(at: Vector2) -> int:
	return clear_rows(at, Layout.SPIKE_BLADE_POINT_X, 33.0, Layout.BLADE_ROWS)


static func smear_rows(at: Vector2) -> int:
	return clear_rows(at, Layout.SMEAR.anchor.x, Layout.SMEAR.size.x, int(Layout.SMEAR.anchor.y))
