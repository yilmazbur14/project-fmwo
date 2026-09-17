extends State

@export var body : CharacterBody2D

@onready var state_machine = get_parent()

# He turns for the other side once he's this close to a strafe point.
const STRAFE_TURN_DISTANCE := 40.0

var elapsed := 0.0
var duration := 0.0
var strafe_side := 1.0


func Enter() -> void:
	body.play_anim(&"hover")
	elapsed = 0.0
	duration = state_machine.hover_duration()


func Physics_Update(delta: float) -> void:
	elapsed += delta
	var player = state_machine.get_player()
	if player:
		var bounds: Rect2 = body.ground_bounds(body.height)
		var strafe_point: Vector2 = player.global_position + Vector2(strafe_side * state_machine.strafe_distance, -state_machine.hover_lead)
		strafe_point = strafe_point.clamp(bounds.position, bounds.end)
		if body.fly_toward(strafe_point, state_machine.hover_speed, delta) < STRAFE_TURN_DISTANCE:
			strafe_side = -strafe_side
	if elapsed >= duration:
		state_machine.hover_finished(self)
