extends SceneTree

# Stills of the Liam fight's arena at 1920x1080 for the elements-phase approval mock: the real arena,
# crowd, ropes and boss HUD, with the beast (and anything of his) hidden and frozen. Writes ONLY into
# the out dir given after "--" (the scratchpad); it changes nothing in the project.
#   Godot.exe --path <project> --position 100,100 --resolution 1920x1080 --fixed-fps 60 \
#       --script <this file> -- <out dir>
# Shots:
#   arena_hud.png        HUD at full strength, no boss, no player
#   arena_hud_faded.png  the whole boss HUD block at modulate.a 0.30 (the Bixby-perch fade)
#   arena_nohud.png      no HUD at all
#   arena_player.png     HUD at full, player standing at PLAYER_BODY_AT (used to cut the player out)

const FIGHT := "res://Scenes/Bosses/LiamBossFightScene.tscn"
const PLAYER_PATH := "Arena/MainPlayer/CharacterBody2D"
const BOSS_SCENE := "Arena/BixbyBeastScene"
const BOSS_PATH := "Arena/BixbyBeastScene/BixbyBeastCharacterBody"
const PLAYER_BODY_AT := Vector2(960, 858)
const FADE := 0.30

var out_dir := "."
var scene: Node
var player: Node
var boss: Node
var sm: Node
var intro: Node
var frames := 0
var fight_frames := 0


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() > 0:
		out_dir = args[0]
	scene = load(FIGHT).instantiate()
	root.add_child(scene)
	current_scene = scene
	player = scene.get_node(PLAYER_PATH)
	boss = scene.get_node(BOSS_PATH)
	sm = boss.get_node("StateManager")
	intro = sm.get_node_or_null("Intro")


func _hud(alpha: float, shown: bool) -> void:
	var layer: CanvasLayer = boss.get("hud_layer")
	if layer:
		layer.visible = shown
	for key in ["health_bar", "gauge_bar"]:
		var c: CanvasItem = boss.get(key)
		if c:
			c.modulate.a = alpha


func _process(_delta: float) -> bool:
	frames += 1
	if frames > 4000:
		print("TIMEOUT")
		return true
	player.playerHealth = 9999
	if intro and intro.entered and not intro.cut and intro.has_method("skip_to_fight"):
		intro.skip_to_fight()
	var card: Node = scene.get_node_or_null("Arena/VsCard")
	if card and card.has_method("is_playing") and card.is_playing():
		card.skip()
		card.grace_until_msec = 0
	var state_name := String(sm.current_state.name) if sm.current_state else ""
	if state_name == "" or state_name == "Intro":
		return false
	fight_frames += 1
	if fight_frames == 2:
		print("FIGHT STATE ", state_name)
		scene.get_node(BOSS_SCENE).visible = false
		boss.process_mode = Node.PROCESS_MODE_DISABLED
		sm.process_mode = Node.PROCESS_MODE_DISABLED
		player.global_position = PLAYER_BODY_AT
		player.get_node("Sprite2D").visible = false
	if fight_frames == 60:
		_hud(1.0, true)
		_grab(out_dir + "/arena_hud.png")
	if fight_frames == 64:
		_hud(FADE, true)
	if fight_frames == 70:
		_grab(out_dir + "/arena_hud_faded.png")
	if fight_frames == 74:
		_hud(1.0, false)
	if fight_frames == 80:
		_grab(out_dir + "/arena_nohud.png")
	if fight_frames == 84:
		_hud(1.0, true)
		player.get_node("Sprite2D").visible = true
		player.global_position = PLAYER_BODY_AT
	if fight_frames == 100:
		_grab(out_dir + "/arena_player.png")
		print("PLAYER frame ", player.get_node("Sprite2D").frame, " at ", player.global_position)
	return fight_frames > 110


func _grab(path: String) -> void:
	RenderingServer.frame_post_draw.connect(func() -> void:
		root.get_texture().get_image().save_png(path)
		print("SHOT ", path)
	, CONNECT_ONE_SHOT)
