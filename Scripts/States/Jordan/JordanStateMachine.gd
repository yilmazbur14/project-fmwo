extends Node

@export var initial_state : State

@export var states : Dictionary = {}
@export var current_state : State
@export var JordanCharacterBody : CharacterBody2D

#TIMERS
@export var post_dialogue_pre_fight_timer: Timer
@export var finisher_stagger_timer: Timer

const VsCard := preload("res://Scripts/VsCard.gd")
const JordanIntro := preload("res://Scripts/States/Jordan/JordanIntro.gd")
const JordanBroken := preload("res://Scripts/States/Jordan/JordanBroken.gd")
const JordanJuggled := preload("res://Scripts/States/Jordan/JordanJuggled.gd")
const PRE_FIGHT_DIALOGUE := "res://Dialogue/JordanPreFight.dialogue"
const HAZARD_GROUP := "jordan_hazard"

# Phase 1's loop, a placeholder until his other attacks are designed: Idle, SummonFunkos, Taunt, then
# back to Idle, which waits for the swarm to be over before it rests.
const IDLE_TIME := 1.2
const SUMMON_WINDUP := 0.8
# Figures per summon. Summons take turns through the list.
const SUMMON_COUNTS := [3, 4]
# The figures pop in evenly spaced around the middle of his hurtbox on an ellipse with these radii, in
# px. Its height clears that box by 15 px above and below once a figure's own half height is counted,
# the margin the old ring kept round the old 64x64 sprite: a figure that popped in over his head would
# be drawn behind him.
const SUMMON_RING := Vector2(170, 170)
const TAUNT_TIME := 3.0
# The swarm is over once every figure is gone, or this many seconds after it was summoned.
const SWARM_WAIT_LIMIT := 5.0

# States only run while the fight is on: not during the pre-fight lines, and not once it's decided.
var fighting := false
var player_defeated := false
var summons := 0
var last_summon_time := -INF
var stagger_left := 0.0
# The pre-fight lines' balloon, which a held skip takes down, and whether those lines have handed
# over to the VS card yet.
var pre_fight_balloon: Node
var pre_fight_over := false


func _ready() -> void:
	# His lines are all of his entrance, and he waits them out in the intro that carries the hold to
	# skip over them. The fight itself starts on the scene's initial state once the card is gone.
	var intro := JordanIntro.new()
	intro.name = "Intro"
	intro.body = JordanCharacterBody
	add_child(intro)
	# The Break window and the juggle it pays out, built in code like the intro: neither needs anything
	# the scene would have to wire.
	_add_down_state(JordanBroken.new(), "Broken")
	_add_down_state(JordanJuggled.new(), "Juggled")
	show_pre_fight_dialogue()

	for child in get_children():
		if child is State:
			states[child.name] = child

	current_state = intro
	# Deferred until the body is ready, since the intro draws him.
	current_state.Enter.call_deferred()


# His body's own ready comes after this node's, so its hurtbox is looked up rather than read off it.
func _add_down_state(state: Node, state_name: String) -> void:
	state.name = state_name
	state.body = JordanCharacterBody
	state.hurtbox = JordanCharacterBody.get_node("Hurtbox")
	state.state_machine = self
	add_child(state)


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


# His lines call no beats, so the dialogue needs nothing from his intro.
func show_pre_fight_dialogue() -> void:
	# One-shot: the outro's lines end a dialogue too, and must not start the fight again.
	DialogueManager.dialogue_ended.connect(_on_dialogue_ended, CONNECT_ONE_SHOT)
	pre_fight_balloon = DialogueManager.show_dialogue_balloon(load(PRE_FIGHT_DIALOGUE), "start")


# A held skip's way past the lines (BossEntrance): the hand-over their own end makes, made from here
# instead. pre_fight_over keeps it to once.
func end_pre_fight_dialogue() -> void:
	if pre_fight_over:
		return
	if DialogueManager.dialogue_ended.is_connected(_on_dialogue_ended):
		DialogueManager.dialogue_ended.disconnect(_on_dialogue_ended)
	_on_dialogue_ended(null)


func _on_dialogue_ended(_dialogue: Object) -> void:
	pre_fight_over = true
	var intro = states.get("Intro")
	if intro:
		intro.lines_over()
	VsCard.play_intro(self, "jordan", post_dialogue_pre_fight_timer.start)


# The fight opens on the scene's own first state, Idle, which rests IDLE_TIME before his first summon.
func _on_post_dialogue_pre_fight_timer_timeout() -> void:
	JordanCharacterBody.start_music()
	on_child_transition(current_state, initial_state.name)
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


# A full Break gauge (BossBreakGauge): whatever he was doing stops, every figure goes, and he is Broken
# until his time is up or the finisher's uppercut ends it.
func enter_broken() -> void:
	if not fighting or current_state in [states.get("Defeated"), states.get("Broken"), states.get("Juggled")]:
		return
	for hazard in get_tree().get_nodes_in_group(HAZARD_GROUP):
		hazard.queue_free()
	stagger_left = 0.0
	finisher_stagger_timer.stop()
	on_child_transition(current_state, "Broken")


# The finisher's uppercut ends the Break window instead of its own clock, as it ends a taunt.
func end_break(delay: float) -> void:
	end_taunt(maxf(delay, 0.01))


# The tiered finisher's first uppercut (JordanScript.begin_juggle).
func enter_juggled() -> void:
	var juggled = states["Juggled"]
	if JordanCharacterBody.defeated or current_state == juggled:
		return
	on_child_transition(current_state, "Juggled")


# Down after a juggle, he gets up where he crashed and summons `delay` after this, as after a taunt.
# Idle's own Enter plays his idle, since the juggle hands back no animation to finish.
func after_juggle(delay: float) -> void:
	end_taunt(maxf(delay, 0.01))


# The one switch past the fight being decided: a juggled Jordan, killed in the air, lands into his
# defeat rather than snapping to its pose mid-flight.
func land_juggled(final_state_name: String) -> void:
	var final_state = states.get(final_state_name)
	if final_state == states.get("Defeated"):
		final_state.lying = true
	current_state.Exit()
	final_state.Enter()
	current_state = final_state


# The fight's floor layer (Arena/GroundFx, which the finisher's ground effects use too), or his scene in
# a fight without one, where his juggle's shadow y-sorts at his soles.
func ground_layer() -> Node2D:
	var arena: Node = JordanCharacterBody.get_parent().get_parent()
	var layer: Node2D = arena.get_node_or_null("GroundFx") if arena else null
	return layer if layer else JordanCharacterBody.get_parent()


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
	var juggled = states.get("Juggled")
	# In the air, he finishes his fall and his crash first (land_juggled). The juggle draws itself on
	# its own clock, so it plays out with the fight no longer running.
	if juggled and current_state == juggled:
		juggled.final_state = final_state_name
		return
	on_child_transition(current_state, final_state_name)
