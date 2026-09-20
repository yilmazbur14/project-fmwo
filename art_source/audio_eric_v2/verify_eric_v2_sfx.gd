extends SceneTree

# Loads the Eric V2 finisher sounds in Godot and plays the charge loop across its seam, before they are wired.
#   Godot.exe --headless --path . --script res://art_source/audio_eric_v2/verify_eric_v2_sfx.gd
#
# Each WAV is read two ways: parsed from the file the way the importer parses it (AudioStreamWAV.load_from_file,
# import defaults, so edit/loop_mode is "Detect From WAV"), and through load() when the editor has imported it.
# Then the loop is played through Godot's own playback (mix_audio) for three turns at pitch 1.0, 1.6 and a 48 kHz
# device's rate, and every pass through the seam is compared with the rest of the loop on a click measure: the
# energy of the second difference over 1.5 ms. A click at the seam would stand out above everything else.

const NAMES := [
	"finisher_charge_loop", "finisher_bar_1", "finisher_bar_2", "finisher_bar_3",
	"break_sting", "eric_crash_thud", "knight_breaker_sting",
]
const LOOP_NAME := "finisher_charge_loop"
const RATES := [1.0, 1.6, 0.91875]
const WINDOW := 66

var _failed := false


func _initialize() -> void:
	for name: String in NAMES:
		var path := "res://Assets/Audio/SFX/%s.wav" % name
		var parsed := AudioStreamWAV.load_from_file(path)
		if parsed == null:
			_fail("could not parse %s" % path)
			continue
		_describe("parsed  ", name, parsed)
		if ResourceLoader.exists(path):
			var imported := load(path) as AudioStreamWAV
			_describe("imported", name, imported)
			if imported.loop_mode != parsed.loop_mode or imported.loop_end != parsed.loop_end:
				_fail("%s imports differently from how it parses" % name)
		else:
			print("imported %-22s not imported yet (the editor imports it on its next scan)" % name)
		var expect_loop: bool = name == LOOP_NAME
		# The loop's frames, then one guard frame that copies its first (make_eric_v2_sfx.build_all).
		if expect_loop and (parsed.loop_mode != AudioStreamWAV.LOOP_FORWARD or parsed.loop_begin != 0 or parsed.loop_end != _frames(parsed) - 1):
			_fail("%s should loop forward over all but its guard frame" % name)
		if not expect_loop and parsed.loop_mode != AudioStreamWAV.LOOP_DISABLED:
			_fail("%s should not loop" % name)
		if parsed.format != AudioStreamWAV.FORMAT_16_BITS or parsed.mix_rate != 44100 or parsed.stereo:
			_fail("%s is not 16-bit mono 44.1 kHz" % name)
		if not expect_loop:
			_check_one_shot(name, parsed)

	var loop := AudioStreamWAV.load_from_file("res://Assets/Audio/SFX/%s.wav" % LOOP_NAME)
	if loop:
		for rate in RATES:
			_check_seam(loop, rate)
	print("VERIFY %s" % ("FAILED" if _failed else "OK"))
	quit(1 if _failed else 0)


func _frames(stream: AudioStreamWAV) -> int:
	return stream.data.size() / 2


func _describe(how: String, name: String, stream: AudioStreamWAV) -> void:
	print("%s %-22s %s %d Hz %s  %.3f s  loop mode %d  begin %d  end %d  (%d frames)" % [
		how, name, "16-bit" if stream.format == AudioStreamWAV.FORMAT_16_BITS else "format %d" % stream.format,
		stream.mix_rate, "stereo" if stream.stereo else "mono", stream.get_length(), stream.loop_mode,
		stream.loop_begin, stream.loop_end, _frames(stream)])


# Plays it to the end through Godot's playback: it must end by itself, start and end silent, and stay in range.
func _check_one_shot(name: String, stream: AudioStreamWAV) -> void:
	var playback := stream.instantiate_playback()
	playback.start(0.0)
	var frames := PackedVector2Array()
	for i in 200:
		frames.append_array(playback.mix_audio(1.0, 1024))
		if not playback.is_playing():
			break
	var peak := 0.0
	for f in frames:
		peak = maxf(peak, absf(f.x))
	# The resampler starts 2 frames late and the stream stops a frame or two short of its end.
	var first := frames[2].x
	var last := frames[mini(frames.size(), _frames(stream)) - 1].x
	print("played   %-22s %d frames, ended by itself: %s, first %+.5f, last %+.5f, peak %.1f dBFS" % [
		name, frames.size(), str(not playback.is_playing()), first, last, linear_to_db(peak)])
	if playback.is_playing() or absf(first) > 0.01 or absf(last) > 0.01 or peak >= 1.0:
		_fail("%s does not play cleanly" % name)


func _check_seam(stream: AudioStreamWAV, rate: float) -> void:
	var n := stream.loop_end - stream.loop_begin
	var playback := stream.instantiate_playback()
	playback.start(0.0)
	var count := int(n * 3.2 / rate)
	var y := PackedFloat32Array()
	while y.size() < count:
		for f in playback.mix_audio(rate, 1024):
			y.append(f.x)
	var d2 := PackedFloat32Array()
	d2.resize(y.size())
	for i in range(2, y.size()):
		d2[i] = y[i] - 2.0 * y[i - 1] + y[i - 2]
	var seams: Array[int] = []
	for k in range(1, 4):
		# Where the frame at loop_end comes out: the resampler lags the data by 2 frames.
		var at := 2 + int(round(k * n / rate))
		if at < y.size() - WINDOW:
			seams.append(at)
	var others: Array[float] = []
	var c := WINDOW
	while c < y.size() - WINDOW:
		var near := false
		for s in seams:
			near = near or absi(c - s) <= 2 * WINDOW
		if not near:
			others.append(_energy(d2, c))
		c += WINDOW / 2
	others.sort()
	var median: float = others[others.size() / 2]
	var worst := 0.0
	for s in seams:
		worst = maxf(worst, _energy(d2, s))
	var above := 0
	for e in others:
		if e < worst:
			above += 1
	print("seam at rate %.5f: %d passes, worst click measure %+.1f dB vs the loop's median, %.1f percentile; loudest elsewhere %+.1f dB" % [
		rate, seams.size(), 10.0 * log(worst / median) / log(10.0), 100.0 * above / others.size(),
		10.0 * log(others[-1] / median) / log(10.0)])
	if worst > others[-1]:
		_fail("the loop's seam clicks at rate %.3f" % rate)


func _energy(d2: PackedFloat32Array, centre: int) -> float:
	var total := 0.0
	var lo := maxi(2, centre - WINDOW / 2)
	for i in range(lo, mini(lo + WINDOW, d2.size())):
		total += d2[i] * d2[i]
	return total / WINDOW


func _fail(message: String) -> void:
	_failed = true
	printerr("FAIL: ", message)
