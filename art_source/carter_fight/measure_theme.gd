extends SceneTree

# One-off calibration: plays Carter's theme through a capture bus and reports its real peak and RMS,
# so its volume_db is measured against the fight's other sounds instead of guessed.
#   Godot.exe --fixed-fps 60 --script res://art_source/carter_fight/measure_theme.gd

const TRACK := "res://Assets/Audio/SFX/local/carter_theme_local.mp3"
const REFERENCE := {
	"ko bell": "res://Assets/Audio/SFX/carter_ko_ding.wav",
	"clone rush": "res://Assets/Audio/SFX/carter_rush_1.wav",
	"clone strike": "res://Assets/Audio/SFX/carter_strike.wav",
	"old placeholder theme": "res://Assets/Audio/Music/boss3_theme.ogg",
}
# Where in the track to listen, and for how long at each point.
const AT := [0.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 10.0, 260.0, 262.0, 264.0, 265.0]
const LISTEN := 0.9

var capture: AudioEffectCapture
var player: AudioStreamPlayer
var order: Array = []
var step := -1
var clock := 0.0
var peak := 0.0
var sum_sq := 0.0
var samples := 0


func _initialize() -> void:
	var bus := AudioServer.bus_count
	AudioServer.add_bus(bus)
	AudioServer.set_bus_name(bus, "Measure")
	capture = AudioEffectCapture.new()
	capture.buffer_length = 2.0
	AudioServer.add_bus_effect(bus, capture)
	player = AudioStreamPlayer.new()
	player.bus = "Measure"
	root.add_child(player)
	for at in AT:
		order.append({"label": "theme @ %ds" % int(at), "path": TRACK, "at": at})
	for label in REFERENCE:
		order.append({"label": label, "path": REFERENCE[label], "at": 0.0})
	_time_load()


# What loading the track actually costs, and therefore whether it can be left until the fight starts.
# It is loaded in CarterAkumaScript._ready() precisely because of this number.
func _time_load() -> void:
	var start := Time.get_ticks_usec()
	var stream: AudioStream = load(TRACK)
	var loaded := (Time.get_ticks_usec() - start) / 1000.0
	start = Time.get_ticks_usec()
	var again: AudioStream = load(TRACK)
	var cached := (Time.get_ticks_usec() - start) / 1000.0
	print("load from disk %.1f ms, from cache %.2f ms, length %.1f s (%s)"
		% [loaded, cached, stream.get_length(), "same resource" if again == stream else "reloaded"])


func _process(delta: float) -> bool:
	# Not from _initialize(): the player can't start until it is actually in the tree.
	if step < 0:
		_next()
		return false
	if step >= order.size():
		return true
	clock += delta
	_drain()
	if clock >= LISTEN:
		_report()
		_next()
	return false


func _next() -> void:
	step += 1
	if step >= order.size():
		print("")
		return
	var item: Dictionary = order[step]
	if not ResourceLoader.exists(item.path):
		printerr("missing ", item.path)
		_next()
		return
	player.stream = load(item.path)
	clock = 0.0
	peak = 0.0
	sum_sq = 0.0
	samples = 0
	capture.clear_buffer()
	player.play(item.at)


func _drain() -> void:
	var frames := capture.get_frames_available()
	if frames <= 0:
		return
	for frame in capture.get_buffer(frames):
		for value in [frame.x, frame.y]:
			peak = maxf(peak, absf(value))
			sum_sq += value * value
			samples += 1


func _report() -> void:
	if samples == 0:
		print("%-24s no audio captured" % order[step].label)
		return
	var rms := sqrt(sum_sq / samples)
	print("%-24s peak %6.1f dBFS   rms %6.1f dBFS" % [order[step].label,
		linear_to_db(maxf(peak, 0.00001)), linear_to_db(maxf(rms, 0.00001))])
