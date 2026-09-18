extends State

# THE CATCH: Computah's pounce landed, so he hands the player to Greyson, who puts five punches
# through them and launches them off the fifth.
#
#   0.00  the grab lands - lock_actions(), hit-stop, the crowd
#   0.25  the player is warped to Greyson's combo spot and turned to face him; Computah tosses,
#         Greyson starts his combo on its wind-up frame
#
# In phase two with Greyson gone there is nobody to hand them to, so the same state runs a SOLO
# version: Computah holds them, slams them for the damage the fifth punch would have dealt, and
# tosses them. The plan did not cover a landed pounce with no catcher; without this the move has
# nobody to pass to at all.
#   +     five hits, timed off the combo animation's own frames so the beats can never drift from
#         the drawings they land on. Hits 1-4 deal nothing; the fifth deals the damage and launches.
#   end   unlock_actions(), then release_grab() for the toss and the i-frames, and straight back to
#         Idle with no punish window - the catch is the punishment.
#
# IT IS ONE STATE WITH ONE release() FUNNEL, CALLED FROM Exit() AND FROM _exit_tree(). A player left
# locked can never move again, which is the worst bug this fight can have, and a single idempotent
# funnel is the only way every failure path - a win, a loss, a finisher, a scene change - is provably
# safe. DO NOT SPLIT THIS INTO THREE STATES.
#
# The combo is unblockable by construction rather than by a new kind of lock: the player keeps the
# parry-only lock, and the hits are catalogued unblockable and unparryable, so there is nothing for
# the guard to answer. The player also keeps their own sprite - grab() is never called, which is why
# release_grab() below is called without one.
#
# FREEZE SAFETY: every beat is a Physics_Update accumulator. Nothing here may use
# get_tree().create_timer() or a tree-level create_tween().

const HitStop := preload("res://Scripts/HitStop.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const Layout := preload("res://Scripts/GreysonComputahArtLayout.gd")

@export var greyson : CharacterBody2D
@export var computah : CharacterBody2D
@export var fx_layer : Node2D
@export var catch_sfx_player : AudioStreamPlayer
@export var punch_sfx_player : AudioStreamPlayer

@onready var state_machine = get_parent()

# Set by GcChase before the transition.
var grabber: Node = null
var catcher: Node = null

# When the player is handed over, measured from the grab.
const WARP_AT := 0.25
# Phase two with Greyson gone: there is nobody to hand the player to, so Computah slams them himself.
# One blow for the same damage the fifth punch deals, off frames he already has.
const SOLO_SLAM_AT := 0.3
const SOLO_END := 0.55
const GRAB_HIT_STOP := 0.1
const JAB_HIT_STOP := 0.05
const FINISH_HIT_STOP := 0.18
const JAB_SHAKE := 6.0
const FINISH_SHAKE := 18.0
const SHAKE_STEPS := 4
const FINISH_SHAKE_STEPS := 7
const SHAKE_STEP_TIME := 0.03
# Up and away from Greyson, so the launch clears his reach.
const TOSS_LIFT := 0.7

# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
var clock := 0.0
var warped := false
var hits_done := 0
var combo_end := 0.0
var hold_point := Vector2.ZERO
# No Greyson to hand them to: Computah finishes it himself.
var solo := false


func Enter() -> void:
	released = false
	clock = 0.0
	warped = false
	hits_done = 0
	solo = not is_instance_valid(catcher)
	combo_end = SOLO_END if solo else WARP_AT + Layout.combo_length()

	state_machine.lock_player()
	var player: Node2D = state_machine.get_player()
	hold_point = grabber.global_position if is_instance_valid(grabber) else Vector2.ZERO
	if player:
		hold_point = player.global_position
		if is_instance_valid(catcher):
			catcher.face_toward(player.global_position)
	if is_instance_valid(grabber):
		grabber.velocity = Vector2.ZERO
		grabber.set_grab_active(false)
		grabber.play_anim(&"grab_hold")
	HitStop.freeze(get_tree(), GRAB_HIT_STOP)
	get_tree().call_group("arena_crowd", "cheer", 1.2)
	catch_sfx_player.play()


func Exit() -> void:
	release()


func _exit_tree() -> void:
	release()


# Idempotent, and called from both Exit() and _exit_tree(). Every way out of this state runs through
# here, including the terminal ones that skip Exit() (GcStateMachine._end_fight).
func release() -> void:
	if released:
		return
	released = true
	if state_machine and is_instance_valid(state_machine):
		state_machine.unlock_player()
		state_machine.clear_player_facing()
	if is_instance_valid(grabber):
		grabber.set_grab_active(false)
		grabber.show_battery(false)


func Physics_Update(delta: float) -> void:
	if released:
		return
	clock += delta
	if solo:
		_hold_player()
		if hits_done == 0 and clock >= SOLO_SLAM_AT:
			hits_done = 1
			_slam()
	else:
		if not warped and clock >= WARP_AT:
			_hand_over()
		if warped:
			_hold_player()
			while hits_done < Layout.COMBO_HIT_STEPS.size() and clock >= WARP_AT + Layout.combo_hit_time(hits_done):
				_land_hit(hits_done)
				hits_done += 1
	if clock >= combo_end:
		_let_go()


# The solo version: he shakes them and puts them down, for the damage the fifth punch would have.
func _slam() -> void:
	var player: Node2D = state_machine.get_player()
	if is_instance_valid(grabber):
		grabber.play_anim(&"toss", state_machine.rest_anim(grabber))
	if player:
		player.receive_hit(HitInfo.make(&"computah_slam", self, hold_point, grabber))
	_burst(hold_point, true)
	punch_sfx_player.pitch_scale = 0.8
	punch_sfx_player.play()
	HitStop.freeze(get_tree(), FINISH_HIT_STOP)
	if is_instance_valid(grabber):
		grabber.shake_screen(FINISH_SHAKE, FINISH_SHAKE_STEPS, SHAKE_STEP_TIME)
	get_tree().call_group("arena_crowd", "cheer", 2.0)


# Computah throws them across; Greyson catches them on his combo's wind-up frame, which is the same
# drawing he starts every one of these from.
func _hand_over() -> void:
	warped = true
	if is_instance_valid(grabber):
		grabber.play_anim(&"toss", &"idle")
	if not is_instance_valid(catcher):
		return
	hold_point = catcher.combo_spot()
	state_machine.warp_player(hold_point)
	state_machine.face_player_at(catcher.global_position)
	catcher.play_anim(&"combo")


# Kept where Greyson holds them, so every burst lines up with the art. A locked player's
# _physics_process returns before anything moves them, so writing the position here is what carries.
func _hold_player() -> void:
	var player: Node2D = state_machine.get_player()
	if player == null:
		return
	player.global_position = hold_point.round()
	player.velocity = Vector2.ZERO


func _land_hit(index: int) -> void:
	var last := index == Layout.COMBO_HIT_STEPS.size() - 1
	var player: Node2D = state_machine.get_player()
	var fist: Vector2 = catcher.combo_fist(index) if is_instance_valid(catcher) else hold_point
	if player:
		player.receive_hit(HitInfo.make(
			&"greyson_combo_finish" if last else &"greyson_combo_jab", self, fist, catcher))
	_burst(fist, last)
	punch_sfx_player.pitch_scale = 0.8 if last else 1.0 + index * 0.05
	punch_sfx_player.play()
	HitStop.freeze(get_tree(), FINISH_HIT_STOP if last else JAB_HIT_STOP)
	if is_instance_valid(catcher):
		catcher.shake_screen(FINISH_SHAKE if last else JAB_SHAKE,
			FINISH_SHAKE_STEPS if last else SHAKE_STEPS, SHAKE_STEP_TIME)
	if last:
		get_tree().call_group("arena_crowd", "cheer", 2.0)


# The player is freed first and only then tossed: release_grab() is called without a preceding
# grab(), which looks odd but is deliberate. It is the only existing way to hand back the post-grab
# i-frames and the launch, and calling it unpaired is harmless - is_grabbed is already false and the
# sprite is already shown, since this fight never took either away.
func _let_go() -> void:
	var thrower: Node = catcher if is_instance_valid(catcher) else grabber
	var away := Vector2(-1.0 if (is_instance_valid(thrower) and thrower.facing_left) else 1.0, -TOSS_LIFT)
	release()
	state_machine.release_player(away)
	if is_instance_valid(catcher):
		catcher.play_anim(state_machine.rest_anim(catcher))
	if is_instance_valid(grabber) and not solo:
		grabber.play_anim(state_machine.rest_anim(grabber))
	# Straight back to the beat: the catch was the punishment, so it opens no window.
	state_machine.on_child_transition(self, "Idle")


func _burst(at: Vector2, finish: bool) -> void:
	if Layout.USE_FINAL_COMBO_IMPACT:
		return
	var spec := Layout.PLACEHOLDER_COMBO_IMPACT
	var burst := Polygon2D.new()
	burst.polygon = Layout.star(spec.points, spec.radius, spec.inner_ratio)
	burst.color = spec.finish_color if finish else spec.color
	burst.scale = Vector2.ONE * spec.from_scale
	burst.material = Layout.additive()
	fx_layer.add_child(burst)
	burst.global_position = at.round()
	var reach: float = spec.finish_scale if finish else spec.to_scale
	var time: float = spec.finish_time if finish else spec.time
	var play := burst.create_tween()
	play.tween_property(burst, "scale", Vector2.ONE * reach, time)
	play.parallel().tween_property(burst, "modulate:a", 0.0, time)
	play.tween_callback(burst.queue_free)
