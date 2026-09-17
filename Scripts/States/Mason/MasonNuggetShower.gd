extends State

@export var animation_player : AnimationPlayer
@export var toss_sfx_player : AudioStreamPlayer

const NUGGET_METEOR_SCENE := "res://Scenes/Bosses/NuggetMeteorScene.tscn"
const NuggetMeteor := preload("res://Scripts/NuggetMeteorScript.gd")
const TARGET_EVERY := 3
# No marker goes down this close to a nugget due to land after it appears. Nuggets already landing don't
# count, or the aimed nugget after one that hit a player standing still would be pushed off them.
const NUGGET_SPACING := 110.0
# How deep an aimed nugget moved off the player has to reach into their hurtbox, so the hit registers
# reliably rather than by a hair.
const MIN_PLAYER_OVERLAP := 4.0
const RANDOM_TRIES := 30
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


func Enter() -> void:
	animation_player.play("nugget_toss")
	animation_player.queue("nugget_hold")
	toss_sfx_player.play()
	keep_out = state_machine.keep_out_around_mason(NuggetMeteor.footprint())
	nuggets.clear()
	landing_spots.clear()
	landing_times.clear()
	shower_done = false


# Called by the nugget_toss animation on its heave frame, as the nuggets leave the bucket.
func start_shower() -> void:
	var phase: int = state_machine.cycle_phase
	var count: int = state_machine.NUGGET_COUNT[phase]
	var interval: float = state_machine.NUGGET_SHOWER_TIME[phase] / count
	# One tween runs the whole shower, so leaving the state stops it in one go.
	shower = create_tween()
	for i in count:
		if i > 0:
			shower.tween_interval(interval)
		shower.tween_callback(_drop_nugget.bind((i + 1) % TARGET_EVERY == 0, i * interval))
	shower.tween_callback(func(): shower_done = true)


func Exit() -> void:
	# Leaving during the toss comes before the animation has started the shower.
	if shower:
		shower.kill()
	for nugget in nuggets:
		if is_instance_valid(nugget):
			nugget.queue_free()


# The cycle moves on once the last impact has finished playing.
func Update(_delta: float) -> void:
	if shower_done and not nuggets.any(func(nugget): return is_instance_valid(nugget)):
		state_machine.next_attack(self)


func _drop_nugget(aimed: bool, drop_time: float) -> void:
	var spot: Vector2
	var player = state_machine.get_player()
	if aimed and player:
		var hurtbox_shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
		spot = _aimed_spot(player.global_position, hurtbox_shape.global_transform * hurtbox_shape.shape.get_rect(), drop_time)
	else:
		spot = _random_open_spot(drop_time)
	var warning: float = state_machine.NUGGET_WARNING[state_machine.cycle_phase]
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


# Nuggets land anywhere a poo bomb can.
func _random_open_spot(drop_time: float) -> Vector2:
	var area: Rect2 = state_machine.BOMB_AREA
	var spot := Vector2.ZERO
	for attempt in RANDOM_TRIES:
		spot = Vector2(randf_range(area.position.x, area.end.x), randf_range(area.position.y, area.end.y))
		if _is_open(spot, drop_time):
			return spot
	return _nearest_open_spot(spot, drop_time)


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
		if landing_times[i] > drop_time and landing_spots[i].distance_to(spot) < NUGGET_SPACING:
			return false
	return true
