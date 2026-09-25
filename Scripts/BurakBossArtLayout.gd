extends RefCounted

# Every number that depends on how Captain Burak is drawn, so a redraw only needs this file. Points and
# boxes are in texels on one of his frames, origin top-left.
#
# HIS BODY'S ORIGIN IS HIS FEET, as Matt's is: every spot BurakBossStateMachine names is a feet point, and
# every sheet stands his soles on the node. Most of his sheets are 96x96 with the feet at (48,95); the run
# is 128x96, and the cutlass and the laugh are 112 tall for the overhead and the hat hop, each with its
# `frame` and `feet` in FINAL_ANIMS. A sheet's feet are always on its frame's centre column.
#
# THE OFFSET FOLLOWS THE SHEET, NEVER THE ANIMATION. The 112-tall sheets stand on (0,-56) and the rest on
# (0,-48) (sheet_offset). BurakBossScript writes sprite.offset only when the sheet it swaps in stands on a
# different offset from the one it replaces, which only happens on the way into or out of the cutlass or
# the laugh. So the finisher's recoil and hop, which rock that offset and settle it back, never have it
# pulled from under them, and nor does BossJuggled, which owns it from the juggle's first frame until it
# restores the sheet and offset it found.
#
# Each body sheet has its own flag, so placeholder and final art go through the same code, and nothing
# loads a final sheet while its flag is off. The placeholders are the approved burak_boss.png - frame 0 for
# everything, frame 1 (the shot) for the pistol - with an AnimationPlayer clip in BurakBossScene moving
# the whole sprite under them. Every flag is on: the artist's fight set landed and was approved on
# 2026-09-23.
#
# A FLIPPED POINT MIRRORS AS A TEXEL, x becoming frame width - 1 - x, which is where the flipped sprite
# draws it.
#
# FX HEADINGS: every directional effect is drawn travelling right and down only, at Godot's angles (y
# down), and art_frame() flips it into the other three quadrants: flip_h when it goes left, flip_v when it
# goes up. The code never rotates a drawn frame.

const SCALE := 3.0

#BURAK (horizontal strips, facing right, soles on the feet row, the feet on the centre column)
const FRAME_SIZE := Vector2(96, 96)
const ANCHOR := Vector2(48, 95)
# Stands the bottom edge of ANCHOR's row on the sprite's origin. Comes to (0, -48).
const SPRITE_OFFSET := Vector2(FRAME_SIZE.x / 2.0 - ANCHOR.x, FRAME_SIZE.y / 2.0 - ANCHOR.y - 1.0)
const BURAK_SHEET := "res://Assets/Characters/BurakBoss/burak_boss.png"
const SHEET_DIR := "res://Assets/Characters/BurakBoss/"
const FX_DIR := "res://Assets/Characters/BurakBoss/FX/"
const SLASH_SHEET := SHEET_DIR + "burak_slash.png"
const SLASH_FRAME := Vector2(128, 112)
const SLASH_FEET := Vector2(64, 111)

# What the player can punch and turns to face, on a 96x96 frame: his body from the hat brim to his boots,
# the cutlass and the pistol left out. 108 x 246 px.
const BODY_BOX := Rect2(30, 14, 36, 82)

# The tricorn's top front point (where the badges and the daze stars stand), the pistol's muzzle on the
# frame the ball leaves on, and the keg's hand on the frame it leaves. The artist reported the idle, walk,
# broken, hit, laugh and defeat crowns; the rest were measured by matching the idle hat into each frame,
# which gives back every reported one to within a texel. One point an animation: its first frame, or the
# frame the attack acts on.
const PLACEHOLDER_CROWN := Vector2(48, 1)
const PLACEHOLDER_MUZZLE := Vector2(86, 70)
const PLACEHOLDER_RELEASE := Vector2(86, 38)
const CROWNS := {
	&"idle": Vector2(48, 1),
	&"walk": Vector2(48, 1),
	&"talk": Vector2(48, 1),
	&"laugh": Vector2(45, 12),
	&"throw": Vector2(50, 1),
	&"load": Vector2(48, 1),
	&"fire_aim": Vector2(48, 1),
	&"fire": Vector2(45, 1),
	&"taunt": Vector2(48, 0),
	&"run": Vector2(66, 2),
	&"slash_windup_0": Vector2(62, 17),
	&"slash_strike_0": Vector2(67, 19),
	&"slash_follow_0": Vector2(69, 19),
	&"slash_windup_1": Vector2(68, 20),
	&"slash_strike_1": Vector2(71, 24),
	&"slash_follow_1": Vector2(65, 23),
	&"slash_windup_2": Vector2(64, 16),
	&"slash_strike_2": Vector2(67, 19),
	&"slash_follow_2": Vector2(68, 21),
	&"broken": Vector2(48, 5),
	&"hit": Vector2(42, 2),
	&"defeat": Vector2(48, 24),
}
# The taunt's is where he blows the smoke off.
const MUZZLES := {
	&"fire_aim": Vector2(86, 70),
	&"fire": Vector2(86, 70),
	&"load": Vector2(76, 36),
	&"taunt": Vector2(64, 37),
}
const RELEASES := {
	&"throw": Vector2(86, 38),
}
# Where the finisher's daze stars circle and a badge's tip stands, over his crown.
const DAZE_GAP := 34.0
const TELL_GAP := 12.0

#ANIMATIONS
# name: sheet, frames in order, seconds on each (the last value repeats) and whether it loops. Optional:
# `frame` and `feet` for a sheet that isn't 96x96 with its feet at (48,95), and `motion`, the
# AnimationPlayer clip in BurakBossScene that moves the whole sprite under a placeholder's single frame.
# A pose the attack holds for its own time is a one-frame loop, so a state's own animation replaces it at
# once (play_state_anim). The pistol's sheet is split at the shot: fire_aim is its aim frame, fire the shot
# and the recoil held. The cutlass sheet is split per swing k (0 side, 1 backhand, 2 overhead) and beat.
# An animation goes by its sheet's flag: the first word of its name.
const USE_FINAL_ANIMS := {
	&"idle": true,
	&"walk": true,
	&"talk": true,
	&"laugh": true,
	&"throw": true,
	&"load": true,
	&"fire": true,
	&"taunt": true,
	&"run": true,
	&"slash": true,
	&"broken": true,
	&"hit": true,
	&"defeat": true,
}

const PLACEHOLDER_ANIMS := {
	&"idle": {sheet = BURAK_SHEET, frames = [0], times = [1.0], loop = true, motion = &"idle"},
	&"walk": {sheet = BURAK_SHEET, frames = [0], times = [1.0], loop = true, motion = &"walk"},
	&"talk": {sheet = BURAK_SHEET, frames = [0], times = [1.0], loop = true, motion = &"talk"},
	&"laugh": {sheet = BURAK_SHEET, frames = [0], times = [1.0], loop = true, motion = &"laugh"},
	&"throw": {sheet = BURAK_SHEET, frames = [0], times = [0.56], loop = false, motion = &"throw"},
	&"load": {sheet = BURAK_SHEET, frames = [0], times = [0.56], loop = true, motion = &"load"},
	&"fire_aim": {sheet = BURAK_SHEET, frames = [1], times = [1.0], loop = true},
	&"fire": {sheet = BURAK_SHEET, frames = [1], times = [0.26], loop = false, motion = &"fire"},
	# Open: leaning back, pleased with himself.
	&"taunt": {sheet = BURAK_SHEET, frames = [0], times = [1.0], loop = true, motion = &"taunt"},
	&"run": {sheet = BURAK_SHEET, frames = [0], times = [1.0], loop = true, motion = &"run"},
	&"slash_windup_0": {sheet = BURAK_SHEET, frames = [0], times = [1.0], loop = true, motion = &"slash_windup"},
	&"slash_strike_0": {sheet = BURAK_SHEET, frames = [0], times = [1.0], loop = true, motion = &"slash_strike"},
	&"slash_follow_0": {sheet = BURAK_SHEET, frames = [0], times = [1.0], loop = true, motion = &"slash_follow"},
	&"slash_windup_1": {sheet = BURAK_SHEET, frames = [0], times = [1.0], loop = true, motion = &"slash_windup"},
	&"slash_strike_1": {sheet = BURAK_SHEET, frames = [0], times = [1.0], loop = true, motion = &"slash_strike"},
	&"slash_follow_1": {sheet = BURAK_SHEET, frames = [0], times = [1.0], loop = true, motion = &"slash_follow"},
	&"slash_windup_2": {sheet = BURAK_SHEET, frames = [0], times = [1.0], loop = true, motion = &"slash_windup"},
	&"slash_strike_2": {sheet = BURAK_SHEET, frames = [0], times = [1.0], loop = true, motion = &"slash_strike"},
	&"slash_follow_2": {sheet = BURAK_SHEET, frames = [0], times = [1.0], loop = true, motion = &"slash_follow"},
	&"broken": {sheet = BURAK_SHEET, frames = [0], times = [1.0], loop = true, motion = &"broken"},
	&"hit": {sheet = BURAK_SHEET, frames = [0], times = [0.24], loop = false, motion = &"hit"},
	&"defeat": {sheet = BURAK_SHEET, frames = [0], times = [1.0], loop = false, motion = &"defeated"},
}

# The artist's timings (ANIMS_FOR_CODER). One loop of `load` loads one bullet, and the attacks rescale it
# to their bullet time (BurakBossScript.play_anim's loop_time). The throw's keg leaves on frame 2.
const FINAL_ANIMS := {
	&"idle": {sheet = SHEET_DIR + "burak_idle.png", frames = [0, 1, 2, 3], times = [0.30, 0.20, 0.12, 0.20], loop = true},
	# A swagger, facing screen-right; it plays straight down his walk-in.
	&"walk": {sheet = SHEET_DIR + "burak_walk.png", frames = [0, 1, 2, 3, 4, 5], times = [0.12], loop = true},
	&"talk": {sheet = TALK_SHEET, frames = [0], times = [TALK_FRAME_TIME], loop = true},
	# Doubled over, slapping his knee on frames 1 and 3.
	&"laugh": {sheet = SHEET_DIR + "burak_laugh.png", frames = [0, 1, 2, 3], times = [0.13, 0.11, 0.13, 0.11], loop = true,
		frame = Vector2(96, 112), feet = Vector2(48, 111)},
	&"throw": {sheet = SHEET_DIR + "burak_throw.png", frames = [0, 1, 2, 3], times = [0.16, 0.12, 0.10, 0.18], loop = false},
	&"load": {sheet = SHEET_DIR + "burak_load.png", frames = [0, 1, 2, 3], times = [0.14, 0.14, 0.12, 0.16], loop = true},
	&"fire_aim": {sheet = SHEET_DIR + "burak_fire.png", frames = [0], times = [1.0], loop = true},
	&"fire": {sheet = SHEET_DIR + "burak_fire.png", frames = [1, 2], times = [0.10, 0.16], loop = false},
	# Blowing the smoke off his muzzle, then a twirl: open for punches.
	&"taunt": {sheet = SHEET_DIR + "burak_taunt.png", frames = [0, 1, 2, 3], times = [0.30, 0.30, 0.12, 0.12], loop = true},
	&"run": {sheet = SHEET_DIR + "burak_run.png", frames = [0, 1, 2, 3, 4, 5], times = [0.08], loop = true,
		frame = Vector2(128, 96), feet = Vector2(64, 95)},
	&"slash_windup_0": {sheet = SLASH_SHEET, frames = [0], times = [1.0], loop = true, frame = SLASH_FRAME, feet = SLASH_FEET},
	&"slash_strike_0": {sheet = SLASH_SHEET, frames = [1], times = [1.0], loop = true, frame = SLASH_FRAME, feet = SLASH_FEET},
	&"slash_follow_0": {sheet = SLASH_SHEET, frames = [2], times = [1.0], loop = true, frame = SLASH_FRAME, feet = SLASH_FEET},
	&"slash_windup_1": {sheet = SLASH_SHEET, frames = [3], times = [1.0], loop = true, frame = SLASH_FRAME, feet = SLASH_FEET},
	&"slash_strike_1": {sheet = SLASH_SHEET, frames = [4], times = [1.0], loop = true, frame = SLASH_FRAME, feet = SLASH_FEET},
	&"slash_follow_1": {sheet = SLASH_SHEET, frames = [5], times = [1.0], loop = true, frame = SLASH_FRAME, feet = SLASH_FEET},
	&"slash_windup_2": {sheet = SLASH_SHEET, frames = [6], times = [1.0], loop = true, frame = SLASH_FRAME, feet = SLASH_FEET},
	&"slash_strike_2": {sheet = SLASH_SHEET, frames = [7], times = [1.0], loop = true, frame = SLASH_FRAME, feet = SLASH_FEET},
	&"slash_follow_2": {sheet = SLASH_SHEET, frames = [8], times = [1.0], loop = true, frame = SLASH_FRAME, feet = SLASH_FEET},
	&"broken": {sheet = SHEET_DIR + "burak_broken.png", frames = [0, 1, 2, 3], times = [0.18], loop = true},
	&"hit": {sheet = SHEET_DIR + "burak_hit.png", frames = [0, 1], times = [0.10, 0.14], loop = false},
	# Struck, reeling, down on his knees and slumped, held.
	&"defeat": {sheet = SHEET_DIR + "burak_defeat.png", frames = [0, 1, 2, 3, 4, 5],
		times = [0.14, 0.18, 0.14, 0.12, 0.18, 1.0], loop = false},
}

#TALK POSES
# The poses the lines' `captain` tags name, as the two frames each flaps between: mouth shut, mouth open.
const TALK_FRAME_TIME := 0.12
const TALK_SHEET := SHEET_DIR + "burak_talk.png"
const TALK_POSES := {
	&"smug": [0, 1],
	&"laugh": [2, 3],
	# "Think!", a finger tapping his temple.
	&"point": [4, 5],
	&"shrug": [6, 7],
}

#THE CUTLASS
# What swing k (0 side, 1 backhand, 2 overhead) hits, in facing-space px from his feet (x forward, y down),
# mirrored when he faces left (BurakBossScript.slash_box). Each is the box round that swing's drawn blade in
# front of him, fist to tip from wind-up through strike to follow-through, and never past it
# (art_source/burak_boss_anims/sheets.py's SLASH lines, the backhand as lowered). Each overlaps
# BurakBossSlashScript.REACH, so every player his tracking leaves at a strike is hit: the no-walk-out rule.
const SLASH_BOXES := [Rect2(0, -184, 126, 157), Rect2(0, -186, 129, 162), Rect2(0, -250, 126, 244)]

#THE HUD
# His bullet timer (BurakBossPips): pip 0's centre from HOME, in px, with the row running right from it,
# FX.pips.spacing texels apart. Fixed in the world, beside his head on the gun side. An estimate until a
# capture places it.
const PIPS_OFFSET := Vector2(96, -246)
# The rounds he never fired, fading as he lowers the gun after a volley.
const PIPS_FADE := 0.3
# The tutorial's hints (BurakBossScript.show_hint): bottom centre on his HUD layer, above the player's
# bars, each once a fight. `bottom` is the text's bottom edge in screen px.
const HINT := {font_size = 33, outline = 6, color = Color("#F2F3FF"), outline_color = Color("#06181A"), width = 1100.0,
	bottom = 924.0, fade = 0.2}

#FX (FX_FOR_CODER: horizontal strips, never rotated)
# `offset` is the frame's centre minus its pivot, in texels, for a centred sprite, so the node sits on the
# pivot.
const FX := {
	# The shot: a small iron ball with a spark trail, 5 headings x 4 flicker frames, pivoted on the ball.
	&"ball": {texture = FX_DIR + "burak_ball.png", hframes = 20, headings = [0.0, 22.5, 45.0, 67.5, 90.0],
		frames_per_heading = 4, frame_time = 0.05, offset = Vector2.ZERO},
	# 3 headings x 5 frames on the muzzle: 0-1 the flash, 2-4 the smoke. flip_h only, never flip_v: the
	# smoke always rises.
	&"muzzle": {texture = FX_DIR + "burak_muzzle.png", hframes = 15, headings = [0.0, 45.0, 90.0], frames_per_heading = 5,
		flash_frames = [0, 1], smoke_frames = [2, 3, 4], frame_time = 0.04, offset = Vector2.ZERO},
	# The parry spark, for the shot and the cutlass alike.
	&"clash": {texture = FX_DIR + "burak_clash.png", hframes = 5, frame_time = 0.04, offset = Vector2.ZERO},
	# One arc per swing, 3 frames each (side 0-2, backhand 3-5, overhead 6-8), on the slash sheet's own
	# 128x112 frame and feet, so it goes on his node, flipped with him and drawn over him. A swing's three
	# start on the body's strike frame: the first two span the strike, the third the follow-through's start.
	&"slash_trail": {texture = FX_DIR + "burak_slash_trail.png", hframes = 9, frames_per_swing = 3, frame_time = 0.04,
		offset = Vector2(0, -56)},
	# A keg's explosion on its floor point, carrying its own floor shockwave. Its first frame covers the keg,
	# so the keg is hidden on it.
	&"blast": {texture = FX_DIR + "burak_blast.png", hframes = 8, frame_time = 0.05, offset = Vector2(0, -40)},
	# The whole-arena flash, smoke and ash: world space from (0,0), centred = false, at SCALE, on this
	# z_index on his projectile layer, which keeps it under every CanvasLayer and so under the HUD. The
	# later blasts of a volley start at smoke_first: f2 still carries the flash's colour at 31% over most of
	# the screen.
	&"blast_screen": {texture = FX_DIR + "burak_blast_screen.png", hframes = 5, frame_time = 0.05, z_index = 20,
		smoke_first = 3},
	# The bullet timer: f0 empty, f1 the loading flash, f2 loaded, f3 spent.
	&"pips": {texture = FX_DIR + "burak_pips.png", hframes = 4, empty = 0, flash = 1, loaded = 2, spent = 3,
		flash_time = 0.1, spacing = 18.0, offset = Vector2.ZERO},
}

#THE KEG BLOCK
# Everything drawn to the keg's size, in one place, so a redraw of the keg edits only this block. Texels on
# each sheet's own frame. The keg's pivot is its floor point, which the break, the landing dust and the
# marker share, so all four go on the same position. Nothing may hard-code these numbers elsewhere.
# The 2x keg, the user's pick over 1.5x (2026-09-23). Its fuse tip stands 156 px over its floor point.
const KEG := {
	texture = FX_DIR + "burak_barrel.png",
	hframes = 7,
	frame_size = Vector2(48, 56),
	pivot = Vector2(24, 56),
	offset = Vector2(0, -28),
	# f0 intact, f1 cracked once, f2 cracked twice. The lit fuse is an OVERLAY on a second sprite over
	# whichever of those is showing, so a cracked keg burns too.
	damage_frames = [0, 1, 2],
	fuse_frames = [3, 4, 5, 6],
	fuse_frame_time = 0.06,
	# The drawn body with the fuse left out, measured on f0.
	body = Rect2(7, 9, 34, 46),
	# What a punch has to reach: the body grown by 6 px (2 texels) all round. 114 x 150 px.
	hurtbox = Rect2(5, 7, 38, 50),
	# Where it stands on the mat: the artist's "about 28x9 texels" on the pivot, which is the drawn base.
	footprint = Rect2(10, 47, 28, 9),
}
const KEG_FX := {
	# Every piece has landed by f5, which is held as the debris.
	&"barrel_break": {texture = FX_DIR + "burak_barrel_break.png", hframes = 6, frame_time = 0.05, debris_frame = 5,
		offset = Vector2(0, -40)},
	&"barrel_land": {texture = FX_DIR + "burak_barrel_land.png", hframes = 5, frame_time = 0.05, offset = Vector2(0, -12)},
	# Centred on the landing point, looping.
	&"barrel_marker": {texture = FX_DIR + "burak_barrel_marker.png", hframes = 4, frame_time = 0.1, offset = Vector2.ZERO},
}

#THE JUGGLE (the Break's tiered uppercut; BossJuggled reads exactly this shape)
# A sheet of its own: its frame is not his 96x96 and its origin is not his feet, so its texels go through
# BossJuggled.texel_point(), never frame_local(). top_row is the tumble's highest row (frames 2-6).
const USE_FINAL_JUGGLE := true
const FINAL_JUGGLE := {
	"texture": "res://Assets/Characters/BurakBoss/burak_boss_juggle.png",
	"hframes": 12,
	"frame_size": Vector2(192, 144),
	"offset": Vector2(0, -72),
	"feet": Vector2(96, 143),
	"tumble_centre": Vector2(96, 86),
	"top_row": 35,
	"clips": {
		&"launch": {"frames": [0, 1], "times": [0.06, 0.08], "loop": false},
		&"tumble": {"frames": [2, 3, 4, 5, 6], "times": [0.16, 0.07, 0.06, 0.06, 0.07], "loop": true},
		&"crash": {"frames": [7, 8, 9], "times": [0.06, 0.08, 0.12], "loop": false},
		&"down": {"frames": [10, 11], "times": [0.4, 0.4], "loop": true},
	},
	"shadow": {
		"texture": "res://Assets/Characters/BurakBoss/burak_boss_leap_shadow.png",
		"hframes": 3, "scale": 3.0, "alpha": 0.35, "step": 100.0, "offset": Vector2.ZERO,
	},
	"lying_time": 0.3,
	"outro_delay": 1.8,
	"crash_sfx": {"stream": "res://Assets/Audio/SFX/eric_crash_thud.wav", "pitch": 1.0, "volume_db": 0.0},
}

#AUDIO
# His own synthesized set (art_source/audio_burak/make_burak_sfx.py), every file at a -3 dBFS peak, so the volume
# here is the whole mix. The ringing ears are Matt's and the Break's sting is everyone's.
const SFX_DIR := "res://Assets/Audio/SFX/"
const SFX := {
	&"throw": {stream = SFX_DIR + "burak_throw.wav", pitch = 1.0, volume_db = -6.0},
	&"barrel_land": {stream = SFX_DIR + "burak_barrel_land.wav", pitch = 1.0, volume_db = -4.0},
	&"barrel_hit": {stream = SFX_DIR + "burak_barrel_hit.wav", pitch = 1.0, volume_db = -4.0},
	&"barrel_break": {stream = SFX_DIR + "burak_barrel_break.wav", pitch = 1.0, volume_db = -2.0},
	&"barrel_tonk": {stream = SFX_DIR + "burak_barrel_tonk.wav", pitch = 1.0, volume_db = -8.0},
	# Plays for as long as the kegs burn, so its stream loops; it sits under everything.
	&"fuse_hiss": {stream = SFX_DIR + "burak_fuse_hiss.wav", pitch = 1.0, volume_db = -18.0, loop = true},
	&"load_click": {stream = SFX_DIR + "burak_load_click.wav", pitch = 1.0, volume_db = -6.0},
	&"gunshot": {stream = SFX_DIR + "burak_gunshot.wav", pitch = 1.0, volume_db = -2.0},
	&"blast": {stream = SFX_DIR + "burak_blast.wav", pitch = 1.0, volume_db = 0.0},
	&"misfire": {stream = SFX_DIR + "burak_misfire.wav", pitch = 1.0, volume_db = -6.0},
	&"laugh": {stream = SFX_DIR + "burak_laugh.wav", pitch = 1.0, volume_db = -3.0},
	&"slash": {stream = SFX_DIR + "burak_slash.wav", pitch = 1.0, volume_db = -6.0},
	&"clang": {stream = SFX_DIR + "burak_clang.wav", pitch = 1.0, volume_db = -4.0},
	&"taunt": {stream = SFX_DIR + "burak_taunt.wav", pitch = 1.0, volume_db = -10.0},
	&"ear_ring": {stream = SFX_DIR + "matt_ear_ring.wav", pitch = 1.0, volume_db = -14.0},
	&"break_sting": {stream = SFX_DIR + "break_sting.wav", pitch = 1.0, volume_db = 0.0},
}
# How many players a sound gets, for the ones a keg chain or a string overlaps with itself.
const SFX_VOICES := {&"barrel_land": 3, &"barrel_hit": 3, &"barrel_break": 3, &"blast": 2, &"gunshot": 2, &"slash": 2}

# "Main Character Energy", written for this fight. Its import loops it forward end to end (0 to 1535999),
# so nothing here rewrites its loop points, and it is never preloaded: the shared theme stands in if it is
# missing. -4 dB is the composer's level match; the stand-in keeps the -7 the other fights use.
const THEME := "res://Assets/Audio/Music/burak_theme.wav"
const THEME_DB := -4.0
const THEME_FALLBACK := "res://Assets/Audio/Music/boss_theme.ogg"
const THEME_FALLBACK_DB := -7.0


static func uses_final(anim_name: StringName) -> bool:
	return USE_FINAL_ANIMS.get(StringName(String(anim_name).get_slice("_", 0)), false)


static func anim(anim_name: StringName) -> Dictionary:
	if uses_final(anim_name):
		return FINAL_ANIMS[anim_name]
	return PLACEHOLDER_ANIMS.get(anim_name, PLACEHOLDER_ANIMS[&"idle"])


# The name of swing k's `beat` (&"windup", &"strike" or &"follow").
static func slash_anim(k: int, beat: StringName) -> StringName:
	return StringName("slash_%s_%d" % [beat, k])


# A talk pose: its sheet, its [shut, open] frames, and the clip that moves the stand-in while he talks.
static func talk(pose: StringName) -> Dictionary:
	if uses_final(&"talk"):
		return {sheet = TALK_SHEET, frames = TALK_POSES.get(pose, TALK_POSES[&"smug"]), motion = &"RESET"}
	return {sheet = BURAK_SHEET, frames = [0, 0], motion = &"talk"}


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


# Position from his feet, in px, of a point on a frame of `spec`'s sheet: the scaling is on his sprite, so
# it is already applied here.
static func frame_local(point: Vector2, spec: Dictionary) -> Vector2:
	return (point - frame_size(spec) / 2.0 + sheet_offset(spec)) * SCALE


# A texel of `anim_name`'s frames from his feet, in px, drawn flipped or not.
static func texel_local(point: Vector2, anim_name: StringName, flip := false) -> Vector2:
	var spec := anim(anim_name)
	if flip:
		point.x = frame_size(spec).x - 1.0 - point.x
	return frame_local(point, spec)


# BODY_BOX in px from his feet, on a 96x96 frame.
static func body_rect() -> Rect2:
	return Rect2(frame_local(BODY_BOX.position, {}), BODY_BOX.size * SCALE)


static func crown(anim_name: StringName) -> Vector2:
	if uses_final(anim_name) and CROWNS.has(anim_name):
		return CROWNS[anim_name]
	return PLACEHOLDER_CROWN


static func muzzle(anim_name: StringName) -> Vector2:
	if uses_final(anim_name) and MUZZLES.has(anim_name):
		return MUZZLES[anim_name]
	return PLACEHOLDER_MUZZLE


static func release(anim_name: StringName) -> Vector2:
	if uses_final(anim_name) and RELEASES.has(anim_name):
		return RELEASES[anim_name]
	return PLACEHOLDER_RELEASE


static func fx(key: StringName) -> Dictionary:
	return KEG_FX[key] if KEG_FX.has(key) else FX[key]


# A rect in texels on the keg's frame as px from its floor point: its hurtbox or footprint.
static func keg_rect(rect: Rect2) -> Rect2:
	var pivot: Vector2 = KEG.pivot
	return Rect2((rect.position - pivot) * SCALE, rect.size * SCALE)


# Which of a sheet's headings draws `heading`, and the flips that turn it the right way: [heading index,
# flip_h, flip_v]. The sheets travel right and down, so going left flips h and going up flips v.
static func art_frame(heading: Vector2, angles: Array) -> Array:
	var base := rad_to_deg(atan2(absf(heading.y), absf(heading.x)))
	var best := 0
	for i in angles.size():
		if absf(angles[i] - base) < absf(angles[best] - base):
			best = i
	return [best, heading.x < 0.0, heading.y < 0.0]


# An offset off a centred sheet's middle, kept on its pivot under the sheet's flips.
static func flipped_offset(offset: Vector2, flip_h: bool, flip_v: bool) -> Vector2:
	return Vector2(-offset.x if flip_h else offset.x, -offset.y if flip_v else offset.y)


static func juggle() -> Dictionary:
	return FINAL_JUGGLE
