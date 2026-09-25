extends Sprite2D

# The arena crowd: the band over the ring (crowd_v3.png) and the ringside crowd round it
# (arena_ringside_crowd.png), both 7 frames - 0-2 a calm idle loop, 3-4 a cheer loop and 5-6 a boo
# loop - and both run this, so one call sets them both off:
#     get_tree().call_group("arena_crowd", "cheer", seconds)
#     get_tree().call_group("arena_crowd", "boo", seconds)
# The latest mood wins, and hush() clears it. It plays no sound: both nodes run it, so a sound here
# would play twice per call, and every fight's cheers would pick it up. A fight plays its own.

const IDLE_FRAMES := [0, 1, 2]
const CHEER_FRAMES := [3, 4]
const BOO_FRAMES := [5, 6]
const IDLE_FRAME_TIME := 0.35
const CHEER_FRAME_TIME := 0.15
const BOO_FRAME_TIME := 0.20

var _cheer_time_left := 0.0
var _boo_time_left := 0.0
var _frame_clock := 0.0
var _step := 0
var _hyped := false


func _ready() -> void:
	add_to_group("arena_crowd")
	frame = IDLE_FRAMES[0]


func cheer(duration: float = 1.5) -> void:
	_boo_time_left = 0.0
	if _cheer_time_left <= 0.0:
		_restart_loop()
	# Overlapping cheers extend rather than restart, so the loop doesn't stutter.
	_cheer_time_left = maxf(_cheer_time_left, duration)


func boo(duration: float = 1.5) -> void:
	_cheer_time_left = 0.0
	if _boo_time_left <= 0.0:
		_restart_loop()
	_boo_time_left = maxf(_boo_time_left, duration)


# Cuts a cheer or a boo short, for a moment that needs the crowd quiet:
#     get_tree().call_group("arena_crowd", "hush")
func hush() -> void:
	if _cheer_time_left <= 0.0 and _boo_time_left <= 0.0:
		return
	_cheer_time_left = 0.0
	_boo_time_left = 0.0
	if not _hyped:
		_restart_loop()


# While the player's hype meter is full the cheer loop never runs out.
func set_hyped(on: bool) -> void:
	if on == _hyped:
		return
	_hyped = on
	if _cheer_time_left <= 0.0 and _boo_time_left <= 0.0:
		_restart_loop()


func _process(delta: float) -> void:
	if _cheer_time_left > 0.0:
		_cheer_time_left -= delta
		if _cheer_time_left <= 0.0 and not _hyped:
			_restart_loop()
	if _boo_time_left > 0.0:
		_boo_time_left -= delta
		if _boo_time_left <= 0.0:
			_restart_loop()

	var booing := _boo_time_left > 0.0
	var cheering := not booing and (_hyped or _cheer_time_left > 0.0)
	var frame_time := BOO_FRAME_TIME if booing else (CHEER_FRAME_TIME if cheering else IDLE_FRAME_TIME)
	_frame_clock += delta
	if _frame_clock >= frame_time:
		_frame_clock -= frame_time
		_step += 1

	var frames: Array = BOO_FRAMES if booing else (CHEER_FRAMES if cheering else IDLE_FRAMES)
	frame = frames[_step % frames.size()]


func _restart_loop() -> void:
	_step = 0
	_frame_clock = 0.0
