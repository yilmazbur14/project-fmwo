extends Node2D

# One of the fifteen shapes that rush the player during Carter's Raging Demon. It materialises out of
# the dark at the edge of the spotlight with a light over its head - RED to parry, YELLOW a feint
# that punishes a parry, or the hot white PUNISH that only ever follows a feint the player bit on and
# that nothing answers - holds while the player reads it, then covers the gap and strikes.
# It is much smaller than Carter, forms and dissolves rather than appearing and vanishing, and every
# bit of that happens at the START of the read window: a clone still resolving when the player has to
# decide would eat the reaction time the whole mechanic depends on.
# It reports its own hit rather than letting the player's hurtbox find it, because the sequence needs
# the result: a stopped clone breaks, one that landed leaves the strike burst, and both are tallied
# for the banked damage and the punish window.
# There is no Area2D and no "enemy projectile" group on purpose. The contact instant is a number the
# sequence owns (CarterRagingDemon), not an overlap, and the hit's origin is the PLAYER's own hurtbox
# centre, inside PlayerDefense.block_omni_radius, so a clone arriving from behind is as answerable as
# one from the front. This is a timing check, not an aiming one.
# Each clone is its own node and so its own hit source: PlayerDefense keeps absorbed_until per source
# for blocked_rehit_interval (1.0 s) and the clones come 0.70 s apart, so sharing one source would
# make every clone after a blocked or parried one free - which is exactly what the barrage is not
# allowed to do.

const CarterArtLayout := preload("res://Scripts/CarterArtLayout.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")

@export var sprite: Sprite2D
@export var light: Node2D

# Set by the sequence before it enters the tree. A clone is a red, a feint, or - only ever directly
# after a feint the player bit on - a punish, which nothing can answer.
var is_feint := false
var is_punish := false
var from_point := Vector2.ZERO
var to_point := Vector2.ZERO
var player: Node2D
var body: Node

var spent := false
var travel_time := 0.0
var travel_clock := 0.0
var launched := false
var passing := false
var pass_clock := 0.0
var pass_step := Vector2.ZERO
var light_clock := 0.0
var light_sprite: Sprite2D
var shade: Polygon2D
var ghost: Sprite2D
var ghost_clock := 0.0
var body_clock := 0.0


func _ready() -> void:
	global_position = from_point
	_build_ghost()
	_build_body()
	_build_light()
	light.hide()
	body_clock = 0.0
	# The sheet's own frames carry the gather and the scatter, so nothing here ramps alpha on top of
	# them; only the placeholder, which has no frames to carry it, fades in code.
	if not CarterArtLayout.USE_FINAL_CLONE:
		modulate.a = 0.0
		var form := create_tween()
		form.tween_property(self, "modulate:a", 1.0, CarterArtLayout.CLONE_FADE_IN)


func _physics_process(delta: float) -> void:
	_animate(delta)
	if passing:
		pass_clock += delta
		global_position += pass_step * delta
		if pass_clock >= CarterArtLayout.CLONE_PASS_TIME:
			queue_free()
		return
	if not launched or spent:
		return
	travel_clock += delta
	var weight := clampf(travel_clock / maxf(travel_time, 0.0001), 0.0, 1.0)
	global_position = from_point.lerp(to_point, weight).round()


func _animate(delta: float) -> void:
	body_clock += delta
	if sprite.texture:
		_step_body()
	if ghost:
		# Only while it is actually moving: a trail behind a shape standing still reads as a smear.
		ghost.visible = launched
		ghost_clock += delta
		ghost.frame = int(ghost_clock / CarterArtLayout.FINAL_CLONE_GHOST.frame_time) % ghost.hframes
	if not light.visible:
		return
	light_clock += delta
	if light_sprite:
		light_sprite.frame = _light_frame()
	if is_punish:
		var spec := CarterArtLayout.PUNISH_CLONE
		var beat := 0.5 + 0.5 * sin(TAU * light_clock / (spec.beat_time * 2.0))
		light.scale = Vector2.ONE * spec.light_scale * lerpf(spec.beat[0], spec.beat[1], beat)


# Gathers out of nothing, holds full strength while it commits and travels, then scatters away.
func _step_body() -> void:
	var art := CarterArtLayout.FINAL_CLONE
	if passing:
		sprite.frame = art.dissipate[_step_of(art.dissipate_times, pass_clock)]
		return
	var formed: float = _phase_length(art.appear_times)
	if body_clock < formed:
		sprite.frame = art.appear[_step_of(art.appear_times, body_clock)]
		return
	var rush: Array = art.rush
	sprite.frame = rush[int((body_clock - formed) / art.rush_time) % rush.size()]


# Ignite, peak, then the hold frame steady for the whole reaction window. Never pulsed and never
# looped: a tell that flickers gets re-read instead of acted on. Only a clone that has already gone
# past ever shows the fade.
func _light_frame() -> int:
	var spec := CarterArtLayout.FINAL_CLONE_LIGHT
	var steps: Dictionary = spec.yellow if is_feint else spec.red
	if passing:
		return steps.fade
	if light_clock < spec.ignite_time:
		return steps.ignite
	if light_clock < spec.ignite_time + spec.peak_time:
		return steps.peak
	return steps.hold


# The read. Called on the frame the clone appears, and it is the same frame the sequence re-arms the
# player's parry on: every clone is a clean, independent reaction test.
func show_light() -> void:
	light_clock = 0.0
	if light_sprite:
		light_sprite.frame = _light_frame()
	light.show()


func launch(seconds: float) -> void:
	travel_time = seconds
	travel_clock = 0.0
	launched = true


# Red: the hit is built from the player's own hurtbox centre, so any facing can answer it.
# Yellow: never reaches the player at all - it passes through and dissolves.
# Punish: the same hit under an id nothing can block or parry.
func strike() -> int:
	if spent:
		return HitInfo.Result.IGNORED
	spent = true
	if is_feint:
		_begin_pass()
		return HitInfo.Result.IGNORED
	if not is_instance_valid(player):
		dissipate(false, global_position)
		return HitInfo.Result.IGNORED
	# No dodge-ghost branch: the origin IS the player's hurtbox centre, so the clone can never reach
	# the spot a dash left without reaching the player, and a locked player can't dash anyway.
	var contact := _player_hurtbox_centre()
	var attack: StringName = &"carter_clone_punish" if is_punish else &"carter_clone_rush"
	var result: int = player.receive_hit(HitInfo.make(attack, self, contact, body))
	dissipate(result == HitInfo.Result.PARRIED or result == HitInfo.Result.BLOCKED, contact)
	return result


func dissipate(stopped: bool, at: Vector2) -> void:
	_burst(stopped, at)
	queue_free()


# A feint carries on past the player and scatters away as it goes.
func _begin_pass() -> void:
	passing = true
	pass_clock = 0.0
	var direction := (to_point - from_point).normalized()
	pass_step = direction * (to_point.distance_to(from_point) / maxf(travel_time, 0.0001))
	# The light goes out fast - faster than the body scatters - so it is gone before the next clone's
	# light comes up. This is the light's own node, not the clone art, whose fade is authored in.
	var dim := light.create_tween()
	dim.tween_property(light, "modulate:a", 0.0, CarterArtLayout.CLONE_LIGHT_OUT)
	if not CarterArtLayout.USE_FINAL_CLONE:
		var fade := create_tween()
		fade.tween_property(self, "modulate:a", 0.0, CarterArtLayout.CLONE_PASS_TIME)


func _player_hurtbox_centre() -> Vector2:
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	return shape.global_position


# Left on the layer the clone was on, so it plays out after the clone is gone. Its first frame is
# drawn the moment it is added, which is the frame the parry resolved on.
func _burst(stopped: bool, at: Vector2) -> void:
	var parent := get_parent()
	if parent == null:
		return
	var spec: Dictionary = CarterArtLayout.clone_shatter() if stopped else CarterArtLayout.clone_hit()
	if spec.has("texture"):
		var sheet := Sprite2D.new()
		sheet.texture = load(spec.texture)
		sheet.hframes = spec.hframes
		sheet.scale = Vector2.ONE * spec.scale
		sheet.offset = spec.frame_size / 2.0 - spec.pivot
		sheet.z_index = CarterArtLayout.BURST_Z
		if spec.get("additive", false):
			sheet.material = CarterArtLayout.additive()
		parent.add_child(sheet)
		sheet.global_position = at.round()
		var times: Array = spec.frame_times
		var play := sheet.create_tween()
		for i in range(1, spec.hframes):
			play.tween_interval(times[i - 1])
			play.tween_callback(func() -> void: sheet.frame = i)
		play.tween_interval(times[times.size() - 1])
		play.tween_callback(sheet.queue_free)
		return

	var burst := Polygon2D.new()
	if stopped:
		burst.polygon = CarterArtLayout.star(spec.points, spec.radius, spec.inner_ratio)
	else:
		burst.polygon = CarterArtLayout.ellipse(spec.radii, spec.points)
	burst.color = spec.color
	burst.scale = Vector2.ONE * spec.from_scale
	burst.z_index = CarterArtLayout.BURST_Z
	parent.add_child(burst)
	burst.global_position = at.round()
	var play := burst.create_tween()
	play.tween_property(burst, "scale", Vector2.ONE * spec.to_scale, spec.time)
	play.parallel().tween_property(burst, "modulate:a", 0.0, spec.time)
	play.tween_callback(burst.queue_free)


func _build_body() -> void:
	# Drawn facing right, so a clone rushing left mirrors; the symmetry axis is the anchor's column,
	# which keeps its feet where they are.
	var facing_left := to_point.x < from_point.x
	if not CarterArtLayout.USE_FINAL_CLONE:
		sprite.hide()
		shade = Polygon2D.new()
		shade.polygon = CarterArtLayout.clone_shape()
		shade.color = CarterArtLayout.PLACEHOLDER_CLONE.color
		shade.scale = Vector2(-1.0 if facing_left else 1.0, 1.0)
		add_child(shade)
		var rim := Line2D.new()
		rim.points = shade.polygon
		rim.closed = true
		rim.width = CarterArtLayout.PLACEHOLDER_CLONE.rim_width
		rim.default_color = CarterArtLayout.PLACEHOLDER_CLONE.rim_color
		shade.add_child(rim)
		return

	var art := CarterArtLayout.FINAL_CLONE
	var sheet: Texture2D = load(art.sheet)
	sprite.texture = sheet
	sprite.hframes = roundi(sheet.get_width() / CarterArtLayout.CLONE_FRAME_SIZE.x)
	sprite.offset = CarterArtLayout.clone_sheet_offset()
	sprite.scale = Vector2.ONE * CarterArtLayout.CLONE_SCALE
	sprite.frame = art.appear[0]
	sprite.flip_h = facing_left
	modulate.a = CarterArtLayout.CLONE_ALPHA
	if is_punish:
		sprite.modulate = CarterArtLayout.PUNISH_CLONE.tint


# Purely the tail: it erases the clone's own footprint, and the clone drawn on top of it provides the
# figure. It shares the clone's offset, which is all it takes to line the two frames up.
func _build_ghost() -> void:
	if not CarterArtLayout.USE_FINAL_CLONE or not CarterArtLayout.USE_FINAL_CLONE_GHOST:
		return
	var spec := CarterArtLayout.FINAL_CLONE_GHOST
	ghost = Sprite2D.new()
	ghost.texture = load(spec.texture)
	ghost.hframes = spec.hframes
	ghost.scale = Vector2.ONE * spec.scale
	ghost.offset = CarterArtLayout.clone_sheet_offset()
	ghost.flip_h = to_point.x < from_point.x
	ghost.z_index = CarterArtLayout.CLONE_GHOST_Z
	ghost.hide()
	add_child(ghost)


func _build_light() -> void:
	light.position = CarterArtLayout.clone_light_anchor()
	light.z_index = CarterArtLayout.CLONE_LIGHT_Z
	if is_punish:
		light.scale = Vector2.ONE * CarterArtLayout.PUNISH_CLONE.light_scale
	var sheet := CarterArtLayout.clone_light()
	if sheet.has("texture"):
		light_sprite = Sprite2D.new()
		light_sprite.texture = load(sheet.texture)
		light_sprite.hframes = sheet.hframes
		light_sprite.scale = Vector2.ONE * sheet.scale
		light_sprite.offset = sheet.frame_size / 2.0 - sheet.pivot
		if is_punish:
			light_sprite.modulate = CarterArtLayout.PUNISH_CLONE.light_tint
		light.add_child(light_sprite)
		return

	var spec: Dictionary = sheet.yellow if is_feint else sheet.red
	if spec.shape == "ring":
		var ring := Line2D.new()
		ring.points = CarterArtLayout.ellipse(Vector2.ONE * spec.radius, spec.points)
		ring.closed = true
		ring.width = spec.width
		ring.default_color = spec.color
		light.add_child(ring)
		return
	var gem := Polygon2D.new()
	gem.polygon = CarterArtLayout.diamond(spec.radius)
	gem.position = Vector2(0, spec.radius)
	gem.color = spec.color
	light.add_child(gem)


# Where a phase's frame `clock` seconds in has got to, and how long the whole phase runs.
func _step_of(times: Array, clock: float) -> int:
	var total := 0.0
	for i in times.size():
		total += times[i]
		if clock < total:
			return i
	return times.size() - 1


func _phase_length(times: Array) -> float:
	var total := 0.0
	for time in times:
		total += time
	return total
