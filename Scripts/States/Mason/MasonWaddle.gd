extends State

@export var animation_player : AnimationPlayer
@export var body : CharacterBody2D

@onready var state_machine = get_parent()

var distance := 0.0


func Enter() -> void:
	animation_player.play("waddle")
	distance = 0.0


func Physics_Update(delta: float) -> void:
	var speed: float = state_machine.WADDLE_SPEED[state_machine.cycle_phase]
	distance = minf(distance + delta * speed, state_machine.line_length)
	body.global_position = state_machine.walk_position(distance)
	state_machine.drop_bombs_up_to(distance)

	if distance >= state_machine.line_length:
		state_machine.finish_line()
