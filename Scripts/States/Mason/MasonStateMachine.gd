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
const LINE_START_SCENE := "res://Scenes/Bosses/PooLineStartScene.tscn"

# Mason's walk limits: his whole sprite stays inside the ropes and below the back rope.
const LINE_X_LEFT := 260.0
const LINE_X_RIGHT := 1660.0
const WALK_Y_MIN := 206.0
const WALK_Y_MAX := 810.0
const BOMB_SPAWN_OFFSET := Vector2(0, 80)
# Mason's drawn sprite around his origin.
const MASON_SPRITE := Rect2(-93, -93, 186, 189)

# Bombs land past his walk limits so their blasts still reach the wall columns and the strip
# under the back rope, where his sprite can't go.
const BOMB_AREA := Rect2(170, 170, 1580, 720)
# A bomb above this height is still hidden behind Mason's body if he stops beside it,
# so a line that high ends with him stepping down until it's in view. No bombs drop on that step.
const HIDDEN_BEHIND_Y := 260.0
const REVEAL_STEP := 215.0
# Mason stops 90px short of the far wall column. Bombs within his sprite's reach of that spot
# (93px half-width + 39px bomb half-width) stay on the aimed row, where the reveal step or his
# feet keep them in view instead of arching behind him.
const WIGGLE_END_FLAT := 222.0
const WIGGLE_RAMP := 120.0

# Index of the line_points segment that crosses the arena; the other segments are vertical.
const RUN_SEGMENT := 2

# The attacks run after a cycle's bomb lines, before the delivery. Each cycle takes the next entry of
# its phase's list, wrapping around, so phase 1 takes turns between Carter and the nuggets.
const FINISHERS := [
	[["CallCarter"], ["NuggetShower"]],
	[["NuggetShower", "CallCarter"]],
]

# Every number the fight is paced on is a knob, so it can be retuned without code edits. The
# per-phase ones are indexed by cycle_phase: [phase 1, phase 2].

# A line runs at the player's height and puts one bomb at their x. The offset keeps that bomb
# inside the blast reach of a player who stands still, while a short step clears it.
@export var aim_offset := 50.0
# The snake only touches the player's row at the aimed bomb and arches away from them elsewhere,
# so a player pinned against a wall can still sidestep along it.
@export var wiggle_amp := 60.0
@export var wiggle_length := 467.0
# How close two bombs may sit. Below a blast's own radius (60) the line becomes one unbroken wall
# instead of beads, which is the point - but it must stay under the tightest bomb_spacing, or every
# other bomb of a line would be dropped as a stack.
@export var stack_radius := 80.0
# However late a bomb is dropped, it sits on the mat at least this long before it goes off.
@export var min_fuse := 1.4
@export var bomb_spacing: Array[float] = [100.0, 88.0]
@export var waddle_speed: Array[float] = [820.0, 960.0]
# The wait before a laid line starts going off, and the beat between one bomb and the next. The
# wait is what decides how much poo is on the mat at once: the longer it is, the more of the next
# line is down before this one clears.
@export var fuse_delay: Array[float] = [0.8, 0.65]
@export var detonate_interval: Array[float] = [0.09, 0.07]
@export var lines_per_cycle: Array[int] = [5, 3]
# How far along the line the start telegraph draws its path preview, so its direction reads while
# Mason is still squatting on the spot it begins at.
@export var line_preview_length := 700.0
@export var eat_window: Array[float] = [3.5, 3.0]
@export var elbow_drops: Array[int] = [5, 8]
@export var elbow_telegraph: Array[float] = [0.32, 0.26]
@export var elbow_dive: Array[float] = [0.2, 0.17]
@export var elbow_sit_up: Array[float] = [0.07, 0.05]
@export var elbow_leap_out: Array[float] = [0.22, 0.18]
@export var elbow_gap: Array[float] = [0.12, 0.08]
# Grows the elbow drop's marker art, its dust and its oval hit area together, so the hit stays
# exactly what the marker showed. 5/3: the art is drawn at 3x, so this lands it on a whole 5x and
# its pixels stay square.
@export var elbow_hit_scale := 5.0 / 3.0
# A nugget marker goes down every nugget_shower_time / nugget_count seconds, and its nugget lands
# nugget_warning after that: the warning divided by that gap is how many are in the sky at once.
@export var nugget_count: Array[int] = [28, 40]
@export var nugget_shower_time: Array[float] = [3.2, 3.6]
@export var nugget_warning: Array[float] = [0.9, 0.8]

var cycle_phase := 0
var lines_done := 0
var cycles_started := 0
var finishers : Array = []
var player_defeated := false

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
# The ring on the spot the current line begins at; it frees itself once that line's first bomb,
# which is also the first to go off, has cleared the spot again.
var line_start: Node2D = null


func _ready() -> void:
	DialogueManager.show_dialogue_balloon(load("res://Dialogue/MasonPreFight.dialogue"), "start")
	# One-shot: the outro's lines end a dialogue too, and must not start the fight again.
	DialogueManager.dialogue_ended.connect(_on_dialogue_ended, CONNECT_ONE_SHOT)

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

	# Defeat, Mason's or the player's, is terminal: a late timer or hazard signal must never restart
	# the fight.
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
	MasonCharacterBody.start_music()
	start_cycle()


# The phase is locked in here and nowhere else, so hitting the phase-two
# threshold mid-cycle never reshapes the cycle already underway.
func start_cycle() -> void:
	cycle_phase = 1 if MasonCharacterBody.phase_two else 0
	lines_done = 0
	var turns: Array = FINISHERS[cycle_phase]
	finishers = turns[cycles_started % turns.size()].duplicate()
	cycles_started += 1
	on_child_transition(current_state, "PooSquat")


func get_player() -> Node2D:
	return get_tree().current_scene.get_node_or_null("Arena/MainPlayer/CharacterBody2D")


func spawn_hazard(scene_path: String, spawn_position: Vector2) -> Node2D:
	var hazard: Node2D = load(scene_path).instantiate()
	get_tree().current_scene.add_child(hazard)
	hazard.global_position = spawn_position
	return hazard


# The spots where something covering `footprint` around itself would overlap Mason's sprite.
func keep_out_around_mason(footprint: Rect2) -> Rect2:
	return Rect2(MasonCharacterBody.global_position + MASON_SPRITE.position - footprint.end, MASON_SPRITE.size + footprint.size)


func begin_line() -> void:
	var start := rest_point
	var end_x := BOMB_AREA.end.x if start.x < 960 else BOMB_AREA.position.x
	line_aim = Vector2(end_x, start.y)
	line_bend = 1.0
	var player := get_player()
	if player:
		var target := player.global_position
		var aim_y := target.y + aim_offset
		if aim_y > BOMB_AREA.end.y:
			aim_y = target.y - aim_offset
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
	var spacing: float = bomb_spacing[cycle_phase]
	var first_mark := fposmod(absf(line_aim.y - start.y) + absf(line_aim.x - start.x), spacing)
	var run_end := absf(line_aim.y - start.y) + absf(end_x - start.x)
	bomb_marks.clear()
	if first_mark > stack_radius:
		bomb_marks.append(0.0)
	var mark := first_mark
	while mark <= run_end:
		bomb_marks.append(mark)
		mark += spacing
	next_mark = 0
	line_bombs.clear()
	line_bomb_times.clear()
	_show_line_start(start)


# The ring on the spot the line begins at, with a preview of the path leading out of it, up while
# Mason squats there and all through his walk: the first bomb of the line is also the first to go
# off, so this spot is the one the player can read ahead and run to.
func _show_line_start(start: Vector2) -> void:
	# The ring of the line before this one is already counting its own spot down to its blast, and
	# fades itself out after it, so it is left alone here.
	if is_instance_valid(line_start) and not line_start.holding:
		line_start.queue_free()
	var preview := PackedVector2Array()
	var step := maxf(20.0, line_preview_length / 24.0)
	var along := 0.0
	while along < minf(line_preview_length, line_length):
		preview.append(line_position(along))
		along += step
	preview.append(line_position(minf(line_preview_length, line_length)))
	line_start = spawn_hazard(LINE_START_SCENE, start)
	line_start.show_path(preview)


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
			point.y += line_bend * ramp * wiggle_amp * (1.0 - cos(TAU * (point.x - line_aim.x) / wiggle_length))
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
		if is_instance_valid(other) and other.global_position.distance_to(drop_position) < stack_radius:
			return
	var first := line_bombs.is_empty()
	var bomb := spawn_hazard(POO_BOMB_SCENE, drop_position)
	line_bombs.append(bomb)
	line_bomb_times.append(MasonCharacterBody.fight_clock)
	spawned_bombs.append(bomb)
	if first and is_instance_valid(line_start):
		line_start.flash()


func bombs_cleared() -> bool:
	spawned_bombs = spawned_bombs.filter(func(bomb): return is_instance_valid(bomb))
	return spawned_bombs.is_empty()


func finish_line() -> void:
	var first_fuse := 0.0
	for i in line_bombs.size():
		if is_instance_valid(line_bombs[i]):
			var waited: float = MasonCharacterBody.fight_clock - line_bomb_times[i]
			var fuse := maxf(fuse_delay[cycle_phase] + i * detonate_interval[cycle_phase], min_fuse - waited)
			line_bombs[i].arm(fuse)
			if i == 0:
				first_fuse = fuse
	lines_done += 1
	# The ring stays up until the bomb on that spot has gone off and cleared it.
	if is_instance_valid(line_start):
		line_start.hold_for(first_fuse)

	var waddle = states.get("Waddle")
	if lines_done < lines_per_cycle[cycle_phase]:
		on_child_transition(waddle, "PooSquat")
	else:
		next_attack(waddle)


# Runs the cycle's next finisher, or the delivery once they're all done.
func next_attack(state: State) -> void:
	# Checked before popping, so a late call from an attack that's already over can't skip the next one.
	if state != current_state:
		return
	on_child_transition(state, "AwaitDelivery" if finishers.is_empty() else finishers.pop_front())


func enter_defeated() -> void:
	_end_fight("Defeated")


# The player lost: he stops where he is and stands idle.
func enter_player_defeated() -> void:
	_end_fight("Idle")
	player_defeated = true


func _end_fight(final_state_name: String) -> void:
	for timer in [post_dialogue_pre_fight_timer, squat_timer, release_timer, phone_timer, eat_timer]:
		timer.stop()
	on_child_transition(current_state, final_state_name)
