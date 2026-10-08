extends State

# Danny on his back (Addendum 1, section A.5), knocked silly: the parried fifth slam bounced him off the player's
# fists onto it (DannyBossSlams), or his belly bump slipped on his own worms (DannyBossBellyBump). It is the
# string's payoff: a window with no nap and no regen, sooner than the nap and with nothing healed.
# DannyBossStateMachine.enter_on_back() sets the window, its cap, whether it pays the finisher and what put him
# there, then enters it; a bare transition opens the parried slam's.
#   LAND    land_time: back_land, a shake, the bounce's thud and the dust either side of him.
#   WINDOW  the daze loop with stars (or his nap's Z's: Layout.BACK_DAZE_MARK), his lying box punchable: hit_cap
#           punches, each a flinch, and while `dazeable`
#           a charged third dazes him for the single-bar finisher, whose uppercut rolls him up at once
#           (DannyBossScript.end_recovery, DannyBossStateMachine.roll_up_then_start_cycle).
#   ROLL    roll_time: back_roll up onto his feet, the hurtbox off, then Idle and his next attack in order.
# No regen and no music duck: this isn't his nap. The one exception is the user's open question 1: with
# nap_after_slam on, a parried slam's window ends in his nap instead of the roll.

const Layout := preload("res://Scripts/DannyBossArtLayout.gd")
const FinisherArtLayout := preload("res://Scripts/FinisherArtLayout.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")

enum Beat { LAND, WINDOW, ROLL }

const SHAKE_STEPS := 4
const SHAKE_STEP := 0.04
# The finisher's effects layer: the stars draw over both fighters.
const STARS_Z_INDEX := 2
# Where the landing's dust puffs go, from his feet, either side: the edges of his lying box.
const DUST_ROW := &"danny_row"

@export var body : CharacterBody2D

#KNOBS (seconds and px)
@export var land_time := 0.15
@export var roll_time := 0.45
@export var land_shake := 8.0
# What a bare transition opens: the parried slam's.
@export var default_window := 3.0
@export var default_cap := 6
# The user's open question 1, off by default: the nap still follows a parried slam's window.
@export var nap_after_slam := false

@onready var state_machine = get_parent()

# Set by enter_on_back() just before the transition; `window` is used once.
var window := 0.0
var hit_cap := 6
var dazeable := true
var from := &""

# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
var beat := Beat.LAND
var beat_left := 0.0
var stars: Sprite2D
var stars_clock := 0.0
var stars_shown := true
var dust: Array[Sprite2D] = []
var dust_clock := 0.0
# For tests: the window this entry opened, the fight_clock at Enter, as the window opened and as he left, and the
# punches that landed in it.
var open_for := 0.0
var entered_at := -1.0
var window_at := -1.0
var left_at := -1.0
var hits := 0


func Enter() -> void:
	released = false
	if window > 0.0:
		open_for = window
	else:
		open_for = default_window
		hit_cap = default_cap
		dazeable = true
		from = &""
	window = 0.0
	entered_at = body.fight_clock
	window_at = -1.0
	left_at = -1.0
	hits = 0
	stars_shown = true
	body.velocity = Vector2.ZERO
	body.set_lift(0.0)
	body.set_hurtbox_active(false)
	body.set_body_box(&"back")
	body.state_anim = &"back_land"
	body.play_anim(&"back_land")
	body.play_sfx(&"back_bounce")
	ScreenView.shake(get_tree(), land_shake, SHAKE_STEPS, SHAKE_STEP)
	_puff_dust()
	beat = Beat.LAND
	beat_left = land_time


func Physics_Update(delta: float) -> void:
	if released:
		return
	_step_stars(delta)
	_step_dust(delta)
	beat_left -= delta
	if beat_left > 0.0:
		return
	match beat:
		Beat.LAND:
			_open()
		Beat.WINDOW:
			if nap_after_slam and from == &"slam":
				left_at = body.fight_clock
				state_machine.on_child_transition(self, "Sleep")
				return
			_roll()
		Beat.ROLL:
			left_at = body.fight_clock
			state_machine.attack_done(self)


func Exit() -> void:
	release()


# Idempotent: his box and hurtbox back to standing, and the stars and the dust gone. His animation is left as it
# is, so the sumo, if this was where 0 HP caught him, still sees him on his back (DannyBossSumo.was_on_back).
func release() -> void:
	if released:
		return
	released = true
	_clear_stars()
	for puff in dust:
		if is_instance_valid(puff):
			puff.queue_free()
	dust.clear()
	if not is_instance_valid(body):
		return
	body.show_zzz(false)
	body.set_hurtbox_active(false)
	body.set_body_box(&"idle")


func _exit_tree() -> void:
	released = true


# His window is open: punches land, and the finisher may daze him.
func is_window() -> bool:
	return not released and beat == Beat.WINDOW


# A punch landed: he flinches and stays dazed.
func flinch() -> void:
	if not is_window():
		return
	hits += 1
	body.play_anim(&"back_hit", &"back_daze")
	body.play_sfx(&"back_hit")


# The finisher's daze draws its own stars over his head (DannyBossScript.enter_daze).
func show_stars(shown: bool) -> void:
	stars_shown = shown
	_step_stars(0.0)


func _open() -> void:
	beat = Beat.WINDOW
	beat_left = open_for
	window_at = body.fight_clock
	body.hits_this_window = 0
	body.daze_used = false
	body.set_hurtbox_active(true)
	body.state_anim = &"back_daze"
	body.play_anim(&"back_daze")
	# The back sheet draws its stars into the daze loop; its stand-in has none.
	if Layout.BACK_DAZE_MARK == &"zs":
		body.show_zzz(true)
	elif not Layout.is_final(&"back_daze"):
		_spawn_stars()


func _roll() -> void:
	beat = Beat.ROLL
	beat_left = roll_time
	_clear_stars()
	body.show_zzz(false)
	body.set_hurtbox_active(false)
	# Idle lets a roll still playing carry on into its own idle.
	body.play_anim(&"back_roll", &"idle")
	body.play_sfx(&"back_roll")


func _head_point() -> Vector2:
	return body.crown_point(&"back_daze") - Vector2(0, Layout.DAZE_GAP)


func _spawn_stars() -> void:
	_clear_stars()
	var spec := FinisherArtLayout.stars()
	stars = Sprite2D.new()
	stars.texture = load(spec.texture)
	stars.hframes = spec.hframes
	stars.centered = false
	stars.offset = -spec.pivot
	stars.scale = Vector2.ONE * spec.scale
	stars.z_index = STARS_Z_INDEX
	body.get_parent().add_child(stars)
	stars_clock = 0.0
	_step_stars(0.0)


func _step_stars(delta: float) -> void:
	if not is_instance_valid(stars):
		return
	stars_clock += delta
	stars.frame = int(stars_clock / FinisherArtLayout.stars().frame_time) % stars.hframes
	stars.visible = stars_shown
	stars.global_position = _head_point().round()


func _clear_stars() -> void:
	if is_instance_valid(stars):
		stars.queue_free()
	stars = null


# A puff of his skid dust at each end of his lying box, once.
func _puff_dust() -> void:
	var spec := Layout.fx(&"sumo_dust")
	var box: Rect2 = body.body_box_rect(&"back")
	for side in [-1.0, 1.0]:
		var puff := Sprite2D.new()
		puff.texture = load(spec.texture)
		puff.hframes = spec.hframes
		puff.vframes = spec.vframes
		puff.frame_coords = Vector2i(0, spec[DUST_ROW])
		puff.flip_h = side > 0.0
		puff.offset = Layout.flipped_offset(spec.offset, puff.flip_h)
		puff.scale = Vector2.ONE * Layout.SCALE
		state_machine.add_hazard(puff, Vector2(box.position.x if side < 0.0 else box.end.x, box.end.y), body.floor_layer)
		dust.append(puff)
	dust_clock = 0.0


# The puffs play once on this state's clock, so a pause holds them, and go.
func _step_dust(delta: float) -> void:
	if dust.is_empty():
		return
	dust_clock += delta
	var spec := Layout.fx(&"sumo_dust")
	var frame := int(dust_clock / spec.frame_time)
	for puff in dust:
		if is_instance_valid(puff):
			if frame >= spec.hframes:
				puff.queue_free()
			else:
				puff.frame_coords = Vector2i(frame, spec[DUST_ROW])
	if frame >= spec.hframes:
		dust.clear()
