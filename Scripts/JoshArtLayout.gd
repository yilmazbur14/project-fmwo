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

# What is drawn on any of his frames, for keeping his whole sprite on screen, traced off the sheets.
# His coat tails reach the left edge on the riding frames and a sparkle off the throw's
# follow-through reaches the right one. Only his hat reaches row 1, knocked off on hit frame 0 and
# flying on defeat frame 1.
const BODY_DRAWN := Rect2(0, 1, 80, 79)
# The riding frames alone reach this far above the anchor row in px (their hats top out on row 8),
# which is what decides how high a pass row can be before the top of the screen cuts his hat off: a
# row has to be at least glider_height + this.
const RIDE_HEADROOM := 213.0
# What the player can punch while he is down recovering: the mass of the hunched pose, head to soles
# and elbow to elbow, traced off josh_recovery. His hat is left out, as the old pose's loose card was:
# it would add ten rows over his head, up to row 13. Drawn facing right, so it mirrors with him.
const RECOVER_BODY_BOX := Rect2(19, 23, 47, 57)
# Where the finisher's daze stars circle, in px from the floor point he stands on, facing right: five
# rows over the hat of the hunched recovery pose, whose crown sits at texel (48, 14) and breathes
# between rows 13 and 15. Facing left it mirrors.
const DAZE_ANCHOR := Vector2(24, -210)
# Where a parry tell stands, in px above whatever height his feet are at, facing right: four rows over
# the hat of the standing throw pose, whose crown sits at texel row 5, centred on column 40. Facing
# left it mirrors.
const TELL_ANCHOR := Vector2(0, -234)

#ANIMATIONS
# name: sheet, frames in order, seconds on each (the last value repeats) and whether it loops.
# Optional: flips for poses drawn facing right that mirror while he faces left, which in the air is
# the way he is riding and on the ground is toward the player; and turn, the degrees the sprite is
# rotated (the defeat placeholder is his standing pose keeled over).
# The final sheets are 80x80 strips drawn facing right, so one flip rule covers the set. Ground poses
# put his soles on row 79, the anchor; the riding poses put them on row 75, which is what stands him
# on the card he rides without any code knowing about it. lay, bomb, show and show_hold are riding
# poses, and mount and dismount step between the two.
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
		frames = [0, 1, 2, 3], times = [0.15], loop = true, flips = true},
	# His entrance, ending with the card he flicks buried in the floor.
	&"intro": {sheet = "res://Assets/Characters/Josh/josh_intro.png",
		frames = [0, 1, 2, 3, 4, 5], times = [0.11, 0.15, 0.11, 0.26, 0.16, 0.42], loop = false,
		flips = true},
	&"glide": {sheet = "res://Assets/Characters/Josh/josh_glide.png",
		frames = [0, 1, 2, 3], times = [0.11], loop = true, flips = true},
	&"mount": {sheet = "res://Assets/Characters/Josh/josh_mount.png",
		frames = [0, 1, 2], times = [0.16, 0.13, 0.2], loop = false, flips = true},
	&"dismount": {sheet = "res://Assets/Characters/Josh/josh_dismount.png",
		frames = [0, 1, 2], times = [0.12, 0.16, 0.24], loop = false, flips = true},
	&"lay": {sheet = "res://Assets/Characters/Josh/josh_lay_card.png",
		frames = [0, 1, 2], times = [0.14, 0.22, 0.3], loop = false, flips = true},
	&"bomb": {sheet = "res://Assets/Characters/Josh/josh_drop_bomb.png",
		frames = [0, 1, 2], times = [0.09, 0.08, 0.13], loop = false, flips = true},
	# 0 is the wind-up, and it is held for the whole tell rather than the artist's 0.14 s, because the
	# tell length is what makes his cards parryable (JoshCardsStateMachine.throw_tell). 1 is the
	# release, 2 the follow-through, 3 ready, held until the next card.
	&"throw": {sheet = "res://Assets/Characters/Josh/josh_throw.png",
		frames = [0, 1, 2, 3], times = [0.45, 0.07, 0.11, 0.13], loop = false, flips = true},
	# Played as show -> show_hold: frame 0 once, then the presenting loop.
	&"show": {sheet = "res://Assets/Characters/Josh/josh_show_card.png",
		frames = [0], times = [0.13], loop = false, flips = true},
	&"show_hold": {sheet = "res://Assets/Characters/Josh/josh_show_card.png",
		frames = [1, 2], times = [0.2], loop = true, flips = true},
	&"recover": {sheet = "res://Assets/Characters/Josh/josh_recovery.png",
		frames = [0, 1, 2, 3], times = [0.19], loop = true, flips = true},
	&"hit": {sheet = "res://Assets/Characters/Josh/josh_hit.png",
		frames = [0, 1], times = [0.07, 0.12], loop = false, flips = true},
	&"defeat": {sheet = "res://Assets/Characters/Josh/josh_defeat.png",
		frames = [0, 1, 2, 3, 4, 5], times = [0.13, 0.11, 0.11, 0.13, 0.18, 1.0], loop = false,
		flips = true},
}
# The step of `intro` that flicks the card into the floor, which the flick at the camera starts on.
const INTRO_FLICK_STEP := 5

#WHERE CARDS LEAVE HIS HAND (texels on the frame that draws the hand-off)
# josh_throw frame 1, travelling right and slightly up.
const HAND_THROW := Vector2(72, 45)
# josh_drop_bomb frame 1, falling down-left: the card's centre.
const HAND_BOMB := Vector2(15, 65)
# The step of `bomb` that draws that hand-off. The bomb only leaves his hand there: the wind-up before
# it still holds the card up.
const BOMB_RELEASE_STEP := 1

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

#THE JUGGLE (the Break's tiered uppercut; BossJuggled reads exactly this shape)
# A sheet of its own: 160x120 frames against his 80x80, hung so its row 119 stands on the same ground
# line as ANCHOR, so its texels go through BossJuggled.texel_point(), never local(). top_row is the
# highest row drawn on an air frame (1-6). There is no leap shadow of his own: his flight shadow above
# already draws his height as its frame index, and it is drawn here as he draws it, opaque and 3 texels
# over his feet (FINAL_SHADOW.offset), so nothing under him changes when his own comes back at the crash.
const USE_FINAL_JUGGLE := true
const FINAL_JUGGLE := {
	"texture": "res://Assets/Characters/Josh/josh_juggle.png",
	"hframes": 12,
	"frame_size": Vector2(160, 120),
	"offset": Vector2(0, -59),
	"feet": Vector2(80, 119),
	"tumble_centre": Vector2(80, 62),
	"top_row": 27,
	"clips": {
		&"launch": {"frames": [0, 1], "times": [0.06, 0.08], "loop": false},
		&"tumble": {"frames": [2, 3, 4, 5, 6], "times": [0.2, 0.07, 0.06, 0.06, 0.07], "loop": true},
		&"crash": {"frames": [7, 8, 9], "times": [0.06, 0.08, 0.12], "loop": false},
		&"down": {"frames": [10, 11], "times": [0.4, 0.4], "loop": true},
	},
	"shadow": {
		"texture": "res://Assets/Characters/Josh/Cards/josh_shadow.png",
		"hframes": 4, "scale": 3.0, "alpha": 1.0, "step": 80.0, "offset": Vector2(0, -3),
	},
	"lying_time": 0.3,
	"outro_delay": 1.8,
	"crash_sfx": {"stream": "res://Assets/Audio/SFX/hit_impact.ogg", "pitch": 0.7, "volume_db": 0.0},
}
# What is drawn on any of the twelve juggle frames, traced off josh_juggle.png: 231 px left of his feet
# to 228 right, twice his width, which is what the last uppercut's shove keeps inside the ropes.
const JUGGLE_DRAWN := Rect2(3, 6, 153, 114)

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
	# All three laid thirds show their shadow, so the arena reads as "three of these are coming", but
	# queued runs faint enough to see the floor and the player through. The one that commits is
	# unmistakable: several times darker, throbbing between these two, and tinted so its gold border
	# burns red. The art is a 50% black checker, so alpha is the whole lever.
	"shadow_queued_alpha": 0.16,
	"shadow_commit_alpha": [0.45, 0.85],
	"shadow_commit_tint": Color(1.0, 0.48, 0.4),
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

# The placeholder card's floor shadow. It is solid black rather than a checker, so the same reading
# needs lower numbers than the final art.
const GIANT_CARD_SHADOW_COLOR := Color(0, 0, 0)
const GIANT_CARD_QUEUED_ALPHA := 0.1
const GIANT_CARD_COMMIT_ALPHA := [0.28, 0.55]
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
	"blast_scale": 9.0,
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


static func juggle() -> Dictionary:
	return FINAL_JUGGLE


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


# The same for a box of texels. Mirrored, its left edge is the mirror of its right-hand column.
static func local_rect(rect: Rect2, flipped := false) -> Rect2:
	var corner := Vector2(rect.end.x - 1.0 if flipped else rect.position.x, rect.position.y)
	return Rect2(local(corner, flipped), rect.size * SCALE)


# A px offset from his feet, measured with him facing right, for the way he is facing. The sprite
# mirrors about his anchor, so the offset mirrors about x = 0.
static func mirrored(offset: Vector2, flipped: bool) -> Vector2:
	return Vector2(-offset.x, offset.y) if flipped else offset


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
