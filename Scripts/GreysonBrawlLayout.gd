extends RefCounted

# Every number of Greyson's final brawl (GreysonFinalBrawl) that depends on how it is drawn and staged: where the
# two of them stand, the camera, the points on him and on the player, his clips, the player's poses and uppercut
# sheet, the rubble fill and the FX. The staging and the points are PLAN_BRAWL.md section 4's; the FX contract is
# art_source/greyson_brawl_fx/APPROVED.md; his anchors and timings are the brawl-set artist's report, and the
# player's the player artist's.
#
# HIS POINTS are texels on one of his 112x112 cells with his feet at (56,111), and land in the world at
# feet + (texel - FEET) * SCALE, the plan's own convention. His brawl sheets are never flipped: the gauntlet stays
# on screen-right.
#
# EACH SHEET HAS ITS FLAG, and nothing loads a final sheet while its flag is off or before it has been imported
# (ResourceLoader.exists). Until his brawl set is on he is his approved fight idle's f0 for everything, moved by
# code: PLACEHOLDER_CLIPS' `shifts` (texels, per step) and the KO's `tilt`. Until an FX sheet is on, GreysonBrawlFx
# and GreysonBrawlRubble draw a stand-in on the same point and clock.

const GreysonArt := preload("res://Scripts/GreysonArtLayout.gd")

const SCALE := 3.0
const FEET := Vector2(56, 111)

#THE STAGING (world px)
# His feet: HOME, where the brawl is fought.
const SPOT := Vector2(960, 560)
# The player's origin, their soles 39 px under it, 12 px in front of his feet.
const PLAYER_MARK := Vector2(960, 533)
# Where the player is put as the brawl hands over to either outro: soles in front of his boots, sorted over him.
const PLAYER_HANDOFF := Vector2(960, 566)
# What the player faces: his middle.
const FACE_AT := Vector2(960, 404)
const ZOOM := 1.5
const FOCUS := Vector2(960, 402)
# Absolute z: the player over his sprite (0), the whooshes and a slip's afterimage between, the impacts over all.
const PLAYER_Z := 3
const WHOOSH_Z := 2
const IMPACT_Z := 4
const TELL_Z := 3
# The tell stands this many texels over his guard crown; the daze stars this many px over his dazed crown.
const TELL_GAP := 6.0
const DAZE_GAP := GreysonArt.DAZE_GAP

#POINTS ON HIM (texels)
# His crown on each sheet: the brawl set's (the artist's anchors), and the stand-in's, which is the idle's f0.
const FINAL_CROWNS := {&"guard": Vector2(56, 33), &"dazed": Vector2(56, 39)}
const PLACEHOLDER_CROWN := Vector2(56, 26)
# The dazed chin, 46 texels up: where the uppercut's glove arrives, and the middle of the finisher's hurtbox. Both
# artists agree on it, and the uppercut's contact fist is drawn to it.
const DAZED_CHIN := Vector2(56, 65)
# px. Small, so the finisher's burst, clamped into it, lands on the chin; the finisher's 48 px reach still finds it.
const CHIN_BOX := Vector2(18, 18)
# The camera's follow point through the uppercuts, (960,431).
const JUGGLE_POINT := Vector2(56, 68)
# Where each punch arrives: the hooks' contact on the head at rest, which each hook's whoosh pivots on and a hook
# that lands bursts on; the straight's contact (the parry contact), which its burst pivots on; and the point a
# straight that lands bursts on.
const HOOK_CONTACT := Vector2(56, 73)
const STRAIGHT_CONTACT := Vector2(55, 63)
const STRAIGHT_LANDED := Vector2(56, 71)

#THE PLAYER (px from their origin)
const USE_FINAL_PLAYER_2X := true
# The native 2x back view: 10x4 cells of 64x96, soles 39 px under the origin, every row the same view. `head` is
# where the words over the player stand on the cell (CombatPopupUI): 4 texels over the top of the guard's hair, as
# FinisherArtLayout.PLAYER_HEAD stands over their own sheet's.
const PLAYER_SHEET_2X := {texture = "res://Assets/Characters/MainPlayer/player_final_brawl_2x.png", hframes = 10, vframes = 4, head = Vector2(32, 8)}
# The approved 1x poses, the same columns, for a checkout without the 2x sheet.
const PLAYER_SHEET_1X := {texture = "res://Assets/Characters/MainPlayer/player_final_brawl.png", hframes = 10, vframes = 4}
# Columns, seconds each (the last for the rest), looping or held on the last. A slip is its half then its full; the
# parry's snap is up for the answer's resolve_delay and its absorb from the parry on.
const PLAYER_POSES := {
	&"guard": {frames = [0, 1], times = [0.2], loop = true},
	&"slip_left": {frames = [2, 3], times = [0.05, 1.0], loop = false},
	&"slip_right": {frames = [4, 5], times = [0.05, 1.0], loop = false},
	&"parry": {frames = [6, 7], times = [0.06, 1.0], loop = false},
	&"hit": {frames = [8, 9], times = [0.08, 1.0], loop = false},
}
# A full slip moves the head this far aside (10 texels on the 2x sheet).
const PLAYER_SLIP := 30.0

#THE BRAWL'S UPPERCUT (PlayerFinisher.begin's sheet override: FinisherArtLayout.FINAL_PLAYER's keys)
# Drawn from behind, climbing the centre line: 10 cells of 64x128, soles 39 px under the origin. Frame 5 is the
# contact, the glove on his dazed chin; FINAL_PLAYER's timings, so the relaunch rhythm is unchanged.
const USE_FINAL_BRAWL_UPPERCUT := true
const BRAWL_UPPERCUT := {
	"texture": "res://Assets/Characters/MainPlayer/player_final_brawl_uppercut.png",
	"super_texture": "res://Assets/Characters/MainPlayer/player_final_brawl_uppercut_super.png",
	"hframes": 10,
	"vframes": 1,
	"offset": Vector2(0, -16),
	"ready": [0, Vector2.ZERO],
	"charge": [[0, Vector2.ZERO], [1, Vector2.ZERO], [2, Vector2.ZERO]],
	"charge_frame_time": [0.08, 0.05],
	"uppercut": [
		[3, Vector2.ZERO, 0.05],
		[4, Vector2.ZERO, 0.06],
		[5, Vector2.ZERO, 0.06],
		[6, Vector2.ZERO, 0.06],
		[7, Vector2.ZERO, 0.14],
		[8, Vector2.ZERO, 0.10],
		[9, Vector2.ZERO, 0.16],
	],
	"contact_step": 2,
	"reach_steps": [1, 2, 3],
	"fists": {1: Vector2(21, -93), 2: Vector2(0, -111), 3: Vector2(0, -141), 4: Vector2(0, -171)},
}

#HIS CLIPS
# His brawl set, a flag a sheet, all 112x112 with the feet at (56,111).
const SHEET_DIR := "res://Assets/Characters/Greyson/"
const USE_FINAL_SHEETS := {
	&"guard": true,
	&"hook_l": true,
	&"hook_r": true,
	&"straight": true,
	&"rocked": true,
	&"dazed": true,
	&"uppercut": true,
	&"recover": true,
	&"ko": true,
	&"toss": true,
}
const SHEETS := {
	&"guard": SHEET_DIR + "greyson_brawl_guard.png",
	&"hook_l": SHEET_DIR + "greyson_brawl_hook_l.png",
	&"hook_r": SHEET_DIR + "greyson_brawl_hook_r.png",
	&"straight": SHEET_DIR + "greyson_brawl_straight.png",
	&"rocked": SHEET_DIR + "greyson_brawl_rocked.png",
	&"dazed": SHEET_DIR + "greyson_brawl_dazed.png",
	&"uppercut": SHEET_DIR + "greyson_brawl_uppercut.png",
	&"recover": SHEET_DIR + "greyson_brawl_recover.png",
	&"ko": SHEET_DIR + "greyson_brawl_ko.png",
	&"toss": SHEET_DIR + "greyson_brawl_toss.png",
}
# name: sheet, frames in order, seconds on each (the last value repeats), whether it loops, and `next`, the clip a
# one-shot hands to at its end (without one it holds its last frame). A wind-up holds through the lead; the strike
# is the resolve's frame; the follow-through (landed), the whiff (dodged) and the parried frames follow it.
const FINAL_CLIPS := {
	&"guard": {sheet = &"guard", frames = [0, 1, 2, 3], times = [0.14], loop = true},
	&"hook_l_windup": {sheet = &"hook_l", frames = [0], times = [1.0], loop = true},
	&"hook_l_dodged": {sheet = &"hook_l", frames = [1, 3, 4], times = [0.10, 0.15, 0.12], loop = false, next = &"guard"},
	&"hook_l_landed": {sheet = &"hook_l", frames = [1, 2, 4], times = [0.10, 0.15, 0.12], loop = false, next = &"guard"},
	&"hook_r_windup": {sheet = &"hook_r", frames = [0], times = [1.0], loop = true},
	&"hook_r_dodged": {sheet = &"hook_r", frames = [1, 3, 4], times = [0.10, 0.15, 0.12], loop = false, next = &"guard"},
	&"hook_r_landed": {sheet = &"hook_r", frames = [1, 2, 4], times = [0.10, 0.15, 0.12], loop = false, next = &"guard"},
	&"straight_windup": {sheet = &"straight", frames = [0], times = [1.0], loop = true},
	&"straight_parried": {sheet = &"straight", frames = [1, 2, 3, 4], times = [0.10, 0.12, 0.18, 0.12], loop = false,
		next = &"guard"},
	&"straight_landed": {sheet = &"straight", frames = [1, 4], times = [0.25, 0.12], loop = false, next = &"guard"},
	# The feint, on the straight's own frames: the cannon arm cocked up and UNCHARGED (f4, the follow-through's
	# frame: no glow in the muzzle), held through the hold; bitten, the counter-jab snaps out on the thrust (f1) and
	# comes back. Held or slipped, he just drops back into his guard.
	&"feint_windup": {sheet = &"straight", frames = [4], times = [1.0], loop = true},
	&"feint_landed": {sheet = &"straight", frames = [1, 4], times = [0.10, 0.12], loop = false, next = &"guard"},
	&"rocked": {sheet = &"rocked", frames = [0, 1], times = [0.12, 0.13], loop = false},
	&"dazed": {sheet = &"dazed", frames = [0, 1, 2, 3], times = [0.12], loop = true},
	# Each uppercut's snap, then the reel held until the next one or his landing.
	&"uppercut": {sheet = &"uppercut", frames = [0, 1], times = [0.06, 1.0], loop = false},
	&"uppercut_settle": {sheet = &"uppercut", frames = [2], times = [1.0], loop = false},
	&"recover": {sheet = &"recover", frames = [0, 1, 2], times = [0.14, 0.13, 0.13], loop = false, next = &"guard"},
	# The killing uppercut's bigger snap, then the fall at its crash; the last frame, lying, is Defeated's.
	&"ko_snap": {sheet = &"ko", frames = [0], times = [1.0], loop = false},
	&"ko_fall": {sheet = &"ko", frames = [1, 2, 3, 4], times = [0.15, 0.15, 0.15, 1.0], loop = false},
	&"toss": {sheet = &"toss", frames = [0, 1, 2], times = [0.13, 0.13, 0.14], loop = false, next = &"guard"},
}
# The stand-ins: every clip on his fight idle's f0, with the plan's code motion. A 2-texel lean toward the wind-up,
# a 4-texel lunge toward the contact on the strike, a 3-texel lift on each uppercut (5 on the killing one), and the
# KO as a -80 degree fall about his feet over its `tilt_time`.
const PLACEHOLDER_CLIPS := {
	&"guard": {times = [1.0], loop = true},
	&"hook_l_windup": {times = [1.0], loop = true, shifts = [Vector2(2, 0)]},
	&"hook_l_dodged": {times = [0.10, 0.15, 0.12], loop = false, next = &"guard",
		shifts = [Vector2(-4, 0), Vector2(-4, 0), Vector2.ZERO]},
	&"hook_l_landed": {times = [0.10, 0.15, 0.12], loop = false, next = &"guard",
		shifts = [Vector2(-4, 0), Vector2(-4, 0), Vector2.ZERO]},
	&"hook_r_windup": {times = [1.0], loop = true, shifts = [Vector2(-2, 0)]},
	&"hook_r_dodged": {times = [0.10, 0.15, 0.12], loop = false, next = &"guard",
		shifts = [Vector2(4, 0), Vector2(4, 0), Vector2.ZERO]},
	&"hook_r_landed": {times = [0.10, 0.15, 0.12], loop = false, next = &"guard",
		shifts = [Vector2(4, 0), Vector2(4, 0), Vector2.ZERO]},
	&"straight_windup": {times = [1.0], loop = true, shifts = [Vector2(0, -2)]},
	&"straight_parried": {times = [0.10, 0.12, 0.18, 0.12], loop = false, next = &"guard",
		shifts = [Vector2(0, 4), Vector2.ZERO, Vector2.ZERO, Vector2.ZERO]},
	&"straight_landed": {times = [0.25, 0.12], loop = false, next = &"guard", shifts = [Vector2(0, 4), Vector2.ZERO]},
	&"feint_windup": {times = [1.0], loop = true, shifts = [Vector2(2, -2)]},
	&"feint_landed": {times = [0.10, 0.12], loop = false, next = &"guard", shifts = [Vector2(0, 4), Vector2.ZERO]},
	&"rocked": {times = [0.12, 0.13], loop = false},
	&"dazed": {times = [1.0], loop = true},
	&"uppercut": {times = [0.06, 1.0], loop = false, shifts = [Vector2(0, -3), Vector2(0, -3)]},
	&"uppercut_settle": {times = [1.0], loop = false},
	&"recover": {times = [0.14, 0.13, 0.13], loop = false, next = &"guard"},
	&"ko_snap": {times = [1.0], loop = false, shifts = [Vector2(0, -5)]},
	&"ko_fall": {times = [1.0], loop = false, tilt = -80.0, tilt_time = 0.45},
	&"toss": {times = [0.13, 0.13, 0.14], loop = false, next = &"guard"},
}
# Off his main set, for a brawl entered off a juggle: lying on his defeat's last frame until the cut, then up.
const MAIN_CLIPS := {
	&"lying": {anim = &"defeat", frames = [4], times = [1.0], loop = true},
	&"get_up": {anim = &"defeat", frames = [4, 3, 2, 1, 0], times = [0.12], loop = false, next = &"guard"},
}

#THE RUBBLE (world px)
# The pocket the two of them box in, left empty.
const CLEARING := Rect2(690, 400, 540, 300)
# No heap may be drawn over this: his silhouette and the tell (the adopted rule).
const KEEP_CLEAR := Rect2(840, 225, 240, 335)
# A jittered grid over the ropes' inside, inset, skipping bases inside the clearing grown by the margin; a row of
# low ridges along the clearing's front edge; the same fill every time, off a fixed seed.
const FILL_STEP := Vector2(150, 100)
const FILL_INSET := 20.0
const FILL_JITTER := Vector2(0.3, 0.15)
const CLEARING_MARGIN := 30.0
const FILL_SEED := 20260924
const FRONT_RIDGE_STEP := 132.0
const FRONT_RIDGE_JITTER := 10.0
# brawl_rubble_mound's frames, texels: 0-1 big with a beam, 2-4 big, 5-7 medium, 8-9 low ridges.
const HEAP_HEIGHTS := [40, 37, 38, 34, 36, 28, 26, 24, 16, 13]
const HEAP_HALF_WIDTHS := [31, 30, 31, 30, 29, 26, 24, 27, 30, 29]
const BEAM_HEAPS := [0, 1]
const BIG_HEAPS := [2, 3, 4]
const MEDIUM_HEAPS := [5, 6, 7]
const FRONT_HEAPS := [7, 8, 9]
const RIDGE_HEAPS := [8, 9]
const BEAM_CHANCE := 0.22
# Within this of the clearing a heap is a medium one; further out, big.
const NEAR_CLEARING := 160.0
# The four waves, one a slam, farthest from the clearing first. Each piece starts up to piece_delay after its slam.
const WAVES := 4
const PIECE_DELAY := 0.30
# The barbell, flung to screen-left into the rubble: greyson_barbell_prop, one 64x32 cell drawn lying flat, turning
# about its centre of mass as it flies. On the toss's fling frame (TOSS_FLING into it) his grip is on TOSS_GRIP of his
# cell, and the prop leaves with its own grip there; it lands TOSS_LANDS before the cut-in, its centre of mass on
# TOSS_TO, flat among the heaps.
const USE_FINAL_BARBELL := true
const BARBELL_PROP := {texture = SHEET_DIR + "greyson_barbell_prop.png", size = Vector2(64, 32), grip = Vector2(57, 16),
	balance = Vector2(22, 16)}
const TOSS_GRIP := Vector2(6, 50)
const TOSS_FLING := 0.13
const TOSS_LANDS := 0.05
const TOSS_TO := Vector2(470, 545)
const TOSS_ARC := 180.0
const TOSS_TURNS := 1.0

#THE FX (APPROVED.md). Horizontal strips at SCALE. `offset` is the frame's centre minus its pivot, for a centred
# Sprite2D standing its pivot on the point.
const FX_DIR := "res://Assets/Characters/Greyson/Brawl/"
const USE_FINAL_FX := {
	&"arrow": true,
	&"hook": true,
	&"straight": true,
	&"impact": true,
	&"debris": true,
	&"debris_shadow": true,
	&"debris_land": true,
	&"rubble_mound": true,
}
const FX := {
	# frame = direction * 4 + state: direction 0 LEFT, 1 RIGHT; state 0 pop, 1 live, 2 answered, 3 missed. Its
	# pivot, the disc's bottom, on the tell point.
	&"arrow": {texture = FX_DIR + "brawl_arrow.png", hframes = 8, offset = Vector2(0, -11)},
	# frame = hook * 4 + step: hook 0 his LEFT hook, 1 his RIGHT. The pivot on the head at rest.
	&"hook": {texture = FX_DIR + "brawl_hook.png", hframes = 8, offsets = [Vector2(10, -3), Vector2(-10, -3)]},
	# Centred on the parry contact.
	&"straight": {texture = FX_DIR + "brawl_straight.png", hframes = 4, offset = Vector2.ZERO},
	# Centred where the punch lands.
	&"impact": {texture = FX_DIR + "brawl_impact.png", hframes = 5, offset = Vector2.ZERO},
	# frame = shape * 2 + spin; the pivot, bottom centre, on the piece's base.
	&"debris": {texture = FX_DIR + "brawl_debris.png", hframes = 8, offset = Vector2(0, -28)},
	&"debris_shadow": {texture = FX_DIR + "brawl_debris_shadow.png", hframes = 1, offset = Vector2.ZERO},
	&"debris_land": {texture = FX_DIR + "brawl_debris_land.png", hframes = 6, offset = Vector2(0, -16)},
	&"rubble_mound": {texture = FX_DIR + "brawl_rubble_mound.png", hframes = 10, offset = Vector2(0, -22)},
}
# The arrow: pop, live to the resolve, then answered or missed, then ParryTell's fade.
const ARROW_POP := 0.05
const ARROW_HOLD := 0.12
const ARROW_FADE := 0.09
# The punch strips' steps; step 1 is on screen on the resolve's frame, so step 0 goes up this long before it.
const STRIKE_STEP := 0.04
const STRIP_LEAD := 0.04
const IMPACT_STEP := 0.04
# The debris: shapes, its spin, the drop and the fall; its shadow grows and darkens over the fall; its landing's
# frames, the heap swapped in under land_heap_frame.
const DEBRIS_SHAPES := 4
const DEBRIS_SPIN := 0.06
const DEBRIS_DROP := 420.0
const DEBRIS_FALL := 0.40
const SHADOW_SCALE := Vector2(0.3, 1.0)
const SHADOW_ALPHA := Vector2(0.15, 0.5)
const LAND_STEP := 0.05
const LAND_HEAP_FRAME := 2
# A clean slip's afterimage: copies of the player's frame in the perfect-dodge cyan, spaced from the slip back to
# the rest position, fading out.
const AFTERIMAGE_TINT := Color("#5FCDE4")
const AFTERIMAGE_ALPHAS := [0.45, 0.30, 0.15]
const AFTERIMAGE_FADE := 0.15

# The stand-ins' looks, in the kit's own colours (APPROVED.md's palette table).
const PLACEHOLDER_FX := {
	&"arrow": {radius = 33.0, ring = 6.0, disc = Color("#391555"), ring_color = Color("#FFC21E"),
		glyph = Color("#FFE45C"), answered = Color("#FFFCE0"), missed = Color("#9DA1C0"), pop_scale = 1.2},
	# The hook's arc in texels from its pivot, y = a x^2 + b x through the wind-up (34,-14), the head (0,0) and past
	# it (-10,-3); each step's tail and front along it, and its alpha.
	&"hook": {a = -24.2 / 1496.0, b = 10.0 * (-24.2 / 1496.0) + 0.3, width = 12.0, color = Color("#FFFFFF"),
		steps = [Vector2(34, 14), Vector2(34, 0), Vector2(22, -10), Vector2(6, -10)], alphas = [1.0, 1.0, 0.72, 0.45]},
	&"straight": {core = 12.0, rings = [16.0, 24.0, 36.0, 48.0], width = 6.0, color = Color("#FFFFFF"),
		alphas = [0.6, 1.0, 0.72, 0.45]},
	&"impact": {points = 8, outer = 36.0, inner = 14.0, scales = [0.7, 1.0, 1.15, 1.25, 1.3],
		alphas = [1.0, 1.0, 0.72, 0.45, 0.25], color = Color("#FFFFFF")},
	&"debris": {size = Vector2(66, 48), light = Color("#C7BBAB"), dark = Color("#6B6157")},
	&"debris_shadow": {radii = Vector2(54, 18), color = Color(0, 0, 0)},
	&"debris_land": {radius = 48.0, color = Color("#EDE4D6"), scales = [0.6, 0.9, 1.1, 1.25, 1.35, 1.4],
		alphas = [1.0, 0.9, 0.72, 0.55, 0.35, 0.2]},
	&"heap": {top = Color("#948779"), base = Color("#332B2B"), points = 12},
	&"barbell": {length = 180.0, width = 9.0, bar = Color("#9DA1C0"), plate = Color("#2A2A38"), plate_size = Vector2(18, 60)},
}


# His feet + a texel's offset from his, at SCALE.
static func his_point(texel: Vector2, feet := SPOT) -> Vector2:
	return feet + (texel - FEET) * SCALE


static func uses_final_sheet(sheet: StringName) -> bool:
	return USE_FINAL_SHEETS.get(sheet, false) and ResourceLoader.exists(SHEETS.get(sheet, ""))


# The clip `key` as it is drawn now: its texture, frames, times, loop, next, and the stand-in's shifts and tilt.
static func clip(key: StringName) -> Dictionary:
	if MAIN_CLIPS.has(key):
		var main: Dictionary = MAIN_CLIPS[key].duplicate()
		main.texture = GreysonArt.anim(main.anim).sheet
		return main
	var shipped: Dictionary = FINAL_CLIPS[key]
	if uses_final_sheet(shipped.sheet):
		var drawn := shipped.duplicate()
		drawn.texture = SHEETS[shipped.sheet]
		return drawn
	var stand_in: Dictionary = PLACEHOLDER_CLIPS[key].duplicate()
	stand_in.texture = GreysonArt.anim(&"idle").sheet
	stand_in.frames = []
	stand_in.frames.resize(stand_in.times.size())
	stand_in.frames.fill(0)
	return stand_in


# His crown on `sheet` (the guard's or the dazed one's), stand-in or drawn.
static func crown(sheet: StringName) -> Vector2:
	return FINAL_CROWNS[sheet] if uses_final_sheet(sheet) else PLACEHOLDER_CROWN


# Where the gold arrow's pivot and the red badge's tip stand: over his guard crown.
static func tell_point(feet := SPOT) -> Vector2:
	return his_point(crown(&"guard") - Vector2(0, TELL_GAP), feet)


static func daze_anchor(feet := SPOT) -> Vector2:
	return his_point(crown(&"dazed"), feet) - Vector2(0, DAZE_GAP)


# The player's pose sheet: the 2x once it can load, the approved 1x otherwise.
static func player_sheet() -> Dictionary:
	if USE_FINAL_PLAYER_2X and ResourceLoader.exists(PLAYER_SHEET_2X.texture):
		return PLAYER_SHEET_2X
	return PLAYER_SHEET_1X


# The finisher's override: the brawl's uppercut once it can load (its supercharged copy only if that can), or
# empty, the finisher's own.
static func uppercut_sheet() -> Dictionary:
	if not USE_FINAL_BRAWL_UPPERCUT or not ResourceLoader.exists(BRAWL_UPPERCUT.texture):
		return {}
	var sheet := BRAWL_UPPERCUT.duplicate()
	if not ResourceLoader.exists(sheet.super_texture):
		sheet.erase("super_texture")
	return sheet


static func uses_final_fx(key: StringName) -> bool:
	return USE_FINAL_FX.get(key, false) and ResourceLoader.exists(FX[key].texture)


# Where the prop's centre of mass is as it leaves his hand on the fling frame, his feet on `feet`.
static func toss_from(feet := SPOT) -> Vector2:
	return his_point(TOSS_GRIP, feet) + (BARBELL_PROP.balance - BARBELL_PROP.grip) * SCALE


static func uses_final_barbell() -> bool:
	return USE_FINAL_BARBELL and ResourceLoader.exists(BARBELL_PROP.texture)


static func heap_rect(base: Vector2, frame: int) -> Rect2:
	var half: float = HEAP_HALF_WIDTHS[frame] * SCALE
	var height: float = HEAP_HEIGHTS[frame] * SCALE
	return Rect2(base.x - half, base.y - height, half * 2.0, height)
