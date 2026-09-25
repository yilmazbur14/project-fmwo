extends RefCounted

# Jordan's gauge spec for verify_defense.gd's gauge modes (break_gauge, break_entry, juggle, juggle_kill
# and gauge_extra with fight=jordan). The keys and the optional statics are listed over
# GAUGE_FIGHTS_DIR there. He is the reference fight on BossBroken and BossJuggled.

const SPEC := {
	"body": "Arena/JordanScene/JordanCharacterBody",
	# His spot, the user's call. His soles are on y 506 there, already lower than his juggle floor.
	"home": Vector2(960, 410),
	"light": &"funko_blast",
	"strong": &"",
	"foreign": &"josh_card_throw",
	"punish_state": "Taunt",
	"broken_state": "Broken",
	"cycle_states": ["SummonFunkos"],
	"defeated_state": "Defeated",
	"reads_to_break": 6,
	"art": "res://Scripts/JordanArtLayout.gd",
	"juggle_via": "clip",
	"drives_player": true,
}


# His states only run while `fighting` is set, which his post-dialogue timer does and
# reset_gauged()'s stop_boss_timers() keeps from happening. His Idle is held short of summoning, so
# nothing he sends out lands between the checks, until a Break or a juggle sends him back into it and
# starts his cycle again, as it does in play.
static func reset(t) -> void:
	t.sm.fighting = true
	t.sm.stagger_left = 0.0
	t.sm.states["Idle"].rested = -INF
	t.boss.explosion_hits_this_cycle = 0


static func entry_cases(t) -> Array:
	var sm = t.sm
	return [
		["between two summons", func(): sm.on_child_transition(sm.current_state, "Idle"), func(): return sm.current_state.name == "Idle"],
		["his summon's wind-up", func(): sm.on_child_transition(sm.current_state, "SummonFunkos"), func(): return sm.current_state.name == "SummonFunkos" and sm.current_state.elapsed >= 0.3],
		["his figures giving chase", func(): sm.on_child_transition(sm.current_state, "SummonFunkos"), func():
			var figures: Array = t.hazards_of("FunkoFigureScript.gd")
			return figures.size() >= 2 and figures.all(func(f): return f.phase == f.Phase.CHASING)],
		["the taunt", func(): sm.on_child_transition(sm.current_state, "Taunt"), func(): return sm.current_state.name == "Taunt"],
	]


static func extra(t) -> void:
	var boss = t.boss
	var sm = t.sm
	var gauge = boss.break_gauge
	var broken = sm.states["Broken"]
	var juggled = sm.states["Juggled"]

	t.log_p("-- standing high, a Break slides him down to his juggle floor first (BossBroken)")
	boss.global_position = Vector2(960, 200)
	await t.settle_player(Vector2(600, 700))
	var floor_y: float = juggled.floor_y()
	gauge.add(gauge.max_value)
	var broke: bool = await t.wait_until(func(): return sm.current_state == broken, 30)
	var driven: bool = await t.wait_until(func(): return not t.player.is_action_locked, 120)
	var feet: Vector2 = broken._feet()
	var box: Rect2 = boss.hurtbox_rect()
	var stand_off: float = t.player.global_position.y + broken.PLAYER_FEET_OFFSET - broken.PLAYER_IN_FRONT - box.end.y
	t.log_p("floor y %.1f: soles from y 296 to %s; the player driven to %s, %.1f px off his ground line" % [floor_y, feet, t.player.global_position, stand_off])
	t.check(broke and driven and feet == Vector2(960, roundf(floor_y)), "his soles slide from y 296 down to his floor, y %.0f (%s)" % [roundf(floor_y), feet])
	t.check(absf(stand_off) <= 1.0, "and the player is driven in beside where he lands, on that ground line")
	var lift_scale: float = juggled.headroom() / t.player.finisher.planned_apex(3)
	t.check(lift_scale >= 0.49, "where a three-uppercut juggle is drawn at least half its height (%.2f)" % lift_scale)

	t.log_p("-- a Break out of his summon's wind-up puts him down at once, and no figure comes of it")
	await t.reset_gauged(t.fight_spec.home)
	sm.on_child_transition(sm.current_state, "SummonFunkos")
	await t.wait(18)
	gauge.add(gauge.max_value)
	await t.wait_until(func(): return sm.current_state == broken, 30)
	await t.wait(2)
	var sprite: Sprite2D = boss.sprite
	t.log_p("anim %s, sheet %s frame %d, stars at %s, daze anchor %s" % [boss.current_anim, sprite.texture.resource_path.get_file(), sprite.frame, broken.stars.global_position, boss.get_daze_anchor()])
	t.check(boss.current_anim == &"broken" and sprite.texture.resource_path.ends_with("jordan_defeat.png") and sprite.frame == 4, "kneeling on defeat frame 4, not finishing the wind-up first")
	t.check(broken.stars.global_position == broken.head_point().round() and boss.get_daze_anchor() == broken.head_point(), "his stars and the finisher's daze anchor over the kneel's crown")
	await t.wait(60)
	t.check(t.hazards_of("FunkoFigureScript.gd").is_empty(), "and the summon he was winding up never comes")

	t.log_p("-- a figure punched back into him is two reads")
	await t.reset_gauged(t.fight_spec.home)
	var breaks := [0]
	var count_break := func(): breaks[0] += 1
	gauge.broke.connect(count_break)
	boss.take_explosion_hit(1)
	t.check(is_equal_approx(gauge.value, 2.0 * gauge.parry_gain), "its blast: %.3f, two reads of %.3f" % [gauge.value, gauge.parry_gain])
	await t.reset_gauged(t.fight_spec.home)
	for i in 4:
		gauge.add(gauge.parry_gain)
	boss.take_explosion_hit(1)
	t.check(breaks[0] == 1, "four reads and one redirect break him")
	await t.wait(2)
	gauge.broke.disconnect(count_break)
	t.check(sm.current_state == broken and boss.sprite.rotation == 0.0, "down at once, with the blast's lean cut (rotation %.2f)" % boss.sprite.rotation)
