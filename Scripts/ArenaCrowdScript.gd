extends Sprite2D

# The arena crowd strip (crowd_v2.png): frames 0-2 are a calm idle loop and
# frames 3-4 a cheer loop. Anything can set the crowd off for a moment with:
#     get_tree().call_group("arena_crowd", "cheer", seconds)

const IDLE_FRAMES := [0, 1, 2]
const CHEER_FRAMES := [3, 4]
const IDLE_FRAME_TIME := 0.35
const CHEER_FRAME_TIME := 0.15

var _cheer_time_left := 0.0
var _frame_clock := 0.0
var _step := 0


func _ready() -> void:
	add_to_group("arena_crowd")
	frame = IDLE_FRAMES[0]


func cheer(duration: float = 1.5) -> void:
	if _cheer_time_left <= 0.0:
		_restart_loop()
	# Overlapping cheers extend rather than restart, so the loop doesn't stutter.
	_cheer_time_left = maxf(_cheer_time_left, duration)


func _process(delta: float) -> void:
	if _cheer_time_left > 0.0:
		_cheer_time_left -= delta
		if _cheer_time_left <= 0.0:
			_restart_loop()

	var cheering := _cheer_time_left > 0.0
	var frame_time := CHEER_FRAME_TIME if cheering else IDLE_FRAME_TIME
	_frame_clock += delta
	if _frame_clock >= frame_time:
		_frame_clock -= frame_time
		_step += 1

	var frames: Array = CHEER_FRAMES if cheering else IDLE_FRAMES
	frame = frames[_step % frames.size()]


func _restart_loop() -> void:
	_step = 0
	_frame_clock = 0.0
