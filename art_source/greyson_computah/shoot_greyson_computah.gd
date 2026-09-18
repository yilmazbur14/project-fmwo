extends SceneTree

# Stills of boss 2 for review. Needs a real window, so no --headless:
#   Godot.exe --fixed-fps 60 --script res://art_source/greyson_computah/shoot_greyson_computah.gd -- <out dir>
#
# It runs one whole cycle with the player driven by hand: the laser and Greyson's crank window, then
# a chase with the player fleeing so the battery runs flat, then a second chase it lets catch them
# for the five-hit combo, and finally a kill that drives the phase swap.

const FIGHT := "res://Scenes/Bosses/GreysonBossFightScene.tscn"
const PLAYER_PATH := "Arena/MainPlayer/CharacterBody2D"
const FIGHT_PATH := "Arena/GreysonComputahScene"

var out_dir := "."
var scene: Node
var fight: Node
var machine: Node
var greyson: Node
var computah: Node
var player: Node

var frames := 0
var clock := 0.0
var started := false
var taken := {}
var shots := 0
var caught_once := false
var surged := false
var killed := false


func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		out_dir = argument
	scene = load(FIGHT).instantiate()
	root.add_child(scene)
	current_scene = scene
	player = scene.get_node(PLAYER_PATH)
	fight = scene.get_node(FIGHT_PATH)
	machine = fight.get_node("StateManager")
	greyson = fight.greyson
	computah = fight.computah


func _process(delta: float) -> bool:
	frames += 1
	if not started:
		if frames < 3:
			return false
		started = true
		machine.states["Intro"].process_mode = Node.PROCESS_MODE_DISABLED
		# The balloon the fight opens with would sit over every shot.
		for child in scene.get_children():
			if child is CanvasLayer:
				child.queue_free()
		player.is_talking = false
		player.playerHealth = 9999
		machine.start_cycle()
		return false
	clock += delta
	_watch()
	return shots >= 9


func _watch() -> void:
	var state: String = machine.current_state.name
	var chase: Node = machine.states["Chase"]
	match state:
		"LaserSweep":
			_flee()
			var beam: Node = machine.states["LaserSweep"].beam
			if beam.phase == beam.Phase.TELEGRAPH and beam.elapsed > 0.3:
				_shoot("1_laser_telegraph")
			if beam.phase == beam.Phase.SWEEP and beam.elapsed > 1.4:
				_shoot("2_laser_sweep")
		"Chase":
			if not caught_once and chase.clock > 0.6:
				# The first chase runs its battery flat, so the gauge and the charge states show.
				_flee()
				if chase.clock > 1.0:
					_shoot("4_chase")
				if computah.charge_state == 2:
					_shoot("5_battery_low")
			elif caught_once:
				_flee()
		"Punish":
			var body: Node = machine.states["Punish"].window_body
			if body == greyson:
				_shoot("3_greyson_crank_window")
			else:
				_shoot("6_battery_death_window")
				# Once the battery window has been shot, walk into the next pounce.
				caught_once = true
		"Caught":
			var combo: Node = machine.states["Caught"]
			if combo.hits_done >= 3:
				_shoot("7_combo")
		"Swap":
			# Past the hit flash, so the rage pose and the survivor's aura are what is drawn.
			if machine.states["Swap"].clock > 0.9:
				_shoot("9_phase_swap")
	# Stand in the way of the next chase once the battery shot is in the bag.
	if caught_once and state == "Chase" and not taken.has("7_combo"):
		player.global_position = computah.global_position + Vector2(60, 0)
	# Hurt only Greyson, so the surge opens on Computah: his bar goes hot and his aura comes on.
	if taken.has("7_combo") and not surged and state == "Idle":
		surged = true
		greyson._apply_damage(5)
	if surged and not taken.has("8_surge") and state == "LaserSweep":
		_shoot("8_surge")
	# Then kill Greyson, with Computah already under the clamp's guard ratio.
	if taken.has("8_surge") and not killed and state == "Idle":
		killed = true
		computah._apply_damage(computah.max_health - floori(computah.max_health * fight.SWAP_GUARD_RATIO))
		greyson._apply_damage(greyson.max_health)


func _flee() -> void:
	var corners := [Vector2(240, 220), Vector2(1680, 220), Vector2(240, 900), Vector2(1680, 900)]
	var far: Vector2 = corners[0]
	for corner in corners:
		if corner.distance_to(computah.global_position) > far.distance_to(computah.global_position):
			far = corner
	player.global_position = far


func _shoot(name: String) -> void:
	if taken.has(name):
		return
	taken[name] = true
	shots += 1
	var path := "%s/gc_%s.png" % [out_dir, name]
	RenderingServer.frame_post_draw.connect(func() -> void:
		var image := root.get_texture().get_image()
		image.save_png(path)
		print("saved ", path)
	, CONNECT_ONE_SHOT)
