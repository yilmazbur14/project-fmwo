extends State

@export var body : CharacterBody2D


# Holding still on the floor: staggered after a finisher, or wherever he was when the player lost.
func Enter() -> void:
	body.fly_velocity = Vector2.ZERO
	body.height = 0.0
	body.place()
	body.hide_glider()
	body.set_air_draw(false)
	# A recoil the finisher started carries on; only the stagger's own anim queue ends it.
	if body.current_anim != &"hit":
		body.play_anim(&"idle")
