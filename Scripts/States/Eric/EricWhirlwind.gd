extends State

const HitInfo := preload("res://Scripts/HitInfo.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")
const EricArtLayout := preload("res://Scripts/EricArtLayout.gd")

# Over his head on the spin frames, right of the sword he hoists on his left.
const TELL_HEAD_PIXEL := Vector2(152, 116)

@export var animation_player : AnimationPlayer

#MainPlayer
@onready var player = get_tree().current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
var move_speed : float = 300.0

#Eric
@export var character_body : CharacterBody2D
@export var hurtbox : Area2D
@export var boss_collision_shape : CollisionShape2D
@export var whirlwind_hitbox : Area2D
@export var whirlwind_duration_timer : Timer
var whirlwind_direction : Vector2
@export var eric_state_machine : Node

# Chase speed in px/s and animation speed, at full health and at none.
@export var chase_speed := 420.0
@export var rage_chase_speed := 540.0
@export var animation_speed := 1.5
@export var rage_animation_speed := 2.1
@export var duration := 3.0

var eric_original_position : Vector2
var back_to_original_position = false

func Enter() -> void:
	eric_original_position = character_body.global_position
	back_to_original_position = false

	var rage: float = eric_state_machine.rage
	move_speed = lerpf(chase_speed, rage_chase_speed, rage)
	animation_player.speed_scale = lerpf(animation_speed, rage_animation_speed, rage)

	animation_player.play("whirlwind")
	# The spin has no separate wind-up: the warning stays up while he bears down on the player.
	ParryTell.telegraph(character_body, &"eric_whirlwind", duration, _tell_anchor)
	boss_collision_shape.disabled = true
	whirlwind_hitbox.monitoring = true
	whirlwind_duration_timer.start(duration)

	var sfx = character_body.get_node_or_null("WhirlwindSfxPlayer")
	if sfx:
		if not sfx.stream:
			sfx.stream = load("res://Assets/Audio/SFX/whirlwind_whoosh.ogg")
		sfx.play()

func Exit() -> void:
	ParryTell.clear(character_body)
	boss_collision_shape.disabled = false
	whirlwind_hitbox.monitoring = false
	whirlwind_duration_timer.stop()
	back_to_original_position = false
	animation_player.speed_scale = 1.0


# Called every frame. 'delta' is the elapsed time since the previous frame.
func Physics_Update(_delta: float):
	# A parry staggers him at the end of this step, where he is now.
	if _damage_player() == HitInfo.Result.PARRIED:
		return

	if back_to_original_position:
		whirlwind_direction = (
			eric_original_position -
			character_body.global_position
		).normalized()

		character_body.velocity = whirlwind_direction * move_speed
		character_body.move_and_slide()

		if character_body.global_position.distance_to(eric_original_position) < 10.0:
			character_body.global_position = eric_original_position
			eric_state_machine.attack_finished()

	else:
		# Move towards the player
		whirlwind_direction = (
			player.global_position -
			character_body.global_position
		).normalized()

		character_body.velocity = whirlwind_direction * move_speed
		character_body.move_and_slide()


# The whirlwind hurts whoever it overlaps while it spins, and only then: a flag set on the
# player when they entered it could outlive the whirlwind if it switched off around them.
func _damage_player() -> int:
	var near_miss := false
	for area in whirlwind_hitbox.get_overlapping_areas():
		if area == player.hurtBox:
			return player.receive_hit(_hit())
		if player.is_dodge_ghost(area):
			near_miss = true
	# Only where the player isn't: the spin passing the spot a dash left is a perfect dodge.
	if near_miss:
		player.receive_near_miss(_hit())
	return HitInfo.Result.IGNORED


# His daze anchor is tuned for his downed frames, too low for a standing tell.
func _tell_anchor() -> Vector2:
	return character_body.to_global(EricArtLayout.frame_local(TELL_HEAD_PIXEL + Vector2(0.5, 0.5), character_body.sprite.flip_h))


func _hit() -> RefCounted:
	var centre: Vector2 = whirlwind_hitbox.get_node("CollisionShape2D").global_position
	return HitInfo.make(&"eric_whirlwind", whirlwind_hitbox, centre, character_body)


func _on_whirlwind_duration_timeout() -> void:
	back_to_original_position = true
