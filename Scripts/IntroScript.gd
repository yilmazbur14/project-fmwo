extends Control


# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	DialogueManager.show_dialogue_balloon(load("res://Dialogue/DannyIntro.dialogue"), "start")
	DialogueManager.dialogue_ended.connect(_on_dialogue_ended)


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	pass

func _on_dialogue_ended(dialogue: Object) -> void:
	get_tree().change_scene_to_file("res://Scenes/Core/ControlsScene.tscn")
