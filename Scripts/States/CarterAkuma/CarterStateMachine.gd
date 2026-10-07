extends Node

# Carter's fight, boss 5. Intro once, then attack -> Recover -> Idle -> attack for as long as he is
# standing. He has three attacks and they come round in a fixed rotation (next_attack): the Raging
# Demon barrage, the Beam Rush twice, the Messatsu, then the barrage again - as one combo since
# 2026-10-05, the barrage straight into the Beam Rush and that straight on, with his punish window after
# the Messatsu (chain_attacks).
#
# THE BARRAGE'S DIFFICULTY AXIS IS THE NUMBER OF YELLOWS, AND NOTHING ELSE. Eighteen clones,
# identical rhythm, every round forever - that is what makes the fight learnable. To make it harder,
# raise what yellow_count() returns. Never shorten clone_show: 0.36 s is a red/yellow DISCRIMINATION
# reaction (~0.35-0.40 s), which is slower than a simple one, and cutting it makes the move a coin
# flip rather than a read.
#
# THERE IS NO PER-BOSS HYPE TABLE HERE, AND THAT IS A MEASURED RESULT RATHER THAN AN OVERSIGHT.
# PlayerFeel's feel_v2 cuts a parry from [25, 30, 35] to [15, 20, 25], which is 40% off the first
# parry but only 29% off a barrage: fifteen clones spend almost all of it on the third tier. A
# perfect first barrage pays 360 against V1's 510 and a whole fight 1040 against 1480, and the meter
# only holds 100 - so it fills on the 5th clean parry instead of the 4th, both inside barrage one,
# and still does at 50% reads with the guard down between clones. The reworked dash and punch reach
# change nothing during the barrage at all: the player is is_action_locked and the guard is the only
# answer they have.
#
# THE PLAYER-API WRAPPERS BELOW ARE THE ONLY PLACE THIS FIGHT TOUCHES THE PLAYER'S LOCK, PARRY OR
# STAMINA. Each is has_method-guarded with a one-shot push_warning, like JoshCardsStateMachine's
# apply_status(): the parts of the API that aren't written yet leave the fight running and testable,
# just easier. PlayerScript.gd and PlayerDefense.gd belong to the defence coder; nothing here edits
# them.

@export var initial_state : State

@export var states : Dictionary = {}
@export var current_state : State
@export var CarterAkumaCharacterBody : CharacterBody2D

#TIMERS
@export var post_dialogue_pre_fight_timer: Timer
@export var recover_timer: Timer
@export var finisher_stagger_timer: Timer
@export var beat_timer: Timer

const VsCard := preload("res://Scripts/VsCard.gd")
const CarterJuggled := preload("res://Scripts/States/CarterAkuma/CarterJuggled.gd")
const PRE_FIGHT_DIALOGUE := "res://Dialogue/CarterPreFight.dialogue"
const HAZARD_GROUP := "carter_hazard"

# The inside edges of the ropes, as every other fight measures them, and the point he drags the
# player to. Nothing else may hardcode either.
const ROPES := Rect2(113, 114, 1692, 853)
const ARENA_CENTRE := Vector2(959, 540)
# How far inside the ropes a Break keeps his feet - where its window drops him, and where the juggle's
# last uppercut shoves him - and the gap in x that drop leaves between him and the player.
const BREAK_ROPE_MARGIN := 90.0
const BREAK_PLAYER_GAP := 250.0

#TUNING (seconds and px)
# Beat 0: the eyes go. The lock lands on frame 1 of this, not at the end of it - a player mid-dash
# has to stop before the yank, not during it.
@export var flash_time := 0.55
# Beat 1: dragged to the middle. Not a teleport; the drive is what sells it as him grabbing you.
# The drive is 0.20 rather than the plan's 0.30 because carter_warp.wav's arrival transient lands
# 195 ms in: the sound and the landing have to be the same moment. The beat is still 0.35 s - what
# the drive gives up, the hold after it takes - so nothing downstream moved.
@export var yank_time := 0.20
@export var yank_hold := 0.15
# Beat 2: the lights go out.
@export var darken_time := 0.45
# Beat 3: the barrage. clone_show is the read, clone_dash the timing cue; splitting them is what
# makes the parry window fair.
# CLONE_SHOW IS AT ITS FLOOR AT 0.36 AND MUST NOT GO BELOW IT. Telling red from yellow is a
# DISCRIMINATION reaction, about 0.35 s, which is slower than simply reacting to something appearing;
# 0.36 is the last value at which a player can still make that decision at all. It came down from
# 0.44 once, on the user's call, and there is nothing left to give. Anything under this and the
# feints stop being readable and the whole mechanic is a coin flip. Cut somewhere else.
# The cadence is clone_show + clone_dash + clone_gap = 0.62 s. That is well inside
# PlayerDefense.parry_mash_lockout (0.5 s) plus the parry window, so the cadence is no longer its own
# safety net: the rearm_parry() this fight makes as each light comes up is what keeps consecutive
# clones answerable. Don't remove it, and don't shorten anything here without re-reading that.
# One clone lives clone_show + clone_dash = 0.54 s against that 0.62 s cadence, so two lights are
# never up at once and the player always knows which clone a press is answering. CLONE_LIGHT_OUT is
# what keeps a feint's light from being the second one on screen; it has 0.08 s to work in.
# The first barrage's, all red: it teaches the rhythm. Fifteen until 2026-10-05, eighteen since.
@export var clone_count := 18
# Every barrage after the first (2026-10-06): longer, and PALE_X_ROUND of it lies. The reds stay about
# what they were - every parried red is a read toward his Break, which pays as fast as it costs - and the
# lies are what is added: a pale X answered right pays nothing, and one bitten costs a heart.
@export var pale_x_clone_count := 24
@export var clone_show := 0.36
@export var clone_dash := 0.18
@export var clone_gap := 0.08
@export var clone_radius := 420.0
# Beat 4: the lights come up and he is standing there.
@export var clear_time := 0.50
@export var recover_offset := 340.0
# Beat 5: the punish window, longer for a barrage read well and shorter for one blown. The per-parry
# numbers are small because there are fifteen clones to earn them on, not five; the cap is what a
# perfect barrage is worth.
# 1.5 s since 2026-10-05 (3.0 before): with his window only after the Messatsu, a string read well -
# 2.9 s for all seven parried, 2.45 s for six - leaves time to reach him for the finisher, and one
# blown - 2.0 s for five, the 1.5 s floor below that - mostly doesn't. He kneels at least
# messatsu_min_range from where the player stood.
@export var recover_base := 1.5
@export var recover_parry_bonus := 0.2
@export var recover_miss_penalty := 0.25
@export var recover_min := 1.5
@export var recover_max := 6.0
# HIS ATTACKS ARE ONE COMBO (tuning 2026-10-05). Each attack in CHAINED_ATTACKS that didn't break him
# hands straight on to the next one in the rotation (chain_on), and only the Messatsu ends in his punish
# window. Every finisher pays a share of his health, so his length is how many windows he hands out: a
# window after every attack killed him in about 45 s at any max_health once the 2026-10-04 mash made a
# Break worth 56%, and the user wants the difficulty from his move set (2026-10-05). His Break is still
# his punish window, in any of them.
@export var chain_attacks := true
const CHAINED_ATTACKS := ["RagingDemon", "BeamRush"]
# The banked damage a barrage earns: one half-heart per this many reds parried, plus the bonus for a
# barrage with every red parried and no feint bitten. Scaled to fifteen clones, so a barrage read
# well is worth proportionally what the five-clone version was.
@export var bank_per_parries := 3
@export var bank_perfect_bonus := 2
# Beat 6: the breath before he starts again.
@export var beat_time := 0.60
# What parrying a yellow costs. More than any block in the game: if it empties the bar the existing
# guard break fires, which is self-inflicted and legible.
@export var feint_stamina := 40.0

#BEAM RUSH (CarterBeamRush, seconds and px)
# Four clones at the top of the ring charge beams, lock them onto the player and fire them, volley after
# volley, and once in the attack he teleports in beside the player and strikes. The player is NOT locked
# here, unlike the barrage: walking or dashing out of the locked lines is the only answer to the beams,
# which can't be blocked or parried, and his strike is the one parry in the attack.
#
# THE ESCAPE IS beam_escape + messatsu_travel: 0.90 s from the lines locking to the heads landing. From
# where the four cross, the player's hurtbox has to be 180 px plus its own reach across a beam off every
# one of them. A dash and a step after it does that from anywhere in the ring in 0.63 s at worst - up
# between the middle two clones, where the lines fan out all round the player - which leaves 0.27 s to
# react in; walking alone does it in time from about 80% of the ring. The defence suite's beam_rush mode
# walks that model over the whole ring, so re-run it before shortening beam_escape.
#
# THE ATTACK ENDS ON A VOLLEY COUNT OR A BREAK, NEVER ON A CLOCK. A parry costs about 0.73 s of wall
# clock (PlayerDefense's hit-stop and slow), and a count is the one bound that is frame-rate-, freeze-
# and hit-stop-independent. A player who never moves doesn't escape it; they die to it.
#
# STRIKE_SHOW IS AT THE SAME FLOOR AS CLONE_SHOW AND MUST NOT GO BELOW IT: 0.36 s is the last value at
# which the read is a read. The strike comes at a random moment in one charge, from strike_from into it
# to strike_latest(), so its blow lands at least strike_clear before the lines lock: never while a beam
# is out, and with the whole escape still ahead of a player who stood rooted to parry it.
@export var beam_summon := 0.70
# Each volley's charge, as long as his own Messatsu's.
@export var beam_charge := 1.20
# From the lines locking to the four firing, all of it under the yellow badge: the badge goes up on the
# lock (CarterBeamRush._lock).
@export var beam_escape := 0.80
# How long each volley's beams hurt, from the heads landing to their fade. Against the player's 1 s of
# i-frames, a player who stays in them takes two hits a volley.
@export var beam_live := 1.20
@export var beam_volleys := 3
@export var strike_show := 0.36
@export var strike_dash := 0.08
@export var strike_gap := 0.06
# How far beside the player he materialises, along x, and how far off their line on y.
@export var strike_range := Vector2(190, 260)
@export var strike_y_jitter := 40.0
# Half-width of the box around the latched point the player has to still be in for it to connect.
@export var strike_reach := 120.0
# NOT UNDER 0.30. A beam hurts up to its volley's last frame, and his strike doesn't pass the
# i-frames, so his blow has to land more than the player's 1.0 s of them after it: messatsu_fade +
# strike_from + strike_show + strike_dash is 1.04 s at 0.30. At 0.15 it was 0.89 s, and a beam hit
# in a volley's last 0.11 s swallowed an on-time parry of the strike whole (the defence suite's
# carter_strike_iframes).
@export var strike_from := 0.30
@export var strike_clear := 0.30
@export var beam_end := 0.40
# The punish window: at least his body's BREAK.broken_time for a Break - that number and no other -
# and recover_spent for a rush simply sat through. His Break IS his punish window, which is why the
# gauge unlocks 0.5 s after it rather than Eric's 3.
var recover_break: float:
	get:
		return CarterAkumaCharacterBody.BREAK.broken_time
# A breath, not a window to plan on: he is typically 400-800 px off, and in 1.5 s a player reaches him
# for a punch or two and rarely the POW. At 2.5 s every rush sat through paid the POW and the finisher
# (measured 2026-10-05), which made the attack that is all escape worth a third of his health.
@export var recover_spent := 1.5

#THE MESSATSU (CarterMessatsu, seconds and px)
# The lights go out, he reappears across the ring and charges a beam locked onto the player, and the
# lights come back on with the badge already over his head. The beam comes out messatsu_tell later and
# its head lands messatsu_travel after that: 0.40 s from the lights to the first hit, which is the
# read, at or over the 0.36 s floor the other two attacks keep. Then one hit per surge, messatsu_tick
# apart, messatsu_hits in all. The player is never locked here.
# MESSATSU_TRAVEL IS THE DODGE DIAL, NOT THE WIDTH. 0.10 s is six frames, and only a dash whose three
# frames all fall inside them clears the beam: about four frames of dodge, timed before it is seen.
# THE TICK SITS EXACTLY ON PlayerDefense.parry_mash_lockout (0.5 s), SO THE REARM IS LOAD-BEARING.
# The fight re-arms the parry as the lights come on and messatsu_rearm_delay after every hit, and
# nowhere else. Between two hits that gives three zones: a press up to 0.08 s late for the last hit is
# wiped by the rearm and costs nothing; a press from 0.08 to 0.26 s after it whiffs and costs the next
# hit only; and the last 0.24 s before a hit is its parry window. Do not widen this into a per-press
# rearm or the string becomes a mash-fest.
# The rest must hold: messatsu_pulse_travel over parry_window plus a frame, so pressing as a surge
# leaves his palms is too early; tick - rearm - window at least 0.15 s of early zone; and the rearm
# before the next surge leaves (rearm < tick - pulse_travel). The defence suite's messatsu mode checks
# all of it.
@export var messatsu_charge := 1.20
@export var messatsu_tell := 0.30
@export var messatsu_travel := 0.10
@export var messatsu_tick := 0.50
# 7 since 2026-10-05 (6 before), and no more: a player who never moves takes all of them, and at 8 the
# string alone would kill one from full health, which the Beam Rush's 2026-09-30 rule forbids for it.
@export var messatsu_hits := 7
@export var messatsu_rearm_delay := 0.08
@export var messatsu_pulse_travel := 0.30
@export var messatsu_end_hold := 0.20
@export var messatsu_fade := 0.30
# How far from the player he may reappear, so the charge is a thing across the ring and never one on
# top of them.
@export var messatsu_min_range := 520.0

var player_defeated := false
var cycles_started := 0
# Locked once, at the top of each cycle, so a hit landing mid-sequence can't change what the rest of
# it does.
var cycle_yellows := 0
# The pre-fight lines' balloon, which a held skip takes down, and whether those lines have handed
# over to the VS card yet.
var pre_fight_balloon: Node
var pre_fight_over := false
# His gauge broke with no attack running to end - which only the defence suite ever does, parrying
# between attacks: the Break is owed, and the next hand-over cashes it as a Break window
# (take_break_owed).
var break_owed := false

var warned := {}


func _ready() -> void:
	# Built here rather than in his scene, which nothing in this fight edits.
	var juggled := CarterJuggled.new()
	juggled.name = "Juggled"
	juggled.body = CarterAkumaCharacterBody
	juggled.hurtbox = CarterAkumaCharacterBody.get_node("Hurtbox")
	juggled.state_machine = self
	add_child(juggled)
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


#THE CYCLE

# His lines call no beats, so the intro hands the dialogue over and waits for it to end.
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


func _on_dialogue_ended(_dialogue: Object) -> void:
	pre_fight_over = true
	var intro = states.get("Intro")
	if intro:
		intro.lines_over()
	VsCard.play_intro(self, "carter", post_dialogue_pre_fight_timer.start)


func _on_post_dialogue_pre_fight_timer_timeout() -> void:
	CarterAkumaCharacterBody.start_music()
	start_cycle()


func start_cycle() -> void:
	cycles_started += 1
	cycle_yellows = yellow_count()
	on_child_transition(current_state, next_attack())


# Whether `attack`, ending without a Break, hands straight on to the next attack (chain_attacks). The
# attack asks with what it is about to hand his window - `recover` already prepared - so the bank its
# parries earned decides it: one that would kill him goes to the window, where his defeat is handled.
func chains_on(attack: State, recover: State) -> bool:
	return chain_attacks and CHAINED_ATTACKS.has(str(attack.name)) and not recover.from_break \
		and recover.banked_damage() < CarterAkumaCharacterBody.boss_health


# The hand-on itself: the lights are coming up or the four are gone, what the attack's parries banked is
# cashed - as his window would cash it - and the next attack starts at once.
func chain_on(recover: State) -> void:
	var banked: int = recover.banked_damage()
	recover.prepare(0, 0, 0, 0)
	if banked > 0:
		CarterAkumaCharacterBody._apply_damage(banked)
	start_cycle()


# A strict rotation, never a random pick, and never gated on his health. Cycle 1 is always the
# barrage: it is the teaching round, and the Beam Rush and the Messatsu both assume the player already
# knows what a red badge on Carter means. The Beam Rush comes twice running since 2026-10-06: the four
# dissolve and gather again for a second set, which is three more volleys to walk out of and a second
# strike - beams that cost when they catch and pay nothing when escaped. With the attacks chained
# (chain_attacks) the rotation is his combo: barrage, Beam Rush, Beam Rush, Messatsu, then his window.
const ATTACK_ROTATION := ["RagingDemon", "BeamRush", "BeamRush", "Messatsu"]


func next_attack() -> String:
	return ATTACK_ROTATION[maxi(cycles_started - 1, 0) % ATTACK_ROTATION.size()]


# The one difficulty dial. Cycle 1 is all red - it teaches the rhythm - and every barrage after it
# has PALE_X_ROUND lies in pale_x_clone_count clones (3/5/6 of 15 by his health until 2026-10-05, 6 of
# 18 then, 10 of 24 since 2026-10-06). No two feints may be adjacent (CarterRagingDemon._build_pattern):
# 10 of 23 slots still leaves 1001 arrangements, where a lie in every other slot would be one fixed
# pattern the player learns rather than reads.
const PALE_X_ROUND := 10


func yellow_count() -> int:
	if cycles_started <= 1:
		return 0
	return PALE_X_ROUND


# How many clones this cycle's barrage throws.
func barrage_clones() -> int:
	return clone_count if cycles_started <= 1 else pale_x_clone_count


# Light to light. At 0.62 s this is inside PlayerDefense.parry_mash_lockout's reach, so a press that
# whiffs late on one clone WOULD lock the guard out of the next one if the fight didn't re-arm the
# parry as each light comes up.
func clone_interval() -> float:
	return clone_show + clone_dash + clone_gap


# The latest the Beam Rush's strike may appear in its charge: its blow lands strike_clear before the lock.
func strike_latest() -> float:
	return maxf(beam_charge - strike_show - strike_dash - strike_clear, strike_from)


# When the Messatsu's hit `k` lands, counted from the frame it fires: k 0 is the head arriving, 1 to 5
# the surges after it.
func messatsu_hit_time(k: int) -> float:
	return messatsu_travel + k * messatsu_tick


# The punish window the round earned. Later rounds have fewer reds to parry, so the longest possible
# window shrinks as he gets more dangerous.
func recover_window(reds_parried: int, reds_missed: int) -> float:
	return clampf(recover_base + recover_parry_bonus * reds_parried - recover_miss_penalty * reds_missed,
		recover_min, recover_max)


# EVERY WINDOW HE OPENS IS AT LEAST THIS LONG (the user, 2026-10-06: every opening long enough to walk in
# and land three punches, and three punches always the uppercut). From `distance` px off his feet,
# walking alone: measured, the third punch lands 0.8-1.1 s + distance / 600 s after the walk starts,
# depending on the line in, and a reaction to his window opening comes on top. The Messatsu kneels him
# at least messatsu_min_range away and as far as the ring is wide, where a read-earned 1.5 s left
# nothing to walk in on.
const WALK_IN_BASE := 1.2
const WALK_IN_REACTION := 0.30


func walk_in_time(distance: float) -> float:
	var player := get_player()
	var speed: float = player.get_script().SPEED if player else 600.0
	return WALK_IN_BASE + distance / speed + WALK_IN_REACTION


# His one punish window per cycle.
func is_recovering() -> bool:
	return current_state == states.get("Recover")


func flinch() -> void:
	if is_recovering():
		current_state.flinch()


# His Break gauge filled. Called deferred from CarterAkumaScript._on_break: the gauge fills inside a
# physics flush, where states can't switch. Whichever attack is running ends on the spot and hands him
# to his Break's window, open, by the user's call (2026-09-27): "the attack should immediately stop and
# Carter should be hittable". Each one's on_broke() takes everything of it with it. The sting and the
# gauge's own BREAK! go off now either way.
func on_break() -> void:
	CarterAkumaCharacterBody.play_break_sting()
	if ATTACK_ROTATION.has(str(current_state.name)):
		current_state.on_broke()
		return
	break_owed = true


func break_beam_rush() -> void:
	on_break()


# A Break owed, handed to the window that cashes it, and cleared.
func take_break_owed() -> bool:
	var owed := break_owed
	break_owed = false
	return owed


# The finisher ended his recovery early: he stays down, staggered, then starts the next cycle.
func stagger_then_start_cycle(stagger_time: float) -> void:
	recover_timer.stop()
	on_child_transition(current_state, "Idle")
	# Idle starts the beat before the next Demon; the stagger replaces it.
	beat_timer.stop()
	# Held on the recoil frame through the stagger instead of the idle loop Idle starts.
	CarterAkumaCharacterBody.play_anim(&"hit", &"idle")
	finisher_stagger_timer.start(stagger_time)


func _on_finisher_stagger_timer_timeout() -> void:
	start_cycle()


# The tiered finisher's first uppercut (CarterAkumaScript.begin_juggle), out of a Break window.
func enter_juggled() -> void:
	var juggled: State = states["Juggled"]
	if CarterAkumaCharacterBody.defeated or current_state == juggled:
		return
	for timer in [recover_timer, finisher_stagger_timer, beat_timer]:
		timer.stop()
	on_child_transition(current_state, "Juggled")


# Down after a juggle, he picks himself up where he crashed - staggered, as after any finisher - and
# his next attack comes `delay` after this. A Timer can't start at 0.
func after_juggle(delay: float) -> void:
	stagger_then_start_cycle(maxf(delay, 0.01))


# The one switch past the fight being decided: juggled and killed in the air, he lands into his
# defeat rather than snapping to its pose mid-flight.
func land_juggled(final_state_name: String) -> void:
	var final_state: State = states.get(final_state_name)
	if final_state == states.get("Defeated"):
		final_state.lying = true
	current_state.Exit()
	final_state.Enter()
	current_state = final_state


func get_player() -> Node2D:
	return get_tree().current_scene.get_node_or_null("Arena/MainPlayer/CharacterBody2D")


# Everything he sends out lives under the fight scene, so a finisher's freeze holds it and the end of
# the fight takes it away.
func add_hazard(hazard: Node2D, at: Vector2, layer: Node2D) -> void:
	hazard.add_to_group(HAZARD_GROUP)
	layer.add_child(hazard)
	hazard.global_position = at.round()


#THE PLAYER API

# Held for a parry-only sequence: no walking, no dash, no punch, while the guard, its parry window
# and the streak behind it all keep working. It must never be confused with is_grabbed or is_talking,
# which PlayerScript._input returns on BEFORE the block branch - reusing either would make the
# sequence unparryable with no error at all.
func lock_player() -> void:
	var player := get_player()
	if player and player.has_method("lock_actions"):
		player.lock_actions()
	else:
		_warn_once("lock", "Carter: player has no lock_actions(); the Demon can't root them")


func unlock_player() -> void:
	var player := get_player()
	if player and player.has_method("unlock_actions"):
		player.unlock_actions()


# Turned to meet each clone as its light comes up. It changes nothing about whether the parry lands -
# the hit's origin is the player's own hurtbox centre, so any facing answers it - it is the drama of
# the sequence, and unlock_actions() clears it.
func face_player_at(point: Vector2) -> void:
	var player := get_player()
	if player and player.has_method("face_point"):
		player.face_point(point)


func clear_player_facing() -> void:
	var player := get_player()
	if player and player.has_method("clear_face_point"):
		player.clear_face_point()


# The darkness draws above the floor and below the fighters, and the player's own stage is z 0, so
# the sequence lifts it over the dark and puts it back. The only thing this fight writes to a node it
# doesn't own, and CarterRagingDemon.release() is what undoes it.
func set_player_stage_z(z: int) -> void:
	var player := get_player()
	if player == null:
		return
	var stage := player.get_parent()
	if stage is CanvasItem:
		stage.z_index = z


func player_stage_z() -> int:
	var player := get_player()
	if player == null:
		return 0
	var stage := player.get_parent()
	return stage.z_index if stage is CanvasItem else 0


# Called on the exact frame each clone's light comes up, every one of them, every round. PlayerDefense counts
# a press that didn't parry against the next one for parry_mash_lockout (0.5 s), and every further
# press inside that pushes the clock forward, so without this a player who whiffs on clone N can be
# mathematically unable to parry clone N+1.
# It deliberately does NOT fix mashing WITHIN one clone's window: an early press still whiffs and
# still locks that clone out. Do not widen this into a per-press re-arm or the fight becomes a
# mash-fest.
func rearm_parry() -> void:
	var defense := _defense()
	if defense and defense.has_method("rearm_parry"):
		defense.rearm_parry()
	else:
		_warn_once("rearm", "Carter: PlayerDefense has no rearm_parry(); a whiffed clone can lock out the next")


func end_parry_streak() -> void:
	var defense := _defense()
	if defense and defense.has_method("end_parry_streak"):
		defense.end_parry_streak()
	else:
		_warn_once("streak", "Carter: PlayerDefense has no end_parry_streak(); a parried feint keeps the streak")


func drain_stamina(amount: float) -> void:
	var defense := _defense()
	if defense and defense.has_method("drain_stamina"):
		defense.drain_stamina(amount)
	else:
		_warn_once("stamina", "Carter: PlayerDefense has no drain_stamina(); a parried feint costs nothing")


# Returns whether the signal was there. When it wasn't, the caller polls the block action in
# Physics_Update instead - and only there, since polling in both would fire the punish twice.
func connect_block_presses(handler: Callable) -> bool:
	var defense := _defense()
	if defense and defense.has_signal("block_pressed"):
		if not defense.block_pressed.is_connected(handler):
			defense.block_pressed.connect(handler)
		return true
	_warn_once("presses", "Carter: PlayerDefense has no block_pressed signal; feints fall back to polling")
	return false


func disconnect_block_presses(handler: Callable) -> void:
	var defense := _defense()
	if defense and defense.has_signal("block_pressed") and defense.block_pressed.is_connected(handler):
		defense.block_pressed.disconnect(handler)


func _defense() -> Node:
	var player := get_player()
	return player.get("defense") if player else null


func _warn_once(key: String, message: String) -> void:
	if warned.has(key):
		return
	warned[key] = true
	push_warning(message)


#THE END OF THE FIGHT

func enter_defeated() -> void:
	_end_fight("Defeated")


# The player lost: he turns his back on them and the emblem burns. The barrage's darkness is handed
# straight on to his victory pose rather than lifted - they always die in the dark, since only the
# clones can hurt them, and the lights never come back up.
func enter_player_defeated() -> void:
	_end_fight("Victory", true)
	player_defeated = true


func _end_fight(final_state_name: String, keep_dark := false) -> void:
	# Before anything else: a terminal path that never reaches RagingDemon.Exit() still has to free
	# the player and take the curtain down. A player left locked is unrecoverable. The one exception
	# to the curtain is his own win, which keeps it (RagingDemon.release).
	var demon: State = states.get("RagingDemon")
	if demon:
		demon.release(keep_dark)
	# The same for the Beam Rush, and for the same reason: a terminal path that skips its Exit()
	# would leave four live curtains and a parry tell standing on a finished fight.
	var beam_rush: State = states.get("BeamRush")
	if beam_rush:
		beam_rush.release()
	# And the Messatsu, with the Demon's stay-dark rule for his win: it never leaves a player to die in
	# the dark, but if one ever did, the dark goes on into his victory pose rather than lifting.
	var messatsu: State = states.get("Messatsu")
	if messatsu:
		messatsu.release(keep_dark)
	for hazard in get_tree().get_nodes_in_group(HAZARD_GROUP):
		hazard.queue_free()
	# In the air, he finishes his fall and his crash first, and lands into it (land_juggled).
	var juggled: State = states.get("Juggled")
	if juggled and current_state == juggled:
		juggled.final_state = final_state_name
	else:
		on_child_transition(current_state, final_state_name)
	# After the transition, not before: entering Idle starts the beat timer, which must not survive
	# the end of the fight.
	for timer in [post_dialogue_pre_fight_timer, recover_timer, finisher_stagger_timer, beat_timer]:
		timer.stop()
