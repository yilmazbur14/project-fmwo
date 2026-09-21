extends State

@export var punching_animation : String = "punch"
# @export var speed_threshold : float = 0.1
@export var animation_player : AnimationPlayer
@export var hitBox : Area2D
@export var player : CharacterBody2D

# feel_v2: the arm has reached full extension this swing, so the punch lands on whatever it reaches.
var extended := false

func Enter() -> void:
	# This fight's box for the locked facing, before the hitbox goes live (PlayerScript.feel_v2).
	player.fit_punch_hitbox()
	hitBox.monitoring = true
	hitBox.monitorable = true
	extended = false
	player.combo.start_swing()
	animation_player.speed_scale = 2.0  # Speed up only the punch animation
	animation_player.play(punching_animation)
	# The swoosh, star and whoosh; PunchFx does nothing without feel_v2.
	if player.punch_fx:
		player.punch_fx.swing()

func Exit() -> void:
	hitBox.monitoring = false  # Disable hitbox when exiting punch state
	hitBox.monitorable = false
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
