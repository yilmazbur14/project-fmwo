extends Node

@export var initial_state : State

@export var states : Dictionary = {}
@export var current_state : State
@export var BixbyBeastCharacterBody : CharacterBody2D

#TIMERS
@export var post_dialogue_pre_fight_timer: Timer
@export var recover_timer: Timer
@export var finisher_stagger_timer: Timer

const VsCard := preload("res://Scripts/VsCard.gd")
const BixbyBeastArtLayout := preload("res://Scripts/BixbyBeastArtLayout.gd")
const FIRE_PATCH_SCENE := preload("res://Scenes/Bosses/BixbyFirePatchScene.tscn")
const FirePatch := preload("res://Scripts/BixbyFirePatchScript.gd")
const QUAKE_RING_SCENE := preload("res://Scenes/Bosses/BixbyQuakeRingScene.tscn")
const Ember := preload("res://Scripts/BixbyEmberScript.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")
const BixbyBeastBroken := preload("res://Scripts/States/BixbyBeast/BixbyBeastBroken.gd")
const BixbyBeastJuggled := preload("res://Scripts/States/BixbyBeast/BixbyBeastJuggled.gd")

const PRE_FIGHT_DIALOGUE := "res://Dialogue/LiamPreFight.dialogue"
const HAZARD_GROUP := "bixby_beast_hazard"
# The inside edges of the ropes, as Mason's Carter call-in measures them.
const ROPES := Rect2(113, 114, 1692, 853)
# Where the centre of the player's body can go, inside the arena walls: ArenaScene's wall boxes reach
# in to 105, 105, 1815 and 975, inset by PLAYER_HALF_BODY on each edge.
const PLAYER_FLOOR := Rect2(123, 145.5, 1674, 789)
# Half the player's collision box, and the margin past it that fire has to leave for a way through to count.
# The margin is a gap, not a proportion, so it stays where it is when his body grows.
const PLAYER_HALF_BODY := Vector2(18, 40.5)
const FIRE_PASSAGE_MARGIN := 6.0
# The grid the floor is checked on for places the fire would wall off.
const FLOOR_CELL := 16.0

# The fight's loop: hover and strafe, run the cycle's attacks with a short hover between them, land for
# the punishable recovery, take off, repeat. Cycles take turns through this list: fire breath, the combined
# attack, a double breath, the combined attack again. A new attack is a state that calls attack_finished()
# when it's done, listed here. The combined attack ends on a punish window of its own and takes off from
# it, so it is always the last attack of its cycle and that cycle has no landing recovery.
const ATTACK_CYCLES := [["FireBreath"], ["Combined"], ["FireBreath", "FireBreath"], ["Combined"]]
# From the first cycle he starts at or under inferno_health_gate, he is enraged: the Inferno comes at once,
# then these take turns from the top. It hands its own clearance and recharge to the landing straight after
# it, so it always has a cycle to itself.
const ENRAGED_CYCLES := [["Inferno"], ["FireBreath"], ["Combined"], ["FireBreath", "FireBreath"]]

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
# The combined attack: he lands and braces this long, then pounds this many times this far apart.
@export var combined_windup := 0.5
@export var combined_pounds := 3
@export var combined_pound_interval := 0.35
# The scream: at least this long, then on until his heads come round to a frame the wobble he stops on is
# drawn to follow, which is at most one more loop (BixbyBeastArtLayout.SPIN_LOOP, a third of a turn). He
# wobbles dizzy for this long afterwards.
@export var combined_spin_time := 6.0
@export var combined_dizzy_time := 2.0
# Every pound sends a quake ring rolling out from under him (BixbyQuakeRingScript), its radius growing this
# fast, and while he spins another follows every interval. Slow enough that the pounds' rings are still
# rolling out while he spins, and far enough apart on the floor to stand between. The three a pound sends
# come 0.35 s apart, too close to stand between, so this is also what keeps them one dash thick.
@export var quake_ring_speed := 200.0
@export var combined_spin_ring_interval := 2.0
# The fire trail the full stream leaves on the floor: patches that block the player but don't hurt. How
# long each burns between catching and burning out, whose timing is drawn.
@export var fire_trail_time := 6.0
@export var fire_trail_spacing := 96.0
@export var max_fire_patches := 14
@export var max_trail_patches := 6
# When he lands, fire this close to where he'll be punched burns out.
@export var fire_landing_clearance := 220.0
# THE INFERNO (BixbyBeastInferno). The first cycle he starts at or under this share of his health runs it,
# and his enraged rotation after that. 1.0 has it from the start.
@export var inferno_health_gate := 0.6
# He flies to the top rope this fast, perching when he gets there or after this long at most.
@export var inferno_perch_speed := 1300.0
@export var inferno_perch_time := 1.8
# The volley: this many fireballs spat up over this long, rising this fast, each up to this many degrees
# off straight up. Then a beat with the sky empty.
@export var inferno_fireballs := 24
@export var inferno_volley_time := 1.2
@export var inferno_rise_speed := 1600.0
@export var inferno_rise_spread_degrees := 15.0
@export var inferno_sky_beat := 0.35
# The shower tracks the player: the first marker this long into the inhale and one more every interval,
# each on the player's feet as it appears, up to the scatter off them at random, and lit for the warning
# before its fireball lands there. Markers may overlap: a player who stops can't sit in a gap between them.
@export var inferno_first_marker := 0.3
@export var inferno_marker_interval := 0.14
@export var inferno_fireball_warning := 1.0
@export var inferno_track_scatter := 40.0
# The pull, from the inhale until the last fireball lands: this many px/s toward the floor under him,
# reached over the ramp, and fading out inside the dead zone so nobody jitters at rest.
@export var inferno_pull_speed := 330.0
@export var inferno_pull_ramp := 0.4
@export var inferno_pull_dead_zone := 90.0
# The breath is one cone straight down from his mouth, this many degrees either side of straight down: 65
# covers about 72% of the ring with the cone's tip 45 px under the rope, leaving the two upper corners
# beside him. The widest it can go is capped by the wind-up: the longest run out of it has to fit in that.
@export var inferno_cone_half_angle := 65.0
# While he hangs off the middle of the rope, the boss bar and its plate over him fade to this.
@export var inferno_hud_fade_alpha := 0.3
# The wind-up has no pull and is sized to the longest run to safety, from the bottom-centre of the ring.
# The breath hurts for less than the player's invincibility, so it lands once at most. Then his spent pose
# before he lets go.
@export var inferno_windup := 1.4
@export var inferno_breath_time := 0.9
@export var inferno_spent_time := 0.35
# The embers it leaves burning: up to this many, this far apart, each burning this long.
@export var inferno_lingering_patches := 8
@export var inferno_lingering_time := 10.0
@export var inferno_lingering_spacing := 180.0
# Its landing only burns out fire this close to him or in the player's way, so most embers outlive it, and
# his recharge is this long.
@export var inferno_landing_clearance := 60.0
@export var inferno_recover_time := 4.5

var player_defeated := false
var enraged := false
var cycles_started := 0
var attacks: Array = []
var attacks_done := 0
# The Inferno puts him down in a window of its own: the next landing's clearance and the next recovery's
# length. Below 0 is the usual; Land and Recover take them.
var landing_clearance_override := -1.0
var recover_time_override := -1.0
# The pre-fight lines' balloon, which a held skip takes down, and whether those lines have handed
# over to the VS card yet.
var pre_fight_balloon: Node
var pre_fight_over := false


func _ready() -> void:
	# His Break and his juggle are built here rather than in his scene.
	_add_state(BixbyBeastBroken.new(), "Broken")
	_add_state(BixbyBeastJuggled.new(), "Juggled")
	for child in get_children():
		if child is State:
			states[child.name] = child

	if initial_state:
		current_state = initial_state
		# Deferred until the body is ready, since the intro moves and draws him.
		current_state.Enter.call_deferred()


# The body is this node's parent, so it isn't ready yet: its hurtbox is looked up, not read off it.
func _add_state(state, state_name: String) -> void:
	state.name = state_name
	state.body = BixbyBeastCharacterBody
	state.hurtbox = BixbyBeastCharacterBody.get_node("Air/Hurtbox")
	state.state_machine = self
	add_child(state)


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
	pre_fight_balloon = DialogueManager.show_dialogue_balloon(load(PRE_FIGHT_DIALOGUE), "start", [intro])


# A held skip's way past the lines (BossEntrance), whether they were ever put up or not: the hand-over
# their own end makes, made from here instead. pre_fight_over keeps it to once - the lines can end on
# their own inside the skip, on the transformation it ran out.
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
	VsCard.play_intro(self, "liam", post_dialogue_pre_fight_timer.start)


# The transformation leaves him standing after his roar: the fight starts with his takeoff.
func _on_post_dialogue_pre_fight_timer_timeout() -> void:
	BixbyBeastCharacterBody.start_music()
	on_child_transition(current_state, "Takeoff")


func start_cycle() -> void:
	if not enraged and BixbyBeastCharacterBody.get_health_ratio() <= inferno_health_gate:
		enraged = true
		cycles_started = 0
	var cycles: Array = ENRAGED_CYCLES if enraged else ATTACK_CYCLES
	attacks = cycles[cycles_started % cycles.size()].duplicate()
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


func take_landing_clearance() -> float:
	var clearance := landing_clearance_override if landing_clearance_override >= 0.0 else fire_landing_clearance
	landing_clearance_override = -1.0
	return clearance


func take_recover_time() -> float:
	var time := recover_time_override if recover_time_override >= 0.0 else recover_time
	recover_time_override = -1.0
	return time


# His punish windows: the recovery he lands in, the dizzy spell the combined attack ends on, and a Break.
func is_recovering() -> bool:
	if current_state == states.get("Recover") or current_state == states.get("Broken"):
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


# The punish window has to be reachable: as he comes down, fire within `clearance` of where he'll land (below
# 0, fire_landing_clearance), or in the way between the player and there, burns out. The Inferno's embers
# don't block, but they hurt, so the straight way to him has to be clear of them too.
func clear_fire_for_landing(landing_point: Vector2, clearance := -1.0) -> void:
	var body_box := BixbyBeastArtLayout.local_rect(BixbyBeastArtLayout.RECOVER_BODY_BOX)
	var landed := Rect2(landing_point + body_box.position, body_box.size)
	var near := landed.grow(clearance if clearance >= 0.0 else fire_landing_clearance)
	var player := get_player()
	for fire in fire_patches(false) + embers():
		var footprint: Rect2 = fire.footprint()
		if footprint.intersects(near) or (player and _fire_in_the_way(footprint, player.global_position, landed)):
			fire.burn_out()


# The Inferno's embers that are burning, or about to.
func embers() -> Array:
	return get_tree().get_nodes_in_group(HAZARD_GROUP).filter(func(hazard: Node) -> bool:
		return hazard is Ember and hazard.is_active())


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

# A quake ring out from under his feet at `feet`, across the floor to the ropes.
func send_quake_ring(feet: Vector2) -> void:
	var ring := QUAKE_RING_SCENE.instantiate()
	ring.position = feet.round()
	ring.speed = quake_ring_speed
	ring.player = get_player()
	get_tree().current_scene.add_child(ring)


#BREAK AND JUGGLE

# His Break gauge filled (BixbyBeastScript._on_break): whatever he was doing stops, everything he sent out
# goes, and he comes down Broken. There is no flag for the fight being on, so the states it isn't on in
# are refused by name.
func enter_broken() -> void:
	if BixbyBeastCharacterBody.defeated or BixbyBeastCharacterBody.boss_health <= 0 or player_defeated:
		return
	if current_state in [states.get("Intro"), states.get("Defeated"), states.get("Broken"), states.get("Juggled")]:
		return
	for timer in [post_dialogue_pre_fight_timer, recover_timer, finisher_stagger_timer]:
		timer.stop()
	ParryTell.clear(BixbyBeastCharacterBody)
	BixbyBeastCharacterBody.clear_hazards()
	# An Inferno cut short leaves its long landing window booked for whichever landing comes next.
	landing_clearance_override = -1.0
	recover_time_override = -1.0
	on_child_transition(current_state, "Broken")


# The tiered finisher's first uppercut (BixbyBeastScript.begin_juggle).
func enter_juggled() -> void:
	if BixbyBeastCharacterBody.defeated or current_state == states.get("Juggled"):
		return
	on_child_transition(current_state, "Juggled")


# Down after a juggle, he lies slumped where he crashed and takes off into his next cycle `delay` after
# this, as after the finisher out of any other window.
func after_juggle(delay: float) -> void:
	on_child_transition(current_state, "Idle")
	BixbyBeastCharacterBody.play_anim(&"recover")
	finisher_stagger_timer.start(maxf(delay, 0.01))


# The one switch past the fight being decided: killed in the air, he lands into his defeat rather than
# snapping to its first frame mid-flight.
func land_juggled(final_state_name: String) -> void:
	var final_state = states.get(final_state_name)
	if final_state == states.get("Defeated"):
		final_state.lying = true
	current_state.Exit()
	final_state.Enter()
	current_state = final_state


# Where the leap shadow lies: his own shadow's layer, under everyone standing on the floor.
func ground_layer() -> Node2D:
	return BixbyBeastCharacterBody.shadow.get_parent()


func enter_defeated() -> void:
	_end_fight("Defeated")


# The player lost: he stops where he is.
func enter_player_defeated() -> void:
	_end_fight("Idle")
	player_defeated = true


func _end_fight(final_state_name: String) -> void:
	for timer in [post_dialogue_pre_fight_timer, recover_timer, finisher_stagger_timer]:
		timer.stop()
	var juggled = states.get("Juggled")
	# In the air, he finishes his fall and his crash first (land_juggled).
	if current_state == juggled:
		juggled.final_state = final_state_name
		return
	on_child_transition(current_state, final_state_name)
