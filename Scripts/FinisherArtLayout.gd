extends RefCounted

# Every number that depends on how the finisher is drawn. Each asset has its own USE_FINAL_* flag;
# placeholder and final art go through the same code, so turning a flag off brings the placeholder
# back.

#PLAYER SHEET
# Offsets are texels added to the sprite's own offset. Points are px from the player's body origin on
# a frame facing right; flip_h mirrors the frames for the left, so a point is mirrored by negating x.
const USE_FINAL_PLAYER := true
const PLACEHOLDER_PLAYER := {
	"texture": "res://Assets/Characters/MainPlayer/player_4dir_sheet.png",
	"hframes": 10,
	"vframes": 4,
	"offset": Vector2.ZERO,
	# [frame, texel offset]. The ready pose is held while dazed and through a fizzle.
	"ready": [39, Vector2(0, 1)],
	"charge": [[39, Vector2(0, 1)], [39, Vector2(0, 0)]],
	# Seconds per charge frame with the meter empty and full.
	"charge_frame_time": [0.10, 0.05],
	# [frame, texel offset, seconds]: launch, three rise steps, apex, fall, land. These frames can't
	# draw the rise, so the offsets do.
	"uppercut": [
		[39, Vector2(0, 1), 0.08],
		[17, Vector2(0, -6), 0.06],
		[18, Vector2(0, -14), 0.06],
		[18, Vector2(0, -20), 0.06],
		[18, Vector2(0, -22), 0.12],
		[30, Vector2(0, -10), 0.08],
		[39, Vector2(0, 0), 0.10],
	],
	# The step whose start is the moment of contact.
	"contact_step": 1,
	# The steps whose gloves count for the reach check.
	"reach_steps": [1],
	# The glove per step: the up punch's hitbox centre (PlayerScript.PUNCH_HITBOXES) moved by the step's offset.
	"fists": {1: Vector2(-12, -60.5)},
}
const FINAL_PLAYER := {
	"texture": "res://Assets/Characters/MainPlayer/player_uppercut.png",
	"hframes": 10,
	"vframes": 1,
	# The 48x64 frames' bottom 32x32 lines up with the 4-direction sheet's frames.
	"offset": Vector2(0, -16),
	"ready": [0, Vector2.ZERO],
	"charge": [[0, Vector2.ZERO], [1, Vector2.ZERO], [2, Vector2.ZERO]],
	"charge_frame_time": [0.08, 0.05],
	# The rise is drawn into the frames.
	"uppercut": [
		[3, Vector2.ZERO, 0.05],
		[4, Vector2.ZERO, 0.06],
		[5, Vector2.ZERO, 0.06],
		[6, Vector2.ZERO, 0.06],
		[7, Vector2.ZERO, 0.14],
		[8, Vector2.ZERO, 0.10],
		[9, Vector2.ZERO, 0.16],
	],
	# Frame 5: the artist's pick, it reads better than frame 4.
	"contact_step": 2,
	"reach_steps": [1, 2, 3],
	"fists": {1: Vector2(18, -81), 2: Vector2(10.5, -102), 3: Vector2(7.5, -120), 4: Vector2(7.5, -126)},
}
# While finishing the player draws over the boss, whom some fights put later in the tree, and over
# the finisher's effects.
const FINISHING_Z_INDEX := 3
# The mash prompt goes under the feet, or over the head, in px from the body origin.
const PLAYER_FEET := Vector2(0, 36)
const PLAYER_HEAD := Vector2(0, -48)

#DAZE STARS
# `pivot` is the texel put on the boss's daze anchor; `scale` is screen px per texel.
const USE_FINAL_STARS := true
const PLACEHOLDER_STARS := {
	"texture": "res://Assets/UI/Screens/defeat_stars.png",
	"hframes": 4,
	"frame_time": 0.125,
	"scale": 3.0,
	"pivot": Vector2(28, 26),
}
const FINAL_STARS := {
	"texture": "res://Assets/Effects/daze_stars.png",
	"hframes": 6,
	"frame_time": 0.10,
	"scale": 3.0,
	"pivot": Vector2(24, 13),
}

#IMPACT
# The burst is pushed from the contact glove onto the boss by this many px (facing right), then kept
# on the boss's hurtbox. It draws under the player, who is small next to it.
const IMPACT_OFFSET := Vector2(60, -60)
const USE_FINAL_IMPACT := true
# A burst polygon built in code, in px.
const PLACEHOLDER_IMPACT := {
	"points": 8,
	"outer_radius": 60.0,
	"inner_radius": 21.0,
	"color": Color(1.0, 0.95, 0.6),
	"from_scale": 0.5,
	"to_scale": 1.5,
	"time": 0.25,
}
const FINAL_IMPACT := {
	"texture": "res://Assets/Effects/uppercut_impact.png",
	"hframes": 6,
	# Played once.
	"frame_times": [0.04, 0.06, 0.06, 0.07, 0.08, 0.09],
	# The player's own scale, which is now the artist's 3x. It was held at 2x while he was half this
	# size, where 3x hid smaller bosses and the rising player behind it.
	"scale": 3.0,
	"pivot": Vector2(48, 48),
}

#SUPERCHARGED IMPACT
# The burst when a full hype meter supercharges the uppercut (PlayerHype).
const USE_FINAL_SUPER_IMPACT := true
# The normal burst, whichever it is, tinted gold.
const PLACEHOLDER_SUPER_IMPACT := {"tint": Color(1.6, 1.25, 0.45)}
# Drawn bigger than the normal burst, and still under the player, who draws at FINISHING_Z_INDEX.
const FINAL_SUPER_IMPACT := {
	"texture": "res://Assets/Effects/uppercut_impact_super.png",
	"hframes": 7,
	# The same step past the normal burst it always was (x1.375), off the player's new scale.
	"frame_times": [0.04, 0.06, 0.06, 0.07, 0.08, 0.09, 0.10],
	"scale": 4.125,
	"pivot": Vector2(48, 48),
}

#SUPERCHARGED CONTACT EXTRAS
# A shock ring and radial speed lines thrown out by a supercharged contact. Both are built in code
# until the artist's sheets land; the flags then swap them the way every other asset works.
# The ring is drawn in world space on the ground under the impact, beneath the boss and the player;
# the lines are drawn in screen space, over the arena and under the HUD.
const USE_FINAL_SUPER_SHOCK_RING := true
# An expanding circle, in px.
const PLACEHOLDER_SUPER_SHOCK_RING := {
	"points": 40,
	"radius": 36.0,
	"to_radius": 340.0,
	"width": 9.0,
	"color": Color(1.0, 0.86, 0.4, 0.9),
	"time": 0.32,
}
const FINAL_SUPER_SHOCK_RING := {
	"texture": "res://Assets/Effects/super_impact_ring.png",
	"hframes": 6,
	"frame_times": [0.04, 0.05, 0.06, 0.07, 0.08, 0.09],
	"scale": 3.0,
	"pivot": Vector2(96, 48),
}

const USE_FINAL_SUPER_SPEEDLINES := true
# Wedges radiating from the contact, in px.
const PLACEHOLDER_SUPER_SPEEDLINES := {
	"rays": 20,
	"inner_radius": 120.0,
	"length": 1100.0,
	"width": 30.0,
	"color": Color(1.0, 0.95, 0.75, 0.45),
	"time": 0.3,
}
const FINAL_SUPER_SPEEDLINES := {
	"texture": "res://Assets/Effects/super_impact_rays.png",
	"hframes": 5,
	"frame_times": [0.03, 0.04, 0.05, 0.06, 0.07],
	# 3x fills the screen from the middle; further out than off_centre px the corners need 4x.
	"scale": 3.0,
	"off_centre": 150.0,
	"off_centre_scale": 4.0,
	"pivot": Vector2(320, 180),
}

#SUPERCHARGED IMPACT SOUND
# The one sound the supercharged uppercut has that the normal one doesn't: the user's own power
# punch, kept out of the repo, so a fresh clone falls back to the hit every punch in the game makes,
# pitched down into something heavier. The normal uppercut is left alone either way, which is the
# point: spending a full meter should be the loudest thing the player can do.
const SUPER_IMPACT_LOCAL := "res://Assets/Audio/SFX/local/super_uppercut_local.mp3"
const SUPER_IMPACT_FALLBACK := "res://Assets/Audio/SFX/hit_impact.ogg"
# Loud on purpose, and the loudest cue the player has: the parry sits at -6 and a block at -8. It
# lands inside the contact's hit-stop, where the fight is silent apart from the music and the crowd,
# so it has room to be the biggest hit in the game without fighting anything for it.
const SUPER_IMPACT_LOCAL_DB := 0.0
const SUPER_IMPACT_FALLBACK_DB := 0.0
const SUPER_IMPACT_FALLBACK_PITCH := 0.7


static func super_impact_sfx() -> Dictionary:
	if ResourceLoader.exists(SUPER_IMPACT_LOCAL):
		return {"stream": SUPER_IMPACT_LOCAL, "pitch": 1.0, "volume_db": SUPER_IMPACT_LOCAL_DB}
	return {"stream": SUPER_IMPACT_FALLBACK, "pitch": SUPER_IMPACT_FALLBACK_PITCH, "volume_db": SUPER_IMPACT_FALLBACK_DB}


#SUPERCHARGED PLAYER SHEET
# The same frames as the finisher sheet with the energy recoloured, swapped in for the whole
# supercharged finisher so the charge reads as loaded.
const USE_FINAL_SUPER_PLAYER := true
const FINAL_SUPER_PLAYER_TEXTURE := "res://Assets/Characters/MainPlayer/player_uppercut_super.png"

#PROMPT
# One row on the HUD layer, in screen px: [punch key] [meter] [dodge key], with the text centred
# under the meter.
const PROMPT_KEY_GAP := 18.0

# [frame, modulate, px the key drops] for a key that's idle, lit (the next one to press) and pressed.
const USE_FINAL_KEYS := true
const PLACEHOLDER_KEYS := {
	"punch": "res://Assets/UI/key_q.png",
	"dodge": "res://Assets/UI/key_w.png",
	"mash_left": "res://Assets/UI/key_left.png",
	"mash_right": "res://Assets/UI/key_right.png",
	"hframes": 1,
	"scale": 3.0,
	"idle": [0, Color(0.6, 0.6, 0.6), 0],
	"lit": [0, Color(1.35, 1.35, 1.35), 0],
	"pressed": [0, Color(2.0, 2.0, 2.0), 3],
}
const FINAL_KEYS := {
	"punch": "res://Assets/UI/qte_key_q_3x.png",
	"dodge": "res://Assets/UI/qte_key_w_3x.png",
	# A feel_v2 fight's mash keys (PlayerFinisher.mash_actions), made the same way from the arrows.
	"mash_left": "res://Assets/UI/qte_key_left_3x.png",
	"mash_right": "res://Assets/UI/qte_key_right_3x.png",
	"hframes": 2,
	"scale": 1.0,
	# Frame 1 is drawn gold and 2 px down. A pressed key sinks without turning gold, so only the next
	# key to press is ever gold.
	"idle": [0, Color.WHITE, 0],
	"lit": [1, Color.WHITE, 0],
	"pressed": [0, Color.WHITE, 2],
}

# The same keys on a gamepad, for whatever punch and dodge are bound to (InputSettings). Unlike the
# two dicts above, the first element of idle/lit/pressed is a ROW OFFSET added to the button's column
# on the sheet (InputSettings.pad_frame_for), not an absolute frame.
const USE_FINAL_PAD_KEYS := true
# A key built in code with the button's name on it (ControlsArtLayout.keycap), `size` px; lit is
# tinted gold, standing in for the final sheet's gold row.
const PLACEHOLDER_PAD_KEYS := {
	"size": Vector2(96, 96),
	"idle": [0, Color(0.6, 0.6, 0.6), 0],
	"lit": [0, Color(1.6, 1.35, 0.55), 0],
	"pressed": [0, Color(2.0, 2.0, 2.0), 3],
}
# 14 columns by 2 rows of 96x96. Row 1 is drawn gold and 2 px down, as the keyboard's frame 1 is, so
# lit is a whole row further on; a pressed key sinks without turning gold.
const FINAL_PAD_KEYS := {
	"texture": "res://Assets/UI/Pad/pad_buttons_3x.png",
	"hframes": 14,
	"vframes": 2,
	"scale": 1.0,
	"idle": [0, Color.WHITE, 0],
	"lit": [14, Color.WHITE, 0],
	"pressed": [0, Color.WHITE, 2],
}

# MASH! while charging, FULL! once the meter fills; each alternates two looks.
const USE_FINAL_PROMPT_TEXT := true
const PLACEHOLDER_PROMPT_TEXT := {
	"mash": "MASH!",
	"full": "FULL!",
	"size": Vector2(192, 60),
	"colors": [Color(1.0, 0.72, 0.1), Color(1.0, 0.95, 0.6)],
	"mash_frame_time": 0.15,
	"full_frame_time": 0.08,
}
const FINAL_PROMPT_TEXT := {
	"mash": "res://Assets/UI/qte_mash_text_3x.png",
	"full": "res://Assets/UI/qte_full_text_3x.png",
	"hframes": 2,
	"size": Vector2(192, 60),
	"mash_frame_time": 0.15,
	"full_frame_time": 0.08,
}

const USE_FINAL_METER := true
# A bar styled like the boss health bars, inside the meter's slot.
const PLACEHOLDER_METER := {
	"size": Vector2(216, 48),
	"bar_rect": Rect2(12, 12, 192, 24),
	"fill_color": Color(1.0, 0.72, 0.1),
	"full_colors": [Color(1.0, 1.0, 1.0), Color(1.0, 0.85, 0.2)],
	"full_frame_time": 0.08,
}
# The fill is a fixed gradient revealed left to right, not stretched. The full overlay covers the
# whole meter.
const FINAL_METER := {
	"size": Vector2(216, 48),
	"frame": "res://Assets/UI/qte_meter_frame_3x.png",
	"fill": "res://Assets/UI/qte_meter_fill_3x.png",
	"fill_offset": Vector2(21, 15),
	"full": "res://Assets/UI/qte_meter_full_3x.png",
	"full_hframes": 2,
	"full_frame_time": 0.08,
}


#TIERED MASH (PlayerFinisher against a boss that can be juggled)
# The same slot as the single meter, three bars across it, in px from the meter's top-left.
const USE_FINAL_TIER_METER := true
# A dark slot per bar, filled in code.
const PLACEHOLDER_TIER_METER := {
	"size": Vector2(216, 48),
	"bars": [Rect2(21, 15, 48, 18), Rect2(84, 15, 48, 18), Rect2(147, 15, 48, 18)],
	"slot_color": Color(0.08, 0.08, 0.08, 0.85),
	"fill_color": Color(1.0, 0.72, 0.1),
	"banked_colors": [Color(1.0, 0.85, 0.3), Color(1.0, 0.6, 0.15), Color(1.0, 0.4, 0.1)],
	"full_colors": [Color(1.0, 1.0, 1.0), Color(1.0, 0.85, 0.2)],
	"full_frame_time": 0.08,
}
const FINAL_TIER_METER := {
	"size": Vector2(216, 48),
	"frame": "res://Assets/UI/qte_meter3_frame_3x.png",
	"fill": "res://Assets/UI/qte_meter3_fill_3x.png",
	"fill_offset": Vector2(21, 15),
	# In the fill, bar k (from 0) starts bar_stride * k px in and is bar_length px long, with nothing
	# between the bars, so one bar reveals all three.
	"bar_stride": 63.0,
	"bar_length": 48.0,
	# Over each banked bar its own row's glint, looping: frame (bar - 1) * 4 + step.
	"banked": "res://Assets/UI/qte_meter3_banked_3x.png",
	"banked_hframes": 4,
	"banked_vframes": 3,
	"banked_frame_times": [0.06, 0.06, 0.06, 0.24],
	# As a bar banks its row's burst plays once, bigger each tier.
	"flash": "res://Assets/UI/qte_meter3_flash_3x.png",
	"flash_hframes": 4,
	"flash_vframes": 3,
	"flash_offset": Vector2(-36, -36),
	"flash_frame_times": [0.04, 0.05, 0.06, 0.07],
	# FULL, once bar 3 banks.
	"full": "res://Assets/UI/qte_meter3_full_3x.png",
	"full_hframes": 2,
	"full_frame_time": 0.08,
}

# 1!, 2!! and 3!!! in MASH!'s place under the meter, from its top-left; the newest stays up until the
# next bar banks.
const USE_FINAL_TIER_STAMPS := true
const PLACEHOLDER_TIER_STAMPS := {
	"texts": ["1!", "2!!", "3!!!"],
	"size": Vector2(120, 66),
	"colors": [Color(1.0, 0.85, 0.2), Color(1.0, 1.0, 1.0)],
	"offset": Vector2(48, 48),
	"frame_time": 0.09,
}
const FINAL_TIER_STAMPS := {
	"textures": ["res://Assets/UI/qte_tier_1_3x.png", "res://Assets/UI/qte_tier_2_3x.png", "res://Assets/UI/qte_tier_3_3x.png"],
	"hframes": 2,
	"offset": Vector2(48, 48),
	"frame_time": 0.09,
}

# KNIGHT BREAKER!, centred on the HUD above the fight from bar 3 banking until just after the third
# uppercut lands, then faded. Real seconds.
const USE_FINAL_KNIGHT_BREAKER := true
const PLACEHOLDER_KNIGHT_BREAKER := {
	"text": "KNIGHT BREAKER!",
	"size": Vector2(480, 60),
	"font_size": 44,
	"outline": 8,
	"colors": [Color(1.0, 0.85, 0.2), Color(1.0, 1.0, 1.0)],
	"position": Vector2(720, 150),
	"frame_time": 0.08,
	"hold_after_hit": 0.15,
	"fade_time": 0.2,
}
const FINAL_KNIGHT_BREAKER := {
	"texture": "res://Assets/UI/knight_breaker_3x.png",
	"hframes": 2,
	"position": Vector2(720, 150),
	"frame_time": 0.08,
	"hold_after_hit": 0.15,
	"fade_time": 0.2,
}

# The third uppercut's afterimage: a gold copy of each rise frame left behind as the next one shows,
# fading. Drawn in the finisher's effects layer, so behind the player and over the boss.
const KNIGHT_BREAKER_GHOST := {
	"steps": [1, 2, 3],
	"tint": Color(2.0, 1.6, 0.6, 0.6),
	"fade_time": 0.25,
}

# The juggle's hit sound, each uppercut the boss's own hit pitched a step higher.
const JUGGLE_HIT_PITCHES := [1.12, 1.26, 1.4]

#TIERED MASH SOUND
# Every level is baked into its file, so each plays at 0 dB.
# From the prompt until the mash resolves, pitched up with the charge: 1 + CHARGE_LOOP_PITCH_PER_BAR x
# m_s. The file carries its own loop points: setting a loop mode on the stream brings back a click.
const CHARGE_LOOP_SFX := "res://Assets/Audio/SFX/finisher_charge_loop.wav"
const CHARGE_LOOP_PITCH_PER_BAR := 0.2
# As each bar banks, each tuned to the loop's pitch at that moment.
const BAR_SFX := [
	"res://Assets/Audio/SFX/finisher_bar_1.wav",
	"res://Assets/Audio/SFX/finisher_bar_2.wav",
	"res://Assets/Audio/SFX/finisher_bar_3.wav",
]
# On the third uppercut's contact, over the rest of it.
const KNIGHT_BREAKER_SFX := "res://Assets/Audio/SFX/knight_breaker_sting.wav"


static func player_sheet() -> Dictionary:
	return FINAL_PLAYER if USE_FINAL_PLAYER else PLACEHOLDER_PLAYER


static func tier_meter() -> Dictionary:
	return FINAL_TIER_METER if USE_FINAL_TIER_METER else PLACEHOLDER_TIER_METER


static func tier_stamps() -> Dictionary:
	return FINAL_TIER_STAMPS if USE_FINAL_TIER_STAMPS else PLACEHOLDER_TIER_STAMPS


static func knight_breaker() -> Dictionary:
	return FINAL_KNIGHT_BREAKER if USE_FINAL_KNIGHT_BREAKER else PLACEHOLDER_KNIGHT_BREAKER


static func stars() -> Dictionary:
	return FINAL_STARS if USE_FINAL_STARS else PLACEHOLDER_STARS


static func impact() -> Dictionary:
	return FINAL_IMPACT if USE_FINAL_IMPACT else PLACEHOLDER_IMPACT


static func super_shock_ring() -> Dictionary:
	return FINAL_SUPER_SHOCK_RING if USE_FINAL_SUPER_SHOCK_RING else PLACEHOLDER_SUPER_SHOCK_RING


static func super_speedlines() -> Dictionary:
	return FINAL_SUPER_SPEEDLINES if USE_FINAL_SUPER_SPEEDLINES else PLACEHOLDER_SUPER_SPEEDLINES


static func super_impact() -> Dictionary:
	return FINAL_SUPER_IMPACT if USE_FINAL_SUPER_IMPACT else impact().merged(PLACEHOLDER_SUPER_IMPACT, true)


# The recoloured sheet only exists for the final frames.
static func player_texture(supercharged: bool) -> String:
	if supercharged and USE_FINAL_PLAYER and USE_FINAL_SUPER_PLAYER:
		return FINAL_SUPER_PLAYER_TEXTURE
	return player_sheet().texture


static func keys(gamepad := false) -> Dictionary:
	if gamepad:
		return FINAL_PAD_KEYS if USE_FINAL_PAD_KEYS else PLACEHOLDER_PAD_KEYS
	return FINAL_KEYS if USE_FINAL_KEYS else PLACEHOLDER_KEYS


static func prompt_text() -> Dictionary:
	return FINAL_PROMPT_TEXT if USE_FINAL_PROMPT_TEXT else PLACEHOLDER_PROMPT_TEXT


static func meter() -> Dictionary:
	return FINAL_METER if USE_FINAL_METER else PLACEHOLDER_METER


# Seconds from the uppercut's start to each step's start, with the landing as the last entry.
static func uppercut_step_starts() -> Array:
	var starts := [0.0]
	for step in player_sheet().uppercut:
		starts.append(starts[-1] + step[2])
	return starts


static func mirrored(point: Vector2, flipped: bool) -> Vector2:
	return Vector2(-point.x, point.y) if flipped else point
