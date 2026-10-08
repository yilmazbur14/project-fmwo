extends SceneTree

# Headless checks on controller support and the rebindable controls: the input map, InputSettings'
# bindings, their file, the 8-way stick, the device tracking, and every screen that shows a control.
# One mode per run, no window needed:
#   Godot.exe --headless --fixed-fps 60 --path . --script res://art_source/controls_settings/verify_controls.gd -- mode=<name>
# README.md lists the modes.
#
# Every check prints "P PASS ..." or "P FAIL ...", each run ends with
#   P [<time> f<frame>] RESULT mode=<name> fails=<n>
# and the process exits with that number of failures.
#
# Input goes in as real events through Input.parse_input_event(), so what is under test is the path
# the game uses. Bindings are pointed at a scratch file before anything changes them, so no run
# changes the controls of whoever is playtesting from this checkout: the only write the real file
# can get is the one booting the game gives it anyway (a first run, a repair or a migration).

const TEST_SAVE_PATH := "user://input_bindings_test.cfg"
const CONTROLS_SCENE := "res://Scenes/Core/ControlsScene.tscn"
const SETTINGS_SCENE := "res://Scenes/Core/ControlsSettingsScene.tscn"
const MENU_SCENE := "res://Scenes/Core/MainMenuScene.tscn"
const INTRO_SCENE := "res://Scenes/Core/IntroCutsceneScene.tscn"
const VICTORY_SCENE := "res://Scenes/Core/VictoryScene.tscn"
const DEFEAT_SCENE := "res://Scenes/Core/DefeatScene.tscn"
const DANNY_DIALOGUE := "res://Dialogue/ControlsSceneDialogue.dialogue"
# The modes about Eric's own fight: his mash, his outro and the quiet fight the pause modes use. The rooms
# lead to GameProgress.first_fight(), which is Captain Burak's.
const ERIC_FIGHT := "res://Scenes/Bosses/EricBossFightScene.tscn"
# Each mash action's pad button, whichever pair the finisher is on.
const PAD_MASH := {&"punch": JOY_BUTTON_A, &"dodge": JOY_BUTTON_B, &"mash_left": JOY_BUTTON_LEFT_SHOULDER, &"mash_right": JOY_BUTTON_RIGHT_SHOULDER}

# D2 and the arrows, written out rather than read back from InputSettings, so a wrong default there
# can't pass by agreeing with itself.
const EXPECTED_KEYS := {
	&"move_up": KEY_UP, &"move_down": KEY_DOWN, &"move_left": KEY_LEFT, &"move_right": KEY_RIGHT,
	&"punch": KEY_Q, &"dodge": KEY_W, &"block": KEY_SHIFT,
}
const EXPECTED_PAD := {
	&"punch": JOY_BUTTON_A, &"dodge": JOY_BUTTON_B, &"block": JOY_BUTTON_LEFT_SHOULDER,
}
const UI_ACTIONS: Array[StringName] = [&"ui_accept", &"ui_cancel", &"ui_select", &"ui_up", &"ui_down", &"ui_left", &"ui_right", &"ui_focus_next", &"ui_focus_prev"]

var mode := ""
# outro_mash only: what the outro gets, a | ab | deliberate.
var press := "a"
# eric_mash only: keyboard | pad.
var mash_device := "keyboard"
# defeat_retry only: one of its cases by label (RETRY_EXTRA_CASES, or a fight's scene file name), "" for all of them.
var retry_only := ""
var fails := 0
var clock := 0.0
var frame := 0
var settings: Node


func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("mode="):
			mode = arg.substr(5)
		elif arg.begins_with("press="):
			press = arg.substr(6)
		elif arg.begins_with("device="):
			mash_device = arg.substr(7)
		elif arg.begins_with("fight="):
			retry_only = arg.substr(6)
	_main.call_deferred()


func log_p(msg: String) -> void:
	print("P [%.3f f%d] %s" % [clock, frame, msg])


func check(cond: bool, msg: String) -> void:
	print("P %s %s" % ["PASS" if cond else "FAIL", msg])
	if not cond:
		fails += 1


func _process(delta: float) -> bool:
	clock += delta
	frame += 1
	return false


func wait(n: int) -> void:
	for i in n:
		await process_frame


func _main() -> void:
	await process_frame
	settings = root.get_node("InputSettings")
	settings.save_path = TEST_SAVE_PATH
	settings.reset_to_defaults()
	# The progress save too, and from no save at all: a scratch file a run that died left behind must not hand the menu
	# a CONTINUE.
	var progress: Node = root.get_node("GameProgress")
	progress.save_path = TEST_PROGRESS_PATH
	remove_progress_file()
	progress.load_save()
	match mode:
		"defaults": await test_defaults()
		"rebind": await test_rebind()
		"persist": await test_persist()
		"move_vector": await test_move_vector()
		"device": await test_device()
		"screens": await test_screens()
		"training": await test_training()
		"rebind_screen": await test_rebind_screen()
		"handoffs": await test_handoffs()
		"outro_mash": await test_outro_mash()
		"eric_mash": await test_eric_mash()
		"pause_input": await test_pause_input()
		"pause_controls": await test_pause_controls()
		"trigger_press": await test_trigger_press()
		"flow_prefetch": await test_flow_prefetch()
		"parry_tap": await test_parry_tap()
		"restart_phase": await test_restart_phase()
		"hud_fade": await test_hud_fade()
		"dash_punch": await test_dash_punch()
		"outro_stale": await test_outro_stale()
		"defeat_retry": await test_defeat_retry()
		"ladder_order": await test_ladder_order()
		"progress_save": await test_progress_save()
		"retry_skip": await test_retry_skip()
		"loss_lines": await test_loss_lines()
		"balloon_accept": await test_balloon_accept()
		"playtest_panel": await test_playtest_panel()
		"unlock_panel": await test_unlock_panel()
		"victory_menu": await test_victory_menu()
		"menu_music": await test_menu_music()
		_:
			log_p("unknown mode " + mode)
			fails += 1
	DirAccess.remove_absolute(ProjectSettings.globalize_path(TEST_SAVE_PATH))
	remove_progress_file()
	log_p("RESULT mode=%s fails=%d" % [mode, fails])
	quit(fails)


# ------------------------------------------------------------------ helpers

func key_event(code: int, pressed: bool, echo := false) -> InputEventKey:
	var ev := InputEventKey.new()
	ev.physical_keycode = code
	ev.keycode = code
	ev.pressed = pressed
	ev.echo = echo
	return ev


func button_event(button: int, pressed: bool) -> InputEventJoypadButton:
	var ev := InputEventJoypadButton.new()
	ev.button_index = button
	ev.pressed = pressed
	return ev


func axis_event(axis: int, value: float) -> InputEventJoypadMotion:
	var ev := InputEventJoypadMotion.new()
	ev.axis = axis
	ev.axis_value = value
	return ev


# Dispatched now rather than at the start of the next frame.
func send(events: Array) -> void:
	for ev in events:
		Input.parse_input_event(ev)
	Input.flush_buffered_events()


func tap_key(code: int) -> void:
	send([key_event(code, true), key_event(code, false)])


func tap_button(button: int) -> void:
	send([button_event(button, true), button_event(button, false)])


func load_scene(path: String) -> void:
	change_scene_to_file(path)
	while current_scene == null or current_scene.scene_file_path != path:
		await process_frame
	await wait(3)


# The boss entrance that plays between a fight loading and its pre-fight lines, and holds the player
# through it. Only Eric has one. Every mode here is about what a device does in the fight or in the
# lines, so it is cut the way a held ui_cancel cuts it.
func skip_entrance() -> void:
	var intro: Node = null
	for node in current_scene.find_children("*", "Node", true, false):
		if node.has_method(&"finish_entrance"):
			intro = node
			break
	if intro == null:
		return
	# Its Enter() is deferred, so on a freshly loaded fight it may not have started yet.
	for i in 60:
		if intro.entered:
			break
		await process_frame
	if not intro.finished:
		intro.skip()
	await wait(2)


# The VS card plays between a fight's pre-fight lines and the fight itself and holds the player
# until it is done. Every mode here is about what a device does in the fight, so the card is skipped
# the way a player skips it, and the input grace it leaves behind is dropped rather than waited out:
# those 0.15 seconds are real ones, and under --fixed-fps 60 a frame costs none of them.
func skip_vs_card() -> void:
	var card := current_scene.get_node_or_null("Arena/VsCard")
	if card == null:
		return
	if card.is_playing():
		card.skip()
		for i in 60:
			if not card.is_playing():
				break
			await process_frame
	card.grace_until_msec = 0
	await wait(2)


func wait_for_scene(path: String, max_frames := 300) -> bool:
	for i in max_frames:
		if current_scene != null and current_scene.scene_file_path == path:
			return true
		await process_frame
	return false


# The alpha a control is actually drawn at: its own, times every parent's up to its CanvasLayer.
# Checking a node's own modulate would miss a group fading out from over it.
func drawn_alpha(control: Control) -> float:
	var alpha := 1.0
	var item: CanvasItem = control
	while item != null:
		alpha *= item.modulate.a
		item = item.get_parent() as CanvasItem
	return alpha


func focus_owner() -> Control:
	return root.gui_get_focus_owner()


func focus_name() -> String:
	var owner := focus_owner()
	return str(owner.name) if owner else "<none>"


func describe(ev: InputEvent) -> String:
	if ev is InputEventKey:
		return "key:%d" % (ev.physical_keycode if ev.physical_keycode != 0 else ev.keycode)
	if ev is InputEventJoypadButton:
		return "button:%d" % ev.button_index
	if ev is InputEventJoypadMotion:
		return "axis:%d@%.1f" % [ev.axis, ev.axis_value]
	return ev.get_class()


# InputMap's events for an action, one side of it, as sorted text.
func events_of(action: StringName, gamepad: bool) -> Array:
	var out := []
	for ev in InputMap.action_get_events(action):
		if (ev is InputEventKey) != gamepad:
			out.append(describe(ev))
	out.sort()
	return out


func saved_bindings() -> Dictionary:
	var cfg := ConfigFile.new()
	if cfg.load(TEST_SAVE_PATH) != OK:
		return {}
	var out := {}
	for action in settings.ACTIONS:
		out[action] = cfg.get_value("bindings", action, null)
	return out


func defaults() -> Dictionary:
	return settings._default_bindings()


# ------------------------------------------------------------------ defaults

func test_defaults() -> void:
	log_p("-- every action: one key and one pad binding, and they are D2's")
	for action in settings.ACTIONS:
		var keys := events_of(action, false)
		var pad := events_of(action, true)
		check(keys == ["key:%d" % EXPECTED_KEYS[action]], "%s has exactly its one key %s" % [action, keys])
		if settings.MOVE_ACTIONS.has(action):
			var fixed: Array = settings.MOVE_PAD_EVENTS[action]
			var expected := ["axis:%d@%.1f" % [fixed[1], fixed[2]], "button:%d" % fixed[0]]
			expected.sort()
			check(pad == expected, "%s has its d-pad button and its stick direction %s" % [action, pad])
		else:
			check(pad == ["button:%d" % EXPECTED_PAD[action]], "%s has exactly its one pad button %s" % [action, pad])
		# project.godot and InputSettings are both a source of the defaults; the editor shows the one
		# and the game runs the other, so they have to agree.
		var written := []
		for ev in ProjectSettings.get_setting("input/" + action)["events"]:
			written.append(describe(ev))
		written.sort()
		var live := keys + pad
		live.sort()
		check(written == live, "%s in project.godot matches what the game applies %s" % [action, written])
	check(events_of(&"startdialogue", false) == ["key:32"] and events_of(&"startdialogue", true).is_empty(), "the dead startdialogue is untouched")

	log_p("-- ui_* is never written, only topped up")
	var in_input := false
	var ui_written := []
	for line in FileAccess.get_file_as_string("res://project.godot").split("\n"):
		if line.begins_with("["):
			in_input = line.strip_edges() == "[input]"
		elif in_input and line.begins_with("ui_"):
			ui_written.append(line.get_slice("=", 0))
	check(ui_written.is_empty(), "project.godot overrides no ui_* action %s" % [ui_written])
	for action in UI_ACTIONS:
		var builtin: Array = ProjectSettings.get_setting("input/" + action)["events"]
		var live: Array = InputMap.action_get_events(action)
		var kept := builtin.all(func(b: InputEvent) -> bool: return live.any(func(l: InputEvent) -> bool: return describe(l) == describe(b)))
		var extra := live.filter(func(l: InputEvent) -> bool: return not builtin.any(func(b: InputEvent) -> bool: return describe(l) == describe(b)))
		var only_pad := extra.all(func(e: InputEvent) -> bool: return e is InputEventJoypadButton or e is InputEventJoypadMotion)
		check(kept and only_pad, "%s keeps every built-in event, and anything added is a pad event %s" % [action, extra.map(describe)])
	check(events_of(&"ui_accept", true).has("button:%d" % JOY_BUTTON_A), "A confirms (the engine ships ui_accept without it)")
	check(events_of(&"ui_cancel", true).has("button:%d" % JOY_BUTTON_B), "B cancels (the engine ships ui_cancel without it)")
	for action in [&"ui_up", &"ui_down", &"ui_left", &"ui_right"]:
		check(events_of(action, true).size() == 2, "%s still has the engine's d-pad and stick %s" % [action, events_of(action, true)])

	log_p("-- names and glyphs")
	check([settings.move_name, settings.punch_name, settings.dodge_name, settings.block_name] == ["ARROWS", "Q", "W", "SHIFT"], "keyboard names %s" % [[settings.move_name, settings.punch_name, settings.dodge_name, settings.block_name]])
	check([settings.pad_label_for(&"punch"), settings.pad_label_for(&"dodge"), settings.pad_label_for(&"block")] == ["A", "B", "LB"], "pad names: attack A, dash B, block LB")
	check([settings.pad_frame_for(&"punch"), settings.pad_frame_for(&"dodge"), settings.pad_frame_for(&"block")] == [0, 1, 4], "pad glyph columns")
	check(settings.label_for(settings.MOVE) == "ARROWS", "label_for(MOVE) names movement as a whole")

	log_p("-- the feel_v2 mash's own pair")
	check(events_of(&"mash_left", false) == ["key:%d" % KEY_LEFT] and events_of(&"mash_left", true) == ["button:%d" % JOY_BUTTON_LEFT_SHOULDER], "mash_left is the left arrow and LB %s" % [events_of(&"mash_left", false) + events_of(&"mash_left", true)])
	check(events_of(&"mash_right", false) == ["key:%d" % KEY_RIGHT] and events_of(&"mash_right", true) == ["button:%d" % JOY_BUTTON_RIGHT_SHOULDER], "mash_right is the right arrow and RB %s" % [events_of(&"mash_right", false) + events_of(&"mash_right", true)])
	var file := ConfigFile.new()
	file.load(TEST_SAVE_PATH)
	var saved: PackedStringArray = file.get_section_keys("bindings")
	check(not settings.ACTIONS.has(&"mash_left") and not saved.has("mash_left") and not saved.has("mash_right"), "neither is rebindable yet, nor saved")
	check([settings.key_label_for(&"mash_left"), settings.key_label_for(&"mash_right"), settings.pad_label_for(&"mash_left"), settings.pad_label_for(&"mash_right")] == ["LEFT", "RIGHT", "LB", "RB"], "named LEFT, RIGHT, LB and RB")
	check([settings.pad_frame_for(&"mash_left"), settings.pad_frame_for(&"mash_right")] == [4, 5], "drawn from the bumper columns")


# ------------------------------------------------------------------ rebind

func test_rebind() -> void:
	var changes := [0]
	settings.bindings_changed.connect(func() -> void: changes[0] += 1)

	log_p("-- one side changes, the other stays byte-identical")
	var before: Dictionary = settings.bindings.duplicate(true)
	var pad_events := events_of(&"punch", true)
	var loser: StringName = settings.rebind(&"punch", key_event(KEY_E, true))
	check(loser == &"", "E was free")
	check(settings.bindings[&"punch"]["key"] == KEY_E, "punch is on E")
	check(settings.bindings[&"punch"]["pad_button"] == before[&"punch"]["pad_button"] and settings.bindings[&"punch"]["pad_axis"] == before[&"punch"]["pad_axis"], "punch's pad side is unchanged")
	check(events_of(&"punch", true) == pad_events and events_of(&"punch", false) == ["key:%d" % KEY_E], "and so is its pad side in the input map")
	check(saved_bindings()[&"punch"] == settings.bindings[&"punch"], "written to the file at once")
	check(settings.punch_name == "E", "the dialogue name follows (%s)" % settings.punch_name)
	check(changes[0] == 1, "bindings_changed once")

	var key_events := events_of(&"dodge", false)
	loser = settings.rebind(&"dodge", button_event(JOY_BUTTON_Y, true))
	check(loser == &"" and settings.bindings[&"dodge"]["pad_button"] == JOY_BUTTON_Y, "dodge is on Y")
	check(events_of(&"dodge", false) == key_events and settings.bindings[&"dodge"]["key"] == KEY_W, "dodge's key is unchanged")

	log_p("-- a trigger")
	loser = settings.rebind(&"block", axis_event(JOY_AXIS_TRIGGER_RIGHT, 0.8))
	check(settings.bindings[&"block"]["pad_axis"] == JOY_AXIS_TRIGGER_RIGHT and settings.bindings[&"block"]["pad_button"] == -1, "block is on RT, and on no button")
	check(events_of(&"block", true) == ["axis:%d@1.0" % JOY_AXIS_TRIGGER_RIGHT], "the input map has the trigger %s" % [events_of(&"block", true)])
	check(settings.pad_label_for(&"block") == "RT" and settings.pad_frame_for(&"block") == 7, "named RT, drawn from column 7")
	send([axis_event(JOY_AXIS_TRIGGER_RIGHT, 0.9)])
	check(Input.is_action_pressed(&"block"), "pulling RT blocks")
	send([axis_event(JOY_AXIS_TRIGGER_RIGHT, 0.0)])
	check(not Input.is_action_pressed(&"block"), "letting go stops")
	# The pull put the player on the pad; the names below are the keyboard's.
	send([key_event(KEY_Z, true), key_event(KEY_Z, false)])

	log_p("-- a conflict unbinds exactly the loser")
	before = settings.bindings.duplicate(true)
	loser = settings.rebind(&"dodge", key_event(KEY_E, true))
	check(loser == &"punch", "punch lost E (%s)" % loser)
	check(settings.bindings[&"punch"]["key"] == -1 and events_of(&"punch", false).is_empty(), "punch has no key now")
	check(settings.bindings[&"punch"]["pad_button"] == before[&"punch"]["pad_button"], "punch keeps its pad button")
	check(settings.bindings[&"dodge"]["key"] == KEY_E, "dodge is on E")
	for action in settings.ACTIONS:
		if action != &"punch" and action != &"dodge":
			check(settings.bindings[action] == before[action], "%s untouched" % action)
	check(not settings.is_bound(&"punch", false) and settings.key_label_for(&"punch") == settings.UNBOUND_LABEL, "shown unbound")
	check(saved_bindings()[&"punch"]["key"] == -1, "the unbind is in the file")

	before = settings.bindings.duplicate(true)
	loser = settings.rebind(&"punch", button_event(JOY_BUTTON_Y, true))
	check(loser == &"dodge", "on the pad too: dodge lost Y (%s)" % loser)
	check(settings.bindings[&"dodge"]["pad_button"] == -1 and settings.bindings[&"dodge"]["pad_axis"] == -1 and events_of(&"dodge", true).is_empty(), "dodge has no pad binding now")
	check(settings.bindings[&"dodge"]["key"] == before[&"dodge"]["key"], "dodge keeps its key")

	log_p("-- what can't be bound")
	before = settings.bindings.duplicate(true)
	var count: int = changes[0]
	settings.rebind(&"move_up", button_event(JOY_BUTTON_A, true))
	settings.rebind(&"punch", button_event(JOY_BUTTON_DPAD_UP, true))
	settings.rebind(&"punch", axis_event(JOY_AXIS_LEFT_X, 1.0))
	settings.rebind(&"punch", axis_event(JOY_AXIS_RIGHT_Y, 1.0))
	check(settings.bindings == before and changes[0] == count, "movement's pad side, the d-pad and the sticks are all refused, and nothing changes")

	log_p("-- movement's keys")
	settings.reset_to_defaults()
	loser = settings.rebind(&"move_up", key_event(KEY_W, true))
	check(loser == &"dodge", "W taken from dash (%s)" % loser)
	var move_pad := events_of(&"move_up", true)
	check(move_pad.size() == 2, "move_up keeps the d-pad and the stick %s" % [move_pad])
	check(settings.move_name == "W/LEFT/DOWN/RIGHT", "the dialogue name spells the keys out (%s)" % settings.move_name)
	check(not settings.is_default(settings.MOVE, false), "movement is off its defaults")

	log_p("-- reset")
	count = changes[0]
	settings.reset_to_defaults()
	check(settings.bindings == defaults(), "everything back to the defaults")
	check(saved_bindings() == defaults(), "and written")
	check(changes[0] == count + 1, "bindings_changed once for the reset")
	check(settings.move_name == "ARROWS" and settings.dodge_name == "W", "names back")


# ------------------------------------------------------------------ persist

func write_file(text: String) -> void:
	var file := FileAccess.open(TEST_SAVE_PATH, FileAccess.WRITE)
	file.store_string(text)
	file.close()


func reload() -> void:
	settings._load()
	settings.apply_all()


# A file as version 1 wrote it: its defaults, which had the pad on X, RB and LB, with `changes`
# ({action: {field: value}}) over them.
func write_v1(changes: Dictionary) -> void:
	var v1_pad := {&"punch": JOY_BUTTON_X, &"dodge": JOY_BUTTON_RIGHT_SHOULDER, &"block": JOY_BUTTON_LEFT_SHOULDER}
	var cfg := ConfigFile.new()
	cfg.set_value("meta", "version", 1)
	for action in settings.ACTIONS:
		var binding: Dictionary = defaults()[action].duplicate()
		if v1_pad.has(action):
			binding["pad_button"] = v1_pad[action]
		binding.merge(changes.get(action, {}), true)
		cfg.set_value("bindings", action, binding)
	cfg.save(TEST_SAVE_PATH)


# Attack's, dash's and block's pad buttons.
func pad_buttons() -> Array:
	return [settings.bindings[&"punch"]["pad_button"], settings.bindings[&"dodge"]["pad_button"], settings.bindings[&"block"]["pad_button"]]


func saved_version() -> int:
	var cfg := ConfigFile.new()
	cfg.load(TEST_SAVE_PATH)
	return cfg.get_value("meta", "version", -1)


func test_persist() -> void:
	log_p("-- save, clear, load")
	settings.rebind(&"punch", key_event(KEY_E, true))
	settings.rebind(&"dodge", axis_event(JOY_AXIS_TRIGGER_LEFT, 1.0))
	settings.rebind(&"block", key_event(KEY_Q, true))
	settings.rebind(&"move_left", key_event(KEY_A, true))
	var saved: Dictionary = settings.bindings.duplicate(true)
	var map_before := {}
	for action in settings.ACTIONS:
		map_before[action] = events_of(action, false) + events_of(action, true)
	check(saved_bindings() == saved, "every change is already on disk")
	settings.bindings = {}
	for action in settings.ACTIONS:
		InputMap.action_erase_events(action)
	reload()
	check(settings.bindings == saved, "loaded back identical")
	var map_same := true
	for action in settings.ACTIONS:
		map_same = map_same and map_before[action] == events_of(action, false) + events_of(action, true)
	check(map_same, "and the input map is identical")
	check(settings.bindings[&"punch"]["key"] == KEY_E and settings.bindings[&"block"]["key"] == KEY_Q, "rebinds survive")
	check(settings.bindings[&"punch"]["key"] == KEY_E and settings.bindings[&"dodge"]["pad_axis"] == JOY_AXIS_TRIGGER_LEFT, "a trigger survives")
	settings.rebind(&"punch", key_event(KEY_Q, true))
	reload()
	check(settings.bindings[&"block"]["key"] == -1, "an unbind survives (block lost Q to punch)")

	log_p("-- missing")
	DirAccess.remove_absolute(ProjectSettings.globalize_path(TEST_SAVE_PATH))
	reload()
	check(settings.bindings == defaults(), "defaults")
	check(FileAccess.file_exists(TEST_SAVE_PATH) and saved_bindings() == defaults(), "and written straight away")

	# A crash mid-write can cut anywhere: into something that no longer parses, which is the garbage
	# case below, or into a shorter file that does, which is this one.
	log_p("-- truncated")
	settings.rebind(&"punch", key_event(KEY_E, true))
	settings.rebind(&"block", key_event(KEY_C, true))
	var custom: Dictionary = settings.bindings.duplicate(true)
	var whole := FileAccess.get_file_as_string(TEST_SAVE_PATH)
	write_file(whole.substr(0, whole.length() / 2))
	reload()
	var sane: bool = settings.ACTIONS.all(func(a: StringName) -> bool: return settings.bindings[a] == custom[a] or settings.bindings[a] == defaults()[a])
	check(sane, "every action is what it was or its default, never a half-read value")
	check(settings.bindings[&"block"] == defaults()[&"block"], "the cut-off actions fall back (block)")
	check(saved_bindings() == settings.bindings, "and the file is rewritten whole")

	log_p("-- garbage")
	write_file("}{ not a config file ][ ===\n\"unterminated")
	reload()
	check(settings.bindings == defaults(), "falls back to defaults")
	check(saved_bindings() == defaults(), "and the file is rewritten")

	log_p("-- a version it doesn't know")
	settings.rebind(&"punch", key_event(KEY_E, true))
	write_file(FileAccess.get_file_as_string(TEST_SAVE_PATH).replace("version=%d" % settings.SAVE_VERSION, "version=99"))
	reload()
	check(settings.bindings == defaults(), "falls back wholesale, custom binding and all")
	var cfg := ConfigFile.new()
	cfg.load(TEST_SAVE_PATH)
	check(cfg.get_value("meta", "version") == settings.SAVE_VERSION and saved_bindings() == defaults(), "and is rewritten at the current version")

	log_p("-- version 1, the pad never changed: moved from X, RB, LB onto A, B, LB")
	write_v1({&"punch": {"key": KEY_E}})
	reload()
	check(pad_buttons() == [JOY_BUTTON_A, JOY_BUTTON_B, JOY_BUTTON_LEFT_SHOULDER], "attack on A, dash on B, block still LB %s" % [pad_buttons()])
	check(settings.bindings[&"punch"]["key"] == KEY_E and settings.bindings[&"dodge"]["key"] == KEY_W, "the keyboard is kept exactly, custom key and all")
	check(saved_version() == settings.SAVE_VERSION and saved_bindings() == settings.bindings, "rewritten at version %d" % settings.SAVE_VERSION)

	log_p("-- version 1, the pad changed: kept exactly")
	write_v1({&"punch": {"pad_button": JOY_BUTTON_Y}})
	reload()
	check(pad_buttons() == [JOY_BUTTON_Y, JOY_BUTTON_RIGHT_SHOULDER, JOY_BUTTON_LEFT_SHOULDER], "attack moved to Y keeps Y, and the RB and LB kept with it stay too %s" % [pad_buttons()])
	check(saved_version() == settings.SAVE_VERSION and saved_bindings() == settings.bindings, "rewritten at version %d, unchanged" % settings.SAVE_VERSION)
	write_v1({&"block": {"pad_button": -1, "pad_axis": JOY_AXIS_TRIGGER_RIGHT}})
	reload()
	check(pad_buttons() == [JOY_BUTTON_X, JOY_BUTTON_RIGHT_SHOULDER, -1] and settings.bindings[&"block"]["pad_axis"] == JOY_AXIS_TRIGGER_RIGHT, "so is block moved to RT, with X and RB beside it %s" % [pad_buttons()])

	log_p("-- version %d holding X, RB and LB: chosen, so kept" % settings.SAVE_VERSION)
	settings.reset_to_defaults()
	settings.rebind(&"punch", button_event(JOY_BUTTON_X, true))
	settings.rebind(&"dodge", button_event(JOY_BUTTON_RIGHT_SHOULDER, true))
	reload()
	check(pad_buttons() == [JOY_BUTTON_X, JOY_BUTTON_RIGHT_SHOULDER, JOY_BUTTON_LEFT_SHOULDER], "not migrated %s" % [pad_buttons()])

	log_p("-- one bad action")
	settings.rebind(&"punch", key_event(KEY_E, true))
	settings.rebind(&"dodge", key_event(KEY_R, true))
	cfg = ConfigFile.new()
	cfg.load(TEST_SAVE_PATH)
	cfg.set_value("bindings", &"punch", {"key": 0, "pad_button": JOY_BUTTON_Y, "pad_axis": -1})
	cfg.erase_section_key("bindings", &"block")
	cfg.save(TEST_SAVE_PATH)
	reload()
	check(settings.bindings[&"punch"]["key"] == KEY_Q and settings.bindings[&"punch"]["pad_button"] == JOY_BUTTON_Y, "key 0 falls back to that key's default, the rest of the action loads")
	check(settings.bindings[&"block"] == defaults()[&"block"], "a missing action falls back to its default")
	check(settings.bindings[&"dodge"]["key"] == KEY_R, "the other actions keep what they had")
	check(saved_bindings() == settings.bindings, "and the repaired set is written back")


# ------------------------------------------------------------------ move_vector

func hold_keys(codes: Array) -> void:
	var events := []
	for code in codes:
		events.append(key_event(code, true))
	send(events)


func release_keys(codes: Array) -> void:
	var events := []
	for code in codes:
		events.append(key_event(code, false))
	send(events)


func stick(x: float, y: float) -> void:
	send([axis_event(JOY_AXIS_LEFT_X, x), axis_event(JOY_AXIS_LEFT_Y, y)])


# The read PlayerScript made before InputSettings existed.
func old_read() -> Vector2:
	return Vector2(Input.get_axis("ui_left", "ui_right"), Input.get_axis("ui_up", "ui_down"))


# The smallest push, as a fraction of a full one, that moves the player along `degrees`: found by
# halving, so it is exact rather than whichever step of a sweep happens to land on the threshold.
func engage_push(degrees: float) -> float:
	var direction := Vector2.from_angle(deg_to_rad(degrees))
	var low := 0.0
	var high := 1.0
	for i in 24:
		var mid := (low + high) / 2.0
		stick(direction.x * mid, direction.y * mid)
		if settings.move_vector() == Vector2.ZERO:
			low = mid
		else:
			high = mid
	stick(0.0, 0.0)
	return high


func test_move_vector() -> void:
	log_p("-- the keyboard, byte for byte what it always was")
	var arrows := [KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT]
	for mask in 16:
		var codes := []
		for bit in 4:
			if mask & (1 << bit):
				codes.append(arrows[bit])
		hold_keys(codes)
		var got: Vector2 = settings.move_vector()
		var old := old_read()
		# Bytes rather than ==, which would let a -0.0 through.
		check(var_to_bytes(got) == var_to_bytes(old), "keys %s -> %s, as the old read gave %s" % [codes, got, old])
		release_keys(codes)

	log_p("-- the stick, full over, in 8 directions")
	var directions := [Vector2(1, 0), Vector2(1, 1), Vector2(0, 1), Vector2(-1, 1), Vector2(-1, 0), Vector2(-1, -1), Vector2(0, -1), Vector2(1, -1)]
	for i in 8:
		var raw := Vector2.from_angle(i * PI / 4.0)
		stick(raw.x, raw.y)
		check(settings.move_vector() == directions[i], "%d degrees -> %s (expected %s)" % [i * 45, settings.move_vector(), directions[i]])

	log_p("-- every direction starts moving at the same push")
	var engage := {}
	for degrees in [0, 45, 90, 135, 180, 225, 270, 315, 10, 30, 60, 100, 200, 290]:
		engage[degrees] = engage_push(degrees)
	log_p("first moves at %s" % [engage])
	var first: float = engage[0]
	check(engage.values().all(func(push: float) -> bool: return absf(push - first) < 0.0005), "all 8 directions, and the angles between them, at the same push (%.4f)" % first)
	check(absf(first - 0.30) < 0.0005, "which is 30%% of a full push (the 2026-10-04 playtest; it was 52%%, and half a push walked nowhere) (%.4f)" % first)
	var diagonal := Vector2.from_angle(PI / 4.0) * 0.6
	stick(diagonal.x, diagonal.y)
	check(settings.move_vector() == Vector2(1, 1), "a 60 percent diagonal push moves diagonally; it used to read as centred")
	stick(0.0, 0.0)

	log_p("-- each 22.5 degree boundary snaps to the nearer direction")
	var boundaries_ok := true
	for k in 8:
		var boundary := 22.5 + 45.0 * k
		for push in [1.0, 0.6]:
			for side in [-0.5, 0.5]:
				var d: Vector2 = Vector2.from_angle(deg_to_rad(boundary + side)) * push
				stick(d.x, d.y)
				var want: Vector2 = directions[k] if side < 0.0 else directions[(k + 1) % 8]
				if settings.move_vector() != want:
					boundaries_ok = false
					log_p("  %.1f degrees at %.1f of a push -> %s, expected %s" % [boundary + side, push, settings.move_vector(), want])
	stick(0.0, 0.0)
	check(boundaries_ok, "half a degree either side of all 8 boundaries, at a full push and at 60 percent, goes to the nearer direction")

	stick(0.7, 0.7)
	var corner: Vector2 = settings.move_vector()
	stick(0.0, 0.0)
	hold_keys([KEY_RIGHT, KEY_DOWN])
	var keys: Vector2 = settings.move_vector()
	release_keys([KEY_RIGHT, KEY_DOWN])
	check(corner == Vector2(1, 1) and corner == keys, "a (0.7, 0.7) stick corner is exactly two arrow keys (%s against %s)" % [corner, keys])
	check(corner.normalized() * 600.0 == keys.normalized() * 600.0, "so the dash off it is the same length")

	log_p("-- the d-pad")
	send([button_event(JOY_BUTTON_DPAD_RIGHT, true), button_event(JOY_BUTTON_DPAD_DOWN, true)])
	check(settings.move_vector() == Vector2(1, 1), "right and down on the d-pad -> (1, 1)")
	send([button_event(JOY_BUTTON_DPAD_RIGHT, false), button_event(JOY_BUTTON_DPAD_DOWN, false)])
	check(settings.move_vector() == Vector2.ZERO, "released -> zero")

	log_p("-- the dead zone")
	for push in [Vector2(0.1, 0.0), Vector2(0.2, 0.1), Vector2(0.29, 0.0), Vector2(0.0, -0.29), Vector2(0.2, 0.2)]:
		stick(push.x, push.y)
		check(settings.move_vector() == Vector2.ZERO, "a %s push reads as centred" % push)
	# Half a push and a little past the threshold both move, on the snapped direction: a dash pressed while
	# the stick is still on its way out reads the same, rather than going off in place.
	for case in [[Vector2(0.32, 0.0), Vector2(1, 0)], [Vector2(0.0, -0.35), Vector2(0, -1)], [Vector2(0.25, 0.25), Vector2(1, 1)], [Vector2(-0.5, 0.0), Vector2(-1, 0)], [Vector2(0.36, 0.36), Vector2(1, 1)]]:
		stick(case[0].x, case[0].y)
		check(settings.move_vector() == case[1], "a %s push moves %s (%s)" % [case[0], case[1], settings.move_vector()])
	stick(0.0, 0.0)


# ------------------------------------------------------------------ device

func test_device() -> void:
	var changes := []
	settings.device_changed.connect(func(device: int) -> void: changes.append(device))
	check(settings.device == 0, "starts on the keyboard with no pad connected")

	send([button_event(JOY_BUTTON_A, true)])
	check(settings.device == 1 and changes == [1], "a pad press -> gamepad, one signal")
	send([button_event(JOY_BUTTON_A, false), button_event(JOY_BUTTON_B, true), button_event(JOY_BUTTON_B, false)])
	check(changes == [1], "more pad presses and releases -> no more signals")
	var art: GDScript = load("res://Scripts/ControlsArtLayout.gd")
	check(settings.punch_name == art.inline_glyph(0) and settings.move_name == "LEFT STICK" and settings.label_for(&"punch") == "A", "the dialogue names follow the pad: A drawn inline, the stick named")

	send([key_event(KEY_Z, true)])
	check(settings.device == 0 and changes == [1, 0], "a key press -> keyboard")
	check(settings.punch_name == "Q" and settings.move_name == "ARROWS", "names follow the keyboard")
	send([key_event(KEY_Z, false)])
	send([button_event(JOY_BUTTON_A, true), button_event(JOY_BUTTON_A, false)])
	send([key_event(KEY_Z, true, true), key_event(KEY_Z, false)])
	check(settings.device == 1 and changes == [1, 0, 1], "a held key's echo and a key release don't count")

	send([key_event(KEY_Z, true), key_event(KEY_Z, false)])
	send([axis_event(JOY_AXIS_LEFT_X, 0.3), axis_event(JOY_AXIS_LEFT_Y, -0.3), axis_event(JOY_AXIS_TRIGGER_LEFT, 0.3)])
	check(settings.device == 0 and changes == [1, 0, 1, 0], "stick and trigger drift at 0.3 don't count")
	send([axis_event(JOY_AXIS_LEFT_X, 0.6)])
	check(settings.device == 1 and changes == [1, 0, 1, 0, 1], "a real push at 0.6 does")
	send([axis_event(JOY_AXIS_LEFT_X, 0.0), axis_event(JOY_AXIS_LEFT_Y, 0.0), axis_event(JOY_AXIS_TRIGGER_LEFT, 0.0)])

	var motion := InputEventMouseMotion.new()
	motion.relative = Vector2(30, 12)
	motion.position = Vector2(400, 300)
	send([motion])
	check(settings.device == 1 and changes.size() == 5, "a mouse nudge doesn't count")
	var click := InputEventMouseButton.new()
	click.button_index = MOUSE_BUTTON_LEFT
	click.pressed = true
	click.position = Vector2(400, 300)
	send([click])
	check(settings.device == 0 and changes == [1, 0, 1, 0, 1, 0], "a mouse click does")
	click = click.duplicate()
	click.pressed = false
	send([click])

	log_p("-- plugging in and out")
	Input.joy_connection_changed.emit(0, true)
	check(settings.device == 1 and changes.size() == 7, "plugging a pad in -> gamepad at once")
	Input.joy_connection_changed.emit(1, true)
	check(changes.size() == 7, "a second pad -> no second signal")
	send([key_event(KEY_Z, true), key_event(KEY_Z, false)])
	Input.joy_connection_changed.emit(0, true)
	check(settings.device == 1 and changes.size() == 9, "plugging in wins even straight after a key press")
	# Headless has no real pads, so the engine's list is empty whichever one is unplugged: this is
	# the "none left" case.
	Input.joy_connection_changed.emit(0, false)
	check(settings.device == 0 and changes.size() == 10, "unplugging the last pad -> keyboard")
	check(changes.size() == 10 and changes == [1, 0, 1, 0, 1, 0, 1, 0, 1, 0], "exactly one signal per real change %s" % [changes])


# ------------------------------------------------------------------ screens

func card(glyph_name: String) -> Array:
	var glyph: TextureRect = current_scene.get_node("%" + glyph_name)
	var keycap: Label = null
	for child in glyph.get_parent().get_children():
		if child is Label:
			keycap = child
	return [glyph, keycap]


# A drawn texture by file, and an atlas cell by file and column.
func texture_name(texture: Texture2D) -> String:
	if texture is AtlasTexture:
		return "%s@%d" % [texture.atlas.resource_path.get_file(), roundi(texture.region.position.x / texture.region.size.x)]
	return texture.resource_path.get_file()


func cards_state() -> Array:
	var out := []
	for glyph_name in ["MoveGlyph", "AttackGlyph", "DashGlyph", "BlockGlyph"]:
		var pair := card(glyph_name)
		if pair[0].visible:
			out.append(texture_name(pair[0].texture))
		else:
			out.append("[%s]" % pair[1].text)
	return out


func danny_lines() -> Array:
	var manager: Node = root.get_node("DialogueManager")
	var resource: Resource = manager.create_resource_from_text(FileAccess.get_file_as_string(DANNY_DIALOGUE))
	var lines := []
	var line = await manager.get_next_dialogue_line(resource, "start")
	while line != null:
		lines.append(line.text)
		line = await manager.get_next_dialogue_line(resource, line.next_id)
	return lines


func test_screens() -> void:
	log_p("-- the Controls screen follows the device live")
	await load_scene(CONTROLS_SCENE)
	var art := ["key_arrows.png", "key_q.png", "key_w.png", "key_shift.png"]
	var title: Label = current_scene.get_node("%MoveTitle")
	check(cards_state() == art, "keyboard on its defaults: the hand-drawn keys, as approved %s" % [cards_state()])
	check(title.text == "Classic arrow key movement", "and the approved title")
	var pad_art := ["pad_move.png", "pad_buttons_3x.png@0", "pad_buttons_3x.png@1", "pad_buttons_3x.png@4"]
	Input.joy_connection_changed.emit(0, true)
	await wait(1)
	check(cards_state() == pad_art, "plugging a pad in swaps all four cards on the spot: the stick and X, RB, LB %s" % [cards_state()])
	check(title.text == "Left stick or D-pad", "and the title (%s)" % title.text)
	Input.joy_connection_changed.emit(0, false)
	await wait(1)
	check(cards_state() == art and title.text == "Classic arrow key movement", "unplugging it swaps them back %s" % [cards_state()])
	tap_button(JOY_BUTTON_X)
	await wait(1)
	check(cards_state() == pad_art, "touching the pad swaps them %s" % [cards_state()])
	tap_key(KEY_Z)
	await wait(1)
	check(cards_state() == art, "touching the keyboard swaps them back")
	settings.rebind(&"punch", key_event(KEY_E, true))
	settings.rebind(&"move_up", key_event(KEY_W, true))
	await wait(1)
	check(cards_state() == ["[W/LEFT/DOWN/RIGHT]", "[E]", "[%s]" % settings.UNBOUND_LABEL, "key_shift.png"], "rebound keys are written on keys, the dash W lost is shown unbound %s" % [cards_state()])
	check(title.text == "Movement", "a rebound movement doesn't claim to be the arrow keys (%s)" % title.text)
	var dash_keycap: Label = card("DashGlyph")[1]
	check(dash_keycap.get_theme_color("font_color") == load("res://Scripts/ControlsArtLayout.gd").UNBOUND_COLOR, "unbound is drawn in the warning colour")
	settings.reset_to_defaults()
	await wait(1)
	check(cards_state() == art, "a reset puts the drawn keys back")
	var ready_button: Button = current_scene.get_node("%ReadyButton")
	root.get_node("DialogueManager").dialogue_ended.emit(null)
	await wait(1)
	# On a pad the training room takes that focus straight back off it, since ui_accept is also
	# punch; the `training` mode checks that, and the Arena #1 door is what a pad leaves through.
	check(focus_owner() == ready_button, "once Danny is done the ready button has focus, so Enter presses it (%s)" % focus_name())

	log_p("-- Danny names whatever the controls are")
	var imported: Resource = load(DANNY_DIALOGUE)
	if not imported.using_states.has("InputSettings"):
		log_p("note: the imported copy of the dialogue is older than its source; the open editor reimports it on its next scan")
	var lines := await danny_lines()
	log_p("keyboard: %s" % [lines])
	var text := " ".join(lines)
	check(lines.size() == 6 and not text.contains("{{"), "six lines, every token resolved")
	# Blocking is out of the game (PlayerDefense.BLOCKING_ENABLED), so nothing tells the player to hold the key.
	check(text.contains("ARROWS to move, Q punches, W dashes") and text.contains("TAP SHIFT") and not text.contains("HOLD SHIFT"), "on the keyboard: arrows, Q, W and Shift, tapped to parry and never held to block")
	check(text.contains("There's no blocking on this server"), "and it says outright that there is no blocking")
	# The finisher is mashed on its own keys in every fight, not attack and dash, so those are the ones it names.
	check(text.contains("Boss goes all dizzy? Follow the prompt to finish him: mash LEFT and RIGHT."), "and the finisher's mash on the arrows, behind the prompt")
	check(text.contains("Need out mid-fight? ESC pauses it"), "and the pause key")
	# The last line hands the room over rather than ending the screen: the dummy, the post that makes
	# it hit back, that nothing in here can kill you, and BOTH ways out, since on a pad the Ready
	# button can't hold focus (ui_accept is also punch) and the door is how pad players leave.
	check(text.contains("go warm up on that sparring bot") and text.contains("WALK INTO THE POST beside it"), "the hand-over line offers the dummy and names the post in capitals")
	# The two split-second reads the whole fight design rests on. Being the hardest thing in the room
	# to find would be exactly backwards, so his last line says them outright, on this device's keys.
	check(text.contains("red over its head means TAP SHIFT to parry") and text.contains("yellow means W straight through it"), "and spells out the red parry and the yellow dodge")
	check(text.contains("You CAN'T lose in here"), "and promises the player can't lose in there")
	check(text.contains("Hit I'm ready, or walk out the Arena #1 door"), "and names both ways out")
	Input.joy_connection_changed.emit(0, true)
	lines = await danny_lines()
	text = " ".join(lines)
	log_p("gamepad: %s" % [lines])
	var layout: GDScript = load("res://Scripts/ControlsArtLayout.gd")
	var a: String = layout.inline_glyph(0)
	var b: String = layout.inline_glyph(1)
	var lb: String = layout.inline_glyph(4)
	check(text.contains("LEFT STICK to move, %s punches, %s dashes" % [a, b]) and text.contains("TAP %s" % lb) and not text.contains("HOLD %s" % lb), "on a pad: the stick named, A, B and LB drawn inline")
	check(text.contains("Follow the prompt to finish him: mash %s and %s." % [lb, layout.inline_glyph(5)]), "and the finisher's mash on LB and RB")
	check(a.contains("pad_buttons_inline_3x.png") and b.contains("pad_buttons_inline_3x.png") and lb.contains("pad_buttons.png"), "the face buttons from the 11 px set, the bumper from the 32 px sheet")
	Input.joy_connection_changed.emit(0, false)
	settings.rebind(&"block", key_event(KEY_C, true))
	text = " ".join(await danny_lines())
	check(text.contains("TAP C") and not text.contains("HOLD C"), "and a rebind")
	settings.reset_to_defaults()

	log_p("-- a line with glyphs in it types out whole, in the real balloon")
	Input.joy_connection_changed.emit(0, true)
	await load_scene(CONTROLS_SCENE)
	var balloon: Node = null
	for i in 120:
		for child in current_scene.get_children():
			if "dialogue_label" in child:
				balloon = child
		if balloon != null and balloon.dialogue_label.text.contains("[img"):
			break
		await process_frame
	var typed: RichTextLabel = balloon.dialogue_label
	var spoken := [0]
	typed.spoke.connect(func(_letter: String, _index: int, _speed: float) -> void: spoken[0] += 1)
	typed.type_out()
	for i in 900:
		if not typed.is_typing:
			break
		await process_frame
	var total := typed.get_total_character_count()
	log_p("typed %d of %d characters, %d spoken, %d in the parsed text" % [typed.visible_characters, total, spoken[0], typed.get_parsed_text().length()])
	check(typed.text.contains("[img") and not typed.is_typing and typed.visible_characters == total, "it types to the end")
	check(spoken[0] == total and typed.get_parsed_text().length() == total, "one spoken letter per character, each glyph counting as one, so nothing drifts")
	Input.joy_connection_changed.emit(0, false)

	log_p("-- the intro's skip hint")
	await load_scene(INTRO_SCENE)
	var hint: Label = current_scene.get_node("HintLayer/SkipHint")
	check(hint.text == "ESC: skip" and hint.offset_left == -177.0, "keyboard: the approved hint in its approved box (%s, %.0f)" % [hint.text, hint.offset_left])
	Input.joy_connection_changed.emit(0, true)
	await wait(1)
	check(hint.text == "B: skip" and hint.offset_left > -177.0 and hint.offset_right == -21.0, "pad: B, in a box fitted to it on the same right edge (%.0f..%.0f)" % [hint.offset_left, hint.offset_right])
	tap_button(JOY_BUTTON_B)
	await wait(1)
	check(current_scene.leaving, "B skips the cutscene")
	Input.joy_connection_changed.emit(0, false)

	log_p("-- the main menu on a pad")
	await load_scene(MENU_SCENE)
	var start: Button = current_scene.get_node("StartGameButton")
	var controls: Button = current_scene.get_node("ControlsButton")
	var slider: HSlider = current_scene.get_node("VolumeSlider")
	check(focus_owner() == null, "nothing has focus while the menu fades in (%s)" % focus_name())
	# Enter rather than A: the device tracker follows every press, and the checks below are the
	# keyboard's.
	tap_key(KEY_ENTER)
	await wait(2)
	check(current_scene.scene_file_path == MENU_SCENE, "so an accept still held from the screen that led here presses nothing")
	await wait(40)
	check(focus_owner() == start, "then NEW GAME has it (%s)" % focus_name())
	check(controls.get_rect() == Rect2(156, 566, 480, 126) and current_scene.get_node("VolumeLabel").position.y == 716.0 and slider.get_rect() == Rect2(156, 766, 480, 54), "CONTROLS sits under NEW GAME and the volume moved down")
	check(start.get_theme_stylebox("focus") is StyleBoxEmpty, "on the keyboard the menu draws no focus, as approved")
	tap_key(KEY_DOWN)
	await wait(1)
	check(focus_owner() == controls, "down from NEW GAME -> CONTROLS (%s)" % focus_name())
	tap_button(JOY_BUTTON_DPAD_DOWN)
	await wait(1)
	check(focus_owner() == slider, "the d-pad -> VOLUME (%s)" % focus_name())
	check(start.get_theme_stylebox("focus") is StyleBoxFlat and slider.get_theme_stylebox("grabber_area_highlight").modulate_color != Color.WHITE, "on a pad the focus shows: a ring on the buttons, a tint on the slider")
	tap_button(JOY_BUTTON_DPAD_DOWN)
	await wait(1)
	# The INVINCIBLE toggle heads the boss select, and the fights come under it.
	check(focus_owner() is CheckBox, "and on down into the boss select, onto its INVINCIBLE toggle (%s)" % focus_name())
	tap_button(JOY_BUTTON_DPAD_DOWN)
	await wait(1)
	# Button -> its column -> the columns -> the rows -> the panel.
	var first_boss := focus_owner()
	var panel: Node = null
	if first_boss is Button and not (first_boss is CheckBox) and first_boss != start:
		panel = first_boss.get_parent().get_parent().get_parent().get_parent()
	check(panel is PanelContainer, "then onto the first fight (%s: %s)" % [focus_name(), first_boss.text if first_boss is Button else ""])
	tap_button(JOY_BUTTON_DPAD_UP)
	await wait(1)
	tap_button(JOY_BUTTON_DPAD_UP)
	await wait(1)
	check(focus_owner() == slider, "back up to VOLUME")
	send([axis_event(JOY_AXIS_LEFT_Y, -1.0)])
	send([axis_event(JOY_AXIS_LEFT_Y, 0.0)])
	await wait(1)
	check(focus_owner() == controls, "the stick -> CONTROLS (%s)" % focus_name())
	if panel is PanelContainer:
		check(panel.get_rect().end.y <= 1080.0 and panel.size.y <= 240.0 + 0.5, "the boss select still fits under it (%s)" % panel.get_rect())
	tap_button(JOY_BUTTON_A)
	check(await wait_for_scene(SETTINGS_SCENE), "A on CONTROLS opens the rebind screen")

	log_p("-- the victory and defeat buttons take focus once the screen is up")
	await load_scene(VICTORY_SCENE)
	check(focus_owner() == null, "victory: nothing has focus while it fades in (%s)" % focus_name())
	tap_button(JOY_BUTTON_A)
	await wait(2)
	check(current_scene.scene_file_path == VICTORY_SCENE, "so an A still being mashed as the fight ended presses nothing")
	await wait(40)
	check(focus_name() == "NextBossButton", "then NEXT BOSS has it (%s)" % focus_name())
	await load_scene(DEFEAT_SCENE)
	check(focus_owner() == null, "defeat: nothing while it fades in (%s)" % focus_name())
	tap_button(JOY_BUTTON_A)
	await wait(2)
	check(current_scene.scene_file_path == DEFEAT_SCENE, "and a mashed A presses nothing")
	await wait(40)
	check(focus_name() == "ReturnToMenuButton", "then RETURN TO MENU has it (%s)" % focus_name())
	tap_button(JOY_BUTTON_A)
	check(await wait_for_scene(MENU_SCENE), "and A on it goes back to the menu")


# ------------------------------------------------------------------ training

# The training room the Controls screen becomes once Danny is done: the sparring dummy is the real
# punch, the real finisher and the real defence, and the two things the room adds on top of them are
# the two that must never break.
#   The player cannot lose in here. PlayerScript._process fires FightOutro.finish_fight at zero
#   health, and FightOutro.PLAYER_PATH is hard-coded to "Arena/MainPlayer/CharacterBody2D", which
#   this scene does not have, so a death would end the room with a defeat screen and crash on the way
#   out. TrainingRoomScript floors the health at 1 from a lower process priority than the player's.
#   A pad punch must never start the fight. ui_accept carries JOY_BUTTON_A, which is also punch, so
#   a focused Ready button would launch Eric on every punch thrown at the dummy. On a pad the button
#   takes no focus and the Arena #1 door is the way out.
func test_training() -> void:
	await load_scene(CONTROLS_SCENE)
	var room: Node2D = current_scene.get_node("Room")
	var player: CharacterBody2D = current_scene.get_node("Room/MainPlayer/CharacterBody2D")
	var dummy: CharacterBody2D = current_scene.get_node("Room/TrainingDummy")
	var finisher: Node = player.get_node("Finisher")
	var prompt: Node2D = current_scene.get_node("Room/MainPlayer/CanvasLayer/FinisherPrompt")
	var ready_button: Button = current_scene.get_node("%ReadyButton")
	var cards: Control = current_scene.get_node("ScreenUI/Screen/Cards")

	log_p("-- the room opens when Danny finishes")
	check(player.is_talking, "the player is held while he talks")
	root.get_node("DialogueManager").dialogue_ended.emit(null)
	# The real balloon frees itself when the lines actually run out; this mode ends them by hand, so
	# it has to, or it sits there holding focus and eating presses meant for the room.
	var balloon := find_balloon()
	if balloon:
		balloon.free()
	await wait(3)
	check(room.room_open and not player.is_talking, "his last line hands the room over and frees the player")
	check(player.feel_v2, "on feel_v2, the feel every fight uses")
	check(player.dash_parry, "and on the dash parry, which the fight this room opens into turns on")
	check(not dummy.is_sparring(), "the dummy starts as a bag, so nobody is ambushed feeling out the movement")
	check(current_scene.get_node_or_null("Room/GroundFx") != null, "the ground layer is in the room, so the finisher doesn't build one in the lockers")
	check(ready_button.get_parent().name == "Persistent" and cards.get_parent().name == "Screen", "the button sits outside the card wall, in the group nothing fades")

	log_p("-- the cards get out of the way while they practise, and the button never does")
	check(is_equal_approx(drawn_alpha(cards), 1.0), "they are up when the room opens (%.2f)" % drawn_alpha(cards))
	send([key_event(KEY_DOWN, true)])
	var button_low := 1.0
	for i in 140:
		button_low = minf(button_low, drawn_alpha(ready_button))
		await process_frame
	log_p("held DOWN for 140 frames: cards %.2f, button %.2f" % [drawn_alpha(cards), drawn_alpha(ready_button)])
	check(drawn_alpha(cards) < 0.2, "a bout of practice takes them down (%.2f)" % drawn_alpha(cards))
	send([key_event(KEY_DOWN, false)])
	for i in 110:
		button_low = minf(button_low, drawn_alpha(ready_button))
		await process_frame
	check(is_equal_approx(drawn_alpha(cards), 1.0), "stopping brings them back (%.2f)" % drawn_alpha(cards))
	check(is_equal_approx(button_low, 1.0), "and the Ready button held full alpha throughout (lowest %.2f)" % button_low)

	log_p("-- three punches daze it")
	await place_under(player, dummy.get_node("Hurtbox"))
	await wait(6)
	for i in 3:
		await swing_on(player, false)
		if i < 2:
			await wait(6)
	var dazed := false
	for i in 180:
		dazed = finisher.phase == 2 and finisher.prompt_visible
		if dazed:
			break
		await process_frame
	check(dazed, "the charged punch of the combo dazed it")
	check(finisher.tiered and prompt.tiered_built, "and the mash is the tiered one, so the three-bar meter is what comes up")
	check(prompt.actions == [&"mash_left", &"mash_right"], "on the finisher's own pair, as in Eric's fight %s" % [prompt.actions])
	# The measured reason: the finisher's zoom throws the dummy to screen y 127, behind a card. The
	# fade has to land inside the settle beat, because the freeze stops the room mid-fade otherwise.
	log_p("at the daze: cards %.2f, button %.2f" % [drawn_alpha(cards), drawn_alpha(ready_button)])
	check(drawn_alpha(cards) <= 0.05, "the finisher takes the cards right out, so the juggle is not drawn behind one (%.2f)" % drawn_alpha(cards))
	check(is_equal_approx(drawn_alpha(ready_button), 1.0), "and it still leaves the Ready button alone (%.2f)" % drawn_alpha(ready_button))
	log_p("waiting the mash out, so the fizzle unfreezes the room")
	for i in 400:
		if finisher.phase == 0:
			break
		await process_frame
	check(finisher.phase == 0, "an unmashed prompt fizzles and hands the room back")

	log_p("-- the player cannot die in here")
	var lowest: int = player.playerHealth
	var outro_seen := false
	for i in 90:
		player.playerHealth = 0
		await process_frame
		lowest = mini(lowest, player.playerHealth)
		outro_seen = outro_seen or root.has_node(^"FightOutro")
	check(lowest >= 1, "health driven to 0 every frame is floored at 1 before the death check reads it (lowest %d)" % lowest)
	check(not outro_seen, "so no outro is ever started")
	check(current_scene != null and current_scene.scene_file_path == CONTROLS_SCENE, "and the room is still the scene")

	log_p("-- it hits back once it is sparring")
	dummy.set_sparring(true)
	var swung := false
	for i in 240:
		swung = swung or dummy.phase == 2
		await process_frame
	check(swung, "standing next to it, it winds up and swings")

	log_p("-- a pad punch never starts the fight, and Y always does")
	Input.joy_connection_changed.emit(0, true)
	await wait(2)
	check(ready_button.focus_mode == Control.FOCUS_NONE and not ready_button.has_focus(), "the Ready button drops its focus on a pad and can't take it back (focus is on %s)" % focus_name())
	# Column 3 of pad_buttons_3x.png, 14 cells of 96 px, written out rather than read back from
	# InputSettings so a wrong frame table can't pass by agreeing with itself.
	var glyph: AtlasTexture = ready_button.icon
	check(glyph != null and glyph.region.position == Vector2(288, 0), "and wears the Y glyph instead, so a pad player can see the way out %s" % [glyph.region if glyph else "<none>"])
	for i in 8:
		tap_button(JOY_BUTTON_A)
		await wait(4)
	check(current_scene != null and current_scene.scene_file_path == CONTROLS_SCENE, "eight A presses punched the dummy and left the room alone")
	Input.joy_connection_changed.emit(0, false)
	await wait(2)
	check(focus_owner() == ready_button and ready_button.icon == null, "back on the keyboard it takes its focus back and drops the glyph, Enter being the only accept there (%s)" % focus_name())
	Input.joy_connection_changed.emit(0, true)
	await wait(2)
	tap_button(JOY_BUTTON_Y)
	var first_fight: String = root.get_node("GameProgress").first_fight()
	check(await wait_for_scene(first_fight, 120), "Y confirms, straight into the first fight (%s)" % first_fight.get_file())

	log_p("-- and the door is still a way out as well")
	# The pad stays plugged in for the rest of the mode. Unplugging the last one INSIDE a fight opens
	# the pause screen (the pause_input mode's rule), and a paused tree survives the scene change:
	# the room would load with its physics stopped and nothing would ever enter the doorway.
	await load_scene(CONTROLS_SCENE)
	room = current_scene.get_node("Room")
	player = current_scene.get_node("Room/MainPlayer/CharacterBody2D")
	root.get_node("DialogueManager").dialogue_ended.emit(null)
	balloon = find_balloon()
	if balloon:
		balloon.free()
	await wait(3)
	player.global_position = Vector2(1797, 752)
	check(await wait_for_scene(first_fight, 180), "standing in the Arena #1 doorway for the dwell goes through to the first fight too")


# ------------------------------------------------------------------ rebind_screen

# The keycap's text, or the glyph's column when the drawn glyph is showing instead.
func cell_text(gamepad: bool, action: StringName) -> String:
	var glyph: TextureRect = current_scene.glyphs[gamepad][action]
	if glyph.visible:
		return "glyph@%d" % roundi(glyph.texture.region.position.x / glyph.texture.region.size.x)
	return current_scene.keycaps[gamepad][action].text


func open_cell(gamepad: bool, action: StringName) -> void:
	current_scene.cells[gamepad][action].grab_focus()
	if gamepad:
		tap_button(JOY_BUTTON_A)
	else:
		tap_key(KEY_ENTER)
	await wait(2)


func test_rebind_screen() -> void:
	await load_scene(SETTINGS_SCENE)
	var screen: Control = current_scene
	var table: GridContainer = screen.get_node("%Table")
	check(table.get_child_count() == 3 + 7 * 3, "a header and seven rows of three (%d cells)" % table.get_child_count())
	check(focus_owner() == screen.cells[false][&"move_up"], "the first cell has focus (%s)" % focus_name())
	var fixed_ok := true
	for action in settings.MOVE_ACTIONS:
		var row: int = settings.ACTIONS.find(action) + 1
		var pad_cell: Control = table.get_child(row * 3 + 2)
		fixed_ok = fixed_ok and pad_cell is Label and pad_cell.text == "LEFT STICK / D-PAD" and pad_cell.focus_mode == Control.FOCUS_NONE
		fixed_ok = fixed_ok and not screen.cells[true].has(action)
	check(fixed_ok, "movement's pad cells are a fixed, unfocusable LEFT STICK / D-PAD")
	check([cell_text(false, &"punch"), cell_text(true, &"punch"), cell_text(false, &"move_left"), cell_text(true, &"block")] == ["Q", "glyph@0", "LEFT", "glyph@4"], "cells show the bindings: keys by name, pad buttons by glyph")
	var notice: Label = screen.get_node("%Notice")

	log_p("-- Enter opens a keyboard cell without binding Enter")
	await open_cell(false, &"punch")
	check(screen.listening and screen.listen_action == &"punch" and not screen.listen_gamepad, "listening")
	check(settings.bindings[&"punch"]["key"] == KEY_Q, "the Enter that opened it is not the binding")
	check(cell_text(false, &"punch") == "PRESS A KEY", "the cell asks for a key")
	tap_key(KEY_E)
	await wait(1)
	check(not screen.listening and settings.bindings[&"punch"]["key"] == KEY_E and cell_text(false, &"punch") == "E", "E is bound and shown")
	check(saved_bindings()[&"punch"]["key"] == KEY_E, "and saved on the spot")

	log_p("-- A opens a pad cell without binding A")
	await open_cell(true, &"block")
	check(screen.listening and screen.listen_gamepad, "listening")
	check(settings.bindings[&"block"]["pad_button"] == JOY_BUTTON_LEFT_SHOULDER and settings.bindings[&"punch"]["pad_button"] == JOY_BUTTON_A, "the A that opened block's cell is not its binding, and attack keeps A")
	check(cell_text(true, &"block") == "PRESS A BUTTON" and screen.get_node("%Hint").text == screen.HINT_LISTEN_BUTTON, "the cell asks for a button, and says how to keep it or cancel")
	tap_button(JOY_BUTTON_Y)
	await wait(1)
	check(settings.bindings[&"block"]["pad_button"] == JOY_BUTTON_Y and cell_text(true, &"block") == "glyph@3", "Y is bound and shown (%s)" % cell_text(true, &"block"))

	log_p("-- B binds on a pad cell, though B is also cancel")
	await open_cell(true, &"block")
	tap_button(JOY_BUTTON_B)
	await wait(1)
	check(not screen.listening and settings.bindings[&"block"]["pad_button"] == JOY_BUTTON_B and current_scene == screen, "B is bound to block, and nothing backed out")
	check(settings.bindings[&"dodge"]["pad_button"] == -1 and cell_text(true, &"dodge") == settings.UNBOUND_LABEL, "dash, which had B, is unbound")
	check(notice.text == "B WAS ON DASH, WHICH IS NOW UNBOUND", "and the notice says so (%s)" % notice.text)
	await open_cell(true, &"dodge")
	tap_button(JOY_BUTTON_B)
	await wait(1)
	check(settings.bindings[&"dodge"]["pad_button"] == JOY_BUTTON_B and cell_text(true, &"dodge") == "glyph@1", "and B goes back on dash from the pad alone")

	log_p("-- pressing the button a cell already has keeps it")
	await open_cell(true, &"punch")
	var before: Dictionary = settings.bindings.duplicate(true)
	tap_button(JOY_BUTTON_A)
	await wait(1)
	check(not screen.listening and settings.bindings == before, "attack stays on A and nothing else moves: the way out of a cell with only a pad")

	log_p("-- sticks and the d-pad are refused, a trigger is taken")
	await open_cell(true, &"dodge")
	var dodge_cell: Button = screen.cells[true][&"dodge"]
	send([axis_event(JOY_AXIS_LEFT_X, 0.9)])
	send([axis_event(JOY_AXIS_LEFT_X, 0.0)])
	await wait(1)
	check(screen.listening and settings.bindings[&"dodge"]["pad_button"] == JOY_BUTTON_B, "a stick push is refused")
	check(notice.text == screen.NOTICE_STICK_OR_DPAD, "and says why")
	tap_button(JOY_BUTTON_DPAD_UP)
	await wait(1)
	check(screen.listening and settings.bindings[&"dodge"]["pad_button"] == JOY_BUTTON_B and focus_owner() == dodge_cell, "so is the d-pad, and it moves no focus while listening")
	send([axis_event(JOY_AXIS_TRIGGER_RIGHT, 0.3)])
	await wait(1)
	check(screen.listening, "a trigger barely touched isn't a press")
	send([axis_event(JOY_AXIS_TRIGGER_RIGHT, 0.8)])
	send([axis_event(JOY_AXIS_TRIGGER_RIGHT, 0.0)])
	await wait(1)
	check(not screen.listening and settings.bindings[&"dodge"]["pad_axis"] == JOY_AXIS_TRIGGER_RIGHT and cell_text(true, &"dodge") == "glyph@7", "a trigger pulled in is bound, and drawn as RT (%s)" % cell_text(true, &"dodge"))

	log_p("-- cancelling")
	before = settings.bindings.duplicate(true)
	await open_cell(true, &"punch")
	tap_key(KEY_ESCAPE)
	await wait(1)
	check(not screen.listening and settings.bindings == before and current_scene == screen, "Esc cancels a pad cell, and stays on the screen")
	await open_cell(false, &"block")
	tap_button(JOY_BUTTON_B)
	await wait(1)
	check(not screen.listening and settings.bindings == before and current_scene == screen, "B cancels a key cell, and stays on the screen")
	await open_cell(false, &"block")
	tap_key(KEY_ESCAPE)
	await wait(1)
	check(not screen.listening and settings.bindings == before and current_scene == screen, "and so does Esc")
	check(cell_text(false, &"block") == "SHIFT", "the cell shows its binding again")

	log_p("-- a conflict")
	await open_cell(false, &"dodge")
	tap_key(KEY_E)
	await wait(1)
	check(settings.bindings[&"dodge"]["key"] == KEY_E and settings.bindings[&"punch"]["key"] == -1, "E moved from attack to dash")
	check(cell_text(false, &"punch") == settings.UNBOUND_LABEL and screen.keycaps[false][&"punch"].get_theme_color("font_color") == load("res://Scripts/ControlsArtLayout.gd").UNBOUND_COLOR, "attack's key cell shows unbound, in the warning colour")
	check(notice.text == "E WAS ON ATTACK, WHICH IS NOW UNBOUND" and notice.modulate.a == 1.0, "the notice says so (%s)" % notice.text)
	await wait(roundi((screen.NOTICE_HOLD + screen.NOTICE_FADE) * 60.0) + 10)
	check(notice.modulate.a == 0.0, "and fades")

	log_p("-- focus")
	screen.cells[false][&"move_up"].grab_focus()
	tap_key(KEY_RIGHT)
	await wait(1)
	check(focus_owner() == screen.cells[false][&"move_up"], "right from a movement row stays put (%s)" % focus_name())
	screen.cells[false][&"punch"].grab_focus()
	tap_key(KEY_RIGHT)
	await wait(1)
	check(focus_owner() == screen.cells[true][&"punch"], "right from attack reaches its pad cell (%s)" % focus_name())
	check(screen.cells[true][&"punch"].get_theme_stylebox("focus") is StyleBoxFlat, "focus is drawn")

	log_p("-- reset")
	var reset: Button = screen.get_node("%ResetButton")
	reset.grab_focus()
	tap_key(KEY_ENTER)
	await wait(1)
	check(settings.bindings == defaults() and cell_text(false, &"punch") == "Q" and cell_text(true, &"dodge") == "glyph@1", "everything is back and repainted")
	check(notice.text == screen.NOTICE_RESET, "and it says so")
	check(saved_bindings() == defaults(), "and it's saved")

	log_p("-- the hint follows the device")
	tap_key(KEY_Z)
	await wait(1)
	check(screen.get_node("%Hint").text == screen.HINT_KEYBOARD, "keyboard hint")
	tap_button(JOY_BUTTON_Y)
	await wait(1)
	check(screen.get_node("%Hint").text == screen.HINT_GAMEPAD, "pad hint")

	log_p("-- back")
	tap_button(JOY_BUTTON_B)
	check(await wait_for_scene(MENU_SCENE), "B, when nothing is listening, goes back to the menu")


# ------------------------------------------------------------------ handoffs

func punching(player: CharacterBody2D) -> bool:
	return player.state_machine.current_state.name == "Punching"


# A is attack and B is dash, and they are also ui_accept and ui_cancel, which the dialogue balloon
# reads: nothing may carry from one to the other.
func test_handoffs() -> void:
	Input.joy_connection_changed.emit(0, true)
	await load_scene(ERIC_FIGHT)
	# A debugging aid another coder sometimes leaves in this scene; see the defence suite.
	var scratch := current_scene.get_node_or_null("ScratchEricDriver")
	if scratch:
		scratch.free()
	await skip_entrance()
	var player: CharacterBody2D = current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
	player.playerHealth = 100
	var ended := [false]
	root.get_node("DialogueManager").dialogue_ended.connect(func(_resource: Resource) -> void: ended[0] = true)
	var balloon: Node = null
	for i in 180:
		for child in current_scene.get_children():
			if "dialogue_label" in child:
				balloon = child
		if balloon != null:
			break
		await process_frame
	check(balloon != null and player.is_talking, "the pre-fight dialogue is up, and the player is held for it")

	log_p("-- reading the dialogue with the pad")
	var dash_frame: int = player.last_dodge_physics_frame
	var punched := false
	var presses := 0
	for i in 4000:
		if ended[0]:
			break
		punched = punched or punching(player)
		if i % 6 == 0 and is_instance_valid(balloon):
			# B skips a line still typing, A moves on from one that has finished: how a pad reads it.
			tap_button(JOY_BUTTON_B if balloon.dialogue_label.is_typing else JOY_BUTTON_A)
			presses += 1
		await process_frame
	check(ended[0], "A and B read it to the end (%d presses)" % presses)
	for i in 12:
		punched = punched or punching(player)
		await process_frame
	check(not punched, "no A that read it threw a punch, the one that closed the last line included")
	check(player.last_dodge_physics_frame == dash_frame, "no B that skipped its typing dashed")
	# The lines hand over to the VS card, which holds the player itself until it is done.
	var card: Node = current_scene.get_node("Arena/VsCard")
	check(card.is_playing() and player.is_talking, "the lines handed over to the VS card, which holds the player on")
	await skip_vs_card()
	check(not player.is_talking and focus_owner() == null, "the fight has the player back, and nothing on screen has focus for A to press (%s)" % focus_name())

	# Eric is parked for the rest: his attacks would take the player's turn, and they are not what is
	# under test.
	var boss: Node = current_scene.get_node("Arena/EricBossScene/CharacterBody2D")
	boss.state_machine.set_process(false)
	boss.state_machine.set_physics_process(false)
	for timer in boss.find_children("*", "Timer", true, false):
		timer.stop()

	log_p("-- in the fight, A attacks and B dashes, and that is all")
	await wait(5)
	tap_button(JOY_BUTTON_A)
	var swung := false
	for i in 20:
		swung = swung or punching(player)
		await process_frame
	check(swung, "A throws a punch")
	await wait(30)
	dash_frame = player.last_dodge_physics_frame
	for i in 5:
		tap_button(JOY_BUTTON_B)
		await wait(20)
	check(player.last_dodge_physics_frame != dash_frame, "B dashes")
	check(current_scene.scene_file_path == ERIC_FIGHT and not paused and current_scene.can_process(), "and five of them never paused, quit or backed out of the fight")
	check(focus_owner() == null, "nor gave anything focus")
	Input.joy_connection_changed.emit(0, false)


# ------------------------------------------------------------------ outro_mash

# A punch thrown with A on the pad or Q on the keyboard, waited out.
func swing_on(player: CharacterBody2D, pad: bool) -> void:
	if pad:
		tap_button(JOY_BUTTON_A)
	else:
		tap_key(KEY_Q)
	for i in 10:
		await process_frame
		if punching(player):
			break
	while punching(player):
		await process_frame
	await wait(3)


# The player's punch box on the bottom edge of `area`'s shape, as the defence suite stands them.
# Placed twice, because moving them re-aims the facing and the facing is what picks the punch box the
# placement was measured from. One pass was enough while the player drew at 2x and ended up beside the
# dummy either way; at 3x the first pass leaves him below it, facing up, with the up punch's box - which
# is drawn off to his left - beside the dummy's narrow hurtbox rather than on it.
func place_under(player: CharacterBody2D, area: Area2D) -> void:
	var shape: CollisionShape2D = area.get_node("CollisionShape2D")
	var half: Vector2 = shape.shape.size * shape.global_scale.abs() / 2.0
	var hitbox: CollisionShape2D = player.get_node("Hitbox/CollisionShape2D")
	for i in 2:
		var reach: Vector2 = hitbox.global_position - player.global_position
		player.global_position = Vector2(shape.global_position.x - reach.x, shape.global_position.y + half.y - reach.y - 4.0)
		await physics_frame
		await physics_frame


func find_balloon() -> Node:
	for child in current_scene.get_children():
		if "dialogue_label" in child:
			return child
	return null


# How a pad player ends a fight in a hurry: A punches Eric dizzy, the finisher's own pair (LB and RB,
# his fight being on feel_v2) mashes the uppercut into the kill, and A goes on being mashed into his
# outro, where it is also the dialogue's accept. Every line must still show for at least 1.2 s. Real
# time (--max-fps 60): the finisher's presses and the outro's lock are both on the wall clock. press=
# sets what the outro gets:
#   a           A mashed. A can't skip the typing, so each line types out and waits out the lock.
#   ab          A and B mashed. B skips the typing, and a skipped line must stay up for the lock again.
#   deliberate  per line, one skip too early, which must be eaten, then one press after the lock,
#               which must advance at once: the pad on the first line, the keyboard on the second.
func test_outro_mash() -> void:
	Input.joy_connection_changed.emit(0, true)
	await load_scene(ERIC_FIGHT)
	# A debugging aid another coder sometimes leaves in this scene; see the defence suite.
	var scratch := current_scene.get_node_or_null("ScratchEricDriver")
	if scratch:
		scratch.free()
	# His pre-fight lines are the handoffs mode's business: off with them, as the defence suite does.
	await skip_entrance()
	for child in current_scene.get_children():
		if child is CanvasLayer:
			child.queue_free()
	var manager: Node = root.get_node("DialogueManager")
	manager.dialogue_ended.emit(null)
	await wait(2)
	await skip_vs_card()
	var player: CharacterBody2D = current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
	player.playerHealth = 100
	var boss: Node = current_scene.get_node("Arena/EricBossScene/CharacterBody2D")
	var sm: Node = boss.state_machine
	sm.post_dialogue_pre_fight_timer.stop()
	var finisher: Node = player.get_node("Finisher")
	# The requirement, not FightOutro's constant, so a lock lowered again can't pass by agreeing.
	var lock_ms := 1200
	# The frame a change is seen on can be one late at either end of a measurement.
	var frame_ms := 20

	log_p("-- A punches him dizzy")
	sm.rest_timer.stop()
	sm.downed_state_timer.start(60.0)
	sm.on_child_transition(sm.current_state, "Downed")
	await wait(5)
	await place_under(player, boss.get_node("Hurtbox"))
	await wait(6)
	for i in 3:
		await swing_on(player, true)
		if i < 2:
			await wait(6)
	var dazed := false
	for i in 120:
		dazed = finisher.phase == 2 and finisher.prompt_visible
		if dazed:
			break
		await process_frame
	check(dazed, "dazed, on the pad alone")
	boss.boss_health = 2

	log_p("-- the finisher's pair mashes the uppercut into the kill, and the outro gets: %s" % press)
	var ended := [false]
	manager.dialogue_ended.connect(func(_resource: Resource) -> void: ended[0] = true)
	var lines := []
	var entry := {}
	var shown_line: Object = null
	var balloon: Node = null
	var was_visible := 0
	var step := 0
	var uppercut := false
	for i in 60 * 40:
		if ended[0]:
			break
		var now := Time.get_ticks_msec()
		if player.fight_over and (balloon == null or not is_instance_valid(balloon)):
			balloon = find_balloon()
		var label: RichTextLabel = balloon.dialogue_label if balloon != null and is_instance_valid(balloon) else null
		if label != null and balloon.dialogue_line != null and balloon.dialogue_line != shown_line:
			if not entry.is_empty():
				entry.gone = now
			shown_line = balloon.dialogue_line
			entry = {"text": shown_line.text, "shown": now, "skipped": -1, "gone": -1, "early": "", "late_at": -1}
			lines.append(entry)
			was_visible = 0
		if label != null and not entry.is_empty() and press == "ab":
			var total := label.get_total_character_count()
			# A skip shows the rest of the line in one frame; typing shows a letter or two, a few more
			# on a slow frame.
			if entry.skipped < 0 and label.visible_characters == total and was_visible < total - 6:
				entry.skipped = now
			was_visible = label.visible_characters
		uppercut = uppercut or finisher.phase == 4
		if not player.fight_over or press != "deliberate":
			if i % 4 == 0:
				if finisher.phase == 2 or finisher.phase == 3:
					# The finisher's own pair: LB and RB in Eric's fight, on feel_v2.
					tap_button(PAD_MASH[finisher.mash_actions()[step % 2]])
				else:
					var use_b: bool = step % 2 == 1 and press == "ab"
					tap_button(JOY_BUTTON_B if use_b else JOY_BUTTON_A)
				step += 1
		elif label != null and not entry.is_empty():
			var keyboard := lines.size() == 2
			if entry.early.is_empty() and now - entry.shown >= 500:
				# The typing skip, well inside the lock: Esc on the keyboard, B on the pad.
				if keyboard:
					tap_key(KEY_ESCAPE)
				else:
					tap_button(JOY_BUTTON_B)
				entry.early = "sent"
			elif entry.early == "sent":
				entry.early = "eaten" if label.is_typing else "skipped"
			elif entry.late_at < 0 and not label.is_typing and now - entry.shown >= lock_ms + 100:
				if keyboard:
					tap_key(KEY_ENTER)
				else:
					tap_button(JOY_BUTTON_A)
				entry.late_at = now
		await process_frame
	if not entry.is_empty() and entry.gone < 0:
		entry.gone = Time.get_ticks_msec()
	var outro: Node = root.get_node_or_null("FightOutro")
	check(uppercut and outro != null and outro.player_won, "the uppercut killed him, and the fight is won")
	check(ended[0], "the outro played to its end")

	var texts := lines.map(func(e: Dictionary) -> String: return e.text)
	log_p("outro lines: %s" % [texts])
	check(texts == ["No... the White Knight, felled by a filthy conservative?", "This isn't over. The mods will hear about this!"], "both of his lines came up, in order")
	for e in lines:
		log_p("  up %d ms%s: %s" % [e.gone - e.shown, (", typing skipped at %d ms, then up %d ms more" % [e.skipped - e.shown, e.gone - e.skipped]) if e.skipped >= 0 else "", e.text])
		check(e.gone - e.shown >= lock_ms - frame_ms, "on screen at least %d ms (%d)" % [lock_ms, e.gone - e.shown])
		if e.skipped >= 0:
			check(e.skipped - e.shown >= lock_ms - frame_ms, "its typing couldn't be skipped before then (%d)" % [e.skipped - e.shown])
			check(e.gone - e.skipped >= lock_ms - frame_ms, "and once skipped, the whole line stayed up that long again (%d)" % [e.gone - e.skipped])
	match press:
		"ab":
			check(lines.any(func(e: Dictionary) -> bool: return e.skipped >= 0), "B did skip typing, so the skip's own wait was tried")
		"deliberate":
			for e in lines:
				var device := "keyboard" if e == lines[1] else "pad"
				check(e.early == "eaten", "%s: the skip at half a second was eaten, the line still typing (%s)" % [device, e.early])
				check(e.late_at >= 0 and e.gone - e.late_at <= 3 * frame_ms, "%s: the press after the lock moved on at once (%d ms)" % [device, e.gone - e.late_at])
	Input.joy_connection_changed.emit(0, false)


# ------------------------------------------------------------------ eric_mash

func held(player: CharacterBody2D, defense: Node) -> bool:
	return defense.guard_up or player.state_machine.current_state.name == "Blocking"


# Eric's fight mashes the finisher on its own pair (PlayerFinisher.mash_actions, on player.feel_v2):
# the arrows on a keyboard, LB and RB on a pad, which movement and the guard share. Every press is a
# real event, and the proof is that nothing but the meter hears them: the player never moves, the
# guard never goes up and no block reaches the defence to credit a parry, during the mash or while the
# last key is still held after it. Real time (--max-fps 60), as the mash is. device= keyboard | pad.
func test_eric_mash() -> void:
	var pad := mash_device == "pad"
	if pad:
		Input.joy_connection_changed.emit(0, true)
	await load_scene(ERIC_FIGHT)
	# A debugging aid another coder sometimes leaves in this scene; see the defence suite.
	var scratch := current_scene.get_node_or_null("ScratchEricDriver")
	if scratch:
		scratch.free()
	# His pre-fight lines are the handoffs mode's business: off with them, as the defence suite does.
	await skip_entrance()
	for child in current_scene.get_children():
		if child is CanvasLayer:
			child.queue_free()
	root.get_node("DialogueManager").dialogue_ended.emit(null)
	await wait(2)
	await skip_vs_card()
	var player: CharacterBody2D = current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
	player.playerHealth = 100
	var boss: Node = current_scene.get_node("Arena/EricBossScene/CharacterBody2D")
	var sm: Node = boss.state_machine
	sm.post_dialogue_pre_fight_timer.stop()
	var finisher: Node = player.get_node("Finisher")
	var defense: Node = player.get_node("Defense")
	var prompt: Node2D = current_scene.get_node("Arena/MainPlayer/CanvasLayer/FinisherPrompt")
	var left_press: Callable = tap_button.bind(JOY_BUTTON_LEFT_SHOULDER) if pad else tap_key.bind(KEY_LEFT)
	var right_press: Callable = tap_button.bind(JOY_BUTTON_RIGHT_SHOULDER) if pad else tap_key.bind(KEY_RIGHT)
	var credited := [0]
	defense.block_pressed.connect(func(_credited: bool) -> void: credited[0] += 1)
	check(player.feel_v2 and finisher.mash_actions() == [&"mash_left", &"mash_right"], "the fight is on feel_v2, so it mashes mash_left and mash_right")

	log_p("-- dazed with %s" % ("A" if pad else "Q"))
	sm.rest_timer.stop()
	sm.downed_state_timer.start(60.0)
	sm.on_child_transition(sm.current_state, "Downed")
	await wait(5)
	await place_under(player, boss.get_node("Hurtbox"))
	await wait(6)
	for i in 3:
		await swing_on(player, pad)
		if i < 2:
			await wait(6)
	var dazed := false
	for i in 120:
		dazed = finisher.phase == 2 and finisher.prompt_visible
		if dazed:
			break
		await process_frame
	check(dazed, "dazed")
	# The punches took some off him; topped up, so the uppercut leaves the fight going for the checks after it.
	boss.boss_health = boss.max_health
	await wait(2)

	log_p("-- the prompt")
	check(prompt.actions == [&"mash_left", &"mash_right"] and prompt.gamepad_keys == pad, "built for the mash's own pair, on this device")
	var left_key: Sprite2D = prompt.keys[&"mash_left"]
	var right_key: Sprite2D = prompt.keys[&"mash_right"]
	if pad:
		check(left_key.texture.resource_path.ends_with("pad_buttons_3x.png") and [left_key.frame % 14, right_key.frame % 14] == [4, 5], "LB and RB, off the pad sheet (%d, %d)" % [left_key.frame, right_key.frame])
	else:
		check([left_key.texture.resource_path.get_file(), right_key.texture.resource_path.get_file()] == ["qte_key_left_3x.png", "qte_key_right_3x.png"], "the left and right arrow keys")
	var lit_frame := 14 if pad else 1
	var lit := [false, false]
	for i in 20:
		lit[0] = lit[0] or left_key.frame >= lit_frame
		lit[1] = lit[1] or right_key.frame >= lit_frame
		await process_frame
	check(lit[0] and lit[1], "lighting up in turn")

	log_p("-- attack and dash don't fill it")
	if pad:
		tap_button(JOY_BUTTON_A)
		await wait(4)
		tap_button(JOY_BUTTON_B)
	else:
		tap_key(KEY_Q)
		await wait(4)
		tap_key(KEY_W)
	await wait(4)
	check(finisher.meter == 0.0 and finisher.phase == 2, "the meter hasn't moved (%.3f)" % finisher.meter)

	log_p("-- mashed to the uppercut")
	var anchor := player.global_position
	var drift := 0.0
	var guarded := false
	var health: int = boss.boss_health
	var presses := 0
	var frames := 0
	while finisher.phase == 2 or finisher.phase == 3:
		if frames % 4 == 0:
			(left_press if presses % 2 == 0 else right_press).call()
			presses += 1
		frames += 1
		drift = maxf(drift, player.global_position.distance_to(anchor))
		guarded = guarded or held(player, defense)
		await process_frame
	check(finisher.phase == 4, "the meter filled in %d presses and the uppercut is off" % presses)
	# Held through the uppercut and past its end, as a hand comes off a mash.
	if pad:
		send([button_event(JOY_BUTTON_LEFT_SHOULDER, true)])
	else:
		send([key_event(KEY_LEFT, true)])
	while finisher.phase != 0:
		drift = maxf(drift, player.global_position.distance_to(anchor))
		guarded = guarded or held(player, defense)
		await process_frame
	check(boss.boss_health < health, "it lands (%d -> %d)" % [health, boss.boss_health])
	check(drift < 0.5, "the player never moved (%.2f px)" % drift)
	check(not guarded and credited[0] == 0, "no guard went up, and no block reached the defence to credit a parry")

	# Eric is parked from here: his next attack would move the player, and it isn't under test.
	sm.set_process(false)
	sm.set_physics_process(false)
	for timer in boss.find_children("*", "Timer", true, false):
		timer.stop()

	log_p("-- right after, %s still held" % ("LB" if pad else "the left arrow"))
	check(finisher.is_mash_latched(), "the release latch is on")
	anchor = player.global_position
	drift = 0.0
	var walked := false
	for i in 30:
		drift = maxf(drift, player.global_position.distance_to(anchor))
		walked = walked or player.state_machine.current_state.name == "Walking"
		guarded = guarded or held(player, defense)
		await process_frame
	check(drift < 0.5 and not walked, "half a second on, it hasn't walked the player (%.2f px)" % drift)
	check(not guarded and credited[0] == 0, "or raised the guard")
	if pad:
		send([button_event(JOY_BUTTON_LEFT_SHOULDER, false)])
		await wait(1)
		check(not finisher.is_mash_latched(), "letting go ends it at once")
		send([button_event(JOY_BUTTON_LEFT_SHOULDER, true)])
		var up := false
		for i in 10:
			up = up or (defense.guard_up and player.state_machine.current_state.name == "Blocking")
			await process_frame
		check(up and credited[0] == 1, "and a fresh LB raises the guard, reaching the defence as a press (%d)" % credited[0])
		send([button_event(JOY_BUTTON_LEFT_SHOULDER, false)])
	else:
		for i in 60:
			await process_frame
		check(not finisher.is_mash_latched(), "at a second it lets go, key held or not")
		check(player.global_position.x < anchor.x - 10.0, "and the arrow still held walks the player at last (%.0f px)" % (anchor.x - player.global_position.x))
		send([key_event(KEY_LEFT, false)])

		log_p("-- the prompt still swaps with the device")
		Input.joy_connection_changed.emit(0, true)
		await wait(1)
		check(prompt.gamepad_keys and prompt.actions == [&"mash_left", &"mash_right"] and prompt.keys[&"mash_left"].texture.resource_path.ends_with("pad_buttons_3x.png"), "plugging a pad in swaps it to LB and RB")
		Input.joy_connection_changed.emit(0, false)
		await wait(1)
		check(not prompt.gamepad_keys and prompt.keys[&"mash_left"].texture.resource_path.ends_with("qte_key_left_3x.png"), "and back to the arrows")
	if pad:
		Input.joy_connection_changed.emit(0, false)


# ------------------------------------------------------------------ the pause screen


func pause_menu() -> Node:
	return current_scene.get_node("Arena/PauseMenu")


# Eric's fight with the pre-fight dialogue cleared and Eric parked: what is under test here is the
# pause screen's own input, not his turn.
func load_quiet_fight() -> void:
	await load_scene(ERIC_FIGHT)
	var scratch := current_scene.get_node_or_null("ScratchEricDriver")
	if scratch:
		scratch.free()
	await skip_entrance()
	# The balloon is a CanvasLayer under the fight's root; the pause screen lives under Arena.
	for child in current_scene.get_children():
		if child is CanvasLayer:
			child.queue_free()
	root.get_node("DialogueManager").dialogue_ended.emit(null)
	# Before his timers are stopped: the card is what starts the post-dialogue one, when it ends.
	await skip_vs_card()
	var boss: Node = current_scene.get_node("Arena/EricBossScene/CharacterBody2D")
	boss.state_machine.set_process(false)
	boss.state_machine.set_physics_process(false)
	for timer in boss.find_children("*", "Timer", true, false):
		timer.stop()
	await wait(4)


# The resume grace is 0.15 real seconds; frames are not, under --fixed-fps, so it is waited out on
# the same clock it is set on.
func past_resume_grace(pause: Node) -> void:
	for i in 100000:
		if pause.grace_until_msec <= Time.get_ticks_msec():
			break
		await process_frame
	await wait(2)


# The pause action itself: fixed on both devices, named for the device in use, out of the
# rebindable set and out of the file, and never opened by ui_cancel on its own.
func test_pause_input() -> void:
	log_p("-- the action")
	check(InputMap.has_action(&"pause"), "there is a pause action")
	var keys := []
	var buttons := []
	for ev in InputMap.action_get_events(&"pause"):
		if ev is InputEventKey:
			keys.append([ev.physical_keycode, ev.keycode])
		elif ev is InputEventJoypadButton:
			buttons.append(ev.button_index)
	log_p("pause is bound to %s and %s" % [keys, buttons])
	check(keys == [[KEY_ESCAPE, 0]], "one key, Escape, as a physical position")
	check(buttons == [JOY_BUTTON_START], "and one button, Start")
	check(not settings.ACTIONS.has(&"pause"), "it is not in the rebindable list")
	check(settings.rebind(&"pause", key_event(KEY_P, true)) == &"" and InputMap.action_get_events(&"pause").size() == 2, "and rebind() refuses it")
	settings._save()
	var cfg := ConfigFile.new()
	cfg.load(TEST_SAVE_PATH)
	check(not cfg.has_section_key("bindings", "pause"), "nothing about it is written to the file")

	log_p("-- what the prompts call it")
	check(settings.device == settings.Device.KEYBOARD, "starting on the keyboard")
	check(settings.pause_name == "ESC", "on a keyboard it is ESC (%s)" % settings.pause_name)
	Input.joy_connection_changed.emit(0, true)
	await wait(1)
	var glyph: String = load("res://Scripts/ControlsArtLayout.gd").inline_glyph(13)
	log_p("on a pad: %s" % settings.pause_name)
	check(settings.pause_name == glyph, "on a pad it is the sheet's Start glyph, drawn inline")
	check(settings.pad_label_for(&"pause") == "START" and settings.pad_frame_for(&"pause") == 13, "named START, column 13")
	Input.joy_connection_changed.emit(0, false)
	await wait(1)

	log_p("-- in a fight")
	await load_quiet_fight()
	var pause: Node = pause_menu()
	check(pause != null and not pause.is_open(), "the fight starts unpaused")
	Input.joy_connection_changed.emit(0, true)
	for i in 3:
		tap_button(JOY_BUTTON_B)
		await wait(3)
	check(not pause.is_open() and not paused, "B, which is ui_cancel and the dash, never opens it")
	tap_button(JOY_BUTTON_START)
	await wait(3)
	check(pause.is_open() and paused, "Start does")
	tap_button(JOY_BUTTON_START)
	await wait(3)
	check(not pause.is_open() and not paused, "and Start again closes it")

	log_p("-- and the last pad going away pauses the fight on its own")
	Input.joy_connection_changed.emit(0, false)
	await wait(3)
	check(pause.is_open() and paused, "unplugging the last pad opened it")
	tap_key(KEY_ESCAPE)
	await wait(3)
	check(not pause.is_open() and not paused, "and Escape closes it")
	await past_resume_grace(pause)
	tap_key(KEY_ESCAPE)
	await wait(3)
	check(pause.is_open(), "Escape opens it on the keyboard")
	tap_key(KEY_ESCAPE)
	await wait(3)
	check(not pause.is_open() and not paused, "and closes it again")
	check(current_scene.scene_file_path == ERIC_FIGHT, "none of that left the fight")


# The rebind screen, hosted inside the pause screen: it changes a binding without leaving the fight,
# its Back returns to the pause rows, and the new binding is live the moment the fight resumes.
func test_pause_controls() -> void:
	await load_quiet_fight()
	var player: CharacterBody2D = current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
	player.playerHealth = 100
	var pause: Node = pause_menu()
	tap_key(KEY_ESCAPE)
	await wait(3)
	check(pause.is_open(), "paused")

	log_p("-- CONTROLS opens the rebind screen over the fight")
	# RESUME, RESTART FIGHT, then CONTROLS.
	for i in 2:
		tap_key(KEY_DOWN)
		await wait(2)
	check(focus_owner() == pause.controls_button, "CONTROLS has focus (%s)" % focus_name())
	tap_key(KEY_ENTER)
	await wait(4)
	check(pause.level == pause.Level.CONTROLS, "the screen is on its controls level")
	var screen: Control = pause.controls_host.get_child(0) if pause.controls_host.get_child_count() > 0 else null
	check(screen != null and screen.embedded, "the rebind screen is hosted here, in embedded mode")
	check(not screen.background.visible, "with its own backdrop off, so the paused fight shows through behind it")
	check(current_scene.scene_file_path == ERIC_FIGHT and paused, "without leaving the fight, which is still paused")

	log_p("-- rebinding attack from inside it")
	screen.cells[false][&"punch"].grab_focus()
	await wait(2)
	tap_key(KEY_ENTER)
	await wait(4)
	check(screen.listening, "the attack cell is listening")
	tap_key(KEY_Z)
	await wait(4)
	check(settings.bindings[&"punch"]["key"] == KEY_Z, "attack is on Z now (%d)" % settings.bindings[&"punch"]["key"])
	check(settings.bindings[&"punch"]["pad_button"] == JOY_BUTTON_A, "and its pad side is untouched")

	log_p("-- Back returns to the pause rows, not to the main menu")
	tap_key(KEY_ESCAPE)
	await wait(4)
	check(current_scene.scene_file_path == ERIC_FIGHT, "still in the fight")
	check(pause.level == pause.Level.ROOT and pause.is_open(), "back on the pause rows")
	check(pause.controls_host.get_child_count() == 0, "and the rebind screen is gone")
	check(focus_owner() == pause.controls_button, "with focus back on the row that opened it (%s)" % focus_name())

	log_p("-- and the new binding punches as soon as the fight is back")
	tap_key(KEY_ESCAPE)
	await wait(3)
	check(not pause.is_open() and not paused, "resumed")
	await past_resume_grace(pause)
	tap_key(KEY_Z)
	var swung := false
	for i in 20:
		swung = swung or punching(player)
		await process_frame
	check(swung, "Z throws a punch")
	# Let that swing finish before the old key is tried, or its own animation would answer for it.
	for i in 120:
		if not punching(player):
			break
		await process_frame
	await wait(20)
	tap_key(KEY_Q)
	var old_key := false
	for i in 20:
		old_key = old_key or punching(player)
		await process_frame
	check(not old_key, "and Q, which it used to be, does not")
	settings.reset_to_defaults()


# ------------------------------------------------------------------ trigger_press

# A trigger reports a pull as a run of motion events past the dead zone, the way a pad does, and holds as more of
# them while it jitters at the top.
func pull_trigger(axis: int) -> void:
	for value in [0.05, 0.15, 0.3, 0.45, 0.6, 0.75, 0.9, 1.0, 0.98, 1.0, 0.99, 1.0]:
		send([axis_event(axis, value)])
		await wait(1)


func release_trigger(axis: int) -> void:
	for value in [0.6, 0.3, 0.1, 0.0]:
		send([axis_event(axis, value)])
		await wait(1)


# A press rebound to a trigger, in a fight: one pull is one press, its first report past the dead zone
# (PlayerScript._repeat_of_held_axis). Until 2026-10-04 every report past it was another press, so one pull of a
# trigger-bound parry was five presses: five missed parries paid, and the first press's window ended by the
# second, so it could never parry.
func test_trigger_press() -> void:
	settings.rebind(&"block", axis_event(JOY_AXIS_TRIGGER_RIGHT, 1.0))
	settings.rebind(&"punch", axis_event(JOY_AXIS_TRIGGER_LEFT, 1.0))
	await load_quiet_fight()
	var player: CharacterBody2D = current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
	var defense: Node = player.get_node("Defense")
	var presses := []
	defense.block_pressed.connect(func(credited: bool) -> void: presses.append(credited))

	log_p("-- the guard on RT")
	await pull_trigger(JOY_AXIS_TRIGGER_RIGHT)
	await release_trigger(JOY_AXIS_TRIGGER_RIGHT)
	await wait(10)
	check(presses == [true], "one pull is one press, credited (%s)" % [presses])
	check(is_equal_approx(defense.stamina, defense.max_stamina - defense.parry_whiff_cost), "and it pays one missed parry (%.1f)" % defense.stamina)
	await wait(30)
	await pull_trigger(JOY_AXIS_TRIGGER_RIGHT)
	await release_trigger(JOY_AXIS_TRIGGER_RIGHT)
	check(presses == [true, true], "a second pull, past the mash lockout, is a second credited press (%s)" % [presses])

	log_p("-- a pull parries")
	await wait(60)
	var hit_info: GDScript = load("res://Scripts/HitInfo.gd")
	var centre: Vector2 = player.hurtBox.get_node("CollisionShape2D").global_position
	var result := -1
	for value in [0.15, 0.3, 0.45, 0.6]:
		send([axis_event(JOY_AXIS_TRIGGER_RIGHT, value)])
		await wait(1)
	var source := Node2D.new()
	result = player.receive_hit(hit_info.make(&"eric_quake_wave_v2", source, centre))
	source.free()
	check(result == hit_info.Result.PARRIED, "a wave landing on the pull's fourth report is parried (%s)" % hit_info.Result.keys()[result])
	await release_trigger(JOY_AXIS_TRIGGER_RIGHT)

	log_p("-- attack on LT")
	await wait(120)
	var swings := 0
	var was_punching := false
	for value in [0.05, 0.15, 0.3, 0.45, 0.6, 0.75, 0.9, 1.0]:
		send([axis_event(JOY_AXIS_TRIGGER_LEFT, value)])
		await wait(1)
	# Held for well past a swing, jittering at the top as a held trigger does.
	for i in 60:
		send([axis_event(JOY_AXIS_TRIGGER_LEFT, 1.0 if i % 2 == 0 else 0.99)])
		await wait(1)
		var now := punching(player)
		if now and not was_punching:
			swings += 1
		was_punching = now
	await release_trigger(JOY_AXIS_TRIGGER_LEFT)
	check(swings == 1, "one pull held for a second throws one punch (%d)" % swings)
	settings.reset_to_defaults()


# ------------------------------------------------------------------ flow_prefetch

# The screens between fights load the next scene on threads while they are up (the 2026-10-04 playtest: NEXT BOSS
# froze the Victory screen for 0.2 to 0.8 s a fight, and Danny's intro line froze for about a second before the
# controls room). What it must not change: where each one goes, and the fight it opens being the ladder's fight.
func test_flow_prefetch() -> void:
	var progress: Node = root.get_node("GameProgress")
	log_p("-- Victory, with a next fight")
	progress.reset_progress()
	progress.next_boss_scene = ERIC_FIGHT
	await load_scene(VICTORY_SCENE)
	var status := ResourceLoader.load_threaded_get_status(ERIC_FIGHT)
	check(status == ResourceLoader.THREAD_LOAD_IN_PROGRESS or status == ResourceLoader.THREAD_LOAD_LOADED, "the next fight is loading behind it (%d)" % status)
	await wait(45)
	check(focus_name() == "NextBossButton" and current_scene.next_boss_button.text == "NEXT BOSS", "NEXT BOSS has focus (%s)" % focus_name())
	tap_key(KEY_ENTER)
	tap_key(KEY_ENTER)
	check(await wait_for_scene(ERIC_FIGHT), "and opens Eric's fight, once, for two presses (%s)" % current_scene.scene_file_path)
	await wait(2)
	check(progress.fight_index == 3, "which the ladder reads as FIGHT 04 (%d)" % progress.fight_index)

	log_p("-- Victory, at the end of the ladder")
	progress.next_boss_scene = ""
	await load_scene(VICTORY_SCENE)
	await wait(45)
	check(current_scene.next_boss_button.text == "MAIN MENU", "the button says MAIN MENU")
	tap_key(KEY_ENTER)
	check(await wait_for_scene(MENU_SCENE), "and goes there")

	log_p("-- Danny's intro line")
	await load_scene("res://Scenes/Core/IntroScene.tscn")
	status = ResourceLoader.load_threaded_get_status(CONTROLS_SCENE)
	check(status == ResourceLoader.THREAD_LOAD_IN_PROGRESS or status == ResourceLoader.THREAD_LOAD_LOADED, "the controls room is loading behind it (%d)" % status)
	var reached := false
	for i in 1200:
		if current_scene != null and current_scene.scene_file_path == CONTROLS_SCENE:
			reached = true
			break
		if i % 20 == 10:
			tap_key(KEY_ENTER)
		await process_frame
	check(reached, "reading the line opens the controls room")
	progress.reset_progress()


# ------------------------------------------------------------------ parry_tap

# A parry TAPPED, its key let go before the hit lands, against one held through it: with blocking off the stance is
# the press's 0.24 s window whether the key is still down or not (PlayerBlocking). Until 2026-10-04 letting go
# dropped it, so a tap parried only while it was down - about half the window for a quick tap.
func tap_parry_result(hold_frames: int, gap: int, player: CharacterBody2D) -> int:
	var defense: Node = player.get_node("Defense")
	var hit_info: GDScript = load("res://Scripts/HitInfo.gd")
	defense._set_stamina(defense.max_stamina)
	player.is_invincible = false
	player.invincibility_timer.stop()
	await wait(45)
	send([key_event(KEY_SHIFT, true)])
	var down := true
	for frame in gap:
		await physics_frame
		if down and frame + 1 >= hold_frames:
			send([key_event(KEY_SHIFT, false)])
			down = false
	var source := Node2D.new()
	var centre: Vector2 = player.hurtBox.get_node("CollisionShape2D").global_position
	var result: int = player.receive_hit(hit_info.make(&"eric_quake_wave_v2", source, centre))
	source.free()
	if down:
		send([key_event(KEY_SHIFT, false)])
	return result


# A 2-frame tap, then `code` (attack or dash) pressed, and a wave on the player 10 frames after the tap.
func tap_then(player: CharacterBody2D, code: int) -> int:
	var defense: Node = player.get_node("Defense")
	var hit_info: GDScript = load("res://Scripts/HitInfo.gd")
	defense._set_stamina(defense.max_stamina)
	player.is_invincible = false
	player.invincibility_timer.stop()
	await wait(70)
	send([key_event(KEY_SHIFT, true)])
	await wait(2)
	send([key_event(KEY_SHIFT, false)])
	await wait(2)
	send([key_event(code, true), key_event(code, false)])
	await wait(6)
	var source := Node2D.new()
	var result: int = player.receive_hit(hit_info.make(&"eric_quake_wave_v2", source, player.hurtBox.get_node("CollisionShape2D").global_position))
	source.free()
	await wait(30)
	return result


func test_parry_tap() -> void:
	await load_quiet_fight()
	var player: CharacterBody2D = current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
	# Twenty parries of his own wave would Break him, and a Break holds the player.
	var eric: Node = current_scene.get_node("Arena/EricBossScene/CharacterBody2D")
	if eric.break_gauge:
		eric.break_gauge.locked = true
		eric.break_gauge.set_physics_process(false)
	var hit_info: GDScript = load("res://Scripts/HitInfo.gd")
	root.get_node("GameProgress").playtest_invincible = true

	log_p("-- inside the window, tapped or held")
	var table := []
	var all_parried := true
	for hold in [1, 3, 6, 999]:
		for gap in [2, 6, 10, 14]:
			var result: int = await tap_parry_result(hold, gap, player)
			table.append("%s/%d:%s" % ["held" if hold == 999 else str(hold), gap, hit_info.Result.keys()[result]])
			all_parried = all_parried and result == hit_info.Result.PARRIED
	log_p("key down/frames to the hit: %s" % [table])
	check(all_parried, "a press parries a hit up to 14 frames later whether its key is let go after 1, 3 or 6 frames or held")
	var late: int = await tap_parry_result(2, 17, player)
	check(late == hit_info.Result.HIT, "and a tap's hit 17 frames on, past the window, lands (%s)" % hit_info.Result.keys()[late])

	log_p("-- a tap frees the player at once, and only letting go keeps the parry")
	await wait(70)
	var from := player.global_position
	send([key_event(KEY_SHIFT, true)])
	await wait(2)
	send([key_event(KEY_SHIFT, false), key_event(KEY_RIGHT, true)])
	await wait(6)
	var walked := player.global_position.x - from.x
	var source := Node2D.new()
	var walking: int = player.receive_hit(hit_info.make(&"eric_quake_wave_v2", source, player.hurtBox.get_node("CollisionShape2D").global_position))
	source.free()
	send([key_event(KEY_RIGHT, false)])
	check(walked > 20.0 and walking == hit_info.Result.PARRIED, "after a 2-frame tap they walk on (%.0f px in 6 frames) and the press still parries 8 frames in (%s)" % [walked, hit_info.Result.keys()[walking]])
	var after_punch := await tap_then(player, KEY_Q)
	check(after_punch == hit_info.Result.HIT, "a punch thrown after the tap gives the parry up (%s)" % hit_info.Result.keys()[after_punch])
	var after_dash := await tap_then(player, KEY_W)
	check(after_dash == hit_info.Result.HIT, "and so does a dash (%s)" % hit_info.Result.keys()[after_dash])

	log_p("-- with blocking on, letting go still drops the guard")
	var defense_script: GDScript = load("res://Scripts/PlayerDefense.gd")
	defense_script.BLOCKING_ENABLED = true
	await wait(70)
	send([key_event(KEY_SHIFT, true)])
	await wait(4)
	send([key_event(KEY_SHIFT, false)])
	await wait(2)
	check(player.state_machine.current_state.name != "Blocking", "the guard drops with the key (%s)" % player.state_machine.current_state.name)
	defense_script.BLOCKING_ENABLED = false
	root.get_node("GameProgress").playtest_invincible = false


# ------------------------------------------------------------------ restart_phase

# Pause, RESTART FIGHT and its confirmation, pressed the way a player presses them.
func restart_from_pause() -> void:
	var pause: Node = pause_menu()
	pause.open()
	await wait(2)
	pause.restart_button.pressed.emit()
	await wait(2)
	pause.confirm_ok_button.pressed.emit()


func greyson_in_fight() -> Node:
	return current_scene.find_child("GreysonCharacterBody", true, false) if current_scene != null else null


# FIGHT 06's restart: in Greyson's half it opens his half again, the way the menu's GREYSON row does, and in
# Computah's half it opens Computah's fight from his intro (the 2026-10-04 playtest: a restart in Greyson's half
# reloaded Computah's intro and his fight, already won). FIGHT 07's the same: in Liam's half his half again, and in
# Bixby's the fight from Bixby (the 2026-10-07 playtest: a restart in Liam's half went back to Bixby). Each straight to
# the fight, its takeover or its intro skipped.
func test_restart_phase() -> void:
	var fight := "res://Scenes/Bosses/ComputahBossFightScene.tscn"
	var progress: Node = root.get_node("GameProgress")
	progress.reset_progress()
	progress.start_at_greyson = true
	await load_scene(fight)
	var reached := false
	for i in 900:
		if greyson_in_fight() != null:
			reached = true
			break
		await process_frame
	check(reached, "the GREYSON row opens his half")
	await wait(30)
	var scene_before := current_scene
	await restart_from_pause()
	for i in 600:
		if current_scene != null and current_scene != scene_before and current_scene.scene_file_path == fight:
			break
		await process_frame
	var back := false
	for i in 900:
		if greyson_in_fight() != null:
			back = true
			break
		await process_frame
	check(back, "RESTART FIGHT in his half opens his half again")
	var computah: Node = current_scene.get_node("Arena/ComputahScene/ComputahCharacterBody")
	check(computah.defeated, "with Computah already down")
	check(not progress.start_at_greyson, "and the request spent")
	var handed: Array = await free_without_presses(RETRY_FREE_FRAMES_PHASE + RETRY_RUN_FRAMES + 30)
	check(handed[0] >= 0 and handed[0] <= RETRY_FREE_FRAMES_PHASE and handed[1] == 0, "his takeover skipped: no line shown (%d), the player free from frame %d" % [handed[1], handed[0]])

	log_p("-- in Computah's half")
	await wait(30)
	progress.reset_progress()
	await load_scene(fight)
	await wait(20)
	scene_before = current_scene
	await restart_from_pause()
	for i in 600:
		if current_scene != null and current_scene != scene_before and current_scene.scene_file_path == fight:
			break
		await process_frame
	await wait(20)
	var again: Node = current_scene.get_node("Arena/ComputahScene/ComputahCharacterBody")
	check(greyson_in_fight() == null and not again.defeated and String(again.state_machine.current_state.name) == "Intro", "RESTART FIGHT in Computah's half opens his fight from the intro (%s)" % again.state_machine.current_state.name)
	check(fight_player() != null and not fight_player().is_talking and not current_scene.get_node("Arena/VsCard").is_playing(), "skipped to the fight: the player free 20 frames in")

	log_p("-- in Liam's half")
	var liam_fight := "res://Scenes/Bosses/LiamBossFightScene.tscn"
	progress.reset_progress()
	progress.start_at_liam = true
	await load_scene(liam_fight)
	check(await wait_frames_for(func() -> bool: return boss_with_script(LIAM_SCRIPT) != null, 3000), "the LIAM row opens his half")
	check(await read_into_fight(), "and his takeover reads through to his fight")
	scene_before = current_scene
	await restart_from_pause()
	for i in 600:
		if current_scene != null and current_scene != scene_before and current_scene.scene_file_path == liam_fight:
			break
		await process_frame
	check(await wait_frames_for(func() -> bool: return boss_with_script(LIAM_SCRIPT) != null, 900), "RESTART FIGHT in his half opens his half again")
	check(current_scene.get_node(BIXBY_BODY).defeated, "with Bixby already down")
	check(not progress.start_at_liam, "and the request spent")
	handed = await free_without_presses(RETRY_FREE_FRAMES_PHASE + RETRY_RUN_FRAMES + 30)
	check(handed[0] >= 0 and handed[0] <= RETRY_FREE_FRAMES_PHASE and handed[1] == 0, "his takeover skipped: no line shown (%d), the player free from frame %d" % [handed[1], handed[0]])

	log_p("-- in Bixby's half")
	progress.reset_progress()
	await load_scene(liam_fight)
	check(await read_into_fight(), "the fight reads through to Bixby")
	scene_before = current_scene
	await restart_from_pause()
	for i in 600:
		if current_scene != null and current_scene != scene_before and current_scene.scene_file_path == liam_fight:
			break
		await process_frame
	await wait(20)
	check(boss_with_script(LIAM_SCRIPT) == null and not current_scene.get_node(BIXBY_BODY).defeated, "RESTART FIGHT in Bixby's half opens the fight from Bixby, with no Liam")
	check(fight_player() != null and not fight_player().is_talking and not current_scene.get_node("Arena/VsCard").is_playing(), "skipped to the fight: the player free 20 frames in")
	progress.reset_progress()


# ------------------------------------------------------------------ hud_fade

func fade_of(block: Control) -> float:
	var wrapper := block.get_node_or_null(^"PlayerFade") as Control
	return wrapper.modulate.a if wrapper != null else -1.0


# Puts the player's origin at `at` (the ring keeps them on its floor), stands Eric well away, and waits out a fade.
func stand_at(player: CharacterBody2D, eric: Node2D, at: Vector2) -> void:
	eric.global_position = Vector2(960, 640)
	player.global_position = at
	player.velocity = Vector2.ZERO
	await wait(30)


# The HUD blocks fade while the player, a boss or a tell's badge is under them (HudPlayerFade): the boss bar and the
# Break gauge at the top middle, the hearts and stamina bottom left, the hype meter bottom right (the 2026-10-04
# playtest: a player by the top rope's middle vanished under the boss bar, and the corner panels covered their feet).
func test_hud_fade() -> void:
	await load_quiet_fight()
	var player: CharacterBody2D = current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
	var eric: Node2D = current_scene.get_node("Arena/EricBossScene/CharacterBody2D")
	var hud: CanvasLayer = current_scene.get_node("Arena/MainPlayer/CanvasLayer")
	var bar: Control = eric.health_bar
	var gauge: Control = null
	for child in bar.get_parent().get_children():
		if child.get_script() != null and str(child.get_script().resource_path).ends_with("BreakGaugeUI.gd"):
			gauge = child
	var hearts: Control = hud.get_node("Control")
	var stamina: Control = hud.get_node("StaminaBar")
	var hype: Control = hud.get_node("HypeMeter")
	var middle: Vector2 = player.ring_origins.get_center()
	await stand_at(player, eric, middle)
	var blocks := {"bar": bar, "hearts": hearts, "stamina": stamina, "hype": hype}
	if gauge != null:
		blocks["gauge"] = gauge
	var clear := true
	for key in blocks:
		clear = clear and is_equal_approx(fade_of(blocks[key]), 1.0)
	check(clear, "mid-ring, every block is whole (%s)" % [blocks.keys().map(func(k): return "%s %.2f" % [k, fade_of(blocks[k])])])

	await stand_at(player, eric, Vector2(960, player.ring_origins.position.y))
	check(fade_of(bar) < 0.35, "by the top rope's middle the boss bar fades (%.2f)" % fade_of(bar))
	check(gauge == null or fade_of(gauge) < 0.35, "and the Break gauge under it (%.2f)" % (fade_of(gauge) if gauge else 0.0))
	check(is_equal_approx(fade_of(hearts), 1.0) and is_equal_approx(fade_of(hype), 1.0), "the corners stay whole")
	check(is_equal_approx(bar.modulate.a, 1.0), "on its own wrapper: the bar's own modulate, which the fights tween, is untouched (%.2f)" % bar.modulate.a)

	await stand_at(player, eric, player.ring_origins.position + Vector2(0, player.ring_origins.size.y))
	check(fade_of(hearts) < 0.35, "in the bottom-left corner the hearts fade (%.2f; the stamina bar under them, which the feet don't reach, %.2f)" % [fade_of(hearts), fade_of(stamina)])
	check(is_equal_approx(fade_of(bar), 1.0), "and the boss bar is whole again (%.2f)" % fade_of(bar))
	await stand_at(player, eric, player.ring_origins.end)
	check(fade_of(hype) < 0.35, "in the bottom-right corner the hype meter fades (%.2f)" % fade_of(hype))

	log_p("-- a tell's badge under the bar, and a boss who isn't")
	await stand_at(player, eric, middle)
	eric.global_position = Vector2(960, 150)
	await wait(30)
	check(is_equal_approx(fade_of(bar), 1.0), "Eric's own body by the top rope leaves the bar to his fight (%.2f)" % fade_of(bar))
	eric.global_position = Vector2(960, 640)
	await wait(30)
	var tell_script: GDScript = load("res://Scripts/ParryTell.gd")
	tell_script.telegraph(eric, &"eric_quake_wave_v2", 5.0, func() -> Vector2: return Vector2(960, 140))
	await wait(30)
	check(fade_of(bar) < 0.35, "a red badge under it fades it too (%.2f)" % fade_of(bar))
	tell_script.clear(eric)
	await wait(60)
	check(is_equal_approx(fade_of(bar), 1.0), "and it comes back once the badge is gone (%.2f)" % fade_of(bar))
	var prompt: Node = hud.get_node("FinisherPrompt")
	var stamp: CanvasItem = prompt.knight_breaker
	stamp.visible = true
	await wait(30)
	check(fade_of(bar) < 0.35, "KNIGHT BREAKER!, which goes up under it, fades it too (%.2f)" % fade_of(bar))
	stamp.visible = false
	await wait(30)


# ------------------------------------------------------------------ dash_punch

# A punch pressed in a dash's three moving frames is dropped, as one in its landing beat is: it used to freeze the
# dash where it was for the whole swing, still dashing, and finish it after (the 2026-10-04 playtest).
func test_dash_punch() -> void:
	await load_quiet_fight()
	var player: CharacterBody2D = current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
	var defense: Node = player.get_node("Defense")
	var clean := true
	var table := []
	for punch_at in [0, 1, 2]:
		defense._set_stamina(defense.max_stamina)
		defense.clear_dash_recovery()
		player.global_position = player.ring_origins.position + Vector2(100, player.ring_origins.size.y - 60)
		await wait(40)
		var from := player.global_position
		send([key_event(KEY_RIGHT, true), key_event(KEY_W, true), key_event(KEY_W, false)])
		var swung := false
		for frame in 8:
			if frame == punch_at:
				send([key_event(KEY_Q, true), key_event(KEY_Q, false)])
			await physics_frame
			swung = swung or punching(player)
		var dashed := player.global_position.x - from.x
		send([key_event(KEY_RIGHT, false)])
		table.append("%d: %.0f px%s" % [punch_at, dashed, ", swung" if swung else ""])
		clean = clean and is_equal_approx(dashed, 250.0) and not swung and not player.is_dodging
		await wait(40)
	check(clean, "a punch pressed 0, 1 or 2 frames into a dash leaves it its whole 250 px and throws nothing (%s)" % [table])
	await wait(20)
	tap_key(KEY_Q)
	var swung_after := false
	for i in 20:
		swung_after = swung_after or punching(player)
		await process_frame
	check(swung_after, "and a punch after the dash's landing throws as ever")


# ------------------------------------------------------------------ outro_stale

# A fight lost while the last fight's outro is still alive under the root (a scene changed under it): FightOutro's
# one-outro guard is for the fight it decided only, so this fight ends too, on its own outro, through to the Defeat
# screen. Before 2026-10-04 the guard took any outro, and the player sat at 0 health with the boss attacking on.
func test_outro_stale() -> void:
	await load_quiet_fight()
	var player: CharacterBody2D = current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
	player.playerHealth = 0
	await wait(5)
	var first: Node = root.get_node_or_null(^"FightOutro")
	check(first != null and player.fight_over, "a loss puts an outro up")
	await load_quiet_fight()
	check(is_instance_valid(first) and first.is_inside_tree(), "and it is still alive as the next fight loads")
	player = current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
	player.playerHealth = 0
	await wait(5)
	var second: Node = root.get_node_or_null(^"FightOutro")
	check(player.fight_over and second != null and second != first and second.fight_scene == current_scene, "losing the next fight decides it, on an outro of its own")
	check(not is_instance_valid(first) or not first.is_inside_tree(), "and the one left over is gone")
	var reached := false
	for i in 1800:
		if current_scene != null and current_scene.scene_file_path == DEFEAT_SCENE:
			reached = true
			break
		if i % 20 == 10:
			tap_key(KEY_ENTER)
		await process_frame
	check(reached, "through to the Defeat screen")


# ------------------------------------------------------------------ defeat_retry

# The phases a retry must land in that the ladder's own scenes don't show: [label, the scene the fight is opened on, the
# main menu's request it is opened with, what the retry must open]. Greyson's half opens his half again, and Liam's half
# his (it opened the fight from Bixby until the 2026-10-07 playtest); the Puppet Master is a scene of its own.
const RETRY_EXTRA_CASES := [
	["greyson", "res://Scenes/Bosses/ComputahBossFightScene.tscn", &"greyson", &"greyson"],
	["liam_half", "res://Scenes/Bosses/LiamBossFightScene.tscn", &"liam", &"liam"],
	["god", "res://Scenes/Bosses/JordanGodFightScene.tscn", &"", &""],
]
# Frames a retry may take to hand the player the fight with nothing pressed (the 2026-10-07 playtest: it replayed every
# pre-fight line and the VS card). The skip lands on the card's flash in about 12; a takeover's KO beat (0.8 s) and the
# Puppet Master's own opening (1 s) come before theirs.
const RETRY_FREE_FRAMES := 30
const RETRY_FREE_FRAMES_PHASE := 75
const RETRY_RUN_FRAMES := 30
const BIXBY_BODY := "Arena/BixbyBeastScene/BixbyBeastCharacterBody"
const BOSS_ENTRANCE_SCRIPT := "res://Scripts/BossEntrance.gd"
const LIAM_SCRIPT := "res://Scripts/LiamScript.gd"
const COMPUTAH_BODY := "Arena/ComputahScene/ComputahCharacterBody"
const COMPUTAH_FIGHT := "res://Scenes/Bosses/ComputahBossFightScene.tscn"
# Frames the player must stay free for the fight to count as handed over: the first frames of a load, before the
# walk-in has taken hold of them, are free too.
const LIVE_FRAMES := 60


func fight_player() -> CharacterBody2D:
	return current_scene.get_node_or_null("Arena/MainPlayer/CharacterBody2D") if current_scene != null else null


func boss_with_script(path: String) -> Node:
	for boss in get_nodes_in_group("fight_boss"):
		var script: Script = boss.get_script()
		if script != null and script.resource_path == path:
			return boss
	return null


func wait_frames_for(cond: Callable, max_frames: int) -> bool:
	for i in max_frames:
		if cond.call():
			return true
		await process_frame
	return false


# Reads whatever holds the player the way a player does - Enter every 15 frames through the walk-in, the lines and the VS
# card - until the fight has let go of them for LIVE_FRAMES in a row. False if it never does. The pre-fight hold is
# is_talking (BossEntrance); an action lock is a boss's own attack - Carter's barrage roots the player - so it counts as
# the fight, as does a loss to it.
func read_into_fight(max_frames := 6000) -> bool:
	var free_for := 0
	for i in max_frames:
		var player := fight_player()
		var card: Node = current_scene.get_node_or_null("Arena/VsCard") if current_scene != null else null
		var free: bool = player != null and not player.is_talking and (card == null or not card.is_playing())
		free_for = free_for + 1 if free else 0
		if free_for >= LIVE_FRAMES:
			log_p("the fight let go of the player %d frames in" % (i + 1 - LIVE_FRAMES))
			return true
		if i % 15 == 0:
			tap_key(KEY_ENTER)
		await process_frame
	var held := fight_player()
	if held != null:
		log_p("still held: is_talking %s, action locked %s, fight over %s" % [held.is_talking, held.is_action_locked, held.fight_over])
	return false


# A fight just opened by a retry, watched with nothing pressed until it has let go of the player for RETRY_RUN_FRAMES
# frames in a row: [the frame that run started on, -1 if it never came; frames a dialogue line was up on; frames a skip
# hint was showing on].
func free_without_presses(max_frames: int) -> Array:
	var run := 0
	var lines := 0
	var hints := 0
	for i in max_frames:
		var balloon := find_balloon()
		if balloon != null and balloon.is_inside_tree() and balloon.balloon.visible:
			lines += 1
		if skip_hint_showing():
			hints += 1
		var player := fight_player()
		var card: Node = current_scene.get_node_or_null("Arena/VsCard")
		run = run + 1 if player != null and not player.is_talking and (card == null or not card.is_playing()) else 0
		if run >= RETRY_RUN_FRAMES:
			return [i + 1 - run, lines, hints]
		await process_frame
	return [-1, lines, hints]


# Whether any BossEntrance in the fight is showing its skip hint at all.
func skip_hint_showing() -> bool:
	for node in current_scene.find_children("*", "CanvasLayer", true, false):
		var script: Script = node.get_script()
		if script != null and script.resource_path == BOSS_ENTRANCE_SCRIPT and node.hint != null and node.hint.modulate.a > 0.0:
			return true
	return false


# A boss's blow landing on the player, who stands still where the fight let them go, since they were last on `health`:
# the fight is on.
func boss_lands_hit(health: int, max_frames := 3600) -> bool:
	var player := fight_player()
	for i in max_frames:
		if player.playerHealth < health:
			return true
		if i % 15 == 0:
			tap_key(KEY_ENTER)
		await process_frame
	return false


# The fight lost, its outro read through with Enter, up to the Defeat screen's first frame. Enter stops on the frame that
# screen is up, so what presses it from there is the caller's. Bounded by the wall clock, not frames: the loss lines hold
# their input for 0.3 REAL seconds (FightOutro.LOSS_LINE_INPUT_LOCK) before a press ends them, and under --fixed-fps that
# can be many frames.
func lose_to_defeat() -> bool:
	fight_player().playerHealth = 0
	var until := Time.get_ticks_msec() + 60000
	var i := 0
	while Time.get_ticks_msec() < until:
		if current_scene != null and current_scene.scene_file_path == DEFEAT_SCENE:
			return true
		if i % 20 == 10:
			tap_key(KEY_ENTER)
		i += 1
		await process_frame
	var outro := root.get_node_or_null(^"FightOutro")
	log_p("still on %s: outro %s, leaving %s" % [current_scene.scene_file_path if current_scene else "<none>", outro != null, outro.leaving if outro else false])
	return false


# The Defeat screen's RETRY (2026-10-04): every fight on the ladder lost and retried through the screen, and the phases
# whose retry isn't the fight's own start. The retry opens the same fight, in the phase the pause screen's RESTART FIGHT
# would, straight to the fight with nothing pressed - no line shown, the card's build-up skipped (the 2026-10-07
# playtest) - and with the walk-in already seen; it is clean and it goes live. On the way, the screen's guards: a mash and
# a held press in its fade-in press nothing, RETRY then has the focus, and two presses open the fight once.
func test_defeat_retry() -> void:
	var progress: Node = root.get_node("GameProgress")
	progress.playtest_invincible = false
	var freeze: GDScript = load("res://Scripts/FightFreeze.gd")
	var view: GDScript = load("res://Scripts/ScreenView.gd")
	var full_health: int = load("res://Scripts/PlayerHealthArtLayout.gd").CONTAINERS * 2
	var base_nodes := root.get_children()
	var cases := []
	for scene in progress.FIGHT_SCENES:
		cases.append([scene.get_file().get_basename(), scene, &"", &""])
	cases.append_array(RETRY_EXTRA_CASES)
	if retry_only != "":
		cases = cases.filter(func(c: Array) -> bool: return c[0] == retry_only)
		check(not cases.is_empty(), "fight=%s is a case" % retry_only)

	for case in cases:
		var label: String = case[0]
		var scene: String = case[1]
		var request: StringName = case[2]
		var lands_in: StringName = case[3]
		log_p("-- %s" % label)
		progress.reset_progress()
		progress.start_at_greyson = request == &"greyson"
		progress.start_at_liam = request == &"liam"
		await load_scene(scene)
		if request == &"greyson":
			check(await wait_frames_for(func() -> bool: return greyson_in_fight() != null, 900), "the GREYSON row opens his half")
		elif request == &"liam":
			check(await wait_frames_for(func() -> bool: return boss_with_script(LIAM_SCRIPT) != null, 3000), "the LIAM row opens his half")
		check(await read_into_fight(), "the fight lets go of the player")
		check(await lose_to_defeat(), "losing it reads through to the Defeat screen")
		if current_scene.scene_file_path != DEFEAT_SCENE:
			continue
		var screen: Control = current_scene
		# A fight with no walk-in (Computah, Jordan, the Puppet Master) never marks one, and the GREYSON and LIAM rows
		# skip the one the fight would have played first.
		var walked_in: bool = progress.entrances_seen.has(scene)
		check(progress.retry_scene == scene and progress.retry_at_greyson == (request == &"greyson") and progress.retry_at_liam == (request == &"liam"), "the loss noted the fight to retry (%s, Greyson's half %s, Liam's half %s)" % [progress.retry_scene, progress.retry_at_greyson, progress.retry_at_liam])
		var retry: Button = screen.retry_button
		var menu: Button = screen.return_to_menu_button
		check(retry != null and retry.visible and retry.text == "RETRY" and retry.get_rect().position.x < menu.get_rect().position.x, "RETRY is up, first, beside RETURN TO MAIN MENU")
		if retry == null:
			continue
		check(retry.size == menu.size and retry.get_theme_stylebox("normal") == menu.get_theme_stylebox("normal") and retry.theme_type_variation == menu.theme_type_variation, "and it is that button's art and size (%s)" % retry.size)
		var status := ResourceLoader.load_threaded_get_status(scene)
		check(status == ResourceLoader.THREAD_LOAD_IN_PROGRESS or status == ResourceLoader.THREAD_LOAD_LOADED, "the fight is loading behind the screen (%d)" % status)

		# A player still mashing, on both devices, through the screen's fade-in, then holding accept across its end.
		for i in 6:
			tap_key(KEY_ENTER)
			tap_button(JOY_BUTTON_A)
			await wait(4)
		check(current_scene == screen and focus_owner() == null, "a mash in the fade-in presses nothing (%s)" % focus_name())
		send([key_event(KEY_ENTER, true)])
		await wait(15)
		send([key_event(KEY_ENTER, false)])
		await wait(2)
		check(current_scene == screen, "and an accept held across its end presses nothing either")
		check(focus_owner() == retry, "then RETRY has the focus (%s)" % focus_name())

		var changes := [0]
		var count_change := func() -> void: changes[0] += 1
		scene_changed.connect(count_change)
		tap_key(KEY_ENTER)
		tap_key(KEY_ENTER)
		var landed := await wait_for_scene(scene)
		if landed:
			var limit: int = RETRY_FREE_FRAMES if request == &"" and not progress.PHASE_SCENES.has(scene) else RETRY_FREE_FRAMES_PHASE
			var handed: Array = await free_without_presses(limit + RETRY_RUN_FRAMES + 30)
			check(handed[0] >= 0 and handed[0] <= limit and handed[1] == 0, "straight to the fight with nothing pressed: no line shown (%d frames of one), the player free from frame %d (at most %d)" % [handed[1], handed[0], limit])
		await wait(30)
		scene_changed.disconnect(count_change)
		check(landed and changes[0] == 1, "two presses open %s once (%d scene changes)" % [scene.get_file(), changes[0]])
		if not landed:
			continue

		var player := fight_player()
		check(player.playerHealth == full_health and not player.fight_over, "the player is on full health (%d)" % player.playerHealth)
		var hurt := []
		for boss in get_nodes_in_group("fight_boss"):
			var down_by_design: bool = lands_in == &"greyson" and boss == current_scene.get_node_or_null(COMPUTAH_BODY)
			if boss.boss_health != boss.max_health and not down_by_design:
				hurt.append("%s %d/%d" % [boss.name, boss.boss_health, boss.max_health])
		check(hurt.is_empty(), "every boss is on full health %s" % [hurt])
		var left_over := root.get_children().filter(func(n: Node) -> bool: return n != current_scene and not base_nodes.has(n))
		check(left_over.is_empty(), "no outro or anything else left over under the root %s" % [left_over.map(func(n: Node) -> String: return str(n.name))])
		check(is_equal_approx(Engine.time_scale, 1.0) and not paused and not freeze.is_frozen(), "time scale 1 (%.3f), not paused, not frozen" % Engine.time_scale)
		# Settled rather than level at once, and on the fight's base rather than the identity: the Puppet Master opens on a
		# zoom-out of his own (1.47 to 1 over 75 frames, a fresh load's too), onto his whole void drawn further out.
		var settled := await wait_frames_for(func() -> bool: return view.zoom == 1.0 and view.shake_offset == Vector2.ZERO, 120)
		check(settled, "no zoom or shake left over: the view settles on the fight's base (zoom %.2f)" % view.zoom)
		if walked_in:
			check(progress.entrances_seen.has(scene), "the walk-in is still marked seen")
			var entrance: Node = null
			for node in current_scene.find_children("*", "Node", true, false):
				if node.has_method(&"finish_entrance"):
					entrance = node
			if entrance != null:
				check(await wait_frames_for(func() -> bool: return entrance.finished, 10), "so it doesn't play again")
		else:
			log_p("no walk-in was seen before the loss, so none is skipped")
		var index: int = progress.FIGHT_SCENES.find(progress.PHASE_SCENES.get(scene, scene))
		check(progress.fight_index == index, "which the ladder reads as FIGHT %02d (%d)" % [index + 1, progress.fight_index])
		check(progress.retry_scene == "" and not progress.start_at_greyson and not progress.start_at_liam, "and the retry is spent")
		# Taken by the fight's entrance; the Puppet Master has none, and is never owed one.
		check(progress.intro_skip_scene == "", "and so is the skip (%s)" % progress.intro_skip_scene)

		match lands_in:
			&"greyson":
				check(await wait_frames_for(func() -> bool: return greyson_in_fight() != null, 900), "it opens Greyson's half again")
				check(current_scene.get_node(COMPUTAH_BODY).defeated, "with Computah already down")
			&"liam":
				check(boss_with_script(LIAM_SCRIPT) != null, "it opens Liam's half again")
				check(current_scene.get_node(BIXBY_BODY).defeated, "with Bixby already down")
			_:
				if scene == COMPUTAH_FIGHT:
					check(greyson_in_fight() == null and not current_scene.get_node(COMPUTAH_BODY).defeated, "it opens Computah's half, with no Greyson")
		check(await read_into_fight(), "the fight lets go of the player again")
		check(await boss_lands_hit(full_health), "and it is on: a blow lands on them standing still")

	if retry_only != "":
		progress.reset_progress()
		return
	log_p("-- RETURN TO MAIN MENU, and the screen with no fight to retry")
	progress.reset_progress()
	await load_scene(ERIC_FIGHT)
	await read_into_fight()
	await lose_to_defeat()
	await wait(40)
	check(focus_name() == "RetryButton", "RETRY has the focus (%s)" % focus_name())
	tap_button(JOY_BUTTON_DPAD_RIGHT)
	await wait(1)
	var menu_button: Button = current_scene.return_to_menu_button
	check(focus_owner() == menu_button, "right on the d-pad moves it to RETURN TO MAIN MENU (%s)" % focus_name())
	check(menu_button.get_theme_stylebox("focus") is StyleBoxFlat, "and on a pad the focus shows")
	tap_button(JOY_BUTTON_DPAD_LEFT)
	await wait(1)
	check(focus_owner() == current_scene.retry_button, "left takes it back to RETRY (%s)" % focus_name())
	tap_button(JOY_BUTTON_DPAD_RIGHT)
	await wait(1)
	tap_button(JOY_BUTTON_A)
	check(await wait_for_scene(MENU_SCENE), "A on RETURN TO MAIN MENU goes back to the menu")
	await load_scene(DEFEAT_SCENE)
	check(current_scene.retry_button == null, "opened with no fight lost, the screen offers no RETRY")
	check(current_scene.return_to_menu_button.get_rect() == Rect2(636, 915, 648, 126), "and keeps its one button where it was (%s)" % current_scene.return_to_menu_button.get_rect())
	await wait(40)
	check(focus_name() == "ReturnToMenuButton", "with the focus on it (%s)" % focus_name())
	progress.reset_progress()


# ------------------------------------------------------------------ ladder_order

# The user's ladder of 2026-10-06, by difficulty, written out rather than read back from GameProgress so a wrong table
# can't pass by agreeing with itself: [fight scene, VS card key, the name it is listed under, the rank its win pays, his
# face on the Victory screen's ladder - a frame of rank_icons.png, a strip drawn in the order of 2026-09-17].
const LADDER := [
	["res://Scenes/Bosses/BurakBossFightScene.tscn", "burak", "BURAK", "@member", 0],
	["res://Scenes/Bosses/MasonBossFightScene.tscn", "mason", "MASON", "@regular", 4],
	["res://Scenes/Bosses/JoshBossFightScene.tscn", "josh", "JOSH", "@active", 5],
	["res://Scenes/Bosses/EricBossFightScene.tscn", "eric", "ERIC", "@veteran", 1],
	["res://Scenes/Bosses/DannyBossFightScene.tscn", "danny", "DANNY", "@trusted", 6],
	["res://Scenes/Bosses/ComputahBossFightScene.tscn", "computah", "COMPUTAH", "@vip", 2],
	["res://Scenes/Bosses/LiamBossFightScene.tscn", "liam", "LIAM & BIXBY", "@helper", 8],
	["res://Scenes/Bosses/CarterBossFightScene.tscn", "carter", "CARTER", "@moderator", 7],
	["res://Scenes/Bosses/MattBossFightScene.tscn", "matt", "MATT", "@admin", 3],
	["res://Scenes/Bosses/JordanBossFightScene.tscn", "jordan", "JORDAN", "", 9],
]
# The strip's last frame, the goal slot's.
const LADDER_INVITE_ICON := 10
# The boss select's rows, in its order: each fight's own, then its halves and Jordan's finale, god fight and ending.
const LADDER_MENU_ROWS := ["1  BURAK", "2  MASON", "3  JOSH", "4  ERIC", "5  DANNY", "6  COMPUTAH", "    GREYSON",
	"7  LIAM & BIXBY", "    LIAM", "8  CARTER", "9  MATT", "10  JORDAN", "    FINALE", "    GOD", "    ENDING"]
const INTRO_LINE_SCENE := "res://Scenes/Core/IntroScene.tscn"
const GOD_FIGHT := "res://Scenes/Bosses/JordanGodFightScene.tscn"


# The boss select's fight rows, in the panel's order: the buttons four levels under its PanelContainer.
func boss_select_rows() -> Array:
	var rows := []
	for node in current_scene.find_children("*", "Button", true, false):
		if node is CheckBox:
			continue
		var up: Node = node
		for i in 4:
			up = up.get_parent() if up != null else null
		# The menu's own panel: NEW GAME's question box is a PanelContainer as deep, inside a container of its own.
		if up is PanelContainer and up.get_parent() == current_scene:
			rows.append(node.text)
	return rows


# What the fight's own VS card draws for `key`, played and skipped: the file of every plate and the text of every
# written line.
func vs_card_writing(key: String) -> Array:
	var card: Node = load("res://Scripts/VsCard.gd").in_fight(self)
	if card == null:
		return []
	card.play(key)
	await wait(2)
	var drawn := []
	for node in card.writing.find_children("*", "", true, false):
		if node is Sprite2D and node.texture != null:
			drawn.append(node.texture.resource_path.get_file())
		elif node is Label:
			drawn.append(node.text)
	card.skip()
	await wait_frames_for(func() -> bool: return not card.is_playing(), 120)
	card.grace_until_msec = 0
	return drawn


# The Victory screen's rank ladder, as the frames of rank_icons.png its slots show, left to right.
func victory_icons() -> Array:
	var icons: Texture2D = load("res://Assets/UI/Screens/rank_icons.png")
	var shown := []
	for sprite in current_scene.rank_ladder.get_children():
		if sprite is Sprite2D and sprite.texture == icons:
			shown.append([sprite.position.x, sprite.frame])
	shown.sort_custom(func(a: Array, b: Array) -> bool: return a[0] < b[0])
	return shown.map(func(entry: Array) -> int: return entry[1])


# The ladder from NEW GAME to the top (2026-10-06: Burak, Mason, Josh, Eric, Danny, Computah and Greyson, Liam and Bixby,
# Carter, Matt, Jordan). The boss select lists it; NEW GAME's intro, Danny's line and the controls room's READY open the
# first fight; and in each fight its number and its place are the same everywhere: fight_index, the name, the VS card's
# FIGHT plate and WIN plate, #arena-N on the Defeat screen, the Victory screen's rank and its ladder of faces, and NEXT
# BOSS opening the next fight, until the last, whose Victory goes back to the menu. The wins and losses are the screens
# reached straight from each fight, not fights played out: what is under test is the order, not the fights.
func test_ladder_order() -> void:
	var progress: Node = root.get_node("GameProgress")
	var card_art: GDScript = load("res://Scripts/VsCardArtLayout.gd")
	progress.reset_progress()
	var order := []
	for scene in progress.FIGHT_SCENES:
		order.append(scene)
	check(order == LADDER.map(func(step: Array) -> String: return step[0]), "the ladder is the order of 2026-10-06 %s" % [order.map(func(s: String) -> String: return s.get_file().get_basename())])
	check(progress.FIGHT_SCENES.find(progress.PHASE_SCENES.get(GOD_FIGHT, GOD_FIGHT)) == LADDER.size() - 1, "and the Puppet Master is still part of the last fight, FIGHT 10")

	log_p("-- the boss select")
	await load_scene(MENU_SCENE)
	var rows := boss_select_rows()
	check(rows == LADDER_MENU_ROWS, "lists the fights in that order, each half under its fight %s" % [rows])

	log_p("-- NEW GAME: the intro, Danny's line, the controls room and READY")
	await wait(45)
	check(focus_name() == "StartGameButton", "NEW GAME has the focus (%s)" % focus_name())
	tap_key(KEY_ENTER)
	check(await wait_for_scene(INTRO_SCENE), "it opens the intro")
	await wait(5)
	tap_key(KEY_ESCAPE)
	check(await wait_for_scene(INTRO_LINE_SCENE, 600), "skipped, the intro goes on to Danny's line")
	var reached := false
	for i in 1200:
		if current_scene != null and current_scene.scene_file_path == CONTROLS_SCENE:
			reached = true
			break
		if i % 20 == 10:
			tap_key(KEY_ENTER)
		await process_frame
	check(reached, "and his line to the controls room")
	await wait(3)
	root.get_node("DialogueManager").dialogue_ended.emit(null)
	var balloon := find_balloon()
	if balloon:
		balloon.free()
	await wait(3)
	check(focus_name() == "ReadyButton", "once Danny is done READY has the focus (%s)" % focus_name())
	tap_key(KEY_ENTER)
	check(await wait_for_scene(LADDER[0][0], 300), "and opens the first fight, Burak's (%s)" % current_scene.scene_file_path.get_file())

	for i in LADDER.size():
		var step: Array = LADDER[i]
		var scene: String = step[0]
		var number := i + 1
		var rank: String = step[3]
		var next: String = LADDER[i + 1][0] if i + 1 < LADDER.size() else ""
		log_p("-- FIGHT %02d, %s" % [number, step[2]])
		if current_scene == null or current_scene.scene_file_path != scene:
			check(false, "the ladder is in %s (%s)" % [scene.get_file(), current_scene.scene_file_path.get_file() if current_scene else "<none>"])
			break
		await wait(3)
		check(progress.fight_index == i, "fight_index %d (%d)" % [i, progress.fight_index])
		check(progress.boss_name(scene) == step[2], "named %s (%s)" % [step[2], progress.boss_name(scene)])
		check(card_art.key_for_scene(scene) == step[1], "its VS card is %s's (%s)" % [step[1], card_art.key_for_scene(scene)])
		var data: Dictionary = card_art.card(step[1])
		check(int(data["number"]) == number and data["rank"] == rank, "whose table reads FIGHT %02d, WIN %s (%02d, %s)" % [number, rank, int(data["number"]), data["rank"]])
		var drawn: Array = await vs_card_writing(step[1])
		check(drawn.has("fight_%02d.png" % number), "the card draws the FIGHT %02d plate %s" % [number, drawn])
		var wins := drawn.filter(func(file: String) -> bool: return file.begins_with("win_"))
		if rank != "":
			check(wins == ["win_%s.png" % rank.trim_prefix("@")], "and WIN %s" % rank)
		else:
			check(wins.is_empty(), "and no WIN plate: the last fight hands over the invite")

		change_scene_to_file(DEFEAT_SCENE)
		await wait_for_scene(DEFEAT_SCENE)
		await wait(3)
		var lost: String = current_scene.message_label.text
		check(lost.contains("#arena-%d." % number), "a loss reads #arena-%d (%s)" % [number, lost])
		check(progress.fight_index == i, "and the Defeat screen keeps fight_index %d (%d)" % [i, progress.fight_index])

		progress.next_boss_scene = progress.next_fight_after(scene)
		check(progress.next_boss_scene == next, "the fight after it is %s (%s)" % [next.get_file() if next != "" else "none", progress.next_boss_scene.get_file()])
		await load_scene(VICTORY_SCENE)
		var won: String = current_scene.message_label.text
		var paid := "@newcomer ranked up to %s!" % rank if rank != "" else "@newcomer received an invite!"
		check(won == paid, "a win: \"%s\" (%s)" % [paid, won])
		var faces := []
		for j in mini(number + 1, LADDER.size()):
			faces.append(LADDER[j][4])
		faces.append(LADDER_INVITE_ICON)
		var shown := victory_icons()
		check(shown == faces, "its ladder shows the faces of the fights so far, the next and the invite %s (%s)" % [faces, shown])
		await wait(45)
		check(current_scene.next_boss_button.text == ("NEXT BOSS" if next != "" else "MAIN MENU"), "its button says %s" % current_scene.next_boss_button.text)
		tap_key(KEY_ENTER)
		if next != "":
			check(await wait_for_scene(next, 600), "NEXT BOSS opens %s" % next.get_file())
		else:
			check(await wait_for_scene(MENU_SCENE), "at the top of the ladder it goes back to the menu")
	progress.reset_progress()


# ------------------------------------------------------------------ progress_save

# Every mode points GameProgress.save_path here (_main) and deletes it at both ends, so no run reads or writes the save
# of whoever is playtesting from this checkout.
const TEST_PROGRESS_PATH := "user://save_test.cfg"
const MASON_FIGHT := "res://Scenes/Bosses/MasonBossFightScene.tscn"
const JOSH_FIGHT := "res://Scenes/Bosses/JoshBossFightScene.tscn"
const LIAM_FIGHT := "res://Scenes/Bosses/LiamBossFightScene.tscn"
const CARTER_FIGHT := "res://Scenes/Bosses/CarterBossFightScene.tscn"
const FINALE_ROOM := "res://Scenes/Core/JordanFinaleScene.tscn"
const ENDING_SCENE := "res://Scenes/Core/ChampionEndingScene.tscn"
const CONFIRM_TEXT := "START OVER?\nYOUR PROGRESS WILL BE LOST."


func remove_progress_file() -> void:
	if FileAccess.file_exists(TEST_PROGRESS_PATH):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(TEST_PROGRESS_PATH))


# The scratch save as it is on disk, {} when there is none or it doesn't parse.
func saved_file() -> Dictionary:
	var cfg := ConfigFile.new()
	if not FileAccess.file_exists(TEST_PROGRESS_PATH) or cfg.load(TEST_PROGRESS_PATH) != OK:
		return {}
	return {
		"version": cfg.get_value("meta", "version", -1),
		"checkpoint": cfg.get_value("progress", "checkpoint", "<missing>"),
		"phase": cfg.get_value("progress", "phase", "<missing>"),
		"cleared": cfg.get_value("progress", "cleared", -1),
		"finished": cfg.get_value("progress", "finished", "<missing>"),
		"volume": cfg.get_value("settings", "volume", -1.0),
	}


func saved_bytes() -> PackedByteArray:
	return FileAccess.get_file_as_bytes(TEST_PROGRESS_PATH)


# A save at Carter's fight, 7 cleared, with `changes` written over it: what a player who stopped there has.
func write_progress(changes: Dictionary) -> void:
	var fields := {"version": 1, "checkpoint": CARTER_FIGHT, "phase": "", "cleared": 7, "finished": false}
	fields.merge(changes, true)
	var cfg := ConfigFile.new()
	cfg.set_value("meta", "version", fields["version"])
	for key in ["checkpoint", "phase", "cleared", "finished"]:
		cfg.set_value("progress", key, fields[key])
	cfg.set_value("settings", "volume", 1.0)
	cfg.save(TEST_PROGRESS_PATH)


# A change of scene waited out by the tree's own signal, so the scene already up can be loaded again.
func open_scene(path: String) -> void:
	change_scene_to_file(path)
	await scene_changed
	await wait(3)


# The main menu loaded and faded in, its first button focused.
func open_menu() -> Control:
	await open_scene(MENU_SCENE)
	await wait(45)
	return current_scene


# A boss select row pressed the way a player presses it.
func press_row(text: String) -> void:
	for node in current_scene.find_children("*", "Button", true, false):
		if node.text == text and not (node is CheckBox):
			node.grab_focus()
			tap_key(KEY_ENTER)
			return
	check(false, "the boss select has a %s row" % text.strip_edges())


func caption() -> String:
	return current_scene.continue_caption.text if current_scene.continue_button != null else "<no CONTINUE>"


# Equal and of one type: a value read back from the file can be anything, and comparing across types is a script error.
func same(a, b) -> bool:
	return typeof(a) == typeof(b) and a == b


# Progress saving (the user, 2026-10-07: "lets add progress saving"): the save follows the story run and never the boss
# select's practice. Entering a fight, a phase or Jordan's room makes it the checkpoint, a win moves it on to the next
# fight at once, the menu's CONTINUE opens it with its intro, NEW GAME over it asks first, the champion ending finishes
# the run, a file that can't be used is no save, and the volume is kept in it.
func test_progress_save() -> void:
	var progress: Node = root.get_node("GameProgress")
	var bus := AudioServer.get_bus_index("Master")

	log_p("-- no save")
	check(not progress.has_resume() and saved_file().is_empty(), "a first run has nothing to continue, and no file")
	var menu := await open_menu()
	check(menu.continue_button == null and menu.get_node_or_null("ContinueButton") == null, "the menu has no CONTINUE")
	check(focus_owner() == menu.start_game_button, "NEW GAME has the focus (%s)" % focus_name())
	check(menu.get_node("TitleLogo").position.y == 84.0, "and the title is where it always was")

	log_p("-- a file that can't be used is no save")
	var unusable := [
		["an unknown version", {"version": 99}],
		["a version that isn't a number", {"version": "1"}],
		["a scene that isn't there", {"checkpoint": "res://Scenes/Bosses/NoSuchBossFightScene.tscn"}],
		["a scene that isn't a checkpoint", {"checkpoint": MENU_SCENE}],
		["a phase on the wrong fight", {"phase": "greyson"}],
		["a phase it doesn't know", {"checkpoint": LIAM_FIGHT, "phase": "bixby"}],
		["a checkpoint that isn't text", {"checkpoint": 8}],
	]
	for case in unusable:
		write_progress(case[1])
		progress.load_save()
		check(not progress.has_resume(), "%s: nothing to continue" % case[0])
	var garbled := FileAccess.open(TEST_PROGRESS_PATH, FileAccess.WRITE)
	garbled.store_string("[meta\nversion=1\n[progress]\ncheckpoint=\"res://Scenes/Bosses/CarterBo")
	garbled.close()
	progress.load_save()
	check(not progress.has_resume() and not progress.saved_finished, "a file that doesn't parse: no save at all")
	menu = await open_menu()
	check(menu.continue_button == null and focus_owner() == menu.start_game_button, "the menu treats it as a first run: no CONTINUE, NEW GAME focused")
	tap_key(KEY_ENTER)
	check(await wait_for_scene(INTRO_SCENE), "and NEW GAME asks nothing, straight into the intro")
	var file := saved_file()
	check(same(file.get("version"), 1) and same(file.get("checkpoint"), "") and same(file.get("cleared"), 0), "the broken file is written over by a good one (%s)" % [file])

	log_p("-- the round trip: FIGHT 07 entered, won, and continued from the menu")
	progress.start_new_run()
	check(progress.saving_run, "NEW GAME starts the run the save follows")
	await open_scene(LIAM_FIGHT)
	file = saved_file()
	check(same(file.get("version"), 1) and same(file.get("checkpoint"), LIAM_FIGHT) and same(file.get("phase"), "") and same(file.get("finished"), false), "entering FIGHT 07 makes it the checkpoint (%s)" % [file])
	progress.next_boss_scene = progress.next_fight_after(LIAM_FIGHT)
	await open_scene(VICTORY_SCENE)
	file = saved_file()
	check(same(file.get("checkpoint"), CARTER_FIGHT) and same(file.get("cleared"), 7), "its win moves the checkpoint on to FIGHT 08 at once, 7 cleared (%s)" % [file])
	await wait(45)
	tap_key(KEY_ENTER)
	check(await wait_for_scene(CARTER_FIGHT, 600), "NEXT BOSS opens Carter's fight")
	await wait(3)
	file = saved_file()
	check(same(file.get("checkpoint"), CARTER_FIGHT) and same(file.get("cleared"), 7), "and the save still says FIGHT 08, 7 cleared (%s)" % [file])
	await open_scene(MENU_SCENE)
	menu = current_scene
	var cont: Button = menu.continue_button
	check(cont != null and cont.text == "CONTINUE" and caption() == "VS CARTER", "the menu offers CONTINUE, VS CARTER (%s)" % caption())
	if cont == null:
		return
	check(focus_owner() == null, "nothing has the focus while the menu fades in (%s)" % focus_name())
	await wait(45)
	check(focus_owner() == cont, "then CONTINUE has it (%s)" % focus_name())
	check(cont.get_rect() == Rect2(156, 274, 480, 126) and menu.get_node("TitleLogo").position.y == 52.0, "it sits above NEW GAME, the title risen to make room (%s)" % cont.get_rect())
	var start: Button = menu.start_game_button
	check(cont.theme_type_variation == start.theme_type_variation and (cont.get_theme_stylebox("normal") as StyleBoxTexture).texture == (start.get_theme_stylebox("normal") as StyleBoxTexture).texture, "in NEW GAME's art and font")
	check(start.get_rect() == Rect2(156, 420, 480, 126) and menu.controls_button.get_rect() == Rect2(156, 566, 480, 126), "and NEW GAME and CONTROLS haven't moved")
	tap_key(KEY_DOWN)
	await wait(1)
	check(focus_owner() == start, "down -> NEW GAME (%s)" % focus_name())
	tap_button(JOY_BUTTON_DPAD_DOWN)
	await wait(1)
	check(focus_owner() == menu.controls_button, "the d-pad -> CONTROLS (%s)" % focus_name())
	check(cont.get_theme_stylebox("focus") is StyleBoxFlat, "on a pad CONTINUE shows its focus like the rest")
	tap_button(JOY_BUTTON_DPAD_UP)
	await wait(1)
	tap_key(KEY_UP)
	await wait(1)
	check(focus_owner() == cont, "and back up to CONTINUE (%s)" % focus_name())
	tap_key(KEY_ENTER)
	check(await wait_for_scene(CARTER_FIGHT, 600), "CONTINUE opens Carter's fight")
	await wait(3)
	check(progress.fight_index == 7 and progress.bosses_cleared == 7 and progress.saving_run, "as FIGHT 08, 7 cleared, the save still following the run (%d, %d)" % [progress.fight_index, progress.bosses_cleared])
	check(await wait_frames_for(func() -> bool: return fight_player() != null and fight_player().is_talking, 120), "with its intro, holding the player as arriving there does")

	log_p("-- a phase checkpoint: Liam's half of FIGHT 07")
	progress.start_new_run()
	await open_scene(LIAM_FIGHT)
	check(same(saved_file().get("checkpoint"), LIAM_FIGHT) and same(saved_file().get("phase"), ""), "FIGHT 07 entered at Bixby")
	await open_scene(MENU_SCENE)
	progress.start_at_liam = true
	await open_scene(LIAM_FIGHT)
	check(await wait_frames_for(func() -> bool: return boss_with_script(LIAM_SCRIPT) != null, 3000), "Liam takes the fight over")
	file = saved_file()
	check(same(file.get("checkpoint"), LIAM_FIGHT) and same(file.get("phase"), "liam"), "and his takeover makes his half the checkpoint (%s)" % [file])
	var takeover_scene := current_scene.get_instance_id()
	await restart_from_pause()
	check(await wait_frames_for(func() -> bool: return current_scene != null and current_scene.get_instance_id() != takeover_scene and boss_with_script(LIAM_SCRIPT) != null, 900), "RESTART FIGHT in his half opens his half again")
	check(same(saved_file().get("checkpoint"), LIAM_FIGHT) and same(saved_file().get("phase"), "liam"), "and the checkpoint stays his half (%s)" % saved_file().get("phase"))
	await open_scene(MENU_SCENE)
	await open_scene(LIAM_FIGHT)
	await wait(10)
	check(same(saved_file().get("phase"), "liam"), "the fight's scene opened from Bixby again doesn't put it back (%s)" % saved_file().get("phase"))
	menu = await open_menu()
	check(caption() == "VS LIAM" and focus_owner() == menu.continue_button, "CONTINUE says VS LIAM (%s)" % caption())
	tap_key(KEY_ENTER)
	check(await wait_for_scene(LIAM_FIGHT, 600), "and opens FIGHT 07")
	check(await wait_frames_for(func() -> bool: return boss_with_script(LIAM_SCRIPT) != null, 3000), "in Liam's half")

	log_p("-- a phase checkpoint: Greyson's half of FIGHT 06")
	progress.start_new_run()
	progress.start_at_greyson = true
	await open_scene(COMPUTAH_FIGHT)
	check(await wait_frames_for(func() -> bool: return greyson_in_fight() != null, 900), "Greyson takes FIGHT 06 over")
	file = saved_file()
	check(same(file.get("checkpoint"), COMPUTAH_FIGHT) and same(file.get("phase"), "greyson"), "and his half is the checkpoint (%s)" % [file])
	menu = await open_menu()
	check(caption() == "VS GREYSON", "CONTINUE says VS GREYSON (%s)" % caption())
	tap_key(KEY_ENTER)
	check(await wait_for_scene(COMPUTAH_FIGHT, 600), "and opens FIGHT 06")
	check(await wait_frames_for(func() -> bool: return greyson_in_fight() != null, 900) and current_scene.get_node(COMPUTAH_BODY).defeated, "in Greyson's half, Computah already down")

	log_p("-- Jordan's room and his last phase")
	progress.start_new_run()
	await open_scene(FINALE_ROOM)
	check(same(saved_file().get("checkpoint"), FINALE_ROOM), "Jordan's room is a checkpoint (%s)" % saved_file().get("checkpoint"))
	menu = await open_menu()
	check(caption() == "THE FINALE", "CONTINUE says THE FINALE (%s)" % caption())
	tap_key(KEY_ENTER)
	check(await wait_for_scene(FINALE_ROOM, 600), "and opens the room")
	await wait(3)
	check(current_scene.beat == &"arrive", "from the player walking in (%s)" % current_scene.beat)
	await open_scene(GOD_FIGHT)
	check(same(saved_file().get("checkpoint"), GOD_FIGHT), "the Puppet Master is a checkpoint (%s)" % saved_file().get("checkpoint"))
	menu = await open_menu()
	check(caption() == "VS GOD JORDAN", "CONTINUE says VS GOD JORDAN (%s)" % caption())
	tap_key(KEY_ENTER)
	check(await wait_for_scene(GOD_FIGHT, 600), "and opens his last phase")
	await wait(3)
	check(progress.fight_index == 9 and progress.saving_run, "as FIGHT 10 (%d)" % progress.fight_index)

	log_p("-- the champion ending finishes the run")
	await open_scene(ENDING_SCENE)
	file = saved_file()
	check(same(file.get("finished"), true) and same(file.get("checkpoint"), "") and not progress.has_resume(), "reaching it marks the save finished, with nothing left to continue (%s)" % [file])
	menu = await open_menu()
	check(menu.continue_button == null and focus_owner() == menu.start_game_button and menu.get_node("TitleLogo").position.y == 84.0, "the menu is a first run's again: no CONTINUE, NEW GAME focused")
	tap_key(KEY_ENTER)
	check(await wait_for_scene(INTRO_SCENE), "and NEW GAME asks nothing, there being no progress to lose")
	file = saved_file()
	check(same(file.get("finished"), true) and same(file.get("checkpoint"), "") and same(file.get("cleared"), 0), "the new run keeps the finish (%s)" % [file])

	log_p("-- the boss select is practice")
	write_progress({})
	progress.load_save()
	var before := saved_bytes()
	await open_menu()
	press_row("2  MASON")
	check(await wait_for_scene(MASON_FIGHT, 600), "the MASON row opens his fight")
	await wait(3)
	check(not progress.saving_run and saved_bytes() == before, "and leaves the save alone")
	progress.next_boss_scene = progress.next_fight_after(MASON_FIGHT)
	await open_scene(VICTORY_SCENE)
	await wait(45)
	tap_key(KEY_ENTER)
	check(await wait_for_scene(JOSH_FIGHT, 600), "its win's NEXT BOSS opens Josh's")
	await wait(3)
	check(saved_bytes() == before, "and neither the win nor the fight it chains on to touch it")
	await open_menu()
	press_row("    LIAM")
	check(await wait_for_scene(LIAM_FIGHT, 600) and await wait_frames_for(func() -> bool: return boss_with_script(LIAM_SCRIPT) != null, 3000), "the LIAM row opens Liam's half")
	check(saved_bytes() == before, "and his takeover leaves it alone too")
	await open_menu()
	press_row("    ENDING")
	check(await wait_for_scene(ENDING_SCENE, 600), "the ENDING row opens the ending")
	await wait(3)
	check(saved_bytes() == before and not progress.saved_finished, "which doesn't finish the game")

	log_p("-- NEW GAME over a run asks first")
	await open_scene(MENU_SCENE)
	menu = current_scene
	start = menu.start_game_button
	check(caption() == "VS CARTER" and menu.confirm != null, "the run at FIGHT 08 is still there to continue (%s)" % caption())
	if menu.confirm == null:
		return
	# A mouse click lands while the menu is still fading in, before anything has the focus.
	start.pressed.emit()
	await wait(45)
	check(menu.confirm.visible and focus_owner() == menu.confirm_back_button, "a click on NEW GAME as the menu fades in asks, and the fade-in leaves the focus on BACK (%s)" % focus_name())
	tap_key(KEY_ESCAPE)
	await wait(2)
	check(not menu.confirm.visible and focus_owner() == start, "put away, the focus is on NEW GAME (%s)" % focus_name())
	tap_key(KEY_ENTER)
	await wait(2)
	check(current_scene == menu and menu.confirm.visible, "NEW GAME asks rather than starting")
	var message: Label = menu.confirm.find_child("Message", true, false)
	check(message != null and message.text == CONFIRM_TEXT, "\"%s\"" % (message.text.replace("\n", " ") if message else "<none>"))
	check(focus_owner() == menu.confirm_back_button and menu.confirm_back_button.text == "BACK" and menu.confirm_ok_button.text == "START OVER", "BACK has the focus, START OVER beside it (%s)" % focus_name())
	check((menu.confirm_ok_button.get_theme_stylebox("normal") as StyleBoxTexture).texture == (start.get_theme_stylebox("normal") as StyleBoxTexture).texture, "both in the menu's own button art")
	tap_key(KEY_ENTER)
	await wait(2)
	check(not menu.confirm.visible and focus_owner() == start and saved_bytes() == before, "BACK puts it away, the focus on NEW GAME and the save as it was (%s)" % focus_name())
	tap_key(KEY_ENTER)
	await wait(2)
	tap_button(JOY_BUTTON_B)
	await wait(2)
	check(not menu.confirm.visible and focus_owner() == start, "B backs out of it (%s)" % focus_name())
	tap_key(KEY_ENTER)
	await wait(2)
	tap_key(KEY_ESCAPE)
	await wait(2)
	check(not menu.confirm.visible and focus_owner() == start and current_scene == menu and saved_bytes() == before, "and so does Escape, still on the menu with the save as it was")
	tap_button(JOY_BUTTON_A)
	await wait(2)
	check(menu.confirm.visible and focus_owner() == menu.confirm_back_button, "A on NEW GAME asks the same (%s)" % focus_name())
	check(menu.confirm_back_button.get_theme_stylebox("focus") is StyleBoxFlat, "with the focus showing on a pad")
	tap_button(JOY_BUTTON_DPAD_RIGHT)
	await wait(1)
	check(focus_owner() == menu.confirm_ok_button, "right -> START OVER (%s)" % focus_name())
	tap_button(JOY_BUTTON_DPAD_UP)
	await wait(1)
	tap_button(JOY_BUTTON_DPAD_DOWN)
	await wait(1)
	check(focus_owner() == menu.confirm_ok_button, "up and down stay in the question (%s)" % focus_name())
	tap_button(JOY_BUTTON_DPAD_LEFT)
	await wait(1)
	check(focus_owner() == menu.confirm_back_button, "left -> BACK (%s)" % focus_name())
	tap_button(JOY_BUTTON_DPAD_RIGHT)
	await wait(1)
	tap_button(JOY_BUTTON_A)
	check(await wait_for_scene(INTRO_SCENE), "START OVER starts the new run")
	file = saved_file()
	check(same(file.get("checkpoint"), "") and same(file.get("cleared"), 0) and same(file.get("finished"), false) and progress.saving_run and not progress.has_resume(), "on a reset save (%s)" % [file])
	menu = await open_menu()
	check(menu.continue_button == null, "and the menu has no CONTINUE until it reaches a fight")

	log_p("-- the volume is kept")
	menu.volume_slider.value = 0.4
	check(is_equal_approx(saved_file().get("volume", -1.0), 0.4), "the menu's slider writes it at once (%s)" % saved_file().get("volume", -1.0))
	AudioServer.set_bus_volume_db(bus, 0.0)
	progress.load_save()
	check(absf(db_to_linear(AudioServer.get_bus_volume_db(bus)) - 0.4) < 0.001 and not AudioServer.is_bus_mute(bus), "the next launch puts it back on the Master bus (%.3f)" % db_to_linear(AudioServer.get_bus_volume_db(bus)))
	menu = await open_menu()
	check(absf(menu.volume_slider.value - 0.4) < 0.001, "where the menu's slider shows it (%.3f)" % menu.volume_slider.value)
	menu.volume_slider.value = 0.0
	check(same(saved_file().get("volume", -1.0), 0.0) and AudioServer.is_bus_mute(bus), "all the way down mutes the bus and is kept as 0")
	AudioServer.set_bus_mute(bus, false)
	progress.load_save()
	check(AudioServer.is_bus_mute(bus), "and comes back muted")
	await load_quiet_fight()
	var pause: Node = pause_menu()
	pause.open()
	await wait(2)
	pause.volume_slider.value = 0.7
	check(absf(saved_file().get("volume", -1.0) - 0.7) < 0.001 and not AudioServer.is_bus_mute(bus), "the pause screen's slider is the same setting, written at once (%s)" % saved_file().get("volume", -1.0))
	pause.close()
	await past_resume_grace(pause)
	progress.start_new_run()
	check(absf(saved_file().get("volume", -1.0) - 0.7) < 0.001, "and a progress write keeps it (%s)" % saved_file().get("volume", -1.0))

	log_p("-- the player's own save is out of a check's reach")
	progress.save_path = progress.SAVE_PATH
	check(not progress._save_reachable(), "under a --script check the real save.cfg is never read or written")
	progress.save_path = TEST_PROGRESS_PATH

	AudioServer.set_bus_mute(bus, false)
	AudioServer.set_bus_volume_db(bus, 0.0)
	progress.reset_progress()


# ------------------------------------------------------------------ retry_skip

# The fights retry_skip restarts: plain ones, and the ones whose lines set the ring up as they go - Mason's, Danny's, and
# Matt's, who pulls out his doll Hong - which the skip has to leave the way the lines would have. The takeovers are
# restart_phase's, and every fight's RETRY is defeat_retry's.
const SKIP_CASES := [
	"res://Scenes/Bosses/BurakBossFightScene.tscn",
	"res://Scenes/Bosses/MasonBossFightScene.tscn",
	"res://Scenes/Bosses/EricBossFightScene.tscn",
	"res://Scenes/Bosses/DannyBossFightScene.tscn",
	"res://Scenes/Bosses/MattBossFightScene.tscn",
]
const MATT_FIGHT := "res://Scenes/Bosses/MattBossFightScene.tscn"
const MATT_SCRIPT := "res://Scripts/MattScript.gd"


# The state a fight's entrance is driven from.
func fight_intro() -> Node:
	for node in current_scene.find_children("*", "Node", true, false):
		if node.has_method(&"skip_to_fight"):
			return node
	return null


func lines_showing() -> bool:
	var balloon := find_balloon()
	return balloon != null and balloon.is_inside_tree() and balloon.balloon.visible


# RETRY and RESTART FIGHT straight to the fight (the 2026-10-07 playtest: a retry replayed every pre-fight line and the
# VS card). Each fight entered for the first time plays its lines; its RESTART FIGHT lands on the fight within
# RETRY_FREE_FRAMES with nothing pressed, no line and no skip hint ever shown, its intro cut the way a held skip cuts it,
# the skip spent and his theme playing (Matt's started once and his doll put away), and the fight is on; and entered
# again from the boss select it plays its lines again.
func test_retry_skip() -> void:
	var progress: Node = root.get_node("GameProgress")
	progress.playtest_invincible = false
	var full_health: int = load("res://Scripts/PlayerHealthArtLayout.gd").CONTAINERS * 2
	for scene in SKIP_CASES:
		log_p("-- %s" % scene.get_file())
		progress.reset_progress()
		await load_scene(scene)
		check(await wait_frames_for(lines_showing, 1800) and fight_player().is_talking, "entered for the first time, its lines come up, holding the player")
		check(await read_into_fight(), "read through, the fight lets go of them")
		var before := current_scene.get_instance_id()
		await restart_from_pause()
		check(await wait_frames_for(func() -> bool: return current_scene != null and current_scene.get_instance_id() != before and current_scene.scene_file_path == scene, 600), "RESTART FIGHT opens it again")
		var handed: Array = await free_without_presses(RETRY_FREE_FRAMES + RETRY_RUN_FRAMES + 30)
		check(handed[0] >= 0 and handed[0] <= RETRY_FREE_FRAMES and handed[1] == 0 and handed[2] == 0, "straight to the fight with nothing pressed: the player free from frame %d (at most %d), no line (%d frames) and no skip hint (%d)" % [handed[0], RETRY_FREE_FRAMES, handed[1], handed[2]])
		var intro := fight_intro()
		check(intro != null and intro.cut, "its intro cut the way a held skip cuts it")
		check(progress.intro_skip_scene == "", "the skip spent (%s)" % progress.intro_skip_scene)
		# Some themes start on the card's hand-over to the fight (Mason's), as they do after the lines.
		var music := current_scene.find_children("MusicPlayer", "AudioStreamPlayer", true, false)
		check(await wait_frames_for(func() -> bool: return music.any(func(player: AudioStreamPlayer) -> bool: return player.playing), 300), "his theme playing")
		if scene == MATT_FIGHT:
			var matt: Node = boss_with_script(MATT_SCRIPT)
			check(matt.music_starts == 1, "started once (%d)" % matt.music_starts)
			check(current_scene.find_child("Hong", true, false) == null, "and Hong put away")
		check(await boss_lands_hit(full_health), "and the fight is on: a blow lands on them standing still")
		var index: int = progress.FIGHT_SCENES.find(scene)
		await open_menu()
		press_row("%d  %s" % [index + 1, progress.BOSSES[index]["name"]])
		check(await wait_for_scene(scene, 600), "the boss select's row opens it")
		check(await wait_frames_for(lines_showing, 1800), "and its lines play again")
	progress.reset_progress()


# ------------------------------------------------------------------ loss_lines

# FightOutro.LOSS_LINE_INPUT_LOCK, written out rather than read back.
const LOSS_LOCK_MS := 300
const CARTER_SCRIPT := "res://Scripts/CarterAkumaScript.gd"
# Where his pose stands him (CarterStateMachine.ARENA_CENTRE).
const CARTER_CENTRE := Vector2(959, 540)


# Real time: the balloon's lock is on the wall clock.
func wait_real(msec: int) -> void:
	var until := Time.get_ticks_msec() + msec
	while Time.get_ticks_msec() < until:
		await process_frame


# Eric's player_lost and Carter's, written out rather than read back.
const ERIC_LOSS_LINES := ["Ha! The server stays pure for another day.", "Log off, and don't come back."]
const CARTER_LOSS_LINES := ["Wretched weakling, you will never make it to Jordan."]


func same_lines(seen: Array[String], expected: Array) -> bool:
	if seen.size() != expected.size():
		return false
	for i in seen.size():
		if seen[i] != expected[i]:
			return false
	return true


# What a press on the loss lines can change: the line up ("<gone>" once they are taken down), whether it is still
# typing, and how many lines have come up so far.
# Untyped: it is asked about a balloon that may have been freed.
func loss_line_state(balloon, shown: Array[String]) -> Array:
	if not is_instance_valid(balloon) or balloon.is_queued_for_deletion() or balloon.dialogue_line == null:
		return ["<gone>", false, shown.size()]
	return [balloon.dialogue_line.text, balloon.dialogue_label.is_typing, shown.size()]


# Whether `after` is exactly one step on from `before`: a line still typing finished, the next line up, or the last one
# taken down with the outro leaving.
func one_step(before: Array, after: Array, outro: Node) -> bool:
	if before[1]:
		return after[0] == before[0] and not after[1] and after[2] == before[2]
	if after[0] == "<gone>":
		return after[2] == before[2] and outro.leaving
	return after[2] == before[2] + 1 and after[0] != before[0]


# The loss lines read to their end the way an eager player reads them: a fresh A as soon as each line's lock is past,
# every press exactly one step. The presses it took, -1 at the first press that wasn't one step.
func read_loss_lines(outro: Node, shown: Array[String]) -> int:
	var presses := 0
	while not outro.leaving and presses < 20:
		await wait_real(LOSS_LOCK_MS + 50)
		var balloon = find_balloon()
		var before := loss_line_state(balloon, shown)
		tap_button(JOY_BUTTON_A)
		presses += 1
		await wait(2)
		var after := loss_line_state(balloon, shown)
		if not one_step(before, after, outro):
			log_p("not one step: %s -> %s" % [before, after])
			return -1
	return presses


# The loss lines on the way back to the fight (the 2026-10-07 playtest: each death cost 6 to 9 s before the player was
# back in control, mostly lines locked for 1.2 s each), each on a 0.3 s lock, every one of them seen. Eric's quiet
# fight, lost: a mash inside the 0.3 s lock from the fight being decided does nothing, through the wait for his line and
# into the line's own lock, and neither does a key held across that lock's end, its repeats included; a key going down
# past it moves one step - finishes the typing or moves on a line - and held on past the next lock, its repeats move
# nothing; then a fresh A a step reads his lines to the end, both of them shown in order, the last press fading to
# Defeat. Carter's fight, lost (the user, 2026-10-07: "make carters pose skippable"): the wait for his line is his
# victory pose, ~3.4 s; a press inside the lock and a key held across its end skip nothing; one fresh press past it ends
# the wait with his pose at its end and his line up, which a key held from there past the line's own lock doesn't move,
# and fresh presses read to Defeat. A win's lines keep their 1.2 s lock.
func test_loss_lines() -> void:
	var manager: Node = root.get_node("DialogueManager")
	var shown: Array[String] = []
	var note_line := func(line: RefCounted) -> void: shown.append(line.text)
	manager.got_dialogue.connect(note_line)
	await load_quiet_fight()
	shown.clear()
	var lost_at := Time.get_ticks_msec()
	fight_player().playerHealth = 0
	var mash := 0
	for i in 600:
		if lines_showing():
			break
		# Inside the lock on the wait only: a press past it ends the wait, which the Carter case below is about.
		if i % 4 == 0 and Time.get_ticks_msec() - lost_at < LOSS_LOCK_MS - 50:
			tap_key(KEY_ENTER)
			tap_button(JOY_BUTTON_A)
			mash += 1
		await process_frame
	var balloon := find_balloon()
	check(balloon != null and lines_showing() and mash > 0, "his loss lines come up through a mash inside the lock (%d presses)" % mash)
	if balloon == null:
		return
	var outro: Node = root.get_node(^"FightOutro")
	var first: String = balloon.dialogue_line.text
	check(is_equal_approx(balloon.input_lock_time, LOSS_LOCK_MS / 1000.0), "each line on a %.1f s lock" % balloon.input_lock_time)
	tap_key(KEY_ENTER)
	tap_button(JOY_BUTTON_A)
	tap_button(JOY_BUTTON_B)
	await wait(2)
	check(is_instance_valid(balloon) and balloon.dialogue_line.text == first and shown.size() == 1 and not outro.leaving, "a press inside the lock is eaten")
	send([key_event(KEY_ENTER, true)])
	await wait_real(LOSS_LOCK_MS + 50)
	for i in 5:
		send([key_event(KEY_ENTER, true, true)])
		await wait(2)
	send([key_event(KEY_ENTER, false)])
	await wait(2)
	check(is_instance_valid(balloon) and balloon.dialogue_line.text == first and shown.size() == 1 and not outro.leaving, "a key held across its end moves nothing, its repeats included")
	await wait_real(LOSS_LOCK_MS + 50)
	var before := loss_line_state(balloon, shown)
	send([key_event(KEY_ENTER, true)])
	await wait(2)
	var stepped := loss_line_state(balloon, shown)
	await wait_real(LOSS_LOCK_MS + 50)
	for i in 5:
		send([key_event(KEY_ENTER, true, true)])
		await wait(2)
	send([key_event(KEY_ENTER, false)])
	await wait(2)
	var held_on := loss_line_state(balloon, shown)
	check(one_step(before, stepped, outro) and held_on[0] == stepped[0] and held_on[2] == stepped[2] and not outro.leaving, "a key going down past it moves one step (%s -> %s), and held on past the next lock its repeats move nothing (%s)" % [before, stepped, held_on])
	var presses := await read_loss_lines(outro, shown)
	check(presses > 0, "then a fresh A a step reads the rest (%d presses)" % presses)
	check(same_lines(shown, ERIC_LOSS_LINES), "both his lines shown, in order (%s)" % [shown])
	check(outro.leaving and outro.destination == DEFEAT_SCENE, "and the last one's press fades to Defeat")
	check(await wait_for_scene(DEFEAT_SCENE, 600), "which comes up")
	log_p("lost to the Defeat screen in %d ms of wall clock (fixed frames: the waits are game time)" % (Time.get_ticks_msec() - lost_at))

	log_p("-- Carter's pose before his line")
	root.get_node("GameProgress").reset_progress()
	await load_scene(CARTER_FIGHT)
	check(await read_into_fight(), "his fight lets go of the player")
	shown.clear()
	fight_player().playerHealth = 0
	await wait(2)
	outro = root.get_node_or_null(^"FightOutro")
	var carter: Node = boss_with_script(CARTER_SCRIPT)
	var pose: Node = carter.state_machine.states["Victory"]
	check(outro != null and outro.line_delay_skippable and carter.state_machine.current_state == pose and not lines_showing(), "his pose is up, the wait for his line on")
	if outro == null:
		return
	tap_key(KEY_ENTER)
	tap_button(JOY_BUTTON_A)
	await wait(2)
	check(outro.line_delay_skippable and not pose.looked and not lines_showing(), "a press inside the lock is eaten")
	send([key_event(KEY_ENTER, true)])
	# Real time past the lock with no frame run, so the pose is still at its start.
	OS.delay_msec(LOSS_LOCK_MS + 50)
	for i in 5:
		send([key_event(KEY_ENTER, true, true)])
		await wait(1)
	send([key_event(KEY_ENTER, false)])
	await wait(1)
	check(outro.line_delay_skippable and not pose.looked and not lines_showing(), "a key held across its end skips nothing, its repeats included")
	tap_button(JOY_BUTTON_A)
	check(not outro.line_delay_skippable, "one fresh press past it ends the wait")
	check(pose.looked and pose.lit and pose.ignited and carter.current_anim == &"look_back_hold" and carter.global_position == CARTER_CENTRE, "with his pose at its end: in the middle, the mark lit, the light up, his head round (%s)" % carter.current_anim)
	check(await wait_frames_for(lines_showing, 10), "and his line up")
	balloon = find_balloon()
	before = loss_line_state(balloon, shown)
	send([key_event(KEY_ENTER, true)])
	OS.delay_msec(LOSS_LOCK_MS + 50)
	for i in 5:
		send([key_event(KEY_ENTER, true, true)])
		await wait(1)
	send([key_event(KEY_ENTER, false)])
	await wait(1)
	held_on = loss_line_state(balloon, shown)
	check(held_on[0] == before[0] and held_on[2] == before[2] and not outro.leaving, "a key held from there, down inside the line's own lock, moves nothing past it")
	presses = await read_loss_lines(outro, shown)
	check(presses > 0 and same_lines(shown, CARTER_LOSS_LINES), "fresh presses read his line, a step each (%d presses, %s)" % [presses, shown])
	check(outro.leaving and outro.destination == DEFEAT_SCENE, "into the fade to Defeat")
	check(await wait_for_scene(DEFEAT_SCENE, 600), "which comes up")

	log_p("-- a win's lines")
	await load_quiet_fight()
	load("res://Scripts/FightOutro.gd").finish_fight(self, true)
	check(await wait_frames_for(lines_showing, 600), "his win lines come up")
	balloon = find_balloon()
	check(is_equal_approx(balloon.input_lock_time, 1.2), "on the 1.2 s lock (%.1f s)" % balloon.input_lock_time)
	await wait_real(LOSS_LOCK_MS + 100)
	first = balloon.dialogue_line.text
	tap_button(JOY_BUTTON_A)
	await wait(2)
	check(is_instance_valid(balloon) and balloon.dialogue_line.text == first, "a press past 0.3 s is still inside it")
	manager.got_dialogue.disconnect(note_line)


# ------------------------------------------------------------------ balloon_accept

# Four lines long enough to still be typing a while after they come up.
const ACCEPT_LINE := "line, long enough to still be typing for a good while after it comes up, so that a press lands on it."
const ACCEPT_DIALOGUE := "~ start\nEric: One %s\nEric: Two %s\nEric: Three %s\nEric: Four %s\n=> END"


func line_word(balloon: Node) -> String:
	return balloon.dialogue_line.text.get_slice(" ", 0) if is_instance_valid(balloon) and balloon.dialogue_line != null else "<none>"


# Every dialogue balloon (the 2026-10-07 playtest: A did nothing while a line typed): on a pad A finishes a line still
# typing as B does, and only finishes it; the keyboard's confirm the same, a held key's repeats doing nothing; a held A
# moves on one line and no more. Read in a blank scene, so nothing but the balloon hears the presses.
func test_balloon_accept() -> void:
	var blank := Control.new()
	blank.name = "Blank"
	root.add_child(blank)
	current_scene = blank
	var manager: Node = root.get_node("DialogueManager")
	var ended := [false]
	manager.dialogue_ended.connect(func(_resource: Resource) -> void: ended[0] = true, CONNECT_ONE_SHOT)
	var text := ACCEPT_DIALOGUE % [ACCEPT_LINE, ACCEPT_LINE, ACCEPT_LINE, ACCEPT_LINE]
	var balloon: Node = manager.show_dialogue_balloon(manager.create_resource_from_text(text), "start")
	await wait(4)
	check(line_word(balloon) == "One" and balloon.dialogue_label.is_typing, "the first line is typing")
	tap_button(JOY_BUTTON_A)
	await wait(1)
	check(line_word(balloon) == "One" and not balloon.dialogue_label.is_typing and balloon.dialogue_label.visible_ratio == 1.0, "A finishes it, all of it showing, and stays on it")
	tap_button(JOY_BUTTON_A)
	await wait(3)
	check(line_word(balloon) == "Two" and balloon.dialogue_label.is_typing, "the next A moves on to the second, typing")
	tap_key(KEY_ENTER)
	await wait(1)
	check(line_word(balloon) == "Two" and not balloon.dialogue_label.is_typing, "Enter finishes it the same way")
	for i in 5:
		send([key_event(KEY_ENTER, true, true)])
		await wait(2)
	check(line_word(balloon) == "Two", "and a held Enter's repeats move nothing on")
	send([button_event(JOY_BUTTON_A, true)])
	await wait(3)
	check(line_word(balloon) == "Three" and balloon.dialogue_label.is_typing, "A pressed and held moves on to the third")
	await wait(240)
	check(line_word(balloon) == "Three" and not balloon.dialogue_label.is_typing, "held through its typing, it stays there (%s)" % line_word(balloon))
	send([button_event(JOY_BUTTON_A, false)])
	await wait(1)
	tap_button(JOY_BUTTON_A)
	await wait(3)
	check(line_word(balloon) == "Four" and balloon.dialogue_label.is_typing, "the next A, the fourth")
	tap_button(JOY_BUTTON_B)
	await wait(1)
	check(line_word(balloon) == "Four" and not balloon.dialogue_label.is_typing, "B still finishes a line")
	tap_button(JOY_BUTTON_A)
	await wait(3)
	check(ended[0], "and A ends the dialogue")
	current_scene = null
	blank.queue_free()
	await wait(2)


# ------------------------------------------------------------------ playtest_panel

const BOSS_SELECT_TITLE := "BOSS SELECT (PLAYTEST)"
const BADGE_THEME := "res://Assets/UI/ui_theme.tres"


func has_boss_select(menu: Node) -> bool:
	return menu.find_children("*", "Label", true, false).any(func(label: Label) -> bool: return label.text == BOSS_SELECT_TITLE)


# Everything the fight's boss bars draw, a rect per drawn piece.
func boss_bar_rects() -> Array[Rect2]:
	var rects: Array[Rect2] = []
	for bar in current_scene.find_children("*", "Control", true, false):
		var script: Script = bar.get_script()
		if script == null or script.resource_path != "res://Scripts/BossHealthBarUI.gd":
			continue
		for piece in bar.find_children("*", "Control", true, false):
			if piece.is_visible_in_tree() and piece.size != Vector2.ZERO:
				rects.append(piece.get_global_rect())
	return rects


# The editor is also the playtest build (the user, 2026-10-08: "just need the editor build (which is also the playtest
# build) and the normal build"): run from it, as this suite is, the menu builds the whole boss select - every row,
# whatever the player has beaten, under the playtest's title - with its INVINCIBLE toggle. While INVINCIBLE is on, every
# fight shows a small INVINCIBLE badge in the HUD's font and the skip hint's look, in the top left corner clear of the
# boss bar and the hearts, through a RESTART FIGHT too; nothing else does, and nothing does with it off. An exported
# build's panel is unlock_panel's.
func test_playtest_panel() -> void:
	var progress: Node = root.get_node("GameProgress")
	check(OS.has_feature("editor") and progress.playtest_build and progress.beaten.is_empty(), "run from the editor, this is the playtest build, with nothing beaten")
	var menu := await open_menu()
	check(has_boss_select(menu) and menu.find_children("*", "CheckBox", true, false).size() == 1, "its menu has the boss select under the playtest's title, with its INVINCIBLE toggle")
	check(boss_select_rows() == LADDER_MENU_ROWS, "and every row of it (%d)" % boss_select_rows().size())

	log_p("-- the INVINCIBLE badge")
	progress.playtest_invincible = false
	menu = await open_menu()
	var toggle: CheckBox = menu.find_children("*", "CheckBox", true, false)[0]
	toggle.grab_focus()
	tap_key(KEY_ENTER)
	await wait(1)
	check(progress.playtest_invincible, "the toggle turns it on")
	check(menu.get_node_or_null("InvincibleBadge") == null, "the menu has no badge")
	await load_scene(ERIC_FIGHT)
	var badge_layer: CanvasLayer = current_scene.get_node_or_null("InvincibleBadge")
	check(badge_layer != null, "a fight has the badge")
	if badge_layer != null:
		var badge: Label = badge_layer.get_node("Badge")
		var rect := badge.get_global_rect()
		check(badge.text == "INVINCIBLE" and badge.is_visible_in_tree(), "saying INVINCIBLE")
		check(badge.theme == load(BADGE_THEME) and badge.get_theme_font_size("font_size") == 22, "in the HUD's font, small (%d)" % badge.get_theme_font_size("font_size"))
		check(rect.position.x < 100.0 and rect.position.y < 100.0 and rect.end.x < 400.0 and rect.end.y < 100.0, "in the top left corner (%s)" % rect)
		# Once the fight is on, his bar up.
		await read_into_fight()
		var hp_layout: GDScript = load("res://Scripts/PlayerHealthArtLayout.gd")
		var hearts := Rect2(hp_layout.TRAY_POSITION, hp_layout.TRAY_SIZE)
		var bars := boss_bar_rects()
		check(not bars.is_empty() and bars.all(func(bar: Rect2) -> bool: return not bar.intersects(rect)) and not hearts.intersects(rect), "clear of the boss bar (%d pieces) and the hearts" % bars.size())
	else:
		await read_into_fight()
	var before := current_scene.get_instance_id()
	await restart_from_pause()
	check(await wait_frames_for(func() -> bool: return current_scene != null and current_scene.get_instance_id() != before and current_scene.get_node_or_null("InvincibleBadge") != null, 600), "RESTART FIGHT keeps it")
	await load_scene(DEFEAT_SCENE)
	check(current_scene.get_node_or_null("InvincibleBadge") == null, "the Defeat screen has none")
	progress.playtest_invincible = false
	await load_scene(ERIC_FIGHT)
	check(current_scene.get_node_or_null("InvincibleBadge") == null, "with it off, a fight has none")
	progress.reset_progress()


# ------------------------------------------------------------------ unlock_panel

const NORMAL_TITLE := "BOSS SELECT"


# The boss select's panel on `menu`, null when it wasn't built.
func boss_select_panel(menu: Node) -> Node:
	for label in menu.find_children("*", "Label", true, false):
		if label.text.begins_with(NORMAL_TITLE):
			return label.get_parent().get_parent().get_parent()
	return null


# Every word the panel shows: its title, its toggle and its rows.
func panel_texts(menu: Node) -> Array[String]:
	var texts: Array[String] = []
	var panel := boss_select_panel(menu)
	if panel == null:
		return texts
	for node in panel.find_children("*", "", true, false):
		if node is Label or node is Button:
			texts.append(node.text)
	return texts


# The names a boss select must not show while the save says they are still to come: every unbeaten fight's, and the halves,
# the finale, the god and the ending until theirs are; and nothing of the playtest's.
func unbeaten_words(progress: Node) -> Array[String]:
	var words: Array[String] = ["PLAYTEST", "INVINCIBLE"]
	for boss in progress.BOSSES:
		if not progress.has_beaten(boss["scene"]):
			for word in boss["name"].split(" ", false):
				if word != "&":
					words.append(word)
	if not progress.has_beaten(COMPUTAH_FIGHT):
		words.append("GREYSON")
	if not progress.has_beaten("res://Scenes/Bosses/JordanBossFightScene.tscn"):
		words.append("FINALE")
	if not progress.has_beaten(GOD_FIGHT):
		words.append("GOD")
	if not progress.saved_finished:
		words.append("ENDING")
	return words


func shows_unbeaten(menu: Node, progress: Node) -> Array[String]:
	var found: Array[String] = []
	for text in panel_texts(menu):
		for word in unbeaten_words(progress):
			if text.contains(word):
				found.append("%s in \"%s\"" % [word, text.strip_edges()])
	return found


func set_beaten(progress: Node, scenes: Array) -> void:
	progress.beaten.clear()
	for scene in scenes:
		progress.beaten.append(scene)


func saved_unlocks() -> Variant:
	var cfg := ConfigFile.new()
	if cfg.load(TEST_PROGRESS_PATH) != OK or not cfg.has_section_key("unlocks", "beaten"):
		return null
	return cfg.get_value("unlocks", "beaten")


# A fight of the story run won the way the game wins one: read into, the win handed to FightOutro with the next fight
# named as his defeat names it, his lines read with Enter, up to the Victory screen. Whether it got there.
func win_story_fight(scene: String) -> bool:
	if not await read_into_fight():
		return false
	var progress: Node = root.get_node("GameProgress")
	progress.next_boss_scene = progress.next_fight_after(scene)
	load("res://Scripts/FightOutro.gd").finish_fight(self, true)
	var until := Time.get_ticks_msec() + 60000
	var i := 0
	while Time.get_ticks_msec() < until:
		if current_scene != null and current_scene.scene_file_path == VICTORY_SCENE:
			return true
		if i % 20 == 10:
			tap_key(KEY_ENTER)
		i += 1
		await process_frame
	return false


# An exported build's boss select (the user, 2026-10-08: "only if theyve beat the boss. They shouldnt be able to see the
# name of the next boss in this menu and should only show bosses theyve already beat"), seen by turning
# GameProgress.playtest_build off. With nothing beaten there is no panel and the menu's column ends at VOLUME; INVINCIBLE
# can't be had, set or not, and no fight wears the badge. Fights 1 to 3 won in a story run, each through FightOutro to
# its Victory screen and on with NEXT BOSS, are beaten, in the save too, and the panel - titled BOSS SELECT, with no
# toggle - lists exactly those three, no unbeaten name anywhere in it, chained from VOLUME on the d-pad. A row opens its
# fight as practice, and won to its Victory screen that leaves the save byte for byte as it was. The three survive a
# restart (the save read again) and START OVER. Rows come only with what unlocks them: GREYSON and LIAM with fights 6 and
# 7, FINALE with Jordan's kaiju, GOD once his last phase is won and ENDING once the game is finished, and never a name
# before. A save from before the unlocks reads its cleared fights as beaten (a finished one all of them), one with them
# reads them as they are, and what in it isn't a fight is dropped.
func test_unlock_panel() -> void:
	var progress: Node = root.get_node("GameProgress")
	progress.playtest_build = false

	log_p("-- nothing beaten")
	check(progress.beaten.is_empty(), "a first run has beaten nothing")
	var menu := await open_menu()
	check(boss_select_panel(menu) == null and boss_select_rows().is_empty() and menu.find_children("*", "CheckBox", true, false).is_empty(), "the menu has no boss select at all")
	var slider: HSlider = menu.volume_slider
	slider.grab_focus()
	tap_button(JOY_BUTTON_DPAD_DOWN)
	await wait(1)
	check(slider.focus_neighbor_bottom.is_empty() and focus_owner() == slider, "and its column ends at VOLUME (%s)" % focus_name())

	log_p("-- INVINCIBLE can't be had")
	progress.playtest_invincible = true
	check(not progress.playtest_invincible, "turned on, it still reads off")
	await load_scene(ERIC_FIGHT)
	check(current_scene.get_node_or_null("InvincibleBadge") == null, "and a fight has no badge")
	progress.playtest_invincible = false

	log_p("-- fights 1 to 3 won in a story run")
	progress.start_new_run()
	await open_scene(progress.FIGHT_SCENES[0])
	for i in 3:
		var scene: String = progress.FIGHT_SCENES[i]
		check(await win_story_fight(scene), "FIGHT %02d won, to its Victory screen" % (i + 1))
		if i < 2:
			await wait(45)
			tap_key(KEY_ENTER)
			check(await wait_for_scene(progress.FIGHT_SCENES[i + 1], 600), "NEXT BOSS opens FIGHT %02d" % (i + 2))
	var three: Array = progress.FIGHT_SCENES.slice(0, 3)
	check(same_lines(progress.beaten, three), "those three are beaten %s" % [progress.beaten])
	var unlocks = saved_unlocks()
	check(unlocks is Array and unlocks == three, "and the save has them under [unlocks] (%s)" % [unlocks])
	menu = await open_menu()
	check(boss_select_rows() == ["1  BURAK", "2  MASON", "3  JOSH"], "the boss select lists exactly them %s" % [boss_select_rows()])
	check(panel_texts(menu).has(NORMAL_TITLE) and menu.find_children("*", "CheckBox", true, false).is_empty(), "titled BOSS SELECT, with no INVINCIBLE toggle %s" % [panel_texts(menu)])
	check(shows_unbeaten(menu, progress).is_empty(), "no name it hasn't earned anywhere in it %s" % [shows_unbeaten(menu, progress)])
	var panel: Control = boss_select_panel(menu)
	check(panel.position == Vector2(156, 830) and panel.size.x == 664.0 and panel.get_rect().end.y < 1070.0, "in the playtest panel's place, as tall as its rows (%s)" % panel.get_rect())
	menu.volume_slider.grab_focus()
	tap_button(JOY_BUTTON_DPAD_DOWN)
	await wait(1)
	var first: Control = focus_owner()
	tap_button(JOY_BUTTON_DPAD_DOWN)
	await wait(1)
	var second: Control = focus_owner()
	check(first is Button and first.text == "1  BURAK" and second is Button and second.text == "2  MASON", "the d-pad goes down from VOLUME into it, row by row (%s)" % focus_name())

	log_p("-- practice from it")
	var before := saved_bytes()
	press_row("2  MASON")
	check(await wait_for_scene(MASON_FIGHT, 600), "the MASON row opens his fight")
	await wait(3)
	check(not progress.saving_run and saved_bytes() == before, "as practice: the save untouched")
	check(await win_story_fight(MASON_FIGHT), "won to its Victory screen")
	await wait(3)
	check(saved_bytes() == before and same_lines(progress.beaten, three), "and still untouched, the checkpoint and the unlocks as they were")

	log_p("-- kept across a restart and START OVER")
	progress.beaten.clear()
	progress.load_save()
	check(same_lines(progress.beaten, three), "read again from the save, the three are still beaten")
	menu = await open_menu()
	check(menu.confirm != null, "the run is there to continue, so NEW GAME asks")
	if menu.confirm != null:
		menu.start_game_button.pressed.emit()
		await wait(2)
		menu.confirm_ok_button.pressed.emit()
		check(await wait_for_scene(INTRO_SCENE), "START OVER starts a new run")
	unlocks = saved_unlocks()
	check(not progress.has_resume() and unlocks is Array and unlocks == three, "on a reset save that keeps them (%s)" % [unlocks])
	progress.load_save()
	await open_menu()
	check(boss_select_rows() == ["1  BURAK", "2  MASON", "3  JOSH"], "and the boss select still lists them %s" % [boss_select_rows()])

	log_p("-- the halves and the rest only with what unlocks them")
	var steps := [
		[5, false, false, false, ["1  BURAK", "2  MASON", "3  JOSH", "4  ERIC", "5  DANNY"]],
		[6, false, false, false, ["1  BURAK", "2  MASON", "3  JOSH", "4  ERIC", "5  DANNY", "6  COMPUTAH", "    GREYSON"]],
		[7, false, false, false, ["1  BURAK", "2  MASON", "3  JOSH", "4  ERIC", "5  DANNY", "6  COMPUTAH", "    GREYSON", "7  LIAM & BIXBY", "    LIAM"]],
		[10, false, false, false, LADDER_MENU_ROWS.slice(0, 13)],
		[10, true, false, false, LADDER_MENU_ROWS.slice(0, 14)],
		[10, true, true, false, LADDER_MENU_ROWS],
	]
	for step in steps:
		var scenes: Array = progress.FIGHT_SCENES.slice(0, step[0])
		if step[1]:
			scenes.append(GOD_FIGHT)
		set_beaten(progress, scenes)
		progress.saved_finished = step[2]
		menu = await open_menu()
		check(boss_select_rows() == step[4] and shows_unbeaten(menu, progress).is_empty(), "%d fights%s%s beaten: %s %s" % [step[0], ", the god" if step[1] else "", ", the game finished" if step[2] else "", boss_select_rows(), shows_unbeaten(menu, progress)])
	progress.saved_finished = false

	log_p("-- saves from before the unlocks, and broken ones")
	write_progress({})
	progress.load_save()
	check(same_lines(progress.beaten, progress.FIGHT_SCENES.slice(0, 7)), "a run at FIGHT 08 with 7 cleared and no [unlocks] reads fights 1 to 7 as beaten %s" % [progress.beaten])
	write_progress({"checkpoint": "", "cleared": 0, "finished": true})
	progress.load_save()
	var everything: Array = progress.FIGHT_SCENES.duplicate()
	everything.append(GOD_FIGHT)
	check(same_lines(progress.beaten, everything), "a finished one reads all of them, the god's last phase too (%d)" % progress.beaten.size())
	var cfg := ConfigFile.new()
	cfg.load(TEST_PROGRESS_PATH)
	cfg.set_value("unlocks", "beaten", [])
	cfg.save(TEST_PROGRESS_PATH)
	progress.load_save()
	check(progress.beaten.is_empty(), "one that has [unlocks] reads it as it is, here none")
	cfg.set_value("unlocks", "beaten", ["res://Scenes/Bosses/NoSuchBossFightScene.tscn", 5, progress.FIGHT_SCENES[0], MENU_SCENE])
	cfg.save(TEST_PROGRESS_PATH)
	progress.load_save()
	check(same_lines(progress.beaten, [progress.FIGHT_SCENES[0]]), "and what in it isn't a fight is dropped %s" % [progress.beaten])
	cfg.set_value("unlocks", "beaten", "BURAK")
	cfg.save(TEST_PROGRESS_PATH)
	progress.load_save()
	check(progress.beaten.is_empty() and progress.saved_finished, "a value that isn't a list is none, the rest of the save read")

	progress.playtest_build = true
	progress.beaten.clear()
	progress.reset_progress()


# ------------------------------------------------------------------ victory_menu

const CHEER_PATH := "res://Assets/Audio/SFX/crowd_cheer.wav"


# The Victory screen (the 2026-10-07 playtest: it only went on, and was silent): MAIN MENU beside NEXT BOSS, a copy of it,
# the pair centred where the one button was; NEXT BOSS takes the first focus once the screen is up, and the d-pad moves
# between them with the focus showing on a pad; the crowd cheers once, quietly; MAIN MENU goes to the menu once for two
# presses, and the menu's CONTINUE opens the next fight, which the win had saved, with its lines. With no next fight the
# one button still says MAIN MENU, where it always was.
func test_victory_menu() -> void:
	var progress: Node = root.get_node("GameProgress")
	progress.start_new_run()
	await open_scene(LIAM_FIGHT)
	progress.next_boss_scene = progress.next_fight_after(LIAM_FIGHT)
	await open_scene(VICTORY_SCENE)
	var screen: Control = current_scene
	var next: Button = screen.next_boss_button
	var menu_button: Button = screen.main_menu_button
	check(menu_button != null and menu_button.text == "MAIN MENU" and next.text == "NEXT BOSS", "MAIN MENU is up beside NEXT BOSS")
	if menu_button == null:
		return
	check(menu_button.size == next.size and menu_button.theme_type_variation == next.theme_type_variation and (menu_button.get_theme_stylebox("normal") as StyleBoxTexture).texture == (next.get_theme_stylebox("normal") as StyleBoxTexture).texture, "in its art and size (%s)" % menu_button.size)
	var pair := next.get_rect().merge(menu_button.get_rect())
	check(next.get_rect().position.x < menu_button.get_rect().position.x and next.position.y == 840.0 and menu_button.position.y == 840.0 and is_equal_approx(pair.get_center().x, 960.0), "NEXT BOSS on the left, the pair centred where the one button was (%s)" % pair)
	var cheer: AudioStreamPlayer = screen.get_node_or_null("CheerPlayer")
	check(cheer != null and cheer.playing and cheer.stream.resource_path == CHEER_PATH, "the crowd cheers as it comes up")
	if cheer != null:
		check(cheer.volume_db == -6.0 and (cheer.stream as AudioStreamWAV).loop_mode == AudioStreamWAV.LOOP_DISABLED, "once, at -6 dB (%.1f)" % cheer.volume_db)
	var file := saved_file()
	check(same(file.get("checkpoint"), CARTER_FIGHT) and same(file.get("cleared"), 7), "the win has saved the next fight, FIGHT 08 (%s)" % [file])
	check(focus_owner() == null, "nothing has the focus while it fades in (%s)" % focus_name())
	await wait(45)
	check(focus_owner() == next, "then NEXT BOSS has it (%s)" % focus_name())
	tap_button(JOY_BUTTON_DPAD_RIGHT)
	await wait(1)
	check(focus_owner() == menu_button and menu_button.get_theme_stylebox("focus") is StyleBoxFlat, "right on the d-pad moves it to MAIN MENU, showing on a pad (%s)" % focus_name())
	tap_button(JOY_BUTTON_DPAD_LEFT)
	await wait(1)
	check(focus_owner() == next, "left takes it back (%s)" % focus_name())
	tap_button(JOY_BUTTON_DPAD_RIGHT)
	await wait(1)
	var changes := [0]
	var count_change := func() -> void: changes[0] += 1
	scene_changed.connect(count_change)
	tap_button(JOY_BUTTON_A)
	tap_button(JOY_BUTTON_A)
	var to_menu := await wait_for_scene(MENU_SCENE)
	await wait(10)
	scene_changed.disconnect(count_change)
	check(to_menu and changes[0] == 1, "A on MAIN MENU goes to the menu, once for two presses (%d)" % changes[0])
	await wait(45)
	check(caption() == "VS CARTER" and focus_owner() == current_scene.continue_button, "where CONTINUE says VS CARTER, focused (%s)" % caption())
	tap_key(KEY_ENTER)
	check(await wait_for_scene(CARTER_FIGHT, 600), "and opens Carter's fight")
	await wait(3)
	check(progress.fight_index == 7 and progress.bosses_cleared == 7, "as FIGHT 08, 7 cleared (%d, %d)" % [progress.fight_index, progress.bosses_cleared])
	check(await wait_frames_for(lines_showing, 1800), "with his lines, as arriving there plays them")

	log_p("-- with no next fight")
	progress.next_boss_scene = ""
	await open_scene(VICTORY_SCENE)
	check(current_scene.main_menu_button == null and current_scene.next_boss_button.text == "MAIN MENU" and current_scene.next_boss_button.get_rect() == Rect2(753, 840, 414, 126), "one button, MAIN MENU, where it always was (%s)" % current_scene.next_boss_button.get_rect())
	progress.reset_progress()


# ------------------------------------------------------------------ menu_music

# Real milliseconds: the theme's playback position is on the audio clock.
const MUSIC_WAIT_MS := 400


# The main menu's theme across its CONTROLS screen (the 2026-10-07 playtest: the screen was silent and Back started the
# theme over): the same player plays on through the screen, held by GameProgress, and is the menu's again on Back, still
# playing and further on, the menu's own copy dropped; round again the same. Leaving the menu for anything else stops it,
# and a menu reached any other way starts it from the top, as before; the screen left for anything but the menu stops it
# too.
func test_menu_music() -> void:
	var progress: Node = root.get_node("GameProgress")
	var menu := await open_menu()
	var theme: AudioStreamPlayer = menu.music_player
	check(theme.playing and theme.stream.resource_path.ends_with("main_menu_theme.ogg"), "the menu's theme is playing")
	for trip in 2:
		await wait_real(MUSIC_WAIT_MS)
		var at := theme.get_playback_position()
		menu.controls_button.grab_focus()
		tap_key(KEY_ENTER)
		check(await wait_for_scene(SETTINGS_SCENE), "CONTROLS opens the rebind screen")
		await wait(5)
		check(is_instance_valid(theme) and theme.playing and theme.get_parent() == progress, "the same theme plays on there, held by GameProgress")
		await wait_real(MUSIC_WAIT_MS)
		tap_key(KEY_ESCAPE)
		check(await wait_for_scene(MENU_SCENE), "Back returns to the menu")
		await wait(3)
		menu = current_scene
		var players := menu.find_children("*", "AudioStreamPlayer", true, false)
		check(menu.music_player == theme and theme.get_parent() == menu and theme.name == "MusicPlayer" and theme.playing and players.size() == 1 and players[0] == theme, "where it is the menu's player again, still playing, the only one (%d)" % players.size())
		check(theme.get_playback_position() > at, "never started over: %.2f s in, from %.2f" % [theme.get_playback_position(), at])
		check(progress.carried_music == null, "and nothing is left carried")
		await wait(45)

	log_p("-- leaving the menu stops it, and a menu reached another way starts it over")
	menu.start_game_button.grab_focus()
	tap_key(KEY_ENTER)
	check(await wait_for_scene(INTRO_SCENE), "NEW GAME opens the intro")
	await wait(3)
	check(not is_instance_valid(theme) and progress.carried_music == null, "and the theme is gone with the menu")
	menu = await open_menu()
	check(menu.music_player.playing and menu.music_player.get_playback_position() < 1.0, "a menu opened anew plays it from the top (%.2f)" % menu.music_player.get_playback_position())

	log_p("-- the rebind screen left for anything but the menu")
	menu.controls_button.grab_focus()
	tap_key(KEY_ENTER)
	check(await wait_for_scene(SETTINGS_SCENE), "CONTROLS again")
	var carried: AudioStreamPlayer = progress.carried_music
	await load_scene(VICTORY_SCENE)
	await wait(2)
	check(progress.carried_music == null and not is_instance_valid(carried), "stops it")
	progress.reset_progress()
