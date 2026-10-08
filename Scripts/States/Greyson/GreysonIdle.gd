extends State

# The breath before each cycle, where he gets up after a Break or a finisher, and where he is left standing
# between the two. A chain that pays the Break waits here while the gauge is locked
# (GreysonStateMachine.gauge_ready), one that throws while his last throw's plates are still flying for up to
# plate_wait_cap (throw_ready), and start_cycle() is only ever reached from here.

@export var body : CharacterBody2D
@export var beat_timer : Timer

@onready var state_machine = get_parent()


func Enter() -> void:
	body.velocity = Vector2.ZERO
	body.set_hurtbox_active(false)
	body.set_body_box(&"idle")
	# A recoil the finisher or a Break started carries on; only its own queue ends it.
	if not (body.current_anim in [&"hit", &"idle"]):
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
