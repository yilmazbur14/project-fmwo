extends RefCounted

# Every number that depends on how the controls room's sparring dummy is drawn, so a redraw only
# needs this file. Points and boxes are in texels on one of its 64x64 frames, origin top-left.
# USE_FINAL_DUMMY picks between the sheet and a code-drawn stand-in; placeholder and final art go
# through the same code, so the room is playable before the sheet lands and turning the flag off
# brings the stand-in back.
# It is a prop, not a character: a leather sparring bot on a weighted spring base with a crude
# screen-face and one padded swing arm, drawn flat and cartoony like the lockers behind it.

const SCALE := 3.0

#SHEET (training_dummy.png: one row of 64x64 frames, the dummy facing right, base on row 50)
# The barrel is 34 texels tall, 102 px on screen at SCALE: the size the user asked for. The cell
# and SCALE are untouched by that redraw, so the pixel grid still matches everything else.
const FRAME_SIZE := Vector2(64, 64)
const SHEET := "res://Assets/Characters/TrainingDummy/training_dummy.png"
const SHEET_FRAMES := 19
const USE_FINAL_DUMMY := true

# Bottom middle of the weighted base: the floor point the dummy stands on.
const ANCHOR := Vector2(32, 50)
# Where the room y-sorts it, in texels from its origin: the middle of the row its base stands on.
# The sprite sits here and its offset takes the same amount back, so the dummy is drawn exactly
# where SPRITE_OFFSET puts it and its body, hurtbox and frame_texel() don't move.
const SORT_POINT := Vector2(0, 8)
# Where the frames are drawn relative to the dummy's origin, in texels: what puts ANCHOR on the
# floor point SORT_POINT below the origin.
const SPRITE_OFFSET := FRAME_SIZE / 2.0 - ANCHOR + SORT_POINT

# The weighted base: collision, so the player bumps into it rather than standing inside it. It has
# to reach the floor, which means its bottom edge sits 3 x SORT_POINT.y below the origin - and THAT,
# not the barrel's width, is what sets how far off a player stands when they are in front of it.
const BODY_BOX := Rect2(24, 41, 16, 9)
# Everything punchable, from the top of the barrel down to the base. It reaches the floor for the
# same reason Eric's does: the punch box always reaches a little past where collision stops the
# player, so a hurtbox that stopped short of the collision box would eat punches from below.
const HURT_BOX := Rect2(24, 21, 16, 29)

# The padded arm's sweep and the torso's shove, in texels from the dummy's origin along the way it is
# facing. Both are aimed at the player rather than flipped with the sprite: it is bolted down and
# cannot turn, so nothing else would reach a player standing above or below it.
# The lunge commits the whole body, so it reaches a little PAST the arm. That is not flavour, and
# the margin is thin: collision holds the player 42 px off beside the dummy but 63 px off in front
# (the base reaches the floor, they do not), while the box is placed unrotated, so in front it is
# the box's OWN half-height that has to cover them. Beside: 72 px of reach over a 42 px standoff.
# In front: 68 over 63. A yellow attack that cannot reach the spot they punch from teaches nothing,
# and `h` is the lever for the front reach alone - it does not touch the beside reach.
# Those two standoffs are the player's own half-body against the base box, so they move when he does:
# they were 36 and 50 while he drew at 2x. What does not move is the near edge of where he stands -
# his body is flush against the base either way - which is why the reach still covers him unchanged.
# art_source/player_size/probe_dummy_dodge.gd measures all of it.
const SWING_BOX := Rect2(4, -8, 12, 16)
const LUNGE_BOX := Rect2(5, -8, 19, 16)
# How far the torso leans out on the lunge, on the sprite offset alone.
const LUNGE_PUSH := 4.0

# About 34 px over the screen-face, where the finisher's daze stars circle.
const DAZE_ANCHOR_OFFSET := Vector2(0, -112)
# Where a red or yellow tell badge stands, just over the head.
const TELL_ANCHOR_OFFSET := Vector2(0, -92)
# Its middle in the air, which the camera follows through a juggle.
const JUGGLE_POINT_OFFSET := Vector2(0, -38)
# The most an uppercut may lift it and still be seen whole. The tiered finisher plans an arc of about
# 480 px, so a full three-bar mash is scaled down to this.
const JUGGLE_HEADROOM := 300.0

#ANIMATIONS
# name: the frames in order, the seconds on each (the last value repeats) and whether it loops.
const ANIMS := {
	&"idle": {frames = [0, 1], times = [0.9, 0.9], loop = true},
	&"recoil": {frames = [2, 3], times = [0.07, 0.11], loop = false},
	&"windup_red": {frames = [4, 5], times = [0.45, 0.45], loop = true},
	&"swing": {frames = [6, 7, 8], times = [0.08, 0.10, 0.16], loop = false},
	&"windup_yellow": {frames = [9, 10], times = [0.4, 0.4], loop = true},
	&"lunge": {frames = [11, 12], times = [0.08, 0.17], loop = false},
	&"daze": {frames = [13, 14], times = [0.16, 0.16], loop = true},
	&"launch": {frames = [15], times = [0.2], loop = false},
	&"crash": {frames = [16, 17], times = [0.18, 0.3], loop = false},
	&"stagger": {frames = [18], times = [0.4], loop = false},
}

#PLACEHOLDER
# Five polygons standing in for the sheet: a weighted base, a spring post, a barrel torso, a
# screen-face and one padded arm. Each sheet frame is a pose of those pieces, so the same animation
# table drives both and flipping USE_FINAL_DUMMY changes nothing else.
#     lean  texels the barrel leans along the way it faces
#     arm   degrees the padded arm has swung from hanging, positive toward the front
#     tip   degrees the whole figure has tipped over its base
const PLACEHOLDER_POSES := {
	0: {lean = 0.0, arm = 10.0, tip = 0.0},
	1: {lean = 0.325, arm = -6.0, tip = 1.5},
	2: {lean = -3.25, arm = 26.0, tip = -6.0},
	3: {lean = -1.3, arm = 16.0, tip = -2.0},
	4: {lean = -1.95, arm = -70.0, tip = -3.0},
	5: {lean = -2.6, arm = -84.0, tip = -4.0},
	6: {lean = 0.65, arm = -30.0, tip = 0.0},
	7: {lean = 2.6, arm = 40.0, tip = 5.0},
	8: {lean = 1.3, arm = 62.0, tip = 3.0},
	9: {lean = -2.6, arm = 4.0, tip = -5.0},
	10: {lean = -3.9, arm = 2.0, tip = -7.0},
	11: {lean = 4.55, arm = 12.0, tip = 9.0},
	12: {lean = 3.25, arm = 14.0, tip = 7.0},
	13: {lean = 1.95, arm = 20.0, tip = 4.0},
	14: {lean = -1.95, arm = -14.0, tip = -4.0},
	15: {lean = 0.0, arm = -40.0, tip = -20.0},
	16: {lean = 0.0, arm = 70.0, tip = 78.0},
	17: {lean = -1.3, arm = 30.0, tip = 30.0},
	18: {lean = -2.6, arm = 34.0, tip = -10.0},
}
# The locker room's flat palette (DB32), so the stand-in already reads as gear the room owns.
const PLACEHOLDER_COLOURS := {
	base = Color("524b24"),
	base_rim = Color("222034"),
	post = Color("696a6a"),
	torso = Color("8f563b"),
	torso_band = Color("d9a066"),
	face = Color("306082"),
	face_lit = Color("9badb7"),
	arm = Color("663931"),
	arm_pad = Color("df7126"),
}
# Each piece in texels on the frame, before the pose moves it. The figure tips about PIVOT and the
# arm turns about SHOULDER, both of which are in texels from the dummy's origin.
const PLACEHOLDER_PIVOT := Vector2(0, 3)
const PLACEHOLDER_SHOULDER := Vector2(5, -12)
const PLACEHOLDER_PARTS := {
	base = Rect2(-15, 12, 30, 12),
	base_foot = Rect2(-15, 20, 30, 4),
	post = Rect2(-3, 6, 6, 8),
	torso = Rect2(-12, -22, 24, 30),
	torso_band = Rect2(-12, -10, 24, 5),
	face = Rect2(-7, -28, 14, 9),
	face_lit = Rect2(-5, -26, 10, 3),
	arm = Rect2(0, -3, 17, 6),
	arm_pad = Rect2(13, -5, 6, 10),
}


#MODE POST
# training_dummy_switch.png: 2 frames of 24x40, BAG lit then SPAR lit. It stands beside the dummy,
# against the lockers, and walking into it is what flips the dummy between the two.
const USE_FINAL_SWITCH := true
const SWITCH_SHEET := "res://Assets/Characters/TrainingDummy/training_dummy_switch.png"
const SWITCH_FRAME_SIZE := Vector2(24, 40)
const SWITCH_SCALE := 3.0
# The stand-in: a steel column with a lamp on its head plate, lit red while it is sparring. Texels
# around the post's origin, which is the floor point it stands on.
const PLACEHOLDER_SWITCH := {
	column = Rect2(-5, -28, 10, 28),
	plate = Rect2(-9, -41, 18, 13),
	lamp = Rect2(-5, -38, 10, 7),
	column_colour = Color("595652"),
	plate_colour = Color("222034"),
	bag_colour = Color("696a6a"),
	spar_colour = Color("ac3232"),
}


# Texels from the dummy's origin of a point on its frames. Shapes under the body are measured in
# these: the body is drawn at SCALE, so its own local space is already the sheet's texels.
static func frame_texel(point: Vector2) -> Vector2:
	return point - FRAME_SIZE / 2.0 + SPRITE_OFFSET


static func anim(anim_name: StringName) -> Dictionary:
	return ANIMS[anim_name]


# The four corners of a rect, for the stand-in's pieces.
static func rect_polygon(box: Rect2) -> PackedVector2Array:
	return PackedVector2Array([
		box.position, Vector2(box.end.x, box.position.y), box.end,
		Vector2(box.position.x, box.end.y),
	])
