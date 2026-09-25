extends Control

# Greyson's hype meter (plan section 3.5): the cannon's battery, six cells shown in half cells, on his HUD layer
# beside his boss bar (GreysonArtLayout.HYPE_METER has its parts and places). The player's HYPE is a gold
# word-labelled bar at the bottom right; this is his purple and blue, counted in cells, with no word, so the two
# can't be confused.
# A gain fills at once and pops the cell it reaches; a spoil drains a texel row at a time; at six the full frames
# alternate until the spirit bomb hides his HUD. It animates on its own process, so the pause holds it.
# `body` is set before it is added; it follows his hype_changed, and set_hype() moves it.

const Layout := preload("res://Scripts/GreysonArtLayout.gd")
const CELLS := 6
# Any drain takes this long, however much it loses.
const DRAIN_TIME := 0.3

var body: Node
# Where his hype stands, in cells.
var value := 0.0
# What the cells show: the value, or on the way down to it.
var shown := 0.0
var drain_from := 0.0
var drain_clock := -1.0
var pop_cell := -1
var pop_clock := 0.0
var full_clock := 0.0
var frame_art: Texture2D
var cell_art: Texture2D
var pop_art: Texture2D
var full_art: Texture2D


func _ready() -> void:
	var spec: Dictionary = Layout.HYPE_METER
	frame_art = load(spec.frame)
	cell_art = load(spec.cell)
	pop_art = load(spec.pop)
	full_art = load(spec.full)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	size = spec.size
	if body != null:
		value = body.hype
		shown = value
		body.hype_changed.connect(set_hype)
	queue_redraw()


func set_hype(to: float) -> void:
	if to > shown:
		shown = to
		drain_clock = -1.0
		pop_cell = ceili(to) - 1
		pop_clock = 0.0
	elif to < shown:
		drain_from = shown
		drain_clock = 0.0
	value = to
	queue_redraw()


func _process(delta: float) -> void:
	var spec: Dictionary = Layout.HYPE_METER
	if drain_clock >= 0.0:
		drain_clock += delta
		shown = lerpf(drain_from, value, minf(drain_clock / DRAIN_TIME, 1.0))
		if drain_clock >= DRAIN_TIME:
			drain_clock = -1.0
		queue_redraw()
	if pop_cell >= 0:
		pop_clock += delta
		if pop_clock >= spec.pop_hframes * spec.pop_frame_time:
			pop_cell = -1
		queue_redraw()
	if value >= CELLS:
		full_clock += delta
		queue_redraw()


func _draw() -> void:
	var spec: Dictionary = Layout.HYPE_METER
	if value >= CELLS:
		var full_frame: int = int(full_clock / spec.full_frame_time) % spec.full_hframes
		draw_texture_rect_region(full_art, Rect2(Vector2.ZERO, size), Rect2(Vector2(full_frame * size.x, 0), size))
	else:
		draw_texture(frame_art, Vector2.ZERO)
		var cell_size := cell_art.get_size()
		var rows_high := roundi(cell_size.y / Layout.SCALE)
		for k in CELLS:
			var rows := clampi(roundi((shown - k) * rows_high), 0, rows_high)
			if rows == 0:
				continue
			var cut := Vector2(0, (rows_high - rows) * Layout.SCALE)
			var at: Vector2 = spec.cell_at + Vector2(spec.cell_step * k, 0)
			draw_texture_rect_region(cell_art, Rect2(at + cut, cell_size - cut), Rect2(cut, cell_size - cut))
	if pop_cell >= 0:
		var pop_size := Vector2(pop_art.get_width() / float(spec.pop_hframes), pop_art.get_height())
		var pop_frame := mini(int(pop_clock / spec.pop_frame_time), spec.pop_hframes - 1)
		var at: Vector2 = spec.pop_at + Vector2(spec.cell_step * pop_cell, 0)
		draw_texture_rect_region(pop_art, Rect2(at, pop_size), Rect2(Vector2(pop_frame * pop_size.x, 0), pop_size))
