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

# Mason's walk limits: his whole sprite stays inside the ropes and below the back rope.
const LINE_X_LEFT := 260.0
const LINE_X_RIGHT := 1660.0
const WALK_Y_MIN := 206.0
const WALK_Y_MAX := 810.0
const BOMB_SPAWN_OFFSET := Vector2(0, 80)

# Bombs land past his walk limits so their blasts still reach the wall columns and the strip
# under the back rope, where his sprite can't go.
const BOMB_AREA := Rect2(170, 170, 1580, 720)
# A line runs at the player's height and puts one bomb at their x. The offset keeps that bomb
# inside the blast reach of a player who stands still, while a short step clears it.
const AIM_OFFSET := 50.0
# A bomb above this height is still hidden behind Mason's body if he stops beside it,
# so a line that high ends with him stepping down until it's in view. No bombs drop on that step.
const HIDDEN_BEHIND_Y := 260.0
const REVEAL_STEP := 215.0
# The snake only touches the player's row at the aimed bomb and arches away from them elsewhere,
# so a player pinned against a wall can still sidestep along it.
const WIGGLE_AMP := 60.0
const WIGGLE_LENGTH := 467.0
const WIGGLE_RAMP := 120.0
# Mason stops 90px short of the far wall column. Bombs within his sprite's reach of that spot
# (93px half-width + 39px bomb half-width) stay on the aimed row, where the reveal step or his
# feet keep them in view instead of arching behind him.
const WIGGLE_END_FLAT := 222.0
# Blast art radius (66) plus a bomb's half-width (39): any closer and a new bomb would sit in another's explosion,
# e.g. where a line starts on top of the previous line's end.
const STACK_RADIUS := 105.0
const MIN_FUSE := 1.4

# Per-phase tuning, indexed by cycle_phase: [phase 1, phase 2].
const BOMB_SPACING := [175.0, 150.0]
const WADDLE_SPEED := [440.0, 540.0]
const FUSE_DELAY := [0.7, 0.5]
const DETONATE_INTERVAL := [0.12, 0.09]
const LINES_PER_CYCLE := [2, 1]
const EAT_WINDOW := [3.5, 3.0]

# Index of the line_points segment that crosses the arena; the other segments are vertical.
const RUN_SEGMENT := 2

var cycle_phase := 0
var lines_done := 0

# Bomb-space path of the current line: start, turn onto the player's height, far wall column,
# and optionally the reveal step down. Mason walks it minus BOMB_SPAWN_OFFSET, clamped to his limits.
var rest_point := Vector2.ZERO
var line_points := PackedVector2Array()
var line_length := 0.0
var line_aim := Vector2.ZERO
var line_bend := 1.0
var bomb_marks : Array[float] = []
var next_mark := 0
var line_bombs : Array = []
var line_bomb_times : Array[float] = []
var spawned_bombs : Array = []


func _ready() -> void:
	DialogueManager.show_dialogue_balloon(load("res://Dialogue/MasonPreFight.dialogue"), "start")
	DialogueManager.dialogue_ended.connect(_on_dialogue_ended)

	for child in get_children():
		if child is State:
			states[child.name] = child

	rest_point = MasonCharacterBody.global_position + BOMB_SPAWN_OFFSET

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
	var start := rest_point
	var end_x := BOMB_AREA.end.x if start.x < 960 else BOMB_AREA.position.x
	line_aim = Vector2(end_x, start.y)
	line_bend = 1.0
	var player := get_player()
	if player:
		var target := player.global_position
		var aim_y := target.y + AIM_OFFSET
		if aim_y > BOMB_AREA.end.y:
			aim_y = target.y - AIM_OFFSET
			line_bend = -1.0
		line_aim = Vector2(
			clampf(target.x, minf(start.x, end_x), maxf(start.x, end_x)),
			clampf(aim_y, BOMB_AREA.position.y, BOMB_AREA.end.y)
		)

	line_points = PackedVector2Array([start, Vector2(start.x, line_aim.y), Vector2(end_x, line_aim.y)])
	if line_aim.y < HIDDEN_BEHIND_Y:
		line_points.append(Vector2(end_x, line_aim.y + REVEAL_STEP))
	rest_point = line_points[line_points.size() - 1]

	line_length = 0.0
	for i in range(1, line_points.size()):
		line_length += line_points[i - 1].distance_to(line_points[i])

	# Marks are spaced out from the aimed bomb so one always lands exactly at the player's x.
	var spacing: float = BOMB_SPACING[cycle_phase]
	var first_mark := fposmod(absf(line_aim.y - start.y) + absf(line_aim.x - start.x), spacing)
	var run_end := absf(line_aim.y - start.y) + absf(end_x - start.x)
	bomb_marks.clear()
	if first_mark > STACK_RADIUS:
		bomb_marks.append(0.0)
	var mark := first_mark
	while mark <= run_end:
		bomb_marks.append(mark)
		mark += spacing
	next_mark = 0
	line_bombs.clear()
	line_bomb_times.clear()


func line_position(distance: float) -> Vector2:
	var remaining := distance
	for i in range(1, line_points.size()):
		var from := line_points[i - 1]
		var to := line_points[i]
		var length := from.distance_to(to)
		if remaining > length and i < line_points.size() - 1:
			remaining -= length
			continue
		var point := to if length == 0.0 else from.lerp(to, clampf(remaining / length, 0.0, 1.0))
		if i == RUN_SEGMENT:
			var ramp := clampf(minf(absf(point.x - from.x), absf(to.x - point.x) - WIGGLE_END_FLAT) / WIGGLE_RAMP, 0.0, 1.0)
			point.y += line_bend * ramp * WIGGLE_AMP * (1.0 - cos(TAU * (point.x - line_aim.x) / WIGGLE_LENGTH))
		return point.clamp(BOMB_AREA.position, BOMB_AREA.end)
	return rest_point


func walk_position(distance: float) -> Vector2:
	var point := line_position(distance) - BOMB_SPAWN_OFFSET
	return Vector2(clampf(point.x, LINE_X_LEFT, LINE_X_RIGHT), clampf(point.y, WALK_Y_MIN, WALK_Y_MAX))


func drop_bombs_up_to(distance: float) -> void:
	while next_mark < bomb_marks.size() and bomb_marks[next_mark] <= distance:
		drop_bomb()


func drop_bomb() -> void:
	var drop_position := line_position(bomb_marks[next_mark])
	next_mark += 1
	for other in spawned_bombs:
		if is_instance_valid(other) and other.global_position.distance_to(drop_position) < STACK_RADIUS:
			return
	var bomb := spawn_hazard(POO_BOMB_SCENE, drop_position)
	line_bombs.append(bomb)
	line_bomb_times.append(MasonCharacterBody.fight_clock)
	spawned_bombs.append(bomb)


func bombs_cleared() -> bool:
	spawned_bombs = spawned_bombs.filter(func(bomb): return is_instance_valid(bomb))
	return spawned_bombs.is_empty()


func finish_line() -> void:
	for i in line_bombs.size():
		if is_instance_valid(line_bombs[i]):
			var waited: float = MasonCharacterBody.fight_clock - line_bomb_times[i]
			line_bombs[i].arm(maxf(FUSE_DELAY[cycle_phase] + i * DETONATE_INTERVAL[cycle_phase], MIN_FUSE - waited))
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
