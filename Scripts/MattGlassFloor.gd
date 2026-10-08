extends Node2D

# The Glass Row's floor, on Matt's FloorLayer under both fighters: the bed of glass over the glass band,
# built as segments that start clear and fade in as the shards falling on them land, and the code-drawn
# lane and row guides. It only draws; MattGlassRow decides when and where things fall, off the fight's
# seeded rng. Only the landing ping's pitch is left to chance here.
#
# Falling shards are drawn on the layer handed to build() - over both fighters - and are hazards in their
# own right, so the end of the fight frees them mid-fall. A segment is the band cut at whole texels, so
# the drawn tile never lands between two screen texels.

const MattArtLayout := preload("res://Scripts/MattArtLayout.gd")

const SHARD_FROM_Y := -60.0
const SEGMENT_FADE := 0.12
const CLEAR_STAGGER := 0.03
# A glint catches the new glass just above where each shard lands.
const GLINT_OFFSET := Vector2(9, -12)

var band := Rect2()
var body: Node
var shard_layer: Node2D
var hazard_group := ""
var segments: Array[CanvasItem] = []
var rects: Array[Rect2] = []
var revealed: Array[bool] = []
# Where the segments of the bed's top row start: the ones a row grown in front of them covers the edge of.
var top_first := 0
var guides: Node2D
var guide_spec: Dictionary
var guide_fade: Tween
# Shards still falling. They hang off another layer, so the floor takes them with it when it goes.
var shards: Array[Node2D] = []
# Every landing point so far, for a test; and whether the floor is on its way out.
var landings: Array[Vector2] = []
var clearing := false


# `count` segments across `band`, the shards falling on `shards_on`; `owner_body` plays the sounds and
# `group` is the group the falling shards join.
func build(glass_band: Rect2, count: int, shards_on: Node2D, owner_body: Node, group: String) -> void:
	band = glass_band
	shard_layer = shards_on
	body = owner_body
	hazard_group = group
	var texels := roundi(band.size.x / MattArtLayout.SCALE)
	for i in count:
		var from := roundi(float(texels) * i / count)
		var to := roundi(float(texels) * (i + 1) / count)
		var rect := Rect2(band.position.x + from * MattArtLayout.SCALE, band.position.y,
			(to - from) * MattArtLayout.SCALE, band.size.y)
		rects.append(rect)
		revealed.append(false)
		var segment := _build_segment(i, rect)
		segment.modulate.a = 0.0
		add_child(segment)
		segments.append(segment)


func _exit_tree() -> void:
	for shard in shards:
		if is_instance_valid(shard):
			shard.queue_free()
	shards.clear()


func segment_rects() -> Array[Rect2]:
	return rects


func revealed_count() -> int:
	return revealed.count(true)


# The segment a point lies in, the newest row's first; shards only ever land inside one.
func segment_at(at: Vector2) -> int:
	for i in range(rects.size() - 1, -1, -1):
		if rects[i].has_point(at):
			return i
	return rects.size() - 1


# One more row of glass in front of the bed, `count` segments across `row_band`, their rects returned. Each
# is drawn on down over the bed's old jagged edge, which is trimmed off the row it was on, so the two read
# as one bed; the new segments start clear, for the shards falling on them to fill in.
func grow(row_band: Rect2, count: int) -> Array[Rect2]:
	var cover := 0.0
	if MattArtLayout.uses_final_fx(&"glass_floor"):
		var edge: int = MattArtLayout.fx(&"glass_floor").edge
		cover = edge * MattArtLayout.SCALE
		for i in range(top_first, segments.size()):
			var tile := segments[i] as Sprite2D
			tile.position.y += cover
			tile.region_rect = Rect2(tile.region_rect.position + Vector2(0, edge), tile.region_rect.size - Vector2(0, edge))
	band = band.merge(row_band)
	top_first = segments.size()
	var added: Array[Rect2] = []
	var texels := roundi(row_band.size.x / MattArtLayout.SCALE)
	for i in count:
		var from := roundi(float(texels) * i / count)
		var to := roundi(float(texels) * (i + 1) / count)
		var rect := Rect2(row_band.position.x + from * MattArtLayout.SCALE, row_band.position.y,
			(to - from) * MattArtLayout.SCALE, row_band.size.y)
		rects.append(rect)
		revealed.append(false)
		added.append(rect)
		var segment := _build_segment(i, rect.grow_individual(0, 0, 0, cover))
		segment.modulate.a = 0.0
		add_child(segment)
		segments.append(segment)
	return added


# A shard from the ceiling onto `land`, `drift` px off to the side where it starts, over `fall_time`
# (ease-in). Its shadow grows on the spot as it comes; when it lands it bursts and its segment fades in.
func drop_shard(land: Vector2, fall_time: float, drift: float, shape: int) -> void:
	var shadow := _build_shadow()
	add_child(shadow)
	shadow.global_position = land.round()
	shadow.scale = Vector2.ONE * 0.3
	shadow.modulate.a = 0.15
	var grow := shadow.create_tween().set_parallel()
	grow.tween_property(shadow, "scale", Vector2.ONE, fall_time)
	grow.tween_property(shadow, "modulate:a", 0.5, fall_time)
	var shard := _build_shard(shape)
	shard.add_to_group(hazard_group)
	shard_layer.add_child(shard)
	shards.append(shard)
	shard.global_position = Vector2(land.x + drift, SHARD_FROM_Y).round()
	var fall := shard.create_tween()
	fall.tween_property(shard, "global_position", land.round(), fall_time).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	fall.tween_callback(_land.bind(shard, shadow, land))


func _land(shard: Node2D, shadow: Node2D, land: Vector2) -> void:
	shards.erase(shard)
	shard.queue_free()
	if is_instance_valid(shadow):
		shadow.queue_free()
	if clearing:
		return
	landings.append(land)
	var i := segment_at(land)
	_reveal(i, SEGMENT_FADE)
	_play_once(&"glass_land", land)
	_play_once(&"glass_glint", land + GLINT_OFFSET)
	if body:
		body.play_sfx(&"glass_land", 1.0 + randf_range(-0.1, 0.1))


func _reveal(i: int, time: float) -> void:
	if revealed[i]:
		return
	revealed[i] = true
	var fade := segments[i].create_tween()
	fade.tween_property(segments[i], "modulate:a", 1.0, time)


# Whatever hasn't landed yet is there at once: the glass is whole before the first boom.
func reveal_all() -> void:
	for i in segments.size():
		if not revealed[i]:
			revealed[i] = true
			segments[i].modulate.a = 1.0


# The lane and the rows, faded in over `time`: `layout` is MattStateMachine.GLASS_ROW, `lane_top` the y
# the lane starts at and `ropes` the ring's inside edges. The rows' lines stop at the glass as it lies when
# they go up.
func show_guides(on: bool, time: float, layout: Dictionary, lane_top: float, ropes: Rect2) -> void:
	if on and guides == null:
		guide_spec = {layout = layout, lane_top = lane_top, ropes = ropes, glass_top = band.position.y}
		guides = Node2D.new()
		guides.name = "Guides"
		guides.modulate.a = 0.0
		guides.draw.connect(_draw_guides)
		add_child(guides)
		guides.queue_redraw()
	if guides == null:
		return
	if guide_fade:
		guide_fade.kill()
	guide_fade = guides.create_tween()
	guide_fade.tween_property(guides, "modulate:a", 1.0 if on else 0.0, time)


func _draw_guides() -> void:
	var style := MattArtLayout.GLASS_GUIDES
	var layout: Dictionary = guide_spec.layout
	var ropes: Rect2 = guide_spec.ropes
	var lane: Vector2 = layout.lane
	var top: float = guide_spec.lane_top
	var origin := guides.global_position
	guides.draw_rect(Rect2(Vector2(lane.x, top) - origin, Vector2(lane.y - lane.x, ropes.end.y - top)), style.lane_tint)
	for x in [lane.x, lane.y]:
		guides.draw_dashed_line(Vector2(x, top) - origin, Vector2(x, ropes.end.y) - origin, style.edge, style.edge_width, style.dash)
	# Between every two rows down to the glass's top edge.
	var glass_top: float = guide_spec.glass_top
	for k in range(1, layout.row_names.size()):
		var y: float = layout.rows_top + layout.row_height * k
		if y > glass_top + 0.5:
			break
		guides.draw_line(Vector2(ropes.position.x, y) - origin, Vector2(ropes.end.x, y) - origin, style.row_line, style.row_width)


func shatter_at(feet: Vector2) -> void:
	_play_once(&"glass_shatter", feet)


# The glass goes, left to right across `time`, and the floor with it.
func clear(time: float) -> void:
	if clearing:
		return
	clearing = true
	if body:
		body.play_sfx(&"glass_clear")
	var fade_each := maxf(time - CLEAR_STAGGER * (segments.size() - 1), 0.05)
	for i in segments.size():
		var fade := segments[i].create_tween()
		fade.tween_interval(CLEAR_STAGGER * i)
		fade.tween_property(segments[i], "modulate:a", 0.0, fade_each)
	show_guides(false, minf(time, MattArtLayout.GLASS_GUIDES.hide_time), {}, 0.0, Rect2())
	var done := create_tween()
	done.tween_interval(time)
	done.tween_callback(queue_free)


#WHAT IS DRAWN

func _build_segment(i: int, rect: Rect2) -> CanvasItem:
	if MattArtLayout.uses_final_fx(&"glass_floor"):
		var spec := MattArtLayout.fx(&"glass_floor")
		var tile := Sprite2D.new()
		tile.texture = load(spec.texture)
		tile.centered = false
		tile.texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
		tile.region_enabled = true
		tile.region_rect = Rect2(spec.segment_shift * i, 0, rect.size.x / MattArtLayout.SCALE, rect.size.y / MattArtLayout.SCALE)
		tile.scale = Vector2.ONE * MattArtLayout.SCALE
		tile.position = rect.position - global_position
		return tile
	var spec := MattArtLayout.fx(&"glass_floor")
	var piece := Node2D.new()
	piece.position = rect.position - global_position
	var fill := Polygon2D.new()
	var teeth: float = spec.teeth
	var depth: float = spec.edge_depth
	var outline := PackedVector2Array()
	var steps := maxi(int(rect.size.x / teeth), 1)
	for s in steps + 1:
		var x := rect.size.x * s / steps
		outline.append(Vector2(x, depth * (0.0 if s % 2 == 0 else 1.0) * 0.5))
	outline.append(Vector2(rect.size.x, rect.size.y))
	outline.append(Vector2(0, rect.size.y))
	fill.polygon = outline
	fill.color = spec.fill
	piece.add_child(fill)
	var edge := Line2D.new()
	edge.points = outline.slice(0, steps + 1)
	edge.default_color = spec.edge
	edge.width = 3.0
	piece.add_child(edge)
	var shine := Line2D.new()
	shine.points = PackedVector2Array([Vector2(rect.size.x * 0.15, depth + 24.0), Vector2(rect.size.x * 0.45, depth + 60.0)])
	shine.default_color = spec.shine
	shine.width = 6.0
	piece.add_child(shine)
	return piece


func _build_shard(shape: int) -> Node2D:
	if MattArtLayout.uses_final_fx(&"glass_shard"):
		var spec := MattArtLayout.fx(&"glass_shard")
		var sheet := Sprite2D.new()
		sheet.texture = load(spec.texture)
		sheet.hframes = spec.hframes
		sheet.scale = Vector2.ONE * MattArtLayout.SCALE
		sheet.offset = spec.offset
		var first: int = (shape % int(spec.shapes)) * 2
		sheet.frame = first
		var spin := sheet.create_tween().set_loops()
		spin.tween_interval(spec.frame_time)
		spin.tween_callback(sheet.set_frame.bind(first + 1))
		spin.tween_interval(spec.frame_time)
		spin.tween_callback(sheet.set_frame.bind(first))
		return sheet
	var spec := MattArtLayout.fx(&"glass_shard")
	var size: Vector2 = spec.size
	var shard := Polygon2D.new()
	shard.polygon = PackedVector2Array([Vector2(0, 0), Vector2(size.x / 2.0, -size.y * 0.6), Vector2(0, -size.y),
		Vector2(-size.x / 2.0, -size.y * 0.5)])
	shard.color = spec.color
	return shard


func _build_shadow() -> Node2D:
	if MattArtLayout.uses_final_fx(&"glass_shadow"):
		var spec := MattArtLayout.fx(&"glass_shadow")
		var sheet := Sprite2D.new()
		sheet.texture = load(spec.texture)
		sheet.scale = Vector2.ONE * MattArtLayout.SCALE
		sheet.offset = spec.offset
		var holder := Node2D.new()
		holder.add_child(sheet)
		return holder
	var spec := MattArtLayout.fx(&"glass_shadow")
	var shadow := Polygon2D.new()
	shadow.polygon = MattArtLayout.ellipse(spec.radii, 16)
	shadow.color = spec.color
	return shadow


# A one-shot effect at `at`, freed when it has played: a drawn sheet's frames, or a stand-in star.
func _play_once(key: StringName, at: Vector2) -> void:
	var play: Tween
	if MattArtLayout.uses_final_fx(key):
		var spec := MattArtLayout.fx(key)
		var sheet := Sprite2D.new()
		sheet.texture = load(spec.texture)
		sheet.hframes = spec.hframes
		sheet.scale = Vector2.ONE * MattArtLayout.SCALE
		sheet.offset = spec.offset
		add_child(sheet)
		sheet.global_position = at.round()
		play = sheet.create_tween()
		for f in range(1, spec.hframes):
			play.tween_interval(spec.frame_time)
			play.tween_callback(sheet.set_frame.bind(f))
		play.tween_interval(spec.frame_time)
		play.tween_callback(sheet.queue_free)
		return
	var spec := MattArtLayout.fx(key)
	var star := Polygon2D.new()
	star.polygon = MattArtLayout.star(spec.points, spec.radius, spec.inner_ratio)
	star.color = spec.color
	star.scale = Vector2.ONE * 0.4
	add_child(star)
	star.global_position = at.round()
	play = star.create_tween().set_parallel()
	play.tween_property(star, "scale", Vector2.ONE, spec.time)
	play.tween_property(star, "modulate:a", 0.0, spec.time)
	play.chain().tween_callback(star.queue_free)
