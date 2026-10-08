extends RefCounted

# One impact sound start at a time across Mason's bombs and nuggets (the 2026-10-04 playtest: a line going off
# under a shower started a dozen in a second, and they machine-gunned). Counted in physics frames, so a hit-stop,
# which stretches game seconds into many real ones, can't let a burst through either.
const MIN_GAP := 0.09

static var last_frame := -1000000


static func allow() -> bool:
	var now := Engine.get_physics_frames()
	if now - last_frame < ceili(MIN_GAP * Engine.physics_ticks_per_second):
		return false
	last_frame = now
	return true
