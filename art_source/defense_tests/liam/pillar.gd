extends RefCounted

# liam_pillar: his pillar and its rounds (LiamStateMachine.take_pillar_hit, LiamWobble, LiamRoundBlast, LiamFall), on his
# test scene with the player kept unhurt, punching from the front spot (the row lets them reach it nowhere else).
#   front     a punch from FRONT_SPOT lands; from anywhere else along the row's face it can't reach, and nobody gets
#             behind the row or inside it
#   shield    shielded from each attack's start until its first live threat: the Tsunami's gate wave's crash on the
#             bottom rope (tsunami_gate_wave), the Tremors' heave; a punch on it then is refused and counts nothing
#   rounds    the round's first hit cuts the attack; three hits end the round there, shielded, and the count carries on
#   blast     his air blast: no damage, the player sealed and thrown on rails to RESET_SPOT (960, 900), and the next attack
#             in the loop resume_delay after they land: a Tsunami round leads to Tremors, a Tremors round to Firestorm
#   timeout   a round of one hit that runs its 2.0 s out ends the same way, the pillar shielded at once
#   fall      the sixth hit, in either attack, crumbles it and the row: he tumbles to LAND_SPOT, the player turns to face
#             him, and he is down in Downed, the flood (and in Tremors the ice) kept through his window; after it he gets
#             back up on a new pillar with no hits on it, the row rises again, and the loop goes on with the attack after
#             the toppled one: the Tsunami's topple leads to Tremors, Tremors' to Firestorm
#   runout    a Tsunami that runs out: his wind's reset, then Tremors

const Common := preload("res://art_source/defense_tests/liam/common.gd")


# The knob's own tremor_time, put back after a check that shortens it.
static var tremor_time := 9.5


static func run(t) -> void:
	await Common.enter(t)
	tremor_time = t.sm.tremor_time
	t.track()
	var unhurt := func():
		t.player.is_invincible = true
		t.player.playerHealth = 1000
	t.physics_frame.connect(unhurt)
	await front(t)
	await shield(t)
	await rounds(t)
	await fall(t)
	await runout(t)
	t.physics_frame.disconnect(unhurt)


# Punches in an open Tsunami from the front spot, and from the row's face to either side of it; then a walk straight up
# into the row and a dash up-left at it from beside his pillar.
static func front(t) -> void:
	t.log_p("-- the front spot and the row")
	var row_face: float = t.boss.row.band().end.y
	var reached := {}
	for at: Vector2 in [t.sm.FRONT_SPOT, Vector2(700, 402), Vector2(1250, 402), Vector2(840, 402)]:
		await Common.fresh(t, at)
		t.sm.pillar_hits = 0
		t.sm.round_hits_taken = 0
		Common.start(t, "Tsunami")
		await t.wait_until(func(): return not t.boss.pillar.shielded, 60 * 8)
		reached[at] = await Common.punch_pillar(t)
		Common.hold(t)
		await Common.clear(t)
	t.log_p("punches from %s" % [reached])
	t.check(reached[t.sm.FRONT_SPOT] and not reached[Vector2(700, 402)] and not reached[Vector2(1250, 402)] and not reached[Vector2(840, 402)], "his pillar is reached from the front spot and nowhere else along the row")
	await Common.fresh(t, Vector2(600, 600))
	var highest := [INF]
	var watch := func(): highest[0] = minf(highest[0], Common.player_box(t).position.y)
	t.physics_frame.connect(watch)
	t.press(KEY_UP)
	await t.wait(90)
	t.release(KEY_UP)
	await Common.fresh(t, Vector2(1010, 420), 40)
	t.press(KEY_UP)
	t.press(KEY_RIGHT)
	t.tap(KEY_W)
	await t.wait(30)
	Common.keys_up(t)
	t.physics_frame.disconnect(watch)
	t.log_p("the highest the player's box got: %.1f (the row's face %.0f)" % [highest[0], row_face])
	t.check(highest[0] >= row_face - 0.5, "nobody gets into the row or behind it, walking or dashing")
	# Back to how he stands between attacks.
	t.sm.pillar_hits = 0
	t.sm.round_hits_taken = 0
	t.boss.pillar.show_hits(0)
	t.boss.pillar.set_shielded(true)


static func shield(t) -> void:
	t.log_p("-- the shield")
	await Common.fresh(t, t.sm.FRONT_SPOT)
	var held_shielded: bool = t.boss.pillar.shielded
	var refused: bool = not await Common.punch_pillar(t)
	t.check(held_shielded and refused and t.sm.pillar_hits == 0, "held between attacks it is shielded, and a punch counts nothing")
	Common.start(t, "Tsunami")
	var first_crashed := [false]
	var before_crash := [false]
	await t.wait_until(func():
		var first: Node2D = t.sm.states["Tsunami"].gate_wave
		first_crashed[0] = is_instance_valid(first) and first.spent
		before_crash[0] = before_crash[0] or (not first_crashed[0] and not t.boss.pillar.shielded)
		return first_crashed[0], 60 * 8)
	await t.wait(1)
	t.check(not before_crash[0] and first_crashed[0] and not t.boss.pillar.shielded, "shielded through the Tsunami's gate wave's fall, open from its crash")
	Common.hold(t)
	await Common.clear(t)
	t.sm.tremor_time = 3.0
	Common.start(t, "Tremors")
	var before_heave := [false]
	await t.wait_until(func():
		before_heave[0] = before_heave[0] or (t.sm.states["Tremors"].clock < t.sm.heave_slam - 0.05 and not t.boss.pillar.shielded)
		return t.sm.states["Tremors"].beats.has(&"heave"), 120)
	await t.wait(1)
	t.check(not before_heave[0] and not t.boss.pillar.shielded, "shielded through the Tremors' build, open from the heave")
	Common.hold(t)
	await Common.clear(t)
	t.sm.tremor_time = tremor_time


# From the Tsunami: a round of three, the blast, and Tremors; then a round of one that runs out, the blast, and back to
# the Tsunami. Four hits in all.
static func rounds(t) -> void:
	t.log_p("-- a round of three in the Tsunami")
	await Common.fresh(t, t.sm.FRONT_SPOT)
	t.sm.pillar_hits = 0
	t.sm.rotation_index = 0
	Common.start(t, "Tsunami")
	await t.wait_until(func(): return not t.boss.pillar.shielded, 60 * 8)
	var took := []
	var after_first := ""
	for i in 3:
		took.append(await Common.punch_pillar(t))
		if i == 0:
			after_first = Common.state(t)
		await t.wait(4)
	await t.wait(1)
	var shielded_at_three: bool = t.boss.pillar.shielded
	t.check(took == [true, true, true] and after_first == "Wobble", "the first hit cuts the attack into the round (%s, %s)" % [took, after_first])
	t.check(Common.state(t) == "RoundBlast" and shielded_at_three and t.sm.pillar_hits == 3, "three end it, shielded (%s, %d hits)" % [Common.state(t), t.sm.pillar_hits])
	var thrown_from: Vector2 = t.player.global_position
	var refused: bool = not await Common.punch_pillar(t)
	t.check(refused and t.sm.pillar_hits == 3, "a fourth punch is refused")
	await blast(t, "Tremors", thrown_from)

	t.log_p("-- a round of one in Tremors that runs out")
	await t.wait_until(func(): return t.sm.states["Tremors"].beats.has(&"heave"), 120)
	await Common.fresh(t, t.sm.FRONT_SPOT, 2)
	var one: bool = await Common.punch_pillar(t)
	var round_start: float = t.defense.clock
	await t.wait_until(func(): return Common.state(t) != "Wobble", 200)
	var lasted: float = t.defense.clock - round_start
	t.log_p("took %s, the round lasted %.2f s, then %s with %d hits" % [one, lasted, Common.state(t), t.sm.pillar_hits])
	t.check(one and Common.state(t) == "RoundBlast" and t.sm.pillar_hits == 4 and t.boss.pillar.shielded, "the timeout ends it, shielded, the count carried on to 4")
	t.check(lasted <= t.sm.wobble_time + 0.35, "within the round's %.1f s" % t.sm.wobble_time)
	await blast(t, "Firestorm", t.player.global_position)
	Common.hold(t)
	await Common.clear(t)


# The blast under way, the round having left the player at `from`: its throw, and the attack it hands to.
static func blast(t, next: String, from: Vector2) -> void:
	var health: int = t.player.playerHealth
	await t.wait_until(func(): return t.sm.is_launching(), 60)
	var sealed: bool = t.player.is_action_locked and t.player.lock_seals_guard
	var to: Vector2 = t.sm.RESET_SPOT
	await t.wait_until(func(): return not t.sm.is_launching(), 90)
	var landed: Vector2 = t.player.global_position
	var land_time: float = t.defense.clock
	await t.wait_until(func(): return Common.state(t) != "RoundBlast", 120)
	var resumed: float = t.defense.clock - land_time
	t.log_p("thrown from %s to %s (want %s), sealed %s, next %s %.2f s after landing" % [from, landed, to, sealed, Common.state(t), resumed])
	t.check(sealed and t.player.playerHealth == health, "sealed on rails, unhurt")
	t.check(landed.distance_to(to) <= 1.0, "landed on %s" % to)
	# Three frames: the landing and the switch are each seen a step after they happen.
	t.check(Common.state(t) == next and absf(resumed - t.sm.resume_delay) <= 3.0 / 60.0, "%s %.1f s after landing" % [next, t.sm.resume_delay])


static func fall(t) -> void:
	t.log_p("-- the sixth hit")
	await Common.fresh(t, t.sm.FRONT_SPOT)
	t.sm.pillar_hits = 5
	t.boss.pillar.show_hits(5)
	Common.start(t, "Tsunami")
	await t.wait_until(func(): return not t.boss.pillar.shielded, 60 * 8)
	t.boss.flood.add_water(0.5)
	var took: bool = await Common.punch_pillar(t)
	await t.wait_until(func(): return Common.state(t) == "Downed", 90)
	await t.wait(8)
	var water_down: float = t.boss.flood.coverage
	var faced: Area2D = t.player.facing_target
	t.log_p("took %s, now %s at %s, pillar standing %s, hud %.2f, player facing %s" % [took, Common.state(t), t.boss.global_position, t.boss.pillar.standing, t.boss.hud_alpha(), faced.get_parent().name if faced else "nothing"])
	t.check(took and Common.state(t) == "Downed" and t.boss.global_position == t.sm.LAND_SPOT and t.boss.height == 0.0, "he tumbles to LAND_SPOT and is down")
	t.check(not t.boss.pillar.standing and not t.boss.pillar.hurtbox.is_in_group("boss_target"), "the pillar is gone")
	t.check(not t.boss.row.is_up() and t.boss.row.body_shape.disabled, "the row went down with it")
	t.check(faced == t.boss.hurtbox, "the player turns to face him")
	await t.wait_until(func(): return Common.state(t) == "GetUp", 60 * 5)
	await t.wait_until(func(): return Common.state(t) != "GetUp", 60 * 5)
	var water_up: float = t.boss.flood.coverage
	t.log_p("up again into %s, pillar at %s parked %s, hits %d, row up %s, the flood %.3f through the window and %.3f after" % [Common.state(t), t.boss.pillar.global_position, t.boss.pillar.parked, t.sm.pillar_hits, t.boss.row.is_up(), water_down, water_up])
	t.check(Common.state(t) == "Tremors" and t.boss.pillar.parked and t.boss.pillar.global_position == t.sm.PERCH and t.sm.pillar_hits == 0, "then back up on a new pillar with no hits on it, into Tremors")
	t.check(water_down >= 0.5 and water_up >= water_down, "the flood kept through his window")
	t.check(t.boss.row.is_up() and not t.boss.row.body_shape.disabled, "and the row is up again")
	Common.hold(t)
	await Common.clear(t)

	t.log_p("-- the sixth hit in Tremors")
	await Common.fresh(t, t.sm.FRONT_SPOT)
	t.sm.tremor_time = 3.0
	t.sm.pillar_hits = 5
	Common.start(t, "Tremors")
	await t.wait_until(func(): return t.sm.states["Tremors"].beats.has(&"heave"), 120)
	await Common.fresh(t, t.sm.FRONT_SPOT, 2)
	var took_again: bool = await Common.punch_pillar(t)
	var fell: bool = await t.wait_until(func(): return Common.state(t) == "Downed", 90)
	var iced_down: bool = t.boss.flood.is_iced()
	var next: bool = await t.wait_until(func(): return Common.state(t) != "Downed" and Common.state(t) != "GetUp", 60 * 12)
	t.log_p("the sixth hit in Tremors: down %s, the ice kept %s, then %s" % [fell, iced_down, Common.state(t)])
	t.check(took_again and fell and iced_down, "the sixth hit in Tremors drops him too, the ice kept")
	t.check(next and Common.state(t) == "Firestorm", "and Firestorm follows his window")
	t.sm.tremor_time = tremor_time
	Common.hold(t)
	await Common.clear(t)


static func runout(t) -> void:
	t.log_p("-- a Tsunami that runs out")
	await Common.fresh(t, Vector2(1500, 900))
	var tsunami_time: float = t.sm.tsunami_time
	t.sm.tsunami_time = 1.2
	var seen := []
	var watch := func():
		if seen.is_empty() or seen[-1] != Common.state(t):
			seen.append(Common.state(t))
	t.physics_frame.connect(watch)
	Common.start(t, "Tsunami")
	await t.wait_until(func(): return Common.state(t) == "Tremors", 60 * 6)
	t.physics_frame.disconnect(watch)
	t.sm.tsunami_time = tsunami_time
	t.check(seen == ["Tsunami", "RoundBlast", "Tremors"], "his wind's reset, then Tremors (%s)" % [seen])
	Common.hold(t)
	await Common.clear(t)
