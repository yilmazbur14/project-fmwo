extends RefCounted

# pow_always_dazes fight=<fight> (the user, 2026-10-06: "it should be as simple as 3 hits should trigger the uppercut"):
# every opening of the fight in which the player's punches land on its boss is entered and held open, and three
# punches go in from under him. All three land, the third is the POW, and it dazes him into the finisher's mash; the
# mash's uppercut lands and shuts the opening. No opening is left where a POW lands and nothing follows.
# Where an opening takes more than three punches (Danny's nap and his back after a parried slam: 6; Greyson's poses: 8),
# a mash left to fizzle hands the daze back, and three more punches daze him again.
# Matt, the fight the user named, plays his attacks for real instead of being dropped into his window: the Ezreal set
# into its Echo Roars, the Glass Row and the Deafening Glass Row. Through every beat of each his punch gate stays shut
# (his Spent, the roars and the glass included), and the window each ends in, at HOME or at the Glass Row's station
# over the player, takes the three punches and the daze.
# Jordan's kaiju: the knock-off and, since the user's 2026-10-06 "yes give the kaiju breath opening the uppercut too",
# the breath's recoil. From the recoil the head stays down through the uppercut and comes back up once it is over,
# sliding the player out of the back wall's way as it does when the opening times out.
# Eric (V2, as he ships): Winded, a parried hug's stagger, his own sword's (both 3 punches since 2026-10-06), the hug's
# stumble, the whirlwind's throw while the sword is out of his hands, and his Break.
# tier=settle (fight=matt|danny|josh|carter_akuma|jordan|eric): a window whose clock runs out 0.05, 0.15 and 0.20 s after
#   the POW lands, inside the finisher's settle beat: each still dazes him (PlayerFinisher._hold_window), and once a mash
#   left to fizzle is over his clock runs on from where it was and shuts the window on time. Matt's Recover, Danny's nap,
#   Josh's and Carter's recoveries on their Timers, the kaiju's recoil on its own clock, Eric's hug stumble on his
#   AnimationPlayer (EricScript.hold_window). Matt's also: a hit on the player in the beat, which the finisher already
#   shrugs off (PlayerDefense: is_finishing), the game paused in it, and the fight ending in it (FightOutro, as a loss),
#   after which the finisher lets go of his window and nothing of his is left held.
# tier=race (fight=mason|eric|matt): the third punch pressed and his window shut on its own timeout at the idle step
#   10 to 20 frames on, across the fist's contact: no punch lands once it has shut (PlayerPunching._land_on_contact,
#   MasonScript.take_punch), and a POW that lands dazes him. Eric's also: the whirlwind throw played through to its
#   chain's next attack, three punches as fast as they go from the step his hurtbox opens.
# --fixed-fps 60.

const FIGHTS := ["burak", "eric", "computah", "greyson", "matt", "mason", "josh", "danny", "carter_akuma", "liam", "liam_elements", "jordan"]
const ERIC_MODES := "res://art_source/defense_tests/eric/window_daze.gd"
const HitInfo := preload("res://Scripts/HitInfo.gd")
# A held opening's clock, far past anything the case needs.
const HELD := 99.0
# Matt's attacks run live up to their window for at most this long.
const MATT_CHAIN_FRAMES := 60 * 60
# tier=settle: each fight's window on a clock, and how long before the POW's daze it runs out.
const SETTLE_WINDOWS := {"matt": "Recover", "danny": "Sleep", "josh": "Recover", "carter_akuma": "Recover", "jordan": "Recoil", "eric": "BearHug"}
const LEADS := [0.05, 0.15, 0.20]
# A window let go of after a fizzle shuts its lead after the finisher is over, give or take this many frames.
const RESUME_SLACK := 15
# tier=race: each fight's window, and the frames after the third press at whose idle step it shuts.
const RACE_WINDOWS := {"mason": "Eat", "eric": "Winded", "matt": "Recover"}
const RACE_FROM := 10
const RACE_TO := 20

# Bixby's dizzy spell as his fight has it, put back on every reset after the case that holds it open.
static var dizzy_time := -1.0


static func run(t) -> void:
	if not FIGHTS.has(t.fight):
		t.check(false, "pow_always_dazes knows no openings for fight=%s" % t.fight)
		return
	if t.tier == "settle":
		await settle(t)
		return
	if t.tier == "race":
		await race(t)
		return
	if t.fight == "eric":
		await eric(t)
		return
	if not await t.load_gauged():
		return
	if t.fight == "liam":
		dizzy_time = t.sm.combined_dizzy_time
	var finisher: Node = t.player.get_node("Finisher")
	# Its key bounce is real seconds, which a fixed-fps run outpaces.
	finisher.min_press_interval = 0.0
	if t.fight == "matt":
		await matt_chains(t)
	for c in cases(t):
		await reset(t)
		t.log_p("-- %s" % c.what)
		await c.enter.call()
		await opening(t, c)


# Each opening: what it is, how he is put in it, and whether it takes a second combo after a fizzled mash.
static func cases(t) -> Array:
	var sm: Node = t.sm
	var bare := func(state_name: String) -> Callable:
		return func(): sm.on_child_transition(sm.current_state, state_name)
	var broken := {"what": "his Break", "state": t.fight_spec.broken_state, "enter": func(): await into_break(t)}
	match t.fight:
		"burak":
			return [{"what": "his taunt", "state": "Taunt", "enter": bare.call("Taunt")}, broken]
		"computah":
			return [{"what": "his vent", "state": "Punish", "enter": bare.call("Punish")}, broken]
		"greyson":
			return [{"what": "his poses", "state": "Pose", "enter": bare.call("Pose"), "twice": true}, broken]
		"matt":
			return [broken]
		"mason":
			return [{"what": "his eat window", "state": "Eat", "enter": bare.call("Eat")}, broken]
		"josh":
			return [{"what": "his recovery", "state": "Recover", "enter": bare.call("Recover")}, broken]
		"danny":
			var bump: Node = sm.states["BellyBump"]
			var slip := func():
				# The slip's own hand-over, from where he lies down: what a belly bump that slips on his worms passes.
				bump.feet = t.boss.global_position
				bump._onto_back()
			return [
				{"what": "his nap", "state": "Sleep", "enter": bare.call("Sleep"), "twice": true},
				{"what": "his dizzy spell after a parried headbutt or belly bump", "state": "Staggered", "enter": bare.call("Staggered")},
				{"what": "his back after a parried slam", "state": "OnBack", "enter": func(): sm.enter_on_back(HELD, 6, true, &"slam"), "twice": true},
				{"what": "his back after a slip on his own worms", "state": "OnBack", "enter": slip},
				broken,
			]
		"carter_akuma":
			return [
				{"what": "his recovery", "state": "Recover", "enter": bare.call("Recover")},
				{"what": "his recovery cashed from a Break", "state": "Recover", "enter": func(): await into_break(t)},
			]
		"liam":
			var dizzy := func():
				sm.combined_spin_time = 1.0
				sm.attacks = []
				sm.on_child_transition(sm.current_state, "Combined")
				var combined: Node = sm.states["Combined"]
				await t.wait_until(func(): return sm.current_state == combined and combined.is_dizzy(), 60 * 30)
				for hazard in t.get_nodes_in_group(sm.HAZARD_GROUP):
					hazard.queue_free()
			return [
				{"what": "his landing's recovery", "state": "Recover", "enter": bare.call("Recover")},
				{"what": "the dizzy spell his spin ends on", "state": "Combined", "enter": dizzy},
				broken,
			]
		"liam_elements":
			return [{"what": "down off his pillar", "state": "Downed", "enter": bare.call("Downed")}, broken]
		"jordan":
			return [
				{"what": "knocked off the kaiju by a parried stomp", "state": "Dismounted", "enter": bare.call("Dismounted")},
				{"what": "on the kaiju's lowered head after its breath", "state": "Recoil", "enter": bare.call("Recoil")},
				broken,
			]
	return []


# Riding at home or on his spot, idle, gauge held empty, full health, nothing of his live, the player whole.
static func reset(t) -> void:
	t.player.get_node("Finisher").min_press_interval = 0.0
	await t.reset_gauged(t.fight_spec.home)
	if t.fight == "liam":
		t.sm.combined_dizzy_time = dizzy_time
	t.hold_break_gauge(t.boss)
	t.player.combo.reset()
	await t.settle_player(t.fight_spec.home + Vector2(-320, 60))


# A Break the way his fight takes one, the player let go of once the drive beside him is over.
static func into_break(t) -> void:
	var gauge: Node = t.boss.break_gauge
	gauge.locked = false
	gauge.set_physics_process(true)
	gauge.value = 0.0
	await t.force_break()
	await t.wait_until(func(): return t.boss.get_finisher_hurtbox().monitorable, 60)
	await t.wait_until(func(): return not t.player.is_action_locked, 120)
	t.hold_break_gauge(t.boss)


# The opening he is in, held open on every clock it has, then three punches: the daze, the mash and its uppercut.
static func opening(t, c: Dictionary) -> void:
	var sm: Node = t.sm
	var finisher: Node = t.player.get_node("Finisher")
	var hurtbox: Area2D = t.boss.get_finisher_hurtbox()
	var opened: bool = await t.wait_until(func(): return hurtbox.monitorable and sm.current_state.name == c.state, 120)
	t.check(opened, "%s: he is in %s with his hurtbox on (%s)" % [c.what, c.state, sm.current_state.name])
	if not opened:
		return
	hold(t)
	var first: Dictionary = await three(t)
	var dazed: bool = await t.wait_until(func(): return finisher.phase == t.FINISHER_DAZED and finisher.prompt_visible, 120)
	t.log_p("%s: landed %s in %s, POW %s, can_be_dazed after %s, dazed %s, tiered %s" % [c.what, first.dealt, first.states, first.pow, first.dazeable, dazed, finisher.tiered])
	t.check(first.dealt.size() == 3 and first.pow and dazed, "%s: three punches land, the third the POW, and it dazes him into the mash" % c.what)
	if not dazed:
		await t.wait_until(func(): return not finisher.is_active(), 900)
		return
	if c.get("twice", false):
		await t.wait_until(func(): return finisher.phase == t.FINISHER_OFF, 600)
		await t.wait(20)
		var still: bool = sm.current_state.name == c.state and hurtbox.monitorable
		var again: Dictionary = await three(t)
		dazed = await t.wait_until(func(): return finisher.phase == t.FINISHER_DAZED and finisher.prompt_visible, 120)
		t.log_p("%s, after the fizzle: still open %s, landed %s, POW %s, dazed %s" % [c.what, still, again.dealt, again.pow, dazed])
		t.check(still and again.dealt.size() == 3 and again.pow and dazed,
			"%s: a fizzled mash leaves it open, and three more punches daze him again" % c.what)
		if not dazed:
			await t.wait_until(func(): return not finisher.is_active(), 900)
			return
	var health: float = t.boss.get_health_ratio()
	await t.mash_finisher()
	await t.wait_until(func(): return finisher.phase == t.FINISHER_OFF, 900)
	var shut: bool = await t.wait_until(func(): return not hurtbox.monitorable and not t.boss.can_be_dazed(), 60)
	t.log_p("%s: health %.3f -> %.3f, then %s, hurtbox on %s" % [c.what, health, t.boss.get_health_ratio(), sm.current_state.name, hurtbox.monitorable])
	t.check(t.boss.get_health_ratio() < health and shut, "%s: the mash's uppercut lands and shuts the opening" % c.what)
	if c.state == "Recoil":
		await recoil_after(t)


# Every clock of his that would close it: his Timers stopped, and the opening's own accumulator pushed out.
static func hold(t) -> void:
	var sm: Node = t.sm
	var state: Node = sm.current_state
	t.stop_boss_timers()
	match String(state.name):
		"Staggered":
			state.left = HELD
		"OnBack":
			state.beat_left = HELD
		"Dismounted", "Recoil":
			state.window = HELD
		"Combined":
			sm.combined_dizzy_time = HELD
		_:
			if "time_left" in state:
				state.time_left = HELD


# Three punches from under him, PUNCH_GAP apart: what each dealt, whether the POW landed, and whether he could still be
# dazed after it.
static func three(t) -> Dictionary:
	var combo: Node = t.player.combo
	var seen := {"dealt": [], "pow": false, "dazeable": false, "states": []}
	var on_landed := func(_target, dealt: int, charged: bool):
		seen.dealt.append(dealt)
		seen.states.append(String(t.sm.current_state.name))
		if charged:
			seen.pow = true
	combo.punch_landed.connect(on_landed)
	t.place_under(t.boss.get_finisher_hurtbox())
	await t.wait(6)
	for i in 3:
		await t.swing_any()
		if i < 2:
			await t.wait(6)
	combo.punch_landed.disconnect(on_landed)
	seen.dazeable = t.boss.can_be_dazed()
	return seen


# The kaiju's head after an uppercut on it: down until the finisher is over, then up, the player slid clear of the
# back wall coming home, and his turns going on.
static func recoil_after(t) -> void:
	var kaiju: Node2D = t.sm.kaiju
	var layout: GDScript = load("res://Scripts/JordanKaijuLayout.gd")
	var recoil: Node = t.sm.states["Recoil"]
	var idle: bool = await t.wait_until(func(): return t.sm.current_state.name == "Idle", 60 * 4)
	var shape: CollisionShape2D = t.player.get_node("CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	t.log_p("after the recoil's uppercut: %s, mounted %s, wall %s, slid %s, player %s" % [t.sm.current_state.name, t.boss.mounted,
		kaiju.wall_rect(0), recoil.slid_out, t.player.global_position])
	t.check(idle and t.boss.mounted and kaiju.wall_rect(0) == layout.WALLS[0] and not layout.WALLS[0].intersects(box) and not t.player.is_action_locked,
		"then the head comes up with him on it, the player clear of the back wall coming home, and his turns go on")


# Matt's three attacks played live into their windows, his gauge held and the player whole: his punch gate is shut on
# every frame before the window (his Spent, the Echo Roars and the glass included), and each window takes the daze.
static func matt_chains(t) -> void:
	var sm: Node = t.sm
	var fresh: Node = load("res://Scripts/States/Matt/MattStateMachine.gd").new()
	var live := {"echo_after_ezreal": fresh.echo_after_ezreal, "phase_two_ratio": fresh.phase_two_ratio,
		"phase_two_at_break": fresh.phase_two_at_break, "yell_counter_enabled": fresh.yell_counter_enabled}
	fresh.free()
	var chains := [
		["the Ezreal set and the Echo Roars it runs into", "MysticVolley", false],
		["the Glass Row, its window at the station over the player", "GlassRow", false],
		["the Deafening Glass Row", "GlassRow", true],
	]
	for chain in chains:
		await reset(t)
		for key in live:
			sm.set(key, live[key])
		var rotation: Array[String] = [chain[1]]
		sm.attack_rotation = rotation
		sm.last_attack = ""
		if chain[2]:
			t.boss.boss_health = int(t.boss.max_health * 0.45)
			sm.glass_rows_done = 1
			sm.deafen_opened = false
		t.log_p("-- Matt: %s" % chain[0])
		sm.start_cycle()
		var deafened: bool = sm.cycle_deafen
		var states := []
		var leaks := []
		for f in MATT_CHAIN_FRAMES:
			t.player.playerHealth = 1000
			var name := String(sm.current_state.name)
			if states.is_empty() or states[-1] != name:
				states.append(name)
			if name == "Recover":
				break
			if t.boss._is_open() or t.boss.hurtbox.monitorable:
				if not leaks.has(name):
					leaks.append(name)
			await t.physics_frame
		t.log_p("%s: %s, the yell %s; punchable in %s" % [chain[0], states, "deafening" if deafened else "plain", leaks])
		t.check(states[-1] == "Recover" and leaks.is_empty() and deafened == chain[2],
			"%s: his punches are kept out of every beat of it, up to his window (%s)" % [chain[0], states])
		await t.wait_until(func(): return not t.player.is_action_locked, 120)
		await opening(t, {"what": "his window after " + chain[0], "state": "Recover"})


# Eric's openings, on window_daze's own way into each: he is parked, and each case is set up from his home.
static func eric(t) -> void:
	var wd: GDScript = load(ERIC_MODES)
	t.pin_eric(2)
	await t.load_eric()
	await wd.park(t)
	var home: Vector2 = t.boss.global_position
	var sm: Node = t.sm
	var whirl := func():
		await t.settle_player(home + Vector2(-350, 40))
		sm.throw_from_whirlwind()
		var throw: Node = sm.states["SwordThrow"]
		await t.wait_until(func(): return t.boss.get_finisher_hurtbox().monitorable and is_instance_valid(throw.sword), 120)
		# The sword held where it is, so it never comes back to his hand and shuts the opening.
		throw.sword.process_mode = Node.PROCESS_MODE_DISABLED
	var cases := [
		{"what": "Winded at the end of a chain", "state": "Winded", "enter": func(): await wd.open_winded(t), "twice": true},
		{"what": "a parried hug's stagger", "state": "ParryStaggered", "enter": func(): sm.parry_stagger(HELD, home)},
		{"what": "his own sword's stagger", "state": "ParryStaggered", "enter": func(): sm.parry_stagger(HELD, home, true)},
		{"what": "the hug's stumble", "state": "BearHug", "enter": func(): await wd.open_stumble(t, home)},
		{"what": "the whirlwind's throw, the sword out of his hands", "state": "SwordThrow", "enter": whirl},
		{"what": "his Break", "state": "Broken", "enter": func(): await into_break(t)},
	]
	for c in cases:
		await wd.park(t)
		await wd.reset(t, home)
		t.boss.animationPlayer.speed_scale = 1.0
		t.player.get_node("Finisher").min_press_interval = 0.0
		t.player.combo.reset()
		t.log_p("-- %s" % c.what)
		await c.enter.call()
		await opening(t, c)


#THE SETTLE BEAT (tier=settle)

static func settle(t) -> void:
	if not SETTLE_WINDOWS.has(t.fight):
		t.check(false, "tier=settle has no window on a clock for fight=%s" % t.fight)
		return
	await load_for(t)
	for lead in LEADS:
		await settle_window(t)
		await pow_closing(t, lead)
	if t.fight == "matt":
		for extra in ["hit", "pause", "over"]:
			await settle_window(t)
			await pow_closing(t, 0.15, extra)


static func load_for(t) -> void:
	if t.fight == "eric":
		t.pin_eric(2)
		await t.load_eric()
		await load(ERIC_MODES).park(t)
		t.set_meta(&"eric_home", t.boss.global_position)
	else:
		await t.load_gauged()
	t.player.get_node("Finisher").min_press_interval = 0.0


# His settle-tier window, open and held, the combo started fresh.
static func settle_window(t) -> void:
	var state: String = SETTLE_WINDOWS[t.fight]
	if t.fight == "eric":
		var wd: GDScript = load(ERIC_MODES)
		var home: Vector2 = t.get_meta(&"eric_home")
		await wd.park(t)
		await wd.reset(t, home)
		t.player.get_node("Finisher").min_press_interval = 0.0
		await wd.open_stumble(t, home)
	else:
		await reset(t)
		t.sm.on_child_transition(t.sm.current_state, state)
		await t.wait_until(func(): return t.boss.get_finisher_hurtbox().monitorable and t.sm.current_state.name == state, 120)
		hold(t)
	t.player.combo.reset()
	t.player.playerHealth = 1000
	t.clear_iframes()


# His window's clock set to run out `lead` from now.
static func close_in(t, lead: float) -> void:
	var state: Node = t.sm.current_state
	match t.fight:
		"matt":
			t.sm.recover_timer.start(lead)
		"danny":
			t.sm.sleep_timer.start(lead)
		"josh", "carter_akuma":
			state.recover_timer.start(lead)
		"jordan":
			state.window = state.clock - state.opened_at + lead
		"eric":
			var animation: AnimationPlayer = t.boss.animationPlayer
			animation.speed_scale = 1.0
			animation.seek(animation.current_animation_length - lead, true)


static func window_open(t) -> bool:
	var state: Node = t.sm.current_state
	if String(state.name) != SETTLE_WINDOWS[t.fight]:
		return false
	match t.fight:
		"jordan":
			return state.open
		"eric":
			return state.phase == state.Phase.STUMBLE
	return t.boss.get_finisher_hurtbox().monitorable


# Two punches, then the third: as the POW lands his window is set to run out `lead` later. `extra` is what else happens
# in the beat between the POW and the daze: "hit", "pause" or "over".
static func pow_closing(t, lead: float, extra := "") -> void:
	var finisher: Node = t.player.get_node("Finisher")
	var extras := {"": "", "hit": ", a hit on the player in the beat", "pause": ", the game paused in the beat", "over": ", the fight ending in the beat"}
	var what := "%.2f s left at the POW%s" % [lead, extras[extra]]
	t.place_under(t.boss.get_finisher_hurtbox())
	await t.wait(6)
	for i in 2:
		await t.swing_any()
		await t.wait(6)
	var at := {"pow": -1}
	var on_pow := func(_target):
		close_in(t, lead)
		at.pow = Engine.get_physics_frames()
	t.player.combo.charged_hit_landed.connect(on_pow, CONNECT_ONE_SHOT)
	t.tap(KEY_Q)
	await t.wait_until(func(): return at.pow >= 0, 60)
	var hit_result := -1
	if extra == "hit":
		await t.wait(2)
		t.clear_iframes()
		hit_result = t.front_hit(&"matt_mystic_shot", t.dummy_source())
	elif extra == "over":
		await t.wait(2)
		load("res://Scripts/FightOutro.gd").finish_fight(t, false)
	elif extra == "pause":
		await t.wait(1)
		t.paused = true
		await t.wait(30)
		t.paused = false
	if extra == "over":
		var aborted: bool = await t.wait_until(func(): return t.player.fight_over and finisher.phase == t.FINISHER_OFF, 120)
		await t.wait(2)
		var timers_free: bool = t.boss.find_children("*", "Timer", true, false).all(func(timer): return not timer.paused)
		var stepping: bool = t.sm.is_physics_processing() and t.sm.is_processing()
		t.log_p("%s: fight over %s, finisher off %s, his window let go %s, machine stepping %s, timers free %s, now %s" % [what,
			t.player.fight_over, aborted, finisher.held_boss == null, stepping, timers_free, t.sm.current_state.name])
		t.check(aborted and finisher.held_boss == null and stepping and timers_free,
			"%s: the finisher lets go, and nothing of his is left held" % what)
		return
	var dazed: bool = await t.wait_until(func(): return finisher.phase == t.FINISHER_DAZED, 120)
	var settle_s: float = (Engine.get_physics_frames() - at.pow) / 60.0
	t.log_p("%s: the POW %s, the daze %.3f s of physics steps after it: %s" % [what, "landed" if at.pow >= 0 else "never landed", settle_s, dazed])
	t.check(at.pow >= 0 and dazed, "%s: the POW dazes him" % what)
	if extra == "hit":
		t.check(hit_result == HitInfo.Result.IGNORED and t.player.playerHealth == 1000, "%s: shrugged off (result %d)" % [what, hit_result])
	if not dazed:
		await t.wait_until(func(): return not finisher.is_active(), 900)
		return
	await t.wait_until(func(): return finisher.phase == t.FINISHER_OFF, 900)
	var over := Engine.get_physics_frames()
	var limit := int(lead * 60.0) + RESUME_SLACK
	await t.wait_until(func(): return not window_open(t), limit + 30)
	var shut_after: int = Engine.get_physics_frames() - over
	t.log_p("%s: the mash left to fizzle, his window shut %d frames after it was over (%d at most)" % [what, shut_after, limit])
	t.check(not window_open(t) and shut_after <= limit, "%s: after a fizzle his clock runs on from where it was and shuts the window" % what)


#THE WINDOW SHUTTING UNDER THE FIST (tier=race)

static func race(t) -> void:
	if not RACE_WINDOWS.has(t.fight):
		t.check(false, "tier=race has no window for fight=%s" % t.fight)
		return
	await load_for(t)
	var finisher: Node = t.player.get_node("Finisher")
	var state: String = RACE_WINDOWS[t.fight]
	var report := []
	for k in range(RACE_FROM, RACE_TO + 1):
		if t.fight == "eric":
			var wd: GDScript = load(ERIC_MODES)
			await wd.park(t)
			await wd.reset(t, t.get_meta(&"eric_home"))
			t.player.get_node("Finisher").min_press_interval = 0.0
			await wd.open_winded(t)
		else:
			await reset(t)
			t.sm.on_child_transition(t.sm.current_state, state)
			await t.wait_until(func(): return t.boss.get_finisher_hurtbox().monitorable and t.sm.current_state.name == state, 120)
			hold(t)
		t.player.combo.reset()
		t.place_under(t.boss.get_finisher_hurtbox())
		await t.wait(6)
		for i in 2:
			await t.swing_any()
			await t.wait(6)
		var seen := {"states": [], "pow": false}
		var on_landed := func(_target, _dealt, charged: bool):
			seen.states.append(String(t.sm.current_state.name))
			seen.pow = seen.pow or charged
		t.player.combo.punch_landed.connect(on_landed)
		t.tap(KEY_Q)
		for f in k:
			await t.physics_frame
		await t.process_frame
		shut(t)
		await t.wait(30)
		var dazed: bool = finisher.phase == t.FINISHER_DAZED or await t.wait_until(func(): return finisher.phase == t.FINISHER_DAZED, 30)
		t.player.combo.punch_landed.disconnect(on_landed)
		var late: Array = seen.states.filter(func(name): return name != state)
		report.append("%d: %s%s%s" % [k, seen.states, " POW" if seen.pow else "", " dazed" if dazed else ""])
		t.check(late.is_empty() and (not seen.pow or dazed), "shut %d frames after the press: no punch lands once it has (landed in %s, POW %s, dazed %s), and a POW that lands dazes him" % [k, seen.states, seen.pow, dazed])
		await t.wait_until(func(): return not finisher.is_active(), 900)
	t.log_p("the third punch, by the frame his %s shut: %s" % [state, report])
	if t.fight == "eric":
		await eric_whirl_live(t)


# His window's own clock run out in this idle step, as it would run out on its own: a clock the finisher holds doesn't.
static func shut(t) -> void:
	match t.fight:
		"matt":
			t.sm.recover_timer.start(0.001)
		"mason":
			t.sm.eat_timer.start(0.001)
		"eric":
			t.sm.downed_state_timer.start(0.001)


# The audit's repro (probe_eric_whirl): the whirlwind's throw, its chain going on to an Earthquake, three punches as fast
# as they go from under him the step his hurtbox opens. The third used to land as the throw ended, in his Idle, with no
# mash.
static func eric_whirl_live(t) -> void:
	var wd: GDScript = load(ERIC_MODES)
	var finisher: Node = t.player.get_node("Finisher")
	var home: Vector2 = t.get_meta(&"eric_home")
	await wd.park(t)
	await wd.reset(t, home)
	t.player.get_node("Finisher").min_press_interval = 0.0
	await t.settle_player(home + Vector2(-350, 40))
	t.player.combo.reset()
	t.sm.chain = ["Earthquake"]
	t.sm.throw_from_whirlwind()
	var hurtbox: Area2D = t.boss.get_finisher_hurtbox()
	await t.wait_until(func(): return hurtbox.monitorable, 120)
	var seen := {"states": [], "pow": false}
	var on_landed := func(_target, _dealt, charged: bool):
		seen.states.append(String(t.sm.current_state.name))
		seen.pow = seen.pow or charged
	t.player.combo.punch_landed.connect(on_landed)
	t.place_under(hurtbox)
	for i in 3:
		await t.swing_any()
	var dazed: bool = await t.wait_until(func(): return finisher.phase == t.FINISHER_DAZED, 30)
	t.player.combo.punch_landed.disconnect(on_landed)
	t.log_p("the whirlwind's throw, live: punches landed in %s, POW %s, dazed %s" % [seen.states, seen.pow, dazed])
	t.check(seen.states.all(func(name): return name == "SwordThrow") and (not seen.pow or dazed),
		"the whirlwind's throw, live: every punch lands while the sword is out of his hands, and a POW dazes him")
	await t.wait_until(func(): return not finisher.is_active(), 900)
