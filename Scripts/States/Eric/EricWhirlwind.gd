extends State

@export var animation_player : AnimationPlayer

#MainPlayer
@onready var player = get_tree().current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
var move_speed : float = 300.0

#Eric
@export var character_body : CharacterBody2D
@export var hurtbox : Area2D
@export var boss_collision_shape : CollisionShape2D
var whirlwind_direction : Vector2
@export var eric_state_machine : Node

var eric_original_position : Vector2
var back_to_original_position = false

func Enter() -> void:
	eric_original_position = character_body.global_position

	# Whirlwind gets faster and chases harder as Eric's health drops.
	var ratio := 1.0
	if character_body.has_method("get_health_ratio"):
		ratio = character_body.get_health_ratio()
	move_speed = lerp(300.0, 430.0, 1.0 - ratio)
	animation_player.speed_scale = lerp(1.5, 2.1, 1.0 - ratio)

	animation_player.play("whirlwind")
	boss_collision_shape.disabled = true

	var sfx = character_body.get_node_or_null("WhirlwindSfxPlayer")
	if sfx:
		if not sfx.stream:
			sfx.stream = load("res://Assets/Audio/SFX/whirlwind_whoosh.ogg")
		sfx.play()

func Exit() -> void:
	boss_collision_shape.disabled = false


# Called every frame. 'delta' is the elapsed time since the previous frame.
func Physics_Update(_delta: float):
	if back_to_original_position:
		whirlwind_direction = (
			eric_original_position -
			character_body.global_position
		).normalized()

		character_body.velocity = whirlwind_direction * move_speed
		character_body.move_and_slide()

		if character_body.global_position.distance_to(eric_original_position) < 10.0:
			back_to_original_position = false
			eric_state_machine.whirlwind_finished()

	else:
		# Move towards the player
		whirlwind_direction = (
			player.global_position -
			character_body.global_position
		).normalized()

		character_body.velocity = whirlwind_direction * move_speed
		character_body.move_and_slide()


func _on_whirlwind_duration_timeout() -> void:
	back_to_original_position = true
