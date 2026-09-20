extends State

# He beat them, and he beat them in the dark - only the clones can hurt the player - so the lights
# never come back up:
#   VANISH    he goes, wherever he was standing - the Demon's own dissolve, lifted over the barrage's
#             darkness so it reads in it.
#   REAPPEAR  he is simply in the middle of the ring. No walk.
#   TURN      he turns his back on them, and the rest goes to full black around him: what the barrage
#             darkness still let through, the fallen player's pool, and him. The blackout lands
#             exactly on the ignition, so the last of the world goes as the mark takes.
#   BURN      the emblem, alone and lit, in a black room, for KO_HOLD_TIME. He isn't even watching.
#   LIGHT     the Demon's spotlight comes back up on him, and his whole body with it; the arena stays
#             gone around him.
#   LOOK      his head comes round over his shoulder to stare at them, back still turned, and he holds
#             that while the outro plays.
#
# THE BELL LANDS ON THE FRAME THE MARK LIGHTS. That is the whole point of the beat and the user's
# specific ask, so the wait for it is read off the animation's own timing rather than written down:
# retiming carter_victory.png retimes the sound with it. Nothing after it touches audio, so the ring
# runs out on its own.
# Terminal. The fight was already decided before this ran. The Demon gave back the lock on its way
# out but handed on its darkness, the fallen player's draw order and the ducked music, which this
# takes to full black and silence and never gives back - the fight scene goes away after it. Nothing
# here may take the HUD or the outro's balloon with it; the blackout is world-space for exactly that.

const CarterArtLayout := preload("res://Scripts/CarterArtLayout.gd")

@export var body : CharacterBody2D

@onready var state_machine = get_parent()

enum Beat { VANISH, REAPPEAR, TURN, BURN, LIGHT, LOOK }

var beat := Beat.VANISH
# Per-beat, for stepping from one animation to the next.
var clock := 0.0
# From the moment he won, for the blackout, which is longer than any single beat and has to land on
# the ignition rather than near it.
var total := 0.0
var ignited := false
var darkening := false
var lit := false
var looked := false


func Enter() -> void:
	beat = Beat.VANISH
	clock = 0.0
	total = 0.0
	ignited = false
	darkening = false
	lit = false
	looked = false
	body.velocity = Vector2.ZERO
	# The dark is NOT cleared: the barrage handed it straight on (RagingDemon.release), and the lights
	# never come back up between the kill and the ignition. He is lifted over it for the teleport.
	body.lift_for_teleport()
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
			if clock >= CarterArtLayout.KO_HOLD_TIME:
				_light_up()
		Beat.LIGHT:
			if clock >= CarterArtLayout.KO_LIGHT_TIME + CarterArtLayout.KO_LOOK_DELAY:
				_look_back()
		Beat.LOOK:
			pass


# When the mark takes, counted from the moment he won: the teleport out, the teleport in, the turn.
func _ignite_at() -> float:
	return _anim_time(&"ko_vanish") + _anim_time(&"ko_reappear") + _anim_time(&"victory")


# The whole pose, from the moment he won to his head having come all the way round: the ignition, the
# emblem burning alone, the light coming up, the breath before the look, and the look itself. Summed
# from the same numbers that drive the beat, so retiming any of them - or the look-back sheet landing
# with its own length - moves this with it. His outro line waits for it (CarterAkumaScript).
func pose_length() -> float:
	return (_ignite_at() + CarterArtLayout.KO_HOLD_TIME + CarterArtLayout.KO_LIGHT_TIME
		+ CarterArtLayout.KO_LOOK_DELAY + _anim_time(&"look_back"))


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
	clock = 0.0
	ignited = true
	body.ignite_ko_mark()
	body.play_ko_ding()
	# The track bows out entirely rather than ducking: the arena is black, the bell is the only thing
	# left, and his outro lines land in the quiet after it.
	body.fade_music_out(CarterArtLayout.VICTORY_MUSIC_FADE)
	body.shake_screen(CarterArtLayout.VICTORY_SHAKE, CarterArtLayout.VICTORY_SHAKE_STEPS,
		CarterArtLayout.VICTORY_SHAKE_STEP_TIME)
	get_tree().call_group("arena_crowd", "cheer", CarterArtLayout.VICTORY_CHEER)


# The spotlight comes back up on him, and the whole of him with it for the first time since the arena
# went out. He moves onto the look-back sheet here rather than when his head starts to turn: the burn
# frames paint the emblem white-hot and this sheet paints it crisp, and the light coming up is what
# hides the swap.
func _light_up() -> void:
	beat = Beat.LIGHT
	clock = 0.0
	lit = true
	body.play_anim(&"look_back_ready")
	body.ko_light_up(CarterArtLayout.KO_LIGHT_TIME)


# His head comes round over his shoulder to stare at them.
func _look_back() -> void:
	beat = Beat.LOOK
	clock = 0.0
	looked = true
	body.play_anim(&"look_back", &"look_back_hold")


# How long an animation runs. For `victory` that is also where it hands over to `victory_hold`, which
# is the frame the mark snaps to full burn - the sheet's generator calls it IGNITE_MS = 370.
func _anim_time(anim_name: StringName) -> float:
	return CarterArtLayout.time_to_step(anim_name, CarterArtLayout.anim(anim_name).frames.size())
