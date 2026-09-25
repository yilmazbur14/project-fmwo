extends Node2D

# The Deafening Yell's wobble, once the mash has failed: the arena and the booms swim in crossed waves and
# the whole view sways round its middle, so an arrow's direction is hard to read while the input still
# takes the true one. It is the arena's last draw - the top z of the world's canvas, reading the screen as
# the arena left it - so every CanvasLayer draws over it sharp: the fight HUD and the RESIST! prompt (1),
# the entrance (90), the lines (100), the VS card (110), the pause menu (120) and the outro fade (128).
# MattScript owns one, built in its _ready; amount 0 hides it outright.
#
# The phases move in _process, so a pause, a fight freeze and a hit-stop all hold it; the shader never
# reads TIME.

const SHADER := preload("res://Assets/Shaders/screen_wobble.gdshader")

@export var amplitude_px := 36.0
@export var cross := 0.6
@export var wavelength_px := 380.0
# Radians a second.
@export var speed := 2.2
# The whole view's sway round its middle at full amount: this many degrees each way, one swing every
# TAU / sway_speed seconds.
@export var sway_degrees := 18.0
@export var sway_speed := 1.6
# Drawn this much larger at full amount, so the sway turns less of the edge in.
@export var zoom := 1.06
@export var vignette := 0.5
@export var snap_px := 3.0

var amount := 0.0:
	set(value):
		amount = value
		_apply()
var phase := 0.0
var sway_phase := 0.0
var shader_material: ShaderMaterial
var fade: Tween


func _ready() -> void:
	z_index = RenderingServer.CANVAS_ITEM_Z_MAX
	z_as_relative = false
	shader_material = ShaderMaterial.new()
	shader_material.shader = SHADER
	material = shader_material
	_apply()


func _process(delta: float) -> void:
	if not visible:
		return
	# Wrapped at ten turns, where both waves (the cross one runs at 0.7 of the phase) come round together.
	phase = fmod(phase + speed * delta, TAU * 10.0)
	sway_phase = fmod(sway_phase + sway_speed * delta, TAU)
	shader_material.set_shader_parameter(&"phase", phase)
	shader_material.set_shader_parameter(&"sway", sway_angle())
	queue_redraw()


# The whole view, wherever the camera and the shakes have put the arena.
func _draw() -> void:
	draw_set_transform_matrix(get_global_transform_with_canvas().affine_inverse())
	draw_rect(get_viewport_rect(), Color.WHITE)


# Radians the view is turned by now.
func sway_angle() -> float:
	return deg_to_rad(sway_degrees) * amount * sin(sway_phase)


# To `to` over `time` seconds on a tween bound to this node, from wherever it is now.
func set_amount(to: float, time: float) -> void:
	if fade:
		fade.kill()
	if time <= 0.0:
		amount = to
		return
	fade = create_tween()
	fade.tween_property(self, "amount", to, time)


func clear() -> void:
	if fade:
		fade.kill()
	amount = 0.0


func _apply() -> void:
	visible = amount >= 0.001
	if shader_material == null:
		return
	shader_material.set_shader_parameter(&"amount", amount)
	shader_material.set_shader_parameter(&"amplitude_px", amplitude_px)
	shader_material.set_shader_parameter(&"cross", cross)
	shader_material.set_shader_parameter(&"wavelength_px", wavelength_px)
	shader_material.set_shader_parameter(&"snap_px", snap_px)
	shader_material.set_shader_parameter(&"zoom", lerpf(1.0, zoom, amount))
	shader_material.set_shader_parameter(&"vignette", vignette)
	shader_material.set_shader_parameter(&"phase", phase)
	shader_material.set_shader_parameter(&"sway", sway_angle())
