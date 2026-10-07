extends Node2D

# The fire result's one pass in Jordan's Elemental Wheel (JordanComboWheel; every number JordanWheelLayout's): Bixby's
# Flyby fire (BixbyFlybyFireScript's pattern) over the god fight's whole floor but one column - the gap Liam's wind holds
# open - which sits off the player. The projection of where it will fall, faintly then strongly for the warning, a gold
# rim down both of the column's edges; then the front sweeping across from the entry wall at `speed`, the curtain falling
# at it from his mouths except over the column, the floor burning behind it for `burn_time` and dying down.
#
# Every look and every hit reads the same spans, each cut to the floor either side of the column, so the fire falls
# exactly where the projection said. It reports its own hits, the player's hurtbox against the spans: the curtain
# jordan_wheel_breath, the floor still burning behind it jordan_wheel_fire, and the curtain reaching only a dash's ghost a
# near miss, once a pass. Its node is the world's origin on the Floor layer, under everyone.
#
# The attack drives it on its own clock from the projection (drive); let go (driven false) it plays out its die-down by
# itself on physics steps and frees itself once it has died down.

const Layout := preload("res://Scripts/JordanWheelLayout.gd")
const FlybyLayout := preload("res://Scripts/BixbyFlybyLayout.gd")
const InfernoLayout := preload("res://Scripts/BixbyInfernoArtLayout.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")

# Set by the attack before it enters the tree.
var direction := 1.0
var column := Vector2.ZERO
var telegraph_time := Layout.T_PROJ
var warn_time := Layout.WARN
var speed := Layout.FRONT_SPEED
var burn_time := Layout.BURN
var player: CharacterBody2D
var boss: Node2D

var clock := 0.0
var driven := true
var near_missed := false
# For a test: what each of its reports that wasn't ignored resolved to, {id, result, clock}.
var reports: Array[Dictionary] = []

# Per side of the column (0 the floor left of it, 1 right): its x span, and its masks and their tiles.
var pieces: Array[Vector2] = []
var telegraph_masks: Array[Polygon2D] = []
var burn_masks: Array[Polygon2D] = []
var die_masks: Array[Polygon2D] = []
var curtain_masks: Array[Polygon2D] = []
var curtains: Array[Node2D] = []
var telegraph_tiles: Array = []
var burn_tiles: Array = []
var die_tiles: Array = []
var curtain_tiles: Array[Sprite2D] = []
var rims: Array[Line2D] = []


func _ready() -> void:
	var floor_rect: Rect2 = Layout.FLOOR
	pieces = [Vector2(floor_rect.position.x, column.x), Vector2(column.y, floor_rect.end.x)]
	for piece in pieces:
		telegraph_masks.append(_mask())
		burn_masks.append(_mask())
		die_masks.append(_mask())
	for i in pieces.size():
		telegraph_tiles.append(_lay_tiles(telegraph_masks[i], pieces[i]))
		burn_tiles.append(_lay_tiles(burn_masks[i], pieces[i]))
		die_tiles.append(_lay_tiles(die_masks[i], pieces[i]))
	for i in pieces.size():
		curtain_masks.append(_mask())
		curtains.append(_lay_curtain(curtain_masks[i]))
	for x: float in [column.x, column.y]:
		rims.append(_lay_rim(x))
	drive(clock)


func _physics_process(delta: float) -> void:
	if not driven:
		drive(clock + delta)


# `t` seconds from the projection: everything shown for then, the player burnt, and once it has all died down, gone.
func drive(t: float) -> void:
	if is_queued_for_deletion():
		return
	clock = t
	if is_spent():
		queue_free()
		return
	for i in pieces.size():
		_set_mask(telegraph_masks[i], _cut(telegraph_span(), i), Layout.FLOOR.position.y)
		_set_mask(burn_masks[i], _cut(hurting_span(), i), Layout.FLOOR.position.y)
		_set_mask(die_masks[i], _cut(dying_span(), i), Layout.FLOOR.position.y)
		_set_mask(curtain_masks[i], _cut(curtain_span(), i), Layout.mouth_y())
	_show_tiles()
	_show_curtain()
	_show_rims()
	_burn_player()


#THE SPANS (world x: Vector2(lo, hi), empty once lo >= hi)

func entry() -> float:
	return Layout.entry_x(direction)


func mouth_x(t := clock) -> float:
	return entry() + direction * speed * (t - telegraph_time)


func front_x() -> float:
	return clampf(mouth_x(), Layout.FLOOR.position.x, Layout.FLOOR.end.x)


func far_x() -> float:
	return Layout.FLOOR.end.x if direction > 0.0 else Layout.FLOOR.position.x


func telegraph_span() -> Vector2:
	if clock < telegraph_time:
		return Vector2(Layout.FLOOR.position.x, Layout.FLOOR.end.x)
	if clock >= sweep_end():
		return Vector2.ZERO
	return FlybyLayout.ordered(front_x(), far_x())


func curtain_span() -> Vector2:
	if clock < telegraph_time:
		return Vector2.ZERO
	var mouth := mouth_x()
	return _on_floor(FlybyLayout.ordered(mouth - direction * Layout.CURTAIN_W, mouth))


func hurting_span() -> Vector2:
	if clock < telegraph_time:
		return Vector2.ZERO
	return _on_floor(FlybyLayout.ordered(mouth_x(clock - burn_time), front_x()))


func dying_span() -> Vector2:
	if clock < telegraph_time:
		return Vector2.ZERO
	var tail := mouth_x(clock - burn_time)
	return _on_floor(FlybyLayout.ordered(mouth_x(clock - burn_time - Layout.DIE_TIME), tail))


func sweep_end() -> float:
	return telegraph_time + Layout.FLOOR.size.x / speed


func is_hurting() -> bool:
	return clock >= telegraph_time and clock < sweep_end() + burn_time


func is_spent() -> bool:
	return clock >= sweep_end() + burn_time + Layout.DIE_TIME


func _on_floor(span: Vector2) -> Vector2:
	return Vector2(maxf(span.x, Layout.FLOOR.position.x), minf(span.y, Layout.FLOOR.end.x))


# A span cut to one side of the column.
func _cut(span: Vector2, i: int) -> Vector2:
	return Vector2(maxf(span.x, pieces[i].x), minf(span.y, pieces[i].y))


#THE HITS

func _burn_player() -> void:
	if not is_instance_valid(player):
		return
	var box := _rect_of(player.hurtBox)
	if _touches_any(box, curtain_span()):
		_report(Layout.BREATH_ID)
	elif _touches_any(box, hurting_span()):
		_report(Layout.FIRE_ID)
	elif not near_missed and player.dodge_ghost_position() != Vector2.INF \
			and _touches_any(_rect_of(player.dodge_ghost), curtain_span()):
		near_missed = true
		player.receive_near_miss(_hit(Layout.BREATH_ID))


func _touches_any(rect: Rect2, span: Vector2) -> bool:
	for i in pieces.size():
		var cut := _cut(span, i)
		if not FlybyLayout.span_empty(cut) and rect.position.x < cut.y and rect.end.x > cut.x \
				and rect.position.y < Layout.FLOOR.end.y and rect.end.y > Layout.FLOOR.position.y:
			return true
	return false


func _report(id: StringName) -> void:
	var result: int = player.receive_hit(_hit(id))
	if result != HitInfo.Result.IGNORED:
		reports.append({"id": id, "result": result, "clock": clock})


func _rect_of(area: Area2D) -> Rect2:
	var shape: CollisionShape2D = area.get_node("CollisionShape2D")
	return shape.global_transform * shape.shape.get_rect()


func _hit(id: StringName) -> RefCounted:
	return HitInfo.make(id, self, Vector2(front_x(), player.global_position.y), boss)


#THE LOOK

# Draws nothing itself, and cuts whatever is put under it to the rect _set_mask gives it.
func _mask() -> Polygon2D:
	var mask := Polygon2D.new()
	mask.clip_children = CanvasItem.CLIP_CHILDREN_ONLY
	add_child(mask)
	return mask


func _set_mask(mask: Polygon2D, span: Vector2, top: float) -> void:
	mask.visible = not FlybyLayout.span_empty(span)
	if not mask.visible:
		return
	mask.polygon = PackedVector2Array([Vector2(span.x, top), Vector2(span.y, top), Vector2(span.y, Layout.FLOOR.end.y),
		Vector2(span.x, Layout.FLOOR.end.y)])


# The Inferno flood's tiles over one side's floor, or its flat stand-in until the sheet is in.
func _lay_tiles(mask: Polygon2D, piece: Vector2) -> Array:
	var laid: Array = []
	if piece.x >= piece.y:
		return laid
	if not ResourceLoader.exists(InfernoLayout.FINAL_FLOOD.sheet):
		var flat := Polygon2D.new()
		flat.polygon = PackedVector2Array([Vector2(piece.x, Layout.FLOOR.position.y), Vector2(piece.y, Layout.FLOOR.position.y),
			Vector2(piece.y, Layout.FLOOR.end.y), Vector2(piece.x, Layout.FLOOR.end.y)])
		mask.add_child(flat)
		laid.append(flat)
		return laid
	var sheet: Texture2D = load(InfernoLayout.FINAL_FLOOD.sheet)
	var bed := InfernoLayout.FLOOD_TILE * InfernoLayout.SCALE
	var rise := (InfernoLayout.FLOOD_FRAME_SIZE.y - InfernoLayout.FLOOD_TILE.y) * InfernoLayout.SCALE
	var y: float = Layout.FLOOR.position.y
	while y < Layout.FLOOR.end.y:
		var x: float = Layout.FLOOR.position.x
		while x < Layout.FLOOR.end.x:
			if x + bed.x > piece.x and x < piece.y:
				var tile := Sprite2D.new()
				tile.texture = sheet
				tile.hframes = roundi(sheet.get_width() / InfernoLayout.FLOOD_FRAME_SIZE.x)
				tile.centered = false
				tile.scale = Vector2.ONE * InfernoLayout.SCALE
				tile.position = Vector2(x, y - rise)
				mask.add_child(tile)
				laid.append(tile)
			x += bed.x
		y += bed.y
	return laid


# Neighbouring tiles start their loops on different frames, so the floor doesn't flicker in step. A dying tile shows
# how long its middle has been dying.
func _show_tiles() -> void:
	var spec := InfernoLayout.FINAL_FLOOD
	var look := InfernoLayout.PLACEHOLDER_FLOOD
	var strong := clock >= telegraph_time - warn_time
	for i in pieces.size():
		if telegraph_masks[i].visible:
			var frame_time: float = spec.warn_frame_time if strong else spec.frame_time
			var step := int((clock - (telegraph_time - warn_time) if strong else clock) / frame_time)
			for k in telegraph_tiles[i].size():
				var tile = telegraph_tiles[i][k]
				if tile is Sprite2D:
					tile.frame = spec.smoulder[(step + k) % spec.smoulder.size()]
					tile.modulate.a = 1.0 if strong else spec.faint_alpha
				else:
					tile.color = look.warn_peak if strong else look.faint
		if burn_masks[i].visible:
			var step := int((clock - telegraph_time) / spec.frame_time)
			for k in burn_tiles[i].size():
				var tile = burn_tiles[i][k]
				if tile is Sprite2D:
					tile.frame = spec.burn[(step + k) % spec.burn.size()]
				else:
					tile.color = look.burn
		if die_masks[i].visible:
			for tile in die_tiles[i]:
				if tile is Sprite2D:
					var middle: float = tile.position.x + InfernoLayout.FLOOD_TILE.x * InfernoLayout.SCALE / 2.0
					var dying := clock - burn_time - telegraph_time - absf(middle - entry()) / speed
					tile.frame = spec.die[clampi(int(dying / (Layout.DIE_TIME / spec.die.size())), 0, spec.die.size() - 1)]
				else:
					tile.color = look.die


# The curtain: its frames stacked from his mouths' height to the floor's bottom edge, moved with the mouth; the
# stand-in a gradient.
func _lay_curtain(mask: Polygon2D) -> Node2D:
	var holder := Node2D.new()
	mask.add_child(holder)
	var top := Layout.mouth_y()
	var bottom: float = Layout.FLOOR.end.y
	if not FlybyLayout.final_curtain():
		var look: Dictionary = Layout.PLACEHOLDER_CURTAIN
		var fall := Polygon2D.new()
		fall.polygon = PackedVector2Array([Vector2(0, top), Vector2(Layout.CURTAIN_W, top), Vector2(Layout.CURTAIN_W, bottom),
			Vector2(0, bottom)])
		fall.vertex_colors = PackedColorArray([look.top, look.top, look.bottom, look.bottom])
		holder.add_child(fall)
		return holder
	var sheet: Texture2D = load(FlybyLayout.CURTAIN_SHEET)
	var frame: Vector2 = FlybyLayout.CURTAIN.frame
	var y := top
	while y < bottom:
		var piece := Sprite2D.new()
		piece.texture = sheet
		piece.hframes = roundi(sheet.get_width() / frame.x)
		piece.centered = false
		piece.flip_h = direction < 0.0
		piece.scale = Vector2.ONE * FlybyLayout.SCALE
		piece.position = Vector2(0, y)
		holder.add_child(piece)
		curtain_tiles.append(piece)
		y += frame.y * FlybyLayout.SCALE
	return holder


func _show_curtain() -> void:
	var mouth := mouth_x()
	for holder in curtains:
		holder.position.x = mouth - Layout.CURTAIN_W if direction > 0.0 else mouth
	if curtain_tiles.is_empty():
		var look: Dictionary = Layout.PLACEHOLDER_CURTAIN
		for holder in curtains:
			holder.modulate.a = 1.0 - look.pulse * (0.5 + 0.5 * sin(clock * TAU * look.rate))
		return
	var spec := FlybyLayout.CURTAIN
	var frame := int(clock / spec.frame_time) % int(spec.frames)
	for piece in curtain_tiles:
		piece.frame = frame


func _lay_rim(x: float) -> Line2D:
	var line := Line2D.new()
	line.points = PackedVector2Array([Vector2(x, Layout.FLOOR.position.y), Vector2(x, Layout.FLOOR.end.y)])
	line.width = Layout.RIM.width
	add_child(line)
	return line


# Faint with the faint projection, full from the warning until the pass's fire stops hurting, then faded out.
func _show_rims() -> void:
	var look: Dictionary = Layout.RIM
	var colour: Color = look.colour
	var hurting_until := sweep_end() + burn_time
	if clock < telegraph_time - warn_time:
		colour.a = look.faint_alpha
	elif clock < hurting_until:
		colour.a = 1.0
	else:
		colour.a = maxf(1.0 - (clock - hurting_until) / look.fade_time, 0.0)
	for rim in rims:
		rim.default_color = colour
