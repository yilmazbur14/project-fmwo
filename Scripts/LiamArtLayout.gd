extends RefCounted

# Liam's own phase (after beast Bixby coughs him up): every number that depends on how his poses, his earth pillar,
# his waves, the gust, the flood, the ice and the tremor ridges are drawn, so the approved art only needs this file.
# Texel numbers are on a frame, origin top-left; world numbers are px.
#
# THE ART SWITCHES IN ON ITS OWN, JoshHandsLayout's way: each piece plays its final sheet once that sheet is in and
# imported (the final_* checks, gated on ResourceLoader.exists and its USE_FINAL_* switch), and its placeholder until
# then. Shipping the approved sheet IS wiring it; nothing may ship into Assets/ before the user approves it. The
# switches are static vars so a test can hold the placeholders while the final art is in (tier=placeholder).
# The numbers are the approval pass's (art_source/liam_elements/approval/anchors.json, approved 2026-09-29) where it
# gives them, and the plan's section 8 contract otherwise. The pose sheets are named for ANIMS (liam_<sheet>.png): the
# pass drew key poses, and the full sheets ship after the user's second approval.

const BixbyBeastArtLayout := preload("res://Scripts/BixbyBeastArtLayout.gd")

const SCALE := 3.0
const DIR := "res://Assets/Characters/Liam/Elements/"
const LIAM_SPRITE := "res://Assets/Characters/Liam/liam.png"

#HIS POSES
# The artist's rig: 96x96 cells with liam.png pasted at (16, 32), his feet on texel row 95. The anchor POINT is (48, 96),
# the cell's bottom-centre edge, which HopLiam's (0, -32) on liam.png also stands on. His shadow and every piece of dust
# are separate sprites on their own layers, so nothing needs texels under his feet inside his cells. On the pillar every
# pose keeps inside PERCH_BOX: row 30 is the screen's top edge there, and x 12..83 the top rope's doorway.
static var USE_FINAL_POSES := true
const CELL := Vector2(96, 96)
const ANCHOR := Vector2(48, 96)
const PERCH_BOX := Rect2(12, 30, 72, 66)
const PLACEHOLDER_CELL := Vector2(64, 64)
const PLACEHOLDER_ANCHOR := Vector2(32, 64)
# Each pose's sheet (DIR + "liam_<sheet>.png", one strip), its frames on it and their times. A talk pair is one sheet:
# frame 0 talking, frame 1 shut. The plan's frame counts are hard; the times are soft (the artist's, within 20%).
# An `all` pose plays every frame its sheet holds, however many that is (clip): a one-shot splits its `length` evenly
# across them, or plays the artist's own `times` when the sheet holds exactly that many (spread otherwise), and a loop
# steps at its `frame_time`. Only the poses whose code times a beat off their frames keep explicit frames. `cell` and
# `anchor` default to CELL and ANCHOR.
const ANIMS := {
	&"slimed_sit": {sheet = "slimed_sit", all = true, frame_time = 1.0},
	&"get_up": {sheet = "get_up", all = true, length = 0.5},
	&"wipe": {sheet = "wipe", all = true, frame_time = 0.2},
	&"talk_thanks": {sheet = "talk_thanks", frames = [0], times = [1.0], loop = true},
	&"talk_thanks_shut": {sheet = "talk_thanks", frames = [1], times = [1.0], loop = true},
	&"talk_explain": {sheet = "talk_explain", frames = [0], times = [1.0], loop = true},
	&"talk_explain_shut": {sheet = "talk_explain", frames = [1], times = [1.0], loop = true},
	&"talk_elements": {sheet = "talk_elements", frames = [0], times = [1.0], loop = true},
	&"talk_elements_shut": {sheet = "talk_elements", frames = [1], times = [1.0], loop = true},
	&"talk_smug": {sheet = "talk_smug", frames = [0], times = [1.0], loop = true},
	&"talk_smug_shut": {sheet = "talk_smug", frames = [1], times = [1.0], loop = true},
	&"talk_staff": {sheet = "talk_staff", frames = [0], times = [1.0], loop = true},
	&"talk_staff_shut": {sheet = "talk_staff", frames = [1], times = [1.0], loop = true},
	&"laugh": {sheet = "laugh", all = true, frame_time = 0.1},
	&"staff_pull": {sheet = "staff_pull", frames = [0, 1, 2, 3, 4], times = [0.3, 0.3, 0.3, 0.35, 0.35], loop = false},
	&"slam_rise": {sheet = "slam_rise", frames = [0, 1, 2], times = [0.15, 0.1, 0.75], loop = false},
	&"ride": {sheet = "ride", all = true, frame_time = 0.2},
	&"perch_idle": {sheet = "perch_idle", all = true, frame_time = 0.2},
	&"cast_left": {sheet = "cast_left", frames = [0, 1, 2], times = [0.15, 0.15, 0.15], loop = false},
	&"cast_right": {sheet = "cast_right", frames = [0, 1, 2], times = [0.15, 0.15, 0.15], loop = false},
	&"wobble": {sheet = "wobble", all = true, frame_time = 0.12},
	&"steady": {sheet = "steady", all = true, frame_time = 1.0},
	&"blast": {sheet = "blast", frames = [0, 1, 2], times = [0.15, 0.15, 0.3], loop = false},
	&"cold_breath": {sheet = "breathe", frames = [0, 1, 2, 1, 2, 1, 2, 1, 2, 3], times = [0.3, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.2], loop = false},
	# Its last frame cut to 0.1 s (addendum 4) so the pose fits the 0.45 s slam; the impact stays at 0.2 s.
	&"slam": {sheet = "slam", frames = [0, 1, 2, 3], times = [0.1, 0.1, 0.15, 0.1], loop = false},
	&"fall": {sheet = "fall", all = true, length = 0.6},
	&"downed": {sheet = "downed", all = true, frame_time = 0.3},
	&"downed_hit": {sheet = "downed_hit", all = true, length = 0.22},
	&"stand_up": {sheet = "get_up", all = true, length = 0.4},
	# The first four frames at the pace they always had (0.58 s); the last is held as a one-shot's last frame is.
	&"defeat": {sheet = "defeat", all = true, length = 0.725},
	# Attack 3 (addendum 3, E.3; approval_34/contract.json): the blow that raises the tornados (blow_time: two frames
	# of breathing in, the BLOW on BLOW_FRAME), the staff lighting them (ignite_time: the streaks leave its tip on
	# IGNITE_STREAK_FRAME), and the channel he holds while they burn.
	&"blow": {sheet = "blow", all = true, times = [0.15, 0.2, 0.12, 0.16, 0.14, 0.13]},
	&"ignite": {sheet = "ignite", all = true, length = 0.3},
	&"channel": {sheet = "channel", all = true, frame_time = 0.12},
	# Attack 4 (addendum 3, E.3; approval_34): into the steam off his stump (vanish_time), the lunge (lunge_show, drawn
	# facing right, his staff tip's reach on its last frame), carried past (a whiff), knocked down (a parry: its last
	# frame is downed's first), the player hoisted on his staff (impale, then the call to Bixby looping), the water
	# blast (the jet leaves the tip on BLAST_RELEASE_FRAME) and the teleport (teleport_time; teleport_in is it backward).
	&"vanish": {sheet = "vanish", all = true, times = [0.12, 0.14, 0.14, 0.14, 0.13, 0.13]},
	&"lunge": {sheet = "lunge", all = true, times = [0.03, 0.02, 0.02, 0.02, 0.03], cell = Vector2(144, 96)},
	&"lunge_whiff": {sheet = "lunge_whiff", all = true, times = [0.07, 0.08, 0.08, 0.07], cell = Vector2(144, 96)},
	&"parried": {sheet = "parried", all = true, times = [0.06, 0.08, 0.08, 0.08]},
	&"impale": {sheet = "impale", all = true, length = 0.4, cell = Vector2(96, 144), anchor = Vector2(48, 144)},
	&"impale_call": {sheet = "impale_call", all = true, frame_time = 0.15, cell = Vector2(96, 144), anchor = Vector2(48, 144)},
	&"water_blast": {sheet = "water_blast", all = true, times = [0.05, 0.05, 0.05, 0.075, 0.075], cell = Vector2(144, 96)},
	&"teleport": {sheet = "teleport", all = true, times = [0.06, 0.06, 0.06, 0.06, 0.06, 0.05]},
	&"teleport_in": {sheet = "teleport", all = true, times = [0.06, 0.06, 0.06, 0.06, 0.06, 0.05], reverse = true},
}

# On the stand-in (liam.png, one frame), each pose is his sprite moved in code instead: `rot` degrees, a `wave`
# oscillation of [degrees, hz], a `bob` of [texels, hz], a `squash` scale, and `lie` for flat on the mat.
const PLACEHOLDER_MOTION := {
	&"get_up": {squash = Vector2(1.08, 0.86)},
	&"wipe": {wave = [4.0, 3.0]},
	&"laugh": {bob = [2.0, 7.0], squash = Vector2(1.04, 0.97)},
	&"staff_pull": {rot = -8.0, bob = [1.0, 3.3]},
	&"slam_rise": {squash = Vector2(1.06, 0.92)},
	&"cast_left": {rot = -7.0},
	&"cast_right": {rot = 7.0},
	&"wobble": {wave = [8.0, 2.5]},
	&"blast": {squash = Vector2(1.1, 1.1)},
	&"cold_breath": {squash = Vector2(1.05, 0.95)},
	&"slam": {squash = Vector2(1.08, 0.9)},
	&"fall": {wave = [40.0, 1.5]},
	&"downed": {lie = true},
	&"downed_hit": {lie = true, bob = [1.0, 12.0]},
	&"defeat": {lie = true},
	&"blow": {squash = Vector2(1.06, 0.94), bob = [1.0, 4.0]},
	&"ignite": {rot = 9.0},
	&"channel": {wave = [5.0, 4.0]},
	&"vanish": {squash = Vector2(0.94, 1.06)},
	&"lunge": {rot = 14.0},
	&"lunge_whiff": {rot = 24.0},
	&"parried": {rot = -20.0},
	&"impale": {squash = Vector2(1.05, 0.95)},
	&"impale_call": {bob = [2.0, 6.0]},
	&"water_blast": {rot = -10.0},
	&"teleport": {squash = Vector2(0.9, 1.1)},
	&"teleport_in": {squash = Vector2(0.9, 1.1)},
}
# While a stand-in talk pose is typing, his whole body squashes as Greyson's does.
const TALK_SQUASH := Vector2(1.013, 0.987)
const TALK_SQUASH_TIME := 0.12

# Points on his poses, texels on a final cell (the full sheets' anchors.json): the staff tip's orb, the mouth (his cold
# breath), the staff butt (the summoning slam on the ground, the tremor slam on the pillar), the dazed head top and the
# daze point. POINTS is one a pose, the frame the code reads it on (the blast's release, the breath's blow, each slam's
# impact); FRAME_POINTS is where a sheet frame of it differs. A pose without its own takes the key's first.
const POINTS := {
	&"staff_tip": {&"perch_idle": Vector2(21, 41), &"cast_left": Vector2(22.5, 41), &"cast_right": Vector2(22.5, 41), &"blast": Vector2(74, 70),
		&"ignite": Vector2(21.5, 63.5), &"channel": Vector2(22.5, 40), &"lunge": Vector2(95, 77), &"impale": Vector2(95, 125),
		&"impale_call": Vector2(71.5, 59.5), &"water_blast": Vector2(77.67, 24.74)},
	&"mouth": {&"cold_breath": Vector2(43.5, 55), &"blow": Vector2(43.5, 56)},
	&"staff_butt": {&"slam_rise": Vector2(18.5, 95), &"slam": Vector2(65, 95)},
	&"head_top": {&"downed": Vector2(48, 44)},
	&"daze": {&"downed": Vector2(47, 36)},
}
const FRAME_POINTS := {
	&"staff_tip": {&"cast_left": {1: Vector2(20.5, 39), 2: Vector2(21, 40)}, &"blast": {0: Vector2(70, 68)},
		&"ride": {0: Vector2(21, 41), 1: Vector2(21, 40)}, &"slam_rise": {2: Vector2(21, 42)},
		&"ignite": {0: Vector2(22.5, 40), 1: Vector2(22.5, 39), 3: Vector2(23, 62.5), 4: Vector2(23, 62.5)},
		&"channel": {2: Vector2(22.5, 39), 3: Vector2(22.5, 39)},
		&"lunge": {0: Vector2(67.5, 80), 1: Vector2(81.5, 79), 2: Vector2(89.5, 78), 3: Vector2(93.5, 77)},
		&"impale": {1: Vector2(83.7, 77.16), 2: Vector2(61.65, 63.96), 3: Vector2(71.5, 59.5)}},
	&"mouth": {&"cold_breath": {0: Vector2(43.5, 54), 2: Vector2(43.5, 56)},
		&"blow": {0: Vector2(43.5, 54), 1: Vector2(43.5, 52), 4: Vector2(43.5, 55), 5: Vector2(43.5, 55)}},
	&"staff_butt": {&"slam_rise": {0: Vector2(19, 83), 2: Vector2(20.5, 94.5)},
		&"slam": {0: Vector2(65, 87), 1: Vector2(65, 82), 3: Vector2(65, 93)}},
	&"head_top": {&"downed": {1: Vector2(49, 44)}},
	&"daze": {&"downed": {1: Vector2(48, 36)}},
}
# The same on the stand-in, liam.png's own texels; lying on his back, his daze is over his middle.
const PLACEHOLDER_POINTS := {
	&"staff_tip": Vector2(52, 4),
	&"mouth": Vector2(32, 27),
	&"staff_butt": Vector2(46, 63),
	&"head_top": Vector2(32, 1),
	&"daze": Vector2(32, 24),
}
# The frames the firestorm's beats go off on: the gust off his mouth and the tornados on the blow's BLOW, the fire
# streaks off his staff tip on the ignite's thrust. On the stand-in (one frame) both go off as the pose starts.
const BLOW_FRAME := 2
const IGNITE_STREAK_FRAME := 2
# The water blast's release: the jet leaves his staff tip as it comes up (its start, BLAST_RELEASE_TIME, on the stand-in).
const BLAST_RELEASE_FRAME := 3
const BLAST_RELEASE_TIME := 0.15
# The daze stars and a badge stand this far over his head top, standing.
const DAZE_GAP := 34.0
# His hurtbox off his feet, px: standing, and down on the mat in his punish window (the pass's dazed sit, 88 across).
const BODY_BOXES := {&"standing": Rect2(-48, -180, 96, 180), &"downed": Rect2(-120, -150, 240, 150)}
# His head top off his feet standing, px: liam.png's row 1 of 64, the rig's row 33 of 96.
const HEAD_TOP := Vector2(0, -186)
# The stand-in lying flat: turned onto his back, his middle over his feet.
const PLACEHOLDER_LIE := {rotation = -90.0, shift = Vector2(93, -45)}
# The poses he lies in.
const LYING := [&"downed", &"downed_hit", &"defeat"]

#THE HAND-OVER (bixby_beast_defeat.png frame 9: normal Bixby and the slimy Liam he coughed up, side by side)
# Measured by the artist: the lowest texel row under each figure, Bixby's ANCHOR (96, 151) convention. liam_slimed_sit
# is frame 9 itself: a frame-9 texel is a slimed_sit texel plus SLIMED_SIT_OFFSET, so his cell's anchor point (48, 96)
# is frame 9's continuous point (157, 154) and the swap can't move a pixel (checked with imgdiff.py).
const DEFEAT_FRAME := 9
const DEFEAT_LIAM_FEET := Vector2(157, 153)
const DEFEAT_BIXBY_FEET := Vector2(88, 152)
const SLIMED_SIT_OFFSET := Vector2(109, 58)
# Until slimed_sit ships, he and the dog are that frame itself, cut in two where they don't touch.
const DEFEAT_LIAM_REGION := Rect2(126, 60, 66, 100)
const DEFEAT_BIXBY_REGION := Rect2(56, 60, 70, 100)
# The dog's hop out of the ring on bixby.png: seconds, the arc's rise over its chord, and how far past the screen's
# nearer side it lands.
const BIXBY_SPRITE := "res://Assets/Characters/Bixby/bixby.png"
const BIXBY_HOP := {time = 0.7, arc = 220.0, off_screen = 140.0}

#THE EARTH PILLAR (LiamPillar)
# liam_pillar.png: 64x80 cells, anchored on the floor line's centre (32, 72); he stands on (32, 22), exactly 50 texels
# up. A 36-texel column (x 14..49) under a 16-row top slab (rows 14..30), 48 drawn across. Rise 0-4 (4 is stand 0's
# picture), stand 5-10 (hits 0 to 5: frame 5 + h has 6 - h runes lit, the top going dark first), crumble 11-16.
# liam_pillar_shield.png (4, looping) and liam_pillar_dust.png (3) share the cell and the anchor. Its solid footprint is
# x -18..+18, y -16..0 texels: Rect2(906, 300, 108, 48) at the perch.
static var USE_FINAL_PILLAR := true
const STAND_TEXELS := 50
const STAND_HEIGHT := STAND_TEXELS * SCALE
const PILLAR_FOOTPRINT := Rect2(-54, -48, 108, 48)
# The pillar's hurtbox off its anchor: Rect2(900, 190, 120, 182) at the perch. It reaches 24 px under the floor line,
# so an up-punch lands from the front spot and anywhere up to the row's face (addendum 3, A.2).
const PILLAR_HURTBOX := Rect2(-60, -158, 120, 182)
const PILLAR_SHEET := DIR + "liam_pillar.png"
const PILLAR_SHIELD_SHEET := DIR + "liam_pillar_shield.png"
const PILLAR_DUST_SHEET := DIR + "liam_pillar_dust.png"
const PILLAR_FRAME := Vector2(64, 80)
const PILLAR_PIVOT := Vector2(32, 72)
const PILLAR_RISE_FRAMES := [0, 1, 2, 3, 4]
const PILLAR_STAND_FIRST := 5
const PILLAR_CRUMBLE_FRAMES := [11, 12, 13, 14, 15, 16]
const PILLAR_SHIELD_FRAME_TIME := 0.1
const PILLAR_DUST_FRAME_TIME := 0.065
# The stand-in: a stone column 36 texels wide from the floor line to the standing surface under a 16-row slab, six
# runes up its face going dark from the top a hit, and a crack a hit; the shield a rune ring round it.
const PLACEHOLDER_PILLAR := {
	width = 36.0, cap_width = 48.0, cap_height = 16.0,
	stone = Color("#6E6259"), stone_dark = Color("#4A4039"), edge = Color("#2B2420"), cap = Color("#8A7D71"),
	rune = Color("#7FE3FF"), rune_dark = Color("#33302C"), crack = Color("#1C1714"),
	shield = Color(0.55, 0.9, 1.0, 0.35), shield_edge = Color(0.75, 0.97, 1.0, 0.85),
	dust = Color(0.62, 0.55, 0.48, 0.8), shadow = Color(0.0, 0.0, 0.0, 0.3),
}
# The runes up the face (the pass's rows 35..65, off the anchor's row 72), top first: the hit that darkens each.
const PLACEHOLDER_RUNES := [Vector2(0, -37), Vector2(0, -31), Vector2(0, -25), Vector2(0, -19), Vector2(0, -13), Vector2(0, -7)]
# Its cracks, one a hit, texels off the anchor.
const PLACEHOLDER_CRACKS := [
	[Vector2(-18, -12), Vector2(-11, -16), Vector2(-13, -22)],
	[Vector2(18, -30), Vector2(10, -26), Vector2(12, -19)],
	[Vector2(-4, -34), Vector2(1, -28), Vector2(-3, -22)],
	[Vector2(-18, -40), Vector2(-9, -37), Vector2(-5, -29), Vector2(-11, -24)],
	[Vector2(18, -8), Vector2(9, -5), Vector2(4, -12), Vector2(7, -20)],
	[Vector2(-2, 0), Vector2(3, -9), Vector2(-3, -18), Vector2(2, -27)],
]

#THE ROW (LiamRow, addendum 3 A.1): his wall of pillars across the top of the ring
# ROW_PER_SIDE neighbours each side of his own pillar, ROW_SPACING apart on his floor line, ROW_STAND_TEXELS tall (his
# own is STAND_TEXELS), and one solid band over the whole width. liam_row_pillar_rise / _stand / _crumble: 64x80 cells on
# PILLAR_PIVOT, one row a variant (approval_34: 3 variants; rise 5, stand 1, crumble 6); frame counts off each sheet. A
# rise plays over each pillar's share of the ripple and a crumble over its time, frame to frame in the artist's
# proportions (ROW_RISE_TIMES, ROW_CRUMBLE_TIMES). Until they ship, the pillar's stand-in column, without runes.
static var USE_FINAL_ROW := true
const ROW_Y := 348.0
const ROW_BAND := Rect2(105, 300, 1710, 48)
const ROW_SPACING := 108.0
const ROW_PER_SIDE := 8
const ROW_STAND_TEXELS := 34
# A player standing in the band or behind it is put with their box's top this far under it as it rises.
const ROW_NUDGE_GAP := 2.0
const ROW_CRUMBLE_RIPPLE := 0.03
const ROW_RISE_SHEET := DIR + "liam_row_pillar_rise.png"
const ROW_STAND_SHEET := DIR + "liam_row_pillar_stand.png"
const ROW_CRUMBLE_SHEET := DIR + "liam_row_pillar_crumble.png"
const ROW_FRAME := Vector2(64, 80)
const ROW_RISE_TIMES := [0.06, 0.06, 0.07, 0.07, 0.08]
const ROW_STAND_FRAME_TIME := 0.2
const ROW_CRUMBLE_TIMES := [0.05, 0.06, 0.07, 0.08, 0.1, 0.14]

#THE WAVES (LiamWave, attack 1)
# The hit bands are section 5's gameplay: 861 px (287 texels) each, overlapping 12 px at the seam. The pass drew the wave
# 282 across as liam_wave_body (94x80) under liam_wave_crest (94x40, a 3-frame loop), three tiles each, and liam_wave.png
# is exactly that; so it is laid here from those two tiles out to the band's full 287: whole tiles from the seam end, the
# 5-texel remainder (a tile's last five columns, so it runs on into the next) at the rope end, where the corner post is.
# Drawn as the left wave, mirrored for the right. liam_wave_tell (282x24, 3) stands on the rope line and
# liam_wave_collapse (282x120, 3) on the band, both flush with the seam end; the splash (32x32, 4) on its pivot.
# fx_v2 (approved 2026-09-29, art_source/liam_elements/fx_v2/contract.json) redrew them all with more frames, counted off
# each sheet (the crest 12, its body 12, which steps with the crest's frame: the shimmer); these are its times.
static var USE_FINAL_WAVE := true
const WAVE_BODY_SHEET := DIR + "liam_wave_body.png"
const WAVE_CREST_SHEET := DIR + "liam_wave_crest.png"
const WAVE_TELL_SHEET := DIR + "liam_wave_tell.png"
const WAVE_COLLAPSE_SHEET := DIR + "liam_wave_collapse.png"
const WAVE_SPLASH_SHEET := DIR + "liam_wave_splash.png"
const WAVE_TILE := Vector2(94, 120)
const WAVE_BODY_ROWS := 80
const WAVE_CREST_FRAMES := 3
const WAVE_FRAME_TIME := 0.06
const WAVE_TELL_FRAME := Vector2(282, 24)
const WAVE_COLLAPSE_FRAME := Vector2(282, 120)
const WAVE_ART_FRAMES := 3
const WAVE_SPLASH_FRAME := Vector2(32, 32)
const WAVE_SPLASH_PIVOT := Vector2(16, 20)
const WAVE_SPLASH_TIMES := [0.03, 0.03, 0.04, 0.04, 0.04, 0.04, 0.04]
# The two bands across (px): left and right, overlapping 12 px at the seam.
const WAVE_LEFT_X := Vector2(105, 966)
const WAVE_RIGHT_X := Vector2(954, 1815)
# Each wave hurts only this far short of its seam end: x 105..948 and 972..1815. The 24 px strip between is narrower
# than the player's 36, so no path runs straight up through it, and the corner zip's lane is 36 px wider.
const WAVE_SEAM_INSET := 18.0
# The line down the middle a zip crosses from one wave's half into the other's.
const SEAM_X := 960.0
# The red badge's tip, outside the HUD block, over each half.
const WAVE_BADGE := {&"left": Vector2(536, 135), &"right": Vector2(1383, 135)}
const PLACEHOLDER_WAVE := {
	body = Color(0.16, 0.42, 0.74, 0.88), crest = Color(0.86, 0.95, 1.0, 0.95),
	crest_depth = 18.0, foam = Color(1.0, 1.0, 1.0, 0.8), foam_size = 8.0, foam_spacing = 64.0,
	tell = Color(0.55, 0.85, 1.0, 0.9), tell_height = 22.0,
	splash = Color(0.8, 0.95, 1.0, 0.9), splash_radius = 40.0,
}

#THE GUST (LiamGust: the round's air blast)
# A burst on his staff tip (48x48, 4, pivot 24,24, opening down at the player) and a trail on the launched player's feet
# (24x32, 3, pivot 12,31).
static var USE_FINAL_GUST := true
const GUST_BURST_SHEET := DIR + "liam_gust_burst.png"
const GUST_TRAIL_SHEET := DIR + "liam_gust_trail.png"
const GUST_BURST_FRAME := Vector2(48, 48)
const GUST_BURST_PIVOT := Vector2(24, 24)
const GUST_BURST_TIMES := [0.03, 0.03, 0.04, 0.04, 0.04, 0.05, 0.06]
const GUST_TRAIL_FRAME := Vector2(24, 32)
const GUST_TRAIL_PIVOT := Vector2(12, 31)
const GUST_TRAIL_FRAME_TIME := 0.05
const PLACEHOLDER_GUST := {
	burst = Color(0.85, 0.97, 1.0, 0.85), ring = Color(1.0, 1.0, 1.0, 0.9), radius = 72.0, spokes = 10,
	trail = Color(0.9, 0.98, 1.0, 0.7), trail_lines = 3, trail_length = 90.0,
}

#THE FLOOD AND THE ICE (LiamFlood, attack 2)
# Over the ring inside the ropes. liam_flood.png: a seamless 64x64 tile, 6 nested coverage frames (every wet texel in
# frame k is wet in k+1, puddles to a full sheet), semi-transparent, never flipped. liam_ice.png the same tile, 2 frames
# (the second a glint); liam_ice_melt.png 3 (ice, slush, water frame 5); liam_ice_shatter.png 4.
# liam_freeze_front.png: a 16x16 frost rim on its centre, 3 frames, stamped every FROST_SPACING px round the front.
# fx_v2 added liam_flood_ripple.png (64x64, 12 frames at FLOOD_RIPPLE_FRAME_TIME), tiled over the water inside its shape.
static var USE_FINAL_FLOOD := true
const FLOOD_RECT := Rect2(113, 114, 1692, 855)
const FLOOD_SHEET := DIR + "liam_flood.png"
const ICE_SHEET := DIR + "liam_ice.png"
const ICE_MELT_SHEET := DIR + "liam_ice_melt.png"
const ICE_SHATTER_SHEET := DIR + "liam_ice_shatter.png"
const FROST_SHEET := DIR + "liam_freeze_front.png"
const FLOOD_TILE := Vector2(64, 64)
const FLOOD_FRAMES := 6
const ICE_GLINT_TIME := 0.8
const MELT_FRAMES := 3
const SHATTER_FRAMES := 4
const FROST_FRAME := Vector2(16, 16)
const FROST_FRAME_TIME := 0.08
const FROST_SPACING := 48.0
const SHATTER_TIME := 0.4
const FLOOD_RIPPLE_SHEET := DIR + "liam_flood_ripple.png"
const FLOOD_RIPPLE_FRAME_TIME := 0.1
const PLACEHOLDER_FLOOD := {
	water = Color(0.22, 0.5, 0.82, 0.34), puddles = Vector2i(9, 5), puddle_radius = Vector2(88.0, 50.0), jitter = 46.0,
	ice = Color(0.78, 0.93, 1.0, 0.62), ice_line = Color(1.0, 1.0, 1.0, 0.55), ice_lines = 14,
	frost = Color(0.95, 1.0, 1.0, 0.95), frost_size = 9.0, slush = Color(0.6, 0.8, 0.95, 0.45),
}

#THE TREMOR RIDGES (LiamTremorBlock) AND THEIR CRACKS
# liam_tremor_block.png: 96x32 frames, the footprint texel rows 8..31 (96x24, the collision rect exactly), rows 0..7
# only rock jutting up; 17 frames: tell 0-3 (0.15 each, the 0.6 s tell), heave 4-6, the active loop 7-10, the pulse on
# each slam 11-12, the crumble 13-16 then a fade. It may be flipped; its ends overlap the next block's by 16 texels.
# liam_tremor_crack.png: a 16x8 segment, 3 frames, pivot (0, 4) on its left-centre, laid end to end from the pillar.
static var USE_FINAL_TREMOR := true
const TREMOR_SHEET := DIR + "liam_tremor_block.png"
const TREMOR_CRACK_SHEET := DIR + "liam_tremor_crack.png"
const TREMOR_FRAME := Vector2(96, 32)
const TREMOR_FOOTPRINT_TOP := 8
const TREMOR_CLIPS := {
	&"tell": {frames = [0, 1, 2, 3], times = [0.15, 0.15, 0.15, 0.15], loop = false},
	&"heave": {frames = [4, 5, 6], times = [0.06, 0.08, 0.10], loop = false},
	&"active": {frames = [7, 8, 9, 10], times = [0.12, 0.12, 0.12, 0.12], loop = true},
	&"pulse": {frames = [11, 12], times = [0.06, 0.10], loop = false},
	&"crumble": {frames = [13, 14, 15, 16], times = [0.08, 0.08, 0.08, 0.08], loop = false},
}
# fx_v2's own strips per clip (liam_tremor_block_<clip>.png), their times when a strip has exactly this many frames;
# spread over its length (a loop at its frame time) when it doesn't.
const TREMOR_STRIP_TIMES := {
	&"tell": [0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
	&"heave": [0.04, 0.04, 0.04, 0.04, 0.04, 0.04],
	&"active": [0.12, 0.12, 0.12, 0.12, 0.12, 0.12],
	&"pulse": [0.04, 0.04, 0.04, 0.04],
	&"crumble": [0.05, 0.05, 0.05, 0.05, 0.06, 0.06],
}
const TREMOR_CRACK_FRAME := Vector2(16, 8)
const TREMOR_CRACK_PIVOT := Vector2(0, 4)
const TREMOR_CRACK_FRAME_TIME := 0.06
const CRUMBLE_TIME := 0.35
# The pass's tell: earth green with a white core, never the red parry badge or the yellow dodge ring.
const PLACEHOLDER_TREMOR := {
	glow = Color(0.5, 0.83, 0.35, 0.5), glow_edge = Color(0.95, 1.0, 0.9, 0.95),
	rock = Color("#5E6F7C"), rock_top = Color("#8FA7B5"), edge = Color("#1E2A33"), edge_width = 4.0,
	jut = 18.0, pulse = Color(1.6, 1.8, 2.0, 1.0),
	crack = Color("#7FD35A"), crack_core = Color(1.0, 1.0, 1.0, 0.9), crack_width = 5.0,
}

#HIS COLD BREATH AND HIS SLAM
# liam_cold_breath.png: 40x100, pivot (20, 2) on the mouth point, the plume down 97 texels to the pillar's base: a start
# frame, a loop, and an end frame played as it stops (fx_v2: 8, 0 / 1-6 / 7). liam_slam_burst.png: 32x16, pivot (16, 15)
# on the staff butt.
static var USE_FINAL_BREATH := true
const BREATH_SHEET := DIR + "liam_cold_breath.png"
const BREATH_FRAME := Vector2(40, 100)
const BREATH_PIVOT := Vector2(20, 2)
const BREATH_FRAME_TIME := 0.06
const SLAM_BURST_SHEET := DIR + "liam_slam_burst.png"
const SLAM_BURST_FRAME := Vector2(32, 16)
const SLAM_BURST_PIVOT := Vector2(16, 15)
const SLAM_BURST_TIMES := [0.03, 0.03, 0.04, 0.04, 0.04, 0.04]
const PLACEHOLDER_BREATH := {color = Color(0.85, 0.97, 1.0, 0.55), edge = Color(1.0, 1.0, 1.0, 0.7), width = 90.0}
const PLACEHOLDER_SLAM := {color = Color(0.9, 0.85, 0.7, 0.9), radius = 48.0, spikes = 7}

#THE DOWNDRAFT (LiamElementFx.downdraft: what his cold breath's blow down the ring looks like, while it blows)
# A streak every DOWNDRAFT_SPAWN_TIME at a random x on his floor line, falling at DOWNDRAFT_SPEED_SCALE times the drift:
# full for the first DOWNDRAFT_SOLID of its fall, then fading out by the time its head reaches the bottom rope (fx_v2's
# suggestion), and never past DOWNDRAFT_LIFE. liam_downdraft.png's frame, pivot and time are fx_v2's; it loops in place
# from a random frame, its count off the sheet.
static var USE_FINAL_DOWNDRAFT := true
const DOWNDRAFT_SHEET := DIR + "liam_downdraft.png"
const DOWNDRAFT_FRAME := Vector2(20, 80)
const DOWNDRAFT_PIVOT := Vector2(10, 0)
const DOWNDRAFT_FRAME_TIME := 0.04
const DOWNDRAFT_SPAWN_TIME := 0.03
const DOWNDRAFT_SPEED_SCALE := 1.5
const DOWNDRAFT_LIFE := 0.35
const DOWNDRAFT_SOLID := 0.35
# The bottom rope's line, where a streak's head is gone by.
const DOWNDRAFT_BOTTOM := 969.0
# Where the streaks start: across the ring on his floor line.
const DOWNDRAFT_X := Vector2(113, 1805)
const DOWNDRAFT_Y := 348.0
const PLACEHOLDER_DOWNDRAFT := {color = Color(0.9, 0.97, 1.0, 0.55), length = 70.0, width = 3.0}

#THE FIRESTORM (attack 3, addendum 3 B and E.4; the approved art's numbers are approval_34/contract.json's): the
# tornados, the streaks that light them and his blow's gust, the fire rings, the melt. The tornado sheets are 48x112 on
# (24, 108), the base on the floor, the base ring on rows 100-111 x 8-40 (TORNADO_CORE's 96 px); frame counts come off
# the sheets. Fire keeps warm, bright cores (R - B at least 0.4, value at least 0.6) so the steam's glow-through
# catches it. Stand-ins are drawn in code until the art ships.
static var USE_FINAL_FIRESTORM := true
const TORNADO_SHEETS := {
	&"spin": DIR + "liam_tornado_spin.png",
	&"ignite": DIR + "liam_tornado_ignite.png",
	&"fire": DIR + "liam_tornado_fire.png",
	&"out": DIR + "liam_tornado_out.png",
}
const TORNADO_FRAME := Vector2(48, 112)
const TORNADO_PIVOT := Vector2(24, 108)
const TORNADO_LOOP_TIME := 0.06
const TORNADO_IGNITE_TIME := 0.3
const TORNADO_FADE_IN := 0.4
# The artist's two extras, each on its own switch: the funnel forming out of a whirl of spray over TORNADO_FADE_IN in
# place of the fade-in, and a spew played instead of the fire loop as each ring leaves, the ring going out on its
# TORNADO_SPEW_RING_FRAME.
static var USE_TORNADO_FORM := true
static var USE_TORNADO_SPEW := true
const TORNADO_FORM_SHEET := DIR + "liam_tornado_form.png"
const TORNADO_SPEW_SHEET := DIR + "liam_tornado_spew.png"
const TORNADO_SPEW_TIMES := [0.08, 0.08, 0.08, 0.08, 0.08]
const TORNADO_SPEW_RING_FRAME := 1
const FIRE_STREAK_SHEET := DIR + "liam_fire_streak.png"
const FIRE_STREAK_FRAME := Vector2(24, 12)
const FIRE_STREAK_PIVOT := Vector2(20, 6)
const FIRE_STREAK_FRAME_TIME := 0.05
const BLOW_GUST_SHEET := DIR + "liam_blow_gust.png"
const BLOW_GUST_FRAME := Vector2(64, 48)
const BLOW_GUST_PIVOT := Vector2(32, 4)
const BLOW_GUST_TIME := 0.5
# The wind streaks the tornados draw in, in BixbyInfernoArtLayout.FINAL_SUCTION's format (rows at 0, 45 and 90 degrees).
const WIND_STREAK := {"sheet": DIR + "liam_wind_streak.png", "frame_size": Vector2(24, 24), "frames": 4, "frame_time": 0.05}
# His own fire rings on Bixby's ring layout (40x32 on its centre, FIRE_QUAKE_RING_ROWS by tangent and as many again
# dying, frames across at Bixby's RING_FRAME_TIME), the user's pick over Bixby's hellfire ring as-is, which is what
# plays with the switch off or until the sheet is in.
static var USE_OWN_RING_ART := true
const FIRE_QUAKE_RING_SHEET := DIR + "liam_fire_quake_ring.png"
const FIRE_QUAKE_RING_FRAME := Vector2(40, 32)
const FIRE_QUAKE_RING_ROWS := 7
const MELT_RIM_SHEET := DIR + "liam_melt_rim.png"
const MELT_RIM_FRAME := Vector2(16, 16)
const MELT_RIM_FRAME_TIME := 0.1
const PLACEHOLDER_TORNADO := {
	height = 330.0, base_half = 40.0, top_half = 96.0,
	spin = Color(0.85, 0.95, 1.0, 0.55), spin_edge = Color(1.0, 1.0, 1.0, 0.8),
	fire = Color(1.0, 0.5, 0.08, 0.85), fire_core = Color(1.0, 0.85, 0.3, 0.95), fire_edge = Color(1.0, 0.25, 0.05, 0.95),
	core = Color(1.0, 0.7, 0.2, 0.6),
}
const PLACEHOLDER_FIRE_STREAK := {color = Color(1.0, 0.6, 0.1, 0.95), length = 44.0, width = 7.0}
const PLACEHOLDER_BLOW_GUST := {color = Color(0.9, 0.97, 1.0, 0.8), radius = 60.0, spokes = 8}
const PLACEHOLDER_MELT_RIM := {color = Color(0.6, 0.8, 0.95, 0.7), size = 8.0}

#THE STEAM (LiamSteam: over the fighters and the ropes, under his FxLayer, the parry badge and the HUD)
# liam_steam_tile.png: a seamless 128x128 tile, frame 0 the shader's first layer and frame 1 its second, white steam
# whose alpha is its thickness; liam_steam_wisp.png 16x32 on (8, 31), its frames over STEAM_WISP_TIME. Until they ship,
# value noise in the shader and pale ellipses.
static var USE_FINAL_STEAM := true
const STEAM_Z := 2
const STEAM_RECT := Rect2(-240, -240, 2400, 1560)
const STEAM_TILE_SHEET := DIR + "liam_steam_tile.png"
const STEAM_TILE_TEXELS := 128.0
const STEAM_WISP_SHEET := DIR + "liam_steam_wisp.png"
const STEAM_WISP_FRAME := Vector2(16, 32)
const STEAM_WISP_PIVOT := Vector2(8, 31)
const STEAM_WISP_TIME := 0.8
const STEAM_BUBBLE := 150.0
const STEAM_FEATHER := 70.0
const STEAM_COLOUR := Color(0.9, 0.93, 0.96)
# The two layers' drift, px a second, on the steam's own clock.
const STEAM_DRIFT := [Vector2(16, -7), Vector2(-11, -5)]
const STEAM_WISPS_PER_SECOND := 6.0
const STEAM_WISP_NEAR := 300.0
const STEAM_WISP_NEAR_SHARE := 0.6
const PLACEHOLDER_WISP := {color = Color(0.95, 0.97, 1.0, 0.5), radii = Vector2(10, 18), rise = 60.0}

#THE LUNGE (attack 4, addendum 3 C and E.4; approval_34/contract.json's numbers)
# Its tell is the game's red parry badge (the user's question 1). The steam puff (48x48 on his feet: his vanish, a whiff,
# the teleports, backward for an arrival), the wake behind a lunge (48x24 facing right on his back), Bixby's fire from
# above (a 32x48 column tile stacked up from the impaled player's head, and its splash there), the flames and then the
# embers on the player (24x32 on their feet), the extinguish when the water hits them, the water jet (a 16x16 body tile
# laid from his staff tip to the player) and the water trail on the washed-down player. Frame counts off the sheets;
# the one-shots keep their time. Until they ship, shapes drawn in code.
static var USE_FINAL_LUNGE := true
const STEAM_PUFF := {sheet = DIR + "liam_steam_puff.png", frame = Vector2(48, 48), pivot = Vector2(24, 44), time = 0.35}
const LUNGE_WAKE := {sheet = DIR + "liam_lunge_wake.png", frame = Vector2(48, 24), pivot = Vector2(47, 12), time = 0.15}
# The sky fire is his own column (the user's pick); with USE_OWN_SKY_FIRE off, Bixby's flyby curtain stacked the same way.
static var USE_OWN_SKY_FIRE := true
const SKY_FIRE := {sheet = DIR + "liam_sky_fire.png", frame = Vector2(32, 48), pivot = Vector2(16, 0), frame_time = 0.06}
const SKY_FIRE_CURTAIN := {sheet = "res://Assets/Characters/Bixby/bixby_flyby_curtain.png", frame = Vector2(32, 48), pivot = Vector2(16, 0), frame_time = 0.06}
const SKY_FIRE_SPLASH := {sheet = DIR + "liam_sky_fire_splash.png", frame = Vector2(48, 32), pivot = Vector2(24, 28), frame_time = 0.06}
# Where the column starts: over the top of the screen, so a shake never shows its end.
const SKY_FIRE_TOP := -60.0
const PLAYER_FLAMES := {sheet = DIR + "liam_player_flames.png", frame = Vector2(24, 32), pivot = Vector2(12, 30), frame_time = 0.06}
const PLAYER_EMBERS := {sheet = DIR + "liam_player_embers.png", frame = Vector2(24, 32), pivot = Vector2(12, 30), frame_time = 0.08}
const EXTINGUISH := {sheet = DIR + "liam_extinguish.png", frame = Vector2(48, 48), pivot = Vector2(24, 40), time = 0.5}
const WATER_JET := {sheet = DIR + "liam_water_jet.png", frame = Vector2(16, 16), pivot = Vector2(0, 8), frame_time = 0.05}
const WATER_TRAIL := {sheet = DIR + "liam_water_trail.png", frame = Vector2(24, 32), pivot = Vector2(12, 31), frame_time = 0.07}
const PLACEHOLDER_PUFF := {color = Color(0.95, 0.97, 1.0, 0.75), radii = Vector2(44, 26)}
const PLACEHOLDER_WAKE := {color = Color(0.95, 0.97, 1.0, 0.6), length = 130.0, width = 6.0, lines = 3}
const PLACEHOLDER_SKY_FIRE := {edge = Color(1.0, 0.45, 0.08, 0.85), core = Color(1.0, 0.9, 0.5, 0.95), width = 72.0,
	core_width = 28.0, splash = Vector2(60, 26)}
const PLACEHOLDER_FLAMES := {flame = Color(1.0, 0.55, 0.1, 0.75), ember = Color(0.9, 0.3, 0.1, 0.6), radii = Vector2(30, 52)}
const PLACEHOLDER_EXTINGUISH := {color = Color(0.92, 0.96, 1.0, 0.85), radius = 64.0}
const PLACEHOLDER_JET := {color = Color(0.45, 0.75, 1.0, 0.9), core = Color(0.92, 0.98, 1.0, 0.95), width = 26.0}
const PLACEHOLDER_WATER_TRAIL := {color = Color(0.55, 0.82, 1.0, 0.75), lines = 3, length = 70.0}

#HIS SHADOW (on the mat while he's on the ground)
# liam_shadow.png: one 64x16 frame, a solid black ellipse on its centre; the code sets its alpha, as with Mason's.
static var USE_FINAL_SHADOW := true
const SHADOW_SHEET := DIR + "liam_shadow.png"
const SHADOW_ALPHA := 0.32
const PLACEHOLDER_SHADOW := {color = Color(0.0, 0.0, 0.0, 0.32), radii = Vector2(46, 12)}

#THE JUGGLE (the Break's tiered uppercut; BossJuggled reads exactly this shape)
# liam_juggle.png: 12 frames of 128x96, the BossJuggled clip table (launch 0-1, tumble 2-6 looping, crash 7-9, down
# 10-11), his feet on (64, 95) and the sheet on Mason's (0, -48); liam_leap_shadow.png 3 frames of 64x16, solid black,
# its alpha the code's. Until it ships, liam.png stands in.
static var USE_FINAL_JUGGLE := true
const FINAL_JUGGLE := {
	"texture": DIR + "liam_juggle.png",
	"hframes": 12,
	"frame_size": Vector2(128, 96),
	"offset": Vector2(0, -48),
	"feet": Vector2(64, 95),
	"tumble_centre": Vector2(64, 50),
	"top_row": 10,
	"clips": {
		&"launch": {"frames": [0, 1], "times": [0.06, 0.08], "loop": false},
		&"tumble": {"frames": [2, 3, 4, 5, 6], "times": [0.14, 0.08, 0.08, 0.08, 0.08], "loop": true},
		&"crash": {"frames": [7, 8, 9], "times": [0.07, 0.09, 0.14], "loop": false},
		&"down": {"frames": [10, 11], "times": [0.4, 0.4], "loop": true},
	},
	"shadow": {
		"texture": DIR + "liam_leap_shadow.png",
		"hframes": 3, "scale": 3.0, "alpha": 0.35, "step": 100.0, "offset": Vector2.ZERO,
	},
	"lying_time": 0.3,
	"outro_delay": 1.8,
	"crash_sfx": {"stream": "res://Assets/Audio/SFX/earthquake_slam.ogg", "pitch": 1.0, "volume_db": 0.0},
}
const PLACEHOLDER_JUGGLE := {
	"texture": LIAM_SPRITE,
	"hframes": 1,
	"frame_size": Vector2(64, 64),
	"offset": Vector2(0, -32),
	"feet": Vector2(32, 63),
	"tumble_centre": Vector2(32, 32),
	"top_row": 1,
	"clips": {
		&"launch": {"frames": [0], "times": [0.14], "loop": false},
		&"tumble": {"frames": [0], "times": [0.2], "loop": true},
		&"crash": {"frames": [0], "times": [0.26], "loop": false},
		&"down": {"frames": [0], "times": [0.4], "loop": true},
	},
	"shadow": {
		"texture": "res://Assets/Characters/Mason/mason_leap_shadow.png",
		"hframes": 3, "scale": 3.0, "alpha": 0.35, "step": 100.0, "offset": Vector2.ZERO,
	},
	"lying_time": 0.3,
	"outro_delay": 1.8,
	"crash_sfx": {"stream": "res://Assets/Audio/SFX/earthquake_slam.ogg", "pitch": 1.0, "volume_db": 0.0},
}

#SOUNDS (stand-ins off the shared set until he has his own)
const SFX := {
	&"laugh": {stream = "res://Assets/Audio/SFX/burak_laugh.wav", pitch = 1.2, volume_db = 0.0},
	&"pillar_rise": {stream = "res://Assets/Audio/SFX/greyson_eruption_rumble.wav", pitch = 1.0, volume_db = 0.0},
	&"pillar_hit": {stream = "res://Assets/Audio/SFX/hit_impact.ogg", pitch = 0.7, volume_db = 0.0},
	&"crumble": {stream = "res://Assets/Audio/SFX/greyson_barbell_slam.wav", pitch = 1.0, volume_db = 0.0},
	&"wave": {stream = "res://Assets/Audio/SFX/whirlwind_whoosh.ogg", pitch = 0.6, volume_db = -4.0},
	&"gust": {stream = "res://Assets/Audio/SFX/greyson_hurl_whoosh.wav", pitch = 1.0, volume_db = 0.0},
	&"breath": {stream = "res://Assets/Audio/SFX/greyson_hurl_whoosh.wav", pitch = 0.8, volume_db = -2.0},
	&"slam": {stream = "res://Assets/Audio/SFX/earthquake_slam.ogg", pitch = 1.0, volume_db = 0.0},
	&"rumble": {stream = "res://Assets/Audio/SFX/earthquake_slam.ogg", pitch = 0.7, volume_db = -8.0},
	&"staff_pull": {stream = "res://Assets/Audio/SFX/wrestler_collision.ogg", pitch = 1.4, volume_db = 0.0},
	&"window": {stream = "res://Assets/Audio/SFX/downed_stinger.ogg", pitch = 1.0, volume_db = 0.0},
	&"blow": {stream = "res://Assets/Audio/SFX/whirlwind_whoosh.ogg", pitch = 0.8, volume_db = 0.0},
	&"tornado": {stream = "res://Assets/Audio/SFX/greyson_hurl_whoosh.wav", pitch = 0.7, volume_db = -4.0},
	&"ignite": {stream = "res://Assets/Audio/SFX/matt_mystic_fire.wav", pitch = 0.8, volume_db = 0.0},
	&"quake": {stream = "res://Assets/Audio/SFX/earthquake_slam.ogg", pitch = 1.3, volume_db = -12.0},
	&"hiss": {stream = "res://Assets/Audio/SFX/burak_fuse_hiss.wav", pitch = 0.8, volume_db = 0.0},
	&"fizzle": {stream = "res://Assets/Audio/SFX/matt_mystic_fizzle.wav", pitch = 1.0, volume_db = 0.0},
	&"lunge_tell": {stream = "res://Assets/Audio/SFX/greyson_brawl_tell_parry.wav", pitch = 1.0, volume_db = 0.0},
	&"lunge": {stream = "res://Assets/Audio/SFX/carter_rush_1.wav", pitch = 1.0, volume_db = 0.0},
	&"impale": {stream = "res://Assets/Audio/SFX/carter_strike.wav", pitch = 1.0, volume_db = 0.0},
	&"call": {stream = "res://Assets/Audio/SFX/greyson_shout.wav", pitch = 1.3, volume_db = 0.0},
	&"bixby_answer": {stream = "res://Assets/Audio/SFX/bixby_roar_short.wav", pitch = 1.0, volume_db = -6.0},
	&"sky_fire": {stream = "res://Assets/Audio/SFX/rocket_launch.ogg", pitch = 0.6, volume_db = 0.0},
	&"water_jet": {stream = "res://Assets/Audio/SFX/danny_spit.wav", pitch = 0.7, volume_db = 0.0},
	&"vanish": {stream = "res://Assets/Audio/SFX/greyson_teleport_out.wav", pitch = 1.0, volume_db = 0.0},
	&"teleport_out": {stream = "res://Assets/Audio/SFX/matt_teleport_out.wav", pitch = 1.0, volume_db = 0.0},
	&"teleport_in": {stream = "res://Assets/Audio/SFX/matt_teleport_in.wav", pitch = 1.0, volume_db = 0.0},
}
const THEME := "res://Assets/Audio/Music/liam_theme.wav"
const THEME_DB := -7.0


#HIS POSES

static func sheet_path(anim_name: StringName) -> String:
	return DIR + "liam_%s.png" % ANIMS[anim_name].sheet


static func uses_final(anim_name: StringName) -> bool:
	return USE_FINAL_POSES and ResourceLoader.exists(sheet_path(anim_name))


static func cell(anim_name: StringName) -> Vector2:
	return ANIMS[anim_name].get("cell", CELL)


static func anchor(anim_name: StringName) -> Vector2:
	return ANIMS[anim_name].get("anchor", ANCHOR)


# The frames and times `anim_name` plays and whether it loops: an `all` pose's every frame on its sheet (one on the
# stand-in), a one-shot's times (spread) or its length split evenly across them, and a loop at its frame_time; any
# other pose its own.
static func clip(anim_name: StringName) -> Dictionary:
	var spec: Dictionary = ANIMS[anim_name]
	if not spec.get("all", false):
		return {frames = spec.frames, times = spec.times, loop = spec.loop}
	var count := strip_count(sheet_path(anim_name), cell(anim_name)) if uses_final(anim_name) else 1
	var looping: bool = spec.has("frame_time")
	var times: Array = []
	if spec.has("times"):
		times = spread(spec.times, count)
	else:
		for i in count:
			times.append(spec.frame_time if looping else spec.length / count)
	var frames := range(count)
	if spec.get("reverse", false):
		frames.reverse()
		times = times.duplicate()
		times.reverse()
	return {frames = frames, times = times, loop = looping}


# How far into `anim_name` its frame `frame` comes up (its last frame's, if it has fewer).
static func frame_start(anim_name: StringName, frame: int) -> float:
	var times: Array = clip(anim_name).times
	var start := 0.0
	for i in mini(frame, times.size() - 1):
		start += times[i]
	return start


# The point `key` on the pose `anim_name`, px off his feet, unflipped: on its sheet frame `frame` where that frame has
# its own, and the pose's otherwise.
static func point(key: StringName, anim_name: StringName, frame := -1) -> Vector2:
	if not uses_final(anim_name):
		return (PLACEHOLDER_POINTS[key] - PLACEHOLDER_ANCHOR) * SCALE
	var by_frame: Dictionary = FRAME_POINTS[key].get(anim_name, {})
	var by_pose: Dictionary = POINTS[key]
	var texel: Vector2 = by_frame.get(frame, by_pose.get(anim_name, by_pose.values()[0]))
	return (texel - anchor(anim_name)) * SCALE


static func anim_length(anim_name: StringName) -> float:
	var total := 0.0
	for time: float in clip(anim_name).times:
		total += time
	return total


#FRAME COUNTS (addendum 3, E.1): a sheet redrawn with more frames plays them all

static var _strip_counts := {}


# How many `frame`-wide frames the strip at `path` holds: its width over the frame's, read once.
static func strip_count(path: String, frame: Vector2) -> int:
	var key := "%s@%d" % [path, roundi(frame.x)]
	if not _strip_counts.has(key):
		var texture: Texture2D = load(path)
		_strip_counts[key] = maxi(roundi(texture.get_width() / frame.x), 1)
	return _strip_counts[key]


# `times` for a one-shot drawn in `count` frames: as they are when the count matches, otherwise `count` equal parts of
# their total, so it keeps its length however many frames it is drawn in.
static func spread(times: Array, count: int) -> Array:
	if count == times.size() or count <= 0:
		return times
	var total := 0.0
	for time: float in times:
		total += time
	var out := []
	for i in count:
		out.append(total / count)
	return out


# The frame `through` (0 to 1) of the way along a one-shot of `count` frames timed `times` (spread), whatever its length.
static func frame_at(times: Array, count: int, through: float) -> int:
	var parts := spread(times, count)
	var total := 0.0
	for time: float in parts:
		total += time
	var at := clampf(through, 0.0, 1.0) * total
	var end := 0.0
	for i in parts.size():
		end += parts[i]
		if at < end:
			return i
	return parts.size() - 1


#THE HAND-OVER

# Where a continuous texel point on the defeat frame stands in the world, for the beast's body at `beast_feet`.
static func defeat_point(beast_feet: Vector2, texel: Vector2) -> Vector2:
	return beast_feet + (texel - BixbyBeastArtLayout.ANCHOR) * SCALE


# His feet as frame 9 draws him: his cell's anchor point, one texel under his lowest row.
static func liam_handover(beast_feet: Vector2) -> Vector2:
	return defeat_point(beast_feet, DEFEAT_LIAM_FEET + Vector2(0, 1))


# The dog's, on bixby.png's own convention: its anchor one texel under its lowest row.
static func bixby_handover(beast_feet: Vector2) -> Vector2:
	return defeat_point(beast_feet, DEFEAT_BIXBY_FEET + Vector2(0, 1))


# The defeat sheet's frame-9 `region` as a Sprite2D region and offset (centered off) that draw it exactly where the
# beast drew it, for a sprite standing on the frame-9 point `feet`.
static func defeat_region(region: Rect2, feet: Vector2) -> Dictionary:
	var frame_x := DEFEAT_FRAME * BixbyBeastArtLayout.FRAME_SIZE.x
	return {rect = Rect2(region.position + Vector2(frame_x, 0), region.size), offset = region.position - feet}


#THE PILLAR

static func final_pillar() -> bool:
	return USE_FINAL_PILLAR and ResourceLoader.exists(PILLAR_SHEET)


static func final_pillar_shield() -> bool:
	return final_pillar() and ResourceLoader.exists(PILLAR_SHIELD_SHEET)


static func final_pillar_dust() -> bool:
	return final_pillar() and ResourceLoader.exists(PILLAR_DUST_SHEET)


#THE ROW

static func final_row() -> bool:
	return USE_FINAL_ROW and ResourceLoader.exists(ROW_RISE_SHEET) and ResourceLoader.exists(ROW_STAND_SHEET) \
		and ResourceLoader.exists(ROW_CRUMBLE_SHEET)


#THE WAVES

static func final_wave() -> bool:
	return USE_FINAL_WAVE and ResourceLoader.exists(WAVE_BODY_SHEET) and ResourceLoader.exists(WAVE_CREST_SHEET)


static func wave_x(side: StringName) -> Vector2:
	return WAVE_LEFT_X if side == &"left" else WAVE_RIGHT_X


#THE GUST

static func final_gust() -> bool:
	return USE_FINAL_GUST and ResourceLoader.exists(GUST_BURST_SHEET) and ResourceLoader.exists(GUST_TRAIL_SHEET)


#THE FLOOD

static func final_flood() -> bool:
	return USE_FINAL_FLOOD and ResourceLoader.exists(FLOOD_SHEET)


static func final_ice() -> bool:
	return final_flood() and ResourceLoader.exists(ICE_SHEET) and ResourceLoader.exists(ICE_MELT_SHEET) \
		and ResourceLoader.exists(ICE_SHATTER_SHEET)


static func final_frost() -> bool:
	return USE_FINAL_FLOOD and ResourceLoader.exists(FROST_SHEET)


#THE RIDGES

static func final_tremor() -> bool:
	return USE_FINAL_TREMOR and ResourceLoader.exists(TREMOR_SHEET)


static func final_crack() -> bool:
	return USE_FINAL_TREMOR and ResourceLoader.exists(TREMOR_CRACK_SHEET)


static func clip_length(clip: StringName) -> float:
	var total := 0.0
	for time: float in TREMOR_CLIPS[clip].times:
		total += time
	return total


# A ridge clip drawn as its own strip (fx_v2), which plays over the combined sheet's frames when it is in.
static func tremor_clip_sheet(clip: StringName) -> String:
	return DIR + "liam_tremor_block_%s.png" % clip


#THE REST

static func final_breath() -> bool:
	return USE_FINAL_BREATH and ResourceLoader.exists(BREATH_SHEET)


static func final_slam_burst() -> bool:
	return USE_FINAL_BREATH and ResourceLoader.exists(SLAM_BURST_SHEET)


static func final_downdraft() -> bool:
	return USE_FINAL_DOWNDRAFT and ResourceLoader.exists(DOWNDRAFT_SHEET)


#THE FIRESTORM AND THE STEAM

static func final_firestorm(path: String) -> bool:
	return USE_FINAL_FIRESTORM and ResourceLoader.exists(path)


static func final_tornado() -> bool:
	for path: String in TORNADO_SHEETS.values():
		if not final_firestorm(path):
			return false
	return true


static func final_tornado_form() -> bool:
	return USE_TORNADO_FORM and final_tornado() and ResourceLoader.exists(TORNADO_FORM_SHEET)


static func final_tornado_spew() -> bool:
	return USE_TORNADO_SPEW and final_tornado() and ResourceLoader.exists(TORNADO_SPEW_SHEET)


static func own_ring_art() -> bool:
	return USE_OWN_RING_ART and final_firestorm(FIRE_QUAKE_RING_SHEET)


static func final_steam(path: String) -> bool:
	return USE_FINAL_STEAM and ResourceLoader.exists(path)


#THE LUNGE

static func final_lunge(path: String) -> bool:
	return USE_FINAL_LUNGE and ResourceLoader.exists(path)


# The sky fire's column: his own, or Bixby's curtain with USE_OWN_SKY_FIRE off; empty until the one it wants is in.
static func sky_fire_column() -> Dictionary:
	var spec: Dictionary = SKY_FIRE if USE_OWN_SKY_FIRE else SKY_FIRE_CURTAIN
	return spec if final_lunge(spec.sheet) else {}


static func final_shadow() -> bool:
	return USE_FINAL_SHADOW and ResourceLoader.exists(SHADOW_SHEET)


static func juggle() -> Dictionary:
	if USE_FINAL_JUGGLE and ResourceLoader.exists(FINAL_JUGGLE.texture):
		return FINAL_JUGGLE
	return PLACEHOLDER_JUGGLE


# A closed ellipse of `points` round the origin, px.
static func ellipse(radii: Vector2, points := 24) -> PackedVector2Array:
	var out := PackedVector2Array()
	for i in points:
		out.append(Vector2.from_angle(TAU * i / points) * radii)
	return out


static func rect_polygon(rect: Rect2) -> PackedVector2Array:
	return PackedVector2Array([rect.position, Vector2(rect.end.x, rect.position.y), rect.end, Vector2(rect.position.x, rect.end.y)])
