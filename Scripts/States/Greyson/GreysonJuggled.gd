extends "res://Scripts/BossJuggled.gd"

# Greyson thrown into the air by the tiered finisher's uppercuts (BossJuggled), off GreysonArtLayout.juggle(), his
# juggle sheet. Only the Break's window pays it (GreysonScript.can_be_juggled). Juggled to 0 HP, he lands into the
# final brawl lying on his KO loop (GreysonStateMachine.land_juggled).

const Layout := preload("res://Scripts/GreysonArtLayout.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")


func _art() -> Dictionary:
	return Layout.juggle()


# Nothing may hang over him in the air.
func _on_enter() -> void:
	ParryTell.clear(body)
