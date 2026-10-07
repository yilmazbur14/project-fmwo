extends RefCounted

# champion_ending: the champion ending after god-Jordan (ChampionEndingScript, ChampionEndingLayout), the trophy lift on
# the song's drop, the announcer whose line the crowd swallows, the credits and the menu. --max-fps 60 and real time:
# the ending runs on the song's own clock. Each tier logs which clock it ran on - the user's track is local only, so a
# fresh clone runs on the fallback's scene clock. A frame either side is SLACK. tier=
#   sync      from five start spots (entry_override) and again with DROP_TIME at the 7.78 slam: the lift's DROP frame
#             first shows within a frame of DROP_TIME and the grab on the grip cue's frame within a frame of its time;
#             the walker exactly on LIFT_MARK from the arrival on; the walk's pace inside its limits
#   line      the announcer: `???`, the parsed text the verbatim line, no portrait, his voice; typed out before NAME_AT;
#             accept, punch and an ESC tap while it types and once it has typed change nothing; the balloon closes at
#             NAME_AT + NAME_HOLD within a frame, and it is the only line ever shown
#   watched   the whole run: every cue in order within a frame of its time; the black reached within a frame of
#             FADE_AT + FADE_TIME; the song still rising on the same stream into the credits; every role Burak Yilmaz,
#             the Universal Collapse line with the user's track (none without it), THANK YOU last; then the menu, with
#             the view level, time_scale 1, no balloon, no FightOutro, nothing of the ending on the root and no bare frame
#   held      ESC held through the walk, the gather and the line each lands on the credits within SKIP_FADE and a
#             frame, the balloon gone, the view level and the song playing on; an ESC held as it loads does nothing until
#             it is let go; and a hold in the credits lands on the menu
#   switch    god-Jordan beaten (boss_health 1 and take_uppercut(null), the final beam off): with the switch on, one
#             FightOutro and the ending, the view level and the base view the arena's on its first frame; off, the card
#             and then the menu
#   fallback  MUSIC_LOCAL pointed at a missing file: the fallback playing, the cues on the scene clock within a frame,
#             and no Universal Collapse in the credits
#   menu      the boss select's ENDING row, enabled, opens the ending with the run's progress reset
#   art       the approved art on (every USE_FINAL_*): the crowd sheets swapped for the roar sheets; the waiting cup's
#             loop until the arrival, then the lift sheet on the song's frame every frame, frame 0 on the arrival and
#             frame 6 on the drop within a frame, the walker and the waiting cup hidden; the lift flash and the sweep
#             from the drop, the burst's 28 grid frames once in order from it, the rain a beat after; the crowd roaring;
#             the still behind THANK YOU
#   stand_in  the art off: the stand-in cup where the art's is on every frame, over the player on the stand and under
#             them overhead; the stand-in flash and shower on the drop
#   normal    all of them in turn; only watched sits through the whole roll.

const ENDING := "res://Scenes/Core/ChampionEndingScene.tscn"
const CARD := "res://Scenes/Core/ToBeContinuedScene.tscn"
const MENU := "res://Scenes/Core/MainMenuScene.tscn"
const GOD_SCENE := "res://Scenes/Bosses/JordanGodFightScene.tscn"
const Layout := preload("res://Scripts/ChampionEndingLayout.gd")
const GodLayout := preload("res://Scripts/JordanGodLayout.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const DialogueVoices := preload("res://Scripts/DialogueVoices.gd")
const Finale := preload("res://art_source/defense_tests/jordan/finale.gd")
const God := preload("res://art_source/defense_tests/jordan/god.gd")
const TIERS := ["sync", "line", "watched", "held", "switch", "fallback", "menu", "art", "stand_in"]
const SLACK := 1.0 / 60.0 + 0.002
const LINE := "And announcing your new discord champion of this server...."
const ENTRIES: Array[Vector2] = [Vector2(960, -30), Vector2(700, -30), Vector2(1300, -30), Vector2(960, 300),
	Vector2(300, 200)]
const ESCAPE_HOLD := 40
const AUTOLOADS := [&"DialogueManager", &"GameProgress", &"InputSettings"]
const MISSING_TRACK := "res://Assets/Audio/SFX/local/no_such_champion_track.mp3"


static func run(t) -> void:
	var tiers: Array = TIERS if t.tier == "normal" else [t.tier]
	var saved := _settings()
	for tier in tiers:
		t.log_p("-- champion_ending %s" % tier)
		match tier:
			"sync":
				await tier_sync(t)
			"line":
				await tier_line(t)
			"watched":
				await tier_watched(t)
			"held":
				await tier_held(t)
			"switch":
				await tier_switch(t)
			"fallback":
				await tier_fallback(t)
			"menu":
				await tier_menu(t)
			"art":
				await tier_art(t)
			"stand_in":
				await tier_stand_in(t)
			_:
				t.check(false, "champion_ending has no tier %s" % tier)
		_restore(saved)
		t.release(KEY_ESCAPE)


#GETTING THERE

static func _settings() -> Dictionary:
	return {"drop": Layout.DROP_TIME, "entry": Layout.entry_override, "music": Layout.MUSIC_LOCAL,
		"on": Layout.USE_CHAMPION_ENDING, "champion": Layout.USE_FINAL_CHAMPION, "fx": Layout.USE_FINAL_FX,
		"roar": Layout.USE_FINAL_CROWD_ROAR, "credits": Layout.USE_FINAL_CREDITS_ART, "burst": Layout.USE_FINAL_BURST,
		"combos": GodLayout.COMBOS.duplicate(), "beam": GodLayout.USE_FINAL_BEAM}


static func _restore(saved: Dictionary) -> void:
	Layout.DROP_TIME = saved.drop
	Layout.entry_override = saved.entry
	Layout.MUSIC_LOCAL = saved.music
	Layout.USE_CHAMPION_ENDING = saved.on
	Layout.USE_FINAL_CHAMPION = saved.champion
	Layout.USE_FINAL_FX = saved.fx
	Layout.USE_FINAL_CROWD_ROAR = saved.roar
	Layout.USE_FINAL_CREDITS_ART = saved.credits
	Layout.USE_FINAL_BURST = saved.burst
	GodLayout.COMBOS = saved.combos
	GodLayout.USE_FINAL_BEAM = saved.beam


static func _art(on: bool) -> void:
	Layout.USE_FINAL_CHAMPION = on
	Layout.USE_FINAL_FX = on
	Layout.USE_FINAL_CROWD_ROAR = on
	Layout.USE_FINAL_CREDITS_ART = on
	Layout.USE_FINAL_BURST = on


# A fresh ending, the run's progress reset. Not open_scene(): an ending already up has the same path, and would pass for
# the new one until the change lands.
static func open_ending(t) -> Node:
	t.root.get_node("GameProgress").reset_progress()
	var old_id: int = t.current_scene.get_instance_id() if t.current_scene != null else 0
	t.change_scene_to_file(ENDING)
	var arrived := func() -> bool:
		return t.current_scene != null and t.current_scene.get_instance_id() != old_id 			and t.current_scene.scene_file_path == ENDING
	var opened: bool = await until(t, arrived, 600)
	t.check(opened, "the ending opens")
	var scene: Node = t.current_scene
	t.log_p("on %s (%s)" % ["the song's clock: the user's track" if scene.own_track else "the scene clock: the fallback",
		scene.music.stream.resource_path])
	return scene


static func scene_is(t, path: String) -> bool:
	return t.current_scene != null and t.current_scene.scene_file_path == path


# Idle frames, the ending's own: its clock and its cues step on them.
static func until(t, done: Callable, frames := 60 * 30) -> bool:
	for i in frames:
		if done.call():
			return true
		await t.process_frame
	return done.call()


static func until_song(t, scene: Node, at: float) -> bool:
	return await until(t, func(): return not is_instance_valid(scene) or scene.music_time() >= at, int((at + 5.0) * 60))


static func hold_escape(t) -> void:
	t.press(KEY_ESCAPE)
	for i in ESCAPE_HOLD:
		await t.process_frame
	t.release(KEY_ESCAPE)


static func near(value: float, want: float) -> bool:
	return absf(value - want) <= SLACK


#SYNC

static func tier_sync(t) -> void:
	for drop in [Layout.DROP_TIME, Layout.GRIP_TIME]:
		Layout.DROP_TIME = drop
		for entry in ENTRIES:
			Layout.entry_override = entry
			var scene: Node = await open_ending(t)
			var seen := {"off_mark": 0, "grab_on_cue": false, "grab_seen": false, "first_walk": Vector2.INF}
			var watch := func():
				if not is_instance_valid(scene) or scene.credits != null:
					return
				if scene.cues.has(&"arrive") and scene.walker.global_position != Layout.LIFT_MARK:
					seen.off_mark += 1
				if scene.lift_frame == &"grab" and not seen.grab_seen:
					seen.grab_seen = true
					seen.grab_on_cue = scene.cues.has(&"grip")
				if scene.walker.visible and seen.first_walk == Vector2.INF:
					seen.first_walk = scene.walker.global_position
			t.process_frame.connect(watch)
			await until(t, func(): return scene.drop_shown_at >= 0.0, 60 * 15)
			await t.wait(5)
			t.process_frame.disconnect(watch)
			var grip: float = scene.cues.get(&"grip", -1.0)
			var distance := entry.distance_to(Layout.LIFT_MARK)
			t.log_p("drop %.2f from %s: the drop frame at %.4f (%+.4f), the grab at %.4f (%+.4f, %.2f), arrived %.4f, walk %.3f at %.1f px/s; off the mark %d frames" % [
				drop, entry, scene.drop_shown_at, scene.drop_shown_at - drop, grip, grip - Layout.grip_time(),
				Layout.grip_time(), scene.cues.get(&"arrive", -1.0), scene.walk_at, scene.walk_speed, seen.off_mark])
			t.check(near(scene.drop_shown_at, drop), "the drop frame within a frame of %.2f, from %s (%.4f)" % [drop, entry,
				scene.drop_shown_at])
			t.check(near(grip, Layout.grip_time()) and seen.grab_on_cue,
				"the grab within a frame of %.2f, on the grip cue's frame, from %s (%.4f)" % [Layout.grip_time(), entry, grip])
			t.check(seen.off_mark == 0 and near(scene.cues.get(&"arrive", -1.0), Layout.arrive_time()),
				"on LIFT_MARK from the arrival on, which is within a frame of %.2f (%d frames off)" % [Layout.arrive_time(),
					seen.off_mark])
			t.check(scene.walk_speed >= Layout.WALK_PACE - 0.01 and scene.walk_speed <= Layout.WALK_PACE * 1.25
				and scene.walk_at >= Layout.EARLIEST_WALK - 1e-6 and is_equal_approx(scene.walk_speed,
					distance / (Layout.arrive_time() - scene.walk_at)) and seen.first_walk.distance_to(entry) <= scene.walk_speed / 30.0,
				"the walk starts on its spot, no earlier than %.1f s, at %.1f px/s, inside its limits" % [Layout.EARLIEST_WALK,
					scene.walk_speed])
			if scene.own_track and drop == Layout.GRIP_TIME and entry == ENTRIES[0]:
				t.check(absf(scene.music.stream.get_length() - Layout.MUSIC_LOCAL_LENGTH) < 0.05,
					"the user's track is the one the beat sheet was read off (%.2f s)" % scene.music.stream.get_length())
	Layout.entry_override = Vector2.INF


#THE LINE

static func tier_line(t) -> void:
	var scene: Node = await open_ending(t)
	var watch = Finale.Watch.new(t)
	t.process_frame.connect(watch.step)
	var typing := func() -> bool:
		return is_instance_valid(scene.balloon) and scene.balloon.is_inside_tree() and scene.balloon.dialogue_line != null 			and scene.balloon.dialogue_label.visible_characters > 4
	await until(t, typing, 60 * 20)
	var balloon: Node = scene.balloon
	var line: RefCounted = balloon.dialogue_line
	var text: String = balloon.dialogue_label.get_parsed_text()
	t.log_p("the line at %.3f: %s: %s" % [scene.cues.get(&"announce", -1.0), line.character, text])
	t.check(line.character == "???" and text == LINE, "the announcer's line, verbatim (%s: %s)" % [line.character, text])
	t.check(not balloon.portrait_frame.visible, "no portrait")
	t.check(DialogueVoices.for_character(line.character) == DialogueVoices.VOICES["???"], "his own voice")
	var typed := {"at": -1.0}
	var track := func():
		if is_instance_valid(balloon) and balloon.is_inside_tree() and typed.at < 0.0 and not balloon.dialogue_label.is_typing:
			typed.at = scene.music_time()
	t.process_frame.connect(track)
	var before: int = balloon.dialogue_label.visible_characters
	await _presses(t)
	var during := {"line": balloon.dialogue_line == line, "chars": balloon.dialogue_label.visible_characters,
		"cut": scene.cut, "typing": balloon.dialogue_label.is_typing}
	t.check(during.line and during.typing and during.chars > before and during.chars < text.length() and not during.cut,
		"accept, punch and an ESC tap while it types change nothing (%s, from %d letters)" % [during, before])
	await until(t, func(): return typed.at >= 0.0, 60 * 10)
	t.process_frame.disconnect(track)
	t.log_p("typed out at %.3f, NAME_AT %.2f (%.3f to spare)" % [typed.at, Layout.NAME_AT, Layout.NAME_AT - typed.at])
	t.check(typed.at > 0.0 and typed.at < Layout.NAME_AT, "typed out before NAME_AT (%.3f)" % typed.at)
	await t.wait(10)
	await _presses(t)
	t.check(is_instance_valid(balloon) and balloon.dialogue_line == line and not scene.cut,
		"accept, punch and an ESC tap once it has typed change nothing")
	t.check(balloon.progress.modulate.a == 0.0, "no 'press on' arrow")
	var closed := {"at": -1.0, "gone": false}
	var close_track := func():
		if closed.at < 0.0 and scene.cues.has(&"line_off"):
			closed.at = scene.cues[&"line_off"]
			closed.gone = not is_instance_valid(scene.balloon)
	t.process_frame.connect(close_track)
	await until(t, func(): return closed.at >= 0.0, 60 * 10)
	t.process_frame.disconnect(close_track)
	t.check(near(closed.at, Layout.NAME_AT + Layout.NAME_HOLD) and closed.gone,
		"closed at %.2f within a frame (%.4f), gone on that frame" % [Layout.NAME_AT + Layout.NAME_HOLD, closed.at])
	await until_song(t, scene, Layout.FADE_AT + 1.0)
	t.process_frame.disconnect(watch.step)
	t.check(watch.lines.size() == 1, "the only line ever shown (%d)" % watch.lines.size())


static func _presses(t) -> void:
	t.tap(KEY_ENTER)
	await t.wait(3)
	t.tap(KEY_Q)
	await t.wait(3)
	t.press(KEY_ESCAPE)
	await t.wait(4)
	t.release(KEY_ESCAPE)
	await t.wait(3)


#WATCHED

static func tier_watched(t) -> void:
	var scene: Node = await open_ending(t)
	var schedule: Array = scene.schedule.map(func(cue: Dictionary) -> Array: return [cue.name, cue.at])
	var watch = Finale.Watch.new(t)
	t.process_frame.connect(watch.step)
	var seen := {"black": -1.0}
	var track := func():
		if scene_is(t, ENDING) and seen.black < 0.0 and scene.cues.has(&"fade") and scene.fade.color.a >= 0.999:
			seen.black = scene.music_time()
	t.process_frame.connect(track)
	await until(t, func(): return scene.credits != null, 60 * 30)
	t.process_frame.disconnect(track)
	var cues: Dictionary = scene.cues.duplicate()
	var stream: AudioStream = scene.music.stream
	var into: float = scene.music.get_playback_position()
	var off := []
	for cue in schedule:
		if cue[0] != &"fade_in" and not near(cues.get(cue[0], -1.0), cue[1]):
			off.append("%s %.4f/%.2f" % [cue[0], cues.get(cue[0], -1.0), cue[1]])
	t.log_p("cues %s" % [cues])
	t.check(cues.keys() == schedule.map(func(cue: Array) -> StringName: return cue[0]) and off.is_empty(),
		"every cue in order within a frame of its time (%s)" % [off])
	t.check(near(seen.black, Layout.FADE_AT + Layout.FADE_TIME), "black within a frame of %.2f (%.4f)" % [
		Layout.FADE_AT + Layout.FADE_TIME, seen.black])
	await t.wait(90)
	var later: float = scene.music.get_playback_position()
	t.check(scene.music.playing and scene.music.stream == stream and later > into + 1.0,
		"the song plays on into the credits on the same stream (%.2f -> %.2f)" % [into, later])
	var lines: Array = scene.credits.rendered_lines()
	var roles := 0
	var named := 0
	for i in lines.size() - 1:
		if lines[i].kind == &"role" and Layout.CREDITS_ROLES.has(lines[i].text):
			roles += 1
			named += 1 if lines[i + 1].kind == &"name" and lines[i + 1].text == "Burak Yilmaz" else 0
	var song: bool = lines.any(func(line: Dictionary) -> bool: return String(line.text).contains("Universal Collapse"))
	t.check(roles == Layout.CREDITS_ROLES.size() and named == roles, "every role is Burak Yilmaz (%d of %d)" % [named, roles])
	t.check(song == scene.own_track, "the Universal Collapse line %s" % ("there, the song having played" if scene.own_track
		else "not there, the song not having played"))
	t.check(lines[-1].kind == &"thanks" and lines[-1].text == Layout.CREDITS_THANK_YOU, "THANK YOU FOR PLAYING last")
	var phases := []
	var phase_track := func():
		if scene_is(t, ENDING) and scene.credits != null and (phases.is_empty() or phases[-1] != scene.credits.phase):
			phases.append(scene.credits.phase)
	t.process_frame.connect(phase_track)
	var started := Time.get_ticks_msec()
	var menu: bool = await until(t, func(): return scene_is(t, MENU), 60 * 100)
	t.process_frame.disconnect(phase_track)
	t.log_p("the credits' phases %s; the menu %.1f s after the roll began" % [phases, (Time.get_ticks_msec() - started) / 1000.0])
	t.check(menu and phases.has(&"roll") and phases.slice(phases.find(&"roll")) == [&"roll", &"thanks", &"leaving"],
		"the roll, THANK YOU, then the menu (%s)" % [phases])
	await at_menu(t, watch, "watched")


# At the menu: nothing of the ending left anywhere.
static func at_menu(t, watch, label: String) -> void:
	await until(t, func(): return scene_is(t, MENU), 60 * 20)
	await t.wait(5)
	t.process_frame.disconnect(watch.step)
	var left: Array = t.root.get_children().filter(func(node: Node) -> bool:
		return node != t.current_scene and not AUTOLOADS.has(node.name))
	var balloon: Node = Finale.balloon_in(t.current_scene)
	t.check(scene_is(t, MENU) and t.root.canvas_transform == Transform2D.IDENTITY and Engine.time_scale == 1.0
		and balloon == null and not t.root.has_node("FightOutro") and left.is_empty() and watch.bare == 0,
		"%s: at the menu, the view level, time_scale 1, no balloon, no FightOutro, nothing left on the root (%s), no bare frame (%d)" % [
			label, left.map(func(node: Node) -> String: return node.name), watch.bare])


#HELD

static func tier_held(t) -> void:
	for point in [["the walk", 4.5], ["the gather", 8.3], ["the line", 12.4]]:
		var scene: Node = await open_ending(t)
		await until_song(t, scene, point[1])
		var seen := {"cut": 0, "landed": 0, "view": Transform2D(), "balloon": true}
		var track := func():
			if not is_instance_valid(scene):
				return
			if scene.cut and seen.cut == 0:
				seen.cut = Time.get_ticks_usec()
			if scene.credits != null and seen.landed == 0:
				seen.landed = Time.get_ticks_usec()
				seen.view = t.root.canvas_transform
				seen.balloon = is_instance_valid(scene.balloon)
		t.process_frame.connect(track)
		await hold_escape(t)
		await until(t, func(): return scene.credits != null, 120)
		t.process_frame.disconnect(track)
		var took: float = (seen.landed - seen.cut) / 1e6
		t.log_p("a hold in %s: the credits %.3f s after the skip, the song at %.2f" % [point[0], took,
			scene.music.get_playback_position()])
		t.check(seen.cut > 0 and seen.landed > 0 and took <= Layout.SKIP_FADE + SLACK + 0.005 and not seen.balloon
			and seen.view == Transform2D.IDENTITY and scene.music.playing,
			"a hold in %s lands on the credits within SKIP_FADE and a frame (%.3f s), no balloon, the view level, the song on" % [
				point[0], took])
	t.press(KEY_ESCAPE)
	var held: Node = await open_ending(t)
	for i in 60:
		await t.process_frame
	t.check(not held.cut and held.entrance == null, "an ESC held as it loads does nothing")
	t.release(KEY_ESCAPE)
	await t.wait(3)
	t.check(held.entrance != null, "and arms the skip once it is let go")
	await hold_escape(t)
	await until(t, func(): return held.credits != null, 120)
	t.check(held.credits != null, "after which a hold skips")
	var watch = Finale.Watch.new(t)
	t.process_frame.connect(watch.step)
	await until(t, func(): return held.credits_skip != null, 120)
	await t.wait(3)
	await hold_escape(t)
	var menu: bool = await until(t, func(): return scene_is(t, MENU), 120)
	t.check(menu, "a hold in the credits lands on the menu")
	await at_menu(t, watch, "held")


#THE SWITCH

static func tier_switch(t) -> void:
	GodLayout.USE_FINAL_BEAM = false
	for on in [true, false]:
		Layout.USE_CHAMPION_ENDING = on
		var god: Node = await God.open_god(t, [] as Array[String])
		await t.wait_until(func(): return god.state_machine.current_state.name == "Idle", 300)
		var watch = Finale.Watch.new(t)
		t.process_frame.connect(watch.step)
		var first := {}
		var track := func():
			if first.is_empty() and scene_is(t, ENDING):
				first.view = t.root.canvas_transform
				first.base = ScreenView.base_zoom
		t.process_frame.connect(track)
		god.boss_health = 1
		god.take_uppercut(null)
		if on:
			var ended: bool = await until(t, func(): return scene_is(t, ENDING), 60 * 25)
			await t.wait(5)
			t.process_frame.disconnect(track)
			t.process_frame.disconnect(watch.step)
			t.log_p("on: scenes %s, first frame %s, outros %d" % [watch.scenes.map(func(s: String) -> String: return s.get_file()),
				first, watch.outros.size()])
			t.check(ended and watch.outros.size() == 1 and not watch.scenes.has(CARD) and watch.bare == 0,
				"on: his defeat goes to the ending, one FightOutro, no card, no bare frame")
			t.check(first.get("view") == Transform2D.IDENTITY and first.get("base") == 1.0,
				"on: the view level and the base the arena's on its first frame (%s)" % [first])
		else:
			var carded: bool = await until(t, func(): return scene_is(t, MENU), 60 * 40)
			t.process_frame.disconnect(track)
			t.process_frame.disconnect(watch.step)
			var after: Array = watch.scenes.slice(watch.scenes.find(GOD_SCENE) + 1)
			t.check(carded and after == [CARD, MENU], "off: the card, then the menu (%s)" % [after.map(func(s: String) -> String:
				return s.get_file())])


#THE FALLBACK

static func tier_fallback(t) -> void:
	Layout.MUSIC_LOCAL = MISSING_TRACK
	var scene: Node = await open_ending(t)
	await t.wait(3)
	t.check(not scene.own_track and scene.music.playing and scene.music.stream.resource_path == Layout.MUSIC_FALLBACK,
		"the fallback plays (%s)" % scene.music.stream.resource_path)
	await until(t, func(): return scene.drop_shown_at >= 0.0, 60 * 15)
	var off := []
	for cue in [&"walk", &"arrive", &"grip", &"drop"]:
		var want: float = {&"walk": scene.walk_at, &"arrive": Layout.arrive_time(), &"grip": Layout.grip_time(),
			&"drop": Layout.DROP_TIME}[cue]
		if not near(scene.cues.get(cue, -1.0), want):
			off.append("%s %.4f/%.2f" % [cue, scene.cues.get(cue, -1.0), want])
	t.check(off.is_empty() and near(scene.drop_shown_at, Layout.DROP_TIME),
		"the cues and the drop frame on the scene clock within a frame (%s; drop %.4f)" % [off, scene.drop_shown_at])
	await hold_escape(t)
	await until(t, func(): return scene.credits != null, 120)
	var song: bool = scene.credits.rendered_lines().any(func(line: Dictionary) -> bool:
		return String(line.text).contains("Universal Collapse"))
	t.check(scene.credits != null and not song, "no Universal Collapse in the credits without the song")


#THE MENU

static func tier_menu(t) -> void:
	await t.open_scene(MENU)
	await t.wait(40)
	var progress: Node = t.root.get_node("GameProgress")
	progress.fight_index = 4
	progress.start_at_finale = true
	var row: Button = null
	for button in t.current_scene.find_children("*", "Button", true, false):
		if button.text.strip_edges() == "ENDING":
			row = button
	t.check(row != null and not row.disabled, "the ENDING row, enabled")
	if row == null:
		return
	row.pressed.emit()
	var opened: bool = await until(t, func(): return scene_is(t, ENDING), 120)
	t.check(opened and progress.fight_index == -1 and not progress.start_at_finale,
		"it opens the ending with the run's progress reset (fight_index %d)" % progress.fight_index)


#THE ART

static func tier_art(t) -> void:
	_art(true)
	var scene: Node = await open_ending(t)
	var roar_sheets: bool = scene.crowds.size() == 2 and scene.crowds.all(func(crowd: Sprite2D) -> bool:
		return Layout.CROWD_ROAR.values().has(crowd.texture.resource_path) and crowd.hframes == Layout.ROAR_HFRAMES)
	var burst: Sprite2D = scene.art_fx.get(&"confetti_burst")
	t.check(scene.final_champion and scene.final_fx and scene.final_roar and scene.final_burst and roar_sheets
		and burst != null and burst.hframes * burst.vframes >= Layout.FX[&"confetti_burst"].frames,
		"the approved art in play, the crowd on its roar sheets, the burst on its grid (%s)" % [
			"%dx%d" % [burst.hframes, burst.vframes] if burst != null else "none"])
	t.check(scene.stand_idle.visible and not scene.champion.visible and not scene.trophy.visible and not scene.stand.visible,
		"the waiting cup's loop up, the lift and the stand-ins not")
	var seen := {"wrong": [], "arrive": {}, "drop": {}, "roar": false, "rain_early": false, "rain_at": -1.0, "idle_frames": {},
		"burst": [], "burst_on": -1.0, "burst_off": -1.0}
	var track := func():
		if not is_instance_valid(scene) or scene.credits != null or scene.cut:
			return
		var frame_name: StringName = scene.lift_frame
		if frame_name == &"":
			seen.idle_frames[scene.stand_idle.frame] = true
			return
		var want := Layout.LIFT_FRAMES.find(frame_name)
		if not scene.champion.visible or scene.champion.frame != want or scene.walker.sprite.visible or scene.stand_idle.visible:
			seen.wrong.append("%s %d" % [frame_name, scene.champion.frame])
		if seen.arrive.is_empty():
			seen.arrive = {"frame": scene.champion.frame, "at": scene.cues.get(&"arrive", -1.0)}
		if frame_name == &"lift" and seen.drop.is_empty():
			seen.drop = {"frame": scene.champion.frame, "at": scene.drop_shown_at,
				"flash": scene.art_fx[&"lift_flash"].visible and scene.art_fx[&"lift_flash"].frame == 0,
				"sweep": scene.art_fx[&"spot_sweep"].visible, "rain": scene.art_fx[&"confetti_rain"].visible}
		if scene.cues.has(&"drop") and not scene.cues.has(&"settle") and scene.crowds.all(func(crowd: Sprite2D) -> bool:
				return Layout.ROAR_FRAMES.has(crowd.frame)):
			seen.roar = true
		if scene.art_fx[&"confetti_rain"].visible and seen.rain_at < 0.0:
			seen.rain_at = scene.music_time()
		var burst_sheet: Sprite2D = scene.art_fx[&"confetti_burst"]
		if burst_sheet.visible and (seen.burst.is_empty() or seen.burst[-1] != burst_sheet.frame):
			if seen.burst.is_empty():
				seen.burst_on = scene.music_time()
			seen.burst.append(burst_sheet.frame)
		elif not burst_sheet.visible and not seen.burst.is_empty() and seen.burst_off < 0.0:
			seen.burst_off = scene.music_time()
	t.process_frame.connect(track)
	await until_song(t, scene, Layout.DROP_TIME + 1.6)
	t.process_frame.disconnect(track)
	t.log_p("art: arrival %s, drop %s, rain from %.3f, the waiting cup's frames %s, wrong %s" % [seen.arrive, seen.drop,
		seen.rain_at, seen.idle_frames.keys(), seen.wrong.slice(0, 5)])
	t.check(seen.idle_frames.size() >= 3, "the waiting cup's shine loop plays through the walk-in")
	t.check(seen.arrive.get("frame", -1) == 0 and near(seen.arrive.get("at", -1.0), Layout.arrive_time())
		and seen.wrong.is_empty(), "the lift sheet from the arrival, frame 0, on the song's frame every frame (%d wrong)" % [
			seen.wrong.size()])
	t.check(seen.drop.get("frame", -1) == 6 and near(seen.drop.get("at", -1.0), Layout.DROP_TIME)
		and seen.drop.get("flash", false) and seen.drop.get("sweep", false) and not seen.drop.get("rain", true),
		"frame 6 within a frame of the drop, the lift flash and the sweep with it, no rain yet (%s)" % [seen.drop])
	t.check(near(seen.rain_at, Layout.DROP_TIME + Layout.FX[&"confetti_rain"].from), "the rain a beat after (%.3f)" % seen.rain_at)
	t.check(seen.roar, "the crowd roaring after the drop")
	var frames: int = Layout.FX[&"confetti_burst"].frames
	var burst_time: float = frames * Layout.FX[&"confetti_burst"].step
	var rising := true
	for i in range(1, seen.burst.size()):
		rising = rising and seen.burst[i] > seen.burst[i - 1]
	t.log_p("the burst's frames %s, on at %.3f and off at %.3f" % [seen.burst, seen.burst_on, seen.burst_off])
	t.check(not seen.burst.is_empty() and near(seen.burst_on, Layout.DROP_TIME) and seen.burst[0] == 0
		and seen.burst[-1] == frames - 1 and rising and near(seen.burst_off, Layout.DROP_TIME + burst_time),
		"the burst from frame 0 on the drop to frame %d in order, once, gone %.2f s on, within a frame" % [frames - 1,
			burst_time])
	await hold_escape(t)
	await until(t, func(): return scene.credits != null, 120)
	scene.credits.phase = &"roll"
	scene.credits.scroll = scene.credits.roll_height + 2000.0
	await until(t, func(): return scene.credits.phase == &"thanks", 60)
	t.check(scene.credits.thanks.get_node_or_null("Still") != null, "the still behind THANK YOU")


static func tier_stand_in(t) -> void:
	_art(false)
	var scene: Node = await open_ending(t)
	t.check(not scene.final_champion and scene.champion == null and scene.trophy.visible and scene.stand.visible,
		"the stand-ins up")
	var seen := {"wrong": [], "frames": {}, "flash": false, "shower": false}
	var track := func():
		if not is_instance_valid(scene) or scene.credits != null:
			return
		var frame_name: StringName = scene.lift_frame
		seen.frames[frame_name] = true
		var want: Vector2 = Layout.at_cell(Layout.TROPHY_BOTTOM.get(frame_name, Layout.TROPHY_REST))
		var over := frame_name == &"" or Layout.TROPHY_ON_STAND.has(frame_name)
		var z: int = Layout.TROPHY_OVER_Z if over else Layout.TROPHY_UNDER_Z
		if scene.trophy.global_position != want or scene.trophy.z_index != z:
			seen.wrong.append("%s %s z%d" % [frame_name, scene.trophy.global_position, scene.trophy.z_index])
		if frame_name == &"lift":
			seen.flash = seen.flash or scene.flash.color.a > 0.0
			seen.shower = seen.shower or scene.shower.visible
	t.process_frame.connect(track)
	await until_song(t, scene, Layout.DROP_TIME + 1.6)
	t.process_frame.disconnect(track)
	t.log_p("stand-in: frames seen %s, wrong %s" % [seen.frames.keys(), seen.wrong.slice(0, 5)])
	t.check(seen.wrong.is_empty() and seen.frames.size() >= 10,
		"the stand-in cup where the art's is on every frame, over the player on the stand and under them overhead")
	t.check(seen.flash and seen.shower, "the stand-in flash and shower on the drop")
