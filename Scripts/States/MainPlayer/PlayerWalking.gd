extends State

@export var walking_animation : String = "walking"
@export var speed_threshold : float = 0.1
@export var animation_player : AnimationPlayer

var player : Node

func _ready() -> void:
	player = get_parent().get_parent()
	# print("Player node: ", player)
	animation_player = player.get_node("AnimationPlayer")

func Enter() -> void:
	# print("Entering Walking State")
	animation_player.play(walking_animation)

func Exit() -> void:
	pass
	# print("Exiting Walking State")

func Update(delta: float) -> void:
	var input_vector = InputSettings.move_vector()

	# A parry-only sequence roots the player, so a walk that was under way ends here.
	if input_vector.length() < speed_threshold or player.is_action_locked:
		# Transition to Run state
		get_parent().on_child_transition(self, "Idle")
		return

func Physics_Update(delta: float) -> void:
	# var directionHorz := Input.get_axis("ui_left", "ui_right")
	# var directionVert := Input.get_axis("ui_up", "ui_down")

	# if directionHorz:
	# 	player.velocity.x = directionHorz * 100.0
	# else:
	# 	player.velocity.x = move_toward(player.velocity.x, 0, 100.0)

	# if directionVert:
	# 	player.velocity.y = directionVert * 100.0
	# else:
	# 	player.velocity.y = move_toward(player.velocity.y, 0, 100.0)

	# player.move_and_slide()
	pass
