extends State

# He is down. His defeat plays where he stands, and nothing about him is live any more.

@export var body : CharacterBody2D

# Killed in the air by the tiered finisher's juggle (ComputahStateMachine.land_juggled): he is already
# lying on the juggle's own KO loop, which stays up, so his defeat isn't played over it.
var lying := false


func Enter() -> void:
	body.snap_music_level()
	body.velocity = Vector2.ZERO
	body.show_aura(false)
	body.set_hurtbox_active(false)
	body.set_grab_active(false)
	body.set_solid(false)
	body.set_target_active(false)
	body.show_battery(false)
	if not lying and body.current_anim != &"defeat":
		body.play_anim(&"defeat")
