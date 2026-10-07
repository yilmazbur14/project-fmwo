extends "res://Scripts/States/JordanGod/JordanCombo.gd"

# Jordan's attack 3, Josh + Eric's portals: the user's own design (2026-09-28; every number is JordanPortalsLayout's).
# Josh casts a portal between them and Eric plunges his greatsword into it. From then on Josh's floor portals shoot the
# blade up round the player as fast spikes (JordanPortalSpike, placed by JordanPortalSpikes), and Josh ports Eric to the
# centre, where for PHASE_TIME he spams his full-screen bear hug - the red badge every time, always parryable, a parry
# never opening him up - Josh porting him on after every grab, already charging, and now and then pulling him out of his
# own lunge into a closer exit (the feint). Then Josh brings him home, both recover, and the player walks into either
# one's reach for the three punches and the three-bar mash, every bar one off Jordan.
#
# THE BEATS: the summon and the opening - Josh's cast, the sword portal, the plunge, the spikes starting, the port to the
# centre - are a coroutine (run) on the combo's own waits; the grab loop, the feint, the holds, the end and every spike
# are beats on Physics_Update, so every timing in them is game time, a physics step at a time; then the coroutine again
# for the payoff and the wrap. A run left behind by a cut never resumes into the next one (generation).
#
# THE PLAYER is free all through it - walking, the parry, the dash - and the HUD stays up. Only a player standing where
# the puppets, the sword portal or Eric's first arrival would cover them (START_CLEAR) is warped first, to the nearest
# clear spot, and let go as the summon starts. Eric's grab reaches them through receive_hit off his own sprite, its
# origin their hurtbox centre, so any facing parries it; a parry never staggers him (the puppet has no
# can_parry_stagger) and only flashes him.
#
# ERIC never flips. His frames draw the planted sword while he holds it (the plunge, the plant) and while he leans on it
# winded: then the prop is hidden and his clip leaves the prop's dirt out (and, under the drawn portal's collar, the
# blade's foot: NOTCHES); the rest of the time the prop stands in the sword portal.

const Layout := preload("res://Scripts/JordanPortalsLayout.gd")
const Spikes := preload("res://Scripts/JordanPortalSpikes.gd")
const PortalScript := preload("res://Scripts/JordanPortal.gd")
const SpikeScript := preload("res://Scripts/JordanPortalSpike.gd")
const EricArtLayout := preload("res://Scripts/EricArtLayout.gd")
const FinisherArtLayout := preload("res://Scripts/FinisherArtLayout.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const PlayerScript := preload("res://Scripts/PlayerScript.gd")

const JOSH := &"josh"
const ERIC := &"eric"
const HUG_SHEET := "eric_bearhug_v2"
const WINDED_SHEET := "eric_winded"
# The bear-hug frames that draw the planted sword.
const PLANTED_FRAMES: Array[int] = [0, 13]
# A float clock summed a step at a time lands a hair short of a beat's end.
const STEP_TOLERANCE := 0.0001

# Both recovering, then the player in reach of one of them.
signal stage_ended

enum Beat { OFF, OPENING, PHASE, ENDING, WALK, PAYOFF }
enum Move { NONE, PLANT, HOP_OPEN, HOP_SINK, HOP_TELL, HOP_RISE, CHARGE, RUSH, CONTACT, DIVE, UNDER, WHIFF, STUMBLE, GRAB,
	SQUEEZE, TOSS, TOSS_END, HOME }

var rng := RandomNumberGenerator.new()
# A test's: the rushes (0 the phase's first) that feint whatever the roll, where there is an exit for them.
var pinned_feint: Array[int] = []
var generation := 0
var beat := Beat.OFF
# The player is down: nothing more happens, and the fight's end releases this.
var stopped := false
# From the summon's end, in game seconds; the phase clock from Eric's first rise at the centre.
var portals_clock := 0.0
var phase_clock := 0.0
var phase_on := false
var josh: Node2D
var eric: Node2D
var target: Node2D
var bars := -1
var hits := 0

var move := Move.NONE
var move_clock := 0.0
var move_time := 0.0
# The hop under way: {timing, to, charges, reroute}.
var hop := {}
var sink_from := 0.0
var entry: Node2D
var exit_portal: Node2D
var charging := false
var charge_left := 0.0
var feint_planned := false
var rerouted := false
var feint_count := 0
var rush := {}
var rush_t0 := 0.0
var rush_clock := 0.0
var rush_end := 0.0
var feint_on := false
var entry_point := Vector2.INF
var exit_point := Vector2.INF
# rush_clock as he bursts out of a feint's exit, or -1.
var burst_at := -1.0
var rearmed := false
var holding := false
var squeezes_left := 0
var recoiling := false
var recoil_from := Vector2.ZERO
var recoil_dir := Vector2.RIGHT
var stumble_for := 0.0

var sword_portal: Node2D
var sword_planted := false
var prop: Sprite2D
var live_spikes: Array = []
var spike_records := {}
# The stand-in blade, cut once for every spike until the drawn one is in.
var blade_cut: Texture2D
var spikes_on := false
var next_wave_at := 0.0
var waves := 0
var stars := {}
var stars_clock := 0.0
var sounds := {}

# For tests, times on portals_clock unless they say phase: every rush {index, start (phase), at, feint, from, exit, contact
# (phase), contact_at, result, rearmed_at, held_at, held_from, held_to}; every spike {opened, erupted, sucked,
# retracted, aimed, at, hit, rows, live_from, live_to}; every feint {rush, entry, exit, entry_at, exit_at, burst_at}; every hop {from, at, charges, reroute, to,
# player (their soles as he rose), rose_at, badge (up as he rose)}; and how the phase ended {at (phase), clock, move,
# cancelled, recovered_at}.
var rushes: Array[Dictionary] = []
# {from, to}: the player's soles warped clear at the start, or empty when they stood clear.
var start_warp := {}
var spikes: Array[Dictionary] = []
var feints: Array[Dictionary] = []
var hops: Array[Dictionary] = []
var ending := {}


func _init() -> void:
	rng.randomize()


func pair() -> Array[Dictionary]:
	return [
		{boss = JOSH, feet = Layout.JOSH_FEET, face_left = false, hand = &"left", hooks = [&"back"], strings = 2},
		{boss = ERIC, feet = Layout.ERIC_FEET, face_left = false, hand = &"right", hooks = [&"back"], strings = 2},
	]


func run() -> void:
	generation += 1
	var run_of := generation
	_start()
	var body := player()
	if body != null:
		var start := Spikes.start_spot(_soles(), body.ring_origins)
		if start != _soles():
			start_warp = {from = _soles(), to = start}
			warp_player(start, PlayerScript.Facing.UP)
			await wait(Layout.WARP_TIME)
			if _gone(run_of):
				return
			body.unlock_actions()
	_wall_no_stand()
	await summon()
	if _gone(run_of):
		return
	josh = puppets.get(JOSH)
	eric = puppets.get(ERIC)
	_build_sounds()
	_watch_hits(true)
	beat = Beat.OPENING
	josh.play(&"cast")
	god.play(&"yank_left", &"control")
	await wait(Layout.CAST_RELEASE)
	if _gone(run_of):
		return
	_open_sword_portal()
	await wait(Layout.PLUNGE_AT - Layout.CAST_RELEASE)
	if _gone(run_of):
		return
	_plunge()
	await wait(Layout.PLUNGE_ENTER)
	if _gone(run_of):
		return
	_blade_in()
	await wait(Layout.SPIKES_AT - Layout.PLUNGE_AT - Layout.PLUNGE_ENTER)
	if _gone(run_of):
		return
	_start_spikes()
	await wait(Layout.TO_CENTRE_AT - Layout.SPIKES_AT)
	if _gone(run_of):
		return
	_hop(Layout.TO_CENTRE, Layout.STAGE_CENTRE, true)
	await stage_ended
	if _gone(run_of):
		return
	await stage_ended
	if _gone(run_of):
		return
	bars = await punch_out(target)
	if _gone(run_of):
		return
	await _wrap(run_of)


func release() -> void:
	generation += 1
	beat = Beat.OFF
	move = Move.NONE
	phase_on = false
	spikes_on = false
	_let_go()
	# His defeat may take him standing in his notch (JordanCombo.adopt_puppets): he crumples whole.
	if is_instance_valid(eric) and eric.is_clipped() and _depth_now() == 0.0:
		eric.set_clipped(false)
	_watch_hits(false)
	_clear_stars()
	for voices in sounds.values():
		for voice: AudioStreamPlayer in voices:
			voice.stop()
	super.release()
	live_spikes.clear()
	spike_records.clear()
	stage_ended.emit()


func Physics_Update(delta: float) -> void:
	super.Physics_Update(delta)
	if beat == Beat.OFF or cut or stopped:
		return
	if _player_down():
		stopped = true
		_let_go()
		return
	portals_clock += delta
	if phase_on:
		phase_clock += delta
	_run_spikes(delta)
	_run_eric(delta)
	match beat:
		Beat.PHASE:
			if phase_clock >= Layout.PHASE_TIME - STEP_TOLERANCE:
				_end_phase()
		Beat.ENDING:
			if move == Move.HOME and live_spikes.is_empty():
				_recover()
		Beat.WALK:
			var reached := _reached()
			if reached != null:
				_take(reached)
		Beat.PAYOFF:
			# The finisher's own stars take over as it dazes the one taken.
			if is_instance_valid(target) and stars.has(target.boss) and player().finisher.is_active():
				stars[target.boss].queue_free()
				stars.erase(target.boss)
	_sync_prop()
	_spin_stars(delta)


# For tests: when the rush under way lands, on portals_clock, or -1 with none.
func rush_contact_at() -> float:
	match move:
		Move.RUSH, Move.DIVE, Move.UNDER:
			return rush_t0 + (Layout.FEINT_TOTAL if feint_on else Layout.RUSH_TIME)
		Move.CONTACT:
			return portals_clock - move_clock
	return -1.0


func _start() -> void:
	Layout.assert_invariants()
	beat = Beat.OFF
	stopped = false
	portals_clock = 0.0
	phase_clock = 0.0
	phase_on = false
	josh = null
	eric = null
	target = null
	bars = -1
	hits = 0
	move = Move.NONE
	move_clock = 0.0
	move_time = 0.0
	hop = {}
	entry = null
	exit_portal = null
	charging = false
	charge_left = 0.0
	feint_planned = false
	rerouted = false
	feint_count = 0
	rush = {}
	feint_on = false
	entry_point = Vector2.INF
	exit_point = Vector2.INF
	burst_at = -1.0
	rearmed = false
	holding = false
	recoiling = false
	sword_portal = null
	sword_planted = false
	prop = null
	live_spikes.clear()
	spike_records.clear()
	spikes_on = false
	next_wave_at = 0.0
	waves = 0
	stars.clear()
	stars_clock = 0.0
	rushes.clear()
	start_warp = {}
	spikes.clear()
	feints.clear()
	hops.clear()
	ending = {}


func _gone(run_of: int) -> bool:
	return cut or run_of != generation


func _player_down() -> bool:
	var body := player()
	return body == null or body.playerHealth <= 0 or body.fight_over


#THE OPENING

# The no-stand zones walled off for the attack (JordanPortalsLayout.no_stand_zones), off the player's own collision box.
func _wall_no_stand() -> void:
	var body := player()
	if body == null:
		return
	var shape: CollisionShape2D = body.get_node("CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	var walls := StaticBody2D.new()
	walls.name = "NoStandWalls"
	walls.collision_layer = 1
	walls.collision_mask = 0
	for rect in Layout.no_stand_walls(Rect2(box.position - _soles(), box.size)):
		var piece := CollisionShape2D.new()
		var square := RectangleShape2D.new()
		square.size = rect.size
		piece.shape = square
		piece.position = rect.get_center()
		walls.add_child(piece)
	add_hazard(walls, Vector2.ZERO, god.layer(&"floor"))


func _open_sword_portal() -> void:
	sword_portal = PortalScript.make(&"sword", god.layer(&"stage"))
	add_hazard(sword_portal, Layout.SWORD_PORTAL, god.layer(&"floor"))
	sword_portal.open()
	_sound(&"portal")


func _plunge() -> void:
	_notch(&"plant")
	eric.play(&"plunge", &"plant")


# The plunge's frame 13: the blade goes into the portal.
func _blade_in() -> void:
	sword_planted = true
	move = Move.PLANT
	_plant_prop()
	if is_instance_valid(sword_portal):
		sword_portal.burst()
	_sound(&"plunge")
	var shake: Dictionary = Layout.PLUNGE_SHAKE
	ScreenView.shake(get_tree(), shake.strength, shake.steps, shake.step)


func _start_spikes() -> void:
	josh.play(&"wild_hold")
	spikes_on = true
	next_wave_at = portals_clock


#THE PLANTED SWORD

func _plant_prop() -> void:
	prop = Sprite2D.new()
	prop.name = "PlantedSword"
	prop.texture = load(Layout.PLANTED_SWORD)
	prop.centered = false
	prop.region_enabled = true
	prop.scale = Vector2.ONE * Layout.SCALE
	_cut_prop(Layout.PLANTED_REGION.size.y)
	prop.visible = false
	add_hazard(prop, Layout.SWORD_PORTAL, god.layer(&"stage"))


# The prop's top `rows` rows standing on the floor line: all of it, or less as it goes back in.
func _cut_prop(rows: float) -> void:
	var region: Rect2 = Layout.PLANTED_REGION
	var shown := roundf(clampf(rows, 0.0, region.size.y))
	prop.region_rect = Rect2(region.position, Vector2(region.size.x, shown))
	prop.offset = Vector2(region.position.x - Layout.SWORD_BASE_TEXEL.x, -shown)


func _sync_prop() -> void:
	if is_instance_valid(prop):
		prop.visible = sword_planted and prop.region_rect.size.y > 0.0 and not _eric_shows_sword()


func _eric_shows_sword() -> bool:
	if not is_instance_valid(eric) or eric.sprite.texture == null or eric.is_juggled():
		return false
	var sheet: String = eric.sprite.texture.resource_path.get_file().get_basename()
	return sheet == WINDED_SHEET or (sheet == HUG_SHEET and PLANTED_FRAMES.has(eric.sprite.frame))


# His clip: his soles' line, less where his frame draws the planted sword's dirt (and, under the drawn portal's collar,
# the blade's foot).
func _notch(pose: StringName) -> void:
	var drawn: bool = is_instance_valid(sword_portal) and sword_portal.drawn
	var outline: Array = Layout.NOTCHES[pose].collar if drawn else Layout.NOTCHES[pose].floor
	var above: Rect2 = JordanPuppet.ABOVE_FLOOR
	var points := PackedVector2Array([above.position, Vector2(above.end.x, above.position.y), above.end])
	for texel: Vector2 in outline:
		points.append((texel - Layout.FEET_ANCHOR) * Layout.SCALE)
	points.append(Vector2(above.position.x, above.end.y))
	eric.set_clipped(true)
	eric.mask.polygon = points


#THE PORTALS

func _open_body_portal(at: Vector2, fast := false) -> Node2D:
	var portal: Node2D = PortalScript.make(&"body", god.layer(&"stage"))
	add_hazard(portal, at, god.layer(&"floor"))
	portal.open(fast)
	_sound(&"portal")
	return portal


func _close(portal: Node2D) -> void:
	if is_instance_valid(portal):
		portal.close()


#THE SPIKES

func _run_spikes(delta: float) -> void:
	for i in range(live_spikes.size() - 1, -1, -1):
		var spike: Node2D = live_spikes[i]
		if not is_instance_valid(spike):
			live_spikes.remove_at(i)
			continue
		spike.step(delta)
		var record: Dictionary = spike_records.get(spike, {})
		if record.erupted < 0.0 and spike.rose:
			record.erupted = portals_clock
			_sound(&"spike_burst")
		if record.sucked < 0.0 and spike.rose and spike.stage >= SpikeScript.Stage.SUCK:
			record.sucked = portals_clock
			_sound(&"spike_suck")
		if spike.struck >= 0:
			record.hit = spike.struck
		if spike.stage == SpikeScript.Stage.DONE:
			spike_records.erase(spike)
			spike.queue_free()
			live_spikes.remove_at(i)
	if spikes_on and portals_clock >= next_wave_at - STEP_TOLERANCE:
		next_wave_at += Layout.WAVE_EVERY
		_wave()


# The next wave round the player: the patterns in turn, the other where the turn's places nothing.
func _wave() -> void:
	var p := player()
	var soles := _soles()
	var held := soles if p.is_grabbed else Vector2.INF
	var room := Layout.MAX_LIVE - live_spikes.size()
	var points := _spike_points()
	var fixed: Array = [Layout.SWORD_PORTAL]
	var aim_ok := _aim_ok()
	var pattern: StringName = Layout.PATTERNS[waves % Layout.PATTERNS.size()]
	var exits: Array = [exit_portal.global_position] if is_instance_valid(exit_portal) else []
	var placed := Spikes.wave(rng, pattern, soles, points, fixed, room, aim_ok, held, p.ring_origins, exits)
	if placed.is_empty():
		var other: StringName = Layout.PATTERNS[(waves + 1) % Layout.PATTERNS.size()]
		placed = Spikes.wave(rng, other, soles, points, fixed, room, aim_ok, held, p.ring_origins, exits)
	waves += 1
	for spot in placed:
		_open_spike(spot.at, spot.aimed)
	if not placed.is_empty() and is_instance_valid(josh):
		josh.play(&"flick", &"wild_hold")


func _open_spike(at: Vector2, aimed: bool) -> void:
	var portal: Node2D = PortalScript.make(&"spike", god.layer(&"stage"))
	add_hazard(portal, at, god.layer(&"floor"))
	portal.open()
	if blade_cut == null and not Layout.final_blade():
		blade_cut = SpikeScript.cut_stand_in()
	var spike: Node2D = SpikeScript.new()
	spike.name = "Spike"
	spike.stand_in_blade = blade_cut
	spike.portal = portal
	spike.player = player()
	spike.aimed = aimed
	spike.rows = Spikes.blade_rows(at)
	spike.smear_rows = Spikes.smear_rows(at)
	add_hazard(spike, at, god.layer(&"stage"))
	live_spikes.append(spike)
	var live_from := portals_clock + Layout.SPIKE_TELL
	var record := {opened = portals_clock, erupted = -1.0, sucked = -1.0, retracted = -1.0, aimed = aimed, at = at, hit = -1,
		rows = spike.rows, live_from = live_from, live_to = live_from + Layout.SPIKE_RISE + Layout.SPIKE_HOLD}
	spikes.append(record)
	spike_records[spike] = record
	_sound(&"portal")


func _spike_points() -> Array:
	var out: Array = []
	for spike: Node2D in live_spikes:
		if is_instance_valid(spike):
			out.append(spike.global_position)
	return out


# Rule c: an aimed spike opened now keeps its live window out of AIM_CLEAR round every grab that may land meanwhile.
func _aim_ok() -> bool:
	var live_from := portals_clock + Layout.SPIKE_TELL
	var live_to := live_from + Layout.SPIKE_RISE + Layout.SPIKE_HOLD
	for contact in _contacts():
		if live_from <= contact + Layout.AIM_CLEAR.y and live_to >= contact - Layout.AIM_CLEAR.x:
			return false
	return true


# When the grabs coming up land, on portals_clock: every candidate where the next one's feint isn't known yet. Only what
# can land within a spike's life matters; a hold or a whiff puts the next one further off than that.
func _contacts() -> Array[float]:
	var out: Array[float] = []
	var left := maxf(move_time - move_clock, 0.0)
	match move:
		Move.CONTACT:
			out.append(portals_clock - move_clock)
		Move.RUSH, Move.DIVE, Move.UNDER:
			out.append(rush_t0 + (Layout.FEINT_TOTAL if feint_on else Layout.RUSH_TIME))
			if move == Move.RUSH and feint_planned and Layout.FEINT_MODE == &"lunge":
				out.append(rush_t0 + Layout.FEINT_TOTAL)
		Move.CHARGE:
			_charge_contacts(out, portals_clock + charge_left, false)
		Move.HOP_OPEN, Move.HOP_SINK, Move.HOP_TELL, Move.HOP_RISE:
			if hop.get("charges", false):
				var rise_in := 0.0
				if move == Move.HOP_OPEN:
					rise_in = left + hop.timing.sink + hop.timing.tell
				elif move == Move.HOP_SINK:
					rise_in = left + hop.timing.tell
				elif move == Move.HOP_TELL:
					rise_in = left
				if hop.reroute or charging:
					_charge_contacts(out, portals_clock + rise_in + charge_left, false)
				else:
					_charge_contacts(out, portals_clock + rise_in + Layout.CHARGE_TIME, true)
	return out


func _charge_contacts(out: Array[float], rush_at: float, unknown: bool) -> void:
	out.append(rush_at + Layout.RUSH_TIME)
	if not (unknown or feint_planned):
		return
	if Layout.FEINT_MODE == &"lunge":
		out.append(rush_at + Layout.FEINT_TOTAL)
	elif not rerouted:
		out.append(rush_at + Layout.REROUTE.open + Layout.REROUTE.sink + Layout.REROUTE.tell + Layout.RUSH_TIME)


#ERIC

func _set_move(next: Move, seconds: float) -> void:
	move = next
	move_clock = 0.0
	move_time = seconds


func _done() -> bool:
	return move_clock >= move_time - STEP_TOLERANCE


func _t() -> float:
	return clampf(move_clock / move_time, 0.0, 1.0) if move_time > 0.0 else 1.0


func _run_eric(delta: float) -> void:
	if not is_instance_valid(eric) or move == Move.NONE or move == Move.PLANT or move == Move.HOME:
		return
	move_clock += delta
	match move:
		Move.HOP_OPEN:
			if _done():
				_hop_sink()
		Move.HOP_SINK:
			_depth(lerpf(sink_from, Layout.HOP_DEPTH, _ease_in(_t())))
			if _done():
				_hop_under()
		Move.HOP_TELL:
			if _done():
				_hop_rise()
		Move.HOP_RISE:
			_depth(Layout.HOP_DEPTH * (1.0 - _ease_out(_t())))
			if charging:
				charge_left -= delta
			if _done():
				_hop_risen()
		Move.CHARGE:
			charge_left -= delta
			if _reroute_due():
				_reroute()
			elif charge_left <= STEP_TOLERANCE:
				_rush()
		Move.RUSH:
			_rush_step(delta)
		Move.CONTACT:
			_contact_step()
		Move.DIVE:
			rush_clock += delta
			_depth(Layout.HOP_DEPTH * _ease_in(_t()))
			_rearm()
			if rush_clock >= Layout.FEINT_ENTER + Layout.FEINT_DIVE - STEP_TOLERANCE:
				_under()
		Move.UNDER:
			rush_clock += delta
			_rearm()
			if rush_clock >= Layout.FEINT_ENTER + Layout.EXIT_TELL - STEP_TOLERANCE:
				_burst_out()
		Move.WHIFF:
			if recoiling:
				_place_eric(recoil_from + recoil_dir * Layout.PARRY_RECOIL * _ease_out(_t()))
			if _done():
				_stumble()
		Move.STUMBLE:
			if _done():
				_after_attack()
		Move.GRAB:
			if _done():
				_squeeze()
		Move.SQUEEZE:
			if _done():
				if squeezes_left > 0:
					_squeeze()
				else:
					_toss()
		Move.TOSS:
			if _done():
				_release_player()
				rush.held_to = portals_clock
				_sound(&"toss")
				eric.play(&"toss_end")
				_set_move(Move.TOSS_END, Layout.TOSS_END_TIME)
		Move.TOSS_END:
			if _done():
				_after_attack()
	if holding:
		_hold_player()


# Josh ports him: a body portal opens under him, he sinks through it, the exit opens at `to` (picked as it opens, off
# the player's soles then, when INF), and he rises out of it - charging, when `charges`. A `reroute` is the charge
# feint's: fast in, and his charge held while he is under.
func _hop(timing: Dictionary, to: Vector2, charges: bool, reroute := false) -> void:
	hop = {timing = timing, to = to, charges = charges, reroute = reroute}
	sink_from = _depth_now()
	_set_move(Move.HOP_OPEN, timing.open)
	_close(entry)
	entry = _open_body_portal(eric.global_position, reroute)
	god.play(&"yank_right", &"control")
	god.layer(&"strings").set_tension(eric, GodLayout.TENSION_YANK, 0.0)
	_sound(&"hop")
	hops.append({from = eric.global_position, at = portals_clock, charges = charges, reroute = reroute, to = to,
		player = Vector2.INF, rose_at = -1.0, badge = false})


# He leaves his sword planted: the prop stands in for it from here.
func _hop_sink() -> void:
	_set_move(Move.HOP_SINK, hop.timing.sink)
	if _eric_shows_sword():
		eric.play(&"empty")
	eric.set_clipped(true)


func _hop_under() -> void:
	_close(entry)
	entry = null
	var to: Vector2 = hop.to
	if not to.is_finite():
		to = Spikes.hop_spot(rng, _soles(), _spike_points())
	eric.global_position = to
	_depth(Layout.HOP_DEPTH)
	_clear_exit(to)
	exit_portal = _open_body_portal(to)
	hops[-1].to = to
	_set_move(Move.HOP_TELL, hop.timing.tell)


func _hop_rise() -> void:
	_set_move(Move.HOP_RISE, hop.timing.rise)
	if not hop.charges:
		eric.play(&"empty")
	elif not hop.reroute:
		_begin_charge()
	hops[-1].player = _soles()
	hops[-1].rose_at = portals_clock
	hops[-1].badge = _badge_up()


func _hop_risen() -> void:
	_depth(0.0)
	eric.set_clipped(false)
	_close(exit_portal)
	exit_portal = null
	god.layer(&"strings").set_tension(eric, GodLayout.TENSION_WORK)
	if not hop.charges:
		_set_move(Move.HOME, 0.0)
	elif charge_left <= STEP_TOLERANCE:
		_rush()
	else:
		_set_move(Move.CHARGE, 0.0)


# As he starts to rise: the badge, and whether the rush it ends in feints. The first one starts the phase.
func _begin_charge() -> void:
	charging = true
	charge_left = Layout.CHARGE_TIME
	rerouted = false
	var index := rushes.size()
	var last: bool = not rushes.is_empty() and rushes[-1].feint
	feint_planned = pinned_feint.has(index) or Spikes.feint_roll(rng, index, last, feint_count)
	eric.play(Layout.charge_anim())
	_telegraph(_head_anchor)
	if not phase_on and beat == Beat.OPENING:
		beat = Beat.PHASE
		phase_on = true
		phase_clock = 0.0


func _telegraph(anchor: Callable) -> void:
	ParryTell.telegraph(eric, Layout.GRAB_ID, Layout.BADGE_HOLD, anchor)
	var tell := eric.get_parent().get_node_or_null("ParryTell%d" % eric.get_instance_id())
	if tell != null:
		tell.scale = Vector2.ONE * GodLayout.ui_scale()


func _badge_up() -> bool:
	return eric.get_parent().get_node_or_null("ParryTell%d" % eric.get_instance_id()) != null


func _head_anchor() -> Vector2:
	return eric.global_position + Layout.tell_offset()


func _exit_anchor(at: Vector2) -> Vector2:
	return at + Layout.tell_offset()


# FEINT_MODE &"charge": REROUTE.at into the charge, Josh takes him under and out near the player, the badge on him.
func _reroute_due() -> bool:
	return Layout.FEINT_MODE == &"charge" and feint_planned and not rerouted \
		and Layout.CHARGE_TIME - charge_left >= Layout.REROUTE.at - STEP_TOLERANCE


func _reroute() -> void:
	rerouted = true
	feint_planned = false
	var exit := Spikes.feint_exit(rng, _soles(), eric.global_position)
	if not exit.is_finite():
		rerouted = false
		return
	feint_count += 1
	feints.append({rush = rushes.size(), entry = eric.global_position, exit = exit, entry_at = portals_clock,
		exit_at = portals_clock + Layout.REROUTE.open + Layout.REROUTE.sink, burst_at = -1.0})
	_hop(Layout.REROUTE, exit, true, true)


# The badge clears: his grab box homes on the player's hurtbox centre and reaches it RUSH_TIME later from anywhere.
func _rush() -> void:
	ParryTell.clear(eric)
	charging = false
	rush_t0 = portals_clock
	rush_clock = 0.0
	rush_end = Layout.RUSH_TIME
	feint_on = false
	entry_point = Vector2.INF
	exit_point = Vector2.INF
	burst_at = -1.0
	rearmed = false
	var rerouted_here := rerouted and Layout.FEINT_MODE == &"charge"
	rush = {index = rushes.size(), start = phase_clock, at = portals_clock, feint = rerouted_here, from = eric.global_position,
		exit = hops[-1].to if rerouted_here else Vector2.INF, contact = -1.0, contact_at = -1.0, result = -1, rearmed_at = -1.0,
		held_at = Vector2.INF, held_from = -1.0, held_to = -1.0}
	rushes.append(rush)
	eric.play(&"rush")
	_sound(&"rush")
	_set_move(Move.RUSH, Layout.RUSH_TIME)


func _rush_step(delta: float) -> void:
	rush_clock += delta
	if feint_planned and Layout.FEINT_MODE == &"lunge" and burst_at < 0.0 \
			and rush_clock >= Layout.FEINT_ENTRY_OPEN - STEP_TOLERANCE:
		feint_planned = false
		_open_entry()
	if entry_point.is_finite():
		var to_entry := maxf(Layout.FEINT_ENTER - rush_clock, delta)
		eric.global_position = eric.global_position.move_toward(entry_point,
			eric.global_position.distance_to(entry_point) / to_entry * delta)
		if rush_clock >= Layout.FEINT_ENTER - STEP_TOLERANCE:
			_dive()
		return
	if burst_at >= 0.0 and eric.is_clipped():
		var out := (rush_clock - burst_at) / Layout.FEINT_RISE
		_depth(Layout.HOP_DEPTH * (1.0 - _ease_out(out)))
		if out >= 1.0:
			eric.set_clipped(false)
			_close(exit_portal)
			exit_portal = null
	var aim := _hurt_centre() - Layout.GRAB_OFFSET
	var left := maxf(rush_end - rush_clock, delta)
	_place_eric(eric.global_position.move_toward(aim, eric.global_position.distance_to(aim) / left * delta))
	if rush_clock >= rush_end - STEP_TOLERANCE:
		_contact()


# The feint: Josh's entry opens on his path, where he will be at FEINT_ENTER, and the exit is picked; with none there
# is no feint and the rush lands as promised.
func _open_entry() -> void:
	exit_point = Spikes.feint_exit(rng, _soles(), eric.global_position)
	if not exit_point.is_finite():
		return
	feint_on = true
	feint_count += 1
	rush.feint = true
	rush.exit = exit_point
	var aim := _hurt_centre() - Layout.GRAB_OFFSET
	var share := (Layout.FEINT_ENTER - Layout.FEINT_ENTRY_OPEN) / (Layout.RUSH_TIME - Layout.FEINT_ENTRY_OPEN)
	entry_point = eric.global_position.lerp(aim, share).round()
	_close(entry)
	entry = _open_body_portal(entry_point, true)
	feints.append({rush = rush.index, entry = entry_point, exit = exit_point, entry_at = portals_clock, exit_at = -1.0,
		burst_at = -1.0})


func _dive() -> void:
	entry_point = Vector2.INF
	eric.set_clipped(true)
	_set_move(Move.DIVE, Layout.FEINT_DIVE)
	_clear_exit(exit_point)
	exit_portal = _open_body_portal(exit_point)
	_telegraph(_exit_anchor.bind(exit_point))
	feints[-1].exit_at = portals_clock


func _under() -> void:
	_close(entry)
	entry = null
	eric.global_position = exit_point
	_depth(Layout.HOP_DEPTH)
	_set_move(Move.UNDER, 0.0)


# The promised contact: a press made on it is let off the mash lockout, so the real grab can still be parried with the
# next one. It still pays its whiff.
func _rearm() -> void:
	if rearmed or rush_clock < Layout.REARM_AT - STEP_TOLERANCE:
		return
	rearmed = true
	player().defense.rearm_parry()
	rush.rearmed_at = portals_clock


func _burst_out() -> void:
	ParryTell.clear(eric)
	burst_at = rush_clock
	rush_end = Layout.FEINT_TOTAL
	feints[-1].burst_at = portals_clock
	eric.play(&"rush")
	_sound(&"rush")
	_set_move(Move.RUSH, Layout.RUSH_TIME)


func _contact() -> void:
	_set_move(Move.CONTACT, Layout.RUSH_HOT)
	rush.contact = phase_clock
	rush.contact_at = portals_clock
	_contact_step()


# His arms are live for RUSH_HOT: a HIT holds them, a parry sends him off, and nothing (i-frames, or them out of his
# box) is a miss.
func _contact_step() -> void:
	var p := player()
	if _grab_box().intersects(_player_box()):
		var result: int = p.receive_hit(HitInfo.make(Layout.GRAB_ID, eric.sprite, _hurt_centre(), eric))
		rush.result = result
		if result == HitInfo.Result.HIT:
			_grab()
			return
		if result == HitInfo.Result.PARRIED:
			_whiff(true)
			return
	if _done():
		if int(rush.result) < 0:
			rush.result = HitInfo.Result.IGNORED
		_whiff(false)


func _whiff(parried: bool) -> void:
	eric.play(&"whiff")
	_set_move(Move.WHIFF, Layout.WHIFF_TIME)
	recoiling = parried
	stumble_for = Layout.STUMBLE_PARRIED if parried else Layout.STUMBLE_IGNORED
	if parried:
		recoil_from = eric.global_position
		var away: Vector2 = eric.global_position - player().global_position
		recoil_dir = away.normalized() if away.length() > 1.0 else Vector2.RIGHT


# An exit reads clean under its badge: spikes still in their tell round it are called off as it opens, and no new one
# opens there while it shows (_wave).
func _clear_exit(at: Vector2) -> void:
	_retract_near(at, Layout.HOP_SPIKE_CLEAR)


func _retract_near(at: Vector2, reach: float) -> void:
	for spike: Node2D in live_spikes:
		if is_instance_valid(spike) and spike.stage == SpikeScript.Stage.TELL and spike.global_position.distance_to(at) < reach:
			spike.retract()
			spike_records[spike].retracted = portals_clock


func _stumble() -> void:
	recoiling = false
	eric.play(&"stumble")
	_set_move(Move.STUMBLE, stumble_for)


func _grab() -> void:
	# Rule d: the hold stays clear. A spike still in its tell there is called off before its blade can rise through it.
	var held := _soles()
	_retract_near(held, Layout.HELD_CLEAR)
	rush.held_at = held
	rush.held_from = portals_clock
	holding = true
	player().grab()
	eric.play(&"grab")
	squeezes_left = Layout.SQUEEZES
	_set_move(Move.GRAB, Layout.GRAB_TIME)
	_hold_player()


func _squeeze() -> void:
	squeezes_left -= 1
	eric.play(&"squeeze")
	player().take_grab_damage(Layout.SQUEEZE_ID)
	_sound(&"squeeze")
	_set_move(Move.SQUEEZE, Layout.SQUEEZE_TIME)


func _toss() -> void:
	eric.play(&"toss")
	_set_move(Move.TOSS, Layout.TOSS_TIME)


# Kept where his frame draws them, so the art lines up; on the toss frame, where they reappear.
func _hold_player() -> void:
	var p := player()
	var frame: int = eric.sprite.frame
	var centre: Vector2 = EricArtLayout.HUG_RELEASE_CENTRE if frame == 11 \
		else EricArtLayout.HUG_PLAYER_CENTRES.get(frame, EricArtLayout.HUG_PLAYER_CENTRES[7])
	p.global_position = _on_floor(eric.global_position + centre * Layout.SCALE, p)
	p.velocity = Vector2.ZERO


func _release_player() -> void:
	holding = false
	var p := player()
	if p == null:
		return
	p.global_position = _on_floor(eric.global_position + EricArtLayout.HUG_RELEASE_CENTRE * Layout.SCALE, p)
	p.release_grab(Layout.TOSS_DIRECTION)


func _let_go() -> void:
	if holding and is_instance_valid(eric):
		_release_player()
	holding = false
	if is_instance_valid(eric):
		ParryTell.clear(eric)


# After a grab: Josh ports him on, charging - or, the phase over, home.
func _after_attack() -> void:
	if beat == Beat.PHASE:
		_hop(Layout.HOP, Vector2.INF, true)
	else:
		_hop(Layout.HOME, Layout.ERIC_RECOVERY, false)


#THE END

# No new charge: one in progress is called off and he goes home at once; a rush or a feint resolves, a hold plays out
# through its toss, and then he goes home.
func _end_phase() -> void:
	beat = Beat.ENDING
	spikes_on = false
	ending = {at = phase_clock, clock = portals_clock, move = Move.keys()[move], cancelled = false, recovered_at = -1.0}
	var cancel := charging
	if cancel:
		ParryTell.clear(eric)
		charging = false
		ending.cancelled = true
	feint_planned = false
	match move:
		Move.CHARGE:
			_hop(Layout.HOME, Layout.ERIC_RECOVERY, false)
		Move.HOP_RISE:
			if cancel:
				_close(exit_portal)
				exit_portal = null
				_hop(Layout.HOME, Layout.ERIC_RECOVERY, false)
		Move.HOP_OPEN, Move.HOP_SINK:
			hop.to = Layout.ERIC_RECOVERY
			hop.charges = false
			hop.reroute = false
			hops[-1].charges = false
			hops[-1].reroute = false
		Move.HOP_TELL:
			_close(exit_portal)
			eric.global_position = Layout.ERIC_RECOVERY
			exit_portal = _open_body_portal(Layout.ERIC_RECOVERY)
			hop.to = Layout.ERIC_RECOVERY
			hop.charges = false
			hop.reroute = false
			hops[-1].to = Layout.ERIC_RECOVERY
			hops[-1].charges = false
			hops[-1].reroute = false
			_set_move(Move.HOP_TELL, Layout.HOME.tell)


# Home, and the last spike closed: Eric leans on his sword in its portal, Josh slumps, and either can be taken.
func _recover() -> void:
	beat = Beat.WALK
	phase_on = false
	_notch(&"winded")
	eric.play(&"winded")
	josh.play(&"recover")
	var strings: Node2D = god.layer(&"strings")
	for puppet: Node2D in [josh, eric]:
		strings.set_tension(puppet, GodLayout.TENSION_LIMP)
		_show_stars(puppet)
		puppet.set_punchable(true)
	if hits == 0:
		player().hype.add(Layout.HYPE_CLEAN)
	ending.recovered_at = portals_clock
	stage_ended.emit()


# The one the player walked into the uppercut's reach of; the nearer, in reach of both.
func _reached() -> Node2D:
	var best: Node2D = null
	var nearest := INF
	for puppet: Node2D in [josh, eric]:
		var away: float = player().global_position.distance_to(puppet.global_position)
		if _in_reach(puppet) and away < nearest:
			best = puppet
			nearest = away
	return best


# PlayerFinisher._in_reach: its hurtbox grown uppercut_reach, with a margin to spare.
func _in_reach(puppet: Node2D) -> bool:
	var body := player()
	var shape: CollisionShape2D = puppet.get_finisher_hurtbox().get_node("CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	return box.grow(body.finisher.uppercut_reach - Layout.REACH_MARGIN).has_point(body.global_position)


func _take(puppet: Node2D) -> void:
	target = puppet
	for other: Node2D in [josh, eric]:
		if other != puppet:
			other.set_punchable(false)
	beat = Beat.PAYOFF
	stage_ended.emit()


# The sword goes back into its portal as the portal closes, then the recall.
func _wrap(run_of: int) -> void:
	_clear_stars()
	if _eric_shows_sword():
		eric.set_clipped(false)
		eric.play(&"empty")
	var closing := 0.0
	if is_instance_valid(sword_portal):
		closing = sword_portal.close()
	if is_instance_valid(prop):
		var sink := prop.create_tween().set_process_mode(Tween.TWEEN_PROCESS_PHYSICS)
		sink.tween_method(_cut_prop, Layout.PLANTED_REGION.size.y, 0.0, maxf(closing, 0.01))
	await wait(closing)
	if _gone(run_of):
		return
	sword_planted = false
	await recall()
	if _gone(run_of):
		return
	if bars > 0:
		god.play(&"hit", &"hover")
	finish()


func _show_stars(puppet: Node2D) -> void:
	var spec := FinisherArtLayout.stars()
	var sprite := Sprite2D.new()
	sprite.name = "DazeStars"
	sprite.texture = load(spec.texture)
	sprite.hframes = spec.hframes
	sprite.centered = false
	sprite.offset = -spec.pivot
	sprite.scale = Vector2.ONE * spec.scale
	add_hazard(sprite, puppet.get_daze_anchor(), god.layer(&"fx"))
	stars[puppet.boss] = sprite


func _spin_stars(delta: float) -> void:
	if stars.is_empty():
		return
	stars_clock += delta
	var frame_time: float = FinisherArtLayout.stars().frame_time
	for sprite: Sprite2D in stars.values():
		if is_instance_valid(sprite):
			sprite.frame = int(stars_clock / frame_time) % sprite.hframes


func _clear_stars() -> void:
	for sprite in stars.values():
		if is_instance_valid(sprite):
			sprite.queue_free()
	stars.clear()


#SOUND AND HITS

func _build_sounds() -> void:
	if not sounds.is_empty():
		return
	for key: StringName in Layout.SOUNDS:
		var spec: Dictionary = Layout.SOUNDS[key]
		if not ResourceLoader.exists(spec.stream):
			continue
		var stream: AudioStream = load(spec.stream)
		var voices: Array[AudioStreamPlayer] = []
		for i in int(spec.voices):
			var voice := AudioStreamPlayer.new()
			voice.name = "%s_%d" % [key, i]
			voice.stream = stream
			voice.volume_db = spec.volume_db
			voice.pitch_scale = spec.pitch
			add_child(voice)
			voices.append(voice)
		sounds[key] = voices


func _sound(key: StringName) -> void:
	var voices: Array = sounds.get(key, [])
	if voices.is_empty():
		return
	var voice: AudioStreamPlayer = voices.pop_front()
	voices.append(voice)
	voice.play()


func _watch_hits(on: bool) -> void:
	var body := player()
	if body == null:
		return
	var defense: Node = body.defense
	if on and not defense.hit_taken.is_connected(_on_hit_taken):
		defense.hit_taken.connect(_on_hit_taken)
	elif not on and defense.hit_taken.is_connected(_on_hit_taken):
		defense.hit_taken.disconnect(_on_hit_taken)


func _on_hit_taken(_hit: RefCounted) -> void:
	hits += 1


#HELPERS

func _soles() -> Vector2:
	return player().global_position + Vector2(0, Layout.SOLES_OVER_ORIGIN)


func _hurt_centre() -> Vector2:
	return player().hurtBox.get_node("CollisionShape2D").global_position


func _player_box() -> Rect2:
	var shape: CollisionShape2D = player().hurtBox.get_node("CollisionShape2D")
	return shape.global_transform * shape.shape.get_rect()


func _grab_box() -> Rect2:
	return Rect2(eric.global_position + Layout.GRAB_BOX.position, Layout.GRAB_BOX.size)


# His rush and recoil stay where the player can be (ring_origins).
func _place_eric(at: Vector2) -> void:
	var origins: Rect2 = player().ring_origins
	eric.global_position = at.clamp(origins.position, origins.end) if origins.has_area() else at


func _on_floor(at: Vector2, body: CharacterBody2D) -> Vector2:
	var origins: Rect2 = body.ring_origins
	var on := at.clamp(origins.position, origins.end) if origins.has_area() else at
	var below := Vector2(0, Layout.SOLES_OVER_ORIGIN)
	return Layout.out_of_no_stand(on + below, Rect2(origins.position + below, origins.size)) - below


# How far under the floor line his sprite is drawn, px: 0 standing, HOP_DEPTH all the way under.
func _depth(px: float) -> void:
	eric.sprite.position = eric.sprite_base_position + Vector2(0.0, roundf(px))


func _depth_now() -> float:
	return eric.sprite.position.y - eric.sprite_base_position.y


static func _ease_in(x: float) -> float:
	var t := clampf(x, 0.0, 1.0)
	return t * t


static func _ease_out(x: float) -> float:
	var left := 1.0 - clampf(x, 0.0, 1.0)
	return 1.0 - left * left
