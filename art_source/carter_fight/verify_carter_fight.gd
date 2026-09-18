extends SceneTree

# Headless checks for Carter's Raging Demon. Run with:
#   Godot.exe --headless --fixed-fps 60 --script res://art_source/carter_fight/verify_carter_fight.gd
#
# 1  one cycle: the pattern rules, the clone count, and that the sequence gives back everything it
#    took - the lock, the player's draw order, the dark and the music level.
# 2  ten cycles: the pattern rules every round, and that the per-clone hit sources get pruned.
# 3  the player dies mid-rush.
# 4  the boss dies mid-rush.
# 5  the fight scene is freed mid-rush, so _exit_tree() is the only thing left to free the player.
# 6  one more clean cycle after all of that.
# 7  the heart of the fight: mash block through one clone, then parry the next. The presses that
#    whiff on clone 2 would lock the guard out of clone 3 for PlayerDefense.parry_mash_lockout, and
#    the rearm_parry() the fight makes as each light comes up is the only thing that stops it.
#
# The pre-fight dialogue is skipped by disabling the Intro state, which stops the node-bound tweens
# its entrance is waiting on, so no balloon is ever shown.

const FIGHT := "res://Scenes/Bosses/CarterBossFightScene.tscn"
const PLAYER_PATH := "Arena/MainPlayer/CharacterBody2D"
const BOSS_PATH := "Arena/CarterAkumaScene/CarterAkumaCharacterBody"
const DARK_PATH := "Arena/CarterAkumaScene/DarkStage"
const HAZARD_GROUP := "carter_hazard"
const SETTLE_FRAMES := 40
# Clone 2 is mashed at, clone 3 is parried; a credited press this far before contact is inside
# PlayerDefense.parry_window.
const MASH_CLONE := 1
const PARRY_CLONE := 2
const PARRY_PRESS_LEAD := 0.02

var scene: Node
var boss: Node
var state_machine: Node
var demon: Node
var player: Node

var scenario := 0
var settle_left := 0
var after_settle := Callable()
var cycles_seen := 0
var last_beat := -1
var last_clone := -1
var clones_this_cycle := 0
var failures: Array[String] = []
var notes: Array[String] = []
var done := false

var mashes := 0
var mash_clock := 0.0
var parry_pressed := false
var parried := false


func _initialize() -> void:
	_build(1)


func _process(_delta: float) -> bool:
	if done:
		return true
	if settle_left > 0:
		settle_left -= 1
		if settle_left == 0 and after_settle.is_valid():
			var next := after_settle
			after_settle = Callable()
			next.call()
		return done
	match scenario:
		1:
			_watch_pattern()
			if cycles_seen >= 1 and state_machine.is_recovering():
				_check_given_back("one cycle")
				_restart(2)
		2:
			_watch_pattern()
			if cycles_seen >= 10 and state_machine.is_recovering():
				var sources: int = player.defense.sources.size()
				_expect(sources <= player.defense.MAX_SOURCES, "ten cycles: defense.sources is %d, over the %d cap"
					% [sources, player.defense.MAX_SOURCES])
				notes.append("ten cycles: defense.sources settled at %d of %d" % [sources, player.defense.MAX_SOURCES])
				_restart(3)
		3:
			if _in_rush():
				player.playerHealth = 0
				_settle(func() -> void: _check_released("the player dies mid-rush", 4))
		4:
			if _in_rush():
				boss.boss_health = 1
				boss._apply_damage(1)
				_settle(func() -> void: _check_released("the boss dies mid-rush", 5))
		5:
			if _in_rush():
				# The player node goes with the scene, so the release is caught as it happens rather
				# than read off a node that no longer exists.
				var freed := {"unlocked": false}
				player.actions_unlocked.connect(func() -> void: freed.unlocked = true, CONNECT_ONE_SHOT)
				_expect(player.is_action_locked, "the scene is freed mid-rush: the player wasn't locked to start with")
				_drop_outro()
				scene.free()
				_expect(freed.unlocked, "the scene is freed mid-rush: the player was never unlocked")
				notes.append("the scene is freed mid-rush: released by _exit_tree()")
				_build(6)
		6:
			_watch_pattern()
			if cycles_seen >= 1 and state_machine.is_recovering():
				_check_given_back("one more cycle after every interruption")
				_restart(7)
		7:
			_watch_mash()
			if state_machine.is_recovering():
				_expect(mashes > 0, "mash then parry: the mashed presses never went in")
				_expect(parried, "mash then parry: clone %d was not parried after %d whiffed presses on clone %d"
					% [PARRY_CLONE + 1, mashes, MASH_CLONE + 1])
				notes.append("mash then parry: %d whiffed presses on clone %d, clone %d still parried"
					% [mashes, MASH_CLONE + 1, PARRY_CLONE + 1])
				_finish()
	return done


func _settle(then: Callable) -> void:
	settle_left = SETTLE_FRAMES
	after_settle = then


func _restart(next: int) -> void:
	_drop_outro()
	if scene and is_instance_valid(scene):
		scene.free()
	_build(next)


# A fight decided by one scenario must not have its outro still standing for the next; and the HUD
# reads get_tree().current_scene every frame, so it is never left null between scenes.
func _drop_outro() -> void:
	var outro := root.get_node_or_null(^"FightOutro")
	if outro:
		outro.free()


func _build(next: int) -> void:
	scenario = 0
	cycles_seen = 0
	last_beat = -1
	last_clone = -1
	clones_this_cycle = 0
	scene = load(FIGHT).instantiate()
	root.add_child(scene)
	current_scene = scene
	player = scene.get_node(PLAYER_PATH)
	boss = scene.get_node(BOSS_PATH)
	state_machine = boss.get_node("StateManager")
	demon = state_machine.get_node("RagingDemon")
	# The state machine fills its own states dictionary and defers the entrance, so the cycle is
	# forced a frame later rather than in the middle of the scene coming up.
	_settle(func() -> void: _launch(next))


func _launch(next: int) -> void:
	# No balloon: the entrance is waiting on node-bound tweens, which a disabled node stops.
	state_machine.states["Intro"].process_mode = Node.PROCESS_MODE_DISABLED
	player.is_talking = false
	# Every clone that isn't parried lands, so six half-hearts wouldn't survive one round. The
	# scenarios that need the fight to keep running take the damage without dying of it.
	player.playerHealth = 9999
	state_machine.start_cycle()
	scenario = next


func _in_rush() -> bool:
	return (state_machine.current_state == demon and demon.beat == demon.Beat.RUSH
		and demon.clone_index >= 2)


# Counts the clones a round actually spawns, and checks the pattern it was dealt.
func _watch_pattern() -> void:
	if state_machine.current_state != demon:
		last_beat = -1
		return
	if demon.beat == demon.Beat.RUSH and last_beat != demon.beat:
		_check_pattern()
		clones_this_cycle = 0
		last_clone = -1
	last_beat = demon.beat
	if demon.beat == demon.Beat.RUSH and demon.clone_index != last_clone:
		last_clone = demon.clone_index
		clones_this_cycle += 1
		if demon.clone_index == demon.feints.size() - 1:
			_expect(clones_this_cycle == state_machine.clone_count, "cycle %d: %d clones, expected %d"
				% [cycles_seen + 1, clones_this_cycle, state_machine.clone_count])
			cycles_seen += 1


# Block mashed through one clone, then one honest press on the next. Nothing here calls
# rearm_parry(): the only re-arm is the one the fight itself makes as each light comes up, which is
# exactly what is being tested.
func _watch_mash() -> void:
	if state_machine.current_state != demon or demon.beat != demon.Beat.RUSH:
		return
	var index: int = demon.clone_index
	var at: float = demon.clone_clock
	# The whole of clone 2, its dark gap included, so the last whiffed press is as close to the next
	# clone's light as a player could physically get it.
	if index == MASH_CLONE:
		player.defense.on_guard_raised()
		mash_clock += 1.0 / 60.0
		if mash_clock >= 0.06:
			mash_clock = 0.0
			mashes += 1
			player.defense.on_block_pressed()
	# And the press on clone 3 goes in at the very start of its window rather than the easy end of it.
	var contact: float = state_machine.clone_show + state_machine.clone_dash
	if index == PARRY_CLONE and not parry_pressed and at >= contact - player.defense.parry_window + PARRY_PRESS_LEAD:
		parry_pressed = true
		player.defense.on_block_pressed()
	if demon.reds_parried > 0:
		parried = true


func _check_pattern() -> void:
	var round_number: int = state_machine.cycles_started
	var feints: Array = demon.feints
	var yellows: int = feints.count(true)
	_expect(feints.size() == state_machine.clone_count, "cycle %d: pattern is %d long, expected %d"
		% [round_number, feints.size(), state_machine.clone_count])
	_expect(yellows == state_machine.cycle_yellows, "cycle %d: %d feints, expected %d"
		% [round_number, yellows, state_machine.cycle_yellows])
	_expect(not feints[0], "cycle %d: clone 1 is a feint" % round_number)
	if state_machine.cycle_yellows <= 2:
		for i in range(feints.size() - 1):
			_expect(not (feints[i] and feints[i + 1]), "cycle %d: feints %d and %d are adjacent at %d yellows"
				% [round_number, i, i + 1, yellows])
	var seen := {}
	for direction in demon.directions:
		_expect(not seen.has(direction), "cycle %d: direction %s dealt twice" % [round_number, direction])
		seen[direction] = true
	_expect(absf(demon.directions[0].y) < 0.001, "cycle %d: clone 1 comes from %s, not the left or the right"
		% [round_number, demon.directions[0]])
	notes.append("cycle %d at %d%% health: %d yellows, pattern %s, from %s"
		% [round_number, roundi(boss.get_health_ratio() * 100.0), yellows, str(feints), str(demon.directions)])


# Everything the sequence took has to be back by the time the punish window opens.
func _check_given_back(label: String) -> void:
	_expect(not player.is_action_locked, "%s: the player is still locked" % label)
	_expect(player.get_parent().z_index == 0, "%s: the player's stage is still at z %d"
		% [label, player.get_parent().z_index])
	_expect(not scene.get_node(DARK_PATH).visible, "%s: the arena is still dark" % label)
	_expect(is_equal_approx(boss.music_player.volume_db, boss.music_base_db),
		"%s: the music is still ducked (%.1f dB)" % [label, boss.music_player.volume_db])
	_expect(get_nodes_in_group(HAZARD_GROUP).is_empty(), "%s: %d clones left live"
		% [label, get_nodes_in_group(HAZARD_GROUP).size()])
	notes.append("%s: lock, draw order, dark, music and clones all given back" % label)


func _check_released(label: String, next: int) -> void:
	_expect(not player.is_action_locked, "%s: the player is still locked" % label)
	_expect(player.get_parent().z_index == 0, "%s: the player's stage is still at z %d"
		% [label, player.get_parent().z_index])
	_expect(not scene.get_node(DARK_PATH).visible, "%s: the arena is still dark" % label)
	_expect(get_nodes_in_group(HAZARD_GROUP).is_empty(), "%s: %d clones left live"
		% [label, get_nodes_in_group(HAZARD_GROUP).size()])
	notes.append("%s: released" % label)
	_restart(next)


func _expect(ok: bool, message: String) -> void:
	if not ok:
		failures.append(message)


func _finish() -> void:
	done = true
	print("")
	for note in notes:
		print("  ", note)
	print("")
	if failures.is_empty():
		print("carter fight: all checks passed")
	else:
		for failure in failures:
			printerr("FAIL  ", failure)
		print("carter fight: %d FAILED" % failures.size())
	quit(0 if failures.is_empty() else 1)
