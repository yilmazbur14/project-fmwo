extends SceneTree

# Stills of Carter's Messatsu, for review. Needs a real window, so no --headless, and the window has to
# open small and wholly on the primary screen - never --fullscreen or --maximized. 1280x720 is the
# smallest size that keeps a texel a whole number of pixels (two), which the eye check needs:
#   Godot.exe --fixed-fps 60 --position 100,100 --resolution 1280x720 --script res://art_source/carter_fight/shoot_messatsu.gd -- <out dir> [name suffix]
#
# It forces one Messatsu with him on a known spot across the ring from the player and shoots it beat by
# beat. Three shots are pairs of consecutive frames, for the hand-overs that must not jump: his last lit
# frame against the first dark one, the last dark frame against the first lit one (the glow onto his
# drawn eyes), and the last held fire frame against the first spent one. One frame mid-charge is shot
# with his body forced back on, as the control for checking that none of him shows in the dark. Every
# shot prints a META line of where everything was as the frame was drawn, for the checks run on the
# images.

const FIGHT := "res://Scenes/Bosses/CarterBossFightScene.tscn"
const PLAYER_PATH := "Arena/MainPlayer/CharacterBody2D"
const BOSS_PATH := "Arena/CarterAkumaScene/CarterAkumaCharacterBody"
const CARTER_SPOT := Vector2(1500, 700)
const PLAYER_SPOT := Vector2(600, 700)
# How far into their beats the warp, charge and fire shots are taken.
const WARP_SHOT := 0.15
const CHARGE_SHOT := 0.8
const FIRE_SHOT := 0.2
# The dark frames kept for the last-dark shot: this close to the end of the charge.
const LAST_DARK_WINDOW := 0.05
const SHOTS := 11

var out_dir := "."
var suffix := ""
var scene: Node
var boss: Node
var state_machine: Node
var messatsu: Node
var player: Node

var started := false
var frames := 0
var taken := {}
var last_shot_frame := 0
# The latest frame kept for the first half of a pair, and where everything was on it.
var kept_image: Image
var kept_meta := {}
var control_on := false


func _initialize() -> void:
	var arguments := OS.get_cmdline_user_args()
	if arguments.size() > 0:
		out_dir = arguments[0]
	if arguments.size() > 1:
		suffix = arguments[1]
	scene = load(FIGHT).instantiate()
	root.add_child(scene)
	current_scene = scene
	player = scene.get_node(PLAYER_PATH)
	boss = scene.get_node(BOSS_PATH)
	state_machine = boss.get_node("StateManager")
	messatsu = state_machine.get_node("Messatsu")


func _process(_delta: float) -> bool:
	frames += 1
	if not started:
		if frames < 3:
			return false
		_launch()
		return false
	if control_on:
		control_on = false
		boss.show_body(false)
	_watch()
	# A few frames past the last shot, so its save has been drawn.
	return taken.size() >= SHOTS and frames >= last_shot_frame + 3


func _launch() -> void:
	started = true
	state_machine.states["Intro"].process_mode = Node.PROCESS_MODE_DISABLED
	player.is_talking = false
	player.playerHealth = 9999
	player.global_position = PLAYER_SPOT
	messatsu.spot_override = CARTER_SPOT
	# The rotation's third cycle is the Messatsu.
	state_machine.cycles_started = 2
	state_machine.start_cycle()


func _watch() -> void:
	if state_machine.current_state == state_machine.states["Recover"]:
		if taken.has("5_fire"):
			_shoot_pair("6a_last_hold", "6b_spent")
		return
	if state_machine.current_state != messatsu:
		return
	var clock: float = messatsu.beat_clock
	match messatsu.beat:
		messatsu.Beat.CUT:
			_keep()
		messatsu.Beat.VANISH:
			_shoot_pair("0_last_lit", "1a_first_dark")
			_shoot_first_full_dark()
		messatsu.Beat.WARP:
			if clock >= WARP_SHOT:
				_shoot("2_warp")
		messatsu.Beat.CHARGE:
			if clock >= CHARGE_SHOT and not taken.has("3_charge"):
				_shoot("3_charge")
			elif taken.has("3_charge") and not taken.has("3c_control_body_shown"):
				# One frame of him drawn in the dark the way he used to be, under the curtain.
				boss.show_body(true)
				control_on = true
				_shoot("3c_control_body_shown")
			elif clock >= state_machine.messatsu_charge - LAST_DARK_WINDOW:
				_keep()
		messatsu.Beat.TELL:
			_shoot_pair("4a_last_dark", "4b_lights_on")
		messatsu.Beat.STRING:
			if messatsu.fire_clock >= FIRE_SHOT:
				_shoot("5_fire")
		messatsu.Beat.END:
			_keep()


func _keep() -> void:
	RenderingServer.frame_post_draw.connect(func() -> void:
		kept_image = root.get_texture().get_image()
		kept_meta = _meta()
	, CONNECT_ONE_SHOT)


# The first frame drawn with the curtain all the way down, which is only known once it is drawn: the
# curtain's tween steps after this runs.
func _shoot_first_full_dark() -> void:
	if taken.has("1_full_dark"):
		return
	RenderingServer.frame_post_draw.connect(func() -> void:
		if taken.has("1_full_dark") or boss.curtain.modulate.a < 1.0:
			return
		taken["1_full_dark"] = true
		last_shot_frame = frames
		_save(root.get_texture().get_image(), "1_full_dark", _meta())
	, CONNECT_ONE_SHOT)


# The kept frame - the one drawn just before this - and this one.
func _shoot_pair(before_name: String, after_name: String) -> void:
	if taken.has(before_name) or kept_image == null:
		return
	taken[before_name] = true
	_save(kept_image, before_name, kept_meta)
	kept_image = null
	_shoot(after_name)


func _shoot(shot_name: String) -> void:
	if taken.has(shot_name):
		return
	taken[shot_name] = true
	last_shot_frame = frames
	RenderingServer.frame_post_draw.connect(func() -> void:
		_save(root.get_texture().get_image(), shot_name, _meta())
	, CONNECT_ONE_SHOT)


func _save(image: Image, shot_name: String, meta: Dictionary) -> void:
	var path := "%s/carter_messatsu_%s%s.png" % [out_dir, shot_name, suffix]
	image.save_png(path)
	print("saved ", path)
	print("META ", shot_name, " ", JSON.stringify(meta))


func _meta() -> Dictionary:
	var meta := {
		"frame": frames,
		"state": String(state_machine.current_state.name),
		"beat": messatsu.Beat.keys()[messatsu.beat],
		"carter": _xy(boss.global_position),
		"flip": boss.sprite.flip_h,
		"shown": [boss.sprite.visible, boss.aura.visible, boss.mark_glow.visible],
		"body_alpha": [boss.sprite.modulate.a, boss.aura.modulate.a],
		"anim": String(boss.current_anim),
		"anim_frame": boss.sprite.frame,
		"curtain": boss.curtain.modulate.a,
		"player": _xy(player.global_position),
		"player_centre": _xy(player.hurtBox.get_node("CollisionShape2D").global_position),
		"muzzle": _xy(messatsu.aim_origin),
	}
	if is_instance_valid(messatsu.eyes):
		meta.eyes = _xy(messatsu.eyes.global_position)
		meta.eyes_mirror = messatsu.eyes.scale.x
		meta.eyes_alpha = messatsu.eyes.modulate.a
		meta.eyes_shown = messatsu.eyes.visible
	if is_instance_valid(messatsu.ball):
		meta.ball = _xy(messatsu.ball.global_position)
		meta.ball_scale = messatsu.ball.scale.x
		meta.ball_shown = messatsu.ball.visible
	if is_instance_valid(messatsu.aim_line) and messatsu.aim_line.points.size() == 2:
		meta.line = [_xy(messatsu.aim_line.to_global(messatsu.aim_line.points[0])),
			_xy(messatsu.aim_line.to_global(messatsu.aim_line.points[1]))]
		meta.line_shown = messatsu.aim_line.visible
	if is_instance_valid(messatsu.lock_ring):
		meta.lock = _xy(messatsu.lock_ring.global_position)
		meta.lock_scale = messatsu.lock_ring.scale.x
	return meta


func _xy(at: Vector2) -> Array:
	return [at.x, at.y]
