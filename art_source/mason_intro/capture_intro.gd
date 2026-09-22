extends SceneTree

# Mason's entrance, shot beat by beat so it can be read without playing it: the fry trail leading up
# to his spot, him working along it with the trail shortening behind him, the gates slamming on him
# mid-mouthful, and the three lines that follow.
#
#   Godot.exe --path . --position 100,100 --resolution 960x540 --fixed-fps 60 \
#     --audio-driver Dummy --script res://art_source/mason_intro/capture_intro.gd -- out=<dir>
#
# The eating shots are taken off the intro's own gobble count rather than off a frame count, so a
# retimed walk still shoots the same reads. The lines are advanced with real ENTER presses.

const FIGHT := "res://Scenes/Bosses/MasonBossFightScene.tscn"
const BOSS_PATH := "Arena/MasonScene/MasonCharacterBody"
const INTRO_PATH := "Arena/MasonScene/MasonCharacterBody/StateManager/Intro"

var out_dir := ""
var boss: Node
var machine: Node
var intro: Node
var shots := 0
var last_line := ""


func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("out="):
			out_dir = arg.substr(4)
	_main.call_deferred()


func _process(_delta: float) -> bool:
	return false


func _main() -> void:
	change_scene_to_file(FIGHT)
	while current_scene == null or current_scene.scene_file_path != FIGHT:
		await process_frame
	await wait(4)
	boss = current_scene.get_node(BOSS_PATH)
	machine = boss.get_node("StateManager")
	intro = current_scene.get_node(INTRO_PATH)

	await _shot("01_trail_laid", "the ring opens on the trail, both fighters still outside it")
	await _until(func(): return _player().global_position.y <= intro.player_home.y + 1.0)
	await _shot("02_player_in", "the player has walked up, with the trail ahead of them")

	await _until(func(): return intro.gobbles >= 2)
	await _shot("03_first_fries", "he is in, head down, two pieces eaten")
	await _until(func(): return intro.gobbles >= _stops() - 2)
	await _shot("04_half_eaten", "past halfway, crumbs behind him and fries still ahead")
	await _until(func(): return intro.gobbles >= _stops())
	await _shot("05_last_fry", "the last piece goes and he is on his mark, still chewing")

	await _until(func(): return not _gates().is_open())
	await wait(14)
	await _shot("06_gates_shut", "the gates slam behind him")
	await wait(12)
	await _shot("07_startled", "and he looks up")

	await _next_line()
	await _shot("08_line_mason", "line 1: %s" % last_line)
	await _read_line()
	await _next_line()
	await _shot("09_line_danny", "line 2: %s" % last_line)
	await _read_line()
	await _next_line()
	await _shot("10_line_mason", "line 3: %s" % last_line)
	await _read_line()

	await _until(func(): return _card() != null and _card().is_playing())
	await wait(30)
	await _shot("11_card", "the lines are over and the VS card plays")
	await _until(func(): return machine.current_state.name != "Intro", 1200)
	await wait(30)
	await _shot("12_fight", "and the fight is on (%s)" % machine.current_state.name)

	print("SHOTS %d, gobbles %d of %d" % [shots, intro.gobbles, _stops()])
	quit(0)


func _shot(shot_name: String, note: String) -> void:
	print("%-16s gobbles=%-2d piles=%-2d state=%-6s  %s" % [shot_name, intro.gobbles,
		_piles_left(), machine.current_state.name, note])
	if out_dir == "":
		return
	await process_frame
	await RenderingServer.frame_post_draw
	var image := root.get_viewport().get_texture().get_image()
	image.save_png("%s/%s.png" % [out_dir, shot_name])
	shots += 1


# Pieces still drawn as fries rather than as the crumbs he left of them.
func _piles_left() -> int:
	var art: GDScript = load("res://Scripts/MasonArtLayout.gd")
	var left := 0
	for index in intro.piles.size():
		var piece = intro.piles[index]
		if is_instance_valid(piece) and piece is Sprite2D and piece.frame == art.FRY_TRAIL[index].frame:
			left += 1
	return left


func _stops() -> int:
	return load("res://Scripts/MasonArtLayout.gd").FRY_TRAIL.size()


# The next line, typed out and waiting on the player the way it does in the fight. Its text has to
# have changed: a press takes a frame to reach the balloon, so the line that is up the moment after
# one is still the line that was just read.
func _next_line() -> void:
	for i in 1200:
		var balloon := _balloon()
		if balloon and balloon.is_waiting_for_input and not balloon.dialogue_label.is_typing \
				and balloon.dialogue_line.text != last_line:
			last_line = balloon.dialogue_line.text
			return
		await physics_frame
	print("NO LINE after %s" % last_line)


func _read_line() -> void:
	_tap_enter()
	await wait(4)


func _until(cond: Callable, max_frames := 900) -> void:
	for i in max_frames:
		if cond.call():
			return
		await physics_frame
	print("TIMED OUT waiting")


func _player() -> Node:
	return current_scene.get_node("Arena/MainPlayer/CharacterBody2D")


func _gates() -> Node:
	return current_scene.get_node("Arena/Gates")


func _card() -> Node:
	return current_scene.get_node_or_null("Arena/VsCard")


func _balloon() -> Node:
	for child in current_scene.get_children():
		if child.has_method(&"rearm_input_lock"):
			return child
	return null


func _tap_enter() -> void:
	var down := InputEventKey.new()
	down.physical_keycode = KEY_ENTER
	down.keycode = KEY_ENTER
	down.pressed = true
	Input.parse_input_event(down)
	var up := InputEventKey.new()
	up.physical_keycode = KEY_ENTER
	up.keycode = KEY_ENTER
	Input.parse_input_event(up)


func wait(n: int) -> void:
	for i in n:
		await physics_frame
