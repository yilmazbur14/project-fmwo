extends SceneTree

# Stills and a frame burst of Mason's retuned attacks, for review. Needs a real window, so no
# --headless:
#   Godot.exe --fixed-fps 60 --script res://art_source/mason_tuning/shoot_mason_tuning.gd -- <mode> <out dir>
# Modes: poo (the start ring, a line at full density and the wave rolling out of it, plus a burst of
# frames for a GIF), carter (the call-in's marker and slam), nuggets (the sky at its busiest).
# The player is driven to the start of each line by hand, which is the read the ring is there to sell.

const FIGHT := "res://Scenes/Bosses/MasonBossFightScene.tscn"
const PLAYER_PATH := "Arena/MainPlayer/CharacterBody2D"
const BOSS_PATH := "Arena/MasonScene/MasonCharacterBody"
const PLAYER_SPEED := 600.0
# Far enough out of the ring that the player isn't standing in its bomb's blast.
const STAND_OFF := 150.0
const BURST_EVERY := 3
# The burst frames are the mat only, small enough that the GIF the art scripts write off them keeps
# to the 256 colours it allows.
const BURST_CROP := Rect2i(100, 100, 1720, 880)
const BURST_SIZE := Vector2i(430, 220)

var mode := "poo"
var out_dir := "."
var scene: Node
var boss: Node
var sm: Node
var player: Node

var frames := 0
var clock := 0.0
var started := false
var taken := {}
var burst_frames := 0
var bursting := false
var run_target := Vector2.INF


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() > 0:
		mode = args[0]
	if args.size() > 1:
		out_dir = args[1]
	scene = load(FIGHT).instantiate()
	root.add_child(scene)
	current_scene = scene
	player = scene.get_node(PLAYER_PATH)
	boss = scene.get_node(BOSS_PATH)
	sm = boss.get_node("StateManager")


func _process(delta: float) -> bool:
	frames += 1
	if not started:
		if frames < 4:
			return false
		_launch()
		return false
	clock += delta
	_run_to_ring(delta)
	_watch()
	return clock > 16.0


func _launch() -> void:
	started = true
	player.is_talking = false
	player.playerHealth = 9999
	player.is_invincible = true
	_drop_balloon()
	sm.start_cycle()
	if mode == "carter":
		sm.on_child_transition(sm.current_state, "CallCarter")
	elif mode == "nuggets":
		sm.on_child_transition(sm.current_state, "NuggetShower")


# The intended answer: head for the ring, and stop short of the bomb that sits in it.
func _run_to_ring(delta: float) -> void:
	var ring = sm.line_start
	if is_instance_valid(ring):
		run_target = ring.global_position + Vector2(STAND_OFF if ring.global_position.x < 960 else -STAND_OFF, 0)
	if run_target == Vector2.INF:
		return
	var to: Vector2 = run_target - player.global_position
	var step := PLAYER_SPEED * delta
	player.global_position += Vector2(clampf(to.x, -step, step), clampf(to.y, -step, step))


# The pre-fight balloon covers the bottom of the arena, and these shots are of the fight. It is
# added a frame after the fight scene, so it is looked for until it turns up.
func _drop_balloon() -> void:
	for node in scene.get_children():
		if "Balloon" in node.name:
			node.queue_free()


func _watch() -> void:
	_drop_balloon()
	var bombs := []
	var nuggets := []
	var drops := []
	var blowing := 0
	for node in scene.get_tree().get_nodes_in_group("mason_hazard"):
		if node.has_method("arm"):
			bombs.append(node)
			if node.animation_player.current_animation == "explode":
				blowing += 1
		elif node.has_method("drop"):
			if node.marker.visible:
				nuggets.append(node)
		elif node.has_method("begin"):
			drops.append(node)

	if clock < 0.6:
		return
	match mode:
		"poo":
			if is_instance_valid(sm.line_start) and sm.line_bombs.is_empty():
				_shoot("1_start_ring")
			if bombs.size() >= 14:
				_shoot("2_line_laid")
			if bombs.size() >= 24:
				_shoot("3_mat_covered")
			if blowing >= 3:
				_shoot("4_wave_rolling")
			if clock > 3.0:
				bursting = true
		"carter":
			for drop in drops:
				if drop.target_sprite.visible:
					_shoot("5_elbow_marker")
				if not drop.hitbox_shape.disabled:
					_shoot("6_elbow_slam")
		"nuggets":
			if nuggets.size() >= 8:
				_shoot("7_sky_busy")
			if nuggets.size() >= 11:
				_shoot("8_sky_busiest")
	if bursting and frames % BURST_EVERY == 0 and burst_frames < 120:
		_save("burst_%03d" % burst_frames, true)
		burst_frames += 1


func _shoot(shot: String) -> void:
	if taken.has(shot):
		return
	taken[shot] = true
	_save(shot, false)


func _save(shot: String, small: bool) -> void:
	var path := "%s/mason_%s.png" % [out_dir, shot]
	RenderingServer.frame_post_draw.connect(func() -> void:
		var image := root.get_texture().get_image()
		if small:
			image = image.get_region(BURST_CROP)
			image.resize(BURST_SIZE.x, BURST_SIZE.y, Image.INTERPOLATE_NEAREST)
		image.save_png(path)
	, CONNECT_ONE_SHOT)
