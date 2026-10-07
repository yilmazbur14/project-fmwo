extends Node2D

# Jordan's room as it comes apart (JordanFinaleScript). Its layers - floor, walls, furniture, props and clutter,
# bottom to top, each a full screen of 640x360 texels drawn from the screen's origin at SCALE - are cut into pieces:
# the room artist's own (build_pieces), or CHUNK-texel squares cut here, each a Sprite2D showing its own region of its
# layer (build). Standing, they sit where they belong and the room looks
# whole. tremble() shakes the view and jitters the clutter; drop() lets a few pieces of a layer go; collapse() lets
# them all go in waves and is over once the last has fallen away. add_piece() puts another node - the empty chair, the
# fallen moustache - in with a layer, to go with it.
#
# ONE LOOP moves every falling piece (_process), off a seeded generator, so the collapse comes out the same every
# time: a jitter, gravity, a spin, and each shrinks and darkens as it drops into the void, and is freed. A chunk with
# nothing drawn in it is never made when its layer's pixels can be read; where they can't (an imported texture in a
# headless run), every chunk is kept.

const SCALE := 3.0
const CHUNK := 24
const MAX_PIECES := 2048
const SEED := 20260928

#THE FALL (px and seconds)
const FALL_TIME := 1.1
const GRAVITY := 1400.0
const KICK := Vector2(90.0, 160.0)
const SPIN := 4.0
const SHRINK_TO := 0.35
const DARKEN_TO := Color(0.2, 0.12, 0.25)
# A wave's pieces don't all go on its beat: each is this much later at most.
const WAVE_STAGGER := 0.35
# The floor goes from the edges in, its middle this much after its edges.
const FLOOR_INWARD := 0.8

#THE TREMBLE (px and seconds), by level
const SHAKE := [0.0, 3.0, 6.0]
const SHAKE_STEP := 0.05
const JITTER := [0.0, 1.0, 2.0]
const VIEW_SIZE := Vector2(1920, 1080)

const ScreenView := preload("res://Scripts/ScreenView.gd")

var rng := RandomNumberGenerator.new()
# layer name -> its pieces, each {node, home, start, velocity, spin, age}; `start` is INF until it goes.
var layers := {}
var order: Array[StringName] = []
var clock := 0.0
var level := 0
var shake_clock := 0.0
# The collapse a beat is waiting on, for a skip to run out.
var collapsing: Tween


func _ready() -> void:
	rng.seed = SEED


# `layer_specs`, bottom to top, each {name, texture, image}: `image` the layer's pixels if they can be read, or null.
func build(layer_specs: Array) -> void:
	var made := 0
	for spec in layer_specs:
		var layer_name: StringName = spec.name
		var texture: Texture2D = spec.texture
		var image: Image = spec.get("image")
		order.append(layer_name)
		layers[layer_name] = []
		var size := Vector2i(texture.get_width(), texture.get_height())
		for y in range(0, size.y, CHUNK):
			for x in range(0, size.x, CHUNK):
				if made >= MAX_PIECES:
					break
				var region := Rect2i(x, y, mini(CHUNK, size.x - x), mini(CHUNK, size.y - y))
				if image != null and image.get_region(region).is_invisible():
					continue
				var piece := Sprite2D.new()
				piece.texture = texture
				piece.region_enabled = true
				piece.region_rect = Rect2(region)
				piece.scale = Vector2.ONE * SCALE
				piece.position = (Vector2(region.position) + Vector2(region.size) / 2.0) * SCALE
				add_child(piece)
				_add(piece, layer_name)
				made += 1


# The room artist's own pieces instead (JordanRoomPieces.PIECES): `layer_order` bottom to top, and `pieces` layer ->
# [{texture: its path, at: its top-left texel on the layer}], a whole prop or a chunk of floor or wall each, which
# tile each layer exactly.
func build_pieces(layer_order: Array, pieces: Dictionary) -> void:
	for layer_name in layer_order:
		order.append(layer_name)
		layers[layer_name] = []
		for spec in pieces.get(layer_name, []):
			var texture: Texture2D = load(spec.texture)
			var piece := Sprite2D.new()
			piece.texture = texture
			piece.scale = Vector2.ONE * SCALE
			piece.position = (spec.at + texture.get_size() / 2.0) * SCALE
			add_child(piece)
			_add(piece, layer_name)


# Another node in with `layer_name`, to go with it: where it stands now is where it belongs.
func add_piece(node: Node2D, layer_name: StringName) -> void:
	if not layers.has(layer_name):
		layers[layer_name] = []
	_add(node, layer_name)


func pieces_left() -> int:
	var left := 0
	for layer_name in layers:
		left += layers[layer_name].size()
	return left


# 0 still, 1 the room trembling, 2 worse.
func tremble(to_level: int) -> void:
	level = clampi(to_level, 0, SHAKE.size() - 1)
	if level == 0:
		_settle_view()
		for piece in layers.get(&"clutter", []):
			if piece.start == INF and is_instance_valid(piece.node):
				piece.node.position = piece.home


# `count` pieces of `layer_name` go now, the ones nearest its top first: what the shaking shakes loose.
func drop(layer_name: StringName, count: int) -> void:
	var standing: Array = layers.get(layer_name, []).filter(func(piece): return piece.start == INF)
	standing.sort_custom(func(a, b): return a.home.y < b.home.y)
	for i in mini(count, standing.size()):
		_let_go(standing[i], clock)


# Every piece goes, a layer a wave: `waves` is layer name -> seconds from now its wave starts. Awaitable: over when the
# last piece has fallen away, and the tremble with it.
func collapse(waves: Dictionary) -> void:
	var last := 0.0
	for layer_name in layers:
		var wave: float = waves.get(layer_name, 0.0)
		for piece in layers[layer_name]:
			if piece.start != INF:
				continue
			var delay := rng.randf() * WAVE_STAGGER
			if layer_name == &"floor":
				delay = _inward(piece.home) * FLOOR_INWARD
			_let_go(piece, clock + wave + delay)
			last = maxf(last, wave + delay)
	collapsing = create_tween()
	collapsing.tween_interval(last + FALL_TIME)
	await collapsing.finished
	collapsing = null
	# Only a skip, running the wait out, finds any still there.
	for layer_name in layers:
		for piece in layers[layer_name]:
			if is_instance_valid(piece.node):
				piece.node.queue_free()
		layers[layer_name].clear()
	tremble(0)


func _process(delta: float) -> void:
	clock += delta
	_step_tremble(delta)
	for layer_name in layers:
		var pieces: Array = layers[layer_name]
		for i in range(pieces.size() - 1, -1, -1):
			var piece: Dictionary = pieces[i]
			if piece.start > clock:
				continue
			if not is_instance_valid(piece.node):
				pieces.remove_at(i)
				continue
			piece.age += delta
			var t := minf(piece.age / FALL_TIME, 1.0)
			piece.velocity.y += GRAVITY * delta
			var node: Node2D = piece.node
			node.position += piece.velocity * delta
			node.rotation += piece.spin * delta
			node.scale = piece.scale * lerpf(1.0, SHRINK_TO, t)
			node.modulate = Color.WHITE.lerp(DARKEN_TO, t)
			if piece.age >= FALL_TIME:
				node.queue_free()
				pieces.remove_at(i)


func _step_tremble(delta: float) -> void:
	if level == 0:
		return
	shake_clock += delta
	if shake_clock < SHAKE_STEP:
		return
	shake_clock = 0.0
	var strength: float = SHAKE[level]
	ScreenView.shake_offset = Vector2(rng.randf_range(-strength, strength), rng.randf_range(-strength, strength)).round()
	ScreenView.apply(get_tree())
	var jitter: float = JITTER[level] * SCALE
	for piece in layers.get(&"clutter", []):
		if piece.start == INF and is_instance_valid(piece.node):
			piece.node.position = piece.home + Vector2(rng.randf_range(-jitter, jitter), rng.randf_range(-jitter, jitter)).round()


func _settle_view() -> void:
	ScreenView.shake_offset = Vector2.ZERO
	if is_inside_tree():
		ScreenView.apply(get_tree())


func _add(node: Node2D, layer_name: StringName) -> void:
	layers[layer_name].append({"node": node, "home": node.position, "scale": node.scale, "start": INF,
		"velocity": Vector2.ZERO, "spin": 0.0, "age": 0.0})


func _let_go(piece: Dictionary, at: float) -> void:
	piece.start = at
	piece.velocity = Vector2(rng.randf_range(-KICK.x, KICK.x), -rng.randf_range(0.0, KICK.y))
	piece.spin = rng.randf_range(-SPIN, SPIN)


# 0 at the screen's edge and 1 in its middle.
func _inward(at: Vector2) -> float:
	var edge := minf(minf(at.x, VIEW_SIZE.x - at.x), minf(at.y, VIEW_SIZE.y - at.y))
	return clampf(edge / (VIEW_SIZE.y / 2.0), 0.0, 1.0)
