extends State

const BixbyBeastArtLayout := preload("res://Scripts/BixbyBeastArtLayout.gd")

@export var body : CharacterBody2D

var outro_started := false


# He collapses, turns back into normal Bixby and coughs Liam up, all drawn on the defeat sheet.
func Enter() -> void:
	body.fly_velocity = Vector2.ZERO
	outro_started = false
	body.play_anim(&"defeat")


# The fight is only called once Liam has landed, so his win lines follow the cough-up.
func Update(_delta: float) -> void:
	if not outro_started and body.current_anim == &"defeat" and body.anim_step >= BixbyBeastArtLayout.DEFEAT_LIAM_LANDS_FRAME:
		outro_started = true
		body.finish_victory()
