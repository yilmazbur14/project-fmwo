extends RefCounted

# carter_caster_see_through (playtest 2026-10-04): the Beam Rush's four figures (CarterBeamRush) are on the clone
# layer, over every fighter and not y-sorted, and cover the whole top strip of the ring; a player standing up there
# was drawn under one, lock ring and all, and couldn't be seen. --fixed-fps 60. Through a charge: the player put
# behind each figure in turn (feet 50 px over its feet) and just in front of its feet, and that figure's
# self_modulate alpha is CarterArtLayout.BEAM_CLONE_SEE_THROUGH within BEAM_CLONE_SEE_THROUGH_TIME and a frame, the
# other three's 1; walked off down the ring, all four back to 1 as fast; and the attack still fades the four out on
# its own modulate and frees them at its end.

const CarterArtLayout := preload("res://Scripts/CarterArtLayout.gd")


static func run(t) -> void:
	var rush: Node = await t.load_carter_akuma()
	var sm: Node = t.sm
	var player: Node = t.player
	player.playerHealth = 99
	await t.settle_player(Vector2(960, 760))
	if not await t.start_beam_rush(rush, 2, 0.3):
		t.check(false, "the Beam Rush starts")
		return
	if not await t.wait_until(func(): return rush.beat == rush.Beat.CHARGE, 300):
		t.check(false, "its first charge comes")
		return
	var settle := int(ceil(CarterArtLayout.BEAM_CLONE_SEE_THROUGH_TIME * 60.0)) + 1
	var alphas := func() -> Array: return rush.casters.map(func(c): return snappedf(c.figure.self_modulate.a, 0.001))
	await t.wait(settle)
	t.check(alphas.call() == [1.0, 1.0, 1.0, 1.0], "with the player down the ring all four are solid (%s)" % [alphas.call()])
	for i in rush.casters.size():
		for rise in [50.0, -30.0]:
			var feet := Vector2(CarterArtLayout.BEAM_X[i], CarterArtLayout.BEAM_CLONE_Y - rise)
			player.global_position = feet
			player.velocity = Vector2.ZERO
			if rush.beat != rush.Beat.CHARGE:
				await t.wait_until(func(): return rush.beat == rush.Beat.CHARGE, 300)
			await t.wait(settle)
			var now: Array = alphas.call()
			var want := [1.0, 1.0, 1.0, 1.0]
			want[i] = snappedf(CarterArtLayout.BEAM_CLONE_SEE_THROUGH, 0.001)
			t.check(now == want, "the player %s figure %d: it alone goes see-through (%s)" % ["behind" if rise > 0.0 else "in front of", i, now])
	player.global_position = Vector2(960, 760)
	await t.wait(settle)
	t.check(alphas.call() == [1.0, 1.0, 1.0, 1.0], "walked back down the ring, all four solid again (%s)" % [alphas.call()])
	var figures: Array = rush.casters.map(func(c): return c.figure)
	var faded := [true]
	var watch := func() -> void:
		if rush.beat == rush.Beat.END and rush.beat_clock >= 0.25:
			for figure in figures:
				if is_instance_valid(figure) and figure.modulate.a > 0.01:
					faded[0] = false
	t.physics_frame.connect(watch)
	await t.wait_until(func(): return sm.current_state != rush, 1800)
	t.physics_frame.disconnect(watch)
	await t.wait(2)
	t.check(faded[0], "the attack's own fade still takes the four out at its end")
	t.check(figures.all(func(f): return not is_instance_valid(f)), "and they are freed with it")
