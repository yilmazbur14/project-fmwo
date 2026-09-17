extends State

@export var animation_player : AnimationPlayer
@export var mech : Node2D
@export var rocket_sfx_player : AudioStreamPlayer

const ROCKET_SCENE := preload("res://Scenes/Bosses/ComputahRocketProjectilesScene.tscn")
const LAUNCH_SPEED := 800.0
# Rack muzzles on frame 10, the frame rocket_volley fires on, and the launch directions
# the racks point in on frames 9-10.
const RACK_MUZZLES := [Vector2(13, 12), Vector2(82, 12)]
const LAUNCH_DIRECTIONS := [Vector2(-0.41, -0.91), Vector2(0.41, -0.91)]

# Set by the state machine's rage scaling.
var volleys := 2
var volleys_left := 0
var rockets : Array = []

@onready var state_machine = get_parent()


func Enter() -> void:
	volleys_left = volleys
	rockets.clear()
	animation_player.play("rocket_volley")


# Called by the rocket_volley animation on frame 10.
func fire_volley() -> void:
	for i in RACK_MUZZLES.size():
		var rocket = ROCKET_SCENE.instantiate()
		# The rocket script climbs along velocityUp before it turns to home in on the player.
		rocket.velocityUp = LAUNCH_DIRECTIONS[i] * LAUNCH_SPEED
		mech.add_hazard(rocket, get_tree().current_scene, mech.frame_point(RACK_MUZZLES[i]))
		rockets.append(rocket)
	rocket_sfx_player.play()


func rockets_cleared() -> bool:
	rockets = rockets.filter(func(rocket): return is_instance_valid(rocket))
	return rockets.is_empty()


func clear_rockets() -> void:
	for rocket in rockets:
		if is_instance_valid(rocket):
			rocket.queue_free()


func _on_animation_player_animation_finished(anim_name: StringName) -> void:
	if anim_name != "rocket_volley" or state_machine.current_state != self:
		return
	volleys_left -= 1
	if volleys_left > 0:
		animation_player.play("rocket_volley")
	else:
		state_machine.on_child_transition(self, "AwaitRockets")
