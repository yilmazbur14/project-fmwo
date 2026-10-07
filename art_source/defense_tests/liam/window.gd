extends RefCounted

# liam_window: his punish window and the way back up (LiamDowned, LiamGetUp), the Break he banks on his pillar, and the
# boss HUD's fade, on his test scene.
#   cap      off the beat, every punch a first one: 4 half-hearts in all, the fifth refused (PunchAllowance)
#   finisher a clean combo: 4, and its charged third dazes him into the single-bar uppercut, 10 (a quarter of 40); then
#            he gets up - the player blown to RESET_SPOT, a new pillar, the ride up - into the next attack in the loop
#   banked   a Break filled while he is up on the pillar waits, locked, and his fall lands him in Broken
#   hud      the whole boss HUD at 0.30 while he is up, 1.0 on the mat and back to 0.30 once he is up again; the player's
#            loss while he is up brings it back to 1.0

const Common := preload("res://art_source/defense_tests/liam/common.gd")


static func run(t) -> void:
	await Common.enter(t)
	t.hold_break_gauge(t.boss)
	await cap(t)
	await finisher(t)
	await banked(t)
	await hud_on_loss(t)


static func down(t) -> void:
	await Common.clear(t)
	Common.start(t, "Fall")
	await t.wait_until(func(): return Common.state(t) == "Downed", 90)
	t.place_under(t.boss.get_finisher_hurtbox())
	await t.wait(6)


static func cap(t) -> void:
	t.log_p("-- the window's cap")
	await Common.fresh(t, Vector2(700, 800))
	t.check(is_equal_approx(t.boss.hud_alpha(), t.sm.pillar_hud_fade_alpha), "the HUD at %.2f while he is up (%.2f)" % [t.sm.pillar_hud_fade_alpha, t.boss.hud_alpha()])
	var up_rect: Rect2 = t.sm.stand_rect()
	# Five slow punches outlast his window: it is held open for them.
	var downed_time: float = t.sm.downed_time
	t.sm.downed_time = 30.0
	await down(t)
	t.check(is_equal_approx(t.boss.hud_alpha(), 1.0), "and at 1.0 on the mat (%.2f)" % t.boss.hud_alpha())
	t.check(up_rect.position.y == t.sm.row_stand_top and up_rect.end == t.sm.STAND_RECT.end and t.sm.stand_rect() == t.sm.STAND_RECT, "where he may stand: kept off the row while it stands (%s), all of STAND_RECT once it is down" % up_rect)
	var health: int = t.boss.boss_health
	var dealt := []
	for i in 5:
		dealt.append(await t.swing())
		# Past the combo's beat, so every punch starts a new one.
		await t.wait(50)
	t.sm.downed_time = downed_time
	t.log_p("five punches off the beat: %s" % [dealt])
	t.check(health - t.boss.boss_health == 4 and dealt[4] == 0, "4 in all, the fifth refused (%s)" % [dealt])


static func finisher(t) -> void:
	t.log_p("-- a clean combo and the finisher")
	await Common.fresh(t, Vector2(700, 800))
	t.boss.boss_health = t.boss.max_health
	Common.hold(t)
	t.boss.pillar.rise(t.sm.PERCH, 0.0)
	t.boss.pillar.park()
	t.boss.stand_on_pillar()
	await down(t)
	var fin: Node = t.player.get_node("Finisher")
	fin.min_press_interval = 0.0
	var health: int = t.boss.boss_health
	for i in 3:
		await t.swing()
		if i < 2:
			await t.wait(6)
	var combo: int = health - t.boss.boss_health
	var dazed: bool = await t.wait_until(func(): return fin.phase == t.FINISHER_DAZED and fin.prompt_visible, 120)
	var tiered: bool = fin.tiered
	await t.mash_tiered(5)
	await t.wait_until(func(): return fin.phase == t.FINISHER_OFF, 240)
	var uppercut: int = health - combo - t.boss.boss_health
	t.log_p("combo %d, dazed %s (tiered %s), uppercut %d, now %s" % [combo, dazed, tiered, uppercut, Common.state(t)])
	t.check(combo == 4 and dazed and not tiered, "a clean combo is 4 and dazes him into the single bar")
	t.check(uppercut == roundi(t.boss.max_health * fin.finisher_damage_ratio), "the uppercut: %d, a quarter of %d (%d)" % [roundi(t.boss.max_health * fin.finisher_damage_ratio), t.boss.max_health, uppercut])
	var expected: String = String(t.sm.ATTACK_ROTATION[(t.sm.rotation_index + 1) % t.sm.ATTACK_ROTATION.size()])
	var up: bool = await t.wait_until(func(): return Common.state(t) == "GetUp", 60 * 4)
	var thrown: bool = await t.wait_until(func(): return t.sm.is_launching(), 60 * 3)
	await t.wait_until(func(): return not t.sm.is_launching(), 60 * 2)
	var landed: Vector2 = t.player.global_position
	var back: bool = await t.wait_until(func(): return Common.state(t) != "GetUp", 60 * 5)
	await t.wait(20)
	t.log_p("up %s, blew the player to %s %s, then %s (expected %s), pillar parked %s at %s, hud %.2f" % [up, landed, thrown, Common.state(t), expected, t.boss.pillar.parked, t.boss.pillar.global_position, t.boss.hud_alpha()])
	t.check(up and thrown and landed.distance_to(t.sm.RESET_SPOT) <= 1.0, "he gets up and blows the player to %s" % t.sm.RESET_SPOT)
	t.check(back and Common.state(t) == expected, "and the loop goes on with %s" % expected)
	t.check(t.boss.pillar.parked and t.boss.pillar.global_position == t.sm.PERCH and t.boss.height == t.boss.pillar.top_height(), "on a new pillar at the top")
	t.check(is_equal_approx(t.boss.hud_alpha(), t.sm.pillar_hud_fade_alpha), "the HUD back at %.2f" % t.sm.pillar_hud_fade_alpha)
	Common.hold(t)


static func banked(t) -> void:
	t.log_p("-- a Break while he's up")
	await Common.clear(t)
	await Common.fresh(t, Vector2(700, 800))
	var gauge: Node = t.boss.break_gauge
	gauge.locked = false
	gauge.value = 0.0
	gauge.set_physics_process(true)
	Common.start(t, "Tsunami")
	await t.wait(5)
	gauge.add(gauge.max_value)
	await t.wait(3)
	var owed: bool = t.sm.break_owed
	var still: String = Common.state(t)
	var locked: bool = gauge.locked
	await t.wait(60 * 4)
	t.log_p("owed %s, in %s, locked %s, still locked 4 s on %s" % [owed, still, locked, gauge.locked])
	t.check(owed and still == "Tsunami" and locked and gauge.locked, "banked: his attack goes on and the gauge stays locked")
	Common.start(t, "Fall")
	var broken: bool = await t.wait_until(func(): return Common.state(t) == "Broken", 90)
	t.check(broken and not t.sm.break_owed, "his fall lands him in Broken")
	await t.wait_until(func(): return Common.state(t) != "Broken", 60 * 5)
	t.hold_break_gauge(t.boss)
	await t.wait_until(func(): return Common.state(t) != "GetUp", 60 * 5)
	Common.hold(t)


static func hud_on_loss(t) -> void:
	t.log_p("-- the player's loss while he's up")
	await Common.clear(t)
	t.boss.set_hud_alpha(t.sm.pillar_hud_fade_alpha, 0.0)
	Common.start(t, "Tsunami")
	await t.wait(10)
	t.boss.on_player_defeated()
	await t.wait(30)
	t.log_p("hud %.2f, state %s, hazards %d" % [t.boss.hud_alpha(), Common.state(t), t.get_nodes_in_group(t.sm.HAZARD_GROUP).filter(func(h): return not h.collapsing).size()])
	t.check(is_equal_approx(t.boss.hud_alpha(), 1.0), "the HUD back at 1.0")
	t.check(Common.state(t) == "Idle", "and he stops where he is")
