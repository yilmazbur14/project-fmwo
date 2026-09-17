extends Node2D

# One of the three cards Josh throws once he is back on the floor. It flies straight at where the
# player's hurtbox was when he let go, spinning, with the parry aura on it.
# It reports its own hits rather than letting the player's hurtbox find it, because it needs the
# result: a parried or blocked card shatters, a card that lands puffs out. The dodge-ghost branch is
# mandatory, or the card would silently eat perfect dodges.

const JoshArtLayout := preload("res://Scripts/JoshArtLayout.gd")
const Arena := preload("res://Scripts/States/JoshCards/JoshCardsStateMachine.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")

# How far outside the ropes a card flies before it is given up on.
const OUT_OF_PLAY_MARGIN := 200.0

@export var card: Node2D
@export var hitbox: Area2D
@export var hitbox_shape: CollisionShape2D

# Set by the throw, before it enters the tree.
var speed := 900.0
var direction := Vector2.RIGHT
var hit_size := Vector2(90, 90)
var player: Node2D

var spent := false
var spin := 0.0
var card_sprite: Sprite2D


func _ready() -> void:
	hitbox.set_meta(HitInfo.META_ATTACK, &"josh_card_throw")
	(hitbox_shape.shape as RectangleShape2D).size = hit_size
	_build()


func _physics_process(delta: float) -> void:
	if spent:
		return
	global_position += direction * speed * delta
	spin += delta
	if card_sprite:
		var spec := JoshArtLayout.FINAL_THROWN_CARD
		card_sprite.frame = int(spin / spec.frame_time) % spec.hframes
	else:
		card.rotation = TAU * JoshArtLayout.PLACEHOLDER_THROWN_CARD.spin * spin
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
	# Only where the player isn't: a card passing the spot a dash left is a perfect dodge.
	if near_miss:
		player.receive_near_miss(_hit())


# No boss: a parry negates the card and pays hype, but nothing about it staggers him.
func _hit() -> RefCounted:
	return HitInfo.make(&"josh_card_throw", hitbox, global_position, null)


func _consume(result: int) -> void:
	spent = true
	hitbox_shape.set_deferred("disabled", true)
	var stopped := result == HitInfo.Result.PARRIED or result == HitInfo.Result.BLOCKED
	if result != HitInfo.Result.IGNORED:
		_burst(stopped)
	queue_free()


# Left on the layer the card was flying in, so it plays out after the card is gone. Its first frame
# is drawn the moment it is added, which is the frame the parry resolved on.
func _burst(stopped: bool) -> void:
	var parent := get_parent()
	if parent == null:
		return
	if JoshArtLayout.USE_FINAL_CARD_SHATTER:
		var crack_spec := JoshArtLayout.FINAL_CARD_SHATTER
		var crack := Sprite2D.new()
		crack.texture = load(crack_spec.texture)
		crack.hframes = crack_spec.hframes
		crack.scale = Vector2.ONE * crack_spec.scale
		if not stopped:
			crack.modulate = crack_spec.hit_tint
		parent.add_child(crack)
		crack.global_position = global_position
		var crack_times: Array = crack_spec.frame_times
		var play_crack := crack.create_tween()
		for i in range(1, crack_spec.hframes):
			play_crack.tween_interval(crack_times[i - 1])
			play_crack.tween_callback(func() -> void: crack.frame = i)
		play_crack.tween_interval(crack_times[crack_times.size() - 1])
		play_crack.tween_callback(crack.queue_free)
		return

	var spec := JoshArtLayout.PLACEHOLDER_CARD_SHATTER
	var burst := Polygon2D.new()
	burst.polygon = JoshArtLayout.star(spec.points, spec.radius, spec.inner_ratio)
	burst.color = spec.shatter_color if stopped else spec.puff_color
	burst.scale = Vector2.ONE * spec.from_scale
	parent.add_child(burst)
	burst.global_position = global_position
	var play := burst.create_tween()
	play.tween_property(burst, "scale", Vector2.ONE * spec.to_scale, spec.time)
	play.parallel().tween_property(burst, "modulate:a", 0.0, spec.time)
	play.tween_callback(burst.queue_free)


func _build() -> void:
	if JoshArtLayout.USE_FINAL_THROWN_CARD:
		var final_spec := JoshArtLayout.FINAL_THROWN_CARD
		card_sprite = Sprite2D.new()
		card_sprite.texture = load(final_spec.texture)
		card_sprite.hframes = final_spec.hframes
		card_sprite.scale = Vector2.ONE * final_spec.scale
		# The pivot is the card body's centre, which is what the hitbox sits on; the trail follows.
		card_sprite.offset = final_spec.frame_size / 2.0 - final_spec.pivot
		card_sprite.flip_h = direction.x < 0.0
		card.add_child(card_sprite)
		return

	var spec := JoshArtLayout.PLACEHOLDER_THROWN_CARD
	var face := Polygon2D.new()
	face.polygon = JoshArtLayout.centred_rect(spec.size)
	face.color = spec.color
	card.add_child(face)
	var rim := Line2D.new()
	rim.points = face.polygon
	rim.closed = true
	rim.width = spec.edge_width
	rim.default_color = spec.edge_color
	card.add_child(rim)
