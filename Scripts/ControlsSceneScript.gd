extends Control

@onready var ReadyButton: Button = %ReadyButton


func _ready() -> void:
	_set_ready_button_locked(true)
	DialogueManager.show_dialogue_balloon(load("res://Dialogue/ControlsSceneDialogue.dialogue"), "start")
	DialogueManager.dialogue_ended.connect(_on_dialogue_ended)

	ReadyButton.pressed.connect(_on_ready_button_pressed)


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	pass

func _on_ready_button_pressed() -> void:
	get_tree().change_scene_to_file("res://Scenes/Bosses/EricBossFightScene.tscn")

func _on_dialogue_ended(dialogue: Object) -> void:
	# get_tree().change_scene_to_file("res://Scenes/ArenaScene.tscn")
	_set_ready_button_locked(false)

func _set_ready_button_locked(locked: bool) -> void:
	ReadyButton.disabled = locked
	ReadyButton.focus_mode = Control.FOCUS_NONE if locked else Control.FOCUS_ALL