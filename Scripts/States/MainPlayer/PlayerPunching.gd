extends State

const PunchComboArtLayout := preload("res://Scripts/PunchComboArtLayout.gd")
const PlayerFeel := preload("res://Scripts/PlayerFeel.gd")

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
var swing_animation := "punch"
# Found as the player loaded, with PunchComboArtLayout's switch on; null, and every swing is hit 1's.
var combo_sheet: Texture2D
# The sprite's own sheet, the only one the combo's hits are drawn to stand in for.
var base_sheet: Texture2D
# What this swing took off the sprite to put the combo sheet on; null while it hasn't.
var swapped_sheet: Texture2D
var swapped_hframes := 1
var swapped_vframes := 1
# The visual chain (_swing_animation): the place the next quick swing takes in it - 0 hit 1's art, 1 the
# other hand's, 2 the body blow's - and the combo's clock as the last swing ended.
var chain_next := 0
var chain_ended_at := -INF


func _ready() -> void:
	if PunchComboArtLayout.COMBO_ANIMS_ENABLED and ResourceLoader.exists(PunchComboArtLayout.SHEET):
		combo_sheet = load(PunchComboArtLayout.SHEET)
		# PlayerScript's own `sprite` is only set once its children are ready.
		base_sheet = player.get_node(^"Sprite2D").texture
		_build_combo_animations()


# Copies of "punch" - its length, beats and enable_hitbox key - stepping their own columns instead. The
# library is the scene's, shared by every MainPlayer, so the next fight's player only puts back the same
# two.
func _build_combo_animations() -> void:
	var punch := animation_player.get_animation(punching_animation)
	for animation in PunchComboArtLayout.FIRST_COLUMNS:
		var hit: Animation = punch.duplicate()
		var frames := hit.find_track(^"Sprite2D:frame_coords:x", Animation.TYPE_VALUE)
		for key in hit.track_get_key_count(frames):
			hit.track_set_key_value(frames, key, PunchComboArtLayout.FIRST_COLUMNS[animation] + key)
		animation_player.get_animation_library(&"").add_animation(animation, hit)


func Enter() -> void:
	# This fight's box for the locked facing, before the hitbox goes live (PlayerScript.feel_v2).
	player.fit_punch_hitbox()
	hitBox.monitoring = true
	hitBox.monitorable = true
	extended = false
	closed_target = null
	player.combo.start_swing()
	swing_animation = _swing_animation()
	if swing_animation != punching_animation:
		_put_on_combo_sheet()
	animation_player.speed_scale = 2.0  # Speed up only the punch animation
	animation_player.play(swing_animation)
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
	chain_ended_at = player.combo.clock
	_take_off_combo_sheet()
	animation_player.speed_scale = 1.0  # Reset back to normal for other animations


# Hit 1's, the other hand's or the body blow's, by the swing's place in a visual chain: quick swings run
# through the three in turn, whether they land or not (the user, 2026-09-27). A count the combo carries
# decides its place (PlayerCombo.swing_position): at 1 the other hand, at 2 the body blow, so the body blow
# says the next punch to land on the same target is the POW, and a landed combo looks as it always has.
# With nothing carried, a swing started within quick_gap() of the last one's end takes the chain's next
# place, and any other swing starts the chain again. Only the drawing: the charge, and everything that
# shows it, is still PlayerCombo's, so a body blow that isn't the charged punch lands as plainly as any
# other. Hit 1's as well while the combo sheet isn't found, or while the sprite is on a sheet a fight has
# put it on.
func _swing_animation() -> String:
	var chain := [punching_animation, PunchComboArtLayout.OTHER_HAND, PunchComboArtLayout.BODY_BLOW]
	var place := _chain_place()
	if combo_sheet == null or player.sprite.texture != base_sheet:
		place = 0
	chain_next = (place + 1) % chain.size()
	return chain[place]


func _chain_place() -> int:
	var position: int = player.combo.swing_position()
	if position > 0:
		return 2 if position == player.combo.hits_to_charge - 1 else 1
	if player.combo.clock - chain_ended_at <= quick_gap():
		return chain_next
	return 0


# How soon after a swing ends the next must start to carry the chain on, measured from the swing's end in
# the combo's game time, so a swing is quick or not the same whether it lands or not. No floor: a press as
# soon as the arm is back carries it on. 0.29 s under feel_v2, 0.40 s in a fight that opts out of it
# (PlayerFeel's punch_chain_gap, where the combo's beat window closed while it had one).
func quick_gap() -> float:
	return PlayerFeel.value("punch_chain_gap", player.feel_v2)


func _put_on_combo_sheet() -> void:
	var sprite: Sprite2D = player.sprite
	swapped_sheet = sprite.texture
	swapped_hframes = sprite.hframes
	swapped_vframes = sprite.vframes
	sprite.texture = combo_sheet
	sprite.hframes = PunchComboArtLayout.HFRAMES
	sprite.vframes = PunchComboArtLayout.VFRAMES
	# Narrowing the grid can reset the frame to row 0; the animation's first key only lands next process.
	sprite.frame_coords = Vector2i(PunchComboArtLayout.FIRST_COLUMNS[swing_animation], player.facing)


# From Exit, so it runs however the swing ends and before the next state's Enter: Posed, Finishing and
# GuardBroken save the sprite as they find it and give that back. A sprite something else has put on a
# sheet of its own mid-swing is left on it. Column 0 is where Idle and Walking both start.
func _take_off_combo_sheet() -> void:
	if swapped_sheet == null:
		return
	var sprite: Sprite2D = player.sprite
	if sprite.texture == combo_sheet:
		sprite.texture = swapped_sheet
		sprite.hframes = swapped_hframes
		sprite.vframes = swapped_vframes
		sprite.frame_coords = Vector2i(0, player.facing)
	swapped_sheet = null


func Update(delta: float) -> void:
	if !animation_player.is_playing():
		get_parent().on_child_transition(self, "Idle")
		return

func Physics_Update(delta: float) -> void:
	# Zero out velocity during punch; on ice the player slides on under it.
	if player.on_ice:
		player.ice_coast(delta)
	else:
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
# The overlaps are the hitbox's own list, which can keep a hurtbox for frames after his window has
# switched it off: a punch landed there after his window shut, with no mash for its POW (the user,
# 2026-10-06). One switched off is a closed boss, refused below.
func _land_on_contact() -> void:
	if not player.combo.swing_open:
		return
	for area in hitBox.get_overlapping_areas():
		if not area.is_in_group(player.BOSS_TARGET_GROUP) or not area.monitorable:
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
