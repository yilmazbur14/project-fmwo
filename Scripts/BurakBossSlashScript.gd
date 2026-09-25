extends Node2D

# One swing of Captain Burak's cutlass string, the instant it lands: a bare node on his feet that asks
# the player's defence once, on the strike step, and is gone LIFE later.
#
# NO SPRITE, on purpose. His body draws the blade and the trail sheet draws the arc. PlayerCombatFx
# flashes and shatters the first visible sprite on a parried hit's source or beside it, and a shatter
# says a projectile broke, which a sword swing never does. For the same reason, whoever places it gives
# it a parent with no sprite in it (CarterBeamRush's source holder).
# Every swing is its own node, so its own hit source: PlayerDefense absorbs a source for a second after a
# parry, and a string sharing one would give away the swings after it.
# The hit's origin is the player's own hurtbox centre, so any facing answers it: a parry is timing, not
# aim. A held guard is no answer (burak_cutlass is parryable, not blockable), and a dash through it is
# the dodge.

# PARRIED, HIT or DODGED, once. A strike that reached nobody, or that the defence ignored, says nothing.
signal answered(result: int)

const HitInfo := preload("res://Scripts/HitInfo.gd")
const BurakBossBall := preload("res://Scripts/BurakBossBallScript.gd")

const CUTLASS_ID := &"burak_cutlass"
const LIFE := 0.2
# px from his feet, facing right: what the player's hurtbox covers wherever his tracking can leave them at
# a strike, 100 px off him give or take a physics frame. A box that overlaps it hits every one of them, so
# a walker is hit by all three swings (the no-walk-out rule).
const REACH := Rect2(96, -67, 8, 53)

# Set before strike().
var player: Node2D
var body: Node2D
# One of BurakBossArtLayout.SLASH_BOXES: px from his feet, drawn facing right.
var box := Rect2()
# He faces left: the box mirrors about his feet, as his sprite does.
var flip := false

var struck := false
var result: int = HitInfo.Result.IGNORED
var contact := Vector2.INF
var life := 0.0


func _physics_process(delta: float) -> void:
	life += delta
	if life >= LIFE:
		queue_free()


# Called on the strike step once it stands on his feet. The second call only gets the first answer.
func strike() -> int:
	if struck:
		return result
	struck = true
	if not is_instance_valid(player):
		return result
	var reach := world_box()
	var hurt := _rect_of(player.hurtBox.get_node("CollisionShape2D"))
	if reach.intersects(hurt):
		contact = reach.intersection(hurt).get_center()
		result = player.receive_hit(_hit())
		# Its parent all the same: PlayerCombatFx has already looked for art, and the clash is gone long
		# before the next swing's strike.
		if result == HitInfo.Result.PARRIED:
			BurakBossBall.clash_at(get_parent(), contact)
		if result != HitInfo.Result.IGNORED:
			answered.emit(result)
	elif player.dodge_ghost_position() != Vector2.INF and reach.intersects(_rect_of(player.dodge_ghost.get_node("CollisionShape2D"))):
		player.receive_near_miss(_hit())
	return result


func world_box() -> Rect2:
	var facing := Rect2(-box.end.x, box.position.y, box.size.x, box.size.y) if flip else box
	return Rect2(global_position + facing.position, facing.size)


static func reaches(slash_box: Rect2) -> bool:
	return slash_box.intersects(REACH)


func _hit() -> RefCounted:
	var centre: Vector2 = player.hurtBox.get_node("CollisionShape2D").global_position
	return HitInfo.make(CUTLASS_ID, self, centre, body)


func _rect_of(shape: CollisionShape2D) -> Rect2:
	var size: Vector2 = (shape.shape as RectangleShape2D).size * shape.global_scale.abs()
	return Rect2(shape.global_position - size / 2.0, size)
