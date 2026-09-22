extends SceneTree

# What a full poo cycle threatens and what it leaves open, against a player who keeps walking to the
# nearest safe spot. verify_mason_tuning's poo mode leaves the player standing still, and every line
# aims at them, so all of them stack on one row and the coverage it reads is a floor, not the figure.
# No window needed:
#   Godot.exe --headless --fixed-fps 60 --script res://art_source/mason_tuning/measure_poo_coverage.gd -- <phase> [knob=value ...]
# Trailing knob=value arguments try a setting without editing the fight, e.g. bomb_spacing=88.

const FIGHT := "res://Scenes/Bosses/MasonBossFightScene.tscn"
const PLAYER_PATH := "Arena/MainPlayer/CharacterBody2D"
const BOSS_PATH := "Arena/MasonScene/MasonCharacterBody"

# verify_mason_tuning's standing area and player box, on a grid fine enough to read a gap against them.
const STAND_AREA := Rect2(117, 132, 1686, 816)
const PLAYER_HALF := Vector2(12, 27)
const PLAYER_SPEED := 600.0
const GRID := 12.0
const BLAST_RADIUS := 60.0
const SAMPLE_EVERY := 3

var phase := 0
var scene: Node
var player: Node
var boss: Node
var sm: Node

var cols := 0
var rows := 0
var clock := 0.0
var frames := 0
var started := false
var done := false

# Every cell a blast ever reached, and every cell a standing player would ever have been caught on.
var threatened := PackedByteArray()
var body_threatened := PackedByteArray()

var samples := 0
var free_total := 0
var worst_free := 1 << 30
var worst_free_at := 0.0
var worst_region := 0
var narrowest := 1 << 30
var narrowest_at := 0.0
var narrowest_x := 0.0
var trapped_frames := 0
var furthest_from_free := 0.0
var furthest_at := 0.0
var worst_walk := 0.0
var worst_walk_at := 0.0
var peak_bombs := 0
var bombs_seen := {}
var walked := 0.0


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() > 0 and not "=" in args[0]:
		phase = int(args[0])
	cols = int(STAND_AREA.size.x / GRID) + 1
	rows = int(STAND_AREA.size.y / GRID) + 1
	threatened.resize(cols * rows)
	body_threatened.resize(cols * rows)
	scene = load(FIGHT).instantiate()
	root.add_child(scene)
	current_scene = scene
	player = scene.get_node(PLAYER_PATH)
	boss = scene.get_node(BOSS_PATH)
	sm = boss.get_node("StateManager")


func _process(delta: float) -> bool:
	if done:
		return true
	frames += 1
	if not started:
		if frames < 4:
			return false
		_launch()
		return false
	clock += delta
	_watch(delta)
	return done


func _launch() -> void:
	started = true
	player.is_talking = false
	player.playerHealth = 9999
	player.is_invincible = true
	boss.phase_two = phase == 1
	_apply_overrides()
	sm.start_cycle()
	print("phase %d: bomb_spacing %.0f  waddle_speed %.0f  wiggle_amp %.0f  fuse_delay %.2f  lines %d" % [
		phase + 1, sm.bomb_spacing[phase], sm.waddle_speed[phase], sm.wiggle_amp,
		sm.fuse_delay[phase], sm.lines_per_cycle[phase]])


func _apply_overrides() -> void:
	for argument in OS.get_cmdline_user_args():
		if not "=" in argument:
			continue
		var parts := argument.split("=")
		var knob := parts[0]
		var value := float(parts[1])
		var current = sm.get(knob)
		if current is Array:
			current[phase] = int(value) if current[0] is int else value
		elif current is int:
			sm.set(knob, int(value))
		else:
			sm.set(knob, value)
		print("  override %s = %s" % [knob, value])


func _bombs() -> Array:
	var out := []
	for node in scene.get_tree().get_nodes_in_group("mason_hazard"):
		if node.has_method("arm"):
			out.append(node)
	return out


func _watch(delta: float) -> void:
	var bombs := _bombs()
	peak_bombs = maxi(peak_bombs, bombs.size())
	for bomb in bombs:
		if not bombs_seen.has(bomb.get_instance_id()):
			bombs_seen[bomb.get_instance_id()] = bomb.global_position
	var point_free := PackedByteArray()
	var body_free := PackedByteArray()
	point_free.resize(cols * rows)
	body_free.resize(cols * rows)
	point_free.fill(1)
	body_free.fill(1)
	for bomb in bombs:
		_stamp(bomb.global_position, point_free, body_free)
	_move_player(body_free, delta)
	if frames % SAMPLE_EVERY == 0:
		_sample(point_free, body_free)
	if clock > 60.0 or (sm.lines_done >= sm.lines_per_cycle[phase] and bombs.is_empty() and clock > 1.0):
		_report()
		done = true


# Marks every cell this bomb's blast reaches, in the two masks and in the cycle's running union: the
# point mask is the floor the blast covers, the body mask the spots a 24x54 player is caught standing on.
func _stamp(at: Vector2, point_free: PackedByteArray, body_free: PackedByteArray) -> void:
	var low := _cell(at - Vector2(BLAST_RADIUS, BLAST_RADIUS) - PLAYER_HALF)
	var high := _cell(at + Vector2(BLAST_RADIUS, BLAST_RADIUS) + PLAYER_HALF)
	for i in range(low.x, high.x + 1):
		for j in range(low.y, high.y + 1):
			var spot := _world(i, j)
			var index := j * cols + i
			if spot.distance_to(at) < BLAST_RADIUS:
				point_free[index] = 0
				threatened[index] = 1
			if at.distance_to(at.clamp(spot - PLAYER_HALF, spot + PLAYER_HALF)) < BLAST_RADIUS:
				body_free[index] = 0
				body_threatened[index] = 1


func _cell(at: Vector2) -> Vector2i:
	return Vector2i(
		clampi(int(floor((at.x - STAND_AREA.position.x) / GRID)), 0, cols - 1),
		clampi(int(floor((at.y - STAND_AREA.position.y) / GRID)), 0, rows - 1))


func _world(i: int, j: int) -> Vector2:
	return STAND_AREA.position + Vector2(i, j) * GRID


# Walks to the nearest spot it could stand on, and stays put while it is standing on one.
func _move_player(body_free: PackedByteArray, delta: float) -> void:
	player.velocity = Vector2.ZERO
	var here := _cell(player.global_position)
	if body_free[here.y * cols + here.x] == 1:
		return
	var target := _nearest_free(body_free, player.global_position)
	if target == Vector2.INF:
		trapped_frames += 1
		return
	var step: float = PLAYER_SPEED * delta
	var to: Vector2 = target - player.global_position
	var moved: Vector2 = to if to.length() <= step else to.normalized() * step
	player.global_position += moved
	walked += moved.length()


func _nearest_free(body_free: PackedByteArray, from: Vector2) -> Vector2:
	var best := Vector2.INF
	var best_distance := INF
	for j in rows:
		for i in cols:
			if body_free[j * cols + i] == 0:
				continue
			var spot := _world(i, j)
			var distance := from.distance_squared_to(spot)
			if distance < best_distance:
				best_distance = distance
				best = spot
	return best


func _sample(point_free: PackedByteArray, body_free: PackedByteArray) -> void:
	samples += 1
	var free := _count(body_free)
	free_total += free
	if free < worst_free:
		worst_free = free
		worst_free_at = clock
		worst_region = _largest_region(body_free)
	# The tightest place to cross the arena: the tallest unbroken run of open floor in the column
	# where that run is shortest. Measured between the outer open cells, so it reads a grid step low.
	var tightest := 1 << 30
	var tightest_x := 0.0
	for i in cols:
		var longest := 0
		var run := 0
		for j in rows:
			run = run + 1 if point_free[j * cols + i] == 1 else 0
			longest = maxi(longest, run)
		if longest < tightest:
			tightest = longest
			tightest_x = _world(i, 0).x
	if tightest < narrowest:
		narrowest = tightest
		narrowest_at = clock
		narrowest_x = tightest_x
	var nearest := INF
	for j in rows:
		for i in cols:
			if body_free[j * cols + i] == 1:
				nearest = minf(nearest, player.global_position.distance_to(_world(i, j)))
	if nearest < INF and nearest > furthest_from_free:
		furthest_from_free = nearest
		furthest_at = clock
	var walk := _furthest_walk(body_free)
	if walk > worst_walk:
		worst_walk = walk
		worst_walk_at = clock


# The longest walk to safety from anywhere on the mat: a flood out of every open cell at once, so the
# answer holds wherever the player was caught. Stepped along the grid, so it reads a diagonal long.
func _furthest_walk(body_free: PackedByteArray) -> float:
	var steps := PackedInt32Array()
	steps.resize(cols * rows)
	steps.fill(-1)
	var queue : Array[int] = []
	for index in cols * rows:
		if body_free[index] == 1:
			steps[index] = 0
			queue.append(index)
	if queue.is_empty():
		return INF
	var head := 0
	var furthest := 0
	while head < queue.size():
		var index: int = queue[head]
		head += 1
		var i: int = index % cols
		var j: int = index / cols
		furthest = maxi(furthest, steps[index])
		for step: Vector2i in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
			var x: int = i + step.x
			var y: int = j + step.y
			if x < 0 or y < 0 or x >= cols or y >= rows:
				continue
			var next: int = y * cols + x
			if steps[next] >= 0:
				continue
			steps[next] = steps[index] + 1
			queue.append(next)
	return furthest * GRID


func _largest_region(body_free: PackedByteArray) -> int:
	var seen := {}
	var best := 0
	for j in rows:
		for i in cols:
			var cell := Vector2i(i, j)
			if body_free[j * cols + i] == 0 or seen.has(cell):
				continue
			var size := 0
			var stack : Array[Vector2i] = [cell]
			seen[cell] = true
			while not stack.is_empty():
				var at: Vector2i = stack.pop_back()
				size += 1
				for step: Vector2i in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
					var next: Vector2i = at + step
					if next.x < 0 or next.y < 0 or next.x >= cols or next.y >= rows:
						continue
					if body_free[next.y * cols + next.x] == 0 or seen.has(next):
						continue
					seen[next] = true
					stack.append(next)
			best = maxi(best, size)
	return best


func _count(mask: PackedByteArray) -> int:
	var total := 0
	for value in mask:
		total += value
	return total


func _report() -> void:
	var cells := cols * rows
	print("  %.1f s, %d bombs over %d lines, peak %d on the mat at once, the player walked %.0f px" % [
		clock, bombs_seen.size(), sm.lines_done, peak_bombs, walked])
	print("  blast coverage of the standing area: %.0f%% of the floor, %.0f%% of the spots a player could stand on" % [
		100.0 * _count(threatened) / cells, 100.0 * _count(body_threatened) / cells])
	print("  free standing cells (%.0f px grid): %d of %d at worst (t %.2f), biggest open patch %d cells (%.0f%%); %.0f%% free on average" % [
		GRID, worst_free, cells, worst_free_at, worst_region, 100.0 * worst_region / cells,
		100.0 * free_total / maxi(samples * cells, 1)])
	print("  narrowest crossing: %.0f px of open floor at x %.0f (t %.2f), against a %.0fx%.0f px body" % [
		maxf((narrowest - 1) * GRID, 0.0), narrowest_x, narrowest_at, PLAYER_HALF.x * 2, PLAYER_HALF.y * 2])
	print("  furthest the player was ever from a spot it could stand on: %.0f px at t %.2f; no spot at all on %d frames" % [
		furthest_from_free, furthest_at, trapped_frames])
	print("  longest walk to safety from anywhere on the mat: %.0f px (t %.2f), %.2f s at %.0f px/s" % [
		worst_walk, worst_walk_at, worst_walk / PLAYER_SPEED, PLAYER_SPEED])
