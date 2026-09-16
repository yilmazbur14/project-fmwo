extends Node

@export var initial_state : State

@export var states : Dictionary = {}
@export var current_state : State


# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	for child in get_children():
		if child is State:
			states[child.name] = child

	print("State Machine initialized with states: ", states.keys())

	if initial_state:
		current_state = initial_state
		current_state.Enter()


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	if current_state:
		# print("State Machine update") working
		current_state.Update(delta)

func _physics_process(delta: float) -> void:
	if current_state:
		current_state.Physics_Update(delta)

func on_child_transition(state, new_state_name):
	# print("state: ", state, " new_state_name: ", new_state_name)working
	if state != current_state:
		return

	var new_state = states.get(new_state_name)
	print("new state: ", new_state)
	if !new_state:
		return

	if current_state:
		current_state.Exit()

	new_state.Enter()
	current_state = new_state
