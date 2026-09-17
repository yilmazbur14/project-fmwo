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
# Corner of the 320x256 transform frames: the storyboard frame's corner moved (-124, -156) texels.
const TRANSFORM_CORNER := Vector2(-480, -756)
const FLASH_COLOR := Color(1, 250 / 255.0, 214 / 255.0)
# How strongly the screen under the transform's flash frame is tinted with FLASH_COLOR.
const FLASH_FRAME_TINT := 0.62


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
