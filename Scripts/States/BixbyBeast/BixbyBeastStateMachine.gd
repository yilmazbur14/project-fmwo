extends Node

@export var initial_state : State

@export var states : Dictionary = {}
@export var current_state : State
@export var BixbyBeastCharacterBody : CharacterBody2D

#TIMERS
@export var post_dialogue_pre_fight_timer: Timer
@export var recover_timer: Timer
@export var finisher_stagger_timer: Timer

const PRE_FIGHT_DIALOGUE := "res://Dialogue/LiamPreFight.dialogue"
const HAZARD_GROUP := "bixby_beast_hazard"
# The inside edges of the ropes, as Mason's Carter call-in measures them.
const ROPES := Rect2(113, 114, 1692, 853)

# The fight's loop: hover and strafe, run the cycle's attacks with a short hover between them, land for
# the punishable recovery, take off, repeat. Cycles take turns through this list, so every second cycle
# breathes fire twice. A new attack is a state that calls attack_finished() when it's done, listed here.
const ATTACK_CYCLES := [["FireBreath"], ["FireBreath", "FireBreath"]]

#TUNING (seconds, px and px/s)
@export var hover_time := 1.8
@export var hover_between_attacks := 0.5
@export var hover_speed := 460.0
# While hovering he strafes between points this far to either side of the player, this far up the arena from them.
@export var strafe_distance := 360.0
@export var hover_lead := 260.0
# The fire breath's telegraph: he flies over the player until he's this close to lined up, or for this long.
@export var breath_approach_speed := 1100.0
@export var breath_align_distance := 16.0
@export var breath_approach_time := 1.6
@export var breath_windup := 0.5
# The stream, including the burst it starts and ends on.
@export var breath_time := 1.4
@export var breath_burst_time := 0.15
# How fast the stream follows the player sideways while it's out.
@export var breath_drift_speed := 90.0
# How far below his feet he aims the player, in the wide lower half of the stream.
@export var breath_aim_depth := 200.0
# Against the back rope, the most the player can be above his feet and still be in the fire from his
# mouths, and how far past the top of the screen his sprite may go to get there.
@export var breath_mouth_reach := 195.0
@export var breath_top_overshoot := 120.0
# How far past a side of the screen his sprite may go to reach a player against a side rope.
@export var breath_side_overshoot := 48.0
@export var land_time := 0.5
@export var recover_time := 3.5
@export var takeoff_time := 0.6

var player_defeated := false
var cycles_started := 0
var attacks: Array = []
var attacks_done := 0


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


# The intro's lines call its beats, so it passes itself along to the dialogue.
func show_pre_fight_dialogue(intro: State) -> void:
	# One-shot: the outro's lines end a dialogue too, and must not start the fight again.
	DialogueManager.dialogue_ended.connect(_on_dialogue_ended, CONNECT_ONE_SHOT)
	DialogueManager.show_dialogue_balloon(load(PRE_FIGHT_DIALOGUE), "start", [intro])


func _on_dialogue_ended(_dialogue: Object) -> void:
	post_dialogue_pre_fight_timer.start()


func _on_post_dialogue_pre_fight_timer_timeout() -> void:
	BixbyBeastCharacterBody.start_music()
	start_cycle()


func start_cycle() -> void:
	attacks = ATTACK_CYCLES[cycles_started % ATTACK_CYCLES.size()].duplicate()
	attacks_done = 0
	cycles_started += 1
	on_child_transition(current_state, "Hover")


# A full strafe before a cycle's first attack, a short one between attacks.
func hover_duration() -> float:
	return hover_time if attacks_done == 0 else hover_between_attacks


func hover_finished(state: State) -> void:
	if state != current_state:
		return
	on_child_transition(state, "Land" if attacks.is_empty() else attacks.pop_front())


func attack_finished(state: State) -> void:
	if state != current_state:
		return
	attacks_done += 1
	on_child_transition(state, "Land" if attacks.is_empty() else "Hover")


func is_recovering() -> bool:
	return current_state == states.get("Recover")


func flinch() -> void:
	if is_recovering():
		current_state.flinch()


# The finisher ended his recovery early: he stays down, staggered, then takes off into the next cycle.
func stagger_then_take_off(stagger_time: float) -> void:
	recover_timer.stop()
	on_child_transition(current_state, "Idle")
	finisher_stagger_timer.start(stagger_time)


func _on_finisher_stagger_timer_timeout() -> void:
	on_child_transition(states.get("Idle"), "Takeoff")


func get_player() -> Node2D:
	return get_tree().current_scene.get_node_or_null("Arena/MainPlayer/CharacterBody2D")


func enter_defeated() -> void:
	_end_fight("Defeated")


# The player lost: he stops where he is.
func enter_player_defeated() -> void:
	_end_fight("Idle")
	player_defeated = true


func _end_fight(final_state_name: String) -> void:
	for timer in [post_dialogue_pre_fight_timer, recover_timer, finisher_stagger_timer]:
		timer.stop()
	on_child_transition(current_state, final_state_name)
