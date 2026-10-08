extends RefCounted

# Liam's own phase's gauge spec for verify_defense.gd's gauge modes (break_gauge, break_entry, juggle, juggle_kill and
# gauge_extra with fight=liam_elements), on his test scene (LiamTestFightScene: the takeover's end state). The keys and
# the optional statics are listed over GAUGE_FIGHTS_DIR there.
# His gauge is on the rollout's rule, 8 clean reads from empty (LiamScript.BREAK): only his tsunami's and his lunge's
# parries and perfect dodges are reads; his tremor ridges, fire rings and tornados drain it but never fill it, and the
# impale's burns cost nothing. The shared modes play on the mat: he is
# parked at LAND_SPOT with his pillar gone, where his fall puts him, so a Break there is his Broken at once; a Break
# earned while he is up on his pillar is banked for his fall, which extra() covers.

const SPEC := {
	"body": "Arena/LiamScene/LiamCharacterBody",
	# LAND_SPOT: below his juggle floor, with the ring round him for the player and room over his head.
	"home": Vector2(960, 480),
	"light": &"liam_tsunami",
	"strong": &"",
	"foreign": &"eric_quake_wave_v2",
	"punish_state": "Downed",
	"broken_state": "Broken",
	"cycle_states": ["GetUp", "Tsunami", "Tremors", "Firestorm", "Lunge"],
	"defeated_state": "Defeated",
	"reads_to_break": 8,
	"art": "res://Scripts/LiamArtLayout.gd",
	"juggle_via": "clip",
	"drives_player": true,
}

const HitInfo := preload("res://Scripts/HitInfo.gd")


# On the mat at `home`, his pillar gone and nothing coming: where his fall leaves him.
static func park(t, home: Vector2) -> void:
	var boss = t.boss
	var sm = t.sm
	sm.states["Idle"].beat_left = -1.0
	boss.pillar.gone()
	boss.stand_on_floor(home)
	boss.leave_perch()
	boss.play_anim(&"perch_idle")


static func reset(t) -> void:
	var sm = t.sm
	sm.break_owed = false
	sm.pillar_hits = 0
	sm.carry_left = 0.0
	sm.cancel_launch()
	t.player.set_ice(false)


# Every moment on the mat a read can Break him in: his punish window, and standing between his attacks.
static func entry_cases(t) -> Array:
	var sm = t.sm
	return [
		["his punish window", func(): sm.on_child_transition(sm.current_state, "Downed"), func(): return sm.current_state.name == "Downed"],
		["standing on the mat between attacks", func(): sm.on_child_transition(sm.current_state, "Idle"), func(): return sm.current_state.name == "Idle"],
	]


static func extra(t) -> void:
	var boss = t.boss
	var sm = t.sm
	var gauge = boss.break_gauge
	var home: Vector2 = SPEC.home

	t.log_p("-- what fills it, and what only drains it")
	var source: Node2D = t.dummy_source()
	t.check(gauge.earns_from.call(HitInfo.make(&"liam_tsunami", source, Vector2.ZERO)) and gauge.owns_attack.call(&"liam_tsunami"), "a read of his tsunami fills it")
	t.check(not gauge.earns_from.call(HitInfo.make(&"liam_tremor", source, Vector2.ZERO)) and gauge.owns_attack.call(&"liam_tremor"), "his tremor ridges never fill it, but land and drain it")
	await t.reset_gauged(home)
	await t.settle_player(Vector2(640, 800))
	gauge.value = 3.0 * gauge.parry_gain
	t.front_hit(&"liam_tremor", source)
	t.clear_iframes()
	t.player.playerHealth = 1000
	t.check(is_equal_approx(gauge.value, 2.0 * gauge.parry_gain), "a ridge that lands drains a read (%.3f)" % gauge.value)
	t.check(await t.parry_once(&"liam_tsunami") == 3 and is_equal_approx(gauge.value, 3.0 * gauge.parry_gain), "a parried wave is a read (%.3f)" % gauge.value)
	t.clear_iframes()

	t.log_p("-- attacks 3 and 4")
	t.check(gauge.earns_from.call(HitInfo.make(&"liam_lunge", source, Vector2.ZERO)) and gauge.owns_attack.call(&"liam_lunge"), "a read of his lunge fills it, parried or perfectly dodged")
	for id: StringName in [&"liam_fire_quake", &"liam_fire_tornado"]:
		t.check(not gauge.earns_from.call(HitInfo.make(id, source, Vector2.ZERO)) and gauge.owns_attack.call(id), "%s never fills it, but lands and drains it" % id)
	await t.reset_gauged(home)
	await t.settle_player(Vector2(640, 800))
	gauge.value = 3.0 * gauge.parry_gain
	t.front_hit(&"liam_fire_quake", source)
	t.clear_iframes()
	t.player.playerHealth = 1000
	var after_ring: float = gauge.value
	t.front_hit(&"liam_impale_burn", source)
	t.clear_iframes()
	t.player.playerHealth = 1000
	t.check(is_equal_approx(after_ring, 2.0 * gauge.parry_gain), "a fire ring that lands drains a read (%.3f)" % after_ring)
	t.check(is_equal_approx(gauge.value, after_ring), "an impale burn costs nothing (%.3f)" % gauge.value)
	t.check(await t.parry_once(&"liam_lunge") == 3 and is_equal_approx(gauge.value, 3.0 * gauge.parry_gain), "a parried lunge is a read (%.3f)" % gauge.value)
	t.clear_iframes()

	t.log_p("-- the pillar is not him: punching it fills nothing")
	await t.reset_gauged(home)
	boss.pillar.rise(sm.PERCH, 0.0)
	boss.pillar.park()
	boss.stand_on_pillar()
	boss.perch()
	sm.on_child_transition(sm.current_state, "Tsunami")
	await t.settle_player(sm.FRONT_SPOT)
	var keep_safe := func(): t.player.is_invincible = true
	t.physics_frame.connect(keep_safe)
	# It opens on the Tsunami's first wave's crash on the bottom rope (liam_tsunami_gate).
	await t.wait_until(func(): return not boss.pillar.shielded, 60 * 8)
	var before: float = gauge.value
	var hits: int = sm.pillar_hits
	await t.swing()
	t.physics_frame.disconnect(keep_safe)
	t.player.is_invincible = false
	t.check(sm.pillar_hits == hits + 1 and gauge.value == before, "the pillar took the punch and the gauge didn't move (%.3f)" % gauge.value)

	t.log_p("-- a Break on the pillar is banked for his fall")
	sm.on_child_transition(sm.current_state, "Tsunami")
	await t.wait(3)
	gauge.locked = false
	gauge.value = gauge.max_value - gauge.parry_gain
	# Before his first wave reaches the player at the spot.
	var read: bool = await t.parry_once(&"liam_tsunami") == 3
	await t.wait(2)
	t.log_p("read %s, owed %s, in %s, locked %s, down %s" % [read, sm.break_owed, sm.current_state.name, gauge.locked, boss.is_down()])
	t.check(read and sm.break_owed and String(sm.current_state.name) != "Broken" and gauge.locked and boss.is_down(), "banked: still up there, the gauge locked and him counted down")
	sm.on_child_transition(sm.current_state, "Fall")
	var broken: bool = await t.wait_until(func(): return sm.current_state.name == "Broken", 90)
	t.check(broken and not sm.break_owed and boss.global_position == sm.LAND_SPOT, "his fall lands him in Broken, at LAND_SPOT")
	await t.wait_until(func(): return sm.current_state.name != "Broken", 60 * 5)
