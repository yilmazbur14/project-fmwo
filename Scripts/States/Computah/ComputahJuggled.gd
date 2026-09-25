extends "res://Scripts/BossJuggled.gd"

# Computah thrown by the tiered finisher's uppercuts after a Break (BossJuggled), drawn off
# computah_juggle. ComputahStateMachine builds it in code; the frames, the anchors and the timings are
# all ComputahArtLayout.FINAL_JUGGLE's.

const Layout := preload("res://Scripts/ComputahArtLayout.gd")


func _art() -> Dictionary:
	return Layout.juggle()


# His fight has no Arena/GroundFx and his body no floor_layer, and the base's last resort, his scene
# root, would add the leap shadow after his body: at the same y the y-sort then draws it over his feet.
func _ground_layer() -> Node:
	return state_machine.ground_layer()
