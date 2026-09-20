extends Node

# The one place that knows what the controls are and which device the player is on. Every prompt in
# the game asks this node what to draw, and every movement read goes through move_vector().
#
# WARNING to anyone adding an _input() handler: autoloads sit before the current scene, and _input
# propagates in reverse tree order, so a node that calls set_input_as_handled() in its own _input
# hides the event from the tracker below and prompts stop following the device. If you write one,
# call InputSettings.note_device(event) before marking it handled, the way PlayerFinisher does.

const ControlsArtLayout := preload("res://Scripts/ControlsArtLayout.gd")

enum Device { KEYBOARD, GAMEPAD }

# Only on an actual change, never on a repeat of the device already in use.
signal device_changed(device: int)
signal bindings_changed()

# Movement is deliberately NOT on ui_left/ui_right/ui_up/ui_down: rebinding those would rebind menu
# navigation with them, and a bad bind could leave the player unable to reach this screen to fix it.
const ACTIONS: Array[StringName] = [
	&"move_up", &"move_down", &"move_left", &"move_right", &"punch", &"dodge", &"block",
]
# The four whose gamepad side is the fixed stick-and-d-pad cluster rather than a single button.
const MOVE_ACTIONS: Array[StringName] = [&"move_up", &"move_down", &"move_left", &"move_right"]
# The pseudo-action label_for() understands, for prompts that name movement as one thing.
const MOVE := &"move"

# `key` is a physical keycode, -1 for unbound. `pad_button` and `pad_axis` are mutually exclusive;
# an axis is only ever a trigger, which always reads positive. -1 means "not this kind".
const DEFAULTS := {
	&"move_up": {"key": KEY_UP, "pad_button": JOY_BUTTON_DPAD_UP, "pad_axis": -1},
	&"move_down": {"key": KEY_DOWN, "pad_button": JOY_BUTTON_DPAD_DOWN, "pad_axis": -1},
	&"move_left": {"key": KEY_LEFT, "pad_button": JOY_BUTTON_DPAD_LEFT, "pad_axis": -1},
	&"move_right": {"key": KEY_RIGHT, "pad_button": JOY_BUTTON_DPAD_RIGHT, "pad_axis": -1},
	&"punch": {"key": KEY_Q, "pad_button": JOY_BUTTON_A, "pad_axis": -1},
	&"dodge": {"key": KEY_W, "pad_button": JOY_BUTTON_B, "pad_axis": -1},
	&"block": {"key": KEY_SHIFT, "pad_button": JOY_BUTTON_LEFT_SHOULDER, "pad_axis": -1},
}
# What version 1 of the file shipped as the pad's defaults. A version 1 file still holding exactly
# these was never changed by its player, so it moves onto the defaults above; one that differs in any
# of them was, and is kept as it is.
const V1_PAD_DEFAULTS := {
	&"punch": JOY_BUTTON_X,
	&"dodge": JOY_BUTTON_RIGHT_SHOULDER,
	&"block": JOY_BUTTON_LEFT_SHOULDER,
}

# The finisher mash's own pair, for a fight on the player's feel_v2 (PlayerFinisher.mash_actions):
# the arrows on a keyboard, the bumpers on a pad. Registered at startup like the ui_* top-up, and kept
# out of ACTIONS and the file for now; they become rebindable when feel_v2 reaches every fight. They
# share keys with movement and a bumper with block, which the finisher keeps apart while it runs.
const MASH_DEFAULTS := {
	&"mash_left": {"key": KEY_LEFT, "pad_button": JOY_BUTTON_LEFT_SHOULDER, "pad_axis": -1},
	&"mash_right": {"key": KEY_RIGHT, "pad_button": JOY_BUTTON_RIGHT_SHOULDER, "pad_axis": -1},
}

# What opens the pause screen in a fight. Fixed, like the mash pair: it is the way out of a fight
# and out of a bad binding, so it is never rebindable and never in the file. Escape is deliberately
# not ui_cancel's business here - ui_cancel is also B, which is the dash.
const PAUSE_DEFAULTS := {
	&"pause": {"key": KEY_ESCAPE, "pad_button": JOY_BUTTON_START, "pad_axis": -1},
}

# [d-pad button, stick axis, axis direction] re-added to every move action on every apply, whatever
# the saved keyboard side is. The stick is not individually rebindable (D6).
const MOVE_PAD_EVENTS := {
	&"move_up": [JOY_BUTTON_DPAD_UP, JOY_AXIS_LEFT_Y, -1.0],
	&"move_down": [JOY_BUTTON_DPAD_DOWN, JOY_AXIS_LEFT_Y, 1.0],
	&"move_left": [JOY_BUTTON_DPAD_LEFT, JOY_AXIS_LEFT_X, -1.0],
	&"move_right": [JOY_BUTTON_DPAD_RIGHT, JOY_AXIS_LEFT_X, 1.0],
}

const ACTION_DEADZONE := 0.2
# The stick is digital, snapped to 8 directions, because every speed and i-frame in the game is tuned
# against a keyboard's (1, 1) diagonal and a raw stick corner is about 30% slower than that. It is
# measured by how far it is pushed, whichever way, so every direction starts moving at the same push,
# and then snapped by angle to the nearest of these, in Vector2.angle() order.
const MOVE_DIRECTIONS: Array[Vector2] = [
	Vector2(1, 0), Vector2(1, 1), Vector2(0, 1), Vector2(-1, 1),
	Vector2(-1, 0), Vector2(-1, -1), Vector2(0, -1), Vector2(1, -1),
]
# Of the engine's vector, which has already taken the 0.2 action dead zone off and rescaled the rest,
# so 0.4 of it is 52% of a full push.
const MOVE_THRESHOLD := 0.4
# A stick has to be pushed at least this far to count as "the player is using the pad": drift must
# never flip the prompts on its own.
const DEVICE_AXIS_THRESHOLD := 0.5
# Triggers are only ever bound in the positive direction, so a trigger binding stores its axis alone.
const TRIGGER_AXES: Array[int] = [JOY_AXIS_TRIGGER_LEFT, JOY_AXIS_TRIGGER_RIGHT]

const SAVE_PATH := "user://input_bindings.cfg"
# 2: the pad's defaults moved from X, RB and LB to A, B and LB.
const SAVE_VERSION := 2

# Godot's ui_* actions are never written into project.godot (doing so replaces the engine's built-in
# event list wholesale and silently drops its joypad events), so they are topped up here instead,
# additively, and only where the event isn't already there. [buttons, [axis, direction]...]
const UI_PAD_DEFAULTS := {
	&"ui_accept": [[JOY_BUTTON_A], []],
	&"ui_cancel": [[JOY_BUTTON_B], []],
	&"ui_up": [[JOY_BUTTON_DPAD_UP], [[JOY_AXIS_LEFT_Y, -1.0]]],
	&"ui_down": [[JOY_BUTTON_DPAD_DOWN], [[JOY_AXIS_LEFT_Y, 1.0]]],
	&"ui_left": [[JOY_BUTTON_DPAD_LEFT], [[JOY_AXIS_LEFT_X, -1.0]]],
	&"ui_right": [[JOY_BUTTON_DPAD_RIGHT], [[JOY_AXIS_LEFT_X, 1.0]]],
}
# Godot 4.6.3 ships ui_accept and ui_cancel with keys only, so a pad cannot confirm or cancel
# anything until the lines above put A and B on them: that is normal and says nothing. The four
# directions do come with the d-pad and the stick, so one of those turning up bare means something
# has overwritten the action — almost certainly the editor's Input Map panel — and is worth saying.
const UI_ENGINE_PROVIDES_PAD: Array[StringName] = [&"ui_up", &"ui_down", &"ui_left", &"ui_right"]

# Short names for the pad, in the wording the glyph sheet uses.
const PAD_BUTTON_LABELS := {
	JOY_BUTTON_A: "A",
	JOY_BUTTON_B: "B",
	JOY_BUTTON_X: "X",
	JOY_BUTTON_Y: "Y",
	JOY_BUTTON_BACK: "BACK",
	JOY_BUTTON_GUIDE: "GUIDE",
	JOY_BUTTON_START: "START",
	JOY_BUTTON_LEFT_STICK: "L3",
	JOY_BUTTON_RIGHT_STICK: "R3",
	JOY_BUTTON_LEFT_SHOULDER: "LB",
	JOY_BUTTON_RIGHT_SHOULDER: "RB",
	JOY_BUTTON_DPAD_UP: "D-PAD UP",
	JOY_BUTTON_DPAD_DOWN: "D-PAD DOWN",
	JOY_BUTTON_DPAD_LEFT: "D-PAD LEFT",
	JOY_BUTTON_DPAD_RIGHT: "D-PAD RIGHT",
}
const PAD_AXIS_LABELS := {
	JOY_AXIS_TRIGGER_LEFT: "LT",
	JOY_AXIS_TRIGGER_RIGHT: "RT",
}
# Keys the engine's own name is too long for a key cap or a hint. The rest are named as Godot names
# them, on whatever layout the player is on.
const KEY_LABELS := {
	KEY_ESCAPE: "ESC",
}

# Columns of the glyph sheets. The order is ours and deliberately decoupled from JoyButton, so the
# sheets can be drawn in a sensible order; anything unrecognised renders as the "?" column.
const PAD_FRAME_FALLBACK := 12
const PAD_BUTTON_FRAMES := {
	JOY_BUTTON_A: 0,
	JOY_BUTTON_B: 1,
	JOY_BUTTON_X: 2,
	JOY_BUTTON_Y: 3,
	JOY_BUTTON_LEFT_SHOULDER: 4,
	JOY_BUTTON_RIGHT_SHOULDER: 5,
	JOY_BUTTON_DPAD_UP: 8,
	JOY_BUTTON_DPAD_DOWN: 9,
	JOY_BUTTON_DPAD_LEFT: 10,
	JOY_BUTTON_DPAD_RIGHT: 11,
	JOY_BUTTON_START: 13,
}
const PAD_AXIS_FRAMES := {
	JOY_AXIS_TRIGGER_LEFT: 6,
	JOY_AXIS_TRIGGER_RIGHT: 7,
}

const UNBOUND_LABEL := "—"

var device := Device.KEYBOARD

# What Danny's dialogue tokens say for each control, refreshed on every device change and every
# rebind: the key's name on a keyboard, and on a pad the button drawn inline as BBCode (the stick has
# no inline cell, so movement is named). label_for() is the plain name.
var punch_name := ""
var dodge_name := ""
var block_name := ""
var move_name := ""
var mash_left_name := ""
var mash_right_name := ""
var pause_name := ""

var bindings := {}
# SAVE_PATH, except in the headless checks, which point this elsewhere so that no test run can ever
# overwrite the controls of the person playtesting from the same checkout.
var save_path := SAVE_PATH


func _ready() -> void:
	# Nothing about the controls may stop working because a fight froze the scene around the player.
	process_mode = Node.PROCESS_MODE_ALWAYS
	_load()
	apply_all()
	_top_up_ui_actions()
	_register_fixed_actions(MASH_DEFAULTS)
	_register_fixed_actions(PAUSE_DEFAULTS)
	device = Device.GAMEPAD if not Input.get_connected_joypads().is_empty() else Device.KEYBOARD
	Input.joy_connection_changed.connect(_on_joy_connection_changed)
	_refresh_names()


func _input(event: InputEvent) -> void:
	note_device(event)


# The single movement read for the whole game: 8-way, digital, identical on both devices. The keys
# only ever make the 8 exact directions, which come back as they are.
func move_vector() -> Vector2:
	var raw := Input.get_vector(&"move_left", &"move_right", &"move_up", &"move_down")
	if raw.length() < MOVE_THRESHOLD:
		return Vector2.ZERO
	return MOVE_DIRECTIONS[posmod(roundi(raw.angle() / (PI / 4.0)), MOVE_DIRECTIONS.size())]


# Mouse motion is ignored on purpose: a nudged mouse must not flip the prompts mid-fight.
func note_device(event: InputEvent) -> void:
	if event is InputEventKey:
		if event.pressed and not event.echo:
			_set_device(Device.KEYBOARD)
	elif event is InputEventMouseButton:
		if event.pressed:
			_set_device(Device.KEYBOARD)
	elif event is InputEventJoypadButton:
		if event.pressed:
			_set_device(Device.GAMEPAD)
	elif event is InputEventJoypadMotion:
		if absf(event.axis_value) >= DEVICE_AXIS_THRESHOLD:
			_set_device(Device.GAMEPAD)


# What the current device calls this action. MOVE asks about movement as a whole.
func label_for(action: StringName) -> String:
	if action == MOVE:
		return move_name
	return pad_label_for(action) if device == Device.GAMEPAD else key_label_for(action)


func key_label_for(action: StringName) -> String:
	var code: int = _binding(action)["key"]
	if code <= 0:
		return UNBOUND_LABEL
	# Bindings are physical positions; the name is whatever that position says on this layout. The
	# headless server has no layout and logs an error for asking, so tests get the US name.
	if DisplayServer.get_name() != "headless":
		code = DisplayServer.keyboard_get_keycode_from_physical(code)
	return KEY_LABELS.get(code, OS.get_keycode_string(code).to_upper())


func pad_label_for(action: StringName) -> String:
	var binding: Dictionary = _binding(action)
	if binding["pad_button"] >= 0:
		return PAD_BUTTON_LABELS.get(binding["pad_button"], "BTN %d" % binding["pad_button"])
	if binding["pad_axis"] >= 0:
		return PAD_AXIS_LABELS.get(binding["pad_axis"], "AXIS %d" % binding["pad_axis"])
	return UNBOUND_LABEL


func pad_frame_for(action: StringName) -> int:
	var binding: Dictionary = _binding(action)
	if binding["pad_button"] >= 0:
		return PAD_BUTTON_FRAMES.get(binding["pad_button"], PAD_FRAME_FALLBACK)
	if binding["pad_axis"] >= 0:
		return PAD_AXIS_FRAMES.get(binding["pad_axis"], PAD_FRAME_FALLBACK)
	return PAD_FRAME_FALLBACK


func is_bound(action: StringName, gamepad: bool) -> bool:
	var binding: Dictionary = _binding(action)
	if gamepad:
		return binding["pad_button"] >= 0 or binding["pad_axis"] >= 0
	return binding["key"] > 0


# MOVE asks whether all four movement bindings are.
func is_default(action: StringName, gamepad: bool) -> bool:
	if action == MOVE:
		return MOVE_ACTIONS.all(func(move: StringName) -> bool: return is_default(move, gamepad))
	var binding: Dictionary = bindings[action]
	var fallback: Dictionary = DEFAULTS[action]
	if gamepad:
		return binding["pad_button"] == fallback["pad_button"] and binding["pad_axis"] == fallback["pad_axis"]
	return binding["key"] == fallback["key"]


# Applies the event to `action`, writes the file and repaints every prompt. An action that already
# had that binding on the same side is left unbound rather than swapped (D7); its name comes back so
# the screen can say so. Returns &"" when nothing else lost anything.
func rebind(action: StringName, event: InputEvent) -> StringName:
	if not ACTIONS.has(action):
		return &""
	var gamepad := not (event is InputEventKey)
	# The stick and d-pad belong to movement and are not a per-action binding.
	if gamepad and (MOVE_ACTIONS.has(action) or is_stick_or_dpad(event)):
		return &""
	var value := {}
	if event is InputEventKey:
		value = {"key": event.physical_keycode}
	elif event is InputEventJoypadButton:
		value = {"pad_button": event.button_index, "pad_axis": -1}
	elif event is InputEventJoypadMotion:
		value = {"pad_button": -1, "pad_axis": int(event.axis)}
	else:
		return &""

	var loser := &""
	for other in ACTIONS:
		if other == action:
			continue
		if not _same_binding(other, value):
			continue
		loser = other
		for field in value:
			bindings[other][field] = -1
		break

	for field in value:
		bindings[action][field] = value[field]
	apply_all()
	_save()
	bindings_changed.emit()
	return loser


# Pad input no action can be bound to: the d-pad and every stick axis. Only triggers are axes that bind.
func is_stick_or_dpad(event: InputEvent) -> bool:
	if event is InputEventJoypadButton:
		return MOVE_PAD_EVENTS.values().any(func(fixed: Array) -> bool: return fixed[0] == event.button_index)
	if event is InputEventJoypadMotion:
		return not TRIGGER_AXES.has(event.axis)
	return false


func reset_to_defaults() -> void:
	bindings = _default_bindings()
	apply_all()
	_save()
	bindings_changed.emit()


# Rewrites every action's event list from `bindings`. Never touches any ui_* action.
func apply_all() -> void:
	for action in ACTIONS:
		if not InputMap.has_action(action):
			InputMap.add_action(action, ACTION_DEADZONE)
		InputMap.action_erase_events(action)
		var binding: Dictionary = bindings[action]
		if binding["key"] > 0:
			var key := InputEventKey.new()
			key.physical_keycode = binding["key"]
			InputMap.action_add_event(action, key)
		if MOVE_PAD_EVENTS.has(action):
			var fixed: Array = MOVE_PAD_EVENTS[action]
			InputMap.action_add_event(action, _pad_button_event(fixed[0]))
			InputMap.action_add_event(action, _pad_motion_event(fixed[1], fixed[2]))
			continue
		if binding["pad_button"] >= 0:
			InputMap.action_add_event(action, _pad_button_event(binding["pad_button"]))
		elif binding["pad_axis"] >= 0:
			InputMap.action_add_event(action, _pad_motion_event(binding["pad_axis"], 1.0))
	_refresh_names()


func _same_binding(action: StringName, value: Dictionary) -> bool:
	for field in value:
		if value[field] < 0:
			continue
		if bindings[action][field] != value[field]:
			return false
	return true


func _pad_button_event(button: int) -> InputEventJoypadButton:
	var event := InputEventJoypadButton.new()
	event.button_index = button
	return event


func _pad_motion_event(axis: int, value: float) -> InputEventJoypadMotion:
	var event := InputEventJoypadMotion.new()
	event.axis = axis
	event.axis_value = value
	return event


func _set_device(next: int) -> void:
	if next == device:
		return
	device = next
	_refresh_names()
	device_changed.emit(device)


func _on_joy_connection_changed(_joypad: int, connected: bool) -> void:
	if connected:
		_set_device(Device.GAMEPAD)
	elif Input.get_connected_joypads().is_empty():
		_set_device(Device.KEYBOARD)


func _refresh_names() -> void:
	punch_name = _dialogue_name(&"punch")
	dodge_name = _dialogue_name(&"dodge")
	block_name = _dialogue_name(&"block")
	move_name = _move_name()
	mash_left_name = _dialogue_name(&"mash_left")
	mash_right_name = _dialogue_name(&"mash_right")
	pause_name = _dialogue_name(&"pause")


# A rebindable action's binding, or a fixed one's (the mash pair, pause).
func _binding(action: StringName) -> Dictionary:
	if bindings.has(action):
		return bindings[action]
	return MASH_DEFAULTS[action] if MASH_DEFAULTS.has(action) else PAUSE_DEFAULTS[action]


# On a pad a bound button is drawn inline rather than named.
func _dialogue_name(action: StringName) -> String:
	if device == Device.GAMEPAD and is_bound(action, true) and ControlsArtLayout.USE_FINAL_INLINE_GLYPHS:
		return ControlsArtLayout.inline_glyph(pad_frame_for(action))
	return label_for(action)


# Keys in W/A/S/D order: up, left, down, right.
func _move_name() -> String:
	if device == Device.GAMEPAD:
		return "LEFT STICK"
	if is_default(MOVE, false):
		return "ARROWS"
	var names: PackedStringArray = []
	for action in [&"move_up", &"move_left", &"move_down", &"move_right"]:
		names.append(key_label_for(action))
	return "/".join(names)


func _default_bindings() -> Dictionary:
	var fresh := {}
	for action in ACTIONS:
		fresh[action] = DEFAULTS[action].duplicate()
	return fresh


# Missing is the normal first run: take the defaults and write them. A file that can't be read, or
# was written by a version this doesn't know, falls back wholesale and is overwritten at once, so a
# broken file can't come back every boot. An action that is missing or bad falls back on its own, and
# the file is rewritten whole for the same reason. A version 1 file is migrated and rewritten.
func _load() -> void:
	bindings = _default_bindings()
	if not FileAccess.file_exists(save_path):
		_save()
		return
	var cfg := ConfigFile.new()
	if cfg.load(save_path) != OK:
		push_warning("InputSettings: %s could not be read; controls reset to defaults." % save_path)
		_save()
		return
	var version := int(cfg.get_value("meta", "version", -1))
	if version != SAVE_VERSION and version != 1:
		_save()
		return
	var repaired := version != SAVE_VERSION
	for action in ACTIONS:
		# Not null: ConfigFile takes a null default as no default and logs an error for a missing key.
		var stored = cfg.get_value("bindings", action, {})
		if typeof(stored) != TYPE_DICTIONARY:
			repaired = true
			continue
		var binding: Dictionary = bindings[action]
		# A key of 0 is no key at all rather than "unbound", so it falls back; -1 is a real unbind.
		if typeof(stored.get("key")) == TYPE_INT and stored["key"] != 0:
			binding["key"] = int(stored["key"])
		else:
			repaired = true
		for field in ["pad_button", "pad_axis"]:
			if typeof(stored.get(field)) == TYPE_INT:
				binding[field] = int(stored[field])
			else:
				repaired = true
	if version == 1:
		_migrate_v1_pad()
	if repaired:
		_save()


func _migrate_v1_pad() -> void:
	for action in V1_PAD_DEFAULTS:
		if bindings[action]["pad_button"] != V1_PAD_DEFAULTS[action] or bindings[action]["pad_axis"] != -1:
			return
	for action in V1_PAD_DEFAULTS:
		bindings[action]["pad_button"] = DEFAULTS[action]["pad_button"]


# Synchronous, on every change: a crash must never cost the player their controls.
func _save() -> void:
	var cfg := ConfigFile.new()
	cfg.set_value("meta", "version", SAVE_VERSION)
	for action in ACTIONS:
		cfg.set_value("bindings", action, bindings[action])
	cfg.save(save_path)


# The actions that aren't rebindable and aren't in the file: their events are written from their
# defaults on every boot, so nothing on disk and nothing in the editor's Input Map panel can move them.
func _register_fixed_actions(defaults: Dictionary) -> void:
	for action in defaults:
		if not InputMap.has_action(action):
			InputMap.add_action(action, ACTION_DEADZONE)
		InputMap.action_erase_events(action)
		var key := InputEventKey.new()
		key.physical_keycode = defaults[action]["key"]
		InputMap.action_add_event(action, key)
		InputMap.action_add_event(action, _pad_button_event(defaults[action]["pad_button"]))


# Nothing in the project protects the ui_* joypad events: if anyone edits one of these actions in
# the editor's Input Map panel, Godot writes it out and the pad silently loses menu navigation.
# Whatever is missing is put back here, without disturbing what is there.
func _top_up_ui_actions() -> void:
	for action in UI_PAD_DEFAULTS:
		if not InputMap.has_action(action):
			continue
		var has_pad := false
		for event in InputMap.action_get_events(action):
			if event is InputEventJoypadButton or event is InputEventJoypadMotion:
				has_pad = true
				break
		if has_pad:
			continue
		var spec: Array = UI_PAD_DEFAULTS[action]
		for button in spec[0]:
			InputMap.action_add_event(action, _pad_button_event(button))
		for motion in spec[1]:
			InputMap.action_add_event(action, _pad_motion_event(motion[0], motion[1]))
		if UI_ENGINE_PROVIDES_PAD.has(action):
			push_warning("InputSettings: %s had lost its joypad events (edited in the Input Map panel?); put back." % action)
