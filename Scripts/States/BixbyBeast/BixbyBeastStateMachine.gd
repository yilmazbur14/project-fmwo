extends Node

@export var initial_state : State

@export var states : Dictionary = {}
@export var current_state : State
@export var BixbyBeastCharacterBody : CharacterBody2D

#TIMERS
@export var post_dialogue_pre_fight_timer: Timer
@export var recover_timer: Timer
@export var finisher_stagger_timer: Timer

const BixbyBeastArtLayout := preload("res://Scripts/BixbyBeastArtLayout.gd")
const FIRE_PATCH_SCENE := preload("res://Scenes/Bosses/BixbyFirePatchScene.tscn")
const FirePatch := preload("res://Scripts/BixbyFirePatchScript.gd")
const QUAKE_CRACK_SCENE := preload("res://Scenes/Bosses/BixbyQuakeCrackScene.tscn")
const QuakeCrack := preload("res://Scripts/BixbyQuakeCrackScript.gd")

const PRE_FIGHT_DIALOGUE := "res://Dialogue/LiamPreFight.dialogue"
const HAZARD_GROUP := "bixby_beast_hazard"
# The inside edges of the ropes, as Mason's Carter call-in measures them.
const ROPES := Rect2(113, 114, 1692, 853)
# Where the centre of the player's body can go, inside the arena walls.
const PLAYER_FLOOR := Rect2(117, 132, 1686, 816)
# Half the player's collision box, and the margin past it that fire has to leave for a way through to count.
const PLAYER_HALF_BODY := Vector2(12, 27)
const FIRE_PASSAGE_MARGIN := 6.0
# The grid the floor is checked on for places the fire would wall off.
const FLOOR_CELL := 16.0
# A quake wave runs along the line between him and the crack it comes out of. Off a crack planted against a
# rope, that way is a few steps of floor, so it runs the other way along the same line instead.
const QUAKE_MIN_TRAVEL := 500.0

# The fight's loop: hover and strafe, run the cycle's attacks with a short hover between them, land for
# the punishable recovery, take off, repeat. Cycles take turns through this list: fire breath, the combined
# attack, a double breath, the combined attack again. A new attack is a state that calls attack_finished()
# when it's done, listed here. The combined attack ends on a punish window of its own and takes off from
# it, so it is always the last attack of its cycle and that cycle has no landing recovery.
const ATTACK_CYCLES := [["FireBreath"], ["Combined"], ["FireBreath", "FireBreath"], ["Combined"]]

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
@export var recover_time := 3.5
# How long he takes to rise to hover height, from the takeoff's rising frame.
@export var takeoff_rise_time := 0.3
# The combined attack: he lands and braces this long, then pounds this many cracks into the floor this far
# apart, one under the player each time.
@export var combined_windup := 0.5
@export var combined_pounds := 3
@export var combined_pound_interval := 0.35
# How long the first pound's crack glows before it erupts, and how fast its wave then travels out. The
# eruption comes up out of the floor with no travel at all, so the throbbing crack is the whole of the
# warning anyone standing on one gets: it has to stay well clear of PlayerDefense.parry_window, and the
# defence suite's approach mode holds it to that.
@export var quake_warning := 1.2
@export var quake_speed := 700.0
# Every crack after it burns this much longer than the one before, so the three go off further apart than
# the player's invincibility lasts: together they were one hit, spread out they are three to keep clear of.
@export var quake_stagger := 0.85
# The scream: one full turn of the drawn spin, which is a third of a turn every 0.3s. Kept to whole turns,
# since the wobble he stops on is drawn to follow the last frame of the loop. He wobbles dizzy for this
# long afterwards.
@export var combined_spin_time := 1.2
@export var combined_dizzy_time := 2.0
# The fire trail the full stream leaves on the floor: patches that block the player but don't hurt. How
# long each burns between catching and burning out, whose timing is drawn.
@export var fire_trail_time := 6.0
@export var fire_trail_spacing := 96.0
@export var max_fire_patches := 14
@export var max_trail_patches := 6
# When he lands, fire this close to where he'll be punched burns out.
@export var fire_landing_clearance := 220.0

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


# The transformation leaves him standing after his roar: the fight starts with his takeoff.
func _on_post_dialogue_pre_fight_timer_timeout() -> void:
	BixbyBeastCharacterBody.start_music()
	on_child_transition(current_state, "Takeoff")


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


# His punish windows: the recovery he lands in, and the dizzy spell the combined attack ends on.
func is_recovering() -> bool:
	if current_state == states.get("Recover"):
		return true
	return current_state == states.get("Combined") and current_state.is_dizzy()


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


#FIRE TRAIL

# Sets a patch of floor burning at `centre`, slot `trail_slot` of its trail, unless it's outside the ropes,
# too much fire is already burning, or the patch would wall off part of the floor. Returns whether it was laid.
func lay_fire_patch(centre: Vector2, trail_slot := 0) -> bool:
	if not ROPES.has_point(centre):
		return false
	var active := fire_patches(false)
	if active.size() >= max_fire_patches:
		return false
	var footprint := Rect2(centre.round() - FirePatch.SIZE / 2.0, FirePatch.SIZE)
	var footprints: Array = active.map(func(patch: Node) -> Rect2: return patch.footprint())
	footprints.append(footprint)
	if not _floor_stays_connected(footprints):
		return false

	var patch := FIRE_PATCH_SCENE.instantiate()
	patch.position = centre.round()
	patch.burn_time = fire_trail_time
	patch.trail_slot = trail_slot
	patch.player = get_player()
	patch.may_turn_solid = _fire_patch_may_turn_solid
	get_tree().current_scene.add_child(patch)
	return true


# Patches that are burning or about to, or only those already solid.
func fire_patches(solid_only: bool) -> Array:
	return get_tree().get_nodes_in_group(HAZARD_GROUP).filter(func(hazard: Node) -> bool:
		return hazard is FirePatch and (hazard.solid if solid_only else hazard.is_active()))


# The last word before a patch turns solid, counting only the fire that's solid already. Patches still
# waiting for the player to step off them are open floor here, so solid fire can never close in around
# the player standing in one.
func _fire_patch_may_turn_solid(patch: Node) -> bool:
	var footprints: Array = fire_patches(true).map(func(other: Node) -> Rect2: return other.footprint())
	footprints.append(patch.footprint())
	return _floor_stays_connected(footprints)


# Whether every spot on the floor the player could stand on can still reach every other one around these
# fire footprints. Fire can close down space, but never wall any of it off.
func _floor_stays_connected(footprints: Array) -> bool:
	var columns := int(PLAYER_FLOOR.size.x / FLOOR_CELL) + 1
	var rows := int(PLAYER_FLOOR.size.y / FLOOR_CELL) + 1
	var cells := PackedByteArray()
	cells.resize(columns * rows)
	var reach := PLAYER_HALF_BODY + Vector2.ONE * FIRE_PASSAGE_MARGIN
	for footprint in footprints:
		var blocked: Rect2 = footprint.grow_individual(reach.x, reach.y, reach.x, reach.y)
		var first := ((blocked.position - PLAYER_FLOOR.position) / FLOOR_CELL).ceil()
		var last := ((blocked.end - PLAYER_FLOOR.position) / FLOOR_CELL).floor()
		for row in range(maxi(int(first.y), 0), mini(int(last.y), rows - 1) + 1):
			for column in range(maxi(int(first.x), 0), mini(int(last.x), columns - 1) + 1):
				cells[row * columns + column] = 1

	var start := cells.find(0)
	if start < 0:
		return false
	var open_cells := cells.count(0)
	var queue := PackedInt32Array([start])
	cells[start] = 2
	var head := 0
	while head < queue.size():
		var cell := queue[head]
		head += 1
		var column := cell % columns
		if cell >= columns and cells[cell - columns] == 0:
			cells[cell - columns] = 2
			queue.append(cell - columns)
		if cell + columns < cells.size() and cells[cell + columns] == 0:
			cells[cell + columns] = 2
			queue.append(cell + columns)
		if column > 0 and cells[cell - 1] == 0:
			cells[cell - 1] = 2
			queue.append(cell - 1)
		if column < columns - 1 and cells[cell + 1] == 0:
			cells[cell + 1] = 2
			queue.append(cell + 1)
	return queue.size() == open_cells


# The punish window has to be reachable: as he comes down, fire near where he'll land, or in the way
# between the player and there, burns out.
func clear_fire_for_landing(landing_point: Vector2) -> void:
	var body_box := BixbyBeastArtLayout.local_rect(BixbyBeastArtLayout.RECOVER_BODY_BOX)
	var landed := Rect2(landing_point + body_box.position, body_box.size)
	var near := landed.grow(fire_landing_clearance)
	var player := get_player()
	for patch in fire_patches(false):
		var footprint: Rect2 = patch.footprint()
		if footprint.intersects(near) or (player and _fire_in_the_way(footprint, player.global_position, landed)):
			patch.burn_out()


# Whether fire stands anywhere on the straight way from `from` to the nearest point of `target`, for the
# player's body walking it.
func _fire_in_the_way(footprint: Rect2, from: Vector2, target: Rect2) -> bool:
	var reach := PLAYER_HALF_BODY + Vector2.ONE * FIRE_PASSAGE_MARGIN
	var blocked := footprint.grow_individual(reach.x, reach.y, reach.x, reach.y)
	var to := from.clamp(target.position, target.end)
	var steps := ceili(from.distance_to(to) / FLOOR_CELL) + 1
	for i in steps + 1:
		if blocked.has_point(from.lerp(to, float(i) / steps)):
			return true
	return false


#COMBINED ATTACK

# Sets a crack glowing where a pound landed, pointing the way its wave travels when it erupts. Kept inside
# the ropes, so a pound aimed at a player against one still cracks floor. `order` is which pound planted
# it, which is what holds its eruption back behind the one before.
func plant_quake_crack(at: Vector2, from: Vector2, order := 0) -> void:
	var point := at.clamp(ROPES.position, ROPES.end)
	var direction := Vector2.DOWN if point.is_equal_approx(from) else (point - from).normalized()
	if _wave_room(point, direction) < QUAKE_MIN_TRAVEL:
		direction = -direction
	var crack := QUAKE_CRACK_SCENE.instantiate()
	crack.position = point.round()
	crack.warning_time = quake_warning + order * quake_stagger
	crack.speed = quake_speed
	crack.direction = direction
	get_tree().current_scene.add_child(crack)


# How far a wave out of `point` runs that way before it is off the floor.
func _wave_room(point: Vector2, direction: Vector2) -> float:
	var floor_area: Rect2 = QuakeCrack.WAVE_AREA
	var room := INF
	if absf(direction.x) > 0.001:
		room = minf(room, ((floor_area.end.x if direction.x > 0.0 else floor_area.position.x) - point.x) / direction.x)
	if absf(direction.y) > 0.001:
		room = minf(room, ((floor_area.end.y if direction.y > 0.0 else floor_area.position.y) - point.y) / direction.y)
	return room


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
