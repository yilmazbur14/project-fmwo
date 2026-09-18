extends Node

# Carter's fight, boss 5. His cycle is one move: Intro once, then RagingDemon -> Recover -> Idle ->
# RagingDemon for as long as he is standing. It is shaped so a second attack slots in beside
# RagingDemon without any of this changing.
#
# THE DIFFICULTY AXIS IS THE NUMBER OF YELLOWS, AND NOTHING ELSE. Fifteen clones, identical rhythm,
# every round forever - that is what makes the fight learnable. To make it harder, raise what
# yellow_count() returns. Never shorten clone_show: 0.44 s is a red/yellow DISCRIMINATION reaction
# (~0.35-0.40 s), which is slower than a simple one, and cutting it makes the move a coin flip
# rather than a read.
#
# THE PLAYER-API WRAPPERS BELOW ARE THE ONLY PLACE THIS FIGHT TOUCHES THE PLAYER'S LOCK, PARRY OR
# STAMINA. Each is has_method-guarded with a one-shot push_warning, like JoshCardsStateMachine's
# apply_status(): the parts of the API that aren't written yet leave the fight running and testable,
# just easier. PlayerScript.gd and PlayerDefense.gd belong to the defence coder; nothing here edits
# them.

@export var initial_state : State

@export var states : Dictionary = {}
@export var current_state : State
@export var CarterAkumaCharacterBody : CharacterBody2D

#TIMERS
@export var post_dialogue_pre_fight_timer: Timer
@export var recover_timer: Timer
@export var finisher_stagger_timer: Timer
@export var beat_timer: Timer

const PRE_FIGHT_DIALOGUE := "res://Dialogue/CarterPreFight.dialogue"
const HAZARD_GROUP := "carter_hazard"

# The inside edges of the ropes, as every other fight measures them, and the point he drags the
# player to. Nothing else may hardcode either.
const ROPES := Rect2(113, 114, 1692, 853)
const ARENA_CENTRE := Vector2(959, 540)

#TUNING (seconds and px)
# Beat 0: the eyes go. The lock lands on frame 1 of this, not at the end of it - a player mid-dash
# has to stop before the yank, not during it.
@export var flash_time := 0.55
# Beat 1: dragged to the middle. Not a teleport; the drive is what sells it as him grabbing you.
# The drive is 0.20 rather than the plan's 0.30 because carter_warp.wav's arrival transient lands
# 195 ms in: the sound and the landing have to be the same moment. The beat is still 0.35 s - what
# the drive gives up, the hold after it takes - so nothing downstream moved.
@export var yank_time := 0.20
@export var yank_hold := 0.15
# Beat 2: the lights go out.
@export var darken_time := 0.45
# Beat 3: the barrage. clone_show is the read, clone_dash the timing cue; splitting them is what
# makes the parry window fair.
# CLONE_SHOW IS AT ITS FLOOR AT 0.36 AND MUST NOT GO BELOW IT. Telling red from yellow is a
# DISCRIMINATION reaction, about 0.35 s, which is slower than simply reacting to something appearing;
# 0.36 is the last value at which a player can still make that decision at all. It came down from
# 0.44 once, on the user's call, and there is nothing left to give. Anything under this and the
# feints stop being readable and the whole mechanic is a coin flip. Cut somewhere else.
# The cadence is clone_show + clone_dash + clone_gap = 0.62 s. That is well inside
# PlayerDefense.parry_mash_lockout (0.5 s) plus the parry window, so the cadence is no longer its own
# safety net: the rearm_parry() this fight makes as each light comes up is what keeps consecutive
# clones answerable. Don't remove it, and don't shorten anything here without re-reading that.
# One clone lives clone_show + clone_dash = 0.54 s against that 0.62 s cadence, so two lights are
# never up at once and the player always knows which clone a press is answering. CLONE_LIGHT_OUT is
# what keeps a feint's light from being the second one on screen; it has 0.08 s to work in.
@export var clone_count := 15
@export var clone_show := 0.36
@export var clone_dash := 0.18
@export var clone_gap := 0.08
@export var clone_radius := 420.0
# Beat 4: the lights come up and he is standing there.
@export var clear_time := 0.50
@export var recover_offset := 340.0
# Beat 5: the punish window, longer for a barrage read well and shorter for one blown. The per-parry
# numbers are small because there are fifteen clones to earn them on, not five; the cap is what a
# perfect barrage is worth.
@export var recover_base := 3.0
@export var recover_parry_bonus := 0.2
@export var recover_miss_penalty := 0.25
@export var recover_min := 1.5
@export var recover_max := 6.0
# The banked damage a barrage earns: one half-heart per this many reds parried, plus the bonus for a
# barrage with every red parried and no feint bitten. Scaled to fifteen clones, so a barrage read
# well is worth proportionally what the five-clone version was.
@export var bank_per_parries := 3
@export var bank_perfect_bonus := 2
# Beat 6: the breath before he starts again.
@export var beat_time := 0.60
# What parrying a yellow costs. More than any block in the game: if it empties the bar the existing
# guard break fires, which is self-inflicted and legible.
@export var feint_stamina := 40.0

var player_defeated := false
var cycles_started := 0
# Locked once, at the top of each cycle, so a hit landing mid-sequence can't change what the rest of
# it does.
var cycle_yellows := 0

var warned := {}


func _ready() -> void:
	for child in get_children():
		if child is State:
			states[child.name] = child

	if initial_state:
		current_state = initial_state
		# Deferred until the body is ready, since the intro moves and draws him.
		current_state.Enter.call_deferred()


func _process(delta: float) -> void:
	if current_state:
		current_state.Update(delta)


func _physics_process(delta: float) -> void:
	if current_state:
		current_state.Physics_Update(delta)


func on_child_transition(state, new_state_name):
	if state != current_state:
		return

	# Defeat, his or the player's, is terminal: a late timer must never restart the fight.
	if current_state == states.get("Defeated") or player_defeated:
		return

	var new_state = states.get(new_state_name)
	if !new_state:
		return

	if current_state:
		current_state.Exit()

	new_state.Enter()
	current_state = new_state


#THE CYCLE

# His lines call no beats, so the intro hands the dialogue over and waits for it to end.
func show_pre_fight_dialogue() -> void:
	# One-shot: the outro's lines end a dialogue too, and must not start the fight again.
	DialogueManager.dialogue_ended.connect(_on_dialogue_ended, CONNECT_ONE_SHOT)
	DialogueManager.show_dialogue_balloon(load(PRE_FIGHT_DIALOGUE), "start")


func _on_dialogue_ended(_dialogue: Object) -> void:
	post_dialogue_pre_fight_timer.start()


func _on_post_dialogue_pre_fight_timer_timeout() -> void:
	CarterAkumaCharacterBody.start_music()
	start_cycle()


func start_cycle() -> void:
	cycles_started += 1
	cycle_yellows = yellow_count()
	on_child_transition(current_state, "RagingDemon")


# The one difficulty dial. Cycle 1 is all red - it teaches the rhythm - and after that it is his
# health that decides how many of the fifteen lie. The cap is 6 rather than the proportional 9: no
# two feints may be adjacent (CarterRagingDemon._build_pattern), and above 6 in fourteen slots the
# only arrangements left are near-forced ones the player would learn as a fixed pattern.
func yellow_count() -> int:
	if cycles_started <= 1:
		return 0
	var ratio: float = CarterAkumaCharacterBody.get_health_ratio()
	if ratio > 0.66:
		return 3
	if ratio > 0.33:
		return 5
	return 6


# Light to light. At 0.70 s this is inside PlayerDefense.parry_mash_lockout's reach, so a press that
# whiffs late on one clone WOULD lock the guard out of the next one if the fight didn't re-arm the
# parry as each light comes up.
func clone_interval() -> float:
	return clone_show + clone_dash + clone_gap


# The punish window the round earned. Later rounds have fewer reds to parry, so the longest possible
# window shrinks as he gets more dangerous.
func recover_window(reds_parried: int, reds_missed: int) -> float:
	return clampf(recover_base + recover_parry_bonus * reds_parried - recover_miss_penalty * reds_missed,
		recover_min, recover_max)


# His one punish window per cycle.
func is_recovering() -> bool:
	return current_state == states.get("Recover")


func flinch() -> void:
	if is_recovering():
		current_state.flinch()


# The finisher ended his recovery early: he stays down, staggered, then starts the next cycle.
func stagger_then_start_cycle(stagger_time: float) -> void:
	recover_timer.stop()
	on_child_transition(current_state, "Idle")
	# Idle starts the beat before the next Demon; the stagger replaces it.
	beat_timer.stop()
	# Held on the recoil frame through the stagger instead of the idle loop Idle starts.
	CarterAkumaCharacterBody.play_anim(&"hit", &"idle")
	finisher_stagger_timer.start(stagger_time)


func _on_finisher_stagger_timer_timeout() -> void:
	start_cycle()


func get_player() -> Node2D:
	return get_tree().current_scene.get_node_or_null("Arena/MainPlayer/CharacterBody2D")


# Everything he sends out lives under the fight scene, so a finisher's freeze holds it and the end of
# the fight takes it away.
func add_hazard(hazard: Node2D, at: Vector2, layer: Node2D) -> void:
	hazard.add_to_group(HAZARD_GROUP)
	layer.add_child(hazard)
	hazard.global_position = at.round()


#THE PLAYER API

# Held for a parry-only sequence: no walking, no dash, no punch, while the guard, its parry window
# and the streak behind it all keep working. It must never be confused with is_grabbed or is_talking,
# which PlayerScript._input returns on BEFORE the block branch - reusing either would make the
# sequence unparryable with no error at all.
func lock_player() -> void:
	var player := get_player()
	if player and player.has_method("lock_actions"):
		player.lock_actions()
	else:
		_warn_once("lock", "Carter: player has no lock_actions(); the Demon can't root them")


func unlock_player() -> void:
	var player := get_player()
	if player and player.has_method("unlock_actions"):
		player.unlock_actions()


# Turned to meet each clone as its light comes up. It changes nothing about whether the parry lands -
# the hit's origin is the player's own hurtbox centre, so any facing answers it - it is the drama of
# the sequence, and unlock_actions() clears it.
func face_player_at(point: Vector2) -> void:
	var player := get_player()
	if player and player.has_method("face_point"):
		player.face_point(point)


func clear_player_facing() -> void:
	var player := get_player()
	if player and player.has_method("clear_face_point"):
		player.clear_face_point()


# The darkness draws above the floor and below the fighters, and the player's own stage is z 0, so
# the sequence lifts it over the dark and puts it back. The only thing this fight writes to a node it
# doesn't own, and CarterRagingDemon.release() is what undoes it.
func set_player_stage_z(z: int) -> void:
	var player := get_player()
	if player == null:
		return
	var stage := player.get_parent()
	if stage is CanvasItem:
		stage.z_index = z


func player_stage_z() -> int:
	var player := get_player()
	if player == null:
		return 0
	var stage := player.get_parent()
	return stage.z_index if stage is CanvasItem else 0


# Called on the exact frame each clone's light comes up, all five, every round. PlayerDefense counts
# a press that didn't parry against the next one for parry_mash_lockout (0.5 s), and every further
# press inside that pushes the clock forward, so without this a player who whiffs on clone N can be
# mathematically unable to parry clone N+1.
# It deliberately does NOT fix mashing WITHIN one clone's window: an early press still whiffs and
# still locks that clone out. Do not widen this into a per-press re-arm or the fight becomes a
# mash-fest.
func rearm_parry() -> void:
	var defense := _defense()
	if defense and defense.has_method("rearm_parry"):
		defense.rearm_parry()
	else:
		_warn_once("rearm", "Carter: PlayerDefense has no rearm_parry(); a whiffed clone can lock out the next")


func end_parry_streak() -> void:
	var defense := _defense()
	if defense and defense.has_method("end_parry_streak"):
		defense.end_parry_streak()
	else:
		_warn_once("streak", "Carter: PlayerDefense has no end_parry_streak(); a parried feint keeps the streak")


func drain_stamina(amount: float) -> void:
	var defense := _defense()
	if defense and defense.has_method("drain_stamina"):
		defense.drain_stamina(amount)
	else:
		_warn_once("stamina", "Carter: PlayerDefense has no drain_stamina(); a parried feint costs nothing")


# Returns whether the signal was there. When it wasn't, the caller polls the block action in
# Physics_Update instead - and only there, since polling in both would fire the punish twice.
func connect_block_presses(handler: Callable) -> bool:
	var defense := _defense()
	if defense and defense.has_signal("block_pressed"):
		if not defense.block_pressed.is_connected(handler):
			defense.block_pressed.connect(handler)
		return true
	_warn_once("presses", "Carter: PlayerDefense has no block_pressed signal; feints fall back to polling")
	return false


func disconnect_block_presses(handler: Callable) -> void:
	var defense := _defense()
	if defense and defense.has_signal("block_pressed") and defense.block_pressed.is_connected(handler):
		defense.block_pressed.disconnect(handler)


func _defense() -> Node:
	var player := get_player()
	return player.get("defense") if player else null


func _warn_once(key: String, message: String) -> void:
	if warned.has(key):
		return
	warned[key] = true
	push_warning(message)


#THE END OF THE FIGHT

func enter_defeated() -> void:
	_end_fight("Defeated")


# The player lost: he turns his back on them and the emblem burns.
func enter_player_defeated() -> void:
	_end_fight("Victory")
	player_defeated = true


func _end_fight(final_state_name: String) -> void:
	# Before anything else: a terminal path that never reaches RagingDemon.Exit() still has to free
	# the player and take the curtain down. A player left locked is unrecoverable.
	var demon: State = states.get("RagingDemon")
	if demon:
		demon.release()
	for hazard in get_tree().get_nodes_in_group(HAZARD_GROUP):
		hazard.queue_free()
	on_child_transition(current_state, final_state_name)
	# After the transition, not before: entering Idle starts the beat timer, which must not survive
	# the end of the fight.
	for timer in [post_dialogue_pre_fight_timer, recover_timer, finisher_stagger_timer, beat_timer]:
		timer.stop()
