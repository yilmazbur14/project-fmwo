# Reference captures for the pause-menu mock. Run as a SceneTree script from OUTSIDE the project's
# resource tree (art_source is .gdignore'd), so nothing in the project is touched:
#   Godot --path <project> -s <abs>/capture_ref.gd --position 100,100 --resolution 960x540 \
#         --fixed-fps 30 --audio-driver Dummy
# Env: CAP_OUT = folder the PNGs go to,
#      CAP_MODE = menu_pad | menu_pad_slider | victory | defeat | fight | pause | pause_confirm,
#      CAP_SCENE = a fight scene path, overriding Eric's, for the fight and pause modes.
# The pause modes open the real PauseMenu over a running fight and save the frame, which is what
# the design-pass compositor's own geometry is checked against - if the compositor and a real
# capture disagree about where the panel's edges are, the compositor is wrong.
# The window stays small; the root viewport renders at 1920x1080 through viewport stretch, so every
# saved frame is 1:1 game pixels.
extends SceneTree

const FIGHT := "res://Scenes/Bosses/EricBossFightScene.tscn"
const MENU := "res://Scenes/Core/MainMenuScene.tscn"
const SCREENS := {
	"victory": "res://Scenes/Core/VictoryScene.tscn",
	"defeat": "res://Scenes/Core/DefeatScene.tscn",
}
# Frames after the fight starts at which a still is saved.
const FIGHT_SHOTS := [30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 360]
# Far enough in that the boss has landed and the HUD is settled.
const PAUSE_AT := 245

var frames := 0
var out_dir := ""
var mode := ""


func _initialize() -> void:
	out_dir = OS.get_environment("CAP_OUT")
	mode = OS.get_environment("CAP_MODE")
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_VIEWPORT
	root.content_scale_size = Vector2i(1920, 1080)
	if SCREENS.has(mode):
		change_scene_to_file(SCREENS[mode])
	else:
		var fight: String = OS.get_environment("CAP_SCENE")
		if fight.is_empty():
			fight = FIGHT
		change_scene_to_file(MENU if mode.begins_with("menu") else fight)


func _hide_balloons(n: Node) -> void:
	for c in n.get_children():
		var nm := String(c.name).to_lower()
		if nm.find("balloon") >= 0:
			if c is CanvasItem or c is CanvasLayer:
				c.visible = false
		_hide_balloons(c)


func _save(file_name: String) -> void:
	var img := root.get_texture().get_image()
	img.save_png(out_dir + "/" + file_name)
	print("CAP saved ", file_name, " ", img.get_size())


func _process(_delta: float) -> bool:
	frames += 1
	if mode.begins_with("menu"):
		return _menu()
	if SCREENS.has(mode):
		if frames == 40:
			_save("ref_%s.png" % mode)
			quit()
		return false
	if mode.begins_with("pause"):
		return _pause()
	return _fight()


# The real screen over a real fight, which is the only honest check of the compositor's geometry.
# The pause layer is a child of the arena, and the arena is a child of the fight scene.
func _pause() -> bool:
	if frames == 5:
		var dm = root.get_node_or_null("DialogueManager")
		if dm:
			dm.dialogue_ended.emit(null)
		var input_settings = root.get_node("InputSettings")
		input_settings._set_device(1)
	if frames >= 6:
		_hide_balloons(root)
	if frames == PAUSE_AT:
		var menu := _find(current_scene, "PauseMenu")
		if menu == null:
			print("CAP no PauseMenu in ", current_scene.scene_file_path)
			quit()
			return true
		menu.open()
		if mode == "pause_confirm":
			menu._ask(menu.CONFIRM_QUIT, menu._quit)
	if frames == PAUSE_AT + 4:
		_save("ref_%s.png" % mode)
		quit()
	return false


func _find(n: Node, want: String) -> Node:
	if String(n.name) == want:
		return n
	for c in n.get_children():
		var hit := _find(c, want)
		if hit != null:
			return hit
	return null


func _menu() -> bool:
	if frames == 3:
		var input_settings = root.get_node("InputSettings")
		input_settings._set_device(1)
	if frames == 5 and mode == "menu_pad_slider":
		var menu := current_scene
		menu.volume_slider.value = 0.7
		menu.volume_slider.grab_focus()
	# The menu fades in over 0.5 s.
	if frames == 40:
		_save("ref_%s.png" % mode)
		quit()
	return false


func _fight() -> bool:
	if frames == 5:
		var dm = root.get_node_or_null("DialogueManager")
		if dm:
			dm.dialogue_ended.emit(null)
	if frames >= 6:
		_hide_balloons(root)
	var t := frames - 5
	if FIGHT_SHOTS.has(t):
		_save("fight_%03d.png" % t)
	if t >= FIGHT_SHOTS[-1]:
		quit()
	return false
