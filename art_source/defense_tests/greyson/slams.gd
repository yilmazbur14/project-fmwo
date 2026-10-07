extends RefCounted

# greyson_slams (coder B): Greyson's slams and their eruption zones (GreysonSlams, GreysonEruptionScript; plan
# sections 3.2, 3.3 and 9.6), in his test scene, the cycle pinned to his slams and poses. --fixed-fps 60. tier=
#   timeline  (the default) each teleport to the spot furthest from the player's feet and never the one he is on,
#             home last; four slams 0.62 s apart from 0.50 s, each planting two zones by the fence rule - on the
#             player's feet at that slam, or beside the waiting zones when they stood in one, a slam's second
#             always beside; none going off in the slams, all eight waiting as he lands home and goes into Pose at
#             2.72 s; then set off oldest first at GreysonPose's eruptions from the first pose's strike, to the
#             frame, none closer than ERUPTION_GAP_FLOOR, each told eruption_notice before - the first ones
#             while he is still slamming - with its ring the last ring_lead; each rumble ramped up its fuse and
#             stopped as it goes; the feet in zone 1 as it goes hit once.
#   feet      the player's feet just outside zone 1 as it goes off, their body over it: no hit.
#   dash      a dash through zone 1 as it goes off: DODGED, a perfect dodge, and no read.
#   break     a Break in the middle of the slams: every zone still waiting fizzles, none goes off, and he is
#             left visible.
#   fence     the fence swept, zone_spot alone: players standing still or drifting through the slams from spots
#             all over the floor; every zone keeps the fence rule, and from wherever the player is once every zone
#             is down and zone 1 told (maze.clock's start) a walk (no dash) comes through all eight bursts
#             (maze.gd); a player standing still can walk out of zone 1 inside its ring. The numbers are logged.
#   still     a player standing still through it all: zone 1 lands on them, the other seven box them in, and
#             zone 1's burst hits them.
#   step      the old way out, a player standing still through the slams who steps out of zone 1 as it rings and
#             stands there: a later zone of the fence hits them.
#   weave     a player standing still through the slams who, once the last zone is down, walks the maze
#             (maze.weave): out of each zone before it goes, and to him to punch as soon as the bursts let them. No
#             burst hits them, and they reach him in pose 2 or 3.
#   ring      (playtest 2026-10-04) zone 1's yellow ring with the player standing on its centre: over their head,
#             not on their body; a zone by the top rope keeps its ring inside the ropes, one under his HUD below it.

const Plates := preload("res://art_source/defense_tests/greyson/plates.gd")
const Maze := preload("res://art_source/defense_tests/greyson/maze.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const FRAME_TIME := 1.0 / 60.0
const SLACK := FRAME_TIME + 0.0001
# The closest two eruptions may go off: the fence sweep (a walk through all eight) and the weave (no burst, and him
# reached in poses 1-3) both pass with them this close (the 2026-10-06 density pass; 0.6 before it).
const ERUPTION_GAP_FLOOR := 0.5
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
		"ring":
			await tier_ring(t)
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
	var zone_count: int = count * slams.zones_per_slam
	var seen := {"steps": 0, "states": [], "zones": {}, "start": t.boss.fight_clock, "erupted": {}, "fuses": {}, "ids": {}}
	var watch := watch_slams(t, seen)
	t.physics_frame.connect(watch)
	# Nothing banks: this is about the zones' clock, and his third bank would fire the bomb before the last one goes.
	var hold := func(): t.boss.reset_hype()
	t.physics_frame.connect(hold)
	t.sm.start_cycle()
	# Each slam's feet while it winds up; then in zone 1 as it goes, and off the ring once it has hurt.
	for k in count:
		await t.wait_until(func(): return slams.beat == slams.Beat.WINDUP and slams.slammed == k and slams.beat_clock >= slams.windup_time / 2.0, 240)
		await Plates.put_feet(t, SLAM_FEET[k])
	await t.wait_until(func(): return not Plates.state_is(t, "Slams"), 240)
	var waiting_home: int = t.sm.live_zones().size()
	var gone_in_slams: int = seen.erupted.size()
	await Plates.put_feet(t, ZONE_1_FEET)
	await t.wait_until(func(): return seen.erupted.has(0), 120)
	await t.wait(15)
	await Plates.put_feet(t, Plates.AWAY)
	var all_went := func() -> bool: return seen.erupted.size() == zone_count
	await t.wait_until(all_went, 600)
	await t.wait(2)
	t.physics_frame.disconnect(watch)
	t.physics_frame.disconnect(hold)
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
	t.check(count == 4 and on_time, "four slams, %.2f s apart from %.2f s, to the frame (%s)" % [apart, first, times])
	var broken := fence_broken(t, slams, slams.slam_feet, slams.zone_centres, slams.placements)
	t.log_p("zones placed %s" % [slams.placements])
	t.check(zone_count == 8 and slams.zone_centres.size() == zone_count and broken == "",
		"eight zones, two a slam, each by the fence rule: on the player's feet, or beside the waiting zones when they stood in one %s" % broken)
	var seconds_beside := true
	for k in count:
		seconds_beside = seconds_beside and slams.placements[2 * k + 1] != &"aimed"
	t.check(slams.placements[0] == &"aimed" and seconds_beside, "zone 1 on the player's feet, and each slam's second beside the zones already down (%s)" % [slams.placements])
	var into_pose: Array = seen.states.filter(func(s): return s[0] == "Pose")
	var done_at: float = apart * count + 2.0 * slams.teleport_time
	t.check(not into_pose.is_empty() and absf(into_pose[0][1] - done_at) <= SLACK, "done at %.2f s, landed home, into Pose (%s)" % [done_at, into_pose])
	t.check(gone_in_slams == 0 and waiting_home == zone_count, "none goes off in the slams: all %d still waiting as he goes into Pose (%d)" % [zone_count, waiting_home])

	t.log_p("-- the poses set them off")
	var strike: float = into_pose[0][1] + pose.turn_time if not into_pose.is_empty() else INF
	var went: Array = []
	for k in zone_count:
		went.append(snappedf(seen.erupted.get(k, -1.0) - strike, 0.0001))
	var fuses: Array = []
	for k in zone_count:
		fuses.append(seen.fuses.get(k, [-1.0, -1.0]).map(func(x): return snappedf(x, 0.0001)))
	t.log_p("from the first strike, zones 1-%d went off at %s s (want %s); rung and gone off that long after each was told: %s" % [zone_count, went, pose.eruptions, fuses])
	var in_order: bool = went.size() == pose.eruptions.size()
	for k in went.size():
		in_order = in_order and absf(went[k] - pose.eruptions[k]) <= SLACK
	t.check(in_order, "oldest first, at %s s from the first pose's strike, to the frame" % [pose.eruptions])
	var spaced := true
	for k in range(1, went.size()):
		spaced = spaced and went[k] - went[k - 1] >= ERUPTION_GAP_FLOOR - SLACK
	t.check(spaced, "never closer than %.2f s apart, the spacing the fence and weave tiers were proven at (%.4f s the last)" % [ERUPTION_GAP_FLOOR, went[-1]])
	var told_ahead := true
	for k in zone_count:
		var notice: float = minf(pose.eruption_notice, pose.eruptions[k] + slams.duration() + pose.turn_time)
		told_ahead = told_ahead and absf(fuses[k][1] - notice) <= 2.0 * SLACK and absf(fuses[k][0] - (notice - ring_lead)) <= 2.0 * SLACK
	t.check(told_ahead, "each told %.2f s before it goes, the first while he is still slamming, its ring the last %.2f s" % [pose.eruption_notice, ring_lead])
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
	t.check(ids.size() == 2 * slams.zones_per_slam and fizzling and t.sm.live_zones().is_empty() and not t.sm.eruption_clock_running,
		"the %d zones of two slams fizzled at the Break, the queue emptied and the eruption clock stopped" % ids.size())
	t.check(not goes[0] and t.events.is_empty(), "none went off")
	t.check(ids.all(func(id): return Plates.live(id) == null), "and they are gone")
	t.check(Plates.state_is(t, "Broken") and t.boss.sprite.visible, "Broken, and visible")


# His slams run until zone 1 is planted and scheduled - the eruption clock tells it as the last slam comes - with the
# player standing at `stand`; the state machine then held still around it, so only the zone runs on. Zone 1, or
# null.
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
# side to punch, a whole swing (PlayerPunching holds them still for it) and the suite's swing()'s few frames after.
const BOT_MARGIN := 32.0
const BOT_HOLD := 0.5
# How far off its cell a bot's feet may be when it swings.
const PUNCH_SLOP := 12.0


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
	# On the eruptions' clock: each landing, then the maze's start.
	var marks: Array[float] = []
	marks.assign(times.landings)
	marks.append(times.start)
	var steps := Maze.step_grid(ropes)
	var goals := punch_cells(t, steps)
	var punch_poses := {}
	var punch_times: Array[float] = []
	var fenced_steps := [0, 0]
	var cases := 0
	var failures: Array[String] = []
	var kinds := {}
	var tightest := {cells = 1 << 30, case = ""}
	var longest_out := 0.0
	var longest_still := 0.0
	var spent := 0
	var y := ropes.position.y + SWEEP_STEP.y / 2.0
	while y < ropes.end.y:
		var x := ropes.position.x + SWEEP_STEP.x / 2.0
		while x < ropes.end.x:
			for drift in SWEEP_DRIFTS:
				var track := drift_track(Vector2(x, y), drift, marks, ropes)
				var waiting: Array[Vector2] = []
				var zone_feet: Array[Vector2] = []
				var placed_kinds: Array = []
				var started := Time.get_ticks_usec()
				for k in slams.slams:
					for n in slams.zones_per_slam:
						var placed: Dictionary = slams.zone_spot(track[k], waiting)
						waiting.append(placed.centre)
						zone_feet.append(track[k])
						placed_kinds.append(placed.kind)
						kinds[placed.kind] = kinds.get(placed.kind, 0) + 1
				spent += Time.get_ticks_usec() - started
				cases += 1
				var label := "from %s drifting %s" % [Vector2(x, y).round(), drift]
				var broken := fence_broken(t, slams, zone_feet, waiting, placed_kinds)
				var sets: Array = Maze.forward(grid, track[-1], waiting, times, times.start, MAZE_MARGIN)
				var sizes: Array = sets.map(func(s): return Maze.count(s))
				var out: float = Maze.distance_from(grid, Maze.outside(grid, waiting[0], times.radii, MAZE_MARGIN))[Maze.index_of(grid, track[-1])]
				longest_out = maxf(longest_out, out)
				if drift == Vector2.ZERO:
					longest_still = maxf(longest_still, out)
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
					var run: Dictionary = Maze.stepped(steps, track[-1], waiting, times, times.start, MAZE_MARGIN, times.eruptions[-1] + 1.0)
					var best: Dictionary = Maze.first_punch(run, goals, BOT_HOLD, 0.0)
					var at_pose: String = "after the bursts"
					if not best.is_empty():
						var at: float = run.clocks[best.step]
						punch_times.append(at)
						at_pose = str(floori(at / pose.pose_time) + 1)
					punch_poses[at_pose] = punch_poses.get(at_pose, 0) + 1
			x += SWEEP_STEP.x
		y += SWEEP_STEP.y
	var zones_placed: int = cases * slams.slams * slams.zones_per_slam
	var to_first_hurt: float = times.eruptions[0] + times.first_hurt - times.start
	t.log_p("%d cases (%d starts, still and three drifts), %d zones a case: placements %s; zone_spot %.1f ms a zone on average" % [cases, cases / SWEEP_DRIFTS.size(), slams.slams * slams.zones_per_slam, kinds, spent / 1000.0 / zones_placed])
	t.log_p("the maze starts %.2f s from the first strike, the last zone down and zone 1 told; zone 1 hurts %.2f s after" % [times.start, to_first_hurt])
	t.log_p("the tightest: %d safe %d px cells at one burst (%s)" % [tightest.cells, Maze.CELL, tightest.case])
	punch_times.sort()
	t.log_p("standing still through the slams, the pose a flawless walk (no dash, from the maze's start) could first punch him in: %s; from the first strike %s" % [punch_poses,
		"never" if punch_times.is_empty() else "%.2f s at the soonest, %.2f s the median, %.2f s at the latest" % [punch_times[0], punch_times[punch_times.size() / 2], punch_times[-1]]])
	t.log_p("standing still, the one step out of zone 1 lands in a later zone of the fence from %d of %d starts" % fenced_steps)
	t.log_p("the longest walk out of zone 1 from where the player stood at the start: %.0f px (standing still %.0f px), at %.0f px/s %.2f s (%.2f s); zone 1 hurts %.2f s after the start, and its ring and first hurt frame are %.2f s" % [longest_out, longest_still, Maze.WALK, longest_out / Maze.WALK, longest_still / Maze.WALK, to_first_hurt, times.ring + times.first_hurt])
	for failure in failures.slice(0, 6):
		t.log_p("  %s" % failure)
	t.check(cases > 0 and failures.is_empty(),
		"every case keeps the fence rule, and a walk with no dash comes through all %d bursts (%d of %d fail)" % [slams.slams * slams.zones_per_slam, failures.size(), cases])
	t.check(longest_out <= Maze.WALK * to_first_hurt, "zone 1 can always be walked out of before it hurts")
	t.check(longest_still <= Maze.WALK * (times.ring + times.first_hurt), "and a player who stood still can walk out of it inside its ring")


# The eruptions' clock, from the first strike: the poses' own, and the state machine's before them (-INF otherwise).
static func strike_clock(t) -> float:
	var pose: Node = t.sm.states["Pose"]
	if t.sm.current_state == pose:
		return pose.phase_clock - pose.turn_time
	if t.sm.current_state == t.sm.states["Slams"] and t.sm.eruption_clock_running:
		return t.sm.eruption_clock
	return -INF


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


# A player standing at `feet` through the slams, into the poses - or, `to_last` on, only until the last slam has
# landed, every zone down: the watch on their hits running.
static func stand_through_slams(t, feet: Vector2, hits: Array, to_last := false) -> Callable:
	await Plates.park(t, feet)
	var watch := watch_hits(t, hits)
	t.physics_frame.connect(watch)
	t.sm.start_cycle()
	var slams: Node = t.sm.states["Slams"]
	if to_last:
		await t.wait_until(func(): return slams.slammed >= slams.slams or Plates.state_is(t, "Pose"), 600)
	else:
		await t.wait_until(func(): return Plates.state_is(t, "Pose"), 600)
	return watch


# The poses played on past pose 3's end, so all the bursts are over.
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
	var beside: bool = slams.placements.slice(1).all(func(kind): return kind != &"aimed")
	t.check(slams.placements.size() == slams.slams * slams.zones_per_slam and slams.placements[0] == &"aimed" and beside and broken == "",
		"zone 1 on them, and the other %d beside the zones already down by the fence rule %s" % [slams.placements.size() - 1, broken])
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


# The step cells whose feet can punch him where he stands now (he is to be at HOME), with a bot's PUNCH_SLOP px off
# its cell to spare: the player plainly faces him side-on there (PlayerScript._aim, past its turning hysteresis), and
# the punch still lands PUNCH_SLOP px further from him.
static func punch_cells(t, steps: Dictionary) -> Array[Vector2i]:
	var shape: CollisionShape2D = t.boss.get_node("Hurtbox/CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	var offset: Vector2 = t.sm.player_feet() - t.player.global_position
	var scale: Vector2 = t.player.global_scale
	var cells: Array[Vector2i] = []
	for row in steps.rows:
		for column in steps.columns:
			var at: Vector2 = Maze.step_centre(steps, row, column) - offset
			var aim: Vector2 = at.clamp(box.position, box.end) - at
			if absf(aim.x) < 2.0 * (absf(aim.y) + PUNCH_SLOP) or aim.x == 0.0:
				continue
			var facing: int = t.player.Facing.RIGHT if aim.x > 0.0 else t.player.Facing.LEFT
			var punch: Rect2 = t.player.punch_box(facing)
			var away := Vector2(-signf(aim.x) * PUNCH_SLOP, 0.0)
			var lands := true
			for slip in [away, Vector2(0, PUNCH_SLOP), Vector2(0, -PUNCH_SLOP)]:
				lands = lands and Rect2(at + slip + punch.position * scale, punch.size * scale).intersects(box)
			if lands:
				cells.append(Vector2i(column, row))
	return cells


static func tier_weave(t) -> void:
	t.log_p("-- weaving: standing still through the slams, then out of each zone before it goes and in to him")
	var slams: Node = t.sm.states["Slams"]
	var pose: Node = t.sm.states["Pose"]
	var hits: Array = []
	# Where a punch lands on him at HOME, read while he stands there.
	await Plates.park(t, STAND_FEET)
	var steps := Maze.step_grid(t.sm.ROPES)
	var goals := punch_cells(t, steps)
	var watch: Callable = await stand_through_slams(t, STAND_FEET, hits, true)
	var times := Maze.clock(t)
	var zones: Array = slams.zone_centres.duplicate()
	var start_time := strike_clock(t)
	var run: Dictionary = Maze.stepped(steps, t.sm.player_feet(), zones, times, start_time, BOT_MARGIN, times.eruptions[-1] + 1.5)
	var punch: Dictionary = Maze.first_punch(run, goals, BOT_HOLD, 0.0)
	if punch.is_empty():
		t.check(false, "a walk through the maze to him exists (zones %s)" % [zones])
		t.physics_frame.disconnect(watch)
		return
	var route: Array = Maze.punch_route(steps, run, punch, BOT_HOLD)
	t.log_p("zones at %s, placed %s; planned from %.2f s: at his side %.2f s after the first strike, %d moves" % [zones, slams.placements, start_time, run.clocks[punch.step], route.size()])
	var bot := {"held": []}
	var offset: Vector2 = t.sm.player_feet() - t.player.global_position
	var landed := {pose = -1, at = INF}
	var punched := false
	var index := 0
	var worst_lag := 0.0
	for frame in 60 * 8:
		var now := strike_clock(t)
		if now == -INF:
			break
		while index + 1 < route.size() and now >= route[index + 1].at - Maze.STEP_TIME:
			index += 1
			if route[index].punch:
				break
		var leg: Dictionary = route[index]
		var there: bool = t.sm.player_feet().distance_to(leg.to) <= 10.0
		if leg.punch and not punched and now >= leg.at and (there or now >= leg.at + Maze.STEP_TIME * 2.0):
			punched = true
			t._bot_release(bot)
			t.log_p("swinging at %.2f s from the feet %s (planned %s), facing %d, him %s open %s" % [now, t.sm.player_feet(), leg.to, t.player.facing, t.sm.current_state.name, t.sm.is_open()])
			var dealt: int = await t.swing()
			t.log_p("  dealt %d, his health %d, hits this window %d" % [dealt, t.boss.boss_health, t.boss.hits_this_window])
			if dealt > 0:
				landed = {pose = pose.pose_index + 1, at = strike_clock(t)}
			continue
		if now >= leg.at:
			worst_lag = maxf(worst_lag, t.sm.player_feet().distance_to(leg.to))
		t._bot_walk(bot, leg.to - offset)
		await t.physics_frame
		if index == route.size() - 1 and now > times.eruptions[-1] + times.hurt_end + 0.1:
			break
	t._bot_release(bot)
	await past_the_bursts(t)
	t.physics_frame.disconnect(watch)
	t.log_p("punched him in pose %d, %.2f s after the first strike; the feet at most %.0f px off the plan; hit by zones %s, health %d" % [landed.pose, landed.at, worst_lag, hits, t.player.playerHealth])
	t.check(hits.is_empty(), "no burst hits them")
	t.check(landed.pose in [1, 2, 3], "and they reach him and punch in poses 1-3, before his third bank fills the meter (pose %d)" % landed.pose)


# Zone 1's yellow ring with the player standing on its centre as it rings (playtest 2026-10-04: it stood on their feet,
# drawn over the fighters, and covered them to the chest just as they had to move): over their head, clear of their
# body and over the zone's centre; and a zone planted up by the top rope keeps its ring inside the ropes.
static func tier_ring(t) -> void:
	t.log_p("-- zone 1's yellow ring over a player standing on its centre")
	var zone := await first_zone_to_go(t)
	if zone == null:
		return
	await Plates.put_feet(t, zone.global_position)
	var id := zone.get_instance_id()
	await t.wait_until(func(): return Plates.live(id) == null or Plates.live(id).stage == 3, 120)
	await t.wait(2)
	var ring := ring_rect(t, zone)
	var body: Rect2 = t.hurtbox_rect()
	t.log_p("zone at %s, ring %s, the player's hurtbox %s" % [zone.global_position, ring, body])
	t.check(ring.size != Vector2.ZERO, "the ring is up as it rushes")
	t.check(not ring.intersects(body) and ring.end.y <= body.position.y, "over their head, clear of their body (ring bottom %.0f, their top %.0f)" % [ring.end.y, body.position.y])
	t.check(absf(ring.get_center().x - zone.global_position.x) <= 2.0, "over the zone's centre")
	t.sm.clear_pending_zones()
	t.sm.set_physics_process(true)
	await t.wait(20)
	var high := await ring_of_zone_at(t, Vector2(400, t.sm.ROPES.position.y + 10.0))
	t.check(high.size != Vector2.ZERO and high.position.y >= t.sm.ROPES.position.y - 1.0, "a zone by the top rope keeps its ring inside the ropes (top %.0f)" % high.position.y)
	# Under his HUD block it is never lifted up into it (the HUD is drawn over the ring).
	var hud: Rect2 = t.sm.HUD_FADE_RECT
	for centre in [Vector2(960, 300), Vector2(960, 230)]:
		var under := await ring_of_zone_at(t, centre)
		t.check(under.size != Vector2.ZERO and under.position.y >= hud.end.y - 1.0, "a zone at %s keeps its ring below his HUD (top %.0f, the HUD to %.0f)" % [centre, under.position.y, hud.end.y])


# A zone of his planted at `centre` and told to go at once: its ring's drawn rect, then the zone fizzled.
static func ring_of_zone_at(t, centre: Vector2) -> Rect2:
	var zone: Node2D = load("res://Scripts/GreysonEruptionScript.gd").new()
	zone.player = t.player
	zone.body = t.boss
	t.sm.add_hazard(zone, centre, t.boss.floor_layer)
	zone.schedule(0.5)
	await t.wait(3)
	var ring := ring_rect(t, zone)
	t.log_p("a zone at %s: ring %s" % [zone.global_position, ring])
	zone.fizzle()
	await t.wait(20)
	return ring


# The drawn rect of `zone`'s yellow ring, or an empty one.
static func ring_rect(t, zone: Node2D) -> Rect2:
	for tell in t.live_tells():
		if tell.name == "ParryTell%d" % zone.get_instance_id() and tell.get("sprite") is Sprite2D:
			var sprite: Sprite2D = tell.sprite
			return sprite.get_global_transform() * sprite.get_rect()
	return Rect2()
