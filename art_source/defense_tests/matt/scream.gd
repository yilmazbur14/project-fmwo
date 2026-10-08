extends RefCounted

# matt_scream (the user, 2026-09-27): once a punch short of the POW has landed in his punish window (MattRecover),
# a swing that whiffs or is refused and he screams at once. OFF IN THE LIVE GAME since 2026-10-05 ("remove matts
# whiff screm shove"): the mode first holds the live default to no scream and no shove, then turns
# MattStateMachine.scream_on_miss on for every case below but "off". The combo has had no timing since 2026-09-30, so a
# slow or a mashed press is never one. --fixed-fps 60, with the finisher's press interval zeroed as matt_yell
# zeroes it.
#   live     the default: one punch, then a whiff - no scream, nobody shoved, the window open.
#   whiff    one punch, then a swing out of his reach: on the frame it is known missed (PlayerCombo.punch_missed),
#            or the one after, he roars - the yell's roar frames and sound and a ring that hurts nobody - and the
#            player is shoved straight away from his mouth to scream_clear from it, inside the ring, locked through
#            the shove and given back on landing. The combo's count is gone with it. No damage, no daze and no
#            uppercut: he is out of his window, his hurtbox off, a punch at him is refused, and he attacks again
#            post_yell_beat after the scream.
#   refused  one punch, then one with the window's allowance spent (PunchAllowance): the same.
#   slow     one punch, then another SLOW_FRAMES on: it lands as the second, no scream, the window open.
#   mashed   a second press mid-swing: the punch lands, no scream, the window open.
#   clean    three punches daze him with no scream, and the uppercut lands.
#   pow      three punches with no daze to give, then a whiff: the POW ended the watch, so no scream.
#   none     a whiff with nothing landed in this window, the count carried in from the last: no scream, and the
#            window stays open.
#   yell     a whiff through his yell is the yell's: no scream, and the window carries on with the yell's bonus.
#            A punch landed after the yell and a whiff are screamed away.
#   off      MattStateMachine.scream_on_miss off: one punch and a whiff, and no scream; the window stays open and
#            the count carries.
#   ropes    scream_point from spots all round his mouth at HOME and at the Glass Row's station: on whole px
#            inside the ring's floor and scream_clear from his mouth, straight away when that fits and turned
#            along a rope when it doesn't; a player already that far off stays put.

const PunchAllowance := preload("res://Scripts/PunchAllowance.gd")
const RING_SCRIPT := "res://Scripts/MattYellRingScript.gd"
# The case's frames to wait for the scream.
const SCREAM_WAIT := 90
# How far a whiffing player stands back from where place_under() puts them: the fist well short of him.
const WHIFF_STEP := Vector2(0, 70)
# A slow press, past anything the combo's old beat window allowed (0.40 s from the swing's end), and still inside
# PlayerCombo.COMBO_RESET_TIME of the punch before it, which drops the count (the user, 2026-10-04).
const SLOW_FRAMES := 30


static func run(t) -> void:
	await t.load_matt()
	# "clean" and "pow" are about his window's daze, which is the live default again (2026-10-05).
	t.boss.daze_in_recover = true
	t.track()
	t.hold_gauge()
	var sm: Node = t.sm
	var boss: Node = t.boss
	var player: Node = t.player
	var finisher: Node = player.get_node("Finisher")
	finisher.min_press_interval = 0.0
	# Every miss - a whiff or a refusal - where the player stood for it, and the count as it came: the count lapses
	# COMBO_RESET_TIME after the last punch landed, so what a miss carries is read as it happens.
	var misses := []
	var on_miss := func():
		misses.append({"frame": Engine.get_physics_frames(), "at": player.global_position, "count": player.combo.count})
	player.combo.punch_missed.connect(on_miss)
	player.combo.punch_refused.connect(func(_target): on_miss.call())
	var landed := []
	player.combo.punch_landed.connect(func(_target, _dealt, _charged): landed.append(Engine.get_physics_frames()))
	var refused := []
	player.combo.punch_refused.connect(func(_target): refused.append(Engine.get_physics_frames()))

	t.log_p("-- live: the default, one punch and a whiff")
	var live_off: bool = not sm.scream_on_miss
	var live_window: Node = await open(t)
	await t.swing_any()
	var stood: Vector2 = player.global_position + WHIFF_STEP
	misses.clear()
	var shoved := [false]
	var watch_shove := func(): shoved[0] = shoved[0] or boss.is_launching()
	t.physics_frame.connect(watch_shove)
	await whiff(t)
	await t.wait(SCREAM_WAIT)
	t.physics_frame.disconnect(watch_shove)
	t.log_p("live default: scream_on_miss %s, %d missed, %d screams, shoved %s, moved %s" % [sm.scream_on_miss, misses.size(), live_window.screams, shoved[0], player.global_position - stood])
	t.check(live_off and not misses.is_empty() and live_window.screams == 0 and not shoved[0] and player.global_position == stood and sm.is_recovering(),
		"off by default: a whiff after a punch screams nothing and shoves nobody, and the window stays open")
	sm.scream_on_miss = true

	t.log_p("-- whiff: one punch, then a swing out of his reach")
	var recover: Node = await open(t)
	var health: int = player.playerHealth
	await t.swing_any()
	misses.clear()
	await whiff(t)
	var seen: Dictionary = await watch(t, recover, misses)
	check_scream(t, seen, "whiff")
	t.check(boss.boss_health == boss.max_health - 1 and player.playerHealth == health and t.events_of("HIT").is_empty(),
		"his punch landed for 1, and the scream did the player no damage (%d, %d)" % [boss.boss_health, player.playerHealth])
	t.place_under(boss.get_finisher_hurtbox())
	await t.wait(3)
	refused.clear()
	var dealt: int = await t.swing()
	t.check(dealt == 0 and refused.size() == 1, "a punch at him after it is refused (%d dealt, %d refusals)" % [dealt, refused.size()])
	var again: bool = await t.wait_until(func(): return sm.current_state.name == "MysticVolley", 120)
	var after := (Engine.get_physics_frames() - int(seen.frame)) / 60.0
	t.log_p("his next attack %.3f s after the scream" % after)
	t.check(again and absf(after - sm.post_yell_beat) <= 2.0 / 60.0, "and he attacks again %.1f s after it" % sm.post_yell_beat)

	t.log_p("-- refused: one punch, then one with the window's allowance spent")
	recover = await open(t)
	await t.swing_any()
	boss.punches.spent = PunchAllowance.clean_chain(boss.MAX_HITS_PER_WINDOW)
	misses.clear()
	refused.clear()
	await t.wait(3)
	t.tap(KEY_Q)
	seen = await watch(t, recover, misses)
	check_scream(t, seen, "refused")
	t.check(refused.size() == 1 and not misses.is_empty() and misses[0].frame == refused[0] and boss.boss_health == boss.max_health - 1,
		"the punch was refused, and that was the miss (refused %s, missed %s)" % [refused, misses.map(func(m): return m.frame)])

	t.log_p("-- slow: one punch, then another %d frames on" % SLOW_FRAMES)
	recover = await open(t)
	await t.swing_any()
	await t.wait(SLOW_FRAMES)
	await t.swing_any()
	await t.wait(30)
	t.check(recover.screams == 0 and sm.is_recovering() and boss.hits_this_window == 2 and player.combo.count == 2,
		"both land, the second as the combo's second, with no scream and the window open (%d landed, count %d, %d screams)" % [boss.hits_this_window, player.combo.count, recover.screams])

	t.log_p("-- mashed: a second press mid-swing")
	recover = await open(t)
	landed.clear()
	t.tap(KEY_Q)
	await t.wait(4)
	t.tap(KEY_Q)
	await t.wait_until(func(): return player.state_machine.current_state.name != "Punching", 60)
	await t.wait(30)
	t.check(landed.size() == 1 and recover.screams == 0 and sm.is_recovering() and player.combo.count == 1,
		"the punch landed, the count 1, with no scream and the window open (landed %d, count %d, %d screams)" % [landed.size(), player.combo.count, recover.screams])

	t.log_p("-- clean: three punches")
	recover = await open(t)
	var launched := [false]
	var watch_launch := func(): launched[0] = launched[0] or boss.is_launching()
	t.physics_frame.connect(watch_launch)
	for i in 3:
		await t.swing_any()
		if i < 2:
			await t.wait(6)
	var dazed: bool = await t.wait_until(func(): return finisher.phase == t.FINISHER_DAZED, 120)
	var chain: int = boss.max_health - boss.boss_health
	t.check(dazed and chain == PunchAllowance.clean_chain(3) and recover.screams == 0, "dazed, %d off him and no scream" % chain)
	await t.mash_finisher()
	var uppercut: bool = await t.wait_until(func(): return boss.max_health - boss.boss_health > chain, 120)
	await t.wait_until(func(): return finisher.phase == t.FINISHER_OFF, 300)
	t.physics_frame.disconnect(watch_launch)
	t.log_p("the uppercut took him to %d; screams %d, launched %s" % [boss.boss_health, recover.screams, launched[0]])
	t.check(uppercut and recover.screams == 0 and not launched[0], "the uppercut lands, and nothing screamed or shoved")

	t.log_p("-- pow: three punches with no daze to give, then a whiff")
	recover = await open(t)
	# After his window's Enter, which clears it.
	boss.daze_used = true
	for i in 3:
		await t.swing_any()
	var pow_landed: int = boss.max_health - boss.boss_health
	misses.clear()
	await whiff(t)
	await t.wait(30)
	t.check(pow_landed == PunchAllowance.clean_chain(3) and not misses.is_empty() and recover.screams == 0 and sm.is_recovering() and not finisher.is_active(),
		"the POW landed and dazed nothing, and the whiff after it is no scream: the window open (%d off him, %d missed, %d screams)" % [pow_landed, misses.size(), recover.screams])

	t.log_p("-- none: a whiff with nothing landed in this window, the count carried in from the last")
	recover = await open(t)
	await t.swing_any()
	recover = await open(t, true)
	var carried: int = player.combo.count
	misses.clear()
	await whiff(t)
	await t.wait(30)
	t.check(carried == 1 and not misses.is_empty() and recover.screams == 0 and sm.is_recovering() and boss.hits_this_window == 0 and misses[0].count == 1,
		"nothing landed here to watch: no scream, the window open, the count still %d at the whiff (%d missed, %d screams)" % [carried, misses.size(), recover.screams])

	t.log_p("-- yell: a whiff through his yell, then a punch and a whiff after it")
	sm.yell_counter_enabled = true
	sm.yell_chance = 1.0
	sm.windows_opened = sm.yell_from_window
	recover = await open(t)
	recover.yell_on_hit = 1
	t.tap(KEY_Q)
	t.check(await t.wait_until(func(): return recover.yell == recover.Yell.TELL, 60), "the yell's tell on the first punch")
	await t.wait_until(func(): return player.state_machine.current_state.name != "Punching", 60)
	await t.settle_player(boss.mouth_point(&"roar") + Vector2(0, sm.yell_radius + sm.yell_band + 120.0))
	misses.clear()
	await t.swing_any()
	await t.wait_until(func(): return recover.yell == recover.Yell.NONE, 90)
	t.log_p("through the yell: misses %s, screams %d, still open %s, %.3f s left, count %d" % [misses.map(func(m): return m.frame), recover.screams, sm.is_recovering(), sm.recover_timer.time_left, player.combo.count])
	t.check(not misses.is_empty() and recover.screams == 0 and sm.is_recovering() and t.events_of("HIT").is_empty() and misses[0].count == 1,
		"the whiff through it is no scream, the window carries on, and the count with it at the whiff")
	sm.yell_chance = 0.0
	sm.yell_counter_enabled = false
	t.place_under(boss.get_finisher_hurtbox())
	await t.wait(4)
	await t.swing_any()
	misses.clear()
	await whiff(t)
	seen = await watch(t, recover, misses)
	check_scream(t, seen, "a punch after the yell, then a whiff")

	t.log_p("-- off: scream_on_miss off, one punch and a whiff")
	sm.scream_on_miss = false
	recover = await open(t)
	await t.swing_any()
	misses.clear()
	await whiff(t)
	await t.wait(30)
	sm.scream_on_miss = true
	t.check(not misses.is_empty() and recover.screams == 0 and sm.is_recovering() and misses[0].count == 1 and t.events_of("HIT").is_empty(),
		"no scream: the window open and the count carried through the whiff (%d missed, %d screams, count %d at it)" % [misses.size(), recover.screams, misses[0].count if not misses.is_empty() else -1])

	t.log_p("-- ropes: the shove from all round his mouth")
	await open(t)
	sm.on_child_transition(sm.current_state, "Idle")
	sm.beat_timer.stop()
	var inside: Rect2 = player.ring_origins
	t.log_p("the ring's floor for the player's origin: %s" % inside)
	var clear: float = sm.scream_clear
	var bad := []
	var turned := 0
	var spots := 0
	for feet in [sm.HOME, sm.GLASS_ROW.station]:
		boss.global_position = feet
		var mouth: Vector2 = boss.mouth_point(&"roar")
		for degrees in range(0, 360, 30):
			for reach in [0.0, 60.0, 150.0, 250.0, clear + 30.0]:
				var from: Vector2 = (mouth + Vector2.from_angle(deg_to_rad(degrees)) * reach).round().clamp(inside.position.ceil(), inside.end.floor())
				var to: Vector2 = recover.scream_point(from, inside)
				spots += 1
				var ok: bool = within(inside, to) and to == to.round()
				if from.distance_to(mouth) >= clear:
					ok = ok and to == from
				else:
					ok = ok and to.distance_to(mouth) >= clear - 1.0
					var straight: Vector2 = mouth + (Vector2.DOWN if reach == 0.0 else (from - mouth).normalized()) * clear
					if within(inside, straight):
						ok = ok and to.distance_to(straight) <= 1.0
					else:
						turned += 1
				if not ok:
					bad.append("%s from %s -> %s (%.0f px)" % [feet, from, to, to.distance_to(mouth)])
	boss.global_position = sm.HOME
	t.log_p("%d spots, %d turned along a rope; wrong: %s" % [spots, turned, bad])
	t.check(bad.is_empty(), "always inside the ring and %.0f px from his mouth, straight away where that fits" % clear)
	t.check(turned > 0, "and the rope cases were met (%d)" % turned)


# His window, fresh: the last case's shove landed and its finisher's input lock over, his health whole, the combo's
# count clear unless `keep_count`, nothing of his out, and the player under him.
static func open(t, keep_count := false) -> Node:
	var sm: Node = t.sm
	var finisher: Node = t.player.get_node("Finisher")
	await t.wait_until(func(): return not t.boss.is_launching() and not t.player.is_action_locked and not finisher.is_input_locked(), 120)
	sm.on_child_transition(sm.current_state, "Idle")
	sm.beat_timer.stop()
	sm.finisher_stagger_timer.stop()
	for hazard in t.get_nodes_in_group(sm.HAZARD_GROUP):
		hazard.queue_free()
	await t.wait(2)
	if not keep_count:
		t.player.combo.reset()
	t.boss.boss_health = t.boss.max_health
	t.clear_iframes()
	t.health_ok()
	t.events.clear()
	sm.on_child_transition(sm.current_state, "Recover")
	await t.wait(3)
	t.place_under(t.boss.get_finisher_hurtbox())
	await t.wait(4)
	return sm.states["Recover"]


# A swing from WHIFF_STEP back of where place_under() puts the player: the fist well short of him.
static func whiff(t) -> void:
	t.player.global_position += WHIFF_STEP
	await t.wait(3)
	t.tap(KEY_Q)
	await t.wait_until(func(): return t.player.state_machine.current_state.name == "Punching", 10)
	await t.wait_until(func(): return t.player.state_machine.current_state.name != "Punching", 60)


# Up to SCREAM_WAIT frames for the scream, then until its shove has landed: what it did.
static func watch(t, recover: Node, misses: Array) -> Dictionary:
	var boss: Node = t.boss
	var finisher: Node = t.player.get_node("Finisher")
	var seen := {"frame": -1, "dazed": false}
	for i in SCREAM_WAIT:
		if recover.screams > 0:
			seen.frame = Engine.get_physics_frames()
			break
		await t.physics_frame
		seen.dazed = seen.dazed or finisher.phase != t.FINISHER_OFF
	if seen.frame < 0 or misses.is_empty():
		return seen
	var is_ring := func(h: Node) -> bool:
		return is_instance_valid(h) and h.get_script() != null and h.get_script().resource_path == RING_SCRIPT
	var rings: Array = t.get_nodes_in_group(t.sm.HAZARD_GROUP).filter(is_ring)
	seen["miss"] = misses[0].frame
	seen["from"] = misses[0].at
	seen["count"] = t.player.combo.count
	seen["mouth"] = boss.mouth_point(&"roar")
	seen["anim"] = boss.current_anim
	seen["ring"] = rings.size() == 1 and rings[0].player == null
	seen["sound"] = boss.sfx_players[&"yell"].any(func(p): return p.playing)
	seen["out"] = not t.sm.is_recovering() and not boss.can_be_dazed()
	seen["held"] = t.player.is_action_locked and t.player.lock_seals_guard and t.player.scripted_pose and boss.is_launching()
	await t.wait_until(func(): return not boss.is_launching(), 120)
	await t.wait(2)
	seen["to"] = t.player.global_position
	seen["free"] = not t.player.is_action_locked and not t.player.scripted_pose
	seen["hurtbox_off"] = not boss.hurtbox.monitorable and not boss.hurtbox.monitoring
	seen["health"] = t.player.playerHealth
	return seen


static func check_scream(t, seen: Dictionary, what: String) -> void:
	var sm: Node = t.sm
	t.log_p("%s: %s" % [what, seen])
	if seen.frame < 0 or not seen.has("miss"):
		t.check(false, "%s: he screams" % what)
		return
	var mouth: Vector2 = seen.mouth
	var from: Vector2 = seen.from
	var to: Vector2 = seen.to
	var inside: Rect2 = t.player.ring_origins
	t.check(seen.frame - seen.miss <= 1, "%s: he screams on the frame of the miss, or the one after (%d, %d)" % [what, seen.miss, seen.frame])
	t.check(seen.count == 0, "the combo's count gone with it (%d)" % seen.count)
	t.check(seen.anim == &"roar" and seen.sound and seen.ring, "the yell's roar, its sound and a ring that hurts nobody (%s, %s, %s)" % [seen.anim, seen.sound, seen.ring])
	t.check(seen.out and seen.hurtbox_off and not seen.dazed, "out of his window: no daze, no uppercut, his hurtbox off")
	t.check(seen.held and seen.free, "the player locked through the shove and given back on landing")
	t.check(to.distance_to(mouth) >= sm.scream_clear - 1.0 and within(inside, to)
		and (to - mouth).normalized().dot((from - mouth).normalized()) > 0.99,
		"shoved straight away from his mouth, %.0f px from it (was %.0f), inside the ring" % [to.distance_to(mouth), from.distance_to(mouth)])
	t.check(t.events_of("HIT").is_empty() and seen.health == 100, "and no damage (%d)" % seen.health)


# Rect2.has_point() leaves out the far edges, which a clamp to the rect can land on.
static func within(rect: Rect2, point: Vector2) -> bool:
	return point.x >= rect.position.x and point.x <= rect.end.x and point.y >= rect.position.y and point.y <= rect.end.y
