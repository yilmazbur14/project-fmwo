extends "res://Scripts/BossJuggled.gd"

# Beast Bixby thrown by the tiered finisher's uppercuts, drawn by BossJuggled from his layout's juggle
# table. While he is up, the leap shadow stands in for his own; as he crashes, his own comes back as the
# exhausted, wings-flat one he lies on.

const BixbyBeastArtLayout := preload("res://Scripts/BixbyBeastArtLayout.gd")

# bixby_beast_shadow_ground.png's exhausted frame, the wings flat.
const CRASH_SHADOW_FRAME := 1


func _art() -> Dictionary:
	return BixbyBeastArtLayout.juggle()


func _own_shadow(mode: StringName) -> void:
	var own: Sprite2D = body.shadow
	match mode:
		&"air":
			own.hide()
		&"ground":
			own.texture = body.shadow_sheets[BixbyBeastArtLayout.Shadow.GROUND]
			own.frame = CRASH_SHADOW_FRAME
			own.flip_h = false
			own.show()
		&"restore":
			own.show()


# His scene's root would sort the leap shadow in among the fighters.
func _ground_layer() -> Node:
	return state_machine.ground_layer()
