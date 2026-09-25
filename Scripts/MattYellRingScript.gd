extends Node2D

# Matt's yell: one ring of sound blown out from his mouth, 60 to 270 px in 0.18 s, then gone. Only the
# band the ring is drawn on hurts, so a player it has already passed is safe - except for the first
# 0.05 s, when the whole disc does, so it can't open around someone standing on his mouth. Copied from
# EricQuakeRingScript's shape.
#
# No guard or parry stops it (AttackCatalog's matt_yell). A dash through it is DODGED and pays a perfect
# dodge; being further than the end radius plus the band from his mouth is the other answer. It answers
# once: the first hit or dodge is reported to whoever blew it (`answered`), and it stops hurting.

signal answered(result: int)

const HitInfo := preload("res://Scripts/HitInfo.gd")
const MattArtLayout := preload("res://Scripts/MattArtLayout.gd")

const YELL_ID := &"matt_yell"

# Set before it is added.
var player: Node2D
var start_radius := 60.0
var end_radius := 270.0
var band := 15.0
var expand_time := 0.18
var landing_time := 0.05

var radius := 60.0
var elapsed := 0.0
var spent := false
var fading := false
var rings: Array[Line2D] = []
var sheet: Sprite2D


func _ready() -> void:
	radius = start_radius
	_build()
	_draw_rings()


func _physics_process(delta: float) -> void:
	elapsed += delta
	radius = lerpf(start_radius, end_radius, clampf(elapsed / maxf(expand_time, 0.0001), 0.0, 1.0))
	_draw_rings()
	if not spent:
		_damage_player()
	if elapsed >= expand_time and not fading:
		spent = true
		_fade()


# The player's hurtbox against the band, then against the dodge ghost for a near miss.
func _damage_player() -> void:
	if not is_instance_valid(player):
		return
	if _touches(_rect_of(player.hurtBox.get_node("CollisionShape2D"))):
		var result: int = player.receive_hit(_hit())
		if result == HitInfo.Result.HIT or result == HitInfo.Result.DODGED:
			spent = true
			answered.emit(result)
		return
	if player.dodge_ghost_position() == Vector2.INF:
		return
	if _touches(_rect_of(player.dodge_ghost.get_node("CollisionShape2D"))):
		player.receive_near_miss(_hit())


func _touches(rect: Rect2) -> bool:
	var centre := global_position
	var nearest := centre.clamp(rect.position, rect.end).distance_to(centre)
	var farthest := 0.0
	for corner in [rect.position, Vector2(rect.end.x, rect.position.y), Vector2(rect.position.x, rect.end.y), rect.end]:
		farthest = maxf(farthest, centre.distance_to(corner))
	var inner := 0.0 if elapsed < landing_time else radius - band
	return nearest <= radius + band and farthest >= inner


func _hit() -> RefCounted:
	return HitInfo.make(YELL_ID, self, global_position)


func _rect_of(shape: CollisionShape2D) -> Rect2:
	var size: Vector2 = (shape.shape as RectangleShape2D).size * shape.global_scale.abs()
	return Rect2(shape.global_position - size / 2.0, size)


#WHAT IS DRAWN

func _build() -> void:
	if MattArtLayout.uses_final_fx(&"yell_rings"):
		var spec := MattArtLayout.fx(&"yell_rings")
		sheet = Sprite2D.new()
		sheet.texture = load(spec.texture)
		sheet.hframes = spec.hframes
		sheet.scale = Vector2.ONE * MattArtLayout.SCALE
		add_child(sheet)
		return
	var spec := MattArtLayout.fx(&"yell_rings")
	# Drawn back to front: the fainter ring behind, then the edge, the flanks and the core.
	for layer in [[spec.edge, spec.edge_width, spec.trail_alpha], [spec.edge, spec.edge_width, 1.0],
			[spec.flank, spec.flank_width, 1.0], [spec.core, spec.core_width, 1.0]]:
		var ring := Line2D.new()
		ring.closed = true
		ring.width = layer[1]
		ring.default_color = Color(layer[0], layer[2])
		add_child(ring)
		rings.append(ring)


# The drawn sheet steps to the frame whose front radius is nearest; the stand-in is the radius itself.
func _draw_rings() -> void:
	if sheet != null:
		var spec := MattArtLayout.fx(&"yell_rings")
		var radii: Array = spec.radii
		var best := 0
		for i in radii.size():
			if absf(radii[i] * MattArtLayout.SCALE - radius) < absf(radii[best] * MattArtLayout.SCALE - radius):
				best = i
		sheet.frame = spec.fade_frame if fading else best
		return
	var spec := MattArtLayout.fx(&"yell_rings")
	for i in rings.size():
		var r := maxf(radius - spec.trail_gap, 1.0) if i == 0 else radius
		rings[i].points = MattArtLayout.circle(r, spec.points)


func _fade() -> void:
	fading = true
	var spec := MattArtLayout.fx(&"yell_rings")
	var time: float = spec.get("fade", 0.06)
	var out := create_tween()
	out.tween_property(self, "modulate:a", 0.0, time)
	out.tween_callback(queue_free)
