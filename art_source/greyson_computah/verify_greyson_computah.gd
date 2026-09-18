extends SceneTree

# Headless checks on boss 2, GREYSON & COMPUTAH. One mode per process:
#
#   Godot.exe --headless --fixed-fps 60 --path . \
#     --script res://art_source/greyson_computah/verify_greyson_computah.gd -- mode=cycle
#
# Modes:
#   cycle      the A-B-A-B alternation, both punish windows, the hit cap and the beat
#   hype       both bodies are in FightOutro.BOSS_GROUP, so the hype meter is not inert
#   chase      the chase's outcomes: caught, outrun to a battery death, and the parry stagger
#   caught     the five-hit combo: the beats, the damage split, and the lock released every way out
#   clamp      the near-death clamp: it holds at 1 HP, refuses the daze, and lifts at 75%
#   swap       the phase swap: power latched, no healing, telegraph floors, shorter windows
#   junk       phase two with Greyson alone: the three-shot burst and the rig in his hands
#   alone      phase two with Computah alone: the chase never times out, and the double pounce
#   freeze     a finisher on Greyson mid-chase leaves Computah where he was
#
# It ends with "RESULT mode=<name> fails=<n>" and exits with that failure count.

const FIGHT := "res://Scenes/Bosses/GreysonBossFightScene.tscn"
const PLAYER_PATH := "Arena/MainPlayer/CharacterBody2D"
const FIGHT_PATH := "Arena/GreysonComputahScene"

var mode := "cycle"
var fails := 0
var checks := 0

var scene: Node
var fight: Node
var machine: Node
var greyson: Node
var computah: Node
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
	fight = scene.get_node(FIGHT_PATH)
	machine = fight.get_node("StateManager")
	greyson = fight.greyson
	computah = fight.computah


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
		"chase":
			_watch_chase(delta)
		"caught":
			_watch_caught(delta)
		"clamp":
			_watch_clamp()
		"swap":
			_watch_swap()
		"junk":
			_watch_junk()
		"alone":
			_watch_alone()
		"surge":
			_watch_surge()
		"finisher":
			_watch_finisher()
		"win":
			_watch_win()
		"scenechange":
			_watch_scene_change()
		"freeze":
			_watch_freeze()


#CYCLE
# The fight left to run with the player parked out of reach: the alternation and both windows.

var seen: Array[String] = []
var window_bodies: Array[String] = []


# Parked in whichever corner Computah is furthest from, so a chase runs its battery flat instead of
# ending in a catch.
func _flee() -> void:
	var corners := [Vector2(240, 220), Vector2(1680, 220), Vector2(240, 900), Vector2(1680, 900)]
	var far: Vector2 = corners[0]
	for corner in corners:
		if corner.distance_to(computah.global_position) > far.distance_to(computah.global_position):
			far = corner
	player.global_position = far


func _watch_cycle() -> void:
	_flee()
	var now := _state()
	if seen.is_empty() or seen[-1] != now:
		seen.append(now)
		_note("-> " + now)
		if now == "Punish":
			window_bodies.append(machine.states["Punish"].window_body.name)
	if seen.size() < 9:
		return
	done = true
	var attacks: Array[String] = []
	for name in seen:
		if name == "LaserSweep" or name == "Chase":
			attacks.append(name)
	_check(attacks.size() >= 3, "at least three attacks ran (%s)" % str(attacks))
	var alternating := true
	for i in range(1, attacks.size()):
		if attacks[i] == attacks[i - 1]:
			alternating = false
	_check(alternating, "attacks strictly alternate")
	_check(window_bodies.has("Greyson"), "the laser ends in Greyson's window")
	_check(window_bodies.has("Computah"), "the chase ends in Computah's window")
	_check(machine.open_body == null or machine.is_open_to(machine.open_body),
		"no body is left open outside a window")


#HYPE
# Risk 1: PlayerHype.is_inert() scans FightOutro.BOSS_GROUP for a node with can_be_dazed(). If only
# the coordinator were in the group it would silently make hype inert and hide the meter.

func _watch_hype() -> void:
	if frames < 10:
		return
	done = true
	var hype: Node = player.get_node("Hype")
	_check(not hype.is_inert(), "hype is not inert")
	var group: Array = get_nodes_in_group("fight_boss")
	_check(group.has(greyson) and group.has(computah), "both bodies are in the boss group")
	_check(group.has(fight), "the coordinator is in the boss group, for OUTRO_DIALOGUE")
	var dazeable := 0
	for boss in group:
		if boss.has_method("can_be_dazed"):
			dazeable += 1
	_check(dazeable == 2, "exactly the two bodies answer can_be_dazed (%d)" % dazeable)


#CHASE

var chase_phase := ""
var chase_caught := false
var battery_died := false
var stagger_window := 0.0


# The pounce's parry: it sparks him out into the battery window early, and the pounce is the only
# thing in this fight a parry can stagger.
func _watch_chase(_delta: float) -> void:
	var chase: Node = machine.states["Chase"]
	if step == 0:
		if _state() != "Chase":
			return
		if chase_phase == "":
			chase_phase = "chasing"
			_check(not computah.hurtbox.is_in_group("boss_target"),
				"Computah leaves boss_target while he chases, so the player can line up on Greyson")
		# Just inside pounce range, so he commits.
		player.global_position = computah.global_position + Vector2(130, 0)
		if chase.phase == chase.Phase.TELL:
			_note("pounce tell, %.2f s" % chase.tell_left)
			_check(chase.tell_left >= machine.POUNCE_TELL_FLOOR - 0.01,
				"the pounce tell is at or above its floor (%.2f)" % chase.tell_left)
			step = 1
			step_clock = 0.0
		return
	if step == 1:
		# Out of the way, so the lunge is in the air with nothing to grab.
		_flee()
		if chase.phase != chase.Phase.LUNGE:
			return
		_check(machine.can_parry_stagger(computah, null), "a live pounce can be parry-staggered")
		_check(not machine.can_parry_stagger(greyson, null), "nothing of Greyson's can be")
		machine.parry_stagger(computah, 1.2)
		step = 2
		step_clock = 0.0
		return
	if step == 2:
		_flee()
		_check(_state() == "Punish", "a parried pounce ends the chase (%s)" % _state())
		var window: Node = machine.states["Punish"]
		_check(window.window_body == computah, "into Computah's window")
		stagger_window = window.window_time
		_check(stagger_window >= machine.battery_window + machine.parry_stagger_bonus - 0.01,
			"the parried window is at least the battery one plus its bonus (%.2f)" % stagger_window)
		_check(machine.is_open_to(computah), "and he is open in it")
		_check(computah.hurtbox.is_in_group("boss_target"), "and back in boss_target")
		done = true


#CAUGHT

var combo_hits := 0
var health_before := 0
var locked_seen := false


func _watch_caught(_delta: float) -> void:
	var state := _state()
	if step == 0:
		# Stand on him until a pounce lands.
		if state == "Caught":
			health_before = player.playerHealth
			locked_seen = player.is_action_locked
			_note("caught")
			step = 1
			step_clock = 0.0
			return
		if state == "Chase":
			player.global_position = computah.global_position
		return
	if step == 1:
		if state == "Caught":
			combo_hits = machine.states["Caught"].hits_done
			return
		_check(locked_seen, "the catch locked the player")
		_check(combo_hits == 5, "five hits landed (%d)" % combo_hits)
		_check(health_before - player.playerHealth == 3,
			"only the fifth hit deals damage, and it deals 3 (%d)" % (health_before - player.playerHealth))
		_check(not player.is_action_locked, "the lock is released")
		_check(player.is_invincible, "the toss hands back i-frames")
		step = 2
		step_clock = 0.0
		return
	if step == 2:
		# The other exit path: the fight ends mid-combo. Any path leaving the lock on is a hard failure.
		if state == "Caught" and machine.states["Caught"].hits_done >= 2:
			machine.enter_player_defeated()
			_check(not player.is_action_locked, "ending the fight mid-combo releases the player")
			done = true
			return
		if state == "Chase":
			player.global_position = computah.global_position


#CLAMP

func _watch_clamp() -> void:
	if step == 0:
		greyson._apply_damage(greyson.max_health)
		_check(greyson.boss_health == 1, "Greyson clamps at 1 HP while Computah is full (%d)" % greyson.boss_health)
		_check(greyson.on_brink, "he is visibly on the brink")
		_check(not greyson.can_be_dazed(), "a body on the brink cannot be dazed")
		greyson._apply_damage(5)
		_check(greyson.boss_health == 1, "further punches do nothing (%d)" % greyson.boss_health)
		step = 1
		return
	if step == 1:
		# Drop Computah under the guard ratio; the clamp has to lift.
		computah._apply_damage(3)
		_check(computah.get_health_ratio() < fight.SWAP_GUARD_RATIO, "Computah is under the guard ratio")
		_check(not greyson.on_brink, "the clamp lifts")
		greyson._apply_damage(1)
		_check(greyson.boss_health == 0, "Greyson can be killed once it has")
		step = 2
		return
	if step == 2:
		_check(fight.swapped, "the swap fired")
		_check(is_equal_approx(fight.power, computah.get_health_ratio()),
			"power is the survivor's ratio (%.2f)" % fight.power)
		done = true


#SWAP

var swap_health := 0


func _watch_swap() -> void:
	if step == 0:
		# The clamp caps `power` at SWAP_GUARD_RATIO by construction: one of them cannot be killed
		# while the other is above 75%, so the strongest phase two the fight can produce is 0.75.
		greyson._apply_damage(greyson.max_health - floori(greyson.max_health * fight.SWAP_GUARD_RATIO))
		computah._apply_damage(computah.max_health)
		swap_health = greyson.boss_health
		step = 1
		step_clock = 0.0
		return
	if step == 1 and step_clock > 0.1:
		_check(_state() == "Swap", "the kill enters the swap beat (%s)" % _state())
		_check(fight.power >= 0.7, "power latched near the clamp's ceiling (%.2f)" % fight.power)
		_check(fight.surge == 0.0, "the surge resets at the swap, so it never stacks with power")
		step = 2
		step_clock = 0.0
		return
	if step == 2 and step_clock > 2.5:
		_check(greyson.boss_health == swap_health, "nobody healed at the swap")
		_check(greyson.aura.visible, "the survivor's overcharge aura is on")
		var laser: Node = machine.states["LaserSweep"]
		var window: float = machine.laser_window * fight.window_scale()
		_check(window < machine.laser_window, "windows are shorter at high power (%.2f)" % window)
		_check(maxf(machine.laser_telegraph, machine.LASER_TELL_FLOOR) >= machine.LASER_TELL_FLOOR,
			"the laser telegraph never drops under its floor")
		_check(maxf(machine.pounce_tell, machine.POUNCE_TELL_FLOOR) >= machine.POUNCE_TELL_FLOOR,
			"the pounce tell never drops under its floor")
		_check(laser != null, "the laser survives the death of its owner")
		done = true


#PHASE TWO, GREYSON ALONE
# His junk throw became a three-shot burst, and he picks up Computah's rig for the same twin sweep.

var junk_seen := 0
var junk_hits := 0


func _watch_junk() -> void:
	if step == 0:
		greyson._apply_damage(greyson.max_health - floori(greyson.max_health * fight.SWAP_GUARD_RATIO))
		computah._apply_damage(computah.max_health)
		step = 1
		step_clock = 0.0
		return
	if step == 1 and step_clock > 2.5:
		_check(fight.swapped and not fight.is_alive(computah), "Computah is gone")
		step = 2
		step_clock = 0.0
		return
	if step >= 2:
		# In his line, and well clear of where his old partner used to stand.
		player.global_position = Vector2(400, 380)
		junk_seen = maxi(junk_seen, get_nodes_in_group(machine.HAZARD_GROUP).size())
		if _state() == "Chase":
			step = 3
		if step == 3 and _state() == "Punish":
			_check(junk_seen >= 2, "the burst puts more than one piece of junk in the air (%d at once)" % junk_seen)
			_check(machine.states["Punish"].window_body == greyson, "the burst ends in his own window")
			step = 4
			step_clock = 0.0
		# The last piece is still in the air when the window opens, so the damage is read after it.
		if step == 4 and step_clock > 1.5:
			_check(player.playerHealth < 9999, "the burst reaches the player (%d lost)" % (9999 - player.playerHealth))
			done = true
		if _state() == "LaserSweep" and junk_hits == 0:
			junk_hits = 1
			_check(machine.states["LaserSweep"].owner_body == greyson,
				"he picks up the rig himself once Computah is gone")


#PHASE TWO, COMPUTAH ALONE
# Nobody left to change his battery, so the chase no longer times out: it ends when he pounces and
# misses, and the whiff overheats him into a window.

func _watch_alone() -> void:
	var chase: Node = machine.states["Chase"]
	if step == 0:
		computah._apply_damage(computah.max_health - floori(computah.max_health * fight.SWAP_GUARD_RATIO))
		greyson._apply_damage(greyson.max_health)
		step = 1
		step_clock = 0.0
		return
	if step == 1 and step_clock > 2.5:
		_check(fight.swapped and not fight.is_alive(greyson), "Greyson is gone")
		_check(fight.power > machine.double_pounce_power,
			"power is over the double-pounce threshold (%.2f)" % fight.power)
		step = 2
		step_clock = 0.0
		return
	if step == 2:
		if _state() != "Chase":
			_flee()
			return
		_check(chase.chase_length == INF, "his chase no longer times out")
		player.global_position = computah.global_position + Vector2(130, 0)
		if chase.phase == chase.Phase.TELL:
			step = 3
			step_clock = 0.0
		return
	if step == 3:
		_flee()
		if chase.phase == chase.Phase.WHIFF and chase.double_left > 0:
			_note("double pounce owing")
			step = 4
		return
	if step == 4:
		_flee()
		if chase.phase == chase.Phase.TELL:
			_check(chase.tell_left >= machine.POUNCE_TELL_FLOOR - 0.01,
				"the second tell is at or above the floor (%.2f)" % chase.tell_left)
			step = 5
		return
	if step == 5:
		_flee()
		if _state() == "Punish":
			_check(machine.states["Punish"].window_body == computah, "the whiff overheats him into a window")
			_check(machine.is_open_to(computah), "and he is open in it")
			step = 6
			step_clock = 0.0
		return
	if step == 6:
		# A landed pounce with no Greyson to hand the player to: the solo slam.
		if _state() == "Caught":
			_check(machine.states["Caught"].solo, "the catch runs its solo version")
			health_before = player.playerHealth
			step = 7
			step_clock = 0.0
			return
		if _state() == "Chase":
			player.global_position = computah.global_position
		return
	if step == 7:
		if _state() == "Caught":
			return
		_check(health_before - player.playerHealth == 3, "the slam deals 3 (%d)" % (health_before - player.playerHealth))
		_check(not player.is_action_locked, "and gives the player back")
		done = true


#SURGE
# The visible warning while both live: hurt one and only one, and the other goes hot.

var words_seen := 0


func _watch_surge() -> void:
	if step == 0:
		_check(fight.surge == 0.0, "no surge while they are even")
		_check(fight.surging_body() == null, "and nobody is hot")
		greyson._apply_damage(2)
		_check(fight.surge == 0.0, "a 20%% gap is still inside the floor (%.2f)" % fight.surge)
		step = 1
		return
	if step == 1:
		greyson._apply_damage(2)
		_check(fight.surge > 0.0, "a 40%% gap opens the surge (%.2f)" % fight.surge)
		_check(fight.surging_body() == computah, "and it works for the healthier one")
		_check(computah.aura.visible, "his overcharge aura is on")
		_check(not greyson.aura.visible, "the neglected one's is not")
		_check(fight.interval_scale(computah) < 1.0,
			"his intervals tighten (x%.2f)" % fight.interval_scale(computah))
		_check(is_equal_approx(fight.interval_scale(greyson), 1.0), "Greyson's do not")
		_check(maxf(machine.pounce_tell, machine.POUNCE_TELL_FLOOR) == machine.pounce_tell,
			"and no telegraph moves")
		step = 2
		return
	if step == 2:
		greyson._apply_damage(3)
		_check(fight.surge >= 0.5, "a 70%% gap is past the word (%.2f)" % fight.surge)
		_check(fight.surge_word_shown, "OVERCLOCKING fired")
		for child in fight.hud_layer.get_children():
			if child is Label and child.text == fight.SURGE_WORD:
				words_seen += 1
		greyson._apply_damage(0)
		_check(fight.surge_word_shown, "and only once")
		_check(words_seen <= 1, "one popup on screen (%d)" % words_seen)
		# The ghost marker on each bar is the other body's ratio.
		var mark: float = fight.markers[0].position.x
		_check(is_equal_approx(mark, clampf(computah.get_health_ratio() * 400.0 - 1.5, 0.0, 397.0)),
			"Greyson's bar carries Computah's ratio as a tick (%.1f px)" % mark)
		done = true


#THE FINISHER INTERFACE
# The uppercut itself is the defence suite's job; this is the boss half of the contract, on both
# bodies, including one held by the clamp.

func _watch_finisher() -> void:
	if step == 0:
		if _state() != "Punish":
			return
		var body: Node = machine.states["Punish"].window_body
		_check(body.can_be_dazed(), "%s can be dazed in his window" % body.name)
		_check(body.get_finisher_hurtbox() == body.hurtbox, "his finisher hurtbox is his hurtbox")
		_check(body.get_daze_anchor().y < body.global_position.y - 100.0,
			"his daze anchor is over his head")
		body.enter_daze()
		_check(not body.can_be_dazed(), "and only once per window")
		var before: int = body.boss_health
		# Past the hit cap the combo would have used up.
		body.hits_this_window = body.window_cap
		var dealt: int = body.take_finisher(4)
		_check(dealt > 0 and body.boss_health == before - dealt,
			"take_finisher reaches past the hit cap (%d)" % dealt)
		_check(body.end_recovery(1.2), "end_recovery closes the window")
		_check(not machine.is_open_to(body), "and he is shut")
		step = 1
		step_clock = 0.0
		return
	if step == 1 and step_clock > 2.0:
		_check(_state() != "Punish", "the stagger runs into the next attack (%s)" % _state())
		# The clamp has to refuse a finisher that would kill.
		greyson._apply_damage(greyson.max_health)
		computah.boss_health = computah.max_health
		greyson.refresh_brink()
		_check(greyson.on_brink and greyson.take_finisher(9) == 0,
			"a finisher cannot kill a body the clamp is holding")
		done = true


#THE END OF THE FIGHT

func _watch_win() -> void:
	if step == 0:
		greyson._apply_damage(greyson.max_health - floori(greyson.max_health * fight.SWAP_GUARD_RATIO))
		computah._apply_damage(computah.max_health)
		step = 1
		step_clock = 0.0
		return
	if step == 1 and step_clock > 2.5:
		greyson._apply_damage(greyson.max_health)
		step = 2
		step_clock = 0.0
		return
	if step == 2 and step_clock > 0.5:
		_check(fight.both_dead(), "both are down")
		_check(_state() == "Defeated", "the fight enters Defeated (%s)" % _state())
		_check(root.has_node("FightOutro"), "the outro started")
		_check(player.fight_over, "and the player is out of the fight")
		_check(not player.is_action_locked, "with no lock left on them")
		_check(greyson.current_anim == &"defeat" and computah.current_anim == &"defeat",
			"both hold their defeat frame")
		var progress: Node = root.get_node("GameProgress")
		_check(progress.next_boss_scene != null, "the next fight is handed to the Victory screen (%s)"
			% progress.next_boss_scene)
		done = true


#A SCENE CHANGE MID-COMBO
# The worst path out of Caught: the state never gets Exit(), only _exit_tree().

var caught_state: Node


func _watch_scene_change() -> void:
	if step == 0:
		if _state() == "Caught":
			caught_state = machine.states["Caught"]
			_check(not caught_state.released, "the combo is holding the player")
			change_scene_to_file("res://Scenes/Core/MainMenuScene.tscn")
			step = 1
			step_clock = 0.0
			return
		if _state() == "Chase":
			player.global_position = computah.global_position
		return
	if step == 1 and step_clock > 0.5:
		_check(is_instance_valid(caught_state) == false or caught_state.released,
			"the release funnel ran on the way out")
		_check(not is_instance_valid(fight), "the fight scene is gone")
		done = true


#FREEZE

var frozen_at := Vector2.ZERO


func _watch_freeze() -> void:
	if step == 0:
		if _state() != "Chase":
			return
		_flee()
		if machine.open_body == greyson:
			frozen_at = computah.global_position
			var freeze := load("res://Scripts/FightFreeze.gd")
			freeze.freeze(self, [player.get_parent()])
			step = 1
			step_clock = 0.0
		return
	if step == 1 and step_clock > 0.5:
		_check(computah.global_position == frozen_at, "a freeze stops Computah mid-stride")
		var chase: Node = machine.states["Chase"]
		var was: float = chase.clock
		load("res://Scripts/FightFreeze.gd").unfreeze(self)
		_note("chase clock at unfreeze %.2f" % was)
		step = 2
		step_clock = 0.0
		return
	if step == 2 and step_clock > 0.5:
		_check(computah.global_position != frozen_at, "he carries on once it lifts")
		done = true
