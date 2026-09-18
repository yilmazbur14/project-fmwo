extends State

# Carter's entrance, on the approved 17-frame sheet: he walks on, plants his foot and the mark on his
# back catches. The ground ring and the mark's glare land on the stomp, and the sheet's last two
# frames are pixel-identical to the approved standing and signature poses, so it cuts straight into
# idle with nothing to hide the seam.
# Every wait is a node-bound tween, so a freeze holds it.

const CarterArtLayout := preload("res://Scripts/CarterArtLayout.gd")

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


func Enter() -> void:
	flash.color.a = 0.0
	body.show_body(true)
	body.show_mark_glow(false)
	_play()


func _play() -> void:
	get_tree().call_group("arena_crowd", "hush")
	body.play_anim(&"intro")
	await _pause(_stomp_time())
	_stomp()
	await _pause(maxf(_intro_time() - _stomp_time(), 0.0))
	body.show_mark_glow(false)
	body.play_anim(&"idle")
	await _pause(BEAT_AFTER)
	state_machine.show_pre_fight_dialogue()


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
	var ring := Sprite2D.new()
	ring.texture = load(spec.texture)
	ring.scale = Vector2.ONE * spec.scale
	ring.offset = spec.frame_size / 2.0 - spec.pivot
	ring.material = CarterArtLayout.additive()
	body.floor_layer.add_child(ring)
	ring.global_position = body.global_position
	var fade := ring.create_tween()
	fade.tween_property(ring, "modulate:a", 0.0, spec.time)
	fade.tween_callback(ring.queue_free)


# The placeholder entrance is one frame, so the stomp lands on whatever step it has.
func _stomp_time() -> float:
	var frames: Array = CarterArtLayout.anim(&"intro").frames
	return CarterArtLayout.time_to_step(&"intro", mini(CarterArtLayout.INTRO_FLASH_STEP, frames.size() - 1))


func _intro_time() -> float:
	return CarterArtLayout.time_to_step(&"intro", CarterArtLayout.anim(&"intro").frames.size())


func _pause(seconds: float) -> void:
	var tween := create_tween()
	tween.tween_interval(seconds)
	await tween.finished
