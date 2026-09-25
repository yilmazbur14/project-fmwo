extends "res://Scripts/BossJuggled.gd"

# Josh under the tiered finisher's uppercuts (BossJuggled), on his own juggle sheet. While he is up his
# flight shadow is hidden and the juggle's leap shadow, the same shadow at the same spot, stands in for
# it; his own comes back as he crashes. His state machine builds this in code (JoshCardsStateMachine).

const JoshArtLayout := preload("res://Scripts/JoshArtLayout.gd")


func _art() -> Dictionary:
	return JoshArtLayout.juggle()


# The leap shadow stands on his floor point, where his own shadow's node is, rather than under the centre
# of his feet texel, which rounds a step or two off it: the two are the same dithered sheet, and a
# shift of a pixel or two would show as the checker jumping when his own comes back at the crash.
func lift(px: float) -> void:
	super(px)
	if is_instance_valid(shadow):
		shadow.global_position = body.shadow.global_position


func _own_shadow(mode: StringName) -> void:
	body.shadow.visible = mode != &"air"


func _ground_layer() -> Node:
	return state_machine.ground_layer()
