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
		_:
			log_p("unknown mode " + mode)
			fails += 1
	DirAccess.remove_absolute(ProjectSettings.globalize_path(TEST_SAVE_PATH))
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
	check(absf(first - 0.52) < 0.0005, "which is still the old straight-across threshold: 52%%, so the first whole percent that moves is 53%% (%.4f)" % first)
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
	for push in [Vector2(0.1, 0.0), Vector2(0.2, 0.1), Vector2(0.3, 0.0), Vector2(0.0, -0.35), Vector2(0.25, 0.25), Vector2(0.36, 0.36)]:
		stick(push.x, push.y)
		check(settings.move_vector() == Vector2.ZERO, "a %s push reads as centred" % push)
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
	check(text.contains("ARROWS to move, Q punches, W dashes") and text.contains("HOLD SHIFT") and text.contains("TAP SHIFT"), "on the keyboard: arrows, Q, W and Shift")
	# The line leads straight into Eric, so it names his mash keys, not attack and dash.
	check(text.contains("Boss goes all dizzy? Follow the prompt to finish him: mash LEFT and RIGHT."), "and Eric's mash on the arrows, behind the prompt")
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
	check(text.contains("LEFT STICK to move, %s punches, %s dashes" % [a, b]) and text.contains("HOLD %s" % lb) and text.contains("TAP %s" % lb), "on a pad: the stick named, A, B and LB drawn inline")
	check(text.contains("Follow the prompt to finish him: mash %s and %s." % [lb, layout.inline_glyph(5)]), "and Eric's mash on LB and RB")
	check(a.contains("pad_buttons_inline_3x.png") and b.contains("pad_buttons_inline_3x.png") and lb.contains("pad_buttons.png"), "the face buttons from the 11 px set, the bumper from the 32 px sheet")
	Input.joy_connection_changed.emit(0, false)
	settings.rebind(&"block", key_event(KEY_C, true))
	text = " ".join(await danny_lines())
	check(text.contains("HOLD C") and text.contains("TAP C"), "and a rebind")
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
	# Button -> its column -> the columns -> the rows -> the panel.
	var first_boss := focus_owner()
	var panel: Node = first_boss.get_parent().get_parent().get_parent().get_parent() if first_boss is Button and first_boss != start else null
	check(panel is PanelContainer, "and on down into the boss select (%s)" % focus_name())
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
	check(await wait_for_scene(ERIC_FIGHT, 120), "Y confirms, straight into Eric's fight")

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
	check(await wait_for_scene(ERIC_FIGHT, 180), "standing in the Arena #1 doorway for the dwell goes through to Eric's fight too")


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
