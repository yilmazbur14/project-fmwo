extends Control

@export var return_to_menu_button: Button
@export var music_player: AudioStreamPlayer
@export var timestamp_label: Label
@export var message_label: Label
@export var fade_in_time := 0.5


func _ready() -> void:
	return_to_menu_button.pressed.connect(_on_return_to_menu_button_pressed)

	if music_player:
		music_player.stream = load("res://Assets/Audio/Music/defeat_theme.ogg")
		if music_player.stream:
			music_player.stream.loop = true
		music_player.play()

	var arena := GameProgress.fight_index + 1 if GameProgress.fight_index >= 0 else 1
	timestamp_label.text = _chat_timestamp()
	message_label.text = "@newcomer was knocked out and kicked from #arena-%d." % arena
	_fade_in()


func _on_return_to_menu_button_pressed() -> void:
	if music_player and music_player.playing:
		music_player.stop()
	get_tree().change_scene_to_file("res://Scenes/Core/MainMenuScene.tscn")


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
