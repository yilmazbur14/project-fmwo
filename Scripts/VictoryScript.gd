extends Control

@export var next_boss_button: Button

func _ready() -> void:
	if next_boss_button:
		next_boss_button.pressed.connect(_on_next_boss_button_pressed)
		if GameProgress.next_boss_scene == "":
			next_boss_button.text = "MAIN MENU"
		else:
			next_boss_button.text = "NEXT BOSS"

func _on_next_boss_button_pressed() -> void:
	if GameProgress.next_boss_scene != "":
		get_tree().change_scene_to_file(GameProgress.next_boss_scene)
	else:
		get_tree().change_scene_to_file("res://Scenes/Core/MainMenuScene.tscn")
