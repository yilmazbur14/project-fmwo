extends State

# ATTACK B: Computah runs the player down while Greyson throws junk over the top of it.
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
# THE CHASE CLOCK IS THE BATTERY. It runs flat over chase_time and that is what opens Computah's
# punish window - the B half of the A-B alternation. His own frames carry the coarse read (cells,
# cell colour and antenna ball, all three at once) and the gauge over his head the precise one.
#
# rearm_parry() IS CALLED AT THE START OF EVERY POUNCE TELL, ALWAYS. Without it a whiffed press
# earlier in the chase can leave the next pounce mathematically unparryable.
#
# The same state covers phase two. Computah alone: the chase no longer times out, because there is
# nobody left to change his battery - it ends when he pounces and misses, and the whiff overheats him
# into a window instead. Greyson alone: there is no runner at all, and the state is his three-shot
# junk burst, which is what his throws became.

const ParryTell := preload("res://Scripts/ParryTell.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const JUNK_SCENE := preload("res://Scenes/Bosses/GreysonJunkProjectileScene.tscn")

@export var greyson : CharacterBody2D
@export var computah : CharacterBody2D
@export var hazard_layer : Node2D
@export var chase_sfx_player : AudioStreamPlayer
@export var pounce_sfx_player : AudioStreamPlayer
@export var throw_sfx_player : AudioStreamPlayer

@onready var state_machine = get_parent()

enum Phase { PURSUE, TELL, LUNGE, WHIFF }

# How close to the lunge target counts as having got there.
const LUNGE_ARRIVE := 8.0
# The last seconds of the battery flash, and the charge state steps at these fractions left.
const BATTERY_FLASH_LEFT := 1.0
const CHARGE_STEPS := [0.66, 0.33]

# Computah while he is running, or null once he is gone.
var runner: Node = null
# Greyson while he is throwing, or null once he is gone.
var thrower: Node = null

var clock := 0.0
var chase_length := 0.0
var ended := false

var phase := Phase.PURSUE
var tell_left := 0.0
var lunge_target := Vector2.ZERO
var whiff_left := 0.0
var pounce_ready_at := 0.0
# Phase two above double_pounce_power: one more lunge, with its own tell and its own rearm. One per
# pounce - `doubled` is what stops the second whiff arming a third.
var double_left := 0
var doubled := false

var throw_clock := 0.0
var throw_tell_left := 0.0
var throwing := false
var shots_left := 0
var burst_left := 0.0
var open_left := 0.0


func Enter() -> void:
	clock = 0.0
	ended = false
	# A body held on the brink still fights; it just can't be hurt any further.
	runner = computah if state_machine.fight.is_alive(computah) else null
	thrower = greyson if state_machine.fight.is_alive(greyson) else null

	if runner:
		phase = Phase.PURSUE
		runner.velocity = Vector2.ZERO
		runner.set_solid(false)
		# He isn't punchable while he runs, so the player can line up on Greyson instead. The old
		# boss script pulled the same trick when the mech formed.
		runner.set_target_active(false)
		runner.play_anim(&"chase")
		pounce_ready_at = 0.0
		double_left = 0
		# Greyson is the one who changes his battery. With him gone the chase runs on empty and only
		# a whiff ends it, which makes the pounce tell the whole read.
		chase_length = INF if thrower == null else lerpf(state_machine.chase_time,
			state_machine.chase_time_surge, state_machine.pace(computah))
		runner.set_charge_state(0 if _has_battery() else 2)
		runner.show_battery(_has_battery())
		chase_sfx_player.play()

	if thrower:
		throw_clock = 0.0
		throwing = false
		open_left = 0.0
		shots_left = 0
		if runner == null:
			# Greyson alone: the throw is a burst, and it starts with its own tell.
			_start_throw_tell()
		else:
			thrower.play_anim(&"idle")


func Exit() -> void:
	if is_instance_valid(computah):
		ParryTell.clear(computah)
		computah.set_grab_active(false)
		computah.set_solid(true)
		computah.set_target_active(true)
		computah.show_battery(false)
		computah.velocity = Vector2.ZERO
	if is_instance_valid(greyson):
		ParryTell.clear(greyson)
		greyson.set_hurtbox_active(false)
	state_machine.set_open_body(null)


func Physics_Update(delta: float) -> void:
	if ended:
		return
	clock += delta
	if runner:
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
		if _has_battery() and clock >= chase_length:
			_battery_died()
			return
	if thrower:
		_advance_throws(delta)


# In phase one Greyson keeps him charged; alone, nobody does.
func _has_battery() -> bool:
	return chase_length < INF


#THE BATTERY
# His own frames are the read: cell count, cell colour and antenna ball all change together, which
# is why the charge state is a frame offset and not a tint.

func _advance_battery() -> void:
	if not _has_battery():
		return
	var left := clampf(1.0 - clock / chase_length, 0.0, 1.0)
	var state := 2
	if left > CHARGE_STEPS[0]:
		state = 0
	elif left > CHARGE_STEPS[1]:
		state = 1
	runner.set_charge_state(state)
	runner.set_battery(left, left * chase_length <= BATTERY_FLASH_LEFT)


func _battery_died() -> void:
	ended = true
	runner.velocity = Vector2.ZERO
	runner.show_battery(false)
	state_machine.open_window(computah, state_machine.battery_window, computah.MAX_HITS_PER_WINDOW,
		&"collapse", &"down", &"reboot")


#PURSUIT
# Steered, never snapped: he accelerates toward the player, so a juke makes him overshoot. That
# overshoot is the skill expression, and it is why the pathing is deliberately dumb - the arena is a
# convex box with nothing in it.

func _pursue(delta: float) -> void:
	var player: Node2D = state_machine.get_player()
	if player == null:
		return
	var along := clampf(clock / maxf(_speed_ramp_time(), 0.01), 0.0, 1.0)
	var speed := lerpf(state_machine.chase_speed_from, state_machine.chase_speed_to, along)
	var to_player: Vector2 = player.global_position - runner.global_position
	var desired := to_player.normalized() * speed if to_player.length() > 0.0 else Vector2.ZERO
	runner.velocity = runner.velocity.move_toward(desired, state_machine.chase_accel * delta)
	_step(delta)
	runner.face_toward(player.global_position)
	if to_player.length() <= state_machine.pounce_range and clock >= pounce_ready_at:
		_start_tell()


func _speed_ramp_time() -> float:
	return chase_length if _has_battery() else state_machine.chase_time


# He writes his own position, clamped to the ropes, with his collision shape off: he neither shoves
# the player nor sticks to them. Eric's lunge does the same.
func _step(delta: float) -> void:
	var bounds: Rect2 = state_machine.runner_bounds()
	runner.global_position = (runner.global_position + runner.velocity * delta).clamp(bounds.position, bounds.end)


#THE POUNCE

# A fresh pounce takes no duration; the second lunge of a double passes its own shorter one.
func _start_tell(duration := -1.0) -> void:
	if duration <= 0.0:
		doubled = false
		duration = maxf(state_machine.pounce_tell, state_machine.POUNCE_TELL_FLOOR)
	phase = Phase.TELL
	tell_left = duration
	runner.velocity = Vector2.ZERO
	runner.play_anim(&"pounce_wind")
	ParryTell.telegraph(runner, &"computah_chase", tell_left, runner.tell_anchor)
	# ALWAYS, at the start of every tell: a press that whiffed earlier must never make this one
	# unanswerable (PlayerDefense.parry_mash_lockout).
	state_machine.rearm_parry()
	pounce_sfx_player.play()


func _advance_tell(delta: float) -> void:
	tell_left -= delta
	var player: Node2D = state_machine.get_player()
	if player:
		runner.face_toward(player.global_position)
	if tell_left <= 0.0:
		_start_lunge()


func _start_lunge() -> void:
	ParryTell.clear(runner)
	phase = Phase.LUNGE
	var player: Node2D = state_machine.get_player()
	var to_player: Vector2 = (player.global_position - runner.global_position) if player else Vector2.RIGHT
	lunge_target = runner.global_position + to_player.limit_length(state_machine.pounce_reach)
	runner.set_grab_active(true)
	runner.play_anim(&"pounce")


func _advance_lunge(delta: float) -> void:
	# Overlaps are from the last physics step, so the final position still gets checked on the frame
	# after he arrives.
	if _catches_player():
		_caught()
		return
	if runner.global_position.distance_to(lunge_target) <= LUNGE_ARRIVE:
		_whiff()
		return
	var bounds: Rect2 = state_machine.runner_bounds()
	runner.global_position = runner.global_position.move_toward(lunge_target,
		state_machine.pounce_speed * delta).clamp(bounds.position, bounds.end)


func _catches_player() -> bool:
	var player: Node2D = state_machine.get_player()
	if player == null:
		return false
	var near_miss := false
	for area in runner.grab_area.get_overlapping_areas():
		if area == player.hurtBox:
			return player.receive_hit(_grab_hit()) == HitInfo.Result.HIT
		if player.is_dodge_ghost(area):
			near_miss = true
	# Only where the player isn't: the pounce closing on the spot a dash left is a perfect dodge.
	if near_miss:
		player.receive_near_miss(_grab_hit())
	return false


func _grab_hit() -> RefCounted:
	return HitInfo.make(&"computah_chase", self, runner.grab_shape.global_position, runner)


func _whiff() -> void:
	runner.set_grab_active(false)
	phase = Phase.WHIFF
	whiff_left = state_machine.pounce_stumble
	runner.play_anim(&"pounce_whiff")
	# The second lunge of a high-power double pounce, once per pounce and never again off its own
	# whiff.
	if not doubled and _double_pounces():
		doubled = true
		double_left = 1
		whiff_left = state_machine.double_pounce_delay


func _double_pounces() -> bool:
	return state_machine.fight.swapped and runner == computah \
		and state_machine.fight.power > state_machine.double_pounce_power


func _advance_whiff(delta: float) -> void:
	whiff_left -= delta
	if whiff_left > 0.0:
		return
	if double_left > 0:
		double_left = 0
		_start_tell(maxf(state_machine.double_pounce_tell, state_machine.POUNCE_TELL_FLOOR))
		return
	# Alone, a whiff is the end of it: he overheats and stands there venting.
	if not _has_battery():
		ended = true
		state_machine.open_window(computah, state_machine.overheat_window, computah.MAX_HITS_PER_WINDOW,
			&"collapse", &"down", &"reboot")
		return
	pounce_ready_at = clock + state_machine.pounce_cooldown
	phase = Phase.PURSUE
	runner.play_anim(&"chase")


func _caught() -> void:
	ended = true
	runner.set_grab_active(false)
	runner.velocity = Vector2.ZERO
	var caught: State = state_machine.states.get("Caught")
	caught.grabber = runner
	# With Greyson gone there is nobody to hand them to, and Caught runs its solo version instead.
	caught.catcher = greyson if state_machine.fight.is_alive(greyson) else null
	state_machine.on_child_transition(self, "Caught")


#THE PARRY
# Only a live pounce can be parried, and a parried one sparks him out into the battery window early.

func can_parry_stagger(_hit: RefCounted) -> bool:
	return not ended and runner != null and phase == Phase.LUNGE


func parry_stagger(duration: float) -> void:
	if ended or runner == null:
		return
	ended = true
	ParryTell.clear(runner)
	runner.set_grab_active(false)
	runner.velocity = Vector2.ZERO
	runner.show_battery(false)
	var window := maxf(duration, state_machine.battery_window + state_machine.parry_stagger_bonus)
	state_machine.open_window(computah, window, computah.MAX_HITS_PER_WINDOW,
		&"collapse", &"down", &"reboot")


#GREYSON'S JUNK
# One piece every junk_interval with its own tell, aimed where the player was when he let go, and he
# is open for junk_open afterwards - the greedy, risky extra damage the cycle doesn't hand out.
# In phase two it becomes a burst of three off one tell.

func _advance_throws(delta: float) -> void:
	if open_left > 0.0:
		open_left -= delta
		if open_left <= 0.0:
			_close_opening()
			if ended:
				return
	if burst_left > 0.0:
		burst_left -= delta
		if burst_left <= 0.0:
			_fire_shot()
		return
	if throwing:
		throw_tell_left -= delta
		if throw_tell_left <= 0.0:
			_release()
		return
	throw_clock += delta
	if throw_clock >= _throw_interval():
		_start_throw_tell()


func _throw_interval() -> float:
	return state_machine.junk_interval * state_machine.fight.interval_scale(greyson)


func _start_throw_tell() -> void:
	throwing = true
	throw_clock = 0.0
	throw_tell_left = state_machine.junk_tell
	shots_left = state_machine.burst_shots if runner == null else 1
	thrower.play_anim(&"throw_wind")
	var player: Node2D = state_machine.get_player()
	if player:
		thrower.face_toward(player.global_position)
	ParryTell.telegraph(thrower, _junk_id(), throw_tell_left, thrower.tell_anchor)


func _release() -> void:
	throwing = false
	ParryTell.clear(thrower)
	_fire_shot()
	_open_greyson()


func _fire_shot() -> void:
	if shots_left <= 0:
		return
	shots_left -= 1
	var player: Node2D = state_machine.get_player()
	var from: Vector2 = thrower.hand_point()
	var to: Vector2 = player.global_position if player else from + Vector2.LEFT * 400.0
	var junk := JUNK_SCENE.instantiate()
	junk.attack_id = _junk_id()
	junk.speed = state_machine.junk_speed
	junk.direction = (to - from).normalized()
	junk.player = player
	state_machine.add_hazard(junk, from, hazard_layer)
	thrower.play_anim(&"throw", &"idle")
	throw_sfx_player.play()
	if shots_left > 0:
		burst_left = state_machine.burst_gap


# Phase two's burst hits harder to block than the single piece does.
func _junk_id() -> StringName:
	return &"greyson_throw_hard" if runner == null else &"greyson_throw"


func _open_greyson() -> void:
	open_left = state_machine.junk_open
	# Nothing to open on a body the clamp is holding at 1 HP: a punch that resolves for 0 would reset
	# the player's combo for free.
	if thrower.on_brink:
		return
	thrower.begin_window(state_machine.junk_window_cap)
	thrower.set_hurtbox_active(true)
	state_machine.set_open_body(thrower)


func _close_opening() -> void:
	open_left = 0.0
	if is_instance_valid(thrower):
		thrower.set_hurtbox_active(false)
	if state_machine.open_body == thrower:
		state_machine.set_open_body(null)
	# Greyson alone runs one burst per cycle and then stands there to be punished for it.
	if runner == null and not ended:
		ended = true
		state_machine.open_window(greyson, state_machine.burst_window, greyson.MAX_HITS_PER_WINDOW,
			&"throw_recover", &"throw_recover", &"")


func flinch(_body: Node) -> void:
	thrower.play_anim(&"hit", &"idle")


# A finisher landing on Greyson's moment mid-chase must NOT end the chase: FightFreeze already
# stopped Computah mid-stride and he picks up exactly where he was. The opening simply closes, and
# Greyson's next throw is pushed back by the stagger he just took.
func end_window(body: Node, stagger_time: float) -> bool:
	if body != thrower or open_left <= 0.0:
		return false
	_close_opening()
	throw_clock = -stagger_time
	thrower.play_anim(&"hit", &"idle")
	return true
