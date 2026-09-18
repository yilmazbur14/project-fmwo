extends State

# The breath between attacks, and where they are left standing when the player loses. The beat
# tightens with the surge and with `power`, which is the only thing about it that changes.

@export var greyson : CharacterBody2D
@export var computah : CharacterBody2D
@export var beat_timer : Timer

@onready var state_machine = get_parent()

# A recoil or a reboot already playing is left to finish; anything else goes back to resting.
const KEEP_PLAYING := [&"hit", &"reboot"]


func Enter() -> void:
	for body in state_machine.fight.bodies():
		if not state_machine.fight.is_alive(body):
			continue
		body.velocity = Vector2.ZERO
		if body == computah:
			computah.set_solid(true)
			computah.set_target_active(true)
			computah.set_down_box(false)
			computah.show_battery(false)
		if body.on_brink:
			body.play_anim(&"brink")
		elif not KEEP_PLAYING.has(body.current_anim):
			body.play_anim(state_machine.rest_anim(body))
	beat_timer.start(state_machine.beat_time * state_machine.fight.interval_scale(state_machine.next_attacker()))


func _on_beat_timer_timeout() -> void:
	state_machine.start_cycle()
