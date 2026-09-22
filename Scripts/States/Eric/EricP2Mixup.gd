extends State

# Eric's phase-two mixup: one wind-up, two branches, and the colours have swapped sides. Phase one
# taught red = the grab and yellow = the charge; here red is a haymaker only a parry answers and
# yellow is the command grab only a dash answers. Same badge, same wind-up length (p2_windup is
# hug_charge_time to the frame), opposite attacks.
#
# THE NUMBER THIS STANDS ON is p2_strike_travel. Both branches leave the wind-up and reach the player
# after exactly that long, at any range: the rush is fixed-duration and homes every physics step, so
# running does not work, the answer window never shrinks with distance, and the moment of contact
# says nothing about which branch it is. Only the colour does.
# Red must never land AFTER yellow. If it did, a dash for the grab followed by a press for the
# haymaker would beat both branches with no read at all, because the press would land after the grab
# had already resolved and so could not give the dash's i-frames up (DashImmunity reads
# player.dash_cancelled at the moment of contact). Landing together is the only ordering where the
# press that parries red is necessarily at or before the grab's own contact.
# What a dash and a press each buy is the catalogue's business: eric_p2_haymaker is parryable and not
# dash_through, eric_p2_grab is dash_through and neither blockable nor parryable. Neither input does
# anything at all in the other branch.
#
# A landed grab holds them and crushes, and PlayerGrabEscape's mash is the way out. He always lets
# go: the hold ends on the meter filling or on the tick cap, never on nothing.

const HitInfo := preload("res://Scripts/HitInfo.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")
const EricArtLayout := preload("res://Scripts/EricArtLayout.gd")
const EricPacing := preload("res://Scripts/EricPacing.gd")
const EricPhaseTwoPose := preload("res://Scripts/EricPhaseTwoPose.gd")
const EricColourRule := preload("res://Scripts/EricColourRule.gd")

@export var animation_player : AnimationPlayer
@export var character_body : CharacterBody2D
@export var hurtbox : Area2D
@export var grab_area : Area2D
@export var boss_collision_shape : CollisionShape2D
@export var eric_state_machine : Node

# Where his origin may end its rush: his body inside the ropes, the whirlwind's own lunge area.
const RUSH_AREA := Rect2(240, 180, 1440, 590)
const TOSS_DIRECTION := Vector2(0.7071, -0.7071)

enum Phase { WINDUP, RUSH, CONTACT, HOLD, STUMBLE, RECOVER }

@onready var player = get_tree().current_scene.get_node("Arena/MainPlayer/CharacterBody2D")

var phase := Phase.WINDUP
# Where the attack started, which a parry stagger puts him back on.
var home := Vector2.ZERO
var phase_left := 0.0
var rage := 0.0
# This mixup is the yellow grab rather than the red haymaker; the colours of the last two.
var yellow := false
var mixups_started := 0
var recent_yellows: Array[bool] = []
var holding := false
var crushes_left := 0
var crush_left := 0.0
var sheet_texture: Texture2D
var sheet_frames := 0
var pose_frames: Array = []
var pose_clock := 0.0


func Enter() -> void:
	rage = eric_state_machine.rage
	home = character_body.global_position
	# The mixup drives its own frames; an animation still running would fight it for them.
	animation_player.stop()
	var sprite: Sprite2D = character_body.sprite
	sheet_texture = sprite.texture
	sheet_frames = sprite.hframes
	yellow = EricColourRule.next_is_yellow(mixups_started, recent_yellows, EricPacing.value("p2_yellow_chance"))
	mixups_started += 1
	hurtbox.monitoring = false
	hurtbox.monitorable = false
	grab_area.monitoring = false
	holding = false
	phase = Phase.WINDUP
	phase_left = EricPacing.p2("p2_windup", rage)
	_show("windup")
	sprite.flip_h = player.global_position.x < character_body.global_position.x
	ParryTell.telegraph(character_body, hit_id(), phase_left, _tell_anchor)


func Exit() -> void:
	ParryTell.clear(character_body)
	if holding:
		_release_player()
	grab_area.monitoring = false
	hurtbox.monitoring = false
	hurtbox.monitorable = false
	boss_collision_shape.disabled = false
	var sprite: Sprite2D = character_body.sprite
	sprite.hframes = sheet_frames
	sprite.texture = sheet_texture


# What this mixup's strike is. Its badge follows from the id: red and strong for the haymaker, which
# a parry staggers, yellow for the grab, which only a dash answers.
func hit_id() -> StringName:
	return &"eric_p2_grab" if yellow else &"eric_p2_haymaker"


func Physics_Update(delta: float) -> void:
	_step_pose(delta)
	match phase:
		Phase.WINDUP:
			phase_left -= delta
			if phase_left <= 0.0:
				_start_rush()
		Phase.RUSH:
			phase_left -= delta
			# The homing step: whatever time is left has to cover whatever ground is left, so the
			# arrival lands on p2_strike_travel however far they ran.
			var target := _rush_target()
			var step: float = character_body.global_position.distance_to(target) / maxf(phase_left, delta)
			character_body.global_position = character_body.global_position.move_toward(target, step * delta).clamp(RUSH_AREA.position, RUSH_AREA.end)
			character_body.sprite.flip_h = target.x < character_body.global_position.x
			if phase_left <= 0.0:
				_arrive()
		Phase.CONTACT:
			phase_left -= delta
			if _resolve_contact():
				return
			if phase_left <= 0.0:
				_whiff()
		Phase.HOLD:
			crush_left -= delta
			if crush_left <= 0.0:
				_crush()
			elif player.grab_escape.escaped:
				_end_hold()
		Phase.STUMBLE, Phase.RECOVER:
			phase_left -= delta
			if phase_left <= 0.0:
				eric_state_machine.attack_finished()
	if holding:
		player.global_position = _player_point(EricArtLayout.P2_HOLD_CENTRE)
		player.velocity = Vector2.ZERO


# The rush is the hitbox, and it is harmless until it arrives: the badge promised a moment, and arms
# that clipped the player on the way in would be a tell that lies. The same rule the thrown sword
# keeps with hot_from.
func _start_rush() -> void:
	ParryTell.clear(character_body)
	boss_collision_shape.disabled = true
	phase = Phase.RUSH
	phase_left = EricPacing.value("p2_strike_travel")
	_show("strike")


func _rush_target() -> Vector2:
	var offset: Vector2 = grab_area.get_node("CollisionShape2D").global_position - character_body.global_position
	return player.global_position - offset


func _arrive() -> void:
	phase = Phase.CONTACT
	phase_left = EricPacing.value("p2_strike_hot")
	grab_area.monitoring = true


# Returns whether the contact ended the phase. The haymaker resolves once, whatever the answer was;
# the grab keeps its arms open for p2_strike_hot, and a dash ghost inside them is a perfect dodge
# rather than a whiff nobody is paid for.
func _resolve_contact() -> bool:
	var near_miss := false
	for area in grab_area.get_overlapping_areas():
		if area == player.hurtBox:
			var result: int = player.receive_hit(_hit())
			if not yellow:
				grab_area.monitoring = false
				_recover()
				return true
			if result == HitInfo.Result.HIT:
				_grab()
				return true
			return false
		if player.is_dodge_ghost(area):
			near_miss = true
	# Only where the player isn't: the rush closing on the spot a dash left is a perfect dodge.
	if near_miss:
		player.receive_near_miss(_hit())
	return false


func _hit() -> RefCounted:
	var centre: Vector2 = grab_area.get_node("CollisionShape2D").global_position
	return HitInfo.make(hit_id(), self, centre, character_body)


# A grab that closed on nobody, or a haymaker that swung through the air: he is off balance and open
# to punches.
func _whiff() -> void:
	grab_area.monitoring = false
	hurtbox.monitoring = true
	hurtbox.monitorable = true
	boss_collision_shape.disabled = false
	phase = Phase.STUMBLE
	phase_left = EricPacing.value("p2_stumble_time")
	_show("stumble")


# A haymaker that connected follows through instead, on its own shorter beat, and is not open.
func _recover() -> void:
	boss_collision_shape.disabled = false
	phase = Phase.RECOVER
	phase_left = EricPacing.value("p2_recover_time")
	_show("stumble")


func _grab() -> void:
	holding = true
	grab_area.monitoring = false
	boss_collision_shape.disabled = false
	player.grab()
	player.grab_escape.begin()
	phase = Phase.HOLD
	crushes_left = EricPacing.value("p2_crush_ticks")
	crush_left = 0.0
	_show("hold")


# One tick of the crush, the first of them the moment he closes his arms: being caught always costs
# something, and mashing out on the first tick is what costs least.
func _crush() -> void:
	crushes_left -= 1
	player.take_grab_damage(&"eric_p2_crush")
	_show("crush")
	if crushes_left <= 0 or player.playerHealth <= 0:
		_end_hold()
		return
	crush_left = EricPacing.p2("p2_crush_interval", rage)


func _end_hold() -> void:
	_release_player()
	phase = Phase.RECOVER
	phase_left = EricPacing.value("p2_recover_time")
	_show("toss")


func _release_player() -> void:
	holding = false
	player.grab_escape.cancel()
	player.global_position = _player_point(EricArtLayout.P2_TOSS_CENTRE)
	player.release_grab(TOSS_DIRECTION)


func _player_point(centre: Vector2) -> Vector2:
	var offset := EricArtLayout.feet_offset(centre)
	return (character_body.global_position + offset).clamp(EricArtLayout.PLAYER_AREA.position, EricArtLayout.PLAYER_AREA.end)


# His daze anchor is tuned for his downed frames, too low for a standing tell.
func _tell_anchor() -> Vector2:
	return character_body.to_global(EricArtLayout.frame_local(EricArtLayout.P2_TELL_HEAD_PIXEL + Vector2(0.5, 0.5), character_body.sprite.flip_h))


func _show(key: String) -> void:
	pose_frames = EricPhaseTwoPose.show(character_body.sprite, key)
	pose_clock = 0.0


func _step_pose(delta: float) -> void:
	pose_clock += delta
	character_body.sprite.frame = EricPhaseTwoPose.frame_at(pose_frames, pose_clock)
