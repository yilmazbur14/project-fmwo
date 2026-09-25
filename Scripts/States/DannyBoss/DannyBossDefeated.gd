extends State

# He is out of the ring: the sumo's win pushed him through the top gate and hid him (DannyBossSumo), and all
# that is left is keeping his hurtbox off while the outro plays.

@export var body : CharacterBody2D


func Enter() -> void:
	body.velocity = Vector2.ZERO
	body.set_hurtbox_active(false)
