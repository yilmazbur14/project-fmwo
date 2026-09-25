extends State

# The breath before each attack, where he gets up after a Break or a finisher, and where he is left
# standing between the two. An attack that pays the Break waits here while the gauge is locked
# (BurakBossStateMachine.gauge_ready).

@export var body : CharacterBody2D
@export var beat_timer : Timer

@onready var state_machine = get_parent()


func Enter() -> void:
	body.velocity = Vector2.ZERO
	body.set_hurtbox_active(false)
	# A recoil the finisher started carries on; only the stagger's own anim queue ends it. Out of his intro
	# he is idling already, and restarting the loop would jump him a frame as the fight starts.
	if body.current_anim != &"hit" and body.current_anim != &"idle":
		body.play_state_anim(&"idle")
	beat_timer.start(state_machine.idle_beat)


func _on_beat_timer_timeout() -> void:
	if state_machine.gauge_ready():
		state_machine.start_cycle()
	else:
		beat_timer.start(state_machine.gauge_wait_step)
