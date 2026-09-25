extends Node2D

# One of Matt's Trueshot waves: a golden crescent, convex side forward, fired from the middle of one
# side of the ring along a latched heading. It never bounces and nothing stops it - a hit, a block, a
# parry and a dash all leave it flying - so it goes on through the player and off the screen, and is
# freed once it is well past the view.
#
# It resolves its own hits the way MattMysticBoltScript does, with the same latch, except that a hit
# latches it rather than consuming it: the user's wave passes through the player whatever they do.
# Its hitbox is the drawn crescent inset 2 texels, traced on the 0 degree drawing and turned to the
# heading. Only the hitbox turns; the drawn frames never do.
#
# THE BURST: for its first burst_time the shot also hits the burst zone the barrage hands it - him, the
# space round him and back to the rope behind him, which its path never crosses. The zone stays where it
# was fired while the wave flies on, and is part of this shot: the same latch, and the wave's hitbox as
# the source, so one parry or dash answers both and neither lands twice.

const HitInfo := preload("res://Scripts/HitInfo.gd")
const MattArtLayout := preload("res://Scripts/MattArtLayout.gd")

const WAVE_ID := &"matt_trueshot"
const VIEW := Rect2(0, 0, 1920, 1080)
const FLICKER_TIME := 0.2
const FLICKER_HZ := 30.0
const FLICKER_ALPHA := 0.35

@export var art: Node2D
@export var hitbox: Area2D
@export var hit_shape: CollisionPolygon2D

# Set before it enters the tree.
var heading := Vector2.RIGHT
var speed := 1500.0
var view_margin := 160.0
var player: Node2D
# In world px; empty for no burst.
var burst_zone := PackedVector2Array()
var burst_time := 0.0

var latched := false
var flicker_left := 0.0
var fx_clock := 0.0
var burst: Area2D
var burst_left := 0.0
var sheet: Sprite2D
var sheet_spec: Dictionary
var sheet_first := 0
# Everything the player's hurtbox said about it, for a test: each resolved result in order.
var results: Array[int] = []


func _ready() -> void:
	hitbox.rotation = heading.angle()
	hit_shape.polygon = MattArtLayout.scaled_poly(MattArtLayout.trueshot_hit_poly(), MattArtLayout.SCALE, 0.0)
	if not burst_zone.is_empty():
		_build_burst()
	_build()


func _physics_process(delta: float) -> void:
	fx_clock += delta
	global_position += heading * speed * delta
	if not VIEW.grow(view_margin).intersects(_bounds()):
		queue_free()
		return
	_step_art(delta)
	_resolve_hits()
	if burst != null:
		burst_left -= delta
		if burst_left <= 0.0:
			burst.queue_free()
			burst = null


# Top level, so it stays put while the wave moves; on the hitbox's own layers.
func _build_burst() -> void:
	burst = Area2D.new()
	burst.name = "Burst"
	burst.top_level = true
	burst.collision_layer = hitbox.collision_layer
	burst.collision_mask = hitbox.collision_mask
	burst.monitorable = false
	var shape := CollisionPolygon2D.new()
	shape.polygon = burst_zone
	burst.add_child(shape)
	add_child(burst)
	burst_left = burst_time


func _resolve_hits() -> void:
	if not is_instance_valid(player):
		return
	var touching := false
	var near := false
	var areas := hitbox.get_overlapping_areas()
	if burst != null:
		areas.append_array(burst.get_overlapping_areas())
	for area in areas:
		if area == player.hurtBox:
			touching = true
		elif player.is_dodge_ghost(area):
			near = true
	if touching:
		if latched:
			return
		var result: int = player.receive_hit(_hit())
		if result != HitInfo.Result.IGNORED:
			results.append(result)
			latched = true
			if result != HitInfo.Result.HIT:
				flicker_left = FLICKER_TIME
		return
	latched = false
	if near:
		player.receive_near_miss(_hit())


# The player's own hurtbox centre, like the bolts: whichever side it comes in from, any facing answers.
func _hit() -> RefCounted:
	var centre: Vector2 = player.hurtBox.get_node("CollisionShape2D").global_position
	return HitInfo.make(WAVE_ID, hitbox, centre, null)


# The hit polygon's box in the world, which is what leaves the view.
func _bounds() -> Rect2:
	var points := MattArtLayout.scaled_poly(MattArtLayout.trueshot_hit_poly(), MattArtLayout.SCALE, heading.angle())
	var box := Rect2(points[0], Vector2.ZERO)
	for point in points:
		box = box.expand(point)
	box.position += global_position
	return box


#WHAT IS DRAWN

# The drawn sheet hangs straight off the wave, beside its hitbox, where PlayerCombatFx looks for a
# parried projectile's art to flash.
func _build() -> void:
	if MattArtLayout.uses_final_fx(&"wave"):
		var pick: Array = MattArtLayout.wave_art(&"wave", heading)
		sheet_spec = pick[0]
		sheet_first = pick[1] * sheet_spec.frames_per_heading
		sheet = Sprite2D.new()
		sheet.texture = load(sheet_spec.texture)
		sheet.hframes = sheet_spec.hframes
		sheet.frame = sheet_first
		sheet.scale = Vector2.ONE * MattArtLayout.SCALE
		sheet.flip_h = pick[2]
		sheet.flip_v = pick[3]
		add_child(sheet)
		return
	var spec := MattArtLayout.fx(&"wave")
	var outline := MattArtLayout.scaled_poly(MattArtLayout.PLACEHOLDER_WAVE_POLY, MattArtLayout.SCALE, 0.0)
	var fill := Polygon2D.new()
	fill.polygon = outline
	fill.color = spec.fill
	art.add_child(fill)
	var inner := Line2D.new()
	var back := PackedVector2Array()
	for i in range(outline.size() / 2 + 1, outline.size()):
		back.append(outline[i])
	inner.points = back
	inner.width = spec.edge_width
	inner.default_color = spec.inner
	art.add_child(inner)
	var edge := Line2D.new()
	var front := PackedVector2Array()
	for i in outline.size() / 2 + 1:
		front.append(outline[i])
	edge.points = front
	edge.width = spec.edge_width
	edge.default_color = spec.edge
	art.add_child(edge)
	art.rotation = heading.angle()


func _step_art(delta: float) -> void:
	if sheet != null:
		sheet.frame = sheet_first + int(fx_clock / sheet_spec.frame_time) % int(sheet_spec.frames_per_heading)
	if flicker_left > 0.0:
		flicker_left -= delta
		var dim := int(flicker_left * FLICKER_HZ * 2.0) % 2 == 1
		modulate.a = FLICKER_ALPHA if dim and flicker_left > 0.0 else 1.0
