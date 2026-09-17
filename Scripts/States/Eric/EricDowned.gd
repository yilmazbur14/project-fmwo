extends State

@export var animation_player : AnimationPlayer
@export var hurtbox : Area2D


# Called when the node enters the scene tree for the first time.
func Enter() -> void:
	animation_player.play("downed")
	hurtbox.monitoring = true
	hurtbox.monitorable = true
	hurtbox.get_parent().daze_used = false


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	pass
