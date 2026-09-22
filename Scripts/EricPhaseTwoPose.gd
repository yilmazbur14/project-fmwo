extends RefCounted

# Drawing Eric on his phase-two frames. Six states need it - the cut, the mixup, the leap, his stand
# between attacks, his winded window and his parry stagger - because from the moment the sword leaves
# the ring NOTHING may draw him holding it, and every one of his main-sheet poses does.
# Which frames a pose is on is EricArtLayout's business (phase_two); this only puts them on his
# sprite and picks the one a clock is up to.

const EricArtLayout := preload("res://Scripts/EricArtLayout.gd")


# Puts `key`'s sheet and first frame on `sprite` and hands back the pose's frames, for the caller to
# step with frame_at().
static func show(sprite: Sprite2D, key: String) -> Array:
	var pose: Dictionary = EricArtLayout.phase_two(key)
	sprite.texture = load(pose.texture)
	sprite.hframes = pose.hframes
	sprite.frame = pose.frames[0]
	return pose.frames


static func frame_at(frames: Array, clock: float) -> int:
	if frames.size() < 2:
		return frames[0]
	return frames[int(clock / EricArtLayout.phase_two_frame_time()) % frames.size()]
