extends State

@export var animation_player : AnimationPlayer
@export var hurtbox : Area2D

func Enter() -> void:
	animation_player.play("idle")
	if hurtbox:
		hurtbox.monitoring = false
		hurtbox.monitorable = false

func Exit() -> void:
	pass

func Update(_delta: float) -> void:
	pass

func Physics_Update(_delta: float) -> void:
	pass
