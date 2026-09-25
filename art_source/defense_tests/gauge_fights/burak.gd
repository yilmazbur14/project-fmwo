extends RefCounted

# Captain Burak's gauge spec for verify_defense.gd's gauge modes (break_entry, juggle, juggle_kill and
# gauge_extra with fight=burak). The keys and the optional statics are listed over GAUGE_FIGHTS_DIR there.
# His gauge is a parry counter (BurakBossScript.BREAK): max 60, and a parried shot is worth 30 and a parried
# swing 20, credited by his body's own Defense.parried connection rather than the gauge's own gains, which
# are all 0. So break_gauge, which reads those gains, doesn't apply to him, and extra() covers his
# arithmetic instead: two shots break him, three swings do, a hit costs 20, and credit carries over.

const SPEC := {
	"body": "Arena/BurakBossScene/BurakBossCharacterBody",
	# HOME, already below his juggle floor, with the ring round him for the player.
	"home": Vector2(960, 560),
	"light": &"burak_shot",
	"strong": &"",
	"foreign": &"josh_card_throw",
	"punish_state": "Taunt",
	"broken_state": "Broken",
	"cycle_states": ["Shots", "Barrels", "Cutlass"],
	"defeated_state": "Defeated",
	"reads_to_break": 0,
	"art": "res://Scripts/BurakBossArtLayout.gd",
	"juggle_via": "clip",
	"drives_player": true,
	# His body credits his parries, so break_gauge skips him and extra() covers the gauge.
	"gauge_gains": false,
}


# The Laugh is its own mode's: a volley in a cycle these modes start again must never cut to it.
static func reset(t) -> void:
	t.sm.laugh_played = true


static func entry_cases(t) -> Array:
	var sm = t.sm
	return [
		["the pistol pair's load", func(): sm.on_child_transition(sm.current_state, "Shots"), func(): return sm.current_state.name == "Shots" and sm.current_state.beat == sm.current_state.Beat.LOAD and sm.current_state.beat_clock >= 0.3],
		["a ball in the air", func(): sm.on_child_transition(sm.current_state, "Shots"), func(): return not t.hazards_of("BurakBossBallScript.gd").is_empty()],
		["the kegs coming down", func(): sm.on_child_transition(sm.current_state, "Barrels"), func(): return t.hazards_of("BurakBossBarrelScript.gd").size() >= 2],
		["the cutlass chase", func(): sm.on_child_transition(sm.current_state, "Cutlass"), func(): return sm.current_state.name == "Cutlass" and sm.current_state.beat == sm.current_state.Beat.CHASE and sm.current_state.beat_clock >= 0.1],
		["a cutlass wind-up", func(): sm.on_child_transition(sm.current_state, "Cutlass"), func(): return sm.current_state.name == "Cutlass" and sm.current_state.beat == sm.current_state.Beat.WINDUP],
		["the taunt", func(): sm.on_child_transition(sm.current_state, "Taunt"), func(): return sm.current_state.name == "Taunt"],
		["between two attacks", func(): sm.on_child_transition(sm.current_state, "Idle"), func(): return sm.current_state.name == "Idle"],
	]


# Straight through the player's own defence, a read at a time: the gauge's arithmetic and nothing else,
# with no attack of his running.
static func extra(t) -> void:
	var sm = t.sm
	var gauge: Node = t.boss.break_gauge
	var breaks := [0]
	var count_break := func(): breaks[0] += 1
	gauge.broke.connect(count_break)

	t.log_p("-- his numbers")
	t.check(gauge.max_value == 60.0 and gauge.unlock_delay == 1.0 and gauge.hit_loss == 20.0 and gauge.guard_break_loss == 40.0, "max 60, open again 1 s after he's up, a hit -20, a guard break -40")
	t.check(gauge.parry_gain == 0.0 and gauge.grab_parry_gain == 0.0 and gauge.perfect_dodge_gain == 0.0 and gauge.punch_gain == 0.0 and gauge.charged_punch_gain == 0.0 and gauge.reflect_gain == 0.0, "and none of the gauge's own gains: his body credits his parries")

	t.log_p("-- two parried shots from empty break him, one doesn't")
	await t.parry_once(&"burak_shot")
	t.check(gauge.value == 30.0 and breaks[0] == 0, "one parried shot: 30, half of it exactly (%.1f)" % gauge.value)
	await t.parry_once(&"burak_shot")
	await t.wait(2)
	t.check(breaks[0] == 1 and gauge.value == 0.0 and gauge.locked and sm.current_state.name == "Broken", "the second breaks him, and the gauge empties and locks")

	await t.reset_gauged(SPEC.home)
	t.log_p("-- three parried swings from empty break him, two don't")
	await t.parry_once(&"burak_cutlass")
	await t.parry_once(&"burak_cutlass")
	t.check(gauge.value == 40.0 and breaks[0] == 1, "two parried swings: 40, two thirds of it exactly (%.1f)" % gauge.value)
	await t.parry_once(&"burak_cutlass")
	await t.wait(2)
	t.check(breaks[0] == 2 and sm.current_state.name == "Broken", "the third breaks him")

	await t.reset_gauged(SPEC.home)
	t.log_p("-- any hit of his costs 20, never under 0, and one between two parries keeps him standing")
	gauge.add(50.0)
	var drained := []
	for id: StringName in [&"burak_shot", &"burak_cutlass", &"burak_barrel_blast"]:
		t.clear_iframes()
		t.omni_hit(id, t.dummy_source())
		drained.append(gauge.value)
	t.check(drained == [30.0, 10.0, 0.0], "a shot, a swing and a blast landing from 50: 30, 10, 0 (%s)" % [drained])
	t.clear_iframes()
	t.player.playerHealth = 1000
	await t.wait(40)
	await t.parry_once(&"burak_shot")
	t.clear_iframes()
	t.omni_hit(&"burak_shot", t.dummy_source())
	var between: float = gauge.value
	await t.wait(40)
	await t.parry_once(&"burak_shot")
	await t.wait(2)
	t.check(between == 10.0 and gauge.value == 40.0 and breaks[0] == 2, "parry, hit, parry: 10 after the hit, 40 after, and no Break (%.0f)" % gauge.value)

	await t.reset_gauged(SPEC.home)
	t.log_p("-- a guard break costs 40, and nobody else's attack moves it")
	gauge.add(50.0)
	t.defense._set_stamina(t.defense.max_stamina)
	t.press(KEY_SHIFT)
	await t.wait(3)
	t.defense.drain_stamina(t.defense.max_stamina)
	await t.wait(2)
	t.release(KEY_SHIFT)
	t.check(t.defense.is_guard_broken and gauge.value == 10.0, "a guard break: 50 -> %.0f" % gauge.value)
	t.defense.clear_guard_break()
	t.clear_iframes()
	await t.wait(40)
	await t.parry_once(&"josh_card_throw")
	t.clear_iframes()
	t.omni_hit(&"josh_card_throw", t.dummy_source())
	t.check(gauge.value == 10.0, "someone else's attack, parried or landed: still %.0f" % gauge.value)

	await t.reset_gauged(SPEC.home)
	t.log_p("-- credit carries from one attack to the next")
	await t.parry_once(&"burak_cutlass")
	await t.parry_once(&"burak_cutlass")
	t.check(gauge.value == 40.0 and breaks[0] == 2, "two swings carried: 40")
	await t.parry_once(&"burak_shot")
	await t.wait(2)
	t.check(breaks[0] == 3 and sm.current_state.name == "Broken", "and one parried shot on top breaks him: 40 + 30")
	gauge.broke.disconnect(count_break)
