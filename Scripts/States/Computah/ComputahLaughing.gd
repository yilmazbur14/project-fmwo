extends State

@export var animation_player : AnimationPlayer
@export var greyson_animation_player : AnimationPlayer

func Enter() -> void:
	animation_player.play("laughing")
	if greyson_animation_player:
		greyson_animation_player.play("laughing")

func Exit() -> void:
	if greyson_animation_player:
		greyson_animation_player.play("RESET")

func Update(_delta: float) -> void:
	pass

func Physics_Update(_delta: float) -> void:
	pass
