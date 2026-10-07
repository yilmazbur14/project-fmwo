extends State

# Eric throws his sword at where the player stands. It sticks in the ground and sends out an
# earthquake ring, then flies back to his hand.
# The wind-up warns first: a parry as the sword comes down on its mark flings it back at him, and it
# takes a chip of health off and staggers him where he threw it when it arrives. A held guard absorbs
# it as before, and an unparried sword plants and rings as before. It hurts nobody on the way to the
# mark (EricThrownSwordScript), and nobody on the way back to his hand.
# The V2 whirlwind ends in this same state (EricStateMachine.throw_from_whirlwind): the spin lets the
# sword go on these release frames, so the parry, the chip and the stagger are the throw's own. That
# one skips off the mat instead of planting, so there is no ring and no wait before he takes it back,
# and he is open to punches while it is out of his hands, a POW there dazing him (EricScript.can_be_dazed).

@export var animation_player : AnimationPlayer
@export var character_body : CharacterBody2D
@export var hurtbox : Area2D
@export var eric_state_machine : Node

const EricPacing := preload("res://Scripts/EricPacing.gd")
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
# whirl_release's length up to its own release frame, for the throw the whirlwind hands over. Past the
# red tell's floor (EricPacing's slam_tell_time) and 1.8x PlayerDefense.parry_window.
const WHIRL_TELL_TIME := 0.44
# What the flung-back sword takes off him, on top of the punches the stagger then opens up.
const REFLECT_DAMAGE := 1

@onready var player = get_tree().current_scene.get_node("Arena/MainPlayer/CharacterBody2D")

var sword: Node2D
var planted_left := -1.0
# Where he stood to throw, which the stagger puts him back on.
var throw_spot: Vector2
var pending_stagger := 0.0
# Set by the state machine before it switches here, and cleared on the way out: the whirlwind's spin
# release rather than a throw he wound up himself.
var from_whirlwind := false


func Enter() -> void:
	planted_left = -1.0
	pending_stagger = 0.0
	throw_spot = character_body.global_position
	if from_whirlwind:
		# whirl_release's spin frames are spaced wider and wider on purpose: the throw plays at
		# speed_scale 1.0 where the whirlwind spins at 1.5-2.1x, so evenly spaced ones would speed the
		# spin up into the release instead of winding it down.
		animation_player.play("whirl_release")
		ParryTell.telegraph(character_body, &"eric_thrown_sword", WHIRL_TELL_TIME, _tell_anchor)
		return
	animation_player.play("throw_windup")
	ParryTell.telegraph(character_body, &"eric_thrown_sword", TELL_TIME, _tell_anchor)


func Exit() -> void:
	ParryTell.clear(character_body)
	planted_left = -1.0
	pending_stagger = 0.0
	if is_instance_valid(sword):
		sword.queue_free()
	sword = null
	if from_whirlwind:
		# Shut here and now, not deferred: the window he goes on to (EricWinded) opens its own on the
		# way in, and a deferred close would land on top of it and shut him for all of it.
		hurtbox.monitoring = false
		hurtbox.monitorable = false
	from_whirlwind = false


func Physics_Update(delta: float) -> void:
	if planted_left < 0.0:
		return
	planted_left -= delta
	if planted_left <= 0.0:
		_recall_now()


# Back into his hand: from the mat it is planted in, or from where a spin release skipped off it.
func _recall_now() -> void:
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
	sword.speed = EricPacing.raged("sword_speed", rage)
	sword.player = player
	sword.thrower = character_body
	sword.landed.connect(_on_sword_landed)
	sword.returned.connect(_on_sword_returned)
	sword.struck_thrower.connect(_on_sword_struck_thrower)
	var hand: Vector2 = character_body.frame_point(EricArtLayout.THROW_RELEASE_PIXEL)
	eric_state_machine.add_hazard(sword, Vector2(hand.x, _ground_y()), false)
	sword.lay_shadow_on(eric_state_machine.ground_layer())
	sword.plants = not from_whirlwind
	sword.throw(hand, _ground_y(), player.global_position)
	# The reworked feel only. The sword is aimed at where they stood and never re-aims, so once they
	# have walked off that spot the throw says nothing: the floor says where and when it lands, and
	# the blade wears the red the badge over his head just dropped. Neither touches the attack.
	if player.feel_v2:
		eric_state_machine.add_hazard(sword.mark_landing(), sword.to_ground, true)
		sword.glow_as_parryable()
	if from_whirlwind:
		# What the spin's dizzy stop was, and only now the sword is out of his hands: the red wind-up
		# before this is still a warning to read, not a free punch.
		hurtbox.set_deferred("monitoring", true)
		hurtbox.set_deferred("monitorable", true)
		# An opening of its own, with its own daze (EricScript.can_be_dazed).
		character_body.daze_used = false
	_play_whoosh()


# Called by the boss once the player parries the sword on its mark (EricScript.parry_stagger). It
# is already stopped where they caught it; from here it only flies at him, and nothing interrupts it
# short of the fight ending, which frees every hazard.
func reflect(stagger_duration: float) -> void:
	if not is_instance_valid(sword):
		return
	pending_stagger = stagger_duration + EricPacing.value("reflect_stagger_bonus")
	sword.reflect(character_body.frame_point(EricArtLayout.BODY_BOX.get_center()), _ground_y(), EricPacing.value("reflect_speed"))
	_play_whoosh()


# The flung-back sword arrives. It never planted, so there is no ring; it is spent on him, and his
# staggered frames draw him holding it again, ready for the next throw.
# Reading his own sword back into his chest is the payoff move. With EricPacing's reflect_auto_uppercut
# (V1) the stagger it leaves him in opens a finisher daze and the uppercut fires on its own; without it
# (V2 since 2026-10-04) it is a plain parry stagger, open to punches, as a parried bear hug is, and the
# payoff is the chip and a big share of his Break gauge. A reflect that kills him outright never gets
# there, and the outro runs off take_punch as it always has.
func _on_sword_struck_thrower() -> void:
	if eric_state_machine.current_state != self:
		return
	sword.queue_free()
	sword = null
	character_body.take_punch(REFLECT_DAMAGE)
	if character_body.boss_health <= 0 or eric_state_machine.defeated:
		return
	# V2: it fills his Break gauge too, and one it fills breaks him instead.
	var gauge: Node = character_body.break_gauge
	if gauge and gauge.add(gauge.reflect_gain):
		return
	if not EricPacing.value("reflect_auto_uppercut"):
		eric_state_machine.parry_stagger(pending_stagger, throw_spot)
		return
	# This window is its own daze, whatever an earlier Downed window spent.
	character_body.daze_used = false
	eric_state_machine.parry_stagger(pending_stagger, throw_spot, true)
	if player.finisher.begin_auto(character_body):
		eric_state_machine.states["ParryStaggered"].drive_player_in(player)


func _on_sword_landed() -> void:
	var contact: Vector2 = sword.global_position
	eric_state_machine.add_hazard(IMPACT_SCENE.instantiate(), contact)
	# The spin release skips off the mat: the dust it kicks up, but no plant, no ring, and no wait
	# before he pulls it back.
	if from_whirlwind:
		_recall_now()
		return
	var rage: float = eric_state_machine.rage
	var ring = RING_SCENE.instantiate()
	ring.speed = EricPacing.raged("ring_speed", rage)
	ring.player = player
	eric_state_machine.add_hazard(ring, contact)
	planted_left = EricPacing.raged("planted_time", rage)

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
		&"throw_release", &"whirl_release":
			animation_player.play("empty_wait")
		&"recall_catch":
			eric_state_machine.attack_finished()
