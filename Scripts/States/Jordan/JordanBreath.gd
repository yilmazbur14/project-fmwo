extends State

# The kaiju's Atomic Breath (scratchpad jordan_kaiju/PLAN.md section 3), one of its two turns: Jordan throws his
# figures down from its head, its plates light one row at a time from the tail to the neck while its head follows the
# player, a yellow ring comes up over its mouth as the aim locks, and the beam lands beside the player and sweeps
# through where they will be (JordanKaijuBeam), leaving a line of fire burning where it stopped (JordanBurnLine).
# Under half health (JordanStateMachine.phase_b) it re-tracks and sweeps back the other way, laying a second line.
#
# LOCK-THEN-LEAD: the aim locks on the player's feet plus their velocity times lead_time. The sweep starts s_back px of
# arc to one side of that point and stops s_end past it, at v_beam px/s along the lock's radius. Against a player
# running across it, it sweeps against their motion; otherwise toward the side with more room, so running ahead of it
# has somewhere to go, and on a cramped side it starts past the ropes and sweeps in. Fire to contact never comes in
# under min_contact.
#
# THE QUIET RULE: no figure's blast lands within half a second before a beam's contact or 0.3 s after it. The fixed
# times guarantee it: the figures land at throw_windup + their 0.45 s flight and their fuses (2.8 +/- 0.4 s, from when
# they land, punched or not) are all out by about 4.1 s; the first fire is at fire_at whatever the phase, its charge
# and lock fitted in before it.
#
# One clock from Enter; release() on Exit and _exit_tree. JordanStateMachine builds it when the kaiju is on.

const KaijuLayout := preload("res://Scripts/JordanKaijuLayout.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")
const Beam := preload("res://Scripts/JordanKaijuBeam.gd")
const BurnLine := preload("res://Scripts/JordanBurnLine.gd")

enum Beat { THROW, CHARGE, LOCK, FIRE, HOLD, RETRACK, DONE }

const BEAM_ID := &"jordan_kaiju_breath"
const PLATE_ROWS := 7
# Where the player's feet can be, for the room either side of the lead point.
const FEET_AREA := Rect2(131, 186, 1656, 761)
const ROOM_STEP_DEGREES := 0.5

@export var throw_windup := 0.40
@export var fire_at := 4.42
@export var row_time := 0.26
@export var row_time_b := 0.22
@export var lock_time := 0.45
@export var lock_time_b := 0.40
@export var track_rate := 120.0
@export var lead_time := 0.25
@export var s_back := 380.0
@export var s_end := 300.0
@export var v_beam := 1000.0
@export var omega_min := 40.0
@export var omega_max := 220.0
@export var grow_time := 0.08
@export var hold_time := 0.30
# Still splitting the ring through the next turn's figures (2026-10-05, longer 2026-10-06): at 4 and 5 s it had gone out
# before they landed.
@export var burn_time := 9.0
@export var burn_time_b := 10.0
@export var retrack_time := 0.50
@export var lock2_time := 0.40
@export var flash_time := 0.15
@export var against_speed := 150.0
@export var min_contact := 0.25
# The yellow ring's anchor over the mouth.
@export var badge_rise := 46.0
@export var badge_slack := 0.05

var body: CharacterBody2D
var hurtbox: Area2D
var state_machine: Node

# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
var clock := 0.0
var beat := Beat.THROW
var beat_at := 0.0
var phase_b := false
var passes := 1
var pass_index := 1
var thrown := false
var charge_start := 0.0
var aim_deg := 0.0
var beam: Node2D
var plan: Dictionary = {}
# For a test: every pass's plan (its lock, fire and contact on this clock), the burn lines laid, and the throw.
var plans: Array[Dictionary] = []
var burns: Array[Node2D] = []
var throw_id := -1


func Enter() -> void:
	released = false
	clock = 0.0
	beat = Beat.THROW
	beat_at = 0.0
	thrown = false
	pass_index = 1
	phase_b = state_machine.phase_b
	passes = 2 if phase_b else 1
	plans.clear()
	burns.clear()
	charge_start = fire_at - _lock_time() - PLATE_ROWS * _row_time()
	var kaiju: Node2D = state_machine.kaiju
	kaiju.play_anim(&"idle")
	kaiju.light_spines(0)
	kaiju.set_charge(0.0)
	aim_deg = kaiju.aim
	body.play_anim(&"ride_throw", &"ride_idle")


func Exit() -> void:
	release()


func _exit_tree() -> void:
	release()


func release() -> void:
	if released:
		return
	released = true
	if is_instance_valid(beam):
		beam.stop()
	beam = null
	var kaiju: Node2D = state_machine.kaiju if is_instance_valid(state_machine) else null
	if is_instance_valid(kaiju):
		ParryTell.clear(kaiju)
		kaiju.light_spines(0)
		kaiju.set_charge(0.0)


func Physics_Update(delta: float) -> void:
	if released:
		return
	clock += delta
	if not thrown and clock >= throw_windup:
		thrown = true
		throw_id = state_machine.throw_funkos()
	match beat:
		Beat.THROW:
			if clock >= charge_start:
				_begin_charge()
		Beat.CHARGE:
			_charge_step(delta)
			if clock >= fire_at - _lock_time():
				_begin_lock()
		Beat.LOCK:
			if clock >= plan.fire:
				_begin_fire()
		Beat.FIRE:
			_fire_step()
		Beat.HOLD:
			beam.sweep_to(state_machine.kaiju.breath_origin(), plan.end, 1.0)
			if clock >= beat_at + hold_time:
				_end_pass()
		Beat.RETRACK:
			_track(delta, true)
			if clock >= beat_at + flash_time:
				state_machine.kaiju.light_spines(PLATE_ROWS)
			if clock >= beat_at + retrack_time:
				pass_index = 2
				_begin_lock()


func _row_time() -> float:
	return row_time_b if phase_b else row_time


func _lock_time() -> float:
	return lock_time_b if phase_b else lock_time


func _begin(new_beat: int) -> void:
	beat = new_beat
	beat_at = clock


func _begin_charge() -> void:
	_begin(Beat.CHARGE)
	state_machine.kaiju.play_anim(&"charge")
	state_machine.play_sfx(&"charge")


func _charge_step(delta: float) -> void:
	var into := clock - charge_start
	state_machine.kaiju.light_spines(clampi(int(into / _row_time()) + 1, 1, PLATE_ROWS))
	state_machine.kaiju.set_charge(into / (PLATE_ROWS * _row_time()))
	_track(delta, false)


# The head after the player's feet, at track_rate, or at once (re-tracking).
func _track(delta: float, snap: bool) -> void:
	var kaiju: Node2D = state_machine.kaiju
	var target := rad_to_deg((state_machine.player_feet() - kaiju.breath_origin()).angle())
	aim_deg = target if snap else move_toward(aim_deg, target, track_rate * delta)
	kaiju.aim_head(aim_deg)


func _begin_lock() -> void:
	_begin(Beat.LOCK)
	var length: float = _lock_time() if pass_index == 1 else lock2_time
	plan = _plan(0.0 if pass_index == 1 else -float(plans[0].dir))
	plan.lock = clock
	plan.fire = fire_at if pass_index == 1 else clock + length
	plan.contact = plan.fire + grow_time + plan.back / plan.v_eff
	plans.append(plan)
	var kaiju: Node2D = state_machine.kaiju
	aim_deg = rad_to_deg(plan.start)
	kaiju.aim_head(aim_deg)
	kaiju.light_spines(PLATE_ROWS)
	kaiju.set_charge(1.0)
	beam = Beam.new()
	beam.name = "KaijuBeam"
	beam.player = state_machine.get_player()
	beam.boss = body
	state_machine.add_floor_hazard(beam, Vector2.ZERO)
	beam.aim(kaiju.breath_origin(), plan.start)
	ParryTell.telegraph(kaiju, BEAM_ID, plan.fire - clock + badge_slack, _badge_point)


func _badge_point() -> Vector2:
	var mouth: Vector2 = state_machine.kaiju.mouth_point()
	return Vector2(mouth.x, maxf(mouth.y - badge_rise, KaijuLayout.BADGE_TOP))


func _begin_fire() -> void:
	_begin(Beat.FIRE)
	ParryTell.clear(state_machine.kaiju)
	state_machine.kaiju.set_charge(1.0, true)
	_fire_step()


func _fire_step() -> void:
	var t := clock - beat_at
	var span := absf(float(plan.end) - float(plan.start))
	var swept := minf(maxf(t - grow_time, 0.0) * float(plan.omega), span)
	var theta: float = plan.start + plan.dir * swept
	aim_deg = rad_to_deg(theta)
	state_machine.kaiju.aim_head(aim_deg)
	beam.sweep_to(state_machine.kaiju.breath_origin(), theta, t / grow_time)
	if swept >= span:
		_begin(Beat.HOLD)
		var burn := BurnLine.new()
		burn.name = "BurnLine"
		burn.player = state_machine.get_player()
		burn.boss = body
		burn.origin = state_machine.kaiju.breath_origin()
		burn.angle = plan.end
		burn.life = burn_time_b if phase_b else burn_time
		state_machine.add_floor_hazard(burn, Vector2.ZERO)
		burns.append(burn)


func _end_pass() -> void:
	beam.stop()
	beam = null
	state_machine.kaiju.set_charge(0.0)
	if pass_index < passes:
		_begin(Beat.RETRACK)
		state_machine.kaiju.light_spines(8)
		state_machine.kaiju.set_charge(0.5)
		_track(0.0, true)
		return
	# Winded by it: its head comes down within reach (JordanRecoil), the plan's half-second recovery made an opening.
	_begin(Beat.DONE)
	state_machine.on_child_transition(self, "Recoil")


#THE AIM

# Where this pass locks and how it sweeps, `force_dir` its direction if not 0. Angles in radians, screen-clockwise.
func _plan(force_dir: float) -> Dictionary:
	var kaiju: Node2D = state_machine.kaiju
	var origin: Vector2 = kaiju.breath_origin()
	var player: Node2D = state_machine.get_player()
	var velocity: Vector2 = player.velocity if player != null else Vector2.ZERO
	var lead: Vector2 = (state_machine.player_feet() + velocity * lead_time).clamp(FEET_AREA.position, FEET_AREA.end)
	var radius := maxf(origin.distance_to(lead), 80.0)
	var theta := (lead - origin).angle()
	var omega := clampf(v_beam / radius, deg_to_rad(omega_min), deg_to_rad(omega_max))
	var v_eff := omega * radius
	var tangential := velocity.dot(Vector2.from_angle(theta).rotated(PI / 2.0))
	var moving := absf(tangential) > against_speed
	var room_plus := room(origin, theta, radius, 1.0)
	var room_minus := room(origin, theta, radius, -1.0)
	var dir := 1.0
	if force_dir != 0.0:
		dir = force_dir
	elif moving:
		dir = -signf(tangential)
	else:
		dir = 1.0 if room_plus >= room_minus else -1.0
	# The start may lie past the ropes on a cramped side - it sweeps in from there - but never closer than
	# min_contact's worth of sweep.
	var min_back := maxf(min_contact - grow_time, 0.0) * v_eff
	var back := maxf(s_back, min_back)
	var lo := deg_to_rad(KaijuLayout.BEAM_AIM_MIN)
	var hi := deg_to_rad(KaijuLayout.BEAM_AIM_MAX)
	var start := clampf(theta - dir * back / radius, lo, hi)
	var end := clampf(theta + dir * s_end / radius, lo, hi)
	return {
		"origin": origin, "lead": lead, "theta": theta, "radius": radius, "omega": omega, "v_eff": v_eff,
		"dir": dir, "start": start, "end": end, "back": absf(theta - start) * radius, "moving": moving,
		"tangential": tangential, "room_plus": room_plus, "room_minus": room_minus,
	}


# How much arc, in px at `radius`, there is from `theta` toward `sign` before the circle leaves the floor the player
# can stand on or the beam's range.
static func room(origin: Vector2, theta: float, radius: float, sign: float) -> float:
	var step := deg_to_rad(ROOM_STEP_DEGREES)
	var lo := deg_to_rad(KaijuLayout.BEAM_AIM_MIN)
	var hi := deg_to_rad(KaijuLayout.BEAM_AIM_MAX)
	var a := theta
	var walked := 0.0
	while walked < PI:
		var next := a + sign * step
		if next < lo or next > hi:
			break
		var point := origin + Vector2.from_angle(next) * radius
		if not FEET_AREA.has_point(point) or KaijuLayout.in_walls(point):
			break
		a = next
		walked += step
	return walked * radius
