extends Sprite2D

@onready var animation_player: AnimationPlayer = $AnimationPlayer


func _ready() -> void:
	DialogueManager.dialogue_started.connect(_on_dialogue_started)
	DialogueManager.dialogue_ended.connect(_on_dialogue_ended)


func _on_dialogue_started(_resource: DialogueResource) -> void:
	animation_player.play("talk")


func _on_dialogue_ended(_resource: DialogueResource) -> void:
	animation_player.play("RESET")
