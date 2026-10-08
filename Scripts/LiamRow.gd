extends Node2D

# Liam's wall of pillars (addendum 3, A): ROW_PER_SIDE shorter neighbours each side of his own pillar (LiamPillar), all on
# his floor line, and one solid band over the whole width (ROW_BAND), so nobody gets round him or even next to him. Only
# his own pillar is hittable, and only from the front spot (LiamStateMachine.FRONT_SPOT): the neighbours are pictures.
# LiamScript builds it in _build_stage as body.row, a child of his scene, so its pillars sort with everyone. It rises at
# the takeover's ride and at the end of his get-up, and crumbles with him when he's toppled and at the fight's end.
# Everything it times is node-bound, so a pause and a finisher's freeze hold it.

const Layout := preload("res://Scripts/LiamArtLayout.gd")

var body: StaticBody2D
var body_shape: CollisionShape2D
var up := false
var pillars: Array[Node2D] = []
# Per pillar: how far out from his own it stands (1 is his neighbour), how far up it is, and how far through its crumble
# (below 0 while it isn't crumbling).
var steps_out: Array[int] = []
var risen: Array[float] = []
var crumbled: Array[float] = []
var columns: Array[Node2D] = []
var masks: Array[Polygon2D] = []
var sheets: Array[Sprite2D] = []
var tweens: Array[Tween] = []
var stand_clock := 0.0


func _ready() -> void:
	y_sort_enabled = true
	global_position = Vector2.ZERO
	_build_band()
	for side: float in [-1.0, 1.0]:
		for k in range(1, Layout.ROW_PER_SIDE + 1):
			_build_pillar(k, side)
	visible = false


func _process(delta: float) -> void:
	if up and not sheets.is_empty():
		stand_clock += delta
		for i in pillars.size():
			if risen[i] >= 1.0:
				_show(i)


func is_up() -> bool:
	return up


func band() -> Rect2:
	return Layout.ROW_BAND


# Out of the floor over `time`, rippling out from his pillar: pillar k starts (k - 1) * `ripple` in and takes the rest,
# so the outermost lands on `time`. Solid from the first frame, once a player in its way is put in front of it.
# Awaitable.
func rise(time: float, ripple: float) -> void:
	_kill()
	up = true
	visible = true
	_nudge_player()
	body_shape.set_deferred("disabled", false)
	if time <= 0.0:
		stand_up_now()
		return
	var each := maxf(time - (Layout.ROW_PER_SIDE - 1) * ripple, 0.01)
	var last: Tween
	for i in pillars.size():
		risen[i] = 0.0
		crumbled[i] = -1.0
		_show(i)
		var tween := create_tween()
		if steps_out[i] > 1:
			tween.tween_interval((steps_out[i] - 1) * ripple)
		tween.tween_method(_set_risen.bind(i), 0.0, 1.0, each)
		tweens.append(tween)
		last = tween
	await last.finished


# Fully up at once.
func stand_up_now() -> void:
	_kill()
	up = true
	visible = true
	_nudge_player()
	body_shape.set_deferred("disabled", false)
	for i in pillars.size():
		risen[i] = 1.0
		crumbled[i] = -1.0
		_show(i)


# Into the floor over `time`, rippling out ROW_CRUMBLE_RIPPLE a pillar; nothing solid from the first frame.
func crumble(time: float) -> void:
	if not up:
		return
	_kill()
	up = false
	body_shape.set_deferred("disabled", true)
	var last: Tween
	for i in pillars.size():
		var tween := create_tween()
		if steps_out[i] > 1:
			tween.tween_interval((steps_out[i] - 1) * Layout.ROW_CRUMBLE_RIPPLE)
		tween.tween_method(_set_crumbled.bind(i), 0.0, 1.0, maxf(time, 0.01))
		tweens.append(tween)
		last = tween
	last.tween_callback(hide)


#BUILDING IT

func _build_band() -> void:
	body = StaticBody2D.new()
	body.name = "Band"
	body.collision_layer = 1
	body.collision_mask = 0
	body_shape = CollisionShape2D.new()
	var rect := RectangleShape2D.new()
	rect.size = Layout.ROW_BAND.size
	body_shape.shape = rect
	body_shape.position = Layout.ROW_BAND.get_center()
	body_shape.disabled = true
	body.add_child(body_shape)
	add_child(body)


func _build_pillar(k: int, side: float) -> void:
	var pillar := Node2D.new()
	pillar.name = "RowPillar%s%d" % ["L" if side < 0.0 else "R", k]
	pillar.position = Vector2(960.0 + side * Layout.ROW_SPACING * k, Layout.ROW_Y)
	add_child(pillar)
	pillars.append(pillar)
	steps_out.append(k)
	risen.append(0.0)
	crumbled.append(-1.0)
	if Layout.final_row():
		var sheet := Sprite2D.new()
		var texture: Texture2D = load(Layout.ROW_RISE_SHEET)
		sheet.texture = texture
		sheet.hframes = Layout.strip_count(Layout.ROW_RISE_SHEET, Layout.ROW_FRAME)
		sheet.vframes = _rows(sheet)
		sheet.scale = Vector2.ONE * Layout.SCALE
		sheet.offset = Layout.ROW_FRAME / 2.0 - Layout.PILLAR_PIVOT
		pillar.add_child(sheet)
		sheets.append(sheet)
		return
	# LiamPillar's stand-in column, ROW_STAND_TEXELS tall under its slab, without runes, sliding up out of the floor.
	var look: Dictionary = Layout.PLACEHOLDER_PILLAR
	var s := Layout.SCALE
	var tall := float(Layout.ROW_STAND_TEXELS)
	var column := Node2D.new()
	pillar.add_child(column)
	var mask := Polygon2D.new()
	mask.polygon = Layout.rect_polygon(Rect2(-40 * s, -(tall + 12.0) * s, 80 * s, (tall + 12.0) * s))
	mask.clip_children = CanvasItem.CLIP_CHILDREN_ONLY
	column.add_child(mask)
	var half: float = look.width / 2.0 * s
	var face := Polygon2D.new()
	face.polygon = Layout.rect_polygon(Rect2(-half, -(tall - 4.0) * s, half * 2.0, (tall - 4.0) * s))
	face.color = look.stone
	mask.add_child(face)
	var shade := Polygon2D.new()
	shade.polygon = Layout.rect_polygon(Rect2(half - 6 * s, -(tall - 4.0) * s, 6 * s, (tall - 4.0) * s))
	shade.color = look.stone_dark
	mask.add_child(shade)
	var outline := Line2D.new()
	outline.points = face.polygon
	outline.closed = true
	outline.width = s
	outline.default_color = look.edge
	mask.add_child(outline)
	var cap_half: float = look.cap_width / 2.0 * s
	var cap := Polygon2D.new()
	cap.polygon = Layout.rect_polygon(Rect2(-cap_half, -(tall + 8.0) * s, cap_half * 2.0, look.cap_height * s))
	cap.color = look.cap
	mask.add_child(cap)
	var cap_outline := Line2D.new()
	cap_outline.points = cap.polygon
	cap_outline.closed = true
	cap_outline.width = s
	cap_outline.default_color = look.edge
	mask.add_child(cap_outline)
	columns.append(column)
	masks.append(mask)


#DRAWING IT

func _set_risen(value: float, i: int) -> void:
	risen[i] = value
	_show(i)


func _set_crumbled(value: float, i: int) -> void:
	crumbled[i] = value
	_show(i)


func _show(i: int) -> void:
	if not sheets.is_empty():
		var sheet := sheets[i]
		var variant := steps_out[i] % _rows(sheet)
		if crumbled[i] >= 0.0:
			var count := _use_strip(sheet, Layout.ROW_CRUMBLE_SHEET)
			_show_frame(sheet, Layout.frame_at(Layout.ROW_CRUMBLE_TIMES, count, crumbled[i]), variant)
		elif risen[i] < 1.0:
			var count := _use_strip(sheet, Layout.ROW_RISE_SHEET)
			_show_frame(sheet, Layout.frame_at(Layout.ROW_RISE_TIMES, count, risen[i]), variant)
		else:
			var count := _use_strip(sheet, Layout.ROW_STAND_SHEET)
			_show_frame(sheet, int(stand_clock / Layout.ROW_STAND_FRAME_TIME) % count, variant)
		return
	# The stand-in column slides out of the floor easing in to its stop, and back into it gathering speed.
	var up_by: float = 1.0 - crumbled[i] * crumbled[i] if crumbled[i] >= 0.0 else 1.0 - pow(1.0 - risen[i], 2.0)
	var column := columns[i]
	column.position.y = roundf((1.0 - up_by) * (Layout.ROW_STAND_TEXELS + 8.0) * Layout.SCALE)
	masks[i].position.y = -column.position.y


# The strip at `path` on `sheet` (swapped in if it isn't already): how many frames it holds.
func _use_strip(sheet: Sprite2D, path: String) -> int:
	if sheet.texture.resource_path != path:
		sheet.frame = 0
		sheet.texture = load(path)
		sheet.hframes = Layout.strip_count(path, Layout.ROW_FRAME)
		sheet.vframes = _rows(sheet)
	return sheet.hframes


func _show_frame(sheet: Sprite2D, frame: int, variant: int) -> void:
	sheet.frame_coords = Vector2i(mini(frame, sheet.hframes - 1), mini(variant, sheet.vframes - 1))


func _rows(sheet: Sprite2D) -> int:
	return maxi(roundi(sheet.texture.get_height() / Layout.ROW_FRAME.y), 1)


func _nudge_player() -> void:
	var scene := get_tree().current_scene
	var player: Node2D = scene.get_node_or_null("Arena/MainPlayer/CharacterBody2D") if scene else null
	if player == null:
		return
	var shape: CollisionShape2D = player.get_node("CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	var face := Layout.ROW_BAND.end.y
	if box.position.y >= face:
		return
	player.global_position.y += face + Layout.ROW_NUDGE_GAP - box.position.y


func _kill() -> void:
	for tween in tweens:
		if tween.is_valid():
			tween.kill()
	tweens.clear()
