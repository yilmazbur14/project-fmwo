extends Control

# Playtest aid, not part of the game: a panel that jumps straight into any fight in the order.
# Set this to false for a real build and the panel is never built, so it takes no space and holds
# no keyboard focus.
const SHOW_BOSS_SELECT := true

# Under the volume slider, inside the column the menu art keeps clear of the boss tower. Three
# columns, because ten rows in one would run off the bottom of the screen. The slider ends at y 820 and
# the screen at 1080, so this panel can grow neither up nor down - the column count is the only knob.
const BOSS_SELECT_RECT := Rect2(156, 830, 664, 240)
const BOSS_SELECT_COLUMNS := 3
# Pixelify Sans is only crisp at multiples of its 11 px design size.
const BOSS_SELECT_FONT_SIZE := 22
const BOSS_SELECT_BUTTON_HEIGHT := 34
# FIGHT 06's second half has a row of its own, right after the fight's and indented under it so it reads as part
# of that fight rather than another one: it opens the fight on Greyson's takeover (GameProgress.start_at_greyson).
const GREYSON_ROW_FIGHT := "res://Scenes/Bosses/ComputahBossFightScene.tscn"
const GREYSON_ROW := "    GREYSON"
const GREYSON_SCENE := "res://Scenes/Bosses/GreysonScene.tscn"
# FIGHT 10's finale has one too, the same way: it opens the fight at Jordan's KO (GameProgress.start_at_finale), and
# needs his room's scene built.
const FINALE_ROW_FIGHT := "res://Scenes/Bosses/JordanBossFightScene.tscn"
const FINALE_ROW := "    FINALE"
const FINALE_SCENE := "res://Scenes/Core/JordanFinaleScene.tscn"
# And his last phase, the Puppet Master, after the FINALE row: straight into that fight, with no finale before it.
const GOD_ROW := "    GOD"
const GOD_SCENE := "res://Scenes/Bosses/JordanGodFightScene.tscn"
# And the game's ending after his last phase, the champion cutscene and its credits, straight in, whatever its switch
# (ChampionEndingLayout.USE_CHAMPION_ENDING) says. Fifteen rows in three columns is the panel's limit: a sixteenth would
# run it past BOSS_SELECT_RECT.
const ENDING_ROW := "    ENDING"
const ENDING_SCENE := "res://Scenes/Core/ChampionEndingScene.tscn"
# FIGHT 07's second half has one as well, the way FIGHT 06's does: it opens the fight on Liam's takeover
# (GameProgress.start_at_liam), and needs his scene built.
const LIAM_ROW_FIGHT := "res://Scenes/Bosses/LiamBossFightScene.tscn"
const LIAM_ROW := "    LIAM"
const LIAM_SCENE := "res://Scenes/Bosses/LiamScene.tscn"
# The INVINCIBLE toggle's box, drawn for this panel: the theme's default empty box barely shows on it.
const INVINCIBLE_ICONS := {
	"unchecked": preload("res://Assets/UI/checkbox_off_2x.png"),
	"checked": preload("res://Assets/UI/checkbox_on_2x.png"),
	"unchecked_disabled": preload("res://Assets/UI/checkbox_off_disabled_2x.png"),
	"checked_disabled": preload("res://Assets/UI/checkbox_on_disabled_2x.png"),
}

const ControlsArtLayout := preload("res://Scripts/ControlsArtLayout.gd")

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
# ladder, the GREYSON row after FIGHT 06's, the LIAM row after FIGHT 07's and the FINALE and GOD rows after FIGHT 10's. A fight
# whose scene hasn't been built yet shows as a disabled row rather than vanishing.
func _build_boss_select() -> void:
	var panel := PanelContainer.new()
	panel.position = BOSS_SELECT_RECT.position
	panel.size = BOSS_SELECT_RECT.size
	panel.add_theme_stylebox_override("panel", _boss_select_panel_style())
	add_child(panel)

	var rows := VBoxContainer.new()
	rows.add_theme_constant_override("separation", 4)
	panel.add_child(rows)

	# The title and the INVINCIBLE toggle share the first row: on a row of its own the toggle made the
	# panel taller than BOSS_SELECT_RECT, and its last fight ran off the bottom of the screen.
	var heading := HBoxContainer.new()
	rows.add_child(heading)

	var title := Label.new()
	title.text = "BOSS SELECT (PLAYTEST)"
	title.add_theme_font_size_override("font_size", BOSS_SELECT_FONT_SIZE)
	title.add_theme_color_override("font_color", Color(0.65, 0.68, 0.74))
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	heading.add_child(title)

	# The player takes no damage, so a whole fight can be watched without dying. It sits above the
	# fight list because it applies to whichever of them you pick, and it is the head of the focus
	# chain below for the same reason.
	var invincible := CheckBox.new()
	invincible.text = "INVINCIBLE"
	invincible.button_pressed = GameProgress.playtest_invincible
	invincible.add_theme_font_size_override("font_size", BOSS_SELECT_FONT_SIZE)
	invincible.add_theme_color_override("font_color", Color(0.88, 0.9, 0.93))
	invincible.add_theme_color_override("font_hover_color", Color(1, 1, 1))
	for icon_name in INVINCIBLE_ICONS:
		invincible.add_theme_icon_override(icon_name, INVINCIBLE_ICONS[icon_name])
	invincible.add_theme_constant_override("h_separation", 8)
	# Focused, it is framed the way the fights under it are, not with the theme's rounded ring.
	invincible.add_theme_stylebox_override("focus", _boss_select_button_style("focus"))
	invincible.toggled.connect(func(on: bool) -> void: GameProgress.playtest_invincible = on)
	heading.add_child(invincible)
	# The theme pads a toggle 4 px above and below its text, which would make this row 8 px taller than
	# the title. Those styles draw nothing, so trimming them changes the height and nothing else.
	for style_name in ["normal", "pressed", "hover", "hover_pressed", "disabled"]:
		var style: StyleBox = invincible.get_theme_stylebox(style_name).duplicate()
		style.content_margin_top = 0
		style.content_margin_bottom = 0
		invincible.add_theme_stylebox_override(style_name, style)

	var columns := HBoxContainer.new()
	columns.add_theme_constant_override("separation", 8)
	rows.add_child(columns)

	# The rows in order, and the columns are filled by rows rather than by fights, so the GREYSON, LIAM, FINALE and GOD
	# rows take a place like any other: [text, the scene it loads, its kind - &"" a fight, &"greyson", &"liam", &"finale"
	# or &"god"].
	var entries: Array[Array] = []
	for i in GameProgress.BOSSES.size():
		var boss: Dictionary = GameProgress.BOSSES[i]
		entries.append(["%d  %s" % [i + 1, boss["name"]], boss["scene"], &""])
		if boss["scene"] == GREYSON_ROW_FIGHT:
			entries.append([GREYSON_ROW, boss["scene"], &"greyson"])
		if boss["scene"] == LIAM_ROW_FIGHT:
			entries.append([LIAM_ROW, boss["scene"], &"liam"])
		if boss["scene"] == FINALE_ROW_FIGHT:
			entries.append([FINALE_ROW, boss["scene"], &"finale"])
			entries.append([GOD_ROW, GOD_SCENE, &"god"])
			entries.append([ENDING_ROW, ENDING_SCENE, &"ending"])
	var per_column := ceili(float(entries.size()) / BOSS_SELECT_COLUMNS)
	var column: VBoxContainer = null
	# CheckBox is a Button, so the toggle rides the same hand-wired chain as the fights and keyboard
	# and pad navigation reach it. It is first: the volume slider hands down into it, then the fights.
	var chain: Array[Button] = [invincible]
	for i in entries.size():
		if i % per_column == 0:
			column = VBoxContainer.new()
			column.add_theme_constant_override("separation", 4)
			column.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			columns.add_child(column)
		var scene: String = entries[i][1]
		var kind: StringName = entries[i][2]
		var needs: String = {&"greyson": GREYSON_SCENE, &"liam": LIAM_SCENE, &"finale": FINALE_SCENE, &"ending": ENDING_SCENE}.get(kind, scene)
		var built: bool = ResourceLoader.exists(scene) and ResourceLoader.exists(needs)
		var button := _boss_select_button(entries[i][0])
		button.disabled = not built
		button.focus_mode = Control.FOCUS_ALL if built else Control.FOCUS_NONE
		if built:
			var pressed: Callable = {&"greyson": _on_greyson_select_pressed, &"liam": _on_liam_select_pressed, &"finale": _on_finale_select_pressed, &"ending": _on_ending_select_pressed}.get(kind, _on_boss_select_pressed)
			button.pressed.connect(pressed.bind(scene))
			chain.append(button)
		else:
			button.tooltip_text = "%s hasn't been built yet" % (needs if ResourceLoader.exists(scene) else scene)
		column.add_child(button)

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


# FIGHT 06 from Greyson's takeover. It ASKS rather than setting anything up itself: the fight takes the request
# as it loads (ComputahStateMachine._ready) and puts Computah down with no fight of his first, so what plays is
# the takeover the real fight plays, hold-to-skip and all, then Greyson's fight, won and lost the way the real
# one is: the same Victory and Defeat, Liam & Bixby next, and the pause screen's restart starting FIGHT 06 over.
func _on_greyson_select_pressed(scene_path: String) -> void:
	GameProgress.reset_progress()
	GameProgress.start_at_greyson = true
	get_tree().change_scene_to_file(scene_path)


# FIGHT 07 from Liam's takeover: Bixby already down, then Liam's own phase. It asks, as the GREYSON row does, and the
# fight takes the request as it loads (BixbyBeastStateMachine._ready).
func _on_liam_select_pressed(scene_path: String) -> void:
	GameProgress.reset_progress()
	GameProgress.start_at_liam = true
	get_tree().change_scene_to_file(scene_path)


# FIGHT 10 from Jordan's KO: the whole finale a win plays - the walk-out, his room, the collapse and the card. It asks,
# as the GREYSON row does, and the fight takes the request as it loads (JordanStateMachine._ready).
func _on_finale_select_pressed(scene_path: String) -> void:
	GameProgress.reset_progress()
	GameProgress.start_at_finale = true
	get_tree().change_scene_to_file(scene_path)


# The ending on its own, from a fresh run.
func _on_ending_select_pressed(scene_path: String) -> void:
	GameProgress.reset_progress()
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
