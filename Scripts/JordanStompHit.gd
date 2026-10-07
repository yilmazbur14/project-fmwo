extends Node2D

# One landing of the kaiju's stomp (JordanStomp), DannyBossSlamHit's: its own hit source, so the guard and the dodge
# judge every landing afresh. Added on the stomp's mark, it tests the footprint, an ellipse `radii` round that point,
# once against the player's feet. Inside, the foot reaches them through receive_hit(); only the dodge ghost's feet
# inside, it came down on the spot a dash just left, and that is a near miss. The stomp reads what happened off it as
# soon as it is added: `result`, and `feet_inside`, which spares the player the quake ring it sends.

const HitInfo := preload("res://Scripts/HitInfo.gd")

const STOMP_ID := &"jordan_kaiju_stomp"
const RADII := Vector2(150, 105)
const FREE_AFTER := 0.2

# Set before it is added.
var player: CharacterBody2D
var boss: Node
var attack_id: StringName = STOMP_ID
var radii: Vector2 = RADII

var feet_inside := false
var ghost_inside := false
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
