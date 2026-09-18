extends State

# He goes down and the dark goes with him. Nothing here may leave the curtain up: it would follow the
# fight into FightOutro and cover his own last lines.

@export var body : CharacterBody2D


func Enter() -> void:
	body.velocity = Vector2.ZERO
	body.snap_dark_clear()
	body.snap_music_level()
	body.show_body(true)
	body.show_mark_glow(false)
	body.show_aura(false)
	body.play_anim(&"defeat")
