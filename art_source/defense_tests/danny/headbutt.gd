extends RefCounted

# danny_headbutt (coder B): his Sumo Headbutt at a rooted player, and the dizzy spell a parried one leaves him
# in (DannyBossHeadbutt, DannyBossStaggered; plan sections 6 and 13). --fixed-fps 60. tier=
#   parry       (the default) a press 0.4 s before the wind-up, then one as he launches: PARRIED, +1 read,
#               the root bursts, and the flip back lands him in Staggered for the parry's stagger and his walk_in - a cap of 3
#               punches, so a clean chain of 3's damage (PunchAllowance), its POW dazing him (the user, 2026-10-06:
#               3 hits always trigger the uppercut; pow_always_dazes plays the mash) - then Idle.
#   hit         no answer: 2 damage, the root lets go, the player is knocked 160 px along his flight, and he
#               flips back into Idle.
#   guard       the guard held from before the wind-up to the impact: still a HIT.
#   from_sleep  a root in his nap wakes him into the headbutt and stops the regen.
#   from_slams  a root in his string brings no headbutt, and lets go at the next landing, or by itself at
#               the string's 1.5 s hold.
#   ropes       the player rooted against the bottom rope, then the top one: the launch spot clamped so the
#               whole wind-up and its badge stay on screen, the flight closing the height on a diagonal, his
#               flying body kept on screen, and the impact still landing on the player's near edge.
# Every tier that headbutts: the red badge up from the wind-up to the impact (0.77 s) and never before it,
# launch to impact 0.22 s, his head flying straight at the near edge of the player's hurtbox and meeting it
# at the impact, drawn behind the player from the launch until he lands and back on his own y-sort after,
# the trail behind him in flight only, the player held until the impact, and ROOT_GRACE from it.

const Spit := preload("res://art_source/defense_tests/danny/spit.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const Layout := preload("res://Scripts/DannyBossArtLayout.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const PunchAllowance := preload("res://Scripts/PunchAllowance.gd")

const FRAME_TIME := 1.0 / 60.0
const SLACK := FRAME_TIME + 0.0001
# He starts at HOME, left of the player, so he flies right; from_sleep puts the player on his left instead.
const PLAYER_FEET := Vector2(1160, 842)
const PLAYER_FEET_LEFT := Vector2(760, 842)
# A press this long before the wind-up must not keep the parry from being credited.
const EARLY_PRESS := 0.4
# The flip back's tuck (danny_sumo_headbutt f5), opaque from row 8 to his feet: px over them.
const TUCK_HEIGHT := 408.0


static func run(t) -> void:
	await Spit.enter(t)
	t.track()
	t.track_parries()
	var answer: String = "parry" if t.tier == "normal" else t.tier
	match answer:
		"parry":
			await tier_parry(t)
		"hit":
			await tier_hit(t)
		"guard":
			await tier_guard(t)
		"from_sleep":
			await tier_from_sleep(t)
		"from_slams":
			await tier_from_slams(t)
		"ropes":
			await tier_ropes(t)
		_:
			t.check(false, "danny_headbutt has no tier %s" % answer)


# Parked with an empty open gauge and no grace left, the player's feet at `feet`.
static func ready_at(t, feet: Vector2) -> void:
	await Spit.park(t, feet)
	t.sm.root_grace_left = 0.0
	t.boss.break_gauge.locked = false
	t.boss.break_gauge.value = 0.0
	await t.wait(2)
	t.events.clear()
	t.parries.clear()


static func player_box(t) -> Rect2:
	var shape: CollisionShape2D = t.player.hurtBox.get_node("CollisionShape2D")
	return shape.global_transform * shape.shape.get_rect()


# The player walked with `code` held until a rope stops them.
static func walk_to_rope(t, code: int) -> void:
	t.press(code)
	var last := [Vector2.INF, 0]
	var stopped := func() -> bool:
		var at: Vector2 = t.player.global_position
		last[1] = last[1] + 1 if at == last[0] else 0
		last[0] = at
		return last[1] >= 3
	await t.wait_until(stopped, 240)
	t.release(code)
	await t.wait(2)


# One headbutt from the root, answered as `answer` says ("parry", "guard" or "hit"), watched on every step.
static func headbutt(t, answer: String) -> Dictionary:
	var hb: Node = t.sm.states["Headbutt"]
	var steps: Array = []
	var watch := func():
		var trail_valid: bool = is_instance_valid(hb.trail)
		steps.append({
			"state": String(t.sm.current_state.name), "beat": hb.beat, "tell": not t.live_tells().is_empty(),
			"clock": t.boss.fight_clock, "at": t.boss.global_position, "head": t.boss.head_point(&"headbutt_fly"),
			"centre": t.sm.player_hurtbox_centre(), "box": player_box(t), "lift": t.boss.lift_px, "sink": hb.sink,
			"drawn": t.boss.global_position.y - t.boss.lift_px, "feet": hb.feet,
			"sort": t.player.to_global(t.player.sprite_base_position).y, "badge_top": t.boss.tell_anchor().y - hb.badge_room,
			"locked": t.player.is_action_locked, "trail": trail_valid,
			"behind": trail_valid and hb.trail.get_index() < t.boss.sprite.get_index(),
			"trail_y": hb.trail.global_position.y if trail_valid else INF,
			"grace": t.sm.root_grace_left, "root": t.sm.root != null, "last_press": t.defense.last_press_time,
			"anim": t.boss.current_anim,
		})
	t.physics_frame.connect(watch)
	var root: Node = t.sm.test_root_player()
	var marks := {"rooted": root != null, "early_press": -1.0, "guard_at_impact": false}
	if root == null:
		t.physics_frame.disconnect(watch)
		return {"steps": steps, "marks": marks}
	await t.wait_until(func(): return hb.beat == hb.Beat.SLIDE, 30)
	if answer == "parry":
		await t.wait_until(func(): return hb.slide_length - hb.beat_clock <= EARLY_PRESS + FRAME_TIME / 2.0, 60)
		marks.early_press = hb.slide_length - hb.beat_clock
		t.press(KEY_SHIFT)
		await t.wait(1)
		t.release(KEY_SHIFT)
	elif answer == "guard":
		t.press(KEY_SHIFT)
	await t.wait_until(func(): return hb.beat == hb.Beat.FLIGHT or not Spit.state_is(t, "Headbutt"), 120)
	if answer == "parry":
		t.press(KEY_SHIFT)
	await t.wait_until(func(): return hb.result >= 0 or not Spit.state_is(t, "Headbutt"), 60)
	marks.guard_at_impact = t.defense.is_guarding()
	if answer != "hit":
		t.release(KEY_SHIFT)
	await t.wait_until(func(): return not Spit.state_is(t, "Headbutt"), 60)
	await t.wait(2)
	t.physics_frame.disconnect(watch)
	return {"steps": steps, "marks": marks}


# What every tier that headbutts shares.
static func check_headbutt(t, run: Dictionary) -> void:
	var hb: Node = t.sm.states["Headbutt"]
	var steps: Array = run.steps
	var marks: Dictionary = run.marks
	t.check(marks.rooted, "the player is rooted where they stand, and he answers with his headbutt")
	var mine := steps.filter(func(s): return s.state == "Headbutt")
	var before := mine.filter(func(s): return s.beat == hb.Beat.REACT or s.beat == hb.Beat.SLIDE)
	var told := mine.filter(func(s): return s.beat == hb.Beat.WINDUP or s.beat == hb.Beat.FLIGHT)
	var after := mine.filter(func(s): return s.beat == hb.Beat.RECOIL)
	t.check(not before.is_empty() and before.all(func(s): return not s.tell), "no badge while he reacts and slides back (%d steps)" % before.size())
	t.check(not told.is_empty() and told.all(func(s): return s.tell), "the red badge up on all %d steps from the wind-up to the impact" % told.size())
	t.check(not after.is_empty() and not after[0].tell, "and gone at the impact")
	var windup_to_impact: float = hb.impact_at - hb.windup_at
	var flight: float = hb.impact_at - hb.launch_at
	t.log_p("wind-up %.4f s to the impact, launch %.4f s to it; launch spot %s, feet then %s" % [windup_to_impact, flight, hb.launch_spot, hb.flight_to])
	t.check(absf(windup_to_impact - (hb.windup_time + hb.flight_time)) <= SLACK, "the badge's 0.77 s: wind-up to impact %.4f s" % windup_to_impact)
	t.check(absf(flight - hb.flight_time) <= SLACK, "launch to impact %.2f s, to the frame (%.4f)" % [hb.flight_time, flight])
	var flying := mine.filter(func(s): return s.beat == hb.Beat.FLIGHT)
	if flying.is_empty() or after.is_empty():
		t.check(false, "he flies and lands the impact")
		return
	var from: Vector2 = flying[0].head
	var to: Vector2 = hb.impact_point
	var off := flying.map(func(s): return snappedf(Geometry2D.get_closest_point_to_segment(s.head, from, to).distance_to(s.head), 0.1))
	var rise: float = from.y - to.y
	t.log_p("his head flies %s -> %s: %.0f px across, %.0f px %s, %.1f degrees" % [from, to, absf(to.x - from.x), absf(rise), "up" if rise > 0.0 else "down", rad_to_deg(atan2(absf(rise), absf(to.x - from.x)))])
	t.check(off.all(func(d): return d <= 1.0), "in flight his head flies straight at the point it meets the player (off it by %s px)" % [off])
	var box: Rect2 = flying[-1].box
	var flip: bool = t.boss.sprite.flip_h
	var near: float = box.end.x if flip else box.position.x
	var lowest: float = ScreenView.VIEW_SIZE.y + Layout.texel_local(Layout.head(&"headbutt_fly"), &"headbutt_fly", flip).y
	t.check(absf(to.x - near) <= 0.01 and absf(to.y - minf(box.get_center().y, lowest)) <= 0.01,
		"that point is on the near edge of the player's hurtbox, level with its middle or as low as keeps his feet on screen (%s; %.1f px under the box's top)" % [to, to.y - box.position.y])
	t.check(after[0].head.distance_to(to) <= 1.0, "and his head is on it at the impact (%.2f px)" % after[0].head.distance_to(to))
	var airborne := mine.filter(func(s): return s.beat == hb.Beat.FLIGHT or s.beat == hb.Beat.RECOIL)
	t.check(airborne.all(func(s): return s.at.y < s.sort), "drawn behind the player from the launch until he lands: his sort point over theirs on all %d steps" % airborne.size())
	t.check(flying.all(func(s): return absf(s.drawn - s.feet.y) <= 0.01), "while his drawing stays on his flight path")
	t.check(flying.all(func(s): return s.trail and s.behind), "the trail behind his body on every flying step")
	var middle: float = Layout.body_rect(&"headbutt").get_center().y
	t.check(flying.all(func(s): return absf(s.trail_y - (s.drawn + middle)) <= 1.0), "level with his drawn body")
	t.check(mine.all(func(s): return s.trail == (s.beat == hb.Beat.FLIGHT)), "and on none other")
	var held := mine.filter(func(s): return s.beat != hb.Beat.RECOIL)
	t.check(not held.is_empty() and held.all(func(s): return s.locked and s.root), "the player held by the root from the root to the impact")
	t.check(not after.is_empty() and not after[0].root and absf(after[0].grace - t.sm.ROOT_GRACE) <= SLACK,
		"let go at the impact, and ROOT_GRACE starts there (%.3f)" % (after[0].grace if not after.is_empty() else -1.0))


# The flip back from the impact: flip_back px behind the flight, on an arc flip_arc high, over flip_time.
static func check_flip(t, run: Dictionary, lands_in: String) -> void:
	var hb: Node = t.sm.states["Headbutt"]
	var after: Array = run.steps.filter(func(s): return s.state == "Headbutt" and s.beat == hb.Beat.RECOIL)
	var landed: Array = run.steps.filter(func(s): return s.state == lands_in)
	if after.is_empty() or landed.is_empty():
		t.check(false, "he flips back into %s" % lands_in)
		return
	var back: float = landed[0].at.x - after[0].at.x
	var walk: Rect2 = t.sm.WALK_RECT
	var want: float = clampf(after[0].at.x + (1.0 if t.boss.sprite.flip_h else -1.0) * hb.flip_back, walk.position.x, walk.end.x) - after[0].at.x
	var peak: float = after.map(func(s): return s.lift + s.sink).max()
	var took: float = landed[0].clock - after[0].clock
	t.log_p("flipped back %.0f px (want %.0f), peak %.0f px, landed %.4f s after the impact at %s" % [back, want, peak, took, landed[0].at])
	t.check(absf(back - want) <= 1.0 and absf(peak - hb.flip_arc) <= 3.0, "he flips back %.0f px on a %.0f px arc" % [hb.flip_back, hb.flip_arc])
	var inside: bool = landed[0].at == landed[0].at.clamp(walk.position, walk.end)
	t.check(landed[0].lift == 0.0 and landed[0].sink == 0.0 and inside, "and lands on his own feet and his own y-sort, inside WALK_RECT")
	t.check(absf(took - hb.flip_time) <= SLACK + FRAME_TIME, "%.2f s after the impact, into %s (%.4f)" % [hb.flip_time, lands_in, took])


static func tier_parry(t) -> void:
	t.log_p("-- parried: a press 0.4 s before the wind-up, then one as he launches")
	await ready_at(t, PLAYER_FEET)
	var gauge: Node = t.boss.break_gauge
	var values: Array = []
	gauge.changed.connect(func(value, _max_value): values.append(value))
	var run: Dictionary = await headbutt(t, "parry")
	var hb: Node = t.sm.states["Headbutt"]
	var staggered: Node = t.sm.states["Staggered"]
	check_headbutt(t, run)
	var windup: Array = run.steps.filter(func(s): return s.state == "Headbutt" and s.beat == hb.Beat.WINDUP)
	t.check(absf(run.marks.early_press - EARLY_PRESS) <= FRAME_TIME and not windup.is_empty() and windup[0].last_press == -INF,
		"the press %.3f s before the wind-up is rearmed away as it starts" % run.marks.early_press)
	var parried: Array = t.parries.filter(func(p): return p.id == &"danny_headbutt")
	t.check(hb.result == HitInfo.Result.PARRIED and parried.size() == 1 and parried[0].staggered and t.events_of("HIT").is_empty(),
		"the launch press parries it, with the stagger, and nothing lands")
	t.check(values == [12.5] and gauge.value == 12.5, "one read: the gauge 12.5 (%s)" % [values])
	t.check(not t.player.is_action_locked and t.sm.root == null, "the root burst: the player free")
	check_flip(t, run, "Staggered")
	var window: float = t.defense.parry_stagger_time
	t.check(Spit.state_is(t, "Staggered") and absf(hb.stagger_time - window) <= 0.0001, "Staggered, for the parry's %.2f s" % window)
	await t.wait(2)
	t.check(t.boss.hurtbox.monitoring and t.boss.window_hit_cap() == 3 and t.boss.can_be_dazed() and t.sm.is_open(),
		"open to punches, capped at 3, and the daze on offer")
	# The cap is a clean chain's damage (1 + 1 + 2), so plain punches land four times.
	var allowance: int = PunchAllowance.clean_chain(3)
	var dealt: Array = []
	for i in allowance + 1:
		dealt.append(t.boss.take_punch(1))
	var want: Array = []
	want.resize(allowance)
	want.fill(1)
	want.append(0)
	t.check(dealt == want, "%d plain punches land, a clean chain of 3's damage, and the next doesn't (%s)" % [allowance, dealt])
	var entered: float = run.steps.filter(func(s): return s.state == "Staggered")[0].clock
	var idle: bool = await t.wait_until(func(): return Spit.state_is(t, "Idle"), 180)
	var lasted: float = t.boss.fight_clock - entered
	# The parry's stagger and his walk_in, the time to walk back in over his flip (the 2026-10-06 tuning).
	var dizzy: float = window + t.sm.states["Staggered"].walk_in
	t.check(idle and absf(lasted - dizzy) <= 2.0 * FRAME_TIME, "then Idle, %.2f s on (%.4f)" % [dizzy, lasted])
	t.check(t.boss.current_anim in [&"wake", &"idle"] and not t.boss.hurtbox.monitoring, "shaking himself awake, the window shut")
	t.stop_boss_timers()
	t.log_p("-- a parry that fills his gauge Breaks him as he starts his flip back, drawn behind the player")
	await ready_at(t, PLAYER_FEET)
	gauge.value = gauge.max_value - gauge.parry_gain
	var broke := {"at": Vector2.INF, "lift": INF, "feet": Vector2.INF, "sink": 0.0}
	var raised := {"sink": 0.0}
	# The Break comes in the impact's own frame (deferred), so the last flying step shows how far he was raised.
	var watch := func():
		if Spit.state_is(t, "Headbutt") and hb.beat == hb.Beat.FLIGHT:
			raised.sink = hb.sink
		if broke.at == Vector2.INF and Spit.state_is(t, "Broken"):
			broke.at = t.boss.global_position
			broke.lift = t.boss.lift_px
			broke.feet = hb.feet
	t.physics_frame.connect(watch)
	await headbutt(t, "parry")
	await t.wait_until(func(): return broke.at != Vector2.INF, 60)
	t.physics_frame.disconnect(watch)
	t.log_p("raised %.0f px into the impact; Broken at %s with lift %.0f, his feet were %s" % [raised.sink, broke.at, broke.lift, broke.feet])
	t.check(raised.sink > 0.0 and broke.at == broke.feet and broke.lift == 0.0, "Broken: back down on his own feet and y-sort, nothing left of the lift")
	t.stop_boss_timers()


static func tier_hit(t) -> void:
	t.log_p("-- no answer: it lands for a whole heart and knocks the player on along his flight")
	await ready_at(t, PLAYER_FEET)
	# In game time: the player's own hit-stop stretches the drive over more frames.
	var knock := {"from": Vector2.INF, "to": Vector2.INF, "start": 0.0, "took": -1.0}
	var hb: Node = t.sm.states["Headbutt"]
	var watch := func():
		if hb.result >= 0 and knock.from == Vector2.INF:
			knock.from = t.player.global_position
			knock.start = t.boss.fight_clock
		if knock.from != Vector2.INF and knock.to == Vector2.INF and not t.sm.is_driving_player():
			knock.to = t.player.global_position
			knock.took = t.boss.fight_clock - knock.start
	t.physics_frame.connect(watch)
	var run: Dictionary = await headbutt(t, "hit")
	t.physics_frame.disconnect(watch)
	check_headbutt(t, run)
	t.check(hb.result == HitInfo.Result.HIT and t.events_of("HIT", &"danny_headbutt").size() == 1 and t.player.playerHealth == 998,
		"HIT, for 2 (health %d)" % t.player.playerHealth)
	var along := -1.0 if t.boss.sprite.flip_h else 1.0
	var moved: Vector2 = knock.to - knock.from
	t.log_p("knocked %s over %.4f s" % [moved, knock.took])
	t.check(absf(moved.x - along * hb.knock_back) <= 1.0 and absf(moved.y) <= 1.0, "knocked %.0f px along his flight (%s)" % [hb.knock_back, moved])
	t.check(absf(knock.took - hb.knock_back_time) <= SLACK, "over %.2f s (%.4f)" % [hb.knock_back_time, knock.took])
	t.check(not t.player.is_action_locked and t.sm.root == null, "and free once it stops")
	check_flip(t, run, "Idle")
	t.stop_boss_timers()


static func tier_guard(t) -> void:
	t.log_p("-- a guard held from before the wind-up: it goes straight through")
	await ready_at(t, PLAYER_FEET)
	var run: Dictionary = await headbutt(t, "guard")
	var hb: Node = t.sm.states["Headbutt"]
	check_headbutt(t, run)
	# Without blocking (PlayerDefense.BLOCKING_ENABLED) a held guard drops once its parry window is over,
	# long before the impact.
	if t.blocking():
		t.check(run.marks.guard_at_impact, "the guard was up at the impact")
	else:
		t.check(not run.marks.guard_at_impact, "the guard held from before the wind-up had dropped by the impact")
	t.check(hb.result == HitInfo.Result.HIT and t.events_of("BLOCKED").is_empty() and t.parries.is_empty() and t.player.playerHealth == 998,
		"and it is a HIT all the same (health %d)" % t.player.playerHealth)
	check_flip(t, run, "Idle")
	t.stop_boss_timers()


static func tier_from_sleep(t) -> void:
	t.log_p("-- a root in his nap: he wakes into the headbutt, and the regen stops")
	await ready_at(t, PLAYER_FEET_LEFT)
	var sleep: Node = t.sm.states["Sleep"]
	var hb: Node = t.sm.states["Headbutt"]
	t.boss.boss_health = 30
	t.sm.on_child_transition(t.sm.current_state, "Sleep")
	var regenerating: bool = await t.wait_until(func(): return sleep.is_regenerating() and sleep.healed > 0, 120)
	t.check(regenerating, "asleep and healing (%d so far)" % sleep.healed)
	var health: int = t.boss.boss_health
	var run: Dictionary = await headbutt(t, "hit")
	var mine: Array = run.steps.filter(func(s): return s.state == "Headbutt")
	t.check(hb.from_state == "Sleep" and not mine.is_empty() and mine[0].anim == &"wake", "the root cuts his nap short, and he pops awake into it (%s)" % [mine[0].anim if not mine.is_empty() else &""])
	t.check(sleep.released and not sleep.is_regenerating() and not is_instance_valid(t.boss.regen) and not is_instance_valid(t.boss.zzz),
		"the nap is over: no regen, no Z's")
	t.check(t.boss.boss_health == health, "and he healed nothing more (%d)" % t.boss.boss_health)
	check_headbutt(t, run)
	t.check(hb.result == HitInfo.Result.HIT and t.boss.sprite.flip_h, "it flies left at a player on his left, and lands")
	check_flip(t, run, "Idle")
	t.stop_boss_timers()


static func tier_from_slams(t) -> void:
	t.log_p("-- a root in his string: no headbutt, and it lets go at the next landing")
	await ready_at(t, PLAYER_FEET)
	var slams: Node = t.sm.states["Slams"]
	var hb: Node = t.sm.states["Headbutt"]
	t.sm.on_child_transition(t.sm.current_state, "Slams")
	await t.wait(10)
	var marks := {"headbutt": false, "landed": -1.0, "released": -1.0}
	var root: Node = t.sm.test_root_player()
	var rooted_at: float = t.boss.fight_clock
	if root == null:
		t.check(false, "a root may be sprung in his string")
		return
	var root_id := root.get_instance_id()
	var landing := [t.boss.current_anim == &"slam_impact"]
	var watch := func():
		var now: float = t.boss.fight_clock
		if Spit.state_is(t, "Headbutt"):
			marks.headbutt = true
		var impact: bool = t.boss.current_anim == &"slam_impact"
		if impact and not landing[0] and marks.landed < 0.0:
			marks.landed = now
		landing[0] = impact
		if marks.released < 0.0 and (not is_instance_id_valid(root_id) or instance_from_id(root_id).released):
			marks.released = now
	t.physics_frame.connect(watch)
	await t.wait_until(func(): return marks.released >= 0.0, 150)
	await t.wait(2)
	t.physics_frame.disconnect(watch)
	var held: float = marks.released - rooted_at
	t.log_p("rooted in %s; landed %.4f s on, let go %.4f s on" % [slams.name, marks.landed - rooted_at if marks.landed >= 0.0 else -1.0, held])
	t.check(not marks.headbutt and hb.result < 0, "no headbutt")
	if marks.landed >= 0.0 and marks.landed <= marks.released:
		t.check(marks.released - marks.landed <= FRAME_TIME + 0.0001, "the root lets go at the next landing (%.4f s after it)" % (marks.released - marks.landed))
	else:
		t.log_p("no landing came while it held: his string is still the Phase 0 stub, or slower than the hold")
		t.check(marks.released >= 0.0 and absf(held - t.sm.SLAMS_ROOT_HOLD) <= SLACK, "it lets go by itself at the string's %.1f s hold (%.4f)" % [t.sm.SLAMS_ROOT_HOLD, held])
	t.check(not t.player.is_action_locked, "and the player is free")
	t.sm.on_child_transition(t.sm.current_state, "Idle")
	t.stop_boss_timers()


# Against each rope the formula's launch spot would put him off the screen: below the ring at the bottom, his
# badge over the top at the top. The spot is clamped, the flight closes the height, and it still lands. His
# frames reach his feet (the launch and the bonk), so at the bottom his feet stay on the screen from the root
# to the landing. At the top his flip back's tuck, 408 px tall, rises past the screen's top the way his
# standing crown already does at WALK_RECT's top: logged, not checked.
static func tier_ropes(t) -> void:
	var hb: Node = t.sm.states["Headbutt"]
	var screen: float = ScreenView.VIEW_SIZE.y
	var flight_box: Rect2 = Layout.body_rect(&"headbutt")
	var head: Vector2 = Layout.texel_local(Layout.head(&"headbutt_fly"), &"headbutt_fly")
	for rope in ["bottom", "top"]:
		t.log_p("-- rooted against the %s rope" % rope)
		await ready_at(t, PLAYER_FEET)
		await walk_to_rope(t, KEY_DOWN if rope == "bottom" else KEY_UP)
		var level: float = t.sm.player_hurtbox_centre().y - head.y
		var run: Dictionary = await headbutt(t, "hit")
		check_headbutt(t, run)
		var mine: Array = run.steps.filter(func(s): return s.state == "Headbutt")
		var windup: Array = mine.filter(func(s): return s.beat == hb.Beat.WINDUP)
		var flying: Array = mine.filter(func(s): return s.beat == hb.Beat.FLIGHT)
		var recoil: Array = mine.filter(func(s): return s.beat == hb.Beat.RECOIL)
		var badge_top: float = windup.map(func(s): return s.badge_top).min() if not windup.is_empty() else -INF
		var lowest: float = mine.map(func(s): return s.drawn).max()
		var tuck_top: float = recoil.map(func(s): return s.drawn - TUCK_HEIGHT).min() if not recoil.is_empty() else INF
		t.log_p("the player's feet %s; his launch spot %s where the formula had y %.0f; badge top %.0f; lowest feet %.0f; tuck top %.0f"
			% [t.sm.player_feet(), hb.launch_spot, level, badge_top, lowest, tuck_top])
		t.check(absf(hb.launch_spot.y - roundf(level)) >= 1.0, "the formula's launch spot would have left the screen: clamped from y %.0f to %.0f" % [level, hb.launch_spot.y])
		t.check(not windup.is_empty() and badge_top >= 0.0 and windup.all(func(s): return s.drawn <= t.sm.WALK_RECT.end.y),
			"his whole wind-up on screen: its badge's top at or under the screen's top, his feet inside WALK_RECT")
		t.check(flying.all(func(s): return s.drawn + flight_box.position.y >= 0.0 and s.drawn + flight_box.end.y <= screen), "his flying body on screen, top and bottom")
		if rope == "bottom":
			t.check(lowest <= screen, "his feet on the screen from the root to the landing (lowest %.0f)" % lowest)
		t.check(hb.result == HitInfo.Result.HIT and t.player.playerHealth == 998, "and the impact still lands (health %d)" % t.player.playerHealth)
		check_flip(t, run, "Idle")
		t.stop_boss_timers()
