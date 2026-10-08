extends State

# Danny's Attack 2, the Sumo Smash string (plan section 4; SF6 E. Honda's Sumo Smash), dodge first since Addendum 1:
# he crouches, leaps and hangs over the ring tracking the player, then latches and comes down rear first on the
# marked spot, ten to twelve times (hop_counts; five before the 2026-10-06 tuning, which the beats below still show,
# homing aside). All but the last are hops (danny_hop_slam), yellow, told by the dodge ring and a dashed
# splash zone on the floor: each is its own hit (DannyBossSlamHit) and then its worm splash (DannyBossSplash), which
# roots a player still in the zone, and none sends a quake ring. From the second on they home in (THE HOMING HOPS,
# with the exports): the spot follows the player down until he has all but landed. The last is the big one
# (danny_butt_slam): a longer hang, a longer red read, a heavier drop, and the only quake ring
# (DannyBossQuakeRingScript). Parried, it bounces him off the player's fists onto his back (DannyBossOnBack) instead
# of his nap; anything else ends in his nap (DannyBossStateMachine.attack_done).
#
# THE BEATS, in seconds (landings at 1.45, 2.35, 3.25, 4.15 and 5.45):
#   CROUCH  0.30              jump_crouch, facing the player: the tell.
#   LAUNCH  0.30              jump_launch. The lift and the tracking start on its lift-off frame (the artist's
#                             f2) and he rises to hover_height with an ease-out, the mark coming up under him.
#   TRACK   0.45, then 0.22   the tuck (air) at hover_height, the spot he'll land on chasing the player's feet at
#                             track_speed, the mark flickering on it.
#   LATCH   0.12              the spot holds, and the yellow ring stands over it and the splash zone lies round it
#                             until the landing, 0.40 s.
#   DROP    0.28              slam_drop, lifted hover_height * (1 - p^drop_ease), the mark growing to full size.
#   IMPACT  0.05              slam_impact, the squash: the landing resolves on the player on its first step, then
#                             the splash and everything else it sets off; held three steps so it reads.
#   REBOUND 0.05, RISE 0.18   after the hops: slam_rebound on the mat (the plan's 0.10 less the squash), then the
#                             tuck rising back to hover_height with the tracking on again.
#   The big one: a RISE of big_rise_time after the fourth hop's rebound, a TRACK of big_track_time (the hang), a
#   LATCH of big_latch_time under the strong red badge, a DROP of big_drop_time at big_drop_ease (slower at the
#   start, harder at the end), and IMPACT at 5.45. Then SETTLE 0.35: slam_impact held and a player sat in his
#   footprint slid out beside him, and the nap from 5.80. Or, parried, BOUNCE bounce_time: back_bounce on a
#   bounce_arc arc onto the floor beside the player, and onto his back.
#   A homing hop (the 2026-10-07 tuning): a TRACK of homing_track_time, then its LATCH and DROP as above with the
#   spot still chasing the feet at homing_speed, and the yellow ring, the splash zone and he himself with it, until
#   commit_time before it lands: 1.35 s landing to landing.
# It all runs on one clock against that schedule, worked out as he enters, so no landing drifts off the beat
# whatever length a step is.
#
# FAIRNESS: landing to landing is 0.90 s between the hops, over AttackCatalog.DASH_IMMUNITY_COOLDOWN and a dash's
# lead, so a dash can answer every one (EricBarbaricLeap's rule), and inside the player's 1.0 s i-frames, so a hit
# buys the next landing: a player who does nothing takes the first, the third and the fifth, 1 + 1 + 2 half-hearts.
# The splash zone, splash_radius on the floor flattened by floor_flatten (ry 97), is cleared in 0.16 s walking up or
# down, leaving 0.24 s to react; sideways from a standstill is too slow, on purpose.
# A homing hop is never walked out of, since its zone keeps up with the feet until it commits, and its yellow ring
# still stands the whole 0.40 s before it lands. Its answer is a dash as he lands: one started in the last
# AttackCatalog.DASH_IMMUNITY_TIME has its i-frames over the landing and holds his spot where it set off, so it is
# clear of the zone and a perfect dodge besides; one before that is followed. Homing hops land 1.35 s apart, past
# the i-frames, so each is its own read (a player who does nothing takes every one), and the dashes they ask for are
# well over DASH_IMMUNITY_COOLDOWN apart. A bar answered right holds level through them: each dash's third comes back
# before the next, half from the refill and half from the perfect dodge's refund on every other one
# (PlayerDefense.perfect_dodge_cooldown), so only misses run it down.
#
# HIS LIFT IS ON HIS SPRITE ALONE (DannyBossScript.set_lift): his node, hurtbox and y-sort stay on the spot
# he'll land on, placed so the slam sheet's rear contact texel comes down on it.
#
# STUCK MEANS NO PARRY (the user's pick after the 2026-09-24 playtest). A root taken in the string - from a splash
# or from any puddle - seals the parry as well, the Computah trap's seal, lock_actions_sealed(), so the next
# landing comes down on them: the popup says STUCK!, a parry pressed then only squelches, and no badge of either
# colour asks for an answer that can't be given. The next landing lets the root go once it has resolved, or it
# lets go by itself. Each hop also leaves a fresh puddle on its spot (DannyBossSlamPuddle), which arms
# puddle_grace later and takes any feet still on it, so crossing back over the trail roots too. The big one leaves
# none: parried, the floor round him on his back is cleared, and unparried the floor round his nap
# (_clear_nap_floor), so the punish is always reachable.
#
# RELEASE: the mark, the splash, the hints and his lift go back through release(), which Exit(), _exit_tree() and
# DannyBossStateMachine._stop_everything() call. It starts no tween once he is out of the tree: _exit_tree() can
# come as the fight scene is torn down. _stop_everything() clears the badge and brings the bar back itself, and
# what the landings left on the mat is in the hazard group it clears.

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
const Splash := preload("res://Scripts/DannyBossSplash.gd")
const AttackCatalog := preload("res://Scripts/AttackCatalog.gd")

enum Beat { CROUCH, LAUNCH, TRACK, LATCH, DROP, IMPACT, REBOUND, RISE, SETTLE, BOUNCE, DONE }

# Summed steps land a hair short of a scheduled time, which would start its beat a step late.
const STEP_TOLERANCE := 0.0001
const IMPACT_SHAKE_STEPS := 4
const IMPACT_SHAKE_STEP := 0.04
# The landing clears the badge, and lands on a whole physics step, which can be one past its scheduled time: the
# badge's own clock must not run out that step first.
const BADGE_SLACK := 0.05
# Each shown once a fight: the first hop's and the first big one's.
const HOP_HINT := &"hop"
const HOP_HINT_TEXT := "DODGE HIS HOPS - GET CLEAR OF THE WORMS!"
const BIG_HINT := &"big_slam"
const BIG_HINT_TEXT := "THE BIG ONE! TAP %s AS HE LANDS!"
# The first homing hop's, which takes over from the hop hint.
const HOMING_HINT := &"homing_hop"
const HOMING_HINT_TEXT := "NOW HE FOLLOWS YOU! DASH (%s) AS HE LANDS!"

@export var body : CharacterBody2D

# squash_time + rebound_time + rise_time + track_time + latch_time + drop_time is landing to landing: keep it over
# AttackCatalog.DASH_IMMUNITY_COOLDOWN and a dash's lead, and under the player's i-frames.
@export var slams := 5
# The hops before the big one, drawn afresh for each string off the fight's rng, which sets `slams`: the string was
# the same five beats every time, so it could be counted rather than read (the 2026-10-06 tuning). Empty: `slams`
# as it is set. 7, 8 or 9 until the homing hops (the user, 2026-10-07: "make the hops harder for danny"): two more,
# with the hang they take, put him between Eric and Greyson for the experienced player who dashes.
@export var hop_counts: Array[int] = [9, 10, 11]
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
# Every landing parried, dodged or stepped clear of, and no splash taking the player's feet.
@export var clean_hype := 10.0
@export var clean_cheer := 2.0
@export var nudge_time := 0.18
# A landing's puddle arms this long after it: the time to step off after a landing. 0.40 until the 2026-10-06 tuning;
# a player the hop just hit, standing on it, still walks off it from a 0.25 s reaction (danny_slams tier=step_off).
@export var puddle_grace := 0.35
# The most of the string's own puddles live at once (_dry_old_trail): the five-beat string's four, so a spit's four
# and the trail are never more than eight.
@export var trail_max := 4
# The squelch of a parry pressed while stuck.
@export var squelch_pitch := 1.35
# The nap's open-floor check (coder B's in danny_spit): the floor in way_cell squares, open where a square keeps
# way_clearance from every trigger, and the spots beside him a punch is thrown from.
@export var way_cell := 16.0
@export var way_clearance := 32.0
@export var punch_side := Vector2(190, 3)

#ADDENDUM 1 (dodge-first slams)
@export var hop_id := &"danny_hop_slam"
@export var big_id := &"danny_butt_slam"
@export var big_rise_time := 0.25
@export var big_track_time := 0.40
@export var big_latch_time := 0.20
@export var big_drop_time := 0.35
@export var big_drop_ease := 1.5
@export var big_shake := 22.0
# The highest a hop's spot goes (_track): the player's highest feet (y 186, under the top rope) plus the 20 px
# WALK_RECT leaves under their lowest by the bottom rope, so neither rope is safer from a hop than the other.
@export var hop_top := 206.0
# A badge's anchor no higher than this, so a hop's yellow ring by the top rope stays whole on screen: it stands 72 px
# over its anchor (DefenseHypeArtLayout.FINAL_DODGE_TELL), with 12 to spare.
@export var badge_top := 84.0
# The splash zone: a circle this big on the floor, flattened onto the screen as Bixby's floor ellipses are. 230 until
# the 2026-10-04 tuning (Danny 4 -> 5 of 10): 270 leaves a learned 0.20 s reaction about 13 px to spare walking out of
# it (danny_slams tier=react), and the artist's worm burst (576 px across) still covers it.
@export var splash_radius := 270.0
@export var floor_flatten := 0.36
# The user's open question 2, off by default: the splash hits for the hop's half a heart and never roots.
@export var splash_hurts := false
@export var bounce_time := 0.45
@export var bounce_arc := 140.0
# His lying box's near edge this far past the player's hurtbox, and the floor this far round it cleared.
@export var bounce_gap := 60.0
@export var bounce_clear := 40.0
@export var back_window := 3.0
@export var back_cap := 6

#THE HOMING HOPS (the user, 2026-10-07: "make the hops harder for danny")
# From hop homing_from on, every hop but the big one homes in: its spot runs on after the player's feet through its
# latch and its drop at homing_speed, the yellow ring, the splash zone and he himself with it, and holds only
# commit_time before it lands. A walk out of the zone is followed, and so is a dash before his last
# AttackCatalog.DASH_IMMUNITY_TIME; a dash in it holds the spot where it set off and goes through on its i-frames.
# 0 turns them off. Every hop but the first: the first keeps teaching the hop as it was, under its own hint.
@export var homing_from := 2
@export var commit_time := 0.05
# How fast a homing hop's spot chases through its latch and drop. At track_speed a dash 0.25 s out with a run on after
# it outran him; at this, any dash before his last DASH_IMMUNITY_TIME is caught, run on or not. Walking is slower
# than either, so it only shows when they dash.
@export var homing_speed := 2000.0
# A homing hop's hang before its latch, in place of track_time: 0.67 makes it 1.35 s landing to landing, the
# shortest at which a bar answered right holds level through a string of them (FAIRNESS). At 1.20 the experienced
# model ran dry on about one homing hop in twenty-five.
@export var homing_track_time := 0.67

@onready var state_machine = get_parent()

# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
var clock := 0.0
# [seconds from Enter, Beat, which slam, the beat's length], in order.
var schedule: Array = []
var next_entry := 0
var beat := Beat.CROUCH
var beat_start := 0.0
var beat_length := 0.0
var slam := 0
var drop_ease_now := 1.0
# On this state's clock, when the homing hop in the air commits to its spot; -INF while none is chasing.
var chase_until := -INF
# How far into the launch its lift-off frame comes.
var liftoff := 0.0
# Where his rear contact texel comes down, and from there to his node.
var target := Vector2.ZERO
var contact_offset := Vector2.ZERO
var mark: Node2D
var splash: Node2D
var player: Node2D
var bounce_from := Vector2.ZERO
var bounce_to := Vector2.ZERO
# For a test: each landing as it resolved, when each latch and landing came on this state's clock, whether
# every landing so far was answered, and whether the player was slid out of his footprint.
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
# For a test: every landing's id, the splashes that burst and those that rooted, the rings sent, whether he bounced
# onto his back, and how many puddles the floor round his back took.
var slam_ids: Array[StringName] = []
var splashes := 0
var splash_roots := 0
var rings := 0
var bounced := false
var bounce_cleared := 0


func Enter() -> void:
	released = false
	clock = 0.0
	next_entry = 0
	slam = 0
	chase_until = -INF
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
	slam_ids.clear()
	splashes = 0
	splash_roots = 0
	rings = 0
	bounced = false
	bounce_cleared = 0
	player = state_machine.get_player()
	liftoff = liftoff_delay()
	body.velocity = Vector2.ZERO
	body.show_body()
	body.set_hurtbox_active(false)
	body.set_body_box(&"idle")
	body.face_toward(state_machine.player_feet())
	contact_offset = body.global_position - body.contact_point(&"slam_impact")
	target = body.contact_point(&"slam_impact")
	if not hop_counts.is_empty():
		slams = hop_counts[state_machine.rng.randi_range(0, hop_counts.size() - 1)] + 1
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
	_free_splash()
	if is_instance_valid(body):
		body.set_lift(0.0)
		if body.is_inside_tree():
			body.hide_hint(HOP_HINT)
			body.hide_hint(HOMING_HINT)
			body.hide_hint(BIG_HINT)


# The big one's parry picks the strong look (DannyBossScript relays PlayerDefense's ask here). What it staggers
# him into is his back, which _bounce() sees to: nothing takes the stagger's length.
func can_parry_stagger(hit: RefCounted) -> bool:
	return not released and beat == Beat.IMPACT and slam == slams and hit.attack_id == big_id


#THE SCHEDULE

func _schedule() -> Array:
	var entries := []
	var at := 0.0
	entries.append([at, Beat.CROUCH, 1, crouch_time])
	at += crouch_time
	entries.append([at, Beat.LAUNCH, 1, launch_time])
	at += launch_time
	for k in range(1, slams + 1):
		var big := k == slams
		var track := track_time
		if big:
			track = big_track_time
		elif k == 1:
			track = first_track_time
		elif homes(k):
			track = homing_track_time
		var latch: float = big_latch_time if big else latch_time
		var drop: float = big_drop_time if big else drop_time
		entries.append([at, Beat.TRACK, k, track])
		at += track
		entries.append([at, Beat.LATCH, k, latch])
		at += latch
		entries.append([at, Beat.DROP, k, drop])
		at += drop
		entries.append([at, Beat.IMPACT, k, squash_time])
		if big:
			entries.append([at, Beat.SETTLE, k, settle_time])
			at += settle_time
		else:
			at += squash_time
			entries.append([at, Beat.REBOUND, k, rebound_time])
			at += rebound_time
			var rise: float = big_rise_time if k + 1 == slams else rise_time
			entries.append([at, Beat.RISE, k, rise])
			at += rise
	entries.append([at, Beat.DONE, slams, 0.0])
	return entries


# When slam `number` lands, on this state's clock.
func landing_time(number: int) -> float:
	for entry in schedule:
		if entry[1] == Beat.IMPACT and entry[2] == number:
			return entry[0]
	return INF


# When slam `number`'s spot holds, on this state's clock.
func latch_at(number: int) -> float:
	for entry in schedule:
		if entry[1] == Beat.LATCH and entry[2] == number:
			return entry[0]
	return INF


# Whether slam `number` is a homing hop. Never the big one.
func homes(number: int) -> bool:
	return homing_from > 0 and number >= homing_from and number < slams


# When slam `number`'s spot stops moving for good, on this state's clock: its latch, or a homing hop's commit.
func commit_at(number: int) -> float:
	return landing_time(number) - commit_time if homes(number) else latch_at(number)


# Every beat that is due, in order, stopping after a landing: the fifth's settle, due with it, starts a step
# later with the squash already showing.
func _run_due() -> void:
	while not released and next_entry < schedule.size() and clock >= schedule[next_entry][0] - STEP_TOLERANCE:
		var entry: Array = schedule[next_entry]
		next_entry += 1
		_begin(entry[1], entry[2], entry[0], entry[3])
		if entry[1] == Beat.IMPACT:
			return


func _begin(new_beat: int, number: int, at: float, length: float) -> void:
	beat = new_beat
	beat_start = at
	beat_length = length
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
			_latch(number)
		Beat.DROP:
			drop_ease_now = big_drop_ease if number == slams else drop_ease
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
			_chase(delta)
		Beat.DROP:
			lift = hover_height * (1.0 - pow(clampf(t / beat_length, 0.0, 1.0), drop_ease_now))
			_chase(delta)
		Beat.RISE:
			lift = hover_height * _ease_out(t / beat_length)
			_track(delta)
		Beat.BOUNCE:
			_step_bounce(t)
			return
	body.set_lift(lift)
	if is_instance_valid(mark):
		if beat == Beat.TRACK or beat == Beat.LATCH:
			mark.hover()
		else:
			mark.set_height(lift)
	body.update_hud_fade_at(body.crown_point())


#IN THE AIR

# The spot he'll land on chases the player's feet, as far as his feet may go, and a hop's up to hop_top: clamped to
# WALK_RECT's top (y 300), no hop's footprint or splash ever reached feet above y 266, so the strip under the top rope
# sat out all four (the 2026-10-04 playtest). The big one keeps WALK_RECT's top, since his nap and his back are laid
# out from where it lands. Side to side, every slam stays Layout.STRING_REACH in from the screen's sides, where
# WALK_RECT let the tuck be cut off (the same playtest); a footprint there still reaches the ropes.
func _track(delta: float, speed := 0.0) -> void:
	var walk: Rect2 = state_machine.WALK_RECT
	var top: float = walk.position.y if _tracking_big() else minf(hop_top, walk.position.y)
	var side: float = Layout.STRING_REACH * Layout.SCALE
	var low := Vector2(maxf(walk.position.x, side), top)
	var high := Vector2(minf(walk.end.x, ScreenView.VIEW_SIZE.x - side), walk.end.y)
	var goal: Vector2 = state_machine.player_feet().clamp(low, high)
	target = target.move_toward(goal, (speed if speed > 0.0 else _track_speed(goal, delta)) * delta)
	_place()


# The first hop's spot leaps as fast as it must to be on the feet by its latch. It sets off from where he stood,
# and with him by one rope and the player by the other, track_speed alone came down well short of them and the
# hop sat out (the 2026-10-04 playtest). The rest set off from the last landing, beside the player, at track_speed.
func _track_speed(goal: Vector2, delta: float) -> float:
	if slam != 1 or beat == Beat.RISE:
		return track_speed
	return maxf(track_speed, target.distance_to(goal) / maxf(latch_at(1) - clock, delta))


# A homing hop's spot runs on after the player through its latch and drop until it commits. A dash started in his
# last DASH_IMMUNITY_TIME commits it there and then, where the dash set off from: chased on, the spot left the dodge
# ghost behind and an on-time dash up or down paid no perfect dodge, nor its refund. One before that is followed.
func _chase(delta: float) -> void:
	if clock >= chase_until - STEP_TOLERANCE:
		return
	if _dashing_as_he_lands():
		chase_until = clock
		return
	_track(delta, homing_speed)


func _dashing_as_he_lands() -> bool:
	if not is_instance_valid(player) or not player.is_dodging:
		return false
	var ago := float(Engine.get_physics_frames() - player.last_dodge_physics_frame) / Engine.physics_ticks_per_second
	return landing_time(slam) - (clock - maxf(ago, 0.0)) <= AttackCatalog.DASH_IMMUNITY_TIME + STEP_TOLERANCE


# Rising off the last hop or hanging before the big one: the spot is the big one's.
func _tracking_big() -> bool:
	return slam == slams or (beat == Beat.RISE and slam == slams - 1)


func _place() -> void:
	body.global_position = (target + contact_offset).round()
	if is_instance_valid(mark):
		mark.global_position = target.round()
	if is_instance_valid(splash):
		splash.global_position = target.round()


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
	return Vector2(target.x, maxf(target.y - badge_rise, badge_top))


# The spot holds, or a homing hop's runs on to its commit. A hop's splash zone goes down round it and the yellow ring
# up over it; the big one's red badge goes up alone. Not over a stuck player, who can give neither answer.
func _latch(number: int) -> void:
	latch_times.append(clock)
	chase_until = commit_at(number) if homes(number) else -INF
	var big := number == slams
	if big:
		body.show_hint(BIG_HINT, BIG_HINT_TEXT % InputSettings.label_for(&"block"))
	else:
		_add_splash()
		if number == 1:
			body.show_hint(HOP_HINT, HOP_HINT_TEXT)
		elif homes(number):
			body.hide_hint(HOP_HINT)
			body.show_hint(HOMING_HINT, HOMING_HINT_TEXT % InputSettings.label_for(&"dodge"))
	if _sealed():
		badges_withheld.append(number)
		return
	ParryTell.telegraph(body, big_id if big else hop_id, landing_time(number) - beat_start + BADGE_SLACK, _badge_point)


func _add_splash() -> void:
	_free_splash()
	splash = Splash.new()
	splash.name = "Splash"
	splash.player = player
	splash.body = body
	splash.state_machine = state_machine
	splash.radii = Vector2(splash_radius, roundf(splash_radius * floor_flatten))
	splash.roots = not splash_hurts
	splash.hit_id = hop_id
	state_machine.add_hazard(splash, target, body.floor_layer)


func _free_splash() -> void:
	if is_instance_valid(splash):
		splash.queue_free()
	splash = null


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
	var big := slam == slams
	body.set_lift(0.0)
	body.play_anim(&"slam_impact")
	_place()
	impact_times.append(clock)
	var hit := SlamHit.new()
	hit.player = player
	hit.boss = body
	hit.attack_id = big_id if big else hop_id
	state_machine.add_hazard(hit, target, body.floor_layer)
	slam_ids.append(hit.attack_id)
	results.append({"result": hit.result, "feet_inside": hit.feet_inside, "ghost_inside": hit.ghost_inside, "id": hit.attack_id})
	var answered := hit.result == HitInfo.Result.PARRIED or hit.result == HitInfo.Result.DODGED
	clean = clean and (answered or not hit.feet_inside)
	if big:
		body.hide_hint(BIG_HINT)
		if hit.result == HitInfo.Result.PARRIED:
			_bounce()
			return
	elif slam == slams - 1:
		body.hide_hint(HOP_HINT)
		body.hide_hint(HOMING_HINT)
	# Only now the landing has had its say on the player does a root sprung in the string let go. The puddles
	# under a stuck player armed while they were held, so the one it frees gets puddle_grace to step off them before
	# another root can take them; the landing that frees them has just hit them, or found them in the i-frames of
	# the one before, so its own splash wouldn't have taken them anyway.
	var root = state_machine.root
	var freed: bool = is_instance_valid(root) and not root.released
	state_machine.release_root()
	if freed:
		state_machine.start_root_grace(puddle_grace)
	state_machine.splat_puddles_in(target, hit.radii.x, hit.radii.y)
	if big:
		_big_impact(hit)
	else:
		_hop_impact()
	if is_instance_valid(mark):
		mark.set_height(0.0)


# The hop's splash has its say once the landing has, then the puddle it leaves and its cracks.
func _hop_impact() -> void:
	body.play_sfx(&"hop_slam")
	ScreenView.shake(get_tree(), impact_shake, IMPACT_SHAKE_STEPS, IMPACT_SHAKE_STEP)
	if is_instance_valid(splash):
		splashes += 1
		if splash.burst():
			splash_roots += 1
			clean = false
		elif splash.result == HitInfo.Result.HIT:
			clean = false
	# It frees itself once its burst is over.
	splash = null
	# Sealed on the landing's own step, so STUCK! comes up with it.
	_seal_if_rooted()
	_leave_puddle()
	play_impact(state_machine, body, target, cracks_hold, cracks_fade)


func _big_impact(hit: Node2D) -> void:
	body.play_sfx(&"big_slam")
	body.play_sfx(&"big_slam_quake")
	ScreenView.shake(get_tree(), big_shake, IMPACT_SHAKE_STEPS, IMPACT_SHAKE_STEP)
	play_impact(state_machine, body, target, cracks_hold, cracks_fade,
		&"big_slam_impact" if Layout.final_fx(&"big_slam_impact") else &"slam_impact")
	var ring := QuakeRing.new()
	ring.player = hit.player
	ring.speed = ring_speed
	ring.spared = hit.feet_inside
	state_machine.add_hazard(ring, target, body.ring_layer)
	rings += 1


# The flash and the dust burst over both fighters where his rear came down at `at`, then the cracks alone on
# the mat under him, held and faded, off the FX sheet `key`. His leap to the gate at 0 HP lands the same way
# (DannyBossSumo).
static func play_impact(fight: Node, danny: Node2D, at: Vector2, hold: float, fade: float, key := &"slam_impact") -> void:
	var spec := Layout.fx(key)
	var cracks_frame: int = spec.cracks_frame
	var burst := _fx_sprite(spec, 0)
	fight.add_hazard(burst, at, danny.projectile_layer)
	var cracks := _fx_sprite(spec, cracks_frame)
	cracks.visible = false
	fight.add_hazard(cracks, at, danny.floor_layer)
	var play := burst.create_tween()
	var burst_time := 0.0
	for i in range(1, cracks_frame):
		play.tween_interval(Layout.fx_frame_time(spec, i - 1))
		play.tween_callback(burst.set_frame.bind(i))
		burst_time += Layout.fx_frame_time(spec, i - 1)
	play.tween_interval(Layout.fx_frame_time(spec, cracks_frame - 1))
	play.tween_callback(burst.queue_free)
	burst_time += Layout.fx_frame_time(spec, cracks_frame - 1)
	var lie := cracks.create_tween()
	lie.tween_interval(burst_time)
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


# The fifth landing, not parried: the mark's done, a clean string pays, and a player sat in his footprint is slid
# out of it.
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


#THE BOUNCE (the big one parried)

# Off the player's fists and onto his back beside them: no ring, no cracks and no puddle, and a clean string still
# pays. The rest of the schedule - the settle and the nap - is dropped.
func _bounce() -> void:
	bounced = true
	next_entry = schedule.size()
	_free_mark()
	_free_splash()
	state_machine.release_root()
	body.play_sfx(&"slam_bonk")
	HitStop.freeze(get_tree(), parry_hit_stop)
	if clean:
		body.add_player_hype(clean_hype)
		get_tree().call_group("arena_crowd", "cheer", clean_cheer)
	bounce_from = body.global_position
	var walk: Rect2 = state_machine.WALK_RECT
	var hurt := _player_box()
	var right := walk.end.x - hurt.get_center().x >= hurt.get_center().x - walk.position.x
	# The back sheet lies with his head to the left unflipped: he lands with it toward the player, as the artist's
	# mock and bounce have him, and his lying box is mirrored to match before the spot is worked out from it.
	body.sprite.flip_h = not right
	bounce_to = _back_spot(right)
	beat = Beat.BOUNCE
	beat_start = clock
	beat_length = bounce_time
	body.play_anim(&"back_bounce")


func _step_bounce(t: float) -> void:
	var weight := minf(t / beat_length, 1.0)
	body.global_position = bounce_from.lerp(bounce_to, weight).round()
	body.set_lift(roundf(4.0 * bounce_arc * weight * (1.0 - weight)))
	body.update_hud_fade_at(body.crown_point())
	if weight < 1.0:
		return
	body.set_lift(0.0)
	body.restore_hud()
	bounce_cleared = state_machine.clear_floor_round(body.body_box_rect(&"back"), bounce_clear)
	state_machine.enter_on_back(back_window, back_cap, true, &"slam")


# Beside the player, on their right or left, his lying box's near edge bounce_gap past their hurtbox, on the
# landing's line, or lower by the top of the ring, so lying he stays under the top rope and the boss bar
# (lying_top_min): the gap is side to side, so it holds either way.
func _back_spot(right: bool) -> Vector2:
	var walk: Rect2 = state_machine.WALK_RECT
	var feet: Vector2 = body.global_position
	var lying: Rect2 = body.body_box_rect(&"back")
	lying.position -= feet
	var hurt := _player_box()
	var x: float = hurt.end.x + bounce_gap - lying.position.x if right else hurt.position.x - bounce_gap - lying.end.x
	var y: float = maxf(feet.y, state_machine.lying_feet_y_min(lying))
	return Vector2(x, y).clamp(walk.position, walk.end).round()


func _player_box() -> Rect2:
	if not is_instance_valid(player):
		return Rect2(body.global_position, Vector2.ZERO)
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	return shape.global_transform * shape.shape.get_rect()


#STUCK AND THE WORMS

# A root taken in the string, from a splash or any puddle, takes the parry with it until it lets go
# (unlock_actions lifts both): the popup says why, and a badge up for the landing coming goes.
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
	_dry_old_trail()


# The string's trail keeps its newest trail_max puddles; older ones dry as a spit's gulp dries them. Seven to nine hops
# left a trail that walled the player in round where they had been, so every way off a hop was a dash, more than
# the stamina bar pays for (the 2026-10-06 tuning).
func _dry_old_trail() -> void:
	var live: Array = puddles_left.filter(func(p): return is_instance_valid(p) and not p.gone)
	for i in maxi(live.size() - trail_max, 0):
		live[i].dry(state_machine.states["Spit"].dry_time)


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
