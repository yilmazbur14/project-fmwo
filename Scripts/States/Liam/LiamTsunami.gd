extends State

# Attack 1 (plan section 5): tsunami waves (LiamWave) down the ring from off the top of the screen, half the ring at a
# time, alternating sides, the first on the player's half. Each is wave_height tall and rolls at wave_speed, and each new
# one is placed wave_gap above the last one's top edge - not by a clock - so on every frame the gap between them is
# wave_gap, under a player's height, and nobody walks up through it: the way up is the seam's corners, a timed diagonal
# dash or a parry. They pass behind his row and come out of its foot. Each wave gets wave_tell of warning before its
# front crosses the top rope: its swell behind the rope, the red badge over its half, and his cast toward it.
# tsunami_time of waves (12 at the defaults), then the ones still rolling finish and the next attack starts. The pillar
# opens as the tsunami_gate_wave-th wave's front crashes on the bottom rope (the first's, the user's pick, 2026-10-04):
# opened with the first tell, a walk straight up the half the first wave isn't on punched the pillar 1.15 s in, before
# the second wave came out of the row's foot. From the crash on, every way up to the pillar crosses a wave.
# The round's first pillar hit interrupts it: no more waves, and every one still rolling collapses harmlessly. Every
# wave floods the ring by 1 / flood_waves as its front crashes on the bottom rope (or as it collapses short of it).

const LiamWave := preload("res://Scripts/LiamWave.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")
const Layout := preload("res://Scripts/LiamArtLayout.gd")

const WAVE_ID := &"liam_tsunami"

var body: CharacterBody2D
var state_machine: Node
var running := false
var waves: Array[Node2D] = []
var spawned := 0
var side := &"left"
var last_wave: Node2D
# For a test: each wave's side and the front it spawned at, and the state's clock when it did.
var spawn_log: Array[Dictionary] = []
var clock := 0.0
# The wave whose crash opens the pillar, and the clock when it did (-1 until then), for a test.
var gate_wave: Node2D
var opened_at := -1.0


func Enter() -> void:
	running = true
	clock = 0.0
	spawned = 0
	waves.clear()
	spawn_log.clear()
	last_wave = null
	opened_at = -1.0
	var player: Node2D = state_machine.get_player()
	side = &"left" if player == null or player.global_position.x < 960.0 else &"right"
	body.play_anim(&"perch_idle")
	body.pillar.set_shielded(true)
	gate_wave = null
	_spawn(spawn_front())


func Exit() -> void:
	interrupt()


func Physics_Update(delta: float) -> void:
	if not running:
		return
	clock += delta
	if opened_at < 0.0 and gate_wave != null and (not is_instance_valid(gate_wave) or gate_wave.spent):
		opened_at = clock
		body.pillar.open_with_burst()
	var next_front: float = last_wave.front_y - state_machine.wave_height - state_machine.wave_gap if is_instance_valid(last_wave) else 0.0
	if spawned < wave_count() and is_instance_valid(last_wave) and next_front >= spawn_front():
		_spawn(next_front)
	if spawned >= wave_count() and waves.all(func(wave): return not is_instance_valid(wave) or wave.finished):
		running = false
		state_machine.attack_finished(self)


# Stops it where it is: no more waves, the badge down, and every wave still rolling collapses harmlessly. Idempotent.
func interrupt() -> void:
	running = false
	ParryTell.clear(body)
	for wave in waves:
		if is_instance_valid(wave):
			wave.collapse(state_machine.wave_collapse_time)
	waves.clear()


# tsunami_time of waves, one a wave's height and its gap at its speed apart.
func wave_count() -> int:
	return roundi(state_machine.tsunami_time * state_machine.wave_speed / (state_machine.wave_height + state_machine.wave_gap))


# Where a wave's front starts: wave_tell above the top rope.
func spawn_front() -> float:
	return state_machine.ROPES.position.y - state_machine.wave_tell * state_machine.wave_speed


func _spawn(front: float) -> void:
	var wave := LiamWave.new()
	wave.name = "Wave%d" % spawned
	wave.side = side
	wave.front_y = front
	wave.height = state_machine.wave_height
	wave.speed = state_machine.wave_speed
	wave.carry_time = state_machine.wave_carry
	wave.rope_top = state_machine.ROPES.position.y
	wave.rope_bottom = state_machine.ROPES.end.y
	wave.player = state_machine.get_player()
	wave.host = state_machine
	wave.flood = body.flood
	wave.water_share = 1.0 / state_machine.flood_waves
	wave.fx_layer = body.fx_layer
	state_machine.add_hazard(wave, body.wave_layer)
	waves.append(wave)
	last_wave = wave
	spawned += 1
	if spawned == mini(state_machine.tsunami_gate_wave, wave_count()):
		gate_wave = wave
	spawn_log.append({"side": side, "front": front, "t": clock})
	var badge: Vector2 = Layout.WAVE_BADGE[side]
	var tell_time: float = (state_machine.ROPES.position.y - front) / state_machine.wave_speed
	ParryTell.telegraph(body, WAVE_ID, tell_time, func() -> Vector2: return badge)
	body.play_anim(&"cast_left" if side == &"left" else &"cast_right", &"perch_idle")
	body.play_sfx(&"wave")
	side = &"right" if side == &"left" else &"left"
