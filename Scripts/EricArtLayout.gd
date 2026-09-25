extends RefCounted

# Every number that depends on how Eric, his bear-hug sheet and his thrown sword are drawn, so a
# redraw at a new frame size only needs this file. Points and boxes are in texels on a frame,
# origin top-left. EricScript and EricThrownSwordScript apply the sizes, offsets and shapes at
# runtime; the values in EricScene and EricThrownSwordScene are copies for the editor.

const SCALE := 3.0

#ERIC SHEETS (eric_sheet_v2.png, eric_bearhug_v2.png)
const FRAME_SIZE := Vector2(256, 192)
const SHEET_FRAMES := 40
const HUG_FRAMES := 15
# Where the frames are drawn relative to Eric's origin, in texels. It keeps his feet 63.5 texels
# below the origin, where the 128-texel frames had them. The bear hug's planted sword is drawn in
# his frame space, so it uses this too.
const SPRITE_OFFSET := Vector2(0, -32)
# Where his fight y-sorts him, in texels from his origin: the middle of the row his feet stand on.
# The sprite sits here and its offset takes the same amount back, so he is drawn exactly where
# SPRITE_OFFSET puts him and his body, hurtbox and frame_local() don't move.
const SORT_POINT := Vector2(0, 63.5)

# His torso and legs on the idle frames: collision box and hurtbox.
const BODY_BOX := Rect2(102, 120, 58, 72)
# Active during the bear hug's lunge.
const GRAB_BOX := Rect2(102, 120, 58, 72)
# The whirlwind's sword sweep, an ellipse at waist height. The blade tips reach 126 texels out,
# a little past it.
const WHIRLWIND_CENTRE := Vector2(128, 156)
const WHIRLWIND_RADII := Vector2(118, 35)

# Blade tip on earthquake frame 7, where the slam lands.
const SLAM_PIXEL := Vector2(93, 191)
# Sword centre on frame 34, as it leaves his hand.
const THROW_RELEASE_PIXEL := Vector2(144, 92)
# Centre of the sword he holds on catch frame 39, where the returning sword arrives.
const THROW_CATCH_CENTRE := Vector2(81, 111.5)
# That sword's lean from upright, in degrees clockwise. The upright spin frame is the nearest
# match, mirrored or not, so the returning sword turns from it to this as it arrives.
const THROW_CATCH_ANGLE := -11.31
# The row his feet stand on; a flying sword's shadow is measured from it.
const FEET_ROW := 191.0

# Where the player's centre can be put inside the ropes: the floor their body fits on, kept 3 px
# further in again so a toss never parks them flush against a rope. Read by the bear hug, which puts
# the player where his art draws them, and by EricBroken, which drives them in beside him.
const PLAYER_AREA := Rect2(126, 148.5, 1668, 783)

# Bottom middle of the frame, under his feet. The bear hug's player centres are measured from it.
const FEET_ANCHOR := Vector2(128, 192)
# Centre of the player drawn in his arms on bear-hug frames 7-10.
const HUG_PLAYER_CENTRES := {
	7: Vector2(-1, -30),
	8: Vector2(-0.5, -31),
	9: Vector2(0, -27.5),
	10: Vector2(-0.5, -27.5),
}
# Centre of the player thrown on frame 11, where they reappear when frame 12 starts.
const HUG_RELEASE_CENTRE := Vector2(30.5, -83.5)
# Just above his head on downed frames 27-31, where the finisher's daze stars circle.
const DAZE_HEAD_PIXEL := Vector2(128, 112)
# The frame a delayed slam (EricPacing V2) holds before impact: the sword at the top of its arc.
const SLAM_HOLD_FRAME := 6

#WINDED (EricWinded, EricPacing V2's window after a chain)
# eric_winded.png: 4 frames of 256x192, feet at (128, 191), leaning on his sword planted in the frame
# and panting, looped by `winded_final`. The placeholder, `winded`, alternates idle frames 25 and 26.
const USE_FINAL_WINDED := true
const FINAL_WINDED := {
	"texture": "res://Assets/Characters/Eric/eric_winded.png",
	"hframes": 4,
	"anim": &"winded_final",
}
const PLACEHOLDER_WINDED := {"anim": &"winded"}

#BROKEN (EricBroken, a full Break gauge)
# eric_broken.png: 8 frames of 256x192, feet at (128, 191): the Break knocks his sword out of his grip
# as he reels (0-2), he drops to one knee (3 reaching, 4 gripping), `broken_final`, then slumps in a
# loop (5-7), `broken_final_loop`. The placeholder, `broken`, loops his downed frames 27-31, which
# draw the sword in his hands.
const USE_FINAL_BROKEN := true
# Just above his head on the slumped frames, where the daze stars circle; `heads` has it frame by frame.
const BROKEN_HEAD_PIXEL := Vector2(137, 125)
const FINAL_BROKEN := {
	"texture": "res://Assets/Characters/Eric/eric_broken.png",
	"hframes": 8,
	"intro": &"broken_final",
	"loop": &"broken_final_loop",
	"head": BROKEN_HEAD_PIXEL,
	# By frame; the reel's (0-2) has none, so the stars wait for him to go down.
	"heads": {3: Vector2(123, 120), 4: Vector2(123, 120), 5: Vector2(138, 124), 6: Vector2(141, 127), 7: Vector2(133, 124)},
	# His sword, knocked into the mat: eric_broken_sword.png, 7 frames drawn in his own frame space, so
	# it goes where his sprite goes, at the Break spot in the world. It plunges (0-3), wobbles (4-5) and
	# stands planted (6) from the Break's first tick, behind him.
	"sword": {
		"texture": "res://Assets/Characters/Eric/eric_broken_sword.png",
		"hframes": 7,
		"frame_times": [0.04, 0.05, 0.05, 0.05, 0.05, 0.05],
		# Its crossguard's centre, where the return flight picks it up, and the row it enters the mat on.
		"guard": Vector2(88, 150),
		"mat_row": 186.0,
	},
	# Getting up: one knee, hand out (broken frame `reach_frame`), long enough for an uppercut's shove
	# to finish, then his recall reach and catch on the main sheet as his sword flies back to him.
	"reach_frame": 3,
	"reach_time": 0.3,
}
const PLACEHOLDER_BROKEN := {"intro": &"", "loop": &"broken", "head": DAZE_HEAD_PIXEL}

#JUGGLED (EricJuggled, under the tiered finisher's uppercuts)
# eric_juggle.png: 10 frames of 256x192, feet at (128, 191), none holding the sword, which the Break or
# the first uppercut knocks into the mat (EricDroppedSword): hit 0-1, a clockwise cartwheel round
# (128, 146) looping 2-5, the crash 6-7, a bounce 8, then lying 9. `launch` plays the hit into the
# tumble, `crash` the crash, bounce and lying frames, `down` holds him lying.
const USE_FINAL_JUGGLE := true
const FINAL_JUGGLE := {
	"texture": "res://Assets/Characters/Eric/eric_juggle.png",
	"hframes": 10,
	"launch": &"juggle_hit_final",
	"tumble": &"juggle_tumble_final",
	"crash": &"juggle_crash_final",
	"down": &"juggle_down_final",
	# The highest row anything is drawn on while he's in the air (frame 4), so his top is this far over
	# his ground line when he isn't lifted.
	"top_row": 76,
}
# His downed frames with a hit flash, spinning through them in the air.
const PLACEHOLDER_JUGGLE := {
	"launch": &"juggle_hit",
	"tumble": &"juggle_tumble",
	"crash": &"juggle_crash",
	"down": &"juggle_down",
	"top_row": 80,
}
# The centre his cartwheel turns round.
const JUGGLE_TUMBLE_CENTRE := Vector2(128, 146)
# The whole of him stays at least this far below the top of the arena at the top of his flight: the
# finisher scales the juggle's heights down to fit (juggle_headroom).
const JUGGLE_TOP_MARGIN := 12.0
# His shadow on the mat while he's in the air: eric_leap_shadow.png, frame `lift / shadow_step` (0 low,
# 2 high), under his feet.
const JUGGLE_SHADOW := {
	"texture": "res://Assets/Characters/Eric/eric_leap_shadow.png",
	"hframes": 3,
	"scale": 3.0,
	"alpha": 0.35,
	"step": 100.0,
}
# Knight Breaker's crash: eric_crash_crater.png, 4 frames of 128x48 on the floor layer, its pivot on the
# point his crash lands on (his feet). Flash, crack and settle, then held, then faded.
const CRASH_CRATER := {
	"texture": "res://Assets/Characters/Eric/eric_crash_crater.png",
	"hframes": 4,
	"scale": 3.0,
	"pivot": Vector2(64, 25),
	"impact_pixel": Vector2(128, 191),
	"frame_times": [0.06, 0.08, 0.30],
	"hold": 3.0,
	"fade_time": 0.8,
}
# Lying after the crash, before he gets up for his sword (EricBroken's retrieve).
const JUGGLE_LYING_TIME := 0.3
# From a juggle that killed him, how long before the outro's first line: his fall and his crash first.
const JUGGLE_OUTRO_DELAY := 1.8
# Every crash, whatever the tier. Its level is baked in.
const CRASH_THUD_SFX := {"stream": "res://Assets/Audio/SFX/eric_crash_thud.wav", "pitch": 1.0, "volume_db": 0.0}

#BREAK GAUGE (BreakGaugeUI, BossBreakGauge)
# Positions are HUD px, and times real seconds.
# From this share of full it pulses.
const BREAK_GAUGE_PULSE_FROM := 0.8
# Real seconds for the fill to catch up with the gauge.
const BREAK_GAUGE_FILL_TIME := 0.15
const USE_FINAL_BREAK_GAUGE := true
# A thin bar under his health bar, styled like it. It shatters into shards of itself thrown out and
# faded, under a BREAK! that rises and fades.
const PLACEHOLDER_BREAK_GAUGE := {
	"position": Vector2(770, 96),
	"size": Vector2(380, 10),
	"fill_color": Color(1.0, 0.78, 0.2),
	"pulse_modulate": Color(1.8, 1.8, 1.8),
	"pulse_time": 0.12,
	# While it takes nothing after a Break.
	"locked_modulate": Color(0.5, 0.5, 0.5),
	"shards": 12,
	"shard_size": Vector2(18, 10),
	"shard_speed": Vector2(220, 520),
	"shatter_time": 0.45,
	"word": "BREAK!",
	"word_size": Vector2(380, 60),
	"font_size": 44,
	"outline": 8,
	"word_colors": [Color(1.0, 0.85, 0.2), Color(1, 1, 1)],
	"word_frame_time": 0.08,
	"word_time": 1.0,
	"word_rise": 24.0,
}
# The daze meter, in the health bar's own gothic language and hung 6 px under its bottom rail, so the
# two read as one instrument. EricScript places it from health_bar.break_gauge_anchor(); this
# position is the same point written out, for anything that builds the gauge on its own.
# The _3x art is drawn at scale 1, each piece placed from the frame's top-left.
const FINAL_BREAK_GAUGE := {
	"position": Vector2(768, 160),
	"size": Vector2(384, 21),
	"frame": "res://Assets/UI/break_gauge_frame_3x.png",
	"fill": "res://Assets/UI/break_gauge_fill_3x.png",
	"fill_offset": Vector2(21, 6),
	# Revealed left to right in whole texels, 3 px each.
	"fill_steps": 114,
	# From BREAK_GAUGE_PULSE_FROM up, a looping overlay that lights the brass, with a hot fill swapped
	# in on the same frame. They are the pulse: nothing brightens it on top.
	"pulse": "res://Assets/UI/break_gauge_pulse_3x.png",
	"pulse_hframes": 4,
	"pulse_offset": Vector2(-18, 0),
	"pulse_frame_times": [0.10, 0.09, 0.11, 0.09],
	"fill_hot": "res://Assets/UI/break_gauge_fill_hot_3x.png",
	"locked_modulate": Color(0.5, 0.5, 0.5),
	# Played once on a Break, over the emptied frame.
	"shatter": "res://Assets/UI/break_gauge_shatter_3x.png",
	"shatter_hframes": 6,
	"shatter_offset": Vector2(-24, -36),
	"shatter_frame_times": [0.05, 0.05, 0.06, 0.06, 0.07, 0.07],
	# Centred under the gauge on the mat. It doesn't rise.
	"word_texture": "res://Assets/UI/break_text_3x.png",
	"word_hframes": 2,
	"word_offset": Vector2(84, 27),
	"word_frame_time": 0.08,
	"word_time": 1.0,
	"word_rise": 0.0,
}
# The Break's sting, on the Break frame. Its level is baked in.
const BREAK_STING_SFX := [
	{"stream": "res://Assets/Audio/SFX/break_sting.wav", "pitch": 1.0, "volume_db": 0.0},
]

#THROWN SWORD (eric_thrown_sword_v2.png, eric_sword_planted_v2.png)
const SPIN_FRAMES := 8
# Spin frames pointing down, which it lands on, and up, which he catches.
const SPIN_LANDING_FRAME := 2
const SPIN_CATCH_FRAME := 6
const PLANTED_FRAMES := 2
# Offset that puts the planted sword's ground contact on its origin, in texels.
const PLANTED_OFFSET := Vector2(0, -59)
# The spinning sword's hitbox, in px.
const SWORD_HITBOX_RADIUS := 108.0
# The parry aura on the blade in flight (ParryTell.glow), as a multiple of parry_glow.png's texel.
# It hangs off the Sword sprite, so it already rides that sprite's SCALE; this is only how far the
# art has to be opened up to ring a greatsword instead of the small projectile it was drawn for.
const SWORD_GLOW_SCALE := 4.0


static func winded() -> Dictionary:
	return FINAL_WINDED if USE_FINAL_WINDED else PLACEHOLDER_WINDED


static func broken() -> Dictionary:
	return FINAL_BROKEN if USE_FINAL_BROKEN else PLACEHOLDER_BROKEN


static func break_gauge() -> Dictionary:
	return FINAL_BREAK_GAUGE if USE_FINAL_BREAK_GAUGE else PLACEHOLDER_BREAK_GAUGE


static func juggle() -> Dictionary:
	return FINAL_JUGGLE if USE_FINAL_JUGGLE else PLACEHOLDER_JUGGLE


# Position in Eric's body space (texels, before his scale) of a point on his frames, drawn
# mirrored when flip_h is set.
static func frame_local(point: Vector2, flip_h := false) -> Vector2:
	var local := point - FRAME_SIZE / 2.0
	if flip_h:
		local.x = -local.x
	return local + SPRITE_OFFSET


# Screen-px offset from Eric's origin of the centre of a pixel on his frames.
static func pixel_offset(pixel: Vector2) -> Vector2:
	return frame_local(pixel + Vector2(0.5, 0.5)) * SCALE


# Screen-px offset from Eric's origin of a point given relative to FEET_ANCHOR.
static func feet_offset(offset: Vector2) -> Vector2:
	return frame_local(FEET_ANCHOR + offset) * SCALE
