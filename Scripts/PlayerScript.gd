extends CharacterBody2D

#CONSTANTS
const SPEED = 600.0
const DODGE_SPEED = 5000
const GRAB_KNOCKBACK_SPEED = 4200.0
const FightOutro := preload("res://Scripts/FightOutro.gd")
# const JUMP_VELOCITY = -400.0

#DODGING VARS
var is_dodging = false
var dodge_timer = 0.0
var dodge_time = 0.05
var direction = Vector2.ZERO
# Read by Computah's laser, which players are meant to dash through.
var last_dodge_physics_frame := -1
var previous_dodge_physics_frame := -1

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

@onready var combo: Node = $Combo
var punch_buffered := false

#FACING
# Rows of player_4dir_sheet.png; the animations only step the column.
enum Facing { DOWN, UP, LEFT, RIGHT }
# Bosses add the hurtbox to face to this group; its shape has to be a child named CollisionShape2D.
const BOSS_TARGET_GROUP := "boss_target"
# The facing only turns to the other axis once the boss is this far past the 45° diagonal, so
# walking along the diagonal can't flicker it.
const FACING_HYSTERESIS_DEGREES := 10.0
# Between Carter and Josh, the other one has to be this many px nearer to take over, so standing
# midway can't flip the facing back and forth.
const TARGET_SWITCH_MARGIN := 12.0
# Punch hitbox per facing, in texels from the frame centre: 4.33 across the arm by 7.67 along it,
# reaching 2 texels past the glove at full extension, the size and reach of the original up-only
# punch. The down punch's glove is drawn over the body, so its box instead reaches 5 texels past the
# collision box, as far as the up punch does: a boss with collision stops the player at that box.
const PUNCH_HITBOXES := {
	Facing.DOWN: Rect2(-1.665, 11.33, 4.33, 7.67),
	Facing.UP: Rect2(-6.165, -18.0, 4.33, 7.67),
	Facing.LEFT: Rect2(-13.0, -8.165, 7.67, 4.33),
	Facing.RIGHT: Rect2(5.33, -8.165, 7.67, 4.33),
}

var facing := Facing.UP
var facing_target: Area2D
@onready var punch_hitbox: CollisionShape2D = $Hitbox/CollisionShape2D

#AUDIO
@onready var hurt_sfx_player: AudioStreamPlayer = $HurtSfxPlayer

var is_talking = false
# Set while Eric's bear hug holds the player.
var is_grabbed := false
# Set once the fight is decided, won or lost: from then on the player can't act or be hurt.
var fight_over := false

var state_machine : Node
var current_state : State
func _ready():
	# var hurtBox = get_node("Hurtbox")
	# var hitBox = get_node("Hitbox")
	hurtBox.area_entered.connect(_on_hurtbox_entered)
	# hitBox.area_entered.connect(_on_hitbox_entered)
	hitBox.monitoring = false
	hitBox.monitorable = false

	# animationPlayer.play("idle_down")

	state_machine = get_node("StateMachine")
	current_state = state_machine.current_state
	is_talking = true

	sprite_base_position = sprite.position
	_apply_facing()
	hurt_sfx_player.stream = load("res://Assets/Audio/SFX/player_hurt.ogg")

	DialogueManager.dialogue_ended.connect(_on_dialogue_ended)

func _process(delta: float) -> void:
	if punch_buffered and not combo.report_pending():
		punch_buffered = false
		state_machine.on_child_transition(state_machine.current_state, "Punching")
	current_state = state_machine.current_state
	if playerHealth <= 0 and not fight_over:
		# A step late, so a boss beaten on the same frame still wins the tie.
		FightOutro.finish_fight.call_deferred(get_tree(), false)

func _physics_process(delta: float) -> void:
	_update_facing()

	# Don't move during punch or block
	if current_state.name == "Punching" || is_talking || is_grabbed || fight_over:
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
	if event.is_action_pressed("punch") and not is_talking and not is_grabbed and not fight_over:
		combo.register_press()
		# A press held back until the last punch's report is in, so its hit can't be lost.
		if combo.report_pending():
			punch_buffered = true
			return

	# Don't allow any input if currently punching or blocking
	if current_state.name == "Punching" || is_talking || is_grabbed || fight_over:
		# print("Current state: ", current_state.name)
		return

	if event.is_action_pressed("dodge"):
		is_dodging = true
		direction = Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
		previous_dodge_physics_frame = last_dodge_physics_frame
		last_dodge_physics_frame = Engine.get_physics_frames()

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


func _on_invincibility_timer_timeout() -> void:
	is_invincible = false
	invincibility_timer.stop()
	print("Invincibility ended")

func _on_dialogue_ended(dialogue: Object) -> void:
	is_talking = false

func take_damage() -> void:
	# At 0 the loss is only reported at the end of the frame, and nothing may hurt them before that.
	if fight_over or playerHealth <= 0:
		return
	if is_invincible:
		print("Player is invincible, ignoring damage")
		return
	playerHealth -= 1
	combo.reset()
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


# Eric's bear hug draws the held player in his own frames.
func grab() -> void:
	is_grabbed = true
	is_dodging = false
	dodge_timer = 0.0
	punch_buffered = false
	velocity = Vector2.ZERO
	sprite.visible = false
	state_machine.on_child_transition(state_machine.current_state, "Idle")


# A held player can't dodge, so every squeeze lands, even inside the last one's invincibility.
func take_grab_damage() -> void:
	is_invincible = false
	take_damage()


func release_grab(push_direction: Vector2) -> void:
	is_grabbed = false
	sprite.visible = true
	# Slows to a stop through the normal movement deceleration: about 140 px on the diagonal toss.
	velocity = push_direction.normalized() * GRAB_KNOCKBACK_SPEED
	is_invincible = true
	invincibility_timer.start()
	_flicker_while_invincible(invincibility_timer.wait_time)


# Called by FightOutro once the fight is decided.
func end_fight() -> void:
	fight_over = true
	punch_buffered = false
	is_dodging = false
	dodge_timer = 0.0
	# The fight can end inside a physics callback, where ending a punch can't switch its hitbox off.
	_stand_still.call_deferred()


# After the bosses have stopped, so a bear hug has already let go of the player.
func _stand_still() -> void:
	velocity = Vector2.ZERO
	state_machine.on_child_transition(state_machine.current_state, "Idle")
	# Idle would still start the walk animation while a direction key is held.
	state_machine.set_process(false)
	state_machine.set_physics_process(false)


func _update_facing() -> void:
	# Held from the press until the boss has reported the swing: a hurtbox reports a punch after
	# the hitbox switches off, and moving the hitbox before then would lose the hit.
	if state_machine.current_state.name == "Punching" or combo.report_pending():
		return
	var aim := _aim()
	if aim == Vector2.ZERO:
		return
	var new_facing := _facing_toward(aim)
	if new_facing != facing:
		facing = new_facing
		_apply_facing()


# Toward the nearest point of the nearest target's hurtbox, so the player faces the side of the
# boss they're on (its centre once they're inside it). With no target, as during boss 2's morph,
# the facing follows movement.
func _aim() -> Vector2:
	var target := _nearest_target()
	if target == null:
		return velocity
	var box := _hurtbox_rect(target)
	if box.has_point(global_position):
		return box.get_center() - global_position
	return global_position.clamp(box.position, box.end) - global_position


func _nearest_target() -> Area2D:
	var nearest: Area2D = null
	var nearest_distance := INF
	for target in get_tree().get_nodes_in_group(BOSS_TARGET_GROUP):
		var box := _hurtbox_rect(target)
		var distance := global_position.distance_to(global_position.clamp(box.position, box.end))
		if target == facing_target:
			distance -= TARGET_SWITCH_MARGIN
		if distance < nearest_distance:
			nearest = target
			nearest_distance = distance
	facing_target = nearest
	return nearest


func _hurtbox_rect(target: Area2D) -> Rect2:
	var shape: CollisionShape2D = target.get_node("CollisionShape2D")
	return shape.global_transform * shape.shape.get_rect()


func _facing_toward(aim: Vector2) -> Facing:
	var switch_ratio := tan(deg_to_rad(45.0 + FACING_HYSTERESIS_DEGREES))
	var horizontal := facing == Facing.LEFT or facing == Facing.RIGHT
	if horizontal:
		horizontal = absf(aim.y) < absf(aim.x) * switch_ratio
	else:
		horizontal = absf(aim.x) > absf(aim.y) * switch_ratio
	if horizontal:
		return Facing.RIGHT if aim.x > 0.0 else Facing.LEFT
	return Facing.DOWN if aim.y > 0.0 else Facing.UP


func _apply_facing() -> void:
	sprite.frame_coords.y = facing
	var box: Rect2 = PUNCH_HITBOXES[facing]
	punch_hitbox.position = box.get_center()
	(punch_hitbox.shape as RectangleShape2D).size = box.size
