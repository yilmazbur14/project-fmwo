extends CharacterBody2D

#CONSTANTS
const SPEED = 600.0
const DODGE_SPEED = 5000
# const JUMP_VELOCITY = -400.0

#DODGING VARS
var is_dodging = false
var dodge_timer = 0.0
var dodge_time = 0.05
var direction = Vector2.ZERO

#PLAYER STATS
var playerHealth = 6
# var playerHealth = 1000

#TIMERS
@export var invincibility_timer : Timer

var is_invincible = false



# #ANIMATION
# @onready var animationPlayer = $AnimationPlayer

@export var healthUI : Control
@export var hurtBox : Area2D
@export var hitBox : Area2D

@onready var sprite: Sprite2D = $Sprite2D
var sprite_base_position: Vector2

#AUDIO
@onready var hurt_sfx_player: AudioStreamPlayer = $HurtSfxPlayer

var is_talking = false
var is_in_whirlwind = false

var state_machine : Node
var current_state : State
func _ready():
	# var hurtBox = get_node("Hurtbox")
	# var hitBox = get_node("Hitbox")
	hurtBox.area_entered.connect(_on_hurtbox_entered)
	hurtBox.area_exited.connect(_on_hurtbox_area_exited)
	# hitBox.area_entered.connect(_on_hitbox_entered)
	hitBox.monitoring = false
	hitBox.monitorable = false

	# animationPlayer.play("idle_down")

	state_machine = get_node("StateMachine")
	current_state = state_machine.current_state
	is_talking = true

	sprite_base_position = sprite.position
	hurt_sfx_player.stream = load("res://Assets/Audio/SFX/player_hurt.ogg")

	DialogueManager.dialogue_ended.connect(_on_dialogue_ended)

func _process(delta: float) -> void:
	current_state = state_machine.current_state
	if playerHealth <= 0:
		get_tree().change_scene_to_file("res://Scenes/Core/DefeatScene.tscn")

	if is_in_whirlwind:
		# print("Player is in whirlwind, applying damage")
		take_damage()

func _physics_process(delta: float) -> void:

	# Don't move during punch or block
	if current_state.name == "Punching" || is_talking:
		return

	if is_dodging:
		dodge_timer += delta
		velocity = direction.normalized() * DODGE_SPEED

		if dodge_timer >= dodge_time:
			is_dodging = false
			dodge_timer = 0.0

	else:
		var directionHorz := Input.get_axis("ui_left", "ui_right")
		var directionVert := Input.get_axis("ui_up", "ui_down")

		if directionHorz:
			velocity.x = directionHorz * SPEED
		else:
			velocity.x = move_toward(velocity.x, 0, SPEED)

		if directionVert:
			velocity.y = directionVert * SPEED
		else:
			velocity.y = move_toward(velocity.y, 0, SPEED)

	move_and_slide()

func _input(event: InputEvent) -> void:
	# Don't allow any input if currently punching or blocking
	if current_state.name == "Punching" || is_talking:
		# print("Current state: ", current_state.name)
		return

	if event.is_action_pressed("dodge"):
		is_dodging = true
		direction = Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")

	if event.is_action_pressed("punch"):
		# print("Punch")
		state_machine.on_child_transition(current_state, "Punching")

func _on_hurtbox_entered(area: Area2D) -> void:
	print("Hurtbox entered by: ", area.name)
	print("Groups: ", area.get_groups())
	if is_invincible:
		print("Player is invincible, ignoring damage")
		return
	if area.is_in_group("enemy projectile"):
		take_damage()

	if area.is_in_group("whirlwind"):
		print("Player entered whirlwind area")
		is_in_whirlwind = true


func _on_invincibility_timer_timeout() -> void:
	is_invincible = false
	invincibility_timer.stop()
	print("Invincibility ended")

func _on_dialogue_ended(dialogue: Object) -> void:
	is_talking = false

func take_damage() -> void:
	if is_invincible:
		print("Player is invincible, ignoring damage")
		return
	playerHealth -= 1
	healthUI.update_health(playerHealth)
	invincibility_timer.start()
	is_invincible = true
	print(playerHealth)
	_hit_feedback()
	hurt_sfx_player.play()
	_flicker_while_invincible(invincibility_timer.wait_time)


func _hit_feedback() -> void:
	if not sprite:
		return
	sprite.modulate = Color(3, 0.6, 0.6)
	var flash_tween = create_tween()
	flash_tween.tween_property(sprite, "modulate", Color(1, 1, 1), 0.15)

	var shake_tween = create_tween()
	for i in 3:
		var offset = Vector2(randf_range(-4, 4), randf_range(-4, 4))
		shake_tween.tween_property(sprite, "position", sprite_base_position + offset, 0.025)
	shake_tween.tween_property(sprite, "position", sprite_base_position, 0.025)


func _flicker_while_invincible(duration: float) -> void:
	if not sprite:
		return
	var flicker_tween = create_tween()
	var cycles = max(int(duration / 0.1), 1)
	for i in cycles:
		flicker_tween.tween_property(sprite, "modulate:a", 0.3, 0.05)
		flicker_tween.tween_property(sprite, "modulate:a", 1.0, 0.05)


func _on_hurtbox_area_exited(area: Area2D) -> void:
	if area.is_in_group("whirlwind"):
		print("Player exited whirlwind area")
		is_in_whirlwind = false
