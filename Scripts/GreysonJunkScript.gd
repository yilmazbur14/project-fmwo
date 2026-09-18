extends Node2D

# One of the pieces of gym junk Greyson throws over the chase. It flies straight at where the
# player's hurtbox was when he let go, spinning, with the parry aura on it.
# It reports its own hits rather than letting the player's hurtbox find it, because it needs the
# result: a parried or blocked piece cracks apart, one that lands puffs out. The dodge-ghost branch
# is mandatory, or it would silently eat perfect dodges.
# Modelled on JoshThrownCardScript: a parry negates it but never staggers Greyson, who is standing
# still to begin with.

const Layout := preload("res://Scripts/GreysonComputahArtLayout.gd")
const Arena := preload("res://Scripts/States/GreysonComputah/GcStateMachine.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")

# How far outside the ropes a piece flies before it is given up on.
const OUT_OF_PLAY_MARGIN := 200.0

@export var junk: Node2D
@export var hitbox: Area2D
@export var hitbox_shape: CollisionShape2D

# Set by the throw, before it enters the tree.
var attack_id := &"greyson_throw"
var speed := 850.0
var direction := Vector2.RIGHT
var player: Node2D

var spent := false
var spin := 0.0


func _ready() -> void:
	hitbox.set_meta(HitInfo.META_ATTACK, attack_id)
	(hitbox_shape.shape as RectangleShape2D).size = Layout.JUNK_HIT_SIZE
	_build()


func _physics_process(delta: float) -> void:
	if spent:
		return
	global_position += direction * speed * delta
	spin += delta
	junk.rotation = TAU * Layout.PLACEHOLDER_JUNK.spin * spin
	if not Arena.ROPES.grow(OUT_OF_PLAY_MARGIN).has_point(global_position):
		queue_free()
		return
	_resolve_hits()


func _resolve_hits() -> void:
	if not is_instance_valid(player):
		return
	var near_miss := false
	for area in hitbox.get_overlapping_areas():
		if area == player.hurtBox:
			_consume(player.receive_hit(_hit()))
			return
		if player.is_dodge_ghost(area):
			near_miss = true
	# Only where the player isn't: a piece passing the spot a dash left is a perfect dodge.
	if near_miss:
		player.receive_near_miss(_hit())


# No boss: a parry negates the throw and pays hype, but nothing about it staggers him.
func _hit() -> RefCounted:
	return HitInfo.make(attack_id, hitbox, global_position, null)


func _consume(result: int) -> void:
	spent = true
	hitbox_shape.set_deferred("disabled", true)
	var stopped := result == HitInfo.Result.PARRIED or result == HitInfo.Result.BLOCKED
	if result != HitInfo.Result.IGNORED:
		_burst(stopped)
	queue_free()


# Left on the layer it was flying in, so it plays out after the piece is gone. Its first frame is
# drawn the moment it is added, which is the frame the parry resolved on.
func _burst(stopped: bool) -> void:
	var parent := get_parent()
	if parent == null:
		return
	var spec := Layout.PLACEHOLDER_JUNK_BURST
	var burst := Polygon2D.new()
	burst.polygon = Layout.star(spec.points, spec.radius, spec.inner_ratio)
	burst.color = spec.stopped_color if stopped else spec.hit_color
	burst.scale = Vector2.ONE * spec.from_scale
	parent.add_child(burst)
	burst.global_position = global_position
	var play := burst.create_tween()
	play.tween_property(burst, "scale", Vector2.ONE * spec.to_scale, spec.time)
	play.parallel().tween_property(burst, "modulate:a", 0.0, spec.time)
	play.tween_callback(burst.queue_free)


func _build() -> void:
	var spec := Layout.PLACEHOLDER_JUNK
	var face := Polygon2D.new()
	face.polygon = Layout.centred_rect(spec.size)
	face.color = spec.color
	junk.add_child(face)
	var rim := Line2D.new()
	rim.points = face.polygon
	rim.closed = true
	rim.width = spec.edge_width
	rim.default_color = spec.edge_color
	junk.add_child(rim)
