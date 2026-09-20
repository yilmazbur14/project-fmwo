extends SceneTree

# Measures the player against Eric on screen and saves a frame of the two standing side by side, so
# a size change can be judged rather than argued about. Prints every box that depends on his size.
#   Godot.exe --path . --position 100,100 --resolution 1920x1080 --fixed-fps 60 \
#     --script res://art_source/player_size/probe_player_size.gd -- out=<dir> tag=<name>
# Headless (numbers only, no png):
#   Godot.exe --headless --path . --fixed-fps 60 --script res://... -- tag=<name>

const FIGHT := "res://Scenes/Bosses/EricBossFightScene.tscn"

var out_dir := ""
var tag := "now"
# Only for the look: a scale forced on the body before the capture, so a size can be judged on screen
# before anything in the project moves.
var forced_scale := 0.0
var player: CharacterBody2D
var boss: CharacterBody2D


func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("out="):
			out_dir = arg.substr(4)
		elif arg.begins_with("tag="):
			tag = arg.substr(4)
		elif arg.begins_with("scale="):
			forced_scale = float(arg.substr(6))
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
	player = current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
	boss = current_scene.get_node("Arena/EricBossScene/CharacterBody2D")
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
		await wait(2)
	for child in current_scene.get_children():
		if child is CanvasLayer:
			child.queue_free()
	root.get_node("DialogueManager").dialogue_ended.emit(null)
	await wait(1)
	var card := current_scene.get_node_or_null("Arena/VsCard")
	if card:
		if card.is_playing():
			card.skip()
			for i in 60:
				if not card.is_playing():
					break
				await physics_frame
		card.grace_until_msec = 0
	await wait(2)

	_report()

	if out_dir != "":
		await _capture()
	quit(0)


func _rect(shape: CollisionShape2D) -> Rect2:
	return shape.global_transform * shape.shape.get_rect()


func _v(r: Rect2) -> String:
	return "pos (%.2f,%.2f) size (%.2f,%.2f)" % [r.position.x, r.position.y, r.size.x, r.size.y]


# What the live frame actually paints, in screen px: the frame cut out of the sheet, its blank
# border trimmed, put through the sprite's own transform.
func _drawn(sprite: Sprite2D) -> Rect2:
	var image := sprite.texture.get_image()
	var size := Vector2i(image.get_width() / sprite.hframes, image.get_height() / sprite.vframes)
	var frame := Rect2i(Vector2i(sprite.frame_coords.x, sprite.frame_coords.y) * size, size)
	var cut := Image.create_empty(size.x, size.y, false, image.get_format())
	cut.blit_rect(image, frame, Vector2i.ZERO)
	var used := cut.get_used_rect()
	var local := Vector2(used.position) - Vector2(size) * 0.5 + sprite.offset
	return Rect2(sprite.global_transform * local, Vector2(used.size) * sprite.global_scale)


func _report() -> void:
	print("== player size probe: %s ==" % tag)
	var sprite: Sprite2D = player.get_node("Sprite2D")
	print("body scale %s  sprite scale %s" % [player.scale, sprite.global_scale])
	print("player drawn   %s" % _v(_drawn(sprite)))
	print("player body    %s" % _v(_rect(player.get_node("CollisionShape2D"))))
	print("player hurtbox %s" % _v(_rect(player.get_node("Hurtbox/CollisionShape2D"))))
	var ghost: CollisionShape2D = player.get_parent().get_node("DodgeGhost/CollisionShape2D")
	print("dodge ghost    size (%.2f,%.2f)" % [ghost.shape.size.x * ghost.global_scale.x,
		ghost.shape.size.y * ghost.global_scale.y])
	print("feel_v2 %s" % player.feel_v2)
	for facing in [0, 1, 2, 3]:
		var box: Rect2 = player.punch_box(facing)
		var world := Rect2(box.position * player.scale, box.size * player.scale)
		print("  punch %d texels %s -> world px %s" % [facing, _v(box), _v(world)])
	var bs: Sprite2D = boss.get_node("Sprite2D")
	print("eric scale %s" % boss.scale)
	print("eric drawn     %s" % _v(_drawn(bs)))
	print("eric body      %s" % _v(_rect(boss.get_node("CollisionShape2D"))))


func _capture() -> void:
	if forced_scale > 0.0:
		player.scale = Vector2(forced_scale, forced_scale)
	# Beside Eric on his left, both feet on the same row, so the two read against each other.
	player.global_position = boss.global_position + Vector2(-260, 0)
	player.velocity = Vector2.ZERO
	await wait(4)
	await process_frame
	await RenderingServer.frame_post_draw
	var image := root.get_viewport().get_texture().get_image()
	var path := "%s/player_beside_eric_%s.png" % [out_dir, tag]
	image.save_png(path)
	print("SAVED %s" % path)
