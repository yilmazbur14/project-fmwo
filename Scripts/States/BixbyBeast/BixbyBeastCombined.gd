extends State

# His combined attack: he comes down and rears back, pounds the floor three times, each pound sending a
# quake ring rolling out from under him, then clamps his wings in and spins slowly on the spot while his
# three heads scream sonic beams across the arena, sending another ring out on every beat of the spin. The
# rings are slow, so they are still rolling out across the floor while the beams sweep it: the answer is
# to circle with the beams and dash through each ring as it reaches you. He wobbles to a stop dizzy at the
# end, open to punishment like his landing recovery.

const BixbyBeastArtLayout := preload("res://Scripts/BixbyBeastArtLayout.gd")
const CombinedLayout := preload("res://Scripts/BixbyCombinedArtLayout.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")
const SWEEP_SCENE := preload("res://Scenes/Bosses/BixbySonicSweepScene.tscn")

@export var body : CharacterBody2D
@export var pound_sfx_player : AudioStreamPlayer
@export var scream_sfx_player : AudioStreamPlayer
@export var dizzy_sfx_player : AudioStreamPlayer

@onready var state_machine = get_parent()

enum Phase { DESCENT, BRACE, POUNDS, SPIN_UP, SPIN, SPIN_DOWN, DIZZY }

const POUND_SHAKE := 9.0
const LANDING_SHAKE := 12.0
const SHAKE_STEPS := 4
const SHAKE_STEP_TIME := 0.03
# How far his drawn body wobbles as the dizzy spell starts.
const DIZZY_WOBBLE_PX := 5.0
const DIZZY_WOBBLE_STEPS := 8
const DIZZY_WOBBLE_STEP_TIME := 0.05

var phase := Phase.DESCENT
var elapsed := 0.0
var start_height := 0.0
var pounds_done := 0
var impact_done := false
var sweep: Node2D
# Seconds since the spin started or last sent a ring out.
var ring_clock := 0.0
# Once the beams stop he turns on through the loop until his heads reach the wobble's first frame: the
# seconds that takes, and whether he is still doing it.
var coast_time := 0.0
var coasting := false


func Enter() -> void:
	pounds_done = 0
	body.fly_velocity = Vector2.ZERO
	# He pounds from where his whole standing sprite fits on screen.
	var bounds: Rect2 = body.ground_bounds(0.0)
	body.ground_position = body.ground_position.clamp(bounds.position, bounds.end)
	start_height = body.height
	if start_height > 0.0:
		_start(Phase.DESCENT)
		body.play_anim(&"land")
	else:
		_touchdown()


func Exit() -> void:
	body.set_hurtbox_active(false)
	ParryTell.clear(body)
	if is_instance_valid(sweep):
		sweep.queue_free()
	sweep = null


func Physics_Update(delta: float) -> void:
	elapsed += delta
	match phase:
		# Frame 0 of the landing lasts as long as the fall, as it does off every other attack.
		Phase.DESCENT:
			var weight := clampf(elapsed / BixbyBeastArtLayout.time_to_step(&"land", 1), 0.0, 1.0)
			body.height = start_height * (1.0 - weight * weight)
			body.place()
			if weight >= 1.0:
				_touchdown()
		Phase.BRACE:
			if elapsed >= state_machine.combined_windup:
				_start(Phase.POUNDS)
				_pound()
		Phase.POUNDS:
			if not impact_done and elapsed >= BixbyBeastArtLayout.time_to_step(&"pound", BixbyBeastArtLayout.POUND_IMPACT_STEP):
				_impact()
			if elapsed >= state_machine.combined_pound_interval:
				elapsed -= state_machine.combined_pound_interval
				if pounds_done < state_machine.combined_pounds:
					_pound()
				else:
					_start(Phase.SPIN_UP)
					body.play_anim(&"spin_up")
					_tell_the_scream()
		Phase.SPIN_UP:
			if sweep == null and elapsed >= BixbyBeastArtLayout.time_to_step(&"spin_up", BixbyBeastArtLayout.SPIN_BEAMS_STEP):
				_start_beams()
			if elapsed >= BixbyBeastArtLayout.anim_time(&"spin_up"):
				_start(Phase.SPIN)
				ring_clock = 0.0
				body.play_anim(&"spin", &"", _widest_gap_step())
		Phase.SPIN:
			ring_clock += delta
			if ring_clock >= state_machine.combined_spin_ring_interval:
				ring_clock -= state_machine.combined_spin_ring_interval
				_spin_ring()
			if _spun_round():
				_stop_spin()
		Phase.SPIN_DOWN:
			if coasting:
				if elapsed >= coast_time:
					elapsed -= coast_time
					coasting = false
					body.play_anim(&"spin_down")
			elif elapsed >= BixbyBeastArtLayout.anim_time(&"spin_down"):
				_start_dizzy()
		Phase.DIZZY:
			if elapsed >= state_machine.combined_dizzy_time:
				state_machine.on_child_transition(self, "Takeoff")


# The punish window is his dizzy spell, so a punch mid-window flinches him back into it.
func flinch() -> void:
	body.play_anim(&"hit", &"dizzy")


func is_dizzy() -> bool:
	return phase == Phase.DIZZY


func _start(new_phase: Phase) -> void:
	phase = new_phase
	elapsed = 0.0


func _touchdown() -> void:
	body.height = 0.0
	body.place()
	_start(Phase.BRACE)
	body.play_anim(&"brace")
	pound_sfx_player.play()
	body.shake_screen(LANDING_SHAKE, SHAKE_STEPS, SHAKE_STEP_TIME)


# One slam, on the cadence the pound loop is drawn at.
func _pound() -> void:
	pounds_done += 1
	impact_done = false
	body.play_anim(&"pound")


# The frame his claws land on: the floor shakes and a ring rolls out from under him.
func _impact() -> void:
	impact_done = true
	pound_sfx_player.play()
	body.shake_screen(POUND_SHAKE, SHAKE_STEPS, SHAKE_STEP_TIME)
	state_machine.send_quake_ring(body.ground_position)


# Another ring out from under him on the spin's beat. It starts under his body, so the thud is what says
# it has.
func _spin_ring() -> void:
	pound_sfx_player.play()
	state_machine.send_quake_ring(body.ground_position)


# The yellow ring, from his maws lighting up to the last sweep. Unlike a wind-up warning it stays up
# while the beams are out: they sweep for the whole spin and cross any one spot several times over, so
# the read is not "it is coming" but "this one is dashed, not parried", and it has to hold for as long
# as that is true. Nothing else can carry it: the beams come off him and reach the whole floor, so
# there is no one place they land to stand it on. The spin can run up to a loop past combined_spin_time
# (_spun_round), so it is booked for that long and _stop_spin takes it down.
func _tell_the_scream() -> void:
	ParryTell.telegraph(body, &"bixby_sonic_beam", BixbyBeastArtLayout.anim_time(&"spin_up")
		+ state_machine.combined_spin_time + BixbyBeastArtLayout.anim_time(&"spin"), _spin_centre)


# The point his maws orbit, which is where the beams come out of: his daze anchor is on the headband
# plate of his downed frames, and on the spin sheet he is coiled low enough that it lands a body above him,
# up behind the boss bar.
func _spin_centre() -> Vector2:
	return body.feet_position() + BixbyBeastArtLayout.local(CombinedLayout.SPIN_CENTRE)


# His maws light up: the beams come out of them and follow them through the spin.
func _start_beams() -> void:
	scream_sfx_player.play()
	sweep = SWEEP_SCENE.instantiate()
	sweep.player = state_machine.get_player()
	sweep.body = body
	sweep.arena = state_machine.ROPES
	sweep.position = body.feet_position()
	get_tree().current_scene.add_child(sweep)


# Which step of the spin loop to start screaming on, of those spin_up's last frame runs on into
# (SPIN_LOOP.entry_steps). Each has his heads a third of a turn apart, so the one that leaves the player
# furthest from a beam buys them the longest run-up before the first one sweeps over them. A step his heads
# jump to across the player leaves them none: the beams are already lit on spin_up's last frame, and the
# sweep's hit test covers the jump.
func _widest_gap_step() -> int:
	var loop: Dictionary = BixbyBeastArtLayout.SPIN_LOOP
	var steps: Array = loop.entry_steps
	var player = state_machine.get_player()
	if player == null:
		return steps[0]
	var centre: Vector2 = body.feet_position() + BixbyBeastArtLayout.local(CombinedLayout.SPIN_CENTRE)
	var to_player: Vector2 = player.global_position - centre
	if to_player.length() < 1.0:
		return steps[0]
	var azimuth := CombinedLayout.floor_azimuth(to_player.angle())
	var lit: Array = CombinedLayout.MOUTH_ANCHORS[BixbyBeastArtLayout.ANIMS[&"spin_up"].frames[-1]]
	var best: int = steps[0]
	var widest := -1.0
	for step in steps:
		var anchors: Array = CombinedLayout.LOOP_MOUTH_ANCHORS[loop.frames[step]]
		var gap := INF
		for anchor in anchors:
			gap = minf(gap, absf(wrapf(azimuth - deg_to_rad(anchor[0]), -PI, PI)))
		if _jump_crosses(lit, anchors, rad_to_deg(azimuth)):
			gap = 0.0
		if gap > widest:
			widest = gap
			best = step
	return best


# Whether a head turning on from its maw on `from` to the nearest one ahead of it on `to` passes the
# azimuth, in degrees, on the way.
func _jump_crosses(from: Array, to: Array, azimuth: float) -> bool:
	for head in from:
		var turn := 360.0
		for other in to:
			turn = minf(turn, fposmod(other[0] - head[0], 360.0))
		if fposmod(azimuth - head[0], 360.0) <= turn:
			return true
	return false


# He spins for combined_spin_time, then on until his heads come round to a frame the wobble he stops on
# is drawn to follow (SPIN_LOOP.exit_frames), so they never jump backwards into it: at most one more loop.
# He stops screaming halfway through that frame, which a frame's drift between his drawn clock and this one
# can't carry past.
func _spun_round() -> bool:
	if elapsed < state_machine.combined_spin_time:
		return false
	var loop: Dictionary = BixbyBeastArtLayout.SPIN_LOOP
	return loop.exit_frames.has(body.drawn_frame_of(loop.sheet)) \
		and body.anim_clock >= BixbyBeastArtLayout.spin_step_time() / 2.0


# The beams stop, and he winds down: on through the loop at its rate until his heads reach the wobble's
# first frame, so it follows the loop without a jump, then the wobble, which slows him to a stop.
func _stop_spin() -> void:
	if is_instance_valid(sweep):
		sweep.stop()
	sweep = null
	# The beams stop hurting the moment they start dying away.
	ParryTell.clear(body)
	_start(Phase.SPIN_DOWN)
	coast_time = _turn_to_the_wobble() / BixbyBeastArtLayout.SPIN_DEGREES_PER_SECOND
	coasting = true


# How many degrees his heads still turn, at the loop's rate, before they reach the wobble's first frame. The
# heads are alike, so any of its three will do; one his heads have already passed is reached now.
func _turn_to_the_wobble() -> float:
	var loop: Dictionary = BixbyBeastArtLayout.SPIN_LOOP
	var front: float = CombinedLayout.LOOP_MOUTH_ANCHORS[loop.frames[body.anim_step]][0][0] \
		+ loop.step_degrees * body.anim_clock / BixbyBeastArtLayout.spin_step_time()
	var wobble: float = CombinedLayout.MOUTH_ANCHORS[BixbyBeastArtLayout.ANIMS[&"spin_down"].frames[0]][0][0]
	var apart := 360.0 / CombinedLayout.SONIC_BEAMS
	var turn := fposmod(wobble - front, apart)
	return turn if turn < apart / 2.0 else 0.0


func _start_dizzy() -> void:
	_start(Phase.DIZZY)
	body.play_anim(&"dizzy")
	body.shake_screen(LANDING_SHAKE, SHAKE_STEPS, SHAKE_STEP_TIME)
	body.shake_sprite(DIZZY_WOBBLE_PX, DIZZY_WOBBLE_STEPS, DIZZY_WOBBLE_STEP_TIME)
	dizzy_sfx_player.play()
	body.hits_this_window = 0
	body.daze_used = false
	body.set_hurtbox_active(true)
	# The same rule as his landing: the punish window has to be reachable through the fire.
	state_machine.clear_fire_for_landing(body.ground_position)
