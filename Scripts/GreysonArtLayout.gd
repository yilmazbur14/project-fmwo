extends RefCounted

# Every number that depends on how Greyson is drawn and heard, so a redraw or a re-record only needs this file.
# Points and boxes are in texels on one of his frames, origin top-left.
#
# HIS BODY'S ORIGIN IS HIS FEET, as Danny's and Captain Burak's are: every spot GreysonStateMachine names is a
# feet point, and every sheet stands his soles on the node.
#
# UNTIL HIS FIGHT SHEETS LAND he is the approved design sheet, greyson_redesign.png: 2 frames of 112x112 with the
# feet at (56,111), f0 the ready stance and f1 a front double biceps, and every animation below is one of those
# two frames (PLACEHOLDER_ANIMS). Each sheet of the plan's art list (section 7) gets its flag in USE_FINAL_ANIMS,
# looked up by the animation's whole name first and then by its first word, and nothing loads a final sheet while
# its flag is off. A final row for a sheet that isn't 112x112 with the feet at (56,111) carries `frame` and `feet`.
#
# THE OFFSET FOLLOWS THE SHEET, NEVER THE ANIMATION (GreysonScript._stand_on). The cannon-arm sheets are
# asymmetric, so they are drawn facing screen-right and flip with him where their row says `flips`. A FLIPPED
# POINT MIRRORS AS A TEXEL, x becoming frame width - 1 - x, which is where the flipped sprite draws it.
#
# HIS SOUNDS are the approved set (the sound agent's make_greyson_sfx.py), keyed by their names without the
# "greyson_" prefix. Until coder A ships them into Assets/Audio/SFX, each key plays its `stand_in`, and the body
# picks whichever of the two exists (GreysonScript._build_sfx).

const ComputahLayout := preload("res://Scripts/ComputahArtLayout.gd")

const SCALE := 3.0

#GREYSON (horizontal strips, soles on the feet row, the feet on the centre column)
const FRAME_SIZE := Vector2(112, 112)
const ANCHOR := Vector2(56, 111)
# Stands the bottom edge of ANCHOR's row on the sprite's origin. Comes to (0, -56).
const SPRITE_OFFSET := Vector2(FRAME_SIZE.x / 2.0 - ANCHOR.x, FRAME_SIZE.y / 2.0 - ANCHOR.y - 1.0)
const SHEET_DIR := "res://Assets/Characters/Greyson/"
# The approved design (art_source/greyson_redesign/APPROVED.md).
const DESIGN_SHEET := SHEET_DIR + "greyson_redesign.png"

# What the player can punch and turns to face. `idle` is every standing pose on the design sheet: his head and
# torso from the crown to the soles, the lats' flare and the arms left out (132 x 258 px). A box is mirrored with
# him (GreysonScript.set_body_box).
const BODY_BOXES := {
	&"idle": Rect2(34, 26, 44, 86),
}
# The frame and feet of a box drawn on a sheet that isn't 112x112 with the feet at (56,111).
const BODY_BOX_FRAMES := {}

# POINTS are keyed by sheet (USE_FINAL_ANIMS' keys), each one point for the whole sheet or one a sheet frame, and
# each has its stand-in on the design sheet for a sheet whose flag is off. They are the artists' reports: the
# attack set's anchors, gp_export.py's and gf_ship.py's printouts, and the coordinator's takeover anchors; the
# crowns of attach, roar and barbell_pull were measured off the sheets the way gf_ship.py measures (the top of the
# head in columns 40-72).
# The top of his head over its middle column, where the badges and the daze stars stand.
const CROWNS := {
	&"walk": [Vector2(56, 28), Vector2(56, 27), Vector2(56, 26), Vector2(56, 28), Vector2(56, 27), Vector2(56, 26)],
	&"talk": Vector2(56, 26),
	&"tear": [Vector2(55, 28), Vector2(58, 30), Vector2(59, 30), Vector2(61, 27), Vector2(56, 26)],
	&"attach": Vector2(56, 26),
	&"walk_cannon": [Vector2(56, 28), Vector2(56, 27), Vector2(56, 26), Vector2(56, 28), Vector2(56, 27), Vector2(56, 26)],
	&"talk_cannon": Vector2(56, 26),
	&"roar": Vector2(56, 26),
	&"barbell_pull": Vector2(56, 26),
	&"idle": [Vector2(56, 26), Vector2(56, 25), Vector2(56, 25), Vector2(56, 26)],
	&"throw": Vector2(56, 26),
	&"teleport": [Vector2(56, 30), Vector2(56, 33), Vector2(56, 25)],
	&"slam": [Vector2(56, 26), Vector2(56, 25), Vector2(56, 27), Vector2(56, 31), Vector2(56, 28)],
	&"hit": [Vector2(52, 25), Vector2(54, 26)],
	&"broken": [Vector2(53, 28), Vector2(56, 29), Vector2(59, 28), Vector2(56, 30)],
	&"defeat": [Vector2(50, 26), Vector2(54, 30), Vector2(55, 37), Vector2(56, 39), Vector2(55, 40)],
	&"victory": [Vector2(56, 24), Vector2(56, 26), Vector2(56, 23), Vector2(56, 26)],
	&"pose_a": Vector2(56, 26),
	&"pose_b": Vector2(56, 26),
	&"pose_c": Vector2(56, 26),
	&"pose_hit": [Vector2(54, 26), Vector2(56, 26)],
	&"spirit": [Vector2(56, 26), Vector2(56, 26), Vector2(56, 26), Vector2(57, 28)],
	&"hurl": [Vector2(52, 33), Vector2(56, 27), Vector2(62, 28), Vector2(56, 26)],
}
const PLACEHOLDER_CROWN := Vector2(56, 26)
# Where a plate leaves his hand on the throw's RELEASE frame (f2).
const RELEASES := {&"throw": Vector2(88, 87)}
const PLACEHOLDER_RELEASE := Vector2(90, 88)
# Where the barbell's plate meets the mat on the slam's IMPACT frame (f3).
const IMPACTS := {&"slam": Vector2(89, 111)}
const PLACEHOLDER_IMPACT := Vector2(90, 111)
# The cannon's muzzle centre, where the glow sits and the spirit bomb forms. Before the attach the cannon is in his
# fist, not on his arm, so attach f0 carries f1's.
const MUZZLES := {
	&"attach": [Vector2(100.4, 29.8), Vector2(100.4, 29.8), Vector2(97, 28)],
	&"idle": [Vector2(98, 95), Vector2(98, 94), Vector2(99, 94), Vector2(99, 95)],
	&"throw": [Vector2(100, 95), Vector2(102, 93), Vector2(100, 92), Vector2(100, 94)],
	&"teleport": [Vector2(97, 97), Vector2(95, 100), Vector2(98, 93)],
	&"slam": [Vector2(82, 12), Vector2(72, 16), Vector2(95, 44), Vector2(93, 89), Vector2(99, 94)],
	&"hit": [Vector2(100, 92), Vector2(98, 94)],
	&"broken": [Vector2(94, 97), Vector2(95, 97), Vector2(96, 97), Vector2(95, 97)],
	&"defeat": [Vector2(101, 91), Vector2(95, 98), Vector2(96, 106), Vector2(96, 106), Vector2(96, 106)],
	&"victory": [Vector2(97, 27), Vector2(97, 28), Vector2(97, 27), Vector2(97, 28)],
	&"pose_a": [Vector2(16, 76), Vector2(8, 67), Vector2(8, 67)],
	&"pose_b": [Vector2(98, 40), Vector2(97, 28), Vector2(97, 28)],
	&"pose_c": [Vector2(13, 15), Vector2(10, 7), Vector2(12, 7)],
	&"pose_hit": [Vector2(102, 93), Vector2(98, 95)],
	&"spirit": [Vector2(82, 7), Vector2(82, 7), Vector2(82, 7), Vector2(66, 70)],
}
const PLACEHOLDER_MUZZLES := {&"spirit": Vector2(99, 34), &"roar": Vector2(99, 34)}
const PLACEHOLDER_MUZZLE := Vector2(90, 88)
# His grip: the tear's fist on Computah's arm (f0-3) and held up (f4), the attach's with the prop on it, the
# barbell's hand and then its bar grip, and the fight sheets' free hand.
const HANDS := {
	&"tear": [Vector2(18.5, 85), Vector2(18.5, 85), Vector2(18.5, 85), Vector2(18.5, 85), Vector2(15.5, 37)],
	&"attach": [Vector2(15.5, 37), Vector2(15.5, 37), Vector2(15.5, 37)],
	&"barbell_pull": [Vector2(27.5, 38), Vector2(44.5, 61.5), Vector2(44.5, 61.5)],
	&"idle": [Vector2(41, 58), Vector2(41, 56), Vector2(41, 55), Vector2(41, 57)],
	&"throw": [Vector2(19, 37), Vector2(37, 19), Vector2(57, 63), Vector2(62, 72)],
	&"teleport": [Vector2(41, 60), Vector2(41, 63), Vector2(41, 55)],
	&"slam": [Vector2(32, 18), Vector2(41, 17), Vector2(60, 61), Vector2(64, 75), Vector2(62, 73)],
	&"hit": [Vector2(39, 56), Vector2(40, 57)],
	&"broken": [Vector2(24, 89), Vector2(25, 89), Vector2(26, 89), Vector2(25, 89)],
	&"defeat": [Vector2(38, 56), Vector2(24, 91), Vector2(24, 99), Vector2(24, 99), Vector2(24, 99)],
	&"victory": [Vector2(15, 35), Vector2(15, 36), Vector2(15, 35), Vector2(15, 36)],
	# The fist Computah hangs from: his collar on the grab, the tumble's grip on the heave and the release. The
	# recovery holds nothing, and keeps the release's.
	&"hurl": [Vector2(15.5, 94), Vector2(28.5, 27), Vector2(46.5, 29), Vector2(46.5, 29)],
}
const PLACEHOLDER_HAND := Vector2(90, 88)
# His mouth on the roar's open frames, where greyson_roar's FX sits.
const ROAR_MOUTH := Vector2(56, 50)
# Where the finisher's daze stars circle and a badge's tip stands, over his crown.
const DAZE_GAP := 34.0
const TELL_GAP := 12.0

#ANIMATIONS
# name: sheet, frames in order, seconds on each (the last value repeats) and whether it loops. Optional: `frame`
# and `feet` for a sheet that isn't 112x112 with the feet at (56,111); `flips` for a sheet he mirrors with, drawn
# facing screen-right unless `drawn_left` says it faces left; and `motion`, the AnimationPlayer clip in
# GreysonScene that moves the whole sprite under it. A pose a state holds for its own time is a one-frame loop, so
# the state's next animation replaces it at once (play_state_anim).
# The flags, one a sheet, looked up by the animation's longest name that has one (talk_cannon_show goes by
# talk_cannon, not talk). All shipped, all on: the takeover set (art_source/greyson_fight/gf_ship.py's timings), the
# poses (art_source/greyson_poses/gp_export.py's) and the attack set (the artist's anchors report).
const USE_FINAL_ANIMS := {
	&"walk": true,
	&"talk": true,
	&"tear": true,
	&"attach": true,
	&"walk_cannon": true,
	&"talk_cannon": true,
	&"roar": true,
	&"barbell_pull": true,
	&"idle": true,
	&"throw": true,
	&"teleport": true,
	&"slam": true,
	&"pose_a": true,
	&"pose_b": true,
	&"pose_c": true,
	&"pose_hit": true,
	&"spirit": true,
	&"hit": true,
	&"broken": true,
	&"defeat": true,
	&"victory": true,
	&"hurl": true,
}

const WALK_SHEET := SHEET_DIR + "greyson_walk.png"
const TALK_SHEET := SHEET_DIR + "greyson_talk.png"
const TEAR_SHEET := SHEET_DIR + "greyson_tear.png"
const ATTACH_SHEET := SHEET_DIR + "greyson_attach.png"
const WALK_CANNON_SHEET := SHEET_DIR + "greyson_walk_cannon.png"
const TALK_CANNON_SHEET := SHEET_DIR + "greyson_talk_cannon.png"
const ROAR_SHEET := SHEET_DIR + "greyson_roar.png"
const PULL_SHEET := SHEET_DIR + "greyson_barbell_pull.png"
const IDLE_SHEET := SHEET_DIR + "greyson_idle.png"
const THROW_SHEET := SHEET_DIR + "greyson_throw.png"
const TELEPORT_SHEET := SHEET_DIR + "greyson_teleport.png"
const SLAM_SHEET := SHEET_DIR + "greyson_slam.png"
const POSE_A_SHEET := SHEET_DIR + "greyson_pose_a.png"
const POSE_B_SHEET := SHEET_DIR + "greyson_pose_b.png"
const POSE_C_SHEET := SHEET_DIR + "greyson_pose_c.png"
const POSE_HIT_SHEET := SHEET_DIR + "greyson_pose_hit.png"
const SPIRIT_SHEET := SHEET_DIR + "greyson_spirit.png"
const HIT_SHEET := SHEET_DIR + "greyson_hit.png"
const BROKEN_SHEET := SHEET_DIR + "greyson_broken.png"
const DEFEAT_SHEET := SHEET_DIR + "greyson_defeat.png"
const VICTORY_SHEET := SHEET_DIR + "greyson_victory.png"
const HURL_SHEET := SHEET_DIR + "greyson_hurl.png"

# The talk sheets' mouth pairs (shut, open), flapped at TALK_FLAP while one of his lines types: before the cannon
# grief, fond and fury, the upset line's three beats; with it the smug stance and the smug show.
const TALK_FLAP := 0.12

const FINAL_ANIMS := {
	# THE TAKEOVER, before the cannon. He walks facing the camera (Burak's convention), the contacts on 0 and 3.
	&"walk": {sheet = WALK_SHEET, frames = [0, 1, 2, 3, 4, 5], times = [0.10], loop = true, flips = true},
	&"talk_grief": {sheet = TALK_SHEET, frames = [0, 1], times = [TALK_FLAP], loop = true},
	&"talk_grief_shut": {sheet = TALK_SHEET, frames = [0], times = [1.0], loop = true},
	&"talk_fond": {sheet = TALK_SHEET, frames = [2, 3], times = [TALK_FLAP], loop = true},
	&"talk_fond_shut": {sheet = TALK_SHEET, frames = [2], times = [1.0], loop = true},
	&"talk_fury": {sheet = TALK_SHEET, frames = [4, 5], times = [TALK_FLAP], loop = true},
	&"talk_fury_shut": {sheet = TALK_SHEET, frames = [4], times = [1.0], loop = true},
	# The one-handed tear, drawn with Computah on his left: the grip, the strain alternated under the shake, the
	# RIP, and the arm held up to the end of the beat.
	&"tear_grip": {sheet = TEAR_SHEET, frames = [0], times = [0.25], loop = false, flips = true, drawn_left = true},
	&"tear_strain": {sheet = TEAR_SHEET, frames = [1, 2], times = [0.08], loop = true, flips = true, drawn_left = true},
	&"tear_rip": {sheet = TEAR_SHEET, frames = [3], times = [0.15], loop = false, flips = true, drawn_left = true},
	&"tear_hold": {sheet = TEAR_SHEET, frames = [4], times = [1.0], loop = true, flips = true, drawn_left = true},
	# The prop on his fist, the CLANK under the shake and the green flicker, then the flex into the cannon-arm set.
	&"attach": {sheet = ATTACH_SHEET, frames = [0, 1, 2], times = [0.30, 0.25, 0.45], loop = false, flips = true,
		drawn_left = true},
	# The hurl (GreysonTakeover._hurl), the cannon on, drawn with Computah on his left and thrown over his head to the
	# right: the grab, the heave overhead, the release, and the recovery, which is talk_cannon's first frame.
	&"hurl_grab": {sheet = HURL_SHEET, frames = [0], times = [0.30], loop = false, flips = true, drawn_left = true},
	&"hurl_heave": {sheet = HURL_SHEET, frames = [1], times = [0.45], loop = false, flips = true, drawn_left = true},
	&"hurl_release": {sheet = HURL_SHEET, frames = [2], times = [0.15], loop = false, flips = true, drawn_left = true},
	&"hurl_recover": {sheet = HURL_SHEET, frames = [3], times = [0.35], loop = false, flips = true, drawn_left = true},
	# THE TAKEOVER, with the cannon.
	&"walk_cannon": {sheet = WALK_CANNON_SHEET, frames = [0, 1, 2, 3, 4, 5], times = [0.10], loop = true, flips = true},
	&"talk_cannon_stance": {sheet = TALK_CANNON_SHEET, frames = [0, 1], times = [TALK_FLAP], loop = true},
	&"talk_cannon_stance_shut": {sheet = TALK_CANNON_SHEET, frames = [0], times = [1.0], loop = true},
	&"talk_cannon_show": {sheet = TALK_CANNON_SHEET, frames = [2, 3], times = [TALK_FLAP], loop = true},
	&"talk_cannon_show_shut": {sheet = TALK_CANNON_SHEET, frames = [2], times = [1.0], loop = true},
	# The inhale, the roar alternated under the shake, and the settle held.
	&"roar_inhale": {sheet = ROAR_SHEET, frames = [0], times = [0.40], loop = false},
	&"roar": {sheet = ROAR_SHEET, frames = [1, 2], times = [0.06], loop = true},
	&"roar_settle": {sheet = ROAR_SHEET, frames = [3], times = [1.0], loop = true},
	# The barbell out; its last frame is the fight idle's first.
	&"barbell_pull": {sheet = PULL_SHEET, frames = [0, 1, 2], times = [0.15, 0.15, 0.20], loop = false},
	# THE FIGHT, drawn facing right. The throw's RELEASE frame (f2) starts at 0.35 s and the slam's IMPACT frame (f3)
	# at 0.40 s; teleport_in is the out frames backwards.
	&"idle": {sheet = IDLE_SHEET, frames = [0, 1, 2, 3], times = [0.20, 0.16, 0.20, 0.16], loop = true, flips = true},
	&"throw": {sheet = THROW_SHEET, frames = [0, 1, 2, 3], times = [0.27, 0.08, 0.10, 0.16], loop = false, flips = true},
	# Plates 2 and 3: the wind-up again from its second frame (coder B's Throw).
	&"throw_again": {sheet = THROW_SHEET, frames = [1, 2, 3], times = [0.08, 0.10, 0.16], loop = false, flips = true},
	&"teleport_out": {sheet = TELEPORT_SHEET, frames = [0, 1, 2], times = [0.10, 0.10, 0.05], loop = false, flips = true},
	&"teleport_in": {sheet = TELEPORT_SHEET, frames = [2, 1, 0], times = [0.05, 0.10, 0.10], loop = false, flips = true},
	&"slam": {sheet = SLAM_SHEET, frames = [0, 1, 2, 3, 4], times = [0.15, 0.20, 0.05, 0.14, 0.16], loop = false,
		flips = true},
	&"hit": {sheet = HIT_SHEET, frames = [0, 1], times = [0.08, 0.14], loop = false, flips = true},
	&"broken": {sheet = BROKEN_SHEET, frames = [0, 1, 2, 3], times = [0.20, 0.16, 0.20, 0.16], loop = true, flips = true},
	&"defeat": {sheet = DEFEAT_SHEET, frames = [0, 1, 2, 3, 4], times = [0.10, 0.16, 0.14, 0.20, 0.40], loop = false,
		flips = true},
	&"victory": {sheet = VICTORY_SHEET, frames = [0, 1, 2, 3], times = [0.14, 0.12, 0.14, 0.12], loop = true,
		flips = true},
	# THE POSES, to the crowd, never flipped: the 0.3 s strike, then the hold's frames f1 f2 f1 through its 1.2 s.
	&"pose_a": {sheet = POSE_A_SHEET, frames = [0, 1, 2, 1], times = [0.30, 0.40], loop = false},
	&"pose_b": {sheet = POSE_B_SHEET, frames = [0, 1, 2, 1], times = [0.30, 0.40], loop = false},
	&"pose_c": {sheet = POSE_C_SHEET, frames = [0, 1, 2, 1], times = [0.30, 0.40], loop = false},
	# Knocked out of the pose, then annoyed, held to that pose's end.
	&"pose_hit": {sheet = POSE_HIT_SHEET, frames = [0, 1], times = [0.12, 1.0], loop = false},
	# The spirit bomb: the arm up (0-0.5 s), held through the gather, the grin (3.0 s), the THROW (3.5 s on).
	&"spirit": {sheet = SPIRIT_SHEET, frames = [0, 1], times = [0.50, 1.0], loop = false},
	&"spirit_grin": {sheet = SPIRIT_SHEET, frames = [2], times = [1.0], loop = true},
	&"spirit_throw": {sheet = SPIRIT_SHEET, frames = [3], times = [1.0], loop = true},
}

# The stand-ins, off the design sheet: f0 the ready stance, f1 the double biceps. Each holds its frame for about
# as long as the state that plays it waits, so a state times itself the same way on either.
const PLACEHOLDER_ANIMS := {
	# Before the cannon: the walk in, his upset lines, the tear and the attach.
	&"walk": {sheet = DESIGN_SHEET, frames = [0], times = [1.0], loop = true},
	&"talk_grief": {sheet = DESIGN_SHEET, frames = [0], times = [1.0], loop = true},
	&"talk_grief_shut": {sheet = DESIGN_SHEET, frames = [0], times = [1.0], loop = true},
	&"talk_fond": {sheet = DESIGN_SHEET, frames = [0], times = [1.0], loop = true},
	&"talk_fond_shut": {sheet = DESIGN_SHEET, frames = [0], times = [1.0], loop = true},
	&"talk_fury": {sheet = DESIGN_SHEET, frames = [0], times = [1.0], loop = true},
	&"talk_fury_shut": {sheet = DESIGN_SHEET, frames = [0], times = [1.0], loop = true},
	&"tear_grip": {sheet = DESIGN_SHEET, frames = [1], times = [0.25], loop = false},
	&"tear_strain": {sheet = DESIGN_SHEET, frames = [1], times = [1.0], loop = true},
	&"tear_rip": {sheet = DESIGN_SHEET, frames = [1], times = [0.15], loop = false},
	&"tear_hold": {sheet = DESIGN_SHEET, frames = [1], times = [1.0], loop = true},
	&"attach": {sheet = DESIGN_SHEET, frames = [1], times = [1.0], loop = false},
	# The fight, all with the cannon arm.
	&"idle": {sheet = DESIGN_SHEET, frames = [0], times = [1.0], loop = true},
	&"walk_cannon": {sheet = DESIGN_SHEET, frames = [0], times = [1.0], loop = true},
	&"talk_cannon_stance": {sheet = DESIGN_SHEET, frames = [0], times = [1.0], loop = true},
	&"talk_cannon_stance_shut": {sheet = DESIGN_SHEET, frames = [0], times = [1.0], loop = true},
	&"talk_cannon_show": {sheet = DESIGN_SHEET, frames = [1], times = [1.0], loop = true},
	&"talk_cannon_show_shut": {sheet = DESIGN_SHEET, frames = [1], times = [1.0], loop = true},
	&"roar_inhale": {sheet = DESIGN_SHEET, frames = [0], times = [0.40], loop = false},
	&"roar": {sheet = DESIGN_SHEET, frames = [1], times = [1.0], loop = true},
	&"roar_settle": {sheet = DESIGN_SHEET, frames = [1], times = [1.0], loop = true},
	&"barbell_pull": {sheet = DESIGN_SHEET, frames = [0], times = [0.5], loop = false},
	&"throw": {sheet = DESIGN_SHEET, frames = [0], times = [1.0], loop = true},
	&"throw_again": {sheet = DESIGN_SHEET, frames = [0], times = [0.34], loop = false},
	&"teleport_out": {sheet = DESIGN_SHEET, frames = [0], times = [0.25], loop = false},
	&"teleport_in": {sheet = DESIGN_SHEET, frames = [0], times = [0.25], loop = false},
	&"slam": {sheet = DESIGN_SHEET, frames = [1], times = [1.0], loop = true},
	&"pose_a": {sheet = DESIGN_SHEET, frames = [1], times = [1.0], loop = true},
	&"pose_b": {sheet = DESIGN_SHEET, frames = [1], times = [1.0], loop = true},
	&"pose_c": {sheet = DESIGN_SHEET, frames = [1], times = [1.0], loop = true},
	&"pose_hit": {sheet = DESIGN_SHEET, frames = [0], times = [1.0], loop = true},
	&"spirit": {sheet = DESIGN_SHEET, frames = [1], times = [1.0], loop = true},
	&"spirit_grin": {sheet = DESIGN_SHEET, frames = [1], times = [1.0], loop = true},
	&"spirit_throw": {sheet = DESIGN_SHEET, frames = [1], times = [1.0], loop = true},
	&"hit": {sheet = DESIGN_SHEET, frames = [0], times = [0.2], loop = false},
	&"broken": {sheet = DESIGN_SHEET, frames = [0], times = [1.0], loop = true},
	&"defeat": {sheet = DESIGN_SHEET, frames = [0], times = [0.5], loop = false},
	&"victory": {sheet = DESIGN_SHEET, frames = [1, 0], times = [0.5], loop = true},
}

#FX (scratchpad/greyson_fx/FX_FOR_CODER.md, APPROVED and shipped 2026-09-24)
# Horizontal strips at SCALE, never rotated, except the bomb and its orbs, which are grids read row by row (frame n
# is column n % hframes, row n / hframes). `offset` is the frame's centre minus its pivot, for a centred Sprite2D
# on that pivot; flip_h doesn't mirror an offset, so its x is negated when one flips (flipped_offset). The screen
# layers (`screen = true`) are 640x360, drawn top-left at (0,0) at SCALE, under the HUD.
# `plate` and `zone` also carry the gameplay numbers coder B's scripts had in their LAYOUT constants: the plate's
# hit circle is the artist's 27 px (its 18-texel width), and the zone's hurt ellipse is the user's rx 480 x ry 350
# (after playtesting the plan's 380 x 280), which the mark's ring is drawn to exactly. The cannon's glow has no
# art: it stays code, one alpha a level of his hype meter, 0 to 6.
const FX_DIR := SHEET_DIR + "FX/"
const FX := {
	# In flight, spinning in its frames; a hit drops it (drop_time: no art), a parry plays the shared parry flash.
	&"plate": {texture = FX_DIR + "greyson_plate.png", hframes = 6, frame_time = 0.04, loop = true,
		offset = Vector2(0, 1), radius = 27.0, drop_time = 0.3},
	# At each rope contact, on the contact point.
	&"plate_bounce": {texture = FX_DIR + "greyson_plate_bounce.png", hframes = 4, frame_time = 0.04, loop = false,
		offset = Vector2.ZERO},
	# After the last bounce, where the plate was.
	&"plate_vanish": {texture = FX_DIR + "greyson_plate_vanish.png", hframes = 5, frame_time = 0.05, loop = false,
		offset = Vector2.ZERO},
	# The zone's hurt ellipse round its centre, px, and its beats: the yellow ring from ring_lead out (the mark's
	# stage 3), and a fizzle's fade. At this size a zone spills past the ropes almost anywhere, so what it draws is
	# cut to the floor (global px): the mark to the floor inside the ropes, the burst to that floor run up to the
	# screen's top, so its flames stand in front of the crowd. The hurt ellipse is never cut.
	&"zone": {radii = Vector2(480, 350), ring_lead = 0.6, ring_slack = 0.05, fizzle_time = 0.25,
		mark_clip = Rect2(93, 114, 1734, 873), burst_clip = Rect2(93, 0, 1734, 987)},
	# The mark, on the zone's centre: f0-1 planted, then a pair a stage (dim, violet, white-hot), throbbing at that
	# stage's beat; stage 3 is the rush. A third of the fuse a stage, for example.
	&"erupt_mark": {texture = FX_DIR + "greyson_erupt_mark.png", hframes = 8, offset = Vector2(0, -4),
		planted = [0, 1], planted_time = 0.07, stages = [[2, 3], [4, 5], [6, 7]], stage_times = [0.3, 0.22, 0.17]},
	# The eruption on the same centre, once; it hurts on hurt_frames.
	&"erupt_burst": {texture = FX_DIR + "greyson_erupt_burst.png", hframes = 7, frame_time = 0.05, loop = false,
		offset = Vector2(0, -22), hurt_frames = [1, 2, 3]},
	# Where the barbell's plate hits the floor, as it hits.
	&"slam": {texture = FX_DIR + "greyson_slam.png", hframes = 6, frame_time = 0.05, loop = false,
		offset = Vector2(0, -10)},
	# On his feet: his sprite shows under the out sheet's f0 and hides from its f1, and shows again from the in
	# sheet's f3 (GreysonScript.teleport_out / teleport_in).
	&"teleport_out": {texture = FX_DIR + "greyson_teleport_out.png", hframes = 6, frame_time = 0.05, loop = false,
		offset = Vector2(0, -56), hide_from = 1},
	&"teleport_in": {texture = FX_DIR + "greyson_teleport_in.png", hframes = 6, frame_time = 0.05, loop = false,
		offset = Vector2(0, -56), show_from = 3},
	# On his mouth; f2-5 loop to hold the roar.
	&"roar": {texture = FX_DIR + "greyson_roar.png", hframes = 6, frame_time = 0.06, offset = Vector2.ZERO,
		hold = [2, 3, 4, 5]},
	# Its ring starts at screen (960, 260) with his feet at the top of the arena; with a camera shake.
	&"roar_screen": {texture = FX_DIR + "greyson_roar_screen.png", hframes = 6, frame_time = 0.08, loop = false,
		screen = true},
	# The sphere, its pivot on the cannon's muzzle: f0-15 grow across the 2.5 s gather, then f16-19 shimmer.
	&"bomb": {texture = FX_DIR + "greyson_bomb.png", hframes = 5, vframes = 4, offset = Vector2(0, -182),
		grow = 16, shimmer = [16, 17, 18, 19], shimmer_time = 0.08, diameter = 1032.0},
	# The crowd's energy: a row a size (small, medium, large, extra large), four frames each.
	&"bomb_orb": {texture = FX_DIR + "greyson_bomb_orb.png", hframes = 4, vframes = 4, frame_time = 0.1,
		offset = Vector2.ZERO},
	# Over the arena and UNDER the fighters, faded in with the growth; the fighters' modulate eases to fighter_tint.
	&"bomb_light": {texture = FX_DIR + "greyson_bomb_light.png", hframes = 1, screen = true,
		fighter_tint = Color(0.8, 0.88, 1.0)},
	# The explosion, once, centred on the screen; its white flashes are f0, f3 and f6 only.
	&"bomb_screen": {texture = FX_DIR + "greyson_bomb_screen.png", hframes = 10, screen = true,
		times = [0.10, 0.15, 0.15, 0.10, 0.15, 0.15, 0.10, 0.25, 0.35, 0.35]},
	# On the player, over the screen layer, a row a facing: it replaces the code dissolve.
	&"player_disintegrate": {texture = FX_DIR + "player_disintegrate.png", hframes = 12, vframes = 4, frame_time = 0.08,
		rows = {&"down": 0, &"up": 1, &"left": 2, &"right": 3}},
	&"cannon_glow": {radius = 15.0, points = 16, color = Color("#9FE8FF"), alphas = [0.0, 0.15, 0.3, 0.45, 0.6, 0.75, 0.9]},
}

#THE HUD
# The hints (GreysonScript.show_hint): bottom centre on his HUD layer, above the player's bars, each once a fight.
# `bottom` is the text's bottom edge in screen px.
const HINT := {font_size = 33, outline = 6, color = Color("#F2F3FF"), outline_color = Color("#1A0D26"), width = 1100.0,
	bottom = 924.0, fade = 0.2}
# His hype meter (GreysonHypeMeterUI, coder C's): beside his boss bar, its top-left at screen `at`, well away from
# the player's HYPE at the bottom right. The approved parts, the _3x copies, positioned in 1x texels times SCALE:
# cell k at cell_at + (cell_step * k, 0), its pop at pop_at + (cell_step * k, 0), and the full frames over the frame.
const UI_DIR := "res://Assets/UI/"
const HYPE_METER := {at = Vector2(1212, 97), size = Vector2(240, 60),
	frame = UI_DIR + "greyson_hype_frame_3x.png",
	cell = UI_DIR + "greyson_hype_cell_3x.png", cell_at = Vector2(75, 15), cell_step = 24.0,
	pop = UI_DIR + "greyson_hype_pop_3x.png", pop_hframes = 3, pop_frame_time = 0.05, pop_at = Vector2(69, 9),
	full = UI_DIR + "greyson_hype_full_3x.png", full_hframes = 2, full_frame_time = 0.2}
# The bar's sweep to full at the bar swap, and how long the HUD takes to come and go.
const HUD_SWEEP_TIME := 0.8
const HUD_FADE_TIME := 0.25

#THE JUGGLE (the Break's tiered uppercut; BossJuggled reads exactly this shape)
# greyson_juggle.png, the artist's anchors: 12 frames of 192x144, facing right, flipping with him (the cannon swaps
# arms, as on his other rows). floor_y() comes to about 518, under HOME's 560, so a Break never slides him down, and
# his headroom at HOME is about 197 px. Its frame is not his 112x112, so its texels go through
# BossJuggled.texel_point(), never frame_local().
const USE_FINAL_JUGGLE := true
const FINAL_JUGGLE := {
	"texture": SHEET_DIR + "greyson_juggle.png",
	"hframes": 12,
	"frame_size": Vector2(192, 144),
	"offset": Vector2(0, -72),
	"feet": Vector2(96, 143),
	"tumble_centre": Vector2(96, 85),
	"top_row": 26,
	"clips": {
		&"launch": {"frames": [0, 1], "times": [0.06, 0.08], "loop": false},
		&"tumble": {"frames": [2, 3, 4, 5, 6], "times": [0.16, 0.07, 0.07, 0.07, 0.07], "loop": true},
		&"crash": {"frames": [7, 8, 9], "times": [0.06, 0.08, 0.12], "loop": false},
		&"down": {"frames": [10, 11], "times": [0.4, 0.4], "loop": true},
	},
	"shadow": {
		"texture": SHEET_DIR + "greyson_leap_shadow.png",
		"hframes": 3, "scale": 3.0, "alpha": 0.35, "step": 100.0, "offset": Vector2.ZERO,
	},
	"lying_time": 0.3,
	"outro_delay": 1.8,
	"crash_sfx": {"stream": "res://Assets/Audio/SFX/eric_crash_thud.wav", "pitch": 1.0, "volume_db": 0.0},
}
# The stand-in the juggle drew on before its sheet shipped, with the contract's frame and top_row 24.
const PLACEHOLDER_JUGGLE := {
	"texture": DESIGN_SHEET,
	"hframes": 2,
	"frame_size": Vector2(192, 144),
	"offset": Vector2(0, -72),
	"feet": Vector2(96, 143),
	"tumble_centre": Vector2(96, 86),
	"top_row": 24,
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
	"crash_sfx": {"stream": "res://Assets/Audio/SFX/eric_crash_thud.wav", "pitch": 1.0, "volume_db": 0.0},
}

#THE HURL (the takeover throwing the armless Computah out of the ring, GreysonTakeover._hurl)
# His hurl rows and Computah's tumble (ComputahArtLayout.ARMLESS_TUMBLE), once both sheets are in; until they are
# imported - they shipped ahead of it - the stand-ins: three of his tear rows, which lack the cannon, and
# Computah's own frame as he lay turned a quarter a step, which keeps its pixels square.
const USE_FINAL_HURL := true
const HURL_STAND_INS := {&"hurl_grab": &"tear_grip", &"hurl_heave": &"tear_rip", &"hurl_release": &"tear_rip",
	&"hurl_recover": &"tear_hold"}
const PLACEHOLDER_HURL_TUMBLE := {step = 0.08, turn = 90.0}

#AUDIO
# The approved set, each file at a -3 dBFS peak, so `volume_db` is the whole mix: the sound agent's proposed
# levels against hit_impact at -17. A key with `streams` plays its variants in turn. `loop` keys are the two
# loops, which a hazard plays on a player of its own (GreysonScript.sfx_player_for). Until the files ship, each
# plays its stand-in at the stand-in's own pitch and level. The last keys are the plan's, which the approved set
# has no sound for: stand-ins only.
const SFX_DIR := "res://Assets/Audio/SFX/"
const SFX := {
	# The takeover.
	&"shout": {stream = SFX_DIR + "greyson_shout.wav", volume_db = -3.5,
		stand_in = SFX_DIR + "matt_roar.wav", stand_in_pitch = 1.3, stand_in_db = -6.0},
	&"cannon_rip": {stream = SFX_DIR + "greyson_cannon_rip.wav", volume_db = 1.5,
		stand_in = SFX_DIR + "carter_parry_break.wav", stand_in_pitch = 0.8, stand_in_db = 0.0},
	&"cannon_clamp": {stream = SFX_DIR + "greyson_cannon_clamp.wav", volume_db = 1.5,
		stand_in = SFX_DIR + "burak_clang.wav", stand_in_pitch = 0.7, stand_in_db = 0.0},
	&"roar": {stream = SFX_DIR + "greyson_roar.wav", volume_db = 1.5,
		stand_in = SFX_DIR + "bixby_roar.wav", stand_in_pitch = 1.0, stand_in_db = 0.0},
	# Attack 1.
	&"plate_throw": {stream = SFX_DIR + "greyson_plate_throw.wav", volume_db = -4.5,
		stand_in = SFX_DIR + "whirlwind_whoosh.ogg", stand_in_pitch = 1.4, stand_in_db = 0.0},
	&"plate_spin": {stream = SFX_DIR + "greyson_plate_spin.wav", volume_db = -9.5, loop = true,
		stand_in = SFX_DIR + "laser_charge.ogg", stand_in_pitch = 1.6, stand_in_db = -18.0},
	&"plate_bounce": {streams = [SFX_DIR + "greyson_plate_bounce_1.wav", SFX_DIR + "greyson_plate_bounce_2.wav",
		SFX_DIR + "greyson_plate_bounce_3.wav"], volume_dbs = [-1.0, -2.0, -2.5],
		stand_in = SFX_DIR + "burak_clang.wav", stand_in_pitch = 1.2, stand_in_db = -6.0},
	&"plate_parry": {stream = SFX_DIR + "greyson_plate_parry.wav", volume_db = -1.5,
		stand_in = SFX_DIR + "burak_barrel_tonk.wav", stand_in_pitch = 0.8, stand_in_db = 0.0},
	&"barbell_slam": {stream = SFX_DIR + "greyson_barbell_slam.wav", volume_db = 1.0,
		stand_in = SFX_DIR + "earthquake_slam.ogg", stand_in_pitch = 1.0, stand_in_db = 0.0},
	# The same slam under the name the brawl plan calls it by: its debris cut's slams, and the KO thud at 0.8.
	&"slam": {stream = SFX_DIR + "greyson_barbell_slam.wav", volume_db = 1.0,
		stand_in = SFX_DIR + "earthquake_slam.ogg", stand_in_pitch = 1.0, stand_in_db = 0.0},
	&"teleport_out": {stream = SFX_DIR + "greyson_teleport_out.wav", volume_db = -5.0,
		stand_in = SFX_DIR + "matt_teleport_out.wav", stand_in_pitch = 1.0, stand_in_db = 0.0},
	&"teleport_in": {stream = SFX_DIR + "greyson_teleport_in.wav", volume_db = -3.5,
		stand_in = SFX_DIR + "matt_teleport_in.wav", stand_in_pitch = 1.0, stand_in_db = 0.0},
	&"eruption_rumble": {stream = SFX_DIR + "greyson_eruption_rumble.wav", volume_db = -3.5, loop = true,
		stand_in = SFX_DIR + "laser_charge.ogg", stand_in_pitch = 0.5, stand_in_db = -16.0},
	&"eruption_blast": {stream = SFX_DIR + "greyson_eruption_blast.wav", volume_db = 2.0,
		stand_in = SFX_DIR + "burak_blast.wav", stand_in_pitch = 0.9, stand_in_db = 0.0},
	# The poses.
	&"flex": {stream = SFX_DIR + "greyson_flex.wav", volume_db = -3.0,
		stand_in = SFX_DIR + "matt_roar.wav", stand_in_pitch = 1.6, stand_in_db = -10.0},
	&"crowd_cheer": {stream = SFX_DIR + "crowd_cheer.wav", volume_db = -1.0,
		stand_in = SFX_DIR + "finisher_bar_1.wav", stand_in_pitch = 1.2, stand_in_db = -6.0},
	&"crowd_boo": {stream = SFX_DIR + "crowd_boo.wav", volume_db = -3.0,
		stand_in = SFX_DIR + "carter_spent.wav", stand_in_pitch = 1.2, stand_in_db = 0.0},
	# The spirit bomb.
	&"spirit_charge": {stream = SFX_DIR + "greyson_spirit_charge.wav", volume_db = -1.5,
		stand_in = SFX_DIR + "laser_charge.ogg", stand_in_pitch = 0.4, stand_in_db = 0.0},
	&"spirit_launch": {stream = SFX_DIR + "greyson_spirit_launch.wav", volume_db = 1.0,
		stand_in = SFX_DIR + "rocket_launch.ogg", stand_in_pitch = 0.7, stand_in_db = 0.0},
	&"spirit_explosion": {stream = SFX_DIR + "greyson_spirit_explosion.wav", volume_db = 2.5,
		stand_in = SFX_DIR + "burak_blast.wav", stand_in_pitch = 0.6, stand_in_db = 0.0},
	&"disintegrate": {stream = SFX_DIR + "greyson_disintegrate.wav", volume_db = -1.0,
		stand_in = SFX_DIR + "laser_charge.ogg", stand_in_pitch = 2.5, stand_in_db = -8.0},
	# The brawl (the brawl plan's).
	&"brawl_debris": {stream = SFX_DIR + "greyson_brawl_debris.wav", volume_db = 1.0,
		stand_in = SFX_DIR + "earthquake_slam.ogg", stand_in_pitch = 0.6, stand_in_db = 0.0},
	&"brawl_hook": {stream = SFX_DIR + "greyson_brawl_hook.wav", volume_db = -4.5,
		stand_in = SFX_DIR + "punch_whoosh.wav", stand_in_pitch = 0.8, stand_in_db = 0.0},
	&"brawl_straight": {stream = SFX_DIR + "greyson_brawl_straight.wav", volume_db = -7.0,
		stand_in = SFX_DIR + "punch_whoosh.wav", stand_in_pitch = 1.1, stand_in_db = 0.0},
	&"brawl_hit": {stream = SFX_DIR + "greyson_brawl_hit.wav", volume_db = 1.5,
		stand_in = SFX_DIR + "hit_impact.ogg", stand_in_pitch = 0.9, stand_in_db = -4.0},
	&"brawl_dodge": {stream = SFX_DIR + "greyson_brawl_dodge.wav", volume_db = -7.5,
		stand_in = SFX_DIR + "punch_whoosh.wav", stand_in_pitch = 1.4, stand_in_db = -6.0},
	&"brawl_tell": {stream = SFX_DIR + "greyson_brawl_tell.wav", volume_db = -7.5,
		stand_in = SFX_DIR + "finisher_bar_1.wav", stand_in_pitch = 1.5, stand_in_db = -8.0},
	&"brawl_tell_parry": {stream = SFX_DIR + "greyson_brawl_tell_parry.wav", volume_db = -8.0,
		stand_in = SFX_DIR + "finisher_bar_1.wav", stand_in_pitch = 0.8, stand_in_db = -8.0},
	# The barbell tossed into the rubble: the whoosh of its 0.22 s flight from the fling (GreysonFinalBrawl._fling),
	# handing over to its crash as it lands, at the crash's t=0.
	&"brawl_toss_whoosh": {stream = SFX_DIR + "greyson_brawl_toss_whoosh.wav", volume_db = -3.5,
		stand_in = SFX_DIR + "punch_whoosh.wav", stand_in_pitch = 0.6, stand_in_db = 0.0},
	&"brawl_toss": {stream = SFX_DIR + "greyson_brawl_toss.wav", volume_db = 0.5,
		stand_in = SFX_DIR + "burak_clang.wav", stand_in_pitch = 0.8, stand_in_db = 0.0},
	# The takeover's hurl: his grunt from the grab, bursting on the heave; the whoosh from the release, dulling
	# off-screen; the crash out there as he leaves the screen, with no crowd in it (the takeover's cheer is its
	# own). Their stand-ins are the set's own flex, barbell toss whoosh and barbell toss crash.
	&"hurl_grab": {stream = SFX_DIR + "greyson_hurl_grab.wav", volume_db = -8.0,
		stand_in = SFX_DIR + "greyson_flex.wav", stand_in_pitch = 0.9, stand_in_db = -3.0},
	&"hurl_whoosh": {stream = SFX_DIR + "greyson_hurl_whoosh.wav", volume_db = -6.0,
		stand_in = SFX_DIR + "greyson_brawl_toss_whoosh.wav", stand_in_pitch = 1.0, stand_in_db = -3.5},
	&"hurl_crash": {stream = SFX_DIR + "greyson_hurl_crash.wav", volume_db = -1.5,
		stand_in = SFX_DIR + "greyson_brawl_toss.wav", stand_in_pitch = 1.0, stand_in_db = 0.5},
	# The takeover's footsteps, the left foot and the right in turn, and the tear's sparks.
	&"stomp": {streams = [SFX_DIR + "greyson_stomp_1.wav", SFX_DIR + "greyson_stomp_2.wav"], volume_dbs = [0.5, 0.0],
		stand_in = SFX_DIR + "matt_stomp.wav", stand_in_pitch = 1.2, stand_in_db = -8.0},
	&"spark": {stream = SFX_DIR + "greyson_spark.wav", volume_db = 0.0,
		stand_in = SFX_DIR + "laser_charge.ogg", stand_in_pitch = 2.0, stand_in_db = -12.0},
	# The slam's wind-up, peaking on GreysonSlams.windup_time (0.40 s).
	&"slam_windup": {stream = SFX_DIR + "greyson_slam_windup.wav", volume_db = -7.5,
		stand_in = SFX_DIR + "wrestler_charge.ogg", stand_in_pitch = 0.8, stand_in_db = 0.0},
	# A plate that hit, knocked down: its clang lands on the drop's floor, 0.30 s in (fx plate's drop_time).
	&"plate_drop": {stream = SFX_DIR + "greyson_plate_drop.wav", volume_db = -2.5,
		stand_in = SFX_DIR + "burak_barrel_tonk.wav", stand_in_pitch = 0.8, stand_in_db = 0.0},
	&"pose_bank": {stream = SFX_DIR + "greyson_pose_bank.wav", volume_db = -7.0,
		stand_in = SFX_DIR + "finisher_bar_1.wav", stand_in_pitch = 1.2, stand_in_db = 0.0},
	&"pose_spoiled": {stream = SFX_DIR + "greyson_pose_spoiled.wav", volume_db = -9.0,
		stand_in = SFX_DIR + "carter_spent.wav", stand_in_pitch = 1.2, stand_in_db = 0.0},
	# The cannon's hum, a loop by its own points, from the attach on: this level on a full meter, and
	# CANNON_HUM's ramp below it (GreysonScript._tune_cannon_hum).
	&"cannon_hum": {stream = SFX_DIR + "greyson_cannon_hum.wav", volume_db = -12.5, loop = true,
		stand_in = SFX_DIR + "finisher_charge_loop.wav", stand_in_pitch = 0.6, stand_in_db = -14.0},
	# The doom orb (GreysonDoomOrb), from sounds already in the game: the glass giving as a hit bursts it, and his stomp,
	# played low (DOOM_ORB.thump_pitch), as the vignette's heartbeat.
	&"orb_burst": {stream = SFX_DIR + "matt_glass_shatter.wav", volume_db = -4.0,
		stand_in = SFX_DIR + "carter_parry_break.wav", stand_in_pitch = 1.0, stand_in_db = -4.0},
	&"orb_thump": {stream = SFX_DIR + "greyson_stomp_1.wav", volume_db = -9.0,
		stand_in = SFX_DIR + "matt_stomp.wav", stand_in_pitch = 1.0, stand_in_db = -12.0},
}
# The hum under his meter, the sound agent's ramp: this many dB quieter on an empty meter than on a full one, and
# its pitch from x (empty) to y (full).
const CANNON_HUM := {quieter_empty = 14.0, pitch = Vector2(0.85, 1.3)}

#THE DOOM ORB (GreysonDoomOrb; the user's 2026-09-30 playtest: the poses, his meter and the spirit bomb made plain,
# with no text)
# His hype meter made physical over his head: a spirit-bomb orb that forms at his first banked cell and grows a stage
# a cell, the crowd's energy streaking into it on each bank, a vignette and a heartbeat from vignette_from on, a burst
# when a hit empties his meter, and the camera nudging to him the first time it forms in a fight.
const USE_DOOM_ORB := true
# The approved art, used once its files exist (the art pass drops them in FX_DIR; its contract.json has the numbers
# for DOOM_ORB_FINAL). Until the orb's own sheet exists, the placeholders in DOOM_ORB; each other sheet is used once it
# exists too (the glow and the vignette are extras the placeholders do without).
const DOOM_ORB_ART := {orb = FX_DIR + "greyson_doom_orb.png", glow = FX_DIR + "greyson_doom_orb_glow.png",
	burst = FX_DIR + "greyson_doom_orb_burst.png", streak = FX_DIR + "greyson_hype_streak.png",
	vignette = FX_DIR + "greyson_doom_vignette.png"}
# The approved sheets as the art pass's contract has them (art_source/greyson_doom_orb/approval/contract.json,
# 2026-09-30), in texels at SCALE:
#   orb: a row a stage (1-6), `frames` frames of frame_size each - loop_frames its pulse, at the stage's frame_time,
#     and flash_frame shown once for flash_time as the stage banks - its pivot the orb's FOOT, the bottom of its
#     sphere, the same on every stage, so it grows upward off one point over his head; `radii` the sphere a stage.
#     The glow: the same grid, pivot and frame, drawn additively under it.
#   burst: a row per size (row 0 for stages under burst_big_from, row 1 from it) of burst_frames frames, pivot its
#     centre, placed on the orb's centre, once at burst_frame_times.
#   streak: streak_rows rows, a heading each, 360/streak_rows degrees apart from row 0 flying right (row 4 down), of
#     streak_frames frames, its head on the pivot, its tail drawn behind it; the row picked from its velocity.
#   vignette: one 640x360 frame, a screen layer.
#   The hand-off: stage 6 f0 is greyson_bomb's handoff_bomb_frame less the muzzle's beam; through his arm going up
#     the orb's foot goes to the muzzle + handoff_lift px, and the bomb gathers on from that frame.
const DOOM_ORB_FINAL := {frames = 5, loop_frames = [0, 1, 2, 3], flash_frame = 4, frame_size = Vector2(72, 72),
	pivot = Vector2(36, 56), radii = [5.0, 7.0, 9.0, 11.0, 13.0, 19.0],
	frame_times = [0.14, 0.13, 0.12, 0.11, 0.10, 0.09], flash_time = 0.08,
	burst_rows = 2, burst_big_from = 4, burst_frames = 6, burst_frame_size = Vector2(96, 96), burst_pivot = Vector2(48, 48),
	burst_frame_times = [0.05, 0.06, 0.05, 0.06, 0.07, 0.08],
	streak_rows = 16, streak_frames = 4, streak_frame_size = Vector2(40, 40), streak_pivot = Vector2(20, 20),
	streak_frame_time = 0.05,
	handoff_bomb_frame = 1, handoff_lift = Vector2(0, -9)}
const DOOM_ORB := {
	# Stages 1-6 on the placeholder, the bomb_orb sheet's rows (10, 16, 26 and 40 texels across) at whole-number
	# scales, [row, scale], near the approved sheet's sizes (30, 42, 54, 66, 78 and 114 px across). Two banks' cells
	# show it at stage 2 first (bank 2). Stage 6 is his spirit bomb itself, which takes over from the orb as it fires.
	stages = [[0, 3], [1, 3], [2, 2], [2, 3], [3, 2], [3, 3]],
	# The orb's foot, the bottom of its sphere, this far over his crown (the contract's 6 px: at HOME, (960, 296)),
	# kept clear of the HUD's keep-out (HUD_FADE_RECT) and inside the screen, pushed down behind his head rather than
	# over the bar.
	gap = 6.0,
	# While the player's body box overlaps it, it fades to this, so it never hides them.
	player_fade = 0.4,
	# The placeholder's throb a stage: brighter this much at the peak, this often (s). The approved sheet pulses in
	# its own frames.
	pulse_times = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4],
	pulse_bright = 0.35,
	# The bomb's own light on the floor under it (bomb_light), this strong a stage (the art pass: 0.1, 0.3 and 0.5
	# read fine at HOME).
	light_alphas = [0.1, 0.1, 0.3, 0.3, 0.5, 0.5],
	# The placeholder's purple crackle from crackle_from on: bolts at a time, how often, how long each shows, its
	# colour. The approved sheet crackles in its own frames.
	crackle_from = 3, crackle_bolts = 2, crackle_every = 0.35, crackle_time = 0.08, crackle_color = Color("#C77DFF"),
	# On each bank, streaks from the crowd (the stands across the top, and ringside down each side) into it over
	# streak_time, set off inside streak_spread; it grows as they land. On the placeholder, each is one of the bomb's
	# own crowd orbs (bomb_orb's row streak_row, at SCALE) with a trail.
	streaks = 12, streak_time = 0.4, streak_spread = 0.12, streak_arc = 60.0, streak_tail = 90.0, streak_width = 8.0,
	streak_color = Color("#B35CFF"), streak_head = Color("#E9D2FF"), streak_row = 0,
	crowd_top = Rect2(150, 20, 1620, 70), crowd_sides = Rect2(20, 200, 1880, 700),
	# The crowd's cheer this much louder a banked cell (dB).
	cheer_gain_db = 1.0,
	# The vignette from vignette_from on (the contract's): its alpha a stage from there, and bomb_vignette as the
	# spirit bomb starts; the heartbeat every heartbeat_every s lifts it heartbeat_bump for heartbeat_hold s, easing
	# back over heartbeat_ease s, with the thump at thump_pitch. The placeholder's own gradient (vignette_color, up
	# to vignette_edge at the screen's edges) stands in for greyson_doom_vignette.
	vignette_from = 4, vignette_alphas = [0.5, 0.75], bomb_vignette = 1.0, vignette_color = Color(0.36, 0.06, 0.52),
	vignette_edge = 0.6,
	heartbeat_every = 0.9, heartbeat_bump = 0.25, heartbeat_hold = 0.12, heartbeat_ease = 0.3, thump_pitch = 0.55,
	# A hit that empties his meter: the placeholder's pop (greyson_hype_pop, at the whole-number scale nearest the
	# orb), this long a frame, and the streaks flung back out to the crowd.
	burst_frame_time = 0.07,
	# The meter up top flashing with each growth and throb, so the two read as one thing.
	meter_flash = Color(1.6, 1.3, 1.9),
	# The first time it forms in a fight: the view eases this much closer on him over nudge_in, holds, and eases back.
	nudge = true, nudge_zoom = 1.12, nudge_in = 0.2, nudge_hold = 0.15, nudge_out = 0.25,
}
# How many players a sound gets, for the ones that overlap with themselves: a voice a plate for the throw's six,
# and three for the blasts, 1.55 s long and never under 0.8 s apart.
const SFX_VOICES := {&"plate_throw": 6, &"plate_bounce": 6, &"plate_parry": 6, &"plate_drop": 6, &"eruption_blast": 3,
	&"stomp": 2, &"flex": 2}
# "Two Bars", the fight's theme since Computah's half (art_source/music/greyson_theme.rb), restarted at the bar swap.
# It loops by its own import.
const THEME := "res://Assets/Audio/Music/greyson_theme.wav"
const THEME_DB := -7.0


# The sheet an animation is drawn from, as USE_FINAL_ANIMS names them: its longest name that has a flag
# (talk_cannon_show is talk_cannon's, pose_hit its own), or &"" for none.
static func sheet_key(anim_name: StringName) -> StringName:
	var parts := String(anim_name).split("_")
	for n in range(parts.size(), 0, -1):
		var key := StringName("_".join(parts.slice(0, n)))
		if USE_FINAL_ANIMS.has(key):
			return key
	return &""


static func uses_final(anim_name: StringName) -> bool:
	return USE_FINAL_ANIMS.get(sheet_key(anim_name), false)


static func anim(anim_name: StringName) -> Dictionary:
	if uses_final(anim_name) and FINAL_ANIMS.has(anim_name):
		return FINAL_ANIMS[anim_name]
	return PLACEHOLDER_ANIMS.get(anim_name, PLACEHOLDER_ANIMS[&"idle"])


# Seconds one pass over an animation's frames takes.
static func loop_length(spec: Dictionary) -> float:
	var times: Array = spec.times
	var total := 0.0
	for i in spec.frames.size():
		total += times[mini(i, times.size() - 1)]
	return total


# `spec` with its timings scaled so one pass over its frames takes `loop_time`.
static func timed(spec: Dictionary, loop_time: float) -> Dictionary:
	var scale := loop_time / loop_length(spec)
	var times: Array = []
	for i in spec.frames.size():
		times.append(spec.times[mini(i, spec.times.size() - 1)] * scale)
	var out := spec.duplicate()
	out.times = times
	return out


static func frame_size(spec: Dictionary) -> Vector2:
	return spec.get("frame", FRAME_SIZE)


# What stands a sheet's feet on the node.
static func sheet_offset(spec: Dictionary) -> Vector2:
	var frame := frame_size(spec)
	var feet: Vector2 = spec.get("feet", ANCHOR)
	return Vector2(frame.x / 2.0 - feet.x, frame.y / 2.0 - feet.y - 1.0)


# Position from his feet, in px, of a point on a frame of `spec`'s sheet: the scaling is on his sprite, so it is
# already applied here.
static func frame_local(point: Vector2, spec: Dictionary) -> Vector2:
	return (point - frame_size(spec) / 2.0 + sheet_offset(spec)) * SCALE


# A texel of `anim_name`'s frames from his feet, in px, drawn flipped or not.
static func texel_local(point: Vector2, anim_name: StringName, flip := false) -> Vector2:
	var spec := anim(anim_name)
	if flip:
		point.x = frame_size(spec).x - 1.0 - point.x
	return frame_local(point, spec)


# A body box in px from his feet, drawn unflipped, on its own frame (BODY_BOX_FRAMES) or a 112x112 one.
static func body_rect(key: StringName) -> Rect2:
	var box: Rect2 = BODY_BOXES.get(key, BODY_BOXES[&"idle"])
	return Rect2(frame_local(box.position, BODY_BOX_FRAMES.get(key, {})), box.size * SCALE)


# Each point on `anim_name`'s sheet, on its sheet frame `frame`, or on the animation's first frame at -1.
static func crown(anim_name: StringName, frame := -1) -> Vector2:
	return _point(CROWNS, PLACEHOLDER_CROWN, anim_name, frame)


static func release(anim_name: StringName, frame := -1) -> Vector2:
	return _point(RELEASES, PLACEHOLDER_RELEASE, anim_name, frame)


static func impact(anim_name: StringName, frame := -1) -> Vector2:
	return _point(IMPACTS, PLACEHOLDER_IMPACT, anim_name, frame)


static func muzzle(anim_name: StringName, frame := -1) -> Vector2:
	return _point(MUZZLES, PLACEHOLDER_MUZZLES.get(anim_name, PLACEHOLDER_MUZZLE), anim_name, frame)


static func hand(anim_name: StringName, frame := -1) -> Vector2:
	return _point(HANDS, PLACEHOLDER_HAND, anim_name, frame)


static func _point(finals: Dictionary, placeholder: Vector2, anim_name: StringName, frame: int) -> Vector2:
	var key := sheet_key(anim_name)
	if not uses_final(anim_name) or not finals.has(key):
		return placeholder
	var point = finals[key]
	if point is Array:
		var at: int = frame if frame >= 0 else int(anim(anim_name).frames[0])
		return point[clampi(at, 0, point.size() - 1)]
	return point


# Whether a sheet frame of `anim_name`'s is drawn mirrored when he faces left: the rows that flip, against the
# way they were drawn.
static func mirrored(anim_name: StringName, facing_left: bool) -> bool:
	var spec := anim(anim_name)
	return spec.get("flips", false) and facing_left != spec.get("drawn_left", false)


static func fx(key: StringName) -> Dictionary:
	return FX[key]


# An offset off a centred sheet's middle, kept on its pivot when the sheet flips.
static func flipped_offset(offset: Vector2, flip_h: bool) -> Vector2:
	return Vector2(-offset.x if flip_h else offset.x, offset.y)


static func juggle() -> Dictionary:
	return FINAL_JUGGLE if USE_FINAL_JUGGLE else PLACEHOLDER_JUGGLE


# Whether the hurl plays on its own sheets: on, and both imported.
static func uses_final_hurl() -> bool:
	return USE_FINAL_HURL and ResourceLoader.exists(HURL_SHEET) and ResourceLoader.exists(ComputahLayout.ARMLESS_TUMBLE.texture)


# The row the hurl's `anim_name` plays: its own, or its stand-in.
static func hurl_anim(anim_name: StringName) -> StringName:
	return anim_name if uses_final_hurl() else HURL_STAND_INS[anim_name]
