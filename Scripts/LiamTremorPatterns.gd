extends RefCounted

# Liam's tremor walls (attack 2, LiamTremors; addendum 5): a stream of flat walls running rope to rope, each with one
# gap, marching down the ring on his slams, a new one heaving at the top whenever the newest has marched stream_every
# steps down; and the offline check that the stream always leaves a way to the front spot (validate_stream). World px.
#
# Every block is BLOCK_SIZE (96x24 texels at 3x). A wall is a row of blocks from each rope to its gap, spread evenly so
# neighbours overlap by at least 48 px. Its gap is stream_gap wide round a centre from GAP_CYCLE, never at the middle
# or a rope, so every x on the floor is covered by at least every other wall and a camper gets swept. The first two
# walls rise at the heave (OPEN_TOPS: the lower one ending clear of the reset spot, the upper one at SPAWN_TOP, right
# under the front spot's clearance, so the front corridor is always above the newest wall and reached through its
# gap). Every later wall tells and heaves at SPAWN_TOP. The row and everything behind it is solid, and the one punch
# spot is the front spot.

const BLOCK_SIZE := Vector2(288, 72)
# Neighbouring blocks of a wall are spread at most this far apart, so they overlap by 48 px or more.
const BLOCK_SPREAD := 240.0
# The ropes the walls run between.
const ROPE_X := Vector2(113, 1805)
# The front spot and the room round it: no block may touch it.
const FRONT_CLEAR := Rect2(860, 348, 200, 150)
# The row (LiamRow) and everything behind it, which the flood fill treats as one wall.
const ROW_SOLID := Rect2(105, 105, 1710, 243)

# Where the player stands to punch his pillar (their centre): the front spot, LiamStateMachine.FRONT_SPOT.
const SPOTS := {
	&"front": Vector2(960, 402),
}

# Where a new wall heaves (its top), and where the two that heave at the start do. The lower one at 760 rather than
# 734 (addendum 5's second fallback, which keeps the user's wall every 7 slams): at 734 a run starting on the first gap
# order (runs 0, 3, ...) leaves no way to the front spot from x 780 (validate_stream).
const SPAWN_TOP := 498.0
const OPEN_TOPS := [760.0, 498.0]
# Gap centres in turn: a run's k-th wall (k 0 the lower opening wall) takes GAP_CYCLE[(2 run + k) % 6]. Valid centres
# are 521..1397, which leaves every side of a wall at least one block long.
const GAP_CYCLE := [1260.0, 660.0, 1380.0, 540.0, 1140.0, 780.0]
const STREAM_GAP := 240.0
# The narrowest a corridor between two walls may be as a new one heaves.
const MIN_CORRIDOR := 150.0
const BOTTOM_ROW_Y := 900.0

#THE FLOOD FILL (validate_stream)
# The player's floor (their centre), their body, the margin a cell keeps from every wall, and the grid.
const PLAYER_FLOOR := Rect2(123, 145.5, 1674, 789)
const PLAYER_BODY := Vector2(36, 81)
const MARGIN := 6.0
const CELL := 16.0
# The bottom wall a marching block sinks at: LiamStateMachine.march_floor_y's default.
const MARCH_FLOOR_Y := 975.0
# Where every attack starts (the reset to the bottom middle, addendum 4) and what a player reaches from there along the
# ice before the heave: the bottom-row starts validate_stream is run from. The pace a player makes on the ice, px/s.
const RESET_STARTS := [780.0, 870.0, 960.0, 1050.0, 1140.0]
const ICE_PACE := 400.0


static func gap_centre(run: int, k: int) -> float:
	return GAP_CYCLE[posmod(2 * run + k, GAP_CYCLE.size())]


# One wall rope to rope with its top at `top` and a gap `gap_width` wide round `centre`: each side a row of blocks from
# its rope to the gap, the first flush with the one and the last with the other, spread evenly between.
static func stream_wall(centre: float, top: float, gap_width := STREAM_GAP) -> Array[Rect2]:
	var out: Array[Rect2] = []
	for side: Vector2 in [Vector2(ROPE_X.x, centre - gap_width / 2.0), Vector2(centre + gap_width / 2.0, ROPE_X.y)]:
		var length := side.y - side.x
		var count := ceili((length - BLOCK_SIZE.x) / BLOCK_SPREAD) + 1
		var spread := (length - BLOCK_SIZE.x) / maxf(count - 1, 1)
		for i in count:
			out.append(Rect2(Vector2(roundf(side.x + i * spread), top), BLOCK_SIZE))
	return out


# A run's walls in the order they rise, k 0 the lower opening wall: {k, gap, top, rects (where it heaves), tell_slam,
# heave_slam, move_from}, slams counted from the heave (0). The opening walls tell on the crack (-1) and march from
# `delay`; each later wall tells a slam before it heaves, every `every` slams on from the delay, and marches from its
# heave. Only walls heaving before the run's `slams`-th slam, the timeout's.
static func schedule(run: int, delay: int, every: int, slams: int, gap_width := STREAM_GAP) -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	for k in OPEN_TOPS.size():
		var gap := gap_centre(run, k)
		out.append({k = k, gap = gap, top = OPEN_TOPS[k], rects = stream_wall(gap, OPEN_TOPS[k], gap_width),
			tell_slam = -1, heave_slam = 0, move_from = delay})
	var j := 1
	while delay + every * j < slams:
		var k := OPEN_TOPS.size() - 1 + j
		var heave := delay + every * j
		var gap := gap_centre(run, k)
		out.append({k = k, gap = gap, top = SPAWN_TOP, rects = stream_wall(gap, SPAWN_TOP, gap_width),
			tell_slam = heave - 1, heave_slam = heave, move_from = heave})
		j += 1
	return out


# Each wall there is over slam `slam` (0 the heave): {k, from, to}, its blocks where the slam starts and where it ends,
# any that had sunk by its start left out. A wall still to tell isn't there; a telling one stands where it will heave.
static func walls_at(walls: Array, slam: int, step: float, floor_y := MARCH_FLOOR_Y) -> Array:
	var out := []
	for wall: Dictionary in walls:
		if slam < wall.tell_slam:
			continue
		var from: float = maxi(slam - wall.move_from, 0) * step
		var to: float = maxi(slam + 1 - wall.move_from, 0) * step
		var here := []
		var there := []
		for rect: Rect2 in wall.rects:
			if rect.end.y + from >= floor_y:
				continue
			here.append(Rect2(rect.position + Vector2(0, from), rect.size))
			there.append(Rect2(rect.position + Vector2(0, to), rect.size))
		if not here.is_empty():
			out.append({k = wall.k, from = here, to = there})
	return out


#VALIDATION

# Everything wrong with run `run`'s stream, in words: empty when it is sound. One slam at a time on the flood fill's grid,
# from the heave to the run's last: a cell is shut if the player's body (with MARGIN) touches a block where that slam
# starts or where it ends, a telling wall included, or the row. From the bottom-row cells nearest each x of `starts`,
# the cells a player could be in grow by up to `pace_per_step` px of open cells a slam. Wrong: a start left with nowhere
# to be (a forced hit), a start that never reaches the front spot, an open cell cut off from it on any slam (there must
# always be a way), a block in the front spot's clearance, a wall rising onto a live one or leaving a corridor under
# MIN_CORRIDOR, a gap under `gap_width`.
static func validate_stream(run: int, step: float, delay: int, every: int, slams: int, pace_per_step: float, floor_y := MARCH_FLOOR_Y, starts: Array = RESET_STARTS, gap_width := STREAM_GAP) -> Array[String]:
	var problems: Array[String] = []
	var walls := schedule(run, delay, every, slams, gap_width)
	for wall: Dictionary in walls:
		var rects: Array = wall.rects
		var left := 0.0
		var right := INF
		for rect: Rect2 in rects:
			if rect.get_center().x < wall.gap:
				left = maxf(left, rect.end.x)
			else:
				right = minf(right, rect.position.x)
		if right - left < gap_width - 0.5:
			problems.append("run %d wall %d: its gap is %.0f px, under %.0f" % [run, wall.k, right - left, gap_width])
		if wall.tell_slam >= 0:
			var at_heave := walls_at(walls, wall.heave_slam, step, floor_y)
			var below := INF
			for other: Dictionary in at_heave:
				if other.k == wall.k:
					continue
				for rect: Rect2 in other.from:
					for mine: Rect2 in rects:
						if mine.intersects(rect):
							problems.append("run %d wall %d heaves onto wall %d" % [run, wall.k, other.k])
					if rect.position.y > wall.top:
						below = minf(below, rect.position.y)
			if below < INF and below - (wall.top + BLOCK_SIZE.y) < MIN_CORRIDOR:
				problems.append("run %d wall %d heaves %.0f px over the wall below, under %.0f" % [run, wall.k, below - wall.top - BLOCK_SIZE.y, MIN_CORRIDOR])
	var size := grid_size()
	var depth := int(pace_per_step / CELL)
	var open_by_slam: Array[PackedByteArray] = []
	var spots_by_slam: Array[PackedInt32Array] = []
	for slam in slams:
		var shut := []
		for wall: Dictionary in walls_at(walls, slam, step, floor_y):
			for rect: Rect2 in wall.from + wall.to:
				if rect.intersects(FRONT_CLEAR):
					problems.append("run %d slam %d: %s touches the front spot's clearance" % [run, slam, rect])
				shut.append(rect)
		var open := open_cells(shut)
		var spots := spot_cells(open)
		open_by_slam.append(open)
		spots_by_slam.append(spots)
		var reached := flood(open, spots)
		var stranded := 0
		for i in open.size():
			if open[i] == 1 and reached[i] == 0:
				stranded += 1
		if spots.is_empty() or stranded > 0:
			problems.append("run %d slam %d: %d open cells cut off from the front spot" % [run, slam, stranded])
	var bottom := (size.y - 1) * size.x
	for x: float in starts:
		var column := clampi(roundi((x - PLAYER_FLOOR.position.x) / CELL), 0, size.x - 1)
		var reached := PackedByteArray()
		reached.resize(size.x * size.y)
		reached[bottom + column] = 1
		var arrived := false
		for slam in open_by_slam.size():
			reached = _grow(reached, open_by_slam[slam], depth)
			if not reached.has(1):
				problems.append("run %d: from x %.0f on the bottom row, nowhere left to be on slam %d" % [run, x, slam])
				break
			for index in spots_by_slam[slam]:
				if reached[index] == 1:
					arrived = true
			if arrived:
				break
		if reached.has(1) and not arrived:
			problems.append("run %d: from x %.0f on the bottom row, no way to the front spot by the last slam" % [run, x])
	return problems


# The open cells within `depth` 4-connected steps of the cells of `from` that are still open.
static func _grow(from: PackedByteArray, open: PackedByteArray, depth: int) -> PackedByteArray:
	var columns := grid_size().x
	var seen := PackedByteArray()
	seen.resize(open.size())
	var queue := PackedInt32Array()
	for i in open.size():
		if from[i] == 1 and open[i] == 1:
			seen[i] = 1
			queue.append(i)
	var head := 0
	for level in depth:
		var level_end := queue.size()
		if head == level_end:
			break
		while head < level_end:
			var cell := queue[head]
			head += 1
			var column := cell % columns
			for next in [cell - columns, cell + columns, cell - 1 if column > 0 else -1, cell + 1 if column < columns - 1 else -1]:
				if next >= 0 and next < open.size() and open[next] == 1 and seen[next] == 0:
					seen[next] = 1
					queue.append(next)
	return seen


static func grid_size() -> Vector2i:
	return Vector2i(int(PLAYER_FLOOR.size.x / CELL) + 1, int(PLAYER_FLOOR.size.y / CELL) + 1)


static func cell_centre(column: int, row: int) -> Vector2:
	return PLAYER_FLOOR.position + Vector2(column, row) * CELL


# 1 where the player's body, centred on the cell and grown by MARGIN, touches neither a block nor the row.
static func open_cells(walls_px: Array) -> PackedByteArray:
	var size := grid_size()
	var cells := PackedByteArray()
	cells.resize(size.x * size.y)
	var half := PLAYER_BODY / 2.0 + Vector2.ONE * MARGIN
	var solid: Array = walls_px + [ROW_SOLID]
	for row in size.y:
		for column in size.x:
			var body := Rect2(cell_centre(column, row) - half, half * 2.0)
			var free := true
			for wall: Rect2 in solid:
				if body.intersects(wall):
					free = false
					break
			cells[row * size.x + column] = 1 if free else 0
	return cells


# The open cell nearest the front spot, if it is open.
static func spot_cells(open: PackedByteArray) -> PackedInt32Array:
	var size := grid_size()
	var out := PackedInt32Array()
	var at: Vector2 = ((SPOTS[&"front"] as Vector2) - PLAYER_FLOOR.position) / CELL
	var index := clampi(roundi(at.y), 0, size.y - 1) * size.x + clampi(roundi(at.x), 0, size.x - 1)
	if open[index] == 1:
		out.append(index)
	return out


# 1 on every open cell that reaches one of `from`, 4-connected.
static func flood(open: PackedByteArray, from: PackedInt32Array) -> PackedByteArray:
	var columns := grid_size().x
	var seen := PackedByteArray()
	seen.resize(open.size())
	var queue := PackedInt32Array()
	for start in from:
		if seen[start] == 0:
			seen[start] = 1
			queue.append(start)
	var head := 0
	while head < queue.size():
		var cell := queue[head]
		head += 1
		var column := cell % columns
		for next in [cell - columns, cell + columns, cell - 1 if column > 0 else -1, cell + 1 if column < columns - 1 else -1]:
			if next >= 0 and next < open.size() and open[next] == 1 and seen[next] == 0:
				seen[next] = 1
				queue.append(next)
	return seen
