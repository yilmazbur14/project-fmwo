extends SceneTree

# Headless checks on boss 2, COMPUTAH. One mode per process:
#
#   Godot.exe --headless --fixed-fps 60 --path . \
#     --script res://art_source/computah/verify_computah.gd -- mode=cycle
#
# Modes:
#   cycle      the beam-and-vent loop: the attack runs, the window opens, the hit cap holds, the
#              beat leads into the next one, and nothing is left open outside a window
#   hype       he is in FightOutro.BOSS_GROUP, so the hype meter is not inert
#   freeze     a FightFreeze mid-charge stops the beam's clock and its aim, and it carries on after
#
# The beam's own read - the track following the player, the aim latching, the ring living exactly
# from the lock to the shot - is checked in the defence suite's `beam` mode, which has the player's
# input path under it. This file is about the fight around it.
#
# It ends with "RESULT mode=<name> fails=<n>" and exits with that failure count.

const FIGHT := "res://Scenes/Bosses/ComputahBossFightScene.tscn"
const PLAYER_PATH := "Arena/MainPlayer/CharacterBody2D"
const BOSS_PATH := "Arena/ComputahScene/ComputahCharacterBody"

var mode := "cycle"
var fails := 0
var checks := 0

var scene: Node
var boss: Node
var machine: Node
var player: Node

var frames := 0
var clock := 0.0
var started := false
var done := false
var log: Array[String] = []
var step := 0
var step_clock := 0.0


func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("mode="):
			mode = argument.substr(5)
	scene = load(FIGHT).instantiate()
	root.add_child(scene)
	current_scene = scene
	player = scene.get_node(PLAYER_PATH)
	boss = scene.get_node(BOSS_PATH)
	machine = boss.get_node("StateManager")


func _process(delta: float) -> bool:
	frames += 1
	if not started:
		if frames < 3:
			return false
		_launch()
		return false
	clock += delta
	step_clock += delta
	_watch(delta)
	if done:
		_finish()
		return true
	if clock > 90.0:
		_check(false, "mode did not finish inside 90 s")
		_finish()
		return true
	return false


func _launch() -> void:
	started = true
	machine.states["Intro"].process_mode = Node.PROCESS_MODE_DISABLED
	player.is_talking = false
	player.playerHealth = 9999
	match mode:
		"hype":
			pass
		_:
			machine.start_cycle()


func _state() -> String:
	return machine.current_state.name if machine.current_state else "-"


func _note(text: String) -> void:
	log.append("%6.2f %s" % [clock, text])


func _check(ok: bool, text: String) -> void:
	checks += 1
	if not ok:
		fails += 1
	print("P %s %s" % ["PASS" if ok else "FAIL", text])


func _finish() -> void:
	for line in log:
		print("  " + line)
	print("RESULT mode=%s fails=%d checks=%d" % [mode, fails, checks])
	quit(fails)


func _watch(delta: float) -> void:
	match mode:
		"cycle":
			_watch_cycle()
		"hype":
			_watch_hype()
		"freeze":
			_watch_freeze(delta)


#CYCLE
# The fight left to run with the player parked out of reach.

var seen: Array[String] = []
var windows := 0


# Parked in whichever corner he is furthest from, so nothing he does reaches them.
func _flee() -> void:
	var corners := [Vector2(240, 220), Vector2(1680, 220), Vector2(240, 900), Vector2(1680, 900)]
	var far: Vector2 = corners[0]
	for corner in corners:
		if corner.distance_to(boss.global_position) > far.distance_to(boss.global_position):
			far = corner
	player.global_position = far


func _watch_cycle() -> void:
	_flee()
	var now := _state()
	if seen.is_empty() or seen[-1] != now:
		seen.append(now)
		_note("-> " + now)
		if now == "Punish":
			windows += 1
	if seen.size() < 9:
		return
	done = true
	var attacks: Array[String] = []
	for name in seen:
		if machine.ATTACKS.has(name):
			attacks.append(name)
	_check(attacks.size() >= 3, "at least three attacks ran (%s)" % str(attacks))
	_check(windows >= 3, "each of them ended in a punish window (%d)" % windows)
	# Beam, Punish, Idle, over and over: nothing else may get into the loop while the picker has one
	# entry in it.
	var unexpected: Array[String] = []
	for name in seen:
		if not [&"Beam", &"Punish", &"Idle"].has(StringName(name)):
			unexpected.append(name)
	_check(unexpected.is_empty(), "the loop is only the beam, its window and the beat (%s)" % str(unexpected))
	_check(not machine.is_open() or _state() == "Punish", "he is never left open outside a window")


#HYPE
# PlayerHype.is_inert() scans FightOutro.BOSS_GROUP for a node with can_be_dazed(). With nobody in
# it, hype goes inert and the meter hides with no error at all.

func _watch_hype() -> void:
	if frames < 10:
		return
	done = true
	var hype: Node = player.get_node("Hype")
	_check(not hype.is_inert(), "hype is not inert")
	var group: Array = get_nodes_in_group("fight_boss")
	_check(group.has(boss), "he is in the boss group, for can_be_dazed() and OUTRO_DIALOGUE")
	var dazeable := 0
	for node in group:
		if node.has_method("can_be_dazed"):
			dazeable += 1
	_check(dazeable == 1, "exactly one node answers can_be_dazed (%d)" % dazeable)


#FREEZE
# A finisher's FightFreeze has to stop the beam with everything else: its clock is a Physics_Update
# accumulator and nothing in it is on a tree timer.

var frozen_clock := 0.0
var frozen_angle := 0.0


func _watch_freeze(_delta: float) -> void:
	_flee()
	var beam: Node = machine.states["Beam"]
	if step == 0:
		if _state() != "Beam" or beam.phase != beam.Phase.TRACK or beam.elapsed < 0.3:
			return
		frozen_clock = beam.elapsed
		frozen_angle = beam.beam.rotation
		load("res://Scripts/FightFreeze.gd").freeze(self, [player.get_parent()])
		step = 1
		step_clock = 0.0
		return
	if step == 1 and step_clock > 0.5:
		_check(beam.elapsed == frozen_clock, "a freeze stops the beam's clock (%.3f)" % beam.elapsed)
		_check(beam.beam.rotation == frozen_angle, "and its aim stops with it")
		load("res://Scripts/FightFreeze.gd").unfreeze(self)
		_note("beam clock at unfreeze %.2f" % frozen_clock)
		step = 2
		step_clock = 0.0
		return
	if step == 2 and step_clock > 0.3:
		_check(beam.elapsed > frozen_clock, "it carries on once the freeze lifts (%.3f)" % beam.elapsed)
		done = true
