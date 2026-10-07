extends State

# Attack 2 (plan section 6, addendum 5): the tsunami's water tops up to a full flood, his cold breath freezes it from the
# pillar's base outward and blows the player down the ring, and his slams crack and then heave a stream of tremor walls
# (LiamTremorBlock rows, LiamTremorPatterns.schedule) across the ice, each rope to rope with one gap. On his clock (the
# state machine's knobs, section 6.1):
#   0            the flood tops up over settle_time; he inhales
#   breath_start his cold breath: the freeze front grows at freeze_speed (the player's ice on where it reaches them), and
#                the downdraft blows down the ring until the heave; a player above downdraft_launch_above is thrown down
#   crack_slam   slam 1: cracks race out from the pillar's base to the two opening walls over crack_time, their
#                footprints glowing
#   heave_slam   slam 2: both heave, solid and hurting; the downdraft ends; the pillar opens
#   then         a slam every slam_interval (a rumble and a small shake): from march_delay_slams slams after the heave
#                the opening walls march march_step px down a slam, gliding the whole slam with march_glide
#                (LiamTremorBlock.march), and a block whose bottom reaches march_floor_y sinks; each time the newest wall
#                has marched stream_every steps, a new one tells at the top (cracks racing to it from the pillar's base)
#                and heaves a slam later, marching from that slam on
#   heave + tremor_time   every wall crumbles; CRUMBLE_TIME later it is over (his wind's reset, then the next attack).
#                The ice and the player's footing on it carry on into attack 3, which melts it.
# The round's first pillar hit interrupts it: the slams and the new walls stop and every block crumbles at once, and the
# ice stays, through the round and its blast, for attack 3.

const LiamTremorBlock := preload("res://Scripts/LiamTremorBlock.gd")
const Patterns := preload("res://Scripts/LiamTremorPatterns.gd")
const Layout := preload("res://Scripts/LiamArtLayout.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const LiamElementFx := preload("res://Scripts/LiamElementFx.gd")

# The slam pose's impact lands this far into it: raise and overhead first.
const SLAM_IMPACT := 0.2
const CRACK_SHAKE := 6.0
const HEAVE_SHAKE := 10.0
const SHAKE_STEPS := 4
const SHAKE_STEP_TIME := 0.03
# What sixty steps of 1/60 fall short of a second by: a beat due on a frame lands on that frame, so the slams come
# exactly a slam_interval apart and a glide chained slam to slam never stalls a frame.
const EPSILON := 0.0001

var body: CharacterBody2D
var state_machine: Node
var running := false
var clock := 0.0
# This run's number (its walls' gap order) and its walls, LiamTremorPatterns.schedule's with each one's blocks once it
# is built; every block of every wall, for the crumbles.
var run := 0
var walls: Array[Dictionary] = []
var blocks: Array[Node2D] = []
var built := 0
# The run's beats as they happen, on this state's clock, for a test: breath, crack, heave, timeout; and each wall's
# tell and heave [k, tell clock, heave clock].
var beats := {}
var wall_log: Array = []
var next_slam_pose := 0.0
var next_pulse := 0.0
# Slams since the heave, counted rather than timed so a float's last bit can't put the march a slam late, and the
# march's steps so far.
var slams_since_heave := 0
var march_steps := 0
# Seconds since the ridges crumbled at the timeout, or below 0.
var ending := -1.0
var breath: Node2D
# The downdraft drawn (LiamElementFx.downdraft), from the breath to the heave: exactly while it blows.
var downdraft_fx: Node2D


func Enter() -> void:
	running = true
	clock = 0.0
	ending = -1.0
	slams_since_heave = 0
	march_steps = 0
	beats.clear()
	wall_log.clear()
	var sm: Node = state_machine
	run = sm.tremor_runs
	sm.tremor_runs += 1
	walls = Patterns.schedule(run, sm.march_delay_slams, sm.stream_every, roundi(sm.tremor_time / sm.slam_interval), sm.stream_gap)
	blocks.clear()
	built = 0
	body.pillar.set_shielded(true)
	body.flood.settle(sm.settle_time)
	body.play_anim(&"cold_breath")
	next_slam_pose = sm.crack_slam - SLAM_IMPACT
	for wall in walls:
		if wall.tell_slam < 0:
			_build_wall(wall)


func Exit() -> void:
	interrupt()


# The slams stop and every ridge crumbles at once; the ice stays. Idempotent.
func interrupt() -> void:
	running = false
	ending = -1.0
	_show_breath(false)
	_stop_downdraft()
	for block in blocks:
		if is_instance_valid(block):
			block.crumble()
	blocks.clear()


func Physics_Update(delta: float) -> void:
	if ending >= 0.0:
		_step_ending(delta)
		return
	if not running:
		return
	clock += delta
	var sm: Node = state_machine
	var player: Node2D = sm.get_player()
	if player != null and not player.on_ice and body.flood.is_frozen_at(player.global_position):
		sm.set_player_ice(true)
	if clock + EPSILON >= sm.breath_start and not beats.has(&"breath"):
		_breathe(player)
	if beats.has(&"breath") and not beats.has(&"heave") and player != null:
		player.add_drift(Vector2(0, sm.downdraft_speed))
	if clock + EPSILON >= next_slam_pose:
		body.play_anim(&"slam")
		next_slam_pose += sm.slam_interval
		if beats.has(&"breath"):
			_show_breath(false)
	if clock + EPSILON >= sm.crack_slam and not beats.has(&"crack"):
		_crack()
	if clock + EPSILON >= sm.heave_slam and not beats.has(&"heave"):
		_heave()
	if beats.has(&"heave") and clock + EPSILON >= next_pulse and clock + EPSILON < sm.heave_slam + sm.tremor_time:
		_pulse()
	if beats.has(&"heave") and clock + EPSILON >= sm.heave_slam + sm.tremor_time:
		_time_out()


func _breathe(player: Node2D) -> void:
	var sm: Node = state_machine
	beats[&"breath"] = clock
	body.flood.freeze_from(sm.PERCH, sm.freeze_speed)
	body.play_sfx(&"breath")
	_show_breath(true)
	_stop_downdraft()
	downdraft_fx = LiamElementFx.downdraft(body.fx_layer, sm.downdraft_speed)
	if player != null and player.global_position.y < sm.downdraft_launch_above:
		sm.launch_player(sm.launch_spot(player.global_position))


func _stop_downdraft() -> void:
	if is_instance_valid(downdraft_fx):
		downdraft_fx.stop()
	downdraft_fx = null


func _crack() -> void:
	beats[&"crack"] = clock
	for wall in walls:
		if wall.tell_slam < 0:
			_tell(wall)
	_slam_burst()
	ScreenView.shake(get_tree(), CRACK_SHAKE, SHAKE_STEPS, SHAKE_STEP_TIME)


func _heave() -> void:
	var sm: Node = state_machine
	beats[&"heave"] = clock
	_stop_downdraft()
	for wall in walls:
		if wall.heave_slam == 0:
			_heave_wall(wall)
	body.pillar.set_shielded(false)
	next_pulse = sm.heave_slam + sm.slam_interval
	_slam_burst()
	ScreenView.shake(get_tree(), HEAVE_SHAKE, SHAKE_STEPS, SHAKE_STEP_TIME)


# A slam: every heaved wall past its hold marches (the rest pulse), a wall due to heave heaves and marches from this
# slam, and a wall due to tell rises into its tell at the top.
func _pulse() -> void:
	var sm: Node = state_machine
	slams_since_heave += 1
	var slam := slams_since_heave
	# Untyped: a typed parameter would refuse a freed ridge before is_instance_valid could look at it.
	blocks.assign(blocks.filter(func(block) -> bool: return is_instance_valid(block)))
	var marched := false
	for wall in walls:
		if not wall.has("blocks") or wall.heave_slam >= slam:
			continue
		if slam >= wall.move_from:
			_march_wall(wall)
			marched = true
		else:
			for block in wall.blocks:
				if is_instance_valid(block):
					block.pulse()
	for wall in walls:
		if wall.has("blocks") and wall.heave_slam == slam:
			_heave_wall(wall)
			_march_wall(wall)
			marched = true
	for wall in walls:
		if wall.tell_slam == slam:
			_build_wall(wall)
			_tell(wall)
	if marched:
		march_steps += 1
	next_pulse += sm.slam_interval
	body.play_sfx(&"rumble")
	ScreenView.shake(get_tree(), state_machine.pulse_shake, SHAKE_STEPS, SHAKE_STEP_TIME)


func _time_out() -> void:
	beats[&"timeout"] = clock
	running = false
	for block in blocks:
		if is_instance_valid(block):
			block.crumble()
	blocks.clear()
	body.play_anim(&"perch_idle")
	ending = 0.0


func _step_ending(delta: float) -> void:
	clock += delta
	ending += delta
	var sm: Node = state_machine
	if ending >= Layout.CRUMBLE_TIME:
		ending = -1.0
		sm.attack_finished(self)


# A wall's blocks laid where it will heave, not yet telling.
func _build_wall(wall: Dictionary) -> void:
	var sm: Node = state_machine
	var player: Node2D = sm.get_player()
	var built_blocks: Array[Node2D] = []
	for rect: Rect2 in wall.rects:
		var block := LiamTremorBlock.new()
		block.name = "Ridge%d" % built
		block.rect = rect
		block.player = player
		block.bounce = sm.tremor_bounce
		block.floor_y = sm.march_floor_y
		block.pinned_crumbles = sm.march_pinned_crumbles
		block.position = body.floor_layer.to_local(rect.position)
		sm.add_hazard(block, body.floor_layer)
		blocks.append(block)
		built_blocks.append(block)
		built += 1
	for block in built_blocks:
		block.siblings = built_blocks
	wall.blocks = built_blocks
	wall_log.append([wall.k, -1.0, -1.0])


# Its cracks racing out to it from the pillar's base, reaching its farthest block in crack_time.
func _tell(wall: Dictionary) -> void:
	var sm: Node = state_machine
	var reach := 0.0
	for block in wall.blocks:
		reach = maxf(reach, sm.PERCH.distance_to(sm.PERCH.clamp(block.rect.position, block.rect.end)))
	var speed: float = reach / sm.crack_time
	for block in wall.blocks:
		block.tell(sm.PERCH, speed)
	_log_wall(wall.k, 1)


func _heave_wall(wall: Dictionary) -> void:
	for block in wall.blocks:
		if is_instance_valid(block):
			block.heave()
	_log_wall(wall.k, 2)


# march_step px down: gliding the whole slam, or with march_glide off a lurch over march_lurch_time.
func _march_wall(wall: Dictionary) -> void:
	var sm: Node = state_machine
	var step_time: float = sm.slam_interval if sm.march_glide else sm.march_lurch_time
	for block in wall.blocks:
		if is_instance_valid(block):
			block.march(sm.march_step, step_time, not sm.march_glide)


func _log_wall(k: int, column: int) -> void:
	for entry: Array in wall_log:
		if entry[0] == k:
			entry[column] = clock


func _slam_burst() -> void:
	body.play_sfx(&"slam")
	var at: Vector2 = body.pose_point(&"staff_butt", &"slam")
	var fx := Node2D.new()
	body.fx_layer.add_child(fx)
	fx.global_position = at.round()
	var play := fx.create_tween()
	if Layout.final_slam_burst():
		var sheet := Sprite2D.new()
		var texture: Texture2D = load(Layout.SLAM_BURST_SHEET)
		sheet.texture = texture
		sheet.hframes = roundi(texture.get_width() / Layout.SLAM_BURST_FRAME.x)
		sheet.scale = Vector2.ONE * Layout.SCALE
		sheet.offset = Layout.SLAM_BURST_FRAME / 2.0 - Layout.SLAM_BURST_PIVOT
		fx.add_child(sheet)
		var times := Layout.spread(Layout.SLAM_BURST_TIMES, sheet.hframes)
		for k in sheet.hframes:
			play.tween_callback(sheet.set_frame.bind(k))
			play.tween_interval(times[k])
		play.tween_callback(fx.queue_free)
		return
	var look: Dictionary = Layout.PLACEHOLDER_SLAM
	var spikes := PackedVector2Array()
	var count: int = look.spikes * 2
	for k in count:
		var reach: float = look.radius * (1.0 if k % 2 == 0 else 0.4)
		spikes.append(Vector2.from_angle(PI + PI * float(k) / float(count - 1)) * reach)
	var star := Polygon2D.new()
	star.polygon = spikes
	star.color = look.color
	fx.add_child(star)
	play.set_parallel()
	play.tween_property(fx, "scale", Vector2.ONE * 1.3, 0.2).from(Vector2.ONE * 0.6)
	play.tween_property(fx, "modulate:a", 0.0, 0.2)
	play.chain().tween_callback(fx.queue_free)


# The plume stopping: its sheet's end frame for a frame's time, then gone; the stand-in cone at once.
func _end_breath(plume: Node2D) -> void:
	var sheet: Sprite2D = null
	for child in plume.get_children():
		if child is Sprite2D:
			sheet = child
	if sheet == null:
		plume.queue_free()
		return
	var cycle: Tween = plume.get_meta(&"cycle", null)
	if cycle != null and cycle.is_valid():
		cycle.kill()
	sheet.frame = sheet.hframes - 1
	var hold := plume.create_tween()
	hold.tween_interval(Layout.BREATH_FRAME_TIME)
	hold.tween_callback(plume.queue_free)


# His cold breath's plume, from his mouth down to the pillar's base: its sheet once it ships, a pale cone until then.
func _show_breath(on: bool) -> void:
	if not on:
		if is_instance_valid(breath):
			_end_breath(breath)
		breath = null
		return
	if is_instance_valid(breath):
		return
	breath = Node2D.new()
	breath.name = "ColdBreath"
	body.fx_layer.add_child(breath)
	breath.global_position = body.pose_point(&"mouth", &"cold_breath").round()
	if Layout.final_breath():
		var sheet := Sprite2D.new()
		var texture: Texture2D = load(Layout.BREATH_SHEET)
		sheet.texture = texture
		sheet.hframes = roundi(texture.get_width() / Layout.BREATH_FRAME.x)
		sheet.scale = Vector2.ONE * Layout.SCALE
		sheet.offset = Layout.BREATH_FRAME / 2.0 - Layout.BREATH_PIVOT
		breath.add_child(sheet)
		# Its start frame once, then the frames between it and its end frame in turn, however many the sheet holds.
		sheet.frame = 0
		var loop_frames := maxi(sheet.hframes - 2, 1)
		var step := [0]
		var cycle := breath.create_tween().set_loops()
		cycle.tween_interval(Layout.BREATH_FRAME_TIME)
		cycle.tween_callback(func() -> void:
			sheet.frame = 1 + step[0] % loop_frames
			step[0] += 1)
		breath.set_meta(&"cycle", cycle)
		return
	var look: Dictionary = Layout.PLACEHOLDER_BREATH
	var reach: float = state_machine.PERCH.y - breath.global_position.y
	var cone := Polygon2D.new()
	cone.polygon = PackedVector2Array([Vector2(-10, 0), Vector2(10, 0), Vector2(look.width / 2.0, reach), Vector2(-look.width / 2.0, reach)])
	cone.color = look.color
	breath.add_child(cone)
	var edge := Line2D.new()
	edge.points = cone.polygon
	edge.closed = true
	edge.width = 3.0
	edge.default_color = look.edge
	breath.add_child(edge)
