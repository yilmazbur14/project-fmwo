extends Control

# Playtest aid, not part of the game: a panel that jumps straight into any fight in the order.
# Set this to false for a real build and the panel is never built, so it takes no space and holds
# no keyboard focus.
const SHOW_BOSS_SELECT := true

# Under the volume slider, inside the column the menu art keeps clear of the boss tower. Three
# columns: ten rows in one would run off the bottom of the screen, and two no longer fit either now
# that a fight can have a second row under it (PHASE_TWO_FIGHTS). The slider ends at y 820 and the
# screen at 1080, so this panel can grow neither up nor down - the column count is the only knob.
const BOSS_SELECT_RECT := Rect2(156, 830, 664, 240)
const BOSS_SELECT_COLUMNS := 3
# Pixelify Sans is only crisp at multiples of its 11 px design size.
const BOSS_SELECT_FONT_SIZE := 22
const BOSS_SELECT_BUTTON_HEIGHT := 34

const ControlsArtLayout := preload("res://Scripts/ControlsArtLayout.gd")
const EricPacing := preload("res://Scripts/EricPacing.gd")

# Fights that get a second row under their own, jumping straight into their second phase rather than
# the start of the fight: the phase is at half health, so testing it otherwise means winning most of
# the fight first, every time. Keyed by fight scene, valued by the row's label. Eric's is the only one
# today; Computah's phase two is the next, and only needs a row here plus its own availability test in
# _phase_two_available().
const PHASE_TWO_FIGHTS := {
	"res://Scenes/Bosses/EricBossFightScene.tscn": "ERIC PHASE 2",
}

@export var arena_scene = "res://Scenes/Core/ArenaScene.tscn"
var intro_scene = "res://Scenes/Core/IntroCutsceneScene.tscn"
var controls_scene = "res://Scenes/Core/ControlsSettingsScene.tscn"
@export var start_game_button : Button
@export var controls_button : Button
@export var volume_slider : HSlider
@export var music_player : AudioStreamPlayer
@export var fade_in_time := 0.5

var master_bus_index := 0
# The menu's own looks, put back whenever the player isn't on a pad.
var menu_focus_style: StyleBox
var menu_slider_highlight: StyleBox
var pad_slider_highlight: StyleBoxTexture


# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	start_game_button.pressed.connect(_on_start_game_button_pressed)
	controls_button.pressed.connect(_on_controls_button_pressed)

	if music_player:
		music_player.stream = load("res://Assets/Audio/Music/main_menu_theme.ogg")
		if music_player.stream:
			music_player.stream.loop = true
		music_player.play()

	master_bus_index = AudioServer.get_bus_index("Master")
	if volume_slider:
		# Reflect whatever the current master volume already is (in case it
		# was changed earlier this session) instead of always resetting to full.
		if AudioServer.is_bus_mute(master_bus_index):
			volume_slider.value = 0.0
		else:
			volume_slider.value = db_to_linear(AudioServer.get_bus_volume_db(master_bus_index))
		volume_slider.value_changed.connect(_on_volume_slider_changed)

	_link_menu_focus()
	if SHOW_BOSS_SELECT:
		_build_boss_select()

	menu_focus_style = start_game_button.get_theme_stylebox("focus")
	menu_slider_highlight = volume_slider.get_theme_stylebox("grabber_area_highlight")
	pad_slider_highlight = menu_slider_highlight.duplicate() as StyleBoxTexture
	pad_slider_highlight.modulate_color = ControlsArtLayout.FOCUS_TINT
	_show_focus()
	InputSettings.device_changed.connect(_show_focus.unbind(1))

	_fade_in()


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	pass

func _on_start_game_button_pressed() -> void:
	GameProgress.reset_progress()
	get_tree().change_scene_to_file(intro_scene)


func _on_controls_button_pressed() -> void:
	get_tree().change_scene_to_file(controls_scene)


# Geometric navigation can't be trusted across the gap the menu art leaves, so the column is chained
# by hand: NEW GAME, CONTROLS, VOLUME, and on into the boss select when it's built.
func _link_menu_focus() -> void:
	var column: Array[Control] = [start_game_button, controls_button, volume_slider]
	for i in column.size():
		if i > 0:
			column[i].focus_neighbor_top = column[i - 1].get_path()
			column[i].focus_previous = column[i - 1].get_path()
		if i < column.size() - 1:
			column[i].focus_neighbor_bottom = column[i + 1].get_path()
			column[i].focus_next = column[i + 1].get_path()


# The menu draws no focus, which suits a mouse, but on a pad focus is the only way to see where you
# are. A slider can't draw a focus box at all, so it shows focus through its highlight art instead.
func _show_focus() -> void:
	var on_pad := InputSettings.device == InputSettings.Device.GAMEPAD
	for button in [start_game_button, controls_button]:
		button.add_theme_stylebox_override("focus", ControlsArtLayout.focus_ring() if on_pad else menu_focus_style)
	volume_slider.add_theme_stylebox_override("grabber_area_highlight", pad_slider_highlight if on_pad else menu_slider_highlight)


# One button per fight in GameProgress' order, so the panel can't drift out of step with the
# ladder. A fight whose scene hasn't been built yet shows as a disabled row rather than vanishing.
func _build_boss_select() -> void:
	var panel := PanelContainer.new()
	panel.position = BOSS_SELECT_RECT.position
	panel.size = BOSS_SELECT_RECT.size
	panel.add_theme_stylebox_override("panel", _boss_select_panel_style())
	add_child(panel)

	var rows := VBoxContainer.new()
	rows.add_theme_constant_override("separation", 4)
	panel.add_child(rows)

	var title := Label.new()
	title.text = "BOSS SELECT (PLAYTEST)"
	title.add_theme_font_size_override("font_size", BOSS_SELECT_FONT_SIZE)
	title.add_theme_color_override("font_color", Color(0.65, 0.68, 0.74))
	rows.add_child(title)

	# The player takes no damage, so a whole fight can be watched without dying. It sits above the
	# fight list because it applies to whichever of them you pick, and it is the head of the focus
	# chain below for the same reason.
	var invincible := CheckBox.new()
	invincible.text = "INVINCIBLE"
	invincible.button_pressed = GameProgress.playtest_invincible
	invincible.add_theme_font_size_override("font_size", BOSS_SELECT_FONT_SIZE)
	invincible.add_theme_color_override("font_color", Color(0.88, 0.9, 0.93))
	invincible.add_theme_color_override("font_hover_color", Color(1, 1, 1))
	invincible.toggled.connect(func(on: bool) -> void: GameProgress.playtest_invincible = on)
	rows.add_child(invincible)

	var columns := HBoxContainer.new()
	columns.add_theme_constant_override("separation", 8)
	rows.add_child(columns)

	var count := GameProgress.BOSSES.size()
	var per_column := ceili(float(count) / BOSS_SELECT_COLUMNS)
	var column: VBoxContainer = null
	# CheckBox is a Button, so the toggle rides the same hand-wired chain as the fights and keyboard
	# and pad navigation reach it. It is first: the volume slider hands down into it, then the fights.
	var chain: Array[Button] = [invincible]
	for i in count:
		if i % per_column == 0:
			column = VBoxContainer.new()
			column.add_theme_constant_override("separation", 4)
			column.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			columns.add_child(column)
		var boss: Dictionary = GameProgress.BOSSES[i]
		var scene: String = boss["scene"]
		var built: bool = ResourceLoader.exists(scene)
		var button := _boss_select_button("%d  %s" % [i + 1, boss["name"]])
		button.disabled = not built
		button.focus_mode = Control.FOCUS_ALL if built else Control.FOCUS_NONE
		if built:
			button.pressed.connect(_on_boss_select_pressed.bind(scene))
			chain.append(button)
		else:
			button.tooltip_text = "%s hasn't been built yet" % scene
		column.add_child(button)
		if PHASE_TWO_FIGHTS.has(scene):
			_add_phase_two_row(column, chain, scene, built)

	# Walk the list in table order whichever key is used, stepping over the fights that aren't
	# built yet and over the break between the two columns, which neither Godot's geometric
	# navigation nor tree order would follow on its own.
	for i in chain.size():
		var previous := chain[i - 1].get_path() if i > 0 else volume_slider.get_path()
		var next := chain[i + 1].get_path() if i < chain.size() - 1 else NodePath()
		chain[i].focus_previous = previous
		chain[i].focus_neighbor_top = previous
		chain[i].focus_next = next
		chain[i].focus_neighbor_bottom = next

	# The menu column hands down into the panel from the volume slider.
	if not chain.is_empty():
		volume_slider.focus_neighbor_bottom = chain[0].get_path()
		volume_slider.focus_next = chain[0].get_path()


# The second row under a fight that has a phase-two shortcut, drawn as one of its own rows and
# indented so it reads as belonging to the fight above it rather than as another fight.
func _add_phase_two_row(column: VBoxContainer, chain: Array[Button], scene: String, built: bool) -> void:
	var button := _boss_select_button("    %s" % PHASE_TWO_FIGHTS[scene])
	var available: bool = built and _phase_two_available(scene)
	button.disabled = not available
	button.focus_mode = Control.FOCUS_ALL if available else Control.FOCUS_NONE
	if available:
		button.pressed.connect(_on_phase_two_select_pressed.bind(scene))
		chain.append(button)
	elif not built:
		button.tooltip_text = "%s hasn't been built yet" % scene
	else:
		button.tooltip_text = "No second phase in this build"
	column.add_child(button)


# Whether the fight actually has the phase the row jumps to right now. Eric's is the reworked fight's
# alone (EricPacing V2): on V1 there is no sword to knock out of the ring and no phase two behind it.
func _phase_two_available(scene: String) -> bool:
	if scene == "res://Scenes/Bosses/EricBossFightScene.tscn":
		return EricPacing.is_v2()
	return false


func _boss_select_button(text: String) -> Button:
	var button := Button.new()
	button.text = text
	button.custom_minimum_size = Vector2(0, BOSS_SELECT_BUTTON_HEIGHT)
	button.alignment = HORIZONTAL_ALIGNMENT_LEFT
	button.clip_text = true
	button.add_theme_font_size_override("font_size", BOSS_SELECT_FONT_SIZE)
	for style_name in ["normal", "hover", "pressed", "disabled", "focus"]:
		button.add_theme_stylebox_override(style_name, _boss_select_button_style(style_name))
	button.add_theme_color_override("font_color", Color(0.88, 0.9, 0.93))
	button.add_theme_color_override("font_hover_color", Color(1, 1, 1))
	button.add_theme_color_override("font_disabled_color", Color(0.42, 0.44, 0.48))
	return button


func _boss_select_panel_style() -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.05, 0.05, 0.07, 0.88)
	style.border_color = Color(0.35, 0.36, 0.42)
	style.set_border_width_all(2)
	style.set_content_margin_all(8)
	return style


func _boss_select_button_style(style_name: String) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.14, 0.14, 0.17)
	match style_name:
		"hover":
			style.bg_color = Color(0.22, 0.23, 0.28)
		"pressed":
			style.bg_color = Color(0.09, 0.09, 0.11)
		"disabled":
			style.bg_color = Color(0.09, 0.09, 0.1)
	style.border_color = Color(0.9, 0.92, 0.95) if style_name == "focus" else Color(0.3, 0.31, 0.36)
	style.set_border_width_all(1)
	style.content_margin_left = 10
	return style


# Jumping in starts a fresh run at that fight: GameProgress reads fight_index back from the scene
# itself, so the fight's intro, its victory screen and the chain onward all behave as usual. No
# earlier boss is marked cleared, so the ladder only ever shows fights that were really fought.
func _on_boss_select_pressed(scene_path: String) -> void:
	GameProgress.reset_progress()
	get_tree().change_scene_to_file(scene_path)


# Straight into a fight's second phase. It ASKS for the phase rather than setting anything itself:
# the fight takes the request in its own _ready through the same entry point a crossing punch takes
# (EricScript.enter_phase_two) and leaves the transition cut owed, so what plays is exactly what the
# fight plays for real - the entrance, then the sword thrown out of the ring, its lines, then phase
# two. Nobody's health is touched, so he is in phase two on a full bar.
func _on_phase_two_select_pressed(scene_path: String) -> void:
	GameProgress.reset_progress()
	GameProgress.start_in_phase_two = scene_path
	get_tree().change_scene_to_file(scene_path)


func _on_volume_slider_changed(value: float) -> void:
	if value <= 0.001:
		AudioServer.set_bus_mute(master_bus_index, true)
	else:
		AudioServer.set_bus_mute(master_bus_index, false)
		AudioServer.set_bus_volume_db(master_bus_index, linear_to_db(value))


func _fade_in() -> void:
	var fade := ColorRect.new()
	fade.color = Color.BLACK
	fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(fade)
	var tween := create_tween()
	tween.tween_property(fade, "color:a", 0.0, fade_in_time)
	tween.tween_callback(fade.queue_free)
	# Nothing takes focus by itself, and a pad can only press what has it. Not before the screen is
	# up, though, as on the Victory and Defeat screens: an accept still held or mashed from whatever
	# led here - quitting a fight from the pause screen, or the rebind screen's Back - would
	# otherwise press NEW GAME before the player ever saw this menu.
	tween.tween_callback(start_game_button.grab_focus)
