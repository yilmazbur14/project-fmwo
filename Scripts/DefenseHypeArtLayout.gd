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
# From the third parry in a row: a double shock ring with magenta rays and a white-hot core.
const FINAL_PARRY_FLASH_STRONG := {
	"texture": "res://Assets/Effects/parry_flash_strong.png",
	"hframes": 7,
	"frame_times": [0.03, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10],
	"scale": 2.0,
	"pivot": Vector2(48, 48),
	"push": 34.0,
}

# Bursts at a parried projectile, at the projectile's own scale. Neutral, so it reads over any of them.
const USE_FINAL_PARRY_SHATTER := true
const FINAL_PARRY_SHATTER := {
	"texture": "res://Assets/Effects/parry_shatter.png",
	"hframes": 4,
	"frame_times": [0.04, 0.05, 0.06, 0.07],
	"pivot": Vector2(16, 16),
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
# By parry streak tier: x1, x2, then x3 and up. The rim flash grows with the streak.
const PARRY_FLASH := [Color(2.4, 2.2, 1.4), Color(2.8, 2.5, 1.6), Color(3.4, 3.0, 1.9)]
const PARRY_FLASH_TIME := [0.25, 0.3, 0.35]
# The burst's scale by tier.
const PARRY_FLASH_SCALE := [1.0, 1.15, 1.35]
const PERFECT_DODGE_FLASH := Color(0.7, 2.2, 2.6)
const PERFECT_DODGE_FLASH_TIME := 0.25

#PARRY PUNCH
# A short zoom on the player and a jolt away from the attack, both by tier and both ignoring hit-stop
# so they play out during the parry's freeze. Tier 1 and 2 don't zoom.
const PARRY_ZOOM := [1.0, 1.0, 1.06]
const PARRY_ZOOM_TIME := 0.18
const PARRY_SHAKE := [4.0, 6.0, 9.0]
const PARRY_SHAKE_STEPS := 4
const PARRY_SHAKE_STEP_TIME := 0.025
# How far a parried projectile's art is knocked back, in px, before it carries on. Cosmetic: the
# hitbox never moves, so nothing is ever deflected.
const PARRY_KNOCKBACK := 6.0
const PARRY_KNOCKBACK_TIME := 0.14
const PARRY_ATTACK_FLASH := Color(3.0, 3.0, 3.0)

#CROWD
# Seconds the crowd cheers, by parry streak tier.
const PARRY_CHEER := [1.5, 2.0, 3.0]
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

#LOCKED SEQUENCE
# A fight holding the player for a parry-only sequence (Carter's clones). The blink that puts them in
# place leaves the dash's own ghosts along the way, and a held player is tinted a shade so being
# unable to move doesn't read as a bug. The tint is on the body, so the sprite's own block, parry and
# hurt flashes still show through it.
const WARP_GHOST_COUNT := 5
const LOCKED_TINT := Color(0.78, 0.82, 1.0)
const LOCKED_TINT_TIME := 0.15

#PARRY STREAK COUNTER
# A running count while a streak is alive, over the hype meter, fading out when it lapses.
const STREAK_COUNTER_POSITION := Vector2(1371, 985)
const STREAK_COUNTER_SIZE := Vector2(150, 66)
const STREAK_COUNTER_FADE_TIME := 0.25
const STREAK_COUNTER_POP := 8.0
const STREAK_COUNTER_POP_TIME := 0.12

const USE_FINAL_STREAK_COUNTER := true
const PLACEHOLDER_STREAK_COUNTER := {
	"text": "PARRY x%d",
	"font_size": 33,
	"outline": 6,
	"colors": [Color(1.0, 0.95, 0.6), Color(1.0, 0.72, 0.1)],
	"frame_time": 0.1,
}
# A badge whose row is the tier (x1 gold, x2 orange, x3+ magenta), looping, with white digits laid
# over it: one digit centred, two digits side by side.
const FINAL_STREAK_COUNTER := {
	"texture": "res://Assets/UI/streak_badge_3x.png",
	"hframes": 4,
	"vframes": 3,
	"frame_time": 0.09,
	"digits": "res://Assets/UI/streak_digits_3x.png",
	"digit_hframes": 10,
	"digit_offsets": [[Vector2(90, 12)], [Vector2(78, 12), Vector2(105, 12)]],
}

#STATUS ICONS
# The status effects a boss puts on the player (PlayerStatus): a row of icons with countdowns, right
# of the stamina bar and on its line, so a drained bar and its cause read together. The row is only
# there while something is active.
# High enough that the icon and its countdown bar clear the bottom of the screen.
const STATUS_ICONS_POSITION := Vector2(292, 990)
const STATUS_ICON_GAP := 12.0
# The hype meter's fade, so every HUD piece gets out of a balloon's way at the same speed.
const STATUS_FADE_TIME := HYPE_FADE_TIME
# The countdown bar under each icon.
const STATUS_BAR_HEIGHT := 9.0
const STATUS_BAR_GAP := 3.0
const STATUS_BAR_BACK := Color(0.08, 0.08, 0.08, 0.85)

const USE_FINAL_STATUS_ICONS := true
# A square per kind, alternating two shades for the pulse, at the final icon's size. `frame_times`
# is real seconds on the dim frame then the lit one.
const PLACEHOLDER_STATUS_ICONS := {
	"size": Vector2(72, 72),
	"frame_times": [0.18, 0.18],
	"colors": {
		&"stamina_drain": [Color(0.95, 0.72, 0.2), Color(0.7, 0.4, 0.1)],
		&"inverted_controls": [Color(0.78, 0.5, 1.0), Color(0.45, 0.25, 0.8)],
	},
	"bar_colors": {
		&"stamina_drain": Color(0.95, 0.72, 0.2),
		&"inverted_controls": Color(0.78, 0.5, 1.0),
	},
}
# Drawn with Josh's card set, which is why it lives in his folder: a 2x2 grid of 24x24 icons at 3x,
# a row per kind, frame 0 dim and frame 1 lit. The long dim frame against the short lit one gives the
# pulse its nervous beat.
const FINAL_STATUS_ICONS := {
	"texture": "res://Assets/Characters/Josh/Cards/status_icons.png",
	"hframes": 2,
	"vframes": 2,
	"scale": 3.0,
	"size": Vector2(72, 72),
	"frame_times": [0.40, 0.22],
	"rows": {
		&"stamina_drain": 0,
		&"inverted_controls": 1,
	},
	"bar_colors": {
		&"stamina_drain": Color(0.95, 0.72, 0.2),
		&"inverted_controls": Color(0.78, 0.5, 1.0),
	},
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
	# The streak words; the exact number is on the badge.
	&"parry_x2": {"text": "PARRY x2", "font_size": 55, "outline": 10, "colors": [Color(1.0, 0.95, 0.6), Color(1.0, 0.55, 0.1)], "frame_time": 0.08},
	&"parry_x3": {"text": "PARRY x3+", "font_size": 55, "outline": 10, "colors": [Color(1.0, 0.95, 0.6), Color(1.0, 0.35, 0.6)], "frame_time": 0.07},
	# The status effects (PlayerStatus), as they land.
	&"drained": {"text": "DRAINED!", "font_size": 44, "outline": 8, "colors": [Color(1.0, 0.72, 0.1), Color(0.8, 0.35, 0.1)], "frame_time": 0.1},
	&"reversed": {"text": "REVERSED!", "font_size": 44, "outline": 8, "colors": [Color(0.85, 0.6, 1.0), Color(0.5, 0.3, 0.9)], "frame_time": 0.1},
}
# Frame 0 rests and frame 1 pops; the word fills the top 48 px of each frame.
const FINAL_POPUPS := {
	&"parry": {"texture": "res://Assets/UI/popup_parry_3x.png", "hframes": 2, "frame_time": 0.08},
	&"perfect": {"texture": "res://Assets/UI/popup_perfect_3x.png", "hframes": 2, "frame_time": 0.08},
	&"guard_break": {"texture": "res://Assets/UI/popup_guard_break_3x.png", "hframes": 2, "frame_time": 0.1},
	&"hype": {"texture": "res://Assets/UI/popup_hype_3x.png", "hframes": 2, "frame_time": 0.08},
	&"parry_x2": {"texture": "res://Assets/UI/popup_parry_x2_3x.png", "hframes": 2, "frame_time": 0.08},
	# The x3+ word covers every longer streak.
	&"parry_x3": {"texture": "res://Assets/UI/popup_parry_x3_3x.png", "hframes": 2, "frame_time": 0.07},
}

#SOUNDS
# Placeholders from the existing sounds until final ones arrive.
const BLOCK_SFX := {"stream": "res://Assets/Audio/SFX/hit_impact.ogg", "pitch": 1.6, "volume_db": -8.0}
# A bright tink per streak tier, plus a sting when a streak reaches tier 3. Placeholders from the
# existing sounds until the audio coder's parry_tink_1..3 and streak sting land; the flag swaps them.
const USE_FINAL_PARRY_SFX := true
const PLACEHOLDER_PARRY_SFX := [
	{"stream": "res://Assets/Audio/SFX/hit_impact.ogg", "pitch": 2.2},
	{"stream": "res://Assets/Audio/SFX/hit_impact.ogg", "pitch": 2.5},
	{"stream": "res://Assets/Audio/SFX/hit_impact.ogg", "pitch": 2.8},
]
# A major triad climbing with the tier. Their peaks match by design, so `volume_db` is the knob if a
# later tier should also feel heavier.
const FINAL_PARRY_SFX = [
	{"stream": "res://Assets/Audio/SFX/parry_tink_1.wav", "pitch": 1.0, "volume_db": 0.0},
	{"stream": "res://Assets/Audio/SFX/parry_tink_2.wav", "pitch": 1.0, "volume_db": 0.0},
	{"stream": "res://Assets/Audio/SFX/parry_tink_3.wav", "pitch": 1.0, "volume_db": 0.0},
]
# Tails overlap when parries come quickly, so the tinks round-robin through a few players.
const PARRY_SFX_VOICES := 3
# The sting lands just after the third tink, so the hit itself reads first.
const PARRY_STREAK_STING_DELAY := 0.04
const PLACEHOLDER_PARRY_STREAK_STING := {"stream": "res://Assets/Audio/SFX/downed_stinger.ogg", "pitch": 1.5}
const FINAL_PARRY_STREAK_STING := {"stream": "res://Assets/Audio/SFX/parry_streak.wav", "pitch": 1.0}
const GUARD_BREAK_SFX := {"stream": "res://Assets/Audio/SFX/wrestler_collision.ogg", "pitch": 0.8}
const PERFECT_DODGE_SFX := {"stream": "res://Assets/Audio/SFX/whirlwind_whoosh.ogg", "pitch": 1.5}
const HYPE_FULL_SFX := {"stream": "res://Assets/Audio/SFX/downed_stinger.ogg", "pitch": 1.3}


static func stamina() -> Dictionary:
	return FINAL_STAMINA if USE_FINAL_STAMINA else PLACEHOLDER_STAMINA


static func hype() -> Dictionary:
	return FINAL_HYPE if USE_FINAL_HYPE else PLACEHOLDER_HYPE


static func block_spark() -> Dictionary:
	return FINAL_BLOCK_SPARK if USE_FINAL_BLOCK_SPARK else PLACEHOLDER_BLOCK_SPARK


# The strong sheet from the third parry in a row.
static func parry_flash(tier := 0) -> Dictionary:
	if not USE_FINAL_PARRY_FLASH:
		return PLACEHOLDER_PARRY_FLASH
	return FINAL_PARRY_FLASH_STRONG if tier >= 2 else FINAL_PARRY_FLASH


static func parry_shatter() -> Dictionary:
	return FINAL_PARRY_SHATTER if USE_FINAL_PARRY_SHATTER else {}


static func parry_tell() -> Dictionary:
	return FINAL_PARRY_TELL if USE_FINAL_PARRY_TELL else PLACEHOLDER_PARRY_TELL


static func perfect_dodge_trail() -> Dictionary:
	return FINAL_PERFECT_DODGE_TRAIL if USE_FINAL_PERFECT_DODGE_TRAIL else PLACEHOLDER_PERFECT_DODGE_TRAIL


static func guard_break_stars() -> Dictionary:
	return FINAL_GUARD_BREAK_STARS if USE_FINAL_GUARD_BREAK_STARS else PLACEHOLDER_GUARD_BREAK_STARS


static func guard_break_pose() -> Dictionary:
	return FINAL_GUARD_BREAK_POSE if USE_FINAL_GUARD_BREAK_POSE else PLACEHOLDER_GUARD_BREAK_POSE


# Falls back to the placeholder for a word the final set doesn't have yet, such as the streak popup
# the artist is still drawing.
static func status_icons() -> Dictionary:
	return FINAL_STATUS_ICONS if USE_FINAL_STATUS_ICONS else PLACEHOLDER_STATUS_ICONS


static func popup(kind: StringName) -> Dictionary:
	if USE_FINAL_POPUPS and FINAL_POPUPS.has(kind):
		return FINAL_POPUPS[kind]
	return PLACEHOLDER_POPUPS[kind]


static func parry_sfx(tier: int) -> Dictionary:
	var sounds: Array = FINAL_PARRY_SFX if USE_FINAL_PARRY_SFX else PLACEHOLDER_PARRY_SFX
	return sounds[clampi(tier, 0, sounds.size() - 1)]


static func parry_streak_sting() -> Dictionary:
	return FINAL_PARRY_STREAK_STING if USE_FINAL_PARRY_SFX else PLACEHOLDER_PARRY_STREAK_STING


static func streak_counter() -> Dictionary:
	return FINAL_STREAK_COUNTER if USE_FINAL_STREAK_COUNTER else PLACEHOLDER_STREAK_COUNTER
