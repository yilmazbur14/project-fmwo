extends RefCounted

# matt_echo_bots tier=perfect|human (the Echo Roars played whole, a phase-one and a phase-two instance, standing on the
# smoke spot). --fixed-fps 60, the gauge held.
#   perfect  every red and echo pressed 0.12 s before its touch, every X left alone, every BOOMBURST dashed in place
#            0.105 s before its touch: not one hit in either
#   human    the brief's learned player on a fixed seed: each press 0.12 s before the touch give or take 0.083 s, each X
#            pressed on one time in ten, each dash 0.105 s before the touch give or take 0.10 s: phase one costs
#            HUMAN_ONE half-hearts and phase two HUMAN_TWO, loose bounds round what the model bot measured
# Both play the live plan, which has had no X since 2026-10-06; what they do with one is kept for a feint knob turned
# back on.

const Lib := preload("res://art_source/defense_tests/matt/echo_lib.gd")
# Raised from (1, 8) and (2, 10) with the second BOOMBURST a string (2026-10-06): about 0.9 half-hearts each for this
# player, so a whole instance costs about 8 in phase one and 11 in phase two.
const HUMAN_ONE := Vector2i(2, 14)
const HUMAN_TWO := Vector2i(3, 18)
const SEED := 20261004
const PRESS_SD := 0.083
const DASH_SD := 0.10
const BITE := 0.1


static func run(t) -> void:
	await t.load_matt()
	t.hold_break_gauge(t.boss)
	t.track()
	var human: bool = t.tier == "human"
	var rng := RandomNumberGenerator.new()
	rng.seed = SEED
	var lost := []
	for two in [false, true]:
		lost.append(await play(t, two, human, rng))
	t.log_p("%s: half-hearts lost, phase one %d, phase two %d" % [t.tier, lost[0], lost[1]])
	if human:
		t.check(lost[0] >= HUMAN_ONE.x and lost[0] <= HUMAN_ONE.y and lost[1] >= HUMAN_TWO.x and lost[1] <= HUMAN_TWO.y,
			"the learned model loses %d to %d in phase one (%d) and %d to %d in phase two (%d)" % [HUMAN_ONE.x, HUMAN_ONE.y, lost[0], HUMAN_TWO.x, HUMAN_TWO.y, lost[1]])
	else:
		t.check(lost[0] == 0 and lost[1] == 0, "a perfect read takes no hit in either phase (%s)" % [lost])


static func play(t, two: bool, human: bool, rng: RandomNumberGenerator) -> int:
	var echo: Node = await Lib.start(t, two)
	await t.settle_player(t.SMOKE_SPOTS["matt"])
	var spot: Vector2 = t.player.global_position
	var health: int = t.player.playerHealth
	var planned := {}
	var presses := []
	var dash_at := INF
	var badges_seen := 0
	for f in 1600:
		var now: float = t.defense.clock
		if not t.player.is_dodging:
			t.player.global_position = spot
		for ring in echo.rings:
			if not is_instance_valid(ring) or ring.answered or planned.has(ring.get_instance_id()):
				continue
			planned[ring.get_instance_id()] = true
			var due: float = now + Lib.contact_in(t, ring)
			match ring.kind:
				Lib.RED, Lib.ECHO:
					presses.append(due - 0.12 + (rng.randfn(0.0, PRESS_SD) if human else 0.0) - 1.0 / 60.0)
				Lib.GHOST:
					if human and rng.randf() < BITE:
						presses.append(due - 0.12 + rng.randfn(0.0, PRESS_SD) - 1.0 / 60.0)
				Lib.BOOMBURST:
					pass
		# The BOOMBURST is timed off its yellow badge: its birth on the beat, then its flight to the player.
		while badges_seen < echo.badges.size():
			var badge: Array = echo.badges[badges_seen]
			badges_seen += 1
			if badge[0] == &"yellow":
				var rect: Rect2 = t.hurtbox_rect()
				var nearest: float = echo.centre.clamp(rect.position, rect.end).distance_to(echo.centre)
				var flight: float = maxf(nearest - t.sm.echo_band - t.sm.echo_ring_start_radius, 0.0) / t.sm.echo_ring_speed
				dash_at = now + badge[1] + badge[2] - echo.clock + flight - 0.105 + (rng.randfn(0.0, DASH_SD) if human else 0.0) - 1.0 / 60.0
		var keep := []
		for at in presses:
			if now >= at:
				t.tap(KEY_SHIFT)
			else:
				keep.append(at)
		presses = keep
		if now >= dash_at:
			dash_at = INF
			t.tap(KEY_W)
		await t.physics_frame
		if t.sm.current_state != echo:
			break
	var lost: int = health - t.player.playerHealth
	await Lib.reset(t)
	await t.wait(100)
	return lost
