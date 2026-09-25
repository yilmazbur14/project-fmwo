extends RefCounted

# Greyson's gauge spec for verify_defense.gd's gauge modes (break_gauge, break_entry, juggle, juggle_kill and
# gauge_extra with fight=greyson), on his test scene (GreysonTestFightScene, start_active). The keys and the
# optional statics are listed over GAUGE_FIGHTS_DIR there.
# His gauge is on the rollout's rule, 8 clean reads from empty (GreysonScript.BREAK): a parry or a perfect dodge of
# a plate is a read; his eruptions drain it but never fill it. At 0 HP his fight isn't over: it hands to the final
# brawl (GreysonStateMachine.enter_final_brawl), which is the state a juggle kill lands him in, and only the brawl's
# end calls the win. before_kill() asks the brawl for a win at once, so juggle_kill sees the one outro.
# break_entry and gauge_extra take a comma list of their keys in tier= to run only those (tier=idle,posing): all
# of them without one.

const SPEC := {
	"body": "Arena/GreysonScene/GreysonCharacterBody",
	# HOME: under his juggle floor (about y 518), so a Break leaves him where he stands, with the ring round him for
	# the player and about 197 px of headroom for the juggle.
	"home": Vector2(960, 560),
	"light": &"greyson_plate",
	"strong": &"",
	"foreign": &"josh_card_throw",
	"punish_state": "Pose",
	"broken_state": "Broken",
	"cycle_states": ["Throw", "Slams"],
	"defeated_state": "FinalBrawl",
	"reads_to_break": 8,
	"art": "res://Scripts/GreysonArtLayout.gd",
	"juggle_via": "clip",
	"drives_player": true,
}

const ENTRY_KEYS := ["idle", "throwing", "teleport", "zone", "posing"]
const EXTRA_KEYS := ["numbers", "parry", "eruption", "break", "spoil"]


# A test's brawl resolves only when a case asks it to, and nothing he did before is left on the mat or his meter.
static func reset(t) -> void:
	var brawl = t.sm.states["FinalBrawl"]
	if "auto_result" in brawl:
		brawl.auto_result = &""
	t.sm.clear_pending_zones()
	t.boss.reset_hype()


# The brawl the kill lands him in goes straight to his KO, so the fight ends with one outro.
static func before_kill(t) -> void:
	t.sm.states["FinalBrawl"].auto_result = &"win"


# Every moment a read can Break him in play: between two attacks, the throw with plates out, a teleport, a zone
# waiting to go off, and the poses.
static func entry_cases(t) -> Array:
	var sm = t.sm
	var boss = t.boss
	var cases := [
		["idle", "between two attacks", func(): sm.on_child_transition(sm.current_state, "Idle"), func(): return sm.current_state.name == "Idle"],
		["throwing", "the throw, a plate in flight", func(): sm.on_child_transition(sm.current_state, "Throw"), func():
			return sm.current_state.name == "Throw" and not t.hazards_of("GreysonPlateScript.gd").is_empty()],
		["teleport", "mid-teleport", func(): sm.on_child_transition(sm.current_state, "Slams"), func():
			return sm.current_state.name == "Slams" and boss.current_anim == &"teleport_out"],
		["zone", "a zone waiting to go off", func(): sm.on_child_transition(sm.current_state, "Slams"), func():
			return sm.current_state.name == "Slams" and not sm.live_zones().is_empty()],
		["posing", "a pose, his window open", func(): sm.on_child_transition(sm.current_state, "Pose"), func():
			return sm.current_state.name == "Pose" and sm.is_open() and boss.hurtbox.monitoring],
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
		t.check(gauge.max_value == 100.0 and is_equal_approx(read, 100.0 / 8.0) and is_equal_approx(gauge.parry_gain, read)
			and is_equal_approx(gauge.perfect_dodge_gain, read) and is_equal_approx(gauge.punch_gain, read / 4.0)
			and is_equal_approx(gauge.charged_punch_gain, read / 2.0) and is_equal_approx(gauge.hit_loss, read)
			and is_equal_approx(gauge.guard_break_loss, 2.0 * read) and gauge.grab_parry_gain == 0.0 and gauge.reflect_gain == 0.0
			and gauge.unlock_delay == 3.0, "a read 12.5 of 100: parry and perfect dodge a read, punches a quarter and a half, a hit one back, a guard break two, open again 3 s after he's up")

	if wanted.has("parry"):
		t.log_p("-- a parried plate is one read")
		await t.reset_gauged(SPEC.home)
		await t.settle_player(Vector2(500, 760))
		var result: int = await t.parry_once(&"greyson_plate")
		t.check(result == 3 and is_equal_approx(gauge.value, gauge.parry_gain), "PARRIED, and the gauge %.3f: one read (%.3f)" % [gauge.value, gauge.parry_gain])

	if wanted.has("eruption"):
		t.log_p("-- a perfect dodge of an eruption earns nothing; of a plate, a read")
		await t.reset_gauged(SPEC.home)
		await t.settle_player(Vector2(500, 760))
		var eruption_dodged: bool = await perfect_dodge(t, &"greyson_eruption")
		var after_eruption: float = gauge.value
		var plate_dodged: bool = await perfect_dodge(t, &"greyson_plate")
		t.check(eruption_dodged and after_eruption == 0.0, "an eruption dashed through for a perfect dodge: the gauge stays at %.1f" % after_eruption)
		t.check(plate_dodged and is_equal_approx(gauge.value, gauge.perfect_dodge_gain), "a plate the same way: one read (%.3f)" % gauge.value)

	if wanted.has("break"):
		t.log_p("-- a Break with plates out and a zone waiting takes them all")
		await t.reset_gauged(SPEC.home)
		await t.settle_player(t.OUT_OF_REACH)
		sm.on_child_transition(sm.current_state, "Throw")
		var thrown: bool = await t.wait_until(func(): return not t.hazards_of("GreysonPlateScript.gd").is_empty(), 200)
		sm.on_child_transition(sm.current_state, "Slams")
		var planted: bool = await t.wait_until(func(): return not sm.live_zones().is_empty(), 400)
		var plates_in: int = t.hazards_of("GreysonPlateScript.gd").size()
		var zones_in: int = sm.live_zones().size()
		await t.force_break()
		await t.wait(2)
		t.log_p("before the Break: %d plates, %d zones; after: %s, hazards %d, zones %d" % [plates_in, zones_in, sm.current_state.name, t.live_hazards().size(), sm.live_zones().size()])
		t.check(thrown and planted and zones_in > 0, "plates out, then a zone waiting")
		t.check(sm.current_state.name == "Broken" and t.hazards_of("GreysonPlateScript.gd").is_empty() and sm.live_zones().is_empty(),
			"the Break leaves no plate in flight and no zone waiting")

	if wanted.has("spoil"):
		t.log_p("-- a hit in a pose spoils it: half a cell off")
		await t.reset_gauged(SPEC.home)
		await t.settle_player(Vector2(760, 700))
		sm.on_child_transition(sm.current_state, "Pose")
		# Past his turn to the crowd, which Pose counts as the phase but spoils nothing in: the first pose struck.
		var open: bool = await t.wait_until(func(): return sm.is_open() and boss.hurtbox.monitoring, 60)
		boss.add_hype(2.0)
		var dealt: int = boss.take_punch(1)
		await t.wait(2)
		t.check(open and dealt == 1 and is_equal_approx(boss.hype, 1.5), "the pose's first hit takes his meter from 2 to %.1f" % boss.hype)


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
