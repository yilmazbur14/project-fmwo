extends State

# Attack 3 (addendum 3 B, and the wall of fire: the user's option A of 2026-10-04): the firestorm. On its own clock:
#   0               he blows (blow); on its BLOW frame (Layout.BLOW_FRAME, at once on the stand-in) a gust off his
#                   mouth, tornado_count tornados (LiamTornado) rise harmless in a line across the ring between the
#                   player and him (LiamFirestormLayout.wall_spots), and his downdraft blows down the ring: a player
#                   above downdraft_launch_above is thrown down to RESET_SPOT, and downdraft_speed holds them at the
#                   bottom every frame until the release
#   blow_time       he lights them (ignite): on its thrust (Layout.IGNITE_STREAK_FRAME) a streak of fire flies from his
#                   staff tip to each base, landing on IGNITION
#   IGNITION        (blow_time + ignite_time) they catch: their cores burn and their pull ramps in over
#                   tornado_pull_ramp, any ice melts out from each of them, the water boils off over firestorm_time as
#                   the steam thickens to steam_max over the same time, wisps rising; he channels. The pillar stays
#                   shielded
#   rings           tornado i's first fire ring (BixbyQuakeRingScript) at IGNITION + quake_first +
#                   LiamFirestormLayout.ring_phase(i) quake_interval, neighbours half a cycle apart so the line never
#                   has a gap to walk through, then one every quake_interval; each grows at quake_speed and dies at
#                   quake_max_radius round where its tornado was as it left, the tornado's spew just ahead of it
#                   (LiamTornado.spew_lead)
#   RELEASE         (IGNITION + wall_release) the downdraft lets go and the pillar opens, its shield bursting
#                   (LiamPillar.open_with_burst): the way to him is through the line of fire
#   BREAK           (RELEASE + wall_hold) the line breaks up, each tornado gliding out to its roam start
#                   (LiamFirestormLayout.START_ALONG) over wall_break_time, still burning and ringing
#   ROAM            from there to the burn-out they roam the track together at tornado_speed, each leaning up to
#                   tornado_lean off it toward the player (pushed down out of the front keep-out,
#                   LiamFirestormLayout.place), their pull, suction and wisps going with them and the melt trailing them
#   IGNITION + firestorm_time   burn-out: no more rings, the cores and the pull off at once, the tornados out over
#                   burnout_time, the rings still out put out, the steam held at steam_max; perch_idle
#   + burnout_time  the next attack
# While they burn, the pull drags the player (pull_at), except while a core's fling carries them, and ice the melt has
# taken lets go of them. The round's first pillar hit interrupts it: everything put out, the melt finished, the player's
# ice off, the steam held where it is; the water still boils off.

const LiamTornado := preload("res://Scripts/LiamTornado.gd")
const FirestormLayout := preload("res://Scripts/LiamFirestormLayout.gd")
const Layout := preload("res://Scripts/LiamArtLayout.gd")
const LiamElementFx := preload("res://Scripts/LiamElementFx.gd")
const BixbyQuakeRing := preload("res://Scripts/BixbyQuakeRingScript.gd")
const BixbySuction := preload("res://Scripts/BixbySuctionScript.gd")

const FIRE_QUAKE_ID := &"liam_fire_quake"
const POSITION_LOG_EVERY := 0.25

enum Beat { BLOW, IGNITE, BURN, BURNOUT }
enum WallStage { WALL, BREAK, ROAM }

var body: CharacterBody2D
var state_machine: Node
var running := false
var clock := 0.0
var beat := Beat.BLOW
var bases: Array = []
var tornados: Array[Node2D] = []
var rings: Array[Node2D] = []
var next_rings: Array[float] = []
var spewed: Array[bool] = []
var suction: Node2D
# When on its clock the blow's gust and the tornados come (the BLOW frame), and the streaks leave his staff.
var blow_at := 0.0
var blown := false
var streak_at := 0.0
var streaked := false
# The pull's ramp, 0 to 1, and its clock at IGNITION.
var ramp := 0.0
var ignition := 0.0
# For a test: its beats as they happen on its clock (ignite, ignition, burnout, done), and each ring sent [tornado, clock].
var beats := {}
var ring_log: Array = []
# Each tornado's distance round the track and its lean off it, and its travel since it last left a melt centre.
var along: Array[float] = []
var lean: Array[Vector2] = []
var stamp_travel: Array[float] = []
# For a test: every tornado's base every POSITION_LOG_EVERY s of the burn [clock, [bases]].
var positions: Array = []
var next_position_log := 0.0
# The wall: standing, breaking up or roaming; whether the downdraft has let go and whether it still holds the player
# down; its streaks; when the line breaks up, and where each tornado glides out from.
var wall := WallStage.WALL
var released := false
var drafting := false
var downdraft_fx: Node2D
var break_at := INF
var glide_from: Array = []


func Enter() -> void:
	var sm: Node = state_machine
	running = true
	clock = 0.0
	ramp = 0.0
	beat = Beat.BLOW
	beats.clear()
	ring_log.clear()
	tornados.clear()
	rings.clear()
	bases = FirestormLayout.wall_spots(sm.tornado_count)
	along.assign(FirestormLayout.starts(sm.tornado_count))
	wall = WallStage.WALL
	released = false
	drafting = false
	break_at = INF
	glide_from.clear()
	lean.clear()
	stamp_travel.clear()
	for i in bases.size():
		lean.append(Vector2.ZERO)
		stamp_travel.append(0.0)
	positions.clear()
	blown = false
	streaked = false
	body.pillar.set_shielded(true)
	body.play_anim(&"blow")
	blow_at = Layout.frame_start(&"blow", Layout.BLOW_FRAME)
	# No ice to melt (his test harness enters it straight): the player walks on dry mat.
	if not body.flood.is_iced():
		sm.set_player_ice(false)
	if blow_at <= 0.0:
		_blow()


func Exit() -> void:
	interrupt()


# Everything put out where it is; the melt finished, the player's ice off and the steam held. The water still boils
# off. Idempotent.
func interrupt() -> void:
	var was_running := running
	running = false
	ramp = 0.0
	_stop_downdraft()
	for tornado in tornados:
		if is_instance_valid(tornado):
			tornado.extinguish(state_machine.interrupt_burnout)
	tornados.clear()
	for ring in rings:
		if is_instance_valid(ring):
			ring.extinguish()
	rings.clear()
	_stop_suction()
	if not was_running:
		return
	if body.flood.is_melting():
		body.flood.finish_melt()
	state_machine.set_player_ice(false)
	body.steam.hold()


func Physics_Update(delta: float) -> void:
	if not running:
		return
	clock += delta
	var sm: Node = state_machine
	if drafting:
		var held: Node2D = sm.get_player()
		if held != null:
			held.add_drift(Vector2(0, sm.downdraft_speed))
	match beat:
		Beat.BLOW:
			if not blown and clock >= blow_at:
				_blow()
			if clock >= sm.blow_time:
				_light()
		Beat.IGNITE:
			if not streaked and clock >= streak_at:
				_streak()
			if clock >= sm.blow_time + sm.ignite_time:
				_ignition()
		Beat.BURN:
			if not released and clock >= ignition + sm.wall_release:
				_release()
			_form(delta)
			ramp = minf(ramp + delta / maxf(sm.tornado_pull_ramp, 0.001), 1.0)
			var player: Node2D = sm.get_player()
			if player != null:
				# Let go of while a core's fling carries them, or the pull would eat most of it back.
				if sm.carry_left <= 0.0:
					player.add_drift(pull_at(player.global_position))
				if player.on_ice and not body.flood.is_frozen_at(player.global_position):
					sm.set_player_ice(false)
			var lead := LiamTornado.spew_lead()
			for i in bases.size():
				if not spewed[i] and clock >= next_rings[i] - lead and next_rings[i] < ignition + sm.firestorm_time:
					spewed[i] = true
					if is_instance_valid(tornados[i]):
						tornados[i].spew()
				if clock >= next_rings[i]:
					_send_ring(i)
					next_rings[i] += sm.quake_interval
					spewed[i] = false
			rings.assign(rings.filter(func(ring) -> bool: return is_instance_valid(ring)))
			if clock >= ignition + sm.firestorm_time:
				_burn_out()
		Beat.BURNOUT:
			if clock >= ignition + sm.firestorm_time + sm.burnout_time:
				running = false
				beats[&"done"] = clock
				sm.attack_finished(self)


# Where the tornados stand this frame: still on the wall until BREAK, gliding out to their roam starts, then roaming.
func _form(delta: float) -> void:
	var sm: Node = state_machine
	match wall:
		WallStage.WALL:
			if released and clock >= break_at:
				wall = WallStage.BREAK
				beats[&"break"] = clock
				glide_from = bases.duplicate()
		WallStage.BREAK:
			var weight := minf((clock - break_at) / maxf(sm.wall_break_time, 0.001), 1.0)
			for i in bases.size():
				var to := FirestormLayout.track_point(along[i])
				_place_base(i, FirestormLayout.place(FirestormLayout.glide(glide_from[i], to, weight), sm))
			if weight >= 1.0:
				wall = WallStage.ROAM
				beats[&"roam"] = clock
		WallStage.ROAM:
			_move(delta)
			return
	_bases_moved()


# Every tornado a frame on round the track, leaning toward the player's feet, and everything that goes with them.
func _move(delta: float) -> void:
	var sm: Node = state_machine
	var player: Node2D = sm.get_player()
	for i in bases.size():
		along[i] += sm.tornado_speed * delta
		var on_track := FirestormLayout.track_point(along[i])
		var want := Vector2.ZERO
		if player != null:
			want = (player.global_position + FirestormLayout.FEET - on_track).limit_length(sm.tornado_lean)
		lean[i] = lean[i].move_toward(want, sm.tornado_lean_speed * delta)
		_place_base(i, FirestormLayout.place(on_track + lean[i], sm))
	_bases_moved()


# Tornado i's base moved to `at`, the tornado with it, and the melt it leaves behind as it goes.
func _place_base(i: int, at: Vector2) -> void:
	var was: Vector2 = bases[i]
	bases[i] = at
	if i < tornados.size() and is_instance_valid(tornados[i]):
		tornados[i].global_position = at
	if body.flood.is_melting():
		stamp_travel[i] += was.distance_to(at)
		if stamp_travel[i] >= FirestormLayout.MELT_STAMP:
			stamp_travel[i] = 0.0
			body.flood.add_melt_centre(at)


# What goes with the bases wherever they are: the suction's mouths, the steam's wisps, and the test's position log.
func _bases_moved() -> void:
	if is_instance_valid(suction):
		suction.mouths.assign(bases)
	body.steam.wisp_sources.assign(bases)
	if clock >= next_position_log:
		positions.append([clock, bases.duplicate()])
		next_position_log += POSITION_LOG_EVERY


# RELEASE: the downdraft lets go and the pillar opens; wall_hold later the line breaks up.
func _release() -> void:
	released = true
	beats[&"release"] = clock
	break_at = clock + state_machine.wall_hold
	_stop_downdraft()
	body.pillar.open_with_burst()


func _stop_downdraft() -> void:
	drafting = false
	if is_instance_valid(downdraft_fx):
		downdraft_fx.stop()
	downdraft_fx = null


# The tornados' pull on a player at `point` now: nothing before IGNITION or after the burn-out.
func pull_at(point: Vector2) -> Vector2:
	if ramp <= 0.0:
		return Vector2.ZERO
	return FirestormLayout.pull_field(point, state_machine, bases) * ramp


# The BLOW: his gust, and the tornados rising harmless at their spots.
func _blow() -> void:
	var sm: Node = state_machine
	blown = true
	LiamElementFx.blow_gust(body.fx_layer, body.pose_point(&"mouth", &"blow", Layout.BLOW_FRAME), body.facing_left)
	body.play_sfx(&"blow")
	body.play_sfx(&"tornado")
	var player: Node2D = sm.get_player()
	for base: Vector2 in bases:
		var tornado := LiamTornado.new()
		tornado.name = "Tornado%d" % tornados.size()
		tornado.host = sm
		tornado.player = player
		sm.add_hazard(tornado, body.get_parent())
		tornado.global_position = base
		tornados.append(tornado)
	beats[&"blow"] = clock
	_stop_downdraft()
	drafting = true
	downdraft_fx = LiamElementFx.downdraft(body.fx_layer, sm.downdraft_speed)
	if player != null and player.global_position.y < sm.downdraft_launch_above:
		sm.launch_player(sm.launch_spot(player.global_position))


func _light() -> void:
	var sm: Node = state_machine
	if not blown:
		_blow()
	beat = Beat.IGNITE
	beats[&"ignite"] = clock
	body.play_anim(&"ignite")
	body.play_sfx(&"ignite")
	streak_at = clock + minf(Layout.frame_start(&"ignite", Layout.IGNITE_STREAK_FRAME), sm.ignite_time)
	if streak_at <= clock:
		_streak()


# A streak of fire from his staff tip to each base, landing on IGNITION.
func _streak() -> void:
	var sm: Node = state_machine
	streaked = true
	var tip: Vector2 = body.pose_point(&"staff_tip", &"ignite", Layout.IGNITE_STREAK_FRAME)
	var flight: float = sm.blow_time + sm.ignite_time - clock
	for base: Vector2 in bases:
		LiamElementFx.fire_streak(body.fx_layer, tip, base, flight)


func _ignition() -> void:
	var sm: Node = state_machine
	beat = Beat.BURN
	ignition = clock
	next_position_log = clock
	beats[&"ignition"] = clock
	for tornado in tornados:
		if is_instance_valid(tornado):
			tornado.ignite()
	if body.flood.is_iced():
		body.flood.melt_from(bases, sm.melt_speed)
	body.flood.drain(sm.firestorm_time)
	body.steam.wisp_sources.assign(bases)
	body.steam.set_density(sm.steam_max, sm.firestorm_time)
	body.steam.set_wisps(true)
	_start_suction()
	body.play_anim(&"channel")
	next_rings.clear()
	spewed.clear()
	for i in bases.size():
		next_rings.append(ignition + sm.quake_first + FirestormLayout.ring_phase(bases.size(), i) * sm.quake_interval)
		spewed.append(false)


func _send_ring(i: int) -> void:
	var sm: Node = state_machine
	var ring := BixbyQuakeRing.new()
	ring.name = "FireQuake%d" % ring_log.size()
	ring.y_sort_enabled = true
	ring.speed = sm.quake_speed
	ring.radius = sm.quake_start_radius
	ring.attack_id = FIRE_QUAKE_ID
	ring.max_radius = sm.quake_max_radius
	ring.die_time = sm.quake_die_time
	ring.shown_rect = FirestormLayout.RING_SHOWN
	ring.hurt_rect = FirestormLayout.RING_HURT
	ring.player = sm.get_player()
	if Layout.own_ring_art():
		ring.sheet_path = Layout.FIRE_QUAKE_RING_SHEET
		ring.frames = Layout.strip_count(Layout.FIRE_QUAKE_RING_SHEET, Layout.FIRE_QUAKE_RING_FRAME)
		ring.rows = Layout.FIRE_QUAKE_RING_ROWS
	sm.add_hazard(ring, body.get_parent())
	ring.global_position = bases[i]
	rings.append(ring)
	ring_log.append([i, clock, bases[i]])
	body.play_sfx(&"quake")


func _burn_out() -> void:
	var sm: Node = state_machine
	beat = Beat.BURNOUT
	beats[&"burnout"] = clock
	ramp = 0.0
	_stop_downdraft()
	for tornado in tornados:
		if is_instance_valid(tornado):
			tornado.burn_out(sm.burnout_time)
	tornados.clear()
	for ring in rings:
		if is_instance_valid(ring):
			ring.extinguish()
	rings.clear()
	_stop_suction()
	body.steam.hold()
	body.play_anim(&"perch_idle")


# Streaks rushing at the tornados, most of them round the player (BixbySuctionScript with his settings).
func _start_suction() -> void:
	var sm: Node = state_machine
	_stop_suction()
	suction = BixbySuction.new()
	suction.name = "FirestormSuction"
	suction.player = sm.get_player()
	suction.mouths.assign(bases)
	suction.pull_speed = sm.tornado_pull
	suction.area = Layout.FLOOD_RECT
	suction.spec = Layout.WIND_STREAK
	suction.use_final = Layout.final_firestorm(Layout.WIND_STREAK.sheet)
	body.fx_layer.add_child(suction)


func _stop_suction() -> void:
	if is_instance_valid(suction):
		suction.stop()
	suction = null
