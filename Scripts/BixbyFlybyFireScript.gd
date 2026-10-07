extends Node2D

# One pass of beast Bixby's Flyby (BixbyBeastFlyby): the projection of where its fire will fall - the whole floor but the
# safe column at the far edge, smouldering faintly, then strongly for the warning - then the front sweeping across it at
# the pass's speed, the curtain falling at it from his mouths, the floor burning behind it for burn_time and dying down,
# and a gold rim down the column's edge throughout. The masks, the curtain and the hits all read the same four spans
# (BixbyFlybyLayout), so the fire falls exactly where the projection said. It reports its own hits, the player's hurtbox
# against the spans, as the Inferno's flood does: the curtain is bixby_flyby_breath, the floor still burning behind it
# bixby_flyby_fire, and the curtain reaching a dash's ghost is a near miss. One source for both, so a pass pays one
# PERFECT DODGE at most.
#
# The attack drives it on its own clock from the pass's projection beat (drive); let go (driven false) it plays out its
# die-down by itself. Either way it runs on physics steps, so a freeze or a pause holds it, and it frees itself once it
# has died down.

const FlybyLayout := preload("res://Scripts/BixbyFlybyLayout.gd")
const InfernoLayout := preload("res://Scripts/BixbyInfernoArtLayout.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")

# Set by the attack before it enters the tree.
var direction := 1.0
var telegraph_time := 1.0
var warn_time := 0.5
var speed := 540.0
var safe_width := 204.0
var burn_time := 0.8
var player: CharacterBody2D
var boss: Node2D

var clock := 0.0
var driven := true

var floor_layer: Node2D
var curtain_layer: Node2D
var rim_layer: Node2D
var telegraph_mask: Polygon2D
var burn_mask: Polygon2D
var die_mask: Polygon2D
var curtain_mask: Polygon2D
var curtain: Node2D
var rim: Line2D
var telegraph_tiles: Array[Sprite2D] = []
var burn_tiles: Array[Sprite2D] = []
var die_tiles: Array[Sprite2D] = []
var curtain_tiles: Array[Sprite2D] = []
# For a test: what each of its reports that wasn't ignored resolved to, {id, result, clock}.
var reports: Array[Dictionary] = []


func _ready() -> void:
	y_sort_enabled = true
	floor_layer = _layer(FlybyLayout.FLOOR_LAYER_Y)
	curtain_layer = _layer(FlybyLayout.CURTAIN_SORT_Y)
	rim_layer = _layer(FlybyLayout.RIM_SORT_Y)
	telegraph_mask = _mask(floor_layer)
	burn_mask = _mask(floor_layer)
	die_mask = _mask(floor_layer)
	telegraph_tiles = _lay_tiles(telegraph_mask)
	burn_tiles = _lay_tiles(burn_mask)
	die_tiles = _lay_tiles(die_mask)
	curtain_mask = _mask(curtain_layer)
	curtain = _lay_final_curtain() if FlybyLayout.final_curtain() else _lay_placeholder_curtain()
	rim = _lay_rim()
	drive(clock)


func _physics_process(delta: float) -> void:
	if not driven:
		drive(clock + delta)


# `t` seconds from this pass's projection: everything shown for then, the player burnt, and once it has all died down,
# gone.
func drive(t: float) -> void:
	if is_queued_for_deletion():
		return
	clock = t
	if is_spent():
		queue_free()
		return
	_set_mask(telegraph_mask, telegraph_span(), FlybyLayout.FLOOR.position.y)
	_set_mask(burn_mask, hurting_span(), FlybyLayout.FLOOR.position.y)
	_set_mask(die_mask, dying_span(), FlybyLayout.FLOOR.position.y)
	_set_mask(curtain_mask, curtain_span(), FlybyLayout.exit_y())
	_show_tiles()
	_show_curtain()
	_show_rim()
	_burn_player()


#THE SPANS

# His lead exit's line, flying on at the pass's speed after the breath stops: the curtain slides with it into the
# column's edge.
func mouth_x(t := clock) -> float:
	return _entry() + direction * speed * (t - telegraph_time)


func front_x() -> float:
	var span := _lightable()
	return clampf(mouth_x(), span.x, span.y)


# All of it before the sweep, what the front hasn't reached yet during it.
func telegraph_span() -> Vector2:
	if clock < telegraph_time:
		return _lightable()
	if clock >= sweep_end():
		return Vector2.ZERO
	return FlybyLayout.ordered(front_x(), _safe_edge())


func curtain_span() -> Vector2:
	if clock < telegraph_time:
		return Vector2.ZERO
	var mouth := mouth_x()
	return _clip(FlybyLayout.ordered(mouth - direction * FlybyLayout.CURTAIN_WIDTH, mouth))


func hurting_span() -> Vector2:
	if clock < telegraph_time:
		return Vector2.ZERO
	return _clip(FlybyLayout.ordered(mouth_x(clock - burn_time), front_x()))


# Only a look: the floor's die-down, after it stops hurting.
func dying_span() -> Vector2:
	if clock < telegraph_time:
		return Vector2.ZERO
	var tail := mouth_x(clock - burn_time)
	return _clip(FlybyLayout.ordered(mouth_x(clock - burn_time - InfernoLayout.FLOOD_DIE_TIME), tail))


func sweep_end() -> float:
	return telegraph_time + FlybyLayout.sweep_time(safe_width, speed)


func is_warning() -> bool:
	return clock < sweep_end()


func is_hurting() -> bool:
	return not FlybyLayout.span_empty(hurting_span())


func is_spent() -> bool:
	return clock >= sweep_end() + burn_time + InfernoLayout.FLOOD_DIE_TIME


func _entry() -> float:
	return FlybyLayout.entry_x(direction)


func _safe_edge() -> float:
	return FlybyLayout.safe_edge(direction, safe_width)


func _lightable() -> Vector2:
	return FlybyLayout.lightable(direction, safe_width)


func _clip(span: Vector2) -> Vector2:
	var lit := _lightable()
	return Vector2(maxf(span.x, lit.x), minf(span.y, lit.y))


#THE HITS

# It covers most of the floor, so it tests the player's box against the spans directly rather than through an area.
func _burn_player() -> void:
	if not is_instance_valid(player):
		return
	var box := _rect_of(player.hurtBox)
	var falling := curtain_span()
	if FlybyLayout.span_touches(box, falling):
		_report(FlybyLayout.BREATH_ID)
	elif FlybyLayout.span_touches(box, hurting_span()):
		_report(FlybyLayout.FIRE_ID)
	elif player.dodge_ghost_position() != Vector2.INF and FlybyLayout.span_touches(_rect_of(player.dodge_ghost), falling):
		player.receive_near_miss(_hit(FlybyLayout.BREATH_ID))


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

func _layer(y: float) -> Node2D:
	var layer := Node2D.new()
	layer.position = Vector2(0, y)
	add_child(layer)
	return layer


# Draws nothing itself, and cuts whatever is put under it to the rect _set_mask gives it.
func _mask(layer: Node2D) -> Polygon2D:
	var mask := Polygon2D.new()
	mask.clip_children = CanvasItem.CLIP_CHILDREN_ONLY
	layer.add_child(mask)
	return mask


func _set_mask(mask: Polygon2D, span: Vector2, top: float) -> void:
	mask.visible = not FlybyLayout.span_empty(span)
	if not mask.visible:
		return
	var y := (mask.get_parent() as Node2D).position.y
	mask.polygon = PackedVector2Array([Vector2(span.x, top - y), Vector2(span.y, top - y),
		Vector2(span.y, FlybyLayout.FLOOR.end.y - y), Vector2(span.x, FlybyLayout.FLOOR.end.y - y)])


# The Inferno flood's tiles on its grid (BixbyInfernoFloodScript._lay_final), on every bed this pass can light.
func _lay_tiles(mask: Polygon2D) -> Array[Sprite2D]:
	var spec := InfernoLayout.FINAL_FLOOD
	var area := InfernoLayout.INFERNO_AREA
	var sheet: Texture2D = load(spec.sheet)
	var bed := InfernoLayout.FLOOD_TILE * InfernoLayout.SCALE
	var rise := (InfernoLayout.FLOOD_FRAME_SIZE.y - InfernoLayout.FLOOD_TILE.y) * InfernoLayout.SCALE
	var lit := _lightable()
	var layer_y := (mask.get_parent() as Node2D).position.y
	var laid: Array[Sprite2D] = []
	for row in InfernoLayout.FLOOD_GRID.y:
		for column in InfernoLayout.FLOOD_GRID.x:
			var cell := Rect2(area.position + Vector2(column * bed.x, row * bed.y), bed)
			if cell.position.x >= lit.y or cell.end.x <= lit.x:
				continue
			var tile := Sprite2D.new()
			tile.texture = sheet
			tile.hframes = roundi(sheet.get_width() / InfernoLayout.FLOOD_FRAME_SIZE.x)
			tile.centered = false
			tile.scale = Vector2.ONE * InfernoLayout.SCALE
			tile.position = cell.position - Vector2(0, layer_y + rise)
			mask.add_child(tile)
			laid.append(tile)
	return laid


# Neighbouring tiles start their loops on different frames, so the floor doesn't flicker in step. A dying tile shows
# how long its middle has been dying.
func _show_tiles() -> void:
	var spec := InfernoLayout.FINAL_FLOOD
	if telegraph_mask.visible:
		var strong := clock >= telegraph_time - warn_time
		var frame_time: float = spec.warn_frame_time if strong else spec.frame_time
		var step := int((clock - (telegraph_time - warn_time) if strong else clock) / frame_time)
		var smoulder: Array = spec.smoulder
		for i in telegraph_tiles.size():
			telegraph_tiles[i].frame = smoulder[(step + i) % smoulder.size()]
			telegraph_tiles[i].modulate.a = 1.0 if strong else spec.faint_alpha
	if burn_mask.visible:
		var step := int((clock - telegraph_time) / spec.frame_time)
		var burn: Array = spec.burn
		for i in burn_tiles.size():
			burn_tiles[i].frame = burn[(step + i) % burn.size()]
	if die_mask.visible:
		var die: Array = spec.die
		var half_bed := InfernoLayout.FLOOD_TILE.x * InfernoLayout.SCALE / 2.0
		for tile in die_tiles:
			var dying := clock - burn_time - telegraph_time - absf(tile.position.x + half_bed - _entry()) / speed
			tile.frame = die[clampi(int(dying / (InfernoLayout.FLOOD_DIE_TIME / die.size())), 0, die.size() - 1)]


# Down from the height his mouths cross at to the floor's bottom edge, over all this pass can light: the mask cuts it
# to the curtain's span.
func _lay_placeholder_curtain() -> Node2D:
	var look := FlybyLayout.PLACEHOLDER_CURTAIN
	var lit := _lightable()
	var top := FlybyLayout.exit_y() - curtain_layer.position.y
	var bottom := FlybyLayout.FLOOR.end.y - curtain_layer.position.y
	var fall := Polygon2D.new()
	fall.polygon = PackedVector2Array([Vector2(lit.x, top), Vector2(lit.y, top), Vector2(lit.y, bottom), Vector2(lit.x, bottom)])
	fall.vertex_colors = PackedColorArray([look.top, look.top, look.bottom, look.bottom])
	curtain_mask.add_child(fall)
	return fall


# A column of the curtain's frames stacked from his mouths' height down to the floor's bottom edge, moved with the mouth.
func _lay_final_curtain() -> Node2D:
	var holder := Node2D.new()
	curtain_mask.add_child(holder)
	var sheet: Texture2D = load(FlybyLayout.CURTAIN_SHEET)
	var frame: Vector2 = FlybyLayout.CURTAIN.frame
	var y := FlybyLayout.exit_y() - curtain_layer.position.y
	var bottom := FlybyLayout.FLOOR.end.y - curtain_layer.position.y
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
	if not curtain_mask.visible:
		return
	if curtain_tiles.is_empty():
		var look := FlybyLayout.PLACEHOLDER_CURTAIN
		curtain.modulate.a = 1.0 - look.pulse * (0.5 + 0.5 * sin(clock * TAU * look.rate))
		return
	var mouth := mouth_x()
	curtain.position.x = mouth - FlybyLayout.CURTAIN_WIDTH if direction > 0.0 else mouth
	var spec := FlybyLayout.CURTAIN
	var frame := int(clock / spec.frame_time) % int(spec.frames)
	for piece in curtain_tiles:
		piece.frame = frame


func _lay_rim() -> Line2D:
	var line := Line2D.new()
	var x := _safe_edge()
	var y := rim_layer.position.y
	line.points = PackedVector2Array([Vector2(x, FlybyLayout.FLOOR.position.y - y), Vector2(x, FlybyLayout.FLOOR.end.y - y)])
	line.width = FlybyLayout.RIM.width
	rim_layer.add_child(line)
	return line


func _show_rim() -> void:
	var look := FlybyLayout.RIM
	var colour: Color = look.colour
	var hurting_until := sweep_end() + burn_time
	if clock < telegraph_time - warn_time:
		colour.a = look.faint_alpha
	elif clock < hurting_until:
		colour.a = 1.0
	else:
		colour.a = maxf(1.0 - (clock - hurting_until) / look.fade_time, 0.0)
	rim.default_color = colour
