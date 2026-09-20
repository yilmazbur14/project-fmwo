extends SceneTree

# Windowed capture of the player's punch in Eric's fight, for GIFs and mockups. Eric's fight as it
# ships: feel_v2 on, the v2 hitbox fitted by the game and PunchFx on the player. mode=today switches
# feel_v2 off for a before/after. Eric is held down so his hurtbox is live; every frame of each swing
# is saved as a WxH crop centred between the player and where the punch goes (crops.txt says where).
#   Godot.exe --path . --resolution 1920x1080 --fixed-fps 60 --script res://art_source/punch_fx/probe_punch_capture.gd -- out=<dir> [mode=today] [crop=640x360]
# Needs a window: headless runs don't render.

const SCENE := "res://Scenes/Bosses/EricBossFightScene.tscn"
const BINDINGS := "user://input_bindings_punch_fx_probe.cfg"
const FACING_NAMES := ["down", "up", "left", "right"]
const FACING_VECTORS := [Vector2.DOWN, Vector2.UP, Vector2.LEFT, Vector2.RIGHT]
const FRAMES := 42
# Where his hurtbox's near face is put, in px past today's far edge (as verify_defense's punch_reach).
const SPOTS := {"hit": -6.0, "whiff": 40.0, "reach": 3.0}

var out_dir := ""
var v2 := true
var crop := Vector2i(640, 360)
var kinds: Array = ["hit", "whiff"]
var player: CharacterBody2D
var boss: Node
var sm: Node
var log_lines: PackedStringArray = []


func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("out="):
			out_dir = arg.substr(4)
		elif arg == "mode=today":
			v2 = false
		elif arg.begins_with("crop="):
			var wh := arg.substr(5).split("x")
			crop = Vector2i(int(wh[0]), int(wh[1]))
		elif arg == "reach=1":
			kinds.append("reach")
	DirAccess.make_dir_recursive_absolute(out_dir)
	_main.call_deferred()


func wait(n: int) -> void:
	for i in n:
		await physics_frame


func punch() -> void:
	for pressed in [true, false]:
		var ev := InputEventAction.new()
		ev.action = &"punch"
		ev.pressed = pressed
		Input.parse_input_event(ev)


func _main() -> void:
	var settings: Node = root.get_node("InputSettings")
	settings.save_path = BINDINGS
	settings.reset_to_defaults()
	change_scene_to_file(SCENE)
	while current_scene == null or current_scene.scene_file_path != SCENE:
		await process_frame
	await wait(3)
	player = current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
	for child in current_scene.get_children():
		if child is CanvasLayer:
			child.queue_free()
	root.get_node("DialogueManager").dialogue_ended.emit(null)
	await wait(2)
	current_scene.get_node("Arena/MainPlayer/CanvasLayer").visible = false
	boss = current_scene.get_node("Arena/EricBossScene/CharacterBody2D")
	sm = boss.state_machine
	sm.post_dialogue_pre_fight_timer.stop()
	sm.chain = []
	sm.on_child_transition(sm.current_state, "Idle")
	sm.set_process(false)
	sm.set_physics_process(false)
	for timer in boss.find_children("*", "Timer", true, false):
		timer.stop()
	player.playerHealth = 100
	boss.boss_health = 1000
	sm.downed_state_timer.start(600.0)
	sm.on_child_transition(sm.current_state, "Downed")
	await wait(40)
	boss.daze_used = true
	player.feel_v2 = v2

	var hurtbox: Area2D = boss.get_node("Hurtbox")
	var shape: CollisionShape2D = hurtbox.get_node("CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	log_lines.append("hurtbox %f %f %f %f" % [box.position.x, box.position.y, box.size.x, box.size.y])
	for f in [1, 0, 2, 3]:
		for kind in kinds:
			await run_case(f, kind, box)
	var file := FileAccess.open(out_dir + "/crops.txt", FileAccess.WRITE)
	file.store_string("\n".join(log_lines) + "\n")
	file.close()
	DirAccess.remove_absolute(ProjectSettings.globalize_path(BINDINGS))
	quit(0)


# Where the player stands so `facing` points at `box` with today's far edge `past` px short of its near
# face (negative: inside it).
func stand_point(facing: int, past: float, box: Rect2) -> Vector2:
	var r: Rect2 = player.PUNCH_HITBOXES[facing]
	var px := Rect2(r.position * 2.0, r.size * 2.0)
	match facing:
		1:
			return Vector2(box.get_center().x - px.get_center().x, box.end.y + past - px.position.y)
		0:
			return Vector2(box.get_center().x - px.get_center().x, box.position.y - past - px.end.y)
		2:
			return Vector2(box.end.x + past - px.position.x, box.get_center().y + 30.0 - px.get_center().y)
		_:
			return Vector2(box.position.x - past - px.end.x, box.get_center().y + 30.0 - px.get_center().y)


func run_case(facing: int, kind: String, box: Rect2) -> void:
	var at := stand_point(facing, SPOTS[kind], box).round()
	player.global_position = at
	player.velocity = Vector2.ZERO
	await wait(10)
	player.global_position = at
	await wait(6)
	var tag := "%s_%s" % [FACING_NAMES[facing], kind]
	# Centred a little toward where the punch goes, kept on screen.
	var centre := Vector2i(at + FACING_VECTORS[facing] * 40.0)
	var screen := Vector2i(root.get_texture().get_image().get_size())
	var origin := (centre - crop / 2).clamp(Vector2i.ZERO, screen - crop)
	var health: int = boss.boss_health
	punch()
	for i in FRAMES:
		await physics_frame
		await RenderingServer.frame_post_draw
		var img := root.get_texture().get_image()
		img.get_region(Rect2i(origin, crop)).save_png("%s/%s_f%02d.png" % [out_dir, tag, i])
	log_lines.append("%s player %d %d crop %d %d facing %d dealt %d" % [tag, int(at.x), int(at.y), origin.x, origin.y, player.facing, health - boss.boss_health])
	await wait(20)
