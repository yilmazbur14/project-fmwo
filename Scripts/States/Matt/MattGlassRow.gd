extends State

# Matt's Attack 2, the Glass Row, and with cycle_deafen on, Attack 3: the Deafening Yell inside it.
# He teleports to the top of the ring over the lane, stamps the player to the floor and drags them into
# row F under him, and brings glass down on the last rows with a furious jig: two, three or four of them by
# his health (MattStateMachine.glass_rows_for). Then he roars sonic booms down the lane one at a time, each
# carrying an arrow: the first direction pressed while it is live decides it. Answered, it breaks on the
# braced player; failed, it knocks them a row nearer the glass. The knock that reaches the glass costs a
# whole heart, ends the barrage and bounces them back to the row in front of it; from row F that is the
# fourth over two rows of glass, the third over three and the second over four. Then he is winded, lets them
# go, and the window opens over them. In phase two the booms come in sets, and between each two he stomps
# again and brings more shards down onto the glass (G11).
#
# THE BEATS (seconds):
#   OUT 0.15, IN 0.15   he teleports to the station over the lane.
#   TELL    0.45        the stomp's knee comes up, the crowd hushes, the ring rumbles. The player is
#                       still free; if they are mid-finisher it holds here until they land.
#   SLAM    (one step)  sealed, posed, turned to face him, the root clamped on their feet (G1).
#   ROOT    0.15        the clamp.
#   DRAG    0.25 + 0.10 pulled into row F along a line, leaving lavender ghosts (Carter's yank).
#   FURY    1.40        he stamps; 18 shards fall from the ceiling onto the glass's bed, rows B and A, and
#                       9 onto each row of glass in front of it, their shadows first, and the glass is
#                       whole by the end of it.
#   [DEAFEN_TELL 0.50, DEAFEN 3.00, DEAFEN_AFTER 0.40: phase two only]
#   INHALE  0.35        the roar's breath in.
#   BOOMS               per boom: CHARGE at his mouth (sinking and growing), FLIGHT down the lane, the
#                       IMPACT step, a KNOCK on a fail (the glass's BOUNCE on the one that reaches it),
#                       then a GAP. In phase two a STOMP follows the last GAP of every set but the last:
#                       the knee up 0.20, the slam, and 0.65 of stamping while 9 shards fall onto the
#                       glass's front row, shadows first. It lays no glass.
#   WINDED  0.50        the player is let go on its first step, the glass clears and he is spent.
# Then Recover opens where he stands, straight over the player (recover_spot), glass_clean_bonus longer
# if nothing failed.
#
# THE ANSWER is a direction (DirectionPress): only the first one pressed between a boom's birth and its
# impact counts. Keys and the D-pad are read off input events, so a tap inside one frame still counts,
# and the events go on to everyone else; the stick is decided once a step, with both its axes in. The
# timing is the same whatever the answer; only what happens at the impact differs (G4).
#
# RELEASE: the lock, the pose, the facing, the floor, the boom, the root, the hint and the wobble all go
# back through release(), which Exit(), _exit_tree() and MattStateMachine._end_fight call (G7).
#
# FREEZE SAFETY: every wait is a Physics_Update accumulator or a node-bound tween.

const HitInfo := preload("res://Scripts/HitInfo.gd")
const HitStop := preload("res://Scripts/HitStop.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const MattArtLayout := preload("res://Scripts/MattArtLayout.gd")
const DirectionPress := preload("res://Scripts/DirectionPress.gd")
const BOOM_SCRIPT := preload("res://Scripts/MattBoomScript.gd")
const FLOOR_SCRIPT := preload("res://Scripts/MattGlassFloor.gd")
const RING_SCENE := preload("res://Scenes/Bosses/MattYellRingScene.tscn")
const MashInput := preload("res://Scripts/MashInput.gd")
const MashCurve := preload("res://Scripts/MashCurve.gd")
const FinisherPromptUI := preload("res://Scripts/FinisherPromptUI.gd")
const DefenseHypeArtLayout := preload("res://Scripts/DefenseHypeArtLayout.gd")
const UI_THEME := preload("res://Assets/UI/ui_theme.tres")

const GLASS_ID := &"matt_glass"
const DIRECTIONS: Array[StringName] = [&"up", &"right", &"down", &"left"]
const INHALE_TIME := 0.35
# Screen shakes: strength, steps and step seconds.
const TELL_RUMBLE := 3.0
const RUMBLE_STEP := 0.04
const SLAM_SHAKE_STEPS := 6
const SLAM_SHAKE_STEP := 0.04
const LAND_SHAKE := 8.0
const LAND_SHAKE_STEPS := 4
const FURY_SHAKE_STEPS := 2
const BOOM_FIRE_SHAKE := 4.0
const BOOM_FIRE_STEPS := 2
const BOOM_HIT_STEPS := 4
const GLASS_SHAKE_STEPS := 6
const GLASS_SHAKE_STEP := 0.04
const SHAKE_STEP := 0.03
const FURY_PITCH := 0.06
# The shards: their spawn times' jitter, their sideways drift as they fall, and how far inside its
# segment each lands.
const SHARD_JITTER := 0.02
const SHARD_DRIFT := 20.0
const SHARD_INSET := Vector2(16, 12)
# A phase-two stomp's last shard lands at least this long before its next boom is born.
const SPREAD_LAND_MARGIN := 0.05
const GHOST_STAGGER := 0.04
const ANSWER_CHEER := 0.4
const CLEAN_CHEER := 2.0
const HINT_WIDTH := 1200.0
# The Deafening Yell: its onset's shake, the rumble's, the mash's minimum gap between two presses that
# both count (real seconds, MashInput's rule) and the crowd for a player who mashed through it.
const DEAFEN_SHAKE := 10.0
const DEAFEN_SHAKE_STEPS := 4
const DEAFEN_SHAKE_STEP := 0.04
const DEAFEN_RUMBLE_STEPS := 3
const MASH_MIN_INTERVAL := 0.03
const RESIST_CHEER := 1.5

#WHAT FinisherPromptUI READS for the RESIST! mash: ComputahTrapped's surface. A tiered mash is the
# finisher's alone, so the last two are never emitted.
signal prompt_shown
signal meter_changed(meter: float, next_action: StringName)
signal charge_ended(filled: bool)
signal finished
signal tier_banked(tier: int)
signal juggle_hit(index: int, last: bool)

@export var body : CharacterBody2D

@onready var state_machine = get_parent()

enum Beat { OUT, IN, TELL, ROOT, DRAG, FURY, DEAFEN_TELL, DEAFEN, DEAFEN_AFTER, INHALE, BOOMS, WINDED }
enum BoomPhase { CHARGE, FLIGHT, KNOCK, BOUNCE, GAP, STOMP }

var beat := Beat.OUT
var beat_clock := 0.0
var boom_phase := BoomPhase.CHARGE
var boom_clock := 0.0
var boom_index := -1
var booms_total := 0
var arrows: Array[StringName] = []
# At each impact: &"answered", &"cracked" (a wrong press) or &"missed" (none).
var outcomes: Array[StringName] = []
# Each boom's arrow-shown-to-impact time, in game seconds.
var windows: Array[float] = []
var fails := 0
var row := 0
# The glass's first row, and whether the knock under way reaches it.
var glass_top := 0
var into_glass := false
# Phase two: how many booms have gone before each stomp, whether the stomp under way has slammed, and how
# many stomps there have been, for a test.
var stomp_after: Array[int] = []
var stomp_slammed := false
var stomps := 0
var glass_hit := false
var deafen_on := false
var deafen_passed := false
var dizzy := false
var meter := 0.0
var boom: Node2D
var glass_floor: Node2D
# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
var player_held := false
# The player's life ended in the glass: from then on the fight's end is what moves anyone.
var stopped := false

var press := DirectionPress.new()
# The live boom's first press, or empty.
var answer := &""
var state_clock := 0.0
var birth_clock := 0.0
var boom_y := 0.0
# The forming sound's length at its own pitch, read off its stream as the row starts.
var form_length := 0.0
var station := Vector2.ZERO
var drag_from := Vector2.ZERO
var drag_landed := false
var move_from := Vector2.ZERO
var move_to := Vector2.ZERO
var shard_plan: Array = []
var last_fury_step := -1
var root_fx: Node2D
var root_tween: Tween
var hint: Node2D
# When the hint went up, on state_clock, and how many booms had landed by then.
var hint_shown_at := 0.0
var hint_impacts := 0
# What it put in the ring that goes on its own - puffs, ghosts, a bursting boom, the root letting go, the
# hint fading - which release() takes if it is still there.
var loose: Array[Node] = []
# When the one-shot pose playing now hands back to the base loop, on state_clock; -1 for none.
var pose_back_at := -1.0
var wobble_fading := false
# What the player's pose falls back to between one-shots: rooted, the ears through the yell, the resist
# once they have mashed through it, dizzy after a failed mash.
var base_pose := &"rooted"

#THE MASH
var tiered := false
var prompt_key := &"resist"
# The finisher's own pair (the arrows or the shoulder buttons on the reworked feel), read as the Glass Row
# starts and kept for it.
var pair: Array[StringName] = []
var last_action := &""
var last_press_usec := 0
# Built the first time and kept, on his HUD layer.
var prompt: Node2D
var charge_owed := false
var finish_owed := false
var rumble_clock := 0.0
var ring_clock := 0.0
var stars: Sprite2D
var stars_clock := 0.0


func Enter() -> void:
	released = false
	player_held = false
	stopped = false
	state_machine.glass_rows_done += 1
	station = state_machine.GLASS_ROW.station
	deafen_on = state_machine.cycle_deafen
	booms_total = state_machine.cycle_booms
	arrows = _roll_arrows(booms_total)
	var form: Dictionary = MattArtLayout.SFX[&"boom_form"]
	form_length = (load(form.stream) as AudioStream).get_length() / form.pitch
	outcomes.clear()
	windows.clear()
	fails = 0
	row = state_machine.GLASS_ROW.start_row
	glass_top = state_machine.glass_top_row()
	into_glass = false
	stomp_after.clear()
	var sets: int = maxi(state_machine.cycle_sets, 1)
	for k in range(1, sets):
		stomp_after.append(roundi(float(booms_total) * k / sets))
	stomps = 0
	glass_hit = false
	deafen_passed = false
	dizzy = false
	meter = 0.0
	boom_index = -1
	answer = &""
	state_clock = 0.0
	last_fury_step = -1
	shard_plan.clear()
	pose_back_at = -1.0
	wobble_fading = false
	base_pose = &"rooted"
	press = DirectionPress.new()
	last_action = &""
	last_press_usec = 0
	charge_owed = false
	finish_owed = false
	_read_pair()
	body.velocity = Vector2.ZERO
	body.set_hurtbox_active(false)
	body.show_body()
	_begin(Beat.OUT)
	body.teleport_out()


func Exit() -> void:
	release()


func _exit_tree() -> void:
	release()


# Idempotent: whichever way the Glass Row ends, the player is let go and everything it put in the ring
# goes. A floor already clearing is left to finish, and a wobble already fading out to fade.
func release() -> void:
	if released:
		return
	released = true
	_release_player()
	if is_instance_valid(boom):
		boom.queue_free()
	boom = null
	if is_instance_valid(glass_floor) and not glass_floor.clearing:
		glass_floor.queue_free()
	glass_floor = null
	if is_instance_valid(root_fx):
		root_fx.queue_free()
	root_fx = null
	if is_instance_valid(hint):
		hint.queue_free()
	hint = null
	for node in loose:
		if is_instance_valid(node):
			node.queue_free()
	loose.clear()
	_clear_stars()
	if charge_owed:
		charge_owed = false
		charge_ended.emit(false)
	if finish_owed:
		finish_owed = false
		finished.emit()
	if is_instance_valid(body):
		body.stop_sfx(&"deafen_yell")
		body.stop_sfx(&"ear_ring")
		if not wobble_fading:
			body.clear_wobble()


func _release_player() -> void:
	if not player_held:
		return
	player_held = false
	state_machine.end_player_pose()
	state_machine.pose_player(false)
	state_machine.unlock_player()
	state_machine.clear_player_facing()


func _input(event: InputEvent) -> void:
	if released:
		return
	if beat == Beat.DEAFEN and not deafen_passed:
		for action in pair:
			if event.is_action_pressed(action):
				_mash(action)
				break
	_answer(press.read(event))


# The live boom's answer, if it hasn't one yet: presses outside a live boom do nothing (G3).
func _answer(direction: StringName) -> void:
	if direction == &"" or beat != Beat.BOOMS or boom == null or answer != &"":
		return
	if boom_phase != BoomPhase.CHARGE and boom_phase != BoomPhase.FLIGHT:
		return
	answer = direction
	if direction == arrows[boom_index]:
		boom.mark(&"answered")
		body.play_sfx(&"boom_answer")
		state_machine.add_player_hype(state_machine.boom_hype_each)
		get_tree().call_group("arena_crowd", "cheer", ANSWER_CHEER)
	else:
		boom.mark(&"cracked")
		body.play_sfx(&"boom_wrong")


func Physics_Update(delta: float) -> void:
	if released or stopped:
		return
	beat_clock += delta
	state_clock += delta
	_answer(press.poll())
	_follow_root()
	_follow_stars(delta)
	_hand_back_pose()
	match beat:
		Beat.OUT:
			if beat_clock >= state_machine.teleport_out:
				_begin(Beat.IN)
				body.teleport_in(station)
				body.update_hud_fade(&"stomp_tell")
		Beat.IN:
			if beat_clock >= state_machine.teleport_in:
				_begin_tell()
		Beat.TELL:
			if beat_clock >= state_machine.glass_stomp_tell and not _player_finishing():
				_slam()
		Beat.ROOT:
			if beat_clock >= state_machine.glass_root_time:
				_begin_drag()
		Beat.DRAG:
			_drive_drag()
		Beat.FURY:
			_run_fury()
		Beat.DEAFEN_TELL:
			if beat_clock >= state_machine.deafen_tell:
				_begin_deafen()
		Beat.DEAFEN:
			_run_deafen(delta)
		Beat.DEAFEN_AFTER:
			if beat_clock >= state_machine.deafen_after:
				_begin_inhale()
		Beat.INHALE:
			if beat_clock >= INHALE_TIME:
				_begin_booms()
		Beat.BOOMS:
			_run_booms(delta)
		Beat.WINDED:
			if beat_clock >= state_machine.glass_winded:
				_end_winded()
	# After the booms have stepped, so the hint goes on the step its last boom lands.
	_keep_hint()


func _begin(next: Beat) -> void:
	beat = next
	beat_clock = 0.0


# Uniform over the four, re-rolling any that would make three of the same in a row.
func _roll_arrows(count: int) -> Array[StringName]:
	var out: Array[StringName] = []
	while out.size() < count:
		var pick: StringName = DIRECTIONS[state_machine.rng.randi_range(0, DIRECTIONS.size() - 1)]
		var n := out.size()
		if n >= 2 and out[n - 1] == pick and out[n - 2] == pick:
			continue
		out.append(pick)
	return out


#THE STOMP, THE ROOT AND THE DRAG

func _begin_tell() -> void:
	_begin(Beat.TELL)
	body.play_anim(&"stomp_tell")
	get_tree().call_group("arena_crowd", "hush")
	ScreenView.shake(get_tree(), TELL_RUMBLE, ceili(state_machine.glass_stomp_tell / RUMBLE_STEP), RUMBLE_STEP)


# G1: the lock lands on this step and no earlier.
func _slam() -> void:
	_begin(Beat.ROOT)
	state_machine.seal_player()
	state_machine.pose_player(true)
	state_machine.face_player_at(body.mouth_point(&"roar"))
	player_held = true
	body.play_anim(&"stomp_slam")
	ScreenView.shake(get_tree(), state_machine.stomp_shake, SLAM_SHAKE_STEPS, SLAM_SHAKE_STEP)
	_puff(&"stomp_dust", _foot_point(&"stomp_slam", 0))
	_build_root()
	body.play_sfx(&"stomp")
	body.play_sfx(&"root_clamp")


func _begin_drag() -> void:
	_begin(Beat.DRAG)
	drag_landed = false
	var player: Node2D = state_machine.get_player()
	drag_from = player.global_position if is_instance_valid(player) else state_machine.row_body_point(row)
	_spawn_drag_ghosts()


# Driven along a straight line with an ease-in, like Carter's yank; the locked player's own physics never
# moves them, so writing the position is what carries them.
func _drive_drag() -> void:
	var to: Vector2 = state_machine.row_body_point(row)
	var weight := clampf(beat_clock / maxf(state_machine.glass_drag_time, 0.0001), 0.0, 1.0)
	_put_player(drag_from.lerp(to, weight * weight).round())
	if not drag_landed and weight >= 1.0:
		drag_landed = true
		ScreenView.shake(get_tree(), LAND_SHAKE, LAND_SHAKE_STEPS, SHAKE_STEP)
		_puff(&"stomp_dust", to + Vector2(0, state_machine.BODY_OVER_FEET))
		state_machine.hold_player_pose(MattArtLayout.player_poses())
		_play_base_pose()
	if beat_clock >= state_machine.glass_drag_time + state_machine.glass_drag_hold:
		_begin_fury()


func _spawn_drag_ghosts() -> void:
	var player: Node2D = state_machine.get_player()
	if not is_instance_valid(player):
		return
	var to: Vector2 = state_machine.row_body_point(row)
	var count := MattArtLayout.DRAG_GHOSTS
	for i in count:
		var ghost := Sprite2D.new()
		ghost.texture = player.sprite.texture
		ghost.hframes = player.sprite.hframes
		ghost.vframes = player.sprite.vframes
		ghost.frame = player.sprite.frame
		ghost.scale = player.sprite.global_scale
		ghost.modulate = MattArtLayout.DRAG_GHOST_TINT
		state_machine.add_hazard(ghost, drag_from.lerp(to, float(i) / count), body.floor_layer)
		loose.append(ghost)
		var fade := ghost.create_tween()
		fade.tween_interval(i * GHOST_STAGGER)
		fade.tween_property(ghost, "modulate:a", 0.0, MattArtLayout.DRAG_GHOST_FADE)
		fade.tween_callback(ghost.queue_free)


#THE FURY AND THE GLASS

func _begin_fury() -> void:
	_begin(Beat.FURY)
	body.play_anim(&"fury")
	last_fury_step = -1
	glass_floor = FLOOR_SCRIPT.new()
	glass_floor.name = "GlassFloor"
	state_machine.add_hazard(glass_floor, Vector2.ZERO, body.floor_layer)
	var bed_top: int = state_machine.bed_top_row()
	glass_floor.build(state_machine.rows_band(bed_top), state_machine.glass_segments, body.projectile_layer, body,
		state_machine.HAZARD_GROUP)
	var bed: Array = glass_floor.segment_rects().duplicate()
	# Glass past the bed grows on in front of it at once, a row at a time, each with its own edge: a bed drawn
	# taller would show its tile's edge again inside it. Each of those rows gets a stomp's shards.
	var grown: Array = []
	for k in range(bed_top - 1, glass_top - 1, -1):
		grown.append_array(glass_floor.grow(state_machine.row_band(k), state_machine.glass_segments))
	glass_floor.show_guides(true, MattArtLayout.GLASS_GUIDES.show_time, state_machine.GLASS_ROW, station.y,
		state_machine.ROPES)
	shard_plan = _plan_shards(bed, state_machine.glass_shards_per_segment, state_machine.glass_shard_spawn,
		state_machine.glass_fury_time)
	if not grown.is_empty():
		shard_plan.append_array(_plan_shards(grown, state_machine.glass_spread_shards_per_segment,
			state_machine.glass_shard_spawn, state_machine.glass_fury_time))
		shard_plan.sort_custom(func(a, b): return a.t < b.t)


# `per_segment` shards on each of `rects`, the order shuffled, spread evenly over the `span` shares of
# `over` seconds with a little jitter, each landing somewhere in its segment clear of its edges. All of it
# off the fight's seeded rng.
func _plan_shards(rects: Array, per_segment: int, span: Vector2, over: float) -> Array:
	var order: Array = []
	for i in rects.size():
		for n in per_segment:
			order.append(i)
	for i in range(order.size() - 1, 0, -1):
		var j: int = state_machine.rng.randi_range(0, i)
		var held = order[i]
		order[i] = order[j]
		order[j] = held
	var plan := []
	for k in order.size():
		var share := lerpf(span.x, span.y, float(k) / maxf(order.size() - 1, 1))
		var rect: Rect2 = rects[order[k]]
		var inside := rect.grow_individual(-SHARD_INSET.x, -SHARD_INSET.y, -SHARD_INSET.x, -SHARD_INSET.y)
		plan.append({
			"t": share * over + state_machine.rng.randf_range(-SHARD_JITTER, SHARD_JITTER),
			"land": Vector2(state_machine.rng.randf_range(inside.position.x, inside.end.x),
				state_machine.rng.randf_range(inside.position.y, inside.end.y)),
			"drift": state_machine.rng.randf_range(-SHARD_DRIFT, SHARD_DRIFT),
			"shape": state_machine.rng.randi_range(0, 3),
		})
	plan.sort_custom(func(a, b): return a.t < b.t)
	return plan


func _run_fury() -> void:
	while not shard_plan.is_empty() and shard_plan[0].t <= beat_clock:
		var shard: Dictionary = shard_plan.pop_front()
		glass_floor.drop_shard(shard.land, state_machine.glass_shard_fall, shard.drift, shard.shape)
		body.play_sfx(&"glass_fall")
	_stamp()
	if beat_clock >= state_machine.glass_fury_time:
		glass_floor.reveal_all()
		if deafen_on:
			_begin_deafen_tell()
		else:
			_begin_inhale()


# Each of the fury's slam steps: a shake, a stamp and a puff at that foot.
func _stamp() -> void:
	if body.current_anim != &"fury" or body.anim_step == last_fury_step:
		return
	last_fury_step = body.anim_step
	if not MattArtLayout.slam_feet(&"fury").has(last_fury_step):
		return
	ScreenView.shake(get_tree(), state_machine.fury_shake, FURY_SHAKE_STEPS, SHAKE_STEP)
	body.play_sfx(&"fury_stomp", 1.0 + randf_range(-FURY_PITCH, FURY_PITCH))
	_puff(&"fury_puff", _foot_point(&"fury", last_fury_step))


func _begin_inhale() -> void:
	_begin(Beat.INHALE)
	body.play_anim(&"roar_inhale")
	body.play_sfx(&"roar_inhale")


#THE DEAFENING YELL (phase two: the glass is down, the booms not yet started)

func _begin_deafen_tell() -> void:
	_begin(Beat.DEAFEN_TELL)
	body.play_anim(&"yell_up_tell")
	body.play_sfx(&"deafen_tell")
	get_tree().call_group("arena_crowd", "hush")


# He yells at the ceiling for deafen_time whatever happens; the RESIST! prompt is up and presses count
# from this step.
func _begin_deafen() -> void:
	_begin(Beat.DEAFEN)
	body.play_anim(&"yell_up")
	body.play_sfx(&"deafen_yell")
	ScreenView.shake(get_tree(), DEAFEN_SHAKE, DEAFEN_SHAKE_STEPS, DEAFEN_SHAKE_STEP)
	rumble_clock = 0.0
	ring_clock = 0.0
	_yell_ring()
	base_pose = &"ears"
	_play_pose(&"ears_in")
	meter = 0.0
	last_action = &""
	last_press_usec = 0
	_build_prompt()
	charge_owed = true
	finish_owed = true
	prompt_shown.emit()


func _run_deafen(delta: float) -> void:
	if not deafen_passed:
		meter = maxf(meter - MashCurve.drain(state_machine.deafen_drain, meter) * delta, 0.0)
	rumble_clock += delta
	if rumble_clock >= state_machine.deafen_rumble_step:
		rumble_clock -= state_machine.deafen_rumble_step
		ScreenView.shake(get_tree(), state_machine.deafen_rumble, DEAFEN_RUMBLE_STEPS, DEAFEN_SHAKE_STEP)
	ring_clock += delta
	if ring_clock >= state_machine.deafen_ring_every:
		ring_clock -= state_machine.deafen_ring_every
		_yell_ring()
	if beat_clock >= state_machine.deafen_time:
		_begin_deafen_after()


func _begin_deafen_after() -> void:
	_begin(Beat.DEAFEN_AFTER)
	if charge_owed:
		charge_owed = false
		charge_ended.emit(false)
	if deafen_passed:
		body.show_talk(&"irritated", false)
		base_pose = &"rooted"
		_play_pose(&"resist")
		body.play_sfx(&"resist")
		get_tree().call_group("arena_crowd", "cheer", RESIST_CHEER)
		_ring_pop()
		return
	body.show_talk(&"laugh", true)
	dizzy = true
	base_pose = &"dizzy"
	_play_base_pose()
	_show_stars()
	body.play_sfx(&"ear_ring")
	body.set_wobble(1.0, state_machine.wobble_in)


func mash_actions() -> Array[StringName]:
	return pair


func _read_pair() -> void:
	var player: Node2D = state_machine.get_player()
	if player and player.get("finisher"):
		pair = player.finisher.mash_actions()


# PlayerFinisher's rule through MashInput: the other key of the pair, and not twice in one flush.
func _mash(action: StringName) -> void:
	var now := Time.get_ticks_usec()
	if not MashInput.counts(action, last_action, now, last_press_usec, MASH_MIN_INTERVAL):
		return
	last_action = action
	last_press_usec = now
	meter = minf(meter + MashCurve.gain(state_machine.deafen_gain, meter), 1.0)
	meter_changed.emit(meter, pair[1] if action == pair[0] else pair[0])
	if meter >= 1.0:
		_resist()


# Mashed through it: FULL! at once and the player stands up to it, though he yells on to the end.
func _resist() -> void:
	deafen_passed = true
	if charge_owed:
		charge_owed = false
		charge_ended.emit(true)
	base_pose = &"resist"
	_play_pose(&"resist")


func _build_prompt() -> void:
	var player: Node2D = state_machine.get_player()
	if is_instance_valid(prompt) or player == null or body.hud_layer == null or pair.size() != 2:
		return
	var ui: Node2D = FinisherPromptUI.new()
	ui.name = "ResistPrompt"
	ui.finisher = self
	ui.player = player
	body.hud_layer.add_child(ui)
	prompt = ui


# A ring of sound off his mouth, straight up at the ceiling, that hurts nobody.
func _yell_ring() -> void:
	var ring: Node2D = RING_SCENE.instantiate()
	ring.player = null
	ring.start_radius = state_machine.yell_start_radius
	ring.end_radius = state_machine.yell_radius
	ring.band = state_machine.yell_band
	ring.expand_time = state_machine.yell_expand_time
	ring.landing_time = state_machine.yell_landing_time
	state_machine.add_hazard(ring, body.mouth_point(&"yell_up"), body.projectile_layer)
	loose.append(ring)


func _ring_pop() -> void:
	var spec := MattArtLayout.RESIST_RING
	var ring := Line2D.new()
	ring.points = MattArtLayout.circle(spec.from_radius, spec.points)
	ring.closed = true
	ring.width = spec.width
	ring.default_color = spec.color
	state_machine.add_hazard(ring, _player_point(), body.projectile_layer)
	loose.append(ring)
	var grow := ring.create_tween().set_parallel()
	grow.tween_property(ring, "scale", Vector2.ONE * (spec.to_radius / spec.from_radius), spec.time)
	grow.tween_property(ring, "modulate:a", 0.0, spec.time)
	grow.chain().tween_callback(ring.queue_free)


# The guard break's own stars, circling over the dizzy player's head until he lets go of them.
func _show_stars() -> void:
	var spec := DefenseHypeArtLayout.guard_break_stars()
	stars = Sprite2D.new()
	stars.name = "DizzyStars"
	stars.texture = load(spec.texture)
	stars.hframes = spec.hframes
	stars.centered = false
	stars.offset = -spec.pivot
	stars.scale = Vector2.ONE * spec.scale
	stars_clock = 0.0
	state_machine.add_hazard(stars, _player_point() + spec.offset, body.projectile_layer)


func _follow_stars(delta: float) -> void:
	if not is_instance_valid(stars):
		return
	var spec := DefenseHypeArtLayout.guard_break_stars()
	stars_clock += delta
	stars.frame = int(stars_clock / spec.frame_time) % stars.hframes
	stars.global_position = (_player_point() + spec.offset).round()


func _clear_stars() -> void:
	if is_instance_valid(stars):
		stars.queue_free()
	stars = null


#THE BOOMS

func _begin_booms() -> void:
	_begin(Beat.BOOMS)
	if finish_owed:
		finish_owed = false
		finished.emit()
	boom_index = -1
	_next_boom()


func _next_boom() -> void:
	boom_index += 1
	if boom_index >= booms_total:
		_begin_winded()
		return
	boom_phase = BoomPhase.CHARGE
	boom_clock = 0.0
	answer = &""
	birth_clock = state_clock
	boom = BOOM_SCRIPT.new()
	boom.name = "Boom%d" % boom_index
	state_machine.add_hazard(boom, _boom_spawn(), body.projectile_layer)
	boom.setup(arrows[boom_index])
	# Sped up to end as the boom fires: it was cut for a charge longer than today's. A charge too short for
	# that within BOOM_FORM_MAX_PITCH cuts it at the fire instead (_fire_boom).
	body.play_sfx(&"boom_form", clampf(form_length / _charge_time(), 1.0, MattArtLayout.BOOM_FORM_MAX_PITCH))
	body.play_anim(&"roar")
	if not state_machine.glass_hint_shown:
		state_machine.glass_hint_shown = true
		_show_hint()


func _run_booms(delta: float) -> void:
	boom_clock += delta
	match boom_phase:
		BoomPhase.CHARGE:
			var charge := _charge_time()
			var progress := clampf(boom_clock / charge, 0.0, 1.0)
			var sink := 1.0 - (1.0 - progress) * (1.0 - progress)
			boom.global_position = (_boom_spawn() + Vector2(0, state_machine.boom_charge_drift * sink)).round()
			boom.set_charge(progress)
			if boom_clock >= charge:
				_fire_boom()
		BoomPhase.FLIGHT:
			boom_y += state_machine.boom_speed * delta
			boom.global_position = Vector2(boom.global_position.x, roundf(boom_y))
			if boom_y >= _player_centre().y:
				_impact()
		BoomPhase.KNOCK:
			if _move_player(state_machine.boom_knock_time):
				if into_glass:
					_hit_glass()
				else:
					_begin_gap()
		BoomPhase.BOUNCE:
			# The barrage ends here: the booms still to come are never born.
			if _move_player(state_machine.glass_bounce_time):
				_begin_winded()
		BoomPhase.GAP:
			if boom_clock >= state_machine.boom_gap:
				if stomp_after.has(boom_index + 1):
					_begin_spread()
				else:
					_next_boom()
		BoomPhase.STOMP:
			_run_spread()


func _charge_time() -> float:
	var charge: float = state_machine.boom_charge_wobble if dizzy else state_machine.boom_charge
	return charge + state_machine.cycle_boom_charge_extra


func _boom_spawn() -> Vector2:
	return body.mouth_point(&"roar") + Vector2(0, state_machine.boom_spawn_drop)


func _fire_boom() -> void:
	boom_phase = BoomPhase.FLIGHT
	boom_clock = 0.0
	boom_y = boom.global_position.y
	boom.fly()
	body.stop_sfx(&"boom_form")
	body.play_sfx(&"boom_fire")
	ScreenView.shake(get_tree(), BOOM_FIRE_SHAKE, BOOM_FIRE_STEPS, SHAKE_STEP, Vector2.DOWN)


# The step its apex reaches the player's hurtbox centre: the answer given by now is the answer.
func _impact() -> void:
	windows.append(state_clock - birth_clock)
	boom.global_position = Vector2(boom.global_position.x, roundf(_player_centre().y))
	if answer == arrows[boom_index]:
		outcomes.append(&"answered")
		boom.burst(true)
		loose.append(boom)
		boom = null
		body.play_sfx(&"boom_block")
		_play_pose(&"brace")
		_begin_gap()
		return
	outcomes.append(&"cracked" if answer != &"" else &"missed")
	boom.burst(false)
	loose.append(boom)
	boom = null
	body.play_sfx(&"boom_hit")
	ScreenView.shake(get_tree(), state_machine.boom_hit_shake, BOOM_HIT_STEPS, SHAKE_STEP, Vector2.DOWN)
	fails += 1
	boom_phase = BoomPhase.KNOCK
	boom_clock = 0.0
	move_from = _player_point()
	into_glass = row + 1 >= glass_top
	if into_glass:
		move_to = _glass_point()
	else:
		row += 1
		move_to = state_machine.row_body_point(row)
	_play_pose(&"knock")


func _begin_gap() -> void:
	boom_phase = BoomPhase.GAP
	boom_clock = 0.0


#PHASE TWO'S STOMPS (G11)

# Between two sets: the knee comes up again and the ring rumbles. The hint was the first set's alone.
func _begin_spread() -> void:
	boom_phase = BoomPhase.STOMP
	boom_clock = 0.0
	stomp_slammed = false
	_hide_hint()
	body.play_anim(&"stomp_tell")
	ScreenView.shake(get_tree(), TELL_RUMBLE, ceili(state_machine.glass_spread_tell / RUMBLE_STEP), RUMBLE_STEP)


func _run_spread() -> void:
	if not stomp_slammed:
		if boom_clock >= state_machine.glass_spread_tell:
			_spread_slam()
		return
	if body.current_anim == &"stomp_slam" and boom_clock >= state_machine.glass_spread_slam:
		body.play_anim(&"fury")
		last_fury_step = -1
	while not shard_plan.is_empty() and shard_plan[0].t <= boom_clock:
		var shard: Dictionary = shard_plan.pop_front()
		glass_floor.drop_shard(shard.land, state_machine.glass_shard_fall, shard.drift, shard.shape)
		body.play_sfx(&"glass_fall")
	_stamp()
	if boom_clock >= state_machine.glass_spread_time:
		_next_boom()


# The slam, and more shards on their way down onto the glass's front row, their shadows first. It lays no
# glass (the user, 2026-09-27): his fury laid all of it, so nothing moves the player.
func _spread_slam() -> void:
	stomp_slammed = true
	stomps += 1
	boom_clock = 0.0
	body.play_anim(&"stomp_slam")
	body.play_sfx(&"stomp")
	ScreenView.shake(get_tree(), state_machine.stomp_shake, SLAM_SHAKE_STEPS, SLAM_SHAKE_STEP)
	_puff(&"stomp_dust", _foot_point(&"stomp_slam", 0))
	var front: float = state_machine.row_band(glass_top).position.y
	var rects: Array = glass_floor.segment_rects().filter(func(r: Rect2) -> bool: return is_equal_approx(r.position.y, front))
	var fall_by := maxf(state_machine.glass_spread_time - state_machine.glass_shard_fall - SPREAD_LAND_MARGIN, 0.0)
	shard_plan = _plan_shards(rects, state_machine.glass_spread_shards_per_segment, Vector2(0.0, 1.0), fall_by)


# Over `time` from move_from to move_to, ease-out, in whole px; whether it has got there.
func _move_player(time: float) -> bool:
	var t := clampf(boom_clock / maxf(time, 0.0001), 0.0, 1.0)
	var eased := 1.0 - (1.0 - t) * (1.0 - t)
	_put_player(move_from.lerp(move_to, eased).round())
	return t >= 1.0


# The glass's edge, wherever phase two has grown it to, plus the overshoot, for the soles: the body stands
# BODY_OVER_FEET above that.
func _glass_point() -> Vector2:
	var edge: float = state_machine.row_band(glass_top).position.y + state_machine.glass_edge_overshoot
	return Vector2(state_machine.GLASS_ROW.lane_x, edge - state_machine.BODY_OVER_FEET)


# G5: the knock that reaches the glass. Two damage once, inside the i-frames, and unless it killed them,
# back to the row in front of it.
func _hit_glass() -> void:
	glass_hit = true
	var feet := move_to + Vector2(0, state_machine.BODY_OVER_FEET)
	HitStop.freeze(get_tree(), state_machine.glass_hit_stop)
	ScreenView.shake(get_tree(), state_machine.glass_shake, GLASS_SHAKE_STEPS, GLASS_SHAKE_STEP)
	if is_instance_valid(glass_floor):
		glass_floor.shatter_at(feet)
	body.play_sfx(&"glass_shatter")
	var player: Node2D = state_machine.get_player()
	if is_instance_valid(player):
		player.receive_hit(HitInfo.make(GLASS_ID, glass_floor, feet, body))
	_play_pose(&"glass")
	if not is_instance_valid(player) or player.playerHealth <= 0:
		# PlayerScript unlocks them at 0, which ends the pose, and the fight's end releases the rest.
		stopped = true
		return
	row = glass_top - 1
	boom_phase = BoomPhase.BOUNCE
	boom_clock = 0.0
	move_from = move_to
	move_to = state_machine.row_body_point(row)


#WINDED, AND THE HAND-OVER

func _begin_winded() -> void:
	_begin(Beat.WINDED)
	_release_player()
	if is_instance_valid(glass_floor):
		glass_floor.clear(state_machine.glass_clear_time)
	_unroot()
	_hide_hint()
	_clear_stars()
	wobble_fading = true
	body.set_wobble(0.0, state_machine.wobble_out)
	body.play_anim(&"spent")
	body.set_hurtbox_active(false)


func _end_winded() -> void:
	state_machine.recover_spot = station
	if fails == 0 and not glass_hit:
		state_machine.recover_bonus = state_machine.glass_clean_bonus
		state_machine.add_player_hype(state_machine.boom_hype_clean)
		get_tree().call_group("arena_crowd", "cheer", CLEAN_CHEER)
	body.update_hud_fade(&"recover")
	state_machine.on_child_transition(self, "Recover")


#THE PLAYER

func _player_point() -> Vector2:
	var player: Node2D = state_machine.get_player()
	return player.global_position if is_instance_valid(player) else state_machine.row_body_point(row)


func _player_centre() -> Vector2:
	var player: Node2D = state_machine.get_player()
	if not is_instance_valid(player):
		return state_machine.row_body_point(row)
	return player.hurtBox.get_node("CollisionShape2D").global_position


func _put_player(point: Vector2) -> void:
	var player: Node2D = state_machine.get_player()
	if is_instance_valid(player):
		player.global_position = point


func _player_finishing() -> bool:
	var player: Node2D = state_machine.get_player()
	return is_instance_valid(player) and player.is_finishing


func _player_feet() -> Vector2:
	return _player_point() + Vector2(0, state_machine.BODY_OVER_FEET)


# A pose off MattArtLayout's set; a one-shot hands back to the base loop when it has played.
func _play_pose(pose: StringName) -> void:
	var spec := MattArtLayout.player_pose(pose)
	state_machine.play_player_pose(spec.frames, spec.times, spec.loop)
	pose_back_at = -1.0 if spec.loop else state_clock + _pose_length(spec)


func _play_base_pose() -> void:
	_play_pose(base_pose)


func _hand_back_pose() -> void:
	if pose_back_at >= 0.0 and state_clock >= pose_back_at and player_held:
		_play_base_pose()


func _pose_length(spec: Dictionary) -> float:
	var times: Array = spec.times
	var total := 0.0
	for i in spec.frames.size():
		total += float(times[mini(i, times.size() - 1)])
	return total


#WHAT IS DRAWN

func _foot_point(anim_name: StringName, step: int) -> Vector2:
	var feet := MattArtLayout.slam_feet(anim_name)
	var texel: Vector2 = feet.get(step, MattArtLayout.ANCHOR)
	return body.global_position + MattArtLayout.texel_local(texel, body.sprite.flip_h)


# The shackle on the player's feet: it clamps shut on the slam and follows them until they go.
func _build_root() -> void:
	var spec := MattArtLayout.fx(&"root")
	if MattArtLayout.uses_final_fx(&"root"):
		var sheet := Sprite2D.new()
		sheet.texture = load(spec.texture)
		sheet.hframes = spec.hframes
		sheet.scale = Vector2.ONE * MattArtLayout.SCALE
		sheet.offset = spec.offset
		root_fx = sheet
		root_tween = sheet.create_tween()
		for f in spec.clamp_frames:
			root_tween.tween_callback(sheet.set_frame.bind(f))
			root_tween.tween_interval(spec.clamp_time)
		root_tween.tween_callback(_loop_root.bind(sheet))
	else:
		var ring := Line2D.new()
		ring.points = MattArtLayout.ellipse(spec.radii, spec.points)
		ring.closed = true
		ring.width = spec.width
		ring.default_color = spec.color
		ring.scale = Vector2.ONE * 1.6
		root_fx = ring
		root_tween = ring.create_tween()
		root_tween.tween_property(ring, "scale", Vector2.ONE, spec.clamp_time)
	state_machine.add_hazard(root_fx, _player_feet(), body.floor_layer)


func _loop_root(sheet: Sprite2D) -> void:
	var spec := MattArtLayout.fx(&"root")
	var frames: Array = spec.loop_frames
	root_tween = sheet.create_tween().set_loops()
	for f in frames:
		root_tween.tween_callback(sheet.set_frame.bind(f))
		root_tween.tween_interval(spec.loop_time)


func _follow_root() -> void:
	if is_instance_valid(root_fx) and player_held:
		root_fx.global_position = _player_feet().round()


# The clamp opens - the drawn one's frames backwards - and it goes.
func _unroot() -> void:
	if not is_instance_valid(root_fx):
		return
	var fx := root_fx
	root_fx = null
	loose.append(fx)
	var spec := MattArtLayout.fx(&"root")
	if root_tween:
		root_tween.kill()
	root_tween = null
	var open := fx.create_tween()
	if fx is Sprite2D:
		var frames: Array = spec.clamp_frames.duplicate()
		frames.reverse()
		for f in frames:
			open.tween_callback((fx as Sprite2D).set_frame.bind(f))
			open.tween_interval(spec.clamp_time)
	else:
		open.set_parallel()
		open.tween_property(fx, "scale", Vector2.ONE * 1.6, spec.clamp_time)
		open.tween_property(fx, "modulate:a", 0.0, spec.clamp_time)
		open.chain()
	open.tween_callback(fx.queue_free)


# A one-shot puff on the floor: the drawn sheet's frames, or a stand-in ellipse that grows and fades.
func _puff(key: StringName, at: Vector2) -> void:
	var spec := MattArtLayout.fx(key)
	var puff: Node2D
	var play: Tween
	if MattArtLayout.uses_final_fx(key):
		var sheet := Sprite2D.new()
		sheet.texture = load(spec.texture)
		sheet.hframes = spec.hframes
		sheet.scale = Vector2.ONE * MattArtLayout.SCALE
		sheet.offset = spec.offset
		puff = sheet
		state_machine.add_hazard(puff, at, body.floor_layer)
		play = sheet.create_tween()
		for f in range(1, spec.hframes):
			play.tween_interval(spec.frame_time)
			play.tween_callback(sheet.set_frame.bind(f))
		play.tween_interval(spec.frame_time)
	else:
		var shape := Polygon2D.new()
		shape.polygon = MattArtLayout.ellipse(spec.radii, spec.points)
		shape.color = spec.color
		shape.scale = Vector2.ONE * spec.from_scale
		puff = shape
		state_machine.add_hazard(puff, at, body.floor_layer)
		play = shape.create_tween().set_parallel()
		play.tween_property(shape, "scale", Vector2.ONE * spec.to_scale, spec.time)
		play.tween_property(shape, "modulate:a", 0.0, spec.time)
		play.chain()
	play.tween_callback(puff.queue_free)
	loose.append(puff)


# Under the player, from the fight's first boom only.
func _show_hint() -> void:
	var spec := MattArtLayout.GLASS_HINT
	hint_shown_at = state_clock
	hint_impacts = outcomes.size()
	hint = Node2D.new()
	hint.name = "GlassHint"
	var label := Label.new()
	label.theme = UI_THEME
	label.text = spec.text
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.add_theme_font_size_override("font_size", spec.font_size)
	label.add_theme_constant_override("outline_size", spec.outline)
	label.add_theme_color_override("font_color", spec.color)
	label.add_theme_color_override("font_outline_color", spec.outline_color)
	label.size = Vector2(HINT_WIDTH, spec.font_size * 2)
	label.position = Vector2(-HINT_WIDTH / 2.0, 0)
	hint.add_child(label)
	hint.modulate.a = 0.0
	state_machine.add_hazard(hint, _player_point() + spec.offset, body.projectile_layer)
	var fade := hint.create_tween()
	fade.tween_property(hint, "modulate:a", 1.0, spec.fade)


# On the player as a fail knocks them down a row, until GLASS_HINT.booms have landed since it went up and it
# has been up GLASS_HINT.min_time, whichever is later.
func _keep_hint() -> void:
	if not is_instance_valid(hint):
		return
	var spec := MattArtLayout.GLASS_HINT
	hint.global_position = (_player_point() + spec.offset).round()
	if outcomes.size() - hint_impacts >= spec.booms and state_clock - hint_shown_at >= spec.min_time:
		_hide_hint()


func _hide_hint() -> void:
	if not is_instance_valid(hint):
		return
	var gone := hint
	hint = null
	loose.append(gone)
	var fade := gone.create_tween()
	fade.tween_property(gone, "modulate:a", 0.0, MattArtLayout.GLASS_HINT.fade)
	fade.tween_callback(gone.queue_free)
