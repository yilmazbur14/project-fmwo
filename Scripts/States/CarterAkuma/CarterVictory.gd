extends State

# He beat them:
#   VANISH    he goes, wherever he was standing - the Demon's own dissolve, so this reads as his
#             technique and not as the fight shoving him somewhere.
#   REAPPEAR  he is simply in the middle of the ring. No walk.
#   TURN      he turns his back on them, and the arena goes out around him while he does it. The
#             blackout lands exactly on the ignition, so the last of the world goes as the mark takes.
#   BURN      the emblem, alone and lit, in a black room. He isn't even watching.
#
# THE BELL LANDS ON THE FRAME THE MARK LIGHTS. That is the whole point of the beat and the user's
# specific ask, so the wait for it is read off the animation's own timing rather than written down:
# retiming carter_victory.png retimes the sound with it.
# Terminal. The fight was already decided before this ran - the Demon gave back the lock, the dark,
# the player's draw order and the music level on its way out - so nothing here has to hand anything
# back, and nothing here may take the HUD or the outro's balloon with it. The blackout is world-space
# for exactly that reason.

const CarterArtLayout := preload("res://Scripts/CarterArtLayout.gd")

@export var body : CharacterBody2D

@onready var state_machine = get_parent()

enum Beat { VANISH, REAPPEAR, TURN, BURN }

var beat := Beat.VANISH
# Per-beat, for stepping from one animation to the next.
var clock := 0.0
# From the moment he won, for the blackout, which is longer than any single beat and has to land on
# the ignition rather than near it.
var total := 0.0
var ignited := false
var darkening := false


func Enter() -> void:
	beat = Beat.VANISH
	clock = 0.0
	total = 0.0
	ignited = false
	darkening = false
	body.velocity = Vector2.ZERO
	body.snap_dark_clear()
	body.show_body(true)
	body.show_mark_glow(false)
	body.play_anim(&"ko_vanish")
	get_tree().call_group("arena_crowd", "hush")


func Physics_Update(delta: float) -> void:
	clock += delta
	total += delta
	# Started so that it LANDS on the ignition rather than near it - the arena has to be all the way
	# out on the frame the mark lights. That is earlier than the turn, so it is driven off the total
	# rather than the current beat; the turn alone is shorter than the fade.
	if not darkening and total >= _ignite_at() - CarterArtLayout.KO_BLACKOUT_TIME:
		darkening = true
		body.ko_blackout(CarterArtLayout.KO_BLACKOUT_TIME)
	match beat:
		Beat.VANISH:
			if clock >= _anim_time(&"ko_vanish"):
				_reappear()
		Beat.REAPPEAR:
			if clock >= _anim_time(&"ko_reappear"):
				_turn()
		Beat.TURN:
			if clock >= _anim_time(&"victory"):
				_ignite()
		Beat.BURN:
			pass


# When the mark takes, counted from the moment he won: the teleport out, the teleport in, the turn.
func _ignite_at() -> float:
	return _anim_time(&"ko_vanish") + _anim_time(&"ko_reappear") + _anim_time(&"victory")


# Gone from where he was, and standing in the middle of the ring.
func _reappear() -> void:
	beat = Beat.REAPPEAR
	clock = 0.0
	body.global_position = state_machine.ARENA_CENTRE
	body.play_anim(&"ko_reappear")


func _turn() -> void:
	beat = Beat.TURN
	clock = 0.0
	body.play_anim(&"victory", &"victory_hold")


# The mark takes. The sound is already loaded, so it starts on this frame and not the one after.
func _ignite() -> void:
	beat = Beat.BURN
	ignited = true
	body.ignite_ko_mark()
	body.play_ko_ding()
	# The music gets out of the way of it rather than being stopped, so the ring has room.
	body.duck_music(CarterArtLayout.VICTORY_DUCK_DB, CarterArtLayout.VICTORY_DUCK_TIME)
	body.shake_screen(CarterArtLayout.VICTORY_SHAKE, CarterArtLayout.VICTORY_SHAKE_STEPS,
		CarterArtLayout.VICTORY_SHAKE_STEP_TIME)
	get_tree().call_group("arena_crowd", "cheer", CarterArtLayout.VICTORY_CHEER)


# How long an animation runs. For `victory` that is also where it hands over to `victory_hold`, which
# is the frame the mark snaps to full burn - the sheet's generator calls it IGNITE_MS = 370.
func _anim_time(anim_name: StringName) -> float:
	return CarterArtLayout.time_to_step(anim_name, CarterArtLayout.anim(anim_name).frames.size())
