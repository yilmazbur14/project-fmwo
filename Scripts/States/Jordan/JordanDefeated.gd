extends State

@export var body : CharacterBody2D

# Set by the state machine when a juggle killed him (JordanStateMachine.land_juggled): he stays lying
# where he crashed, on the juggle's `down` loop (JordanJuggled lingers on it), and never kneels.
var lying := false


# At once, cutting the killing blow's flinch: the defeat opens on the same reel, and letting the flinch
# finish would flash the idle stance between the two.
func Enter() -> void:
	if lying:
		return
	body.play_anim(&"defeat")
