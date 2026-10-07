extends Node

# Danny's fight, boss 7. His intro once (the lines, the hold that skips them and the VS card), then
# ATTACK_ORDER round and round, one attack at a time with a breath in Idle between:
#   Spit       four worm globs that land as puddles; a player whose feet step into one is rooted.
#   BellyBump  a charge along the player's line under a red badge (Addendum 1): a hit carries them into the ropes,
#              a parry holds their ground and leaves him dizzy in Staggered, and his run can slip on his own worms
#              onto his back.
#   Slams      the Sumo Smash string from the air: seven to nine hops that splash worms round where they land, then the big
#              one, the only quake ring. Parried, the big one bounces him onto his back (OnBack); anything else
#              ends in
#   Sleep      his nap: he heals, and it is the window to punish him in.
# A root in Idle, Spit or Sleep turns into his Headbutt (on_player_rooted); a parried one leaves him in
# Staggered, a window of its own. The windows are Sleep, Staggered, OnBack's and the Break's.
#
# THE BREAK: reads fill his gauge (DannyBossScript.BREAK). The one that fills it drops him into Broken where
# he stands, mid-attack if need be (enter_broken), and he gets up into Idle and the next attack in order.
# Idle holds Slams while the gauge is locked (gauge_ready), so every read the string asks for is credited.
#
# 0 HP IS NOT THE END (enter_sumo): the gates open for a false victory, then he wakes, blocks the top gate
# and the two of them push for it (DannyBossSumo). Nothing before the sumo's result may finish the fight or
# set the player's fight_over, because PlayerPosed.hold_pose() refuses once it is set: only that result
# calls FightOutro.
#
# WHAT EVERY ATTACK STATE KEEPS: it exports `body`, ends with attack_done(self) (Slams hands over to Sleep,
# the rest to Idle), and has an idempotent release() that its own Exit() and _exit_tree() call, and
# _stop_everything() calls for all of them at once. Its knobs are its own exports, so no two attacks share a
# file.
#
# Every wait in this fight is a Timer, a Physics_Update accumulator or a node-bound tween, so a pause and a
# finisher's freeze hold all of it. Nothing may use get_tree().create_timer() or a tree-level
# create_tween().

@export var initial_state : State

@export var states : Dictionary = {}
@export var current_state : State
@export var DannyBossCharacterBody : CharacterBody2D

#TIMERS
@export var post_dialogue_pre_fight_timer: Timer
@export var finisher_stagger_timer: Timer
@export var beat_timer: Timer
@export var sleep_timer: Timer

const VsCard := preload("res://Scripts/VsCard.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")
const Layout := preload("res://Scripts/DannyBossArtLayout.gd")
# Addendum 1's two states, built here rather than in his scene (_add_state).
const BellyBump := preload("res://Scripts/States/DannyBoss/DannyBossBellyBump.gd")
const OnBack := preload("res://Scripts/States/DannyBoss/DannyBossOnBack.gd")
const PRE_FIGHT_DIALOGUE := "res://Dialogue/DannyBossPreFight.dialogue"
const SUMO_DIALOGUE := "res://Dialogue/DannyBossSumo.dialogue"
# Coder B's root, which test_root_player() puts on the player the way a puddle does.
const ROOT_SCRIPT := "res://Scripts/DannyBossRoot.gd"
# Everything he sends out: globs, puddles, roots, slam marks and hits, rings, trails and their effects.
const HAZARD_GROUP := "danny_hazard"
# The states with a release(), which _stop_everything() calls.
const RELEASING_STATES := ["Spit", "Slams", "Sleep", "Headbutt", "Staggered", "BellyBump", "OnBack"]
# The attacks whose reads fill the gauge, which Idle holds while it is locked. The headbutt only ever
# answers a root.
const GAUGE_ATTACKS := ["BellyBump", "Slams"]
# No root is sprung while he is in one of these (can_root).
const NO_ROOT_STATES := ["Intro", "Sumo", "Defeated", "Victory", "Broken", "Juggled", "Headbutt"]
# A root sprung while he is in one of these is his headbutt's cue.
const HEADBUTT_STATES := ["Idle", "Spit", "Sleep"]
# After a headbutt resolves, however it went, no puddle roots for this long (start_root_grace).
const ROOT_GRACE := 1.5
# A root sprung anywhere else lets go by itself: in the string, if no landing has let it go first; in
# anything else, soon.
const SLAMS_ROOT_HOLD := 1.5
const OTHER_ROOT_HOLD := 0.8

#WHERE THINGS ARE (feet points, px)
# His mark, where he spits and naps.
const HOME := Vector2(960, 600)
# The sumo: he blocks the top gate standing in front of it, facing the camera, and the player clinches from
# below with their feet here. Their origin is 42 px over their feet, at y 506, which still sorts them in front
# of his feet at 500, with 6 px to spare.
const GATE_BLOCK := Vector2(960, 500)
const CLINCH := Vector2(960, 548)
# His feet past this are out through the top doorway; the player's past the other, out through the bottom.
const WIN_FEET_Y := 400.0
const LOSE_FEET_Y := 900.0
# The inside edges of the ropes, as every other fight measures them.
const ROPES := Rect2(113, 114, 1692, 853)
# Where his feet may go.
const WALK_RECT := Rect2(200, 300, 1520, 655)
# A badge over his crown in here is inside the boss bar, which fades while he is there.
const HUD_FADE_RECT := Rect2(680, -1080, 560, 1280)
# The player's feet on a ground line: their body's centre is this far above their hurtbox's bottom, and
# this much below it keeps them drawn in front of him (BossBroken's numbers, for spot_beside).
const PLAYER_FEET_OFFSET := 42.0
const PLAYER_IN_FRONT := 3.0

#PACING (seconds)
@export var idle_beat := 0.8
# How often Idle looks again at a locked gauge.
@export var gauge_wait_step := 0.2

#HUD
@export var hud_fade_alpha := 0.3

#ON HIS BACK (px)
# His lying box's top never rises above this (DannyBossOnBack): under the top rope (ROPES, y 114) and clear of the
# boss HP block that hangs below it, whose Break gauge ends at y 181. A bounce or a slip near the top of the ring
# lands him that much lower instead, still beside the player (lying_feet_y_min); his standing poses keep WALK_RECT.
@export var lying_top_min := 182.0

# Seedable, so a test or a bot can replay a fight: the puddles' spots come from it.
var rng := RandomNumberGenerator.new()

var player_defeated := false
# His attacks in the order they come, advanced as each one starts. A var, so a test can pin it. The belly bump
# comes while the spit's four fresh puddles are down, so the player can line one up between them and him. Three
# strings to a bump since the 2026-10-06 tuning: every attack of his ends in an opening, and the bump's, a parry
# away, was the cheap one.
var ATTACK_ORDER: Array[String] = ["Spit", "Slams", "Spit", "Slams", "Spit", "BellyBump", "Slams"]
var attacks_started := 0
# The pre-fight lines' balloon, which a held skip takes down, and whether those lines have handed over to
# the VS card yet.
var pre_fight_balloon: Node
var pre_fight_over := false
# The sumo's line, which its skip takes down.
var sumo_balloon: Node
# 0 HP was reached: from here the only ways on are the sumo and its two endings.
var sumo_entered := false
# The final tug's rope the player has banked by parrying his belly bumps (DannyBossBellyBump.tug_head_start, the
# user's open question 4: 0 unless that knob is on), which the sumo starts from.
var tug_head_start := 0.0
# The worm puddles lying on the floor, and the root holding the player's feet, if one is.
var puddles: Array[Node] = []
var root: Node
var root_grace_left := 0.0
# A drive of the player to a spot (drive_player_to), stepped here.
var driven: Node2D
var drive_from := Vector2.ZERO
var drive_to := Vector2.ZERO
var drive_time := 0.0
var drive_left := 0.0
var drive_locked := false
var warned := {}


func _ready() -> void:
	rng.randomize()
	# Before the children are gathered, which takes these in with them. Built in code so nothing an open editor
	# saves can write over them (Computah's and Liam's way).
	_add_state(BellyBump.new(), "BellyBump")
	_add_state(OnBack.new(), "OnBack")
	for child in get_children():
		if child is State:
			states[child.name] = child

	if initial_state:
		current_state = initial_state
		# Deferred until the scene is up: his entrance reads the player and the gates off the fight scene.
		current_state.Enter.call_deferred()


# `body` is set before the state is ready, which needs it; the state finds this node as its parent itself.
func _add_state(state: State, state_name: String) -> void:
	state.name = state_name
	state.body = DannyBossCharacterBody
	add_child(state)


func _process(delta: float) -> void:
	if current_state:
		current_state.Update(delta)


func _physics_process(delta: float) -> void:
	if root_grace_left > 0.0:
		root_grace_left = maxf(root_grace_left - delta, 0.0)
	if drive_left > 0.0:
		_step_drive(delta)
	if current_state:
		current_state.Physics_Update(delta)


func on_child_transition(state, new_state_name):
	if state != current_state:
		return

	# Defeat, his or the player's, is terminal: a late timer must never restart the fight.
	if current_state == states.get("Defeated") or player_defeated:
		return
	# Past 0 HP the fight only goes on into the sumo and out of it.
	if sumo_entered and not (new_state_name in ["Sumo", "Defeated", "Victory"]):
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


# A held skip's way past the lines (BossEntrance), whether they were ever put up or not: the hand-over their
# own end makes, made from here instead. pre_fight_over keeps it to once.
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
	VsCard.play_intro(self, "danny", post_dialogue_pre_fight_timer.start)


# The fight opens on the loop's own breath.
func _on_post_dialogue_pre_fight_timer_timeout() -> void:
	DannyBossCharacterBody.start_music()
	on_child_transition(current_state, "Idle")


# The sumo's line (DannyBossSumo), which its cut passes itself along to. Its natural end is the cut's
# line_over().
func show_sumo_line(cut: State) -> void:
	DialogueManager.dialogue_ended.connect(_on_sumo_line_ended, CONNECT_ONE_SHOT)
	sumo_balloon = DialogueManager.show_dialogue_balloon(load(SUMO_DIALOGUE), "start", [cut])


# A skip's way out of the line: its natural end, disconnected so it can't come again.
func end_sumo_line() -> void:
	if DialogueManager.dialogue_ended.is_connected(_on_sumo_line_ended):
		DialogueManager.dialogue_ended.disconnect(_on_sumo_line_ended)


func _on_sumo_line_ended(_dialogue: Object) -> void:
	var sumo = states.get("Sumo")
	if sumo and sumo.has_method("line_over"):
		sumo.line_over()


#THE LOOP

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


# Whether the next attack may start: every read the string asks for must be credited, and a locked gauge
# credits none.
func gauge_ready() -> bool:
	var gauge: Node = DannyBossCharacterBody.break_gauge
	return gauge == null or not gauge.locked or not GAUGE_ATTACKS.has(next_attack())


# An attack is over. The string always ends in his nap; everything else in Idle.
func attack_done(state: State) -> void:
	if state != current_state:
		return
	if state == states.get("Slams"):
		on_child_transition(state, "Sleep")
		return
	on_child_transition(state, "Idle")


# His windows: his nap, the dizzy spell after a parried headbutt or bump, the Break's, and his time on his back
# while it is open.
func is_open() -> bool:
	if current_state in [states.get("Sleep"), states.get("Staggered"), states.get("Broken")]:
		return true
	return is_on_back() and current_state.is_window()


func is_sleeping() -> bool:
	return current_state == states.get("Sleep")


func is_staggered() -> bool:
	return current_state == states.get("Staggered")


func is_on_back() -> bool:
	return current_state != null and current_state == states.get("OnBack")


# On his back with the finisher's daze on offer: the parried slam's window and, since 2026-10-06, a slip's.
func on_back_dazeable() -> bool:
	return is_on_back() and current_state.dazeable and current_state.is_window()


# Onto his back for `window` seconds, `cap` punches, the finisher offered or not, and what put him there.
func enter_on_back(window: float, cap: int, dazeable: bool, from: StringName) -> void:
	var on_back = states.get("OnBack")
	if on_back == null:
		return
	on_back.window = window
	on_back.hit_cap = cap
	on_back.dazeable = dazeable
	on_back.from = from
	on_child_transition(current_state, "OnBack")


# The finisher's uppercut ended his time on his back: he flinches where he lies, rolls up onto his feet, and his next
# attack comes once the stagger is over and the roll has played out. The flinch first: rolled up on the uppercut's own
# frame, its flash lit the curled-up roll pose and its star hit the floor beside it (the 2026-10-04 playtest).
func roll_up_then_start_cycle(stagger_time: float) -> void:
	on_child_transition(current_state, "Idle")
	beat_timer.stop()
	DannyBossCharacterBody.play_anim(&"back_hit", &"back_roll")
	if not DannyBossCharacterBody.anim_finished.is_connected(_on_roll_flinch_finished):
		DannyBossCharacterBody.anim_finished.connect(_on_roll_flinch_finished, CONNECT_ONE_SHOT)
	var chain := Layout.loop_length(Layout.anim(&"back_hit")) + Layout.loop_length(Layout.anim(&"back_roll"))
	finisher_stagger_timer.start(maxf(stagger_time, chain))


# The flinch is over and the roll has taken over from it: it hands over to his idle, with its sound.
func _on_roll_flinch_finished(finished: StringName) -> void:
	if finished != &"back_hit" or DannyBossCharacterBody.current_anim != &"back_roll":
		return
	DannyBossCharacterBody.anim_next = &"idle"
	DannyBossCharacterBody.play_sfx(&"back_roll")


func flinch() -> void:
	if is_open() and current_state.has_method("flinch"):
		current_state.flinch()


# The finisher ended his nap or his dizzy spell early: he stays down, staggered, then the next attack.
func stagger_then_start_cycle(stagger_time: float) -> void:
	sleep_timer.stop()
	on_child_transition(current_state, "Idle")
	# Idle starts the breath before the next attack; the stagger replaces it.
	beat_timer.stop()
	# Held on the recoil through the stagger instead of the idle loop Idle starts.
	DannyBossCharacterBody.play_anim(&"hit", &"idle")
	finisher_stagger_timer.start(stagger_time)


func _on_finisher_stagger_timer_timeout() -> void:
	start_cycle()


#THE BREAK

# A full Break gauge (DannyBossScript._on_break): whatever he was doing stops, everything he sent out goes,
# and he drops where he stands.
func enter_broken() -> void:
	if DannyBossCharacterBody.defeated or DannyBossCharacterBody.boss_health <= 0 or player_defeated or sumo_entered:
		return
	if current_state in [states.get("Broken"), states.get("Juggled"), states.get("Defeated")]:
		return
	_stop_everything()
	on_child_transition(current_state, "Broken")


# The finisher's uppercut ends the Break's window instead of its own clock.
func end_break(delay: float) -> void:
	_get_up(delay)


# The tiered finisher's first uppercut (DannyBossScript.begin_juggle).
func enter_juggled() -> void:
	var juggled = states["Juggled"]
	if DannyBossCharacterBody.defeated or current_state == juggled:
		return
	_stop_everything()
	on_child_transition(current_state, "Juggled")


# Down after a juggle, he picks himself up where he crashed.
func after_juggle(delay: float) -> void:
	_get_up(delay)


# He shakes himself awake as he gets up, then idles, and his next attack comes `delay` from now.
func _get_up(delay: float) -> void:
	on_child_transition(current_state, "Idle")
	beat_timer.stop()
	DannyBossCharacterBody.play_anim(&"wake", &"idle")
	finisher_stagger_timer.start(maxf(delay, 0.01))


# The one switch past the fight being decided: juggled to 0 HP, he lands into the sumo lying on his back
# rather than snapping to its pose mid-flight.
func land_juggled(final_state_name: String) -> void:
	var final_state = states.get(final_state_name)
	if final_state == null:
		return
	if "lying" in final_state:
		final_state.lying = true
	current_state.Exit()
	final_state.Enter()
	current_state = final_state


# Where the juggle's shadow lies: under both fighters.
func ground_layer() -> Node2D:
	return DannyBossCharacterBody.floor_layer


#HELPERS

# Null between two scenes, which is where an attack cut short by a scene change lets go.
func get_player() -> Node2D:
	var scene := get_tree().current_scene
	return scene.get_node_or_null("Arena/MainPlayer/CharacterBody2D") if scene else null


# The ring's gates (ArenaGate), which his entrance slams and the sumo opens and slams again. Null in a scene
# without them.
func gates() -> Node:
	var scene := get_tree().current_scene
	return scene.get_node_or_null("Arena/Gates") if scene else null


# The player's position with their hurtbox's far edge on the inner line of the side rope `dir` points at (+1 the
# right rope, -1 the left), where the belly bump carries them: inside the positions their own ring net allows
# (PlayerScript._keep_in_ring), so the net never snaps them off it.
func player_rope_position(dir: float) -> Vector2:
	var player := get_player()
	if player == null:
		return HOME
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	var far_edge := box.end.x if dir > 0.0 else box.position.x
	var to: Vector2 = player.global_position + Vector2(rope_point(dir, 0.0).x - far_edge, 0.0)
	var origins: Rect2 = player.ring_origins if "ring_origins" in player else Rect2()
	if origins.has_area():
		to = to.clamp(origins.position, origins.end)
	return to.round()


# The least feet y he may lie on his back at, with his lying box `box` given from his feet: its top then stays at
# lying_top_min or below.
func lying_feet_y_min(box: Rect2) -> float:
	return lying_top_min - box.position.y


# The side rope's inner line at height `y`: +1 the right rope, -1 the left.
func rope_point(dir: float, y: float) -> Vector2:
	return Vector2(ROPES.end.x if dir > 0.0 else ROPES.position.x, y)


# Where every hit of his comes from: the player's own hurtbox centre, so any facing answers it and the check
# is timing, not aim.
func player_hurtbox_centre() -> Vector2:
	var player := get_player()
	if player == null:
		return HOME
	return player.hurtBox.get_node("CollisionShape2D").global_position


# The bottom middle of the player's hurtbox: what a puddle tests and a slam's footprint covers.
func player_feet() -> Vector2:
	var player := get_player()
	if player == null:
		return HOME
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	return Vector2(box.get_center().x, box.end.y)


# Everything he sends out lives under his scene, so a finisher's freeze holds it, and in the hazard group,
# so a Break or the end of the fight takes it away.
func add_hazard(hazard: Node2D, at: Vector2, layer: Node2D) -> void:
	hazard.add_to_group(HAZARD_GROUP)
	hazard.position = layer.to_local(at.round())
	layer.add_child(hazard)


# Where the player stands to punch `box` from its `side` (+1 his right, -1 his left): BossBroken's spot, their
# punch reaching over the box's edge by half its length. The player's position, not their feet.
func spot_beside(box: Rect2, side: float) -> Vector2:
	var player := get_player()
	if player == null:
		return box.get_center()
	var facing: int = player.Facing.LEFT if side > 0.0 else player.Facing.RIGHT
	var reach: Rect2 = player.punch_box(facing)
	var reach_middle: float = reach.get_center().x * player.global_scale.x
	var edge: float = box.end.x if side > 0.0 else box.position.x
	return Vector2(edge - reach_middle, box.end.y - PLAYER_FEET_OFFSET + PLAYER_IN_FRONT)


# The player slid to `point` over `time`, in whole pixels, their actions locked for it unless something else
# holds them already. Stepped in this node's physics, so a pause holds it.
func drive_player_to(point: Vector2, time: float) -> void:
	_end_drive()
	var player := get_player()
	if player == null:
		return
	driven = player
	drive_from = player.global_position
	drive_to = point.round()
	drive_time = maxf(time, 0.0)
	drive_left = drive_time
	drive_locked = not player.is_action_locked
	if drive_locked:
		player.lock_actions()
	if drive_left <= 0.0:
		_end_drive()


func is_driving_player() -> bool:
	return drive_left > 0.0


func _step_drive(delta: float) -> void:
	drive_left = maxf(drive_left - delta, 0.0)
	if not is_instance_valid(driven):
		drive_left = 0.0
		return
	var weight := 1.0 - drive_left / drive_time if drive_time > 0.0 else 1.0
	driven.global_position = drive_from.lerp(drive_to, weight).round()
	if drive_left <= 0.0:
		_end_drive()


func _end_drive() -> void:
	drive_left = 0.0
	if is_instance_valid(driven):
		driven.global_position = drive_to
		if drive_locked:
			driven.unlock_actions()
	drive_locked = false
	driven = null


#THE PUDDLES AND THE ROOT

# Every puddle a glob leaves (DannyBossGlobScript), so a Spit can dry the old ones and a slam can splat one.
func register_puddle(puddle: Node) -> void:
	puddles.append(puddle)


# The puddles still in play: not dried, splatted or used.
func live_puddles() -> Array[Node]:
	var live: Array[Node] = []
	for puddle in puddles:
		if is_instance_valid(puddle) and not puddle.gone:
			live.append(puddle)
	puddles = live.duplicate()
	return live


# Every puddle gone at once: a Break and 0 HP.
func clear_puddles() -> void:
	for puddle in puddles:
		if is_instance_valid(puddle):
			puddle.queue_free()
	puddles.clear()


# A slam coming down splats every puddle whose pivot is inside its footprint: an ellipse of radii rx and ry
# round `centre`.
func splat_puddles_in(centre: Vector2, rx: float, ry: float) -> void:
	for puddle in live_puddles():
		var d: Vector2 = puddle.global_position - centre
		if pow(d.x / rx, 2.0) + pow(d.y / ry, 2.0) <= 1.0:
			puddle.splat()


# Every puddle whose trigger reaches into `box` grown by `margin` splats: the floor he lies on and the room round it,
# clean for the punish. How many it took.
func clear_floor_round(box: Rect2, margin: float) -> int:
	var room := box.grow(margin)
	var cleared := 0
	for puddle in live_puddles():
		var centre: Vector2 = puddle.global_position
		var nearest := centre.clamp(room.position, room.end)
		if ((nearest - centre) / puddle.radii).length_squared() <= 1.0:
			puddle.splat()
			cleared += 1
	return cleared


# The first armed puddle whose trigger `point` is in, or null.
func armed_puddle_at(point: Vector2) -> Node:
	for puddle in live_puddles():
		if puddle.armed and puddle.contains_feet(point):
			return puddle
	return null


# Whether a puddle may root the player now. Never in his intro, the Break, the juggle, the headbutt or the
# ending; never on a player already rooted, or for ROOT_GRACE after a headbutt; and never on a player already
# held by anything else: there is one lock flag, and a root's release would lift the other hold's lock with
# its own.
func can_root() -> bool:
	var player := get_player()
	if player == null or sumo_entered or player_defeated or current_state == null:
		return false
	if String(current_state.name) in NO_ROOT_STATES:
		return false
	if is_instance_valid(root) and not root.released:
		return false
	if root_grace_left > 0.0:
		return false
	if player.fight_over or player.is_finishing or player.is_grabbed or player.is_talking or player.is_action_locked:
		return false
	return player.playerHealth > 0 and DannyBossCharacterBody.boss_health > 0


# A puddle has rooted the player (the root has already taken hold). In Idle, Spit or his nap it is his
# headbutt's cue, and whatever he was doing lets go on the way out. In the string there is no headbutt: the
# next landing lets it go once that slam has resolved on the player (release_root), or it lets go by itself.
# Anywhere else it lets go by itself soon.
func on_player_rooted(new_root: Node) -> void:
	root = new_root
	if can_headbutt():
		on_child_transition(current_state, "Headbutt")
	elif current_state == states.get("Slams"):
		new_root.hold(SLAMS_ROOT_HOLD)
	else:
		new_root.hold(OTHER_ROOT_HOLD)


func can_headbutt() -> bool:
	return current_state != null and String(current_state.name) in HEADBUTT_STATES and not sumo_entered \
		and DannyBossCharacterBody.boss_health > 0


# Lets the player go, at once and in this call: the unlock has to land before anything else takes them.
func release_root() -> void:
	if is_instance_valid(root):
		root.release()
	root = null


# The headbutt calls it as it resolves, however it went.
func start_root_grace(seconds := ROOT_GRACE) -> void:
	root_grace_left = seconds


# For tests and bots: roots the player where they stand exactly as a puddle would, whatever he is doing, if
# a root may be sprung now. The root, or null.
func test_root_player() -> Node:
	var player := get_player()
	if player == null or not can_root() or not ResourceLoader.exists(ROOT_SCRIPT):
		return null
	var script: GDScript = load(ROOT_SCRIPT)
	var new_root: Node2D = script.new()
	new_root.player = player
	new_root.body = DannyBossCharacterBody
	add_hazard(new_root, script.pivot_of(player), DannyBossCharacterBody.projectile_layer)
	on_player_rooted(new_root)
	return new_root


#THE PLAYER (every call guarded, CarterStateMachine's way: a player scene without one is a warning)

# Held: no move, dash or punch, but the guard and its parry stay live.
func lock_player() -> void:
	var player := get_player()
	if player and player.has_method("lock_actions"):
		player.lock_actions()
	else:
		_warn_once("lock", "Danny: player has no lock_actions()")


# Held and unable to answer at all - no move, dash, punch, guard or parry.
func seal_player() -> void:
	var player := get_player()
	if player and player.has_method("lock_actions_sealed"):
		player.lock_actions_sealed()
	else:
		_warn_once("seal", "Danny: player has no lock_actions_sealed(); the sumo can't hold them")


func unlock_player() -> void:
	var player := get_player()
	if player and player.has_method("unlock_actions"):
		player.unlock_actions()


func hold_player_pose(sheet: Dictionary) -> bool:
	var player := get_player()
	if player and player.has_method("hold_pose"):
		return player.hold_pose(sheet)
	_warn_once("pose", "Danny: player has no hold_pose(); the sumo's poses stay off")
	return false


func play_player_pose(frames: Array, times: Array, loop: bool) -> void:
	var player := get_player()
	if player and player.has_method("play_pose"):
		player.play_pose(frames, times, loop)


func end_player_pose() -> void:
	var player := get_player()
	if player and player.has_method("end_pose"):
		player.end_pose()


func face_player_at(point: Vector2) -> void:
	var player := get_player()
	if player and player.has_method("face_point"):
		player.face_point(point)


func clear_player_facing() -> void:
	var player := get_player()
	if player and player.has_method("clear_face_point"):
		player.clear_face_point()


# Called at the start of EVERY headbutt tell, always. PlayerDefense counts a press that didn't parry against
# the next attack for parry_mash_lockout, so without this a whiffed press can leave the headbutt
# unparryable. Carter's fight learned this the hard way.
func rearm_parry() -> void:
	var defense := _defense()
	if defense and defense.has_method("rearm_parry"):
		defense.rearm_parry()
	else:
		_warn_once("rearm", "Danny: PlayerDefense has no rearm_parry(); a whiffed press can lock out the headbutt")


func _defense() -> Node:
	var player := get_player()
	return player.get("defense") if player else null


func _warn_once(key: String, message: String) -> void:
	if warned.has(key):
		return
	warned[key] = true
	push_warning(message)


#THE END OF THE FIGHT

# 0 HP (DannyBossScript._on_zero_health): everything of his stops, and the sumo takes over. Juggled to 0, he
# finishes his fall and his crash first and lands into it (land_juggled). It neither ends the fight nor lets
# FightOutro run: only the sumo's result does.
func enter_sumo() -> void:
	if sumo_entered or player_defeated or DannyBossCharacterBody.defeated:
		return
	sumo_entered = true
	var intro = states.get("Intro")
	if intro:
		intro.finish_entrance()
	_stop_everything()
	var juggled = states.get("Juggled")
	if juggled and current_state == juggled:
		juggled.final_state = "Sumo"
		return
	on_child_transition(current_state, "Sumo")


# The player won the sumo and he is out (DannyBossSumo).
func enter_defeated() -> void:
	_end_fight("Defeated")


# The player lost, in the fight or in the sumo: he sits down and naps where he is.
func enter_player_defeated() -> void:
	_end_fight("Victory")
	player_defeated = true


func _end_fight(final_state_name: String) -> void:
	# A fight decided over the top of his entrance still leaves the ring set.
	var intro = states.get("Intro")
	if intro:
		intro.finish_entrance()
	_stop_everything()
	var juggled = states.get("Juggled")
	# In the air, he finishes his fall and his crash first (land_juggled).
	if juggled and current_state == juggled:
		juggled.final_state = final_state_name
		return
	on_child_transition(current_state, final_state_name)


# Everything of his still running, stopped on the spot: a Break, a juggle, 0 HP or either side winning.
func _stop_everything() -> void:
	ParryTell.clear(DannyBossCharacterBody)
	# First, and in this call: a root freed with the hazards would let go of the player on its way out, a
	# frame after a Break has locked them for its drive-in, and lift that lock with its own.
	release_root()
	for state_name in RELEASING_STATES:
		var state = states.get(state_name)
		if state and state.has_method("release"):
			state.release()
	_end_drive()
	clear_puddles()
	DannyBossCharacterBody.clear_nap_fx()
	# Once the sumo has started his bar is gone for good (DannyBossSumo hides it at the KO), so neither the KO nor
	# either finish may bring it back.
	if not sumo_entered:
		DannyBossCharacterBody.restore_hud()
	for hazard in get_tree().get_nodes_in_group(HAZARD_GROUP):
		hazard.queue_free()
	for timer in [post_dialogue_pre_fight_timer, finisher_stagger_timer, beat_timer, sleep_timer]:
		timer.stop()
		timer.paused = false
