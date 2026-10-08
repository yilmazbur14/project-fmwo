extends RefCounted

# greyson_poses (coder C; coder B since the 2026-09-30 pace): his six poses (GreysonPose) in his test fight, his cycle
# parked and the poses entered from Idle, each part on a fresh meter unless it says otherwise. His meter banks
# GreysonPose.bank (2 cells) a clean pose, and any hit that lands empties it (GreysonScript.hit_resets_hype).
#   clean     nothing touches him: the strikes turn_time in and then every 1.5 s, to the frame, A B C; his window
#             shut for the turn and open from the first strike; three banks of two cells, each with a cheer; and
#             the third, filling the meter, fires the spirit bomb.
#   spoils    poses 1-2 left alone, 3-6 punched: two banks, then four spoils, each with a boo and pose_hit; the
#             first punch empties the four cells at once and the meter shows it draining, the later ones find it
#             empty; the meter at 0 and the phase played out into Idle. The second punch of a pair in pose 4 deals
#             its damage too.
#   zones     a zone waiting from Slams for each of the pose's eruptions, going off oldest first at them from the
#             first strike, each told eruption_notice before it goes, or as the poses begin.
#   carry     poses 1 and 4 punched, the rest banked: the phase leaves 4 cells, the next phase starts on them and
#             its first bank fills the meter and fires the spirit bomb.
#   finisher  a combo from pose 2's strike dazes him and the mash lands the uppercut: the combo's damage and the
#             single-bar uppercut's 19; the meter empty from the combo's first punch; that pose never resolved; the
#             zones still waiting fizzled, none going off; and him staggered into Idle.

const BODY := "Arena/GreysonScene/GreysonCharacterBody"
const ZONE_SCRIPT := "res://Scripts/GreysonEruptionScript.gd"
const SEED := 20260924
const FRAME := 1.0 / 60.0
# Where the player waits, clear of him and of the zones below, which are clear of the punch beside him too.
const CLEAR := Vector2(1400, 440)
const ZONE_SPOTS: Array[Vector2] = [Vector2(330, 820), Vector2(1590, 820), Vector2(330, 300), Vector2(480, 560),
	Vector2(250, 560), Vector2(1590, 300), Vector2(960, 900), Vector2(640, 900), Vector2(1280, 900), Vector2(250, 900)]
const POSES: Array[StringName] = [&"pose_a", &"pose_b", &"pose_c", &"pose_a", &"pose_b", &"pose_c"]


static func run(t) -> void:
	await enter(t)
	await clean(t)
	await spoils(t)
	await zones(t)
	await carry(t)
	await finisher(t)
	park(t)


static func enter(t) -> void:
	await t.load_fight("greyson")
	t.boss = t.current_scene.get_node(BODY)
	t.sm = t.boss.state_machine
	t.sm.rng.seed = SEED
	t.player.playerHealth = 1000000
	t.player.get_node("Finisher").min_press_interval = 0.0
	park(t)


static func park(t) -> void:
	t.sm.on_child_transition(t.sm.current_state, "Idle")
	t.stop_boss_timers()


# At HOME and parked on `hype` cells, full health, his HUD up, nothing of his on the mat, the player free at CLEAR
# with the combo's count clear.
static func reset(t, hype := 0.0) -> void:
	park(t)
	t.player.combo.reset()
	load("res://Scripts/ScreenView.gd").reset(t)
	t.sm.clear_pending_zones()
	for hazard in t.get_nodes_in_group(t.sm.HAZARD_GROUP):
		hazard.queue_free()
	t.boss.global_position = t.sm.HOME
	t.boss.show_body()
	t.boss.play_anim(&"idle")
	t.boss.restore_hud()
	t.boss.boss_health = t.boss.max_health
	t.boss.reset_hype()
	t.boss.add_hype(hype)
	t.player.is_talking = false
	t.player.clear_face_point()
	t.player.global_position = CLEAR
	await t.wait(3)


static func pose_state(t) -> Node:
	return t.sm.states["Pose"]


static func start(t) -> void:
	t.sm.on_child_transition(t.sm.current_state, "Pose")


static func sound_playing(t, key: StringName) -> bool:
	return t.boss.sfx_players.get(key, []).any(func(sfx): return sfx.playing)


# Beside him within a punch's reach, then one swing; the damage it dealt.
static func punch(t) -> int:
	t.player.global_position = t._bot_punch_spot()
	await t.wait(2)
	return await t.swing()


static func clean(t) -> void:
	await reset(t)
	t.log_p("-- clean: nothing touches him")
	var pose := pose_state(t)
	var bomb: Node = t.sm.states["SpiritBomb"]
	start(t)
	var anims: Array[StringName] = []
	var hypes: Array[float] = []
	var cheers: Array[bool] = []
	var shut_in_turn := true
	var open_in_poses := true
	for i in 900:
		await t.wait(1)
		if pose.outcomes.size() > hypes.size():
			hypes.append(t.boss.hype)
			cheers.append(sound_playing(t, &"crowd_cheer"))
		if t.sm.current_state == bomb:
			break
		if pose.pose_index < 0:
			shut_in_turn = shut_in_turn and not t.boss.hurtbox.monitoring
		else:
			open_in_poses = open_in_poses and (t.boss.hurtbox.monitoring or pose.pose_clock < 2.0 * FRAME)
		if pose.strike_times.size() > anims.size():
			anims.append(t.boss.current_anim)
	var strikes: Array[float] = pose.strike_times
	var on_clock := strikes.size() == 3
	for k in strikes.size():
		on_clock = on_clock and absf(strikes[k] - (pose.turn_time + pose.pose_time * k)) <= FRAME + 0.0001
	t.log_p("strikes %s, anims %s, hype after each %s, cheers %s, outcomes %s" % [strikes.map(func(x): return snappedf(x, 0.001)), anims, hypes, cheers, pose.outcomes])
	t.check(on_clock, "three strikes, %.2f s in and then every %.1f s, to the frame" % [pose.turn_time, pose.pose_time])
	t.check(anims == POSES.slice(0, 3), "A B C (%s)" % [anims])
	t.check(shut_in_turn and open_in_poses, "his window shut for the turn and open from the first strike")
	t.check(is_equal_approx(pose.bank, 2.0) and hypes == [2.0, 4.0, 6.0] and pose.outcomes.all(func(o): return o == &"banked"), "three banks of two cells each (%s)" % [hypes])
	t.check(cheers.size() == 3 and cheers.all(func(c): return c), "each with a cheer")
	t.check(t.sm.current_state == bomb and bomb.entered_count == 1, "the third fills the meter and fires the spirit bomb (%s)" % t.sm.current_state.name)


static func spoils(t) -> void:
	await reset(t)
	t.log_p("-- spoils: poses 1-2 left alone, 3-6 punched: each hit empties the meter")
	var pose := pose_state(t)
	start(t)
	var drained: Array[float] = []
	var boos: Array[bool] = []
	var hit_anims: Array[StringName] = []
	var pair := {}
	var shown_from := [-1.0]
	var health: int = t.boss.boss_health
	for index in range(2, 6):
		await t.wait_until(func(): return pose.pose_index == index and pose.pose_clock >= 0.3, 400)
		var before: float = t.boss.hype
		# Each pose's punches a combo of their own: the count carries (PlayerCombo), and a POW would daze him
		# out of the phase.
		t.player.combo.reset()
		var dealt: int = await punch(t)
		drained.append(before - t.boss.hype)
		if index == 2:
			shown_from[0] = t.boss.hype_meter.drain_from
		boos.append(sound_playing(t, &"crowd_boo"))
		hit_anims.append(t.boss.current_anim)
		if index == 3:
			await t.wait(6)
			var mid: float = t.boss.hype
			var second: int = await t.swing()
			pair = {"first": dealt, "second": second, "drained_by_second": mid - t.boss.hype, "same_pose": pose.pose_index == 3}
		t.player.global_position = CLEAR
	await t.wait_until(func(): return t.sm.current_state != pose, 400)
	t.log_p("outcomes %s, drained %s, boos %s, anims after the hit %s, the pair %s, health %d -> %d, hype %.1f" % [pose.outcomes, drained, boos, hit_anims, pair, health, t.boss.boss_health, t.boss.hype])
	t.check(pose.outcomes == [&"banked", &"banked", &"spoiled", &"spoiled", &"spoiled", &"spoiled"], "two banks, four spoils (%s)" % [pose.outcomes])
	t.check(drained == [4.0, 0.0, 0.0, 0.0], "the first punch empties the four cells at once; the later ones find it empty (%s)" % [drained])
	t.check(is_equal_approx(shown_from[0], 4.0) and t.boss.hype_meter.shown == 0.0, "the meter drains from 4 to 0 to show it (from %.1f)" % shown_from[0])
	t.check(boos.all(func(b): return b) and hit_anims.all(func(a): return a == &"pose_hit"), "each with a boo, pose_hit on him")
	t.check(pair.get("same_pose", false) and pair.get("second", 0) > 0 and is_equal_approx(pair.get("drained_by_second", -1.0), 0.0),
		"a second punch in a pose deals its damage too (%s)" % [pair])
	t.check(is_equal_approx(t.boss.hype, 0.0), "the meter back at 0 (%.1f)" % t.boss.hype)
	t.check(t.sm.current_state == t.sm.states["Idle"], "the phase played out into Idle (%s)" % t.sm.current_state.name)


static func zones(t) -> void:
	await reset(t)
	t.log_p("-- zones: one waiting from Slams for each eruption")
	var pose := pose_state(t)
	var went_off: Array[float] = []
	var order: Array[int] = []
	var told_ahead: Array[float] = []
	var zone_script: GDScript = load(ZONE_SCRIPT)
	var count: int = pose.eruptions.size()
	for k in count:
		var zone: Node2D = zone_script.new()
		zone.body = t.boss
		zone.player = t.player
		t.sm.add_hazard(zone, ZONE_SPOTS[k], t.boss.floor_layer)
		t.sm.add_pending_zone(zone)
		var went := func():
			went_off.append(pose.phase_clock)
			order.append(k)
			told_ahead.append(zone.erupt_after)
		zone.erupted.connect(went)
	start(t)
	# Nothing banks here: this is about the zones' clock, and three banks would fire the bomb as the last one goes.
	var hold := func(): t.boss.reset_hype()
	t.physics_frame.connect(hold)
	await t.wait_until(func(): return went_off.size() == count or t.sm.current_state != pose, 900)
	t.physics_frame.disconnect(hold)
	var strikes: Array[float] = pose.strike_times
	var slack := 2.0 * FRAME + 0.0001
	var on_time: bool = went_off.size() == pose.eruptions.size() and strikes.size() >= 3
	for k in went_off.size():
		on_time = on_time and absf(went_off[k] - (strikes[0] + pose.eruptions[k])) <= slack
	t.log_p("strikes %s, zones %s went off at %s, told %s s before" % [strikes.map(func(x): return snappedf(x, 0.001)), order.map(func(k): return k + 1),
		went_off.map(func(x): return snappedf(x, 0.001)), told_ahead.map(func(x): return snappedf(x, 0.001))])
	t.check(on_time and order == range(count), "oldest first, at %s s from the first strike" % [pose.eruptions])
	var noticed: bool = told_ahead.size() == pose.eruptions.size()
	for k in told_ahead.size():
		noticed = noticed and absf(told_ahead[k] - minf(pose.eruption_notice, pose.eruptions[k] + pose.turn_time)) <= slack
	t.check(noticed, "each told %.2f s before it goes, or as the poses begin" % pose.eruption_notice)
	park(t)


static func carry(t) -> void:
	await reset(t)
	t.log_p("-- carry: poses 1 and 4 punched, the rest banked, then the next phase")
	var pose := pose_state(t)
	start(t)
	for index in [0, 3]:
		await t.wait_until(func(): return pose.pose_index == index and pose.pose_clock >= 0.3, 600)
		t.player.combo.reset()
		await punch(t)
		t.player.global_position = CLEAR
	await t.wait_until(func(): return t.sm.current_state != pose, 700)
	var left: float = t.boss.hype
	t.log_p("the phase left %.1f (outcomes %s)" % [left, pose.outcomes])
	t.check(is_equal_approx(left, 4.0) and pose.outcomes == [&"spoiled", &"banked", &"banked", &"spoiled", &"banked", &"banked"],
		"each punch emptied it, then two banks: 4 (%.1f)" % left)
	start(t)
	await t.wait_until(func(): return pose.pose_index == 0, 60)
	var shown: float = t.boss.hype_meter.shown
	await t.wait_until(func(): return pose.outcomes.size() == 1 or t.sm.current_state != pose, 200)
	t.log_p("the next phase's first strike: hype %.1f, the meter %.1f; then %s" % [left, shown, t.sm.current_state.name])
	t.check(is_equal_approx(t.boss.hype, 6.0) and is_equal_approx(shown, 4.0), "the next phase starts on the meter the last left, 4, and banks on to full (%.1f)" % t.boss.hype)
	t.check(t.sm.current_state == t.sm.states["SpiritBomb"], "which fires the spirit bomb in that phase's first pose")
	park(t)


static func finisher(t) -> void:
	await reset(t)
	t.log_p("-- finisher: a combo from pose 2's strike, the mash, the uppercut")
	var pose := pose_state(t)
	var zone_script: GDScript = load(ZONE_SCRIPT)
	var planted: Array = []
	var went_off: Array[int] = []
	for k in ZONE_SPOTS.size():
		var zone: Node2D = zone_script.new()
		zone.body = t.boss
		zone.player = t.player
		t.sm.add_hazard(zone, ZONE_SPOTS[k], t.boss.floor_layer)
		t.sm.add_pending_zone(zone)
		zone.erupted.connect(func(): went_off.append(k))
		planted.append(zone)
	var finisher_node: Node = t.player.get_node("Finisher")
	start(t)
	await t.wait_until(func(): return pose.pose_index == 1, 400)
	var health: int = t.boss.boss_health
	var hype: float = t.boss.hype
	var hit_in: Array[int] = []
	var emptied_at := [-1]
	var landed := func(_target, _dealt, _charged):
		hit_in.append(pose.pose_index)
		if emptied_at[0] < 0 and t.boss.hype == 0.0:
			emptied_at[0] = hit_in.size() - 1
	t.player.combo.punch_landed.connect(landed)
	t.player.global_position = t._bot_punch_spot()
	for n in 3:
		await t.swing()
		if n < 2:
			await t.wait(6)
	var dazed: bool = await t.wait_until(func(): return finisher_node.phase == t.FINISHER_DAZED and finisher_node.prompt_visible, 120)
	var combo: int = health - t.boss.boss_health
	var in_pose: int = pose.pose_index
	var waiting: Array = range(planted.size()).filter(func(k): return is_instance_valid(planted[k]) and planted[k].is_pending())
	var went_before: Array = went_off.duplicate()
	await t.mash_finisher()
	await t.wait_until(func(): return finisher_node.phase == t.FINISHER_OFF, 300)
	var total: int = health - t.boss.boss_health
	var zone_left: bool = waiting.is_empty() or waiting.any(func(k): return k in went_off or (is_instance_valid(planted[k]) and planted[k].is_pending()))
	var poses_hit := {in_pose: true}
	for index in hit_in:
		poses_hit[index] = true
	t.log_p("punches landed in poses %s, dazed %s in pose %d; combo %d, then the finisher %d (total %d); hype %.1f -> %.1f; outcomes %s; zones gone off before the daze %s, waiting at it %s, gone off after %s; he is in %s" % [hit_in.map(func(i): return i + 1), dazed, in_pose + 1, combo, total - combo, total, hype, t.boss.hype, pose.outcomes,
		went_before.map(func(k): return k + 1), waiting.map(func(k): return k + 1), went_off.slice(went_before.size()).map(func(k): return k + 1), t.sm.current_state.name])
	t.check(dazed, "the combo's charged third punch dazes him")
	t.check(combo > 0 and total - combo == 19, "the combo's %d and the single-bar uppercut's 19 (%d)" % [combo, total - combo])
	t.check(is_equal_approx(hype, pose.bank) and is_equal_approx(t.boss.hype, 0.0) and emptied_at[0] == 0,
		"pose 1's bank, %.1f, gone at the combo's first punch (the meter at %.1f, emptied at punch %d)" % [hype, t.boss.hype, emptied_at[0] + 1])
	t.check(pose.outcomes.size() == in_pose, "the pose he was dazed in never resolves (%s)" % [pose.outcomes])
	t.check(not zone_left, "the zones still waiting as the daze caught him fizzle with the phase, none going off")
	t.check(t.sm.current_state == t.sm.states["Idle"] and not pose.live, "the phase is over: staggered into Idle (%s)" % t.sm.current_state.name)
