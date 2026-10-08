extends RefCounted

# Every number Jordan's room plays on (JordanFinaleScript): its points, the beats' timings, the cameo table, the
# crumble's waves, and every piece of its art, each behind a USE_FINAL_* flag with the stand-in it plays on until the
# art is approved. Points are screen px (1920x1080, the room drawn at SCALE from the screen's origin); texel points
# are on the art's own frames.
#
# THE STAGING, a contract the room's art can adopt - a different staging is a change here, not in the script:
#   The door is in the back wall on the left; everyone comes in through it, walking down.
#   Jordan's desk is against the back wall right of centre, and he sits at it with his back to the camera.
#   The talk spot is at his left elbow, beside his chair and a little behind it: the player faces RIGHT to talk, and
#   he swivels to face screen-left.
#   The moustache goes on facing the camera (DOWN), the clearest view of it; the player turns back RIGHT to tap him.
#   The camera zooms to GAG_ZOOM on the pair for the gag, so the moustache and its fall read.

const SCALE := 3.0
const VIEW_SIZE := Vector2(1920, 1080)

#THE ROOM (px; the room artist's numbers from its approval pass, 2026-09-28)
# The floor the player walks: texel rows 163 (under the shelf and cabinet bases, which reach 161) to 349, texel
# columns 14 to 626. Its whole outline is WALK_POLYGON, which adds the door's sill and takes out the desk and chair.
const WALK_AREA := Rect2(42, 489, 1836, 558)
# In texels, clockwise.
const WALK_POLYGON: Array[Vector2] = [
	Vector2(14, 163), Vector2(45, 163), Vector2(45, 152), Vector2(99, 152), Vector2(99, 163), Vector2(336, 163),
	Vector2(336, 170), Vector2(393, 170), Vector2(393, 216), Vector2(446, 216), Vector2(446, 170), Vector2(516, 170),
	Vector2(516, 163), Vector2(626, 163), Vector2(626, 349), Vector2(14, 349),
]
# Floor nothing walks through: the desk (texel x 340-482, rows 150-167), the PC beside it, and the chair's spot. The
# chair's spot starts at texel x 393, the drawn chair base's left edge (seated frame x 46 on the anchor at 64), which
# leaves the talk spot beside it clear.
const BLOCKERS: Array[Rect2] = [Rect2(1020, 450, 429, 54), Rect2(1464, 450, 69, 51), Rect2(1179, 504, 159, 144)]
# Where everyone comes in: the door's sill in the back wall (its clear opening texel x 45-99, its threshold row 150),
# walking down into the room.
const DOOR_POINT := Vector2(216, 450)
const ENTRY_MARK := Vector2(330, 660)
# The floor point under the seat's centre, which is his y-sort point while he sits.
const CHAIR_POINT := Vector2(1233, 588)
# The player's soles (-26, -19) texels from the chair's anchor, the seated artist's staging: at his left elbow, where
# the RIGHT tap's glove (texels 23-24, 4-5 of its frame) lands on it, and clear of the chair's spot.
const TALK_SPOT := Vector2(1155, 531)
# Up to the chair's spot, so it takes in the talk spot.
const TALK_ZONE := Rect2(900, 510, 279, 240)
# Over his head while he sits.
const PROMPT_POINT := Vector2(1233, 230)
# In front of the chair once he leaps up, and far enough right of it that the empty chair's back shows beside his head
# rather than rising behind it: 24 texels clears his quiff on every standing frame, where 20 still touched it.
const JORDAN_STAND_POINT := Vector2(1332, 700)
# The nine cameos' feet, in ladder order (CAMEOS). Two loose rows on the room's left two thirds, every foot at y 800
# or above, clear of the balloon at 816, and all facing the talk spot.
const BOSS_MARKS: Array[Vector2] = [
	Vector2(300, 620), Vector2(520, 600), Vector2(740, 610), Vector2(380, 790), Vector2(620, 800),
	Vector2(860, 790), Vector2(170, 790), Vector2(940, 620), Vector2(1060, 780),
]
# The void: where the player drifts to as the floor goes, and where the god hovers (his anchor texel's point).
const VOID_PLAYER_MARK := Vector2(620, 800)
const GOD_POINT := Vector2(960, 600)

#THE BEATS (seconds unless it says otherwise)
const ARRIVE_FADE := 1.0
const TALK_STEP := 0.3
const TALK_INPUT_LOCK := 0.3
const NO_ANSWER := 1.2
const BOSS_STEP := 0.35
const CAMEO_SPEED := 420.0
const GAG_ZOOM := 2.0
const GAG_ZOOM_TIME := 0.5
const GAG_FOCUS := Vector2(1156, 480)
# The moustache: reach, press, done - facing the camera - and back to face him, held a beat before the taps.
const MOUSTACHE_ON := [0.35, 0.4, 0.35, 0.4]
# Two taps: wind-up, tap, wind-up, tap. On the second he snaps round and swivels, pulling his headset down, over SWIVEL
# from it (SEATED's swivel pair fills it).
const TAP := [0.15, 0.2, 0.15, 0.2]
const SWIVEL := 0.4
# The moustache's fall from his lip to the floor, swaying side to side, and the stare after it lands.
const FALL_TIME := 2.2
const FALL_SWAY_TEXELS := 4.0
const FALL_SWAY_CYCLES := 2.0
const STARE := 0.4
# He leaps up, and the view comes back out.
const LEAP := 0.8
const DUST_POP := 0.3
const UNZOOM_TIME := 0.4
# The tremble shakes three props loose as it starts.
const TREMBLE_DROPS := 3
# The zap: his gesture, the line's flash, and Liam dissolving while the rest flinch.
const ZAP_GESTURE := 0.3
const ZAP_FLASH := 0.12
const ZAP_DISSOLVE := 1.2
const FLINCH := 0.3
# The rest: arms up, the ring, and the eight gone nearest first.
const ARMS_UP := 0.3
const RING_TIME := 0.5
const RING_TEXELS := 220.0
const REST_STEP := 0.12
const REST_DISSOLVE := 0.7
# The collapse's waves, from its start, a layer a wave; the floor goes from the edges in. Then silence.
const COLLAPSE_WAVES := {&"clutter": 0.0, &"props": 0.6, &"furniture": 1.2, &"walls": 1.8, &"floor": 2.6}
const COLLAPSE_SILENCE := 0.5
const VOID_DRIFT := 1.5
# The ascension: up RISE_PX under a growing aura and shake, the flash, the god, and his drone.
const RISE_PX := 120.0
const RISE_TIME := 1.2
const RISE_SHAKE := 6.0
const FLASH_UP := 0.1
const FLASH_DOWN := 0.4
const GOD_SETTLE := 0.8
const END_FADE := 1.0
const SKIP_FADE := 0.5
# His theme through the door, muffled: whichever one his fight plays (JordanArtLayout.theme()), this far under its
# fight level. It fades out as the room comes apart, gone well before the intro's hit. OFF since the user asked
# (2026-09-29: "lets also make it so the jordan finale boss music isnt playing during the cutscene leading up to it"):
# the cutscene plays with no music under it, and his fight's theme starts with the fight. The intro below is the reveal's
# own hit, not his theme, and still plays at the flash.
const MUSIC_UNDER := false
const MUSIC_UNDER_DB := -13.0
const MUSIC_PITCH := 0.92
const MUSIC_FADE_OUT := 2.0
# His final theme's intro (approved 2026-09-28), a teaser for the fight to come: 8 bars at 185 BPM, 10.378 s, no loop.
# Its hit and roar open it (peaking 0.028 s in) on the flash he becomes the god in, under a hymn of his music-box phrase
# to 5.189 s; then a quiet stretch his last line types in, to 7.784 s; then a wind-up to the downbeat the file ends
# on, where the card smashes in. Times are the composer's, on the file's own clock. -6 dB is level with his other
# themes. Until it is in and imported, the stand-in drone plays and the last line ends on a press and a fade.
# OFF since 2026-10-06 (the user: "then during the cutscene no music, then when the jordan god fight starts you can
# use neo tokyo"): it teases his final theme, which his god fight no longer plays wherever Neo Tokyo is in. Off, the
# flash plays the stand-in sting and drone, and his last line ends on a press and a fade into the fight.
static var USE_INTRO := false
const INTRO := "res://Assets/Audio/Music/jordan_final_intro.wav"
const INTRO_DB := -6.0
const INTRO_LINE_AT := 5.189
# The file ends at full tilt, so its last 20 ms fade out as the screen cuts: the ear still hears a smash cut, with no
# click.
const INTRO_TAIL_AT := 10.358
const INTRO_TAIL := 0.02

#WHERE IT ENDS
# Every end of the finale - his last line, a hold in the room, a hold in the walk-out - lands on TO BE CONTINUED, or,
# with this on and his last phase built, on that fight (the Puppet Master, JordanGodFightScene), which his last line
# is the start of. A static var rather than a const so the defence suite can turn it on for a run (jordan_god). ON
# since the user linked them (2026-09-28: "link jordans finale cutscene with the boss fight now"); the fight's own
# end, his defeat, is what lands on TO BE CONTINUED now.
static var USE_GOD_FIGHT := true
const GOD_FIGHT_SCENE := "res://Scenes/Bosses/JordanGodFightScene.tscn"
const CARD_SCENE := "res://Scenes/Core/ToBeContinuedScene.tscn"

#THE PROMPT
const PROMPT_TEXT := "TALK"
const PROMPT_KEY := "ENTER"
const PROMPT_FONT_SIZE := 33
const PROMPT_COLOR := Color(0.93, 0.92, 0.88)
const PROMPT_BACKING := Color(0.043, 0.039, 0.071, 0.75)

#THE ART
# Final art goes up only once the user has approved it: each flag stays false until then, and nothing loads a final
# sheet while its flag is off. An approved set's flag is on, and still plays its stand-in until its files are in and
# the editor has imported them (the final_* functions below). Approved 2026-09-28: the room; demon-god Jordan (variant
# A2, the full obsidian mask) with the void; Jordan at his desk with the moustache and its prop; and Jordan on his feet.
const USE_FINAL_ROOM := true
const USE_FINAL_SEATED := true
const USE_FINAL_STANDING := true
const USE_FINAL_MOUSTACHE := true
const USE_FINAL_PROP := true
const USE_FINAL_GOD := true
const USE_FINAL_VOID := true

const ROOM_LAYERS: Array[StringName] = [&"floor", &"walls", &"furniture", &"props", &"clutter"]
const ROOM_DIR := "res://Assets/Environment/JordanRoom/"
const ROOM_SIZE := Vector2i(640, 360)
# The room artist's crumble pieces (generated by art_source/jordan_room/jr_export.py): layer -> [{texture: path, at: the
# texel its top-left sits on in the layer}], each a whole prop or a chunk of floor or wall, tiling its layer exactly.
const ROOM_PIECES := "res://Scripts/JordanRoomPieces.gd"

# The room's stand-in: coloured rects on each layer, in texels, [x, y, w, h, colour], drawn in order. The floor and the
# walls cover the canvas between them, and each layer stands on its own, as the drawn one must.
const BLURPLE := Color(0.345, 0.396, 0.949)
const PLACEHOLDER_ROOM := {
	&"floor": [
		[0, 0, 640, 360, Color(0.33, 0.24, 0.19)],
		[45, 58, 54, 92, Color(0.07, 0.05, 0.09)],
		[0, 176, 640, 1, Color(0.27, 0.19, 0.15)], [0, 202, 640, 1, Color(0.27, 0.19, 0.15)],
		[0, 228, 640, 1, Color(0.27, 0.19, 0.15)], [0, 254, 640, 1, Color(0.27, 0.19, 0.15)],
		[0, 280, 640, 1, Color(0.27, 0.19, 0.15)], [0, 306, 640, 1, Color(0.27, 0.19, 0.15)],
		[0, 332, 640, 1, Color(0.27, 0.19, 0.15)],
		[185, 245, 267, 85, Color(0.24, 0.22, 0.36)],
	],
	&"walls": [
		[0, 0, 45, 150, Color(0.2, 0.19, 0.29)], [99, 0, 541, 150, Color(0.2, 0.19, 0.29)],
		[45, 0, 54, 58, Color(0.2, 0.19, 0.29)],
		[0, 146, 41, 4, Color(0.12, 0.1, 0.16)], [103, 146, 537, 4, Color(0.12, 0.1, 0.16)],
		[41, 54, 4, 96, Color(0.46, 0.34, 0.24)], [99, 54, 4, 96, Color(0.46, 0.34, 0.24)],
		[41, 54, 62, 4, Color(0.46, 0.34, 0.24)],
		[0, 150, 8, 210, Color(0.17, 0.16, 0.24)], [632, 150, 8, 210, Color(0.17, 0.16, 0.24)],
	],
	&"furniture": [
		[150, 60, 110, 6, Color(0.36, 0.25, 0.17)], [150, 66, 6, 95, Color(0.3, 0.2, 0.14)],
		[254, 66, 6, 95, Color(0.3, 0.2, 0.14)], [150, 94, 110, 4, Color(0.36, 0.25, 0.17)],
		[150, 124, 110, 4, Color(0.36, 0.25, 0.17)], [150, 155, 110, 6, Color(0.36, 0.25, 0.17)],
		[338, 114, 146, 6, Color(0.42, 0.3, 0.21)], [340, 120, 142, 47, Color(0.16, 0.14, 0.2)],
		[488, 104, 23, 63, Color(0.08, 0.08, 0.1)], [560, 90, 60, 71, Color(0.32, 0.23, 0.17)],
	],
	&"props": [
		[383, 83, 57, 27, Color(0.06, 0.06, 0.08)], [386, 86, 51, 21, BLURPLE],
		[407, 107, 8, 7, Color(0.06, 0.06, 0.08)], [389, 122, 34, 7, Color(0.15, 0.15, 0.18)],
		[491, 110, 17, 2, BLURPLE],
		[338, 120, 30, 2, Color(1.0, 0.2, 0.3)], [368, 120, 30, 2, Color(1.0, 0.7, 0.2)],
		[398, 120, 30, 2, Color(0.3, 1.0, 0.4)], [428, 120, 30, 2, Color(0.3, 0.6, 1.0)],
		[458, 120, 26, 2, Color(0.8, 0.3, 1.0)],
		[160, 80, 8, 14, Color(0.9, 0.5, 0.2)], [176, 80, 8, 14, Color(0.3, 0.8, 0.9)],
		[192, 80, 8, 14, Color(0.9, 0.9, 0.3)], [208, 80, 8, 14, Color(0.8, 0.3, 0.5)],
		[224, 80, 8, 14, Color(0.4, 0.9, 0.4)], [240, 80, 8, 14, Color(0.9, 0.3, 0.3)],
		[162, 110, 8, 14, Color(0.5, 0.4, 0.9)], [178, 110, 8, 14, Color(0.95, 0.75, 0.6)],
		[194, 110, 8, 14, Color(0.3, 0.5, 0.9)], [226, 110, 8, 14, Color(0.9, 0.6, 0.8)],
		[166, 141, 12, 14, Color(0.85, 0.7, 0.3)], [200, 141, 12, 14, Color(0.6, 0.3, 0.2)],
		[210, 26, 50, 30, Color(0.75, 0.3, 0.35)], [290, 20, 42, 56, Color(0.95, 0.85, 0.5)],
		[586, 18, 40, 50, Color(0.3, 0.55, 0.8)],
	],
	&"clutter": [
		[24, 300, 32, 14, Color(0.25, 0.35, 0.55)], [560, 318, 42, 16, Color(0.6, 0.2, 0.25)],
		[598, 214, 24, 12, Color(0.2, 0.5, 0.35)], [30, 176, 22, 10, Color(0.75, 0.7, 0.6)],
		[520, 180, 16, 12, Color(0.85, 0.75, 0.3)], [118, 250, 6, 9, Color(0.8, 0.2, 0.2)],
		[610, 270, 6, 9, Color(0.2, 0.7, 0.9)], [454, 330, 30, 12, Color(0.35, 0.3, 0.5)],
	],
}

# The void under the room: the drawn one, or a flat colour with motes drifting up through it.
const VOID_BG := "res://Assets/Environment/Void/void_bg.png"
const PLACEHOLDER_VOID := {"color": Color(0.06, 0.02, 0.1), "motes": Color(0.55, 0.25, 0.8, 0.8), "amount": 60}

# Jordan at his desk, the user's approved art (2026-09-28): 128x128 frames, the front caster's floor contact at
# (64, 127), which is his y-sort point. 0-3 gaming with his back to the camera; 4 his head snapping round and 5 the
# swivel, pulling his headset down, played once; 6-7 his friendly talk pair and 8-9 his glare's, pointing at the
# player; 10 the empty chair. 6-10 face screen-left, where the player stands.
const SEATED_SHEET := "res://Assets/Characters/Jordan/Room/jordan_seated.png"
const SEATED := {
	&"gaming": {sheet = SEATED_SHEET, frames = [0, 1, 2, 3], times = [0.18, 0.14, 0.18, 0.14], loop = true,
		frame = Vector2(128, 128), feet = Vector2(64, 127)},
	# The snap held so the pair fills SWIVEL.
	&"swivel": {sheet = SEATED_SHEET, frames = [4, 5], times = [0.25, 0.15], loop = false, frame = Vector2(128, 128),
		feet = Vector2(64, 127)},
	&"talk": {sheet = SEATED_SHEET, frames = [6, 7], times = [0.16, 0.12], loop = true, frame = Vector2(128, 128),
		feet = Vector2(64, 127)},
	&"talk_shut": {sheet = SEATED_SHEET, frames = [6], times = [1.0], loop = true, frame = Vector2(128, 128),
		feet = Vector2(64, 127)},
	&"glare": {sheet = SEATED_SHEET, frames = [8, 9], times = [0.16, 0.12], loop = true, frame = Vector2(128, 128),
		feet = Vector2(64, 127)},
	&"glare_shut": {sheet = SEATED_SHEET, frames = [8], times = [1.0], loop = true, frame = Vector2(128, 128),
		feet = Vector2(64, 127)},
	&"empty": {sheet = SEATED_SHEET, frames = [10], times = [1.0], loop = true, frame = Vector2(128, 128),
		feet = Vector2(64, 127)},
}
# Until it is in: hunched on his defeat's last frame and lit blue by the monitor for the gaming, his idle for the rest -
# swivel, talk and glare alike - and a chair drawn in code.
const PLACEHOLDER_SEATED := {
	&"gaming": {sheet = "res://Assets/Characters/Jordan/jordan_defeat.png", frames = [5], times = [1.0], loop = true,
		frame = Vector2(96, 96), feet = Vector2(48, 95)},
	&"idle": {sheet = "res://Assets/Characters/Jordan/jordan_idle.png", frames = [0, 1, 2, 3],
		times = [0.2, 0.16, 0.2, 0.16], loop = true, frame = Vector2(96, 96), feet = Vector2(48, 95)},
}
const SEATED_TINT := Color(0.6, 0.7, 1.3)
# The stand-in chair, in texels from the floor contact: its seat and its back, behind him from the camera.
const PLACEHOLDER_CHAIR := {"seat": Rect2(-16, -22, 32, 8), "back": Rect2(-14, -58, 28, 36), "stem": Rect2(-2, -14, 4, 14),
	"base": Rect2(-14, -3, 28, 3), "color": Color(0.12, 0.12, 0.16), "trim": Color(0.8, 0.2, 0.35)}

# Jordan on his feet, the user's approved art (2026-09-28): 96x96 with his soles at (48, 95) like his fight sheets,
# drawn facing right, so each flips to face whoever he turns to. The rage's talk pair, shut then open; the zap - wind-up,
# thrust, hold, recover, holding the recovery - its hold up from 0.20 to 0.55 s, so the line's flash at ZAP_GESTURE
# lands on it; and the zap sheet's frame 4, both fists up with an arc of energy between them, held.
# Their effect points are px off his feet, facing right (x mirrors with him): the zap's `hand`, where its line
# starts, and the arms-up's `ring`, where the ring goes out from, just under the arc (its centre is at (0, -259.5)).
const STANDING_RAGE := "res://Assets/Characters/Jordan/jordan_rage.png"
const STANDING_ZAP := "res://Assets/Characters/Jordan/jordan_zap.png"
const STANDING := {
	&"rage": {sheet = STANDING_RAGE, frames = [0, 1], times = [0.12], loop = true, frame = Vector2(96, 96),
		feet = Vector2(48, 95), flips = true},
	&"rage_shut": {sheet = STANDING_RAGE, frames = [0], times = [1.0], loop = true, frame = Vector2(96, 96),
		feet = Vector2(48, 95), flips = true},
	&"zap": {sheet = STANDING_ZAP, frames = [0, 1, 2, 3], times = [0.12, 0.08, 0.35, 0.15], loop = false,
		frame = Vector2(96, 96), feet = Vector2(48, 95), flips = true, hand = Vector2(100.5, -148.5)},
	&"arms_up": {sheet = STANDING_ZAP, frames = [4], times = [1.0], loop = false, frame = Vector2(96, 96),
		feet = Vector2(48, 95), flips = true, ring = Vector2(0, -255)},
}
# Until they are in: the rage is his idle, pulsing red, the zap his summon's crouch and punch up, then its pop, and the
# arms up his taunt, the box hoisted; the zap's line from his head and the ring from his chest.
const PLACEHOLDER_STANDING := {
	&"rage": {sheet = "res://Assets/Characters/Jordan/jordan_idle.png", frames = [0, 1, 2, 3],
		times = [0.2, 0.16, 0.2, 0.16], loop = true, frame = Vector2(96, 96), feet = Vector2(48, 95)},
	&"zap": {sheet = "res://Assets/Characters/Jordan/jordan_summon.png", frames = [0, 1, 2, 3],
		times = [0.12, 0.08, 0.1, 0.1], loop = false, frame = Vector2(96, 96), feet = Vector2(48, 95),
		hand = Vector2(0, -150)},
	&"arms_up": {sheet = "res://Assets/Characters/Jordan/jordan_taunt.png", frames = [0, 1, 2, 3],
		times = [0.13, 0.11, 0.13, 0.11], loop = true, frame = Vector2(96, 96), feet = Vector2(48, 95),
		ring = Vector2(0, -120)},
}
# The red pulse over a stand-in's glare and rage: once a PULSE seconds, well under three flashes a second.
const PULSE := 0.6
const PULSE_TINT := Color(1.6, 0.55, 0.55)

# The moustache, the user's approved art (2026-09-28): player_moustache.png, 32x32 cells laid out as
# player_4dir_sheet.png - its rows the same facings, its soles and centre column the same. Columns: 0 idle with it on,
# 1 reach, 2 press, 3 done, 4 tap wind-up, 5 tap, 6 talk, 7 caught without it.
const MOUSTACHE_SHEET := "res://Assets/Characters/MainPlayer/player_moustache.png"
const MOUSTACHE_FRAMES := {&"on": 0, &"reach": 1, &"press": 2, &"done": 3, &"tap_windup": 4, &"tap": 5, &"talk": 6,
	&"caught": 7}
# Where it sits on each facing's frames, in texels, by StoryPlayer facing (DOWN 0, LEFT 2, RIGHT 3; from behind there
# is none): the prop's pivot goes here as it comes off.
const MOUSTACHE_LIP := {0: Vector2(15, 10), 2: Vector2(13, 9), 3: Vector2(18, 9)}
# Until it is in: the player's own frames, and a moustache drawn on at StoryPlayer.lip_point(), in texels round it.
const PLACEHOLDER_MOUSTACHE := {"points": [Vector2(-2.5, -0.5), Vector2(-0.5, -1.0), Vector2(0.5, -1.0),
	Vector2(2.5, -0.5), Vector2(2.0, 0.5), Vector2(0.5, 0.0), Vector2(-0.5, 0.0), Vector2(-2.0, 0.5)],
	"color": Color(0.16, 0.09, 0.05)}
# moustache_prop.png, 16x16: 0-3 fluttering round its pivot (8, 8) - level, left end up, curled, right end up - once
# a sway, and 4 lying flat on its row 15. Frame 0 on DOWN's lip covers the drawn moustache exactly.
const MOUSTACHE_PROP := {sheet = "res://Assets/Characters/MainPlayer/moustache_prop.png", flutter = [0, 1, 2, 3],
	flat = 4, frame = Vector2(16, 16), pivot = Vector2(8, 8), rest_row = 15}
# Where it lands: the floor just in front of his feet, between him and Jordan's shins.
const PROP_FLOOR_OFFSET := Vector2(18, 6)

# Demon-god Jordan, the user's variant A2 (2026-09-28): an armoured demon lord in a full obsidian mask, huge spread
# wings, a flame-horn crown, lava cracks and a white chest core. Each sheet is a strip of `frames` frames of `frame`
# texels, at 3x, placed as the artist placed it: its `anchor` texel's top-left corner on GOD_POINT (not centred). The
# hover loops with its bob drawn in. He talks on the talk pair, shut then open, drawn in hover frame 0's pose. The aura
# goes over him added, on the hover's frame - frame 0 while he talks - so its glow stays on his outline.
const GOD := {
	&"hover": {sheet = "res://Assets/Characters/Jordan/God/jordan_god_hover.png", frames = 6, frame = Vector2(320, 224),
		anchor = Vector2(160, 223)},
	&"talk": {sheet = "res://Assets/Characters/Jordan/God/jordan_god_talk.png", frames = 2, frame = Vector2(320, 224),
		anchor = Vector2(160, 223)},
	&"aura": {sheet = "res://Assets/Characters/Jordan/God/jordan_god_aura.png", frames = 6, frame = Vector2(336, 232),
		anchor = Vector2(168, 223)},
}
const GOD_FRAME_TIME := 0.14
# 36 frames of 192x192, a 60-degree turn drawn fresh on each, so the node itself never turns. Centred on his chest
# core, RUNES_OFFSET from GOD_POINT, behind him.
const GOD_RUNES := "res://Assets/Characters/Jordan/God/jordan_god_runes.png"
const RUNES_FRAMES := 36
const RUNES_FRAME_TIME := 0.1
const RUNES_OFFSET := Vector2(0, -296)
# The rune circle comes in behind him as he appears.
const RUNES_IN := 0.6
# Until his hover is in: his taunt's frame 1 at twice the scale, crimson and bobbing, a blue ring turning behind him
# for the runes and a red glow.
const PLACEHOLDER_GOD := {"spec": {sheet = "res://Assets/Characters/Jordan/jordan_taunt.png", frames = [1], times = [1.0],
	loop = true, frame = Vector2(96, 96), feet = Vector2(48, 95)}, "scale": 2.0, "tint": Color(1.5, 0.35, 0.3),
	"bob_px": 9.0, "bob_time": 1.2, "ring": Color(0.35, 0.6, 1.0, 0.7), "ring_radius": 250.0,
	"glow": Color(0.9, 0.1, 0.15, 0.45)}

# The aura as he rises, and the flash he becomes the god in: at most one flash a beat.
const AURA_COLOR := Color(1.0, 0.1, 0.15, 0.55)
const AURA_RADIUS := 170.0
const FLASH_COLOR := Color(1, 1, 1, 1)
const ZAP_COLOR := Color(1.0, 0.3, 0.75)
const RING_COLOR := Color(1.0, 0.3, 0.75, 0.8)

#THE SOUNDS (stand-ins: no finale sound is drawn up yet)
const SOUNDS := {
	&"rumble": {"stream": "res://Assets/Audio/SFX/earthquake_slam.ogg", "volume_db": -4.0, "pitch": 0.8},
	&"dark": {"stream": "res://Assets/Audio/SFX/carter_dark.wav", "volume_db": -2.0, "pitch": 1.0},
	&"roar": {"stream": "res://Assets/Audio/SFX/bixby_roar.wav", "volume_db": 0.0, "pitch": 0.7},
	&"sting": {"stream": "res://Assets/Audio/SFX/knight_breaker_sting.wav", "volume_db": -2.0, "pitch": 1.0},
	&"tink": {"stream": "res://Assets/Audio/SFX/parry_tink_1.wav", "volume_db": -4.0, "pitch": 0.7},
}

#THE CAMEOS, in ladder order (GameProgress.BOSSES), each off its own fight's sheets. `enter`: walk (on `walk`), bob
# (the bob-walk, no walk of its own), glide (on `walk`, then `arrive` at the mark) or teleport (`arrive` at the mark).
# `idle` is his fight's own; `talk`, where he has lines, plays while they type.
const CAMEOS: Array[Dictionary] = [
	{"name": &"captain_burak", "enter": &"walk",
		"walk": {sheet = "res://Assets/Characters/BurakBoss/burak_walk.png", frames = [0, 1, 2, 3, 4, 5], times = [0.12],
			loop = true, frame = Vector2(96, 96), feet = Vector2(48, 95), flips = true},
		"idle": {sheet = "res://Assets/Characters/BurakBoss/burak_idle.png", frames = [0, 1, 2, 3],
			times = [0.30, 0.20, 0.12, 0.20], loop = true, frame = Vector2(96, 96), feet = Vector2(48, 95), flips = true}},
	{"name": &"eric", "enter": &"walk",
		"walk": {sheet = "res://Assets/Characters/Eric/eric_entrance.png", frames = [0, 1, 2, 3], times = [0.14],
			loop = true, frame = Vector2(256, 192), feet = Vector2(128, 191)},
		"idle": {sheet = "res://Assets/Characters/Eric/eric_entrance.png", frames = [3], times = [1.0], loop = true,
			frame = Vector2(256, 192), feet = Vector2(128, 191)}},
	{"name": &"greyson", "enter": &"walk",
		"walk": {sheet = "res://Assets/Characters/Greyson/greyson_walk.png", frames = [0, 1, 2, 3, 4, 5], times = [0.10],
			loop = true, frame = Vector2(112, 112), feet = Vector2(56, 111), flips = true},
		"idle": {sheet = "res://Assets/Characters/Greyson/greyson_idle.png", frames = [0, 1, 2, 3],
			times = [0.20, 0.16, 0.20, 0.16], loop = true, frame = Vector2(112, 112), feet = Vector2(56, 111), flips = true}},
	{"name": &"matt", "enter": &"walk",
		"walk": {sheet = "res://Assets/Characters/Matt/matt_walk.png", frames = [0, 1, 2, 3, 4, 5], times = [0.10],
			loop = true, frame = Vector2(96, 96), feet = Vector2(48, 95), flips = true},
		"idle": {sheet = "res://Assets/Characters/Matt/matt_idle.png", frames = [0, 1, 2, 3], times = [0.16],
			loop = true, frame = Vector2(96, 96), feet = Vector2(48, 95), flips = true}},
	{"name": &"mason", "enter": &"walk",
		"walk": {sheet = "res://Assets/Characters/Mason/mason_sheet.png", frames = [2, 3, 4, 5], times = [0.125],
			loop = true, frame = Vector2(64, 64), feet = Vector2(32, 63), flips = true},
		"idle": {sheet = "res://Assets/Characters/Mason/mason_sheet.png", frames = [0, 1], times = [0.4], loop = true,
			frame = Vector2(64, 64), feet = Vector2(32, 63), flips = true}},
	{"name": &"josh", "enter": &"glide",
		"walk": {sheet = "res://Assets/Characters/Josh/josh_glide.png", frames = [0, 1, 2, 3], times = [0.11],
			loop = true, frame = Vector2(80, 80), feet = Vector2(40, 79), flips = true},
		"arrive": {sheet = "res://Assets/Characters/Josh/josh_dismount.png", frames = [0, 1, 2],
			times = [0.12, 0.16, 0.24], loop = false, frame = Vector2(80, 80), feet = Vector2(40, 79), flips = true},
		"idle": {sheet = "res://Assets/Characters/Josh/josh_idle.png", frames = [0, 1, 2, 3], times = [0.15],
			loop = true, frame = Vector2(80, 80), feet = Vector2(40, 79), flips = true}},
	{"name": &"danny", "enter": &"walk",
		"walk": {sheet = "res://Assets/Characters/Danny/danny_walk.png", frames = [0, 1, 2, 3], times = [0.14],
			loop = true, frame = Vector2(64, 64), feet = Vector2(32, 63), flips = true},
		"idle": {sheet = "res://Assets/Characters/Danny/danny_walk.png", frames = [1], times = [1.0], loop = true,
			frame = Vector2(64, 64), feet = Vector2(32, 63), flips = true}},
	{"name": &"carter", "enter": &"teleport",
		"arrive": {sheet = "res://Assets/Characters/Carter/carter_intro.png", frames = [0, 1, 2, 3, 4],
			times = [0.09, 0.09, 0.10, 0.10, 0.10], loop = false, frame = Vector2(96, 96), feet = Vector2(48, 95), flips = true},
		"idle": {sheet = "res://Assets/Characters/Carter/carter_idle.png", frames = [0, 1, 2, 3], times = [0.18],
			loop = true, frame = Vector2(96, 96), feet = Vector2(48, 95), flips = true}},
	{"name": &"liam", "enter": &"bob",
		"idle": {sheet = "res://Assets/Characters/Liam/liam.png", frames = [0], times = [1.0], loop = true,
			frame = Vector2(64, 64), feet = Vector2(32, 63), flips = true},
		"talk": {sheet = "res://Assets/Characters/Liam/liam_glasses_push.png", frames = [0, 1, 2, 3, 4, 5, 6, 7, 8],
			times = [0.08], loop = false, frame = Vector2(64, 64), feet = Vector2(32, 63), flips = true}},
]


static func room_layer_path(layer: StringName) -> String:
	return ROOM_DIR + "room_%s.png" % layer


# The drawn room, once its layers are in and imported.
static func final_room() -> bool:
	return USE_FINAL_ROOM and ROOM_LAYERS.all(func(layer: StringName) -> bool: return ResourceLoader.exists(room_layer_path(layer)))


# The drawn god, once his hover is in and imported.
static func final_god() -> bool:
	return USE_FINAL_GOD and ResourceLoader.exists(GOD[&"hover"].sheet)


static func final_void() -> bool:
	return USE_FINAL_VOID and ResourceLoader.exists(VOID_BG)


static func final_seated() -> bool:
	return USE_FINAL_SEATED and ResourceLoader.exists(SEATED_SHEET)


static func final_moustache() -> bool:
	return USE_FINAL_MOUSTACHE and ResourceLoader.exists(MOUSTACHE_SHEET)


static func final_prop() -> bool:
	return USE_FINAL_PROP and ResourceLoader.exists(MOUSTACHE_PROP.sheet)


static func final_standing() -> bool:
	return USE_FINAL_STANDING and ResourceLoader.exists(STANDING_RAGE) and ResourceLoader.exists(STANDING_ZAP)


# Where the finale goes when it ends, however it ends (USE_GOD_FIGHT).
static func after_finale_scene() -> String:
	if USE_GOD_FIGHT and ResourceLoader.exists(GOD_FIGHT_SCENE):
		return GOD_FIGHT_SCENE
	return CARD_SCENE


# His spec at the desk: the drawn one, or the stand-in's gaming, or its idle for everything after it.
static func seated(name: StringName, drawn: bool) -> Dictionary:
	if drawn:
		return SEATED[name]
	return PLACEHOLDER_SEATED[&"gaming" if name == &"gaming" else &"idle"]


# His spec on his feet: the drawn one, or its stand-in, the stand-in's rage serving the rage's pair.
static func standing(name: StringName, drawn: bool) -> Dictionary:
	if drawn:
		return STANDING[name]
	return PLACEHOLDER_STANDING[&"rage" if name == &"rage_shut" else name]
