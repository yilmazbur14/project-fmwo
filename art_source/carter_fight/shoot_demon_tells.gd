extends SceneTree

# One Raging Demon barrage dealt through every direction a clone can come from, each clone shot as its
# light holds, for review of where the clones and their tells sit against the HUD. Needs a real window,
# so no --headless, and the window has to open small and wholly on the primary screen - never
# --fullscreen or --maximized. 640x360 is a third of the view, one texel of the art to a pixel:
#   Godot.exe --fixed-fps 60 --position 100,100 --resolution 640x360 --script res://art_source/carter_fight/shoot_demon_tells.gd -- <out dir>
#
# The directions go round CarterRagingDemon.COMPASS in order and clones 4, 8 and 12 are fakes, so the
# first seven shots are one of each direction with a fake among them. Nobody presses anything.

const FIGHT := "res://Scenes/Bosses/CarterBossFightScene.tscn"
const PLAYER_PATH := "Arena/MainPlayer/CharacterBody2D"
const BOSS_PATH := "Arena/CarterAkumaScene/CarterAkumaCharacterBody"
const FAKES := [3, 7, 11]
# How far into its read each clone is shot: its light is on the hold frame by then.
const SHOT_AT := 0.25

var out_dir := "."
var scene: Node
var boss: Node
var sm: Node
var demon: Node
var player: Node

var started := false
var frames := 0
var shot := -1


func _initialize() -> void:
	var arguments := OS.get_cmdline_user_args()
	if arguments.size() > 0:
		out_dir = arguments[0]
	scene = load(FIGHT).instantiate()
	root.add_child(scene)
	current_scene = scene
	player = scene.get_node(PLAYER_PATH)
	boss = scene.get_node(BOSS_PATH)
	sm = boss.get_node("StateManager")
	demon = sm.get_node("RagingDemon")


func _process(_delta: float) -> bool:
	frames += 1
	if not started:
		if frames < 3:
			return false
		_launch()
		return false
	if sm.current_state != demon:
		return shot >= 0
	if demon.beat == demon.Beat.RUSH and demon.clone_index > shot and demon.clone_clock >= SHOT_AT:
		shot = demon.clone_index
		var kind := "fake" if demon.clone_is_feint else "red"
		var path := "%s/demon_tell_%02d_%s.png" % [out_dir, shot + 1, kind]
		RenderingServer.frame_post_draw.connect(func() -> void:
			root.get_texture().get_image().save_png(path)
		, CONNECT_ONE_SHOT)
		print("SHOT %s from %s, feet at %s" % [path, demon.directions[shot], demon.clone.global_position])
	return false


func _launch() -> void:
	started = true
	sm.states["Intro"].process_mode = Node.PROCESS_MODE_DISABLED
	player.is_talking = false
	player.playerHealth = 9999
	sm.cycles_started = 0
	sm.start_cycle()
	var dealt: Array[Vector2] = []
	var fakes: Array[bool] = []
	for i in sm.clone_count:
		dealt.append(demon.COMPASS[i % demon.COMPASS.size()])
		fakes.append(i in FAKES)
	demon.directions = dealt
	demon.feints = fakes
	demon.reds_total = sm.clone_count - FAKES.size()
