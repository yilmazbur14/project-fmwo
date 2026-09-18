extends State

# Both of them are down. The second one plays its defeat where it stands; the first one is already
# holding the last frame of its own from the swap, and nothing here may restart it.

@export var greyson : CharacterBody2D
@export var computah : CharacterBody2D

@onready var state_machine = get_parent()


func Enter() -> void:
	state_machine.fight.snap_music_level()
	for body in state_machine.fight.bodies():
		body.velocity = Vector2.ZERO
		body.show_aura(false)
		body.set_hurtbox_active(false)
		if body.current_anim != &"defeat":
			body.play_anim(&"defeat")
	computah.set_solid(false)
	computah.show_battery(false)
	computah.set_target_active(false)
