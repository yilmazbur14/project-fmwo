extends State

# He drops out of the sky in front of the player, on the side he is already on, and steps off the card.

@export var body : CharacterBody2D
@export var land_sfx_player : AudioStreamPlayer

@onready var state_machine = get_parent()

const ARRIVE_DISTANCE := 24.0
# A dive that somehow can't reach its landing point still has to end.
const DIVE_CAP := 2.5
const GLIDER_SHRINK := 0.15
const LAND_SHAKE := 6.0
const LAND_SHAKE_STEPS := 3
const LAND_SHAKE_STEP_TIME := 0.03

var landing := Vector2.ZERO
var start_distance := 1.0
var diving := true
var clock := 0.0


func Enter() -> void:
	body.play_anim(&"glide")
	diving = true
	clock = 0.0
	landing = _landing_point()
	start_distance = maxf(body.ground_position.distance_to(landing), 1.0)


func Physics_Update(delta: float) -> void:
	clock += delta
	if not diving:
		if clock >= state_machine.dismount_land_time:
			state_machine.on_child_transition(self, "Throw")
		return

	var left: float = body.fly_toward(landing, state_machine.dive_speed, delta)
	body.height = state_machine.glider_height * clampf(left / start_distance, 0.0, 1.0)
	body.place()
	if left < ARRIVE_DISTANCE or clock >= DIVE_CAP:
		_land()


func _land() -> void:
	diving = false
	clock = 0.0
	body.fly_velocity = Vector2.ZERO
	body.height = 0.0
	body.place()
	body.shrink_glider(GLIDER_SHRINK)
	body.set_air_draw(false)
	body.play_anim(&"dismount")
	land_sfx_player.play()
	body.shake_screen(LAND_SHAKE, LAND_SHAKE_STEPS, LAND_SHAKE_STEP_TIME)


# Throwing distance from the player, on the side he is already on, and never outside his own ground.
func _landing_point() -> Vector2:
	var player: Node2D = state_machine.get_player()
	var anchor: Vector2 = player.global_position if player else state_machine.ROPES.get_center()
	var bounds: Rect2 = body.ground_bounds(0.0)
	var side := 1.0 if body.ground_position.x >= anchor.x else -1.0
	var point := Vector2(anchor.x + side * state_machine.throw_distance, anchor.y).clamp(bounds.position, bounds.end)
	# Pinned against a rope on that side: the other one is the only side with room to throw from.
	if absf(point.x - anchor.x) < state_machine.throw_distance * 0.6:
		point = Vector2(anchor.x - side * state_machine.throw_distance, anchor.y).clamp(bounds.position, bounds.end)
	return point
