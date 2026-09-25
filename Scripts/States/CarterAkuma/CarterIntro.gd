extends State

# Carter's entrance, on the approved 17-frame sheet: he walks on, plants his foot and the mark on his
# back catches. The ground ring and the mark's glare land on the stomp, and the sheet's last two
# frames are pixel-identical to the approved standing and signature poses, so it cuts straight into
# idle with nothing to hide the seam.
# Every wait is a node-bound tween, so a freeze holds it. A cut-short entrance never kills one
# something is waiting on: `finished` makes the walk-on bail instead, and a held skip runs the waits
# out on the spot rather than letting them run their time (BossEntrance.run_out).

const BossEntrance := preload("res://Scripts/BossEntrance.gd")
const CarterArtLayout := preload("res://Scripts/CarterArtLayout.gd")
# This fight's place in the order, for the entrance's once-per-run flag.
const FIGHT_SCENE := "res://Scenes/Bosses/CarterBossFightScene.tscn"

@export var body : CharacterBody2D
@export var flash : ColorRect
@export var land_sfx_player : AudioStreamPlayer

@onready var state_machine = get_parent()

const HUSH_CHEER := 1.6
const FLASH_PEAK := 0.55
const FLASH_OUT_TIME := 0.28
const STOMP_SHAKE := 9.0
const STOMP_SHAKE_STEPS := 4
const STOMP_SHAKE_STEP_TIME := 0.03
const BEAT_AFTER := 0.4

# The skip and its hint, up through the walk-on and the lines.
var entrance: CanvasLayer
# Enter() is deferred, so anything that can reach in from outside checks this first.
var entered := false
# The walk-on is over, one way or another. finish_entrance() is the only thing that sets it.
var finished := false
var dialogue_started := false
# A held skip took everything up to the VS card, and the lines are gone.
var cut := false
# The tweens the walk-on is waiting on, for the skip to run out.
var waits: Array[Tween] = []
# The ring of light the stomp leaves on the floor, while it fades.
var ring: Sprite2D


func Enter() -> void:
	entered = true
	flash.color.a = 0.0
	body.show_body(true)
	body.show_mark_glow(false)
	# On the retry path too: the walk-on is skipped there, but the lines still play and the hold
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
	_cut_walk_on()
	if is_instance_valid(entrance):
		entrance.queue_free()
	entrance = null


func _play() -> void:
	get_tree().call_group("arena_crowd", "hush")
	body.play_anim(&"intro")
	await _pause(_stomp_time())
	if finished:
		return
	_stomp()
	await _pause(maxf(_intro_time() - _stomp_time(), 0.0))
	if finished:
		return
	body.show_mark_glow(false)
	body.play_anim(&"idle")
	await _pause(BEAT_AFTER)
	if finished:
		return
	finish_entrance()
	_start_dialogue()


# The mark catches: a ring of light on the floor he stands on, his own mark glaring, and the room
# jolting with it.
func _stomp() -> void:
	land_sfx_player.play()
	body.shake_screen(STOMP_SHAKE, STOMP_SHAKE_STEPS, STOMP_SHAKE_STEP_TIME)
	body.show_mark_glow(true)
	get_tree().call_group("arena_crowd", "cheer", HUSH_CHEER)
	_ground_ring()
	flash.color.a = FLASH_PEAK
	var fade := flash.create_tween()
	fade.tween_property(flash, "color:a", 0.0, FLASH_OUT_TIME)


func _ground_ring() -> void:
	if not CarterArtLayout.USE_FINAL_INTRO_FLASH:
		return
	var spec := CarterArtLayout.FINAL_INTRO_FLASH
	ring = Sprite2D.new()
	ring.texture = load(spec.texture)
	ring.scale = Vector2.ONE * spec.scale
	ring.offset = spec.frame_size / 2.0 - spec.pivot
	ring.material = CarterArtLayout.additive()
	body.floor_layer.add_child(ring)
	ring.global_position = body.global_position
	var fade := ring.create_tween()
	fade.tween_property(ring, "modulate:a", 0.0, spec.time)
	fade.tween_callback(ring.queue_free)


#ENDING IT

# The one way the walk-on ends: its last beat, a skip, or the fight starting over the top of it.
# Idempotent - it leaves him exactly as the fight expects him whichever of those got here.
func finish_entrance() -> void:
	if finished or not entered:
		return
	finished = true
	body.show_body(true)
	body.show_mark_glow(false)
	if body.current_anim != &"idle":
		body.play_anim(&"idle")
	if is_instance_valid(entrance):
		entrance.release_player()
	BossEntrance.mark_seen(FIGHT_SCENE)


# The walk-on cut on the spot and the lines started: where a second go at the fight starts on its
# own. Public, so the defence suite can cut the entrance this way - its modes are about the fight,
# and read the lines or throw them away themselves.
func skip() -> void:
	if finished or cut:
		return
	_cut_walk_on()
	BossEntrance.settle_arena(get_tree())
	_start_dialogue()


# What a held ui_cancel does: the walk-on, whatever is left of the lines and the card's build-up, all
# at once, landing on the card's flash. His lines call no beats, so the walk-on's end is all there is
# to leave.
func skip_to_fight() -> void:
	if not entered or cut:
		return
	cut = true
	BossEntrance.close_balloon(state_machine.pre_fight_balloon)
	_cut_walk_on()
	state_machine.end_pre_fight_dialogue()
	BossEntrance.settle_arena(get_tree())
	BossEntrance.card_to_flash(get_tree())


func _on_skipped() -> void:
	skip_to_fight()


# The lines have handed over to the VS card, and the skip goes with them.
func lines_over() -> void:
	if is_instance_valid(entrance):
		entrance.end()


# The walk-on's end, with its waits run out and nothing of the stomp left on screen.
func _cut_walk_on() -> void:
	finish_entrance()
	BossEntrance.run_out(waits)
	if is_instance_valid(ring):
		ring.queue_free()
	ring = null
	flash.color.a = 0.0


func _start_dialogue() -> void:
	if dialogue_started or cut:
		return
	dialogue_started = true
	state_machine.show_pre_fight_dialogue()


# The placeholder entrance is one frame, so the stomp lands on whatever step it has.
func _stomp_time() -> float:
	var frames: Array = CarterArtLayout.anim(&"intro").frames
	return CarterArtLayout.time_to_step(&"intro", mini(CarterArtLayout.INTRO_FLASH_STEP, frames.size() - 1))


func _intro_time() -> float:
	return CarterArtLayout.time_to_step(&"intro", CarterArtLayout.anim(&"intro").frames.size())


func _pause(seconds: float) -> void:
	var tween := create_tween()
	tween.tween_interval(seconds)
	await _wait(tween)


func _wait(tween: Tween) -> void:
	waits.append(tween)
	await tween.finished
	waits.erase(tween)
