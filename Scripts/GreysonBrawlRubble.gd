extends Node2D

# The roof coming in on the ring for Greyson's final brawl (GreysonFinalBrawl). plan() lays the fill out, off a
# fixed seed, so a watched cut and a skipped one build the same arena: a jittered grid over the ropes' inside with
# the clearing left empty, low ridges along the clearing's front edge, medium heaps near it and big ones further
# out, and nothing drawn over his silhouette and the tell (GreysonBrawlLayout.KEEP_CLEAR). drop_wave() brings one
# of four waves down, farthest first: each piece falls onto its base with its shadow growing under it, and its heap
# is swapped in under its landing's dust. settle() is the whole fill at once, which a skip lands on.
#
# This node is the heaps' y-sorted layer under GreysonScene's HazardLayer, so they sort with the fighters by their
# bases, and the barbell he tosses away lies among them. The pieces in the air are drawn over everything on FxLayer
# and their shadows on FloorLayer. Nothing here is in greyson_hazard: the heaps are scenery and stay through both
# outros, and clear_falling() takes whatever is still in the air. Every wait is a tween bound to what it moves.

signal wave_landed(wave: int)
signal barbell_landed

const Layout := preload("res://Scripts/GreysonBrawlLayout.gd")

var fx_layer: Node2D
var floor_layer: Node2D
# {base, frame, wave, delay, shape}, farthest from the clearing first, and each one's heap once it is down.
var slots: Array[Dictionary] = []
var heaps := {}
# Whatever is still in the air - pieces, their shadows and their landings - and the tweens driving them.
var falling: Array[Node] = []
var falling_tweens: Array[Tween] = []
var waves_landed := {}
var barbell: Node2D
var barbell_tween: Tween
var barbell_down := false
var barbell_from := Vector2.ZERO


func setup(fx: Node2D, ground: Node2D, ropes: Rect2) -> void:
	fx_layer = fx
	floor_layer = ground
	y_sort_enabled = true
	slots = plan(ropes)


static func plan(ropes: Rect2) -> Array[Dictionary]:
	var rng := RandomNumberGenerator.new()
	rng.seed = Layout.FILL_SEED
	var clearing: Rect2 = Layout.CLEARING
	var keep_out := clearing.grow(Layout.CLEARING_MARGIN)
	# The front ridges' own row: the grid leaves it to them.
	var front := Rect2(keep_out.position.x, keep_out.end.y, keep_out.size.x, Layout.FILL_STEP.y * 0.6)
	var area := ropes.grow(-Layout.FILL_INSET)
	var step: Vector2 = Layout.FILL_STEP
	var cols := floori(area.size.x / step.x)
	var rows := floori(area.size.y / step.y)
	var pad := (area.size - step * Vector2(cols, rows)) / 2.0
	var planned: Array[Dictionary] = []
	for row in rows:
		for col in cols:
			var jitter := Vector2(rng.randf_range(-1.0, 1.0), rng.randf_range(-1.0, 1.0)) * step * Layout.FILL_JITTER
			var base := (area.position + pad + step * Vector2(col + 0.5, row + 0.85) + jitter).round()
			if keep_out.has_point(base) or front.has_point(base):
				continue
			var frame := _pick(rng, base)
			if frame >= 0:
				planned.append({base = base, frame = frame})
	var ridges := floori(clearing.size.x / Layout.FRONT_RIDGE_STEP)
	var first_x := clearing.get_center().x - Layout.FRONT_RIDGE_STEP * (ridges - 1) / 2.0
	for k in ridges:
		var spread: float = Layout.FRONT_RIDGE_JITTER
		var base := Vector2(first_x + Layout.FRONT_RIDGE_STEP * k + rng.randf_range(-spread, spread),
			keep_out.end.y + rng.randf_range(0.0, spread)).round()
		var frame: int = Layout.FRONT_HEAPS[rng.randi_range(0, Layout.FRONT_HEAPS.size() - 1)]
		if not Layout.heap_rect(base, frame).intersects(Layout.KEEP_CLEAR):
			planned.append({base = base, frame = frame})
	planned.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return _from_clearing(a.base) > _from_clearing(b.base))
	for i in planned.size():
		planned[i].wave = mini(floori(float(i * Layout.WAVES) / planned.size()), Layout.WAVES - 1)
		planned[i].delay = rng.randf_range(0.0, Layout.PIECE_DELAY)
		planned[i].shape = rng.randi_range(0, Layout.DEBRIS_SHAPES - 1)
	return planned


# Low in front of the clearing, medium near it, big further out with a beam in about one in four or five; a heap
# that would stand over his silhouette or the tell falls back to a ridge, and is left out if even that would.
static func _pick(rng: RandomNumberGenerator, base: Vector2) -> int:
	var clearing: Rect2 = Layout.CLEARING
	var near := _from_clearing(base) <= Layout.NEAR_CLEARING
	var kinds: Array
	if near and base.y > clearing.end.y:
		kinds = Layout.FRONT_HEAPS
	elif near:
		kinds = Layout.MEDIUM_HEAPS
	elif rng.randf() < Layout.BEAM_CHANCE:
		kinds = Layout.BEAM_HEAPS
	else:
		kinds = Layout.BIG_HEAPS
	var frame: int = kinds[rng.randi_range(0, kinds.size() - 1)]
	if not Layout.heap_rect(base, frame).intersects(Layout.KEEP_CLEAR):
		return frame
	frame = Layout.RIDGE_HEAPS[rng.randi_range(0, Layout.RIDGE_HEAPS.size() - 1)]
	return -1 if Layout.heap_rect(base, frame).intersects(Layout.KEEP_CLEAR) else frame


static func _from_clearing(point: Vector2) -> float:
	var clearing: Rect2 = Layout.CLEARING
	var outside := Vector2(maxf(maxf(clearing.position.x - point.x, 0.0), point.x - clearing.end.x),
		maxf(maxf(clearing.position.y - point.y, 0.0), point.y - clearing.end.y))
	return outside.length()


#THE WAVES

func drop_wave(wave: int) -> void:
	for i in slots.size():
		if slots[i].wave == wave and not heaps.has(i):
			_drop(i)


func _drop(i: int) -> void:
	var slot: Dictionary = slots[i]
	var piece := _make_piece(slot.shape)
	piece.visible = false
	fx_layer.add_child(piece)
	piece.global_position = slot.base - Vector2(0, Layout.DEBRIS_DROP)
	var shadow := _make_shadow()
	shadow.visible = false
	floor_layer.add_child(shadow)
	shadow.global_position = slot.base
	falling.append(piece)
	falling.append(shadow)
	var fall := piece.create_tween()
	falling_tweens.append(fall)
	fall.tween_interval(slot.delay)
	fall.tween_method(_fall_step.bind(piece, shadow, slot), 0.0, 1.0, Layout.DEBRIS_FALL)
	fall.tween_callback(_land.bind(i, piece, shadow))


# `t` is the fall's share of its time; the drop eases in, so the piece is falling fastest as it lands.
func _fall_step(t: float, piece: Node2D, shadow: Node2D, slot: Dictionary) -> void:
	piece.visible = true
	shadow.visible = true
	piece.global_position = (slot.base - Vector2(0, Layout.DEBRIS_DROP * (1.0 - t * t))).round()
	var spin := int(t * Layout.DEBRIS_FALL / Layout.DEBRIS_SPIN) % 2
	if piece is Sprite2D:
		piece.frame = slot.shape * 2 + spin
	else:
		piece.scale.x = 1.0 if spin == 0 else -1.0
	shadow.scale = Vector2.ONE * lerpf(Layout.SHADOW_SCALE.x, Layout.SHADOW_SCALE.y, t) * (Layout.SCALE if shadow is Sprite2D else 1.0)
	shadow.modulate.a = lerpf(Layout.SHADOW_ALPHA.x, Layout.SHADOW_ALPHA.y, t)


func _land(i: int, piece: Node2D, shadow: Node2D) -> void:
	piece.queue_free()
	shadow.queue_free()
	var slot: Dictionary = slots[i]
	var landing := _make_landing()
	fx_layer.add_child(landing)
	landing.global_position = slot.base
	falling.append(landing)
	var play := landing.create_tween()
	falling_tweens.append(play)
	for frame in _landing_frames():
		play.tween_callback(_landing_step.bind(landing, frame))
		if frame == Layout.LAND_HEAP_FRAME:
			play.tween_callback(_place.bind(i))
		play.tween_interval(Layout.LAND_STEP)
	play.tween_callback(landing.queue_free)
	if not waves_landed.has(slot.wave):
		waves_landed[slot.wave] = true
		wave_landed.emit(slot.wave)


# The whole fill, down and still: what a watched cut has left by the cut-in, and what a skip lands on.
func settle() -> void:
	clear_falling()
	for i in slots.size():
		_place(i)


func clear_falling() -> void:
	for tween in falling_tweens:
		if tween.is_valid():
			tween.kill()
	falling_tweens.clear()
	for node in falling:
		if is_instance_valid(node):
			node.queue_free()
	falling.clear()
	if is_instance_valid(barbell) and not barbell_down:
		barbell.queue_free()
		barbell = null


func falling_count() -> int:
	return falling.filter(func(node: Node) -> bool: return is_instance_valid(node) and not node.is_queued_for_deletion()).size()


func _place(i: int) -> void:
	if heaps.has(i):
		return
	var slot: Dictionary = slots[i]
	var heap := _make_heap(slot.frame)
	add_child(heap)
	heap.global_position = slot.base
	heaps[i] = heap


#THE BARBELL

# From `from` (its centre of mass as it leaves his hand) to screen-left into the rubble over `time`, turning over
# as it flies, and down flat among the heaps.
func toss_barbell(from: Vector2, time: float) -> void:
	if is_instance_valid(barbell):
		return
	barbell_from = from
	barbell = _make_barbell()
	add_child(barbell)
	barbell.global_position = from.round()
	barbell_tween = barbell.create_tween()
	barbell_tween.tween_method(_barbell_step, 0.0, 1.0, time)
	barbell_tween.tween_callback(_barbell_landed)


func _barbell_step(t: float) -> void:
	var flight: Vector2 = barbell_from.lerp(Layout.TOSS_TO, t) - Vector2(0, Layout.TOSS_ARC * 4.0 * t * (1.0 - t))
	barbell.global_position = flight.round()
	barbell.rotation = -Layout.TOSS_TURNS * TAU * t


func _barbell_landed() -> void:
	place_barbell()
	barbell_landed.emit()


# Where the toss leaves it, at once: the skip's end state.
func place_barbell() -> void:
	if barbell_tween:
		barbell_tween.kill()
	barbell_tween = null
	if not is_instance_valid(barbell):
		barbell = _make_barbell()
		add_child(barbell)
	barbell.global_position = Layout.TOSS_TO
	barbell.rotation = 0.0
	barbell_down = true


#THE PIECES, the sheets once they are on and the stand-ins until then

func _make_piece(shape: int) -> Node2D:
	if Layout.uses_final_fx(&"debris"):
		var sheet := _sheet(&"debris")
		sheet.frame = shape * 2
		return sheet
	var look: Dictionary = Layout.PLACEHOLDER_FX[&"debris"]
	var size: Vector2 = look.size * (0.8 + 0.1 * shape)
	var chunk := Polygon2D.new()
	chunk.polygon = PackedVector2Array([Vector2(-size.x * 0.5, -size.y * 0.35), Vector2(-size.x * 0.1, -size.y),
		Vector2(size.x * 0.5, -size.y * 0.7), Vector2(size.x * 0.4, 0), Vector2(-size.x * 0.3, 0)])
	chunk.vertex_colors = PackedColorArray([look.light, look.light, look.light, look.dark, look.dark])
	return chunk


func _make_shadow() -> Node2D:
	if Layout.uses_final_fx(&"debris_shadow"):
		return _sheet(&"debris_shadow")
	var look: Dictionary = Layout.PLACEHOLDER_FX[&"debris_shadow"]
	var shadow := Polygon2D.new()
	var polygon := PackedVector2Array()
	for k in 16:
		polygon.append(Vector2.from_angle(TAU * k / 16.0) * look.radii)
	shadow.polygon = polygon
	shadow.color = look.color
	return shadow


func _make_landing() -> Node2D:
	if Layout.uses_final_fx(&"debris_land"):
		return _sheet(&"debris_land")
	var look: Dictionary = Layout.PLACEHOLDER_FX[&"debris_land"]
	var puff := Polygon2D.new()
	var polygon := PackedVector2Array()
	for k in 16:
		polygon.append(Vector2.from_angle(PI + PI * k / 15.0) * Vector2(look.radius * 1.6, look.radius))
	puff.polygon = polygon
	puff.color = look.color
	return puff


func _landing_frames() -> int:
	if Layout.uses_final_fx(&"debris_land"):
		return Layout.FX[&"debris_land"].hframes
	return Layout.PLACEHOLDER_FX[&"debris_land"].scales.size()


func _landing_step(landing: Node2D, frame: int) -> void:
	if landing is Sprite2D:
		landing.frame = frame
		return
	var look: Dictionary = Layout.PLACEHOLDER_FX[&"debris_land"]
	landing.scale = Vector2.ONE * look.scales[frame]
	landing.modulate.a = look.alphas[frame]


func _make_heap(frame: int) -> Node2D:
	if Layout.uses_final_fx(&"rubble_mound"):
		var sheet := _sheet(&"rubble_mound")
		sheet.frame = frame
		return sheet
	var look: Dictionary = Layout.PLACEHOLDER_FX[&"heap"]
	var half: float = Layout.HEAP_HALF_WIDTHS[frame] * Layout.SCALE
	var height: float = Layout.HEAP_HEIGHTS[frame] * Layout.SCALE
	var mound := Polygon2D.new()
	var polygon := PackedVector2Array()
	var colors := PackedColorArray()
	var points: int = look.points
	for k in points + 1:
		var u := lerpf(-1.0, 1.0, float(k) / points)
		polygon.append(Vector2(u * half, -height * (1.0 - pow(absf(u), 1.7))).round())
		colors.append(look.base.lerp(look.top, 1.0 - pow(absf(u), 1.7)))
	mound.polygon = polygon
	mound.vertex_colors = colors
	return mound


# Its origin is its centre of mass, which it turns about.
func _make_barbell() -> Node2D:
	if Layout.uses_final_barbell():
		var prop := Sprite2D.new()
		prop.name = "Barbell"
		prop.texture = load(Layout.BARBELL_PROP.texture)
		prop.offset = Layout.BARBELL_PROP.size / 2.0 - Layout.BARBELL_PROP.balance
		prop.scale = Vector2.ONE * Layout.SCALE
		return prop
	var look: Dictionary = Layout.PLACEHOLDER_FX[&"barbell"]
	var prop := Node2D.new()
	prop.name = "Barbell"
	var bar := Line2D.new()
	bar.points = PackedVector2Array([Vector2(-look.length / 2.0, 0), Vector2(look.length / 2.0, 0)])
	bar.width = look.width
	bar.default_color = look.bar
	prop.add_child(bar)
	for side in [-1.0, 1.0]:
		var plate := Polygon2D.new()
		var size: Vector2 = look.plate_size
		var centre := Vector2(side * (look.length / 2.0 - size.x), 0)
		plate.polygon = PackedVector2Array([centre - size / 2.0, centre + Vector2(size.x, -size.y) / 2.0, centre + size / 2.0,
			centre + Vector2(-size.x, size.y) / 2.0])
		plate.color = look.plate
		prop.add_child(plate)
	return prop


func _sheet(key: StringName) -> Sprite2D:
	var spec: Dictionary = Layout.FX[key]
	var sheet := Sprite2D.new()
	sheet.texture = load(spec.texture)
	sheet.hframes = spec.hframes
	sheet.offset = spec.offset
	sheet.scale = Vector2.ONE * Layout.SCALE
	return sheet
