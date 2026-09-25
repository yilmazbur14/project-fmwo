extends Node2D

# One fireball of beast Bixby's Inferno coming back down (BixbyBeastInferno): a marker on the landing spot
# for the whole warning, the ball dropping straight onto it over the last of it, then a burst that hurts
# for a moment and leaves a scorch mark fading on the floor. The marker IS the warning, as the nugget's is
# (NuggetMeteorScript), so nothing puts a ParryTell over it. Its timing all runs in _physics_process, so a
# freeze holds it.

# The ball has hit the floor: its burst is live from here.
signal landed

const InfernoLayout := preload("res://Scripts/BixbyInfernoArtLayout.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")

enum Phase { WAITING, WARNING, IMPACT, SCORCH }

var phase := Phase.WAITING
var clock := 0.0
var warning_time := 1.0
var hit_live := false
var ball_frames: Array = []
var ball_frame_time := 0.06
var impact_frames: Array = []
var impact_times: Array = []
var impact_scorch_step := 0

@onready var marker: Node2D = $Marker
@onready var marker_ring: Line2D = $Marker/Ring
@onready var marker_sprite: Sprite2D = $Marker/Sprite
@onready var ball: Node2D = $Ball
@onready var ball_sprite: Sprite2D = $Ball/Sprite
@onready var impact: Sprite2D = $Impact
@onready var floor_layer: Node2D = $Floor
@onready var scorch: Sprite2D = $Floor/Scorch
@onready var hitbox: Area2D = $Hitbox
@onready var hitbox_shape: CollisionShape2D = $Hitbox/CollisionShape2D
@onready var impact_sfx: AudioStreamPlayer = $ImpactSfx


func _ready() -> void:
	hitbox.set_meta(HitInfo.META_ATTACK, &"bixby_fireball")
	(hitbox_shape.shape as ConvexPolygonShape2D).points = InfernoLayout.fireball_oval()
	# The shower lands these where he hangs off the rope over the floor. The marker is its warning, so it
	# lies over him, for a player he has dragged onto his belly, but under the player; the scorch lies flat
	# on the floor under them both. Each is drawn back down on the spot.
	_sort_at(marker, InfernoLayout.MARKER_LAYER_Y)
	_sort_at(floor_layer, InfernoLayout.FLOOR_LAYER_Y)
	if InfernoLayout.USE_FINAL_FIREBALL:
		_dress_final()
	else:
		_dress_placeholder()


# The marker goes down now and the ball lands `warning` seconds later.
func drop(warning: float) -> void:
	warning_time = warning
	_start(Phase.WARNING)
	_show_marker_frame(0)
	marker.show()


func _physics_process(delta: float) -> void:
	if phase == Phase.WAITING:
		return
	clock += delta
	match phase:
		Phase.WARNING:
			_show_marker_frame(_marker_frame(clock))
			var fall := minf(InfernoLayout.FIREBALL_FALL_TIME, warning_time)
			var falling := clock - (warning_time - fall)
			if falling >= 0.0:
				ball.show()
				var weight := clampf(falling / fall, 0.0, 1.0)
				ball.position.y = roundf(lerpf(InfernoLayout.FIREBALL_FALL_START_Y - global_position.y, 0.0, weight))
				ball_sprite.frame = ball_frames[int(falling / ball_frame_time) % ball_frames.size()]
			if clock >= warning_time:
				_land()
		Phase.IMPACT:
			if hit_live and clock >= InfernoLayout.FIREBALL_HIT_TIME:
				_end_hit()
			var step := _impact_step(clock)
			if step < 0:
				_start(Phase.SCORCH)
				impact.hide()
				scorch.frame = 0
				scorch.show()
			else:
				if step >= impact_scorch_step and impact.get_parent() != floor_layer:
					# Its flames were over everyone, as the ball was, but from its first frame of scorch it
					# lies on the floor with the scorch it hands over to: the dark oval never lands on him.
					impact.reparent(floor_layer)
					impact.z_index = 0
				impact.frame = impact_frames[step]
		Phase.SCORCH:
			if hit_live:
				_end_hit()
			var smoulder := InfernoLayout.SCORCH_SMOULDER_TIME
			if clock >= smoulder + InfernoLayout.SCORCH_FADE_TIME:
				queue_free()
			elif clock >= smoulder:
				scorch.frame = 1
				scorch.modulate.a = 1.0 - (clock - smoulder) / InfernoLayout.SCORCH_FADE_TIME


func _start(new_phase: Phase) -> void:
	phase = new_phase
	clock = 0.0


# Sorts `layer` at `y` with everything it holds, which stays drawn where it was.
func _sort_at(layer: Node2D, y: float) -> void:
	var moved := y - layer.global_position.y
	layer.global_position.y = y
	for piece: Node2D in layer.get_children():
		piece.position.y -= moved


func _land() -> void:
	_start(Phase.IMPACT)
	marker.hide()
	ball.hide()
	impact.frame = impact_frames[0]
	impact.show()
	hit_live = true
	# Deferred, as every hazard switching its shape from its own step does.
	hitbox_shape.set_deferred("disabled", false)
	impact_sfx.play()
	landed.emit()


func _end_hit() -> void:
	hit_live = false
	hitbox_shape.set_deferred("disabled", true)


# The nugget target's contract: frames 0 and 1 for a quarter of the warning each, then 2 and 3 flashing.
func _marker_frame(elapsed: float) -> int:
	var quarter := warning_time / 4.0
	if elapsed < quarter * 2.0:
		return int(elapsed / quarter)
	return 2 + int((elapsed - quarter * 2.0) / InfernoLayout.MARKER_FLASH_TIME) % 2


func _show_marker_frame(frame: int) -> void:
	if InfernoLayout.USE_FINAL_FIREBALL:
		marker_sprite.frame = frame
		return
	var look: Array = InfernoLayout.PLACEHOLDER_FIREBALL.marker[frame]
	marker_ring.default_color = look[0]
	marker_ring.width = look[1]


# Which frame of the burst is showing `at` seconds after it landed, or -1 once it is over.
func _impact_step(at: float) -> int:
	var total := 0.0
	for step in impact_frames.size():
		total += impact_times[mini(step, impact_times.size() - 1)]
		if at < total:
			return step
	return -1


func _dress_final() -> void:
	var spec := InfernoLayout.FINAL_FIREBALL
	marker_ring.hide()
	marker_sprite.texture = load(spec.marker)
	marker_sprite.hframes = roundi(marker_sprite.texture.get_width() / spec.marker_frame_size.x)
	ball_sprite.texture = load(spec.ball)
	ball_sprite.hframes = spec.ball_frames
	ball_sprite.vframes = 2
	ball_sprite.offset = spec.fall_offset
	# Row 1, the falling one.
	ball_frames = range(spec.ball_frames, spec.ball_frames * 2)
	ball_frame_time = spec.ball_frame_time
	impact.texture = load(spec.impact)
	impact.hframes = roundi(impact.texture.get_width() / spec.impact_frame_size.x)
	impact.offset = spec.impact_offset
	impact_frames = spec.impact_frames
	impact_scorch_step = spec.impact_scorch_step
	impact_times = spec.impact_times


func _dress_placeholder() -> void:
	var spec := InfernoLayout.PLACEHOLDER_FIREBALL
	marker_sprite.hide()
	var ring := PackedVector2Array()
	for point in InfernoLayout.fireball_oval():
		ring.append(point + Vector2(0, InfernoLayout.MARKER_RAISE))
	marker_ring.points = ring
	var trail: Texture2D = load(InfernoLayout.FIRE_TRAIL_SHEET)
	ball_sprite.texture = trail
	ball_sprite.hframes = InfernoLayout.FIRE_TRAIL_FRAMES
	ball_sprite.offset = spec.ball_offset
	ball_frames = spec.ball_frames
	ball_frame_time = spec.ball_frame_time
	impact.texture = trail
	impact.hframes = InfernoLayout.FIRE_TRAIL_FRAMES
	impact.offset = spec.impact_offset
	impact_frames = spec.impact_frames
	impact_scorch_step = spec.impact_scorch_step
	impact_times = spec.impact_times
