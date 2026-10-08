extends RefCounted

# greyson_plates (coder B): Greyson's throw and its plates (GreysonThrow, GreysonPlateScript; plan sections 3.1 and
# 9.6), in his test scene, the cycle pinned to the throw alone (the volley's and the poses' to the throw through to
# the poses). --fixed-fps 60. tier=
#   throw    (the default) the red badge over his crown for the wind-up and the parry rearmed; six plates from his
#            hand at 0.35 s and then every 0.25 s (GreysonThrow.release_at), in two fans of three: the first at the
#            player's feet and the second and third 35 degrees either side of its line; the fourth, the player having
#            crossed to his other side, turned round at their feet again, and the fifth and sixth 35 degrees either
#            side of its line; each first leg too slow to reach the player in under 0.40 s; done at done_at (1.65 s).
#   bounces  with the player off the ring, below it and then level with his hand beside it (plates 1 and 4 along the
#            ring's length, the longest flights there are): each plate off the ropes ten times, then gone in its
#            vanish, every flight inside the plate_life cap.
#   parry    the first plate parried: PARRIED, knocked down, and one read.
#   dash     dashed through: DODGED, a perfect dodge, one read, and it flies on.
#   hit      no answer: HIT for half a heart, it drops, and the gauge loses a read.
#   guard    the block key held from before the throw: HIT all the same.
#   volley   (coder A) a decent player's read of whole throws up to his poses - the throw, then the slams - the
#            2026-09-27 throw (6 plates, 5 ropes) and today's side by side: a bot that stands where it is and parries
#            whatever comes at it, pressing PRESS_BEFORE the contact it foresees - each plate's own path, its bounces
#            included - but never sooner than REACTION after it first foresaw it. Three throws round each of three
#            spots, the gauge emptied before each. With today's throw every plate that comes at it is foreseen at
#            least REACTION before contact and parried, none lands, its presses never whiff (a press with a plate
#            gone from under it is counted apart) or are refused, and the bar is never charged; logged per throw:
#            the plates, those that came at it, the reads (parries), the shortest warning, the last legs off a rope
#            shorter than REACTION (the bounces a player has to see coming), the most plates in the air at once, the
#            lowest the stamina bar went, the plates that ran out their ropes, and those still flying as the poses
#            began.
#   poses    (coder A) the plates flying on into his poses (the user, 2026-09-28): whole cycles read by a parrier and
#            a dodger (tier_poses), each going to him as the poses begin and spoiling each pose it can while reading
#            the plates. Neither lets a plate land, whiffs a press or has one refused, and both spoil all six poses of
#            every cycle; logged: the plates still flying into the poses and how long, how long it waited to set off
#            and held a swing back for a plate, when it was at him, and the reads a cycle.
#   fair     (coder A) a press that parries nothing costs PlayerDefense.parry_whiff_cost with no plate about and with
#            plates flying, but nothing when a plate still flying vanishes while it is open: off its last rope, in a
#            Break, or by its cap (the user, 2026-09-28).
#   ends     (coder A) all six plates in the air, then into the brawl, the spirit bomb, or the player's loss: not one
#            left flying anywhere in the scene.
#   pointblank  (playtest 2026-10-04) the player round his HOME: no first leg from outside min_contact touches them
#            sooner than min_flight, timed to their hurtbox; point blank keeps the old timing; no safe pocket there.
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
# The volley bot: how long it takes to answer a plate it has just seen coming, and how far ahead of the contact it
# presses (inside PlayerDefense.parry_window); where it stands, three spots on the player's side of him; his cycle,
# the throw through to the poses; and the throw of the user's 2026-09-27 notes, for the side-by-side.
const REACTION := 0.22
const PRESS_BEFORE := 0.10
# How long it holds the guard key for a press.
const PRESS_HOLD := 0.2
const VOLLEY_SPOTS: Array[Vector2] = [Vector2(640, 780), Vector2(1280, 780), Vector2(960, 860)]
const VOLLEY_THROWS := 3
const VOLLEY_CHAIN := ["Throw", "Slams", "Pose"]
# The poses bot: cycles from each VOLLEY_SPOTS spot; how close to his punch spot is there; how soon a plate's contact
# stops it on its way, to read it standing; how far ahead on its way it looks (PlayerScript.SPEED is its walk); and
# how soon a plate keeps it from swinging (the swing's 0.37 s, and a press PRESS_BEFORE the contact after it).
const POSE_CYCLES := 2
const ARRIVE := 10.0
const HOLD_STILL := 0.5
const LOOK_AHEAD := 0.3
const WALK_SPEED := 600.0
const PUNCH_CLEAR := 0.5
const THROW_0927 := {release_at = [0.35, 0.70, 1.05, 1.40, 1.75, 2.10], fresh_aim = [true, false, false, true, false, false],
	spreads = [0.0, 35.0, -35.0, 0.0, 35.0, -35.0], done_at = 2.45, bounces = 5, plate_life = 10.0}
# Below the ring altogether: nothing of his reaches it.
const AWAY := Vector2(960, 1500)
# Off the ring beside him, level with his hand as he faces them (y 509), so plates 1 and 4 fly along its length.
const BESIDE := Vector2(-100, 509)


static func run(t) -> void:
	await enter(t, [["Throw"]])
	match "throw" if t.tier == "normal" else t.tier:
		"throw":
			await tier_throw(t)
		"bounces":
			await tier_bounces(t)
		"parry", "dash", "hit", "guard":
			await tier_answer(t, t.tier)
		"volley":
			await tier_volley(t)
		"poses":
			await tier_poses(t)
		"fair":
			await tier_fair(t)
		"ends":
			await tier_ends(t)
		"pointblank":
			await tier_pointblank(t)
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
	# A press still inside its window as the last run ended owes its whiff: not out of this run's bar.
	t.defense.whiff_owed = false
	t.defense._set_stamina(t.defense.max_stamina)
	t.boss.break_gauge.locked = false
	t.boss.break_gauge.value = 0.0
	await t.wait(20)
	t.events.clear()
	t.parries.clear()
	t.dodges.clear()


static func put_feet(t, feet: Vector2) -> void:
	# AWAY and BESIDE are past the ropes, where the ring's net (PlayerScript.may_leave_ring) would put them back on the
	# mat.
	t.player.may_leave_ring = not t.sm.ROPES.has_point(feet)
	t.player.global_position += feet - t.sm.player_feet()
	t.player.velocity = Vector2.ZERO
	await t.wait(2)


# By id: a lambda holding a plate or a zone itself errors once it frees.
static func live(id: int) -> Node2D:
	return instance_from_id(id) as Node2D if is_instance_id_valid(id) else null


static func state_is(t, state_name: String) -> bool:
	return String(t.sm.current_state.name) == state_name


static func tier_throw(t) -> void:
	t.log_p("-- the throw: the badge, then six plates off his hand")
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
	var on_time := count == 6 and times.size() == count
	for i in times.size():
		on_time = on_time and absf(times[i] - throw.release_at[i]) <= SLACK
	t.check(on_time, "six plates, at %s s, to the frame" % [throw.release_at])
	var from_hand: bool = seen.hands.size() == throw.release_points.size()
	for i in throw.release_points.size():
		from_hand = from_hand and throw.release_points[i].distance_to(seen.hands[i]) <= 1.0
	t.check(from_hand, "each from his hand as it left (%s)" % [seen.hands])
	if throw.headings.size() == 6:
		var line: Vector2 = (throw.aimed_at[0] - throw.release_points[0]).normalized()
		var second: float = rad_to_deg(line.angle_to(throw.headings[1]))
		var third: float = rad_to_deg(line.angle_to(throw.headings[2]))
		var again: Vector2 = (throw.aimed_at[3] - throw.release_points[3]).normalized()
		var fifth: float = rad_to_deg(again.angle_to(throw.headings[4]))
		var sixth: float = rad_to_deg(again.angle_to(throw.headings[5]))
		t.check(throw.headings[0].is_equal_approx(line), "the first at the player's feet as it left")
		t.check(absf(second - throw.spreads[1]) <= 0.01 and absf(third - throw.spreads[2]) <= 0.01,
			"the second and third %.0f and %.0f degrees off that line, though the player has gone (%.2f, %.2f)" % [throw.spreads[1], throw.spreads[2], second, third])
		t.check(throw.aimed_at[3].distance_to(PLATE_4_FEET) <= 1.0 and throw.headings[3].is_equal_approx(again),
			"the fourth at the player's feet again, where they have gone (%s)" % throw.aimed_at[3])
		t.check(absf(fifth - throw.spreads[4]) <= 0.01 and absf(sixth - throw.spreads[5]) <= 0.01,
			"the fifth and sixth %.0f and %.0f degrees off the fourth's line (%.2f, %.2f)" % [throw.spreads[4], throw.spreads[5], fifth, sixth])
		t.check(seen.facing_left == [true, true, true, false, false, false], "turned round to them for it (facing left %s)" % [seen.facing_left])
	# The reach a first leg is timed over is to where it first touches the player's hurtbox (GreysonThrow.first_contact),
	# never past their feet; point blank, inside min_contact of his hand, it keeps the reach to the feet.
	var slow_enough: bool = throw.first_legs.size() == count
	for i in seen.speeds.size():
		var reach: float = throw.release_points[i].distance_to(throw.aimed_at[i])
		if i < throw.first_legs.size():
			slow_enough = slow_enough and throw.first_legs[i] <= reach + 0.01
			slow_enough = slow_enough and (not throw.point_blank[i] or is_equal_approx(throw.first_legs[i], reach))
			slow_enough = slow_enough and is_equal_approx(seen.speeds[i], minf(throw.plate_speed, throw.first_legs[i] / throw.min_flight))
	t.check(seen.speeds.size() == count and slow_enough,
		"each first leg min(%.0f, its reach to their hurtbox / %.2f): never at the player in under %.2f s (legs %s)" % [throw.plate_speed, throw.min_flight, throw.min_flight, throw.first_legs])
	t.check(done and absf(lasted - throw.done_at) <= SLACK, "done %.2f s in, and the chain goes on (%.4f)" % [throw.done_at, lasted])


static func tier_bounces(t) -> void:
	var throw: Node = t.sm.states["Throw"]
	t.log_p("-- the plates with the player off the ring: %d ropes each, then the vanish" % throw.bounces)
	var inner: Rect2 = t.sm.ROPES.grow(-load("res://Scripts/GreysonArtLayout.gd").fx(&"plate").radius)
	var count: int = throw.release_at.size()
	for feet in [AWAY, BESIDE]:
		await park(t, feet)
		t.sm.start_cycle()
		await t.wait_until(func(): return throw.thrown == count, roundi(throw.done_at * 60.0) + 30)
		var ids: Array = throw.plates.map(func(p): return p.get_instance_id())
		var kept := {}
		var flights := {}
		var all_up := [0]
		var watch := func():
			# One throw: the breath after it would start the next.
			if t.sm.current_state != throw:
				t.stop_boss_timers()
			var up := 0
			for id in ids:
				var plate := live(id)
				if plate != null:
					kept[id] = plate.turns.duplicate()
					flights[id] = plate.life
					up += 0 if plate.spent else 1
			all_up[0] += 1 if up == count else 0
		t.physics_frame.connect(watch)
		await t.wait_until(func(): return ids.all(func(id): return live(id) == null), roundi((throw.plate_life + 1.0) * 60.0))
		t.physics_frame.disconnect(watch)
		var counts: Array = ids.map(func(id): return kept.get(id, []).size())
		var lasted: Array = ids.map(func(id): return snappedf(flights.get(id, 0.0), 0.01))
		var edges: bool = ids.all(func(id): return kept.get(id, []).all(func(turn): return on_edge(turn.at, inner)))
		t.log_p("from %s: turns a plate %s, each flying %s s; all %d up at once for %.2f s" % [feet, counts, lasted, count, all_up[0] * FRAME_TIME])
		t.check(counts.size() == count and counts.all(func(n): return n == throw.bounces) and edges,
			"each of the %d plates off the ropes %d times, each on their inner edge" % [count, throw.bounces])
		t.check(lasted.max() < throw.plate_life, "the longest flight %.1f s, inside the %.0f s cap" % [lasted.max(), throw.plate_life])
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


#THE VOLLEY, READ BY A DECENT PLAYER

static func tier_volley(t) -> void:
	var cycle: Array[Array] = [VOLLEY_CHAIN.duplicate()]
	t.sm.ATTACKS = cycle
	var throw: Node = t.sm.states["Throw"]
	var today := {release_at = throw.release_at.duplicate(), fresh_aim = throw.fresh_aim.duplicate(),
		spreads = throw.spreads.duplicate(), done_at = throw.done_at, bounces = throw.bounces, plate_life = throw.plate_life}
	var before: Dictionary = await volley(t, "the 2026-09-27 throw", THROW_0927)
	var now: Dictionary = await volley(t, "today's throw", today)
	set_throw(throw, today)
	t.log_p("reads a throw before his poses (parries): %.2f on 2026-09-27, %.2f today" % [before.reads, now.reads])
	t.check(now.plates == now.throws * today.release_at.size(), "today's throw: %d plates a throw (%d in %d throws)" % [today.release_at.size(), now.plates, now.throws])
	t.check(now.arrivals > 0 and now.hits == 0 and now.late == 0 and now.whiffs == 0 and now.refused == 0
		and now.stamina == t.defense.max_stamina,
		"every plate that came at the bot foreseen at least %.2f s ahead and parried: %d of %d, none landed, no press whiffed or refused, the bar never charged"
		% [REACTION, now.parried, now.arrivals])


# `label`'s throw from every VOLLEY_SPOTS spot, VOLLEY_THROWS times each, read by the bot. The tallies.
static func volley(t, label: String, knobs: Dictionary) -> Dictionary:
	var throw: Node = t.sm.states["Throw"]
	set_throw(throw, knobs)
	var tally := {"throws": 0, "reads": 0.0, "warning": INF, "in_air": 0, "stamina": INF, "to_poses": 0.0}
	var summed := ["plates", "arrivals", "parried", "hits", "late", "whiffs", "emptied", "refused", "short_legs", "shared",
		"ran_out", "at_poses"]
	for key in summed:
		tally[key] = 0
	for base in VOLLEY_SPOTS:
		for k in VOLLEY_THROWS:
			# A step aside each throw, so each spot is read from three places rather than one.
			var spot: Vector2 = base + Vector2((k - 1) * 60.0, (k - 1) * -30.0)
			await park(t, spot)
			var one: Dictionary = await read_throw(t, throw)
			for key in summed:
				tally[key] += one[key]
			tally.warning = minf(tally.warning, one.warning)
			tally.in_air = maxi(tally.in_air, one.in_air)
			tally.stamina = minf(tally.stamina, one.stamina)
			tally.to_poses = maxf(tally.to_poses, one.to_poses)
			tally.throws += 1
			t.log_p("%s from %s: %d plates, %d came at the bot, %d parried, %d landed, %d late, %d presses whiffed, %d refused, %d with a plate gone from under them, warning at least %.2f s, %d last legs off a rope under %.2f s, at most %d in the air, stamina down to %.0f; %d ran out their ropes, %d still flying as the poses began"
				% [label, spot, one.plates, one.arrivals, one.parried, one.hits, one.late, one.whiffs, one.refused, one.emptied, one.warning, one.short_legs, REACTION, one.in_air, one.stamina, one.ran_out, one.at_poses])
	tally.reads = float(tally.parried) / tally.throws
	t.log_p("%s, in all: %d throws, %d plates, %d came at the bot, %d parried (%.2f a throw), %d landed, %d late, %d whiffed, %d refused, %d with a plate gone from under them; warning at least %.2f s; %d short last legs; %d plates arriving inside one press's window; at most %d plates in the air; stamina down to %.0f; %d plates ran out their ropes and %d were still flying as the poses began, %.2f s after the throw"
		% [label, tally.throws, tally.plates, tally.arrivals, tally.parried, tally.reads, tally.hits, tally.late, tally.whiffs, tally.refused, tally.emptied, tally.warning, tally.short_legs, tally.shared, tally.in_air, tally.stamina, tally.ran_out, tally.at_poses, tally.to_poses])
	return tally


static func set_throw(throw: Node, knobs: Dictionary) -> void:
	var release: Array[float] = []
	release.assign(knobs.release_at)
	var fresh: Array[bool] = []
	fresh.assign(knobs.fresh_aim)
	var spreads: Array[float] = []
	spreads.assign(knobs.spreads)
	throw.release_at = release
	throw.fresh_aim = fresh
	throw.spreads = spreads
	throw.done_at = knobs.done_at
	throw.bounces = knobs.bounces
	throw.plate_life = knobs.plate_life


# One throw from where the player stands, the bot reading it through his slams, until every plate of it is gone or his
# poses begin.
static func read_throw(t, throw: Node) -> Dictionary:
	var read := new_read(t, throw)
	read.merge({"at_poses": 0, "to_poses": 0.0})
	var pose: Node = t.sm.states["Pose"]
	var began: float = t.boss.fight_clock
	t.sm.start_cycle()
	for i in 60 * 16:
		if t.sm.current_state == pose:
			read.at_poses = read.flying.size()
			read.to_poses = t.boss.fight_clock - began
			break
		read_plates(t, read)
		if throw.thrown >= throw.release_at.size() and read.ids.all(func(id): return live(id) == null):
			break
		await t.physics_frame
	await finish_read(t, read)
	t.sm.on_child_transition(t.sm.current_state, "Idle")
	t.stop_boss_timers()
	return read


# A bot's reading of one throw's plates, about to start: what it follows of each plate, its presses and the plates
# gone from under them, and its tallies.
static func new_read(t, throw: Node) -> Dictionary:
	var read := {"throw": throw, "ids": [], "notes": {}, "flying": {}, "held_until": -INF, "presses": [], "vanished": [],
		"refusals": [0], "parried_before": t.parries.size(), "soonest": INF, "hands_off": false, "pressed_at": -INF,
		"inner": t.sm.ROPES.grow(-load("res://Scripts/GreysonArtLayout.gd").fx(&"plate").radius),
		"plates": 0, "arrivals": 0, "parried": 0, "hits": 0, "passed": 0, "late": 0, "warning": INF, "short_legs": 0,
		"in_air": 0, "shared": 0, "whiffs": 0, "emptied": 0, "refused": 0, "stamina": t.defense.stamina, "ran_out": 0,
		"soonest_plate": 0}
	read.press_notes = []
	read.count_press = func(_credited: bool):
		read.presses.append(t.defense.clock)
		var plate := live(read.soonest_plate)
		read.press_notes.append("%.2f s, %s%s, the soonest plate %.2f s off (%s)" % [t.boss.fight_clock, t.player.state_machine.current_state.name,
			" (invincible)" if t.player.is_invincible else "", read.soonest,
			"gone" if plate == null else "at %s heading %s, %d ropes, answers %s, latched %s, the hurtbox %s" % [plate.global_position.round(), plate.heading, plate.turns.size(), plate.results, plate.latched, t.hurtbox_rect()]])
	read.count_refusal = func(): read.refusals[0] += 1
	t.defense.block_pressed.connect(read.count_press)
	t.defense.stamina_refused.connect(read.count_refusal)
	t.boss.break_gauge.value = 0.0
	return read


# One frame of the bot reading the plates from where it stands: each plate noted as it leaves his hand, each answer
# tallied as it comes, and the guard pressed PRESS_BEFORE a contact it foresees but never sooner than REACTION after
# it first foresaw it, and held a moment, as a player's is (a press and a release on one frame never raise it). The
# soonest contact it foresees goes in `read.soonest`.
static func read_plates(t, read: Dictionary) -> void:
	var now: float = t.boss.fight_clock
	if read.held_until != -INF and now >= read.held_until:
		t.release(KEY_SHIFT)
		read.held_until = -INF
	for plate in read.throw.plates:
		if is_instance_valid(plate) and not read.ids.has(plate.get_instance_id()):
			read.ids.append(plate.get_instance_id())
			read.notes[plate.get_instance_id()] = {"leg": now, "turns": 0, "noticed": INF, "pressed": false, "results": 0}
	var live_count := 0
	var rect: Rect2 = t.hurtbox_rect()
	read.stamina = minf(read.stamina, t.defense.stamina)
	read.soonest = INF
	read.soonest_plate = 0
	for id in read.ids:
		var plate := live(id)
		var note: Dictionary = read.notes[id]
		if read.flying.has(id) and (plate == null or plate.spent or plate.down):
			if plate == null or plate.spent:
				read.vanished.append(t.defense.clock)
				read.ran_out += 1 if note.turns == read.throw.bounces else 0
			read.flying.erase(id)
		if plate == null:
			continue
		if not plate.down and not plate.spent:
			live_count += 1
			read.flying[id] = plate.turns.size()
		if plate.turns.size() != note.turns:
			note.turns = plate.turns.size()
			note.leg = now
		while note.results < plate.results.size():
			var got: int = plate.results[note.results]
			note.results += 1
			# Through a player who couldn't be touched (i-frames, a finisher): it flies on, to be read again.
			if got == HitInfo.Result.IGNORED:
				read.passed += 1
				continue
			read.arrivals += 1
			if got == HitInfo.Result.PARRIED:
				read.parried += 1
			elif got == HitInfo.Result.HIT:
				read.hits += 1
			var warned: float = now - note.noticed if note.noticed != INF else 0.0
			read.warning = minf(read.warning, warned)
			if warned < REACTION:
				read.late += 1
			if now - note.leg < REACTION:
				read.short_legs += 1
			note.noticed = INF
		if plate.down or plate.spent:
			continue
		# Latched inside it (let through the i-frames), it asks nothing more on this pass: a press would only whiff.
		var ahead: float = INF if plate.latched else foresee(plate, rect, read.inner, 1.5)
		# Not coming at it, or no longer: the next time it does is a fresh read.
		if ahead == INF:
			note.noticed = INF
			note.pressed = false
			continue
		if ahead < read.soonest:
			read.soonest_plate = id
		read.soonest = minf(read.soonest, ahead)
		if note.noticed == INF:
			note.noticed = now
		# Untouchable (the i-frames after a hit), it lets the plate go through it: a press would only whiff.
		if read.hands_off or t.player.is_invincible:
			continue
		if not note.pressed and ahead <= PRESS_BEFORE and now - note.noticed >= REACTION:
			note.pressed = true
			# One press parries everything inside its window while the key is still down (the guard drops with the
			# key, PlayerBlocking): a plate arriving inside the last one's is already answered, and a second press
			# there would only restart the window uncredited. A press made this very frame isn't PlayerDefense's yet.
			var covered: bool = read.pressed_at == now or (t.defense.press_credited
				and t.defense.clock + ahead - t.defense.last_press_time <= minf(t.defense.parry_window, PRESS_HOLD) - 0.02)
			if covered:
				read.shared += 1
			else:
				if read.held_until != -INF:
					t.release(KEY_SHIFT)
				t.press(KEY_SHIFT)
				read.held_until = now + PRESS_HOLD
				read.pressed_at = now
	read.in_air = maxi(read.in_air, live_count)


# The bot's reading over, once its last press's window has closed (reading on until then, so a plate that press was
# for is answered): the key let go, its counters off, and each press it made judged. One that parried nothing inside
# its window whiffed, unless a plate still flying went from under it (GreysonPlateScript._vanish).
static func finish_read(t, read: Dictionary) -> void:
	for i in 30:
		if read.presses.is_empty() or t.defense.clock > read.presses[-1] + t.defense.parry_window + 0.02:
			break
		read_plates(t, read)
		await t.physics_frame
	t.release(KEY_SHIFT)
	t.defense.block_pressed.disconnect(read.count_press)
	t.defense.stamina_refused.disconnect(read.count_refusal)
	read.refused = read.refusals[0]
	read.plates = read.ids.size()
	var window: float = t.defense.parry_window + 0.02
	var parried: Array = t.parries.slice(read.parried_before)
	for at in read.presses:
		if parried.any(func(p): return p.t >= at and p.t <= at + window):
			continue
		if read.vanished.any(func(gone): return gone >= at and gone <= at + window):
			read.emptied += 1
		else:
			read.whiffs += 1
			t.log_p("  a press parried nothing: %s" % read.press_notes[read.presses.find(at)])


#THE POSES, WITH THE PLATES STILL FLYING

# (the user, 2026-09-28: the plates fly on into his poses) Whole cycles, two bots, each from every VOLLEY_SPOTS spot:
# the parrier reads the plates where it stands through the throw and the slams; the dodger stands there untouchable
# for them, as a player who dodged every one would be, so each flies on through it and every plate is still his to
# face in the poses. Then each goes to him and spoils each pose it can, reading the plates all the while: it walks on
# only with no plate foreseen across the next LOOK_AHEAD of its way, stands still to read one coming at it, and
# swings only with no plate foreseen before the swing is over and it could guard again. His eruptions are off for
# these bots: ten a cycle since 2026-09-30, and a burst that lands on one mid-read knocks it off the plate it was
# reading, which is about the zones (the slams tiers), not the plates. Neither lets a plate land, whiffs a press or
# has one refused; each is at him in every cycle before his third clean pose fills the meter (two cells a pose), and
# spoils every pose from the third on; the parrier, which reads the plates where it stands, and the dodger, which
# may have to wait them out, are logged for how soon.
static func tier_poses(t) -> void:
	var cycle: Array[Array] = [VOLLEY_CHAIN.duplicate()]
	t.sm.ATTACKS = cycle
	var throw: Node = t.sm.states["Throw"]
	var pose: Node = t.sm.states["Pose"]
	var eruptions: Array[float] = pose.eruptions.duplicate()
	pose.eruptions.clear()
	for bot in ["parrier", "dodger"]:
		var tally := {"cycles": 0, "reached": 0.0, "stamina": INF, "warning": INF, "in_air": 0, "all_spoiled": 0,
			"from_third": 0}
		var summed := ["arrivals", "parried", "hits", "late", "whiffs", "emptied", "refused", "passed", "posed_arrivals",
			"posed_parried", "posed_hits", "spoiled", "punches", "eruptions", "at_poses", "after_poses", "held_back",
			"waited", "last_up"]
		for key in summed:
			tally[key] = 0
		for base in VOLLEY_SPOTS:
			for k in POSE_CYCLES:
				var spot: Vector2 = base + Vector2((k - 1) * 60.0, (k - 1) * -30.0)
				await park(t, spot)
				# Each cycle his first: the spoiling punches would have him at 0 HP, into the brawl, a few cycles on.
				t.boss.boss_health = t.boss.max_health
				t.boss.reset_hype()
				var one: Dictionary = await play_cycle(t, throw, bot == "dodger")
				for key in summed:
					tally[key] += one[key]
				tally.reached = maxf(tally.reached, one.reached)
				tally.stamina = minf(tally.stamina, one.stamina)
				tally.warning = minf(tally.warning, one.warning)
				tally.in_air = maxi(tally.in_air, one.in_air)
				tally.all_spoiled += 1 if one.spoiled == 6 else 0
				tally.from_third += 1 if one.outcomes.size() == 6 and one.outcomes.slice(2).all(func(o): return o == &"spoiled") else 0
				tally.cycles += 1
				t.log_p("%s from %s: %d plates came at it, %d parried, %d landed (in the poses %d, %d, %d), %d late, %d whiffed, %d refused, %d with a plate gone from under them, warning at least %.2f s, stamina down to %.0f; %d still flying as the poses began, the last of them %.2f s into them, %d as they ended; it waited %.2f s to set off, was at him %.2f s in, held a swing back %.2f s for a plate, swung %d times and spoiled %s (%d of 6); %d eruptions landed"
					% [bot, spot, one.arrivals, one.parried, one.hits, one.posed_arrivals, one.posed_parried, one.posed_hits, one.late, one.whiffs, one.refused, one.emptied, one.warning, one.stamina, one.at_poses, one.last_up, one.after_poses, one.waited, one.reached, one.held_back, one.punches, one.outcomes, one.spoiled, one.eruptions])
		var reads: float = float(tally.parried) / tally.cycles
		t.log_p("%s, in all: %d cycles, %d plates came at it, %d parried (%.2f a cycle, %.2f of them in the poses), %d landed, %d late, %d whiffed, %d refused; warning at least %.2f s; stamina down to %.0f; at most %d plates in the air; %d still flying as the poses began and %d as they ended; at him %.2f s into the poses at the latest; %d of %d poses spoiled, every pose in %d of %d cycles; swings held back %.2f s and set-offs waited %.2f s in all; %d eruptions landed; the Break's %d reads from empty take %.1f cycles at that"
			% [bot, tally.cycles, tally.arrivals, tally.parried, reads, float(tally.posed_parried) / tally.cycles, tally.hits, tally.late, tally.whiffs, tally.refused, tally.warning, tally.stamina, tally.in_air, tally.at_poses, tally.after_poses, tally.reached, tally.spoiled, 6 * tally.cycles, tally.all_spoiled, tally.cycles, tally.held_back, tally.waited, tally.eruptions, t.boss.BREAK_READS, t.boss.BREAK_READS / maxf(reads, 0.01)])
		t.check(tally.arrivals > 0 and tally.hits == 0 and tally.late == 0 and tally.whiffs == 0 and tally.refused == 0
			and tally.stamina == t.defense.max_stamina,
			"%s: every plate that came at it read and parried, %d of %d, none landed, no press whiffed or refused, the bar never charged"
			% [bot, tally.parried, tally.arrivals])
		t.check(tally.from_third == tally.cycles, "%s: at him before his meter fills, and every pose from the third on spoiled, in every cycle (%d of %d; every pose in %d)" % [bot, tally.from_third, tally.cycles, tally.all_spoiled])
	pose.eruptions.assign(eruptions)


# One whole cycle from where the player stands, the bot playing it as tier_poses says, until the poses are over;
# `dodged`, untouchable and pressing nothing until the poses.
static func play_cycle(t, throw: Node, dodged := false) -> Dictionary:
	var read := new_read(t, throw)
	read.hands_off = dodged
	read.merge({"at_poses": 0, "after_poses": 0, "last_up": 0.0, "reached": INF, "waited": 0.0, "held_back": 0.0,
		"punches": 0, "spoiled": 0, "outcomes": [], "eruptions": 0, "posed_arrivals": 0, "posed_parried": 0, "posed_hits": 0})
	var pose: Node = t.sm.states["Pose"]
	var keys := {}
	var began := -1.0
	var before := {}
	var eruptions_before: int = t.events_of("HIT", &"greyson_eruption").size()
	t.sm.start_cycle()
	for i in 60 * 30:
		var posing: bool = t.sm.current_state == pose
		if posing and began < 0.0:
			began = t.boss.fight_clock
			read.at_poses = read.flying.size()
			before = {"arrivals": read.arrivals, "parried": read.parried, "hits": read.hits}
			if dodged:
				read.hands_off = false
				t.clear_iframes()
		elif began >= 0.0 and not posing:
			break
		if read.hands_off:
			t.player.is_invincible = true
		read_plates(t, read)
		if posing:
			if not read.flying.is_empty():
				read.last_up = t.boss.fight_clock - began
			to_him(t, read, keys, pose, began)
		await t.physics_frame
	hold_keys(t, keys, Vector2.ZERO)
	read.after_poses = read.flying.size()
	await finish_read(t, read)
	read.outcomes = pose.outcomes.duplicate()
	read.spoiled = pose.outcomes.count(&"spoiled")
	read.posed_arrivals = read.arrivals - before.get("arrivals", read.arrivals)
	read.posed_parried = read.parried - before.get("parried", read.parried)
	read.posed_hits = read.hits - before.get("hits", read.hits)
	read.eruptions = t.events_of("HIT", &"greyson_eruption").size() - eruptions_before
	if read.reached == INF:
		read.reached = 99.0
	t.sm.on_child_transition(t.sm.current_state, "Idle")
	t.stop_boss_timers()
	return read


# One frame of the bot through his poses: on its way to him, or at him swinging.
static func to_him(t, read: Dictionary, keys: Dictionary, pose: Node, began: float) -> void:
	var spot: Vector2 = t._bot_punch_spot()
	var at: Vector2 = t.player.global_position
	var state := String(t.player.state_machine.current_state.name)
	var guarding: bool = read.held_until != -INF or state == "Blocking"
	if absf(spot.x - at.x) <= ARRIVE and absf(spot.y - at.y) <= ARRIVE:
		hold_keys(t, keys, Vector2.ZERO)
		if read.reached == INF:
			read.reached = t.boss.fight_clock - began
		if not t.sm.is_open() or pose.spoiled or state == "Punching" or guarding:
			return
		if read.soonest <= PUNCH_CLEAR:
			read.held_back += FRAME_TIME
			return
		# A punch a pose, each its own: any three that land make a POW (PlayerCombo), which would daze him out of
		# the poses this bot is spoiling one by one.
		t.player.combo.reset()
		t.tap(KEY_Q)
		read.punches += 1
		return
	# The next LOOK_AHEAD of its way: it only walks on into it with no plate foreseen there before it could stand
	# and read one.
	var here: Rect2 = t.hurtbox_rect()
	var step: Vector2 = (spot - at).limit_length(WALK_SPEED * LOOK_AHEAD)
	var next: Rect2 = here.merge(Rect2(here.position + step, here.size))
	if guarding or read.soonest <= HOLD_STILL or soonest_across(read, next) <= LOOK_AHEAD + HOLD_STILL:
		hold_keys(t, keys, Vector2.ZERO)
		read.waited += FRAME_TIME
		return
	hold_keys(t, keys, spot - at)


# The arrow keys held for a walk along `toward`, each axis on while there is more than ARRIVE of it to go.
static func hold_keys(t, keys: Dictionary, toward: Vector2) -> void:
	var want := {KEY_LEFT: toward.x < -ARRIVE, KEY_RIGHT: toward.x > ARRIVE, KEY_UP: toward.y < -ARRIVE,
		KEY_DOWN: toward.y > ARRIVE}
	for code in want:
		if want[code] == keys.get(code, false):
			continue
		keys[code] = want[code]
		if want[code]:
			t.press(code)
		else:
			t.release(code)


# The soonest any plate still flying is foreseen to touch `rect`.
static func soonest_across(read: Dictionary, rect: Rect2) -> float:
	var soonest := INF
	for id in read.flying:
		var plate := live(id)
		if plate != null and not plate.down and not plate.spent:
			soonest = minf(soonest, foresee(plate, rect, read.inner, 2.0))
	return soonest


#A PLATE GONE FROM UNDER A PRESS

# (the user, 2026-09-28) A parry press that parries nothing costs PlayerDefense.parry_whiff_cost, but never when a
# plate still flying vanishes while it is open: off its last rope, fizzled by a Break, or by its cap.
static func tier_fair(t) -> void:
	t.track_spends()
	var throw: Node = t.sm.states["Throw"]
	var count: int = throw.release_at.size()
	var spent := {}
	for how in ["alone", "flying", "last_rope", "broken", "cap"]:
		await park(t, AWAY)
		t.spends.clear()
		var id := 0
		if how != "alone":
			t.sm.start_cycle()
			await t.wait_until(func(): return throw.thrown == count, roundi(throw.done_at * 60.0) + 30)
			id = throw.plates[0].get_instance_id()
		if how == "last_rope":
			# Its next rope its last: pressed PRESS_BEFORE it gets there. The plate soonest to its rope that is still
			# a few frames short of the press: a nearer one would be gone before the press is in, and a far one cut
			# first, with the rest, by his next cycle (plate_wait_cap).
			var flying: Array = throw.plates.filter(func(plate) -> bool: return to_rope(plate, t.sm.ROPES) > PRESS_BEFORE + 0.05)
			flying.sort_custom(func(a, b) -> bool: return to_rope(a, t.sm.ROPES) < to_rope(b, t.sm.ROPES))
			id = flying[0].get_instance_id()
			live(id).bounces = live(id).reflections
			await t.wait_until(func(): return live(id) == null or live(id).spent or to_rope(live(id), t.sm.ROPES) <= PRESS_BEFORE, 600)
		var before: float = t.defense.last_press_time
		t.press(KEY_SHIFT)
		await t.wait_until(func(): return t.defense.last_press_time != before, 10)
		var pressed_at: float = t.defense.last_press_time
		match how:
			"broken":
				t.sm.enter_broken()
			"cap":
				live(id).max_life = live(id).life + 0.05
		var gone := func() -> bool: return id != 0 and (live(id) == null or live(id).spent)
		await t.wait_until(func(): return gone.call() or t.defense.clock - pressed_at > t.defense.parry_window, 60)
		var gone_in: float = t.defense.clock - pressed_at if gone.call() else INF
		await t.wait_until(func(): return t.defense.clock - pressed_at > t.defense.parry_window + 0.05, 180)
		await t.wait(2)
		t.release(KEY_SHIFT)
		spent[how] = t.spends.duplicate()
		t.log_p("%s: %s; spends %s, stamina %.0f" % [how, "its plate gone %.3f s after the press" % gone_in if gone_in != INF else "nothing gone inside the window", t.spends, t.defense.stamina])
		if how == "broken":
			await t.reset_gauged(t.sm.HOME)
	t.check(spent.alone == t.whiffs(1) and spent.flying == t.whiffs(1),
		"a press that parries nothing costs the whiff, with nothing about (%s) and with his plates flying (%s)" % [spent.alone, spent.flying])
	t.check(spent.last_rope.is_empty() and spent.broken.is_empty() and spent.cap.is_empty(),
		"but not with a plate gone from under it: off its last rope %s, in a Break %s, by its cap %s" % [spent.last_rope, spent.broken, spent.cap])


# Seconds until `plate`, as it flies, reaches the next rope.
static func to_rope(plate: Node2D, ropes: Rect2) -> float:
	if not is_instance_valid(plate) or plate.spent:
		return INF
	var inner: Rect2 = ropes.grow(-plate.radius)
	var at: Vector2 = plate.global_position
	var velocity: Vector2 = plate.heading * plate.speed
	var soonest := INF
	if velocity.x != 0.0:
		soonest = minf(soonest, ((inner.end.x if velocity.x > 0.0 else inner.position.x) - at.x) / velocity.x)
	if velocity.y != 0.0:
		soonest = minf(soonest, ((inner.end.y if velocity.y > 0.0 else inner.position.y) - at.y) / velocity.y)
	return soonest


#NOTHING LINGERS

# His throw's plates all in the air, then the fight turns: into the brawl, into the spirit bomb, or to the player's
# loss. Not one plate is left flying, in his group or anywhere in the scene.
static func tier_ends(t) -> void:
	for ending in ["brawl", "bomb", "loss"]:
		await enter(t, [["Throw"]])
		await park(t, AWAY)
		var throw: Node = t.sm.states["Throw"]
		t.sm.start_cycle()
		await t.wait_until(func(): return throw.thrown == throw.release_at.size(), roundi(throw.done_at * 60.0) + 30)
		var up: int = t.sm.flying_plates().size()
		match ending:
			"brawl":
				t.boss.skip_to_brawl()
			"bomb":
				t.sm.enter_spirit_bomb()
			"loss":
				t.sm.enter_player_defeated()
		await t.wait(2)
		var left: Array = flying_anywhere(t)
		t.log_p("%s: %d plates up, then %s: %d left flying, now in %s" % [ending, up, ending, left.size(), t.sm.current_state.name])
		t.check(up == throw.release_at.size() and left.is_empty(), "into the %s, all %d plates in the air: none left flying (%d)" % [ending, up, left.size()])
		var outro: Node = t.root.get_node_or_null("FightOutro")
		if outro != null:
			outro.free()


# Every plate of his still flying anywhere in the scene.
static func flying_anywhere(t) -> Array:
	var plate_script: Script = load("res://Scripts/GreysonPlateScript.gd")
	return t.current_scene.find_children("*", "Node2D", true, false).filter(func(n) -> bool:
		return n.get_script() == plate_script and not n.spent and not n.down)


# Seconds until `plate`, flying on as it is - its speed, then max_speed after a rope, mirrored off each rope it has
# left - first touches `rect`, or INF inside `horizon` or once its last rope would end it. On the physics steps it
# will really take: it only meets the player where a step puts it, and a finer look sees it clip a corner it flies
# past between two steps (a 950 px/s plate goes 16 px a step), which would have the bot press for nothing.
static func foresee(plate: Node2D, rect: Rect2, inner: Rect2, horizon: float) -> float:
	var lift := Vector2(0.0, -load("res://Scripts/GreysonPlateScript.gd").FLIGHT.height)
	var at: Vector2 = plate.global_position
	var heading: Vector2 = plate.heading
	var speed: float = plate.speed
	var reflections: int = plate.reflections
	var step := 1.0 / Engine.physics_ticks_per_second
	var clock := 0.0
	while clock < horizon:
		var centre := at + lift
		if centre.distance_to(centre.clamp(rect.position, rect.end)) <= plate.radius:
			return clock
		at += heading * speed * step
		clock += step
		var met := false
		if at.x < inner.position.x or at.x > inner.end.x:
			var wall := inner.position.x if at.x < inner.position.x else inner.end.x
			at.x = 2.0 * wall - at.x
			heading.x = -heading.x
			met = true
		if at.y < inner.position.y or at.y > inner.end.y:
			var wall := inner.position.y if at.y < inner.position.y else inner.end.y
			at.y = 2.0 * wall - at.y
			heading.y = -heading.y
			met = true
		if met:
			if reflections >= plate.bounces:
				return INF
			reflections += 1
			speed = plate.max_speed
	return INF


# Beside him as he throws (playtest 2026-10-04): the player's feet round his HOME, where a punish leaves them. No first
# leg touches them sooner than min_flight after it leaves his hand - timed to their hurtbox, not their feet - unless
# it left inside min_contact of them (point blank, where the throw's red badge is the read and the old timing stays).
# Standing there is no safe pocket: every spot still takes plate hits.
const POINTBLANK_FEET: Array[Vector2] = [Vector2(850, 560), Vector2(1070, 560), Vector2(810, 540), Vector2(1110, 580),
	Vector2(890, 620), Vector2(1030, 620), Vector2(760, 560), Vector2(960, 720), Vector2(700, 640), Vector2(1220, 640)]


static func tier_pointblank(t) -> void:
	t.log_p("-- point blank: first legs timed to the hurtbox")
	var throw: Node = t.sm.states["Throw"]
	var soonest := INF
	var early: Array = []
	var timed := 0
	var pocket: Array = []
	for feet in POINTBLANK_FEET:
		await park(t, feet)
		var touches := {}
		var count := [0]
		var on_hit := func(hit):
			if hit.attack_id != &"greyson_plate" or not is_instance_valid(hit.source):
				return
			count[0] += 1
			var i: int = throw.plates.find(hit.source)
			if i >= 0 and not touches.has(i):
				touches[i] = {"after": t.boss.fight_clock - throw.release_clocks[i], "ropes": hit.source.turns.size()}
		t.defense.hit_taken.connect(on_hit)
		t.sm.on_child_transition(t.sm.current_state, "Throw")
		for f in 360:
			if t.player.is_invincible:
				t.clear_iframes()
			await t.physics_frame
		t.defense.hit_taken.disconnect(on_hit)
		for i in touches:
			var touch: Dictionary = touches[i]
			if touch.ropes > 0 or (i < throw.point_blank.size() and throw.point_blank[i]):
				continue
			timed += 1
			soonest = minf(soonest, touch.after)
			if touch.after < throw.min_flight - FRAME_TIME - 0.001:
				early.append([feet, i, snappedf(touch.after, 0.001)])
		if count[0] < 1:
			pocket.append([feet, count[0]])
		t.log_p("feet %s: first legs %s, point blank %s, first touches %s, %d plate hits in 6 s" % [feet, throw.first_legs, throw.point_blank, touches, count[0]])
		t.sm.on_child_transition(t.sm.current_state, "Idle")
		t.stop_boss_timers()
	t.check(timed > 0 and early.is_empty(), "no first leg from outside point blank touches them sooner than %.2f s after it leaves his hand (%d timed, soonest %.3f s; early %s)" % [throw.min_flight, timed, soonest, early])
	t.check(pocket.is_empty(), "and standing beside him is no safe pocket: plate hits at every spot (%s)" % [pocket])
