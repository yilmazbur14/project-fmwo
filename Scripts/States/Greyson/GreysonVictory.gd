extends State

# The player lost, to his hearts or to the spirit bomb: a laughing double biceps where he stands while his outro
# plays.

@export var body : CharacterBody2D


func Enter() -> void:
	body.velocity = Vector2.ZERO
	body.set_hurtbox_active(false)
	body.set_talking(false)
	body.show_body()
	body.play_anim(&"victory")
