extends State

const BixbyBeastArtLayout := preload("res://Scripts/BixbyBeastArtLayout.gd")

# Killed by a juggle, he lies belly-up on its `down` loop this long before his defeat takes over.
const JUGGLE_DEFEAT_HOLD := 0.6

@export var body : CharacterBody2D

@onready var state_machine = get_parent()

var outro_started := false
# Set by the state machine when a juggle killed him (BixbyBeastStateMachine.land_juggled): he is already
# down on the juggle sheet, which is still his sprite's.
var lying := false
var hold_left := 0.0


# He collapses, turns back into normal Bixby and coughs Liam up, all drawn on the defeat sheet. Killed by a
# juggle he is down already, so after the beat he lies there his defeat starts on its smoke cloud, which
# hides the cut from belly-up on the juggle sheet to his own.
func Enter() -> void:
	body.fly_velocity = Vector2.ZERO
	outro_started = false
	if lying:
		hold_left = JUGGLE_DEFEAT_HOLD
		return
	body.play_anim(&"defeat")


func Physics_Update(delta: float) -> void:
	if hold_left <= 0.0:
		return
	hold_left -= delta
	if hold_left <= 0.0:
		state_machine.states["Juggled"].stop_lingering()
		body.play_anim(&"defeat", &"", BixbyBeastArtLayout.DEFEAT_SMOKE_FRAME)


# The fight is only called once Liam has landed, so his win lines follow the cough-up.
func Update(_delta: float) -> void:
	if not outro_started and body.current_anim == &"defeat" and body.anim_step >= BixbyBeastArtLayout.DEFEAT_LIAM_LANDS_FRAME:
		outro_started = true
		body.finish_victory()
