extends "res://Scripts/BossJuggled.gd"

# Matt thrown into the air by the tiered finisher's uppercuts, on his juggle sheet (BossJuggled), with
# his leap shadow on the floor under both fighters. MattStateMachine builds it, beside his Broken.

const MattArtLayout := preload("res://Scripts/MattArtLayout.gd")


func _art() -> Dictionary:
	return MattArtLayout.juggle()


func _ground_layer() -> Node:
	return state_machine.ground_layer()
