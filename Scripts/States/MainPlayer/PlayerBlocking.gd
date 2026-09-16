extends State

@export var blocking_animation : String = "blocking"
@export var animation_player : AnimationPlayer

var player : Node

func _ready() -> void:
	player = get_parent().get_parent()
	animation_player = player.get_node("AnimationPlayer")

func Enter() -> void:
	animation_player.play(blocking_animation)

func Exit() -> void:
	pass

func Update(delta: float) -> void:
	# Exit block when button is released
	if !Input.is_action_pressed("block"):
		get_parent().on_child_transition(self, "Idle")
		return

func Physics_Update(delta: float) -> void:
	# Zero out velocity while blocking
	player.velocity = Vector2.ZERO
	player.move_and_slide() 