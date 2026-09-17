extends State

# Liam and Bixby's entrance, as named beats: carry_in plays first, then LiamPreFight.dialogue calls the
# rest between its lines and waits for each one. Placement follows the entrance mockups
# (LiamEntranceLayout).

const LiamEntranceLayout := preload("res://Scripts/LiamEntranceLayout.gd")
const BixbyBeastArtLayout := preload("res://Scripts/BixbyBeastArtLayout.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const HitStop := preload("res://Scripts/HitStop.gd")
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
@export var transform_stage : Node2D
@export var transform_body : Sprite2D
@export var transform_aura : Sprite2D
@export var transform_shockwave : Sprite2D
@export var dim : ColorRect
@export var flash : ColorRect
@export var land_sfx_player : AudioStreamPlayer
@export var slap_sfx_player : AudioStreamPlayer
@export var growl_sfx_player : AudioStreamPlayer
@export var gulp_sfx_player : AudioStreamPlayer
@export var glow_sfx_player : AudioStreamPlayer
@export var blast_sfx_player : AudioStreamPlayer
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

#TRANSFORM (every cue hangs off a frame of bixby_transform.png)
const SHAKE_STEP_TIME := 0.04
const CRACK_SHAKE := 4.0
const LIFT_SHAKE := 11.0
const SWELL_SHAKE := 4.0
const WINGS_SHAKE := 14.0
const WINGS_SNAP_SHAKE := 16.0
const WINGS_SNAP_HIT_STOP := 0.07
const BLAST_SHAKE := 26.0
const BLAST_SHAKE_TIME := 0.4
const BLAST_HIT_STOP := 0.12
# How dark the arena goes for the implosion.
const DIM_DEEPEST := 0.45
# The view pushes in on him while he swells, eases back for the implosion and punches in on the blast.
const SWELL_ZOOM := 1.07
const BLAST_ZOOM := 1.12
const BLAST_ZOOM_TIME := 0.06
const ZOOM_FOCUS_RISE := 300.0
const FLASH_OUT_TIME := 0.2
const THRONE_FADE_TIME := 0.8

#LANDING AND ROAR
const LANDING_SHAKE := 12.0
const LANDING_SHAKE_TIME := 0.14
const ROAR_JOLT_SHAKE := 6.0
const ROAR_JOLT_TIME := 0.12
# [wait since the last one, strength, how long it shakes]: the roar builds to its peak 0.8s in, where the
# sound peaks, and eases off from 1.1s.
const ROAR_SHAKES := [[0.45, 12.0, 0.35], [0.35, 22.0, 0.3], [0.3, 12.0, 0.55]]
# He holds the roar until the sound has decayed, before the fight starts.
const ROAR_HOLD := 1.9
const ROAR_CHEER := 2.5

var carrier_rests := {}
var bixby_shadow: Sprite2D
var liam_shadow: Sprite2D
var aura_loop: Tween


func Enter() -> void:
	for spec in LiamEntranceLayout.MARCH_SHADOWS:
		_add_shadow(march_shadows, spec[0], spec[1])
	_add_shadow(set_down_shadows, LiamEntranceLayout.SET_DOWN_SHADOW[0], LiamEntranceLayout.SET_DOWN_SHADOW[1])
	bixby_shadow = _add_shadow(downstage, LiamEntranceLayout.BIXBY_SHADOW[0], LiamEntranceLayout.BIXBY_SHADOW[1])
	liam_shadow = _add_shadow(downstage, LiamEntranceLayout.LIAM_SHADOW[0], LiamEntranceLayout.LIAM_SHADOW[1])
	transform_body.offset = LiamEntranceLayout.transform_offset()
	transform_aura.offset = LiamEntranceLayout.transform_offset()
	dim.color.a = 0.0
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


# Bixby freezes, cracks open, tears off the floor, swells into the beast and detonates, and the beast drops
# out of the blast and roars. bixby_transform.png carries it; every cue below hangs off one of its frames.
func bixby_transforms() -> void:
	storyboard.hide()
	transform_body.frame = 0
	transform_stage.show()
	var play := create_tween()
	for index in LiamEntranceLayout.TRANSFORM_TIMES.size():
		play.tween_callback(_transform_frame.bind(index))
		play.tween_interval(LiamEntranceLayout.TRANSFORM_TIMES[index])
	await play.finished
	await _beast_lands()
	await _beast_roars()


func _transform_frame(index: int) -> void:
	transform_body.frame = index
	var times := LiamEntranceLayout.TRANSFORM_TIMES
	match index:
		# 0-2: he freezes, and the crowd with him.
		1:
			get_tree().call_group("arena_crowd", "hush")
		# 3-6: the cracks ignite and burn brighter.
		3:
			glow_sfx_player.play()
			_start_aura()
		5:
			_shake(CRACK_SHAKE, times[5])
		6:
			_shake(CRACK_SHAKE, times[6])
			get_tree().call_group("arena_crowd", "cheer", LiamEntranceLayout.transform_time(6, 7))
		# 7-9: he tears off the floor.
		7:
			bixby_shadow.hide()
			_shockwave()
			_shake(LIFT_SHAKE, LiamEntranceLayout.transform_time(7, 8))
		# 10-14: he swells and grows horns while the arena darkens and the view pushes in on him.
		10:
			_dim_to(DIM_DEEPEST, LiamEntranceLayout.transform_time(10, 17))
			_zoom(SWELL_ZOOM, LiamEntranceLayout.transform_time(10, 14))
			_shake(SWELL_SHAKE, times[10])
			get_tree().call_group("arena_crowd", "cheer", LiamEntranceLayout.transform_time(10, 14))
		11, 12, 13, 14:
			_shake(SWELL_SHAKE, times[index])
		# 15-17: the wings tear out and snap open.
		15:
			_shake(WINGS_SHAKE, LiamEntranceLayout.transform_time(15, 16))
		17:
			_shake(WINGS_SNAP_SHAKE, times[17])
			HitStop.freeze(get_tree(), WINGS_SNAP_HIT_STOP)
			get_tree().call_group("arena_crowd", "cheer", times[17])
		# 18-19: it implodes and holds. Nothing shakes here: the stillness sells the blast.
		18:
			get_tree().call_group("arena_crowd", "hush")
			_fade_aura(LiamEntranceLayout.transform_time(18, 19))
			_zoom(1.0, LiamEntranceLayout.transform_time(18, 19))
		# 20: it detonates.
		20:
			blast_sfx_player.play()
			_shockwave()
			_shake(BLAST_SHAKE, BLAST_SHAKE_TIME)
			HitStop.freeze(get_tree(), BLAST_HIT_STOP)
			_zoom(BLAST_ZOOM, BLAST_ZOOM_TIME)
			_flash()
			_fade_throne()
			get_tree().call_group("arena_crowd", "cheer", LiamEntranceLayout.transform_time(20, 25))
		# 21-25: the beast stands there cold, his eyes light, and the arena and the view come back.
		21:
			_dim_to(0.0, LiamEntranceLayout.transform_time(21, 23))
			_zoom(1.0, LiamEntranceLayout.transform_time(21, 22))


# The blast leaves the beast hovering where Bixby stood: he drops out of it and lands hard.
func _beast_lands() -> void:
	transform_stage.hide()
	downstage.hide()
	body.appear(downstage.global_position, BixbyBeastArtLayout.HOVER_HEIGHT * BixbyBeastArtLayout.SCALE)
	body.play_anim(&"land")
	var fall := create_tween()
	fall.tween_method(_fall.bind(body.height), 0.0, 1.0, BixbyBeastArtLayout.time_to_step(&"land", 1))
	await fall.finished
	land_sfx_player.play()
	_shake(LANDING_SHAKE, LANDING_SHAKE_TIME)
	if not body.anim_done:
		await body.anim_finished


func _fall(weight: float, from_height: float) -> void:
	body.height = from_height * (1.0 - weight * weight)
	body.place()


# The roar he lands on, held until the sound has decayed.
func _beast_roars() -> void:
	body.play_anim(&"roar")
	roar_sfx_player.play()
	get_tree().call_group("arena_crowd", "cheer", ROAR_CHEER)
	_shake(ROAR_JOLT_SHAKE, ROAR_JOLT_TIME)
	var shakes := create_tween()
	for cue in ROAR_SHAKES:
		shakes.tween_interval(cue[0])
		shakes.tween_callback(_shake.bind(cue[1], cue[2]))
	await _pause(ROAR_HOLD)
	if not body.anim_done:
		await body.anim_finished


func _shake(strength: float, seconds: float) -> void:
	body.shake_screen(strength, maxi(roundi(seconds / SHAKE_STEP_TIME), 1), SHAKE_STEP_TIME)


func _zoom(to_zoom: float, seconds: float) -> void:
	var focus := transform_stage.global_position - Vector2(0, ZOOM_FOCUS_RISE)
	ScreenView.zoom_to(get_tree(), to_zoom, focus, seconds)


func _dim_to(alpha: float, seconds: float) -> void:
	dim.create_tween().tween_property(dim, "color:a", alpha, seconds)


func _flash() -> void:
	flash.color.a = 1.0
	# In real time, so the detonation's own frame is out from under the white while the hit-stop holds it.
	var fade := flash.create_tween().set_ignore_time_scale(true)
	fade.tween_property(flash, "color:a", 0.0, FLASH_OUT_TIME)


func _fade_throne() -> void:
	var fade := procession.create_tween()
	fade.tween_property(procession, "modulate:a", 0.0, THRONE_FADE_TIME)
	fade.tween_callback(procession.hide)


func _start_aura() -> void:
	transform_aura.frame = 0
	transform_aura.modulate.a = 1.0
	transform_aura.show()
	aura_loop = transform_aura.create_tween().set_loops()
	aura_loop.tween_interval(LiamEntranceLayout.AURA_FRAME_TIME)
	aura_loop.tween_callback(func() -> void:
		transform_aura.frame = (transform_aura.frame + 1) % transform_aura.hframes)


func _fade_aura(seconds: float) -> void:
	var fade := transform_aura.create_tween()
	fade.tween_property(transform_aura, "modulate:a", 0.0, seconds)
	fade.tween_callback(transform_aura.hide)
	fade.tween_callback(aura_loop.kill)


func _shockwave() -> void:
	transform_shockwave.frame = 0
	transform_shockwave.show()
	var wave := transform_shockwave.create_tween()
	for frame in range(1, transform_shockwave.hframes):
		wave.tween_interval(LiamEntranceLayout.SHOCKWAVE_FRAME_TIME)
		wave.tween_callback(func() -> void: transform_shockwave.frame = frame)
	wave.tween_interval(LiamEntranceLayout.SHOCKWAVE_FRAME_TIME)
	wave.tween_callback(transform_shockwave.hide)


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
