extends State

# The breath before each attack, where he gets up after a Break or a finisher, and where he is left standing
# between the two. Slams waits here while the gauge is locked (DannyBossStateMachine.gauge_ready), and
# start_cycle() is only ever reached from here.

@export var body : CharacterBody2D
@export var beat_timer : Timer

@onready var state_machine = get_parent()


func Enter() -> void:
	body.velocity = Vector2.ZERO
	body.set_hurtbox_active(false)
	body.set_body_box(&"idle")
	# A recoil, a wake or a roll up off his back that the finisher, the nap or his time on his back started carries
	# on; only its own queue ends it. Out of his intro he is idling already, and restarting the loop would jump him a
	# frame as the fight starts.
	if not (body.current_anim in [&"hit", &"wake", &"idle", &"back_roll"]):
		body.play_state_anim(&"idle")
	else:
		body.state_anim = &"idle"
	beat_timer.start(state_machine.idle_beat)


func Exit() -> void:
	beat_timer.stop()


func _on_beat_timer_timeout() -> void:
	if state_machine.current_state != self:
		return
	if state_machine.gauge_ready():
		state_machine.start_cycle()
	else:
		beat_timer.start(state_machine.gauge_wait_step)
