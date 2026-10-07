extends Node2D

# The screen's part of Greyson's beam, V2 (JordanComboMaze): the dark closing in on the player as he charges, the flash
# red then white as the beam lands, and the colours kicked apart and settling. Laid over the whole view in world space
# (JordanGodLayout.DARK_BORDER) rather than on a CanvasLayer, so the HUD's layers stay over it and clean. On the Fx
# layer: the vignette under the layer's own effects and over everything the lights-out lifted, the kick and the flash
# over the effects. The flash and the kick run on real seconds, as a hit-stop does, so they play through one.
#
# Two canvas_item shaders built here in code. The vignette is stepped on the texel grid and banded, to sit with the
# pixel art; the kick is shown only while it runs, since it redraws the whole screen.

const Layout := preload("res://Scripts/JordanMazeLayout.gd")
const GodLayout := preload("res://Scripts/JordanGodLayout.gd")

const VIGNETTE_Z := -5
const KICK_Z := 10
const FLASH_Z := 11
const TEXEL := 3.0

const VIGNETTE_SHADER := """
shader_type canvas_item;
render_mode unshaded;
uniform vec2 player_at;
uniform vec2 muzzle_at;
uniform float radius = 1500.0;
uniform float muzzle_radius = 150.0;
uniform float softness = 210.0;
uniform float strength = 0.0;
uniform float bands = 6.0;
uniform float texel = 3.0;
varying vec2 local_pos;
void vertex() {
	local_pos = VERTEX;
}
void fragment() {
	vec2 p = (floor(local_pos / texel) + 0.5) * texel;
	float dark = smoothstep(radius, radius + softness, distance(p, player_at));
	dark *= smoothstep(muzzle_radius, muzzle_radius + softness * 0.6, distance(p, muzzle_at));
	dark = floor(dark * bands + 0.5) / bands;
	COLOR = vec4(0.0, 0.0, 0.0, dark * strength);
}
"""

const KICK_SHADER := """
shader_type canvas_item;
render_mode unshaded;
uniform sampler2D screen_tex : hint_screen_texture, filter_nearest;
uniform float amount = 0.0;
void fragment() {
	vec2 off = vec2(amount, 0.0) * SCREEN_PIXEL_SIZE;
	COLOR = vec4(texture(screen_tex, SCREEN_UV - off).r, texture(screen_tex, SCREEN_UV).g,
		texture(screen_tex, SCREEN_UV + off).b, 1.0);
}
"""

var vignette: Polygon2D
var kick_cover: Polygon2D
var flash_cover: Polygon2D
var flash_tween: Tween
var kick_tween: Tween
# How dark it is now, 0 to 1 of the vignette's strength, for a test.
var darkness := 0.0


func _ready() -> void:
	vignette = _cover(VIGNETTE_Z)
	vignette.material = _material(VIGNETTE_SHADER)
	vignette.color = Color.WHITE
	kick_cover = _cover(KICK_Z)
	kick_cover.material = _material(KICK_SHADER)
	kick_cover.visible = false
	flash_cover = _cover(FLASH_Z)
	flash_cover.visible = false
	close_in(Vector2.ZERO, Vector2.ZERO, 0.0)


# The dark `share` of the way closed in on `player_at`, clear round `muzzle_at` too, world px.
func close_in(player_at: Vector2, muzzle_at: Vector2, share: float) -> void:
	var spec := Layout.BEAM_V2_VIGNETTE
	var closing := share * share
	_set_vignette(player_at, muzzle_at, lerpf(spec.from, spec.to, closing), clampf(share * 2.0, 0.0, 1.0))


# Opening again as the beam breaks up: `share` of the way back to nothing.
func open_up(player_at: Vector2, muzzle_at: Vector2, share: float) -> void:
	var spec := Layout.BEAM_V2_VIGNETTE
	_set_vignette(player_at, muzzle_at, lerpf(spec.to, spec.from, share * share), 1.0 - share)


func _set_vignette(player_at: Vector2, muzzle_at: Vector2, radius: float, amount: float) -> void:
	var spec := Layout.BEAM_V2_VIGNETTE
	darkness = amount
	vignette.visible = amount > 0.0
	var material := vignette.material as ShaderMaterial
	material.set_shader_parameter("player_at", to_local(player_at))
	material.set_shader_parameter("muzzle_at", to_local(muzzle_at))
	material.set_shader_parameter("radius", radius)
	material.set_shader_parameter("muzzle_radius", spec.muzzle)
	material.set_shader_parameter("softness", spec.softness)
	material.set_shader_parameter("strength", spec.strength * amount)
	material.set_shader_parameter("bands", spec.bands)
	material.set_shader_parameter("texel", TEXEL)


# Red for a frame, then white, then gone: real seconds.
func flash() -> void:
	var spec := Layout.BEAM_V2_FLASH
	if flash_tween != null and flash_tween.is_valid():
		flash_tween.kill()
	flash_cover.color = spec.red
	flash_cover.visible = true
	flash_tween = create_tween().set_ignore_time_scale(true)
	flash_tween.tween_interval(spec.red_time)
	flash_tween.tween_callback(func() -> void: flash_cover.color = spec.white)
	flash_tween.tween_interval(spec.white_time)
	flash_tween.tween_callback(flash_cover.hide)


# The colours kicked apart and settling back in whole px: real seconds.
func kick() -> void:
	var spec := Layout.BEAM_V2_CHROMA
	if kick_tween != null and kick_tween.is_valid():
		kick_tween.kill()
	kick_cover.visible = true
	kick_tween = create_tween().set_ignore_time_scale(true)
	kick_tween.tween_method(_kick_amount, spec.px, 0.0, spec.time).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	kick_tween.tween_callback(kick_cover.hide)


func _kick_amount(px: float) -> void:
	(kick_cover.material as ShaderMaterial).set_shader_parameter("amount", roundf(px))


# The whole view and a view past it each way, whatever the camera does.
func _cover(z: int) -> Polygon2D:
	var border: Rect2 = GodLayout.DARK_BORDER
	var cover := Polygon2D.new()
	cover.polygon = PackedVector2Array([to_local(border.position), to_local(Vector2(border.end.x, border.position.y)),
		to_local(border.end), to_local(Vector2(border.position.x, border.end.y))])
	cover.z_index = z
	add_child(cover)
	return cover


func _material(code: String) -> ShaderMaterial:
	var shader := Shader.new()
	shader.code = code
	var material := ShaderMaterial.new()
	material.shader = shader
	return material
