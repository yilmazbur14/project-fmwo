extends State

# ONE PARAMETERISED PUNISH WINDOW. The beam's vent and the chase's flat battery both go through
# here, so the rules of a window - the hit cap, the daze, the finisher's early end, what he is drawn
# as - cannot drift apart between them.
# ComputahStateMachine.open_window() fills the fields in before the transition; the defaults below
# are the vent, so a bare transition into this state (the defence suite drives one) still opens a
# working window.

@export var body : CharacterBody2D
@export var window_timer : Timer
@export var window_sfx_player : AudioStreamPlayer

@onready var state_machine = get_parent()

# Set by ComputahStateMachine.open_window() before the transition. The defaults are the beam's
# vent, which is the window the fight actually runs.
var window_time := 2.4
var window_cap := 3
var enter_anim := &"vent"
var hold_anim := &"vent_hold"
var exit_anim := &"vent_up"


func Enter() -> void:
	body.velocity = Vector2.ZERO
	body.set_solid(true)
	body.set_target_active(true)
	body.show_battery(false)
	# The pose the window is spent in, not the one it starts on: the kneeling vent and the floor
	# loop are different bands, and the punches land on the hold.
	body.set_body_box(hold_anim)

	body.begin_window(window_cap)
	body.play_anim(enter_anim, hold_anim)
	body.set_hurtbox_active(true)
	state_machine.set_open(true)
	window_sfx_player.play()
	window_timer.start(window_time)


func Exit() -> void:
	window_timer.stop()
	body.set_hurtbox_active(false)
	body.set_body_box(&"idle")
	state_machine.set_open(false)


# No pose change: every window's hold is on the mat (his knee in the vent, flat out after a collapse or a fall), and
# his only hit sheet stands him up, so playing it popped him up off the mat and back on every punch. His damage's
# white flash and shake are the flinch.
func flinch() -> void:
	pass


func _on_window_timer_timeout() -> void:
	if exit_anim != &"":
		body.play_anim(exit_anim, &"idle")
	state_machine.on_child_transition(self, "Idle")
