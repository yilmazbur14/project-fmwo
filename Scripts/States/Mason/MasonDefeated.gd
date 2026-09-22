extends State

const MasonArtLayout := preload("res://Scripts/MasonArtLayout.gd")

@export var animation_player : AnimationPlayer
@export var body : CharacterBody2D

# Set by the state machine when a juggle killed him (MasonStateMachine.land_juggled): he stays lying
# where he crashed, on the juggle sheet, rather than dropping into his own defeat pose.
var lying := false
var sheet_texture: Texture2D
var sheet_frames := 0
var sheet_offset := Vector2.ZERO


func Enter() -> void:
	if not lying:
		animation_player.play("defeated")
		return
	var art := MasonArtLayout.juggle()
	var sprite: Sprite2D = body.sprite
	sheet_texture = sprite.texture
	sheet_frames = sprite.hframes
	sheet_offset = sprite.offset
	if art.has("texture"):
		sprite.frame = 0
		sprite.hframes = art.hframes
		sprite.texture = load(art.texture)
		# The juggle frames are taller than his main ones and hang lower to keep his feet on the
		# same ground line.
		sprite.offset = art.offset
	animation_player.play(art.down)
	# At once: this comes from inside his AnimationPlayer's own step, which would otherwise leave the
	# new clip's first frame to its next one and draw frame 0 in between.
	animation_player.advance(0.0)


func Exit() -> void:
	if not lying:
		return
	lying = false
	var sprite: Sprite2D = body.sprite
	sprite.offset = sheet_offset
	sprite.hframes = sheet_frames
	sprite.texture = sheet_texture
