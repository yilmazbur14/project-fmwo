extends State

# He is down. His defeat plays where he stands, and nothing about him is live any more.

@export var body : CharacterBody2D


func Enter() -> void:
	body.snap_music_level()
	body.velocity = Vector2.ZERO
	body.show_aura(false)
	body.set_hurtbox_active(false)
	body.set_grab_active(false)
	body.set_solid(false)
	body.set_target_active(false)
	body.show_battery(false)
	if body.current_anim != &"defeat":
		body.play_anim(&"defeat")
