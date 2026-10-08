extends "res://Scripts/BossJuggled.gd"

# A puppet of Jordan's thrown into the air by the tiered finisher's uppercuts (BossJuggled), on its boss's own juggle
# sheet: the recoloured twin once it is in, the live one under the placeholder recolour until then
# (JordanPuppet.juggle_art). The puppet builds it and is its host, so the juggle's ends come back to the puppet's own
# after_juggle() and land_juggled(). Every uppercut's damage goes to Jordan, not here (JordanPuppet.take_juggle_hit).


func _art() -> Dictionary:
	return body.juggle_art()


# The puppets stand high - Greyson's top at about y 158, Captain Burak's about 200 - where a boss in his own fight is
# slid down to his juggle floor first (BossBroken), and nothing may move a puppet off its mark, so the base's clamp
# would flatten the lift. The apex runs up under the HUD instead, as the other bosses' apexes do, to at least
# JUGGLE_MIN_LIFT_SCALE of the planned three-uppercut apex.
func headroom() -> float:
	var finisher: Node = _finisher()
	var apex: float = finisher.planned_apex(3) if finisher else FALLBACK_APEX
	return maxf(super.headroom(), JUGGLE_MIN_LIFT_SCALE * apex)


func _on_enter() -> void:
	body.settle_sprite()
	body.use_twin_material(body.juggle_twin)
