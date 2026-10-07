extends "res://Scripts/States/JordanGod/JordanCombo.gd"

# Jordan's attack 2, Captain Burak + Danny's kegs: the user's own design (2026-09-28; every number is JordanKegsLayout's).
# Burak lays four kegs round the player, who stands in the centre. One glows at a time, never the same one twice running,
# and blows GLOW_TIME later for half a heart unless the player dashes to it and punches it out. There is no walking: a
# dash snaps the player to a keg's station or back to the centre, and costs nothing. Danny butt-slams the centre while
# they wait in it. Eight defuses in all, blasts or not; the eighth flies into Burak and dazes him, walking comes back,
# and the punches, the mash and his juggle hurt Jordan through the strings.
#
# THE BEATS: the warp and the summon are a coroutine (run) on the combo's own waits; the lay, the loop and the eighth
# are beats on Physics_Update, so every timing in them is game time, a physics step at a time; then the coroutine again
# for the payoff and the wrap. A run left behind by a cut never resumes into the next one (generation).
#
# THE PLAYER is held in the sealed lock until the eighth, so their own dash and punch never fire and the kegs' hurtboxes
# never hear a punch: this state reads the presses itself. A direction press alone is the move (the user's rule: the
# arrows dash here, the dash button does nothing), drawn as the dash is. It is DirectionPress's - keys and the D-pad off
# the event, the stick flicked - so a held direction moves once. Two directions pressed in one step are a diagonal and
# do nothing; presses inside a move or a punch count for nothing. The player draws over the kegs, so the south one
# never hides them.

const Layout := preload("res://Scripts/JordanKegsLayout.gd")
const BurakArt := preload("res://Scripts/BurakBossArtLayout.gd")
const DannyArt := preload("res://Scripts/DannyBossArtLayout.gd")
const FinisherArtLayout := preload("res://Scripts/FinisherArtLayout.gd")
const PlayerScript := preload("res://Scripts/PlayerScript.gd")
const DirectionPress := preload("res://Scripts/DirectionPress.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const KEG_SCENE := preload("res://Scenes/Bosses/BurakBossBarrelScene.tscn")
const BLAST_SCRIPT := preload("res://Scripts/BurakBossBlastScript.gd")
const PIPS_SCRIPT := preload("res://Scripts/BurakBossPips.gd")
const SlamMark := preload("res://Scripts/DannyBossSlamMark.gd")
const SlamHit := preload("res://Scripts/DannyBossSlamHit.gd")

const BURAK := &"burak"
const DANNY := &"danny"
const CENTRE := &"centre"
# A float clock summed a step at a time lands a hair short of a beat's end.
const STEP_TOLERANCE := 0.0001

# The eighth keg is on Burak, then the player is in reach of him.
signal stage_ended

enum Beat { OFF, LAY, LOOP, LAUNCH, WALK, PAYOFF }
enum Slam { REST, YANK, LEAP, SHADOW, DROP, SIT, HOP, LIMP }

var rng := RandomNumberGenerator.new()
# The hint is the fight's first run's alone.
var hint_given := false
var generation := 0
var beat := Beat.OFF
# The player is down: nothing more happens, and the fight's end releases this.
var stopped := false
# From the lay's start, in game seconds: every beat of the loop is timed on it.
var kegs_clock := 0.0
var loop_at := 0.0
var burak: Node2D
var danny: Node2D
var counter: Node2D
# The kegs standing on their spots, by name. One being thrown is in `throws`, then `flights`, until it lands.
var kegs := {}
var throws: Array = []
var flights: Array = []
var debris := {}
var glowing := &""
var glow_started := 0.0
# The punch on the glowing keg is in: it can no longer blow.
var claimed := false
var last_glow := &""
var defused := 0
var hits := 0
var quiet_since := 0.0
var quiet_gap := 0.0
var arrow_off_at := -1.0
# &"centre", a keg's name at its station, or &"" in a dash.
var where := CENTRE
var centre_since := -1.0
var press := DirectionPress.new()
# The directions pressed since the last physics step.
var pressed_ways: Array[StringName] = []
var dash_goal := &""
var dash_from := Vector2.ZERO
var dash_to := Vector2.ZERO
var dash_clock := -1.0
var punch_keg := &""
var punch_clock := -1.0
var punch_landed := false
var saved_z := 0
var player_raised := false
var slam := Slam.REST
var slam_clock := 0.0
var limp_owed := false
var lift := 0.0
var mark: Node2D
var hop_from := Vector2.ZERO
var hop_lift := 0.0
var launched: Node2D
var launch_from := Vector2.ZERO
var launch_at := 0.0
var stars: Sprite2D
var stars_clock := 0.0
var bars := -1
# For tests, on kegs_clock: every glow, blast, defuse and slam as it came.
var glows: Array = []
var blasts: Array = []
var defuses: Array = []
var slams: Array = []


func pair() -> Array[Dictionary]:
	return [
		{boss = BURAK, feet = Layout.BURAK_FEET, face_left = false, hand = &"left", hooks = [&"back"], strings = 2},
		{boss = DANNY, feet = Layout.DANNY_REST, face_left = true, hand = &"right", hooks = [&"back"], strings = 2},
	]


func run() -> void:
	generation += 1
	var run_of := generation
	_start()
	god.play(&"yank_right", &"control")
	warp_player(Layout.CENTRE, PlayerScript.Facing.UP)
	_raise_player()
	hud(false)
	await wait(Layout.TELEPORT_TIME)
	if _gone(run_of):
		return
	await summon()
	if _gone(run_of):
		return
	burak = puppets.get(BURAK)
	danny = puppets.get(DANNY)
	_build_counter()
	_begin_lay()
	await stage_ended
	if _gone(run_of):
		return
	await stage_ended
	if _gone(run_of):
		return
	bars = await punch_out(burak)
	if _gone(run_of):
		return
	await recall()
	if _gone(run_of):
		return
	if bars > 0:
		god.play(&"hit", &"hover")
	finish()


func release() -> void:
	generation += 1
	beat = Beat.OFF
	_free_mark()
	if is_instance_valid(stars):
		stars.queue_free()
	stars = null
	if is_instance_valid(burak):
		burak.stop_sfx(&"fuse_hiss")
	_lower_player()
	super.release()
	stage_ended.emit()


func _input(event: InputEvent) -> void:
	super(event)
	if beat != Beat.LOOP or stopped or cut:
		return
	var way := press.read(event)
	if way != &"":
		if not pressed_ways.has(way):
			pressed_ways.append(way)
	elif event.is_action_pressed(&"punch"):
		_punch()


func Physics_Update(delta: float) -> void:
	super.Physics_Update(delta)
	if beat == Beat.OFF or cut or stopped:
		return
	if _player_down():
		stopped = true
		return
	kegs_clock += delta
	_run_throws()
	match beat:
		Beat.LAY:
			if _due(loop_at):
				_begin_loop()
		Beat.LOOP:
			_run_player(delta)
			if beat == Beat.LOOP:
				_run_glow()
		Beat.LAUNCH:
			_run_launch()
		Beat.WALK:
			if _in_reach():
				beat = Beat.PAYOFF
				stage_ended.emit()
		Beat.PAYOFF:
			# The finisher's own stars take over as it dazes him.
			if is_instance_valid(stars) and player().finisher.is_active():
				stars.queue_free()
				stars = null
	_run_danny(delta)
	if arrow_off_at >= 0.0 and _due(arrow_off_at):
		arrow_off_at = -1.0
		hide_arrow()
	_spin_stars(delta)


func _start() -> void:
	beat = Beat.OFF
	stopped = false
	kegs_clock = 0.0
	burak = null
	danny = null
	counter = null
	kegs.clear()
	throws.clear()
	flights.clear()
	debris.clear()
	glowing = &""
	claimed = false
	last_glow = &""
	defused = 0
	hits = 0
	quiet_since = 0.0
	quiet_gap = 0.0
	arrow_off_at = -1.0
	where = CENTRE
	centre_since = -1.0
	press = DirectionPress.new()
	pressed_ways.clear()
	dash_clock = -1.0
	punch_clock = -1.0
	slam = Slam.REST
	slam_clock = 0.0
	limp_owed = false
	lift = 0.0
	mark = null
	launched = null
	stars = null
	bars = -1
	glows.clear()
	blasts.clear()
	defuses.clear()
	slams.clear()


func _gone(run_of: int) -> bool:
	return cut or run_of != generation


func _due(at: float) -> bool:
	return kegs_clock >= at - STEP_TOLERANCE


#THE LAY, AND EVERY THROW

func _begin_lay() -> void:
	beat = Beat.LAY
	kegs_clock = 0.0
	for i in Layout.KEGS.size():
		throws.append({keg = Layout.KEGS[i], at = i * Layout.LAY_CADENCE})
	loop_at = (Layout.KEGS.size() - 1) * Layout.LAY_CADENCE + Layout.CARRY_TIME + Layout.LAY_SETTLE


func _begin_loop() -> void:
	beat = Beat.LOOP
	quiet_since = kegs_clock
	quiet_gap = 0.0
	if where == CENTRE:
		centre_since = kegs_clock


func _run_throws() -> void:
	while not throws.is_empty() and _due(throws[0].at):
		_throw(throws.pop_front().keg)
	for i in range(flights.size() - 1, -1, -1):
		var flight: Dictionary = flights[i]
		var weight := clampf((kegs_clock - flight.at) / Layout.CARRY_TIME, 0.0, 1.0)
		if _due(flight.at + Layout.CARRY_TIME):
			weight = 1.0
		flight.node.carry(flight.from, weight, Layout.ARC_HEIGHT)
		if weight >= 1.0:
			flight.node.land()
			kegs[flight.keg] = flight.node
			flights.remove_at(i)


func _throw(keg_name: StringName) -> void:
	var keg: Node2D = KEG_SCENE.instantiate()
	keg.boss = burak
	keg.floor_layer = god.layer(&"floor")
	add_hazard(keg, Layout.KEG_POINTS[keg_name], god.layer(&"stage"))
	keg.show_marker()
	_face(burak, keg.global_position)
	burak.play(&"throw", &"idle")
	burak.play_sfx(&"throw")
	var from := _texel_world(burak, BurakArt.release(&"throw"))
	keg.carry(from, 0.0, Layout.ARC_HEIGHT)
	flights.append({keg = keg_name, node = keg, from = from, at = kegs_clock})


#THE PLAYER

func _busy() -> bool:
	return not pressed_ways.is_empty() or dash_clock >= 0.0 or punch_clock >= 0.0


func _run_player(delta: float) -> void:
	var flick := press.poll()
	if flick != &"" and not pressed_ways.has(flick):
		pressed_ways.append(flick)
	if pressed_ways.size() == 1:
		_dash(pressed_ways[0])
	pressed_ways.clear()
	if dash_clock >= 0.0:
		_step_dash(delta)
	if punch_clock >= 0.0:
		_step_punch(delta)


# From the centre, to the keg that way if it is standing; from a keg, only back to the centre. Anything else does
# nothing.
func _dash(way: StringName) -> void:
	if dash_clock >= 0.0 or punch_clock >= 0.0:
		return
	var goal := &""
	if where == CENTRE:
		goal = Layout.keg_toward(way)
		if not kegs.has(goal):
			return
	elif where != &"" and way == Layout.back_way(where):
		goal = CENTRE
	else:
		return
	var body := player()
	dash_goal = goal
	dash_from = body.global_position
	dash_to = Layout.body_point(Layout.CENTRE if goal == CENTRE else Layout.STATIONS[goal])
	dash_clock = 0.0
	where = &""
	centre_since = -1.0
	body.direction = Layout.WAY_VECTORS[way]
	# Far along the way back, so the facing never flips as the dash passes the point it looks at.
	var look: Vector2 = dash_to + Layout.WAY_VECTORS[way] * 4000.0 if goal == CENTRE else _keg_centre(kegs[goal])
	body.face_point(look)


# Written straight onto the locked player; dash_stepped draws the approved trail and plays the whoosh.
func _step_dash(delta: float) -> void:
	var body := player()
	var kick_off := dash_clock == 0.0
	dash_clock += delta
	var t := clampf(dash_clock / Layout.DASH_TIME, 0.0, 1.0)
	if dash_clock >= Layout.DASH_TIME - STEP_TOLERANCE:
		t = 1.0
	var from := body.global_position
	body.global_position = dash_from.lerp(dash_to, t).round()
	body.dash_stepped.emit(from, body.global_position, kick_off)
	if t >= 1.0:
		dash_clock = -1.0
		where = dash_goal
		if where == CENTRE:
			centre_since = kegs_clock


# A press on the glowing keg claims it at once, so it can't go up before the fist lands.
func _punch() -> void:
	if _busy() or where == CENTRE or where == &"":
		return
	punch_keg = where
	punch_clock = 0.0
	punch_landed = false
	if glowing == where:
		claimed = true
	player().play_pose(_swing_frames(player()).frames, Layout.PUNCH_TIMES, false)


func _step_punch(delta: float) -> void:
	punch_clock += delta
	if not punch_landed and punch_clock >= Layout.punch_contact() - STEP_TOLERANCE:
		punch_landed = true
		_punch_lands()
	if punch_clock >= Layout.punch_time() - STEP_TOLERANCE:
		punch_clock = -1.0
		_stand()


# On the glowing keg it goes out; on a quiet one it only tonks; on a spot being laid again it swings at nothing.
func _punch_lands() -> void:
	var keg: Node2D = kegs.get(punch_keg)
	if keg == null:
		return
	if glowing == punch_keg:
		_defuse(keg)
	else:
		burak.play_sfx(&"barrel_tonk")


#THE GLOWS

func _run_glow() -> void:
	if glowing != &"":
		if not claimed and _due(glow_started + Layout.GLOW_TIME):
			_blow()
		return
	if not _due(quiet_since + quiet_gap):
		return
	var due := quiet_since + Layout.STALL_TIME
	if where == CENTRE:
		due = minf(due, maxf(centre_since, quiet_since) + Layout.GLOW_DELAY)
	if _due(due):
		_glow()


# A standing keg, never the one that glowed last.
func pick_glow() -> StringName:
	var choices: Array[StringName] = []
	for keg_name in Layout.KEGS:
		if keg_name != last_glow and kegs.has(keg_name):
			choices.append(keg_name)
	return choices[rng.randi_range(0, choices.size() - 1)]


func _glow() -> void:
	var keg_name := pick_glow()
	var keg: Node2D = kegs[keg_name]
	glowing = keg_name
	glow_started = kegs_clock
	claimed = false
	last_glow = keg_name
	keg.light_fuse()
	keg.arm()
	burak.play_sfx(&"fuse_hiss")
	arrow(Layout.WAYS[keg_name])
	arrow_off_at = -1.0
	_face(burak, keg.global_position)
	burak.play(&"fire_aim")
	glows.append({keg = keg_name, at = kegs_clock})
	if not hint_given:
		hint_given = true
		hint(Layout.HINT % InputSettings.label_for(&"move"))


func _defuse(keg: Node2D) -> void:
	var keg_name := glowing
	keg.defuse(player().global_position)
	burak.stop_sfx(&"fuse_hiss")
	glowing = &""
	claimed = false
	defused += 1
	quiet_since = kegs_clock
	quiet_gap = 0.0
	defuses.append({keg = keg_name, at = kegs_clock})
	counter.load_pip(defused - 1)
	player().hype.add(Layout.HYPE_EACH)
	arrow(Layout.WAYS[keg_name], &"answered")
	arrow_off_at = kegs_clock + Layout.ARROW_HOLD
	hide_hint()
	burak.play(&"idle")
	if defused >= Layout.DEFUSES:
		_launch(keg_name)


# He shoots it as it goes (looks only): the blast is the keg's own, over the whole arena, and he lays another there.
func _blow() -> void:
	var keg_name := glowing
	var keg: Node2D = kegs[keg_name]
	kegs.erase(keg_name)
	glowing = &""
	quiet_since = kegs_clock
	quiet_gap = Layout.BLAST_GAP
	burak.stop_sfx(&"fuse_hiss")
	var target := _keg_centre(keg)
	_face(burak, target)
	burak.play(&"fire", &"idle")
	burak.play_sfx(&"gunshot")
	var muzzle := _texel_world(burak, BurakArt.muzzle(&"fire"))
	_muzzle(muzzle, target - muzzle)
	var blast: Node2D = BLAST_SCRIPT.new()
	add_hazard(blast, keg.global_position, god.layer(&"fx"))
	var result: int = blast.go_off(keg, player(), burak, true, false)
	_cover_view(blast.screen)
	blasts.append({keg = keg_name, at = kegs_clock, result = result})
	if result == HitInfo.Result.HIT:
		hits += 1
	_lay_debris(keg_name)
	arrow(Layout.WAYS[keg_name], &"cracked")
	arrow_off_at = kegs_clock + Layout.ARROW_HOLD
	throws.append({keg = keg_name, at = kegs_clock + Layout.RELAY_AFTER})


# The blast's whole-arena flash is drawn over the arena's own 1920x1080 from the world's origin, and this fight's view
# is wider (ScreenView's base), so it is stretched over all of it.
func _cover_view(flash: Sprite2D) -> void:
	var view := ScreenView.base_rect()
	flash.global_position = view.position
	flash.scale = Vector2.ONE * BurakArt.SCALE * view.size.x / ScreenView.VIEW_SIZE.x


#DANNY

func _run_danny(delta: float) -> void:
	if not is_instance_valid(danny):
		return
	slam_clock += delta
	match slam:
		Slam.REST:
			if limp_owed:
				_go_limp()
			elif beat == Beat.LOOP and where == CENTRE and _due(centre_since + Layout.DANNY_WAIT):
				_yank()
		Slam.YANK:
			# On the yank's pull frame, or at once if something cut the yank short.
			if god.current_anim != &"yank_right" or god.anim_step >= 1:
				_leap()
		Slam.LEAP:
			var t := clampf(slam_clock / Layout.LEAP_TIME, 0.0, 1.0)
			_place_danny(Layout.DANNY_REST.lerp(Layout.CENTRE, t), Layout.HOVER_HEIGHT * _ease_out(t))
			if slam_clock >= Layout.LEAP_TIME - STEP_TOLERANCE:
				_hang()
		Slam.SHADOW:
			if slam_clock >= Layout.SHADOW_TIME - STEP_TOLERANCE:
				_drop()
		Slam.DROP:
			var t := clampf(slam_clock / Layout.DROP_TIME, 0.0, 1.0)
			_place_danny(Layout.CENTRE, Layout.HOVER_HEIGHT * (1.0 - t))
			mark.set_height(lift)
			if slam_clock >= Layout.DROP_TIME - STEP_TOLERANCE:
				_land_slam()
		Slam.SIT:
			if slam_clock >= Layout.SIT_TIME - STEP_TOLERANCE:
				_hop()
		Slam.HOP:
			var t := clampf(slam_clock / Layout.HOP_TIME, 0.0, 1.0)
			_place_danny(hop_from.lerp(Layout.DANNY_REST, t), hop_lift * (1.0 - t) + Layout.HOP_HEIGHT * 4.0 * t * (1.0 - t))
			if slam_clock >= Layout.HOP_TIME - STEP_TOLERANCE:
				_rest()


func _begin_slam(next: Slam) -> void:
	slam = next
	slam_clock = 0.0


func _yank() -> void:
	_begin_slam(Slam.YANK)
	god.play(&"yank_right", &"control")
	god.play_sound(&"yank")
	god.layer(&"strings").set_tension(danny, GodLayout.TENSION_YANK, 0.0)
	slams.append({yank_at = kegs_clock})


func _leap() -> void:
	_begin_slam(Slam.LEAP)
	_face(danny, Layout.CENTRE)
	danny.play(&"jump_launch", &"air")
	danny.play_sfx(&"jump")
	slams[-1].leap_at = kegs_clock


func _hang() -> void:
	_begin_slam(Slam.SHADOW)
	_place_danny(Layout.CENTRE, Layout.HOVER_HEIGHT)
	mark = SlamMark.new()
	mark.name = "SlamMark"
	mark.full_height = Layout.HOVER_HEIGHT
	add_hazard(mark, Layout.CENTRE, god.layer(&"floor"))
	mark.hover()
	slams[-1].shadow_at = kegs_clock


func _drop() -> void:
	_begin_slam(Slam.DROP)
	danny.play(&"slam_drop")
	slams[-1].drop_at = kegs_clock


# DannyBossSlamHit delivers it, the player's i-frames and all, but only to soles inside his seat.
func _land_slam() -> void:
	_begin_slam(Slam.SIT)
	_place_danny(Layout.CENTRE, 0.0)
	danny.play(&"slam_impact")
	mark.set_height(0.0)
	var entry: Dictionary = slams[-1]
	entry.impact_at = kegs_clock
	entry.inside = Layout.in_slam_zone(_soles())
	entry.result = HitInfo.Result.IGNORED
	if entry.inside:
		var hit: Node2D = SlamHit.new()
		hit.player = player()
		hit.boss = danny
		hit.attack_id = Layout.SLAM_ID
		add_hazard(hit, Layout.CENTRE, god.layer(&"floor"))
		entry.result = hit.result
		if hit.result == HitInfo.Result.HIT:
			hits += 1
	danny.play_sfx(&"butt_slam")
	ScreenView.shake(get_tree(), Layout.IMPACT_SHAKE, Layout.IMPACT_SHAKE_STEPS, Layout.IMPACT_SHAKE_STEP)
	_play_impact(Layout.CENTRE)


func _hop() -> void:
	_begin_slam(Slam.HOP)
	_free_mark()
	hop_from = danny.global_position
	hop_lift = lift
	_face(danny, Layout.DANNY_REST)
	danny.play(&"air")


func _rest() -> void:
	_begin_slam(Slam.REST)
	_place_danny(Layout.DANNY_REST, 0.0)
	_face(danny, Layout.CENTRE)
	danny.play(&"idle")
	god.layer(&"strings").set_tension(danny, GodLayout.TENSION_WORK)


func _go_limp() -> void:
	_begin_slam(Slam.LIMP)
	limp_owed = false
	danny.play(danny.spec.limp)
	god.layer(&"strings").set_tension(danny, GodLayout.TENSION_LIMP)


# The eighth: he goes limp at rest. Called off mid-slam he never lands; he goes straight back.
func _calm_danny() -> void:
	match slam:
		Slam.REST, Slam.YANK:
			_go_limp()
		Slam.LEAP, Slam.SHADOW, Slam.DROP:
			limp_owed = true
			_hop()
		Slam.SIT, Slam.HOP:
			limp_owed = true


# His lift rides on his sprite alone, so his node, his hooks' base and his sort stay on the floor under him.
func _place_danny(at: Vector2, px: float) -> void:
	danny.global_position = at.round()
	lift = px
	danny.sprite.position = danny.sprite_base_position + Vector2(0, -roundf(px))


func _free_mark() -> void:
	if is_instance_valid(mark):
		mark.queue_free()
	mark = null


# DannyBossSlams' landing: the flash and dust over everyone, then the cracks alone on the floor, held and faded.
func _play_impact(at: Vector2) -> void:
	var spec: Dictionary = DannyArt.fx(&"slam_impact")
	var cracks_frame: int = spec.cracks_frame
	var burst := _sheet(spec, DannyArt.SCALE)
	add_hazard(burst, at, god.layer(&"fx"))
	_play_once(burst, range(cracks_frame), spec.frame_time)
	var cracks := _sheet(spec, DannyArt.SCALE)
	cracks.frame = cracks_frame
	cracks.visible = false
	add_hazard(cracks, at, god.layer(&"floor"))
	var lie := cracks.create_tween()
	lie.tween_interval(spec.frame_time * cracks_frame)
	lie.tween_callback(cracks.show)
	lie.tween_interval(Layout.CRACKS_HOLD)
	lie.tween_property(cracks, "modulate:a", 0.0, Layout.CRACKS_FADE)
	lie.tween_callback(cracks.queue_free)


#THE EIGHTH

func _launch(keg_name: StringName) -> void:
	beat = Beat.LAUNCH
	launched = kegs[keg_name]
	kegs.erase(keg_name)
	launch_from = launched.global_position
	launch_at = kegs_clock
	# Its node goes to him at once, so the flight is carry()'s arc from its spot, and it sorts with him as it lands.
	launched.global_position = Layout.BURAK_FEET
	launched.carry(launch_from, 0.0, Layout.LAUNCH_ARC)
	_calm_danny()


func _run_launch() -> void:
	var weight := clampf((kegs_clock - launch_at) / Layout.LAUNCH_TIME, 0.0, 1.0)
	if _due(launch_at + Layout.LAUNCH_TIME):
		weight = 1.0
	launched.carry(launch_from, weight, Layout.LAUNCH_ARC)
	if weight >= 1.0:
		_burst_on_burak()


# A burst on him that hurts nobody, and he is dazed. The rest of the floor goes, the HUD comes back for the payoff, and
# the player is let go to walk to him.
func _burst_on_burak() -> void:
	launched.blow()
	launched = null
	var spec: Dictionary = BurakArt.fx(&"blast")
	var burst := _sheet(spec, Layout.BURST_SCALE)
	add_hazard(burst, Layout.BURAK_FEET, god.layer(&"fx"))
	_play_once(burst, range(spec.hframes), spec.frame_time)
	burak.play_sfx(&"blast")
	burak.stop_sfx(&"fuse_hiss")
	ScreenView.shake(get_tree(), Layout.BURST_SHAKE, Layout.BURST_SHAKE_STEPS, Layout.BURST_SHAKE_STEP)
	burak.play(&"broken")
	_show_stars()
	for keg in kegs.values():
		if is_instance_valid(keg):
			keg.fade_away()
	kegs.clear()
	for flight in flights:
		if is_instance_valid(flight.node):
			flight.node.fade_away()
	flights.clear()
	throws.clear()
	_clear_floor()
	if hits == 0:
		player().hype.add(Layout.HYPE_CLEAN)
	hud(true)
	hide_hint()
	hide_arrow()
	arrow_off_at = -1.0
	_lower_player()
	player().unlock_actions()
	beat = Beat.WALK
	stage_ended.emit()


# In the uppercut's reach of him (PlayerFinisher._in_reach: his hurtbox grown uppercut_reach), with a margin to spare.
func _in_reach() -> bool:
	var body := player()
	var shape: CollisionShape2D = burak.get_finisher_hurtbox().get_node("CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	return box.grow(body.finisher.uppercut_reach - Layout.REACH_MARGIN).has_point(body.global_position)


func _show_stars() -> void:
	var spec := FinisherArtLayout.stars()
	stars = Sprite2D.new()
	stars.name = "DazeStars"
	stars.texture = load(spec.texture)
	stars.hframes = spec.hframes
	stars.centered = false
	stars.offset = -spec.pivot
	stars.scale = Vector2.ONE * spec.scale
	stars_clock = 0.0
	add_hazard(stars, burak.get_daze_anchor(), god.layer(&"fx"))


func _spin_stars(delta: float) -> void:
	if not is_instance_valid(stars):
		return
	stars_clock += delta
	stars.frame = int(stars_clock / FinisherArtLayout.stars().frame_time) % stars.hframes


#THE FLOOR

func _build_counter() -> void:
	var scale := GodLayout.ui_scale()
	counter = PIPS_SCRIPT.new()
	counter.name = "KegCounter"
	counter.scale = Vector2.ONE * scale
	add_hazard(counter, Layout.counter_origin(scale), god.layer(&"fx"))
	counter.show_pips(Layout.DEFUSES)


# The burst's last frame on the floor where a keg blew, until the eighth; a second blast there replaces it.
func _lay_debris(keg_name: StringName) -> void:
	if is_instance_valid(debris.get(keg_name)):
		debris[keg_name].queue_free()
	var spec: Dictionary = BurakArt.fx(&"barrel_break")
	var sprite := _sheet(spec, BurakArt.SCALE)
	sprite.frame = spec.debris_frame
	add_hazard(sprite, Layout.KEG_POINTS[keg_name], god.layer(&"floor"))
	debris[keg_name] = sprite


func _clear_floor() -> void:
	for node in debris.values() + [counter]:
		if not is_instance_valid(node):
			continue
		var fade: Tween = node.create_tween()
		fade.tween_property(node, "modulate:a", 0.0, Layout.COUNTER_FADE)
		fade.tween_callback(node.queue_free)
	debris.clear()
	counter = null


#THE PLAYER'S DRAWING

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


func _stand() -> void:
	var pose: Dictionary = GodLayout.BASE_POSE
	player().play_pose(pose.frames, pose.times, pose.loop)


#HELPERS

func _soles() -> Vector2:
	return player().global_position + Vector2(0, Layout.SOLES_OVER_ORIGIN)


func _player_down() -> bool:
	var body := player()
	return body == null or body.playerHealth <= 0 or body.fight_over


func _keg_centre(keg: Node2D) -> Vector2:
	return keg.global_position + BurakArt.keg_rect(BurakArt.KEG.body).get_center()


# A texel of the frame `puppet` shows now, in world px, mirrored with its sprite: every sheet is centred on the sprite,
# so its rect is the frame's.
func _texel_world(puppet: Node2D, texel: Vector2) -> Vector2:
	var sprite: Sprite2D = puppet.sprite
	var rect := sprite.get_rect()
	if sprite.flip_h:
		texel.x = rect.size.x - 1.0 - texel.x
	return sprite.to_global(rect.position + texel)


static func _face(puppet: Node2D, point: Vector2) -> void:
	if point.x != puppet.global_position.x:
		puppet.face(point.x < puppet.global_position.x)


static func _ease_out(x: float) -> float:
	var left := 1.0 - clampf(x, 0.0, 1.0)
	return 1.0 - left * left


# The pistol's flash and smoke off the muzzle, at the nearest of its drawn headings, flipped sideways only.
func _muzzle(at: Vector2, heading: Vector2) -> void:
	var spec: Dictionary = BurakArt.fx(&"muzzle")
	var pick: Array = BurakArt.art_frame(heading, spec.headings)
	var first: int = pick[0] * spec.frames_per_heading
	var frames: Array = (spec.flash_frames + spec.smoke_frames).map(func(f: int) -> int: return first + f)
	var sprite := _sheet(spec, BurakArt.SCALE)
	sprite.flip_h = pick[1]
	add_hazard(sprite, at, god.layer(&"fx"))
	_play_once(sprite, frames, spec.frame_time)


static func _sheet(spec: Dictionary, scale: float) -> Sprite2D:
	var sprite := Sprite2D.new()
	sprite.texture = load(spec.texture)
	sprite.hframes = spec.hframes
	sprite.offset = spec.get("offset", Vector2.ZERO)
	sprite.scale = Vector2.ONE * scale
	return sprite


static func _play_once(sprite: Sprite2D, frames: Array, frame_time: float) -> void:
	sprite.frame = frames[0]
	var play := sprite.create_tween()
	for i in range(1, frames.size()):
		play.tween_interval(frame_time)
		play.tween_callback(sprite.set_frame.bind(frames[i]))
	play.tween_interval(frame_time)
	play.tween_callback(sprite.queue_free)
