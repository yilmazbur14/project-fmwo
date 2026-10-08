extends State

# The punish window, and the only place punches reach him outside a Break (MattBroken): recover_time on
# RecoverTimer, three punches at most (1 + 1 + 2), the third still the POW. NO FINISHER STARTS HERE: only his
# Break dazes him (MattScript.can_be_dazed, the Break-only rule, 2026-10-04; daze_in_recover brings the old
# daze back). It opens at HOME unless the attack before it left a recover_spot (the Glass Row: where he
# stands, over the player) and a bonus.
# Enter() needs nothing from the state before it, so a bare transition into it opens a working window.
#
# THE YELL is a sub-phase INSIDE it, and OFF in the live game (MattStateMachine.yell_counter_enabled, the user,
# 2026-10-04: no pushing a player away while they hit him). With it on it is decided once as the window opens:
# never in the fight's first window, then yell_chance. If it is planned, it goes off the frame after landed punch
# 1 or 2 (even odds):
#   TELL   0.58 s  the yellow ring over his head, a sharp inhale. Punches still land and count, and
#                  flash him without flinching him. Long enough for the swing that set it off and one more
#                  chained before a reaction (MattStateMachine.yell_tell).
#   BLAST  0.18 s  MattYellRingScript blown out from his mouth, 60 to 270 px, and the roar frames.
#   AFTER  0.35 s  the roar held.
# The window's timer is paused through all three and he can't be dazed in any of them. If it lands he
# is out of the window at once: the player is thrown across the ring and he starts again a second
# later (MattStateMachine.idle_after_yell). If it doesn't - dodged, or walked away from - the window
# gets yell_whiff_bonus back on top of what it had left, and its hit count starts again, so a whole
# combo into the daze is still there to be had.
#
# THE SCREAM (the user, 2026-09-27): once a punch short of the POW has landed here outside the yell, a
# swing that whiffs or is refused before the POW lands and he screams at once, with no tell: the yell's
# roar and a ring that hurts nobody, and the player shoved back to scream_clear from his mouth, inside the
# ring, with no damage. The combo's count goes with it. He is out of his window the way a landed yell takes
# him out, so there is no daze and no uppercut. The combo has no timing since 2026-09-30, so a slow press
# or a mashed one is never a miss. The POW ends the watch, and nothing is watched again until a punch short
# of it lands. Once the yell is on its way the combo is the yell's business: a miss through it does nothing,
# and a punch landed after it is watched again. MattStateMachine.scream_on_miss off retires it.

const ParryTell := preload("res://Scripts/ParryTell.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const RING_SCENE := preload("res://Scenes/Bosses/MattYellRingScene.tscn")
const DefenseHypeArtLayout := preload("res://Scripts/DefenseHypeArtLayout.gd")

const YELL_ID := &"matt_yell"
# Between the yellow badge's top and the top of the screen, when his crown is too high for all of it.
const BADGE_TOP_MARGIN := 4.0
const YELL_SHAKE_STEPS := 6
const YELL_SHAKE_STEP_TIME := 0.03
# A rope in the scream's way turns its push this many degrees a try, up to this many tries each way.
const SCREAM_TURN_STEP := 22.5
const SCREAM_TURNS := 4

@export var body : CharacterBody2D
@export var recover_timer : Timer

@onready var state_machine = get_parent()

enum Yell { NONE, TELL, BLAST, AFTER }

var yell := Yell.NONE
var yell_clock := 0.0
var yell_planned := false
# The landed punch it goes off after: 1 or 2.
var yell_on_hit := 0
# Due on the next physics step after the punch that triggers it. The punch resolves in the player's
# branch, which steps before his, so without the frame it would start on the same step.
var yell_due := false
var yell_due_frame := -1
var yell_result := HitInfo.Result.IGNORED
var ring: Node2D
# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
# Yells blown this window, for a test.
var yells := 0
# The player's combo, heard while the window is open, and whether the last punch to land was one short of
# the POW, landed on him outside the yell: the one a miss after it is screamed at. The scream itself waits
# for the end of the frame, out of the callback the miss came in.
var combo: Node
var combo_watched := false
var scream_due := false
# Screams this window, for a test.
var screams := 0


func Enter() -> void:
	released = false
	body.global_position = state_machine.take_recover_spot()
	body.velocity = Vector2.ZERO
	body.show_body()
	body.hits_this_window = 0
	body.daze_used = false
	state_machine.windows_opened += 1
	yell = Yell.NONE
	yell_due = false
	yells = 0
	yell_result = HitInfo.Result.IGNORED
	combo_watched = false
	scream_due = false
	screams = 0
	var player: Node2D = state_machine.get_player()
	combo = player.combo if player else null
	if combo and not combo.punch_landed.is_connected(_on_punch_landed):
		combo.punch_landed.connect(_on_punch_landed)
		combo.punch_missed.connect(_on_punch_missed)
		combo.punch_refused.connect(_on_punch_refused)
	_plan_yell()
	body.play_state_anim(&"recover")
	body.set_hurtbox_active(true)
	body.play_sfx(&"recover")
	recover_timer.paused = false
	recover_timer.start(state_machine.recover_time + state_machine.take_recover_bonus())


func Exit() -> void:
	release()


# Idempotent. The window's timer is never left paused, and nothing of the yell outlives it but a ring
# already blown, which is a hazard like any other.
func release() -> void:
	if released:
		return
	released = true
	yell = Yell.NONE
	yell_due = false
	scream_due = false
	if is_instance_valid(combo) and combo.punch_landed.is_connected(_on_punch_landed):
		combo.punch_landed.disconnect(_on_punch_landed)
		combo.punch_missed.disconnect(_on_punch_missed)
		combo.punch_refused.disconnect(_on_punch_refused)
	combo = null
	recover_timer.paused = false
	recover_timer.stop()
	if is_instance_valid(body):
		ParryTell.clear(body)
		body.set_hurtbox_active(false)
	if is_instance_valid(ring) and ring.answered.is_connected(_on_ring_answered):
		ring.answered.disconnect(_on_ring_answered)
	ring = null


# Both draws are made whether the yell is on or not, so his rng gives every other roll what it always did.
func _plan_yell() -> void:
	var roll: float = state_machine.rng.randf()
	yell_planned = state_machine.yell_counter_enabled and state_machine.windows_opened >= state_machine.yell_from_window 		and roll < state_machine.yell_chance
	var pick: int = state_machine.rng.randi_range(1, 2)
	yell_on_hit = pick if yell_planned else 0


func is_yelling() -> bool:
	return yell != Yell.NONE or yell_due


func on_punch_landed(count: int) -> void:
	if yell_planned and yell == Yell.NONE and yells == 0 and count == yell_on_hit:
		yell_due = true
		yell_due_frame = Engine.get_physics_frames()


func flinch() -> void:
	if not is_yelling():
		body.play_anim(&"hit", &"recover")


func Physics_Update(delta: float) -> void:
	if yell_due:
		if Engine.get_physics_frames() > yell_due_frame:
			yell_due = false
			_tell()
		return
	if yell == Yell.NONE:
		return
	yell_clock += delta
	match yell:
		Yell.TELL:
			if yell_clock >= state_machine.yell_tell:
				_blast()
		Yell.BLAST:
			if yell_clock >= state_machine.yell_expand_time:
				yell = Yell.AFTER
				yell_clock = 0.0
		Yell.AFTER:
			if yell_clock >= state_machine.yell_after:
				_missed()


func _tell() -> void:
	yell = Yell.TELL
	yell_clock = 0.0
	yells += 1
	recover_timer.paused = true
	body.play_anim(&"yell_tell")
	body.play_sfx(&"yell_tell")
	ParryTell.telegraph(body, YELL_ID, state_machine.yell_tell, _tell_anchor)


# Over his crown, but never with the badge's top off the screen: in the window at the Glass Row's station the
# tip's spot over his crown is 53 px from the top, so the 72 px badge stood with its top quarter out of the view
# (playtest 2026-10-04). Pushed down onto his crest instead.
func _tell_anchor() -> Vector2:
	var at: Vector2 = body.tell_anchor(&"yell_tell")
	return Vector2(at.x, maxf(at.y, badge_floor()))


# The lowest the badge's tip may stand: its whole height (the dodge tell's pivot over its bottom, drawn at its
# scale, or the stand-in ring's diameter) under the top of the screen.
static func badge_floor() -> float:
	var spec := DefenseHypeArtLayout.dodge_tell()
	if spec.has("pivot"):
		return spec.pivot.y * spec.scale + BADGE_TOP_MARGIN
	return 2.0 * spec.radius + spec.width + BADGE_TOP_MARGIN


func _blast() -> void:
	yell = Yell.BLAST
	yell_clock = 0.0
	ParryTell.clear(body)
	body.play_anim(&"roar")
	body.play_sfx(&"yell")
	ScreenView.shake(get_tree(), state_machine.yell_shake, YELL_SHAKE_STEPS, YELL_SHAKE_STEP_TIME)
	ring = _blow_ring(state_machine.get_player())
	ring.answered.connect(_on_ring_answered)


# One ring of sound off his roaring mouth, at the yell's size: at `target`, or at nobody.
func _blow_ring(target: Node2D) -> Node2D:
	var blown: Node2D = RING_SCENE.instantiate()
	blown.player = target
	blown.start_radius = state_machine.yell_start_radius
	blown.end_radius = state_machine.yell_radius
	blown.band = state_machine.yell_band
	blown.expand_time = state_machine.yell_expand_time
	blown.landing_time = state_machine.yell_landing_time
	state_machine.add_hazard(blown, body.mouth_point(&"roar"), body.projectile_layer)
	return blown


# The ring's one answer. A hit throws the player unless it killed them, and ends the window; a dodge is a
# miss like any other and waits for the after-pose.
func _on_ring_answered(result: int) -> void:
	yell_result = result
	if result != HitInfo.Result.HIT:
		return
	var player: Node2D = state_machine.get_player()
	if player != null and player.playerHealth > 0:
		body.launch_player(player, launch_point(player.global_position))
	state_machine.idle_after_yell()


# The far side of the ring on the player's side of his mouth, pushed on along the line they were
# thrown down, inside the ropes.
func launch_point(from: Vector2) -> Vector2:
	var mouth: Vector2 = body.mouth_point(&"roar")
	var x: float = state_machine.launch_left_x if from.x < mouth.x else state_machine.launch_right_x
	var y: float = from.y + state_machine.launch_follow * (from.y - mouth.y)
	return Vector2(x, clampf(y, state_machine.launch_y_range.x, state_machine.launch_y_range.y))


#THE SCREAM

# Every punch that lands: one on him outside the yell, short of the POW, starts the watch, and anything
# else ends it.
func _on_punch_landed(target: Node, _dealt: int, charged: bool) -> void:
	combo_watched = target == body and not charged and not is_yelling()


# A swing that reached nothing, or one refused, while the watch is on.
func _on_punch_missed() -> void:
	if not combo_watched or is_yelling() or scream_due or not state_machine.scream_on_miss:
		return
	combo_watched = false
	scream_due = true
	_scream.call_deferred()


func _on_punch_refused(_target: Node) -> void:
	_on_punch_missed()


func _scream() -> void:
	if released or not scream_due:
		return
	scream_due = false
	screams += 1
	combo.reset()
	body.play_anim(&"roar")
	body.play_sfx(&"yell")
	ScreenView.shake(get_tree(), state_machine.yell_shake, YELL_SHAKE_STEPS, YELL_SHAKE_STEP_TIME)
	_blow_ring(null)
	var player: Node2D = state_machine.get_player()
	if player != null and player.playerHealth > 0:
		var to := scream_point(player.global_position, player.ring_origins)
		if to != player.global_position:
			body.launch_player(player, to)
	state_machine.idle_after_yell()


# Where the scream leaves a player standing at `from`: straight away from his mouth to scream_clear px
# from it, on whole px inside `inside`, the ring's floor for their origin. A rope in the way turns the push
# along it, as little as still clears him; a player already that far off is left where they are.
func scream_point(from: Vector2, inside: Rect2) -> Vector2:
	var mouth: Vector2 = body.mouth_point(&"roar")
	var clear: float = state_machine.scream_clear
	if from.distance_to(mouth) >= clear:
		return from
	var away := Vector2.DOWN if from.is_equal_approx(mouth) else (from - mouth).normalized()
	var best := from
	for step in SCREAM_TURNS + 1:
		for turn in ([0] if step == 0 else [step, -step]):
			var to := (mouth + away.rotated(deg_to_rad(turn * SCREAM_TURN_STEP)) * clear).round() \
				.clamp(inside.position.ceil(), inside.end.floor())
			if to.distance_to(mouth) > best.distance_to(mouth):
				best = to
		if best.distance_to(mouth) >= clear - 1.0:
			return best
	return best


# Nothing landed: the window carries on with what it had left and the bonus, and its punches count
# again from nothing.
func _missed() -> void:
	yell = Yell.NONE
	yell_clock = 0.0
	if is_instance_valid(ring) and ring.answered.is_connected(_on_ring_answered):
		ring.answered.disconnect(_on_ring_answered)
	ring = null
	body.hits_this_window = 0
	var left := recover_timer.time_left
	recover_timer.paused = false
	recover_timer.start(left + state_machine.yell_whiff_bonus)
	body.play_state_anim(&"recover")


func _on_recover_timer_timeout() -> void:
	state_machine.on_child_transition(self, "Idle")
