extends State

# Eric throws his sword at where the player stands. It sticks in the ground and sends out an
# earthquake ring, then flies back to his hand.
# The wind-up warns first: a parry while the sword is in the air flings it back at him, and it takes
# a chip of health off and staggers him where he threw it when it arrives. A held guard absorbs it
# as before, and an unparried sword plants and rings as before.

@export var animation_player : AnimationPlayer
@export var character_body : CharacterBody2D
@export var eric_state_machine : Node

# Sword speed in px/s both ways, ring growth in px/s and how long the sword stays planted before
# he recalls it, at full health and at none.
@export var flight_speed := 1400.0
@export var rage_flight_speed := 1700.0
@export var ring_speed := 950.0
@export var rage_ring_speed := 1200.0
@export var planted_time := 0.7
@export var rage_planted_time := 0.45
# How fast a parried sword comes back, in px/s: faster than he threw it, since the player sent it.
@export var reflect_speed := 1600.0
# Added to the parry's own stagger window. He is struck at throwing range, not standing over the
# player the way a parried whirlwind left him, so there is further to run before the punish.
@export var reflect_stagger_bonus := 0.5

const SWORD_SCENE := preload("res://Scenes/Bosses/EricThrownSwordScene.tscn")
const IMPACT_SCENE := preload("res://Scenes/Bosses/EricQuakeImpactScene.tscn")
const RING_SCENE := preload("res://Scenes/Bosses/EricQuakeRingScene.tscn")
const EricArtLayout := preload("res://Scripts/EricArtLayout.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")

# Over his head on the wind-up frames, left of the greatsword he swings up over his shoulder.
const TELL_HEAD_PIXEL := Vector2(116, 104)
# throw_windup's length plus the release frames before the sword leaves his hands: the warning is up
# for the whole wind-up, and the sword itself is the cue from then on.
const TELL_TIME := 0.63
# What the flung-back sword takes off him, on top of the punches the stagger then opens up.
const REFLECT_DAMAGE := 1

@onready var player = get_tree().current_scene.get_node("Arena/MainPlayer/CharacterBody2D")

var sword: Node2D
var planted_left := -1.0
# Where he stood to throw, which the stagger puts him back on.
var throw_spot: Vector2
var pending_stagger := 0.0


func Enter() -> void:
	planted_left = -1.0
	pending_stagger = 0.0
	throw_spot = character_body.global_position
	animation_player.play("throw_windup")
	ParryTell.telegraph(character_body, &"eric_thrown_sword", TELL_TIME, _tell_anchor)


func Exit() -> void:
	ParryTell.clear(character_body)
	planted_left = -1.0
	pending_stagger = 0.0
	if is_instance_valid(sword):
		sword.queue_free()
	sword = null


func Physics_Update(delta: float) -> void:
	if planted_left < 0.0:
		return
	planted_left -= delta
	if planted_left <= 0.0:
		planted_left = -1.0
		animation_player.play("recall_reach")
		var flipped: bool = character_body.sprite.flip_h
		var lean := deg_to_rad(EricArtLayout.THROW_CATCH_ANGLE)
		var catch_centre: Vector2 = character_body.to_global(EricArtLayout.frame_local(EricArtLayout.THROW_CATCH_CENTRE, flipped))
		sword.recall(catch_centre, _ground_y(), -lean if flipped else lean, not flipped)
		_play_whoosh()


func _ground_y() -> float:
	return character_body.frame_point(Vector2(0, EricArtLayout.FEET_ROW)).y


# His daze anchor is tuned for his downed frames, too low for a standing tell.
func _tell_anchor() -> Vector2:
	return character_body.to_global(EricArtLayout.frame_local(TELL_HEAD_PIXEL + Vector2(0.5, 0.5), character_body.sprite.flip_h))


# Called by the throw_release animation on frame 35: frame 34 still draws the sword leaving his
# hands.
func release_sword() -> void:
	# The sword in the air is the threat now: the warning has done its job.
	ParryTell.clear(character_body)
	var rage: float = eric_state_machine.rage
	sword = SWORD_SCENE.instantiate()
	sword.speed = lerpf(flight_speed, rage_flight_speed, rage)
	sword.player = player
	sword.thrower = character_body
	sword.landed.connect(_on_sword_landed)
	sword.returned.connect(_on_sword_returned)
	sword.struck_thrower.connect(_on_sword_struck_thrower)
	var hand: Vector2 = character_body.frame_point(EricArtLayout.THROW_RELEASE_PIXEL)
	eric_state_machine.add_hazard(sword, Vector2(hand.x, _ground_y()))
	sword.throw(hand, _ground_y(), player.global_position)
	_play_whoosh()


# Called by the boss once the player parries the sword in the air (BossOneScript.parry_stagger). It
# is already stopped where they caught it; from here it only flies at him, and nothing interrupts it
# short of the fight ending, which frees every hazard.
func reflect(stagger_duration: float) -> void:
	if not is_instance_valid(sword):
		return
	pending_stagger = stagger_duration + reflect_stagger_bonus
	sword.reflect(character_body.frame_point(EricArtLayout.BODY_BOX.get_center()), _ground_y(), reflect_speed)
	_play_whoosh()


# The flung-back sword arrives. It never planted, so there is no ring; it is spent on him, and his
# staggered frames draw him holding it again, ready for the next throw.
# Reading his own sword back into his chest is the payoff move: the stagger it leaves him in opens a
# finisher daze and the uppercut fires on its own. A reflect that kills him outright never gets
# there, and the outro runs off take_punch as it always has.
func _on_sword_struck_thrower() -> void:
	if eric_state_machine.current_state != self:
		return
	sword.queue_free()
	sword = null
	character_body.take_punch(REFLECT_DAMAGE)
	if character_body.boss_health <= 0 or eric_state_machine.defeated:
		return
	# This window is its own daze, whatever an earlier Downed window spent.
	character_body.daze_used = false
	eric_state_machine.parry_stagger(pending_stagger, throw_spot, true)
	if player.finisher.begin_auto(character_body):
		eric_state_machine.states["ParryStaggered"].drive_player_in(player)


func _on_sword_landed() -> void:
	var rage: float = eric_state_machine.rage
	var contact: Vector2 = sword.global_position
	eric_state_machine.add_hazard(IMPACT_SCENE.instantiate(), contact)
	var ring = RING_SCENE.instantiate()
	ring.speed = lerpf(ring_speed, rage_ring_speed, rage)
	ring.player = player
	eric_state_machine.add_hazard(ring, contact)
	planted_left = lerpf(planted_time, rage_planted_time, rage)

	var sfx = character_body.get_node_or_null("EarthquakeSfxPlayer")
	if sfx:
		if not sfx.stream:
			sfx.stream = load("res://Assets/Audio/SFX/earthquake_slam.ogg")
		sfx.play()


func _on_sword_returned() -> void:
	sword.queue_free()
	sword = null
	animation_player.play("recall_catch")


func _play_whoosh() -> void:
	var sfx = character_body.get_node_or_null("WhirlwindSfxPlayer")
	if sfx:
		if not sfx.stream:
			sfx.stream = load("res://Assets/Audio/SFX/whirlwind_whoosh.ogg")
		sfx.play()


func _on_animation_player_animation_finished(anim_name: StringName) -> void:
	if eric_state_machine.current_state != self:
		return
	match anim_name:
		&"throw_windup":
			animation_player.play("throw_release")
		&"throw_release":
			animation_player.play("empty_wait")
		&"recall_catch":
			eric_state_machine.attack_finished()
