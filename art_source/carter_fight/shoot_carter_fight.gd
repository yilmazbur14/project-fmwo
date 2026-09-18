extends SceneTree

# Stills of Carter's Raging Demon, for review. Needs a real window, so no --headless:
#   Godot.exe --fixed-fps 60 --script res://art_source/carter_fight/shoot_carter_fight.gd -- <out dir>
#
# It forces one cycle with a known pattern - clones 2 and 4 are feints - and drives a parry on clone
# 3 by hand, so every shot below lands every run.

const FIGHT := "res://Scenes/Bosses/CarterBossFightScene.tscn"
const PLAYER_PATH := "Arena/MainPlayer/CharacterBody2D"
const BOSS_PATH := "Arena/CarterAkumaScene/CarterAkumaCharacterBody"
# Which clone each dark shot is taken on, and how far into it.
const RED_SHOT := {"clone": 0, "at": 0.30}
const RED_DASH_SHOT := {"clone": 2, "at": 0.55}
const YELLOW_SHOT := {"clone": 1, "at": 0.30}
const PARRY_CLONE := 4
# A credited press this far before contact parries: PlayerDefense.parry_window is 0.15 s.
const PARRY_PRESS_LEAD := 0.06
# Which feint to bite on, and how far into it.
const FEINT_CLONE := 3
const FEINT_PRESS_AT := 0.3

var out_dir := "."
var scene: Node
var boss: Node
var state_machine: Node
var demon: Node
var player: Node

var started := false
var frames := 0
var taken := {}
var shots := 0
var parry_pressed := false
var parry_at := -1.0
var feint_pressed := false
var feint_at := -1.0
var clock := 0.0


func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		out_dir = argument
	scene = load(FIGHT).instantiate()
	root.add_child(scene)
	current_scene = scene
	player = scene.get_node(PLAYER_PATH)
	boss = scene.get_node(BOSS_PATH)
	state_machine = boss.get_node("StateManager")
	demon = state_machine.get_node("RagingDemon")


func _process(delta: float) -> bool:
	frames += 1
	if not started:
		if frames < 3:
			return false
		_launch()
		return false
	clock += delta
	_watch()
	return shots >= 9


func _launch() -> void:
	started = true
	state_machine.states["Intro"].process_mode = Node.PROCESS_MODE_DISABLED
	player.is_talking = false
	player.playerHealth = 9999
	state_machine.start_cycle()
	# A known round: clone 1 red as always, then a feint, a red, a feint, a red.
	var pattern: Array[bool] = [false, true, false, true, false]
	var from: Array[Vector2] = [Vector2.LEFT, Vector2.RIGHT, Vector2.LEFT, Vector2.RIGHT,
		Vector2(-0.70710678, 0.70710678)]
	demon.feints = pattern
	demon.directions = from
	demon.reds_total = 3


func _watch() -> void:
	if state_machine.current_state == demon:
		match demon.beat:
			demon.Beat.FLASH:
				if demon.beat_clock >= 0.36:
					_shoot("1_eye_flash")
			demon.Beat.YANK:
				if demon.beat_clock >= 0.12:
					_shoot("2_yank")
			demon.Beat.RUSH:
				_watch_rush()
			demon.Beat.CLEAR:
				if demon.beat_clock >= 0.1:
					_shoot("6_lights_up")
	elif state_machine.is_recovering():
		_shoot("7_punish_window")


func _watch_rush() -> void:
	var index: int = demon.clone_index
	var at: float = demon.clone_clock
	if index == RED_SHOT.clone and at >= RED_SHOT.at:
		_shoot("3_red_light")
	if index == YELLOW_SHOT.clone and at >= YELLOW_SHOT.at:
		_shoot("4_yellow_light")
	if index == RED_DASH_SHOT.clone and at >= RED_DASH_SHOT.at:
		_shoot("5_red_mid_rush")
	# Biting on a feint: a press while the yellow light is up, which is the punish.
	if index == FEINT_CLONE and not feint_pressed and at >= FEINT_PRESS_AT:
		feint_pressed = true
		player.defense.on_guard_raised()
		player.defense.on_block_pressed()
		feint_at = clock
	if feint_at >= 0.0 and clock - feint_at >= 0.05:
		_shoot("9_feint_punish")
	# The parry, driven by hand: the guard goes up and a fresh credited press lands inside the window.
	var contact: float = state_machine.clone_show + state_machine.clone_dash
	if index == PARRY_CLONE and not parry_pressed and at >= contact - PARRY_PRESS_LEAD:
		parry_pressed = true
		player.defense.on_guard_raised()
		player.defense.rearm_parry()
		player.defense.on_block_pressed()
	if parry_at < 0.0 and demon.reds_parried > 0:
		parry_at = clock
	if parry_at >= 0.0 and clock - parry_at >= 0.03:
		_shoot("8_parry_break")


func _shoot(name: String) -> void:
	if taken.has(name):
		return
	taken[name] = true
	shots += 1
	var path := "%s/carter_%s.png" % [out_dir, name]
	RenderingServer.frame_post_draw.connect(func() -> void:
		var image := root.get_texture().get_image()
		image.save_png(path)
		print("saved ", path)
	, CONNECT_ONE_SHOT)
