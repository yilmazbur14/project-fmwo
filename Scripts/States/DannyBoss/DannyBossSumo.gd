extends State

# Danny at 0 HP (plan section 8): it isn't over. A false victory with the gates open, then he wakes, leaps
# onto the top gate and blocks it, says his line, and the two of them push for it: a tug-of-war mash
# (DannyBossTugOfWar), the same effort wherever the rope is and swinging both ways as he surges, that throws
# the loser out through a gate. Only its result ends the fight, so nothing before it may set the player's
# fight_over: hold_pose() refuses from then on.
#
# THE BEATS, in seconds:
#   KO             once the finisher is done with him, 0.4. Juggled to 0 he lands here from his crash, lying.
#   FALSE VICTORY  1.8, the player free: he lies on (the juggle's `down`), naps on, or sits down (`defeat`);
#                  his bar and gauge go, his theme fades, the fanfare and the crowd; the gates open 0.6 in.
#   STIR           0.5: the cut starts (BossEntrance, the hold on the player and hold-to-skip); a snort, the
#                  record scratch over the fanfare, the crowd hushed, and he wakes. Lying, he sits up first.
#   LEAP           0.2 crouched, then a 0.70 s arc onto GATE_BLOCK peaking 420 px up, the slam target as his
#                  shadow; he lands on the slam's squash with its dust, and a player near the gate is shoved clear.
#   RISE           0.49: into his block, the crowd, and his theme from the top, once.
#   LINE           his line (DannyBossSumo.dialogue), squashing him while it types; its end is line_over().
#   WALK           the player walked onto CLINCH, 0.3 to 1.4 s by the distance, facing him.
#   CALL           0.8: SUMO!, two stomps, a shake and the crowd.
#   CLINCH         0.3: the cut is over; the player sealed and posed facing him, his push set, the tachiai's
#                  clash, and the meter (DannyBossSumoMeter) coming up with the mash keys either side and PUSH!
#   MASH           the tug-of-war: presses in _input, the rope stepped in Physics_Update and drawn as the two
#                  of them on the gate's line, whoever it is going against skidding, him leaning in through each
#                  surge; then WON or LOST, which push the loser out and end the fight.
# A held skip anywhere in the cut (skip_cut) lands on the clinch exactly as a watched cut does.
#
# EVERY WAIT is a node-bound tween in `waits` or the MASH's physics step, so a pause holds any beat; the skip
# runs the waits out and every beat bails on the cut being over (_cut_live).
#
# RELEASE: what it put on the HUD and the mat goes back through release(), which Exit() and _exit_tree()
# call. It starts no tween: _exit_tree() can come as the fight scene is torn down.

const Layout := preload("res://Scripts/DannyBossArtLayout.gd")
const BossEntrance := preload("res://Scripts/BossEntrance.gd")
const FightOutro := preload("res://Scripts/FightOutro.gd")
const HitStop := preload("res://Scripts/HitStop.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const MashInput := preload("res://Scripts/MashInput.gd")
const FinisherArtLayout := preload("res://Scripts/FinisherArtLayout.gd")
const TugOfWar := preload("res://Scripts/DannyBossTugOfWar.gd")
const SumoMeter := preload("res://Scripts/DannyBossSumoMeter.gd")
const SlamMark := preload("res://Scripts/DannyBossSlamMark.gd")
const Slams := preload("res://Scripts/States/DannyBoss/DannyBossSlams.gd")

enum Phase { KO, FALSE_VICTORY, STIR, LEAP, RISE, LINE, WALK, CALL, CLINCH, MASH, WON, LOST, DONE }

const SPEAKER := "Danny"
# His theme at the KO, faded to nothing.
const SILENT_DB := -60.0
# MashInput's rule, real seconds: both keys pressed in one flush count once.
const MASH_MIN_INTERVAL := 0.03
const SHAKE_STEPS := 4
const SHAKE_STEP := 0.04
# His landing on the gate leaves the slam's cracks as long as a slam does.
const CRACKS_HOLD := 0.6
const CRACKS_FADE := 0.4
# A one-shot shown straight on its last frame (_hold_last).
const SNAP_TIME := 0.001
const METER_FADE := 0.3
# Measured off the push sheets: his feet either side of his middle column, in texels; the player's two feet off
# their frame's middle, in texels, and their soles under their origin, in px.
const DANNY_FOOT_X := 68.0
const PLAYER_FOOT_X := [-7.5, 5.5]
const PLAYER_SOLES := 39.0
# SUMO!, written out until it is drawn: in the mash's colours, big, across the middle of the ring.
const CALL_WORD := "SUMO!"
const CALL_FONT_SIZE := 99
const CALL_OUTLINE := 12
const CALL_SIZE := Vector2(720, 150)
const CALL_CENTRE := Vector2(960, 660)
const CALL_FLICKER := 0.15

@export var body : CharacterBody2D

#THE CUT (seconds and px)
@export var ko_hold := 0.4
@export var false_victory_time := 1.8
@export var gates_open_at := 0.6
@export var hud_fade_time := 0.6
@export var music_fade_time := 0.5
@export var victory_cheer := 3.0
@export var gate_shake := 6.0
@export var stir_time := 0.5
@export var sit_up_time := 0.15
@export var crouch_time := 0.2
@export var leap_time := 0.70
@export var leap_height := 420.0
@export var landing_shake := 16.0
@export var shove_reach := 220.0
@export var shove_time := 0.18
@export var rise_time := 0.49
@export var rise_cheer := 2.0
@export var walk_speed := 650.0
@export var walk_min := 0.3
@export var walk_max := 1.4
@export var call_time := 0.8
@export var call_shake := 8.0
@export var call_cheer := 2.0
@export var clinch_time := 0.3
@export var clash_hit_stop := 0.08
@export var clash_shake := 10.0

#THE TUG (DannyBossTugOfWar's knobs and its fit: re-run its table() whenever one of these moves)
@export var press_gain := 0.1
@export var press_speed := 0.75
@export var danny_push := 0.40
@export var surge_push := 1.2
@export var surge_time := 1.0
@export var surge_every := 3.0
@export var surge_first := 1.2
@export var sumo_max := 30.0
@export var final_surge := 1.0
# The crowd for every tenth of the rope the player wins off the line, and as each surge starts, with a shake.
@export var gain_cheer := 0.4
@export var surge_cheer := 1.5
@export var surge_shake := 6.0
# His strain loop's length.
@export var strain_loop := 0.27

#THE FINISH
@export var danny_out_time := 0.8
@export var danny_out_feet_y := -60.0
@export var danny_gate_feet_y := 100.0
@export var player_out_time := 0.45
@export var player_out_feet_y := 1040.0
@export var player_gate_feet_y := 967.0
@export var on_back_after := 0.30
@export var won_cheer := 4.0

@onready var state_machine = get_parent()

# Set by DannyBossStateMachine.land_juggled(): juggled to 0 HP, he starts the sumo lying on his back.
var lying := false
# The tests' knob: &"win" or &"loss" ends the fight that way as soon as the KO is over.
var auto_result := &""
# &"win" or &"loss", once the tug has one.
var result := &""
var phase := Phase.KO
# Beats seen through to their end: name -> game seconds it took.
var beat_times := {}
# The tug as it stands, for a test.
var rope := 0.0
var presses := 0

# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
var cut: CanvasLayer
var cut_skipped := false
var waits: Array[Tween] = []
var was_asleep := false
# 0 HP caught him on his back (DannyBossOnBack): he lies on through the false victory and rolls up to stir.
var was_on_back := false
var ko_left := 0.0
var beat_started := 0.0
var tug: TugOfWar
var meter: SumoMeter
var call_label: Label
var leap_mark: SlamMark
# Two puffs a fighter, his feet then the player's, left then right.
var dust: Array[Sprite2D] = []
var dust_clock := 0.0
var pair: Array[StringName] = []
var last_action := &""
var last_press_usec := 0
var best_tenth := 0
var danny_surging := false
# The push pose he is showing: straining, skidding, or leaning in (push_win) through a surge.
var danny_pose := &""
var player_skidding := false
var danny_skidding := false
var gates_closing := false
var gates_shut := false
var pushed_out := false
var prop: Sprite2D


func Enter() -> void:
	released = false
	result = &""
	phase = Phase.KO
	beat_times.clear()
	rope = 0.0
	presses = 0
	cut_skipped = false
	gates_closing = false
	gates_shut = false
	pushed_out = false
	danny_surging = false
	danny_pose = &""
	best_tenth = 0
	player_skidding = false
	danny_skidding = false
	tug = null
	ko_left = ko_hold
	was_asleep = body.current_anim in [&"sleep", &"sleep_hit"]
	was_on_back = String(body.current_anim).begins_with("back_")
	body.velocity = Vector2.ZERO
	body.set_hurtbox_active(false)


func Update(_delta: float) -> void:
	if released or phase != Phase.LINE:
		return
	# Untyped: the balloon frees itself when the line ends, and a freed object can't be held in a typed
	# variable long enough to ask is_instance_valid about it.
	var balloon = state_machine.sumo_balloon
	if not is_instance_valid(balloon) or not balloon.is_inside_tree():
		return
	var line: RefCounted = balloon.dialogue_line
	if line != null:
		body.set_talking(line.character == SPEAKER and balloon.dialogue_label.is_typing)


func Physics_Update(delta: float) -> void:
	if released:
		return
	match phase:
		Phase.KO:
			if _finisher_busy():
				return
			ko_left -= delta
			if ko_left <= 0.0:
				_after_ko()
		Phase.MASH:
			_mash(delta)


func Exit() -> void:
	release()


func _exit_tree() -> void:
	release()


func release() -> void:
	if released:
		return
	released = true
	if is_instance_valid(cut):
		# Out of the tree with the fight scene, it can only go; in it, it hands the player back.
		if cut.is_inside_tree():
			cut.end()
		else:
			cut.queue_free()
	cut = null
	for node in [meter, call_label, leap_mark]:
		if is_instance_valid(node):
			node.queue_free()
	meter = null
	call_label = null
	leap_mark = null
	for puff in dust:
		if is_instance_valid(puff):
			puff.queue_free()
	dust.clear()
	if is_instance_valid(body):
		body.stop_sfx(&"push_strain")


#THE KO AND THE FALSE VICTORY

func _after_ko() -> void:
	if auto_result == &"win":
		_danny_gone()
		return
	if auto_result == &"loss":
		_player_gone()
		return
	_false_victory()


func _false_victory() -> void:
	phase = Phase.FALSE_VICTORY
	_start_beat()
	# Lying, the juggle's `down` loop is still his, until the stir.
	if not lying:
		body.show_body()
		if was_on_back:
			body.play_anim(&"back_daze")
		else:
			body.play_anim(&"sleep" if was_asleep else &"defeat")
	body.finish_health_bar()
	body.hide_boss_hud(hud_fade_time)
	body.fade_music(SILENT_DB, music_fade_time, true)
	body.victory_sfx_player.play()
	get_tree().call_group("arena_crowd", "cheer", victory_cheer)
	await _beat(gates_open_at)
	if not _live():
		return
	var gates: Node = state_machine.gates()
	if gates != null:
		gates.open()
	body.play_sfx(&"gate_clang")
	ScreenView.shake(get_tree(), gate_shake, SHAKE_STEPS, SHAKE_STEP)
	await _beat(false_victory_time - gates_open_at)
	if not _live():
		return
	_end_beat(&"false_victory")
	_stir()


#THE CUT

func _stir() -> void:
	phase = Phase.STIR
	_start_beat()
	cut = BossEntrance.new()
	cut.name = "SumoCut"
	add_child(cut)
	cut.skipped.connect(skip_cut)
	cut.begin(_player())
	body.play_sfx(&"wake")
	body.play_sfx(&"record_scratch")
	body.victory_sfx_player.stop()
	get_tree().call_group("arena_crowd", "hush")
	if lying:
		_stop_lingering()
		body.show_body()
		_hold_last(&"defeat")
		await _beat(sit_up_time)
		if not _cut_live():
			return
	elif was_on_back:
		body.play_anim(&"back_roll")
		body.play_sfx(&"back_roll")
		await _beat(Layout.loop_length(Layout.anim(&"back_roll")))
		if not _cut_live():
			return
	body.play_anim(&"wake")
	await _beat(stir_time)
	if not _cut_live():
		return
	_end_beat(&"stir")
	_leap()


# Crouched, off the mat on the launch's lift-off frame, and over in an arc onto the gate, the slam target
# under him as his shadow.
func _leap() -> void:
	phase = Phase.LEAP
	_start_beat()
	var liftoff: float = Slams.liftoff_delay()
	body.show_body()
	body.play_anim(&"jump_crouch")
	await _beat(maxf(crouch_time - liftoff, 0.0))
	if not _cut_live():
		return
	body.play_anim(&"jump_launch")
	await _beat(liftoff)
	if not _cut_live():
		return
	var from := body.global_position
	leap_mark = SlamMark.new()
	leap_mark.name = "LeapShadow"
	leap_mark.full_height = leap_height
	state_machine.add_hazard(leap_mark, from, body.floor_layer)
	var arc := create_tween()
	arc.tween_method(_step_leap.bind(from), 0.0, 1.0, leap_time)
	await _wait(arc)
	if not _cut_live():
		return
	_land_at_gate()
	_end_beat(&"leap")
	_rise()


func _step_leap(progress: float, from: Vector2) -> void:
	if not _cut_live():
		return
	var ground := from.lerp(state_machine.GATE_BLOCK, progress).round()
	var lift := leap_height * 4.0 * progress * (1.0 - progress)
	body.global_position = ground
	body.set_lift(lift)
	if body.current_anim == &"jump_launch" and body.anim_done:
		body.play_anim(&"air")
	if is_instance_valid(leap_mark):
		leap_mark.global_position = ground
		leap_mark.set_height(lift)


func _land_at_gate() -> void:
	body.global_position = state_machine.GATE_BLOCK
	body.set_lift(0.0)
	body.play_anim(&"slam_impact")
	_free_leap_mark()
	body.play_sfx(&"butt_slam")
	ScreenView.shake(get_tree(), landing_shake, SHAKE_STEPS, SHAKE_STEP)
	Slams.play_impact(state_machine, body, body.contact_point(&"slam_impact"), CRACKS_HOLD, CRACKS_FADE)
	_shove_clear()


# A player standing where he came down is shoved south, clear of him.
func _shove_clear() -> void:
	var player := _player()
	if player == null:
		return
	var feet: Vector2 = state_machine.player_feet()
	var gate: Vector2 = state_machine.GATE_BLOCK
	if feet.distance_to(gate) >= shove_reach:
		return
	var clear := Vector2(feet.x, gate.y + shove_reach - state_machine.PLAYER_FEET_OFFSET)
	state_machine.drive_player_to(clear, shove_time)


func _rise() -> void:
	phase = Phase.RISE
	_start_beat()
	body.play_anim(&"wake", &"block")
	get_tree().call_group("arena_crowd", "cheer", rise_cheer)
	body.restart_music()
	await _beat(rise_time)
	if not _cut_live():
		return
	_end_beat(&"rise")
	phase = Phase.LINE
	_start_beat()
	state_machine.show_sumo_line(self)


# The line's natural end (DannyBossStateMachine._on_sumo_line_ended). A skip never comes through here.
func line_over() -> void:
	if not _cut_live() or phase != Phase.LINE:
		return
	body.set_talking(false)
	_end_beat(&"line")
	_walk()


# Onto their mark facing him, on this node's own tween rather than the cut's walk: the skip runs it out.
func _walk() -> void:
	phase = Phase.WALK
	_start_beat()
	var player := _player()
	if player == null:
		return
	# The line's end let go of the hold the cut put on them.
	player.is_talking = true
	var to := _clinch_position()
	var seconds := clampf(player.global_position.distance_to(to) / walk_speed, walk_min, walk_max)
	player.face_point(to)
	cut.play_player_anim(&"walking")
	var walk := create_tween()
	walk.tween_method(_step_player.bind(player.global_position, to), 0.0, 1.0, seconds)
	await _wait(walk)
	if not _cut_live():
		return
	player.global_position = to
	cut.play_player_anim(&"idle_down")
	state_machine.face_player_at(state_machine.GATE_BLOCK)
	_end_beat(&"walk")
	_call()


func _step_player(weight: float, from: Vector2, to: Vector2) -> void:
	var player := _player()
	if _cut_live() and player != null:
		player.global_position = from.lerp(to, weight).round()


func _call() -> void:
	phase = Phase.CALL
	_start_beat()
	_show_call()
	body.play_sfx(&"sumo_stomp")
	ScreenView.shake(get_tree(), call_shake, SHAKE_STEPS, SHAKE_STEP)
	get_tree().call_group("arena_crowd", "cheer", call_cheer)
	await _beat(call_time / 2.0)
	if not _cut_live():
		return
	body.play_sfx(&"sumo_stomp")
	await _beat(call_time / 2.0)
	if not _cut_live():
		return
	_end_beat(&"call")
	_clinch()


# What a held ui_cancel does anywhere in the cut: the line and whatever is left of the beats, at once, landing
# on the clinch exactly as a watched cut does.
func skip_cut() -> void:
	if released or cut_skipped or phase < Phase.STIR or phase >= Phase.CLINCH:
		return
	cut_skipped = true
	# Untyped, and asked first: once the line is over its balloon has freed itself, and a freed object can't be
	# passed to close_balloon()'s typed argument.
	var balloon = state_machine.sumo_balloon
	if is_instance_valid(balloon):
		BossEntrance.close_balloon(balloon)
	state_machine.end_sumo_line()
	BossEntrance.run_out(waits)
	_stop_lingering()
	for hazard in get_tree().get_nodes_in_group(state_machine.HAZARD_GROUP):
		hazard.queue_free()
	leap_mark = null
	var gates: Node = state_machine.gates()
	if gates != null and not gates.is_open():
		gates.open()
	body.restart_music()
	BossEntrance.settle_arena(get_tree())
	_clinch()


#THE CLINCH AND THE MASH

func _clinch() -> void:
	phase = Phase.CLINCH
	_start_beat()
	_free_call()
	_free_leap_mark()
	if is_instance_valid(cut):
		cut.end()
	cut = null
	body.global_position = state_machine.GATE_BLOCK
	body.show_body()
	body.set_talking(false)
	body.play_anim(&"push_set", &"push_strain")
	var player := _player()
	if player != null:
		# Ends a shove still under way, and puts them on their mark.
		state_machine.drive_player_to(_clinch_position(), 0.0)
		player.is_talking = false
		state_machine.seal_player()
		state_machine.hold_player_pose(Layout.player_pose_sheet())
		state_machine.face_player_at(state_machine.GATE_BLOCK)
		_pose_player(&"set")
	HitStop.freeze(get_tree(), clash_hit_stop)
	ScreenView.shake(get_tree(), clash_shake, SHAKE_STEPS, SHAKE_STEP)
	body.play_sfx(&"sumo_clash")
	_read_pair()
	_build_meter()
	await _beat(clinch_time)
	if not _live():
		return
	_end_beat(&"clinch")
	_start_mash()


func _start_mash() -> void:
	phase = Phase.MASH
	tug = TugOfWar.new()
	for knob in TugOfWar.KNOBS:
		tug.set(knob, get(knob))
	# The head start his parried belly bumps banked, 0 unless the user's open question 4 turns it on.
	tug.rope = state_machine.tug_head_start
	last_action = &""
	last_press_usec = 0
	player_skidding = false
	danny_skidding = false
	danny_surging = false
	_pose_player(&"strain")
	danny_pose = &"push_strain"
	body.play_anim(&"push_strain", &"", strain_loop)
	body.play_sfx(&"push_strain")
	_build_dust()
	_apply_rope()


func _input(event: InputEvent) -> void:
	if released or phase != Phase.MASH or tug == null or tug.result != &"":
		return
	for action in pair:
		if event.is_action_pressed(action):
			_press(action)
			return


func _press(action: StringName) -> void:
	var now := Time.get_ticks_usec()
	if not MashInput.counts(action, last_action, now, last_press_usec, MASH_MIN_INTERVAL):
		return
	last_action = action
	last_press_usec = now
	tug.press()
	presses = tug.presses
	if is_instance_valid(meter):
		meter.key_pressed(action, pair[1] if action == pair[0] else pair[0])


func _mash(delta: float) -> void:
	tug.advance(delta)
	rope = tug.rope
	presses = tug.presses
	_apply_rope()
	_mash_feedback(delta)
	if tug.result != &"":
		_finish(tug.result)


# The rope as the two of them on the gate's line, in whole px: at or past the line, his feet between
# GATE_BLOCK and WIN_FEET_Y with the player 48 under him; short of it, theirs between CLINCH and LOSE_FEET_Y
# with him 48 over them.
func _apply_rope() -> void:
	var gate: Vector2 = state_machine.GATE_BLOCK
	var clinch: Vector2 = state_machine.CLINCH
	var gap := clinch.y - gate.y
	var danny_y: float
	var player_y: float
	if rope >= 0.0:
		danny_y = lerpf(gate.y, state_machine.WIN_FEET_Y, rope)
		player_y = danny_y + gap
	else:
		player_y = lerpf(clinch.y, state_machine.LOSE_FEET_Y, -rope)
		danny_y = player_y - gap
	body.global_position = Vector2(gate.x, danny_y).round()
	var player := _player()
	if player != null:
		player.global_position = Vector2(clinch.x, player_y - state_machine.PLAYER_FEET_OFFSET).round()
	if is_instance_valid(meter):
		meter.set_rope(rope)


func _mash_feedback(delta: float) -> void:
	var tenth := floori(tug.fill() * 10.0)
	if tenth > best_tenth:
		best_tenth = tenth
		get_tree().call_group("arena_crowd", "cheer", gain_cheer)
	# Each surge is told as it starts, a stomp, a shake and the crowd, and his end of the meter stays lit
	# through it.
	var surging: bool = tug.surging()
	if surging != danny_surging:
		danny_surging = surging
		if surging:
			get_tree().call_group("arena_crowd", "cheer", surge_cheer)
			ScreenView.shake(get_tree(), surge_shake, SHAKE_STEPS, SHAKE_STEP)
			body.play_sfx(&"sumo_stomp")
		if is_instance_valid(meter):
			meter.surging = surging
	# Whoever the rope is going against skids, and the other strains: the player behind the line, him past it.
	# Through a surge he leans in, gaining, wherever the rope is.
	var skidding := rope < 0.0
	if skidding != player_skidding:
		player_skidding = skidding
		_pose_player(&"skid" if skidding else &"strain")
	var pose := &"push_win" if danny_surging else (&"push_skid" if rope > 0.0 else &"push_strain")
	if pose != danny_pose:
		danny_pose = pose
		body.play_anim(pose, &"", strain_loop if pose == &"push_strain" else 0.0)
	danny_skidding = pose == &"push_skid"
	_step_dust(delta)


#THE FINISH

func _finish(outcome: StringName) -> void:
	result = outcome
	body.stop_sfx(&"push_strain")
	for puff in dust:
		if is_instance_valid(puff):
			puff.visible = false
	if is_instance_valid(meter):
		var fade := meter.create_tween()
		fade.tween_property(meter, "modulate:a", 0.0, METER_FADE)
	if outcome == &"win":
		_push_danny_out()
	else:
		_push_player_out()


# The player's shove, and him out through the top gate, which slams behind him.
func _push_danny_out() -> void:
	phase = Phase.WON
	_start_beat()
	_pose_player(&"shove")
	body.play_anim(&"push_out")
	body.play_sfx(&"pushed_out")
	var out := create_tween()
	out.tween_method(_step_danny_out.bind(body.global_position.y), 0.0, 1.0, danny_out_time) \
		.set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)


func _step_danny_out(weight: float, from_y: float) -> void:
	if released:
		return
	var y := lerpf(from_y, danny_out_feet_y, weight)
	body.global_position = Vector2(state_machine.GATE_BLOCK.x, y).round()
	if not gates_closing and y < danny_gate_feet_y:
		gates_closing = true
		_shut_gates()


# His shove, and the player out through the bottom gate: thrown, then flat on their back past the rope.
func _push_player_out() -> void:
	phase = Phase.LOST
	_start_beat()
	body.play_anim(&"push_win")
	body.play_sfx(&"pushed_out")
	_pose_player(&"launched")
	var player := _player()
	if player == null:
		_player_gone()
		return
	# Out past the rope for good: the fight ends with them lying there, so nothing turns it back off.
	player.may_leave_ring = true
	var feet_y: float = player.global_position.y + state_machine.PLAYER_FEET_OFFSET
	var back := create_tween()
	back.tween_interval(on_back_after)
	back.tween_callback(_pose_player.bind(&"on_back"))
	var out := create_tween()
	out.tween_method(_step_player_out.bind(feet_y), 0.0, 1.0, player_out_time) \
		.set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	await out.finished
	if not _live():
		return
	_prop_player()
	pushed_out = true
	if gates_shut:
		_player_gone()


func _step_player_out(weight: float, from_feet_y: float) -> void:
	var player := _player()
	if released or player == null:
		return
	var feet_y := lerpf(from_feet_y, player_out_feet_y, weight)
	player.global_position = Vector2(state_machine.CLINCH.x, feet_y - state_machine.PLAYER_FEET_OFFSET).round()
	if not gates_closing and feet_y > player_gate_feet_y:
		gates_closing = true
		_shut_gates()


func _shut_gates() -> void:
	var gates: Node = state_machine.gates()
	if gates != null:
		await gates.close()
	if not _live():
		return
	gates_shut = true
	if phase == Phase.WON:
		_danny_gone()
	elif pushed_out:
		_player_gone()


# The fight's end, won: he's gone, and FightOutro takes it from here.
func _danny_gone() -> void:
	if phase == Phase.DONE:
		return
	if result == &"":
		result = &"win"
	_end_beat(&"won")
	phase = Phase.DONE
	body.sprite.visible = false
	body.defeated = true
	body.victory_sfx_player.play()
	get_tree().call_group("arena_crowd", "cheer", won_cheer)
	GameProgress.next_boss_scene = GameProgress.next_fight_after(body.FIGHT_SCENE)
	FightOutro.finish_fight(get_tree(), true)
	state_machine.enter_defeated()
	# The fight's end brings his bar back for a live fight's sake; his is finished and stays gone.
	body.hide_boss_hud(0.0)


# The fight's end, lost: FightOutro calls on_player_defeated(), which sits him down for his nap (Victory).
func _player_gone() -> void:
	if phase == Phase.DONE:
		return
	if result == &"":
		result = &"loss"
	_end_beat(&"lost")
	phase = Phase.DONE
	# Straight from a juggle kill (auto_result), the juggle's `down` loop would go on drawing over his nap.
	_stop_lingering()
	FightOutro.finish_fight(get_tree(), false)
	body.hide_boss_hud(0.0)


# The fight's end hands the player's own sprite back, pose and all: a copy of the pose's last frame lies where
# they landed, and theirs hides under it.
func _prop_player() -> void:
	var player := _player()
	if player == null:
		return
	var sprite: Sprite2D = player.sprite
	prop = Sprite2D.new()
	prop.name = "PushedOutPlayer"
	prop.texture = sprite.texture
	prop.hframes = sprite.hframes
	prop.vframes = sprite.vframes
	prop.frame = sprite.frame
	prop.offset = sprite.offset
	prop.flip_h = sprite.flip_h
	prop.centered = sprite.centered
	prop.scale = sprite.global_scale
	body.get_parent().add_child(prop)
	prop.global_position = sprite.global_position
	sprite.visible = false


#PIECES

func _clinch_position() -> Vector2:
	return state_machine.CLINCH - Vector2(0, state_machine.PLAYER_FEET_OFFSET)


func _pose_player(pose_name: StringName) -> void:
	var pose: Dictionary = Layout.player_pose(pose_name)
	state_machine.play_player_pose(pose.frames, pose.times, pose.loop)


# A one-shot shown straight on its last frame and held there.
func _hold_last(anim_name: StringName) -> void:
	body.play_anim(anim_name, &"", SNAP_TIME)
	body.sprite.frame = Layout.anim(anim_name).frames[-1]


func _stop_lingering() -> void:
	if not lying:
		return
	var juggled = state_machine.states.get("Juggled")
	if juggled != null and juggled.has_method("stop_lingering"):
		juggled.stop_lingering()


# The pair the mash runs on, the finisher's own (the arrows or the shoulder buttons on the reworked feel).
func _read_pair() -> void:
	pair.clear()
	var player := _player()
	if player != null:
		pair = player.finisher.mash_actions()


func _build_meter() -> void:
	if is_instance_valid(meter) or body.hud_layer == null:
		return
	meter = SumoMeter.new()
	meter.name = "SumoMeter"
	meter.modulate.a = 0.0
	body.hud_layer.add_child(meter)
	meter.show_keys(pair)
	var fade := meter.create_tween()
	fade.tween_property(meter, "modulate:a", 1.0, clinch_time)


func _show_call() -> void:
	_free_call()
	if body.hud_layer == null:
		return
	var colors: Array = FinisherArtLayout.prompt_word(&"mash").colors
	call_label = Label.new()
	call_label.name = "SumoCall"
	call_label.theme = load("res://Assets/UI/ui_theme.tres")
	call_label.text = CALL_WORD
	call_label.add_theme_font_size_override("font_size", CALL_FONT_SIZE)
	call_label.add_theme_constant_override("outline_size", CALL_OUTLINE)
	call_label.add_theme_color_override("font_outline_color", Color(0, 0, 0))
	call_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	call_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	call_label.size = CALL_SIZE
	call_label.position = CALL_CENTRE - CALL_SIZE / 2.0
	call_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	body.hud_layer.add_child(call_label)
	var flicker := call_label.create_tween().set_loops()
	for color in colors:
		flicker.tween_callback(call_label.add_theme_color_override.bind("font_color", color))
		flicker.tween_interval(CALL_FLICKER)


func _free_call() -> void:
	if is_instance_valid(call_label):
		call_label.queue_free()
	call_label = null


func _free_leap_mark() -> void:
	if is_instance_valid(leap_mark):
		leap_mark.queue_free()
	leap_mark = null


func _build_dust() -> void:
	var spec := Layout.fx(&"sumo_dust")
	var sheet: Texture2D = load(spec.texture)
	for i in 4:
		var puff := Sprite2D.new()
		puff.texture = sheet
		puff.hframes = spec.hframes
		puff.vframes = spec.vframes
		puff.scale = Vector2.ONE * Layout.SCALE
		# Drawn spraying off a foot to the left: the right feet's are mirrored, so both spray outward.
		puff.flip_h = i % 2 == 1
		puff.offset = Layout.flipped_offset(spec.offset, puff.flip_h)
		puff.visible = false
		state_machine.add_hazard(puff, body.global_position, body.floor_layer)
		dust.append(puff)


# The skidding side's feet kick up dust, by the same rule as their skid poses: his while the rope is the player's
# way, theirs while it's his. The rope sags back between presses, so going by its motion step to step would puff
# at the feet of a player who is winning.
func _step_dust(delta: float) -> void:
	if dust.is_empty():
		return
	var spec := Layout.fx(&"sumo_dust")
	dust_clock += delta
	var step := int(dust_clock / spec.frame_time) % int(spec.hframes)
	var player := _player()
	for i in dust.size():
		var puff := dust[i]
		if not is_instance_valid(puff):
			continue
		var his := i < 2
		var right := i % 2 == 1
		puff.visible = danny_skidding if his else (player_skidding and player != null)
		if not puff.visible:
			continue
		var foot: Vector2
		if his:
			foot = body.global_position + Vector2((DANNY_FOOT_X if right else -DANNY_FOOT_X) * Layout.SCALE, 0)
		else:
			foot = player.global_position + Vector2(PLAYER_FOOT_X[1 if right else 0] * Layout.SCALE, PLAYER_SOLES)
		puff.global_position = foot.round()
		puff.frame = int(spec.danny_row if his else spec.player_row) * int(spec.hframes) + step


func _finisher_busy() -> bool:
	var player := _player()
	return player != null and player.finisher.is_active()


# Waits `seconds` on this node's own clock. A skip runs it out rather than killing it, and the caller's own check
# is what bails.
func _beat(seconds: float) -> void:
	var tween := create_tween()
	tween.tween_interval(seconds)
	await _wait(tween)


func _wait(tween: Tween) -> void:
	waits.append(tween)
	await tween.finished
	waits.erase(tween)


func _start_beat() -> void:
	beat_started = body.fight_clock


func _end_beat(beat_name: StringName) -> void:
	beat_times[beat_name] = body.fight_clock - beat_started


func _live() -> bool:
	return not released and is_instance_valid(body) and state_machine.current_state == self


# Every beat of the cut asks this before it goes on, so one a skip ran out stops where it is.
func _cut_live() -> bool:
	return _live() and not cut_skipped


func _player() -> Node2D:
	return state_machine.get_player()
