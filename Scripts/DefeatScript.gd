extends Control

@export var return_to_menu_button: Button
@export var music_player: AudioStreamPlayer


func _ready() -> void:
	return_to_menu_button.pressed.connect(_on_return_to_menu_button_pressed)

	if music_player:
		music_player.stream = load("res://Assets/Audio/Music/defeat_theme.ogg")
		if music_player.stream:
			music_player.stream.loop = true
		music_player.play()


func _on_return_to_menu_button_pressed() -> void:
	if music_player and music_player.playing:
		music_player.stop()
	get_tree().change_scene_to_file("res://Scenes/Core/MainMenuScene.tscn")
