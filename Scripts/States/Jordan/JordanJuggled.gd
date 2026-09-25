extends "res://Scripts/BossJuggled.gd"

# Jordan thrown into the air by the tiered finisher's uppercuts, on his juggle sheet (BossJuggled).
# JordanStateMachine builds it, beside his Broken.

const JordanArtLayout := preload("res://Scripts/JordanArtLayout.gd")


func _art() -> Dictionary:
	return JordanArtLayout.juggle()


# A blast from a figure he was punched with leans him back on a tween of the sprite's rotation, which
# would go on tipping the juggle frames.
func _on_enter() -> void:
	if body.stagger_tween:
		body.stagger_tween.kill()
	body.sprite.rotation = 0.0


func _ground_layer() -> Node:
	return state_machine.ground_layer()
