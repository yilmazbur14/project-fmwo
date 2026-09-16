extends Node

@export var initial_state : State

@export var states : Dictionary = {}
@export var current_state : State
@export var loops_done = 0
@export var max_loops = 2 #quakes per set, was 3
@export var total_earthquake_loops = 0
@export var max_total_loops := 3 #sets before Downed, was 5

#TIMERS
@export var post_dialogue_pre_fight_timer: Timer
@export var pause_between_earthquakes_timer: Timer
@export var downed_state_timer: Timer
@export var recovery_timer: Timer
@export var whirlwind_duration_timer: Timer

var eric_original_position : Vector2
var back_to_original_position : bool = false
var current_cycle_name = "Earthquake"
@export var whirlwind_hitbox : Area2D


# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	DialogueManager.show_dialogue_balloon(load("res://Dialogue/EricPreFight.dialogue"), "start")
	DialogueManager.dialogue_ended.connect(_on_dialogue_ended)

	whirlwind_hitbox.monitoring = false
	whirlwind_hitbox.monitorable = false

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
		# print("State Machine update") working
		current_state.Update(delta)

func _physics_process(delta: float) -> void:
	if current_state:
		current_state.Physics_Update(delta)

func on_child_transition(state, new_state_name):
	# print("state: ", state, " new_state_name: ", new_state_name)working
	if state != current_state:
		return

	var new_state = states.get(new_state_name)
	# print("new state: ", new_state)
	if !new_state:
		return

	if current_state:
		current_state.Exit()

	new_state.Enter()
	current_state = new_state

func _on_dialogue_ended(dialogue: Object) -> void:
	print("post dialogue timer started: ", post_dialogue_pre_fight_timer)
	post_dialogue_pre_fight_timer.start()


func _on_animation_player_animation_finished(anim_name: StringName) -> void:
	if anim_name == "earthquake":
		loop_earthquake_cycle()
		return



func _on_pause_between_earthquakes_timer_timeout() -> void:
	loop_earthquake_cycle()

func _on_post_dialogue_pre_fight_timer_timeout() -> void:
	print("post dialogue timer done")
	on_child_transition(current_state, "Earthquake")
	loops_done += 1
	var boss = get_parent()
	if boss and boss.has_method("start_music"):
		boss.start_music()
	# get_parent().on_child_transition(self, "Earthquake")
	# loop_earthquake_cycle()


func _play_downed_stinger() -> void:
	var boss = get_parent()
	if boss:
		var sfx = boss.get_node_or_null("DownedSfxPlayer")
		if sfx:
			sfx.play()

func loop_earthquake_cycle():
	print("Looping earthquake cycle. Loops done: ", loops_done, " Total earthquake loops: ", total_earthquake_loops)
	if total_earthquake_loops >= max_total_loops:
		pause_between_earthquakes_timer.stop()
		print("timer started: ", downed_state_timer)
		downed_state_timer.start()
		on_child_transition(current_state, "Downed")
		_play_downed_stinger()
		total_earthquake_loops = 0
		return

	if loops_done >= max_loops:
		loops_done = 0
		total_earthquake_loops += 1
		on_child_transition(current_state, "Idle")
		pause_between_earthquakes_timer.start()
	else:
		pause_between_earthquakes_timer.stop()
		on_child_transition(current_state, "Earthquake")
		loops_done += 1



func _on_downed_timer_timeout() -> void:
	on_child_transition(current_state, "Idle")
	downed_state_timer.stop()
	recovery_timer.start()


func _on_recovery_timer_timeout() -> void:
	recovery_timer.stop()
	if current_cycle_name == "Earthquake":
		on_child_transition(current_state, "Whirlwind")
		eric_original_position = get_parent().global_position
		whirlwind_hitbox.monitoring = true
		whirlwind_hitbox.monitorable = true
		whirlwind_duration_timer.start()
		current_cycle_name = "Whirlwind"
	elif current_cycle_name == "Whirlwind":
		on_child_transition(current_state, "Earthquake")
		loops_done = 1  # Start counting this earthquake cycle
		current_cycle_name = "Earthquake"


# func _on_whirlwind_duration_timeout() -> void:
# 	whirlwind_duration_timer.stop()
# 	back_to_original_position = true
# 	on_child_transition(current_state, "Downed")
# 	downed_state_timer.start()

func whirlwind_finished():
	whirlwind_duration_timer.stop()
	whirlwind_hitbox.monitoring = false
	whirlwind_hitbox.monitorable = false
	# back_to_original_position = true
	on_child_transition(current_state, "Downed")
	downed_state_timer.start()
	_play_downed_stinger()


# func _on_whirlwind_area_2d_area_entered(area: Area2D) -> void:
# 	pass # Replace with function body.
