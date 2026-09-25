extends RefCounted

# danny_spit (coder B): Danny's worm spit, its puddles and the root they spring (DannyBossSpit,
# DannyBossGlobScript, DannyBossPuddleScript, DannyBossRoot; plan sections 3 and 13). --fixed-fps 60.
#   spit       the globs leave his mouth in two volleys of two, at 0.45 and 0.53 s then 0.80 and 0.88 s, and he
#              is done at 1.10; all four land, armed, on spots that keep the rules (rope_gap inside the ropes,
#              clear of the player's feet and of his, apart from each other), the first volley on the side the
#              first spit frame aims at; and the open floor left is one piece, holding the player's feet and a
#              side of him to punch from.
#   placement  pick_spots swept over the floor, the player's feet and his at spots all round, a few seeds each:
#              always four, keeping the rules, the open floor always one piece with a way to his side.
#   next       the next gulp takes the old four out of play at once and lays four more.
#   spared     standing where a glob lands, the player isn't rooted by it until they step out and back in.
#   rooted     walking in roots them: actions locked, the guard still live, that puddle used up.
#   dash       a dash down across a puddle roots nothing; a dash that ends in one roots on the step it ends.
# And never more than four puddles live at any step of the whole run.
# headbutt.gd borrows enter(), park() and put_feet().

const BODY := "Arena/DannyBossScene/DannyBossCharacterBody"
const SEED := 7
const FRAME_TIME := 1.0 / 60.0
# The player's feet where each check starts: the suite's smoke spot for him.
const PLAYER_FEET := Vector2(960, 842)
# In the open, clear of any puddle yet: where the dash is measured.
const DASH_FEET := Vector2(600, 842)
# Where the dash tests end inside a puddle: this far past its pivot.
const DASH_END_IN := 20.0
# The open floor is measured in cells this size, open when their centre keeps CLEARANCE from every trigger: a
# way through is at least twice that wide.
const CELL := 16.0
const CLEARANCE := 32.0
# Where the player stands to punch him standing, either side of his feet.
const SIDE := Vector2(190, 3)
# The placement sweep: the player's feet on this lattice over the floor, his at each of these, and seeds.
const SWEEP_FEET_STEP := Vector2(160, 100)
const SWEEP_DANNY: Array[Vector2] = [Vector2(960, 600), Vector2(400, 400), Vector2(1500, 850), Vector2(700, 900)]
const SWEEP_SEEDS := 2


static func run(t) -> void:
	await enter(t)
	var spit: Node = t.sm.states["Spit"]
	var dash: float = await dash_length(t)
	var most := [0]
	var count := func(): most[0] = maxi(most[0], t.sm.live_puddles().size())
	t.physics_frame.connect(count)
	await check_spit(t, spit)
	check_placement(t, spit)
	await check_next(t, spit)
	await check_spared_and_rooted(t, spit)
	await check_dashes(t, dash)
	t.physics_frame.disconnect(count)
	t.check(most[0] <= 4, "never more than four puddles live at any step (at most %d)" % most[0])


# His fight up to its first Idle, whatever his intro does on the way; the rng seeded.
static func enter(t) -> void:
	await t.load_fight("danny", true)
	t.boss = t.current_scene.get_node(BODY)
	t.sm = t.boss.state_machine
	for i in 1800:
		if String(t.sm.current_state.name) == "Idle":
			break
		if t.vs_card() != null and t.vs_card().is_playing():
			await t.skip_vs_card()
		elif t.live_balloon() != null and i % 8 == 0:
			t.tap(KEY_ENTER)
		await t.physics_frame
	t.check(String(t.sm.current_state.name) == "Idle", "his fight comes up to Idle")
	t.sm.rng.seed = SEED
	t.player.playerHealth = 1000


# Idle at HOME with his next attack held off, the player's feet at `feet` with every key up, fresh, and
# with a full bar.
static func park(t, feet: Vector2) -> void:
	t.sm.on_child_transition(t.sm.current_state, "Idle")
	t.stop_boss_timers()
	t.boss.global_position = t.sm.HOME
	for code in [KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN, KEY_SHIFT, KEY_W]:
		t.release(code)
	await put_feet(t, feet)
	t.clear_iframes()
	t.player.playerHealth = 1000
	t.defense._set_stamina(t.defense.max_stamina)


# The bottom middle of the player's hurtbox on `feet`.
static func put_feet(t, feet: Vector2) -> void:
	t.player.global_position += feet - t.sm.player_feet()
	t.player.velocity = Vector2.ZERO
	await t.wait(2)


static func state_is(t, state_name: String) -> bool:
	return String(t.sm.current_state.name) == state_name


static func dash_toward(t, code: int) -> void:
	t.press(code)
	t.tap(KEY_W)
	await t.wait_until(func(): return t.player.is_dodging, 20)
	await t.wait_until(func(): return not t.player.is_dodging, 20)
	t.release(code)
	await t.wait(2)


# How far the player's feet go on one dash to the right, measured before any puddle is down.
static func dash_length(t) -> float:
	await park(t, DASH_FEET)
	await t.dash_ready()
	var from: Vector2 = t.sm.player_feet()
	await dash_toward(t, KEY_RIGHT)
	var length: float = t.sm.player_feet().x - from.x
	t.log_p("a dash carries the feet %.1f px" % length)
	return length


static func live_ids(t) -> Array:
	return t.sm.live_puddles().map(func(p): return p.get_instance_id())


static func puddle_at(t, spot: Vector2) -> Node2D:
	for puddle in t.sm.live_puddles():
		if puddle.global_position.distance_to(spot.round()) <= 1.0:
			return puddle
	return null


static func inside_ellipse(offset: Vector2, half: Vector2) -> bool:
	return pow(offset.x / half.x, 2.0) + pow(offset.y / half.y, 2.0) < 1.0


# The first placement rule `spots` break with the player's feet and his where they are, or "" for none.
static func broken_rule(t, spit: Node, spots: Array, feet: Vector2, danny: Vector2) -> String:
	var radii: Vector2 = spit.radii
	var ropes: Rect2 = t.sm.ROPES
	var inset: Vector2 = radii + Vector2.ONE * spit.rope_gap
	var area := Rect2(ropes.position + inset, ropes.size - 2.0 * inset)
	for spot in spots:
		if not area.has_point(spot):
			return "%s not %.0f px inside the ropes" % [spot, spit.rope_gap]
		if inside_ellipse(feet - spot, radii + Vector2.ONE * spit.clear_of_player):
			return "%s within %.0f px of the player's feet %s" % [spot, spit.clear_of_player, feet]
		if inside_ellipse(danny - spot, radii + spit.clear_of_danny):
			return "%s on the floor round his feet %s" % [spot, danny]
	for i in spots.size():
		for j in range(i + 1, spots.size()):
			if inside_ellipse(spots[i] - spots[j], 2.0 * radii + Vector2.ONE * spit.apart):
				return "%s and %s under %.0f px apart" % [spots[i], spots[j], spit.apart]
	return ""


# The floor inside the ropes in CELL cells, open where a cell keeps CLEARANCE from every puddle's trigger: whether
# the feet's cell is open, whether every open cell is reached from it (one piece: nothing walled off), and
# whether a side of him to punch from is reached.
static func open_floor(t, radii: Vector2, spots: Array, feet: Vector2, danny: Vector2) -> Dictionary:
	var ropes: Rect2 = t.sm.ROPES
	var columns := int(ropes.size.x / CELL)
	var rows := int(ropes.size.y / CELL)
	var half := radii + Vector2.ONE * CLEARANCE
	var open := PackedByteArray()
	open.resize(columns * rows)
	var total := 0
	for row in rows:
		for column in columns:
			var at := ropes.position + (Vector2(column, row) + Vector2(0.5, 0.5)) * CELL
			var free := true
			for spot in spots:
				if inside_ellipse(at - spot, half):
					free = false
					break
			open[row * columns + column] = 1 if free else 0
			total += 1 if free else 0
	var cell_of := func(point: Vector2) -> int:
		var column := clampi(int((point.x - ropes.position.x) / CELL), 0, columns - 1)
		var row := clampi(int((point.y - ropes.position.y) / CELL), 0, rows - 1)
		return row * columns + column
	var start: int = cell_of.call(feet)
	var result := {"feet_open": open[start] == 1, "one_piece": false, "side": false}
	if open[start] == 0:
		return result
	var seen := PackedByteArray()
	seen.resize(columns * rows)
	var queue: Array[int] = [start]
	seen[start] = 1
	var head := 0
	while head < queue.size():
		var at: int = queue[head]
		head += 1
		var column := at % columns
		var row := floori(at / float(columns))
		for step in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
			var c: int = column + step.x
			var r: int = row + step.y
			if c < 0 or c >= columns or r < 0 or r >= rows:
				continue
			var next := r * columns + c
			if open[next] == 1 and seen[next] == 0:
				seen[next] = 1
				queue.append(next)
	result.one_piece = queue.size() == total
	for side in [-1.0, 1.0]:
		var spot := danny + Vector2(SIDE.x * side, SIDE.y)
		if ropes.has_point(spot) and seen[cell_of.call(spot)] == 1:
			result.side = true
	return result


static func check_spit(t, spit: Node) -> void:
	t.log_p("-- a spit: four globs from his mouth in two volleys, four puddles on spots that keep the rules")
	await park(t, PLAYER_FEET)
	var feet: Vector2 = t.sm.player_feet()
	var froms: Array = []
	var seen := {}
	var watch := func():
		for glob in spit.globs:
			if is_instance_valid(glob) and not seen.has(glob.get_instance_id()):
				seen[glob.get_instance_id()] = true
				froms.append(glob.from)
	t.physics_frame.connect(watch)
	var start: float = t.boss.fight_clock
	t.sm.on_child_transition(t.sm.current_state, "Spit")
	var spots: Array = spit.spots.duplicate()
	var idle: bool = await t.wait_until(func(): return state_is(t, "Idle"), 120)
	var done: float = t.boss.fight_clock - start
	t.stop_boss_timers()
	var landed: bool = await t.wait_until(func(): return t.sm.live_puddles().size() == 4 and t.sm.live_puddles().all(func(p): return p.armed), 150)
	t.physics_frame.disconnect(watch)
	var times: Array = spit.release_times.map(func(at): return snappedf(at - start, 0.0001))
	var puddles: Array = t.sm.live_puddles().map(func(p): return p.global_position)
	t.log_p("released %s s in, done %.4f s in; spots %s from feet %s; puddles %s" % [times, done, spots, feet, puddles])
	var slack := FRAME_TIME + 0.0001
	var want: Array = [spit.first_at, spit.first_at + spit.volley_gap, spit.second_at, spit.second_at + spit.volley_gap]
	var on_time := times.size() == 4
	for i in times.size():
		on_time = on_time and absf(times[i] - want[i]) <= slack
	t.check(on_time, "the globs leave at %s s, to the frame (%s)" % [want, times])
	t.check(idle and absf(done - spit.done_at) <= slack, "and he is done at %.2f s (%.4f)" % [spit.done_at, done])
	var mouths: Array = [t.boss.mouth_point(&"spit_fire"), t.boss.mouth_point(&"spit_fire2")]
	var from_mouths := froms.size() == 4
	for i in froms.size():
		from_mouths = from_mouths and froms[i].distance_to(mouths[0 if i < 2 else 1]) < 0.5
	t.check(from_mouths, "two from each spit frame's mouth texel (%s, want %s)" % [froms, mouths])
	var broken := broken_rule(t, spit, spots, feet, t.sm.HOME)
	t.check(spots.size() == 4 and broken == "", "four spots keeping the rules %s" % broken)
	if spots.size() == 4:
		var first_right: bool = not t.boss.sprite.flip_h
		var first: Array = spots.slice(0, 2).map(func(s): return s.x)
		var second: Array = spots.slice(2, 4).map(func(s): return s.x)
		var sided: bool = first.min() >= second.max() if first_right else first.max() <= second.min()
		t.check(sided, "the first volley goes to the side the first spit frame aims at (%s)" % ["right" if first_right else "left"])
	t.check(landed and spots.all(func(s): return puddle_at(t, s) != null), "all four land, armed, one on each spot")
	var ground := open_floor(t, spit.radii, puddles, feet, t.sm.HOME)
	t.check(ground.feet_open and ground.one_piece and ground.side,
		"the open floor is one piece, a way through at least %.0f px wide, from the player's feet to his side (%s)" % [2.0 * CLEARANCE, ground])


static func check_placement(t, spit: Node) -> void:
	t.log_p("-- placement swept over the floor")
	var ropes: Rect2 = t.sm.ROPES
	var cases := 0
	var failures: Array[String] = []
	var near: Array[float] = []
	var y := ropes.position.y + SWEEP_FEET_STEP.y / 2.0
	while y < ropes.end.y:
		var x := ropes.position.x + SWEEP_FEET_STEP.x / 2.0
		while x < ropes.end.x:
			var feet := Vector2(x, y)
			for danny in SWEEP_DANNY:
				if inside_ellipse(feet - danny, Vector2(200, 60)):
					continue
				for seed in SWEEP_SEEDS:
					t.sm.rng.seed = SEED * 1000 + cases
					cases += 1
					var spots: Array = spit.pick_spots(feet, danny)
					var broken := broken_rule(t, spit, spots, feet, danny)
					var ground := open_floor(t, spit.radii, spots, feet, danny)
					if spots.size() != 4 or broken != "" or not (ground.feet_open and ground.one_piece and ground.side):
						failures.append("feet %s, his %s: %d spots %s %s %s" % [feet, danny, spots.size(), spots, broken, ground])
					near.append(spots.map(func(s): return s.distance_to(feet)).min())
			x += SWEEP_FEET_STEP.x
		y += SWEEP_FEET_STEP.y
	t.sm.rng.seed = SEED
	near.sort()
	t.log_p("%d cases; the nearest puddle's pivot from the feet: least %.0f, median %.0f, most %.0f px" % [cases, near[0], near[floori(near.size() / 2.0)], near[-1]])
	for failure in failures.slice(0, 5):
		t.log_p("  %s" % failure)
	t.check(cases > 0 and failures.is_empty(), "every case: four spots keeping the rules, the open floor one piece with a way from the player to his side (%d of %d fail)" % [failures.size(), cases])


static func check_next(t, spit: Node) -> void:
	t.log_p("-- the next spit: its gulp dries the old four out of play at once, and four more land")
	var old := live_ids(t)
	t.sm.on_child_transition(t.sm.current_state, "Spit")
	var out_of_play: bool = t.sm.live_puddles().is_empty() and old.all(func(id): return is_instance_id_valid(id) and instance_from_id(id).gone and not instance_from_id(id).armed)
	t.check(old.size() == 4 and out_of_play, "the gulp takes the old four out of play at once")
	await t.wait_until(func(): return state_is(t, "Idle"), 120)
	t.stop_boss_timers()
	var dried: bool = await t.wait_until(func(): return old.all(func(id): return not is_instance_id_valid(id)), 60)
	t.check(dried, "and they are gone once dried")
	var landed: bool = await t.wait_until(func(): return t.sm.live_puddles().size() == 4 and t.sm.live_puddles().all(func(p): return p.armed), 150)
	t.check(landed and spit.spots.all(func(s): return puddle_at(t, s) != null), "four new puddles lie on its own spots")


static func check_spared_and_rooted(t, spit: Node) -> void:
	t.log_p("-- spared where a glob lands, rooted walking back in")
	await park(t, PLAYER_FEET)
	t.sm.on_child_transition(t.sm.current_state, "Spit")
	var spot: Vector2 = spit.spots[0]
	await put_feet(t, spot)
	await t.wait_until(func(): return state_is(t, "Idle"), 120)
	t.stop_boss_timers()
	var armed: bool = await t.wait_until(func(): return puddle_at(t, spot) != null and puddle_at(t, spot).armed, 120)
	var puddle: Node2D = puddle_at(t, spot)
	if not armed or puddle == null:
		t.check(false, "the first glob's puddle lands under the player")
		return
	var id := puddle.get_instance_id()
	t.check(puddle.spared and not t.player.is_action_locked, "it lands and arms under the player's feet, and spares them")
	await t.wait(30)
	t.check(is_instance_valid(puddle) and puddle.armed and not t.player.is_action_locked, "standing in it half a second: still not rooted")
	t.press(KEY_LEFT)
	await t.wait_until(func(): return not puddle.contains_feet(t.sm.player_feet()), 60)
	t.release(KEY_LEFT)
	await t.wait(3)
	t.check(is_instance_valid(puddle) and not puddle.spared and puddle.armed and not t.player.is_action_locked, "stepped out of it: no longer spared, not rooted")
	var live_before: int = t.sm.live_puddles().size()
	t.press(KEY_RIGHT)
	var rooted: bool = await t.wait_until(func(): return t.player.is_action_locked, 60)
	t.release(KEY_RIGHT)
	var root: Node = t.sm.root
	var inside: bool = is_instance_id_valid(id) and instance_from_id(id).contains_feet(t.sm.player_feet())
	t.log_p("rooted %s, feet inside %s, root %s, live %d -> %d, now %s" % [rooted, inside, root, live_before, t.sm.live_puddles().size(), t.sm.current_state.name])
	t.check(rooted and root != null and not root.released, "walking back in roots them: their actions locked, the worms holding")
	t.check(not is_instance_id_valid(id) or instance_from_id(id).gone, "and uses that puddle up")
	t.check(t.sm.live_puddles().size() == live_before - 1, "leaving the other three (%d live)" % t.sm.live_puddles().size())
	t.press(KEY_SHIFT)
	await t.wait(3)
	t.check(t.defense.is_guarding(), "the guard still comes up while rooted")
	t.release(KEY_SHIFT)
	t.check(state_is(t, "Headbutt"), "and he answers it with his headbutt")
	await t.wait_until(func(): return state_is(t, "Idle"), 240)
	t.stop_boss_timers()


# On the puddle nearest the middle of the ring, the others dried so no dash meets them: end to end a puddle is
# wider than a dash, so the dash across it goes down.
static func check_dashes(t, dash: float) -> void:
	t.log_p("-- dashes: down across a puddle roots nothing; one that ends in it roots as it ends")
	var puddles: Array = t.sm.live_puddles()
	if puddles.is_empty():
		t.check(false, "a puddle is left to dash over")
		return
	var middle: Vector2 = t.sm.ROPES.get_center()
	puddles.sort_custom(func(a, b): return a.global_position.distance_to(middle) < b.global_position.distance_to(middle))
	var puddle: Node2D = puddles[0]
	for other in puddles.slice(1):
		other.dry(0.05)
	var id := puddle.get_instance_id()
	var centre: Vector2 = puddle.global_position
	t.log_p("its trigger %.0f x %.0f px, a dash %.0f px" % [2.0 * puddle.radii.x, 2.0 * puddle.radii.y, dash])
	await park(t, centre - Vector2(0.0, dash / 2.0))
	await t.dash_ready()
	t.check(await t.wait_until(func(): return t.sm.can_root(), 120), "the grace over, a root may be sprung again")
	t.check(not puddle.contains_feet(t.sm.player_feet()), "the feet start clear of it, %.0f px above its pivot" % (dash / 2.0))
	await dash_toward(t, KEY_DOWN)
	var feet: Vector2 = t.sm.player_feet()
	t.check(not t.player.is_action_locked and is_instance_id_valid(id) and puddle.armed,
		"a dash straight down across it roots nothing, and leaves it armed (feet %.0f px past its pivot)" % (feet.y - centre.y))
	await put_feet(t, centre + Vector2(DASH_END_IN - dash, 0.0))
	await t.dash_ready()
	var steps := [0, -1]
	var watch := func():
		steps[0] += 1
		if steps[1] < 0 and t.player.is_action_locked:
			steps[1] = steps[0]
	var ended := [0]
	t.press(KEY_RIGHT)
	t.tap(KEY_W)
	await t.wait_until(func(): return t.player.is_dodging, 20)
	t.physics_frame.connect(watch)
	await t.wait_until(func(): return not t.player.is_dodging, 20)
	ended[0] = steps[0]
	t.release(KEY_RIGHT)
	await t.wait(4)
	t.physics_frame.disconnect(watch)
	var end_feet: Vector2 = t.sm.player_feet()
	t.log_p("the dash ended on step %d, rooted on step %d, feet %.0f px past the pivot" % [ended[0], steps[1], end_feet.x - centre.x])
	t.check(steps[1] > 0 and steps[1] - ended[0] <= 1 and t.sm.root != null, "a dash that ends inside it roots on the step it ends")
	t.check(not is_instance_id_valid(id) or instance_from_id(id).gone, "and uses it up")
	await t.wait_until(func(): return state_is(t, "Idle"), 240)
	t.stop_boss_timers()
