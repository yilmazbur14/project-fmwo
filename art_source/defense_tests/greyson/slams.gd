extends RefCounted

# greyson_slams (coder B): Greyson's slams and their eruption zones (GreysonSlams, GreysonEruptionScript; plan
# sections 3.2, 3.3 and 9.6), in his test scene, the cycle pinned to his slams and poses. --fixed-fps 60. tier=
#   timeline  (the default) each teleport to the spot furthest from the player's feet and never the one he is on,
#             home last; five slams 1.30 s apart from 0.90 s, each zone by the fence rule - on the player's feet
#             at that slam, or beside the waiting zones when they stood in one (zone 5 here); none going off in the
#             slams, all five waiting as he lands home and goes into
#             Pose at 7.00 s; then set off oldest first at GreysonPose's eruptions from the first pose's strike
#             (0.6, 1.4, 2.2, 3.0 and 4.5 s), the last as pose 3 ends, never under 0.8 s apart, each told
#             eruption_notice before (or as the poses begin) with its ring the last ring_lead; each rumble ramped
#             up its fuse and stopped as it goes; the feet in zone 1 as it goes hit once.
#   feet      the player's feet just outside zone 1 as it goes off, their body over it: no hit.
#   dash      a dash through zone 1 as it goes off: DODGED, a perfect dodge, and no read.
#   break     a Break in the middle of the slams: every zone still waiting fizzles, none goes off, and he is
#             left visible.
#   fence     the fence swept, zone_spot alone: players standing still or drifting through the slams from spots
#             all over the floor; every zone keeps the fence rule, and from wherever the player is as zone 1's ring
#             starts a walk (no dash) comes through all five bursts (maze.gd). The numbers are logged.
#   still     a player standing still through it all: zone 1 lands on them, the other four box them in, and
#             zone 1's burst hits them.
#   step      the old way out, a player standing still through the slams who steps out of zone 1 as it rings and
#             stands there: a later zone of the fence hits them.
#   weave     a player standing still through the slams who then walks the maze (maze.weave): out of each zone
#             before it goes, and to him to punch as soon as the bursts let them. No burst hits them, and they
#             reach him in pose 2 or 3.

const Plates := preload("res://art_source/defense_tests/greyson/plates.gd")
const Maze := preload("res://art_source/defense_tests/greyson/maze.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const FRAME_TIME := 1.0 / 60.0
const SLACK := FRAME_TIME + 0.0001
# Where the player stands for each slam in the timeline, the third outside the zones' inset so it is clamped.
const SLAM_FEET: Array[Vector2] = [Vector2(700, 820), Vector2(1300, 700), Vector2(1790, 950), Vector2(400, 300),
	Vector2(1100, 400)]
const ZONE_1_FEET := Vector2(700, 820)
# Where the feet tier stands through the slams: high enough that zone 1's bottom edge is on the floor, where the
# ring's walls let the feet stand just below it.
const FEET_TIER_STAND := Vector2(700, 520)


static func run(t) -> void:
	await Plates.enter(t, [["Slams", "Pose"]])
	match "timeline" if t.tier == "normal" else t.tier:
		"timeline":
			await tier_timeline(t)
		"feet":
			await tier_feet(t)
		"dash":
			await tier_dash(t)
		"break":
			await tier_break(t)
		"fence":
			tier_fence(t)
		"still":
			await tier_still(t)
		"step":
			await tier_step(t)
		"weave":
			await tier_weave(t)
		_:
			t.check(false, "greyson_slams has no tier %s" % t.tier)


# Slams from Idle, watched on every step: each state he is in, and each zone's phase, rumble level and pitch.
static func watch_slams(t, seen: Dictionary) -> Callable:
	var slams: Node = t.sm.states["Slams"]
	return func():
		seen.steps += 1
		var state := String(t.sm.current_state.name)
		if seen.states.is_empty() or seen.states[-1][0] != state:
			seen.states.append([state, t.boss.fight_clock - seen.start])
		for i in slams.zones.size():
			var zone = slams.zones[i]
			if not is_instance_valid(zone):
				continue
			if not seen.ids.has(i):
				seen.ids[i] = zone.get_instance_id()
				var went := func():
					seen.erupted[i] = t.boss.fight_clock - seen.start
					seen.fuses[i] = [zone.ring_after, zone.erupt_after]
				zone.erupted.connect(went)
			var row: Array = seen.zones.get(i, [])
			var rumble: AudioStreamPlayer = zone.rumble
			row.append({"clock": t.boss.fight_clock - seen.start, "phase": zone.phase, "stage": zone.stage,
				"db": rumble.volume_db - rumble.get_meta(&"base_db") if is_instance_valid(rumble) else INF,
				"playing": is_instance_valid(rumble) and rumble.playing, "progress": zone.fuse_progress()})
			seen.zones[i] = row


static func tier_timeline(t) -> void:
	t.log_p("-- his slams, start to end, then his poses setting the zones off")
	await Plates.park(t, SLAM_FEET[0])
	var slams: Node = t.sm.states["Slams"]
	var pose: Node = t.sm.states["Pose"]
	var ring_lead: float = load("res://Scripts/GreysonArtLayout.gd").fx(&"zone").ring_lead
	var count: int = slams.slams
	var seen := {"steps": 0, "states": [], "zones": {}, "start": t.boss.fight_clock, "erupted": {}, "fuses": {}, "ids": {}}
	var watch := watch_slams(t, seen)
	t.physics_frame.connect(watch)
	t.sm.start_cycle()
	# Each slam's feet while it winds up; then in zone 1 as it goes, and off the ring once it has hurt.
	for k in count:
		await t.wait_until(func(): return slams.beat == slams.Beat.WINDUP and slams.slammed == k and slams.beat_clock >= 0.25, 240)
		await Plates.put_feet(t, SLAM_FEET[k])
	await t.wait_until(func(): return not Plates.state_is(t, "Slams"), 240)
	var waiting_home: int = t.sm.live_zones().size()
	var gone_in_slams: int = seen.erupted.size()
	await Plates.put_feet(t, ZONE_1_FEET)
	await t.wait_until(func(): return seen.erupted.has(0), 120)
	await t.wait(15)
	await Plates.put_feet(t, Plates.AWAY)
	var all_went := func() -> bool: return seen.erupted.size() == count
	await t.wait_until(all_went, 600)
	await t.wait(2)
	t.physics_frame.disconnect(watch)
	var times: Array = slams.slam_clocks.map(func(at): return snappedf(at - seen.start, 0.0001))
	t.log_p("states %s" % [seen.states.map(func(s): return [s[0], snappedf(s[1], 0.001)])])
	t.log_p("spots %s from feet %s; slams at %s; zones on %s" % [slams.spots, slams.picked_from, times, slams.zone_centres])

	var furthest := true
	var here: Vector2 = t.sm.HOME
	for i in slams.spots.size():
		var want: Vector2 = t.sm.furthest_spot(slams.picked_from[i], here) if i < count else t.sm.HOME
		furthest = furthest and slams.spots[i] == want and slams.spots[i] != here
		here = slams.spots[i]
	t.check(slams.spots.size() == count + 1 and furthest, "each teleport to the spot furthest from the player's feet, never the one he is on, home last")
	var first: float = 2.0 * slams.teleport_time + slams.windup_time
	var apart: float = first + slams.recover_time
	var on_time := times.size() == count
	for i in times.size():
		on_time = on_time and absf(times[i] - (first + apart * i)) <= SLACK
	t.check(count == 5 and on_time, "five slams, %.2f s apart from %.2f s, to the frame (%s)" % [apart, first, times])
	var broken := fence_broken(t, slams, SLAM_FEET, slams.zone_centres, slams.placements)
	t.check(slams.zone_centres.size() == count and broken == "", "each zone by the fence rule: on the player's feet, or beside the waiting zones when they stood in one %s" % broken)
	t.check(slams.placements == [&"aimed", &"aimed", &"aimed", &"aimed", &"fence"],
		"zones 1-4 on the feet, zone 5 beside, the feet then in zone 2 (%s, at %s)" % [slams.placements, slams.zone_centres])
	var into_pose: Array = seen.states.filter(func(s): return s[0] == "Pose")
	var done_at: float = apart * count + 2.0 * slams.teleport_time
	t.check(not into_pose.is_empty() and absf(into_pose[0][1] - done_at) <= SLACK, "done at %.2f s, landed home, into Pose (%s)" % [done_at, into_pose])
	t.check(gone_in_slams == 0 and waiting_home == count, "none goes off in the slams: all %d still waiting as he goes into Pose (%d)" % [count, waiting_home])

	t.log_p("-- the poses set them off")
	var strike: float = into_pose[0][1] + pose.turn_time if not into_pose.is_empty() else INF
	var went: Array = []
	for k in count:
		went.append(snappedf(seen.erupted.get(k, -1.0) - strike, 0.0001))
	var fuses: Array = []
	for k in count:
		fuses.append(seen.fuses.get(k, [-1.0, -1.0]).map(func(x): return snappedf(x, 0.0001)))
	t.log_p("from the first strike, zones 1-%d went off at %s s (want %s); rung and gone off that long after each was told: %s" % [count, went, pose.eruptions, fuses])
	var in_order: bool = went.size() == pose.eruptions.size()
	for k in went.size():
		in_order = in_order and absf(went[k] - pose.eruptions[k]) <= SLACK
	t.check(in_order, "oldest first, at %s s from the first pose's strike, to the frame" % [pose.eruptions])
	t.check(absf(went[-1] - 3.0 * pose.pose_time) <= SLACK, "the last as pose 3 ends (%.4f s)" % went[-1])
	var spaced := true
	for k in range(1, went.size()):
		spaced = spaced and went[k] - went[k - 1] >= 0.8 - SLACK
	t.check(spaced, "never under 0.8 s apart: no ring starts while the burst before it can still hurt")
	var told_ahead := true
	for k in count:
		var notice: float = minf(pose.eruption_notice, pose.eruptions[k] + pose.turn_time)
		told_ahead = told_ahead and absf(fuses[k][1] - notice) <= SLACK and absf(fuses[k][0] - (notice - ring_lead)) <= SLACK
	t.check(told_ahead, "each told %.2f s before it goes, or as the poses begin, its ring the last %.2f s" % [pose.eruption_notice, ring_lead])
	t.check(t.events.size() == 1 and t.events[0].id == &"greyson_eruption" and t.player.playerHealth == 998,
		"the feet in zone 1 as it goes: hit once, for a whole heart (health %d)" % t.player.playerHealth)
	t.check(t.sm.live_zones().is_empty(), "and none left waiting")

	var rows: Dictionary = seen.zones
	var one: Array = rows.get(0, [])
	var waiting: Array = one.filter(func(r): return r.phase == 0)
	var fused: Array = one.filter(func(r): return r.phase == 1)
	t.check(not waiting.is_empty() and waiting.all(func(r): return absf(r.db + 12.0) < 0.01 and r.playing and r.stage == 1),
		"zone 1's rumble at its level less 12 dB while it waits, at stage 1")
	var staged: bool = fused.size() >= 2 and fused[0].stage == 2 and fused[-1].stage == 3
	for k in range(1, fused.size()):
		staged = staged and fused[k].stage >= fused[k - 1].stage
	var rising: bool = fused.size() >= 2 and fused[-1].db > fused[0].db
	t.check(staged and rising and fused[-1].db > -2.0, "then rising up its fuse to about its own level, stage 2 once told and stage 3 under the ring (%.2f to %.2f dB)"
		% [fused[0].db if not fused.is_empty() else INF, fused[-1].db if not fused.is_empty() else INF])
	var after: Array = one.filter(func(r): return r.phase == 2)
	t.check(not after.is_empty() and after.all(func(r): return not r.playing), "and stopped as it goes off")
	t.sm.clear_pending_zones()


static func tier_feet(t) -> void:
	t.log_p("-- the feet just outside zone 1 as it goes, the body over its edge: no hit")
	var zone := await first_zone_to_go(t, FEET_TIER_STAND)
	if zone == null:
		return
	var radii: Vector2 = zone.radii
	await Plates.put_feet(t, zone.global_position + Vector2(0, radii.y + 6.0))
	t.clear_iframes()
	var rect: Rect2 = t.hurtbox_rect()
	var over: bool = zone.contains_feet(rect.get_center()) or zone.contains_feet(rect.position)
	var id := zone.get_instance_id()
	await t.wait_until(func(): return Plates.live(id) == null or Plates.live(id).phase == Plates.live(id).Phase.ERUPTING, 120)
	await t.wait(20)
	t.check(over and t.events.is_empty() and t.player.playerHealth == 1000, "its body over the zone, its feet 6 px out: no hit")
	t.sm.clear_pending_zones()


static func tier_dash(t) -> void:
	t.log_p("-- a dash through zone 1 as it goes: DODGED, a perfect dodge, no read")
	var zone := await first_zone_to_go(t)
	if zone == null:
		return
	await Plates.put_feet(t, zone.global_position + Vector2(-200, 0))
	await t.dash_ready()
	t.clear_iframes()
	var gauge: Node = t.boss.break_gauge
	var before: float = gauge.value
	var answers: Array = []
	zone.answered.connect(func(r): answers.append(r))
	var id := zone.get_instance_id()
	await t.wait_until(func(): return Plates.live(id) == null or (Plates.live(id).phase == 1 and Plates.live(id).fuse_left <= 2.0 * FRAME_TIME), 120)
	t.press(KEY_RIGHT)
	t.tap(KEY_W)
	await t.wait_until(func(): return t.player.is_dodging, 20)
	await t.wait_until(func(): return not t.player.is_dodging, 20)
	t.release(KEY_RIGHT)
	await t.wait_until(func(): return Plates.live(id) == null, 60)
	t.log_p("answers %s, dodges %s, events %s, gauge %.3f -> %.3f" % [answers, t.dodges, t.events, before, gauge.value])
	t.check(answers == [HitInfo.Result.DODGED] and t.events.is_empty(), "DODGED, nothing lands")
	t.check(t.dodges.size() == 1 and t.dodges[0].id == &"greyson_eruption", "a perfect dodge")
	t.check(gauge.value == before, "and no read: only plates fill his gauge")
	t.sm.clear_pending_zones()


static func tier_break(t) -> void:
	t.log_p("-- a Break in the middle of his slams: the zones waiting fizzle, none goes off")
	await Plates.park(t, SLAM_FEET[0])
	var slams: Node = t.sm.states["Slams"]
	t.sm.start_cycle()
	await t.wait_until(func(): return slams.slammed == 2 and slams.beat == slams.Beat.OUT, 300)
	var ids: Array = slams.zones.map(func(z): return z.get_instance_id())
	var hidden_before: bool = not t.boss.sprite.visible
	t.boss.break_gauge.add(t.boss.break_gauge.max_value)
	await t.wait_until(func(): return Plates.state_is(t, "Broken"), 30)
	var fizzling: bool = ids.all(func(id): return Plates.live(id) == null or not Plates.live(id).is_pending())
	var goes := [false]
	var watch := func():
		for id in ids:
			var zone := Plates.live(id)
			if zone != null and zone.phase == zone.Phase.ERUPTING:
				goes[0] = true
	t.physics_frame.connect(watch)
	await t.wait(90)
	t.physics_frame.disconnect(watch)
	t.log_p("zones %d, hidden as it broke %s, now %s, visible %s" % [ids.size(), hidden_before, t.sm.current_state.name, t.boss.sprite.visible])
	t.check(ids.size() == 2 and fizzling and t.sm.live_zones().is_empty(), "both zones fizzled at the Break, and the queue emptied")
	t.check(not goes[0] and t.events.is_empty(), "none went off")
	t.check(ids.all(func(id): return Plates.live(id) == null), "and they are gone")
	t.check(Plates.state_is(t, "Broken") and t.boss.sprite.visible, "Broken, and visible")


# His slams run until zone 1 is planted and scheduled - the poses tell it as they begin - with the player standing
# at `stand`; the state machine then held still around it, so only the zone runs on. Zone 1, or null.
static func first_zone_to_go(t, stand: Vector2 = SLAM_FEET[0]) -> Node2D:
	await Plates.park(t, stand)
	var slams: Node = t.sm.states["Slams"]
	t.sm.start_cycle()
	var scheduled := func() -> bool: return not slams.zones.is_empty() and is_instance_valid(slams.zones[0]) and slams.zones[0].phase == slams.zones[0].Phase.SCHEDULED
	var told: bool = await t.wait_until(scheduled, 600)
	var zone: Node2D = slams.zones[0] if not slams.zones.is_empty() else null
	t.check(told and zone != null and zone.phase == zone.Phase.SCHEDULED, "zone 1 planted and told to go off")
	if zone == null:
		return null
	t.sm.set_physics_process(false)
	t.events.clear()
	t.dodges.clear()
	t.player.playerHealth = 1000
	return zone


#THE FENCE

# Where the still, step and weave players stand through the slams: down and left of his pose spot, so zone 1
# covers his spot and the fence his way to it.
const STAND_FEET := Vector2(700, 700)
# The sweep: players starting on this lattice over the floor, standing still or drifting at these px/s from the
# first slam on; a floor cell is safe from a burst when its centre is this far outside the zone.
const SWEEP_STEP := Vector2(150, 120)
const SWEEP_DRIFTS: Array[Vector2] = [Vector2.ZERO, Vector2(124, 85), Vector2(-85, 124), Vector2(-124, -85)]
const MAZE_MARGIN := 4.0
# The bots walk to cells whose centres are this far outside any zone about to go off, and hold this long on his
# side to punch.
const BOT_MARGIN := 16.0
const BOT_HOLD := 0.4


# The span of an offset in zone radii (1: on the edge; 2: two zones touching), and the share of a zone's area
# another covers that far away.
static func span_of(offset: Vector2, radii: Vector2) -> float:
	return Vector2(offset.x / radii.x, offset.y / radii.y).length()


static func shared_at(span: float) -> float:
	if span >= 2.0:
		return 0.0
	return (2.0 * acos(span / 2.0) - span / 2.0 * sqrt(4.0 - span * span)) / PI


# The first way `centres` break the fence rule for a player whose feet were at feet[k] at slam k, or "".
static func fence_broken(t, slams: Node, feet: Array, centres: Array, kinds: Array) -> String:
	var radii: Vector2 = slams.radii
	var area: Rect2 = t.sm.ROPES.grow(-slams.zone_inset)
	for k in centres.size():
		var centre: Vector2 = centres[k]
		if centre.x < area.position.x or centre.x > area.end.x or centre.y < area.position.y or centre.y > area.end.y:
			return "zone %d at %s is off the floor" % [k + 1, centre]
		var aim: Vector2 = feet[k].clamp(area.position, area.end)
		var standing_in := false
		var shared := 0.0
		for j in k:
			standing_in = standing_in or span_of(feet[k] - centres[j], radii) <= 1.0
			shared = maxf(shared, shared_at(span_of(aim - centres[j], radii)))
		if not standing_in or shared <= slams.fence_overlap:
			if kinds[k] != &"aimed" or centre.distance_to(aim) > 1.0:
				return "zone %d should be on the feet %s: %s at %s" % [k + 1, aim, kinds[k], centre]
			continue
		if kinds[k] == &"least":
			continue
		var most := 0.0
		var nearest := INF
		for j in k:
			var span := span_of(centre - centres[j], radii)
			most = maxf(most, shared_at(span))
			nearest = minf(nearest, span)
		if kinds[k] != &"fence" or most > slams.fence_overlap + 0.001 or nearest > slams.fence_touch + 0.001:
			return "zone %d at %s isn't beside the waiting ones: %s, shares %.2f, %.2f radii from the nearest" % [k + 1, centre, kinds[k], most, nearest]
	return ""


# The feet at each of `marks` (the slams' clock) for a player on `start` at the first mark, walking at `drift`
# px/s, turned back by the ropes.
static func drift_track(start: Vector2, drift: Vector2, marks: Array, ropes: Rect2) -> Array[Vector2]:
	var inside := ropes.grow(-20.0)
	var at := start
	var velocity := drift
	var clock: float = marks[0]
	var track: Array[Vector2] = []
	for mark in marks:
		var left: float = mark - clock
		while left > 0.0:
			var step := minf(left, 0.05)
			at += velocity * step
			if at.x < inside.position.x or at.x > inside.end.x:
				velocity.x = -velocity.x
				at.x = clampf(at.x, inside.position.x, inside.end.x)
			if at.y < inside.position.y or at.y > inside.end.y:
				velocity.y = -velocity.y
				at.y = clampf(at.y, inside.position.y, inside.end.y)
			left -= step
		clock = mark
		track.append(at)
	return track


static func tier_fence(t) -> void:
	t.log_p("-- the fence swept: zone_spot for players standing still or drifting through the slams, then the maze")
	var slams: Node = t.sm.states["Slams"]
	var pose: Node = t.sm.states["Pose"]
	var times := Maze.clock(t)
	var grid := Maze.make_grid(t.sm.ROPES)
	var ropes: Rect2 = t.sm.ROPES
	var first: float = 2.0 * slams.teleport_time + slams.windup_time
	var apart: float = first + slams.recover_time
	var ring_start: float = times.eruptions[0] - times.ring
	var marks: Array[float] = []
	for k in slams.slams:
		marks.append(first + apart * k)
	marks.append(apart * slams.slams + 2.0 * slams.teleport_time + pose.turn_time + ring_start)
	var reach := reach_cells(t, grid)
	var punch_poses := {}
	var fenced_steps := [0, 0]
	var cases := 0
	var failures: Array[String] = []
	var kinds := {}
	var tightest := {cells = 1 << 30, case = ""}
	var longest_out := 0.0
	var spent := 0
	var y := ropes.position.y + SWEEP_STEP.y / 2.0
	while y < ropes.end.y:
		var x := ropes.position.x + SWEEP_STEP.x / 2.0
		while x < ropes.end.x:
			for drift in SWEEP_DRIFTS:
				var track := drift_track(Vector2(x, y), drift, marks, ropes)
				var waiting: Array[Vector2] = []
				var placed_kinds: Array = []
				var started := Time.get_ticks_usec()
				for k in slams.slams:
					var placed: Dictionary = slams.zone_spot(track[k], waiting)
					waiting.append(placed.centre)
					placed_kinds.append(placed.kind)
					kinds[placed.kind] = kinds.get(placed.kind, 0) + 1
				spent += Time.get_ticks_usec() - started
				cases += 1
				var label := "from %s drifting %s" % [Vector2(x, y).round(), drift]
				var broken := fence_broken(t, slams, track, waiting, placed_kinds)
				var sets: Array = Maze.forward(grid, track[-1], waiting, times, ring_start, MAZE_MARGIN)
				var sizes: Array = sets.map(func(s): return Maze.count(s))
				var out: float = Maze.distance_from(grid, Maze.outside(grid, waiting[0], times.radii, MAZE_MARGIN))[Maze.index_of(grid, track[-1])]
				longest_out = maxf(longest_out, out)
				if broken != "" or sizes.has(0):
					failures.append("%s: zones %s %s, safe cells at each burst %s" % [label, waiting, broken, sizes])
				elif sizes.min() < tightest.cells:
					tightest = {cells = sizes.min(), case = "%s: zones %s, safe cells %s" % [label, waiting, sizes]}
				if drift == Vector2.ZERO:
					var step := nearest_out(grid, track[-1], waiting[0], times.radii)
					fenced_steps[1] += 1
					for k in range(1, waiting.size()):
						if span_of(step - waiting[k], times.radii) <= 1.0:
							fenced_steps[0] += 1
							break
					var best: Dictionary = Maze.earliest(grid, track[-1], waiting, times, -pose.turn_time, BOT_MARGIN, reach, BOT_HOLD)
					var at_pose: String = "never" if best.is_empty() else str(maxi(floori(best.at / pose.pose_time) + 1, 1))
					punch_poses[at_pose] = punch_poses.get(at_pose, 0) + 1
			x += SWEEP_STEP.x
		y += SWEEP_STEP.y
	t.log_p("%d cases (%d starts, still and three drifts): placements %s; zone_spot %.1f ms a zone on average" % [cases, cases / SWEEP_DRIFTS.size(), kinds, spent / 1000.0 / (cases * slams.slams)])
	t.log_p("the tightest: %d safe %d px cells at one burst (%s)" % [tightest.cells, Maze.CELL, tightest.case])
	t.log_p("standing still through the slams, the pose a flawless walk (no dash, from the poses' start) could first punch him in, anywhere in reach: %s" % [punch_poses])
	t.log_p("standing still, the one step out of zone 1 lands in a later zone of the fence from %d of %d starts" % fenced_steps)
	t.log_p("the longest walk out of zone 1 from where the player stood: %.0f px, %.2f s at %.0f px/s; its ring and the burst's first hurt frame give %.2f s" % [longest_out, longest_out / Maze.WALK, Maze.WALK, times.ring + times.first_hurt])
	for failure in failures.slice(0, 6):
		t.log_p("  %s" % failure)
	t.check(cases > 0 and failures.is_empty(),
		"every case keeps the fence rule, and a walk with no dash comes through all five bursts (%d of %d fail)" % [failures.size(), cases])
	t.check(longest_out <= Maze.WALK * (times.ring + times.first_hurt), "zone 1 can always be walked out of before it hurts")


# The poses' clock from the first strike: less than 0 through the turn, and -INF out of the poses.
static func pose_clock(t) -> float:
	var pose: Node = t.sm.states["Pose"]
	if t.sm.current_state != pose:
		return -INF
	return pose.phase_clock - pose.turn_time


# Every zone the slams plant, as it lands a hit on the player: its number into `hits`.
static func watch_hits(t, hits: Array) -> Callable:
	var slams: Node = t.sm.states["Slams"]
	var seen := {}
	return func():
		for i in slams.zones.size():
			var zone = slams.zones[i]
			if seen.has(i) or not is_instance_valid(zone):
				continue
			seen[i] = true
			var got := func(result: int):
				if result == HitInfo.Result.HIT:
					hits.append(i + 1)
			zone.answered.connect(got)


# A player standing at `feet` through the slams, into the poses: the watch on their hits running.
static func stand_through_slams(t, feet: Vector2, hits: Array) -> Callable:
	await Plates.park(t, feet)
	var watch := watch_hits(t, hits)
	t.physics_frame.connect(watch)
	t.sm.start_cycle()
	await t.wait_until(func(): return Plates.state_is(t, "Pose"), 600)
	return watch


# The poses played on past pose 3's end, so all five bursts are over.
static func past_the_bursts(t) -> void:
	var pose: Node = t.sm.states["Pose"]
	await t.wait_until(func(): return not Plates.state_is(t, "Pose") or pose.pose_index >= 3, 600)
	await t.wait(20)


static func tier_still(t) -> void:
	t.log_p("-- a player standing still through the slams and the poses")
	var slams: Node = t.sm.states["Slams"]
	var hits: Array = []
	var watch: Callable = await stand_through_slams(t, STAND_FEET, hits)
	await past_the_bursts(t)
	t.physics_frame.disconnect(watch)
	var broken := fence_broken(t, slams, slams.slam_feet, slams.zone_centres, slams.placements)
	t.log_p("zones at %s, placed %s from the feet %s; hit by zones %s, health %d" % [slams.zone_centres, slams.placements, slams.slam_feet[0], hits, t.player.playerHealth])
	t.check(slams.placements == [&"aimed", &"fence", &"fence", &"fence", &"fence"] and broken == "",
		"zone 1 on them, and the other four beside it by the fence rule %s" % broken)
	t.check(not hits.is_empty() and hits[0] == 1, "standing there, zone 1's burst hits them (%s)" % [hits])


# The floor cell nearest `feet` that is BOT_MARGIN clear of the zone on `centre`.
static func nearest_out(grid: Dictionary, feet: Vector2, centre: Vector2, radii: Vector2) -> Vector2:
	var clear := Maze.outside(grid, centre, radii, BOT_MARGIN)
	var best := Vector2.INF
	for i in clear.size():
		if clear[i] == 1 and Maze.centre_of(grid, i).distance_to(feet) < best.distance_to(feet):
			best = Maze.centre_of(grid, i)
	return best


static func tier_step(t) -> void:
	t.log_p("-- the old way out: standing still through the slams, one step out of zone 1 as it rings, and stand")
	var slams: Node = t.sm.states["Slams"]
	var hits: Array = []
	var watch: Callable = await stand_through_slams(t, STAND_FEET, hits)
	var times := Maze.clock(t)
	var grid := Maze.make_grid(t.sm.ROPES)
	await t.wait_until(func(): return pose_clock(t) >= times.eruptions[0] - times.ring, 120)
	var feet: Vector2 = t.sm.player_feet()
	var step := nearest_out(grid, feet, slams.zone_centres[0], times.radii)
	await walk_feet_to(t, step, 90)
	var out_at := pose_clock(t)
	var stood: Vector2 = t.sm.player_feet()
	await past_the_bursts(t)
	t.physics_frame.disconnect(watch)
	var later := hits.filter(func(zone): return zone > 1)
	t.log_p("stepped %.0f px from %s to %s, there %.2f s after the first strike; zones at %s; hit by zones %s" % [feet.distance_to(stood), feet, stood, out_at, slams.zone_centres, hits])
	t.check(not hits.has(1), "the step clears zone 1")
	t.check(not later.is_empty(), "and standing where it stepped, a later zone of the fence hits them (zone %s)" % [later])


# The feet walked to `feet` with the arrow keys, for at most `frames` steps.
static func walk_feet_to(t, feet: Vector2, frames: int) -> bool:
	var bot := {"held": []}
	var offset: Vector2 = t.sm.player_feet() - t.player.global_position
	var to := feet - offset
	var arrived := false
	for i in frames:
		var d: Vector2 = to - t.player.global_position
		if absf(d.x) <= 8.0 and absf(d.y) <= 8.0:
			arrived = true
			break
		t._bot_walk(bot, to)
		await t.physics_frame
	t._bot_release(bot)
	return arrived


# Where the player's feet stand to punch him from `side` (+1 his right), as the suite's bots stand.
static func punch_feet(t, side: float) -> Vector2:
	var shape: CollisionShape2D = t.boss.get_node("Hurtbox/CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	var reach: Rect2 = t.player.punch_box(t.player.Facing.LEFT if side > 0.0 else t.player.Facing.RIGHT)
	var edge: float = box.end.x if side > 0.0 else box.position.x
	var at := Vector2(edge - reach.get_center().x * t.player.global_scale.x, box.end.y - 28.0)
	return at + (t.sm.player_feet() - t.player.global_position)


# The cells whose feet can punch him where he poses: a punch facing him, from the left or the right, over his
# hurtbox. Not only the suite's two spots beside his feet: higher up his side lands too.
static func reach_cells(t, grid: Dictionary) -> PackedByteArray:
	var shape: CollisionShape2D = t.boss.get_node("Hurtbox/CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	var offset: Vector2 = t.sm.player_feet() - t.player.global_position
	var scale: Vector2 = t.player.global_scale
	var mask := PackedByteArray()
	mask.resize(grid.columns * grid.rows)
	for i in mask.size():
		var at: Vector2 = Maze.centre_of(grid, i) - offset
		var punch: Rect2 = t.player.punch_box(t.player.Facing.LEFT if at.x > box.get_center().x else t.player.Facing.RIGHT)
		mask[i] = 1 if Rect2(at + punch.position * scale, punch.size * scale).intersects(box) else 0
	return mask


static func tier_weave(t) -> void:
	t.log_p("-- weaving: standing still through the slams, then out of each zone before it goes and in to him")
	var slams: Node = t.sm.states["Slams"]
	var pose: Node = t.sm.states["Pose"]
	var hits: Array = []
	var watch: Callable = await stand_through_slams(t, STAND_FEET, hits)
	var times := Maze.clock(t)
	var grid := Maze.make_grid(t.sm.ROPES)
	var zones: Array = slams.zone_centres.duplicate()
	var start_time := pose_clock(t)
	var feet: Vector2 = t.sm.player_feet()
	var plan := {}
	for side in [-1.0, 1.0]:
		var tried: Dictionary = Maze.weave(grid, feet, zones, times, start_time, BOT_MARGIN, punch_feet(t, side), BOT_HOLD)
		if not tried.is_empty() and (plan.is_empty() or tried.at < plan.at):
			plan = tried
	if plan.is_empty():
		t.check(false, "a walk through the maze to him exists (zones %s)" % [zones])
		t.physics_frame.disconnect(watch)
		return
	t.log_p("zones at %s, placed %s; the plan: %s; at his side %.2f s after the first strike" % [zones, slams.placements, plan.legs.map(func(leg): return [snappedf(leg.from, 0.01), leg.to.round(), leg.punch]), plan.at])
	var best: Dictionary = Maze.earliest(grid, feet, zones, times, start_time, BOT_MARGIN, reach_cells(t, grid), BOT_HOLD)
	t.log_p("the earliest a flawless walk could punch him from anywhere in reach: %s" % ("never" if best.is_empty() else "%.2f s after the first strike, pose %d" % [best.at, floori(best.at / pose.pose_time) + 1]))
	var landed := {pose = -1, at = INF}
	for leg in plan.legs:
		await t.wait_until(func(): return pose_clock(t) >= leg.from, 400)
		await walk_feet_to(t, leg.to, 120)
		if leg.punch:
			var dealt: int = await t.swing()
			if dealt > 0 and landed.pose < 0:
				landed = {pose = pose.pose_index + 1, at = pose_clock(t)}
	await past_the_bursts(t)
	t.physics_frame.disconnect(watch)
	t.log_p("punched him in pose %d, %.2f s after the first strike; hit by zones %s, health %d" % [landed.pose, landed.at, hits, t.player.playerHealth])
	t.check(hits.is_empty(), "no burst hits them")
	t.check(landed.pose in [2, 3], "and they reach him and punch in pose 2 or 3 (pose %d)" % landed.pose)
