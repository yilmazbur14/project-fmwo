extends RefCounted

# Shared by every hit-stop, so overlapping ones keep the longest: a boss's regular hit-stop
# would otherwise restore time_scale in the middle of a charged punch's longer one.
const TIME_SCALE := 0.05

static var release_timer: SceneTreeTimer


static func freeze(tree: SceneTree, duration: float) -> void:
	Engine.time_scale = TIME_SCALE
	if release_timer and release_timer.time_left >= duration:
		return
	# Ignores time_scale, otherwise the slowdown would stretch its own duration.
	var timer := tree.create_timer(duration, true, false, true)
	release_timer = timer
	timer.timeout.connect(func():
		if release_timer == timer:
			release_timer = null
			Engine.time_scale = 1.0
	)
