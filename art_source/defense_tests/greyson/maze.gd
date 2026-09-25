extends RefCounted

# The fence-in slam zones as a timed maze (coder B), for slams.gd's fence tiers: the floor inside the ropes in
# CELL cells, which cells a walking player may stand on as each zone goes off, and a walk through them.
# A zone's burst hurts on its hurt frames only, so the player must be clear of zone k from t_k + first_hurt to
# t_k + hurt_end, and may be anywhere else, inside zones still to go off included. Between those windows they walk
# at WALK px/s, never dashing. Distances are octile over the cells, never shorter than the straight walk, so every
# set here is one a walking player can really keep to.

const CELL := 20.0
const WALK := 600.0
const DIAGONAL := 1.41421356


static func make_grid(ropes: Rect2) -> Dictionary:
	return {origin = ropes.position, columns = int(ropes.size.x / CELL), rows = int(ropes.size.y / CELL)}


static func centre_of(grid: Dictionary, index: int) -> Vector2:
	var column: int = index % grid.columns
	var row: int = floori(index / float(grid.columns))
	return grid.origin + (Vector2(column, row) + Vector2(0.5, 0.5)) * CELL


static func index_of(grid: Dictionary, point: Vector2) -> int:
	var column := clampi(int((point.x - grid.origin.x) / CELL), 0, grid.columns - 1)
	var row := clampi(int((point.y - grid.origin.y) / CELL), 0, grid.rows - 1)
	return row * grid.columns + column


# 1 where a cell's centre is `margin` or more outside the zone.
static func outside(grid: Dictionary, centre: Vector2, radii: Vector2, margin: float) -> PackedByteArray:
	var mask := PackedByteArray()
	mask.resize(grid.columns * grid.rows)
	var half := radii + Vector2.ONE * margin
	for index in mask.size():
		var d := centre_of(grid, index) - centre
		mask[index] = 1 if pow(d.x / half.x, 2.0) + pow(d.y / half.y, 2.0) > 1.0 else 0
	return mask


static func both(a: PackedByteArray, b: PackedByteArray) -> PackedByteArray:
	var out := PackedByteArray()
	out.resize(a.size())
	for i in a.size():
		out[i] = a[i] & b[i]
	return out


static func count(mask: PackedByteArray) -> int:
	var total := 0
	for value in mask:
		total += value
	return total


# The octile walk in px from the nearest cell set in `mask` to every cell (INF for none).
static func distance_from(grid: Dictionary, mask: PackedByteArray) -> PackedFloat32Array:
	var columns: int = grid.columns
	var rows: int = grid.rows
	var far := PackedFloat32Array()
	far.resize(mask.size())
	for i in mask.size():
		far[i] = 0.0 if mask[i] == 1 else INF
	var straight := CELL
	var slant := CELL * DIAGONAL
	for row in rows:
		for column in columns:
			var i := row * columns + column
			var best: float = far[i]
			if column > 0:
				best = minf(best, far[i - 1] + straight)
			if row > 0:
				best = minf(best, far[i - columns] + straight)
				if column > 0:
					best = minf(best, far[i - columns - 1] + slant)
				if column < columns - 1:
					best = minf(best, far[i - columns + 1] + slant)
			far[i] = best
	for row in range(rows - 1, -1, -1):
		for column in range(columns - 1, -1, -1):
			var i := row * columns + column
			var best: float = far[i]
			if column < columns - 1:
				best = minf(best, far[i + 1] + straight)
			if row < rows - 1:
				best = minf(best, far[i + columns] + straight)
				if column < columns - 1:
					best = minf(best, far[i + columns + 1] + slant)
				if column > 0:
					best = minf(best, far[i + columns - 1] + slant)
			far[i] = best
	return far


static func within(grid: Dictionary, mask: PackedByteArray, reach: float) -> PackedByteArray:
	var far := distance_from(grid, mask)
	var out := PackedByteArray()
	out.resize(mask.size())
	for i in far.size():
		out[i] = 1 if far[i] <= reach else 0
	return out


# The eruptions' clock, after the first pose's strike: when each goes off, and when its burst starts and stops
# hurting after that.
static func clock(t) -> Dictionary:
	var pose: Node = t.sm.states["Pose"]
	var burst: Dictionary = load("res://Scripts/GreysonArtLayout.gd").fx(&"erupt_burst")
	var zone: Dictionary = load("res://Scripts/GreysonArtLayout.gd").fx(&"zone")
	var frames: Array = burst.hurt_frames
	return {eruptions = pose.eruptions.duplicate(), ring = zone.ring_lead, radii = zone.radii,
		first_hurt = frames[0] * burst.frame_time, hurt_end = (frames[-1] + 1) * burst.frame_time}


# Interval k's walking time: up to zone k's first hurt, from the start (k = 0) or from zone k-1's last.
static func leg_time(times: Dictionary, k: int, start_time: float) -> float:
	var from: float = start_time if k == 0 else times.eruptions[k - 1] + times.hurt_end
	return times.eruptions[k] + times.first_hurt - from


# Where a player walking from `start` at `start_time` can stand through each zone's burst, in order: the sets are
# empty from the first eruption they can't come through on.
static func forward(grid: Dictionary, start: Vector2, zones: Array, times: Dictionary, start_time: float, margin: float) -> Array:
	var sets: Array = []
	var here := PackedByteArray()
	here.resize(grid.columns * grid.rows)
	here[index_of(grid, start)] = 1
	for k in zones.size():
		here = both(within(grid, here, WALK * leg_time(times, k, start_time)), outside(grid, zones[k], times.radii, margin))
		sets.append(here)
	return sets


# Where a player standing through zone k's burst can go on and come through all the later ones.
static func backward(grid: Dictionary, zones: Array, times: Dictionary, margin: float) -> Array:
	var sets: Array = []
	sets.resize(zones.size())
	var last := zones.size() - 1
	sets[last] = outside(grid, zones[last], times.radii, margin)
	for k in range(last - 1, -1, -1):
		sets[k] = both(outside(grid, zones[k], times.radii, margin), within(grid, sets[k + 1], WALK * leg_time(times, k + 1, 0.0)))
	return sets


# A walk from `start` at `start_time` that comes through every burst and stands on `goal` for `hold` s as early as
# it can: {legs: [{from, to, punch}] in pose time, at: when it gets to `goal`, interval: the one it punches in}, or
# {} if it can't. Leg k is walked from its `from`; a punch leg holds on `goal` and then walks on to its `to`.
static func weave(grid: Dictionary, start: Vector2, zones: Array, times: Dictionary, start_time: float, margin: float, goal: Vector2, hold: float) -> Dictionary:
	var fwd := forward(grid, start, zones, times, start_time, margin)
	var back := backward(grid, zones, times, margin)
	var n := zones.size()
	var to_goal := distance_from(grid, _single(grid, goal))
	for j in n + 1:
		var begin: float = start_time if j == 0 else times.eruptions[j - 1] + times.hurt_end
		var near := INF
		var from_cell := -1
		if j == 0:
			near = start.distance_to(goal)
		else:
			var standing := both(fwd[j - 1], back[j - 1])
			for i in standing.size():
				if standing[i] == 1 and to_goal[i] < near:
					near = to_goal[i]
					from_cell = i
		if near == INF:
			continue
		var onward := 0.0
		var onward_cell := -1
		if j < n:
			onward = INF
			for i in back[j].size():
				if back[j][i] == 1 and goal.distance_to(centre_of(grid, i)) < onward:
					onward = goal.distance_to(centre_of(grid, i))
					onward_cell = i
		var length: float = INF if j == n else times.eruptions[j] + times.first_hurt - begin
		if (near + onward) / WALK + hold > length:
			continue
		var legs: Array = []
		var here := start
		var waypoints: Array = []
		if j > 0:
			waypoints = _back_track(grid, fwd, from_cell, j - 1, times, start_time)
		for k in waypoints.size():
			var leave: float = start_time if k == 0 else times.eruptions[k - 1] + times.hurt_end
			legs.append({from = leave, to = waypoints[k], punch = false})
			here = waypoints[k]
		legs.append({from = begin, to = goal, punch = true})
		if j < n:
			legs.append({from = begin + near / WALK + hold, to = centre_of(grid, onward_cell), punch = false})
			var at: int = onward_cell
			for k in range(j + 1, n):
				at = _step_on(grid, back[k], at, WALK * leg_time(times, k, start_time), goal)
				legs.append({from = times.eruptions[k - 1] + times.hurt_end, to = centre_of(grid, at), punch = false})
		return {legs = legs, at = begin + near / WALK, interval = j}
	return {}


# The earliest a walk from `start` at `start_time` can stand on any cell of `goals` for `hold` s and still come
# through every burst: {at, interval}, or {} if never. Cells are paired - the walk in and the walk on are from the
# same goal cell.
static func earliest(grid: Dictionary, start: Vector2, zones: Array, times: Dictionary, start_time: float, margin: float, goals: PackedByteArray, hold: float) -> Dictionary:
	var fwd := forward(grid, start, zones, times, start_time, margin)
	var back := backward(grid, zones, times, margin)
	var n := zones.size()
	for j in n + 1:
		var begin: float = start_time if j == 0 else times.eruptions[j - 1] + times.hurt_end
		var inward: PackedFloat32Array
		if j == 0:
			inward = distance_from(grid, _single(grid, start))
		else:
			inward = distance_from(grid, both(fwd[j - 1], back[j - 1]))
		var onward := PackedFloat32Array()
		if j < n:
			onward = distance_from(grid, back[j])
		var length: float = INF if j == n else times.eruptions[j] + times.first_hurt - begin
		var soonest := INF
		for i in goals.size():
			if goals[i] == 0 or inward[i] == INF:
				continue
			var out: float = 0.0 if j == n else onward[i]
			if (inward[i] + out) / WALK + hold <= length:
				soonest = minf(soonest, begin + inward[i] / WALK)
		if soonest < INF:
			return {at = soonest, interval = j}
	return {}


static func _single(grid: Dictionary, point: Vector2) -> PackedByteArray:
	var mask := PackedByteArray()
	mask.resize(grid.columns * grid.rows)
	mask[index_of(grid, point)] = 1
	return mask


# The cells stood on through bursts 0..last, ending on `cell`, each a straight walk from the one before.
static func _back_track(grid: Dictionary, fwd: Array, cell: int, last: int, times: Dictionary, start_time: float) -> Array:
	var points: Array = []
	points.resize(last + 1)
	points[last] = centre_of(grid, cell)
	for k in range(last, 0, -1):
		var reach: float = WALK * leg_time(times, k, start_time)
		var best := -1
		var best_gap := INF
		for i in fwd[k - 1].size():
			if fwd[k - 1][i] == 1:
				var gap: float = centre_of(grid, i).distance_to(points[k])
				if gap <= reach and gap < best_gap:
					best = i
					best_gap = gap
		points[k - 1] = centre_of(grid, best)
	return points


# The cell of `mask` a straight walk of `reach` from `cell` gets to that is nearest `goal`.
static func _step_on(grid: Dictionary, mask: PackedByteArray, cell: int, reach: float, goal: Vector2) -> int:
	var from := centre_of(grid, cell)
	var best := cell
	var best_gap := INF
	for i in mask.size():
		if mask[i] == 1 and centre_of(grid, i).distance_to(from) <= reach:
			var gap := centre_of(grid, i).distance_to(goal)
			if gap < best_gap:
				best = i
				best_gap = gap
	return best
