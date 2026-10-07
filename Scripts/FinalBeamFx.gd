extends Node2D

# Everything the final beam draws in the world (JordanGodFinalBeam owns the flow): the player's drawn overlay or their
# posed stand-in, the charge's ball, aura, debris and arcs, the beam itself, the impact, his end - the drawn
# disintegration and reform sheets in place of his body, or the stand-in's radial dissolve, cracks and ash - and
# world-space covers for the vignette and the flashes. On the god's Fx layer; his end's sprites are children of him so
# they sit where his body does. Each drawn piece replaces its stand-in on its own (FinalBeamLayout). Every clock is
# this node's own process or a tween bound to it, so the pause holds all of it.

const Layout := preload("res://Scripts/FinalBeamLayout.gd")
const GodLayout := preload("res://Scripts/JordanGodLayout.gd")

const DISSOLVE_SHADER := """
shader_type canvas_item;
render_mode %s;
uniform float progress : hint_range(0.0, 1.0) = 0.0;
uniform vec2 frame_size = vec2(320.0, 224.0);
uniform vec2 impact = vec2(160.0, 124.0);
uniform float reach = 240.0;
uniform float sweep = 0.65;
uniform float edge = 0.12;
uniform vec4 edge_hot : source_color = vec4(1.0);
uniform vec4 edge_cool : source_color = vec4(0.56, 0.89, 1.0, 1.0);

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void fragment() {
	vec4 color = texture(TEXTURE, UV) * COLOR;
	vec2 local = mod(floor(UV / TEXTURE_PIXEL_SIZE), frame_size);
	float away = clamp(distance(local + 0.5, impact) / reach, 0.0, 1.0);
	float order = mix(hash(local), away, sweep);
	float gone = progress * (1.0 + edge) - edge;
	if (order < gone) {
		color.a = 0.0;
	} else if (order < gone + edge && color.a > 0.0) {
		color.rgb = mix(edge_hot.rgb, edge_cool.rgb, (order - gone) / edge);
	}
	COLOR = color;
}
"""

# Stepped on the texel grid and banded, to sit with the pixel art (JordanBeamScreen's vignette, round one point).
const VIGNETTE_SHADER := """
shader_type canvas_item;
render_mode unshaded;
uniform vec2 center;
uniform float radius = 300.0;
uniform float softness = 150.0;
uniform float strength = 0.0;
uniform float bands = 5.0;
uniform float texel = 3.0;
varying vec2 local_pos;
void vertex() {
	local_pos = VERTEX;
}
void fragment() {
	vec2 p = (floor(local_pos / texel) + 0.5) * texel;
	float dark = smoothstep(radius, radius + softness, distance(p, center));
	dark = floor(dark * bands + 0.5) / bands;
	COLOR = vec4(0.0, 0.0, 0.0, dark * strength);
}
"""

const CIRCLE_POINTS := 28

var god: Node2D
var player: CharacterBody2D
var staging: Dictionary
var final_player := false
var final_god := false
var textures := {}

# What a test reads: the ball's size (bars), the dissolve's progress (on the drawn sheets, the tau of the frame
# showing), and the beam's width factor and length.
var ball_size := 0
var progress := 0.0
var beam_width := 0.0
var beam_length := 0.0

var clock := 0.0
var bars := 0
var charging := false
var contact_column := 0
var vignette: Polygon2D
var vignette_strength := 0.0
var vignette_radius := 0.0
var aura: Node2D
var aura_sprite: Sprite2D
var aura_glow: Polygon2D
var flames: Polygon2D
var flicker_left := 0.0
var overlay: Sprite2D
var overlay_on := false
var pose_spec := {}
var pose_name := &""
var pose_step := 0
var pose_clock := 0.0
var debris: CPUParticles2D
var ash: CPUParticles2D
var beam: Node2D
var beam_clock := 0.0
var beam_layers: Array[Polygon2D] = []
var head_layers: Array[Polygon2D] = []
var muzzle_layers: Array[Polygon2D] = []
var start_sprites: Array[Sprite2D] = []
var tile_sprites: Array[Sprite2D] = []
var head_sprites: Array[Sprite2D] = []
var muzzle_sprites: Array[Sprite2D] = []
var beam_full := 0.0
var beam_fade := 1.0
var sputtering := false
var ball: Node2D
var ball_layers: Array[Polygon2D] = []
var ball_sprites: Array[Sprite2D] = []
var fizzle: Node2D
var fizzle_sprites: Array[Sprite2D] = []
var arcs: Array[Line2D] = []
var arc_left := 0.0
var impact: Node2D
var impact_sprites: Array[Sprite2D] = []
var impact_clock := -1.0
var flash_cover: Polygon2D
var flash_tween: Tween
var cracks: Node2D
var crack_rays: Array[Line2D] = []
var crack_points: Array = []
var god_end: Node2D
var god_end_sprites: Array[Sprite2D] = []
var core_popped := false
var dissolve_materials: Array[ShaderMaterial] = []
var dissolve_tween: Tween
var width_tween: Tween
var runes_tween: Tween
var aura_flare := 1.0
var god_jitter := false
var saved := {}


#BUILDING

# In the collapse beat: every texture is loaded here, never in a preload, and whatever isn't drawn yet is its stand-in.
func setup(jordan: Node2D, p: CharacterBody2D) -> void:
	god = jordan
	player = p
	staging = Layout.staging()
	final_player = Layout.final_player()
	final_god = Layout.final_god()
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	contact_column = _contact_column()
	_save_god()
	_build_vignette()
	_build_aura()
	_build_overlay()
	_build_debris()
	_build_ash()
	_build_beam()
	_build_ball()
	_build_arcs()
	impact = Node2D.new()
	impact.name = "Impact"
	add_child(impact)
	flash_cover = _cover()
	flash_cover.name = "Flash"
	flash_cover.visible = false
	add_child(flash_cover)
	_build_god_end()


func _texture(path: String) -> Texture2D:
	if not textures.has(path):
		textures[path] = load(path) if Layout.has_piece(path) else null
	return textures[path]


func _additive() -> CanvasItemMaterial:
	var added := CanvasItemMaterial.new()
	added.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	return added


func _circle(radius: float) -> PackedVector2Array:
	var points := PackedVector2Array()
	for i in CIRCLE_POINTS:
		points.append(Vector2.from_angle(TAU * i / CIRCLE_POINTS) * radius)
	return points


func _polygon(points: PackedVector2Array, color: Color, add: bool) -> Polygon2D:
	var shape := Polygon2D.new()
	shape.polygon = points
	shape.color = color
	if add:
		shape.material = _additive()
	return shape


func _cover() -> Polygon2D:
	var border: Rect2 = GodLayout.DARK_BORDER
	return _polygon(PackedVector2Array([border.position, Vector2(border.end.x, border.position.y), border.end,
		Vector2(border.position.x, border.end.y)]), Color.WHITE, false)


func _shader(code: String) -> Shader:
	var shader := Shader.new()
	shader.code = code
	return shader


# A sheet on its pivot at 3 px a texel, `add` for a glow.
func _sheet_sprite(path: String, frame: Vector2, anchor: Vector2, add: bool) -> Sprite2D:
	var sprite := Sprite2D.new()
	sprite.texture = _texture(path)
	sprite.hframes = maxi(roundi(sprite.texture.get_width() / frame.x), 1)
	sprite.vframes = maxi(roundi(sprite.texture.get_height() / frame.y), 1)
	sprite.centered = false
	sprite.offset = -anchor
	sprite.scale = Vector2.ONE * Layout.TEXEL
	if add:
		sprite.material = _additive()
	return sprite


# A piece's glow under it, then the piece: as many of the two as are in.
func _glow_and_piece(spec: Dictionary, parent: Node) -> Array[Sprite2D]:
	var out: Array[Sprite2D] = []
	if spec.has("glow") and Layout.has_piece(spec.glow):
		out.append(_sheet_sprite(spec.glow, spec.frame, spec.anchor, true))
	if Layout.has_piece(spec.sheet):
		out.append(_sheet_sprite(spec.sheet, spec.frame, spec.anchor, false))
	for sprite in out:
		parent.add_child(sprite)
	return out


func _build_vignette() -> void:
	vignette = _cover()
	vignette.name = "Vignette"
	var material := ShaderMaterial.new()
	material.shader = _shader(VIGNETTE_SHADER)
	vignette.material = material
	vignette.visible = false
	add_child(vignette)


# Behind the player: under the Stage they stand on, over him and the void.
func _build_aura() -> void:
	aura = Node2D.new()
	aura.name = "Aura"
	aura.z_as_relative = false
	aura.z_index = -1
	aura.visible = false
	add_child(aura)
	if Layout.has_piece(staging.aura):
		aura_sprite = _sheet_sprite(staging.aura, Layout.FINAL_AURA.frame, Layout.FINAL_AURA.anchor, true)
		aura.add_child(aura_sprite)
		return
	aura_glow = _polygon(_ellipse(Layout.AURA_SIZE, 0.0), Layout.AURA_COLOR, true)
	aura.add_child(aura_glow)
	flames = _polygon(_ellipse(Layout.AURA_SIZE, 0.0), Layout.FLAME_COLOR, true)
	flames.visible = false
	aura.add_child(flames)


# An ellipse round the body, its top half pushed up by up to `flare` of its height in tongues.
func _ellipse(radii: Vector2, flare: float) -> PackedVector2Array:
	var points := PackedVector2Array()
	for i in CIRCLE_POINTS:
		var at := Vector2.from_angle(TAU * i / CIRCLE_POINTS) * radii
		if at.y < 0.0 and flare > 0.0 and i % 2 == 0:
			at.y -= randf_range(0.2, 1.0) * flare * radii.y
		points.append((at / Layout.TEXEL).round() * Layout.TEXEL)
	return points


func _build_overlay() -> void:
	overlay = Sprite2D.new()
	overlay.name = "PlayerOverlay"
	overlay.visible = false
	if final_player:
		overlay.texture = _texture(staging.sheet)
		overlay.hframes = Layout.FINAL_PLAYER_CELLS
	add_child(overlay)


func _build_debris() -> void:
	debris = _particles(Layout.DEBRIS[0], 1.4, Layout.DEBRIS_COLORS)
	debris.name = "Debris"
	debris.direction = Vector2.UP
	debris.spread = 20.0
	debris.initial_velocity_min = 20.0
	debris.initial_velocity_max = 70.0
	debris.gravity = Vector2(0, -40)
	debris.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	debris.emission_rect_extents = Vector2(150, 6)
	add_child(debris)


func _particles(amount: int, life: float, colors: Array) -> CPUParticles2D:
	var particles := CPUParticles2D.new()
	var dot := Image.create(1, 1, false, Image.FORMAT_RGBA8)
	dot.fill(Color.WHITE)
	particles.texture = ImageTexture.create_from_image(dot)
	particles.amount = amount
	particles.lifetime = life
	particles.scale_amount_min = Layout.TEXEL
	particles.scale_amount_max = Layout.TEXEL
	var ramp := Gradient.new()
	ramp.interpolation_mode = Gradient.GRADIENT_INTERPOLATE_CONSTANT
	ramp.offsets = PackedFloat32Array()
	ramp.colors = PackedColorArray()
	for i in colors.size():
		ramp.add_point(float(i) / colors.size(), colors[i])
	particles.color_initial_ramp = ramp
	particles.emitting = false
	return particles


# The stand-in's ash: the drawn sheets carry their own.
func _build_ash() -> void:
	var spec: Dictionary = Layout.ASH
	ash = _particles(spec.amount, spec.life, Layout.ASH_COLORS)
	ash.name = "Ash"
	ash.direction = Layout.beam_direction()
	ash.spread = spec.spread
	ash.initial_velocity_min = spec.speed.x
	ash.initial_velocity_max = spec.speed.y
	ash.gravity = Vector2(0, -spec.gravity)
	ash.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	ash.position = Layout.core()
	add_child(ash)


func _build_beam() -> void:
	beam = Node2D.new()
	beam.name = "Beam"
	beam.rotation = deg_to_rad(staging.angle)
	beam.visible = false
	add_child(beam)
	var start: Dictionary = Layout.FINAL_START
	var body: Dictionary = Layout.FINAL_BODY
	if Layout.has_piece(start.sheet) and Layout.has_piece(body.sheet):
		var glows := Layout.has_piece(start.glow) and Layout.has_piece(body.glow)
		if glows:
			start_sprites.append(_start_piece(start.glow, start.glow_frame, true))
			tile_sprites.append(_tile_run(body.glow, body.glow_frame, true))
		start_sprites.append(_start_piece(start.sheet, start.frame, false))
		tile_sprites.append(_tile_run(body.sheet, body.frame, false))
		if Layout.has_piece(body.spiral):
			tile_sprites.append(_tile_run(body.spiral, body.frame, true))
	else:
		for layer in Layout.BEAM_LAYERS:
			var shape := _polygon(PackedVector2Array(), layer.color, layer.add)
			beam.add_child(shape)
			beam_layers.append(shape)
	head_sprites = _glow_and_piece(Layout.FINAL_HEAD, beam)
	for sprite in head_sprites:
		sprite.hframes = 1
		sprite.region_enabled = true
	if head_sprites.is_empty():
		head_layers = _orb_layers(beam)
	muzzle_sprites = _glow_and_piece(Layout.FINAL_MUZZLE, beam)
	if muzzle_sprites.is_empty():
		muzzle_layers = _orb_layers(beam)


# The start piece, cropped to the travelled length while the beam is shorter than it.
func _start_piece(path: String, frame: Vector2, add: bool) -> Sprite2D:
	var sprite := Sprite2D.new()
	sprite.texture = _texture(path)
	sprite.centered = false
	sprite.region_enabled = true
	sprite.offset = Vector2(0, -frame.y / 2.0)
	sprite.set_meta(&"frame", frame)
	if add:
		sprite.material = _additive()
	beam.add_child(sprite)
	return sprite


# A run of body tiles from FINAL_BODY.from on, every frame its own texture so it can repeat along the beam.
func _tile_run(path: String, frame: Vector2, add: bool) -> Sprite2D:
	var tiles := _tiles(path, frame)
	var sprite := Sprite2D.new()
	sprite.texture = tiles[0] if not tiles.is_empty() else null
	sprite.set_meta(&"tiles", tiles)
	sprite.set_meta(&"frame", frame)
	sprite.centered = false
	sprite.region_enabled = true
	sprite.texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
	sprite.offset = Vector2(0, -frame.y / 2.0)
	sprite.position = Vector2(Layout.FINAL_BODY.from * Layout.TEXEL, 0)
	if add:
		sprite.material = _additive()
	beam.add_child(sprite)
	return sprite


func _tiles(path: String, frame: Vector2) -> Array[Texture2D]:
	var out: Array[Texture2D] = []
	var sheet := _texture(path)
	var image := sheet.get_image() if sheet != null else null
	if image == null or image.is_empty():
		return out
	if image.is_compressed():
		image.decompress()
	for i in roundi(image.get_width() / frame.x):
		out.append(ImageTexture.create_from_image(image.get_region(Rect2i(Vector2i(i * int(frame.x), 0), Vector2i(frame)))))
	return out


# The beam's head and its muzzle on the stand-in: its layers as discs.
func _orb_layers(parent: Node) -> Array[Polygon2D]:
	var out: Array[Polygon2D] = []
	for layer in Layout.BEAM_LAYERS:
		var disc := _polygon(_circle(1.0), layer.color, layer.add)
		parent.add_child(disc)
		out.append(disc)
	return out


func _build_ball() -> void:
	ball = Node2D.new()
	ball.name = "Ball"
	ball.visible = false
	add_child(ball)
	ball_sprites = _glow_and_piece(Layout.FINAL_BALL, ball)
	if ball_sprites.is_empty():
		var colors: Dictionary = Layout.BALL_COLORS
		for entry in [[colors.rim, false], [colors.mid, true], [colors.hot, false], [colors.core, false]]:
			var disc := _polygon(_circle(1.0), entry[0], entry[1])
			ball.add_child(disc)
			ball_layers.append(disc)
	fizzle = Node2D.new()
	fizzle.name = "Fizzle"
	fizzle.visible = false
	add_child(fizzle)
	fizzle_sprites = _glow_and_piece(Layout.FINAL_FIZZLE, fizzle)


func _build_arcs() -> void:
	for i in Layout.ARC_COUNT:
		var arc := Line2D.new()
		arc.width = Layout.TEXEL
		arc.default_color = Layout.ARC_COLOR
		arc.material = _additive()
		arc.visible = false
		add_child(arc)
		arcs.append(arc)


# A child of him, so it sits where his body does: the drawn end's sheets, or the stand-in's rays out of his core.
func _build_god_end() -> void:
	god_end = Node2D.new()
	god_end.name = "FinalBeamEnd"
	god_end.visible = false
	god.add_child(god_end)
	if final_god:
		for i in 3:
			var sprite := Sprite2D.new()
			sprite.centered = false
			sprite.scale = Vector2.ONE * GodLayout.GOD_SCALE
			if i == 1:
				sprite.material = _additive()
			god_end.add_child(sprite)
			god_end_sprites.append(sprite)
		return
	cracks = Node2D.new()
	cracks.name = "Cracks"
	god_end.add_child(cracks)
	var core := god.to_local(Layout.core())
	for i in Layout.CRACK_RAYS:
		var angle := TAU * (i + randf_range(-0.3, 0.3)) / Layout.CRACK_RAYS
		var length := randf_range(Layout.CRACK_LENGTH.x, Layout.CRACK_LENGTH.y)
		var points: Array[Vector2] = [core]
		for k in range(1, Layout.CRACK_FRAMES + 1):
			var along := Vector2.from_angle(angle) * length * k / Layout.CRACK_FRAMES
			var side := Vector2.from_angle(angle + PI / 2.0) * randf_range(-9.0, 9.0)
			points.append(((core + along + side) / GodLayout.GOD_SCALE).round() * GodLayout.GOD_SCALE)
		var ray := Line2D.new()
		ray.width = GodLayout.GOD_SCALE * 2.0
		ray.default_color = Layout.CRACK_COLOR
		ray.material = _additive()
		cracks.add_child(ray)
		crack_rays.append(ray)
		crack_points.append(points)


func _save_god() -> void:
	saved = {"material": god.body.material, "position": god.body.position, "visible": god.body.visible}
	if god.aura != null:
		saved["aura"] = god.aura.modulate
		saved["aura_visible"] = god.aura.visible
	var runes := _runes()
	if runes != null:
		saved["runes_alpha"] = runes.modulate.a
		saved["runes_scale"] = runes.scale


func _runes() -> CanvasItem:
	var void_layer: Node2D = god.layer(&"void")
	return void_layer.get_node_or_null(^"Runes") if void_layer != null else null


# MainPlayer's own punch at the frame its hitbox goes live: the stand-in's thrust.
func _contact_column() -> int:
	var animation: Animation = player.animation_player.get_animation(GodLayout.PUNCH_ANIM)
	var frames := animation.find_track(^"Sprite2D:frame_coords:x", Animation.TYPE_VALUE)
	var calls := -1
	for track in animation.get_track_count():
		if animation.track_get_type(track) == Animation.TYPE_METHOD:
			calls = track
	var at := animation.track_get_key_time(calls, 0) if calls >= 0 and animation.track_get_key_count(calls) > 0 else 0.0
	var column := 0
	for k in animation.track_get_key_count(frames):
		if animation.track_get_key_time(frames, k) <= at + 0.0001:
			column = int(animation.track_get_key_value(frames, k))
	return column


#THE PLAYER

# Drawn over the player, the overlay copying their sprite's transform so its 48x48 cells land on its 32x32 pixel for
# pixel; on the stand-in they are posed on their own sheet. Either way the real sprite holds its idle column under it,
# so showing it again at the end is seamless.
func stage_player() -> void:
	if player.hold_pose(GodLayout.PLAYER_SHEET):
		player.play_pose(GodLayout.BASE_POSE.frames, GodLayout.BASE_POSE.times, GodLayout.BASE_POSE.loop)
	overlay_on = final_player and overlay.texture != null
	overlay.visible = overlay_on
	overlay.frame = 0
	_follow_player()


func reveal_player() -> void:
	overlay_on = false
	overlay.visible = false
	if is_instance_valid(player):
		player.sprite.visible = true
		if player.hold_pose(GodLayout.PLAYER_SHEET):
			player.play_pose(GodLayout.BASE_POSE.frames, GodLayout.BASE_POSE.times, GodLayout.BASE_POSE.loop)


func pose(name_of: StringName) -> void:
	var spec: Dictionary = Layout.poses().get(name_of, {})
	if spec.is_empty():
		return
	pose_name = name_of
	if overlay_on:
		pose_spec = spec
		pose_step = 0
		pose_clock = 0.0
		overlay.frame = clampi(int(spec.frames[0]), 0, overlay.hframes - 1)
		return
	var frames: Array = spec.frames.map(func(column: int) -> int: return contact_column if column == Layout.CONTACT else column)
	if player.hold_pose(GodLayout.PLAYER_SHEET):
		player.play_pose(frames, spec.times if not spec.times.is_empty() else [Layout.at_bars(Layout.CHARGE_FRAME_TIMES, bars)],
			spec.loop)


# A one-shot pose's length.
func pose_length(name_of: StringName) -> float:
	var spec: Dictionary = Layout.poses().get(name_of, {})
	var total := 0.0
	for time in spec.get("times", []):
		total += float(time)
	return total


func _step_pose(delta: float) -> void:
	if pose_spec.is_empty():
		return
	pose_clock += delta
	var frames: Array = pose_spec.frames
	while pose_clock >= _pose_time(pose_step) and (pose_spec.loop or pose_step < frames.size() - 1):
		pose_clock -= _pose_time(pose_step)
		pose_step = (pose_step + 1) % frames.size()
	overlay.frame = clampi(int(frames[pose_step]), 0, overlay.hframes - 1)


func _pose_time(step: int) -> float:
	var times: Array = pose_spec.times
	if times.is_empty():
		return Layout.at_bars(Layout.CHARGE_FRAME_TIMES, bars)
	return maxf(float(times[mini(step, times.size() - 1)]), 0.001)


func _follow_player() -> void:
	if not overlay_on or not is_instance_valid(player):
		return
	var sprite: Sprite2D = player.sprite
	overlay.global_transform = sprite.global_transform
	overlay.offset = sprite.offset
	overlay.centered = sprite.centered
	sprite.visible = false


func ball_point() -> Vector2:
	return player.global_position + Layout.cell_offset(staging.ball)


func muzzle_point() -> Vector2:
	return player.global_position + Layout.cell_offset(staging.muzzle)


#THE CHARGE

func begin_charge() -> void:
	charging = true
	ball.visible = true
	ball.scale = Vector2.ONE
	ball.modulate.a = 1.0
	set_bars(0)


# Everything that escalates with the bars banked.
func set_bars(count: int) -> void:
	bars = count
	ball_size = clampi(count, 0, Layout.BALL_RADII.size() - 1)
	vignette_strength = Layout.at_bars(Layout.VIGNETTE, count)
	vignette_radius = Layout.at_bars(Layout.LIGHT_RADIUS, count)
	vignette.visible = charging
	aura.visible = charging and count >= Layout.AURA_FROM
	if flames != null:
		flames.visible = count >= Layout.FLAMES_FROM
	if charging and count >= Layout.DEBRIS_FROM:
		var amount: int = Layout.DEBRIS[0] if count < Layout.ARCS_FROM else Layout.DEBRIS[1]
		if debris.amount != amount:
			debris.amount = amount
		debris.emitting = true
	god_jitter = charging and count >= Layout.ARCS_FROM
	if not god_jitter:
		calm_god()


# The bank's ring off the ball.
func bank_burst() -> void:
	var radius: float = Layout.at_bars(Layout.BALL_RADII, ball_size) * Layout.TEXEL
	_ring(ball_point(), radius, radius + 72.0, Layout.BALL_COLORS.hot, 0.2, false)


# The charge giving out at `at`: the drawn fizzle from `first`, or the stand-in ball popping.
func fizzle_at(at: Vector2, first: int) -> void:
	end_charge()
	if not fizzle_sprites.is_empty():
		ball.visible = false
		fizzle.position = at
		fizzle.visible = true
		var spec: Dictionary = Layout.FINAL_FIZZLE
		var play := fizzle.create_tween()
		for i in range(first, spec.frames):
			play.tween_callback(_show_fizzle.bind(i))
			play.tween_interval(spec.time)
		play.tween_callback(fizzle.hide)
		return
	ball.position = at
	var pop := ball.create_tween()
	pop.tween_property(ball, "scale", Vector2.ONE * 1.6, Layout.POP_TIME)
	pop.parallel().tween_property(ball, "modulate:a", 0.0, Layout.POP_TIME)
	pop.tween_callback(ball.hide)


func _show_fizzle(frame: int) -> void:
	for sprite in fizzle_sprites:
		sprite.frame = frame


# A ring growing from `from` to `to` px round `at` and fading, over `seconds` (real ones when `real`).
func _ring(at: Vector2, from: float, to: float, color: Color, seconds: float, real: bool, width := 9.0) -> void:
	var ring := Line2D.new()
	ring.points = _circle(1.0)
	ring.closed = true
	ring.width = width / maxf(from, 1.0)
	ring.default_color = color
	ring.material = _additive()
	ring.position = at
	ring.scale = Vector2.ONE * from
	impact.add_child(ring)
	var grow := ring.create_tween().set_ignore_time_scale(real).set_parallel(true)
	grow.tween_property(ring, "scale", Vector2.ONE * to, seconds).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	grow.tween_property(ring, "width", 0.0, seconds)
	grow.tween_property(ring, "modulate:a", 0.0, seconds)
	grow.chain().tween_callback(ring.queue_free)


func end_charge() -> void:
	charging = false
	god_jitter = false
	calm_god()
	debris.emitting = false
	aura.visible = false
	vignette.visible = false
	for arc in arcs:
		arc.visible = false


func _step_charge(delta: float) -> void:
	if not charging:
		return
	var point := ball_point()
	ball.position = point
	var pulse := 1.0 if int(clock * Layout.BALL_PULSE_HZ * 2.0) % 2 == 0 else 0.0
	var radius: float = (Layout.at_bars(Layout.BALL_RADII, ball_size) + pulse) * Layout.TEXEL
	var shares := [1.0, 0.82, 0.6, 0.35]
	for i in ball_layers.size():
		ball_layers[i].scale = Vector2.ONE * maxf(roundf(radius * shares[i] / Layout.TEXEL), 1.0) * Layout.TEXEL
	if not ball_sprites.is_empty():
		var spec: Dictionary = Layout.FINAL_BALL
		ball.visible = bars >= 1
		var row := clampi(bars - 1, 0, int(spec.rows) - 1)
		for sprite in ball_sprites:
			sprite.frame = row * int(spec.frames) + int(clock / spec.time) % int(spec.frames)
	var material := vignette.material as ShaderMaterial
	material.set_shader_parameter("center", to_local(point))
	material.set_shader_parameter("radius", vignette_radius)
	material.set_shader_parameter("softness", Layout.VIGNETTE_SOFTNESS)
	material.set_shader_parameter("strength", vignette_strength)
	material.set_shader_parameter("bands", Layout.VIGNETTE_BANDS)
	material.set_shader_parameter("texel", Layout.TEXEL)
	aura.position = player.global_position
	if aura_sprite != null:
		var row_by_bars: Array = Layout.FINAL_AURA.row_by_bars
		var column := clampi(overlay.frame - 2, 0, 2) if overlay_on and pose_name == &"charge" else 0
		aura_sprite.frame = int(row_by_bars[clampi(bars - 1, 0, row_by_bars.size() - 1)]) * Layout.FINAL_AURA.frames + column
	debris.position = player.global_position + Vector2(0, GodLayout.SOLES_BELOW_ORIGIN)
	flicker_left -= delta
	arc_left -= delta
	if flicker_left <= 0.0:
		flicker_left = Layout.ARC_EVERY
		_flicker()
	if arc_left <= 0.0 and bars >= Layout.ARCS_FROM and ball_sprites.is_empty():
		arc_left = Layout.ARC_EVERY
		_spark_arcs(point, radius)


func _flicker() -> void:
	if aura_glow != null:
		aura_glow.modulate.a = randf_range(0.5, 1.0)
	if flames != null and flames.visible:
		flames.polygon = _ellipse(Layout.AURA_SIZE * 1.15, 0.5 if bars < Layout.ARCS_FROM else 0.8)
	if god_jitter:
		var step: float = Layout.GOD_JITTER * GodLayout.GOD_SCALE
		god.body.position = saved.position + Vector2(randi_range(-1, 1), randi_range(-1, 1)) * step
		if god.aura != null:
			god.aura.modulate.a = randf_range(Layout.GOD_AURA_FLICKER.x, Layout.GOD_AURA_FLICKER.y)


func _spark_arcs(from: Vector2, radius: float) -> void:
	for arc in arcs:
		var angle := randf() * TAU
		var length := randf_range(Layout.ARC_LENGTH.x, Layout.ARC_LENGTH.y)
		var points := PackedVector2Array()
		var segments := 5
		for k in segments + 1:
			var along := Vector2.from_angle(angle) * (radius + length * k / segments)
			var side := Vector2.from_angle(angle + PI / 2.0) * (randf_range(-10.0, 10.0) if 0 < k and k < segments else 0.0)
			points.append(((from + along + side) / Layout.TEXEL).round() * Layout.TEXEL)
		arc.points = points
		arc.visible = true


# His jitter and his aura's flicker let go.
func calm_god() -> void:
	if not is_instance_valid(god) or saved.is_empty():
		return
	god.body.position = saved.position
	if god.aura != null and saved.has("aura"):
		god.aura.modulate.a = saved.aura.a


#THE BEAM

# The muzzle flashes open, and the beam leaves it MUZZLE_OPEN later at `width` of its thickness, its head reaching his
# core in `travel`. Its tween.
func fire(width: float, travel: float) -> Tween:
	end_charge()
	ball.visible = false
	beam_width = width
	beam_fade = 1.0
	sputtering = false
	beam_clock = 0.0
	beam_full = Layout.beam_length(muzzle_point())
	beam_length = 0.0
	beam.visible = true
	_step_beam()
	var reach := create_tween()
	reach.tween_interval(Layout.MUZZLE_OPEN)
	reach.tween_property(self, "beam_length", beam_full, maxf(travel, 0.001))
	return reach


# Once he is gone: the tip carries on off the screen, then the whole beam thins out.
func punch_through() -> Tween:
	var spec: Dictionary = Layout.PUNCH_THROUGH
	var past := create_tween()
	past.tween_property(self, "beam_length", beam_full + spec.speed * spec.time, spec.time)
	_kill_width()
	width_tween = create_tween()
	width_tween.tween_interval(spec.time)
	width_tween.tween_property(self, "beam_width", 0.0, Layout.BODY_FADE)
	width_tween.parallel().tween_property(self, "beam_fade", Layout.BODY_FADE_ALPHA, Layout.BODY_FADE)
	width_tween.tween_callback(beam.hide)
	width_tween.tween_callback(_end_impact)
	return width_tween


# A weak beam giving out: its width flickering down to nothing, and the drawn fizzle at the hands.
func sputter(seconds: float) -> void:
	sputtering = true
	_kill_width()
	width_tween = create_tween()
	width_tween.tween_property(self, "beam_width", 0.0, seconds)
	width_tween.tween_callback(beam.hide)
	width_tween.tween_callback(_end_impact)
	width_tween.tween_callback(func() -> void:
		if not fizzle_sprites.is_empty():
			fizzle_at(muzzle_point(), 2)
	)


func _kill_width() -> void:
	if width_tween != null and width_tween.is_valid():
		width_tween.kill()


func _step_beam(delta := 0.0) -> void:
	if not beam.visible:
		return
	beam_clock += delta
	beam.position = muzzle_point()
	beam.modulate.a = beam_fade
	var wobble: Dictionary = Layout.BEAM_WOBBLE
	var width := beam_width * (randf_range(0.6, 1.1) if sputtering else 1.0)
	var length := beam_length
	for i in beam_layers.size():
		var half: float = Layout.BEAM_LAYERS[i].half * width * (1.0 + wobble.amount * sin(clock * TAU * wobble.hz + i))
		beam_layers[i].polygon = PackedVector2Array([Vector2(0, -half), Vector2(length, -half), Vector2(length, half),
			Vector2(0, half)])
	for i in head_layers.size():
		head_layers[i].position = Vector2(length, 0)
		head_layers[i].scale = Vector2.ONE * maxf(Layout.BEAM_LAYERS[i].half * width * Layout.BEAM_HEAD_RADIUS, 0.001)
		head_layers[i].visible = length > 0.0
	for i in muzzle_layers.size():
		muzzle_layers[i].scale = Vector2.ONE * maxf(Layout.BEAM_LAYERS[i].half * maxf(width, 0.3) * Layout.MUZZLE_FLARE * 0.5, 0.001)
	var step := int(beam_clock / Layout.FINAL_BODY.time)
	var texels := length / Layout.TEXEL
	var thick := Vector2(Layout.TEXEL, Layout.TEXEL * maxf(width, 0.001))
	var cut := clampf(ceilf(texels), 0.0, Layout.FINAL_START.frame.x)
	for sprite in start_sprites:
		var frame: Vector2 = sprite.get_meta(&"frame")
		sprite.region_rect = Rect2((step % Layout.FINAL_START.frames) * frame.x, 0, cut, frame.y)
		sprite.scale = thick
		sprite.visible = cut >= 1.0 and (sprite.material == null or texels >= Layout.FINAL_START.frame.x)
	var body: Dictionary = Layout.FINAL_BODY
	var tiles := maxi(ceili((texels - body.short_of_tip - body.from) / body.frame.x), 0)
	for sprite in tile_sprites:
		var run: Array = sprite.get_meta(&"tiles")
		var frame: Vector2 = sprite.get_meta(&"frame")
		if not run.is_empty():
			sprite.texture = run[step % run.size()]
		sprite.region_rect = Rect2(0, 0, tiles * frame.x, frame.y)
		sprite.scale = thick
		sprite.visible = tiles > 0
	# The head's cell carries a stretch of body behind its sphere, cut flat: while the beam is shorter than that, it is
	# cropped at the hands, as the start piece is, so it never shows behind the player. Its glow fades out on its own.
	var head: Dictionary = Layout.FINAL_HEAD
	var tail := clampf(head.anchor.x - texels / maxf(width, 0.001), 0.0, head.anchor.x)
	for sprite in head_sprites:
		var cut_tail := tail if sprite.material == null else 0.0
		sprite.position = Vector2(length, 0)
		sprite.scale = Vector2.ONE * Layout.TEXEL * maxf(width, 0.001)
		sprite.region_rect = Rect2((step % head.frames) * head.frame.x + cut_tail, 0, head.frame.x - cut_tail, head.frame.y)
		sprite.offset = -head.anchor + Vector2(cut_tail, 0)
		sprite.visible = length > 0.0
	var muzzle: Dictionary = Layout.FINAL_MUZZLE
	var muzzle_step := int(beam_clock / muzzle.time)
	var opening: Array = muzzle.open
	var looping: Array = muzzle.loop
	var muzzle_frame: int = opening[muzzle_step] if muzzle_step < opening.size() else looping[(muzzle_step - opening.size()) % looping.size()]
	for sprite in muzzle_sprites:
		sprite.frame = muzzle_frame


#THE IMPACT

# On his core: the flash (white then cyan, real seconds, so it plays through the hit-stop), the shockwave, and the
# drawn impact held on him while the beam is (or the stand-in's burst). A weak beam's is softer.
func impact_at_core(full: bool) -> void:
	var core := Layout.core()
	var spec: Dictionary = Layout.IMPACT_FLASH
	_kill_flash()
	flash_cover.visible = true
	flash_tween = create_tween().set_ignore_time_scale(true)
	if full:
		flash_cover.color = Layout.FLASH_COLORS.white
		flash_tween.tween_interval(spec.white)
	var cyan: Color = Layout.FLASH_COLORS.cyan
	cyan.a = spec.cyan_alpha * (1.0 if full else 0.5)
	flash_tween.tween_callback(func() -> void: flash_cover.color = cyan)
	flash_tween.tween_interval(spec.cyan)
	flash_tween.tween_property(flash_cover, "color:a", 0.0, spec.fade)
	flash_tween.tween_callback(flash_cover.hide)
	var wave: Dictionary = Layout.SHOCKWAVE
	var size := 1.0 if full else 0.5
	_ring(core, wave.from, wave.to * size, Layout.IMPACT_COLOR, wave.time, true, wave.width)
	impact_sprites = _glow_and_piece(Layout.FINAL_IMPACT, impact)
	if not impact_sprites.is_empty():
		for sprite in impact_sprites:
			sprite.position = core
		impact_clock = 0.0 if full else Layout.FINAL_IMPACT.open.size() * Layout.FINAL_IMPACT.time
		_step_impact(0.0)
		return
	var burst := _polygon(_circle(1.0), Layout.IMPACT_COLOR, true)
	burst.position = core
	burst.scale = Vector2.ONE * 40.0 * size
	impact.add_child(burst)
	var grow := burst.create_tween().set_parallel(true)
	grow.tween_property(burst, "scale", Vector2.ONE * 150.0 * size, 0.3).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	grow.tween_property(burst, "modulate:a", 0.0, 0.3)
	grow.chain().tween_callback(burst.queue_free)


func _step_impact(delta: float) -> void:
	if impact_clock < 0.0:
		return
	impact_clock += delta
	var spec: Dictionary = Layout.FINAL_IMPACT
	var step := int(impact_clock / spec.time)
	var opening: Array = spec.open
	var looping: Array = spec.loop
	var frame: int = opening[step] if step < opening.size() else looping[(step - opening.size()) % looping.size()]
	for sprite in impact_sprites:
		if is_instance_valid(sprite):
			sprite.frame = frame


func _end_impact() -> void:
	impact_clock = -1.0
	for sprite in impact_sprites:
		if is_instance_valid(sprite):
			sprite.queue_free()
	impact_sprites.clear()


# The release's two white frames, real seconds.
func release_flash() -> void:
	_flash(Layout.FLASH_COLORS.white, Layout.RELEASE_FLASH)


# A cover of `color` for `seconds`, real ones.
func _flash(color: Color, seconds: float) -> void:
	_kill_flash()
	flash_cover.color = color
	flash_cover.visible = true
	flash_tween = create_tween().set_ignore_time_scale(true)
	flash_tween.tween_interval(seconds)
	flash_tween.tween_callback(flash_cover.hide)


# The stage's cut: white in, a hold, and out. Its tween.
func white_cut(spec: Dictionary) -> Tween:
	_kill_flash()
	flash_cover.color = Color(1, 1, 1, 0)
	flash_cover.visible = true
	flash_tween = create_tween()
	flash_tween.tween_property(flash_cover, "color:a", 1.0, spec.white_in)
	flash_tween.tween_interval(spec.white_hold)
	flash_tween.tween_property(flash_cover, "color:a", 0.0, spec.white_out)
	flash_tween.tween_callback(flash_cover.hide)
	return flash_tween


func _kill_flash() -> void:
	if flash_tween != null and flash_tween.is_valid():
		flash_tween.kill()


#HIS END

# The beam lands on him: the drawn disintegration (`success`) or reform takes his body's place, his aura off; on the
# stand-in, the radial dissolve goes on his body.
func begin_end(success: bool) -> void:
	god_end.visible = true
	god_end.position = saved.position
	if not final_god:
		_apply_dissolve()
		return
	var sheet: Dictionary = Layout.FINAL_DISINTEGRATE if success else Layout.FINAL_REFORM
	var ash_path: String = staging.disintegrate_ash if success else staging.reform_ash
	var parts := [[sheet.sheet, sheet.frame, sheet.anchor], [sheet.glow, sheet.frame, sheet.anchor],
		[ash_path, sheet.ash_frame, sheet.ash_anchor]]
	for i in parts.size():
		var sprite := god_end_sprites[i]
		sprite.texture = _texture(parts[i][0])
		sprite.visible = sprite.texture != null
		if sprite.texture == null:
			continue
		sprite.hframes = maxi(roundi(sprite.texture.get_width() / parts[i][1].x), 1)
		sprite.offset = -parts[i][2]
		sprite.frame = 0
	god.body.visible = false
	if god.aura != null:
		god.aura.visible = false
	_show_god_frame(0)


func _show_god_frame(frame: int) -> void:
	for sprite in god_end_sprites:
		if sprite.texture != null:
			sprite.frame = clampi(frame, 0, sprite.hframes - 1)


# His success: from where it is to gone over `seconds`. Its tween.
func dissolve(seconds: float) -> Tween:
	core_popped = false
	ash.emitting = not final_god
	return _drive(_dissolve_step, progress, 1.0, seconds)


# His runes going with him.
func fade_runes() -> void:
	var runes := _runes()
	if runes == null or not saved.has("runes_alpha"):
		return
	runes_tween = runes.create_tween().set_parallel(true)
	runes_tween.tween_property(runes, "modulate:a", 0.0, Layout.RUNES_FADE)
	runes_tween.tween_property(runes, "scale", saved.runes_scale * Layout.RUNES_GROW, Layout.DISSOLVE_TIME)


func _dissolve_step(value: float) -> void:
	_set_progress(value)
	if not final_god:
		return
	var spec: Dictionary = Layout.FINAL_DISINTEGRATE
	_show_god_frame(mini(int(value * spec.frames), spec.frames - 1))
	if not core_popped and value >= Layout.CORE_POP:
		core_popped = true
		var pop: Color = Layout.FLASH_COLORS.white
		pop.a = Layout.CORE_POP_FLASH.alpha
		_flash(pop, Layout.CORE_POP_FLASH.time)


# A weak beam: he comes apart as far as `reached` (FAIL_DISSOLVE's tau) and holds there. Its tween.
func come_apart(reached: float, seconds: float) -> Tween:
	ash.emitting = not final_god
	if not final_god:
		return _drive(_set_progress, progress, reached, seconds)
	var frames: Vector2i = Layout.reform_frames(reached)
	return _drive(_reform_step, 0.0, float(frames.x) + 0.999, (frames.x + 1) * Layout.FINAL_REFORM.time)


# And pulls himself back together: the drawn red reform from the first frame at or under where he got to, or the
# stand-in's dissolve run back with his aura flaring. How long it takes.
func reform(reached: float) -> float:
	ash.emitting = false
	if not final_god:
		aura_flare = Layout.AURA_FLARE
		var flare := create_tween()
		flare.tween_property(self, "aura_flare", 1.0, Layout.REFORM_TIME)
		_drive(_set_progress, progress, 0.0, Layout.REFORM_TIME)
		return Layout.REFORM_TIME
	var frames: Vector2i = Layout.reform_frames(reached)
	var last: int = Layout.FINAL_REFORM.frames - 1
	var seconds: float = (last - frames.y + 1) * Layout.FINAL_REFORM.time
	var back := _drive(_reform_step, float(frames.y), float(last) + 0.999, seconds)
	back.tween_callback(func() -> void:
		restore_god()
		_flash(Layout.REFORM_FLASH.color, Layout.REFORM_FLASH.time)
	)
	return seconds


func _reform_step(frame: float) -> void:
	var index := clampi(int(frame), 0, Layout.FINAL_REFORM.frames - 1)
	_show_god_frame(index)
	progress = Layout.FINAL_REFORM.taus[index]


func _drive(step: Callable, from: float, to: float, seconds: float) -> Tween:
	if dissolve_tween != null and dissolve_tween.is_valid():
		dissolve_tween.kill()
	dissolve_tween = create_tween()
	dissolve_tween.tween_method(step, from, to, maxf(seconds, 0.001))
	dissolve_tween.tween_callback(func() -> void: ash.emitting = false)
	return dissolve_tween


func _set_progress(value: float) -> void:
	progress = value
	for material in dissolve_materials:
		material.set_shader_parameter("progress", value)
		material.set_shader_parameter("frame_size", _frame_size())
	for i in crack_rays.size():
		var points: Array = crack_points[i]
		var shown := clampi(int(ceil(value * Layout.CRACK_FRAMES)) + 1, 0, points.size()) if value > 0.0 else 0
		crack_rays[i].points = PackedVector2Array(points.slice(0, shown))
		crack_rays[i].modulate.a = 1.0 - smoothstep(0.7, 1.0, value)
	if not final_god and god.aura != null and saved.has("aura"):
		var tint: Color = saved.aura
		var left := 1.0 - clampf(value / (Layout.AURA_FADE / Layout.DISSOLVE_TIME), 0.0, 1.0)
		god.aura.modulate = Color(tint.r * aura_flare, tint.g * aura_flare, tint.b * aura_flare, tint.a * left)
	ash.emission_rect_extents = Vector2(GodLayout.FRAME * GodLayout.GOD_SCALE / 2.0) * maxf(value, 0.08)


func _frame_size() -> Vector2:
	var body: Sprite2D = god.body
	if body.texture == null:
		return Vector2.ONE
	return Vector2(body.texture.get_width() / float(body.hframes), body.texture.get_height() / float(body.vframes))


func _apply_dissolve() -> void:
	if not dissolve_materials.is_empty():
		return
	var body: Sprite2D = god.body
	var material := ShaderMaterial.new()
	material.shader = _shader(DISSOLVE_SHADER % "blend_mix")
	var texel := body.to_local(Layout.core()) - body.get_rect().position
	var frame := _frame_size()
	var reach := 0.0
	for corner in [Vector2.ZERO, Vector2(frame.x, 0), Vector2(0, frame.y), frame]:
		reach = maxf(reach, texel.distance_to(corner))
	material.set_shader_parameter("impact", texel)
	material.set_shader_parameter("reach", reach)
	material.set_shader_parameter("frame_size", frame)
	material.set_shader_parameter("sweep", Layout.DISSOLVE_SWEEP)
	material.set_shader_parameter("edge", Layout.DISSOLVE_EDGE)
	material.set_shader_parameter("edge_hot", Layout.DISSOLVE_EDGE_COLORS[0])
	material.set_shader_parameter("edge_cool", Layout.DISSOLVE_EDGE_COLORS[1])
	material.set_shader_parameter("progress", progress)
	dissolve_materials.append(material)
	body.material = material


# He is gone: whatever of him is still drawn is hidden, the drawn sheet left on its last frame of ash.
func hide_god() -> void:
	god.body.visible = false
	if god.aura != null:
		god.aura.visible = false
	if cracks != null:
		cracks.visible = false


# Everything of his this put on him, put back: the fail path's end, and release().
func restore_god() -> void:
	if not is_instance_valid(god) or saved.is_empty():
		return
	if dissolve_tween != null and dissolve_tween.is_valid():
		dissolve_tween.kill()
	if runes_tween != null and runes_tween.is_valid():
		runes_tween.kill()
	aura_flare = 1.0
	progress = 0.0
	god.body.material = saved.material
	god.body.position = saved.position
	god.body.visible = saved.visible
	if god.aura != null and saved.has("aura"):
		god.aura.modulate = saved.aura
		god.aura.visible = saved.aura_visible
	var runes := _runes()
	if runes != null and saved.has("runes_alpha"):
		runes.modulate.a = saved.runes_alpha
		runes.scale = saved.runes_scale
	dissolve_materials.clear()
	if is_instance_valid(god_end):
		god_end.visible = false
	ash.emitting = false


#EVERY FRAME

func _process(delta: float) -> void:
	clock += delta
	_follow_player()
	if overlay_on:
		_step_pose(delta)
	_step_charge(delta)
	_step_beam(delta)
	_step_impact(delta)
	if not final_god and aura_flare != 1.0:
		_set_progress(progress)


func _exit_tree() -> void:
	if is_instance_valid(god_end):
		god_end.queue_free()
