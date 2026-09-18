extends State

# Eric after his own sword is parried back into him, or the player parries his bear-hug grab: the
# attack stops and he's open to punches, up to BossOneScript.PARRY_STAGGER_HIT_CAP of them, then he
# glides back to where that attack started and carries on with his chain. It never opens a finisher
# daze: can_be_dazed() is Downed-only.

@export var animation_player : AnimationPlayer
@export var character_body : CharacterBody2D
@export var hurtbox : Area2D
@export var boss_collision_shape : CollisionShape2D
@export var eric_state_machine : Node
@export var stagger_timer : Timer

const FLASH := Color(1.6, 1.9, 2.6)
const FLASH_TIME := 0.3

# Both set by the state machine before it switches here.
var duration := 1.2
var home := Vector2.ZERO
var window_open := false
var gliding := false
var glide_speed := 0.0


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
	boss_collision_shape.disabled = false


func Physics_Update(delta: float) -> void:
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
