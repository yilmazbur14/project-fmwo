extends RefCounted

# Every number that depends on how Eric, his bear-hug sheet and his thrown sword are drawn, so a
# redraw at a new frame size only needs this file. Points and boxes are in texels on a frame,
# origin top-left. BossOneScript and EricThrownSwordScript apply the sizes, offsets and shapes at
# runtime; the values in BossOneScene and EricThrownSwordScene are copies for the editor.

const SCALE := 3.0

#ERIC SHEETS (eric_sheet_v2.png, eric_bearhug_v2.png)
const FRAME_SIZE := Vector2(256, 192)
const SHEET_FRAMES := 40
const HUG_FRAMES := 15
# Where the frames are drawn relative to Eric's origin, in texels. It keeps his feet 63.5 texels
# below the origin, where the 128-texel frames had them. The bear hug's planted sword is drawn in
# his frame space, so it uses this too.
const SPRITE_OFFSET := Vector2(0, -32)

# His torso and legs on the idle frames: collision box and hurtbox.
const BODY_BOX := Rect2(102, 120, 58, 72)
# Active during the bear hug's lunge.
const GRAB_BOX := Rect2(102, 120, 58, 72)
# The whirlwind's sword sweep, an ellipse at waist height. The blade tips reach 126 texels out,
# a little past it.
const WHIRLWIND_CENTRE := Vector2(128, 156)
const WHIRLWIND_RADII := Vector2(118, 35)

# Blade tip on earthquake frame 7, where the slam lands.
const SLAM_PIXEL := Vector2(93, 191)
# Sword centre on frame 34, as it leaves his hand.
const THROW_RELEASE_PIXEL := Vector2(144, 92)
# Centre of the sword he holds on catch frame 39, where the returning sword arrives.
const THROW_CATCH_CENTRE := Vector2(81, 111.5)
# That sword's lean from upright, in degrees clockwise. The upright spin frame is the nearest
# match, mirrored or not, so the returning sword turns from it to this as it arrives.
const THROW_CATCH_ANGLE := -11.31
# The row his feet stand on; a flying sword's shadow is measured from it.
const FEET_ROW := 191.0

# Bottom middle of the frame, under his feet. The bear hug's player centres are measured from it.
const FEET_ANCHOR := Vector2(128, 192)
# Centre of the player drawn in his arms on bear-hug frames 7-10.
const HUG_PLAYER_CENTRES := {
	7: Vector2(-1, -30),
	8: Vector2(-0.5, -31),
	9: Vector2(0, -27.5),
	10: Vector2(-0.5, -27.5),
}
# Centre of the player thrown on frame 11, where they reappear when frame 12 starts.
const HUG_RELEASE_CENTRE := Vector2(30.5, -83.5)

#THROWN SWORD (eric_thrown_sword_v2.png, eric_sword_planted_v2.png)
const SPIN_FRAMES := 8
# Spin frames pointing down, which it lands on, and up, which he catches.
const SPIN_LANDING_FRAME := 2
const SPIN_CATCH_FRAME := 6
const PLANTED_FRAMES := 2
# Offset that puts the planted sword's ground contact on its origin, in texels.
const PLANTED_OFFSET := Vector2(0, -59)
# The spinning sword's hitbox, in px.
const SWORD_HITBOX_RADIUS := 108.0


# Position in Eric's body space (texels, before his scale) of a point on his frames, drawn
# mirrored when flip_h is set.
static func frame_local(point: Vector2, flip_h := false) -> Vector2:
	var local := point - FRAME_SIZE / 2.0
	if flip_h:
		local.x = -local.x
	return local + SPRITE_OFFSET


# Screen-px offset from Eric's origin of the centre of a pixel on his frames.
static func pixel_offset(pixel: Vector2) -> Vector2:
	return frame_local(pixel + Vector2(0.5, 0.5)) * SCALE


# Screen-px offset from Eric's origin of a point given relative to FEET_ANCHOR.
static func feet_offset(offset: Vector2) -> Vector2:
	return frame_local(FEET_ANCHOR + offset) * SCALE
