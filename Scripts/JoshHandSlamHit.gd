extends Node2D

# One landing of Josh's Hand Slam (JoshCardsHandSlam), DannyBossSlamHit's shape: its own hit source, so the parry and
# the dodge judge every landing afresh (PlayerDefense keeps its records per source). Put down on the landing's spot,
# it tests the footprint (JoshHandsLayout.FOOTPRINT) round that spot once against the player's feet, the foot of their
# hurtbox. Inside, the slam reaches them through receive_hit(); only the dodge ghost's feet inside, it came down on
# the spot a dash just left, and that is a near miss. It stays in the hazard group for FREE_AFTER, so whatever the hit
# set off still finds its source, then frees itself. The attack reads what happened off it as soon as it is added.
# It resolves in _ready(), so its player, its boss and its position are all set before it is added.

const HitInfo := preload("res://Scripts/HitInfo.gd")
const Layout := preload("res://Scripts/JoshHandsLayout.gd")

const SLAM_ID := &"josh_hand_slam"
const FREE_AFTER := 0.2

var player: CharacterBody2D
var boss: Node

var feet_inside := false
var ghost_inside := false
# The feet it tested, for a test.
var feet := Vector2.INF
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
	return Layout.footprint_covers(global_position, point)


func _resolve() -> void:
	if not is_instance_valid(player):
		return
	feet = _feet_of(player.hurtBox.get_node("CollisionShape2D"))
	feet_inside = covers(feet)
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
	return HitInfo.make(SLAM_ID, self, centre, boss)


static func _feet_of(shape: CollisionShape2D) -> Vector2:
	var rect: Rect2 = shape.global_transform * shape.shape.get_rect()
	return Vector2(rect.get_center().x, rect.end.y)
