extends Node2D

# The shadow on the mat under the kaiju's stomp (JordanStomp), DannyBossSlamMark's job: it hunts the player while the
# kaiju is up out of sight, holds once it latches, and grows into the foot coming down. Its rim is the impact's
# footprint, JordanStompHit's ellipse. While it hunts its toed foot flickers small; the rest of the time its size says
# how high the kaiju is. It knows nothing of the kaiju: the stomp places it and pushes the height in every step. On the
# fight's floor layer, under everyone; whoever made it frees it. Its sheet once it is in (JordanKaijuLayout.fx): f0-1 the
# hunting flicker, f2 high, f3 mid, f4 low, f5 landed; drawn in code until then.

const Layout := preload("res://Scripts/JordanKaijuLayout.gd")

const RADII := Vector2(150, 105)
const RIM := Color(0.05, 0.05, 0.08, 0.55)
const RIM_WIDTH := 4.0
const FOOT := Color(0.0, 0.0, 0.0, 0.45)
const FLICKER_TIME := 0.08
# The foot's size while it hunts (its two flicker frames), and landed.
const HOVER_SIZES := [0.30, 0.38]
const LANDED_SIZE := 1.0
# [share of the height, frame]: the first share its height is over picks the frame, and under them all it has landed.
const HEIGHT_FRAMES := [[0.75, 2], [0.45, 3], [0.12, 4]]
const LANDED_FRAME := 5

var hovering := false
var hover_clock := 0.0
# 1 at the top of the leap, 0 landed.
var height := 1.0
var spec: Dictionary = Layout.fx(&"stomp_mark")
var sprite: Sprite2D


func _ready() -> void:
	if spec.is_empty():
		return
	sprite = Sprite2D.new()
	sprite.texture = Layout.texture(spec.sheet)
	sprite.hframes = spec.count
	sprite.offset = spec.offset
	sprite.scale = Vector2.ONE * Layout.SCALE
	add_child(sprite)
	_show_frame()


func _show_frame() -> void:
	if sprite == null:
		return
	if hovering:
		sprite.frame = int(hover_clock / FLICKER_TIME) % 2
		return
	sprite.frame = LANDED_FRAME
	for step in HEIGHT_FRAMES:
		if height > step[0]:
			sprite.frame = step[1]
			return


func hover() -> void:
	if hovering:
		return
	hovering = true
	hover_clock = 0.0
	_show_frame()
	queue_redraw()


func set_height(share: float) -> void:
	hovering = false
	height = clampf(share, 0.0, 1.0)
	_show_frame()
	queue_redraw()


func _physics_process(delta: float) -> void:
	if not hovering:
		return
	var was := int(hover_clock / FLICKER_TIME)
	hover_clock += delta
	if int(hover_clock / FLICKER_TIME) != was:
		_show_frame()
		queue_redraw()


func foot_size() -> float:
	if hovering:
		return HOVER_SIZES[int(hover_clock / FLICKER_TIME) % HOVER_SIZES.size()]
	return lerpf(LANDED_SIZE, HOVER_SIZES[1], height)


func _draw() -> void:
	if sprite != null:
		return
	var rim := PackedVector2Array()
	for i in 33:
		var a := TAU * i / 32.0
		rim.append(Vector2(cos(a) * RADII.x, sin(a) * RADII.y))
	draw_polyline(rim, RIM, RIM_WIDTH)
	var size := foot_size()
	var sole := PackedVector2Array()
	for i in 20:
		var a := TAU * i / 20.0
		sole.append(Vector2(cos(a) * RADII.x * 0.72, sin(a) * RADII.y * 0.62) * size)
	draw_colored_polygon(sole, FOOT)
	for toe in 3:
		var at := Vector2(RADII.x * 0.72 + 6.0, (toe - 1) * RADII.y * 0.34) * size
		draw_circle(at, 16.0 * size, FOOT)
