extends "res://Scripts/States/JordanGod/JordanCombo.gd"

# Jordan's attack 1, Greyson + Matt: the dark maze (the user's own design, 2026-09-28; every number is
# JordanMazeLayout's). Jordan warps the player to the start, raises Greyson and Matt, then the maze's walls; the walls
# show, the lights go out, and only Jordan, his puppets, the player and what they need are left to see. Matt yells an
# arrow over the player for each step of the path: the right direction hops them a block on and the block behind turns
# to glass; any other throws them back onto the glass behind for half a heart, then back onto their block for the
# same arrow again. Meanwhile Greyson poses to his meter, and full, his beam runs down the path for a heart and a half
# and the attack ends there. Reach him first and the lights come up for the three punches, the mash and his juggle:
# each bar banked is an uppercut on Jordan through the strings.
#
# THE ROUTE is new each time it starts, 18 steps from the start to the goal off the maze's own rng
# (JordanMazeLayout.generate(), which has its rules): the arrows, the walls, the glass, the knock and the beam all come
# off it. The rng is seeded once a fight, so a test that seeds it replays the same routes; pinned_route plays one route
# instead, the drawn path for one.
#
# THE BEATS: the warp, the summon, the walls and the lights going out are a coroutine (run) on the combo's own waits.
# The steps, the meter and the beam are beats on Physics_Update, so every timing in them is game time, one physics
# step at a time. Then the coroutine again for the payoff and the wrap. A run left behind by a cut never resumes into
# the next one (run_id).
#
# THE ANSWER is DirectionPress's - keys, the D-pad and the stick - and only the first press while an arrow is live
# counts. Presses before it shows and any during a hop or a knock do nothing. The player is under the sealed lock
# for all of it, so dash, block and punch do nothing either, until the payoff's punches.
#
# THE DARK: what must show is lifted over it (lift_above_dark): Jordan, the strings, both puppets, the player and the
# glass, the glass faintly. The arrow, the meter, the rings and the beam are on the Fx layer, over it already. As the
# lights come back up everything lifted goes back to its own z (_lower_lifts), so the payoff's effects on the player's
# layer draw over Jordan again.

const Layout := preload("res://Scripts/JordanMazeLayout.gd")
const MattArtLayout := preload("res://Scripts/MattArtLayout.gd")
const GreysonArtLayout := preload("res://Scripts/GreysonArtLayout.gd")
const PlayerScript := preload("res://Scripts/PlayerScript.gd")
const DirectionPress := preload("res://Scripts/DirectionPress.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const WALLS_SCRIPT := preload("res://Scripts/JordanMazeWalls.gd")
const BEAM_SCRIPT := preload("res://Scripts/JordanPathBeam.gd")
const BEAM_V2_SCRIPT := preload("res://Scripts/JordanPathBeamV2.gd")
const SCREEN_SCRIPT := preload("res://Scripts/JordanBeamScreen.gd")
const HitStop := preload("res://Scripts/HitStop.gd")
const GLASS_SCRIPT := preload("res://Scripts/MattGlassFloor.gd")
const METER_SCRIPT := preload("res://Scripts/GreysonHypeMeterUI.gd")
const RING_SCENE := preload("res://Scenes/Bosses/MattYellRingScene.tscn")

# A float clock summed a step at a time lands a hair either side of a beat's end.
const CLOCK_SLACK := 0.0001

# The steps, the meter and the beam are over: the goal reached, or the beam faded and the lights back up.
signal maze_over

enum Beat { OFF, TELL, LIVE, ANSWERED, HOP, KNOCK, GLASS, BACK, CHARGE, TRACE, HOLD, FADE, LIGHTS }

# A test's: while it holds a route, every maze plays that one.
static var pinned_route: Array[Vector2i] = []

var beat := Beat.OFF
var beat_clock := 0.0
var run_id := 0
var route: Array[Vector2i] = []
var step := 0
var press := DirectionPress.new()
var rng := RandomNumberGenerator.new()
var move_from := Vector2.ZERO
var move_to := Vector2.ZERO
var dark := false
var meter_on := false
var meter_clock := 0.0
var cells := 0
var beam_due := false
var reached := false
var beamed := false
var wrongs := 0
var bars := 0
var walls: Node2D
# Every block of glass laid, by cell.
var glass := {}
var beam: Node2D
var meter_holder: Node2D
var hum: AudioStreamPlayer
var glow: Polygon2D
var charge_sound: AudioStreamPlayer
# V2's beam (JordanMazeLayout.BEAM_V2): the screen's dark, flash and kick, the scorched path, the walls waiting to light
# as the head passes ([block, px along]), the charge's sound layers ([player, layer]), the rumble's next beat and the
# corners heard so far.
var screen: Node2D
var scorch: Node2D
var wall_flares: Array = []
var beam_voices: Array = []
var next_rumble := 0.0
var corners_heard := 0
# The fight's first maze shows the hint; `maze_clock` runs from its first arrow.
var hint_shown := false
var hint_up := false
var hint_at := 0.0
var maze_clock := 0.0
var right_answers := 0

# For the tests: each arrow as it went live (its step, physics frame and meter clock), the frames the first arrow went
# live on, the meter filled on, the beam began on and it landed on, and the beam's line.
var live_log: Array[Dictionary] = []
var first_arrow_frame := -1
var full_frame := -1
var beam_frame := -1
var beam_hit_frame := -1
var beam_route := PackedVector2Array()
# And the frames the trace began and the head reached the player's block, and where the head was as the hit landed.
var trace_frame := -1
var head_arrival_frame := -1
var head_at_hit := Vector2.INF


func _init() -> void:
	rng.randomize()


func pair() -> Array[Dictionary]:
	return [
		{boss = &"greyson", feet = Layout.GREYSON_FEET, face_left = false, hand = &"left", hooks = [&"back"], strings = 2},
		{boss = &"matt", feet = Layout.MATT_FEET, face_left = true, hand = &"right", hooks = [&"back"], strings = 2},
	]


func greyson() -> Node2D:
	return puppets.get(&"greyson")


func matt() -> Node2D:
	return puppets.get(&"matt")


func run() -> void:
	run_id += 1
	var this_run := run_id
	_reset()
	god.play(&"yank_right", &"control")
	warp_player(Layout.soles(Layout.START), PlayerScript.Facing.UP)
	_pose_player(&"rooted")
	await wait(Layout.TELEPORT_TIME)
	if _over(this_run):
		return
	await summon()
	if _over(this_run):
		return
	await _raise_walls(this_run)
	if _over(this_run):
		return
	_lights_out()
	await wait(Layout.DARK_FALL + Layout.DARK_STILL)
	if _over(this_run):
		return
	_begin_tell()
	await maze_over
	if _over(this_run):
		return
	if reached:
		await _meet_greyson()
		if _over(this_run):
			return
		bars = await punch_out(greyson())
		if _over(this_run):
			return
	await _wrap(this_run)


func _over(this_run: int) -> bool:
	return cut or this_run != run_id


func _reset() -> void:
	route = pinned_route.duplicate() if not pinned_route.is_empty() else Layout.generate(rng)
	beat = Beat.OFF
	beat_clock = 0.0
	step = 0
	press = DirectionPress.new()
	dark = false
	meter_on = false
	meter_clock = 0.0
	cells = 0
	beam_due = false
	reached = false
	beamed = false
	wrongs = 0
	bars = 0
	walls = null
	glass = {}
	beam = null
	meter_holder = null
	hum = null
	glow = null
	charge_sound = null
	hint_up = false
	maze_clock = 0.0
	right_answers = 0
	live_log.clear()
	first_arrow_frame = -1
	full_frame = -1
	beam_frame = -1
	beam_hit_frame = -1
	beam_route = PackedVector2Array()
	trace_frame = -1
	head_arrival_frame = -1
	head_at_hit = Vector2.INF
	screen = null
	scorch = null
	wall_flares = []
	beam_voices = []
	next_rumble = 0.0
	corners_heard = 0


func release() -> void:
	beat = Beat.OFF
	meter_on = false
	if is_instance_valid(hum):
		hum.stop()
	if is_instance_valid(charge_sound):
		charge_sound.stop()
	super.release()


#THE WALLS AND THE DARK

# A second dip and yank: the back glass is there from the start, and the walls rise rippling out from it on the yank,
# then stand lit.
func _raise_walls(this_run: int) -> void:
	god.play(&"summon", &"control")
	walls = WALLS_SCRIPT.new()
	walls.name = "MazeWalls"
	add_hazard(walls, Vector2.ZERO, god.layer(&"stage"))
	walls.build(Layout.walls_by_distance(route))
	_lay_glass(Layout.BACK_GLASS, true)
	await wait(GodLayout.summon_beats(god.final_puppeteer).rise)
	if _over(this_run):
		return
	god.play_sound(&"rift")
	walls.rise(Layout.WALL_STAGGER, Layout.WALL_RISE)
	await wait(walls.rise_duration(Layout.WALL_STAGGER, Layout.WALL_RISE) + Layout.WALL_SHOW)


func _lights_out() -> void:
	dark = true
	darken(true, Layout.DARK_FALL)
	walls.vanish(Layout.DARK_FALL)
	hud(false)
	lift_above_dark(god)
	lift_above_dark(god.layer(&"strings"))
	for puppet: Node2D in puppets.values():
		lift_above_dark(puppet)
	lift_above_dark(player())
	for floor: Node2D in glass.values():
		_dim(floor)
	_build_meter()


func _dim(floor: Node2D) -> void:
	lift_above_dark(floor)
	var fade := floor.create_tween()
	fade.tween_property(floor, "modulate:a", Layout.GLASS_DARK_ALPHA, Layout.DARK_FALL)


# The dark lifts, the HUD comes back, the glass shows whole and the meter goes.
func _lights_up() -> void:
	dark = false
	darken(false, Layout.LIGHTS_UP)
	hud(true)
	for floor: Node2D in glass.values():
		if is_instance_valid(floor):
			var fade := floor.create_tween()
			fade.tween_property(floor, "modulate:a", 1.0, Layout.LIGHTS_UP)
	_fade_meter()


# Once the lights are up: everything lifted over the dark back on its own z. lift_above_dark() has no way down but
# release(), and a Jordan left lifted would cover the finisher's stars and bursts, which draw at the player's own z.
func _lower_lifts() -> void:
	for i in range(lifted.size() - 1, -1, -1):
		var item: CanvasItem = lifted[i][0]
		if is_instance_valid(item):
			item.z_index = lifted[i][1]
	lifted.clear()


#THE STEPS

func Physics_Update(delta: float) -> void:
	super.Physics_Update(delta)
	if beat == Beat.OFF:
		return
	beat_clock += delta
	if first_arrow_frame >= 0:
		maze_clock += delta
	_answer(press.poll())
	_run_meter(delta)
	match beat:
		Beat.TELL:
			if _past(Layout.YELL_TELL):
				_go_live()
		Beat.ANSWERED:
			if _past(Layout.ANSWERED_TIME):
				_begin_hop()
		Beat.HOP:
			_drive_hop()
		Beat.KNOCK:
			if _drive_move(Layout.KNOCK_TIME):
				_hit_glass()
		Beat.GLASS:
			if _past(Layout.GLASS_HOLD):
				_begin_back()
		Beat.BACK:
			if _drive_move(Layout.BACK_TIME):
				_after_move()
		Beat.CHARGE:
			_charge()
		Beat.TRACE:
			_trace()
		Beat.HOLD:
			if Layout.BEAM_V2:
				_drive_move(Layout.BEAM_V2_KNOCKBACK.time)
			if _past(Layout.hold_time()):
				_begin_fade()
		Beat.FADE:
			if Layout.BEAM_V2:
				_dissipate_v2()
			else:
				_fade_beam()
		Beat.LIGHTS:
			if _past(Layout.LIGHTS_UP):
				_lower_lifts()
				_set_beat(Beat.OFF)
				maze_over.emit()
	_keep_hint()


func _input(event: InputEvent) -> void:
	super(event)
	_answer(press.read(event))


func _set_beat(next: Beat) -> void:
	beat = next
	beat_clock = 0.0


# Whether the beat has run `time`, on a clock summed a step at a time.
func _past(time: float) -> bool:
	return beat_clock + CLOCK_SLACK >= time


# How far through a beat `time` long, 1 once it has run it.
func _share(time: float) -> float:
	return 1.0 if _past(time) else clampf(beat_clock / time, 0.0, 1.0)


# Matt's yell coming: his tell, and the arrow put away while it comes.
func _begin_tell() -> void:
	_set_beat(Beat.TELL)
	hide_arrow()
	matt().play(&"yell_tell")


func _go_live() -> void:
	_set_beat(Beat.LIVE)
	arrow(Layout.arrow(route, step), &"live")
	matt().play(&"roar")
	matt().play_sfx(&"boom_fire")
	_blow_ring()
	if first_arrow_frame < 0:
		first_arrow_frame = Engine.get_physics_frames()
		_start_meter()
		if not hint_shown:
			hint_shown = true
			hint_up = true
			hint_at = maze_clock
			hint(Layout.HINT)
	live_log.append({step = step, frame = Engine.get_physics_frames(), meter = meter_clock})


func _answer(direction: StringName) -> void:
	if direction == &"" or beat != Beat.LIVE:
		return
	if direction == Layout.arrow(route, step):
		_right()
	else:
		_wrong()


func _right() -> void:
	right_answers += 1
	arrow(Layout.arrow(route, step), &"answered")
	matt().play_sfx(&"boom_answer")
	_add_player_hype(Layout.HYPE_EACH)
	# The last arrow answered is the goal reached: the meter stops on the press, not on the landing.
	if step + 1 == Layout.step_count():
		reached = true
		meter_on = false
	_set_beat(Beat.ANSWERED)


func _begin_hop() -> void:
	_set_beat(Beat.HOP)
	hide_arrow()
	matt().play(&"idle")
	move_from = Layout.body_point(route[step])
	move_to = Layout.body_point(route[step + 1])
	_lay_glass(route[step], false)


func _drive_hop() -> void:
	var t := _share(Layout.HOP_TIME)
	var arc := Vector2(0, -Layout.HOP_HEIGHT * 4.0 * t * (1.0 - t))
	_put_player((move_from.lerp(move_to, t) + arc).round())
	if t < 1.0:
		return
	step += 1
	_face_up()
	if reached:
		_set_beat(Beat.OFF)
		maze_over.emit()
		return
	_after_move()


# Back on a block: the beam if the meter filled while they were moving, the next yell if not.
func _after_move() -> void:
	if beam_due:
		_begin_beam()
	else:
		_begin_tell()


func _wrong() -> void:
	wrongs += 1
	arrow(Layout.arrow(route, step), &"cracked")
	matt().play(&"roar")
	matt().play_sfx(&"boom_wrong")
	_blow_ring()
	_set_beat(Beat.KNOCK)
	move_from = Layout.body_point(route[step])
	move_to = Layout.body_point(Layout.behind(route, step))
	_pose_player(&"knock")


# Over `time` from move_from to move_to, ease-out, in whole px; whether it has got there.
func _drive_move(time: float) -> bool:
	var t := _share(time)
	var eased := 1.0 - (1.0 - t) * (1.0 - t)
	_put_player(move_from.lerp(move_to, eased).round())
	return t >= 1.0


# Onto the glass behind: half a heart through the i-frames, and unless it killed them, the glass pose held.
func _hit_glass() -> void:
	var cell := Layout.behind(route, step)
	var feet := Layout.soles(cell)
	var floor: Node2D = glass.get(cell)
	if is_instance_valid(floor):
		floor.shatter_at(feet)
	matt().play_sfx(&"glass_shatter")
	ScreenView.shake(get_tree(), Layout.KNOCK_SHAKE, Layout.KNOCK_SHAKE_STEPS, Layout.KNOCK_SHAKE_STEP)
	var target := player()
	target.receive_hit(HitInfo.make(Layout.GLASS_ID, floor if is_instance_valid(floor) else self, feet, matt()))
	if target.playerHealth <= 0:
		# PlayerScript unlocks them at 0, and the fight's end releases the rest.
		_set_beat(Beat.OFF)
		return
	_pose_player(&"glass")
	_set_beat(Beat.GLASS)


func _begin_back() -> void:
	_set_beat(Beat.BACK)
	move_from = Layout.body_point(Layout.behind(route, step))
	move_to = Layout.body_point(route[step])
	_pose_player(&"rooted")
	matt().play(&"idle")


# One ring of sound off his roaring mouth that hurts nobody.
func _blow_ring() -> void:
	var ring: Node2D = RING_SCENE.instantiate()
	ring.player = null
	ring.start_radius = Layout.YELL_RING.start_radius
	ring.end_radius = Layout.YELL_RING.end_radius
	ring.band = Layout.YELL_RING.band
	ring.expand_time = Layout.YELL_RING.expand_time
	ring.landing_time = Layout.YELL_RING.landing_time
	add_hazard(ring, _texel_world(matt(), MattArtLayout.mouth(&"roar")), god.layer(&"fx"))


#THE GLASS

# A block of glass on `cell`: whole at once, or as the shards falling on it land.
func _lay_glass(cell: Vector2i, whole: bool) -> void:
	var floor: Node2D = GLASS_SCRIPT.new()
	floor.name = "Glass%d" % glass.size()
	add_hazard(floor, Vector2.ZERO, god.layer(&"floor"))
	floor.build(Layout.block_rect(cell), 1, god.layer(&"fx"), matt(), GodLayout.HAZARD_GROUP)
	glass[cell] = floor
	if dark:
		floor.modulate.a = Layout.GLASS_DARK_ALPHA
		lift_above_dark(floor)
	if whole:
		floor.reveal_all()
		return
	var inside := Layout.block_rect(cell).grow_individual(-Layout.SHARD_INSET.x, -Layout.SHARD_INSET.y,
		-Layout.SHARD_INSET.x, -Layout.SHARD_INSET.y)
	for k in Layout.SHARDS_PER_BLOCK:
		var land := Vector2(rng.randf_range(inside.position.x, inside.end.x), rng.randf_range(inside.position.y, inside.end.y))
		floor.drop_shard(land, Layout.SHARD_FALL, rng.randf_range(-Layout.SHARD_DRIFT, Layout.SHARD_DRIFT), rng.randi_range(0, 3))
	matt().play_sfx(&"glass_fall")


#GREYSON'S METER

func _build_meter() -> void:
	var puppet := greyson()
	puppet.hype = 0.0
	var scale := GodLayout.ui_scale()
	meter_holder = Node2D.new()
	meter_holder.name = "MazeMeter"
	meter_holder.scale = Vector2.ONE * scale
	add_hazard(meter_holder, Layout.meter_rect(scale).position, god.layer(&"fx"))
	var ui: Control = METER_SCRIPT.new()
	ui.body = puppet
	meter_holder.add_child(ui)
	hum = puppet.sfx_player_for(&"cannon_hum", meter_holder)


func _start_meter() -> void:
	meter_on = true
	meter_clock = 0.0
	_strike(0)
	if is_instance_valid(hum) and hum.stream != null:
		_tune_hum()
		hum.play()


func _run_meter(delta: float) -> void:
	if not meter_on:
		return
	meter_clock += delta
	var pose_time := Layout.METER_TIME / Layout.METER_CELLS
	while meter_on and meter_clock + CLOCK_SLACK >= pose_time * (cells + 1):
		_bank()
	_tune_hum()


# A pose played out: a cell banked, and the next pose struck, or the meter full.
func _bank() -> void:
	cells += 1
	var puppet := greyson()
	puppet.hype = float(cells)
	puppet.play_sfx(&"pose_bank")
	if cells < Layout.METER_CELLS:
		_strike(cells)
		return
	meter_on = false
	full_frame = Engine.get_physics_frames()
	if beat == Beat.TELL or beat == Beat.LIVE:
		_begin_beam()
	else:
		beam_due = true


func _strike(index: int) -> void:
	var puppet := greyson()
	puppet.play(Layout.POSES[index])
	puppet.play_sfx(&"flex", lerpf(Layout.FLEX_PITCH.x, Layout.FLEX_PITCH.y, float(cells) / Layout.METER_CELLS))


# GreysonScript's ramp: quieter and lower on an empty meter, the key's own level and higher on a full one.
func _tune_hum() -> void:
	if not is_instance_valid(hum):
		return
	var fill := clampf(meter_clock / Layout.METER_TIME, 0.0, 1.0)
	var base_db: float = hum.get_meta(&"base_db", hum.volume_db)
	var base_pitch: float = hum.get_meta(&"base_pitch", hum.pitch_scale)
	hum.volume_db = base_db - GreysonArtLayout.CANNON_HUM.quieter_empty * (1.0 - fill)
	hum.pitch_scale = base_pitch * lerpf(GreysonArtLayout.CANNON_HUM.pitch.x, GreysonArtLayout.CANNON_HUM.pitch.y, fill)


func _fade_meter() -> void:
	if not is_instance_valid(meter_holder):
		return
	var fade := meter_holder.create_tween()
	fade.tween_property(meter_holder, "modulate:a", 0.0, Layout.METER_FADE)
	if is_instance_valid(hum):
		fade.parallel().tween_property(hum, "volume_db", hum.volume_db - 30.0, Layout.METER_FADE)
		fade.tween_callback(hum.stop)


#THE BEAM
# V1 or V2 by JordanMazeLayout.BEAM_V2, through the same beats: the charge, the trace, the hold, then FADE, which V2
# plays as the beam breaking up. V2's beam node is up from the charge, for its charge and the overlay on him.

func _begin_beam() -> void:
	beam_due = false
	beamed = true
	meter_on = false
	beam_frame = Engine.get_physics_frames()
	_set_beat(Beat.CHARGE)
	hide_arrow()
	_hide_hint()
	matt().play(&"idle")
	var puppet := greyson()
	puppet.play(&"spirit")
	if Layout.BEAM_V2:
		_begin_charge_v2()
		return
	glow = _build_glow()
	add_hazard(glow, _muzzle(), god.layer(&"fx"))
	charge_sound = puppet.sfx_player_for(&"spirit_charge", glow)
	if charge_sound.stream != null:
		charge_sound.play()


func _charge() -> void:
	var share := _share(Layout.charge_time())
	if Layout.BEAM_V2:
		_charge_v2(share)
	else:
		_grow_glow(share)
	if _past(Layout.charge_time()):
		_begin_trace()


func _begin_trace() -> void:
	_set_beat(Beat.TRACE)
	trace_frame = Engine.get_physics_frames()
	var puppet := greyson()
	puppet.play(&"spirit_throw")
	if Layout.BEAM_V2:
		_fire_v2()
		return
	if is_instance_valid(charge_sound):
		charge_sound.stop()
	puppet.play_sfx(&"spirit_launch")
	_place_glow()
	beam = BEAM_SCRIPT.new()
	beam.name = "MazeBeam"
	add_hazard(beam, Vector2.ZERO, god.layer(&"fx"))
	beam_route = Layout.beam_points(route, _muzzle(), step)
	beam.setup(beam_route)


# The line runs out from his muzzle to the player's block, and lands as it reaches them.
func _trace() -> void:
	var share := _share(Layout.trace_time())
	if Layout.BEAM_V2:
		_flare_walls(beam.trace(share))
		if beam.corners_done > corners_heard:
			corners_heard = beam.corners_done
			_beam_sounds(&"corner")
	else:
		beam.trace(share)
	if beam.is_through() and head_arrival_frame < 0:
		head_arrival_frame = Engine.get_physics_frames()
	if not _past(Layout.trace_time()):
		return
	beam_hit_frame = Engine.get_physics_frames()
	head_at_hit = beam.head()
	if Layout.BEAM_V2:
		_impact_v2()
	else:
		ScreenView.shake(get_tree(), Layout.KNOCK_SHAKE * 2.0, Layout.KNOCK_SHAKE_STEPS * 2, Layout.KNOCK_SHAKE_STEP)
	var target := player()
	target.receive_hit(HitInfo.make(Layout.BEAM_ID, beam, beam_route[0], greyson()))
	if Layout.BEAM_V2:
		HitStop.freeze(get_tree(), Layout.BEAM_V2_HIT_STOP)
	if target.playerHealth <= 0:
		_set_beat(Beat.OFF)
		return
	if Layout.BEAM_V2:
		_thrown_back()
	_set_beat(Beat.HOLD)


func _begin_fade() -> void:
	_set_beat(Beat.FADE)
	if not Layout.BEAM_V2:
		return
	beam.set_crackling(false)
	_beam_sounds(&"dissipate")
	_pose_player(&"dizzy")
	move_from = player().global_position
	move_to = Layout.body_point(route[step])


func _fade_beam() -> void:
	var left := 1.0 - _share(Layout.fade_time())
	beam.modulate.a = left
	if is_instance_valid(glow):
		glow.modulate.a = minf(glow.modulate.a, left)
	if not _past(Layout.fade_time()):
		return
	beam.queue_free()
	beam = null
	if is_instance_valid(glow):
		glow.queue_free()
	glow = null
	greyson().play(&"idle")
	_set_beat(Beat.LIGHTS)
	_lights_up()


#THE BEAM, V2

# The screen's dark starts closing in, the charge lights on his muzzle and the overlay on him, and the charge's sound
# layers start ramping. His meter goes: it has said its piece, and his raised cannon charges under it.
func _begin_charge_v2() -> void:
	_fade_meter()
	beam = BEAM_V2_SCRIPT.new()
	beam.name = "MazeBeam"
	add_hazard(beam, Vector2.ZERO, god.layer(&"fx"))
	beam.begin_charge(greyson().sprite)
	screen = SCREEN_SCRIPT.new()
	screen.name = "MazeBeamScreen"
	add_hazard(screen, Vector2.ZERO, god.layer(&"fx"))
	beam_voices = _beam_sounds(&"charge")
	next_rumble = 0.0
	_charge_v2(0.0)


func _charge_v2(share: float) -> void:
	beam.charge(share, _muzzle())
	screen.close_in(player().global_position, _muzzle(), share)
	for pair in beam_voices:
		var layer: Dictionary = pair[1]
		if layer.has("to_pitch") and is_instance_valid(pair[0]):
			var voice: AudioStreamPlayer = pair[0]
			voice.pitch_scale = lerpf(layer.pitch, layer.to_pitch, share)
			voice.volume_db = lerpf(layer.volume_db, layer.to_db, share)
	var rumble := Layout.BEAM_V2_RUMBLE
	if beat_clock + CLOCK_SLACK >= next_rumble:
		next_rumble += rumble.step
		ScreenView.shake(get_tree(), lerpf(rumble.strength.x, rumble.strength.y, share), rumble.steps, rumble.step_time)


# The head snaps out of his muzzle: the charge's layers cut under the launch's, the jolt along it, Jordan yanking the
# string, the path to scorch, and the walls along it waiting to light, lifted over the dark and under the player.
func _fire_v2() -> void:
	_quiet(beam_voices, 0.12)
	beam_voices = []
	_beam_sounds(&"launch")
	god.play(&"yank_left", &"control")
	beam_route = Layout.beam_points(route, _muzzle(), step)
	ScreenView.shake(get_tree(), Layout.BEAM_V2_RUMBLE.launch, 4, 0.03, beam_route[1] - beam_route[0])
	scorch = Node2D.new()
	scorch.name = "MazeScorch"
	add_hazard(scorch, Vector2.ZERO, god.layer(&"floor"))
	lift_above_dark(scorch)
	beam.fire(beam_route, scorch)
	corners_heard = 0
	_plan_wall_flares()
	if is_instance_valid(walls):
		walls.z_index = GodLayout.LIFT_Z - 1


# The head arrives: the blast off the player, the screen flashing red then white and its colours kicked apart, the
# heavy shake through the hit-stop, the impact's sound, and the band crackling on.
func _impact_v2() -> void:
	beam.impact()
	screen.flash()
	screen.kick()
	var shake := Layout.BEAM_V2_SHAKE
	ScreenView.shake(get_tree(), shake.strength, shake.steps, shake.step_time, Vector2.ZERO, true)
	_beam_sounds(&"impact")
	_beam_sounds(&"crackle")
	_flare_walls(INF)
	beam.set_crackling(true)


# Thrown back along the beam: pushed KNOCKBACK px through the hold's start, then back onto the block as it breaks up.
func _thrown_back() -> void:
	_pose_player(&"knock")
	move_from = Layout.body_point(route[step])
	var way := (beam_route[beam_route.size() - 1] - beam_route[beam_route.size() - 2]).normalized()
	move_to = (move_from + way * Layout.BEAM_V2_KNOCKBACK.px).round()


# It breaks into embers and smoke, the scorch cools, the dark opens again and the player is set back on the block;
# then the lights, the scorch fading with the dark.
func _dissipate_v2() -> void:
	var share := _share(Layout.fade_time())
	beam.dissipate(share)
	beam.cool(share)
	screen.open_up(player().global_position, _muzzle(), share)
	_drive_move(Layout.fade_time())
	if not _past(Layout.fade_time()):
		return
	greyson().play(&"idle")
	_pose_player(&"rooted")
	_face_up()
	if is_instance_valid(walls):
		walls.z_index = 0
	_set_beat(Beat.LIGHTS)
	_lights_up()
	if is_instance_valid(scorch):
		var fade := scorch.create_tween()
		fade.tween_property(scorch, "modulate:a", 0.0, Layout.LIGHTS_UP)


# Each wall along the beam's path and when it lights: LEAD px before the head reaches the nearest block of the path it
# stands beside. The path runs from the goal back down to the player's block; the air before the goal lights none.
func _plan_wall_flares() -> void:
	wall_flares.clear()
	if not is_instance_valid(walls):
		return
	var reach := {}
	var along := beam_route[0].distance_to(beam_route[1])
	var last := route.size() - 1
	reach[last] = along
	for i in range(last - 1, step - 1, -1):
		along += Layout.soles(route[i + 1]).distance_to(Layout.soles(route[i]))
		reach[i] = along
	var lead: float = Layout.BEAM_V2_WALLS.lead
	for k in walls.cells.size():
		var cell: Vector2i = walls.cells[k]
		var first := INF
		for i in reach:
			var gap: Vector2i = (cell - route[i]).abs()
			if gap.x <= 1 and gap.y <= 1:
				first = minf(first, reach[i])
		if first < INF:
			wall_flares.append([k, first - lead])
	wall_flares.sort_custom(func(a: Array, b: Array) -> bool: return a[1] < b[1])


func _flare_walls(reach: float) -> void:
	var spec := Layout.BEAM_V2_WALLS
	while not wall_flares.is_empty() and wall_flares[0][1] <= reach:
		walls.flare(wall_flares[0][0], spec.color, spec.hold, spec.fade)
		wall_flares.pop_front()


# One of BEAM_V2_SOUNDS' sets: each layer whose file is in on a player of its own under the screen node, which the
# release takes. [player, layer] for each.
func _beam_sounds(key: StringName) -> Array:
	var out := []
	for layer: Dictionary in Layout.BEAM_V2_SOUNDS.get(key, []):
		if not ResourceLoader.exists(layer.stream):
			continue
		var voice := AudioStreamPlayer.new()
		voice.stream = load(layer.stream)
		voice.pitch_scale = layer.pitch
		voice.volume_db = layer.volume_db
		screen.add_child(voice)
		voice.play()
		out.append([voice, layer])
	return out


# Layers cut short, over `time` s.
func _quiet(voices: Array, time: float) -> void:
	for pair in voices:
		if not is_instance_valid(pair[0]):
			continue
		var voice: AudioStreamPlayer = pair[0]
		var out := voice.create_tween()
		out.tween_property(voice, "volume_db", voice.volume_db - 30.0, time)
		out.tween_callback(voice.stop)


# The cannon's glow, GreysonArtLayout's code stand-in: stepped up its alphas and grown through the charge, on his muzzle.
func _build_glow() -> Polygon2D:
	var spec := GreysonArtLayout.fx(&"cannon_glow")
	var shape := Polygon2D.new()
	shape.name = "CannonGlow"
	var polygon := PackedVector2Array()
	for i in spec.points:
		polygon.append(Vector2.from_angle(TAU * i / spec.points) * spec.radius)
	shape.polygon = polygon
	shape.color = spec.color
	var additive := CanvasItemMaterial.new()
	additive.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	shape.material = additive
	shape.modulate.a = 0.0
	return shape


func _grow_glow(share: float) -> void:
	if not is_instance_valid(glow):
		return
	var alphas: Array = GreysonArtLayout.fx(&"cannon_glow").alphas
	glow.modulate.a = alphas[clampi(ceili(share * (alphas.size() - 1)), 0, alphas.size() - 1)]
	glow.scale = Vector2.ONE * lerpf(1.0, Layout.GLOW_GROWTH, share)
	_place_glow()


func _place_glow() -> void:
	if is_instance_valid(glow):
		glow.global_position = _muzzle().round()


#THE GOAL AND THE WRAP

# The lights come up on him, knocked out of his pose, and the punches are the player's.
func _meet_greyson() -> void:
	_hide_hint()
	_lights_up()
	matt().play(&"idle")
	greyson().play(&"pose_hit")
	if wrongs == 0:
		_add_player_hype(Layout.HYPE_CLEAN)
	await wait(Layout.LIGHTS_UP)
	_lower_lifts()


func _wrap(this_run: int) -> void:
	for floor: Node2D in glass.values():
		if is_instance_valid(floor):
			floor.clear(Layout.GLASS_CLEAR_TIME)
	_fade_meter()
	await recall()
	if _over(this_run):
		return
	if bars > 0:
		god.play(&"hit", &"hover")
	finish()


#THE HINT

func _keep_hint() -> void:
	if hint_up and right_answers >= Layout.HINT_STEPS and maze_clock - hint_at >= Layout.HINT_MIN_TIME:
		_hide_hint()


func _hide_hint() -> void:
	if not hint_up:
		return
	hint_up = false
	hide_hint()


#THE PLAYER

func _put_player(point: Vector2) -> void:
	var target := player()
	if target != null:
		target.global_position = point


# The maze is all back view: they face up it wherever the steps take them.
func _face_up() -> void:
	var target := player()
	target.face_point(target.global_position + Vector2.UP * 100.0)


# One of the Glass Row's poses (MattArtLayout.PLAYER_POSES) off its sheet.
func _pose_player(pose: StringName) -> void:
	var target := player()
	if target == null or not target.hold_pose(MattArtLayout.player_poses()):
		return
	var spec := MattArtLayout.player_pose(pose)
	target.play_pose(spec.frames, spec.times, spec.loop)


func _add_player_hype(amount: float) -> void:
	var hype_node: Node = player().get_node_or_null("Hype")
	if hype_node != null and hype_node.has_method("add"):
		hype_node.add(amount)


#WHERE THINGS ARE ON THE PUPPETS

# A texel of the frame `puppet` shows now, in world px, mirrored with its sprite, the way his own art layout places it:
# every sheet is centred on the sprite, so its rect is the frame's.
func _texel_world(puppet: Node2D, texel: Vector2) -> Vector2:
	var sprite: Sprite2D = puppet.sprite
	var rect := sprite.get_rect()
	if sprite.flip_h:
		texel.x = rect.size.x - 1.0 - texel.x
	return sprite.to_global(rect.position + texel)


func _muzzle() -> Vector2:
	var puppet := greyson()
	return _texel_world(puppet, GreysonArtLayout.muzzle(puppet.current_anim, puppet.sprite.frame))
