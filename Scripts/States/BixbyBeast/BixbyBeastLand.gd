extends State

const BixbyBeastArtLayout := preload("res://Scripts/BixbyBeastArtLayout.gd")

@export var body : CharacterBody2D
@export var land_sfx_player : AudioStreamPlayer

@onready var state_machine = get_parent()

# Off a breath at a rope he first flies back to where his whole landed sprite fits on screen, until he's
# this close or for this long.
const LANDING_ALIGN_DISTANCE := 8.0
const LANDING_GLIDE_TIME := 0.6
# On the impact frame, which lasts IMPACT_SHAKE_STEPS * IMPACT_SHAKE_STEP_TIME.
const IMPACT_SHAKE_STRENGTH := 12.0
const IMPACT_SHAKE_STEPS := 5
const IMPACT_SHAKE_STEP_TIME := 0.028

enum Phase { GLIDE, DESCENT, TOUCHDOWN }

var phase := Phase.GLIDE
var elapsed := 0.0
var start_height := 0.0
var landing_point := Vector2.ZERO


func Enter() -> void:
	elapsed = 0.0
	var bounds: Rect2 = body.ground_bounds(0.0)
	landing_point = body.ground_position.clamp(bounds.position, bounds.end)
	state_machine.clear_fire_for_landing(landing_point)
	if body.ground_position.distance_to(landing_point) > LANDING_ALIGN_DISTANCE:
		phase = Phase.GLIDE
		body.play_anim(&"fly")
	else:
		_descend()


func Physics_Update(delta: float) -> void:
	elapsed += delta
	match phase:
		Phase.GLIDE:
			if body.fly_toward(landing_point, state_machine.breath_approach_speed, delta) <= LANDING_ALIGN_DISTANCE or elapsed >= LANDING_GLIDE_TIME:
				_descend()
		# Frame 0 lasts as long as the fall.
		Phase.DESCENT:
			var weight := clampf(elapsed / BixbyBeastArtLayout.time_to_step(&"land", 1), 0.0, 1.0)
			body.height = start_height * (1.0 - weight * weight)
			body.place()
			if weight >= 1.0:
				phase = Phase.TOUCHDOWN
				land_sfx_player.play()
				body.shake_screen(IMPACT_SHAKE_STRENGTH, IMPACT_SHAKE_STEPS, IMPACT_SHAKE_STEP_TIME)
		Phase.TOUCHDOWN:
			if body.anim_done:
				state_machine.on_child_transition(self, "Recover")


func _descend() -> void:
	phase = Phase.DESCENT
	elapsed = 0.0
	start_height = body.height
	body.fly_velocity = Vector2.ZERO
	body.play_anim(&"land")
