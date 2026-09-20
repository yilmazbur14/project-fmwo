extends Node2D

# The red mark on the floor under the spot Eric's thrown sword is going to land on: a fixed target
# ring saying where, a second ring closing onto it saying when, and a commit frame lit for exactly
# PlayerDefense.parry_window before the blade arrives.
# It has no clock of its own. The sword pushes its own flight progress in through set_progress(), so
# the closing ring can't drift from the blade and it stops dead wherever the sword does: a finisher's
# freeze, a hit-stop, the pause screen.
# It lives on the fight's floor layer rather than under the sword, so it stays put while the sword
# flies over it. The sword ends it on every path instead: land() when the blade goes in, cancel()
# when a parry stops it in the air, and the fight ending frees it with every other hazard.

const DefenseHypeArtLayout := preload("res://Scripts/DefenseHypeArtLayout.gd")

# The flight progress the commit frame lights at; the sword sets it from the parry window.
var commit_at := 1.0

var spec: Dictionary
var sprite: Sprite2D
# The placeholder's rings: the fixed target and the one closing onto it.
var target_ring: Line2D
var closing_ring: Line2D
var impact_step := 0
var impact_clock := 0.0


func _ready() -> void:
	set_process(false)
	spec = DefenseHypeArtLayout.sword_mark()
	if spec.has("texture"):
		_build_sprite()
	else:
		_build_rings()
	set_progress(0.0)


# 0 as the sword leaves his hand, 1 as it arrives.
func set_progress(t: float) -> void:
	var committed := t >= commit_at
	# 0 when the blade arrives inside a parry window of the release: there is no closing to draw, the
	# whole flight is the window.
	var closed := 1.0 if commit_at <= 0.0 else clampf(t / commit_at, 0.0, 1.0)
	if sprite:
		sprite.frame = spec.commit_frame if committed else mini(int(closed * spec.close_frames), spec.close_frames - 1)
		return
	closing_ring.visible = not committed
	closing_ring.scale = Vector2.ONE * lerpf(spec.close_scale[0], spec.close_scale[1], closed)
	target_ring.default_color = spec.commit_color if committed else spec.color


# The blade went in: the flash plays itself out and the mark goes with it.
func land() -> void:
	impact_step = 0
	impact_clock = 0.0
	_show_impact()
	set_process(true)


# Parried in the air, so nothing is going to land there. It leaves the way the tells do.
func cancel() -> void:
	set_process(false)
	var fade := create_tween()
	fade.tween_property(self, "modulate:a", 0.0, DefenseHypeArtLayout.PARRY_TELL_FADE_OUT)
	fade.tween_callback(queue_free)


func _process(delta: float) -> void:
	impact_clock += delta
	if impact_clock < spec.impact_frame_times[impact_step]:
		return
	impact_clock = 0.0
	impact_step += 1
	if impact_step >= spec.impact_frame_times.size():
		queue_free()
		return
	_show_impact()


func _show_impact() -> void:
	if sprite:
		sprite.frame = spec.impact_frames[impact_step]
		return
	closing_ring.visible = false
	target_ring.default_color = spec.commit_color
	target_ring.scale = Vector2.ONE * spec.impact_scale[impact_step]


func _build_sprite() -> void:
	sprite = Sprite2D.new()
	sprite.texture = load(spec.texture)
	sprite.hframes = spec.hframes
	sprite.centered = false
	sprite.offset = -spec.pivot
	sprite.scale = Vector2.ONE * spec.scale
	add_child(sprite)


func _build_rings() -> void:
	closing_ring = _ring()
	closing_ring.width = spec.width * 0.66
	target_ring = _ring()
	add_child(closing_ring)
	add_child(target_ring)


func _ring() -> Line2D:
	var ring := Line2D.new()
	var points := PackedVector2Array()
	for i in spec.points:
		var step := Vector2.from_angle(TAU * i / spec.points)
		points.append(Vector2(step.x, step.y * spec.squash) * spec.radius)
	ring.points = points
	ring.closed = true
	ring.width = spec.width
	ring.default_color = spec.color
	return ring
