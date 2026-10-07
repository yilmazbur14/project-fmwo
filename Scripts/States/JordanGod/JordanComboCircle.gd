extends "res://Scripts/States/JordanGod/JordanCombo.gd"

# Jordan's attack 4, Carter + Mason's circle: the user's own design and sketch (2026-09-28; every number is
# JordanCircleLayout's). Jordan raises Carter and Mason and puts the player in the middle of the floor; Carter's eyes go
# and a circle of his clones forms round them. From the clone nearest the player they fire his beams in turn,
# clockwise, each one through the middle, a lap round: the player keeps running round the circle ahead of
# them. Jordan holds Mason up on his strings ahead of the beams, dropping poo bombs on the path the player must
# run, and swings him back out in front of a player who dashes past his bombs. Then Mason is brought down beside Carter,
# both are left open, and the first one the player walks up to is the one they take apart.
#
# NOTHING HERE IS PARRIED: a beam costs a heart and only running ahead of it answers it, so there is no badge (the aim
# lines are the warning) and the i-frames space the hits; a bomb costs half a heart, and a dash carries the player
# across one.
#
# THE BEATS: the warp, the summon, Carter's flash and the forming are a coroutine (run) on the combo's own waits. From
# the forming on, everything is timed on circle_clock, summed on Physics_Update, so it is game time that a pause and a
# finisher's freeze hold: the schedule of charges and fires, the clones, Mason's flight and his bombs, the contact and
# the laps, and Mason's flights in and out. The coroutine takes over again for the end, the open, the payoff and the
# wrap. A run left behind by a cut never resumes into the next one (generation).
#
# THE PLAYER is sealed for the warp, the summon and the forming, then free: an invisible wall of segments just inside
# the clones' feet keeps them in the circle. They draw one z over the clones for the whole attack, as Mason in the air
# and his bombs do.
#
# ONE REPORT A STEP: the live band first (one beam hurts at a time, back to back), then the bombs. A step the player is
# in the band never reaches the bombs, and the i-frames of a hit cover a bomb under them, which stays.

const Layout := preload("res://Scripts/JordanCircleLayout.gd")
const CarterArtLayout := preload("res://Scripts/CarterArtLayout.gd")
const FinisherArtLayout := preload("res://Scripts/FinisherArtLayout.gd")
const PlayerScript := preload("res://Scripts/PlayerScript.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const BEAM_SCRIPT := preload("res://Scripts/JordanCircleBeam.gd")
const POO_SCRIPT := preload("res://Scripts/JordanCirclePoo.gd")

const CARTER := &"carter"
const MASON := &"mason"
const WAITING := &"waiting"
const CHARGING := &"charging"
const FIRING := &"firing"
# A float clock summed a step at a time lands a hair short of a beat's end.
const CLOCK_SLACK := 0.0001

# The last beam is gone.
signal loop_over
# The player has walked into reach of one of the pair.
signal reached

enum Beat { OFF, FORM, LOOP, END, WALK, PAYOFF }
enum Flight { REST, ENTRY, FLY, RETURN, LANDED }


# One of the circle: his figure, the ball and the aim line of its charge, and the axis it always fires down.
class Clone:
	var figure: Sprite2D
	var pose := &""
	var pose_since := 0.0
	var ball: Node2D
	var aim: Line2D
	var palms := Vector2.ZERO
	var angle := 0.0
	var length := 0.0
	var charge_at := 0.0
	var charge_time := 1.0


# The hint is the fight's first run's alone.
var hint_given := false
var hint_up := false
var hint_off_at := 0.0
var generation := 0
var beat := Beat.OFF
# The player is down: nothing more happens, and the fight's end releases this.
var stopped := false
# From the forming's start, in game seconds: every beat from there on is timed on it.
var circle_clock := 0.0
var carter: Node2D
var mason: Node2D
# The clone that fires first.
var k0 := 0
var clones: Array[Clone] = []
# Every fire in turn, on circle_clock: {clone, charge_at, fire_at, land_at, off_at, gone_at}.
var schedule: Array[Dictionary] = []
var next_charge := 0
var next_fire := 0
# The beams out, in fire order: {node, fire, clone, landed, landing, live, done}.
var beams: Array[Dictionary] = []
# Mason's bombs on the floor.
var turds: Array[Node2D] = []
var wall: StaticBody2D
var sound_holder: Node2D
var sound_players := {}
var hum: AudioStreamPlayer
var tint: ShaderMaterial
var textures := {}

var flight := Flight.REST
var flight_at := 0.0
var flight_from := Vector2.ZERO
var flight_lift := 0.0
# His angle round the circle, unwrapped from where he came in (mason_start), and the one he is flying to.
var mason_start := 0.0
var mason_angle := 0.0
var mason_target := 0.0
var mason_lift := 0.0
var catching_up := false
var last_yank_at := -INF
# The next zigzag peak he drops at, counted from his start.
var next_mark := 0
var first_fired := false
var shadow: Sprite2D

var target: Node2D
var stars: Array[Sprite2D] = []
var stars_clock := 0.0
var bars := -1
var saved_z := 0
var player_raised := false
var lap_hits: Array[int] = []
var laps_paid := 0
var hits := 0
var loop_done := false
# For tests, on circle_clock: every fire (its clone, when it fired and when it landed), every beam hit, every bomb's
# report and every drop (with Mason's angle and the player's).
var fires: Array[Dictionary] = []
var beam_hits: Array[Dictionary] = []
var poo_hits: Array[Dictionary] = []
var drops: Array[Dictionary] = []


func pair() -> Array[Dictionary]:
	return [
		{boss = CARTER, feet = Layout.CARTER_FEET, face_left = false, hand = &"left", hooks = [&"back"], strings = 2},
		{boss = MASON, feet = Layout.MASON_REST, face_left = false, hand = &"right", hooks = [&"back"], strings = 2},
	]


func run() -> void:
	generation += 1
	var run_of := generation
	_start()
	god.play(&"yank_right", &"control")
	warp_player(Layout.CENTRE, PlayerScript.Facing.UP)
	_raise_player()
	hud(false)
	_build_sounds()
	await wait(Layout.TELEPORT_TIME)
	if _gone(run_of):
		return
	await summon()
	if _gone(run_of):
		return
	carter = puppets.get(CARTER)
	mason = puppets.get(MASON)
	_flash()
	await wait(Layout.FLASH_TO_FORM)
	if _gone(run_of):
		return
	_begin_form()
	await wait(Layout.FORM_STAGGER * (Layout.CLONES - 1) + Layout.FORM_TIME)
	if _gone(run_of):
		return
	_close()
	await loop_over
	if _gone(run_of):
		return
	_end()
	await wait(Layout.MASON_RETURN_TIME)
	if _gone(run_of):
		return
	_open()
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


func release() -> void:
	generation += 1
	beat = Beat.OFF
	flight = Flight.REST
	if is_instance_valid(hum):
		hum.stop()
	_lower_player()
	super.release()
	loop_over.emit()
	reached.emit()


func Physics_Update(delta: float) -> void:
	super.Physics_Update(delta)
	if beat == Beat.OFF or cut or stopped:
		return
	if _player_down():
		stopped = true
		return
	circle_clock += delta
	if beat == Beat.LOOP:
		_run_schedule()
	_step_beams()
	_step_clones()
	_run_mason(delta)
	_step_turds(delta)
	match beat:
		Beat.LOOP:
			if not _beam_contact():
				_poo_contact()
		Beat.WALK:
			_walk()
		Beat.PAYOFF:
			# The finisher's own stars take over as it dazes the one being taken apart.
			if not stars.is_empty() and player().finisher.is_active():
				_clear_stars()
	_spin_stars(delta)
	if hint_up and _due(hint_off_at):
		hint_up = false
		hide_hint()
	if beat == Beat.LOOP:
		_run_laps()


func _start() -> void:
	beat = Beat.OFF
	stopped = false
	circle_clock = 0.0
	carter = null
	mason = null
	k0 = 0
	clones.clear()
	schedule.clear()
	next_charge = 0
	next_fire = 0
	beams.clear()
	turds.clear()
	wall = null
	sound_holder = null
	sound_players.clear()
	hum = null
	hint_up = false
	flight = Flight.REST
	flight_at = 0.0
	mason_start = 0.0
	mason_angle = 0.0
	mason_target = 0.0
	mason_lift = 0.0
	catching_up = false
	last_yank_at = -INF
	next_mark = 0
	first_fired = false
	shadow = null
	target = null
	stars.clear()
	bars = -1
	lap_hits.clear()
	for lap in Layout.lap_count():
		lap_hits.append(0)
	laps_paid = 0
	hits = 0
	loop_done = false
	fires.clear()
	beam_hits.clear()
	poo_hits.clear()
	drops.clear()


func _gone(run_of: int) -> bool:
	return cut or run_of != generation


func _due(at: float) -> bool:
	return circle_clock >= at - CLOCK_SLACK


#THE CIRCLE FORMING

# His eyes go, and he takes his stance to conduct.
func _flash() -> void:
	carter.play(&"eye_flash", &"messatsu_charge")
	god.play(&"yank_left", &"control")
	_play(&"flash")


# The clones fade in nearest Carter first, one after another.
func _begin_form() -> void:
	beat = Beat.FORM
	circle_clock = 0.0
	var order: Array[int] = []
	for i in Layout.CLONES:
		order.append(i)
	order.sort_custom(func(a: int, b: int) -> bool: return _from_carter(a) < _from_carter(b))
	for i in Layout.CLONES:
		clones.append(_build_clone(i))
	for n in order.size():
		var figure: Sprite2D = clones[order[n]].figure
		var form := figure.create_tween()
		form.tween_interval(n * Layout.FORM_STAGGER)
		form.tween_property(figure, "modulate:a", Layout.CLONE_TINT.a, Layout.FORM_TIME)
	_play(&"warp")


static func _from_carter(i: int) -> float:
	return Layout.clone_feet(i).distance_to(Layout.CARTER_FEET)


# The circle closes: the wall goes up, the player is let go, and Mason is swung in over the circle.
func _close() -> void:
	beat = Beat.LOOP
	var p := player()
	k0 = Layout.first_clone(_soles(), FACINGS[clampi(p.facing, 0, FACINGS.size() - 1)])
	_build_schedule(circle_clock + Layout.LOOP_DELAY)
	_build_wall()
	p.unlock_actions()
	player_held = false
	if not hint_given:
		hint_given = true
		hint_up = true
		hint_off_at = circle_clock + Layout.HINT_TIME
		hint(Layout.HINT)
	god.play(&"yank_right", &"control")
	_begin_entry()


# The first charge `from`; each band live for its cadence, so the next takes over as it goes.
func _build_schedule(from: float) -> void:
	schedule.clear()
	var fire_at := from + Layout.charge_time(0)
	for k in Layout.FIRES:
		var off_at := fire_at + Layout.TRAVEL + Layout.cadence(k)
		schedule.append({clone = (k0 + k) % Layout.CLONES, charge_at = fire_at - Layout.charge_time(k), fire_at = fire_at,
			land_at = fire_at + Layout.TRAVEL, off_at = off_at, gone_at = off_at + Layout.FADE})
		fire_at += Layout.cadence(k)


func _build_wall() -> void:
	wall = StaticBody2D.new()
	wall.name = "CircleWall"
	wall.collision_layer = 1
	wall.collision_mask = 0
	var shape := CollisionPolygon2D.new()
	shape.build_mode = CollisionPolygon2D.BUILD_SEGMENTS
	shape.polygon = Layout.wall_polygon()
	wall.add_child(shape)
	add_hazard(wall, Layout.CENTRE, god.layer(&"floor"))


#THE SWEEP

# The sweep's round angle at `clock`, unwrapped from the first clone's: that clone's until it fires, then moving on to
# each next clone's as it fires, evenly between them.
func sweep_at(clock: float) -> float:
	var base := Layout.clone_round(k0)
	if schedule.is_empty() or clock < schedule[0].fire_at:
		return base
	var last := schedule.size() - 1
	for k in last:
		if clock < schedule[k + 1].fire_at:
			var gap: float = schedule[k + 1].fire_at - schedule[k].fire_at
			return base + Layout.CLONE_STEP * (k + (clock - schedule[k].fire_at) / gap)
	return base + Layout.CLONE_STEP * (last + (clock - schedule[last].fire_at) / Layout.cadence(last))


# How far ahead of the sweep's chasing half `soles` are, 0 to 180 round degrees.
func lead_of(soles: Vector2) -> float:
	return fposmod(Layout.round_angle(soles) - sweep_at(circle_clock), 180.0)


func _run_schedule() -> void:
	while next_charge < schedule.size() and _due(schedule[next_charge].charge_at):
		_charge(schedule[next_charge])
		next_charge += 1
	while next_fire < schedule.size() and _due(schedule[next_fire].fire_at):
		_fire(next_fire)
		next_fire += 1
	for shot in beams:
		var entry: Dictionary = schedule[shot.fire]
		if not shot.landed and _due(entry.land_at):
			shot.landed = true
			shot.landing = true
			shot.live = true
			fires[shot.fire].landed = circle_clock
		if shot.live and _due(entry.off_at):
			shot.live = false
			if is_instance_valid(shot.node):
				shot.node.fade(Layout.FADE)
		if not shot.done and _due(entry.gone_at):
			shot.done = true
			var clone: Clone = clones[shot.clone]
			if clone.pose == FIRING:
				_pose(clone, WAITING)
	beams = beams.filter(func(shot: Dictionary) -> bool: return not shot.done)


func _charge(entry: Dictionary) -> void:
	var clone: Clone = clones[entry.clone]
	clone.charge_at = entry.charge_at
	clone.charge_time = entry.fire_at - entry.charge_at
	_pose(clone, CHARGING)
	clone.ball.visible = true
	clone.aim.visible = true
	if is_instance_valid(hum) and not hum.playing:
		hum.play()


func _fire(k: int) -> void:
	var entry: Dictionary = schedule[k]
	var clone: Clone = clones[entry.clone]
	clone.ball.visible = false
	clone.aim.visible = false
	_pose(clone, FIRING)
	var beam: Node2D = BEAM_SCRIPT.new()
	beam.name = "CircleBeam%d" % k
	add_hazard(beam, clone.palms, god.layer(&"floor"))
	beam.setup(clone.palms, clone.angle, clone.length)
	beam.fire()
	beams.append({node = beam, fire = k, clone = entry.clone, landed = false, landing = false, live = false, done = false})
	fires.append({clone = entry.clone, at = circle_clock, landed = -1.0})
	first_fired = true
	_play(&"fire")


func _step_beams() -> void:
	for shot in beams:
		if is_instance_valid(shot.node):
			shot.node.step(circle_clock - schedule[shot.fire].fire_at)


# A lap with no beam hit pays hype as its last band goes out, a part lap its share; the whole loop with no hit of any
# kind, as its last beam is gone, and then the loop is over.
func _run_laps() -> void:
	while laps_paid < Layout.lap_count() and _due(schedule[laps_paid * Layout.CLONES + Layout.lap_fires(laps_paid) - 1].off_at):
		if lap_hits[laps_paid] == 0:
			player().hype.add(Layout.HYPE_LAP * Layout.lap_fires(laps_paid) / float(Layout.CLONES))
		laps_paid += 1
	if loop_done or not _due(schedule[schedule.size() - 1].gone_at):
		return
	loop_done = true
	if hits == 0:
		player().hype.add(Layout.HYPE_CLEAN)
	loop_over.emit()


#THE CLONES

func _build_clone(i: int) -> Clone:
	var clone := Clone.new()
	clone.palms = Layout.palms(i)
	clone.angle = Layout.beam_angle(i)
	clone.length = Layout.beam_length(i)
	var figure := Sprite2D.new()
	figure.name = "CircleClone%d" % i
	figure.scale = Vector2.ONE * CarterArtLayout.SCALE
	figure.flip_h = Layout.faces_left(i)
	figure.modulate = Layout.CLONE_TINT
	figure.modulate.a = 0.0
	clone.figure = figure
	_pose(clone, WAITING)
	add_hazard(figure, Layout.clone_feet(i), god.layer(&"stage"))
	clone.ball = _build_ball()
	add_hazard(clone.ball, clone.palms, god.layer(&"fx"))
	clone.aim = _build_aim(clone)
	add_hazard(clone.aim, clone.palms, god.layer(&"fx"))
	return clone


# Waiting on his charge's first frame, charging on its loop, firing on the fire's frames, whose brace holds through
# the band and its fade.
func _pose(clone: Clone, pose: StringName) -> void:
	var anim := CarterArtLayout.anim(&"messatsu_fire" if pose == FIRING else &"messatsu_charge")
	var frame_size: Vector2 = anim.get("frame_size", CarterArtLayout.FRAME_SIZE)
	var twin := PuppetLayout.twin_path(CARTER, anim.sheet)
	var sheet := _texture(twin if twin != "" else anim.sheet)
	clone.pose = pose
	clone.pose_since = circle_clock
	# Back to the first frame before the frame count changes, so the current one can't be out of range.
	clone.figure.frame = 0
	clone.figure.texture = sheet
	clone.figure.hframes = maxi(roundi(sheet.get_width() / frame_size.x), 1)
	clone.figure.offset = CarterArtLayout.sheet_offset(frame_size)
	clone.figure.material = null if twin != "" else _tint()
	clone.figure.frame = _clone_frame(clone)


func _clone_frame(clone: Clone) -> int:
	var anim := CarterArtLayout.anim(&"messatsu_fire" if clone.pose == FIRING else &"messatsu_charge")
	if clone.pose == WAITING:
		return anim.frames[0]
	return _pose_frame(anim, circle_clock - clone.pose_since)


func _step_clones() -> void:
	var ball_spec := CarterArtLayout.messatsu_ball()
	var drawn_at: float = ball_spec.get("scale", 1.0)
	var line := CarterArtLayout.PLACEHOLDER_MESSATSU_LINE
	for clone in clones:
		if not is_instance_valid(clone.figure):
			continue
		clone.figure.frame = _clone_frame(clone)
		if clone.pose != CHARGING or not is_instance_valid(clone.ball) or not is_instance_valid(clone.aim):
			continue
		var into := circle_clock - clone.charge_at
		clone.ball.scale = Vector2.ONE * drawn_at * lerpf(ball_spec.from_scale, 1.0,
			clampf(into / clone.charge_time, 0.0, 1.0))
		if ball_spec.has("texture"):
			(clone.ball as Sprite2D).frame = _looped_frame(ball_spec, into)
		if into + CLOCK_SLACK >= clone.charge_time - Layout.TELL_TIME:
			clone.aim.default_color = line.lit_color
		else:
			var dim := int(into / line.flicker_time) % 2 == 1
			clone.aim.default_color = line.color
			clone.aim.default_color.a = line.flicker_alpha if dim else line.color.a


# The Messatsu's ball gathering in the palms, drawn as light: the void is dark, as the Messatsu's own was.
func _build_ball() -> Node2D:
	var spec := CarterArtLayout.messatsu_ball()
	var ball: Node2D
	if spec.has("texture"):
		var pivot: Vector2 = spec.pivot
		var sheet := Sprite2D.new()
		sheet.texture = _texture(spec.texture)
		sheet.hframes = spec.hframes
		sheet.centered = false
		sheet.offset = -pivot
		ball = sheet
	else:
		var shape := Polygon2D.new()
		shape.polygon = CarterArtLayout.ellipse(Vector2.ONE * spec.radius, spec.points)
		shape.color = spec.color
		ball = shape
	ball.name = "ChargeBall"
	ball.material = CarterArtLayout.additive()
	ball.visible = false
	return ball


# Down the clone's axis to the far end of its beam, drawn at UI scale to read at its own width in the 2/3 view.
func _build_aim(clone: Clone) -> Line2D:
	var spec := CarterArtLayout.PLACEHOLDER_MESSATSU_LINE
	var line := Line2D.new()
	line.name = "AimLine"
	line.width = spec.width * GodLayout.ui_scale()
	line.default_color = spec.color
	line.points = PackedVector2Array([Vector2.ZERO, (Vector2.from_angle(clone.angle) * clone.length).round()])
	line.visible = false
	return line


# The frame `anim` is on `clock` seconds in, `times` repeating its last value; one that doesn't loop holds its last.
func _pose_frame(anim: Dictionary, clock_in: float) -> int:
	var frames: Array = anim.frames
	var times: Array = anim.times
	var total := 0.0
	for i in frames.size():
		total += times[mini(i, times.size() - 1)]
	var into := clock_in + CLOCK_SLACK
	if anim.loop:
		into = fposmod(into, maxf(total, 0.0001))
	for i in frames.size():
		into -= times[mini(i, times.size() - 1)]
		if into < 0.0:
			return frames[i]
	return frames[frames.size() - 1]


func _looped_frame(spec: Dictionary, clock_in: float) -> int:
	if spec.has("frame_time"):
		return int((clock_in + CLOCK_SLACK) / spec.frame_time) % int(spec.hframes)
	var times: Array = spec.frame_times
	var loop := 0.0
	for time: float in times:
		loop += time
	var into := fposmod(clock_in + CLOCK_SLACK, loop)
	for i in times.size():
		if into < times[i]:
			return i
		into -= times[i]
	return times.size() - 1


func _texture(path: String) -> Texture2D:
	if not textures.has(path):
		textures[path] = load(path)
	return textures[path]


# The placeholder recolour JordanPuppet wears on a live sheet, for a clone whose twin isn't in.
func _tint() -> ShaderMaterial:
	if tint == null:
		tint = ShaderMaterial.new()
		tint.shader = load(PuppetLayout.TINT_SHADER)
		tint.set_shader_parameter("deep", PuppetLayout.TINT.deep)
		tint.set_shader_parameter("red", PuppetLayout.TINT.red)
		tint.set_shader_parameter("bone", PuppetLayout.TINT.bone)
		tint.set_shader_parameter("keyline", PuppetLayout.TINT.keyline)
	return tint


#MASON

func _run_mason(delta: float) -> void:
	match flight:
		Flight.ENTRY:
			var t := _share(circle_clock - flight_at, Layout.MASON_ENTRY_TIME)
			_place_mason(flight_from.lerp(_path_point(mason_start), _ease_out(t)),
				Layout.MASON_LIFT * t + Layout.MASON_ENTRY_ARC * 4.0 * t * (1.0 - t))
			if t >= 1.0:
				flight = Flight.FLY
		Flight.FLY:
			# He waits on his entry point, his first peak, and drops his first bomb there as the first clone fires.
			if beat == Beat.LOOP and first_fired:
				_fly(delta)
		Flight.RETURN:
			var t := _share(circle_clock - flight_at, Layout.MASON_RETURN_TIME)
			_place_mason(flight_from.lerp(Layout.MASON_LANDING, t),
				flight_lift * (1.0 - t) + Layout.MASON_RETURN_ARC * 4.0 * t * (1.0 - t))
			if t >= 1.0:
				_land_mason()
	_place_shadow()


# In from his rest, swung up onto the run line MASON_ENTRY_LEAD ahead of the first clone.
func _begin_entry() -> void:
	flight = Flight.ENTRY
	flight_at = circle_clock
	flight_from = mason.global_position
	mason_start = Layout.clone_round(k0) + Layout.MASON_ENTRY_LEAD
	mason_angle = mason_start
	mason_target = mason_start
	next_mark = 0
	mason.z_index = 1
	mason.play(&"squat")
	god.layer(&"strings").set_tension(mason, Layout.MASON_TENSION)
	_build_shadow()
	_play(&"squat")


# Toward his lead over the beam chasing the player, the short way, at up to MASON_SPEED; a bomb at each peak of his
# zigzag he crosses going forward while he is on his lead and far enough ahead of the player.
func _fly(delta: float) -> void:
	var theta := Layout.round_angle(_soles())
	var sweep := sweep_at(circle_clock)
	var lead := fposmod(theta - sweep, 180.0)
	var ahead := clampf(maxf(Layout.MASON_LEAD.x, lead + Layout.MASON_AHEAD), Layout.MASON_LEAD.x, Layout.MASON_LEAD.y)
	mason_target = mason_angle + wrapf(theta - lead + ahead - mason_angle, -180.0, 180.0)
	var off := mason_target - mason_angle
	var off_target := absf(off) > Layout.MASON_TOLERANCE
	if off_target and not catching_up:
		_catch_up()
	catching_up = off_target
	var most := Layout.MASON_SPEED * delta
	mason_angle += clampf(off, -most, most)
	_place_mason(_path_point(mason_angle), Layout.MASON_LIFT)
	_drop_at_marks(theta)


func _catch_up() -> void:
	if circle_clock - last_yank_at >= Layout.YANK_GAP:
		last_yank_at = circle_clock
		god.play(&"yank_right", &"control")
	_play(&"squat")


func _drop_at_marks(theta: float) -> void:
	var crossed := false
	while mason_angle >= mason_start + Layout.ZIG_STEP * next_mark - CLOCK_SLACK:
		next_mark += 1
		crossed = true
	if not crossed:
		return
	var on_lead := absf(mason_target - mason_angle) <= Layout.MASON_TOLERANCE
	if on_lead and wrapf(mason_angle - theta, -180.0, 180.0) >= Layout.DROP_AHEAD:
		_drop(theta)


func _drop(theta: float) -> void:
	var bomb: Node2D = POO_SCRIPT.new()
	bomb.name = "CirclePoo%d" % drops.size()
	bomb.z_index = 1
	add_hazard(bomb, mason.global_position, god.layer(&"stage"))
	bomb.drop(mason_lift, Layout.POO_FALL)
	turds.append(bomb)
	drops.append({at = circle_clock, angle = mason_angle, player = theta, point = bomb.global_position})


func _path_point(angle: float) -> Vector2:
	return Layout.round_point(angle, Layout.RUN_RADIUS + Layout.zig(angle - mason_start))


# His lift rides on his sprite alone, so his node, his hooks' base and his sort stay on the floor under him.
func _place_mason(at: Vector2, px: float) -> void:
	mason.global_position = at.round()
	mason_lift = px
	mason.sprite.position = mason.sprite_base_position + Vector2(0, -roundf(px))


# Down beside Carter at the end, over MASON_RETURN_ARC.
func _begin_return() -> void:
	flight = Flight.RETURN
	flight_at = circle_clock
	flight_from = mason.global_position
	flight_lift = mason_lift


func _land_mason() -> void:
	if flight == Flight.LANDED or not is_instance_valid(mason):
		return
	flight = Flight.LANDED
	_place_mason(Layout.MASON_LANDING, 0.0)
	mason.z_index = 0
	mason.play(&"broken")
	if is_instance_valid(shadow):
		var gone := shadow.create_tween()
		gone.tween_property(shadow, "modulate:a", 0.0, Layout.SHADOW.fade)
		gone.tween_callback(shadow.queue_free)
	shadow = null


func _build_shadow() -> void:
	var spec: Dictionary = Layout.SHADOW
	shadow = Sprite2D.new()
	shadow.name = "MasonShadow"
	shadow.texture = _texture(spec.texture)
	shadow.hframes = spec.hframes
	shadow.scale = Vector2.ONE * spec.scale
	shadow.modulate.a = spec.alpha
	add_hazard(shadow, mason.global_position, god.layer(&"floor"))
	_place_shadow()


func _place_shadow() -> void:
	if not is_instance_valid(shadow) or not is_instance_valid(mason):
		return
	shadow.global_position = mason.global_position
	shadow.frame = clampi(int(mason_lift / Layout.SHADOW.step), 0, shadow.hframes - 1)
	shadow.visible = mason_lift > 0.0


#THE BOMBS

func _step_turds(delta: float) -> void:
	for bomb in turds:
		if is_instance_valid(bomb) and not bomb.is_queued_for_deletion():
			bomb.step(delta)
	turds = turds.filter(func(bomb: Node2D) -> bool: return is_instance_valid(bomb) and not bomb.is_queued_for_deletion())


#THE CONTACT

# Whether the live band holds the player this step. Its hit is skipped while they flash: the band doesn't pass the
# i-frames, and reporting into them would only be noise. On a band's landing step, one that misses a dash's ghost pays
# its perfect dodge.
func _beam_contact() -> bool:
	var p := player()
	if p == null or p.playerHealth <= 0:
		return false
	var box := _rect_of(p.hurtBox.get_node("CollisionShape2D"))
	var held := false
	for shot in beams:
		if not shot.live:
			continue
		var clone: Clone = clones[shot.clone]
		var in_band := _in_band(clone, box)
		if shot.landing:
			shot.landing = false
			if not in_band:
				_near_miss(shot, clone)
		if not in_band or held:
			continue
		held = true
		if p.is_invincible:
			continue
		var contact := box.get_center()
		if p.receive_hit(HitInfo.make(Layout.BEAM_ID, shot.node, contact, carter)) == HitInfo.Result.HIT:
			_hit_fx(contact)
			beam_hits.append({at = circle_clock, fire = shot.fire})
			lap_hits[mini(shot.fire / Layout.CLONES, Layout.lap_count() - 1)] += 1
			hits += 1
	return held


# CarterBeamRush's: the band against a box, within half the hit width of the axis, the box's own reach across it
# included, and not wholly more than MESSATSU_BACK behind the palms.
func _in_band(clone: Clone, box: Rect2) -> bool:
	var dir := Vector2.from_angle(clone.angle)
	var n := dir.orthogonal()
	var c := box.get_center() - clone.palms
	var half := box.size / 2.0
	var across := CarterArtLayout.MESSATSU_HIT_WIDTH / 2.0 + half.x * absf(n.x) + half.y * absf(n.y)
	var reach := c.dot(dir) + half.x * absf(dir.x) + half.y * absf(dir.y)
	return absf(c.dot(n)) <= across and reach >= -CarterArtLayout.MESSATSU_BACK


func _near_miss(shot: Dictionary, clone: Clone) -> void:
	var p := player()
	if p.dodge_ghost_position() == Vector2.INF:
		return
	var ghost := _rect_of(p.dodge_ghost.get_node("CollisionShape2D"))
	if _in_band(clone, ghost):
		p.receive_near_miss(HitInfo.make(Layout.BEAM_ID, shot.node, ghost.get_center(), carter))


# The soles in a live bomb: half a heart and it is squashed. Dashed across or inside the i-frames, it stays.
func _poo_contact() -> void:
	var soles := _soles()
	for bomb in turds:
		if not bomb.live or ((soles - bomb.global_position) / Layout.POO_CONTACT).length_squared() > 1.0:
			continue
		var result: int = player().receive_hit(HitInfo.make(Layout.POO_ID, bomb, bomb.global_position, mason))
		poo_hits.append({at = circle_clock, bomb = bomb.name, result = result})
		if result == HitInfo.Result.HIT:
			bomb.pop()
			_play(&"pop")
			hits += 1
		return


# CarterAkumaScript.spawn_burst's hit, on the Fx layer: the clone's strike landing on the player.
func _hit_fx(at: Vector2) -> void:
	var spec := CarterArtLayout.clone_hit()
	if spec.has("texture"):
		var frame_size: Vector2 = spec.frame_size
		var pivot: Vector2 = spec.pivot
		var sheet := Sprite2D.new()
		sheet.name = "BeamHit"
		sheet.texture = _texture(spec.texture)
		sheet.hframes = spec.hframes
		sheet.scale = Vector2.ONE * spec.scale
		sheet.offset = frame_size / 2.0 - pivot
		if spec.get("additive", false):
			sheet.material = CarterArtLayout.additive()
		add_hazard(sheet, at, god.layer(&"fx"))
		var times: Array = spec.frame_times
		var play := sheet.create_tween()
		for i in range(1, spec.hframes):
			play.tween_interval(times[i - 1])
			play.tween_callback(sheet.set_frame.bind(i))
		play.tween_interval(times[times.size() - 1])
		play.tween_callback(sheet.queue_free)
	else:
		var burst := Polygon2D.new()
		burst.name = "BeamHit"
		burst.polygon = CarterArtLayout.ellipse(spec.radii, spec.points)
		burst.color = spec.color
		burst.scale = Vector2.ONE * spec.from_scale
		add_hazard(burst, at, god.layer(&"fx"))
		var play := burst.create_tween()
		play.tween_property(burst, "scale", Vector2.ONE * spec.to_scale, spec.time)
		play.parallel().tween_property(burst, "modulate:a", 0.0, spec.time)
		play.tween_callback(burst.queue_free)
	_play(&"strike")
	ScreenView.shake(get_tree(), CarterArtLayout.MESSATSU_HIT_SHAKE, CarterArtLayout.MESSATSU_HIT_SHAKE_STEPS,
		CarterArtLayout.MESSATSU_HIT_SHAKE_STEP_TIME)


#THE END

# The clones dissolve, the wall and the bombs go, and Mason is yanked back down beside Carter.
func _end() -> void:
	beat = Beat.END
	if is_instance_valid(hum):
		hum.stop()
	for clone in clones:
		for node in [clone.ball, clone.aim]:
			if is_instance_valid(node):
				node.queue_free()
		if is_instance_valid(clone.figure):
			var gone := clone.figure.create_tween()
			gone.tween_property(clone.figure, "modulate:a", 0.0, Layout.DISSOLVE_TIME)
			gone.tween_callback(clone.figure.queue_free)
	if is_instance_valid(wall):
		wall.queue_free()
	wall = null
	for bomb in turds:
		bomb.fade(Layout.POO_FADE)
	if hint_up:
		hint_up = false
		hide_hint()
	god.play(&"yank_right", &"control")
	_begin_return()


# Both left open: Carter spent, Mason slumped, their strings slack and the stars on them; the HUD back and the player
# drawn at their own z again, to walk up to either.
func _open() -> void:
	_land_mason()
	carter.play(&"recover")
	_play(&"spent")
	var strings: Node2D = god.layer(&"strings")
	for puppet: Node2D in [carter, mason]:
		strings.set_tension(puppet, GodLayout.TENSION_LIMP)
		puppet.set_punchable(true)
	_show_stars()
	hud(true)
	_lower_player()
	beat = Beat.WALK


# The first one in reach is the one they fight; the nearer hurtbox, in reach of both.
func _walk() -> void:
	var body := player()
	var best: Node2D = null
	var best_distance := INF
	for puppet: Node2D in [carter, mason]:
		if not _in_reach(puppet):
			continue
		var distance := body.global_position.distance_to(_hurt_centre(puppet))
		if distance < best_distance:
			best = puppet
			best_distance = distance
	if best == null:
		return
	target = best
	for puppet: Node2D in [carter, mason]:
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
	for puppet: Node2D in [carter, mason]:
		var star := Sprite2D.new()
		star.name = "DazeStars_%s" % puppet.boss
		star.texture = _texture(spec.texture)
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


#SOUND

# Every sound of the attack's own, under one holder in the hazard group, so release() takes them all.
func _build_sounds() -> void:
	sound_holder = Node2D.new()
	sound_holder.name = "CircleSounds"
	add_hazard(sound_holder, Vector2.ZERO, god.layer(&"fx"))
	for key: StringName in Layout.SOUNDS:
		var spec: Dictionary = Layout.SOUNDS[key]
		var voices: Array[AudioStreamPlayer] = []
		for i in spec.get("voices", 1):
			voices.append(_sound(load(spec.stream), spec.volume_db))
		sound_players[key] = voices
	var fires_voices: Array[AudioStreamPlayer] = []
	var fire_stream: AudioStream = load(CarterArtLayout.messatsu_sfx(&"fire"))
	for i in Layout.FIRE_VOICES:
		fires_voices.append(_sound(fire_stream, Layout.FIRE_DB))
	sound_players[&"fire"] = fires_voices
	hum = _sound(_looped(load(CarterArtLayout.messatsu_sfx(&"charge"))), Layout.HUM_DB)


func _sound(stream: AudioStream, volume_db: float) -> AudioStreamPlayer:
	var sound := AudioStreamPlayer.new()
	sound.stream = stream
	sound.volume_db = volume_db
	sound_holder.add_child(sound)
	return sound


func _looped(stream: AudioStream) -> AudioStream:
	var copy: AudioStream = stream.duplicate()
	if copy is AudioStreamWAV:
		copy.loop_mode = AudioStreamWAV.LOOP_FORWARD
		if copy.loop_end <= copy.loop_begin:
			copy.loop_end = int(copy.get_length() * copy.mix_rate)
	elif "loop" in copy:
		copy.loop = true
	return copy


# On the next of its voices, round and round.
func _play(key: StringName) -> void:
	var voices: Array = sound_players.get(key, [])
	if voices.is_empty():
		return
	var sound: AudioStreamPlayer = voices.pop_front()
	voices.append(sound)
	if is_instance_valid(sound):
		sound.play()


#THE PLAYER

func _raise_player() -> void:
	var body := player()
	if body == null:
		return
	if not player_raised:
		saved_z = body.z_index
		player_raised = true
	body.z_index = saved_z + 1


func _lower_player() -> void:
	var body := player()
	if player_raised and body != null:
		body.z_index = saved_z
	player_raised = false


func _soles() -> Vector2:
	return player().global_position + Vector2(0, Layout.SOLES_OVER_ORIGIN)


func _player_down() -> bool:
	var body := player()
	return body == null or body.playerHealth <= 0 or body.fight_over


func _rect_of(shape: CollisionShape2D) -> Rect2:
	var size: Vector2 = (shape.shape as RectangleShape2D).size * shape.global_scale.abs()
	return Rect2(shape.global_position - size / 2.0, size)


# How far through `time` `clock_in` is, 1 once it has run it.
static func _share(clock_in: float, time: float) -> float:
	if clock_in + CLOCK_SLACK >= time:
		return 1.0
	return clampf(clock_in / maxf(time, 0.0001), 0.0, 1.0)


static func _ease_out(x: float) -> float:
	var left := 1.0 - clampf(x, 0.0, 1.0)
	return 1.0 - left * left
