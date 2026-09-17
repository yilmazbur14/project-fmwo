extends State

const BixbyBeastArtLayout := preload("res://Scripts/BixbyBeastArtLayout.gd")

@export var body : CharacterBody2D
@export var normal_bixby : Sprite2D
@export var liam : Sprite2D

# Placeholder defeat, until bixby_beast_defeat.png: he buckles, bursts back into normal Bixby, and Bixby
# coughs Liam up to land beside him. It's over before the outro's first line, 0.7 s after the win.
const CRASH_TIME := 0.2
const CRASH_FLASH := Color(4, 4, 4)
const CRASH_SCREEN_SHAKE := 14.0
const CRASH_SPRITE_SHAKE := 9.0
const CRASH_SHAKE_STEPS := 6
const REVERT_FADE_TIME := 0.3
const REVERT_CHEER := 2.0
# Normal Bixby's middle mouth on bixby.png, in px from his feet.
const BIXBY_MOUTH := Vector2(0, -132)
const COUGH_UP_TIME := 0.36
const COUGH_UP_HEIGHT := 150.0
# Liam lands this far to Bixby's side, toward the middle of the arena.
const COUGH_UP_DISTANCE := 150.0
const COUGH_UP_START_SCALE := 1.0
const LANDING_BOUNCE_PX := 9.0
const LANDING_BOUNCE_TIME := 0.06
const SPRITE_SCALE := 3.0


func Enter() -> void:
	body.fly_velocity = Vector2.ZERO
	if BixbyBeastArtLayout.uses_final(&"defeat"):
		body.play_anim(&"defeat")
	else:
		_placeholder_defeat()


func _placeholder_defeat() -> void:
	body.play_anim(&"hit")
	body.shake_screen(CRASH_SCREEN_SHAKE, CRASH_SHAKE_STEPS, CRASH_TIME / CRASH_SHAKE_STEPS)
	body.shake_sprite(CRASH_SPRITE_SHAKE, CRASH_SHAKE_STEPS, CRASH_TIME / CRASH_SHAKE_STEPS)
	var crash := create_tween()
	crash.tween_property(body.sprite, "modulate", CRASH_FLASH, CRASH_TIME)
	await crash.finished

	body.air.hide()
	body.shadow.hide()
	normal_bixby.show()
	normal_bixby.modulate = CRASH_FLASH
	create_tween().tween_property(normal_bixby, "modulate", Color.WHITE, REVERT_FADE_TIME)
	get_tree().call_group("arena_crowd", "cheer", REVERT_CHEER)

	var side := 1.0 if body.global_position.x < 960.0 else -1.0
	var landing := Vector2(side * COUGH_UP_DISTANCE, 0)
	liam.position = BIXBY_MOUTH
	liam.scale = Vector2.ONE * COUGH_UP_START_SCALE
	liam.show()
	var cough := create_tween()
	cough.tween_method(_arc_liam.bind(BIXBY_MOUTH, landing), 0.0, 1.0, COUGH_UP_TIME)
	cough.tween_callback(func() -> void: liam.position = landing - Vector2(0, LANDING_BOUNCE_PX))
	cough.tween_interval(LANDING_BOUNCE_TIME)
	cough.tween_callback(func() -> void: liam.position = landing)


func _arc_liam(weight: float, from: Vector2, to: Vector2) -> void:
	var rise := COUGH_UP_HEIGHT * 4.0 * weight * (1.0 - weight)
	liam.position = (from.lerp(to, weight) - Vector2(0, rise)).round()
	liam.scale = Vector2.ONE * lerpf(COUGH_UP_START_SCALE, SPRITE_SCALE, weight)
