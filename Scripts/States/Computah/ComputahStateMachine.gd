extends Node

@export var initial_state : State

@export var states : Dictionary = {}
@export var current_state : State
var Projectile = preload("res://Scenes/Bosses/ComputahRocketProjectilesScene.tscn")
@export var ComputahCharacterBody : CharacterBody2D
var rocket_projectile_count = 0

var rocket_projectiles : Array = []

#TIMERS
@export var post_dialogue_pre_fight_timer: Timer
@export var rocket_fire_interval_timer: Timer
@export var laser_beam_duration_timer: Timer
@export var downed_state_timer: Timer
@export var recovery_timer: Timer
@export var laughing_timer: Timer

const MAX_ROCKETS := 5


# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	DialogueManager.show_dialogue_balloon(load("res://Dialogue/GreysonAndComputahPreFightDialogue.dialogue"), "start")
	# One-shot: the outro's lines end a dialogue too, and must not start the fight again.
	DialogueManager.dialogue_ended.connect(_on_dialogue_ended, CONNECT_ONE_SHOT)

	for child in get_children():
		if child is State:
			states[child.name] = child

	print("State Machine initialized with states: ", states.keys())

	if initial_state:
		current_state = initial_state
		current_state.Enter()


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	if current_state:
		current_state.Update(delta)

func _physics_process(delta: float) -> void:
	if current_state:
		current_state.Physics_Update(delta)

func on_child_transition(state, new_state_name):
	if state != current_state:
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
	post_dialogue_pre_fight_timer.start()


func _on_post_dialogue_pre_fight_timer_timeout() -> void:
	print("post dialogue timer done")
	var boss = get_parent()
	if boss and boss.has_method("start_music"):
		boss.start_music()
	_start_attack_cycle()


# One full attack loop: rocket barrage -> growing laser sweep -> a
# short vulnerable/Downed window -> a taunting laugh -> back around.
# Keeps the original rocket-barrage and laser-sweep attacks intact
# while giving the fight an actual loop and a way to damage the boss.
func _start_attack_cycle() -> void:
	_apply_rage_scaling()
	on_child_transition(current_state, "FireRockets")
	rocket_fire_interval_timer.start()


func _apply_rage_scaling() -> void:
	# Ramp up intensity as Computah's health drops - mirrors Eric's
	# lerp-based rage scaling.
	var ratio := 1.0
	var boss = ComputahCharacterBody
	if boss and boss.has_method("get_health_ratio"):
		ratio = boss.get_health_ratio()
	var rage = clamp(1.0 - ratio, 0.0, 1.0)

	# Fires rockets faster and sweeps the laser beams quicker the lower
	# Computah's health gets.
	rocket_fire_interval_timer.wait_time = lerp(0.5, 0.18, rage)

	var laser_state = states.get("LaserBeam")
	if laser_state:
		laser_state.sweep_duration = lerp(2.0, 1.4, rage)
		laser_beam_duration_timer.wait_time = laser_state.get_total_duration()


func fire_rockets() -> void:
	var projectile = Projectile.instantiate()
	projectile.global_position = ComputahCharacterBody.global_position
	get_tree().current_scene.add_child(projectile)
	rocket_projectile_count += 1

	var sfx = ComputahCharacterBody.get_node_or_null("RocketSfxPlayer")
	if sfx:
		sfx.play()


func _on_rocket_fire_interval_timer_timeout() -> void:
	if rocket_projectile_count < MAX_ROCKETS:
		fire_rockets()
	else:
		rocket_fire_interval_timer.stop()
		rocket_projectile_count = 0
		on_child_transition(current_state, "LaserBeam")
		laser_beam_duration_timer.start()


func _on_laser_beam_duration_timer_timeout() -> void:
	laser_beam_duration_timer.stop()
	on_child_transition(current_state, "Downed")
	downed_state_timer.start()
	_play_downed_stinger()


func _on_downed_timer_timeout() -> void:
	downed_state_timer.stop()
	on_child_transition(current_state, "Idle")
	recovery_timer.start()


func _on_recovery_timer_timeout() -> void:
	recovery_timer.stop()
	on_child_transition(current_state, "Laughing")
	laughing_timer.start()


func _on_laughing_timer_timeout() -> void:
	laughing_timer.stop()
	_start_attack_cycle()


func end_phase_one() -> void:
	for timer in [post_dialogue_pre_fight_timer, rocket_fire_interval_timer, laser_beam_duration_timer, downed_state_timer, recovery_timer, laughing_timer]:
		timer.stop()
	rocket_projectile_count = 0
	# Idle's Enter shuts the hurtbox and the laser state's Exit hides and disarms the beams.
	on_child_transition(current_state, "Idle")
	for node in get_tree().current_scene.get_children():
		if node.scene_file_path == Projectile.resource_path:
			node.queue_free()


func _play_downed_stinger() -> void:
	if not ComputahCharacterBody:
		return
	var sfx = ComputahCharacterBody.get_node_or_null("DownedSfxPlayer")
	if sfx:
		sfx.play()
