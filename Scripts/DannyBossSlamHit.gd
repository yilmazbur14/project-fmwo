extends Node2D

# One landing of Danny's Sumo Smash (DannyBossSlams): its own hit source, so the guard and the dodge judge
# every landing afresh (PlayerDefense keeps its records per source). Added on the landing's contact point, it
# tests his seated footprint, an ellipse `radii` round that point, once against the player's feet, the foot of
# their hurtbox, and hits them with `attack_id`: a hop or the big fifth (Addendum 1). Inside, the slam reaches
# them through receive_hit(); only the dodge ghost's feet inside, it came down on the spot a dash just left, and
# that is a near miss. It stays in the hazard group for FREE_AFTER, so whatever the hit set off still finds its
# source, then frees itself.
# The attack reads what happened off it as soon as it is added: `result`, and `feet_inside`, which spares the
# player from this landing's quake ring.

const HitInfo := preload("res://Scripts/HitInfo.gd")

const SLAM_ID := &"danny_butt_slam"
const RADII := Vector2(198, 33)
const FREE_AFTER := 0.2

# Set before it is added.
var player: CharacterBody2D
var boss: Node
var attack_id: StringName = SLAM_ID
var radii: Vector2 = RADII

var feet_inside := false
var ghost_inside := false
# What receive_hit() came to; IGNORED when the feet were outside too.
var result: int = HitInfo.Result.IGNORED
var age := 0.0


func _ready() -> void:
	_resolve()


func _physics_process(delta: float) -> void:
	age += delta
	if age >= FREE_AFTER:
		queue_free()


func covers(point: Vector2) -> bool:
	return ((point - global_position) / radii).length_squared() <= 1.0


func _resolve() -> void:
	if not is_instance_valid(player):
		return
	feet_inside = covers(_feet_of(player.hurtBox.get_node("CollisionShape2D")))
	if feet_inside:
		result = player.receive_hit(_hit())
		return
	if player.dodge_ghost_position() == Vector2.INF:
		return
	ghost_inside = covers(_feet_of(player.dodge_ghost.get_node("CollisionShape2D")))
	if ghost_inside:
		player.receive_near_miss(_hit())


# From the player's own hurtbox centre, so any facing answers it: it comes from above.
func _hit() -> RefCounted:
	var centre: Vector2 = player.hurtBox.get_node("CollisionShape2D").global_position
	return HitInfo.make(attack_id, self, centre, boss)


static func _feet_of(shape: CollisionShape2D) -> Vector2:
	var rect: Rect2 = shape.global_transform * shape.shape.get_rect()
	return Vector2(rect.get_center().x, rect.end.y)
