extends Node

# Captain Burak's fight, boss 1 and the tutorial. His intro once (the lines, the hold that skips them and
# the VS card), then ATTACK_ORDER round and round, one attack at a time with a breath in Idle between:
#   Shots    the opener, two pistol shots under a red badge. Teaches the parry, and pays only the Break.
#   Barrels  five powder kegs, the load, then a shot for every keg still standing. Teaches punching, then
#            dashing. Ends in the Laugh when one is owed, then the Taunt.
#   Cutlass  a chase and three swings that only a parry or a timed dash answers. Pays only the Break.
# The Taunt is his punish window, and the Break's is the only other one.
#
# THE BREAK: parries fill his gauge (BurakBossScript.BREAK). The one that fills it drops him into Broken
# where he stands, mid-attack if need be (enter_broken), and he gets up into Idle and the next attack in
# order. Idle holds Shots and Cutlass while the gauge is locked (gauge_ready), so every parry they ask for
# is credited.
#
# WHAT EVERY ATTACK STATE KEEPS: it exports `body`, ends with attack_done(self), and has an idempotent
# release() that its own Exit() and _exit_tree() call, and _stop_everything() calls for all of them at
# once. Its knobs are its own exports, so no two attacks share a file.
#
# Every wait in this fight is a Timer, a Physics_Update accumulator or a node-bound tween, so a pause and a
# finisher's freeze hold all of it. Nothing may use get_tree().create_timer() or a tree-level
# create_tween().

@export var initial_state : State

@export var states : Dictionary = {}
@export var current_state : State
@export var BurakBossCharacterBody : CharacterBody2D

#TIMERS
@export var post_dialogue_pre_fight_timer: Timer
@export var taunt_timer: Timer
@export var finisher_stagger_timer: Timer
@export var beat_timer: Timer

const VsCard := preload("res://Scripts/VsCard.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")
const PRE_FIGHT_DIALOGUE := "res://Dialogue/BurakBossPreFight.dialogue"
const LAUGH_DIALOGUE := "res://Dialogue/BurakBossLaugh.dialogue"
# Everything he sends out: balls, kegs, blasts, slashes and their effects.
const HAZARD_GROUP := "burak_hazard"
# The states with a release(), which _stop_everything() calls.
const ATTACK_STATES := ["Shots", "Barrels", "Cutlass"]
# The attacks whose parries fill the gauge, which Idle holds while it is locked.
const GAUGE_ATTACKS := ["Shots", "Cutlass"]

#WHERE THINGS ARE (feet points, px)
# His mark in the entrance, where he loads, shoots and taunts. Low enough that a badge over his hat clears
# the boss bar and the Break gauge under it.
const HOME := Vector2(960, 560)
# Where his feet may go in the chase.
const WALK_RECT := Rect2(200, 300, 1520, 655)
# The inside edges of the ropes, as every other fight measures them.
const ROPES := Rect2(113, 114, 1692, 853)
# A badge over his crown in here is inside the boss bar, which fades while he is there.
const HUD_FADE_RECT := Rect2(680, -1080, 560, 1280)
# His health at or under this share is the top of the keg attack's ramp, and turns his bar fully hot.
const CAP_RATIO := 0.20

#PACING (seconds)
@export var idle_beat := 0.8
# How often Idle looks again at a locked gauge.
@export var gauge_wait_step := 0.2
@export var taunt_time := 4.0
# On top of the Taunt after a clean run of the kegs.
@export var clean_run_bonus := 1.0

#HUD
@export var hud_fade_alpha := 0.3

# Seedable, so a test or a bot can replay a fight.
var rng := RandomNumberGenerator.new()

var player_defeated := false
# His attacks in the order they come, advanced as each one starts. A var, so a test can pin it.
var ATTACK_ORDER: Array[String] = ["Shots", "Barrels", "Cutlass"]
var attacks_started := 0
var barrel_attacks_done := 0
# Set by Barrels when the fight's first volley landed all five blasts; the Laugh plays once.
var laugh_owed := false
var laugh_played := false
# What the next Taunt gets on top of taunt_time, spent as it opens.
var taunt_bonus := 0.0
# The pre-fight lines' balloon, which a held skip takes down, and whether those lines have handed over to
# the VS card yet.
var pre_fight_balloon: Node
var pre_fight_over := false
# The laugh cut's balloon, which a held skip takes down.
var laugh_balloon: Node


func _ready() -> void:
	rng.randomize()
	for child in get_children():
		if child is State:
			states[child.name] = child

	if initial_state:
		current_state = initial_state
		# Deferred until the scene is up: his entrance reads the player and the gates off the fight scene.
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


#THE LINES

# His intro's lines call its beats, so it passes itself along to the dialogue.
func show_pre_fight_dialogue(intro: State) -> void:
	# One-shot: the outro's lines end a dialogue too, and must not start the fight again.
	DialogueManager.dialogue_ended.connect(_on_dialogue_ended, CONNECT_ONE_SHOT)
	pre_fight_balloon = DialogueManager.show_dialogue_balloon(load(PRE_FIGHT_DIALOGUE), "start", [intro])


# A held skip's way past the lines (BossEntrance), whether they were ever put up or not: the hand-over
# their own end makes, made from here instead. pre_fight_over keeps it to once.
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
	VsCard.play_intro(self, "burak", post_dialogue_pre_fight_timer.start)


# The fight opens on the loop's own breath.
func _on_post_dialogue_pre_fight_timer_timeout() -> void:
	BurakBossCharacterBody.start_music()
	on_child_transition(current_state, "Idle")


# The laugh cut's lines (BurakBossLaugh), which call its beat. Their natural end finishes the cut.
func show_laugh_dialogue(cut: State) -> void:
	DialogueManager.dialogue_ended.connect(_on_laugh_dialogue_ended, CONNECT_ONE_SHOT)
	laugh_balloon = DialogueManager.show_dialogue_balloon(load(LAUGH_DIALOGUE), "start", [cut])


# A held skip's way out of the cut: its natural end, disconnected so it can't come again.
func end_laugh_dialogue() -> void:
	if DialogueManager.dialogue_ended.is_connected(_on_laugh_dialogue_ended):
		DialogueManager.dialogue_ended.disconnect(_on_laugh_dialogue_ended)


func _on_laugh_dialogue_ended(_dialogue: Object) -> void:
	var laugh = states.get("Laugh")
	if laugh:
		laugh.finish_cut()


#THE LOOP

# The keg attack's difficulty: 0 at full health, 1 at CAP_RATIO of it or under, linear between. Barrels
# locks it as it starts.
func ramp_p() -> float:
	return clampf((1.0 - BurakBossCharacterBody.get_health_ratio()) / (1.0 - CAP_RATIO), 0.0, 1.0)


func next_attack() -> String:
	return ATTACK_ORDER[attacks_started % ATTACK_ORDER.size()]


# The next attack in ATTACK_ORDER, now - unless it pays the Break and the gauge is locked, when Idle holds
# it and looks again every gauge_wait_step.
func start_cycle() -> void:
	if not gauge_ready():
		if current_state == states.get("Idle"):
			beat_timer.start(gauge_wait_step)
		else:
			on_child_transition(current_state, "Idle")
		return
	var attack := next_attack()
	attacks_started += 1
	on_child_transition(current_state, attack)


# Whether the next attack may start: every parry Shots and Cutlass ask for must be credited, and a locked
# gauge credits none.
func gauge_ready() -> bool:
	var gauge: Node = BurakBossCharacterBody.break_gauge
	return gauge == null or not gauge.locked or not GAUGE_ATTACKS.has(next_attack())


# An attack is over. After the kegs comes the Laugh when it is owed, then the Taunt, with `bonus` on top
# of it (a clean run's); after the others, Idle.
func attack_done(state: State, bonus := 0.0) -> void:
	if state != current_state:
		return
	if state == states.get("Barrels"):
		barrel_attacks_done += 1
		if laugh_owed and not laugh_played:
			laugh_owed = false
			on_child_transition(state, "Laugh")
		else:
			open_taunt(bonus)
		return
	on_child_transition(state, "Idle")


func open_taunt(bonus := 0.0) -> void:
	taunt_bonus = bonus
	on_child_transition(current_state, "Taunt")


func take_taunt_bonus() -> float:
	var bonus := taunt_bonus
	taunt_bonus = 0.0
	return bonus


# His windows: the Taunt, and the Break's.
func is_open() -> bool:
	return is_taunting() or current_state == states.get("Broken")


func is_taunting() -> bool:
	return current_state == states.get("Taunt")


func flinch() -> void:
	if is_open():
		current_state.flinch()


# The finisher ended his taunt early: he stays down, staggered, then the next attack.
func stagger_then_start_cycle(stagger_time: float) -> void:
	taunt_timer.stop()
	on_child_transition(current_state, "Idle")
	# Idle starts the breath before the next attack; the stagger replaces it.
	beat_timer.stop()
	# Held on the recoil frame through the stagger instead of the idle loop Idle starts.
	BurakBossCharacterBody.play_anim(&"hit", &"idle")
	finisher_stagger_timer.start(stagger_time)


func _on_finisher_stagger_timer_timeout() -> void:
	start_cycle()


#THE BREAK

# A full Break gauge (BurakBossScript._on_break): whatever he was doing stops, everything he sent out goes,
# and he drops where he stands.
func enter_broken() -> void:
	if BurakBossCharacterBody.defeated or BurakBossCharacterBody.boss_health <= 0 or player_defeated:
		return
	if current_state in [states.get("Broken"), states.get("Juggled"), states.get("Defeated")]:
		return
	_stop_everything()
	on_child_transition(current_state, "Broken")


# The finisher's uppercut ends the Break's window instead of its own clock.
func end_break(delay: float) -> void:
	_get_up(delay)


# The tiered finisher's first uppercut (BurakBossScript.begin_juggle).
func enter_juggled() -> void:
	var juggled = states["Juggled"]
	if BurakBossCharacterBody.defeated or current_state == juggled:
		return
	_stop_everything()
	on_child_transition(current_state, "Juggled")


# Down after a juggle, he picks himself up where he crashed.
func after_juggle(delay: float) -> void:
	_get_up(delay)


# The hit frame as he gets up, then idle, and his next attack `delay` from now.
func _get_up(delay: float) -> void:
	on_child_transition(current_state, "Idle")
	beat_timer.stop()
	BurakBossCharacterBody.play_anim(&"hit", &"idle")
	finisher_stagger_timer.start(maxf(delay, 0.01))


# The one switch past the fight being decided: juggled and killed in the air, he lands into his defeat
# rather than snapping to its pose mid-flight.
func land_juggled(final_state_name: String) -> void:
	var final_state = states.get(final_state_name)
	if final_state == states.get("Defeated"):
		final_state.lying = true
	current_state.Exit()
	final_state.Enter()
	current_state = final_state


#HELPERS

# Null between two scenes, which is where an attack cut short by a scene change lets go.
func get_player() -> Node2D:
	var scene := get_tree().current_scene
	return scene.get_node_or_null("Arena/MainPlayer/CharacterBody2D") if scene else null


# Where every hit of his comes from: the player's own hurtbox centre, so any facing answers it and the
# check is timing, not aim.
func player_hurtbox_centre() -> Vector2:
	var player := get_player()
	if player == null:
		return HOME
	return player.hurtBox.get_node("CollisionShape2D").global_position


# Everything he sends out lives under his scene, so a finisher's freeze holds it, and in the hazard group,
# so a Break or the end of the fight takes it away.
func add_hazard(hazard: Node2D, at: Vector2, layer: Node2D) -> void:
	hazard.add_to_group(HAZARD_GROUP)
	hazard.position = layer.to_local(at.round())
	layer.add_child(hazard)


#THE END OF THE FIGHT

func enter_defeated() -> void:
	_end_fight("Defeated")


# The player lost: he laughs where he stands.
func enter_player_defeated() -> void:
	_end_fight("Victory")
	player_defeated = true


func _end_fight(final_state_name: String) -> void:
	# A fight decided over the top of his entrance still leaves the ring set.
	var intro = states.get("Intro")
	if intro:
		intro.finish_entrance()
	_stop_everything()
	var laugh = states.get("Laugh")
	if laugh:
		laugh.finish_cut(false)
	var juggled = states.get("Juggled")
	# In the air, he finishes his fall and his crash first (land_juggled).
	if juggled and current_state == juggled:
		juggled.final_state = final_state_name
		return
	on_child_transition(current_state, final_state_name)


# Everything of his still running, stopped on the spot: a Break, a juggle, or either side winning.
func _stop_everything() -> void:
	ParryTell.clear(BurakBossCharacterBody)
	for state_name in ATTACK_STATES:
		var state = states.get(state_name)
		if state:
			state.release()
	BurakBossCharacterBody.restore_hud()
	for hazard in get_tree().get_nodes_in_group(HAZARD_GROUP):
		hazard.queue_free()
	for timer in [post_dialogue_pre_fight_timer, taunt_timer, finisher_stagger_timer, beat_timer]:
		timer.stop()
		timer.paused = false
