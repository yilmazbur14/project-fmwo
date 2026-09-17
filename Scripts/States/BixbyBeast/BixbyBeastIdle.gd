extends State

@export var body : CharacterBody2D


# Holding still: staggered on the ground after the finisher, or wherever he was when the player lost.
func Enter() -> void:
	body.fly_velocity = Vector2.ZERO
	if body.height > 0.0:
		body.play_anim(&"hover")
	# A flinch already under way carries on into the recover loop.
	elif body.current_anim != &"hit":
		body.play_anim(&"recover")
