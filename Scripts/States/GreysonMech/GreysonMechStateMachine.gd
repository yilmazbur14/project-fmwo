extends Node

@export var initial_state : State

@export var states : Dictionary = {}
@export var current_state : State
@export var mech : Node2D

#TIMERS
@export var rest_timer : Timer

# Set by rage scaling at the start of every cycle.
var cycle_pause := 1.0
var attack_gap := 0.6

var state_after_rest := ""
var player_defeated := false


func _ready() -> void:
	for child in get_children():
		if child is State:
			states[child.name] = child

	if initial_state:
		current_state = initial_state
		current_state.Enter()


func _process(delta: float) -> void:
	if current_state:
		current_state.Update(delta)


func _physics_process(delta: float) -> void:
	if current_state:
		current_state.Physics_Update(delta)


func on_child_transition(state, new_state_name):
	if state != current_state:
		return

	# Defeat, the mech's or the player's, is terminal: a late timer or animation signal must never
	# restart the fight.
	if current_state == states.get("Defeated") or player_defeated:
		return

	var new_state = states.get(new_state_name)
	if !new_state:
		return

	if current_state:
		current_state.Exit()

	new_state.Enter()
	current_state = new_state


# One cycle: laser sweep from the elbow barrels, rocket volley from the shoulder racks, a wait
# for the rockets to clear, then the ground pound, which overheats the mech into its only
# vulnerable window.
func start_cycle() -> void:
	_apply_rage_scaling()
	rest_then("LaserSweep", cycle_pause)


func rest_then(next_state_name: String, duration: float) -> void:
	state_after_rest = next_state_name
	on_child_transition(current_state, "Idle")
	rest_timer.start(duration)


func _on_rest_timer_timeout() -> void:
	on_child_transition(states.get("Idle"), state_after_rest)


func _apply_rage_scaling() -> void:
	# 0 when the mech takes over at half health, 1 as it runs out.
	var rage := clampf(1.0 - mech.get_health_ratio() / mech.computah.PHASE_TWO_RATIO, 0.0, 1.0)

	cycle_pause = lerpf(1.0, 0.6, rage)
	attack_gap = lerpf(0.6, 0.35, rage)

	states["LaserSweep"].sweep_duration = lerpf(2.2, 1.6, rage)
	states["RocketVolley"].volleys = 2 if rage < 0.5 else 3
	states["GroundPound"].ring_speed = lerpf(900.0, 1150.0, rage)


func enter_defeated() -> void:
	rest_timer.stop()
	on_child_transition(current_state, "Defeated")


# The player lost: every attack stops and the mech stands idle. A morph under way still plays out,
# though the fight it leads into never starts.
func enter_player_defeated() -> void:
	rest_timer.stop()
	if current_state != states.get("Dormant") and current_state != states.get("Morph"):
		on_child_transition(current_state, "Idle")
	player_defeated = true
