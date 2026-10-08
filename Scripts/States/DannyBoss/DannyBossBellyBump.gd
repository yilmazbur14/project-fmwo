extends State

# His ring-out belly bump (Addendum 1, section B): a charge along the player's line that, landing, carries them
# into the side rope for the rest of a whole heart - the sumo's ring-out in small, which the tug at 0 HP pays off.
# Red: a fresh press as the belly meets them holds their ground (HELD!), and he rebounds dizzy (Staggered); a dash
# timed to it goes through; stepping out of his line lets him run on into the rope.
#   REACT    react_time: he faces the player.
#   SLIDE    suriashi to the launch spot: launch_offset px beside the player's feet on the side he's on, or the far
#            side if WALK_RECT leaves that run under min_run, at their feet's height. slide_time, or longer at
#            slide_max_speed; bump_slide toward the player, his step backing off.
#   WINDUP   windup_time under the strong red badge, the parry rearmed: bump_stomp for stomp_time (a small shake),
#            bump_slap for slap_time, then bump_crouch. He keeps to the player's line at up to align_speed px/s
#            and keeps facing them.
#   RUN      the line latches from his feet to theirs, within max_angle of level, and bump_run carries him along it:
#            his belly reaches their near edge max(min_run_time, run / charge_speed) later, the run measured from his
#            belly to that edge.
#   CONTACT  as his belly reaches their near edge, with their feet within band_half of his line: danny_belly_bump,
#            from their own hurtbox centre, so any facing answers it.
#            HIT      carried into the ropes: sealed, and driven along his facing at shove_speed into the side rope,
#                     his belly pinned on them; danny_rope_slam there, which the i-frames don't stop, pinned for
#                     pin_time; then the rope springs them rope_rebound px back and lets them go as he steps back
#                     step_back px.
#            PARRIED  HELD!: they don't move, the sumo's clash, their skid dust, held_hype; he rebounds `rebound` px
#                     back along his line and is dizzy for the parry's stagger (Staggered).
#            anything else, or their feet out of his line: he runs on into the rope, bounces off it and skids back.
#   SLIP     on the run, his feet into an armed puddle at least slip_min_run from where he launched: it splats, his
#            feet go, he slides slip_slide px (never within slip_gap of the player, and down off the top of the ring
#            as far as his lying box needs: DannyBossStateMachine.lying_top_min), and lands on his back
#            (DannyBossOnBack) for slip_window and slip_cap punches, the third the POW into the single-bar finisher
#            (the user, 2026-10-06: 3 hits always trigger the uppercut); slip_hype for the player. A puddle
#            under his feet as he launches is spared until he is off it.
# From the launch until he's back on his own feet he draws BEHIND the player (_place), so the contact reads as
# contact. Every way out gives the player ROOT_GRACE before a puddle can root them again (start_root_grace): one
# carried to the ropes is never rooted straight into a headbutt. A root taken in the bump doesn't seal the guard:
# rooted is holding your ground.

const ParryTell := preload("res://Scripts/ParryTell.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const HitStop := preload("res://Scripts/HitStop.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const Layout := preload("res://Scripts/DannyBossArtLayout.gd")

enum Beat { REACT, SLIDE, WINDUP, RUN, SHOVE, PIN, SPRING, REBOUND, SKID, SLIP }

const BUMP_ID := &"danny_belly_bump"
const ROPE_ID := &"danny_rope_slam"
const HINT_KEY := &"bump"
const HINT_TEXT := "HOLD YOUR GROUND! TAP %s AS HE HITS!"
const SHAKE_STEPS := 4
const SHAKE_STEP := 0.04
# The badge is cleared at the contact, or as he passes the player: this outlasts the longest run the ring allows.
const BADGE_SLACK := 0.05
const LONGEST_RUN := 1.25
# The placeholder rope: slam_impact's burst frames on the rope, and the side rope's own sprite bowed outward.
const ROPE_BURST_FRAMES := 5
const ROPE_BOW_OUT := 0.10
const ROPE_BOW_BACK := 0.15
const WALLS := {-1.0: ^"Arena/wallBoundaries/leftWall/wall", 1.0: ^"Arena/wallBoundaries/rightWall/wall"}

@export var body : CharacterBody2D

#KNOBS (seconds and px)
@export var react_time := 0.15
@export var launch_offset := 620.0
@export var min_run := 420.0
@export var slide_time := 0.40
@export var slide_max_speed := 1800.0
# One pass of his step loop: 0.06 s a frame.
@export var slide_loop_time := 0.24
@export var windup_time := 0.80
@export var stomp_time := 0.25
@export var slap_time := 0.20
@export var stomp_shake := 3.0
@export var align_speed := 700.0
@export var max_angle := 18.0
@export var charge_speed := 1400.0
@export var min_run_time := 0.30
@export var band_half := 70.0
# Until the contact his charge leans toward the player's line at up to this many px/s (_steer): slower than a walk, so
# a dash out of his line still clears it, but walking up or down from anywhere in his crouch no longer does (the
# 2026-10-04 playtest: on a dead straight line that was a free dodge with no read in it). 0 runs him dead straight.
@export var run_align_speed := 500.0
@export var rebound := 180.0
@export var rebound_time := 0.35
@export var shove_speed := 1100.0
@export var shove_min := 0.12
@export var shove_max := 0.60
# Nearer the rope than this, the shove is skipped: the rope slam comes at once.
@export var near_rope := 40.0
@export var pin_time := 0.15
@export var rope_rebound := 90.0
@export var rope_rebound_time := 0.20
@export var step_back := 160.0
@export var step_back_time := 0.35
@export var skid := 100.0
@export var skid_time := 0.35
@export var rope_hit_stop := 0.10
@export var rope_shake := 12.0
@export var rope_cheer := 1.0
# His own bounce off the rope, dodged or missed.
@export var bounce_shake := 6.0
@export var clash_hit_stop := 0.08
@export var clash_shake := 8.0
@export var held_hype := 6.0
@export var held_cheer := 2.0
# The side rope's sprite bowed outward this far while the placeholder rope stands in.
@export var rope_bow := 6.0
# The user's open question 3, on by default.
@export var slip_enabled := true
@export var slip_min_run := 150.0
@export var slip_slide := 100.0
@export var slip_time := 0.30
@export var slip_gap := 40.0
@export var slip_window := 2.2
@export var slip_cap := 4
@export var slip_hype := 8.0
@export var slip_cheer := 2.0
# The floor round his lying box cleared this far out.
@export var slip_clear := 40.0
# The user's open question 4, off by default: each parried bump banks this much of the final tug's rope for the
# player, up to tug_head_start_max (DannyBossSumo).
@export var tug_head_start := 0.0
@export var tug_head_start_max := 0.24

@onready var state_machine = get_parent()

# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
var beat := Beat.REACT
var beat_clock := 0.0
var facing := 1.0
var slide_from := Vector2.ZERO
var slide_length := 0.0
var launch_spot := Vector2.ZERO
var run_from := Vector2.ZERO
var run_speed := 0.0
var run_time := 0.0
var run_travel := 0.0
# How far _steer has leant his run off its line, px down the screen.
var run_drift := 0.0
var run_on := false
# From the launch until he lands: where his feet are drawn, and how far his node sits above them (_place).
var feet := Vector2.ZERO
var sink := 0.0
var move_from := Vector2.ZERO
var move_to := Vector2.ZERO
var move_time := 0.0
var spared_puddle: Node
var sealed_player := false
var freed_player := false
var rope_fx: Node2D
var stagger_time := -1.0
# For tests: HitInfo.Result at the contact (-1 before it, or with no contact), the fight_clock at the wind-up, the
# launch and the contact, the line he ran along, the rearms, whether he slipped, where the ropes caught the player's
# feet and what the rope slam came to, and whether he ran on into the rope.
var result := -1
var windup_at := -1.0
var launch_at := -1.0
var contact_at := -1.0
var line := Vector2.RIGHT
var rearms := 0
var slipped := false
var shoved_to := Vector2.INF
var rope_result := -1
var ran_on := false


func Enter() -> void:
	released = false
	result = -1
	stagger_time = -1.0
	windup_at = -1.0
	launch_at = -1.0
	contact_at = -1.0
	rearms = 0
	slipped = false
	shoved_to = Vector2.INF
	rope_result = -1
	ran_on = false
	run_on = false
	sink = 0.0
	sealed_player = false
	freed_player = false
	spared_puddle = null
	beat = Beat.REACT
	beat_clock = 0.0
	body.velocity = Vector2.ZERO
	body.set_hurtbox_active(false)
	body.show_body()
	body.set_body_box(&"idle")
	_face_player()
	body.play_anim(&"idle")


func Physics_Update(delta: float) -> void:
	if released:
		return
	beat_clock += delta
	match beat:
		Beat.REACT:
			if beat_clock >= react_time:
				_slide()
		Beat.SLIDE:
			_step_slide()
		Beat.WINDUP:
			_step_windup(delta)
		Beat.RUN:
			_step_run(delta)
		Beat.SHOVE:
			_step_shove()
		Beat.PIN:
			if beat_clock >= pin_time:
				_spring()
		Beat.SPRING:
			_step_spring()
		Beat.REBOUND:
			_step_move()
			if beat_clock >= move_time:
				_stagger()
		Beat.SKID:
			_step_move()
			if beat_clock >= move_time:
				_done()
		Beat.SLIP:
			_step_move()
			if beat_clock >= move_time:
				_onto_back()


func Exit() -> void:
	release()


# Idempotent, however it ended: the badge, the hint, a drive of the player and his sink undone, and a player it
# sealed let go.
func release() -> void:
	if released:
		return
	released = true
	if not is_instance_valid(body):
		return
	ParryTell.clear(body)
	if sink != 0.0:
		_unsink()
	body.set_lift(0.0)
	if sealed_player:
		sealed_player = false
		if state_machine.is_driving_player():
			state_machine._end_drive()
		state_machine.unlock_player()
	if is_instance_valid(rope_fx):
		rope_fx.queue_free()
	rope_fx = null
	if body.is_inside_tree():
		body.restore_hud()
		body.hide_hint(HINT_KEY)
		if result < 0:
			state_machine.start_root_grace()


# Leaving with his whole scene: the badge, the hint and the HUD go with it.
func _exit_tree() -> void:
	released = true


#THE PARRY (DannyBossScript relays PlayerDefense's calls here)

# Only the run: the contact asks while he is still running.
func can_parry_stagger(_hit: RefCounted) -> bool:
	return not released and beat == Beat.RUN


# Deferred by PlayerDefense, so it lands once the parried contact has already turned him into his rebound.
func parry_stagger(duration: float) -> void:
	if released or result != HitInfo.Result.PARRIED:
		return
	stagger_time = duration


#THE APPROACH

func _slide() -> void:
	beat = Beat.SLIDE
	beat_clock = 0.0
	slide_from = body.global_position
	launch_spot = _launch_spot()
	slide_length = maxf(slide_time, slide_from.distance_to(launch_spot) / slide_max_speed)
	# Side-on run frames only carry him forward: backing off to the spot, or round the player to their far side, he
	# steps front on.
	var player_x: float = state_machine.player_feet().x
	var closing: bool = signf(launch_spot.x - player_x) == signf(slide_from.x - player_x) \
		and absf(launch_spot.x - player_x) < absf(slide_from.x - player_x)
	if closing:
		body.play_anim(&"bump_slide")
	else:
		body.play_anim(&"step", &"", slide_loop_time)


func _step_slide() -> void:
	var weight := minf(beat_clock / slide_length, 1.0)
	body.global_position = slide_from.lerp(launch_spot, weight).round()
	_face_player()
	if weight >= 1.0:
		_wind_up()


# launch_offset px beside the player's feet on the side he's on, or the far side if WALK_RECT leaves that run under
# min_run; at their feet's height.
func _launch_spot() -> Vector2:
	var target: Vector2 = state_machine.player_feet()
	var walk: Rect2 = state_machine.WALK_RECT
	var side := -1.0 if body.global_position.x < target.x else 1.0
	var x := clampf(target.x + side * launch_offset, walk.position.x, walk.end.x)
	if absf(x - target.x) < min_run:
		side = -side
		x = clampf(target.x + side * launch_offset, walk.position.x, walk.end.x)
	return Vector2(x, clampf(target.y, walk.position.y, walk.end.y)).round()


func _wind_up() -> void:
	beat = Beat.WINDUP
	beat_clock = 0.0
	windup_at = body.fight_clock
	_face_player()
	body.play_anim(&"bump_stomp")
	body.play_sfx(&"bump_stomp")
	ScreenView.shake(get_tree(), stomp_shake, SHAKE_STEPS, SHAKE_STEP)
	ParryTell.telegraph(body, BUMP_ID, windup_time + LONGEST_RUN + BADGE_SLACK, body.tell_anchor)
	# ALWAYS, at the start of every tell: a press that whiffed earlier must never make this one unanswerable.
	state_machine.rearm_parry()
	rearms += 1
	body.update_hud_fade(&"bump_crouch")
	body.show_hint(HINT_KEY, HINT_TEXT % InputSettings.label_for(&"block"))


# The stomp, the belly slap and the crouch, keeping to the player's line and facing them.
func _step_windup(delta: float) -> void:
	var walk: Rect2 = state_machine.WALK_RECT
	var to_y: float = clampf(state_machine.player_feet().y, walk.position.y, walk.end.y)
	body.global_position = Vector2(body.global_position.x, move_toward(body.global_position.y, to_y, align_speed * delta)).round()
	_face_player()
	if beat_clock >= stomp_time and body.current_anim == &"bump_stomp":
		body.play_anim(&"bump_slap")
		body.play_sfx(&"belly_slap")
	if beat_clock >= stomp_time + slap_time and body.current_anim == &"bump_slap":
		body.play_anim(&"bump_crouch")
		body.play_sfx(&"bump_charge")
	if beat_clock >= windup_time:
		_launch()


#THE RUN

func _launch() -> void:
	beat = Beat.RUN
	beat_clock = 0.0
	launch_at = body.fight_clock
	run_from = body.global_position
	facing = -1.0 if body.sprite.flip_h else 1.0
	var to_player: Vector2 = state_machine.player_feet() - run_from
	var angle := clampf(atan2(to_player.y, absf(to_player.x)), -deg_to_rad(max_angle), deg_to_rad(max_angle))
	line = Vector2(cos(angle) * facing, sin(angle))
	body.play_anim(&"bump_run")
	body.play_sfx(&"bump_launch")
	var run := maxf(_belly_to_near_edge() / absf(line.x), 0.0)
	run_time = maxf(min_run_time, run / charge_speed)
	run_speed = run / run_time
	run_travel = 0.0
	run_drift = 0.0
	spared_puddle = state_machine.armed_puddle_at(run_from)
	_place(run_from)


# Along his line at the run's speed, and at least charge_speed once the read is over and he is running on.
func _step_run(delta: float) -> void:
	run_travel += (maxf(run_speed, charge_speed) if run_on else run_speed) * delta
	if not run_on:
		_steer(delta)
	_place(_run_point())
	if not run_on:
		if _slips():
			return
		if _belly_to_near_edge() <= 0.0 and beat_clock >= minf(run_time, min_run_time):
			if _in_band() and not _past_him():
				_contact()
				return
			_pass()
	if run_on:
		var rope_x: float = state_machine.rope_point(facing, 0.0).x
		var walk: Rect2 = state_machine.WALK_RECT
		if facing * (body.belly_point(&"bump_run").x - rope_x) >= 0.0 or feet.x <= walk.position.x or feet.x >= walk.end.x:
			_bounce_off_rope()


# How far his belly is short of the player's near edge along his facing, px; 0 or less once it has reached it.
func _belly_to_near_edge() -> float:
	var box := _player_box()
	var near := box.position.x if facing > 0.0 else box.end.x
	return facing * (near - body.belly_point(&"bump_run").x)


func _in_band() -> bool:
	var offset: Vector2 = state_machine.player_feet() - _run_point()
	return absf(offset.cross(line)) <= band_half


# Where his feet are on the run: along his line, leant off it by _steer.
func _run_point() -> Vector2:
	return run_from + line * run_travel + Vector2(0.0, run_drift)


func _steer(delta: float) -> void:
	var walk: Rect2 = state_machine.WALK_RECT
	var on_line: Vector2 = run_from + line * run_travel
	var want: float = clampf(state_machine.player_feet().y, walk.position.y, walk.end.y) - on_line.y
	run_drift = move_toward(run_drift, want, run_align_speed * delta)


# Their middle is behind his: a dash carried them through him, and his belly has nothing to meet. Without this a
# player who dashed through him early in the run was hit from behind once the dash's immunity ran out.
func _past_him() -> bool:
	return facing * (state_machine.player_hurtbox_centre().x - feet.x) < 0.0


# His feet into an armed puddle past slip_min_run from the launch. The one under him as he launched is spared until
# he is off it.
func _slips() -> bool:
	if not slip_enabled:
		return false
	var puddle: Node = state_machine.armed_puddle_at(feet)
	if spared_puddle != null and (not is_instance_valid(spared_puddle) or not spared_puddle.contains_feet(feet)):
		spared_puddle = null
	if puddle == null or puddle == spared_puddle or puddle.global_position.distance_to(run_from) < slip_min_run:
		return false
	_slip(puddle)
	return true


# He passed the player without meeting them: the read is over, and he runs on into the rope.
func _pass() -> void:
	run_on = true
	ran_on = true
	ParryTell.clear(body)
	body.hide_hint(HINT_KEY)
	body.restore_hud()


func _contact() -> void:
	contact_at = body.fight_clock
	ParryTell.clear(body)
	body.hide_hint(HINT_KEY)
	body.restore_hud()
	var player: Node2D = state_machine.get_player()
	result = HitInfo.Result.IGNORED
	if player:
		result = player.receive_hit(HitInfo.make(BUMP_ID, self, state_machine.player_hurtbox_centre(), body))
	# A hit that ended the fight has handed it on already, or will a step from now.
	if released:
		return
	if result == HitInfo.Result.HIT and player.playerHealth <= 0:
		release()
		return
	match result:
		HitInfo.Result.HIT:
			_shove(player)
		HitInfo.Result.PARRIED:
			_held(player)
		_:
			run_on = true
			ran_on = true


#HIT: THE ROPES

func _shove(player: Node2D) -> void:
	beat = Beat.SHOVE
	beat_clock = 0.0
	body.play_anim(&"bump_contact")
	body.play_sfx(&"bump_hit")
	# The root the wind-up may have left on them goes first: its release would lift the seal with its own.
	state_machine.release_root()
	state_machine.seal_player()
	sealed_player = true
	state_machine.face_player_at(feet)
	var to: Vector2 = state_machine.player_rope_position(facing)
	var distance := absf(to.x - player.global_position.x)
	if distance > near_rope:
		state_machine.drive_player_to(to, clampf(distance / shove_speed, shove_min, shove_max))
	_pin_belly()
	if not state_machine.is_driving_player():
		_rope_slam()


func _step_shove() -> void:
	_pin_belly()
	if not state_machine.is_driving_player():
		_rope_slam()


# His belly on the player's near edge as they are carried, his feet on his line's height.
func _pin_belly() -> void:
	var box := _player_box()
	var near := box.position.x if facing > 0.0 else box.end.x
	var belly_x: float = Layout.texel_local(Layout.belly(&"bump_contact"), &"bump_contact", body.sprite.flip_h).x
	var walk: Rect2 = state_machine.WALK_RECT
	_place(Vector2(clampf(near - belly_x, walk.position.x, walk.end.x), feet.y))


func _rope_slam() -> void:
	beat = Beat.PIN
	beat_clock = 0.0
	var player: Node2D = state_machine.get_player()
	shoved_to = state_machine.player_feet()
	rope_fx = _rope_impact(state_machine.rope_point(facing, state_machine.player_hurtbox_centre().y))
	if player:
		rope_result = player.receive_hit(HitInfo.make(ROPE_ID, rope_fx, state_machine.player_hurtbox_centre(), body))
	if released:
		return
	body.play_sfx(&"rope_slam")
	HitStop.freeze(get_tree(), rope_hit_stop)
	ScreenView.shake(get_tree(), rope_shake, SHAKE_STEPS, SHAKE_STEP)
	get_tree().call_group("arena_crowd", "cheer", rope_cheer)
	if player and player.playerHealth <= 0:
		release()


# The ropes spring the player back toward the middle and let them go, as he steps back off them.
func _spring() -> void:
	beat = Beat.SPRING
	beat_clock = 0.0
	var player: Node2D = state_machine.get_player()
	if player:
		state_machine.drive_player_to(player.global_position - Vector2(facing * rope_rebound, 0.0), rope_rebound_time)
	var walk: Rect2 = state_machine.WALK_RECT
	_move(Vector2(feet.x - facing * step_back, feet.y).clamp(walk.position, walk.end), step_back_time)
	body.play_anim(&"bump_skid")
	freed_player = false


func _step_spring() -> void:
	_step_move()
	if not freed_player and not state_machine.is_driving_player():
		freed_player = true
		sealed_player = false
		state_machine.unlock_player()
	if freed_player and beat_clock >= move_time:
		_done()


#PARRIED: HELD

func _held(player: Node2D) -> void:
	body.play_anim(&"bump_rebound")
	body.play_sfx(&"clash")
	HitStop.freeze(get_tree(), clash_hit_stop)
	ScreenView.shake(get_tree(), clash_shake, SHAKE_STEPS, SHAKE_STEP)
	_player_dust()
	var popups: Node = player.get_parent().get_node_or_null(^"CanvasLayer/CombatPopups")
	if popups != null and popups.has_method("show_popup"):
		popups.show_popup(&"held")
	body.add_player_hype(held_hype)
	get_tree().call_group("arena_crowd", "cheer", held_cheer)
	if tug_head_start > 0.0:
		state_machine.tug_head_start = minf(state_machine.tug_head_start + tug_head_start, tug_head_start_max)
	var walk: Rect2 = state_machine.WALK_RECT
	_move((feet - line * rebound).clamp(walk.position, walk.end), rebound_time)
	beat = Beat.REBOUND


func _stagger() -> void:
	_unsink()
	state_machine.start_root_grace()
	state_machine.states["Staggered"].window = maxf(stagger_time, 0.0)
	state_machine.on_child_transition(self, "Staggered")


# Two of the player's own skid puffs at their feet, once.
func _player_dust() -> void:
	var spec := Layout.fx(&"sumo_dust")
	var at: Vector2 = state_machine.player_feet()
	for side in [-1.0, 1.0]:
		var puff := Sprite2D.new()
		puff.texture = load(spec.texture)
		puff.hframes = spec.hframes
		puff.vframes = spec.vframes
		puff.frame_coords = Vector2i(0, spec.player_row)
		puff.flip_h = side > 0.0
		puff.offset = Layout.flipped_offset(spec.offset, puff.flip_h)
		puff.scale = Vector2.ONE * Layout.SCALE
		state_machine.add_hazard(puff, at + Vector2(side * 12.0, 0.0), body.floor_layer)
		var play := puff.create_tween()
		for i in range(1, spec.hframes):
			play.tween_interval(spec.frame_time)
			play.tween_callback(puff.set_frame_coords.bind(Vector2i(i, spec.player_row)))
		play.tween_interval(spec.frame_time)
		play.tween_callback(puff.queue_free)


#MISSED OR DODGED: HIS OWN ROPE

func _bounce_off_rope() -> void:
	beat = Beat.SKID
	beat_clock = 0.0
	_rope_impact(state_machine.rope_point(facing, body.belly_point(&"bump_run").y))
	body.play_sfx(&"rope_slam")
	ScreenView.shake(get_tree(), bounce_shake, SHAKE_STEPS, SHAKE_STEP)
	body.play_anim(&"bump_skid")
	var walk: Rect2 = state_machine.WALK_RECT
	_move(Vector2(feet.x - facing * skid, feet.y).clamp(walk.position, walk.end), skid_time)


func _done() -> void:
	_unsink()
	state_machine.start_root_grace()
	state_machine.attack_done(self)


#SLIP

func _slip(puddle: Node) -> void:
	slipped = true
	run_on = true
	puddle.splat()
	body.play_sfx(&"slip")
	ParryTell.clear(body)
	body.hide_hint(HINT_KEY)
	body.restore_hud()
	body.play_anim(&"bump_slip")
	body.add_player_hype(slip_hype)
	get_tree().call_group("arena_crowd", "cheer", slip_cheer)
	_move(_slip_end(), slip_time)
	beat = Beat.SLIP


# slip_slide px on along his line, his lying box never nearer the player's hurtbox than slip_gap, and inside
# WALK_RECT; by the top of the ring he slides down too, so lying he stays under the top rope and the boss bar
# (lying_top_min).
func _slip_end() -> Vector2:
	var walk: Rect2 = state_machine.WALK_RECT
	var to := feet + line * slip_slide
	to.y = maxf(to.y, state_machine.lying_feet_y_min(Layout.body_rect(&"back")))
	# The lying box mirrors with him, so its leading edge is its far edge whichever way he faces.
	var reach: float = Layout.body_rect(&"back").end.x
	var box := _player_box()
	var near := box.position.x if facing > 0.0 else box.end.x
	var furthest := near - facing * (slip_gap + reach)
	if facing * (to.x - furthest) > 0.0:
		to.x = furthest if facing * (furthest - feet.x) > 0.0 else feet.x
	return to.clamp(walk.position, walk.end).round()


func _onto_back() -> void:
	_unsink()
	body.play_sfx(&"wake")
	state_machine.clear_floor_round(body.body_box_rect(&"back"), slip_clear)
	state_machine.start_root_grace()
	state_machine.enter_on_back(slip_window, slip_cap, true, &"slip")


#MOVING HIM

func _move(to: Vector2, seconds: float) -> void:
	move_from = feet
	move_to = to
	move_time = maxf(seconds, 0.001)
	beat_clock = 0.0


func _step_move() -> void:
	var weight := minf(beat_clock / move_time, 1.0)
	# Out fast and settling, as a skid does.
	var eased := 1.0 - (1.0 - weight) * (1.0 - weight)
	_place(move_from.lerp(move_to, eased))


func _face_player() -> void:
	var player: Node2D = state_machine.get_player()
	if player:
		body.face_toward(player.global_position)


func _player_box() -> Rect2:
	var player: Node2D = state_machine.get_player()
	if player == null:
		return Rect2(state_machine.HOME, Vector2.ZERO)
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	return shape.global_transform * shape.shape.get_rect()


#THE ROPE'S FX

# The side rope bowing at `at`: the artist's sheet, or slam_impact's burst frames and the arena's side rope sprite
# bowed outward and back. The rope slam's hit source, so it lives in the hazard group until its frames are done.
func _rope_impact(at: Vector2) -> Node2D:
	var final := Layout.final_fx(&"rope_impact")
	var spec := Layout.fx(&"rope_impact" if final else &"slam_impact")
	var fx := Sprite2D.new()
	fx.texture = load(spec.texture)
	fx.hframes = spec.hframes
	fx.scale = Vector2.ONE * Layout.SCALE
	fx.flip_h = final and facing < 0.0
	fx.offset = Layout.flipped_offset(spec.offset, fx.flip_h)
	state_machine.add_hazard(fx, at, body.projectile_layer)
	var frames: int = spec.hframes if final else ROPE_BURST_FRAMES
	var play := fx.create_tween()
	for i in range(1, frames):
		play.tween_interval(Layout.fx_frame_time(spec, i - 1))
		play.tween_callback(fx.set_frame.bind(i))
	play.tween_interval(Layout.fx_frame_time(spec, frames - 1))
	play.tween_callback(fx.queue_free)
	if not final:
		_bow_rope()
	return fx


func _bow_rope() -> void:
	var scene := get_tree().current_scene
	var wall: Node2D = scene.get_node_or_null(WALLS[facing]) if scene else null
	if wall == null:
		return
	if not wall.has_meta(&"rest"):
		wall.set_meta(&"rest", wall.global_position)
	var rest: Vector2 = wall.get_meta(&"rest")
	var bow := wall.create_tween()
	bow.tween_property(wall, "global_position", rest + Vector2(facing * rope_bow, 0.0), ROPE_BOW_OUT)
	bow.tween_property(wall, "global_position", rest, ROPE_BOW_BACK)


#DRAWN BEHIND THE PLAYER (the Headbutt's own, copied: no two attacks share a file)

# His feet drawn at `at` and `arc` px up, with his node - what the fight's y-sort orders him by - no lower than
# just over the player's sprite, and his lift putting his drawing back down where it belongs. His points all take
# the lift off, so his belly, crown and badge stay where they are drawn.
func _place(at: Vector2, arc := 0.0) -> void:
	feet = at.round()
	var node := Vector2(feet.x, minf(feet.y, _sort_line()))
	sink = feet.y - node.y
	body.global_position = node
	body.set_lift(roundf(arc) - sink)


# Down on his own feet and his own y-sort.
func _unsink() -> void:
	body.global_position = feet
	sink = 0.0
	body.set_lift(0.0)


# A pixel over the player's sprite's origin, which is where the y-sort puts them.
func _sort_line() -> float:
	var player: Node2D = state_machine.get_player()
	if player == null:
		return INF
	return floorf(player.to_global(player.sprite_base_position).y) - 1.0
