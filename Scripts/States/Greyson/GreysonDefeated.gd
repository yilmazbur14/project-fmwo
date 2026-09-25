extends State

# Beaten for good, at the end of the final brawl (GreysonStateMachine.greyson_beaten): his defeat plays where he
# stands, or he stays down on the juggle's KO loop if the brawl left him lying there. Nothing about him is live.

@export var body : CharacterBody2D

# Set before Enter() by greyson_beaten().
var lying := false


func Enter() -> void:
	body.velocity = Vector2.ZERO
	body.set_hurtbox_active(false)
	body.set_target_active(false)
	body.set_talking(false)
	if not lying:
		body.show_body()
		body.play_anim(&"defeat")
