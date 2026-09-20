extends Sprite2D

# Eric's sword out of his hands. The Break (EricBroken), or the first uppercut of a juggle that didn't
# start from one (EricJuggled), knocks it out of his grip into the mat, where it stands until he calls it
# back (EricBroken's retrieve). EricStateMachine keeps the one that's out.
# It's drawn in his frame space where his sprite stood, and left in the world there rather than on him,
# so whatever moves him afterwards, it stays. It ties with him on the y-sort and goes first, so it draws
# behind him. Harmless, so it isn't one of his hazards: those are freed whenever his attacks stop.
# It plunges, wobbles and stands on its own clock, in game time, frozen with the fight.

const EricArtLayout := preload("res://Scripts/EricArtLayout.gd")

# His origin when it was knocked away.
var spot := Vector2.ZERO
var clock := 0.0


func plant(body: CharacterBody2D, state_machine: Node) -> void:
	var spec: Dictionary = EricArtLayout.broken().sword
	texture = load(spec.texture)
	hframes = spec.hframes
	scale = body.scale
	offset = EricArtLayout.SPRITE_OFFSET - EricArtLayout.SORT_POINT
	flip_h = body.sprite.flip_h
	spot = body.global_position
	state_machine.add_hazard(self, spot + EricArtLayout.SORT_POINT * body.scale, false)
	remove_from_group(state_machine.HAZARD_GROUP)


# It plunges, wobbles and stands, then holds its last frame.
func _physics_process(delta: float) -> void:
	clock += delta
	var times: Array = EricArtLayout.broken().sword.frame_times
	var t := clock
	var shown := times.size()
	for i in times.size():
		if t < times[i]:
			shown = i
			break
		t -= times[i]
	frame = shown


# Its crossguard's centre, where the return flight picks it up.
func guard_point() -> Vector2:
	var spec: Dictionary = EricArtLayout.broken().sword
	return spot + EricArtLayout.frame_local(spec.guard + Vector2(0.5, 0.5), flip_h) * scale


# The point on the mat under the crossguard, where the blade goes in.
func mat_point() -> Vector2:
	var spec: Dictionary = EricArtLayout.broken().sword
	return spot + EricArtLayout.frame_local(Vector2(spec.guard.x + 0.5, spec.mat_row), flip_h) * scale
