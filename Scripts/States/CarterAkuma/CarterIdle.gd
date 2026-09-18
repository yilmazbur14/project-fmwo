extends State

@export var body : CharacterBody2D
@export var beat_timer : Timer

@onready var state_machine = get_parent()


# The breath between the lights coming up and the eyes going again, and where he is left standing
# when the player loses.
func Enter() -> void:
	body.velocity = Vector2.ZERO
	body.show_body(true)
	body.show_mark_glow(false)
	# A recoil the finisher started carries on; only the stagger's own anim queue ends it.
	if body.current_anim != &"hit":
		body.play_anim(&"idle")
	beat_timer.start(state_machine.beat_time)


func _on_beat_timer_timeout() -> void:
	state_machine.start_cycle()
