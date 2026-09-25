extends State

# Danny's Attack 2, the Sumo Smash string (plan section 4; SF6 E. Honda's Sumo Smash): he crouches, leaps and
# hangs over the ring tracking the player, then latches and comes down rear first on the marked spot. Five
# landings 0.90 s apart, each its own hit (DannyBossSlamHit) and a quake ring rolling out from under it
# (DannyBossQuakeRingScript), then his nap (DannyBossStateMachine.attack_done).
#
# THE BEATS, in seconds (landings at 1.45, 2.35, 3.25, 4.15 and 5.05):
#   CROUCH  0.30              jump_crouch, facing the player: the tell.
#   LAUNCH  0.30              jump_launch. The lift and the tracking start on its lift-off frame (the artist's
#                             f2) and he rises to hover_height with an ease-out, the mark coming up under him.
#   TRACK   0.45, then 0.22   the tuck (air) at hover_height, the spot he'll land on chasing the player's feet at
#                             track_speed, the mark flickering on it.
#   LATCH   0.12              the spot holds, and the red badge stands over it until the landing, 0.40 s.
#   DROP    0.28              slam_drop, lifted hover_height * (1 - p^drop_ease), the mark growing to full size.
#   IMPACT  0.05              slam_impact, the squash: the landing resolves on the player on its first step,
#                             then everything it sets off; held three steps so it reads.
#   REBOUND 0.05, RISE 0.18   after the first four: slam_rebound on the mat (the plan's 0.10 less the squash),
#                             then the tuck rising back to hover_height with the tracking on again.
#   SETTLE  0.35              after the fifth: slam_impact held, and a player sat in his footprint is slid out
#                             beside him.
# It all runs on one clock against that schedule, worked out as he enters, so no landing drifts off the beat
# whatever length a step is. After the fifth the squash is the settle's own pose.
#
# FAIRNESS: landing to landing is 0.90 s, over AttackCatalog.DASH_IMMUNITY_COOLDOWN and a dash's lead, so a
# dash can answer every one (EricBarbaricLeap's rule), and inside the player's 1.0 s i-frames, so a hit buys
# the next landing and a player who does nothing takes three.
#
# HIS LIFT IS ON HIS SPRITE ALONE (DannyBossScript.set_lift): his node, hurtbox and y-sort stay on the spot
# he'll land on, placed so the slam sheet's rear contact texel comes down on it.
#
# STUCK MEANS NO PARRY, AND EVERY LANDING LEAVES WORMS (the user's pick after the 2026-09-24 playtest, where a
# player could parry the string standing still). Each of the first four landings leaves a fresh puddle on its
# spot once it has resolved (DannyBossSlamPuddle), which arms puddle_grace later: parry, then step off. A root
# taken in the string, from any puddle, seals the parry as well - the Computah trap's seal, lock_actions_sealed()
# - so the next landing can only land; the popup says STUCK!, a parry pressed then only squelches, and no badge
# asks for a parry that can't be made. The root lets go as before. The fifth leaves none: it is his nap, and
# the floor round him is cleared then, so the nap is always there to punish (_clear_nap_floor).
#
# RELEASE: the mark and his lift go back through release(), which Exit(), _exit_tree() and
# DannyBossStateMachine._stop_everything() call. It starts no tween: _exit_tree() can come as the fight scene
# is torn down, when the badge and the bar are already out of the tree. _stop_everything() clears the badge
# and brings the bar back itself, and what the landings left on the mat is in the hazard group it clears.

const Layout := preload("res://Scripts/DannyBossArtLayout.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const HitStop := preload("res://Scripts/HitStop.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const SlamMark := preload("res://Scripts/DannyBossSlamMark.gd")
const SlamHit := preload("res://Scripts/DannyBossSlamHit.gd")
const QuakeRing := preload("res://Scripts/DannyBossQuakeRingScript.gd")
const BossBroken := preload("res://Scripts/BossBroken.gd")
const SlamPuddle := preload("res://Scripts/DannyBossSlamPuddle.gd")

enum Beat { CROUCH, LAUNCH, TRACK, LATCH, DROP, IMPACT, REBOUND, RISE, SETTLE, DONE }

# Summed steps land a hair short of a scheduled time, which would start its beat a step late.
const STEP_TOLERANCE := 0.0001
const IMPACT_SHAKE_STEPS := 4
const IMPACT_SHAKE_STEP := 0.04

@export var body : CharacterBody2D

# squash_time + rebound_time + rise_time + track_time + latch_time + drop_time is landing to landing: keep it over
# AttackCatalog.DASH_IMMUNITY_COOLDOWN and a dash's lead, and under the player's i-frames.
@export var slams := 5
@export var crouch_time := 0.30
@export var launch_time := 0.30
@export var first_track_time := 0.45
@export var track_time := 0.22
@export var latch_time := 0.12
@export var drop_time := 0.28
@export var squash_time := 0.05
@export var rebound_time := 0.05
@export var rise_time := 0.18
@export var settle_time := 0.35
@export var hover_height := 380.0
@export var track_speed := 1100.0
# 1.0 to 1.5: higher keeps him up longer and brings him down faster at the end.
@export var drop_ease := 1.0
@export var ring_speed := 240.0
@export var impact_shake := 14.0
@export var parry_hit_stop := 0.06
# The badge's tip over the marked spot.
@export var badge_rise := 150.0
# The impact's cracks stay on the mat this long, then fade out.
@export var cracks_hold := 0.6
@export var cracks_fade := 0.4
# Every landing parried or dodged.
@export var clean_hype := 10.0
@export var clean_cheer := 2.0
@export var nudge_time := 0.18
# A landing's puddle arms this long after it: the time to step off after a parry.
@export var puddle_grace := 0.40
# The squelch of a parry pressed while stuck.
@export var squelch_pitch := 1.35
# The nap's open-floor check (coder B's in danny_spit): the floor in way_cell squares, open where a square keeps
# way_clearance from every trigger, and the spots beside him a punch is thrown from.
@export var way_cell := 16.0
@export var way_clearance := 32.0
@export var punch_side := Vector2(190, 3)

@onready var state_machine = get_parent()

# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
var clock := 0.0
# [seconds from Enter, Beat, which slam], in order.
var schedule: Array = []
var next_entry := 0
var beat := Beat.CROUCH
var beat_start := 0.0
var slam := 0
# How far into the launch its lift-off frame comes.
var liftoff := 0.0
# Where his rear contact texel comes down, and from there to his node.
var target := Vector2.ZERO
var contact_offset := Vector2.ZERO
var mark: Node2D
var player: Node2D
# For a test: each landing as it resolved, when each latch and landing came on this state's clock, whether
# every landing so far was parried or dodged, and whether the player was slid out of his footprint.
var results: Array[Dictionary] = []
var latch_times: Array[float] = []
var impact_times: Array[float] = []
var clean := true
var nudged := false
# The root whose parry this string sealed.
var sealed_root: Node
# For a test: the puddles the landings left, when each root in the string sealed the parry, the landings whose
# badge was withheld from a stuck player, the STUCK! words and the squelches, and at the nap how many puddles
# the floor round him took and whether the string's own had to go for a way to him.
var puddles_left: Array = []
var seal_times: Array[float] = []
var badges_withheld: Array[int] = []
var stuck_words := 0
var squelches := 0
var nap_cleared := 0
var way_opened := false


func Enter() -> void:
	released = false
	clock = 0.0
	next_entry = 0
	slam = 0
	results.clear()
	latch_times.clear()
	impact_times.clear()
	clean = true
	nudged = false
	sealed_root = null
	puddles_left.clear()
	seal_times.clear()
	badges_withheld.clear()
	stuck_words = 0
	squelches = 0
	nap_cleared = 0
	way_opened = false
	player = state_machine.get_player()
	liftoff = liftoff_delay()
	body.velocity = Vector2.ZERO
	body.show_body()
	body.set_hurtbox_active(false)
	body.set_body_box(&"idle")
	body.face_toward(state_machine.player_feet())
	contact_offset = body.global_position - body.contact_point(&"slam_impact")
	target = body.contact_point(&"slam_impact")
	schedule = _schedule()
	_run_due()


func Physics_Update(delta: float) -> void:
	if released:
		return
	clock += delta
	_seal_if_rooted()
	_run_due()
	if released:
		return
	_step(delta)


func Exit() -> void:
	release()


func _exit_tree() -> void:
	release()


func release() -> void:
	if released:
		return
	released = true
	_free_mark()
	if is_instance_valid(body):
		body.set_lift(0.0)


#THE SCHEDULE

func _schedule() -> Array:
	var entries := []
	var at := 0.0
	entries.append([at, Beat.CROUCH, 1])
	at += crouch_time
	entries.append([at, Beat.LAUNCH, 1])
	at += launch_time
	for k in range(1, slams + 1):
		entries.append([at, Beat.TRACK, k])
		at += first_track_time if k == 1 else track_time
		entries.append([at, Beat.LATCH, k])
		at += latch_time
		entries.append([at, Beat.DROP, k])
		at += drop_time
		entries.append([at, Beat.IMPACT, k])
		if k < slams:
			at += squash_time
			entries.append([at, Beat.REBOUND, k])
			at += rebound_time
			entries.append([at, Beat.RISE, k])
			at += rise_time
		else:
			entries.append([at, Beat.SETTLE, k])
			at += settle_time
	entries.append([at, Beat.DONE, slams])
	return entries


# Every beat that is due, in order, stopping after a landing: the fifth's settle, due with it, starts a step
# later with the squash already showing.
func _run_due() -> void:
	while not released and next_entry < schedule.size() and clock >= schedule[next_entry][0] - STEP_TOLERANCE:
		var entry: Array = schedule[next_entry]
		next_entry += 1
		_begin(entry[1], entry[2], entry[0])
		if entry[1] == Beat.IMPACT:
			return


func _begin(new_beat: int, number: int, at: float) -> void:
	beat = new_beat
	beat_start = at
	slam = number
	match new_beat:
		Beat.CROUCH:
			body.play_anim(&"jump_crouch")
		Beat.LAUNCH:
			body.play_anim(&"jump_launch")
			body.play_sfx(&"jump")
			_raise_mark()
		Beat.TRACK, Beat.RISE:
			body.play_anim(&"air")
		Beat.LATCH:
			latch_times.append(clock)
			if _sealed():
				badges_withheld.append(number)
			else:
				ParryTell.telegraph(body, SlamHit.SLAM_ID, latch_time + drop_time, _badge_point)
		Beat.DROP:
			body.play_anim(&"slam_drop")
		Beat.IMPACT:
			_land()
		Beat.REBOUND:
			body.play_anim(&"slam_rebound")
		Beat.SETTLE:
			_settle()
		Beat.DONE:
			body.restore_hud()
			state_machine.attack_done(self)


func _step(delta: float) -> void:
	var t := clock - beat_start
	var lift := 0.0
	match beat:
		Beat.LAUNCH:
			if t >= liftoff:
				lift = hover_height * _ease_out((t - liftoff) / maxf(launch_time - liftoff, 0.001))
				_track(delta)
		Beat.TRACK:
			lift = hover_height
			_track(delta)
		Beat.LATCH:
			lift = hover_height
		Beat.DROP:
			lift = hover_height * (1.0 - pow(clampf(t / drop_time, 0.0, 1.0), drop_ease))
		Beat.RISE:
			lift = hover_height * _ease_out(t / rise_time)
			_track(delta)
	body.set_lift(lift)
	if is_instance_valid(mark):
		if beat == Beat.TRACK or beat == Beat.LATCH:
			mark.hover()
		else:
			mark.set_height(lift)
	body.update_hud_fade_at(body.crown_point())


#IN THE AIR

# The spot he'll land on chases the player's feet, as far as his feet may go.
func _track(delta: float) -> void:
	var walk: Rect2 = state_machine.WALK_RECT
	var goal: Vector2 = state_machine.player_feet().clamp(walk.position, walk.end)
	target = target.move_toward(goal, track_speed * delta)
	_place()


func _place() -> void:
	body.global_position = (target + contact_offset).round()
	if is_instance_valid(mark):
		mark.global_position = target.round()


func _raise_mark() -> void:
	_free_mark()
	mark = SlamMark.new()
	mark.name = "SlamMark"
	mark.full_height = hover_height
	state_machine.add_hazard(mark, target, body.floor_layer)


func _free_mark() -> void:
	if is_instance_valid(mark):
		mark.queue_free()
	mark = null


func _badge_point() -> Vector2:
	return target + Vector2(0, -badge_rise)


# Into the launch's last frame, its lift-off: his leap to the gate at 0 HP leaves the mat on it too.
static func liftoff_delay() -> float:
	var spec := Layout.anim(&"jump_launch")
	var times: Array = spec.times
	var delay := 0.0
	for i in spec.frames.size() - 1:
		delay += times[mini(i, times.size() - 1)]
	return delay


func _ease_out(x: float) -> float:
	var left := 1.0 - clampf(x, 0.0, 1.0)
	return 1.0 - left * left


#THE LANDING

func _land() -> void:
	ParryTell.clear(body)
	body.set_lift(0.0)
	body.play_anim(&"slam_impact")
	_place()
	impact_times.append(clock)
	var hit := SlamHit.new()
	hit.player = player
	hit.boss = body
	state_machine.add_hazard(hit, target, body.floor_layer)
	results.append({"result": hit.result, "feet_inside": hit.feet_inside, "ghost_inside": hit.ghost_inside})
	var answered := hit.result == HitInfo.Result.PARRIED or hit.result == HitInfo.Result.DODGED
	clean = clean and (answered or (hit.ghost_inside and not hit.feet_inside))
	if hit.result == HitInfo.Result.PARRIED:
		body.play_sfx(&"slam_bonk")
		HitStop.freeze(get_tree(), parry_hit_stop)
	# Only now the landing has had its say on the player does a root sprung in the string let go.
	state_machine.release_root()
	body.play_sfx(&"butt_slam")
	ScreenView.shake(get_tree(), impact_shake, IMPACT_SHAKE_STEPS, IMPACT_SHAKE_STEP)
	state_machine.splat_puddles_in(target, SlamHit.RADII.x, SlamHit.RADII.y)
	if slam < slams:
		_leave_puddle()
	play_impact(state_machine, body, target, cracks_hold, cracks_fade)
	var ring := QuakeRing.new()
	ring.player = hit.player
	ring.speed = ring_speed
	ring.spared = hit.feet_inside
	state_machine.add_hazard(ring, target, body.ring_layer)
	if is_instance_valid(mark):
		mark.set_height(0.0)


# The flash and the dust burst over both fighters where his rear came down at `at`, then the cracks alone on
# the mat under him, held and faded. His leap to the gate at 0 HP lands the same way (DannyBossSumo).
static func play_impact(fight: Node, danny: Node2D, at: Vector2, hold: float, fade: float) -> void:
	var spec := Layout.fx(&"slam_impact")
	var cracks_frame: int = spec.cracks_frame
	var burst := _fx_sprite(spec, 0)
	fight.add_hazard(burst, at, danny.projectile_layer)
	var cracks := _fx_sprite(spec, cracks_frame)
	cracks.visible = false
	fight.add_hazard(cracks, at, danny.floor_layer)
	var play := burst.create_tween()
	for i in range(1, cracks_frame):
		play.tween_interval(spec.frame_time)
		play.tween_callback(burst.set_frame.bind(i))
	play.tween_interval(spec.frame_time)
	play.tween_callback(burst.queue_free)
	var lie := cracks.create_tween()
	lie.tween_interval(spec.frame_time * cracks_frame)
	lie.tween_callback(cracks.show)
	lie.tween_interval(hold)
	lie.tween_property(cracks, "modulate:a", 0.0, fade)
	lie.tween_callback(cracks.queue_free)


static func _fx_sprite(spec: Dictionary, frame: int) -> Sprite2D:
	var fx := Sprite2D.new()
	fx.texture = load(spec.texture)
	fx.hframes = spec.hframes
	fx.frame = frame
	fx.offset = spec.offset
	fx.scale = Vector2.ONE * Layout.SCALE
	return fx


# The fifth landing: the mark's done, a clean string pays, and a player sat in his footprint is slid out of it.
func _settle() -> void:
	_free_mark()
	if clean:
		body.add_player_hype(clean_hype)
		get_tree().call_group("arena_crowd", "cheer", clean_cheer)
	_clear_nap_floor()
	_nudge()


# Beside the box his nap is about to take up, on their own side of it, so it doesn't start with them inside him.
# By a rope his nap can reach past it, leaving no floor on their side: then it is the other side, as BossBroken's
# drive does it, and on the floor either way.
func _nudge() -> void:
	if not is_instance_valid(player):
		return
	var feet: Vector2 = state_machine.player_feet()
	if ((feet - target) / SlamHit.RADII).length_squared() > 1.0:
		return
	var box: Rect2 = body.body_box_rect(&"sleep")
	var side := 1.0 if player.global_position.x >= box.get_center().x else -1.0
	var area: Rect2 = BossBroken.PLAYER_AREA
	var spot: Vector2 = state_machine.spot_beside(box, side)
	if not area.has_point(spot):
		spot = state_machine.spot_beside(box, -side)
	state_machine.drive_player_to(spot.clamp(area.position, area.end), nudge_time)
	nudged = true


#STUCK AND THE WORMS

# A root taken in the string, from any puddle, takes the parry with it until it lets go (unlock_actions lifts
# both): the popup says why, and a badge up for the landing coming goes.
func _seal_if_rooted() -> void:
	# Untyped: a root that let go by itself outside the string can be freed and still held there.
	var root = state_machine.root
	if not is_instance_valid(root) or root == sealed_root or root.released or not is_instance_valid(player):
		return
	sealed_root = root
	player.lock_actions_sealed()
	seal_times.append(clock)
	if beat == Beat.LATCH or beat == Beat.DROP:
		ParryTell.clear(body)
		badges_withheld.append(slam)
	var popups: Node = player.get_parent().get_node_or_null(^"CanvasLayer/CombatPopups")
	if popups != null and popups.has_method("show_popup"):
		popups.show_popup(&"stuck")
		stuck_words += 1


func _sealed() -> bool:
	return is_instance_valid(sealed_root) and not sealed_root.released and is_instance_valid(player) \
		and player.lock_seals_guard


# The player's own input is sealed; this is only the squelch that says so.
func _input(event: InputEvent) -> void:
	if released or not _sealed() or not event.is_action_pressed(&"block"):
		return
	body.play_sfx(&"glob_splat", squelch_pitch)
	squelches += 1


func _leave_puddle() -> void:
	var puddle: Node2D = SlamPuddle.new()
	puddle.player = player
	puddle.body = body
	puddle.state_machine = state_machine
	puddle.arm_grace = puddle_grace
	state_machine.add_hazard(puddle, target, body.floor_layer)
	state_machine.register_puddle(puddle)
	puddles_left.append(puddle)


# The floor round his feet as a spit keeps it clear (its radii and clear_of_danny), and then, if the puddles
# still wall the player off from both of his sides, the string's own puddles go too: a spit's alone always leave
# the floor one piece.
func _clear_nap_floor() -> void:
	var spit: Node = state_machine.states["Spit"]
	var feet: Vector2 = body.global_position
	var around: Vector2 = spit.radii + spit.clear_of_danny
	for puddle in state_machine.live_puddles():
		if ((puddle.global_position - feet) / around).length_squared() < 1.0:
			puddle.splat()
			nap_cleared += 1
	if not is_instance_valid(player) or way_to_sides(state_machine.player_feet(), feet):
		return
	for puddle in puddles_left:
		if is_instance_valid(puddle) and not puddle.gone:
			puddle.splat()
	way_opened = true


# Whether the open floor leads from `from` to a side of `danny` to punch him from. Squares are opened as the
# search reaches them; feet within way_clearance of a trigger start from the open squares round them.
func way_to_sides(from: Vector2, danny: Vector2) -> bool:
	var ropes: Rect2 = state_machine.ROPES
	var size := Vector2i((ropes.size / way_cell).floor())
	var triggers: Array = []
	for puddle in state_machine.live_puddles():
		triggers.append([puddle.global_position, puddle.radii + Vector2.ONE * way_clearance])
	# 0 not looked at yet, 1 open, 2 shut.
	var state := PackedByteArray()
	state.resize(size.x * size.y)
	var is_open := func(cell: Vector2i) -> bool:
		var index := cell.y * size.x + cell.x
		if state[index] == 0:
			var at: Vector2 = ropes.position + (Vector2(cell) + Vector2(0.5, 0.5)) * way_cell
			state[index] = 1
			for trigger in triggers:
				if ((at - trigger[0]) / trigger[1]).length_squared() < 1.0:
					state[index] = 2
					break
		return state[index] == 1
	var cell_of := func(point: Vector2) -> Vector2i:
		return Vector2i(((point - ropes.position) / way_cell).floor()).clamp(Vector2i.ZERO, size - Vector2i.ONE)
	var goals := {}
	for side in [-1.0, 1.0]:
		var spot: Vector2 = danny + Vector2(punch_side.x * side, punch_side.y)
		if ropes.has_point(spot):
			goals[cell_of.call(spot)] = true
	var start: Vector2i = cell_of.call(from)
	var reach := int(ceil(way_clearance / way_cell)) + 1
	var queue: Array[Vector2i] = []
	var seen := {}
	for dy in range(-reach, reach + 1):
		for dx in range(-reach, reach + 1):
			var cell: Vector2i = (start + Vector2i(dx, dy)).clamp(Vector2i.ZERO, size - Vector2i.ONE)
			if not seen.has(cell) and is_open.call(cell):
				seen[cell] = true
				queue.append(cell)
	var head := 0
	while head < queue.size():
		var cell: Vector2i = queue[head]
		head += 1
		if goals.has(cell):
			return true
		for step in [Vector2i.RIGHT, Vector2i.LEFT, Vector2i.DOWN, Vector2i.UP]:
			var next: Vector2i = cell + step
			if next.x < 0 or next.y < 0 or next.x >= size.x or next.y >= size.y or seen.has(next):
				continue
			seen[next] = true
			if is_open.call(next):
				queue.append(next)
	return false
