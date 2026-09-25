extends RefCounted

# Which of the four directions the player pressed, for Matt's Glass Row arrows: keys and the D-pad through
# the move actions (so rebinds carry over) and the left stick flicked past a threshold. Four cardinal
# directions, never a diagonal. One instance per state that reads it, since the stick's arming is state.
#
# KEYS AND THE D-PAD are read off the event itself (read), so a press and release inside one frame still
# counts.
#
# THE STICK never goes through is_action_pressed(), which is true for every motion event past the dead
# zone - a stick held over would answer every boom. Its axes arrive as separate events, so an x event
# still sees the y of before it: read() only records them, and poll(), once a physics step, decides with
# both. It fires once when the leading axis reaches STICK_PRESS with the other under STICK_DOMINANCE of
# it, and re-arms once both are back under STICK_RELEASE. A diagonal it can't call waits for the stick
# to move on.

const STICK_PRESS := 0.5
const STICK_RELEASE := 0.3
const STICK_DOMINANCE := 0.8
const ACTIONS := {&"move_up": &"up", &"move_down": &"down", &"move_left": &"left", &"move_right": &"right"}

var stick := Vector2.ZERO
var armed := true


func read(event: InputEvent) -> StringName:
	if event is InputEventJoypadMotion:
		var motion := event as InputEventJoypadMotion
		if motion.axis == JOY_AXIS_LEFT_X:
			stick.x = motion.axis_value
		elif motion.axis == JOY_AXIS_LEFT_Y:
			stick.y = motion.axis_value
		return &""
	for action: StringName in ACTIONS:
		if event.is_action_pressed(action):
			return ACTIONS[action]
	return &""


func poll() -> StringName:
	var x := absf(stick.x)
	var y := absf(stick.y)
	if maxf(x, y) < STICK_RELEASE:
		armed = true
		return &""
	if not armed or maxf(x, y) < STICK_PRESS:
		return &""
	if x >= y and y < x * STICK_DOMINANCE:
		armed = false
		return &"right" if stick.x > 0.0 else &"left"
	if y > x and x < y * STICK_DOMINANCE:
		armed = false
		return &"down" if stick.y > 0.0 else &"up"
	return &""
