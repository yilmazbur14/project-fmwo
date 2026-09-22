extends SceneTree

# Stills of boss 2 for review. Needs a real window, so no --headless:
#   Godot.exe --fixed-fps 60 --script res://art_source/computah/shoot_computah.gd -- <out dir>
#
# It runs the beam cycle with the player parked out of reach: the tracking aim line, the locked one
# with its yellow ring up, the shot itself, and the vent window it leaves open.

const FIGHT := "res://Scenes/Bosses/ComputahBossFightScene.tscn"
const PLAYER_PATH := "Arena/MainPlayer/CharacterBody2D"
const BOSS_PATH := "Arena/ComputahScene/ComputahCharacterBody"

# Off to one side rather than in a corner: the aim line has to cross the ring to reach them.
const PLAYER_SPOT := Vector2(1600, 780)

var out_dir := "."
var scene: Node
var boss: Node
var machine: Node
var player: Node

var frames := 0
var started := false
var taken := {}
var shots := 0
var fire_frames := 0


func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		out_dir = argument
	scene = load(FIGHT).instantiate()
	root.add_child(scene)
	current_scene = scene
	player = scene.get_node(PLAYER_PATH)
	boss = scene.get_node(BOSS_PATH)
	machine = boss.get_node("StateManager")


func _process(_delta: float) -> bool:
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
		# BEFORE the cycle starts, not on the next frame: the beam faces him at Enter and never
		# again, so a player still on their spawn mark buys a shot of him aiming the wrong way.
		player.global_position = PLAYER_SPOT
		machine.start_cycle()
		return false
	_watch()
	return shots >= 4


func _watch() -> void:
	player.global_position = PLAYER_SPOT
	var beam: Node = machine.states["Beam"]
	match machine.current_state.name:
		"Beam":
			if beam.phase == beam.Phase.TRACK and beam.elapsed > 0.5:
				_shoot("1_beam_track")
			if beam.phase == beam.Phase.LOCKED:
				_shoot("2_beam_locked")
			# beam.elapsed runs from the start of the whole attack, so the shot is timed off the
			# moment the phase changed instead: at 0.15 s the beam is out to full length.
			if beam.phase == beam.Phase.FIRE:
				fire_frames += 1
				if fire_frames > 9:
					_shoot("3_beam_fire")
		"Punish":
			_shoot("4_vent_window")


func _shoot(name: String) -> void:
	if taken.has(name):
		return
	taken[name] = true
	shots += 1
	var path := "%s/computah_%s.png" % [out_dir, name]
	RenderingServer.frame_post_draw.connect(func() -> void:
		var image := root.get_texture().get_image()
		image.save_png(path)
		print("saved ", path)
	, CONNECT_ONE_SHOT)
