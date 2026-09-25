extends RefCounted

# Carter's gauge spec for verify_defense.gd's gauge modes (juggle, juggle_kill and gauge_extra with
# fight=carter_akuma). The keys and the optional statics are listed over GAUGE_FIGHTS_DIR there.
# His Break window is not a state of its own: a Break is owed in the middle of an attack and cashed
# when it hands over, as his Recover with from_break (CarterStateMachine.on_break, CarterRecover). So
# break_gauge and break_entry don't apply to him (broken_state ""), and extra() covers his banked
# Break and the user's calibration instead: "if the player can parry 8 in a row, that should be enough
# to break carter ... getting hit lowers the break bar like all other scenarios".

const SPEC := {
	"body": "Arena/CarterAkumaScene/CarterAkumaCharacterBody",
	# His scene's own spot: low enough in the ring for a whole juggle over him.
	"home": Vector2(959, 700),
	"light": &"carter_teleport_strike",
	"strong": &"",
	"foreign": &"josh_card_throw",
	"punish_state": "Recover",
	"broken_state": "",
	"cycle_states": ["RagingDemon", "BeamRush", "Messatsu"],
	"defeated_state": "Defeated",
	"reads_to_break": 8,
	"art": "res://Scripts/CarterArtLayout.gd",
	"juggle_via": "clip",
	"drives_player": false,
}


# His feet, as a Break window stands him: he has no Broken state to ask.
static func break_feet(t) -> Vector2:
	return t.boss.global_position


# The Break the real way - his gauge filled, which owes it - and then cashed the way an attack's
# hand-over cashes it.
static func force_break(t) -> void:
	var gauge: Node = t.boss.break_gauge
	gauge.add(gauge.max_value)
	await t.wait_until(func(): return t.sm.break_owed, 10)
	var recover: Node = t.sm.states["Recover"]
	recover.prepare(0, 0, 0, 0, -1.0, t.sm.take_break_owed())
	t.sm.on_child_transition(t.sm.current_state, "Recover")


static func reset(t) -> void:
	t.sm.break_owed = false


static func extra(t) -> void:
	await _calibration(t)
	await _banked_break(t)
	await t.reset_gauged(SPEC.home)
	await _feints(t)
	await t.reset_gauged(SPEC.home)
	await _rush_break(t)
	await t.reset_gauged(SPEC.home)
	await _drop(t)


# Straight through the player's own defence, one read at a time, the gauge's arithmetic and nothing
# else: no attack of his is running.
static func _calibration(t) -> void:
	var gauge: Node = t.boss.break_gauge
	var read: float = gauge.max_value / t.boss.BREAK_READS
	t.log_p("-- the user's calibration: eight reds in a row from empty break him, seven don't")
	t.check(is_equal_approx(gauge.parry_gain, read) and is_equal_approx(gauge.hit_loss, read) and is_equal_approx(gauge.guard_break_loss, 2.0 * read), "a parry is one read of %.1f, a hit costs one and a guard break two (%.1f / %.1f / %.1f)" % [read, gauge.parry_gain, gauge.hit_loss, gauge.guard_break_loss])
	t.check(gauge.perfect_dodge_gain == 0.0 and gauge.punch_gain == 0.0 and gauge.charged_punch_gain == 0.0, "and a perfect dodge or a punch earns nothing")
	var seven := await _parries(t, &"carter_clone_rush", 7)
	t.check(is_equal_approx(gauge.value, 7.0 * read) and not t.sm.break_owed and not gauge.locked, "seven reds parried: %s, and no Break" % [seven])
	await _parries(t, &"carter_clone_rush", 1)
	t.check(t.sm.break_owed and gauge.locked and gauge.value == 0.0, "the eighth breaks him: owed, and the gauge empty and locked (%.1f)" % gauge.value)
	await _parries(t, &"carter_clone_rush", 1)
	t.check(gauge.value == 0.0 and gauge.locked, "a red parried with the Break owed changes nothing (%.1f)" % gauge.value)

	_clear(t)
	t.log_p("-- a hit between costs a read: eight parries around it don't break him, a ninth does")
	await _parries(t, &"carter_clone_rush", 4)
	t.clear_iframes()
	t.omni_hit(&"carter_clone_rush", t.dummy_source())
	var after_hit: float = gauge.value
	await _parries(t, &"carter_clone_rush", 4)
	t.check(is_equal_approx(after_hit, 3.0 * read) and is_equal_approx(gauge.value, 7.0 * read) and not t.sm.break_owed, "four, a hit, four: %.1f after the hit and %.1f after all eight, no Break" % [after_hit, gauge.value])
	await _parries(t, &"carter_clone_rush", 1)
	t.check(t.sm.break_owed, "and the ninth breaks him")

	_clear(t)
	t.log_p("-- the rest of what drains and what doesn't")
	await _parries(t, &"carter_clone_rush", 6)
	var before: float = gauge.value
	t.clear_iframes()
	t.omni_hit(&"carter_clone_punish", t.dummy_source())
	var punished: float = gauge.value
	t.clear_iframes()
	t.omni_hit(&"carter_messatsu_beam", t.dummy_source())
	var messatsu_hit: float = gauge.value
	t.clear_iframes()
	t.omni_hit(&"carter_rush_beam", t.dummy_source())
	var beamed: float = gauge.value
	t.check(is_equal_approx(before - punished, read) and is_equal_approx(punished - messatsu_hit, read) and is_equal_approx(messatsu_hit - beamed, read), "a feint's punish clone costs a read, and so do a Messatsu hit and a Beam Rush beam (%.1f -> %.1f -> %.1f -> %.1f)" % [before, punished, messatsu_hit, beamed])
	t.clear_iframes()
	await _parries(t, &"josh_card_throw", 1)
	t.omni_hit(&"josh_card_throw", t.dummy_source())
	t.check(is_equal_approx(gauge.value, beamed), "someone else's attack, parried or landed, moves nothing (%.1f)" % gauge.value)
	t.clear_iframes()
	t.defense._set_stamina(t.defense.max_stamina)
	t.press(KEY_SHIFT)
	await t.wait(3)
	t.defense.drain_stamina(t.defense.max_stamina)
	await t.wait(2)
	t.release(KEY_SHIFT)
	t.check(t.defense.is_guard_broken and is_equal_approx(gauge.value, beamed - 2.0 * read), "a guard break costs two reads (%.1f -> %.1f)" % [beamed, gauge.value])
	t.defense.clear_guard_break()
	await t.wait(4)

	_clear(t)
	var messatsu := await _parries(t, &"carter_messatsu_beam", 6)
	t.check(is_equal_approx(gauge.value, 75.0) and not t.sm.break_owed, "a perfect Messatsu's six parries fill 75 and can't break him from empty (%s)" % [messatsu])
	_clear(t)


# A real barrage, all red: eight parried from empty owe the Break with seven clones still to come.
# The string plays on to its end with the gauge empty and locked, and when the lights come up the
# window it cashes is the tiered one, at least BREAK.broken_time long, level with the player in the
# middle and a clear gap from them.
static func _banked_break(t) -> void:
	t.log_p("-- a barrage: the eighth red banks the Break, and the lights come up on its window")
	var gauge: Node = t.boss.break_gauge
	var demon: Node = t.sm.states["RagingDemon"]
	t.player.playerHealth = 1000
	t.sm.cycles_started = 0
	t.sm.start_cycle()
	t.check(t.sm.current_state == demon and demon.feints.count(true) == 0, "the first barrage, every clone red")
	var owed_at := -1
	var while_owed := []
	for k in demon.feints.size():
		if not await _parry_clone(t, demon, k):
			break
		if owed_at < 0 and t.sm.break_owed:
			owed_at = k + 1
			t.check(t.sm.current_state == demon and gauge.locked and gauge.value == 0.0 and t.boss.break_sting_player.playing, "the Break is owed on red %d: the string carries on, the gauge is empty and locked and the sting plays" % owed_at)
		elif owed_at > 0:
			while_owed.append(gauge.value)
	t.log_p("reds parried %d, the Break owed on red %d, the gauge after each later one %s" % [demon.reds_parried, owed_at, while_owed])
	t.check(owed_at == 8, "on the eighth red, not before (%d)" % owed_at)
	t.check(not while_owed.is_empty() and while_owed.all(func(v): return v == 0.0), "and the reds after it move nothing")
	t.check(await t.wait_until(func(): return t.sm.current_state.name == "Recover", 240), "the lights come up on his window")
	var recover: Node = t.sm.current_state
	await t.wait(2)
	var juggled: Node = t.sm.states["Juggled"]
	var feet: Vector2 = t.boss.global_position
	var gap: float = absf(feet.x - t.player.global_position.x)
	var lift: float = t.boss.juggle_headroom() / t.player.finisher.planned_apex(3)
	t.log_p("window %.2f s, from_break %s, his feet %s (floor %.1f), %.0f px from the player, lift scale %.2f" % [t.sm.recover_timer.wait_time, recover.from_break, feet, juggled.floor_y(), gap, lift])
	t.check(recover.from_break and not t.sm.break_owed and t.boss.can_be_juggled(), "it cashes the Break: the tiered finisher's window")
	t.check(t.sm.recover_timer.wait_time >= t.boss.BREAK.broken_time - 0.001, "at least %.1f s long (%.2f s)" % [t.boss.BREAK.broken_time, t.sm.recover_timer.wait_time])
	t.check(feet.y == t.sm.ARENA_CENTRE.y and feet.y >= juggled.floor_y() and lift >= 0.49, "level with the middle of the ring, where a full juggle fits (y %.0f, lift %.2f)" % [feet.y, lift])
	t.check(gap >= t.sm.BREAK_PLAYER_GAP, "a clear gap from the player (%.0f px)" % gap)


# A real barrage with two feints dealt into it by hand: one mid-string, bitten, whose punish clone is
# the read it costs, and one in the last slot, bitten, which has no clone after it and costs its read
# as it is bitten.
static func _feints(t) -> void:
	t.log_p("-- a bitten feint costs a read, in the last slot too")
	var gauge: Node = t.boss.break_gauge
	var demon: Node = t.sm.states["RagingDemon"]
	var read: float = gauge.max_value / t.boss.BREAK_READS
	var mid := 5
	var last: int = t.sm.clone_count - 1
	t.player.playerHealth = 1000
	t.sm.cycles_started = 0
	t.sm.start_cycle()
	demon.feints[mid] = true
	demon.feints[last] = true
	var bites := {}
	for k in [mid, mid + 1, last]:
		if not await t.wait_until(func(): return demon.clone_index == k and demon.clone_clock > 0.05, 900):
			break
		t.clear_iframes()
		t.defense._set_stamina(t.defense.max_stamina)
		gauge.locked = false
		gauge.value = 50.0
		if k == mid + 1:
			t.check(demon.clone_is_punish, "the clone after the bitten feint comes in as a punish")
			await t.wait_until(func(): return demon.clone_struck, 60)
			await t.wait(2)
			bites[k] = gauge.value
			continue
		t.press(KEY_SHIFT)
		await t.wait(3)
		t.release(KEY_SHIFT)
		await t.wait(2)
		bites[k] = gauge.value
	t.log_p("the gauge from 50: after the mid feint's bite %s, after its punish clone %s, after the last feint's bite %s" % [bites.get(mid), bites.get(mid + 1), bites.get(last)])
	t.check(demon.feints_parried == 2 and is_equal_approx(bites.get(mid, -1.0), 50.0), "biting a feint mid-string costs nothing yet")
	t.check(is_equal_approx(bites.get(mid + 1, -1.0), 50.0 - read), "its punish clone lands, and costs the read")
	t.check(is_equal_approx(bites.get(last, -1.0), 50.0 - read), "a bitten feint in the last slot, with no clone to follow it, costs the read as it is bitten")
	await t.wait_until(func(): return t.sm.current_state.name == "Recover", 240)


# A Beam Rush against a gauge that comes in all but full: seven reads carried in from the attacks before
# it. Its beams can't be parried, so a press as they land answers nothing and the hit only costs a read.
# Its one read is his strike, and that parry breaks him and ends the attack on the spot, where the Demon
# and the Messatsu bank a Break: both badges come down, the lines and the ring go and the four dissolve,
# then the Break's window.
static func _rush_break(t) -> void:
	var gauge: Node = t.boss.break_gauge
	var rush: Node = t.sm.states["BeamRush"]
	var read: float = gauge.max_value / t.boss.BREAK_READS
	var parried: Array = []
	t.defense.parried.connect(func(hit, _at, _staggered, _streak): parried.append(hit.attack_id))

	t.log_p("-- seven reads carried in, and a press as a volley's beams land, standing in them")
	_idle(t)
	await t.settle_player(SPEC.home + Vector2(0, 120))
	_clear(t)
	t.player.playerHealth = 1000
	gauge.value = 7.0 * read
	# His strike out of the way, in the last charge.
	t.check(await t.start_beam_rush(rush, 2, 0.3), "a Beam Rush with %.1f in the gauge" % gauge.value)
	var pressed: bool = await t.press_at_beam_rush_landing(rush, 0)
	await t.wait(1)
	t.check(pressed and parried.is_empty(), "the press parries nothing")
	t.check(is_equal_approx(gauge.value, 6.0 * read) and not rush.broke and t.sm.current_state == rush, "and the hit costs a read, with no Break and the attack running on (%.1f)" % gauge.value)

	t.log_p("-- seven reads carried in, and his strike parried")
	_idle(t)
	await t.settle_player(SPEC.home + Vector2(0, 120))
	_clear(t)
	gauge.value = 7.0 * read
	t.check(await t.start_beam_rush(rush, 0, 0.3), "a Beam Rush with %.1f in the gauge, his strike in the first charge" % gauge.value)
	var answered: bool = await t.parry_beam_rush_strike(rush)
	await t.wait(1)
	var up: bool = rush.lock_ring.visible or rush.casters.any(func(c): return c.ball.visible or c.aim_line.visible)
	t.check(answered and parried == [&"carter_teleport_strike"], "his strike, parried")
	t.check(rush.broke and rush.beat == rush.Beat.END, "breaks him and ends the attack at once (%s)" % rush.Beat.keys()[rush.beat])
	t.check(gauge.locked and gauge.value == 0.0 and not t.sm.break_owed, "the gauge empty and locked, and nothing banked: this attack cashes its own Break")
	t.check(not up and t.messatsu_badge() == null, "no line, ball, ring or badge left up")
	t.check(await t.wait_until(func(): return t.sm.current_state.name == "Recover", 120), "into his window")
	t.check(t.sm.current_state.from_break and t.boss.can_be_juggled() and t.sm.recover_timer.wait_time >= t.boss.BREAK.broken_time - 0.001, "a Break's window, %.2f s, which pays the tiered finisher" % t.sm.recover_timer.wait_time)
	t.check(t.get_nodes_in_group(t.sm.HAZARD_GROUP).is_empty(), "and nothing left on the mat")
	_idle(t)


# A Break cashed with his feet above the line a full juggle needs, as a Beam Rush broken beside a
# player up by the top rope leaves him: he vanishes and comes back on it, a clear gap from the player,
# and the window opens then. One cashed below the line opens where he stands.
static func _drop(t) -> void:
	t.log_p("-- a Break window high in the ring comes down to the juggle's floor")
	var recover: Node = t.sm.states["Recover"]
	var juggled: Node = t.sm.states["Juggled"]
	var line: float = ceilf(juggled.floor_y())
	await t.settle_player(Vector2(1250, 320))
	t.boss.global_position = Vector2(1320, 300)
	recover.prepare(0, 0, 0, 0, -1.0, true)
	t.sm.on_child_transition(t.sm.current_state, "Recover")
	await t.wait(2)
	t.check(recover.dropping and not t.boss.hurtbox.monitoring, "he goes, and can't be hit while he does")
	t.check(await t.wait_until(func(): return not recover.dropping, 90), "and comes back")
	await t.wait(2)
	var feet: Vector2 = t.boss.global_position
	var bounds: Rect2 = t.sm.ROPES.grow(-t.sm.BREAK_ROPE_MARGIN)
	var gap: float = absf(feet.x - t.player.global_position.x)
	var lift: float = t.boss.juggle_headroom() / t.player.finisher.planned_apex(3)
	t.log_p("from (1320, 300) to %s: floor %.0f, %.0f px from the player, lift scale %.2f, window %.2f s" % [feet, line, gap, lift, t.sm.recover_timer.wait_time])
	t.check(feet.y == line and lift >= 0.49, "on the juggle's floor (y %.0f, lift %.2f)" % [feet.y, lift])
	t.check(gap >= t.sm.BREAK_PLAYER_GAP and bounds.has_point(feet), "a clear gap from the player and inside the ropes (%.0f px)" % gap)
	t.check(t.boss.hurtbox.monitoring and t.sm.recover_timer.wait_time >= t.boss.BREAK.broken_time - 0.001 and not t.sm.recover_timer.is_stopped(), "then his window opens, the whole of it")

	_idle(t)
	t.boss.global_position = SPEC.home
	await t.wait(2)
	recover.prepare(0, 0, 0, 0, -1.0, true)
	t.sm.on_child_transition(t.sm.current_state, "Recover")
	await t.wait(2)
	t.check(not recover.dropping and t.boss.global_position == SPEC.home, "one below the line opens where he stands")
	_idle(t)


# Idle, with his next attack held off: entering Idle starts the beat to it.
static func _idle(t) -> void:
	t.sm.on_child_transition(t.sm.current_state, "Idle")
	t.stop_boss_timers()


# `count` fresh parries of `id`, and the gauge after each.
static func _parries(t, id: StringName, count: int) -> Array:
	var values := []
	for i in count:
		await t.parry_once(id)
		await t.wait(1)
		values.append(t.boss.break_gauge.value)
	return values


# The press a player makes for a red in a real barrage: inside the parry window, a few frames before
# the clone lands, held through the contact.
static func _parry_clone(t, demon: Node, k: int) -> bool:
	var contact: float = t.sm.clone_show + t.sm.clone_dash
	if not await t.wait_until(func(): return demon.clone_index == k and demon.clone_clock >= contact - 0.1, 900):
		return false
	t.press(KEY_SHIFT)
	await t.wait_until(func(): return demon.clone_index > k or demon.clone_struck, 60)
	t.release(KEY_SHIFT)
	await t.wait(2)
	return true


# An empty open gauge and a fresh player: full stamina, no guard break, and no whiffed press still
# locking the next one out (PlayerDefense.parry_mash_lockout).
static func _clear(t) -> void:
	var gauge: Node = t.boss.break_gauge
	t.sm.break_owed = false
	gauge.locked = false
	gauge.value = 0.0
	t.clear_iframes()
	if t.defense.is_guard_broken:
		t.defense.clear_guard_break()
	t.defense._set_stamina(t.defense.max_stamina)
	t.defense.rearm_parry()
