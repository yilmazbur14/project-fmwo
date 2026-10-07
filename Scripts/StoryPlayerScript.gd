extends CharacterBody2D

# The player in a story scene - Jordan's room (JordanFinaleScript). It walks 8-way at PlayerScript.SPEED on the fight
# player's own 4-direction sheet and does nothing else: the combat MainPlayer would bring the fight's HUD, punches,
# dash and guard, a grey tint on lock_actions(), and a death path wired to the arena's node paths. The intro cutscene
# draws its own Burak the same way.
#
# Its origin is its soles, which is what the room y-sorts it by, and it collides by a foot box of about 12x6 texels
# against the room's walls. While `controllable` the move keys walk it; otherwise a beat moves it: walk_to() on rails
# (awaitable, its tween in `rails` for a skip to run out), face() to turn it, and pose() to play frames off another
# sheet laid out like this one - a column a pose, a row a facing - as the moustache gag does, until end_pose().

const PlayerScript := preload("res://Scripts/PlayerScript.gd")

enum Facing { DOWN, UP, LEFT, RIGHT }

const SHEET := "res://Assets/Characters/MainPlayer/player_4dir_sheet.png"
const SCALE := 3.0
const FRAME_SIZE := Vector2(32, 32)
# The point on the frame, in texels, its soles stand on: under the sheet's lowest drawn row, between the feet.
const SOLES := Vector2(16, 29)
# MainPlayer's walk and idle: the sheet's columns, as its AnimationPlayer plays them.
const WALK_FRAMES := [0, 1, 2, 3, 4]
const WALK_FRAME_TIME := 1.0 / 6.0
const IDLE_FRAME := 0
# The foot box, in texels, its bottom edge on the soles.
const FOOT_BOX := Vector2(12, 6)
# The middle of its upper lip on the sheet's idle frame, in texels, by facing row: from behind it is where the lip
# would be, and nothing is drawn there.
const LIP := {Facing.DOWN: Vector2(15.5, 10.0), Facing.UP: Vector2(15.5, 10.0), Facing.LEFT: Vector2(14.5, 9.5),
	Facing.RIGHT: Vector2(17.5, 9.5)}

var controllable := false
var facing := Facing.DOWN
var sprite: Sprite2D
# The walk on rails a beat is waiting on, for a skip to run out.
var rails: Tween
var walk_clock := 0.0
# A pose off another sheet: its frames and times, whether it loops, and where it is.
var pose_spec := {}
var pose_step := 0
var pose_clock := 0.0


func _ready() -> void:
	sprite = Sprite2D.new()
	sprite.name = "Sprite2D"
	sprite.scale = Vector2.ONE * SCALE
	add_child(sprite)
	var feet := CollisionShape2D.new()
	var box := RectangleShape2D.new()
	box.size = FOOT_BOX * SCALE
	feet.shape = box
	feet.position = Vector2(0.0, -FOOT_BOX.y * SCALE / 2.0)
	add_child(feet)
	_show_sheet(SHEET)
	_show_frame(IDLE_FRAME)


func _physics_process(delta: float) -> void:
	var moving := rails != null
	if controllable and not moving:
		var move := InputSettings.move_vector()
		velocity = move * PlayerScript.SPEED
		move_and_slide()
		if move != Vector2.ZERO:
			face(_facing_of(move))
			moving = true
	if pose_spec.is_empty():
		_step_walk_frames(delta, moving)
	else:
		_step_pose(delta)


# Turns it on the spot: Facing.DOWN, UP, LEFT or RIGHT, the sheet's rows.
func face(to: int) -> void:
	facing = to
	sprite.frame_coords = Vector2i(sprite.frame_coords.x, facing)


# Walks it to `to` on rails over `seconds`, facing the way it goes, in whole pixels, and stands it idle there.
func walk_to(to: Vector2, seconds: float) -> void:
	var from := global_position
	if from.distance_to(to) >= 1.0:
		face(_facing_of(to - from))
	var tween := create_tween()
	tween.tween_method(_step_rails.bind(from, to), 0.0, 1.0, maxf(seconds, 0.01))
	rails = tween
	await tween.finished
	if rails == tween:
		rails = null
	global_position = to.round()


func _step_rails(weight: float, from: Vector2, to: Vector2) -> void:
	global_position = from.lerp(to, weight).round()


# Frames off `sheet` - laid out as this one, a column a pose and a row a facing - in turn for `times` (the last value
# repeats), held on the last unless `loop`.
func pose(sheet: String, frames: Array, times: Array, loop := false) -> void:
	pose_spec = {"frames": frames, "times": times, "loop": loop}
	pose_step = 0
	pose_clock = 0.0
	_show_sheet(sheet)
	_show_frame(frames[0])


# Back on its own sheet, standing.
func end_pose() -> void:
	pose_spec = {}
	_show_sheet(SHEET)
	_show_frame(IDLE_FRAME)


# Its lip where it is drawn now, in the scene: a moustache goes on here. `lips` is another sheet's, by facing, for a
# pose off it.
func lip_point(lips := LIP) -> Vector2:
	return global_position + (lips[facing] - SOLES) * SCALE


func _step_pose(delta: float) -> void:
	var frames: Array = pose_spec.frames
	var times: Array = pose_spec.times
	pose_clock += delta
	var time: float = times[mini(pose_step, times.size() - 1)]
	while pose_clock >= time:
		if pose_step < frames.size() - 1:
			pose_step += 1
		elif pose_spec.loop:
			pose_step = 0
		else:
			pose_clock = 0.0
			break
		pose_clock -= time
		time = times[mini(pose_step, times.size() - 1)]
	_show_frame(frames[pose_step])


func _step_walk_frames(delta: float, moving: bool) -> void:
	if not moving:
		walk_clock = 0.0
		_show_frame(IDLE_FRAME)
		return
	walk_clock += delta
	_show_frame(WALK_FRAMES[int(walk_clock / WALK_FRAME_TIME) % WALK_FRAMES.size()])


func _show_sheet(path: String) -> void:
	var sheet: Texture2D = load(path)
	sprite.texture = sheet
	sprite.hframes = roundi(sheet.get_width() / FRAME_SIZE.x)
	sprite.vframes = roundi(sheet.get_height() / FRAME_SIZE.y)
	# The soles' point on this node's origin.
	sprite.offset = FRAME_SIZE / 2.0 - SOLES


func _show_frame(column: int) -> void:
	sprite.frame_coords = Vector2i(column, facing)


func _facing_of(direction: Vector2) -> int:
	if absf(direction.x) > absf(direction.y):
		return Facing.RIGHT if direction.x > 0.0 else Facing.LEFT
	return Facing.DOWN if direction.y > 0.0 else Facing.UP
