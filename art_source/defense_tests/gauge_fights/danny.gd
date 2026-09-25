extends RefCounted

# Danny's gauge spec for verify_defense.gd's gauge modes (break_gauge, break_entry, juggle, juggle_kill and
# gauge_extra with fight=danny). The keys and the optional statics are listed over GAUGE_FIGHTS_DIR there.
# His gauge is on the rollout's rule, 8 clean reads from empty (DannyBossScript.BREAK): a parry or a perfect
# dodge of a slam or a headbutt is a read, his quake rings drain it but never fill it.
# At 0 HP his fight isn't over: he gets up for the sumo (DannyBossStateMachine.enter_sumo), which is the
# state a juggle kill lands him in, and only the sumo's result ends the fight. before_kill() asks it for a
# win at once, so juggle_kill sees the one outro.
# break_entry and gauge_extra take a comma list of their keys in tier= to run only those (tier=idle,asleep):
# all of them without one.

const SPEC := {
	"body": "Arena/DannyBossScene/DannyBossCharacterBody",
	# Under his juggle floor (about y 746), so a Break leaves him where he stands, with the ring round him for
	# the player.
	"home": Vector2(960, 760),
	"light": &"danny_butt_slam",
	"strong": &"",
	"foreign": &"josh_card_throw",
	"punish_state": "Sleep",
	"broken_state": "Broken",
	"cycle_states": ["Spit", "Slams"],
	"defeated_state": "Sumo",
	"reads_to_break": 8,
	"art": "res://Scripts/DannyBossArtLayout.gd",
	"juggle_via": "clip",
	"drives_player": true,
}

const ENTRY_KEYS := ["idle", "gulp", "glob", "hovering", "drop", "asleep", "headbutt", "staggered"]
const EXTRA_KEYS := ["numbers", "parry", "ring", "string", "sleep"]


# A test's sumo resolves only when a case asks it to, and nothing he did before is left on him or the mat.
static func reset(t) -> void:
	var sumo = t.sm.states["Sumo"]
	if "auto_result" in sumo:
		sumo.auto_result = &""
	t.boss.set_lift(0.0)
	t.sm.clear_puddles()


# The sumo the kill lands him in resolves straight away as a win, so the fight ends with one outro.
static func before_kill(t) -> void:
	t.sm.states["Sumo"].auto_result = &"win"


# Every moment a read can Break him in play: between two attacks, each beat of his spit and his string, his nap,
# the headbutt winding up at a rooted player, and the dizzy spell after a parried one.
static func entry_cases(t) -> Array:
	var sm = t.sm
	var boss = t.boss
	var rooted := func():
		sm.on_child_transition(sm.current_state, "Idle")
		sm.root_grace_left = 0.0
		sm.test_root_player()
	var cases := [
		["idle", "between two attacks", func(): sm.on_child_transition(sm.current_state, "Idle"), func(): return sm.current_state.name == "Idle"],
		["gulp", "the spit's gulp", func(): sm.on_child_transition(sm.current_state, "Spit"), func():
			return sm.current_state.name == "Spit" and boss.current_anim == &"spit_windup"],
		["glob", "a glob in the air", func(): sm.on_child_transition(sm.current_state, "Spit"), func():
			return not t.hazards_of("DannyBossGlobScript.gd").is_empty()],
		["hovering", "hovering over the player in the string", func(): sm.on_child_transition(sm.current_state, "Slams"), func():
			return sm.current_state.name == "Slams" and boss.current_anim == &"air" and boss.lift_px >= 300.0],
		["drop", "the string's drop", func(): sm.on_child_transition(sm.current_state, "Slams"), func():
			return sm.current_state.name == "Slams" and boss.current_anim == &"slam_drop"],
		["asleep", "his nap", func(): sm.on_child_transition(sm.current_state, "Sleep"), func(): return sm.is_sleeping()],
		["headbutt", "the headbutt's wind-up at a rooted player", rooted, func():
			return sm.current_state.name == "Headbutt" and boss.current_anim == &"headbutt_windup" and t.player.is_action_locked],
		["staggered", "dizzy after a parried headbutt", func(): sm.on_child_transition(sm.current_state, "Staggered"), func():
			return sm.current_state.name == "Staggered"],
	]
	var wanted := _keys(t, ENTRY_KEYS)
	var out := []
	for case in cases:
		if wanted.has(case[0]):
			out.append([case[1], case[2], case[3]])
	return out


static func extra(t) -> void:
	var boss = t.boss
	var sm = t.sm
	var gauge: Node = boss.break_gauge
	var wanted := _keys(t, EXTRA_KEYS)

	if wanted.has("numbers"):
		t.log_p("-- his numbers: 8 reads from empty")
		var read: float = boss.BREAK_READ
		t.check(gauge.max_value == 100.0 and is_equal_approx(read, 12.5) and is_equal_approx(gauge.parry_gain, read)
			and is_equal_approx(gauge.perfect_dodge_gain, read) and is_equal_approx(gauge.punch_gain, read / 4.0)
			and is_equal_approx(gauge.charged_punch_gain, read / 2.0) and is_equal_approx(gauge.hit_loss, read)
			and is_equal_approx(gauge.guard_break_loss, 2.0 * read) and gauge.grab_parry_gain == 0.0 and gauge.reflect_gain == 0.0
			and gauge.unlock_delay == 3.0, "a read 12.5 of 100: parry and perfect dodge a read, punches a quarter and a half, a hit one back, a guard break two, open again 3 s after he's up")

	if wanted.has("parry"):
		t.log_p("-- a parried headbutt is one read")
		await t.reset_gauged(SPEC.home)
		await t.settle_player(Vector2(500, 700))
		var result: int = await t.parry_once(&"danny_headbutt")
		t.check(result == 3 and is_equal_approx(gauge.value, gauge.parry_gain), "PARRIED, and the gauge %.3f: one read, not two (%.3f)" % [gauge.parry_gain, gauge.value])

	if wanted.has("ring"):
		t.log_p("-- a perfect dodge of a quake ring earns nothing; of a slam, a read")
		await t.reset_gauged(SPEC.home)
		await t.settle_player(Vector2(500, 700))
		var ring_dodged: bool = await perfect_dodge(t, &"danny_quake_ring")
		var after_ring: float = gauge.value
		var slam_dodged: bool = await perfect_dodge(t, &"danny_butt_slam")
		t.check(ring_dodged and after_ring == 0.0, "a ring dashed through for a perfect dodge: the gauge stays at %.1f" % after_ring)
		t.check(slam_dodged and is_equal_approx(gauge.value, gauge.perfect_dodge_gain), "a slam the same way: one read (%.3f)" % gauge.value)

	if wanted.has("string"):
		t.log_p("-- a Break mid-string takes every ring and puddle with it")
		await t.reset_gauged(SPEC.home)
		await t.settle_player(t.OUT_OF_REACH)
		sm.on_child_transition(sm.current_state, "Spit")
		var spat: bool = await t.wait_until(func(): return sm.live_puddles().size() == 2, 300)
		sm.on_child_transition(sm.current_state, "Slams")
		var rolling: bool = await t.wait_until(func(): return not t.hazards_of("DannyBossQuakeRingScript.gd").is_empty(), 400)
		var puddles_in: int = sm.live_puddles().size()
		var rings_in: int = t.hazards_of("DannyBossQuakeRingScript.gd").size()
		await t.force_break()
		await t.wait(2)
		t.log_p("before the Break: %d puddles, %d rings; after: %s, hazards %d, puddles %d" % [puddles_in, rings_in, sm.current_state.name, t.live_hazards().size(), sm.live_puddles().size()])
		t.check(spat and rolling and rings_in > 0, "two puddles down, then a ring rolling mid-string")
		t.check(sm.current_state.name == "Broken" and t.live_hazards().is_empty() and sm.live_puddles().is_empty(), "the Break mid-string leaves no ring or puddle")

	if wanted.has("sleep"):
		t.log_p("-- a Break from his nap stops the regen")
		await t.reset_gauged(SPEC.home)
		await t.settle_player(Vector2(500, 700))
		var sleep = sm.states["Sleep"]
		sm.on_child_transition(sm.current_state, "Sleep")
		boss.boss_health = boss.get_max_health() - 20
		var ticked: bool = await t.wait_until(func(): return sleep.healed > 0, 120)
		var before: int = boss.boss_health
		await t.force_break()
		var broke: bool = await t.wait_until(func(): return sm.current_state.name == "Broken", 30)
		await t.wait(90)
		t.log_p("healed %d asleep, then Broken: %d HP -> %d after 1.5 s" % [sleep.healed, before, boss.boss_health])
		t.check(ticked and broke, "asleep and healing, then Broken")
		t.check(boss.boss_health == before and sleep.released and not is_instance_valid(boss.regen) and not is_instance_valid(boss.zzz),
			"the regen stopped with the nap: no HP back, no regen or Z's left on him")


# A perfect dodge of `id`: a dash, and inside its immunity the hit, from a source of its own. Whether it paid one.
static func perfect_dodge(t, id: StringName) -> bool:
	var defense: Node = t.defense
	var ready := func() -> bool:
		return not defense.is_dash_recovering() and not defense.is_dash_cooling_down() \
			and defense.clock - defense.last_perfect_dodge_time >= defense.perfect_dodge_cooldown + 0.05
	await t.wait_until(ready, 240)
	# Past the gap a dash's immunity needs from the last one.
	await t.wait(40)
	var got := [false]
	var on_dodge := func(hit: RefCounted): got[0] = got[0] or hit.attack_id == id
	defense.perfect_dodged.connect(on_dodge)
	t.clear_iframes()
	t.tap(KEY_W)
	await t.wait_until(func(): return t.player.is_dodging, 20)
	await t.wait(2)
	t.omni_hit(id, t.dummy_source())
	defense.perfect_dodged.disconnect(on_dodge)
	await t.wait_until(func(): return not t.player.is_dodging, 30)
	await t.wait(4)
	return got[0]


# The keys tier= names, or all of them.
static func _keys(t, all: Array) -> Array:
	var asked := []
	for key in str(t.tier).split(","):
		if all.has(key.strip_edges()):
			asked.append(key.strip_edges())
	return asked if not asked.is_empty() else all
