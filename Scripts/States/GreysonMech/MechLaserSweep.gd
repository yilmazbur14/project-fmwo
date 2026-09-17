extends "res://Scripts/States/Computah/ComputahLaserBeam.gd"

# Computah's laser, fired from the mech's elbow barrels: the beam origins follow the barrel
# muzzles as the sheet frames change.
@export var mech : Node2D
@export var sprite : Sprite2D

const CHARGE_FRAME := 4
# Sheet pixel of the left and right muzzle on each laser frame.
const MUZZLES := {
	4: [Vector2(1, 48), Vector2(94, 48)],
	5: [Vector2(1, 40), Vector2(94, 40)],
	6: [Vector2(1, 40), Vector2(94, 40)],
	7: [Vector2(4, 53), Vector2(91, 53)],
	8: [Vector2(14, 58), Vector2(81, 58)],
}
# laser_fire frames 6, 7 and 8 aim the barrels 0, 45 and 90 degrees below horizontal.
# Each is shown while it's the closest to the beams' angle.
const FIRE_FRAMES := [6, 7, 8]
const FIRE_FRAME_ANGLE_STEP := 45.0

@onready var state_machine = get_parent()


func Enter():
	# The charge animation's first frame only lands on the next process step, and the
	# beams are placed from the current frame straight away.
	sprite.frame = CHARGE_FRAME
	super()


func Physics_Update(_delta: float):
	super(_delta)
	_place_beams()
	if elapsed >= get_total_duration():
		state_machine.rest_then("RocketVolley", state_machine.attack_gap)


func _set_sweep(amount: float) -> void:
	super(amount)
	if phase != Phase.TELEGRAPH:
		var angle := rad_to_deg(laser_beam_right.rotation)
		var index := clampi(roundi(angle / FIRE_FRAME_ANGLE_STEP), 0, FIRE_FRAMES.size() - 1)
		sprite.frame = FIRE_FRAMES[index]
	_place_beams()


func _place_beams() -> void:
	var muzzles: Array = MUZZLES[sprite.frame]
	laser_beam_left.global_position = mech.frame_point(muzzles[0])
	laser_beam_right.global_position = mech.frame_point(muzzles[1])
