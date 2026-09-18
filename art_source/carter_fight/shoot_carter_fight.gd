extends SceneTree

# Stills of Carter's Raging Demon, for review. Needs a real window, so no --headless:
#   Godot.exe --fixed-fps 60 --script res://art_source/carter_fight/shoot_carter_fight.gd -- <out dir>
#
# It forces one barrage with a known pattern - clones 4 and 8 are feints - bites the first of them by
# hand and parries clone 7, so every shot below lands every run.

const FIGHT := "res://Scenes/Bosses/CarterBossFightScene.tscn"
const PLAYER_PATH := "Arena/MainPlayer/CharacterBody2D"
const BOSS_PATH := "Arena/CarterAkumaScene/CarterAkumaCharacterBody"
# Which clone each dark shot is taken on, and how far into it.
const RED_SHOT := {"clone": 0, "at": 0.30}
const RED_DASH_SHOT := {"clone": 1, "at": 0.55}
const YELLOW_SHOT := {"clone": 3, "at": 0.30}
# The clone after the bitten feint, which nothing can answer.
const PUNISH_SHOT := {"clone": 4, "at": 0.32}
const PARRY_CLONE := 6
# A credited press this far before contact parries: PlayerDefense.parry_window is 0.2 s.
const PARRY_PRESS_LEAD := 0.06
# Which feint to bite on, and how far into it.
const FEINT_CLONE := 3
const FEINT_PRESS_AT := 0.3

# A second argument of "kill" instead lets a clone finish the player off late in the barrage and
# shoots his victory pose: back turned, emblem burning.
var kill_mode := false
var killed := false
var victory_clock := 0.0
var last_clock := 0.0
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
		if argument == "kill":
			kill_mode = true
		else:
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
	last_clock = clock
	clock += delta
	if kill_mode:
		_watch_kill()
		return shots >= 4
	_watch()
	return shots >= 10


func _launch() -> void:
	started = true
	state_machine.states["Intro"].process_mode = Node.PROCESS_MODE_DISABLED
	player.is_talking = false
	player.playerHealth = 9999
	state_machine.start_cycle()
	# A known barrage: clone 1 red as always, feints on 4 and 8, everything else red. The clone after
	# the bitten feint becomes a punish at runtime.
	var pattern: Array[bool] = []
	pattern.resize(state_machine.clone_count)
	pattern.fill(false)
	pattern[FEINT_CLONE] = true
	pattern[FEINT_CLONE + 4] = true
	demon.feints = pattern
	demon.reds_total = state_machine.clone_count - 2
	# Left and right by turns, so every shot frames the clone clear of the spotlight.
	var from: Array[Vector2] = []
	for i in state_machine.clone_count:
		from.append(Vector2.LEFT if i % 2 == 0 else Vector2.RIGHT)
	demon.directions = from


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


# Late in the barrage, so the kill lands where it really would: locked, in the dark, mid-rush.
func _watch_kill() -> void:
	if not killed and state_machine.current_state == demon and demon.beat == demon.Beat.RUSH and demon.clone_index >= 10:
		killed = true
		player.playerHealth = 1
	var victory: State = state_machine.states.get("Victory")
	if not (victory or state_machine.current_state == victory):
		return
	if state_machine.current_state != victory:
		return
	# The whole beat: gone, standing in the middle, the arena going out around the turn, and the
	# emblem alone in the black.
	match victory.beat:
		victory.Beat.REAPPEAR:
			if victory.clock >= 0.12:
				_shoot("11_ko_teleport")
		victory.Beat.TURN:
			if boss.blackout.visible and boss.blackout.modulate.a >= 0.55:
				_shoot("12_ko_fading_out")
		victory.Beat.BURN:
			victory_clock += clock - last_clock
			if victory_clock >= 0.05:
				_shoot("13_ko_ignition")
			if victory_clock >= 1.4:
				_shoot("14_ko_hold_under_outro")


func _watch_rush() -> void:
	var index: int = demon.clone_index
	var at: float = demon.clone_clock
	if index == RED_SHOT.clone and at >= RED_SHOT.at:
		_shoot("3_red_light")
	if index == YELLOW_SHOT.clone and at >= YELLOW_SHOT.at:
		_shoot("4_yellow_light")
	if index == RED_DASH_SHOT.clone and at >= RED_DASH_SHOT.at:
		_shoot("5_red_mid_rush")
	if index == PUNISH_SHOT.clone and at >= PUNISH_SHOT.at:
		_shoot("10_punish_clone")
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
