extends RefCounted

# Shared by every hit-stop, so overlapping ones keep the longest: a boss's regular hit-stop
# would otherwise restore time_scale in the middle of a charged punch's longer one.
const TIME_SCALE := 0.05

# Whoever holds this owns the restore: every stage checks it is still the one that set it before
# touching time_scale, so a later stop always wins and nothing restores under it. FightOutro clears
# it, so a fight ending mid-stop doesn't leave the outro crawling.
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


# A dead stop, then a beat of slow motion before normal speed: the parry's 3rd Strike moment. The
# times are real seconds, so the stop doesn't stretch itself, and a second call restarts the shape,
# which is what parries in a row want.
static func freeze_then_slow(tree: SceneTree, hold: float, tail: float, tail_scale: float) -> void:
	Engine.time_scale = TIME_SCALE
	var stop := tree.create_timer(hold, true, false, true)
	release_timer = stop
	stop.timeout.connect(func():
		if release_timer != stop:
			return
		Engine.time_scale = tail_scale
		var back := tree.create_timer(tail, true, false, true)
		release_timer = back
		back.timeout.connect(func():
			if release_timer == back:
				release_timer = null
				Engine.time_scale = 1.0
		)
	)


# Normal speed at once, whatever stage a stop was in.
static func clear() -> void:
	release_timer = null
	Engine.time_scale = 1.0
