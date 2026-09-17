extends State

@export var animation_player : AnimationPlayer
@export var hurtbox : Area2D


func Enter() -> void:
	animation_player.play("idle")
	hurtbox.monitoring = false
	hurtbox.monitorable = false
