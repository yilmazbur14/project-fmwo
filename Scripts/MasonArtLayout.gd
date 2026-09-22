extends RefCounted

# Every number that depends on how Mason is drawn, so a redraw at a new frame size only needs this
# file. Points are in texels on a frame, origin top-left. MasonScript and his states apply them at
# runtime; the values in MasonScene are copies for the editor.
#
# His transform is the opposite of Eric's: his CharacterBody2D is at scale 1 and the 3x lives on his
# Sprite2D. So frame_local() below returns BODY-LOCAL PIXELS, not texels, and nothing may multiply
# its result by SCALE again.

const SCALE := 3.0

#MASON SHEET (mason_sheet.png)
const FRAME_SIZE := Vector2(64, 64)
const SHEET_FRAMES := 19
# Sprite2D.offset in MasonScene: where the frames are drawn relative to his origin, in texels.
const SPRITE_OFFSET := Vector2(0, -32)
# Sprite2D.position in MasonScene, in body px: where his fight y-sorts him, the row his feet stand on.
const SORT_POINT := Vector2(0, 96)
# The row his feet stand on. A flying Mason's shadow is measured from it.
const FEET_ROW := 63.0
# Bottom middle of him, under his feet.
const FEET_PIXEL := Vector2(32, FEET_ROW)

#BROKEN (MasonBroken, a full Break gauge)
# mason_broken.png, when it is drawn: he drops, winded and open, and slumps in a loop. Its dictionary
# takes the same keys as the placeholder plus "texture" and "hframes", and may add "head" and "heads"
# (frame pixels just above his head, where the daze stars circle) once the frames are known. It has no
# "sword": Mason has nothing to drop.
# The placeholder loops his defeated frames 13-14, where he is already down and beaten.
const USE_FINAL_BROKEN := false
const FINAL_BROKEN := {}
const PLACEHOLDER_BROKEN := {"intro": &"", "loop": &"broken"}

#JUGGLED (MasonJuggled, under the tiered finisher's uppercuts)
# mason_juggle.png: 12 frames of 128x96, feet at (64, 95). The hit 0-1; a tumble looping 2-6 that opens
# on a long hang at the apex and then spins; the crash 7-9; and him lying breathing 10-11.
# ITS FRAME IS NOT HIS MAIN SHEET'S. 128x96 against 64x64, so the sprite has to hang 16 texels lower
# (offset -48 against -32) to keep his feet on the same ground line, and every point on it is measured
# through juggle_local() rather than frame_local(). What makes that easy to get wrong: his
# CharacterBody2D's origin is his middle, not his feet, which are 94.5 px below it.
# The placeholder threw his hit frame around his waddle frames on the main sheet, so it names no frame
# or offset of its own and falls back to that sheet's, and its top_row counts the whole frame as him.
const USE_FINAL_JUGGLE := true
const FINAL_JUGGLE := {
	"texture": "res://Assets/Characters/Mason/mason_juggle.png",
	"hframes": 12,
	"frame_size": Vector2(128, 96),
	"offset": Vector2(0, -48),
	"feet": Vector2(64, 95),
	# The middle of him in the air, which the finisher's camera follows.
	"tumble_centre": Vector2(64, 52),
	# The highest row anything is drawn on while he's in the air, so his top is this far over his
	# ground line when he isn't lifted.
	"top_row": 9,
	"launch": &"juggle_hit_final",
	"tumble": &"juggle_tumble_final",
	"crash": &"juggle_crash_final",
	"down": &"juggle_down_final",
}
const PLACEHOLDER_JUGGLE := {
	"launch": &"juggle_hit",
	"tumble": &"juggle_tumble",
	"crash": &"juggle_crash",
	"down": &"juggle_down",
	"feet": FEET_PIXEL,
	"tumble_centre": Vector2(32, 36),
	"top_row": 0,
}
# The whole of him stays at least this far below the top of the arena at the top of his flight: the
# finisher scales the juggle's heights down to fit (juggle_headroom).
const JUGGLE_TOP_MARGIN := 12.0
# His shadow on the mat while he's in the air: frame `lift / step` (0 low, 2 high), under his feet. The
# ellipses are drawn solid black; the alpha here is what makes them a shadow.
const JUGGLE_SHADOW := {
	"texture": "res://Assets/Characters/Mason/mason_leap_shadow.png",
	"hframes": 3,
	"scale": 3.0,
	"alpha": 0.35,
	"step": 100.0,
}
# The mark a Knight Breaker crash leaves on the floor. Gated by presence rather than a flag: there is
# no Mason crater art, so this is empty and MasonJuggled skips it. When there is one it takes the same
# keys as EricArtLayout.CRASH_CRATER.
const CRASH_CRATER := {}
# Lying after the crash, before he gets up.
const JUGGLE_LYING_TIME := 0.3
# A juggle that kills him holds the outro's first line this long, so the line does not start over him
# while he is still in the air. Eric's is 1.8 for the same reason; the fall is the finisher's own arc
# and is the dominant term, so his number carries. Mason's crash clip is 0.26 against Eric's 0.30, so
# this has 0.04 more margin than Eric's does rather than less.
const JUGGLE_OUTRO_DELAY := 1.8
# Every crash, whatever the tier: the fight's own impact, pitched down so it reads as weight.
const CRASH_THUD_SFX := {"stream": "res://Assets/Audio/SFX/hit_impact.ogg", "pitch": 0.7, "volume_db": 0.0}

#BREAK (MasonBroken's Break frame)
# The Break's sting, on the Break frame. Its level is baked in.
const BREAK_STING_SFX := [
	{"stream": "res://Assets/Audio/SFX/break_sting.wav", "pitch": 1.0, "volume_db": 0.0},
]

#THE FRY TRAIL (MasonIntro)
# The fries on the floor he is lured into the ring along: one dropped piece per stop he makes on the
# way in, each one left as crumbs once he has reached it.
#
# fry_trail.png: 7 frames of 32x16, drawn at SCALE, in his own six measured colours over his
# pure-black keyline. EVERY PIECE IS CENTRED ON TEXEL (16, 8), so a plain centred Sprite2D drops one
# on the floor point it is given and there is no pivot to keep in step with a redraw. flip_h doubles
# the sheet and is safe; flip_v is not - it puts the drawn contact edge on the far side of the piece
# and it stops sitting on the floor. Its source, and the round-trip check for it, are in
# art_source/mason_intro/.
#   0 one bent fry, the workhorse      3 three and crumbs, a dropped handful
#   1 one steeper, shorter fry         4 one fry in a ketchup drag, the accent
#   2 two crossed, a small drop        5, 6 the residues (FRY_EATEN)
const USE_FINAL_FRY_TRAIL := true
const FINAL_FRY_TRAIL := {
	"texture": "res://Assets/Characters/Mason/fry_trail.png",
	"hframes": 7,
	"scale": SCALE,
}
# The stand-in the beat was built and timed on, before the sheet landed: one piece is a blob of
# ketchup with loose sticks fanned over it, in the same palette. Its sticks are half the drawn ones'
# length, so a trail built from it sits closer together than the numbers below are set for.
# `at` is where a stick sits in the piece and `turn` how far it is rolled over, in turns.
const PLACEHOLDER_FRY_TRAIL := {
	"fry": Vector2(3, 11),
	"tip": Vector2(3, 3),
	"ketchup": Vector2(9, 4),
	"keyline": Color(0, 0, 0),
	"fry_color": Color(0.83137256, 0.8, 0.18039216),
	"tip_color": Color(0.627451, 0.5647059, 0.3137255),
	"ketchup_color": Color(0.6745098, 0.19607843, 0.19607843),
	"scale": SCALE,
	"fries": [
		{"at": Vector2(-4, -1), "turn": -0.16},
		{"at": Vector2(3, -3), "turn": 0.09},
		{"at": Vector2(0, 2), "turn": 0.31},
	],
}
# What a piece becomes once he has eaten it. NOTHING IS EVER TAKEN OFF THE FLOOR: bare mat behind him
# reads as a trail that was always shorter, not one he ate, so the line has to visibly turn to crumbs
# rather than empty. The residues are deliberately quiet - broken bits and crumbs, nothing more - so
# the eye stays on him and on the fries still ahead of him.
const FRY_EATEN := {0: 5, 1: 5, 2: 6, 3: 6, 4: 6}
# The line the pieces sit on, one entry per stop he makes, in order from the far end to his mark:
#   across  px off the centre line, so the trail reads as dropped rather than laid out. He walks to
#           each piece, so it is his weave as well. It stays well inside the 216 px rope doorway
#           (screen x 852..1068) both fighters come through, and the last one is 0 because he has to
#           finish on his mark.
#   frame   which piece of the sheet is dropped here.
#   flip    drawn mirrored (flip_h only, see above).
#
# THE FRAMES ARE NOT IN AN ARBITRARY ORDER. The trail runs down the screen and the pieces are drawn
# in landscape frames, so two tall ones on neighbouring stops touch. Drawn heights are 9, 14, 15, 16
# and 11 texels for frames 0-4, which at this spacing (FRY_TRAIL_SPAN over these stops, 46 px) makes
# 1-3 and 2-3 the pairs that collide: every tall piece here has a short one either side of it.
# Frame 4 is the accent and goes in ONCE. Five yellow stamps in a row on a green mat is a dotted
# line; one red one in the middle of them is a trail.
const FRY_TRAIL := [
	{"across": 15.0, "frame": 3, "flip": false},
	{"across": -21.0, "frame": 0, "flip": false},
	{"across": 8.0, "frame": 2, "flip": true},
	{"across": -13.0, "frame": 0, "flip": true},
	{"across": 19.0, "frame": 4, "flip": false},
	{"across": 0.0, "frame": 1, "flip": false},
]
# How much of his walk in has fries on it: the last FRY_TRAIL_SPAN px of it, with the stops spread
# evenly over them.
#
# THE SPAN IS NOT HIS WHOLE WALK IN (MasonIntro.WALK_IN_RISE), and must stay under it. He fights from
# the top of the ring, so there are only about 260 px of mat between the top rope and his mark: a
# trail any longer than that has its far end out over the crowd band, where a piece is drawn against
# the crowd rather than the floor and the gobble that takes it can't be seen. The span is what is on
# the mat, and the rest of his walk in is the approach he makes to the first piece.
const FRY_TRAIL_SPAN := 276.0
# A stand-in until a gobble has a sound of its own: the fight's own impact, pitched up and dropped to
# where it reads as a bite rather than a hit.
const INTRO_SFX := {
	"gobble": {"stream": "res://Assets/Audio/SFX/hit_impact.ogg", "pitch": 1.75, "volume_db": -17.0},
}


static func broken() -> Dictionary:
	return FINAL_BROKEN if USE_FINAL_BROKEN else PLACEHOLDER_BROKEN


static func juggle() -> Dictionary:
	return FINAL_JUGGLE if USE_FINAL_JUGGLE else PLACEHOLDER_JUGGLE


static func crash_crater() -> Dictionary:
	return CRASH_CRATER


# Position in Mason's BODY space, in px, of a point on his frames: the scaling is on his sprite, so it
# is already applied here.
static func frame_local(point: Vector2) -> Vector2:
	return (point - FRAME_SIZE / 2.0 + SPRITE_OFFSET) * SCALE + SORT_POINT


# The same, for a point on the juggle sheet, whose frames are a different size and hang at a different
# offset. Both put his feet on the same body-local row, so a ground line read off either agrees.
static func juggle_local(point: Vector2) -> Vector2:
	var art := juggle()
	var size: Vector2 = art.get("frame_size", FRAME_SIZE)
	var offset: Vector2 = art.get("offset", SPRITE_OFFSET)
	return (point - size / 2.0 + offset) * SCALE + SORT_POINT
