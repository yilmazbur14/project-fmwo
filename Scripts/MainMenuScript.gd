extends Control

# Playtest aid, not part of the game: a panel that jumps straight into any fight in the order.
# Set this to false for a real build and the panel is never built, so it takes no space and holds
# no keyboard focus.
const SHOW_BOSS_SELECT := true

# Under the volume slider, inside the column the menu art keeps clear of the boss tower.
const BOSS_SELECT_RECT := Rect2(156, 714, 480, 350)
const BOSS_SELECT_FONT_SIZE := 22
const BOSS_SELECT_BUTTON_HEIGHT := 40

@export var arena_scene = "res://Scenes/Core/ArenaScene.tscn"
var intro_scene = "res://Scenes/Core/IntroCutsceneScene.tscn"
@export var start_game_button : Button
@export var volume_slider : HSlider
@export var music_player : AudioStreamPlayer
@export var fade_in_time := 0.5

var master_bus_index := 0


# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	start_game_button.pressed.connect(_on_start_game_button_pressed)

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

	if SHOW_BOSS_SELECT:
		_build_boss_select()

	_fade_in()


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	pass

func _on_start_game_button_pressed() -> void:
	GameProgress.reset_progress()
	get_tree().change_scene_to_file(intro_scene)


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

	for i in GameProgress.BOSSES.size():
		var boss: Dictionary = GameProgress.BOSSES[i]
		var scene: String = boss["scene"]
		var built: bool = ResourceLoader.exists(scene)
		var button := Button.new()
		button.text = "%d  %s" % [i + 1, boss["name"]]
		button.custom_minimum_size = Vector2(0, BOSS_SELECT_BUTTON_HEIGHT)
		button.alignment = HORIZONTAL_ALIGNMENT_LEFT
		button.add_theme_font_size_override("font_size", BOSS_SELECT_FONT_SIZE)
		for style_name in ["normal", "hover", "pressed", "disabled", "focus"]:
			button.add_theme_stylebox_override(style_name, _boss_select_button_style(style_name))
		button.add_theme_color_override("font_color", Color(0.88, 0.9, 0.93))
		button.add_theme_color_override("font_hover_color", Color(1, 1, 1))
		button.add_theme_color_override("font_disabled_color", Color(0.42, 0.44, 0.48))
		button.disabled = not built
		# A disabled row must not swallow a keyboard step on its way down the list.
		button.focus_mode = Control.FOCUS_ALL if built else Control.FOCUS_NONE
		if built:
			button.pressed.connect(_on_boss_select_pressed.bind(scene))
		else:
			button.tooltip_text = "%s hasn't been built yet" % scene
		rows.add_child(button)

	# The panel is added after the menu's own controls, but make sure it can never be what the
	# keyboard lands on first.
	start_game_button.grab_focus()


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
