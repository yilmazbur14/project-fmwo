extends Node2D

# One laser of Josh's Gun Hands (JoshGunHands): its own hit source, so the dash and the dodge judge each beam afresh
# (PlayerDefense keeps its records per source). Its band (JoshHandsLayout.gun_band) is where it hurts, what its
# telegraph draws and what the tests measure, so the three can't drift apart (the Wild Cards lanes' rule).
# The layer adds it to the SkyLayer at its muzzle, in the hazard group: its live beam draws there (z 2, under the
# hands). It puts its telegraph on the FloorLayer, under everyone and over the clones' lanes, in the hazard group too,
# and takes it with it when it goes. Everything it draws steps on the clock the layer steps it on (step()), so a pause
# or a finisher's freeze holds it:
#   step_tell()  the band's fill ramping up over the charge, and its last beat in the flash colour
#   fire()       the telegraph goes and the beam is live: it hurts (the layer tests it) until fade()
#   fade()       harmless, fading out
# The drawn beam (start, tile and end, JoshHandsLayout.final_beam, with its glow if that is in), or until then a crimson
# band with a white core and an added glow. Drawn pointing left; the left hand's is mirrored.

const Layout := preload("res://Scripts/JoshHandsLayout.gd")

# The tile's frames, cut out once each so they can repeat along a beam (region + texture repeat).
static var frame_textures := {}

var side := &"left"
var row := 0.0
var origin := Vector2.ZERO
var live := false
var fading := false
var fade_time := 0.0
var fade_clock := 0.0
var shimmer_clock := 0.0
var drawn := false
# Set before it is added: the fight that owns the hazard group, and the layer the telegraph lies on.
var fight: Node
var floor_layer: Node2D
var tell: Node2D
var tell_fill: Polygon2D
var tell_rims: Array[Line2D] = []
var visual: Node2D
var start_piece: Sprite2D
var end_piece: Sprite2D
var tile_piece: Sprite2D
var glow_piece: Sprite2D
var glow_frames := 1


static func make(beam_side: StringName, beam_row: float, muzzle: Vector2) -> Node2D:
	var beam = new()
	beam.side = beam_side
	beam.row = beam_row
	beam.origin = muzzle
	beam.name = "JoshGunBeam_%s" % beam_side
	return beam


func _ready() -> void:
	drawn = Layout.final_beam()
	visual = Node2D.new()
	visual.name = "Beam"
	visual.scale = Vector2(-1.0 if side == &"left" else 1.0, 1.0)
	visual.visible = false
	add_child(visual)
	var length := band().size.x
	if drawn:
		_build_drawn(length)
	else:
		_build_placeholder(length)
	_build_tell()


func _exit_tree() -> void:
	if is_instance_valid(tell):
		tell.queue_free()


# Where it hurts.
func band() -> Rect2:
	return Layout.gun_band(side, row)


#THE TELEGRAPH

# `progress` through the charge, and whether it is in its last beat.
func step_tell(progress: float, flash := false) -> void:
	var spec: Dictionary = Layout.GUN_TELL
	var alpha: float = spec.flash_alpha if flash else lerpf(spec.fill_from, spec.fill_to, clampf(progress, 0.0, 1.0))
	tell_fill.color = Color(spec.flash if flash else spec.fill, alpha)
	for rim in tell_rims:
		rim.default_color = spec.flash if flash else spec.rim


# A clone's lanes laid after it (the fourth clone's, mid-charge) are added over it on the floor: it goes back on top
# of them before they are ever drawn, past anything but the other beam's telegraph.
func _on_floor_child(node: Node) -> void:
	if not str(node.name).contains("JoshGunTell"):
		_keep_over_lanes.call_deferred()


func _keep_over_lanes() -> void:
	if not is_instance_valid(tell) or not tell.is_inside_tree():
		return
	var siblings := floor_layer.get_children()
	for i in range(tell.get_index() + 1, siblings.size()):
		if not str(siblings[i].name).contains("JoshGunTell"):
			floor_layer.move_child(tell, -1)
			return


func _build_tell() -> void:
	var spec: Dictionary = Layout.GUN_TELL
	var box := band()
	tell = Node2D.new()
	tell.name = "JoshGunTell_%s" % side
	tell_fill = Polygon2D.new()
	tell_fill.polygon = _rect_points(box)
	tell.add_child(tell_fill)
	for y in [box.position.y, box.end.y]:
		var rim := Line2D.new()
		rim.points = PackedVector2Array([Vector2(box.position.x, y), Vector2(box.end.x, y)])
		rim.width = spec.rim_width
		tell.add_child(rim)
		tell_rims.append(rim)
	fight.add_hazard(tell, Vector2.ZERO, floor_layer)
	floor_layer.child_entered_tree.connect(_on_floor_child)
	step_tell(0.0)


#THE BEAM

func fire() -> void:
	live = true
	tell.visible = false
	visual.visible = true


# Harmless from now, gone from view over `seconds`.
func fade(seconds: float) -> void:
	live = false
	fading = true
	fade_time = maxf(seconds, 0.001)
	fade_clock = 0.0


func step(delta: float) -> void:
	shimmer_clock += delta
	if drawn and visual.visible:
		var spec: Dictionary = Layout.GUN_BEAM
		var index := int(shimmer_clock / spec.frame_time) % int(spec.frames)
		start_piece.frame = index
		end_piece.frame = index
		tile_piece.texture = _frame_texture(spec.tile, index, spec.frame)
		if glow_piece != null:
			glow_piece.texture = _frame_texture(spec.glow, index % glow_frames, spec.glow_frame)
	if fading:
		fade_clock += delta
		visual.modulate.a = 1.0 - clampf(fade_clock / fade_time, 0.0, 1.0)


# Pointing left from the muzzle (the visual's origin) to the far rope `length` px away: start on the muzzle, end on the
# rope, the tile between, the glow along all of it.
func _build_drawn(length: float) -> void:
	var spec: Dictionary = Layout.GUN_BEAM
	var frame: Vector2 = spec.frame
	var piece_px: float = frame.x * Layout.SCALE
	if ResourceLoader.exists(spec.glow):
		var glow_sheet: Texture2D = load(spec.glow)
		var glow_frame: Vector2 = spec.glow_frame
		glow_piece = _repeat(_frame_texture(spec.glow, 0, glow_frame), length, glow_frame, spec.glow_pivot)
		glow_piece.position = Vector2(-length, 0.0)
		var added := CanvasItemMaterial.new()
		added.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		glow_piece.material = added
		glow_frames = maxi(roundi(glow_sheet.get_width() / glow_frame.x), 1)
		visual.add_child(glow_piece)
	tile_piece = _repeat(_frame_texture(spec.tile, 0, frame), maxf(length - 2.0 * piece_px, 0.0), frame, spec.tile_pivot)
	tile_piece.position = Vector2(-length + piece_px, 0.0)
	visual.add_child(tile_piece)
	start_piece = _piece(spec.start, spec.start_pivot)
	visual.add_child(start_piece)
	end_piece = _piece(spec.end, spec.end_pivot)
	end_piece.position = Vector2(-length, 0.0)
	visual.add_child(end_piece)


func _piece(path: String, pivot: Vector2) -> Sprite2D:
	var spec: Dictionary = Layout.GUN_BEAM
	var piece := Sprite2D.new()
	piece.texture = load(path)
	piece.hframes = spec.frames
	piece.scale = Vector2.ONE * Layout.SCALE
	piece.offset = spec.frame / 2.0 - pivot
	return piece


# `texture` repeated along `length` px, its pivot (on its left edge) at the sprite's origin.
func _repeat(texture: Texture2D, length: float, frame: Vector2, pivot: Vector2) -> Sprite2D:
	var width := length / Layout.SCALE
	var piece := Sprite2D.new()
	piece.texture = texture
	piece.texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
	piece.region_enabled = true
	piece.region_rect = Rect2(0.0, 0.0, width, frame.y)
	piece.scale = Vector2.ONE * Layout.SCALE
	piece.offset = Vector2(width / 2.0 - pivot.x, frame.y / 2.0 - pivot.y)
	return piece


static func _frame_texture(path: String, index: int, frame: Vector2) -> Texture2D:
	var key := "%s#%d" % [path, index]
	if not frame_textures.has(key):
		var image: Image = load(path).get_image()
		if image.is_compressed():
			image.decompress()
		var cell := Rect2i(Vector2i(roundi(index * frame.x), 0), Vector2i(frame))
		frame_textures[key] = ImageTexture.create_from_image(image.get_region(cell))
	return frame_textures[key]


func _build_placeholder(length: float) -> void:
	var spec: Dictionary = Layout.PLACEHOLDER_BEAM
	var added := CanvasItemMaterial.new()
	added.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	var glow := Polygon2D.new()
	glow.name = "Glow"
	glow.polygon = _rect_points(Rect2(-length, -spec.glow_half, length, 2.0 * spec.glow_half))
	glow.color = spec.glow
	glow.material = added
	visual.add_child(glow)
	var band_shape := Polygon2D.new()
	band_shape.name = "Band"
	band_shape.polygon = _rect_points(Rect2(-length, -Layout.BEAM_HALF, length, 2.0 * Layout.BEAM_HALF))
	band_shape.color = spec.band
	visual.add_child(band_shape)
	var core := Line2D.new()
	core.name = "Core"
	core.points = PackedVector2Array([Vector2(-length, 0.0), Vector2.ZERO])
	core.width = spec.core_width
	core.default_color = spec.core
	visual.add_child(core)


static func _rect_points(box: Rect2) -> PackedVector2Array:
	return PackedVector2Array([box.position, Vector2(box.end.x, box.position.y), box.end, Vector2(box.position.x, box.end.y)])
