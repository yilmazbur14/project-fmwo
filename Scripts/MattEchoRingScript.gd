extends Node2D

# Matt's Echo Roars (MattEchoRoars): one ring of sound off his roaring mouth, swept out over the whole ring at a
# steady speed from start_radius to end_radius, then gone in a short fade. Built with new() and set up before it is
# added. The band it is drawn on is what touches, except for its first birth_disc_time, when the whole disc does, so
# it can't open round a player standing on his mouth (E2, the yell ring's rule).
#
# IT ANSWERS ONCE (E4): the first touch on the player is the ring's one hit - a parry, a dash, a hit or nothing - and
# `touched` reports it; however long it then overlaps them it never hurts them again. A GHOST (phase two's pale X)
# never hits at all, but its first touch is still reported, since the bite window is timed off it. Every kind's hit
# origin is the player's own hurtbox centre, so any facing answers it (R1). No near misses are reported.

signal touched(ring: Node2D, result: int)

const HitInfo := preload("res://Scripts/HitInfo.gd")
const MattArtLayout := preload("res://Scripts/MattArtLayout.gd")

enum Kind { RED, ECHO, GHOST, PUNISH, BOOMBURST }

const IDS := {Kind.RED: &"matt_echo", Kind.ECHO: &"matt_echo", Kind.PUNISH: &"matt_echo_punish", Kind.BOOMBURST: &"matt_boomburst"}

# Set before it is added.
var kind := Kind.RED
var player: Node2D
var speed := 1800.0
var start_radius := 40.0
var end_radius := 1050.0
var band := 14.0
var birth_disc_time := 0.05
# How far past its exact birth the step that adds it is: its radius starts where an exact birth would have put it.
var overshoot := 0.0

var radius := 0.0
var elapsed := 0.0
# The player's defense clock at its exact birth, and at its first touch.
var born_at := 0.0
var touched_at := -1.0
var answered := false
var result := -1
var centre := Vector2.ZERO
var fading := false
var art: Node2D
var lines: Array[Line2D] = []
var beat_clock := 0.0


func _ready() -> void:
	centre = global_position
	elapsed = overshoot
	radius = minf(start_radius + speed * elapsed, end_radius)
	born_at = _clock() - overshoot
	_build()
	_draw_rings()
	_check()


func _physics_process(delta: float) -> void:
	if fading:
		return
	elapsed += delta
	beat_clock += delta
	radius = minf(start_radius + speed * elapsed, end_radius)
	_draw_rings()
	_check()
	if radius >= end_radius:
		_fade()


# Turns a ring still on its way into another kind: an echo becomes the punish a bitten X arms.
func set_kind(new_kind: Kind) -> void:
	if answered or new_kind == kind:
		return
	kind = new_kind
	if is_instance_valid(art):
		art.queue_free()
	_build()
	_draw_rings()


func is_live() -> bool:
	return not fading and not is_queued_for_deletion()


func _check() -> void:
	if answered or not is_instance_valid(player):
		return
	var rect := _rect_of(player.hurtBox.get_node("CollisionShape2D"))
	if not _touches(rect):
		return
	answered = true
	touched_at = _clock()
	if kind == Kind.GHOST:
		result = HitInfo.Result.IGNORED
	else:
		result = player.receive_hit(HitInfo.make(IDS[kind], self, rect.get_center()))
	touched.emit(self, result)


func _touches(rect: Rect2) -> bool:
	var nearest := centre.clamp(rect.position, rect.end).distance_to(centre)
	var farthest := 0.0
	for corner in [rect.position, Vector2(rect.end.x, rect.position.y), Vector2(rect.position.x, rect.end.y), rect.end]:
		farthest = maxf(farthest, centre.distance_to(corner))
	var inner := 0.0 if elapsed < birth_disc_time else radius - band
	return nearest <= radius + band and farthest >= inner


func _rect_of(shape: CollisionShape2D) -> Rect2:
	var size: Vector2 = (shape.shape as RectangleShape2D).size * shape.global_scale.abs()
	return Rect2(shape.global_position - size / 2.0, size)


func _clock() -> float:
	var defense = player.get("defense") if is_instance_valid(player) else null
	return defense.clock if defense else 0.0


#WHAT IS DRAWN (MattArtLayout.ECHO_RINGS, in code)

func _build() -> void:
	art = Node2D.new()
	add_child(art)
	lines.clear()
	var spec := MattArtLayout.ECHO_RINGS
	match kind:
		Kind.RED, Kind.ECHO:
			var look: Dictionary = spec.red
			for layer in [[look.edge, look.edge_width, look.trail_alpha], [look.edge, look.edge_width, 1.0],
					[look.flank, look.flank_width, 1.0], [look.core, look.core_width, 1.0], [look.rim, look.rim_width, 1.0]]:
				_add_line(Color(layer[0], layer[2]), layer[1], true)
			if kind == Kind.ECHO:
				art.modulate.a = spec.echo_alpha
		Kind.GHOST:
			var look: Dictionary = spec.ghost
			for i in look.arcs:
				_add_line(look.edge, look.edge_width, false)
				_add_line(look.core, look.core_width, false)
			art.modulate.a = look.alpha
		Kind.PUNISH:
			var look: Dictionary = spec.punish
			var glow := _add_line(look.glow, look.glow_width, true)
			var added := CanvasItemMaterial.new()
			added.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
			glow.material = added
			_add_line(look.color, look.width, true)
		Kind.BOOMBURST:
			var look: Dictionary = spec.boomburst
			_add_line(look.inner, look.inner_width, true)
			_add_line(look.body, 1.0, true)
			_add_line(look.edge, look.edge_width, true)


func _add_line(color: Color, width: float, closed: bool) -> Line2D:
	var line := Line2D.new()
	line.closed = closed
	line.width = width
	line.default_color = color
	art.add_child(line)
	lines.append(line)
	return line


func _draw_rings() -> void:
	var spec := MattArtLayout.ECHO_RINGS
	match kind:
		Kind.RED, Kind.ECHO:
			var look: Dictionary = spec.red
			lines[0].points = _circle(maxf(radius - look.trail_gap, 1.0))
			for i in range(1, 4):
				lines[i].points = _circle(radius)
			lines[4].points = _circle(radius + look.rim_gap)
		Kind.GHOST:
			var look: Dictionary = spec.ghost
			var step: float = TAU / look.arcs
			for i in look.arcs:
				var arc := _arc(radius, step * i, step * look.fill)
				lines[i * 2].points = arc
				lines[i * 2 + 1].points = arc
		Kind.PUNISH:
			var look: Dictionary = spec.punish
			var swing: float = 0.5 + 0.5 * sin(TAU * beat_clock / (look.beat_time * 2.0))
			var beat: float = lerpf(look.beat[0], look.beat[1], swing)
			lines[0].width = look.glow_width * beat
			lines[1].width = look.width * beat
			for line in lines:
				line.points = _circle(radius)
		Kind.BOOMBURST:
			var look: Dictionary = spec.boomburst
			var back: float = maxf(radius - look.depth, 1.0)
			lines[0].points = _circle(back)
			lines[1].width = maxf(radius - back, 1.0)
			lines[1].points = _circle((radius + back) / 2.0)
			lines[2].points = _circle(radius)


func _circle(r: float) -> PackedVector2Array:
	return MattArtLayout.circle(r, _points(r))


func _arc(r: float, from: float, span: float) -> PackedVector2Array:
	var count := maxi(roundi(_points(r) * span / TAU), 2)
	var out := PackedVector2Array()
	for i in count + 1:
		out.append(Vector2.from_angle(from + span * i / count) * r)
	return out


func _points(r: float) -> int:
	var spec := MattArtLayout.ECHO_RINGS
	return clampi(roundi(TAU * r / spec.chord), spec.min_points, spec.max_points)


func _fade() -> void:
	fading = true
	var out := create_tween()
	out.tween_property(self, "modulate:a", 0.0, MattArtLayout.ECHO_RINGS.fade)
	out.tween_callback(queue_free)
