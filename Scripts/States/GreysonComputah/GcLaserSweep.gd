extends State

# ATTACK A: the twin laser sweep, and the fight's identity move. One state for both owners -
# Computah fires it while he lives, and Greyson hauls the ruined rig up in phase two - so the beams,
# their sweep and their dash-through rule are never absent and never duplicated.
#
# The beam itself is ComputahLaserBeam, kept as the single source and driven from here as a child
# rather than as a sibling state: this state owns who is holding the rig, where it sits and what
# window follows, and the beam owns the sweep. Its beams stay OUT of the "enemy projectile" group
# and report their own hits, which is what makes dashing through them work.
#
# The telegraph never scales. Only the sweep does.

const ParryTell := preload("res://Scripts/ParryTell.gd")

@export var greyson : CharacterBody2D
@export var computah : CharacterBody2D
@export var rig : Node2D
# The ComputahLaserBeam state, a child of this node so the fight's machine never registers it.
@export var beam : State

@onready var state_machine = get_parent()

var owner_body: Node = null
var clock := 0.0
var total := 0.0


func Enter() -> void:
	clock = 0.0
	owner_body = state_machine.laser_owner()
	var player: Node2D = state_machine.get_player()
	if player:
		owner_body.face_toward(player.global_position)

	beam.telegraph_duration = maxf(state_machine.laser_telegraph, state_machine.LASER_TELL_FLOOR)
	beam.sweep_duration = lerpf(state_machine.laser_sweep, state_machine.laser_sweep_fast,
		state_machine.pace(owner_body))
	beam.fade_duration = state_machine.laser_fade
	beam.body = owner_body
	if owner_body == computah:
		beam.charge_anim = &"laser_charge"
		beam.fire_anim = &"laser_fire"
	else:
		beam.charge_anim = &"beam_hold"
		beam.fire_anim = &"beam_hold"
	total = beam.get_total_duration()

	_place_rig()
	rig.show()
	beam.Enter()

	# The other one works the crowd while the rig does the job.
	var idle_body: Node = state_machine.fight.other_body(owner_body)
	if state_machine.fight.is_alive(idle_body) and not idle_body.on_brink:
		idle_body.play_anim(&"taunt")


func Exit() -> void:
	beam.Exit()
	rig.hide()


func Physics_Update(delta: float) -> void:
	_place_rig()
	beam.Physics_Update(delta)
	clock += delta
	if clock >= total:
		_hand_over()


# The rig is drawn where its owner holds it, and follows them for the whole sweep.
func _place_rig() -> void:
	if is_instance_valid(owner_body):
		rig.global_position = owner_body.beam_origin().round()


# Phase one: the sweep ends in GREYSON's window, which is the half of the A-B alternation that
# teaches the player to spread their damage. Alone, each of them vents into their own.
func _hand_over() -> void:
	if not state_machine.fight.swapped:
		state_machine.open_window(greyson, state_machine.laser_window, greyson.MAX_HITS_PER_WINDOW,
			&"crank", &"crank", &"")
	elif owner_body == computah:
		state_machine.open_window(computah, state_machine.laser_vent_window, computah.MAX_HITS_PER_WINDOW,
			&"collapse", &"down", &"reboot")
	else:
		state_machine.open_window(greyson, state_machine.beam_window, greyson.MAX_HITS_PER_WINDOW,
			&"throw_recover", &"throw_recover", &"")
