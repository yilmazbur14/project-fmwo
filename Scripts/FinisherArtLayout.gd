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
	"fists": {1: Vector2(-8, -40.33)},
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
	"fists": {1: Vector2(12, -54), 2: Vector2(7, -68), 3: Vector2(5, -80), 4: Vector2(5, -84)},
}
# While finishing the player draws over the boss, whom some fights put later in the tree, and over
# the finisher's effects.
const FINISHING_Z_INDEX := 3
# The mash prompt goes under the feet, or over the head, in px from the body origin.
const PLAYER_FEET := Vector2(0, 24)
const PLAYER_HEAD := Vector2(0, -32)

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
const IMPACT_OFFSET := Vector2(40, -40)
const USE_FINAL_IMPACT := true
# A burst polygon built in code, in px.
const PLACEHOLDER_IMPACT := {
	"points": 8,
	"outer_radius": 40.0,
	"inner_radius": 14.0,
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
	"scale": 3.0,
	"pivot": Vector2(48, 48),
}

#PROMPT
# One row on the HUD layer, in screen px: [punch key] [meter] [dodge key], with the text centred
# under the meter.
const PROMPT_KEY_GAP := 18.0

# [frame, modulate, px the key drops] for a key that's idle, lit (the next one to press) and pressed.
const USE_FINAL_KEYS := true
const PLACEHOLDER_KEYS := {
	"punch": "res://Assets/UI/key_q.png",
	"dodge": "res://Assets/UI/key_w.png",
	"hframes": 1,
	"scale": 3.0,
	"idle": [0, Color(0.6, 0.6, 0.6), 0],
	"lit": [0, Color(1.35, 1.35, 1.35), 0],
	"pressed": [0, Color(2.0, 2.0, 2.0), 3],
}
const FINAL_KEYS := {
	"punch": "res://Assets/UI/qte_key_q_3x.png",
	"dodge": "res://Assets/UI/qte_key_w_3x.png",
	"hframes": 2,
	"scale": 1.0,
	# Frame 1 is drawn gold and 2 px down. A pressed key sinks without turning gold, so only the next
	# key to press is ever gold.
	"idle": [0, Color.WHITE, 0],
	"lit": [1, Color.WHITE, 0],
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


static func player_sheet() -> Dictionary:
	return FINAL_PLAYER if USE_FINAL_PLAYER else PLACEHOLDER_PLAYER


static func stars() -> Dictionary:
	return FINAL_STARS if USE_FINAL_STARS else PLACEHOLDER_STARS


static func impact() -> Dictionary:
	return FINAL_IMPACT if USE_FINAL_IMPACT else PLACEHOLDER_IMPACT


static func keys() -> Dictionary:
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
