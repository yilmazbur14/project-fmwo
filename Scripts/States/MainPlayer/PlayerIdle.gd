extends State

@export var idle_animation : String = "idle_down"
@export var speed_threshold : float = 0.1
@export var animation_player : AnimationPlayer

var player : Node

func _ready() -> void:
	player = get_parent().get_parent()
	animation_player = player.get_node("AnimationPlayer")

func Enter() -> void:
	# print("Entering Idle State")
	animation_player.play(idle_animation)

func Exit() -> void:
	pass
	# print("Exiting Idle State")

func Update(delta: float) -> void:
	var input_vector = InputSettings.move_vector()
	# print("input vector length: ", input_vector.length())
    
	# A parry-only sequence roots the player: holding a direction mustn't even start the walk.
	if input_vector.length() > speed_threshold and not player.is_action_locked:
		print("check passed")
		# Transition to Run state
		# print("Transitioning to Walking State")working
		# print("parent", get_parent())working
		get_parent().on_child_transition(self, "Walking")
		return

func Physics_Update(delta: float) -> void:
	pass
