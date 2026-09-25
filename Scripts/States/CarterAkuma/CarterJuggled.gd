extends "res://Scripts/BossJuggled.gd"

# A Break's payout: the tiered finisher's juggle (BossJuggled), drawn from his juggle sheet
# (CarterArtLayout.FINAL_JUGGLE). His state machine builds it in code. There is no Broken state before
# it: his Break window is his Recover, cashed from a Break (CarterRecover.from_break).

const CarterArtLayout := preload("res://Scripts/CarterArtLayout.gd")


func _art() -> Dictionary:
	return CarterArtLayout.juggle()


# His aura and his mark are laid out on his standing 96x96 frame, not on the juggle's, so they would
# hang where he stood. Idle brings the aura back as he gets up.
func _on_enter() -> void:
	body.show_aura(false)
	body.show_mark_glow(false)
