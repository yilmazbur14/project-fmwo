extends RefCounted

# Shared by hazards that cover the whole arena (Computah's laser, the mech's shockwave),
# where dashing through is the intended dodge. A dash only grants immunity if the previous
# dash started at least `cooldown` before it, so mashing dash can't chain immunity windows.
static func is_immune(player: Node, immunity_time: float, cooldown: float) -> bool:
	var dodge_frame: int = player.last_dodge_physics_frame
	if dodge_frame < 0:
		return false
	var ticks := Engine.physics_ticks_per_second
	if Engine.get_physics_frames() - dodge_frame > roundi(immunity_time * ticks):
		return false
	var previous_frame: int = player.previous_dodge_physics_frame
	return previous_frame < 0 or dodge_frame - previous_frame >= roundi(cooldown * ticks)
