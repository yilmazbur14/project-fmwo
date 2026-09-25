extends "res://Scripts/BossJuggled.gd"

# Captain Burak thrown into the air by the tiered finisher's uppercuts, on his juggle sheet (BossJuggled).
# Only his Break's window pays it (BurakBossScript.can_be_juggled).

const Layout := preload("res://Scripts/BurakBossArtLayout.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")


func _art() -> Dictionary:
	return Layout.juggle()


# Nothing of an attack may hang over him in the air: its bullet timer or its badge.
func _on_enter() -> void:
	body.hide_pips()
	ParryTell.clear(body)
