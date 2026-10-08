extends RefCounted

# crowd_murmur: the arena crowd's murmur (ArenaMurmur; the 2026-10-07 playtest: every walk-in and pre-fight line played in
# silence). Levels are read as heard: a loop's volume_db over its measured RMS (ArenaMurmur.MURMUR_RMS, CHEERING_RMS).
# A fade is given its time and SLACK_FRAMES more. tier=
#   start   Burak's, Eric's, Josh's, Matt's and Jordan's fights opened as the ladder opens them, entrance and all: one
#           murmur in the arena, playing a frame after the fight comes up, at UNDER_LINES once FADE_IN is over with the
#           fight's music not yet playing; both loops on the Master bus (the volume slider's) and looping.
#   duck    Eric's fight, his entrance watched and his line read: at UNDER_LINES until his theme starts on the sword
#           pull, then at UNDER_MUSIC within DUCK and still playing.
#   cheer   Eric's quiet fight (load_eric), his theme on: one call_group cheer brings the cheering loop up to CHEER_OVER
#           over the bed within CHEER_IN, one loop and not one a crowd, and it is gone CHEER_OUT after the cheer's
#           seconds; a hush cuts a long one short, gone within CHEER_OUT. Then his theme stopped by hand with the fight
#           still on: the murmur back at UNDER_LINES within RISE.
#   end     Eric beaten (his health to 0, the real KO): the murmur and the cheering gone within FADE_OUT, and never back
#           for 3 s of his outro. Lost (the player at 0): the same, with his theme playing on.
#   silent  not a frame of either loop: Jordan's FINALE row (GameProgress.start_at_finale) from his KO through his
#           walk-out, his room, the Puppet Master's void (the arena's crowd hidden) and the champion ending (its arena,
#           its own crowd).
#   normal  all of them in turn.

const Murmur := preload("res://Scripts/ArenaMurmur.gd")
const TIERS := ["start", "duck", "cheer", "end", "silent"]
const START_FIGHTS := ["burak", "eric", "josh", "matt", "jordan"]
const ERIC_BODY := "Arena/EricBossScene/CharacterBody2D"
const JORDAN_BODY := "Arena/JordanScene/JordanCharacterBody"
const KAIJU := "res://Scenes/Bosses/JordanBossFightScene.tscn"
const ROOM := "res://Scenes/Core/JordanFinaleScene.tscn"
const GOD := "res://Scenes/Bosses/JordanGodFightScene.tscn"
const ENDING := "res://Scenes/Core/ChampionEndingScene.tscn"
const FPS := 60
const SLACK_FRAMES := 2
# How near a level as heard must be to the one it is heading for, in dB.
const NEAR := 0.05
# The walk-out watched this long after WalkOut is entered, and each scene of the silent tier this long.
const WALK_OUT_FRAMES := 60 * 6
const WATCH_FRAMES := 60 * 3


static func run(t) -> void:
	var tiers: Array = TIERS if t.tier == "normal" else [t.tier]
	for tier in tiers:
		t.log_p("-- crowd_murmur %s" % tier)
		match tier:
			"start": await tier_start(t)
			"duck": await tier_duck(t)
			"cheer": await tier_cheer(t)
			"end": await tier_end(t)
			"silent": await tier_silent(t)
			_: t.check(false, "unknown tier %s" % tier)


static func voices(t) -> Array:
	if t.current_scene == null:
		return []
	return t.current_scene.find_children("Murmur", "", true, false).filter(func(node: Node) -> bool:
		return node.get_script() == Murmur)


static func heard(player: AudioStreamPlayer, rms: float) -> float:
	return player.volume_db + rms if player.playing else Murmur.SILENT


static func murmur_db(voice: Node) -> float:
	return heard(voice.murmur, Murmur.MURMUR_RMS)


static func cheering_db(voice: Node) -> float:
	return heard(voice.cheering, Murmur.CHEERING_RMS)


static func loops_playing(t) -> int:
	var playing := 0
	for voice in voices(t):
		playing += int(voice.murmur.playing) + int(voice.cheering.playing)
	return playing


static func within(seconds: float) -> int:
	return int(ceilf(seconds * FPS)) + SLACK_FRAMES


# Out of the scene that is up, so the next open of the same fight waits for a fresh one: open_scene takes a scene with
# the path it is after as arrived. A decided fight's outro goes too, before a load's dialogue_ended reads it on to the
# Victory screen.
static func leave(t) -> void:
	var outro: Node = t.root.get_node_or_null(^"FightOutro")
	if outro != null:
		outro.free()
	var empty := Node.new()
	t.change_scene_to_node(empty)
	await t.wait_until(func() -> bool: return t.current_scene == empty, 60)


# Frames until `cond` holds, or -1 if it doesn't inside `max_frames`.
static func frames_until(t, cond: Callable, max_frames: int) -> int:
	for i in max_frames + 1:
		if cond.call():
			return i
		await t.physics_frame
	return -1


#START

static func tier_start(t) -> void:
	for key in START_FIGHTS:
		await t.open_scene(t.SCENES[key])
		var found := voices(t)
		t.check(found.size() == 1, "%s: one murmur in the arena, not one a crowd (%d)" % [key, found.size()])
		if found.size() != 1:
			continue
		var voice: Node = found[0]
		await t.wait(1)
		var first: bool = voice.murmur.playing
		await t.wait(within(Murmur.FADE_IN))
		var music: AudioStreamPlayer = t.get_first_node_in_group("fight_boss").music_player
		var level := murmur_db(voice)
		t.log_p("%s: playing a frame in %s, %.2f dBFS as heard at %.2f s, his theme %s" % [key, first, level,
			Murmur.FADE_IN, "playing" if music.playing else "not yet"])
		t.check(first, "%s: the murmur is playing a frame after the fight comes up" % key)
		t.check(not music.playing and absf(level - Murmur.UNDER_LINES) < NEAR,
			"%s: under the walk-in at UNDER_LINES, %.1f dBFS, before the music" % [key, Murmur.UNDER_LINES])
		t.check(voice.murmur.bus == &"Master" and voice.cheering.bus == &"Master", "%s: both loops on the Master bus" % key)
		t.check(voice.murmur.stream.loop_mode == AudioStreamWAV.LOOP_FORWARD
			and voice.cheering.stream.loop_mode == AudioStreamWAV.LOOP_FORWARD, "%s: both loops loop" % key)


#DUCK

static func tier_duck(t) -> void:
	await leave(t)
	await t.open_scene(t.SCENES["eric"])
	var voice: Node = voices(t)[0]
	var music: AudioStreamPlayer = t.current_scene.get_node(ERIC_BODY).music_player
	# Frame by frame: the murmur's level until his theme starts, the frame it starts and the frame it is ducked.
	var seen := {"before": Murmur.SILENT, "started": -1, "ducked": -1, "frame": 0}
	var watch := func() -> void:
		seen.frame += 1
		if not music.playing:
			seen.before = murmur_db(voice)
			return
		if seen.started < 0:
			seen.started = seen.frame
		if seen.ducked < 0 and absf(murmur_db(voice) - Murmur.UNDER_MUSIC) < NEAR and voice.murmur.playing:
			seen.ducked = seen.frame
	t.process_frame.connect(watch)
	# His theme starts on the sword pull, which his first line calls: the lines are read as a player reads them.
	for i in 60 * 60:
		if music.playing:
			break
		if t.live_balloon() != null:
			await t.read_line()
		else:
			await t.wait(1)
	await t.wait(within(Murmur.DUCK))
	t.process_frame.disconnect(watch)
	t.log_p("his theme started on frame %d, the murmur at %.2f dBFS just before, ducked %d frames later" % [seen.started,
		seen.before, seen.ducked - seen.started])
	t.check(seen.started > within(Murmur.FADE_IN) and absf(seen.before - Murmur.UNDER_LINES) < NEAR,
		"under his walk-in and his line the murmur is at UNDER_LINES until his theme starts")
	t.check(seen.ducked >= 0 and seen.ducked - seen.started <= within(Murmur.DUCK),
		"ducked to UNDER_MUSIC, %.1f dBFS, within DUCK of his theme starting, still playing" % Murmur.UNDER_MUSIC)


#CHEER

static func tier_cheer(t) -> void:
	await leave(t)
	await t.load_eric()
	var voice: Node = voices(t)[0]
	await t.wait(within(Murmur.FADE_IN + Murmur.DUCK + Murmur.CHEER_OUT))
	var bed := murmur_db(voice)
	t.log_p("the bed with his theme %s: %.2f dBFS" % ["on" if t.boss.music_player.playing else "OFF", bed])
	t.check(t.boss.music_player.playing and absf(bed - Murmur.UNDER_MUSIC) < NEAR and not voice.cheering.playing,
		"his quiet fight: the murmur at UNDER_MUSIC under his theme, no cheering")
	t.call_group("arena_crowd", "cheer", 2.0)
	var lift := bed + Murmur.CHEER_OVER
	var up := await frames_until(t, func() -> bool: return absf(cheering_db(voice) - lift) < NEAR, within(Murmur.CHEER_IN))
	var cheering_players := 0
	for player in t.current_scene.find_children("*", "AudioStreamPlayer", true, false):
		if player.playing and player.stream != null and player.stream.resource_path == Murmur.CHEERING:
			cheering_players += 1
	t.log_p("a 2 s cheer: the cheering loop at %.2f dBFS in %d frames, %d playing" % [cheering_db(voice), up, cheering_players])
	t.check(up >= 0, "a cheer brings the cheering loop up to CHEER_OVER over the bed within CHEER_IN")
	t.check(cheering_players == 1, "one cheering loop for the two crowds")
	var gone := await frames_until(t, func() -> bool: return not voice.cheering.playing, within(2.0 + Murmur.CHEER_OUT))
	t.log_p("gone %d frames after it came up" % (up + gone))
	t.check(gone >= 0 and up + gone >= int((2.0 + Murmur.CHEER_OUT) * FPS) - SLACK_FRAMES,
		"and gone CHEER_OUT after the cheer's 2 s")
	t.check(absf(murmur_db(voice) - bed) < NEAR, "the murmur under it untouched")
	t.call_group("arena_crowd", "cheer", 5.0)
	await t.wait(within(Murmur.CHEER_IN))
	t.call_group("arena_crowd", "hush")
	var hushed := await frames_until(t, func() -> bool: return not voice.cheering.playing, within(Murmur.CHEER_OUT))
	t.log_p("a 5 s cheer hushed: gone in %d frames" % hushed)
	t.check(hushed >= 0, "a hush cuts a 5 s cheer short: gone within CHEER_OUT")
	# Here rather than in duck: his entrance starts his theme again as it finishes, and this fight's is long finished.
	t.boss.music_player.stop()
	var rose := await frames_until(t, func() -> bool: return absf(murmur_db(voice) - Murmur.UNDER_LINES) < NEAR,
		within(Murmur.RISE))
	t.log_p("his theme stopped: back to %.2f dBFS in %d frames" % [murmur_db(voice), rose])
	t.check(rose >= 0, "with his theme stopped and the fight still on, back at UNDER_LINES within RISE")


#END

static func tier_end(t) -> void:
	for won in [true, false]:
		var label := "won" if won else "lost"
		await leave(t)
		await t.load_eric()
		var voice: Node = voices(t)[0]
		await t.wait(within(Murmur.FADE_IN + Murmur.DUCK))
		var was := murmur_db(voice)
		if won:
			t.boss.boss_health = 0
		else:
			t.player.playerHealth = 0
		var decided: bool = await t.wait_until(func() -> bool: return t.root.has_node(^"FightOutro"), 10)
		var gone := await frames_until(t, func() -> bool: return loops_playing(t) == 0, within(Murmur.FADE_OUT))
		var back := 0
		for i in WATCH_FRAMES:
			back += loops_playing(t)
			await t.physics_frame
		var music: bool = t.boss.music_player.playing
		t.log_p("%s: from %.2f dBFS, the fight decided %s, gone in %d frames, %d frames back after; his theme %s" % [label,
			was, decided, gone, back, "playing" if music else "stopped"])
		t.check(decided and gone >= 0, "%s: the murmur and the cheering gone within FADE_OUT of the fight ending" % label)
		t.check(back == 0, "%s: and never back through 3 s of his outro" % label)
		if not won:
			t.check(music, "lost: his theme playing on, so it is the fight's end that takes the murmur")


#SILENT

static func tier_silent(t) -> void:
	await leave(t)
	var progress: Node = t.root.get_node("GameProgress")
	progress.reset_progress()
	progress.start_at_finale = true
	var heard_frames := [0]
	var count := func() -> void:
		heard_frames[0] += loops_playing(t)
	t.process_frame.connect(count)
	await t.open_scene(KAIJU)
	var walk_out: Node = t.current_scene.get_node(JORDAN_BODY).state_machine.states["WalkOut"]
	var entered: bool = await t.wait_until(func() -> bool: return walk_out.entered, 300)
	await t.wait(WALK_OUT_FRAMES)
	t.log_p("FINALE row: WalkOut entered %s, %d frames of a loop playing" % [entered, heard_frames[0]])
	t.check(entered and heard_frames[0] == 0, "Jordan's walk-out, from his KO: not a frame of the murmur")
	progress.start_at_finale = false
	for path in [ROOM, GOD, ENDING]:
		heard_frames[0] = 0
		await t.open_scene(path)
		await t.wait(WATCH_FRAMES)
		var found := voices(t)
		var shown := found.any(func(voice: Node) -> bool: return voice.get_parent().is_visible_in_tree())
		t.log_p("%s: %d murmur nodes (crowd %s), %d frames of a loop playing" % [path.get_file(), found.size(),
			"on screen" if shown else "hidden or none", heard_frames[0]])
		t.check(heard_frames[0] == 0, "%s: not a frame of the murmur" % path.get_file())
	t.process_frame.disconnect(count)
	progress.reset_progress()
