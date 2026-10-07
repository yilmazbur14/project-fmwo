extends Node

# Computah's machine. ONE body, ONE cycle: an attack, then the window it leaves open, then a beat.
#
# TODAY THE CYCLE HAS ONE ATTACK IN IT - the cannon beam (live_attacks). The user took the mine field and
# the overload out of the rotation (2026-09-24): FIGHT 06's first half is meant to be easy, so that Greyson's
# half lands as the surprise. Both are still here, wired and working - the mine field, its chase, the trap and
# the catch, and the overload - and come back by name in live_attacks, with his health back up with them
# (ComputahScript.FULL_ROTATION_HEALTH). start_cycle() is the picker, and nothing else starts any of them.
#
# TELEGRAPHS NEVER SCALE. BEAM_LOCK_FLOOR is the floor the beam's read may never go under, because
# below about 0.35 s a read stops being a read and becomes a coin flip.
#
# THE PLAYER-API WRAPPERS BELOW ARE THE ONLY PLACE THIS FIGHT TOUCHES THE PLAYER'S LOCK, FACING OR
# PARRY. Each is has_method-guarded with a one-shot push_warning, the way Carter's is. PlayerScript
# and PlayerDefense belong to the defence coder; nothing here edits them.
#
# FREEZE SAFETY: every wait is a Timer node or a Physics_Update accumulator and every ramp is a
# node-bound tween, all of which a finisher's FightFreeze stops with the rest of the fight. Nothing
# here may use get_tree().create_timer() or a tree-level create_tween().

@export var initial_state : State

@export var states : Dictionary = {}
@export var current_state : State
@export var boss : CharacterBody2D

#TIMERS
@export var post_dialogue_pre_fight_timer: Timer
@export var window_timer: Timer
@export var finisher_stagger_timer: Timer
@export var beat_timer: Timer

const VsCard := preload("res://Scripts/VsCard.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")
const ComputahBroken := preload("res://Scripts/States/Computah/ComputahBroken.gd")
const ComputahJuggled := preload("res://Scripts/States/Computah/ComputahJuggled.gd")
const PRE_FIGHT_DIALOGUE := "res://Dialogue/ComputahPreFight.dialogue"
const HAZARD_GROUP := "computah_hazard"

# The inside edges of the ropes, as every other fight measures them. Nothing else may hardcode them.
const ROPES := Rect2(113, 114, 1692, 853)
# WHERE HE STANDS WHEN THE FIGHT STARTS AND AFTER EACH ATTACK, and his own health block decides the
# row. He fights on x=960, directly under it, and the redesign is 237 px tall standing and 285 to the
# antenna tip against the 132 he used to be; on the pair's old row his crown was behind his own bar
# and the beam's lock ring - which is the entire read of the fight - had nowhere left above him to
# hang. His health block's crest reaches down to y=174, the ring is 69 px of that, and he is 285 px
# to the antenna tip: this row fits all three with about 15 px of air above and below the ring.
const COMPUTAH_HOME := Vector2(960, 560)

#TUNING (seconds, px and px/s)
# The breath between attacks.
@export var beat_time := 0.6
@export var intro_beat := 2.0

#THE CANNON BEAM
# He braces, the aim line follows the player while the cannon charges, the aim LATCHES, and after a
# fixed hold the beam fires down the latched line. The charge is not the read - it tracks, so there
# is nothing to answer yet - the LOCK is, and beam_lock is how long the player has to be somewhere
# else by the time it goes off.
@export var beam_charge := 1.10
@export var beam_lock := 0.45
@export var beam_fire := 0.30
@export var beam_fade := 0.20
# The vent he opens afterwards.
@export var beam_window := 2.4

#THE CHASE (not in the rotation yet; see the header)
# The chase is a rhythm, not a grab blob: touching does nothing, the POUNCE is the grab, and it has
# three counters - outrun it, dash through it, or parry it.
@export var chase_time := 5.0
@export var chase_accel := 2500.0
# The player walks 600. Outrunnable early, marginally faster late; a dash buys the ground back.
@export var chase_speed_from := 420.0
@export var chase_speed_to := 660.0
@export var pounce_range := 140.0
@export var pounce_tell := 0.45
@export var pounce_cooldown := 1.2
@export var pounce_speed := 1400.0
@export var pounce_reach := 320.0
@export var pounce_stumble := 0.5
# The window his flat battery opens, and the longer one a parry buys.
@export var battery_window := 3.2
@export var parry_stagger_bonus := 0.8

#THE MINE FIELD
# ATTACK 2. He seeds the mat with pods, then runs the player down at speed, so that getting away from
# him costs ground the player has to pick their way through. A pod that closes SEALS them - no move,
# no dash, no punch, no guard and no parry - and he walks over and charges an uppercut while they
# mash out of it. Mashing out in time does not stop the punch; it takes the player off the end of it,
# and he overbalances into the longest window in the fight.
@export var mine_count := 6
# Live pods at once, across cycles. The field is meant to overlap itself by about one cycle, never to
# silt up.
@export var mine_cap := 8
@export var mine_arm := 0.45
@export var mine_flight := 0.28
@export var mine_lay_interval := 0.18
@export var mine_life := 14.0
@export var mine_fade := 1.0
# Between pods, and between a pod and the player it is laid near. 200 px of gap down the sides leaves
# a clear lane of about 80 px: narrow enough to be a real test against a 720 px/s chaser, wide enough
# that there is always an out.
@export var mine_spacing := 200.0
@export var mine_min_from_player := 220.0
# After a hold lets go - a catch or a trap - before anything of his may take the player again. A
# player who has just been put down has no answer available to them yet.
@export var trap_grace := 1.2
@export var catch_grace := 2.0
# The chase this attack runs, faster and longer than the standalone one.
@export var mine_chase_speed_from := 560.0
@export var mine_chase_speed_to := 720.0
@export var mine_chase_time := 6.0
@export var mine_walk_speed := 900.0
@export var mine_charge := 1.50
# The escape mash. Deliberately NOT the finisher's 0.107/0.14, which would take longer to fill than
# the whole trap lasts: these two are PlayerGrabEscape's shape, with a heavier drain, because this
# hold is shorter than a bear hug and standing still in it has to cost. Both are bent by MashCurve, and
# the drain is fitted so getting out takes about 5.5 a second with him beside the pod and 4.6 with the
# ring to cross.
@export var escape_gain := 0.16
@export var escape_drain := 0.21
# The window a whiffed uppercut opens, and what a catch costs on top of the damage.
@export var mine_fall_window := 3.6
@export var mine_fall_cap := 4
@export var mine_uppercut_recover := 0.6
@export var catch_stamina_drain := 30.0

#THE OVERLOAD
# ATTACK 3, AND THE ONE THE REST OF THE FIGHT'S VOCABULARY DOES NOT ANSWER. He stands still and winds
# himself up; the player has to RUSH HIM AND PUNCH, and land overload_threshold half-hearts before the
# clock runs out. Fail and the charge goes off over the whole mat, where there is nowhere to be - no
# guard, no parry, no dash - for a full heart. Break it and he is left dazed, which is the uppercut.
# IT CARRIES NO TELL OF EITHER COLOUR. Red means parry and yellow means dodge, and both are WRONG
# here: a badge is an answer key naming a button and this has no button. carter_clone_punish is the
# precedent. What goes up instead is the two-row race gauge over his head, plus his own body, whose
# charge rows say the same thing a second way.
#
# NOTHING HERE SCALES, IN EITHER PHASE, and that is a stronger rule than the house one about
# telegraphs. Duration and threshold together define a REQUIRED DPS, and the player's own DPS is
# fixed by the punch animation; move either and the check crosses from winnable to unwinnable with
# nothing visible changing. It is the one attack that cannot be answered by reaction - the player has
# to have learned the number. Only overload_every_cycles, how often it comes round, may ever move.
@export var overload_time := 3.4
@export var overload_threshold := 6
# WELL ABOVE THE 5 PUNCHES THE THRESHOLD NEEDS, and it exists only so nothing is unbounded: THE
# THRESHOLD ENDS THE CHARGE, NEVER THE CAP. ComputahScript.take_punch() returns 0 past the window cap,
# and a punch that returns 0 is refused (PlayerCombo.punch_refused) - so a cap anywhere near the
# threshold would leave the player punching a boss that has stopped taking anything while the charge
# runs on.
@export var overload_hit_cap := 12
# HOW FAR AWAY HE MAY START IT, AND THIS IS THE LOAD-BEARING NUMBER, NOT THE DURATION. Measured in the
# suite (computah_overload, REACHABILITY) rather than assumed: a punch first reaches him at 123 px and
# the player walks 600 px/s, so from 700 px the run-in costs 0.98 s. The combo has no timing since
# 2026-09-30, so from a fresh count the threshold takes five punches however they are pressed, the
# third the POW (four, with a count carried in): mashed, they clear at 2.75 s, 0.65 s of the charge to
# spare; pressed a tenth of a second after each swing ends, at 3.13 s, 0.27 s to spare. The slowest
# steady player that still clears leaves 0.14 s between a swing and the next press. The masher's spare
# puts the unwinnable ceiling at about 1090 px, past anywhere the ring lets him be from HOME, so THIS,
# not the duration, is what makes the check winnable at all, and ANY CHANGE TO overload_time MUST MOVE
# IT WITH THEM.
@export var overload_start_range := 700.0
# Only if break_now() falls back - a build with no Break gauge, or one that refuses.
@export var overload_break_window := 3.2
# The stingy window after a blast that landed. Short on purpose: the player has just been handed a
# full heart of damage for nothing, and the attack is not also a gift.
@export var overload_vent := 1.6
@export var overload_every_cycles := 3

# THE READ FLOORS. A telegraph under about 0.35 s is a coin flip rather than a reaction.
const POUNCE_TELL_FLOOR := 0.32
const BEAM_LOCK_FLOOR := 0.38
# THE CHASE'S CEILING, and it is the other kind of floor. Above about 800 px/s a dash's 250 px is
# back in his hands inside 0.6 s of closing, and the chase stops being winnable at all.
const CHASE_SPEED_CEILING := 800.0

var player_defeated := false
var cycles_started := 0
# Whether he is punchable right now. One source, so the rules can't drift.
var open := false
# Which attack the last cycle picked, and whether a hold has let go since. Both feed the picker, and
# both are why the mine field can never run twice in a row (see _next_attack).
var last_attack := "LayMines"
var caught_since_cycle := false
# On his own fight clock (game seconds), so a hit-stop holds the grace with everything else.
var last_release_time := -INF
# The pre-fight lines' balloon, which a held skip takes down, and whether those lines have handed
# over to the VS card yet.
var pre_fight_balloon: Node
var pre_fight_over := false

var warned := {}


func _ready() -> void:
	# His Break and his juggle are built here rather than in his scene, as Jordan's intro is, so nothing
	# an open editor saves can write over them. Before the loop registers them, and before any Break:
	# Broken's slide reads Juggled's floor.
	_add_state(ComputahBroken.new(), "Broken")
	_add_state(ComputahJuggled.new(), "Juggled")
	for child in get_children():
		if child is State:
			states[child.name] = child

	if initial_state:
		current_state = initial_state
	# The main menu's GREYSON row (GameProgress.start_at_greyson), taken whether or not Greyson follows him, so it
	# can never carry over into a later load: the fight opens on Greyson's takeover, with no entrance, lines or
	# card of Computah's. Deferred until the body is ready, which loads Greyson's scene.
	var at_greyson: bool = GameProgress.start_at_greyson
	GameProgress.start_at_greyson = false
	if at_greyson and boss.greyson_follows:
		boss.start_at_greyson.call_deferred()
		return
	if initial_state:
		# Deferred until the body is ready, since the intro places and draws him.
		current_state.Enter.call_deferred()
	# On the first frame, the way the fight has always done it, rather than at the end of the intro
	# pose: anything driving the fight from outside (the defence suite) ends the dialogue as soon as
	# the scene loads, and a handler connected a second later would never hear it.
	show_pre_fight_dialogue.call_deferred(initial_state)


# The hurtbox comes off the tree, not off the body's onready var: the body is this node's parent, and a
# parent is ready after its children, so that var isn't set yet.
func _add_state(state, state_name: String) -> void:
	state.name = state_name
	state.body = boss
	state.hurtbox = boss.get_node("Hurtbox")
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


#THE CYCLE

# His lines call the entrance's beats - the dead air and the charge-up - so the intro goes in as an
# extra game state for them to resolve against, the way Eric's and Liam's do.
func show_pre_fight_dialogue(intro: State) -> void:
	# One-shot: the outro's lines end a dialogue too, and must not start the fight again.
	DialogueManager.dialogue_ended.connect(_on_dialogue_ended, CONNECT_ONE_SHOT)
	pre_fight_balloon = DialogueManager.show_dialogue_balloon(load(PRE_FIGHT_DIALOGUE), "start", [intro])


# A held skip's way past the lines (BossEntrance): the hand-over their own end makes, made from here
# instead. pre_fight_over keeps it to once - the lines can end on their own inside the skip, on the
# charge-up it ran out.
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
	VsCard.play_intro(self, "computah", post_dialogue_pre_fight_timer.start.bind(intro_beat))


func _on_post_dialogue_pre_fight_timer_timeout() -> void:
	boss.start_music()
	start_cycle()


# THE ATTACK PICKER. Three moves, and what decides between them is chosen here and nowhere else.
const ATTACKS := ["Beam", "LayMines", "Overload"]
# The ones the picker may choose: the beam alone (see the header). A var, so a test of the dormant two can put
# them back for itself.
var live_attacks: Array[String] = ["Beam"]


# THE OVERLOAD TAKES A TURN WITHOUT SPENDING ONE. It does not write `last_attack`, so the beam and the
# mine field carry on alternating either side of it and the mine field is still always followed by the
# beam. A cycle it is refused on is a plain one, and it waits for the next multiple.
func start_cycle() -> void:
	cycles_started += 1
	caught_since_cycle = false
	if live_attacks.has("Overload") and cycles_started % overload_every_cycles == 0 and can_start_overload():
		on_child_transition(current_state, "Overload")
		return
	last_attack = _next_attack()
	on_child_transition(current_state, last_attack)


#THE OVERLOAD'S GATES
# FAILING THIS CHECK HAS TO BE THE PLAYER'S FAULT. The blast cannot be dodged, blocked or parried, so
# every way of being unable to answer it has to be a reason not to START it - and then, because the
# charge lasts 3.4 s, the same rule has to hold for the whole of it:
#
#   THE BLAST IS ARMED WHEN THE CHARGE STARTS AND DISARMED BY ANYTHING THAT TAKES THE PLAYER'S INPUTS
#   AWAY.
#
# Stated as a general rule rather than a list, because it has to cover the cases nobody has thought of
# yet. ComputahOverload checks it every physics step and vents harmlessly - no blast, no damage - the
# moment it stops holding.
func player_can_answer() -> bool:
	var player: Node2D = get_player()
	if player == null or player.fight_over or player.is_finishing or player.is_grabbed:
		return false
	if player.is_talking or player.playerHealth <= 0:
		return false
	# Sealed by a pod, or held by anything else that locks them: no punches, so no way through it.
	if player.is_action_locked:
		return false
	# A guard break is a stun with no input in it, and an undodgeable blast on the end of one is a
	# punish the player never had a turn in.
	var defense: Node = _defense()
	return defense == null or not defense.is_guard_broken


func can_start_overload() -> bool:
	if player_defeated or not is_instance_valid(boss) or boss.defeated or boss.boss_health <= 0:
		return false
	if not player_can_answer():
		return false
	# THE PACING GATE, AND IT IS THE WHOLE OF ONE. A broken charge is a guaranteed finisher, so what
	# stops one coming round too often is the same lock that stops the gauge handing them out - the
	# attack needs no cooldown of its own.
	if boss.break_gauge and boss.break_gauge.locked:
		return false
	return get_player().global_position.distance_to(boss.global_position) <= overload_start_range


# HE WIPES THE MAT AS HE STARTS CHARGING, and that is how the attack keeps the blunt fairness rule
# without the rule strangling it. A player who has to cross a minefield to reach him is being asked
# the impossible - but refusing to start on a live pod refuses forever, because the field is built to
# overlap itself (mine_cap, mine_life) and measured over a whole fight the mat is clear on 2 cycles in
# 35. So the rule is kept by making it true instead of by waiting for it: by the time the charge
# starts, there is no minefield.
#
# EXPIRED, NOT FREED. Each pod runs through its own breaking-up frames, so the clear reads as him
# pulling the charge back out of them rather than as pods blinking out, which would look like a bug.
# The trigger dies on the instant, so the mat is SAFE from the first frame of the charge; only the
# picture takes mine_fade to play out, which is inside the 0.98 s run-in from the furthest legal start.
#
# LIVE PODS ONLY. A sprung one is holding the player and ComputahTrapped.release() owns its life;
# freeing it out from under somebody being held is exactly how a player gets stranded. Nothing can be
# held here anyway - can_start_overload() refuses a locked player - but the two rules must not be one
# rule, because only one of them is about fairness.
func sweep_field() -> void:
	for mine in live_mines():
		mine.expire()


# NO FINISHER MAY START MID-CHARGE. A charged punch landing into the charge would otherwise freeze the
# fight and hand out the uppercut for NOT completing the check. ComputahScript.can_be_dazed() consults
# this, the way flinch() and end_window() consult the current state.
func allows_daze() -> bool:
	if current_state and current_state.has_method("allows_daze"):
		return current_state.allows_daze()
	return true


# THE MINE FIELD NEVER RUNS TWICE IN A ROW AND NEVER STRAIGHT AFTER A HOLD LET GO. With two attacks
# that means a catch is always followed by the beam, which is the fight's recovery beat: the chase
# and the uppercut both land inside the i-frames, and back-to-back mine fields would leave a caught
# player no window with nothing in it. It is structural rather than a rule somebody has to remember.
# `last_attack` starts on the mine field so the fight OPENS on the beam - the mine field is answered
# by moving, and the player needs one cycle of him standing still to read him first.
func _next_attack() -> String:
	if not live_attacks.has("LayMines") or last_attack == "LayMines" or caught_since_cycle:
		return "Beam"
	return "LayMines"


# A hold landed: ComputahCaught's pounce, or the mine trap's uppercut.
func note_catch() -> void:
	caught_since_cycle = true


func start_beat() -> void:
	on_child_transition(current_state, "Idle")


#THE PUNISH WINDOW
# One parameterised state, so an attack that opens a different-looking window still plays by the
# same rules.

# The chase, on the caller's numbers rather than its own: the standalone chase and the mine field's
# are the same rhythm at two different speeds. open_window's idiom - the fields are set before the
# transition - and a bare transition into Chase still gets its own defaults.
func start_chase(speed_from: float, speed_to: float, length: float) -> void:
	var chase: State = states.get("Chase")
	if chase == null:
		return
	chase.speed_from = speed_from
	chase.speed_to = minf(speed_to, CHASE_SPEED_CEILING)
	chase.length = length
	on_child_transition(current_state, "Chase")


func open_window(duration: float, cap: int, enter_anim: StringName,
		hold_anim: StringName, exit_anim: StringName) -> void:
	var punish: State = states.get("Punish")
	punish.window_time = duration
	punish.window_cap = cap
	punish.enter_anim = enter_anim
	punish.hold_anim = hold_anim
	punish.exit_anim = exit_anim
	on_child_transition(current_state, "Punish")


# Called by a state that opens him itself, inside a longer attack.
func set_open(on: bool) -> void:
	open = on


func is_open() -> bool:
	return open and not boss.defeated


# The state that opened the window decides what he goes back to after the recoil.
func flinch() -> void:
	if not is_open():
		return
	if current_state.has_method("flinch"):
		current_state.flinch()
	else:
		boss.flinch()


# The finisher ended a window early. A state that owns a window inside a longer attack answers for
# itself, so a finisher there doesn't end the attack around it.
func end_window(stagger_time: float) -> bool:
	if not is_open():
		return false
	if current_state.has_method("end_window"):
		return current_state.end_window(stagger_time)
	return _end_punish_window(stagger_time)


func _end_punish_window(stagger_time: float) -> bool:
	window_timer.stop()
	open = false
	on_child_transition(current_state, "Idle")
	# Idle starts the beat before the next attack; the stagger replaces it.
	beat_timer.stop()
	# Held on the recoil frame through the stagger instead of the idle loop Idle started, and on it to the end: the
	# finisher rocks his sprite back and settles it over the whole stagger, so a floor pose in it floats, and the next
	# beam's brace stands up out of it rather than off the mat.
	boss.play_anim(&"hit")
	finisher_stagger_timer.start(stagger_time)
	return true


func _on_finisher_stagger_timer_timeout() -> void:
	start_cycle()


#THE MINE FIELD
# ONE GATE FOR EVERY TRIGGER. A pod asks this before it does anything at all, so the rules of when a
# trap may open live in one place and a refused pod is never consumed - it stays armed for whatever
# the player does next.
#
# WHAT IT DELIBERATELY DOES NOT REFUSE, because a mine is a STATE and not damage:
#   a dashing player  - lock_actions() cuts a dash, and that is what "no dash_through" has to mean
#   a punching player - a swing already in the air finishes
#   an invincible one - being hit a moment ago is not a reason to walk through a bear trap
func trap_allowed() -> bool:
	if player_defeated or not is_instance_valid(boss) or boss.defeated or boss.boss_health <= 0:
		return false
	# The intro places him and the defeat is terminal; a trap in either is a hold with no fight
	# around it. A trap already open is the whole of the second rule. Broken and juggled, the player has
	# just been driven in to punish him, and a pod closing on them would take that away.
	for state_name in ["Intro", "Defeated", "Trapped", "Broken", "Juggled"]:
		if current_state == states.get(state_name):
			return false
	if boss.fight_clock - last_release_time < trap_grace:
		return false
	# Once the beam's aim has latched, being somewhere else is the ONLY answer the player has, and a
	# pod that took that away would make the attack unanswerable. The tracking charge is fine: there
	# is nothing to answer yet.
	var beam: State = states.get("Beam")
	if beam and current_state == beam and beam.is_committed():
		return false
	var player: Node2D = get_player()
	if player == null or player.fight_over or player.is_finishing or player.is_grabbed:
		return false
	if player.playerHealth <= 0:
		return false
	# A guard break is a 1.5 s stun with no input in it. Stacking an inescapable hold on top of that
	# is a death sentence the player never had a turn in, so the pod waits and stays armed.
	var defense: Node = _defense()
	return defense == null or not defense.is_guard_broken


# A pod closed on the player. Called from the pod's own physics step, which is where it sees them.
func trap_player(mine: Node2D) -> void:
	var trapped: State = states.get("Trapped")
	if trapped == null:
		return
	trapped.mine = mine
	on_child_transition(current_state, "Trapped")


# Every pod still worth keeping out of the way of, for the next one's placement and for the cap.
func live_mines() -> Array:
	var mines := []
	for hazard in get_tree().get_nodes_in_group(HAZARD_GROUP):
		if hazard.has_method("is_live") and hazard.is_live():
			mines.append(hazard)
	return mines


# A hold let go, whichever one. trap_grace and catch_grace are both measured from here: one moment,
# two windows, so a player put down can never be picked straight back up.
func note_release() -> void:
	if is_instance_valid(boss):
		last_release_time = boss.fight_clock


# The pounce still tells and still lunges inside the grace - it just comes up empty, which reads as
# him fumbling rather than as the player being invulnerable. THE TELL NEVER SCALES.
func in_catch_grace() -> bool:
	return is_instance_valid(boss) and boss.fight_clock - last_release_time < catch_grace


#THE BREAK
# His daze meter filling (BossBreakGauge) drops him where he stands (ComputahBroken): the one window
# that pays out the three-bar finisher and the juggle. Fed by reading his fight and drained by being
# caught by it.

func enter_broken() -> void:
	if player_defeated or boss.defeated or boss.boss_health <= 0:
		return
	for state_name in ["Defeated", "Intro", "Broken", "Juggled"]:
		if current_state == states.get(state_name):
			return
	# Nothing may be left holding the player while he falls over.
	var trapped: State = states.get("Trapped")
	if trapped:
		trapped.release()
	var caught: State = states.get("Caught")
	if caught:
		caught.release()
	ParryTell.clear(boss)
	beat_timer.stop()
	window_timer.stop()
	finisher_stagger_timer.stop()
	# The mat goes with him: the player is about to be driven in beside him, and a pod left armed there
	# is a trap they are walked into blind. Expired, as the overload's sweep is, so it reads as him
	# losing the charge in them.
	sweep_field()
	on_child_transition(current_state, "Broken")


# The single-bar finisher ended his Break window instead of its own clock (ComputahBroken.end_window):
# the same stagger any other window's finisher leaves.
func end_break(stagger_time: float) -> void:
	_end_punish_window(stagger_time)


# The tiered finisher's first uppercut (ComputahScript.begin_juggle).
func enter_juggled() -> void:
	if boss.defeated or current_state == states["Juggled"]:
		return
	on_child_transition(current_state, "Juggled")


# Down after a juggle, he gets up where he crashed, and his next attack comes `delay` after this.
func after_juggle(delay: float) -> void:
	on_child_transition(current_state, "Idle")
	beat_timer.stop()
	# The juggle left his own animation halted. This is him getting up, and Idle lets it play out.
	boss.play_anim(&"reboot", &"idle")
	finisher_stagger_timer.start(maxf(delay, 0.01))


# The one switch past the fight being decided that on_child_transition refuses: killed in the air, he
# lands into his end rather than snapping to it mid-flight, and goes straight into it.
func land_juggled(final_state_name: String) -> void:
	var juggled = current_state
	var final_state = states.get(final_state_name)
	var beaten: bool = final_state == states.get("Defeated")
	if beaten:
		final_state.lying = true
	juggled.Exit()
	# Only beaten does he stay down on the juggle's KO loop. The player losing leaves him standing.
	if not beaten:
		juggled.stop_lingering()
	final_state.Enter()
	current_state = final_state
	# The player losing ends the fight in Idle, whose Enter starts the beat into his next attack.
	beat_timer.stop()


#THE PARRY STAGGER
# Only the pounce can be parried, and only the chase knows whether one is in the air.

func can_parry_stagger(hit: RefCounted) -> bool:
	var chase: State = states.get("Chase")
	if chase == null or current_state != chase:
		return false
	return chase.can_parry_stagger(hit)


func parry_stagger(duration: float) -> void:
	var chase: State = states.get("Chase")
	if chase == null or current_state != chase:
		return
	chase.parry_stagger(duration)


#THE END

func enter_defeated() -> void:
	_end_fight("Defeated")


# The player lost: they stop where they stand.
func enter_player_defeated() -> void:
	_end_fight("Idle")
	player_defeated = true


func _end_fight(final_state_name: String) -> void:
	# Before anything else: a terminal path that never reaches Caught.Exit() or Trapped.Exit() still
	# has to free the player. A player left locked - or worse, sealed - is unrecoverable.
	for holder in ["Caught", "Trapped"]:
		var hold: State = states.get(holder)
		if hold:
			hold.release()
	open = false
	if is_instance_valid(boss):
		ParryTell.clear(boss)
	for hazard in get_tree().get_nodes_in_group(HAZARD_GROUP):
		hazard.queue_free()
	var juggled = states.get("Juggled")
	if current_state == juggled:
		# In the air, he finishes his fall and his crash first (land_juggled). His clocks stop now.
		juggled.final_state = final_state_name
		_stop_timers()
		return
	on_child_transition(current_state, final_state_name)
	# After the transition, not before: entering Idle starts the beat timer, which must not survive
	# the end of the fight.
	_stop_timers()


func _stop_timers() -> void:
	for timer in [post_dialogue_pre_fight_timer, window_timer, finisher_stagger_timer, beat_timer]:
		timer.stop()


#THE ARENA

# Guarded both ways because Caught.release() runs from _exit_tree(): a scene change mid-catch takes
# the fight down around it, and the release must not be the thing that errors on the way out.
func get_player() -> Node2D:
	if not is_inside_tree():
		return null
	var scene: Node = get_tree().current_scene
	return scene.get_node_or_null("Arena/MainPlayer/CharacterBody2D") if is_instance_valid(scene) else null


# Where his feet may be while he runs: inside the ropes, and far enough from the top edge that his
# antenna stays on screen. 170 is his run frames' own height - 273 px to the antenna tip - measured
# down from the ropes' top rail at y=114.
const RUNNER_MARGIN := Vector2(80, 170)


func runner_bounds() -> Rect2:
	return Rect2(ROPES.position + RUNNER_MARGIN, ROPES.size - RUNNER_MARGIN * 2.0)


# Where the juggle's leap shadow lies: the floor his pods lie on. His fight has no Arena/GroundFx, and
# this layer is y-sorted and ahead of his body in the tree, so a shadow on his ground line draws under
# him.
func ground_layer() -> Node2D:
	return boss.get_parent().get_node("HazardLayer")


# Everything he sends out lives under the fight scene, so a finisher's freeze holds it and the end
# of the fight takes it away.
func add_hazard(hazard: Node2D, at: Vector2, layer: Node2D) -> void:
	hazard.add_to_group(HAZARD_GROUP)
	layer.add_child(hazard)
	hazard.global_position = at.round()


#THE PLAYER API
# Reused, never reinvented: the parry-only lock, the warp and the facing are all the player's own,
# and every call is guarded so a build without one of them still runs.

func lock_player() -> void:
	var player := get_player()
	if player and player.has_method("lock_actions"):
		player.lock_actions()
	else:
		_warn_once("lock", "Computah: player has no lock_actions(); the catch can't hold them")


# THE TOTAL LOCK, and only the mine trap uses it: as lock_actions(), and the guard and its parry are
# sealed off too. A pod that has closed has no answer at all - that is what the attack IS - so leaving
# the guard live would draw presses at something nothing can be done about. unlock_actions() below
# clears both kinds; there is no second way out.
func seal_player() -> void:
	var player := get_player()
	if player and player.has_method("lock_actions_sealed"):
		player.lock_actions_sealed()
	else:
		_warn_once("seal", "Computah: player has no lock_actions_sealed(); the mine trap can't seal them")


func unlock_player() -> void:
	var player := get_player()
	if player and player.has_method("unlock_actions"):
		player.unlock_actions()


# Held in a still pose for the hold. Paired with the seal, which is what keeps them from moving:
# without the pose a player who walked into the pod moonwalks on the spot for the whole of it.
func pose_player(on: bool) -> void:
	var player := get_player()
	if player and player.has_method("set_scripted_pose"):
		player.set_scripted_pose(on)


# What a catch costs beyond the damage. PlayerDefense.drain_stamina counts as a spend, so the refill
# delay restarts, and it only breaks the guard if one is up - and a caught player is sealed with
# their guard down, so a catch never guard-breaks them. That is correct: a stun on top of a grab is a
# double punish.
func drain_player_stamina(amount: float) -> void:
	var defense := _defense()
	if defense and defense.has_method("drain_stamina"):
		defense.drain_stamina(amount)
	else:
		_warn_once("drain", "Computah: PlayerDefense has no drain_stamina(); a catch costs no stamina")


func warp_player(point: Vector2) -> void:
	var player := get_player()
	if player and player.has_method("warp_to"):
		player.warp_to(point.round())
	elif player:
		player.global_position = point.round()


func face_player_at(point: Vector2) -> void:
	var player := get_player()
	if player and player.has_method("face_point"):
		player.face_point(point)


func clear_player_facing() -> void:
	var player := get_player()
	if player and player.has_method("clear_face_point"):
		player.clear_face_point()


# The only existing way to hand back the post-grab i-frames and the toss. Calling it without a
# preceding grab() is harmless - it sets is_grabbed false, which it already is, shows the sprite,
# which is already shown, and gives the push and the i-frames, which is the whole point.
func release_player(push: Vector2) -> void:
	var player := get_player()
	if player and player.has_method("release_grab"):
		player.release_grab(push)


# Called at the start of EVERY pounce tell, always. PlayerDefense counts a press that didn't parry
# against the next attack for parry_mash_lockout (0.5 s), so without this a whiffed press can leave
# the next pounce mathematically unparryable. Carter's fight learned this the hard way.
func rearm_parry() -> void:
	var defense := _defense()
	if defense and defense.has_method("rearm_parry"):
		defense.rearm_parry()
	else:
		_warn_once("rearm", "Computah: PlayerDefense has no rearm_parry(); a whiffed press can lock out the next pounce")


func _defense() -> Node:
	var player := get_player()
	return player.get("defense") if player else null


func _warn_once(key: String, message: String) -> void:
	if warned.has(key):
		return
	warned[key] = true
	push_warning(message)
