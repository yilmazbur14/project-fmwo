extends State

@export var body : CharacterBody2D

# Set by the state machine when a juggle killed him (land_juggled): he stays lying where he crashed, on the
# juggle sheet, rather than playing his own defeat.
var lying := false


# At once, cutting the killing blow's flinch: struck, reeling, down on his knees, and held there.
func Enter() -> void:
	body.velocity = Vector2.ZERO
	body.set_hurtbox_active(false)
	if lying:
		return
	body.show_body()
	body.play_anim(&"defeat")
