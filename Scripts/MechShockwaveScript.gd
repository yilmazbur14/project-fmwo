extends Node2D

# The mech's ground-pound ring: crest segments around an expanding ellipse. Only a segment's
# crest hurts, so a player the ring has already passed is safe; dashing through is the dodge.

const HitInfo := preload("res://Scripts/HitInfo.gd")
const SEGMENT_SCENE := preload("res://Scenes/Bosses/MechShockwaveSegmentScene.tscn")

const VERTICAL_RATIO := 0.42
const START_RADIUS := 60.0
const START_SEGMENTS := 6
# The widest gap is split once it grows past this. Splitting off-centre keeps gaps from all
# reaching it on the same frame and popping in together; spacing averages about 54px.
const MAX_SPACING := 75.0
const SPLIT_MIN := 0.4
const SPLIT_MAX := 0.6
const FRAME_COUNT := 4
const FRAME_TIME := 0.08
# A segment is drawn while its bottom-centre keeps the whole 72px sprite inside the rope art
# (so it never draws over a rope or the crowd), but hurts until that point reaches the ropes'
# collision edges. Its crest is already over a rope-hugging player before it disappears, and
# without the extra reach a player pressed into a corner could slip between segments.
const VISIBLE_AREA := Rect2(149, 186, 1627, 781)
const HURT_AREA := Rect2(105, 105, 1710, 870)
const ARC_SAMPLES := 256

# Horizontal radius growth in px/s, set by the ground pound before the ring is added.
var speed := 900.0
var radius := START_RADIUS
var elapsed := 0.0

# Position of each segment around the ring as a fraction of its length, in order. A segment
# keeps its fraction for life, so growing the ring never slides segments along it.
var arcs : Array[float] = []
var segments : Array[Area2D] = []
var start_frames : Array[int] = []

# Arc length of the ellipse up to each of ARC_SAMPLES + 1 evenly spaced angles, as a fraction
# of the whole loop; the ellipse's shape never changes, only its size.
static var arc_table := PackedFloat32Array()
static var perimeter_per_radius := 0.0


func _ready() -> void:
	if arc_table.is_empty():
		_build_arc_table()
	for i in START_SEGMENTS:
		_add_segment(i, (i + randf_range(0.0, 0.6)) / START_SEGMENTS)
	_place_segments()


func _physics_process(delta: float) -> void:
	elapsed += delta
	radius += speed * delta
	_split_wide_gaps()
	_place_segments()
	_damage_player()
	if _has_passed_hurt_area():
		queue_free()


func _add_segment(index: int, arc: float) -> void:
	var segment: Area2D = SEGMENT_SCENE.instantiate()
	arcs.insert(index, arc)
	segments.insert(index, segment)
	start_frames.insert(index, randi() % FRAME_COUNT)
	add_child(segment)


func _split_wide_gaps() -> void:
	var perimeter := radius * perimeter_per_radius
	while true:
		var widest := 0
		var widest_gap := 0.0
		for i in arcs.size():
			var next_arc := arcs[i + 1] if i + 1 < arcs.size() else arcs[0] + 1.0
			if next_arc - arcs[i] > widest_gap:
				widest_gap = next_arc - arcs[i]
				widest = i
		if widest_gap * perimeter <= MAX_SPACING:
			return
		var arc := arcs[widest] + widest_gap * randf_range(SPLIT_MIN, SPLIT_MAX)
		if arc >= 1.0:
			_add_segment(0, arc - 1.0)
		else:
			_add_segment(widest + 1, arc)


func _place_segments() -> void:
	var frame_step := int(elapsed / FRAME_TIME)
	for i in segments.size():
		var segment := segments[i]
		segment.position = (_unit_point(arcs[i]) * radius).round()
		segment.visible = VISIBLE_AREA.has_point(segment.global_position)
		segment.get_node("Sprite2D").frame = (start_frames[i] + frame_step) % FRAME_COUNT


# Reports its own hits rather than joining "enemy projectile", which also hits dashing players:
# PlayerDefense applies the dash-through rule this ring is built around.
func _damage_player() -> void:
	for segment in segments:
		if not HURT_AREA.has_point(segment.global_position):
			continue
		for area in segment.get_overlapping_areas():
			var player := area.get_parent()
			if player.get("hurtBox") == area:
				player.receive_hit(HitInfo.make(&"mech_shockwave", self, global_position))
				return


func _has_passed_hurt_area() -> bool:
	for corner in [HURT_AREA.position, Vector2(HURT_AREA.end.x, HURT_AREA.position.y), Vector2(HURT_AREA.position.x, HURT_AREA.end.y), HURT_AREA.end]:
		var offset: Vector2 = (corner - global_position) / Vector2(radius, radius * VERTICAL_RATIO)
		if offset.length_squared() >= 1.0:
			return false
	return true


static func _build_arc_table() -> void:
	var table := PackedFloat32Array()
	table.resize(ARC_SAMPLES + 1)
	var total := 0.0
	var previous := Vector2(1.0, 0.0)
	for i in range(1, ARC_SAMPLES + 1):
		var angle := TAU * i / ARC_SAMPLES
		var point := Vector2(cos(angle), VERTICAL_RATIO * sin(angle))
		total += previous.distance_to(point)
		table[i] = total
		previous = point
	for i in table.size():
		table[i] /= total
	arc_table = table
	perimeter_per_radius = total


static func _unit_point(arc: float) -> Vector2:
	var i := clampi(arc_table.bsearch(arc), 1, ARC_SAMPLES)
	var from := arc_table[i - 1]
	var to := arc_table[i]
	var angle := TAU * (i - 1 + (arc - from) / (to - from)) / ARC_SAMPLES
	return Vector2(cos(angle), VERTICAL_RATIO * sin(angle))
