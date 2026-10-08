extends Control

const ControlsArtLayout := preload("res://Scripts/ControlsArtLayout.gd")

# RETRY and RETURN TO MAIN MENU side by side, centred where the one button was. They can't stack: the banner sits
# just under the fallen player, and two buttons this tall don't fit in what the screen leaves below it.
const BUTTON_GAP := 24.0

@export var return_to_menu_button: Button
@export var music_player: AudioStreamPlayer
@export var timestamp_label: Label
@export var message_label: Label
@export var fade_in_time := 0.5

# Only when there is a fight to retry (GameProgress.retry_scene); without one the screen keeps its one button.
var retry_button: Button
var menu_focus_style: StyleBox
# The fight RETRY opens, loading on threads behind this screen the way Victory loads NEXT BOSS's.
var _prefetching := false
# The path it was requested under, for _exit_tree: GameProgress.retry_scene can be changed under the screen.
var _prefetch_path := ""
var _leaving := false


func _ready() -> void:
	return_to_menu_button.pressed.connect(_on_return_to_menu_button_pressed)
	if GameProgress.retry_scene != "":
		_build_retry_button()
		_prefetch_path = GameProgress.retry_scene
		_prefetching = ResourceLoader.load_threaded_request(_prefetch_path) == OK

	if music_player:
		music_player.stream = load("res://Assets/Audio/Music/defeat_theme.ogg")
		if music_player.stream:
			music_player.stream.loop = true
		music_player.play()

	var arena := GameProgress.fight_index + 1 if GameProgress.fight_index >= 0 else 1
	timestamp_label.text = _chat_timestamp()
	message_label.text = "@newcomer was knocked out and kicked from #arena-%d." % arena
	_fade_in()


# A copy of RETURN TO MAIN MENU, so it is that button exactly - art, font, colours and size - on its left, first.
func _build_retry_button() -> void:
	retry_button = return_to_menu_button.duplicate(0) as Button
	retry_button.name = "RetryButton"
	retry_button.text = "RETRY"
	add_child(retry_button)
	var width := return_to_menu_button.size.x
	var left := return_to_menu_button.position.x + width / 2.0 - width - BUTTON_GAP / 2.0
	retry_button.position.x = left
	return_to_menu_button.position.x = left + width + BUTTON_GAP
	retry_button.pressed.connect(_on_retry_button_pressed)

	retry_button.focus_neighbor_right = return_to_menu_button.get_path()
	retry_button.focus_next = return_to_menu_button.get_path()
	return_to_menu_button.focus_neighbor_left = retry_button.get_path()
	return_to_menu_button.focus_previous = retry_button.get_path()

	menu_focus_style = return_to_menu_button.get_theme_stylebox("focus")
	_show_focus()
	InputSettings.device_changed.connect(_show_focus.unbind(1))


# The screen draws no focus, which suited one button; with two, a pad needs to see which one A presses. The main
# menu's own buttons, the same art, show it the same way.
func _show_focus() -> void:
	var on_pad := InputSettings.device == InputSettings.Device.GAMEPAD
	for button in [retry_button, return_to_menu_button]:
		button.add_theme_stylebox_override("focus", ControlsArtLayout.focus_ring() if on_pad else menu_focus_style)


# The fight just lost, from where the pause screen's RESTART FIGHT would start it, straight to the fight: its walk-in,
# lines and VS card skipped (GameProgress.arm_retry). Once: a second press while it loads would open it twice.
func _on_retry_button_pressed() -> void:
	if _leaving:
		return
	_leaving = true
	_stop_music()
	var scene := GameProgress.arm_retry()
	var fight: PackedScene = ResourceLoader.load_threaded_get(scene) if _prefetching else null
	if fight != null:
		get_tree().change_scene_to_packed(fight)
	else:
		get_tree().change_scene_to_file(scene)


func _on_return_to_menu_button_pressed() -> void:
	if _leaving:
		return
	_leaving = true
	_stop_music()
	get_tree().change_scene_to_file("res://Scenes/Core/MainMenuScene.tscn")


# Quitting on this screen with the prefetch still loading tears the engine down under the loader's threads, and the
# half-loaded fight prints parse errors at exit: waiting for it here closes it first. Not when a button left - RETRY has
# taken it, and RETURN TO MAIN MENU lets it finish behind the menu rather than stall the press.
func _exit_tree() -> void:
	if _prefetching and not _leaving:
		ResourceLoader.load_threaded_get(_prefetch_path)


func _stop_music() -> void:
	if music_player and music_player.playing:
		music_player.stop()


func _chat_timestamp() -> String:
	var now := Time.get_time_dict_from_system()
	var hour: int = now.hour % 12
	if hour == 0:
		hour = 12
	return "Today at %d:%02d %s" % [hour, now.minute, "AM" if now.hour < 12 else "PM"]


func _fade_in() -> void:
	var fade := ColorRect.new()
	fade.color = Color.BLACK
	fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(fade)
	var tween := create_tween()
	tween.tween_property(fade, "color:a", 0.0, fade_in_time)
	tween.tween_callback(fade.queue_free)
	# Nothing takes focus by itself: without this a pad can't press either button. Not before the screen is up,
	# though: A punches too, and a player still mashing it as the fight was lost would retry, or be sent to the menu,
	# before ever seeing this screen.
	tween.tween_callback((retry_button if retry_button else return_to_menu_button).grab_focus)
