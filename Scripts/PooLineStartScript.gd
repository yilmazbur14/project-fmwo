extends Node2D

# Where Mason's next line of poo bombs begins, and which way it runs. A line goes off from its start
# outward, so the spot inside this ring is the first the wave clears: it is the answer the player is
# meant to read while Mason is still squatting on it, and run to. The bright stretch sliding out of
# the ring along the path is the line's direction, up before a single bomb has dropped.
# In the "mason_hazard" group, so the sweep that ends a fight takes it with everything else of his.

@export var ring: Line2D
@export var ring_outline: Line2D
@export var path: Line2D
@export var path_outline: Line2D
@export var runner: Line2D
@export var hold_timer: Timer

# The ring stands a little wider than the blast that clears the spot (120 px across).
@export var ring_size := Vector2(196.0, 108.0)
@export var ring_segments := 28
# It breathes between these widths, once per pulse_time.
@export var ring_width := 7.0
@export var ring_pulse_width := 14.0
@export var pulse_time := 0.5
# How much wider the dark backing of a line is than the line drawn on top of it.
@export var outline_extra := 6.0
@export var path_width := 12.0
# The bright stretch of path, and how fast it slides out of the ring.
@export var runner_length := 220.0
@export var runner_speed := 1100.0
# The pop when the first bomb lands on the spot, and the fade once that bomb's blast has cleared it.
@export var flash_time := 0.25
@export var fade_time := 0.35

# Set once the line is laid: the ring is now counting its own spot down to the blast, and frees
# itself after it, so a new line's ring doesn't cut it off.
var holding := false

var clock := 0.0
var flash_left := 0.0
var points := PackedVector2Array()
var reached : Array[float] = []
var path_length := 0.0


func _ready() -> void:
	hold_timer.timeout.connect(_on_hold_timer_timeout)
	var oval := PackedVector2Array()
	for i in ring_segments + 1:
		oval.append(Vector2.from_angle(TAU * i / ring_segments) * ring_size / 2.0)
	ring.points = oval
	ring_outline.points = oval
	path.width = path_width
	path_outline.width = path_width + outline_extra
	runner.width = path_width + outline_extra * 0.5


# The path the line will take out of this spot, in world points.
func show_path(world_points: PackedVector2Array) -> void:
	points = PackedVector2Array()
	reached = [0.0]
	path_length = 0.0
	for point in world_points:
		points.append(point - global_position)
		if points.size() > 1:
			path_length += points[points.size() - 2].distance_to(points[points.size() - 1])
			reached.append(path_length)
	path.points = points
	path_outline.points = points


func flash() -> void:
	flash_left = flash_time


func hold_for(seconds: float) -> void:
	holding = true
	# Timer.start(0) falls back to the timer's old wait_time instead of firing at once.
	if seconds <= 0.0:
		_on_hold_timer_timeout.call_deferred()
		return
	hold_timer.start(seconds)


func _physics_process(delta: float) -> void:
	clock += delta
	flash_left = maxf(flash_left - delta, 0.0)

	var beat := 0.5 - 0.5 * cos(TAU * clock / pulse_time)
	if flash_left > 0.0:
		beat = 1.0
	var width := lerpf(ring_width, ring_pulse_width, beat)
	ring.width = width
	ring_outline.width = width + outline_extra
	_slide_runner()


# A stretch of the path, lit from the ring outward on a loop. It runs off the end of the preview and
# starts again out of the ring, so the direction reads however long the line takes to lay.
func _slide_runner() -> void:
	if path_length <= 0.0:
		runner.points = PackedVector2Array()
		return
	var head := fmod(clock * runner_speed, path_length + runner_length)
	var tail := maxf(head - runner_length, 0.0)
	head = minf(head, path_length)
	if head <= tail:
		runner.points = PackedVector2Array()
		return
	var lit := PackedVector2Array([_point_at(tail)])
	for i in reached.size():
		if reached[i] > tail and reached[i] < head:
			lit.append(points[i])
	lit.append(_point_at(head))
	runner.points = lit


func _point_at(distance: float) -> Vector2:
	for i in range(1, reached.size()):
		if distance > reached[i]:
			continue
		var span := reached[i] - reached[i - 1]
		if span <= 0.0:
			return points[i]
		return points[i - 1].lerp(points[i], (distance - reached[i - 1]) / span)
	return points[points.size() - 1]


func _on_hold_timer_timeout() -> void:
	set_physics_process(false)
	# Bound to this node, so it goes with the ring if the fight frees it mid-fade.
	var fade := create_tween()
	fade.tween_property(self, "modulate:a", 0.0, fade_time)
	fade.tween_callback(queue_free)
