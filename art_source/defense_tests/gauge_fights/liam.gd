extends RefCounted

# Liam & Bixby's gauge spec for verify_defense.gd's gauge modes (break_gauge, break_entry, juggle,
# juggle_kill and gauge_extra with fight=liam). The keys and the optional statics are listed over
# GAUGE_FIGHTS_DIR there. Beast Bixby flies: his node is his floor point (ground_position) and his feet
# are `height` over it, so he is parked through those. His Break brings him down to the floor a juggle
# needs, falling if he was in the air and hopping if he was on the ground higher up the arena.

const SPEC := {
	"body": "Arena/BixbyBeastScene/BixbyBeastCharacterBody",
	# Below his juggle floor (about 713), so a Break leaves him where he is.
	"home": Vector2(960, 760),
	# His one attack that is parried, blocked and landed, and fills and drains.
	"light": &"bixby_fire_breath",
	"strong": &"",
	"foreign": &"josh_card_throw",
	"punish_state": "Recover",
	"broken_state": "Broken",
	"cycle_states": ["Takeoff"],
	"defeated_state": "Defeated",
	"reads_to_break": 8,
	"art": "res://Scripts/BixbyBeastArtLayout.gd",
	"juggle_via": "clip",
	"drives_player": true,
}

const BixbyBeastArtLayout := preload("res://Scripts/BixbyBeastArtLayout.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")

# juggle_kill's frames from the killing blow on (before_kill), read back in after_kill.
static var kill_trace: Array = []
static var kill_watch: Callable
# His spin's length as the fight has it: break_entry's dizzy case shortens it to reach the dizzy spell in
# time, and every reset puts it back.
static var spin_time := -1.0


# Standing on the floor at `home`, slumped, the way he waits between attacks after a finisher.
static func park(t, home: Vector2) -> void:
	var boss = t.boss
	boss.height = 0.0
	boss.fly_velocity = Vector2.ZERO
	boss.ground_position = home
	boss.place()
	boss.play_anim(&"recover")


# A parry of the fire breath earlier in the run has spent that breath's one read. His fight loads the way
# the ones whose intro is a state do, which leaves the VS card's input grace up: it is counted in real
# time and would swallow the checks' first presses.
static func reset(t) -> void:
	await t.skip_vs_card()
	t.boss.breath_read = false
	if spin_time < 0.0:
		spin_time = t.sm.combined_spin_time
	t.sm.combined_spin_time = spin_time


# Only moments a read can Break him in: parrying his breath, dodging his cone, dashing through his rings or
# beams (which roll on across the floor after the combined attack, through his dizzy spell, his takeoff and
# his hover), and punching him in a window. The airborne ones fall to his juggle floor, the ones on the
# ground high up the arena hop down to it, and the rest are low enough already.
static func entry_cases(t) -> Array:
	var sm = t.sm
	var boss = t.boss
	var combined = sm.states["Combined"]
	var inferno = sm.states["Inferno"]
	var hover_high := func():
		boss.height = boss.HOVER_HEIGHT_PX
		boss.ground_position = Vector2(960, 600)
		boss.place()
		sm.on_child_transition(sm.current_state, "Hover")
	var take_off := func():
		boss.ground_position = Vector2(960, 640)
		boss.place()
		sm.on_child_transition(sm.current_state, "Takeoff")
	var rising := func(): return sm.current_state.name == "Takeoff" and boss.height > 0.0
	var breathe := func():
		boss.height = boss.HOVER_HEIGHT_PX
		boss.place()
		sm.attacks = []
		sm.on_child_transition(sm.current_state, "FireBreath")
	var pound_high := func():
		boss.ground_position = Vector2(960, 520)
		boss.place()
		sm.attacks = []
		sm.on_child_transition(sm.current_state, "Combined")
	var pounding := func(): return sm.current_state == combined and combined.phase == combined.Phase.POUNDS and not t.hazards_of("BixbyQuakeRingScript.gd").is_empty()
	var spinning := func():
		return sm.current_state == combined and combined.phase == combined.Phase.SPIN \
			and t.hazards_of("BixbyQuakeRingScript.gd").size() >= 3 and t.hazards_of("BixbySonicSweepScript.gd").size() == 1
	var spin_short := func():
		sm.combined_spin_time = 1.0
		sm.attacks = []
		sm.on_child_transition(sm.current_state, "Combined")
	var take_rope := func():
		boss.height = boss.HOVER_HEIGHT_PX
		boss.place()
		sm.attacks = []
		sm.on_child_transition(sm.current_state, "Inferno")
	var cone_lit := func(): return sm.current_state == inferno and inferno.phase == inferno.Phase.BREATH and not t.hazards_of("BixbyInfernoFloodScript.gd").is_empty()
	return [
		["hovering high over the arena", hover_high, func(): return sm.current_state.name == "Hover"],
		["taking off", take_off, rising],
		["the fire breath's stream", breathe, func(): return sm.current_state.name == "FireBreath" and boss.current_anim == &"stream"],
		["the combined attack's pounds, high up the arena", pound_high, pounding],
		["the combined attack's spin, high up the arena", pound_high, spinning],
		["the dizzy spell his spin ends on", spin_short, func(): return sm.current_state == combined and combined.is_dizzy()],
		["the Inferno's breath, on the rope", take_rope, cone_lit],
		["the landing's recovery", func(): sm.on_child_transition(sm.current_state, "Recover"), func(): return sm.current_state.name == "Recover"],
		["between two cycles", func(): sm.on_child_transition(sm.current_state, "Idle"), func(): return sm.current_state.name == "Idle"],
	]


static func before_kill(t) -> void:
	var boss = t.boss
	var sm = t.sm
	var juggled = sm.states["Juggled"]
	kill_trace.clear()
	kill_watch = func():
		kill_trace.append({"t": t.defense.clock, "state": str(sm.current_state.name), "anim": boss.current_anim,
			"step": boss.anim_step, "lingering": juggled.lingering, "clip": juggled.clip_name,
			"outros": t.root.get_children().filter(func(c): return c.name == "FightOutro").size()})
	t.physics_frame.connect(kill_watch)


# Beaten in the air, he lies belly-up on the juggle's down loop for a beat, his defeat cuts in on its smoke
# cloud, Liam is coughed up, and only then does the one outro start.
static func after_kill(t) -> void:
	var sm = t.sm
	var outro_up: bool = await t.wait_until(func(): return t.root.has_node("FightOutro"), 300)
	await t.wait(60)
	t.physics_frame.disconnect(kill_watch)
	var hold: float = sm.states["Defeated"].JUGGLE_DEFEAT_HOLD
	var beaten: Array = kill_trace.filter(func(s): return s.state == "Defeated")
	var cut: Array = beaten.filter(func(s): return s.anim == &"defeat")
	var landed: Array = cut.filter(func(s): return s.step >= BixbyBeastArtLayout.DEFEAT_LIAM_LANDS_FRAME)
	var outro_at: Array = kill_trace.filter(func(s): return s.outros > 0)
	var held_for: float = cut[0].t - beaten[0].t if not cut.is_empty() and not beaten.is_empty() else -1.0
	var coughed_for: float = landed[0].t - cut[0].t if not landed.is_empty() else -1.0
	var outros: int = t.root.get_children().filter(func(c): return c.name == "FightOutro").size()
	t.log_p("lying %.3f s on the juggle's %s, cut to defeat step %d, Liam down %.3f s after that, outro up %s, outros %d" % [
		held_for, beaten[0].clip if not beaten.is_empty() else &"", cut[0].step if not cut.is_empty() else -1,
		coughed_for, outro_up, outros])
	t.check(not beaten.is_empty() and beaten[0].lingering and beaten[0].clip == &"down", "beaten, he lies belly-up on the juggle's down loop")
	t.check(absf(held_for - hold) <= t.FRAME_TIME + 0.001, "for %.1f s (%.3f)" % [hold, held_for])
	t.check(not cut.is_empty() and cut[0].step == BixbyBeastArtLayout.DEFEAT_SMOKE_FRAME and cut.all(func(s): return not s.lingering), "then his defeat cuts in on its smoke cloud, and the juggle sheet is gone")
	t.check(outro_up and not landed.is_empty() and not outro_at.is_empty() and outro_at[0].t >= landed[0].t, "the outro starts only once Liam has been coughed up and has landed")
	t.check(outros == 1 and kill_trace.all(func(s): return s.outros <= 1), "exactly one outro (%d)" % outros)


static func extra(t) -> void:
	var boss = t.boss
	var sm = t.sm
	var gauge = boss.break_gauge
	var broken = sm.states["Broken"]
	var juggled = sm.states["Juggled"]
	var home: Vector2 = t.fight_spec.home

	t.log_p("-- what fills it, and what only drains it")
	var source: Node2D = t.dummy_source()
	var earning: Array = [&"bixby_fire_breath", &"bixby_sonic_beam", &"bixby_quake_ring", &"bixby_inferno"]
	var draining: Array = [&"bixby_fireball", &"bixby_ember", &"bixby_quake_burst"]
	t.check(earning.all(func(id): return gauge.earns_from.call(HitInfo.make(id, source, Vector2.ZERO))), "a read of any of %s fills it" % [earning])
	t.check(draining.all(func(id): return not gauge.earns_from.call(HitInfo.make(id, source, Vector2.ZERO)) and gauge.owns_attack.call(id)), "%s never fill it, but land and drain it" % [draining])
	t.check(not gauge.earns_from.call(HitInfo.make(&"josh_card_throw", source, Vector2.ZERO)) and not gauge.owns_attack.call(&"josh_card_throw"), "and someone else's attack does neither")

	t.log_p("-- a fire breath is one read, however often its stream is parried")
	await t.reset_gauged(home)
	await t.settle_player(Vector2(640, 700))
	t.check(await t.parry_once(&"bixby_fire_breath") == 3 and is_equal_approx(gauge.value, gauge.parry_gain), "a breath's first parry: %.3f" % gauge.value)
	t.clear_iframes()
	await t.wait(40)
	t.check(await t.parry_once(&"bixby_fire_breath") == 3 and is_equal_approx(gauge.value, gauge.parry_gain), "a second parry of the same breath adds nothing (%.3f)" % gauge.value)
	t.clear_iframes()
	sm.on_child_transition(sm.current_state, "FireBreath")
	await t.wait(2)
	sm.on_child_transition(sm.current_state, "Idle")
	park(t, home)
	await t.wait(40)
	t.check(await t.parry_once(&"bixby_fire_breath") == 3 and is_equal_approx(gauge.value, 2.0 * gauge.parry_gain), "the next breath's is a read again (%.3f)" % gauge.value)
	t.clear_iframes()

	t.log_p("-- Broken in the air, he falls onto his juggle floor on his landing's curve")
	var hover := func():
		boss.height = boss.HOVER_HEIGHT_PX
		boss.ground_position = Vector2(1100, 560)
		boss.place()
		sm.on_child_transition(sm.current_state, "Hover")
	var fall: Dictionary = await _break_and_watch(t, hover)
	var floor_y: float = juggled.floor_y()
	var fall_time: float = BixbyBeastArtLayout.time_to_step(&"land", 1)
	var up: float = fall.samples[0].height if not fall.samples.is_empty() else 0.0
	var halfway: Array = fall.samples.filter(func(s): return fall.touch >= 0 and absf(s.t - fall.samples[0].t - fall_time / 2.0) <= t.FRAME_TIME / 2.0 + 0.001)
	var impact: Array = fall.samples.filter(func(s): return s.anim == &"land" and s.step >= 1)
	var touch: Dictionary = fall.samples[fall.touch] if fall.touch >= 0 else {}
	t.log_p("from %s at %.0f px up to %s: %.3f s, %.1f px up halfway; the impact frame %.3f s after touching down, the thud %s; the player %.1f px off his ground line" % [broken.slide_from, up, broken.slide_to, fall.took, halfway[0].height if not halfway.is_empty() else -1.0, impact[0].t - touch.t if not impact.is_empty() and not touch.is_empty() else -1.0, touch.get("thud", false), fall.stand_off])
	t.check(fall.broke and boss.ground_position == Vector2(roundf(broken.slide_from.x), roundf(floor_y)) and boss.height == 0.0, "down on y %.0f, his juggle floor (%s)" % [roundf(floor_y), boss.ground_position])
	t.check(up == boss.HOVER_HEIGHT_PX and absf(fall.took - fall_time) <= t.FRAME_TIME + 0.001, "from his full height in %.2f s, as his landing falls (%.3f)" % [fall_time, fall.took])
	t.check(not halfway.is_empty() and absf(halfway[0].height - 0.75 * up) <= 4.0, "falling faster as he comes: three quarters of his height left halfway, on Land's curve")
	t.check(not impact.is_empty() and absf(impact[0].t - touch.get("t", INF)) <= t.FRAME_TIME + 0.001 and touch.get("thud", false) and fall.thuds_before == 0, "onto the landing's impact, with its thud as he touches down and not before")
	t.check(absf(fall.stand_off) <= 1.0, "and the player is driven in beside where he lands, not where he was in the air")
	var lift_scale: float = juggled.headroom() / t.player.finisher.planned_apex(3)
	t.check(lift_scale >= 0.49, "where a three-uppercut juggle is drawn at least half its height (%.2f)" % lift_scale)

	t.log_p("-- Broken on the ground high up the arena, he hops down to it")
	var spin_high := func():
		boss.ground_position = Vector2(900, 480)
		boss.place()
		sm.attacks = []
		sm.on_child_transition(sm.current_state, "Combined")
	var spinning := func(): return sm.current_state.name == "Combined" and sm.current_state.phase == sm.current_state.Phase.SPIN
	var hop: Dictionary = await _break_and_watch(t, spin_high, spinning)
	var top: float = hop.samples.map(func(s): return s.height).max() if not hop.samples.is_empty() else 0.0
	var landing: Dictionary = hop.samples[hop.touch] if hop.touch >= 0 else {}
	var hopping: Array = hop.samples.slice(0, maxi(hop.touch, 0)).filter(func(s): return s.height > 0.0)
	t.log_p("from %s to %s: %.3f s, %.1f px at the top, landed on %s step %s with the thud %s; the player %.1f px off his ground line" % [broken.slide_from, broken.slide_to, hop.took, top, landing.get("anim", &""), landing.get("step", -1), landing.get("thud", false), hop.stand_off])
	t.check(hop.broke and boss.ground_position == Vector2(900, roundf(floor_y)) and boss.height == 0.0, "down on y %.0f (%s)" % [roundf(floor_y), boss.ground_position])
	t.check(absf(hop.took - broken.HOP_TIME) <= t.FRAME_TIME + 0.001 and absf(top - broken.HOP_HEIGHT) <= 2.0, "in a %.2f s hop about %.0f px high (%.3f s, %.1f px)" % [broken.HOP_TIME, broken.HOP_HEIGHT, hop.took, top])
	t.check(not hopping.is_empty() and hopping.all(func(s): return s.anim == &"hop") and landing.get("anim", &"") == &"land" and landing.get("step", -1) == 1 and landing.get("thud", false) and hop.thuds_before == 0, "on the landing's flared frame, onto its impact and thud")
	t.check(absf(hop.stand_off) <= 1.0, "and the player is driven in beside where he lands")

	t.log_p("-- Broken already low enough, he stays where he is")
	var stay: Dictionary = await _break_and_watch(t, func(): pass)
	t.check(stay.broke and boss.ground_position == home and stay.samples.all(func(s): return s.height == 0.0 and not s.thud and s.anim == &"recover"), "no fall, no hop and no thud: slumped where he stood (%s)" % boss.ground_position)

	t.log_p("-- the Break gauge fades with his bar while he hangs off the rope")
	await t.reset_gauged(home)
	boss._fade_hud(sm.inferno_hud_fade_alpha)
	await t.wait(roundi(boss.HUD_FADE_TIME / t.FRAME_TIME) + 2)
	var faded: float = boss.gauge_bar.modulate.a
	boss._fade_hud(1.0)
	await t.wait(roundi(boss.HUD_FADE_TIME / t.FRAME_TIME) + 2)
	t.check(is_equal_approx(faded, sm.inferno_hud_fade_alpha) and is_equal_approx(boss.gauge_bar.modulate.a, 1.0), "faded to %.2f with it, and back (%.2f, %.2f)" % [sm.inferno_hud_fade_alpha, faded, boss.gauge_bar.modulate.a])

	t.log_p("-- juggled, the leap shadow stands in for his own, on his shadows' layer")
	await t.reset_gauged(home)
	t.check(await t.break_into_prompt_fight(t.fight_spec), "a Break and the opener put up the prompt")
	var seen := {"up": 0, "own_shown": 0, "leap_shown": 0, "off_layer": 0, "crash": 0, "crash_wrong": 0}
	var watch := func():
		if sm.current_state != juggled:
			return
		if juggled.drawn_lift > 0.0:
			seen.up += 1
			seen.own_shown += int(boss.shadow.visible)
			seen.leap_shown += int(is_instance_valid(juggled.shadow) and juggled.shadow.visible)
			seen.off_layer += int(not is_instance_valid(juggled.shadow) or juggled.shadow.get_parent() != boss.shadow.get_parent())
		elif juggled.clip_name == &"crash":
			seen.crash += 1
			var own: Sprite2D = boss.shadow
			seen.crash_wrong += int(not own.visible or own.texture != boss.shadow_sheets[BixbyBeastArtLayout.Shadow.GROUND] or own.frame != 1)
	t.physics_frame.connect(watch)
	await t.mash_tiered(5)
	var up_again: bool = await t.wait_until(func(): return sm.current_state.name == "Takeoff", 600)
	t.physics_frame.disconnect(watch)
	t.log_p("%s" % [seen])
	t.check(seen.up > 0 and seen.own_shown == 0 and seen.leap_shown == seen.up and seen.off_layer == 0, "in the air his own shadow is hidden and the leap shadow shows, on his shadows' layer")
	t.check(seen.crash > 0 and seen.crash_wrong == 0, "on the crash his own is back as the exhausted, wings-flat one")
	t.check(up_again and boss.shadow.visible, "and it is still there as he takes off again")


# Starts him with `start` (then waits for `ready`, if given), Breaks him and follows him frame by frame
# while he's Broken: {broke, samples: [{t, height, anim, step, thud}], touch: the sample he first stands on
# the floor in after last being off it (-1 if never), took: the game seconds from the Break to that,
# thuds_before: samples with the thud playing before it, stand_off: how far the player's feet were driven
# from the ground line of his hurtbox as it ended up}.
static func _break_and_watch(t, start: Callable, ready := Callable()) -> Dictionary:
	var boss = t.boss
	var sm = t.sm
	var broken = sm.states["Broken"]
	await t.reset_gauged(t.fight_spec.home)
	await t.settle_player(Vector2(600, 860))
	start.call()
	if ready.is_valid():
		await t.wait_until(ready, 600)
	await t.wait(1)
	# Headless, a sound can still count as playing long after it was last heard.
	boss.land_sfx_player.stop()
	var samples := []
	var watch := func():
		if sm.current_state == broken:
			samples.append({"t": t.defense.clock, "height": boss.height, "anim": boss.current_anim, "step": boss.anim_step, "thud": boss.land_sfx_player.playing})
	t.physics_frame.connect(watch)
	boss.break_gauge.add(boss.break_gauge.max_value)
	var broke: bool = await t.wait_until(func(): return sm.current_state == broken, 30)
	await t.wait_until(func(): return not t.player.is_action_locked, 120)
	await t.wait(40)
	t.physics_frame.disconnect(watch)
	var last_up := -1
	for i in samples.size():
		if samples[i].height > 0.0:
			last_up = i
	var touch := last_up + 1 if last_up >= 0 and last_up + 1 < samples.size() else -1
	var box: Rect2 = t.area_rect(boss.hurtbox)
	return {
		"broke": broke,
		"samples": samples,
		"touch": touch,
		"took": samples[touch].t - samples[0].t if touch >= 0 else -1.0,
		"thuds_before": samples.slice(0, maxi(touch, 0)).filter(func(s): return s.thud).size(),
		"stand_off": t.player.global_position.y + broken.PLAYER_FEET_OFFSET - broken.PLAYER_IN_FRONT - box.end.y,
	}
