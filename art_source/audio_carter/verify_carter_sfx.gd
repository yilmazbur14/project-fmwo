extends SceneTree

const NAMES := [
	"carter_eye_flash", "carter_warp", "carter_dark", "carter_rush_1", "carter_rush_2", "carter_rush_3",
	"carter_strike", "carter_parry_break", "carter_fake_punish", "carter_finish", "carter_spent",
]

var _players: Array[AudioStreamPlayer] = []
var _frames := 0


func _initialize() -> void:
	for name in NAMES:
		var path := "res://Assets/Audio/SFX/%s.wav" % name
		var stream := load(path) as AudioStreamWAV
		if stream == null:
			printerr("FAILED to load ", path)
			continue
		var player := AudioStreamPlayer.new()
		player.stream = stream
		root.add_child(player)
		_players.append(player)
		print("%-20s %s  %d Hz  %s  %.3f s  loop %d" % [
			name, "16-bit" if stream.format == AudioStreamWAV.FORMAT_16_BITS else "format %d" % stream.format,
			stream.mix_rate, "stereo" if stream.stereo else "mono", stream.get_length(), stream.loop_mode])

	var voices := load("res://Scripts/DialogueVoices.gd")
	var carter: Dictionary = voices.VOICES["carter"]
	print("carter voice: %d streams, pitch %.3f-%.3f, melody %s, every %d, volume %.1f dB" % [
		carter.streams.size(), carter.pitch_min, carter.pitch_max, str(carter.melody), carter.every,
		carter.volume_db])


func _process(_delta: float) -> bool:
	_frames += 1
	if _frames == 1:
		for player in _players:
			player.play()
		return false
	if _frames < 4:
		return false
	var playing := 0
	for player in _players:
		if player.playing:
			playing += 1
	print("%d of %d still playing after %d frames" % [playing, _players.size(), _frames])
	for player in _players:
		player.stream = null
		player.free()
	_players.clear()
	return true
