extends Node2D

# The two rope gates that shut the ring once both fighters are in: one in the gap at the bottom of
# the ropes, one in the gap at the top. A boss entrance opens them, walks its fighters through and
# slams them.
#
# THEY ARE HIDDEN UNTIL AN ENTRANCE OPENS THEM. Every fight without one, and MainScene, draw exactly
# what they draw today - an unbroken rope line with nothing over it. Only open() puts them on screen,
# and only close()/shut_now() leaves them shut for the fight.
#
# They are purely visual: both fighters walk in on written global_position, not move_and_slide, so
# wallBoundaries is untouched and nothing about collision changes.

const ScreenView := preload("res://Scripts/ScreenView.gd")

#ART
# The gate's three poses, whichever art draws them: stowed, mid-swing, shut.
enum Pose { OPEN, SWINGING, SHUT }
# arena_gate.png, when it lands: 3 frames authored in the ringside's 640x360 texel space, drawn at
# SCALE. The top copy is the same art flipped vertically.
const USE_FINAL_GATE_ART := false
const FINAL_GATE := {
	"texture": "res://Assets/Environment/arena_gate.png",
	"hframes": 3,
}
# Until then: two leaves per gate, drawn in the ringside's own posts-and-canvas colours, parked at
# the sides when open and meeting in the middle when shut. Same three poses, same timing, so the
# entrance plays and reads before any art exists.
const PLACEHOLDER_GATE := {
	# Texels, before SCALE: one leaf, and the post cap on its inner end.
	"leaf": Vector2(36, 8),
	"post": Vector2(4, 12),
	"frame": Color(0.08235294, 0.07450981, 0.12156863),
	"canvas": Color(0.44313726, 0.59607846, 0.30980393),
	"post_color": Color(0.85490197, 0.62745096, 0.4),
}
# How far apart the two leaves sit in each pose, as a fraction of one leaf's width.
const PLACEHOLDER_SPREAD := [1.0, 0.45, 0.0]

const SCALE := 3.0
# Where each gate sits, in the arena's own screen space: on the rope line, centred on the ring.
const BOTTOM_AT := Vector2(960, 980)
const TOP_AT := Vector2(960, 100)

#THE SLAM
# Seconds the leaves take to swing, and the beat the shut pose is held for before the entrance
# carries on.
const SWING_TIME := 0.25
const IMPACT_HOLD := 0.25
# A stand-in until the gate has a clang of its own: the heaviest impact already in the build.
const CLANG_SFX := "res://Assets/Audio/SFX/eric_crash_thud.wav"
const SHAKE := 9.0
const SHAKE_STEPS := 5
const SHAKE_STEP_TIME := 0.03
const CHEER := 1.4

@onready var bottom: Sprite2D = $Bottom
@onready var top: Sprite2D = $Top
@onready var clang_sfx: AudioStreamPlayer = $ClangSfxPlayer

var open_now := false


func _ready() -> void:
	bottom.position = BOTTOM_AT
	top.position = TOP_AT
	top.flip_v = true
	for gate in [bottom, top]:
		gate.scale = Vector2(SCALE, SCALE)
		if USE_FINAL_GATE_ART:
			gate.texture = load(FINAL_GATE.texture)
			gate.hframes = FINAL_GATE.hframes
		else:
			_build_placeholder(gate)
	clang_sfx.stream = load(CLANG_SFX)
	_set_pose(Pose.SHUT)
	hide()


func is_open() -> bool:
	return open_now


# Stowed and on screen: the doorway the fighters walk through.
func open() -> void:
	open_now = true
	_set_pose(Pose.OPEN)
	show()


# Both gates slam on the same frame, with one clang, one shake and one roar. Awaitable; the tween is
# this node's, so a pause holds the slam where it is.
func close() -> void:
	if not open_now:
		return
	open_now = false
	show()
	_set_pose(Pose.SWINGING)
	var swing := create_tween()
	swing.tween_interval(SWING_TIME)
	await swing.finished
	_set_pose(Pose.SHUT)
	if clang_sfx.stream != null:
		clang_sfx.play()
	ScreenView.shake(get_tree(), SHAKE, SHAKE_STEPS, SHAKE_STEP_TIME)
	get_tree().call_group("arena_crowd", "cheer", CHEER)
	var hold := create_tween()
	hold.tween_interval(IMPACT_HOLD)
	await hold.finished


# Shut with no swing, no clang and no shake: where a skipped entrance leaves the ring.
func shut_now() -> void:
	open_now = false
	_set_pose(Pose.SHUT)
	show()


func _set_pose(pose: int) -> void:
	for gate in [bottom, top]:
		if USE_FINAL_GATE_ART:
			gate.frame = pose
			continue
		var leaf: Vector2 = PLACEHOLDER_GATE.leaf
		var spread: float = PLACEHOLDER_SPREAD[pose] * leaf.x
		gate.get_node(^"Left").position.x = -spread
		gate.get_node(^"Right").position.x = spread


# One leaf either side of the gate's centre, each drawn from its outer edge inward: a dark frame, the
# canvas inside it and a post cap on the end that meets the other leaf.
func _build_placeholder(gate: Sprite2D) -> void:
	var leaf: Vector2 = PLACEHOLDER_GATE.leaf
	var post: Vector2 = PLACEHOLDER_GATE.post
	for side in [-1.0, 1.0]:
		var node := Node2D.new()
		node.name = "Left" if side < 0.0 else "Right"
		gate.add_child(node)
		# The leaf hangs outward from the node's origin, which is the inner end the post caps.
		var x := minf(0.0, side * leaf.x)
		node.add_child(_panel(Rect2(x, -leaf.y * 0.5, leaf.x, leaf.y), PLACEHOLDER_GATE.frame))
		node.add_child(_panel(Rect2(x + 1.0, -leaf.y * 0.5 + 1.0, leaf.x - 2.0, leaf.y - 2.0), PLACEHOLDER_GATE.canvas))
		node.add_child(_panel(Rect2(-post.x * 0.5, -post.y * 0.5, post.x, post.y), PLACEHOLDER_GATE.post_color))


func _panel(rect: Rect2, colour: Color) -> Polygon2D:
	var panel := Polygon2D.new()
	panel.polygon = PackedVector2Array([
		rect.position,
		rect.position + Vector2(rect.size.x, 0),
		rect.position + rect.size,
		rect.position + Vector2(0, rect.size.y),
	])
	panel.color = colour
	return panel
