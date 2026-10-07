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

const VsCard := preload("res://Scripts/VsCard.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")
# The Nugget Fastball's state, built here rather than in his scene (_add_state), so nothing an open editor saves can
# write over it.
const MasonPitch := preload("res://Scripts/States/Mason/MasonPitch.gd")
const PRE_FIGHT_DIALOGUE := "res://Dialogue/MasonPreFight.dialogue"
const POO_BOMB_SCENE := "res://Scenes/Bosses/PooBombScene.tscn"
const LINE_START_SCENE := "res://Scenes/Bosses/PooLineStartScene.tscn"
# Everything he sends out: bombs, nuggets, Carter, the driver and the line's ring.
const HAZARD_GROUP := "mason_hazard"

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
# its phase's list, wrapping around, so phase 1 takes turns between Carter and the nuggets. Phase 2 has
# the one, the shower with Carter called in under it (carter_in_shower). Every cycle's attack is followed
# by his pitches. An entry is a state's name or an alias (resolve_attack): "CarterRain" is Carter with
# the light rain (carter_rain), "Pitch" the Nugget Fastball (pitch_enabled), skipped while it is off.
const FINISHERS := [
	[["CarterRain", "Pitch"], ["NuggetShower", "Pitch"]],
	[["NuggetShower", "Pitch"]],
]

# Every number the fight is paced on is a knob, so it can be retuned without code edits. The
# per-phase ones are indexed by cycle_phase: [phase 1, phase 2].

# A line runs at the player's height and puts one bomb at their x. The offset keeps that bomb
# inside the blast reach of a player who stands still, while a short step clears it.
@export var aim_offset := 50.0
# The snake only touches the player's row at the aimed bomb and arches away from them elsewhere,
# so a player pinned against a wall can still sidestep along it. The arch is what decides how many
# rows one line covers: it reaches twice this off the aimed row, so a line is 2 * amp + 120 px of mat.
@export var wiggle_amp := 90.0
@export var wiggle_length := 467.0
# How close two bombs may sit. Below a blast's own radius (60) the line becomes one unbroken wall
# instead of beads, which is the point - but it must stay under the tightest bomb_spacing, or every
# other bomb of a line would be dropped as a stack. A line's spacing compresses by up to 10px where
# it turns onto the player's row, so it has to clear the tightest spacing by that much as well.
@export var stack_radius := 72.0
# However late a bomb is dropped, it sits on the mat at least this long before it goes off.
@export var min_fuse := 1.26
@export var bomb_spacing: Array[float] = [88.0, 82.0]
@export var waddle_speed: Array[float] = [980.0, 1120.0]
# The wait before a laid line starts going off, and the beat between one bomb and the next. The
# wait is what decides how much poo is on the mat at once: the longer it is, the more of the next
# line is down before this one clears. Long enough here that a line is still down while the next is
# being laid, so two lines cover the mat rather than one, and a bomb waits longer to go off, not less.
@export var fuse_delay: Array[float] = [1.17, 0.99]
@export var detonate_interval: Array[float] = [0.09, 0.07]
# Cut from [5, 4] for his pitches (the user's approval, 2026-10-04): a cycle keeps about the length it had.
@export var lines_per_cycle: Array[int] = [3, 3]
# How far along the line the start telegraph draws its path preview, so its direction reads while
# Mason is still squatting on the spot it begins at.
@export var line_preview_length := 700.0
@export var eat_window: Array[float] = [3.5, 2.55]
@export var elbow_drops: Array[int] = [6, 8]
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
# nugget_warning after that: the warning divided by that gap is how many are in the sky at once. With
# Carter called in under it, a marker whose nugget would land in one of his slams' clear time
# (slam_clear_before, slam_clear_after) is skipped, so fewer than nugget_count come down, and phase
# 2's shower runs as long as his drops do.
@export var nugget_count: Array[int] = [35, 132]
@export var nugget_shower_time: Array[float] = [3.2, 7.2]
@export var nugget_warning: Array[float] = [0.9, 0.8]
# How many open spots a nugget that isn't aimed at the player is picked from (MasonNuggetShower). The
# one taken lies furthest from this shower's other landings, so the more it has to pick from, the more
# evenly the rain spreads over the whole mat rather than bunching. 1 takes the first open spot.
@export var nugget_spread: Array[int] = [1, 8]
# Whether the shower calls Carter in while it rains (MasonNuggetShower), with the same phone call, badge
# and drops as his own attack (MasonCallCarter), the two making one finisher.
@export var carter_in_shower: Array[bool] = [false, true]
# From the heave to Mason picking up the phone, so the bucket's toss plays out and the first markers are
# down before the badge goes up.
@export var shower_call_after := 0.3
# Around each of Carter's slams under the shower, no nugget lands from this long before the slam to
# this long after its hitbox goes off. The rain is timed around him rather than aimed around him
# because every nugget that could land then is marked before he picks his spot: its warning is longer
# than his. The lead is a whole parry window, so from the earliest press that parries him until he is
# done, nothing new lands anywhere, whether the player stands in his marker to parry him or steps out
# of it at the last moment.
@export var slam_clear_before := 0.25
@export var slam_clear_after := 0.1
# The Nugget Fastball (MasonPitch): a FINISHERS entry "Pitch" runs it, after the cycle's attack. Off, the entry is
# skipped and the cycle is the one before it.
@export var pitch_enabled := true
# Phase one's Carter call comes with a light nugget rain (FINISHERS' "CarterRain": the shower with Carter called in
# under it, at these numbers), so walking loops no longer dodge it. Off, "CarterRain" is his plain call.
@export var carter_rain := true
@export var rain_count := 60
@export var rain_time := 7.0
@export var rain_warning := 0.9
@export var rain_spread := 8
@export var rain_target_every := 3
# An aimed nugget of the rain lands where the player is heading: their velocity, capped at RAIN_LEAD_CAP, times its
# warning and this.
@export var rain_lead := 1.0
# A player still standing in him as a cycle's first squat starts (eating ends with them punching him) isn't hit by
# the contact for this long; one walking into him is (MasonScript._touch_player).
@export var cycle_contact_grace := 0.45

# What a FINISHERS entry that isn't a state's own name runs, and with which variant (attack_variant).
const ATTACK_ALIASES := {"CarterRain": "NuggetShower"}
const RAIN_LEAD_CAP := 600.0

var cycle_phase := 0
var lines_done := 0
var cycles_started := 0
var finishers : Array = []
var player_defeated := false
# The pre-fight lines' balloon, which a held skip takes down, and whether those lines have handed
# over to the VS card yet.
var pre_fight_balloon: Node
var pre_fight_over := false
# Until this on his fight_clock, the contact's poll leaves a player already in him alone (cycle_contact_grace).
var contact_grace_until := -INF
# Which alias the attack being entered was run as ("CarterRain"), read and cleared by the attack's Enter().
var attack_variant := ""
# How many pitch sets have started this fight: the first one teaches (MasonPitch).
var pitch_sets_started := 0

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
	# Before the children are gathered, which takes it in with them.
	_add_state(MasonPitch.new(), "Pitch")
	for child in get_children():
		if child is State:
			states[child.name] = child

	rest_point = MasonCharacterBody.global_position + BOMB_SPAWN_OFFSET

	if initial_state:
		current_state = initial_state
		# Deferred until the scene is up: his entrance moves him, the player and the gates, and
		# reads all three off the fight scene.
		current_state.Enter.call_deferred()


# `body` is set before the state is ready, which needs it; the state finds this node as its parent itself.
func _add_state(state: State, state_name: String) -> void:
	state.name = state_name
	state.body = MasonCharacterBody
	add_child(state)


# His entrance opens the lines once it has walked him in and shut the ring behind him.
func show_pre_fight_dialogue() -> void:
	# One-shot: the outro's lines end a dialogue too, and must not start the fight again.
	DialogueManager.dialogue_ended.connect(_on_dialogue_ended, CONNECT_ONE_SHOT)
	pre_fight_balloon = DialogueManager.show_dialogue_balloon(load(PRE_FIGHT_DIALOGUE), "start")


# A held skip's way past the lines (BossEntrance), whether they were ever put up or not: the hand-over
# their own end makes, made from here instead. pre_fight_over keeps it to once.
func end_pre_fight_dialogue() -> void:
	if pre_fight_over:
		return
	if DialogueManager.dialogue_ended.is_connected(_on_dialogue_ended):
		DialogueManager.dialogue_ended.disconnect(_on_dialogue_ended)
	_on_dialogue_ended(null)


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
	pre_fight_over = true
	var intro = states.get("Intro")
	if intro:
		intro.lines_over()
	VsCard.play_intro(self, "mason", post_dialogue_pre_fight_timer.start)


func _on_post_dialogue_pre_fight_timer_timeout() -> void:
	MasonCharacterBody.start_music()
	start_cycle()


# The phase is locked in here and nowhere else, so hitting the phase-two
# threshold mid-cycle never reshapes the cycle already underway.
func start_cycle() -> void:
	cycle_phase = 1 if MasonCharacterBody.phase_two else 0
	lines_done = 0
	contact_grace_until = MasonCharacterBody.fight_clock + cycle_contact_grace
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
	# Its red tell only goes up for a player its blast has in it, so it needs to know where they are.
	bomb.player = get_player()
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


# Runs the cycle's next finisher, or the delivery once they're all done. An entry its knob has off is skipped.
func next_attack(state: State) -> void:
	# Checked before popping, so a late call from an attack that's already over can't skip the next one.
	if state != current_state:
		return
	while not finishers.is_empty():
		if run_attack(finishers.pop_front()):
			return
	on_child_transition(state, "AwaitDelivery")


# The state a FINISHERS entry runs, or "" when its knob has it off.
func resolve_attack(entry: String) -> String:
	match entry:
		"CarterRain":
			return ATTACK_ALIASES[entry] if carter_rain else "CallCarter"
		"Pitch":
			return entry if pitch_enabled else ""
	return entry


# Runs `entry` from whatever he is doing now; false when it is off. Tests run an attack this way too.
func run_attack(entry: String) -> bool:
	var state_name := resolve_attack(entry)
	if state_name.is_empty() or not states.has(state_name):
		return false
	attack_variant = entry if ATTACK_ALIASES.get(entry, "") == state_name else ""
	on_child_transition(current_state, state_name)
	return true


# The fight's floor layer (Arena/GroundFx, which the finisher's ground effects use too), or his scene
# root in a scene without one.
func ground_layer() -> Node2D:
	var arena: Node = MasonCharacterBody.get_parent().get_parent()
	var layer: Node2D = arena.get_node_or_null("GroundFx") if arena else null
	return layer if layer else MasonCharacterBody.get_parent()


# A full Break gauge (BossBreakGauge): whatever he was doing stops, everything he sent out goes, and
# he is Broken until he gets up and starts a new cycle.
func enter_broken() -> void:
	if MasonCharacterBody.defeated or MasonCharacterBody.boss_health <= 0 or player_defeated:
		return
	if current_state == states.get("Broken"):
		return
	_stop_everything()
	on_child_transition(current_state, "Broken")


# The finisher's uppercut ends the Break window instead of its own clock: he is up, and his next cycle
# starts `delay` after now.
func end_break(delay: float) -> void:
	on_child_transition(current_state, "Idle")
	# Held on the recoil frame through the stagger instead of the idle loop Idle starts.
	MasonCharacterBody.animation_player.play("hit")
	MasonCharacterBody.finisher_stagger_timer.start(maxf(delay, 0.01))


# The tiered finisher's first uppercut (MasonScript.begin_juggle).
func enter_juggled() -> void:
	var juggled = states["Juggled"]
	if MasonCharacterBody.defeated or current_state == juggled:
		return
	_stop_everything()
	on_child_transition(current_state, "Juggled")


# Down after a juggle, he picks himself up where he crashed and his next cycle starts `delay` after
# this.
func after_juggle(delay: float) -> void:
	on_child_transition(current_state, "Idle")
	MasonCharacterBody.finisher_stagger_timer.start(maxf(delay, 0.01))


# The one switch past the fight being decided: a juggled Mason, killed in the air, lands into his
# defeat rather than snapping to its pose mid-flight.
func land_juggled(final_state_name: String) -> void:
	var final_state = states.get(final_state_name)
	if final_state == states.get("Defeated"):
		final_state.lying = true
	current_state.Exit()
	final_state.Enter()
	current_state = final_state


func enter_defeated() -> void:
	_end_fight("Defeated")


# The player lost: he stops where he is and stands idle.
func enter_player_defeated() -> void:
	_end_fight("Idle")
	player_defeated = true


func _end_fight(final_state_name: String) -> void:
	_stop_everything()
	var juggled = states.get("Juggled")
	# In the air, he finishes his fall and his crash first (land_juggled).
	if juggled and current_state == juggled:
		juggled.final_state = final_state_name
		return
	on_child_transition(current_state, final_state_name)


# Everything of his that is still running. PooSquat's Exit() leaves its timers running and its
# squat_timer fires an unguarded drop_bomb(), so a Break taken out of the squat lays a bomb after he is
# already down unless the timers stop here.
func _stop_everything() -> void:
	states["Pitch"].release()
	ParryTell.clear(MasonCharacterBody)
	for timer in [post_dialogue_pre_fight_timer, squat_timer, release_timer, phone_timer, eat_timer]:
		timer.stop()
	# Not one of the five: it would otherwise start the next cycle out from under a Break taken during
	# the stagger after a finisher.
	MasonCharacterBody.finisher_stagger_timer.stop()
	# Anything he sent out that outlives what he was doing could still hurt the player.
	for hazard in get_tree().get_nodes_in_group(HAZARD_GROUP):
		hazard.queue_free()
