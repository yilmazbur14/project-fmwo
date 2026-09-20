extends CanvasLayer

# The in-fight pause screen. It rides at the bottom of ArenaScene, so all eight fights have one, and
# it is the only thing in a fight that runs while the tree is paused: everything else - the bosses,
# the player, the hazards, the HUD, the music, the hit-stop and the finisher's freeze - stops where
# it is and carries on from there.
#
# WARNING to anyone writing fight code: a pause is SceneTree.paused, so anything that wants to stop
# with the fight must be pausable. Timer nodes, _physics_process accumulators and node-bound tweens
# all are. get_tree().create_timer(t) is NOT - its second argument is process_always, and it
# defaults to true - so pass false. Engine.time_scale is never touched here: six scripts divide by
# it, and a zero scale makes them jump.
#
# This handler is _input rather than _unhandled_input because the dialogue balloon swallows every
# unhandled event while it is showing, and pausing mid-banter has to work.

signal opened
signal closed

const PauseArtLayout := preload("res://Scripts/PauseArtLayout.gd")
const ControlsArtLayout := preload("res://Scripts/ControlsArtLayout.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const HitStop := preload("res://Scripts/HitStop.gd")
const FightFreeze := preload("res://Scripts/FightFreeze.gd")

const MAIN_MENU := "res://Scenes/Core/MainMenuScene.tscn"
const CONTROLS_SETTINGS := "res://Scenes/Core/ControlsSettingsScene.tscn"

# Real seconds after resuming during which the presses that could leak into combat are eaten. Real,
# not game time: the fight may resume into a hit-stop.
const RESUME_INPUT_GRACE := 0.15
const GRACE_ACTIONS: Array[StringName] = [
	&"punch", &"dodge", &"block", &"mash_left", &"mash_right", &"ui_accept", &"ui_cancel",
]

# The node FightOutro adds under the root the moment a fight is decided.
const OUTRO_NODE := ^"FightOutro"
# The fight's VS intro card, a sibling of this layer in the arena.
const VS_CARD_NODE := ^"VsCard"

# [the word, the glyph sheet's column for the pad button that does it]. On a keyboard Escape does
# both jobs, so both hints show the pause key; on a pad Start closes the screen from wherever it is
# and B backs out one level.
const FOOTER_HINTS := [
	["RESUME", JOY_BUTTON_START],
	["BACK", JOY_BUTTON_B],
]

const CONFIRM_RESTART := "START THIS FIGHT AGAIN?"
const CONFIRM_QUIT := "LEAVE THE FIGHT AND GO BACK TO THE MAIN MENU?"

# Which screen the presses belong to. CONTROLS is the rebind screen, instanced as a child overlay.
enum Level { ROOT, CONFIRM, CONTROLS }

@onready var dim: ColorRect = $Dim
@onready var root: Control = $Root
@onready var panel: PanelContainer = %Panel
@onready var panel_margin: MarginContainer = %Margin
@onready var title: Label = %Title
@onready var title_art: TextureRect = %TitleArt
@onready var rows: VBoxContainer = %Rows
@onready var footer: HBoxContainer = %Footer
@onready var resume_button: Button = %ResumeButton
@onready var restart_button: Button = %RestartButton
@onready var quit_button: Button = %QuitButton
@onready var volume_label: Label = %VolumeLabel
@onready var volume_slider: HSlider = %VolumeSlider
@onready var confirm: Control = %Confirm
@onready var confirm_panel: PanelContainer = %ConfirmPanel
@onready var confirm_margin: MarginContainer = %ConfirmMargin
@onready var confirm_message: Label = %Message
@onready var confirm_buttons: HBoxContainer = %Buttons
@onready var confirm_back_button: Button = %BackButton
@onready var confirm_ok_button: Button = %ConfirmButton
@onready var controls_button: Button = %ControlsButton
@onready var controls_host: Control = %ControlsHost
@onready var column: VBoxContainer = $Root/Center/Panel/Margin/Column

# The shake the fight was in the middle of, held still for the paused frames so the panel isn't
# drawn against a jittering arena, and put back before the fight runs again.
var held_shake := Vector2.ZERO
var grace_until_msec := 0
var level := Level.ROOT
# Restart or Quit is on its way: the fight is already over as far as this screen is concerned, so
# nothing may reopen it or press anything again while the scene change is in flight.
var leaving := false
# What CONFIRM will do when it is confirmed.
var pending := Callable()

var master_bus_index := 0
# The slider's own highlight art, and a tinted copy of it: a slider can't draw a focus box, so on a
# pad that tint is the only way to see that focus is on it. The same trick the main menu uses.
var slider_highlight: StyleBox
var pad_slider_highlight: StyleBoxTexture
# [written key, drawn pad glyph] per footer hint, swapped over on every device change.
var footer_keys: Array[Label] = []
var footer_glyphs: Array[TextureRect] = []


func _ready() -> void:
	dim.color = PauseArtLayout.DIM_COLOR
	_style_panel(panel, panel_margin, PauseArtLayout.panel_style())
	_style_panel(confirm_panel, confirm_margin, PauseArtLayout.confirm_panel_style())
	confirm_panel.custom_minimum_size.x = PauseArtLayout.CONFIRM_MIN_WIDTH
	_style_title()
	_style_confirm()
	rows.add_theme_constant_override("separation", PauseArtLayout.ROW_SEPARATION)
	column.add_theme_constant_override("separation", PauseArtLayout.COLUMN_SEPARATION)
	for button in [resume_button, restart_button, controls_button, quit_button]:
		_style_row(button)
	resume_button.pressed.connect(close)
	restart_button.pressed.connect(_ask.bind(CONFIRM_RESTART, _restart))
	controls_button.pressed.connect(_open_controls)
	quit_button.pressed.connect(_ask.bind(CONFIRM_QUIT, _quit))
	confirm_back_button.pressed.connect(_show_root)
	confirm_ok_button.pressed.connect(_take_pending)
	_setup_volume()
	_build_footer()
	_link_focus()
	InputSettings.device_changed.connect(_on_device_changed)
	Input.joy_connection_changed.connect(_on_joy_connection_changed)
	_show_focus()
	_paint_footer()
	visible = false


# Alt-tabbing out of a fight pauses it. Coming back does NOT resume: the player left the window on
# purpose, and a fight restarting itself under an unwatched window is the worse of the two.
func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT and can_open():
		open()


# The last pad going away pauses too, so nobody is left holding a dead controller mid-combo.
func _on_joy_connection_changed(_joypad: int, connected: bool) -> void:
	if not connected and Input.get_connected_joypads().is_empty() and can_open():
		open()


func _input(event: InputEvent) -> void:
	if event is InputEventMouseMotion:
		return
	if is_open():
		_paused_input(event)
		return
	# Before the grace, so the pause key is never eaten by its own resume: Escape is also ui_cancel,
	# which the grace does eat, and a player tapping Escape twice has to get the screen back.
	if event.is_action_pressed(&"pause") and can_open():
		_take(event)
		open()
		return
	if _in_grace():
		_eat_grace_press(event)


# ui_cancel is tried first because Escape is both: backing out a level is the more useful of the two
# on the key that does both jobs, and Start still closes the screen from wherever it is.
func _paused_input(event: InputEvent) -> void:
	if event.is_action_pressed(&"ui_cancel"):
		# The rebind screen's own Back is on ui_cancel; leaving the event alone is what lets it run,
		# and it comes back here through its closed signal.
		if level == Level.CONTROLS:
			return
		_take(event)
		if level == Level.ROOT:
			close()
		else:
			_show_root()
		return
	if event.is_action_pressed(&"pause"):
		_take(event)
		close()


# Before it is marked handled: the device tracker is an autoload, and autoloads are earlier in the
# tree than the scene, so _input reaches them last.
func _take(event: InputEvent) -> void:
	InputSettings.note_device(event)
	get_viewport().set_input_as_handled()


func is_open() -> bool:
	return visible


# Everything a fight can be in the middle of is pausable except the two ends of it: the VS card,
# which is on its own clock between the pre-fight lines and the fight, and the outro - once
# FightOutro is up the fight is decided, its lines and fade are on their own clock, and there is
# nothing to come back to. MainScene.tscn instances the arena too but is not a fight, so it is
# never pausable.
func can_open() -> bool:
	if is_open() or leaving:
		return false
	var tree := get_tree()
	if tree == null or tree.current_scene == null:
		return false
	if not GameProgress.FIGHT_SCENES.has(tree.current_scene.scene_file_path):
		return false
	if tree.root.has_node(OUTRO_NODE):
		return false
	var card := _vs_card()
	if card != null and card.is_playing():
		return false
	var player := _player()
	return player == null or not player.fight_over


func open() -> void:
	if is_open():
		return
	held_shake = ScreenView.shake_offset
	ScreenView.shake_offset = Vector2.ZERO
	ScreenView.apply(get_tree())
	_read_volume()
	get_tree().paused = true
	visible = true
	_show_root()
	opened.emit()


func close() -> void:
	if not is_open():
		return
	_show_root()
	visible = false
	ScreenView.shake_offset = held_shake
	ScreenView.apply(get_tree())
	_rearm_balloon()
	grace_until_msec = Time.get_ticks_msec() + roundi(RESUME_INPUT_GRACE * 1000.0)
	# Deferred, so the press that closed the screen has finished being flushed before the fight is
	# running again: otherwise the same event could still be read as a punch.
	_unpause.call_deferred()
	closed.emit()


func _unpause() -> void:
	get_tree().paused = false


func _in_grace() -> bool:
	return Time.get_ticks_msec() < grace_until_msec


# Only presses: a held guard or a held direction must carry straight on through a resume, and both
# of those are polled rather than read from the event.
func _eat_grace_press(event: InputEvent) -> void:
	for action in GRACE_ACTIONS:
		if event.is_action_pressed(action):
			_take(event)
			return


func _show_root() -> void:
	level = Level.ROOT
	pending = Callable()
	_free_controls()
	confirm.visible = false
	root.visible = true
	resume_button.grab_focus()


# The whole rebind screen, over the pause panel. It writes its bindings as it always does; nothing
# about a fight in progress depends on them, so a rebind here takes effect on the resuming frame.
func _open_controls() -> void:
	if level == Level.CONTROLS:
		return
	var screen: Control = load(CONTROLS_SETTINGS).instantiate()
	screen.embedded = true
	screen.closed.connect(_close_controls)
	controls_host.add_child(screen)
	controls_host.visible = true
	root.visible = false
	level = Level.CONTROLS
	screen.focus_first()


func _close_controls() -> void:
	_show_root()
	controls_button.grab_focus()


func _free_controls() -> void:
	controls_host.visible = false
	for child in controls_host.get_children():
		controls_host.remove_child(child)
		child.queue_free()


# BACK takes focus, so a mashed accept can't restart or quit the fight by itself.
func _ask(message: String, action: Callable) -> void:
	level = Level.CONFIRM
	pending = action
	confirm_message.text = message
	root.visible = false
	confirm.visible = true
	confirm_back_button.grab_focus()


func _take_pending() -> void:
	if pending.is_valid():
		pending.call()


func _restart() -> void:
	_leave("")


func _quit() -> void:
	_leave(MAIN_MENU)


# Everything the fight put on the engine comes off before the scene goes, in this order. The
# unfreeze is not optional: FightFreeze.frozen is static, so a fight left frozen would make the
# next fight's first freeze() refuse. GameProgress is left alone - quitting doesn't undo a run.
func _leave(to_scene: String) -> void:
	if leaving:
		return
	leaving = true
	HitStop.clear()
	FightFreeze.unfreeze(get_tree())
	ScreenView.reset(get_tree())
	get_tree().paused = false
	visible = false
	if to_scene.is_empty():
		get_tree().reload_current_scene.call_deferred()
	else:
		get_tree().change_scene_to_file.call_deferred(to_scene)


func _player() -> Node:
	var arena := get_parent()
	return arena.get_node_or_null(^"MainPlayer/CharacterBody2D") if arena != null else null


func _vs_card() -> Node:
	var arena := get_parent()
	return arena.get_node_or_null(VS_CARD_NODE) if arena != null else null


# The balloon's input lock is on the real clock, so a line that was up when the screen opened would
# come back already unlocked and take the resuming press as "next line".
func _rearm_balloon() -> void:
	var scene := get_tree().current_scene
	if scene == null:
		return
	for child in scene.get_children():
		if child.has_method(&"rearm_input_lock"):
			child.rearm_input_lock()


# Neither column can be trusted to geometric navigation once the rows are drawn on art of their own,
# so both are chained by hand, the way the main menu chains its own.
func _link_focus() -> void:
	var column: Array[Control] = [resume_button, restart_button, controls_button, volume_slider, quit_button]
	for i in column.size():
		if i > 0:
			column[i].focus_neighbor_top = column[i - 1].get_path()
			column[i].focus_previous = column[i - 1].get_path()
		if i < column.size() - 1:
			column[i].focus_neighbor_bottom = column[i + 1].get_path()
			column[i].focus_next = column[i + 1].get_path()
	confirm_back_button.focus_neighbor_right = confirm_ok_button.get_path()
	confirm_back_button.focus_next = confirm_ok_button.get_path()
	confirm_ok_button.focus_neighbor_left = confirm_back_button.get_path()
	confirm_ok_button.focus_previous = confirm_back_button.get_path()


func _style_panel(target: PanelContainer, margin: MarginContainer, style: StyleBox) -> void:
	target.add_theme_stylebox_override("panel", style)
	target.custom_minimum_size.x = PauseArtLayout.PANEL_MIN_WIDTH
	for side in ["left", "top", "right", "bottom"]:
		margin.add_theme_constant_override("margin_" + side, PauseArtLayout.PANEL_MARGIN)


func _style_title() -> void:
	var art := PauseArtLayout.title_texture()
	title_art.texture = art
	title_art.visible = art != null
	title.visible = art == null
	title.add_theme_font_size_override("font_size", PauseArtLayout.TITLE_FONT_SIZE)
	title.add_theme_color_override("font_color", PauseArtLayout.TITLE_COLOR)


func _style_confirm() -> void:
	confirm_message.add_theme_font_size_override("font_size", PauseArtLayout.ROW_FONT_SIZE)
	confirm_message.add_theme_color_override("font_color", PauseArtLayout.CONFIRM_MESSAGE_COLOR)
	confirm_buttons.add_theme_constant_override("separation", PauseArtLayout.CONFIRM_BUTTON_SEPARATION)
	for button in [confirm_back_button, confirm_ok_button]:
		_style_row(button)
		button.custom_minimum_size = PauseArtLayout.CONFIRM_BUTTON_MIN_SIZE


# Volume is session-only here, exactly as it is on the main menu: nothing is written to disk.
func _setup_volume() -> void:
	volume_label.add_theme_font_size_override("font_size", PauseArtLayout.LABEL_FONT_SIZE)
	volume_label.add_theme_color_override("font_color", PauseArtLayout.LABEL_COLOR)
	volume_slider.custom_minimum_size = PauseArtLayout.SLIDER_MIN_SIZE
	master_bus_index = AudioServer.get_bus_index("Master")
	slider_highlight = volume_slider.get_theme_stylebox("grabber_area_highlight")
	pad_slider_highlight = slider_highlight.duplicate() as StyleBoxTexture
	pad_slider_highlight.modulate_color = ControlsArtLayout.FOCUS_TINT
	_read_volume()
	volume_slider.value_changed.connect(_on_volume_changed)


# On every open, so the slider shows whatever the volume already is rather than what it was.
func _read_volume() -> void:
	if AudioServer.is_bus_mute(master_bus_index):
		volume_slider.set_value_no_signal(0.0)
	else:
		volume_slider.set_value_no_signal(db_to_linear(AudioServer.get_bus_volume_db(master_bus_index)))


func _on_volume_changed(value: float) -> void:
	if value <= 0.001:
		AudioServer.set_bus_mute(master_bus_index, true)
	else:
		AudioServer.set_bus_mute(master_bus_index, false)
		AudioServer.set_bus_volume_db(master_bus_index, linear_to_db(value))


func _show_focus() -> void:
	var on_pad := InputSettings.device == InputSettings.Device.GAMEPAD
	volume_slider.add_theme_stylebox_override("grabber_area_highlight", pad_slider_highlight if on_pad else slider_highlight)


func _on_device_changed(_device: int) -> void:
	_show_focus()
	_paint_footer()


func _build_footer() -> void:
	footer.add_theme_constant_override("separation", PauseArtLayout.FOOTER_SEPARATION)
	for hint in FOOTER_HINTS:
		var group := HBoxContainer.new()
		group.add_theme_constant_override("separation", PauseArtLayout.FOOTER_HINT_SEPARATION)
		group.alignment = BoxContainer.ALIGNMENT_CENTER
		footer.add_child(group)

		var word := Label.new()
		word.text = hint[0]
		word.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		word.add_theme_font_size_override("font_size", PauseArtLayout.FOOTER_FONT_SIZE)
		word.add_theme_color_override("font_color", PauseArtLayout.FOOTER_COLOR)
		group.add_child(word)

		var key := ControlsArtLayout.keycap("", PauseArtLayout.FOOTER_KEY_FONT_SIZE, PauseArtLayout.FOOTER_KEY_MIN_SIZE)
		group.add_child(key)
		footer_keys.append(key)

		var glyph := TextureRect.new()
		glyph.custom_minimum_size = PauseArtLayout.FOOTER_KEY_MIN_SIZE
		glyph.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		glyph.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		glyph.mouse_filter = Control.MOUSE_FILTER_IGNORE
		glyph.texture = ControlsArtLayout.pad_glyph_frame(InputSettings.PAD_BUTTON_FRAMES[hint[1]])
		group.add_child(glyph)
		footer_glyphs.append(glyph)


func _paint_footer() -> void:
	var drawn := InputSettings.device == InputSettings.Device.GAMEPAD and ControlsArtLayout.USE_FINAL_PAD_GLYPHS
	for i in footer_keys.size():
		footer_glyphs[i].visible = drawn
		footer_keys[i].visible = not drawn
		footer_keys[i].text = InputSettings.key_label_for(&"pause") if not drawn else ""


func _style_row(button: Button) -> void:
	button.custom_minimum_size = PauseArtLayout.ROW_MIN_SIZE
	button.add_theme_font_size_override("font_size", PauseArtLayout.ROW_FONT_SIZE)
	for state in ["normal", "hover", "pressed", "focus"]:
		button.add_theme_stylebox_override(state, PauseArtLayout.row_style(state))
	for colour in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color", "font_hover_pressed_color"]:
		button.add_theme_color_override(colour, PauseArtLayout.ROW_FONT_COLOR)
	var plain := PauseArtLayout.row_style("normal")
	var lit := PauseArtLayout.row_lit_style()
	# Into `normal`, not `hover`: a Button only enters DRAW_HOVER under the mouse, so on a pad the
	# hover face is never drawn and the ring would be the only mark of which row is selected.
	button.focus_entered.connect(func() -> void: button.add_theme_stylebox_override("normal", lit))
	button.focus_exited.connect(func() -> void: button.add_theme_stylebox_override("normal", plain))
