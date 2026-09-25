extends RefCounted

# greyson_plates (coder B): Greyson's throw and its plates (GreysonThrow, GreysonPlateScript; plan sections 3.1 and
# 9.6), in his test scene, the cycle pinned to the throw alone. --fixed-fps 60. tier=
#   throw    (the default) the red badge over his crown for the wind-up and the parry rearmed; four plates from
#            his hand at 0.35, 0.70, 1.05 and 1.40 s, the first at the player's feet, the second and third 35
#            degrees either side of its line, and the fourth, the player having crossed to his other side, turned
#            round at their feet again; each first leg too slow to reach the player in under 0.40 s; done at 1.75 s.
#   bounces  with the player off the ring: each plate off the ropes three times, then gone in its vanish.
#   parry    the first plate parried: PARRIED, knocked down, and one read.
#   dash     dashed through: DODGED, a perfect dodge, one read, and it flies on.
#   hit      no answer: HIT for half a heart, it drops, and the gauge loses a read.
#   guard    the block key held from before the throw: HIT all the same.
# slams.gd borrows enter(), park() and put_feet().

const SCENE := "res://Scenes/Bosses/GreysonTestFightScene.tscn"
const BODY := "Arena/GreysonScene/GreysonCharacterBody"
const HitInfo := preload("res://Scripts/HitInfo.gd")
const SEED := 3
const FRAME_TIME := 1.0 / 60.0
const SLACK := FRAME_TIME + 0.0001
# Down and to the left of him, well clear of his feet: plate 1 comes straight at them.
const PLAYER_FEET := Vector2(700, 820)
# Where the player has gone once plate 1 is out: down and to his right, clear of plates 1-3.
const PLATE_4_FEET := Vector2(1250, 820)
# Below the ring altogether: nothing of his reaches it.
const AWAY := Vector2(960, 1500)


static func run(t) -> void:
	await enter(t, [["Throw"]])
	match "throw" if t.tier == "normal" else t.tier:
		"throw":
			await tier_throw(t)
		"bounces":
			await tier_bounces(t)
		"parry", "dash", "hit", "guard":
			await tier_answer(t, t.tier)
		_:
			t.check(false, "greyson_plates has no tier %s" % t.tier)


# His test scene, the takeover landed at once and Idle, his cycles pinned to `chain`, and the rng seeded.
static func enter(t, chain: Array) -> void:
	await t.open_scene(SCENE)
	await t.wait(3)
	t.player = t.current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
	t.defense = t.player.get_node("Defense")
	t.boss = t.current_scene.get_node(BODY)
	t.sm = t.boss.state_machine
	t.check(await t.wait_until(func(): return String(t.sm.current_state.name) == "Idle", 120), "his test scene comes up in Idle")
	var pinned: Array[Array] = []
	pinned.assign(chain)
	t.sm.ATTACKS = pinned
	t.sm.rng.seed = SEED
	t.track()
	t.track_parries()
	t.track_dodges()


# Idle at HOME with his next attack held off, nothing of his left, the player's feet at `feet` with every key up,
# and an empty open gauge.
static func park(t, feet: Vector2) -> void:
	t.sm.on_child_transition(t.sm.current_state, "Idle")
	t.sm.clear_pending_zones()
	for node in t.get_nodes_in_group(t.sm.HAZARD_GROUP):
		node.queue_free()
	t.stop_boss_timers()
	t.boss.global_position = t.sm.HOME
	t.boss.show_body()
	for code in [KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN, KEY_SHIFT, KEY_W]:
		t.release(code)
	await put_feet(t, feet)
	t.clear_iframes()
	t.player.playerHealth = 1000
	t.defense._set_stamina(t.defense.max_stamina)
	t.boss.break_gauge.locked = false
	t.boss.break_gauge.value = 0.0
	await t.wait(20)
	t.events.clear()
	t.parries.clear()
	t.dodges.clear()


static func put_feet(t, feet: Vector2) -> void:
	# AWAY is past the bottom rope, where the ring's net (PlayerScript.may_leave_ring) would put them back on the mat.
	t.player.may_leave_ring = feet == AWAY
	t.player.global_position += feet - t.sm.player_feet()
	t.player.velocity = Vector2.ZERO
	await t.wait(2)


# By id: a lambda holding a plate or a zone itself errors once it frees.
static func live(id: int) -> Node2D:
	return instance_from_id(id) as Node2D if is_instance_id_valid(id) else null


static func state_is(t, state_name: String) -> bool:
	return String(t.sm.current_state.name) == state_name


static func tier_throw(t) -> void:
	t.log_p("-- the throw: the badge, then four plates off his hand")
	await park(t, PLAYER_FEET)
	var throw: Node = t.sm.states["Throw"]
	var count: int = throw.release_at.size()
	var height: float = load("res://Scripts/GreysonPlateScript.gd").FLIGHT.height
	t.defense.on_block_pressed()
	var pressed_before: bool = t.defense.last_press_time != -INF
	var seen := {"badge_steps": 0, "badge_after": false, "speeds": {}, "hands": [], "facing_left": [], "clock": 0.0}
	var start: float = t.boss.fight_clock
	var watch := func():
		var badge: bool = t.live_tells().any(func(tell): return tell.name == "ParryTell%d" % t.boss.get_instance_id())
		if badge:
			if throw.thrown == 0:
				seen.badge_steps += 1
			else:
				seen.badge_after = true
		for i in throw.plates.size():
			if not seen.speeds.has(i) and is_instance_valid(throw.plates[i]):
				seen.speeds[i] = throw.plates[i].speed
		while seen.hands.size() < throw.thrown:
			seen.hands.append(t.boss.release_point(&"throw") + Vector2(0, height))
			seen.facing_left.append(t.boss.facing_left)
	t.physics_frame.connect(watch)
	t.sm.start_cycle()
	var rearmed: bool = t.defense.last_press_time == -INF
	await t.wait_until(func(): return throw.thrown >= 1, 60)
	await put_feet(t, PLATE_4_FEET)
	var done: bool = await t.wait_until(func(): return state_is(t, "Idle"), 180)
	var lasted: float = t.boss.fight_clock - start
	t.physics_frame.disconnect(watch)
	var times: Array = throw.release_clocks.map(func(at): return snappedf(at - start, 0.0001))
	t.log_p("released at %s s from %s, facing left %s, at feet %s, headings %s, first legs %s px/s; done after %.4f s"
		% [times, throw.release_points, seen.facing_left, throw.aimed_at, throw.headings, seen.speeds.values(), lasted])
	t.check(pressed_before and rearmed, "the parry rearmed as he winds up")
	t.check(absf(seen.badge_steps * FRAME_TIME - throw.release_at[0]) <= SLACK + FRAME_TIME and not seen.badge_after,
		"the red badge over him through the wind-up, %.2f s, and gone once the first plate is out (%d steps)" % [throw.release_at[0], seen.badge_steps])
	var on_time := count == 4 and times.size() == count
	for i in times.size():
		on_time = on_time and absf(times[i] - throw.release_at[i]) <= SLACK
	t.check(on_time, "four plates, at %s s, to the frame" % [throw.release_at])
	var from_hand: bool = seen.hands.size() == throw.release_points.size()
	for i in throw.release_points.size():
		from_hand = from_hand and throw.release_points[i].distance_to(seen.hands[i]) <= 1.0
	t.check(from_hand, "each from his hand as it left (%s)" % [seen.hands])
	if throw.headings.size() == 4:
		var line: Vector2 = (throw.aimed_at[0] - throw.release_points[0]).normalized()
		var second: float = rad_to_deg(line.angle_to(throw.headings[1]))
		var third: float = rad_to_deg(line.angle_to(throw.headings[2]))
		var again: Vector2 = (throw.aimed_at[3] - throw.release_points[3]).normalized()
		t.check(throw.headings[0].is_equal_approx(line), "the first at the player's feet as it left")
		t.check(absf(second - throw.spreads[1]) <= 0.01 and absf(third - throw.spreads[2]) <= 0.01,
			"the second and third %.0f and %.0f degrees off that line, though the player has gone (%.2f, %.2f)" % [throw.spreads[1], throw.spreads[2], second, third])
		t.check(throw.aimed_at[3].distance_to(PLATE_4_FEET) <= 1.0 and throw.headings[3].is_equal_approx(again),
			"the fourth at the player's feet again, where they have gone (%s)" % throw.aimed_at[3])
		t.check(seen.facing_left == [true, true, true, false], "turned round to them for it (facing left %s)" % [seen.facing_left])
	var slow_enough := true
	for i in seen.speeds.size():
		var reach: float = throw.release_points[i].distance_to(throw.aimed_at[i])
		slow_enough = slow_enough and is_equal_approx(seen.speeds[i], minf(throw.plate_speed, reach / throw.min_flight))
	t.check(seen.speeds.size() == count and slow_enough,
		"each first leg min(%.0f, its reach / %.2f): never at the player in under %.2f s" % [throw.plate_speed, throw.min_flight, throw.min_flight])
	t.check(done and absf(lasted - throw.done_at) <= SLACK, "done %.2f s in, and the chain goes on (%.4f)" % [throw.done_at, lasted])


static func tier_bounces(t) -> void:
	t.log_p("-- the plates with the player off the ring: three ropes each, then the vanish")
	await park(t, AWAY)
	var throw: Node = t.sm.states["Throw"]
	var inner: Rect2 = t.sm.ROPES.grow(-load("res://Scripts/GreysonArtLayout.gd").fx(&"plate").radius)
	t.sm.start_cycle()
	var count: int = throw.release_at.size()
	await t.wait_until(func(): return throw.thrown == count, 120)
	var ids: Array = throw.plates.map(func(p): return p.get_instance_id())
	var kept := {}
	var watch := func():
		for id in ids:
			var plate := live(id)
			if plate != null:
				kept[id] = plate.turns.duplicate()
	t.physics_frame.connect(watch)
	await t.wait_until(func(): return ids.all(func(id): return live(id) == null), 900)
	t.physics_frame.disconnect(watch)
	var counts: Array = ids.map(func(id): return kept.get(id, []).size())
	var edges := ids.all(func(id): return kept.get(id, []).all(func(turn): return on_edge(turn.at, inner)))
	t.log_p("turns a plate %s" % [counts])
	t.check(counts.size() == count and counts.all(func(n): return n == throw.bounces) and edges, "each of the %d plates off the ropes %d times, each on their inner edge" % [count, throw.bounces])
	t.check(ids.all(func(id): return live(id) == null) and t.events.is_empty(), "then gone, having touched nobody")


static func on_edge(at: Vector2, rect: Rect2) -> bool:
	return absf(at.x - rect.position.x) < 0.51 or absf(at.x - rect.end.x) < 0.51 \
		or absf(at.y - rect.position.y) < 0.51 or absf(at.y - rect.end.y) < 0.51


# The first plate answered as `answer` says, the others kept off the player: plates 2 and 3 fly wide of them, and
# they are off the ring before plate 4 comes looking. What it got, and the gauge.
static func tier_answer(t, answer: String) -> void:
	t.log_p("-- the first plate, answered: %s" % answer)
	await park(t, PLAYER_FEET)
	var gauge: Node = t.boss.break_gauge
	var read: float = gauge.parry_gain
	if answer == "hit":
		gauge.value = 3.0 * read
	var before: float = gauge.value
	if answer == "dash":
		await t.dash_ready()
	var throw: Node = t.sm.states["Throw"]
	if answer == "guard":
		t.press(KEY_SHIFT)
	t.sm.start_cycle()
	await t.wait_until(func(): return throw.thrown >= 1, 60)
	var id: int = throw.plates[0].get_instance_id()
	await t.wait_until(func(): return live(id) == null or steps_to_contact(t, live(id)) <= 5.0, 120)
	match answer:
		"parry":
			t.press(KEY_SHIFT)
		"dash":
			var start: Vector2 = live(id).global_position if live(id) != null else Vector2.ZERO
			await dash_at(t, start)
	var answered := func() -> bool: return live(id) == null or not live(id).results.is_empty()
	await t.wait_until(answered, 60)
	var plate := live(id)
	var results: Array = plate.results.duplicate() if plate != null else []
	var down: bool = plate != null and plate.down
	var guarded: bool = t.defense.is_guarding()
	await t.wait(2)
	t.release(KEY_SHIFT)
	var after: float = gauge.value
	t.log_p("results %s, down %s, gauge %.3f -> %.3f, events %s, parries %s, dodges %s, health %d"
		% [results, down, before, after, t.events.map(func(e): return e.kind), t.parries.size(), t.dodges.size(), t.player.playerHealth])
	match answer:
		"parry":
			t.check(results == [HitInfo.Result.PARRIED] and t.parries.size() == 1 and t.events.is_empty(), "PARRIED, nothing lands")
			t.check(down, "knocked down")
			t.check(is_equal_approx(after - before, read), "one read (%.3f)" % (after - before))
		"dash":
			t.check(results == [HitInfo.Result.DODGED] and t.events.is_empty(), "DODGED, nothing lands")
			t.check(not down and t.dodges.size() == 1, "a perfect dodge, and it flies on")
			t.check(is_equal_approx(after - before, read), "one read (%.3f)" % (after - before))
		"hit":
			t.check(results == [HitInfo.Result.HIT] and t.events.size() == 1 and t.player.playerHealth == 999, "HIT, for half a heart")
			t.check(down, "and it drops")
			t.check(is_equal_approx(before - after, gauge.hit_loss), "the gauge loses %.3f (%.3f)" % [gauge.hit_loss, before - after])
		"guard":
			# Blocking is gone game-wide, so a held key is only a press gone stale, whatever the guard shows.
			t.log_p("the block key held from before the throw; guarding as it came: %s" % guarded)
			t.check(results == [HitInfo.Result.HIT] and t.parries.is_empty() and t.player.playerHealth == 999, "HIT all the same")
	await put_feet(t, AWAY)
	await t.wait_until(func(): return state_is(t, "Idle"), 180)
	t.stop_boss_timers()


# Physics steps until the plate's circle, flying over its shadow, reaches the player's hurtbox where it is now.
static func steps_to_contact(t, plate: Node2D) -> float:
	var rect: Rect2 = t.hurtbox_rect()
	var at: Vector2 = plate.hitbox.global_position
	var gap: float = at.distance_to(at.clamp(rect.position, rect.end)) - plate.radius
	return gap / maxf(plate.speed * FRAME_TIME, 0.001)


# A dash head-on at where the plate is now, through it: the one of the eight ways nearest it.
static func dash_at(t, plate_at: Vector2) -> void:
	var toward: Vector2 = (plate_at - t.sm.player_feet()).normalized()
	var codes: Array[int] = []
	if absf(toward.x) > sin(PI / 8.0):
		codes.append(KEY_LEFT if toward.x < 0.0 else KEY_RIGHT)
	if absf(toward.y) > sin(PI / 8.0):
		codes.append(KEY_UP if toward.y < 0.0 else KEY_DOWN)
	for code in codes:
		t.press(code)
	t.tap(KEY_W)
	await t.wait_until(func(): return t.player.is_dodging, 20)
	await t.wait_until(func(): return not t.player.is_dodging, 20)
	for code in codes:
		t.release(code)
