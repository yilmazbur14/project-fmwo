extends CharacterBody2D

# Carter only ever charges VERTICALLY - the mirror of Josh. He locks
# onto the player's X position the instant a charge begins, snaps to
# that horizontal spot, then sweeps the whole height of the arena.

enum State { IDLE, TELEGRAPH, CHARGING, RECOVERING }

@export var sprite: Sprite2D
@export var animation_player: AnimationPlayer
@export var telegraph_line: Line2D
@export var body_hitbox: Area2D

const TELEGRAPH_DURATION := 0.6
const DEFAULT_ARRIVAL_TIME := 0.45
const MAX_TRAVEL := 2600.0
const RECOVER_DURATION := 1.0

var state := State.IDLE
var origin_position: Vector2
var charge_speed := 0.0
var charge_direction := 1.0
var traveled := 0.0
var main_player = null


func _ready() -> void:
	origin_position = global_position
	main_player = get_tree().current_scene.get_node_or_null("Arena/MainPlayer/CharacterBody2D")
	if telegraph_line:
		telegraph_line.visible = false
	if body_hitbox:
		body_hitbox.area_entered.connect(_on_body_hitbox_area_entered)
	_play_idle()


func _physics_process(delta: float) -> void:
	if state == State.CHARGING:
		var move = charge_direction * charge_speed * delta
		global_position.y += move
		traveled += abs(move)
		if traveled >= MAX_TRAVEL:
			_finish_charge()


# Called by the coordinator with a snapshot of the player's position.
func begin_charge(target: Vector2, arrival_time: float = DEFAULT_ARRIVAL_TIME) -> void:
	if state != State.IDLE:
		return
	state = State.TELEGRAPH
	global_position.x = target.x
	if telegraph_line:
		telegraph_line.visible = true
	_play_telegraph()
	await get_tree().create_timer(TELEGRAPH_DURATION).timeout
	if state != State.TELEGRAPH:
		return
	_start_charging(target, arrival_time)


func _start_charging(target: Vector2, arrival_time: float) -> void:
	if telegraph_line:
		telegraph_line.visible = false
	state = State.CHARGING
	traveled = 0.0
	if body_hitbox:
		body_hitbox.add_to_group("enemy projectile")

	var dist = abs(target.y - global_position.y)
	dist = max(dist, 40.0)
	charge_speed = dist / max(arrival_time, 0.05)
	charge_direction = sign(target.y - global_position.y)
	if charge_direction == 0:
		charge_direction = 1.0
	_play_charging()


# Called by the coordinator when Carter and Josh actually collide, so
# the charge stops immediately instead of sweeping off to the wall.
func interrupt_charge() -> void:
	if state == State.CHARGING:
		_finish_charge()


func _finish_charge() -> void:
	state = State.RECOVERING
	if body_hitbox:
		body_hitbox.remove_from_group("enemy projectile")
	_play_recovering()
	await get_tree().create_timer(RECOVER_DURATION).timeout
	global_position = origin_position
	state = State.IDLE
	_play_idle()


func hit_feedback() -> void:
	if not sprite:
		return
	sprite.modulate = Color(3, 3, 3)
	var flash_tween = create_tween()
	flash_tween.tween_property(sprite, "modulate", Color(1, 1, 1), 0.15)


func _on_body_hitbox_area_entered(area: Area2D) -> void:
	# Attempting to punch either wrestler - even mid-recovery, out of
	# breath - always gets the player hit back. Never a safe window.
	if area.is_in_group("player attack"):
		if main_player and main_player.has_method("take_damage"):
			main_player.take_damage()
		return

	# Only counts while actually charging - this is how Carter and Josh
	# damage each other (and the boss) when their charges collide.
	if state == State.CHARGING and area.is_in_group("josh_body"):
		var coordinator = get_parent()
		if coordinator and coordinator.has_method("on_wrestler_collision"):
			coordinator.on_wrestler_collision()


func _play_idle() -> void:
	if animation_player:
		animation_player.play("idle")


func _play_telegraph() -> void:
	if sprite:
		sprite.modulate = Color(1.35, 1.5, 1.9)


func _play_charging() -> void:
	if sprite:
		sprite.modulate = Color(1, 1, 1)
	if animation_player:
		animation_player.stop()
	if sprite:
		sprite.frame = min(2, sprite.hframes * sprite.vframes - 1)


func _play_recovering() -> void:
	if animation_player:
		animation_player.stop()
	if sprite:
		sprite.modulate = Color(1, 1, 1)
		sprite.frame = min(3, sprite.hframes * sprite.vframes - 1)
