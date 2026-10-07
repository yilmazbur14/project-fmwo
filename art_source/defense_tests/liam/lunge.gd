extends RefCounted

# liam_lunge: attack 4 (LiamLunge), entered straight on his test scene (it is only in the rotation once the loop is
# wired). tier= one of flow, reaction, impale, parry, death; any other runs them all.
#   flow      his vanish: the stump at stump_risen, him unseen, the HUD at 1.0, the steam at steam_max; 20 seeded waits
#             all inside lunge_wait_range; each badge liam_lunge's, lunge_distance beside the player and inside
#             LUNGE_AREA; the impact exactly 24 frames after the badge with the player standing and dashing, walking
#             and dashing, and walking up and dashing; three dodges, then back up: the steam cleared within
#             steam_clear_time, him on his pillar at full height at PERCH, his wind's reset to RESET_SPOT, and the Tsunami
#   reaction  a parry pressed 0.18, 0.25, 0.32 and 0.38 s after the badge is PARRIED; at 0.12 and 0.42 it is HIT
#   impale    the player sealed, posed, seen and at IMPALE_Z; exactly burn_ticks burns burn_interval apart, a half-heart
#             each and landing through i-frames; washed down to WATER_BLAST_SPOT (+-1), unlocked, back at their own z;
#             him at PERCH at full height, and no second gust: the reset skips the player already on its spot, straight
#             on to the Tsunami
#   parry     knocked down where he stood into Downed (Broken with a Break owed); a clean combo, the daze and the
#             uppercut; his get-up blows the player back, teleports him onto his stump and raises it, keeps
#             pillar_hits, and starts the next attack
#   death     killed by the second burn: one FightOutro, the player not locked, not posed, no fire on them, their z back

const Common := preload("res://art_source/defense_tests/liam/common.gd")
const Layout := preload("res://Scripts/LiamArtLayout.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")

const FRAME := 1.0 / 60.0
const SPOT := Vector2(960, 700)


static func run(t) -> void:
	await Common.enter(t)
	t.track()
	t.track_dodges()
	t.hold_break_gauge(t.boss)
	var all: bool = not t.tier in ["flow", "reaction", "impale", "parry", "death"]
	if all or t.tier == "flow":
		await flow(t)
	if all or t.tier == "reaction":
		await reaction(t)
	if all or t.tier == "impale":
		await impale(t)
	if all or t.tier == "parry":
		await parry(t)
	if all or t.tier == "death":
		await death(t)


static func lunge(t) -> Node:
	return t.sm.states["Lunge"]


# Back on his pillar at the top, whole, the steam gone: where an attack starts from.
static func reset_perch(t) -> void:
	t.sm.cancel_launch()
	t.sm.states["GetUp"].to_stump = false
	t.sm.states["Downed"].opening_anim = &""
	t.sm.lunge_seed = -1
	t.sm.lunge_wait_range = Vector2(1.5, 3.0)
	t.boss.pillar.stand_up_now()
	t.boss.pillar.set_shielded(true)
	t.boss.air.visible = true
	t.boss.air.modulate.a = 1.0
	t.boss.set_facing(false)
	t.boss.set_body_box(&"standing")
	t.boss.set_hurtbox_active(false)
	t.boss.stand_on_pillar()
	t.boss.perch()
	t.boss.play_anim(&"perch_idle")
	t.boss.steam.set_density(0.0, 0.0)
	t.boss.steam.set_bubble(Layout.STEAM_BUBBLE, 0.0)


# Into the lunge with the player at `at`: its waits `wait` long (short, where the wait isn't what is tested), seeded.
static func begin(t, at: Vector2, wait := Vector2(0.3, 0.3), seed := 7) -> Node:
	await Common.clear(t)
	reset_perch(t)
	await Common.fresh(t, at)
	t.sm.lunge_seed = seed
	t.sm.lunge_wait_range = wait
	var state: Node = lunge(t)
	Common.start(t, "Lunge")
	return state


# The next badge: the physics frame it went up on (seen at the start of the one after).
static func next_badge(t, state: Node, count: int) -> int:
	await t.wait_until(func(): return state.tells.size() > count, 60 * 6)
	return Engine.get_physics_frames() - 1


static func next_result(t, state: Node, count: int) -> int:
	await t.wait_until(func(): return state.results.size() > count, 60 * 2)
	return Engine.get_physics_frames() - 1


# A dash along the held arrows `seconds` after the badge that went up on `badge_frame`.
static func dash_at(t, badge_frame: int, seconds: float, arrows: Array) -> void:
	await t.wait_until(func(): return Engine.get_physics_frames() - 1 - badge_frame >= roundi(seconds * 60.0) - 1, 60)
	for code in arrows:
		t.press(code)
	t.tap(KEY_W)


static func flow(t) -> void:
	t.log_p("-- the flow: the vanish, the waits, three dodged lunges, back up")
	var state: Node = await begin(t, SPOT, Vector2(1.5, 3.0), 3)
	await t.wait(roundi(t.sm.vanish_time * 60.0) + 2)
	var risen: float = t.boss.pillar.risen
	t.log_p("after the vanish: stump %.3f, him seen %s, hud %.2f, steam %.3f, pillar standing %s shielded %s" % [risen, t.boss.air.visible, t.boss.hud_alpha(), t.boss.steam.density, t.boss.pillar.standing, t.boss.pillar.shielded])
	t.check(absf(risen - t.sm.stump_risen) <= 0.001 and not t.boss.air.visible and is_equal_approx(t.boss.hud_alpha(), 1.0) and t.boss.steam.density >= t.sm.steam_max - 0.001, "the stump at %.1f, him unseen, the HUD at 1.0, the steam at %.2f" % [t.sm.stump_risen, t.sm.steam_max])
	t.check(t.boss.pillar.standing and t.boss.pillar.shielded and t.boss.pillar.parked, "his pillar still standing, shielded and solid")
	var probe := RandomNumberGenerator.new()
	probe.seed = 11
	var old_rng: RandomNumberGenerator = state.rng
	state.rng = probe
	var drawn := []
	for i in 20:
		drawn.append(state.next_wait())
	state.rng = old_rng
	var span: Vector2 = t.sm.lunge_wait_range
	t.log_p("20 seeded waits: %s" % [drawn.map(func(w): return snappedf(w, 0.01))])
	t.check(drawn.all(func(w): return w >= span.x and w <= span.y), "20 seeded waits all inside [%.1f, %.1f]" % [span.x, span.y])
	var ways := [[[], 0.3, "standing"], [[KEY_RIGHT], 0.3, "walking"], [[KEY_UP], 0.36, "walking up"]]
	var frames := []
	var dodged := []
	var badges_ok := true
	for i in ways.size():
		var way: Array = ways[i]
		await Common.fresh(t, SPOT + Vector2(0, 60 * i), 0)
		var held: Array = way[0]
		var badge: int = await next_badge(t, state, i)
		var entry: Array = state.tells[i]
		var origin: Vector2 = entry[1]
		var tell: Node = t.boss.get_parent().get_node_or_null("ParryTell%d" % t.boss.get_instance_id())
		var beside := absf(absf(origin.x - t.player.global_position.x) - t.sm.lunge_distance) <= 0.5
		var inside: bool = t.sm.LUNGE_AREA.grow(0.5).has_point(origin)
		badges_ok = badges_ok and tell != null and beside and inside
		for code in held:
			t.press(code)
		await dash_at(t, badge, way[1], [])
		var result_frame: int = await next_result(t, state, i)
		Common.keys_up(t)
		frames.append(result_frame - badge)
		dodged.append(state.results[i] == HitInfo.Result.DODGED)
		t.log_p("lunge %d (%s, dash at %.2f): badge %s at %s beside %s inside %s, impact %d frames on, %s" % [i + 1, way[2], way[1], tell != null, origin, beside, inside, result_frame - badge, HitInfo.Result.keys()[state.results[i]]])
	t.check(badges_ok, "each badge liam_lunge's, %.0f px beside the player, inside LUNGE_AREA" % t.sm.lunge_distance)
	t.check(frames.all(func(f): return f == 24), "the impact exactly 24 frames after the badge each time (%s)" % [frames])
	t.check(dodged.all(func(d): return d), "all three dashed through: DODGED (%s)" % [dodged])
	var expected: StringName = next_attack_after(t)
	var back_at: bool = await t.wait_until(func(): return state.phase == state.Phase.RETURN, 60 * 3)
	var steam_from: float = t.boss.steam.density
	var cleared: bool = await t.wait_until(func(): return t.boss.steam.density <= 0.001, roundi((t.sm.steam_clear_time + 0.1) * 60.0))
	var over: bool = await t.wait_until(func(): return Common.state(t) != "Lunge", 60 * 3)
	var perched: bool = is_equal_approx(t.boss.pillar.risen, 1.0) and t.boss.global_position == t.sm.PERCH and is_equal_approx(t.boss.height, Layout.STAND_HEIGHT) and t.boss.air.visible
	var reset: bool = Common.state(t) == "RoundBlast"
	var next: bool = await t.wait_until(func(): return Common.state(t) == String(expected), 60 * 3)
	t.log_p("back up %s: steam %.2f cleared %s; then %s and %s (expected %s), the player at %s, pillar %.2f at %s, him %.0f up at %s, hud %.2f" % [back_at, steam_from, cleared, "his wind's reset" if reset else "no reset", Common.state(t), expected, t.player.global_position, t.boss.pillar.risen, t.boss.pillar.global_position, t.boss.height, t.boss.global_position, t.boss.hud_alpha()])
	t.check(cleared, "the steam cleared within %.1f s" % t.sm.steam_clear_time)
	t.check(over and perched, "him on his pillar at full height at PERCH")
	t.check(reset and next and t.player.global_position.distance_to(t.sm.RESET_SPOT) <= 1.0, "his wind's reset to %s, then %s" % [t.sm.RESET_SPOT, expected])
	Common.hold(t)
	reset_perch(t)


# The attack after the lunge: its place in the rotation once it is wired, the one after the rotation's current one
# until then.
static func next_attack_after(t) -> StringName:
	var rotation: Array = t.sm.ATTACK_ROTATION
	var at: int = rotation.find(&"Lunge")
	if at < 0:
		at = t.sm.rotation_index
	return rotation[(at + 1) % rotation.size()]


static func reaction(t) -> void:
	t.log_p("-- the reaction check")
	var cases := [[0.18, HitInfo.Result.PARRIED], [0.25, HitInfo.Result.PARRIED], [0.32, HitInfo.Result.PARRIED],
		[0.38, HitInfo.Result.PARRIED], [0.12, HitInfo.Result.HIT], [0.42, HitInfo.Result.HIT]]
	var wrong := []
	for case: Array in cases:
		var state: Node = await begin(t, SPOT)
		var badge: int = await next_badge(t, state, 0)
		var badge_clock: float = t.defense.clock
		await t.wait_until(func(): return Engine.get_physics_frames() - 1 - badge >= roundi(case[0] * 60.0) - 1, 60)
		t.press(KEY_SHIFT)
		var result_frame: int = await next_result(t, state, 0)
		var press_at: float = t.defense.last_press_time - badge_clock
		t.release(KEY_SHIFT)
		var result: int = state.results[0]
		var credited := "credited %.3f s on" % press_at if press_at >= 0.0 else "not taken: the player was already held"
		t.log_p("pressed %.2f s after the badge (%s), impact %d frames on: %s" % [case[0], credited, result_frame - badge, HitInfo.Result.keys()[result]])
		if result != case[1]:
			wrong.append("%.2f: %s" % [case[0], HitInfo.Result.keys()[result]])
		Common.hold(t)
		await t.wait(40)
	t.check(wrong.is_empty(), "0.18, 0.25, 0.32 and 0.38 s after the badge PARRIED, 0.12 and 0.42 HIT (%s)" % [wrong])
	await Common.clear(t)
	reset_perch(t)


static func impale(t) -> void:
	t.log_p("-- the impale")
	var state: Node = await begin(t, SPOT)
	var health: int = t.player.playerHealth
	var badge: int = await next_badge(t, state, 0)
	var result_frame: int = await next_result(t, state, 0)
	await t.wait(2)
	var stage: Node = t.player.get_parent()
	var held := {"sealed": t.player.is_action_locked and t.player.lock_seals_guard, "posed": t.player.scripted_pose,
		"seen": t.player.sprite.visible, "z": stage.z_index}
	t.log_p("impact %d frames after the badge: %s; held %s" % [result_frame - badge, HitInfo.Result.keys()[state.results[0]], held])
	t.check(state.results[0] == HitInfo.Result.HIT and result_frame - badge == 24, "standing still: HIT, 24 frames after the badge")
	t.check(held.sealed and held.posed and held.seen and held.z == t.sm.IMPALE_Z, "the player sealed, posed, seen and at z %d" % t.sm.IMPALE_Z)
	# Up in their i-frames for every burn: they land anyway.
	var watch := func(): t.player.is_invincible = true
	t.physics_frame.connect(watch)
	var landed: bool = await t.wait_until(func(): return state.washed and not t.sm.is_launching(), 60 * 5)
	t.physics_frame.disconnect(watch)
	t.player.is_invincible = false
	await t.wait(2)
	var ticks: Array = state.tick_times
	var apart := []
	for i in range(1, ticks.size()):
		apart.append(snappedf(ticks[i] - ticks[i - 1], 0.001))
	var burns: Array = t.events_of("HIT", &"liam_impale_burn")
	t.log_p("burns at %s (apart %s), health %d -> %d, %d burn hits; landed %s at %s, locked %s posed %s z %d" % [ticks, apart, health, t.player.playerHealth, burns.size(), landed, t.player.global_position, t.player.is_action_locked, t.player.scripted_pose, stage.z_index])
	t.check(ticks.size() == t.sm.burn_ticks and apart.all(func(a): return absf(a - t.sm.burn_interval) <= FRAME + 0.001), "exactly %d burns %.1f s apart" % [t.sm.burn_ticks, t.sm.burn_interval])
	t.check(health - t.player.playerHealth == t.sm.burn_ticks and burns.size() == t.sm.burn_ticks, "a half-heart each (%d), through the i-frames" % (health - t.player.playerHealth))
	t.check(landed and t.player.global_position.distance_to(t.sm.WATER_BLAST_SPOT) <= 1.0, "washed down to %s (+-1)" % t.sm.WATER_BLAST_SPOT)
	t.check(not t.player.is_action_locked and not t.player.scripted_pose and stage.z_index == 0, "unlocked, unposed, back at their own z")
	var back: bool = await t.wait_until(func(): return Common.state(t) != "Lunge", 60 * 4)
	var perched: bool = t.boss.global_position == t.sm.PERCH and is_equal_approx(t.boss.height, Layout.STAND_HEIGHT) and is_equal_approx(t.boss.pillar.risen, 1.0)
	var gusts := [0]
	var gust_watch := func():
		if Common.state(t) == "RoundBlast" and t.sm.is_launching():
			gusts[0] += 1
	t.physics_frame.connect(gust_watch)
	var next: bool = await t.wait_until(func(): return Common.state(t) == "Tsunami", 60 * 2)
	t.physics_frame.disconnect(gust_watch)
	t.log_p("then %s: pillar %.2f, him at %s %.0f up, steam %.3f; frames of a second gust %d" % [Common.state(t), t.boss.pillar.risen, t.boss.global_position, t.boss.height, t.boss.steam.density, gusts[0]])
	t.check(back and perched, "him back at PERCH at full height")
	t.check(next and gusts[0] == 0, "no second gust: the reset skips the player already on its spot, straight on to the Tsunami")
	Common.hold(t)
	reset_perch(t)


static func parry(t) -> void:
	t.log_p("-- a parried lunge and the pillarless window")
	var state: Node = await begin(t, SPOT)
	t.sm.pillar_hits = 2
	t.boss.pillar.show_hits(2)
	t.boss.boss_health = t.boss.max_health
	var badge: int = await next_badge(t, state, 0)
	await t.wait_until(func(): return Engine.get_physics_frames() - 1 - badge >= 14, 60)
	t.press(KEY_SHIFT)
	await next_result(t, state, 0)
	t.release(KEY_SHIFT)
	await t.wait(2)
	var at: Vector2 = t.boss.global_position
	t.log_p("%s: now %s at %s (he lunged from %s), stump %.2f, steam %.2f" % [HitInfo.Result.keys()[state.results[0]], Common.state(t), at, state.tells[0][1], t.boss.pillar.risen, t.boss.steam.density])
	t.check(state.results[0] == HitInfo.Result.PARRIED and Common.state(t) == "Downed", "PARRIED: down where he stood, in Downed")
	t.check(t.boss.pillar.standing and absf(t.boss.pillar.risen - t.sm.stump_risen) <= 0.001, "his stump still standing behind the row")
	await t.wait(20)
	t.place_under(t.boss.get_finisher_hurtbox())
	await t.wait(6)
	var fin: Node = t.player.get_node("Finisher")
	fin.min_press_interval = 0.0
	var health: int = t.boss.boss_health
	for i in 3:
		await t.swing()
		if i < 2:
			await t.wait(6)
	var combo: int = health - t.boss.boss_health
	var dazed: bool = await t.wait_until(func(): return fin.phase == t.FINISHER_DAZED and fin.prompt_visible, 120)
	await t.mash_tiered(5)
	await t.wait_until(func(): return fin.phase == t.FINISHER_OFF, 240)
	var uppercut: int = health - combo - t.boss.boss_health
	t.log_p("combo %d, dazed %s, uppercut %d, now %s" % [combo, dazed, uppercut, Common.state(t)])
	t.check(combo == 4 and dazed and uppercut == roundi(t.boss.max_health * fin.finisher_damage_ratio), "a clean combo (4), the daze and the uppercut (%d)" % uppercut)
	var getup: Node = t.sm.states["GetUp"]
	var up: bool = await t.wait_until(func(): return Common.state(t) == "GetUp", 60 * 4)
	# The blast throws the player to the bottom of the ring unless they are already there (launch_skip).
	var seen := {"thrown": false, "at_bottom": false, "arrived_on": Vector2.INF}
	var watch := func():
		if getup.beat == getup.Beat.BLAST:
			seen.thrown = seen.thrown or t.sm.is_launching()
			if not getup.fired:
				var spot: Vector2 = t.sm.launch_spot(t.player.global_position)
				seen.at_bottom = t.player.global_position.distance_to(spot) <= t.sm.launch_skip
		if getup.beat == getup.Beat.ARRIVE and seen.arrived_on == Vector2.INF:
			seen.arrived_on = t.boss.global_position
	t.physics_frame.connect(watch)
	var expected: StringName = t.sm.ATTACK_ROTATION[0]
	var done: bool = await t.wait_until(func(): return Common.state(t) != "GetUp", 60 * 6)
	t.physics_frame.disconnect(watch)
	await t.wait(2)
	t.log_p("up %s, blew the player back %s (already at the bottom %s), teleported onto the stump at %s, then %s: pillar %.2f at %s, hits %d, him %.0f up" % [up, seen.thrown, seen.at_bottom, seen.arrived_on, Common.state(t), t.boss.pillar.risen, t.boss.pillar.global_position, t.sm.pillar_hits, t.boss.height])
	t.check(up and (seen.thrown or seen.at_bottom) and seen.arrived_on == t.sm.PERCH, "he gets up, blows the player back and teleports onto his stump")
	t.check(done and is_equal_approx(t.boss.pillar.risen, 1.0) and is_equal_approx(t.boss.height, Layout.STAND_HEIGHT) and t.sm.pillar_hits == 2, "raises it under him and it keeps its hits (%d)" % t.sm.pillar_hits)
	t.check(Common.state(t) == String(expected), "and starts %s" % expected)
	Common.hold(t)
	t.log_p("-- a parry with a Break owed")
	state = await begin(t, SPOT)
	t.sm.break_owed = true
	badge = await next_badge(t, state, 0)
	await t.wait_until(func(): return Engine.get_physics_frames() - 1 - badge >= 14, 60)
	t.press(KEY_SHIFT)
	await next_result(t, state, 0)
	t.release(KEY_SHIFT)
	await t.wait(2)
	t.log_p("%s: now %s, owed %s" % [HitInfo.Result.keys()[state.results[0]], Common.state(t), t.sm.break_owed])
	t.check(state.results[0] == HitInfo.Result.PARRIED and Common.state(t) == "Broken" and not t.sm.break_owed, "Broken instead, the Break cashed")
	t.hold_break_gauge(t.boss)
	Common.hold(t)
	reset_perch(t)


static func death(t) -> void:
	t.log_p("-- killed by the second burn")
	var state: Node = await begin(t, SPOT)
	await next_badge(t, state, 0)
	await next_result(t, state, 0)
	t.player.playerHealth = 2
	await t.wait_until(func(): return t.player.playerHealth <= 0, 60 * 3)
	var ticks: int = state.tick_times.size()
	await t.wait(90)
	var outros: int = t.root.get_children().filter(func(n): return n.name == "FightOutro").size()
	var fire: Array = t.boss.fx_layer.get_children().filter(func(n): return not n.is_queued_for_deletion() and n.get("kind") in [&"sky_fire", &"flames"])
	var stage: Node = t.player.get_parent()
	t.log_p("dead on burn %d: outros %d, locked %s, posed %s (Posed %s), fire nodes %d, z %d" % [ticks, outros, t.player.is_action_locked, t.player.scripted_pose, t.player.is_posed(), fire.size(), stage.z_index])
	t.check(ticks == 2 and outros == 1, "the second burn kills: one FightOutro")
	t.check(not t.player.is_action_locked and not t.player.scripted_pose and not t.player.is_posed(), "the player neither locked nor posed")
	t.check(fire.is_empty() and stage.z_index == 0, "no fire left on them, their z back")
