extends SceneTree
# Confirms every shipped theme imports as a genuinely looping stream, rather than relying on the
# fight code to force it onto the shared resource at runtime. Godot's WAV importer numbers
# edit/loop_mode as 0=Detect, 1=Disabled, 2=Forward - the 1 that looks like LOOP_FORWARD is Disabled.
#   Godot.exe --headless --path . --script res://art_source/music/loopcheck.gd
# A theme the user has swapped for a track of their own is still ours, and moved to OriginalThemes/.
const ORIGINAL_THEMES := "res://Assets/Audio/Music/OriginalThemes/%s_theme.wav"


func _initialize() -> void:
	var names := ["DISABLED", "FORWARD", "PINGPONG", "BACKWARD"]
	var bad := 0
	for n in ["eric", "greyson", "jordan", "carter", "josh", "mason", "danny", "liam", "matt", "burak", "danny_sumo", "jordan_final"]:
		var path := "res://Assets/Audio/Music/%s_theme.wav" % n
		if not ResourceLoader.exists(path) and ResourceLoader.exists(ORIGINAL_THEMES % n):
			path = ORIGINAL_THEMES % n
		var s = load(path)
		if s == null:
			print("%-8s MISSING" % n); bad += 1; continue
		var mode: int = s.loop_mode
		var ok: bool = mode == AudioStreamWAV.LOOP_FORWARD and s.loop_end > 0
		if not ok:
			bad += 1
		print("%-8s %-8s loop_end %-9d length %.3f  %s" % [n, names[mode], s.loop_end, s.get_length(), "OK" if ok else "*** WRONG ***"])
	print("RESULT bad=%d" % bad)
	quit(1 if bad > 0 else 0)
