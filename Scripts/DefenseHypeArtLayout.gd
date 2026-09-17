extends RefCounted

# Every number that depends on how the defence and hype HUD and effects are drawn. Each asset has its
# own USE_FINAL_* flag; placeholder and final art go through the same code, so turning a flag off
# brings the placeholder back. HUD art uses the _3x copies at scale 1 on whole screen px; world
# effects are drawn at the player's 2x.

#STAMINA BAR
# The frame's top-left on the 1920x1080 HUD: under the hearts, left of the dialogue box.
const STAMINA_BAR_POSITION := Vector2(10, 1026)
# Real seconds a spend takes to drain off the bar.
const STAMINA_DROP_TIME := 0.1
# A refused dash.
const STAMINA_REFUSED_FLASH := Color(2.2, 0.45, 0.45)
const STAMINA_REFUSED_FLASH_TIME := 0.3
# While holding block keeps the bar from refilling.
const STAMINA_PAUSED_DIM := Color(0.55, 0.55, 0.55)

const USE_FINAL_STAMINA := true
# A bar styled like the boss health bars, in px from the bar's top-left.
const PLACEHOLDER_STAMINA := {
	"bar_rect": Rect2(6, 9, 252, 27),
	"fill_color": Color(0.3, 0.85, 0.35),
	# Below the dash cost.
	"low_color": Color(1.0, 0.55, 0.1),
	# Alternates while the guard is broken.
	"broken_colors": [Color(0.95, 0.15, 0.15), Color(0.45, 0.05, 0.05)],
	"broken_frame_time": 0.1,
}
# The fill is revealed left to right in whole texels, never stretched. Below the dash cost the low
# strip's frames, each the fill's size, take turns as the fill. The broken overlay covers frame and
# fill.
const FINAL_STAMINA := {
	"frame": "res://Assets/UI/stamina_bar_frame_3x.png",
	"fill": "res://Assets/UI/stamina_bar_fill_3x.png",
	"fill_offset": Vector2(21, 15),
	"fill_texels": 74,
	"low": "res://Assets/UI/stamina_bar_low_3x.png",
	"low_frames": 2,
	"low_frame_time": 0.12,
	"broken": "res://Assets/UI/stamina_bar_broken_3x.png",
	"broken_hframes": 2,
	"broken_frame_time": 0.1,
}

#HYPE METER
# The frame's top-left on the 1920x1080 HUD: bottom right, in the dialogue box's corner, so the meter
# hides while a balloon is up and fades while the finisher prompt would sit on it.
const HYPE_METER_POSITION := Vector2(1539, 946)
# Real seconds.
const HYPE_POP_TEXELS := 6.0
const HYPE_POP_TIME := 0.12
const HYPE_FADE_TIME := 0.2

const USE_FINAL_HYPE := true
# A bar and a label styled like the rest of the placeholder HUD, in px from the meter's top-left.
const PLACEHOLDER_HYPE := {
	"size": Vector2(369, 126),
	"label_rect": Rect2(78, 18, 156, 60),
	"text": "HYPE",
	"font_size": 33,
	"outline": 6,
	"label_colors": [Color(1.0, 0.72, 0.1), Color(1.0, 0.95, 0.6)],
	"bar_rect": Rect2(84, 78, 264, 15),
	"fill_color": Color(1.0, 0.55, 0.1),
	"full_colors": [Color(1.0, 0.95, 0.5), Color(1.0, 0.72, 0.1)],
	"full_frame_time": 0.08,
}
# The fill is revealed left to right in whole texels. The full glow covers frame and fill, and the
# label is drawn last, on its second frame while full.
const FINAL_HYPE := {
	"size": Vector2(369, 126),
	"frame": "res://Assets/UI/hype_meter_frame_3x.png",
	"fill": "res://Assets/UI/hype_meter_fill_3x.png",
	"fill_offset": Vector2(84, 78),
	"fill_texels": 88,
	"full": "res://Assets/UI/hype_meter_full_3x.png",
	"full_hframes": 4,
	"full_frame_time": 0.08,
	"label": "res://Assets/UI/hype_label_3x.png",
	"label_hframes": 2,
	"label_offset": Vector2(78, 18),
}

#CONTACT EFFECTS
# Played once where the guard meets an attack: the hurtbox centre pushed this many px toward the
# attack's origin, or straight up for a sky attack.
const CONTACT_PUSH := 14.0

# Final bursts are sheets played once; `pivot` is the texel put on the contact point and `scale` is
# screen px per texel. Placeholders are stars built in code, in px.
const USE_FINAL_BLOCK_SPARK := true
const PLACEHOLDER_BLOCK_SPARK := {
	"points": 4,
	"outer_radius": 16.0,
	"inner_radius": 5.0,
	"color": Color(0.65, 0.88, 1.0),
	"from_scale": 0.6,
	"to_scale": 1.2,
	"time": 0.15,
}
const FINAL_BLOCK_SPARK := {
	"texture": "res://Assets/Effects/block_spark.png",
	"hframes": 4,
	"frame_times": [0.04, 0.05, 0.06, 0.07],
	"scale": 2.0,
	"pivot": Vector2(16, 16),
}

# `push` moves the burst this many px further from the player than the contact point.
const USE_FINAL_PARRY_FLASH := true
const PLACEHOLDER_PARRY_FLASH := {
	"points": 4,
	"outer_radius": 30.0,
	"inner_radius": 7.0,
	"color": Color(1.0, 0.95, 0.65),
	"from_scale": 0.5,
	"to_scale": 1.4,
	"time": 0.25,
	"push": 0.0,
}
# At its peak the flash would cover the small player's head, and the effects draw above him.
const FINAL_PARRY_FLASH := {
	"texture": "res://Assets/Effects/parry_flash.png",
	"hframes": 5,
	"frame_times": [0.03, 0.05, 0.06, 0.07, 0.08],
	"scale": 2.0,
	"pivot": Vector2(32, 32),
	"push": 34.0,
}

#PARRY TELL
# The warning over an attacking boss's head. Attacks pass their own head point (Eric's states do);
# bosses without one fall back to their daze anchor, shifted by this.
const PARRY_TELL_OFFSET := Vector2(0, -20)
# Above the boss and his effects.
const PARRY_TELL_Z_INDEX := 3
# It shows at once, on its biggest frame, so it never eats reaction time; only its exit fades.
const PARRY_TELL_FADE_OUT := 0.09

const USE_FINAL_PARRY_TELL := true
# A chevron built in code, pointing down at him, pulsing between the two scales.
const PLACEHOLDER_PARRY_TELL := {
	"size": Vector2(44, 16),
	"thickness": 0.45,
	"color": Color(1.0, 0.25, 0.2),
	# Attacks whose parry also staggers.
	"strong_color": Color(1.0, 0.45, 0.1),
	"pulse": [0.85, 1.15],
	"pulse_time": 0.5,
}
# A red diamond badge with a white "!", looping; the strong one is bigger, in a broken ring. Each
# pivot is the badge's bottom tip, so the anchor sits a few texels over the boss's head and the badge
# grows upward from it. Drawn at 3x, like the daze stars.
const FINAL_PARRY_TELL := {
	"scale": 3.0,
	"standard": {
		"texture": "res://Assets/Effects/parry_tell.png",
		"hframes": 6,
		"frame_times": [0.09, 0.09, 0.11, 0.11, 0.09, 0.09],
		"pivot": Vector2(16, 24),
	},
	"strong": {
		"texture": "res://Assets/Effects/parry_tell_strong.png",
		"hframes": 6,
		"frame_times": [0.07, 0.07, 0.08, 0.08, 0.07, 0.07],
		"pivot": Vector2(24, 36),
	},
}

# The aura for a parryable projectile in flight, drawn behind it and centred on it, through
# ParryTell.glow(). Wired but unused: only Eric's whirlwind and grab tell at all for now. The art is
# sized for a projectile 12-16 texels across, so bigger ones want a larger whole-number scale.
const PARRY_GLOW := {
	"texture": "res://Assets/Effects/parry_glow.png",
	"hframes": 4,
	"frame_time": 0.09,
	"pivot": Vector2(16, 16),
	"scale": 2.0,
}

#PLAYER FLASHES
# On the player's sprite self_modulate, fading back to white.
const BLOCK_FLASH := Color(1.5, 1.8, 2.2)
const BLOCK_FLASH_TIME := 0.12
const PARRY_FLASH := Color(2.4, 2.2, 1.4)
const PARRY_FLASH_TIME := 0.25
const PERFECT_DODGE_FLASH := Color(0.7, 2.2, 2.6)
const PERFECT_DODGE_FLASH_TIME := 0.25

#CROWD
# Seconds the crowd cheers.
const PARRY_CHEER := 1.5
const PERFECT_DODGE_CHEER := 1.0

#GUARD BREAK
# Loop until the guard recovers, drawn above the player; `offset` is px from the player's body origin
# to the pivot.
const USE_FINAL_GUARD_BREAK_STARS := true
const PLACEHOLDER_GUARD_BREAK_STARS := {
	"texture": "res://Assets/Effects/daze_stars.png",
	"hframes": 6,
	"frame_time": 0.1,
	"scale": 2.0,
	"pivot": Vector2(24, 13),
	"offset": Vector2(0, -40),
}
const FINAL_GUARD_BREAK_STARS := {
	"texture": "res://Assets/Effects/guard_break_stars.png",
	"hframes": 6,
	"frame_time": 0.1,
	"scale": 2.0,
	"pivot": Vector2(16, 9),
	"offset": Vector2(0, -26),
}

# The stunned player: `frames` are columns stepped every frame_time on the facing's row, odd steps move
# the frame by `wobble` texels, and the sprite's self_modulate alternates through `flicker`.
const USE_FINAL_GUARD_BREAK_POSE := true
const PLACEHOLDER_GUARD_BREAK_POSE := {
	"frames": [9],
	"frame_time": 0.08,
	"wobble": Vector2(1, 0),
	"flicker": [Color(2.0, 0.55, 0.55), Color(1, 1, 1)],
	"flicker_time": 0.08,
}
# Rows in the 4-direction sheet's order, centred like it.
const FINAL_GUARD_BREAK_POSE := {
	"texture": "res://Assets/Characters/MainPlayer/player_guard_break.png",
	"hframes": 3,
	"vframes": 4,
	"frames": [0, 1, 2, 1],
	"frame_time": 0.15,
	"wobble": Vector2.ZERO,
	"flicker": [],
	"flicker_time": 0.08,
}

#DASH RECOVERY
# There's no drawn recovery pose yet: the player holds the 4-direction sheet's crouched walk frame in
# his facing row, leaned a texel back along the dash. A drawn sheet can replace this the way
# FINAL_GUARD_BREAK_POSE does.
const DASH_RECOVERY_POSE := {
	"frame": 4,
	"lean_texels": 1.0,
}

#PERFECT DODGE
# Ghosts of the player left along the dash path, evenly spaced from where the dash started to where
# he is now, drawn at his 2x and centred on the body origin like his sprite.
const PERFECT_DODGE_GHOST_COUNT := 3
const USE_FINAL_PERFECT_DODGE_TRAIL := true
# Copies of the player's own frame, tinted and fading.
const PLACEHOLDER_PERFECT_DODGE_TRAIL := {
	"tint": Color(0.45, 1.0, 1.2, 0.75),
	"fade_time": 0.25,
}
# Columns are the frames, rows the facing in the 4-direction sheet's order.
const FINAL_PERFECT_DODGE_TRAIL := {
	"texture": "res://Assets/Effects/perfect_dodge_trail.png",
	"hframes": 4,
	"vframes": 4,
	"frame_times": [0.05, 0.06, 0.07, 0.08],
	"scale": 2.0,
}

#POPUPS
# Words over the player's head on the HUD layer, in screen px and real seconds. Each rises, holds and
# fades; one that shows while another is still up stacks above it. Anywhere they'd go above
# POPUP_TOP_LIMIT they show under the feet instead, sinking rather than rising.
const POPUP_GAP := 12.0
const POPUP_RISE := 30.0
const POPUP_RISE_TIME := 0.35
const POPUP_HOLD_TIME := 0.25
const POPUP_FADE_TIME := 0.2
# The boss health bars are above this line.
const POPUP_TOP_LIMIT := 100.0
const POPUP_SCREEN_MARGIN := 8.0

const USE_FINAL_POPUPS := true
# Pixelify Sans is only crisp at multiples of its 11 px design size. Each word alternates two colours.
const PLACEHOLDER_POPUPS := {
	&"parry": {"text": "PARRY!", "font_size": 55, "outline": 10, "colors": [Color(1, 1, 1), Color(1.0, 0.85, 0.25)], "frame_time": 0.08},
	&"perfect": {"text": "PERFECT!", "font_size": 55, "outline": 10, "colors": [Color(0.55, 1.0, 1.0), Color(1, 1, 1)], "frame_time": 0.08},
	&"guard_break": {"text": "GUARD BREAK!", "font_size": 33, "outline": 6, "colors": [Color(1.0, 0.3, 0.25), Color(1.0, 0.65, 0.2)], "frame_time": 0.1},
	&"hype": {"text": "HYPE!", "font_size": 55, "outline": 10, "colors": [Color(1.0, 0.72, 0.1), Color(1.0, 0.95, 0.6)], "frame_time": 0.08},
}
# Frame 0 rests and frame 1 pops; the word fills the top 48 px of each frame.
const FINAL_POPUPS := {
	&"parry": {"texture": "res://Assets/UI/popup_parry_3x.png", "hframes": 2, "frame_time": 0.08},
	&"perfect": {"texture": "res://Assets/UI/popup_perfect_3x.png", "hframes": 2, "frame_time": 0.08},
	&"guard_break": {"texture": "res://Assets/UI/popup_guard_break_3x.png", "hframes": 2, "frame_time": 0.1},
	&"hype": {"texture": "res://Assets/UI/popup_hype_3x.png", "hframes": 2, "frame_time": 0.08},
}

#SOUNDS
# Placeholders from the existing sounds until final ones arrive.
const BLOCK_SFX := {"stream": "res://Assets/Audio/SFX/hit_impact.ogg", "pitch": 1.6, "volume_db": -8.0}
const PARRY_SFX := {"stream": "res://Assets/Audio/SFX/hit_impact.ogg", "pitch": 2.2}
const GUARD_BREAK_SFX := {"stream": "res://Assets/Audio/SFX/wrestler_collision.ogg", "pitch": 0.8}
const PERFECT_DODGE_SFX := {"stream": "res://Assets/Audio/SFX/whirlwind_whoosh.ogg", "pitch": 1.5}
const HYPE_FULL_SFX := {"stream": "res://Assets/Audio/SFX/downed_stinger.ogg", "pitch": 1.3}


static func stamina() -> Dictionary:
	return FINAL_STAMINA if USE_FINAL_STAMINA else PLACEHOLDER_STAMINA


static func hype() -> Dictionary:
	return FINAL_HYPE if USE_FINAL_HYPE else PLACEHOLDER_HYPE


static func block_spark() -> Dictionary:
	return FINAL_BLOCK_SPARK if USE_FINAL_BLOCK_SPARK else PLACEHOLDER_BLOCK_SPARK


static func parry_flash() -> Dictionary:
	return FINAL_PARRY_FLASH if USE_FINAL_PARRY_FLASH else PLACEHOLDER_PARRY_FLASH


static func parry_tell() -> Dictionary:
	return FINAL_PARRY_TELL if USE_FINAL_PARRY_TELL else PLACEHOLDER_PARRY_TELL


static func perfect_dodge_trail() -> Dictionary:
	return FINAL_PERFECT_DODGE_TRAIL if USE_FINAL_PERFECT_DODGE_TRAIL else PLACEHOLDER_PERFECT_DODGE_TRAIL


static func guard_break_stars() -> Dictionary:
	return FINAL_GUARD_BREAK_STARS if USE_FINAL_GUARD_BREAK_STARS else PLACEHOLDER_GUARD_BREAK_STARS


static func guard_break_pose() -> Dictionary:
	return FINAL_GUARD_BREAK_POSE if USE_FINAL_GUARD_BREAK_POSE else PLACEHOLDER_GUARD_BREAK_POSE


static func popup(kind: StringName) -> Dictionary:
	return FINAL_POPUPS[kind] if USE_FINAL_POPUPS else PLACEHOLDER_POPUPS[kind]
