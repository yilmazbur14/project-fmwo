extends Node2D

# The water over Liam's ring and the ice it freezes into (his attack 2), flat on his FloorLayer under everyone. Purely a
# picture: the player's ice is PlayerScript's (set_ice), which LiamTremors turns on where is_frozen_at() says.
#
# The water: `coverage`, 0 to 1, picks one of FLOOD_FRAMES nested coverage frames, from sparse puddles to a full sheet.
# Each tsunami wave that finishes or collapses adds its share (add_water), settle() tops it up to full, and drain()
# steps it back to dry. The ice: a sheet grown from a point as a widening circle (freeze_from), frost stamped round its
# edge while it grows, then melted back to water (thaw) or shattered (shatter). Attack 3 melts it outward from its
# tornados instead (melt_from): circles of the water's own frame widening over the ice until none is left. Everything it
# times is node-bound or steps in its own _physics_process, so a pause and a finisher's freeze hold it.

const Layout := preload("res://Scripts/LiamArtLayout.gd")

enum Ice { NONE, GROWING, SOLID, MELTING, SHATTERING }

var coverage := 0.0
var ice := Ice.NONE
var ice_centre := Vector2.ZERO
var ice_radius := 0.0
var freeze_speed := 0.0
# The farthest the circle ever needs to reach: the flood's farthest corner from where it started.
var full_radius := 0.0
var ice_clock := 0.0
var ice_time := 0.0
var coverage_tween: Tween

var water: Node2D
var water_sheet: Sprite2D
var water_frames: Array[Texture2D] = []
# fx_v2's ripple over the water, drawn inside the water's own shape (the water sheet clips it).
var ripple: Sprite2D
var ripple_frames: Array[Texture2D] = []
var ripple_clock := 0.0
var puddles: Array[Polygon2D] = []
var full_sheet: Polygon2D
var ice_mask: Polygon2D
var ice_sheet: Sprite2D
var ice_frames: Dictionary = {}
var ice_look: Node2D
var frost: Node2D
var frost_pieces: Array[Node2D] = []
# The melt: a circle of water per point, widening at melt_speed over the ice until melt_full covers the whole flood.
var melt: Node2D
var melt_rim: Node2D
var melt_circles: Array[Polygon2D] = []
var melt_water: Array[Node2D] = []
var melt_centres: Array[Vector2] = []
var melt_pieces: Array[Node2D] = []
var melt_radius := 0.0
var melt_speed := 0.0
var melt_full := 0.0
var melt_clock := 0.0


func _ready() -> void:
	_build_water()
	_build_ice()
	_show_water()


#THE WATER

# The coverage frame showing: -1 dry. Over as many frames as its sheet holds.
func water_frame() -> int:
	if coverage <= 0.0:
		return -1
	var count := water_frames.size() if not water_frames.is_empty() else Layout.FLOOD_FRAMES
	return clampi(ceili(coverage * count) - 1, 0, count - 1)


func add_water(amount: float) -> void:
	_kill_coverage()
	coverage = clampf(coverage + amount, 0.0, 1.0)
	# Six sixths add up a hair under one in floats: full is full.
	if coverage > 1.0 - 0.000001:
		coverage = 1.0
	_show_water()


# Full over `time`.
func settle(time: float) -> void:
	_tween_coverage(1.0, time)


# Dry over `time`, a frame at a time.
func drain(time: float) -> void:
	_tween_coverage(0.0, time)


func _tween_coverage(to: float, time: float) -> void:
	_kill_coverage()
	if time <= 0.0:
		coverage = to
		_show_water()
		return
	coverage_tween = create_tween()
	coverage_tween.tween_method(_set_coverage, coverage, to, time)


func _set_coverage(value: float) -> void:
	coverage = value
	_show_water()


func _kill_coverage() -> void:
	if coverage_tween and coverage_tween.is_valid():
		coverage_tween.kill()
	coverage_tween = null


#THE ICE

# A sheet of ice spreading from `point` at `speed` px/s until it covers the whole flood.
func freeze_from(point: Vector2, speed: float) -> void:
	ice = Ice.GROWING
	ice_centre = point
	ice_radius = 0.0
	freeze_speed = speed
	full_radius = 0.0
	var rect: Rect2 = Layout.FLOOD_RECT
	for corner in [rect.position, Vector2(rect.end.x, rect.position.y), rect.end, Vector2(rect.position.x, rect.end.y)]:
		full_radius = maxf(full_radius, point.distance_to(corner))
	_show_ice_frame(&"solid", 0)
	ice_look.modulate = Color.WHITE
	ice_mask.visible = true
	frost.visible = true
	_shape_ice()


func is_iced() -> bool:
	return ice != Ice.NONE


# Whether the ice has reached `point` and still holds.
func is_frozen_at(point: Vector2) -> bool:
	if ice != Ice.GROWING and ice != Ice.SOLID:
		return false
	for centre in melt_centres:
		if point.distance_to(centre) <= melt_radius:
			return false
	return Layout.FLOOD_RECT.has_point(point) and point.distance_to(ice_centre) <= ice_radius


# Melted outward from every one of `points` at `speed` px/s: a circle of the water under it each, over the ice, until
# they cover the whole flood and the ice is gone. Only while there is ice; it ends any growth.
func melt_from(points: Array, speed: float) -> void:
	if not is_iced():
		return
	_end_growth()
	_free_melt()
	melt_speed = speed
	melt_radius = 0.0
	melt_clock = 0.0
	melt_centres.assign(points)
	melt_full = _melt_reach(points)
	for point: Vector2 in points:
		var circle := Polygon2D.new()
		circle.clip_children = CanvasItem.CLIP_CHILDREN_ONLY
		melt.add_child(circle)
		melt_circles.append(circle)
		var inside := _melt_water()
		circle.add_child(inside)
		melt_water.append(inside)
	_shape_melt()


# One more centre the melt spreads from, while it is melting (a tornado's trail as it moves): a circle of the water under
# it at the melt's radius. The melt still ends when it would have.
func add_melt_centre(point: Vector2) -> void:
	if not is_melting():
		return
	melt_centres.append(point)
	var circle := Polygon2D.new()
	circle.clip_children = CanvasItem.CLIP_CHILDREN_ONLY
	melt.add_child(circle)
	melt_circles.append(circle)
	var inside := _melt_water()
	circle.add_child(inside)
	melt_water.append(inside)
	_shape_melt()


func is_melting() -> bool:
	return not melt_circles.is_empty()


# Whatever ice the melt hasn't reached yet thaws at once (0.3 s), and the circles go.
func finish_melt() -> void:
	if not is_melting():
		return
	thaw(0.3)


# Back to water over `time`: the flood stays full.
func thaw(time: float) -> void:
	if not is_iced() or ice == Ice.MELTING or ice == Ice.SHATTERING:
		return
	_end_growth()
	_free_melt()
	ice = Ice.MELTING
	ice_clock = 0.0
	ice_time = maxf(time, 0.01)


# Broken to pieces over SHATTER_TIME.
func shatter() -> void:
	if not is_iced() or ice == Ice.SHATTERING:
		return
	_end_growth()
	_free_melt()
	ice = Ice.SHATTERING
	ice_clock = 0.0
	ice_time = Layout.SHATTER_TIME


func _physics_process(delta: float) -> void:
	if ripple != null and water.visible:
		ripple_clock += delta
		ripple.texture = ripple_frames[int(ripple_clock / Layout.FLOOD_RIPPLE_FRAME_TIME) % ripple_frames.size()]
	match ice:
		Ice.GROWING:
			ice_radius = minf(ice_radius + freeze_speed * delta, full_radius)
			_shape_ice()
			if ice_radius >= full_radius:
				ice = Ice.SOLID
				_end_growth()
		Ice.SOLID:
			ice_clock += delta
			# The glint runs through every frame after the first, however many the sheet holds.
			var into := fposmod(ice_clock, Layout.ICE_GLINT_TIME * 2.0)
			var glints := maxi(ice_frames.get(&"solid", [null, null]).size() - 1, 1)
			_show_ice_frame(&"solid", 1 + mini(int(into / (0.16 / glints)), glints - 1) if into < 0.16 else 0)
		Ice.MELTING, Ice.SHATTERING:
			ice_clock += delta
			var done := clampf(ice_clock / ice_time, 0.0, 1.0)
			_show_ice_end(done)
			if done >= 1.0:
				_clear_ice()
	if is_melting():
		melt_radius += melt_speed * delta
		melt_clock += delta
		_shape_melt()
		if melt_radius >= melt_full:
			_clear_ice()
			_free_melt()
	if frost.visible:
		_step_frost(delta)


func _end_growth() -> void:
	ice_radius = full_radius
	_shape_ice()
	frost.visible = false


func _clear_ice() -> void:
	ice = Ice.NONE
	ice_radius = 0.0
	ice_mask.visible = false
	frost.visible = false


#BUILDING IT

func _build_water() -> void:
	water = Node2D.new()
	water.name = "Water"
	add_child(water)
	if Layout.final_flood():
		water_frames = _frames(Layout.FLOOD_SHEET)
		water_sheet = _tiled(water_frames[0])
		water.add_child(water_sheet)
		if ResourceLoader.exists(Layout.FLOOD_RIPPLE_SHEET):
			ripple_frames = _frames(Layout.FLOOD_RIPPLE_SHEET)
			water_sheet.clip_children = CanvasItem.CLIP_CHILDREN_AND_DRAW
			ripple = Sprite2D.new()
			ripple.name = "Ripple"
			ripple.texture = ripple_frames[0]
			ripple.centered = false
			ripple.region_enabled = true
			ripple.region_rect = Rect2(Vector2.ZERO, Layout.FLOOD_RECT.size / Layout.SCALE)
			ripple.texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
			water_sheet.add_child(ripple)
		return
	var look: Dictionary = Layout.PLACEHOLDER_FLOOD
	var rect: Rect2 = Layout.FLOOD_RECT
	full_sheet = Polygon2D.new()
	full_sheet.polygon = Layout.rect_polygon(_local_rect(rect))
	full_sheet.color = look.water
	water.add_child(full_sheet)
	var grid: Vector2i = look.puddles
	var random := RandomNumberGenerator.new()
	random.seed = 29
	for row in grid.y:
		for column in grid.x:
			var centre := rect.position + rect.size * Vector2((column + 0.5) / grid.x, (row + 0.5) / grid.y)
			centre += Vector2(random.randf_range(-1.0, 1.0), random.randf_range(-1.0, 1.0)) * look.jitter
			var puddle := Polygon2D.new()
			puddle.polygon = Layout.ellipse(look.puddle_radius, 20)
			puddle.position = to_local_point(centre)
			puddle.color = look.water
			water.add_child(puddle)
			puddles.append(puddle)


func _build_ice() -> void:
	ice_mask = Polygon2D.new()
	ice_mask.name = "IceMask"
	ice_mask.clip_children = CanvasItem.CLIP_CHILDREN_ONLY
	ice_mask.visible = false
	add_child(ice_mask)
	ice_look = Node2D.new()
	ice_mask.add_child(ice_look)
	# Over the ice: the melt's circles, then its rim.
	melt = Node2D.new()
	melt.name = "Melt"
	add_child(melt)
	frost = Node2D.new()
	frost.name = "Frost"
	frost.visible = false
	add_child(frost)
	melt_rim = Node2D.new()
	melt_rim.name = "MeltRim"
	add_child(melt_rim)
	if Layout.final_ice():
		ice_frames = {
			&"solid": _frames(Layout.ICE_SHEET),
			&"melt": _frames(Layout.ICE_MELT_SHEET),
			&"shatter": _frames(Layout.ICE_SHATTER_SHEET),
		}
		ice_sheet = _tiled(ice_frames[&"solid"][0])
		ice_look.add_child(ice_sheet)
		return
	var look: Dictionary = Layout.PLACEHOLDER_FLOOD
	var rect := _local_rect(Layout.FLOOD_RECT)
	var sheet := Polygon2D.new()
	sheet.polygon = Layout.rect_polygon(rect)
	sheet.color = look.ice
	ice_look.add_child(sheet)
	var lines: int = look.ice_lines
	for i in lines:
		var glint := Line2D.new()
		var x := rect.position.x + rect.size.x * (i + 0.5) / lines
		glint.points = PackedVector2Array([Vector2(x, rect.position.y), Vector2(x - 220.0, rect.end.y)])
		glint.width = 3.0
		glint.default_color = look.ice_line
		ice_look.add_child(glint)


# A sheet's frames, each its own texture, so a frame can repeat on its own across the flood: as many as its width holds.
func _frames(path: String) -> Array[Texture2D]:
	var image: Image = (load(path) as Texture2D).get_image()
	if image.is_compressed():
		image.decompress()
	var tile := Vector2i(Layout.FLOOD_TILE)
	var frames: Array[Texture2D] = []
	for i in maxi(image.get_width() / tile.x, 1):
		frames.append(ImageTexture.create_from_image(image.get_region(Rect2i(Vector2i(i * tile.x, 0), tile))))
	return frames


# One tile repeated across the whole flood.
func _tiled(texture: Texture2D) -> Sprite2D:
	var sheet := Sprite2D.new()
	sheet.texture = texture
	sheet.centered = false
	sheet.region_enabled = true
	sheet.region_rect = Rect2(Vector2.ZERO, Layout.FLOOD_RECT.size / Layout.SCALE)
	sheet.texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
	sheet.scale = Vector2.ONE * Layout.SCALE
	sheet.position = to_local_point(Layout.FLOOD_RECT.position)
	return sheet


#DRAWING IT

func _show_water() -> void:
	var frame := water_frame()
	water.visible = frame >= 0
	for inside in melt_water:
		inside.visible = frame >= 0
		var inside_sheet := inside as Sprite2D
		if frame >= 0 and inside_sheet:
			inside_sheet.texture = water_frames[frame]
	if frame < 0:
		return
	if water_sheet != null:
		water_sheet.texture = water_frames[frame]
		return
	full_sheet.visible = frame == Layout.FLOOD_FRAMES - 1
	var grow: float = 0.3 + 0.17 * frame
	for puddle in puddles:
		puddle.scale = Vector2.ONE * grow


func _show_ice_frame(kind: StringName, frame: int) -> void:
	if ice_sheet != null:
		var frames: Array = ice_frames[kind]
		ice_sheet.texture = frames[clampi(frame, 0, frames.size() - 1)]


func _show_ice_end(done: float) -> void:
	var kind := &"melt" if ice == Ice.MELTING else &"shatter"
	if ice_sheet != null:
		var count: int = ice_frames[kind].size()
		_show_ice_frame(kind, mini(int(done * count), count - 1))
		return
	var look: Dictionary = Layout.PLACEHOLDER_FLOOD
	if ice == Ice.MELTING:
		ice_look.modulate = Color(1, 1, 1, 1.0 - done).lerp(look.slush, done * 0.5)
	else:
		ice_look.modulate = Color(1.6, 1.6, 1.6, 1.0 - done)


# The mask to the circle as it stands, cut to the flood.
func _shape_ice() -> void:
	var points := 64
	var outline := PackedVector2Array()
	var centre := to_local_point(ice_centre)
	for i in points:
		outline.append(centre + Vector2.from_angle(TAU * i / points) * ice_radius)
	ice_mask.polygon = outline
	_place_frost()


# Frost stamped every FROST_SPACING px round the growing edge, only where it is over the flood.
func _place_frost() -> void:
	var count := maxi(ceili(TAU * ice_radius / Layout.FROST_SPACING), 1)
	while frost_pieces.size() < count:
		var piece := _frost_piece()
		frost.add_child(piece)
		frost_pieces.append(piece)
	var rect: Rect2 = Layout.FLOOD_RECT
	for i in frost_pieces.size():
		var piece := frost_pieces[i]
		if i >= count:
			piece.visible = false
			continue
		var at := ice_centre + Vector2.from_angle(TAU * i / count) * ice_radius
		piece.visible = rect.has_point(at)
		piece.position = to_local_point(at).round()


func _frost_piece() -> Node2D:
	if Layout.final_frost():
		var sheet := Sprite2D.new()
		var texture: Texture2D = load(Layout.FROST_SHEET)
		sheet.texture = texture
		sheet.hframes = roundi(texture.get_width() / Layout.FROST_FRAME.x)
		sheet.scale = Vector2.ONE * Layout.SCALE
		return sheet
	var look: Dictionary = Layout.PLACEHOLDER_FLOOD
	var piece := Polygon2D.new()
	var size: float = look.frost_size
	piece.polygon = PackedVector2Array([Vector2(0, -size), Vector2(size, 0), Vector2(0, size), Vector2(-size, 0)])
	piece.color = look.frost
	return piece


func _step_frost(delta: float) -> void:
	ice_clock += delta
	var frame := int(ice_clock / Layout.FROST_FRAME_TIME)
	for piece in frost_pieces:
		if piece is Sprite2D:
			piece.frame = frame % piece.hframes


#THE MELT

# How far the circles must reach to cover the flood: the farthest of its points (a 32 px grid) from its nearest centre.
func _melt_reach(points: Array) -> float:
	var rect: Rect2 = Layout.FLOOD_RECT
	var worst := 0.0
	var y := rect.position.y
	while y <= rect.end.y + 31.0:
		var x := rect.position.x
		while x <= rect.end.x + 31.0:
			var at := Vector2(minf(x, rect.end.x), minf(y, rect.end.y))
			var nearest := INF
			for point: Vector2 in points:
				nearest = minf(nearest, at.distance_to(point))
			worst = maxf(worst, nearest)
			x += 32.0
		y += 32.0
	return worst


# What shows inside a melt circle: the water as it is now.
func _melt_water() -> Node2D:
	if not water_frames.is_empty():
		var frame := maxi(water_frame(), 0)
		var inside := _tiled(water_frames[frame])
		inside.visible = water_frame() >= 0
		return inside
	var sheet := Polygon2D.new()
	sheet.polygon = Layout.rect_polygon(_local_rect(Layout.FLOOD_RECT))
	sheet.color = Layout.PLACEHOLDER_FLOOD.water
	sheet.visible = water_frame() >= 0
	return sheet


func _shape_melt() -> void:
	var points := 48
	for i in melt_circles.size():
		var outline := PackedVector2Array()
		var centre := to_local_point(melt_centres[i])
		for k in points:
			outline.append(centre + Vector2.from_angle(TAU * k / points) * melt_radius)
		melt_circles[i].polygon = outline
	_place_melt_rim()


# A rim stamped every FROST_SPACING round each circle, where it lies over the ice and the flood.
func _place_melt_rim() -> void:
	var per_circle := maxi(ceili(TAU * melt_radius / Layout.FROST_SPACING), 1)
	var needed := per_circle * melt_centres.size()
	while melt_pieces.size() < needed:
		var piece := _melt_piece()
		melt_rim.add_child(piece)
		melt_pieces.append(piece)
	var rect: Rect2 = Layout.FLOOD_RECT
	var frame := int(melt_clock / Layout.MELT_RIM_FRAME_TIME)
	for i in melt_pieces.size():
		var piece := melt_pieces[i]
		if i >= needed:
			piece.visible = false
			continue
		var at: Vector2 = melt_centres[i / per_circle] + Vector2.from_angle(TAU * (i % per_circle) / per_circle) * melt_radius
		piece.visible = rect.has_point(at) and is_frozen_at(at + (at - melt_centres[i / per_circle]).normalized() * 4.0)
		piece.position = to_local_point(at).round()
		var sheet := piece as Sprite2D
		if sheet:
			sheet.frame = frame % sheet.hframes


func _melt_piece() -> Node2D:
	if Layout.final_firestorm(Layout.MELT_RIM_SHEET):
		var sheet := Sprite2D.new()
		sheet.texture = load(Layout.MELT_RIM_SHEET)
		sheet.hframes = Layout.strip_count(Layout.MELT_RIM_SHEET, Layout.MELT_RIM_FRAME)
		sheet.scale = Vector2.ONE * Layout.SCALE
		return sheet
	var look: Dictionary = Layout.PLACEHOLDER_MELT_RIM
	var piece := Polygon2D.new()
	var size: float = look.size
	piece.polygon = PackedVector2Array([Vector2(0, -size), Vector2(size, 0), Vector2(0, size), Vector2(-size, 0)])
	piece.color = look.color
	return piece


func _free_melt() -> void:
	for circle in melt_circles:
		circle.queue_free()
	melt_circles.clear()
	melt_water.clear()
	melt_centres.clear()
	for piece in melt_pieces:
		piece.queue_free()
	melt_pieces.clear()
	melt_radius = 0.0


func to_local_point(world: Vector2) -> Vector2:
	return world - global_position


func _local_rect(world: Rect2) -> Rect2:
	return Rect2(to_local_point(world.position), world.size)
