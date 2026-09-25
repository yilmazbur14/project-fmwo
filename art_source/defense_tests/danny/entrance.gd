extends RefCounted

# danny_entrance (coder A): Danny's walk-in, his lines and the FireRed evolve, and the hold that skips any of
# it (DannyBossIntro). Real time (--max-fps 60): the hold is 0.4 real seconds, and the VS card's grace and the
# pause screen's are real seconds too.
#   watched  the ring open and his bar down, the player held; the player walks onto their mark, then tiny Danny
#            ambles down through the top gate onto his and stops with both feet down; the gates slam, then
#            his bar and his first line. His lines squash him while they type, the player's don't. The
#            evolve's beats land on art_source/danny_sumo/transform.py's timings, with the dim under him, his
#            flat white, the burst behind him growing to full, and the white-out; his theme starts on the
#            landing and not before, and at the card's flash the ring is set the plan's way.
#   held     a hold mid-walk, mid-line and mid-flash each lands on that same card-flash state, and never opens
#            the pause screen.
#   paused   a tapped Escape pauses the walk-in dead, and the resume carries it on.
#   retry    no walk-in, tiny Danny already at HOME; the lines and the evolve play again, and a hold in the
#            replayed flash still lands on the snapshot.

const BODY := "Arena/DannyBossScene/DannyBossCharacterBody"
const VS_CARD_LAYOUT := "res://Scripts/VsCardArtLayout.gd"
const SCREEN_VIEW := "res://Scripts/ScreenView.gd"
# The evolve's beats (DannyBossIntro, from transform.py): drain to flash, the flash, the white-out, from its
# start to the landing, and the whole of it.
const DRAIN_TO_FLASH := 0.33
const FLASH_TIME := 1.985
const WHITE_OUT := 0.12
const START_TO_LAND := 4.745
const EVOLVE_TIME := 6.005
# Two frames either way: the beats wait on tweens, which step on idle frames, and this reads them on physics
# frames.
const SLACK := 2.0 / 60.0


static func run(t) -> void:
	t.log_p("-- watched: the walk-in")
	await enter(t)
	var intro: Node = t.entrance_state()
	t.check(intro != null and intro == t.sm.states["Intro"], "his fight opens on DannyBossIntro")
	t.check(await t.wait_until(func(): return intro.entered, 60), "which starts itself")
	var gates: Node = t.current_scene.get_node("Arena/Gates")
	var boss: Node = t.boss
	var player: Node = t.player
	t.check(gates.is_open() and not boss.hud_layer.visible, "the ring is open and his bar is down")
	t.check(player.is_talking and not player.state_machine.is_processing(), "the player is held, their own state machine stopped")
	t.check(boss.global_position.y < 0.0 and boss.current_anim == &"walk_small" and player.global_position.y > intro.player_home.y + 100.0,
		"tiny Danny starts above the ring on his walk, the player below it")
	t.check(await t.wait_until(func(): return player.global_position.is_equal_approx(intro.player_home), 300), "the player walks up onto their mark")
	t.check(await t.wait_until(func(): return boss.global_position.is_equal_approx(intro.home) and boss.current_anim == &"walk_hold", 400),
		"he ambles down onto his and stops with both feet down")
	t.check(boss.sprite.texture.resource_path.ends_with("danny_walk.png") and boss.sprite.offset == Vector2(0, -32), "the small form, on its own feet")
	t.check(await t.wait_until(func(): return not gates.is_open(), 120), "the gates slam behind him")
	t.check(await t.wait_until(func(): return boss.hud_layer.visible, 120), "then his bar comes up")
	t.check(await t.wait_until(func(): return t.live_balloon() != null, 120), "and his first line")
	t.check(t.sm.post_dialogue_pre_fight_timer.is_stopped() and boss.music_starts == 0, "the fight and his theme are still waiting")

	t.log_p("-- his lines and the evolve")
	var card: Node = t.vs_card()
	var squash := {"danny": false, "other": false}
	var marks := {}
	var fx := {"dim_z": -1, "hud_hidden": false, "white": false, "sprite_z": 0, "burst_max": 0.0, "music_at_drain": -1}
	for i in 3600:
		if card.is_playing():
			break
		var balloon: Node = t.live_balloon()
		if balloon != null and balloon.dialogue_line != null and balloon.dialogue_label.is_typing and not intro.beat_running:
			var squashing: bool = boss.animation_player.current_animation == "talk"
			if balloon.dialogue_line.character == "Danny":
				squash.danny = squash.danny or squashing
			else:
				squash.other = squash.other or squashing
		var now: float = boss.fight_clock
		if is_instance_valid(intro.dim):
			if not marks.has("drain"):
				marks.drain = now
				fx.dim_z = intro.dim.z_index
				fx.hud_hidden = not boss.hud_layer.visible
				fx.music_at_drain = boss.music_starts
			if intro.dim.color == Color.WHITE and not marks.has("white"):
				marks.white = now
		if is_instance_valid(intro.burst):
			if not marks.has("flash"):
				marks.flash = now
			fx.burst_max = maxf(fx.burst_max, intro.burst.color.a)
		if boss.sprite.material != null:
			fx.white = true
			fx.sprite_z = maxi(fx.sprite_z, boss.sprite.z_index)
		if boss.current_anim == &"evolve_land" and not marks.has("land"):
			marks.land = now
		if boss.music_starts > 0 and not marks.has("music"):
			marks.music = now
		if i % 8 == 0 and not intro.beat_running:
			t.tap(KEY_ENTER)
		await t.physics_frame
	t.log_p("marks %s, beats %s, fx %s" % [marks, intro.beat_times, fx])
	t.check(squash.danny and not squash.other, "his lines squash him while they type, the player's don't")
	t.check(marks.has("drain") and marks.has("flash") and absf(marks.flash - marks.drain - DRAIN_TO_FLASH) <= SLACK,
		"the drain: three steps of 0.11 s (%.3f)" % [marks.get("flash", 0.0) - marks.get("drain", 0.0)])
	t.check(marks.has("white") and absf(marks.white - marks.flash - FLASH_TIME) <= SLACK,
		"the flash: fourteen holds, 1.985 s (%.3f)" % [marks.get("white", 0.0) - marks.get("flash", 0.0)])
	t.check(marks.has("land") and absf(marks.land - marks.white - WHITE_OUT) <= SLACK,
		"the white-out: 0.12 s (%.3f)" % [marks.get("land", 0.0) - marks.get("white", 0.0)])
	var beats: Dictionary = intro.beat_times
	t.check(absf(beats.get(&"land", -1.0) - START_TO_LAND) <= SLACK and absf(beats.get(&"evolve", -1.0) - EVOLVE_TIME) <= SLACK,
		"the landing 4.745 s in and the whole evolve 6.005 s (%.3f, %.3f)" % [beats.get(&"land", -1.0), beats.get(&"evolve", -1.0)])
	t.check(fx.dim_z == 20 and fx.hud_hidden and fx.white and fx.sprite_z == 30 and is_equal_approx(fx.burst_max, 1.0),
		"the dim at z 20 with his bar gone, him flat white at z 30 over it, the burst up to full")
	t.check(fx.music_at_drain == 0 and marks.has("music") and absf(marks.music - marks.land) <= SLACK and boss.music_starts == 1,
		"his theme starts on the landing and not before, once")
	t.check(await card_flash(t), "the lines hand over to the card")
	var watched := snapshot(t)
	t.log_p("watched, at the card's flash: %s" % [watched])
	t.check(watched.danny == t.sm.HOME and watched.anim == &"idle" and watched.sheet == "danny_sumo_idle.png" and not watched.flip
		and watched.modulate == Color.WHITE and watched.scale == Vector2(3, 3) and not watched.white and watched.z == 0
		and watched.lift == 0.0 and not watched.hurtbox and watched.hud and not watched.gates_open and watched.talking
		and watched.player_sm and watched.music and watched.music_starts == 1 and watched.hazards == 0 and not watched.balloon
		and watched.intro_fx == 0 and watched.evolved and watched.seen and watched.zoom == 1.0 and watched.time_scale == 1.0
		and not watched.crowd_cheering, "and the ring is set the way the plan says")
	card.skip()
	await t.wait_until(func(): return not card.is_playing(), 60)
	card.grace_until_msec = 0
	t.check(await t.wait_until(func(): return t.sm.current_state != intro, 180), "and the fight starts behind it")

	for where in ["walk", "line", "flash"]:
		t.log_p("-- held at mid-%s" % where)
		await enter(t)
		intro = t.entrance_state()
		boss = t.boss
		await t.wait_until(func(): return intro.entered, 60)
		var lines := 0
		var last_line = null
		for i in 3600:
			if where == "walk" and intro.home.y - boss.global_position.y > 200.0 and boss.global_position.y > -60.0:
				break
			var balloon: Node = t.live_balloon()
			if balloon != null and balloon.dialogue_line != null and balloon.dialogue_line != last_line:
				last_line = balloon.dialogue_line
				lines += 1
				if where == "line" and lines == 3:
					await t.wait(10)
					break
			if where == "flash" and is_instance_valid(intro.burst):
				await t.wait(20)
				break
			if where != "walk" and i % 8 == 0 and not intro.beat_running:
				t.tap(KEY_ENTER)
			await t.physics_frame
		t.log_p("holding Escape: anim %s, lines %d, music_starts %d" % [boss.current_anim, lines, boss.music_starts])
		t.press(KEY_ESCAPE)
		var reached: bool = await card_flash(t, 120)
		var skipped := snapshot(t)
		t.release(KEY_ESCAPE)
		await t.wait(4)
		var diffs := diff(skipped, watched)
		t.check(reached and diffs.is_empty(), "mid-%s: the card's flash, with the ring exactly as a watched entrance leaves it %s" % [where, diffs])
		t.check(not t.pause_menu().is_open() and not t.paused, "mid-%s: and the pause screen never opened" % where)

	t.log_p("-- a tapped Escape pauses it")
	await enter(t)
	intro = t.entrance_state()
	await t.wait_until(func(): return intro.entered, 60)
	await t.wait(30)
	var pause: Node = t.pause_menu()
	await t.tap_pause()
	t.check(pause.is_open() and t.paused, "a tap opened the pause screen rather than skipping")
	var held_at: Vector2 = t.player.global_position
	await t.wait(40)
	t.check(t.player.global_position.is_equal_approx(held_at), "and the walk-in stopped dead with the fight")
	await t.tap_pause()
	await t.wait(20)
	t.check(not t.paused and not t.player.global_position.is_equal_approx(held_at), "the resume carries it on")
	# Skipped to its end, which is what marks it seen for the run.
	t.press(KEY_ESCAPE)
	await card_flash(t, 120)
	t.release(KEY_ESCAPE)
	card = t.vs_card()
	card.skip()
	await t.wait_until(func(): return not card.is_playing(), 60)
	card.grace_until_msec = 0

	t.log_p("-- the retry: no walk-in, the lines and the evolve again, and a hold still skips them")
	await enter(t, false)
	intro = t.entrance_state()
	boss = t.boss
	gates = t.current_scene.get_node("Arena/Gates")
	card = t.vs_card()
	t.check(intro.finished and not gates.is_open() and boss.current_anim == &"walk_hold" and boss.global_position == intro.home,
		"the entrance is over on arrival: tiny Danny at HOME, the ring never opened")
	t.check(await t.wait_until(func(): return t.live_balloon() != null, 120), "his lines start straight away")
	for i in 3600:
		if card.is_playing():
			break
		if i % 8 == 0 and not intro.beat_running:
			t.tap(KEY_ENTER)
		await t.physics_frame
	t.check(intro.beat_times.has(&"evolve") and boss.music_starts == 1, "the evolve played again, his theme started once (%s)" % [intro.beat_times.keys()])
	card.skip()
	await t.wait_until(func(): return not card.is_playing(), 60)
	card.grace_until_msec = 0
	await enter(t, false)
	intro = t.entrance_state()
	for i in 3600:
		if is_instance_valid(intro.burst):
			await t.wait(12)
			break
		if i % 8 == 0 and not intro.beat_running:
			t.tap(KEY_ENTER)
		await t.physics_frame
	t.log_p("holding Escape in the replayed flash")
	t.press(KEY_ESCAPE)
	var reached_again: bool = await card_flash(t, 120)
	var again := snapshot(t)
	t.release(KEY_ESCAPE)
	var retry_diffs := diff(again, watched)
	t.check(reached_again and retry_diffs.is_empty(), "the hold lands on the same card-flash state %s" % [retry_diffs])


# His fight, fresh (a new run, so his walk-in plays) or as a retry in the same run.
static func enter(t, fresh := true) -> void:
	var scene: String = t.SCENES["danny"]
	if fresh:
		await t.enter_fight(scene, true)
	else:
		t.change_scene_to_file(scene)
		while t.current_scene == null or t.current_scene.scene_file_path != scene:
			await t.process_frame
		await t.wait(6)
		t.player = t.current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
		t.defense = t.player.get_node("Defense")
	t.boss = t.current_scene.get_node(BODY)
	t.sm = t.boss.state_machine


static func card_flash(t, max_frames := 900) -> bool:
	var card: Node = t.vs_card()
	var card_art: GDScript = load(VS_CARD_LAYOUT)
	return await t.wait_until(func(): return card.is_playing() and card.clock >= card_art.HOLD_END, max_frames)


# What he and the ring look like at the VS card's flash: everything a watched entrance and a held one must agree
# on. Floats are rounded, as matt_snapshot's are.
static func snapshot(t) -> Dictionary:
	var boss: Node = t.boss
	var player: Node = t.player
	var gates: Node = t.current_scene.get_node("Arena/Gates")
	var screen: GDScript = load(SCREEN_VIEW)
	var crowd: Node = t.get_first_node_in_group("arena_crowd")
	var intro: Node = t.sm.states["Intro"]
	return {
		"danny": boss.global_position, "anim": boss.current_anim, "sheet": boss.sprite.texture.resource_path.get_file(),
		"flip": boss.sprite.flip_h, "modulate": boss.sprite.modulate, "scale": boss.sprite.scale,
		"white": boss.sprite.material != null, "z": boss.sprite.z_index, "lift": boss.lift_px,
		"rotation": snappedf(boss.sprite.rotation, 0.0001), "offset": boss.sprite.offset,
		"hurtbox": boss.hurtbox.monitoring, "hud": boss.hud_layer.visible, "hud_alpha": snappedf(boss.health_bar.modulate.a, 0.0001),
		"gates_open": gates.is_open(), "player": player.global_position, "talking": player.is_talking,
		"player_sm": player.state_machine.is_processing(), "face_point": player.facing_point,
		"zoom": snappedf(screen.zoom, 0.0001), "shake": screen.shake_offset, "time_scale": snappedf(Engine.time_scale, 0.0001),
		"crowd_cheering": crowd != null and crowd._cheer_time_left > 0.0, "music": boss.music_player.playing,
		"music_starts": boss.music_starts, "hazards": t.get_nodes_in_group(t.sm.HAZARD_GROUP).size(),
		"balloon": t.live_balloon() != null, "intro_fx": intro.intro_fx.size(), "evolved": intro.evolved,
		"seen": t.root.get_node("GameProgress").entrances_seen.has(boss.FIGHT_SCENE),
	}


static func diff(got: Dictionary, want: Dictionary) -> Array:
	var diffs := []
	for k in want:
		if got[k] != want[k]:
			diffs.append("%s %s (watched %s)" % [k, got[k], want[k]])
	return diffs
