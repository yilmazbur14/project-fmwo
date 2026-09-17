extends State

# Liam and Bixby's entrance, as named beats: carry_in plays first, then LiamPreFight.dialogue calls the
# rest between its lines and waits for each one. Placement follows the entrance mockups
# (LiamEntranceLayout).

const LiamEntranceLayout := preload("res://Scripts/LiamEntranceLayout.gd")
const BixbyBeastArtLayout := preload("res://Scripts/BixbyBeastArtLayout.gd")
const CARRIERS_TEXTURE := preload("res://Assets/Characters/Liam/Entrance/liam_carriers.png")
# Storyboard strips of 128x96 frames with the lettering drawn in.
const SLAP_KEYS := preload("res://Assets/Characters/Liam/Entrance/liam_slap_keys.png")
const FED_UP := preload("res://Assets/Characters/Liam/Entrance/bixby_fedup.png")
const SWALLOW_KEYS := preload("res://Assets/Characters/Liam/Entrance/bixby_swallow_keys.png")

@export var body : CharacterBody2D
@export var procession : Node2D
@export var marcher : Node2D
@export var march_shadows : Node2D
@export var set_down_shadows : Node2D
@export var walking_carrier : Sprite2D
@export var throne_bixby : Sprite2D
@export var seated_liam : Sprite2D
@export var downstage : Node2D
@export var hop_bixby : Sprite2D
@export var hop_liam : Sprite2D
@export var storyboard : Sprite2D
@export var tint : ColorRect
@export var transform_keys : Sprite2D
@export var flash : ColorRect
@export var land_sfx_player : AudioStreamPlayer
@export var slap_sfx_player : AudioStreamPlayer
@export var growl_sfx_player : AudioStreamPlayer
@export var gulp_sfx_player : AudioStreamPlayer
@export var glow_sfx_player : AudioStreamPlayer
@export var roar_sfx_player : AudioStreamPlayer

@onready var state_machine = get_parent()

#SET DOWN
const SET_DOWN_SHAKE_STRENGTH := 6.0
const SET_DOWN_SHAKE_STEPS := 4
const SET_DOWN_SHAKE_STEP_TIME := 0.03
const BEAT_BEFORE_FLOP := 0.25
const FLOP_CHEER := 1.0
const BEAT_AFTER_FLOP := 0.5

#STORYBOARD (seconds each frame holds)
const LANDING_SHAKE_STRENGTH := 4.0
const BEAT_AFTER_HOP := 0.3
const WIND_UP_HOLD := 0.45
const SMACK_HOLD := 0.55
const LIKES_IT_HOLD := 0.3
const FED_UP_HOLD := 0.5
const LUNGE_HOLD := 0.4
const CHOMP_HOLD := 0.6
const GULP_HOLD := 0.5
# On SMACK and CHOMP.
const HIT_SHAKE_PX := 6.0
const HIT_SCREEN_SHAKE := 8.0
const HIT_SHAKE_STEPS := 5
const HIT_SHAKE_STEP_TIME := 0.03
const SMACK_CHEER := 0.8
const CHOMP_CHEER := 1.2

#TRANSFORM
const GLOW_HOLD := 0.7
const SWELL_HOLD := 0.5
const FLASH_FRAME_HOLD := 0.35
const FLASH_IN_TIME := 0.08
const FLASH_OUT_TIME := 0.5
const ROAR_SCREEN_SHAKE := 16.0
const ROAR_SHAKE_STEP_TIME := 0.04
const ROAR_CHEER := 2.5
const THRONE_FADE_TIME := 0.8

var carrier_rests := {}
var bixby_shadow: Sprite2D
var liam_shadow: Sprite2D


func Enter() -> void:
	for spec in LiamEntranceLayout.MARCH_SHADOWS:
		_add_shadow(march_shadows, spec[0], spec[1])
	_add_shadow(set_down_shadows, LiamEntranceLayout.SET_DOWN_SHADOW[0], LiamEntranceLayout.SET_DOWN_SHADOW[1])
	bixby_shadow = _add_shadow(downstage, LiamEntranceLayout.BIXBY_SHADOW[0], LiamEntranceLayout.BIXBY_SHADOW[1])
	liam_shadow = _add_shadow(downstage, LiamEntranceLayout.LIAM_SHADOW[0], LiamEntranceLayout.LIAM_SHADOW[1])
	tint.color = Color(LiamEntranceLayout.FLASH_COLOR, 0.0)
	flash.color = Color(LiamEntranceLayout.FLASH_COLOR, 0.0)
	_play()


func _play() -> void:
	await carry_in()
	state_machine.show_pre_fight_dialogue(self)


# Behind everything else on `parent`.
func _add_shadow(parent: Node2D, centre: Vector2, radii: Vector2) -> Sprite2D:
	var shadow := LiamEntranceLayout.floor_shadow(radii)
	shadow.position = centre
	parent.add_child(shadow)
	parent.move_child(shadow, 0)
	return shadow


# The procession marches in from the top of the screen and sets the throne down, and the carriers flop.
func carry_in() -> void:
	for carrier_name in LiamEntranceLayout.CARRIERS:
		carrier_rests[carrier_name] = marcher.get_node(NodePath(carrier_name)).position
	var start := Vector2(0, -LiamEntranceLayout.MARCH_RISE)
	marcher.position = start
	procession.show()
	get_tree().call_group("arena_crowd", "cheer", LiamEntranceLayout.MARCH_TIME)
	var march := create_tween()
	march.tween_method(_march.bind(start), 0.0, 1.0, LiamEntranceLayout.MARCH_TIME)
	await march.finished

	land_sfx_player.play()
	body.shake_screen(SET_DOWN_SHAKE_STRENGTH, SET_DOWN_SHAKE_STEPS, SET_DOWN_SHAKE_STEP_TIME)
	march_shadows.hide()
	set_down_shadows.show()
	await _pause(BEAT_BEFORE_FLOP)

	var flop := create_tween().set_parallel()
	for carrier_name in LiamEntranceLayout.CARRIERS:
		var carrier: Sprite2D = marcher.get_node(NodePath(carrier_name))
		var spec: Dictionary = LiamEntranceLayout.CARRIERS[carrier_name]
		carrier.texture = CARRIERS_TEXTURE
		carrier.frame = spec.frame
		flop.tween_method(_flop.bind(carrier, carrier.position, spec.flop, deg_to_rad(spec.turn)), 0.0, 1.0, LiamEntranceLayout.FLOP_TIME)
	await flop.finished
	for carrier_name in LiamEntranceLayout.CARRIERS:
		var spec: Dictionary = LiamEntranceLayout.CARRIERS[carrier_name]
		_add_shadow(set_down_shadows, spec.shadow, LiamEntranceLayout.FLOPPED_SHADOW_RADII)
		var sweat := LiamEntranceLayout.sweat_drop()
		sweat.position = spec.sweat
		marcher.add_child(sweat)
	get_tree().call_group("arena_crowd", "cheer", FLOP_CHEER)
	await _pause(BEAT_AFTER_FLOP)


func _march(weight: float, start: Vector2) -> void:
	marcher.position = start.lerp(Vector2.ZERO, weight).round()
	var step := int(weight * LiamEntranceLayout.MARCH_TIME / LiamEntranceLayout.WALK_FRAME_TIME) % LiamEntranceLayout.WALK_FRAMES
	walking_carrier.frame = step
	var bob := LiamEntranceLayout.MARCH_BOB_PX if step % 2 == 0 and weight < 1.0 else 0.0
	for carrier_name in carrier_rests:
		var carrier: Sprite2D = marcher.get_node(NodePath(carrier_name))
		if carrier != walking_carrier:
			carrier.position = carrier_rests[carrier_name] + Vector2(0, bob)


func _flop(weight: float, carrier: Sprite2D, from: Vector2, to: Vector2, turn: float) -> void:
	carrier.position = (from.lerp(to, weight) - Vector2(0, LiamEntranceLayout.FLOP_HOP * 4.0 * weight * (1.0 - weight))).round()
	carrier.rotation = turn * weight


# Liam and Bixby jump down off the throne to stand in front of it.
func liam_and_bixby_step_down() -> void:
	var seat := downstage.to_local(procession.to_global(LiamEntranceLayout.SEAT))
	var cushion := downstage.to_local(procession.to_global(LiamEntranceLayout.CUSHION))
	seated_liam.hide()
	throne_bixby.hide()
	bixby_shadow.hide()
	liam_shadow.hide()
	hop_liam.position = seat
	hop_bixby.position = cushion
	downstage.show()
	var hop := create_tween().set_parallel()
	hop.tween_method(_hop.bind(hop_liam, seat, LiamEntranceLayout.LIAM_FEET), 0.0, 1.0, LiamEntranceLayout.HOP_TIME)
	hop.tween_method(_hop.bind(hop_bixby, cushion, Vector2.ZERO), 0.0, 1.0, LiamEntranceLayout.HOP_TIME)
	await hop.finished
	bixby_shadow.show()
	liam_shadow.show()
	body.shake_screen(LANDING_SHAKE_STRENGTH, HIT_SHAKE_STEPS, HIT_SHAKE_STEP_TIME)
	await _pause(BEAT_AFTER_HOP)


func _hop(weight: float, node: Node2D, from: Vector2, to: Vector2) -> void:
	node.position = (from.lerp(to, weight) - Vector2(0, LiamEntranceLayout.HOP_HEIGHT * 4.0 * weight * (1.0 - weight))).round()


func liam_slaps_bixby() -> void:
	_show_storyboard(SLAP_KEYS, 0)
	await _pause(WIND_UP_HOLD)
	_show_storyboard(SLAP_KEYS, 1)
	slap_sfx_player.play()
	_hit_shake()
	get_tree().call_group("arena_crowd", "cheer", SMACK_CHEER)
	await _pause(SMACK_HOLD)
	# "He likes it!", while Bixby glares.
	_show_storyboard(SLAP_KEYS, 2)
	await _pause(LIKES_IT_HOLD)


func bixby_growls() -> void:
	_show_storyboard(FED_UP, 0)
	growl_sfx_player.play()
	await _pause(FED_UP_HOLD)


func bixby_swallows_liam() -> void:
	_show_storyboard(SWALLOW_KEYS, 0)
	await _pause(LUNGE_HOLD)
	_show_storyboard(SWALLOW_KEYS, 1)
	liam_shadow.hide()
	gulp_sfx_player.play()
	_hit_shake()
	get_tree().call_group("arena_crowd", "cheer", CHOMP_CHEER)
	await _pause(CHOMP_HOLD)
	_show_storyboard(SWALLOW_KEYS, 2)
	await _pause(GULP_HOLD)


# Bixby glows and swells into the beast's silhouette, the screen flashes, and the beast stands in his place
# and roars while the throne fades away.
func bixby_transforms() -> void:
	storyboard.hide()
	transform_keys.position = downstage.global_position + LiamEntranceLayout.TRANSFORM_CORNER
	transform_keys.frame = 0
	transform_keys.show()
	glow_sfx_player.play()
	await _pause(GLOW_HOLD)
	transform_keys.frame = 1
	await _pause(SWELL_HOLD)
	transform_keys.frame = 2
	tint.color.a = LiamEntranceLayout.FLASH_FRAME_TINT
	await _pause(FLASH_FRAME_HOLD)

	var flash_in := create_tween()
	flash_in.tween_property(flash, "color:a", 1.0, FLASH_IN_TIME)
	await flash_in.finished
	transform_keys.hide()
	tint.color.a = 0.0
	downstage.hide()
	body.appear(downstage.global_position)
	body.play_anim(&"roar")
	create_tween().tween_property(flash, "color:a", 0.0, FLASH_OUT_TIME)
	var fade := create_tween()
	fade.tween_property(procession, "modulate:a", 0.0, THRONE_FADE_TIME)
	fade.tween_callback(procession.hide)

	# The roar itself starts after the coil frame.
	var coil := BixbyBeastArtLayout.time_to_step(&"roar", 1)
	await _pause(coil)
	roar_sfx_player.play()
	var roar_frames: int = BixbyBeastArtLayout.ANIMS[&"roar"].frames.size()
	var roar_time := BixbyBeastArtLayout.time_to_step(&"roar", roar_frames) - coil
	body.shake_screen(ROAR_SCREEN_SHAKE, roundi(roar_time / ROAR_SHAKE_STEP_TIME), ROAR_SHAKE_STEP_TIME)
	get_tree().call_group("arena_crowd", "cheer", ROAR_CHEER)
	if not body.anim_done:
		await body.anim_finished


func _show_storyboard(sheet: Texture2D, frame: int) -> void:
	hop_liam.hide()
	hop_bixby.hide()
	storyboard.frame = 0
	storyboard.texture = sheet
	storyboard.hframes = roundi(sheet.get_width() / float(LiamEntranceLayout.STORYBOARD_FRAME_WIDTH))
	storyboard.frame = frame
	storyboard.show()


func _hit_shake() -> void:
	body.shake_screen(HIT_SCREEN_SHAKE, HIT_SHAKE_STEPS, HIT_SHAKE_STEP_TIME)
	var tween := storyboard.create_tween()
	for i in HIT_SHAKE_STEPS:
		var offset := Vector2(randf_range(-HIT_SHAKE_PX, HIT_SHAKE_PX), randf_range(-HIT_SHAKE_PX, HIT_SHAKE_PX)).round()
		tween.tween_callback(func() -> void: storyboard.position = LiamEntranceLayout.STORYBOARD_CENTRE + offset)
		tween.tween_interval(HIT_SHAKE_STEP_TIME)
	tween.tween_callback(func() -> void: storyboard.position = LiamEntranceLayout.STORYBOARD_CENTRE)


func _pause(seconds: float) -> void:
	var tween := create_tween()
	tween.tween_interval(seconds)
	await tween.finished
