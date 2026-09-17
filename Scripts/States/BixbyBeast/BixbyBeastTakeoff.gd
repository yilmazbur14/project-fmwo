extends State

const BixbyBeastArtLayout := preload("res://Scripts/BixbyBeastArtLayout.gd")

@export var body : CharacterBody2D
@export var wing_sfx_player : AudioStreamPlayer

@onready var state_machine = get_parent()

# Frames 0 and 1 are still on the ground; he rises from frame 2.
const RISING_FRAME := 2

var elapsed := 0.0
var start_height := 0.0
var liftoff_point := Vector2.ZERO


func Enter() -> void:
	body.play_anim(&"takeoff", &"hover")
	wing_sfx_player.play()
	elapsed = 0.0
	start_height = body.height
	# At hover height his whole sprite still has to fit on screen, so if he landed high up the arena he
	# drifts down it as he rises.
	var bounds: Rect2 = body.ground_bounds(body.HOVER_HEIGHT_PX)
	liftoff_point = body.ground_position.clamp(bounds.position, bounds.end)


func Physics_Update(delta: float) -> void:
	elapsed += delta
	var rising := elapsed - BixbyBeastArtLayout.time_to_step(&"takeoff", RISING_FRAME)
	if rising < 0.0:
		return
	var weight := clampf(rising / state_machine.takeoff_rise_time, 0.0, 1.0)
	body.height = lerpf(start_height, body.HOVER_HEIGHT_PX, 1.0 - (1.0 - weight) * (1.0 - weight))
	body.fly_toward(liftoff_point, state_machine.breath_approach_speed, delta)
	if weight >= 1.0:
		state_machine.start_cycle()
