extends State

# The Kaiju Stomp (scratchpad jordan_kaiju/PLAN.md section 3; Danny's big slam, DannyBossSlams): Jordan throws his
# figures down, the kaiju rears and leaps off the top of the screen, its shadow (JordanStompMark) hunts the player,
# latches under a strong red badge and it lands foot first (JordanStompHit).
#   PARRIED  it stumbles back onto one knee and Jordan tumbles off onto the mat beside the player: Dismounted. Any
#            burn line still alight goes out; no ring.
#   HIT      it settles, then hops home.
#   DODGED   (or stepped out of) a quake ring rolls out from it (BixbyQuakeRingScript with its settings), sparing a
#            player whose feet were inside the footprint, and now and then the tail whips round (JordanTailSweep,
#            yellow); never after a hit or a parry.
# Under half health a stomp that wasn't parried is followed at once by a second, from where it landed.
# A Break while it is in the air waits for the landing, which then hurts nobody: it crash-lands, collapses, and Jordan
# is thrown off into his Broken (JordanStateMachine.break_now).
#
# Its lift is on its art alone (JordanKaiju.set_lift); its node stands where its front foot will come down. One
# clock from Enter; release() on Exit and _exit_tree. JordanStateMachine builds it when the kaiju is on.

const KaijuLayout := preload("res://Scripts/JordanKaijuLayout.gd")
const JordanArtLayout := preload("res://Scripts/JordanArtLayout.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const HitStop := preload("res://Scripts/HitStop.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const StompMark := preload("res://Scripts/JordanStompMark.gd")
const StompHit := preload("res://Scripts/JordanStompHit.gd")
const TailSweep := preload("res://Scripts/JordanTailSweep.gd")
const QuakeRing := preload("res://Scripts/BixbyQuakeRingScript.gd")

enum Beat { THROW, REAR, LEAP, TRACK, LATCH, DROP, STUMBLE, SETTLE, TAIL_WINDUP, TAIL_SPIN, TAIL_RECOVER, RETURN, CRASH, DONE }

const STOMP_ID := &"jordan_kaiju_stomp"
const TAIL_ID := &"jordan_kaiju_tail"
const QUAKE_ID := &"jordan_kaiju_quake"
const SHAKE_STEPS := 4
const SHAKE_STEP := 0.04
# Where the player's feet can be: the mark hunts them anywhere on it.
const FEET_AREA := Rect2(131, 186, 1656, 761)

@export var throw_windup := 0.40
@export var rear_at := 1.40
@export var rear_time := 0.50
@export var leap_time := 0.30
@export var track_until := 4.40
@export var latch_time := 0.20
@export var drop_time := 0.22
@export var track_speed := 1100.0
@export var latch_lead := 0.30
@export var badge_rise := 150.0
@export var badge_slack := 0.05
@export var parry_hit_stop := 0.08
@export var stumble_time := 0.45
@export var stumble_push := 100.0
@export var topple_time := 0.55
@export var topple_arc := 160.0
# His topple's peak no higher than this: off a seat out on the mat it would otherwise fly him over the top rope.
@export var topple_top := 140.0
@export var settle_time := 0.5
@export var tail_chance := 0.35
@export var tail_chance_b := 0.70
@export var tail_windup := 0.40
@export var tail_spin := 0.70
@export var tail_lead := 0.30
@export var tail_recover := 0.3
@export var second_crouch := 0.30
@export var second_launch := 0.30
@export var second_track := 0.90
@export var ring_start := 160.0
@export var ring_speed := 520.0
@export var ring_max := 900.0
@export var ring_die := 0.25
@export var impact_shake := 18.0
# The impact's cracks stay on the mat this long once its burst has played, then fade (its sheet's f5 held).
@export var cracks_hold := 0.6
@export var cracks_fade := 0.4
@export var crash_time := 0.30

var body: CharacterBody2D
var hurtbox: Area2D
var state_machine: Node

# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
var clock := 0.0
var beat := Beat.THROW
var beat_at := 0.0
var phase_b := false
var stomps := 1
var stomp := 1
var thrown := false
var track_end := 0.0
var target := Vector2.ZERO
var mark: Node2D
var tail: Node2D
var break_queued := false
var player: Node2D
var stumble_from := Vector2.ZERO
var stumble_to := Vector2.ZERO
var topple_from := Vector2.ZERO
var topple_to := Vector2.ZERO
var return_from := Vector2.ZERO
var tail_due := false
# For a test: each landing as it resolved, the latch and impact times on this clock, the rings and tails sent, and
# where he was knocked off to.
var results: Array[Dictionary] = []
var latch_times: Array[float] = []
var impact_times: Array[float] = []
var rings: Array[Node2D] = []
var tails: Array[Node2D] = []
var knocked_to := Vector2.INF
var crashed := false
var throw_id := -1


func Enter() -> void:
	released = false
	clock = 0.0
	thrown = false
	break_queued = false
	crashed = false
	knocked_to = Vector2.INF
	results.clear()
	latch_times.clear()
	impact_times.clear()
	rings.clear()
	tails.clear()
	phase_b = state_machine.phase_b
	stomps = 2 if phase_b else 1
	stomp = 1
	tail_due = false
	player = state_machine.get_player()
	_begin(Beat.THROW)
	state_machine.kaiju.play_anim(&"idle")
	body.play_anim(&"ride_throw", &"ride_idle")


func Exit() -> void:
	release()


func _exit_tree() -> void:
	release()


func release() -> void:
	if released:
		return
	released = true
	_free_mark()
	var kaiju: Node2D = state_machine.kaiju if is_instance_valid(state_machine) else null
	if is_instance_valid(kaiju):
		ParryTell.clear(kaiju)


# In the air: a Break waits for the landing (JordanStateMachine.enter_broken). Returns whether it took it.
func queue_break() -> bool:
	if released or state_machine.kaiju.lift <= 0.0:
		return false
	break_queued = true
	return true


func airborne() -> bool:
	return not released and state_machine.kaiju.lift > 0.0


func Physics_Update(delta: float) -> void:
	if released:
		return
	clock += delta
	if not thrown and clock >= throw_windup:
		thrown = true
		throw_id = state_machine.throw_funkos(1)
	var t := clock - beat_at
	var kaiju: Node2D = state_machine.kaiju
	match beat:
		Beat.THROW:
			if clock >= rear_at:
				_rear()
		Beat.REAR:
			if t >= _rear_length():
				_begin(Beat.LEAP)
				kaiju.play_anim(&"leap")
				body.play_anim(&"ride_brace")
				state_machine.play_sfx(&"leap")
				_raise_mark()
		Beat.LEAP:
			var p := minf(t / _leap_length(), 1.0)
			kaiju.set_lift(KaijuLayout.LEAP_HEIGHT * p * p)
			_track(delta)
			if p >= 1.0:
				_begin(Beat.TRACK)
				mark.hover()
		Beat.TRACK:
			_track(delta)
			if clock >= track_end:
				_latch()
		Beat.LATCH:
			if t >= latch_time:
				_begin(Beat.DROP)
				kaiju.play_anim(&"drop")
		Beat.DROP:
			var p := minf(t / drop_time, 1.0)
			var lift := KaijuLayout.LEAP_HEIGHT * (1.0 - p * p)
			kaiju.set_lift(lift)
			# Its stomping foot moves from frame to frame: kept over the mark.
			_place()
			mark.set_height(lift / KaijuLayout.LEAP_HEIGHT)
			if p >= 1.0:
				_land()
		Beat.STUMBLE:
			_step_stumble(t)
		Beat.SETTLE:
			if t >= settle_time:
				_after_landing()
		Beat.TAIL_WINDUP:
			if t >= tail_windup:
				_spin_tail()
		Beat.TAIL_SPIN:
			if t >= tail_spin:
				_begin(Beat.TAIL_RECOVER)
				kaiju.play_anim(&"idle")
		Beat.TAIL_RECOVER:
			if t >= tail_recover:
				_start_return()
		Beat.RETURN:
			if state_machine.step_return(t, return_from):
				if break_queued:
					_crash()
				else:
					_done()
		Beat.CRASH:
			if t >= crash_time:
				_done_into_break()
	kaiju.update_hud_fade()


func _begin(new_beat: int) -> void:
	beat = new_beat
	beat_at = clock


func _rear_length() -> float:
	return rear_time if stomp == 1 else second_crouch


func _leap_length() -> float:
	return leap_time if stomp == 1 else second_launch


func _rear() -> void:
	_begin(Beat.REAR)
	state_machine.kaiju.play_anim(&"rear")
	body.play_anim(&"ride_brace")
	state_machine.play_sfx(&"roar")


#IN THE AIR

# The spot it will land on chases the player's feet: from the front foot's spot at home, anywhere they can stand.
func _raise_mark() -> void:
	_free_mark()
	var kaiju: Node2D = state_machine.kaiju
	target = kaiju.feet_point() + kaiju.foot_offset()
	track_end = clock + _leap_length() + (track_until - rear_at - rear_time - leap_time if stomp == 1 else second_track)
	mark = StompMark.new()
	mark.name = "StompMark"
	state_machine.add_floor_hazard(mark, target)


func _track(delta: float) -> void:
	var goal: Vector2 = state_machine.player_feet().clamp(FEET_AREA.position, FEET_AREA.end)
	target = target.move_toward(goal, track_speed * delta)
	_place()


func _place() -> void:
	var kaiju: Node2D = state_machine.kaiju
	kaiju.place(target - kaiju.foot_offset())
	if is_instance_valid(mark):
		mark.global_position = target.round()


# The spot jumps to where the player is heading and holds, and the red badge goes up over it.
func _latch() -> void:
	_begin(Beat.LATCH)
	latch_times.append(clock)
	var velocity: Vector2 = player.velocity if is_instance_valid(player) else Vector2.ZERO
	var lead: Vector2 = (state_machine.player_feet() + velocity * latch_lead).clamp(FEET_AREA.position, FEET_AREA.end)
	if not KaijuLayout.in_walls(lead):
		target = lead
	_place()
	ParryTell.telegraph(state_machine.kaiju, STOMP_ID, latch_time + drop_time + badge_slack, _badge_point)


func _badge_point() -> Vector2:
	return Vector2(target.x, maxf(target.y - badge_rise, KaijuLayout.BADGE_TOP))


func _free_mark() -> void:
	if is_instance_valid(mark):
		mark.queue_free()
	mark = null


#THE LANDING

func _land() -> void:
	var kaiju: Node2D = state_machine.kaiju
	ParryTell.clear(kaiju)
	kaiju.set_lift(0.0)
	# The landing's own frame first: its foot is where the mark is.
	if break_queued:
		kaiju.play_anim(&"land", &"collapse")
	else:
		kaiju.play_anim(&"stomp")
	_place()
	impact_times.append(clock)
	_free_mark()
	state_machine.play_sfx(&"stomp")
	state_machine.play_sfx(&"stomp_quake")
	ScreenView.shake(get_tree(), impact_shake, SHAKE_STEPS, SHAKE_STEP)
	if break_queued:
		results.append({"result": HitInfo.Result.IGNORED, "feet_inside": false, "crash": true})
		_crash()
		return
	_play_impact()
	var hit := StompHit.new()
	hit.name = "StompHit"
	hit.player = player
	hit.boss = body
	state_machine.add_floor_hazard(hit, target)
	results.append({"result": hit.result, "feet_inside": hit.feet_inside, "ghost_inside": hit.ghost_inside, "at": target})
	if hit.result == HitInfo.Result.PARRIED:
		_knock_off()
		return
	var hit_them: bool = hit.result == HitInfo.Result.HIT
	if not hit_them:
		_send_ring(hit.feet_inside)
	if stomp < stomps:
		stomp += 1
		_rear()
		return
	tail_due = not hit_them and state_machine.rng.randf() < (tail_chance_b if phase_b else tail_chance)
	_begin(Beat.SETTLE)
	if tail_due:
		_after_landing()


func _send_ring(spared: bool) -> void:
	var ring := QuakeRing.new()
	ring.name = "KaijuQuake"
	ring.y_sort_enabled = true
	ring.attack_id = QUAKE_ID
	ring.speed = ring_speed
	ring.radius = ring_start
	ring.max_radius = ring_max
	ring.die_time = ring_die
	ring.player = null if spared else player
	state_machine.add_sorted_hazard(ring, target)
	rings.append(ring)


# Settled: the tail if it's due, or home.
func _after_landing() -> void:
	if tail_due:
		tail_due = false
		_begin(Beat.TAIL_WINDUP)
		state_machine.kaiju.play_anim(&"tail_windup")
		ParryTell.telegraph(state_machine.kaiju, TAIL_ID, tail_windup + tail_lead + badge_slack, _hip_badge)
		return
	_start_return()


func _hip_badge() -> Vector2:
	var hip: Vector2 = state_machine.kaiju.hip_point()
	return Vector2(hip.x, maxf(hip.y - 30.0, KaijuLayout.BADGE_TOP))


func _spin_tail() -> void:
	_begin(Beat.TAIL_SPIN)
	var kaiju: Node2D = state_machine.kaiju
	kaiju.play_anim(&"tail_spin")
	state_machine.play_sfx(&"tail")
	tail = TailSweep.new()
	tail.name = "TailSweep"
	tail.player = player
	tail.boss = body
	tail.spin_time = tail_spin
	tail.direction = 1.0 if TailSweep.drawn_clockwise() or state_machine.rng.randf() < 0.5 else -1.0
	var bearing := TailSweep.bearing_of(state_machine.player_feet(), kaiju.feet_point())
	tail.start_angle = TailSweep.start_for(bearing, tail_lead, tail_spin, tail.direction)
	state_machine.add_floor_hazard(tail, kaiju.feet_point())
	tail.begin()
	tails.append(tail)


func _start_return() -> void:
	_begin(Beat.RETURN)
	return_from = state_machine.kaiju.feet_point()
	body.play_anim(&"ride_idle")


func _done() -> void:
	_begin(Beat.DONE)
	state_machine.kaiju.play_anim(&"idle")
	state_machine.on_child_transition(self, "Idle")


#THE CRASH (a Break that came in the air)

func _crash() -> void:
	_begin(Beat.CRASH)
	crashed = true
	state_machine.kaiju.set_lift(0.0)
	state_machine.kaiju.play_anim(&"land", &"collapse")


func _done_into_break() -> void:
	_begin(Beat.DONE)
	state_machine.break_now()


#THE KNOCK-OFF (parried)

# Back onto one knee, away from the player, and Jordan off its head onto the mat beside them; every line of fire out.
func _knock_off() -> void:
	_begin(Beat.STUMBLE)
	HitStop.freeze(get_tree(), parry_hit_stop)
	state_machine.put_out_burns()
	var kaiju: Node2D = state_machine.kaiju
	kaiju.play_anim(&"stumble", &"kneel")
	stumble_from = kaiju.feet_point()
	var away: Vector2 = stumble_from - state_machine.player_feet()
	if away.length() < 1.0:
		away = Vector2.LEFT
	stumble_to = (stumble_from + Vector2(signf(away.x) if away.x != 0.0 else -1.0, 0.0) * stumble_push).clamp(
		KaijuLayout.ROPES.position, KaijuLayout.ROPES.end)
	topple_from = kaiju.seat_point()
	topple_to = state_machine.knock_off_spot()
	knocked_to = topple_to
	state_machine.set_mounted(false)
	body.play_anim(&"topple")
	state_machine.play_sfx(&"bonk")


func _step_stumble(t: float) -> void:
	var kaiju: Node2D = state_machine.kaiju
	var s := minf(t / stumble_time, 1.0)
	kaiju.place(stumble_from.lerp(stumble_to, 1.0 - (1.0 - s) * (1.0 - s)))
	var w := minf(t / topple_time, 1.0)
	# His topple sheet: its seat on where he sat, its hips on the arc, its soles on the spot.
	var apex := clampf(topple_from.y - topple_top, 0.0, topple_arc)
	if w >= 1.0 or not body.place_on_arc(topple_from, &"seat", 0, topple_to, &"soles", 5, w, apex):
		var soles := topple_from.lerp(topple_to, w) - Vector2(0, 4.0 * apex * w * (1.0 - w))
		body.global_position = (soles - JordanArtLayout.FLOOR_POINT).round()
	if w >= 1.0 and s >= 1.0:
		_begin(Beat.DONE)
		state_machine.on_child_transition(self, "Dismounted")


# The burst and the cracks under the foot, off its sheet once that is in: every frame but the last played, the last (the
# cracks) held and faded. On the floor layer as a hazard, so a Break takes it with the rest.
func _play_impact() -> void:
	var spec := KaijuLayout.fx(&"stomp_impact")
	if spec.is_empty():
		return
	var fx := Sprite2D.new()
	fx.name = "StompImpact"
	fx.texture = KaijuLayout.texture(spec.sheet)
	fx.hframes = spec.count
	fx.offset = spec.offset
	fx.scale = Vector2.ONE * KaijuLayout.SCALE
	state_machine.add_floor_hazard(fx, target)
	var play := fx.create_tween()
	for i in range(1, spec.count):
		play.tween_interval(spec.times[i - 1])
		play.tween_callback(fx.set_frame.bind(i))
	play.tween_interval(cracks_hold)
	play.tween_property(fx, "modulate:a", 0.0, cracks_fade)
	play.tween_callback(fx.queue_free)
