extends "res://Scripts/BossJuggled.gd"

# Liam thrown by the tiered finisher's uppercuts, drawn by BossJuggled from his layout's juggle table, his own shadow
# hidden while the leap shadow stands in for it.

const Layout := preload("res://Scripts/LiamArtLayout.gd")


func _art() -> Dictionary:
	return Layout.juggle()


# The stand-in's own motion (a lying turn, a squash) must not ride into the juggle's frames.
func _on_enter() -> void:
	body.reset_sprite_pose()


func _own_shadow(mode: StringName) -> void:
	if not is_instance_valid(body.shadow):
		return
	body.shadow.visible = mode != &"air"


func _ground_layer() -> Node:
	return state_machine.ground_layer()
