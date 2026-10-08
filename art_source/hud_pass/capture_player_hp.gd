extends SceneTree

# Drives the player's health containers through every state the final art has and saves a strip of
# what each one draws, over a flat backdrop so only the tray and its hearts are in the picture.
#   Godot.exe --path . --position 100,100 --resolution 320x1080 --fixed-fps 60 \
#     --script res://art_source/hud_pass/capture_player_hp.gd -- out=<dir>
# Headless prints the geometry without the picture.

const PlayerHealthArtLayout := preload("res://Scripts/PlayerHealthArtLayout.gd")
const DefenseHypeArtLayout := preload("res://Scripts/DefenseHypeArtLayout.gd")

var out_dir := ""
var layer: CanvasLayer
var hearts: Control
var shots: Array[Image] = []


func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("out="):
			out_dir = arg.substr(4)
	_main.call_deferred()


func _process(_delta: float) -> bool:
	return false


func wait(n: int) -> void:
	for i in n:
		await process_frame


func _main() -> void:
	layer = CanvasLayer.new()
	root.add_child(layer)
	var backdrop := ColorRect.new()
	backdrop.color = Color(0.16, 0.14, 0.2)
	backdrop.size = Vector2(root.size)
	layer.add_child(backdrop)
	hearts = load("res://Scenes/Player/PlayerHealthScene.tscn").instantiate()
	layer.add_child(hearts)
	await wait(2)

	var spec := PlayerHealthArtLayout.hearts()
	print("tray at %s size %s" % [spec.position, spec.size])
	print("stamina frame at %s" % DefenseHypeArtLayout.STAMINA_BAR_POSITION)
	print("row right edge %.1f" % PlayerHealthArtLayout.row_right_edge())
	var frame: Control = hearts.get_child(0)
	print("hud frame rect %s" % frame.get_global_rect())
	for i in hearts.containers.size():
		var rect: TextureRect = hearts.containers[i]
		print("  container %d %s texture %s %s" % [i, rect.get_global_rect(),
			rect.texture.get_size(), rect.texture.resource_path.get_file()])
	if not hearts.breaks.is_empty():
		print("  tray %s warn %s (%d frames)" % [hearts.tray.texture.get_size(),
			hearts.tray_warn.texture.get_size(), hearts.tray_warn.hframes])
		for i in hearts.breaks.size():
			print("  break %d at %s frames %d" % [i, hearts.breaks[i].position, hearts.breaks[i].hframes])

	if out_dir == "":
		quit(0)
		return

	# Full, a half, both frames of the warning heartbeat, the last half, and the frames a break and a
	# gain actually play.
	var full := PlayerHealthArtLayout.CONTAINERS * 2
	for health in [full, full - 1]:
		hearts.update_health(health)
		await _shot(6)
	# A whole heart left, then both beat frames at the last half: the run has to follow what the
	# container is actually holding. One frame past LOW_FRAME_TIME, so the two shots straddle it.
	hearts.update_health(2)
	await _shot(6)
	hearts.update_health(1)
	for i in 2:
		await _shot(int(PlayerHealthArtLayout.LOW_FRAME_TIME * 60.0) + 1)
	hearts.update_health(full)
	await wait(2)
	hearts.update_health(full - 2)
	for i in 5:
		await _shot(3)
	hearts.update_health(full)
	for i in 4:
		await _shot(3)

	var strip := Image.create_empty(shots[0].get_width() * shots.size(), shots[0].get_height(),
		false, shots[0].get_format())
	for i in shots.size():
		strip.blit_rect(shots[i], Rect2i(Vector2i.ZERO, shots[i].get_size()),
			Vector2i(i * shots[0].get_width(), 0))
	var path := out_dir + "/player_hp_states.png"
	strip.save_png(path)
	print("SAVED %s (%d shots)" % [path, shots.size()])
	quit(0)


func _shot(settle: int) -> void:
	await wait(settle)
	await RenderingServer.frame_post_draw
	var spec := PlayerHealthArtLayout.hearts()
	var image := root.get_viewport().get_texture().get_image()
	var cut := Image.create_empty(int(spec.size.x) + 20, int(spec.size.y) + 40, false, image.get_format())
	cut.blit_rect(image, Rect2i(Vector2i(spec.position) - Vector2i(10, 20),
		Vector2i(spec.size) + Vector2i(20, 40)), Vector2i.ZERO)
	shots.append(cut)
