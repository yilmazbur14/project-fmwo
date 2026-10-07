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
# hurting after that; each zone's notice and ring; and the slams' clock on the same count - each slam as it lands,
# and `start`, when a player can first play the maze: every zone down (the last slam) and zone 1 told, and never
# after zone 1's ring begins.
static func clock(t) -> Dictionary:
	var pose: Node = t.sm.states["Pose"]
	var slams: Node = t.sm.states["Slams"]
	var burst: Dictionary = load("res://Scripts/GreysonArtLayout.gd").fx(&"erupt_burst")
	var zone: Dictionary = load("res://Scripts/GreysonArtLayout.gd").fx(&"zone")
	var frames: Array = burst.hurt_frames
	var strike: float = slams.duration() + pose.turn_time
	var first: float = 2.0 * slams.teleport_time + slams.windup_time
	var apart: float = first + slams.recover_time
	var landings: Array[float] = []
	for k in slams.slams:
		landings.append(first + apart * k - strike)
	var eruptions: Array = pose.eruptions.duplicate()
	var start: float = minf(maxf(eruptions[0] - pose.eruption_notice, landings[-1]), eruptions[0] - zone.ring_lead)
	return {eruptions = eruptions, ring = zone.ring_lead, radii = zone.radii, notice = pose.eruption_notice,
		first_hurt = frames[0] * burst.frame_time, hurt_end = (frames[-1] + 1) * burst.frame_time,
		landings = landings, start = start, per_slam = slams.zones_per_slam}


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


# STEPPED, for the weave and the earliest punch: time in STEP_TIME steps and the floor in STEP_CELL cells, a row a
# bitmask, so a player standing across bursts can be followed step by step (the octile sets above only say where
# they can be as each burst comes). A step moves a cell to any of its eight neighbours: STEP_CELL px straight in
# STEP_TIME is the player's walk, and the diagonal is the keyboard's own diagonal (PlayerScript moves both axes at
# full speed).
const STEP_TIME := 0.05
const STEP_CELL := 30.0


static func step_grid(ropes: Rect2) -> Dictionary:
	var columns := int(ropes.size.x / STEP_CELL)
	return {origin = ropes.position, columns = columns, rows = int(ropes.size.y / STEP_CELL), full = (1 << columns) - 1}


static func step_centre(grid: Dictionary, row: int, column: int) -> Vector2:
	return grid.origin + (Vector2(column, row) + Vector2(0.5, 0.5)) * STEP_CELL


static func step_cell(grid: Dictionary, point: Vector2) -> Vector2i:
	return Vector2i(clampi(int((point.x - grid.origin.x) / STEP_CELL), 0, grid.columns - 1),
		clampi(int((point.y - grid.origin.y) / STEP_CELL), 0, grid.rows - 1))


static func has_cell(rows: PackedInt64Array, cell: Vector2i) -> bool:
	return (rows[cell.y] >> cell.x) & 1 == 1


# A row's bit set where a cell's centre is `margin` or more outside the zone on `centre`.
static func step_outside(grid: Dictionary, centre: Vector2, radii: Vector2, margin: float) -> PackedInt64Array:
	var rows := PackedInt64Array()
	rows.resize(grid.rows)
	var half := radii + Vector2.ONE * margin
	for row in grid.rows:
		var bits := 0
		for column in grid.columns:
			var d := step_centre(grid, row, column) - centre
			if pow(d.x / half.x, 2.0) + pow(d.y / half.y, 2.0) > 1.0:
				bits |= 1 << column
		rows[row] = bits
	return rows


# Every cell one step from a set one, or on it.
static func step_spread(grid: Dictionary, rows: PackedInt64Array) -> PackedInt64Array:
	var out := PackedInt64Array()
	out.resize(rows.size())
	var full: int = grid.full
	for row in rows.size():
		var near := rows[row]
		if row > 0:
			near |= rows[row - 1]
		if row < rows.size() - 1:
			near |= rows[row + 1]
		out[row] = (near | (near << 1) | (near >> 1)) & full
	return out


static func step_and(a: PackedInt64Array, b: PackedInt64Array) -> PackedInt64Array:
	var out := PackedInt64Array()
	out.resize(a.size())
	for row in a.size():
		out[row] = a[row] & b[row]
	return out


# The whole run on the steps from `start_time` (the eruptions' clock) to `until`: each step's time and the cells safe
# then - clear of every zone whose burst is hurting - and, walking from `start`, where the player can be on each step
# (reach) and where they can be and still come through every burst after (live).
static func stepped(grid: Dictionary, start: Vector2, zones: Array, times: Dictionary, start_time: float, margin: float, until: float) -> Dictionary:
	var clear: Array = []
	for zone in zones:
		clear.append(step_outside(grid, zone, times.radii, margin))
	var all := PackedInt64Array()
	all.resize(grid.rows)
	all.fill(grid.full)
	var count := int(ceilf((until - start_time) / STEP_TIME)) + 1
	var clocks: Array[float] = []
	var safe: Array = []
	for i in count:
		var at: float = start_time + i * STEP_TIME
		clocks.append(at)
		var rows := all
		for k in zones.size():
			# A step before the burst starts hurting or after it stops still counts if the walk to or from its cell
			# overlaps the burst: the steps fall anywhere against the eruptions, and a hurt frame 0.003 s after a step
			# found the player still on the way out of it.
			if at > times.eruptions[k] + times.first_hurt - STEP_TIME + 0.0001 and at < times.eruptions[k] + times.hurt_end + STEP_TIME - 0.0001:
				rows = step_and(rows, clear[k])
		safe.append(rows)
	var reach: Array = []
	var here := PackedInt64Array()
	here.resize(grid.rows)
	var first := step_cell(grid, start)
	here[first.y] = 1 << first.x
	for i in count:
		if i > 0:
			here = step_spread(grid, here)
		here = step_and(here, safe[i])
		reach.append(here)
	var live: Array = []
	live.resize(count)
	var after: PackedInt64Array = safe[count - 1]
	live[count - 1] = after
	for i in range(count - 2, -1, -1):
		after = step_and(step_spread(grid, after), safe[i])
		live[i] = after
	return {clocks = clocks, safe = safe, reach = reach, live = live}


# The first step a walk from the run's start can stand on one of `goals` for `hold` s and come through every burst
# after: its index, or -1. On the eruptions' clock, no sooner than `not_before` (his window opening).
static func first_punch(run: Dictionary, goals: Array[Vector2i], hold: float, not_before: float) -> Dictionary:
	var span := int(ceilf(hold / STEP_TIME))
	var count: int = run.clocks.size()
	for i in count - span:
		if run.clocks[i] < not_before - 0.0001:
			continue
		for goal in goals:
			if not has_cell(run.reach[i], goal) or not has_cell(run.live[i + span], goal):
				continue
			var stays := true
			for j in range(i, i + span + 1):
				stays = stays and has_cell(run.safe[j], goal)
			if stays:
				return {step = i, cell = goal}
	return {}


# That walk, a cell a step from the start to the punch, then holding there, then on through the bursts after it:
# [{at, to, punch}] on the eruptions' clock, `punch` on the step the hold starts. Staying put is always preferred.
static func punch_route(grid: Dictionary, run: Dictionary, punch: Dictionary, hold: float) -> Array:
	var span := int(ceilf(hold / STEP_TIME))
	var cells: Array[Vector2i] = []
	cells.resize(punch.step + 1)
	cells[punch.step] = punch.cell
	for i in range(punch.step - 1, -1, -1):
		cells[i] = _step_back(grid, run.reach[i], cells[i + 1])
	for i in span:
		cells.append(punch.cell)
	var count: int = run.clocks.size()
	for i in range(punch.step + span + 1, count):
		cells.append(_step_toward(grid, run.live[i], cells[i - 1], punch.cell))
	var route: Array = []
	for i in cells.size():
		if i == 0 or cells[i] != cells[i - 1] or i == punch.step:
			route.append({at = run.clocks[i], to = step_centre(grid, cells[i].y, cells[i].x), punch = i == punch.step})
	return route


# A cell of `rows` a step from `cell` (itself first).
static func _step_back(grid: Dictionary, rows: PackedInt64Array, cell: Vector2i) -> Vector2i:
	if has_cell(rows, cell):
		return cell
	for d in [Vector2i(0, -1), Vector2i(0, 1), Vector2i(-1, 0), Vector2i(1, 0), Vector2i(-1, -1), Vector2i(1, -1), Vector2i(-1, 1), Vector2i(1, 1)]:
		var near: Vector2i = cell + d
		if near.x >= 0 and near.y >= 0 and near.x < grid.columns and near.y < grid.rows and has_cell(rows, near):
			return near
	return cell


# The cell of `rows` a step from `cell` nearest `goal`, staying put if `cell` is one.
static func _step_toward(grid: Dictionary, rows: PackedInt64Array, cell: Vector2i, goal: Vector2i) -> Vector2i:
	if has_cell(rows, cell):
		return cell
	var best := cell
	var best_gap := INF
	for dy in [-1, 0, 1]:
		for dx in [-1, 0, 1]:
			var near := cell + Vector2i(dx, dy)
			if near.x < 0 or near.y < 0 or near.x >= grid.columns or near.y >= grid.rows or not has_cell(rows, near):
				continue
			var gap := Vector2(near - goal).length()
			if gap < best_gap:
				best = near
				best_gap = gap
	return best
