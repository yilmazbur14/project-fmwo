extends State

# The window after a chain in the reworked fight (EricPacing V2): Eric stands winded for a short beat,
# open to punches, and a POW in it dazes him for the uppercut mash (EricScript.daze_in_windows, the user's
# 2026-10-05 rule; off, only a Break dazes him). The state machine times it on its DownedTimer, as it does
# V1's Downed, and starts the next chain from there.

const EricArtLayout := preload("res://Scripts/EricArtLayout.gd")

@export var animation_player : AnimationPlayer
@export var character_body : CharacterBody2D
@export var hurtbox : Area2D

var sheet_texture: Texture2D
var sheet_frames := 0


func Enter() -> void:
	var art := EricArtLayout.winded()
	var sprite: Sprite2D = character_body.sprite
	sheet_texture = sprite.texture
	sheet_frames = sprite.hframes
	if art.has("texture"):
		sprite.texture = load(art.texture)
		sprite.hframes = art.hframes
	animation_player.play(art.anim)
	hurtbox.monitoring = true
	hurtbox.monitorable = true
	# A window of its own: whatever an earlier one spent, it has its daze.
	character_body.daze_used = false


func Exit() -> void:
	var sprite: Sprite2D = character_body.sprite
	sprite.hframes = sheet_frames
	sprite.texture = sheet_texture
