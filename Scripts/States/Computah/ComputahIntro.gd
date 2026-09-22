extends State

# Computah's entrance, and the joke in it is Greyson's rather than his: he is parked in the middle of
# the ring with a flat battery, doing nothing at all, until somebody says the words he takes.
# ComputahPreFight.dialogue plays these beats between its lines and waits for each one.
#
# HE IS HELD ON ONE FRAME (the `dormant` pose) because there is no powered-down drawing of him: a
# still chassis on the LOW charge row is what "off" is made of, and his idle loop is what "on" is.
#
# THE DEAD AIR IS THE PUNCHLINE. "go get him buddy" is not the robot's command syntax, so
# nothing_happens() holds an empty ring for DEAD_AIR seconds. Under about two seconds that reads as a
# loading hitch instead of a gag, which is the only way this beat can fail.
#
# HIS CHEST IS THE READ, and the charge state is a frame offset on his own sheets rather than a tint
# (0 full, 1 half, 2 low), so charging him steps 2 -> 1 -> 0 and the cell count, the cell colour and
# the antenna ball all change together. CELL_TIME is how long each of those three reads is up for.
#
# Nobody else stands in the arena: Greyson speaks from the stands, through the balloon and his own
# voice, and has no node here at all. Every wait is a node-bound tween, so a freeze holds it.

const Layout := preload("res://Scripts/ComputahArtLayout.gd")

@export var body : CharacterBody2D

@onready var state_machine = get_parent()

# BEAT 4, AND THE WHOLE JOKE: the failed command lands, the balloon goes away and this is how long
# nothing happens for.
const DEAD_AIR := 3.0
# The charge-up. A third of it per charge state, so low, half and full are each on screen long enough
# to be counted, and the gauge over his head fills across all three.
const CELL_TIME := 0.6
# The moment he is live: a shudder as the chassis takes the power, then the taunt held before he
# settles into his fighting idle.
const WAKE_SHAKE := 6.0
const WAKE_SHAKE_STEPS := 6
const WAKE_SHAKE_STEP_TIME := 0.04
const WAKE_CHEER := 1.6
const FULL_HOLD := 0.9


func Enter() -> void:
	body.global_position = state_machine.COMPUTAH_HOME
	body.set_facing(false)
	# Flat, and held on one frame: a robot with nothing in the battery does not breathe either.
	body.set_charge_state(Layout.Charge.LOW)
	body.play_anim(&"dormant")
	get_tree().call_group("arena_crowd", "hush")


# Whatever the lines did or did not get to, he starts the fight charged and on his feet: the defence
# suite and a playtest jump into a fight both throw the dialogue away unread, and neither of them
# should leave him fighting on a red battery.
func Exit() -> void:
	body.show_battery(false)
	body.set_charge_state(Layout.Charge.FULL)
	if body.current_anim == &"dormant":
		body.play_anim(&"idle")


#THE BEATS, played by the dialogue between its lines.

# BEAT 4. "go get him buddy" is not a command he takes, so nothing happens - for long enough that the
# player stops waiting for it to.
func nothing_happens() -> void:
	await _pause(DEAD_AIR)


# BEAT 7. This one is in his own words. His chest fills a cell at a time, he starts moving on the
# frame it goes green, and the fight is on the other side of it.
func battery_charges_up() -> void:
	if not _intro_is_live():
		return
	body.show_battery(true)
	body.set_battery(0.0, false)
	var fill := create_tween()
	fill.tween_method(_charge_to, 0.0, 1.0, CELL_TIME * 3.0)
	await fill.finished
	if not _intro_is_live():
		return
	body.shake_sprite(WAKE_SHAKE, WAKE_SHAKE_STEPS, WAKE_SHAKE_STEP_TIME)
	body.play_anim(&"taunt")
	get_tree().call_group("arena_crowd", "cheer", WAKE_CHEER)
	await _pause(FULL_HOLD)
	if not _intro_is_live():
		return
	body.show_battery(false)
	body.play_anim(&"idle")


# The gauge and his chest off one clock, a third of the fill each.
func _charge_to(filled: float) -> void:
	if not _intro_is_live():
		return
	var state := Layout.Charge.LOW
	if filled >= 2.0 / 3.0:
		state = Layout.Charge.FULL
	elif filled >= 1.0 / 3.0:
		state = Layout.Charge.HALF
	var was: int = body.charge_state
	body.set_charge_state(state)
	body.set_battery(filled, false)
	# He comes alive on the frame his chest goes green: the dormant pose is one held frame, so nothing
	# on him moves until this. `boot` is the hand-over the dormant sheet was drawn with - eye bars snap
	# white, the antenna whips upright, then he takes his own weight - and its last frame is the idle's
	# first, so it settles into the loop rather than cutting to it.
	if state == Layout.Charge.FULL and was != state:
		body.play_anim(&"boot", &"idle")


# The lines can be ended from outside - the defence suite frees the balloon and ends the dialogue by
# hand on the first frames of the fight - which starts the fight under whichever beat is in flight.
# Everything above asks this before it touches him, so a beat that outlived the intro leaves the
# fight alone.
func _intro_is_live() -> bool:
	return is_instance_valid(body) and state_machine.current_state == self


func _pause(seconds: float) -> void:
	var tween := create_tween()
	tween.tween_interval(seconds)
	await tween.finished
