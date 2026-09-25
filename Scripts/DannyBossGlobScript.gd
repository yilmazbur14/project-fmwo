extends Node2D

# One of the four worm globs Danny spits (plan section 3.1): a ball of worms lobbed from his mouth onto a spot
# on the floor, `flight` seconds along a parabola that peaks `arc` px over its chord, with a shadow on the
# floor growing under it. Where it lands it splats into a puddle (DannyBossPuddleScript), handed to his state
# machine, which keeps the fight's puddles. It hurts nothing on the way down.

signal landed(puddle: Node2D)

const PUDDLE_SCRIPT := preload("res://Scripts/DannyBossPuddleScript.gd")
const Layout := preload("res://Scripts/DannyBossArtLayout.gd")

# No shadow was drawn for it: an ellipse on the floor, full size where it lands, a share of that under his
# mouth.
const SHADOW_RADII := Vector2(30, 11)
const SHADOW_START := 0.3
const SHADOW_COLOR := Color(0, 0, 0, 0.3)
const SHADOW_POINTS := 20

# Set before it enters the tree, aim() last.
var flight := 0.70
var arc := 200.0
var player: Node2D
# His floor_layer, where the shadow and the puddle lie, and his sounds.
var body: Node2D
# add_hazard() and register_puddle().
var state_machine: Node

var from := Vector2.ZERO
var target := Vector2.ZERO
# The floor under his mouth, where the shadow starts.
var ground_from := Vector2.ZERO
var clock := 0.0
var spec: Dictionary = Layout.fx(&"glob")
var sheet: Sprite2D
var shadow: Polygon2D


# From his mouth to a spot on the floor. `ground_y` is his feet's line: the shadow starts on it, under his
# mouth.
func aim(mouth: Vector2, spot: Vector2, ground_y: float) -> void:
	from = mouth
	target = spot
	ground_from = Vector2(mouth.x, ground_y)


func _ready() -> void:
	sheet = Sprite2D.new()
	sheet.texture = load(spec.texture)
	sheet.hframes = spec.hframes
	sheet.offset = spec.offset
	sheet.scale = Vector2.ONE * Layout.SCALE
	add_child(sheet)
	shadow = Polygon2D.new()
	var polygon := PackedVector2Array()
	for i in SHADOW_POINTS:
		polygon.append(Vector2.from_angle(TAU * i / SHADOW_POINTS) * SHADOW_RADII)
	shadow.polygon = polygon
	shadow.color = SHADOW_COLOR
	body.floor_layer.add_child(shadow)
	_place(0.0)


func _physics_process(delta: float) -> void:
	clock += delta
	var t := minf(clock / flight, 1.0)
	_place(t)
	var frame_time: float = spec.frame_time
	sheet.frame = int(clock / frame_time) % sheet.hframes
	if t >= 1.0:
		_land()


# Along the chord, lifted by the arc; its shadow along the floor, growing as it comes down.
func point_at(t: float) -> Vector2:
	return from.lerp(target, t) + Vector2(0, -4.0 * arc * t * (1.0 - t))


func _place(t: float) -> void:
	global_position = point_at(t)
	shadow.global_position = ground_from.lerp(target, t)
	shadow.scale = Vector2.ONE * lerpf(SHADOW_START, 1.0, t)


func _land() -> void:
	var puddle: Node2D = PUDDLE_SCRIPT.new()
	puddle.player = player
	puddle.body = body
	puddle.state_machine = state_machine
	state_machine.add_hazard(puddle, target, body.floor_layer)
	state_machine.register_puddle(puddle)
	body.play_sfx(&"glob_splat")
	landed.emit(puddle)
	set_physics_process(false)
	queue_free()


func _exit_tree() -> void:
	if is_instance_valid(shadow):
		shadow.queue_free()
	shadow = null
