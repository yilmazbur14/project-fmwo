extends Node

@export var initial_state : State

@export var states : Dictionary = {}
@export var current_state : State
@export var MasonCharacterBody : CharacterBody2D

#TIMERS
@export var post_dialogue_pre_fight_timer: Timer
@export var squat_timer: Timer
@export var release_timer: Timer
@export var phone_timer: Timer
@export var eat_timer: Timer

const POO_BOMB_SCENE := "res://Scenes/Bosses/PooBombScene.tscn"

const HOME_Y := 280.0
const LINE_X_LEFT := 260.0
const LINE_X_RIGHT := 1660.0
const BOMB_SPAWN_OFFSET := Vector2(0, 80)
const DIP_MIN := 150.0
const DIP_MAX := 520.0
const WIGGLE_AMP := 60.0
const WIGGLE_COUNT := 3

# Per-phase tuning, indexed by cycle_phase: [phase 1, phase 2].
const BOMBS_PER_LINE := [9, 11]
const LINE_DURATION := [3.2, 2.6]
const FUSE_DELAY := [0.7, 0.5]
const DETONATE_INTERVAL := [0.12, 0.09]
const LINES_PER_CYCLE := [2, 1]
const EAT_WINDOW := [3.5, 3.0]

var cycle_phase := 0
var lines_done := 0

var line_start_x := 0.0
var line_end_x := 0.0
var line_dip := 0.0
var line_bombs : Array = []
var spawned_bombs : Array = []


func _ready() -> void:
	DialogueManager.show_dialogue_balloon(load("res://Dialogue/MasonPreFight.dialogue"), "start")
	DialogueManager.dialogue_ended.connect(_on_dialogue_ended)

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

	# Defeated is terminal: a late timer or hazard signal must never restart the fight.
	if current_state == states.get("Defeated"):
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
	MasonCharacterBody.start_music()
	start_cycle()


# The phase is locked in here and nowhere else, so hitting the phase-two
# threshold mid-cycle never reshapes the cycle already underway.
func start_cycle() -> void:
	cycle_phase = 1 if MasonCharacterBody.phase_two else 0
	lines_done = 0
	on_child_transition(current_state, "PooSquat")


func get_player() -> Node2D:
	return get_tree().current_scene.get_node_or_null("Arena/MainPlayer/CharacterBody2D")


func spawn_hazard(scene_path: String, spawn_position: Vector2) -> Node2D:
	var hazard: Node2D = load(scene_path).instantiate()
	get_tree().current_scene.add_child(hazard)
	hazard.global_position = spawn_position
	return hazard


func begin_line() -> void:
	line_start_x = MasonCharacterBody.global_position.x
	line_end_x = LINE_X_RIGHT if line_start_x < 960 else LINE_X_LEFT
	line_dip = DIP_MIN
	var player := get_player()
	if player:
		line_dip = clampf(player.global_position.y - HOME_Y, DIP_MIN, DIP_MAX)
	line_bombs.clear()


func line_point(t: float) -> Vector2:
	return Vector2(
		lerpf(line_start_x, line_end_x, t),
		HOME_Y + line_dip * sin(PI * t) + WIGGLE_AMP * sin(TAU * WIGGLE_COUNT * t)
	)


func drop_bomb() -> void:
	var bomb := spawn_hazard(POO_BOMB_SCENE, MasonCharacterBody.global_position + BOMB_SPAWN_OFFSET)
	line_bombs.append(bomb)
	spawned_bombs.append(bomb)


func bombs_cleared() -> bool:
	spawned_bombs = spawned_bombs.filter(func(bomb): return is_instance_valid(bomb))
	return spawned_bombs.is_empty()


func finish_line() -> void:
	for i in line_bombs.size():
		if is_instance_valid(line_bombs[i]):
			line_bombs[i].arm(FUSE_DELAY[cycle_phase] + i * DETONATE_INTERVAL[cycle_phase])
	lines_done += 1

	var waddle = states.get("Waddle")
	if lines_done < LINES_PER_CYCLE[cycle_phase]:
		on_child_transition(waddle, "PooSquat")
	elif cycle_phase == 1:
		on_child_transition(waddle, "CallCarter")
	else:
		on_child_transition(waddle, "AwaitDelivery")


func enter_defeated() -> void:
	for timer in [post_dialogue_pre_fight_timer, squat_timer, release_timer, phone_timer, eat_timer]:
		timer.stop()
	on_child_transition(current_state, "Defeated")
