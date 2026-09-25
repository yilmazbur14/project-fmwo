extends Node2D

# A puddle of worms on the floor where one of Danny's globs came down (plan section 3). It splats in, then lies
# there armed: a player whose feet come into it on a step they aren't dashing is rooted - the worms take
# their feet (DannyBossRoot) - and the puddle is used up. Feet already in it as it arms are spared until they
# step out, so it never springs on a player it landed on.
# THE TRIGGER IS A POINT TEST: the player's feet, the bottom middle of their hurtbox, inside an ellipse round
# its pivot, which is the stain's body without the drops round it. The Spit keeps them apart and off the ropes,
# so they never wall a player in. A dash carries the feet across it up or down, though not end to end, which
# is wider than a dash; a dash that ends in it roots on the step it ends.
# It goes with the next Spit (dry), a slam coming down on it (splat), a root, a Break or the end of the fight.

const ROOT_SCRIPT := preload("res://Scripts/DannyBossRoot.gd")
const Layout := preload("res://Scripts/DannyBossArtLayout.gd")

# A slam coming down on it takes it this fast.
const SPLAT_FADE := 0.1

# Set before it enters the tree.
var player: Node2D
var body: Node2D
# can_root() and on_player_rooted(root), and the root goes into the fight through its add_hazard().
var state_machine: Node

var armed := false
var spared := false
# Out of play for good: dried, splatted or used.
var gone := false
var clock := 0.0
var splat_spec: Dictionary = Layout.fx(&"splat")
var puddle_spec: Dictionary = Layout.fx(&"puddle")
# The trigger's radii in px: the stain's body without the drops round it.
var radii: Vector2 = puddle_spec.trigger * Layout.SCALE
var sheet: Sprite2D


func _ready() -> void:
	sheet = Sprite2D.new()
	sheet.texture = load(splat_spec.texture)
	sheet.hframes = splat_spec.hframes
	sheet.offset = splat_spec.offset
	sheet.scale = Vector2.ONE * Layout.SCALE
	add_child(sheet)


func _physics_process(delta: float) -> void:
	if gone:
		return
	clock += delta
	if not armed:
		var splat_time: float = splat_spec.frame_time
		var step := int(clock / splat_time)
		if step < sheet.hframes:
			sheet.frame = step
			return
		_arm()
		return
	var puddle_time: float = puddle_spec.frame_time
	sheet.frame = int(clock / puddle_time) % sheet.hframes
	_test_feet()


func contains_feet(point: Vector2) -> bool:
	var d := point - global_position
	return (d.x * d.x) / (radii.x * radii.x) + (d.y * d.y) / (radii.y * radii.y) <= 1.0


# A slam came down on it.
func splat() -> void:
	_fade(SPLAT_FADE)


# The next Spit's gulp: out of play at once, and gone over `seconds`.
func dry(seconds: float) -> void:
	_fade(seconds)


func _arm() -> void:
	armed = true
	clock = 0.0
	sheet.frame = 0
	sheet.texture = load(puddle_spec.texture)
	sheet.hframes = puddle_spec.hframes
	sheet.offset = puddle_spec.offset
	spared = is_instance_valid(player) and contains_feet(_feet())


func _test_feet() -> void:
	if not is_instance_valid(player):
		return
	var inside := contains_feet(_feet())
	if spared:
		spared = inside
		return
	if inside and not player.is_dodging and state_machine.can_root():
		_root()


func _root() -> void:
	gone = true
	armed = false
	var root: Node2D = ROOT_SCRIPT.new()
	root.player = player
	root.body = body
	state_machine.add_hazard(root, ROOT_SCRIPT.pivot_of(player), body.projectile_layer)
	state_machine.on_player_rooted(root)
	queue_free()


func _fade(seconds: float) -> void:
	if gone:
		return
	gone = true
	armed = false
	spared = false
	var fade := create_tween()
	fade.tween_property(self, "modulate:a", 0.0, seconds)
	fade.tween_callback(queue_free)


# The bottom middle of the player's hurtbox.
func _feet() -> Vector2:
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	return Vector2(box.get_center().x, box.end.y)
