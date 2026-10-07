extends Node2D

# One of Josh's portals in Jordan's attack 3 (JordanComboPortals): a spike's, which Eric's greatsword shoots up out of;
# a body portal, which takes Eric under the floor at one spot and out of another; the sword's, which his greatsword
# stands plunged in. It lies on the Floor layer, its anchor on its floor point, and plays on game time, a physics step
# at a time: open() into its loop, burst() (the spike's blade, the sword's plunge) back into it, suck() (the spike's
# blade going down), close(), and it is gone.
#
# The drawn one (JordanPortalsLayout.PORTALS, once every sheet of its kind is in and imported): three synced layers,
# back here on the floor, front and an additive glow on the Stage a pixel below the anchor so they y-sort in front of
# whatever stands in it, as JordanRift's do. Until then JordanRift's placeholder in rune blue, grown in and shrunk away.

const Layout := preload("res://Scripts/JordanPortalsLayout.gd")

# The front's y-sort point under the anchor, and the offset that draws it back where the back is drawn.
const FRONT_SORT_PX := 1.0

var kind := &"spike"
var stage: Node2D
var drawn := false
var sprites := {}
var front: Node2D
var sequence := &""
var step := 0
var clock := 0.0
var speed := 1.0
# On the last frame of a sequence that doesn't go on (the spike's suck), until close().
var held := false
var closing := false
var rim: Line2D
var flecks: CPUParticles2D
var grow: Tween
var flare: Tween


static func make(portal_kind: StringName, stage_layer: Node2D) -> Node2D:
	var portal = new()
	portal.kind = portal_kind
	portal.stage = stage_layer
	portal.name = "Portal_%s" % portal_kind
	return portal


func _ready() -> void:
	drawn = Layout.final_portal(kind)
	if drawn:
		_build_drawn()
	else:
		_build_placeholder()


func _exit_tree() -> void:
	if is_instance_valid(front):
		front.queue_free()


# Open, then its loop; `fast` at twice the speed (a feint's entry). The seconds the opening takes.
func open(fast := false) -> float:
	closing = false
	_play(&"open")
	speed = 2.0 if fast else 1.0
	var seconds := Layout.sequence_time(kind, &"open") / speed
	if not drawn:
		flecks.emitting = true
		_grow_in(Layout.SPIKE_READABLE if kind == &"spike" else seconds)
	return seconds


func burst() -> void:
	if closing or not Layout.PORTAL_BURSTS.has(kind):
		return
	_play(Layout.PORTAL_BURSTS[kind])
	if not drawn:
		_flare()


func suck() -> void:
	if closing or not Layout.PORTAL_SEQUENCES[kind].has(&"suck"):
		return
	_play(&"suck")


# Played out and gone. The seconds that takes.
func close() -> float:
	if closing:
		return _left()
	closing = true
	_play(&"close")
	var seconds := Layout.sequence_time(kind, &"close")
	if not drawn:
		flecks.emitting = false
		_shrink_away(seconds)
	return seconds


# The opening's radii, px.
func opening() -> Vector2:
	return Layout.opening(kind)


func _physics_process(delta: float) -> void:
	if sequence == &"" or held:
		return
	var times: Array = Layout.PORTAL_SEQUENCES[kind][sequence]
	clock += delta * speed
	while clock >= float(times[step]):
		clock -= float(times[step])
		if step < times.size() - 1:
			step += 1
		elif sequence == &"close":
			queue_free()
			return
		elif sequence == &"suck":
			held = true
			return
		elif sequence == Layout.PORTAL_LOOPS[kind]:
			step = 0
		else:
			var carry := clock
			_play(Layout.PORTAL_LOOPS[kind])
			clock = carry
			return
		_show_step()


func _play(next: StringName) -> void:
	sequence = next
	step = 0
	clock = 0.0
	held = false
	speed = 1.0
	if not drawn:
		return
	var frames: int = Layout.PORTAL_SEQUENCES[kind][next].size()
	for layer in Layout.PORTAL_LAYERS:
		var sheet: Sprite2D = sprites[layer]
		sheet.frame = 0
		sheet.texture = load(Layout.portal_sheet(kind, next, layer))
		sheet.hframes = frames
	_show_step()


func _show_step() -> void:
	if not drawn:
		return
	for layer in Layout.PORTAL_LAYERS:
		sprites[layer].frame = step


# What is left of the sequence playing, in seconds.
func _left() -> float:
	var times: Array = Layout.PORTAL_SEQUENCES[kind].get(sequence, [])
	if times.is_empty():
		return 0.0
	var left := maxf(float(times[step]) - clock, 0.0)
	for i in range(step + 1, times.size()):
		left += float(times[i])
	return left / speed


func _build_drawn() -> void:
	var spec: Dictionary = Layout.PORTALS[kind]
	front = Node2D.new()
	front.name = "PortalFront"
	for layer in Layout.PORTAL_LAYERS:
		var sheet := Sprite2D.new()
		sheet.name = String(layer).capitalize()
		sheet.centered = false
		sheet.scale = Vector2.ONE * Layout.SCALE
		sheet.offset = -spec.anchor
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
	var spec: Dictionary = Layout.PLACEHOLDER_PORTAL
	var radii := opening()
	var added := CanvasItemMaterial.new()
	added.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	var glow := Polygon2D.new()
	glow.name = "Glow"
	glow.polygon = _ellipse(radii * spec.glow_scale, spec.points)
	glow.color = spec.glow
	glow.material = added
	add_child(glow)
	var depth := Polygon2D.new()
	depth.name = "Depth"
	depth.polygon = _ellipse(radii, spec.points)
	depth.color = spec.depth
	add_child(depth)
	rim = Line2D.new()
	rim.name = "Rim"
	rim.points = _ellipse(radii, spec.points)
	rim.closed = true
	rim.width = spec.rim_width
	rim.default_color = spec.rim
	add_child(rim)
	flecks = CPUParticles2D.new()
	flecks.name = "Flecks"
	flecks.amount = spec.flecks
	flecks.lifetime = spec.fleck_life
	flecks.emitting = false
	flecks.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	flecks.emission_rect_extents = Vector2(radii.x * 0.8, radii.y * 0.5)
	flecks.direction = Vector2.UP
	flecks.spread = 20.0
	flecks.gravity = Vector2(0, -30)
	flecks.initial_velocity_min = spec.fleck_speed.x
	flecks.initial_velocity_max = spec.fleck_speed.y
	flecks.scale_amount_min = Layout.SCALE
	flecks.scale_amount_max = Layout.SCALE
	flecks.color = spec.fleck_color
	var card := Image.create(int(spec.fleck_size.x), int(spec.fleck_size.y), false, Image.FORMAT_RGBA8)
	card.fill(Color.WHITE)
	flecks.texture = ImageTexture.create_from_image(card)
	add_child(flecks)
	scale = Vector2(0.05, 0.05)


# The placeholder's own tweens run on physics, with its sequence clock.
func _grow_in(seconds: float) -> void:
	if grow != null and grow.is_valid():
		grow.kill()
	grow = create_tween().set_process_mode(Tween.TWEEN_PROCESS_PHYSICS)
	grow.tween_property(self, "scale", Vector2.ONE, maxf(seconds, 0.01)).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)


func _shrink_away(seconds: float) -> void:
	if grow != null and grow.is_valid():
		grow.kill()
	grow = create_tween().set_process_mode(Tween.TWEEN_PROCESS_PHYSICS).set_parallel()
	grow.tween_property(self, "scale", Vector2(0.05, 0.05), maxf(seconds, 0.01)).set_trans(Tween.TRANS_QUAD) \
		.set_ease(Tween.EASE_IN)
	grow.tween_property(self, "modulate:a", 0.0, maxf(seconds, 0.01))


func _flare() -> void:
	var spec: Dictionary = Layout.PLACEHOLDER_PORTAL
	if flare != null and flare.is_valid():
		flare.kill()
	rim.default_color = spec.flare
	flare = create_tween().set_process_mode(Tween.TWEEN_PROCESS_PHYSICS)
	flare.tween_property(rim, "default_color", spec.rim, spec.flare_time)


func _ellipse(radii: Vector2, points: int) -> PackedVector2Array:
	var out := PackedVector2Array()
	for i in points:
		out.append(Vector2.from_angle(TAU * i / points) * radii)
	return out
