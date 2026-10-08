extends State

# Eric spins his greatsword around him.
# V1 (EricPacing): he chases the player for chase_time, then spins back to where he started.
# V2: a yellow wind-up, then straight lunges at the player, re-aiming between them while still
# spinning, then he lets the sword go at them and the throw takes over from there (EricSwordThrow).
# Each lunge is a dodge check: a dash goes through it, and a guard only absorbs it at a heavy cost.

const HitInfo := preload("res://Scripts/HitInfo.gd")
const AttackCatalog := preload("res://Scripts/AttackCatalog.gd")
const EricArtLayout := preload("res://Scripts/EricArtLayout.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")

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

const EricPacing := preload("res://Scripts/EricPacing.gd")

const WINDUP_ANIMATION := &"whirl_windup"
# Over his head on the wind-up frame, clear of the swoosh behind him.
const TELL_HEAD_PIXEL := Vector2(126, 108)
# Where his origin can lunge to: his body inside the ropes, and high enough for the sweep to still
# reach a player against the top rope.
const LUNGE_AREA := Rect2(240, 180, 1440, 590)
# Summed frame deltas land a hair short of a phase's length, which would run it a frame long.
const STEP_TOLERANCE := 0.0001
# How finely a re-aim looks ahead for when the next lunge would reach the player.
const ETA_STEP := 1.0 / 240.0

# HOLD: before the wind-up, until the player's bar can pay for the first lunge's dash (_dash_affordable).
enum Phase { WINDUP, LUNGE, REAIM, RELEASE, HOLD }

var eric_original_position : Vector2
var back_to_original_position = false
var rage := 0.0
var phase := Phase.WINDUP
var phase_left := 0.0
var lunges_left := 0
var lunge_velocity := Vector2.ZERO
var clock := 0.0
# When this lunge first met the player, or the spot their dash left; -1 while it hasn't.
var met_at := -1.0

func Enter() -> void:
	eric_original_position = character_body.global_position
	back_to_original_position = false

	rage = eric_state_machine.rage
	animation_player.speed_scale = EricPacing.raged("spin_animation_speed", rage)
	if EricPacing.is_v2():
		_wind_up_when_affordable()
		return
	move_speed = EricPacing.raged("chase_speed", rage)

	animation_player.play("whirlwind")
	boss_collision_shape.disabled = true
	whirlwind_hitbox.monitoring = true
	whirlwind_duration_timer.start(EricPacing.value("chase_time"))

	_play_whoosh()

func Exit() -> void:
	ParryTell.clear(character_body)
	phase = Phase.WINDUP
	boss_collision_shape.disabled = false
	whirlwind_hitbox.monitoring = false
	whirlwind_duration_timer.stop()
	back_to_original_position = false
	animation_player.speed_scale = 1.0


# Called every frame. 'delta' is the elapsed time since the previous frame.
func Physics_Update(_delta: float):
	if EricPacing.is_v2():
		_lunges(_delta)
		return
	_damage_player()

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


func _wind_up() -> void:
	lunges_left = roundi(EricPacing.raged("whirl_lunges", rage))
	phase = Phase.WINDUP
	phase_left = EricPacing.raged("whirl_windup", rage)
	animation_player.play(WINDUP_ANIMATION)
	ParryTell.telegraph(character_body, EricPacing.value("whirlwind_id"), phase_left, _tell_anchor)


func _lunges(delta: float) -> void:
	clock += delta
	if phase == Phase.LUNGE or phase == Phase.REAIM:
		_damage_player()
	phase_left -= delta
	var phase_over := phase_left <= STEP_TOLERANCE
	match phase:
		Phase.HOLD:
			if _dash_affordable():
				animation_player.speed_scale = EricPacing.raged("spin_animation_speed", rage)
				_wind_up()
		Phase.WINDUP:
			if phase_over:
				_start_spin()
				_start_lunge()
		Phase.LUNGE:
			character_body.global_position = (character_body.global_position + lunge_velocity * delta).clamp(LUNGE_AREA.position, LUNGE_AREA.end)
			if phase_over:
				lunges_left -= 1
				if lunges_left > 0:
					phase = Phase.REAIM
					phase_left = EricPacing.raged("whirl_reaim_time", rage)
				else:
					_start_release()
		Phase.REAIM:
			if phase_over and _next_lunge_dodgeable() and _dash_affordable():
				_start_lunge()


# The wind-up has done its job: the spinning sword is the threat from here. Like the chase, he passes
# through the player instead of being blocked by them.
func _start_spin() -> void:
	ParryTell.clear(character_body)
	animation_player.play("whirlwind")
	boss_collision_shape.disabled = true
	whirlwind_hitbox.monitoring = true


# Straight at where the player is now, the sweep's centre through theirs.
func _start_lunge() -> void:
	var sweep: Vector2 = whirlwind_hitbox.get_node("CollisionShape2D").global_position
	var aim: Vector2 = player.hurtBox.get_node("CollisionShape2D").global_position - sweep
	if aim != Vector2.ZERO:
		lunge_velocity = aim.normalized() * EricPacing.raged("whirl_lunge_speed", rage)
	phase = Phase.LUNGE
	phase_left = EricPacing.value("whirl_lunge_time")
	met_at = -1.0
	_play_whoosh()


# Every lunge asks for a dash, and a dash costs a third of the stamina bar: four in a row only fit a full bar
# with a perfect dodge's refund, and not at all for a player who came in having spent some. So neither the
# wind-up nor a re-aim lets the next lunge go until the player's bar can pay for its dash (fairness,
# 2026-10-06). The bar refills after a short pause (PlayerDefense.stamina_regen_delay), so a hold is short.
func _dash_affordable() -> bool:
	var defense: Node = player.get_node_or_null("Defense")
	return defense == null or defense.can_afford(defense.dash_stamina_cost)


# Winds up now if the player's bar can pay for the first lunge's dash; otherwise stands, harmless and with
# no tell, until it can.
func _wind_up_when_affordable() -> void:
	if _dash_affordable():
		_wind_up()
		return
	phase = Phase.HOLD
	animation_player.speed_scale = 1.0
	animation_player.play("idle")


# A dash is only immune AttackCatalog.DASH_IMMUNITY_COOLDOWN after the last one, so a lunge that
# starts on top of a player who has just dashed through the one before couldn't be dodged at all. The
# re-aim holds until the next lunge would reach them late enough.
func _next_lunge_dodgeable() -> bool:
	if met_at < 0.0:
		return true
	var ready_at: float = met_at + AttackCatalog.DASH_IMMUNITY_COOLDOWN + EricPacing.value("whirl_dodge_lead")
	return clock + _lunge_eta() >= ready_at


# Seconds a lunge starting now would take to reach the player where they stand, or INF if it wouldn't.
func _lunge_eta() -> float:
	var sweep: CollisionShape2D = whirlwind_hitbox.get_node("CollisionShape2D")
	var radii: Vector2 = Vector2.ONE * sweep.shape.radius * sweep.global_scale.abs()
	var body: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	var rect: Rect2 = body.global_transform * body.shape.get_rect()
	var aim: Vector2 = rect.get_center() - sweep.global_position
	if aim == Vector2.ZERO:
		return 0.0
	var velocity := aim.normalized() * EricPacing.raged("whirl_lunge_speed", rage)
	var t := 0.0
	while t <= EricPacing.value("whirl_lunge_time"):
		var at: Vector2 = sweep.global_position + velocity * t
		var near := at.clamp(rect.position, rect.end) - at
		if (near / radii).length_squared() <= 1.0:
			return t
		t += ETA_STEP
	return INF


# The last beat: the spin stops and he throws the sword at the player, which is the sword toss's own
# release from there (EricSwordThrow) - the same red tell, parry, chip and uppercut. It hands over on
# the first frame of that tell, so the badge doesn't blink out and come back at the throw's anchor.
func _start_release() -> void:
	whirlwind_hitbox.monitoring = false
	var sfx: AudioStreamPlayer = character_body.get_node_or_null("WhirlwindSfxPlayer")
	if sfx:
		sfx.stop()
	phase = Phase.RELEASE
	eric_state_machine.throw_from_whirlwind()


func _play_whoosh() -> void:
	var sfx = character_body.get_node_or_null("WhirlwindSfxPlayer")
	if sfx:
		if not sfx.stream:
			sfx.stream = load("res://Assets/Audio/SFX/whirlwind_whoosh.ogg")
		sfx.play()


# His daze anchor is tuned for his downed frames, too low for a standing tell.
func _tell_anchor() -> Vector2:
	return character_body.to_global(EricArtLayout.frame_local(TELL_HEAD_PIXEL + Vector2(0.5, 0.5), character_body.sprite.flip_h))


# The whirlwind hurts whoever it overlaps while it spins, and only then: a flag set on the
# player when they entered it could outlive the whirlwind if it switched off around them.
func _damage_player() -> void:
	var near_miss := false
	for area in whirlwind_hitbox.get_overlapping_areas():
		if area == player.hurtBox:
			_note_meeting()
			player.receive_hit(_hit())
			return
		if player.is_dodge_ghost(area):
			near_miss = true
			_note_meeting()
	# Only where the player isn't: the spin passing the spot a dash left is a perfect dodge.
	if near_miss:
		player.receive_near_miss(_hit())


func _note_meeting() -> void:
	if phase == Phase.LUNGE and met_at < 0.0:
		met_at = clock


func _hit() -> RefCounted:
	var centre: Vector2 = whirlwind_hitbox.get_node("CollisionShape2D").global_position
	return HitInfo.make(EricPacing.value("whirlwind_id"), whirlwind_hitbox, centre, character_body)


func _on_whirlwind_duration_timeout() -> void:
	back_to_original_position = true
