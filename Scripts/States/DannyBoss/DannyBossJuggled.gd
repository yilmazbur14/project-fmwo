extends "res://Scripts/BossJuggled.gd"

# Danny thrown into the air by the tiered finisher's uppercuts, on his juggle sheet (BossJuggled). Only his
# Break's window pays it (DannyBossScript.can_be_juggled). Juggled to 0 HP, he lands into the sumo lying down
# (DannyBossStateMachine.enter_sumo).

const Layout := preload("res://Scripts/DannyBossArtLayout.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")


func _art() -> Dictionary:
	return Layout.juggle()


# Nothing may hang over him in the air: a badge, or anything of his nap.
func _on_enter() -> void:
	ParryTell.clear(body)
	body.clear_nap_fx()
