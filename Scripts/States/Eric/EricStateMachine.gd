extends Node

@export var initial_state : State

@export var states : Dictionary = {}
@export var current_state : State

#TIMERS
@export var post_dialogue_pre_fight_timer: Timer
@export var rest_timer: Timer
@export var downed_state_timer: Timer

const ParryTell := preload("res://Scripts/ParryTell.gd")

const HAZARD_GROUP := "eric_hazard"
const ATTACKS := ["Earthquake", "Whirlwind", "SwordThrow", "BearHug"]

#PACING
# Long enough to walk up to him and land two full three-punch combos.
@export var downed_duration := 6.0
@export var attacks_per_chain := 3
# At or below this health ratio every chain gets one more attack.
@export var rage_chain_health_ratio := 0.34
@export var rage_attacks_per_chain := 4
# Idle between attacks in a chain, at full health and at none.
@export var attack_gap := 0.45
@export var rage_attack_gap := 0.3
# Idle after getting up, before the next chain.
@export var recovery_rest := 0.6

# 0 at full health, 1 at none; set at the start of each chain. Attack states scale their
# speeds with it.
var rage := 0.0
var chain : Array = []
var last_attack := ""
var state_after_rest := ""
var defeated := false

@onready var boss = get_parent()


# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	DialogueManager.show_dialogue_balloon(load("res://Dialogue/EricPreFight.dialogue"), "start")
	# One-shot: the outro's lines end a dialogue too, and must not start the fight again.
	DialogueManager.dialogue_ended.connect(_on_dialogue_ended, CONNECT_ONE_SHOT)

	for child in get_children():
		if child is State:
			states[child.name] = child

	print("State Machine initialized with states: ", states.keys())

	if initial_state:
		current_state = initial_state
		current_state.Enter()


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	if current_state:
		current_state.Update(delta)

func _physics_process(delta: float) -> void:
	if current_state:
		current_state.Physics_Update(delta)

func on_child_transition(state, new_state_name):
	# Defeat is terminal: a late timer or animation signal must never restart the fight.
	if state != current_state or defeated:
		return

	var new_state = states.get(new_state_name)
	if !new_state:
		return

	if current_state:
		current_state.Exit()

	new_state.Enter()
	current_state = new_state

func _on_dialogue_ended(dialogue: Object) -> void:
	print("post dialogue timer started: ", post_dialogue_pre_fight_timer)
	post_dialogue_pre_fight_timer.start()


func _on_post_dialogue_pre_fight_timer_timeout() -> void:
	print("post dialogue timer done")
	if boss and boss.has_method("start_music"):
		boss.start_music()
	start_chain(0.0)


func _play_downed_stinger() -> void:
	if boss:
		var sfx = boss.get_node_or_null("DownedSfxPlayer")
		if sfx:
			sfx.play()


# A chain of different attacks in a random order, then the Downed window.
func start_chain(delay: float) -> void:
	var health_ratio: float = boss.get_health_ratio()
	rage = clampf(1.0 - health_ratio, 0.0, 1.0)
	var count := rage_attacks_per_chain if health_ratio <= rage_chain_health_ratio else attacks_per_chain

	var bag := ATTACKS.duplicate()
	bag.shuffle()
	if bag[0] == last_attack:
		bag.push_back(bag.pop_front())
	chain = bag.slice(0, count)
	_next_attack(delay)


# Called by an attack state once Eric is back in his idle pose at his starting spot.
func attack_finished() -> void:
	if chain.is_empty():
		downed_state_timer.start(downed_duration)
		on_child_transition(current_state, "Downed")
		_play_downed_stinger()
	else:
		_next_attack(lerpf(attack_gap, rage_attack_gap, rage))


func _next_attack(delay: float) -> void:
	last_attack = chain.pop_front()
	if delay <= 0.0:
		on_child_transition(current_state, last_attack)
		return
	state_after_rest = last_attack
	on_child_transition(current_state, "Idle")
	rest_timer.start(delay)


func _on_rest_timer_timeout() -> void:
	on_child_transition(states.get("Idle"), state_after_rest)


func _on_downed_timer_timeout() -> void:
	start_chain(recovery_rest)


# Hazards live under Eric's scene root, ahead of his body, so they draw above the floor and
# below him, and don't move with him.
func add_hazard(hazard: Node2D, spawn_position: Vector2) -> void:
	hazard.add_to_group(HAZARD_GROUP)
	var root: Node2D = boss.get_parent()
	hazard.position = root.to_local(spawn_position)
	root.add_child(hazard)
	root.move_child(hazard, 0)


func enter_defeated() -> void:
	_end_fight("Downed")


# The player lost: he stops attacking and stands idle.
func enter_player_defeated() -> void:
	_end_fight("Idle")


# Called by the boss after a parry: his attack stops and he's open to punches for `duration`, then he
# picks himself up at `home`, where the attack started.
func parry_stagger(duration: float, home: Vector2) -> void:
	states["ParryStaggered"].duration = duration
	states["ParryStaggered"].home = home
	on_child_transition(current_state, "ParryStaggered")


func _end_fight(final_state_name: String) -> void:
	ParryTell.clear(boss)
	post_dialogue_pre_fight_timer.stop()
	rest_timer.stop()
	downed_state_timer.stop()
	states["ParryStaggered"].stagger_timer.stop()
	# Anything he threw that outlives the fight could still hurt the player.
	for hazard in get_tree().get_nodes_in_group(HAZARD_GROUP):
		hazard.queue_free()
	if current_state != states.get(final_state_name):
		on_child_transition(current_state, final_state_name)
	# Terminal whoever lost.
	defeated = true
