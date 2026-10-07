extends Node2D

# One clone's beam in Jordan's circle (JordanComboCircle): Carter's Messatsu, drawn the way his Beam Rush draws its
# beams (CarterBeamRush, copied rather than shared so his fight stays untouched): the body is one frame of the sheet
# tiled along the axis from MESSATSU_BEAM_START and swapped for the next as it flows, the flare over its flat start and
# the head on its front end, all turned to the axis, every position whole. Its head crosses the whole beam in the
# layout's TRAVEL and it is out at full length from then. Drawing only: the attack times it and does its hit test. It
# sits on the god's Floor layer at the clone's palms, under the clones, the puppets and the player.

const CarterArtLayout := preload("res://Scripts/CarterArtLayout.gd")
const Layout := preload("res://Scripts/JordanCircleLayout.gd")

# As CarterBeamRush's: summed 1/60 s steps fall a hair short of a round number.
const CLOCK_SLACK := 0.0001

# Cut apart once for every beam: region repeat tiles a whole texture, so the sheet's frames side by side would tile
# as one.
static var body_frames: Array[Texture2D] = []

var origin := Vector2.ZERO
var angle := 0.0
var length := 0.0
var parts: Array[Node2D] = []
var flare: Node2D
var head: Node2D
var fired := false
var fading: Tween


# Along `angle` (radians) from `origin`, `length` px: built, and hidden until it fires.
func setup(from: Vector2, axis_angle: float, beam_length: float) -> void:
	origin = from.round()
	angle = axis_angle
	length = beam_length
	global_position = origin
	rotation = angle
	_build_body()
	_build_flare()
	_build_head()
	visible = false


func fire() -> void:
	fired = true
	visible = true
	step(0.0)


# `clock` seconds after it fired: the head crossing, then the whole of it out, and its sheets flowing.
func step(clock: float) -> void:
	if not fired:
		return
	var arrived := clock + CLOCK_SLACK >= Layout.TRAVEL
	var reach := length if arrived else length * clock / maxf(Layout.TRAVEL, 0.0001)
	var shown := maxf(reach - CarterArtLayout.MESSATSU_BEAM_START, 0.0)
	var spec := CarterArtLayout.messatsu_beam()
	var flow := clock if Layout.BEAM_FLOW else 0.0
	for part in parts:
		part.visible = shown > 0.0
		if spec.has("texture"):
			var tiled := part as Sprite2D
			tiled.region_rect = Rect2(CarterArtLayout.MESSATSU_BEAM_START / spec.scale, 0.0, shown / spec.scale,
				spec.frame_size.y)
			tiled.texture = body_frames[_looped_frame(spec, flow)]
		elif part.visible:
			part.scale.x = shown
	_step_sheet(flare, CarterArtLayout.messatsu_flare(), flow)
	_step_sheet(head, CarterArtLayout.messatsu_head(), clock)
	head.global_position = (origin + Vector2.from_angle(angle) * reach).round()
	head.visible = not arrived


# Out over `seconds`, and gone.
func fade(seconds: float) -> void:
	if fading != null and fading.is_valid():
		return
	fading = create_tween()
	fading.tween_property(self, "modulate:a", 0.0, maxf(seconds, 0.001))
	fading.tween_callback(queue_free)


func _build_body() -> void:
	var spec := CarterArtLayout.messatsu_beam()
	if spec.has("texture"):
		var pivot: Vector2 = spec.pivot
		var tiled := Sprite2D.new()
		tiled.name = "Body"
		tiled.texture = _beam_frames(spec)[0]
		tiled.centered = false
		tiled.offset = -pivot
		tiled.scale = Vector2.ONE * spec.scale
		tiled.region_enabled = true
		tiled.texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
		parts.append(tiled)
	else:
		for part in [[CarterArtLayout.MESSATSU_DRAW_WIDTH, spec.color], [spec.core_width, spec.core_color]]:
			var width: float = part[0]
			var quad := Polygon2D.new()
			quad.polygon = CarterArtLayout.rect_polygon(Rect2(0.0, -width / 2.0, 1.0, width))
			quad.color = part[1]
			parts.append(quad)
	for part in parts:
		part.position.x = CarterArtLayout.MESSATSU_BEAM_START
		add_child(part)


func _beam_frames(spec: Dictionary) -> Array[Texture2D]:
	if body_frames.is_empty():
		var sheet := (load(spec.texture) as Texture2D).get_image()
		var size := Vector2i(spec.frame_size)
		for k in spec.hframes:
			body_frames.append(ImageTexture.create_from_image(sheet.get_region(Rect2i(Vector2i(k * size.x, 0), size))))
	return body_frames


func _build_flare() -> void:
	var spec := CarterArtLayout.messatsu_flare()
	if spec.has("texture"):
		flare = _sheet(spec)
	else:
		flare = _ellipse(spec.radii, spec.points, spec.color)
		(flare as Polygon2D).offset = Vector2(spec.radii.x, 0.0)
	flare.name = "Flare"
	add_child(flare)


func _build_head() -> void:
	var spec := CarterArtLayout.messatsu_head()
	if spec.has("texture"):
		head = _sheet(spec)
	else:
		head = _ellipse(spec.radii, spec.points, spec.color)
	head.name = "Head"
	add_child(head)


func _ellipse(radii: Vector2, points: int, color: Color) -> Polygon2D:
	var shape := Polygon2D.new()
	shape.polygon = CarterArtLayout.ellipse(radii, points)
	shape.color = color
	return shape


# One of the sheets, its pivot texel on the origin.
func _sheet(spec: Dictionary) -> Sprite2D:
	var pivot: Vector2 = spec.pivot
	var sheet := Sprite2D.new()
	sheet.texture = load(spec.texture)
	sheet.hframes = spec.hframes
	sheet.centered = false
	sheet.offset = -pivot
	sheet.scale = Vector2.ONE * spec.scale
	return sheet


func _step_sheet(sheet: Node2D, spec: Dictionary, clock: float) -> void:
	if spec.has("texture"):
		(sheet as Sprite2D).frame = _looped_frame(spec, clock)


# The frame a looping sheet is on `clock` seconds in: `frame_time` a frame, or one of `frame_times` each.
func _looped_frame(spec: Dictionary, clock: float) -> int:
	if spec.has("frame_time"):
		return int((clock + CLOCK_SLACK) / spec.frame_time) % int(spec.hframes)
	var times: Array = spec.frame_times
	var loop := 0.0
	for time: float in times:
		loop += time
	var into := fposmod(clock + CLOCK_SLACK, loop)
	for i in times.size():
		if into < times[i]:
			return i
		into -= times[i]
	return times.size() - 1
