extends State

# Greyson's poses (plan section 3.4), attack 1's punish window: six poses to the crowd - A, B, C, A, B, C - on a
# fixed clock, the pose sheets' 0.3 s strike and 1.2 s hold, so the race (plan section 4) comes out the same every
# time. A pose that ends unhit banks `bank` cells of his hype meter to a cheer (two since the user's 2026-09-30
# "double the speed greyson builds his hype meter", so three clean poses fill it); the first hit in a pose spoils
# it - a boo, and pose_hit held to the pose's end - and later hits in it only deal their damage. Any hit that lands
# on him also empties the meter (GreysonScript.hit_resets_hype), whenever it comes. The meter carries from cycle to
# cycle, and a bank that fills it fires the spirit bomb.
# The zones Slams planted go off one after another from around the first strike (eruptions, on
# GreysonStateMachine's eruption clock). The single-bar finisher's uppercut ends the phase (the body's
# end_recovery, then stagger_then_start_cycle).

@export var body : CharacterBody2D

@onready var state_machine = get_parent()

#PACING (seconds)
# Before the first pose he plants the barbell and turns to the crowd, his window still shut.
@export var turn_time := 0.15
@export var pose_time := 1.5
# A cheer lasts until the next pose resolves; a boo this long.
@export var boo_time := 1.75

#HYPE (cells)
@export var bank := 2.0
# A spoiled pose's own drain. It only shows with GreysonScript.hit_resets_hype off: the hit that spoils a pose has
# already emptied the meter.
@export var spoil := -0.5
# The flex's pitch on an empty meter and on a full one: it climbs with his hype.
@export var flex_pitch := Vector2(1.0, 1.3)

#ERUPTIONS (seconds)
# When the zones Slams planted go off, the oldest first, counted from the first pose's strike: from 0.45 s, 32 and 33
# frames apart in turn, 0.54 s on average and each on a frame (0.6 apart until the user's 2026-10-06 "denser move
# sets"), the eighth in pose 3. The slams test's fence sweep proves
# a walk (no dash) comes through them all, and its weave reaches him without a burst.
# The first is no sooner than a walk out of a zone after the last slam lands (a zone's ry at the player's walk, plus
# the ring's start).
@export var eruptions: Array[float] = [0.45, 0.9833, 1.5333, 2.0667, 2.6167, 3.15, 3.7, 4.2333]
# How long before it goes off each is told, turning from waiting to next (stage 2, its rumble rising): at least the
# zone's ring_lead, so its ring runs in full. Slams starts the clock that tells them, so the first can be told
# before the poses begin.
@export var eruption_notice := 1.2

# A the three-quarter back twist, B the front double biceps, C the rear V.
const POSES: Array[StringName] = [&"pose_a", &"pose_b", &"pose_c", &"pose_a", &"pose_b", &"pose_c"]

# The whole phase's cap: the combo and room to spoil every pose.
var hit_cap := 8

var turn_left := 0.0
var pose_index := -1
var pose_clock := 0.0
var spoiled := false
# The phase is under way, so cutting it short quiets the crowd.
var live := false

# For the tests.
var entered_count := 0
# This phase's clock at each strike, and each pose's outcome, &"banked" or &"spoiled", as it resolved.
var phase_clock := 0.0
var strike_times: Array[float] = []
var outcomes: Array[StringName] = []


func Enter() -> void:
	entered_count += 1
	live = true
	phase_clock = 0.0
	pose_index = -1
	strike_times.clear()
	outcomes.clear()
	body.velocity = Vector2.ZERO
	body.set_hurtbox_active(false)
	body.play_state_anim(&"idle")
	state_machine.start_eruption_clock(turn_time, false)
	turn_left = turn_time
	if turn_left <= 0.0:
		_open(0.0)


func Exit() -> void:
	release()


func Physics_Update(delta: float) -> void:
	if not live:
		return
	phase_clock += delta
	if pose_index < 0:
		turn_left -= delta
		if turn_left <= 0.0:
			_open(-turn_left)
		return
	pose_clock += delta
	if pose_clock >= pose_time:
		_resolve(pose_clock - pose_time)


# A hit, damaging, in his window: the first in a pose spoils it, and later ones in it only deal their damage.
func flinch() -> void:
	if pose_index < 0 or spoiled:
		return
	spoiled = true
	body.add_hype(spoil)
	body.play_anim(&"pose_hit")
	body.play_sfx(&"pose_spoiled")
	state_machine.crowd(&"boo", boo_time)


# The hurtbox is only this state's to close while it is his: a release from _stop_everything() on the way into
# a Break must not close the window the Break is opening.
func release() -> void:
	if live:
		state_machine.crowd(&"hush")
	live = false
	pose_index = -1
	turn_left = 0.0
	if state_machine.current_state == self:
		body.set_hurtbox_active(false)


# To the crowd, his window open for the rest of the phase. `into` is how far past the turn this step ran, kept
# so the poses stay on the fixed clock.
func _open(into: float) -> void:
	body.begin_window()
	body.set_hurtbox_active(true)
	_strike(0, into)


func _strike(index: int, into: float) -> void:
	pose_index = index
	pose_clock = into
	spoiled = false
	strike_times.append(phase_clock - into)
	body.play_anim(POSES[index])
	body.play_sfx(&"flex", lerpf(flex_pitch.x, flex_pitch.y, body.hype / body.HYPE_MAX))



func _resolve(into: float) -> void:
	if spoiled:
		outcomes.append(&"spoiled")
	else:
		outcomes.append(&"banked")
		body.add_hype(bank)
		body.play_sfx(&"pose_bank")
		state_machine.crowd(&"cheer", pose_time)
		if body.hype_full() and body.boss_health > 0:
			state_machine.enter_spirit_bomb()
			if state_machine.current_state != self:
				return
	if pose_index + 1 < POSES.size():
		_strike(pose_index + 1, into)
		return
	# Played out: the last cheer runs on into the breath before the next attack.
	live = false
	pose_index = -1
	state_machine.chain_next(self)
