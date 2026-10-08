extends RefCounted

# jordan_finale (coder A): Jordan's finale (scratchpad plan PLAN.md, 2026-09-28): his win in the arena through the
# walk-out, his room, the collapse into the void, the TO BE CONTINUED card and back to the menu. --max-fps 60, since the
# balloon's input locks and the card's are real time. tier=
#   watched  Jordan killed after load_fight: one FightOutro, WalkOut entered; the walk-out line verbatim, him off the
#            top of the screen, the gates open, the crowd booing and the player out through the gate; the scenes after
#            the fight exactly the room, the card and the menu, never Victory. In the room an arrow walks the player
#            into the talk zone and the prompt shows, and ENTER starts the talk; all 12 room lines by speaker and
#            parsed text; the nine cameos in ladder order and on their marks (±1 px) as Liam's line comes up; the
#            moustache on the floor line (±1 px) and the player on "caught"; Liam gone and eight left after the first
#            zap, none after the second; no piece of the room left after the collapse, and the god up before the last
#            line; once he leaps out of his chair, never his seated sheet again; his fight's theme never under the
#            cutscene (JordanFinaleLayout.MUSIC_UNDER, off). With his final theme's intro in, on
#            its own clock: it starts on the flash's peak as the god appears, the room's theme gone and no drone; his
#            last line comes up at INTRO_LINE_AT and types out inside the quiet stretch; the presses on it do nothing,
#            and the cut starts at INTRO_TAIL_AT. At the menu: no FightOutro, no balloon, the view level, time_scale 1,
#            start_at_finale off and ten bosses cleared.
#   held     ESC held ESCAPE_HOLD frames at five points - the arena's line while it types, the roam, the moustache
#            going on, the collapse, his last line - each landing on the card and the menu, with the same checks at
#            the menu; on his last line the card comes with the hold, not the intro's end.
#   menu     the FINALE row (GameProgress.start_at_finale), opened with open_scene, not load_fight, which would end
#            a dialogue: no pre-fight line and no VS card; Jordan Defeated, then WalkOut, the flag cleared; a hold
#            then skips to the menu.
#   lost     the player at 0 health: the two player_lost lines verbatim, a press each, and Defeat; WalkOut never
#            entered and no finale scene loaded.
#   normal   all four in turn.
# With his last phase switched on (JordanFinaleLayout.USE_GOD_FIGHT, and its scene built) every end of the finale lands on
# that fight instead of the card: the scenes after the fight are the room and the god fight, each hold lands on the god
# fight, and the checks made at the menu are made there - but for the view, which comes up on the finale's framing with
# nothing of its shakes or zooms left, and settles once its pull-back is over on the fight's own 2/3 base, still. Every
# cut, whatever the switch: no frame between two scenes left bare (the viewport's grey); into his last phase, the fight
# up within CUT_MS of the last frame before it (it loads while the finale plays, JordanGodLayout.prefetch).

const FIGHT := "res://Scenes/Bosses/JordanBossFightScene.tscn"
const GOD := "res://Scenes/Bosses/JordanGodFightScene.tscn"
const ROOM := "res://Scenes/Core/JordanFinaleScene.tscn"
const CARD := "res://Scenes/Core/ToBeContinuedScene.tscn"
const MENU := "res://Scenes/Core/MainMenuScene.tscn"
const DEFEAT := "res://Scenes/Core/DefeatScene.tscn"
const VICTORY := "res://Scenes/Core/VictoryScene.tscn"
const BODY := "Arena/JordanScene/JordanCharacterBody"
const Layout := preload("res://Scripts/JordanFinaleLayout.gd")
const GodLayout := preload("res://Scripts/JordanGodLayout.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const TIERS := ["watched", "held", "menu", "lost"]
# The intro's clock against the composer's timeline, in seconds: a couple of frames either side.
const INTRO_SLACK := 0.05
# Where the quiet stretch his last line types in ends, and the wind-up starts; and the file's end.
const INTRO_WIND_UP := 7.784
const INTRO_END := 10.378
const ESCAPE_HOLD := 40
# The longest the cut into his last phase may take, from the last frame before it to the fight's first, in ms: its load
# was ~700 ms before it was prefetched, ~100 after.
const CUT_MS := 300.0
# A line is read a press this many frames apart, once it has typed out.
const READ_EVERY := 20
# The longest a whole run may take, in frames.
const RUN_FRAMES := 60 * 160

const WALK_OUT_LINE := "No you cheated, don't cheat, don't cheat, no don't cheat. I won't allow cheaters in this server"
const ROOM_LINES := [
	["Burak", "what the hell dude? I won, game over, now let me into the server"],
	["Liam", "Hey bud... I think he has you muted..."],
	["Burak", "Uhhh ok, I have an idea"],
	["Aiden", "Hey Jordan! My name's Aiden! I love funkos, I love Nintendo and I definitely don't cheat! Can I be let into the server?"],
	["Jordan", "Hey! What's going on Aiden? Weird, you look exactly like a guy named Burak I saw..."],
	["Jordan", "Anyways! Yes dude, you sound like a cool dude! Of course you can! Here let me just send you the server invite..."],
	["Jordan", "Hey wait a second... You're Burak! That damn cheating hockey puck! You...You tricked me...."],
	["Liam", "Hey buddy why don't we just calm down..."],
	["Jordan", "What an idiot. He was trying to trick me too. But I'm done playing your games."],
	["Jordan", "What you don't understand is... This is my world, my server, the others don't even exist if I don't want them to."],
	["Jordan", "The only person in this server.... is just me."],
	["Jordan", "Welcome to my world, Burak."],
]
const LOST_LINES := ["Should've read the server rules.", "Come back when you've got more than a starter role."]
const LADDER := [&"captain_burak", &"eric", &"greyson", &"matt", &"mason", &"josh", &"danny", &"carter", &"liam"]


# What a run saw, frame by frame: the scenes in turn, every FightOutro, and every line of dialogue with what the room
# held as it came up.
class Watch:
	var t
	var scenes: Array = []
	var outros := {}
	var lines: Array = []
	var last_line: RefCounted
	var at_line: Callable
	# Frames between two scenes - the one going already out, the next not yet in - that nothing black covered, which
	# show the viewport's grey; and each change's time, from the last frame of one scene to the first of the next, in
	# ms, by the next scene's path.
	var bare := 0
	var changes := {}
	var last_path := ""
	var last_usec := 0

	func _init(tester) -> void:
		t = tester

	func step() -> void:
		var scene: Node = t.current_scene
		var path: String = scene.scene_file_path if scene != null else ""
		var now := Time.get_ticks_usec()
		if scene == null and not Watch.covered(t.root):
			bare += 1
		if path != "":
			if last_path != "" and path != last_path:
				changes[path] = (now - last_usec) / 1000.0
			last_path = path
			last_usec = now
		if path != "" and (scenes.is_empty() or scenes[-1] != path):
			scenes.append(path)
		var outro: Node = t.root.get_node_or_null("FightOutro")
		if outro != null:
			outros[outro.get_instance_id()] = true
		var balloon: Node = Watch.balloon_in(scene)
		if balloon == null or balloon.dialogue_line == null or balloon.dialogue_line == last_line:
			return
		last_line = balloon.dialogue_line
		var entry := {"character": last_line.character, "text": balloon.dialogue_label.get_parsed_text(), "scene": path}
		lines.append(entry)
		if at_line.is_valid():
			at_line.call(entry, scene)

	# Something black and opaque over the whole screen on a layer of the root's own - a leaving scene's fade kept across
	# the change, or a FightOutro's.
	static func covered(root: Node) -> bool:
		for layer in root.get_children():
			if not (layer is CanvasLayer):
				continue
			for rect in layer.find_children("*", "ColorRect", true, false):
				if rect.is_visible_in_tree() and rect.color.a >= 0.99 and rect.color.v <= 0.01:
					return true
		return false

	# The dialogue balloon up in `scene`, if there is one.
	static func balloon_in(scene: Node) -> Node:
		if scene == null:
			return null
		for child in scene.get_children():
			if child.has_method(&"rearm_input_lock") and child.is_inside_tree():
				return child
		return null


static func balloon_in(scene: Node) -> Node:
	return Watch.balloon_in(scene)


static func run(t) -> void:
	var tiers: Array = TIERS if t.tier == "normal" else [t.tier]
	for tier in tiers:
		t.log_p("-- jordan_finale %s" % tier)
		match tier:
			"watched":
				await tier_watched(t)
			"held":
				await tier_held(t)
			"menu":
				await tier_menu(t)
			"lost":
				await tier_lost(t)
			_:
				t.check(false, "jordan_finale has no tier %s" % tier)


#GETTING THERE

# His fight, the way every mode loads it - its pre-fight lines ended - and a Watch on it from there.
static func into_fight(t) -> Watch:
	await t.load_fight("jordan")
	t.boss = t.current_scene.get_node(BODY)
	t.sm = t.boss.state_machine
	var watch := Watch.new(t)
	t.process_frame.connect(watch.step)
	return watch


# His states in turn while his fight is up, into `states`. Looked up each frame: a lambda holding a node of the fight
# would be called with it freed once the scene has gone.
static func track_states(t, states: Array) -> Callable:
	var track := func():
		if not scene_is(t, FIGHT):
			return
		var body: Node = t.current_scene.get_node_or_null(BODY)
		if body == null or body.state_machine.current_state == null:
			return
		var state := String(body.state_machine.current_state.name)
		if states.is_empty() or states[-1] != state:
			states.append(state)
	t.process_frame.connect(track)
	return track


static func kill(t) -> void:
	t.clear_iframes()
	t.boss.take_finisher(t.boss.boss_health)


# Reads the lines the way a player does, a press every READ_EVERY frames once one has typed out, until `done`.
static func read_until(t, done: Callable, frames := RUN_FRAMES) -> bool:
	for i in frames:
		if done.call():
			return true
		var balloon := balloon_in(t.current_scene)
		if balloon != null and i % READ_EVERY == 0 and not balloon.dialogue_label.is_typing:
			t.tap(KEY_ENTER)
		await t.process_frame
	return done.call()


# In the room, from its arrival: the arrow walks the player into the talk zone, and ENTER starts the talk. Whether the
# prompt showed and the talk started.
static func start_talk(t, room: Node) -> Dictionary:
	await t.wait_until(func(): return room.beat == &"roam", 300)
	t.press(KEY_RIGHT)
	var prompt: bool = await t.wait_until(func(): return room.talk_prompt.visible, 300)
	t.release(KEY_RIGHT)
	await t.wait(2)
	t.tap(KEY_ENTER)
	var talking: bool = await t.wait_until(func(): return room.beat != &"roam", 30)
	return {"prompt": prompt, "talking": talking}


static func hold_escape(t) -> void:
	t.press(KEY_ESCAPE)
	for i in ESCAPE_HOLD:
		await t.process_frame
	t.release(KEY_ESCAPE)


static func scene_is(t, path: String) -> bool:
	return t.current_scene != null and t.current_scene.scene_file_path == path


# Whether the finale ends on his last phase rather than the card (JordanFinaleLayout.after_finale_scene).
static func god_fight_on() -> bool:
	return Layout.after_finale_scene() == GOD


# The menu - or his last phase, when the finale ends on it - and everything the finale must not have left behind on
# the way there. At the menu the view is level. His last phase opens on the finale's own framing, level, and pulls back
# from its second frame (JordanGodOpen), so the view there is checked as it comes up - nothing of the finale's shakes
# or zooms carried over - and again once the pull-back is over: exactly the fight's own 2/3 base (settled_god_view).
static func at_menu(t, label: String) -> void:
	var end := GOD if god_fight_on() else MENU
	await t.wait_until(func(): return scene_is(t, end), RUN_FRAMES)
	var arrived := {"view": t.root.canvas_transform, "shake": ScreenView.shake_offset, "tweens": view_tweens_running()}
	# A FightOutro that brought it here stays one idle frame into it, to keep that frame black, and then goes: counted in
	# idle frames, not physics ones, of which a scene's long first frame runs several.
	await t.wait_until(func(): return not t.root.has_node("FightOutro"), 30)
	await t.wait(2)
	var progress: Node = t.root.get_node("GameProgress")
	var outro: bool = t.root.has_node("FightOutro")
	var balloon := balloon_in(t.current_scene)
	t.check(scene_is(t, end) and not outro and balloon == null, "%s: at %s, no FightOutro and no balloon (%s, %s)" % [label,
		end.get_file(), outro, balloon])
	if end == GOD:
		t.check(arrived.view == Transform2D.IDENTITY and arrived.shake == Vector2.ZERO and not arrived.tweens,
			"%s: his last phase comes up on the finale's framing, nothing of its shakes or zooms left (%s)" % [label, arrived])
		var settled: Dictionary = await settled_god_view(t)
		t.check(settled.ok and is_equal_approx(Engine.time_scale, 1.0),
			"%s: then the view settles on the fight's 2/3 base, still (%s) and time_scale 1 (%.2f)" % [label, settled, Engine.time_scale])
	else:
		t.check(t.root.canvas_transform == Transform2D.IDENTITY and is_equal_approx(Engine.time_scale, 1.0),
			"%s: the view level (%s) and time_scale 1 (%.2f)" % [label, t.root.canvas_transform, Engine.time_scale])
	t.check(not progress.start_at_finale and progress.bosses_cleared == 10,
		"%s: start_at_finale off, ten bosses cleared (%d)" % [label, progress.bosses_cleared])


# His last phase's view once its opening pull-back has had its time: exactly the fight's base (JordanGodLayout's
# VIEW_ZOOM on VIEW_FOCUS, as ScreenView draws it), with no zoom over it, no shake and nothing tweening it. What it saw.
static func settled_god_view(t) -> Dictionary:
	var z: float = GodLayout.VIEW_ZOOM
	var want := Transform2D(Vector2(z, 0.0), Vector2(0.0, z), (ScreenView.VIEW_SIZE / 2.0 - GodLayout.VIEW_FOCUS * z).round())
	var settled: bool = await t.wait_until(func(): return not view_tweens_running() and t.root.canvas_transform.is_equal_approx(want),
		60 * 4)
	var seen := {"view": t.root.canvas_transform, "zoom": ScreenView.zoom, "shake": ScreenView.shake_offset,
		"base": [ScreenView.base_zoom, ScreenView.base_focus], "tweens": view_tweens_running()}
	seen["ok"] = settled and ScreenView.zoom == 1.0 and ScreenView.shake_offset == Vector2.ZERO \
		and is_equal_approx(ScreenView.base_zoom, z) and ScreenView.base_focus == GodLayout.VIEW_FOCUS
	return seen


# The cut into what comes after: no frame between the two scenes left bare (the viewport's grey), and, into his last
# phase, the fight up within CUT_MS of the last frame before it - it loaded while the finale played
# (JordanGodLayout.prefetch), rather than in the cut.
static func check_cut(t, watch: Watch, label: String) -> void:
	var took: float = watch.changes.get(GOD, -1.0)
	t.log_p("%s: the cut into %s took %.0f ms, %d bare frames" % [label, watch.last_path.get_file(), took, watch.bare])
	t.check(watch.bare == 0, "%s: no frame between the scenes left bare, grey (%d)" % [label, watch.bare])
	if god_fight_on():
		t.check(took >= 0.0 and took < CUT_MS, "%s: the fight up %.0f ms after the last frame before it (under %.0f)" % [label,
			took, CUT_MS])


static func view_tweens_running() -> bool:
	return (ScreenView.zoom_tween != null and ScreenView.zoom_tween.is_running()) \
		or (ScreenView.shake_tween != null and ScreenView.shake_tween.is_running())


static func after_fight(scenes: Array) -> Array:
	var index := scenes.find(FIGHT)
	return scenes.slice(index + 1) if index >= 0 else scenes


#WATCHED

static func tier_watched(t) -> void:
	var watch := await into_fight(t)
	var walk_out: Node = t.sm.states["WalkOut"]
	var arena := {"lowest": INF, "gates": false, "booed": false, "player_exit": INF, "beats": {}}
	var in_arena := func():
		if not scene_is(t, FIGHT):
			return
		var scene: Node = t.current_scene
		var body: Node = scene.get_node_or_null(BODY)
		var gates: Node = scene.get_node_or_null("Arena/Gates")
		var player: Node = scene.get_node_or_null("Arena/MainPlayer/CharacterBody2D")
		if body == null or gates == null or player == null:
			return
		arena.lowest = minf(arena.lowest, body.global_position.y)
		arena.gates = arena.gates or gates.is_open()
		arena.booed = arena.booed or t.get_nodes_in_group("arena_crowd").any(func(c): return c._boo_time_left > 0.0)
		arena.player_exit = minf(arena.player_exit, player.global_position.y)
		arena.beats = body.state_machine.states["WalkOut"].beat_times.duplicate()
	t.process_frame.connect(in_arena)
	# Looked up each frame, as in_arena is: the room goes when the card comes.
	var stood := {"sat_again": false}
	var sync := {"flash": -1.0, "god": false, "music_off": false, "drone": false, "line": -1.0, "shown": -1.0, "typed": -1.0,
		"cut": -1.0, "arrow": false, "theme_ever": false, "intro_ever": false}
	var in_room_frames := func():
		if not scene_is(t, ROOM):
			return
		var room: Node = t.current_scene
		stood.sat_again = stood.sat_again or (not room.seated and room.jordan.spec.get("sheet", "") == Layout.SEATED_SHEET)
		sync.theme_ever = sync.theme_ever or room.music.playing
		sync.intro_ever = sync.intro_ever or room.intro != null
		if room.intro == null:
			return
		if sync.flash < 0.0:
			sync.flash = room.flash.color.a
			sync.god = room.god_shown
			sync.music_off = not room.music.playing
		sync.drone = sync.drone or room.sounds[&"drone"].playing
		var balloon := balloon_in(room)
		var last: bool = balloon != null and balloon.dialogue_line != null and balloon.dialogue_line.text.begins_with("Welcome")
		if last and sync.line < 0.0:
			sync.line = room.intro_cues.get(&"line", -1.0)
			sync.shown = room.intro_time()
		if last and sync.typed < 0.0 and not balloon.dialogue_label.is_typing:
			sync.typed = room.intro_time()
		if last and not balloon.dialogue_label.is_typing:
			sync.arrow = sync.arrow or (balloon.progress.visible and balloon.progress.modulate.a > 0.0)
		if room.leaving and sync.cut < 0.0:
			sync.cut = room.intro_cues.get(&"cut", -1.0)
	t.process_frame.connect(in_room_frames)
	var room_state := {}
	watch.at_line = func(entry: Dictionary, scene: Node) -> void:
		if entry.scene != ROOM:
			return
		room_state[entry.text] = {"cameos": scene.cameos.keys(), "marks": _on_marks(scene),
			"moustache": scene.moustache.global_position.distance_to(scene.moustache_landing) if is_instance_valid(scene.moustache) and scene.moustache_landing != Vector2.INF else INF,
			"gag": scene.gag_frame, "liam": scene.cameos.has(&"liam"), "pieces": scene.crumble.pieces_left(),
			"god": scene.god_shown}
	kill(t)
	var entered: bool = await t.wait_until(func(): return walk_out.entered, 300)
	t.check(entered and t.sm.current_state == walk_out, "his KO hands to the walk-out (%s)" % t.sm.current_state.name)
	var in_room: bool = await read_until(t, func(): return scene_is(t, ROOM))
	t.process_frame.disconnect(in_arena)
	var walk_line: Array = watch.lines.filter(func(line): return line.scene == FIGHT)
	t.log_p("in the arena: lines %s, him up to y %.0f, gates %s, booed %s, the player up to y %.0f, beats %s"
		% [walk_line, arena.lowest, arena.gates, arena.booed, arena.player_exit, arena.beats])
	t.check(walk_line.size() == 1 and walk_line[0].character == "Jordan" and walk_line[0].text == WALK_OUT_LINE,
		"the walk-out line, verbatim")
	# His soles are 96 px under his origin (JordanArtLayout.FLOOR_POINT): above the screen's top edge, he is off it.
	t.check(arena.lowest + 96.0 <= 0.0 and arena.gates and arena.booed,
		"he storms off the top of the screen (%.0f), through the open gate, to boos" % arena.lowest)
	t.check(in_room and arena.player_exit <= -80.0, "the player follows him out through the gate (%.0f) into his room" % arena.player_exit)
	t.check(watch.outros.size() == 1, "one FightOutro (%d)" % watch.outros.size())
	var room: Node = t.current_scene
	var talk: Dictionary = await start_talk(t, room)
	t.check(talk.prompt and talk.talking, "an arrow walks the player into the talk zone, the prompt shows, and ENTER starts the talk")
	await read_until(t, func(): return scene_is(t, CARD) or scene_is(t, MENU) or scene_is(t, GOD))
	var room_lines: Array = watch.lines.filter(func(line): return line.scene == ROOM).map(func(line): return [line.character, line.text])
	var wrong := []
	for i in maxi(room_lines.size(), ROOM_LINES.size()):
		var got: Array = room_lines[i] if i < room_lines.size() else []
		var want: Array = ROOM_LINES[i] if i < ROOM_LINES.size() else []
		if got != want:
			wrong.append([i, got, want])
	t.check(wrong.is_empty(), "the room's 12 lines by speaker and parsed text (%d seen; wrong %s)" % [room_lines.size(), wrong])
	var at_liam: Dictionary = room_state.get(ROOM_LINES[1][1], {})
	t.log_p("as Liam's line comes up: %s" % [at_liam])
	t.check(at_liam.get("cameos", []) == LADDER and at_liam.get("marks", false), "the nine in ladder order, each on his mark")
	var at_glare: Dictionary = room_state.get(ROOM_LINES[6][1], {})
	t.check(at_glare.get("moustache", INF) <= 1.0 and at_glare.get("gag") == &"caught",
		"the moustache on the floor line (%.2f px off) and the player caught (%s)" % [at_glare.get("moustache", INF), at_glare.get("gag")])
	var after_zap: Dictionary = room_state.get(ROOM_LINES[8][1], {})
	var after_rest: Dictionary = room_state.get(ROOM_LINES[10][1], {})
	t.check(not after_zap.get("liam", true) and after_zap.get("cameos", []).size() == 8 and after_rest.get("cameos", [0]).is_empty(),
		"Liam gone and eight left after the first zap (%s), none after the second (%s)" % [after_zap.get("cameos"), after_rest.get("cameos")])
	var last: Dictionary = room_state.get(ROOM_LINES[11][1], {})
	t.check(last.get("pieces", -1) == 0 and last.get("god", false), "nothing of the room left (%s) and the god up for the last line" % last.get("pieces"))
	t.process_frame.disconnect(in_room_frames)
	t.check(not stood.sat_again, "once he leaps out of his chair he stays on his feet")
	t.check(Layout.MUSIC_UNDER or not sync.theme_ever,
		"his fight's theme never plays under the cutscene (JordanFinaleLayout.MUSIC_UNDER off: %s)" % not sync.theme_ever)
	t.check(Layout.USE_INTRO or not sync.intro_ever,
		"no music at the reveal either: his final theme's intro never starts (JordanFinaleLayout.USE_INTRO off: %s)" % not sync.intro_ever)
	if Layout.USE_INTRO and ResourceLoader.exists(Layout.INTRO):
		t.log_p("the intro's clock: at its start the flash %.2f, the god %s, the room's theme off %s; the last line cued at %.3f, on screen at %.3f, typed out at %.3f; the cut at %.3f; a drone %s"
			% [sync.flash, sync.god, sync.music_off, sync.line, sync.shown, sync.typed, sync.cut, sync.drone])
		t.check(sync.flash >= 0.99 and sync.god and sync.music_off and not sync.drone,
			"the intro starts on the flash's peak as the god appears, the room's theme gone and no drone")
		t.check(absf(sync.line - Layout.INTRO_LINE_AT) <= INTRO_SLACK and sync.typed > sync.line and sync.typed < INTRO_WIND_UP,
			"his last line comes up at %.3f (%.3f) and has typed out inside the quiet stretch (%.3f)" % [Layout.INTRO_LINE_AT, sync.line, sync.typed])
		t.check(absf(sync.cut - Layout.INTRO_TAIL_AT) <= INTRO_SLACK and sync.cut < INTRO_END and not sync.arrow,
			"no press-on arrow, the presses on it do nothing, and the cut starts at %.3f (%.3f), before the file ends"
			% [Layout.INTRO_TAIL_AT, sync.cut])
	await at_menu(t, "watched")
	check_cut(t, watch, "watched")
	t.process_frame.disconnect(watch.step)
	var scenes: Array = after_fight(watch.scenes)
	t.log_p("scenes after the fight: %s" % [scenes])
	if god_fight_on():
		t.check(scenes == [ROOM, GOD] and not watch.scenes.has(VICTORY), "after the fight: the room, his last phase, and never Victory")
	else:
		t.check(scenes == [ROOM, CARD, MENU] and not watch.scenes.has(VICTORY), "after the fight: the room, the card, the menu, and never Victory")


# Every cameo on his mark, ±1 px.
static func _on_marks(room: Node) -> bool:
	if room.cameos.size() != Layout.BOSS_MARKS.size():
		return false
	for i in LADDER.size():
		var actor: Node2D = room.cameos.get(LADDER[i])
		if actor == null or actor.global_position.distance_to(Layout.BOSS_MARKS[i]) > 1.0:
			return false
	return true


#HELD

static func tier_held(t) -> void:
	for point in ["arena", "roam", "moustache", "collapse", "last line"]:
		var watch := await into_fight(t)
		kill(t)
		await t.wait_until(func(): return t.sm.states["WalkOut"].entered, 300)
		match point:
			"arena":
				await t.wait_until(func(): return balloon_in(t.current_scene) != null and balloon_in(t.current_scene).dialogue_label.is_typing, 300)
			_:
				await read_until(t, func(): return scene_is(t, ROOM))
				var room: Node = t.current_scene
				if point != "roam":
					await start_talk(t, room)
				if point == "last line":
					await read_until(t, func(): return scene_is(t, ROOM) and balloon_in(room) != null \
						and balloon_in(room).dialogue_line != null and balloon_in(room).dialogue_line.text.begins_with("Welcome"))
				else:
					var at: StringName = {"roam": &"roam", "moustache": &"gag", "collapse": &"collapse"}[point]
					await read_until(t, func(): return scene_is(t, ROOM) and room.beat == at)
				# Halfway through the room coming apart.
				if point == "collapse":
					await t.wait(90)
		var where: String = t.current_scene.scene_file_path if t.current_scene else ""
		await hold_escape(t)
		# On his last line the hold's own quick fade brings the card, well before the intro's end would.
		var landing := GOD if god_fight_on() else CARD
		var carded: bool = await t.wait_until(func(): return scene_is(t, landing), 90 if point == "last line" else 240)
		t.log_p("held at %s (%s): %s %s" % [point, where.get_file(), landing.get_file(), carded])
		t.check(carded, "held at the %s: %s" % [point, landing.get_file()])
		await at_menu(t, "held at the %s" % point)
		check_cut(t, watch, "held at the %s" % point)
		t.process_frame.disconnect(watch.step)
		var scenes: Array = after_fight(watch.scenes)
		var want: Array = [CARD, MENU] if point == "arena" else [ROOM, CARD, MENU]
		if god_fight_on():
			want = [GOD] if point == "arena" else [ROOM, GOD]
		t.check(scenes == want and not watch.scenes.has(VICTORY), "held at the %s: %s, never Victory (%s)" % [point, want.map(func(s): return s.get_file()), scenes.map(func(s): return s.get_file())])


#THE FINALE ROW

static func tier_menu(t) -> void:
	var progress: Node = t.root.get_node("GameProgress")
	progress.reset_progress()
	progress.start_at_finale = true
	var watch := Watch.new(t)
	t.process_frame.connect(watch.step)
	var states := []
	var track := track_states(t, states)
	var card_played := [false]
	var watch_card := func():
		var card: Node = t.current_scene.get_node_or_null("Arena/VsCard") if scene_is(t, FIGHT) else null
		card_played[0] = card_played[0] or (card != null and card.is_playing())
	t.process_frame.connect(watch_card)
	await t.open_scene(FIGHT)
	# The harness's own change, made in a physics step, is flushed before that frame is drawn; only the game's cuts count.
	watch.bare = 0
	var cleared: bool = not progress.start_at_finale
	t.boss = t.current_scene.get_node(BODY)
	t.sm = t.boss.state_machine
	await t.wait_until(func(): return t.sm.states["WalkOut"].entered, 300)
	# His line only types once he is up off the floor (storms_off), so a fixed wait after the balloon would race it.
	await t.wait_until(func(): return not watch.lines.is_empty(), 180)
	var first_lines: Array = watch.lines.duplicate()
	t.log_p("states %s, lines %s, the card played %s" % [states, first_lines, card_played[0]])
	t.check(cleared, "the fight takes the FINALE row's flag as it loads")
	t.check(first_lines.size() == 1 and first_lines[0].text == WALK_OUT_LINE and not card_played[0],
		"no pre-fight line and no VS card: the walk-out's line is the first")
	t.check(states.slice(-2) == ["Defeated", "WalkOut"], "Jordan Defeated, then WalkOut (%s)" % [states])
	await hold_escape(t)
	await at_menu(t, "the FINALE row")
	check_cut(t, watch, "the FINALE row")
	t.process_frame.disconnect(track)
	t.process_frame.disconnect(watch_card)
	t.process_frame.disconnect(watch.step)


#THE LOSS

static func tier_lost(t) -> void:
	var watch := await into_fight(t)
	var states := []
	var track := track_states(t, states)
	t.player.playerHealth = 0
	var defeated: bool = await read_until(t, func(): return scene_is(t, DEFEAT), 60 * 30)
	t.process_frame.disconnect(watch.step)
	t.process_frame.disconnect(track)
	var lines: Array = watch.lines.map(func(line): return line.text)
	t.log_p("lost: lines %s, his states %s, scenes %s" % [lines, states, watch.scenes])
	t.check(lines == LOST_LINES, "the two player_lost lines, verbatim")
	t.check(defeated and not states.has("WalkOut") and not watch.scenes.has(ROOM), "Defeat, the walk-out never entered and no room")
