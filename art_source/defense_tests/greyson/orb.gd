extends RefCounted

# greyson_orb (coder B): his doom orb (GreysonDoomOrb; the user's 2026-09-30 playtest), in his test fight on its
# placeholder art, his cycle parked and the poses entered from Idle as poses.gd does. In one run:
#   forms     pose 1 banks: the crowd's streaks set off at once, the orb forms only as they land (stage 2, two
#             banked cells), over his crown and clear of his bar and meter, on its layer under both fighters; the view
#             eases in on him and back out, once; the crowd's cheer up a cell's gain each banked cell.
#   grows     his meter from 2 to 4, as pose 2's bank would: stage 4 as its streaks land, and from vignette_from on
#             the vignette creeps in with the heartbeat's thump; the meter up top flashes as it grows.
#   bursts    a punch in his next pose: his meter empty, the orb gone in its pop with the glass, the streaks flung back
#             out, the vignette gone and the cheer back to its own level.
#   follows   his meter at 2 through his slams: the orb forms again with no second nudge, and stays over him from one
#             teleport to the next, hidden while he is.
#   hands off his meter at 4 into a pose's bank: stage 6 is his spirit bomb - the orb shows it over him, rides to
#             the muzzle as his arm goes up, and gives way to the sphere as it gathers, without bursting; with the
#             approved art the sphere gathers on from the frame the orb matches.
# Without a tier it runs on whatever art the game has: the approved sheets once imported. tier=final runs it all on
# the approved sheets (GreysonArtLayout.DOOM_ORB_ART), held in memory under their paths before his scene loads, as
# they are before the editor imports them; and checks what only they do: the foot pivot on his crown, the pulse and
# arrival frames a stage, the burst's row, the streak's heading rows, the drawn vignette. tier=placeholder swaps in
# an orb told to use no approved sheet at all, the placeholders it falls back on.

const Poses := preload("res://art_source/defense_tests/greyson/poses.gd")
const Layout := preload("res://Scripts/GreysonArtLayout.gd")
const FRAME := 1.0 / 60.0

# The approved sheets held in memory for tier=final, so the cache keeps them.
static var held: Array = []


static func run(t) -> void:
	var final: bool = t.tier == "final"
	if final:
		hold_approved(t)
	await Poses.enter(t)
	var orb: Node = t.boss.doom_orb
	t.check(orb != null and Layout.USE_DOOM_ORB, "his doom orb is up with his HUD")
	if orb == null:
		return
	var placeholder: bool = t.tier == "placeholder"
	if placeholder:
		orb = await placeholder_orb(t)
	# Without a tier, whatever the import has given the game.
	var approved: bool = final or (not placeholder and ResourceLoader.exists(Layout.DOOM_ORB_ART.orb))
	t.check(orb.final_art == approved and (orb.glow != null) == approved and orb.art.has("vignette") == approved,
		"on the %s art (%s)" % ["approved" if approved else "placeholder", orb.art.keys()])
	await forms_grows_bursts(t, orb)
	await follows(t, orb)
	await hands_off(t, orb)
	if approved:
		approved_only(t, orb)


# His orb swapped for one that uses no approved sheet: an `art` with none of DOOM_ORB_ART's keys in it.
static func placeholder_orb(t) -> Node:
	var old: Node = t.boss.doom_orb
	var orb: Node2D = load("res://Scripts/GreysonDoomOrb.gd").new()
	orb.body = t.boss
	orb.art = {"placeholders": true}
	old.queue_free()
	await t.wait(1)
	t.boss.get_parent().add_child(orb)
	t.boss.doom_orb = orb
	return orb


# Each approved PNG loaded from its shipped path and put in the cache under it: what the import will give the game.
static func hold_approved(t) -> void:
	held.clear()
	for key in Layout.DOOM_ORB_ART:
		var path: String = Layout.DOOM_ORB_ART[key]
		var image := Image.load_from_file(ProjectSettings.globalize_path(path))
		if image == null or image.is_empty():
			t.check(false, "the approved %s at %s" % [key, path])
			continue
		var texture := ImageTexture.create_from_image(image)
		texture.take_over_path(path)
		held.append(texture)
	t.log_p("the approved sheets in memory under their paths: %d of %d" % [held.size(), Layout.DOOM_ORB_ART.size()])


static func forms_grows_bursts(t, orb: Node) -> void:
	await Poses.reset(t)
	var spec: Dictionary = orb.spec
	var pose: Node = t.sm.states["Pose"]
	var cheer: AudioStreamPlayer = t.boss.sfx_players[&"crowd_cheer"][0]
	var base_db: float = cheer.get_meta(&"base_db")
	t.log_p("-- forms: pose 1 banks")
	Poses.start(t)
	await t.wait_until(func(): return pose.outcomes.size() == 1, 400)
	var sent: int = orb.streaks_in
	var shown_at_bank: bool = orb.is_shown()
	var zoomed := [1.0]
	var watch := func(): zoomed[0] = maxf(zoomed[0], load("res://Scripts/ScreenView.gd").zoom)
	t.physics_frame.connect(watch)
	var landed_frames := [0]
	var count := func(): landed_frames[0] += 1
	t.physics_frame.connect(count)
	await t.wait_until(func(): return orb.stage == 2, 60)
	t.physics_frame.disconnect(count)
	var arrival_frame: int = orb.orb.frame
	await t.wait(40)
	t.physics_frame.disconnect(watch)
	if orb.final_art:
		var fin: Dictionary = orb.final_spec
		var looping: int = orb.orb.frame
		t.log_p("the foot %s on his crown %s; the arrival frame %d, then %d" % [orb.foot, t.boss.crown_point(), arrival_frame, looping])
		t.check(orb.foot == (t.boss.crown_point() + Vector2(0.0, -orb.spec.gap)).round(), "its foot %.0f px over his crown" % orb.spec.gap)
		t.check(arrival_frame == fin.frames + fin.flash_frame and looping >= fin.frames and looping < fin.frames + fin.loop_frames.size(),
			"stage 2's row: its arrival flash as it lands, then its pulse loop")
	var view_back: bool = is_equal_approx(load("res://Scripts/ScreenView.gd").zoom, 1.0)
	var radius: float = orb.diameter(2) / 2.0
	var crown: Vector2 = t.boss.crown_point()
	var keep: Rect2 = t.sm.HUD_FADE_RECT
	var box := Rect2(orb.centre - Vector2.ONE * radius, Vector2.ONE * 2.0 * radius)
	t.log_p("streaks %d at the bank, shown then %s, stage 2 %.2f s after; at %s (his crown %s), %.0f px across; the view to %.2f and back %s; the cheer %.1f dB over its own"
		% [sent, shown_at_bank, landed_frames[0] * FRAME, orb.centre, crown, 2.0 * radius, zoomed[0], view_back, cheer.volume_db - base_db])
	t.check(sent == spec.streaks and not shown_at_bank, "the bank sends %d streaks from the crowd, and the orb isn't there yet" % spec.streaks)
	t.check(orb.stage == 2 and orb.is_shown() and landed_frames[0] * FRAME >= spec.streak_time - FRAME,
		"it forms as they land, at stage 2 for two banked cells (%.2f s)" % (landed_frames[0] * FRAME))
	t.check(orb.centre.y < crown.y and not box.intersects(keep), "over his crown, clear of his bar and meter")
	t.check(orb.position.y < t.player.global_position.y and orb.position.y < t.boss.global_position.y and orb.get_parent() == t.boss.get_parent(),
		"on its layer under both fighters")
	t.check(orb.nudges == 1 and zoomed[0] > 1.05 and view_back, "the view eases in on him the first time it forms, and back (%.2f)" % zoomed[0])
	t.check(is_equal_approx(cheer.volume_db - base_db, 2.0 * spec.cheer_gain_db), "the crowd's cheer %.1f dB up for two cells" % (2.0 * spec.cheer_gain_db))

	Poses.park(t)

	t.log_p("-- grows: his meter from 2 to 4 (as pose 2's bank would), standing at home")
	var flashed := [0.0]
	var vignette := [0.0]
	var thumps_before: int = orb.thumps
	var watch2 := func():
		var meter: Control = t.boss.hype_meter
		flashed[0] = maxf(flashed[0], meter.self_modulate.r)
		vignette[0] = maxf(vignette[0], orb.vignette.modulate.a)
	t.physics_frame.connect(watch2)
	t.boss.add_hype(2.0)
	await t.wait_until(func(): return orb.stage == 4, 60)
	await t.wait(60 * 2)
	t.physics_frame.disconnect(watch2)
	var thumps: int = orb.thumps - thumps_before
	t.log_p("stage %d, the vignette up to %.2f, %d thumps in 2 s, the meter flashed to %.2f" % [orb.stage, vignette[0], thumps, flashed[0]])
	t.check(orb.stage == 4 and orb.stage >= spec.vignette_from and vignette[0] >= spec.vignette_alphas[0] - 0.01,
		"stage 4, and the vignette in from stage %d (%.2f)" % [spec.vignette_from, vignette[0]])
	t.check(thumps >= 2, "with the heartbeat's thump (%d)" % thumps)
	t.check(flashed[0] > 1.2, "and the meter up top flashing with it (%.2f)" % flashed[0])

	t.log_p("-- bursts: a punch in his next pose")
	t.sm.on_child_transition(t.sm.current_state, "Pose")
	await t.wait_until(func(): return pose.pose_index == 0 and pose.pose_clock >= 0.3, 200)
	var bursts_before: int = orb.bursts
	var out_before: int = orb.streaks_out
	var glass: AudioStreamPlayer = t.boss.sfx_players[&"orb_burst"][0]
	t.player.combo.reset()
	var dealt: int = await Poses.punch(t)
	var burst_row: int = orb.burst_row
	var glass_heard: bool = glass.playing
	var gone: bool = not orb.is_shown()
	await t.wait(60)
	t.log_p("dealt %d, his meter %.1f, the orb shown %s, bursts %d, streaks out %d, the glass %s, the vignette %.2f, the cheer %.1f dB over its own"
		% [dealt, t.boss.hype, orb.is_shown(), orb.bursts - bursts_before, orb.streaks_out - out_before, glass_heard, orb.vignette.modulate.a, cheer.volume_db - base_db])
	t.check(dealt > 0 and t.boss.hype == 0.0 and gone and orb.bursts - bursts_before == 1 and orb.stage == 0, "the punch empties his meter and bursts the orb")
	t.check(orb.streaks_out - out_before == spec.streaks and glass_heard, "the streaks flung back out to the crowd, with the glass")
	t.check(orb.vignette.modulate.a < 0.05 and is_equal_approx(cheer.volume_db, base_db), "the vignette gone and the cheer back to its own level")
	if orb.final_art:
		t.check(burst_row == 1, "the big burst for a stage 4 orb (row %d)" % burst_row)
	Poses.park(t)


static func follows(t, orb: Node) -> void:
	t.log_p("-- follows: his meter at 2 through his slams")
	await Poses.reset(t)
	t.boss.add_hype(2.0)
	await t.wait_until(func(): return orb.stage == 2, 60)
	var slams: Node = t.sm.states["Slams"]
	t.sm.on_child_transition(t.sm.current_state, "Slams")
	var worst := [0.0]
	var shown_hidden := [0]
	var spots := {}
	var watch := func():
		if not t.boss.sprite.visible:
			shown_hidden[0] += 1 if orb.is_shown() else 0
			return
		var crown: Vector2 = t.boss.crown_point()
		worst[0] = maxf(worst[0], absf(orb.centre.x - crown.x))
		spots[t.boss.global_position] = true
	t.physics_frame.connect(watch)
	await t.wait_until(func(): return t.sm.current_state != slams, 60 * 8)
	t.physics_frame.disconnect(watch)
	t.log_p("nudges %d; over him at %d spots, at most %.0f px off his crown sideways; shown while he was hidden %d frames" % [orb.nudges, spots.size(), worst[0], shown_hidden[0]])
	t.check(orb.nudges == 1, "no second nudge: once a fight")
	t.check(spots.size() >= 3 and worst[0] <= 1.0, "over him from one teleport to the next")
	t.check(shown_hidden[0] == 0, "and hidden while he is")
	Poses.park(t)


static func hands_off(t, orb: Node) -> void:
	t.log_p("-- hands off: his meter at 4 into a pose's bank")
	await Poses.reset(t)
	t.boss.add_hype(4.0)
	await t.wait_until(func(): return orb.stage == 4, 60)
	var bursts: int = orb.bursts
	var pose: Node = t.sm.states["Pose"]
	var bomb: Node = t.sm.states["SpiritBomb"]
	Poses.start(t)
	await t.wait_until(func(): return t.sm.current_state == bomb, 400)
	await t.wait_until(func(): return bomb.beat == bomb.Beat.ARM, 120)
	await t.wait(5)
	var riding: bool = orb.riding and orb.is_shown() and orb.stage == 6
	var from: Vector2 = orb.foot
	# Its foot on the arm's last step, and the muzzle then.
	var ride := {"foot": orb.foot, "to": Vector2.ZERO}
	var watch := func():
		if bomb.beat == bomb.Beat.ARM:
			ride.foot = orb.foot
			ride.to = (t.boss.muzzle_point(&"spirit") + orb.final_spec.handoff_lift).round()
	t.physics_frame.connect(watch)
	await t.wait_until(func(): return bomb.beat != bomb.Beat.ARM, 120)
	t.physics_frame.disconnect(watch)
	var to: Vector2 = ride.to
	var last_foot: Vector2 = ride.foot
	await t.wait(2)
	var fx: Node = bomb.fx
	var want_first: int = orb.final_spec.handoff_bomb_frame if orb.final_art else 0
	t.log_p("through the arm: shown at stage 6 %s, its foot from %s to %s (the muzzle's lift %s); then shown %s, handed off %s, bursts %d -> %d; the sphere from frame %d, now %d"
		% [riding, from, last_foot, to, orb.is_shown(), orb.handed_off, bursts, orb.bursts, fx.first_frame if fx else -1, fx.sphere.frame if fx else -1])
	t.check(riding and last_foot.distance_to(to) <= 2.0, "stage 6 over him, riding to the cannon's muzzle as his arm goes up")
	t.check(not orb.is_shown() and orb.handed_off and orb.bursts == bursts and fx != null and fx.first_frame == want_first and fx.sphere.frame >= want_first,
		"and giving way to the sphere, which gathers on from frame %d, without bursting" % want_first)


# What only the approved sheets do: a streak's row turns with its heading; the vignette is the drawn one.
static func approved_only(t, orb: Node) -> void:
	t.log_p("-- the approved sheets' own rules")
	var rows := [orb.heading_row(Vector2.RIGHT), orb.heading_row(Vector2.DOWN), orb.heading_row(Vector2.LEFT), orb.heading_row(Vector2.UP),
		orb.heading_row(Vector2(1, 1))]
	t.log_p("heading rows right, down, left, up and down-right: %s" % [rows])
	t.check(rows == [0, 4, 8, 12, 2], "a streak's row from its heading, row 0 flying right and 4 down")
	t.check(orb.vignette.texture == orb.art.vignette, "the drawn vignette")
