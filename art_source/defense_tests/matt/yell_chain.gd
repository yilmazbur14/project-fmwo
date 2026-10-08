extends RefCounted

# matt_yell_chain (tuning 2026-10-04, the 2026-10-04 playtest's "chained punch = guaranteed hit"): the yell is no
# trap for a player mid-combo. Its yellow badge goes up the step after the punch that sets it off lands, 7 steps
# before that swing's arm is back, and a swing holds the player 24 steps and drops any dash pressed in it. At a
# 0.40 s tell a second punch chained as the arm came back - pressed before anyone could react to the badge - held
# the player past the blast, and 93% of first-time yells landed. --fixed-fps 60.
# A yell forced on punch 1, then on punch 2, of a window at HOME, from each of the three spots a player punches him
# from (under him and either side); the dash pressed straight away from his mouth, and again every 0.1 s while a
# swing eats it:
#   answered  the punch that set it off and nothing after it, the dash at the slow end of a first reaction, 0.30 s
#             after the badge; and one more punch chained 0, 0.05 and 0.10 s after the arm is back (an eager
#             chain, inside the reaction), the dash 0.25 s after the badge
#   hit       two more punches chained, each as the arm is back; and one more pressed 0.35 s after the badge,
#             once it has been seen
# Every yell's result is logged with the step its dash started on, counted from the badge.

const REACH_MARGIN := 25.0
const SPOTS := ["under", "left", "right"]
const ANSWERED := [
	{"name": "the punch alone, the dash at 0.30 s", "chain": 0, "gap": 0.0, "late": -1.0, "react": 0.30},
	{"name": "one more chained at once, the dash at 0.25 s", "chain": 1, "gap": 0.0, "late": -1.0, "react": 0.25},
	{"name": "one more chained 0.05 s on, the dash at 0.25 s", "chain": 1, "gap": 0.05, "late": -1.0, "react": 0.25},
	{"name": "one more chained 0.10 s on, the dash at 0.25 s", "chain": 1, "gap": 0.10, "late": -1.0, "react": 0.25},
]
const PUNISHED := [
	{"name": "two more chained, the dash at 0.25 s", "chain": 2, "gap": 0.0, "late": -1.0, "react": 0.25},
	{"name": "one more pressed 0.35 s after the badge", "chain": 1, "gap": 0.0, "late": 0.35, "react": 0.35},
]


static func run(t) -> void:
	await t.load_matt()
	t.hold_break_gauge(t.boss)
	# Written for a window that could daze (Break-only since 2026-10-04): a chained POW through the tell still dazes
	# nothing there, and the window plays as it did.
	t.boss.daze_in_recover = true
	# The yell is off in the live game (MattStateMachine.yell_counter_enabled, 2026-10-04); this holds it fair for when
	# it is on.
	t.sm.yell_counter_enabled = true
	t.player.get_node("Finisher").min_press_interval = 0.0
	t.log_p("yell_tell %.2f s" % t.sm.yell_tell)
	for trigger in [1, 2]:
		for spot in SPOTS:
			var answered := []
			var missed := []
			for case in ANSWERED:
				var got: Dictionary = await yell_once(t, spot, trigger, case)
				t.log_p("punch %d sets it off, %s, %s: %s" % [trigger, spot, case.name, got])
				if got.badge and not got.hit:
					answered.append(case.name)
				else:
					missed.append(case.name)
			t.check(missed.is_empty(), "set off by punch %d, %s him: answered with a reaction after the punch and one eager chained one (%s)" % [
				trigger, spot, missed if not missed.is_empty() else "all %d" % answered.size()])
			var spared := []
			for case in PUNISHED:
				var got: Dictionary = await yell_once(t, spot, trigger, case)
				t.log_p("punch %d sets it off, %s, %s: %s" % [trigger, spot, case.name, got])
				if not (got.badge and got.hit):
					spared.append(case.name)
			t.check(spared.is_empty(), "set off by punch %d, %s him: still hit for two more chained or one pressed once it is seen (%s)" % [
				trigger, spot, spared if not spared.is_empty() else "both"])


# One yell: the window opened fresh, the punches before the trigger swung, then the trigger's punch and the case's
# chain, and the dash. Whether the badge went up, whether the yell HIT, and the step the dash started on.
static func yell_once(t, spot: String, trigger: int, case: Dictionary) -> Dictionary:
	var sm: Node = t.sm
	var boss: Node = t.boss
	var player: Node = t.player
	var recover: Node = sm.states["Recover"]
	player.playerHealth = 1000
	boss.boss_health = boss.max_health
	for hazard in t.get_nodes_in_group(sm.HAZARD_GROUP):
		hazard.queue_free()
	sm.on_child_transition(sm.current_state, "Idle")
	sm.beat_timer.stop()
	await t.wait(2)
	await t.wait_until(func(): return not boss.is_launching() and not player.is_action_locked and not player.is_finishing \
		and player.get_node("Finisher").phase == t.FINISHER_OFF, 600)
	await t.wait_until(func(): return not player.is_dodging and not t.defense.is_dash_recovering() and not t.defense.is_dash_cooling_down(), 120)
	t.clear_iframes()
	t.defense._set_stamina(t.defense.max_stamina)
	player.combo.reset()
	t.track()
	sm.yell_chance = 1.0
	sm.windows_opened = sm.yell_from_window
	sm.on_child_transition(sm.current_state, "Recover")
	recover.yell_on_hit = trigger
	recover.yell_planned = true
	await t.wait(2)
	await t.settle_player(punch_spot(t, t.area_rect(boss.hurtbox), spot))
	await t.wait(2)
	for i in trigger - 1:
		await t.swing_any()
	t.tap(KEY_Q)
	var f := 0
	var badge := -1
	var chained := 0
	var next_punch := -1
	var next_dash := -1
	var dashed_at := -1
	var was := false
	while f < 200:
		var punching: bool = player.state_machine.current_state.name == "Punching"
		if was and not punching and case.late < 0.0 and chained < case.chain:
			next_punch = f + roundi(case.gap * 60.0)
		was = punching
		if badge >= 0 and case.late >= 0.0 and chained < case.chain and next_punch < 0:
			next_punch = badge + roundi(case.late * 60.0)
		if next_punch >= 0 and f >= next_punch and not punching and dashed_at < 0:
			t.tap(KEY_Q)
			chained += 1
			next_punch = -1
		if badge >= 0 and next_dash < 0:
			next_dash = badge + roundi(case.react * 60.0)
			if case.late >= 0.0:
				next_dash += 1
		if next_dash >= 0 and f >= next_dash and dashed_at < 0:
			if player.is_dodging:
				dashed_at = f - badge
			elif (f - next_dash) % 6 == 0:
				dash_away(t)
		await t.physics_frame
		f += 1
		if badge < 0 and recover.yell == recover.Yell.TELL:
			badge = f
		if badge >= 0 and recover.yell == recover.Yell.NONE:
			break
		if sm.current_state != recover:
			break
	for k in [KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN]:
		t.release(k)
	var hit: bool = not t.events_of("HIT", &"matt_yell").is_empty()
	await t.wait(20)
	return {"badge": badge >= 0, "hit": hit, "dash_step": dashed_at, "chained": chained}


# Straight away from his mouth, the arrows held into a fresh dash press.
static func dash_away(t) -> void:
	var away: Vector2 = t.player.global_position - t.boss.mouth_point(&"roar")
	var dir := Vector2(signf(away.x) if absf(away.x) > 20.0 else 0.0, signf(away.y) if absf(away.y) > 20.0 else 1.0)
	for k in [KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN]:
		t.release(k)
	if dir.x > 0.0:
		t.press(KEY_RIGHT)
	if dir.x < 0.0:
		t.press(KEY_LEFT)
	if dir.y > 0.0:
		t.press(KEY_DOWN)
	if dir.y < 0.0:
		t.press(KEY_UP)
	t.tap(KEY_W)


# Where a player stands to punch him: under him punching up, or level with his lower body either side, the fist
# REACH_MARGIN into his hurtbox.
static func punch_spot(t, box: Rect2, which: String) -> Vector2:
	var player: Node = t.player
	var off_up: Rect2 = player.global_transform * player.punch_box(player.Facing.UP)
	off_up.position -= player.global_position
	var off_l: Rect2 = player.global_transform * player.punch_box(player.Facing.LEFT)
	off_l.position -= player.global_position
	var off_r: Rect2 = player.global_transform * player.punch_box(player.Facing.RIGHT)
	off_r.position -= player.global_position
	match which:
		"left":
			return Vector2(box.position.x + REACH_MARGIN - off_r.end.x, box.position.y + box.size.y * 0.7 - off_r.get_center().y)
		"right":
			return Vector2(box.end.x - REACH_MARGIN - off_l.position.x, box.position.y + box.size.y * 0.7 - off_l.get_center().y)
	return Vector2(box.get_center().x - off_up.get_center().x, box.end.y - REACH_MARGIN - off_up.position.y)
