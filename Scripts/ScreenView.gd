extends RefCounted

# The only writer of the root viewport's canvas transform, so the finisher's zoom and the screen
# shakes that go through here combine instead of overwriting each other. CanvasLayers (the HUD, boss
# bars, dialogue and fades) aren't affected by it.

# The arena background's size: a zoomed view is kept inside it.
const VIEW_SIZE := Vector2(1920, 1080)

static var zoom := 1.0
static var focus := VIEW_SIZE / 2.0
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
	if zoom <= 1.0:
		tree.root.canvas_transform = Transform2D.IDENTITY.translated(shake_offset)
		return
	var half_view := VIEW_SIZE / 2.0 / zoom
	var centre := focus.clamp(half_view, VIEW_SIZE - half_view)
	# Whole pixels, so the zoomed pixel art doesn't shimmer as the view moves.
	var origin := (VIEW_SIZE / 2.0 - centre * zoom).round() + shake_offset
	tree.root.canvas_transform = Transform2D(Vector2(zoom, 0.0), Vector2(0.0, zoom), origin)


static func reset(tree: SceneTree) -> void:
	if zoom_tween:
		zoom_tween.kill()
	if shake_tween:
		shake_tween.kill()
	zoom = 1.0
	focus = VIEW_SIZE / 2.0
	shake_offset = Vector2.ZERO
	tree.root.canvas_transform = Transform2D.IDENTITY


static func world_to_screen(tree: SceneTree, point: Vector2) -> Vector2:
	return tree.root.canvas_transform * point
