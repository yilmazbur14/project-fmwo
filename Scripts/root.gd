extends Control

var main_menu_scene = preload("res://Scenes/Core/MainMenuScene.tscn").instantiate()
var arena_scene = preload("res://Scenes/Core/ArenaScene.tscn").instantiate()
var defeat_scene = preload("res://Scenes/Core/DefeatScene.tscn").instantiate()
var intro_scene = preload("res://Scenes/Core/IntroScene.tscn").instantiate()
var victory_scene = preload("res://Scenes/Core/VictoryScene.tscn").instantiate()


# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	add_child(main_menu_scene)
	main_menu_scene.anchors_preset = Control.PRESET_FULL_RECT


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	pass
