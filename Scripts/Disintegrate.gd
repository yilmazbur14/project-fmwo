extends RefCounted

# A figure dissolving, texel by texel from the top down, as Jordan wipes the other bosses out of his server
# (JordanFinaleScript): Assets/Shaders/disintegrate.gdshader on it, driven from 0 to 1 on a tween bound to `host` so a
# pause holds it and a skip can run it out, and a puff of 1-texel dust off it while it goes. The figure is left hidden.

const SHADER := "res://Assets/Shaders/disintegrate.gdshader"
# The dust: squares a texel across at the art's 3x, drifting up off the figure.
const DUST := {
	"amount": 48,
	"lifetime": 0.9,
	"texel": 3.0,
	"color": Color(1.0, 0.45, 0.78),
	"speed": Vector2(20, 70),
	"spread": 60.0,
	"gravity": Vector2(0, -30),
}


# Awaitable.
static func run(host: Node, target: CanvasItem, seconds := 1.2) -> void:
	await start(host, target, seconds).finished


# The dissolve started, and its tween, for a caller that waits on it with its other waits.
static func start(host: Node, target: CanvasItem, seconds := 1.2) -> Tween:
	var material := ShaderMaterial.new()
	material.shader = load(SHADER)
	material.set_shader_parameter("progress", 0.0)
	if target is Sprite2D and target.vframes > 1:
		var row := float(target.frame_coords.y)
		material.set_shader_parameter("frame_v", Vector2(row, row + 1.0) / target.vframes)
	target.material = material
	var dust := _dust(target)
	var tween := host.create_tween()
	tween.tween_method(func(value: float) -> void: material.set_shader_parameter("progress", value), 0.0, 1.0, seconds)
	tween.tween_callback(_finish.bind(target, dust))
	return tween


static func _finish(target: CanvasItem, dust: CPUParticles2D) -> void:
	if is_instance_valid(target):
		target.hide()
	if not is_instance_valid(dust):
		return
	dust.emitting = false
	var gone := dust.create_tween()
	gone.tween_interval(dust.lifetime)
	gone.tween_callback(dust.queue_free)


# Dust over the figure's drawn rect, a sibling of it so it stays where it is.
static func _dust(target: CanvasItem) -> CPUParticles2D:
	var parent := target.get_parent()
	if not (target is Node2D) or parent == null:
		return null
	var dust := CPUParticles2D.new()
	var dot := Image.create(1, 1, false, Image.FORMAT_RGBA8)
	dot.fill(Color.WHITE)
	dust.texture = ImageTexture.create_from_image(dot)
	dust.amount = DUST.amount
	dust.lifetime = DUST.lifetime
	dust.scale_amount_min = DUST.texel
	dust.scale_amount_max = DUST.texel
	dust.color = DUST.color
	dust.direction = Vector2.UP
	dust.spread = DUST.spread
	dust.initial_velocity_min = DUST.speed.x
	dust.initial_velocity_max = DUST.speed.y
	dust.gravity = DUST.gravity
	dust.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	var rect: Rect2 = target.get_rect() if target.has_method("get_rect") else Rect2(Vector2.ZERO, Vector2.ONE)
	var node: Node2D = target
	dust.position = node.position + rect.get_center() * node.scale
	dust.emission_rect_extents = rect.size * node.scale.abs() / 2.0
	dust.z_index = node.z_index + 1
	parent.add_child(dust)
	dust.emitting = true
	return dust
