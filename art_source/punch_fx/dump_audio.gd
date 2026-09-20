extends SceneTree

# Decodes SFX to 16-bit mono WAVs through Godot's own playback, so their loudness can be measured on the
# same scale as the synthesized ones (make_whoosh.py). Writes only to the folder given.
#   Godot.exe --headless --path . --script res://art_source/punch_fx/dump_audio.gd -- out=<dir> res://a.ogg ...


func _initialize() -> void:
	var out_dir := ""
	var paths: Array[String] = []
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("out="):
			out_dir = arg.substr(4)
		else:
			paths.append(arg)
	print("DUMP mix rate %d" % AudioServer.get_mix_rate())
	for path in paths:
		var stream: AudioStream = load(path)
		var playback := stream.instantiate_playback()
		playback.start(0.0)
		var frames := PackedVector2Array()
		for i in 400:
			var chunk := playback.mix_audio(1.0, 1024)
			if chunk.is_empty():
				break
			frames.append_array(chunk)
			if not playback.is_playing():
				break
		var bytes := PackedByteArray()
		bytes.resize(frames.size() * 2)
		for i in frames.size():
			var s := clampf((frames[i].x + frames[i].y) * 0.5, -1.0, 1.0)
			bytes.encode_s16(i * 2, int(round(s * 32767.0)))
		var wav := AudioStreamWAV.new()
		wav.format = AudioStreamWAV.FORMAT_16_BITS
		wav.mix_rate = AudioServer.get_mix_rate()
		wav.stereo = false
		wav.data = bytes
		var name := path.get_file().get_basename()
		wav.save_to_wav("%s/%s.wav" % [out_dir, name])
		print("DUMP %s: %d frames (%.3f s)" % [path, frames.size(), frames.size() / AudioServer.get_mix_rate()])
	quit(0)
