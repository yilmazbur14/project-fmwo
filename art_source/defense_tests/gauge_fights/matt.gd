extends RefCounted

# Matt's gauge spec for verify_defense.gd's gauge modes (break_gauge, break_entry, juggle, juggle_kill
# and gauge_extra with fight=matt). The keys and the optional statics are listed over GAUGE_FIGHTS_DIR
# there. load_fight() parks his yell and pins his rotation to the Ezreal set for all of these modes, so
# a Glass Row or a yell only comes when a case asks for one.

const SPEC := {
	"body": "Arena/MattScene/MattCharacterBody",
	# HOME: where his entrance leaves him and his windows open.
	"home": Vector2(960, 620),
	"light": &"matt_mystic_shot",
	"strong": &"",
	"foreign": &"josh_card_throw",
	"punish_state": "Recover",
	"broken_state": "Broken",
	"cycle_states": ["MysticVolley", "GlassRow"],
	"defeated_state": "Defeated",
	"reads_to_break": 8,
	"art": "res://Scripts/MattArtLayout.gd",
	"juggle_via": "clip",
	"drives_player": true,
}


# The yell case raises his yell chance, and a window's spot and bonus are only ever taken by the window.
static func reset(t) -> void:
	t.sm.yell_chance = 0.0
	t.sm.recover_spot = t.sm.HOME
	t.sm.recover_bonus = 0.0


# Every moment a read can Break him in play, and the Glass Row's booms, which only a forced Break
# reaches: the player is sealed through them and the booms never feed the gauge.
static func entry_cases(t) -> Array:
	var sm = t.sm
	var volley = sm.states["MysticVolley"]
	var barrage = sm.states["TrueshotBarrage"]
	var spent = sm.states["Spent"]
	var recover = sm.states["Recover"]
	var glass = sm.states["GlassRow"]
	# His first cast's teleport, a bolt already flying: whether a later cast finds a spot, and so teleports
	# while his own bolt is still out, is up to his rng and the player's corner.
	var teleport_with_a_bolt := func():
		t.spawn_matt_bolt(Vector2(960, 300), Vector2.from_angle(deg_to_rad(22.5)), false)
		sm.start_cycle()
	var spent_with_a_bolt := func():
		t.spawn_matt_bolt(Vector2(960, 300), Vector2.from_angle(deg_to_rad(22.5)), false)
		sm.on_child_transition(sm.current_state, "Spent")
	var yell_tell := func():
		sm.yell_chance = 1.0
		sm.windows_opened = sm.yell_from_window
		sm.on_child_transition(sm.current_state, "Recover")
		recover.on_punch_landed(recover.yell_on_hit)
	var glass_booms := func():
		sm.cycle_booms = 5
		sm.cycle_deafen = false
		sm.cycle_sets = 1
		sm.on_child_transition(sm.current_state, "GlassRow")
	return [
		["between two attacks", func(): sm.on_child_transition(sm.current_state, "Idle"), func(): return sm.current_state.name == "Idle"],
		["a Mystic cast's wind-up", func(): sm.start_cycle(), func(): return sm.current_state == volley and volley.beat == volley.Beat.WINDUP],
		["mid-teleport, a bolt in the air", teleport_with_a_bolt, func():
			return sm.current_state == volley and volley.beat in [volley.Beat.OUT, volley.Beat.IN] and not sm.live_bolts().is_empty()],
		["a Trueshot charging at a station", func(): sm.on_child_transition(sm.current_state, "TrueshotBarrage"), func():
			return sm.current_state == barrage and barrage.beat == barrage.Beat.CHARGE],
		["spent, a bolt still flying", spent_with_a_bolt, func():
			return sm.current_state == spent and spent.beat == spent.Beat.WAIT and not sm.live_bolts().is_empty()],
		["his window, the yell's tell up", yell_tell, func(): return sm.current_state == recover and recover.yell == recover.Yell.TELL],
		["the Glass Row, sealed in its booms (forced)", glass_booms, func():
			return sm.current_state == glass and glass.beat == glass.Beat.BOOMS and glass.boom != null and t.player.lock_seals_guard],
	]


static func extra(t) -> void:
	var boss = t.boss
	var sm = t.sm
	var gauge = boss.break_gauge
	var broken = sm.states["Broken"]
	var juggled = sm.states["Juggled"]

	t.log_p("-- a Break in the window at the Glass Row's station slides him down to his juggle floor (BossBroken)")
	var station: Vector2 = sm.GLASS_ROW.station
	sm.recover_spot = station
	sm.on_child_transition(sm.current_state, "Recover")
	boss.update_hud_fade(&"recover")
	await t.settle_player(sm.row_body_point(0))
	await t.wait(30)
	var faded: float = boss.health_bar.modulate.a
	var gauge_faded: float = boss.gauge_bar.modulate.a
	t.log_p("at the station %s: health bar alpha %.2f, gauge bar alpha %.2f" % [boss.global_position, faded, gauge_faded])
	t.check(boss.global_position == station and is_equal_approx(faded, sm.hud_fade_alpha) and is_equal_approx(gauge_faded, faded),
		"his window at the station fades the gauge bar with the health bar (%.2f, %.2f)" % [faded, gauge_faded])
	var trail := []
	var watch := func(): trail.append(snappedf(boss.global_position.y, 0.1))
	t.physics_frame.connect(watch)
	var floor_y: float = juggled.floor_y()
	gauge.add(gauge.max_value)
	var broke: bool = await t.wait_until(func(): return sm.current_state == broken, 30)
	var driven: bool = await t.wait_until(func(): return not t.player.is_action_locked, 120)
	await t.wait(2)
	t.physics_frame.disconnect(watch)
	var box: Rect2 = t.area_rect(boss.hurtbox)
	var stand_off: float = t.player.global_position.y + broken.PLAYER_FEET_OFFSET - broken.PLAYER_IN_FRONT - box.end.y
	t.log_p("floor y %.1f: feet %s -> %s, slid through y %s; the player driven to %s, %.1f px off his ground line" % [floor_y, broken.slide_from, broken.slide_to, trail, t.player.global_position, stand_off])
	t.check(broke and driven and broken.slide_from == station and broken.slide_to == Vector2(station.x, roundf(floor_y)) and boss.global_position == broken.slide_to,
		"his feet slide from y %.0f down to his floor, y %.0f, not the %.0f his standing rect stops at" % [station.y, roundf(floor_y), sm.STAND_RECT.position.y])
	t.check(absf(stand_off) <= 1.0, "and the player is driven in beside where he lands, on that ground line")
	var lift_scale: float = juggled.headroom() / t.player.finisher.planned_apex(3)
	t.check(lift_scale >= 0.49, "where a three-uppercut juggle is drawn at least half its height (%.2f)" % lift_scale)
	await t.wait(40)
	t.check(is_equal_approx(boss.health_bar.modulate.a, 1.0) and is_equal_approx(boss.gauge_bar.modulate.a, 1.0),
		"the Break brings both bars back up (%.2f, %.2f)" % [boss.health_bar.modulate.a, boss.gauge_bar.modulate.a])
	t.check(await t.swing() > 0, "and a punch reaches him there")

	t.log_p("-- one read a bolt, however often it comes back through the player")
	await t.reset_gauged(t.fight_spec.home)
	await t.settle_player(Vector2(500, 700))
	var bolt: Node2D = t.dummy_source()
	var results := []
	for pass_number in 2:
		t.press(KEY_SHIFT)
		await t.wait(3)
		results.append(t.front_hit(&"matt_mystic_shot", bolt))
		t.release(KEY_SHIFT)
		t.clear_iframes()
		t.defense._set_stamina(t.defense.max_stamina)
		# Past the per-source absorb, so the second pass is a parry of its own.
		await t.wait(80)
	var one_bolt: float = gauge.value
	results.append(await t.parry_once(&"matt_mystic_shot"))
	t.clear_iframes()
	await t.wait(40)
	var two_bolts: float = gauge.value
	t.log_p("the same bolt parried on two passes %s: %.3f; another bolt: %.3f" % [results.slice(0, 2), one_bolt, two_bolts])
	t.check(results == [3, 3, 3] and is_equal_approx(one_bolt, gauge.parry_gain), "parried on two passes, one bolt pays one read (%.3f)" % one_bolt)
	t.check(is_equal_approx(two_bolts, 2.0 * gauge.parry_gain), "and another bolt pays its own (%.3f)" % two_bolts)

	t.log_p("-- the juggle's frames are its own: a hit in the air never flinches him; the last uppercut shoves him")
	await t.reset_gauged(t.fight_spec.home)
	t.check(await t.break_into_prompt_fight(t.fight_spec), "a Break and the opener put up the prompt")
	var sheets := {}
	var look := func():
		if sm.current_state == juggled:
			sheets[boss.sprite.texture.resource_path.get_file()] = true
	t.physics_frame.connect(look)
	var finisher: Node = t.player.get_node("Finisher")
	var at_last := []
	var on_hit := func(_index: int, last: bool):
		if last:
			at_last.append([boss.global_position, t.player.global_position])
	finisher.juggle_hit.connect(on_hit)
	await t.mash_tiered(5)
	await t.wait_until(func(): return sm.current_state != juggled and not sheets.is_empty(), 600)
	t.physics_frame.disconnect(look)
	finisher.juggle_hit.disconnect(on_hit)
	t.log_p("sheets drawn while juggled: %s; now %s" % [sheets.keys(), sm.current_state.name])
	t.check(sheets.keys() == ["matt_juggle.png"], "only his juggle sheet, never his hit (%s)" % [sheets.keys()])
	var from: Vector2 = at_last[0][0] if not at_last.is_empty() else boss.global_position
	var player_x: float = at_last[0][1].x if not at_last.is_empty() else from.x
	var shove: Vector2 = boss.global_position - from
	t.log_p("the last uppercut: feet %s -> %s (%s), the player at x %.0f" % [from, boss.global_position, shove, player_x])
	t.check(absf(shove.x) > 0.0 and shove.y == 0.0 and signf(shove.x) == signf(from.x - player_x) and sm.STAND_RECT.has_point(boss.global_position),
		"shoves him along the floor away from the player, inside where he may stand (%s)" % [shove])
