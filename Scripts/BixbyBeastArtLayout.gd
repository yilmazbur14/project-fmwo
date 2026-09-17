extends RefCounted

# Every number that depends on how beast Bixby is drawn, so the combat set can drop in with only this
# file changing. Points and boxes are in texels on a frame, origin top-left. BixbyBeastScript builds
# the fire hitbox, the hurtbox and the shadow from these at runtime.

const SCALE := 3.0

#HOVER (bixby_beast.png, 4 frames of 192x160)
const HOVER_SHEET := "res://Assets/Characters/Bixby/bixby_beast.png"
const FRAME_SIZE := Vector2(192, 160)
# His feet: where he stands once landed and what he hovers from. Every beast sheet is drawn top-aligned
# with the hover frames around this point.
const ANCHOR := Vector2(96, 151)
# The shadow is drawn this far below his feet while he hovers.
const HOVER_HEIGHT := 40.0
# What's drawn on the hover frames, and on the fire-breath frames with the stream at its longest.
const HOVER_DRAWN := Rect2(4, 3, 184, 154)
const FIRE_DRAWN := Rect2(4, 3, 184, 250)

#SHADOW (bixby_beast_shadow.png, 4 frames of 192x48, one per hover frame)
const SHADOW_SHEET := "res://Assets/Characters/Bixby/bixby_beast_shadow.png"
const SHADOW_FRAME_SIZE := Vector2(192, 48)
const SHADOW_CENTRE := Vector2(96, 25)
const SHADOW_DRAWN := Rect2(10, 5, 172, 33)
const SHADOW_ALPHA := 0.38

#FIRE BREATH (bixby_beast_firebreath.png, 3 frames of 192x256: wind-up, burst, full stream)
const FIRE_SHEET := "res://Assets/Characters/Bixby/bixby_beast_firebreath.png"
const FIRE_FRAME_SIZE := Vector2(192, 256)
# The fire drawn on the burst and full-stream frames, traced around the stream to within a texel. The
# middle stream leaves the mouth at (96, 82) and the side streams at (52, 86) and (139, 86).
const FIRE_OUTLINES := {
	1: [
		Vector2(93, 76), Vector2(99, 76), Vector2(104, 80), Vector2(104, 87), Vector2(102, 88),
		Vector2(103, 92), Vector2(107, 93), Vector2(105, 88), Vector2(114, 88), Vector2(113, 94),
		Vector2(106, 95), Vector2(112, 114), Vector2(116, 106), Vector2(135, 88), Vector2(137, 82),
		Vector2(141, 83), Vector2(144, 81), Vector2(142, 84), Vector2(145, 85), Vector2(145, 88),
		Vector2(141, 91), Vector2(140, 98), Vector2(153, 99), Vector2(152, 103), Vector2(137, 102),
		Vector2(136, 105), Vector2(134, 105), Vector2(135, 107), Vector2(132, 112), Vector2(138, 109),
		Vector2(138, 107), Vector2(139, 110), Vector2(130, 115), Vector2(124, 139), Vector2(115, 151),
		Vector2(115, 158), Vector2(110, 158), Vector2(109, 162), Vector2(103, 158), Vector2(90, 158),
		Vector2(84, 160), Vector2(82, 155), Vector2(78, 154), Vector2(78, 152), Vector2(75, 156),
		Vector2(74, 141), Vector2(67, 132), Vector2(65, 126), Vector2(62, 124), Vector2(59, 114),
		Vector2(53, 109), Vector2(54, 107), Vector2(58, 111), Vector2(56, 103), Vector2(40, 103),
		Vector2(39, 100), Vector2(53, 97), Vector2(51, 91), Vector2(47, 88), Vector2(47, 85),
		Vector2(55, 82), Vector2(57, 87), Vector2(67, 96), Vector2(76, 112), Vector2(82, 117),
		Vector2(85, 108), Vector2(86, 95), Vector2(79, 94), Vector2(78, 88), Vector2(87, 88),
		Vector2(87, 93), Vector2(89, 88), Vector2(88, 80),
	],
	2: [
		Vector2(96, 76), Vector2(99, 76), Vector2(104, 80), Vector2(105, 93), Vector2(107, 93),
		Vector2(105, 88), Vector2(114, 88), Vector2(113, 94), Vector2(106, 95), Vector2(111, 110),
		Vector2(125, 98), Vector2(125, 96), Vector2(135, 87), Vector2(137, 82), Vector2(145, 85),
		Vector2(145, 88), Vector2(141, 92), Vector2(140, 98), Vector2(153, 99), Vector2(152, 103),
		Vector2(137, 103), Vector2(133, 112), Vector2(138, 107), Vector2(139, 110), Vector2(132, 115),
		Vector2(130, 114), Vector2(130, 117), Vector2(128, 117), Vector2(127, 128), Vector2(121, 144),
		Vector2(122, 159), Vector2(124, 161), Vector2(125, 171), Vector2(129, 176), Vector2(132, 194),
		Vector2(130, 197), Vector2(131, 209), Vector2(133, 209), Vector2(136, 214), Vector2(136, 244),
		Vector2(138, 245), Vector2(139, 235), Vector2(140, 232), Vector2(142, 232), Vector2(142, 250),
		Vector2(129, 250), Vector2(128, 247), Vector2(124, 247), Vector2(124, 250), Vector2(121, 250),
		Vector2(120, 247), Vector2(118, 250), Vector2(111, 250), Vector2(111, 248), Vector2(109, 250),
		Vector2(104, 250), Vector2(103, 247), Vector2(100, 247), Vector2(99, 250), Vector2(79, 250),
		Vector2(76, 244), Vector2(74, 244), Vector2(71, 250), Vector2(64, 250), Vector2(64, 240),
		Vector2(62, 240), Vector2(61, 250), Vector2(53, 250), Vector2(52, 229), Vector2(55, 221),
		Vector2(54, 210), Vector2(56, 197), Vector2(64, 169), Vector2(71, 157), Vector2(72, 141),
		Vector2(63, 130), Vector2(59, 114), Vector2(53, 109), Vector2(53, 107), Vector2(57, 109),
		Vector2(55, 102), Vector2(40, 103), Vector2(39, 99), Vector2(53, 97), Vector2(51, 91),
		Vector2(47, 88), Vector2(47, 85), Vector2(55, 82), Vector2(57, 87), Vector2(67, 95),
		Vector2(73, 107), Vector2(79, 113), Vector2(85, 95), Vector2(79, 94), Vector2(78, 88),
		Vector2(88, 89), Vector2(88, 80), Vector2(91, 77),
	],
}

#RECOVERY
# What the player can punch while he's down: his torso and legs, out to the side heads' jaws.
const RECOVER_BODY_BOX := Rect2(44, 80, 104, 76)
# Where the finisher's daze stars circle, between his horns.
const DAZE_ANCHOR := Vector2(96, 30)

#ANIMATIONS
# name: sheet, its frame size, the frames in order (empty for every frame on the sheet), seconds per
# frame, whether it loops, and the shadow frame under each frame (the last one repeats).
# The placeholders reuse the hover and fire-breath sheets, and the states add tweens to them (a descent,
# a darker slow bob, a flinch). Set a USE_FINAL entry once its sheet is approved and imported to play
# the drawn animation instead and drop the placeholder tweens.
const PLACEHOLDER_ANIMS := {
	&"hover": {sheet = HOVER_SHEET, frame_size = FRAME_SIZE, frames = [0, 1, 2, 3], frame_time = 0.12, loop = true, shadow = [0, 1, 2, 3]},
	&"fly": {sheet = HOVER_SHEET, frame_size = FRAME_SIZE, frames = [0, 1, 2, 3], frame_time = 0.08, loop = true, shadow = [0, 1, 2, 3]},
	&"windup": {sheet = FIRE_SHEET, frame_size = FIRE_FRAME_SIZE, frames = [0], frame_time = 1.0, loop = true, shadow = [2]},
	&"burst": {sheet = FIRE_SHEET, frame_size = FIRE_FRAME_SIZE, frames = [1], frame_time = 1.0, loop = true, shadow = [2]},
	&"stream": {sheet = FIRE_SHEET, frame_size = FIRE_FRAME_SIZE, frames = [2], frame_time = 1.0, loop = true, shadow = [2]},
	&"land": {sheet = HOVER_SHEET, frame_size = FRAME_SIZE, frames = [0, 1, 2, 3], frame_time = 0.06, loop = true, shadow = [0, 1, 2, 3]},
	&"recover": {sheet = HOVER_SHEET, frame_size = FRAME_SIZE, frames = [0], frame_time = 1.0, loop = true, shadow = [0]},
	&"hit": {sheet = HOVER_SHEET, frame_size = FRAME_SIZE, frames = [2], frame_time = 0.2, loop = false, shadow = [2]},
	&"takeoff": {sheet = HOVER_SHEET, frame_size = FRAME_SIZE, frames = [0, 1, 2, 3], frame_time = 0.06, loop = true, shadow = [0, 1, 2, 3]},
	&"roar": {sheet = HOVER_SHEET, frame_size = FRAME_SIZE, frames = [0, 1, 2, 3], frame_time = 0.05, loop = true, shadow = [0, 1, 2, 3]},
}
const FINAL_ANIMS := {
	&"fly": {sheet = "res://Assets/Characters/Bixby/bixby_beast_fly.png", frame_size = FRAME_SIZE, frames = [], frame_time = 0.1, loop = true, shadow = [1]},
	&"land": {sheet = "res://Assets/Characters/Bixby/bixby_beast_land.png", frame_size = FRAME_SIZE, frames = [0, 1, 2], frame_time = 0.17, loop = false, shadow = [1, 0, 0]},
	&"recover": {sheet = "res://Assets/Characters/Bixby/bixby_beast_recover.png", frame_size = FRAME_SIZE, frames = [0, 1, 2, 3], frame_time = 0.25, loop = true, shadow = [0]},
	&"hit": {sheet = "res://Assets/Characters/Bixby/bixby_beast_hit.png", frame_size = FRAME_SIZE, frames = [0, 1], frame_time = 0.1, loop = false, shadow = [0]},
	&"takeoff": {sheet = "res://Assets/Characters/Bixby/bixby_beast_takeoff.png", frame_size = FRAME_SIZE, frames = [0, 1, 2], frame_time = 0.2, loop = false, shadow = [0, 1, 2]},
	# Ends on normal Bixby with Liam coughed up beside him.
	&"defeat": {sheet = "res://Assets/Characters/Bixby/bixby_beast_defeat.png", frame_size = FRAME_SIZE, frames = [], frame_time = 0.1, loop = false, shadow = [0]},
	&"roar": {sheet = "res://Assets/Characters/Bixby/bixby_beast_roar.png", frame_size = FRAME_SIZE, frames = [0, 1, 2], frame_time = 0.15, loop = false, shadow = [1]},
}
const USE_FINAL := {
	&"fly": false,
	&"land": false,
	&"recover": false,
	&"hit": false,
	&"takeoff": false,
	&"defeat": false,
	&"roar": false,
}


static func uses_final(anim_name: StringName) -> bool:
	return USE_FINAL.get(anim_name, false)


static func anim(anim_name: StringName) -> Dictionary:
	return FINAL_ANIMS[anim_name] if uses_final(anim_name) else PLACEHOLDER_ANIMS[anim_name]


# Sprite offset, in texels, that puts ANCHOR on the sprite's origin for a sheet of this frame size.
static func sheet_offset(frame_size: Vector2) -> Vector2:
	return frame_size / 2.0 - ANCHOR


# Screen-px offset from his feet of a point on his frames.
static func local(point: Vector2) -> Vector2:
	return (point - ANCHOR) * SCALE


static func local_rect(rect: Rect2) -> Rect2:
	return Rect2(local(rect.position), rect.size * SCALE)


# The shadow's drawn box in px around the floor point under him.
static func shadow_rect() -> Rect2:
	return Rect2((SHADOW_DRAWN.position - SHADOW_CENTRE) * SCALE, SHADOW_DRAWN.size * SCALE)


static func shadow_offset() -> Vector2:
	return SHADOW_FRAME_SIZE / 2.0 - SHADOW_CENTRE


static func fire_outline(frame: int) -> PackedVector2Array:
	var points := PackedVector2Array()
	for point in FIRE_OUTLINES[frame]:
		points.append(local(point))
	return points
