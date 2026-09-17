extends State

@export var body : CharacterBody2D


# Holding still: staggered on the ground after the finisher, or wherever he was when the player lost.
func Enter() -> void:
	body.fly_velocity = Vector2.ZERO
	body.play_anim(&"hover" if body.height > 0.0 else &"recover")
