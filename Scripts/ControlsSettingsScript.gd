extends Control

# The rebind screen, off the main menu: a row per InputSettings.ACTIONS entry, with its keyboard and
# its gamepad binding. Pressing a cell listens, and the next key or button becomes that binding.
# InputSettings applies and saves it; this screen only asks and repaints.

# Emitted instead of going back to the main menu when this screen is hosted inside another one.
signal closed

const ControlsArtLayout := preload("res://Scripts/ControlsArtLayout.gd")

const MAIN_MENU := "res://Scenes/Core/MainMenuScene.tscn"

const ACTION_NAMES := {
	&"move_up": "MOVE UP",
	&"move_down": "MOVE DOWN",
	&"move_left": "MOVE LEFT",
	&"move_right": "MOVE RIGHT",
	&"punch": "ATTACK",
	&"dodge": "DASH",
	&"block": "BLOCK / PARRY",
}
const HEADERS := ["ACTION", "KEYBOARD", "GAMEPAD"]
# Movement's gamepad side is the stick and the d-pad together, and isn't rebindable.
const MOVE_PAD_TEXT := "LEFT STICK / D-PAD"

const PROMPT_KEY := "PRESS A KEY"
const PROMPT_BUTTON := "PRESS A BUTTON"
# ui_cancel backs out of a capture and off the screen, so Escape can never be bound. B is ui_cancel
# too, but dash is on it by default, so on a gamepad cell it binds like any other button; a player
# with only a pad leaves such a cell by pressing the button it already has.
const HINT_KEYBOARD := "ENTER: CHANGE    ESC: BACK    (ESC CAN'T BE BOUND)"
const HINT_GAMEPAD := "A: CHANGE    B: BACK"
const HINT_LISTEN_KEYBOARD := "ESC: CANCEL"
const HINT_LISTEN_GAMEPAD := "B: CANCEL"
const HINT_LISTEN_BUTTON := "SAME BUTTON: KEEP IT    ESC: CANCEL"
const NOTICE_RESET := "CONTROLS RESET TO DEFAULTS"
const NOTICE_STICK_OR_DPAD := "STICKS AND THE D-PAD CAN'T BE BOUND"
const NOTICE_LOST := "%s WAS ON %s, WHICH IS NOW UNBOUND"

# A trigger counts as pressed this far in; a stick this far out gets told why it can't be bound.
const TRIGGER_THRESHOLD := 0.6
const STICK_NOTICE_THRESHOLD := 0.6

const ACTION_COLUMN_WIDTH := 420.0
# Tall enough for a key's name at full size on key_blank: its 9 px top edge, the text, its 27 px lip.
const CELL_SIZE := Vector2(360, 80)
const HEADER_COLOR := Color(0.65, 0.68, 0.74)
const MOVE_PAD_COLOR := Color(0.65, 0.68, 0.74)
const LISTEN_COLOR := Color(1.0, 0.85, 0.3)
const NOTICE_COLOR := Color(1, 1, 1)
const NOTICE_WARNING_COLOR := Color(1.0, 0.45, 0.35)
const NOTICE_HOLD := 2.5
const NOTICE_FADE := 0.5

# Set by whoever instances this screen as a child overlay - today the in-fight pause screen. Back
# then returns to the host instead of changing scene, and the host says when the table takes focus.
@export var embedded := false

@onready var background: TextureRect = $Background
@onready var table: GridContainer = %Table
@onready var notice_label: Label = %Notice
@onready var hint_label: Label = %Hint
@onready var reset_button: Button = %ResetButton
@onready var back_button: Button = %BackButton

# Keyed [gamepad][action]: the cell's button, the keycap it shows, and the drawn glyph that replaces
# the keycap once the final pad art is in.
var cells := {false: {}, true: {}}
var keycaps := {false: {}, true: {}}
var glyphs := {false: {}, true: {}}
var listening := false
var listen_action := &""
var listen_gamepad := false
var notice_tween: Tween


func _ready() -> void:
	# Hosted over a paused fight, this screen sits on the pause screen's dim: its own backdrop would
	# hide the fight the player is standing in the middle of.
	background.visible = not embedded
	for button in [reset_button, back_button]:
		button.add_theme_stylebox_override("focus", ControlsArtLayout.focus_ring())
	_build_table()
	_repaint()
	InputSettings.device_changed.connect(_repaint.unbind(1))
	InputSettings.bindings_changed.connect(_repaint)
	reset_button.pressed.connect(_on_reset_pressed)
	back_button.pressed.connect(_on_back_pressed)
	notice_label.text = ""
	if not embedded:
		focus_first()


func focus_first() -> void:
	cells[false][InputSettings.ACTIONS[0]].grab_focus()


# While listening every press is swallowed, so nothing can move the focus or press a button until
# the capture is over.
func _input(event: InputEvent) -> void:
	if not listening or event is InputEventMouseMotion:
		return
	# Before it is marked handled: the device tracker is an autoload, later in the order.
	InputSettings.note_device(event)
	get_viewport().set_input_as_handled()
	if event.is_action_pressed(&"ui_cancel") and not (listen_gamepad and event is InputEventJoypadButton):
		set_listening(false)
		return
	var binding := _capture(event)
	if binding == null:
		return
	var action := listen_action
	var gamepad := listen_gamepad
	set_listening(false)
	var loser := InputSettings.rebind(action, binding)
	if not loser.is_empty():
		var bound_as: String = InputSettings.pad_label_for(action) if gamepad else InputSettings.key_label_for(action)
		_show_notice(NOTICE_LOST % [bound_as, ACTION_NAMES[loser]], true)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed(&"ui_cancel"):
		get_viewport().set_input_as_handled()
		_on_back_pressed()


func set_listening(on: bool) -> void:
	listening = on
	if not on:
		listen_action = &""
	_repaint()


func _on_cell_pressed(action: StringName, gamepad: bool) -> void:
	if listening:
		return
	listen_action = action
	listen_gamepad = gamepad
	# Deferred, so the press that opened the cell is flushed before anything is listened for:
	# otherwise the button that pressed the cell could become its own binding.
	set_listening.call_deferred(true)


# The event as a binding for the cell being listened to, or null when it can't be one.
func _capture(event: InputEvent) -> InputEvent:
	if not listen_gamepad:
		if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode != KEY_NONE:
			return event
		return null
	if InputSettings.is_stick_or_dpad(event):
		# Only for a real press or push, so a resting stick's drift can't keep the notice up.
		if (event is InputEventJoypadButton and event.pressed) or (event is InputEventJoypadMotion and absf(event.axis_value) >= STICK_NOTICE_THRESHOLD):
			_show_notice(NOTICE_STICK_OR_DPAD, true)
		return null
	if event is InputEventJoypadButton and event.pressed:
		return event
	if event is InputEventJoypadMotion and event.axis_value >= TRIGGER_THRESHOLD:
		return event
	return null


func _on_reset_pressed() -> void:
	InputSettings.reset_to_defaults()
	_show_notice(NOTICE_RESET)


func _on_back_pressed() -> void:
	if embedded:
		closed.emit()
		return
	get_tree().change_scene_to_file(MAIN_MENU)


func _build_table() -> void:
	for header in HEADERS:
		var label := Label.new()
		label.text = header
		label.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT if header == HEADERS[0] else HORIZONTAL_ALIGNMENT_CENTER
		label.add_theme_color_override("font_color", HEADER_COLOR)
		table.add_child(label)
	for action in InputSettings.ACTIONS:
		var name_label := Label.new()
		name_label.text = ACTION_NAMES[action]
		name_label.custom_minimum_size = Vector2(ACTION_COLUMN_WIDTH, CELL_SIZE.y)
		name_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		table.add_child(name_label)
		var key_cell := _make_cell(action, false)
		table.add_child(key_cell)
		if InputSettings.MOVE_ACTIONS.has(action):
			var fixed := Label.new()
			fixed.text = MOVE_PAD_TEXT
			fixed.custom_minimum_size = CELL_SIZE
			fixed.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			fixed.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
			fixed.add_theme_color_override("font_color", MOVE_PAD_COLOR)
			table.add_child(fixed)
			# Nothing to the right of these rows can take focus, and the nearest thing that can is a
			# row further down, so right stays put instead of jumping there.
			key_cell.focus_neighbor_right = NodePath(".")
		else:
			table.add_child(_make_cell(action, true))


func _make_cell(action: StringName, gamepad: bool) -> Button:
	var cell := Button.new()
	cell.custom_minimum_size = CELL_SIZE
	for style_name in ["normal", "hover", "pressed", "focus"]:
		cell.add_theme_stylebox_override(style_name, _cell_style(style_name))
	cell.pressed.connect(_on_cell_pressed.bind(action, gamepad))
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	cell.add_child(center)
	var keycap := ControlsArtLayout.keycap("", ControlsArtLayout.KEY_FONT_SIZE, ControlsArtLayout.SMALL_KEY_MIN_SIZE)
	center.add_child(keycap)
	var glyph := TextureRect.new()
	glyph.custom_minimum_size = ControlsArtLayout.SMALL_KEY_MIN_SIZE
	glyph.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	glyph.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	glyph.mouse_filter = Control.MOUSE_FILTER_IGNORE
	center.add_child(glyph)
	cells[gamepad][action] = cell
	keycaps[gamepad][action] = keycap
	glyphs[gamepad][action] = glyph
	return cell


func _cell_style(style_name: String) -> StyleBox:
	if style_name == "focus":
		return ControlsArtLayout.focus_ring()
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.05, 0.05, 0.08, 0.55)
	match style_name:
		"hover":
			style.bg_color = Color(0.16, 0.15, 0.24, 0.75)
		"pressed":
			style.bg_color = Color(0.03, 0.03, 0.05, 0.75)
	style.anti_aliasing = false
	return style


func _repaint() -> void:
	var on_pad := InputSettings.device == InputSettings.Device.GAMEPAD
	for gamepad in cells:
		for action in cells[gamepad]:
			_paint_cell(action, gamepad)
	if listening:
		if listen_gamepad:
			hint_label.text = HINT_LISTEN_BUTTON
		else:
			hint_label.text = HINT_LISTEN_GAMEPAD if on_pad else HINT_LISTEN_KEYBOARD
	else:
		hint_label.text = HINT_GAMEPAD if on_pad else HINT_KEYBOARD


func _paint_cell(action: StringName, gamepad: bool) -> void:
	var keycap: Label = keycaps[gamepad][action]
	var glyph: TextureRect = glyphs[gamepad][action]
	if listening and action == listen_action and gamepad == listen_gamepad:
		glyph.visible = false
		keycap.visible = true
		keycap.text = PROMPT_BUTTON if gamepad else PROMPT_KEY
		keycap.add_theme_color_override("font_color", LISTEN_COLOR)
		return
	var drawn := gamepad and ControlsArtLayout.USE_FINAL_PAD_GLYPHS and InputSettings.is_bound(action, true)
	glyph.visible = drawn
	keycap.visible = not drawn
	if drawn:
		glyph.texture = ControlsArtLayout.pad_glyph(action)
	else:
		ControlsArtLayout.paint_keycap(keycap, action, gamepad)


# Node-bound, so it dies with the screen.
func _show_notice(text: String, warning := false) -> void:
	if notice_tween:
		notice_tween.kill()
	notice_label.text = text
	notice_label.modulate.a = 1.0
	notice_label.add_theme_color_override("font_color", NOTICE_WARNING_COLOR if warning else NOTICE_COLOR)
	notice_tween = notice_label.create_tween()
	notice_tween.tween_interval(NOTICE_HOLD)
	notice_tween.tween_property(notice_label, "modulate:a", 0.0, NOTICE_FADE)
