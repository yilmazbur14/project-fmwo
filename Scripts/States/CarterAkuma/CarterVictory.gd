extends State

# He beat them. The mirror of his entrance: he turns his back, settles, and the emblem between his
# shoulders takes and burns, and he stands there like that while the defeat screen fades over him.
# He isn't even watching.
# The bell lands on the exact frame the mark lights, which is the whole point of the beat - the wait
# for it is a Physics_Update accumulator off the animation's own timing, not a guess, so retiming the
# sheet retimes the sound with it.
# Terminal: the fight is already decided by the time this runs, so nothing here has to hand anything
# back. The Demon released the player, the dark and the music before the transition got here.

const CarterArtLayout := preload("res://Scripts/CarterArtLayout.gd")

@export var body : CharacterBody2D

@onready var state_machine = get_parent()

var clock := 0.0
var ignited := false


func Enter() -> void:
	clock = 0.0
	ignited = false
	body.velocity = Vector2.ZERO
	# Belt and braces: whatever killed them, the arena comes back up and he is drawn.
	body.snap_dark_clear()
	body.show_body(true)
	body.show_mark_glow(false)
	body.play_anim(&"victory", &"victory_hold")
	get_tree().call_group("arena_crowd", "hush")


func Physics_Update(delta: float) -> void:
	if ignited:
		return
	clock += delta
	if clock >= _ignite_time():
		ignited = true
		_ignite()


# The mark takes. The sound is already loaded, so it starts on this frame and not the one after.
func _ignite() -> void:
	body.show_mark_glow(true)
	body.play_ko_ding()
	# The music gets out of the way of it rather than being stopped, so the ring has room.
	body.duck_music(CarterArtLayout.VICTORY_DUCK_DB, CarterArtLayout.VICTORY_DUCK_TIME)
	body.shake_screen(CarterArtLayout.VICTORY_SHAKE, CarterArtLayout.VICTORY_SHAKE_STEPS,
		CarterArtLayout.VICTORY_SHAKE_STEP_TIME)
	get_tree().call_group("arena_crowd", "cheer", CarterArtLayout.VICTORY_CHEER)
	var flash: ColorRect = body.flash
	flash.color.a = CarterArtLayout.VICTORY_FLASH
	var fade: Tween = flash.create_tween()
	fade.tween_property(flash, "color:a", 0.0, CarterArtLayout.VICTORY_FLASH_OUT)


# Where `victory` hands over to `victory_hold`, which is the frame the mark snaps to full burn. The
# sheet's generator calls it IGNITE_MS = 370 and the four frames before it sum to exactly that, so
# this is read off the animation rather than written down twice.
func _ignite_time() -> float:
	return CarterArtLayout.time_to_step(&"victory", CarterArtLayout.anim(&"victory").frames.size())
