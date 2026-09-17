extends Node2D

@export var animation_player: AnimationPlayer
@export var detonate_timer: Timer
@export var explode_sfx: AudioStreamPlayer
@export var explosion_hitbox_shape: CollisionShape2D
@export var bomb_sprite: Sprite2D


func _ready() -> void:
	detonate_timer.timeout.connect(_detonate)
	animation_player.animation_finished.connect(_on_animation_player_animation_finished)
	animation_player.play("armed")


func arm(detonate_delay: float) -> void:
	# Mason's next line can walk back across this one while it counts down, and depth
	# sorting would hide a lit bomb behind him, so lit bombs draw above the characters.
	bomb_sprite.z_index = 1
	# Timer.start(0) silently falls back to the timer's old wait_time instead of
	# firing immediately, so a zero delay has to bypass the timer entirely.
	if detonate_delay <= 0.0:
		_detonate.call_deferred()
		return
	detonate_timer.start(detonate_delay)


func _detonate() -> void:
	explode_sfx.play()
	animation_player.play("explode")


# Called by the "explode" animation's method track.
func _enable_hitbox() -> void:
	explosion_hitbox_shape.set_deferred("disabled", false)


# Called by the "explode" animation's method track.
func _disable_hitbox() -> void:
	explosion_hitbox_shape.set_deferred("disabled", true)


func _on_animation_player_animation_finished(anim_name: StringName) -> void:
	if anim_name == &"explode":
		queue_free()
