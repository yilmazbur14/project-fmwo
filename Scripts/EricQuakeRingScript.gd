extends Node2D

# The earthquake ring from Eric's planted sword: identical segments tiled around an expanding
# circle. Only the band the segment art covers hurts, so a player the ring has already passed is
# safe; dashing through it is the dodge.

const HitInfo := preload("res://Scripts/HitInfo.gd")
const SEGMENT_SCENE := preload("res://Scenes/Bosses/EricQuakeSegmentScene.tscn")

# Smaller rings look octagonal.
const START_RADIUS := 120.0
# 32-texel segments overlapping their neighbours by 4 texels, at 3x.
const SEGMENT_SPACING := 84.0
const FRAME_COUNT := 4
const FRAME_TIME := 0.08
# Texture rows 5-26 are the dangerous crest, 11 texels either side of the segment's centre.
const HURT_HALF_WIDTH := 33.0
# For this long after landing the whole disc inside the ring hurts too, so the sword can't land
# on a player without hitting them.
const LANDING_HIT_TIME := 0.1
# A segment is drawn only while its whole sprite stays inside the rope art, but the ring hurts
# everywhere up to the ropes, so hugging a rope isn't safe.
const VISIBLE_AREA := Rect2(160, 160, 1600, 757)
const HURT_AREA := Rect2(105, 105, 1710, 870)

# Radius growth in px/s and the player to hurt, set by the throw before the ring is added.
var speed := 950.0
var player: CharacterBody2D

var radius := START_RADIUS
var elapsed := 0.0
var segments : Array[Sprite2D] = []


func _ready() -> void:
	_place_segments()


func _physics_process(delta: float) -> void:
	elapsed += delta
	radius += speed * delta
	_place_segments()
	_damage_player()
	if _has_passed_hurt_area():
		queue_free()


func _place_segments() -> void:
	var count := ceili(TAU * radius / SEGMENT_SPACING)
	while segments.size() < count:
		var segment: Sprite2D = SEGMENT_SCENE.instantiate()
		segments.append(segment)
		add_child(segment)
	# The segments tile seamlessly, so they all show the same frame.
	var frame := int(elapsed / FRAME_TIME) % FRAME_COUNT
	for i in count:
		var angle := TAU * i / count
		var segment := segments[i]
		segment.position = Vector2.from_angle(angle) * radius
		# The top of the art faces outward.
		segment.rotation = angle + PI / 2.0
		segment.frame = frame
		segment.visible = VISIBLE_AREA.has_point(segment.global_position)


# Deals its own damage rather than joining "enemy projectile", which also hits dashing players.
func _damage_player() -> void:
	if not is_instance_valid(player):
		return
	var hurtbox_shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	var half_size: Vector2 = hurtbox_shape.shape.size * hurtbox_shape.global_scale.abs() / 2.0
	var rect := Rect2(hurtbox_shape.global_position - half_size, half_size * 2.0)
	var centre := global_position
	var nearest := centre.clamp(rect.position, rect.end).distance_to(centre)
	var farthest := 0.0
	for corner in [rect.position, Vector2(rect.end.x, rect.position.y), Vector2(rect.position.x, rect.end.y), rect.end]:
		farthest = maxf(farthest, centre.distance_to(corner))
	var inner := 0.0 if elapsed < LANDING_HIT_TIME else radius - HURT_HALF_WIDTH
	if nearest > radius + HURT_HALF_WIDTH or farthest < inner:
		return
	player.receive_hit(HitInfo.make(&"eric_quake_ring", self, centre))


func _has_passed_hurt_area() -> bool:
	for corner in [HURT_AREA.position, Vector2(HURT_AREA.end.x, HURT_AREA.position.y), Vector2(HURT_AREA.position.x, HURT_AREA.end.y), HURT_AREA.end]:
		if global_position.distance_to(corner) > radius - HURT_HALF_WIDTH:
			return false
	return true
