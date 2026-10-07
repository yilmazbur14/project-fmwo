extends Node

# Liam's own phase, after beast Bixby coughs him up. The takeover once (LiamTakeover: his lines, the staff, the earth
# pillar, the ride to the top of the ring and the row rising either side of him, or its end state at once in the test
# scene), then his wind's reset and his four attacks in a loop that never ends, from the top of his pillar,
# ATTACK_ROTATION: Tsunami (attack 1), Tremors (2), Firestorm (3), Lunge (4), then 1 again. The floor carries through
# it: the tsunami floods the ring, attack 2 freezes the flood, attack 3 melts the ice and boils the water off into
# steam, and attack 4 hides in the steam and clears it as it ends.
#
# THE PILLAR IS WHAT THE PLAYER PUNCHES (LiamPillar asks take_pillar_hit). An attack either runs out on its own
# (attack_finished) or is cut by the round's first pillar hit: the attack stops and everything it sent out collapses
# harmlessly (its interrupt()), and he Wobbles for up to wobble_time and up to round_hits hits. Either way the attack is
# over: the pillar goes shielded and his RoundBlast's wind throws the player to the bottom middle (RESET_SPOT), unhurt,
# before the next attack in the loop (a player already there gets no gust). The hit count carries over across rounds;
# the hits_to_topple-th sends him Falling to LAND_SPOT, into Downed (his punish window), or into Broken if a Break was
# banked while he was up there (break_owed); a parried lunge opens the same window where he stood. The floor stays
# through a window, only the player's footing on it is normal while he's down. After a window he GetsUp - blows the
# player to the bottom middle and rides a new pillar up, or teleports back onto his stump - and the loop goes on with
# the attack after the one he was knocked out of: it never starts over.
# The pillar is shielded from a round's end, and from each attack's start, until that attack's first live threat (in the
# Tsunami, until its first wave crashes on the bottom rope; in the Firestorm, until his blow lets go, wall_release after
# IGNITION).
#
# WHAT EVERY ATTACK STATE KEEPS: Enter(), an idempotent interrupt() that stops it and makes everything it sent out
# collapse harmlessly, an Exit() that leaves the same end state, and attack_finished(self) when it runs out. A new attack
# is one more name in ATTACK_ROTATION. Every state is built here in code; every wait in this fight is a node-bound tween
# or a clock stepped in Physics_Update, so a pause and a finisher's freeze hold all of it: nothing may use
# get_tree().create_timer().

const ParryTell := preload("res://Scripts/ParryTell.gd")
const LiamTakeover := preload("res://Scripts/States/Liam/LiamTakeover.gd")
const LiamIdle := preload("res://Scripts/States/Liam/LiamIdle.gd")
const LiamTsunami := preload("res://Scripts/States/Liam/LiamTsunami.gd")
const LiamTremors := preload("res://Scripts/States/Liam/LiamTremors.gd")
const LiamFirestorm := preload("res://Scripts/States/Liam/LiamFirestorm.gd")
const LiamLunge := preload("res://Scripts/States/Liam/LiamLunge.gd")
const LiamWobble := preload("res://Scripts/States/Liam/LiamWobble.gd")
const LiamRoundBlast := preload("res://Scripts/States/Liam/LiamRoundBlast.gd")
const LiamFall := preload("res://Scripts/States/Liam/LiamFall.gd")
const LiamDowned := preload("res://Scripts/States/Liam/LiamDowned.gd")
const LiamBroken := preload("res://Scripts/States/Liam/LiamBroken.gd")
const LiamJuggled := preload("res://Scripts/States/Liam/LiamJuggled.gd")
const LiamGetUp := preload("res://Scripts/States/Liam/LiamGetUp.gd")
const LiamDefeated := preload("res://Scripts/States/Liam/LiamDefeated.gd")
const LiamGust := preload("res://Scripts/LiamGust.gd")

const TAKEOVER_DIALOGUE := "res://Dialogue/LiamTakeover.dialogue"
# Everything he sends out: waves, ridges and their effects.
const HAZARD_GROUP := "liam_hazard"
const ATTACK_ROTATION: Array[StringName] = [&"Tsunami", &"Tremors", &"Firestorm", &"Lunge"]
# Every attack state, in the rotation or not yet (a test can enter one that isn't wired): what is_attacking() asks.
const ATTACK_STATES: Array[StringName] = [&"Tsunami", &"Tremors", &"Firestorm", &"Lunge"]
# Nothing breaks him in these, and nothing is banked for later either.
const NO_BREAK_STATES := ["Takeover", "Broken", "Juggled", "Defeated"]

#WHERE THINGS ARE (px)
# The pillar's floor line at the top of the ring: his feet STAND_HEIGHT over it, at y 198.
const PERCH := Vector2(960, 348)
# Where he lands when it topples.
const LAND_SPOT := Vector2(960, 480)
# The inside edges of the ropes.
const ROPES := Rect2(113, 114, 1692, 855)
# Where his feet may be on the ground: a shove or a Break slide keeps him inside it (stand_rect(), which keeps him off
# the row while it stands).
const STAND_RECT := Rect2(220, 300, 1480, 620)
# The player's centre while punching his pillar: straight in front of it against the row's face, the only place his
# pillar can be reached from while the row stands (addendum 3, A.2).
const FRONT_SPOT := Vector2(960, 402)
# Attack 4: where his lunges may come from (wider than twice lunge_distance, so one side of the player always fits),
# where a player hung on his staff may be held, where his water blast washes them down to, and the z their stage is
# lifted to while they hang (over the row and his staff, under the steam).
const LUNGE_AREA := Rect2(170, 440, 1580, 480)
const HOLD_AREA := Rect2(150, 200, 1620, 700)
const WATER_BLAST_SPOT := Vector2(960, 900)
const IMPALE_Z := 1
# Where his wind puts the player after every attack and at the start of the fight, the bottom middle: the spot every
# attack starts from (addendum 4).
const RESET_SPOT := WATER_BLAST_SPOT

#THE ROUND
@export var wobble_time := 2.0
@export var steady_time := 0.5
@export var round_hits := 3
@export var hits_to_topple := 6
@export var blast_windup := 0.3
@export var launch_time := 0.5
@export var launch_skip := 40.0
# 0.4 after the reset lands (0.6 before addendum 4, when only a round ended in a blast).
@export var resume_delay := 0.4
# While he's down in a window the player walks normally on any ice (the user's question 4): off, it stays slippery.
@export var normal_footing_when_down := true
#THE HUD
@export var pillar_hud_fade_alpha := 0.3
#THE ROW (LiamRow): its rise, its ripple out from his pillar, and the top of where he may stand while it is up
@export var row_rise_time := 0.8
@export var row_ripple := 0.05
@export var row_stand_top := 420.0
#ATTACK 1: THE TSUNAMI
# 12 waves (the user's question 3, addendum 4): the ring floods in 6 of them, so more only drag.
@export var tsunami_time := 9.6
@export var wave_speed := 600.0
@export var wave_height := 360.0
# Clear floor between one wave's top and the next one's front, the notch a zip up the middle crosses in (the user's
# question 1, addendum 4): a corner every 48 frames against the dash immunity's 36-frame cooldown; walking across it
# needs at least 93 px and exact timing, so it still takes a dash.
@export var wave_gap := 120.0
# How many waves fill the ring: each adds its share as its front crashes on the bottom rope.
@export var flood_waves := 6
@export var wave_tell := 0.45
@export var wave_carry := 0.35
# The pillar opens as this wave's front crashes on the bottom rope: the fifth, about 5.1 s in, so the way to it crosses
# the waves the player's side sends (the tuning round of 2026-10-04, difficulty 7; the first's crash, 1.9 s, was the
# user's pick for the gate the same day).
@export var tsunami_gate_wave := 5
@export var wave_collapse_time := 0.3
#ATTACK 2: FLOOD, FREEZE AND THE TREMOR MAZE (plan section 6.1; seconds from its start)
@export var settle_time := 0.3
@export var breath_start := 0.3
@export var freeze_speed := 1000.0
@export var downdraft_speed := 1200.0
@export var downdraft_launch_above := 700.0
@export var crack_slam := 0.8
@export var heave_slam := 1.4
@export var crack_time := 0.3
# A slam every 0.45 s (0.6 before addendum 4): with march_step, the walls close in at 75.6 px/s (60 before addendum 5).
@export var slam_interval := 0.45
# 11.25 s from the heave, 25 slams (9.5 before addendum 5): long enough for the stream to bring 5 walls in all.
@export var tremor_time := 11.25
# 240 slides the player about 24 px off a ridge on the ice, less than any corridor's 40 px of room.
@export var tremor_bounce := 240.0
@export var pulse_shake := 3.0
# The stream (addendum 5): the two opening walls hold march_delay_slams slams after the heave, then every wall marches
# march_step px down a slam, gliding the whole slam_interval at an even speed with march_glide (the user's question 1;
# off, a lurch over march_lurch_time on each slam), and a block whose bottom reaches march_floor_y sinks there. Each
# time the newest wall has marched stream_every steps, a new one tells at the top and heaves a slam later (the user's
# question 2): at the defaults 34 px a slam, 75.6 px/s (27 and 60 before, a quarter slower), a new wall every 3.15 s,
# 238 px apart with 166 px corridors. Its gap is stream_gap wide. A wall stepping into a player pinned against the
# bottom hurts them once and crumbles, or with march_pinned_crumbles off stops just above them.
@export var march_delay_slams := 2
@export var march_step := 34.0
@export var march_lurch_time := 0.15
@export var march_floor_y := 975.0
@export var march_glide := true
@export var march_pinned_crumbles := true
@export var stream_every := 7
@export var stream_gap := 240.0
#ATTACK 3: THE FIRESTORM (addendum 3 B; seconds on its own clock)
@export var blow_time := 0.9
@export var ignite_time := 0.3
@export var firestorm_time := 12.0
@export var burnout_time := 0.6
@export var interrupt_burnout := 0.3
# How many tornados (the user's question 4): 4 or 5 (LiamFirestormLayout.WALL_X and START_ALONG). Not 5 with the wall:
# its lenses are about a dash deep, and no timing of the stop-and-dash route through one comes out unhurt (2026-10-06).
@export var tornado_count := 4
# The wall of fire (the user's option A, 2026-10-04): from his blow his downdraft (downdraft_speed, and a player above
# downdraft_launch_above thrown down, as in Tremors) holds the player at the bottom while the tornados rise in a line
# and catch fire; wall_release after IGNITION it lets go and the pillar opens, 0.5 s after the first pair of rings
# (quake_first + 0.5: the user's 2.0 s wait). wall_hold later the line breaks, the tornados gliding out to their roam
# starts over wall_break_time, and then they roam.
@export var wall_release := 0.8
@export var wall_hold := 1.5
@export var wall_break_time := 1.0
# From the end of that glide they roam LiamFirestormLayout.TRACK together at tornado_speed px/s (the user's question 3
# of addendum 5), each drifting up to tornado_lean px off it toward the player at tornado_lean_speed px/s (its question
# 4; 0 is a fixed carousel), so a corner can't be camped.
@export var tornado_speed := 200.0
@export var tornado_lean := 180.0
@export var tornado_lean_speed := 90.0
@export var tornado_pull := 450.0
@export var tornado_pull_full := 120.0
@export var tornado_pull_radius := 460.0
# Under the 600 px/s walk, so a player can always make 120 px/s in any direction.
@export var tornado_pull_cap := 480.0
@export var tornado_pull_ramp := 0.6
@export var tornado_dead_zone := 30.0
@export var front_calm_radius := 120.0
@export var front_calm_fade := 80.0
@export var tornado_fling := 900.0
@export var tornado_fling_time := 0.25
# 0.3, not 0.5: the user's 2.0 s wait for the wall (2026-10-04).
@export var quake_first := 0.3
@export var quake_interval := 1.5
@export var quake_speed := 200.0
# 120 rather than the addendum's 60 (the user's pick with the approved art): at 60 Bixby's ring layout has only four
# segments and reads as a box for about 0.3 s.
@export var quake_start_radius := 120.0
@export var quake_max_radius := 360.0
@export var quake_die_time := 0.3
@export var melt_speed := 700.0
#ATTACK 4: THE STEAM LUNGE (addendum 3 C; seconds on its own clock)
@export var vanish_time := 0.8
@export var stump_risen := 0.3
@export var lunge_wait_range := Vector2(1.5, 3.0)
# The badge to the impact (the user's question 2): a parry pressed 0.16 to 0.40 s after the badge lands.
@export var lunge_lead := 0.40
@export var lunge_show := 0.12
@export var lunge_distance := 300.0
@export var lunge_rise := 60.0
# Lunges dodged before he goes back up (the user's question 3).
@export var lunge_count := 3
# -1 draws the waits and the sides at random; any other value repeats them.
@export var lunge_seed := -1
@export var whiff_time := 0.35
@export var whiff_overshoot := 80.0
@export var parry_recoil := 60.0
@export var impale_call_at := 0.45
@export var sky_fire_at := 0.9
@export var burn_ticks := 3
@export var burn_interval := 0.5
@export var water_blast_at := 2.4
@export var jet_time := 0.15
# The player hangs where the impale left them while he aims the water blast up at them (the user's pick); off, they
# stay on his staff tip through it.
@export var blast_hangs_player := true
@export var teleport_time := 0.35
@export var steam_clear_time := 1.2
@export var parry_steam_clear := 0.8
#THE STEAM (LiamSteam)
# By the end of attack 3 the ring is "filled with steam and very hard to see" (the user): 0.95 over the tile's two layers
# at steam_layer_gain covers about 97% of the ring outside the player's bubble at 0.9 or more (they were 0.85 and 0.65,
# a light haze).
@export var steam_max := 0.95
@export var steam_layer_gain := 1.2
@export var fall_steam_clear := 1.0
# How far fire glows through the steam, 0 to 1 (the user's question 5): 0 hides the fire in it too.
@export var steam_glow_through := 0.85
#THE ICE (PlayerScript.set_ice)
@export var ice_accel := 1800.0
@export var ice_friction := 1200.0
@export var ice_dash_carry := 450.0
#THE FALL AND THE WINDOW
@export var crumble_time := 0.5
@export var fall_time := 0.6
# 2.5 s, 4.0 until the tuning round of 2026-10-04 (difficulty 7).
@export var downed_time := 2.5
@export var stand_time := 0.4
@export var rise_time := 0.6
@export var ride_speed := 450.0
@export var ride_time_range := Vector2(0.3, 1.6)

var body: CharacterBody2D
var states := {}
var current_state: State
var player_defeated := false
# Where the rotation is: the next attack is ATTACK_ROTATION[rotation_index % size].
var rotation_index := 0
# Tremors runs so far, the whole fight: where the next run's walls start in the gap order (LiamTremorPatterns.GAP_CYCLE).
var tremor_runs := 0
# Pillar hits since this pillar rose, and in this round.
var pillar_hits := 0
var round_hits_taken := 0
# His gauge broke while he was up there: his fall lands him in Broken.
var break_owed := false
# The takeover's balloon, which its skip takes down.
var takeover_balloon: Node
# A wave's carry on the player: px/s added each step for the seconds left.
var carry_velocity := Vector2.ZERO
var carry_left := 0.0
# The air blast's throw, on his own clock.
var launch: Tween
var launched_player: Node2D
var warned := {}


func _ready() -> void:
	body = get_parent()
	_add_state(LiamTakeover.new(), "Takeover")
	_add_state(LiamIdle.new(), "Idle")
	_add_state(LiamTsunami.new(), "Tsunami")
	_add_state(LiamTremors.new(), "Tremors")
	_add_state(LiamFirestorm.new(), "Firestorm")
	_add_state(LiamLunge.new(), "Lunge")
	_add_state(LiamWobble.new(), "Wobble")
	_add_state(LiamRoundBlast.new(), "RoundBlast")
	_add_state(LiamFall.new(), "Fall")
	_add_state(LiamDowned.new(), "Downed")
	_add_state(LiamBroken.new(), "Broken")
	_add_state(LiamJuggled.new(), "Juggled")
	_add_state(LiamGetUp.new(), "GetUp")
	_add_state(LiamDefeated.new(), "Defeated")
	current_state = states["Takeover"]
	# Deferred until the scene is up: the takeover reads the player, Bixby and the pillar off it.
	current_state.Enter.call_deferred()


# The body is this node's parent, so it isn't ready yet: its hurtbox is looked up, not read off it.
func _add_state(state: State, state_name: String) -> void:
	state.name = state_name
	state.body = body
	state.state_machine = self
	if "hurtbox" in state:
		state.hurtbox = body.get_node("Hurtbox")
	add_child(state)
	states[state_name] = state


func _process(delta: float) -> void:
	if current_state:
		current_state.Update(delta)


func _physics_process(delta: float) -> void:
	if carry_left > 0.0:
		carry_left -= delta
		var player := get_player()
		if player:
			player.add_drift(carry_velocity)
	if current_state:
		current_state.Physics_Update(delta)


func on_child_transition(state, new_state_name):
	if state != current_state:
		return
	# Defeat, his or the player's, is terminal: a late clock must never restart the fight.
	if current_state == states.get("Defeated") or player_defeated:
		return
	var new_state = states.get(new_state_name)
	if !new_state:
		return
	if current_state:
		current_state.Exit()
	# The rotation follows the attack he is in, however he came to it.
	var attack := ATTACK_ROTATION.find(StringName(new_state_name))
	if attack >= 0:
		rotation_index = attack
	new_state.Enter()
	current_state = new_state


#THE TAKEOVER'S LINES

# His lines call the takeover's beats, so it passes itself along to the dialogue. Their natural end finishes it.
func show_takeover_dialogue(takeover: State) -> void:
	DialogueManager.dialogue_ended.connect(_on_takeover_dialogue_ended, CONNECT_ONE_SHOT)
	takeover_balloon = DialogueManager.show_dialogue_balloon(load(TAKEOVER_DIALOGUE), "start", [takeover])


# A held skip's way out of the lines: their natural end, disconnected so it can't come again.
func end_takeover_dialogue() -> void:
	if DialogueManager.dialogue_ended.is_connected(_on_takeover_dialogue_ended):
		DialogueManager.dialogue_ended.disconnect(_on_takeover_dialogue_ended)


func _on_takeover_dialogue_ended(_dialogue: Object) -> void:
	var takeover = states.get("Takeover")
	if takeover:
		takeover.finish_cut()


#THE ROTATION

# The takeover is over: his wind's reset, which hands on to attack 1.
func begin_fight() -> void:
	rotation_index = ATTACK_ROTATION.size() - 1
	on_child_transition(current_state, "RoundBlast")


func idle_then_attack(seconds: float) -> void:
	states["Idle"].beat_left = seconds
	on_child_transition(current_state, "Idle")


func next_attack() -> StringName:
	return ATTACK_ROTATION[rotation_index % ATTACK_ROTATION.size()]


# The next attack in the rotation, from wherever he is on his pillar.
func start_attack() -> void:
	on_child_transition(current_state, next_attack())


# `state` ran out on its own: his wind's reset (RoundBlast), which moves the loop on.
func attack_finished(state: State) -> void:
	if state != current_state:
		return
	on_child_transition(state, "RoundBlast")


func is_attacking() -> bool:
	return current_state != null and ATTACK_STATES.has(StringName(current_state.name))


#THE PILLAR'S ROUNDS

# A punch on the pillar (LiamPillar.take_punch): whether it counts. The round's first hit cuts the attack at once; the
# state switches wait for the flush the punch came in to end. The hit that ends a round, or topples him, shields the
# pillar there and then, so a punch in the same beat is refused.
func take_pillar_hit() -> bool:
	var pillar: Node = body.pillar
	if pillar == null or pillar.shielded or not pillar.parked:
		return false
	var attacking := is_attacking()
	if not attacking and current_state != states["Wobble"]:
		return false
	if attacking:
		current_state.interrupt()
		round_hits_taken = 0
	pillar_hits += 1
	round_hits_taken += 1
	pillar.show_hits(pillar_hits)
	var from: State = current_state
	if pillar_hits >= hits_to_topple:
		pillar.set_shielded(true)
		_switch.call_deferred(from, "Fall")
	elif round_hits_taken >= round_hits:
		pillar.set_shielded(true)
		_switch.call_deferred(from, "RoundBlast")
	elif attacking:
		_switch.call_deferred(from, "Wobble")
	return true


func _switch(from: State, to: String) -> void:
	on_child_transition(from, to)


# The round ran its time out.
func round_over(state: State) -> void:
	if state != current_state:
		return
	body.pillar.set_shielded(true)
	on_child_transition(state, "RoundBlast")


# The blast has thrown the player and the beat after it is over: the next attack.
func blast_finished(state: State) -> void:
	if state != current_state:
		return
	rotation_index += 1
	start_attack()


# He's down off his pillar: into his window, or the Break he banked on the way.
func landed(state: State) -> void:
	if state != current_state:
		return
	on_child_transition(state, "Broken" if take_break_owed() else "Downed")


# His window is over (after `delay` more on the mat): up, and back to the top.
func window_over(state: State, delay := 0.0) -> void:
	if state != current_state:
		return
	states["GetUp"].delay = delay
	on_child_transition(state, "GetUp")


# Where his feet may be on the mat: STAND_RECT, its top brought down to row_stand_top while the row stands.
func stand_rect() -> Rect2:
	var row: Node = body.row
	if not is_instance_valid(row) or not row.is_up():
		return STAND_RECT
	return Rect2(STAND_RECT.position.x, row_stand_top, STAND_RECT.size.x, STAND_RECT.end.y - row_stand_top)


# How long a pillar takes to grind from `from` up to PERCH at ride_speed, inside ride_time_range.
func ride_time_for(from: Vector2) -> float:
	return clampf(from.distance_to(PERCH) / ride_speed, ride_time_range.x, ride_time_range.y)


# Back up on his pillar: the loop goes on with the next attack. A new pillar starts on no hits; the stump a parried
# lunge left him (new_pillar false) is the same pillar raised again, and keeps its count.
func get_up_finished(state: State, new_pillar := true) -> void:
	if state != current_state:
		return
	rotation_index += 1
	if new_pillar:
		pillar_hits = 0
	start_attack()


# His lunge was parried (LiamLunge): knocked down off his pillar where he stood, into his window there (Broken, if a
# Break was banked), and afterwards he goes back up onto his stump rather than riding a new pillar.
func lunge_parried(state: State) -> void:
	if state != current_state:
		return
	states["GetUp"].to_stump = true
	var broken := take_break_owed()
	if not broken:
		states["Downed"].opening_anim = &"parried"
	on_child_transition(state, "Broken" if broken else "Downed")


#HIS WINDOWS AND THE FINISHER

func is_open() -> bool:
	return current_state == states.get("Downed") or current_state == states.get("Broken")


func flinch() -> void:
	if is_open() and current_state.has_method("flinch"):
		current_state.flinch()


# The finisher's uppercut ended his window: staggered on the mat for `stagger_time`, then up.
func end_window(stagger_time: float) -> void:
	window_over(current_state, stagger_time)


#THE BREAK

# His gauge filled (LiamScript._on_break). On the mat he is Broken there and then; with a pillar under him, falling off
# one or lunging out of the steam, it waits for his fall or a parried lunge's window. Inside a window he is Broken at
# once, even with the stump of a parried lunge still standing.
func enter_broken() -> void:
	if body.defeated or body.boss_health <= 0 or player_defeated:
		return
	if current_state == null or String(current_state.name) in NO_BREAK_STATES:
		return
	if not is_open() and (body.pillar.standing or current_state == states["Fall"] or current_state == states["Lunge"]):
		break_owed = true
		return
	cancel_launch()
	on_child_transition(current_state, "Broken")


# A Break owed, handed to the window that cashes it, and cleared.
func take_break_owed() -> bool:
	var owed := break_owed
	break_owed = false
	return owed


# The tiered finisher's first uppercut (LiamScript.begin_juggle).
func enter_juggled() -> void:
	if body.defeated or current_state == states.get("Juggled"):
		return
	on_child_transition(current_state, "Juggled")


# Down after a juggle, he picks himself up where he crashed, `delay` from now.
func after_juggle(delay: float) -> void:
	window_over(current_state, delay)


# The one switch past the fight being decided that on_child_transition refuses: killed in the air, he lands into his
# defeat lying on the juggle's down loop.
func land_juggled(final_state_name: String) -> void:
	var final_state = states.get(final_state_name)
	if final_state == null:
		return
	if "lying" in final_state:
		final_state.lying = true
	current_state.Exit()
	final_state.Enter()
	current_state = final_state


# Where the juggle's leap shadow lies.
func ground_layer() -> Node2D:
	return body.floor_layer


#THE ENDINGS

func enter_defeated() -> void:
	_end_fight("Defeated")


# The player lost: everything of his stops where it is.
func enter_player_defeated() -> void:
	_end_fight("Idle")
	player_defeated = true


func _end_fight(final_state_name: String) -> void:
	var takeover = states.get("Takeover")
	if takeover and takeover.has_method("finish_cut"):
		takeover.finish_cut(false)
	stop_everything()
	states["Idle"].beat_left = -1.0
	var juggled = states.get("Juggled")
	# In the air, he finishes his fall and his crash first (land_juggled).
	if current_state == juggled:
		juggled.final_state = final_state_name
		return
	on_child_transition(current_state, final_state_name)


# Everything of his still running, stopped on the spot, however the fight ended, and the HUD back.
func stop_everything() -> void:
	ParryTell.clear(body)
	body.leave_perch()
	for state: Node in states.values():
		if state.has_method("interrupt"):
			state.interrupt()
	cancel_launch()
	carry_left = 0.0
	set_player_ice(false)
	if is_instance_valid(body.row):
		body.row.crumble(crumble_time)
	if is_instance_valid(body.steam):
		body.steam.set_density(0.0, 0.6)
	for hazard in get_tree().get_nodes_in_group(HAZARD_GROUP):
		if hazard.has_method("crumble"):
			hazard.crumble()
		elif hazard.has_method("collapse"):
			hazard.collapse(wave_collapse_time)
		elif hazard.has_method("extinguish"):
			hazard.extinguish()
	if body.flood and body.flood.is_iced():
		body.flood.shatter()


#THE PLAYER

# Null between two scenes, which is where an attack cut short by a scene change lets go.
func get_player() -> Node2D:
	if not is_inside_tree():
		return null
	var scene := get_tree().current_scene
	return scene.get_node_or_null("Arena/MainPlayer/CharacterBody2D") if scene else null


func player_hurtbox_centre() -> Vector2:
	var player := get_player()
	if player == null:
		return PERCH
	return player.hurtBox.get_node("CollisionShape2D").global_position


# A wave's carry: `velocity` px/s on the player for `seconds`, through their own movement (add_drift).
func carry_player(velocity: Vector2, seconds: float) -> void:
	carry_velocity = velocity
	carry_left = seconds


func set_player_ice(on: bool) -> void:
	var player := get_player()
	if player and player.has_method("set_ice") and player.on_ice != on:
		player.set_ice(on, ice_accel, ice_friction, ice_dash_carry)


# Where his air blast throws the player, from wherever they stand: the bottom middle.
func launch_spot(_from: Vector2) -> Vector2:
	return RESET_SPOT


# Across the ring to `to` on rails and on his own clock, MattScript.launch_player's way: sealed off and stood still for
# it, a trail behind them (LiamGust.trail's `trail` kind: the gust's, or the water blast's), and given back where it
# lands. Returns whether it launched: a player already within launch_skip of the spot stays put.
func launch_player(to: Vector2, trail := &"gust") -> bool:
	var player := get_player()
	if player == null or player.fight_over or player.global_position.distance_to(to) <= launch_skip:
		return false
	cancel_launch()
	launched_player = player
	player.lock_actions_sealed()
	player.set_scripted_pose(true)
	var from: Vector2 = player.global_position
	launch = create_tween()
	launch.tween_method(_step_launch.bind(from, to), 0.0, 1.0, launch_time).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	launch.tween_callback(_land_launch)
	LiamGust.trail(body.fx_layer, player, launch_time, trail)
	return true


func _step_launch(weight: float, from: Vector2, to: Vector2) -> void:
	if is_instance_valid(launched_player):
		launched_player.global_position = from.lerp(to, weight).round()


func _land_launch() -> void:
	var player := launched_player
	launched_player = null
	launch = null
	if is_instance_valid(player):
		player.set_scripted_pose(false)
		player.unlock_actions()


# However the fight ends, nobody is left locked in the air.
func cancel_launch() -> void:
	if launch and launch.is_valid():
		launch.kill()
	launch = null
	if launched_player != null:
		_land_launch()


func is_launching() -> bool:
	return launch != null and launch.is_valid()


# The player's stage lifted to `z` while they hang on his staff (IMPALE_Z), and put back: CarterStateMachine's way, the
# only thing this fight writes to a node it doesn't own, and LiamLunge.release() is what undoes it.
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


# Everything he sends out lives under his scene, so a finisher's freeze holds it, and in the hazard group, so the end
# of the fight takes it.
func add_hazard(hazard: Node2D, layer: Node2D) -> void:
	hazard.add_to_group(HAZARD_GROUP)
	layer.add_child(hazard)


# The crowd: &"cheer" for `seconds`, or &"hush".
func crowd(kind: StringName, seconds := 1.5) -> void:
	for member in get_tree().get_nodes_in_group("arena_crowd"):
		if kind == &"hush" and member.has_method("hush"):
			member.hush()
		elif kind == &"cheer" and member.has_method("cheer"):
			member.cheer(seconds)
