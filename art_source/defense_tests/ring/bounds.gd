extends RefCounted

# bounds: nothing leaves the player outside the ring, in any fight (fight=<key>, one a process). The floor is read
# off ArenaScene's wallBoundaries - the inner faces of its four walls - and after every case the player's body has
# to be on it. His boss is switched off for the shared cases, so nothing of his holds or moves them.
#   walls    a point 190 px past each inner face and each corner is solid wall, so no single step can carry a body
#            through a rope and out the far side.
#   shoves   from the middle and from beside each rope, shoved at each wall and corner at 3000, 20000 and 100000 px/s,
#            through their own velocity and through a fight's pull (add_drift).
#   dashes   a real dash into each wall and corner from beside it.
#   writes   the position written into each rope, just through it and far out, past each wall and corner, with the
#            player free, locked for a parry-only beat and held talking.
#   squeeze  a boss's body put down on a player flush against each rope, reaching 12, 30 and 60 px into them.
#   opt-out  with may_leave_ring on, a held player stays where a sequence puts them outside; off, they are put back.
# Then his own drive, in the fights that have one that could reach a rope, with him switched back on:
#   danny    his slam string with the player in its footprint by the left rope: the settle slides them out on the
#            side of him there is floor for, never past the rope.
#   eric     his parried-sword stagger at the bottom of his ground: the drive in beside him ends on the floor.

const BOSSES_DIR := "res://Scenes/Bosses/"
const DIRECTIONS := {
	"L": Vector2(-1, 0), "R": Vector2(1, 0), "U": Vector2(0, -1), "D": Vector2(0, 1),
	"LU": Vector2(-1, -1), "RU": Vector2(1, -1), "LD": Vector2(-1, 1), "RD": Vector2(1, 1),
}
const DASH_KEYS := {
	"L": [KEY_LEFT], "R": [KEY_RIGHT], "U": [KEY_UP], "D": [KEY_DOWN],
	"LU": [KEY_LEFT, KEY_UP], "RU": [KEY_RIGHT, KEY_UP], "LD": [KEY_LEFT, KEY_DOWN], "RD": [KEY_RIGHT, KEY_DOWN],
}
const SPEEDS: Array[float] = [3000.0, 20000.0, 100000.0]
# How far past the edge of where the player's origin may be each write lands: into the rope, just through it,
# and well out.
const WRITE_DEPTHS: Array[float] = [10.0, 25.0, 60.0, 250.0, 2000.0]
# How far the body put down beside them reaches into a player standing flush against a rope.
const SQUEEZE_OVERLAPS: Array[float] = [12.0, 30.0, 60.0]
# About Eric's body, on the layer the bosses' bodies are on, which the player's own mask meets.
const SQUEEZE_SIZE := Vector2(180, 220)
const BOSS_LAYER := 4
# Where every boss entrance's walk-in starts the player: their mark, 260 px down past the bottom rope.
const WALK_IN_START := Vector2(959, 1160)
# How far past each inner face a point must still be wall.
const WALL_DEPTH := 190.0
# The frames a shove, a write or a squeeze is given to settle.
const SETTLE_FRAMES := 4
# A body flush on the floor's edge reads as on it.
const SLACK := 0.5
const DANNY_BODY := "Arena/DannyBossScene/DannyBossCharacterBody"
const ERIC_BODY := "Arena/EricBossScene/CharacterBody2D"


static func run(t) -> void:
	await enter(t)
	var ring := ring_floor(t)
	var origins := origin_area(t, ring)
	t.log_p("%s: the floor %s, the player's origin on it inside %s" % [t.fight, ring, origins])
	check_walls(t, ring)
	await quiet(t)
	await shoves(t, ring, origins)
	await dashes(t, ring, origins)
	await writes(t, ring, origins)
	await squeezes(t, ring, origins)
	await opt_out(t, ring, origins)
	match t.fight:
		"danny":
			await danny_nudge(t, ring, origins)
		"eric":
			await eric_drive(t, origins)


# The fight, loaded past its entrance, its lines and the card, the way the gauge modes load it.
static func enter(t) -> void:
	await t.load_fight(t.fight, t.STATE_INTROS.has(t.fight))
	await t.clear_intro(t.fight)
	if t.STATE_INTROS.has(t.fight):
		await t.wait_until(func(): return t.vs_card() != null and t.vs_card().is_playing(), t.VS_CARD_WAIT_FRAMES)
		await t.skip_vs_card()


# Every boss scene the fight put in the arena.
static func bosses(t) -> Array:
	return t.current_scene.get_node("Arena").get_children().filter(func(child): return child.scene_file_path.begins_with(BOSSES_DIR))


static func quiet(t) -> void:
	for boss in bosses(t):
		boss.process_mode = Node.PROCESS_MODE_DISABLED
	await free_player(t)


static func wake(t) -> void:
	for boss in bosses(t):
		boss.process_mode = Node.PROCESS_MODE_INHERIT


static func free_player(t) -> void:
	for code in [KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN, KEY_SHIFT, KEY_W]:
		t.release(code)
	t.player.unlock_actions()
	t.player.clear_face_point()
	t.player.clear_statuses()
	t.player.is_talking = false
	t.player.playerHealth = 1000
	t.clear_iframes()
	await t.wait(2)


#THE FLOOR

static func ring_floor(t) -> Rect2:
	var walls: Node = t.current_scene.get_node("Arena/wallBoundaries")
	var left := shape_rect(walls.get_node("leftWall"))
	var right := shape_rect(walls.get_node("rightWall"))
	var top := shape_rect(walls.get_node("topWall"))
	var bottom := shape_rect(walls.get_node("bottomWall"))
	return Rect2(left.end.x, top.end.y, right.position.x - left.end.x, bottom.position.y - top.end.y)


static func shape_rect(shape: CollisionShape2D) -> Rect2:
	return shape.global_transform * shape.shape.get_rect()


# Where the player's origin can be with their whole body on `ring`.
static func origin_area(t, ring: Rect2) -> Rect2:
	var body: Rect2 = t.body_rect()
	var before: Vector2 = t.player.global_position - body.position
	var after: Vector2 = body.end - t.player.global_position
	return Rect2(ring.position + before, ring.size - before - after)


static func on_floor(t, ring: Rect2) -> bool:
	return ring.grow(SLACK).encloses(t.body_rect())


# `gap` px in from the edge of `area` that `direction` points at, level with its middle on an axis it doesn't.
static func beside(area: Rect2, direction: Vector2, gap: float) -> Vector2:
	var at := area.get_center()
	if direction.x != 0.0:
		at.x = area.end.x - gap if direction.x > 0.0 else area.position.x + gap
	if direction.y != 0.0:
		at.y = area.end.y - gap if direction.y > 0.0 else area.position.y + gap
	return at


static func check_walls(t, ring: Rect2) -> void:
	var walls: Node = t.current_scene.get_node("Arena/wallBoundaries")
	var space: PhysicsDirectSpaceState2D = t.player.get_world_2d().direct_space_state
	var hollow := []
	for name in DIRECTIONS:
		var probe := beside(ring, DIRECTIONS[name], -WALL_DEPTH)
		var query := PhysicsPointQueryParameters2D.new()
		query.position = probe
		query.collision_mask = walls.collision_layer
		if not space.intersect_point(query).any(func(hit): return hit.collider == walls):
			hollow.append("%s %s" % [name, probe])
	t.check(hollow.is_empty(), "%.0f px past every inner face and corner is wall (hollow: %s)" % [WALL_DEPTH, hollow])


#THE SHARED CASES

static func shoves(t, ring: Rect2, origins: Rect2) -> void:
	var off := []
	var runs := 0
	for name in DIRECTIONS:
		var direction: Vector2 = DIRECTIONS[name]
		for start in [origins.get_center(), beside(origins, direction, 40.0)]:
			for speed in SPEEDS:
				for pulled in [false, true]:
					await t.settle_player(start)
					if pulled:
						for i in SETTLE_FRAMES:
							t.player.add_drift(direction.normalized() * speed)
							await t.physics_frame
					else:
						t.player.velocity = direction.normalized() * speed
						await t.wait(SETTLE_FRAMES)
					await t.wait(1)
					runs += 1
					if not on_floor(t, ring):
						off.append("%s %s at %.0f from %s: %s" % [name, "pulled" if pulled else "shoved", speed, start, t.player.global_position])
	t.log_p("shoves: %d, off the floor after %d" % [runs, off.size()])
	t.check(off.is_empty(), "%d shoves at the walls and corners, up to %.0f px/s through the player's own velocity and a fight's pull: all end on the floor (off it: %s)" % [runs, SPEEDS[-1], off])


static func dashes(t, ring: Rect2, origins: Rect2) -> void:
	var off := []
	for name in DASH_KEYS:
		await t.dash_ready()
		await t.settle_player(beside(origins, DIRECTIONS[name], 40.0))
		var path: Array = await t.dash_keys(DASH_KEYS[name])
		await t.wait(2)
		t.log_p("dash %s: %s -> %s" % [name, path[0], t.player.global_position])
		if not on_floor(t, ring):
			off.append("%s: %s" % [name, t.player.global_position])
	t.check(off.is_empty(), "a real dash into each wall and corner from 40 px off it stops on the floor (off it: %s)" % [off])


static func writes(t, ring: Rect2, origins: Rect2) -> void:
	var off := []
	var runs := 0
	for hold in ["free", "locked", "talking"]:
		for name in DIRECTIONS:
			for depth in WRITE_DEPTHS:
				await t.settle_player(origins.get_center())
				if hold == "locked":
					t.player.lock_actions()
				elif hold == "talking":
					t.player.is_talking = true
				var to := beside(origins, DIRECTIONS[name], -depth)
				t.player.global_position = to
				await t.wait(SETTLE_FRAMES)
				runs += 1
				if not on_floor(t, ring):
					off.append("%s %s %.0f past: written %s, left at %s" % [hold, name, depth, to, t.player.global_position])
				t.player.unlock_actions()
				t.player.is_talking = false
	t.log_p("writes: %d, off the floor after %d" % [runs, off.size()])
	t.check(off.is_empty(), "%d positions written into and past every wall and corner, the player free, locked and talking: all end on the floor (off it: %s)" % [runs, off])


static func squeezes(t, ring: Rect2, origins: Rect2) -> void:
	var off := []
	for name in ["L", "R", "U", "D"]:
		var direction: Vector2 = DIRECTIONS[name]
		for overlap in SQUEEZE_OVERLAPS:
			await t.settle_player(beside(origins, direction, 0.0))
			var body: Rect2 = t.body_rect()
			var block := StaticBody2D.new()
			block.name = "BoundsSqueeze"
			block.collision_layer = BOSS_LAYER
			block.collision_mask = 0
			var rect := RectangleShape2D.new()
			rect.size = SQUEEZE_SIZE
			var shape := CollisionShape2D.new()
			shape.shape = rect
			block.add_child(shape)
			# On the floor's side of them, reaching `overlap` px in.
			var reach: float = (body.size / 2.0 * direction.abs()).length() + (SQUEEZE_SIZE / 2.0 * direction.abs()).length()
			t.current_scene.get_node("Arena").add_child(block)
			block.global_position = body.get_center() - direction * (reach - overlap)
			await t.wait(SETTLE_FRAMES * 3)
			if not on_floor(t, ring):
				off.append("%s %.0f: %s" % [name, overlap, t.player.global_position])
			block.free()
			await t.wait(1)
	t.check(off.is_empty(), "a boss's body put down on a player flush against each rope, 12, 30 and 60 px into them, never squeezes them out through it (off it: %s)" % [off])


static func opt_out(t, ring: Rect2, origins: Rect2) -> void:
	if not "may_leave_ring" in t.player:
		t.check(false, "the player has may_leave_ring")
		return
	await t.settle_player(origins.get_center())
	t.player.is_talking = true
	t.player.may_leave_ring = true
	t.player.global_position = WALK_IN_START
	await t.wait(SETTLE_FRAMES * 3)
	var held: Vector2 = t.player.global_position
	t.player.may_leave_ring = false
	await t.wait(2)
	var back: bool = on_floor(t, ring)
	t.player.is_talking = false
	t.check(held == WALK_IN_START and back,
		"with may_leave_ring on, a held player stays on the walk-in's start outside the ring (%s); off, they are back on the floor (%s)" % [held, t.player.global_position])


#HIS OWN DRIVES

# His string from Idle with the player standing in its footprint by the left rope. His landings track their feet
# as far as his WALK_RECT lets him, so the big last one comes down beside the rope with them in it. The string draws
# its own number of hops (DannyBossSlams.hop_counts), so the big one is whichever landing came last.
static func danny_nudge(t, ring: Rect2, origins: Rect2) -> void:
	wake(t)
	t.boss = t.current_scene.get_node(DANNY_BODY)
	t.sm = t.boss.state_machine
	t.sm.on_child_transition(t.sm.current_state, "Idle")
	t.stop_boss_timers()
	for hazard in t.get_nodes_in_group(t.sm.HAZARD_GROUP):
		hazard.queue_free()
	await free_player(t)
	await t.settle_player(Vector2(origins.position.x + 30.0, 660.0))
	var slams: Node = t.sm.states["Slams"]
	t.sm.on_child_transition(t.sm.current_state, "Slams")
	await t.wait_until(func(): return t.sm.current_state != slams or slams.beat == slams.Beat.SETTLE, 900)
	var box: Rect2 = t.boss.body_box_rect(&"sleep")
	var inside: bool = slams.results.size() == slams.slams and slams.results[-1].feet_inside
	await t.wait_until(func(): return t.sm.current_state != slams, 120)
	await t.wait_until(func(): return not t.sm.is_driving_player(), 60)
	await t.wait(2)
	var feet: Vector2 = t.sm.player_feet()
	var clear: bool = feet.x <= box.position.x or feet.x >= box.end.x
	t.log_p("danny: the big landing (%d of %d) found them in his footprint %s, his nap's box %s, driven to %s, feet %s" % [slams.results.size(), slams.slams, inside, box, t.sm.drive_to, feet])
	t.check(inside and slams.nudged, "his big landing by the left rope found the player in his footprint, and slid them out")
	t.check(origins.grow(SLACK).has_point(t.sm.drive_to) and clear and on_floor(t, ring),
		"out beside him on the side there is floor for, never past the rope (to %s, feet %s, his box %s)" % [t.sm.drive_to, feet, box])
	t.sm.on_child_transition(t.sm.current_state, "Idle")
	t.stop_boss_timers()


# The drive EricParryStaggered starts as a reflected sword's auto finisher takes him: beside his hurtbox, at its
# foot. Its target only; the state never runs, so nothing moves.
static func eric_drive(t, origins: Rect2) -> void:
	wake(t)
	t.boss = t.current_scene.get_node(ERIC_BODY)
	t.sm = t.boss.state_machine
	t.park_eric()
	await free_player(t)
	t.boss.global_position = Vector2(700.0, t.boss.KNOCKBACK_AREA.end.y)
	await t.settle_player(Vector2(500.0, origins.end.y))
	var staggered: Node = t.sm.states["ParryStaggered"]
	staggered.drive_player_in(t.player)
	var to: Vector2 = staggered.drive_to
	staggered.drive_left = 0.0
	staggered.driven = null
	t.check(origins.grow(SLACK).has_point(to),
		"his parried-sword stagger at the bottom of his ground drives the player in onto the floor (to %s, their origin's floor %s)" % [to, origins])
