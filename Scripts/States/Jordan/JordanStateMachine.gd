extends Node

@export var initial_state : State

@export var states : Dictionary = {}
@export var current_state : State
@export var JordanCharacterBody : CharacterBody2D

#TIMERS
@export var post_dialogue_pre_fight_timer: Timer
@export var finisher_stagger_timer: Timer

const VsCard := preload("res://Scripts/VsCard.gd")
const JordanIntro := preload("res://Scripts/States/Jordan/JordanIntro.gd")
const JordanBroken := preload("res://Scripts/States/Jordan/JordanBroken.gd")
const JordanJuggled := preload("res://Scripts/States/Jordan/JordanJuggled.gd")
const JordanWalkOut := preload("res://Scripts/States/Jordan/JordanWalkOut.gd")
const JordanKaijuIntro := preload("res://Scripts/States/Jordan/JordanKaijuIntro.gd")
const JordanBreath := preload("res://Scripts/States/Jordan/JordanBreath.gd")
const JordanStomp := preload("res://Scripts/States/Jordan/JordanStomp.gd")
const JordanDismounted := preload("res://Scripts/States/Jordan/JordanDismounted.gd")
const JordanRemount := preload("res://Scripts/States/Jordan/JordanRemount.gd")
const JordanRecoil := preload("res://Scripts/States/Jordan/JordanRecoil.gd")
const PRE_FIGHT_DIALOGUE := "res://Dialogue/JordanPreFight.dialogue"
const HAZARD_GROUP := "jordan_hazard"
const KaijuLayout := preload("res://Scripts/JordanKaijuLayout.gd")
const JordanArtLayout := preload("res://Scripts/JordanArtLayout.gd")
const FunkoFigure := preload("res://Scripts/FunkoFigureScript.gd")
const FunkoThrow := preload("res://Scripts/JordanFunkoThrow.gd")
const BurnLine := preload("res://Scripts/JordanBurnLine.gd")
# Under every fighter, as Danny's FloorLayer is: the beam, the burn lines, the stomp's mark, the tail's swoosh.
const KAIJU_FLOOR_Y := 101.0
# The kaiju's sounds, stand-ins from the other fights (the plan's): [stream, pitch].
const KAIJU_SFX := {
	&"roar": ["res://Assets/Audio/SFX/bixby_roar.wav", 0.8],
	&"charge": ["res://Assets/Audio/SFX/laser_charge.ogg", 1.0],
	&"leap": ["res://Assets/Audio/SFX/whirlwind_whoosh.ogg", 0.8],
	&"stomp": ["res://Assets/Audio/SFX/danny_butt_slam.wav", 0.9],
	&"stomp_quake": ["res://Assets/Audio/SFX/earthquake_slam.ogg", 1.0],
	&"tail": ["res://Assets/Audio/SFX/whirlwind_whoosh.ogg", 1.0],
	&"bonk": ["res://Assets/Audio/SFX/danny_headbutt_bonk.wav", 1.0],
}

# Phase 1's loop, a placeholder until his other attacks are designed: Idle, SummonFunkos, Taunt, then
# back to Idle, which waits for the swarm to be over before it rests.
const IDLE_TIME := 1.2
const SUMMON_WINDUP := 0.8
# Figures per summon. Summons take turns through the list.
const SUMMON_COUNTS := [3, 4]
# The figures pop in evenly spaced around the middle of his hurtbox on an ellipse with these radii, in
# px. Its height clears that box by 15 px above and below once a figure's own half height is counted,
# the margin the old ring kept round the old 64x64 sprite: a figure that popped in over his head would
# be drawn behind him.
const SUMMON_RING := Vector2(170, 170)
const TAUNT_TIME := 3.0
# The swarm is over once every figure is gone, or this many seconds after it was summoned.
const SWARM_WAIT_LIMIT := 5.0

# States only run while the fight is on: not during the pre-fight lines, and not once it's decided.
var fighting := false
var player_defeated := false
var summons := 0
var last_summon_time := -INF
var stagger_left := 0.0
# The pre-fight lines' balloon, which a held skip takes down, and whether those lines have handed
# over to the VS card yet.
var pre_fight_balloon: Node
var pre_fight_over := false
# Phase 1 on the kaiju (JordanKaijuLayout.USE_KAIJU), and the kaiju itself once it is built.
var kaiju_mode := false
var kaiju: Node2D

#ON THE KAIJU (scratchpad jordan_kaiju/PLAN.md section 3)
# Its turns in order, from the first; under half health the second list, after a roar. Two breaths to a stomp since a
# parried stomp pays the uppercut (the user, 2026-10-05): one every other turn ended the fight in two of them.
@export var cycle_a: Array[String] = ["Breath", "Breath", "Stomp"]
@export var cycle_b: Array[String] = ["Breath", "Breath", "Stomp"]
@export var rest_a := 0.6
@export var rest_b := 0.4
@export var phase_roar := 0.8
# The figures he throws down from its head: how many a throw ([the breath's, the stomp's] in Phase A, then in Phase B),
# and their flight.
var funko_counts: Array = KaijuLayout.FUNKOS.duplicate(true)
@export var throw_fly := 0.45
@export var throw_apex := 160.0
# Its hop home from wherever it ended up: crouch, the hop, the landing.
@export var return_crouch := 0.25
@export var return_hop := 0.65
@export var return_land := 0.30
@export var return_apex := 420.0
var floor_layer: Node2D
var phase_b := false
var turn := 0
var next_throw_id := 0
# Seedable, so a test or a bot can replay a fight: the figures' spots and the tail's coin come from it.
var rng := RandomNumberGenerator.new()
var sfx := {}
# For a test: every throw's flights.
var throws: Array[Node2D] = []


func _ready() -> void:
	# The main menu's FINALE row (GameProgress.start_at_finale), taken so it can't carry over into a later load: the
	# fight opens at his KO, with no lines and no card, and his win plays the finale. Without the lines' one-shot the
	# walk-out's line ending can't start the fight either.
	var at_finale: bool = GameProgress.start_at_finale
	GameProgress.start_at_finale = false
	# Phase 1 on the kaiju, with the switch on (JordanKaijuLayout.USE_KAIJU); the FINALE row never builds it.
	kaiju_mode = KaijuLayout.USE_KAIJU and not at_finale
	# His lines are all of his entrance, and he waits them out in the intro that carries the hold to
	# skip over them. The fight itself starts on the scene's initial state once the card is gone. On the
	# kaiju his entrance is its own, and starts the lines itself.
	var intro = JordanKaijuIntro.new() if kaiju_mode else JordanIntro.new()
	intro.name = "Intro"
	intro.body = JordanCharacterBody
	add_child(intro)
	# The Break window and the juggle it pays out, built in code like the intro: neither needs anything
	# the scene would have to wire.
	_add_down_state(JordanBroken.new(), "Broken")
	_add_down_state(JordanJuggled.new(), "Juggled")
	# The kaiju's two turns, his knock-off and his climb back on, the same way. The scene's SummonFunkos and Taunt
	# stay, unused.
	if kaiju_mode:
		_add_down_state(JordanBreath.new(), "Breath")
		_add_down_state(JordanStomp.new(), "Stomp")
		_add_down_state(JordanDismounted.new(), "Dismounted")
		_add_down_state(JordanRemount.new(), "Remount")
		_add_down_state(JordanRecoil.new(), "Recoil")
	# His finale's walk-out, which a win hands him (begin_walk_out), built in code like the intro.
	var walk_out := JordanWalkOut.new()
	walk_out.name = "WalkOut"
	walk_out.body = JordanCharacterBody
	add_child(walk_out)
	if not at_finale and not kaiju_mode:
		show_pre_fight_dialogue()

	for child in get_children():
		if child is State:
			states[child.name] = child

	if at_finale:
		current_state = states["Idle"]
		JordanCharacterBody.start_at_finale.call_deferred()
		return
	if kaiju_mode:
		_build_kaiju.call_deferred()
	current_state = intro
	# Deferred until the body is ready, since the intro draws him.
	current_state.Enter.call_deferred()


# Under his scene, beside him: the kaiju, its floor layer, and its sounds. Deferred from _ready, since his scene is still
# setting up its children then.
func _build_kaiju() -> void:
	var scene_node: Node2D = JordanCharacterBody.get_parent()
	floor_layer = Node2D.new()
	floor_layer.name = "KaijuFloor"
	floor_layer.position = Vector2(0, KAIJU_FLOOR_Y)
	scene_node.add_child(floor_layer)
	kaiju = load("res://Scripts/JordanKaiju.gd").new()
	kaiju.name = "Kaiju"
	kaiju.jordan = JordanCharacterBody
	kaiju.floor_layer = floor_layer
	kaiju.position = KaijuLayout.HOME
	kaiju.visible = false
	scene_node.add_child(kaiju)
	for key in KAIJU_SFX:
		var player := AudioStreamPlayer.new()
		player.name = "KaijuSfx_%s" % key
		player.stream = load(KAIJU_SFX[key][0])
		player.pitch_scale = KAIJU_SFX[key][1]
		add_child(player)
		sfx[key] = player


func play_sfx(key: StringName) -> void:
	if sfx.has(key):
		sfx[key].play()


# On its head (JordanKaiju draws him) or off it, his own sprite shown.
func set_mounted(on: bool) -> void:
	JordanCharacterBody.mounted = on
	JordanCharacterBody.sprite.visible = not on


func player_feet() -> Vector2:
	var player := get_player()
	if player == null:
		return Vector2.ZERO
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	return Vector2(box.get_center().x, box.end.y)


# On the kaiju's floor layer, under everyone, at `at` on screen: placed before it is added, so its _ready already
# sees where it is (a stomp's landing resolves there).
func add_floor_hazard(hazard: Node2D, at: Vector2) -> void:
	hazard.add_to_group(HAZARD_GROUP)
	hazard.position = floor_layer.to_local(at.round())
	floor_layer.add_child(hazard)


# Under his scene, y-sorted with the fighters: the quake ring's upright crest.
func add_sorted_hazard(hazard: Node2D, at: Vector2) -> void:
	hazard.add_to_group(HAZARD_GROUP)
	hazard.position = at.round()
	JordanCharacterBody.get_parent().add_child(hazard)


# The next turn in the cycle.
func next_turn() -> String:
	var cycle: Array[String] = cycle_b if phase_b else cycle_a
	var next: String = cycle[turn % cycle.size()]
	turn += 1
	return next


# His figures thrown down from its head onto spots apart from each other, from the player and off the burning lines.
# Returns the throw's id, which every figure in it carries (the gauge pays one parry a throw).
func throw_funkos(turn_kind := 0) -> int:
	next_throw_id += 1
	JordanCharacterBody.explosion_hits_this_cycle = 0
	var count: int = funko_counts[1 if phase_b else 0][turn_kind]
	var from: Vector2 = kaiju.hand_point()
	var player := get_player()
	for spot in funko_spots(count):
		var flight := FunkoThrow.new()
		flight.from = from
		flight.to = spot
		flight.fly_time = throw_fly
		flight.apex = throw_apex
		flight.throw_id = next_throw_id
		flight.player = player
		flight.jordan = JordanCharacterBody
		flight.state_machine = self
		add_hazard(flight, from)
		throws.append(flight)
	JordanCharacterBody.summon_sfx_player.play()
	return next_throw_id


func funko_spots(count: int) -> Array[Vector2]:
	var feet := player_feet()
	var half := FunkoFigure.BODY_SIZE / 2.0
	var area := Rect2(KaijuLayout.ROPES.position + half + Vector2(20, 20), KaijuLayout.ROPES.size - FunkoFigure.BODY_SIZE - Vector2(40, 40))
	var burns := live_burns()
	var spots: Array[Vector2] = []
	for attempt in 800:
		if spots.size() >= count:
			break
		var at := Vector2(rng.randf_range(area.position.x, area.end.x), rng.randf_range(area.position.y, area.end.y)).round()
		if KaijuLayout.box_in_walls(Rect2(at - half, FunkoFigure.BODY_SIZE)) or at.distance_to(feet) < KaijuLayout.FUNKO_FROM_PLAYER:
			continue
		if spots.any(func(other: Vector2) -> bool: return other.distance_to(at) < KaijuLayout.FUNKO_APART):
			continue
		if burns.any(func(burn: Node2D) -> bool: return burn.distance_to_point(at) < KaijuLayout.FUNKO_OFF_BURN):
			continue
		spots.append(at)
	return spots


func live_burns() -> Array:
	return get_tree().get_nodes_in_group(HAZARD_GROUP).filter(
		func(hazard: Node) -> bool: return hazard.get_script() == BurnLine and hazard.is_burning())


func put_out_burns() -> void:
	for burn in live_burns():
		burn.put_out()


# Where a parried stomp throws him (his soles): beside the player on their roomier side - with the kaiju out on the mat,
# the side away from it, so it doesn't stand over him - his body box KNOCK_OFF_GAP past their hurtbox, on their line
# within KNOCK_OFF_SOLES_Y, and clear of the kaiju's walls.
func knock_off_spot() -> Vector2:
	var player := get_player()
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	var hurt: Rect2 = shape.global_transform * shape.shape.get_rect()
	var y := clampf(hurt.end.y, KaijuLayout.KNOCK_OFF_SOLES_Y.x, KaijuLayout.KNOCK_OFF_SOLES_Y.y)
	var box := _body_box_at(Vector2.ZERO)
	var right := Vector2(hurt.end.x + KaijuLayout.KNOCK_OFF_GAP - box.position.x, y)
	var left := Vector2(hurt.position.x - KaijuLayout.KNOCK_OFF_GAP - box.end.x, y)
	var right_room := KaijuLayout.ROPES.end.x - hurt.end.x
	var left_room := hurt.position.x - _wall_edge_at(y)
	var right_first := right_room >= left_room
	if not kaiju.is_home():
		right_first = kaiju.feet_point().x <= hurt.get_center().x
	var first := right if right_first else left
	var second := left if right_first else right
	for spot in [first, second]:
		if KaijuLayout.SOLES_BOUNDS.has_point(spot) and not KaijuLayout.box_in_walls(_body_box_at(spot)):
			return spot.round()
	return first.clamp(KaijuLayout.SOLES_BOUNDS.position, KaijuLayout.SOLES_BOUNDS.end).round()


# His body box with his soles on `soles`.
func _body_box_at(soles: Vector2) -> Rect2:
	var box := JordanArtLayout.local_rect(JordanArtLayout.BODY_BOX)
	box.position += soles - JordanArtLayout.FLOOR_POINT
	return box


func _wall_edge_at(y: float) -> float:
	var edge := KaijuLayout.ROPES.position.x
	for wall in KaijuLayout.WALLS:
		if y >= wall.position.y and y < wall.end.y:
			edge = maxf(edge, wall.end.x)
	return edge


# The kaiju's hop home from `from`, `t` seconds in: true once it has landed. Crouched, then up and across on an arc,
# then down on its feet at home.
func step_return(t: float, from: Vector2) -> bool:
	if t < return_crouch:
		if kaiju.current_anim != &"rear":
			kaiju.play_anim(&"rear")
		return false
	if t < return_crouch + return_hop:
		if kaiju.current_anim != &"leap":
			kaiju.play_anim(&"leap")
		var w := (t - return_crouch) / return_hop
		kaiju.place(from.lerp(KaijuLayout.HOME, w))
		kaiju.set_lift(4.0 * return_apex * w * (1.0 - w))
		return false
	if kaiju.lift > 0.0 or not kaiju.is_home():
		kaiju.place(KaijuLayout.HOME)
		kaiju.set_lift(0.0)
		kaiju.play_anim(&"land", &"idle")
		play_sfx(&"stomp")
	return t >= return_crouch + return_hop + return_land


# His body's own ready comes after this node's, so its hurtbox is looked up rather than read off it.
func _add_down_state(state: Node, state_name: String) -> void:
	state.name = state_name
	state.body = JordanCharacterBody
	state.hurtbox = JordanCharacterBody.get_node("Hurtbox")
	state.state_machine = self
	add_child(state)


func _process(delta: float) -> void:
	if current_state and fighting and stagger_left <= 0.0:
		current_state.Update(delta)


func _physics_process(delta: float) -> void:
	if not fighting:
		return
	# A stagger holds the current state where it is, and it carries on afterwards.
	if stagger_left > 0.0:
		stagger_left -= delta
		return
	if current_state:
		current_state.Physics_Update(delta)


func on_child_transition(state, new_state_name):
	if state != current_state:
		return

	# Defeat, Jordan's or the player's, is terminal, and so is the walk-out his defeat hands over to: nothing late may
	# restart the fight.
	if current_state in [states.get("Defeated"), states.get("WalkOut")] or player_defeated:
		return

	# On the kaiju his taunt is gone: asked for by its old name (the defence suite's punish-window rows), his window is
	# his knock-off.
	if kaiju_mode and new_state_name == "Taunt":
		new_state_name = "Dismounted"
	var new_state = states.get(new_state_name)
	if !new_state:
		return

	if current_state:
		current_state.Exit()

	new_state.Enter()
	current_state = new_state


# His lines call no beats, so the dialogue needs nothing from his intro.
func show_pre_fight_dialogue() -> void:
	# One-shot: the outro's lines end a dialogue too, and must not start the fight again.
	DialogueManager.dialogue_ended.connect(_on_dialogue_ended, CONNECT_ONE_SHOT)
	pre_fight_balloon = DialogueManager.show_dialogue_balloon(load(PRE_FIGHT_DIALOGUE), "start")


# A held skip's way past the lines (BossEntrance): the hand-over their own end makes, made from here
# instead. pre_fight_over keeps it to once.
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
	VsCard.play_intro(self, "jordan", post_dialogue_pre_fight_timer.start)


# The fight opens on the scene's own first state, Idle, which rests IDLE_TIME before his first summon.
func _on_post_dialogue_pre_fight_timer_timeout() -> void:
	JordanCharacterBody.start_music()
	on_child_transition(current_state, initial_state.name)
	fighting = true


func get_player() -> Node2D:
	return get_tree().current_scene.get_node_or_null("Arena/MainPlayer/CharacterBody2D")


# Positioned before it's added, so the hazard's _ready already sees where it spawned.
func add_hazard(hazard: Node2D, spawn_position: Vector2) -> void:
	hazard.position = spawn_position
	get_tree().current_scene.add_child(hazard)


func swarm_over() -> bool:
	if JordanCharacterBody.fight_clock - last_summon_time >= SWARM_WAIT_LIMIT:
		return true
	return get_tree().get_nodes_in_group(HAZARD_GROUP).is_empty()


# The 10-04 probe and the defence suite read his punish window through this: on the kaiju it is his knock-off.
func is_taunting() -> bool:
	return current_state == states.get("Taunt") or (kaiju_mode and current_state == states.get("Dismounted"))


# His punish windows: the taunt, or knocked off the kaiju or clinging to its lowered head after its breath, and a Break.
func is_open() -> bool:
	if kaiju_mode and current_state == states.get("Recoil"):
		return current_state.open
	return is_taunting() or current_state == states.get("Broken")


func is_dismounted() -> bool:
	return kaiju_mode and current_state == states.get("Dismounted")


func stagger(duration: float) -> void:
	stagger_left = maxf(stagger_left, duration)


# The player's finisher cut the taunt short. Idle holds while the stagger timer runs, which stands in for his rest.
# On the kaiju he gets back on it (Remount), which holds on its seat for the stagger; still riding it on its lowered
# head (Recoil), the head comes back up with him on it instead.
func end_taunt(stagger_time: float) -> void:
	if kaiju_mode:
		finisher_stagger_timer.start(stagger_time)
		if current_state == states.get("Recoil"):
			current_state.end_window()
			return
		on_child_transition(current_state, "Remount")
		return
	on_child_transition(current_state, "Idle")
	states["Idle"].rested = IDLE_TIME
	finisher_stagger_timer.start(stagger_time)


# A full Break gauge (BossBreakGauge): whatever he was doing stops, every figure goes, and he is Broken
# until his time is up or the finisher's uppercut ends it.
func enter_broken() -> void:
	if not fighting or current_state in [states.get("Defeated"), states.get("Broken"), states.get("Juggled")]:
		return
	# The kaiju in the air: the Break waits for it to land (JordanStomp), and comes through break_now().
	if kaiju_mode and current_state.has_method("queue_break") and current_state.queue_break():
		return
	break_now()


func break_now() -> void:
	for hazard in get_tree().get_nodes_in_group(HAZARD_GROUP):
		hazard.queue_free()
	stagger_left = 0.0
	finisher_stagger_timer.stop()
	on_child_transition(current_state, "Broken")


# The finisher's uppercut ends the Break window instead of its own clock, as it ends a taunt.
func end_break(delay: float) -> void:
	end_taunt(maxf(delay, 0.01))


# The tiered finisher's first uppercut (JordanScript.begin_juggle).
func enter_juggled() -> void:
	var juggled = states["Juggled"]
	if JordanCharacterBody.defeated or current_state == juggled:
		return
	on_child_transition(current_state, "Juggled")


# Down after a juggle, he gets up where he crashed and summons `delay` after this, as after a taunt.
# Idle's own Enter plays his idle, since the juggle hands back no animation to finish.
func after_juggle(delay: float) -> void:
	end_taunt(maxf(delay, 0.01))


# The one switch past the fight being decided: a juggled Jordan, killed in the air, lands into his
# defeat rather than snapping to its pose mid-flight.
func land_juggled(final_state_name: String) -> void:
	var final_state = states.get(final_state_name)
	if final_state == states.get("Defeated"):
		final_state.lying = true
	current_state.Exit()
	final_state.Enter()
	current_state = final_state


# The fight's floor layer (Arena/GroundFx, which the finisher's ground effects use too), or his scene in
# a fight without one, where his juggle's shadow y-sorts at his soles.
func ground_layer() -> Node2D:
	var arena: Node = JordanCharacterBody.get_parent().get_parent()
	var layer: Node2D = arena.get_node_or_null("GroundFx") if arena else null
	return layer if layer else JordanCharacterBody.get_parent()


func enter_defeated() -> void:
	_end_fight("Defeated")


# FightOutro's won outro, his (JordanScript.take_won_outro): the walk-out waits out the KO and then takes over from his
# defeat (enter_walk_out).
func begin_walk_out(outro: Node, line_delay: float) -> void:
	states["WalkOut"].begin(outro, line_delay)


# The one switch past his defeat, as land_juggled is past the fight being decided: Defeated to the walk-out.
func enter_walk_out() -> void:
	var walk_out = states["WalkOut"]
	if current_state == walk_out:
		return
	if current_state:
		current_state.Exit()
	walk_out.Enter()
	current_state = walk_out


# The player lost: he stops where he is and stands idle. On the kaiju it comes down at home if it was in the air, and
# roars over him.
func enter_player_defeated() -> void:
	_end_fight("Idle")
	player_defeated = true
	if not kaiju_mode or kaiju == null:
		return
	if kaiju.lift > 0.0:
		kaiju.place(KaijuLayout.HOME)
		kaiju.set_lift(0.0)
	kaiju.light_spines(0)
	kaiju.set_charge(0.0)
	kaiju.play_anim(&"roar", &"idle")
	play_sfx(&"roar")
	if JordanCharacterBody.mounted:
		JordanCharacterBody.play_anim(&"ride_taunt")


func _end_fight(final_state_name: String) -> void:
	post_dialogue_pre_fight_timer.stop()
	finisher_stagger_timer.stop()
	fighting = false
	stagger_left = 0.0
	var juggled = states.get("Juggled")
	# In the air, he finishes his fall and his crash first (land_juggled). The juggle draws itself on
	# its own clock, so it plays out with the fight no longer running.
	if juggled and current_state == juggled:
		juggled.final_state = final_state_name
		return
	on_child_transition(current_state, final_state_name)
