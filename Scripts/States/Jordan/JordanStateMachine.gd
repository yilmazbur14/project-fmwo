extends Node

@export var initial_state : State

@export var states : Dictionary = {}
@export var current_state : State
@export var JordanCharacterBody : CharacterBody2D

#TIMERS
@export var post_dialogue_pre_fight_timer: Timer
@export var finisher_stagger_timer: Timer

const HAZARD_GROUP := "jordan_hazard"

# Phase 1's loop, a placeholder until his other attacks are designed: Idle, SummonFunkos, Taunt, then
# back to Idle, which waits for the swarm to be over before it rests.
const IDLE_TIME := 1.2
const SUMMON_WINDUP := 0.8
# Figures per summon. Summons take turns through the list.
const SUMMON_COUNTS := [3, 4]
# The figures pop in evenly spaced around him on an ellipse with these radii, in px.
const SUMMON_RING := Vector2(170, 130)
const TAUNT_TIME := 3.0
# The swarm is over once every figure is gone, or this many seconds after it was summoned.
const SWARM_WAIT_LIMIT := 5.0

# States only run while the fight is on: not during the pre-fight lines, and not once it's decided.
var fighting := false
var player_defeated := false
var summons := 0
var last_summon_time := -INF
var stagger_left := 0.0


func _ready() -> void:
	DialogueManager.show_dialogue_balloon(load("res://Dialogue/JordanPreFight.dialogue"), "start")
	# One-shot: the outro's lines end a dialogue too, and must not start the fight again.
	DialogueManager.dialogue_ended.connect(_on_dialogue_ended, CONNECT_ONE_SHOT)

	for child in get_children():
		if child is State:
			states[child.name] = child

	if initial_state:
		current_state = initial_state
		current_state.Enter()


func _process(delta: float) -> void:
	if current_state and fighting and stagger_left <= 0.0:
		current_state.Update(delta)


func _physics_process(delta: float) -> void:
	if not fighting:
		return
	# A stagger holds the current state where it is, and it carries on afterwards.
	if stagger_left > 0.0:
		stagger_left -= delta
		return
	if current_state:
		current_state.Physics_Update(delta)


func on_child_transition(state, new_state_name):
	if state != current_state:
		return

	# Defeat, Jordan's or the player's, is terminal: nothing late may restart the fight.
	if current_state == states.get("Defeated") or player_defeated:
		return

	var new_state = states.get(new_state_name)
	if !new_state:
		return

	if current_state:
		current_state.Exit()

	new_state.Enter()
	current_state = new_state


func _on_dialogue_ended(_dialogue: Object) -> void:
	post_dialogue_pre_fight_timer.start()


func _on_post_dialogue_pre_fight_timer_timeout() -> void:
	JordanCharacterBody.start_music()
	fighting = true


func get_player() -> Node2D:
	return get_tree().current_scene.get_node_or_null("Arena/MainPlayer/CharacterBody2D")


# Positioned before it's added, so the hazard's _ready already sees where it spawned.
func add_hazard(hazard: Node2D, spawn_position: Vector2) -> void:
	hazard.position = spawn_position
	get_tree().current_scene.add_child(hazard)


func swarm_over() -> bool:
	if JordanCharacterBody.fight_clock - last_summon_time >= SWARM_WAIT_LIMIT:
		return true
	return get_tree().get_nodes_in_group(HAZARD_GROUP).is_empty()


func is_taunting() -> bool:
	return current_state == states.get("Taunt")


func stagger(duration: float) -> void:
	stagger_left = maxf(stagger_left, duration)


# The player's finisher cut the taunt short. Idle holds while the stagger timer runs, which stands in for his rest.
func end_taunt(stagger_time: float) -> void:
	on_child_transition(current_state, "Idle")
	states["Idle"].rested = IDLE_TIME
	finisher_stagger_timer.start(stagger_time)


func enter_defeated() -> void:
	_end_fight("Defeated")


# The player lost: he stops where he is and stands idle.
func enter_player_defeated() -> void:
	_end_fight("Idle")
	player_defeated = true


func _end_fight(final_state_name: String) -> void:
	post_dialogue_pre_fight_timer.stop()
	finisher_stagger_timer.stop()
	fighting = false
	stagger_left = 0.0
	on_child_transition(current_state, final_state_name)
