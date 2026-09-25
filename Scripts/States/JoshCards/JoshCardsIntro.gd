extends State

# Josh's entrance, built entirely from the placeholder kit: a card spins down and plants itself in the
# floor, a fan bursts out of it and snaps upward in a flash, and he is standing there when the light
# clears. Every wait is a node-bound tween, so a freeze holds it. A cut-short entrance never kills one
# something is waiting on: `finished` makes every step bail instead, and a held skip runs the waits
# out on the spot rather than letting them run their time (BossEntrance.run_out).

const BossEntrance := preload("res://Scripts/BossEntrance.gd")
const JoshArtLayout := preload("res://Scripts/JoshArtLayout.gd")
# This fight's place in the order, for the entrance's once-per-run flag.
const FIGHT_SCENE := "res://Scenes/Bosses/JoshBossFightScene.tscn"

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
# Runs from the moment he appears to the start of the frame his entrance pose flicks the card on.
var flick_cue: Tween
# The drawn card burst, and the card he flicks at the camera, while each is up.
var burst: Sprite2D
var flicked: Node2D
# The skip and its hint, up through the entrance and the lines.
var entrance: CanvasLayer
# Enter() is deferred, so anything that can reach in from outside checks this first.
var entered := false
# The entrance is over, one way or another. finish_entrance() is the only thing that sets it.
var finished := false
var dialogue_started := false
# A held skip took everything up to the VS card, and the lines are gone.
var cut := false
# The tweens the entrance is waiting on, for the skip to run out.
var waits: Array[Tween] = []


func Enter() -> void:
	entered = true
	body.height = 0.0
	body.ground_position = body.global_position
	body.place()
	body.hide_glider()
	body.set_air_draw(false)
	body.air.hide()
	body.shadow.hide()
	flash.color.a = 0.0
	# On the retry path too: the entrance is skipped there, but the lines still play and the hold
	# still skips them.
	entrance = BossEntrance.new()
	entrance.name = "BossEntrance"
	add_child(entrance)
	entrance.skipped.connect(_on_skipped)
	entrance.begin()
	if BossEntrance.already_seen(FIGHT_SCENE):
		finish_entrance()
		_start_dialogue()
		return
	_play()


# The fight starts here, and a harness that starts it over the top of the entrance leaves through
# here too, so this is also what guarantees he is standing ready however the entrance ended.
func Exit() -> void:
	_cut_entrance()
	if is_instance_valid(entrance):
		entrance.queue_free()
	entrance = null


func _play() -> void:
	get_tree().call_group("arena_crowd", "hush")
	if JoshArtLayout.USE_FINAL_CARD_BURST:
		await _card_burst()
	else:
		await _plant_card()
		if finished:
			return
		await _fan_out()
		if finished:
			return
		await _he_is_there()
	if finished:
		return
	if flick_cue.is_running():
		await _wait(flick_cue)
	if finished:
		return
	await _flick_at_camera()
	if finished:
		return
	finish_entrance()
	_start_dialogue()


# A card plants itself in the canvas, the deck fans out along the floor and snaps upward, and he is
# standing there as it clears.
func _card_burst() -> void:
	var spec := JoshArtLayout.FINAL_CARD_BURST
	burst = Sprite2D.new()
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
		if finished:
			return
	burst.queue_free()
	burst = null


# A single gold card spins down out of the dark and buries itself upright in the canvas.
func _plant_card() -> void:
	var card := _card(PLANT_SIZE, true)
	card.position = Vector2(0, -PLANT_RISE)
	stage.add_child(card)
	fan.append(card)
	var drop := create_tween()
	drop.tween_method(func(weight: float) -> void:
		card.position = Vector2(0, lerpf(-PLANT_RISE, 0.0, weight * weight)).round()
		card.rotation = TAU * PLANT_SPINS * (1.0 - weight) * (1.0 - weight)
	, 0.0, 1.0, PLANT_TIME)
	await _wait(drop)
	if finished:
		return
	card.rotation = 0.0
	card_sfx_player.play()
	body.shake_screen(PLANT_SHAKE, PLANT_SHAKE_STEPS, PLANT_SHAKE_STEP_TIME)


# The deck bursts out of it in a ring, then snaps up in a column of white.
func _fan_out() -> void:
	var spread := create_tween().set_parallel()
	var count: int = JoshArtLayout.PLACEHOLDER_CARD_BURST.cards
	for i in count:
		var card := _card(JoshArtLayout.PLACEHOLDER_CARD_BURST.size, false)
		card.position = Vector2(0, -PLANT_SIZE.y / 2.0)
		stage.add_child(card)
		fan.append(card)
		var angle := TAU * i / count
		var out := Vector2(cos(angle), sin(angle) * 0.45) * FAN_RADIUS
		spread.tween_method(func(weight: float) -> void:
			card.position = (Vector2(0, -PLANT_SIZE.y / 2.0) + out * weight).round()
			card.rotation = angle + TAU * weight
		, 0.0, 1.0, FAN_TIME)
	await _wait(spread)
	if finished:
		return

	var snap := create_tween().set_parallel()
	for card in fan:
		snap.tween_property(card, "position", card.position - Vector2(0, SNAP_RISE), SNAP_TIME)
	snap.tween_property(flash, "color:a", 1.0, SNAP_TIME * 0.5)
	await _wait(snap)
	if finished:
		return
	_clear_fan()


# His entrance pose, which ends on the card he flicks buried in the floor.
func _appear() -> void:
	body.air.show()
	body.shadow.show()
	body.face_player()
	body.play_anim(&"intro")
	flick_cue = create_tween()
	flick_cue.tween_interval(_flick_time())
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
	await _wait(rain)
	if finished:
		return
	land_sfx_player.play()
	await _pause(BEAT_AFTER_RAIN)


# One last card flicked straight at the camera, on the entrance's own flick frame and out the side he
# faces.
func _flick_at_camera() -> void:
	card_sfx_player.play()
	var card := _card(JoshArtLayout.PLACEHOLDER_THROWN_CARD.size, false)
	card.position = Vector2(0, -180)
	stage.add_child(card)
	flicked = card
	var side := -1.0 if body.sprite.flip_h else 1.0
	var fly := create_tween()
	fly.tween_method(func(weight: float) -> void:
		card.position = Vector2(lerpf(0.0, FLICK_TRAVEL * side, weight), -180.0 + 120.0 * weight).round()
		card.rotation = TAU * 4.0 * weight * side
		card.scale = Vector2.ONE * lerpf(1.0, FLICK_GROW, weight)
	, 0.0, 1.0, FLICK_TIME)
	fly.parallel().tween_property(flash, "color:a", FLICK_FLASH, FLICK_TIME)
	await _wait(fly)
	if finished:
		return
	card.queue_free()
	flicked = null
	var fade := flash.create_tween()
	fade.tween_property(flash, "color:a", 0.0, FLASH_OUT_TIME)
	await _pause(BEAT_AFTER_FLICK)
	if finished:
		return
	body.play_anim(&"idle")


#ENDING IT

# The one way the entrance ends: its last beat, a skip, or the fight starting over the top of it.
# Idempotent - it leaves him exactly as the fight expects him whichever of those got here.
func finish_entrance() -> void:
	if finished or not entered:
		return
	finished = true
	body.air.show()
	body.shadow.show()
	body.face_player()
	if body.current_anim != &"idle":
		body.play_anim(&"idle")
	flash.color.a = 0.0
	if is_instance_valid(entrance):
		entrance.release_player()
	BossEntrance.mark_seen(FIGHT_SCENE)


# The entrance cut on the spot and the lines started: where a second go at the fight starts on its
# own. Public, so the defence suite can cut the entrance this way - its modes are about the fight,
# and read the lines or throw them away themselves.
func skip() -> void:
	if finished or cut:
		return
	_cut_entrance()
	BossEntrance.settle_arena(get_tree())
	_start_dialogue()


# What a held ui_cancel does: the entrance, whatever is left of the lines and the card's build-up,
# all at once, landing on the card's flash. His lines call no beats, so the entrance's end is all
# there is to leave.
func skip_to_fight() -> void:
	if not entered or cut:
		return
	cut = true
	BossEntrance.close_balloon(state_machine.pre_fight_balloon)
	_cut_entrance()
	state_machine.end_pre_fight_dialogue()
	BossEntrance.settle_arena(get_tree())
	BossEntrance.card_to_flash(get_tree())


func _on_skipped() -> void:
	skip_to_fight()


# The lines have handed over to the VS card, and the skip goes with them.
func lines_over() -> void:
	if is_instance_valid(entrance):
		entrance.end()


# The entrance's end, with its waits run out and none of its cards left up. The flash is cleared
# after the run-out, which drives it wherever the cut-short step was taking it.
func _cut_entrance() -> void:
	finish_entrance()
	BossEntrance.run_out(waits)
	if is_instance_valid(burst):
		burst.queue_free()
	burst = null
	if is_instance_valid(flicked):
		flicked.queue_free()
	flicked = null
	_clear_fan()
	flash.color.a = 0.0


func _start_dialogue() -> void:
	if dialogue_started or cut:
		return
	dialogue_started = true
	state_machine.show_pre_fight_dialogue()


# The placeholder entrance is one frame, so the flick comes on whatever step it has.
func _flick_time() -> float:
	var frames: Array = JoshArtLayout.anim(&"intro").frames
	return JoshArtLayout.time_to_step(&"intro", mini(JoshArtLayout.INTRO_FLICK_STEP, frames.size() - 1))


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
		if is_instance_valid(card):
			card.queue_free()
	fan.clear()


func _pause(seconds: float) -> void:
	var tween := create_tween()
	tween.tween_interval(seconds)
	await _wait(tween)


func _wait(tween: Tween) -> void:
	waits.append(tween)
	await tween.finished
	waits.erase(tween)
