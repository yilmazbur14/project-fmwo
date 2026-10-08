extends Node2D

# Attack 1's maze walls (JordanComboMaze), on the god's Stage layer so each one sorts with the player: a block per wall
# cell, standing on the block with its front edge on the block's bottom edge. They rise rippling out from the start,
# stand lit, and vanish as the dark falls. Nothing collides with them: the arrow is the maze's answer.
#
# SORTING: a wall's node stands on its cell's soles line less SOLES_OVER_ORIGIN, so it sorts by its soles against the
# player's soles as the player's origin does, and SORT_LEAD behind that, so on a tie in the same row the body draws
# over the wall. A wall one row behind the player never draws over them.
#
# The block is void_wall.png's rise, stand and vanish frames once it is in (JordanMazeLayout.uses_final_wall()), each
# frame cut at the floor line itself. Until then a code block of the same size - its top face, its front and a
# rune-blue edge - grows up out of the floor and fades.
#
# Every beat here is a node-bound tween, so a pause or a freeze holds it.

const Layout := preload("res://Scripts/JordanMazeLayout.gd")

const SORT_LEAD := 1.0

var cells: Array[Vector2i] = []
var blocks: Array[Node2D] = []
# What rises on each block: the sheet, or the code block's faces grown up from the bottom edge.
var bodies: Array[Node2D] = []
# How many have finished rising; and whether they have been told to go.
var standing := 0
var vanishing := false
# The flares under way, by block, and how many blocks the beam has lit, for a test.
var flares := {}
var lit := 0


func _init() -> void:
	y_sort_enabled = true


# A block on each of `wall_cells`, still under the floor, in the order they will rise. Once it is in the tree.
func build(wall_cells: Array[Vector2i]) -> void:
	var sort_line := Vector2(0, Layout.SOLES_OVER_ORIGIN + SORT_LEAD)
	for cell in wall_cells:
		var block := Node2D.new()
		block.name = "Wall%d" % cells.size()
		add_child(block)
		block.global_position = Layout.soles(cell) - sort_line
		var body := _build_body()
		# The drawing stays where the block is, whatever its node sorts on: the sheet off the soles line less
		# SOLES_OVER_ORIGIN (the artist's point), the code block off the block's bottom edge.
		body.position = Vector2(0, SORT_LEAD) if body is Sprite2D else sort_line + Vector2(0, Layout.BLOCK.y / 2.0)
		body.visible = false
		block.add_child(body)
		cells.append(cell)
		blocks.append(block)
		bodies.append(body)


# Each block `stagger` after the one before it, rising over `rise_time`: the sheet's rise frames at their own
# timings, fitted to it.
func rise(stagger: float, rise_time: float) -> void:
	for k in bodies.size():
		var body := bodies[k]
		var up := body.create_tween()
		up.tween_interval(stagger * k)
		up.tween_callback(body.show)
		if body is Sprite2D:
			_play_frames(up, body as Sprite2D, Layout.WALL.rise, Layout.WALL.rise_times, rise_time)
			up.tween_callback((body as Sprite2D).set_frame.bind(Layout.WALL.stand))
		else:
			# A sliver rather than 0: a zero scale leaves a transform nothing can invert.
			body.scale = Vector2(1, 0.01)
			body.modulate.a = 0.0
			up.set_parallel()
			up.tween_property(body, "scale", Vector2.ONE, rise_time).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
			up.tween_property(body, "modulate:a", 1.0, rise_time)
			up.chain()
		up.tween_callback(_stood)


# From the first block starting until the last is up.
func rise_duration(stagger: float, rise_time: float) -> float:
	return stagger * maxi(bodies.size() - 1, 0) + rise_time


func _stood() -> void:
	standing += 1


# All of them at once, over `time`, to nothing: the sheet's vanish frames, fitted to it, then hidden.
func vanish(time: float) -> void:
	if vanishing:
		return
	vanishing = true
	for body in bodies:
		var out := body.create_tween()
		if body is Sprite2D:
			_play_frames(out, body as Sprite2D, Layout.WALL.vanish, Layout.WALL.vanish_times, time)
		else:
			out.tween_property(body, "modulate:a", 0.0, time)
		out.tween_callback(body.hide)


func is_shown() -> bool:
	return bodies.any(func(body: Node2D) -> bool: return body.visible and body.modulate.a > 0.0)


# Block `k` lit again for a moment, long after it vanished, as Greyson's beam passes it (JordanMazeLayout.BEAM_V2_WALLS):
# standing whole in `color`, held `hold` s, then fading to nothing over `fade` s.
func flare(k: int, color: Color, hold: float, fade: float) -> void:
	var body := bodies[k]
	if flares.has(k) and flares[k].is_valid():
		flares[k].kill()
	if body is Sprite2D:
		(body as Sprite2D).frame = Layout.WALL.stand
	body.modulate = color
	body.show()
	var out := body.create_tween()
	out.tween_interval(hold)
	out.tween_property(body, "modulate:a", 0.0, fade)
	out.tween_callback(body.hide)
	flares[k] = out
	lit += 1


# `frames` onto `run` at `times`, scaled so they take `total`.
func _play_frames(run: Tween, sheet: Sprite2D, frames: Array, times: Array, total: float) -> void:
	var drawn := 0.0
	for time in times:
		drawn += float(time)
	for i in frames.size():
		run.tween_callback(sheet.set_frame.bind(frames[i]))
		run.tween_interval(float(times[i]) * total / drawn)


#WHAT IS DRAWN

func _build_body() -> Node2D:
	if Layout.uses_final_wall():
		var sheet := Sprite2D.new()
		sheet.texture = load(Layout.WALL.texture)
		sheet.hframes = Layout.WALL.hframes
		sheet.centered = false
		sheet.offset = Layout.WALL.offset
		sheet.scale = Vector2.ONE * Layout.SCALE
		sheet.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		return sheet
	var spec := Layout.PLACEHOLDER_WALL
	var half: float = Layout.BLOCK.x / 2.0
	var height: float = spec.height
	var top_y: float = -height - Layout.BLOCK.y
	var body := Node2D.new()
	body.add_child(_face(Rect2(-half, -height, Layout.BLOCK.x, height), spec.front))
	body.add_child(_face(Rect2(-half, top_y, Layout.BLOCK.x, Layout.BLOCK.y), spec.top))
	# Inset half a line, so each edge covers the face's own outermost texel.
	var inset: float = spec.edge_width / 2.0
	var top_edge := Line2D.new()
	top_edge.closed = true
	top_edge.points = PackedVector2Array([Vector2(-half + inset, top_y + inset), Vector2(half - inset, top_y + inset),
		Vector2(half - inset, -height - inset), Vector2(-half + inset, -height - inset)])
	top_edge.width = spec.edge_width
	top_edge.default_color = spec.top_edge
	body.add_child(top_edge)
	var front_edge := Line2D.new()
	front_edge.points = PackedVector2Array([Vector2(-half + inset, -height), Vector2(-half + inset, -inset),
		Vector2(half - inset, -inset), Vector2(half - inset, -height)])
	front_edge.width = spec.edge_width
	front_edge.default_color = spec.front_edge
	body.add_child(front_edge)
	return body


func _face(rect: Rect2, color: Color) -> Polygon2D:
	var face := Polygon2D.new()
	face.polygon = PackedVector2Array([rect.position, Vector2(rect.end.x, rect.position.y), rect.end,
		Vector2(rect.position.x, rect.end.y)])
	face.color = color
	return face
