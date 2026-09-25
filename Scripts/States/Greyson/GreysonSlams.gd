extends State

# Greyson's slams (plan sections 3.2 and 3.3), the second link of attack 1, while his plates are still out: five
# teleports to the spot furthest from the player, each with a barbell slam that plants an eruption zone, then a
# teleport home. The zones wait in the state machine's queue, all five, for the poses after (GreysonPose) to set
# them off one by one; first_eruption_before can have one go off during the slams instead.
#   0.00  out, then in at the furthest spot
#   0.50  the wind-up: the barbell overhead
#   0.90  SLAM 1 on the sheet's impact frame: zone 1 on the player's feet
#   1.30  out and in again; SLAM 2 at 2.20: zone 2
#   2.60  again; SLAM 3 at 3.50: zone 3
#   3.90  again; SLAM 4 at 4.80: zone 4
#   5.20  again; SLAM 5 at 6.10: zone 5
#   6.50  out, and in at HOME
#   7.00  done: the barbell planted and the turn to the crowd are GreysonPose's opening beat
# Each beat carries whatever its last step ran over into the next, so the slams stay on these times to the frame.
# He can't be hit here: every teleport_out() turns his hurtbox off.
#
# THE FENCE (zone_spot): every zone goes on the player's feet, unless they are standing in a zone still waiting
# and a zone on them would share more than fence_overlap of its area with one - standing still would stack the
# five into one burst to step out of once. Then it goes beside the waiting ones instead, touching them or lightly
# over them, wherever it keeps the most of the player's floor blocked until later: the floor round them, where
# they'd step out to, and their way to him. A player who stands still is boxed in by bursts that go off one at a
# time, so reaching him mid-pose means weaving through them. A player who has walked clear of every waiting zone is
# aimed at as ever.

const ZONE_SCRIPT := preload("res://Scripts/GreysonEruptionScript.gd")
const Layout := preload("res://Scripts/GreysonArtLayout.gd")

@export var body : CharacterBody2D

#KNOBS (seconds, px)
@export var slams := 5
# Out, then in: each.
@export var teleport_time := 0.25
# The slam sheet's impact frame, f3, is this far in.
@export var windup_time := 0.40
@export var recover_time := 0.40
# Zone centres are kept this far inside the ropes. None, so zone 1 is right on the feet and walking out of it is
# never longer than its ry; the art is cut to the floor anyway.
@export var zone_inset := 0.0
# Which slam's teleport tells zone 1 to go off, timed to his landing; 0 for none, the poses then setting off all
# five. The poses set off the zones left in order, so with one told here, drop the first of GreysonPose's
# eruptions to keep the last on pose 3's end.
@export var first_eruption_before := 0

#FENCE (px unless said)
# The most of its area a zone may share with any one waiting zone before it goes beside them instead.
@export var fence_overlap := 0.25
# Beside: no further than this from a waiting zone, in zone radii between centres (2 is touching).
@export var fence_touch := 2.0
# The spots it tries, this far apart over the floor.
@export var fence_step := 32.0
# The floor it keeps blocked: rings this far round the player's feet, in this many directions, a point each; and
# their way to him, straight to HOME and his two sides, fence_home_weight points each.
@export var fence_reach: Array[float] = [150.0, 300.0, 450.0, 600.0]
@export var fence_directions := 24
@export var fence_home_weight := 4.0
@export var fence_home_side := 110.0

@onready var state_machine = get_parent()

var radii: Vector2 = Layout.fx(&"zone").radii

enum Beat { OUT, IN, WINDUP, RECOVER }

# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
var beat := Beat.OUT
var beat_clock := 0.0
var slammed := 0
var spot := Vector2.ZERO
# For tests: each teleport's landing spot and the player's feet it was picked against, when each slam landed
# (fight_clock), each zone, where it went, the player's feet as it did and how it was placed (&"aimed", &"fence",
# or &"least" when nothing beside kept under fence_overlap), and when zone 1 was told and he landed after it.
var spots: Array[Vector2] = []
var picked_from: Array[Vector2] = []
var slam_clocks: Array[float] = []
var zones: Array[Node2D] = []
var zone_centres: Array[Vector2] = []
var slam_feet: Array[Vector2] = []
var placements: Array[StringName] = []
var told_clock := -1.0
var landed_clock := -1.0
var entered_count := 0


func Enter() -> void:
	released = false
	entered_count += 1
	slammed = 0
	spots.clear()
	picked_from.clear()
	slam_clocks.clear()
	zones.clear()
	zone_centres.clear()
	slam_feet.clear()
	placements.clear()
	told_clock = -1.0
	landed_clock = -1.0
	beat_clock = 0.0
	body.velocity = Vector2.ZERO
	body.set_hurtbox_active(false)
	_teleport_out()


func Physics_Update(delta: float) -> void:
	if released:
		return
	beat_clock += delta
	match beat:
		Beat.OUT:
			if beat_clock >= teleport_time:
				beat_clock -= teleport_time
				_teleport_in()
		Beat.IN:
			if beat_clock >= teleport_time:
				beat_clock -= teleport_time
				if slammed < slams:
					_wind_up()
				else:
					body.sprite.visible = true
					state_machine.chain_next(self)
		Beat.WINDUP:
			if beat_clock >= windup_time:
				beat_clock -= windup_time
				_slam()
		Beat.RECOVER:
			if beat_clock >= recover_time:
				beat_clock -= recover_time
				_teleport_out()


func Exit() -> void:
	release()


# A teleport cut short leaves him hidden: whatever takes over finds him visible where he is.
func release() -> void:
	if released:
		return
	released = true
	if is_instance_valid(body):
		body.sprite.visible = true


func _exit_tree() -> void:
	released = true


# "The furthest point in the arena away from the player", never the one he is on; home after the last slam.
func _teleport_out() -> void:
	beat = Beat.OUT
	var feet: Vector2 = state_machine.player_feet()
	spot = state_machine.furthest_spot(feet, body.global_position) if slammed < slams else state_machine.HOME
	spots.append(spot)
	picked_from.append(feet)
	if slammed + 1 == first_eruption_before:
		state_machine.schedule_next_eruption(2.0 * teleport_time)
		told_clock = body.fight_clock
	body.teleport_out()


func _teleport_in() -> void:
	beat = Beat.IN
	body.teleport_in(spot)
	if slammed + 1 == first_eruption_before:
		landed_clock = body.fight_clock + teleport_time


func _wind_up() -> void:
	beat = Beat.WINDUP
	body.sprite.visible = true
	var player: Node2D = state_machine.get_player()
	if player:
		body.face_toward(player.global_position)
	body.play_anim(&"slam")
	body.play_sfx(&"slam_windup")


# The barbell meets the mat: its burst where it hits, and a zone where zone_spot puts it for the player's feet as
# they are now.
func _slam() -> void:
	beat = Beat.RECOVER
	body.play_fx(&"slam", body.impact_point(&"slam"))
	body.play_sfx(&"barbell_slam")
	var feet: Vector2 = state_machine.player_feet()
	var waiting: Array[Vector2] = []
	for pending in state_machine.live_zones():
		waiting.append(pending.global_position)
	var placed := zone_spot(feet, waiting)
	var zone: Node2D = ZONE_SCRIPT.new()
	zone.player = state_machine.get_player()
	zone.body = body
	state_machine.add_hazard(zone, placed.centre, body.floor_layer)
	state_machine.add_pending_zone(zone)
	zones.append(zone)
	zone_centres.append(zone.global_position)
	slam_feet.append(feet)
	placements.append(placed.kind)
	slam_clocks.append(body.fight_clock)
	slammed += 1


# Where a zone goes, with the player's feet and the zones still waiting where they are: {centre, kind}. On the
# feet, unless the player stands in a waiting zone and a zone on them would share more than fence_overlap of its
# area with one; then beside them (_fence). Public, so a test can sweep it.
func zone_spot(feet: Vector2, waiting: Array[Vector2]) -> Dictionary:
	var area: Rect2 = state_machine.ROPES.grow(-zone_inset)
	var aim := feet.clamp(area.position, area.end)
	var standing_in := false
	var shared := 0.0
	for centre in waiting:
		standing_in = standing_in or _span(feet - centre) <= 1.0
		shared = maxf(shared, _shared(_span(aim - centre)))
	if not standing_in or shared <= fence_overlap:
		return {centre = aim, kind = &"aimed"}
	return _fence(feet, waiting, area)


# Beside the waiting zones: of the spots fence_step apart over `area` that share at most fence_overlap with each
# and touch one, the one keeping the most of the player's floor (_floor_marks) blocked until later - a point no
# waiting zone covers gains the most, one only the soonest covers the least. Nearest the feet on a tie. None of
# them keeping under fence_overlap: the one sharing least.
func _fence(feet: Vector2, waiting: Array[Vector2], area: Rect2) -> Dictionary:
	var points := PackedVector2Array()
	var weights := PackedFloat32Array()
	_floor_marks(feet, points, weights)
	# Worked in zone radii, so a zone is the unit circle round its centre.
	var unit := Vector2(1.0 / radii.x, 1.0 / radii.y)
	var gains := PackedFloat32Array()
	gains.resize(points.size())
	for i in points.size():
		var latest := 0
		for j in waiting.size():
			if ((points[i] - waiting[j]) * unit).length_squared() <= 1.0:
				latest = j + 1
		gains[i] = weights[i] * (waiting.size() + 1 - latest)
	var closest := _span_sharing(fence_overlap)
	var best := {centre = feet, kind = &"least"}
	var best_score := -1.0
	var best_gap := INF
	var least_shared := INF
	var y := area.position.y
	while y <= area.end.y:
		var x := area.position.x
		while x <= area.end.x:
			var centre := Vector2(x, y)
			var nearest := INF
			for pending in waiting:
				nearest = minf(nearest, ((centre - pending) * unit).length())
			if best_score < 0.0 and _shared(nearest) < least_shared:
				least_shared = _shared(nearest)
				best.centre = centre
			if nearest >= closest and nearest <= fence_touch:
				var score := 0.0
				for i in points.size():
					if ((points[i] - centre) * unit).length_squared() <= 1.0:
						score += gains[i]
				var gap := centre.distance_to(feet)
				if score > best_score or (score == best_score and gap < best_gap):
					best = {centre = centre, kind = &"fence"}
					best_score = score
					best_gap = gap
			x += fence_step
		y += fence_step
	return best


# The floor a fence zone keeps blocked, into `points` with their `weights`: rings round the feet, and the way to
# him.
func _floor_marks(feet: Vector2, points: PackedVector2Array, weights: PackedFloat32Array) -> void:
	var ropes: Rect2 = state_machine.ROPES
	for reach in fence_reach:
		for i in fence_directions:
			var point := feet + Vector2.from_angle(TAU * i / fence_directions) * reach
			if ropes.has_point(point):
				points.append(point)
				weights.append(1.0)
	var home: Vector2 = state_machine.HOME
	var steps := maxi(ceili(feet.distance_to(home) / 40.0), 1)
	for i in steps + 1:
		points.append(feet.lerp(home, float(i) / steps))
		weights.append(fence_home_weight)
	for side in [-1.0, 1.0]:
		points.append(home + Vector2(fence_home_side * side, 0.0))
		weights.append(fence_home_weight)


# How far apart two zone centres are, in zone radii: 1 is one's centre on the other's edge, 2 touching.
func _span(offset: Vector2) -> float:
	return Vector2(offset.x / radii.x, offset.y / radii.y).length()


# The share of a zone's area another the same size covers with their centres `span` radii apart.
static func _shared(span: float) -> float:
	if span >= 2.0:
		return 0.0
	return (2.0 * acos(span / 2.0) - span / 2.0 * sqrt(4.0 - span * span)) / PI


# The least span that keeps the shared area at or under `share`.
static func _span_sharing(share: float) -> float:
	var low := 0.0
	var high := 2.0
	for i in 40:
		var middle := (low + high) / 2.0
		if _shared(middle) > share:
			low = middle
		else:
			high = middle
	return high
