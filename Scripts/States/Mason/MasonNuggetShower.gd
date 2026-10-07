extends State

@export var animation_player : AnimationPlayer
@export var toss_sfx_player : AudioStreamPlayer

const NUGGET_METEOR_SCENE := "res://Scenes/Bosses/NuggetMeteorScene.tscn"
const NuggetMeteor := preload("res://Scripts/NuggetMeteorScript.gd")

# Every nth nugget of a shower is aimed at the player; the rest fall anywhere.
@export var target_every := 3
# No marker goes down this close to a nugget due to land after it appears: with the sky this busy it
# is what keeps gaps between the markers to stand in. Nuggets already landing don't count, or the
# aimed nugget after one that hit a player standing still would be pushed off them.
@export var nugget_spacing := 110.0
# How deep an aimed nugget moved off the player has to reach into their hurtbox, so the hit registers
# reliably rather than by a hair.
const MIN_PLAYER_OVERLAP := 4.0
const RANDOM_TRIES := 30
# The rain and Carter's slams each come off tweens of their own, stepped a frame at a time, so either
# can come down a frame or so off its schedule: the clear time around a slam is kept this much wider on
# both sides, so what the player sees still keeps to slam_clear_before and slam_clear_after.
const SLAM_CLEAR_GUARD := 2.0 / 60.0
# Nuggets moved off the spot they were meant for go to the nearest spot that works, searched for on
# rings this many px apart.
const SEARCH_STEP := 10.0
const SEARCH_RINGS := 40

@onready var state_machine = get_parent()

var shower: Tween
var nuggets : Array = []
# Where each nugget of this shower lands, and when, in seconds from the first drop. Judged by the
# schedule rather than by what's landed yet: in phase 2 an aimed nugget drops within a frame of the
# last aimed one landing on the same spot, and frame order mustn't decide whether it gets moved.
var landing_spots : Array[Vector2] = []
var landing_times : Array[float] = []
var keep_out: Rect2
var shower_done := false
# Carter called in while it rains (MasonStateMachine.carter_in_shower), on MasonCallCarter's own call,
# which this makes on its own tween.
var with_carter := false
var carter_call: State
var phone: Tween
# Phase one's Carter call with a light rain under it (MasonStateMachine.carter_rain, run as "CarterRain"): Carter on
# the call's own numbers and the rain on the state machine's rain_* knobs, every rain_target_every-th nugget aimed
# where the player is heading rather than where they are.
var rain := false
# This shower's nugget warning, whichever numbers it runs on.
var warning := 0.0
# When each of his slams switches its hitbox on, in seconds from the heave, and for how long.
var slams : Array[float] = []
var slam_live := 0.0


func Enter() -> void:
	animation_player.play("nugget_toss")
	animation_player.queue("nugget_hold")
	toss_sfx_player.play()
	keep_out = state_machine.keep_out_around_mason(NuggetMeteor.footprint())
	nuggets.clear()
	landing_spots.clear()
	landing_times.clear()
	shower_done = false
	rain = state_machine.attack_variant == "CarterRain"
	state_machine.attack_variant = ""
	with_carter = rain or state_machine.carter_in_shower[state_machine.cycle_phase]
	warning = state_machine.rain_warning if rain else state_machine.nugget_warning[state_machine.cycle_phase]
	carter_call = state_machine.states["CallCarter"]
	slams.clear()


# Called by the nugget_toss animation on its heave frame, as the nuggets leave the bucket.
func start_shower() -> void:
	var phase: int = state_machine.cycle_phase
	var count: int = state_machine.rain_count if rain else state_machine.nugget_count[phase]
	var interval: float = (state_machine.rain_time if rain else state_machine.nugget_shower_time[phase]) / count
	var aim_every: int = state_machine.rain_target_every if rain else target_every
	if with_carter:
		_call_carter()
	# One tween runs the whole shower, so leaving the state stops it in one go.
	shower = create_tween()
	var gap := 0.0
	for i in count:
		if i > 0:
			gap += interval
		if _near_a_slam(i * interval + warning):
			continue
		if gap > 0.0:
			shower.tween_interval(gap)
			gap = 0.0
		shower.tween_callback(_drop_nugget.bind((i + 1) % aim_every == 0, i * interval))
	shower.tween_callback(func(): shower_done = true)


func Exit() -> void:
	# Leaving during the toss comes before the animation has started the shower.
	if shower:
		shower.kill()
	if phone:
		phone.kill()
	for nugget in nuggets:
		if is_instance_valid(nugget):
			nugget.queue_free()
	if with_carter:
		carter_call.hang_up()


func Physics_Update(_delta: float) -> void:
	if with_carter:
		carter_call.follow_drops()


# The cycle moves on once the last impact has finished playing, and Carter is done.
func Update(_delta: float) -> void:
	if not shower_done or nuggets.any(func(nugget): return is_instance_valid(nugget)):
		return
	if with_carter and is_instance_valid(carter_call.carter):
		return
	state_machine.next_attack(self)


# Carter is set up at the heave, so the rain can be timed around his slams, and sent in once Mason has
# made the call.
func _call_carter() -> void:
	var player = state_machine.get_player()
	if not player:
		return
	var carter: Node2D = carter_call.summon_carter(player)
	carter.marker_sort_y = carter_call.ROPES.position.y
	var sent_at: float = state_machine.shower_call_after + carter_call.phone_duration
	for slam in carter.slam_times(state_machine.elbow_drops[state_machine.cycle_phase]):
		slams.append(sent_at + slam)
	slam_live = carter.hitbox_active_time
	phone = create_tween()
	phone.tween_interval(state_machine.shower_call_after)
	phone.tween_callback(carter_call.pick_up_phone)
	phone.tween_interval(carter_call.phone_duration)
	phone.tween_callback(carter_call.send_carter)


func _near_a_slam(landing: float) -> bool:
	for slam in slams:
		if landing > slam - state_machine.slam_clear_before - SLAM_CLEAR_GUARD and landing < slam + slam_live + state_machine.slam_clear_after + SLAM_CLEAR_GUARD:
			return true
	return false


func _drop_nugget(aimed: bool, drop_time: float) -> void:
	var spot: Vector2
	var player = state_machine.get_player()
	if aimed and player:
		var hurtbox_shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
		var target: Vector2 = player.global_position
		var box: Rect2 = hurtbox_shape.global_transform * hurtbox_shape.shape.get_rect()
		if rain:
			var area: Rect2 = state_machine.BOMB_AREA
			var lead: Vector2 = player.velocity.limit_length(state_machine.RAIN_LEAD_CAP) * warning * state_machine.rain_lead
			var led: Vector2 = (target + lead).clamp(area.position, area.end)
			box.position += led - target
			target = led
		spot = _aimed_spot(target, box, drop_time)
	else:
		spot = _random_open_spot(drop_time)
	var nugget = state_machine.spawn_hazard(NUGGET_METEOR_SCENE, spot)
	nugget.drop(warning, keep_out.has_point(spot))
	nuggets.append(nugget)
	landing_spots.append(spot)
	landing_times.append(drop_time + warning)


# The nearest spot to the player, clear of other nuggets, whose oval still reaches their hurtbox.
# Standing right by Mason mustn't make a player safe: failing such a spot clear of him too, the nugget
# lands over Mason.
func _aimed_spot(target: Vector2, hurtbox: Rect2, drop_time: float) -> Vector2:
	var area: Rect2 = state_machine.BOMB_AREA
	var center := target.clamp(area.position, area.end)
	# No spot further out can reach the hurtbox, and searching every ring for a player deep inside Mason's
	# keep-out would cost a frame hitch.
	var reach_limit := center.distance_to(hurtbox.get_center()) + maxf(NuggetMeteor.HIT_SIZE.x, NuggetMeteor.HIT_SIZE.y) / 2.0 + hurtbox.size.length() / 2.0
	var over_mason := Vector2.INF
	for ring in SEARCH_RINGS:
		if ring * SEARCH_STEP > reach_limit:
			break
		var points := maxi(1, ring * 6)
		for k in points:
			var spot := (center + Vector2.from_angle(TAU * k / points) * ring * SEARCH_STEP).clamp(area.position, area.end)
			if not _reaches(spot, hurtbox) or not _clear_of_nuggets(spot, drop_time):
				continue
			if not keep_out.has_point(spot):
				return spot
			if over_mason == Vector2.INF:
				over_mason = spot
	if over_mason != Vector2.INF:
		return over_mason
	return _nearest_open_spot(center, drop_time)


func _reaches(spot: Vector2, hurtbox: Rect2) -> bool:
	# Scaled so the oval, shrunk by the overlap it needs, is the unit circle.
	var semi_axes := NuggetMeteor.HIT_SIZE / 2.0 - Vector2.ONE * MIN_PLAYER_OVERLAP
	return ((spot.clamp(hurtbox.position, hurtbox.end) - spot) / semi_axes).length() < 1.0


# Nuggets land anywhere a poo bomb can: of the phase's nugget_spread open spots, the one with the most
# room around it.
func _random_open_spot(drop_time: float) -> Vector2:
	var area: Rect2 = state_machine.BOMB_AREA
	var wanted: int = state_machine.rain_spread if rain else state_machine.nugget_spread[state_machine.cycle_phase]
	var spot := Vector2.ZERO
	var best := Vector2.INF
	var best_room := -1.0
	var found := 0
	for attempt in RANDOM_TRIES:
		spot = Vector2(randf_range(area.position.x, area.end.x), randf_range(area.position.y, area.end.y))
		if not _is_open(spot, drop_time):
			continue
		var room := _room_around(spot)
		if room > best_room:
			best_room = room
			best = spot
		found += 1
		if found >= wanted:
			break
	if best != Vector2.INF:
		return best
	return _nearest_open_spot(spot, drop_time)


# How far the nearest of this shower's landings is, aimed or not and landed or not, counted twice over
# up and down: the ovals are twice as wide as they are tall, and so is the mat they have to cover.
func _room_around(spot: Vector2) -> float:
	var room := INF
	for other in landing_spots:
		room = minf(room, ((other - spot) * Vector2(1.0, 2.0)).length())
	return room


func _nearest_open_spot(aim: Vector2, drop_time: float) -> Vector2:
	var area: Rect2 = state_machine.BOMB_AREA
	var center := aim.clamp(area.position, area.end)
	for ring in SEARCH_RINGS:
		var points := maxi(1, ring * 6)
		for k in points:
			var spot := (center + Vector2.from_angle(TAU * k / points) * ring * SEARCH_STEP).clamp(area.position, area.end)
			if _is_open(spot, drop_time):
				return spot
	return center


func _is_open(spot: Vector2, drop_time: float) -> bool:
	return not keep_out.has_point(spot) and _clear_of_nuggets(spot, drop_time)


func _clear_of_nuggets(spot: Vector2, drop_time: float) -> bool:
	for i in landing_spots.size():
		if landing_times[i] > drop_time and landing_spots[i].distance_to(spot) < nugget_spacing:
			return false
	return true
