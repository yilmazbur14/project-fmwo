extends Node2D

# A figure in a story scene - Jordan and the bosses in his room (JordanFinaleScript) - drawn at 3x off any sheet, its
# feet on this node's origin, which is what the room y-sorts it by. play() puts up a spec, and `next` follows one that
# doesn't loop; face_toward() turns it; walk_to() walks it on rails at a speed (awaitable, its tween in `rails` for a
# skip to run out).
#
# A spec is {sheet, frames, times, loop, frame, feet, flips}: `frame` the sheet's frame size and `feet` the texel on
# the origin, both in texels; `times` the seconds on each frame, the last repeating; `flips` for a sheet drawn facing
# right, mirrored to face left. An empty spec is the bob-walk: the frame it is on, hopping a texel every BOB_TIME,
# for a figure with no walk of its own.

const SCALE := 3.0
const BOB_TIME := 0.15
const BOB_TEXELS := 1.0

var sprite: Sprite2D
var spec := {}
var next_spec := {}
var step := 0
var clock := 0.0
var done := false
var facing_left := false
# The walk on rails a beat is waiting on, for a skip to run out.
var rails: Tween
var bobbing := false
var bob_clock := 0.0


func _init() -> void:
	sprite = Sprite2D.new()
	sprite.name = "Sprite2D"
	sprite.scale = Vector2.ONE * SCALE
	add_child(sprite)


# Puts `new_spec` up from its first frame, `after` following it once it ends unless it loops. An empty one bob-walks
# on the frame already up.
func play(new_spec: Dictionary, after := {}) -> void:
	next_spec = after
	step = 0
	clock = 0.0
	done = false
	bobbing = new_spec.is_empty()
	bob_clock = 0.0
	sprite.position = Vector2.ZERO
	if bobbing:
		return
	spec = new_spec
	var sheet: Texture2D = load(spec.sheet)
	var frame: Vector2 = spec.frame
	sprite.frame = 0
	sprite.texture = sheet
	sprite.hframes = roundi(sheet.get_width() / frame.x)
	sprite.vframes = roundi(sheet.get_height() / frame.y)
	_place()
	_show()


# Faces screen-left or screen-right toward `x`: only a spec that flips shows it.
func face_toward(x: float) -> void:
	if absf(x - global_position.x) < 1.0:
		return
	facing_left = x < global_position.x
	_place()


# Walks it to `to` at `speed` px a second on `walk_spec` (empty for the bob-walk), facing the way it goes, in whole
# pixels. It stays on its walk once there: the caller puts up what it does next.
func walk_to(to: Vector2, speed: float, walk_spec := {}) -> void:
	var from := global_position
	face_toward(to.x)
	play(walk_spec)
	var tween := create_tween()
	tween.tween_method(_step_rails.bind(from, to), 0.0, 1.0, maxf(from.distance_to(to) / maxf(speed, 1.0), 0.01))
	rails = tween
	await tween.finished
	if rails == tween:
		rails = null
	global_position = to.round()
	bobbing = false
	sprite.position = Vector2.ZERO


func _step_rails(weight: float, from: Vector2, to: Vector2) -> void:
	global_position = from.lerp(to, weight).round()


func _process(delta: float) -> void:
	if bobbing:
		bob_clock += delta
		sprite.position.y = -BOB_TEXELS * SCALE if int(bob_clock / BOB_TIME) % 2 == 1 else 0.0
		return
	if spec.is_empty() or done:
		return
	clock += delta
	var times: Array = spec.times
	var frames: Array = spec.frames
	while clock >= times[mini(step, times.size() - 1)]:
		clock -= times[mini(step, times.size() - 1)]
		if step < frames.size() - 1:
			step += 1
		elif spec.get("loop", false):
			step = 0
		else:
			done = true
			if not next_spec.is_empty():
				play(next_spec)
			return
	_show()


# Its feet texel on the origin, mirrored with it.
func _place() -> void:
	if spec.is_empty():
		return
	var mirrored: bool = spec.get("flips", false) and facing_left
	sprite.flip_h = mirrored
	var frame: Vector2 = spec.frame
	var feet: Vector2 = spec.feet
	var offset := Vector2(frame.x / 2.0 - feet.x, frame.y / 2.0 - feet.y - 1.0)
	if mirrored:
		offset.x = -offset.x
	sprite.offset = offset


func _show() -> void:
	sprite.frame = spec.frames[step]
