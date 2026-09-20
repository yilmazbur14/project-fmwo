extends SceneTree
# Confirms every shipped theme imports as a genuinely looping stream, rather than relying on the
# fight code to force it onto the shared resource at runtime. Godot's WAV importer numbers
# edit/loop_mode as 0=Detect, 1=Disabled, 2=Forward - the 1 that looks like LOOP_FORWARD is Disabled.
#   Godot.exe --headless --path . --script res://art_source/music/loopcheck.gd
func _initialize() -> void:
	var names := ["DISABLED", "FORWARD", "PINGPONG", "BACKWARD"]
	var bad := 0
	for n in ["eric", "greyson", "jordan", "carter", "josh", "mason", "danny", "liam"]:
		var s = load("res://Assets/Audio/Music/%s_theme.wav" % n)
		if s == null:
			print("%-8s MISSING" % n); bad += 1; continue
		var mode: int = s.loop_mode
		var ok: bool = mode == AudioStreamWAV.LOOP_FORWARD and s.loop_end > 0
		if not ok:
			bad += 1
		print("%-8s %-8s loop_end %-9d length %.3f  %s" % [n, names[mode], s.loop_end, s.get_length(), "OK" if ok else "*** WRONG ***"])
	print("RESULT bad=%d" % bad)
	quit(1 if bad > 0 else 0)
