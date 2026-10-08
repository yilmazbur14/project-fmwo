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
const QUAKE_RING_SCENE := preload("res://Scenes/Bosses/BixbyQuakeRingScene.tscn")
const Ember := preload("res://Scripts/BixbyEmberScript.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")
const BixbyBeastBroken := preload("res://Scripts/States/BixbyBeast/BixbyBeastBroken.gd")
const BixbyBeastJuggled := preload("res://Scripts/States/BixbyBeast/BixbyBeastJuggled.gd")
const BixbyBeastFlyby := preload("res://Scripts/States/BixbyBeast/BixbyBeastFlyby.gd")
const BixbyFlybyLayout := preload("res://Scripts/BixbyFlybyLayout.gd")

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
# The steps the straight way to him is checked for fire at (_fire_in_the_way).
const FLOOR_CELL := 16.0

# The fight's loop: hover and strafe, run the cycle's attacks with a short hover between them, land for
# the punishable recovery, take off, repeat. Cycles take turns through this list from the start of the
# fight, whatever his health: the Flyby, the combined attack, the Flyby, the combined attack again, the Flyby,
# the Inferno. It starts on the Flyby so the fight doesn't open on the Inferno, and a Flyby is two passes
# already, so it has a cycle to itself. A new attack is a state that calls attack_finished() when it's done,
# listed here. The combined attack ends on a punish window of its own and takes off from it, so it is always
# the last attack of its cycle and that cycle has no landing recovery. The Inferno hands its own clearance
# and recharge to the landing straight after it, so it always has a cycle to itself. Every attack is
# followed by a window (the user's "more openings", 2026-10-04). The second combined attack came with the
# denser move sets of 2026-10-06 (difficulty 7; [Flyby], [Combined], [Flyby], [Inferno] before): a clean kill
# takes four windows, so it now meets the combined attack twice and the Inferno only once a window is missed.
const ATTACK_CYCLES := [["Flyby"], ["Combined"], ["Flyby"], ["Combined"], ["Flyby"], ["Inferno"]]

#TUNING (seconds, px and px/s)
@export var hover_time := 1.8
@export var hover_between_attacks := 0.5
@export var hover_speed := 460.0
# While hovering he strafes between points this far to either side of the player, this far up the arena from them.
@export var strafe_distance := 360.0
@export var hover_lead := 260.0
# How fast he glides back to where he'll land, and drifts down the arena as he takes off.
@export var glide_speed := 1100.0
# 3.0: 3.5 before the tuning round of 2026-10-04, 2.5 in it, then 3.0 when the user asked for more openings.
@export var recover_time := 3.0
# How long he takes to rise to hover height, from the takeoff's rising frame.
@export var takeoff_rise_time := 0.3
# The combined attack: he lands and braces this long, then pounds this many times this far apart.
@export var combined_windup := 0.5
@export var combined_pounds := 3
@export var combined_pound_interval := 0.35
# The spin's warning: the bands his beams will come out along lie lit on the floor this long before they do,
# with nothing hurting, so a player standing in one has time to see it and walk out.
@export var combined_spin_tell := 0.6
# The scream: at least this long, then on until his heads come round to a frame the wobble he stops on is
# drawn to follow, which is at most one more loop (BixbyBeastArtLayout.SPIN_LOOP, a third of a turn). He
# wobbles dizzy for this long afterwards.
# The spin can't run longer than 6 s at a ring every 2.0 s without a player who circles and dashes every ring going
# short of stamina (liam combined and spin_reach, 2026-10-04). The dizzy spell: 2.0 s (1.6 in the tuning round of
# 2026-10-04, back to 2.0 when the user asked for more openings).
@export var combined_spin_time := 6.0
@export var combined_dizzy_time := 2.0
# Every pound sends a quake ring rolling out from under him (BixbyQuakeRingScript), its radius growing this
# fast, and while he spins another follows every interval. Slow enough that the pounds' rings are still
# rolling out while he spins, and far enough apart on the floor to stand between. The three a pound sends
# come 0.35 s apart, too close to stand between, so this is also what keeps them one dash thick.
@export var quake_ring_speed := 200.0
@export var combined_spin_ring_interval := 2.0
# When he lands, embers this close to where he'll be punched burn out.
@export var fire_landing_clearance := 220.0
# THE FLYBY (BixbyBeastFlyby; its geometry and fairness are BixbyFlybyLayout's). He rises off the screen over this long;
# each pass's projection is up this long before its front sweeps, its last warn_time strong, and he flies in from off
# the screen entry_lead before the sweep; the front sweeps at this speed, faster than a walk (each projection is long
# enough to walk to its column first), to leave safe_width at the far edge, and the floor burns this long behind it,
# under the i-frames; he takes exit_time to leave the screen after a pass, and return_time to swoop back in over his
# landing point, landing_inset in from his start side's rope at landing_y. Which side pass 0 flies in from: &"away"
# from the player, &"left", &"right", &"random" or &"alternate".
# Faster at the user's word (2026-10-04, "feels slow"): 1900 px/s (1500), projections of 0.73 and 2.12 s (1.0 and 2.2),
# the rise, burn, exit and return 0.35, 0.35, 0.3 and 0.5 s (0.6, 0.45, 0.5 and 1.0): 5.99 s a Flyby, 7.81 before.
# The crossing can't go much shorter: it is a whole ring's walk, held to BixbyFlybyLayout.CROSS_SPARE.
@export var flyby_rise_time := 0.35
@export var flyby_telegraph_time := 0.73
@export var flyby_return_telegraph_time := 2.12
@export var flyby_warn_time := 0.5
@export var flyby_entry_lead := 0.2
@export var flyby_speed := 1900.0
@export var flyby_safe_width := 204.0
@export var flyby_burn_time := 0.35
@export var flyby_exit_time := 0.3
@export var flyby_return_time := 0.5
@export var flyby_landing_inset := 560.0
@export var flyby_landing_y := 720.0
@export var flyby_start_side := &"away"
# THE INFERNO (BixbyBeastInferno). He flies to the top rope this fast, perching when he gets there or after
# this long at most.
@export var inferno_perch_speed := 1300.0
@export var inferno_perch_time := 1.8
# The volley: this many fireballs spat up over this long, rising this fast, each up to this many degrees
# off straight up. Then a beat with the sky empty.
# 30, 24 until the tuning round of 2026-10-04 (difficulty 7), with the markers 0.12 s apart (0.14) and lit 0.85 s
# (1.0).
@export var inferno_fireballs := 30
@export var inferno_volley_time := 1.2
@export var inferno_rise_speed := 1600.0
@export var inferno_rise_spread_degrees := 15.0
@export var inferno_sky_beat := 0.35
# The shower tracks the player: the first marker this long into the inhale and one more every interval,
# each on the player's feet as it appears, up to the scatter off them at random, and lit for the warning
# before its fireball lands there. Markers may overlap: a player who stops can't sit in a gap between them.
@export var inferno_first_marker := 0.3
@export var inferno_marker_interval := 0.12
@export var inferno_fireball_warning := 0.85
@export var inferno_track_scatter := 40.0
# The pull, from the inhale until the last fireball lands: this many px/s toward the floor under him,
# reached over the ramp, and fading out inside the dead zone so nobody jitters at rest. It stays under the
# player's walking speed (600), so walking straight out of it still gains ground, if slowly.
@export var inferno_pull_speed := 495.0
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
# 4.0: 4.5 before the tuning round of 2026-10-04, 3.5 in it, then 4.0 when the user asked for more openings.
@export var inferno_recover_time := 4.0

var player_defeated := false
var cycles_started := 0
# The way his last Flyby's first pass flew, 0 before his first: what &"alternate" turns away from.
var last_flyby_dir := 0.0
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
	# His Break, his juggle and his Flyby are built here rather than in his scene.
	_add_state(BixbyBeastBroken.new(), "Broken")
	_add_state(BixbyBeastJuggled.new(), "Juggled")
	var flyby := BixbyBeastFlyby.new()
	flyby.name = "Flyby"
	flyby.body = BixbyBeastCharacterBody
	add_child(flyby)
	BixbyFlybyLayout.assert_invariants(self)
	for child in get_children():
		if child is State:
			states[child.name] = child

	# The main menu's LIAM row (GameProgress.start_at_liam), taken whether or not Liam follows him, so it can never
	# carry over into a later load: the fight opens on Liam's takeover, with no entrance, lines or card of the beast's.
	# The intro is never made current either - its Exit() tidies up what its Enter() built, and the defeat
	# start_at_liam() puts him in would leave through it. Deferred until the body is ready, which moves and draws him.
	var at_liam: bool = GameProgress.start_at_liam
	GameProgress.start_at_liam = false
	if at_liam and BixbyBeastCharacterBody.liam_follows:
		BixbyBeastCharacterBody.start_at_liam.call_deferred()
		return
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


#FIRE ON THE FLOOR

# The punish window has to be reachable: as he comes down, an ember within `clearance` of where he'll land
# (below 0, fire_landing_clearance), or in the way between the player and there, burns out. The Inferno's
# embers don't block, but they hurt, so the straight way to him has to be clear of them.
func clear_fire_for_landing(landing_point: Vector2, clearance := -1.0) -> void:
	var body_box := BixbyBeastArtLayout.local_rect(BixbyBeastArtLayout.RECOVER_BODY_BOX)
	var landed := Rect2(landing_point + body_box.position, body_box.size)
	var near := landed.grow(clearance if clearance >= 0.0 else fire_landing_clearance)
	var player := get_player()
	for fire in embers():
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
	ring.hurts_inside_at_birth = true
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
