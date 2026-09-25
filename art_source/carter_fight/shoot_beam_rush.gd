extends SceneTree

# One whole Beam Rush, for review: stills at its beats and every fourth frame for a GIF. Needs a real
# window, so no --headless, and the window has to open small and wholly on the primary screen - never
# --fullscreen or --maximized. 640x360 is a third of the view, one texel of the art to a pixel:
#   Godot.exe --fixed-fps 60 --position 100,100 --resolution 640x360 --script res://art_source/carter_fight/shoot_beam_rush.gd -- <out dir>
#
# The player is driven through every answer the attack has: they walk out of the first volley's lines,
# parry his strike in the second volley's charge and dash out of its lines, and stay in the third
# volley's lines until the last moment, then dash out through them as they go live. The strike is forced
# into the second charge so every run shoots the same attack. Frames land in <out dir>/beam_rush_gif/,
# stills in <out dir>.

const FIGHT := "res://Scenes/Bosses/CarterBossFightScene.tscn"
const PLAYER_PATH := "Arena/MainPlayer/CharacterBody2D"
const BOSS_PATH := "Arena/CarterAkumaScene/CarterAkumaCharacterBody"
const CARTER_SPOT := Vector2(1500, 560)
const PLAYER_SPOT := Vector2(1250, 820)
const STRIKE_VOLLEY := 1
const STRIKE_AT := 0.3
const GIF_EVERY := 4
# How long the player walks for in the first charge, so the lines have something to follow, and out of
# the first volley's lines once they lock.
const CHARGE_WALK := 0.5
const ESCAPE_WALK := 0.6
# The second volley's escape: a dash, its three moving frames and five still ones, then this much walking.
const DASH_FRAMES := 8
const DASH_WALK := 0.3
# The third: a step out of the crossing after the lock, then the dash, pressed so it starts a frame or
# two before the beams go live.
const DASH_THROUGH_LEAD := 0.10
const DASH_THROUGH_HOLD := 0.5
# A credited press this far before his blow lands parries it: PlayerDefense.parry_window is 0.24 s.
const PARRY_LEAD := 0.1
# Frames kept after he hands over to his window.
const TAIL_FRAMES := 45

var out_dir := "."
var scene: Node
var boss: Node
var sm: Node
var rush: Node
var player: Node

var started := false
var frames := 0
var gif_frames := 0
var taken := {}
var held := {}
var tail := -1
var dashed := {}
var dashed_at := -1.0
var strike_pressed := false


func _initialize() -> void:
	var arguments := OS.get_cmdline_user_args()
	if arguments.size() > 0:
		out_dir = arguments[0]
	DirAccess.make_dir_recursive_absolute(out_dir + "/beam_rush_gif")
	scene = load(FIGHT).instantiate()
	root.add_child(scene)
	current_scene = scene
	player = scene.get_node(PLAYER_PATH)
	boss = scene.get_node(BOSS_PATH)
	sm = boss.get_node("StateManager")
	rush = sm.get_node("BeamRush")


func _process(_delta: float) -> bool:
	frames += 1
	if not started:
		if frames < 3:
			return false
		_launch()
		return false
	if frames % GIF_EVERY == 0:
		_grab("%s/beam_rush_gif/f_%04d.png" % [out_dir, gif_frames])
		gif_frames += 1
	if sm.current_state == rush:
		_drive()
		_watch()
	elif tail < 0:
		tail = TAIL_FRAMES
		_release_all()
		_shoot("9_his_window")
	else:
		tail -= 1
	return tail == 0


func _launch() -> void:
	started = true
	sm.states["Intro"].process_mode = Node.PROCESS_MODE_DISABLED
	player.is_talking = false
	player.playerHealth = 9999
	player.global_position = PLAYER_SPOT
	boss.global_position = CARTER_SPOT
	rush.forced_strike_volley = STRIKE_VOLLEY
	rush.forced_strike_at = STRIKE_AT
	sm.cycles_started = 1
	sm.start_cycle()


func _drive() -> void:
	var locked_for: float = rush.beat_clock if rush.beat == rush.Beat.LOCK else INF
	match rush.volley:
		0:
			var charging: bool = rush.beat == rush.Beat.CHARGE and rush.beat_clock < CHARGE_WALK
			_hold(KEY_LEFT, charging or locked_for < ESCAPE_WALK)
		1:
			_parry_strike()
			if locked_for < INF and not dashed.has(1):
				dashed[1] = true
				_hold(KEY_RIGHT, true)
				_tap(KEY_W)
			if dashed.has(1) and locked_for >= DASH_FRAMES / 60.0 + DASH_WALK:
				_hold(KEY_RIGHT, false)
		2:
			if locked_for < INF:
				_hold(KEY_RIGHT, locked_for < DASH_THROUGH_LEAD)
			var due: bool = rush.beat == rush.Beat.STRING and rush.fire_clock >= sm.messatsu_travel - 3.5 / 60.0
			if due and not dashed.has(2):
				dashed[2] = true
				dashed_at = rush.fire_clock
				_hold(KEY_RIGHT, true)
				_tap(KEY_W)
			if dashed.has(2) and rush.beat == rush.Beat.STRING and rush.fire_clock >= dashed_at + DASH_THROUGH_HOLD:
				_hold(KEY_RIGHT, false)


func _parry_strike() -> void:
	var contact: float = sm.strike_show + sm.strike_dash
	if rush.strike == rush.Strike.SHOW or rush.strike == rush.Strike.LUNGE:
		if not strike_pressed and rush.strike_clock >= contact - PARRY_LEAD:
			strike_pressed = true
			_hold(KEY_SHIFT, true)
	elif strike_pressed:
		_hold(KEY_SHIFT, false)


func _watch() -> void:
	var v: int = rush.volley
	match rush.beat:
		rush.Beat.CHARGE:
			if v == 0 and rush.beat_clock >= 0.8:
				_shoot("1_charge")
			if v == STRIKE_VOLLEY and rush.strike == rush.Strike.SHOW and rush.strike_clock >= 0.2:
				_shoot("5_strike_badge")
		rush.Beat.LOCK:
			if v == 0 and rush.beat_clock >= 0.15:
				_shoot("2_locked")
		rush.Beat.TELL:
			if v == 0 and rush.beat_clock >= 0.1:
				_shoot("3_tell")
		rush.Beat.STRING:
			if v == 0 and rush.fire_clock >= 0.05:
				_shoot("4a_heads_crossing")
			if v == 0 and rush.fire_clock >= 0.4:
				_shoot("4b_beams_crossed")
			if v == 1 and rush.fire_clock >= 0.4:
				_shoot("6_dashed_out")
			if v == 2 and dashed_at >= 0.0 and rush.fire_clock >= dashed_at + 2.0 / 60.0:
				_shoot("7_dashing_through")
		rush.Beat.END:
			if rush.beat_clock >= 0.1:
				_shoot("8_end")


func _hold(code: int, down: bool) -> void:
	if held.get(code, false) == down:
		return
	held[code] = down
	var ev := InputEventKey.new()
	ev.physical_keycode = code
	ev.keycode = code
	ev.pressed = down
	Input.parse_input_event(ev)


func _tap(code: int) -> void:
	_hold(code, true)
	_hold(code, false)


func _release_all() -> void:
	for code in held.keys():
		_hold(code, false)


func _shoot(name: String) -> void:
	if taken.has(name):
		return
	taken[name] = true
	_grab("%s/beam_rush_%s.png" % [out_dir, name])
	print("SHOT %s beat %s volley %d lock %s player %s carter %s" % [name, rush.Beat.keys()[rush.beat], rush.volley, rush.lock_point, player.global_position, boss.global_position])


func _grab(path: String) -> void:
	RenderingServer.frame_post_draw.connect(func() -> void:
		root.get_texture().get_image().save_png(path)
	, CONNECT_ONE_SHOT)
