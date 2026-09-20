extends SceneTree

# Checks FightOutro's outro_line_delay hook against every boss fight that exists, on a win and on a
# loss: exactly one outro each time, the line at LINE_DELAY for every boss that doesn't ask for more,
# and Carter's losing line held until his victory pose has landed.
#   Godot.exe --headless --fixed-fps 60 --script res://art_source/carter_fight/verify_outro_timing.gd
#
# The fight is ended by calling FightOutro.finish_fight() directly, which is exactly the path every
# boss's defeat and the player's death both take, and the line is timed from that call to the frame
# DialogueManager starts the outro's dialogue.
# FightOutro and DialogueManager are loaded at run time rather than preloaded: FightOutro names the
# DialogueManager autoload, and a --script SceneTree is compiled before autoloads exist.

const STEP := 1.0 / 60.0
# Long enough for the fight's own opening to have started, short enough to be before any pre-fight
# lines, so the only dialogue that can start is the outro's.
const SETTLE_FRAMES := 20
const GIVE_UP := 10.0

var outro_script: GDScript
var cases: Array = []
var case_index := -1
var phase := "start"
var frames := 0
var clock := 0.0
var line_at := -1.0
var outro_paths: Array[String] = []
var expected := 0.0
var failures: Array[String] = []
var notes: Array[String] = []
var done := false


func _initialize() -> void:
	for boss in load("res://Scripts/GameProgress.gd").BOSSES:
		if ResourceLoader.exists(boss.scene):
			cases.append({"name": boss.name, "scene": boss.scene, "won": true})
			cases.append({"name": boss.name, "scene": boss.scene, "won": false})


func _process(_delta: float) -> bool:
	if done:
		return true
	match phase:
		"start":
			outro_script = load("res://Scripts/FightOutro.gd")
			root.get_node("DialogueManager").dialogue_started.connect(_on_dialogue_started)
			_next_case()
		"loading":
			# change_scene_to_file() swaps the scene at the end of a frame; wait until it has.
			if current_scene and current_scene.scene_file_path == cases[case_index].scene:
				frames = 0
				phase = "settle"
		"settle":
			frames += 1
			if frames >= SETTLE_FRAMES:
				_end_fight()
		"wait":
			clock += STEP
			if line_at >= 0.0 or clock >= GIVE_UP:
				_judge()
				_next_case()
	return done


# The same way the game enters a fight, so current_scene is already set while its nodes get ready.
func _next_case() -> void:
	var outro := root.get_node_or_null(^"FightOutro")
	if outro:
		outro.free()
	case_index += 1
	if case_index >= cases.size():
		_finish()
		return
	change_scene_to_file(cases[case_index].scene)
	phase = "loading"


func _end_fight() -> void:
	var case: Dictionary = cases[case_index]
	outro_paths.clear()
	for boss in get_nodes_in_group(outro_script.BOSS_GROUP):
		if "OUTRO_DIALOGUE" in boss:
			outro_paths.append(boss.OUTRO_DIALOGUE)
	clock = 0.0
	line_at = -1.0
	outro_script.finish_fight(self, case.won)
	# The same answer FightOutro will have got: asked after on_player_defeated() has run.
	expected = outro_script.LINE_DELAY
	for boss in get_nodes_in_group(outro_script.BOSS_GROUP):
		if boss.has_method("outro_line_delay"):
			expected = maxf(expected, boss.outro_line_delay(case.won))
	phase = "wait"


func _on_dialogue_started(resource: DialogueResource) -> void:
	if phase == "wait" and line_at < 0.0 and resource.resource_path in outro_paths:
		line_at = clock


func _judge() -> void:
	var case: Dictionary = cases[case_index]
	var label := "%s, %s" % [case.name, "player won" if case.won else "player lost"]
	var outros := root.get_children().filter(func(child: Node) -> bool: return child.name == "FightOutro").size()
	_expect(outros == 1, "%s: %d outros" % [label, outros])
	if line_at < 0.0:
		failures.append("%s: the outro line never started within %.0f s" % [label, GIVE_UP])
		return
	_expect(absf(line_at - expected) <= STEP * 1.5, "%s: line at %.2f s, expected %.2f s" % [label, line_at, expected])
	var held := not is_equal_approx(expected, outro_script.LINE_DELAY)
	notes.append("%-30s line at %.2f s%s" % [label, line_at, "   <- held for his pose" if held else ""])


func _expect(ok: bool, message: String) -> void:
	if not ok:
		failures.append(message)


func _finish() -> void:
	done = true
	print("")
	for note in notes:
		print("  ", note)
	print("")
	for failure in failures:
		printerr("FAIL  ", failure)
	print("outro timing: %s" % ("all checks passed" if failures.is_empty() else "%d FAILED" % failures.size()))
	quit(0 if failures.is_empty() else 1)
