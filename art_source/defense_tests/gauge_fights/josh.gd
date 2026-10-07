extends RefCounted

# Josh's gauge spec for verify_defense.gd's gauge modes (break_gauge, break_entry, juggle, juggle_kill
# and gauge_extra with fight=josh). The keys and the optional statics are listed over GAUGE_FIGHTS_DIR
# there. He is on the N-reads rule with N = 8, and on BossBroken and BossJuggled. His body stands on his
# floor point and everything of him that is drawn, his hurtbox too, rides on Air over it.
# Since the rework of 2026-09-28 his light attack here is Wild Cards (JoshCardsWildCards), which nothing guards or
# parries: it is read by dashing through it (light_read), and a guard is broken with someone else's attack. His
# Hand Slam (2026-09-29, JoshCardsHandSlam) has its own mode, josh_hands, and a Break inside it is two of the
# entry cases below.

const JoshHand := preload("res://Scripts/JoshHand.gd")

const SPEC := {
	"body": "Arena/JoshCardsScene/JoshCardsCharacterBody",
	# Lower than his juggle floor (about y 443), so a Break here leaves his feet where they are.
	"home": Vector2(960, 640),
	"light": &"josh_wild_card",
	"light_read": "dodge",
	"strong": &"",
	"foreign": &"mason_poo_blast",
	"guard_break_attack": &"mason_poo_blast",
	"punish_state": "Recover",
	"broken_state": "Broken",
	"cycle_states": ["WildCards", "HandSlam", "PortalMonte"],
	"defeated_state": "Defeated",
	"reads_to_break": 12,
	"art": "res://Scripts/JoshArtLayout.gd",
	"juggle_via": "clip",
	"drives_player": true,
}

# Near the right rope, where a full shove would carry his juggle frames over it.
const NEAR_ROPE := Vector2(1500, 640)
# His clones' spots for the Break taken with the cards in flight: the last high up, so the Break slides him
# down to his juggle floor, where the juggle is drawn at half its height.
const BREAK_SPOTS: Array[Vector2] = [Vector2(1500, 800), Vector2(300, 800), Vector2(1500, 400), Vector2(900, 850), Vector2(525, 334)]


static func park(t, home: Vector2) -> void:
	t.boss.ground_position = home
	t.boss.height = 0.0
	t.boss.place()


# His fight loads the way the ones whose intro is a state do, which leaves the VS card up and then its
# input grace: it holds the player, and the grace is counted in real time, so either would swallow the
# checks' first presses. A test may have pinned his clones' spots. Since 2026-09-29 his cycle alternates
# his Hand Slam with Wild Cards (JoshCardsStateMachine.ATTACK_ORDER), and these modes read Wild Cards
# whenever they start his cycle, so they pin it; and they read Wild Cards alone, so they pin its Gun Hands
# off (josh_guns tests them, and two entry cases below turn them on). Since 2026-10-04 two of his attacks run before
# each window (attacks_per_window); every mode that resets here reads one attack and its own ending, so it pins one
# (josh_monte's window tier tests the shipped number).
static func reset(t) -> void:
	await t.skip_vs_card()
	var wild: Node = t.sm.states["WildCards"]
	wild.forced_spots.clear()
	wild.forced_return = Vector2.INF
	if "ATTACK_ORDER" in t.sm:
		t.sm.ATTACK_ORDER.assign(["WildCards"])
		t.sm.cycles_started = 0
	if "attacks_per_window" in t.sm:
		t.sm.attacks_per_window = 1
		t.sm.attacks_since_window = 0
	if "wild_guns" in t.sm:
		t.sm.wild_guns = false


# The moments a Break can come in play: as he hops about leaving clones, with the cards in flight and him
# gone from the screen, with his Gun Hands charging and with their lasers live (turned on for these two), in
# his recovery, in his Hand Slam with a hand over the player tracking them and with a hand pinned on the floor
# after its slam, and in his Portal Monte with a mark up over a small gate.
static func entry_cases(t) -> Array:
	var sm = t.sm
	var wild: Node = sm.states["WildCards"]
	var hands: Node = sm.states["HandSlam"]
	var guns: Node = wild.guns
	var monte: Node = sm.states["PortalMonte"]
	return [
		["three clones down, him standing on the third", func(): sm.start_cycle(), func(): return sm.current_state == wild and wild.beat == wild.Beat.HOP and wild.clones.size() == 3],
		["the cards in flight, him off the screen", func(): sm.start_cycle(), func(): return sm.current_state == wild and wild.beat == wild.Beat.VOLLEY and wild.gone and not wild.cards.is_empty()],
		["the gun hands charging", func(): sm.wild_guns = true; sm.start_cycle(), func(): return sm.current_state == wild and guns.active and guns.phase == guns.Phase.CHARGE],
		["a laser live", func(): sm.wild_guns = true; sm.start_cycle(), func(): return sm.current_state == wild and guns.active and guns.phase == guns.Phase.FIRE],
		["a Monte mark up", func(): sm.on_child_transition(sm.current_state, "PortalMonte"), func(): return sm.current_state == monte and monte.beat == monte.Beat.SHOW],
		["recovering", func(): sm.on_child_transition(sm.current_state, "Recover"), func(): return sm.current_state.name == "Recover"],
		["a hand over the player, tracking", func(): sm.on_child_transition(sm.current_state, "HandSlam"), func(): return sm.current_state == hands and hands.beat == hands.Beat.TRACK and hands.slam == 1],
		["a hand pinned after its slam", func(): sm.on_child_transition(sm.current_state, "HandSlam"), func(): return sm.current_state == hands and hands.impact_times.size() == 1 and sm.hands.hand_of(hands.order[0]) != null and sm.hands.hand_of(hands.order[0]).mode == JoshHand.Mode.GROUND],
	]


# Killed in the air, he lies on the juggle's `down` loop rather than playing his own defeat, and the deck
# still rains down over him.
static func after_kill(t) -> void:
	var rained: Array = t.boss.floor_layer.get_children().filter(func(c): return c is Sprite2D and c.texture and c.texture.resource_path.ends_with("card_burst_rain.png"))
	t.check(t.boss.current_anim != &"defeat" and rained.size() == 1, "lying there, he never plays his own defeat, and the deck rains down over him (%s, %d)" % [t.boss.current_anim, rained.size()])


static func extra(t) -> void:
	var boss = t.boss
	var sm = t.sm
	var gauge = boss.break_gauge
	var broken = sm.states["Broken"]
	var juggled = sm.states["Juggled"]
	var wild: Node = sm.states["WildCards"]
	var finisher: Node = t.player.get_node("Finisher")
	var art: GDScript = load(SPEC.art)

	t.log_p("-- Broken with his cards in flight and him off the screen, he is back where he left, down on his floor")
	await t.settle_player(Vector2(600, 760))
	wild.forced_spots.assign(BREAK_SPOTS)
	sm.start_cycle()
	var off: bool = await t.wait_until(func(): return sm.current_state == wild and wild.gone and not wild.cards.is_empty(), 600)
	var last_spot: Vector2 = boss.ground_position
	gauge.add(gauge.max_value)
	var broke: bool = await t.wait_until(func(): return sm.current_state == broken, 30)
	var shown: bool = boss.air.visible and boss.shadow.visible and boss.hurtbox.is_in_group("boss_target")
	var head: Vector2 = broken.head_point()
	var drawn_head: Vector2 = boss.air.global_position + art.mirrored(art.DAZE_ANCHOR, boss.sprite.flip_h)
	await t.wait(2)
	var left: Array = t.live_hazards()
	var landed: bool = await t.wait_until(func(): return broken.slide_left <= 0.0, 120)
	var driven: bool = await t.wait_until(func(): return not t.player.is_action_locked, 120)
	var shape: CollisionShape2D = boss.hurtbox.get_node("CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	var stand_off: float = t.player.global_position.y + broken.PLAYER_FEET_OFFSET - broken.PLAYER_IN_FRONT - box.end.y
	var floor_y: float = juggled.floor_y()
	t.log_p("gone from %s; Broken at %s, height %.0f, juggle floor y %.1f; hazards left %d; the player driven to %s, %.1f px off his ground line" % [last_spot, boss.ground_position, boss.height, floor_y, left.size(), t.player.global_position, stand_off])
	t.check(off and broke, "Broken while the cards fly and he is gone")
	t.check(shown, "he is back in view where he left, with his shadow, and the player faces him again")
	t.check(left.is_empty(), "every clone, lane and card is gone (%s)" % [left.map(func(h): return h.name)])
	t.check(head.distance_to(drawn_head) < 0.5, "the Break's zoom and its stars are on his head as he is drawn (%s)" % head)
	t.check(landed and boss.height == 0.0 and boss.ground_position.y >= roundf(floor_y) - 0.5, "down on his floor, at or below his juggle floor (y %.0f)" % boss.ground_position.y)
	t.check(driven and absf(stand_off) <= 1.0, "the player is driven in beside him, on that ground line")
	await t.wait(2)
	t.check(broken.stars.global_position == broken.head_point().round(), "his stars over his hat")
	var reached: bool = await _opener(t)
	t.check(reached and finisher.tiered, "the opener reaches him there, and the Break's mash is the tiered one")
	var shadows := []
	# The shove's last step is taken on the frame its tween stops running, and trails like the rest.
	var shove := {"was": false}
	var watch_shadow := func():
		var leap: Sprite2D = juggled.shadow
		if sm.current_state == juggled and is_instance_valid(leap) and leap.visible:
			var own: Sprite2D = boss.shadow_sprite
			var shoved: bool = boss.knock_tween != null and boss.knock_tween.is_running()
			shadows.append({"off": leap.global_position - boss.shadow.global_position, "own_shown": boss.shadow.visible,
				"same": leap.texture == own.texture and leap.modulate.a == 1.0 and leap.offset * leap.scale == own.position,
				"shoved": shoved or shove.was})
			shove.was = shoved
	t.physics_frame.connect(watch_shadow)
	await t.mash_tiered(5)
	await t.wait_until(func(): return sm.current_state.name != "Juggled" and finisher.phase == t.FINISHER_OFF, 600)
	t.physics_frame.disconnect(watch_shadow)
	# While the last uppercut's shove slides him, the tween moves his floor point after the frame's lift
	# has placed the shadow, so it trails a frame's worth of the shove behind, its last step too. That is
	# not the crash.
	var shoved: Array = shadows.filter(func(s): return s.shoved)
	var settled: Array = shadows.filter(func(s): return not s.shoved)
	var trail := 0.0
	for s in shoved:
		trail = maxf(trail, s.off.length())
	t.log_p("lift scale %.2f at his floor; the juggle's shadow up for %d frames, %d of them under the shove, trailing it by up to %.0f px" % [finisher.lift_scale, shadows.size(), shoved.size(), trail])
	var astray: Array = []
	for k in shadows.size():
		if not shadows[k].shoved and shadows[k].off != Vector2.ZERO:
			astray.append([k, shadows[k].off])
	t.log_p("frames off his own shadow without a shove: %s" % [astray])
	t.check(finisher.lift_scale >= 0.49, "the juggle is drawn at least half its height there (%.2f)" % finisher.lift_scale)
	t.check(not shadows.is_empty() and shadows.all(func(s): return s.same and not s.own_shown), "while he is up, the juggle's shadow is his own sheet, drawn as his is, with his own hidden")
	t.check(not settled.is_empty() and settled.all(func(s): return s.off == Vector2.ZERO), "and it lies exactly where his does, but for the frames the last shove is sliding him")
	t.check(not shadows.is_empty() and shadows[-1].off == Vector2.ZERO and boss.shadow.visible, "so his own comes back as he crashes on the very spot, without a pixel's jump")

	# From here the first uppercut takes him a point past half, where the phase floor used to stop it, and the whole
	# juggle leaves him standing for the checks after it: worked out from his health and the finisher's shares, so
	# neither retuned breaks it.
	var half: int = floori(boss.get_max_health() * boss.PHASE_TWO_RATIO)
	var past_half: int = half + maxi(1, roundi(boss.get_max_health() * finisher.juggle_shares[0])) - 1
	t.log_p("-- no phase floor any more: a juggle from %d HP deals every uppercut's whole share, on past half" % past_half)
	await t.reset_gauged(SPEC.home)
	t.check(await t.break_into_prompt_fight(SPEC), "a Break and the opener put up the prompt")
	boss.boss_health = past_half
	var healths := []
	var record := func(_index: int, _last: bool): healths.append(boss.boss_health)
	finisher.juggle_hit.connect(record)
	await t.mash_tiered(5)
	await t.wait_until(func(): return sm.current_state.name != "Juggled" and healths.size() > 0, 600)
	finisher.juggle_hit.disconnect(record)
	var want := []
	var health: int = past_half
	for k in 3:
		health = maxi(health - maxi(1, roundi(boss.get_max_health() * finisher.juggle_shares[k])), 0)
		want.append(health)
	t.log_p("health after each uppercut %s, want %s" % [healths, want])
	t.check(healths == want and want[0] < half and want[2] > 0, "each uppercut deals its whole share, straight past %d, and he is still standing (%s)" % [half, healths])
	await t.wait_until(func(): return finisher.phase == t.FINISHER_OFF, 300)

	t.log_p("-- and at half his health his recovery can still be dazed")
	await t.reset_gauged(SPEC.home)
	boss.boss_health = floori(boss.get_max_health() * boss.PHASE_TWO_RATIO)
	sm.on_child_transition(sm.current_state, "Recover")
	sm.recover_timer.stop()
	t.check(boss.can_be_dazed(), "recovering at %d, a daze is open" % boss.boss_health)
	sm.on_child_transition(sm.current_state, "Idle")

	t.log_p("-- by the rope, the last uppercut's shove stops with his juggle frames still inside the ropes")
	await t.reset_gauged(NEAR_ROPE)
	var near: Dictionary = SPEC.duplicate()
	near.home = NEAR_ROPE
	t.check(await t.break_into_prompt_fight(near), "a Break and the opener put up the prompt")
	var start_x: float = boss.ground_position.x
	var facing_left: bool = boss.sprite.flip_h
	await t.mash_tiered(5)
	await t.wait_until(func(): return sm.current_state.name != "Juggled" and finisher.phase == t.FINISHER_OFF, 600)
	var drawn: Rect2 = art.JUGGLE_DRAWN
	var middle: float = art.juggle().frame_size.x / 2.0
	var reach: float = (middle - drawn.position.x if facing_left else drawn.end.x - middle) * art.SCALE
	var line: float = sm.ROPES.end.x - reach
	t.log_p("from x %.0f, facing left %s: shoved to %.1f; the line his frames reach the rope at is %.1f" % [start_x, facing_left, boss.ground_position.x, line])
	t.check(facing_left and boss.ground_position.x > start_x and absf(boss.ground_position.x - line) <= 0.5, "shoved away from the player, and stopped where his frames reach the rope (%.1f against %.1f)" % [boss.ground_position.x, line])

	t.log_p("-- a Break by a rope slides him in off it, so the whole of his juggle is drawn inside the ropes")
	var ground: Rect2 = boss.ground_bounds(0.0)
	var by_rope := "standing as close to the left rope as he can"
	await t.reset_gauged(SPEC.home)
	await t.settle_player(Vector2(700, 700))
	boss.ground_position = Vector2(ground.position.x, SPEC.home.y)
	boss.height = 0.0
	boss.place()
	# Whether the player stands on the spot beside him yet, on each frame of his slide.
	var arrivals := []
	var watch_drive := func():
		if sm.current_state == broken and broken.slide_time > 0.0:
			arrivals.append({"sliding": broken.slide_left > 0.0, "arrived": t.player.global_position == broken.drive_to.round()})
	t.physics_frame.connect(watch_drive)
	gauge.add(gauge.max_value)
	var down: bool = await t.wait_until(func(): return sm.current_state == broken, 30)
	var slid_in: bool = await t.wait_until(func(): return broken.slide_left <= 0.0, 120)
	await t.wait(2)
	t.physics_frame.disconnect(watch_drive)
	var inside: Vector2 = boss.juggle_x_range()
	var drawn_from: float = boss.ground_position.x - (inside.x - sm.ROPES.position.x)
	var want_time: float = maxf(broken.DRIVE_TIME, broken.slide_from.distance_to(broken.slide_to) / sm.dive_speed)
	var early: Array = arrivals.filter(func(s): return s.sliding and s.arrived)
	var shape_now: CollisionShape2D = boss.hurtbox.get_node("CollisionShape2D")
	var box_now: Rect2 = shape_now.global_transform * shape_now.shape.get_rect()
	var standing_off: float = t.player.global_position.y + broken.PLAYER_FEET_OFFSET - broken.PLAYER_IN_FRONT - box_now.end.y
	t.log_p("%s: from %s he slides %.0f px in and %.0f down in %.2f s, to %s, where his juggle is drawn from x %.0f (the rope is at %.0f); the player arrives at %s, %d frames before he lands, %.1f px off his ground line" % [by_rope, broken.slide_from, broken.slide_to.x - broken.slide_from.x, broken.slide_to.y - broken.slide_from.y, broken.slide_time, boss.ground_position, drawn_from, sm.ROPES.position.x, t.player.global_position, early.size(), standing_off])
	t.check(down and slid_in and not boss.sprite.flip_h and boss.ground_position.x == inside.x and drawn_from == sm.ROPES.position.x, "%s, facing the player, he ends where his widest juggle frame reaches the rope and no further" % by_rope)
	t.check(absf(broken.slide_time - want_time) < 1e-6, "%s: his slide takes %.2f s, the drive's beat or his dive speed, whichever is longer" % [by_rope, want_time])
	t.check(early.is_empty() and t.player.global_position == broken.drive_to.round() and absf(standing_off) <= 1.0, "%s: the player arrives beside him as he lands, not before, on his ground line" % by_rope)


# The opener, landed from wherever the Break's drive left the player: the finisher's prompt goes up.
static func _opener(t) -> bool:
	for i in 3:
		await t.swing()
		if i < 2:
			await t.wait(6)
	return await t.wait_until(func(): return t.player.get_node("Finisher").phase == t.FINISHER_DAZED and t.player.get_node("Finisher").prompt_visible, 120)
