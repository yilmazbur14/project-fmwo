extends RefCounted

# danny_bump (Danny D, Addendum 1): his ring-out belly bump (DannyBossBellyBump) in his fight, his cycle parked and
# the bump started from Idle with the player standing in the ring. --fixed-fps 60. tier=
#   parry    (the default) a fresh press as the belly meets them: PARRIED, the player moves no more than 2 px, HELD!,
#            and he is dizzy in Staggered for the parry's stagger and his walk_in; one read.
#   hit      no answer: carried into the side rope, 1 + 1 half-hearts, the feet within 30 px of the rope's inner line
#            when it catches them, and free again within 1.2 s of the contact; then Idle.
#   dash     a dash in through him as the belly arrives: DODGED and a read; he runs on into the rope and skids back.
#   slip     an armed puddle on his line: he slips on it, it goes, and he lies on his back for 2.2 s with a cap of 4
#            and the finisher's daze on offer (the user, 2026-10-06: 3 hits always trigger the uppercut;
#            pow_always_dazes plays the mash), beside the player, level with them and clear of them, his lying box under the top
#            rope and the boss bar; the player unhurt. Twice: mid-floor, then by the top rope, where he slides down
#            off his line to lie there.
#   ropes    the player 60 px off the left rope: a short shove into it, still 1 + 1, the rope's FX on the left rope.
#   timing   a whiffed press during his slide, then the parry: the red badge up from the wind-up to the contact, the
#            parry rearmed at the tell, launch to contact at least 0.30 s, and PARRIED.
#   rooted   rooted during the wind-up: the parry still works; and on a hit, the root is let go before the shove.
#   walkout  (the 2026-10-04 playtest) walking up or down from the crouch, the launch or just after it, and holding it:
#            his run leans after them (run_align_speed) and the bump lands, 1 + 1, every time; on a straight line
#            every one of these walked out of it.
#   vdash    a dash straight down at the launch and at five moments of the run after it: out of his line every time,
#            unhurt, and he runs on into the rope.
#   through  walking at him in the wind-up and dashing through him just after the launch: behind him when his belly
#            gets there, so he runs on, unhurt (it used to hit them from behind once the dash's immunity was over).
#   punish   (the 2026-10-06 tuning) parried, then the experienced player's punish: 0.20 s after his dizzy spell starts,
#            walked straight back in over his rebound and three punches thrown as fast as they come: the third, the POW,
#            lands inside the spell and dazes him for the finisher. In the parry's bare 1.2 s it came 0.1 s too late
#            (Staggered.walk_in).
# Every tier that reaches its contact: one wind-up, the red badge up from it to the contact, and ROOT_GRACE from the
# bump's end.

const BODY := "Arena/DannyBossScene/DannyBossCharacterBody"
const PUDDLE_SCRIPT := "res://Scripts/DannyBossPuddleScript.gd"
const HIT_INFO := "res://Scripts/HitInfo.gd"
const SEED := 20260929
const FRAME := 1.0 / 60.0
const SLACK := FRAME + 0.0001
# He starts at HOME, left of the player, so he runs right.
const STAND := Vector2(1100, 700)
# The same by the top rope, where lying on his line would put him over it and the boss bar.
const STAND_TOP := Vector2(1100, 330)
const LEAD := 4.0 / 60.0
const DASH_LEAD := 3.0 / 60.0
const GAUGE_READ := 100.0 / 8.0
const TIERS := ["parry", "hit", "dash", "slip", "ropes", "timing", "rooted", "walkout", "vdash", "through", "punish"]
# punish: the experienced player's learned reaction to his dizzy spell (playtest_1004/BRIEF.md).
const PUNISH_REACTION := 0.20
# walkout: when each walk starts, from the wind-up's start (the launch is at its 0.80).
const WALK_STARTS := [0.45, 0.60, 0.80, 0.90]
# vdash: how long after the launch each dash goes.
const VDASH_AFTER := [0.0, 0.05, 0.10, 0.15, 0.20, 0.25]
# through: the dash through him, from the wind-up's start.
const THROUGH_AT := [0.80, 0.85, 0.90]


static func run(t) -> void:
	var tier: String = "parry" if t.tier == "normal" else t.tier
	if not tier in TIERS:
		t.check(false, "tier is one of %s (%s)" % [TIERS, tier])
		return
	await enter(t)
	match tier:
		"parry":
			await tier_parry(t)
		"hit":
			await tier_hit(t)
		"dash":
			await tier_dash(t)
		"slip":
			await tier_slip(t, STAND)
			await tier_slip(t, STAND_TOP)
		"ropes":
			await tier_ropes(t)
		"timing":
			await tier_timing(t)
		"rooted":
			await tier_rooted(t, "parry")
			await tier_rooted(t, "hit")
		"walkout":
			for start in WALK_STARTS:
				await tier_walkout(t, start, KEY_DOWN, STAND_TOP + Vector2(0, 120))
				await tier_walkout(t, start, KEY_UP, STAND)
		"vdash":
			for after in VDASH_AFTER:
				await tier_vdash(t, after)
		"through":
			for dash_at in THROUGH_AT:
				await tier_through(t, dash_at)
		"punish":
			await tier_punish(t)


static func enter(t) -> void:
	await t.load_fight("danny")
	t.boss = t.current_scene.get_node(BODY)
	t.sm = t.boss.state_machine
	t.sm.rng.seed = SEED
	park(t)


static func park(t) -> void:
	t.sm.on_child_transition(t.sm.current_state, "Idle")
	t.stop_boss_timers()


# At HOME and parked, nothing of his on the mat, an empty gauge, the player fresh at `at` with every key up.
static func reset(t, at: Vector2) -> void:
	park(t)
	t.boss.global_position = t.sm.HOME
	t.boss.show_body()
	t.sm.clear_puddles()
	for hazard in t.get_nodes_in_group(t.sm.HAZARD_GROUP):
		hazard.queue_free()
	for code in [KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN, KEY_SHIFT]:
		t.release(code)
	t.player.unlock_actions()
	t.sm.root_grace_left = 0.0
	t.clear_iframes()
	t.player.playerHealth = 100
	t.defense._set_stamina(t.defense.max_stamina)
	t.boss.break_gauge.locked = false
	t.boss.break_gauge.value = 0.0
	await t.settle_player(at)
	await t.wait(30)


static func bump_state(t) -> Node:
	return t.sm.states["BellyBump"]


# The bump from Idle, watched every step from here until finish(): his beat, the badge, the player's position and
# seal, the popups, and the states he goes through.
static func start(t) -> Dictionary:
	var bump: Node = bump_state(t)
	var seen := {"badge_up": [], "badge_gaps": [], "positions": [], "states": [], "sealed": false, "skidded": false,
		"popups": [], "grace_at_end": -1.0, "freed_at": -1.0, "start": t.boss.fight_clock}
	var popups: Node = t.player.get_parent().get_node_or_null(^"CanvasLayer/CombatPopups")
	seen.watch = func():
		var name: String = t.sm.current_state.name
		if seen.states.is_empty() or seen.states[-1] != name:
			seen.states.append(name)
		if popups != null:
			for popup in popups.popups:
				if not seen.popups.has(popup.kind):
					seen.popups.append(popup.kind)
		if bump.contact_at >= 0.0 and seen.freed_at < 0.0 and not t.player.is_action_locked:
			seen.freed_at = t.boss.fight_clock
		if t.sm.current_state != bump:
			if seen.grace_at_end < 0.0 and seen.states.size() > 1:
				seen.grace_at_end = t.sm.root_grace_left
			return
		var badge: bool = not t.live_tells().is_empty()
		seen.positions.append(t.player.global_position)
		if bump.beat == bump.Beat.WINDUP or (bump.beat == bump.Beat.RUN and bump.contact_at < 0.0 and not bump.run_on):
			if not badge:
				seen.badge_gaps.append(snappedf(t.boss.fight_clock - seen.start, 0.001))
		if badge:
			seen.badge_up.append(snappedf(t.boss.fight_clock, 0.001))
		seen.sealed = seen.sealed or t.player.lock_seals_guard
		if bump.beat == bump.Beat.SKID:
			seen.skidded = true
	t.sm.on_child_transition(t.sm.current_state, "BellyBump")
	t.physics_frame.connect(seen.watch)
	return seen


# Out of the bump and `settle` steps more, then the watch stops.
static func finish(t, seen: Dictionary, settle := 30) -> void:
	var bump: Node = bump_state(t)
	await t.wait_until(func(): return t.sm.current_state != bump, 400)
	await t.wait_until(func(): return not t.player.is_action_locked, 120)
	await t.wait(settle)
	t.physics_frame.disconnect(seen.watch)


# Until his run has only `lead` s left to the contact his launch planned, for a player standing still.
static func until_contact_lead(t, bump: Node, lead: float) -> void:
	await t.wait_until(func(): return bump.beat == bump.Beat.RUN, 400)
	await t.wait_until(func(): return bump.beat != bump.Beat.RUN or bump.beat_clock >= bump.run_time - lead, 120)


static func press_parry(t, bump: Node) -> void:
	await until_contact_lead(t, bump, LEAD)
	t.press(KEY_SHIFT)
	await t.wait_until(func(): return bump.result >= 0 or bump.run_on or bump.slipped, 60)
	t.release(KEY_SHIFT)


static func player_box(t) -> Rect2:
	var shape: CollisionShape2D = t.player.hurtBox.get_node("CollisionShape2D")
	return shape.global_transform * shape.shape.get_rect()


static func result_name(result: int) -> String:
	var hit_info: GDScript = load(HIT_INFO)
	return "none" if result < 0 else hit_info.Result.keys()[result]


static func log_run(t, bump: Node, seen: Dictionary, health: int) -> void:
	t.log_p("result %s, rope %s; windup %.3f, launch %.3f, contact %.3f; line %s; shoved to %s; slipped %s, ran on %s, skidded %s; health %d -> %d; gauge %.1f; states %s; popups %s; freed at %.3f; grace at the end %.2f" % [
		result_name(bump.result), result_name(bump.rope_result), bump.windup_at, bump.launch_at, bump.contact_at,
		bump.line, bump.shoved_to, bump.slipped, bump.ran_on, seen.skidded, health, t.player.playerHealth,
		t.boss.break_gauge.value, seen.states, seen.popups, seen.freed_at, seen.grace_at_end])


static func check_common(t, bump: Node, seen: Dictionary) -> void:
	t.check(bump.rearms == 1 and bump.windup_at >= 0.0, "one wind-up, the parry rearmed at its tell (%d)" % bump.rearms)
	t.check(seen.badge_gaps.is_empty(), "the red badge up from the wind-up to the contact (%s)" % [seen.badge_gaps])
	t.check(seen.grace_at_end >= t.sm.ROOT_GRACE - 3.0 * FRAME, "no puddle roots for the grace after it (%.2f)" % seen.grace_at_end)


static func tier_parry(t) -> void:
	t.log_p("-- a fresh press as the belly meets them")
	await reset(t, STAND)
	var health: int = t.player.playerHealth
	var seen := start(t)
	var bump: Node = bump_state(t)
	await press_parry(t, bump)
	var stag: Node = t.sm.states["Staggered"]
	await t.wait_until(func(): return t.sm.current_state == stag, 120)
	var entered: float = t.boss.fight_clock
	var window: float = stag.left
	await t.wait_until(func(): return t.sm.current_state != stag, 240)
	var dizzy: float = t.boss.fight_clock - entered
	await finish(t, seen, 10)
	log_run(t, bump, seen, health)
	var moved := 0.0
	for at in seen.positions:
		moved = maxf(moved, at.distance_to(seen.positions[0]))
	# The parry's stagger and his walk_in, the time to walk back in over his rebound (the 2026-10-06 tuning).
	var want: float = t.defense.parry_stagger_time + stag.walk_in
	t.log_p("the player moved at most %.1f px; Staggered %.3f s (window %.3f, the parry's %.2f and %.2f to walk in)" % [moved, dizzy, window, t.defense.parry_stagger_time, stag.walk_in])
	t.check(result_name(bump.result) == "PARRIED" and t.player.playerHealth == health, "PARRIED, unhurt")
	t.check(moved <= 2.0, "the player holds their ground: at most 2 px (%.1f)" % moved)
	t.check(seen.popups.has(&"held"), "HELD! (%s)" % [seen.popups])
	t.check(absf(window - want) <= 0.001 and absf(dizzy - want) <= SLACK + FRAME, "dizzy in Staggered for the parry's stagger and the walk in, %.2f s (%.3f)" % [want, dizzy])
	t.check(is_equal_approx(t.boss.break_gauge.value, GAUGE_READ), "one read (%.2f)" % t.boss.break_gauge.value)
	check_common(t, bump, seen)


static func tier_hit(t) -> void:
	t.log_p("-- no answer: into the ropes")
	await reset(t, STAND)
	var health: int = t.player.playerHealth
	var seen := start(t)
	var bump: Node = bump_state(t)
	await finish(t, seen)
	log_run(t, bump, seen, health)
	var rope_x: float = t.sm.ROPES.end.x
	t.check(result_name(bump.result) == "HIT" and result_name(bump.rope_result) == "HIT", "the bump and the rope both land")
	t.check(health - t.player.playerHealth == 2, "1 + 1 half-hearts (%d)" % (health - t.player.playerHealth))
	t.check(bump.shoved_to != Vector2.INF and absf(bump.shoved_to.x - rope_x) <= 30.0, "carried to the rope: the feet %.1f px off its inner line" % absf(bump.shoved_to.x - rope_x))
	t.check(seen.sealed, "sealed while carried")
	t.check(seen.freed_at >= 0.0 and seen.freed_at - bump.contact_at <= 1.2, "free again %.3f s after the contact" % (seen.freed_at - bump.contact_at))
	t.check(seen.states.has("Idle") and not seen.states.has("Staggered"), "then Idle (%s)" % [seen.states])
	check_common(t, bump, seen)


static func tier_dash(t) -> void:
	t.log_p("-- a dash in through him as the belly arrives")
	await reset(t, STAND)
	var health: int = t.player.playerHealth
	var seen := start(t)
	var bump: Node = bump_state(t)
	await until_contact_lead(t, bump, DASH_LEAD)
	t.press(KEY_LEFT)
	t.tap(KEY_W)
	await t.wait_until(func(): return bump.result >= 0 or bump.run_on, 60)
	await t.wait_until(func(): return not t.player.is_dodging, 30)
	t.release(KEY_LEFT)
	await finish(t, seen)
	log_run(t, bump, seen, health)
	t.check(result_name(bump.result) == "DODGED" and t.player.playerHealth == health, "DODGED, unhurt")
	t.check(is_equal_approx(t.boss.break_gauge.value, GAUGE_READ), "a read (%.2f)" % t.boss.break_gauge.value)
	t.check(bump.ran_on and seen.skidded, "he runs on into the rope and skids back")
	check_common(t, bump, seen)


static func tier_slip(t, stand: Vector2) -> void:
	t.log_p("-- an armed puddle on his line, the player at %s" % stand)
	await reset(t, stand)
	var health: int = t.player.playerHealth
	# His launch spot is 620 px left of the player's feet: a puddle 220 px along from it.
	var feet: Vector2 = t.sm.player_feet()
	var puddle: Node2D = load(PUDDLE_SCRIPT).new()
	puddle.player = t.player
	puddle.body = t.boss
	puddle.state_machine = t.sm
	t.sm.add_hazard(puddle, feet + Vector2(-400, 0), t.boss.floor_layer)
	t.sm.register_puddle(puddle)
	await t.wait_until(func(): return puddle.armed, 60)
	var on_back: Node = t.sm.states["OnBack"]
	var seen := start(t)
	var bump: Node = bump_state(t)
	await t.wait_until(func(): return bump.slipped or t.sm.current_state != bump, 400)
	await t.wait_until(func(): return t.sm.current_state == on_back and on_back.is_window(), 120)
	var back := {"open_for": on_back.open_for, "cap": on_back.hit_cap, "dazeable": on_back.dazeable,
		"can_daze": t.boss.can_be_dazed(), "opened": t.boss.fight_clock}
	var lying: Rect2 = t.boss.hurtbox_rect()
	var hurt := player_box(t)
	back.top = lying.position.y
	back.gap = maxf(lying.position.x - hurt.end.x, hurt.position.x - lying.end.x)
	back.level = lying.position.y < hurt.end.y and lying.end.y > hurt.position.y
	back.lowered = t.boss.global_position.y - bump.run_from.y
	await t.wait_until(func(): return not on_back.is_window(), 240)
	back.window = t.boss.fight_clock - back.opened
	await finish(t, seen, 10)
	log_run(t, bump, seen, health)
	t.log_p("on his back: %s" % [back])
	t.check(bump.slipped and result_name(bump.result) == "none", "he slips before he reaches them")
	t.check(not is_instance_valid(puddle) or puddle.gone, "the puddle is gone")
	t.check(is_equal_approx(back.open_for, 2.2) and back.cap == 4 and back.dazeable and back.can_daze,
		"on his back for 2.2 s, a cap of 4, the finisher's daze on offer (%s)" % [back])
	t.check(absf(back.window - 2.2) <= SLACK, "the window held 2.2 s (%.3f)" % back.window)
	t.check(t.player.playerHealth == health, "the player unhurt")
	t.check(bump.rearms == 1, "one wind-up (%d)" % bump.rearms)
	t.check(back.top >= t.sm.lying_top_min - 0.5 and back.gap >= bump.slip_gap - 1.0 and back.level,
		"lying beside them: his box under the top rope and the boss bar (top at y %.0f), %.0f px clear of them, level with them" % [
		back.top, back.gap])
	if stand == STAND_TOP:
		t.check(back.lowered > 0.0, "by the top rope he slides down off his line to lie there (%.0f px)" % back.lowered)


static func tier_ropes(t) -> void:
	t.log_p("-- 60 px off the left rope")
	await reset(t, STAND)
	var shape: CollisionShape2D = t.player.hurtBox.get_node("CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	var at := Vector2(t.sm.ROPES.position.x + 60.0 + (t.player.global_position.x - box.position.x), STAND.y)
	await t.settle_player(at)
	await t.wait(10)
	var health: int = t.player.playerHealth
	var seen := start(t)
	var bump: Node = bump_state(t)
	await t.wait_until(func(): return bump.rope_result >= 0 or t.sm.current_state != bump, 400)
	var rope_x: float = bump.rope_fx.global_position.x if is_instance_valid(bump.rope_fx) else INF
	await finish(t, seen)
	log_run(t, bump, seen, health)
	t.log_p("the rope's FX at x %.1f" % rope_x)
	t.check(bump.line.x < 0.0, "he runs at them leftward, from their right")
	t.check(result_name(bump.result) == "HIT" and result_name(bump.rope_result) == "HIT" and health - t.player.playerHealth == 2,
		"still 1 + 1 half-hearts (%d)" % (health - t.player.playerHealth))
	t.check(bump.shoved_to != Vector2.INF and absf(bump.shoved_to.x - t.sm.ROPES.position.x) <= 30.0, "into the left rope (feet %.1f px off it)" % absf(bump.shoved_to.x - t.sm.ROPES.position.x))
	t.check(absf(rope_x - t.sm.ROPES.position.x) <= 0.5, "the rope's FX on the left rope (x %.1f)" % rope_x)
	check_common(t, bump, seen)


static func tier_timing(t) -> void:
	t.log_p("-- a whiffed press in his slide, then the parry")
	await reset(t, STAND)
	var health: int = t.player.playerHealth
	var seen := start(t)
	var bump: Node = bump_state(t)
	await t.wait_until(func(): return bump.beat == bump.Beat.SLIDE, 60)
	t.tap(KEY_SHIFT)
	await t.wait_until(func(): return bump.beat == bump.Beat.WINDUP, 120)
	var rearmed: bool = t.defense.last_press_time == -INF
	await press_parry(t, bump)
	await finish(t, seen)
	log_run(t, bump, seen, health)
	var badge_from: float = seen.badge_up[0] if not seen.badge_up.is_empty() else -1.0
	t.log_p("badge up from %.3f; wind-up at %.3f, contact at %.3f; launch to contact %.3f" % [badge_from, bump.windup_at, bump.contact_at, bump.contact_at - bump.launch_at])
	t.check(absf(badge_from - bump.windup_at) <= SLACK, "the badge goes up with the wind-up (%.3f, %.3f)" % [badge_from, bump.windup_at])
	t.check(rearmed, "the parry rearmed at the tell: the slide's whiff doesn't count against it")
	t.check(bump.contact_at - bump.launch_at >= 0.30 - 0.0001, "launch to contact at least 0.30 s (%.3f)" % (bump.contact_at - bump.launch_at))
	t.check(result_name(bump.result) == "PARRIED", "PARRIED (%s)" % result_name(bump.result))
	check_common(t, bump, seen)


static func tier_rooted(t, answer: String) -> void:
	t.log_p("-- rooted in the wind-up, then %s" % answer)
	await reset(t, STAND)
	var health: int = t.player.playerHealth
	var seen := start(t)
	var bump: Node = bump_state(t)
	await t.wait_until(func(): return bump.beat == bump.Beat.WINDUP and bump.beat_clock >= bump.windup_time - 0.3, 120)
	var root: Node = t.sm.test_root_player()
	# Read now: the root frees itself once it has let go.
	var held: bool = root != null and t.player.is_action_locked and not t.player.lock_seals_guard
	var released_at_contact := false
	var sealed_at_contact := false
	if answer == "parry":
		await press_parry(t, bump)
	else:
		await t.wait_until(func(): return bump.result >= 0, 120)
		released_at_contact = root != null and (not is_instance_valid(root) or root.released)
		sealed_at_contact = t.player.lock_seals_guard
	await finish(t, seen)
	log_run(t, bump, seen, health)
	t.check(held, "%s: rooted in the wind-up, held but not sealed" % answer)
	if answer == "parry":
		t.check(result_name(bump.result) == "PARRIED", "the parry still works rooted (%s)" % result_name(bump.result))
	else:
		t.check(result_name(bump.result) == "HIT" and released_at_contact and sealed_at_contact,
			"on a hit the root is let go before the shove seals them (%s, %s)" % [released_at_contact, sealed_at_contact])
		t.check(health - t.player.playerHealth == 2 and seen.freed_at >= 0.0, "1 + 1, and free after it")


# Walking `key` from `start` s into the wind-up, held until the bump is over.
static func tier_walkout(t, start: float, key: int, stand: Vector2) -> void:
	t.log_p("-- walking %s from %.2f s into the wind-up, held" % ["down" if key == KEY_DOWN else "up", start])
	await reset(t, stand)
	var health: int = t.player.playerHealth
	var seen := start(t)
	var bump: Node = bump_state(t)
	await t.wait_until(func(): return bump.beat == bump.Beat.WINDUP, 400)
	var from: float = t.boss.fight_clock
	await t.wait_until(func(): return t.boss.fight_clock - from >= start - 0.0001, 120)
	t.press(key)
	await t.wait_until(func(): return bump.result >= 0 or bump.run_on or t.sm.current_state != bump, 240)
	t.release(key)
	await finish(t, seen)
	log_run(t, bump, seen, health)
	t.check(result_name(bump.result) == "HIT" and health - t.player.playerHealth == 2,
		"walking out doesn't dodge him: HIT, 1 + 1 (%s, %d)" % [result_name(bump.result), health - t.player.playerHealth])
	check_common(t, bump, seen)


# A dash straight down `after` s into the run.
static func tier_vdash(t, after: float) -> void:
	t.log_p("-- a dash straight down %.2f s after the launch" % after)
	await reset(t, STAND_TOP + Vector2(0, 120))
	var health: int = t.player.playerHealth
	var seen := start(t)
	var bump: Node = bump_state(t)
	await t.wait_until(func(): return bump.beat == bump.Beat.RUN, 400)
	var from: float = t.boss.fight_clock
	await t.wait_until(func(): return t.boss.fight_clock - from >= after - 0.0001, 60)
	t.press(KEY_DOWN)
	t.tap(KEY_W)
	await t.wait_until(func(): return t.player.is_dodging, 10)
	await t.wait_until(func(): return not t.player.is_dodging, 30)
	t.release(KEY_DOWN)
	await finish(t, seen)
	log_run(t, bump, seen, health)
	t.check(bump.result < 0 and bump.ran_on and seen.skidded and t.player.playerHealth == health,
		"out of his line: no contact, unhurt, he runs on into the rope (%s, ran on %s)" % [result_name(bump.result), bump.ran_on])
	check_common(t, bump, seen)


# Walking at him through the wind-up, then a dash through him `dash_at` s into it (just after the launch).
static func tier_through(t, dash_at: float) -> void:
	t.log_p("-- walking at him, then a dash through him %.2f s into the wind-up" % dash_at)
	await reset(t, Vector2(1100, 600))
	var health: int = t.player.playerHealth
	var seen := start(t)
	var bump: Node = bump_state(t)
	await t.wait_until(func(): return bump.beat == bump.Beat.WINDUP, 400)
	var from: float = t.boss.fight_clock
	var toward: int = KEY_LEFT if t.boss.global_position.x < t.player.global_position.x else KEY_RIGHT
	t.press(toward)
	await t.wait_until(func(): return t.boss.fight_clock - from >= dash_at - 0.0001, 120)
	t.tap(KEY_W)
	await t.wait_until(func(): return t.player.is_dodging, 10)
	await t.wait_until(func(): return not t.player.is_dodging, 30)
	t.release(toward)
	var behind: bool = signf(t.player.global_position.x - bump.run_from.x) != signf(bump.line.x)
	await finish(t, seen)
	log_run(t, bump, seen, health)
	t.check(bump.launch_at >= 0.0 and bump.launch_at < from + dash_at, "the dash came after the launch")
	t.check(behind, "the dash carried them through to behind him")
	t.check(bump.result < 0 and bump.ran_on and t.player.playerHealth == health,
		"never hit from behind: no contact, unhurt, he runs on (%s)" % result_name(bump.result))
	check_common(t, bump, seen)


# Parried, then PUNISH_REACTION into his dizzy spell the walk straight back to the spot a punch reaches him from,
# steered every step, and three punches each the moment the last is done: the POW inside the spell, and his daze.
static func tier_punish(t) -> void:
	t.log_p("-- parried, then walked back in and punished from a %.2f s reaction" % PUNISH_REACTION)
	await reset(t, STAND)
	var seen := start(t)
	var bump: Node = bump_state(t)
	var stag: Node = t.sm.states["Staggered"]
	var finisher: Node = t.player.get_node("Finisher")
	finisher.min_press_interval = 0.0
	await press_parry(t, bump)
	await t.wait_until(func(): return t.sm.current_state == stag, 120)
	var opened: float = t.boss.fight_clock
	await t.wait_until(func(): return t.boss.fight_clock - opened >= PUNISH_REACTION - 0.0001, 60)
	var held := {}
	var spot: Vector2 = t._bot_punch_spot()
	var gap: float = t.player.global_position.distance_to(spot)
	while t.sm.current_state == stag:
		spot = t._bot_punch_spot()
		var d: Vector2 = spot - t.player.global_position
		if d.length() < 10.0:
			break
		var want := {KEY_LEFT: d.x < -6.0, KEY_RIGHT: d.x > 6.0, KEY_UP: d.y < -6.0, KEY_DOWN: d.y > 6.0}
		for code in want:
			if want[code] != held.get(code, false):
				if want[code]:
					t.press(code)
				else:
					t.release(code)
				held[code] = want[code]
		await t.physics_frame
	for code in held:
		if held[code]:
			t.release(code)
	var in_place: float = t.boss.fight_clock - opened
	var swings := 0
	while t.sm.current_state == stag and finisher.phase == t.FINISHER_OFF and swings < 3:
		if t.player.state_machine.current_state.name != "Punching":
			t.tap(KEY_Q)
			swings += 1
		await t.physics_frame
	var dazed: bool = await t.wait_until(func(): return finisher.phase == t.FINISHER_DAZED, 90)
	t.log_p("rebound %.0f px to the punch spot, in place %.2f s into a %.2f s spell, %d swings, dazed %s" % [gap, in_place, t.defense.parry_stagger_time + stag.walk_in, swings, dazed])
	t.check(result_name(bump.result) == "PARRIED", "PARRIED")
	t.check(dazed, "three punches from a %.2f s reaction: the POW lands inside his dizzy spell and dazes him" % PUNISH_REACTION)
	await t.mash_finisher()
	await t.wait_until(func(): return finisher.phase == t.FINISHER_OFF, 300)
	t.physics_frame.disconnect(seen.watch)
