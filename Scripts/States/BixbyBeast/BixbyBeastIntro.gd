extends State

# Liam and Bixby's entrance, as named beats: carry_in runs first, then LiamPreFight.dialogue calls the
# rest between its lines. Each beat is its own coroutine that the dialogue waits on, so a drawn
# animation from Assets/Characters/Liam/Entrance/ can replace one beat's placeholder tweens at a time.

@export var body : CharacterBody2D
@export var entrance : Node2D
@export var liam : Sprite2D
@export var bixby : Sprite2D
@export var smack_label : Label
@export var flash : ColorRect
@export var slap_sfx_player : AudioStreamPlayer
@export var growl_sfx_player : AudioStreamPlayer
@export var gulp_sfx_player : AudioStreamPlayer
@export var glow_sfx_player : AudioStreamPlayer
@export var roar_sfx_player : AudioStreamPlayer

@onready var state_machine = get_parent()

const SWALLOW_TEXTURE := preload("res://Assets/Characters/Bixby/bixby_swallow_draft.png")
# bixby_swallow_draft.png is 8 texels taller than bixby.png, all of it above his feet.
const SWALLOW_OFFSET := Vector2(0, -4)

#CARRY IN
# The palanquin comes down from above the top of the screen to where the scene places it.
const CARRY_IN_RISE := 760.0
const CARRY_IN_TIME := 2.6
# The carriers' steps bob it by a texel.
const CARRY_STEP_TIME := 0.2
const CARRY_STEP_PX := 3.0
const BEAT_AFTER_CARRY_IN := 0.4

#SLAP
const SLAP_REACH := Vector2(27, -6)
const SLAP_WIND_UP_TIME := 0.12
const SLAP_RETURN_TIME := 0.2
const SMACK_POP_SCALE := 1.2
const SMACK_POP_TIME := 0.07
const SMACK_HOLD := 0.35
const SMACK_FADE_TIME := 0.2
const SMACK_TILT_DEGREES := 10.0
const SMACK_CHEER := 0.6
const FLINCH_PX := 6.0
const FLINCH_STEPS := 5
const FLINCH_STEP_TIME := 0.03
const BEAT_AFTER_SLAP := 0.35

#GROWL
const GROWL_TIME := 0.9
const GROWL_TINT := Color(1.35, 0.8, 0.75)
const TREMBLE_PX := 3.0
const TREMBLE_STEP_TIME := 0.04

#SWALLOW
# Normal Bixby's middle mouth on bixby.png, in px from his feet.
const BIXBY_MOUTH := Vector2(0, -132)
const SWALLOW_TIME := 0.4
const SWALLOWED_SCALE := 0.6
const GULP_HOP_PX := 9.0
const GULP_HOP_TIME := 0.08
const GULP_CHEER := 1.0
const BEAT_AFTER_SWALLOW := 0.5

#TRANSFORM
const GLOW_COLOR := Color(2.6, 1.5, 0.9)
const GLOW_PULSES := 4
const GLOW_PULSE_TIME := 0.28
const FLASH_IN_TIME := 0.12
const FLASH_HOLD := 0.1
const FLASH_OUT_TIME := 0.6
const ROAR_SCREEN_SHAKE := 18.0
const ROAR_SPRITE_SHAKE := 4.0
const ROAR_SHAKE_STEPS := 14
const ROAR_SHAKE_STEP_TIME := 0.04
const ROAR_CHEER := 2.0
const BEAT_AFTER_ROAR := 0.6

var entrance_stop := Vector2.ZERO
var liam_seat := Vector2.ZERO
var bixby_seat := Vector2.ZERO
var smack_tween: Tween


func Enter() -> void:
	entrance_stop = entrance.position
	liam_seat = liam.position
	bixby_seat = bixby.position
	smack_label.pivot_offset = smack_label.size / 2.0
	_play()


func _play() -> void:
	await carry_in()
	state_machine.show_pre_fight_dialogue(self)


func carry_in() -> void:
	var from := entrance_stop - Vector2(0, CARRY_IN_RISE)
	entrance.position = from
	entrance.show()
	get_tree().call_group("arena_crowd", "cheer", CARRY_IN_TIME)
	var tween := create_tween()
	tween.tween_method(_carry.bind(from), 0.0, 1.0, CARRY_IN_TIME)
	await tween.finished
	await _pause(BEAT_AFTER_CARRY_IN)


func _carry(weight: float, from: Vector2) -> void:
	var travelled := 1.0 - (1.0 - weight) * (1.0 - weight)
	var stepping := weight < 1.0 and int(weight * CARRY_IN_TIME / CARRY_STEP_TIME) % 2 == 1
	entrance.position = (from.lerp(entrance_stop, travelled) - Vector2(0, CARRY_STEP_PX if stepping else 0.0)).round()


func liam_slaps_bixby() -> void:
	var tween := create_tween()
	tween.tween_method(_move.bind(liam, liam_seat, liam_seat + SLAP_REACH), 0.0, 1.0, SLAP_WIND_UP_TIME).set_ease(Tween.EASE_IN).set_trans(Tween.TRANS_QUAD)
	tween.tween_callback(_smack)
	tween.tween_method(_move.bind(liam, liam_seat + SLAP_REACH, liam_seat), 0.0, 1.0, SLAP_RETURN_TIME).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_QUAD)
	await tween.finished
	await _pause(BEAT_AFTER_SLAP)


func _smack() -> void:
	slap_sfx_player.play()
	get_tree().call_group("arena_crowd", "cheer", SMACK_CHEER)
	_shake(bixby, bixby_seat, FLINCH_PX, FLINCH_STEPS, FLINCH_STEP_TIME)

	if smack_tween:
		smack_tween.kill()
	smack_label.show()
	smack_label.modulate.a = 1.0
	smack_label.scale = Vector2.ONE * 0.4
	smack_label.rotation = deg_to_rad(randf_range(-SMACK_TILT_DEGREES, SMACK_TILT_DEGREES))
	smack_tween = smack_label.create_tween()
	smack_tween.tween_property(smack_label, "scale", Vector2.ONE * SMACK_POP_SCALE, SMACK_POP_TIME)
	smack_tween.tween_property(smack_label, "scale", Vector2.ONE, SMACK_POP_TIME)
	smack_tween.tween_interval(SMACK_HOLD)
	smack_tween.tween_property(smack_label, "modulate:a", 0.0, SMACK_FADE_TIME)
	smack_tween.tween_callback(smack_label.hide)


func bixby_growls() -> void:
	growl_sfx_player.play()
	_shake(bixby, bixby_seat, TREMBLE_PX, int(GROWL_TIME / TREMBLE_STEP_TIME), TREMBLE_STEP_TIME)
	var tween := create_tween()
	tween.tween_property(bixby, "modulate", GROWL_TINT, GROWL_TIME * 0.3)
	tween.tween_interval(GROWL_TIME * 0.4)
	tween.tween_property(bixby, "modulate", Color.WHITE, GROWL_TIME * 0.3)
	await tween.finished


func bixby_swallows_liam() -> void:
	var mouth := bixby_seat + BIXBY_MOUTH
	var tween := create_tween().set_parallel()
	tween.tween_method(_move.bind(liam, liam_seat, mouth), 0.0, 1.0, SWALLOW_TIME).set_ease(Tween.EASE_IN).set_trans(Tween.TRANS_BACK)
	tween.tween_property(liam, "scale", Vector2.ONE * SWALLOWED_SCALE, SWALLOW_TIME).set_ease(Tween.EASE_IN)
	await tween.finished

	liam.hide()
	bixby.texture = SWALLOW_TEXTURE
	bixby.offset += SWALLOW_OFFSET
	gulp_sfx_player.play()
	get_tree().call_group("arena_crowd", "cheer", GULP_CHEER)
	var gulp := create_tween()
	gulp.tween_callback(func() -> void: bixby.position = bixby_seat - Vector2(0, GULP_HOP_PX))
	gulp.tween_interval(GULP_HOP_TIME)
	gulp.tween_callback(func() -> void: bixby.position = bixby_seat)
	await gulp.finished
	await _pause(BEAT_AFTER_SWALLOW)


func bixby_transforms() -> void:
	glow_sfx_player.play()
	_shake(bixby, bixby_seat, TREMBLE_PX, int(GLOW_PULSES * GLOW_PULSE_TIME / TREMBLE_STEP_TIME), TREMBLE_STEP_TIME)
	var glow := create_tween()
	for i in GLOW_PULSES:
		glow.tween_property(bixby, "modulate", GLOW_COLOR, GLOW_PULSE_TIME / 2.0)
		glow.tween_property(bixby, "modulate", Color.WHITE, GLOW_PULSE_TIME / 2.0)
	await glow.finished

	var flash_in := create_tween()
	flash_in.tween_property(flash, "color:a", 1.0, FLASH_IN_TIME)
	await flash_in.finished
	entrance.hide()
	body.appear(entrance.to_global(bixby_seat))
	await _pause(FLASH_HOLD)

	var flash_out := create_tween()
	flash_out.tween_property(flash, "color:a", 0.0, FLASH_OUT_TIME)
	roar_sfx_player.play()
	body.play_anim(&"roar", &"hover")
	body.shake_screen(ROAR_SCREEN_SHAKE, ROAR_SHAKE_STEPS, ROAR_SHAKE_STEP_TIME)
	body.shake_sprite(ROAR_SPRITE_SHAKE, ROAR_SHAKE_STEPS, ROAR_SHAKE_STEP_TIME)
	get_tree().call_group("arena_crowd", "cheer", ROAR_CHEER)
	await flash_out.finished
	await _pause(BEAT_AFTER_ROAR)
	body.play_anim(&"hover")


func _move(weight: float, node: Node2D, from: Vector2, to: Vector2) -> void:
	node.position = from.lerp(to, weight).round()


# Whole-pixel jolts around `rest`.
func _shake(node: Node2D, rest: Vector2, strength: float, steps: int, step_time: float) -> void:
	var tween := node.create_tween()
	for i in steps:
		var offset := Vector2(randf_range(-strength, strength), randf_range(-strength, strength)).round()
		tween.tween_callback(func() -> void: node.position = rest + offset)
		tween.tween_interval(step_time)
	tween.tween_callback(func() -> void: node.position = rest)


func _pause(seconds: float) -> void:
	var tween := create_tween()
	tween.tween_interval(seconds)
	await tween.finished
