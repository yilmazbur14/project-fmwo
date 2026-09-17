extends State

@export var body : CharacterBody2D
@export var wing_sfx_player : AudioStreamPlayer

@onready var state_machine = get_parent()

var elapsed := 0.0
var start_height := 0.0
var liftoff_point := Vector2.ZERO


func Enter() -> void:
	body.play_anim(&"takeoff")
	wing_sfx_player.play()
	elapsed = 0.0
	start_height = body.height
	# At hover height his whole sprite still has to fit on screen, so if he landed high up the arena he
	# drifts down it as he rises.
	var bounds: Rect2 = body.ground_bounds(body.HOVER_HEIGHT_PX)
	liftoff_point = body.ground_position.clamp(bounds.position, bounds.end)


func Physics_Update(delta: float) -> void:
	elapsed += delta
	var weight := clampf(elapsed / state_machine.takeoff_time, 0.0, 1.0)
	body.height = lerpf(start_height, body.HOVER_HEIGHT_PX, 1.0 - (1.0 - weight) * (1.0 - weight))
	body.fly_toward(liftoff_point, state_machine.breath_approach_speed, delta)
	if weight >= 1.0:
		state_machine.start_cycle()
