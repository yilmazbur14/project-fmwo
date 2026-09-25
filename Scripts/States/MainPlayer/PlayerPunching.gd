extends State

@export var punching_animation : String = "punch"
# @export var speed_threshold : float = 0.1
@export var animation_player : AnimationPlayer
@export var hitBox : Area2D
@export var player : CharacterBody2D

# feel_v2: the arm has reached full extension this swing, so the punch lands on whatever it reaches.
var extended := false
# A boss outside his windows that the fist is on this swing, and the physics frame it first was
# (_refuse_if_closed).
var closed_target: Node = null
var closed_since := -1

func Enter() -> void:
	# This fight's box for the locked facing, before the hitbox goes live (PlayerScript.feel_v2).
	player.fit_punch_hitbox()
	hitBox.monitoring = true
	hitBox.monitorable = true
	extended = false
	closed_target = null
	player.combo.start_swing()
	animation_player.speed_scale = 2.0  # Speed up only the punch animation
	animation_player.play(punching_animation)
	# The swoosh, star and whoosh; PunchFx does nothing without feel_v2.
	if player.punch_fx:
		player.punch_fx.swing()

func Exit() -> void:
	hitBox.monitoring = false  # Disable hitbox when exiting punch state
	hitBox.monitorable = false
	# A swing that ends on a closed boss before its refusal came due, or that he slid out from under.
	if closed_target != null:
		player.combo.refuse_punch(closed_target)
	player.combo.end_swing()
	animation_player.speed_scale = 1.0  # Reset back to normal for other animations

func Update(delta: float) -> void:
	if !animation_player.is_playing():
		get_parent().on_child_transition(self, "Idle")
		return

func Physics_Update(delta: float) -> void:
	# Zero out velocity during punch
	player.velocity = Vector2.ZERO
	player.move_and_slide()
	if extended:
		_land_on_contact()

# Called by the punch animation as the arm reaches full extension.
func enable_hitbox():
	print("Enabling hitbox")
	hitBox = player.get_node("Hitbox")
	hitBox.monitoring = true
	hitBox.monitorable = true
	if player.feel_v2:
		extended = true
		_land_on_contact()

# feel_v2: the punch resolves the moment the arm is out, on the boss hurtbox it reaches, rather than
# when that hurtbox reports it two frames after the swing. The boss's own report still arrives and
# finds the swing already resolved.
func _land_on_contact() -> void:
	if not player.combo.swing_open:
		return
	for area in hitBox.get_overlapping_areas():
		if not area.is_in_group(player.BOSS_TARGET_GROUP):
			continue
		var target := _boss_of(area)
		if target != null:
			player.combo.resolve_punch(target)
			return
	_refuse_if_closed()


# A boss outside his windows has his hurtbox switched off, so the fist would pass through him in
# silence: the punch is refused instead (PlayerCombo.refuse_punch), with its dull deflect. Not on first
# contact, though: an opening that starts under the fist takes PlayerCombo.REPORT_FRAMES to show among
# the overlaps above, and it must land.
func _refuse_if_closed() -> void:
	var target := _closed_boss_reached()
	if target == null:
		return
	if target != closed_target:
		closed_target = target
		closed_since = Engine.get_physics_frames()
	if Engine.get_physics_frames() - closed_since >= player.combo.REPORT_FRAMES:
		player.combo.refuse_punch(target)


# The boss whose switched-off hurtbox the fist is on, if he can be seen: one teleported out or hidden
# for a beat leaves his hurtbox where he was.
func _closed_boss_reached() -> Node:
	var fist: CollisionShape2D = hitBox.get_node("CollisionShape2D")
	var reach: Rect2 = fist.global_transform * fist.shape.get_rect()
	for area in get_tree().get_nodes_in_group(player.BOSS_TARGET_GROUP):
		if area.monitorable:
			continue
		var shape: CollisionShape2D = area.get_node("CollisionShape2D")
		if not reach.intersects(shape.global_transform * shape.shape.get_rect()):
			continue
		var target := _boss_of(area)
		if target != null and target.sprite.is_visible_in_tree():
			return target
	return null


# The body that owns a hurtbox, which is not always its parent: Josh and Bixby both hang theirs off
# an `Air` node so the hover can move the whole body, and Air is a bare Node2D. Taking the parent
# found no `take_punch` there, so under feel_v2 every punch whiffed and end_swing() killed the combo
# - neither fight could be won. Walking up instead of assuming the shape costs nothing and means a
# boss can nest its hurtbox however its animation needs to.
#
# Bounded by the fight's own root rather than the scene's, so a hurtbox with no owner resolves to
# null and the swing stays open for the boss's own report, exactly as it did before.
func _boss_of(area: Area2D) -> Node:
	var node: Node = area
	while node != null and node != get_tree().current_scene:
		if node.has_method("take_punch"):
			return node
		node = node.get_parent()
	return null
