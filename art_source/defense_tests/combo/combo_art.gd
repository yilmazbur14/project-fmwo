extends RefCounted

# combo_art [tier=off|missing]: hits 2 and 3 of the combo drawn apart from hit 1 (PunchComboArtLayout, the
# user's ask of 2026-09-25), and the visual chain that runs them 1-2-3 on any quick swings, landed or not
# (the user, 2026-09-27), on Eric parked and down in his own fight. The combo has had no timing since
# 2026-09-30 (PlayerCombo): a count it carries decides how a swing is drawn, and the chain only runs with
# nothing carried. A count lives PlayerCombo.COMBO_RESET_TIME without a punch landing (2026-10-04), and every
# punch here that is meant to carry one lands inside it. --fixed-fps 60.
# The switch ships on: the user approved the art (2026-09-25). The game finds the sheet once the editor has
# imported it; on a checkout where it hasn't, this puts an in-memory stand-in for it in the resource cache
# under its path, built from player_4dir_sheet.png's punch columns. Nothing is written or imported.
#   (default)  the sheet in the project is 256x128 with all 32 cells drawn; "punch_2" and "punch_3" are
#              "punch" key for key but for their columns, 0-3 and 4-7, and "punch" is as it was.
#              The quick gap is PlayerFeel's punch_chain_gap: 0.29 s under feel_v2, 0.40 s without.
#              Pressed quick or slow, landed hits 1, 2 and 3 play "punch", "punch_2" and "punch_3", the third
#              the charged punch, 2 and 3 on the combo sheet in the facing's row, the swoosh on the same beats,
#              their star across the punch on their drawn fist, and the POW wraps to "punch". Into the air with
#              nothing carried, quick swings run punch, punch_2, punch_3, punch... A swing 17 frames after the
#              last one ended carries the chain on and one 18 frames after starts it again (23 and 25 frames
#              without feel_v2), while onto him either gap carries the count on. Air swings, then onto him: the
#              chain carries into the first punch that lands, the count decides from the second, its charged
#              punch is punch_3 with the whole POW, and a body blow that isn't charged shows none of it. A slow
#              press, a mashed one, a whiff, a refused punch and a hit taken all keep the count: the whiff and
#              the refusal are drawn as punch_2 for it, and the swing after lands as the second, punch_2 for 2
#              HITS. With PlayerCombo.keep_count_when_hit off, a hit taken, a guard break and an action lock
#              each start the count again; on, none does. Over the whole run: enable_hitbox on the same physics
#              frame of every swing, and punch_3 the charged punch whenever the count is at it. A swing hit
#              mid-way keeps its art and its count, and lands as the combo's second. However a swing on the
#              combo sheet ends, the sprite is back on its own sheet: run out, a grab, a pose a fight holds it in
#              (on the fight's sheet meanwhile), a scripted pose, a pause (held on the combo sheet through it),
#              the finisher its POW starts, and the fight's end. A sprite on a sheet of a fight's own is left on
#              it, whether it was on it as the swing started (which then falls back to "punch") or was put on it
#              mid-swing.
#   off        the switch off: nothing built, every punch is "punch", a combo on him or quick into the air.
#   missing    the switch on, the sheet not imported or not there: the same. Skipped once it's imported.

const Layout := preload("res://Scripts/PunchComboArtLayout.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const MattArtLayout := preload("res://Scripts/MattArtLayout.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")

const LAYOUT_SCRIPT := "res://Scripts/PunchComboArtLayout.gd"
const BASE_SHEET := "res://Assets/Characters/MainPlayer/player_4dir_sheet.png"
const BASE_GRID := Vector2i(10, 4)
const PUNCH_COLUMNS := [5, 6, 7, 8]
const CELL := 32
const FRAME_TRACK := ^"Sprite2D:frame_coords:x"
const STEP := 1.0 / 60.0
# The physics frame of a swing that the cases which cut one short cut it on: the arm on its way out.
const CUT_AT := 5
# A finisher nobody mashes has to run itself out.
const FINISHER_FRAMES := 1500
# Where the player swings at nothing: this far below the spot under his hurtbox, still facing him.
const AIR := Vector2(0, 250)
# Physics frames from the last swing's end to the next one's start, inside the quick gap and past it,
# by feel_v2: its 0.29 s is 17.4 frames; without it, 0.40 s is 24, which is too close to call either way.
const QUICK_FRAMES := {true: [17, 18], false: [23, 25]}
# A slow press: this many physics frames after the last swing ended, past the quick gap either way, and landing
# inside PlayerCombo.COMBO_RESET_TIME of the punch before it (about 52 frames between the two), so the count is
# still there for it. combo_reset has a press past it.
const SLOW_FRAMES := 30
# Swings into the air, then onto him on the next quick press and slow ones after it, to the POW.
const MIXED := {
	1: ["punch", "punch_2", "punch_2", "punch_3"],
	2: ["punch", "punch_2", "punch_3", "punch_2", "punch_3"],
	3: ["punch", "punch_2", "punch_3", "punch", "punch_2", "punch_3"],
}

# Every swing of the run, for the checks over all of them.
static var ran: Array = []


static func run(t) -> void:
	ran.clear()
	var source := FileAccess.get_file_as_string(LAYOUT_SCRIPT)
	t.check(source.contains("static var COMBO_ANIMS_ENABLED := true") and Layout.COMBO_ANIMS_ENABLED, "the switch ships on, and this run starts with it on")
	match t.tier:
		"off":
			t.log_p("-- the switch off, with the sheet in")
			var sheet := sheet_in(t)
			Layout.COMBO_ANIMS_ENABLED = false
			await load_down(t)
			await check_all_hit_one(t, sheet)
		"missing":
			if ResourceLoader.exists(Layout.SHEET):
				t.log_p("the sheet is imported, so there is no missing sheet to try")
				return
			t.log_p("-- the switch on, the sheet %s" % ("in the project but not imported" if FileAccess.file_exists(Layout.SHEET) else "missing"))
			Layout.COMBO_ANIMS_ENABLED = true
			await load_down(t)
			await check_all_hit_one(t, null)
		_:
			check_real_sheet(t)
			var sheet := sheet_in(t)
			Layout.COMBO_ANIMS_ENABLED = true
			await load_down(t)
			await run_on(t, sheet)


static func run_on(t, sheet: Texture2D) -> void:
	var punching: Node = punching_of(t)
	var base: Texture2D = t.player.sprite.texture
	t.check(punching.combo_sheet == sheet and punching.base_sheet == base and base.resource_path == BASE_SHEET, "the combo sheet is found under its path, and the sprite's own sheet noted")
	check_built(t)

	t.log_p("-- the quick gap is PlayerFeel's punch_chain_gap, the numbers the combo's beat window closed on")
	for v2 in [true, false]:
		t.player.feel_v2 = v2
		var gap: float = punching.quick_gap()
		t.check(is_equal_approx(gap, t.feel("punch_chain_gap")) and is_equal_approx(gap, 0.29 if v2 else 0.40),
			"%s: %.2f s after the last swing ends, %.1f physics frames" % [feel_name(v2), gap, gap / STEP])
	t.player.feel_v2 = true

	t.log_p("-- quick or slow: landed hits 1, 2 and 3, then the POW wraps to 1")
	var chain := []
	for when in ["fresh", "slow", "quick", "slow", "quick", "slow"]:
		chain.append(await swing(t, when))
	log_swings(t, chain)
	var played: Array = chain.map(func(s): return s.animation)
	t.check(played == ["punch", "punch_2", "punch_3", "punch", "punch_2", "punch_3"], "punch, punch_2, punch_3, then punch again (%s)" % [played])
	t.check(chain.all(func(s): return s.playing == s.animation and s.fx_animation == s.animation), "each is what the AnimationPlayer plays and what PunchFx draws for")
	t.check(chain.map(func(s): return s.charged) == [false, false, true, false, false, true] and chain.all(func(s): return s.dealt == (2 if s.charged else 1)), "punch_3 is exactly the charged punch, for 2")
	for s in chain:
		check_drawn(t, s, sheet, base)
	t.check(chain.all(func(s): return s.swoosh == [0, 1]), "the swoosh snaps out and reaches full extension on the same beats of each (%s)" % [chain.map(func(s): return s.swoosh)])
	t.check(chain.map(func(s): return s.star_row) == [0, 0, 1, 0, 0, 1], "a white star for hits 1 and 2, the gold one for 3 (%s)" % [chain.map(func(s): return s.star_row)])
	t.check(chain.all(func(s): return pow_shown(s) == s.charged and (not s.charged or (s.shook and s.gold and s.counter == "3 POW!"))),
		"the charged punches show the whole POW and the others none of it, the punch right after one included (%s)" % [chain.map(func(s): return pow_shown(s))])
	var on_fist := []
	for s in chain.filter(func(s): return Layout.GLOVE_FRONTS.has(s.animation)):
		var fist: Vector2 = (t.player.global_transform * Layout.GLOVE_FRONTS[s.animation][s.facing]).round()
		on_fist.append(is_equal_approx(across(s.facing, s.star_at), across(s.facing, fist)))
	t.check(on_fist.size() == 4 and not on_fist.has(false), "the star of hits 2 and 3 sits on their drawn fist across the punch, not on the hitbox's middle (%s)" % [chain.map(func(s): return s.star_at)])

	t.log_p("-- into the air: quick swings run 1-2-3 whether they land or not")
	await settle(t)
	await t.settle_player(t.player.global_position + AIR)
	var air := []
	for when in ["fresh", "quick", "quick", "quick", "quick", "quick"]:
		air.append(await swing(t, when))
	log_swings(t, air)
	played = air.map(func(s): return s.animation)
	t.check(played == ["punch", "punch_2", "punch_3", "punch", "punch_2", "punch_3"], "punch, punch_2, punch_3, then punch again (%s)" % [played])
	t.check(air.all(func(s): return s.dealt == 0 and not s.refused and s.position == 0 and not pow_shown(s)), "none of them lands, none is the combo's, and none shows any of the POW")
	t.check(air.slice(1).all(func(s): return s.gap <= punching.quick_gap()), "each started quick after the last one ended (%s s)" % [air.slice(1).map(func(s): return snappedf(s.gap, 0.001))])
	for s in air:
		check_drawn(t, s, sheet, base)

	t.log_p("-- the gap: one frame past it starts a chain in the air again, and onto him it is nothing to the count")
	for v2 in [true, false]:
		t.player.feel_v2 = v2
		t.player.fit_punch_hitbox()
		var inside: int = QUICK_FRAMES[v2][0]
		var past: int = QUICK_FRAMES[v2][1]
		await settle(t)
		await t.settle_player(t.player.global_position + AIR)
		var gaps := [await swing(t, "fresh")]
		for frames in [inside, past, inside, inside]:
			gaps.append(await swing(t, "gap", Callable(), frames))
		log_swings(t, gaps)
		played = gaps.map(func(s): return s.animation)
		var measured: Array = gaps.slice(1).map(func(s): return roundi(s.gap / STEP))
		t.check(measured == [inside, past, inside, inside], "%s: the swings started %s frames after the last ones ended" % [feel_name(v2), measured])
		t.check(played == ["punch", "punch_2", "punch", "punch_2", "punch_3"], "%s: %d frames on carries the chain on, %d starts it again (%s)" % [feel_name(v2), inside, past, played])
	t.player.feel_v2 = true
	t.player.fit_punch_hitbox()
	await settle(t)
	var inside_gap := [await swing(t, "fresh"), await swing(t, "gap", Callable(), QUICK_FRAMES[true][0])]
	await settle(t)
	var past_gap := [await swing(t, "fresh"), await swing(t, "gap", Callable(), QUICK_FRAMES[true][1])]
	log_swings(t, inside_gap + past_gap)
	for pair in [inside_gap, past_gap]:
		t.check(pair[0].dealt == 1 and pair[1].position == 1 and pair[1].animation == "punch_2" and pair[1].dealt == 1 and pair[1].counter == "2 HITS",
			"onto him, %d frames on: the combo goes on, punch_2 for its 2 HITS (%s, '%s')" % [roundi(pair[1].gap / STEP), pair[1].animation, pair[1].counter])

	t.log_p("-- mixed: quick swings into the air, then onto him")
	for n in MIXED:
		await settle(t)
		await t.settle_player(t.player.global_position + AIR)
		var mixed := []
		for i in n:
			mixed.append(await swing(t, "fresh" if i == 0 else "quick"))
		t.place_under(hurtbox(t))
		mixed.append(await swing(t, "quick"))
		while mixed.size() < MIXED[n].size() and not mixed[-1].charged:
			mixed.append(await swing(t, "slow"))
		log_swings(t, mixed)
		played = mixed.map(func(s): return s.animation)
		var landed: Array = mixed.slice(n)
		t.check(played == MIXED[n], "%d into the air, then onto him: %s" % [n, played])
		t.check(mixed.slice(0, n).all(func(s): return s.dealt == 0) and landed.map(func(s): return s.dealt) == [1, 1, 2] and landed.map(func(s): return s.position) == [0, 1, 2],
			"%d into the air: the combo counts from the first punch that lands, for 1, 1, then the POW for 2 (%s)" % [n, landed.map(func(s): return s.dealt)])
		var pow_swing: Dictionary = landed[-1]
		t.check(pow_swing.animation == "punch_3" and pow_swing.charged and pow_swing.pows == 1 and pow_swing.star_row == 1 and pow_swing.counter == "3 POW!" and pow_swing.shook and pow_swing.gold,
			"%d into the air: the POW is punch_3, with the gold star, 3 POW!, the shake and the gold flash on him" % n)
		for s in landed.slice(0, 2):
			t.check(not s.charged and not pow_shown(s) and s.star_row == 0 and s.stopped == landed[1].stopped and s.stopped < pow_swing.stopped,
				"%d into the air: %s for 1 shows none of the POW (star row %d, %s, a %d-frame stop against the POW's %d)" % [n, s.animation, s.star_row, s.counter, s.stopped, pow_swing.stopped])

	t.log_p("-- a slow press, a mashed one, a whiff, a refused punch and a hit taken all keep the count")
	for how in ["slow", "mashed", "whiff", "refused", "hit"]:
		await settle(t)
		# A mashed press: a second one on the first swing's CUT_AT-th frame, the arm on its way out.
		var mash := func(): t.tap(KEY_Q)
		var first: Dictionary = await swing(t, "fresh", mash if how == "mashed" else Callable())
		var missed := {}
		var next: Dictionary
		match how:
			"slow":
				next = await swing(t, "slow")
			"mashed":
				next = await swing(t, "quick")
			"whiff":
				await t.settle_player(t.player.global_position + AIR)
				missed = await swing(t, "quick")
				t.place_under(hurtbox(t))
				next = await swing(t, "quick")
			"refused":
				var box := hurtbox(t)
				box.set_deferred("monitoring", false)
				box.set_deferred("monitorable", false)
				missed = await swing(t, "quick")
				box.set_deferred("monitoring", true)
				box.set_deferred("monitorable", true)
				next = await swing(t, "quick")
			"hit":
				t.clear_iframes()
				var result: int = t.player.receive_hit(HitInfo.make(&"untagged", t.dummy_source(), t.player.global_position))
				t.check(result == HitInfo.Result.HIT, "hit: the hit lands (%s)" % HitInfo.Result.keys()[result])
				next = await swing(t, "quick")
		log_swings(t, [first, missed, next].filter(func(s): return not s.is_empty()))
		t.check(first.animation == "punch" and first.dealt == 1, "%s: hit 1 lands" % how)
		if not missed.is_empty():
			t.check(missed.animation == "punch_2" and missed.position == 1 and missed.dealt == 0 and missed.refused == (how == "refused"), "%s: it is drawn as the second, for the count, and lands nothing (%s, dealt %d, refused %s)" % [how, missed.animation, missed.dealt, missed.refused])
			check_drawn(t, missed, sheet, base)
		t.check(next.position == 1 and next.dealt == 1 and not next.charged and next.counter == "2 HITS", "%s: the next swing lands as the combo's second, for 1 (%s)" % [how, next.counter])
		t.check(next.animation == "punch_2" and not pow_shown(next), "%s: it plays punch_2, %.3f s after the last one ended, and shows none of the POW (%s)" % [how, next.gap, next.animation])

	t.log_p("-- keep_count_when_hit: on, a hit taken, a guard break and an action lock keep the count; off, each starts it again")
	var combo: Node = t.player.combo
	t.check(combo.keep_count_when_hit, "it ships on")
	for keep in [true, false]:
		combo.keep_count_when_hit = keep
		var counts := {}
		for how in ["hit", "guard_break", "lock"]:
			await settle(t)
			await swing(t, "fresh")
			match how:
				"hit":
					t.clear_iframes()
					t.player.receive_hit(HitInfo.make(&"untagged", t.dummy_source(), t.player.global_position))
				"guard_break":
					t.defense._start_guard_break()
					await t.wait(3)
					t.defense.clear_guard_break()
				"lock":
					t.player.lock_actions()
					await t.wait(3)
					t.player.unlock_actions()
			await t.wait(3)
			counts[how] = combo.count
		t.log_p("%s: the count after each %s" % ["on" if keep else "off", counts])
		t.check(counts.values().all(func(c): return c == (1 if keep else 0)), "%s: every one %s (%s)" % ["on" if keep else "off", "keeps the count at 1" if keep else "starts it again", counts])
	combo.keep_count_when_hit = true

	t.log_p("-- a hit taken mid-swing: the swing keeps its art and its count, and lands as the combo's second")
	await settle(t)
	var hit_mid := func():
		t.clear_iframes()
		t.player.receive_hit(HitInfo.make(&"untagged", t.dummy_source(), t.player.global_position))
	var run_in: Array = [await swing(t, "fresh"), await swing(t, "quick", hit_mid)]
	run_in.append(await swing(t, "quick"))
	log_swings(t, run_in)
	var cut: Dictionary = run_in[1]
	t.check(cut.animation == "punch_2" and cut.dealt == 1 and not cut.charged and cut.sheets == [sheet] and cut.counter == "2 HITS", "the hit swing plays out as punch_2 on the combo sheet and lands for 1, 2 HITS")
	check_after(t, cut, base, "after it")
	t.check(run_in[2].animation == "punch_3" and run_in[2].charged, "then the charged punch_3, the count kept through the hit (%s)" % run_in[2].animation)

	t.log_p("-- the sprite is back on its own sheet however a swing on the combo sheet ends")
	await settle(t)
	await swing(t, "fresh")
	var grabbed: Dictionary = await swing(t, "quick", func(): t.player.grab())
	t.check(grabbed.animation == "punch_2" and t.player.is_grabbed, "a grab mid-swing")
	check_after(t, grabbed, base, "grabbed")
	t.player.release_grab(Vector2.DOWN)
	await t.wait(90)

	await settle(t)
	await swing(t, "fresh")
	var pose: Dictionary = MattArtLayout.PLAYER_POSE_SHEET
	var took := [false]
	var posed: Dictionary = await swing(t, "quick", func():
		t.player.lock_actions()
		took[0] = t.player.hold_pose(pose))
	t.log_p("posed: %s, the sprite on %s %s" % [took[0], posed.after.texture.resource_path.get_file(), posed.after.grid])
	t.check(posed.animation == "punch_2" and took[0] and posed.after.texture.resource_path == pose.texture and posed.after.grid == Vector2i(pose.hframes, pose.vframes), "a pose a fight holds the player in mid-swing wears the fight's own sheet")
	t.player.unlock_actions()
	await t.wait(2)
	check_sprite(t, base, "the pose over")

	var sprite: Sprite2D = t.player.sprite
	var theirs: Texture2D = load(pose.texture)
	var wear_theirs := func():
		sprite.texture = theirs
		sprite.hframes = pose.hframes
		sprite.vframes = pose.vframes
	await settle(t)
	await swing(t, "fresh")
	wear_theirs.call()
	var on_theirs: Dictionary = await swing(t, "quick")
	t.check(on_theirs.position == 1 and on_theirs.animation == "punch" and on_theirs.sheets == [theirs] and on_theirs.after.texture == theirs, "a sprite on a sheet of a fight's own as the swing starts keeps it, and the swing falls back to \"punch\" (%s)" % on_theirs.animation)
	wear_own(t, base)
	await settle(t)
	await swing(t, "fresh")
	var taken: Dictionary = await swing(t, "quick", wear_theirs)
	t.check(taken.animation == "punch_2" and taken.after.texture == theirs and taken.after.grid == Vector2i(pose.hframes, pose.vframes), "one put on a sheet of a fight's own mid-swing is left on it (%s)" % taken.after.texture.resource_path.get_file())
	wear_own(t, base)

	await settle(t)
	await swing(t, "fresh")
	var still: Dictionary = await swing(t, "quick", func(): t.player.set_scripted_pose(true))
	t.check(still.animation == "punch_2" and t.player.scripted_pose, "a scripted pose mid-swing")
	check_after(t, still, base, "held still")
	t.player.set_scripted_pose(false)
	await t.wait(4)

	await settle(t)
	await swing(t, "fresh")
	var pause: Node = t.pause_menu()
	var held := {}
	var paused: Dictionary = await swing(t, "quick", func():
		await t.tap_pause()
		held.open = pause.is_open() and t.paused
		held.at = [t.player.sprite.texture, t.player.sprite.frame_coords, t.player.state_machine.current_state.name]
		await t.wait(40)
		held.later = [t.player.sprite.texture, t.player.sprite.frame_coords, t.player.state_machine.current_state.name]
		await t.tap_pause()
		# Real seconds, which --fixed-fps frames don't spend: it would eat the next presses.
		pause.grace_until_msec = 0
		held.resumed = not pause.is_open() and not t.paused)
	t.log_p("paused at %s, 40 frames later %s" % [held.get("at"), held.get("later")])
	t.check(paused.animation == "punch_2" and held.get("open", false) and held.get("resumed", false), "paused mid-swing and resumed")
	t.check(held.get("at", [null])[0] == sheet and held.get("later") == held.get("at") and held.at[2] == "Punching", "the swing holds on the combo sheet through the pause")
	t.check(paused.columns == [0, 1, 2, 3], "and plays out after it (%s)" % [paused.columns])
	check_after(t, paused, base, "paused and run out")

	t.log_p("-- the finisher a POW starts")
	await settle(t)
	t.boss.daze_used = false
	var finisher: Node = t.player.get_node("Finisher")
	var pow := []
	for when in ["fresh", "quick", "quick"]:
		pow.append(await swing(t, when))
	log_swings(t, pow)
	t.check(pow.map(func(s): return s.animation) == ["punch", "punch_2", "punch_3"] and pow[2].charged, "punch_3 is the charged punch")
	check_after(t, pow[2], base, "its swing run out")
	var finishing: bool = await t.wait_until(func(): return t.player.state_machine.current_state.name == "Finishing", 240)
	var wearing: Texture2D = t.player.sprite.texture
	t.check(finishing and wearing != sheet and wearing.resource_path == finisher.texture_path(), "the finisher's own sheet on the sprite (%s)" % wearing.resource_path.get_file())
	t.check(await t.wait_until(func(): return not finisher.is_active(), FINISHER_FRAMES), "the finisher runs out")
	await t.wait(4)
	check_sprite(t, base, "the finisher over")

	t.log_p("-- the fight's end")
	await open_down(t)
	await settle(t)
	await swing(t, "fresh")
	var ended: Dictionary = await swing(t, "quick", func():
		t.player.playerHealth = 1
		t.clear_iframes()
		t.player.receive_hit(HitInfo.make(&"untagged", t.dummy_source(), t.player.global_position)))
	t.check(ended.animation == "punch_2" and t.player.fight_over, "the fight lost mid-swing")
	check_after(t, ended, base, "the fight over")

	t.log_p("-- every swing of the run (%d)" % ran.size())
	var own: Array = ran.filter(func(s): return not s.sheets.is_empty() and (s.sheets[0] == base or s.sheets[0] == sheet))
	var alive: Array = own.filter(func(s): return s.position > 0)
	var alive_wrong: Array = alive.filter(func(s): return s.animation != ("punch_3" if s.position == t.player.combo.hits_to_charge - 1 else "punch_2"))
	t.check(not alive.is_empty() and alive_wrong.is_empty(), "while the combo is alive it decides: punch_2 at its second punch, punch_3 at its charged third (%d swings, wrong: %s)" % [alive.size(), alive_wrong.map(func(s): return s.animation)])
	var charged: Array = ran.filter(func(s): return s.charged)
	t.check(not charged.is_empty() and charged.all(func(s): return s.animation == "punch_3"), "every charged punch played punch_3 (%d)" % charged.size())
	var plain_blows: Array = ran.filter(func(s): return s.animation == "punch_3" and not s.charged and s.dealt > 0)
	t.check(not plain_blows.is_empty() and plain_blows.all(func(s): return not pow_shown(s)), "and none of the %d body blows that landed uncharged showed any of the POW" % plain_blows.size())
	var offsets := {}
	for s in ran.filter(func(s): return not s.cut and s.extended_at >= 0):
		var offset: int = s.extended_at - s.entered_at
		if not offsets.has(offset):
			offsets[offset] = {}
		offsets[offset][s.animation] = offsets[offset].get(s.animation, 0) + 1
	t.check(offsets.size() == 1 and offsets.values()[0].size() == 3, "enable_hitbox fires on the same physics frame of every swing, all three alike: +frame: {animation: swings} %s" % [offsets])


# The switch off or the sheet missing: nothing built, and a clean combo and quick swings into the air are
# hit 1's art every time.
static func check_all_hit_one(t, sheet: Texture2D) -> void:
	var anims: AnimationPlayer = t.player.animation_player
	t.check(punching_of(t).combo_sheet == null and not anims.has_animation(Layout.OTHER_HAND) and not anims.has_animation(Layout.BODY_BLOW), "nothing is loaded or built")
	var base: Texture2D = t.player.sprite.texture
	var chain := []
	for when in ["fresh", "quick", "quick"]:
		chain.append(await swing(t, when))
	await settle(t)
	await t.settle_player(t.player.global_position + AIR)
	var air := []
	for when in ["fresh", "quick", "quick"]:
		air.append(await swing(t, when))
	log_swings(t, chain + air)
	t.check(chain.map(func(s): return s.animation) == ["punch", "punch", "punch"] and chain.map(func(s): return s.charged) == [false, false, true], "a clean combo is \"punch\" three times, the third the charged one")
	t.check(air.map(func(s): return s.animation) == ["punch", "punch", "punch"] and air.all(func(s): return s.dealt == 0), "and three quick swings into the air are \"punch\" three times")
	var all: Array = chain + air
	t.check(all.all(func(s): return s.sheets == [base] and s.grids == [BASE_GRID] and s.after.texture == base and s.columns.slice(-4) == PUNCH_COLUMNS), "all on the player's own sheet, on hit 1's columns")
	t.check(all.all(func(s): return s.swoosh == [0, 1]), "with today's swoosh (%s)" % [all.map(func(s): return s.swoosh)])
	if sheet != null:
		t.check(all.all(func(s): return not s.sheets.has(sheet)), "the sheet in the project never shows")


# "punch_2" and "punch_3" against "punch", track by track and key by key.
static func check_built(t) -> void:
	var anims: AnimationPlayer = t.player.animation_player
	var punch: Animation = anims.get_animation("punch")
	var frames := punch.find_track(FRAME_TRACK, Animation.TYPE_VALUE)
	t.check(column_keys(punch, frames) == PUNCH_COLUMNS, "\"punch\" is as it was: columns %s" % [column_keys(punch, frames)])
	for animation in Layout.FIRST_COLUMNS:
		if not anims.has_animation(animation):
			t.check(false, "%s is built" % animation)
			continue
		var hit: Animation = anims.get_animation(animation)
		var alike := hit.length == punch.length and hit.step == punch.step and hit.loop_mode == punch.loop_mode and hit.get_track_count() == punch.get_track_count()
		for track in punch.get_track_count():
			if not alike:
				break
			alike = hit.track_get_type(track) == punch.track_get_type(track) and hit.track_get_path(track) == punch.track_get_path(track) \
				and hit.track_get_interpolation_type(track) == punch.track_get_interpolation_type(track)
			if track == frames:
				alike = alike and hit.value_track_get_update_mode(track) == punch.value_track_get_update_mode(track) \
					and beats(hit, track) == beats(punch, track)
			else:
				alike = alike and keys(hit, track) == keys(punch, track)
		var first: int = Layout.FIRST_COLUMNS[animation]
		t.log_p("%s: length %.5f, %d tracks, frame keys %s, %s keys %s" % [animation, hit.length, hit.get_track_count(), keys(hit, frames), hit.track_get_path(1), keys(hit, 1)])
		t.check(alike, "%s is \"punch\" key for key: length, beats, update mode and the enable_hitbox key" % animation)
		t.check(column_keys(hit, frames) == [first, first + 1, first + 2, first + 3], "%s steps columns %d-%d" % [animation, first, first + 3])


# [time, transition, value] per key; a method key's value is its method and arguments.
static func keys(anim: Animation, track: int) -> Array:
	var out := []
	for key in anim.track_get_key_count(track):
		var value = anim.track_get_key_value(track, key)
		if anim.track_get_type(track) == Animation.TYPE_METHOD:
			value = [anim.method_track_get_name(track, key), anim.method_track_get_params(track, key)]
		out.append([anim.track_get_key_time(track, key), anim.track_get_key_transition(track, key), value])
	return out


static func beats(anim: Animation, track: int) -> Array:
	return keys(anim, track).map(func(k): return k.slice(0, 2))


static func column_keys(anim: Animation, track: int) -> Array:
	return keys(anim, track).map(func(k): return k[2])


# One swing: "fresh" at once, on a chain of its own after settle(); "quick" at once, right behind the last
# swing; "slow" SLOW_FRAMES after the last one ended; "gap" started `gap_frames` physics frames after the last
# one ended. `cut` is called, and awaited, on the swing's CUT_AT-th physics frame. What it played and showed
# on every physics frame of it, and the sprite on the first one after it.
static func swing(t, when: String, cut := Callable(), gap_frames := 0) -> Dictionary:
	var combo: Node = t.player.combo
	var punching: Node = punching_of(t)
	match when:
		"slow":
			await t.wait_until(func(): return combo.clock - punching.chain_ended_at >= (SLOW_FRAMES - 1) * STEP - 0.001, 120)
		"gap":
			# The press is read in the next frame's input, a physics step on.
			await t.wait_until(func(): return combo.clock - punching.chain_ended_at >= (gap_frames - 1) * STEP - 0.001, 120)
	var sprite: Sprite2D = t.player.sprite
	var fx: Node2D = t.player.punch_fx
	var swoosh: Sprite2D = fx.get_node("Swoosh")
	var star: Sprite2D = fx.get_node("Star")
	var counter: Label = t.player.get_parent().get_node("CanvasLayer/ComboCounter")
	var seen := {"when": when, "animation": "", "playing": "", "fx_animation": "", "position": -1,
		"gap": INF, "sheets": [], "grids": [], "columns": [], "rows": [], "swoosh": [],
		"star_row": -1, "star_at": Vector2.INF, "entered_at": -1, "extended_at": -1, "dealt": 0, "charged": false,
		"refused": false, "counter": "", "pows": 0, "stopped": 0, "shook": false, "gold": false, "cut": cut.is_valid()}
	var on_landed := func(_target, dealt: int, charged: bool):
		seen.dealt += dealt
		seen.charged = charged
		# PunchFx and the counter heard it first: they connected as the player loaded.
		seen.star_row = star.frame_coords.y if star.visible else -1
		seen.star_at = star.global_position if star.visible else Vector2.INF
		seen.counter = counter.text
	var on_refused := func(_target): seen.refused = true
	var on_pow := func(_target): seen.pows += 1
	combo.punch_landed.connect(on_landed)
	combo.punch_refused.connect(on_refused)
	combo.charged_hit_landed.connect(on_pow)
	# A POW's shake and the gold fading off him outlast its swing into the next: only one that starts in
	# this swing is this swing's.
	var shake_before: Tween = ScreenView.shake_tween
	var glow: float = t.boss.sprite.self_modulate.r
	t.tap(KEY_Q)
	for i in 10:
		await t.physics_frame
		if t.player.state_machine.current_state == punching:
			break
	if t.player.state_machine.current_state == punching:
		seen.entered_at = Engine.get_physics_frames()
		seen.animation = punching.swing_animation
		seen.playing = String(t.player.animation_player.current_animation)
		seen.fx_animation = fx.swing_animation
		seen.position = combo.swing_position()
		# No physics step since the swing started, so the combo's clock reads what the swing read.
		seen.gap = combo.clock - punching.chain_ended_at
	var step := 0
	while t.player.state_machine.current_state == punching:
		note(seen.sheets, sprite.texture)
		note(seen.grids, Vector2i(sprite.hframes, sprite.vframes))
		note(seen.columns, sprite.frame_coords.x)
		note(seen.rows, sprite.frame_coords.y)
		if swoosh.visible:
			note(seen.swoosh, swoosh.frame_coords.x)
		if seen.extended_at < 0 and punching.extended:
			seen.extended_at = Engine.get_physics_frames()
		if Engine.time_scale < 1.0:
			seen.stopped += 1
		if ScreenView.shake_tween != shake_before:
			seen.shook = true
		var red: float = t.boss.sprite.self_modulate.r
		if red > glow + 0.01:
			seen.gold = true
		glow = red
		if step == CUT_AT and cut.is_valid():
			await cut.call()
		step += 1
		await t.physics_frame
	seen.facing = t.player.facing
	seen.after = {"texture": sprite.texture, "grid": Vector2i(sprite.hframes, sprite.vframes), "coords": sprite.frame_coords}
	combo.punch_landed.disconnect(on_landed)
	combo.punch_refused.disconnect(on_refused)
	combo.charged_hit_landed.disconnect(on_pow)
	ran.append(seen)
	return seen


# Anything of the charged punch's own show that starts on a swing: charged_hit_landed, the gold star, the
# counter's POW, a screen shake, a gold flash on him. Its longer hit-stop is compared where there is a POW
# to compare it with.
static func pow_shown(s: Dictionary) -> bool:
	return s.pows > 0 or s.star_row == 1 or s.counter.ends_with("POW!") or s.shook or s.gold


static func feel_name(v2: bool) -> String:
	return "feel_v2" if v2 else "without feel_v2"


# A point's coordinate across a punch in `facing` (PlayerScript.Facing: down and up punch along y).
static func across(facing: int, point: Vector2) -> float:
	return point.x if facing <= 1 else point.y


# Appends `value` unless it is already the last one.
static func note(list: Array, value) -> void:
	if list.is_empty() or list[-1] != value:
		list.append(value)


# A swing that ran out: hit 1 on the player's own sheet and columns, hits 2 and 3 on the combo sheet and
# their own columns, every one in the facing's row, and back on the player's own sheet after.
static func check_drawn(t, s: Dictionary, sheet: Texture2D, base: Texture2D) -> void:
	var name: String = "%s %s" % [s.when, s.animation]
	if s.animation == "punch":
		t.check(s.sheets == [base] and s.grids == [BASE_GRID] and s.columns.slice(-4) == PUNCH_COLUMNS and s.rows == [s.facing], "%s: the player's own sheet, columns %s" % [name, s.columns])
		t.check(s.after.texture == base and s.after.grid == BASE_GRID, "%s: still on it after" % name)
		return
	var first: int = Layout.FIRST_COLUMNS.get(s.animation, -1)
	var columns: Array = [first, first + 1, first + 2, first + 3]
	var grid := Vector2i(Layout.HFRAMES, Layout.VFRAMES)
	t.check(s.sheets == [sheet] and s.grids == [grid] and s.rows == [s.facing], "%s: the combo sheet, %s, in the facing's row %d" % [name, grid, s.facing])
	t.check(s.columns == columns, "%s: columns %s (%s)" % [name, columns, s.columns])
	check_after(t, s, base, name)


# The sprite on the first physics frame after a swing on the combo sheet was over.
static func check_after(t, s: Dictionary, base: Texture2D, what: String) -> void:
	var after: Dictionary = s.after
	t.check(after.texture == base and after.grid == BASE_GRID and after.coords == Vector2i(0, s.facing),
		"%s: back on the player's own sheet, %s, at column 0 of the facing's row (%s %s %s)" % [what, BASE_GRID, after.texture.resource_path.get_file(), after.grid, after.coords])


static func wear_own(t, base: Texture2D) -> void:
	var sprite: Sprite2D = t.player.sprite
	sprite.texture = base
	sprite.hframes = BASE_GRID.x
	sprite.vframes = BASE_GRID.y
	sprite.frame_coords = Vector2i(0, t.player.facing)


static func check_sprite(t, base: Texture2D, what: String) -> void:
	var sprite: Sprite2D = t.player.sprite
	var grid := Vector2i(sprite.hframes, sprite.vframes)
	t.check(sprite.texture == base and grid == BASE_GRID and sprite.frame_coords.y == t.player.facing,
		"%s: the player's own sheet, %s, in the facing's row (%s %s %s)" % [what, BASE_GRID, sprite.texture.resource_path.get_file(), grid, sprite.frame_coords])


static func log_swings(t, swings: Array) -> void:
	for s in swings:
		t.log_p("  %s: %s (playing %s, PunchFx %s), %s after the last, combo place %d, dealt %d%s%s%s, on %s %s columns %s rows %s, hitbox %s, swoosh %s, star row %d, counter '%s', stop %d%s%s; after on %s %s at %s" % [
			s.when, s.animation, s.playing, s.fx_animation, "%.3f s" % s.gap if s.gap < INF else "long", s.position,
			s.dealt, " CHARGED" if s.charged else "", " REFUSED" if s.refused else "",
			" charged_hit_landed" if s.pows > 0 else "", s.sheets.map(func(x): return x.resource_path.get_file()), s.grids,
			s.columns, s.rows, "+%d" % (s.extended_at - s.entered_at) if s.extended_at >= 0 else "not under feel_v2's contact", s.swoosh, s.star_row, s.counter, s.stopped,
			" SHAKE" if s.shook else "", " GOLD" if s.gold else "",
			s.after.texture.resource_path.get_file(), s.after.grid, s.after.coords])


# The approved sheet, read off disk: the editor imports it, and nothing here may.
static func check_real_sheet(t) -> void:
	if not FileAccess.file_exists(Layout.SHEET):
		t.check(false, "the approved sheet is in the project (%s)" % Layout.SHEET)
		return
	var art := Image.load_from_file(ProjectSettings.globalize_path(Layout.SHEET))
	var size := Vector2i(Layout.HFRAMES * CELL, Layout.VFRAMES * CELL)
	var blank := []
	for row in Layout.VFRAMES:
		for column in Layout.HFRAMES:
			if art.get_region(Rect2i(column * CELL, row * CELL, CELL, CELL)).get_used_rect().size == Vector2i.ZERO:
				blank.append(Vector2i(column, row))
	t.log_p("the sheet in the project is %s, %s" % [art.get_size(), "imported" if ResourceLoader.exists(Layout.SHEET) else "not imported yet"])
	t.check(art.get_size() == size and blank.is_empty(), "the approved sheet is %s with all %d cells drawn (blank: %s)" % [size, Layout.HFRAMES * Layout.VFRAMES, blank])


# The approved sheet as the game finds it once the editor has imported it, or else the stand-in.
static func sheet_in(t) -> Texture2D:
	if ResourceLoader.exists(Layout.SHEET):
		t.log_p("on the approved sheet, as imported")
		return load(Layout.SHEET)
	t.log_p("on an in-memory stand-in: the approved sheet isn't imported here")
	return stand_in()


# The sheet's stand-in, in memory only: hit 1's columns of player_4dir_sheet.png as both hits, at the
# contract's size, in the resource cache under the sheet's path, which is all the game finds it by.
static func stand_in() -> ImageTexture:
	var base := Image.load_from_file(ProjectSettings.globalize_path(BASE_SHEET))
	base.convert(Image.FORMAT_RGBA8)
	var sheet := Image.create_empty(Layout.HFRAMES * CELL, Layout.VFRAMES * CELL, false, Image.FORMAT_RGBA8)
	for first in Layout.FIRST_COLUMNS.values():
		sheet.blit_rect(base, Rect2i(PUNCH_COLUMNS[0] * CELL, 0, PUNCH_COLUMNS.size() * CELL, Layout.VFRAMES * CELL), Vector2i(first * CELL, 0))
	var texture := ImageTexture.create_from_image(sheet)
	texture.take_over_path(Layout.SHEET)
	return texture


# Eric's fight with him parked, down for good and never dazed, the player under his hurtbox.
static func load_down(t) -> void:
	await t.load_eric()
	t.park_eric()
	t.health_ok()
	await open_down(t)


static func open_down(t) -> void:
	t.boss.boss_health = 1000
	t.sm.downed_state_timer.start(600.0)
	t.sm.on_child_transition(t.sm.current_state, "Downed")
	await t.wait(5)
	# After Downed's Enter, which clears it: no daze, so no charged punch starts a finisher.
	t.boss.daze_used = true
	t.place_under(hurtbox(t))
	await t.wait(40)


# The count cleared and the quick gap after the last swing gone, so the next swing starts a combo and a
# chain of its own; the player unhurt and under his hurtbox again.
static func settle(t) -> void:
	var combo: Node = t.player.combo
	var punching: Node = punching_of(t)
	await t.wait_until(func(): return t.player.state_machine.current_state.name == "Idle", 240)
	combo.reset()
	await t.wait(10)
	await t.wait_until(func(): return combo.clock - punching.chain_ended_at > punching.quick_gap() + 2 * STEP, 120)
	t.clear_iframes()
	t.health_ok()
	t.place_under(hurtbox(t))
	await t.wait(8)


static func hurtbox(t) -> Area2D:
	return t.boss.get_node("Hurtbox")


static func punching_of(t) -> Node:
	return t.player.get_node("StateMachine/Punching")
