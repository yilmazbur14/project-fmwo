extends SceneTree

# One-off calibration for Mason's theme, on the same capture-bus method as Carter's
# (art_source/carter_fight/measure_theme.gd): its level is measured against the cues of his own
# fight rather than guessed, and the ends of the file are listened to rather than assumed, since a
# fade or a silence at the tail is a gap on every loop pass.
#   Godot.exe --fixed-fps 60 --script res://art_source/mason_tuning/measure_mason_theme.gd
# Needs a real audio device, so no --headless. Every listen is timed off the clock rather than off
# process deltas: --fixed-fps runs the loop as fast as it can, while the audio plays in real time.

const TRACK := "res://Assets/Audio/SFX/local/mason_theme_local.mp3"
const REFERENCE := {
	"old placeholder theme": "res://Assets/Audio/Music/boss_theme.ogg",
	"hit on Mason": "res://Assets/Audio/SFX/hit_impact.ogg",
	"squat (wrestler_charge)": "res://Assets/Audio/SFX/wrestler_charge.ogg",
	"phone (laser_charge)": "res://Assets/Audio/SFX/laser_charge.ogg",
	"nugget toss (whoosh)": "res://Assets/Audio/SFX/whirlwind_whoosh.ogg",
	"Carter slam": "res://Assets/Audio/SFX/earthquake_slam.ogg",
	"downed stinger": "res://Assets/Audio/SFX/downed_stinger.ogg",
	"victory fanfare": "res://Assets/Audio/SFX/victory_fanfare.ogg",
}
# Where in the track to listen, and for how long each listen runs.
const AT := [0.0, 20.0, 50.0, 80.0, 100.0]
const LISTEN := 1.0
# The ends of the file, probed at this spacing for this long each: the last seconds before the wrap
# and the first after it.
const PROBE := 0.25
const TAIL_FROM := 8.0
const HEAD_TO := 1.5

var capture: AudioEffectCapture
var player: AudioStreamPlayer
var order: Array = []
var step := -1
var started := 0
var peak := 0.0
var sum_sq := 0.0
var samples := 0
var track_length := 0.0


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
	if not ResourceLoader.exists(TRACK):
		printerr("no track at ", TRACK)
		return
	var stream: AudioStream = load(TRACK)
	track_length = stream.get_length()
	print("%s: %.2f s" % [TRACK.get_file(), track_length])
	for at in AT:
		order.append({"label": "theme @ %ds" % int(at), "path": TRACK, "at": at, "listen": LISTEN})
	for label in REFERENCE:
		order.append({"label": label, "path": REFERENCE[label], "at": 0.0, "listen": LISTEN})
	var at := track_length - TAIL_FROM
	while at < track_length - PROBE:
		order.append({"label": "tail -%4.1f s" % (track_length - at), "path": TRACK, "at": at, "listen": PROBE})
		at += PROBE * 2.0
	at = 0.0
	while at < HEAD_TO:
		order.append({"label": "head +%4.2f s" % at, "path": TRACK, "at": at, "listen": PROBE})
		at += PROBE


func _process(_delta: float) -> bool:
	# Not from _initialize(): the player can't start until it is actually in the tree.
	if step < 0:
		_next()
		return false
	if step >= order.size():
		return true
	_drain()
	if (Time.get_ticks_msec() - started) / 1000.0 >= order[step].listen:
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
	player.stream.loop = false
	peak = 0.0
	sum_sq = 0.0
	samples = 0
	capture.clear_buffer()
	player.play(item.at)
	started = Time.get_ticks_msec()


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
	print("%-24s peak %6.1f dBFS   rms %6.1f dBFS   (%.2f s heard)" % [order[step].label,
		linear_to_db(maxf(peak, 0.00001)), linear_to_db(maxf(rms, 0.00001)),
		float(samples) / 2.0 / AudioServer.get_mix_rate()])
