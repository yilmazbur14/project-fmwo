extends RefCounted

# Every number that depends on how beast Bixby is drawn, so a redraw only needs this file. Points and
# boxes are in texels on a frame, origin top-left. BixbyBeastScript builds the fire hitbox, the hurtbox and
# the shadow from these at runtime.

const SCALE := 3.0

#SHEETS (strips of 192x160 frames, all drawn top-aligned around ANCHOR, with x=96 as the symmetry axis)
const HOVER_SHEET := "res://Assets/Characters/Bixby/bixby_beast.png"
const FLY_SHEET := "res://Assets/Characters/Bixby/bixby_beast_fly.png"
const LAND_SHEET := "res://Assets/Characters/Bixby/bixby_beast_land.png"
const RECOVER_SHEET := "res://Assets/Characters/Bixby/bixby_beast_recover.png"
const HIT_SHEET := "res://Assets/Characters/Bixby/bixby_beast_hit.png"
const TAKEOFF_SHEET := "res://Assets/Characters/Bixby/bixby_beast_takeoff.png"
const ROAR_SHEET := "res://Assets/Characters/Bixby/bixby_beast_roar.png"
const DEFEAT_SHEET := "res://Assets/Characters/Bixby/bixby_beast_defeat.png"
const POUND_SHEET := "res://Assets/Characters/Bixby/bixby_pound.png"
const SPIN_SHEET := "res://Assets/Characters/Bixby/bixby_spin.png"
const DIZZY_SHEET := "res://Assets/Characters/Bixby/bixby_dizzy.png"
# The Inferno, hanging off the top rope: 16 frames, never mirrored.
const PERCH_SHEET := "res://Assets/Characters/Bixby/bixby_perch.png"
const FRAME_SIZE := Vector2(192, 160)
# His feet: where he stands on the ground and what he hovers from.
const ANCHOR := Vector2(96, 151)
# Hover, fly and fire breath are drawn this far above the floor point; everything else stands on it.
const HOVER_HEIGHT := 40.0
# What's drawn on any beast frame, and on the fire-breath frames with the stream at its longest.
const BODY_DRAWN := Rect2(2, 2, 188, 156)
const FIRE_DRAWN := Rect2(2, 2, 188, 251)

#SHADOWS (4 frames of 192x48 each, black, centred on the floor point)
# bixby_beast_shadow.png is cast from the air, one frame per hover frame. bixby_beast_shadow_ground.png
# is at his feet: 0 crouching or standing, 1 exhausted with the wings flat, 2 normal Bixby, 3 Bixby with Liam.
const SHADOW_SHEETS := [
	"res://Assets/Characters/Bixby/bixby_beast_shadow.png",
	"res://Assets/Characters/Bixby/bixby_beast_shadow_ground.png",
]
enum Shadow { AIR, GROUND }
const SHADOW_FRAME_SIZE := Vector2(192, 48)
const SHADOW_CENTRE := Vector2(96, 25)
# The air shadow's drawn extent, the wider of the two.
const SHADOW_DRAWN := Rect2(8, 9, 177, 32)
const SHADOW_ALPHA := 0.38

#FIRE BREATH (bixby_beast_firebreath.png, 3 frames of 192x256: wind-up, burst, full stream)
const FIRE_SHEET := "res://Assets/Characters/Bixby/bixby_beast_firebreath.png"
const FIRE_FRAME_SIZE := Vector2(192, 256)
# The fire drawn on the burst and full-stream frames, traced around the stream to within a texel. The
# middle stream leaves the mouth at (96, 82) and the side streams at (52, 86) and (139, 86).
const FIRE_OUTLINES := {
	1: [
		Vector2(93, 76), Vector2(99, 76), Vector2(104, 80), Vector2(104, 87), Vector2(102, 88),
		Vector2(103, 92), Vector2(107, 93), Vector2(105, 88), Vector2(114, 88), Vector2(113, 94),
		Vector2(106, 95), Vector2(112, 114), Vector2(116, 106), Vector2(135, 88), Vector2(137, 82),
		Vector2(141, 83), Vector2(144, 81), Vector2(142, 84), Vector2(145, 85), Vector2(145, 88),
		Vector2(141, 91), Vector2(140, 98), Vector2(153, 99), Vector2(152, 103), Vector2(137, 102),
		Vector2(136, 105), Vector2(134, 105), Vector2(135, 107), Vector2(132, 112), Vector2(138, 109),
		Vector2(138, 107), Vector2(139, 110), Vector2(130, 115), Vector2(124, 139), Vector2(115, 151),
		Vector2(115, 158), Vector2(110, 158), Vector2(109, 162), Vector2(103, 158), Vector2(90, 158),
		Vector2(84, 160), Vector2(82, 155), Vector2(78, 154), Vector2(78, 152), Vector2(75, 156),
		Vector2(74, 141), Vector2(67, 132), Vector2(65, 126), Vector2(62, 124), Vector2(59, 114),
		Vector2(53, 109), Vector2(54, 107), Vector2(58, 111), Vector2(56, 103), Vector2(40, 103),
		Vector2(39, 100), Vector2(53, 97), Vector2(51, 91), Vector2(47, 88), Vector2(47, 85),
		Vector2(55, 82), Vector2(57, 87), Vector2(67, 96), Vector2(76, 112), Vector2(82, 117),
		Vector2(85, 108), Vector2(86, 95), Vector2(79, 94), Vector2(78, 88), Vector2(87, 88),
		Vector2(87, 93), Vector2(89, 88), Vector2(88, 80),
	],
	2: [
		Vector2(96, 76), Vector2(99, 76), Vector2(104, 80), Vector2(105, 93), Vector2(107, 93),
		Vector2(105, 88), Vector2(114, 88), Vector2(113, 94), Vector2(106, 95), Vector2(111, 110),
		Vector2(125, 98), Vector2(125, 96), Vector2(135, 87), Vector2(137, 82), Vector2(145, 85),
		Vector2(145, 88), Vector2(141, 92), Vector2(140, 98), Vector2(153, 99), Vector2(152, 103),
		Vector2(137, 103), Vector2(133, 112), Vector2(138, 107), Vector2(139, 110), Vector2(132, 115),
		Vector2(130, 114), Vector2(130, 117), Vector2(128, 117), Vector2(127, 128), Vector2(121, 144),
		Vector2(122, 159), Vector2(124, 161), Vector2(125, 171), Vector2(129, 176), Vector2(132, 194),
		Vector2(130, 197), Vector2(131, 209), Vector2(133, 209), Vector2(136, 214), Vector2(136, 244),
		Vector2(138, 245), Vector2(139, 235), Vector2(140, 232), Vector2(142, 232), Vector2(142, 250),
		Vector2(129, 250), Vector2(128, 247), Vector2(124, 247), Vector2(124, 250), Vector2(121, 250),
		Vector2(120, 247), Vector2(118, 250), Vector2(111, 250), Vector2(111, 248), Vector2(109, 250),
		Vector2(104, 250), Vector2(103, 247), Vector2(100, 247), Vector2(99, 250), Vector2(79, 250),
		Vector2(76, 244), Vector2(74, 244), Vector2(71, 250), Vector2(64, 250), Vector2(64, 240),
		Vector2(62, 240), Vector2(61, 250), Vector2(53, 250), Vector2(52, 229), Vector2(55, 221),
		Vector2(54, 210), Vector2(56, 197), Vector2(64, 169), Vector2(71, 157), Vector2(72, 141),
		Vector2(63, 130), Vector2(59, 114), Vector2(53, 109), Vector2(53, 107), Vector2(57, 109),
		Vector2(55, 102), Vector2(40, 103), Vector2(39, 99), Vector2(53, 97), Vector2(51, 91),
		Vector2(47, 88), Vector2(47, 85), Vector2(55, 82), Vector2(57, 87), Vector2(67, 95),
		Vector2(73, 107), Vector2(79, 113), Vector2(85, 95), Vector2(79, 94), Vector2(78, 88),
		Vector2(88, 89), Vector2(88, 80), Vector2(91, 77),
	],
}

# Where the full stream (frame 2) hits the ground: its flame tongues. The fire trail is laid along its
# middle row.
const FIRE_GROUND_CONTACT := Rect2(53, 240, 90, 12)

#COMBINED ATTACK
# The step of the "pound" animation his claws land on, at frame texels (33, 151) and (158, 151).
const POUND_IMPACT_STEP := 1
# The step of "spin_up" his maws light up on, which is where the sonic beams come out.
const SPIN_BEAMS_STEP := 1
# How fast his heads turn while he spins, in degrees of the floor a second: slow enough that a player
# walking round him at mid range keeps ahead of a beam. Walking up or down the screen 300-400 px out to
# his side turns a player 58-66 degrees a second about the axis his maws orbit, and this is 55-62% of it.
const SPIN_DEGREES_PER_SECOND := 36.0
# The loop he spins on, between spin_up and spin_down: its frames, the degrees his heads turn from one to
# the next (every frame has them a third of a turn apart, and the last runs on into the first), the steps
# it may start on out of spin_up's last frame and the frames it may hand over to spin_down's first on,
# without his heads jumping backwards. USE_FINAL_SPIN picks bixby_spin_slow.png's 24 frames, or else the
# four bixby_spin.png draws it in; the lead-in and the wobble stay on bixby_spin.png either way.
const USE_FINAL_SPIN := true
const SPIN_SLOW_SHEET := "res://Assets/Characters/Bixby/bixby_spin_slow.png"
const SPIN_LOOP_FINAL := {sheet = SPIN_SLOW_SHEET,
	frames = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
	step_degrees = 5.0, entry_steps = [22, 0], exit_frames = [1, 2]}
const SPIN_LOOP_PLACEHOLDER := {sheet = SPIN_SHEET, frames = [2, 3, 4, 5], step_degrees = 30.0,
	entry_steps = [0, 1, 2, 3], exit_frames = [5]}
const SPIN_LOOP := SPIN_LOOP_FINAL if USE_FINAL_SPIN else SPIN_LOOP_PLACEHOLDER

#RECOVERY
# What the player can punch while he's down: his grounded body on the recover frames from the headband
# down, side heads and draped wings included.
const RECOVER_BODY_BOX := Rect2(3, 56, 186, 99)
# What he is while he hangs off the rope in the Inferno: the spent pose's drawn body (perch frame 13), from
# the talons on the rope to his hanging feet. Nothing can punch him up there; the player faces it.
const PERCH_BODY_BOX := Rect2(5, 20, 182, 140)
# Where the finisher's daze stars circle: the top of his headband plate as he slumps on the recover
# frames. A daze only ever starts in a punish window, so that is the pose they circle; on the hover
# frames the same point is (96, 12).
const DAZE_ANCHOR := Vector2(96, 56)
# The defeat frame on which the coughed-up Liam lands.
const DEFEAT_LIAM_LANDS_FRAME := 8
# The defeat frame that is a cloud of smoke: a juggle that kills him cuts into his defeat on it.
const DEFEAT_SMOKE_FRAME := 3

#JUGGLED (the tiered finisher's juggle, drawn by BossJuggled from this table)
# bixby_juggle.png's frames are 256x256 against his 192x160, so the sheet hangs on its own offset: (0, -72)
# is what puts its feet texel on his node, the ground line every other sheet of his stands him on.
const USE_FINAL_JUGGLE := true
const FINAL_JUGGLE := {
	"texture": "res://Assets/Characters/Bixby/bixby_juggle.png",
	"hframes": 12,
	"frame_size": Vector2(256, 256),
	"offset": Vector2(0, -72),
	"feet": Vector2(128, 200),
	"tumble_centre": Vector2(128, 136),
	"top_row": 18,
	"clips": {
		&"launch": {"frames": [0, 1], "times": [0.06, 0.08], "loop": false},
		&"tumble": {"frames": [2, 3, 4, 5, 6], "times": [0.14, 0.08, 0.08, 0.08, 0.08], "loop": true},
		&"crash": {"frames": [7, 8, 9], "times": [0.07, 0.09, 0.14], "loop": false},
		&"down": {"frames": [10, 11], "times": [0.4, 0.4], "loop": true},
	},
	"shadow": {
		"texture": "res://Assets/Characters/Bixby/bixby_leap_shadow.png",
		"hframes": 3, "scale": 3.0, "alpha": 0.38, "step": 70.0, "offset": Vector2(0, -1),
	},
	"lying_time": 0.3,
	"outro_delay": 1.8,
	"crash_sfx": {"stream": "res://Assets/Audio/SFX/earthquake_slam.ogg", "pitch": 1.0, "volume_db": 0.0},
}
# The middle of Liam's headband plate on the lying frames (10-11), upside down under the middle head.
# Recorded for later: nothing puts stars over him lying yet.
const JUGGLE_DOWN_PLATE := Vector2(128, 188)

#ANIMATIONS
# name: sheet, frames in order, seconds on each (the last value repeats), whether it loops, and the shadow
# under each frame as [Shadow sheet, frame] (the last one repeats). Optional: frame_size (default
# FRAME_SIZE), and flips for animations drawn facing right that are mirrored while he flies left.
const ANIMS := {
	&"hover": {sheet = HOVER_SHEET, frames = [0, 1, 2, 3], times = [0.12], loop = true,
		shadows = [[Shadow.AIR, 0], [Shadow.AIR, 1], [Shadow.AIR, 2], [Shadow.AIR, 3]]},
	# 0 wings up, 1 downstroke, 2 recovering.
	&"fly": {sheet = FLY_SHEET, frames = [0, 1, 2], times = [0.09, 0.07, 0.08], loop = true, flips = true,
		shadows = [[Shadow.AIR, 0], [Shadow.AIR, 2], [Shadow.AIR, 3]]},
	&"windup": {sheet = FIRE_SHEET, frame_size = FIRE_FRAME_SIZE, frames = [0], times = [1.0], loop = true,
		shadows = [[Shadow.AIR, 2]]},
	&"burst": {sheet = FIRE_SHEET, frame_size = FIRE_FRAME_SIZE, frames = [1], times = [1.0], loop = true,
		shadows = [[Shadow.AIR, 2]]},
	&"stream": {sheet = FIRE_SHEET, frame_size = FIRE_FRAME_SIZE, frames = [2], times = [1.0], loop = true,
		shadows = [[Shadow.AIR, 2]]},
	# 0 wings flared while he comes down (the air shadow stays for his feet to land on), 1 the impact, 2 the heavy crouch.
	&"land": {sheet = LAND_SHEET, frames = [0, 1, 2], times = [0.2, 0.14, 0.35], loop = false,
		shadows = [[Shadow.AIR, 2], [Shadow.GROUND, 0]]},
	# A Break catching him on the ground bounces him down to the floor a juggle needs (BixbyBeastBroken) on
	# the landing's flared frame, held for the hop; he comes down onto the rest of the landing.
	&"hop": {sheet = LAND_SHEET, frames = [0], times = [1.0], loop = true,
		shadows = [[Shadow.AIR, 2]]},
	&"recover": {sheet = RECOVER_SHEET, frames = [0, 1, 2, 3], times = [0.18, 0.14, 0.18, 0.16], loop = true,
		shadows = [[Shadow.GROUND, 1]]},
	&"hit": {sheet = HIT_SHEET, frames = [0, 1], times = [0.08, 0.14], loop = false,
		shadows = [[Shadow.GROUND, 1]]},
	# 0 crouch, 1 wing downbeat, still on the ground, 2 rising.
	&"takeoff": {sheet = TAKEOFF_SHEET, frames = [0, 1, 2], times = [0.22, 0.12, 0.15], loop = false,
		shadows = [[Shadow.GROUND, 0], [Shadow.GROUND, 0], [Shadow.AIR, 3]]},
	# The coil, then the roar shaking between frames 1 and 2 for about a second. On the ground.
	&"roar": {sheet = ROAR_SHEET, frames = [0, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2], times = [0.34, 0.07], loop = false,
		shadows = [[Shadow.GROUND, 0]]},
	# THE COMBINED ATTACK. The pound sheet's first two frames are the rear back, held until he slams; the
	# last four are one slam, looped once per pound, with the claws landing on POUND_IMPACT_STEP.
	&"brace": {sheet = POUND_SHEET, frames = [0, 1], times = [0.09, 0.12], loop = false,
		shadows = [[Shadow.GROUND, 0]]},
	&"pound": {sheet = POUND_SHEET, frames = [2, 3, 4, 5], times = [0.07, 0.08, 0.08, 0.12], loop = true,
		shadows = [[Shadow.GROUND, 0]]},
	# The spin: bixby_spin.png's lead-in his maws light up on, the seamless loop (a third of a turn each
	# time round, SPIN_LOOP) and bixby_spin.png's wobble he stops on. He spins on the floor, not in the air.
	&"spin_up": {sheet = SPIN_SHEET, frames = [0, 1], times = [0.11, 0.09], loop = false,
		shadows = [[Shadow.GROUND, 0]]},
	# Each frame held for as long as his heads take to turn its step at SPIN_DEGREES_PER_SECOND.
	&"spin": {sheet = SPIN_LOOP.sheet, frames = SPIN_LOOP.frames,
		times = [SPIN_LOOP.step_degrees / SPIN_DEGREES_PER_SECOND], loop = true,
		shadows = [[Shadow.GROUND, 0]]},
	# The wobble he stops on. He turns on into its first frame at the loop's rate (BixbyBeastCombined runs the
	# loop on until his heads reach it), and its second is drawn 40 degrees on from the first: held 1.33 s,
	# that turn reads at 30 degrees a second, slowing from the loop's 36, before he stops.
	&"spin_down": {sheet = SPIN_SHEET, frames = [6, 7], times = [1.33, 0.3], loop = false,
		shadows = [[Shadow.GROUND, 0]]},
	&"dizzy": {sheet = DIZZY_SHEET, frames = [0, 1, 2, 3], times = [0.13], loop = true,
		shadows = [[Shadow.GROUND, 0]]},
	# 0 the final blow, 1 collapse, 2 the glow dies, 3 smoke, 4 normal Bixby dizzy, 5 cough wind-up,
	# 6 Liam shoots out, 7 tumbles, 8 lands, 9 the hold. Bixby and Liam are drawn in.
	&"defeat": {sheet = DEFEAT_SHEET, frames = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], times = [0.1, 0.3, 0.16, 0.14, 0.6, 0.34, 0.12, 0.12, 0.4, 1.0], loop = false,
		shadows = [[Shadow.GROUND, 0], [Shadow.GROUND, 1], [Shadow.GROUND, 1], [Shadow.GROUND, 1], [Shadow.GROUND, 2],
			[Shadow.GROUND, 2], [Shadow.GROUND, 2], [Shadow.GROUND, 2], [Shadow.GROUND, 3]]},
	# THE INFERNO, on the middle of the top rope (BixbyBeastInferno, BixbyInfernoArtLayout): the grab, the
	# hang, the volley (the middle, left and right head spitting, one frame each, which the attack shows per
	# spit), the inhale, the rear back, the breath, spent, and letting go, ending on land frame 0's pose.
	# Drawn facing down the screen, never mirrored. His shadow is hidden while he is on the rope, so the ones
	# listed are never seen.
	&"perch_land": {sheet = PERCH_SHEET, frames = [0, 1], times = [0.2, 0.25], loop = false,
		shadows = [[Shadow.AIR, 0]]},
	&"perch": {sheet = PERCH_SHEET, frames = [2, 3], times = [0.25], loop = true,
		shadows = [[Shadow.AIR, 0]]},
	&"volley": {sheet = PERCH_SHEET, frames = [4, 5, 6], times = [1.0], loop = true,
		shadows = [[Shadow.AIR, 0]]},
	&"inhale": {sheet = PERCH_SHEET, frames = [7, 8, 9], times = [0.13], loop = true,
		shadows = [[Shadow.AIR, 0]]},
	&"rear_back": {sheet = PERCH_SHEET, frames = [10], times = [1.0], loop = true,
		shadows = [[Shadow.AIR, 0]]},
	&"perch_breath": {sheet = PERCH_SHEET, frames = [11, 12], times = [0.07], loop = true,
		shadows = [[Shadow.AIR, 0]]},
	&"spent": {sheet = PERCH_SHEET, frames = [13], times = [1.0], loop = true,
		shadows = [[Shadow.AIR, 0]]},
	&"release": {sheet = PERCH_SHEET, frames = [14, 15], times = [0.1], loop = false,
		shadows = [[Shadow.AIR, 0]]},
}


# Seconds from the start of an animation to the start of its frame at `step`.
static func time_to_step(anim_name: StringName, step: int) -> float:
	var times: Array = ANIMS[anim_name].times
	var total := 0.0
	for i in step:
		total += times[mini(i, times.size() - 1)]
	return total


# How long a whole animation lasts, once.
static func anim_time(anim_name: StringName) -> float:
	return time_to_step(anim_name, ANIMS[anim_name].frames.size())


# Seconds each frame of the spin loop is held.
static func spin_step_time() -> float:
	return ANIMS[&"spin"].times[0]


static func juggle() -> Dictionary:
	return FINAL_JUGGLE


# Sprite offset, in texels, that puts ANCHOR on the sprite's origin for a sheet of this frame size.
static func sheet_offset(frame_size: Vector2) -> Vector2:
	return frame_size / 2.0 - ANCHOR


# Screen-px offset from his feet of a point on his frames.
static func local(point: Vector2) -> Vector2:
	return (point - ANCHOR) * SCALE


static func local_rect(rect: Rect2) -> Rect2:
	return Rect2(local(rect.position), rect.size * SCALE)


# The shadow's drawn box in px around the floor point under him.
static func shadow_rect() -> Rect2:
	return Rect2((SHADOW_DRAWN.position - SHADOW_CENTRE) * SCALE, SHADOW_DRAWN.size * SCALE)


static func shadow_offset() -> Vector2:
	return SHADOW_FRAME_SIZE / 2.0 - SHADOW_CENTRE


static func fire_outline(frame: int) -> PackedVector2Array:
	var points := PackedVector2Array()
	for point in FIRE_OUTLINES[frame]:
		points.append(local(point))
	return points
