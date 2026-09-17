extends RefCounted

# Every number that depends on how Liam's entrance is drawn (Assets/Characters/Liam/Entrance) and staged in
# its mockups, all art at 3x. BixbyBeastScene places the entrance sprites to match; BixbyBeastIntro moves
# them, and builds the floor shadows and sweat drops from this.

const SCALE := 3.0
const SHADOW_ALPHA := 0.38

#PROCESSION
# In px from the throne's floor point (the Procession node): texel (96, 124) of the 200x128 throne frame.
# It marches down from above the top of the screen.
const MARCH_RISE := 530.0
const MARCH_TIME := 3.2
# liam_carrier_walk.png; frames 0 and 2 are the steps.
const WALK_FRAMES := 4
const WALK_FRAME_TIME := 0.125
# The carriers with a single pose drop a texel on each step.
const MARCH_BOB_PX := 3.0
# Floor shadows while it marches, [centre, radii in texels]: the dais, then each carrier.
const MARCH_SHADOWS := [
	[Vector2(0, 21), Vector2(74, 7)],
	[Vector2(-252, 3), Vector2(8, 2.2)],
	[Vector2(264, 3), Vector2(8, 2.2)],
	[Vector2(-150, 45), Vector2(8, 2.2)],
	[Vector2(114, 45), Vector2(8, 2.2)],
]
const SET_DOWN_SHADOW := [Vector2(0, -30), Vector2(80, 10)]

# Each carrier's frame on liam_carriers.png, and how it lies flopped on the floor once the throne is set
# down: centre, turn in degrees, the corner of its sweat drop and the centre of its floor shadow.
const CARRIERS := {
	&"RearLeft": {frame = 2, flop = Vector2(-450, -18), turn = -90.0, sweat = Vector2(-486, -60), shadow = Vector2(-450, 0)},
	&"FrontLeft": {frame = 0, flop = Vector2(-358, 36), turn = -90.0, sweat = Vector2(-394, 0), shadow = Vector2(-358, 54)},
	&"FrontRight": {frame = 1, flop = Vector2(366, 40), turn = 90.0, sweat = Vector2(384, 4), shadow = Vector2(366, 58)},
	&"RearRight": {frame = 3, flop = Vector2(460, -12), turn = 90.0, sweat = Vector2(484, -51), shadow = Vector2(460, 6)},
}
const FLOPPED_SHADOW_RADII := Vector2(13, 3)
const FLOP_TIME := 0.3
const FLOP_HOP := 30.0
const SWEAT_ROWS := [".k..", "kbk.", "kWBk", ".kk."]
const SWEAT_COLORS := {
	"k": Color(0, 0, 0),
	"b": Color(203 / 255.0, 219 / 255.0, 252 / 255.0),
	"B": Color(99 / 255.0, 155 / 255.0, 1),
	"W": Color(1, 1, 1),
}

# Liam's seat and Bixby's cushion on the throne: where their feet leave from when they jump down.
const SEAT := Vector2(-96, -114)
const CUSHION := Vector2(126, -60)

#DOWNSTAGE
# In px from Bixby's feet in front of the throne (the Downstage node), where the beast appears.
const LIAM_FEET := Vector2(162, 0)
const HOP_TIME := 0.5
const HOP_HEIGHT := 90.0
# Centre of the 128x96 storyboard frames, which have Bixby at texel (4, 32) and Liam at (58, 32).
const STORYBOARD_CENTRE := Vector2(84, -144)
const STORYBOARD_FRAME_WIDTH := 128
const BIXBY_SHADOW := [Vector2(0, -4), Vector2(28, 4)]
const LIAM_SHADOW := [Vector2(156, -4), Vector2(22, 3.5)]
const FLASH_COLOR := Color(1, 250 / 255.0, 214 / 255.0)

#TRANSFORMATION
# bixby_transform.png: 26 frames of 320x256 in a 13x2 grid, read left to right, with Bixby's feet at texel
# (160, 251) in every one. bixby_transform_aura.png (4 frames) and bixby_transform_shockwave.png (5 frames
# of 320x96, centred on the feet) are drawn on the same point. The beats, by frame: 0-2 he freezes,
# 3-6 the cracks ignite, 7-9 he tears off the floor, 10-14 he swells and grows horns, 15-17 the wings tear
# out and snap open, 18-19 it implodes and holds, 20 detonates, 21-22 the cold beast stands in the smoke,
# 23-24 his eyes light, 25 holds. The frames draw him lifting off the floor themselves, from 7 up to the
# beast's hover height by 15, so they are all drawn on the same point: the last one is the beast's hover
# frame 0, HOVER_HEIGHT texels above it, where the beast takes over.
const TRANSFORM_FRAME_SIZE := Vector2(320, 256)
const TRANSFORM_ANCHOR := Vector2(160, 251)
const TRANSFORM_TIMES: Array[float] = [
	0.26, 0.12, 0.22, 0.15, 0.15, 0.13, 0.2, 0.09, 0.09, 0.11, 0.15, 0.15, 0.15,
	0.15, 0.22, 0.09, 0.09, 0.24, 0.12, 0.26, 0.09, 0.11, 0.2, 0.18, 0.18, 0.4,
]
# The ember aura burns behind him from the cracks to the wings, and fades out over the implosion.
const AURA_FRAME_TIME := 0.09
# The ground ring, on the lift-off and again on the detonation.
const SHOCKWAVE_FRAME_TIME := 0.06


# How long frames `from` to `to` of the transformation take together.
static func transform_time(from: int, to: int) -> float:
	var total := 0.0
	for index in range(from, to + 1):
		total += TRANSFORM_TIMES[index]
	return total


# Where a 320x256 transformation frame is drawn from, with its feet anchor on the sprite's position. The
# shockwave's own centre is that point, so it is drawn centred.
static func transform_offset() -> Vector2:
	return TRANSFORM_FRAME_SIZE / 2.0 - TRANSFORM_ANCHOR


# A floor shadow as the mockups draw them: the texels whose centres fall inside an ellipse with these radii,
# in texels, around the sprite's position.
static func floor_shadow(radii: Vector2) -> Sprite2D:
	var extent := ceili(maxf(radii.x, radii.y)) + 1
	var image := Image.create(extent * 2, extent * 2, false, Image.FORMAT_RGBA8)
	for y in range(-extent, extent):
		for x in range(-extent, extent):
			if pow((x + 0.5) / radii.x, 2) + pow((y + 0.5) / radii.y, 2) <= 1.0:
				image.set_pixel(x + extent, y + extent, Color.BLACK)
	var shadow := _texel_sprite(image)
	shadow.offset = Vector2(-extent, -extent)
	shadow.modulate.a = SHADOW_ALPHA
	return shadow


static func sweat_drop() -> Sprite2D:
	var image := Image.create(SWEAT_ROWS[0].length(), SWEAT_ROWS.size(), false, Image.FORMAT_RGBA8)
	for y in SWEAT_ROWS.size():
		var row: String = SWEAT_ROWS[y]
		for x in row.length():
			if SWEAT_COLORS.has(row[x]):
				image.set_pixel(x, y, SWEAT_COLORS[row[x]])
	return _texel_sprite(image)


static func _texel_sprite(image: Image) -> Sprite2D:
	var sprite := Sprite2D.new()
	sprite.texture = ImageTexture.create_from_image(image)
	sprite.centered = false
	sprite.scale = Vector2(SCALE, SCALE)
	return sprite
