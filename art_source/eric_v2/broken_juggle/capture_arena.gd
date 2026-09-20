# Captures a clean frame of Eric's arena for the review mocks (Eric and player sprites and dialogue hidden).
# Run (writes only to CAP_OUT; a window opens at 100,100 at native size because the mocks need 1:1 pixels):
#   CAP_OUT=<dir> Godot.exe --path <project> --position 100,100 --resolution 1920x1080 --fixed-fps 30 --script <this file>
extends SceneTree
# Loads Eric's fight, ends the intro dialogue, hides Eric's and the player's sprites and any dialogue
# balloon, and saves the rendered viewport. Writes only to CAP_OUT.

var frames := 0
var out_dir := ""

func _initialize() -> void:
	out_dir = OS.get_environment("CAP_OUT")
	change_scene_to_file("res://Scenes/Bosses/EricBossFightScene.tscn")

func _hide_balloons(n: Node) -> void:
	for c in n.get_children():
		var nm := String(c.name).to_lower()
		if nm.find("balloon") >= 0 or c.get_class() == "CanvasLayer" and nm.find("dialog") >= 0:
			if c is CanvasItem or c is CanvasLayer:
				c.visible = false
		_hide_balloons(c)

func _list(n: Node, depth: int) -> void:
	if depth > 3:
		return
	for c in n.get_children():
		print("  ".repeat(depth), c.name, " <", c.get_class(), ">")
		_list(c, depth + 1)

func _process(_delta: float) -> bool:
	frames += 1
	if frames == 5:
		var dm = root.get_node_or_null("DialogueManager")
		if dm:
			dm.dialogue_ended.emit(null)
	if frames == 20:
		print("ROOT CHILDREN")
		_list(root, 0)
	if frames >= 20 and frames < 60:
		var scene := current_scene
		if scene:
			var es = scene.get_node_or_null("Arena/EricBossScene/CharacterBody2D/Sprite2D")
			if es: es.visible = false
			var ps = scene.get_node_or_null("Arena/MainPlayer/CharacterBody2D/Sprite2D")
			if ps: ps.visible = false
		_hide_balloons(root)
	if frames == 60:
		var img := root.get_viewport().get_texture().get_image()
		img.save_png(out_dir + "/arena_clean.png")
		print("SAVED ", out_dir + "/arena_clean.png")
		quit()
	return false
