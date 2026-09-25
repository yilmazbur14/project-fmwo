extends State

# Greyson's final phase, the Punch-Out brawl (PLAN_BRAWL.md). His bar is empty but the fight isn't over: he buries
# the ring in roof debris and the fight becomes a boxing match seen from behind the player.
#
#   KO_WAIT     the finisher that put him at 0 plays out; a juggle's crash can land here and still ask things, so
#               every call of the finisher's contract is inert until the boxing starts.
#   KO_HOLD     ko_hold: his bar, gauge and meter fade, and the player is free.
#   CUT         a BossEntrance cut, hold-to-skip: the player walks onto their mark while he gets home, four barbell
#               slams bring the roof down in four waves (GreysonBrawlRubble), he tosses the barbell away, and on one
#               frame the camera cuts in, the player is locked in their 2x guard and he is in his (_cut_in). A skip
#               lands on that same frame.
#   SQUARE_UP   square_up, then the first combo.
#   BOXING      combos of L (his left hook, a gold LEFT arrow: slip LEFT), R (his right hook: slip RIGHT) and S (the
#               straight under the red badge: the guard, which parries it through PlayerDefense's posed guard). The
#               first answer after a tell decides and resolves resolve_delay later, or at the lead. A slip or a
#               parry is a read and a hit takes one back; daze_reads reads daze him. Nothing shows the count.
#   ROCKED      the dazing read's rocked_delay, then rocked_time of his rocked frames, then the finisher.
#   FINISHER    the house tiered finisher on the brawl's uppercut sheet (PlayerFinisher.begin). Its whole boss
#   UPPERCUTS   contract is answered here, and each uppercut is one of uppercuts_to_kill.
#   RECOVER     after a fizzle, or a crash he survives: his recover frames, the guard, then the next combo.
#   KO_SNAP     the killing uppercut's snap; KO_FALL, his fall at its crash; KO_DOWN, the thud and a beat, then the
#   ...         hand-off to Defeated (greyson_beaten(true)), lying on the frame the KO left him on.
#   LOST        a punch took the player's last heart: the view comes level and FightOutro takes it to Victory.
#
# EVERY WAIT is a Physics_Update accumulator or a node-bound tween, and the cut's go through `waits` so its skip
# can run them out: a pause and a finisher's freeze hold all of it. NOTHING HERE IS IN greyson_hazard: the FX and
# the rubble are GreysonBrawlFx's and GreysonBrawlRubble's. HIS SPRITE is the brawl's own from the barbell toss until
# the KO frame it leaves on him (body.halt_anim(); every clip puts his whole sheet on). release() is idempotent and
# starts no tweens; the settled heaps stay through both outros.

const Layout := preload("res://Scripts/GreysonBrawlLayout.gd")
const GreysonArt := preload("res://Scripts/GreysonArtLayout.gd")
const BrawlFx := preload("res://Scripts/GreysonBrawlFx.gd")
const BrawlRubble := preload("res://Scripts/GreysonBrawlRubble.gd")
const BossEntrance := preload("res://Scripts/BossEntrance.gd")
const DirectionPress := preload("res://Scripts/DirectionPress.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")

enum Phase { KO_WAIT, KO_HOLD, CUT, SQUARE_UP, BOXING, ROCKED, FINISHER, UPPERCUTS, RECOVER, KO_SNAP, KO_FALL, KO_DOWN, LOST, DONE }

const HOOK_L := &"L"
const HOOK_R := &"R"
const STRAIGHT := &"S"
# Combos 1 and 2, then picks off the tier's list: never the same combo twice running, never two straights in a row.
const OPENERS := [[&"L", &"R"], [&"S", &"L"]]
const PATTERNS := [
	[[&"L", &"R"], [&"R", &"L"], [&"L", &"S"], [&"R", &"S"], [&"S", &"L"], [&"S", &"R"]],
	[[&"L", &"R", &"S"], [&"R", &"L", &"S"], [&"L", &"L", &"R"], [&"R", &"R", &"L"], [&"S", &"L", &"R"],
		[&"L", &"S", &"R"], [&"R", &"S", &"L"]],
	[[&"L", &"R", &"L", &"S"], [&"R", &"L", &"R", &"S"], [&"L", &"L", &"S", &"R"], [&"R", &"R", &"S", &"L"],
		[&"S", &"L", &"R", &"S"], [&"L", &"S", &"L", &"R"], [&"R", &"S", &"R", &"L"], [&"S", &"R", &"L"], [&"S", &"L", &"S"]],
]
const ANSWERS := {&"L": &"left", &"R": &"right", &"S": &"guard"}
const CLIPS := {&"L": "hook_l", &"R": "hook_r", &"S": "straight"}
# What lands when the answer was wrong: the straight's twin can't be parried, so a guard press after another
# answer can't rescue it.
const HIT_IDS := {&"L": &"greyson_brawl_hook_l", &"R": &"greyson_brawl_hook_r", &"S": &"greyson_brawl_straight_unguarded"}
const PARRY_ID := &"greyson_brawl_straight"
const SHAKE_STEPS := 6
const SHAKE_STEP := 0.03

@export var body : CharacterBody2D

#THE BOXING (seconds; each array a value a tier, the tier being min(cycle, 3); the lead never under 0.40)
@export var lead_times: Array[float] = [0.46, 0.43, 0.40]
@export var gap_times: Array[float] = [0.30, 0.24, 0.18]
@export var neutral_times: Array[float] = [0.90, 0.75, 0.60]
@export var resolve_delay := 0.06
@export var daze_reads := 6
@export var uppercuts_to_kill := 4
@export var slip_hype := 10.0
# How long the player's answer pose holds after the resolve before their guard comes back.
@export var player_recover := 0.16
@export var hit_shake := 6.0
@export var read_cheer := 0.4
@export var rocked_delay := 0.15
@export var rocked_time := 0.25
@export var rocked_pitch := 0.8
@export var rocked_cheer := 1.0
@export var fizzle_recover := 1.0
@export var reframe_time := 0.3
# Off at 0: the half-hearts the player is given back to at the cut-in, if they have fewer.
@export var entry_min_health := 0

#THE ENTRY AND THE CUT (seconds from the cut's start, S being when both of them are in place)
@export var ko_hold := 0.4
@export var walk_speed := 650.0
@export var walk_min := 0.3
@export var walk_max := 1.2
# Nearer than this to the mark, the player is put on it; further from HOME than home_snap, he teleports there.
@export var walk_snap := 5.0
@export var home_snap := 8.0
@export var teleport_time := 0.5
@export var rise_time := 0.6
@export var music_duck_db := -6.0
@export var music_duck_time := 0.3
# Each slam's impact after S, and its shake; the slam clip is started slam_windup before it, the time its IMPACT
# frame (f3) takes to come up (GreysonArtLayout).
@export var slam_times: Array[float] = [0.40, 0.85, 1.30, 1.75]
@export var slam_shakes: Array[float] = [10.0, 12.0, 14.0, 16.0]
@export var slam_windup := 0.40
@export var toss_at := 2.45
@export var cut_at := 2.85
@export var square_up := 0.8
@export var square_up_cheer := 2.0

#THE KO
@export var ko_fall_time := 0.45
@export var thud_shake := 20.0
@export var thud_pitch := 0.8
@export var ko_cheer := 4.0
@export var ko_settle := 0.3

@onready var state_machine = get_parent()

# Set by the state machine before Enter(): he was juggled to 0 and landed here lying on the juggle's KO loop.
var from_juggle := false
# The tests' knob: &"win" skips the cut and the boxing, and he is beaten as soon as the finisher that put him at 0
# is over.
var auto_result := &""
# The tests' pin: combos thrown in this order before any pick.
var pinned_combos: Array = []

var phase := Phase.DONE
var entered_count := 0
var cuts := 0
# What a test reads: the cycle (1, then one more a finisher), the hidden meter, what is left of him, the dazes,
# each punch as it resolved, and each beat of the cut that was seen through.
var cycle := 1
var reads := 0
var uppercuts_left := 4
var dazes := 0
var punch_log: Array[Dictionary] = []
var beat_times := {}
var setup_time := 0.0

# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
var phase_clock := 0.0
var wait_left := 0.0
var fx: Node2D
var rubble: Node2D
var chin_box: Area2D
var cut: CanvasLayer
var cut_skipped := false
# The cut's beats, [seconds from its start, what happens, order], on the phase's own clock, and the next one due.
var cut_events: Array = []
var cut_next := 0
# The walk's and the teleport's tweens, which a skip runs out.
var waits: Array[Tween] = []
var beat_started := 0.0
var teleport: Tween
var press := DirectionPress.new()
var combo: Array = []
var combo_step := 0
var combos_thrown := 0
var last_combo: Array = []
var last_kind := &""
# The punch from its tell to the next one: kind, tier, lead, its clock, the answer and when, when it resolves, what
# it came to, its source (its own, so a parry's absorbed_until can't swallow the next), and its later beats.
var punch := {}
# True only between offering the daze and the finisher taking it (enter_daze).
var offering := false
var player_ref: Node2D
var player_z := 0
var player_z_saved := false
var framed := false
# His clip, drawn on his sprite by this state.
var clip_name := &""
var clip := {}
var clip_step := 0
var clip_clock := 0.0
var clip_time := 0.0
var clip_done := false


func Enter() -> void:
	entered_count += 1
	released = false
	phase = Phase.KO_WAIT
	phase_clock = 0.0
	cycle = 1
	reads = 0
	uppercuts_left = uppercuts_to_kill
	dazes = 0
	punch_log.clear()
	beat_times.clear()
	combo = []
	combo_step = 0
	combos_thrown = 0
	last_combo = []
	last_kind = &""
	punch = {}
	offering = false
	cut_skipped = false
	framed = false
	clip = {}
	press = DirectionPress.new()
	body.velocity = Vector2.ZERO
	body.set_hurtbox_active(false)
	var player := _player()
	if player != null:
		player.clear_statuses()
	# Off a juggle he lies on its own KO loop until the brawl takes his sprite over (_after_ko).
	if not from_juggle:
		body.show_body()


func Exit() -> void:
	release()


func _exit_tree() -> void:
	release()


func release() -> void:
	if released:
		return
	released = true
	phase = Phase.DONE
	offering = false
	clip = {}
	punch = {}
	combo = []
	if is_instance_valid(body):
		ParryTell.clear(body)
	if is_instance_valid(fx):
		fx.queue_free()
	fx = null
	if is_instance_valid(rubble):
		rubble.clear_falling()
	if is_instance_valid(chin_box):
		chin_box.queue_free()
	chin_box = null
	if teleport:
		teleport.kill()
	teleport = null
	var player := player_ref if is_instance_valid(player_ref) else _player()
	if is_instance_valid(cut):
		# Out of the tree with the fight scene it can only go; in it, it hands the player back.
		if cut.is_inside_tree():
			cut.end()
			if player != null:
				player.is_talking = false
		else:
			cut.queue_free()
	cut = null
	if player != null:
		if player.is_action_locked:
			player.unlock_actions()
		_restore_player_z(player)
	if framed:
		framed = false
		if is_inside_tree():
			ScreenView.reset(get_tree())
	_disconnect_player()


func Physics_Update(delta: float) -> void:
	if released:
		return
	_advance_clip(delta)
	# Every step, so a stick held over from before a tell has to come back to the middle before it can answer.
	var flick := press.poll()
	phase_clock += delta
	match phase:
		Phase.KO_WAIT:
			if not _finisher_busy():
				_after_ko()
		Phase.KO_HOLD:
			if phase_clock >= ko_hold:
				_start_cut()
		Phase.CUT:
			_run_cut()
		Phase.SQUARE_UP:
			if phase_clock >= square_up:
				_end_beat(&"square_up")
				_start_combo()
		Phase.BOXING:
			_box(delta, flick)
		Phase.ROCKED:
			if phase_clock >= rocked_time:
				_offer_daze()
		Phase.RECOVER:
			if phase_clock >= wait_left and not _finisher_busy():
				_start_combo()
		Phase.KO_FALL:
			if phase_clock >= ko_fall_time:
				_thud()
		Phase.KO_DOWN:
			if phase_clock >= ko_settle and not _finisher_busy():
				_hand_off()


#ENTRY

func _after_ko() -> void:
	if auto_result == &"win":
		body.hide_boss_hud(GreysonArt.HUD_FADE_TIME)
		state_machine.greyson_beaten(from_juggle)
		return
	phase = Phase.KO_HOLD
	phase_clock = 0.0
	body.hide_boss_hud(ko_hold)
	if from_juggle:
		_stop_lingering()
	# Before anything draws on his sprite: turning him redraws the frame his own animation is on.
	body.set_facing(false)
	if from_juggle:
		_play_clip(&"lying")
	else:
		_body_anim(&"idle")


#THE CUT

func _start_cut() -> void:
	phase = Phase.CUT
	phase_clock = 0.0
	cuts += 1
	_start_beat()
	_build_stage()
	var player := _player()
	cut = BossEntrance.new()
	cut.name = "BrawlCut"
	add_child(cut)
	cut.skipped.connect(skip_cut)
	cut.begin(player)
	state_machine.crowd(&"hush")
	body.duck_music(music_duck_db, music_duck_time)
	var walk := _walk_player()
	var his := _bring_him_home()
	setup_time = maxf(maxf(walk, his), walk_min)
	cut_events = _cut_events()
	cut_next = 0


func _build_stage() -> void:
	if not is_instance_valid(fx):
		fx = BrawlFx.new()
		fx.name = "BrawlFx"
		body.fx_layer.add_child(fx)
	if not is_instance_valid(rubble):
		rubble = BrawlRubble.new()
		rubble.name = "BrawlRubble"
		body.hazard_layer.add_child(rubble)
		rubble.setup(body.fx_layer, body.floor_layer, state_machine.ROPES)
		rubble.wave_landed.connect(_on_wave_landed)
		rubble.barbell_landed.connect(_on_barbell_landed)


# Onto their mark on rails, on this node's own tween so the skip runs it out. Its seconds, 0 for no walk.
func _walk_player() -> float:
	var player := _player()
	if player == null:
		return 0.0
	var distance: float = player.global_position.distance_to(Layout.PLAYER_MARK)
	if distance <= walk_snap:
		player.global_position = Layout.PLAYER_MARK
		player.face_point(Layout.FACE_AT)
		return 0.0
	var seconds := clampf(distance / walk_speed, walk_min, walk_max)
	player.face_point(Layout.PLAYER_MARK)
	cut.play_player_anim(&"walking")
	var walk := _track(create_tween())
	walk.tween_method(_step_player.bind(player.global_position), 0.0, 1.0, seconds)
	walk.tween_callback(_player_on_mark)
	return seconds


func _step_player(weight: float, from: Vector2) -> void:
	var player := _player()
	if _cut_live() and player != null:
		player.global_position = from.lerp(Layout.PLAYER_MARK, weight).round()


func _player_on_mark() -> void:
	var player := _player()
	if not _cut_live() or player == null:
		return
	player.global_position = Layout.PLAYER_MARK
	cut.play_player_anim(&"idle_down")
	player.face_point(Layout.FACE_AT)


# Off a juggle he gets up where he lies; away from HOME he teleports there. His seconds, 0 if he is already home.
func _bring_him_home() -> float:
	var seconds := 0.0
	if from_juggle:
		_play_clip(&"get_up")
		seconds = rise_time
	if body.global_position.distance_to(state_machine.HOME) <= home_snap:
		body.global_position = state_machine.HOME
		return seconds
	teleport = _track(create_tween())
	teleport.tween_interval(seconds)
	teleport.tween_callback(_teleport_out)
	teleport.tween_interval(teleport_time / 2.0)
	teleport.tween_callback(_teleport_in)
	teleport.tween_interval(teleport_time / 2.0)
	teleport.tween_callback(_teleported)
	return seconds + teleport_time


func _teleport_out() -> void:
	if not _cut_live():
		return
	clip = {}
	body.teleport_out()
	# The teleport puts his HUD back for the main fight's sake; his bar is gone for good here.
	body.hide_boss_hud(0.0)


func _teleport_in() -> void:
	if _cut_live():
		body.teleport_in(state_machine.HOME)


func _teleported() -> void:
	if _cut_live():
		_body_anim(&"idle")


# The beats from S: both of them in place, each slam clip started its windup ahead of its impact, the four slams,
# the toss and the cut-in. All on the one clock, so no beat's rounding to a frame carries into the next.
func _cut_events() -> Array:
	var events: Array = [[setup_time, _in_place]]
	for k in slam_times.size():
		events.append([setup_time + maxf(slam_times[k] - slam_windup, 0.0), _swing])
		events.append([setup_time + slam_times[k], _slam.bind(k)])
	events.append([setup_time + toss_at, _toss])
	events.append([setup_time + toss_at + Layout.TOSS_FLING, _fling])
	events.append([setup_time + cut_at, _cut_in])
	for i in events.size():
		events[i].append(i)
	events.sort_custom(func(a: Array, b: Array) -> bool: return a[0] < b[0] or (a[0] == b[0] and a[2] < b[2]))
	return events


# Summed frame deltas land a hair short of a beat's time, which would hold it a frame long.
func _run_cut() -> void:
	while phase == Phase.CUT and cut_next < cut_events.size() and phase_clock >= cut_events[cut_next][0] - 0.0001:
		var event: Array = cut_events[cut_next]
		cut_next += 1
		event[1].call()


func _in_place() -> void:
	_end_beat(&"setup")
	_start_beat()


func _swing() -> void:
	_body_anim(&"slam")


func _slam(k: int) -> void:
	body.play_sfx(&"slam")
	ScreenView.shake(get_tree(), slam_shakes[k], SHAKE_STEPS, SHAKE_STEP)
	rubble.drop_wave(k)


func _on_wave_landed(_wave: int) -> void:
	body.play_sfx(&"brawl_debris")


func _toss() -> void:
	_play_clip(&"toss")


# The toss's fling frame: the barbell leaves his hand, landing just before the cut-in.
func _fling() -> void:
	body.play_sfx(&"brawl_toss_whoosh")
	rubble.toss_barbell(Layout.toss_from(body.global_position), cut_at - toss_at - Layout.TOSS_FLING - Layout.TOSS_LANDS)


func _on_barbell_landed() -> void:
	body.play_sfx(&"brawl_toss")


# The cut-in, on one frame, watched or skipped: the camera cut to the brawl's framing, the cut over, the player on
# their mark locked in their 2x guard facing him, him home in his, the fill settled and the crowd up.
func _cut_in() -> void:
	if phase == Phase.CUT and not cut_skipped:
		_end_beat(&"cut")
	phase = Phase.SQUARE_UP
	phase_clock = 0.0
	if teleport:
		teleport.kill()
	teleport = null
	rubble.settle()
	rubble.place_barbell()
	if is_instance_valid(cut):
		cut.end()
	cut = null
	body.global_position = state_machine.HOME
	body.show_body()
	body.set_hurtbox_active(false)
	body.hide_boss_hud(0.0)
	_play_clip(&"guard")
	_build_chin_box()
	_frame_view(0.0)
	var player := _player()
	if player != null:
		player.global_position = Layout.PLAYER_MARK
		player.velocity = Vector2.ZERO
		player.is_talking = false
		player.clear_statuses()
		if entry_min_health > 0 and player.playerHealth < entry_min_health:
			player.playerHealth = entry_min_health
			player.healthUI.update_health(player.playerHealth)
		_lock_player()
	state_machine.crowd(&"cheer", square_up_cheer)
	body.duck_music(0.0, music_duck_time)
	_start_beat()


# A held ui_cancel anywhere in the cut: every wait run out, his main-set teleport effects gone, the arena settled,
# and the cut-in a watched cut ends on.
func skip_cut() -> void:
	if released or cut_skipped or phase != Phase.CUT:
		return
	cut_skipped = true
	BossEntrance.run_out(waits)
	for hazard in get_tree().get_nodes_in_group(state_machine.HAZARD_GROUP):
		hazard.queue_free()
	BossEntrance.settle_arena(get_tree())
	body.snap_music_level()
	_cut_in()


#THE BOXING

func _start_combo() -> void:
	phase = Phase.BOXING
	phase_clock = 0.0
	var player := _player()
	if player != null and not player.is_posed():
		_lock_player()
	combo = _pick_combo()
	combo_step = 0
	_tell()


func _pick_combo() -> Array:
	combos_thrown += 1
	var picked: Array
	if not pinned_combos.is_empty():
		picked = pinned_combos.pop_front()
	elif combos_thrown <= OPENERS.size():
		picked = OPENERS[combos_thrown - 1]
	else:
		var pool: Array = PATTERNS[_tier() - 1].filter(func(c: Array) -> bool:
			return c != last_combo and not (last_kind == STRAIGHT and c[0] == STRAIGHT))
		picked = pool[state_machine.rng.randi_range(0, pool.size() - 1)]
	last_combo = picked
	return picked


func _tier() -> int:
	return clampi(cycle, 1, 3)


func _tell() -> void:
	var kind: StringName = combo[combo_step]
	var tier := _tier()
	var lead: float = lead_times[tier - 1]
	punch = {
		kind = kind, tier = tier, lead = lead, clock = 0.0, told_at = body.fight_clock, answer = &"",
		answer_at = -1.0, resolve_at = lead, resolved = false, wound = false, result = &"",
		source = RefCounted.new(), guard_at = INF, rocked_at = INF, next_at = INF,
	}
	last_kind = kind
	state_machine.rearm_parry()
	_play_clip(StringName(CLIPS[kind] + "_windup"))
	if kind == STRAIGHT:
		ParryTell.telegraph(body, PARRY_ID, lead, _tell_point)
		body.play_sfx(&"brawl_tell_parry")
	else:
		fx.show_arrow(kind == HOOK_R, _tell_point())
		body.play_sfx(&"brawl_tell")


func _tell_point() -> Vector2:
	return Layout.tell_point(body.global_position)


func _box(delta: float, flick: StringName) -> void:
	if punch.is_empty():
		return
	punch.clock += delta
	if not punch.resolved:
		if flick == &"left" or flick == &"right":
			_answer_direction(flick)
		if not punch.wound and punch.clock >= punch.resolve_at - Layout.STRIP_LEAD:
			punch.wound = true
			fx.wind(_strip_hook(punch.kind), _strike_point(punch.kind))
		if punch.clock >= punch.resolve_at:
			_resolve()
		return
	if punch.clock >= punch.guard_at:
		punch.guard_at = INF
		_pose_player(&"guard")
	if punch.clock >= punch.rocked_at:
		_rock()
		return
	if punch.clock >= punch.next_at:
		combo_step += 1
		if combo_step < combo.size():
			_tell()
		else:
			_start_combo()


func _input(event: InputEvent) -> void:
	if released:
		return
	# Read in every beat, so the stick's arming follows it through the ones that take no answer.
	var direction := press.read(event)
	if phase == Phase.BOXING and (direction == &"left" or direction == &"right"):
		_answer_direction(direction)


# The mash's keys are the arrows: a key still held from it answers nothing.
func _answer_direction(direction: StringName) -> void:
	var player := _player()
	if player != null and player.finisher.is_mash_latched():
		return
	answer(direction)


func _on_block_pressed(_credited: bool) -> void:
	answer(&"guard")


# The first answer to the punch that is up (&"left", &"right" or &"guard"): the player's pose at once, and the
# resolve resolve_delay from now or at the lead, whichever is first. Any later answer, and any before the tell,
# counts for nothing.
func answer(kind: StringName) -> void:
	if released or phase != Phase.BOXING or punch.is_empty() or punch.resolved or punch.answer != &"":
		return
	punch.answer = kind
	punch.answer_at = punch.clock
	punch.resolve_at = minf(punch.clock + resolve_delay, punch.lead)
	match kind:
		&"left":
			_pose_player(&"slip_left")
		&"right":
			_pose_player(&"slip_right")
		&"guard":
			_pose_player(&"parry")


func _resolve() -> void:
	var p := punch
	p.resolved = true
	var kind: StringName = p.kind
	var resolved_at: float = p.clock
	if kind == STRAIGHT:
		ParryTell.clear(body)
	fx.strike(_strip_hook(kind), _strike_point(kind))
	body.play_sfx(&"brawl_straight" if kind == STRAIGHT else &"brawl_hook")
	var player := _player()
	var health_before: int = player.playerHealth if player != null else 0
	var result := &"ignored"
	if player != null and kind != STRAIGHT and p.answer == ANSWERS[kind]:
		result = &"dodged"
	elif player != null:
		var id: StringName = PARRY_ID if kind == STRAIGHT and p.answer == &"guard" else HIT_IDS[kind]
		var outcome: int = player.receive_hit(HitInfo.make(id, p.source, state_machine.player_hurtbox_centre(), body))
		if outcome == HitInfo.Result.PARRIED:
			result = &"parried"
		elif outcome == HitInfo.Result.HIT:
			result = &"hit"
	p.result = result
	punch_log.append({kind = kind, tier = p.tier, lead = p.lead, told_at = p.told_at, answer = p.answer,
		answer_at = p.answer_at, resolve = resolved_at, result = result,
		damage = health_before - (player.playerHealth if player != null else 0)})
	var clip_key: String = CLIPS[kind]
	match result:
		&"dodged":
			_play_clip(StringName(clip_key + "_dodged"))
			body.play_sfx(&"brawl_dodge")
			fx.answer_arrow(true)
			fx.afterimage(player.sprite, -Layout.PLAYER_SLIP if p.answer == &"left" else Layout.PLAYER_SLIP)
			body.add_player_hype(slip_hype)
			_read(1)
		&"parried":
			_play_clip(StringName(clip_key + "_parried"))
			_read(1)
		&"hit":
			_play_clip(StringName(clip_key + "_landed"))
			fx.answer_arrow(false)
			fx.impact(Layout.his_point(Layout.STRAIGHT_LANDED if kind == STRAIGHT else Layout.HOOK_CONTACT, body.global_position))
			body.play_sfx(&"brawl_hit")
			ScreenView.shake(get_tree(), hit_shake, SHAKE_STEPS, SHAKE_STEP)
			_read(-1)
			if player.playerHealth <= 0:
				_lose()
				return
			if player.is_posed():
				_pose_player(&"hit")
		_:
			_play_clip(StringName(clip_key + "_landed"))
			fx.answer_arrow(false)
	var more := combo_step + 1 < combo.size()
	var after: float = gap_times[p.tier - 1] if more else neutral_times[p.tier - 1]
	p.guard_at = resolved_at + minf(player_recover, after)
	if reads >= daze_reads:
		reads = 0
		p.rocked_at = resolved_at + rocked_delay
	else:
		p.next_at = resolved_at + after


func _read(change: int) -> void:
	reads = clampi(reads + change, 0, daze_reads)
	if change > 0:
		state_machine.crowd(&"cheer", read_cheer, false)


func _strip_hook(kind: StringName) -> int:
	match kind:
		HOOK_L:
			return BrawlFx.LEFT_HOOK
		HOOK_R:
			return BrawlFx.RIGHT_HOOK
	return BrawlFx.STRAIGHT


func _strike_point(kind: StringName) -> Vector2:
	return Layout.his_point(Layout.STRAIGHT_CONTACT if kind == STRAIGHT else Layout.HOOK_CONTACT, body.global_position)


#THE DAZE AND THE FINISHER

func _rock() -> void:
	phase = Phase.ROCKED
	phase_clock = 0.0
	combo = []
	punch = {}
	fx.clear_arrow()
	ParryTell.clear(body)
	_pose_player(&"guard")
	_play_clip(&"rocked")
	body.play_sfx(&"brawl_hit", rocked_pitch)
	state_machine.crowd(&"cheer", rocked_cheer)


func _offer_daze() -> void:
	var player := _player()
	offering = true
	var started: bool = player != null and player.finisher.begin(body, Layout.uppercut_sheet())
	offering = false
	if started:
		dazes += 1
	else:
		_recover(fizzle_recover)


func _recover(seconds: float) -> void:
	phase = Phase.RECOVER
	phase_clock = 0.0
	wait_left = seconds
	_play_clip(&"recover")


# The finisher is over, however it went: the player back in their lock and 2x guard, the view back on the brawl.
func _on_finisher_finished() -> void:
	if released or phase < Phase.SQUARE_UP or phase == Phase.LOST:
		return
	_lock_player()
	_frame_view(reframe_time)
	if phase == Phase.KO_SNAP:
		_ko_fall()


#THE FINISHER'S BOSS CONTRACT (GreysonScript hands each of these here while this is his state)

func can_be_dazed() -> bool:
	return offering


func enter_daze() -> void:
	if not offering:
		return
	offering = false
	phase = Phase.FINISHER
	phase_clock = 0.0
	_play_clip(&"dazed")


# A fizzle, or a first uppercut that whiffed: he shakes it off and the next combo comes fizzle_recover later.
func exit_daze(finisher_landed: bool) -> void:
	if phase != Phase.FINISHER or finisher_landed:
		return
	cycle += 1
	_recover(fizzle_recover)


func can_be_juggled() -> bool:
	return phase == Phase.FINISHER


func begin_juggle() -> void:
	if phase == Phase.FINISHER:
		phase = Phase.UPPERCUTS


# He takes every uppercut standing: the finisher's arc runs, and draws nothing.
func juggle_headroom() -> float:
	return 0.0


func juggle_lift(_px: float) -> void:
	pass


func juggle_pose(pose: StringName, _crater := false) -> void:
	match pose:
		&"launch":
			if phase != Phase.UPPERCUTS:
				return
			if uppercuts_left <= 0:
				_ko_snap()
			else:
				_play_clip(&"uppercut")
		&"crash":
			if phase == Phase.KO_SNAP:
				_ko_fall()
			elif phase == Phase.UPPERCUTS:
				_play_clip(&"uppercut_settle")


func take_juggle_hit(amount: int, pitch: float) -> int:
	if phase != Phase.UPPERCUTS:
		return 0
	uppercuts_left = maxi(uppercuts_left - 1, 0)
	_play_hit(pitch)
	return amount


# The finisher without the tiered mash: one uppercut all the same.
func take_finisher(amount: int) -> int:
	if phase != Phase.FINISHER:
		return 0
	uppercuts_left = maxi(uppercuts_left - 1, 0)
	_play_hit(1.0)
	if uppercuts_left <= 0:
		_ko_snap()
	else:
		_play_clip(&"uppercut")
	return amount


func end_recovery(stagger_time: float) -> bool:
	if phase != Phase.UPPERCUTS and phase != Phase.FINISHER:
		return false
	cycle += 1
	_recover(stagger_time)
	return true


func get_max_health() -> int:
	return 100


func get_health_ratio() -> float:
	if phase < Phase.SQUARE_UP or phase == Phase.DONE:
		return 0.0
	return float(uppercuts_left) / float(uppercuts_to_kill)


func get_daze_anchor() -> Vector2:
	return Layout.daze_anchor(body.global_position)


func get_finisher_hurtbox() -> Area2D:
	_build_chin_box()
	return chin_box


func get_juggle_point() -> Vector2:
	return Layout.his_point(Layout.JUGGLE_POINT, body.global_position)


func juggle_knock_back(_push: Vector2, _time: float) -> void:
	pass


func knock_back(_push: Vector2, _time: float) -> void:
	pass


func flinch() -> void:
	pass


func can_parry_stagger(_hit: RefCounted) -> bool:
	return false


func parry_stagger(_duration: float) -> void:
	pass


func take_punch(_amount: int) -> int:
	return 0


func _play_hit(pitch: float) -> void:
	body.hit_sfx_player.pitch_scale = pitch
	body.hit_sfx_player.play()


# A code-built box on his dazed chin, on no collision layer: only the finisher reads it.
func _build_chin_box() -> void:
	if is_instance_valid(chin_box):
		return
	chin_box = Area2D.new()
	chin_box.name = "BrawlChinBox"
	chin_box.collision_layer = 0
	chin_box.collision_mask = 0
	chin_box.monitoring = false
	chin_box.monitorable = false
	var shape := CollisionShape2D.new()
	shape.name = "CollisionShape2D"
	var rect := RectangleShape2D.new()
	rect.size = Layout.CHIN_BOX
	shape.shape = rect
	chin_box.add_child(shape)
	body.add_child(chin_box)
	chin_box.global_position = Layout.his_point(Layout.DAZED_CHIN, body.global_position)


#THE KO

func _ko_snap() -> void:
	phase = Phase.KO_SNAP
	phase_clock = 0.0
	_play_clip(&"ko_snap")


func _ko_fall() -> void:
	if phase != Phase.KO_SNAP:
		return
	phase = Phase.KO_FALL
	phase_clock = 0.0
	_play_clip(&"ko_fall")


func _thud() -> void:
	phase = Phase.KO_DOWN
	phase_clock = 0.0
	ScreenView.shake(get_tree(), thud_shake, SHAKE_STEPS, SHAKE_STEP)
	body.play_sfx(&"slam", thud_pitch)
	state_machine.crowd(&"cheer", ko_cheer)


# On one frame: the view level, the player out of their lock and back on their own sheet in front of his boots,
# and him beaten, lying on the KO's last frame.
func _hand_off() -> void:
	ScreenView.reset(get_tree())
	framed = false
	var player := _player()
	if player != null:
		player.unlock_actions()
		player.global_position = Layout.PLAYER_HANDOFF
		_restore_player_z(player)
	state_machine.greyson_beaten(true)


#THE LOSS

# The lethal hit's frame: the boxing stops, the view comes level, and the player - already out of their lock, the
# hit's own doing - is put in front of his boots, while he goes back to his guard for his Victory.
func _lose() -> void:
	phase = Phase.LOST
	phase_clock = 0.0
	punch = {}
	combo = []
	ParryTell.clear(body)
	fx.clear()
	ScreenView.reset(get_tree())
	framed = false
	var player := _player()
	if player != null:
		player.global_position = Layout.PLAYER_HANDOFF
		_restore_player_z(player)
	_play_clip(&"guard")


#THE PLAYER

func _lock_player() -> void:
	var player := _player()
	if player == null:
		return
	player.lock_actions()
	if player.hold_pose(Layout.player_sheet()):
		_pose_player(&"guard")
	player.face_point(Layout.FACE_AT)
	if not player_z_saved:
		player_z = player.sprite.z_index
		player_z_saved = true
	player.sprite.z_index = Layout.PLAYER_Z
	_connect_player(player)


func _pose_player(pose_name: StringName) -> void:
	var player := _player()
	if player == null or not player.is_posed():
		return
	var pose: Dictionary = Layout.PLAYER_POSES[pose_name]
	player.play_pose(pose.frames, pose.times, pose.loop)


func _restore_player_z(player: Node2D) -> void:
	if not player_z_saved:
		return
	player_z_saved = false
	player.sprite.z_index = player_z


func _connect_player(player: Node2D) -> void:
	if player_ref == player:
		return
	_disconnect_player()
	player_ref = player
	player.finisher.finished.connect(_on_finisher_finished)
	player.defense.block_pressed.connect(_on_block_pressed)


func _disconnect_player() -> void:
	if is_instance_valid(player_ref):
		if player_ref.finisher.finished.is_connected(_on_finisher_finished):
			player_ref.finisher.finished.disconnect(_on_finisher_finished)
		if player_ref.defense.block_pressed.is_connected(_on_block_pressed):
			player_ref.defense.block_pressed.disconnect(_on_block_pressed)
	player_ref = null


func _frame_view(duration: float) -> void:
	framed = true
	if duration > 0.0:
		ScreenView.zoom_to(get_tree(), Layout.ZOOM, Layout.FOCUS, duration)
		return
	if ScreenView.zoom_tween:
		ScreenView.zoom_tween.kill()
	ScreenView.zoom = Layout.ZOOM
	ScreenView.focus = Layout.FOCUS
	ScreenView.apply(get_tree())


#HIS SPRITE

# One of GreysonBrawlLayout's clips, drawn on his sprite from its first step: his own animation halted, and his
# whole sheet put on.
func _play_clip(key: StringName) -> void:
	var spec := Layout.clip(key)
	clip_name = key
	clip = spec
	clip_step = 0
	clip_clock = 0.0
	clip_time = 0.0
	clip_done = false
	body.halt_anim()
	var sprite: Sprite2D = body.sprite
	var sheet: Texture2D = load(spec.texture)
	sprite.frame = 0
	sprite.texture = sheet
	sprite.vframes = 1
	sprite.hframes = maxi(roundi(sheet.get_width() / GreysonArt.FRAME_SIZE.x), 1)
	sprite.offset = GreysonArt.SPRITE_OFFSET
	sprite.flip_h = false
	sprite.rotation = 0.0
	_show_clip_step()


# His own animation back, this state's clip let go.
func _body_anim(anim_name: StringName) -> void:
	clip = {}
	body.show_body()
	body.play_anim(anim_name)


func _advance_clip(delta: float) -> void:
	if clip.is_empty():
		return
	clip_time += delta
	if clip.has("tilt"):
		var fall := clampf(clip_time / clip.tilt_time, 0.0, 1.0)
		body.sprite.rotation = deg_to_rad(clip.tilt) * fall * fall
	if clip_done:
		return
	clip_clock += delta
	var times: Array = clip.times
	while clip_clock >= times[mini(clip_step, times.size() - 1)]:
		clip_clock -= times[mini(clip_step, times.size() - 1)]
		if clip_step < clip.frames.size() - 1:
			clip_step += 1
		elif clip.loop:
			clip_step = 0
		else:
			var next: StringName = clip.get("next", &"")
			if next != &"":
				_play_clip(next)
			else:
				clip_done = true
			return
		_show_clip_step()


func _show_clip_step() -> void:
	var sprite: Sprite2D = body.sprite
	sprite.frame = clip.frames[clip_step]
	var shifts: Array = clip.get("shifts", [])
	var shift: Vector2 = shifts[mini(clip_step, shifts.size() - 1)] if not shifts.is_empty() else Vector2.ZERO
	sprite.position = body.sprite_base_position + shift * Layout.SCALE


func _stop_lingering() -> void:
	var juggled = state_machine.states.get("Juggled")
	if juggled != null and juggled.has_method("stop_lingering"):
		juggled.stop_lingering()


#WAITS AND PIECES

func _track(tween: Tween) -> Tween:
	waits.append(tween)
	tween.finished.connect(func() -> void: waits.erase(tween))
	return tween


func _start_beat() -> void:
	beat_started = body.fight_clock


func _end_beat(beat_name: StringName) -> void:
	beat_times[beat_name] = body.fight_clock - beat_started


func _live() -> bool:
	return not released and is_instance_valid(body) and state_machine.current_state == self


func _cut_live() -> bool:
	return _live() and not cut_skipped and phase == Phase.CUT


func _finisher_busy() -> bool:
	var player := _player()
	return player != null and player.finisher.is_active()


func _player() -> Node2D:
	return state_machine.get_player()
