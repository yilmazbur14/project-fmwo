extends Node2D

# The line of blue fire the kaiju's breath leaves burning across the mat where its sweep stopped (JordanBreath), for
# `life` seconds: it splits the ring. On the fight's floor layer. It hurts the feet that touch it; a dash carries the
# player across safely, but lying still it never pays a perfect dodge (AttackCatalog's jordan_burn_line). It starts
# where the ray leaves the kaiju's walls, MOUTH_CLEAR out at the least, and runs to the ropes. A parried stomp puts every one out (put_out). Its flames
# are its sheets once they are in (JordanKaijuLayout.fx), upright and never turned, each a frame on from its neighbour,
# dying through the ember's frames as it goes out; drawn in code until then.

const Layout := preload("res://Scripts/JordanKaijuLayout.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const Beam := preload("res://Scripts/JordanKaijuBeam.gd")

const BURN_ID := &"jordan_burn_line"
const HALF_WIDTH := 26.0
const FLAME_STEP := 36.0
const FLAME_SIZE := Vector2(16, 24)
const FLICKER_TIME := 0.08
const OUT_TIME := 0.3
const WALL_STEP := 6.0
# It starts no nearer its mouth than this: the floor in front of the lowered head, where the player stands to punch him
# in the opening after the breath (JordanRecoil), is never on fire.
const MOUTH_CLEAR := 150.0

# Set before it is added.
var player: CharacterBody2D
var boss: Node
var origin := Vector2.ZERO
var angle := 0.0
var life := 4.0

var from := Vector2.ZERO
var to := Vector2.ZERO
var clock := 0.0
var going_out := false
var out_clock := 0.0
# For a test: every result it got out of the player.
var results: Array[int] = []
var flame_spec: Dictionary = Layout.fx(&"burn_flame")
var out_spec: Dictionary = Layout.fx(&"burn_out")
# Loaded before anything draws: a sheet first loaded inside a draw call is drawn as a white box.
var flame_texture: Texture2D = Layout.texture(flame_spec.sheet) if not flame_spec.is_empty() else null
var out_texture: Texture2D = Layout.texture(out_spec.sheet) if not out_spec.is_empty() else null


func _ready() -> void:
	var reach := Layout.reach_to_ropes(origin, angle)
	var direction := Vector2.from_angle(angle)
	var start := minf(MOUTH_CLEAR, reach)
	while start < reach and Layout.in_walls(origin + direction * start):
		start += WALL_STEP
	from = origin + direction * start
	to = origin + direction * reach
	queue_redraw()


func put_out() -> void:
	if going_out:
		return
	going_out = true
	out_clock = 0.0
	queue_redraw()


# Its ember's frames once those are in, faded out in code until then.
func _out_time() -> float:
	if out_spec.is_empty():
		return OUT_TIME
	var total := 0.0
	for time in out_spec.times:
		total += time
	return total


func is_burning() -> bool:
	return not going_out


func distance_to_point(point: Vector2) -> float:
	return point.distance_to(Geometry2D.get_closest_point_to_segment(point, from, to))


func covers(point: Vector2) -> bool:
	return is_burning() and distance_to_point(point) <= HALF_WIDTH


func _physics_process(delta: float) -> void:
	clock += delta
	if not going_out and clock >= life:
		put_out()
	if going_out:
		out_clock += delta
		if out_spec.is_empty():
			modulate.a = clampf(1.0 - out_clock / OUT_TIME, 0.0, 1.0)
		if out_clock >= _out_time():
			queue_free()
		queue_redraw()
		return
	if is_instance_valid(player):
		var feet := Beam.feet_of(player.hurtBox.get_node("CollisionShape2D"))
		if distance_to_point(feet) <= HALF_WIDTH + Beam.FOOT_RADIUS:
			var at := Geometry2D.get_closest_point_to_segment(feet, from, to)
			var result: int = player.receive_hit(HitInfo.make(BURN_ID, self, at, boss))
			if result != HitInfo.Result.IGNORED:
				results.append(result)
	if int(clock / FLICKER_TIME) != int((clock - delta) / FLICKER_TIME):
		queue_redraw()


# Upright flames every FLAME_STEP px along it, never turned with it, each a step of the flicker off its neighbour.
func _draw() -> void:
	var length := from.distance_to(to)
	var direction := (to - from).normalized()
	if not flame_spec.is_empty():
		_draw_sheets(length, direction)
		return
	var step := int(clock / FLICKER_TIME)
	draw_line(to_local(from), to_local(to), Color(Layout.BURN, 0.35), HALF_WIDTH * 1.4)
	var i := 0
	var along := FLAME_STEP / 2.0
	while along < length:
		var foot := to_local(from + direction * along)
		var tall := FLAME_SIZE.y * (0.8 + 0.25 * float((step + i) % 3))
		var half := FLAME_SIZE.x / 2.0
		draw_colored_polygon(PackedVector2Array([foot + Vector2(-half, 0), foot + Vector2(0, -tall), foot + Vector2(half, 0)]), Color(Layout.BURN, 0.9))
		draw_colored_polygon(PackedVector2Array([foot + Vector2(-half * 0.45, 0), foot + Vector2(0, -tall * 0.55), foot + Vector2(half * 0.45, 0)]), Color(Layout.BEAM_CORE, 0.95))
		along += FLAME_STEP
		i += 1


func _draw_sheets(length: float, direction: Vector2) -> void:
	var spec: Dictionary = out_spec if going_out and not out_spec.is_empty() else flame_spec
	var sheet: Texture2D = out_texture if spec == out_spec else flame_texture
	var size: Vector2 = spec.frame
	var pivot: Vector2 = spec.pivot
	var count: int = spec.count
	var step := int(clock / FLICKER_TIME)
	var out_frame := mini(int(out_clock / maxf(spec.times[0], 0.001)), count - 1)
	var i := 0
	var along := FLAME_STEP / 2.0
	while along < length:
		var foot := to_local(from + direction * along).round()
		var frame: int = out_frame if going_out else (step + i) % count
		draw_texture_rect_region(sheet, Rect2(foot - pivot * Layout.SCALE, size * Layout.SCALE), Rect2(Vector2(frame * size.x, 0.0), size))
		along += FLAME_STEP
		i += 1
