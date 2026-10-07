extends RefCounted

# Carter's gauge spec for verify_defense.gd's gauge modes (juggle, juggle_kill and gauge_extra with
# fight=carter_akuma). The keys and the optional statics are listed over GAUGE_FIGHTS_DIR there.
# His Break window is not a state of its own: a Break ends the attack running and hands him to his
# Recover with from_break (CarterStateMachine.on_break, CarterRecover); only between attacks is one owed
# to the next hand-over. So break_gauge and break_entry don't apply to him (broken_state ""), and
# extra() covers his Breaks in each attack and the user's calibration instead: "if the player can parry
# 8 in a row, that should be enough to break carter ... getting hit lowers the break bar like all other
# scenarios", and "When Carter is broken during the 10+ clone attack, the attack should immediately stop
# and Carter should be hittable" (2026-09-27). The count is BREAK_READS, 14 since 2026-10-04, when the
# user made the Break his only finisher, 18 since 2026-10-05 with his attacks chained; every case here
# reads it rather than writing it down.

const SPEC := {
	"body": "Arena/CarterAkumaScene/CarterAkumaCharacterBody",
	# His scene's own spot: low enough in the ring for a whole juggle over him.
	"home": Vector2(959, 700),
	"light": &"carter_teleport_strike",
	"strong": &"",
	"foreign": &"eric_quake_wave_v2",
	"punish_state": "Recover",
	"broken_state": "",
	"cycle_states": ["RagingDemon", "BeamRush", "Messatsu"],
	"defeated_state": "Defeated",
	"reads_to_break": 18,
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
	t.track()
	await _calibration(t)
	await _demon_breaks(t)
	await t.reset_gauged(SPEC.home)
	await _feints(t)
	await t.reset_gauged(SPEC.home)
	await _messatsu_break(t)
	await t.reset_gauged(SPEC.home)
	await _rush_break(t)
	await t.reset_gauged(SPEC.home)
	await _drop(t)


# Straight through the player's own defence, one read at a time, the gauge's arithmetic and nothing
# else: no attack of his is running.
static func _calibration(t) -> void:
	var gauge: Node = t.boss.break_gauge
	var reads: int = t.boss.BREAK_READS
	var read: float = gauge.max_value / reads
	t.log_p("-- the user's calibration: %d reds in a row from empty break him, %d don't" % [reads, reads - 1])
	t.check(is_equal_approx(gauge.parry_gain, read) and is_equal_approx(gauge.hit_loss, read) and is_equal_approx(gauge.guard_break_loss, 2.0 * read), "a parry is one read of %.1f, a hit costs one and a guard break two (%.1f / %.1f / %.1f)" % [read, gauge.parry_gain, gauge.hit_loss, gauge.guard_break_loss])
	t.check(gauge.perfect_dodge_gain == 0.0 and gauge.punch_gain == 0.0 and gauge.charged_punch_gain == 0.0, "and a perfect dodge or a punch earns nothing")
	var short := await _parries(t, &"carter_clone_rush", reads - 1)
	t.check(is_equal_approx(gauge.value, (reads - 1) * read) and not t.sm.break_owed and not gauge.locked, "%d reds parried: %s, and no Break" % [reads - 1, short])
	await _parries(t, &"carter_clone_rush", 1)
	t.check(t.sm.break_owed and gauge.locked and gauge.value == 0.0, "red %d breaks him: owed, and the gauge empty and locked (%.1f)" % [reads, gauge.value])
	await _parries(t, &"carter_clone_rush", 1)
	t.check(gauge.value == 0.0 and gauge.locked, "a red parried with the Break owed changes nothing (%.1f)" % gauge.value)

	_clear(t)
	var half: int = reads / 2
	t.log_p("-- a hit between costs a read: %d parries around it don't break him, one more does" % reads)
	await _parries(t, &"carter_clone_rush", half)
	# Past the last press's window: with blocking off a tap's stance lasts all of it, let go or not, and a hit
	# inside it would be parried rather than land.
	await t.past_window()
	t.clear_iframes()
	t.omni_hit(&"carter_clone_rush", t.dummy_source())
	var after_hit: float = gauge.value
	await _parries(t, &"carter_clone_rush", reads - half)
	t.check(is_equal_approx(after_hit, (half - 1) * read) and is_equal_approx(gauge.value, (reads - 1) * read) and not t.sm.break_owed, "%d, a hit, %d: %.1f after the hit and %.1f after all %d, no Break" % [half, reads - half, after_hit, gauge.value, reads])
	await _parries(t, &"carter_clone_rush", 1)
	t.check(t.sm.break_owed, "and one more breaks him")

	_clear(t)
	t.log_p("-- the rest of what drains and what doesn't")
	await _parries(t, &"carter_clone_rush", 6)
	var before: float = gauge.value
	await t.past_window()
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
	await _parries(t, &"eric_quake_wave_v2", 1)
	t.omni_hit(&"eric_quake_wave_v2", t.dummy_source())
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
	var string: int = t.sm.messatsu_hits
	var messatsu := await _parries(t, &"carter_messatsu_beam", string)
	t.check(string < reads and is_equal_approx(gauge.value, string * read) and not t.sm.break_owed, "a perfect Messatsu's %d parries fill %.1f and can't break him from empty (%s)" % [string, string * read, messatsu])
	_clear(t)


# "When Carter is broken during the 10+ clone attack, the attack should immediately stop and Carter
# should be hittable." A real barrage, every clone red, broken three ways: on its first red with all but
# one read carried in, on its BREAK_READS-th red from empty - the user's reads in a row - and on its last
# clone with all but one carried in. Each time the barrage is over within two frames of the parry and no clone reaches
# the player after it; the player is let go and the lights come up; and he is open in his Break's
# window, level with the player in the middle, clear of the HUD, banked the reds he got to throw -
# where the player's punches land and then the tiered uppercut's juggle.
static func _demon_breaks(t) -> void:
	var gauge: Node = t.boss.break_gauge
	var demon: Node = t.sm.states["RagingDemon"]
	var art: GDScript = load(SPEC.art)
	var reads: int = t.boss.BREAK_READS
	var read: float = gauge.max_value / reads
	var last: int = t.sm.clone_count - 1
	var body_box: Rect2 = art.local_rect(art.RECOVER_BODY_BOX)
	# How it is broken; the clone that breaks him; the first the player parries, and the reads carried
	# in as it comes; and what the window banks (CarterRecover.banked_damage): one for every
	# bank_per_parries reds parried, and the bonus for a barrage perfect as far as he got.
	var bank := func(parried: int, perfect: bool) -> int: return parried / t.sm.bank_per_parries + (t.sm.bank_perfect_bonus if perfect else 0)
	for case in [["on its first red, %d reads carried in" % (reads - 1), 0, 0, reads - 1, bank.call(1, true)],
			["on red %d, from empty" % reads, reads - 1, 0, 0, bank.call(reads, true)],
			["on its last clone, %d reads carried in" % (reads - 1), last, last, reads - 1, bank.call(1, false)]]:
		t.log_p("-- a barrage broken %s" % case[0])
		await t.reset_gauged(SPEC.home)
		_clear(t)
		var at: int = case[1]
		var first: int = case[2]
		t.sm.cycles_started = 0
		t.sm.start_cycle()
		t.check(t.sm.current_state == demon and demon.feints.count(true) == 0, "the first barrage, every clone red")
		var watch: Dictionary = _watch_break(t, demon)
		for k in range(first, at + 1):
			if k == first:
				if not await t.wait_until(func(): return demon.clone_index == k, 900):
					break
				gauge.value = case[3] * read
			if not await _parry_clone(t, demon, k):
				break
		await t.wait(2)
		var recover: Node = t.sm.current_state
		var feet: Vector2 = t.boss.global_position
		var gap: float = absf(feet.x - t.player.global_position.x)
		var lift: float = t.boss.juggle_headroom() / t.player.finisher.planned_apex(3)
		var banked: int = t.boss.get_max_health() - t.boss.boss_health
		t.log_p("%d reds parried, broken on clone %d, the barrage over %d frame(s) after it; %s from_break %s, window %.2f s, banked %d; his feet %s, %.0f px from the player, lift scale %.2f" % [demon.reds_parried, demon.clone_index + 1, watch.ended - watch.broke, recover.name, recover.get("from_break"), t.sm.recover_timer.wait_time, banked, feet, gap, lift])
		t.check(watch.broke >= 0 and demon.clone_index == at, "his gauge broke on clone %d (%d)" % [at + 1, demon.clone_index + 1])
		t.check(watch.ended >= 0 and watch.ended - watch.broke <= 2, "the barrage is over within two frames of the parry that broke him (%d)" % (watch.ended - watch.broke))
		t.check(t.get_nodes_in_group(t.sm.HAZARD_GROUP).is_empty() and demon.clone == null, "not a clone left out")
		t.check(recover.name == "Recover" and recover.from_break and t.boss.can_be_juggled() and t.sm.recover_timer.wait_time >= t.boss.BREAK.broken_time - 0.001, "straight into his Break's window, which pays the tiered finisher")
		t.check(t.boss.sprite.visible and t.boss.hurtbox.monitoring, "him drawn, and hittable")
		t.check(not t.player.is_action_locked and t.player.get_parent().z_index == 0, "the player let go and back under the ropes")
		t.check(banked == case[4], "the reds he got to throw banked: %d (%d)" % [case[4], banked])
		t.check(feet.y == t.sm.ARENA_CENTRE.y and gap >= t.sm.BREAK_PLAYER_GAP and lift >= 0.49, "level with the player in the middle, a clear gap from them, where a full juggle fits (y %.0f, %.0f px, lift %.2f)" % [feet.y, gap, lift])
		t.check(art.clear_of_hud(Rect2(feet + body_box.position, body_box.size)), "and nothing of him near the HUD")
		t.check(await t.wait_until(func(): return not t.boss.dark_stage.visible, 120), "the lights come all the way up")
		await _punch_and_juggle(t)
		var after: Array = t.events_of("HIT").filter(func(e): return e.t > watch.broke_t and (e.id == &"carter_clone_rush" or e.id == &"carter_clone_punish"))
		t.check(after.is_empty(), "and no clone reached the player after the Break (%d)" % after.size())
		watch.stop.call()


# The same in the Messatsu, where only a parried hit reads: with all but one carried in, the first one
# breaks him. The string is over within two frames and no hit of it lands after; the beam, its surges and its
# badge go with it and the music comes back up; and he is open in his Break's window where he fired
# from, where a punch lands.
static func _messatsu_break(t) -> void:
	t.log_p("-- a Messatsu broken on its first hit, all but one read carried in")
	var gauge: Node = t.boss.break_gauge
	var m: Node = t.sm.states["Messatsu"]
	var art: GDScript = load(SPEC.art)
	var read: float = gauge.max_value / t.boss.BREAK_READS
	var spot: Vector2 = t.MESSATSU_CARTER_SPOT
	await t.settle_player(t.MESSATSU_PLAYER_SPOT)
	_clear(t)
	gauge.value = (t.boss.BREAK_READS - 1) * read
	t.check(await t.start_messatsu(m, spot), "a Messatsu with %.1f in the gauge" % gauge.value)
	var watch: Dictionary = _watch_break(t, m)
	var at: float = t.sm.messatsu_hit_time(0) - 0.10
	var firing: bool = await t.wait_until(func(): return m.beat == m.Beat.STRING and m.tick_index == 0 and m.fire_clock >= at, 600)
	t.press(KEY_SHIFT)
	await t.wait_until(func(): return t.sm.current_state != m, 60)
	t.release(KEY_SHIFT)
	await t.wait(2)
	var feet: Vector2 = t.boss.global_position
	var recover: Node = t.sm.current_state
	t.log_p("parried %d, the string over %d frame(s) after the Break; %s from_break %s, window %.2f s, banked %d; his feet %s, fired from %s" % [m.parried, watch.ended - watch.broke, recover.name, recover.get("from_break"), t.sm.recover_timer.wait_time, t.boss.get_max_health() - t.boss.boss_health, feet, spot])
	t.check(firing and watch.broke >= 0 and m.parried == 1, "the first hit parried broke him")
	t.check(watch.ended >= 0 and watch.ended - watch.broke <= 2, "and the string is over within two frames (%d)" % (watch.ended - watch.broke))
	# The parry's own shatter plays out on the mat for a moment (CarterAkumaScript.spawn_burst); what
	# must be gone is the string.
	var pieces: Array = [m.beam_root, m.flare, m.head, m.ball, m.eyes, m.aim_line, m.lock_ring, m.source_holder]
	t.check(pieces.all(func(n): return not is_instance_valid(n)) and m.surges.is_empty() and t.live_tells().is_empty(), "the beam, its surges and its badge gone")
	t.check(recover.name == "Recover" and recover.from_break and t.boss.can_be_juggled() and t.sm.recover_timer.wait_time >= t.boss.BREAK.broken_time - 0.001, "straight into his Break's window, which pays the tiered finisher")
	t.check(t.boss.hurtbox.monitoring and feet.y == spot.y and absf(feet.x - spot.x) <= art.MESSATSU_RECOIL * art.SCALE + 0.5, "hittable where he fired from, the fire's recoil and no more")
	t.check(await t.wait_until(func(): return is_equal_approx(t.boss.music_player.volume_db, t.boss.music_base_db), 120), "the music comes back up")
	t.place_under(t.boss.get_finisher_hurtbox())
	await t.wait(6)
	var dealt: int = await t.swing()
	t.check(dealt > 0, "a punch lands (%d)" % dealt)
	# Past where the rest of the string would have landed.
	await t.wait(roundi(t.sm.messatsu_hit_time(t.sm.messatsu_hits - 1) * 60.0))
	var after: Array = t.events_of("HIT", &"carter_messatsu_beam").filter(func(e): return e.t > watch.broke_t)
	t.check(after.is_empty(), "and no hit of the string landed after the Break (%d)" % after.size())
	watch.stop.call()
	_idle(t)


# Up to him, as a player would come in: three punches, the finisher's prompt, and the tiered uppercut
# mashed through all three bars - the juggle - until he is down.
static func _punch_and_juggle(t) -> void:
	var finisher: Node = t.player.get_node("Finisher")
	t.place_under(t.boss.get_finisher_hurtbox())
	await t.wait(6)
	var dealt: Array = []
	for i in 3:
		dealt.append(await t.swing())
		if i < 2:
			await t.wait(6)
	t.check(dealt.size() == 3 and dealt.all(func(d): return d > 0), "the player's punches land (%s)" % [dealt])
	var prompted: bool = await t.wait_until(func(): return finisher.phase == t.FINISHER_DAZED and finisher.prompt_visible, 120)
	t.check(prompted and finisher.tiered, "the finisher's prompt comes up, the tiered one")
	var uppercuts: Array = []
	var count := func(index: int, _last: bool) -> void: uppercuts.append(index)
	finisher.juggle_hit.connect(count)
	var before: int = t.boss.boss_health
	await t.mash_tiered(5)
	await t.wait_until(func(): return t.sm.current_state.name != "Juggled" and not uppercuts.is_empty(), 600)
	finisher.juggle_hit.disconnect(count)
	t.check(uppercuts.size() == 3 and before > t.boss.boss_health, "and the uppercut lands: the juggle's three, for %d" % (before - t.boss.boss_health))


# The physics frame his gauge broke on, the first he was out of `attack` on and the defence clock at the
# Break; `stop` ends the watch.
static func _watch_break(t, attack: Node) -> Dictionary:
	var gauge: Node = t.boss.break_gauge
	var seen := {"broke": -1, "ended": -1, "broke_t": INF}
	var on_broke := func() -> void:
		if seen.broke < 0:
			seen.broke = Engine.get_physics_frames()
			seen.broke_t = t.defense.clock
	var on_frame := func() -> void:
		if seen.broke >= 0 and seen.ended < 0 and t.sm.current_state != attack:
			seen.ended = Engine.get_physics_frames()
	gauge.broke.connect(on_broke)
	t.physics_frame.connect(on_frame)
	seen["stop"] = func() -> void:
		gauge.broke.disconnect(on_broke)
		t.physics_frame.disconnect(on_frame)
	return seen


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
	await t.wait_until(func(): return t.sm.current_state != demon, 240)


# A Beam Rush against a gauge that comes in all but full: all but one read carried in from the attacks
# before it. Its beams can't be parried, so a press as they land answers nothing and the hit only costs a read.
# Its one read is his strike, and that parry breaks him and ends the attack within two frames, with
# nothing of it left, into his Break's window where the strike left him - where a punch lands.
static func _rush_break(t) -> void:
	var gauge: Node = t.boss.break_gauge
	var rush: Node = t.sm.states["BeamRush"]
	var read: float = gauge.max_value / t.boss.BREAK_READS
	var parried: Array = []
	t.defense.parried.connect(func(hit, _at, _staggered, _streak): parried.append(hit.attack_id))

	var reads: int = t.boss.BREAK_READS
	t.log_p("-- all but one read carried in, and a press as a volley's beams land, standing in them")
	_idle(t)
	await t.settle_player(SPEC.home + Vector2(0, 120))
	_clear(t)
	t.player.playerHealth = 1000
	gauge.value = (reads - 1) * read
	# His strike out of the way, in the last charge.
	t.check(await t.start_beam_rush(rush, 2, 0.3), "a Beam Rush with %.1f in the gauge" % gauge.value)
	var pressed: bool = await t.press_at_beam_rush_landing(rush, 0)
	await t.wait(1)
	t.check(pressed and parried.is_empty(), "the press parries nothing")
	t.check(is_equal_approx(gauge.value, (reads - 2) * read) and not rush.broke and t.sm.current_state == rush, "and the hit costs a read, with no Break and the attack running on (%.1f)" % gauge.value)

	t.log_p("-- all but one read carried in, and his strike parried")
	_idle(t)
	await t.settle_player(SPEC.home + Vector2(0, 120))
	_clear(t)
	gauge.value = (reads - 1) * read
	t.check(await t.start_beam_rush(rush, 0, 0.3), "a Beam Rush with %.1f in the gauge, his strike in the first charge" % gauge.value)
	var watch: Dictionary = _watch_break(t, rush)
	var answered: bool = await t.parry_beam_rush_strike(rush)
	await t.wait(1)
	var feet: Vector2 = t.boss.global_position
	var beside: float = absf(feet.x - t.player.global_position.x)
	t.log_p("the attack over %d frame(s) after the Break, in %s; his feet %s, %.0f px from the player" % [watch.ended - watch.broke, t.sm.current_state.name, feet, beside])
	t.check(answered and parried == [&"carter_teleport_strike"], "his strike, parried")
	t.check(rush.broke and watch.ended >= 0 and watch.ended - watch.broke <= 2, "breaks him, and the attack is over within two frames (%d)" % (watch.ended - watch.broke))
	t.check(gauge.locked and gauge.value == 0.0 and not t.sm.break_owed, "the gauge empty and locked, and nothing owed: this attack cashes its own Break")
	t.check(rush.casters.is_empty() and t.get_nodes_in_group(t.sm.HAZARD_GROUP).is_empty() and t.live_tells().is_empty(), "nothing of it left: no clone, beam, line, ring or badge")
	t.check(t.sm.current_state.name == "Recover" and t.sm.current_state.from_break and t.boss.can_be_juggled() and t.sm.recover_timer.wait_time >= t.boss.BREAK.broken_time - 0.001, "straight into his Break's window, %.2f s, which pays the tiered finisher" % t.sm.recover_timer.wait_time)
	t.check(t.boss.hurtbox.monitoring and beside <= rush.LUNGE_STANDOFF + 1.0, "hittable where the strike left him, beside the player")
	t.place_under(t.boss.get_finisher_hurtbox())
	await t.wait(6)
	var dealt: int = await t.swing()
	t.check(dealt > 0, "and a punch lands (%d)" % dealt)
	watch.stop.call()
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
