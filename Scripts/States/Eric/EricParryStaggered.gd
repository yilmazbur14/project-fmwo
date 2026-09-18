extends State

# Eric after his own sword is parried back into him, or the player parries his bear-hug grab: the
# attack stops and he's open to punches, up to BossOneScript.PARRY_STAGGER_HIT_CAP of them, then he
# glides back to where that attack started and carries on with his chain.
# `from_reflect` marks the sword's version, which is the one that opens a finisher daze: the throw
# hands straight to PlayerFinisher.begin_auto() and the uppercut fires without a mash. A parried
# bear hug leaves it false and stays a plain punish window.

@export var animation_player : AnimationPlayer
@export var character_body : CharacterBody2D
@export var hurtbox : Area2D
@export var boss_collision_shape : CollisionShape2D
@export var eric_state_machine : Node
@export var stagger_timer : Timer

const FLASH := Color(1.6, 1.9, 2.6)
const FLASH_TIME := 0.3
# The sword is parried from wherever the player was standing, usually across the arena, so the
# uppercut the reflect fires would swing at nothing. They are driven onto him over the finisher's
# settle beat, before it freezes the fight, the way Carter's Raging Demon drives them to the centre.
# Shorter than PlayerFinisher.daze_settle_time, so it is over before the freeze.
const DRIVE_TIME := 0.18

# Both set by the state machine before it switches here.
var duration := 1.2
var home := Vector2.ZERO
# Set by the throw before it switches here, and cleared on the way out so the next stagger has to
# claim it again.
var from_reflect := false
var window_open := false
var gliding := false
var glide_speed := 0.0
var drive_left := 0.0
var drive_from := Vector2.ZERO
var drive_to := Vector2.ZERO
var driven: Node2D


func Enter() -> void:
	glide_speed = eric_state_machine.states["Whirlwind"].chase_speed
	animation_player.play("downed")
	# He can be standing on the player.
	boss_collision_shape.disabled = true
	var sfx: AudioStreamPlayer = character_body.get_node_or_null("WhirlwindSfxPlayer")
	if sfx:
		sfx.stop()
	character_body.parry_stagger_hits = 0
	hurtbox.set_deferred("monitoring", true)
	hurtbox.set_deferred("monitorable", true)
	window_open = true
	gliding = false
	# self_modulate stacks on his own hit flash, which tweens modulate.
	var sprite: Sprite2D = character_body.sprite
	sprite.self_modulate = FLASH
	sprite.create_tween().tween_property(sprite, "self_modulate", Color.WHITE, FLASH_TIME)
	stagger_timer.start(duration)


func Exit() -> void:
	stagger_timer.stop()
	# Only while the window is still open: the next state may open the hurtbox itself.
	if window_open:
		_close_window()
	gliding = false
	from_reflect = false
	drive_left = 0.0
	driven = null
	boss_collision_shape.disabled = false


# Called by the throw once the finisher has actually taken the daze, so a refused one never yanks
# the player. Onto the side of him they parried from, at his feet, inside the uppercut's reach.
func drive_player_in(player: Node2D) -> void:
	var shape: CollisionShape2D = hurtbox.get_node("CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	var side := signf(player.global_position.x - box.get_center().x)
	if side == 0.0:
		side = 1.0
	driven = player
	drive_from = player.global_position
	drive_to = Vector2(box.get_center().x + side * box.size.x * 0.5, box.end.y)
	drive_left = DRIVE_TIME


func Physics_Update(delta: float) -> void:
	if drive_left > 0.0 and is_instance_valid(driven):
		drive_left -= delta
		var t := clampf(1.0 - drive_left / DRIVE_TIME, 0.0, 1.0)
		driven.global_position = drive_from.lerp(drive_to, t * t).round()
	if not gliding:
		return
	character_body.global_position = character_body.global_position.move_toward(home, glide_speed * delta)
	if character_body.global_position == home:
		gliding = false
		boss_collision_shape.disabled = false
		eric_state_machine.attack_finished()


func _on_parry_stagger_timer_timeout() -> void:
	if eric_state_machine.current_state != self:
		return
	_close_window()
	animation_player.play("idle")
	gliding = true


func _close_window() -> void:
	window_open = false
	hurtbox.set_deferred("monitoring", false)
	hurtbox.set_deferred("monitorable", false)
