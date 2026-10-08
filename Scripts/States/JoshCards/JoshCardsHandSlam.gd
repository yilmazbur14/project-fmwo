extends State

# Josh's Hand Slam, to the user's design of 2026-09-29: "Josh orders the hands to start hovering over the player,
# tracking him, and eventually slamming down on the player. This attack can be parried and dodged." His two card hands
# (JoshHandsRig) take turns, six slams (four until the tuning round of 2026-10-04), landings at 1.96 s and then every
# 0.81 s:
#   COMMAND  0.50  he points them on (command, command_hold), and they flex at their portals (windup)
#   FLY      0.50  both leave their portals: the one whose portal is nearer the player goes over them, its mark fading
#                  in under it, the other to its deck spot beside them
#   TRACK    0.60, then 0.45  the spot under the hand whose turn it is chases the player's feet at hand_track_speed,
#                  the mark flickering on it; the other waits on deck beside the player, with no mark
#   LOCK     0.13  the spot leaps to where the player is heading (_aim: the user's "aim where you're heading",
#                  2026-10-04) and holds, the hand gliding over it as it rears up, and the red badge stands over the
#                  spot until the landing
#   DROP     0.23  it comes down, the mark's shadow growing
#   IMPACT         it lands (JoshHandSlamHit) and the other hand's turn starts
#   SETTLE   0.35  after the last; then both go home, and he is winded (Recover) or goes on into his next attack
#                  (JoshCardsStateMachine.end_attack)
# A parry shatters the hand into cards and it re-forms on deck before its next turn, with the standard parry's
# rewards; a hit, a dodge or a miss pins it a beat on the floor, then it rises back to deck. Every slam parried or
# dodged pays hand_clean_hype and a cheer.
#
# FAIRNESS: landing to landing is 0.81 s, a lead over the dash immunity's cooldown and inside the player's 1.0 s
# i-frames, so every landing can be dashed and a player who does nothing takes every second one; lock to landing,
# under the badge, is 0.36 s against the 0.24 s parry window; a still player walking out from the lock clears the footprint, and one
# who was walking at the lock clears it by stopping, turning or doubling back a reaction later - walking on is what
# it punishes (JoshHandsLayout.invariants).
#
# IT ALL RUNS ON ONE CLOCK against a schedule worked out as it enters (DannyBossSlams' pattern), started late by
# however long the hands still need to form. Each hand's own beat between its turns runs off the same clock (Arm).
# RELEASE: the mark, the badge and the faded bars go back through release(), which Exit(), _exit_tree() and its own
# end call, and the hands go home on the rig's clock. At a scene's teardown the bars, the badge and the hands have
# already left the tree ahead of this state, so it touches none of them then.

const Layout := preload("res://Scripts/JoshHandsLayout.gd")
const JoshArtLayout := preload("res://Scripts/JoshArtLayout.gd")
const JoshHand := preload("res://Scripts/JoshHand.gd")
const HandMark := preload("res://Scripts/JoshHandMark.gd")
const SlamHit := preload("res://Scripts/JoshHandSlamHit.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const HitStop := preload("res://Scripts/HitStop.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")

enum Beat { COMMAND, FLY, TRACK, LOCK, DROP, IMPACT, SETTLE, DONE }

# Summed steps land a hair short of a scheduled time, which would start its beat a step late.
const STEP_TOLERANCE := 0.0001
const IMPACT_SHAKE_STEPS := 4
const IMPACT_SHAKE_STEP := 0.04
# The badge is cleared as its slam lands; given this much longer, it never runs out a step early on summed steps.
const BADGE_SLACK := 0.1

@export var body : CharacterBody2D

@onready var state_machine = get_parent()


# One hand's own beat: resting at its portal, flying out, on deck beside the player, over them (track, lock, drop),
# pinned after a landing (and held there through the last settle) and rising back to deck, or shattered by a parry
# and re-forming on deck. `since` is when its phase began on the state's clock; `from` where a flight or a rise left;
# `drop_from` the height it actually had as its drop began, clamped at the back rope (JoshHand.place_air).
class Arm:
	var side := &""
	var hand: Node2D
	var phase := &"rest"
	var since := 0.0
	var from := Vector2.ZERO
	var drop_from := 0.0
	var landed_slam := 0


# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
var clock := 0.0
# [seconds from Enter, Beat, which slam], in order.
var schedule: Array = []
var next_entry := 0
var beat := Beat.COMMAND
var beat_start := 0.0
var slam := 0
# Which hand takes each slam, and whose turn it is.
var order: Array[StringName] = []
var active_side := &""
# The spot the hand whose turn it is will land on.
var target := Vector2.ZERO
# The one mark there is, and whose: the hand whose turn it is, or, landed, the one pinned on it.
var mark: Node2D
var mark_side := &""
var player: Node2D
var arms := {}
# How long the hands still needed to form as it entered: the schedule starts that much later.
var lead := 0.0
# The feet last step, and how fast they moved over it (px/s): what the lock leads them by. The trail is where they
# were over the last hand_lead_window, oldest first, [clock, feet] a step: how straight they have been going.
var last_feet := Vector2.ZERO
var heading := Vector2.ZERO
var trail: Array = []
# For a test: each landing as it resolved ({slam, side, result, feet_inside, ghost_inside, at: its spot, feet: the
# feet it tested}), when each lock and landing came on this state's clock, the heading each lock read and the lead it
# took, and whether every landing so far was parried or dodged. forced_first pins the hand that goes first; &"" picks
# the one nearer the player.
var results: Array[Dictionary] = []
var lock_times: Array[float] = []
var headings: Array[Vector2] = []
var leads: Array[Vector2] = []
var impact_times: Array[float] = []
var clean := true
var forced_first := &""


func Enter() -> void:
	released = false
	clock = 0.0
	next_entry = 0
	slam = 0
	beat = Beat.COMMAND
	beat_start = 0.0
	results.clear()
	lock_times.clear()
	headings.clear()
	leads.clear()
	impact_times.clear()
	clean = true
	order.clear()
	active_side = &""
	mark_side = &""
	player = state_machine.get_player()
	last_feet = _feet()
	heading = Vector2.ZERO
	trail.clear()
	_remember(last_feet)
	body.fly_velocity = Vector2.ZERO
	body.height = 0.0
	body.place()
	body.hide_glider()
	body.set_air_draw(false)
	body.set_hurtbox_active(false)
	body.set_target_active(true)
	var rig: Node = state_machine.hands
	if not rig.built:
		rig.build()
		rig.place_summoned()
	var out_there := false
	for side in Layout.SIDES:
		var hand: Node2D = rig.hand_of(side)
		out_there = out_there or (hand != null and (hand.mode == JoshHand.Mode.AIR or hand.mode == JoshHand.Mode.GROUND))
	if out_there:
		rig.snap_home()
	rig.ensure_formed()
	lead = rig.time_to_ready()
	arms.clear()
	for side in Layout.SIDES:
		var arm := Arm.new()
		arm.side = side
		arm.hand = rig.hand_of(side)
		if arm.hand != null:
			arm.hand.driven = true
		arms[side] = arm
	target = _feet()
	schedule = _schedule()
	_run_due()


func Physics_Update(delta: float) -> void:
	if released:
		return
	clock += delta
	_run_due()
	if released:
		return
	_step(delta)


func Exit() -> void:
	release()


func _exit_tree() -> void:
	release()


# Idempotent. The mark goes, and unless the scene is being torn down, the badge, the bars come back and every hand
# goes home on the rig's clock - one a parry left in pieces re-forms there.
func release() -> void:
	if released:
		return
	released = true
	_free_mark()
	if not is_instance_valid(body) or body.health_bar == null or not body.health_bar.is_inside_tree():
		return
	ParryTell.clear(body)
	body.restore_hud()
	var rig: Node = state_machine.hands
	for side in arms:
		var arm: Arm = arms[side]
		if not is_instance_valid(arm.hand):
			continue
		arm.hand.driven = false
		if arm.phase == &"shatter" or arm.hand.mode == JoshHand.Mode.HIDDEN:
			rig.reform_home(side)
		else:
			rig.send_home(side, state_machine.hand_home_time)


#THE SCHEDULE

func _schedule() -> Array:
	var sm = state_machine
	var entries := []
	var at := lead
	entries.append([at, Beat.COMMAND, 1])
	at += sm.hand_command_time
	entries.append([at, Beat.FLY, 1])
	at += sm.hand_fly_time
	for k in range(1, sm.hand_slams + 1):
		entries.append([at, Beat.TRACK, k])
		at += sm.hand_first_track if k == 1 else sm.hand_track_time
		entries.append([at, Beat.LOCK, k])
		at += sm.hand_lock_time
		entries.append([at, Beat.DROP, k])
		at += sm.hand_drop_time
		entries.append([at, Beat.IMPACT, k])
		if k == sm.hand_slams:
			entries.append([at, Beat.SETTLE, k])
			at += sm.hand_settle_time
	entries.append([at, Beat.DONE, sm.hand_slams])
	return entries


# Every beat that is due, in order, stopping after a landing: the next turn, due with it, starts a step later with the
# landing already on the floor.
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
		Beat.COMMAND:
			_point()
			for side in arms:
				var hand: Node2D = arms[side].hand
				if hand != null and hand.mode == JoshHand.Mode.REST:
					hand.play(&"windup", 1.0, false, &"hover")
		Beat.FLY:
			_fly_out(at)
		Beat.TRACK:
			_take_turn(number, at)
		Beat.LOCK:
			lock_times.append(clock)
			arms[active_side].from = arms[active_side].hand.floor_at
			target = _aim()
			_set_phase(arms[active_side], &"lock", at)
			arms[active_side].hand.play(&"windup")
			ParryTell.telegraph(body, SlamHit.SLAM_ID, state_machine.hand_lock_time + state_machine.hand_drop_time + BADGE_SLACK, _badge_point)
			_point()
			state_machine.hands.play_sound(&"hand_lock")
		Beat.DROP:
			var arm: Arm = arms[active_side]
			_set_phase(arm, &"drop", at)
			arm.hand.play(&"drop")
			# From the height it has, so a hand held down at the back rope still takes the whole drop, and its mark's
			# shadow still runs through every frame.
			arm.drop_from = arm.hand.height
			if is_instance_valid(mark) and mark_side == active_side:
				mark.full_height = maxf(arm.drop_from, 1.0)
		Beat.IMPACT:
			_land(at)
		Beat.DONE:
			_finish()


# He turns to the player and points the hands on.
func _point() -> void:
	body.face_player()
	body.play_anim(&"command", &"command_hold")


# Out of their portals: the first over the player, the other to its deck spot. Home in the air is a hand's rest
# point from hover height, so neither jumps as it leaves.
func _fly_out(at: float) -> void:
	var sm = state_machine
	var first := _first_side(_feet())
	order.clear()
	for k in sm.hand_slams:
		order.append(first if k % 2 == 0 else Layout.other_side(first))
	active_side = first
	for side in arms:
		var arm: Arm = arms[side]
		if arm.hand == null:
			continue
		arm.from = Layout.rest_point(side) + Vector2(0.0, sm.hand_hover_height)
		_set_phase(arm, &"fly", at)
		arm.hand.place_air(arm.from, sm.hand_hover_height)
		if arm.hand.clip != &"hover":
			arm.hand.play(&"hover")
	target = arms[first].from


# Slam `number`'s hand takes its turn from wherever it waits; the other waits on deck.
func _take_turn(number: int, at: float) -> void:
	active_side = order[number - 1]
	var arm: Arm = arms[active_side]
	if arm.hand != null:
		target = arm.hand.floor_at
	_set_phase(arm, &"track", at)
	for side in arms:
		if arms[side].phase == &"fly":
			_set_phase(arms[side], &"deck", at)


func _set_phase(arm: Arm, phase: StringName, at: float) -> void:
	arm.phase = phase
	arm.since = at


#EVERY STEP

func _step(delta: float) -> void:
	var feet := _feet()
	heading = (feet - last_feet) / delta
	last_feet = feet
	_remember(feet)
	for side in arms:
		var arm: Arm = arms[side]
		if not is_instance_valid(arm.hand):
			continue
		match arm.phase:
			&"fly":
				_step_fly(arm, feet)
			&"track":
				target = target.move_toward(feet, state_machine.hand_track_speed * delta)
				arm.hand.place_air(target, state_machine.hand_hover_height)
			&"lock":
				var t := clampf((clock - arm.since) / state_machine.hand_lock_time, 0.0, 1.0)
				arm.hand.place_air(arm.from.lerp(target, _ease_out(t)), state_machine.hand_hover_height + state_machine.hand_lock_rise * _ease_out(t))
			&"drop":
				var p := clampf((clock - arm.since) / state_machine.hand_drop_time, 0.0, 1.0)
				arm.hand.place_air(target, arm.drop_from * (1.0 - p * p), 1.0 - p)
			&"deck", &"reform":
				_step_deck(arm, feet, delta)
			&"pin":
				_step_pin(arm)
			&"rise":
				_step_rise(arm, feet)
			&"shatter":
				_step_shatter(arm, feet)
	_step_mark()
	_fade_hud()


# Out of the portal toward its goal, its floor point homing on where that is now, its height swelling on the way.
func _step_fly(arm: Arm, feet: Vector2) -> void:
	var sm = state_machine
	var t := clampf((clock - arm.since) / sm.hand_fly_time, 0.0, 1.0)
	var goal: Vector2 = feet if arm.side == active_side else _deck_spot(arm.side, feet)
	var floor_at: Vector2 = arm.from.lerp(goal, smoothstep(0.0, 1.0, t))
	arm.hand.place_air(floor_at, sm.hand_hover_height + Layout.FLY_ARC * sin(PI * t))
	if arm.side == active_side:
		target = floor_at


# Waiting its turn beside the player; a hand re-forming there has formed once its time is up.
func _step_deck(arm: Arm, feet: Vector2, delta: float) -> void:
	var sm = state_machine
	var floor_at: Vector2 = arm.hand.floor_at.move_toward(_deck_spot(arm.side, feet), sm.hand_track_speed * delta)
	arm.hand.place_air(floor_at, sm.hand_hover_height)
	if arm.phase == &"reform" and clock >= arm.since + sm.hand_reform_time - STEP_TOLERANCE:
		arm.phase = &"deck"


# Flat on the floor for the pin, then it rises back to deck, in the air from the rise's first step; the last slam's
# hand stays down through the settle.
func _step_pin(arm: Arm) -> void:
	var sm = state_machine
	if clock < arm.since + sm.hand_pin_time - STEP_TOLERANCE:
		return
	if arm.landed_slam >= sm.hand_slams:
		_set_phase(arm, &"settle", arm.since + sm.hand_pin_time)
		return
	_set_phase(arm, &"rise", arm.since + sm.hand_pin_time)
	arm.from = arm.hand.floor_at
	arm.hand.place_air(arm.from, 0.0)
	arm.hand.play_motion(&"lift", sm.hand_rise_time, &"hover")


func _step_rise(arm: Arm, feet: Vector2) -> void:
	var sm = state_machine
	var t := clampf((clock - arm.since) / sm.hand_rise_time, 0.0, 1.0)
	var floor_at: Vector2 = arm.from.lerp(_deck_spot(arm.side, feet), smoothstep(0.0, 1.0, t))
	arm.hand.place_air(floor_at, sm.hand_hover_height * _ease_out(t))
	if t >= 1.0:
		arm.phase = &"deck"


# In pieces on the floor, then gone; it re-forms on deck for its next turn, or after the last slam waits to re-form at
# its portal.
func _step_shatter(arm: Arm, feet: Vector2) -> void:
	var sm = state_machine
	if clock < arm.since + sm.hand_shatter_time - STEP_TOLERANCE:
		return
	arm.hand.hide_hand()
	if arm.landed_slam >= sm.hand_slams:
		_set_phase(arm, &"gone", arm.since + sm.hand_shatter_time)
		return
	_set_phase(arm, &"reform", arm.since + sm.hand_shatter_time)
	arm.hand.place_air(_deck_spot(arm.side, feet), sm.hand_hover_height)
	arm.hand.play_motion(&"reform", sm.hand_reform_time, &"hover")


func _ease_out(x: float) -> float:
	var left := 1.0 - clampf(x, 0.0, 1.0)
	return 1.0 - left * left


#THE MARK

# One mark at a time. The hand whose turn it is gets its mark from its flight or its turn - at once after a parry,
# which takes the last one away, and otherwise once the hand pinned on the last one rises off it.
func _step_mark() -> void:
	if is_instance_valid(mark) and mark.landed:
		var pinned: Arm = arms.get(mark_side)
		if pinned == null or pinned.phase != &"pin":
			_free_mark()
	var arm: Arm = arms.get(active_side)
	if arm == null or not is_instance_valid(arm.hand):
		return
	var marked: bool = arm.phase in [&"fly", &"track", &"lock", &"drop"]
	if not is_instance_valid(mark) and marked:
		_raise_mark(arm.side)
	if not is_instance_valid(mark) or mark_side != active_side or not marked:
		return
	mark.global_position = target.round()
	if arm.phase == &"drop":
		mark.set_height(arm.hand.height)
	else:
		mark.hover()


func _raise_mark(side: StringName) -> void:
	mark = HandMark.new()
	mark.name = "HandMark"
	mark.full_height = state_machine.hand_hover_height
	mark_side = side
	state_machine.add_hazard(mark, target, body.floor_layer)
	mark.fade_in(Layout.MARK.fade_in)
	mark.hover()


func _free_mark() -> void:
	if is_instance_valid(mark):
		mark.queue_free()
	mark = null
	mark_side = &""


# The badge's tip over the locked spot, never so high the badge leaves the view.
func _badge_point() -> Vector2:
	return Vector2(target.x, maxf(target.y - state_machine.hand_badge_rise, Layout.BADGE_TOP_MIN))


#THE LANDING

func _land(at: float) -> void:
	var sm = state_machine
	ParryTell.clear(body)
	var arm: Arm = arms[active_side]
	arm.landed_slam = slam
	_set_phase(arm, &"pin", at)
	arm.hand.place_ground(target)
	arm.hand.play(&"impact")
	impact_times.append(clock)
	var hit := SlamHit.new()
	hit.player = player
	hit.boss = body
	# It resolves as it is added, so it has to be standing on the spot by then.
	hit.position = body.floor_layer.to_local(target.round())
	sm.add_hazard(hit, target, body.floor_layer)
	results.append({"slam": slam, "side": active_side, "result": hit.result, "feet_inside": hit.feet_inside,
		"ghost_inside": hit.ghost_inside, "at": target.round(), "feet": hit.feet})
	var answered := hit.result == HitInfo.Result.PARRIED or hit.result == HitInfo.Result.DODGED
	clean = clean and (answered or (hit.ghost_inside and not hit.feet_inside))
	sm.hands.play_sound(&"hand_slam")
	ScreenView.shake(get_tree(), sm.hand_impact_shake, IMPACT_SHAKE_STEPS, IMPACT_SHAKE_STEP)
	_burst(target)
	if is_instance_valid(mark):
		mark.land()
	if hit.result != HitInfo.Result.PARRIED:
		return
	_free_mark()
	_set_phase(arm, &"shatter", at)
	arm.hand.play_motion(&"shatter", sm.hand_shatter_time)
	HitStop.freeze(get_tree(), sm.hand_parry_hit_stop)
	sm.hands.play_sound(&"hand_shatter")
	body.play_anim(&"hit", &"command_hold")


# The burst where it landed, played once (JoshCardsWildCards._flurry's pattern): its own on the floor under the hand
# once it is in, else the fan of cards over the floor point.
func _burst(at: Vector2) -> void:
	var spec := Layout.impact_spec()
	var fan := Sprite2D.new()
	fan.name = "HandImpact"
	fan.texture = load(spec.texture)
	fan.hframes = spec.hframes
	fan.scale = Vector2.ONE * spec.scale
	fan.offset = spec.frame_size / 2.0 - spec.pivot
	state_machine.add_hazard(fan, at, body.floor_layer if spec.on_floor else body.get_parent())
	var times: Array = spec.frame_times
	var play := fan.create_tween()
	for i in range(1, spec.hframes):
		play.tween_interval(times[i - 1])
		play.tween_callback(fan.set_frame.bind(i))
	play.tween_interval(times[times.size() - 1])
	play.tween_callback(fan.queue_free)


# The last has settled: a clean string pays, everything goes home and he is winded, or goes straight on into his next
# attack (JoshCardsStateMachine.end_attack).
func _finish() -> void:
	if clean:
		body.add_player_hype(state_machine.hand_clean_hype)
		get_tree().call_group("arena_crowd", "cheer", state_machine.hand_clean_cheer)
	release()
	state_machine.end_attack(self)


#WHERE THINGS ARE

# The foot of the player's hurtbox, on the floor inside the ropes.
func _feet() -> Vector2:
	var ropes: Rect2 = state_machine.ROPES
	if not is_instance_valid(player):
		return ropes.get_center()
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	return Vector2(box.get_center().x, box.end.y).clamp(ropes.position, ropes.end)


# Where a lock comes down: the feet led by hand_lead_time of their heading, at most hand_lead_max on either axis, inside
# the ropes - once they have been heading somewhere (_straightness). A still or zigzagging player is locked on their
# feet; one walking on walks under it as it lands.
func _aim() -> Vector2:
	var sm = state_machine
	var most := Vector2.ONE * float(sm.hand_lead_max)
	var ahead := Vector2.ZERO
	if _straightness() >= sm.hand_lead_straightness:
		ahead = (heading * float(sm.hand_lead_time)).clamp(-most, most)
	headings.append(heading)
	leads.append(ahead)
	return (_feet() + ahead).clamp(sm.ROPES.position, sm.ROPES.end)


# Kept back to the last step at or before hand_lead_window ago, so the trail always spans the whole window.
func _remember(feet: Vector2) -> void:
	trail.append([clock, feet])
	while trail.size() > 1 and trail[1][0] <= clock - state_machine.hand_lead_window + STEP_TOLERANCE:
		trail.pop_front()


# How far the feet got over the trail against how far they walked along it: 1 going straight, near 0 zigzagging on the
# spot, 0 standing.
func _straightness() -> float:
	var walked := 0.0
	for i in range(1, trail.size()):
		walked += (trail[i][1] as Vector2).distance_to(trail[i - 1][1])
	if walked <= 0.0:
		return 0.0
	return (trail[-1][1] as Vector2).distance_to(trail[0][1]) / walked


# Beside the player on the hand's own side, or on their other side when that would leave the floor.
func _deck_spot(side: StringName, feet: Vector2) -> Vector2:
	var offset: float = state_machine.hand_deck_offset * (-1.0 if side == &"left" else 1.0)
	var spot := feet + Vector2(offset, 0.0)
	if spot.x < Layout.DECK_X.x or spot.x > Layout.DECK_X.y:
		spot.x = feet.x - offset
	return spot


func _first_side(feet: Vector2) -> StringName:
	if forced_first != &"":
		return forced_first
	var left: float = absf(Layout.PORTAL_POINTS[&"left"].x - feet.x)
	var right: float = absf(Layout.PORTAL_POINTS[&"right"].x - feet.x)
	return &"left" if left <= right else &"right"


# The bars fade while a hand in the air, or the badge, is over them.
func _fade_hud() -> void:
	var over: Array[Rect2] = []
	for side in arms:
		var hand: Node2D = arms[side].hand
		if is_instance_valid(hand) and hand.mode == JoshHand.Mode.AIR:
			over.append(hand.drawn_rect())
	if beat == Beat.LOCK or beat == Beat.DROP:
		var badge: Rect2 = JoshArtLayout.TELL_BADGE
		over.append(Rect2(_badge_point() + badge.position, badge.size))
	body.update_hud_fade(over)
