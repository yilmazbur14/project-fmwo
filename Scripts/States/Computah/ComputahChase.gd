extends State

# THE CHASE: he runs the player down and pounces on them.
#
# IT IS NOT IN THE ROTATION YET. ComputahStateMachine.start_cycle() runs the beam and only the beam;
# this state is wired, working and waiting for the second attack that is built on it, where the
# chase turns high-speed and its job is to herd the player onto their own minefield.
#
# THE CHASE IS A RHYTHM, NOT A GRAB BLOB. Touching him does nothing. Within pounce_range he commits
# to a POUNCE with its own parry tell, and the pounce is the grab. It has three counters:
#   OUTRUN IT     - he steers with acceleration rather than snapping to a direction, so juking makes
#                   him overshoot. Max speed ramps 420 -> 660 over the chase; the player walks 600.
#   DASH THROUGH  - `dash_through` on the grab, so dash immunity dodges it and pays a perfect dodge.
#   PARRY IT      - `parryable` + `parry_stagger`: he sparks out into the battery window early.
# A HELD GUARD DOES NOT STOP IT. Grabs bypass the guard in PlayerDefense.resolve_hit, and Eric's bear
# hug already establishes that trap.
#
# THE CHASE CLOCK IS THE BATTERY. It runs flat over chase_time and that is what opens his punish
# window. His own frames carry the coarse read (cells, cell colour and antenna ball, all three at
# once) and the gauge over his head the precise one.
#
# rearm_parry() IS CALLED AT THE START OF EVERY POUNCE TELL, ALWAYS. Without it a whiffed press
# earlier in the chase can leave the next pounce mathematically unparryable.

const ParryTell := preload("res://Scripts/ParryTell.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")

@export var body : CharacterBody2D
@export var chase_sfx_player : AudioStreamPlayer
@export var pounce_sfx_player : AudioStreamPlayer

@onready var state_machine = get_parent()

enum Phase { PURSUE, TELL, LUNGE, WHIFF }

# How close to the lunge target counts as having got there.
const LUNGE_ARRIVE := 8.0
# The last seconds of the battery flash, and the charge state steps at these fractions left.
const BATTERY_FLASH_LEFT := 1.0
const CHARGE_STEPS := [0.66, 0.33]

# Set by ComputahStateMachine.start_chase() before the transition, the way open_window() fills in the
# punish window: the mine field runs this same rhythm faster and longer. Zero means the chase's own
# numbers, so a bare transition into this state still gets a working chase.
var speed_from := 0.0
var speed_to := 0.0
var length := 0.0

var clock := 0.0
var chase_length := 0.0
var ended := false

var phase := Phase.PURSUE
var tell_left := 0.0
var lunge_target := Vector2.ZERO
var whiff_left := 0.0
var pounce_ready_at := 0.0


func Enter() -> void:
	clock = 0.0
	ended = false
	phase = Phase.PURSUE
	chase_length = length if length > 0.0 else state_machine.chase_time
	body.velocity = Vector2.ZERO
	body.set_solid(false)
	# He isn't punchable while he runs, so the player has nothing to auto-face mid-run.
	body.set_target_active(false)
	body.play_anim(&"chase")
	pounce_ready_at = 0.0
	body.set_charge_state(0)
	body.show_battery(true)
	chase_sfx_player.play()


func Exit() -> void:
	ParryTell.clear(body)
	body.set_grab_active(false)
	body.set_solid(true)
	body.set_target_active(true)
	body.show_battery(false)
	body.velocity = Vector2.ZERO
	state_machine.set_open(false)


func Physics_Update(delta: float) -> void:
	if ended:
		return
	clock += delta
	_advance_battery()
	match phase:
		Phase.PURSUE:
			_pursue(delta)
		Phase.TELL:
			_advance_tell(delta)
		Phase.LUNGE:
			_advance_lunge(delta)
		Phase.WHIFF:
			_advance_whiff(delta)
	# A beat above may have handed the fight on; this state is already out of the machine.
	if ended:
		return
	if clock >= chase_length:
		_battery_died()


#THE BATTERY
# His own frames are the read: cell count, cell colour and antenna ball all change together, which
# is why the charge state is a frame offset and not a tint.

func _advance_battery() -> void:
	var left := clampf(1.0 - clock / chase_length, 0.0, 1.0)
	var state := 2
	if left > CHARGE_STEPS[0]:
		state = 0
	elif left > CHARGE_STEPS[1]:
		state = 1
	body.set_charge_state(state)
	body.set_battery(left, left * chase_length <= BATTERY_FLASH_LEFT)


func _battery_died() -> void:
	ended = true
	body.velocity = Vector2.ZERO
	body.show_battery(false)
	state_machine.open_window(state_machine.battery_window, body.MAX_HITS_PER_WINDOW,
		&"collapse", &"down", &"reboot")


#PURSUIT
# Steered, never snapped: he accelerates toward the player, so a juke makes him overshoot. That
# overshoot is the skill expression, and it is why the pathing is deliberately dumb - the arena is a
# convex box with nothing in it.

func _pursue(delta: float) -> void:
	var player: Node2D = state_machine.get_player()
	if player == null:
		return
	var along := clampf(clock / maxf(chase_length, 0.01), 0.0, 1.0)
	var from: float = speed_from if speed_from > 0.0 else state_machine.chase_speed_from
	var to: float = speed_to if speed_to > 0.0 else state_machine.chase_speed_to
	var speed := lerpf(from, to, along)
	var to_player: Vector2 = player.global_position - body.global_position
	var desired := to_player.normalized() * speed if to_player.length() > 0.0 else Vector2.ZERO
	body.velocity = body.velocity.move_toward(desired, state_machine.chase_accel * delta)
	_step(delta)
	body.face_toward(player.global_position)
	if to_player.length() <= state_machine.pounce_range and clock >= pounce_ready_at:
		_start_tell()


# He writes his own position, clamped to the ropes, with his collision shape off: he neither shoves
# the player nor sticks to them. Eric's lunge does the same.
func _step(delta: float) -> void:
	var bounds: Rect2 = state_machine.runner_bounds()
	body.global_position = (body.global_position + body.velocity * delta).clamp(bounds.position, bounds.end)


#THE POUNCE

func _start_tell() -> void:
	phase = Phase.TELL
	tell_left = maxf(state_machine.pounce_tell, state_machine.POUNCE_TELL_FLOOR)
	body.velocity = Vector2.ZERO
	body.play_anim(&"pounce_wind")
	ParryTell.telegraph(body, &"computah_chase", tell_left, body.tell_anchor)
	# ALWAYS, at the start of every tell: a press that whiffed earlier must never make this one
	# unanswerable (PlayerDefense.parry_mash_lockout).
	state_machine.rearm_parry()
	pounce_sfx_player.play()


func _advance_tell(delta: float) -> void:
	tell_left -= delta
	var player: Node2D = state_machine.get_player()
	if player:
		body.face_toward(player.global_position)
	if tell_left <= 0.0:
		_start_lunge()


func _start_lunge() -> void:
	ParryTell.clear(body)
	phase = Phase.LUNGE
	var player: Node2D = state_machine.get_player()
	var to_player: Vector2 = (player.global_position - body.global_position) if player else Vector2.RIGHT
	lunge_target = body.global_position + to_player.limit_length(state_machine.pounce_reach)
	# INSIDE catch_grace THE GRAB NEVER ARMS. The tell still went up and the lunge still happens - he
	# comes up empty, which reads as him fumbling rather than as the player being invulnerable - but a
	# player he has only just put down cannot be picked straight back up. The tell never scales.
	body.set_grab_active(not state_machine.in_catch_grace())
	body.play_anim(&"pounce")


func _advance_lunge(delta: float) -> void:
	# Overlaps are from the last physics step, so the final position still gets checked on the frame
	# after he arrives.
	if _catches_player():
		_caught()
		return
	if body.global_position.distance_to(lunge_target) <= LUNGE_ARRIVE:
		_whiff()
		return
	var bounds: Rect2 = state_machine.runner_bounds()
	body.global_position = body.global_position.move_toward(lunge_target,
		state_machine.pounce_speed * delta).clamp(bounds.position, bounds.end)


func _catches_player() -> bool:
	var player: Node2D = state_machine.get_player()
	if player == null:
		return false
	var near_miss := false
	for area in body.grab_area.get_overlapping_areas():
		if area == player.hurtBox:
			return player.receive_hit(_grab_hit()) == HitInfo.Result.HIT
		if player.is_dodge_ghost(area):
			near_miss = true
	# Only where the player isn't: the pounce closing on the spot a dash left is a perfect dodge.
	if near_miss:
		player.receive_near_miss(_grab_hit())
	return false


func _grab_hit() -> RefCounted:
	return HitInfo.make(&"computah_chase", self, body.grab_shape.global_position, body)


func _whiff() -> void:
	body.set_grab_active(false)
	phase = Phase.WHIFF
	whiff_left = state_machine.pounce_stumble
	body.play_anim(&"pounce_whiff")


func _advance_whiff(delta: float) -> void:
	whiff_left -= delta
	if whiff_left > 0.0:
		return
	pounce_ready_at = clock + state_machine.pounce_cooldown
	phase = Phase.PURSUE
	body.play_anim(&"chase")


func _caught() -> void:
	ended = true
	body.set_grab_active(false)
	body.velocity = Vector2.ZERO
	var caught: State = state_machine.states.get("Caught")
	caught.grabber = body
	state_machine.on_child_transition(self, "Caught")


#THE PARRY
# Only a live pounce can be parried, and a parried one sparks him out into the battery window early.

func can_parry_stagger(_hit: RefCounted) -> bool:
	return not ended and phase == Phase.LUNGE


func parry_stagger(duration: float) -> void:
	if ended:
		return
	ended = true
	ParryTell.clear(body)
	body.set_grab_active(false)
	body.velocity = Vector2.ZERO
	body.show_battery(false)
	var window := maxf(duration, state_machine.battery_window + state_machine.parry_stagger_bonus)
	state_machine.open_window(window, body.MAX_HITS_PER_WINDOW, &"collapse", &"down", &"reboot")
