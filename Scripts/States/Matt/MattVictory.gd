extends State

@export var body : CharacterBody2D


# The player lost: he stands where the fight left him, thumb to his chest in his proud pose, while his
# outro plays.
func Enter() -> void:
	body.velocity = Vector2.ZERO
	body.show_body()
	body.set_hurtbox_active(false)
	body.show_talk(&"proud", false)
