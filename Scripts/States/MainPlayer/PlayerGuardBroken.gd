extends State

# The stun after the guard breaks. PlayerDefense starts and ends it; this only holds the player still
# in the stun pose and gives the sprite back exactly as it was.

const DefenseHypeArtLayout := preload("res://Scripts/DefenseHypeArtLayout.gd")

@export var animation_player : AnimationPlayer
@export var player : CharacterBody2D

var saved_texture: Texture2D
var saved_hframes := 1
var saved_vframes := 1
var saved_frame := 0
var saved_offset := Vector2.ZERO
var clock := 0.0


func Enter() -> void:
	animation_player.stop()
	var sprite: Sprite2D = player.sprite
	saved_texture = sprite.texture
	saved_hframes = sprite.hframes
	saved_vframes = sprite.vframes
	saved_frame = sprite.frame
	saved_offset = sprite.offset
	var pose := DefenseHypeArtLayout.guard_break_pose()
	if pose.has("texture"):
		sprite.texture = load(pose.texture)
		sprite.hframes = pose.hframes
		sprite.vframes = pose.vframes
	clock = 0.0
	_show_pose()


func Exit() -> void:
	var sprite: Sprite2D = player.sprite
	sprite.texture = saved_texture
	sprite.hframes = saved_hframes
	sprite.vframes = saved_vframes
	sprite.frame = saved_frame
	sprite.offset = saved_offset


func Update(delta: float) -> void:
	clock += delta
	_show_pose()


func Physics_Update(_delta: float) -> void:
	player.velocity = Vector2.ZERO


# The offset rather than the position: the hurt shake tweens the sprite's position.
func _show_pose() -> void:
	var pose := DefenseHypeArtLayout.guard_break_pose()
	var step := int(clock / pose.frame_time)
	var sprite: Sprite2D = player.sprite
	sprite.frame_coords = Vector2i(pose.frames[step % pose.frames.size()], player.facing)
	sprite.offset = saved_offset + (pose.wobble if step % 2 == 1 else Vector2.ZERO)
