extends State

@export var animation_player : AnimationPlayer


func Enter() -> void:
	animation_player.play("defeated")
