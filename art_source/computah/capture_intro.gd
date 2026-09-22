extends SceneTree

# Computah's entrance, shot beat by beat so it can be read without playing it: him dead in the ring
# with a flat battery, Greyson's command that does nothing, the dead air, the command that works and
# the battery coming up 2 -> 1 -> 0.
#
#   Godot.exe --path . --position 100,100 --resolution 1280x720 --fixed-fps 60 \
#     --audio-driver Dummy --script res://art_source/computah/capture_intro.gd -- out=<dir>
#
# The lines are advanced with real ENTER presses, one per line, and the shots of the charge are taken
# off his charge state rather than off a frame count, so a retune of CELL_TIME still shoots the same
# three reads.

const FIGHT := "res://Scenes/Bosses/ComputahBossFightScene.tscn"
const BOSS_PATH := "Arena/ComputahScene/ComputahCharacterBody"

var out_dir := ""
var boss: Node
var machine: Node
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
	await wait(2)
	boss = current_scene.get_node(BOSS_PATH)
	machine = boss.get_node("StateManager")

	await _next_line()
	await _shot("01_go_get_him", "line 1 up, and he is dead on the mat: one red cell, red antenna")
	await _read_line()

	await wait(36)
	await _shot("02_dead_air_0.6s", "0.6 s into the dead air: the balloon is gone and nothing happens")
	await wait(120)
	await _shot("03_dead_air_2.6s", "2.6 s in, still nothing - the pause is the joke")

	await _next_line()
	await _shot("04_my_bad", "line 2 up")
	await _read_line()
	await _next_line()
	await _shot("05_the_command", "line 3 up: the words he does take")
	await _read_line()

	await _until(func(): return boss.battery.visible)
	await wait(18)
	await _shot("06_charge_low", "the charge starts: the gauge fills, the chest is still one red cell")
	await _until(func(): return boss.charge_state == 1)
	await _shot("07_charge_half", "two amber cells, amber antenna")
	await _until(func(): return boss.charge_state == 0)
	await _shot("08_charge_full", "four green cells, and he starts moving")
	await _until(func(): return boss.current_anim == &"taunt")
	await wait(6)
	await _shot("09_live", "the taunt he holds once he is full")
	await _until(func(): return _card() != null and _card().is_playing())
	await wait(30)
	await _shot("10_card", "the lines are over and the VS card plays")
	await _until(func(): return machine.current_state.name != "Intro", 1200)
	await wait(30)
	await _shot("11_fight", "and the fight is on (%s)" % machine.current_state.name)

	print("SHOTS %d" % shots)
	quit(0)


func _shot(shot_name: String, note: String) -> void:
	var crowd := get_nodes_in_group("arena_crowd")
	print("%-20s charge=%d anim=%-8s state=%-6s crowd=%d@%d  %s" % [shot_name, boss.charge_state,
		boss.current_anim, machine.current_state.name, crowd.size(),
		crowd[0].frame if not crowd.is_empty() else -1, note])
	if out_dir == "":
		return
	await process_frame
	await RenderingServer.frame_post_draw
	var image := root.get_viewport().get_texture().get_image()
	image.save_png("%s/%s.png" % [out_dir, shot_name])
	shots += 1


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


# One press, and the frames it takes to land.
func _read_line() -> void:
	_tap_enter()
	await wait(4)


func _until(cond: Callable, max_frames := 600) -> void:
	for i in max_frames:
		if cond.call():
			return
		await physics_frame
	print("TIMED OUT waiting")


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
