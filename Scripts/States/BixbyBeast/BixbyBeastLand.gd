extends State

const BixbyBeastArtLayout := preload("res://Scripts/BixbyBeastArtLayout.gd")

@export var body : CharacterBody2D
@export var land_sfx_player : AudioStreamPlayer

@onready var state_machine = get_parent()

const TOUCHDOWN_SCREEN_SHAKE := 10.0
const TOUCHDOWN_SPRITE_SHAKE := 3.0
const TOUCHDOWN_SHAKE_STEPS := 6
const TOUCHDOWN_SHAKE_STEP_TIME := 0.03

var elapsed := 0.0
var start_height := 0.0
var landing_point := Vector2.ZERO


func Enter() -> void:
	body.play_anim(&"land")
	elapsed = 0.0
	start_height = body.height
	# Landed, his whole sprite has to fit on screen too, so off a breath at a rope he drifts back in as he comes down.
	var bounds: Rect2 = body.ground_bounds(0.0)
	landing_point = body.ground_position.clamp(bounds.position, bounds.end)


func Physics_Update(delta: float) -> void:
	elapsed += delta
	var weight := clampf(elapsed / state_machine.land_time, 0.0, 1.0)
	body.height = start_height * (1.0 - weight * weight)
	body.fly_toward(landing_point, state_machine.breath_approach_speed, delta)
	if weight < 1.0:
		return

	body.fly_velocity = Vector2.ZERO
	land_sfx_player.play()
	body.shake_screen(TOUCHDOWN_SCREEN_SHAKE, TOUCHDOWN_SHAKE_STEPS, TOUCHDOWN_SHAKE_STEP_TIME)
	if not BixbyBeastArtLayout.uses_final(&"land"):
		body.kick_up_dust()
		body.shake_sprite(TOUCHDOWN_SPRITE_SHAKE, TOUCHDOWN_SHAKE_STEPS, TOUCHDOWN_SHAKE_STEP_TIME)
	state_machine.on_child_transition(self, "Recover")
