extends Node

@export var initial_state : State

@export var states : Dictionary = {}
@export var current_state : State

#TIMERS
@export var post_dialogue_pre_fight_timer: Timer
@export var rest_timer: Timer
@export var downed_state_timer: Timer

const VsCard := preload("res://Scripts/VsCard.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")
const EricPacing := preload("res://Scripts/EricPacing.gd")
const DROPPED_SWORD := preload("res://Scripts/States/Eric/EricDroppedSword.gd")

const PRE_FIGHT_DIALOGUE := "res://Dialogue/EricPreFight.dialogue"
const HAZARD_GROUP := "eric_hazard"
const ATTACKS := ["Earthquake", "Whirlwind", "SwordThrow", "BearHug"]

# 0 at full health, 1 at none; set at the start of each chain. Attack states scale their
# speeds with it (EricPacing.raged).
var rage := 0.0
var chain : Array = []
var last_attack := ""
var state_after_rest := ""
var defeated := false
# His sword while it's out of his hands (EricDroppedSword), which EricBroken and EricJuggled share.
var dropped_sword: Node2D
# The pre-fight lines' balloon, which a held skip takes down, and whether those lines have handed
# over to the VS card yet.
var pre_fight_balloon: Node
var pre_fight_over := false

@onready var boss = get_parent()


# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	for child in get_children():
		if child is State:
			states[child.name] = child

	print("State Machine initialized with states: ", states.keys())

	if initial_state:
		current_state = initial_state
		# Deferred until the scene is up: his entrance moves him, the player and the gates, and
		# reads all three off the fight scene.
		current_state.Enter.call_deferred()


# His entrance's lines call its beats, so it passes itself along to the dialogue.
func show_pre_fight_dialogue(intro: State) -> void:
	# One-shot: the outro's lines end a dialogue too, and must not start the fight again.
	DialogueManager.dialogue_ended.connect(_on_dialogue_ended, CONNECT_ONE_SHOT)
	pre_fight_balloon = DialogueManager.show_dialogue_balloon(load(PRE_FIGHT_DIALOGUE), "start", [intro])


# A held skip's way past the lines (BossEntrance), whether they were ever put up or not: the hand-over
# their own end makes, made from here instead. pre_fight_over keeps it to once - the lines can end on
# their own inside the skip, on the beat it ran out.
func end_pre_fight_dialogue() -> void:
	if pre_fight_over:
		return
	if DialogueManager.dialogue_ended.is_connected(_on_dialogue_ended):
		DialogueManager.dialogue_ended.disconnect(_on_dialogue_ended)
	_on_dialogue_ended(null)


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	if current_state:
		current_state.Update(delta)

func _physics_process(delta: float) -> void:
	if current_state:
		current_state.Physics_Update(delta)

func on_child_transition(state, new_state_name):
	# Defeat is terminal: a late timer or animation signal must never restart the fight.
	if state != current_state or defeated:
		return

	var new_state = states.get(new_state_name)
	if !new_state:
		return

	if current_state:
		current_state.Exit()

	new_state.Enter()
	current_state = new_state

func _on_dialogue_ended(dialogue: Object) -> void:
	print("post dialogue timer started: ", post_dialogue_pre_fight_timer)
	pre_fight_over = true
	var intro = states.get("Intro")
	if intro:
		intro.lines_over()
	VsCard.play_intro(self, "eric", post_dialogue_pre_fight_timer.start)


func _on_post_dialogue_pre_fight_timer_timeout() -> void:
	print("post dialogue timer done")
	if boss and boss.has_method("start_music"):
		boss.start_music()
	start_chain(0.0)


func _play_downed_stinger() -> void:
	if boss:
		var sfx = boss.get_node_or_null("DownedSfxPlayer")
		if sfx:
			sfx.play()


# A chain of different attacks in a random order, then the window (EricPacing's window_state).
func start_chain(delay: float) -> void:
	var health_ratio: float = boss.get_health_ratio()
	rage = clampf(1.0 - health_ratio, 0.0, 1.0)
	var enraged: bool = health_ratio <= EricPacing.value("rage_chain_health_ratio")
	var count: int = EricPacing.value("rage_attacks_per_chain" if enraged else "attacks_per_chain")

	var bag := ATTACKS.duplicate()
	bag.shuffle()
	if bag[0] == last_attack:
		bag.push_back(bag.pop_front())
	chain = bag.slice(0, count)
	_next_attack(delay)


# Called by an attack state once Eric is back in his idle pose at his starting spot.
func attack_finished() -> void:
	if chain.is_empty():
		downed_state_timer.start(EricPacing.raged("window_time", rage))
		on_child_transition(current_state, EricPacing.value("window_state"))
		_play_downed_stinger()
	else:
		_next_attack(EricPacing.raged("attack_gap", rage))


func _next_attack(delay: float) -> void:
	last_attack = chain.pop_front()
	if delay <= 0.0:
		on_child_transition(current_state, last_attack)
		return
	state_after_rest = last_attack
	on_child_transition(current_state, "Idle")
	rest_timer.start(delay)


func _on_rest_timer_timeout() -> void:
	on_child_transition(states.get("Idle"), state_after_rest)


func _on_downed_timer_timeout() -> void:
	start_chain(EricPacing.value("recovery_rest"))


# Anything lying on the floor (his waves, the ring, the dust) goes on the arena's ground layer, under
# everyone standing on it. Anything off the floor (his swords) lives under his scene root, ahead of
# his body: it sorts among the fighters at its ground point, and doesn't move with him.
func add_hazard(hazard: Node2D, spawn_position: Vector2, on_floor := true) -> void:
	hazard.add_to_group(HAZARD_GROUP)
	var layer: Node2D = ground_layer() if on_floor else boss.get_parent()
	hazard.position = layer.to_local(spawn_position)
	layer.add_child(hazard)
	if not on_floor:
		layer.move_child(hazard, 0)


# The fight's floor layer (Arena/GroundFx, which the finisher's ground effects use too), or his scene
# root in a scene without one.
func ground_layer() -> Node2D:
	var arena: Node = boss.get_parent().get_parent()
	var layer: Node2D = arena.get_node_or_null("GroundFx") if arena else null
	return layer if layer else boss.get_parent()


func enter_defeated() -> void:
	_end_fight("Downed")


# The player lost: he stops attacking and stands idle.
func enter_player_defeated() -> void:
	_end_fight("Idle")


# Called by the boss after a parry: his attack stops and he's open to punches for `duration`, then he
# picks himself up at `home`, where the attack started. `from_reflect` marks the one his own sword
# leaves him in, which is the only stagger the finisher can daze.
func parry_stagger(duration: float, home: Vector2, from_reflect := false) -> void:
	states["ParryStaggered"].duration = duration
	states["ParryStaggered"].home = home
	states["ParryStaggered"].from_reflect = from_reflect
	on_child_transition(current_state, "ParryStaggered")


# The V2 whirlwind's last beat (EricWhirlwind): the spin ends with him throwing the sword instead of
# stopping dizzy, and the throw owns it from its own red tell onwards.
func throw_from_whirlwind() -> void:
	states["SwordThrow"].from_whirlwind = true
	on_child_transition(current_state, "SwordThrow")


# A full Break gauge (BossBreakGauge): whatever he was doing stops, everything he threw goes, and he is
# Broken until he gets up and starts a new chain.
func enter_broken() -> void:
	if defeated or boss.boss_health <= 0 or current_state == states.get("Broken"):
		return
	_stop_everything()
	chain = []
	on_child_transition(current_state, "Broken")


# The tiered finisher's first uppercut (EricScript.begin_juggle): from a Break his sword stays where
# it stands; from anywhere else the uppercut knocks it out of his grip.
func enter_juggled() -> void:
	var juggled = states["Juggled"]
	if defeated or current_state == juggled:
		return
	if current_state == states.get("Broken"):
		current_state.keep_sword = true
	_stop_everything()
	chain = []
	on_child_transition(current_state, "Juggled")


# Down after a juggle, he gets up for his sword (EricBroken's retrieve), and his next chain starts `delay`
# after this, or recovery_rest after he has it.
func after_juggle(delay: float) -> void:
	var broken = states["Broken"]
	broken.retrieve_only = true
	broken.chain_delay = delay
	on_child_transition(current_state, "Broken")


# The one switch past the fight being decided: a juggled Eric, killed in the air, lands into his defeat.
func land_juggled(final_state_name: String) -> void:
	var final_state = states.get(final_state_name)
	if final_state == states.get("Downed"):
		final_state.lying = true
	current_state.Exit()
	final_state.Enter()
	current_state = final_state


func drop_sword() -> void:
	if is_instance_valid(dropped_sword):
		return
	dropped_sword = DROPPED_SWORD.new()
	dropped_sword.plant(boss, self)


func clear_dropped_sword() -> void:
	if is_instance_valid(dropped_sword):
		dropped_sword.queue_free()
	dropped_sword = null


func _end_fight(final_state_name: String) -> void:
	post_dialogue_pre_fight_timer.stop()
	# A fight decided over the top of his entrance still leaves the ring set: gates shut, sword in
	# his hands, both fighters on their marks.
	var intro = states.get("Intro")
	if intro:
		intro.finish_entrance()
	_stop_everything()
	var juggled = states.get("Juggled")
	# In the air, he finishes his fall and his crash first (land_juggled).
	if juggled and current_state == juggled:
		juggled.final_state = final_state_name
	elif current_state != states.get(final_state_name):
		on_child_transition(current_state, final_state_name)
	# Terminal whoever lost.
	defeated = true


func _stop_everything() -> void:
	ParryTell.clear(boss)
	rest_timer.stop()
	downed_state_timer.stop()
	states["ParryStaggered"].stagger_timer.stop()
	# Anything he threw that outlives what he was doing could still hurt the player.
	for hazard in get_tree().get_nodes_in_group(HAZARD_GROUP):
		hazard.queue_free()
