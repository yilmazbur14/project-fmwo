extends Node2D

# The fire beast Bixby's Inferno breathes (BixbyBeastInferno): one giant cone straight down the ring from his
# middle mouth, over roughly three quarters of it, leaving the two upper corners beside him. It smoulders
# faintly over the cone from the moment he takes the rope and strongly through his wind-up, then catches,
# burns and dies down. It lies flat on one floor layer, under everyone and over the mat; only the burst at
# his mouth is drawn over him. It reports its own hits: the player's hurtbox against the cone, and the dodge
# ghost left in it as a near miss. Its timing all runs in _physics_process, so a freeze holds it.

const InfernoLayout := preload("res://Scripts/BixbyInfernoArtLayout.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")

enum Phase { FAINT, WARN, IGNITE, BURN, DIE }

# Over the ropes and over him: the burst comes out of his mouth.
const BURST_Z := 2

# Set by the attack before the flood enters the tree: the cone's tip (px) and how far either side of
# straight down it opens (radians), who it burns, and who breathes it.
var apex := Vector2.ZERO
var half_angle := 0.0
var player: CharacterBody2D
var boss: Node2D

var phase := Phase.FAINT
var clock := 0.0
var warn_time := 1.0
var burn_time := 0.9
var fill: Polygon2D
var edges: Array[Line2D] = []
var burst: Node2D
var tiles: Array[Sprite2D] = []
var strips: Array[Sprite2D] = []


func _ready() -> void:
	position = Vector2(0, InfernoLayout.FLOOR_LAYER_Y)
	if InfernoLayout.USE_FINAL_FLOOD:
		_lay_final()
	else:
		_lay_placeholder()
	_show()


func warn_faint() -> void:
	_start(Phase.FAINT)
	_show()


# The strong smoulder, for the wind-up's `seconds`: it builds to its peak by the time the fire catches.
func warn(seconds: float) -> void:
	warn_time = seconds
	_start(Phase.WARN)
	_show()


# The fire catches now, hurts from FLOOD_IGNITE_TIME until `breath_time`, then dies down harmlessly.
func ignite(breath_time: float) -> void:
	burn_time = breath_time
	_start(Phase.IGNITE)
	_show()


func is_hurting() -> bool:
	return phase == Phase.BURN


func _physics_process(delta: float) -> void:
	clock += delta
	if phase == Phase.IGNITE and clock >= InfernoLayout.FLOOD_IGNITE_TIME:
		phase = Phase.BURN
	if phase == Phase.BURN:
		if clock >= burn_time:
			_start(Phase.DIE)
		else:
			_burn_player()
	elif phase == Phase.DIE and clock >= InfernoLayout.FLOOD_DIE_TIME:
		queue_free()
		return
	_show()


func _start(new_phase: Phase) -> void:
	phase = new_phase
	clock = 0.0


# It covers most of the floor, so it tests the player's box against the cone directly rather than through an
# area. At most one hit lands: it burns for less than the player's invincibility lasts.
func _burn_player() -> void:
	if not is_instance_valid(player):
		return
	if InfernoLayout.rect_hits_cone(_rect_of(player.hurtBox), apex, half_angle):
		player.receive_hit(_hit())
	elif player.dodge_ghost_position() != Vector2.INF and InfernoLayout.rect_hits_cone(_rect_of(player.dodge_ghost), apex, half_angle):
		player.receive_near_miss(_hit())


func _rect_of(area: Area2D) -> Rect2:
	var shape: CollisionShape2D = area.get_node("CollisionShape2D")
	return shape.global_transform * shape.shape.get_rect()


func _hit() -> RefCounted:
	return HitInfo.make(&"bixby_inferno", self, apex, boss)


# From screen px to this layer's own.
func _local(point: Vector2) -> Vector2:
	return point - position


func _lay_placeholder() -> void:
	var look := InfernoLayout.PLACEHOLDER_FLOOD
	fill = Polygon2D.new()
	var outline := PackedVector2Array()
	for point in InfernoLayout.cone_polygon(apex, half_angle):
		outline.append(_local(point))
	fill.polygon = outline
	add_child(fill)
	for side in [-1.0, 1.0]:
		var edge := Line2D.new()
		edge.points = PackedVector2Array([_local(apex), _local(InfernoLayout.cone_edge_end(apex, half_angle, side))])
		edge.width = look.edge_width
		add_child(edge)
		edges.append(edge)
	var spikes := PackedVector2Array()
	var count: int = look.burst_spikes * 2
	for i in count:
		var reach: float = look.burst_radius * (1.0 if i % 2 == 0 else 0.45)
		spikes.append(Vector2.from_angle(TAU * i / count) * reach)
	var star := Polygon2D.new()
	star.polygon = spikes
	star.color = look.burst
	star.position = _local(apex)
	burst = star
	burst.z_index = BURST_Z
	burst.hide()
	add_child(burst)


# The tiles, cut exactly to the cone; the edge strip down both slants over the cut, itself cut at the arena's
# walls; and the burst at his mouth.
func _lay_final() -> void:
	var spec := InfernoLayout.FINAL_FLOOD
	var area := InfernoLayout.INFERNO_AREA
	var sheet: Texture2D = load(spec.sheet)
	var bed := InfernoLayout.FLOOD_TILE * InfernoLayout.SCALE
	var rise := (InfernoLayout.FLOOD_FRAME_SIZE.y - InfernoLayout.FLOOD_TILE.y) * InfernoLayout.SCALE
	var cone := _mask(InfernoLayout.cone_polygon(apex, half_angle))
	for row in InfernoLayout.FLOOD_GRID.y:
		for column in InfernoLayout.FLOOD_GRID.x:
			var cell := Rect2(area.position + Vector2(column * bed.x, row * bed.y), bed)
			if not InfernoLayout.rect_hits_cone(cell, apex, half_angle):
				continue
			var tile := _sprite(sheet, InfernoLayout.FLOOD_FRAME_SIZE)
			tile.position = _local(cell.position) - Vector2(0, rise)
			cone.add_child(tile)
			tiles.append(tile)

	var walls := _mask(PackedVector2Array([area.position, Vector2(area.end.x, area.position.y), area.end,
		Vector2(area.position.x, area.end.y)]))
	var edge_sheet: Texture2D = load(spec.edge_sheet)
	var frame_size: Vector2 = spec.edge_frame_size
	var pivot: Vector2 = spec.edge_pivot
	var width := frame_size.x * InfernoLayout.SCALE
	for side: float in [1.0, -1.0]:
		var i := 0
		while true:
			var across := side * i * width
			var at := apex + Vector2(across, roundf(absf(across) / tan(half_angle)))
			if at.x <= area.position.x or at.x >= area.end.x or at.y >= area.end.y:
				break
			var piece := _sprite(edge_sheet, frame_size)
			piece.flip_h = side < 0.0
			piece.offset = -Vector2(frame_size.x - pivot.x, pivot.y) if piece.flip_h else -pivot
			piece.position = _local(at)
			walls.add_child(piece)
			strips.append(piece)
			i += 1

	var burst_sheet: Texture2D = load(spec.burst_sheet)
	var mouth := Sprite2D.new()
	mouth.texture = burst_sheet
	mouth.hframes = roundi(burst_sheet.get_width() / spec.burst_frame_size.x)
	mouth.offset = spec.burst_offset
	mouth.scale = Vector2.ONE * InfernoLayout.SCALE
	mouth.position = _local(apex + InfernoLayout.BURST_ANCHOR_OFFSET)
	burst = mouth
	burst.z_index = BURST_Z
	burst.hide()
	add_child(burst)


# Draws nothing itself, and cuts whatever is put under it to `outline` (screen px).
func _mask(outline: PackedVector2Array) -> Polygon2D:
	var mask := Polygon2D.new()
	var local := PackedVector2Array()
	for point in outline:
		local.append(_local(point))
	mask.polygon = local
	mask.clip_children = CanvasItem.CLIP_CHILDREN_ONLY
	add_child(mask)
	return mask


func _sprite(sheet: Texture2D, frame_size: Vector2) -> Sprite2D:
	var sprite := Sprite2D.new()
	sprite.texture = sheet
	sprite.hframes = roundi(sheet.get_width() / frame_size.x)
	sprite.centered = false
	sprite.scale = Vector2.ONE * InfernoLayout.SCALE
	return sprite


func _show() -> void:
	if InfernoLayout.USE_FINAL_FLOOD:
		_show_final()
		return
	burst.visible = phase == Phase.IGNITE or phase == Phase.BURN
	var look := InfernoLayout.PLACEHOLDER_FLOOD
	var colour: Color
	match phase:
		Phase.FAINT:
			colour = look.faint
		Phase.WARN:
			var pulse := 0.5 + 0.5 * sin(clock * TAU * look.warn_rate)
			colour = look.warn.lerp(look.warn_peak, clampf(clock / warn_time, 0.0, 1.0) * pulse)
		Phase.IGNITE:
			colour = look.ignite
		Phase.BURN:
			colour = look.burn.lerp(look.burn_peak, 0.5 + 0.5 * sin(clock * TAU * look.burn_rate))
		Phase.DIE:
			colour = look.die
			colour.a *= 1.0 - clampf(clock / InfernoLayout.FLOOD_DIE_TIME, 0.0, 1.0)
	fill.color = colour
	var edge_colour: Color = look.edge
	edge_colour.a = minf(colour.a * 1.6, 1.0)
	for edge in edges:
		edge.default_color = edge_colour
	if burst.visible:
		burst.scale = Vector2.ONE * (1.0 + 0.12 * sin(clock * TAU * look.burn_rate))


# Neighbouring tiles start their loops on different frames, so the floor doesn't flicker in step.
func _show_final() -> void:
	var spec := InfernoLayout.FINAL_FLOOD
	var frames: Array
	var frame_time: float = spec.frame_time
	var looping := true
	var alpha := 1.0
	match phase:
		Phase.FAINT:
			frames = spec.smoulder
			alpha = spec.faint_alpha
		Phase.WARN:
			frames = spec.smoulder
			frame_time = spec.warn_frame_time
		Phase.IGNITE:
			frames = spec.ignite
			frame_time = InfernoLayout.FLOOD_IGNITE_TIME / spec.ignite.size()
			looping = false
		Phase.BURN:
			frames = spec.burn
		Phase.DIE:
			frames = spec.die
			frame_time = InfernoLayout.FLOOD_DIE_TIME / spec.die.size()
			looping = false
	var step := int(clock / frame_time)
	var laid := tiles + strips
	for i in laid.size():
		var index := (step + i) % frames.size() if looping else mini(step, frames.size() - 1)
		laid[i].frame = frames[index]
		laid[i].modulate.a = alpha
	var burst_frame := _burst_frame(spec)
	burst.visible = burst_frame >= 0
	if burst.visible:
		(burst as Sprite2D).frame = burst_frame


# The burst's frame for where the fire is, or -1 once it has died down: it catches with the fire, loops
# while it burns and dies in the first of the fire's own die-down.
func _burst_frame(spec: Dictionary) -> int:
	match phase:
		Phase.IGNITE:
			var ignite: Array = spec.burst_ignite
			return ignite[mini(int(clock / spec.burst_ignite_time), ignite.size() - 1)]
		Phase.BURN:
			var burn: Array = spec.burst_burn
			return burn[int(clock / spec.burst_burn_time) % burn.size()]
		Phase.DIE:
			var die: Array = spec.burst_die
			var step := int(clock / spec.burst_die_time)
			return die[step] if step < die.size() else -1
	return -1
