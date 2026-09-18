extends CharacterBody2D

# A fight can hold the player for a parry-only sequence, where only the guard answers
# (lock_actions), point them at what is rushing them (face_point) and put them somewhere (warp_to).
# PlayerCombatFx draws the lock and the warp from these signals.
signal actions_locked
signal actions_unlocked
signal warped(from: Vector2, to: Vector2)

#CONSTANTS
const SPEED = 600.0
const DODGE_SPEED = 5000
const GRAB_KNOCKBACK_SPEED = 4200.0
const FightOutro := preload("res://Scripts/FightOutro.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
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
@onready var finisher: Node = $Finisher
@onready var defense: Node = $Defense
@onready var hype: Node = $Hype
@onready var status: Node = $Status
# A copy of the hurtbox left where a dash started; see PlayerDefense's perfect dodge.
@onready var dodge_ghost: Area2D = get_parent().get_node("DodgeGhost")

#FACING
# Rows of player_4dir_sheet.png; the animations only step the column.
enum Facing { DOWN, UP, LEFT, RIGHT }
# Bosses add the hurtbox to face to this group; its shape has to be a child named CollisionShape2D.
const BOSS_TARGET_GROUP := "boss_target"
# Hazards the player can punch away, like Jordan's figures, add their hurtbox (shaped the same way) to
# this group while they're worth turning to. The nearest one within this many px takes the facing if
# it's nearer than the nearest boss by more than TARGET_SWITCH_MARGIN.
const THREAT_GROUP := "facing_threat"
const THREAT_FACING_RADIUS := 240.0
# After turning to a threat the facing holds for this many seconds, so a swarm shifting around a
# moving player can't flicker it.
const THREAT_FACING_HOLD := 0.25
# The facing only turns to the other axis once the boss is this far past the 45° diagonal, so
# walking along the diagonal can't flicker it.
const FACING_HYSTERESIS_DEGREES := 10.0
# Between Carter and Josh, or two threats, the other one has to be this many px nearer to take over,
# and a threat being faced keeps the facing this far past THREAT_FACING_RADIUS, so standing midway
# can't flip the facing back and forth.
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
var threat_turn_frame := -1
@onready var punch_hitbox: CollisionShape2D = $Hitbox/CollisionShape2D

#AUDIO
@onready var hurt_sfx_player: AudioStreamPlayer = $HurtSfxPlayer

var is_talking = false
# Set while Eric's bear hug holds the player.
var is_grabbed := false
# Set once the fight is decided, won or lost: from then on the player can't act or be hurt.
var fight_over := false
# Set while the finisher plays, from the beat after the charged punch until the player lands: they
# can't act, turn or be hurt.
var is_finishing := false
# Set while a fight holds the player for a parry-only sequence, like Carter's clones: they can't
# move, dash or punch, and the guard and its parry are all that answer. It is its own flag on
# purpose: is_grabbed and is_talking cut the block press off before it reaches the guard.
var is_action_locked := false
# Where a fight wants the player looking, or Vector2.INF for the usual rules.
var facing_point := Vector2.INF

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
	if punch_buffered and not is_finishing and not combo.report_pending():
		punch_buffered = false
		state_machine.on_child_transition(state_machine.current_state, "Punching")
	current_state = state_machine.current_state
	if playerHealth <= 0 and not fight_over:
		# A step late, so a boss beaten on the same frame still wins the tie.
		FightOutro.finish_fight.call_deferred(get_tree(), false)

func _physics_process(delta: float) -> void:
	_update_facing()

	# A parry-only sequence roots the player where the fight put them: they still turn, but nothing
	# here moves them, and the fight is free to write global_position itself.
	if is_action_locked:
		return

	# Don't move during punch or block
	if current_state.name == "Punching" || is_talking || is_grabbed || fight_over || is_finishing:
		return
	if defense.is_guard_broken:
		return

	# Held block brings the guard back up once a dash or a punch is over.
	if Input.is_action_pressed("block") and not punch_buffered:
		_raise_guard()

	if is_dodging:
		dodge_timer += delta
		velocity = direction.normalized() * DODGE_SPEED

		if dodge_timer >= dodge_time:
			is_dodging = false
			dodge_timer = 0.0
			defense.on_dash_ended()
			var state_name: String = state_machine.current_state.name
			if state_name == "Idle" or state_name == "Walking":
				state_machine.on_child_transition(state_machine.current_state, "DashRecovery")

	elif defense.is_dash_recovering():
		velocity = Vector2.ZERO

	else:
		# Reversed while a status inverts the controls (PlayerStatus); the axes stay separate, so the
		# diagonal is as fast as it has always been.
		var steer: Vector2 = status.steer(InputSettings.move_vector())
		var directionHorz := steer.x
		var directionVert := steer.y
		var speed := SPEED
		if state_machine.current_state.name == "Blocking":
			speed *= defense.block_move_speed_ratio

		# Slowing down stays at full rate, so a guard raised mid-knockback still stops the player.
		if directionHorz:
			velocity.x = directionHorz * speed
		else:
			velocity.x = move_toward(velocity.x, 0, SPEED)

		if directionVert:
			velocity.y = directionVert * speed
		else:
			velocity.y = move_toward(velocity.y, 0, SPEED)

	move_and_slide()

func _input(event: InputEvent) -> void:
	# The finisher swallows these presses before they reach this node; this guard doesn't rely on that order.
	if is_finishing or finisher.is_input_locked():
		return
	# Stunned: no punch, dash or guard until it wears off.
	if defense.is_guard_broken:
		return
	# A dash's recovery frames: the guard may go up, and a parry ends them, but nothing else counts.
	if defense.is_dash_recovering() and not event.is_action_pressed("block"):
		return
	# A parry-only sequence: the guard is the only answer the player has. Block presses go on through
	# to on_block_pressed() and _raise_guard(), so parries read exactly as they always do.
	if is_action_locked and not event.is_action_pressed("block"):
		return
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

	if event.is_action_pressed("block"):
		# A press during a dash still counts toward a parry; the guard goes up when the dash ends.
		defense.on_block_pressed()
		_raise_guard()

	if event.is_action_pressed("dodge"):
		# Before anything about the dash is set, so a refused one can't grant dash immunity.
		if not defense.try_spend_dash():
			return
		if state_machine.current_state.name == "Blocking":
			state_machine.on_child_transition(state_machine.current_state, "Idle")
		is_dodging = true
		direction = status.steer(InputSettings.move_vector())
		previous_dodge_physics_frame = last_dodge_physics_frame
		last_dodge_physics_frame = Engine.get_physics_frames()
		defense.on_dash_started()

	if event.is_action_pressed("punch"):
		# print("Punch")
		# The live state: the guard may have gone up earlier in this same input flush.
		state_machine.on_child_transition(state_machine.current_state, "Punching")


func _raise_guard() -> void:
	if is_dodging or not defense.can_raise_guard():
		return
	var state: State = state_machine.current_state
	if state.name == "Idle" or state.name == "Walking" or state.name == "DashRecovery":
		state_machine.on_child_transition(state, "Blocking")


func _on_hurtbox_entered(area: Area2D) -> void:
	print("Hurtbox entered by: ", area.name)
	print("Groups: ", area.get_groups())
	if area.is_in_group("enemy projectile"):
		receive_hit(HitInfo.from_area(area))


func _on_invincibility_timer_timeout() -> void:
	is_invincible = false
	invincibility_timer.stop()
	print("Invincibility ended")

func _on_dialogue_ended(dialogue: Object) -> void:
	is_talking = false

# Every attack reaches the player through here. Returns a HitInfo.Result; for a grab, HIT means the
# grab landed and the caller grabs.
func receive_hit(hit: RefCounted) -> int:
	var result: int = defense.resolve_hit(hit)
	if result == HitInfo.Result.HIT and hit.damage > 0:
		_apply_damage(hit)
	defense.log_hit(hit, result)
	return result


# This frame the attack touches the dodge ghost but not the player. Attackers that loop over their
# overlaps report either this or receive_hit(), never both.
func receive_near_miss(hit: RefCounted) -> void:
	defense.resolve_near_miss(hit)


func is_dodge_ghost(area: Area2D) -> bool:
	return area == dodge_ghost


func dodge_ghost_position() -> Vector2:
	return defense.dodge_ghost_position()


func _apply_damage(hit: RefCounted) -> void:
	playerHealth = maxi(playerHealth - hit.damage, 0)
	if playerHealth <= 0:
		status.clear_all()
		unlock_actions()
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


# A fight holds the player for a reaction test: movement, the dash and punches are off, while the
# guard, its parry window and the streak behind it are untouched. A dash in the air is cut and a
# buffered punch dropped; a swing already in the air finishes, since its hitbox is already live. A
# raised guard stays up. Locking twice does nothing, and neither does unlocking a free player.
func lock_actions() -> void:
	if is_action_locked or fight_over:
		return
	is_action_locked = true
	velocity = Vector2.ZERO
	is_dodging = false
	dodge_timer = 0.0
	punch_buffered = false
	combo.reset()
	defense.clear_dash_recovery()
	defense.clear_dodge_ghost()
	actions_locked.emit()


func unlock_actions() -> void:
	if not is_action_locked:
		return
	is_action_locked = false
	facing_point = Vector2.INF
	actions_unlocked.emit()


# The fight points the player at whatever is rushing them, and the facing holds there until the fight
# moves it or the lock ends. It turns at once: a reaction test can't wait on the usual hysteresis.
func face_point(point: Vector2) -> void:
	facing_point = point
	var aim := point - global_position
	if aim == Vector2.ZERO:
		return
	facing = _facing_toward(aim)
	_apply_facing()


func clear_face_point() -> void:
	facing_point = Vector2.INF


# A fight puts the player somewhere, like Carter yanking them to the middle of the ring. The move
# itself is instant, so nothing the fight times depends on it; PlayerCombatFx draws the blink.
func warp_to(point: Vector2) -> void:
	var from := global_position
	global_position = point
	velocity = Vector2.ZERO
	warped.emit(from, point)


# A boss puts a temporary status effect on the player (PlayerStatus). A duration of 0 takes the
# kind's default; applying one that is already running refreshes it.
func apply_status(kind: StringName, duration := 0.0) -> void:
	status.apply(kind, duration)


func has_status(kind: StringName) -> bool:
	return status.has(kind)


func clear_statuses() -> void:
	status.clear_all()


# Eric's bear hug draws the held player in his own frames.
func grab() -> void:
	defense.clear_guard_break()
	defense.clear_dodge_ghost()
	defense.clear_dash_recovery()
	is_grabbed = true
	is_dodging = false
	dodge_timer = 0.0
	punch_buffered = false
	velocity = Vector2.ZERO
	sprite.visible = false
	state_machine.on_child_transition(state_machine.current_state, "Idle")


# A held player can't dodge, so every squeeze lands, even inside the last one's invincibility.
func take_grab_damage() -> void:
	receive_hit(HitInfo.make(&"eric_bear_hug_squeeze", self, global_position))


func release_grab(push_direction: Vector2) -> void:
	is_grabbed = false
	sprite.visible = true
	# Slows to a stop through the normal movement deceleration: about 140 px on the diagonal toss.
	velocity = push_direction.normalized() * GRAB_KNOCKBACK_SPEED
	is_invincible = true
	invincibility_timer.start()
	_flicker_while_invincible(invincibility_timer.wait_time)


# Called by PlayerFinisher as its beat starts; the charged punch is left to finish its swing.
func begin_finisher() -> void:
	is_finishing = true
	is_dodging = false
	dodge_timer = 0.0
	punch_buffered = false
	defense.clear_dash_recovery()
	status.clear_all()
	unlock_actions()
	velocity = Vector2.ZERO


func enter_finisher_pose() -> void:
	state_machine.on_child_transition(state_machine.current_state, "Finishing")


func end_finisher(grant_grace: bool) -> void:
	if state_machine.current_state == state_machine.states.get("Finishing"):
		state_machine.on_child_transition(state_machine.current_state, "Idle")
	is_finishing = false
	_apply_facing()
	if grant_grace and not fight_over:
		is_invincible = true
		invincibility_timer.start()
		_flicker_while_invincible(invincibility_timer.wait_time)


# Called by FightOutro once the fight is decided.
func end_fight() -> void:
	fight_over = true
	punch_buffered = false
	is_dodging = false
	dodge_timer = 0.0
	defense.on_fight_over()
	hype.on_fight_over()
	status.clear_all()
	unlock_actions()
	# A finisher under way plays out to its landing first.
	if is_finishing:
		finisher.finished.connect(_stand_still, CONNECT_ONE_SHOT)
		return
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
	# The finisher faces the player toward the boss itself.
	if is_finishing or defense.is_guard_broken:
		return
	# Held from the press until the boss has reported the swing: a hurtbox reports a punch after
	# the hitbox switches off, and moving the hitbox before then would lose the hit.
	if state_machine.current_state.name == "Punching" or combo.report_pending():
		return
	var aim := _aim()
	if aim == Vector2.ZERO:
		return
	var new_facing := _facing_toward(aim)
	if new_facing != facing and not _threat_turn_held():
		facing = new_facing
		_apply_facing()
		if facing_target and facing_target.is_in_group(THREAT_GROUP):
			threat_turn_frame = Engine.get_physics_frames()


func _threat_turn_held() -> bool:
	if threat_turn_frame < 0:
		return false
	return Engine.get_physics_frames() - threat_turn_frame < roundi(THREAT_FACING_HOLD * Engine.physics_ticks_per_second)


# Toward the nearest point of the nearest target's hurtbox, so the player faces the side of the
# boss they're on (its centre once they're inside it). With no target, as during boss 2's morph,
# the facing follows movement.
func _aim() -> Vector2:
	if facing_point != Vector2.INF:
		return facing_point - global_position
	var target := _nearest_target()
	if target == null:
		return velocity
	var box := _hurtbox_rect(target)
	# A threat the punch already reaches keeps the facing, so one jostling around the player can't spin them.
	if target.is_in_group(THREAT_GROUP) and box.intersects(global_transform * PUNCH_HITBOXES[facing]):
		return Vector2.ZERO
	if box.has_point(global_position):
		return box.get_center() - global_position
	return global_position.clamp(box.position, box.end) - global_position


# A near tie goes to the boss, so a player standing by it can still punch it with figures around.
func _nearest_target() -> Area2D:
	var nearest := _nearest_in_group(BOSS_TARGET_GROUP, INF)
	var threat := _nearest_in_group(THREAT_GROUP, THREAT_FACING_RADIUS)
	if threat and (nearest == null or _target_distance(threat) < _target_distance(nearest) - TARGET_SWITCH_MARGIN):
		nearest = threat
	facing_target = nearest
	return nearest


# The target whose hurtbox's nearest point is closest, if that's nearer than `radius`.
func _nearest_in_group(group: String, radius: float) -> Area2D:
	var nearest: Area2D = null
	var nearest_distance := radius
	for target in get_tree().get_nodes_in_group(group):
		var distance := _target_distance(target)
		if distance < nearest_distance:
			nearest = target
			nearest_distance = distance
	return nearest


# To the nearest point of the target's hurtbox, less TARGET_SWITCH_MARGIN for the target already faced.
func _target_distance(target: Area2D) -> float:
	var box := _hurtbox_rect(target)
	var distance := global_position.distance_to(global_position.clamp(box.position, box.end))
	if target == facing_target:
		distance -= TARGET_SWITCH_MARGIN
	return distance


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
