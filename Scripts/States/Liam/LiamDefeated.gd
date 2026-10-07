extends State

# Beaten: his defeat on the mat, or - killed in the air - lying on the juggle's down loop where he crashed (lying,
# set by LiamStateMachine.land_juggled).

var body: CharacterBody2D
var state_machine: Node
var lying := false


func Enter() -> void:
	body.set_hurtbox_active(false)
	body.leave_perch()
	if lying:
		return
	body.play_anim(&"defeat")
