extends State

@export var body : CharacterBody2D


# The player lost: he laughs at them where the fight left him while his outro plays.
func Enter() -> void:
	body.velocity = Vector2.ZERO
	body.show_body()
	body.set_hurtbox_active(false)
	body.play_anim(&"laugh")
