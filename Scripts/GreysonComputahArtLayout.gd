extends RefCounted

# Every number that depends on how Greyson, Computah and their effects are drawn, so a redraw only
# needs this file. Points and boxes are in texels on one of their frames, origin top-left.
#
# BOTH SHEET SETS ARE HORIZONTAL STRIPS DRAWN FACING RIGHT, vframes = 1, at SCALE. Greyson's frames
# are 96x96 with his feet on row 95; Computah's are 64x64 with his feet on row 63. Each ANCHOR is the
# row below the last drawn one - the floor line the body's own origin stands on - so sheet_offset()
# puts a centred Sprite2D's feet on the node. flip_h mirrors, and mirrored() flips a measured point
# with the pose it was measured on.
#
# THE BATTERY COSTS NO EXTRA ART. computah_idle and computah_run are each the same four-frame cycle
# emitted three times, one per charge state, so `frame = charge_state * 4 + cycle_frame` with 0 full,
# 1 half, 2 low. Cell count, cell colour and the antenna ball all change together, which is the
# three-way read the chase depends on; a colour swap alone would keep four lit cells and lose the
# count. Entries drawn off those two sheets carry `charge_rows = true`.

const SCALE := 3.0

#GREYSON (96x96 strips, feet on row 95, x = 47.5 the mirror axis)
const G_FRAME := Vector2(96, 96)
const G_ANCHOR := Vector2(48, 96)
const G_DIR := "res://Assets/Characters/Greyson/"
# What the player can punch: from just under his crown down to his boots, the width of his torso and
# arms at rest. Traced off greyson_idle, whose silhouette runs x 6..88.
const G_BODY_BOX := Rect2(18, 10, 60, 86)
# Where the finisher's daze stars circle, in px above the floor point he stands on: his crown is on
# row 0, so 288 px up, and the stars sit a little over that.
const G_DAZE_ANCHOR := Vector2(0, -312)
# Where a parry tell stands, over the same crown.
const G_TELL_ANCHOR := Vector2(0, -322)
# Where the twin beam rig sits in his hands in phase two: chest height, on his middle.
const G_BEAM_ORIGIN := Vector2(0, -190)
# Where a thrown piece of junk leaves his hand, on the combo sheet's release frame.
const G_HAND_THROW := Vector2(83, 49)

#COMPUTAH (64x64 strips, feet on row 63, x = 31.5 the mirror axis)
const C_FRAME := Vector2(64, 64)
const C_ANCHOR := Vector2(32, 64)
const C_DIR := "res://Assets/Characters/Computah/"
# His standing chassis, traced off computah_idle (x 6..57, y 8..64).
const C_BODY_BOX := Rect2(8, 12, 48, 52)
# The collapsed pose, which is what the battery window opens on: computah_drop's down frames start on
# row 19.
const C_DOWN_BODY_BOX := Rect2(6, 22, 52, 42)
# Over the down pose the punish window shows, high enough to clear his standing antenna too.
const C_DAZE_ANCHOR := Vector2(0, -196)
const C_TELL_ANCHOR := Vector2(0, -206)
# The eyes the twin beams come out of, on his face plate.
const C_BEAM_ORIGIN := Vector2(0, -120)
# The charge gauge over his head while the chase runs.
const C_BATTERY_OFFSET := Vector2(0, -216)

# The four-frame cycle each charge state of computah_idle and computah_run holds.
const CHARGE_CYCLE := 4
enum Charge { FULL, HALF, LOW }

#GREYSON'S ANIMATIONS
# name: sheet, frames in order, seconds on each (the last value repeats) and whether it loops.
# `flips` marks the poses that mirror when he faces left.
# The five-hit combo is three drawings cycled so the fists alternate: wind-up 0 is the tell, then
# 1, 2, 3, 2, 1 are the five extensions, then 4 snaps him back. Damage lands on the first tick of
# each extension frame, which combo_hit_time() reads straight off these numbers.
const GREYSON_ANIMS := {
	&"idle": {sheet = G_DIR + "greyson_idle.png",
		frames = [0, 1, 2, 3], times = [0.16], loop = true},
	# He works the crowd between attacks on the same loop, a touch faster.
	&"taunt": {sheet = G_DIR + "greyson_idle.png",
		frames = [0, 1, 2, 3], times = [0.12], loop = true},
	# The combo sheet's wind-up frame held, which is also the pose he catches in.
	&"throw_wind": {sheet = G_DIR + "greyson_combo.png",
		frames = [0], times = [1.0], loop = true, flips = true},
	&"throw": {sheet = G_DIR + "greyson_combo.png",
		frames = [1, 4], times = [0.09, 0.16], loop = false, flips = true},
	&"throw_recover": {sheet = G_DIR + "greyson_idle.png",
		frames = [0, 1, 2, 3], times = [0.16], loop = true},
	&"crank": {sheet = G_DIR + "greyson_idle.png",
		frames = [0, 1, 2, 3], times = [0.10], loop = true},
	&"catch": {sheet = G_DIR + "greyson_combo.png",
		frames = [0], times = [0.2], loop = false, flips = true},
	&"combo": {sheet = G_DIR + "greyson_combo.png",
		frames = [0, 1, 2, 3, 2, 1, 4], times = [0.20, 0.11, 0.11, 0.11, 0.11, 0.11, 0.20],
		loop = false, flips = true},
	&"hit": {sheet = G_DIR + "greyson_hit.png",
		frames = [0, 1, 2], times = [0.07], loop = false},
	# On the brink: held on the last recoil frame, doubled over and not getting up.
	&"brink": {sheet = G_DIR + "greyson_hit.png",
		frames = [2], times = [1.0], loop = true},
	&"rage": {sheet = G_DIR + "greyson_phase2_idle.png",
		frames = [0, 1, 2, 3], times = [0.12], loop = true},
	&"phase2_idle": {sheet = G_DIR + "greyson_phase2_idle.png",
		frames = [0, 1, 2, 3], times = [0.20], loop = true},
	&"beam_hold": {sheet = G_DIR + "greyson_phase2_idle.png",
		frames = [0], times = [1.0], loop = true},
	&"defeat": {sheet = G_DIR + "greyson_defeat.png",
		frames = [0, 1, 2, 3, 4], times = [0.14, 0.12, 0.12, 0.30, 1.0], loop = false},
}

# The step in `combo` each of the five hits lands on, and the sheet frame that draws it.
const COMBO_HIT_STEPS := [1, 2, 3, 4, 5]
# The punching fist's centre on each combo frame, in texels. One point per drawing, so a burst lands
# on the knuckles whichever of the five hits is playing.
const COMBO_FIST_POINTS := {1: Vector2(53, 49), 2: Vector2(44, 52), 3: Vector2(50, 55)}
# Where the player is held through the combo, in px from Greyson's own floor point, toward the side
# he faces: just past the reach of his lead fist.
const COMBO_SPOT := Vector2(150, 0)

#COMPUTAH'S ANIMATIONS
# `charge_rows` marks the two sheets that carry all three charge states; their frames are the cycle
# index, and the body adds charge_state * CHARGE_CYCLE.
# The hand-over frames the sheets were drawn for: run 2 -> drop 0 (the same pose), drop 3<->4 loops
# for the punish window, and drop 2 -> 1 -> 0 reversed brings him back up.
const COMPUTAH_ANIMS := {
	&"idle": {sheet = C_DIR + "computah_idle.png",
		frames = [0, 1, 2, 3], times = [0.16], loop = true, charge_rows = true},
	&"taunt": {sheet = C_DIR + "computah_idle.png",
		frames = [0, 1, 2, 3], times = [0.11], loop = true, charge_rows = true},
	&"laser_charge": {sheet = C_DIR + "computah_idle.png",
		frames = [0, 1], times = [0.1], loop = true, charge_rows = true},
	&"laser_fire": {sheet = C_DIR + "computah_idle.png",
		frames = [0, 1, 2, 3], times = [0.07], loop = true, charge_rows = true},
	&"chase": {sheet = C_DIR + "computah_run.png",
		frames = [0, 1, 2, 3], times = [0.09], loop = true, flips = true, charge_rows = true},
	# Frame 2 of the run held: the pose the drop was built out of, so committing never pops.
	&"pounce_wind": {sheet = C_DIR + "computah_run.png",
		frames = [2], times = [1.0], loop = true, flips = true, charge_rows = true},
	&"pounce": {sheet = C_DIR + "computah_run.png",
		frames = [0, 1, 2, 3], times = [0.05], loop = true, flips = true, charge_rows = true},
	# The stumble: two frames down the drop and the same two back up again.
	&"pounce_whiff": {sheet = C_DIR + "computah_drop.png",
		frames = [0, 1, 1, 0], times = [0.12], loop = false, flips = true},
	&"grab_hold": {sheet = C_DIR + "computah_run.png",
		frames = [2], times = [1.0], loop = true, flips = true, charge_rows = true},
	&"toss": {sheet = C_DIR + "computah_drop.png",
		frames = [1], times = [0.4], loop = false, flips = true},
	# The battery running out: down onto his face, then the twitching loop the window stays on.
	&"collapse": {sheet = C_DIR + "computah_drop.png",
		frames = [0, 1, 2], times = [0.12, 0.10, 0.14], loop = false},
	&"down": {sheet = C_DIR + "computah_drop.png",
		frames = [3, 4], times = [0.30], loop = true},
	&"reboot": {sheet = C_DIR + "computah_drop.png",
		frames = [2, 1, 0], times = [0.12, 0.10, 0.12], loop = false},
	&"hit": {sheet = C_DIR + "computah_hit.png",
		frames = [0, 1, 2], times = [0.07], loop = false},
	# On the brink: held face down on the mat, not rebooting.
	&"brink": {sheet = C_DIR + "computah_drop.png",
		frames = [3], times = [1.0], loop = true},
	# The alarm he goes off in over Greyson's body, on the same overcharged frames, racing.
	&"rage": {sheet = C_DIR + "computah_phase2_idle.png",
		frames = [0, 1, 2, 3], times = [0.08], loop = true},
	&"overcharge_idle": {sheet = C_DIR + "computah_phase2_idle.png",
		frames = [0, 1, 2, 3], times = [0.18], loop = true},
	&"phase2_idle": {sheet = C_DIR + "computah_phase2_idle.png",
		frames = [0, 1, 2, 3], times = [0.18], loop = true},
	&"defeat": {sheet = C_DIR + "computah_defeat.png",
		frames = [0, 1, 2, 3, 4], times = [0.14, 0.12, 0.12, 0.30, 1.0], loop = false},
}

#THE TWO-BAR HEALTH PANEL
# One framed panel, one name, two stacked bars joined by a bracket: they have to read as one boss.
# Each bar carries a ghost marker at the other body's ratio, so the gap between a bar's fill edge and
# its marker IS the imbalance the fight is about.
const PANEL_RECT := Rect2(720, 28, 480, 104)
const PANEL_BG := Color(0.05, 0.06, 0.09, 0.82)
const PANEL_BORDER := Color(0, 0, 0)
const PANEL_BORDER_WIDTH := 3
const NAME_POSITION := Vector2(732, 32)
const NAME_FONT_SIZE := 30
const BAR_SIZE := Vector2(400, 20)
const BAR_LEFT := 764.0
const BAR_TOP := [70.0, 100.0]
# The bracket joining the two bars down their left edge.
const BRACKET_RECT := Rect2(752, 70, 6, 50)
const BRACKET_COLOR := Color(0.62, 0.66, 0.78, 0.9)
# Which body owns which row: Greyson on top, Computah under him.
const BAR_LABELS := ["G", "C"]
const BAR_LABEL_X := 736.0
const BAR_LABEL_FONT_SIZE := 20
const BAR_BG := Color(0.08, 0.08, 0.08, 0.85)
# Greyson's fill, then Computah's: his trunks and Computah's chassis trim.
const BAR_FILL := [Color(0.72, 0.45, 0.92, 1), Color(0.35, 0.72, 0.95, 1)]
const BAR_FILL_LOW := [Color(0.92, 0.42, 0.44, 1), Color(0.95, 0.5, 0.3, 1)]
const BAR_LOW_RATIO := 0.34
# What the healthier body's bar turns as the surge climbs, and how hard it beats.
const BAR_FILL_HOT := Color(1.0, 0.78, 0.22, 1)
const BAR_PULSE_TIME := 0.45
const BAR_PULSE_ALPHA := 0.45
# The other body's ratio, a tick across the bar.
const GHOST_MARKER_WIDTH := 3.0
const GHOST_MARKER_COLOR := Color(1, 1, 1, 0.85)
const BAR_FILL_TIME := 0.2

#THE WORD POPUPS
const WORD_CENTRE := Vector2(960, 290)
const WORD_TIME := 1.0
const WORD_FONT_SIZE := 84
const WORD_COLOR := Color(1.0, 0.76, 0.24)
const WORD_OUTLINE := 10
const WORD_FROM_SCALE := 0.72
const WORD_GROW_TIME := 0.16

#THE OVERCHARGE AURA
# Behind the sprite and ON ITS OWN NODE rather than a child of it: PlayerFinisher._flash and
# PlayerCombo._charged_feedback both write to boss.sprite, which has to stay the body sprite.
const USE_FINAL_AURA := false
const PLACEHOLDER_AURA := {
	"points": 24,
	"color": Color(1.0, 0.62, 0.18),
	"pulse": [0.9, 1.08],
	"pulse_time": 0.5,
}
const AURA_ALPHA := 0.4
# Per body, in px from the floor point: the middle of the glow and how far it reaches.
const AURA_GREYSON := {"centre": Vector2(0, -140), "radii": Vector2(140, 156)}
const AURA_COMPUTAH := {"centre": Vector2(0, -86), "radii": Vector2(96, 100)}

#THE BATTERY GAUGE
# A coded bar over Computah's head while the chase runs: the chase clock IS the battery, and his own
# frames carry the coarse three-way read. This is the precise one.
const USE_FINAL_BATTERY_GAUGE := false
const BATTERY_GAUGE := {
	"size": Vector2(108, 16),
	"border": 3.0,
	"shell": Color(0.08, 0.1, 0.14, 0.9),
	"edge": Color(0.78, 0.84, 0.94),
	# Full, half, low: the same three colours his chest cells use.
	"fills": [Color(0.31, 0.88, 0.4), Color(1.0, 0.76, 0.24), Color(1.0, 0.42, 0.3)],
	# The last seconds flash.
	"flash_time": 1.0,
	"flash_interval": 0.12,
}

#THE COMBO'S IMPACT BURSTS
const USE_FINAL_COMBO_IMPACT := false
const PLACEHOLDER_COMBO_IMPACT := {
	"points": 6,
	"inner_ratio": 0.42,
	"radius": 46.0,
	"color": Color(1.0, 0.94, 0.72),
	"finish_color": Color(1.0, 0.7, 0.3),
	"from_scale": 0.4,
	"to_scale": 1.3,
	"time": 0.2,
	"finish_scale": 2.0,
	"finish_time": 0.3,
}

#THE SPARKS OFF A CRANKED OR OVERHEATING BATTERY
const USE_FINAL_BATTERY_SPARKS := false
const PLACEHOLDER_BATTERY_SPARKS := {
	"count": 7,
	"size": 9.0,
	"reach": Vector2(90, 70),
	"rise": 60.0,
	"color": Color(1.0, 0.9, 0.42),
	"time": 0.34,
}

#THE JUNK GREYSON THROWS
const USE_FINAL_JUNK := false
const PLACEHOLDER_JUNK := {
	"size": Vector2(46, 46),
	"color": Color(0.72, 0.76, 0.86),
	"edge_color": Color(0.24, 0.27, 0.36),
	"edge_width": 4.0,
	# Turns per second in flight.
	"spin": 2.4,
}
const JUNK_HIT_SIZE := Vector2(84, 84)
# What a piece of junk does when it is stopped or lands.
const PLACEHOLDER_JUNK_BURST := {
	"points": 5,
	"inner_ratio": 0.4,
	"radius": 48.0,
	"stopped_color": Color(1.0, 0.95, 0.72),
	"hit_color": Color(0.66, 0.68, 0.76),
	"from_scale": 0.4,
	"to_scale": 1.2,
	"time": 0.2,
}


static func greyson_anim(anim_name: StringName) -> Dictionary:
	return GREYSON_ANIMS[anim_name]


static func computah_anim(anim_name: StringName) -> Dictionary:
	return COMPUTAH_ANIMS[anim_name]


# Seconds from the start of an animation to the start of its frame at `step`.
static func time_to_step(anim: Dictionary, step: int) -> float:
	var times: Array = anim.times
	var total := 0.0
	for i in step:
		total += times[mini(i, times.size() - 1)]
	return total


# When each of the five combo hits lands, measured from the first frame of `combo`, so the beats can
# never drift from the drawing they land on.
static func combo_hit_time(index: int) -> float:
	return time_to_step(GREYSON_ANIMS[&"combo"], COMBO_HIT_STEPS[index])


static func combo_length() -> float:
	var anim: Dictionary = GREYSON_ANIMS[&"combo"]
	return time_to_step(anim, anim.frames.size())


# The fist point of the combo step `index` (0-4), in px from Greyson's floor point.
static func combo_fist(index: int, flipped: bool) -> Vector2:
	var anim: Dictionary = GREYSON_ANIMS[&"combo"]
	var frame: int = anim.frames[COMBO_HIT_STEPS[index]]
	return greyson_local(COMBO_FIST_POINTS[frame], flipped)


# Sprite offset, in texels, that puts an anchor on the sprite's origin.
static func sheet_offset(frame_size: Vector2, anchor: Vector2) -> Vector2:
	return frame_size / 2.0 - anchor


static func greyson_offset() -> Vector2:
	return sheet_offset(G_FRAME, G_ANCHOR)


static func computah_offset() -> Vector2:
	return sheet_offset(C_FRAME, C_ANCHOR)


# Screen-px offset from a body's floor point of a point on its frames. flip_h mirrors the texel
# column, so a measured point follows the pose it was measured on.
static func local(point: Vector2, frame_size: Vector2, anchor: Vector2, flipped: bool) -> Vector2:
	var column: float = (frame_size.x - 1.0 - point.x) if flipped else point.x
	return (Vector2(column, point.y) - anchor) * SCALE


static func greyson_local(point: Vector2, flipped := false) -> Vector2:
	return local(point, G_FRAME, G_ANCHOR, flipped)


static func computah_local(point: Vector2, flipped := false) -> Vector2:
	return local(point, C_FRAME, C_ANCHOR, flipped)


static func greyson_rect(rect: Rect2) -> Rect2:
	return Rect2(greyson_local(rect.position), rect.size * SCALE)


static func computah_rect(rect: Rect2) -> Rect2:
	return Rect2(computah_local(rect.position), rect.size * SCALE)


# A filled ellipse, points on its rim, centred on the origin.
static func ellipse(radii: Vector2, points: int) -> PackedVector2Array:
	var rim := PackedVector2Array()
	for i in points:
		var angle := TAU * i / points
		rim.append(Vector2(cos(angle) * radii.x, sin(angle) * radii.y))
	return rim


# A star, for the placeholder bursts: `points` spikes out to `radius`, the dips at `inner_ratio`.
static func star(points: int, radius: float, inner_ratio: float) -> PackedVector2Array:
	var shape := PackedVector2Array()
	for i in points * 2:
		var angle := TAU * i / (points * 2) - PI / 2.0
		var reach := radius if i % 2 == 0 else radius * inner_ratio
		shape.append(Vector2(cos(angle), sin(angle)) * reach)
	return shape


# A rectangle around the origin, for the placeholder junk.
static func centred_rect(size: Vector2) -> PackedVector2Array:
	var half := size / 2.0
	return PackedVector2Array([
		Vector2(-half.x, -half.y), Vector2(half.x, -half.y),
		Vector2(half.x, half.y), Vector2(-half.x, half.y),
	])


static func additive() -> CanvasItemMaterial:
	var material := CanvasItemMaterial.new()
	material.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	return material
