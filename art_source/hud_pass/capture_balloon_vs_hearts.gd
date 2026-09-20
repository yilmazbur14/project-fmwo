extends SceneTree

# A fight's first pre-fight line with the health containers up, so where the dialogue box starts can
# be judged against the tray rather than against row_right_edge()'s number.
#   Godot.exe --path . --position 100,100 --resolution 1920x1080 --fixed-fps 60 \
#     --script res://art_source/hud_pass/capture_balloon_vs_hearts.gd -- out=<dir>

const PlayerHealthArtLayout := preload("res://Scripts/PlayerHealthArtLayout.gd")
const FIGHT := "res://Scenes/Bosses/EricBossFightScene.tscn"

var out_dir := ""


func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("out="):
			out_dir = arg.substr(4)
	_main.call_deferred()


func _process(_delta: float) -> bool:
	return false


func wait(n: int) -> void:
	for i in n:
		await physics_frame


func _main() -> void:
	change_scene_to_file(FIGHT)
	while current_scene == null or current_scene.scene_file_path != FIGHT:
		await process_frame
	await wait(3)
	var intro: Node = null
	for node in current_scene.find_children("*", "Node", true, false):
		if node.has_method(&"finish_entrance"):
			intro = node
			break
	if intro:
		for i in 60:
			if intro.entered:
				break
			await physics_frame
		if not intro.finished:
			intro.skip()
	for i in 600:
		await physics_frame
		var balloon := _balloon()
		if balloon and balloon.panel.offset_left != 0.0:
			break
	var balloon := _balloon()
	if balloon == null:
		print("NO BALLOON")
		quit(1)
		return
	print("panel offset_left %.1f right %.1f" % [balloon.panel.offset_left, balloon.panel.offset_right])
	print("panel rect %s" % balloon.panel.get_global_rect())
	print("row right edge %.1f" % PlayerHealthArtLayout.row_right_edge())
	if out_dir != "":
		await process_frame
		await RenderingServer.frame_post_draw
		var image := root.get_viewport().get_texture().get_image()
		image.save_png(out_dir + "/balloon_vs_hearts.png")
		print("SAVED")
	quit(0)


func _balloon() -> Node:
	for child in current_scene.get_children():
		if child.has_method(&"rearm_input_lock"):
			return child
	return null
