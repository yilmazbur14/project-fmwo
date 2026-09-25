extends State

@export var body : CharacterBody2D
@export var beat_timer : Timer

@onready var state_machine = get_parent()

# Seconds the pose he came in with is held before the idle: a landed yell's roar, through its
# after-pose. Set by the state machine before the transition, and spent here.
var hold_left := 0.0


# The breath before each cycle, the stagger after a finisher, the second after a landed yell, and where
# he is left standing when the player loses.
func Enter() -> void:
	body.velocity = Vector2.ZERO
	body.set_hurtbox_active(false)
	# A recoil the finisher started carries on; only the stagger's own anim queue ends it. Out of his
	# intro he is idling already, and restarting the loop would jump him a frame as the fight starts.
	if hold_left <= 0.0 and body.current_anim != &"hit" and body.current_anim != &"idle":
		body.play_state_anim(&"idle")
	beat_timer.start(state_machine.idle_beat)


func Exit() -> void:
	hold_left = 0.0


func Physics_Update(delta: float) -> void:
	if hold_left <= 0.0:
		return
	hold_left -= delta
	if hold_left <= 0.0:
		body.play_state_anim(&"idle")


func _on_beat_timer_timeout() -> void:
	state_machine.start_cycle()
