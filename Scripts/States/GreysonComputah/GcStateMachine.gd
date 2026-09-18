extends Node

# The fight-wide machine for boss 2. ONE machine drives BOTH bodies: their attacks are coordinated
# pairs - Computah chases while Greyson throws, a catch hands the player to Greyson - so two machines
# would need constant cross-talk.
#
# THE CYCLE IS STRICT A-B-A-B, AND THAT IS WHAT MAKES THE FIGHT LEARNABLE.
#   A) LASER SWEEP -> a punish window on GREYSON   (he cranks Computah's battery)
#   B) CHASE       -> a punish window on COMPUTAH  (his battery ran flat), or the catch
# A player who takes what each cycle offers trends toward even damage on the two of them, which is
# the whole point: imbalance is something the player does to themselves, not something the fight
# does to them. Extra damage is opt-in - Greyson is also open for a moment after each junk throw -
# and that is the greedy, risky option.
#
# Phase two keeps the same alternation with whoever is left: Computah alone chases and lasers,
# Greyson alone bursts junk and picks up the ruined rig for the same twin sweep.
#
# TELEGRAPHS NEVER SCALE. Intervals, sweeps and movement get faster with the surge and with `power`;
# the pounce tell and the laser telegraph have floors, because below about 0.35 s a read stops being
# a read and becomes a coin flip.
#
# THE PLAYER-API WRAPPERS BELOW ARE THE ONLY PLACE THIS FIGHT TOUCHES THE PLAYER'S LOCK, FACING OR
# PARRY. Each is has_method-guarded with a one-shot push_warning, the way Carter's is. PlayerScript
# and PlayerDefense belong to the defence coder; nothing here edits them.
#
# FREEZE SAFETY: every wait is a Timer node or a Physics_Update accumulator and every ramp is a
# node-bound tween, all of which a finisher's FightFreeze stops with the rest of the fight. Nothing
# here may use get_tree().create_timer() or a tree-level create_tween().

@export var initial_state : State

@export var states : Dictionary = {}
@export var current_state : State
@export var fight : Node2D

#TIMERS
@export var post_dialogue_pre_fight_timer: Timer
@export var window_timer: Timer
@export var finisher_stagger_timer: Timer
@export var beat_timer: Timer

const ParryTell := preload("res://Scripts/ParryTell.gd")
const PRE_FIGHT_DIALOGUE := "res://Dialogue/GreysonAndComputahPreFightDialogue.dialogue"
const HAZARD_GROUP := "greyson_computah_hazard"

# The inside edges of the ropes, as every other fight measures them. Nothing else may hardcode them.
const ROPES := Rect2(113, 114, 1692, 853)
# Where the two of them stand when the fight starts and after each attack.
const COMPUTAH_HOME := Vector2(700, 380)
const GREYSON_HOME := Vector2(1220, 380)

#TUNING (seconds, px and px/s)
# The breath between attacks.
@export var beat_time := 0.6
@export var intro_beat := 2.0

#A) THE LASER SWEEP
# The telegraph is the read and never scales; the sweep is the attack and does.
@export var laser_telegraph := 0.5
@export var laser_sweep := 2.0
@export var laser_sweep_fast := 1.4
@export var laser_fade := 0.2
# Greyson cranking Computah's battery, phase one.
@export var laser_window := 2.6
# Computah alone: nobody to crank him, so he vents instead.
@export var laser_vent_window := 2.0
# Greyson alone, after the overclock beam.
@export var beam_window := 2.2

#B) THE CHASE
# The chase is a rhythm, not a grab blob: touching does nothing, the POUNCE is the grab, and it has
# three counters - outrun it, dash through it, or parry it.
@export var chase_time := 5.0
# A full surge stretches the chase rather than speeding it up past reading.
@export var chase_time_surge := 6.5
@export var chase_accel := 2500.0
# The player walks 600. Outrunnable early, marginally faster late; a dash buys the ground back.
@export var chase_speed_from := 420.0
@export var chase_speed_to := 660.0
@export var pounce_range := 140.0
@export var pounce_tell := 0.45
@export var pounce_cooldown := 1.2
@export var pounce_speed := 1400.0
@export var pounce_reach := 320.0
@export var pounce_stumble := 0.5
# The battery window his flat battery opens, and the longer one a parry buys.
@export var battery_window := 3.2
@export var parry_stagger_bonus := 0.8
# Greyson's junk over the chase, and the moment he is open after each release.
@export var junk_interval := 1.4
@export var junk_tell := 0.4
@export var junk_speed := 850.0
@export var junk_open := 0.9
@export var junk_window_cap := 2

#PHASE TWO
# Greyson alone: the junk throw becomes a burst.
@export var burst_shots := 3
@export var burst_gap := 0.24
@export var burst_window := 1.2
# Computah alone: nobody changes his battery, so the chase no longer times out - it ends only when
# he pounces and misses, and a whiff overheats him into a window. The tell becomes the whole read.
@export var overheat_window := 2.4
# Above this power he pounces twice, the second one with its own tell and its own rearm.
@export var double_pounce_power := 0.5
@export var double_pounce_delay := 0.35
@export var double_pounce_tell := 0.32

# THE READ FLOORS. A telegraph under about 0.35 s is a coin flip rather than a reaction, so nothing
# the surge or `power` does may take either of these below them.
const POUNCE_TELL_FLOOR := 0.32
const LASER_TELL_FLOOR := 0.38

var player_defeated := false
var cycles_started := 0
# Strict alternation: false runs the laser, true runs the chase.
var chase_next := false
# Whichever body is punchable right now, or null. One source, so the rules can't drift.
var open_body: Node = null

var warned := {}


func _ready() -> void:
	for child in get_children():
		if child is State:
			states[child.name] = child

	if initial_state:
		current_state = initial_state
		# Deferred until the bodies are ready, since the intro places and draws them.
		current_state.Enter.call_deferred()
	# On the first frame, the way the fight has always done it, rather than at the end of the intro
	# pose: anything driving the fight from outside (the defence suite) ends the dialogue as soon as
	# the scene loads, and a handler connected a second later would never hear it.
	show_pre_fight_dialogue.call_deferred()


func _process(delta: float) -> void:
	if current_state:
		current_state.Update(delta)


func _physics_process(delta: float) -> void:
	if current_state:
		current_state.Physics_Update(delta)


func on_child_transition(state, new_state_name):
	if state != current_state:
		return

	# Defeat, theirs or the player's, is terminal: a late timer must never restart the fight.
	if current_state == states.get("Defeated") or player_defeated:
		return

	var new_state = states.get(new_state_name)
	if !new_state:
		return

	if current_state:
		current_state.Exit()

	new_state.Enter()
	current_state = new_state


#THE BODIES

func greyson() -> Node:
	return fight.greyson


func computah() -> Node:
	return fight.computah


# Computah's rig: his while he is alive, and Greyson hauls it up when he isn't.
func laser_owner() -> Node:
	return computah() if fight.is_alive(computah()) else greyson()


# How hard this body is pushing: the surge while both live, `power` once one of them is gone. They
# never stack - the surge resets at the swap.
func pace(body: Node) -> float:
	if fight.swapped:
		return fight.power
	return fight.surge if body == fight.surging_body() else 0.0


#THE CYCLE

# Their lines call no beats, so the intro hands the dialogue over and waits for it to end.
func show_pre_fight_dialogue() -> void:
	# One-shot: the outro's lines end a dialogue too, and must not start the fight again.
	DialogueManager.dialogue_ended.connect(_on_dialogue_ended, CONNECT_ONE_SHOT)
	DialogueManager.show_dialogue_balloon(load(PRE_FIGHT_DIALOGUE), "start")


func _on_dialogue_ended(_dialogue: Object) -> void:
	post_dialogue_pre_fight_timer.start(intro_beat)


func _on_post_dialogue_pre_fight_timer_timeout() -> void:
	fight.start_music()
	start_cycle()


func start_cycle() -> void:
	cycles_started += 1
	var attack := "Chase" if chase_next else "LaserSweep"
	chase_next = not chase_next
	on_child_transition(current_state, attack)


func start_beat() -> void:
	on_child_transition(current_state, "Idle")


#THE PUNISH WINDOWS
# One parameterised state serves all four of them, so their rules can't drift apart.

func open_window(body: Node, duration: float, cap: int, enter_anim: StringName,
		hold_anim: StringName, exit_anim: StringName) -> void:
	var punish: State = states.get("Punish")
	punish.window_body = body
	punish.window_time = duration * fight.window_scale()
	punish.window_cap = cap
	punish.enter_anim = enter_anim
	punish.hold_anim = hold_anim
	punish.exit_anim = exit_anim
	on_child_transition(current_state, "Punish")


# Called by a state that opens a body itself, like Greyson's moment after each junk throw.
func set_open_body(body: Node) -> void:
	open_body = body


# What a body stands in between attacks: its phase-two idle once it is the only one left.
func rest_anim(body: Node) -> StringName:
	return &"phase2_idle" if fight.swapped and body == fight.survivor() else &"idle"


# Whose attack the next beat leads into, so the beat borrows that body's interval scale.
func next_attacker() -> Node:
	if chase_next:
		return computah() if fight.is_alive(computah()) else greyson()
	return laser_owner()


func is_open_to(body: Node) -> bool:
	return open_body == body and fight.is_alive(body) and not body.on_brink


# The state that opened the window decides what the body goes back to after the recoil.
func flinch(body: Node) -> void:
	if not is_open_to(body):
		return
	if current_state.has_method("flinch"):
		current_state.flinch(body)
	else:
		body.flinch()


# The finisher ended a window early. A state that owns a window inside a longer attack - Greyson's
# moment mid-chase - answers for itself, so a finisher there doesn't end the chase around it.
func end_window(body: Node, stagger_time: float) -> bool:
	if not is_open_to(body):
		return false
	if current_state.has_method("end_window"):
		return current_state.end_window(body, stagger_time)
	return _end_punish_window(body, stagger_time)


func _end_punish_window(body: Node, stagger_time: float) -> bool:
	window_timer.stop()
	open_body = null
	on_child_transition(current_state, "Idle")
	# Idle starts the beat before the next attack; the stagger replaces it.
	beat_timer.stop()
	# Held on the recoil frame through the stagger instead of the idle loop Idle started.
	body.play_anim(&"hit", &"idle" if body == greyson() else &"down")
	finisher_stagger_timer.start(stagger_time)
	return true


func _on_finisher_stagger_timer_timeout() -> void:
	start_cycle()


#THE PARRY STAGGER
# Only the pounce can be parried, and only the chase knows whether one is in the air.

func can_parry_stagger(body: Node, hit: RefCounted) -> bool:
	var chase: State = states.get("Chase")
	if current_state != chase or body != computah():
		return false
	return chase.can_parry_stagger(hit)


func parry_stagger(body: Node, duration: float) -> void:
	var chase: State = states.get("Chase")
	if current_state != chase or body != computah():
		return
	chase.parry_stagger(duration)


#THE SWAP AND THE END

func enter_swap(dead_body: Node) -> void:
	var swap: State = states.get("Swap")
	swap.dead_body = dead_body
	open_body = null
	for timer in [window_timer, finisher_stagger_timer, beat_timer]:
		timer.stop()
	on_child_transition(current_state, "Swap")


func enter_defeated() -> void:
	_end_fight("Defeated")


# The player lost: they stop where they stand.
func enter_player_defeated() -> void:
	_end_fight("Idle")
	player_defeated = true


func _end_fight(final_state_name: String) -> void:
	# Before anything else: a terminal path that never reaches Caught.Exit() still has to free the
	# player. A player left locked is unrecoverable.
	var caught: State = states.get("Caught")
	if caught:
		caught.release()
	open_body = null
	for body in fight.bodies():
		if is_instance_valid(body):
			ParryTell.clear(body)
	for hazard in get_tree().get_nodes_in_group(HAZARD_GROUP):
		hazard.queue_free()
	on_child_transition(current_state, final_state_name)
	# After the transition, not before: entering Idle starts the beat timer, which must not survive
	# the end of the fight.
	for timer in [post_dialogue_pre_fight_timer, window_timer, finisher_stagger_timer, beat_timer]:
		timer.stop()


#THE ARENA

# Guarded both ways because Caught.release() runs from _exit_tree(): a scene change mid-combo takes
# the fight down around it, and the release must not be the thing that errors on the way out.
func get_player() -> Node2D:
	if not is_inside_tree():
		return null
	var scene: Node = get_tree().current_scene
	return scene.get_node_or_null("Arena/MainPlayer/CharacterBody2D") if is_instance_valid(scene) else null


# Where Computah's feet may be while he runs: inside the ropes, and far enough from the top edge
# that his antenna stays on screen.
const RUNNER_MARGIN := Vector2(80, 60)


func runner_bounds() -> Rect2:
	return Rect2(ROPES.position + RUNNER_MARGIN, ROPES.size - RUNNER_MARGIN * 2.0)


# Everything they send out lives under the fight scene, so a finisher's freeze holds it and the end
# of the fight takes it away.
func add_hazard(hazard: Node2D, at: Vector2, layer: Node2D) -> void:
	hazard.add_to_group(HAZARD_GROUP)
	layer.add_child(hazard)
	hazard.global_position = at.round()


#THE PLAYER API
# Reused, never reinvented: the parry-only lock, the warp and the facing are all the player's own,
# and every call is guarded so a build without one of them still runs.

func lock_player() -> void:
	var player := get_player()
	if player and player.has_method("lock_actions"):
		player.lock_actions()
	else:
		_warn_once("lock", "GreysonComputah: player has no lock_actions(); the catch can't hold them")


func unlock_player() -> void:
	var player := get_player()
	if player and player.has_method("unlock_actions"):
		player.unlock_actions()


func warp_player(point: Vector2) -> void:
	var player := get_player()
	if player and player.has_method("warp_to"):
		player.warp_to(point.round())
	elif player:
		player.global_position = point.round()


func face_player_at(point: Vector2) -> void:
	var player := get_player()
	if player and player.has_method("face_point"):
		player.face_point(point)


func clear_player_facing() -> void:
	var player := get_player()
	if player and player.has_method("clear_face_point"):
		player.clear_face_point()


# The only existing way to hand back the post-grab i-frames and the toss. Calling it without a
# preceding grab() is harmless - it sets is_grabbed false, which it already is, shows the sprite,
# which is already shown, and gives the push and the i-frames, which is the whole point - and it is
# why the five-hit combo never calls grab(): the player keeps their own sprite through it.
func release_player(push: Vector2) -> void:
	var player := get_player()
	if player and player.has_method("release_grab"):
		player.release_grab(push)


# Called at the start of EVERY pounce tell, always. PlayerDefense counts a press that didn't parry
# against the next attack for parry_mash_lockout (0.5 s), so without this a whiffed press can leave
# the next pounce mathematically unparryable. Carter's fight learned this the hard way.
func rearm_parry() -> void:
	var defense := _defense()
	if defense and defense.has_method("rearm_parry"):
		defense.rearm_parry()
	else:
		_warn_once("rearm", "GreysonComputah: PlayerDefense has no rearm_parry(); a whiffed press can lock out the next pounce")


func _defense() -> Node:
	var player := get_player()
	return player.get("defense") if player else null


func _warn_once(key: String, message: String) -> void:
	if warned.has(key):
		return
	warned[key] = true
	push_warning(message)
