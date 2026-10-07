extends RefCounted

# liam_tremors: attack 2 - the flood, the freeze and the stream of tremor walls (LiamTremors, LiamTremorBlock,
# LiamFlood, LiamTremorPatterns) - on his test scene.
#   stream    validate_stream finds nothing wrong for runs 0-2 (every gap order); on a whole run, each wall tells and
#             heaves on the slams the knobs put it on (+-1 frame), every marching wall moves march_step a slam at an
#             even speed (+-0.5 px), each new wall stays stream_every steps (+-1 px) above the one below it, no wall
#             rises onto a live one, a block sinks on the frame its bottom reaches march_floor_y, none touches the front
#             spot's clearance, and the timeout comes tremor_time after the heave
#   timeline  section 6.1's beats on his clock: the breath 0.3, the cracks 0.8, the heave 1.4, the timeout tremor_time after it,
#             and CRUMBLE_TIME after that his wind's reset, the ice and the player's footing on it kept, then Firestorm;
#             the downdraft holds a player walking up at the bottom from 0.7 s until the heave; the ice turns on under
#             the player once the front reaches them; the opening walls solid from the heave and every block crumbled at
#             the timeout
#   launch    a player above y 700 as the breath starts is blown down on rails to RESET_SPOT
#   touch     touching a wall on the ice: liam_tremor's damage (a full heart since the tuning round of 2026-10-04), and
#             bounced off its face at tremor_bounce
#   dash      a dash into a wall standing still (the opening hold): HIT, not DODGED, no perfect dodge, the dash not paid
#             back, never inside it
#   under     a wall heaving under the player, who stood at y 520 under it as it told: one hit, pushed straight down out
#             of it, then solid
#   round     the pillar's first hit crumbles every block at once, a telling wall's too, and no new wall comes; the ice
#             holds through the round and its blast; a sixth hit's fall keeps it too, the player's footing normal while he
#             is down and back on the ice as he gets up, and Firestorm next
#   gaps      runs 0-3 lay their opening walls where the stream says, their gaps in GAP_CYCLE's order
#   push      a player standing just under a gliding wall: one hit, pushed down and never up, the wall solid again
#   pinned    a player pinned against the bottom: one hit, and that block crumbles over them
#   moving    a dash into a gliding wall: HIT, not DODGED, no perfect dodge, never inside it
#   halfway   a player standing still at (960, 900) under the lower opening wall, the i-frames cleared every frame:
#             touched (on the ice, bounced down to the bottom) and then pinned, the wall costs them one hit

const Common := preload("res://art_source/defense_tests/liam/common.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const Patterns := preload("res://Scripts/LiamTremorPatterns.gd")
const Layout := preload("res://Scripts/LiamArtLayout.gd")
const LiamTremorBlock := preload("res://Scripts/LiamTremorBlock.gd")

const FRAME := 1.0 / 60.0

# The knob's own tremor_time, read as the run starts: what a run that doesn't set its own gets, and what is put back.
static var knob_tremor_time := 11.25


static func ridge_damage() -> int:
	return HitInfo.make(&"liam_tremor", null, Vector2.ZERO).damage


static func run(t) -> void:
	await Common.enter(t)
	knob_tremor_time = t.sm.tremor_time
	t.track()
	t.track_dodges()
	await stream(t)
	await timeline(t)
	await launch(t)
	await touch_and_dash(t)
	await under(t)
	await round_and_ice(t)
	await gaps(t)
	await push(t)
	await pinned(t)
	await moving_dash(t)
	await halfway(t)


# Tremors from the start of run `run`, `tremor_time` long (the knob's, unless given), on a dry ring: a run leaves its
# ice behind for attack 3.
static func begin(t, run: int, tremor_time := -1.0) -> Node:
	await Common.clear(t)
	if t.boss.flood.is_iced():
		t.boss.flood.thaw(0.01)
	t.boss.flood.drain(0.0)
	t.sm.set_player_ice(false)
	await t.wait(3)
	t.sm.tremor_runs = run
	t.sm.tremor_time = tremor_time if tremor_time >= 0.0 else knob_tremor_time
	Common.start(t, "Tremors")
	return t.sm.states["Tremors"]


# Wall k's blocks still standing.
static func live(tremors: Node, k: int) -> Array:
	for wall in tremors.walls:
		if wall.k == k and wall.has("blocks"):
			return wall.blocks.filter(func(b): return is_instance_valid(b) and b.phase != LiamTremorBlock.Phase.CRUMBLE)
	return []


# A block of wall k over x, or null.
static func block_at(tremors: Node, k: int, x: float) -> Node:
	for block in live(tremors, k):
		if block.rect.position.x + 40.0 <= x and x <= block.rect.end.x - 40.0:
			return block
	return null


static func stream(t) -> void:
	t.log_p("-- the stream")
	var sm: Node = t.sm
	var slams: int = roundi(sm.tremor_time / sm.slam_interval)
	for run in 3:
		var problems: Array = Patterns.validate_stream(run, sm.march_step, sm.march_delay_slams, sm.stream_every, slams, Patterns.ICE_PACE * sm.slam_interval, sm.march_floor_y, Patterns.RESET_STARTS, sm.stream_gap)
		t.check(problems.is_empty(), "run %d: validate_stream finds nothing wrong (%s)" % [run, problems])
	await Common.fresh(t, sm.FRONT_SPOT)
	var tremors: Node = await begin(t, 0)
	# The breath blows the player down to the reset spot: back up out of the walls' way once they heave.
	await t.wait_until(func(): return tremors.beats.has(&"heave"), 120)
	await Common.fresh(t, sm.FRONT_SPOT, 0)
	var tops := {}
	var spawn_wrong := []
	var sank := []
	var in_clearance := [0]
	var seen_blocks := {}
	var watch := func():
		t.player.is_invincible = true
		if not tremors.beats.has(&"heave") or tremors.beats.has(&"timeout"):
			return
		for wall in tremors.walls:
			if not wall.has("blocks"):
				continue
			var standing: Array = live(tremors, wall.k)
			if not standing.is_empty():
				if not tops.has(wall.k):
					tops[wall.k] = []
				tops[wall.k].append([tremors.clock, standing[0].rect.position.y])
			for block in wall.blocks:
				if not is_instance_valid(block):
					continue
				var id: int = block.get_instance_id()
				if not seen_blocks.has(id):
					seen_blocks[id] = true
					for other in tremors.blocks:
						if is_instance_valid(other) and other != block and not wall.blocks.has(other) and other.phase != LiamTremorBlock.Phase.CRUMBLE and other.rect.intersects(block.rect):
							spawn_wrong.append("wall %d onto %s" % [wall.k, other.rect])
				if block.phase == LiamTremorBlock.Phase.CRUMBLE and not sank.any(func(s): return s[0] == id):
					sank.append([id, block.rect.end.y])
				if block.phase != LiamTremorBlock.Phase.CRUMBLE and block.rect.intersects(Patterns.FRONT_CLEAR):
					in_clearance[0] += 1
	t.physics_frame.connect(watch)
	await t.wait_until(func(): return tremors.beats.has(&"timeout"), 60 * 20)
	t.physics_frame.disconnect(watch)
	t.player.is_invincible = false
	var heave: float = tremors.beats[&"heave"]
	var walls: Array = Patterns.schedule(0, sm.march_delay_slams, sm.stream_every, slams, sm.stream_gap)
	var off := []
	for wall: Dictionary in walls:
		var entry: Array = []
		for logged: Array in tremors.wall_log:
			if logged[0] == wall.k:
				entry = logged
		var tell_due: float = sm.crack_slam if wall.tell_slam < 0 else heave + wall.tell_slam * sm.slam_interval
		var heave_due: float = heave + wall.heave_slam * sm.slam_interval
		if entry.is_empty() or absf(entry[1] - tell_due) > FRAME + 0.001 or absf(entry[2] - heave_due) > FRAME + 0.001:
			off.append("wall %d %s (want %.2f, %.2f)" % [wall.k, entry, tell_due, heave_due])
	# Each marching wall a slam at a time: march_step a slam, the same every frame of it.
	var frames_a_slam: int = roundi(sm.slam_interval / FRAME)
	var per_frame: float = sm.march_step / frames_a_slam
	var uneven := []
	for k in tops:
		var samples: Array = tops[k]
		for i in range(1, samples.size()):
			var moved: float = samples[i][1] - samples[i - 1][1]
			if moved > 0.0001 and absf(moved - per_frame) > 0.05 and i + 1 < samples.size() and samples[i + 1][1] - samples[i][1] > 0.0001:
				uneven.append("wall %d at %.2f s: %.3f px" % [k, samples[i][0], moved])
		for i in range(frames_a_slam, samples.size()):
			var over_slam: float = samples[i][1] - samples[i - frames_a_slam][1]
			if over_slam > 0.0001 and samples[i - frames_a_slam][1] > samples[0][1] + 0.0001 and absf(over_slam - sm.march_step) > 0.5:
				uneven.append("wall %d by %.2f s: %.2f px a slam" % [k, samples[i][0], over_slam])
				break
	# Each new wall above the one below it, at every frame both stand.
	var spacing := []
	var apart: float = sm.stream_every * sm.march_step
	for k in tops:
		if k < Patterns.OPEN_TOPS.size() or not tops.has(k - 1):
			continue
		var heaved := INF
		for logged: Array in tremors.wall_log:
			if logged[0] == k:
				heaved = logged[2]
		var below := {}
		for sample: Array in tops[k - 1]:
			below[snappedf(sample[0], 0.0001)] = sample[1]
		for sample: Array in tops[k]:
			var under: Variant = below.get(snappedf(sample[0], 0.0001))
			if sample[0] >= heaved and under != null and absf(under - sample[1] - apart) > 1.0:
				spacing.append("walls %d-%d at %.2f s: %.1f px" % [k - 1, k, sample[0], under - sample[1]])
				break
	var sunk_wrong: Array = sank.filter(func(s): return s[1] < sm.march_floor_y - 0.001 or s[1] > sm.march_floor_y + per_frame + 0.001)
	t.log_p("walls %s; logged %s; %d sinks, bottoms %s; timeout at %.2f (heave %.2f)" % [walls.map(func(w): return "k%d gap %.0f tell %d heave %d" % [w.k, w.gap, w.tell_slam, w.heave_slam]), tremors.wall_log, sank.size(), sank.map(func(s): return snappedf(s[1], 0.1)), tremors.beats[&"timeout"], heave])
	t.check(off.is_empty(), "every wall tells and heaves on its slam (%s)" % [off])
	t.check(uneven.is_empty(), "every marching wall moves %.0f px a slam at an even speed (%s)" % [sm.march_step, uneven])
	t.check(spacing.is_empty(), "each new wall stays %.0f +-1 px above the one below it (%s)" % [apart, spacing])
	t.check(spawn_wrong.is_empty(), "no wall rises onto a live one (%s)" % [spawn_wrong])
	t.check(not sank.is_empty() and sunk_wrong.is_empty(), "a block sinks on the frame its bottom reaches y %.0f (%s)" % [sm.march_floor_y, sunk_wrong])
	t.check(in_clearance[0] == 0, "none touches the front spot's clearance")
	t.check(absf(tremors.beats[&"timeout"] - heave - sm.tremor_time) <= FRAME + 0.001, "the timeout %.2f s after the heave" % sm.tremor_time)
	Common.hold(t)


static func timeline(t) -> void:
	t.log_p("-- a whole run, the player walking up from the bottom")
	await Common.fresh(t, Vector2(1500, 900))
	var tremors: Node = await begin(t, 0)
	var sm: Node = t.sm
	t.press(KEY_UP)
	var highest := [INF]
	var iced_at := [-1.0]
	var solid_at_heave := [false]
	var watch := func():
		var clock: float = tremors.clock
		if clock >= 0.7 and not tremors.beats.has(&"heave"):
			highest[0] = minf(highest[0], t.player.global_position.y)
		if iced_at[0] < 0.0 and t.player.on_ice:
			iced_at[0] = clock
	t.physics_frame.connect(watch)
	await t.wait_until(func(): return tremors.beats.has(&"heave"), 120)
	t.release(KEY_UP)
	await t.wait(2)
	solid_at_heave[0] = tremors.blocks.all(func(b): return b.is_solid())
	var pinned_y: float = highest[0]
	await Common.fresh(t, sm.FRONT_SPOT, 2)
	await t.wait_until(func(): return tremors.beats.has(&"timeout"), 60 * 20)
	await t.wait(2)
	var crumbled: bool = t.get_nodes_in_group(sm.HAZARD_GROUP).filter(func(h): return h.has_method("is_solid") and h.is_solid()).is_empty()
	await t.wait_until(func(): return Common.state(t) != "Tremors", 120)
	t.physics_frame.disconnect(watch)
	var over_at: float = tremors.clock
	var reset: bool = Common.state(t) == "RoundBlast"
	var ice_kept: bool = t.boss.flood.is_iced()
	var next: bool = await t.wait_until(func(): return Common.state(t) == "Firestorm", 60 * 3)
	var footing_kept: bool = t.boss.flood.is_iced() and t.player.on_ice
	var beats: Dictionary = tremors.beats
	var want := {&"breath": sm.breath_start, &"crack": sm.crack_slam, &"heave": sm.heave_slam,
		&"timeout": sm.heave_slam + sm.tremor_time}
	var off := []
	for key in want:
		if not beats.has(key) or absf(beats[key] - want[key]) > FRAME + 0.001:
			off.append("%s %s (want %.2f)" % [key, beats.get(key, -1.0), want[key]])
	var front_reach: float = sm.breath_start + sm.PERCH.distance_to(Vector2(1500, 900)) / sm.freeze_speed
	t.log_p("beats %s; the player no higher than y %.0f from 0.7 s to the heave; on ice at %.2f s (the front reaches about %.2f)" % [beats, pinned_y, iced_at[0], front_reach])
	t.check(off.is_empty(), "the beats at 0.3, 0.8, 1.4 and +%.2f (%s)" % [sm.tremor_time, off])
	t.log_p("over at %.2f s (the timeout + %.2f due at %.2f), then %s; ice kept %s, footing kept through the reset %s" % [over_at, Layout.CRUMBLE_TIME, sm.heave_slam + sm.tremor_time + Layout.CRUMBLE_TIME, "his wind's reset" if reset else "no reset", ice_kept, footing_kept])
	t.check(reset and absf(over_at - (sm.heave_slam + sm.tremor_time + Layout.CRUMBLE_TIME)) <= FRAME + 0.001, "CRUMBLE_TIME after the timeout: his wind's reset, not a melt")
	t.check(pinned_y >= 860.0, "the downdraft holds a player walking up at the bottom until the heave (%.0f)" % pinned_y)
	t.check(iced_at[0] > sm.breath_start and absf(iced_at[0] - front_reach) <= 0.25, "their ice on as the front reaches them")
	t.check(solid_at_heave[0] and crumbled, "the opening walls solid from the heave, and every block crumbled at the timeout")
	t.check(ice_kept and footing_kept and next, "the ice and the player's footing on it kept, and Firestorm next")


static func launch(t) -> void:
	t.log_p("-- a player above y 700 as the breath starts")
	await Common.fresh(t, Vector2(400, 520))
	var tremors: Node = await begin(t, 0, 2.0)
	await t.wait_until(func(): return t.sm.is_launching(), 60)
	var sealed: bool = t.player.lock_seals_guard
	await t.wait_until(func(): return not t.sm.is_launching(), 60)
	var landed: Vector2 = t.player.global_position
	t.log_p("launched at %.2f s, sealed %s, landed %s" % [tremors.beats.get(&"breath", -1.0), sealed, landed])
	t.check(sealed and landed.distance_to(t.sm.RESET_SPOT) <= 1.0, "blown down on rails to %s" % t.sm.RESET_SPOT)
	Common.hold(t)


# Straight after the heave, in the opening walls' hold: a touch from below on the ice, then a dash up into one.
static func touch_and_dash(t) -> void:
	t.log_p("-- touching a wall on the ice")
	await Common.fresh(t, Vector2(1500, 900))
	var tremors: Node = await begin(t, 0)
	await t.wait_until(func(): return tremors.beats.has(&"heave"), 120)
	var block: Node = block_at(tremors, 0, 500.0)
	var face: Rect2 = block.rect
	# 20 px short of its reach, sliding up into it on the ice.
	await Common.fresh(t, Vector2(500.0, face.end.y + 6.0 + 20.0 + 39.0), 2)
	var health: int = t.player.playerHealth
	t.sm.set_player_ice(true)
	t.player.velocity = Vector2(0, -400)
	var bounced := [0.0]
	var watch := func(): bounced[0] = maxf(bounced[0], t.player.velocity.y)
	t.physics_frame.connect(watch)
	await t.wait_until(func(): return t.player.playerHealth < health, 40)
	await t.wait(2)
	t.physics_frame.disconnect(watch)
	t.log_p("health %d -> %d, bounced down at up to %.0f px/s" % [health, t.player.playerHealth, bounced[0]])
	t.check(t.player.playerHealth == health - ridge_damage(), "%d half-hearts" % ridge_damage())
	t.check(bounced[0] >= t.sm.tremor_bounce - 1.0, "bounced off its face at %.0f px/s" % t.sm.tremor_bounce)

	t.log_p("-- a dash into a wall standing still")
	block = block_at(tremors, 0, 700.0)
	var still: Rect2 = block.rect
	await Common.fresh(t, Vector2(700.0, still.end.y + 160.0), 0)
	t.sm.set_player_ice(true)
	var stamina: float = t.defense.stamina
	var dodges_before: int = t.dodges.size()
	var inside := [false]
	var moved := [false]
	# Only while it is solid: a later step coming down on them goes non-solid to push them out, by design.
	var in_watch := func():
		inside[0] = inside[0] or (block.is_solid() and Common.player_box(t).grow(-0.5).intersects(block.rect))
		moved[0] = moved[0] or block.marching
	t.physics_frame.connect(in_watch)
	t.press(KEY_UP)
	t.tap(KEY_W)
	await t.wait(30)
	t.release(KEY_UP)
	t.physics_frame.disconnect(in_watch)
	var results: Array = block.results.map(func(r): return HitInfo.Result.keys()[r])
	t.log_p("results %s, perfect dodges %d, stamina %.1f -> %.1f, inside %s, the wall moved meanwhile %s" % [results, t.dodges.size() - dodges_before, stamina, t.defense.stamina, inside[0], moved[0]])
	t.check(block.results.has(HitInfo.Result.HIT) and not block.results.has(HitInfo.Result.DODGED), "HIT, not DODGED")
	t.check(t.dodges.size() == dodges_before and t.defense.stamina < stamina - 1.0, "no perfect dodge, and the dash is not paid back")
	t.check(not inside[0], "never inside the wall")
	Common.hold(t)


# The first stream wall tells at the top with the player standing at y 520 under it, and heaves on them.
static func under(t) -> void:
	t.log_p("-- a wall heaving under the player")
	await Common.fresh(t, t.sm.FRONT_SPOT)
	var tremors: Node = await begin(t, 0)
	var k := Patterns.OPEN_TOPS.size()
	await t.wait_until(func(): return tremors.wall_log.any(func(e): return e[0] == k and e[1] >= 0.0), 60 * 12)
	var block: Node = block_at(tremors, k, 700.0)
	var home: Rect2 = block.rect
	await Common.fresh(t, Vector2(700.0, 520.0), 0)
	var health := 1000
	var pushed_up := [false]
	var start_y: float = t.player.global_position.y
	var watch := func(): pushed_up[0] = pushed_up[0] or t.player.global_position.y < start_y - 2.0
	t.physics_frame.connect(watch)
	await t.wait_until(func(): return block.phase == LiamTremorBlock.Phase.RISEN, 60)
	await t.wait_until(func(): return block.is_solid(), 60)
	await t.wait(20)
	t.physics_frame.disconnect(watch)
	t.log_p("told over them at %s, under %s, results %s, health %d -> %d, now at %s, solid %s" % [home, block.heaved_under, block.results, health, t.player.playerHealth, t.player.global_position, block.is_solid()])
	t.check(block.heaved_under and block.results == [HitInfo.Result.HIT] and t.player.playerHealth == health - ridge_damage(), "one hit")
	t.check(not pushed_up[0] and not Common.player_box(t).grow(block.UNDER_MARGIN).intersects(block.rect), "pushed straight down out of it, never up through it")
	t.check(block.is_solid(), "and then solid")
	Common.hold(t)


static func round_and_ice(t) -> void:
	t.log_p("-- the pillar's first hit, a new wall telling, the round and the blast")
	await Common.fresh(t, t.sm.FRONT_SPOT)
	var tremors: Node = await begin(t, 0)
	var k := Patterns.OPEN_TOPS.size()
	await t.wait_until(func(): return tremors.wall_log.any(func(e): return e[0] == k and e[1] >= 0.0), 60 * 12)
	var ridges: Array = tremors.blocks.duplicate()
	var telling: Array = live(tremors, k)
	await Common.fresh(t, t.sm.FRONT_SPOT, 0)
	var took: bool = await Common.punch_pillar(t)
	await t.wait(1)
	var none_solid: bool = ridges.all(func(b): return not is_instance_valid(b) or not b.is_solid())
	var tell_crumbled: bool = not telling.is_empty() and telling.all(func(b): return not is_instance_valid(b) or b.phase == LiamTremorBlock.Phase.CRUMBLE)
	var iced: bool = t.boss.flood.is_iced()
	var count: int = tremors.wall_log.size()
	await t.wait(30)
	var gone: bool = ridges.all(func(b): return not is_instance_valid(b))
	await t.wait_until(func(): return Common.state(t) == "RoundBlast", 180)
	var no_more: bool = tremors.wall_log.size() == count and t.get_nodes_in_group(t.sm.HAZARD_GROUP).filter(func(h): return h is LiamTremorBlock).is_empty()
	await t.wait_until(func(): return Common.state(t) != "RoundBlast", 180)
	var held_through: bool = t.boss.flood.is_iced() and t.boss.flood.ice != t.boss.flood.Ice.SHATTERING
	t.log_p("took %s, none solid %s, the telling wall crumbled %s, ice held %s, all gone %s, no new wall %s, ice after the blast %s, then %s" % [took, none_solid, tell_crumbled, iced, gone, no_more, held_through, Common.state(t)])
	t.check(took and none_solid and gone and tell_crumbled, "every block crumbled at once, the telling wall's too")
	t.check(no_more, "and no new wall came")
	t.check(iced and held_through, "the ice held through the round and its blast")
	Common.hold(t)

	t.log_p("-- a sixth hit in Tremors")
	await Common.fresh(t, Vector2(1500, 900))
	tremors = await begin(t, 0)
	t.sm.pillar_hits = 5
	await t.wait_until(func(): return tremors.beats.has(&"heave"), 120)
	await Common.fresh(t, t.sm.FRONT_SPOT, 2)
	t.sm.set_player_ice(true)
	var toppled: bool = await Common.punch_pillar(t)
	await t.wait(2)
	var kept: bool = t.boss.flood.is_iced() and t.boss.flood.ice != t.boss.flood.Ice.SHATTERING
	var footing_off: bool = not t.player.on_ice
	await t.wait_until(func(): return Common.state(t) == "Downed", 90)
	var down_kept: bool = t.boss.flood.is_iced() and not t.player.on_ice
	var getup: Node = t.sm.states["GetUp"]
	var footing_back := [false]
	var watch := func():
		if Common.state(t) == "GetUp" and getup.beat == getup.Beat.ROW:
			footing_back[0] = false
		elif Common.state(t) == "Firestorm" and not footing_back[0]:
			footing_back[0] = t.player.on_ice
	t.physics_frame.connect(watch)
	var next: bool = await t.wait_until(func(): return Common.state(t) != "Downed" and Common.state(t) != "GetUp", 60 * 12)
	await t.wait(1)
	t.physics_frame.disconnect(watch)
	t.log_p("toppled %s, ice kept %s, footing off %s, through the window %s; then %s, the player on the ice again %s" % [toppled, kept, footing_off, down_kept, Common.state(t), footing_back[0]])
	t.check(toppled and kept and footing_off and down_kept, "his fall keeps the ice, the player's footing normal while he is down")
	t.check(next and Common.state(t) == "Firestorm" and footing_back[0], "up again: the player on the ice again, and Firestorm next")
	Common.hold(t)


static func gaps(t) -> void:
	t.log_p("-- four runs")
	await Common.fresh(t, t.sm.FRONT_SPOT)
	var wrong := []
	for run in 4:
		var tremors: Node = await begin(t, run, 0.5)
		for k in Patterns.OPEN_TOPS.size():
			var want: Array[Rect2] = Patterns.stream_wall(Patterns.gap_centre(run, k), Patterns.OPEN_TOPS[k], t.sm.stream_gap)
			var laid: Array = live(tremors, k).map(func(b): return Rect2(b.global_position, b.rect.size))
			var same: bool = laid.size() == want.size() and range(laid.size()).all(func(i): return laid[i] == want[i])
			if not same or Patterns.gap_centre(run, k) != Patterns.GAP_CYCLE[(2 * run + k) % Patterns.GAP_CYCLE.size()]:
				wrong.append("run %d wall %d" % [run, k])
		await t.wait_until(func(): return Common.state(t) != "Tremors", 60 * 4)
		Common.hold(t)
	t.sm.tremor_time = knob_tremor_time
	t.check(wrong.is_empty(), "each run's opening walls where the stream lays them, their gaps in GAP_CYCLE's order (%s)" % [wrong])


# The player's box just out of a gliding wall's reach as it comes down on them, off the ice (on it, the touch would
# bounce them clear before the wall got there).
static func push(t) -> void:
	t.log_p("-- a wall gliding down onto a player just under it")
	await Common.fresh(t, t.sm.FRONT_SPOT)
	var tremors: Node = await begin(t, 0)
	await t.wait_until(func(): return tremors.march_steps >= 1, 60 * 4)
	t.boss.flood.thaw(0.01)
	await t.wait(2)
	t.sm.set_player_ice(false)
	var block: Node = block_at(tremors, 0, 500.0)
	await Common.fresh(t, Vector2(500.0, block.rect.end.y + 60.0), 0)
	t.player.global_position.y += block.rect.end.y + block.REACH + 2.0 - Common.player_box(t).position.y
	await t.wait(1)
	var health: int = t.player.playerHealth
	var went_up := [false]
	var pushed := [false]
	var last_y := [t.player.global_position.y]
	var watch := func():
		if block.pushing:
			pushed[0] = true
			went_up[0] = went_up[0] or t.player.global_position.y < last_y[0] - 0.001
		last_y[0] = t.player.global_position.y
	t.physics_frame.connect(watch)
	await t.wait_until(func(): return pushed[0] and not block.pushing, 60 * 2)
	await t.wait(3)
	t.physics_frame.disconnect(watch)
	var clear: bool = not Common.player_box(t).grow(block.UNDER_MARGIN).intersects(block.rect)
	t.log_p("results %s, health %d -> %d, pushed %s, up %s, clear %s, solid %s" % [block.results.map(func(r): return HitInfo.Result.keys()[r]), health, t.player.playerHealth, pushed[0], went_up[0], clear, block.is_solid()])
	t.check(pushed[0] and block.results == [HitInfo.Result.HIT] and t.player.playerHealth == health - ridge_damage(), "one hit, and pushed")
	t.check(not went_up[0] and clear, "pushed down out of it, their y never going up")
	t.check(block.is_solid(), "and the wall solid again")
	Common.hold(t)


# The lower opening wall coming down on a player standing against the bottom under it.
static func pinned(t) -> void:
	t.log_p("-- a wall gliding down onto a player pinned against the bottom")
	await Common.fresh(t, t.sm.FRONT_SPOT)
	var tremors: Node = await begin(t, 0)
	await t.wait_until(func(): return tremors.beats.has(&"heave"), 120)
	var block: Node = block_at(tremors, 0, 500.0)
	await Common.fresh(t, Vector2(500.0, 1000.0), 0)
	var box: Rect2 = Common.player_box(t)
	var health: int = t.player.playerHealth
	var solid_on_them := [false]
	var watch := func():
		if is_instance_valid(block) and block.is_solid() and Common.player_box(t).grow(-0.5).intersects(block.rect):
			solid_on_them[0] = true
	t.physics_frame.connect(watch)
	await t.wait_until(func(): return block.phase == LiamTremorBlock.Phase.CRUMBLE, 60 * 10)
	t.physics_frame.disconnect(watch)
	var crumbled_at: float = block.rect.end.y
	t.log_p("the player's box bottom %.1f (pinned from %.0f); the block crumbled with its bottom at %.1f; results %s, health %d -> %d" % [box.end.y, t.sm.march_floor_y - block.pinned_margin, crumbled_at, block.results.map(func(r): return HitInfo.Result.keys()[r]), health, t.player.playerHealth])
	t.check(box.end.y >= t.sm.march_floor_y - block.pinned_margin, "the player is pinned against the bottom")
	t.check(block.results == [HitInfo.Result.HIT] and t.player.playerHealth == health - ridge_damage(), "one hit")
	t.check(crumbled_at < t.sm.march_floor_y and not solid_on_them[0], "and the block crumbles over them, never solid on them")
	Common.hold(t)


# A dash up into the lower opening wall while it glides.
static func moving_dash(t) -> void:
	t.log_p("-- a dash into a gliding wall")
	await Common.fresh(t, t.sm.FRONT_SPOT)
	var tremors: Node = await begin(t, 0)
	await t.wait_until(func(): return tremors.march_steps >= 1, 60 * 4)
	var block: Node = block_at(tremors, 0, 700.0)
	await Common.fresh(t, Vector2(700.0, block.rect.end.y + 160.0), 0)
	t.sm.set_player_ice(true)
	var stamina: float = t.defense.stamina
	var dodges_before: int = t.dodges.size()
	var inside := [false]
	var met_moving := [false]
	var in_watch := func():
		inside[0] = inside[0] or (block.is_solid() and Common.player_box(t).grow(-0.5).intersects(block.rect))
		met_moving[0] = met_moving[0] or (block.marching and not block.results.is_empty())
	t.physics_frame.connect(in_watch)
	t.press(KEY_UP)
	t.tap(KEY_W)
	await t.wait(30)
	t.release(KEY_UP)
	t.physics_frame.disconnect(in_watch)
	var results: Array = block.results.map(func(r): return HitInfo.Result.keys()[r])
	t.log_p("results %s (met while gliding %s), perfect dodges %d, stamina %.1f -> %.1f, inside %s" % [results, met_moving[0], t.dodges.size() - dodges_before, stamina, t.defense.stamina, inside[0]])
	t.check(met_moving[0] and block.results.has(HitInfo.Result.HIT) and not block.results.has(HitInfo.Result.DODGED), "HIT while it glides, not DODGED")
	t.check(t.dodges.size() == dodges_before, "no perfect dodge")
	t.check(not inside[0], "never inside it")
	Common.hold(t)


# The player standing still at (960, 900) under the lower opening wall from the heave on: it glides onto them, its touch
# bouncing them down on the ice (or pushing them, off it) to the bottom, then pins them. The i-frames are cleared every
# frame, so only the block's own latch can keep a second hit off.
static func halfway(t) -> void:
	t.log_p("-- a player standing still at (960, 900) under the lower opening wall")
	await Common.fresh(t, Vector2(960, 900))
	var tremors: Node = await begin(t, 0)
	await t.wait_until(func(): return tremors.beats.has(&"heave"), 120)
	await Common.fresh(t, Vector2(960, 900), 0)
	var block: Node = block_at(tremors, 0, 960.0)
	var wall: Array = live(tremors, 0)
	var health: int = t.player.playerHealth
	var pushes := [0]
	var was_pushing := [false]
	var watch := func():
		t.clear_iframes()
		if is_instance_valid(block):
			if block.pushing and not was_pushing[0]:
				pushes[0] += 1
			was_pushing[0] = block.pushing
	t.physics_frame.connect(watch)
	await t.wait_until(func(): return block.phase == LiamTremorBlock.Phase.CRUMBLE, 60 * 8)
	t.physics_frame.disconnect(watch)
	var crumbled: bool = block.phase == LiamTremorBlock.Phase.CRUMBLE
	var bottom: float = block.rect.end.y
	var hits := 0
	for piece in wall:
		if is_instance_valid(piece):
			hits += piece.results.count(HitInfo.Result.HIT)
	t.log_p("%d pushes, then %s with its bottom at %.0f; %d hits from the wall's blocks, health %d -> %d" % [pushes[0], "crumbled" if crumbled else "still standing", bottom, hits, health, t.player.playerHealth])
	t.check(crumbled and bottom < t.sm.march_floor_y, "the wall came down on them and crumbled pinning them")
	t.check(hits == 1 and t.player.playerHealth == health - ridge_damage(), "one hit in all, whichever of its overlapping blocks it came from")
	Common.hold(t)
