extends Node2D

# One of Matt's sonic booms in the Glass Row and the arrow it carries. The node sits on the leading arc's
# apex, where the badge is drawn and what reaches the player. It only draws: MattGlassRow moves it, reads
# the answer and decides what happens. It forms as it charges at his mouth (set_charge), flickers as it
# flies (fly), shows its arrow live, answered or cracked (mark) and bursts where it lands, braced against
# or not (burst), then frees itself once the burst has played.

const MattArtLayout := preload("res://Scripts/MattArtLayout.gd")

const ARROW_POLY := [
	Vector2(0, -21), Vector2(18, -3), Vector2(7, -3), Vector2(7, 21), Vector2(-7, 21), Vector2(-7, -3), Vector2(-18, -3),
]
const ARROW_TURNS := {&"up": 0.0, &"right": PI / 2.0, &"down": PI, &"left": -PI / 2.0}

var direction := &"up"
var state := &"live"
var flying := false
var clock := 0.0
var bursting := false
var arcs: Node2D
var sheet: Sprite2D
var badge: Node2D
var badge_sheet: Sprite2D
var badge_ring: Line2D
var badge_arrow: Polygon2D
var badge_cross: Node2D


func setup(dir: StringName) -> void:
	direction = dir
	_build_arcs()
	_build_badge()
	set_charge(0.0)
	mark(&"live")


func set_charge(progress: float) -> void:
	var p := clampf(progress, 0.0, 1.0)
	var spec := MattArtLayout.fx(&"boom")
	if sheet:
		sheet.frame = mini(int(p * spec.charge_frames), spec.charge_frames - 1)
	else:
		arcs.scale = Vector2.ONE * lerpf(spec.charge_from, 1.0, p)


func fly() -> void:
	flying = true
	clock = 0.0
	if arcs:
		arcs.scale = Vector2.ONE


func _process(delta: float) -> void:
	if not flying or bursting or sheet == null:
		return
	clock += delta
	var spec := MattArtLayout.fx(&"boom")
	var flicker: Array = spec.flicker_frames
	sheet.frame = flicker[int(clock / spec.frame_time) % flicker.size()]


func mark(new_state: StringName) -> void:
	state = new_state
	if badge_sheet:
		var spec := MattArtLayout.fx(&"boom_arrow")
		var dir_index: int = spec.directions.find(direction)
		badge_sheet.frame = dir_index * spec.states.size() + spec.states.find(state)
		return
	var spec := MattArtLayout.fx(&"boom_arrow")
	var colour: Color = MattArtLayout.ARROW_COLORS[direction]
	if state == &"answered":
		colour = spec.answered
	elif state == &"cracked":
		colour = spec.cracked
	badge_ring.default_color = colour
	badge_arrow.color = colour
	badge_cross.visible = state == &"cracked"


# The arcs and the badge go, and the burst plays where it is: f0-3 braced against, f4-7 landed.
func burst(blocked: bool) -> void:
	if bursting:
		return
	bursting = true
	if arcs:
		arcs.visible = false
	if sheet:
		sheet.visible = false
	badge.visible = false
	var play := create_tween()
	if MattArtLayout.uses_final_fx(&"boom_burst"):
		var spec := MattArtLayout.fx(&"boom_burst")
		var puff := Sprite2D.new()
		puff.texture = load(spec.texture)
		puff.hframes = spec.hframes
		puff.scale = Vector2.ONE * MattArtLayout.SCALE
		puff.offset = spec.offset
		var first: int = spec.blocked_first if blocked else spec.slam_first
		puff.frame = first
		add_child(puff)
		for i in range(1, spec.frames):
			play.tween_interval(spec.frame_time)
			play.tween_callback(puff.set_frame.bind(first + i))
		play.tween_interval(spec.frame_time)
	else:
		var spec := MattArtLayout.fx(&"boom_burst")
		var star := Polygon2D.new()
		star.polygon = MattArtLayout.star(spec.points, spec.radius, spec.inner_ratio)
		star.color = spec.blocked if blocked else spec.slam
		star.scale = Vector2.ONE * 0.5
		add_child(star)
		play.set_parallel()
		play.tween_property(star, "scale", Vector2.ONE * 1.3, spec.time)
		play.tween_property(star, "modulate:a", 0.0, spec.time)
		play.chain()
	play.tween_callback(queue_free)


#WHAT IS DRAWN

func _build_arcs() -> void:
	if MattArtLayout.uses_final_fx(&"boom"):
		var spec := MattArtLayout.fx(&"boom")
		sheet = Sprite2D.new()
		sheet.texture = load(spec.texture)
		sheet.hframes = spec.hframes
		sheet.scale = Vector2.ONE * MattArtLayout.SCALE
		sheet.offset = spec.offset
		add_child(sheet)
		return
	var spec := MattArtLayout.fx(&"boom")
	arcs = Node2D.new()
	add_child(arcs)
	# Front to back: the leading arc in the ring style's core over its edge, then two fainter ones behind.
	var front := _arc(0.0, spec)
	arcs.add_child(_line(front, spec.edge, spec.edge_width))
	arcs.add_child(_line(front, spec.core, spec.core_width))
	for i in [1, 2]:
		var back := _line(_arc(-spec.spacing * i, spec), spec.flank, spec.flank_width)
		back.modulate.a = 1.0 if i == 1 else spec.trail_alpha
		arcs.add_child(back)


# An arc bowed down, its lowest point `drop` below the origin.
func _arc(drop: float, spec: Dictionary) -> PackedVector2Array:
	var points := PackedVector2Array()
	var count: int = spec.points
	var half: float = spec.chord / 2.0
	for i in count:
		var x := lerpf(-half, half, float(i) / (count - 1))
		var t := x / half
		points.append(Vector2(x, drop - spec.bow * (1.0 - t * t)))
	return points


func _line(points: PackedVector2Array, colour: Color, width: float) -> Line2D:
	var line := Line2D.new()
	line.points = points
	line.default_color = colour
	line.width = width
	return line


func _build_badge() -> void:
	badge = Node2D.new()
	badge.z_index = 1
	add_child(badge)
	if MattArtLayout.uses_final_fx(&"boom_arrow"):
		var spec := MattArtLayout.fx(&"boom_arrow")
		badge_sheet = Sprite2D.new()
		badge_sheet.texture = load(spec.texture)
		badge_sheet.hframes = spec.hframes
		badge_sheet.scale = Vector2.ONE * MattArtLayout.SCALE
		badge_sheet.offset = spec.offset
		badge.add_child(badge_sheet)
		return
	var spec := MattArtLayout.fx(&"boom_arrow")
	var disc := Polygon2D.new()
	disc.polygon = MattArtLayout.circle(spec.radius, 32)
	disc.color = spec.disc
	badge.add_child(disc)
	badge_ring = Line2D.new()
	badge_ring.points = MattArtLayout.circle(spec.radius - spec.ring_width / 2.0, 32)
	badge_ring.closed = true
	badge_ring.width = spec.ring_width
	badge.add_child(badge_ring)
	badge_arrow = Polygon2D.new()
	var scale_to: float = spec.arrow / 42.0
	badge_arrow.polygon = MattArtLayout.scaled_poly(ARROW_POLY, scale_to, ARROW_TURNS[direction])
	badge.add_child(badge_arrow)
	badge_cross = Node2D.new()
	var reach: float = spec.radius * 0.6
	for ends in [[Vector2(-reach, -reach), Vector2(reach, reach)], [Vector2(reach, -reach), Vector2(-reach, reach)]]:
		badge_cross.add_child(_line(PackedVector2Array(ends), spec.cross, 6.0))
	badge.add_child(badge_cross)
