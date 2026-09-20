# Captures Eric's fight as separate layers for the UI mocks: the world with his and the player's
# sprites hidden, the HUD alone on a transparent background, and the full frame. Lives outside the
# project and writes only to CAP_OUT. The window is small; the root viewport renders at 1920x1080
# through viewport stretch, so the saved frames are 1:1 game pixels.
extends SceneTree

var frames := 0
var out_dir := ""
var mode := ""

func _initialize() -> void:
	out_dir = OS.get_environment("CAP_OUT")
	mode = OS.get_environment("CAP_MODE")
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_VIEWPORT
	root.content_scale_size = Vector2i(1920, 1080)
	if mode == "v2":
		var pacing: GDScript = load("res://Scripts/EricPacing.gd")
		pacing.set("version", 2)
		print("CAP pacing version -> ", pacing.get("version"))
	change_scene_to_file("res://Scenes/Bosses/EricBossFightScene.tscn")

func _hide_balloons(n: Node) -> void:
	for c in n.get_children():
		var nm := String(c.name).to_lower()
		if nm.find("balloon") >= 0 or (c is CanvasLayer and nm.find("dialog") >= 0):
			if c is CanvasItem or c is CanvasLayer:
				c.visible = false
		_hide_balloons(c)

func _layers(n: Node, out: Array) -> void:
	for c in n.get_children():
		if c is CanvasLayer:
			out.append(c)
		_layers(c, out)

func _save(file_name: String) -> void:
	var img := root.get_texture().get_image()
	img.save_png(out_dir + "/" + file_name)
	print("CAP saved ", file_name, " ", img.get_size(), " ", img.get_format())

func _process(_delta: float) -> bool:
	frames += 1
	if frames == 5:
		var dm = root.get_node_or_null("DialogueManager")
		if dm:
			dm.dialogue_ended.emit(null)
	if frames >= 6:
		_hide_balloons(root)
	var scene := current_scene
	if frames == 12:
		var all: Array = []
		_layers(root, all)
		for l in all:
			print("CAP layer ", l.get_path(), " layer=", l.layer, " visible=", l.visible)
	if frames == 14:
		_save("real_%s.png" % mode)
		for path in ["Arena/EricBossScene/CharacterBody2D/Sprite2D", "Arena/MainPlayer/CharacterBody2D/Sprite2D"]:
			var s = scene.get_node_or_null(path)
			if s:
				s.visible = false
		var all: Array = []
		_layers(root, all)
		for l in all:
			l.visible = false
	if frames == 16:
		_save("world_%s.png" % mode)
		var all: Array = []
		_layers(root, all)
		for l in all:
			if not String(l.name).to_lower().contains("dialog") and not String(l.name).to_lower().contains("balloon"):
				l.visible = true
		_hide_balloons(root)
		scene.get_node("Arena").visible = false
		root.transparent_bg = true
	if frames == 18:
		_save("hud_%s.png" % mode)
		quit()
	return false
