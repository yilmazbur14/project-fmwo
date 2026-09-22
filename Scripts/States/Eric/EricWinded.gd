extends State

# The window after a chain in the reworked fight (EricPacing V2): Eric stands winded for a short beat,
# open to punches but never dazed, since a Break (BossBreakGauge) is what dazes him now. The state
# machine times it on its DownedTimer, as it does V1's Downed, and starts the next chain from there.

const EricArtLayout := preload("res://Scripts/EricArtLayout.gd")
const EricPhaseTwoPose := preload("res://Scripts/EricPhaseTwoPose.gd")

@export var animation_player : AnimationPlayer
@export var character_body : CharacterBody2D
@export var hurtbox : Area2D

var sheet_texture: Texture2D
var sheet_frames := 0
# Phase two: eric_winded.png draws him leaning on the sword that was thrown out of the ring, so he
# gets his blown phase-two frames instead, driven from here rather than by an animation.
var phase_two := false
var pose_frames: Array = []
var pose_clock := 0.0


func Enter() -> void:
	var art := EricArtLayout.winded()
	var sprite: Sprite2D = character_body.sprite
	sheet_texture = sprite.texture
	sheet_frames = sprite.hframes
	phase_two = character_body.phase_two
	if phase_two:
		animation_player.stop()
		pose_frames = EricPhaseTwoPose.show(sprite, "rest")
		pose_clock = 0.0
	else:
		if art.has("texture"):
			sprite.texture = load(art.texture)
			sprite.hframes = art.hframes
		animation_player.play(art.anim)
	hurtbox.monitoring = true
	hurtbox.monitorable = true


func Physics_Update(delta: float) -> void:
	if not phase_two:
		return
	pose_clock += delta
	character_body.sprite.frame = EricPhaseTwoPose.frame_at(pose_frames, pose_clock)


func Exit() -> void:
	var sprite: Sprite2D = character_body.sprite
	sprite.hframes = sheet_frames
	sprite.texture = sheet_texture
