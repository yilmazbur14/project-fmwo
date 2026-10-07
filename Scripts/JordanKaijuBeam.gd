extends Node2D

# The kaiju's Atomic Breath (JordanBreath): a band of blue fire from its mouth to the ropes, laid along the floor and
# swept across it. It lies on the fight's floor layer, under every fighter; the mouth's flare over them is the
# kaiju's own. JordanBreath drives it: aim() for the lock's thin aim line, then sweep_to() every physics step with
# where the mouth is, which way it points and how far it has grown, then stop().
#
# Its hit is BixbySonicSweepScript's swept test, against the player's feet rather than their middle: the band is on
# the floor, so it hurts where they stand on it. Between two steps it is sampled along the arc its tip covered, so a
# fast sweep can't step over them. A dash through it is the dodge; a dash away that it sweeps over the start of is a
# near miss, and both pay a perfect dodge.
# Drawn from its sheets once they are in (JordanKaijuLayout.fx): its body's 32-texel tile repeated along it and turned
# with it, and its splash where it meets the rope; in code until then.

const Layout := preload("res://Scripts/JordanKaijuLayout.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")

const BEAM_ID := &"jordan_kaiju_breath"
const HALF_WIDTH := 45.0
# The player's feet as a circle this big: half their hurtbox's width.
const FOOT_RADIUS := 18.0
const SWEEP_SAMPLE_PX := 24.0
const MAX_SWEEP_SAMPLES := 48
const FADE_TIME := 0.20
const AIM_LINE_WIDTH := 4.0
const CORE_WIDTH := 38.0
const FLICKER_TIME := 0.05
const FRAME_TIME := 0.05

# Set before it is added.
var player: CharacterBody2D
var boss: Node

var origin := Vector2.ZERO
var angle := 0.0
var length := 0.0
var aiming := false
var live := false
var fading := false
var fade_clock := 0.0
var clock := 0.0
var was_origin := Vector2.ZERO
var was_angle := 0.0
var was_length := 0.0
var tracking := false
# For a test: every result it got out of the player, and the near misses it sent.
var results: Array[int] = []
var near_misses := 0
var body_spec: Dictionary = Layout.fx(&"beam_body")
var end_spec: Dictionary = Layout.fx(&"beam_end")
# Loaded before anything draws: a sheet first loaded inside a draw call is drawn as a white box.
var body_texture: Texture2D = Layout.texture(body_spec.sheet) if not body_spec.is_empty() else null
var end_texture: Texture2D = Layout.texture(end_spec.sheet) if not end_spec.is_empty() else null


# The lock's thin line from the mouth along the ray the sweep starts on: no damage.
func aim(at: Vector2, to_angle: float) -> void:
	aiming = true
	live = false
	origin = at
	angle = to_angle
	length = Layout.reach_to_ropes(origin, angle)
	queue_redraw()


# The beam out of `at` pointing `to_angle` radians, `grown` of the way to the ropes: tested against the player over
# the arc it has swept since the last call. Returns what the player made of a hit, or -1.
func sweep_to(at: Vector2, to_angle: float, grown: float) -> int:
	aiming = false
	live = true
	origin = at
	angle = to_angle
	length = Layout.reach_to_ropes(origin, angle) * clampf(grown, 0.0, 1.0)
	if not tracking:
		was_origin = origin
		was_angle = angle
		was_length = length
		tracking = true
	var result := -1
	if is_instance_valid(player) and length > 0.0:
		if _swept_over(feet_of(player.hurtBox.get_node("CollisionShape2D"))):
			result = player.receive_hit(HitInfo.make(BEAM_ID, self, origin, boss))
			results.append(result)
		elif player.dodge_ghost_position() != Vector2.INF and _swept_over(feet_of(player.dodge_ghost.get_node("CollisionShape2D"))):
			player.receive_near_miss(HitInfo.make(BEAM_ID, self, origin, boss))
			near_misses += 1
	was_origin = origin
	was_angle = angle
	was_length = length
	queue_redraw()
	return result


func stop() -> void:
	if fading:
		return
	fading = true
	live = false
	fade_clock = 0.0


# Whether `point` is on the band as it is now.
func covers(point: Vector2) -> bool:
	if not live:
		return false
	var along := (point - origin).rotated(-angle)
	return absf(along.y) <= HALF_WIDTH and along.x >= 0.0 and along.x <= length


func _physics_process(delta: float) -> void:
	clock += delta
	if fading:
		fade_clock += delta
		modulate.a = clampf(1.0 - fade_clock / FADE_TIME, 0.0, 1.0)
		if fade_clock >= FADE_TIME:
			queue_free()
	queue_redraw()


# Whether the band crossed `feet` anywhere between where it was last step and where it is now.
func _swept_over(feet: Vector2) -> bool:
	var turned := wrapf(angle - was_angle, -PI, PI)
	var travelled := was_origin.distance_to(origin) + absf(turned) * maxf(length, was_length)
	var samples := clampi(ceili(travelled / SWEEP_SAMPLE_PX), 1, MAX_SWEEP_SAMPLES)
	var across := HALF_WIDTH + FOOT_RADIUS
	for step in samples + 1:
		var weight := float(step) / samples
		var from := was_origin.lerp(origin, weight)
		var along := (feet - from).rotated(-(was_angle + turned * weight))
		if absf(along.y) <= across and along.x >= -FOOT_RADIUS and along.x <= lerpf(was_length, length, weight) + FOOT_RADIUS:
			return true
	return false


static func feet_of(shape: CollisionShape2D) -> Vector2:
	var rect: Rect2 = shape.global_transform * shape.shape.get_rect()
	return Vector2(rect.get_center().x, rect.end.y)


func _draw() -> void:
	var from := to_local(origin)
	var to := to_local(origin + Vector2.from_angle(angle) * length)
	if aiming:
		draw_line(from, to, Color(Layout.BEAM_EDGE, 0.7), AIM_LINE_WIDTH)
		return
	if length <= 0.0:
		return
	if not body_spec.is_empty():
		_draw_sheets(from)
		return
	var flicker := 1.0 + 0.08 * float(int(clock / FLICKER_TIME) % 2)
	draw_line(from, to, Color(Layout.BEAM_EDGE, 0.55), HALF_WIDTH * 2.0 * flicker)
	draw_line(from, to, Color(Layout.BEAM_CORE, 0.95), CORE_WIDTH * flicker)
	draw_circle(to, HALF_WIDTH * 1.1, Color(Layout.BEAM_EDGE, 0.6))
	draw_circle(to, CORE_WIDTH * 0.6, Color(Layout.BEAM_CORE, 0.9))


func _draw_sheets(from: Vector2) -> void:
	var scale := Layout.SCALE
	var tile: Vector2 = body_spec.frame
	var frame := int(clock / FRAME_TIME) % int(body_spec.count)
	var body: Texture2D = body_texture
	draw_set_transform(from, angle)
	var step := tile.x * scale
	var x := 0.0
	while x < length:
		var w := minf(step, length - x)
		draw_texture_rect_region(body, Rect2(Vector2(x, -(body_spec.pivot as Vector2).y * scale), Vector2(w, tile.y * scale)),
			Rect2(Vector2(frame * tile.x, 0.0), Vector2(w / scale, tile.y)))
		x += step
	if not end_spec.is_empty():
		var size: Vector2 = end_spec.frame
		draw_texture_rect_region(end_texture, Rect2(Vector2(length, 0.0) - (end_spec.pivot as Vector2) * scale, size * scale),
			Rect2(Vector2((frame % int(end_spec.count)) * size.x, 0.0), size))
	draw_set_transform(Vector2.ZERO, 0.0)
