extends State

# Josh's entrance, built entirely from the placeholder kit: a card spins down and plants itself in the
# floor, a fan bursts out of it and snaps upward in a flash, and he is standing there when the light
# clears. Every wait is a node-bound tween, so a freeze holds it.

const JoshArtLayout := preload("res://Scripts/JoshArtLayout.gd")

@export var body : CharacterBody2D
@export var stage : Node2D
@export var flash : ColorRect
@export var card_sfx_player : AudioStreamPlayer
@export var land_sfx_player : AudioStreamPlayer

@onready var state_machine = get_parent()

#THE PLANTED CARD
const PLANT_RISE := 1300.0
const PLANT_TIME := 0.8
const PLANT_SPINS := 3.0
const PLANT_SHAKE := 7.0
const PLANT_SHAKE_STEPS := 4
const PLANT_SHAKE_STEP_TIME := 0.03
const PLANT_SIZE := Vector2(96, 132)

#THE FAN
const FAN_TIME := 0.5
const FAN_RADIUS := 300.0
const SNAP_TIME := 0.2
const SNAP_RISE := 620.0
const FLASH_OUT_TIME := 0.2

#HIM
const APPEAR_CHEER := 1.5
const RAIN_CARDS := 9
const RAIN_RISE := 700.0
const RAIN_SPREAD := Vector2(280, 90)
const RAIN_TIME := 0.7
const BEAT_AFTER_RAIN := 0.25

#THE FLICK AT THE CAMERA
const FLICK_TIME := 0.35
const FLICK_TRAVEL := 1500.0
const FLICK_GROW := 3.2
const FLICK_FLASH := 0.5
const BEAT_AFTER_FLICK := 0.55

var fan: Array[Node2D] = []


func Enter() -> void:
	body.height = 0.0
	body.ground_position = body.global_position
	body.place()
	body.hide_glider()
	body.set_air_draw(false)
	body.air.hide()
	body.shadow.hide()
	flash.color.a = 0.0
	_play()


func _play() -> void:
	get_tree().call_group("arena_crowd", "hush")
	if JoshArtLayout.USE_FINAL_CARD_BURST:
		await _card_burst()
	else:
		await _plant_card()
		await _fan_out()
		await _he_is_there()
	await _flick_at_camera()
	state_machine.show_pre_fight_dialogue()


# A card plants itself in the canvas, the deck fans out along the floor and snaps upward, and he is
# standing there as it clears.
func _card_burst() -> void:
	var spec := JoshArtLayout.FINAL_CARD_BURST
	var burst := Sprite2D.new()
	burst.texture = load(spec.texture)
	burst.hframes = spec.hframes
	burst.scale = Vector2.ONE * spec.scale
	burst.offset = spec.frame_size / 2.0 - spec.pivot
	stage.add_child(burst)
	card_sfx_player.play()
	body.shake_screen(PLANT_SHAKE, PLANT_SHAKE_STEPS, PLANT_SHAKE_STEP_TIME)

	var times: Array = spec.frame_times
	for i in spec.hframes:
		burst.frame = i
		if i == spec.appear_frame:
			_appear()
		await _pause(times[i])
	burst.queue_free()
	await _pause(BEAT_AFTER_RAIN)


# A single gold card spins down out of the dark and buries itself upright in the canvas.
func _plant_card() -> void:
	var card := _card(PLANT_SIZE, true)
	card.position = Vector2(0, -PLANT_RISE)
	stage.add_child(card)
	var drop := create_tween()
	drop.tween_method(func(weight: float) -> void:
		card.position = Vector2(0, lerpf(-PLANT_RISE, 0.0, weight * weight)).round()
		card.rotation = TAU * PLANT_SPINS * (1.0 - weight) * (1.0 - weight)
	, 0.0, 1.0, PLANT_TIME)
	await drop.finished
	card.rotation = 0.0
	card_sfx_player.play()
	body.shake_screen(PLANT_SHAKE, PLANT_SHAKE_STEPS, PLANT_SHAKE_STEP_TIME)
	fan.append(card)


# The deck bursts out of it in a ring, then snaps up in a column of white.
func _fan_out() -> void:
	var burst := create_tween().set_parallel()
	var count: int = JoshArtLayout.PLACEHOLDER_CARD_BURST.cards
	for i in count:
		var card := _card(JoshArtLayout.PLACEHOLDER_CARD_BURST.size, false)
		card.position = Vector2(0, -PLANT_SIZE.y / 2.0)
		stage.add_child(card)
		fan.append(card)
		var angle := TAU * i / count
		var out := Vector2(cos(angle), sin(angle) * 0.45) * FAN_RADIUS
		burst.tween_method(func(weight: float) -> void:
			card.position = (Vector2(0, -PLANT_SIZE.y / 2.0) + out * weight).round()
			card.rotation = angle + TAU * weight
		, 0.0, 1.0, FAN_TIME)
	await burst.finished

	var snap := create_tween().set_parallel()
	for card in fan:
		snap.tween_property(card, "position", card.position - Vector2(0, SNAP_RISE), SNAP_TIME)
	snap.tween_property(flash, "color:a", 1.0, SNAP_TIME * 0.5)
	await snap.finished
	_clear_fan()


# His entrance pose, which ends on the card he flicks buried in the floor.
func _appear() -> void:
	body.air.show()
	body.shadow.show()
	body.play_anim(&"intro")
	get_tree().call_group("arena_crowd", "cheer", APPEAR_CHEER)
	var fade := flash.create_tween()
	fade.tween_property(flash, "color:a", 0.0, FLASH_OUT_TIME)


# He is standing in the middle of it when the light goes, with the deck still coming down.
func _he_is_there() -> void:
	_appear()

	var rain := create_tween().set_parallel()
	for i in RAIN_CARDS:
		var card := _card(JoshArtLayout.PLACEHOLDER_CARD_BURST.size, false)
		var rest := Vector2(randf_range(-RAIN_SPREAD.x, RAIN_SPREAD.x), randf_range(0.0, RAIN_SPREAD.y))
		card.position = rest - Vector2(0, RAIN_RISE)
		card.rotation = randf_range(-PI, PI)
		stage.add_child(card)
		fan.append(card)
		var turn := card.rotation
		var from := card.position
		rain.tween_method(func(weight: float) -> void:
			card.position = from.lerp(rest, weight * weight).round()
			card.rotation = turn * (1.0 - weight * 0.6)
		, 0.0, 1.0, RAIN_TIME).set_delay(i * 0.05)
	await rain.finished
	land_sfx_player.play()
	await _pause(BEAT_AFTER_RAIN)


# One last card flicked straight at the camera, on the entrance's own flick frames.
func _flick_at_camera() -> void:
	card_sfx_player.play()
	var card := _card(JoshArtLayout.PLACEHOLDER_THROWN_CARD.size, false)
	card.position = Vector2(0, -180)
	stage.add_child(card)
	var fly := create_tween()
	fly.tween_method(func(weight: float) -> void:
		card.position = Vector2(lerpf(0.0, FLICK_TRAVEL, weight), -180.0 + 120.0 * weight).round()
		card.rotation = TAU * 4.0 * weight
		card.scale = Vector2.ONE * lerpf(1.0, FLICK_GROW, weight)
	, 0.0, 1.0, FLICK_TIME)
	fly.parallel().tween_property(flash, "color:a", FLICK_FLASH, FLICK_TIME)
	await fly.finished
	card.queue_free()
	var fade := flash.create_tween()
	fade.tween_property(flash, "color:a", 0.0, FLASH_OUT_TIME)
	await _pause(BEAT_AFTER_FLICK)
	body.play_anim(&"idle")


func _card(size: Vector2, upright: bool) -> Node2D:
	if JoshArtLayout.USE_FINAL_THROWN_CARD:
		return _drawn_card(size)

	var card := Node2D.new()
	var face := Polygon2D.new()
	var shape := JoshArtLayout.centred_rect(size)
	if upright:
		# Planted: it stands on its own point, so it sinks into the floor where it lands.
		for i in shape.size():
			shape[i] += Vector2(0, -size.y / 2.0)
	face.polygon = shape
	face.color = JoshArtLayout.PLACEHOLDER_CARD_BURST.color
	card.add_child(face)
	var rim := Line2D.new()
	rim.points = shape
	rim.closed = true
	rim.width = JoshArtLayout.PLACEHOLDER_CARD_BURST.edge_width
	rim.default_color = JoshArtLayout.PLACEHOLDER_CARD_BURST.edge_color
	card.add_child(rim)
	return card


# A real card, from the thrown card's sheet, sized to stand in for the fan and the rain.
func _drawn_card(size: Vector2) -> Node2D:
	var spec := JoshArtLayout.FINAL_THROWN_CARD
	var card := Node2D.new()
	var face := Sprite2D.new()
	face.texture = load(spec.texture)
	face.hframes = spec.hframes
	face.offset = spec.frame_size / 2.0 - spec.pivot
	face.scale = Vector2.ONE * (size.y / spec.frame_size.y)
	card.add_child(face)
	return card


func _clear_fan() -> void:
	for card in fan:
		card.queue_free()
	fan.clear()


func _pause(seconds: float) -> void:
	var tween := create_tween()
	tween.tween_interval(seconds)
	await tween.finished
