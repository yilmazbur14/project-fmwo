extends State

# He goes down and the dark goes with him. Nothing here may leave the curtain up: it would follow the
# fight into FightOutro and cover his own last lines.

@export var body : CharacterBody2D

# A juggle killed him: he has landed from it and lies on its `down` loop (BossJuggled), so his defeat
# isn't played over the top. Set by CarterStateMachine.land_juggled.
var lying := false


func Enter() -> void:
	body.velocity = Vector2.ZERO
	body.snap_dark_clear()
	body.snap_music_level()
	body.show_body(true)
	body.show_mark_glow(false)
	body.show_aura(false)
	if not lying:
		body.play_anim(&"defeat")
