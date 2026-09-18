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

# What a barrage costs four kinds of player from full health, which is the whole point of the retune:
# no i-frames between clones means being hit no longer hands you the ones behind it.
# `yellows` forces the tier each profile is worst at: the hardest one for anybody who presses block,
# the all-red teach barrage for the player who never does.
const PROFILES := {
	8: {"name": "parries every red", "parry": 1.0, "bite": 0.0, "turtle": false, "yellows": 6, "cap": 0},
	9: {"name": "parries about half, bites some feints", "parry": 0.55, "bite": 0.3, "turtle": false, "yellows": 6, "cap": 4},
	10: {"name": "turtles behind the guard", "parry": 0.0, "bite": 0.0, "turtle": true, "yellows": 6, "cap": 5},
	11: {"name": "never touches the block button", "parry": 0.0, "bite": 0.0, "turtle": false, "yellows": 0, "cap": -1},
}
var start_health := 0
var acted_clone := -1
var acted := false
var wants_parry := false
var wants_bite := false
var reported := false
var guard_broke := false
var most_lights := 0
var ducked_to := 0.0
var loudest := -INF


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
	_watch_lights()
	match scenario:
		1:
			_watch_pattern()
			_watch_music()
			if cycles_seen >= 1 and state_machine.is_recovering():
				_check_given_back("one cycle")
				_check_music()
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
			# Killed by a clone rather than by setting health to 0, so the real path runs: a hit
			# resolving inside a locked, blacked-out barrage has to reach FightOutro cleanly.
			if _in_rush() and player.playerHealth > 1:
				player.playerHealth = 1
			if player.playerHealth <= 0:
				# Long enough to cover the whole KO beat: the teleport, the turn, the blackout
				# and the ignition come to about a second after they go down.
				_settle(func() -> void:
					_check_released("a clone kills the player mid-barrage", 0)
					_check_victory_pose()
					_restart(4), 120)
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
				_restart(8)
		8, 9, 10, 11:
			_play_barrage()
			# A barrage that killed them never reaches the punish window, so both endings report.
			if state_machine.is_recovering() or player.playerHealth <= 0:
				_report_barrage()
	return done


# A clone lives 0.54 s against a 0.62 s cadence and a feint carries on past the player for longer
# than that, so the only thing keeping its light from being the second one on screen is how fast the
# light itself goes out. Two lights up at once and a press is ambiguous, so this watches every frame
# of every scenario rather than being reasoned about.
func _watch_lights() -> void:
	var lit := 0
	for hazard in get_nodes_in_group(HAZARD_GROUP):
		var light: Node2D = hazard.get("light")
		if light and light.visible and light.modulate.a > 0.01:
			lit += 1
	most_lights = maxi(most_lights, lit)
	_expect(lit <= 1, "two clone lights were up at once")


# The music has to get out of the way in the dark and come all the way back when the lights do. A
# duck that never lifts leaves the rest of the fight quiet for no reason.
func _watch_music() -> void:
	if state_machine.current_state != demon:
		return
	var level: float = boss.music_player.volume_db
	if demon.beat == demon.Beat.RUSH:
		ducked_to = minf(ducked_to, level)
	loudest = maxf(loudest, level)


func _check_music() -> void:
	var base: float = boss.music_base_db
	_expect(ducked_to <= base - 6.0, "the music only ducked to %.1f dB against a %.1f dB base"
		% [ducked_to, base])
	_expect(is_equal_approx(boss.music_player.volume_db, base),
		"the music came back to %.1f dB instead of its %.1f dB base" % [boss.music_player.volume_db, base])
	_expect(loudest <= base + 0.01, "the music went above its base, to %.1f dB" % loudest)
	# It has to be playing past the silence its file opens on, not from the top of it.
	_expect(boss.music_player.playing, "the music isn't playing during the fight")
	_expect(boss.music_player.get_playback_position() >= boss.music_start,
		"the music started at %.2f s, before its %.2f s start point" %
		[boss.music_player.get_playback_position(), boss.music_start])
	notes.append("the music: %s at %.1f dB from %.1f s, ducked to %.1f in the dark, back to %.1f when the lights came up"
		% [boss.music_player.stream.resource_path.get_file(), base, boss.music_start, ducked_to,
			boss.music_player.volume_db])


func _settle(then: Callable, frames := SETTLE_FRAMES) -> void:
	settle_left = frames
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
	# The scenarios that only watch the machinery need the fight to keep running; the ones measuring
	# what a barrage costs have to take it on the six half-hearts the player really has.
	if not PROFILES.has(next):
		player.playerHealth = 9999
	start_health = player.playerHealth
	acted_clone = -1
	reported = false
	guard_broke = false
	ducked_to = INF
	loudest = -INF
	player.defense.guard_broken.connect(func() -> void: guard_broke = true)
	# Skipping the entrance skips the dialogue timer that normally starts his theme, so it is started
	# here instead - otherwise nothing would ever check the music at all.
	boss.start_music()
	state_machine.start_cycle()
	if PROFILES.has(next):
		_force_pattern(PROFILES[next].yellows)
	scenario = next


# A fixed tier for a profile run, in place of whatever his health would have dealt.
func _force_pattern(yellows: int) -> void:
	var count: int = state_machine.clone_count
	var pattern: Array[bool] = []
	pattern.resize(count)
	pattern.fill(false)
	# Spread out, never adjacent and never on clone 1, the same rules the fight itself follows.
	for i in yellows:
		pattern[2 + i * 2] = true
	demon.feints = pattern
	demon.reds_total = count - yellows


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


# One of the four profiles playing the barrage. The guard goes up for a press and comes down after
# the contact it was meant for, so a clone this profile chose not to answer actually lands instead of
# being absorbed for nothing.
func _play_barrage() -> void:
	if state_machine.current_state != demon or demon.beat != demon.Beat.RUSH:
		return
	var profile: Dictionary = PROFILES[scenario]
	var index: int = demon.clone_index
	var at: float = demon.clone_clock
	if index != acted_clone:
		acted_clone = index
		acted = false
		# One decision per clone, from the clone's own number, so a run repeats exactly.
		wants_parry = _fraction(index) < profile.parry
		wants_bite = _fraction(index + 97) < profile.bite
	if profile.turtle:
		if not player.defense.is_guarding() and not player.defense.is_guard_broken:
			player.defense.on_guard_raised()
			player.defense.on_block_pressed()
		return
	var contact: float = state_machine.clone_show + state_machine.clone_dash
	if acted:
		if at > contact:
			player.defense.on_guard_lowered()
		return
	if demon.clone_is_feint:
		if wants_bite and at >= 0.3:
			acted = true
			player.defense.on_guard_raised()
			player.defense.on_block_pressed()
		return
	if wants_parry and at >= contact - player.defense.parry_window + 0.03:
		acted = true
		player.defense.on_guard_raised()
		player.defense.on_block_pressed()


func _report_barrage() -> void:
	if reported:
		return
	reported = true
	var profile: Dictionary = PROFILES[scenario]
	var taken: int = start_health - player.playerHealth
	var survived: bool = player.playerHealth > 0
	notes.append("one barrage, %s: %d of %d half-hearts taken%s | %d reds parried, %d missed, %d feints bitten, %d punishes landed, %.0f stamina left"
		% [profile.name, taken, start_health, "" if survived else " - KILLED", demon.reds_parried,
			demon.reds_missed, demon.feints_parried, demon.punishes_landed, player.defense.stamina])
	if profile.cap >= 0:
		_expect(taken <= profile.cap, "one barrage, %s: %d half-hearts, over the %d it is meant to cost"
			% [profile.name, taken, profile.cap])
		_expect(survived, "one barrage, %s: killed outright from full health" % profile.name)
	if profile.turtle:
		# The case that had to be checked rather than assumed: a guard that breaks mid-barrage, with
		# no i-frames behind it, must not be a death sentence.
		_expect(guard_broke, "the turtle's guard never broke, so the guard-break case wasn't tested")
		notes.append("the guard broke mid-barrage and the player still walked out of it with %d of %d"
			% [player.playerHealth, start_health])
	if scenario >= 11:
		_finish()
	else:
		_restart(scenario + 1)


# Repeatable stand-in for a die roll.
func _fraction(n: int) -> float:
	return absf(fmod(sin(float(n) * 12.9898) * 43758.5453, 1.0))


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
	# Fifteen clones and eight compass points, so repeats are forced; what must never happen is two
	# in a row from the same side.
	_expect(demon.directions.size() == state_machine.clone_count,
		"cycle %d: %d directions for %d clones" % [round_number, demon.directions.size(), state_machine.clone_count])
	for i in range(demon.directions.size() - 1):
		_expect(demon.directions[i] != demon.directions[i + 1],
			"cycle %d: clones %d and %d both come from %s" % [round_number, i + 1, i + 2, demon.directions[i]])
	_expect(absf(demon.directions[0].y) < 0.001, "cycle %d: clone 1 comes from %s, not the left or the right"
		% [round_number, demon.directions[0]])
	notes.append("cycle %d at %d%% health: %d of %d are feints, pattern %s"
		% [round_number, roundi(boss.get_health_ratio() * 100.0), yellows, feints.size(), str(feints)])


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
	# The barrage's own darkness has to be gone however the fight ended. The KO's blackout is a
	# different thing on the same stage and is allowed to be up - that beat IS his victory pose - so
	# what is checked is that nothing is dark without something deliberately drawing it.
	var dark: Node2D = scene.get_node(DARK_PATH)
	_expect(dark.get_node("Curtain").modulate.a == 0.0, "%s: the barrage's darkness is still up" % label)
	_expect(not dark.visible or boss.blackout.visible,
		"%s: the arena is dark with nothing drawing it" % label)
	_expect(get_nodes_in_group(HAZARD_GROUP).is_empty(), "%s: %d clones left live"
		% [label, get_nodes_in_group(HAZARD_GROUP).size()])
	notes.append("%s: released" % label)
	if next > 0:
		_restart(next)


# He turns his back and the emblem burns, and the bell lands on the frame it lights. The settle is
# 40 frames, well past the 370 ms ignition, so by now all of it should have happened.
func _check_victory_pose() -> void:
	var victory: State = state_machine.states.get("Victory")
	_expect(victory != null, "the victory pose: there is no Victory state")
	_expect(state_machine.current_state == victory, "the victory pose: he is in %s instead"
		% state_machine.current_state.name)
	_expect(victory.ignited, "the victory pose: the mark never ignited")
	_expect(boss.mark_glow.visible, "the victory pose: the emblem isn't burning")
	_expect(boss.current_anim == &"victory_hold", "the victory pose: he is playing %s, not the burn loop"
		% boss.current_anim)
	_expect(boss.ko_sfx_player.stream != null, "the victory pose: no KO sound was loaded")
	# The track bows out under the bell rather than fighting it.
	_expect(boss.music_player.volume_db < boss.music_base_db - 6.0 or not boss.music_player.playing,
		"the victory pose: the music is still at %.1f dB over the bell" % boss.music_player.volume_db)
	# The arena is all the way out and the emblem is the only thing above it.
	_expect(boss.global_position == state_machine.ARENA_CENTRE,
		"the victory pose: he is at %s, not the middle of the ring" % boss.global_position)
	_expect(boss.blackout.visible and is_equal_approx(boss.blackout.modulate.a, 1.0),
		"the victory pose: the arena isn't fully black (alpha %.2f)" % boss.blackout.modulate.a)
	_expect(boss.mark_glow.z_index > boss.blackout.z_index + boss.dark_stage.z_index,
		"the victory pose: the emblem is under the blackout, so nothing is visible")
	_expect(not boss.sprite.visible or boss.sprite.z_index < boss.blackout.z_index + boss.dark_stage.z_index,
		"the victory pose: his body is drawn over the blackout instead of vanishing into it")
	notes.append("the victory pose: centre of the ring, arena fully black, emblem alone at z %d over a z %d blackout, burning on '%s', bell from %s"
		% [boss.mark_glow.z_index, boss.blackout.z_index + boss.dark_stage.z_index, boss.current_anim,
			boss.ko_sfx_player.stream.resource_path.get_file()])


func _expect(ok: bool, message: String) -> void:
	if not ok:
		failures.append(message)


func _finish() -> void:
	done = true
	notes.append("most clone lights on screen at once, across every scenario: %d" % most_lights)
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
