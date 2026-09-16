extends State

@export var animation_player : AnimationPlayer
@export var body : CharacterBody2D

@onready var state_machine = get_parent()

var elapsed := 0.0
var next_bomb := 1


func Enter() -> void:
	animation_player.play("waddle")
	elapsed = 0.0
	next_bomb = 1


func Physics_Update(delta: float) -> void:
	var phase: int = state_machine.cycle_phase
	var bomb_count: int = state_machine.BOMBS_PER_LINE[phase]

	elapsed += delta
	var t := clampf(elapsed / state_machine.LINE_DURATION[phase], 0.0, 1.0)
	body.global_position = state_machine.line_point(t)

	while next_bomb < bomb_count and t >= float(next_bomb) / (bomb_count - 1):
		state_machine.drop_bomb()
		next_bomb += 1

	if t >= 1.0:
		state_machine.finish_line()
