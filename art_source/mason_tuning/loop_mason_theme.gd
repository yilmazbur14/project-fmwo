extends SceneTree

# Finds, and checks, where Mason's theme can loop without its ending. The file fades out over its last
# seconds and ends in silence, so looping it end to start leaves a gap on every pass; the stream can
# instead be told to loop early, on a beat count. This decodes the whole file offline (no audio device)
# to find the tempo, the bar grid and where the fade begins, then loops the stream at the chosen bar
# and compares what comes out after the seam with the file played from the loop start.
#   Godot.exe --headless --script res://art_source/mason_tuning/loop_mason_theme.gd -- [<loop start s> <beat count> <bpm> [<seam wav>]]
# With no arguments it proposes a loop; with them it checks exactly those stream settings, and can write
# the seam out as a WAV to listen to. That WAV is the user's track: keep it out of the repo.

const TRACK := "res://Assets/Audio/SFX/local/mason_theme_local.mp3"
const HOP := 256
const CHUNK := 4096
const MIN_BPM := 70.0
const MAX_BPM := 190.0
const PHASE_BINS := 64
const BEATS_PER_BAR := 4

var rate := 0.0
var hop_time := 0.0
var energy := PackedFloat32Array()
var onset := PackedFloat32Array()


func _initialize() -> void:
	var stream: AudioStreamMP3 = load(TRACK)
	rate = AudioServer.get_mix_rate()
	hop_time = HOP / rate
	_decode(stream)
	print("decoded %.3f s at %d Hz (stream says %.3f s)" % [energy.size() * hop_time, rate, stream.get_length()])

	var fade_start := _fade_start()
	var period := _tempo(fade_start)
	var phase := _phase(period, fade_start)
	var downbeat := _downbeat(period, phase, fade_start)
	print("tempo %.4f BPM (beat %.5f s), first beat %.4f s, bars start on beat %d (first downbeat %.4f s)" % [
		60.0 / period, period, phase, downbeat, phase + downbeat * period])
	_grid_fit(period, phase + downbeat * period, fade_start)

	# Counted in whole bars from the song's first beat, the start the loop goes back to.
	var bar := period * BEATS_PER_BAR
	var last_bar := int(floor((fade_start - phase) / bar))
	print("fade begins %.2f s; the last bar line before it, from the first beat, is bar %d (%.4f s, %d beats)" % [
		fade_start, last_bar, phase + last_bar * bar, last_bar * BEATS_PER_BAR])
	var args := OS.get_cmdline_user_args()
	if args.size() >= 3:
		_check_seam(stream, float(args[0]), int(args[1]), float(args[2]), args[3] if args.size() > 3 else "")
	quit()


func _decode(stream: AudioStreamMP3) -> void:
	stream.loop = false
	var playback := stream.instantiate_playback()
	playback.start(0.0)
	var carry := 0.0
	var carried := 0
	while playback.is_playing():
		for frame in playback.mix_audio(1.0, CHUNK):
			var mono := (frame.x + frame.y) * 0.5
			carry += mono * mono
			carried += 1
			if carried == HOP:
				energy.append(carry / HOP)
				carry = 0.0
				carried = 0
	# Onset strength: how much louder each hop is than the one before, on a log scale so the quiet
	# stretches still show their beats.
	onset.resize(energy.size())
	for i in range(1, energy.size()):
		onset[i] = maxf(0.0, log(energy[i] + 1e-7) - log(energy[i - 1] + 1e-7))


# Where the level starts falling for good: the last point at which the one-second level is still
# within 3 dB of what the track holds over its last minute before that.
func _fade_start() -> float:
	var window := int(1.0 / hop_time)
	var levels : Array[float] = []
	var times : Array[float] = []
	var i := 0
	while i + window < energy.size():
		var sum := 0.0
		for j in window:
			sum += energy[i + j]
		levels.append(10.0 * log(sum / window + 1e-12) / log(10.0))
		times.append((i + window * 0.5) * hop_time)
		i += window / 4
	var body := 0.0
	var counted := 0
	for k in levels.size():
		if times[k] > times[times.size() - 1] - 70.0 and times[k] < times[times.size() - 1] - 10.0:
			body += levels[k]
			counted += 1
	body /= counted
	var start := times[times.size() - 1]
	for k in range(levels.size() - 1, -1, -1):
		if levels[k] >= body - 3.0:
			start = times[k]
			break
	print("body level %.1f dB; the last 12 s, each second:" % body)
	var line := ""
	for k in levels.size():
		if times[k] > times[times.size() - 1] - 12.0 and k % 4 == 0:
			line += " %.1f@%.0f" % [levels[k], times[k]]
	print("  ", line)
	return start


func _tempo(until: float) -> float:
	var last := int(until / hop_time)
	var best_lag := 0
	var best := -1.0
	var min_lag := int(60.0 / MAX_BPM / hop_time)
	var max_lag := int(60.0 / MIN_BPM / hop_time) + 1
	var scores := {}
	for lag in range(min_lag, max_lag + 1):
		var sum := 0.0
		for i in range(lag, last):
			sum += onset[i] * onset[i - lag]
		scores[lag] = sum
		if sum > best:
			best = sum
			best_lag = lag
	# Fine: the period whose phase histogram over the whole track is sharpest. A period off by a
	# fraction of a millisecond smears 200 beats across the histogram, so this pins it far past the
	# hop size.
	var coarse := best_lag * hop_time
	var best_period := coarse
	var best_peak := -1.0
	for step in 2:
		var span := coarse * 0.02 if step == 0 else hop_time * 0.02
		var increment := span / 200.0
		var centre := best_period
		var candidate := centre - span
		while candidate <= centre + span:
			var peak := _phase_peak(candidate, until)
			if peak > best_peak:
				best_peak = peak
				best_period = candidate
			candidate += increment
	print("autocorrelation peak %.2f BPM; refined %.4f BPM" % [60.0 / coarse, 60.0 / best_period])
	return best_period


func _phase_histogram(period: float, until: float) -> PackedFloat32Array:
	var hist := PackedFloat32Array()
	hist.resize(PHASE_BINS)
	var last := int(until / hop_time)
	for i in last:
		var t := i * hop_time
		var bin := int(fposmod(t, period) / period * PHASE_BINS) % PHASE_BINS
		hist[bin] += onset[i]
	return hist


func _phase_peak(period: float, until: float) -> float:
	var hist := _phase_histogram(period, until)
	var best := 0.0
	for b in PHASE_BINS:
		best = maxf(best, hist[b] + 0.5 * (hist[(b + 1) % PHASE_BINS] + hist[(b + PHASE_BINS - 1) % PHASE_BINS]))
	return best


func _phase(period: float, until: float) -> float:
	var hist := _phase_histogram(period, until)
	var best_bin := 0
	for b in PHASE_BINS:
		if hist[b] > hist[best_bin]:
			best_bin = b
	# The onset lands in the hop the attack starts in, which is half a hop early on average.
	return fposmod((best_bin + 0.5) / PHASE_BINS * period, period)


# Which of the bar's beats the downbeat is: the one whose onsets are strongest across the track.
func _downbeat(period: float, phase: float, until: float) -> int:
	var strength := [0.0, 0.0, 0.0, 0.0]
	var beat := 0
	var t := phase
	while t < until:
		var i := int(t / hop_time)
		var local := 0.0
		for j in range(maxi(i - 2, 0), mini(i + 3, onset.size())):
			local = maxf(local, onset[j])
		strength[beat % BEATS_PER_BAR] += local
		beat += 1
		t += period
	print("onset strength by beat of the bar: %s" % [strength])
	var best := 0
	for b in BEATS_PER_BAR:
		if strength[b] > strength[best]:
			best = b
	return best


# How well the grid holds over the whole track: the spread of each beat's nearest onset peak from
# where the grid puts it, early, middle and late.
func _grid_fit(period: float, first: float, until: float) -> void:
	for part: Array in [["first 20 s", 0.0, 20.0], ["middle", 40.0, 60.0], ["before the fade", until - 20.0, until]]:
		var errors : Array[float] = []
		var t := first
		while t < part[2]:
			if t >= part[1]:
				var i := int(t / hop_time)
				var best_j := i
				for j in range(maxi(i - 4, 1), mini(i + 5, onset.size())):
					if onset[j] > onset[best_j]:
						best_j = j
				if onset[best_j] > 0.5:
					errors.append((best_j + 0.5) * hop_time - t)
			t += period
		errors.sort()
		if errors.is_empty():
			continue
		print("grid vs onsets, %s: %d beats with a clear attack, median offset %+.1f ms, middle half within %+.1f..%+.1f ms" % [
			part[0], errors.size(), 1000.0 * errors[errors.size() / 2],
			1000.0 * errors[errors.size() / 4], 1000.0 * errors[errors.size() * 3 / 4]])


# Loops a copy of the stream with the given settings and plays across the seam: the level either side,
# the loop count, and whether what follows the seam is the file from the loop start. The mixer resamples
# 48 kHz to the mix rate, so a looped pass and a fresh one sit a fraction of a sample apart: they are
# compared by correlation at the best of a few sample offsets, not sample for sample.
func _check_seam(source: AudioStreamMP3, loop_start: float, beats: int, bpm: float, wav_path: String) -> void:
	var stream: AudioStreamMP3 = source.duplicate()
	stream.loop = true
	stream.loop_offset = loop_start
	stream.beat_count = beats
	stream.bpm = bpm
	var loop_end := beats * 60.0 / bpm
	print("loop settings: loop_offset %.4f, beat_count %d, bpm %.4f -> loops at %.4f s, %.4f s before the file ends" % [
		loop_start, beats, bpm, loop_end, source.get_length() - loop_end])

	var lead := 2.0
	var playback := stream.instantiate_playback()
	playback.start(loop_end - lead)
	var across := PackedVector2Array()
	while across.size() < int(2.0 * lead * rate):
		across.append_array(playback.mix_audio(1.0, CHUNK))
	print("loops counted after %.1f s: %d" % [2.0 * lead, playback.get_loop_count()])

	var plain: AudioStreamMP3 = source.duplicate()
	plain.loop = false
	var reference := plain.instantiate_playback()
	reference.start(loop_start)
	var after := PackedVector2Array()
	while after.size() < int(lead * rate):
		after.append_array(reference.mix_audio(1.0, CHUNK))

	var seam_at := int(lead * rate)
	var skip := 1024
	var length := int(1.0 * rate)
	var best := -1.0
	var best_lag := 0
	for lag in range(-4, 5):
		var dot := 0.0
		var aa := 0.0
		var bb := 0.0
		for k in range(skip, skip + length):
			var a: float = across[seam_at + k + lag].x
			var b: float = after[k].x
			dot += a * b
			aa += a * a
			bb += b * b
		var c := dot / sqrt(aa * bb + 1e-12)
		if c > best:
			best = c
			best_lag = lag
	print("the second after the seam vs the file from the loop start: correlation %.5f at %+d samples" % [best, best_lag])

	var window := int(0.05 * rate)
	var line := ""
	for w in range(-10, 10):
		var sum := 0.0
		for k in window:
			var f: Vector2 = across[seam_at + w * window + k]
			sum += f.x * f.x + f.y * f.y
		line += " %.1f" % (10.0 * log(sum / (window * 2) + 1e-12) / log(10.0))
	print("level in 50 ms windows, half a second either side of the seam (dB):")
	print("  ", line)

	if wav_path != "":
		var pcm := PackedByteArray()
		pcm.resize(across.size() * 4)
		for k in across.size():
			pcm.encode_s16(k * 4, int(clampf(across[k].x, -1.0, 1.0) * 32767.0))
			pcm.encode_s16(k * 4 + 2, int(clampf(across[k].y, -1.0, 1.0) * 32767.0))
		var wav := AudioStreamWAV.new()
		wav.format = AudioStreamWAV.FORMAT_16_BITS
		wav.stereo = true
		wav.mix_rate = int(rate)
		wav.data = pcm
		wav.save_to_wav(wav_path)
		print("wrote the %.0f s either side of the seam to %s" % [lead, wav_path])
