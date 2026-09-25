extends RefCounted

# Every number that depends on how Danny is drawn, so a redraw only needs this file. Points and boxes are
# in texels on one of his frames, origin top-left.
#
# HIS BODY'S ORIGIN IS HIS FEET, as Captain Burak's is: every spot DannyBossStateMachine names is a feet
# point, and every sheet stands his soles on the node. The sumo's sheets are 176x144 with the feet at
# (88,143); the jump is 176x160 and the side-view headbutt 224x144, and the small form's are 64x64 with the
# feet at (32,63) (art_source/danny_sumo/transform.py pastes that frame at (+56,+80) inside the big one, so
# the two forms swap in place). A sheet that isn't 176x144 carries its `frame` and `feet` in its row.
#
# THE OFFSET FOLLOWS THE SHEET, NEVER THE ANIMATION (DannyBossScript._stand_on), and his lift rides on top
# of it: set_lift() raises the sprite through sprite.offset alone, and a sheet swap keeps the lift. So the
# node, his hurtbox and his y-sort stay on the ground under him while he is in the air, as Eric's leap did.
# BossJuggled owns the offset from the juggle's first frame until it restores the sheet and offset it found.
#
# Each body sheet has its own flag in USE_FINAL_ANIMS, looked up by the animation's whole name first and
# then by its first word, and nothing loads a final sheet while its flag is off. Every sheet has shipped and
# every flag is on: the idle, wake, step, hit, defeat and evolve sheets and the small form's first, then the
# fight's own nine, approved on 2026-09-24 (art_source/danny_sumo_v2/fight_sheets.py; their anchors are the
# artist's report). A sheet turned off again stands in with a frame of a shipped one (PLACEHOLDER_ANIMS). The
# AnimationPlayer clips in DannyBossScene are only the talk squash and its reset.
#
# A FLIPPED POINT MIRRORS AS A TEXEL, x becoming frame width - 1 - x, which is where the flipped sprite
# draws it. His sheets face screen-right unflipped, the way every flip in this game reads.

const SCALE := 3.0

#DANNY (horizontal strips, soles on the feet row, the feet on the centre column)
const FRAME_SIZE := Vector2(176, 144)
const ANCHOR := Vector2(88, 143)
# Stands the bottom edge of ANCHOR's row on the sprite's origin. Comes to (0, -72).
const SPRITE_OFFSET := Vector2(FRAME_SIZE.x / 2.0 - ANCHOR.x, FRAME_SIZE.y / 2.0 - ANCHOR.y - 1.0)
const SHEET_DIR := "res://Assets/Characters/Danny/Sumo/"
const SMALL_DIR := "res://Assets/Characters/Danny/"
const FX_DIR := "res://Assets/Characters/Danny/FX/"
const UI_DIR := "res://Assets/UI/"
const IDLE_SHEET := SHEET_DIR + "danny_sumo_idle.png"
const WAKE_SHEET := SHEET_DIR + "danny_sumo_wake.png"
const STEP_SHEET := SHEET_DIR + "danny_sumo_step.png"
const HIT_SHEET := SHEET_DIR + "danny_sumo_hit.png"
const DEFEAT_SHEET := SHEET_DIR + "danny_sumo_defeat.png"
const EVOLVE_SHEET := SHEET_DIR + "danny_sumo_evolve.png"
const SLAP_SHEET := SHEET_DIR + "danny_sumo_slap.png"
# The training room's Danny, before he evolves: stands on (0, -32).
const SMALL_FRAME := Vector2(64, 64)
const SMALL_FEET := Vector2(32, 63)
const JUMP_FRAME := Vector2(176, 160)
const JUMP_FEET := Vector2(88, 159)
# The torpedo is side-on and flies screen-right: every frame stands on its bottom centre.
const HEADBUTT_FRAME := Vector2(224, 144)
const HEADBUTT_FEET := Vector2(112, 143)

# What the player can punch and turns to face. `idle` is every standing pose, on a 176x144 frame: his head
# and torso from the top of the beanie to the floor, the spread arms and thighs left out (288 x 426 px).
# `sleep` is the artist's SLEEP_BOX, the whole slumped sit with the bubble left out, and `headbutt` the
# torpedo's flight box on its own 224x144 frame (BODY_BOX_FRAMES). A box is mirrored with him
# (DannyBossScript.set_body_box).
const BODY_BOXES := {
	&"idle": Rect2(40, 2, 96, 142),
	&"sleep": Rect2(2, 16, 172, 128),
	&"headbutt": Rect2(4, 52, 197, 89),
}
const BODY_BOX_FRAMES := {
	&"headbutt": {frame = HEADBUTT_FRAME, feet = HEADBUTT_FEET},
}

# The top of his beanie over its middle column (where the badges and the daze stars stand), one point an
# animation: its first frame, or the frame it is held on. The artist reported the nap's, the nap's flinch
# and the block's; the rest were measured as the first row with a 16- or 20-texel run of the head near his
# middle column, so a raised hand never reads as the crown. The small form's is on its own 64x64 frame, the
# jump's on its 176x160 and the headbutt's on its 224x144 (the top of his hunched back, side-on).
const CROWNS := {
	&"idle": Vector2(88, 2),
	&"talk": Vector2(88, 2),
	&"wake": Vector2(88, 3),
	&"step": Vector2(88, 1),
	&"hit": Vector2(87, 1),
	&"defeat": Vector2(90, 3),
	&"broken": Vector2(90, 3),
	&"evolve_small": Vector2(88, 80),
	&"evolve_awake": Vector2(88, 2),
	&"evolve_land": Vector2(88, 2),
	&"walk_small": Vector2(32, 0),
	&"walk_hold": Vector2(32, 1),
	&"grip": Vector2(32, 1),
	&"tear": Vector2(32, 1),
	&"flex": Vector2(32, 1),
	&"spit_windup": Vector2(88, 5),
	&"spit_fire": Vector2(89, 9),
	&"spit_fire2": Vector2(87, 9),
	&"spit_recover": Vector2(88, 3),
	&"jump_crouch": Vector2(88, 26),
	&"jump_launch": Vector2(88, 4),
	&"air": Vector2(82, 14),
	&"slam_drop": Vector2(88, 7),
	&"slam_impact": Vector2(88, 41),
	&"slam_rebound": Vector2(88, 4),
	&"sleep": Vector2(102, 19),
	&"sleep_hit": Vector2(93, 13),
	&"headbutt_windup": Vector2(158, 12),
	&"headbutt_launch": Vector2(150, 34),
	&"headbutt_fly": Vector2(145, 54),
	&"headbutt_bonk": Vector2(153, 51),
	&"headbutt_recoil": Vector2(68, 9),
	&"block": Vector2(88, 2),
	&"push_set": Vector2(88, 12),
	&"push_strain": Vector2(87, 13),
	&"push_win": Vector2(88, 15),
	&"push_skid": Vector2(88, 10),
	&"push_out": Vector2(88, 1),
}
# The same, on each stand-in's frame.
const PLACEHOLDER_CROWNS := {
	&"spit_windup": Vector2(88, 2),
	&"spit_fire": Vector2(88, 2),
	&"spit_fire2": Vector2(88, 2),
	&"spit_recover": Vector2(88, 2),
	&"jump_crouch": Vector2(88, 1),
	&"jump_launch": Vector2(88, 1),
	&"air": Vector2(88, 2),
	&"slam_drop": Vector2(88, 15),
	&"slam_impact": Vector2(88, 15),
	&"slam_rebound": Vector2(88, 15),
	&"sleep": Vector2(88, 17),
	&"sleep_hit": Vector2(87, 1),
	&"headbutt_windup": Vector2(88, 2),
	&"headbutt_launch": Vector2(88, 2),
	&"headbutt_fly": Vector2(88, 2),
	&"headbutt_bonk": Vector2(87, 1),
	&"headbutt_recoil": Vector2(88, 2),
	&"block": Vector2(88, 2),
	&"push_set": Vector2(88, 2),
	&"push_strain": Vector2(88, 2),
	&"push_win": Vector2(88, 2),
	&"push_skid": Vector2(88, 2),
	&"push_out": Vector2(87, 1),
}
const DEFAULT_CROWN := Vector2(88, 2)

# The rest of his points, the artist's (one an animation, on the frame named), each with its stand-in for a
# sheet turned off: the open mouth a glob leaves from (f3 aims the first glob right, f4 the second left); the
# rear's contact texel, the same on the drop, the impact and the rebound; the front of his head in the
# headbutt (align the flight by it: the plan's launch y is the player's hurtbox centre less its height); the
# middle of his two palms in the push (PUSH_PALMS has both, per frame; the pushed-out frames touch nothing);
# and where the Z's rise from his sleeping head.
const MOUTHS := {
	&"spit_windup": Vector2(88, 50),
	&"spit_fire": Vector2(91, 56),
	&"spit_fire2": Vector2(84, 56),
	&"spit_recover": Vector2(88, 48),
}
const PLACEHOLDER_MOUTH := Vector2(88, 46)
const CONTACTS := {
	&"slam_drop": Vector2(88, 143),
	&"slam_impact": Vector2(88, 143),
	&"slam_rebound": Vector2(88, 143),
}
const PLACEHOLDER_CONTACT := Vector2(88, 143)
const HEADS := {
	&"headbutt_windup": Vector2(185, 38),
	&"headbutt_launch": Vector2(199, 57),
	&"headbutt_fly": Vector2(200, 81),
	&"headbutt_bonk": Vector2(206, 83),
	&"headbutt_recoil": Vector2(103, 42),
}
const PLACEHOLDER_HEAD := Vector2(116, 30)
const HANDS := {
	&"push_set": Vector2(87.5, 128),
	&"push_strain": Vector2(86.5, 128),
	&"push_win": Vector2(87.5, 125),
	&"push_skid": Vector2(87.5, 123),
}
const PLACEHOLDER_HAND := Vector2(88, 110)
# The push's palm centres, left then right, by sheet frame.
const PUSH_PALMS := {
	0: [Vector2(75, 128), Vector2(100, 128)],
	1: [Vector2(74, 128), Vector2(99, 128)],
	2: [Vector2(76, 129), Vector2(101, 129)],
	3: [Vector2(75, 128), Vector2(100, 128)],
	4: [Vector2(71, 125), Vector2(104, 125)],
	5: [Vector2(76, 123), Vector2(99, 123)],
}
const SNORES := {
	&"sleep": Vector2(100, 14),
}
const PLACEHOLDER_SNORE := Vector2(110, 30)
# Where the finisher's daze stars circle and a badge's tip stands, over his crown.
const DAZE_GAP := 34.0
const TELL_GAP := 12.0

#ANIMATIONS
# name: sheet, frames in order, seconds on each (the last value repeats) and whether it loops. Optional:
# `frame` and `feet` for a sheet that isn't 176x144 with its feet at (88,143), and `motion`, the
# AnimationPlayer clip in DannyBossScene that moves the whole sprite under it. A pose the attack holds for its
# own time is a one-frame loop, so a state's own animation replaces it at once (play_state_anim).
const USE_FINAL_ANIMS := {
	&"idle": true,
	&"talk": true,
	&"wake": true,
	&"step": true,
	&"hit": true,
	&"defeat": true,
	&"broken": true,
	&"evolve": true,
	&"walk": true,
	&"grip": true,
	&"tear": true,
	&"flex": true,
	&"spit": true,
	&"jump": true,
	&"air": true,
	&"slam": true,
	&"sleep": true,
	&"sleep_hit": true,
	&"headbutt": true,
	&"block": true,
	&"push": true,
}

# The shipped sheets' timings (art_source/danny_sumo_v2/anim.py and art_source/danny_sumo/sheets.py), and the
# fight sheets' from fight_sheets.py.
const FINAL_ANIMS := {
	# Sleepy: the belly swells, the head nods, the bubble grows.
	&"idle": {sheet = IDLE_SHEET, frames = [0, 1, 2, 3], times = [0.20, 0.18, 0.26, 0.18], loop = true},
	# No mouth frames: the idle's first frame squashes in time with the typing.
	&"talk": {sheet = IDLE_SHEET, frames = [0], times = [1.0], loop = true, motion = &"talk"},
	# The bubble pops and he snaps awake into his guard, 0.49 s; its last frame is the slap's first.
	&"wake": {sheet = WAKE_SHEET, frames = [0, 1, 2], times = [0.14, 0.09, 0.26], loop = false},
	&"step": {sheet = STEP_SHEET, frames = [0, 1, 2, 3], times = [0.14, 0.09, 0.11, 0.16], loop = true},
	&"hit": {sheet = HIT_SHEET, frames = [0, 1], times = [0.09, 0.14], loop = false},
	# He sits down and goes to sleep; he doesn't topple. Held on the last frame.
	&"defeat": {sheet = DEFEAT_SHEET, frames = [0, 1, 2, 3], times = [0.18, 0.16, 0.22, 0.60], loop = false},
	# The Break: his defeat's first two frames, swaying.
	&"broken": {sheet = DEFEAT_SHEET, frames = [0, 1], times = [0.30], loop = true},
	# The transformation's three frames, each held by the beat that shows it: 0 the small form flexing (the
	# flash's first silhouette), 1 the sumo in his guard (its second, and the settle), 2 the landing.
	&"evolve_small": {sheet = EVOLVE_SHEET, frames = [0], times = [1.0], loop = true},
	&"evolve_awake": {sheet = EVOLVE_SHEET, frames = [1], times = [1.0], loop = true},
	&"evolve_land": {sheet = EVOLVE_SHEET, frames = [2], times = [1.0], loop = true},
	&"walk_small": {sheet = SMALL_DIR + "danny_walk.png", frames = [0, 1, 2, 3], times = [0.16], loop = true,
		frame = SMALL_FRAME, feet = SMALL_FEET},
	# Arrived: both feet down, arms at his sides.
	&"walk_hold": {sheet = SMALL_DIR + "danny_walk.png", frames = [1], times = [1.0], loop = true,
		frame = SMALL_FRAME, feet = SMALL_FEET},
	# Reach, grip, then strain and grip ping-ponging.
	&"grip": {sheet = SMALL_DIR + "danny_grip.png", frames = [0, 1, 2, 1, 2], times = [0.14, 0.28, 0.09], loop = false,
		frame = SMALL_FRAME, feet = SMALL_FEET},
	&"tear": {sheet = SMALL_DIR + "danny_tear.png", frames = [0, 1, 2], times = [0.20, 0.06, 0.34], loop = false,
		frame = SMALL_FRAME, feet = SMALL_FEET},
	&"flex": {sheet = SMALL_DIR + "danny_flex.png", frames = [0, 1, 2, 3], times = [0.12, 0.30, 0.30, 0.30], loop = false,
		frame = SMALL_FRAME, feet = SMALL_FEET},
	# The worm spit: 0-2 the wind-up, 3 the first glob, 4 the second, 5 settling back.
	&"spit_windup": {sheet = SHEET_DIR + "danny_sumo_spit.png", frames = [0, 1, 2], times = [0.13, 0.17, 0.15], loop = false},
	&"spit_fire": {sheet = SHEET_DIR + "danny_sumo_spit.png", frames = [3], times = [1.0], loop = true},
	&"spit_fire2": {sheet = SHEET_DIR + "danny_sumo_spit.png", frames = [4], times = [1.0], loop = true},
	&"spit_recover": {sheet = SHEET_DIR + "danny_sumo_spit.png", frames = [5], times = [0.24], loop = false},
	# The Sumo Smash: 0-1 feet on the floor, 2 the tuck with the rear on it (the lift starts from 2).
	&"jump_crouch": {sheet = SHEET_DIR + "danny_sumo_jump.png", frames = [0], times = [1.0], loop = true,
		frame = JUMP_FRAME, feet = JUMP_FEET},
	&"jump_launch": {sheet = SHEET_DIR + "danny_sumo_jump.png", frames = [1, 2], times = [0.08, 0.10], loop = false,
		frame = JUMP_FRAME, feet = JUMP_FEET},
	# The tuck while he hangs and tracks, rear on the floor row: the lift raises it.
	&"air": {sheet = SHEET_DIR + "danny_sumo_air.png", frames = [0, 1, 2, 3], times = [0.12], loop = true},
	&"slam_drop": {sheet = SHEET_DIR + "danny_sumo_slam.png", frames = [0], times = [1.0], loop = true},
	&"slam_impact": {sheet = SHEET_DIR + "danny_sumo_slam.png", frames = [1], times = [1.0], loop = true},
	&"slam_rebound": {sheet = SHEET_DIR + "danny_sumo_slam.png", frames = [2], times = [1.0], loop = true},
	&"sleep": {sheet = SHEET_DIR + "danny_sumo_sleep.png", frames = [0, 1, 2, 3], times = [0.30, 0.28, 0.36, 0.28], loop = true},
	# Once per punch, then back to the nap.
	&"sleep_hit": {sheet = SHEET_DIR + "danny_sumo_sleep_hit.png", frames = [0, 1], times = [0.09, 0.17], loop = false},
	# The torpedo: 0 the wind-up (feet on the mat), 1 the launch, 2-3 in flight, 4 the bonk, 5 the recoil.
	&"headbutt_windup": {sheet = SHEET_DIR + "danny_sumo_headbutt.png", frames = [0], times = [1.0], loop = true,
		frame = HEADBUTT_FRAME, feet = HEADBUTT_FEET},
	&"headbutt_launch": {sheet = SHEET_DIR + "danny_sumo_headbutt.png", frames = [1], times = [0.06], loop = false,
		frame = HEADBUTT_FRAME, feet = HEADBUTT_FEET},
	&"headbutt_fly": {sheet = SHEET_DIR + "danny_sumo_headbutt.png", frames = [2, 3], times = [0.05], loop = true,
		frame = HEADBUTT_FRAME, feet = HEADBUTT_FEET},
	&"headbutt_bonk": {sheet = SHEET_DIR + "danny_sumo_headbutt.png", frames = [4], times = [0.09], loop = false,
		frame = HEADBUTT_FRAME, feet = HEADBUTT_FEET},
	&"headbutt_recoil": {sheet = SHEET_DIR + "danny_sumo_headbutt.png", frames = [5], times = [0.14], loop = false,
		frame = HEADBUTT_FRAME, feet = HEADBUTT_FEET},
	# Filling the top gateway, front on.
	&"block": {sheet = SHEET_DIR + "danny_sumo_block.png", frames = [0, 1, 2, 3], times = [0.22, 0.20, 0.30, 0.20], loop = true},
	# The tug, front on: 0 set, 1-3 even, 4 gaining, 5 losing ground, 6-7 pushed out.
	&"push_set": {sheet = SHEET_DIR + "danny_sumo_push.png", frames = [0], times = [0.20], loop = false},
	&"push_strain": {sheet = SHEET_DIR + "danny_sumo_push.png", frames = [1, 2, 3], times = [0.09], loop = true},
	&"push_win": {sheet = SHEET_DIR + "danny_sumo_push.png", frames = [4], times = [0.15], loop = false},
	&"push_skid": {sheet = SHEET_DIR + "danny_sumo_push.png", frames = [5], times = [0.12], loop = false},
	&"push_out": {sheet = SHEET_DIR + "danny_sumo_push.png", frames = [6, 7], times = [0.11, 0.22], loop = false},
}

# The stand-ins, off the shipped sheets (the plan's art contract). Their timings match the final rows', so a
# state times itself the same way on either.
const PLACEHOLDER_ANIMS := {
	&"spit_windup": {sheet = SLAP_SHEET, frames = [1], times = [0.45], loop = false},
	&"spit_fire": {sheet = SLAP_SHEET, frames = [2], times = [1.0], loop = true},
	&"spit_fire2": {sheet = SLAP_SHEET, frames = [2], times = [1.0], loop = true},
	&"spit_recover": {sheet = IDLE_SHEET, frames = [0], times = [0.24], loop = false},
	&"jump_crouch": {sheet = STEP_SHEET, frames = [0], times = [1.0], loop = true},
	&"jump_launch": {sheet = STEP_SHEET, frames = [0], times = [0.18], loop = false},
	&"air": {sheet = IDLE_SHEET, frames = [0], times = [1.0], loop = true},
	&"slam_drop": {sheet = DEFEAT_SHEET, frames = [2], times = [1.0], loop = true},
	&"slam_impact": {sheet = DEFEAT_SHEET, frames = [2], times = [1.0], loop = true},
	&"slam_rebound": {sheet = DEFEAT_SHEET, frames = [2], times = [1.0], loop = true},
	&"sleep": {sheet = DEFEAT_SHEET, frames = [3], times = [1.0], loop = true},
	&"sleep_hit": {sheet = HIT_SHEET, frames = [0], times = [0.26], loop = false},
	&"headbutt_windup": {sheet = SLAP_SHEET, frames = [0], times = [1.0], loop = true},
	&"headbutt_launch": {sheet = SLAP_SHEET, frames = [1], times = [0.06], loop = false},
	&"headbutt_fly": {sheet = SLAP_SHEET, frames = [2, 3, 4, 5], times = [0.05], loop = true},
	&"headbutt_bonk": {sheet = HIT_SHEET, frames = [0], times = [0.09], loop = false},
	&"headbutt_recoil": {sheet = HIT_SHEET, frames = [1], times = [0.14], loop = false},
	&"block": {sheet = WAKE_SHEET, frames = [2], times = [1.0], loop = true},
	&"push_set": {sheet = SLAP_SHEET, frames = [0], times = [0.20], loop = false},
	&"push_strain": {sheet = SLAP_SHEET, frames = [2, 3, 4, 5], times = [0.09], loop = true},
	&"push_win": {sheet = SLAP_SHEET, frames = [2], times = [0.15], loop = false},
	&"push_skid": {sheet = SLAP_SHEET, frames = [5], times = [0.12], loop = false},
	&"push_out": {sheet = HIT_SHEET, frames = [0, 1], times = [0.11, 0.22], loop = false},
}

#THE PLAYER'S POSES (PlayerPosed, through DannyBossStateMachine.hold_player_pose)
# The tug-of-war against him at the top gate: one sheet in player_4dir_sheet.png's row order, the back view
# copied into every row, because the player only ever faces up at him (art_source/danny_player). Each pose is
# its columns, seconds each (the last for the rest) and whether it loops; a one-shot holds its last column.
# The gloves meet his hands on rows 3-5 of the strain frames. hold_pose() refuses once the player's
# fight_over is set, so nothing may finish the fight before the tug.
const USE_FINAL_PLAYER_POSES := true
const PLAYER_POSE_SHEET := {texture = "res://Assets/Characters/MainPlayer/player_sumo_push.png", hframes = 8, vframes = 4}
const PLAYER_POSES := {
	&"set": {frames = [0], times = [0.20], loop = false},
	&"strain": {frames = [1, 2], times = [0.09], loop = true},
	&"shove": {frames = [3], times = [0.15], loop = false},
	&"skid": {frames = [4, 5], times = [0.12], loop = true},
	&"launched": {frames = [6], times = [0.11], loop = false},
	&"on_back": {frames = [7], times = [0.22], loop = false},
}
const PLACEHOLDER_PLAYER_POSE_SHEET := {texture = "res://Assets/Characters/MainPlayer/player_4dir_sheet.png", hframes = 10, vframes = 4}
const PLACEHOLDER_PLAYER_POSES := {
	&"set": {frames = [0], times = [0.20], loop = false},
	&"strain": {frames = [0], times = [1.0], loop = true},
	&"shove": {frames = [9], times = [0.15], loop = false},
	&"skid": {frames = [0], times = [1.0], loop = true},
	&"launched": {frames = [9], times = [0.11], loop = false},
	&"on_back": {frames = [0], times = [0.22], loop = false},
}

#THE HUD
# The hints (DannyBossScript.show_hint): bottom centre on his HUD layer, above the player's bars, each once a
# fight. `bottom` is the text's bottom edge in screen px.
const HINT := {font_size = 33, outline = 6, color = Color("#F2F3FF"), outline_color = Color("#06181A"), width = 1100.0,
	bottom = 924.0, fade = 0.2}
# The "+N" over his crown on each tick of his nap's regen, in the heal greens of his FX (dfx_pal.py). It rises
# `rise` px over `time` and fades over the last `fade` of it.
const REGEN_LABEL := {font_size = 33, outline = 6, color = Color("#99E550"), outline_color = Color("#24341A"),
	gap = 18.0, rise = 60.0, time = 0.7, fade = 0.3}

#FX (FX_FOR_CODER: horizontal strips, never rotated)
# `offset` is the frame's centre minus its pivot, in texels, for a centred sprite, so the node sits on the
# pivot. Godot's flip_h doesn't mirror an offset, so a flipped one negates its x (flipped_offset).
const FX := {
	# A ball of worms, round, so never rotated or flipped: it moves along its arc.
	&"glob": {texture = FX_DIR + "danny_worm_glob.png", hframes = 4, frame_time = 0.06, offset = Vector2.ZERO},
	# Once where a glob lands; its last frame is the puddle's first, pixel for pixel.
	&"splat": {texture = FX_DIR + "danny_worm_splat.png", hframes = 5, frame_time = 0.05, offset = Vector2.ZERO},
	# On the floor under everyone. The trigger is the stain's body, rx x ry texels round its pivot; the drops
	# round it are decoration.
	&"puddle": {texture = FX_DIR + "danny_worm_puddle.png", hframes = 4, frame_time = 0.12, offset = Vector2.ZERO,
		trigger = Vector2(43, 17)},
	# Over the player, its pivot on the floor under their feet: 13 texels (39 px) below the centre of their
	# 32x32 frame. 0-3 loop while it holds; 4-7 once as it lets go.
	&"root": {texture = FX_DIR + "danny_worm_root.png", hframes = 8, hold_frames = [0, 1, 2, 3], hold_time = 0.08,
		release_frames = [4, 5, 6, 7], release_time = 0.05, offset = Vector2(0, -10), feet_below_centre = 39.0},
	# His tracking shadow, small to full size by his height: 0-1 loop while he hangs, 5 the frame before he
	# lands; full size matches his seated footprint (132 x 22 texels).
	&"slam_target": {texture = FX_DIR + "danny_slam_target.png", hframes = 6, hover_frames = [0, 1], frame_time = 0.1,
		land_frame = 5, offset = Vector2.ZERO},
	# On his rear's contact texel: 0-4 over his body, 5 the cracks alone on the floor, held and then faded.
	&"slam_impact": {texture = FX_DIR + "danny_slam_impact.png", hframes = 6, frame_time = 0.05, cracks_frame = 5,
		offset = Vector2(0, -16)},
	# Bixby's ring layout (BixbyQuakeRingScript): 4 frames x 7 rows of 40x32, pivots on the frame centres.
	&"quake_ring": {texture = FX_DIR + "danny_quake_ring.png", hframes = 4, vframes = 7, frame_time = 0.08,
		offset = Vector2.ZERO},
	# Behind his body, flying right, its pivot on the back of his body box level with its middle.
	&"headbutt_trail": {texture = FX_DIR + "danny_headbutt_trail.png", hframes = 4, frame_time = 0.04,
		offset = Vector2(-76, 0)},
	# At his head (snore_point), drifting up and to the right: flipped with him.
	&"sleep_z": {texture = FX_DIR + "danny_sleep_z.png", hframes = 8, frame_time = 0.12, offset = Vector2(14, -24)},
	# Over his body while the regen runs, on his body's frame and feet, so on his own offset.
	&"regen": {texture = FX_DIR + "danny_regen.png", hframes = 8, frame_time = 0.08, offset = Vector2(0, -72)},
	# One per skidding foot, drawn for a foot sliding left: row 0 his, row 1 the player's.
	&"sumo_dust": {texture = FX_DIR + "danny_sumo_dust.png", hframes = 5, vframes = 2, frame_time = 0.06,
		danny_row = 0, player_row = 1, offset = Vector2(-16, -12)},
}

#THE TUG-OF-WAR METER (HUD layer; FX_FOR_CODER's meter)
# The _3x copies, positioned in 1x texels times SCALE. Its fills are revealed by a region crop from the
# channel's edges to the marker, never stretched; the marker's x is marker_x0 + marker_x_per_rope * rope.
# `anchor` is the frame's top-left in screen px: bottom centre, where the user-approved mock has it
# (scratchpad danny_fx/mock_danny.py's tug), clear of him in the top gate.
const METER := {
	"frame": UI_DIR + "tug_meter_frame_3x.png",
	"fill_player": UI_DIR + "tug_meter_fill_player_3x.png",
	"fill_danny": UI_DIR + "tug_meter_fill_danny_3x.png",
	"centre": UI_DIR + "tug_meter_centre_3x.png",
	"marker": UI_DIR + "tug_meter_marker_3x.png",
	"marker_hframes": 4,
	"marker_frame_time": 0.06,
	"channel": Rect2(29, 9, 102, 6),
	"centre_at": Vector2(79, 8),
	"marker_centre": Vector2(4, 8),
	"marker_y": 12.0,
	"marker_x0": 80.0,
	"marker_x_per_rope": 51.0,
	"anchor": Vector2(720, 900),
}

#THE JUGGLE (the Break's tiered uppercut; BossJuggled reads exactly this shape)
# A sheet of its own: its frame is not his 176x144 and its origin is not his feet, so its texels go through
# BossJuggled.texel_point(), never frame_local(). top_row is the tumble's highest row (frames 2-6).
const USE_FINAL_JUGGLE := true
const FINAL_JUGGLE := {
	"texture": "res://Assets/Characters/Danny/Sumo/danny_juggle.png",
	"hframes": 12,
	"frame_size": Vector2(304, 208),
	"offset": Vector2(0, -104),
	"feet": Vector2(152, 207),
	"tumble_centre": Vector2(152, 100),
	"top_row": 14,
	"clips": {
		&"launch": {"frames": [0, 1], "times": [0.07, 0.10], "loop": false},
		&"tumble": {"frames": [2, 3, 4, 5, 6], "times": [0.26, 0.09, 0.08, 0.08, 0.09], "loop": true},
		&"crash": {"frames": [7, 8, 9], "times": [0.07, 0.10, 0.14], "loop": false},
		&"down": {"frames": [10, 11], "times": [0.45, 0.35], "loop": true},
	},
	"shadow": {
		"texture": "res://Assets/Characters/Danny/Sumo/danny_leap_shadow.png",
		"hframes": 3, "scale": 3.0, "alpha": 0.35, "step": 100.0, "offset": Vector2.ZERO,
	},
	"lying_time": 0.3,
	"outro_delay": 1.8,
	"crash_sfx": {"stream": "res://Assets/Audio/SFX/earthquake_slam.ogg", "pitch": 0.9, "volume_db": 0.0},
}

#AUDIO
# His own synthesized set (art_source/audio_danny/make_danny_sfx.py), every file at a -3 dBFS peak, so the volume
# here is the whole mix. The gate's clang, the record scratch, the sumo's stomp and clash stay on the shared set
# at the plan's pitch and level, and the Break's sting is everyone's. Two loop: the snore under his nap and the
# strain under the tug; each has its own copy of the stream (DannyBossScript._build_sfx).
const SFX_DIR := "res://Assets/Audio/SFX/"
const SFX := {
	&"gulp": {stream = SFX_DIR + "danny_gulp.wav", pitch = 1.0, volume_db = -6.0},
	&"spit": {stream = SFX_DIR + "danny_spit.wav", pitch = 1.0, volume_db = -4.0},
	&"glob_splat": {stream = SFX_DIR + "danny_glob_splat.wav", pitch = 1.0, volume_db = -4.0},
	&"puddle_dry": {stream = SFX_DIR + "danny_puddle_dry.wav", pitch = 1.0, volume_db = -12.0},
	&"root_clamp": {stream = SFX_DIR + "danny_root_clamp.wav", pitch = 1.0, volume_db = -4.0},
	&"root_burst": {stream = SFX_DIR + "danny_root_burst.wav", pitch = 1.0, volume_db = -4.0},
	&"jump": {stream = SFX_DIR + "danny_jump.wav", pitch = 1.0, volume_db = -4.0},
	&"butt_slam": {stream = SFX_DIR + "danny_butt_slam.wav", pitch = 1.0, volume_db = 0.0},
	&"slam_bonk": {stream = SFX_DIR + "danny_slam_bonk.wav", pitch = 1.0, volume_db = -3.0},
	&"snore": {stream = SFX_DIR + "danny_snore.wav", pitch = 1.0, volume_db = -14.0, loop = true},
	&"sleep_hit": {stream = SFX_DIR + "danny_sleep_hit.wav", pitch = 1.0, volume_db = -6.0},
	&"regen_tick": {stream = SFX_DIR + "danny_regen_tick.wav", pitch = 1.0, volume_db = -12.0},
	&"wake": {stream = SFX_DIR + "danny_wake.wav", pitch = 1.0, volume_db = -6.0},
	&"headbutt_charge": {stream = SFX_DIR + "danny_headbutt_charge.wav", pitch = 1.0, volume_db = -6.0},
	&"headbutt_launch": {stream = SFX_DIR + "danny_headbutt_launch.wav", pitch = 1.0, volume_db = -3.0},
	&"headbutt_bonk": {stream = SFX_DIR + "danny_headbutt_bonk.wav", pitch = 1.0, volume_db = -3.0},
	&"headbutt_hit": {stream = SFX_DIR + "danny_headbutt_hit.wav", pitch = 1.0, volume_db = -2.0},
	&"gate_clang": {stream = SFX_DIR + "eric_crash_thud.wav", pitch = 1.0, volume_db = -6.0},
	&"record_scratch": {stream = SFX_DIR + "carter_fake_punish.wav", pitch = 1.5, volume_db = 0.0},
	&"sumo_stomp": {stream = SFX_DIR + "matt_stomp.wav", pitch = 1.0, volume_db = 0.0},
	&"sumo_clash": {stream = SFX_DIR + "wrestler_collision.ogg", pitch = 0.9, volume_db = 0.0},
	&"push_strain": {stream = SFX_DIR + "danny_push_strain.wav", pitch = 1.0, volume_db = -10.0, loop = true},
	&"pushed_out": {stream = SFX_DIR + "danny_pushed_out.wav", pitch = 1.0, volume_db = -2.0},
	&"break_sting": {stream = SFX_DIR + "break_sting.wav", pitch = 1.0, volume_db = 0.0},
}
# How many players a sound gets, for the ones a string or a pair overlaps with itself.
const SFX_VOICES := {&"butt_slam": 2, &"glob_splat": 3, &"spit": 2, &"regen_tick": 2, &"sumo_stomp": 2}

# "Five More Minutes", written for this fight and APPROVED. It loops by its own import, so nothing here
# rewrites its loop points, and it is never preloaded: the shared theme stands in if it is missing. -4 dB is
# the composer's level match; the stand-in keeps the -7 the other fights use. danny_theme.wav is the
# training room's.
const THEME := "res://Assets/Audio/Music/danny_sumo_theme.wav"
const THEME_DB := -4.0
const THEME_FALLBACK := "res://Assets/Audio/Music/boss_theme.ogg"
const THEME_FALLBACK_DB := -7.0


# An animation goes by its sheet's flag: its own name's if it has one (sleep_hit), else its first word's.
static func uses_final(anim_name: StringName) -> bool:
	if USE_FINAL_ANIMS.has(anim_name):
		return USE_FINAL_ANIMS[anim_name]
	return USE_FINAL_ANIMS.get(StringName(String(anim_name).get_slice("_", 0)), false)


static func anim(anim_name: StringName) -> Dictionary:
	if uses_final(anim_name) and FINAL_ANIMS.has(anim_name):
		return FINAL_ANIMS[anim_name]
	if PLACEHOLDER_ANIMS.has(anim_name):
		return PLACEHOLDER_ANIMS[anim_name]
	return FINAL_ANIMS.get(anim_name, FINAL_ANIMS[&"idle"])


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


# Position from his feet, in px, of a point on a frame of `spec`'s sheet: the scaling is on his sprite, so it
# is already applied here. Not his lift: the callers that want the drawn point add it (DannyBossScript).
static func frame_local(point: Vector2, spec: Dictionary) -> Vector2:
	return (point - frame_size(spec) / 2.0 + sheet_offset(spec)) * SCALE


# A texel of `anim_name`'s frames from his feet, in px, drawn flipped or not.
static func texel_local(point: Vector2, anim_name: StringName, flip := false) -> Vector2:
	var spec := anim(anim_name)
	if flip:
		point.x = frame_size(spec).x - 1.0 - point.x
	return frame_local(point, spec)


# A body box in px from his feet, drawn unflipped, on its own frame (BODY_BOX_FRAMES) or a 176x144 one.
static func body_rect(key: StringName) -> Rect2:
	var box: Rect2 = BODY_BOXES.get(key, BODY_BOXES[&"idle"])
	return Rect2(frame_local(box.position, BODY_BOX_FRAMES.get(key, {})), box.size * SCALE)


static func crown(anim_name: StringName) -> Vector2:
	if uses_final(anim_name):
		return CROWNS.get(anim_name, DEFAULT_CROWN)
	return PLACEHOLDER_CROWNS.get(anim_name, DEFAULT_CROWN)


static func mouth(anim_name: StringName) -> Vector2:
	return _point(MOUTHS, PLACEHOLDER_MOUTH, anim_name)


static func contact(anim_name: StringName) -> Vector2:
	return _point(CONTACTS, PLACEHOLDER_CONTACT, anim_name)


static func head(anim_name: StringName) -> Vector2:
	return _point(HEADS, PLACEHOLDER_HEAD, anim_name)


static func hand(anim_name: StringName) -> Vector2:
	return _point(HANDS, PLACEHOLDER_HAND, anim_name)


static func snore(anim_name: StringName) -> Vector2:
	return _point(SNORES, PLACEHOLDER_SNORE, anim_name)


static func _point(finals: Dictionary, placeholder: Vector2, anim_name: StringName) -> Vector2:
	if uses_final(anim_name) and finals.has(anim_name):
		return finals[anim_name]
	return placeholder


static func fx(key: StringName) -> Dictionary:
	return FX[key]


# An offset off a centred sheet's middle, kept on its pivot under the sheet's flips.
static func flipped_offset(offset: Vector2, flip_h: bool, flip_v := false) -> Vector2:
	return Vector2(-offset.x if flip_h else offset.x, -offset.y if flip_v else offset.y)


static func juggle() -> Dictionary:
	return FINAL_JUGGLE


static func player_pose_sheet() -> Dictionary:
	return PLAYER_POSE_SHEET if USE_FINAL_PLAYER_POSES else PLACEHOLDER_PLAYER_POSE_SHEET


static func player_pose(pose: StringName) -> Dictionary:
	var table: Dictionary = PLAYER_POSES if USE_FINAL_PLAYER_POSES else PLACEHOLDER_PLAYER_POSES
	return table.get(pose, table[&"set"])
