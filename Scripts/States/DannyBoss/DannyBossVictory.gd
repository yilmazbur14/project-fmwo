extends State

# The player lost, in the fight or in the sumo: he sits down where he is and naps while his outro plays.

@export var body : CharacterBody2D


func Enter() -> void:
	body.velocity = Vector2.ZERO
	body.set_hurtbox_active(false)
	body.show_body()
	body.play_anim(&"defeat", &"sleep")
