extends RefCounted

# The only writer of the root viewport's canvas transform, so the finisher's zoom and the screen
# shakes that go through here combine instead of overwriting each other. CanvasLayers (the HUD, boss
# bars, dialogue and fades) aren't affected by it.
#
# THE FIGHT'S BASE VIEW: a fight can be drawn further out than the arena - Jordan's last phase shows
# its whole void at 2/3 (set_base) - and `zoom` is a factor OVER that base: 1 is the base view itself,
# and every zoom anything asks for (the finisher's 1.5, a Break's close-up, a parry's punch-in) is
# that much closer than the base, kept inside the base view's own rect, and a zoom back to 1 is back
# to the base. Every other fight plays on the arena's own base (1, centred on it), where the view is
# exactly what it always was. The fight that sets a base clears it as it goes (clear_base).
#
# A FLOOR instead of a base (set_floor): the base view, but `zoom` stays what everything asks for rather than a
# factor over it, and nothing draws the world further out than the floor - a zoom under it, or back to 1, is the
# floor view itself. Greyson's final brawl frames its view this way, so the zooms back to 1 that the finisher and
# the parry's punch-in end on can't pull it out to the whole arena (the user, 2026-10-04). Off, nothing changes.

# The arena background's size: a zoomed view is kept inside it.
const VIEW_SIZE := Vector2(1920, 1080)

static var zoom := 1.0
static var focus := VIEW_SIZE / 2.0
static var base_zoom := 1.0
static var base_focus := VIEW_SIZE / 2.0
static var base_is_floor := false
static var shake_offset := Vector2.ZERO
static var zoom_tween: Tween
static var shake_tween: Tween


# SceneTree tweens, so hit-stop slows them like the fight and a scene change can't leave the canvas
# offset or zoomed. `ignore_time_scale` is for punches meant to play out during a hit-stop.
static func zoom_to(tree: SceneTree, to_zoom: float, to_focus: Vector2, duration: float, ignore_time_scale := false) -> void:
	if zoom_tween:
		zoom_tween.kill()
	var from_zoom := zoom
	var from_focus := focus
	var step := func(weight: float) -> void:
		zoom = lerpf(from_zoom, to_zoom, weight)
		focus = from_focus.lerp(to_focus, weight)
		apply(tree)
	zoom_tween = tree.create_tween().set_ignore_time_scale(ignore_time_scale)
	zoom_tween.tween_method(step, 0.0, 1.0, duration).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)


# With a `direction`, the shake is a jolt along it that settles instead of a random rattle.
static func shake(tree: SceneTree, strength: float, steps: int, step_time: float, direction := Vector2.ZERO, ignore_time_scale := false) -> void:
	if shake_tween:
		shake_tween.kill()
	shake_tween = tree.create_tween().set_ignore_time_scale(ignore_time_scale)
	var push := direction.normalized()
	for i in steps:
		var step_strength := strength * (1.0 - float(i) / steps)
		var offset := Vector2(randf_range(-step_strength, step_strength), randf_range(-step_strength, step_strength)).round()
		if push != Vector2.ZERO:
			offset = (push * step_strength * (1.0 if i % 2 == 0 else -0.5)).round()
		shake_tween.tween_callback(func() -> void:
			shake_offset = offset
			apply(tree)
		)
		shake_tween.tween_interval(step_time)
	shake_tween.tween_callback(func() -> void:
		shake_offset = Vector2.ZERO
		apply(tree)
	)


static func apply(tree: SceneTree) -> void:
	var view := _view()
	var scale: float = view[0]
	var centre: Vector2 = view[1]
	if is_equal_approx(scale, 1.0) and centre.is_equal_approx(VIEW_SIZE / 2.0):
		tree.root.canvas_transform = Transform2D.IDENTITY.translated(shake_offset)
		return
	# Whole pixels, so the zoomed pixel art doesn't shimmer as the view moves.
	var origin := (VIEW_SIZE / 2.0 - centre * scale).round() + shake_offset
	tree.root.canvas_transform = Transform2D(Vector2(scale, 0.0), Vector2(0.0, scale), origin)


# [the scale the world is drawn at, the world point at the middle of the screen], shake aside: the base
# view, or `zoom` times closer centred on `focus`, kept inside the base view's rect.
static func _view() -> Array:
	var scale := base_zoom * zoom
	if base_is_floor:
		if zoom <= base_zoom:
			return [base_zoom, base_focus]
		scale = zoom
	elif zoom <= 1.0:
		return [base_zoom, base_focus]
	var bounds := base_rect()
	var half_view := VIEW_SIZE / 2.0 / scale
	return [scale, focus.clamp(bounds.position + half_view, bounds.end - half_view)]


# The world the base view shows: the arena itself, on the arena's own base.
static func base_rect() -> Rect2:
	return Rect2(base_focus - VIEW_SIZE / 2.0 / base_zoom, VIEW_SIZE / base_zoom)


# Back to the base view, still and level.
static func reset(tree: SceneTree) -> void:
	if zoom_tween:
		zoom_tween.kill()
	if shake_tween:
		shake_tween.kill()
	zoom = 1.0
	focus = base_focus
	shake_offset = Vector2.ZERO
	apply(tree)


# A fight's own base view, `to_zoom` centred on `to_focus`, with the view on screen kept exactly where
# it is: it becomes a zoom over the new base, which a zoom_to(1.0, ...) then eases out to.
static func set_base(tree: SceneTree, to_zoom: float, to_focus: Vector2) -> void:
	var view := _view()
	base_zoom = to_zoom
	base_focus = to_focus
	base_is_floor = false
	zoom = view[0] / base_zoom
	focus = view[1]
	apply(tree)


# A fight's floor view, `to_zoom` centred on `to_focus` (see the header): the zooms asked for stay as they are, and
# none draws the world further out than this. clear_base() ends it.
static func set_floor(tree: SceneTree, to_zoom: float, to_focus: Vector2) -> void:
	base_zoom = to_zoom
	base_focus = to_focus
	base_is_floor = true
	apply(tree)


# The arena's own base again, as the fight that set another goes - or a floor.
static func clear_base(tree: SceneTree) -> void:
	base_zoom = 1.0
	base_focus = VIEW_SIZE / 2.0
	base_is_floor = false
	reset(tree)


static func world_to_screen(tree: SceneTree, point: Vector2) -> Vector2:
	return tree.root.canvas_transform * point
