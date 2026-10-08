extends Node2D

# The kaiju's tail whipped round after a stomp it was dodged out of (JordanStomp): a band of the floor from its feet
# out to an ellipse RADII round them, turning one full circle in `spin_time`. On the fight's floor layer. It starts
# where it reaches the player's bearing `lead` seconds in, so the yellow ring's wind-up and that lead are the whole
# tell. A dash through it is the dodge, and so is stepping up or down out of the ellipse.
# Worked out on the floor: the ellipse stretched back into a circle, so the band turns evenly round it.
# Drawn from its arc sheet once that is in (JordanKaijuLayout.fx, additive): frame k has the tail's leading edge at
# k x 22.5 degrees round the feet, its trail behind it turning clockwise, so with the sheet in it always turns that way
# (drawn_clockwise); each frame's PIVOT_FEET on its feet.

const HitInfo := preload("res://Scripts/HitInfo.gd")
const Beam := preload("res://Scripts/JordanKaijuBeam.gd")
const Layout := preload("res://Scripts/JordanKaijuLayout.gd")

const TAIL_ID := &"jordan_kaiju_tail"
const RADII := Vector2(520, 230)
const BAND_HALF := 40.0
const TRAIL := 1.1
const SWOOSH := Color(1.0, 0.95, 0.75, 0.5)

# Set before it is added: its centre is where it is added.
var player: CharacterBody2D
var boss: Node
var spin_time := 0.70
# +1 turns screen-clockwise, -1 the other way.
var direction := 1.0
# Radians on the floor's circle.
var start_angle := 0.0

var clock := 0.0
var hand := 0.0
var was_hand := 0.0
var spinning := false
var struck := false
# For a test: what the player made of it, or -1, and the near misses it sent.
var result := -1
var near_misses := 0
var arc_spec: Dictionary = Layout.fx(&"tail_arc")
# Loaded before anything draws: a sheet first loaded inside a draw call is drawn as a white box.
var arc_texture: Texture2D = Layout.texture(arc_spec.sheet) if not arc_spec.is_empty() else null


# Whether its arc is drawn, which turns only clockwise.
static func drawn_clockwise() -> bool:
	return not Layout.fx(&"tail_arc").is_empty()


func _ready() -> void:
	if arc_spec.is_empty():
		return
	var additive := CanvasItemMaterial.new()
	additive.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	material = additive


# The start that reaches `bearing` (radians on the floor's circle) `lead` seconds in.
static func start_for(bearing: float, lead: float, spin: float, turn: float) -> float:
	return bearing - turn * TAU * lead / spin


# A point's bearing on the floor's circle, from `centre`.
static func bearing_of(point: Vector2, centre: Vector2) -> float:
	var q := (point - centre) * Vector2(1.0, RADII.x / RADII.y)
	return q.angle()


func begin() -> void:
	spinning = true
	clock = 0.0
	hand = start_angle
	was_hand = start_angle


func _physics_process(delta: float) -> void:
	if not spinning:
		return
	clock += delta
	was_hand = hand
	hand = start_angle + direction * TAU * minf(clock / spin_time, 1.0)
	if not struck and is_instance_valid(player):
		_damage_player()
	queue_redraw()
	if clock >= spin_time:
		spinning = false
		queue_free()


func _damage_player() -> void:
	if _swept_over(Beam.feet_of(player.hurtBox.get_node("CollisionShape2D"))):
		struck = true
		result = player.receive_hit(HitInfo.make(TAIL_ID, self, global_position, boss))
	elif player.dodge_ghost_position() != Vector2.INF and _swept_over(Beam.feet_of(player.dodge_ghost.get_node("CollisionShape2D"))):
		player.receive_near_miss(HitInfo.make(TAIL_ID, self, global_position, boss))
		near_misses += 1


func covers_now(point: Vector2) -> bool:
	return _on_floor(point).length() <= RADII.x + Beam.FOOT_RADIUS


func _on_floor(point: Vector2) -> Vector2:
	return (point - global_position) * Vector2(1.0, RADII.x / RADII.y)


func _swept_over(feet: Vector2) -> bool:
	var q := _on_floor(feet)
	var rho := q.length()
	if rho > RADII.x + Beam.FOOT_RADIUS:
		return false
	var half := atan2(BAND_HALF + Beam.FOOT_RADIUS, maxf(rho, 1.0))
	var swept := absf(hand - was_hand)
	var rel := fposmod((q.angle() - was_hand) * direction + half, TAU) - half
	return rel <= swept + half


func _draw() -> void:
	if not arc_spec.is_empty():
		_draw_sheet()
		return
	var points := PackedVector2Array([Vector2.ZERO])
	var steps := 12
	for i in steps + 1:
		var a := hand - direction * TRAIL * float(i) / steps
		points.append(Vector2(cos(a) * RADII.x, sin(a) * RADII.y))
	draw_colored_polygon(points, SWOOSH)
	draw_line(Vector2.ZERO, Vector2(cos(hand) * RADII.x, sin(hand) * RADII.y), Color(1, 1, 1, 0.85), BAND_HALF)


func _draw_sheet() -> void:
	var count: int = arc_spec.count
	var frame := posmod(roundi(rad_to_deg(hand) / (360.0 / count)), count)
	var size: Vector2 = arc_spec.frame
	var pivot: Vector2 = arc_spec.anchors[frame].pivot_feet
	draw_texture_rect_region(arc_texture, Rect2(-pivot * Layout.SCALE, size * Layout.SCALE),
		Rect2(Vector2(frame * size.x, 0.0), size))
