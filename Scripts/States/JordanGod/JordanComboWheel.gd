extends "res://Scripts/States/JordanGod/JordanCombo.gd"

# Jordan's attack 5, Liam + Bixby's Elemental Wheel (the build plan of 2026-10-06; every number is JordanWheelLayout's).
# Jordan raises Liam and Bixby. Liam floats in the Avatar State on the hub of a four-element wheel (JordanElementWheel);
# it spins three times, each faster, and clicks to a stop, the element's icon popping over his head, and only then do
# Liam and Bixby answer it together: FIRE, Bixby's fly-by fire over the whole floor but one gap Liam's wind holds open;
# WATER, a thin wave rolling down the floor with Bixby breaching it, to stand and dash through, then his snap from where
# it collapsed, parried; EARTH, three pillars Bixby smashes one at a time, a quake ring off each to dash through; AIR,
# Liam's wind dragging the player at Bixby's jaws, walked against, then his bite under the red badge and a second one,
# each parried. The third spin lands on two neighbours at once: the first's result with the second's twist (an
# infusion), or, on AIR + WATER (the undertow), the shark wave first and then the jaws. Then Liam drops out of the Avatar
# State, Bixby crashes, and the first one the player reaches is the one they take apart: the punch-out and the three-bar
# mash, every bar one off Jordan.
#
# THE BEATS: the start check, the summon, the payoff and the wrap are a coroutine (run) on the combo's own waits; from
# the Avatar State to the crash everything is timed on wheel_clock, summed on Physics_Update, which is game time that a
# pause and a finisher's freeze hold. A run left behind by a cut never resumes into the next one (generation).
#
# THE PLAYER is free all through it - walking, the parry, the dash - and the HUD stays up; only a player standing where
# Liam or Bixby is summoned is blinked clear first. From spin 1's stop to the crash the stamina bar is held at
# STAMINA_FLOOR, so a required dash is never refused. Liam and Bixby go see-through while they are drawn over the
# player's hurtbox centre.
#
# THE DECK: a run is two singles and a double, together all four elements, the double never last run's (deal).

const Layout := preload("res://Scripts/JordanWheelLayout.gd")
const WheelScript := preload("res://Scripts/JordanElementWheel.gd")
const FinisherArtLayout := preload("res://Scripts/FinisherArtLayout.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const PlayerScript := preload("res://Scripts/PlayerScript.gd")
const LiamArtLayout := preload("res://Scripts/LiamArtLayout.gd")
const SuctionScript := preload("res://Scripts/BixbySuctionScript.gd")
const WaveScript := preload("res://Scripts/JordanWheelWave.gd")
const RingScript := preload("res://Scripts/BixbyQuakeRingScript.gd")
const PillarScript := preload("res://Scripts/JordanWheelPillar.gd")
const FireScript := preload("res://Scripts/JordanWheelFire.gd")
const FlybyLayout := preload("res://Scripts/BixbyFlybyLayout.gd")
# A slam's beats.
const GLIDING := 1
const TELLING := 2
const DROPPING := 3
const SLAMMED := 4
const FLOOR_RECT: Rect2 = Layout.FLOOR
const FLOOR_MIDDLE := Vector2(960, 804)

const LIAM := &"liam"
const BIXBY := &"bixby"
const FIRE: int = Layout.Element.FIRE
const AIR: int = Layout.Element.AIR
const WATER: int = Layout.Element.WATER
const EARTH: int = Layout.Element.EARTH
# A float clock summed a step at a time lands a hair short of a beat's end.
const CLOCK_SLACK := 0.0001
const LIAM_POSES := {FIRE: &"ignite", WATER: &"cast_left", EARTH: &"slam_rise", AIR: &"blow"}

# The crash is over: both are down and open.
signal rounds_over
# The player has walked into reach of one of them.
signal reached

enum Beat { OFF, AVATAR, SPIN, STOP, RESULT, CLEAR, CRASH, WALK, PAYOFF }

var rng := RandomNumberGenerator.new()
# For tests: the run's deck [single, single, double index] whatever the deal, the fire's column middle (x), the air's
# maw (index into MAWS).
var pinned_deck: Array = []
var pinned_column := NAN
var pinned_maw := -1
var last_double := -1
var hints_given := {}
var generation := 0
var beat := Beat.OFF
# The player is down: nothing more happens, and the fight's end releases this.
var stopped := false
var wheel_clock := 0.0
var beat_at := 0.0
var spin_k := 0
# The three spins' elements: [primary] or [primary, secondary].
var spins: Array = []
var liam: Node2D
var bixby: Node2D
var wheel: Node2D
var glow: Sprite2D
var glow_level := 0.0
var glow_from := 0.0
var glow_to := 0.0
var glow_at := 0.0
var glow_time := 0.0
var liam_lift := 0.0
var liam_lift_from := 0.0
var liam_lift_to := 0.0
var liam_lift_at := 0.0
var liam_lift_time := 0.0
var bobbing := false
# Bixby's flight from place to place, when no result is driving him: {from, to, lift_from, lift_to, at, time, arc}.
var bixby_path := {}
var bixby_lift := 0.0
var bixby_driven := false
var see_through := {}
# The result under way: its elements, its start and its own state.
var result := {}
var target: Node2D
var stars: Array[Sprite2D] = []
var stars_clock := 0.0
var bars := -1
var hits := 0
var result_hits := 0
var flooring := false
var sounds := {}
var sound_holder: Node2D
var hint_up := false
var hint_off_at := 0.0
var start_warp := {}
var crash_landed := true
var liam_falls_at := 0.0
var liam_fallen := true
var auras: Array[Sprite2D] = []
# The State's flare in or burst out under way: {texture, times, at, kind}, or empty.
var flare := {}
# What the result under way put up, freed as it clears: the maw's zone and the like.
var result_nodes: Array[Node] = []
var maw_zone: Node2D
var suction: Node2D
# A swallow has the player held.
var holding := false
# For tests: each air result's own record {maw, index, undertow, at (its start, from the result's), start, swallowed,
# swallow_at, spat, bite_at, contact_at, bite_result (the first bite's), bites, done_at, drift_max, nearest (the soles'
# closest, in maw radii)}.
var air_log: Array[Dictionary] = []
# Each water result's {wave, rolled, cleared, cleared_at, breach, bite, slams, results (its band's, as it cleared)}; every
# ring {at, born, fire, node}.
var water_log: Array[Dictionary] = []
# For tests and the model bot: every bite {kind, id, at (from its result's start), clock (wheel_clock), contact_at,
# contact_clock, result}, as its badge goes up.
var bite_log: Array[Dictionary] = []
var ring_log: Array[Dictionary] = []
# Each earth result's {start, spots, times, magma, slams}; each fire result's {cx, span, direction, firestorm, start,
# reports (its fire's, as it cleared), cleared_at, wind_max}.
var earth_log: Array[Dictionary] = []
var fire_log: Array[Dictionary] = []
var wind_streaks: Array[Node2D] = []
# The physics step under way, for what moves at a speed.
var step_delta := 0.0

# For tests, on wheel_clock: every spin {k, target, second, from, to, position, under, under_second, omega, at, stop_at,
# last90, ticks}; every stop {k, at, badge_at, live_at, elements}; every result {elements, at, live_at, clear_at, hits};
# every hit {id, at, damage}; the most badges up in one frame; the lowest stamina while it was floored.
var spin_log: Array[Dictionary] = []
var stop_log: Array[Dictionary] = []
var result_log: Array[Dictionary] = []
var hit_log: Array[Dictionary] = []
var max_badges := 0
var floor_min := INF
var ticks := 0


func _init() -> void:
	rng.randomize()


func pair() -> Array[Dictionary]:
	return [
		{boss = LIAM, feet = Layout.LIAM_FEET, face_left = false, hand = &"left", hooks = [&"back"], strings = 2},
		{boss = BIXBY, feet = Layout.BIXBY_REST, face_left = Layout.BIXBY_FACE_LEFT, hand = &"right", hooks = [&"back"],
			strings = 2},
	]


func run() -> void:
	generation += 1
	var run_of := generation
	_start()
	var body := player()
	if body != null:
		var start := Layout.start_spot(_soles(), body.ring_origins)
		if start != _soles():
			start_warp = {from = _soles(), to = start}
			warp_player(start, PlayerScript.Facing.UP)
			await wait(Layout.WARP_TIME)
			if _gone(run_of):
				return
			body.unlock_actions()
			player_held = false
	await summon()
	if _gone(run_of):
		return
	liam = puppets.get(LIAM)
	bixby = puppets.get(BIXBY)
	_build_sounds()
	_watch_hits(true)
	_begin_avatar()
	await rounds_over
	if _gone(run_of):
		return
	await reached
	if _gone(run_of):
		return
	bars = await punch_out(target)
	if _gone(run_of):
		return
	_clear_stars()
	await recall()
	if _gone(run_of):
		return
	if bars > 0:
		god.play(&"hit", &"hover")
	finish()


# Idempotent; every exit runs it (JordanCombo.release after).
func release() -> void:
	generation += 1
	beat = Beat.OFF
	for puppet: Node2D in _pair_up():
		_clear_tell(puppet)
	_let_go()
	_floor(false)
	_watch_hits(false)
	for puppet: Node2D in _pair_up():
		if is_instance_valid(puppet):
			puppet.modulate = Color.WHITE
			puppet.sprite.position = puppet.sprite_base_position
			puppet.set_clipped(false)
	_clear_stars()
	_end_result_nodes()
	super.release()
	wheel = null
	glow = null
	sound_holder = null
	sounds.clear()
	rounds_over.emit()
	reached.emit()


func Physics_Update(delta: float) -> void:
	super.Physics_Update(delta)
	if beat == Beat.OFF or cut or stopped:
		return
	if _player_down():
		stopped = true
		_let_go()
		return
	wheel_clock += delta
	step_delta = delta
	if is_instance_valid(wheel):
		wheel.advance(delta)
	_run_beats(delta)
	_step_liam()
	_step_bixby()
	_step_glow()
	_see_through(delta)
	_spin_stars(delta)
	if flooring:
		_hold_floor()
	_count_badges()
	if hint_up and _due(hint_off_at):
		hint_up = false
		hide_hint()


func _start() -> void:
	Layout.assert_invariants()
	beat = Beat.OFF
	stopped = false
	wheel_clock = 0.0
	beat_at = 0.0
	spin_k = 0
	spins.clear()
	liam = null
	bixby = null
	wheel = null
	glow = null
	glow_level = 0.0
	glow_from = 0.0
	glow_to = 0.0
	glow_time = 0.0
	liam_lift = 0.0
	liam_lift_from = 0.0
	liam_lift_to = 0.0
	liam_lift_time = 0.0
	bobbing = false
	bixby_path = {}
	bixby_lift = 0.0
	bixby_driven = false
	see_through = {}
	result = {}
	target = null
	stars.clear()
	bars = -1
	hits = 0
	result_hits = 0
	flooring = false
	sound_holder = null
	sounds.clear()
	hint_up = false
	start_warp = {}
	spin_log.clear()
	stop_log.clear()
	result_log.clear()
	hit_log.clear()
	max_badges = 0
	floor_min = INF
	ticks = 0
	crash_landed = true
	liam_fallen = true
	auras.clear()
	flare = {}
	result_nodes.clear()
	maw_zone = null
	suction = null
	holding = false
	air_log.clear()
	water_log.clear()
	bite_log.clear()
	ring_log.clear()
	earth_log.clear()
	fire_log.clear()
	wind_streaks.clear()


func _gone(run_of: int) -> bool:
	return cut or run_of != generation


func _due(at: float) -> bool:
	return wheel_clock >= at - CLOCK_SLACK


func _since(at: float) -> float:
	return wheel_clock - at + CLOCK_SLACK


func _player_down() -> bool:
	var body := player()
	return body == null or body.playerHealth <= 0 or body.fight_over


#THE AVATAR STATE

# He lifts and his glow flares on, the wheel forms behind him, Bixby takes off to his hover, and Jordan yanks.
func _begin_avatar() -> void:
	_deal()
	beat = Beat.AVATAR
	beat_at = 0.0
	wheel_clock = 0.0
	god.play(&"yank_left", &"control")
	_lift_liam(Layout.liam_lift(Layout.float_pivot()), Layout.LIFT_TIME)
	bobbing = true
	_build_glow()
	if Layout.final_avatar_on():
		liam.play(&"channel_hold")
		_flare(Layout.AVATAR_ON_SHEET, Layout.AVATAR_ON_TIMES, &"on")
		_glow_to(Layout.PLACEHOLDER_GLOW.held, Layout.strip_time(Layout.AVATAR_ON_TIMES))
	else:
		liam.play(&"channel")
		_glow_to(Layout.PLACEHOLDER_GLOW.flare, Layout.PLACEHOLDER_GLOW.flare_time)
	_build_wheel()
	wheel.form()
	_sound(&"form")
	bixby.play(&"hover")
	_fly_bixby(Layout.BIXBY_REST, Layout.BIXBY_LIFT, Layout.LIFT_TIME)


# The run's three spins off the deck (or the test's pinned one).
func _deal() -> void:
	var dealt: Array = pinned_deck if pinned_deck.size() == 3 else Layout.deal(rng, last_double)
	last_double = dealt[2]
	spins = [[dealt[0]], [dealt[1]], Layout.DOUBLES[dealt[2]].duplicate()]


func _build_wheel() -> void:
	wheel = WheelScript.new()
	wheel.name = "ElementWheel"
	wheel.icon_layer = god.layer(&"fx")
	wheel.icon_anchor = _icon_point
	# Over the floor's own pieces, still under the strings (z -2), which run over it to his back.
	wheel.z_index = 1
	add_hazard(wheel, Layout.WHEEL_HUB, god.layer(&"floor"))
	wheel.ticked.connect(_on_tick)


func _icon_point() -> Vector2:
	return Layout.icon_point(_liam_pivot())


#THE BEATS

func _run_beats(_delta: float) -> void:
	match beat:
		Beat.AVATAR:
			if _due(beat_at + Layout.AVATAR_TIME):
				_begin_spin(0)
		Beat.SPIN:
			if not wheel.spinning:
				_stop()
		Beat.STOP:
			if _due(beat_at + Layout.STOP_HOLD[spin_k]):
				_begin_result()
		Beat.RESULT:
			_step_result()
		Beat.CLEAR:
			if _due(beat_at + Layout.CLEAR_GAP):
				_after_clear()
		Beat.CRASH:
			_step_crash()
			if _due(beat_at + Layout.CRASH_TIME):
				_open()
		Beat.WALK:
			_walk()
		Beat.PAYOFF:
			# The finisher's own stars take over as it dazes the one taken.
			if not stars.is_empty() and player().finisher.is_active():
				_clear_stars()


func _begin_spin(k: int) -> void:
	beat = Beat.SPIN
	beat_at = wheel_clock
	spin_k = k
	var elements: Array = spins[k]
	if elements.size() > 1:
		wheel.show_double(true)
	var plan: Dictionary = wheel.begin_spin(k, elements[0])
	spin_log.append({k = k, target = elements[0], second = elements[1] if elements.size() > 1 else -1, from = plan.from,
		to = plan.to, position = -1, under = -1, under_second = -1, omega = plan.omega, at = wheel_clock, stop_at = -1.0,
		last90 = Layout.last_segment_time(plan), ticks = 0})
	ticks = 0
	liam.play(&"channel")


func _on_tick() -> void:
	ticks += 1
	_sound(&"tick")


# The click: the elements lit, their icons up over his head, his pose and its sting.
func _stop() -> void:
	beat = Beat.STOP
	beat_at = wheel_clock
	var elements: Array = spins[spin_k]
	var spin: Dictionary = spin_log[-1]
	spin.stop_at = wheel_clock
	spin.position = wheel.position_now()
	spin.under = wheel.element_under()
	spin.under_second = wheel.element_under(true)
	spin.ticks = ticks
	wheel.light(elements)
	wheel.badge(elements)
	_sound(&"clunk")
	_sound(Layout.NAMES[elements[0]])
	_pose_liam(elements[0])
	stop_log.append({k = spin_k, at = wheel_clock, badge_at = wheel_clock, live_at = -1.0, elements = elements.duplicate()})
	if spin_k == 0:
		_floor(true)


func _begin_result() -> void:
	beat = Beat.RESULT
	beat_at = wheel_clock
	var elements: Array = spins[spin_k]
	result = {primary = elements[0], secondary = elements[1] if elements.size() > 1 else -1, at = wheel_clock, live = false,
		clear = false}
	result_hits = hits
	result_log.append({elements = elements.duplicate(), at = wheel_clock, live_at = -1.0, clear_at = -1.0, hits = 0})
	_give_hint(elements)
	match int(result.primary):
		FIRE:
			_begin_fire()
		WATER:
			_begin_water()
		EARTH:
			_begin_earth()
		AIR:
			# The undertow: the shark wave first, the jaws once it is off the floor.
			if int(result.secondary) == WATER:
				_begin_water()
			else:
				_begin_air(0.0)


func _step_result() -> void:
	if result.is_empty():
		return
	var t := wheel_clock - float(result.at)
	match int(result.primary):
		FIRE:
			_step_fire(t)
		WATER:
			_step_water(t)
		EARTH:
			_step_earth(t)
		AIR:
			if result.has("water") and not result.has("air"):
				_step_water(t)
				if result.water.cleared:
					_begin_air(t)
			else:
				_step_air(t)
	if result.clear:
		_clear_result()


# The result's first hazard is live: the icons go.
func _mark_live() -> void:
	if result.live:
		return
	result.live = true
	wheel.clear_badge()
	stop_log[-1].live_at = wheel_clock
	result_log[-1].live_at = wheel_clock


func _clear_result() -> void:
	beat = Beat.CLEAR
	beat_at = wheel_clock
	var got := hits - result_hits
	result_log[-1].clear_at = wheel_clock
	result_log[-1].hits = got
	if got == 0:
		player().hype.add(Layout.HYPE_RESULT)
	_end_result()
	if hint_up:
		hint_up = false
		hide_hint()


func _after_clear() -> void:
	if spin_k < spins.size() - 1:
		_begin_spin(spin_k + 1)
	else:
		_begin_crash()


#THE RESULTS (each a begin, run on its own clock t from the result's start, that sets result.clear)

#FIRE: THE GAP

# The column off the player, the projection laid over the rest of the floor, and Bixby off past the wall farther from
# the column to wait for his pass. On the firestorm double the column is narrower, and Liam's wind blows outward from it.
func _begin_fire() -> void:
	var firestorm := int(result.secondary) == AIR
	liam.play(&"blow" if firestorm else &"ignite", &"channel")
	var cx := pinned_column if not is_nan(pinned_column) else Layout.column_for(rng, _soles().x, firestorm)
	var direction := Layout.entry_for(cx)
	var node: Node2D = FireScript.new()
	node.name = "WheelFire"
	node.direction = direction
	node.column = Layout.column_span(cx, firestorm)
	node.player = player()
	node.boss = bixby
	add_hazard(node, Vector2.ZERO, god.layer(&"floor"))
	var fire := {node = node, cx = cx, span = node.column, direction = direction, firestorm = firestorm, start = _soles(),
		reports = [], cleared_at = -1.0, wind_max = 0.0}
	result.fire = fire
	fire_log.append(fire)
	var wait_mouth := Layout.entry_x(direction) - direction * Layout.FRONT_SPEED * Layout.ENTRY_LEAD
	bixby.play(&"fly")
	_fly_bixby(Vector2(wait_mouth - FlybyLayout.exit_offset(direction), FLOOR_RECT.position.y), _pass_lift(), Layout.FLY_OFF)
	if firestorm:
		_blow_outward(node.column)
	_sound(&"fire")


func _step_fire(t: float) -> void:
	var fire: Dictionary = result.fire
	var node: Node2D = fire.node
	if is_instance_valid(node):
		node.drive(t)
	var sweep_end := Layout.T_PROJ + FLOOR_RECT.size.x / Layout.FRONT_SPEED
	var direction: float = fire.direction
	if t >= Layout.T_PROJ - Layout.ENTRY_LEAD - CLOCK_SLACK:
		var mouth := Layout.entry_x(direction) + direction * Layout.FRONT_SPEED * (t - Layout.T_PROJ)
		_drive_bixby(Vector2(mouth - FlybyLayout.exit_offset(direction), FLOOR_RECT.position.y), _pass_lift())
		bixby.face(direction < 0.0)
		var breathing := t >= Layout.T_PROJ and t < sweep_end
		var pose := &"flyby_breath" if breathing else &"flyby_glide"
		if bixby.current_anim != pose:
			bixby.play(pose)
			if breathing:
				_sound(&"breath")
	if t >= Layout.T_PROJ - CLOCK_SLACK:
		_mark_live()
	if fire.firestorm and t < sweep_end:
		_crosswind(fire)
	elif fire.firestorm:
		_stop_wind()
	if t >= sweep_end + Layout.BURN - CLOCK_SLACK:
		fire.cleared_at = t
		if is_instance_valid(node):
			fire.reports = node.reports.duplicate()
			node.driven = false
		result.clear = true


# His lift on a pass: his floor point on the floor's top edge, so he sorts behind everyone, and his anchor drawn down at
# PASS_ANCHOR_Y under it.
func _pass_lift() -> float:
	return FLOOR_RECT.position.y - Layout.PASS_ANCHOR_Y


# The firestorm's crosswind: outward from the column's middle, calm inside it.
func _crosswind(fire: Dictionary) -> void:
	var x := _player_centre().x
	var span: Vector2 = fire.span
	if x >= span.x and x <= span.y:
		return
	player().add_drift(Vector2(signf(x - float(fire.cx)) * Layout.WIND, 0.0))
	fire.wind_max = Layout.WIND


# Streaks flying outward either side of the column, toward points far past the walls.
func _blow_outward(span: Vector2) -> void:
	var sides := [[Rect2(FLOOR_RECT.position.x, FLOOR_RECT.position.y, span.x - FLOOR_RECT.position.x, FLOOR_RECT.size.y), -1.0],
		[Rect2(span.y, FLOOR_RECT.position.y, FLOOR_RECT.end.x - span.y, FLOOR_RECT.size.y), 1.0]]
	for side: Array in sides:
		var area: Rect2 = side[0]
		if not area.has_area():
			continue
		var streaks: Node2D = SuctionScript.new()
		streaks.name = "Crosswind"
		streaks.player = player()
		streaks.mouths = [Vector2(FLOOR_RECT.get_center().x + float(side[1]) * Layout.WIND_FAR, FLOOR_RECT.get_center().y)] as Array[Vector2]
		streaks.pull_speed = Layout.WIND
		streaks.area = area
		add_hazard(streaks, Vector2.ZERO, god.layer(&"floor"))
		result_nodes.append(streaks)
		wind_streaks.append(streaks)


func _stop_wind() -> void:
	for streaks in wind_streaks:
		if is_instance_valid(streaks):
			streaks.stop()
	wind_streaks.clear()


#WATER: THE SHARK WAVE

# Liam casts at Bixby, who dives to the floor's top edge over the player, the swell along it and the yellow badge on him.
func _begin_water() -> void:
	_pose_liam(WATER)
	var wave: Node2D = WaveScript.new()
	wave.name = "WheelWave"
	wave.player = player()
	wave.boss = bixby
	wave.fx_layer = god.layer(&"fx")
	add_hazard(wave, FLOOR_RECT.position, god.layer(&"stage"))
	result_nodes.append(wave)
	var water := {wave = wave, clipped = false, rolled = false, cleared = false, cleared_at = -1.0, breach = Vector2.ZERO,
		bite = {}, slams = [], results = []}
	result.water = water
	water_log.append(water)
	_fly_bixby(Vector2(_shark_x(), FLOOR_RECT.position.y + 1.0), -_swim_depth(), Layout.DIVE_TIME)
	bixby.play(Layout.swim_anim())
	_telegraph(bixby, Layout.WAVE_ID, Layout.WAVE_TELL, _bixby_head)
	_sound(&"water")


# The roll: Bixby rides its front, only his heads and wings breaching, his x homing on the player's. Once it is off the
# floor, his snap from where it collapsed; in the undertow the jaws take over instead.
func _step_water(t: float) -> void:
	var water: Dictionary = result.water
	var wave: Node2D = water.wave
	wave.drive(t)
	if not water.clipped and t >= Layout.DIVE_TIME - CLOCK_SLACK:
		water.clipped = true
		bixby.set_clipped(true)
	if not water.rolled and t >= Layout.WAVE_TELL - CLOCK_SLACK:
		water.rolled = true
		_clear_tell(bixby)
		_mark_live()
	if water.rolled and not water.cleared:
		var x := move_toward(bixby.global_position.x, _shark_x(), Layout.SHARK_SPEED * step_delta)
		_drive_bixby(Vector2(x, wave.front_y + 1.0), -_swim_depth())
	if not water.cleared and wave.cleared():
		water.cleared = true
		water.cleared_at = t
		water.results = wave.results.duplicate()
		# Nothing drives the wave once the jaws take over: it goes, or it would hang along the bottom edge.
		if int(result.primary) == AIR:
			bixby.set_clipped(false)
			wave.queue_free()
			return
		water.breach = Vector2(clampf(bixby.global_position.x, FLOOR_RECT.position.x + Layout.SHARK_EDGE,
			FLOOR_RECT.end.x - Layout.SHARK_EDGE), FLOOR_RECT.end.y)
	if water.cleared and int(result.primary) == WATER:
		_step_breach(water, t)


# He surfaces on the floor's bottom edge behind the player, still cut at the waterline, and snaps. Clear CLEAR_AFTER
# after the snap; on the landslide double his aftershock comes once he has recoiled, and it is clear once its ring is
# past the player.
func _step_breach(water: Dictionary, t: float) -> void:
	if water.bite.is_empty():
		var rise := t - float(water.cleared_at)
		if rise < Layout.BREACH_RISE - CLOCK_SLACK:
			_drive_bixby(water.breach, lerpf(-_swim_depth(), 0.0, _ease_out(rise / Layout.BREACH_RISE)))
			return
		_drive_bixby(water.breach, 0.0)
		bixby.set_clipped(false)
		water.bite = _begin_bite(&"breach", Layout.BREACH_ID, t, Layout.SNAP_LIFT)
	var bite: Dictionary = water.bite
	_step_bite(bite, t)
	if bite.contact_at < 0.0:
		return
	if int(result.secondary) != EARTH:
		if t >= float(bite.contact_at) + Layout.CLEAR_AFTER - CLOCK_SLACK:
			result.clear = true
		return
	if water.slams.is_empty() and t >= float(bite.contact_at) + Layout.RECOIL_TIME - CLOCK_SLACK:
		var spot := Layout.aftershock_for(_soles())
		water.slams = [_slam_entry(spot, t, Layout.AFTERSHOCK_DELAY - Layout.SLAM_TELL, t + Layout.AFTERSHOCK_DELAY, 0.0,
			null, false)]
	if not water.slams.is_empty():
		_step_slams(t, water.slams)
		if water.slams[-1].phase >= SLAMMED and _ring_past(water.slams[-1].ring):
			result.clear = true


func _shark_x() -> float:
	return clampf(player().global_position.x, FLOOR_RECT.position.x + Layout.SHARK_EDGE, FLOOR_RECT.end.x - Layout.SHARK_EDGE)


# How far under the front his sprite rides: his waterline row on it.
func _swim_depth() -> float:
	return (Layout.BIXBY_FEET.y + 1.0 - Layout.waterline_row()) * Layout.SCALE


#THE SLAMS (the earth's, over its pillars, and the landslide's aftershock): a glide over the spot, his shadow growing on
# it for SLAM_TELL, the drop, and the ring born where he lands.

func _slam_entry(spot: Vector2, glide_at: float, glide_time: float, slam_at: float, land_lift: float, pillar: Node2D,
		fire: bool) -> Dictionary:
	return {spot = spot, glide_at = glide_at, glide_time = glide_time, tell_at = slam_at - Layout.SLAM_TELL,
		drop_at = slam_at - Layout.SLAM_DROP, slam_at = slam_at, land_lift = land_lift, pillar = pillar, fire = fire,
		phase = 0, shadow = null, ring = null, born_at = -1.0}


func _step_slams(t: float, slams: Array) -> void:
	for slam: Dictionary in slams:
		if slam.phase == 0 and t >= slam.glide_at - CLOCK_SLACK:
			slam.phase = GLIDING
			bixby.play(&"fly")
			_fly_bixby(Vector2(slam.spot) + Vector2(0, 1), Layout.SLAM_LIFT, slam.glide_time)
		if slam.phase == GLIDING and t >= slam.tell_at - CLOCK_SLACK:
			slam.phase = TELLING
			bixby.play(&"brace")
			slam.shadow = _build_shadow(slam.spot)
		if slam.phase == TELLING:
			if is_instance_valid(slam.shadow):
				var grown := lerpf(Layout.SHADOW.from_scale, 1.0, _share(t - float(slam.tell_at), Layout.SLAM_TELL))
				slam.shadow.scale = Vector2.ONE * Layout.SCALE * grown
			if t >= slam.drop_at - CLOCK_SLACK:
				slam.phase = DROPPING
				bixby.play(&"pound")
				_fly_bixby(Vector2(slam.spot) + Vector2(0, 1), slam.land_lift, Layout.SLAM_DROP)
		if slam.phase == DROPPING and t >= slam.slam_at - CLOCK_SLACK:
			slam.phase = SLAMMED
			_slam(slam, t)


# The impact: the pillar crumbles, the screen shakes, and a ring rolls out from under him.
func _slam(slam: Dictionary, t: float) -> void:
	if is_instance_valid(slam.shadow):
		slam.shadow.queue_free()
	slam.shadow = null
	if is_instance_valid(slam.pillar):
		slam.pillar.crumble(Layout.CRUMBLE_TIME)
	slam.ring = _ring(slam.spot, slam.fire)
	slam.born_at = t
	_mark_live()
	_sound(&"slam")
	ScreenView.shake(get_tree(), Layout.SLAM_SHAKE.strength, Layout.SLAM_SHAKE.steps, Layout.SLAM_SHAKE.step)
	if slam.fire:
		bixby.sprite.modulate = Layout.MAGMA_FLARE
		bixby.create_tween().tween_property(bixby.sprite, "modulate", Color.WHITE, Layout.MAGMA_FLARE_TIME)


func _build_shadow(spot: Vector2) -> Sprite2D:
	var spec: Dictionary = Layout.SHADOW
	var shadow := Sprite2D.new()
	shadow.name = "SlamShadow"
	shadow.texture = load(spec.sheet)
	shadow.hframes = maxi(roundi(shadow.texture.get_width() / spec.frame.x), 1)
	shadow.offset = spec.frame / 2.0 - spec.centre
	shadow.scale = Vector2.ONE * Layout.SCALE * spec.from_scale
	shadow.modulate.a = spec.alpha
	add_hazard(shadow, spot, god.layer(&"floor"))
	result_nodes.append(shadow)
	return shadow


# Bixby's quake ring over the whole floor at RING_SPEED, hurting inside on the frame it is born; on the magma double
# Liam's fire ring, a heart.
func _ring(at: Vector2, fire: bool) -> Node2D:
	var ring: Node2D = RingScript.new()
	ring.name = "WheelRing%d" % ring_log.size()
	ring.y_sort_enabled = true
	ring.speed = Layout.RING_SPEED
	ring.attack_id = Layout.FIRE_RING_ID if fire else Layout.RING_ID
	ring.shown_rect = FLOOR_RECT
	ring.hurt_rect = FLOOR_RECT
	ring.hurts_inside_at_birth = true
	ring.player = player()
	if fire and LiamArtLayout.own_ring_art():
		ring.sheet_path = LiamArtLayout.FIRE_QUAKE_RING_SHEET
		ring.frames = LiamArtLayout.strip_count(LiamArtLayout.FIRE_QUAKE_RING_SHEET, LiamArtLayout.FIRE_QUAKE_RING_FRAME)
		ring.rows = LiamArtLayout.FIRE_QUAKE_RING_ROWS
	add_hazard(ring, at, god.layer(&"stage"))
	ring_log.append({at = at, born = wheel_clock, fire = fire, node = ring})
	return ring


# Its band is past the whole of the player's feet, or it is gone: a ring past never comes back.
func _ring_past(ring) -> bool:
	if not is_instance_valid(ring) or ring.is_queued_for_deletion():
		return true
	var box := _hurt_box()
	var feet := Rect2(box.position.x, box.end.y - Layout.RING_FOOT, box.size.x, Layout.RING_FOOT)
	var farthest := 0.0
	for corner: Vector2 in [feet.position, Vector2(feet.end.x, feet.position.y), Vector2(feet.position.x, feet.end.y), feet.end]:
		farthest = maxf(farthest, Layout.ring_distance(ring.global_position, corner))
	return ring.radius - Layout.RING_HALF_WIDTH > farthest


#EARTH: PILLARS AND RINGS

# Liam raises three pillars off the player and Bixby climbs; then he smashes them one at a time, the end farther from
# the player first, a ring off each. On the magma double every ring is Liam's fire ring and Liam ignites.
func _begin_earth() -> void:
	var magma := int(result.secondary) == FIRE
	liam.play(&"ignite" if magma else &"slam_rise", &"channel")
	var spots := Layout.pillars_for(_soles())
	var times := Layout.slam_times(spots)
	var earth := {start = _soles(), spots = spots, times = times, magma = magma, slams = []}
	for k in spots.size():
		var pillar: Node2D = PillarScript.new()
		pillar.name = "WheelPillar%d" % k
		add_hazard(pillar, spots[k], god.layer(&"stage"))
		pillar.rise(Layout.PILLAR_RISE)
		result_nodes.append(pillar)
		earth.slams.append(_slam_entry(spots[k], times[k] - Layout.SLAM_TELL - Layout.GLIDE_TIME, Layout.GLIDE_TIME, times[k],
			LiamArtLayout.STAND_HEIGHT, pillar, magma))
	result.earth = earth
	earth_log.append(earth)
	bixby.play(&"fly")
	_fly_bixby(bixby.global_position, Layout.SLAM_LIFT, Layout.CLIMB_TIME)
	_sound(&"earth")


# Clear once the last ring is past the player.
func _step_earth(t: float) -> void:
	var earth: Dictionary = result.earth
	_step_slams(t, earth.slams)
	if earth.slams[-1].phase < SLAMMED:
		return
	for slam: Dictionary in earth.slams:
		if not _ring_past(slam.ring):
			return
	result.clear = true


#AIR: THE JAWS

# Bixby flies to his lair over the maw farther off, Liam blows at him, and the maw's zone fades in. `at` is when the
# jaws start in their result: at its start, or in the undertow once the wave is off the floor.
func _begin_air(at: float) -> void:
	liam.play(&"blow", &"channel")
	var index := pinned_maw if pinned_maw >= 0 else Layout.maw_for(_soles())
	var maw: Vector2 = Layout.MAWS[index]
	var air := {maw = maw, index = index, undertow = result.has("water"), at = at, start = _soles(), swallowed = false,
		swallow_at = -1.0, spat = false, bite_at = -1.0, contact_at = -1.0, bite_result = -1, bites = [], homing = false,
		done_at = -1.0, drift_max = 0.0, nearest = INF, pulling = false}
	result.air = air
	air_log.append(air)
	_fly_bixby(maw, Layout.AIR_LIFT, Layout.LAIR_TIME)
	bixby.play(&"inhale")
	maw_zone = _build_maw(maw)
	_sound(&"air")


func _step_air(t: float) -> void:
	var air: Dictionary = result.air
	var into := t - float(air.at)
	if is_instance_valid(maw_zone):
		maw_zone.modulate.a = _share(into, Layout.MAW_FADE)
	if air.swallowed:
		_hold_swallowed(air, t)
	else:
		_pull(air, into)
		if air.contact_at < 0.0 and Layout.in_maw(_soles(), air.maw):
			if player().receive_hit(HitInfo.make(Layout.SWALLOW_ID, bixby.sprite, _player_centre(), bixby)) == HitInfo.Result.HIT:
				_swallow(air, t)
				return
		if air.bites.is_empty() and into >= Layout.PULL_START + Layout.PULL_TIME - CLOCK_SLACK:
			air.bite_at = t
			air.bites.append(_begin_bite(&"jaws", Layout.BITE_ID, t, Layout.AIR_LIFT))
		if not air.bites.is_empty():
			_step_jaws(air, t)
	if air.done_at >= 0.0 and t >= air.done_at - CLOCK_SLACK:
		result.clear = true


# Toward the maw, ramped in, every step it lasts; walking away beats it. `into` is from the jaws' start.
func _pull(air: Dictionary, into: float) -> void:
	var pull := Layout.pull_at(into)
	if into >= Layout.PULL_START - CLOCK_SLACK and not air.pulling and into < Layout.PULL_START + Layout.PULL_TIME:
		air.pulling = true
		_mark_live()
		_suck(air.maw, Layout.pull_speed())
	if air.pulling and into >= Layout.PULL_START + Layout.PULL_TIME - CLOCK_SLACK:
		air.pulling = false
		_stop_suction()
	air.nearest = minf(air.nearest, ((_soles() - Vector2(air.maw)) / Layout.R_MAW).length())
	if pull <= 0.0:
		return
	var to: Vector2 = Vector2(air.maw) - _soles()
	if to.length() > 1.0:
		player().add_drift(to.normalized() * pull)
		air.drift_max = maxf(air.drift_max, pull)


# The first bite, then the second: once the first has landed he recoils, flies back over his maw, and snaps again
# SECOND_BITE_GAP after it, whatever it came to. Done CLEAR_AFTER after the second.
func _step_jaws(air: Dictionary, t: float) -> void:
	var bite: Dictionary = air.bites[-1]
	if _step_bite(bite, t) and air.bites.size() == 1:
		air.contact_at = t
		air.bite_result = bite.result
	if bite.contact_at < 0.0:
		return
	if air.bites.size() > 1:
		if air.done_at < 0.0:
			air.done_at = float(bite.contact_at) + Layout.CLEAR_AFTER
		return
	var since := t - float(bite.contact_at)
	if not air.homing and since >= Layout.RECOIL_TIME - CLOCK_SLACK:
		air.homing = true
		bixby.play(&"inhale")
		_fly_bixby(air.maw, Layout.AIR_LIFT, Layout.SECOND_BITE_GAP - Layout.RECOIL_TIME)
	if since >= Layout.SECOND_BITE_GAP - CLOCK_SLACK:
		air.bites.append(_begin_bite(&"jaws2", Layout.BITE_ID, t, Layout.AIR_LIFT))


# Swallowed whole: the jaws close on them, held unseen for SWALLOW_HOLD, one chomp, and spat out toward the middle.
func _swallow(air: Dictionary, t: float) -> void:
	air.swallowed = true
	air.swallow_at = t
	holding = true
	player().grab()
	_clear_tell(bixby)
	_stop_suction()
	bixby.play(Layout.bite_anim())
	_sound(&"bite")
	_hold_swallowed(air, t)


func _hold_swallowed(air: Dictionary, t: float) -> void:
	var p := player()
	if not air.spat:
		p.global_position = Vector2(air.maw) - Vector2(0, Layout.SOLES_OVER_ORIGIN)
		p.velocity = Vector2.ZERO
	if air.spat or t < float(air.swallow_at) + Layout.SWALLOW_HOLD - CLOCK_SLACK:
		return
	air.spat = true
	p.take_grab_damage(Layout.CHOMP_ID)
	_sound(&"chomp")
	var out: Vector2 = (FLOOR_MIDDLE - Vector2(air.maw)).normalized()
	var rim: Vector2 = Vector2(air.maw) + out / (out / Layout.R_MAW).length()
	p.global_position = rim + out * Layout.SPIT_CLEAR - Vector2(0, Layout.SOLES_OVER_ORIGIN)
	holding = false
	p.release_grab(out)
	air.done_at = t + Layout.CLEAR_AFTER


#THE BITES (the jaws' two and the shark's snap after the wave)

# The red badge on his head and his rear back off the player, rising to `lift`: BITE_TELL from the badge to the
# snap, the reaction parry's. `t` is from the result's start.
func _begin_bite(kind: StringName, id: StringName, t: float, lift: float) -> Dictionary:
	bixby_driven = true
	bixby_path = {}
	var away: Vector2 = bixby.global_position - player().global_position
	var bite := {kind = kind, id = id, at = t, clock = wheel_clock, contact_at = -1.0, contact_clock = -1.0, result = -1,
		rear_from = bixby.global_position,
		rear_to = bixby.global_position + (away.normalized() if away.length() > 1.0 else Vector2.UP) * Layout.REAR_BACK,
		lift_from = bixby_lift, lift = lift, recoil_from = Vector2.ZERO, recoil_dir = Vector2.DOWN, recoiled = false}
	bite_log.append(bite)
	bixby.play(Layout.bite_anim())
	_telegraph(bixby, id, Layout.BITE_TELL + 0.1, _bixby_head)
	_sound(&"bite")
	return bite


# The rear, then the lunge homing on the hurtbox's centre, the contact exactly BITE_TELL after the badge (true on its
# step); a parried bite then throws him back over RECOIL_TIME.
func _step_bite(bite: Dictionary, t: float) -> bool:
	var into := t - float(bite.at)
	if bite.contact_at < 0.0:
		if into < Layout.BITE_REAR:
			var r := _ease_out(into / Layout.BITE_REAR)
			_drive_bixby(Vector2(bite.rear_from).lerp(bite.rear_to, r), lerpf(bite.lift_from, bite.lift, r))
			return false
		var s := clampf((into - Layout.BITE_REAR) / Layout.BITE_LUNGE, 0.0, 1.0)
		var jaws := _player_centre() - _jaws_offset()
		_drive_bixby(Vector2(bite.rear_to).lerp(jaws, s * s), lerpf(bite.lift, 0.0, s))
		if into >= Layout.BITE_TELL - CLOCK_SLACK:
			_bite(bite, t)
			return true
		return false
	if bite.result == HitInfo.Result.PARRIED and not bite.recoiled:
		var back := _ease_out(_share(t - float(bite.contact_at), Layout.RECOIL_TIME))
		_drive_bixby(Vector2(bite.recoil_from) + Vector2(bite.recoil_dir) * Layout.RECOIL * back, 0.0)
		bite.recoiled = back >= 1.0
	return false


func _bite(bite: Dictionary, t: float) -> void:
	_clear_tell(bixby)
	bite.contact_at = t
	bite.contact_clock = wheel_clock
	var p := player()
	var result_now: int = p.receive_hit(HitInfo.make(bite.id, bixby.sprite, _player_centre(), bixby))
	bite.result = result_now
	if result_now == HitInfo.Result.PARRIED:
		bite.recoil_from = bixby.global_position
		var away: Vector2 = bixby.global_position - p.global_position
		bite.recoil_dir = away.normalized() if away.length() > 1.0 else Vector2.DOWN
		bixby.sprite.modulate = Layout.BITE_FLASH
		bixby.create_tween().tween_property(bixby.sprite, "modulate", Color.WHITE, Layout.RECOIL_TIME)
	elif result_now == HitInfo.Result.HIT:
		_sound(&"chomp")


# Where his jaws are off his floor point, his lift at 0: the drawn bite's snap frame's, its stand-in's until then.
func _jaws_offset() -> Vector2:
	return (Layout.jaws() - Layout.BIXBY_FEET - Vector2(0, 1)) * Layout.SCALE


func _build_maw(at: Vector2) -> Node2D:
	var look: Dictionary = Layout.PLACEHOLDER_MAW
	var zone := Node2D.new()
	zone.name = "MawZone"
	var points := PackedVector2Array()
	for i in look.points:
		points.append(Vector2.from_angle(TAU * i / look.points) * Layout.R_MAW)
	var fill := Polygon2D.new()
	fill.polygon = points
	fill.color = look.fill
	zone.add_child(fill)
	var rim := Line2D.new()
	rim.points = points
	rim.closed = true
	rim.width = look.rim_width
	rim.default_color = look.rim
	zone.add_child(rim)
	zone.modulate.a = 0.0
	add_hazard(zone, at, god.layer(&"floor"))
	result_nodes.append(zone)
	return zone


func _suck(maw: Vector2, speed: float) -> void:
	_stop_suction()
	suction = SuctionScript.new()
	suction.name = "WheelSuction"
	suction.player = player()
	suction.mouths = [maw] as Array[Vector2]
	suction.pull_speed = speed
	suction.area = FLOOR_RECT
	add_hazard(suction, Vector2.ZERO, god.layer(&"floor"))


func _stop_suction() -> void:
	if is_instance_valid(suction):
		suction.stop()
	suction = null


# Whatever the result left: its hazards gone or past the player, the drift stopped, Bixby home.
func _end_result() -> void:
	_end_result_nodes()
	if is_instance_valid(bixby):
		bixby_driven = false
		bixby.set_clipped(false)
		bixby.play(&"hover")
		_fly_bixby(Layout.BIXBY_REST, Layout.BIXBY_LIFT, Layout.HOME_TIME)
	result = {}


func _end_result_nodes() -> void:
	_stop_suction()
	_stop_wind()
	for node in result_nodes:
		if is_instance_valid(node):
			node.queue_free()
	result_nodes.clear()
	maw_zone = null


#THE CRASH, THE WALK AND THE PAYOFF

# Liam drops out of the Avatar State and falls, the wheel shatters, Bixby comes down, their strings go slack.
func _begin_crash() -> void:
	beat = Beat.CRASH
	beat_at = wheel_clock
	_floor(false)
	bobbing = false
	wheel.shatter()
	_sound(&"shatter")
	if Layout.final_avatar_off():
		liam.play(&"channel_hold")
		_flare(Layout.AVATAR_OFF_SHEET, Layout.AVATAR_OFF_TIMES, &"off")
		_glow_to(0.0, Layout.strip_time(Layout.AVATAR_OFF_TIMES))
		liam_falls_at = beat_at + Layout.strip_time(Layout.AVATAR_OFF_TIMES)
	else:
		_glow_to(0.0, Layout.PLACEHOLDER_GLOW.burst_time)
		liam_falls_at = beat_at
	liam_fallen = false
	bixby_driven = false
	bixby.set_clipped(false)
	bixby.play(&"hit")
	_fly_bixby(Layout.BIXBY_DOWN, 0.0, Layout.CRASH_FALL, Layout.CRASH_ARC)
	crash_landed = false
	var strings: Node2D = god.layer(&"strings")
	for puppet: Node2D in _pair_up():
		strings.set_tension(puppet, GodLayout.TENSION_LIMP)
	if hits == 0:
		player().hype.add(Layout.HYPE_CLEAN)
	god.play(&"control")


func _step_crash() -> void:
	if not liam_fallen and _due(liam_falls_at):
		liam_fallen = true
		_liam_falls()
	if not crash_landed and _due(beat_at + Layout.CRASH_FALL):
		crash_landed = true
		bixby.play(&"land", &"recover")
		_sound(&"crash")
		ScreenView.shake(get_tree(), Layout.SLAM_SHAKE.strength, Layout.SLAM_SHAKE.steps, Layout.SLAM_SHAKE.step)


# Out of the State, he drops straight down onto his mark, landing as the crash ends. His standing sheets stand 12 rows
# lower in their cells than his drawn float, so his lift takes the difference as he changes, and nothing jumps.
func _liam_falls() -> void:
	liam.play(&"fall", &"downed")
	if Layout.final_float():
		liam_lift += (Layout.STAND_IN_PIVOT.y - Layout.FLOAT_PIVOT.y) * Layout.SCALE
	_lift_liam(0.0, maxf(beat_at + Layout.CRASH_TIME - wheel_clock, Layout.CRASH_FALL_MIN))


# Both down and open: the stars on them, either can be taken.
func _open() -> void:
	result = {}
	beat = Beat.WALK
	beat_at = wheel_clock
	if is_instance_valid(wheel):
		wheel.queue_free()
	wheel = null
	for puppet: Node2D in _pair_up():
		puppet.set_punchable(true)
	_show_stars()
	rounds_over.emit()


# The first one in reach is the one they fight; the nearer, in reach of both.
func _walk() -> void:
	var body := player()
	var best: Node2D = null
	var best_distance := INF
	for puppet: Node2D in _pair_up():
		if not _in_reach(puppet):
			continue
		var distance := body.global_position.distance_to(_hurt_centre(puppet))
		if distance < best_distance:
			best = puppet
			best_distance = distance
	if best == null:
		return
	target = best
	for puppet: Node2D in _pair_up():
		if puppet != target:
			puppet.set_punchable(false)
	beat = Beat.PAYOFF
	reached.emit()


# In the uppercut's reach of it (PlayerFinisher._in_reach: its hurtbox grown uppercut_reach), with a margin to spare.
func _in_reach(puppet: Node2D) -> bool:
	var body := player()
	var shape: CollisionShape2D = puppet.get_finisher_hurtbox().get_node("CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	return box.grow(body.finisher.uppercut_reach - Layout.REACH_MARGIN).has_point(body.global_position)


func _hurt_centre(puppet: Node2D) -> Vector2:
	var shape: CollisionShape2D = puppet.get_finisher_hurtbox().get_node("CollisionShape2D")
	return shape.global_position


func _show_stars() -> void:
	var spec := FinisherArtLayout.stars()
	var pivot: Vector2 = spec.pivot
	stars_clock = 0.0
	for puppet: Node2D in _pair_up():
		var star := Sprite2D.new()
		star.name = "DazeStars_%s" % puppet.boss
		star.texture = load(spec.texture)
		star.hframes = spec.hframes
		star.centered = false
		star.offset = -pivot
		star.scale = Vector2.ONE * spec.scale
		add_hazard(star, puppet.get_daze_anchor(), god.layer(&"fx"))
		stars.append(star)


func _spin_stars(delta: float) -> void:
	if stars.is_empty():
		return
	stars_clock += delta
	var frame := int(stars_clock / FinisherArtLayout.stars().frame_time)
	for star in stars:
		if is_instance_valid(star):
			star.frame = frame % star.hframes


func _clear_stars() -> void:
	for star in stars:
		if is_instance_valid(star):
			star.queue_free()
	stars.clear()


#LIAM

func _pose_liam(element: int) -> void:
	var pose: StringName = LIAM_POSES[element]
	if element == WATER and is_instance_valid(bixby) and bixby.global_position.x > liam.global_position.x:
		pose = &"cast_right"
	liam.play(pose, &"channel")


func _lift_liam(to: float, time: float) -> void:
	liam_lift_from = liam_lift
	liam_lift_to = to
	liam_lift_at = wheel_clock
	liam_lift_time = time


func _step_liam() -> void:
	if not is_instance_valid(liam):
		return
	var t := _share(wheel_clock - liam_lift_at, liam_lift_time)
	liam_lift = lerpf(liam_lift_from, liam_lift_to, _ease_out(t))
	var bob := sin(TAU * Layout.LIAM_BOB_HZ * wheel_clock) * Layout.LIAM_BOB if bobbing else 0.0
	liam.sprite.position = liam.sprite_base_position + Vector2(0, -roundf(liam_lift + bob))


# His float pivot where he is drawn now: on the hub once he is lifted.
func _liam_pivot() -> Vector2:
	var raised: float = liam.sprite.position.y - liam.sprite_base_position.y
	return liam.global_position + Vector2(0, raised - (Layout.LIAM_CELL.y - Layout.float_pivot().y) * Layout.SCALE)


#HIS GLOW

# A copy of his frame over him, added: his pose's own glow strip once it is in, his frame in rune blue until then; and
# his aura, its back layer behind him and its front over him, once it is in.
func _build_glow() -> void:
	glow = Sprite2D.new()
	glow.name = "AvatarGlow"
	var additive := CanvasItemMaterial.new()
	additive.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	glow.material = additive
	glow.add_to_group(GodLayout.HAZARD_GROUP)
	liam.mask.add_child(glow)
	auras.clear()
	if Layout.final_aura():
		for path: String in [Layout.AURA_BACK_SHEET, Layout.AURA_FRONT_SHEET]:
			var aura := Sprite2D.new()
			aura.name = "AvatarAura"
			aura.texture = load(path)
			aura.hframes = maxi(roundi(aura.texture.get_width() / Layout.AURA_FRAME.x), 1)
			aura.centered = false
			aura.offset = -Layout.AURA_ANCHOR
			aura.scale = Vector2.ONE * Layout.SCALE
			aura.add_to_group(GodLayout.HAZARD_GROUP)
			liam.mask.add_child(aura)
			auras.append(aura)
		liam.mask.move_child(auras[0], 0)
	glow_level = 0.0
	flare = {}
	_step_glow()


# The State's flare in or burst out, added over his held frame.
func _flare(path: String, times: Array, kind: StringName) -> void:
	flare = {texture = load(path), times = times, at = wheel_clock, kind = kind}


func _glow_to(level: float, time: float) -> void:
	glow_from = glow_level
	glow_to = level
	glow_at = wheel_clock
	glow_time = time


func _step_glow() -> void:
	if not is_instance_valid(glow) or not is_instance_valid(liam):
		return
	glow_level = lerpf(glow_from, glow_to, _share(wheel_clock - glow_at, glow_time))
	# Flared, it settles to its held level.
	if glow_to >= Layout.PLACEHOLDER_GLOW.flare and _due(glow_at + glow_time):
		_glow_to(Layout.PLACEHOLDER_GLOW.held, Layout.PLACEHOLDER_GLOW.flare_time)
	var sprite: Sprite2D = liam.sprite
	var strength := minf(glow_level / Layout.PLACEHOLDER_GLOW.held, 1.0)
	for aura in auras:
		aura.position = sprite.position
		aura.frame = int(wheel_clock / Layout.AURA_TIME) % aura.hframes
		aura.modulate.a = strength
		aura.visible = strength > 0.001
	glow.offset = sprite.offset
	glow.flip_h = sprite.flip_h
	glow.scale = sprite.scale
	glow.position = sprite.position
	if not flare.is_empty():
		var into := wheel_clock - float(flare.at)
		var length := Layout.strip_time(flare.times)
		if into < length:
			glow.texture = flare.texture
			glow.hframes = maxi(roundi(glow.texture.get_width() / Layout.LIAM_CELL.x), 1)
			glow.vframes = 1
			glow.frame = mini(LiamArtLayout.frame_at(flare.times, flare.times.size(), into / length), glow.hframes - 1)
			glow.modulate = Color.WHITE
			glow.visible = true
			return
		if flare.kind == &"on":
			liam.play(&"channel")
		flare = {}
	var strip := Layout.glow_sheet(sprite.texture.resource_path if sprite.texture != null else "")
	glow.texture = load(strip) if strip != "" else sprite.texture
	glow.hframes = sprite.hframes
	glow.vframes = sprite.vframes
	glow.frame = sprite.frame
	var colour: Color = Color.WHITE if strip != "" else Layout.PLACEHOLDER_GLOW.colour
	colour.a = glow_level if strip == "" else strength
	glow.modulate = colour
	glow.visible = glow_level > 0.001


#BIXBY

# From where he is to `to` (his floor point) at `lift`, over `time`, `arc` px over the line at its middle.
func _fly_bixby(to: Vector2, lift: float, time: float, arc := 0.0) -> void:
	bixby_driven = false
	bixby_path = {from = bixby.global_position, to = to, lift_from = bixby_lift, lift_to = lift, at = wheel_clock,
		time = time, arc = arc}
	if absf(to.x - bixby.global_position.x) > 1.0:
		bixby.face(to.x < bixby.global_position.x)


func _step_bixby() -> void:
	if not is_instance_valid(bixby) or bixby_driven or bixby_path.is_empty():
		_place_bixby_lift()
		return
	var t := _share(wheel_clock - float(bixby_path.at), bixby_path.time)
	var eased := _ease_out(t)
	bixby.global_position = Vector2(bixby_path.from).lerp(bixby_path.to, eased).round()
	bixby_lift = lerpf(bixby_path.lift_from, bixby_path.lift_to, eased) + float(bixby_path.arc) * 4.0 * t * (1.0 - t)
	_place_bixby_lift()
	if t >= 1.0:
		bixby_path = {}


func _place_bixby_lift() -> void:
	if is_instance_valid(bixby):
		bixby.sprite.position = bixby.sprite_base_position + Vector2(0, -roundf(bixby_lift))


# Put where a result drives him: his floor point and his lift.
func _drive_bixby(at: Vector2, lift: float) -> void:
	bixby_driven = true
	bixby_path = {}
	bixby.global_position = at.round()
	bixby_lift = lift
	_place_bixby_lift()


func _bixby_head() -> Vector2:
	return bixby.hook_point(&"head") + Vector2(0, -Layout.BADGE_GAP)


func _telegraph(puppet: Node2D, id: StringName, seconds: float, anchor: Callable) -> void:
	ParryTell.telegraph(puppet, id, seconds, anchor)
	var tell := puppet.get_parent().get_node_or_null("ParryTell%d" % puppet.get_instance_id())
	if tell != null:
		tell.scale = Vector2.ONE * GodLayout.ui_scale()


# Gone at once: the badges live beside the puppet on the Stage, not under it.
func _clear_tell(puppet: Node2D) -> void:
	if not is_instance_valid(puppet) or puppet.get_parent() == null:
		return
	for child in puppet.get_parent().get_children():
		if String(child.name).begins_with("ParryTell%d" % puppet.get_instance_id()):
			child.queue_free()


func _count_badges() -> void:
	var count := 0
	for puppet: Node2D in _pair_up():
		if not is_instance_valid(puppet) or puppet.get_parent() == null:
			continue
		var tell := puppet.get_parent().get_node_or_null("ParryTell%d" % puppet.get_instance_id())
		if tell != null and not tell.is_queued_for_deletion():
			count += 1
	max_badges = maxi(max_badges, count)


#SEE-THROUGH

# Liam and Bixby ease to SEE_THROUGH while their drawn frame covers the player's hurtbox centre.
func _see_through(delta: float) -> void:
	var body := player()
	if body == null:
		return
	var centre: Vector2 = body.hurtBox.get_node("CollisionShape2D").global_position
	var rate := (1.0 - Layout.SEE_THROUGH) / Layout.SEE_THROUGH_FADE * delta
	for puppet: Node2D in _pair_up():
		if not is_instance_valid(puppet) or beat == Beat.WALK or beat == Beat.PAYOFF:
			if is_instance_valid(puppet):
				puppet.modulate.a = move_toward(puppet.modulate.a, 1.0, rate)
			continue
		var drawn: Rect2 = puppet.sprite.get_global_transform() * puppet.sprite.get_rect()
		var to := Layout.SEE_THROUGH if drawn.has_point(centre) else 1.0
		puppet.modulate.a = move_toward(puppet.modulate.a, to, rate)


#THE STAMINA FLOOR

func _floor(on: bool) -> void:
	flooring = on
	var body := player()
	if body == null:
		return
	var defense: Node = body.defense
	if on and not defense.stamina_changed.is_connected(_on_stamina_changed):
		defense.stamina_changed.connect(_on_stamina_changed)
	elif not on and defense.stamina_changed.is_connected(_on_stamina_changed):
		defense.stamina_changed.disconnect(_on_stamina_changed)
	if on:
		_hold_floor()


func _on_stamina_changed(value: float, _max_value: float) -> void:
	if flooring and value < Layout.STAMINA_FLOOR - 0.0001:
		_hold_floor()


func _hold_floor() -> void:
	var defense: Node = player().defense
	floor_min = minf(floor_min, defense.stamina)
	if defense.stamina < Layout.STAMINA_FLOOR:
		defense.refund(Layout.STAMINA_FLOOR - defense.stamina)


#HINTS, SOUNDS AND HITS

# The first time each: a double's own (the doubles' one for those without), then each element's.
func _give_hint(elements: Array) -> void:
	var text := ""
	var index: int = Layout.DOUBLES.find(elements)
	var double_key := -2 - index if Layout.DOUBLE_HINTS.has(index) else -1
	if elements.size() > 1 and not hints_given.has(double_key):
		hints_given[double_key] = true
		text = Layout.DOUBLE_HINTS.get(index, Layout.DOUBLE_HINT)
	elif not hints_given.has(elements[0]):
		hints_given[elements[0]] = true
		text = Layout.HINTS[elements[0]]
	if text == "":
		return
	hint(text)
	hint_up = true
	hint_off_at = wheel_clock + Layout.HINT_TIME


func _build_sounds() -> void:
	sound_holder = Node2D.new()
	sound_holder.name = "WheelSounds"
	add_hazard(sound_holder, Vector2.ZERO, god.layer(&"fx"))
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
			sound_holder.add_child(voice)
			voices.append(voice)
		sounds[key] = voices


func _sound(key: StringName) -> void:
	var voices: Array = sounds.get(key, [])
	if voices.is_empty():
		return
	var voice: AudioStreamPlayer = voices.pop_front()
	voices.append(voice)
	if is_instance_valid(voice):
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


func _on_hit_taken(hit: RefCounted) -> void:
	hits += 1
	hit_log.append({id = hit.attack_id, at = wheel_clock, damage = hit.damage})


# Whatever holds the player lets go: a swallow spits them out.
func _let_go() -> void:
	var p := player()
	if holding and p != null and p.is_grabbed:
		p.release_grab(Vector2.UP)
	holding = false
	_stop_suction()


# Liam and Bixby, those still there: a freed one can't go in a typed array.
func _pair_up() -> Array[Node2D]:
	var out: Array[Node2D] = []
	for puppet in [liam, bixby]:
		if is_instance_valid(puppet):
			out.append(puppet)
	return out


func _player_centre() -> Vector2:
	return player().hurtBox.get_node("CollisionShape2D").global_position


#HELPERS

func _soles() -> Vector2:
	return player().global_position + Vector2(0, Layout.SOLES_OVER_ORIGIN)


func _hurt_box() -> Rect2:
	var shape: CollisionShape2D = player().hurtBox.get_node("CollisionShape2D")
	return shape.global_transform * shape.shape.get_rect()


# How far through `time` `clock_in` is, 1 once it has run it.
static func _share(clock_in: float, time: float) -> float:
	if clock_in + CLOCK_SLACK >= time:
		return 1.0
	return clampf(clock_in / maxf(time, 0.0001), 0.0, 1.0)


static func _ease_out(x: float) -> float:
	var left := 1.0 - clampf(x, 0.0, 1.0)
	return 1.0 - left * left
