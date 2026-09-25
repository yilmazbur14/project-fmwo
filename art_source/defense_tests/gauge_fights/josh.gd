extends RefCounted

# Josh's gauge spec for verify_defense.gd's gauge modes (break_gauge, break_entry, juggle, juggle_kill
# and gauge_extra with fight=josh). The keys and the optional statics are listed over GAUGE_FIGHTS_DIR
# there. He is on the N-reads rule with N = 8, and on BossBroken and BossJuggled. His body stands on his
# floor point and everything of him that is drawn, his hurtbox too, rides on Air at his height over it.

const SPEC := {
	"body": "Arena/JoshCardsScene/JoshCardsCharacterBody",
	# Lower than his juggle floor (about y 443), so a Break here leaves his feet where they are.
	"home": Vector2(960, 640),
	"light": &"josh_card_throw",
	"strong": &"",
	"foreign": &"mason_poo_blast",
	"punish_state": "Recover",
	"broken_state": "Broken",
	"cycle_states": ["Mount"],
	"defeated_state": "Defeated",
	"reads_to_break": 8,
	"art": "res://Scripts/JoshArtLayout.gd",
	"juggle_via": "clip",
	"drives_player": true,
}

# The card storm's first pass row, the highest he rides: a Break there drops him off his card and down
# to his juggle floor.
const TOP_ROW := 365.0
# Near the right rope, where a full shove would carry his juggle frames over it.
const NEAR_ROPE := Vector2(1500, 640)


static func park(t, home: Vector2) -> void:
	t.boss.ground_position = home
	t.boss.height = 0.0
	t.boss.place()


# His phase is read off his health at the top of each cycle, so it is put back by hand. His fight loads
# the way the ones whose intro is a state do, which leaves the VS card up and then its input grace: it
# holds the player, and the grace is counted in real time, so either would swallow the checks' first
# presses.
static func reset(t) -> void:
	await t.skip_vs_card()
	t.sm.cycle_phase = 0


# The moments a Break can come in play, which are the moments something of his can be read: a giant card
# coming down while he rides his storm (dodged), his throw's second wind-up with the first card still in
# flight (parried), and his recovery (punched). Nothing fills the gauge while he mounts, lays his cards,
# runs the monte or dives off his card.
static func entry_cases(t) -> Array:
	var sm = t.sm
	return [
		["a giant card coming down as he rides the top row", func(): _start_cycle(t, false), func(): return _on_top_row(t) and sm.current_state.falling],
		["his second wind-up, the first card still in flight", func(): sm.on_child_transition(sm.current_state, "Throw"), func(): return sm.current_state.name == "Throw" and sm.current_state.told == 2 and sm.current_state.thrown == 1 and not t.hazards_of("JoshThrownCardScript.gd").is_empty()],
		["recovering", func(): sm.on_child_transition(sm.current_state, "Recover"), func(): return sm.current_state.name == "Recover"],
	]


# The kill has to be able to reach 0: past the phase floor, as in his phase-two cycles.
static func before_kill(t) -> void:
	t.sm.cycle_phase = 1


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
	var finisher: Node = t.player.get_node("Finisher")
	var art: GDScript = load(SPEC.art)

	t.log_p("-- riding the card storm's top row, a Break drops him off his card onto his juggle floor")
	await t.settle_player(Vector2(600, 760))
	_start_cycle(t, false)
	var riding: bool = await t.wait_until(func(): return _on_top_row(t), 600)
	var floor_y: float = juggled.floor_y()
	var from_y: float = boss.ground_position.y
	var from_height: float = boss.height
	var drop := []
	var trace := func():
		if sm.current_state == broken and broken.slide_time > 0.0:
			drop.append({"w": clampf(1.0 - broken.slide_left / broken.slide_time, 0.0, 1.0), "height": boss.height})
	t.physics_frame.connect(trace)
	gauge.add(gauge.max_value)
	var broke: bool = await t.wait_until(func(): return sm.current_state == broken, 30)
	var head: Vector2 = broken.head_point()
	var drawn_head: Vector2 = boss.air.global_position + art.mirrored(art.DAZE_ANCHOR, boss.sprite.flip_h)
	var card_gone: bool = not boss.glider.visible
	var landed: bool = await t.wait_until(func(): return broken.slide_left <= 0.0, 120)
	var thud: bool = boss.land_sfx_player.playing
	t.physics_frame.disconnect(trace)
	var driven: bool = await t.wait_until(func(): return not t.player.is_action_locked, 120)
	var off_curve: Array = drop.filter(func(s): return absf(s.height - from_height * (1.0 - s.w * s.w)) > 0.5)
	var shape: CollisionShape2D = boss.hurtbox.get_node("CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	var stand_off: float = t.player.global_position.y + broken.PLAYER_FEET_OFFSET - broken.PLAYER_IN_FRONT - box.end.y
	t.log_p("from y %.0f at height %.0f to floor y %.1f: feet %s, height %.1f; %d samples, %d off the fall's curve; the player driven to %s, %.1f px off his ground line" % [from_y, from_height, floor_y, boss.ground_position, boss.height, drop.size(), off_curve.size(), t.player.global_position, stand_off])
	t.check(riding and broke and absf(from_y - TOP_ROW) < 2.0 and from_height == sm.glider_height, "Broken riding the top row, %.0f px up" % sm.glider_height)
	t.check(card_gone, "his card vanishes from under him at once")
	t.check(head.distance_to(drawn_head) < 0.5 and head.y < boss.global_position.y - from_height, "the Break's zoom and its stars are on his head as he is drawn, up with him (%s)" % head)
	t.check(landed and boss.ground_position == Vector2(boss.ground_position.x, roundf(floor_y)) and boss.height == 0.0, "he lands on his floor, y %.0f, at height 0" % roundf(floor_y))
	t.check(drop.size() >= 4 and off_curve.is_empty(), "falling as a fall does, faster the lower he gets (%d samples)" % drop.size())
	t.check(thud, "and lands with his landing thud")
	t.check(driven and absf(stand_off) <= 1.0, "the player is driven in beside where he lands, on that ground line")
	await t.wait(2)
	t.check(broken.stars.global_position == broken.head_point().round(), "his stars over his hat, down on the ground")
	var reached: bool = await _opener(t)
	t.check(reached and finisher.tiered, "the opener reaches him there, and the Break's mash is the tiered one")
	var shadows := []
	var watch_shadow := func():
		var leap: Sprite2D = juggled.shadow
		if sm.current_state == juggled and is_instance_valid(leap) and leap.visible:
			var own: Sprite2D = boss.shadow_sprite
			shadows.append({"off": leap.global_position - boss.shadow.global_position, "own_shown": boss.shadow.visible,
				"same": leap.texture == own.texture and leap.modulate.a == 1.0 and leap.offset * leap.scale == own.position,
				"shoved": boss.knock_tween != null and boss.knock_tween.is_running()})
	t.physics_frame.connect(watch_shadow)
	await t.mash_tiered(5)
	await t.wait_until(func(): return sm.current_state.name != "Juggled" and finisher.phase == t.FINISHER_OFF, 600)
	t.physics_frame.disconnect(watch_shadow)
	# While the last uppercut's shove slides him, the tween moves his floor point after the frame's lift
	# has placed the shadow, so it trails a frame's worth of the shove behind. That is not the crash.
	var shoved: Array = shadows.filter(func(s): return s.shoved)
	var settled: Array = shadows.filter(func(s): return not s.shoved)
	var trail := 0.0
	for s in shoved:
		trail = maxf(trail, s.off.length())
	t.log_p("lift scale %.2f at his floor; the juggle's shadow up for %d frames, %d of them under the shove, trailing it by up to %.0f px" % [finisher.lift_scale, shadows.size(), shoved.size(), trail])
	t.check(finisher.lift_scale >= 0.49, "the juggle is drawn at least half its height there (%.2f)" % finisher.lift_scale)
	t.check(not shadows.is_empty() and shadows.all(func(s): return s.same and not s.own_shown), "while he is up, the juggle's shadow is his own sheet, drawn as his is, with his own hidden")
	t.check(not settled.is_empty() and settled.all(func(s): return s.off == Vector2.ZERO), "and it lies exactly where his does, but for the frames the last shove is sliding him")
	t.check(not shadows.is_empty() and shadows[-1].off == Vector2.ZERO and boss.shadow.visible, "so his own comes back as he crashes on the very spot, without a pixel's jump")

	t.log_p("-- a juggle from 9 HP, over his phase floor of 7, never deals 0")
	await t.reset_gauged(SPEC.home)
	t.check(await t.break_into_prompt_fight(SPEC), "a Break and the opener put up the prompt")
	boss.boss_health = 9
	var floor_health: int = boss._lowest_health()
	var healths := []
	var record := func(_index: int, _last: bool): healths.append(boss.boss_health)
	finisher.juggle_hit.connect(record)
	await t.mash_tiered(5)
	await t.wait_until(func(): return sm.current_state.name != "Juggled" and healths.size() > 0, 600)
	finisher.juggle_hit.disconnect(record)
	var dealt := []
	var before := 9
	for health in healths:
		dealt.append(before - health)
		before = health
	t.log_p("phase-one cycle %s, floor %d: health after each uppercut %s, dealt %s" % [sm.cycle_phase == 0, floor_health, healths, dealt])
	t.check(sm.cycle_phase == 0 and floor_health == 7, "a phase-one cycle, whose floor is 7")
	t.check(healths == [7, 6, 4] and not dealt.has(0), "the first uppercut stops on the floor and the next two go on past it (%s)" % [dealt])
	t.check(boss.phase_two, "and the first latched phase two")
	await t.wait_until(func(): return finisher.phase == t.FINISHER_OFF, 300)

	t.log_p("-- on that floor, his recovery can't be dazed, but his Break can")
	await t.reset_gauged(SPEC.home)
	boss.boss_health = 7
	boss.phase_two = true
	sm.on_child_transition(sm.current_state, "Recover")
	sm.recover_timer.stop()
	var recovery_dazes: bool = boss.can_be_dazed()
	gauge.add(gauge.max_value)
	await t.wait_until(func(): return sm.current_state == broken, 30)
	t.check(not recovery_dazes and sm.current_state == broken and boss.can_be_dazed(), "recovering at 7 in a phase-one cycle no daze is open; Broken, it is (%s, %s)" % [recovery_dazes, boss.can_be_dazed()])

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
	var cases := [["standing as close to the left rope as he can", Vector2(ground.position.x, SPEC.home.y), 0.0],
		["riding his turn off the left of the screen", Vector2(sm.pass_left_edge, TOP_ROW), sm.glider_height]]
	for case in cases:
		await t.reset_gauged(SPEC.home)
		await t.settle_player(Vector2(700, 700))
		boss.ground_position = case[1]
		boss.height = case[2]
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
		t.log_p("%s: from %s he slides %.0f px in and %.0f down in %.2f s, to %s, where his juggle is drawn from x %.0f (the rope is at %.0f); the player arrives at %s, %d frames before he lands, %.1f px off his ground line" % [case[0], broken.slide_from, broken.slide_to.x - broken.slide_from.x, broken.slide_to.y - broken.slide_from.y, broken.slide_time, boss.ground_position, drawn_from, sm.ROPES.position.x, t.player.global_position, early.size(), standing_off])
		t.check(down and slid_in and not boss.sprite.flip_h and boss.ground_position.x == inside.x and drawn_from == sm.ROPES.position.x, "%s, facing the player, he ends where his widest juggle frame reaches the rope and no further" % case[0])
		t.check(absf(broken.slide_time - want_time) < 1e-6, "%s: his slide takes %.2f s, the drive's beat or his dive speed, whichever is longer" % [case[0], want_time])
		t.check(early.is_empty() and t.player.global_position == broken.drive_to.round() and absf(standing_off) <= 1.0, "%s: the player arrives beside him as he lands, not before, on his ground line" % case[0])


# His next cycle, in the phase asked for: the phase is read off his health at the top of each one.
static func _start_cycle(t, phase_two: bool) -> void:
	t.boss.phase_two = phase_two
	t.sm.start_cycle()


static func _on_top_row(t) -> bool:
	var boss = t.boss
	return t.sm.current_state.name == "CardStorm" and absf(boss.ground_position.y - TOP_ROW) < 2.0 and t.sm.ROPES.has_point(boss.ground_position)


# The opener, landed from wherever the Break's drive left the player: the finisher's prompt goes up.
static func _opener(t) -> bool:
	for i in 3:
		await t.swing()
		if i < 2:
			await t.wait(6)
	return await t.wait_until(func(): return t.player.get_node("Finisher").phase == t.FINISHER_DAZED and t.player.get_node("Finisher").prompt_visible, 120)
