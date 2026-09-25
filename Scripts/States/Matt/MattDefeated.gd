extends State

@export var body : CharacterBody2D

# Set by the state machine when a juggle killed him (MattStateMachine.land_juggled): he stays lying where
# he crashed, on the juggle's `down` loop (MattJuggled lingers on it), and never sits down.
var lying := false


# At once, cutting the killing blow's flinch, and whole: a teleport or a throw the fight ended in the
# middle of leaves nothing half-drawn.
func Enter() -> void:
	body.velocity = Vector2.ZERO
	body.show_body()
	body.set_hurtbox_active(false)
	if not lying:
		body.play_anim(&"defeat")
