extends RefCounted

# eric_window_daze: his earned punish windows take a POW's uppercut mash again (the user, 2026-10-05;
# EricScript.daze_in_windows). --fixed-fps 60, V2:
#   Winded       three punches daze him; a two-bar mash juggles him, and he gets up for the sword the
#                uppercut knocked away and starts his next chain
#   a stagger    a parried bear hug's stagger and his own sword's both take the daze; neither fires an
#                uppercut of its own
#   the hug      (the user, 2026-10-06) a parried hug's stagger takes all three punches of a POW, and its
#                mash juggles him: the uppercut knocks the sword he holds into the mat, one sword, which he
#                gets up for. His sword's stagger does the same (the user, 2026-10-06). His stumble after a whiffed hug takes the
#                daze too: the sword he planted across the ring stays planted, the one sword, and he gets up
#                for it there; a fizzled mash leaves the hug to run on, back to it
#   once         a window's daze is spent once it has been used, and the next window has its own
#   switched off daze_in_windows false: three punches in Winded stay three punches, a stagger can't be dazed,
#                a parried hug's stagger and his sword's take two punches again, and the stumble can't be dazed
#   death        killed in the air out of the stumble, he lands into his defeat, one sword in the mat

const WINDOW_HOLD := 60.0
const DROPPED_SWORD := preload("res://Scripts/States/Eric/EricDroppedSword.gd")


static func run(t) -> void:
	t.pin_eric(2)
	await t.load_eric()
	await park(t)
	t.health_ok()
	var finisher: Node = t.player.get_node("Finisher")
	var hurtbox: Area2D = t.boss.get_node("Hurtbox")
	var home: Vector2 = t.boss.global_position
	t.check(t.boss.daze_in_windows, "the knob ships on")

	t.log_p("-- Winded: a POW dazes him, and the mash juggles him")
	await open_winded(t)
	await three_punches(t)
	t.check(await t.wait_until(func(): return finisher.phase == t.FINISHER_DAZED and finisher.prompt_visible, 120), "three punches in Winded put the mash's prompt up (phase %d)" % finisher.phase)
	var tiers: int = await t.mash_tiered(t.TIER_PASS_FRAMES[1])
	t.check(await t.wait_until(func(): return str(t.sm.current_state.name) == "Juggled", 300), "the mash juggles him (%d presses, %s)" % [tiers, t.sm.current_state.name])
	await t.wait_until(func(): return finisher.phase == t.FINISHER_OFF, 600)
	t.check(finisher.juggle_tiers == 2, "two bars at bar 2's rate (%d)" % finisher.juggle_tiers)
	t.check(await t.wait_until(func(): return str(t.sm.current_state.name) == "Broken" and t.sm.states["Broken"].retrieving, 300), "down, he gets up for the sword the uppercut knocked away")
	t.check(await t.wait_until(func(): return ["Earthquake", "Whirlwind", "SwordThrow", "BearHug"].has(str(t.sm.current_state.name)), 600), "and his next chain starts (%s)" % t.sm.current_state.name)
	await park(t)
	await reset(t, home)

	t.log_p("-- once a window")
	await open_winded(t)
	t.boss.daze_used = true
	await three_punches(t)
	await t.wait(30)
	t.check(finisher.phase == t.FINISHER_OFF and not t.boss.can_be_dazed(), "a spent daze stays spent for the rest of the window")
	await reset(t, home)
	await open_winded(t)
	t.check(t.boss.can_be_dazed(), "and the next window has its own")
	await reset(t, home)

	t.log_p("-- the staggers")
	t.sm.parry_stagger(WINDOW_HOLD, home)
	await t.wait(3)
	t.check(str(t.sm.current_state.name) == "ParryStaggered" and not t.sm.states["ParryStaggered"].from_reflect and t.boss.can_be_dazed(), "a parried hug's stagger takes the daze")
	await t.wait(30)
	t.check(finisher.phase == t.FINISHER_OFF, "and nothing fires on its own")
	await reset(t, home)
	t.sm.parry_stagger(WINDOW_HOLD, home, true)
	await t.wait(3)
	t.check(t.boss.can_be_dazed(), "so does his own sword's")
	var sword_hits: Array = await punches_dealt(t)
	t.check(sword_hits == [1, 1, 2], "his sword's stagger takes all three punches of a POW (%s)" % [sword_hits])
	t.check(await t.wait_until(func(): return finisher.phase == t.FINISHER_DAZED and finisher.prompt_visible, 120), "and they put the mash's prompt up")
	await t.mash_tiered(t.TIER_PASS_FRAMES[1])
	t.check(await t.wait_until(func(): return str(t.sm.current_state.name) == "Juggled", 300), "the mash juggles him (%s)" % t.sm.current_state.name)
	t.check(swords(t) == 1 and is_instance_valid(t.sm.dropped_sword), "the uppercut knocks his sword into the mat: one sword (%d)" % swords(t))
	await t.wait_until(func(): return finisher.phase == t.FINISHER_OFF, 600)
	t.check(await t.wait_until(func(): return ["Earthquake", "Whirlwind", "SwordThrow", "BearHug"].has(str(t.sm.current_state.name)), 900) and swords(t) == 0, "he gets up for it, and his next chain starts with it in his hands (%s, %d in the mat)" % [t.sm.current_state.name, swords(t)])
	await park(t)
	await reset(t, home)

	t.log_p("-- a parried hug: three punches, the mash, the juggle")
	t.sm.parry_stagger(WINDOW_HOLD, home)
	await t.wait(3)
	var health_before: int = t.boss.boss_health
	await three_punches(t)
	t.check(health_before - t.boss.boss_health == 4, "all three punches of a POW land in a parried hug's stagger (%d off)" % (health_before - t.boss.boss_health))
	t.check(await t.wait_until(func(): return finisher.phase == t.FINISHER_DAZED and finisher.prompt_visible, 120), "and they put the mash's prompt up")
	await t.mash_tiered(t.TIER_PASS_FRAMES[1])
	t.check(await t.wait_until(func(): return str(t.sm.current_state.name) == "Juggled", 300), "the mash juggles him (%s)" % t.sm.current_state.name)
	t.check(swords(t) == 1 and is_instance_valid(t.sm.dropped_sword), "the uppercut knocks the sword he holds into the mat: one sword (%d)" % swords(t))
	await t.wait_until(func(): return finisher.phase == t.FINISHER_OFF, 600)
	t.check(await t.wait_until(func(): return str(t.sm.current_state.name) == "Broken" and t.sm.states["Broken"].retrieving, 300), "down, he gets up for it")
	t.check(await t.wait_until(func(): return ["Earthquake", "Whirlwind", "SwordThrow", "BearHug"].has(str(t.sm.current_state.name)), 600) and swords(t) == 0, "and his next chain starts with it in his hands (%s, %d in the mat)" % [t.sm.current_state.name, swords(t)])
	await park(t)
	await reset(t, home)

	t.log_p("-- the hug's stumble: the daze, the mash, the juggle, and his planted sword")
	var hug: Node = await open_stumble(t, home)
	t.check(hug.phase == hug.Phase.STUMBLE and t.boss.can_be_dazed() and not t.boss.daze_used, "his stumble after a whiffed hug takes the daze, a window of its own")
	t.check(hug.sword_planted() and swords(t) == 1, "his sword stands where he planted it (%d)" % swords(t))
	var planted_at: Vector2 = drawn_at(hug.planted_sword)
	await three_punches(t)
	t.check(await t.wait_until(func(): return finisher.phase == t.FINISHER_DAZED and finisher.prompt_visible, 120), "three punches in the stumble put the mash's prompt up")
	await t.mash_tiered(t.TIER_PASS_FRAMES[1])
	t.check(await t.wait_until(func(): return str(t.sm.current_state.name) == "Juggled", 300), "the mash juggles him (%s)" % t.sm.current_state.name)
	var dropped = t.sm.dropped_sword
	var last_frame: int = load("res://Scripts/EricArtLayout.gd").broken().sword.frame_times.size()
	t.check(is_instance_valid(dropped) and drawn_at(dropped).distance_to(planted_at) < 1.0 and dropped.frame == last_frame and swords(t) == 1, "his sword stays where he planted it, standing, the one sword (%d; drawn at %s, planted %s)" % [swords(t), drawn_at(dropped) if is_instance_valid(dropped) else Vector2.INF, planted_at])
	await t.wait_until(func(): return finisher.phase == t.FINISHER_OFF, 600)
	var broken: Node = t.sm.states["Broken"]
	t.check(await t.wait_until(func(): return t.sm.current_state == broken and broken.retrieving, 300), "down, he gets up for it")
	var launched := [Vector2.INF]
	var flew: bool = await t.wait_until(func():
		if is_instance_valid(broken.flying_sword) and launched[0] == Vector2.INF:
			launched[0] = broken.flying_sword.global_position
		return launched[0] != Vector2.INF, 300)
	t.check(flew and absf(launched[0].x - planted_at.x) < 60.0, "and calls it back from where it stood (from %s, planted at %s)" % [launched[0], planted_at])
	t.check(await t.wait_until(func(): return ["Earthquake", "Whirlwind", "SwordThrow", "BearHug"].has(str(t.sm.current_state.name)), 600) and swords(t) == 0, "then his next chain starts with it in his hands (%s, %d in the mat)" % [t.sm.current_state.name, swords(t)])
	await park(t)
	await reset(t, home)

	t.log_p("-- the stumble after a fizzled mash")
	hug = await open_stumble(t, home)
	await three_punches(t)
	t.check(await t.wait_until(func(): return finisher.phase == t.FINISHER_DAZED, 120), "dazed in the stumble")
	await t.wait_until(func(): return finisher.phase == t.FINISHER_OFF, 900)
	t.boss.animationPlayer.speed_scale = 1.0
	var ran_on: bool = await t.wait_until(func(): return t.sm.current_state != hug or hug.phase == hug.Phase.RETRIEVE, 900)
	t.check(ran_on and swords(t) <= 1 and not is_instance_valid(t.sm.dropped_sword), "nothing banked: the hug runs on, back to his planted sword, and nothing is left in the mat (%s)" % t.sm.current_state.name)
	await park(t)
	await reset(t, home)

	t.log_p("-- switched off")
	t.boss.daze_in_windows = false
	await open_winded(t)
	t.check(not t.boss.can_be_dazed() and hurtbox.monitoring, "Winded: open to punches, never dazed")
	var health: int = t.boss.boss_health
	await three_punches(t)
	await t.wait(30)
	t.check(finisher.phase == t.FINISHER_OFF and t.boss.boss_health < health, "three punches land and nothing more (%d off)" % (health - t.boss.boss_health))
	await reset(t, home)
	t.sm.parry_stagger(WINDOW_HOLD, home)
	await t.wait(3)
	t.check(not t.boss.can_be_dazed(), "a parried hug's stagger: never dazed")
	var off_hits: Array = await punches_dealt(t)
	t.check(off_hits == [1, 1, 0], "and it takes two punches again (%s)" % [off_hits])
	await reset(t, home)
	t.sm.parry_stagger(WINDOW_HOLD, home, true)
	await t.wait(3)
	var off_sword: Array = await punches_dealt(t)
	t.check(off_sword == [1, 1, 0], "so does his sword's (%s)" % [off_sword])
	await reset(t, home)
	hug = await open_stumble(t, home)
	t.check(hug.phase == hug.Phase.STUMBLE and not t.boss.can_be_dazed(), "the hug's stumble: never dazed")
	await three_punches(t)
	await t.wait(30)
	t.check(finisher.phase == t.FINISHER_OFF, "three punches there and nothing more")
	t.boss.daze_in_windows = true
	await park(t)
	await reset(t, home)

	t.log_p("-- killed in the air out of the stumble")
	hug = await open_stumble(t, home)
	var planted_last: Vector2 = drawn_at(hug.planted_sword)
	t.boss.boss_health = 20
	await three_punches(t)
	t.check(await t.wait_until(func(): return finisher.phase == t.FINISHER_DAZED and finisher.prompt_visible, 120), "dazed on %d health" % t.boss.boss_health)
	await t.mash_tiered(t.TIER_PASS_FRAMES[1])
	t.check(await t.wait_until(func(): return t.boss.boss_health <= 0, 600), "the first uppercut kills him (%d)" % t.boss.boss_health)
	t.check(await t.wait_until(func(): return str(t.sm.current_state.name) == "Downed" and t.sm.states["Downed"].lying, 600), "he lands into his defeat, lying (%s)" % t.sm.current_state.name)
	t.check(await t.wait_until(func(): return finisher.phase == t.FINISHER_OFF, 600) and t.root.get_node_or_null("FightOutro") != null, "the finisher ends and the outro is up")
	t.check(swords(t) == 1 and is_instance_valid(t.sm.dropped_sword) and drawn_at(t.sm.dropped_sword).distance_to(planted_last) < 1.0, "his sword still stands where he planted it, the one sword (%d)" % swords(t))


# His turns stopped and his gauge held, but his states still stepping: the juggle and his getting up run on them.
static func park(t) -> void:
	t.park_eric()
	t.sm.set_process(true)
	t.sm.set_physics_process(true)
	await t.wait(2)


static func open_winded(t) -> void:
	t.sm.downed_state_timer.start(WINDOW_HOLD)
	t.sm.on_child_transition(t.sm.current_state, "Winded")
	await t.wait(3)


# Three landed punches from beside his hurtbox, the combo started fresh.
static func three_punches(t) -> void:
	t.place_under(t.boss.get_node("Hurtbox"))
	t.player.combo.reset()
	await t.wait(4)
	for i in 3:
		await t.swing()
		if i < 2:
			await t.wait(6)


# A yellow hug whiffed on purpose, its stumble held: the next of his hugs is yellow (EricColourRule never
# gives three of a kind), its shoulder charge goes through the player, and the stumble follows either way.
static func open_stumble(t, home: Vector2) -> Node:
	var hug: Node = t.sm.states["BearHug"]
	hug.hugs_started = 1
	hug.recent_yellows.assign([false, false])
	t.boss.global_position = home
	await t.settle_player(home + Vector2(420, 260))
	t.sm.on_child_transition(t.sm.current_state, "BearHug")
	await t.wait_until(func(): return hug.phase == hug.Phase.STUMBLE, 600)
	t.boss.animationPlayer.speed_scale = 0.0
	t.clear_iframes()
	t.health_ok()
	await t.wait(20)
	return hug


# What each of three punches from beside his hurtbox dealt, the combo started fresh.
static func punches_dealt(t) -> Array:
	t.place_under(t.boss.get_node("Hurtbox"))
	t.player.combo.reset()
	await t.wait(4)
	var dealt := []
	for i in 3:
		dealt.append(await t.swing())
		if i < 2:
			await t.wait(6)
	return dealt


# Where a sword sprite's blade is drawn: the middle of its opaque columns, on the mat line under it.
static func drawn_at(sword: Sprite2D) -> Vector2:
	return Vector2(sword.global_position.x + DROPPED_SWORD.drawn_centre_x(sword) * sword.global_scale.x, sword.global_position.y)


# His sword in the mat, drawn: the hug's planted one or the one knocked out of his hands.
static func swords(t) -> int:
	var paths := ["res://Assets/Characters/Eric/eric_bearhug_planted_sword_v2.png", load("res://Scripts/EricArtLayout.gd").broken().sword.texture]
	return t.current_scene.find_children("*", "Sprite2D", true, false).filter(func(s): return s.visible and not s.is_queued_for_deletion() and s.texture != null and paths.has(s.texture.resource_path)).size()


static func reset(t, home: Vector2) -> void:
	t.sm.chain = []
	t.sm.rest_timer.stop()
	t.sm.downed_state_timer.stop()
	t.sm.on_child_transition(t.sm.current_state, "Idle")
	t.boss.global_position = home
	# Full again: every juggle here takes a third of him.
	t.boss.boss_health = t.boss.max_health
	t.clear_iframes()
	t.health_ok()
	await t.wait(20)
