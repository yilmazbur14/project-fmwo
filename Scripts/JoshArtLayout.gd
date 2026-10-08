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
# His throw, whose frames stand in for his summon's and his command's until their own sheets are in.
const THROW_SHEET := "res://Assets/Characters/Josh/josh_throw.png"

# What is drawn on any of his frames, for keeping his whole sprite on screen, traced off the sheets.
# His coat tails reach the left edge on the riding frames and a sparkle off the throw's
# follow-through reaches the right one. Only his hat reaches row 1, knocked off on hit frame 0 and
# flying on defeat frame 1.
const BODY_DRAWN := Rect2(0, 1, 80, 79)
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
# on the card he rides without any code knowing about it. glide is the riding pose, and mount and
# dismount step between the two. Nothing in his fight plays those three since the Wild Cards rework;
# they are kept, with their sheets, for Jordan's finale, whose cameo glides him in on josh_glide and
# josh_dismount (JordanFinaleLayout.CAMEOS).
# A final anim plays only once its sheet is in and imported (anim()): his summon's and his command's are drawn in
# the hands' art pass, and until they ship the placeholders stand in.
const USE_FINAL_ANIMS := {
	&"idle": true,
	&"intro": true,
	&"glide": true,
	&"mount": true,
	&"dismount": true,
	&"throw": true,
	&"recover": true,
	&"hit": true,
	&"defeat": true,
	&"wild_hold": true,
	&"summon": true,
	&"summon_hold": true,
	&"command": true,
	&"command_hold": true,
	&"dive": true,
	&"emerge": true,
}

const PLACEHOLDER_ANIMS := {
	&"idle": {sheet = CARDS_SHEET, frames = [0], times = [1.0], loop = true},
	&"intro": {sheet = CARDS_SHEET, frames = [0], times = [1.2], loop = false},
	&"glide": {sheet = CARDS_SHEET, frames = [0], times = [1.0], loop = true, flips = true},
	&"mount": {sheet = CARDS_SHEET, frames = [1, 0], times = [0.3, 0.3], loop = false},
	&"dismount": {sheet = CARDS_SHEET, frames = [0], times = [0.35], loop = false},
	# Frame 1 is the whole wind-up.
	&"throw": {sheet = CARDS_SHEET, frames = [1, 0], times = [0.45, 0.2], loop = false, flips = true},
	&"recover": {sheet = CARDS_SHEET, frames = [0], times = [1.0], loop = true},
	&"hit": {sheet = CARDS_SHEET, frames = [0], times = [0.22], loop = false},
	&"defeat": {sheet = CARDS_SHEET, frames = [0], times = [1.0], loop = false, turn = 90.0},
	&"wild_hold": {sheet = CARDS_SHEET, frames = [1], times = [1.0], loop = true, flips = true},
	# His summon (JoshCardsSummon): a card held up, then his throw's release and follow-through flicking cards.
	&"summon": {sheet = CARDS_SHEET, frames = [1], times = [0.3], loop = false, flips = true},
	&"summon_hold": {sheet = THROW_SHEET, frames = [1, 2], times = [0.10], loop = true, flips = true},
	# His command to the hands (JoshCardsHandSlam): his throw's wind-up, then its follow-through held as the point.
	&"command": {sheet = THROW_SHEET, frames = [0, 2], times = [0.20, 0.15], loop = false, flips = true},
	&"command_hold": {sheet = THROW_SHEET, frames = [2], times = [1.0], loop = true, flips = true},
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
	# 0 is the wind-up, which wild_hold holds while he and his clones wait; 1 is the release, 2 the
	# follow-through (WILD_RELEASE_STEPS), 3 ready.
	&"throw": {sheet = "res://Assets/Characters/Josh/josh_throw.png",
		frames = [0, 1, 2, 3], times = [0.45, 0.07, 0.11, 0.13], loop = false, flips = true},
	&"recover": {sheet = "res://Assets/Characters/Josh/josh_recovery.png",
		frames = [0, 1, 2, 3], times = [0.19], loop = true, flips = true},
	&"hit": {sheet = "res://Assets/Characters/Josh/josh_hit.png",
		frames = [0, 1], times = [0.07, 0.12], loop = false, flips = true},
	&"defeat": {sheet = "res://Assets/Characters/Josh/josh_defeat.png",
		frames = [0, 1, 2, 3, 4, 5], times = [0.13, 0.11, 0.11, 0.13, 0.18, 1.0], loop = false,
		flips = true},
	# Wild Cards: the throw's wind-up, held while he and each clone he leaves wait to throw.
	&"wild_hold": {sheet = "res://Assets/Characters/Josh/josh_throw.png",
		frames = [0], times = [1.0], loop = true, flips = true},
	# His summon: 0 gathers, 1 sweeps up, 2-3 arms up flicking cards (JoshHandsLayout.SUMMON_CARD_ORIGIN), looped.
	&"summon": {sheet = "res://Assets/Characters/Josh/josh_summon.png",
		frames = [0, 1], times = [0.15, 0.15], loop = false, flips = true},
	&"summon_hold": {sheet = "res://Assets/Characters/Josh/josh_summon.png",
		frames = [2, 3], times = [0.10], loop = true, flips = true},
	# His command: 0 draws back, 1 points, 2-3 hold the point, looped.
	&"command": {sheet = "res://Assets/Characters/Josh/josh_command.png",
		frames = [0, 1], times = [0.20, 0.15], loop = false, flips = true},
	&"command_hold": {sheet = "res://Assets/Characters/Josh/josh_command.png",
		frames = [2, 3], times = [0.16], loop = true, flips = true},
	# His Portal Monte (JoshCardsPortalMonte): the dive up into a big gate - crouch, leap, two diving frames and the
	# vanish in a twist of cards, DIVE_TIME in all - and the emerge back out of it: cards pouring out, dropping out feet
	# first, the thud, and josh_recovery's first frame, handing off to his Recover. Until the dive is in, his summon's
	# sweep up stands in for it (anim()), and until the emerge is (or with it off), the dive backwards.
	&"dive": {sheet = "res://Assets/Characters/Josh/josh_dive.png",
		frames = [0, 1, 2, 3, 4], times = [0.12, 0.10, 0.10, 0.10, 0.08], loop = false, flips = true},
	&"emerge": {sheet = "res://Assets/Characters/Josh/josh_emerge.png",
		frames = [0, 1, 2, 3], times = [0.08, 0.12, 0.14, 0.16], loop = false, flips = true},
}
const DIVE_TIME := 0.5
# The step of `intro` that flicks the card into the floor, which the flick at the camera starts on.
const INTRO_FLICK_STEP := 5

#WHERE CARDS LEAVE HIS HAND (texels on the frame that draws the hand-off)
# josh_throw frame 1, travelling right and slightly up.
const HAND_THROW := Vector2(72, 45)

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
# anything sized to his frame would cut it off. His fight no longer shows it, since the Wild Cards rework;
# it is kept, with josh_glider.png, for Jordan's finale, whose cameo glides him in on his card, and the
# glide sheet does not draw the card.
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
	# The card body's centre, which the square that hurts sits on; the gold trail is drawn behind it.
	"pivot": Vector2(15, 12),
	"scale": 3.0,
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

#WILD CARDS (JoshCardsWildCards)
# The clones he leaves are his own sheets - the throw's wind-up held while they wait (wild_hold), then its
# release and follow-through as they throw - drawn as cool, see-through ghosts of him, so none of them
# reads as him. They stand on a faint copy of his shadow.
const WILD_CLONE_TINT := Color(0.55, 0.72, 1.0, 0.78)
const WILD_CLONE_SHADOW_ALPHA := 0.25
# The steps of `throw` a clone draws letting go, from the frame the cards leave; it holds the last until
# it scatters (JoshCardsStateMachine.wild_clone_linger).
const WILD_RELEASE_STEPS: Array[int] = [1, 2]
# Their cards leave from the throw's release hand-off, HAND_THROW, mirrored with the clone.
# The lanes on the floor are the dodge tell's gold (DefenseHypeArtLayout's yellow ring): faint from the
# moment a clone lays them, up to full over the warning, a last flash as the cards leave, then full
# ahead of each card until it is gone. Each is a band with a brighter rim, so its edge - the edge of
# what hurts - is sharp.
const WILD_LANE_COLOR := Color(1.0, 0.85, 0.15)
const WILD_LANE_DIM_ALPHA := 0.14
const WILD_LANE_FULL_ALPHA := 0.38
const WILD_LANE_FLASH_COLOR := Color(1.0, 0.97, 0.78)
const WILD_LANE_FLASH_ALPHA := 0.75
const WILD_LANE_FLASH_TIME := 0.1
const WILD_LANE_RIM_WIDTH := 3.0
const WILD_LANE_RIM_ALPHA := 1.8
# His gate out and in, and a clone scattering, all draw the fan of cards (FINAL_CARD_BURST) on the floor
# point.

#THE HUD
# CarterArtLayout.HUD_KEEP_OUT's rects, which the suite's carter_hud mode measures off the live HUD: every
# fight has the same boss bar block and the same two player corners, and josh_wild_cards holds these to
# his own live HUD. His clones and their badges, and where he comes back in, stay HUD_CLEARANCE clear of
# them and inside the view.
const VIEW_RECT := Rect2(0, 0, 1920, 1080)
const HUD_KEEP_OUT: Array[Rect2] = [
	# The name plate, bar, crest and Break gauge.
	Rect2(720, 33, 480, 148),
	# The player's combo count, hearts and stamina, bottom left.
	Rect2(10, 842, 406, 229),
	# The player's parry streak and hype meter, bottom right.
	Rect2(1371, 946, 537, 126),
]
const HUD_CLEARANCE := 12.0
# A ParryTell badge, red or yellow, around the anchor its bottom tip stands on: a 32x24 frame at 3x.
const TELL_BADGE := Rect2(-48, -72, 96, 72)


static func anim(anim_name: StringName) -> Dictionary:
	if USE_FINAL_ANIMS.get(anim_name, false) and ResourceLoader.exists(FINAL_ANIMS[anim_name].sheet):
		return FINAL_ANIMS[anim_name]
	match anim_name:
		&"dive":
			var summon := anim(&"summon")
			return {sheet = summon.sheet, frames = [summon.frames[mini(1, summon.frames.size() - 1)]], times = [DIVE_TIME],
				loop = false, flips = true}
		&"emerge":
			return reversed(anim(&"dive"))
	return PLACEHOLDER_ANIMS[anim_name]


# `from` played backwards: its frames the other way, each keeping its own time.
static func reversed(from: Dictionary) -> Dictionary:
	var frames: Array = from.frames.duplicate()
	var times: Array = []
	for i in frames.size():
		times.append(from.times[mini(i, from.times.size() - 1)])
	frames.reverse()
	times.reverse()
	return from.merged({frames = frames, times = times, loop = false}, true)


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


# Whether something drawn at `rect` is wholly in view and clear of every HUD block.
static func clear_of_hud(rect: Rect2) -> bool:
	if not VIEW_RECT.grow(-HUD_CLEARANCE).encloses(rect):
		return false
	for keep_out in HUD_KEEP_OUT:
		if keep_out.grow(HUD_CLEARANCE).intersects(rect):
			return false
	return true


# Him or a clone of him standing at `feet`, and the badge over his head, facing either way: what has to
# be clear of the HUD wherever he or one of them is put.
static func standing_rect(feet: Vector2) -> Rect2:
	var body := local_rect(BODY_DRAWN)
	var badge := Rect2(TELL_ANCHOR + TELL_BADGE.position, TELL_BADGE.size)
	return Rect2(feet + body.position, body.size).merge(Rect2(feet + badge.position, badge.size))


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
