extends State

# The player during the finisher. PlayerFinisher picks the frames and ends the state; this only puts
# the finisher sheet on the sprite and gives the sprite back exactly as it was.

const FinisherArtLayout := preload("res://Scripts/FinisherArtLayout.gd")

@export var animation_player : AnimationPlayer
@export var player : CharacterBody2D

var saved_texture: Texture2D
var saved_hframes := 1
var saved_vframes := 1
var saved_frame := 0
var saved_offset := Vector2.ZERO
var saved_flip_h := false
var saved_z_index := 0


func Enter() -> void:
	animation_player.stop()
	var sprite: Sprite2D = player.sprite
	saved_texture = sprite.texture
	saved_hframes = sprite.hframes
	saved_vframes = sprite.vframes
	saved_frame = sprite.frame
	saved_offset = sprite.offset
	saved_flip_h = sprite.flip_h
	saved_z_index = sprite.z_index
	var sheet := FinisherArtLayout.player_sheet()
	sprite.texture = load(sheet.texture)
	sprite.hframes = sheet.hframes
	sprite.vframes = sheet.vframes
	sprite.z_index = FinisherArtLayout.FINISHING_Z_INDEX


func Exit() -> void:
	var sprite: Sprite2D = player.sprite
	sprite.texture = saved_texture
	sprite.hframes = saved_hframes
	sprite.vframes = saved_vframes
	sprite.frame = saved_frame
	sprite.offset = saved_offset
	sprite.flip_h = saved_flip_h
	sprite.z_index = saved_z_index


func Physics_Update(_delta: float) -> void:
	player.velocity = Vector2.ZERO


# Moves the frame with the sprite's offset, never its position: Mason's fight y-sorts on the position.
func show_frame(frame: int, texel_offset: Vector2, flipped: bool) -> void:
	var sprite: Sprite2D = player.sprite
	sprite.frame = frame
	sprite.offset = saved_offset + FinisherArtLayout.player_sheet().offset + texel_offset
	sprite.flip_h = flipped
