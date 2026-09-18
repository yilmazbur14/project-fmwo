extends SceneTree

# Headless checks on Mason's retuned attacks. No window needed:
#   Godot.exe --headless --fixed-fps 60 --script res://art_source/mason_tuning/verify_mason_tuning.gd -- <mode> <phase>
# Modes: poo (density, pacing and free space of the bomb lines), reach (can a player in the far
# corner make the start of a line before its first bomb goes off), carter (call-in geometry and
# cadence), nuggets (shower density and free space), gaps (what nothing can reach, on paper).

const FIGHT := "res://Scenes/Bosses/MasonBossFightScene.tscn"
const PLAYER_PATH := "Arena/MainPlayer/CharacterBody2D"
const BOSS_PATH := "Arena/MasonScene/MasonCharacterBody"

# Where the player's body can stand: the wall shapes, pulled in by their 24x54 box.
const STAND_AREA := Rect2(117, 132, 1686, 816)
const PLAYER_HALF := Vector2(12, 27)
const PLAYER_SPEED := 600.0
const GRID_STEP := 40.0
const BLAST_RADIUS := 60.0

var mode := "poo"
var phase := 0
var scene: Node
var boss: Node
var sm: Node
var player: Node

var clock := 0.0
var frames := 0
var started := false
var done := false

# Per line: when its ring went up, where it starts, when its first bomb dropped, landed and blew.
var lines : Array = []
var lines_laid := 0
var line_start_node: Object = null
var bombs_seen := {}
var peak_bombs := 0
var covered := {}
var worst_free := 1 << 30
var worst_free_at := 0.0
var worst_region := 0
var samples := 0
var free_total := 0
var furthest_from_free := 0.0
var furthest_at := 0.0

# reach mode
var run_from := Vector2.ZERO
var run_target := Vector2.ZERO
var running := false
var run_started := 0.0
var arrived := -1.0
var health_at_start := 0
var runs : Array = []

# carter mode
var carter: Node = null
var carter_reported := false
var drop_marks : Array[float] = []
var drop_lands : Array[float] = []
var marker_up := false
var hitbox_on := false

# nugget mode
var nuggets_seen := {}
var peak_nuggets := 0

# soak mode
var states_seen := {}
var peak_rings := 0


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() > 0:
		mode = args[0]
	if args.size() > 1:
		phase = int(args[1])
	scene = load(FIGHT).instantiate()
	root.add_child(scene)
	current_scene = scene
	player = scene.get_node(PLAYER_PATH)
	boss = scene.get_node(BOSS_PATH)
	sm = boss.get_node("StateManager")
	if mode == "gaps":
		_report_gaps()
		done = true


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
	# Only the run to a line's start is meant to be taken on the chin; everything else is measured
	# with the player out of the way of the hit-stop a hit would bring.
	player.is_invincible = mode != "reach"
	health_at_start = player.playerHealth
	boss.phase_two = phase == 1
	_apply_overrides()
	sm.start_cycle()
	if mode == "carter":
		sm.on_child_transition(sm.current_state, "CallCarter")
	elif mode == "nuggets":
		sm.on_child_transition(sm.current_state, "NuggetShower")
	print("mode %s, phase %d" % [mode, phase + 1])
	if mode == "poo" or mode == "reach":
		print("  bomb_spacing %.0f  waddle_speed %.0f  fuse_delay %.2f  detonate_interval %.2f  lines %d" % [
			sm.bomb_spacing[phase], sm.waddle_speed[phase], sm.fuse_delay[phase],
			sm.detonate_interval[phase], sm.lines_per_cycle[phase]])


# Trailing knob=value arguments try a setting without editing the fight, e.g. fuse_delay=0.9. The
# per-phase ones are set on the phase being run.
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


func _watch(delta: float) -> void:
	var hazards := _hazards()
	_track_lines(hazards)
	_track_bombs(hazards)
	if mode == "carter":
		_track_carter(hazards)
	if mode == "nuggets" or mode == "soak":
		_track_nuggets(hazards)
	if mode == "reach":
		_run_to_start(delta)
	if frames % 6 == 0:
		_sample_free_space(hazards)
	if _finished(hazards):
		_report()
		done = true


func _finished(hazards: Dictionary) -> bool:
	if clock > 60.0:
		return true
	var state: String = sm.current_state.name
	match mode:
		"poo", "reach":
			return lines.size() >= sm.lines_per_cycle[phase] and state != "PooSquat" and state != "Waddle" \
				and hazards.bombs.is_empty()
		"carter":
			return carter_reported and not is_instance_valid(carter)
		"nuggets":
			return peak_nuggets > 0 and state != "NuggetShower"
		"soak":
			states_seen[state] = states_seen.get(state, 0) + 1
			peak_rings = maxi(peak_rings, hazards.rings.size())
			return false
		"defeat":
			# Beaten in the middle of a line: everything he has sent out, the start ring included,
			# has to go with him.
			if clock > 3.0 and not boss.defeated:
				boss.take_finisher(boss.boss_health)
			if clock > 4.0:
				print("  beaten mid-line: %d bombs, %d rings, %d nuggets left over" % [
					hazards.bombs.size(), hazards.rings.size(), hazards.nuggets.size()])
				return true
			return false
	return false


func _hazards() -> Dictionary:
	var out := {"bombs": [], "nuggets": [], "drops": [], "rings": []}
	for node in scene.get_tree().get_nodes_in_group("mason_hazard"):
		if node.has_method("arm"):
			out.bombs.append(node)
		elif node.has_method("drop"):
			out.nuggets.append(node)
		elif node.has_method("begin"):
			out.drops.append(node)
		elif node.has_method("show_path"):
			out.rings.append(node)
	return out


func _track_lines(hazards: Dictionary) -> void:
	var ring = sm.line_start
	if not is_instance_valid(ring) or ring == line_start_node:
		return
	line_start_node = ring
	lines.append({
		"ring_up": clock,
		"origin": ring.global_position,
		"preview": ring.path_length,
		"first_drop": -1.0,
		"laid": -1.0,
		"first_blast": -1.0,
		"bombs": 0,
		"spacing_min": 1.0e9,
		"last_at": Vector2.INF,
	})
	if mode == "reach":
		_start_run(ring.global_position)


func _track_bombs(hazards: Dictionary) -> void:
	peak_bombs = maxi(peak_bombs, hazards.bombs.size())
	if lines.is_empty():
		return
	for bomb in hazards.bombs:
		var id: int = bomb.get_instance_id()
		if not bombs_seen.has(id):
			var index := lines.size() - 1
			bombs_seen[id] = {"line": index, "at": bomb.global_position, "blew": false}
			_mark_covered(bomb.global_position)
			var owner_line: Dictionary = lines[index]
			if owner_line.first_drop < 0.0:
				owner_line.first_drop = clock
			owner_line.bombs += 1
			if owner_line.last_at != Vector2.INF:
				owner_line.spacing_min = minf(owner_line.spacing_min, owner_line.last_at.distance_to(bomb.global_position))
			owner_line.last_at = bomb.global_position
		if bomb.animation_player.current_animation == "explode" and not bombs_seen[id].blew:
			bombs_seen[id].blew = true
			var of_line: int = bombs_seen[id].line
			if lines[of_line].first_blast < 0.0:
				lines[of_line].first_blast = clock
	# finish_line arms a line and starts the next one in the same frame, so the moment a line is
	# laid is read off the counter rather than off the state.
	if sm.lines_done > lines_laid:
		lines_laid = sm.lines_done
		if lines_laid - 1 < lines.size():
			lines[lines_laid - 1].laid = clock


func _track_carter(hazards: Dictionary) -> void:
	if hazards.drops.is_empty():
		return
	carter = hazards.drops[0]
	if not carter_reported:
		carter_reported = true
		var hit: Vector2 = carter.hit_size()
		var bounds: Rect2 = carter.landing_bounds(carter.ROPES if "ROPES" in carter else Rect2(113, 114, 1692, 853))
		print("  drops %d  telegraph %.2f  dive %.2f  landed %.2f  sit_up %.2f  leap %.2f  gap %.2f" % [
			sm.elbow_drops[phase], sm.elbow_telegraph[phase], sm.elbow_dive[phase], carter.landed_time,
			sm.elbow_sit_up[phase], sm.elbow_leap_out[phase], sm.elbow_gap[phase]])
		print("  hit_scale %.2f  hit oval %.0fx%.0f px  marker art scale %.2f  hit area %.0f px2" % [
			carter.hit_scale, hit.x, hit.y, carter.target_sprite.scale.x, PI * hit.x * hit.y / 4.0])
		print("  landing bounds x %.0f-%.0f y %.0f-%.0f -> oval reaches x %.0f-%.0f y %.0f-%.0f" % [
			bounds.position.x, bounds.end.x, bounds.position.y, bounds.end.y,
			bounds.position.x - hit.x / 2.0, bounds.end.x + hit.x / 2.0,
			bounds.position.y - hit.y / 2.0, bounds.end.y + hit.y / 2.0])
	var showing: bool = carter.target_sprite.visible
	if showing and not marker_up:
		drop_marks.append(clock)
	marker_up = showing
	var live: bool = not carter.hitbox_shape.disabled
	if live and not hitbox_on:
		drop_lands.append(clock)
	hitbox_on = live


func _track_nuggets(hazards: Dictionary) -> void:
	peak_nuggets = maxi(peak_nuggets, hazards.nuggets.size())
	for nugget in hazards.nuggets:
		var id: int = nugget.get_instance_id()
		if not nuggets_seen.has(id):
			nuggets_seen[id] = nugget.global_position


# The far corner of the arena, then straight at the ring the way a player would hold two keys.
func _start_run(target: Vector2) -> void:
	run_target = target
	var corner := Vector2(
		STAND_AREA.position.x if target.x > STAND_AREA.get_center().x else STAND_AREA.end.x,
		STAND_AREA.position.y if target.y > STAND_AREA.get_center().y else STAND_AREA.end.y)
	run_from = corner
	player.global_position = corner
	running = true
	run_started = clock
	arrived = -1.0
	health_at_start = player.playerHealth
	runs.append({"from": corner, "to": target, "took": -1.0, "hits": 0})


func _run_to_start(delta: float) -> void:
	if not running:
		return
	var to: Vector2 = run_target - player.global_position
	var step := PLAYER_SPEED * delta
	player.global_position += Vector2(clampf(to.x, -step, step), clampf(to.y, -step, step))
	if player.global_position.distance_to(run_target) < 8.0 and arrived < 0.0:
		arrived = clock - run_started
		running = false
		runs[runs.size() - 1].took = arrived
		runs[runs.size() - 1].hits = health_at_start - player.playerHealth


func _mark_covered(at: Vector2) -> void:
	var x := STAND_AREA.position.x
	while x <= STAND_AREA.end.x:
		var y := STAND_AREA.position.y
		while y <= STAND_AREA.end.y:
			if Vector2(x, y).distance_to(at) <= BLAST_RADIUS:
				covered[Vector2i(int(x), int(y))] = true
			y += GRID_STEP
		x += GRID_STEP


# Every spot a standing player would not be caught in, right now.
func _sample_free_space(hazards: Dictionary) -> void:
	var free : Array[Vector2i] = []
	var cells := {}
	var x := STAND_AREA.position.x
	while x <= STAND_AREA.end.x:
		var y := STAND_AREA.position.y
		while y <= STAND_AREA.end.y:
			var spot := Vector2(x, y)
			if _is_free(spot, hazards):
				var cell := Vector2i(int(x / GRID_STEP), int(y / GRID_STEP))
				free.append(cell)
				cells[cell] = true
			y += GRID_STEP
		x += GRID_STEP
	samples += 1
	free_total += free.size()
	if free.size() < worst_free:
		worst_free = free.size()
		worst_free_at = clock
		worst_region = _largest_region(cells)
	# How far the player would have to go to be standing somewhere safe, wherever they are.
	var nearest := 1.0e9
	for cell: Vector2i in cells:
		nearest = minf(nearest, player.global_position.distance_to(Vector2(cell) * GRID_STEP))
	if nearest > furthest_from_free:
		furthest_from_free = nearest
		furthest_at = clock


func _is_free(spot: Vector2, hazards: Dictionary) -> bool:
	for bomb in hazards.bombs:
		if spot.distance_to(bomb.global_position) < BLAST_RADIUS + PLAYER_HALF.x:
			return false
	for nugget in hazards.nuggets:
		if _in_oval(spot, nugget.global_position, nugget.HIT_SIZE / 2.0 + PLAYER_HALF):
			return false
	for drop in hazards.drops:
		if drop.target_sprite.visible or not drop.hitbox_shape.disabled:
			if _in_oval(spot, drop.global_position, drop.hit_size() / 2.0 + PLAYER_HALF):
				return false
	return true


func _in_oval(spot: Vector2, at: Vector2, semi: Vector2) -> bool:
	return ((spot - at) / semi).length() < 1.0


func _largest_region(cells: Dictionary) -> int:
	var seen := {}
	var best := 0
	for cell: Vector2i in cells:
		if seen.has(cell):
			continue
		var size := 0
		var stack : Array[Vector2i] = [cell]
		seen[cell] = true
		while not stack.is_empty():
			var at: Vector2i = stack.pop_back()
			size += 1
			for step: Vector2i in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
				var next: Vector2i = at + step
				if cells.has(next) and not seen.has(next):
					seen[next] = true
					stack.append(next)
		best = maxi(best, size)
	return best


func _grid_cells() -> int:
	return int(STAND_AREA.size.x / GRID_STEP + 1) * int(STAND_AREA.size.y / GRID_STEP + 1)


func _report() -> void:
	match mode:
		"poo":
			var total := 0
			for i in lines.size():
				var line: Dictionary = lines[i]
				total += int(line.bombs)
				print("  line %d: %d bombs, closest pair %.0f px, ring up at %.2f, first bomb %.2f, laid %.2f, first blast %.2f" % [
					i + 1, line.bombs, line.spacing_min, line.ring_up, line.first_drop, line.laid, line.first_blast])
				print("          laying took %.2f s, ring to first blast %.2f s, preview %.0f px" % [
					line.laid - line.ring_up, line.first_blast - line.ring_up, line.preview])
			print("  %d bombs over %d lines, peak %d on the mat at once" % [total, lines.size(), peak_bombs])
			print("  blast coverage of the standing area: %.0f%%" % [100.0 * covered.size() / _grid_cells()])
			_print_free()
		"reach":
			for i in lines.size():
				var line: Dictionary = lines[i]
				var lead: float = line.first_blast - line.ring_up
				var run: Dictionary = runs[i] if i < runs.size() else {"from": Vector2.ZERO, "took": -1.0, "hits": 0}
				print("  line %d: start (%.0f, %.0f), ring to its blast %.2f s; far corner (%.0f, %.0f) run %.2f s, %d hits on the way, %.2f s to spare" % [
					i + 1, line.origin.x, line.origin.y, lead, run.from.x, run.from.y, run.took, run.hits, lead - run.took])
			print("  %d bombs over %d lines, peak %d on the mat at once" % [bombs_seen.size(), lines.size(), peak_bombs])
			print("  blast coverage of the standing area: %.0f%%" % [100.0 * covered.size() / _grid_cells()])
			_print_free()
		"carter":
			var cadence := 0.0
			for i in range(1, drop_marks.size()):
				cadence += drop_marks[i] - drop_marks[i - 1]
			if drop_marks.size() > 1:
				cadence /= drop_marks.size() - 1
			var warning := 0.0
			for i in mini(drop_marks.size(), drop_lands.size()):
				warning += drop_lands[i] - drop_marks[i]
			if drop_lands.size() > 0:
				warning /= drop_lands.size()
			print("  %d drops, one every %.2f s, %.2f s of marker before each hit" % [
				drop_marks.size(), cadence, warning])
			_print_free()
		"nuggets":
			print("  %d nuggets, peak %d in the sky at once" % [nuggets_seen.size(), peak_nuggets])
			_print_free()
		"soak":
			print("  %.0f s of fight, %d lines, %d bombs, %d nuggets, peak %d start rings at once" % [
				clock, lines.size(), bombs_seen.size(), nuggets_seen.size(), peak_rings])
			print("  frames spent per state: %s" % [states_seen])
			_print_free()


func _print_free() -> void:
	print("  free standing cells (%.0f px grid): %d of %d at worst (t %.2f), biggest open patch %d cells; %.0f%% free on average" % [
		GRID_STEP, worst_free, _grid_cells(), worst_free_at, worst_region, 100.0 * free_total / maxi(samples * _grid_cells(), 1)])
	print("  furthest the player was ever from a safe spot: %.0f px (t %.2f)" % [furthest_from_free, furthest_at])


# What each attack can never touch, from the bounds alone.
func _report_gaps() -> void:
	var nugget_hit: Vector2 = load("res://Scripts/NuggetMeteorScript.gd").HIT_SIZE
	var bomb_area: Rect2 = sm.BOMB_AREA
	var nugget_reach := bomb_area.grow_individual(nugget_hit.x / 2.0, nugget_hit.y / 2.0, nugget_hit.x / 2.0, nugget_hit.y / 2.0)
	var blast_reach := bomb_area.grow(BLAST_RADIUS)
	var drop: Node = load("res://Scenes/Bosses/CarterElbowDropScene.tscn").instantiate()
	scene.add_child(drop)
	drop.hit_scale = sm.elbow_hit_scale
	var hit: Vector2 = drop.hit_size()
	var elbow_bounds: Rect2 = drop.landing_bounds(Rect2(113, 114, 1692, 853))
	var elbow_reach := elbow_bounds.grow_individual(hit.x / 2.0, hit.y / 2.0, hit.x / 2.0, hit.y / 2.0)
	drop.queue_free()
	print("standing area x %.0f-%.0f y %.0f-%.0f (player box %.0fx%.0f)" % [
		STAND_AREA.position.x, STAND_AREA.end.x, STAND_AREA.position.y, STAND_AREA.end.y,
		PLAYER_HALF.x * 2, PLAYER_HALF.y * 2])
	for named: Array in [["poo blast", blast_reach], ["nugget", nugget_reach], ["elbow drop", elbow_reach]]:
		var reach: Rect2 = named[1]
		print("%-11s reaches x %.0f-%.0f y %.0f-%.0f -> untouched: left %.0f, right %.0f, top %.0f, bottom %.0f px%s" % [
			named[0], reach.position.x, reach.end.x, reach.position.y, reach.end.y,
			maxf(reach.position.x - STAND_AREA.position.x - PLAYER_HALF.x, 0.0),
			maxf(STAND_AREA.end.x - reach.end.x - PLAYER_HALF.x, 0.0),
			maxf(reach.position.y - STAND_AREA.position.y - PLAYER_HALF.y, 0.0),
			maxf(STAND_AREA.end.y - reach.end.y - PLAYER_HALF.y, 0.0),
			"" if named[0] != "elbow drop" else "  (an aimed drop is pushed to the nearest reaching spot)"])
