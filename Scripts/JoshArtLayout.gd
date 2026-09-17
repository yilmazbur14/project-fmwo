extends RefCounted

# Every number that depends on how Josh, his cards and his effects are drawn, so a redraw only needs
# this file. Points and boxes are in texels on one of his frames, origin top-left.
# Each asset has its own USE_FINAL_* flag: placeholder and final art go through the same code, so the
# fight is playable before the sheets land and turning a flag off brings the placeholder back. Every
# flag starts false except the one sheet that is approved, josh_cards.png.

const SCALE := 3.0

#JOSH (horizontal strips of 80x80 frames, feet on row 79, x = 40 the symmetry axis)
const FRAME_SIZE := Vector2(80, 80)
const ANCHOR := Vector2(40, 79)
# The approved sheet: frame 0 is his signature pose, frame 1 holds a card up. Every placeholder pose
# below is one of those two.
const CARDS_SHEET := "res://Assets/Characters/Josh/josh_cards.png"

# What is drawn on any of his frames, for keeping his whole sprite on screen. Traced off the sheets:
# the widest run of drawn texels, so a stray sparkle can't inflate it. His duster reaches the frame
# edge on the riding frames and the blazing card reaches it on the throw's release frame.
const BODY_DRAWN := Rect2(0, 4, 80, 76)
# The riding frames alone reach this far above the anchor row in px, which is what decides how high a
# pass row can be before the top of the screen cuts his hat off: a row has to be at least
# glider_height + this.
const RIDE_HEADROOM := 219.0
# What the player can punch while he is down recovering: the mass of the hunched pose, traced off
# josh_recovery. It leans to his right, and the pose never mirrors, so the box leans with it.
const RECOVER_BODY_BOX := Rect2(18, 24, 55, 56)
# Where the finisher's daze stars circle, in px from the floor point he stands on: just over the hat
# of the hunched recovery pose, whose crown sits at texel (44, 15).
const DAZE_ANCHOR := Vector2(12, -207)
# Where a parry tell stands, in px above whatever height his feet are at: over the hat of the
# standing throw pose, whose crown sits at texel row 7.
const TELL_ANCHOR := Vector2(0, -228)

#ANIMATIONS
# name: sheet, frames in order, seconds on each (the last value repeats) and whether it loops.
# Optional: flips for poses drawn facing right that mirror while he moves left, and turn, the degrees
# the sprite is rotated (the defeat placeholder is his standing pose keeled over).
# The final sheets are 80x80 strips drawn facing right, so one flip rule covers the set. Ground poses
# put his soles on row 79, the anchor; the riding poses put them on row 75, which is what stands him
# on the card he rides without any code knowing about it.
const USE_FINAL_ANIMS := {
	&"idle": true,
	&"intro": true,
	&"glide": true,
	&"mount": true,
	&"dismount": true,
	&"lay": true,
	&"bomb": true,
	&"throw": true,
	&"show": true,
	&"show_hold": true,
	&"recover": true,
	&"hit": true,
	&"defeat": true,
}

const PLACEHOLDER_ANIMS := {
	&"idle": {sheet = CARDS_SHEET, frames = [0], times = [1.0], loop = true},
	&"intro": {sheet = CARDS_SHEET, frames = [0], times = [1.2], loop = false},
	&"glide": {sheet = CARDS_SHEET, frames = [0], times = [1.0], loop = true, flips = true},
	&"mount": {sheet = CARDS_SHEET, frames = [1, 0], times = [0.3, 0.3], loop = false},
	&"dismount": {sheet = CARDS_SHEET, frames = [0], times = [0.35], loop = false},
	&"lay": {sheet = CARDS_SHEET, frames = [1, 0], times = [0.14, 0.12], loop = false, flips = true},
	&"bomb": {sheet = CARDS_SHEET, frames = [1, 0], times = [0.1, 0.1], loop = false, flips = true},
	# Frame 1 is the whole wind-up, so the tell lasts exactly as long as the card is held back.
	&"throw": {sheet = CARDS_SHEET, frames = [1, 0], times = [0.45, 0.2], loop = false, flips = true},
	&"show": {sheet = CARDS_SHEET, frames = [1], times = [0.13], loop = false, flips = true},
	&"show_hold": {sheet = CARDS_SHEET, frames = [1], times = [1.0], loop = true, flips = true},
	&"recover": {sheet = CARDS_SHEET, frames = [0], times = [1.0], loop = true},
	&"hit": {sheet = CARDS_SHEET, frames = [0], times = [0.22], loop = false},
	&"defeat": {sheet = CARDS_SHEET, frames = [0], times = [1.0], loop = false, turn = 90.0},
}

const FINAL_ANIMS := {
	&"idle": {sheet = "res://Assets/Characters/Josh/josh_idle.png",
		frames = [0, 1, 2, 3], times = [0.15], loop = true},
	# His entrance, ending with the card he flicks buried in the floor.
	&"intro": {sheet = "res://Assets/Characters/Josh/josh_intro.png",
		frames = [0, 1, 2, 3, 4, 5], times = [0.11, 0.15, 0.11, 0.26, 0.16, 0.42], loop = false},
	&"glide": {sheet = "res://Assets/Characters/Josh/josh_glide.png",
		frames = [0, 1, 2, 3], times = [0.11], loop = true, flips = true},
	&"mount": {sheet = "res://Assets/Characters/Josh/josh_mount.png",
		frames = [0, 1, 2], times = [0.16, 0.13, 0.2], loop = false},
	&"dismount": {sheet = "res://Assets/Characters/Josh/josh_dismount.png",
		frames = [0, 1, 2], times = [0.12, 0.16, 0.24], loop = false},
	&"lay": {sheet = "res://Assets/Characters/Josh/josh_lay_card.png",
		frames = [0, 1, 2], times = [0.14, 0.22, 0.3], loop = false, flips = true},
	&"bomb": {sheet = "res://Assets/Characters/Josh/josh_drop_bomb.png",
		frames = [0, 1, 2], times = [0.09, 0.08, 0.13], loop = false, flips = true},
	# 0 is the wind-up, and it is held for the whole tell rather than the artist's 0.14 s, because the
	# tell length is what makes the three cards parryable (JoshCardsStateMachine.throw_tell). 1 is the
	# release, 2 the follow-through, 3 ready, held until the next card.
	&"throw": {sheet = "res://Assets/Characters/Josh/josh_throw.png",
		frames = [0, 1, 2, 3], times = [0.45, 0.07, 0.11, 0.13], loop = false, flips = true},
	# Played as show -> show_hold: frame 0 once, then the presenting loop.
	&"show": {sheet = "res://Assets/Characters/Josh/josh_show_card.png",
		frames = [0], times = [0.13], loop = false, flips = true},
	&"show_hold": {sheet = "res://Assets/Characters/Josh/josh_show_card.png",
		frames = [1, 2], times = [0.2], loop = true, flips = true},
	&"recover": {sheet = "res://Assets/Characters/Josh/josh_recovery.png",
		frames = [0, 1, 2, 3], times = [0.19], loop = true},
	&"hit": {sheet = "res://Assets/Characters/Josh/josh_hit.png",
		frames = [0, 1], times = [0.07, 0.12], loop = false},
	&"defeat": {sheet = "res://Assets/Characters/Josh/josh_defeat.png",
		frames = [0, 1, 2, 3, 4, 5], times = [0.13, 0.11, 0.11, 0.13, 0.18, 1.0], loop = false},
}

#WHERE CARDS LEAVE HIS HAND (texels on the frame that draws the hand-off)
# josh_throw frame 1, travelling right and slightly up.
const HAND_THROW := Vector2(72, 45)
# josh_drop_bomb frame 1, falling down-left.
const HAND_BOMB := Vector2(16, 70)

#HIS SHADOW
# Four frames of 80x24, and the frame index is his altitude rather than a step in an animation: 0 on
# the ground, 3 at riding height. The shadow itself never leaves the floor.
const USE_FINAL_SHADOW := true
const PLACEHOLDER_SHADOW := {
	"radii": Vector2(60, 16),
	"points": 20,
	"color": Color(0, 0, 0),
}
const FINAL_SHADOW := {
	"texture": "res://Assets/Characters/Josh/Cards/josh_shadow.png",
	"hframes": 4,
	"frame_size": Vector2(80, 24),
	"pivot": Vector2(40, 12),
	# From his feet anchor. The artist anchors it to his frame centre + (0, 108) px at 3x, and his
	# frame centre is 117 px above the anchor row.
	"offset": Vector2(0, -9),
	"scale": 3.0,
}
const SHADOW_ALPHA := 0.38
# The shadow shrinks and pales toward this as he climbs to his riding height.
const SHADOW_AIR_SCALE := 0.62
const SHADOW_AIR_ALPHA := 0.55

#THE CARD HE RIDES
# One continuous bank cycle, drawn behind him on its own node: it hangs 18 rows below his frame, so
# anything sized to his frame would cut it off.
const USE_FINAL_GLIDER := true
const GLIDER_TOP := -9.0
const PLACEHOLDER_GLIDER := {
	"size": Vector2(168, 54),
	"skew": 34.0,
	"color": Color(0.95, 0.78, 0.2),
	"edge_color": Color(0.42, 0.3, 0.04),
	"edge_width": 5.0,
}
const FINAL_GLIDER := {
	"texture": "res://Assets/Characters/Josh/Cards/josh_glider.png",
	"hframes": 3,
	"frame_size": Vector2(64, 28),
	"pivot": Vector2(32, 14),
	"frame_time": 0.11,
	"scale": 3.0,
	# From his feet anchor, and mirrored with him. The artist anchors the deck to his frame centre +
	# (-3, 132) px at 3x, which puts its top surface under the soles his riding frames stand on.
	"offset": Vector2(-3, 15),
}

#THE GIANT CARDS
# One card covers one third of the ropes. The art is drawn at a whole 3x and centred on the third; the
# hitbox is always the third's own rect, so the boundary that hurts is the boundary the thirds define.
const USE_FINAL_GIANT_CARD := true
const PLACEHOLDER_GIANT_CARD := {
	"back_color": Color(0.09, 0.13, 0.42),
	"border_color": Color(0.95, 0.75, 0.15),
	"border": 12.0,
	# SAFE, DRAIN, INVERT, in JoshGiantCardScript.Kind order.
	"face_colors": [Color(0.14, 0.48, 0.22), Color(0.12, 0.32, 0.6), Color(0.36, 0.14, 0.54)],
	"face_labels": ["SAFE", "STAMINA DRAIN", "INVERSE CONTROLS"],
	"label_font_size": 72,
	"label_color": Color(1, 1, 1),
	"label_outline": 8,
}
const FINAL_GIANT_CARD := {
	# 191x293 texels at 3x: 573x879 px, a third of the mat wide, in 3/4 perspective.
	"back": "res://Assets/Characters/Josh/Cards/card_giant.png",
	# Same size and origin as the card, so it is drawn at the identical position and lands exactly on
	# the card's floor footprint. Its interior is already a half-strength checker: no modulate needed.
	"shadow": "res://Assets/Characters/Josh/Cards/card_giant_shadow.png",
	"frame_size": Vector2(191, 293),
	"scale": 3.0,
	# Only the third that is about to fall shows its shadow, and it runs light: the art is a 50% black
	# checker, so at full strength the player disappears into it and the gold dashed border does the
	# work of marking the edge.
	"shadow_alpha": 0.32,
	"shadow_throb": [0.6, 1.0],
	# The phase-two cards: faces 0-2, the shared back 3, a shuffle blur 5-8 and the reveal burst 10-14,
	# on a 5x3 sheet where frame = row * 5 + column. The faces are drawn as a badge over the card the
	# player is standing on, at 6x. The skid-blur frames are unused: a third-sized card sliding is its
	# own motion read, and a blur badge on top of it read as an artefact.
	"specials": "res://Assets/Characters/Josh/Cards/card_specials.png",
	"specials_frame_size": Vector2(48, 64),
	"specials_hframes": 5,
	"specials_vframes": 3,
	"specials_scale": 6.0,
	"back_frame": 3,
	"reveal_frames": [10, 11, 12, 13, 14],
	"reveal_times": [0.05, 0.05, 0.06, 0.07, 0.09],
	# The burst frame the card's own face appears under, so the reveal is one overlay for every kind.
	"reveal_swap_frame": 12,
}

# The dust plume and floor cracks a card leaves where it slammed home.
const USE_FINAL_GIANT_IMPACT := true
const PLACEHOLDER_GIANT_IMPACT := {
	"color": Color(1, 0.97, 0.86),
	"height": 90.0,
	"time": 0.28,
}
const FINAL_GIANT_IMPACT := {
	"texture": "res://Assets/Characters/Josh/Cards/card_giant_impact.png",
	"hframes": 5,
	"frame_times": [0.05, 0.05, 0.06, 0.07, 0.09],
	"frame_size": Vector2(231, 80),
	"scale": 3.0,
	# From the card's own top-left at 3x: the plume's horizon row on the card's near edge.
	"offset": Vector2(-60, 642),
}

# The placeholder card's floor shadow, and how it reads while it hangs.
const GIANT_CARD_SHADOW_COLOR := Color(0, 0, 0)
const GIANT_CARD_SHADOW_ALPHA := 0.55
# How much smaller a placeholder card reads at its hovering height than lying on the floor.
const GIANT_CARD_HOVER_SCALE := 0.55
# The warning blink, in seconds a beat takes at the start of the fall and at the end of it.
const GIANT_CARD_PULSE_FIRST := 0.26
const GIANT_CARD_PULSE_LAST := 0.07
const GIANT_CARD_DIM_ALPHA := 0.22

#THE CARD BOMBS
const USE_FINAL_BOMB := true
const PLACEHOLDER_BOMB := {
	"size": Vector2(54, 78),
	"color": Color(0.95, 0.78, 0.2),
	"armed_color": Color(1.0, 0.45, 0.2),
	"edge_color": Color(0.42, 0.3, 0.04),
	"edge_width": 4.0,
}
const FINAL_BOMB := {
	"texture": "res://Assets/Characters/Josh/Cards/card_bomb.png",
	"hframes": 12,
	"frame_size": Vector2(32, 32),
	# The landed card's centre, which sits on the bomb's floor point and never moves again.
	"pivot": Vector2(16, 23),
	"scale": 3.0,
	"fall_frames": [0, 1, 2, 3],
	"fall_frame_time": 0.07,
	"land_frame": 4,
	"land_time": 0.09,
	"tick_frames": [5, 6, 7],
	"tick_frame_time": 0.15,
	"boom_frames": [8, 9, 10, 11],
	"boom_times": [0.05, 0.06, 0.07, 0.09],
	# The explosion is drawn twice the size of the card that carried it, so the fireball is a real
	# reason to move. The blast centre is this many texels above the card's centre, and it only hurts
	# while the fireball is drawn: the first two boom frames.
	"blast_scale": 6.0,
	"blast_rise_texels": 4.0,
	"blast_damage_frames": 2,
}
# The placeholder's arming blink, tightening the same way a giant card's warning does. The final sheet
# ramps its own red glow instead.
const BOMB_PULSE_FIRST := 0.24
const BOMB_PULSE_LAST := 0.06
const BOMB_DIM_ALPHA := 0.3
const BOMB_SHADOW_ALPHA := 0.45
# The placeholder's blast, when the fuse runs out; the final sheet draws its own.
const PLACEHOLDER_BOMB_BLAST := {
	"points": 5,
	"inner_ratio": 0.42,
	"color": Color(1.0, 0.85, 0.35),
	"from_scale": 0.35,
	"to_scale": 1.0,
}

#THE THROWN CARDS
const USE_FINAL_THROWN_CARD := true
const PLACEHOLDER_THROWN_CARD := {
	"size": Vector2(48, 66),
	"color": Color(1.0, 0.85, 0.3),
	"edge_color": Color(0.45, 0.32, 0.05),
	"edge_width": 4.0,
	# Turns per second in flight.
	"spin": 3.0,
}
const FINAL_THROWN_CARD := {
	"texture": "res://Assets/Characters/Josh/Cards/card_projectile.png",
	"hframes": 4,
	"frame_time": 0.055,
	"frame_size": Vector2(24, 24),
	# The card body's centre, which the parry hitbox sits on; the gold trail is drawn behind it.
	"pivot": Vector2(15, 12),
	"scale": 3.0,
}

# What a thrown card does when it is stopped: the crack is the parry's reward, so it is spawned on
# the frame the parry resolves, not the one after.
const USE_FINAL_CARD_SHATTER := true
const PLACEHOLDER_CARD_SHATTER := {
	"points": 6,
	"inner_ratio": 0.4,
	"radius": 54.0,
	"shatter_color": Color(1.0, 0.95, 0.7),
	"puff_color": Color(0.75, 0.6, 0.25),
	"from_scale": 0.4,
	"to_scale": 1.25,
	"time": 0.22,
}
const FINAL_CARD_SHATTER := {
	"texture": "res://Assets/Characters/Josh/Cards/card_shatter.png",
	"hframes": 5,
	"frame_times": [0.04, 0.05, 0.06, 0.07, 0.08],
	"frame_size": Vector2(48, 48),
	"scale": 3.0,
	# A card that landed rather than being stopped cracks the same way, duller.
	"hit_tint": Color(0.7, 0.62, 0.45),
}

#THE FAN OF CARDS
# Two cues off one shape: the entrance throws the deck out and up and he is standing there as it
# clears, and the defeat rains it down to settle flat along the ground line.
const USE_FINAL_CARD_BURST := true
const PLACEHOLDER_CARD_BURST := {
	"cards": 10,
	"size": Vector2(30, 42),
	"color": Color(1.0, 0.85, 0.3),
	"edge_color": Color(0.45, 0.32, 0.05),
	"edge_width": 3.0,
}
const FINAL_CARD_BURST := {
	"texture": "res://Assets/Characters/Josh/Cards/card_burst.png",
	"rain": "res://Assets/Characters/Josh/Cards/card_burst_rain.png",
	"hframes": 6,
	"frame_size": Vector2(64, 64),
	# On the ground line, so both cues are placed on his floor point.
	"pivot": Vector2(32, 48),
	"scale": 3.0,
	"frame_times": [0.09, 0.07, 0.07, 0.07, 0.08, 0.09],
	"rain_frame_times": [0.08, 0.08, 0.08, 0.09, 0.1, 0.12],
	# The frame he is standing there on, as the cards clear.
	"appear_frame": 5,
}

#THE PHASE-TWO BANNER
const BANNER_CENTRE := Vector2(960, 300)
const BANNER_TIME := 1.2
const BANNER_FONT_SIZE := 96
const BANNER_COLOR := Color(1.0, 0.92, 0.55)
const BANNER_OUTLINE := 10
const BANNER_FROM_SCALE := 0.7
const BANNER_TO_SCALE := 1.0
const BANNER_GROW_TIME := 0.18


static func anim(anim_name: StringName) -> Dictionary:
	if USE_FINAL_ANIMS.get(anim_name, false):
		return FINAL_ANIMS[anim_name]
	return PLACEHOLDER_ANIMS[anim_name]


# Seconds from the start of an animation to the start of its frame at `step`.
static func time_to_step(anim_name: StringName, step: int) -> float:
	var times: Array = anim(anim_name).times
	var total := 0.0
	for i in step:
		total += times[mini(i, times.size() - 1)]
	return total


# Sprite offset, in texels, that puts ANCHOR on the sprite's origin.
static func sheet_offset(frame_size: Vector2) -> Vector2:
	return frame_size / 2.0 - ANCHOR


# Screen-px offset from his feet of a point on his frames. Mirroring flips the texel column, so a
# hand-off point follows the pose it was measured on.
static func local(point: Vector2, flipped := false) -> Vector2:
	var column: float = (FRAME_SIZE.x - 1.0 - point.x) if flipped else point.x
	return (Vector2(column, point.y) - ANCHOR) * SCALE


static func local_rect(rect: Rect2) -> Rect2:
	return Rect2(local(rect.position), rect.size * SCALE)


# A filled ellipse, points on its rim, centred on the origin.
static func ellipse(radii: Vector2, points: int) -> PackedVector2Array:
	var rim := PackedVector2Array()
	for i in points:
		var angle := TAU * i / points
		rim.append(Vector2(cos(angle) * radii.x, sin(angle) * radii.y))
	return rim


# A star, for the placeholder bursts: `points` spikes out to `radius`, the dips at `inner_ratio` of it.
static func star(points: int, radius: float, inner_ratio: float) -> PackedVector2Array:
	var shape := PackedVector2Array()
	for i in points * 2:
		var angle := TAU * i / (points * 2) - PI / 2.0
		var reach := radius if i % 2 == 0 else radius * inner_ratio
		shape.append(Vector2(cos(angle), sin(angle)) * reach)
	return shape


# A rectangle around the origin, for the placeholder cards.
static func centred_rect(size: Vector2) -> PackedVector2Array:
	var half := size / 2.0
	return PackedVector2Array([
		Vector2(-half.x, -half.y), Vector2(half.x, -half.y),
		Vector2(half.x, half.y), Vector2(-half.x, half.y),
	])


# The card he rides, drawn in perspective under his feet with its top surface on GLIDER_TOP, where
# his riding frames put their soles.
static func glider_shape() -> PackedVector2Array:
	var size: Vector2 = PLACEHOLDER_GLIDER.size
	var skew: float = PLACEHOLDER_GLIDER.skew
	var half := size / 2.0
	return PackedVector2Array([
		Vector2(-half.x + skew, GLIDER_TOP), Vector2(half.x, GLIDER_TOP),
		Vector2(half.x - skew, GLIDER_TOP + size.y), Vector2(-half.x, GLIDER_TOP + size.y),
	])
