extends State

@export var punching_animation : String = "punch"
# @export var speed_threshold : float = 0.1
@export var animation_player : AnimationPlayer
@export var hitBox : Area2D
@export var player : CharacterBody2D

func Enter() -> void:
	hitBox.monitoring = true
	hitBox.monitorable = true
	animation_player.speed_scale = 2.0  # Speed up only the punch animation
	animation_player.play(punching_animation)

func Exit() -> void:
	hitBox.monitoring = false  # Disable hitbox when exiting punch state
	hitBox.monitorable = false
	animation_player.speed_scale = 1.0  # Reset back to normal for other animations

func Update(delta: float) -> void:
	if !animation_player.is_playing():
		get_parent().on_child_transition(self, "Idle")
		return

func Physics_Update(delta: float) -> void:
	# Zero out velocity during punch
	player.velocity = Vector2.ZERO
	player.move_and_slide()

func enable_hitbox():
	print("Enabling hitbox")
	hitBox = player.get_node("Hitbox")
	hitBox.monitoring = true
	hitBox.monitorable = true
