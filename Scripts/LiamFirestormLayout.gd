extends RefCounted

# Liam's attack 3, the firestorm (LiamFirestorm, addendum 3 B, addendum 5): the track its fire tornados roam, where each
# starts on it, the pull they have on the player, the zones their fire rings cover, and the offline check that the front
# spot stays clear of all of it while the rest of the ring gets swept (validate). World px. How many there are is the
# state machine's tornado_count (the user's question 4).

const CombinedLayout := preload("res://Scripts/BixbyCombinedArtLayout.gd")

# The one closed track they all share, clockwise: every edge and corner of the ring, dipping into a notch under him so
# no ring on it ever reaches the front spot.
const TRACK := [Vector2(250, 480), Vector2(540, 480), Vector2(700, 640), Vector2(1220, 640), Vector2(1380, 480),
	Vector2(1670, 480), Vector2(1670, 880), Vector2(250, 880)]
# Where each starts roaming once the wall has broken up, px along the track by count, in WALL_X's order: evenly spread,
# clear of the reset spot and of each other. 4's is (254,880), (724,640), (1197,880), (1600,480): one tornado entering the
# notch under him and one crossing the bottom middle, so the way up stays shut as the wall breaks. 3 has no wall.
const START_ALONG := {
	3: [400.0, 1657.0, 2914.0],
	4: [3369.0, 540.0, 2426.0, 1483.0],
	5: [100.0, 3116.0, 854.0, 2362.0, 1608.0],
}
# A tornado's core round its base: a player's feet inside it are burned. The burn's latch holds until they are out past
# it grown by CORE_LATCH_GROW.
const TORNADO_CORE := Vector2(48, 20)
const CORE_LATCH_GROW := 12.0
# How far apart two cores' bases must stay (both cores and a band and a player between).
const CORE_APART := 2.0 * TORNADO_CORE.x + 36.0 + 24.0
# The player's feet point off their centre.
const FEET := Vector2(0, 42)
# Where the fire rings are drawn and where they hurt: from his row's face down.
const RING_SHOWN := Rect2(92, 348, 1734, 640)
const RING_HURT := Rect2(105, 348, 1710, 627)
# Every base keeps inside this, and the front spot's feet this far outside every ring's zone.
const SPOT_AREA := Rect2(185, 428, 1550, 507)
const FRONT_ZONE_MARGIN := 12.0
# Every attack starts with the player on RESET_SPOT: no start this close, or its ignition drags them straight in.
const RESET_CLEAR := 180.0
# While the ice melts out from them, a moving tornado leaves a melt centre behind this often, px of its travel.
const MELT_STAMP := 48.0
# The player centres the coverage check sweeps: below the row, inside the ropes.
const COVER_AREA := Rect2(123, 390, 1674, 544)
const COVER_CELL := 16.0

#THE WALL OF FIRE (the user's option A, 2026-10-04): they rise in a line across the ring between the player and him,
# alternate tornados ringing half a ring cycle apart so the line never has a walkable gap, and after it breaks they glide
# out to START_ALONG and roam from there.
const WALL_Y := 640.0
const WALL_X := {3: [360.0, 960.0, 1560.0], 4: [190.0, 703.0, 1217.0, 1730.0], 5: [190.0, 575.0, 960.0, 1345.0, 1730.0]}
# Each wall tornado's first ring, in quake_intervals after its first pair's.
const WALL_PHASE := {3: [0.0, 0.5, 0.0], 4: [0.0, 0.5, 0.0, 0.5], 5: [0.0, 0.5, 0.0, 0.5, 0.0]}
# A player the downdraft holds stands lower (y 933, feet 975); the wall is checked against this more cautious line.
const HOLD_FEET_Y := 902.0
const HOLD_CLEAR := 60.0
# Every column from rope to rope crosses at least this much of some wall tornado's ring zone.
const WALL_DEPTH := 80.0
const GLIDE_MAX := 300.0
# The ropes' inside edges across, the columns wall_leaks() walks up, and the walk's speed.
const ROPE_X := Vector2(113, 1805)
const LEAK_X := Vector2(131, 1787)
const LEAK_STEP := 16.0
const WALK := 600.0
# The player's hurtbox (MainPlayer.tscn: 24 x 54, centred 1 px under them), whose foot a ring tests
# (BixbyQuakeRingScript._damage_player); liam_firestorm_gate checks these against the player.
const HURT_HALF := Vector2(12, 27)
const HURT_OFFSET := Vector2(0, 1)


static func track_length() -> float:
	var total := 0.0
	for i in TRACK.size():
		total += (TRACK[i] as Vector2).distance_to(TRACK[(i + 1) % TRACK.size()])
	return total


# The point `along` px round the track from its start, round again past its end.
static func track_point(along: float) -> Vector2:
	var left := fposmod(along, track_length())
	for i in TRACK.size():
		var from: Vector2 = TRACK[i]
		var to: Vector2 = TRACK[(i + 1) % TRACK.size()]
		var length := from.distance_to(to)
		if left <= length:
			return from.lerp(to, left / length)
		left -= length
	return TRACK[0]


static func starts(count: int) -> Array:
	return START_ALONG.get(count, START_ALONG[4])


# Where the tornados start roaming: their START_ALONG points on the track.
static func spots(count: int) -> Array:
	return starts(count).map(func(along: float) -> Vector2: return track_point(along))


# Where they rise: the wall, in the same order as START_ALONG.
static func wall_spots(count: int) -> Array:
	return WALL_X.get(count, WALL_X[4]).map(func(x: float) -> Vector2: return Vector2(x, WALL_Y))


static func ring_phase(count: int, i: int) -> float:
	var phases: Array = WALL_PHASE.get(count, WALL_PHASE[4])
	return phases[i] if i < phases.size() else 0.0


# A wall tornado `weight` (0 to 1) of the way out to its roam start, eased in and out.
static func glide(from: Vector2, to: Vector2, weight: float) -> Vector2:
	return from.lerp(to, smoothstep(0.0, 1.0, weight))


# The tornados' pull at `point` for the state machine's knobs, before its ramp: each drags toward its base at
# tornado_pull, full inside tornado_pull_full and gone at tornado_pull_radius, easing off inside tornado_dead_zone; none
# within front_calm_radius of the front spot, fading in over front_calm_fade; the sum capped at tornado_pull_cap.
static func pull_field(point: Vector2, sm: Node, bases: Array) -> Vector2:
	var sum := Vector2.ZERO
	for base: Vector2 in bases:
		var d := point.distance_to(base)
		if d < 0.001:
			continue
		var reach := clampf((sm.tornado_pull_radius - d) / (sm.tornado_pull_radius - sm.tornado_pull_full), 0.0, 1.0)
		sum += (base - point) / d * sm.tornado_pull * reach * minf(d / sm.tornado_dead_zone, 1.0)
	var calm := smoothstep(sm.front_calm_radius, sm.front_calm_radius + sm.front_calm_fade, point.distance_to(sm.FRONT_SPOT))
	return (sum * calm).limit_length(sm.tornado_pull_cap)


# A ring's zone round its base, as the floor ellipse its band reaches: quake_max_radius and the band's half width across,
# flattened the way the floor is drawn.
static func zone_radii(sm: Node) -> Vector2:
	var across: float = sm.quake_max_radius + CombinedLayout.RING_HURT_HALF_WIDTH
	return Vector2(across, across * CombinedLayout.FLOOR_FLATTEN)


# The front spot's feet: the foot of the hurtbox, RING_FOOT_HEIGHT tall.
static func front_feet(sm: Node) -> Rect2:
	return Rect2(sm.FRONT_SPOT + FEET - Vector2(18, CombinedLayout.RING_FOOT_HEIGHT), Vector2(36, CombinedLayout.RING_FOOT_HEIGHT))


# Whether a ring from `base` would reach the front spot's feet, the margin included: the front keep-out.
static func ring_reaches_front(base: Vector2, sm: Node) -> bool:
	var feet := front_feet(sm)
	var nearest := base.clamp(feet.position, feet.end) - base
	return Vector2(nearest.x, nearest.y / CombinedLayout.FLOOR_FLATTEN).length() < zone_radii(sm).x + FRONT_ZONE_MARGIN


# Where a tornado aiming for `point` stands: inside SPOT_AREA, and pushed straight down out of the front keep-out.
static func place(point: Vector2, sm: Node) -> Vector2:
	var at := point.clamp(SPOT_AREA.position, SPOT_AREA.end)
	var feet := front_feet(sm)
	var keep_out: float = zone_radii(sm).x + FRONT_ZONE_MARGIN
	var across := maxf(absf(at.x - feet.get_center().x) - feet.size.x / 2.0, 0.0)
	if across < keep_out:
		at.y = maxf(at.y, feet.end.y + sqrt(keep_out * keep_out - across * across) * CombinedLayout.FLOOR_FLATTEN + 0.5)
	return at


# Everything wrong with the firestorm's layout at the state machine's knobs, in words: empty when it is sound.
static func validate(sm: Node) -> Array[String]:
	var problems: Array[String] = []
	var length := track_length()
	var samples: Array[Vector2] = []
	var along := 0.0
	while along < length:
		samples.append(track_point(along))
		along += COVER_CELL
	for point in samples:
		if not SPOT_AREA.grow(0.5).has_point(point):
			problems.append("the track at %s is outside %s" % [point, SPOT_AREA])
			break
	for point in samples:
		if ring_reaches_front(point, sm):
			problems.append("the track at %s is inside the front keep-out" % point)
			break
	var from: Array = starts(sm.tornado_count).duplicate()
	from.sort()
	var apart: float = 2.0 * sm.tornado_lean + CORE_APART
	for i in from.size():
		var base := track_point(from[i])
		if base.distance_to(sm.RESET_SPOT) < RESET_CLEAR:
			problems.append("the start at %s is %.0f px from the reset spot, under %.0f" % [base, base.distance_to(sm.RESET_SPOT), RESET_CLEAR])
		var gap := fposmod(from[(i + 1) % from.size()] - from[i], length)
		if from.size() > 1 and gap < apart:
			problems.append("the starts %.0f and %.0f are %.0f px apart along the track, under %.0f" % [from[i], from[(i + 1) % from.size()], gap, apart])
	if sm.tornado_pull_cap > 500.0:
		problems.append("the pull's cap %.0f is over 500" % sm.tornado_pull_cap)
	var at_front := pull_field(sm.FRONT_SPOT, sm, spots(sm.tornado_count))
	if at_front.length() > 0.0:
		problems.append("the pull at the front spot is %s" % at_front)
	# Every player spot outside the front calm is inside some track point's ring zone, on their feet.
	var calm: float = sm.front_calm_radius + sm.front_calm_fade
	var zone: float = zone_radii(sm).x
	var bare := 0
	var y := COVER_AREA.position.y
	while y <= COVER_AREA.end.y:
		var x := COVER_AREA.position.x
		while x <= COVER_AREA.end.x:
			var centre := Vector2(x, y)
			if centre.distance_to(sm.FRONT_SPOT) > calm:
				var feet := centre + FEET
				var covered := false
				for point in samples:
					var off := feet - point
					if Vector2(off.x, off.y / CombinedLayout.FLOOR_FLATTEN).length() <= zone:
						covered = true
						break
				if not covered:
					bare += 1
			x += COVER_CELL
		y += COVER_CELL
	if bare > 0:
		problems.append("%d player spots outside the front calm are out of every ring's reach from the track" % bare)
	problems.append_array(validate_wall(sm))
	return problems


# Every walk straight up through the wall that nothing touches, in words: a walker at every LEAK_STEP px across, its
# feet starting on HOLD_FEET_Y wall_release + d after IGNITION for every frame d of one ring cycle, walking up at WALK
# until its feet are past the wall's zones. Its hurtbox's foot is tested against every live ring's band the way a ring
# does, and its feet against every core. The tornados stand still on the wall and the pull is left out.
# Not part of validate_wall: with every ring 0.3 s dead between two (quake_max_radius 360 reached in 1.2 s of the
# user's 1.5 s cycle) it finds windows of up to 8 frames beside each tornado, but in the game the pull closes nearly
# all of them (liam_firestorm_gate's straight walks, and the tuning sweep of 2026-10-04: a few single frames).
static func wall_leaks(sm: Node) -> Array[String]:
	var leaks: Array[String] = []
	var bases := wall_spots(sm.tornado_count)
	var top: float = WALL_Y - zone_radii(sm).y - 13.0
	var step := 1.0 / 60.0
	var x := LEAK_X.x
	while x <= LEAK_X.y:
		var d := 0.0
		while d < sm.quake_interval - 0.0001:
			var t: float = sm.wall_release + d
			var feet := Vector2(x, HOLD_FEET_Y)
			var touched := false
			while feet.y > top and not touched:
				touched = wall_touches(feet, t, bases, sm)
				t += step
				feet.y -= WALK * step
			if not touched:
				leaks.append("a walk straight up at x %.0f leaving %.3f s after the release" % [x, d])
			d += step
		x += LEAK_STEP
	return leaks


# Whether a player with their feet at `feet`, `t` s after IGNITION, is touched by a wall tornado's core or the live
# band of one of its rings.
static func wall_touches(feet: Vector2, t: float, bases: Array, sm: Node) -> bool:
	var centre: Vector2 = feet - FEET
	var half_width := CombinedLayout.RING_HURT_HALF_WIDTH
	for i in bases.size():
		var base: Vector2 = bases[i]
		var core: Vector2 = feet - base
		if pow(core.x / TORNADO_CORE.x, 2.0) + pow(core.y / TORNADO_CORE.y, 2.0) <= 1.0:
			return true
		var since: float = t - sm.quake_first - ring_phase(bases.size(), i) * sm.quake_interval
		if since < 0.0:
			continue
		var radius: float = sm.quake_start_radius + sm.quake_speed * fmod(since, sm.quake_interval)
		if radius >= sm.quake_max_radius:
			continue
		var foot := Rect2(centre + HURT_OFFSET + Vector2(-HURT_HALF.x, HURT_HALF.y - CombinedLayout.RING_FOOT_HEIGHT) - base,
			Vector2(HURT_HALF.x * 2.0, CombinedLayout.RING_FOOT_HEIGHT))
		var on_floor := Rect2(foot.position.x, foot.position.y / CombinedLayout.FLOOR_FLATTEN,
			foot.size.x, foot.size.y / CombinedLayout.FLOOR_FLATTEN)
		var nearest := Vector2.ZERO.clamp(on_floor.position, on_floor.end).length()
		var farthest := 0.0
		for corner: Vector2 in [on_floor.position, Vector2(on_floor.end.x, on_floor.position.y), Vector2(on_floor.position.x, on_floor.end.y), on_floor.end]:
			farthest = maxf(farthest, corner.length())
		if nearest <= radius + half_width and farthest >= radius - half_width:
			return true
	return false


# Everything wrong with the wall at the state machine's knobs, in words: empty when it is sound.
static func validate_wall(sm: Node) -> Array[String]:
	var problems: Array[String] = []
	var count: int = sm.tornado_count
	var wall := wall_spots(count)
	var radii := zone_radii(sm)
	for i in wall.size():
		var spot: Vector2 = wall[i]
		if not SPOT_AREA.has_point(spot):
			problems.append("the wall spot %s is outside %s" % [spot, SPOT_AREA])
		if ring_reaches_front(spot, sm):
			problems.append("the wall spot %s is inside the front keep-out" % spot)
		if spot.distance_to(sm.RESET_SPOT) < RESET_CLEAR:
			problems.append("the wall spot %s is %.0f px from the reset spot, under %.0f" % [spot, spot.distance_to(sm.RESET_SPOT), RESET_CLEAR])
		if i + 1 < wall.size():
			if spot.distance_to(wall[i + 1]) < CORE_APART:
				problems.append("the wall spots %s and %s are under %.0f px apart" % [spot, wall[i + 1], CORE_APART])
			if not is_equal_approx(absf(ring_phase(count, i) - ring_phase(count, i + 1)), 0.5):
				problems.append("the wall tornados %d and %d don't ring half a cycle apart" % [i, i + 1])
		var to := track_point(starts(count)[i])
		if spot.distance_to(to) > GLIDE_MAX:
			problems.append("the glide from %s to %s is %.0f px, over %.0f" % [spot, to, spot.distance_to(to), GLIDE_MAX])
	if WALL_Y + radii.y + HOLD_CLEAR > HOLD_FEET_Y:
		problems.append("a held player's feet at %.0f are within %.0f px of the wall's zones (%.0f)" % [HOLD_FEET_Y, HOLD_CLEAR, WALL_Y + radii.y])
	var x := ROPE_X.x
	while x <= ROPE_X.y:
		var deepest := 0.0
		for spot: Vector2 in wall:
			var across := absf(x - spot.x) / radii.x
			if across < 1.0:
				deepest = maxf(deepest, 2.0 * radii.y * sqrt(1.0 - across * across))
		if deepest < WALL_DEPTH:
			problems.append("the column at x %.0f crosses only %.0f px of the wall's zones, under %.0f" % [x, deepest, WALL_DEPTH])
		x += LEAK_STEP
	var at_front := pull_field(sm.FRONT_SPOT, sm, wall)
	if at_front.length() > 0.0:
		problems.append("the wall's pull at the front spot is %s" % at_front)
	return problems
