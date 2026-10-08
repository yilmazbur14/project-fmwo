extends Node2D

# The spin's warning (BixbyBeastCombined): each of the three bands beast Bixby's sonic beams will come out
# along, laid flat on the floor, from his maw to where the beam stops and as thick as it hurts
# (BixbyCombinedArtLayout.beam_band), so a player sees exactly where the spin will hit before it can. It hurts
# nothing itself. The attack lays it on his shadow's layer, under everyone, and fades it out as the beams grow
# out over it. Its timing runs in _physics_process, so a freeze holds it.

const CombinedLayout := preload("res://Scripts/BixbyCombinedArtLayout.gd")

# Set by the attack before it enters the tree: each band as beam_band gives it, the ropes they are cut to,
# and how long until the beams come out.
var bands: Array = []
var arena := Rect2()
var lead := 0.6

var clock := 0.0
var fading := false
var fills: Array[Polygon2D] = []
var rims: Array[Line2D] = []


# Every fill first, then every rim: the bands cross at his maws, and no fill may cover another band's rim.
func _ready() -> void:
	var ropes := PackedVector2Array([arena.position, Vector2(arena.end.x, arena.position.y), arena.end,
		Vector2(arena.position.x, arena.end.y)])
	var outlines: Array[PackedVector2Array] = []
	for band in bands:
		for cut in Geometry2D.intersect_polygons(band_polygon(band), ropes):
			var local := PackedVector2Array()
			for point in cut:
				local.append(to_local(point))
			outlines.append(local)
	for outline in outlines:
		var fill := Polygon2D.new()
		fill.polygon = outline
		add_child(fill)
		fills.append(fill)
	for outline in outlines:
		var rim := Line2D.new()
		rim.points = outline
		rim.closed = true
		add_child(rim)
		rims.append(rim)
	_show(0)


func _physics_process(delta: float) -> void:
	clock += delta
	if not fading:
		_show(_look(clock))
		return
	modulate.a = 1.0 - clock / CombinedLayout.LANE_FADE_TIME
	if clock >= CombinedLayout.LANE_FADE_TIME:
		queue_free()


# The beams are coming out over it.
func fade_out() -> void:
	if fading:
		return
	fading = true
	clock = 0.0


# The shower markers' contract: the first two looks a quarter of the lead each, then the last two flashing.
func _look(elapsed: float) -> int:
	var quarter := lead / 4.0
	if elapsed < quarter * 2.0:
		return int(elapsed / quarter)
	return 2 + int((elapsed - quarter * 2.0) / CombinedLayout.LANE_FLASH_TIME) % 2


func _show(look: int) -> void:
	var spec: Array = CombinedLayout.LANE_LOOKS[look]
	for fill in fills:
		fill.color = spec[0]
	for rim in rims:
		rim.default_color = spec[1]
		rim.width = spec[2]


# A band as the sweep's hit test sees the beam: along its angle from where it leaves his maw for its length,
# BEAM_HIT_THICKNESS across, in px.
static func band_polygon(band: Array) -> PackedVector2Array:
	var origin: Vector2 = band[0]
	var along := Vector2.from_angle(band[1])
	var across := along.orthogonal() * CombinedLayout.BEAM_HIT_THICKNESS * CombinedLayout.SCALE / 2.0
	var tip := origin + along * float(band[2])
	return PackedVector2Array([origin + across, tip + across, tip - across, origin - across])
