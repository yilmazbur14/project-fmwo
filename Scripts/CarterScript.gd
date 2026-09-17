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
const TELEGRAPH_TINT := Color(1.35, 1.5, 1.9)

var state := State.IDLE
var origin_position: Vector2
var charge_speed := 0.0
var charge_direction := 1.0
var traveled := 0.0
var main_player = null
var is_defeated := false


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
	if state != State.IDLE or is_defeated:
		return
	state = State.TELEGRAPH
	global_position.x = target.x
	if telegraph_line:
		telegraph_line.visible = true
	_play_telegraph()
	await get_tree().create_timer(TELEGRAPH_DURATION).timeout
	# play_defeated() flips is_defeated without touching state, so a wrestler
	# killed during his own telegraph would otherwise resume the charge here.
	if state != State.TELEGRAPH or is_defeated:
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
	# A wrestler who stood down mid-recovery stays where he is.
	if is_defeated or state != State.RECOVERING:
		return
	global_position = origin_position
	state = State.IDLE
	_play_idle()


func hit_feedback() -> void:
	if not sprite:
		return
	sprite.modulate = Color(3, 3, 3)
	# Getting hit mid-wind-up must not wipe the telegraph tell, so the flash
	# fades back to whatever tint the current state is supposed to be showing.
	var flash_target := TELEGRAPH_TINT if state == State.TELEGRAPH else Color(1, 1, 1)
	var flash_tween = create_tween()
	flash_tween.tween_property(sprite, "modulate", flash_target, 0.15)
	if animation_player and not is_defeated:
		animation_player.play("hit")
		# "hit" is one non-looping frame. Without something queued behind it
		# the player stops and the sprite freezes on it for the rest of the
		# recovery, so the recover pose would never be seen.
		var resume := "idle"
		if state == State.RECOVERING:
			resume = "recover"
		elif state == State.TELEGRAPH:
			resume = "telegraph"
		animation_player.queue(resume)


func play_defeated() -> void:
	is_defeated = true
	if sprite:
		sprite.modulate = Color(1, 1, 1)
	if animation_player:
		animation_player.play("defeated")


# Called by the coordinator when the player loses: whatever he's doing, he stops where he is and
# stands idle. The coordinator's cycle is stopped too, so nothing starts another charge.
func stand_down() -> void:
	state = State.IDLE
	if body_hitbox:
		body_hitbox.remove_from_group("enemy projectile")
	if telegraph_line:
		telegraph_line.visible = false
	_play_idle()


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
	if sprite:
		sprite.modulate = Color(1, 1, 1)
	if animation_player:
		animation_player.play("idle")


func _play_telegraph() -> void:
	if sprite:
		sprite.modulate = TELEGRAPH_TINT
	if animation_player:
		animation_player.play("telegraph")


func _play_charging() -> void:
	if sprite:
		sprite.modulate = Color(1, 1, 1)
	if animation_player:
		if charge_direction < 0:
			animation_player.play("charge_up")
		else:
			animation_player.play("charge_down")


func _play_recovering() -> void:
	if sprite:
		sprite.modulate = Color(1, 1, 1)
	if animation_player:
		animation_player.play("recover")
