extends State

@export var animation_player : AnimationPlayer
@export var mech : Node2D
@export var slam_sfx_player : AudioStreamPlayer

const SHOCKWAVE_SCENE := preload("res://Scenes/Bosses/MechShockwaveScene.tscn")
const IMPACT_SCENE := preload("res://Scenes/Bosses/MechPoundImpactScene.tscn")
# Midpoint of the two fists on frame 14, on the feet row.
const SLAM_PIXEL := Vector2(47.5, 95)

const SHAKE_STEPS := 6
const SHAKE_STEP_TIME := 0.035
const SHAKE_STRENGTH := 9.0

# Set by the state machine's rage scaling.
var ring_speed := 900.0

@onready var state_machine = get_parent()


func Enter() -> void:
	animation_player.play("ground_pound")


# Called by the ground_pound animation on frame 14.
func slam() -> void:
	var slam_point: Vector2 = mech.frame_point(SLAM_PIXEL).round()
	mech.add_hazard(IMPACT_SCENE.instantiate(), mech, slam_point)
	var shockwave = SHOCKWAVE_SCENE.instantiate()
	shockwave.speed = ring_speed
	# Parented to the y-sorted mech root, so the ring's back half passes behind the mech.
	mech.add_hazard(shockwave, mech, slam_point)
	slam_sfx_player.play()
	_shake_screen()


# Offsets the canvas instead of moving nodes, so physics bodies and the UI layers stay put.
func _shake_screen() -> void:
	var viewport := get_viewport()
	var base := viewport.canvas_transform
	# A SceneTree tween, so a scene change mid-shake can't leave the canvas offset.
	var tween := get_tree().create_tween()
	for i in SHAKE_STEPS:
		var strength := SHAKE_STRENGTH * (1.0 - float(i) / SHAKE_STEPS)
		var offset := Vector2(randf_range(-strength, strength), randf_range(-strength, strength)).round()
		tween.tween_callback(func(): viewport.canvas_transform = base.translated(offset))
		tween.tween_interval(SHAKE_STEP_TIME)
	tween.tween_callback(func(): viewport.canvas_transform = base)


func _on_animation_player_animation_finished(anim_name: StringName) -> void:
	if anim_name != "ground_pound" or state_machine.current_state != self:
		return
	state_machine.on_child_transition(self, "Vulnerable")
