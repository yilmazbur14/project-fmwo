extends State

# The player held in a fight's own poses while it has them locked (Matt's Glass Row): the fight hands
# PlayerScript a sheet (hold_pose) and the frames to run (play_pose), and this only draws them and gives
# the sprite back exactly as it was. It only exists inside a lock: unlock_actions() ends it.
#
# The sheet keeps the 4-row facing contract (the rows in player_4dir_sheet.png's order), so the row is
# always the player's facing and a fight that turns them turns the pose with them.

@export var animation_player : AnimationPlayer
@export var player : CharacterBody2D

var saved_texture: Texture2D
var saved_hframes := 1
var saved_vframes := 1
var saved_frame := 0
var saved_offset := Vector2.ZERO
var saved_flip_h := false
# What runs: columns, seconds each (the last entry for the rest), and whether it loops. A one-shot holds
# its last column.
var frames: Array = [0]
var times: Array = [1.0]
var loop := true
var step := 0
var clock := 0.0


func Enter() -> void:
	animation_player.stop()
	var sprite: Sprite2D = player.sprite
	saved_texture = sprite.texture
	saved_hframes = sprite.hframes
	saved_vframes = sprite.vframes
	saved_frame = sprite.frame
	saved_offset = sprite.offset
	saved_flip_h = sprite.flip_h
	apply_sheet()


func Exit() -> void:
	var sprite: Sprite2D = player.sprite
	sprite.texture = saved_texture
	sprite.hframes = saved_hframes
	sprite.vframes = saved_vframes
	sprite.frame = saved_frame
	sprite.offset = saved_offset
	sprite.flip_h = saved_flip_h


func Update(delta: float) -> void:
	clock += delta
	while clock >= _time_of(step) and (loop or step < frames.size() - 1):
		clock -= _time_of(step)
		step = (step + 1) % frames.size()
	_show()


func Physics_Update(_delta: float) -> void:
	player.velocity = Vector2.ZERO


func apply_sheet() -> void:
	var sheet: Dictionary = player.pose_sheet
	var sprite: Sprite2D = player.sprite
	sprite.texture = load(sheet.texture)
	sprite.hframes = sheet.hframes
	sprite.vframes = sheet.vframes
	sprite.flip_h = false
	_show()


func play(run_frames: Array, run_times: Array, run_loop: bool) -> void:
	frames = run_frames if not run_frames.is_empty() else [0]
	times = run_times if not run_times.is_empty() else [1.0]
	loop = run_loop
	step = 0
	clock = 0.0
	_show()


func _time_of(index: int) -> float:
	return maxf(float(times[mini(index, times.size() - 1)]), 0.001)


func _show() -> void:
	player.sprite.frame_coords = Vector2i(int(frames[step]), player.facing)
