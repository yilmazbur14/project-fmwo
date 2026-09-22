extends State

# The breath between attacks, and where he is left standing when the player loses.

@export var body : CharacterBody2D
@export var beat_timer : Timer

@onready var state_machine = get_parent()

# A recoil, or a window's way back up, is left to finish; anything else goes back to resting.
const KEEP_PLAYING := [&"hit", &"reboot", &"vent_up"]


func Enter() -> void:
	body.velocity = Vector2.ZERO
	body.set_solid(true)
	body.set_target_active(true)
	body.set_body_box(&"idle")
	body.show_battery(false)
	if not KEEP_PLAYING.has(body.current_anim):
		body.play_anim(&"idle")
	beat_timer.start(state_machine.beat_time)


func _on_beat_timer_timeout() -> void:
	state_machine.start_cycle()
