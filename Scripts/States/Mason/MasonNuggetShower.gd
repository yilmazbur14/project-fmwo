extends State

@export var animation_player : AnimationPlayer
@export var toss_sfx_player : AudioStreamPlayer

const NUGGET_METEOR_SCENE := "res://Scenes/Bosses/NuggetMeteorScene.tscn"
const NuggetMeteor := preload("res://Scripts/NuggetMeteorScript.gd")
# The length of the nugget_toss animation.
const TOSS_TIME := 1.0
const TARGET_EVERY := 3
# No marker goes down this close to a nugget due to land after it appears. Nuggets already landing don't
# count, or the aimed nugget after one that hit a player standing still would be pushed off them.
const NUGGET_SPACING := 110.0
const RANDOM_TRIES := 30
# An aimed nugget that can't land right on the player moves to the nearest open spot, searched for on
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
	toss_sfx_player.play()
	keep_out = state_machine.keep_out_around_mason(NuggetMeteor.footprint())
	nuggets.clear()
	landing_spots.clear()
	landing_times.clear()
	shower_done = false

	var phase: int = state_machine.cycle_phase
	var count: int = state_machine.NUGGET_COUNT[phase]
	var interval: float = state_machine.NUGGET_SHOWER_TIME[phase] / count
	# One tween runs the whole shower, so leaving the state stops it in one go.
	shower = create_tween()
	shower.tween_interval(TOSS_TIME)
	shower.tween_callback(animation_player.play.bind("nugget_hold"))
	for i in count:
		if i > 0:
			shower.tween_interval(interval)
		shower.tween_callback(_drop_nugget.bind((i + 1) % TARGET_EVERY == 0, i * interval))
	shower.tween_callback(func(): shower_done = true)


func Exit() -> void:
	shower.kill()
	for nugget in nuggets:
		if is_instance_valid(nugget):
			nugget.queue_free()


# The cycle moves on once the last impact has finished playing.
func Update(_delta: float) -> void:
	if shower_done and not nuggets.any(func(nugget): return is_instance_valid(nugget)):
		state_machine.next_attack(self)


func _drop_nugget(aimed: bool, drop_time: float) -> void:
	var player = state_machine.get_player()
	var spot := _nearest_open_spot(player.global_position, drop_time) if aimed and player else _random_open_spot(drop_time)
	var warning: float = state_machine.NUGGET_WARNING[state_machine.cycle_phase]
	var nugget = state_machine.spawn_hazard(NUGGET_METEOR_SCENE, spot)
	nugget.drop(warning)
	nuggets.append(nugget)
	landing_spots.append(spot)
	landing_times.append(drop_time + warning)


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
	if keep_out.has_point(spot):
		return false
	for i in landing_spots.size():
		if landing_times[i] > drop_time and landing_spots[i].distance_to(spot) < NUGGET_SPACING:
			return false
	return true
