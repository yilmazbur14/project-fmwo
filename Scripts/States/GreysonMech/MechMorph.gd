extends State

@export var animation_player : AnimationPlayer
@export var mech : Node2D
@export var sprite : Sprite2D
@export var morph_sprite : Sprite2D

const GATHER_DURATION := 0.45
# Where morph frame 0 draws Computah and Greyson, from the mech sprite's centre. Frame 0
# draws Greyson at half his phase-one size; at that size this offset puts his feet on the mech's.
const COMPUTAH_OFFSET := Vector2(-58, -42)
const GREYSON_OFFSET := Vector2(0, 80)

# The player is often standing where the mech's body appears (the spot under Computah they land
# the threshold punch from straddles both collision boxes). Switching the boxes on around them
# wedges them between the two or throws them through the back rope, so they're shoved clear
# first and the collision waits until they're out.
const SHOVE_DURATION := 0.25
const SHOVE_CLEARANCE := 6.0
# Never up: the back rope is right behind the mech.
const SHOVE_DIRECTIONS := [Vector2.DOWN, Vector2.LEFT, Vector2.RIGHT]
# Inner edges of the arena walls.
const ARENA_FLOOR := Rect2(105, 105, 1710, 870)
const PLAYER_PATH := "Arena/MainPlayer/CharacterBody2D"

var collision_pending := false
var morph_finished := false
var shoving := false

@onready var state_machine = get_parent()


func Enter() -> void:
	collision_pending = false
	morph_finished = false

	var centre := sprite.global_position
	var greyson: Node2D = mech.greyson
	var tween := create_tween().set_parallel().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tween.tween_property(mech.computah.get_node("Sprite2D"), "global_position", centre + COMPUTAH_OFFSET, GATHER_DURATION)
	tween.tween_property(greyson, "global_position", centre + GREYSON_OFFSET, GATHER_DURATION)
	tween.tween_property(greyson, "scale", greyson.scale / 2.0, GATHER_DURATION)
	tween.chain().tween_callback(_swap_to_morph)

	_shove_player_clear()


# Runs after the player has moved this frame (the mech is later in the tree), so nothing can
# step back into the boxes between this check and them switching on.
func Physics_Update(_delta: float) -> void:
	if not collision_pending or shoving:
		return
	if _player_clearing_offset() != Vector2.ZERO:
		_shove_player_clear()
		return
	for shape in _body_shapes():
		shape.disabled = false
	collision_pending = false
	if morph_finished:
		state_machine.start_cycle()


# The morph is only left for the first cycle, so the player starts facing the mech once it has formed.
func Exit() -> void:
	mech.hurtbox.add_to_group("boss_target")


func _swap_to_morph() -> void:
	mech.computah.get_node("Sprite2D").visible = false
	mech.computah.get_node("CollisionShape2D").set_deferred("disabled", true)
	mech.greyson.visible = false

	morph_sprite.visible = true
	collision_pending = true
	animation_player.play("morph")


func _on_animation_player_animation_finished(anim_name: StringName) -> void:
	if anim_name != "morph" or state_machine.current_state != self:
		return
	# The morph's last frame is idle frame 0, so the swap to the sheet is seamless.
	morph_sprite.visible = false
	sprite.visible = true
	morph_finished = true
	if not collision_pending:
		state_machine.start_cycle()


func _shove_player_clear() -> void:
	var offset := _player_clearing_offset()
	if offset == Vector2.ZERO:
		return
	var player := _player()
	shoving = true
	player.velocity = Vector2.ZERO
	# Holds the player's own movement for the shove, so held input or a dash can't fight it.
	player.set_physics_process(false)
	var tween := create_tween().set_process_mode(Tween.TWEEN_PROCESS_PHYSICS).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tween.tween_property(player, "global_position", player.global_position + offset, SHOVE_DURATION)
	tween.tween_callback(_end_shove.bind(player))


func _end_shove(player: CharacterBody2D) -> void:
	player.velocity = Vector2.ZERO
	player.set_physics_process(true)
	shoving = false


# The shortest push down or sideways that takes the player's collision box clear of both of the
# mech's boxes and stays inside the walls; zero when they're already clear.
func _player_clearing_offset() -> Vector2:
	var player_box := _collision_rect(_player().get_node("CollisionShape2D"))
	var mech_boxes := _body_shapes().map(_collision_rect)
	var best := Vector2.ZERO
	var best_distance := INF
	for direction in SHOVE_DIRECTIONS:
		var moved := player_box
		var blocked := true
		# Clearing one box can land the player in the other, so keep pushing until neither overlaps.
		while blocked:
			blocked = false
			for box in mech_boxes:
				if moved.intersects(box):
					blocked = true
					if direction == Vector2.DOWN:
						moved.position.y = box.end.y + SHOVE_CLEARANCE
					elif direction == Vector2.LEFT:
						moved.position.x = box.position.x - moved.size.x - SHOVE_CLEARANCE
					else:
						moved.position.x = box.end.x + SHOVE_CLEARANCE
		var offset := moved.position - player_box.position
		if ARENA_FLOOR.encloses(moved) and offset.length() < best_distance:
			best = offset
			best_distance = offset.length()
	return best


func _player() -> CharacterBody2D:
	return get_tree().current_scene.get_node(PLAYER_PATH)


func _body_shapes() -> Array:
	return mech.body.get_children().filter(func(child): return child is CollisionShape2D)


func _collision_rect(shape: CollisionShape2D) -> Rect2:
	var size: Vector2 = (shape.shape as RectangleShape2D).size * shape.global_scale.abs()
	return Rect2(shape.global_position - size / 2.0, size)
