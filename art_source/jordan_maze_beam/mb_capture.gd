extends SceneTree

# The dark maze's full-meter beam, captured from the real god fight for the beam redesign's approval mocks. It plays
# attack 1 on the drawn path with no presses (the defence suite's "idle" tier: the meter fills, the beam fires down the
# whole route onto the player at the start), and grabs every frame from just before the meter fills until the lights
# are back up, plus stills of the lit maze. Each frame's numbers go into frames.json: the beat and its clock, Greyson's
# animation and frame and his sprite's transform, the muzzle, the player, the view's canvas transform. The beam's route
# is logged once.
#
# It writes ONLY into the out dir given after "--" (refused if it is inside the project), changes nothing in the
# project, and sets nothing but the maze's pinned route, a static var, in this process.
#   Godot.exe --path <project> --position 100,100 --resolution 1920x1080 --fixed-fps 60 \
#       --script res://art_source/jordan_maze_beam/mb_capture.gd -- <out dir> [hide|show]
# "hide" (the default) hides today's placeholder beam and cannon glow, so the new art can be laid over the frames;
# "show" keeps them, for the before-and-after.

const FIGHT := "res://Scenes/Bosses/JordanGodFightScene.tscn"
const MAZE_SCRIPT := "res://Scripts/States/JordanGod/JordanComboMaze.gd"
const Layout := preload("res://Scripts/JordanMazeLayout.gd")
const PLAYER_PATH := "Arena/MainPlayer/CharacterBody2D"
# Grab from this long before the meter fills, and this many frames after the lights are up.
const PRE_SECONDS := 0.75
const POST_FRAMES := 20
const TIMEOUT_FRAMES := 60 * 60

var out_dir := ""
var hide_beam := true
var scene: Node
var maze: Node
var frames := 0
var grabbing := false
var grabbed := 0
var post := -1
var entries: Array = []
var dark_still := false
var route_logged := false
var finishing := 0


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	if args.is_empty():
		push_error("mb_capture: no out dir")
		quit(2)
		return
	out_dir = args[0].replace("\\", "/")
	if args.size() > 1:
		hide_beam = args[1] != "show"
	var project := ProjectSettings.globalize_path("res://").replace("\\", "/").to_lower()
	var target := out_dir.to_lower()
	if not target.ends_with("/"):
		target += "/"
	if target.begins_with(project):
		push_error("mb_capture: refusing to write inside the project: %s" % out_dir)
		quit(2)
		return
	DirAccess.make_dir_recursive_absolute(out_dir)
	var typed: Array[Vector2i] = []
	for cell in Layout.DRAWN_PATH:
		typed.append(cell)
	load(MAZE_SCRIPT).pinned_route = typed
	scene = load(FIGHT).instantiate()
	root.add_child(scene)
	current_scene = scene


func _find_maze() -> Node:
	for node in scene.find_children("*", "Node", true, false):
		var script: Script = node.get_script()
		if script != null and script.resource_path == MAZE_SCRIPT:
			return node
	return null


func _process(_delta: float) -> bool:
	frames += 1
	if frames > TIMEOUT_FRAMES:
		print("mb_capture: TIMEOUT")
		_save_log()
		return true
	if maze == null:
		maze = _find_maze()
		return false
	if hide_beam:
		for name in ["MazeBeam", "CannonGlow"]:
			for node in scene.find_children(name, "", true, false):
				(node as CanvasItem).visible = false
	# The lit maze: every 20 frames while the walls stand lit before the dark, the last grab before it wins.
	if maze.walls != null and is_instance_valid(maze.walls) and not maze.dark and not maze.beamed and maze.run_id > 0 and frames % 20 == 0:
		_grab(out_dir + "/still_lit_maze.png")
	if not dark_still and maze.dark and maze.meter_on and maze.meter_clock > 3.0:
		dark_still = true
		_grab(out_dir + "/still_dark_maze.png")
	if not grabbing and post < 0 and maze.meter_on and maze.meter_clock >= Layout.METER_TIME - PRE_SECONDS:
		grabbing = true
	if grabbing:
		# Recorded as the frame is drawn, so the numbers are the ones the image was drawn with (a shake's tween fires
		# after this script's _process).
		_grab(out_dir + "/f%04d.png" % grabbed, true)
		grabbed += 1
		if maze.beamed and maze.beat == maze.Beat.OFF and post < 0:
			post = POST_FRAMES
		if post >= 0:
			post -= 1
			if post < 0:
				grabbing = false
				_grab(out_dir + "/still_after.png")
				finishing = 3
	if finishing > 0:
		finishing -= 1
		if finishing == 0:
			_save_log()
			print("mb_capture: DONE %d frames" % grabbed)
			return true
	return false


func _record(index: int) -> void:
	var grey: Node2D = maze.greyson()
	var player: Node2D = scene.get_node(PLAYER_PATH)
	var entry := {
		"i": index,
		"physics": Engine.get_physics_frames(),
		"beat": maze.Beat.keys()[maze.beat],
		"beat_clock": maze.beat_clock,
		"meter_clock": maze.meter_clock,
		"cells": maze.cells,
		"canvas": _xf(root.canvas_transform),
		"final": _xf(root.get_final_transform()),
		"player": _v(player.global_position),
		"dark_alpha": maze.god.darkness.modulate.a if is_instance_valid(maze.god.darkness) else 0.0,
	}
	if grey != null:
		var sprite: Sprite2D = grey.sprite
		entry["greyson_anim"] = String(grey.current_anim)
		entry["greyson_frame"] = sprite.frame
		entry["greyson_sprite"] = _xf(sprite.get_global_transform())
		entry["greyson_rect"] = [sprite.get_rect().position.x, sprite.get_rect().position.y,
			sprite.get_rect().size.x, sprite.get_rect().size.y]
		entry["greyson_flip"] = sprite.flip_h
		entry["muzzle"] = _v(maze._muzzle())
	if not route_logged and maze.beam_route.size() > 0:
		route_logged = true
		entry["route"] = []
		for p in maze.beam_route:
			entry["route"].append(_v(p))
	entries.append(entry)


func _v(p: Vector2) -> Array:
	return [p.x, p.y]


func _xf(t: Transform2D) -> Array:
	return [t.x.x, t.x.y, t.y.x, t.y.y, t.origin.x, t.origin.y]


func _save_log() -> void:
	var head := {
		"hide_beam": hide_beam,
		"route_cells": [],
		"block": _v(Layout.BLOCK),
		"origin": _v(Layout.ORIGIN),
		"beam_height": Layout.BEAM_HEIGHT,
		"soles_over_origin": Layout.SOLES_OVER_ORIGIN,
		"frames": entries,
	}
	for cell in Layout.DRAWN_PATH:
		head["route_cells"].append([cell.x, cell.y])
	var file := FileAccess.open(out_dir + "/frames.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(head, " "))
	file.close()


func _grab(path: String, record := false) -> void:
	var index := grabbed
	RenderingServer.frame_post_draw.connect(func() -> void:
		if record:
			_record(index)
		root.get_texture().get_image().save_png(path)
	, CONNECT_ONE_SHOT)
