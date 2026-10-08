extends Node2D

# The rift that opens in the void's floor under a puppet as Jordan drags it up through it, and again as he drags it
# back down (JordanCombo's summon and recall). It sits on the Floor layer, its anchor on the puppet's feet.
#
# The drawn one (approved 2026-09-28, JordanGodLayout.RIFTS): three synced layers - back behind the puppet, here on the
# floor; front and an additive glow over it, on the Stage a pixel below the feet so they y-sort in front of the puppet
# and behind anyone further down. open() plays a sequence up to its `hold` frames and loops them for as long as the
# puppet is on its way; close() plays it out, and it is gone. The puppet is clipped at the anchor row while it is in
# (JordanPuppet.set_clipped). Until it is in: an ellipse with embers, grown in and shrunk away.

const Layout := preload("res://Scripts/JordanGodLayout.gd")

# The front's y-sort point under the feet, and the offset that draws it back where the back is drawn.
const FRONT_SORT_PX := 1.0

var profile := &"standard"
var radius := 80.0
var stage: Node2D
var drawn := false
var sprites := {}
var front: Node2D
var sequence := &""
var step := 0
var clock := 0.0
var closing := false
var embers: CPUParticles2D
var grow: Tween


func setup(rift_profile: StringName, rift_radius: float, stage_layer: Node2D) -> void:
	profile = rift_profile
	radius = rift_radius
	stage = stage_layer


func _ready() -> void:
	drawn = Layout.final_rift(profile)
	if drawn:
		_build_drawn()
	else:
		_build_placeholder()


func _exit_tree() -> void:
	if is_instance_valid(front):
		front.queue_free()


# `rift_sequence` is &"summon" or &"despawn".
func open(rift_sequence := &"summon") -> void:
	closing = false
	if not drawn:
		embers.emitting = true
		if grow != null and grow.is_valid():
			grow.kill()
		grow = create_tween()
		grow.tween_property(self, "scale", Vector2.ONE, Layout.PLACEHOLDER_RIFT.open_time) \
			.set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
		return
	sequence = rift_sequence
	for layer in Layout.RIFT_LAYERS:
		var sheet: Sprite2D = sprites[layer]
		sheet.texture = load(Layout.rift_sheet(profile, sequence, layer))
		sheet.hframes = Layout.RIFT_SEQUENCES[sequence].times.size()
	step = 0
	clock = 0.0
	_show_step()


# Played out and gone. The seconds it takes.
func close() -> float:
	closing = true
	if not drawn:
		embers.emitting = false
		if grow != null and grow.is_valid():
			grow.kill()
		var seconds: float = Layout.PLACEHOLDER_RIFT.close_time
		grow = create_tween().set_parallel()
		grow.tween_property(self, "scale", Vector2(0.05, 0.05), seconds).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
		grow.tween_property(self, "modulate:a", 0.0, seconds)
		grow.chain().tween_callback(queue_free)
		return seconds
	# What is left of the step showing, then every step after it once each: closing, the hold no longer loops.
	var spec: Dictionary = Layout.RIFT_SEQUENCES.get(sequence, Layout.RIFT_SEQUENCES[&"summon"])
	var left := maxf(float(spec.times[step]) - clock, 0.0)
	for i in range(step + 1, spec.times.size()):
		left += float(spec.times[i])
	return left


func _process(delta: float) -> void:
	if not drawn or sequence == &"":
		return
	var spec: Dictionary = Layout.RIFT_SEQUENCES[sequence]
	var times: Array = spec.times
	var hold: Array = spec.hold
	clock += delta
	while clock >= float(times[step]):
		clock -= float(times[step])
		if not closing and step == int(hold[-1]):
			step = int(hold[0])
		elif step < times.size() - 1:
			step += 1
		else:
			queue_free()
			return
		_show_step()


func _show_step() -> void:
	for layer in Layout.RIFT_LAYERS:
		sprites[layer].frame = step


func _build_drawn() -> void:
	var spec: Dictionary = Layout.RIFTS[profile]
	# The anchor texel's row stands with its bottom edge on the feet, as a puppet's soles do.
	var offset: Vector2 = -spec.anchor - Vector2(0.0, 1.0)
	front = Node2D.new()
	front.name = "RiftFront"
	for layer in Layout.RIFT_LAYERS:
		var sheet := Sprite2D.new()
		sheet.name = String(layer).capitalize()
		sheet.centered = false
		sheet.scale = Vector2.ONE * Layout.SCALE
		sheet.offset = offset
		if layer == &"back":
			add_child(sheet)
		else:
			sheet.offset.y -= FRONT_SORT_PX / Layout.SCALE
			front.add_child(sheet)
		if layer == &"glow":
			var added := CanvasItemMaterial.new()
			added.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
			sheet.material = added
		sprites[layer] = sheet
	if is_instance_valid(stage):
		stage.add_child(front)
		front.global_position = global_position + Vector2(0.0, FRONT_SORT_PX)
	else:
		add_child(front)


func _build_placeholder() -> void:
	var spec: Dictionary = Layout.PLACEHOLDER_RIFT
	var radii := Vector2(radius, radius * spec.height_ratio)
	var glow := Polygon2D.new()
	glow.polygon = _ellipse(radii * 1.25, spec.points)
	glow.color = spec.glow
	add_child(glow)
	var depth := Polygon2D.new()
	depth.polygon = _ellipse(radii, spec.points)
	depth.color = spec.depth
	add_child(depth)
	var rim := Line2D.new()
	rim.points = _ellipse(radii, spec.points)
	rim.closed = true
	rim.width = spec.rim_width
	rim.default_color = spec.rim
	add_child(rim)
	embers = CPUParticles2D.new()
	embers.amount = spec.embers
	embers.lifetime = 0.9
	embers.emitting = false
	embers.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	embers.emission_rect_extents = Vector2(radii.x * 0.8, radii.y * 0.5)
	embers.direction = Vector2.UP
	embers.spread = 25.0
	embers.gravity = Vector2(0, -40)
	embers.initial_velocity_min = spec.ember_speed.x
	embers.initial_velocity_max = spec.ember_speed.y
	embers.scale_amount_min = Layout.SCALE
	embers.scale_amount_max = Layout.SCALE
	embers.color = spec.ember_color
	var dot := Image.create(1, 1, false, Image.FORMAT_RGBA8)
	dot.fill(Color.WHITE)
	embers.texture = ImageTexture.create_from_image(dot)
	add_child(embers)
	scale = Vector2(0.05, 0.05)


func _ellipse(radii: Vector2, points: int) -> PackedVector2Array:
	var out := PackedVector2Array()
	for i in points:
		out.append(Vector2.from_angle(TAU * i / points) * radii)
	return out
