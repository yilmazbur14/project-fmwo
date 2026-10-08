extends RefCounted

# Every number that depends on how Matt is drawn, so a redraw only needs this file. Points and boxes
# are in texels on one of his 96x96 frames, origin top-left.
#
# HIS BODY'S ORIGIN IS HIS FEET, as Carter's is: FLOOR_POINT is (0, 0) and every sheet stands his
# soles on row 95 over it, so frame_local() returns px from his feet, and every spot and station
# MattStateMachine names is a feet point. MattScript applies this file at runtime; the values in
# MattScene are copies for the editor. His sprite's offset is set once and never per animation: the
# finisher's recoil tweens it and settles it back to whatever it was.
#
# Each sheet has its own flag: placeholder and final art go through the same code, so the fight is
# playable before the sheets land and turning a flag off brings the placeholder back. Nothing loads a
# final sheet while its flag is off. The placeholders are the approved matt.png - frame 0 the idle,
# frame 1 the roar - with an AnimationPlayer clip in MattScene moving the whole sprite under them.
# Every flag is on: the artists' intro set, fight set, Trueshot side and back views and FX all landed
# on 2026-09-23, and the Glass Row's body, player and FX sheets the same evening.
#
# A FLIPPED POINT MIRRORS AS A TEXEL, x becoming 95 - x, which is where the flipped sprite draws it.
#
# FX HEADINGS: every directional effect is drawn travelling right and down only, at Godot's angles (y
# down), and art_frame() flips it into the other three quadrants: flip_h when it goes left, flip_v when
# it goes up. The code never rotates a drawn frame. Every FX sheet is a centred sprite, so a flip mirrors
# its texture inside its own rect; the bolt's and the streak's pivots are off their frames' centres, so
# their offsets are negated under each flip to keep the pivot put.

const SCALE := 3.0

#MATT (horizontal strips of 96x96 frames, soles on row 95, x = 48 his centre line)
const FRAME_SIZE := Vector2(96, 96)
const ANCHOR := Vector2(48, 95)
# Stands the bottom edge of ANCHOR's row on the sprite's origin. Comes to (0, -48).
const SPRITE_OFFSET := Vector2(FRAME_SIZE.x / 2.0 - ANCHOR.x, FRAME_SIZE.y / 2.0 - ANCHOR.y - 1.0)
const FLOOR_POINT := Vector2(0, 0)
const MATT_SHEET := "res://Assets/Characters/Matt/matt.png"
const SHEET_DIR := "res://Assets/Characters/Matt/"
const FX_DIR := "res://Assets/Characters/Matt/FX/"

# What the player can punch and turns to face: the recover pose's body, bent over with his fists on his
# knees, arms in and the crest's spikes out (the artist's box). 189 x 213 px.
const BODY_BOX := Rect2(17, 25, 63, 71)

# The top of his crest and the middle of his mouth, per animation, for the ones whose final sheet is on:
# the badges and the daze stars stand over the crest, and every bolt, wave and yell leaves the mouth -
# the spawn texel on the frame it leaves on. The Trueshot's side view fires from one texel past his
# cupped hands and the back view from three texels over his head (the artist's anchors).
const PLACEHOLDER_CROWN := Vector2(48, 3)
# 135 px over his feet on the stand-in.
const PLACEHOLDER_MOUTH := Vector2(48, 51)
const CROWNS := {
	&"idle": Vector2(48, 1),
	&"teleport_out": Vector2(48, 7),
	&"teleport_in": Vector2(48, 7),
	&"mystic_windup": Vector2(48, 1),
	&"mystic_fire": Vector2(48, 2),
	&"trueshot_charge": Vector2(48, 1),
	&"trueshot_fire": Vector2(48, 2),
	&"trueshot_charge_side": Vector2(48, 1),
	&"trueshot_fire_side": Vector2(48, 1),
	&"trueshot_charge_back": Vector2(48, 1),
	&"trueshot_fire_back": Vector2(48, 1),
	&"spent": Vector2(48, 2),
	&"recover": Vector2(48, 13),
	&"hit": Vector2(46, 8),
	&"yell_tell": Vector2(48, 1),
	&"roar_inhale": Vector2(48, 1),
	&"roar": Vector2(48, 1),
	&"defeat": Vector2(48, 13),
	# The Glass Row's, off the frame each animation holds: the stomp's knee-high tell and its recoil, the
	# fury's first step, and the yell up at the ceiling's head tipped back.
	&"stomp_tell": Vector2(51, 1),
	&"stomp_slam": Vector2(48, 3),
	&"fury": Vector2(50, 1),
	&"yell_up_tell": Vector2(48, 14),
	&"yell_up": Vector2(48, 14),
	# The Echo Roars (matt_echo.png, the artist's anchors), off the frame each holds: the inhale, the psych's laugh,
	# the wind-up and the blast's hold.
	&"echo_inhale": Vector2(48, 1),
	&"echo_psych": Vector2(48, 2),
	&"boomburst_windup": Vector2(48, 1),
	&"boomburst_blast": Vector2(48, 5),
}
# The roar's is the middle of its open mouth on frame 1, lip line to lip line, which is also where the
# rings and the zoom are centred.
const MOUTHS := {
	&"idle": Vector2(49, 46),
	&"teleport_out": Vector2(48, 51),
	&"teleport_in": Vector2(48, 51),
	&"mystic_windup": Vector2(48, 45),
	&"mystic_fire": Vector2(48, 51),
	&"trueshot_charge": Vector2(48, 45),
	&"trueshot_fire": Vector2(48, 51),
	&"trueshot_charge_side": Vector2(67, 47),
	&"trueshot_fire_side": Vector2(69, 49),
	&"trueshot_charge_back": Vector2(48, 13),
	&"trueshot_fire_back": Vector2(48, 14),
	&"spent": Vector2(48, 46),
	&"recover": Vector2(48, 59),
	&"hit": Vector2(46, 54),
	&"yell_tell": Vector2(48, 44),
	&"roar_inhale": Vector2(48, 44),
	&"roar": Vector2(48, 51),
	&"defeat": Vector2(48, 51),
	&"stomp_tell": Vector2(51, 44),
	&"stomp_slam": Vector2(48, 49),
	&"fury": Vector2(48, 50),
	&"yell_up_tell": Vector2(48, 40),
	# The rings' centre, averaged over the loop's three frames.
	&"yell_up": Vector2(48, 45),
	# The Echo Roars, off the frame each holds. Every ring leaves the roar's mouth (48, 51), which the psych's and the
	# blast's sit within 2 texels of.
	&"echo_inhale": Vector2(48, 43),
	&"echo_psych": Vector2(48, 50),
	&"boomburst_windup": Vector2(48, 43),
	&"boomburst_blast": Vector2(48, 50),
}
# Where the stand-in doll stands in his hand while the doll sheet is off. The drawn sheet has Hong
# baked into his fist.
const DOLL_HAND := Vector2(70, 56)
# Where the finisher's daze stars circle and a badge's tip stands, over his crest.
const DAZE_GAP := 34.0
const TELL_GAP := 12.0

#ANIMATIONS
# name: sheet, frames in order, seconds on each (the last value repeats) and whether it loops.
# Optional: motion, the AnimationPlayer clip in MattScene that moves the whole sprite under the frames.
# The placeholders are single frames and those clips are all the life they have; the final sheets draw
# their own, so they name none and he rests at SCALE, upright (the RESET clip).
const USE_FINAL_ANIMS := {
	&"idle": true,
	&"walk": true,
	&"talk": true,
	&"teleport_out": true,
	&"teleport_in": true,
	&"mystic_windup": true,
	&"mystic_fire": true,
	&"trueshot_charge": true,
	&"trueshot_fire": true,
	&"trueshot_charge_side": true,
	&"trueshot_fire_side": true,
	&"trueshot_charge_back": true,
	&"trueshot_fire_back": true,
	&"spent": true,
	&"recover": true,
	&"hit": true,
	&"yell_tell": true,
	&"roar_inhale": true,
	&"roar": true,
	&"doll_pull": true,
	&"doll_scream": true,
	&"doll_stow": true,
	&"defeat": true,
	&"stomp_tell": true,
	&"stomp_slam": true,
	&"fury": true,
	&"yell_up_tell": true,
	&"yell_up": true,
	# The Echo Roars' sheet (matt_echo.png). Each plays only once its sheet is in (anim()): until then its stand-in.
	&"echo_inhale": true,
	&"echo_psych": true,
	&"boomburst_windup": true,
	&"boomburst_blast": true,
}

const PLACEHOLDER_ANIMS := {
	&"idle": {sheet = MATT_SHEET, frames = [0], times = [1.0], loop = true, motion = &"idle"},
	&"walk": {sheet = MATT_SHEET, frames = [0], times = [1.0], loop = true, motion = &"walk"},
	# He squeezes into a streak and out of one.
	&"teleport_out": {sheet = MATT_SHEET, frames = [0], times = [0.15], loop = false, motion = &"teleport_out"},
	&"teleport_in": {sheet = MATT_SHEET, frames = [0], times = [0.15], loop = false, motion = &"teleport_in"},
	&"mystic_windup": {sheet = MATT_SHEET, frames = [0], times = [0.45], loop = false, motion = &"mystic_windup"},
	# The roar frame is his "HA!".
	&"mystic_fire": {sheet = MATT_SHEET, frames = [1], times = [0.15], loop = false, motion = &"mystic_fire"},
	&"trueshot_charge": {sheet = MATT_SHEET, frames = [0], times = [1.0], loop = true, motion = &"trueshot_charge"},
	&"trueshot_fire": {sheet = MATT_SHEET, frames = [1], times = [0.35], loop = false, motion = &"trueshot_fire"},
	# Standing, and not open: the idle frame.
	&"spent": {sheet = MATT_SHEET, frames = [0], times = [1.0], loop = true, motion = &"spent"},
	# Open: the roar frame bent over and heaving, tongue out, so the punish window has a look of its own.
	&"recover": {sheet = MATT_SHEET, frames = [1], times = [1.0], loop = true, motion = &"recover"},
	&"hit": {sheet = MATT_SHEET, frames = [1], times = [0.19], loop = false},
	&"yell_tell": {sheet = MATT_SHEET, frames = [0], times = [0.4], loop = false, motion = &"yell_tell"},
	&"roar_inhale": {sheet = MATT_SHEET, frames = [0], times = [0.35], loop = false, motion = &"roar_inhale"},
	&"roar": {sheet = MATT_SHEET, frames = [1], times = [1.0], loop = true, motion = &"roar"},
	&"doll_pull": {sheet = MATT_SHEET, frames = [0], times = [0.64], loop = false},
	&"doll_scream": {sheet = MATT_SHEET, frames = [1], times = [1.0], loop = true, motion = &"roar"},
	&"doll_stow": {sheet = MATT_SHEET, frames = [0], times = [0.45], loop = false},
	&"defeat": {sheet = MATT_SHEET, frames = [0], times = [1.0], loop = false, motion = &"defeated"},
	# The Glass Row's stand-ins are his approved sheets: the yell's inhale for the knee coming up and for
	# the head tipping back, the roar for the slam and the yell at the ceiling, and the furious talk pose
	# for the stamping (twice over, so its slam steps sit where the drawn sheet's will).
	&"stomp_tell": {sheet = SHEET_DIR + "matt_yell_tell.png", frames = [0, 1], times = [0.15, 0.30], loop = false},
	&"stomp_slam": {sheet = SHEET_DIR + "matt_roar.png", frames = [1], times = [1.0], loop = false},
	&"fury": {sheet = TALK_SHEET, frames = [14, 15, 14, 15], times = [0.08], loop = true},
	&"yell_up_tell": {sheet = SHEET_DIR + "matt_yell_tell.png", frames = [0, 1], times = [0.25], loop = false},
	&"yell_up": {sheet = SHEET_DIR + "matt_roar.png", frames = [1, 2, 3], times = [0.06], loop = true},
	# The Echo Roars' stand-ins, off his approved sheets: the roar's inhale, the laughing talk pose with its mouth open
	# for the X's "psych!", the Trueshot's charge for the BOOMBURST's wind-up and the roar for its blast. A roar itself
	# is always the roar (matt_roar f1-3).
	&"echo_inhale": {sheet = SHEET_DIR + "matt_roar.png", frames = [0], times = [1.0], loop = false},
	&"echo_psych": {sheet = TALK_SHEET, frames = [3], times = [1.0], loop = false},
	&"boomburst_windup": {sheet = SHEET_DIR + "matt_trueshot_charge.png", frames = [0], times = [1.0], loop = false},
	&"boomburst_blast": {sheet = SHEET_DIR + "matt_roar.png", frames = [1, 2, 3], times = [0.06], loop = true},
}

# The artists' timings. The mystic cast and the teleport are one sheet each, split at the frame the
# state acts on, so the bolt leaves him on the fire frame whatever the frame clock is doing.
const FINAL_ANIMS := {
	&"idle": {sheet = SHEET_DIR + "matt_idle.png", frames = [0, 1, 2, 3], times = [0.16], loop = true},
	# Faces screen-right while he waves to the crowd; it plays straight down his walk-in.
	&"walk": {sheet = SHEET_DIR + "matt_walk.png", frames = [0, 1, 2, 3, 4, 5], times = [0.10], loop = true},
	&"teleport_out": {sheet = SHEET_DIR + "matt_teleport.png", frames = [0, 1, 2], times = [0.05], loop = false},
	&"teleport_in": {sheet = SHEET_DIR + "matt_teleport.png", frames = [3, 4, 5], times = [0.05], loop = false},
	&"mystic_windup": {sheet = SHEET_DIR + "matt_mystic_cast.png", frames = [0, 1], times = [0.225], loop = false},
	&"mystic_fire": {sheet = SHEET_DIR + "matt_mystic_cast.png", frames = [2, 3], times = [0.075], loop = false},
	&"trueshot_charge": {sheet = SHEET_DIR + "matt_trueshot_charge.png", frames = [0, 1, 2, 3], times = [0.12], loop = true},
	&"trueshot_fire": {sheet = SHEET_DIR + "matt_trueshot_fire.png", frames = [0, 1, 2], times = [0.06, 0.08, 1.0], loop = false},
	# The side view is drawn facing screen-right, for the left station; the right one mirrors it.
	&"trueshot_charge_side": {sheet = SHEET_DIR + "matt_trueshot_charge_side.png", frames = [0, 1, 2, 3], times = [0.12], loop = true},
	&"trueshot_fire_side": {sheet = SHEET_DIR + "matt_trueshot_fire_side.png", frames = [0, 1, 2], times = [0.06, 0.08, 1.0], loop = false},
	&"trueshot_charge_back": {sheet = SHEET_DIR + "matt_trueshot_charge_back.png", frames = [0, 1, 2, 3], times = [0.12], loop = true},
	&"trueshot_fire_back": {sheet = SHEET_DIR + "matt_trueshot_fire_back.png", frames = [0, 1, 2], times = [0.06, 0.08, 1.0], loop = false},
	&"spent": {sheet = SHEET_DIR + "matt_spent.png", frames = [0, 1, 2, 3], times = [0.15], loop = true},
	&"recover": {sheet = SHEET_DIR + "matt_recover.png", frames = [0, 1, 2, 3], times = [0.18], loop = true},
	&"hit": {sheet = SHEET_DIR + "matt_hit.png", frames = [0, 1], times = [0.07, 0.12], loop = false},
	&"yell_tell": {sheet = SHEET_DIR + "matt_yell_tell.png", frames = [0, 1], times = [0.20], loop = false},
	&"roar_inhale": {sheet = SHEET_DIR + "matt_roar.png", frames = [0], times = [0.35], loop = false},
	&"roar": {sheet = SHEET_DIR + "matt_roar.png", frames = [1, 2, 3], times = [0.06], loop = true},
	&"doll_pull": {sheet = SHEET_DIR + "matt_doll.png", frames = [0, 1, 2], times = [0.12, 0.12, 0.40], loop = false},
	&"doll_scream": {sheet = SHEET_DIR + "matt_doll.png", frames = [3, 4, 5], times = [0.06], loop = true},
	# Hong back in his pocket and a deep breath out; the forced talk pose holds after it.
	&"doll_stow": {sheet = SHEET_DIR + "matt_doll.png", frames = [6, 7], times = [0.15, 0.30], loop = false},
	# Sat down on his heels hugging Hong, held.
	&"defeat": {sheet = SHEET_DIR + "matt_defeat.png", frames = [0, 1, 2, 3, 4, 5], times = [0.13, 0.11, 0.11, 0.13, 0.18, 1.0], loop = false},
	# The Glass Row. The stomp is one sheet split at the slam: knee rising, knee held high through the
	# tell, then the slam and its recoil, held.
	&"stomp_tell": {sheet = SHEET_DIR + "matt_stomp.png", frames = [0, 1], times = [0.15, 0.30], loop = false},
	&"stomp_slam": {sheet = SHEET_DIR + "matt_stomp.png", frames = [2, 3], times = [0.08, 1.0], loop = false},
	&"fury": {sheet = SHEET_DIR + "matt_fury.png", frames = [0, 1, 2, 3], times = [0.08], loop = true},
	&"yell_up_tell": {sheet = SHEET_DIR + "matt_yell_up.png", frames = [0, 1], times = [0.25], loop = false},
	&"yell_up": {sheet = SHEET_DIR + "matt_yell_up.png", frames = [2, 3, 4], times = [0.06], loop = true},
	# The Echo Roars: one strip, the cupped-hands inhale, the X's "psych!" and the laugh after it, and the BOOMBURST's
	# wind-up, blast and hold.
	&"echo_inhale": {sheet = SHEET_DIR + "matt_echo.png", frames = [0], times = [1.0], loop = false},
	&"echo_psych": {sheet = SHEET_DIR + "matt_echo.png", frames = [1, 2], times = [0.20, 1.0], loop = false},
	&"boomburst_windup": {sheet = SHEET_DIR + "matt_echo.png", frames = [3], times = [1.0], loop = false},
	&"boomburst_blast": {sheet = SHEET_DIR + "matt_echo.png", frames = [4, 5], times = [0.10, 1.0], loop = false},
}
# Whose anchors an animation with no crown or mouth of its own borrows: the Echo Roars' stand-ins', until the artist's
# anchors for matt_echo.png are in.
const BORROWED_ANCHORS := {
	&"echo_inhale": &"roar_inhale",
	&"echo_psych": &"idle",
	&"boomburst_windup": &"trueshot_charge",
	&"boomburst_blast": &"roar",
}

# What each Trueshot station charges and fires in: the front view from the top, the back view from the
# bottom, the side view from the left and, mirrored, from the right. A view whose flag is off falls back
# to the front one, so a station's sheets drop in by data.
const TRUESHOT_STATION_ANIMS := {
	&"top": {charge = &"trueshot_charge", fire = &"trueshot_fire"},
	&"left": {charge = &"trueshot_charge_side", fire = &"trueshot_fire_side"},
	&"bottom": {charge = &"trueshot_charge_back", fire = &"trueshot_fire_back"},
	&"right": {charge = &"trueshot_charge_side", fire = &"trueshot_fire_side"},
}
# The arena draws by y, so a player whose sprite stands higher up the screen than his feet draws under him: on a
# Trueshot station's footprint his 288 px sprite buried them for the whole shot (from the bottom station, a player
# still on their spawn mark, the 2026-10-04 playtest). While the player's sprite overlaps his there, his
# self_modulate alpha eases to this over STATION_SEE_THROUGH_TIME, and back once they are clear
# (MattTrueshotBarrage), the way Carter's beam clones do.
const STATION_SEE_THROUGH := 0.35
const STATION_SEE_THROUGH_TIME := 0.12

#THE GLASS ROW
# Where a stomp lands, by the step of the animation that lands it: the slam's dust and the fury's puffs
# go on that foot. The drawn sheets' feet come with the artist's anchors; until then, and for a sheet
# that is off, the stand-in's.
const SLAM_FEET := {
	&"stomp_slam": {0: Vector2(29, 95)},
	&"fury": {1: Vector2(30, 95), 3: Vector2(66, 95)},
}
const PLACEHOLDER_SLAM_FEET := {
	&"stomp_slam": {0: Vector2(38, 95)},
	&"fury": {1: Vector2(38, 95), 3: Vector2(58, 95)},
}

# The player's poses while he holds them: one sheet in player_4dir_sheet.png's row order (DOWN, UP,
# LEFT, RIGHT), the back view copied into every row, since they only ever face him. Each pose is its
# columns, seconds each (the last for the rest) and whether it loops; a one-shot holds its last column.
const USE_FINAL_PLAYER_POSES := true
const PLAYER_POSE_SHEET := {texture = "res://Assets/Characters/MainPlayer/player_glass_row.png", hframes = 18, vframes = 4}
const PLAYER_POSES := {
	&"rooted": {frames = [0, 1], times = [0.20], loop = true},
	&"brace": {frames = [2], times = [0.12], loop = false},
	# Played over the knock's slide a row down, so it sums to MattStateMachine.boom_knock_time.
	&"knock": {frames = [3, 4, 5], times = [0.03, 0.035, 0.035], loop = false},
	&"ears_in": {frames = [6], times = [0.08], loop = false},
	&"ears": {frames = [7, 8, 9], times = [0.07], loop = true},
	&"resist": {frames = [10, 11], times = [0.12, 1.0], loop = false},
	&"dizzy": {frames = [12, 13, 14, 15], times = [0.14], loop = true},
	&"glass": {frames = [16, 17], times = [0.10, 0.20], loop = false},
}
const PLACEHOLDER_PLAYER_POSE_SHEET := {texture = "res://Assets/Characters/MainPlayer/player_4dir_sheet.png", hframes = 10, vframes = 4}
const PLACEHOLDER_PLAYER_POSES := {
	&"rooted": {frames = [0], times = [1.0], loop = true},
	&"brace": {frames = [9], times = [0.12], loop = false},
	&"knock": {frames = [0], times = [0.10], loop = false},
	&"ears_in": {frames = [9], times = [0.08], loop = false},
	&"ears": {frames = [9], times = [1.0], loop = true},
	&"resist": {frames = [0], times = [1.0], loop = false},
	&"dizzy": {frames = [0], times = [1.0], loop = true},
	&"glass": {frames = [9], times = [0.30], loop = false},
}

# The drag: the player's own frame left along the line in lavender.
const DRAG_GHOSTS := 5
const DRAG_GHOST_TINT := Color("#B3B6F2", 0.55)
const DRAG_GHOST_FADE := 0.25

# The "pillar" and the rows, drawn in code on the floor while a Glass Row runs: a lavender lane with
# dashed edges and faint lines between the rows. No row letters.
const GLASS_GUIDES := {
	lane_tint = Color("#B3B6F2", 0.10), edge = Color("#C4C9FA", 0.45), edge_width = 3.0, dash = 18.0, gap = 12.0,
	row_line = Color("#F2F3FF", 0.18), row_width = 3.0, show_time = 0.30, hide_time = 0.30,
}

# Each arrow's own colour, told apart in greyscale too (the FX artist's measured set).
const ARROW_COLORS := {
	&"up": Color("#FFD93D"), &"right": Color("#38CE7F"), &"down": Color("#349BD7"), &"left": Color("#C6463D"),
}

# What the fight's first Glass Row says under the player, from its first boom until `booms` of them have
# landed and it has been up `min_time`, whichever is later, and never again. One boom at today's pace is
# too short to read it in.
const GLASS_HINT := {
	text = "PRESS THE ARROW BEFORE IT LANDS!", font_size = 33, outline = 6, color = Color("#F2F3FF"),
	outline_color = Color("#332F68"), offset = Vector2(0, 66), fade = 0.2, booms = 3, min_time = 1.5,
}

# The white ring that pops off a player who mashed through the Deafening Yell.
const RESIST_RING := {from_radius = 24.0, to_radius = 120.0, width = 6.0, color = Color("#FFFFFF"), time = 0.30, points = 48}

#THE ECHO ROARS (MattEchoRingScript draws every ring in code, in px)
# A roar is the approved yell ring - its core, flanks and edge, the fainter ring behind - with a rim in his roar red
# outside it; its echo is the same at echo_alpha. A ghost (the X) is the pale steel of Carter's X (demon_feint.png's
# fill and shade), dashed into `arcs` arcs each `fill` of its share of the circle. A punish is hot white, beating
# like Josh's punish glow, with no badge. The BOOMBURST is a gold wall: its bright leading edge, which is all that
# touches, the gold body `depth` behind it and a dark back. A circle gets a point every `chord` px of it.
const ECHO_RINGS := {
	chord = 20.0, min_points = 32, max_points = 330, fade = 0.06, echo_alpha = 0.8,
	red = {core = Color("#F2F3FF"), core_width = 9.0, flank = Color("#C4C9FA"), flank_width = 15.0, edge = Color("#4F4D96"),
		edge_width = 21.0, trail_gap = 36.0, trail_alpha = 0.45, rim = Color("#FF4A58"), rim_width = 6.0, rim_gap = 14.0},
	ghost = {core = Color("#E6ECF2"), core_width = 9.0, edge = Color("#9BADB7"), edge_width = 15.0, arcs = 24, fill = 0.55,
		alpha = 0.5},
	punish = {color = Color("#FFFFFF"), width = 14.0, glow = Color(1.0, 1.0, 1.0, 0.55), glow_width = 36.0, beat = [0.82, 1.18],
		beat_time = 0.07},
	boomburst = {edge = Color("#FFF3A8"), edge_width = 10.0, body = Color("#FFCB3C"), depth = 90.0, inner = Color("#C87414"),
		inner_width = 10.0},
}
# Carter's pale X (Josh's Monte wears it too) over him for a silent roar: stepped through ignite and peak to a hold that
# never pulses, and its fade frame as the ghost is born, gone in `out`. Its tip stands where a badge's would.
const FEINT_MARK := {texture = "res://Assets/Characters/Carter/Demon/demon_feint.png", hframes = 4,
	frame_size = Vector2(24, 24), pivot = Vector2(12, 12), scale = 3.0, steps = {ignite = 0, peak = 1, hold = 2, fade = 3},
	ignite_time = 0.05, peak_time = 0.04, out = 0.05}
# Under the player at the fight's first BOOMBURST, in the Glass Row hint's style: from its yellow badge until
# `hold_after` past its touch.
const ECHO_HINT := {text = "DASH THROUGH THE GOLD!", font_size = 33, outline = 6, color = Color("#F2F3FF"),
	outline_color = Color("#332F68"), offset = Vector2(0, 66), fade = 0.2, hold_after = 1.0}
# What a bitten X puts up beside him, in Josh's and Carter's word style: `offset` from HOME, its x turned the other way
# on every other bite. `box` is the word as drawn, outline included; it must stay clear of `badge_rect` round the
# badge's tip.
const PSYCH_WORD := {text = "PSYCH!", offset = Vector2(-260, -160), time = 0.9, font_size = 92, color = Color(1.0, 0.36, 0.3),
	outline = 10, from_scale = 0.7, to_scale = 1.0, grow_time = 0.16, box = Vector2(300, 100),
	badge_rect = Rect2(-52, -104, 104, 104)}

#THE JUGGLE (the Break's tiered uppercut; BossJuggled reads exactly this shape)
# A sheet of its own: its frame is not his 96x96 and its origin is not his feet, so its texels go through
# BossJuggled.texel_point(), never frame_local(). top_row is the tumble's highest row (frames 2-6).
const USE_FINAL_JUGGLE := true
const FINAL_JUGGLE := {
	"texture": "res://Assets/Characters/Matt/matt_juggle.png",
	"hframes": 12,
	"frame_size": Vector2(192, 144),
	"offset": Vector2(0, -72),
	"feet": Vector2(96, 143),
	"tumble_centre": Vector2(96, 88),
	"top_row": 37,
	"clips": {
		&"launch": {"frames": [0, 1], "times": [0.06, 0.08], "loop": false},
		&"tumble": {"frames": [2, 3, 4, 5, 6], "times": [0.14, 0.07, 0.07, 0.07, 0.07], "loop": true},
		&"crash": {"frames": [7, 8, 9], "times": [0.06, 0.08, 0.12], "loop": false},
		&"down": {"frames": [10, 11], "times": [0.4, 0.4], "loop": true},
	},
	"shadow": {
		"texture": "res://Assets/Characters/Matt/matt_leap_shadow.png",
		"hframes": 3, "scale": 3.0, "alpha": 0.35, "step": 100.0, "offset": Vector2.ZERO,
	},
	"lying_time": 0.3,
	"outro_delay": 1.8,
	"crash_sfx": {"stream": "res://Assets/Audio/SFX/hit_impact.ogg", "pitch": 0.7, "volume_db": 0.0},
}

#TALK POSES
# The poses the lines' `matt` tags name, as the two frames each flaps between: mouth shut, mouth open.
# Only the mouth changes inside a pair, so flapping never jitters the body.
const TALK_FRAME_TIME := 0.12
const TALK_SHEET := SHEET_DIR + "matt_talk.png"
const TALK_POSES := {
	&"friendly": [0, 1],
	&"laugh": [2, 3],
	&"proud": [4, 5],
	&"forced": [6, 7],
	&"irritated": [8, 9],
	&"snap": [10, 11],
	&"sheepish": [12, 13],
	&"furious": [14, 15],
	&"puzzled": [16, 17],
}
# The idle frame for all of them but the snap, which is the roar frame; the `talk` clip is the life.
const PLACEHOLDER_TALK_ROAR_POSES := [&"snap", &"furious"]

#FX
const USE_FINAL_FX := {
	&"bolt": true,
	&"spark": true,
	&"streak": true,
	&"wave": true,
	&"wave_mid": true,
	&"launch": true,
	&"launch_mid": true,
	&"glow": true,
	&"aim_dot": true,
	&"teleport": true,
	&"yell_rings": true,
	&"boom": true,
	&"boom_arrow": true,
	&"boom_burst": true,
	&"glass_floor": true,
	&"glass_glint": true,
	&"glass_shard": true,
	&"glass_shadow": true,
	&"glass_land": true,
	&"glass_shatter": true,
	&"root": true,
	&"stomp_dust": true,
	&"fury_puff": true,
}

# The headings each directional sheet is drawn at, in degrees, in frame order.
const BOLT_ART_ANGLES := [22.5, 45.0, 67.5]
const WAVE_ART_ANGLES := [0.0, 22.5, 45.0, 67.5, 90.0]
# The wave and its launch on an 11.25 degree grid: the even steps are the sheets above, the odd ones
# (11.25, 33.75, 56.25, 78.75) their _mid sheets.
const WAVE_ART_STEP := 11.25
# matt_yell_rings.png's front radius on each frame, in texels: 60 to 270 px at SCALE.
const YELL_RING_RADII := [20, 37, 54, 71, 83, 90]

const FINAL_FX := {
	# 3 headings x 4 flicker frames. Each heading's offset puts its white-hot core - which the hit circle
	# sits on - on the bolt's origin.
	&"bolt": {texture = FX_DIR + "matt_mystic_bolt.png", hframes = 12, frames_per_heading = 4, frame_time = 0.05,
		offsets = [Vector2(-9.5, -3.5), Vector2(-7.5, -7.5), Vector2(-3.5, -9.5)]},
	# Frames 0-5 splash off the top rope (flipped for the bottom), 6-11 off the left (flipped for the right).
	# A bounce plays the first 4 of its six, a fizzle all of them.
	&"spark": {texture = FX_DIR + "matt_mystic_spark.png", hframes = 12, frame_time = 0.04, side_first = 6,
		bounce_frames = 4, fizzle_frames = 6},
	# The faint dark streak on the floor under a bolt, two frames a heading, on the bolt's own offsets.
	&"streak": {texture = FX_DIR + "matt_mystic_streak.png", hframes = 6, frames_per_heading = 2, frame_time = 0.05,
		drop = 24.0, alpha = 0.3},
	# 5 headings x 4 frames, pivoted on its middle.
	&"wave": {texture = FX_DIR + "matt_trueshot_wave.png", hframes = 20, frames_per_heading = 4, frame_time = 0.05},
	# Cyan wisps curling back from where the wave left: 5 headings x 5 frames, once.
	&"launch": {texture = FX_DIR + "matt_trueshot_launch.png", hframes = 25, frames_per_heading = 5, frame_time = 0.05},
	# The in-between headings of both, 11.25 to 78.75, in the same frame order.
	&"wave_mid": {texture = FX_DIR + "matt_trueshot_wave_mid.png", hframes = 16, frames_per_heading = 4, frame_time = 0.05},
	&"launch_mid": {texture = FX_DIR + "matt_trueshot_launch_mid.png", hframes = 20, frames_per_heading = 5,
		frame_time = 0.05},
	# Frames 0-3 grow over the charge up to the lock, 4 is the lock's flash, then 4 and 5 alternate.
	&"glow": {texture = FX_DIR + "matt_trueshot_glow.png", hframes = 6, grow_frames = 4, lock_frame = 4,
		flash_time = 0.06},
	&"aim_dot": {texture = FX_DIR + "matt_aim_dot.png", hframes = 2, spacing = 24.0},
	# A lavender and gold column on his feet, stood on them the way his body sheet is.
	&"teleport": {texture = FX_DIR + "matt_teleport_fx.png", hframes = 6, offset = Vector2(0, -48), frame_time = 0.05},
	&"yell_rings": {texture = FX_DIR + "matt_yell_rings.png", hframes = 7, radii = YELL_RING_RADII, fade_frame = 6,
		fade = 0.06},
	# THE GLASS ROW. Horizontal strips, never flipped. `offset` is the frame's centre minus its pivot, in
	# texels, for a centred sprite, so the node sits on the pivot.
	# The boom forms on f0-2 with its charge, then flickers f3-4 as it flies; its node is the leading apex.
	&"boom": {texture = FX_DIR + "matt_boom.png", hframes = 5, charge_frames = 3, flicker_frames = [3, 4],
		frame_time = 0.05, offset = Vector2(0, -10)},
	# frame = direction * 3 + state.
	&"boom_arrow": {texture = FX_DIR + "matt_boom_arrow.png", hframes = 12, directions = [&"up", &"right", &"down", &"left"],
		states = [&"live", &"answered", &"cracked"], offset = Vector2.ZERO},
	# On the player's hurtbox centre: f0-3 when it breaks on a brace, f4-7 when it lands.
	&"boom_burst": {texture = FX_DIR + "matt_boom_burst.png", hframes = 8, blocked_first = 0, slam_first = 4, frames = 4,
		frame_time = 0.05, offset = Vector2.ZERO},
	# Tiled by region along the band from its top-left, rows 0-6 the jagged danger edge and row 7 its bright
	# line (`edge` rows in all, which a row of glass laid in front of the band covers). Each segment starts
	# its region a different stretch into the tile, so the tile's 192 px repeat never lines up.
	&"glass_floor": {texture = FX_DIR + "matt_glass_floor.png", tile = Vector2(64, 60), segment_shift = 23.0, edge = 8},
	&"glass_glint": {texture = FX_DIR + "matt_glass_glint.png", hframes = 4, frame_time = 0.06, offset = Vector2.ZERO},
	# frame = shape * 2 + spin; the tip is its bottom row, which is the pivot.
	&"glass_shard": {texture = FX_DIR + "matt_glass_shard.png", hframes = 8, shapes = 4, frame_time = 0.06,
		offset = Vector2(0, -12)},
	&"glass_shadow": {texture = FX_DIR + "matt_glass_shadow.png", hframes = 1, offset = Vector2.ZERO},
	&"glass_land": {texture = FX_DIR + "matt_glass_land.png", hframes = 4, frame_time = 0.04, offset = Vector2(0, -4)},
	&"glass_shatter": {texture = FX_DIR + "matt_glass_shatter.png", hframes = 6, frame_time = 0.05, offset = Vector2(0, -16)},
	# The shackle on the feet: f0-2 clamp shut, then f3-4 loop. Played backwards to let go.
	&"root": {texture = FX_DIR + "matt_root.png", hframes = 5, clamp_frames = [0, 1, 2], clamp_time = 0.05,
		loop_frames = [3, 4], loop_time = 0.15, offset = Vector2(0, -2)},
	&"stomp_dust": {texture = FX_DIR + "matt_stomp_dust.png", hframes = 6, frame_time = 0.05, offset = Vector2(0, -10)},
	&"fury_puff": {texture = FX_DIR + "matt_fury_puff.png", hframes = 4, frame_time = 0.04, offset = Vector2(0, -4)},
}

const PLACEHOLDER_FX := {
	# An icy spearhead on its white-hot core with a wake behind it, in px, pointing down +x.
	&"bolt": {head_length = 30.0, head_width = 18.0, core_radius = 6.0, trail_length = 60.0,
		trail_width = 12.0, head_color = Color("#6EF0FF"), core_color = Color("#FFFFFF"),
		edge_color = Color("#22C3E8"), trail_color = Color("#22C3E8", 0.55)},
	&"spark": {points = 6, radius = 20.0, inner_ratio = 0.4, color = Color("#D2FAFF"),
		from_scale = 0.5, to_scale = 1.4, bounce_time = 0.16, fizzle_time = 0.24},
	&"wave": {fill = Color("#FFCB3C"), edge = Color("#FFF3A8"), edge_width = 6.0, inner = Color("#C87414", 0.8)},
	&"launch": {points = 8, radius = 30.0, inner_ratio = 0.35, color = Color("#D2FAFF"), time = 0.25},
	&"glow": {color = Color("#FFCB3C"), lock_color = Color("#FFFFF0"), from_radius = 4.0,
		to_radius = 18.0, flash_time = 0.06},
	&"aim_dot": {size = 9.0, color = Color("#C87414", 0.85), lit_color = Color("#FFF3A8"), spacing = 24.0},
	&"teleport": {size = Vector2(60, 288), color = Color("#B3B6F2", 0.8), accent = Color("#FFCB3C", 0.9),
		time = 0.3},
	&"glint": {radius = 12.0, color = Color("#6EF0FF"), pulse_time = 0.09},
	# The approved ring style: a core, its flanks and an edge, with a fainter ring 12 texels behind.
	&"yell_rings": {core = Color("#F2F3FF"), core_width = 9.0, flank = Color("#C4C9FA"), flank_width = 15.0,
		edge = Color("#4F4D96"), edge_width = 21.0, trail_gap = 36.0, trail_alpha = 0.45, points = 64,
		fade = 0.06},
	# Hong, while the doll sheet is off: 18x36 px of hair, shirt and trousers.
	&"doll": {size = Vector2(18, 36), hair = Color("#2A2233"), skin = Color("#FBD6B0"),
		shirt = Color("#FFFFFF"), trousers = Color("#3A3A48")},
	# THE GLASS ROW's stand-ins, in px. The boom: three arcs bowed down, in the approved ring style, its
	# node on the leading arc's apex.
	&"boom": {chord = 192.0, bow = 30.0, spacing = 14.0, points = 17, core = Color("#F2F3FF"), core_width = 9.0,
		edge = Color("#4F4D96"), edge_width = 15.0, flank = Color("#C4C9FA"), flank_width = 6.0, trail_alpha = 0.5,
		charge_from = 0.4},
	# A 66 px dark disc with a ring in the arrow's colour and a chunky arrow.
	&"boom_arrow": {radius = 33.0, disc = Color("#332F68"), ring_width = 6.0, arrow = 42.0, answered = Color("#FFFFFF"),
		cracked = Color("#6E6A80"), cross = Color("#FF3B3B")},
	&"boom_burst": {points = 8, radius = 66.0, inner_ratio = 0.4, blocked = Color("#F2F3FF"), slam = Color("#C4C9FA"),
		time = 0.20},
	&"glass_floor": {fill = Color("#7FC9DB", 0.85), shine = Color("#E6FBFF", 0.55), edge = Color("#FFFFFF"),
		edge_depth = 18.0, teeth = 24.0},
	&"glass_glint": {points = 4, radius = 9.0, inner_ratio = 0.3, color = Color("#FFFFFF"), time = 0.24},
	&"glass_shard": {size = Vector2(18, 30), color = Color("#B8ECF5"), edge = Color("#FFFFFF")},
	&"glass_shadow": {radii = Vector2(30, 12), color = Color("#1B1638")},
	&"glass_land": {points = 6, radius = 24.0, inner_ratio = 0.4, color = Color("#E6FBFF"), time = 0.16},
	&"glass_shatter": {points = 10, radius = 90.0, inner_ratio = 0.35, color = Color("#E6FBFF"), time = 0.30},
	&"root": {radii = Vector2(42, 14), color = Color("#B3B6F2"), width = 6.0, points = 24, clamp_time = 0.15},
	&"stomp_dust": {radii = Vector2(120, 30), color = Color("#C4C9FA", 0.7), time = 0.30, from_scale = 0.4, to_scale = 1.3,
		points = 24},
	&"fury_puff": {radii = Vector2(36, 12), color = Color("#C4C9FA", 0.6), time = 0.16, from_scale = 0.5, to_scale = 1.2,
		points = 16},
}

# The Trueshot's crescent on its 0 degree drawing, in texels about its middle, convex side forward. The
# stand-in draws this outline: a 90-texel chord, 16 texels thick at the middle and 2 or 3 at the horns.
const PLACEHOLDER_WAVE_POLY := [
	Vector2(-12.0, -45.0), Vector2(-5.0, -39.4), Vector2(0.2, -33.7), Vector2(4.1, -28.1),
	Vector2(7.1, -22.5), Vector2(9.3, -16.9), Vector2(10.8, -11.2), Vector2(11.7, -5.6),
	Vector2(12.0, 0.0), Vector2(11.7, 5.6), Vector2(10.8, 11.2), Vector2(9.3, 16.9), Vector2(7.1, 22.5),
	Vector2(4.1, 28.1), Vector2(0.2, 33.7), Vector2(-5.0, 39.4), Vector2(-12.0, 45.0),
	Vector2(-10.1, 39.4), Vector2(-8.4, 33.7), Vector2(-7.1, 28.1), Vector2(-6.0, 22.5),
	Vector2(-5.1, 16.9), Vector2(-4.5, 11.2), Vector2(-4.1, 5.6), Vector2(-4.0, 0.0), Vector2(-4.1, -5.6),
	Vector2(-4.5, -11.2), Vector2(-5.1, -16.9), Vector2(-6.0, -22.5), Vector2(-7.1, -28.1),
	Vector2(-8.4, -33.7), Vector2(-10.1, -39.4),
]
# What the wave hits with: the drawn crescent inset 2 texels, traced on the 0 degree frame of
# matt_trueshot_wave.png by the FX artist (art_source/matt_fx/mfx_hitpoly.py), in texels about its
# middle. The horn tips, under 5 texels thick, don't hit. The crescent is symmetric, so turning this to
# any heading matches the flipped art.
const TRUESHOT_HIT_POLY := [
	Vector2(10.0, 4.77), Vector2(9.0, 9.12), Vector2(8.02, 13.48), Vector2(7.0, 17.82), Vector2(5.0, 21.76),
	Vector2(3.0, 25.7), Vector2(0.9, 29.6), Vector2(-1.76, 33.26), Vector2(-5.13, 36.63), Vector2(-8.5, 40.0),
	Vector2(-8.0, 35.83), Vector2(-6.26, 31.76), Vector2(-5.0, 27.5), Vector2(-4.0, 23.12),
	Vector2(-3.17, 18.67), Vector2(-3.0, 13.95), Vector2(-2.0, 9.58), Vector2(-2.0, 4.79), Vector2(-2.0, 0.0),
	Vector2(-2.0, -4.79), Vector2(-2.0, -9.58), Vector2(-3.0, -13.95), Vector2(-3.17, -18.67),
	Vector2(-4.0, -23.12), Vector2(-5.0, -27.5), Vector2(-6.26, -31.76), Vector2(-8.0, -35.83),
	Vector2(-8.5, -40.0), Vector2(-5.13, -36.63), Vector2(-1.76, -33.26), Vector2(0.9, -29.6),
	Vector2(3.0, -25.7), Vector2(5.0, -21.76), Vector2(7.0, -17.82), Vector2(8.02, -13.48), Vector2(9.0, -9.12),
	Vector2(10.0, -4.77), Vector2(10.0, 0.0),
]
# The stand-in's own, its outline inset 2 texels.
const PLACEHOLDER_TRUESHOT_HIT_POLY := [
	Vector2(-8.0, -39.4), Vector2(-0.6, -31.5), Vector2(4.3, -23.7), Vector2(7.6, -15.8),
	Vector2(9.4, -7.9), Vector2(10.0, 0.0), Vector2(9.4, 7.9), Vector2(7.6, 15.8), Vector2(4.3, 23.7),
	Vector2(-0.6, 31.5), Vector2(-8.0, 39.4), Vector2(-5.8, 31.5), Vector2(-4.1, 23.7),
	Vector2(-2.9, 15.8), Vector2(-2.2, 7.9), Vector2(-2.0, 0.0), Vector2(-2.2, -7.9), Vector2(-2.9, -15.8),
	Vector2(-4.1, -23.7), Vector2(-5.8, -31.5),
]

#AUDIO
# His own synthesized set (art_source/audio_matt/make_matt_sfx.py), every file at a -3 dBFS peak, so the
# volume here is the whole mix. The roar's brace reuses the yell's sharp breath, a little lower; the doll's
# squeak is still a stand-in from the build.
const SFX_DIR := "res://Assets/Audio/SFX/"
const SFX := {
	&"teleport_out": {stream = SFX_DIR + "matt_teleport_out.wav", pitch = 1.0, volume_db = -6.0},
	&"teleport_in": {stream = SFX_DIR + "matt_teleport_in.wav", pitch = 1.0, volume_db = -6.0},
	&"mystic_fire": {stream = SFX_DIR + "matt_mystic_fire.wav", pitch = 1.0, volume_db = -3.0},
	&"mystic_bounce": {stream = SFX_DIR + "matt_mystic_bounce.wav", pitch = 1.0, volume_db = -12.0},
	&"mystic_fizzle": {stream = SFX_DIR + "matt_mystic_fizzle.wav", pitch = 1.0, volume_db = -8.0},
	&"trueshot_charge": {stream = SFX_DIR + "matt_trueshot_charge.wav", pitch = 1.0, volume_db = -6.0},
	&"trueshot_lock": {stream = SFX_DIR + "matt_trueshot_lock.wav", pitch = 1.0, volume_db = -6.0},
	&"trueshot_fire": {stream = SFX_DIR + "matt_trueshot_fire.wav", pitch = 1.0, volume_db = -1.0},
	&"yell_tell": {stream = SFX_DIR + "matt_yell_tell.wav", pitch = 1.0, volume_db = -4.0},
	&"yell": {stream = SFX_DIR + "matt_yell.wav", pitch = 1.0, volume_db = 0.0},
	&"roar_inhale": {stream = SFX_DIR + "matt_yell_tell.wav", pitch = 0.85, volume_db = -4.0},
	&"roar": {stream = SFX_DIR + "matt_roar.wav", pitch = 1.0, volume_db = 0.0},
	&"scream_hong": {stream = SFX_DIR + "matt_scream_hong.wav", pitch = 1.0, volume_db = -2.0},
	&"doll_squeak": {stream = SFX_DIR + "hit_impact.ogg", pitch = 3.0, volume_db = -14.0},
	&"recover": {stream = SFX_DIR + "matt_recover.wav", pitch = 1.0, volume_db = -2.0},
	# The Glass Row and the Deafening Yell.
	&"stomp": {stream = SFX_DIR + "matt_stomp.wav", pitch = 1.0, volume_db = -1.0},
	&"root_clamp": {stream = SFX_DIR + "matt_root_clamp.wav", pitch = 1.0, volume_db = -6.0},
	&"fury_stomp": {stream = SFX_DIR + "matt_fury_stomp.wav", pitch = 1.0, volume_db = -9.0},
	&"glass_fall": {stream = SFX_DIR + "matt_glass_fall.wav", pitch = 1.0, volume_db = -16.0},
	&"glass_land": {stream = SFX_DIR + "matt_glass_land.wav", pitch = 1.0, volume_db = -10.0},
	&"glass_shatter": {stream = SFX_DIR + "matt_glass_shatter.wav", pitch = 1.0, volume_db = 0.0},
	&"glass_clear": {stream = SFX_DIR + "matt_glass_clear.wav", pitch = 1.0, volume_db = -10.0},
	&"boom_form": {stream = SFX_DIR + "matt_boom_form.wav", pitch = 1.0, volume_db = -8.0},
	&"boom_fire": {stream = SFX_DIR + "matt_boom_fire.wav", pitch = 1.0, volume_db = -3.0},
	&"boom_answer": {stream = SFX_DIR + "matt_boom_answer.wav", pitch = 1.0, volume_db = -6.0},
	&"boom_wrong": {stream = SFX_DIR + "matt_boom_wrong.wav", pitch = 1.0, volume_db = -6.0},
	&"boom_block": {stream = SFX_DIR + "matt_boom_block.wav", pitch = 1.0, volume_db = -8.0},
	&"boom_hit": {stream = SFX_DIR + "matt_boom_hit.wav", pitch = 1.0, volume_db = -2.0},
	&"deafen_tell": {stream = SFX_DIR + "matt_deafen_tell.wav", pitch = 1.0, volume_db = -4.0},
	&"deafen_yell": {stream = SFX_DIR + "matt_deafen_yell.wav", pitch = 1.0, volume_db = 0.0},
	&"ear_ring": {stream = SFX_DIR + "matt_ear_ring.wav", pitch = 1.0, volume_db = -14.0},
	&"resist": {stream = SFX_DIR + "matt_resist.wav", pitch = 1.0, volume_db = -6.0},
	# The Echo Roars, stand-ins off his own set until their synthesized set (`final`) is in (sfx_stream).
	&"echo_inhale": {stream = SFX_DIR + "matt_yell_tell.wav", pitch = 0.85, volume_db = -6.0},
	&"echo_roar": {stream = SFX_DIR + "matt_roar.wav", final = SFX_DIR + "matt_echo_roar.wav", pitch = 1.1, volume_db = -3.0},
	&"echo_echo": {stream = SFX_DIR + "matt_yell.wav", final = SFX_DIR + "matt_echo_echo.wav", pitch = 0.9, volume_db = -12.0},
	&"echo_psych": {stream = SFX_DIR + "matt_yell_tell.wav", final = SFX_DIR + "matt_echo_psych.wav", pitch = 1.4, volume_db = -8.0},
	&"boomburst": {stream = SFX_DIR + "matt_deafen_yell.wav", final = SFX_DIR + "matt_boomburst.wav", pitch = 1.0, volume_db = 0.0},
	&"echo_punish": {stream = SFX_DIR + "matt_boom_hit.wav", pitch = 1.0, volume_db = -2.0},
}

# Bolts come back off the ropes from everywhere at once, so the bounce is its own round-robin, each
# ping pitched a little off the last.
const BOUNCE_VOICES := 3
const BOUNCE_PITCH_JITTER := 0.08
# How many players a sound gets, for the ones that overlap themselves. A late answer to one boom and a
# quick one to the next can come closer together than boom_answer is long, and the booms fire closer
# together than boom_fire is long.
const SFX_VOICES := {&"mystic_bounce": BOUNCE_VOICES, &"fury_stomp": 3, &"glass_land": 3, &"boom_answer": 2, &"boom_fire": 2,
	&"echo_roar": 3, &"echo_echo": 2}
# boom_form is sped up to end as its boom fires, but no higher than this: past it the roar's build turns
# into a squeak, so on a shorter charge it is cut at the fire instead.
const BOOM_FORM_MAX_PITCH := 1.6

# 2 dB hotter than the -7 the other fights use: his theme is brass and lute with almost no sub-bass,
# and this is where it measures level with Liam's and Jordan's (K-weighted, and above 100 Hz).
const THEME := "res://Assets/Audio/Music/matt_theme.wav"
const THEME_DB := -5.0


static func anim(anim_name: StringName) -> Dictionary:
	if uses_final_anim(anim_name):
		return FINAL_ANIMS[anim_name]
	return PLACEHOLDER_ANIMS[anim_name]


# Its flag on and its sheet in: a sheet that hasn't shipped yet keeps the stand-in rather than failing to load.
static func uses_final_anim(anim_name: StringName) -> bool:
	return USE_FINAL_ANIMS.get(anim_name, false) and FINAL_ANIMS.has(anim_name) \
		and ResourceLoader.exists(FINAL_ANIMS[anim_name].sheet)


# The animation a Trueshot station plays for `which`, &"charge" or &"fire": its own view if that sheet's
# flag is on, the front view if not.
static func station_anim(station: StringName, which: StringName) -> StringName:
	var own: StringName = TRUESHOT_STATION_ANIMS[station][which]
	if USE_FINAL_ANIMS.get(own, false):
		return own
	return TRUESHOT_STATION_ANIMS[&"top"][which]


# A talk pose: its sheet, its [shut, open] frames, and the clip that moves the stand-in while it talks.
static func talk(pose: StringName) -> Dictionary:
	if USE_FINAL_ANIMS[&"talk"]:
		return {sheet = TALK_SHEET, frames = TALK_POSES.get(pose, TALK_POSES[&"friendly"]), motion = &"RESET"}
	var frame := 1 if PLACEHOLDER_TALK_ROAR_POSES.has(pose) else 0
	return {sheet = MATT_SHEET, frames = [frame, frame], motion = &"talk"}


# A sound's stream: its own synthesized take once that file is in, its stand-in until then.
static func sfx_stream(key: StringName) -> String:
	var spec: Dictionary = SFX[key]
	if spec.has("final") and ResourceLoader.exists(spec.final):
		return spec.final
	return spec.stream


static func fx(key: StringName) -> Dictionary:
	if USE_FINAL_FX.get(key, false):
		return FINAL_FX[key]
	return PLACEHOLDER_FX[key]


static func uses_final_fx(key: StringName) -> bool:
	return USE_FINAL_FX.get(key, false)


# What the wave hits with, in texels about its middle, on its 0 degree drawing.
static func trueshot_hit_poly() -> Array:
	return TRUESHOT_HIT_POLY if uses_final_fx(&"wave") else PLACEHOLDER_TRUESHOT_HIT_POLY


# Position from his feet, in px, of a point on his frames: the scaling is on his sprite, so it is
# already applied here.
static func frame_local(point: Vector2) -> Vector2:
	return (point - FRAME_SIZE / 2.0 + SPRITE_OFFSET) * SCALE + FLOOR_POINT


static func local_rect(rect: Rect2) -> Rect2:
	return Rect2(frame_local(rect.position), rect.size * SCALE)


static func crown(anim_name: StringName) -> Vector2:
	if uses_final_anim(anim_name) and CROWNS.has(anim_name):
		return CROWNS[anim_name]
	if BORROWED_ANCHORS.has(anim_name):
		return crown(BORROWED_ANCHORS[anim_name])
	return PLACEHOLDER_CROWN


static func mouth(anim_name: StringName) -> Vector2:
	if uses_final_anim(anim_name) and MOUTHS.has(anim_name):
		return MOUTHS[anim_name]
	if BORROWED_ANCHORS.has(anim_name):
		return mouth(BORROWED_ANCHORS[anim_name])
	return PLACEHOLDER_MOUTH


# A texel from his feet, in px, on a frame drawn flipped or not: flipped, the texel mirrors to 95 - x,
# which is where the flipped sprite draws it.
static func texel_local(point: Vector2, flip := false) -> Vector2:
	if flip:
		point.x = FRAME_SIZE.x - 1.0 - point.x
	return frame_local(point)


static func mouth_offset(anim_name: StringName, flip := false) -> Vector2:
	return texel_local(mouth(anim_name), flip)


static func tell_offset(anim_name: StringName, flip := false) -> Vector2:
	return texel_local(crown(anim_name), flip) + Vector2(0, -TELL_GAP)


static func daze_offset(anim_name: StringName) -> Vector2:
	return frame_local(crown(anim_name)) + Vector2(0, -DAZE_GAP)


# Which of a sheet's headings draws `heading`, and the flips that turn it the right way: [heading index,
# flip_h, flip_v]. The sheets travel right and down, so going left flips h and going up flips v.
static func art_frame(heading: Vector2, angles: Array) -> Array:
	var base := rad_to_deg(atan2(absf(heading.y), absf(heading.x)))
	var best := 0
	for i in angles.size():
		if absf(angles[i] - base) < absf(angles[best] - base):
			best = i
	return [best, heading.x < 0.0, heading.y < 0.0]


# The wave's or its launch's sheet for `heading` (`key` is &"wave" or &"launch"): [spec, heading index,
# flip_h, flip_v]. Folded into the first quadrant and put on the 11.25 degree grid, an odd step is on the
# _mid sheet; with that sheet off, the main sheet's nearest heading draws it.
static func wave_art(key: StringName, heading: Vector2) -> Array:
	var step := roundi(rad_to_deg(atan2(absf(heading.y), absf(heading.x))) / WAVE_ART_STEP)
	var mid := StringName(String(key) + "_mid")
	if step % 2 == 1 and uses_final_fx(mid):
		return [fx(mid), int((step - 1) / 2.0), heading.x < 0.0, heading.y < 0.0]
	var pick := art_frame(heading, WAVE_ART_ANGLES)
	return [fx(key), pick[0], pick[1], pick[2]]


# An offset off a centred sheet's middle, kept on its pivot under the sheet's flips.
static func flipped_offset(offset: Vector2, flip_h: bool, flip_v: bool) -> Vector2:
	return Vector2(-offset.x if flip_h else offset.x, -offset.y if flip_v else offset.y)


static func star(points: int, radius: float, inner_ratio: float) -> PackedVector2Array:
	var polygon := PackedVector2Array()
	for i in points * 2:
		var r := radius if i % 2 == 0 else radius * inner_ratio
		polygon.append(Vector2.from_angle(TAU * i / (points * 2) - PI / 2.0) * r)
	return polygon


# Where a stomp lands on `anim_name`'s steps, in texels: {step: foot}.
static func slam_feet(anim_name: StringName) -> Dictionary:
	if USE_FINAL_ANIMS.get(anim_name, false) and SLAM_FEET.has(anim_name):
		return SLAM_FEET[anim_name]
	return PLACEHOLDER_SLAM_FEET.get(anim_name, {})


# The sheet the Glass Row poses the player in: {texture, hframes, vframes}.
static func player_poses() -> Dictionary:
	return PLAYER_POSE_SHEET if USE_FINAL_PLAYER_POSES else PLACEHOLDER_PLAYER_POSE_SHEET


# One of those poses: {frames, times, loop}.
static func player_pose(pose: StringName) -> Dictionary:
	return (PLAYER_POSES if USE_FINAL_PLAYER_POSES else PLACEHOLDER_PLAYER_POSES)[pose]


static func juggle() -> Dictionary:
	return FINAL_JUGGLE


static func ellipse(radii: Vector2, points: int) -> PackedVector2Array:
	var polygon := PackedVector2Array()
	for i in points:
		polygon.append(Vector2.from_angle(TAU * i / points) * radii)
	return polygon


static func circle(radius: float, points: int) -> PackedVector2Array:
	var polygon := PackedVector2Array()
	for i in points:
		polygon.append(Vector2.from_angle(TAU * i / points) * radius)
	return polygon


static func scaled_poly(poly: Array, by: float, turn: float) -> PackedVector2Array:
	var out := PackedVector2Array()
	for point: Vector2 in poly:
		out.append((point * by).rotated(turn))
	return out
