extends RefCounted

# Jordan's attack 5, the Elemental Wheel with Liam and Bixby (JordanComboWheel): every number it plays on, so a retune
# only needs this file (the build plan of 2026-10-06, scratchpad god_elements/PLAN.md; the wheel's layout is the art
# approval pass's contract.json, the coordinator's word of 2026-10-06). Liam floats in the Avatar State on the hub of a
# four-element wheel; three spins (single, single, double) each stop on an element, and Liam and Bixby answer it
# together; then Liam drops out of it, Bixby crashes, and the first one the player reaches is the one taken apart.
#
# THE RETUNE (the user, 2026-10-06: "the liam portion of the jordan god fight is far too easy, the fire needs to come
# out faster along with his other elemental moves"): every beat from the Avatar State to the last result is about a
# third quicker than the plan's - the spins, the stop's hold, the gaps, each result's wait for its first danger and the
# wait between its dangers, the fire's most - and the fairness floors under them are lowered to match (FAIRNESS).
#
# STAGING is world px under the god fight's 2/3 view (screen = (world + (480, 6)) / 1.5). Texel points are on a frame,
# origin its top-left; a "corner" is a texel's top-left corner.
#
# THE WHEEL (the approval pass): 192x192 frames, the centre corner (96, 96) on Liam's float pivot. Its four segments sit
# on the diagonals - at rest WATER top-left, EARTH top-right, FIRE bottom-right, AIR bottom-left (the same clockwise
# order as the plan: fire, air, water, earth) - and its one pointer on the top-right diagonal: a spin always stops on a
# quarter turn, the chosen element's quadrant under it. On a double the second pointer, on the bottom-right diagonal,
# has the clockwise neighbour under it. Positions are STEPS_PER_TURN a turn: SUB_FRAMES drawn sub-angles, each turned
# a quarter in code (pixel-exact); until the sub-angle sheet is in, the disc turns smoothly in code.
#
# THE ART SWITCHES IN ON ITS OWN: each piece once its file is in and imported and its USE_FINAL_* switch is on (static
# vars, so a test can hold the stand-ins); until then a stand-in drawn in code. Nothing ships before the user approves.

const GodLayout := preload("res://Scripts/JordanGodLayout.gd")
const PuppetLayout := preload("res://Scripts/JordanPuppetLayout.gd")
const BixbyBeastArtLayout := preload("res://Scripts/BixbyBeastArtLayout.gd")
const InfernoLayout := preload("res://Scripts/BixbyInfernoArtLayout.gd")
const FlybyLayout := preload("res://Scripts/BixbyFlybyLayout.gd")

const SCALE := 3.0
const FLOOR: Rect2 = GodLayout.FLOOR

enum Element { FIRE, AIR, WATER, EARTH }
const CLOCKWISE: Array[int] = [Element.FIRE, Element.AIR, Element.WATER, Element.EARTH]
const NAMES := {Element.FIRE: &"fire", Element.AIR: &"air", Element.WATER: &"water", Element.EARTH: &"earth"}
const NEXT_CLOCKWISE := {Element.FIRE: Element.AIR, Element.AIR: Element.WATER, Element.WATER: Element.EARTH,
	Element.EARTH: Element.FIRE}
# A double is the primary under the pointer and its clockwise neighbour under the second.
const DOUBLES := [[Element.FIRE, Element.AIR], [Element.AIR, Element.WATER], [Element.WATER, Element.EARTH],
	[Element.EARTH, Element.FIRE]]

#THE STAGING (world px)
# The wheel's hub is Liam's float pivot (the mockup's (960, 924)). He is summoned on LIAM_FEET and lifted until his
# float pivot is on the hub: LIAM_LIFT on his drawn float (the twin of liam_channel, its pivot corner FLOAT_PIVOT, the
# figure raised 12 rows to float), 36 px more on the live sheet, whose figure stands on the cell's floor
# (STAND_IN_PIVOT).
const WHEEL_HUB := Vector2(960, 924)
const LIAM_FEET := Vector2(960, 1194)
const LIAM_LIFT := 150.0
const LIAM_DOWN := LIAM_FEET
const LIAM_CELL := Vector2(96, 96)
const FLOAT_PIVOT := Vector2(48, 56)
const STAND_IN_PIVOT := Vector2(48, 68)
const LIAM_BOB := 6.0
const LIAM_BOB_HZ := 0.8
const LIFT_TIME := 0.5
# Bixby rests where the mockup hangs him (his frame's top-left at (1437, 654)): his anchor drawn at (1725, 1107),
# BIXBY_LIFT over his floor point. He crashes on BIXBY_DOWN.
const BIXBY_REST := Vector2(1725, 1267)
const BIXBY_LIFT := 160.0
const BIXBY_DOWN := Vector2(1460, 1130)
const BIXBY_FACE_LEFT := true
const START_CLEAR := 220.0
const START_STEP := 10.0
const START_RINGS := 90
const START_ANGLES := 32
const START_FALLBACK := Vector2(560, 1400)
const WARP_TIME := 0.35
const SEE_THROUGH := 0.4
const SEE_THROUGH_FADE := 0.15
const SOLES_OVER_ORIGIN := 42.0

#THE KEEP-CLEARS: Jordan's mask and core (world px), the HUD's blocks (screen px) and their clearance.
const MASK := Rect2(912, 189, 96, 69)
const CORE := Rect2(936, 270, 48, 57)
const HUD_KEEP_OUT: Array[Rect2] = [Rect2(720, 33, 480, 148), Rect2(10, 842, 406, 229), Rect2(1371, 946, 537, 126)]
const HUD_CLEARANCE := 12.0

#THE WHEEL
const WHEEL_FRAME := Vector2(192, 192)
const WHEEL_SCALE := 3.0
const WHEEL_RADIUS := 90.5
const WHEEL_HUB_RADIUS := 18.5
const ICON_RADIUS := 55.0
const STEPS_PER_TURN := 32
const SUB_FRAMES := 8
# Each segment's middle at rest, degrees clockwise from twelve o'clock, and the pointers'.
const ELEMENT_ANGLE := {Element.WATER: 315.0, Element.EARTH: 45.0, Element.FIRE: 135.0, Element.AIR: 225.0}
const POINTER_ANGLE := 45.0
const SECOND_POINTER_ANGLE := 135.0
# A spin: up to speed linearly over SPIN_UP, held, then eased out over DECEL as v = omega (1 - t / DECEL)^2, covering
# whole turns plus the way to the target, the fewest turns that keep omega (turns a second) at OMEGA_MIN or over.
const SPIN_UP := 0.2
const SPIN_TIME := [1.2, 1.0, 0.8]
const DECEL := [0.7, 0.55, 0.45]
const OMEGA_MIN := [1.0, 1.4, 1.8]
const STOP_HOLD := [0.3, 0.3, 0.4]
# The last quarter turn of a spin-down is never quicker than this: the stop is watched.
const LAST_SEGMENT_MIN := 0.30
# Over this many turns a second the drawn wheel shows its spin frame.
const BLUR_OMEGA := 1.5
const POINTER_BUMP := 0.04
# Spin 3's second pointer unfolds over its spin-up, in UNFOLD_FRAMES steps.
const UNFOLD_FRAMES := 3
# Formed by the end of the quicker Avatar State (AVATAR_TIME), so spin 1 starts on a whole wheel.
const FORM_DELAY := 0.1
const FORM_TIME := 0.5
const SHATTER_TIME := 0.4
const SHATTER_SCALE := 0.9
# The stop's flash on the chosen quadrant (the stand-in's): white, white-gold, then the lit pulse.
const FLASH_TIMES := [0.05, 0.05]
const LIT_PULSE := 0.1
# The icon over Liam's head: ICON_ABOVE_PIVOT px over his float pivot (the art pass's point), popping from ICON_POP_FROM to 1 over ICON_POP, drawn at ICON_SCALE px a texel; a double's
# two ICON_PAIR_X either side, the second at ICON_SECOND_SCALE. Gone over ICON_FADE once the result's first hazard is live.
const ICON_ABOVE_PIVOT := 144.0
const ICON_POP := 0.12
const ICON_POP_FROM := 0.6
const ICON_FADE := 0.15
const ICON_SCALE := 2.0
const ICON_PAIR_X := 36.0
const ICON_SECOND_SCALE := 0.75

#THE ART (approved by the user 2026-10-06: "approve all, ash fur, keep liam's size"; the full set's file names)
const WHEEL_DIR := "res://Assets/Characters/Jordan/Wheel/"
const PUPPET_DIR := PuppetLayout.PUPPET_DIR
# The disc: SUB_FRAMES sub-angles of the rest orientation, each a further 360 / STEPS_PER_TURN degrees on; the quarter
# turns are code's. The lit sheet, at rest orientation, turned with it at the stop: the four singles, then the four
# doubles (by DOUBLES index). Which frame is which is the full set's contract's: these follow the approval pass's order.
static var USE_FINAL_WHEEL := true
const WHEEL_SHEET := WHEEL_DIR + "element_wheel.png"
const LIT_SHEET := WHEEL_DIR + "element_wheel_lit.png"
const LIT_FRAMES := {Element.WATER: 0, Element.EARTH: 1, Element.FIRE: 2, Element.AIR: 3}
const LIT_DOUBLE_FRAMES := {0: 4, 1: 5, 2: 6, 3: 7}
# Optional: drawn over the disc while it spins faster than BLUR_OMEGA, in BLUR_STEP phases each turned a quarter in code.
static var USE_FINAL_BLUR := true
const BLUR_SHEET := WHEEL_DIR + "element_wheel_blur.png"
const BLUR_STEP := 22.5
# The pointer on the top-right diagonal, 40x40 (rest, bump, lit), drawn in place: the hub is its texel corner
# POINTER_HUB. The second pointer is the same art turned a quarter clockwise about the hub.
static var USE_FINAL_POINTER := true
const POINTER_SHEET := WHEEL_DIR + "element_wheel_pointer.png"
const POINTER_FRAME := Vector2(40, 40)
const POINTER_HUB := Vector2(-54, 94)
# Optional: the icons over Liam's head, 32x32 on (16, 16), each element a pop frame and a hold frame.
static var USE_FINAL_ICONS := true
const ICONS_SHEET := WHEEL_DIR + "element_icons.png"
const ICON_FRAME := Vector2(32, 32)
const ICON_FRAMES := {Element.FIRE: [0, 1], Element.AIR: [2, 3], Element.WATER: [4, 5], Element.EARTH: [6, 7]}
# Optional: the wheel drawing itself in (backward, the dissolve) and its shatter, square frames counted off the sheet.
static var USE_FINAL_FORM := true
const FORM_SHEET := WHEEL_DIR + "element_wheel_form.png"
static var USE_FINAL_SHATTER := true
const SHATTER_SHEET := WHEEL_DIR + "element_wheel_shatter.png"
# The stand-in wheel: a quadrant a segment, a letter on each, a rim, spokes along the axes and a hub.
const PLACEHOLDER_WHEEL := {
	colours = {Element.WATER: Color("#2B6CC0"), Element.EARTH: Color("#2F8A3C"), Element.FIRE: Color("#E0561A"),
		Element.AIR: Color("#A8DFF5")},
	letters = {Element.WATER: "W", Element.EARTH: "E", Element.FIRE: "F", Element.AIR: "A"},
	letter_colour = Color("#0B0610"), rim = Color("#5A5F6E"), rim_width = 30.0, spoke = Color("#3A3E4A"),
	spoke_width = 12.0, hub = Color("#6E7385"), lit = Color(1.8, 1.8, 1.6), flash = Color(3, 3, 3), flash_gold = Color(2.6, 2.2, 1.2),
	points = 48, font_size = 72,
}
const PLACEHOLDER_POINTER := {colour = Color("#E8D8C8"), lit = Color("#FFC45A"), edge = Color("#0B0610"),
	size = Vector2(54, 66), bump = 1.15}
const PLACEHOLDER_ICON := {radius = 32.0, ring = Color("#0B0610"), ring_width = 5.0, plus_colour = Color("#F2F3FF"),
	font_size = 40}

# Liam in the Avatar State: his twins (JordanPuppetLayout's liam row), and over each pose its additive glow strip on
# that pose's grid once drawn (liam_<sheet>_avatar.png), frame and flip synced. Until a pose's strip is in: his own frame
# again, added in rune blue.
static var USE_FINAL_AVATAR := true
const LIVE_FLOAT_SHEET := "res://Assets/Characters/Liam/Elements/liam_channel.png"
const GLOW_SUFFIX := "_avatar"
# His aura, back (behind him) and front (over him): 128x128 frames looping at AURA_TIME, normal blend, its texel corner
# AURA_ANCHOR on his anchor (the cell's bottom-middle), whatever pose. The State's flare in and burst out, added over
# channel's frame 0 (he holds it while they play).
const AURA_BACK_SHEET := PUPPET_DIR + "liam/liam_avatar_aura_back.png"
const AURA_FRONT_SHEET := PUPPET_DIR + "liam/liam_avatar_aura_front.png"
const AURA_FRAME := Vector2(128, 128)
const AURA_ANCHOR := Vector2(64, 104)
const AURA_TIME := 0.12
const AVATAR_ON_SHEET := PUPPET_DIR + "liam/liam_avatar_on.png"
const AVATAR_ON_TIMES := [0.06, 0.06, 0.08, 0.08, 0.12]
const AVATAR_OFF_SHEET := PUPPET_DIR + "liam/liam_avatar_off.png"
const AVATAR_OFF_TIMES := [0.08, 0.1, 0.12, 0.14]
const PLACEHOLDER_GLOW := {colour = Color("#66C6EC"), held = 0.45, flare = 1.0, flare_time = 0.3, burst_time = 0.3}

# Bixby's bite (5 frames on his own grid, f3 the snap) and his swim (4, its front cut at WATERLINE_ROW), each once in;
# until then perch frames 11-12 and his wingbeat cut at the stand-in's row.
static var USE_FINAL_BITE := true
const BITE_SHEET := PUPPET_DIR + "bixby/bixby_bite.png"
const BITE_SNAP_FRAME := 3
const JAWS_STAND_IN := Vector2(96, 62)
static var USE_FINAL_SWIM := true
const SWIM_SHEET := PUPPET_DIR + "bixby/bixby_swim.png"
const WATERLINE_ROW := 100
const WATERLINE_ROW_STAND_IN := 100
# His own frames' feet (BixbyBeastArtLayout.ANCHOR) as the puppet stands them, and his head off his feet.
const BIXBY_FEET := Vector2(96, 151)
const BADGE_GAP := 30.0

#FIRE: the gap (seconds from the result's start)
# "the fire needs to come out faster" (the user, 2026-10-06): a short projection and a quicker front, so the far end of
# the column's range comes in to keep the walk into it ahead of the front (F2).
const T_PROJ := 0.8
const WARN := 0.4
const ENTRY_LEAD := 0.2
const FLY_OFF := 0.35
const FRONT_SPEED := 2400.0
const BURN := 0.35
const DIE_TIME: float = InfernoLayout.FLOOD_DIE_TIME
const CURTAIN_W := 96.0
const COLUMN_W := [240.0, 200.0]
const COLUMN_NEAR := 360.0
const COLUMN_FAR := [640.0, 480.0]
const COLUMN_EDGE_SPARE := 40.0
const WIND := 150.0
# The crosswind's streaks fly at points this far out past the floor's middle, so they run nearly level.
const WIND_FAR := 6000.0
const PASS_ANCHOR_Y := 420.0
const EXIT_TIME := 0.3
const HOME_TIME := 0.5
const BREATH_ID := &"jordan_wheel_breath"
const FIRE_ID := &"jordan_wheel_fire"
const RIM := {width = 6.0, colour = Color(1, 0.85, 0.35), faint_alpha = 0.45, fade_time = 0.15}
const PLACEHOLDER_CURTAIN := {top = Color(1, 0.95, 0.6, 0.95), bottom = Color(1, 0.42, 0.08, 0.6), pulse = 0.1, rate = 9.0}

#WATER: the shark wave
# Its badge and its roll quicker for the user's "far too easy" (2026-10-06): the badge still a dodge's tell
# (DODGE_TELL_MIN), the dash window as wide (F4: the band is thinner than a dash, so a faster wave widens it a hair).
const WAVE_TELL := 0.45
const WAVE_SPEED := 1000.0
const WAVE_H := 150.0
const WAVE_CREST_ROWS := 40
const WAVE_BODY_ROWS := 10
const SHARK_SPEED := 500.0
# His floor point stays this far in from the walls while he rides it.
const SHARK_EDGE := 200.0
const DIVE_TIME := 0.4
const WAVE_ID := &"jordan_wheel_wave"
const WAVE_SPLASH_TIME := 0.3
const WAVE_SPLASHES := 8
# The shark's snap after the wave (the user, 2026-10-07: "C and add 1 and 2"): once it is off the floor he surfaces where
# it collapsed, on the floor's bottom edge behind the player, over BREACH_RISE - surfaced, his badge stands clear of the
# HUD's bottom blocks - then bites as the jaws do, rearing to SNAP_LIFT: the red badge, the contact BITE_TELL after it.
const BREACH_RISE := 0.2
const SNAP_LIFT := 90.0
const BREACH_ID := &"jordan_wheel_breach"

#EARTH: pillars and rings
const PILLAR_SPOTS: Array[Vector2] = [Vector2(-60, 760), Vector2(460, 760), Vector2(1460, 760), Vector2(1980, 760)]
const PILLAR_RISE := 0.4
const PILLAR_CLEAR := 360.0
const PILLAR_EDGE := 60.0
const CLIMB_TIME := 0.4
# The slams come sooner and closer for the user's "far too easy" (2026-10-06): the first as soon as a glide and a
# shadow's tell allow, the shadow still a dodge's tell (DODGE_TELL_MIN), and quicker rings spaced as close as a dash
# through each still has its immunity (DASH_GAP_MIN).
const GLIDE_TIME := 0.2
const SLAM_TELL := 0.45
const SLAM_DROP := 0.12
const FIRST_SLAM := 0.65
const SLAM_GAP_MIN := 0.8
const SLAM_LIFT := 420.0
const CRUMBLE_TIME := 0.4
const RING_SPEED := 2000.0
const RING_SPACING := 0.85
const RING_HALF_WIDTH := 36.0
# The band of the player's feet a ring tests (BixbyCombinedArtLayout.RING_FOOT_HEIGHT).
const RING_FOOT := 12.0
const MAGMA_FLARE := Color(2.4, 1.3, 0.6)
const MAGMA_FLARE_TIME := 0.3
const RING_ID := &"jordan_wheel_ring"
const FIRE_RING_ID := &"jordan_wheel_fire_ring"
const SLAM_SHAKE := {strength = 8.0, steps = 5, step = 0.03}
const AFTERSHOCK_DELAY := 0.75
const AFTERSHOCK_Y := 1360.0
const AFTERSHOCK_X := 700.0
const AFTERSHOCK_CLAMP := Vector2(200, 1720)
const AFTERSHOCK_MIN := 400.0
const SHADOW := {sheet = "res://Assets/Characters/Bixby/bixby_beast_shadow.png", frame = Vector2(192, 48), centre = Vector2(96, 25),
	alpha = 0.38, from_scale = 0.4}

#AIR: the jaws
const MAWS: Array[Vector2] = [Vector2(-120, 700), Vector2(2040, 700)]
const AIR_START_MIN := 700.0
const AIR_START_IDEAL := 1000.0
const R_MAW := Vector2(240, 86)
# The jaws open and bite sooner for the user's "far too easy" (2026-10-06): a shorter pull, so a stronger one, still
# dragging a player who stands AIR_START_MIN out into the maw before it ends; walking still beats it (NET_ESCAPE_MIN).
const LAIR_TIME := 0.3
const AIR_LIFT := 140.0
const MAW_FADE := 0.2
const PULL_START := 0.3
const PULL_SPEED := 480.0
const PULL_RAMP := 0.4
const PULL_TIME := 1.3
const BITE_REAR := 0.15
const BITE_LUNGE := 0.25
const BITE_TELL := BITE_REAR + BITE_LUNGE
# The jaws snap twice (the user's "C and add 1 and 2", 2026-10-07): the second badge goes up this long after the first
# bite lands, parried or not, once he has recoiled and flown back over his maw, so its contact comes after a hit's
# i-frames are over (F8).
const SECOND_BITE_GAP := 0.7
const REAR_BACK := 60.0
const RECOIL := 120.0
const RECOIL_TIME := 0.25
const BITE_FLASH := Color(3, 3, 3)
const SWALLOW_HOLD := 0.5
# A swallowed player is spat out this far past the maw's rim, toward the middle of the floor.
const SPIT_CLEAR := 10.0
# The result is over this long after the bite lands or the spit.
const CLEAR_AFTER := 0.2
# The drawn bite's jaw centre by frame, texels (art_source/god_elements/contract.json).
const BITE_JAWS := {0: Vector2(96, 61), 1: Vector2(96, 68), 2: Vector2(96, 73), 3: Vector2(96, 73), 4: Vector2(96, 63)}
const BITE_ID := &"jordan_wheel_bite"
const SWALLOW_ID := &"jordan_wheel_swallow"
const CHOMP_ID := &"jordan_wheel_chomp"
const PLACEHOLDER_MAW := {fill = Color(0.12, 0.0, 0.02, 0.55), rim = Color("#B3202A"), rim_width = 6.0, points = 40}

#THE RUN
const AVATAR_TIME := 0.6
const CLEAR_GAP := 0.2
const CRASH_TIME := 1.0
const CRASH_FALL := 0.6
# Once the drawn burst out has played, his fall takes what is left of CRASH_TIME, never less than this.
const CRASH_FALL_MIN := 0.3
const CRASH_ARC := 120.0
const STAMINA_FLOOR := 34.0
const HYPE_RESULT := 4.0
const HYPE_CLEAN := 10.0
const REACH_MARGIN := 8.0
const HINT_TIME := 3.0
const HINTS := {
	Element.FIRE: "GET INTO THE GAP IN THE FIRE!",
	Element.WATER: "STAND, DASH THE WAVE, THEN PARRY THE BITE!",
	Element.EARTH: "DASH THROUGH EACH RING!",
	Element.AIR: "WALK AGAINST THE WIND, THEN PARRY BOTH BITES!",
}
const DOUBLE_HINT := "TWO ELEMENTS AT ONCE!"
# A double with its own hint, by DOUBLES index, the first time it comes; the rest share DOUBLE_HINT.
const DOUBLE_HINTS := {1: "DASH THROUGH THE WAVE, THEN PARRY THE JAWS!"}

#SOUNDS (stand-ins off the shared set, each only if its file is in)
const SOUNDS := {
	&"tick": {stream = "res://Assets/Audio/SFX/parry_tink_1.wav", pitch = 1.6, volume_db = -8.0, voices = 4},
	&"clunk": {stream = "res://Assets/Audio/SFX/hit_impact.ogg", pitch = 0.6, volume_db = -2.0, voices = 1},
	&"form": {stream = "res://Assets/Audio/SFX/carter_dark.wav", pitch = 1.2, volume_db = -4.0, voices = 1},
	&"fire": {stream = "res://Assets/Audio/SFX/matt_mystic_fire.wav", pitch = 0.8, volume_db = 0.0, voices = 1},
	&"water": {stream = "res://Assets/Audio/SFX/whirlwind_whoosh.ogg", pitch = 0.6, volume_db = -2.0, voices = 1},
	&"earth": {stream = "res://Assets/Audio/SFX/earthquake_slam.ogg", pitch = 0.9, volume_db = -4.0, voices = 1},
	&"air": {stream = "res://Assets/Audio/SFX/greyson_hurl_whoosh.wav", pitch = 0.8, volume_db = 0.0, voices = 1},
	&"breath": {stream = "res://Assets/Audio/SFX/rocket_launch.ogg", pitch = 0.7, volume_db = -2.0, voices = 1},
	&"slam": {stream = "res://Assets/Audio/SFX/earthquake_slam.ogg", pitch = 1.0, volume_db = 0.0, voices = 2},
	&"bite": {stream = "res://Assets/Audio/SFX/carter_strike.wav", pitch = 0.8, volume_db = 0.0, voices = 1},
	&"chomp": {stream = "res://Assets/Audio/SFX/hit_impact.ogg", pitch = 0.5, volume_db = 0.0, voices = 1},
	&"shatter": {stream = "res://Assets/Audio/SFX/carter_parry_break.wav", pitch = 0.8, volume_db = 0.0, voices = 1},
	&"crash": {stream = "res://Assets/Audio/SFX/earthquake_slam.ogg", pitch = 0.7, volume_db = 0.0, voices = 1},
}

#FAIRNESS (invariants): the model player - their walk, half their width and their hurtbox's height, a dash's reach,
# its immunity (and the wave's), the i-frames, a new player's reaction and the margin; what each rule has to leave.
const PLAYER_WALK := 600.0
const PLAYER_HALF_WIDTH := 18.0
const PLAYER_HURT_HEIGHT := 81.0
const DASH_DISTANCE := 250.0
const DASH_SPENT := 8.0 / 60.0
const DASH_IMMUNITY := 0.18
const WAVE_IMMUNITY := 0.21
const IFRAMES := 1.0
const REACTION := 0.25
const MARGIN := 25.0
const PARRY_WINDOW := 0.24
# A press this soon after one that parried nothing gets no parry (PlayerDefense.parry_mash_lockout).
const PARRY_MASH_LOCKOUT := 0.5
# The floors the retune lowered (the user, 2026-10-06: "the fire needs to come out faster along with his other
# elemental moves"; the plan had 0.15 s to spare on the walk into the gap, 3 frames of curtain on a spot, 180 px/s net
# against the pull, 1.0 s from the stop's end to the first hit and 0.8 s to the wave, slams 0.9 s apart and a 0.6 s
# shadow). Still: the walk into the gap is CROSS_SPARE ahead of the front after a new player's reaction; the curtain,
# 96 px moving 40 a step, can't step over a 36 px body; walking still gets away from the pull; a dodge's tell is never
# under DODGE_TELL_MIN and the bite's red badge never under PARRY_TELL_MIN ahead of it; and a player's required dashes
# are DASH_GAP_MIN apart or more - DASH_REARM and both presses' timing error.
const CROSS_SPARE := 0.10
const DASH_SLACK := 40.0
const CAUGHT_SLACK := 0.02
const CURTAIN_STEPS_MIN := 2
const WAVE_WINDOW_MIN := 0.20
const RING_WINDOW_MIN := 0.20
const NET_ESCAPE_MIN := 120.0
const REACTION_DRIFT_MAX := 60.0
const DODGE_TELL_MIN := 0.4
const PARRY_TELL_MIN := 0.35
# A dash buys its immunity only this long after the one before began (DashImmunity: AttackCatalog's
# DASH_IMMUNITY_COOLDOWN), longer than feel_v2's own cooldown between dashes.
const DASH_REARM := 0.6
const DASH_GAP_MIN := DASH_REARM + 0.12
const EARLIEST_HIT := 0.6
# The water's earliest hit is its badge's whole tell: a player against the top wall has no travel.
const EARLIEST_WAVE := DODGE_TELL_MIN


#THE WHEEL

static func stop_rotation(element: int) -> float:
	return fposmod(POINTER_ANGLE - float(ELEMENT_ANGLE[element]), 360.0)


static func step_degrees() -> float:
	return 360.0 / STEPS_PER_TURN


# Which of the STEPS_PER_TURN positions a rotation (degrees clockwise) is drawn at.
static func position_of(rotation_deg: float) -> int:
	return posmod(roundi(rotation_deg / step_degrees()), STEPS_PER_TURN)


static func stop_position(element: int) -> int:
	return position_of(stop_rotation(element))


# The element whose segment a pointer at `pointer_deg` points into, the wheel turned `rotation_deg`.
static func element_under(rotation_deg: float, pointer_deg: float) -> int:
	var best := Element.FIRE
	var nearest := INF
	for element: int in CLOCKWISE:
		var off := absf(wrapf(float(ELEMENT_ANGLE[element]) + rotation_deg - pointer_deg, -180.0, 180.0))
		if off < nearest:
			nearest = off
			best = element
	return best


# Spin `k` (0, 1 or 2) from `from_deg` to `target`'s stop.
static func spin_plan(k: int, from_deg: float, target: int) -> Dictionary:
	var time: float = SPIN_TIME[k]
	var decel: float = DECEL[k]
	var hold := time - SPIN_UP - decel
	var span := SPIN_UP / 2.0 + hold + decel / 3.0
	var turns := fposmod(stop_rotation(target) - from_deg, 360.0) / 360.0
	while turns / span < float(OMEGA_MIN[k]) - 0.000001:
		turns += 1.0
	return {k = k, target = target, omega = turns / span, turns = turns, from = from_deg, to = from_deg + turns * 360.0,
		up = SPIN_UP, hold = hold, decel = decel, time = time}


# Turns travelled `t` into the spin.
static func spin_turns(plan: Dictionary, t: float) -> float:
	var w: float = plan.omega
	var up: float = plan.up
	var hold: float = plan.hold
	var decel: float = plan.decel
	if t <= 0.0:
		return 0.0
	if t < up:
		return w * t * t / (2.0 * up)
	var done := w * up / 2.0
	if t < up + hold:
		return done + w * (t - up)
	done += w * hold
	var s := minf(t - up - hold, decel)
	return done + w * decel / 3.0 * (1.0 - pow(1.0 - s / decel, 3.0))


static func spin_rotation(plan: Dictionary, t: float) -> float:
	if t >= plan.time:
		return plan.to
	return float(plan.from) + spin_turns(plan, t) * 360.0


# Turns a second `t` into the spin.
static func spin_omega(plan: Dictionary, t: float) -> float:
	var w: float = plan.omega
	var up: float = plan.up
	var hold: float = plan.hold
	var decel: float = plan.decel
	if t <= 0.0 or t >= plan.time:
		return 0.0
	if t < up:
		return w * t / up
	if t < up + hold:
		return w
	var left := 1.0 - (t - up - hold) / decel
	return w * left * left


# How long the last quarter turn of its spin-down takes.
static func last_segment_time(plan: Dictionary) -> float:
	var w: float = plan.omega
	var decel: float = plan.decel
	var decel_turns := w * decel / 3.0
	if decel_turns >= 0.25:
		return decel * pow(0.25 / decel_turns, 1.0 / 3.0)
	return decel + (0.25 - decel_turns) / w


# Pegs on the segments' edges (the axes) pass a pointer (on a diagonal) once a quarter turn: how many by `rotation_deg`.
static func ticks_at(rotation_deg: float) -> int:
	return floori((rotation_deg - POINTER_ANGLE + 45.0) / 90.0)


# A run's three spins from the deck: two singles, then the double, never last run's (-1 on the first: any of the four).
# [single, single, double index].
static func deal(rng: RandomNumberGenerator, last_double: int) -> Array:
	var choices: Array[int] = []
	for i in DOUBLES.size():
		if i != last_double:
			choices.append(i)
	var double_index: int = choices[rng.randi_range(0, choices.size() - 1)]
	var singles: Array[int] = []
	for element: int in CLOCKWISE:
		if not DOUBLES[double_index].has(element):
			singles.append(element)
	if rng.randf() < 0.5:
		singles.reverse()
	return [singles[0], singles[1], double_index]


# The point the icon pops over, off his float pivot.
static func icon_point(pivot: Vector2) -> Vector2:
	return pivot + Vector2(0, -ICON_ABOVE_PIVOT)


# His lift that puts `pivot` (his float pivot on the sheet he is drawn on) on the hub.
static func liam_lift(pivot: Vector2) -> float:
	return LIAM_FEET.y - WHEEL_HUB.y - (LIAM_CELL.y - pivot.y) * SCALE


#FIRE

static func column_width(double: bool) -> float:
	return COLUMN_W[1] if double else COLUMN_W[0]


static func column_far(double: bool) -> float:
	return COLUMN_FAR[1] if double else COLUMN_FAR[0]


# Where a column's middle may be: inside the floor with COLUMN_EDGE_SPARE to spare.
static func column_room(double: bool) -> Vector2:
	var half := column_width(double) / 2.0
	return Vector2(FLOOR.position.x + COLUMN_EDGE_SPARE + half, FLOOR.end.x - COLUMN_EDGE_SPARE - half)


# The column's middle: COLUMN_NEAR to COLUMN_FAR off the player's x, a random side where both have room.
static func column_for(rng: RandomNumberGenerator, player_x: float, double: bool) -> float:
	var room := column_room(double)
	var spans: Array[Vector2] = []
	for side: float in [-1.0, 1.0]:
		var a := player_x + side * COLUMN_NEAR
		var b := player_x + side * column_far(double)
		var span := Vector2(maxf(minf(a, b), room.x), minf(maxf(a, b), room.y))
		if span.x <= span.y:
			spans.append(span)
	if spans.is_empty():
		return clampf(player_x + COLUMN_NEAR, room.x, room.y)
	var pick: Vector2 = spans[rng.randi_range(0, spans.size() - 1)]
	return rng.randf_range(pick.x, pick.y)


# The pass flies in from the wall farther from the column: 1 from the left, -1 from the right.
static func entry_for(cx: float) -> float:
	return 1.0 if cx - FLOOR.position.x > FLOOR.end.x - cx else -1.0


static func entry_x(direction: float) -> float:
	return FLOOR.position.x if direction > 0.0 else FLOOR.end.x


static func column_span(cx: float, double: bool) -> Vector2:
	var half := column_width(double) / 2.0
	return Vector2(cx - half, cx + half)


# The height his mouths cross at on a pass, which the curtain hangs from.
static func mouth_y() -> float:
	return PASS_ANCHOR_Y + (FlybyLayout.lead_exit().y - BixbyBeastArtLayout.ANCHOR.y) * SCALE


# Seconds from the projection to the front reaching the column's near edge.
static func front_reaches(cx: float, double: bool) -> float:
	var span := column_span(cx, double)
	var direction := entry_for(cx)
	var near := span.x if direction > 0.0 else span.y
	return T_PROJ + absf(near - entry_x(direction)) / FRONT_SPEED


# The walk from `from_x` into the column, the body WIDE of its edge by MARGIN.
static func walk_into(from_x: float, cx: float, double: bool) -> float:
	return maxf(absf(cx - from_x) - (column_width(double) / 2.0 - PLAYER_HALF_WIDTH - MARGIN), 0.0)


# F2: what a walker reacting REACTION late has left over, against the wind on a double.
static func fire_spare(from_x: float, cx: float, double: bool, reaction := REACTION) -> float:
	var speed := PLAYER_WALK - (WIND if double else 0.0)
	return front_reaches(cx, double) - reaction - walk_into(from_x, cx, double) / speed


# The worst F2 placement: the column as far as it goes, its near edge as near the entry as it can be.
static func worst_fire_spare(double: bool) -> float:
	var worst_reach := T_PROJ + (FLOOR.size.x / 2.0 - column_width(double) / 2.0) / FRONT_SPEED
	var walk := column_far(double) - (column_width(double) / 2.0 - PLAYER_HALF_WIDTH - MARGIN)
	var speed := PLAYER_WALK - (WIND if double else 0.0)
	return worst_reach - REACTION - walk / speed


#AIR

# The maw: of those at least AIR_START_MIN from the soles, the one whose distance is nearest AIR_START_IDEAL.
static func maw_for(soles: Vector2) -> int:
	var best := 0
	var off := INF
	for i in MAWS.size():
		var distance := soles.distance_to(MAWS[i])
		if distance < AIR_START_MIN:
			continue
		if absf(distance - AIR_START_IDEAL) < off:
			off = absf(distance - AIR_START_IDEAL)
			best = i
	return best


static func in_maw(soles: Vector2, maw: Vector2) -> bool:
	return ((soles - maw) / R_MAW).length_squared() <= 1.0


static func pull_speed() -> float:
	return PULL_SPEED


# The pull `t` into the jaws, px/s: ramped in over PULL_RAMP from PULL_START, for PULL_TIME.
static func pull_at(t: float) -> float:
	if t < PULL_START or t >= PULL_START + PULL_TIME:
		return 0.0
	return pull_speed() * clampf((t - PULL_START) / PULL_RAMP, 0.0, 1.0)


#EARTH

# The three pillars in slam order: the spot nearest the player dropped, any other still within PILLAR_CLEAR moved
# along its row off them, and the slams from the end farther from the player.
static func pillars_for(soles: Vector2) -> Array[Vector2]:
	var nearest := 0
	for i in PILLAR_SPOTS.size():
		if PILLAR_SPOTS[i].distance_to(soles) < PILLAR_SPOTS[nearest].distance_to(soles):
			nearest = i
	var out: Array[Vector2] = []
	for i in PILLAR_SPOTS.size():
		if i == nearest:
			continue
		var spot: Vector2 = PILLAR_SPOTS[i]
		if spot.distance_to(soles) < PILLAR_CLEAR:
			var dy := spot.y - soles.y
			var dx := sqrt(maxf(PILLAR_CLEAR * PILLAR_CLEAR - dy * dy, 0.0)) + 1.0
			var away := signf(spot.x - soles.x)
			if away == 0.0:
				away = 1.0 if soles.x < FLOOR.get_center().x else -1.0
			spot.x = clampf(soles.x + away * dx, FLOOR.position.x + PILLAR_EDGE, FLOOR.end.x - PILLAR_EDGE)
		out.append(spot)
	out.sort_custom(func(a: Vector2, b: Vector2) -> bool: return a.x < b.x)
	if absf(out[0].x - soles.x) < absf(out[out.size() - 1].x - soles.x):
		out.reverse()
	return out


# Each slam after the first: SLAM_GAP_MIN, or long enough that ring k + 1 reaches any point RING_SPACING after ring k.
static func slam_gaps(pillars: Array[Vector2]) -> Array[float]:
	var gaps: Array[float] = []
	for k in range(1, pillars.size()):
		gaps.append(maxf(SLAM_GAP_MIN, absf(pillars[k].x - pillars[k - 1].x) / RING_SPEED + RING_SPACING))
	return gaps


static func slam_times(pillars: Array[Vector2]) -> Array[float]:
	var times: Array[float] = [FIRST_SLAM]
	for gap in slam_gaps(pillars):
		times.append(times[-1] + gap)
	return times


# The landslide's aftershock: AFTERSHOCK_X off the player on the side with more room, clamped, AFTERSHOCK_MIN off them.
static func aftershock_for(soles: Vector2) -> Vector2:
	var side := 1.0 if FLOOR.end.x - soles.x >= soles.x - FLOOR.position.x else -1.0
	var first := Vector2.INF
	for s: float in [side, -side]:
		var at := Vector2(clampf(soles.x + s * AFTERSHOCK_X, AFTERSHOCK_CLAMP.x, AFTERSHOCK_CLAMP.y), AFTERSHOCK_Y)
		if not first.is_finite():
			first = at
		if at.distance_to(soles) >= AFTERSHOCK_MIN:
			return at
	return first


# From the landslide's wave leaving the floor to its aftershock's slam: the shark surfacing and snapping, his recoil,
# then the aftershock's glide and shadow.
static func aftershock_after_clear() -> float:
	return BREACH_RISE + BITE_TELL + RECOIL_TIME + AFTERSHOCK_DELAY


# How far round a ring's floor ellipse a point is from its middle (BixbyQuakeRingScript's metric).
static func ring_distance(centre: Vector2, point: Vector2) -> float:
	var off := point - centre
	return Vector2(off.x, off.y / 0.36).length()


#THE START

static func start_clear(soles: Vector2) -> bool:
	return soles.distance_to(LIAM_FEET) >= START_CLEAR and soles.distance_to(BIXBY_REST) >= START_CLEAR


# The nearest clear spot on half rings, level, down and level again (JordanPortalSpikes.start_spot's search).
static func start_spot(soles: Vector2, origins: Rect2) -> Vector2:
	if start_clear(soles):
		return soles
	for ring in range(1, START_RINGS + 1):
		for k in START_ANGLES + 1:
			var at := (soles + Vector2.from_angle(PI * k / START_ANGLES) * ring * START_STEP).round()
			var origin := at - Vector2(0, SOLES_OVER_ORIGIN)
			if start_clear(at) and (not origins.has_area() or origins.grow(0.5).has_point(origin)):
				return at
	return START_FALLBACK


#KEEP-CLEARS

static func keep_outs() -> Array[Rect2]:
	var out: Array[Rect2] = [MASK, CORE]
	for block: Rect2 in HUD_KEEP_OUT:
		out.append(hud_world(block.grow(HUD_CLEARANCE)))
	return out


static func hud_world(screen: Rect2) -> Rect2:
	var zoom: float = GodLayout.VIEW_ZOOM
	return Rect2((screen.position - GodLayout.VIEW_SIZE / 2.0) / zoom + GodLayout.VIEW_FOCUS, screen.size / zoom)


#THE ART'S GATES

static func final_wheel() -> bool:
	return USE_FINAL_WHEEL and ResourceLoader.exists(WHEEL_SHEET) and ResourceLoader.exists(LIT_SHEET)


static func final_blur() -> bool:
	return final_wheel() and USE_FINAL_BLUR and ResourceLoader.exists(BLUR_SHEET)


static func final_pointer() -> bool:
	return USE_FINAL_POINTER and ResourceLoader.exists(POINTER_SHEET)


static func final_icons() -> bool:
	return USE_FINAL_ICONS and ResourceLoader.exists(ICONS_SHEET)


static func final_form() -> bool:
	return final_wheel() and USE_FINAL_FORM and ResourceLoader.exists(FORM_SHEET)


static func final_shatter() -> bool:
	return final_wheel() and USE_FINAL_SHATTER and ResourceLoader.exists(SHATTER_SHEET)


# His drawn float: the twin of his channel sheet, in and imported.
static func final_float() -> bool:
	return PuppetLayout.twin_path(&"liam", LIVE_FLOAT_SHEET) != ""


static func final_aura() -> bool:
	return USE_FINAL_AVATAR and ResourceLoader.exists(AURA_BACK_SHEET) and ResourceLoader.exists(AURA_FRONT_SHEET)


static func final_avatar_on() -> bool:
	return USE_FINAL_AVATAR and ResourceLoader.exists(AVATAR_ON_SHEET)


static func final_avatar_off() -> bool:
	return USE_FINAL_AVATAR and ResourceLoader.exists(AVATAR_OFF_SHEET)


static func strip_time(times: Array) -> float:
	var total := 0.0
	for time: float in times:
		total += time
	return total


# A pose's own glow strip, or "" until it is in.
static func glow_sheet(sheet_path: String) -> String:
	if not USE_FINAL_AVATAR or sheet_path == "":
		return ""
	var path := PUPPET_DIR + "liam/" + sheet_path.get_file().get_basename() + GLOW_SUFFIX + ".png"
	return path if ResourceLoader.exists(path) else ""


static func final_bite() -> bool:
	return USE_FINAL_BITE and ResourceLoader.exists(BITE_SHEET)


static func final_swim() -> bool:
	return USE_FINAL_SWIM and ResourceLoader.exists(SWIM_SHEET)


# His float's pivot on the sheet he is drawn from.
static func float_pivot() -> Vector2:
	return FLOAT_PIVOT if final_float() else STAND_IN_PIVOT


static func bite_anim() -> StringName:
	return &"bite" if final_bite() else &"bite_stand_in"


# The jaws' texel at the snap.
static func jaws() -> Vector2:
	if final_bite():
		return BITE_JAWS.get(BITE_SNAP_FRAME, JAWS_STAND_IN)
	return JAWS_STAND_IN


static func swim_anim() -> StringName:
	return &"swim" if final_swim() else &"swim_stand_in"


static func waterline_row() -> int:
	return WATERLINE_ROW if final_swim() else WATERLINE_ROW_STAND_IN


#FAIRNESS

static func invariants() -> Array[String]:
	var broken: Array[String] = []
	# F1: the stop reads before anything can hurt.
	for k in SPIN_TIME.size():
		if k > 0 and SPIN_TIME[k] >= SPIN_TIME[k - 1]:
			broken.append("F1: spin %d is not quicker than spin %d" % [k + 1, k])
		if SPIN_UP + float(DECEL[k]) > float(SPIN_TIME[k]) + 0.0001:
			broken.append("F1: spin %d has no hold" % (k + 1))
		for quarter in 4:
			var plan := spin_plan(k, quarter * 90.0, Element.EARTH)
			if last_segment_time(plan) < LAST_SEGMENT_MIN - 0.0001:
				broken.append("F1: spin %d's last quarter turn takes %.3f s" % [k + 1, last_segment_time(plan)])
			if plan.omega < float(OMEGA_MIN[k]) - 0.0001:
				broken.append("F1: spin %d under OMEGA_MIN" % (k + 1))
	if T_PROJ < EARLIEST_HIT or FIRST_SLAM < EARLIEST_HIT:
		broken.append("F1: the fire's projection or the first slam lands under %.1f s after the stop" % EARLIEST_HIT)
	if WAVE_TELL < EARLIEST_WAVE - 0.0001:
		broken.append("F1: the wave rolls %.2f s after the stop, under %.2f" % [WAVE_TELL, EARLIEST_WAVE])
	var drag_in := PULL_START + PULL_RAMP + (AIR_START_MIN - R_MAW.x - PULL_SPEED * PULL_RAMP / 2.0) / PULL_SPEED
	if drag_in < 0.9 + 0.0001:
		broken.append("F1: a still player is dragged into the maw %.2f s after the stop" % drag_in)
	# F2: the fire arrives first.
	for double: bool in [false, true]:
		var spare := worst_fire_spare(double)
		if spare < CROSS_SPARE - 0.0001:
			broken.append("F2: the worst walk into the %s column is %.3f s ahead of the front, under %.2f" % [
				"double's" if double else "single's", spare, CROSS_SPARE])
		if COLUMN_NEAR < column_width(double) / 2.0 + PLAYER_HALF_WIDTH:
			broken.append("F3: a column can be laid under the player")
	# F3: the fire is honest.
	var band := FRONT_SPEED * BURN
	if BURN >= IFRAMES:
		broken.append("F3: the burn outlasts the i-frames")
	if band < DASH_DISTANCE + 2.0 * PLAYER_HALF_WIDTH + DASH_SLACK - 0.0001:
		broken.append("F3: the burning band %.0f px is under a dash, a body and the slack" % band)
	if CURTAIN_W < CURTAIN_STEPS_MIN * FRONT_SPEED / 60.0 - 0.0001:
		broken.append("F3: the curtain covers a spot for under %d frames" % CURTAIN_STEPS_MIN)
	var going_on := IFRAMES - (DASH_DISTANCE + PLAYER_WALK * (IFRAMES - DASH_SPENT)) / FRONT_SPEED - CAUGHT_SLACK
	if BURN > going_on + 0.0001:
		broken.append("F3: a caught player going on is still in the fire as the i-frames end")
	if WARN >= T_PROJ or ENTRY_LEAD > T_PROJ - FLY_OFF:
		broken.append("F3: the warning or his flight in is outside the projection")
	# F4: the wave's dash window, standing.
	if wave_window() < WAVE_WINDOW_MIN - 0.0001:
		broken.append("F4: the wave's dash window is %.4f s, under %.2f" % [wave_window(), WAVE_WINDOW_MIN])
	if WAVE_H >= DASH_DISTANCE:
		broken.append("F4: the wave is as tall as a dash")
	# F6: rings are dashable and spaced.
	if ring_window() < RING_WINDOW_MIN - 0.0001:
		broken.append("F6: a ring's dash window is %.3f s" % ring_window())
	# The dash straight in at one ring can carry the player a dash nearer the next.
	if RING_SPACING - DASH_DISTANCE / RING_SPEED < DASH_GAP_MIN - 0.0001 or SLAM_GAP_MIN < GLIDE_TIME + SLAM_TELL:
		broken.append("F6: after a dash the next ring is under %.2f s away, or the slams under a glide and a tell" % DASH_GAP_MIN)
	if AFTERSHOCK_DELAY < DASH_GAP_MIN - 0.0001:
		broken.append("F6: the aftershock's ring comes under %.2f s after the wave" % DASH_GAP_MIN)
	if SLAM_TELL < DODGE_TELL_MIN - 0.0001:
		broken.append("F6: a slam's shadow tells for under %.2f s" % DODGE_TELL_MIN)
	# F7: walking beats the pull; the bite is parry-only and reactable.
	if PLAYER_WALK - PULL_SPEED < NET_ESCAPE_MIN - 0.0001:
		broken.append("F7: walking away nets under %.0f px/s" % NET_ESCAPE_MIN)
	var early_drift := PULL_SPEED * minf(REACTION, PULL_RAMP) * minf(REACTION, PULL_RAMP) / (2.0 * PULL_RAMP)
	if early_drift > REACTION_DRIFT_MAX:
		broken.append("F7: %.0f px of drift during a reaction" % early_drift)
	if AIR_START_MIN - R_MAW.x <= REACTION_DRIFT_MAX:
		broken.append("F7: the start is inside the maw's reach")
	if MAWS[0].distance_to(MAWS[1]) < 2.0 * AIR_START_MIN:
		broken.append("F7: a start can be under AIR_START_MIN from both maws")
	if not is_equal_approx(BITE_TELL, BITE_REAR + BITE_LUNGE) or BITE_TELL < PARRY_WINDOW or BITE_TELL - PARRY_WINDOW > REACTION \
			or BITE_TELL < PARRY_TELL_MIN - 0.0001:
		broken.append("F7: the bite's tell %.2f doesn't leave a reaction inside the parry window" % BITE_TELL)
	# F8: the second bite is a read of its own: a hit on the first never hides it (its contact comes after the i-frames),
	# and a press on the first's badge that misses never locks out a press on the second's.
	if SECOND_BITE_GAP + BITE_TELL < IFRAMES + CAUGHT_SLACK or SECOND_BITE_GAP < PARRY_MASH_LOCKOUT or SECOND_BITE_GAP < RECOIL_TIME:
		broken.append("F8: the second bite's badge %.2f s after the first lands is inside a hit's i-frames or a press's mash lockout" % SECOND_BITE_GAP)
	if PULL_START + PULL_TIME > 2.9 + 0.0001:
		broken.append("F7: the pull runs into the bite's badge")
	return broken


# F4: standing, no walk credit, MARGIN off: how long a dash's immunity has to carry a body through the band.
static func wave_window() -> float:
	return (DASH_DISTANCE - WAVE_H - PLAYER_HURT_HEIGHT - MARGIN) / WAVE_SPEED + WAVE_IMMUNITY


# F6: across a ring, sideways.
static func ring_window() -> float:
	return (DASH_DISTANCE + RING_SPEED * DASH_IMMUNITY - 2.0 * RING_HALF_WIDTH - 2.0 * PLAYER_HALF_WIDTH - MARGIN) / RING_SPEED


static func assert_invariants() -> void:
	var broken := invariants()
	assert(broken.is_empty(), "JordanWheelLayout: %s" % [broken])
