extends RefCounted

# greyson_poses (coder C): his six poses (GreysonPose) in his test fight, his cycle parked and the poses entered
# from Idle, each part on a fresh meter unless it says otherwise.
#   clean     nothing touches him: the strikes 0.3 s in and then every 1.5 s, to the frame, A B C A B C; his window
#             shut for the turn and open from the first strike; six banks of a cell each, each with a cheer; and
#             the sixth, filling the meter, fires the spirit bomb.
#   spoils    poses 1-2 left alone, 3-6 punched: two banks, four spoils of half a cell each with a boo and
#             pose_hit, the meter back at 0 and the phase played out into Idle. The second punch of a pair in
#             pose 4 deals its damage and drains nothing.
#   zones     five zones waiting from Slams, going off oldest first at the pose's eruptions from the first
#             strike, the last as pose 3 resolves, each told eruption_notice before it goes, or as the poses begin.
#   carry     the meter where one phase left it as the next begins, and banking on from there.
#   finisher  a combo on the beat from pose 2's strike, its third punch charged, dazes him and the mash lands the
#             uppercut: 12 damage; half a cell off for each pose a hit landed in - the combo's, and the uppercut's
#             in the pose the daze caught him in, which can be the next one; that pose never resolved; the zones
#             still waiting fizzled, none going off; and him staggered into Idle.

const BODY := "Arena/GreysonScene/GreysonCharacterBody"
const ZONE_SCRIPT := "res://Scripts/GreysonEruptionScript.gd"
const SEED := 20260924
const FRAME := 1.0 / 60.0
# Where the player waits, clear of him and of the zones below, which are clear of the punch beside him too.
const CLEAR := Vector2(1400, 440)
const ZONE_SPOTS: Array[Vector2] = [Vector2(330, 820), Vector2(1590, 820), Vector2(330, 300), Vector2(480, 560),
	Vector2(250, 560)]
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


# At HOME and parked on `hype` cells, full health, his HUD up, nothing of his on the mat, the player free at CLEAR.
static func reset(t, hype := 0.0) -> void:
	park(t)
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
	var on_clock := strikes.size() == 6
	for k in strikes.size():
		on_clock = on_clock and absf(strikes[k] - (0.3 + 1.5 * k)) <= FRAME + 0.0001
	t.log_p("strikes %s, anims %s, hype after each %s, cheers %s, outcomes %s" % [strikes.map(func(x): return snappedf(x, 0.001)), anims, hypes, cheers, pose.outcomes])
	t.check(on_clock, "six strikes, 0.3 s in and then every 1.5 s, to the frame")
	t.check(anims == POSES, "A B C A B C (%s)" % [anims])
	t.check(shut_in_turn and open_in_poses, "his window shut for the turn and open from the first strike")
	t.check(hypes == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0] and pose.outcomes.all(func(o): return o == &"banked"), "six banks of a cell each (%s)" % [hypes])
	t.check(cheers.size() == 6 and cheers.all(func(c): return c), "each with a cheer")
	t.check(t.sm.current_state == bomb and bomb.entered_count == 1, "the sixth fills the meter and fires the spirit bomb (%s)" % t.sm.current_state.name)


static func spoils(t) -> void:
	await reset(t)
	t.log_p("-- spoils: poses 1-2 left alone, 3-6 punched")
	var pose := pose_state(t)
	start(t)
	var drained: Array[float] = []
	var boos: Array[bool] = []
	var hit_anims: Array[StringName] = []
	var pair := {}
	var health: int = t.boss.boss_health
	for index in range(2, 6):
		await t.wait_until(func(): return pose.pose_index == index and pose.pose_clock >= 0.3, 400)
		var before: float = t.boss.hype
		var dealt: int = await punch(t)
		drained.append(before - t.boss.hype)
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
	t.check(drained.all(func(d): return is_equal_approx(d, 0.5)), "each spoil half a cell (%s)" % [drained])
	t.check(boos.all(func(b): return b) and hit_anims.all(func(a): return a == &"pose_hit"), "each with a boo, pose_hit on him")
	t.check(pair.get("same_pose", false) and pair.get("second", 0) > 0 and is_equal_approx(pair.get("drained_by_second", -1.0), 0.0),
		"a second punch in a pose deals its damage and drains nothing (%s)" % [pair])
	t.check(is_equal_approx(t.boss.hype, 0.0), "the meter back at 0 (%.1f)" % t.boss.hype)
	t.check(t.sm.current_state == t.sm.states["Idle"], "the phase played out into Idle (%s)" % t.sm.current_state.name)


static func zones(t) -> void:
	await reset(t)
	t.log_p("-- zones: five waiting from Slams")
	var pose := pose_state(t)
	var went_off: Array[float] = []
	var order: Array[int] = []
	var told_ahead: Array[float] = []
	var zone_script: GDScript = load(ZONE_SCRIPT)
	for k in ZONE_SPOTS.size():
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
	await t.wait_until(func(): return went_off.size() == ZONE_SPOTS.size() or t.sm.current_state != pose, 900)
	var strikes: Array[float] = pose.strike_times
	var slack := 2.0 * FRAME + 0.0001
	var on_time: bool = went_off.size() == pose.eruptions.size() and strikes.size() >= 4
	for k in went_off.size():
		on_time = on_time and absf(went_off[k] - (strikes[0] + pose.eruptions[k])) <= slack
	t.log_p("strikes %s, zones %s went off at %s, told %s s before" % [strikes.map(func(x): return snappedf(x, 0.001)), order.map(func(k): return k + 1),
		went_off.map(func(x): return snappedf(x, 0.001)), told_ahead.map(func(x): return snappedf(x, 0.001))])
	t.check(on_time and order == [0, 1, 2, 3, 4], "oldest first, at %s s from the first strike" % [pose.eruptions])
	t.check(strikes.size() >= 4 and not went_off.is_empty() and absf(went_off[-1] - strikes[3]) <= slack, "the last as pose 3 resolves")
	var noticed: bool = told_ahead.size() == pose.eruptions.size()
	for k in told_ahead.size():
		noticed = noticed and absf(told_ahead[k] - minf(pose.eruption_notice, pose.eruptions[k] + pose.turn_time)) <= slack
	t.check(noticed, "each told %.2f s before it goes, or as the poses begin" % pose.eruption_notice)
	park(t)


static func carry(t) -> void:
	await reset(t, 2.5)
	t.log_p("-- carry: a phase from 2.5 cells, poses 1-2 spoiled, then the next phase")
	var pose := pose_state(t)
	start(t)
	for index in [0, 1]:
		await t.wait_until(func(): return pose.pose_index == index and pose.pose_clock >= 0.3, 400)
		await punch(t)
		t.player.global_position = CLEAR
	await t.wait_until(func(): return t.sm.current_state != pose, 700)
	var left: float = t.boss.hype
	t.log_p("the phase left %.1f (outcomes %s)" % [left, pose.outcomes])
	t.check(is_equal_approx(left, 5.5), "2.5, two spoils and four banks: 5.5 (%.1f)" % left)
	start(t)
	await t.wait_until(func(): return pose.pose_index == 0, 60)
	var shown: float = t.boss.hype_meter.shown
	await t.wait_until(func(): return pose.outcomes.size() == 1 or t.sm.current_state != pose, 200)
	t.log_p("the next phase's first strike: hype %.1f, the meter %.1f; then %s" % [left, shown, t.sm.current_state.name])
	t.check(is_equal_approx(t.boss.hype, 6.0) and is_equal_approx(shown, 5.5), "the next phase starts on the meter the last left, 5.5, and banks on to full (%.1f)" % t.boss.hype)
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
	t.player.combo.punch_landed.connect(func(_target, _dealt, _charged): hit_in.append(pose.pose_index))
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
	t.check(combo == 4 and total == 12, "the combo 4 and the single-bar uppercut 8: 12 (%d, %d)" % [combo, total])
	t.check(is_equal_approx(hype - t.boss.hype, 0.5 * poses_hit.size()), "half a cell off for each pose a hit landed in, the uppercut's too (%.1f, poses %s)" % [hype - t.boss.hype, poses_hit.keys().map(func(i): return i + 1)])
	t.check(pose.outcomes.size() == in_pose, "the pose he was dazed in never resolves (%s)" % [pose.outcomes])
	t.check(not zone_left, "the zones still waiting as the daze caught him fizzle with the phase, none going off")
	t.check(t.sm.current_state == t.sm.states["Idle"] and not pose.live, "the phase is over: staggered into Idle (%s)" % t.sm.current_state.name)
