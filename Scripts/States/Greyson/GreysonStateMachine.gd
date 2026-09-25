extends Node

# Greyson's half of FIGHT 03. The takeover once (GreysonTakeover: Computah's cannon arm, his lines and the bar
# swap, or its end state at once in the test scene), then his attacks round and round, each a CHAIN of states from
# ATTACKS with a breath in Idle between. Attack 1 is Throw (plates off the ropes), Slams (five teleport slams, each
# planting an eruption zone) and Pose (six poses to the crowd that fill his hype meter). The next attacks are new
# chains in ATTACKS: nothing else changes.
#
# HE CAN BE HIT only while he poses and while he is Broken (is_open). Parried and perfect-dodged plates fill his
# Break gauge; the one that fills it drops him into Broken where he stands, and a Break skips that cycle's poses.
#
# THE ERUPTION ZONES wait in a queue here: Slams adds them (add_pending_zone) and each goes off when the queue says
# (schedule_next_eruption): all five one after another through the first three poses, the last as pose 3 ends
# (GreysonPose.eruptions). Any early end - a finisher, a Break, 0 HP, the spirit bomb - fizzles the rest
# (clear_pending_zones), so none leak into the next cycle.
#
# THE ENDINGS. A full hype meter fires the spirit bomb, a loss (enter_spirit_bomb). 0 HP is not a defeat: it hands
# to the final brawl (enter_final_brawl), whose end calls greyson_beaten() and the normal win. The player losing,
# to hearts or the bomb, ends in Victory. After the brawl starts the only ways on are its two ends.
#
# WHAT EVERY ATTACK STATE KEEPS: it exports `body`, ends with chain_next(self), and has an idempotent release()
# that its own Exit() calls and _stop_everything() calls for all of them at once. Its knobs are its own exports.
# Every wait in this fight is a Timer, a Physics_Update accumulator or a node-bound tween, so a pause and a
# finisher's freeze hold all of it: nothing may use get_tree().create_timer() or a tree-level create_tween().

@export var initial_state : State

@export var states : Dictionary = {}
@export var current_state : State
@export var body : CharacterBody2D

#TIMERS
@export var finisher_stagger_timer: Timer
@export var beat_timer: Timer

const ParryTell := preload("res://Scripts/ParryTell.gd")
const TAKEOVER_DIALOGUE := "res://Dialogue/GreysonTakeover.dialogue"
# Everything he sends out: plates, zones, bursts and their effects.
const HAZARD_GROUP := "greyson_hazard"
# The states with a release(), which _stop_everything() calls. FinalBrawl's is only called while it is his state:
# nothing on the way into the brawl may reach into it.
const RELEASING_STATES := ["Throw", "Slams", "Pose", "SpiritBomb"]
# His windows: the only states a punch lands in.
const OPEN_STATES := ["Pose", "Broken"]
# The attacks whose reads fill the gauge, which Idle holds while it is locked.
const GAUGE_ATTACKS := ["Throw"]
# Nothing breaks him in these.
const NO_BREAK_STATES := ["Takeover", "SpiritBomb", "Broken", "Juggled", "FinalBrawl", "Defeated", "Victory"]
# How many waiting zones rumble at once (rumbles): with five pending through the slams, every loop at once drones.
const RUMBLING_ZONES := 2

#WHERE THINGS ARE (feet points, px)
# His mark, "the top of the arena", Computah's own home: with his arms raised he stays clear of his HUD block.
const HOME := Vector2(960, 560)
# Where his feet may be: his teleports land on its corners and edge midpoints (furthest_spot).
const STAND_RECT := Rect2(260, 560, 1400, 370)
# Where he casts the spirit bomb from, teleported there as it starts: the bomb's light layer is authored for it.
const BOMB_CAST := Vector2(960, 800)
# The inside edges of the ropes, as every other fight measures them: the plates turn off them.
const ROPES := Rect2(113, 114, 1692, 853)
# A badge over his crown in here is inside the boss bar, which fades while he is there.
const HUD_FADE_RECT := Rect2(680, -1080, 560, 1280)

#PACING (seconds)
# The breath between cycles, and the first one, after the takeover.
@export var idle_beat := 0.8
@export var first_beat := 1.0
# How often Idle looks again at a locked gauge.
@export var gauge_wait_step := 0.2

#HUD
@export var hud_fade_alpha := 0.3

# Seedable, so a test or a bot can replay a fight.
var rng := RandomNumberGenerator.new()

var player_defeated := false
# The player's loss has begun. player_defeated can't say so until the loss has run: on_child_transition refuses
# every switch once it is set, the loss's own switch to Victory included.
var loss_started := false
# His attacks, each a chain of states, taken in turn. A var, so a test can pin it.
var ATTACKS: Array[Array] = [["Throw", "Slams", "Pose"]]
var cycles_started := 0
# The chain running, and which of its states he is in.
var chain: Array = []
var chain_step := 0
# 0 HP was reached: from here the only ways on are the brawl and its two ends.
var final_brawl_entered := false
# The takeover's balloon, which its skip takes down.
var takeover_balloon: Node
# Every zone Slams planted this cycle, and the ones not yet told when to go off, oldest first.
var zones: Array[Node] = []
var unscheduled: Array[Node] = []
var warned := {}


func _ready() -> void:
	rng.randomize()
	for child in get_children():
		if child is State:
			states[child.name] = child

	if initial_state:
		current_state = initial_state
		# Deferred until the scene is up: the takeover reads the player, the gates and Computah off it.
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
	if current_state == states.get("Defeated") or current_state == states.get("Victory") or player_defeated:
		return
	# Past 0 HP the fight only goes on into the brawl and out of it.
	if final_brawl_entered and not (new_state_name in ["FinalBrawl", "Defeated", "Victory"]):
		return

	var new_state = states.get(new_state_name)
	if !new_state:
		return

	if current_state:
		current_state.Exit()

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


# The takeover is over: the first breath, then cycle 1 - or, with the body's start_in_brawl, the brawl at once.
func begin_fight() -> void:
	on_child_transition(current_state, "Idle")
	if current_state != states.get("Idle"):
		return
	if body.start_in_brawl:
		body.skip_to_brawl()
		return
	beat_timer.start(first_beat)


#THE CYCLE

func next_chain() -> Array:
	return ATTACKS[cycles_started % ATTACKS.size()]


# The next attack's chain, from its first state. Only from Idle, whose beat asks for it; a locked gauge holds an
# attack that pays the Break, and Idle looks again every gauge_wait_step.
func start_cycle() -> void:
	if current_state != states.get("Idle"):
		return
	if not gauge_ready():
		beat_timer.start(gauge_wait_step)
		return
	chain = next_chain()
	cycles_started += 1
	chain_step = 0
	on_child_transition(current_state, chain[0])


# `state` is done: the chain's next state, or Idle after its last.
func chain_next(state: State) -> void:
	if state != current_state:
		return
	chain_step += 1
	if chain_step < chain.size():
		on_child_transition(state, chain[chain_step])
	else:
		on_child_transition(state, "Idle")


# Whether the next attack may start: every read it asks for must be credited, and a locked gauge credits none.
func gauge_ready() -> bool:
	var gauge: Node = body.break_gauge
	if gauge == null or not gauge.locked:
		return true
	for state_name in next_chain():
		if GAUGE_ATTACKS.has(state_name):
			return false
	return true


# His windows: the poses and the Break's. A state that shuts its window for part of itself says so with an
# is_window_open() of its own (the poses' turn to the crowd).
func is_open() -> bool:
	if current_state == null or not (String(current_state.name) in OPEN_STATES):
		return false
	if current_state.has_method("is_window_open"):
		return current_state.is_window_open()
	return true


# Whether the state he is in lets a finisher daze him.
func allows_daze() -> bool:
	if current_state and current_state.has_method("allows_daze"):
		return current_state.allows_daze()
	return true


func flinch() -> void:
	if is_open() and current_state.has_method("flinch"):
		current_state.flinch()


# The finisher ended his window: a state that owns it answers for itself, and otherwise the whole phase ends.
func end_window(stagger_time: float) -> bool:
	if current_state.has_method("end_window"):
		return current_state.end_window(stagger_time)
	stagger_then_start_cycle(stagger_time)
	return true


# The pose window's uppercut ends the phase: the zones still waiting fizzle, he stays down staggered, and the next
# cycle comes after.
func stagger_then_start_cycle(stagger_time: float) -> void:
	clear_pending_zones()
	on_child_transition(current_state, "Idle")
	# Idle starts the breath before the next attack; the stagger replaces it.
	beat_timer.stop()
	body.play_anim(&"hit", &"idle")
	finisher_stagger_timer.start(maxf(stagger_time, 0.01))


func _on_finisher_stagger_timer_timeout() -> void:
	start_cycle()


#THE BREAK

# A full Break gauge (GreysonScript._on_break): whatever he was doing stops, everything he sent out goes, and he
# drops where he stands.
func enter_broken() -> void:
	if body.defeated or body.boss_health <= 0 or player_defeated or final_brawl_entered:
		return
	if current_state == null or String(current_state.name) in NO_BREAK_STATES:
		return
	_stop_everything()
	on_child_transition(current_state, "Broken")


# The finisher's uppercut ends the Break's window instead of its own clock.
func end_break(delay: float) -> void:
	_get_up(delay)


# The tiered finisher's first uppercut (GreysonScript.begin_juggle).
func enter_juggled() -> void:
	var juggled = states["Juggled"]
	if body.defeated or current_state == juggled:
		return
	_stop_everything()
	on_child_transition(current_state, "Juggled")


# Down after a juggle, he picks himself up where he crashed.
func after_juggle(delay: float) -> void:
	_get_up(delay)


# He gets up into Idle, and his next attack comes `delay` from now.
func _get_up(delay: float) -> void:
	on_child_transition(current_state, "Idle")
	beat_timer.stop()
	body.play_anim(&"hit", &"idle")
	finisher_stagger_timer.start(maxf(delay, 0.01))


# The one switch past the fight being decided that on_child_transition refuses: killed in the air, he lands into
# the brawl lying on the juggle's KO loop rather than snapping to it mid-flight. The player losing while he is up
# stands him back up for his Victory.
func land_juggled(final_state_name: String) -> void:
	var final_state = states.get(final_state_name)
	if final_state == null:
		return
	var juggled = current_state
	if "from_juggle" in final_state:
		final_state.from_juggle = true
	juggled.Exit()
	if final_state_name == "Victory":
		juggled.stop_lingering()
	final_state.Enter()
	current_state = final_state


# Where the juggle's shadow lies: under both fighters.
func ground_layer() -> Node2D:
	return body.floor_layer


#THE ENDINGS

# His meter is full (GreysonPose): the cannon is loaded and nothing the player does now matters.
func enter_spirit_bomb() -> void:
	if body.defeated or body.boss_health <= 0 or player_defeated or final_brawl_entered:
		return
	if current_state == null or String(current_state.name) in ["Takeover", "SpiritBomb", "Defeated", "Victory"]:
		return
	_stop_everything()
	on_child_transition(current_state, "SpiritBomb")


# 0 HP by any path (GreysonScript._on_zero_health): everything of his stops, his meter holds where it is, and the
# brawl takes over. Juggled to 0, he finishes his fall and his crash first and lands into it (land_juggled). It
# neither ends the fight nor sets `defeated`: only the brawl's end does.
func enter_final_brawl() -> void:
	if final_brawl_entered or player_defeated or body.defeated:
		return
	if current_state == null or String(current_state.name) in ["Takeover", "SpiritBomb", "Defeated", "Victory"]:
		return
	final_brawl_entered = true
	body.hype_frozen = true
	body.stop_cannon_hum()
	_stop_everything()
	var juggled = states.get("Juggled")
	if juggled and current_state == juggled:
		juggled.final_state = "FinalBrawl"
		return
	states["FinalBrawl"].from_juggle = false
	on_child_transition(current_state, "FinalBrawl")


func in_final_brawl() -> bool:
	return current_state != null and current_state == states.get("FinalBrawl")


# The brawl is won (GreysonFinalBrawl): he is down for good, lying where the brawl left him if it asks, and the
# fight ends the normal way - the fanfare, his outro, Victory, and Matt next.
func greyson_beaten(lying := false) -> void:
	if body.defeated or player_defeated:
		return
	body.defeated = true
	states["Defeated"].lying = lying
	_end_fight("Defeated")
	body.win()


# The player lost, to hearts or to the spirit bomb (FightOutro calls it): he laughs where he stands.
func enter_player_defeated() -> void:
	loss_started = true
	_end_fight("Victory")
	player_defeated = true


func _end_fight(final_state_name: String) -> void:
	# A fight decided over the top of the takeover still leaves the ring set.
	var takeover = states.get("Takeover")
	if takeover and takeover.has_method("finish_cut"):
		takeover.finish_cut(false)
	_stop_everything()
	var juggled = states.get("Juggled")
	# In the air, he finishes his fall and his crash first (land_juggled).
	if juggled and current_state == juggled:
		juggled.final_state = final_state_name
		return
	on_child_transition(current_state, final_state_name)


# Everything of his still running, stopped on the spot: a Break, a juggle, 0 HP, the spirit bomb, or either side
# winning.
func _stop_everything() -> void:
	ParryTell.clear(body)
	for state_name in RELEASING_STATES:
		var state = states.get(state_name)
		if state and state.has_method("release"):
			state.release()
	if in_final_brawl() and current_state.has_method("release"):
		current_state.release()
	clear_pending_zones()
	_clear_hazards()
	# Once the brawl, the spirit bomb or a loss has started, his bar stays as they left it - gone, for the brawl and
	# the bomb, which take it away - so nothing may bring it back, and never with the bomb's full meter on it. A
	# bomb that spares a playtest-invincible player has left SpiritBomb by the time anything stops him again.
	if not (final_brawl_entered or loss_started or current_state == states.get("SpiritBomb")):
		body.restore_hud()
	for timer in [finisher_stagger_timer, beat_timer]:
		timer.stop()
		timer.paused = false


# Everything he sent out, gone: a zone still waiting to go off, or a plate still flying, fizzles out where it is,
# which reads as the attack collapsing, and leaves the group, since nothing about it can land any more; anything
# else, a burst going off included, goes at once.
func _clear_hazards() -> void:
	for hazard in get_tree().get_nodes_in_group(HAZARD_GROUP):
		if _fizzles(hazard):
			hazard.remove_from_group(HAZARD_GROUP)
			hazard.fizzle()
		else:
			hazard.queue_free()
	# What a fizzle leaves behind as it goes (a plate's vanish puff, through play_fx) joined the group after the
	# pass above: it is the fizzle's own last frames, which can't land, and it frees itself as they play out.
	for leftover in get_tree().get_nodes_in_group(HAZARD_GROUP):
		if not leftover.is_queued_for_deletion():
			leftover.remove_from_group(HAZARD_GROUP)


func _fizzles(hazard: Node) -> bool:
	if hazard.has_method("is_pending"):
		return hazard.is_pending()
	return hazard.has_method("fizzle")


#THE ERUPTION ZONES

# A zone Slams has planted (after add_hazard), waiting its turn.
func add_pending_zone(zone: Node) -> void:
	zones.append(zone)
	unscheduled.append(zone)


# The oldest zone not yet told when to go off, told to go off `seconds` from now. That zone, or null if none is
# waiting.
func schedule_next_eruption(seconds: float) -> Node:
	while not unscheduled.is_empty():
		var zone: Node = unscheduled.pop_front()
		if is_instance_valid(zone) and zone.is_pending():
			zone.schedule(seconds)
			return zone
	return null


# Every zone still waiting, scheduled or not.
func live_zones() -> Array[Node]:
	var live: Array[Node] = []
	for zone in zones:
		if is_instance_valid(zone) and zone.is_pending():
			live.append(zone)
	return live


# Whether `zone` is one of the RUMBLING_ZONES waiting zones going off soonest, the only ones whose rumble sounds:
# those already told when, soonest first, then those still waiting their turn in the order the queue will tell them.
func rumbles(zone: Node) -> bool:
	var told: Array = live_zones().filter(func(live: Node) -> bool: return not unscheduled.has(live))
	told.sort_custom(func(a: Node, b: Node) -> bool: return a.fuse_left < b.fuse_left)
	var soonest: Array = told + unscheduled.filter(func(waiting) -> bool: return is_instance_valid(waiting) and waiting.is_pending())
	return soonest.slice(0, RUMBLING_ZONES).has(zone)


# Every zone still waiting fizzles out, and the queue starts over.
func clear_pending_zones() -> void:
	for zone in zones:
		if is_instance_valid(zone) and zone.is_pending():
			zone.remove_from_group(HAZARD_GROUP)
			zone.fizzle()
	zones.clear()
	unscheduled.clear()


#THE ARENA

# STAND_RECT's four corners and four edge midpoints: the spots his teleports land on.
func teleport_spots() -> Array[Vector2]:
	var spots: Array[Vector2] = []
	for fy in [0.0, 0.5, 1.0]:
		for fx in [0.0, 0.5, 1.0]:
			if fx != 0.5 or fy != 0.5:
				spots.append((STAND_RECT.position + STAND_RECT.size * Vector2(fx, fy)).round())
	return spots


# "The furthest point in the arena away from the player": of teleport_spots(), the one furthest from `from` (the
# player's feet as he goes), never `current`, the spot he is already on, so he takes the next furthest there.
# The first of a tie in teleport_spots()'s order, so a test can predict it.
func furthest_spot(from: Vector2, current: Vector2) -> Vector2:
	var best := HOME
	var best_distance := -1.0
	for spot in teleport_spots():
		if spot.is_equal_approx(current):
			continue
		var distance := spot.distance_squared_to(from)
		if distance > best_distance:
			best = spot
			best_distance = distance
	return best


# Null between two scenes, which is where an attack cut short by a scene change lets go.
func get_player() -> Node2D:
	if not is_inside_tree():
		return null
	var scene := get_tree().current_scene
	return scene.get_node_or_null("Arena/MainPlayer/CharacterBody2D") if scene else null


# The ring's gates (ArenaGate), which the takeover opens and slams. Null in a scene without them.
func gates() -> Node:
	var scene := get_tree().current_scene
	return scene.get_node_or_null("Arena/Gates") if scene else null


# Where every hit of his comes from: the player's own hurtbox centre, so any facing answers it and the check is
# timing, not aim.
func player_hurtbox_centre() -> Vector2:
	var player := get_player()
	if player == null:
		return HOME
	return player.hurtBox.get_node("CollisionShape2D").global_position


# The bottom middle of the player's hurtbox: what a zone is aimed at and tests.
func player_feet() -> Vector2:
	var player := get_player()
	if player == null:
		return HOME
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	return Vector2(box.get_center().x, box.end.y)


# Everything he sends out lives under his scene, so a finisher's freeze holds it, and in the hazard group, so a
# Break or the end of the fight takes it away: zones on the body's floor_layer, plates on its hazard_layer, bursts
# on its fx_layer.
func add_hazard(hazard: Node2D, at: Vector2, layer: Node2D) -> void:
	hazard.add_to_group(HAZARD_GROUP)
	hazard.position = layer.to_local(at.round())
	layer.add_child(hazard)


# The crowd's mood: &"cheer" or &"roar" for `seconds`, &"boo" (a hush until the crowd has a boo of its own), or
# &"hush". A cheer or a boo plays its crowd sound here, once, unless `sound` is off: the crowd band and ringside
# both run ArenaCrowdScript, so a sound played there would play twice, and in every other fight's cheers too.
func crowd(kind: StringName, seconds := 1.5, sound := true) -> void:
	if sound and kind == &"cheer":
		body.play_sfx(&"crowd_cheer")
	elif sound and kind == &"boo":
		body.play_sfx(&"crowd_boo")
	for member in get_tree().get_nodes_in_group("arena_crowd"):
		match kind:
			&"boo":
				if member.has_method("boo"):
					member.boo(seconds)
				elif member.has_method("hush"):
					member.hush()
			&"hush":
				if member.has_method("hush"):
					member.hush()
			_:
				if member.has_method("cheer"):
					member.cheer(seconds)


#THE PLAYER (every call guarded, CarterStateMachine's way: a player scene without one is a warning)

# Held: no move, dash or punch, but the guard and its parry stay live.
func lock_player() -> void:
	var player := get_player()
	if player and player.has_method("lock_actions"):
		player.lock_actions()
	else:
		_warn_once("lock", "Greyson: player has no lock_actions()")


# Held and unable to answer at all - no move, dash, punch, guard or parry.
func seal_player() -> void:
	var player := get_player()
	if player and player.has_method("lock_actions_sealed"):
		player.lock_actions_sealed()
	else:
		_warn_once("seal", "Greyson: player has no lock_actions_sealed()")


func unlock_player() -> void:
	var player := get_player()
	if player and player.has_method("unlock_actions"):
		player.unlock_actions()


func hold_player_pose(sheet: Dictionary) -> bool:
	var player := get_player()
	if player and player.has_method("hold_pose"):
		return player.hold_pose(sheet)
	_warn_once("pose", "Greyson: player has no hold_pose()")
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


# Called at the start of EVERY throw's tell, always. PlayerDefense counts a press that didn't parry against the
# next attack for parry_mash_lockout, so without this a whiffed press can leave the next plate unparryable.
func rearm_parry() -> void:
	var defense := _defense()
	if defense and defense.has_method("rearm_parry"):
		defense.rearm_parry()
	else:
		_warn_once("rearm", "Greyson: PlayerDefense has no rearm_parry(); a whiffed press can lock out the next plate")


func _defense() -> Node:
	var player := get_player()
	return player.get("defense") if player else null


func _warn_once(key: String, message: String) -> void:
	if warned.has(key):
		return
	warned[key] = true
	push_warning(message)
