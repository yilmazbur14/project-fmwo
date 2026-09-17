extends State

# His combined attack: he comes down and rears back, pounds the floor three times, each pound planting a
# crack where the player is standing at that moment, then clamps his wings in and spins on the spot while
# his three heads scream sonic beams across the arena. The cracks erupt into ground waves a beat after they
# were planted, so the waves roll across the floor under the spin. He wobbles to a stop dizzy at the end,
# open to punishment like his landing recovery.

const BixbyBeastArtLayout := preload("res://Scripts/BixbyBeastArtLayout.gd")
const CombinedLayout := preload("res://Scripts/BixbyCombinedArtLayout.gd")
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
		Phase.SPIN_UP:
			if sweep == null and elapsed >= BixbyBeastArtLayout.time_to_step(&"spin_up", BixbyBeastArtLayout.SPIN_BEAMS_STEP):
				_start_beams()
			if elapsed >= BixbyBeastArtLayout.anim_time(&"spin_up"):
				_start(Phase.SPIN)
				body.play_anim(&"spin", &"", _widest_gap_step())
		Phase.SPIN:
			if elapsed >= state_machine.combined_spin_time:
				_stop_spin()
		Phase.SPIN_DOWN:
			if elapsed >= BixbyBeastArtLayout.anim_time(&"spin_down"):
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


# The frame his claws land on: the floor shakes and cracks where the player stands.
func _impact() -> void:
	impact_done = true
	pound_sfx_player.play()
	body.shake_screen(POUND_SHAKE, SHAKE_STEPS, SHAKE_STEP_TIME)
	var player = state_machine.get_player()
	if player:
		state_machine.plant_quake_crack(player.global_position, body.ground_position, pounds_done - 1)


# His maws light up: the beams come out of them and follow them through the spin.
func _start_beams() -> void:
	scream_sfx_player.play()
	sweep = SWEEP_SCENE.instantiate()
	sweep.player = state_machine.get_player()
	sweep.body = body
	sweep.arena = state_machine.ROPES
	sweep.position = body.feet_position()
	get_tree().current_scene.add_child(sweep)


# Which frame of the spin loop to start screaming on. Each one has his heads a third of a turn apart,
# thirty degrees on from the one before, so the one that leaves the player furthest from a beam buys them
# the longest run-up before the first one sweeps over them.
func _widest_gap_step() -> int:
	var player = state_machine.get_player()
	if player == null:
		return 0
	var centre: Vector2 = body.feet_position() + BixbyBeastArtLayout.local(CombinedLayout.SPIN_CENTRE)
	var to_player: Vector2 = player.global_position - centre
	if to_player.length() < 1.0:
		return 0
	var azimuth := CombinedLayout.floor_azimuth(to_player.angle())
	var frames: Array = BixbyBeastArtLayout.ANIMS[&"spin"].frames
	var best := 0
	var widest := -1.0
	for step in frames.size():
		var gap := INF
		for anchor in CombinedLayout.MOUTH_ANCHORS[frames[step]]:
			gap = minf(gap, absf(wrapf(azimuth - deg_to_rad(anchor[0]), -PI, PI)))
		if gap > widest:
			widest = gap
			best = step
	return best


func _stop_spin() -> void:
	if is_instance_valid(sweep):
		sweep.stop()
	sweep = null
	_start(Phase.SPIN_DOWN)
	body.play_anim(&"spin_down")


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
