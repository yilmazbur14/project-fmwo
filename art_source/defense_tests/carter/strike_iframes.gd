extends RefCounted

# carter_strike_iframes (tuning 2026-10-04): the Beam Rush's teleport strike doesn't bypass the i-frames, so a blow
# landing inside the second of them a beam hit leaves is swallowed - the badge was up and the press on time, and
# nothing happens: no parry, no read for his gauge, and the press whiffs and costs its stamina. A volley's beams hurt
# up to their last frame, and from it his earliest blow in the next charge is messatsu_fade + strike_from +
# strike_show + strike_dash away, which was 0.89 s. --fixed-fps 60.
# A still player in the first volley's lines, kept clear of every beam hit but the one on its very last live frame,
# then his strike as early in the second charge as he may come (strike_from), answered with a tap on the read: the
# i-frames that hit left are over before his blow, and the tap parries it.

const RUSH_BEAM_ID := &"carter_rush_beam"
const STRIKE_ID := &"carter_teleport_strike"


static func run(t) -> void:
	var rush: Node = await t.load_carter_akuma()
	var sm: Node = t.sm
	var player: Node = t.player
	var defense: Node = t.defense
	player.playerHealth = 99
	await t.settle_player(Vector2(959, 800))
	t.clear_iframes()
	t.track()
	t.track_parries()
	var iframes: float = player.invincibility_timer.wait_time
	var earliest: float = sm.messatsu_fade + sm.strike_from + sm.strike_show + sm.strike_dash
	t.log_p("his earliest blow after a volley's last live frame: %.2f s (fade %.2f + strike_from %.2f + read %.2f + lunge %.2f), against %.2f s of i-frames" % [earliest, sm.messatsu_fade, sm.strike_from, sm.strike_show, sm.strike_dash, iframes])
	t.check(earliest > iframes + 1.5 / 60.0, "on paper his earliest blow comes after the i-frames a beam's last hit leaves, with a frame to spare (%.2f s against %.2f)" % [earliest, iframes])

	if not await t.start_beam_rush(rush, 1, sm.strike_from):
		t.check(false, "the Beam Rush starts, his strike put at strike_from (%.2f s) into the second charge" % sm.strike_from)
		return
	var last_live: float = sm.messatsu_travel + sm.beam_live
	var seen := {"faded_at": -1.0, "blow_at": -1.0, "invincible_at_blow": false}
	# Before each physics step: held invincible through the first volley's beams except for the step that is their
	# last live one, so the one hit they land is on it.
	var hold := func() -> void:
		if rush.volley == 0 and rush.beat == rush.Beat.STRING:
			var last_step: bool = rush.fire_clock + 1.5 / 60.0 >= last_live
			player.is_invincible = not last_step
			if not last_step:
				player.invincibility_timer.stop()
		if rush.volley == 0 and rush.beat == rush.Beat.FADE and seen.faded_at < 0.0:
			seen.faded_at = defense.clock
		if rush.strike == rush.Strike.HOLD and seen.blow_at < 0.0:
			seen.blow_at = defense.clock
			seen.invincible_at_blow = player.is_invincible
	t.physics_frame.connect(hold)
	var read_at: float = sm.strike_show + sm.strike_dash - 0.12
	var appeared: bool = await t.wait_until(func(): return rush.strike == rush.Strike.SHOW and rush.strike_clock >= read_at - 1.0 / 60.0, 900)
	if appeared:
		t.press(KEY_SHIFT)
		await t.wait(4)
		t.release(KEY_SHIFT)
	await t.wait_until(func(): return rush.strike == rush.Strike.DONE, 120)
	await t.wait(2)
	t.physics_frame.disconnect(hold)
	var beams: Array = t.events_of("HIT", RUSH_BEAM_ID)
	var struck: Array = t.events_of("HIT", STRIKE_ID)
	var parried: Array = t.parries.filter(func(p): return p.id == STRIKE_ID)
	var hit_at: float = beams[-1].t if not beams.is_empty() else -1.0
	t.log_p("beam hits %d, the last at %.3f, the beams stopped hurting at %.3f; his blow at %.3f, %.2f s after that hit, the player %s; strike hits %d, parries %d" % [beams.size(), hit_at, seen.faded_at, seen.blow_at, seen.blow_at - hit_at, "still invincible" if seen.invincible_at_blow else "not invincible", struck.size(), parried.size()])
	t.check(appeared, "he came in, in the second charge")
	t.check(beams.size() == 1 and seen.faded_at >= 0.0 and absf(seen.faded_at - hit_at) <= 1.5 / 60.0, "the first volley's one hit landed on its last live frame (%d hits, at %.3f, faded at %.3f)" % [beams.size(), hit_at, seen.faded_at])
	t.check(seen.blow_at - hit_at > iframes, "his blow came %.2f s after it, past the %.2f s of i-frames it left" % [seen.blow_at - hit_at, iframes])
	t.check(not seen.invincible_at_blow, "so the player was not invincible at his blow")
	t.check(parried.size() == 1 and struck.is_empty(), "and the tap on the read parried it (parries %d, hits %d)" % [parried.size(), struck.size()])
	sm.on_child_transition(sm.current_state, "Idle")
	sm.beat_timer.stop()
