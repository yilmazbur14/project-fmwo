extends State

@export var animation_player : AnimationPlayer


func Enter() -> void:
	animation_player.clear_queue()
	animation_player.play("defeat")
