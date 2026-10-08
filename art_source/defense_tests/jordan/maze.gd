extends RefCounted

# jordan_maze (coder A): Jordan's attack 1, Greyson + Matt's dark maze (JordanComboMaze, JordanMazeLayout), in the god
# fight, each run on a fresh fight whose rotation opens with the maze. Its route is new every time it starts
# (JordanMazeLayout.generate()); a run here plays the drawn path, a route off a seeded rng, or whatever the fight rolls,
# as each tier says, pinned through JordanComboMaze.pinned_route. --max-fps 60: the payoff's mash is real time. tier=
#   layout   the drawn path (the sketch re-snapped to staging option B's grid) is its table, its walls the wall rule's
#            40; for every block a route may use and every wall one may raise: the player's body inside the floor and the
#            ring, clear of the staging's HUD keep-outs and of the player's HUD as drawn, both through the fight's view,
#            and below Jordan's mask and core; Greyson's meter clear of his face too; at the goal the finisher's reach
#            check against Greyson passes.
#   random   ROUTE_SEEDS routes off seeded rngs, each checked here rule by rule (18 unit steps from the start to the goal,
#            self-avoiding, in the box, off the back glass's row, the corridor never touching itself, no wall on Greyson,
#            Matt, the back glass or the goal's top) and by route_problems(); many distinct routes, every direction
#            used, and the search never falling back to the drawn path.
#   perfect  the drawn path and two seeded routes, answered 0.2 s after each arrow: the soles on each block's centre
#            (±0.5 px) in order, glass on each block left behind, no damage, the meter under full at the goal; then three
#            punches and a three-bar mash take Jordan -3 exactly, and the release is clean.
#   human    the user's pressure (2026-09-28: a 10 s meter and snappier steps). A quick player, answering 0.3 s after
#            each arrow on the drawn path and two seeded routes, reaches Greyson with at least HUMAN_MARGIN of the meter
#            left; a slower one, at 0.4 s on the drawn path and a seeded route, does not: the meter fills first and the
#            beam fires, a heart and a half, Jordan untouched. The goal times either way, the slow one's projected off
#            its own pace.
#   wrong    the drawn path and a seeded route, a wrong press at step 0 and at step 7: half a heart each, back on the
#            same block (±0.5 px), the same arrow live again; presses during the knock count for nothing.
#   idle     the drawn path and a seeded route, no presses: the beam starts as the meter fills (±1 frame), runs from his
#            muzzle into the goal and back down the route to the player's block, and deals exactly a heart and a half;
#            its charge and its trace each take their knob's time (±1 frame), the trace whatever the route's length,
#            and the hit lands as the head reaches the player's block; with V2 on (JordanMazeLayout.BEAM_V2), a
#            hit-stop, the flash and the colour kick as it lands, and every wall along its path lit; Jordan untouched;
#            the next attack is attack 2. The slow run in `human` checks the beam the same way on a short path.
#   locks    the fight's own route: dash, block and punch during an arrow change nothing - stamina, the parry window,
#            the position - and a stick flick answers once.
#   tiers    the fight's own routes: mashes that bank 1, 2 and 3 bars take Jordan -1, -2 and -3.
#   fizzle   the fight's own route: no bar banked, Jordan untouched and a clean wrap.
#   pause    the fight's own route: game-time timings hold through a pause mid-arrow, mid-knock and mid-beam - nothing
#            moves while paused, and the meter, the knock and the beam each take their own time in unpaused steps.
#   death    the fight's own route, at half a heart: a wrong press gives Defeat and a clean release.
#   v1       the switch off: the drawn path's idle run on V1's beam, its beats on V1's knobs and its damage the same.
#   normal   all of them in turn.

const FIGHT := "res://Scenes/Bosses/JordanGodFightScene.tscn"
const DEFEAT := "res://Scenes/Core/DefeatScene.tscn"
const GOD := "Arena/JordanGodScene/God"
const MAZE_SCRIPT := "res://Scripts/States/JordanGod/JordanComboMaze.gd"
const Layout := preload("res://Scripts/JordanMazeLayout.gd")
const GodLayout := preload("res://Scripts/JordanGodLayout.gd")
const FinisherArtLayout := preload("res://Scripts/FinisherArtLayout.gd")
const HitStop := preload("res://Scripts/HitStop.gd")
const TIERS := ["layout", "random", "perfect", "human", "wrong", "idle", "locks", "tiers", "fizzle", "pause", "death", "v1"]
const KEYS := {&"up": KEY_UP, &"right": KEY_RIGHT, &"down": KEY_DOWN, &"left": KEY_LEFT}
const WAYS := {Vector2i(0, 1): &"up", Vector2i(1, 0): &"right", Vector2i(0, -1): &"down", Vector2i(-1, 0): &"left"}
# A wrong press for each arrow.
const WRONG := {&"up": &"left", &"right": &"down", &"down": &"right", &"left": &"up"}
# The drawn path on staging option B's grid, world px: the sketch's up 1, right 2, up 4, left 6, up 2, right 3, with one
# more block up the middle run and one fewer right at the top to reach the goal in 18 steps. Block, soles, arrow.
const TABLE := [
	[Vector2i(0, 0), Vector2(960, 1410), &"up"], [Vector2i(0, 1), Vector2(960, 1350), &"right"],
	[Vector2i(1, 1), Vector2(1056, 1350), &"right"], [Vector2i(2, 1), Vector2(1152, 1350), &"up"],
	[Vector2i(2, 2), Vector2(1152, 1290), &"up"], [Vector2i(2, 3), Vector2(1152, 1230), &"up"],
	[Vector2i(2, 4), Vector2(1152, 1170), &"up"], [Vector2i(2, 5), Vector2(1152, 1110), &"up"],
	[Vector2i(2, 6), Vector2(1152, 1050), &"left"], [Vector2i(1, 6), Vector2(1056, 1050), &"left"],
	[Vector2i(0, 6), Vector2(960, 1050), &"left"], [Vector2i(-1, 6), Vector2(864, 1050), &"left"],
	[Vector2i(-2, 6), Vector2(768, 1050), &"left"], [Vector2i(-3, 6), Vector2(672, 1050), &"left"],
	[Vector2i(-4, 6), Vector2(576, 1050), &"up"], [Vector2i(-4, 7), Vector2(576, 990), &"up"],
	[Vector2i(-4, 8), Vector2(576, 930), &"right"], [Vector2i(-3, 8), Vector2(672, 930), &"right"],
	[Vector2i(-2, 8), Vector2(768, 930), &""],
]
# The wall rule's count on the drawn path.
const DRAWN_WALLS := 40
# The staging's HUD keep-outs in screen px (staging.json's hud_keep_out: the boss bar, the player's bottom-left and
# bottom-right pieces) and the clearance kept from them, screen px too.
const HUD_KEEP_OUT: Array[Rect2] = [Rect2(720, 33, 480, 148), Rect2(10, 842, 406, 229), Rect2(1371, 946, 537, 126)]
const HUD_CLEARANCE := 12.0
# How many seeded routes the random tier checks, and the fewest distinct ones it wants among them.
const ROUTE_SEEDS := 600
const MIN_DISTINCT := 200
# The seeded routes the fight tiers play besides the drawn path.
const PLAY_SEEDS := [101, 202]
# How long the bot takes to answer an arrow, in frames at 60 fps: 0.2 s, a quick player's 0.3 s and a slower one's 0.4 s.
# Each press lands a frame after it, on the next input flush.
const PERFECT_REACTION := 12
const HUMAN_REACTION := 18
const SLOW_REACTION := 24
# What a quick player has in hand at the goal, seconds of the meter.
const HUMAN_MARGIN := 1.0
# A press every this many frames banks 1, 2 or 3 bars (verify_defense's TIER_PASS_FRAMES).
const MASH_EVERY := {1: 10, 2: 7, 3: 6}
# The payoff's punches, this many frames apart: over the punch-out's 0.10 s floor.
const PUNCH_GAP := 9
# The longest a maze may take to reach its goal or its wrap, in frames.
const MAZE_FRAMES := 60 * 40
# How long each pause holds, in frames.
const PAUSE_FRAMES := 30


static func run(t) -> void:
	var tiers: Array = TIERS if t.tier == "normal" else [t.tier]
	var beam_v2: bool = Layout.BEAM_V2
	for tier in tiers:
		t.log_p("-- jordan_maze %s" % tier)
		match tier:
			"layout":
				await tier_layout(t)
			"random":
				tier_random(t)
			"perfect":
				await tier_perfect(t)
			"human":
				await tier_human(t)
			"wrong":
				await tier_wrong(t)
			"idle":
				await tier_idle(t)
			"locks":
				await tier_locks(t)
			"tiers":
				await tier_tiers(t)
			"fizzle":
				await tier_fizzle(t)
			"pause":
				await tier_pause(t)
			"death":
				await tier_death(t)
			"v1":
				await tier_v1(t)
			_:
				t.check(false, "unknown tier %s" % tier)
		pin([])
		Layout.BEAM_V2 = beam_v2


#THE ROUTES

# Every maze from here plays `route`, or its own for none.
static func pin(route: Array) -> void:
	var typed: Array[Vector2i] = []
	for cell in route:
		typed.append(cell)
	load(MAZE_SCRIPT).pinned_route = typed


static func seeded_route(seed_value: int) -> Array[Vector2i]:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	return Layout.generate(rng)


# The routes a fight tier plays: the drawn path, then the seeded ones.
static func played_routes() -> Array:
	var routes := [["the drawn path", Layout.DRAWN_PATH]]
	for seed_value in PLAY_SEEDS:
		routes.append(["seed %d" % seed_value, seeded_route(seed_value)])
	return routes


# The walls a route raises, worked out here rather than asked of the layout: every block touching it that isn't on it,
# but Greyson's and the back glass.
static func walls_of(route: Array) -> Array:
	var out := []
	for cell: Vector2i in route:
		for dr in [-1, 0, 1]:
			for dc in [-1, 0, 1]:
				var next: Vector2i = cell + Vector2i(dc, dr)
				if not route.has(next) and next != Layout.GREYSON_CELL and next != Layout.BACK_GLASS and not out.has(next):
					out.append(next)
	return out


# Each rule a route must keep, checked here on its own terms: the broken ones, in words.
static func broken_rules(route: Array) -> Array:
	var broken := []
	if route.size() != Layout.ROUTE_STEPS + 1:
		broken.append("%d steps" % (route.size() - 1))
		return broken
	if route[0] != Layout.START or route[-1] != Layout.GOAL:
		broken.append("ends")
	for i in range(1, route.size()):
		if not WAYS.has(route[i] - route[i - 1]):
			broken.append("step %d" % i)
	for i in route.size():
		var cell: Vector2i = route[i]
		if route.count(cell) > 1:
			broken.append("revisits %s" % cell)
		if cell.x < Layout.ROUTE_COLUMNS.x or cell.x > Layout.ROUTE_COLUMNS.y or cell.y < Layout.ROUTE_ROWS.x or cell.y > Layout.ROUTE_ROWS.y:
			broken.append("leaves the box at %s" % cell)
		if cell.y <= Layout.BACK_GLASS.y:
			broken.append("steps onto the back glass's row at %s" % cell)
		for j in range(i + 2, route.size()):
			var other: Vector2i = route[j]
			var dx := absi(cell.x - other.x)
			var dy := absi(cell.y - other.y)
			if dx + dy == 1:
				broken.append("blocks %d and %d side by side" % [i, j])
			elif dx == 1 and dy == 1 and j > i + 2 and not Layout.DIAGONAL_CONTACT:
				broken.append("blocks %d and %d corner to corner" % [i, j])
	for wall in walls_of(route):
		if wall == Layout.GREYSON_CELL or wall == Layout.BACK_GLASS or Layout.NO_WALL.has(wall):
			broken.append("a wall on %s" % wall)
	return broken


#THE FIGHT

# A fresh god fight with the player at `health`, and its maze once the rotation has opened it.
static func open_maze(t, health := 6) -> Node:
	await t.open_scene(FIGHT)
	await t.wait(3)
	t.player = t.current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
	t.defense = t.player.get_node("Defense")
	t.player.playerHealth = health
	var maze := maze_of(t)
	var began: bool = maze != null and await t.wait_until(func(): return maze.run_id > 0, 60 * 8)
	t.check(began, "the rotation opens with the maze")
	if began:
		t.log_p("route %s" % [maze.route])
	return maze


static func god(t) -> Node:
	return t.current_scene.get_node(GOD)


static func maze_of(t) -> Node:
	for node in t.current_scene.find_children("*", "Node", true, false):
		var script: Script = node.get_script()
		if script != null and script.resource_path == MAZE_SCRIPT:
			return node
	return null


static func soles(t) -> Vector2:
	return t.player.global_position + Vector2(0, Layout.SOLES_OVER_ORIGIN)


static func is_current(maze: Node) -> bool:
	return maze.state_machine.current_state == maze


# Drives the maze from its first arrow until it hands over, answering each arrow `delay` frames after it goes live:
# the arrow, or at the steps in `wrong_at` a wrong direction the first time. With `delay` < 0 it never answers, and
# from step `stop_at` on it stops. `each_frame` is called every physics step with the maze. What it saw.
static func drive(t, maze: Node, delay: int, wrong_at: Array = [], each_frame := Callable(), stop_at := -1) -> Dictionary:
	var seen := {"landed": [], "backs": [], "hurt": [], "lives": [], "answers": [], "health": [t.player.playerHealth],
		"goal_meter": -1.0, "wronged": {}}
	var answered := 0
	var due := -1
	var last_step: int = maze.step
	var last_beat: int = maze.beat
	var start: int = Engine.get_physics_frames()
	while Engine.get_physics_frames() - start < MAZE_FRAMES:
		await t.physics_frame
		if each_frame.is_valid():
			each_frame.call(maze)
		if t.paused:
			continue
		if t.player.playerHealth != seen.health[-1]:
			seen.health.append(t.player.playerHealth)
			seen.hurt.append({"step": maze.step, "beat": maze.Beat.keys()[maze.beat]})
		if maze.step != last_step:
			last_step = maze.step
			seen.landed.append({"step": maze.step, "soles": soles(t)})
		if maze.beat != last_beat:
			if last_beat == maze.Beat.BACK:
				seen.backs.append({"step": maze.step, "soles": soles(t)})
			# The meter as the press landed: both clocks have run on together since it, but for the goal's press, which
			# stops the meter.
			if maze.beat == maze.Beat.ANSWERED:
				seen.answers.append(maze.meter_clock if maze.reached else maze.meter_clock - maze.beat_clock)
			last_beat = maze.beat
		if maze.live_log.size() > answered and due < 0:
			seen.lives.append(maze.live_log[answered])
			answered += 1
			if delay >= 0 and (stop_at < 0 or maze.step < stop_at):
				due = Engine.get_physics_frames() + delay
		if due >= 0 and Engine.get_physics_frames() >= due and maze.beat == maze.Beat.LIVE:
			due = -1
			var arrow: StringName = Layout.arrow(maze.route, maze.step)
			var direction := arrow
			if wrong_at.has(maze.step) and not seen.wronged.has(maze.step):
				seen.wronged[maze.step] = true
				direction = WRONG[arrow]
			t.tap(KEYS[direction])
		if maze.reached and seen.goal_meter < 0.0:
			seen.goal_meter = maze.meter_clock
		if maze.beat == maze.Beat.OFF and (maze.reached or maze.beamed or t.player.playerHealth <= 0):
			break
	return seen


# The payoff's three punches, then a mash that banks `bars` (none for 0): Jordan's health after the wrap.
static func pay_off(t, maze: Node, bars: int) -> Dictionary:
	var finisher: Node = t.player.get_node("Finisher")
	var ready: bool = await t.wait_until(func(): return maze.punching, 120)
	for n in GodLayout.PUNCH_OUT_PRESSES:
		t.tap(KEY_Q)
		await t.wait(PUNCH_GAP)
	var dazed: bool = await t.wait_until(func(): return finisher.phase == t.FINISHER_DAZED and finisher.prompt_visible, 120)
	if bars > 0:
		await t.mash_tiered(MASH_EVERY[bars])
	var wrapped: bool = await t.wait_until(func(): return not is_current(maze), 60 * 12)
	await t.wait(3)
	return {"ready": ready, "dazed": dazed, "wrapped": wrapped, "after": god(t).boss_health,
		"tiers": finisher.juggle_tiers, "bars": maze.bars}


# What a wrap or a release left behind: the lock, the pose, the player's z, anything still lifted, the darkness, the
# HUD, the puppets, the rifts, the hazards, the arrow, the hint, and the maze's own beats.
static func leftovers(t, maze: Node, player_z: int) -> Array:
	var left := []
	if t.player.is_action_locked:
		left.append("locked")
	if t.player.is_posed():
		left.append("posed")
	if t.player.z_index != player_z:
		left.append("player z %d" % t.player.z_index)
	if not maze.lifted.is_empty():
		left.append("lifted %d" % maze.lifted.size())
	var g := god(t)
	if g.darkness.visible and g.darkness.modulate.a > 0.0:
		left.append("dark")
	if not is_equal_approx(g.health_bar.modulate.a, 1.0):
		left.append("HUD alpha %.2f" % g.health_bar.modulate.a)
	if not maze.puppets.is_empty():
		left.append("puppets")
	if not maze.rifts.is_empty():
		left.append("rifts")
	var hazards: Array = t.get_nodes_in_group(GodLayout.HAZARD_GROUP).filter(func(n): return not n.is_queued_for_deletion())
	if not hazards.is_empty():
		left.append("hazards %s" % [hazards.map(func(n): return n.name)])
	if is_instance_valid(maze.arrow_badge):
		left.append("arrow")
	if is_instance_valid(maze.hint_node):
		left.append("hint")
	if maze.beat != maze.Beat.OFF:
		left.append("beat %s" % maze.Beat.keys()[maze.beat])
	return left


#THE TIERS

static func tier_layout(t) -> void:
	var drawn := Layout.DRAWN_PATH
	var path_ok := drawn.size() == TABLE.size()
	for i in TABLE.size():
		var row: Array = TABLE[i]
		path_ok = path_ok and drawn[i] == row[0] and Layout.soles(row[0]) == row[1]
		if i < TABLE.size() - 1:
			path_ok = path_ok and Layout.arrow(drawn, i) == row[2]
	t.check(path_ok and Layout.step_count() == 18, "the drawn path's 19 blocks, soles and 18 arrows are its table")
	var walls := Layout.walls(drawn)
	var expected := walls_of(drawn)
	var same := walls.size() == expected.size() and expected.all(func(c): return walls.has(c))
	t.check(same and walls.size() == DRAWN_WALLS and not walls.any(func(c): return drawn.has(c)),
		"its walls are every off-path neighbour but the goal's top and the back glass: %d, none on it" % walls.size())
	t.check(Layout.route_problems(drawn).is_empty() and broken_rules(drawn).is_empty(),
		"the drawn path keeps every route rule (%s)" % [Layout.route_problems(drawn) + broken_rules(drawn)])
	# Everything any route may use: the box's blocks and the back glass, and every wall around them.
	var blocks: Array[Vector2i] = [Layout.BACK_GLASS]
	var all_walls: Array[Vector2i] = []
	for r in range(Layout.ROUTE_ROWS.x - 1, Layout.ROUTE_ROWS.y + 2):
		for c in range(Layout.ROUTE_COLUMNS.x - 1, Layout.ROUTE_COLUMNS.y + 2):
			var cell := Vector2i(c, r)
			var inside := c >= Layout.ROUTE_COLUMNS.x and c <= Layout.ROUTE_COLUMNS.y and r >= Layout.ROUTE_ROWS.x and r <= Layout.ROUTE_ROWS.y
			if inside:
				blocks.append(cell)
			elif cell != Layout.GREYSON_CELL and cell != Layout.BACK_GLASS and not Layout.NO_WALL.has(cell):
				all_walls.append(cell)
	for cell in blocks:
		if cell != Layout.BACK_GLASS:
			all_walls.append(cell)
	var maze := await open_maze(t)
	var body_rect: Rect2 = t.player._shape_rect(t.player.get_node("CollisionShape2D"))
	var body := Rect2(body_rect.position - t.player.global_position, body_rect.size)
	var outside := []
	for cell in blocks:
		var origin := Layout.body_point(cell)
		if not GodLayout.FLOOR.encloses(Rect2(origin + body.position, body.size)) or not t.player.ring_origins.has_point(origin):
			outside.append(cell)
	t.check(outside.is_empty(), "the player's body inside the floor and the ring on every block a route may use (%d; %s)" % [blocks.size(), outside])
	await t.wait_until(func(): return is_equal_approx(load("res://Scripts/ScreenView.gd").base_zoom, GodLayout.VIEW_ZOOM), 60 * 4)
	var keep_out := []
	for rect: Rect2 in HUD_KEEP_OUT:
		keep_out.append(to_world(t, rect.grow(HUD_CLEARANCE)))
	var hud := []
	for rect: Rect2 in hud_rects(t):
		hud.append(to_world(t, rect))
	var near := []
	var face := []
	var faces := Layout.jordan_face()
	for cell in blocks + all_walls:
		var drawn_rect := Layout.block_rect(cell).grow_individual(0, Layout.PLACEHOLDER_WALL.height, 0, 0)
		if hud_gap(drawn_rect, keep_out) <= 0.0 or hud_gap(drawn_rect, hud) <= 0.0:
			near.append(cell)
		if faces.any(func(f: Rect2) -> bool: return drawn_rect.intersects(f)):
			face.append(cell)
	var widest := Rect2(Layout.block_rect(Layout.BACK_GLASS))
	for cell in blocks + all_walls:
		widest = widest.merge(Layout.block_rect(cell).grow_individual(0, Layout.PLACEHOLDER_WALL.height, 0, 0))
	t.log_p("the keep-outs in world %s; the player's HUD in world %s; the maze at its widest %s" % [keep_out, hud, widest])
	t.check(not hud.is_empty() and near.is_empty(), "every block and wall any route may raise clear of the HUD keep-outs and the player's HUD (%s)" % [near])
	t.check(face.is_empty(), "and below Jordan's mask and core %s (%s)" % [faces, face])
	var meter := Layout.meter_rect(GodLayout.ui_scale())
	t.check(not faces.any(func(f: Rect2) -> bool: return meter.intersects(f)) and hud_gap(meter, keep_out) > 0.0,
		"Greyson's meter %s clear of Jordan's face and the HUD" % [meter])
	await t.wait_until(func(): return maze.greyson() != null, 60 * 4)
	var reach := goal_reach(t, maze.greyson())
	t.check(reach.ok, "at the goal the finisher's reach check against Greyson's hurtbox passes (%s)" % [reach])


static func tier_random(t) -> void:
	var distinct := {}
	var directions := {}
	var fallbacks := 0
	var bad := []
	var longest_usec := 0
	var first_steps := {}
	for seed_value in ROUTE_SEEDS:
		var rng := RandomNumberGenerator.new()
		rng.seed = seed_value
		var began := Time.get_ticks_usec()
		var route := Layout.try_generate(rng)
		longest_usec = maxi(longest_usec, Time.get_ticks_usec() - began)
		if route.is_empty():
			fallbacks += 1
			continue
		var broken := broken_rules(route) + Layout.route_problems(route)
		if not broken.is_empty() and bad.size() < 5:
			bad.append([seed_value, route, broken])
		elif not broken.is_empty():
			bad.append(seed_value)
		distinct[str(route)] = true
		first_steps[WAYS[route[1] - route[0]]] = true
		for i in range(1, route.size()):
			directions[WAYS[route[i] - route[i - 1]]] = true
	t.log_p("%d seeds: %d distinct routes, directions %s, first steps %s, the slowest search %.1f ms, fallbacks %d" % [ROUTE_SEEDS,
		distinct.size(), directions.keys(), first_steps.keys(), longest_usec / 1000.0, fallbacks])
	t.check(bad.is_empty(), "every route keeps every rule (%s)" % [bad])
	t.check(distinct.size() >= MIN_DISTINCT, "many distinct routes: %d of %d" % [distinct.size(), ROUTE_SEEDS])
	t.check(directions.size() == 4, "every direction used (%s)" % [directions.keys()])
	t.check(fallbacks == 0, "the search never falls back to the drawn path (%d)" % fallbacks)
	var pinned := seeded_route(PLAY_SEEDS[0])
	t.check(pinned == seeded_route(PLAY_SEEDS[0]), "a seed replays its route")


# A screen rect in world px, through the fight's view.
static func to_world(t, rect: Rect2) -> Rect2:
	var back: Transform2D = t.root.canvas_transform.affine_inverse()
	return back * rect


# The drawn rects of the player's HUD, as the view has them: only what draws, as verify_defense's carter_hud_rects()
# counts it, so a container laid over the whole view is not a piece.
static func hud_rects(t) -> Array:
	var rects := []
	var layer: Node = t.current_scene.get_node("Arena/MainPlayer/CanvasLayer")
	for item: Node in layer.find_children("*", "", true, false):
		if not item is CanvasItem or not item.is_visible_in_tree():
			continue
		var drawing: bool = item is Sprite2D or item is TextureRect or item is TextureProgressBar or item is ColorRect \
			or item is NinePatchRect or (item is Label and not item.text.is_empty())
		if not drawing:
			continue
		var rect := Rect2()
		if item is Control:
			rect = (item as Control).get_global_rect()
		elif (item as Sprite2D).texture != null:
			rect = (item as Sprite2D).get_global_transform() * (item as Sprite2D).get_rect()
		if rect.has_area():
			rects.append(rect)
	return rects


static func hud_gap(rect: Rect2, hud: Array) -> float:
	var gap := INF
	for piece: Rect2 in hud:
		var dx := maxf(piece.position.x - rect.end.x, rect.position.x - piece.end.x)
		var dy := maxf(piece.position.y - rect.end.y, rect.position.y - piece.end.y)
		gap = minf(gap, maxf(dx, dy))
	return gap


# PlayerFinisher._in_reach() for a player standing on the goal: Greyson's hurtbox grown by the uppercut's reach
# holding their origin or one of the uppercut's fists.
static func goal_reach(t, greyson: Node) -> Dictionary:
	var finisher: Node = t.player.get_node("Finisher")
	var shape: CollisionShape2D = greyson.get_finisher_hurtbox().get_node("CollisionShape2D")
	var box: Rect2 = (shape.global_transform * shape.shape.get_rect()).grow(finisher.uppercut_reach)
	var origin := Layout.body_point(Layout.GOAL)
	var ok := box.has_point(origin)
	var sheet: Dictionary = finisher.sheet()
	for step in sheet.reach_steps:
		ok = ok or box.has_point(origin + FinisherArtLayout.mirrored(sheet.fists[step], false))
	return {"ok": ok, "box": box, "origin": origin}


static func tier_perfect(t) -> void:
	for played in played_routes():
		t.log_p("- %s" % played[0])
		pin(played[1])
		var maze := await open_maze(t)
		var route: Array = maze.route
		var player_z: int = t.player.z_index
		var god_health: int = god(t).boss_health
		var seen := await drive(t, maze, PERFECT_REACTION)
		await t.wait(20)
		var on_centres: bool = seen.landed.size() == Layout.step_count()
		for k in seen.landed.size():
			var landing: Dictionary = seen.landed[k]
			on_centres = on_centres and landing.step == k + 1 and landing.soles.distance_to(Layout.soles(route[k + 1])) <= 0.5
		t.check(route == played[1] and on_centres, "%s: the soles on each block's centre (±0.5 px), in order" % played[0])
		var glassed := []
		for k in Layout.step_count():
			var floor: Node = maze.glass.get(route[k])
			if is_instance_valid(floor) and floor.revealed_count() == 1:
				glassed.append(k)
		t.check(glassed.size() == Layout.step_count(), "%s: glass on each block left behind (%d of %d)" % [played[0], glassed.size(), Layout.step_count()])
		t.check(seen.hurt.is_empty() and maze.wrongs == 0, "%s: no damage (%s)" % [played[0], seen.hurt])
		t.log_p("0.2 s reactions: the goal at %.2f s of the meter, %d cells banked" % [seen.goal_meter, maze.cells])
		t.check(maze.reached and seen.goal_meter < Layout.METER_TIME and maze.cells < Layout.METER_CELLS,
			"%s: the meter under full at the goal (%.2f s, %d cells)" % [played[0], seen.goal_meter, maze.cells])
		var paid := await pay_off(t, maze, 3)
		t.log_p("payoff %s" % [paid])
		t.check(paid.dazed and paid.tiers == 3 and god_health - paid.after == 3,
			"%s: three punches and a three-bar mash, Jordan -3 exactly (%d -> %d)" % [played[0], god_health, paid.after])
		var left := leftovers(t, maze, player_z)
		t.check(paid.wrapped and left.is_empty(), "%s: the release is clean %s" % [played[0], left])


static func tier_human(t) -> void:
	for played in played_routes():
		pin(played[1])
		var maze := await open_maze(t)
		var seen := await drive(t, maze, HUMAN_REACTION)
		var left: float = Layout.METER_TIME - seen.goal_meter
		t.log_p("%s, 0.3 s reactions: the goal at %.2f s of %.1f, %.2f s of the meter left, %d cells banked" % [played[0],
			seen.goal_meter, Layout.METER_TIME, left, maze.cells])
		t.check(maze.reached and left >= HUMAN_MARGIN, "%s: a quick player (0.3 s) reaches Greyson with at least %.1f s of the meter left (%.2f)" % [played[0],
			HUMAN_MARGIN, left])
		await pay_off(t, maze, 1)
	for played in played_routes().slice(0, 2):
		pin(played[1])
		var maze := await open_maze(t)
		var god_health: int = god(t).boss_health
		var marks := {}
		var seen := await drive(t, maze, SLOW_REACTION, [], beam_watch(marks))
		var answers: Array = seen.answers
		var pace: float = (answers[-1] - answers[0]) / (answers.size() - 1) if answers.size() > 1 else 0.0
		var projected: float = answers[0] + (Layout.step_count() - 1) * pace if not answers.is_empty() else 0.0
		t.log_p("%s, 0.4 s reactions: %d of %d arrows answered at %.3f s an arrow as the meter filled; the goal would have come at %.2f s; health %s" % [
			played[0], answers.size(), Layout.step_count(), pace, projected, seen.health])
		t.check(maze.beamed and not maze.reached and answers.size() < Layout.step_count() and projected > Layout.METER_TIME,
			"%s: a slower player (0.4 s) doesn't make it: the meter fills first and the beam fires" % played[0])
		t.check(seen.health == [6, 3] and god(t).boss_health == god_health, "%s: a heart and a half, and Jordan untouched (%s)" % [played[0], seen.health])
		check_beam(t, maze, "%s, at step %d" % [played[0], maze.step], marks)
		await t.wait_until(func(): return not is_current(maze), 60 * 6)


static func tier_wrong(t) -> void:
	for played in played_routes().slice(0, 2):
		t.log_p("- %s" % played[0])
		pin(played[1])
		var maze := await open_maze(t)
		var route: Array = maze.route
		var extra := [0]
		var watch := func(m: Node) -> void:
			if (m.beat == m.Beat.KNOCK or m.beat == m.Beat.GLASS) and m.beat_clock <= 1.5 / 60.0:
				for direction in [&"up", &"right", &"down", &"left"]:
					t.tap(KEYS[direction])
				extra[0] += 4
		var seen := await drive(t, maze, PERFECT_REACTION, [0, 7], watch)
		t.log_p("hurt %s, health %s, backs %s, arrows live at steps %s" % [seen.hurt, seen.health, seen.backs, seen.lives.map(func(l): return l.step)])
		t.check(seen.health == [6, 5, 4] and seen.hurt.map(func(h): return h.step) == [0, 7],
			"%s: half a heart at step 0 and at step 7 (%s)" % [played[0], seen.health])
		var back_ok: bool = seen.backs.size() == 2
		for back: Dictionary in seen.backs:
			back_ok = back_ok and back.soles.distance_to(Layout.soles(route[back.step])) <= 0.5
		t.check(back_ok and seen.backs.map(func(b): return b.step) == [0, 7], "%s: back on the same block each time (±0.5 px)" % played[0])
		var again := [0, 7].all(func(k): return seen.lives.filter(func(l): return l.step == k).size() == 2)
		t.check(again and maze.wrongs == 2, "%s: the same arrow live again after each, and %d presses during the knocks counted for nothing (%d wrong)" % [played[0], extra[0], maze.wrongs])
		t.check(maze.reached, "%s: and on to the goal, at %.2f s of the meter" % [played[0], seen.goal_meter])
		await pay_off(t, maze, 1)


static func tier_idle(t) -> void:
	for played in played_routes().slice(0, 2):
		t.log_p("- %s" % played[0])
		pin(played[1])
		var maze := await open_maze(t)
		var god_health: int = god(t).boss_health
		var marks := {}
		var seen := await drive(t, maze, -1, [], beam_watch(marks))
		var to_full: int = maze.full_frame - maze.first_arrow_frame
		var beam: PackedVector2Array = maze.beam_route
		t.log_p("first arrow f%d, full f%d (+%d), beam f%d, hit f%d; health %s; the beam %s" % [maze.first_arrow_frame,
			maze.full_frame, to_full, maze.beam_frame, maze.beam_hit_frame, seen.health, beam])
		t.check(absi(to_full - roundi(Layout.METER_TIME * 60.0)) <= 1 and maze.beam_frame == maze.full_frame,
			"%s: the beam starts as the meter fills, %.1f s from the first arrow (±1 frame; %d frames)" % [played[0], Layout.METER_TIME, to_full])
		var lift := Vector2(0, -Layout.BEAM_HEIGHT)
		var through_goal: bool = beam.size() >= 3 and beam[1] == Layout.soles(Layout.GOAL) + lift
		var to_player: bool = not beam.is_empty() and beam[beam.size() - 1] == Layout.soles(maze.route[maze.step]) + lift
		var corners_on_route := true
		for k in range(1, beam.size()):
			corners_on_route = corners_on_route and maze.route.any(func(c): return Layout.soles(c) + lift == beam[k])
		t.check(through_goal and to_player and corners_on_route and beam == Layout.beam_points(maze.route, beam[0], maze.step),
			"%s: from his muzzle into the goal and back down the route to the player's block" % played[0])
		t.check(seen.health == [6, 3], "%s: exactly a heart and a half (%s)" % [played[0], seen.health])
		check_beam(t, maze, played[0], marks)
		t.check(god(t).boss_health == god_health, "%s: Jordan untouched (%d)" % [played[0], god(t).boss_health])
		var machine: Node = maze.state_machine
		await t.wait_until(func(): return machine.rotation_log.size() >= 2, 60 * 8)
		var built: Array = machine.combos.map(func(c): return String(c.name))
		t.log_p("the rotation so far %s, the attacks built %s" % [machine.rotation_log, built])
		t.check(machine.rotation_log.size() >= 2 and machine.rotation_log[1] == &"JordanComboKegs",
			"%s: the next attack is attack 2 (%s)" % [played[0], machine.rotation_log.slice(1)])


# How many physics steps a beat `seconds` long takes: the first whose summed clock reaches it (the combo's CLOCK_SLACK).
static func frames_for(seconds: float) -> int:
	return ceili(seconds * 60.0 - 0.006)


# The step after the beam lands: the clock's scale, and whether the flash and the colour kick are up.
static func beam_watch(marks: Dictionary) -> Callable:
	return func(m: Node) -> void:
		if m.beam_hit_frame < 0 or marks.has("stop"):
			return
		marks["stop"] = Engine.time_scale
		marks["flash"] = is_instance_valid(m.screen) and m.screen.flash_cover.visible
		marks["kick"] = is_instance_valid(m.screen) and m.screen.kick_cover.visible


# The beam against its knobs: its charge and its trace each their time (±1 frame), whatever the route's length, and the
# hit landing on the frame the head reaches the player's block, where it is. With V2 on: a hit-stop, the flash and the
# colour kick as it lands, and every wall beside its path lit.
static func check_beam(t, maze: Node, label: String, marks: Dictionary) -> void:
	var route: PackedVector2Array = maze.beam_route
	var length := 0.0
	for k in range(1, route.size()):
		length += route[k - 1].distance_to(route[k])
	var charge_frames: int = maze.trace_frame - maze.beam_frame
	var trace_frames: int = maze.beam_hit_frame - maze.trace_frame
	t.log_p("%s: the charge %d frames, the trace %d over %.0f px, the head at %s as it landed on f%d (arrived f%d); %s" % [label,
		charge_frames, trace_frames, length, maze.head_at_hit, maze.beam_hit_frame, maze.head_arrival_frame, marks])
	t.check(absi(charge_frames - frames_for(Layout.charge_time())) <= 1,
		"%s: the charge takes its %.2f s (%d frames)" % [label, Layout.charge_time(), charge_frames])
	t.check(absi(trace_frames - frames_for(Layout.trace_time())) <= 1,
		"%s: the trace takes its %.2f s over the route's %.0f px (%d frames)" % [label, Layout.trace_time(), length, trace_frames])
	t.check(maze.head_arrival_frame == maze.beam_hit_frame and maze.head_at_hit.distance_to(route[route.size() - 1]) <= 0.5,
		"%s: the hit lands as the head reaches the player's block" % label)
	if not Layout.BEAM_V2:
		return
	t.check(is_equal_approx(marks.get("stop", 1.0), HitStop.TIME_SCALE) and marks.get("flash", false) and marks.get("kick", false),
		"%s: a hit-stop, the flash and the colour kick as it lands" % label)
	var along := walls_along(maze)
	t.check(along > 0 and maze.walls.lit == along, "%s: the walls along its path lit (%d of %d)" % [label, maze.walls.lit, along])


# The walls beside the beam's path, from the goal back down to the player's block.
static func walls_along(maze: Node) -> int:
	var count := 0
	for cell: Vector2i in maze.walls.cells:
		for i in range(maze.step, maze.route.size()):
			var gap: Vector2i = (cell - maze.route[i]).abs()
			if gap.x <= 1 and gap.y <= 1:
				count += 1
				break
	return count


# The switch off: the drawn path's idle run on V1's beam.
static func tier_v1(t) -> void:
	Layout.BEAM_V2 = false
	pin(Layout.DRAWN_PATH)
	var maze := await open_maze(t)
	var marks := {}
	var seen := await drive(t, maze, -1, [], beam_watch(marks))
	t.check(maze.beamed and seen.health == [6, 3], "V1: the beam fires as the meter fills, a heart and a half (%s)" % [seen.health])
	check_beam(t, maze, "V1", marks)
	t.check(not is_instance_valid(maze.screen), "V1: none of V2's screen")


static func tier_locks(t) -> void:
	var maze := await open_maze(t)
	await t.wait_until(func(): return maze.beat == maze.Beat.LIVE, 60 * 10)
	var stamina: float = t.defense.stamina
	var press_time: float = t.defense.last_press_time
	var at: Vector2 = t.player.global_position
	for code in [KEY_W, KEY_SHIFT, KEY_Q]:
		t.tap(code)
		await t.wait(4)
	await t.wait(6)
	t.check(is_equal_approx(t.defense.stamina, stamina) and t.defense.last_press_time == press_time and not t.defense.is_parry_ready()
		and not t.defense.is_guarding() and t.player.global_position == at and maze.beat == maze.Beat.LIVE and maze.step == 0,
		"dash, block and punch change nothing: stamina %.1f -> %.1f, the parry window %s, moved %s" % [stamina,
		t.defense.stamina, "shut" if not t.defense.is_parry_ready() else "OPEN", t.player.global_position - at])
	# The first arrow's way, flicked and held through the hop into step 1's arrow: a second answer off the same flick
	# would be a wrong one unless step 1 went the same way, so the step is what tells.
	var way: Vector2i = maze.route[1] - maze.route[0]
	var flick := Vector2(way.x, -way.y)
	for amount in [0.2, 0.6, 0.9, 1.0]:
		stick(flick * amount)
		await t.wait(1)
	await t.wait(36)
	var held := {"step": maze.step, "wrongs": maze.wrongs, "beat": maze.Beat.keys()[maze.beat]}
	for amount in [0.6, 0.2, 0.0]:
		stick(flick * amount)
		await t.wait(1)
	await t.wait(4)
	t.log_p("the stick held %s: %s; let go: step %d, %d wrong, beat %s" % [WAYS[way], held, maze.step, maze.wrongs, maze.Beat.keys()[maze.beat]])
	t.check(held.step == 1 and held.beat == "LIVE" and maze.step == 1 and maze.wrongs == 0,
		"a stick flick answers once, held into the next arrow or let go (step %d, %d wrong)" % [maze.step, maze.wrongs])
	await drive(t, maze, PERFECT_REACTION)
	await pay_off(t, maze, 1)


# The left stick at `at`, x and y as the stick reads them (y down).
static func stick(at: Vector2) -> void:
	for axis in [JOY_AXIS_LEFT_X, JOY_AXIS_LEFT_Y]:
		var motion := InputEventJoypadMotion.new()
		motion.axis = axis
		motion.axis_value = at.x if axis == JOY_AXIS_LEFT_X else at.y
		Input.parse_input_event(motion)


static func tier_tiers(t) -> void:
	for bars in [1, 2, 3]:
		var maze := await open_maze(t)
		var god_health: int = god(t).boss_health
		await drive(t, maze, PERFECT_REACTION)
		var paid := await pay_off(t, maze, bars)
		t.check(paid.tiers == bars and god_health - paid.after == bars and paid.bars == bars,
			"%d bar%s banked: Jordan -%d (%d -> %d)" % [bars, "" if bars == 1 else "s", bars, god_health, paid.after])


static func tier_fizzle(t) -> void:
	var maze := await open_maze(t)
	var player_z: int = t.player.z_index
	var god_health: int = god(t).boss_health
	await drive(t, maze, PERFECT_REACTION)
	var paid := await pay_off(t, maze, 0)
	var left := leftovers(t, maze, player_z)
	t.check(paid.dazed and paid.tiers == 0 and paid.after == god_health, "no bar banked: Jordan untouched (%d -> %d)" % [god_health, paid.after])
	t.check(paid.wrapped and left.is_empty(), "and a clean wrap %s" % [left])


# Paused at three points: an arrow live at step 2, the knock after a wrong press at step 4, and the beam's trace once
# the answers stop at step 6 and the meter fills. While paused nothing of the maze moves; afterwards the meter, the knock
# and the beam each took their own time, counted in unpaused physics steps.
static func tier_pause(t) -> void:
	var maze := await open_maze(t)
	var state := {"paused_left": 0, "unpaused": 0, "held": {}, "moved": {}, "marks": {}, "current": ""}
	var watch := func(m: Node) -> void:
		if state.paused_left > 0:
			state.paused_left -= 1
			if snapshot(t, m) != state.held[state.current]:
				state.moved[state.current] = snapshot(t, m)
			if state.paused_left == 0:
				t.paused = false
			return
		state.unpaused += 1
		var marks: Dictionary = state.marks
		if m.first_arrow_frame >= 0 and not marks.has("first"):
			marks["first"] = state.unpaused
		if m.beat == m.Beat.KNOCK and not marks.has("knock"):
			marks["knock"] = state.unpaused
		if marks.has("knock") and m.beat == m.Beat.LIVE and m.step == 4 and not marks.has("knock_live"):
			marks["knock_live"] = state.unpaused
		if m.full_frame >= 0 and not marks.has("full"):
			marks["full"] = state.unpaused
		if m.beam_hit_frame >= 0 and not marks.has("hit"):
			marks["hit"] = state.unpaused
		var key := ""
		if m.beat == m.Beat.LIVE and m.step == 2 and m.beat_clock >= 0.05 and not state.held.has("arrow"):
			key = "arrow"
		elif m.beat == m.Beat.KNOCK and m.beat_clock >= 0.05 and not state.held.has("knock"):
			key = "knock"
		elif m.beat == m.Beat.TRACE and m.beat_clock >= Layout.trace_time() / 2.0 and not state.held.has("beam"):
			key = "beam"
		if key != "":
			state.current = key
			state.held[key] = snapshot(t, m)
			state.paused_left = PAUSE_FRAMES
			t.paused = true
	var seen := await drive(t, maze, PERFECT_REACTION, [4], watch, 6)
	var marks: Dictionary = state.marks
	t.log_p("paused at %s; moved while paused %s; unpaused steps %s" % [state.held.keys(), state.moved, marks])
	t.check(state.held.keys() == ["arrow", "knock", "beam"] and state.moved.is_empty(), "paused mid-arrow, mid-knock and mid-beam, and nothing moved")
	var meter_steps: int = marks.get("full", -1) - marks.get("first", 0)
	var knock_steps: int = marks.get("knock_live", -1) - marks.get("knock", 0)
	var beam_steps: int = marks.get("hit", -1) - marks.get("full", 0)
	var knock_expected := roundi((Layout.KNOCK_TIME + Layout.GLASS_HOLD + Layout.BACK_TIME + Layout.YELL_TELL) * 60.0)
	var beam_expected := frames_for(Layout.charge_time()) + frames_for(Layout.trace_time())
	t.check(absi(meter_steps - roundi(Layout.METER_TIME * 60.0)) <= 1, "the meter still fills in %.1f s of game time (%d steps)" % [Layout.METER_TIME, meter_steps])
	t.check(absi(knock_steps - knock_expected) <= 2, "the knock still takes its %.2f s to the same arrow (%d steps against %d)" % [knock_expected / 60.0, knock_steps, knock_expected])
	t.check(absi(beam_steps - beam_expected) <= 2, "the beam still lands %.2f s after the meter fills (%d steps against %d)" % [beam_expected / 60.0, beam_steps, beam_expected])
	t.check(seen.health == [6, 5, 2], "and the damage is the same: half a heart, then a heart and a half (%s)" % [seen.health])


# What must not move while the tree is paused.
static func snapshot(t, m: Node) -> Dictionary:
	return {"beat": m.beat, "clock": m.beat_clock, "meter": m.meter_clock, "at": t.player.global_position,
		"beam": m.beam.progress if is_instance_valid(m.beam) else -1.0}


static func tier_death(t) -> void:
	var maze := await open_maze(t, 1)
	var player_z: int = t.player.z_index
	var seen := await drive(t, maze, PERFECT_REACTION, [0])
	var released: bool = await t.wait_until(func(): return maze.released, 60 * 6)
	await t.wait(3)
	var left := leftovers(t, maze, player_z)
	t.log_p("health %s, released %s" % [seen.health, released])
	t.check(seen.health == [1, 0] and released and left.is_empty(), "the wrong press at half a heart kills, and the release is clean %s" % [left])
	var defeat: bool = await t.wait_until(func(): return t.current_scene != null and t.current_scene.scene_file_path == DEFEAT, 60 * 15)
	t.check(defeat, "then Defeat")
