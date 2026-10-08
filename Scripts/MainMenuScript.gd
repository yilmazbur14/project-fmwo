extends Control

# The boss select: a panel that jumps straight into a fight as practice, never touching the progress save. In the
# editor, which is also the playtest build (GameProgress.playtest_build), it lists every fight in the order and has the
# INVINCIBLE toggle. In an exported build it lists only what the player has beaten (the user, 2026-10-08: "only if
# theyve beat the boss. They shouldnt be able to see the name of the next boss in this menu"), with no toggle, and
# until something is beaten it isn't built at all, so it takes no space and holds no keyboard focus.

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

# CONTINUE, only when the save has a run to pick up (the user, 2026-10-07: "lets add progress saving"): a copy of NEW
# GAME above it, with where it resumes ("VS CARTER") written small under the word. The column has no room above NEW GAME
# for another button of its size, so the title rises by TITLE_RISE to make it, and only then.
const CONTINUE_TOP := 274.0
const TITLE_RISE := 32.0
# The word moves up this far inside the button, and the caption's line sits at CAPTION_TOP from its top: both inside the
# art's 24 px frame.
const CONTINUE_TEXT_RISE := 14.0
const CAPTION_TOP := 75.0
const CAPTION_FONT_SIZE := 22
# NEW GAME over a run CONTINUE could pick up asks first, in the pause screen's question box, with the menu's buttons.
const CONFIRM_NEW_GAME := "START OVER?\nYOUR PROGRESS WILL BE LOST."
const CONFIRM_BUTTON_SIZE := Vector2(400, 126)

const ControlsArtLayout := preload("res://Scripts/ControlsArtLayout.gd")
const PauseArtLayout := preload("res://Scripts/PauseArtLayout.gd")

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
# Built only with a run to continue; null otherwise, and so is the question NEW GAME asks.
var continue_button: Button
var continue_caption: Label
var confirm: Control
var confirm_back_button: Button
var confirm_ok_button: Button


# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	start_game_button.pressed.connect(_on_start_game_button_pressed)
	controls_button.pressed.connect(_on_controls_button_pressed)

	var carried := GameProgress.take_carried_music()
	if carried:
		# Back from CONTROLS: the theme that played on through it takes this scene's player's place, still playing.
		remove_child(music_player)
		music_player.queue_free()
		carried.reparent(self)
		music_player = carried
	elif music_player:
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

	if GameProgress.has_resume():
		_build_continue()
	_link_menu_focus()
	var entries := _boss_select_entries()
	if not entries.is_empty():
		_build_boss_select(entries)
	# Last, so the question is drawn over the boss select too.
	if continue_button:
		_build_confirm()

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

# Over a run CONTINUE could pick up, it asks first.
func _on_start_game_button_pressed() -> void:
	if confirm:
		_ask_new_game()
		return
	_start_new_game()


func _start_new_game() -> void:
	GameProgress.start_new_run()
	get_tree().change_scene_to_file(intro_scene)


func _on_continue_button_pressed() -> void:
	get_tree().change_scene_to_file(GameProgress.continue_run())


# The theme goes on playing through the CONTROLS screen, and the menu picks it up again where it is on Back.
func _on_controls_button_pressed() -> void:
	if music_player:
		GameProgress.carry_music(music_player)
	get_tree().change_scene_to_file(controls_scene)


# A copy of NEW GAME, as the Defeat screen's RETRY is of its button, so it is that button exactly - art, font, colours and
# size - with the word lifted inside it to leave a line for the caption.
func _build_continue() -> void:
	continue_button = start_game_button.duplicate(0) as Button
	continue_button.name = "ContinueButton"
	continue_button.text = "CONTINUE"
	continue_button.position.y = CONTINUE_TOP
	for style_name in ["normal", "hover", "pressed"]:
		var style: StyleBox = start_game_button.get_theme_stylebox(style_name).duplicate()
		style.content_margin_top -= CONTINUE_TEXT_RISE
		style.content_margin_bottom += CONTINUE_TEXT_RISE
		continue_button.add_theme_stylebox_override(style_name, style)
	add_child(continue_button)
	continue_button.pressed.connect(_on_continue_button_pressed)

	continue_caption = Label.new()
	continue_caption.name = "Caption"
	continue_caption.text = GameProgress.resume_label()
	continue_caption.add_theme_font_size_override("font_size", CAPTION_FONT_SIZE)
	continue_caption.add_theme_color_override("font_color", Color(1, 1, 1))
	continue_caption.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	continue_caption.position = Vector2(0, CAPTION_TOP)
	continue_caption.size.x = continue_button.size.x
	continue_button.add_child(continue_caption)

	$TitleLogo.position.y -= TITLE_RISE


# The pause screen's question box (its art, sizes and dim), with two of the menu's own buttons. BACK has the focus when it
# opens, so a mashed accept can't start over by itself.
func _build_confirm() -> void:
	confirm = Control.new()
	confirm.name = "NewGameConfirm"
	confirm.visible = false
	confirm.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(confirm)

	var dim := ColorRect.new()
	dim.color = PauseArtLayout.DIM_COLOR
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	# It takes the mouse too, so nothing on the menu behind it can be clicked while the question is up.
	dim.mouse_filter = Control.MOUSE_FILTER_STOP
	confirm.add_child(dim)

	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	confirm.add_child(center)
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", PauseArtLayout.confirm_panel_style())
	center.add_child(panel)
	var margin := MarginContainer.new()
	for side in ["left", "top", "right", "bottom"]:
		margin.add_theme_constant_override("margin_" + side, PauseArtLayout.PANEL_MARGIN)
	panel.add_child(margin)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", PauseArtLayout.COLUMN_SEPARATION)
	margin.add_child(column)

	var message := Label.new()
	message.name = "Message"
	message.text = CONFIRM_NEW_GAME
	message.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	message.add_theme_font_size_override("font_size", PauseArtLayout.ROW_FONT_SIZE)
	message.add_theme_color_override("font_color", PauseArtLayout.CONFIRM_MESSAGE_COLOR)
	column.add_child(message)

	var buttons := HBoxContainer.new()
	buttons.alignment = BoxContainer.ALIGNMENT_CENTER
	buttons.add_theme_constant_override("separation", PauseArtLayout.CONFIRM_BUTTON_SEPARATION)
	column.add_child(buttons)
	confirm_back_button = _confirm_button("BackButton", "BACK")
	confirm_ok_button = _confirm_button("StartOverButton", "START OVER")
	buttons.add_child(confirm_back_button)
	buttons.add_child(confirm_ok_button)
	confirm_back_button.pressed.connect(_close_confirm)
	confirm_ok_button.pressed.connect(_start_new_game)

	# The two point only at each other, so neither the d-pad nor Tab can leave the question for the menu under it.
	for pair in [[confirm_back_button, confirm_ok_button], [confirm_ok_button, confirm_back_button]]:
		var here: Button = pair[0]
		var other: Button = pair[1]
		for side in [SIDE_LEFT, SIDE_RIGHT]:
			here.set_focus_neighbor(side, other.get_path())
		for side in [SIDE_TOP, SIDE_BOTTOM]:
			here.set_focus_neighbor(side, here.get_path())
		here.focus_next = other.get_path()
		here.focus_previous = other.get_path()


func _confirm_button(button_name: String, text: String) -> Button:
	var button := start_game_button.duplicate(0) as Button
	button.name = button_name
	button.text = text
	button.custom_minimum_size = CONFIRM_BUTTON_SIZE
	return button


func _ask_new_game() -> void:
	confirm.visible = true
	confirm_back_button.grab_focus()


func _close_confirm() -> void:
	confirm.visible = false
	start_game_button.grab_focus()


# B or Escape backs out of the question, as they do out of the pause screen's.
func _unhandled_input(event: InputEvent) -> void:
	if confirm and confirm.visible and event.is_action_pressed(&"ui_cancel"):
		get_viewport().set_input_as_handled()
		_close_confirm()


# Geometric navigation can't be trusted across the gap the menu art leaves, so the column is chained
# by hand: CONTINUE when there is a run to continue, NEW GAME, CONTROLS, VOLUME, and on into the boss
# select when it's built.
func _link_menu_focus() -> void:
	var column: Array[Control] = [start_game_button, controls_button, volume_slider]
	if continue_button:
		column.push_front(continue_button)
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
	for button in [continue_button, start_game_button, controls_button, confirm_back_button, confirm_ok_button]:
		if button:
			button.add_theme_stylebox_override("focus", ControlsArtLayout.focus_ring() if on_pad else menu_focus_style)
	volume_slider.add_theme_stylebox_override("grabber_area_highlight", pad_slider_highlight if on_pad else menu_slider_highlight)


# The rows in GameProgress' order, so the panel can't drift out of step with the ladder: [text, the scene it loads, its
# kind - &"" a fight, &"greyson", &"liam", &"finale", &"god" or &"ending"]. In the playtest build, all of them: one per
# fight, the GREYSON row after FIGHT 06's, the LIAM row after FIGHT 07's and the FINALE, GOD and ENDING rows after FIGHT
# 10's. In an exported build only what the player has beaten, so no row ever names a fight still to come: a half comes
# with its fight once that is beaten (Greyson's and Liam's, and Jordan's finale with his kaiju), his last phase once it is
# won and the ending once the game is finished.
func _boss_select_entries() -> Array[Array]:
	var all: bool = GameProgress.playtest_build
	var entries: Array[Array] = []
	for i in GameProgress.BOSSES.size():
		var boss: Dictionary = GameProgress.BOSSES[i]
		var scene: String = boss["scene"]
		var won: bool = all or GameProgress.has_beaten(scene)
		if won:
			entries.append(["%d  %s" % [i + 1, boss["name"]], scene, &""])
		if won and scene == GREYSON_ROW_FIGHT:
			entries.append([GREYSON_ROW, scene, &"greyson"])
		if won and scene == LIAM_ROW_FIGHT:
			entries.append([LIAM_ROW, scene, &"liam"])
		if scene == FINALE_ROW_FIGHT:
			if won:
				entries.append([FINALE_ROW, scene, &"finale"])
			if all or GameProgress.has_beaten(GOD_SCENE):
				entries.append([GOD_ROW, GOD_SCENE, &"god"])
			if all or GameProgress.saved_finished:
				entries.append([ENDING_ROW, ENDING_SCENE, &"ending"])
	return entries


# One button per row of `entries`, three columns filled by rows rather than by fights, so the GREYSON, LIAM, FINALE, GOD
# and ENDING rows take a place like any other. A fight whose scene hasn't been built yet shows as a disabled row rather
# than vanishing. The playtest build's panel has the INVINCIBLE toggle by its title.
func _build_boss_select(entries: Array[Array]) -> void:
	var playtest: bool = GameProgress.playtest_build
	var panel := PanelContainer.new()
	panel.position = BOSS_SELECT_RECT.position
	# An exported build's panel holds only what has been beaten, often a row or two, so it is only as tall as they are.
	panel.size = BOSS_SELECT_RECT.size if playtest else Vector2(BOSS_SELECT_RECT.size.x, 0)
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
	title.text = "BOSS SELECT (PLAYTEST)" if playtest else "BOSS SELECT"
	title.add_theme_font_size_override("font_size", BOSS_SELECT_FONT_SIZE)
	title.add_theme_color_override("font_color", Color(0.65, 0.68, 0.74))
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	heading.add_child(title)

	# CheckBox is a Button, so the toggle rides the same hand-wired chain as the fights and keyboard
	# and pad navigation reach it. It is first: the volume slider hands down into it, then the fights.
	var chain: Array[Button] = []
	if playtest:
		chain.append(_build_invincible(heading))

	var columns := HBoxContainer.new()
	columns.add_theme_constant_override("separation", 8)
	rows.add_child(columns)

	var per_column := ceili(float(entries.size()) / BOSS_SELECT_COLUMNS)
	var column: VBoxContainer = null
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


# The player takes no damage, so a whole fight can be watched without dying. It sits above the
# fight list because it applies to whichever of them you pick, and it is the head of the focus
# chain below for the same reason.
func _build_invincible(heading: HBoxContainer) -> CheckBox:
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
	return invincible


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
	GameProgress.set_volume(value)


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
	tween.tween_callback(_take_first_focus)


# CONTINUE, when it is there, is what a returning player wants, so it has the focus first. Not over the
# question, though: a mouse can click NEW GAME while the menu is still fading in, and the focus moved
# to CONTINUE under the dim would let Enter continue the run the question is about.
func _take_first_focus() -> void:
	if confirm and confirm.visible:
		return
	(continue_button if continue_button else start_game_button).grab_focus()
