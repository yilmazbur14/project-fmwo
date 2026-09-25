extends RefCounted

# Every number that depends on how Computah and his effects are drawn, so a redraw only needs this
# file. Points and boxes are in texels on one of his frames, origin top-left.
#
# HIS SHEETS ARE HORIZONTAL STRIPS DRAWN FACING RIGHT, vframes = 1, at SCALE. Frames are 96x96 with
# his feet on row 95. C_ANCHOR is the row below the last drawn one - the floor line his own origin
# stands on - so sheet_offset() puts a centred Sprite2D's feet on the node. flip_h mirrors, and
# computah_local() flips a measured point with the pose it was measured on.
#
# EVERY POSE MIRRORS. One arm is a cannon, so there is no symmetric frame left on him: an unflipped
# pose leaves the weapon on his screen-right whichever way he is facing. `flips` is on every entry
# below, and the hurtboxes mirror with him too (computah_rect takes the facing).
#
# THE BATTERY COSTS NO EXTRA ART. computah_idle and computah_run are each the same four-frame cycle
# emitted three times, one per charge state, so `frame = charge_state * 4 + cycle_frame` with 0 full,
# 1 half, 2 low. Cell count, cell colour and the antenna ball all change together, which is the
# three-way read the chase depends on; a colour swap alone would keep four lit cells and lose the
# count. Entries drawn off those two sheets carry `charge_rows = true`.
#
# THE MUZZLE FX ARE NOT ON HIS BODY. computah_beam_charge and computah_beam_ready ship with the
# charge ball and the lock flare stripped off them, so the glow is a node of its own that grows
# through the charge instead of popping on with a frame. It is drawn at C_CHARGE_BALL / C_LOCK_BALL,
# which are where the drawings put those effects: just off the muzzle face, not on it.

const SCALE := 3.0

#COMPUTAH (96x96 strips, feet on row 95, x = 47.5 the mirror axis)
const C_FRAME := Vector2(96, 96)
const C_ANCHOR := Vector2(48, 96)
const C_DIR := "res://Assets/Characters/Computah/"
# His standing chassis, traced off computah_idle frame 0. THE CANNON IS LEFT OUT OF IT: the whole
# silhouette is Rect2(11, 17, 81, 79), and the extra 19 texels are all barrel. Punching a gun reads
# oddly, and the wide box hands him a hurtbox half a body wider than the body it belongs to, so the
# box stops at the shoulder and the weapon is scenery.
const C_BODY_BOX := Rect2(11, 17, 62, 79)
# THE VENT, which is what the beam's punish window opens on: computah_beam_recover's hold, down on
# one knee with the barrel planted on the mat. It is NOT the same band as the floor pose below - he
# is half a body taller kneeling than he is flat out - so the two carry separate boxes.
const C_VENT_BODY_BOX := Rect2(3, 37, 83, 59)
# Flat on the mat: computah_drop's floor loop, which the chase's flat battery and a parried pounce
# both put him in.
const C_DOWN_BODY_BOX := Rect2(2, 53, 87, 43)
# Over whichever pose the punish window caught him in, and high enough to clear his tallest: the
# antenna on beam_ready reaches 285 px above his feet.
const C_DAZE_ANCHOR := Vector2(0, -300)
# HIS CROWN ON THE FLOOR LOOP, computah_drop 3-4 (`down`), where a Break leaves him: the stars circle
# DAZE_GAP over it. Measured the way that 285 px was: the topmost row holding a drawn texel (alpha over
# 128, checks.py's threshold, keyline included). On these frames that is the dome of his helmet, not
# the antenna, which lies out to the left with its ball no higher than row 54. The dome tops out on row
# 50 on frame 3 and row 51 on frame 4, where the twitch drops him a row; the higher is taken so the
# stars clear both. x is the middle of that row's run, columns 24 to 31. 138 px over his floor point.
const C_DOWN_HEAD := Vector2(28, 50)
# The collapse's frames before he is flat, measured the same way, so the stars ride his head down from
# the Break rather than hanging over his chest on the standing falter it opens on: frame 0 is that
# falter (the dome on row 19, columns 50 to 55), 1 the knees going (row 41, columns 24 to 31). Frame 2
# tops out a row under C_DOWN_HEAD, which serves it.
const C_COLLAPSE_HEADS := {0: Vector2(53, 19), 1: Vector2(28, 41)}
# PlayerFinisher's "about 34 px above the head", as Jordan's and Matt's.
const DAZE_GAP := 34.0
# WHERE THE YELLOW LOCK RING STANDS, AND IT IS THE WHOLE READ OF HIS BEAM, so it may not be behind
# anything. The ring hangs UP from this anchor and reaches 69 px above it, and the block's crest
# above him reaches down to y=174. THIS AND COMPUTAH_HOME ARE ONE NUMBER IN TWO PLACES: he fights on
# x=960, under his own health block, and at the pair's old row the redesign's own crown was behind
# that block with nothing left over him to hang this on. His home came down instead, which is what
# lets this sit clear of the block AND above his antenna rather than across his face.
const C_TELL_ANCHOR := Vector2(0, -300)
# THE CANNON ARM'S MUZZLE: where the beam is fired from. In texels on a right-facing frame, so it
# MIRRORS with him - a cannon held out in front is not on the mirror axis the way his eyes were.
# ONE POINT PER POSE, because the barrel is somewhere different in each of them, and one point per
# FRAME on the discharge: the recoil drives it back into the shoulder on frame 1, and a beam pinned
# to a single fixed point visibly comes away from the barrel there.
const C_MUZZLE := Vector2(71, 55)
const C_MUZZLE_CHARGE := Vector2(70, 60)
const C_MUZZLE_VENT := Vector2(66, 89)
const C_MUZZLE_FIRE := [Vector2(74, 54), Vector2(58, 59), Vector2(66, 56)]
# THE UPPERCUT'S LOAD, per frame: the Shoryuken plant drops the barrel to his hip and keeps dropping
# it over the three frames. The charge glow the mine trap hangs on it was reading C_MUZZLE, which is
# the LOCK's muzzle out at chest height, so it floated a body's width above the bore for the whole
# 1.5 s charge.
const C_MUZZLE_UPPERCUT_WIND := [Vector2(66, 78), Vector2(63, 83), Vector2(60, 87)]
# THE OVERLOAD'S BARREL HANGS AT HIS SIDE with the muzzle on the mat, in every one of its poses -
# that silhouette is the whole read of the attack, and computah_mm.py asserts it at build time.
const C_MUZZLE_OVERLOAD := Vector2(64, 90)
# The pose each of those belongs to. Anything not listed fires from the lock's muzzle.
const C_MUZZLES := {
	&"beam_brace": [C_MUZZLE_CHARGE],
	&"beam_ready": [C_MUZZLE],
	&"beam_fire": C_MUZZLE_FIRE,
	&"vent": [C_MUZZLE_VENT],
	&"vent_hold": [C_MUZZLE_VENT],
	&"vent_up": [C_MUZZLE_VENT],
	&"uppercut_wind": C_MUZZLE_UPPERCUT_WIND,
	&"overload_brace": [C_MUZZLE_OVERLOAD],
	&"overload_charge": [C_MUZZLE_OVERLOAD],
	&"overload_release": [C_MUZZLE_OVERLOAD],
	&"overload_break": [C_MUZZLE_OVERLOAD],
}
# The held poses that stand on a box of their own; everything else is the standing chassis.
# The uppercut's felled frames take the floor box too: checks.py fall_band() measures them against
# computah_drop's down frames and fails the build if the two bands drift apart.
const C_POSE_BOXES := {
	&"vent": C_VENT_BODY_BOX,
	&"vent_hold": C_VENT_BODY_BOX,
	&"vent_up": C_VENT_BODY_BOX,
	&"collapse": C_DOWN_BODY_BOX,
	&"down": C_DOWN_BODY_BOX,
	&"reboot": C_DOWN_BODY_BOX,
	&"uppercut_fall": C_DOWN_BODY_BOX,
	&"fallen": C_DOWN_BODY_BOX,
	&"uppercut_up": C_DOWN_BODY_BOX,
}
# The charge gauge over his head while the chase runs, clear of the antenna on his run frames.
const C_BATTERY_OFFSET := Vector2(0, -300)

# The four-frame cycle each charge state of computah_idle and computah_run holds.
const CHARGE_CYCLE := 4
enum Charge { FULL, HALF, LOW }

#COMPUTAH'S ANIMATIONS
# name: sheet, frames in order, seconds on each (the last value repeats) and whether it loops.
# `flips` marks the poses that mirror when he faces left, which is now every one of them: the cannon
# arm means he has no symmetric pose left.
# `charge_rows` marks the two sheets that carry all three charge states; their frames are the cycle
# index, and the body adds charge_state * CHARGE_CYCLE.
# The hand-over frames the sheets were drawn for: run 2 -> drop 0 (the same pose), drop 3<->4 loops
# for the battery window, and drop 2 -> 1 -> 0 reversed brings him back up.
#
# THE BEAM OWNS FOUR POSES OF ITS OWN. beam_brace is the two-handed charge - cannon arm out, normal
# arm bracing it - held for the whole track; beam_ready is THE LOCK, where he snaps upright and the
# aim stops following; beam_fire is the recoil of it going off; and the vent below is the punish
# window the shot leaves open, down on one knee with the barrel cooling on the mat. The vent is NOT
# the drop: being knocked over and putting the weapon down are different pictures and different
# hurtboxes.
const COMPUTAH_ANIMS := {
	&"idle": {sheet = C_DIR + "computah_idle.png",
		frames = [0, 1, 2, 3], times = [0.16], loop = true, flips = true, charge_rows = true},
	&"taunt": {sheet = C_DIR + "computah_idle.png",
		frames = [0, 1, 2, 3], times = [0.11], loop = true, flips = true, charge_rows = true},
	# POWERED DOWN, AND THEN COMING UP, for his entrance. computah_dormant is ONE ROW OF FOUR: 0 is
	# switched off - eye bars dark, antenna flopped over, knees buckled, one dim ember cell - and 1-3
	# are the boot, the jolt, the push and the set. Frames 1-3 were drawn lerped toward idle frame 0,
	# so the boot hands over to the fighting pose by construction rather than by eye, and all three
	# are needed: f3 to idle is a 3-row step, but dropping f2 makes f1 to f3 an 18-row, 54 px jump
	# that pops.
	# ⚠️ NEITHER CARRIES charge_rows, and the entry these replaced did. It was borrowing computah_idle,
	# which is the same cycle three times over; this is a single row of four, so the charge offset
	# would index frame 8 of a 4-frame sheet the moment the intro set the battery LOW. The powered-down
	# read is drawn into frame 0 here instead of being made by a row.
	# He is not punchable in the intro, so neither needs a C_POSE_BOXES entry. Measured for the record
	# if that ever changes: dormant f0's body is Rect2(12, 37, 74, 59), whose top row and height are
	# exactly C_VENT_BODY_BOX's, so that is the box - NOT C_BODY_BOX, whose top row of 17 would float
	# 60 px of hurtbox above his head. The boot frames climb through the band (tops 37, 38, 27, 20
	# against idle's 17), so no single box fits those.
	&"dormant": {sheet = C_DIR + "computah_dormant.png",
		frames = [0], times = [1.0], loop = true, flips = true},
	&"boot": {sheet = C_DIR + "computah_dormant.png",
		frames = [1, 2, 3], times = [0.09, 0.10, 0.10], loop = false, flips = true},
	&"beam_brace": {sheet = C_DIR + "computah_beam_charge.png",
		frames = [0], times = [1.0], loop = true, flips = true},
	&"beam_ready": {sheet = C_DIR + "computah_beam_ready.png",
		frames = [0], times = [1.0], loop = true, flips = true},
	# The discharge, held on its last frame until the vent takes over: 0 is the shot leaving, 1 the
	# peak recoil, 2 the barrel coming back down.
	&"beam_fire": {sheet = C_DIR + "computah_beam_fire.png",
		frames = [0, 1, 2], times = [0.06, 0.10, 0.34], loop = false, flips = true},
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
	# The vent: down onto the knee, then the steam loop the beam's window stays on, and the same
	# frames back up again.
	&"vent": {sheet = C_DIR + "computah_beam_recover.png",
		frames = [0, 1], times = [0.12, 0.10], loop = false, flips = true},
	&"vent_hold": {sheet = C_DIR + "computah_beam_recover.png",
		frames = [2, 3], times = [0.22], loop = true, flips = true},
	&"vent_up": {sheet = C_DIR + "computah_beam_recover.png",
		frames = [1, 0], times = [0.10, 0.12], loop = false, flips = true},
	# Knocked over: down onto his face, then the twitching loop the battery window stays on.
	&"collapse": {sheet = C_DIR + "computah_drop.png",
		frames = [0, 1, 2], times = [0.12, 0.10, 0.14], loop = false, flips = true},
	&"down": {sheet = C_DIR + "computah_drop.png",
		frames = [3, 4], times = [0.30], loop = true, flips = true},
	&"reboot": {sheet = C_DIR + "computah_drop.png",
		frames = [2, 1, 0], times = [0.12, 0.10, 0.12], loop = false, flips = true},
	# THE MINE TRAP'S UPPERCUT, off computah_uppercut. The load is a Shoryuken plant with the barrel
	# dropped to his hip; the rise is the swing; the fall is him overbalancing through it, which only
	# happens when the player mashed out and there is nothing left on the end of the punch.
	# uppercut_wind holds its last frame for as long as the charge does, so mine_charge can be retuned
	# without redrawing anything.
	&"uppercut_wind": {sheet = C_DIR + "computah_uppercut.png",
		frames = [0, 1, 2], times = [0.20, 0.20, 1.0], loop = false, flips = true},
	&"uppercut": {sheet = C_DIR + "computah_uppercut.png",
		frames = [3, 4, 5], times = [0.07, 0.07, 0.26], loop = false, flips = true},
	# Overbalanced: the bounce, then the loop the punish window is spent in, then the same frames back.
	&"uppercut_fall": {sheet = C_DIR + "computah_uppercut.png",
		frames = [6, 7], times = [0.12, 0.10], loop = false, flips = true},
	&"fallen": {sheet = C_DIR + "computah_uppercut.png",
		frames = [8, 9], times = [0.30], loop = true, flips = true},
	&"uppercut_up": {sheet = C_DIR + "computah_uppercut.png",
		frames = [7, 6], times = [0.10, 0.12], loop = false, flips = true},
	# THE OVERLOAD, his DPS check. He plants and arches back over his heels (overload_brace), holds
	# that arch shaking while the core winds up (overload_charge), and then either dumps everything
	# into the arena (overload_release) or fizzles out with nothing to show for it (overload_break,
	# which hands straight into the collapse the Break gauge's own window opens on).
	# THE CHARGE SHEET IS 4 FRAMES x 3 ROWS AND RUNS THE OPPOSITE WAY ROUND TO THE BATTERY: ROW 0 IS
	# BARELY CHARGED AND ROW 2 IS WHITE-HOT, where computah_idle and computah_run have row 0 FULL. Two
	# sheets on one character running opposite ways is a genuine trap, so it is written at both ends -
	# see build_overload_charge in art_source/computah_redesign/computah_mm.py. `charge_rows` is the
	# same mechanism either way: the body adds charge_state * CHARGE_CYCLE, and only what the number
	# MEANS differs.
	&"overload_brace": {sheet = C_DIR + "computah_overload_brace.png",
		frames = [0, 1, 2], times = [0.09, 0.09, 0.12], loop = false, flips = true},
	&"overload_charge": {sheet = C_DIR + "computah_overload_charge.png",
		frames = [0, 1, 2, 3], times = [0.08], loop = true, flips = true, charge_rows = true},
	&"overload_release": {sheet = C_DIR + "computah_overload_release.png",
		frames = [0, 1, 2], times = [0.06, 0.10, 0.22], loop = false, flips = true},
	&"overload_break": {sheet = C_DIR + "computah_overload_break.png",
		frames = [0, 1, 2], times = [0.10, 0.10, 0.16], loop = false, flips = true},
	&"hit": {sheet = C_DIR + "computah_hit.png",
		frames = [0, 1, 2], times = [0.07], loop = false, flips = true},
	&"defeat": {sheet = C_DIR + "computah_defeat.png",
		frames = [0, 1, 2, 3, 4], times = [0.14, 0.12, 0.12, 0.30, 1.0], loop = false, flips = true},
	# Greyson's takeover (GreysonTakeover), the approved armless set (2026-09-24): his arm hauled on (wrench f0) and
	# torn off (f1), then armless on the mat, the stump sparking (armless f0 the pose, 1-2 the sparks, looping).
	&"wrench_haul": {sheet = C_DIR + "computah_wrench.png",
		frames = [0], times = [1.0], loop = true, flips = true},
	&"wrench_tear": {sheet = C_DIR + "computah_wrench.png",
		frames = [1], times = [0.12], loop = false, flips = true},
	&"armless": {sheet = C_DIR + "computah_armless.png",
		frames = [0, 1, 2], times = [0.30, 0.10, 0.10], loop = true, flips = true},
}

#GREYSON'S TAKEOVER (the approved armless set, 2026-09-24)
# The wound on the armless frames, where the stump sparks, and the wrench's socket, where Greyson's grip hauls on the
# arm (f0 haul, f1 tear), both in texels on his 96x96 frame. The torn arm is a prop of its own that Greyson carries
# to his own arm: 56x56 frames (torn, carry, lift, fit, hang), its grip on every frame at `grip`, and a socket and a
# muzzle a frame. On the tear its "torn" frame is drawn centred `handoff` px from his floor point, x mirrored when
# both sprites face left, which lands its socket and muzzle exactly on the hauled arm's.
const C_WOUND := Vector2(50.6, 84.9)
const C_WRENCH_SOCKETS := [Vector2(51, 75), Vector2(49, 80)]
const ARM_PROP := {
	"texture": C_DIR + "computah_arm_prop.png",
	"hframes": 5,
	"frame_size": Vector2(56, 56),
	"frames": {&"torn": 0, &"carry": 1, &"lift": 2, &"fit": 3, &"hang": 4},
	"grip": Vector2(28, 25),
	"sockets": [Vector2(13.8, 31.7), Vector2(12.3, 25), Vector2(19, 37.9), Vector2(28, 40.7), Vector2(28, 9.3)],
	"muzzles": [Vector2(42.1, 18.4), Vector2(43.6, 25), Vector2(36.9, 12.2), Vector2(28, 9.4), Vector2(28, 40.6)],
	"handoff": Vector2(43.8, -73.2),
}
# Greyson's hurl: his collar on the armless frames, which Greyson's fist closes on for the grab, and the tumble he is
# thrown in, computah_armless_tumble, 96x96 cells drawn thrown to the right. `held` is the cell he hangs from
# Greyson's fist in, its `grip` on the fist; `spin` the cells the flight turns through, `spin_time` each. The body's
# middle drifts from cell to cell (`middles`), so the flight puts each cell's middle on its arc.
const C_ARMLESS_COLLAR := Vector2(40, 80)
const ARMLESS_TUMBLE := {
	"texture": C_DIR + "computah_armless_tumble.png",
	"hframes": 5,
	"frame_size": Vector2(96, 96),
	"held": 0,
	"grip": Vector2(58, 60),
	"spin": [1, 2, 3, 4],
	"spin_time": 0.07,
	"middles": [Vector2(54, 42), Vector2(49, 47), Vector2(48, 49), Vector2(47, 49), Vector2(47, 47)],
}

#JUGGLED (the tiered finisher's uppercuts, after a Break)
# computah_juggle.png: 12 frames of 192x144, feet on (96, 143). The hit 0-1; the tumble 2-6, looping
# from a hang at the apex; the crash 7-9; and him lying KO'd 10-11. ITS FRAME IS NOT HIS MAIN SHEET'S:
# 192x144 against 96x96, so it hangs at (0, -72) against computah_offset()'s (0, -48) to keep his feet
# on the same floor line. The anchors and timings are the artist's (art_source/computah_juggle, build.py
# measure() and poses.py FRAMES), re-measured off the shipped sheet.
# Paths rather than textures: they load at runtime, so this parses whether or not the sheets are
# imported yet.
const USE_FINAL_JUGGLE := true
const FINAL_JUGGLE := {
	"texture": "res://Assets/Characters/Computah/computah_juggle.png",
	"hframes": 12,
	"frame_size": Vector2(192, 144),
	"offset": Vector2(0, -72),
	"feet": Vector2(96, 143),
	"tumble_centre": Vector2(94, 79),
	"top_row": 24,
	"clips": {
		&"launch": {"frames": [0, 1], "times": [0.06, 0.08], "loop": false},
		&"tumble": {"frames": [2, 3, 4, 5, 6], "times": [0.16, 0.07, 0.07, 0.07, 0.07], "loop": true},
		&"crash": {"frames": [7, 8, 9], "times": [0.06, 0.08, 0.12], "loop": false},
		&"down": {"frames": [10, 11], "times": [0.4, 0.4], "loop": true},
	},
	"shadow": {
		"texture": "res://Assets/Characters/Computah/computah_leap_shadow.png",
		"hframes": 3, "scale": 3.0, "alpha": 0.35, "step": 100.0, "offset": Vector2.ZERO,
	},
	"lying_time": 0.3,
	"outro_delay": 1.8,
	"crash_sfx": {"stream": "res://Assets/Audio/SFX/hit_impact.ogg", "pitch": 0.7, "volume_db": 0.0},
}

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
# In px from the floor point: the middle of the glow and how far it reaches, sized off the standing
# chassis (186 x 237 px at SCALE) the way the old one was sized off his old body.
const AURA_COMPUTAH := {"centre": Vector2(0, -126), "radii": Vector2(124, 150)}

#THE BATTERY GAUGE
# A coded bar over his head while the chase runs: the chase clock IS the battery, and his own frames
# carry the coarse three-way read. This is the precise one.
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

#THE OVERLOAD'S RACE GAUGE
# TWO ROWS OVER HIS HEAD, AND NEVER ONE TUG-OF-WAR BAR. The top row is HIS charge, filling left to
# right on a fixed clock; the bottom is the PLAYER'S damage, filling toward the threshold. Whichever
# fills first wins. One bar that punches pushed back would make the effective threshold shrink with
# time, which is a different and worse attack.
#
# THE BOTTOM ROW IS CELLED, ONE CELL PER HALF-HEART OF DAMAGE, and that is the point of the widget: a
# colour cannot carry a quantity, and the quantity IS the attack. The player does not need to be told
# something is coming - they need to know HOW MUCH MORE DAMAGE, and a countable row of cells says it
# at a glance where a smooth bar only hints at it.
#
# HOT OVER COOL. The charge steps through the same three levels his chest does (charge_state, which
# on the overload's sheet runs 0 barely -> 2 white-hot), so the row and his body tell one story; the
# damage row is cold blue, so the two can never be read as the same quantity.
const USE_FINAL_OVERLOAD_GAUGE := false
# Higher than the battery's -300: this is two rows tall, and it has to clear the antenna on his
# STANDING frames (285 px) as well as the arched overload pose, without reaching the health block's
# crest above him.
const C_OVERLOAD_OFFSET := Vector2(0, -310)
const OVERLOAD_GAUGE := {
	# Per row, outer.
	"size": Vector2(192, 16),
	"row_gap": 5.0,
	"border": 3.0,
	# The battery's shell and rim, so the two gauges read as the same family of widget.
	"shell": Color(0.08, 0.1, 0.14, 0.9),
	"edge": Color(0.78, 0.84, 0.94),
	# Barely charged, winding up, white-hot: indexed by charge_state, the overload's way round.
	"charge_fills": [Color(1.0, 0.76, 0.24), Color(1.0, 0.42, 0.3), Color(1.0, 0.93, 0.86)],
	# The player's row, and the gap between its cells.
	"damage_fill": Color(0.42, 0.82, 1.0),
	"damage_empty": Color(0.16, 0.22, 0.32, 0.9),
	"cell_gap": 3.0,
	# The last of the charge flashes, exactly as the battery's last seconds do.
	"flash_from": 0.8,
	"flash_interval": 0.1,
}

#THE MINE POD
# A 32x32 strip of nine frames, drawn facing nobody - it is a thing on the floor, so it never flips.
# Its floor point is the BOTTOM-CENTRE OF THE WARNING RING rather than the middle of the body,
# because the ring is what the player reads and what the trigger is measured from.
#
# THE DRAWN RING IS THE TRIGGER AREA, to the texel. MINE_RING_BOX is exactly the cyan's bounding box
# on every armed frame, and art_source/computah_redesign/checks.py mine_ring() fails the build if a
# single cyan pixel strays outside it. That is the promise the attack rests on: a player standing
# clear of the ring they can see is never caught by it. It is NuggetMeteorScript's HIT_SIZE ==
# MARKER_SIZE rule, with the marker drawn into the sheet instead of laid on top of it.
const MINE_FRAME := Vector2(32, 32)
const MINE_ANCHOR := Vector2(16, 31)
const MINE_RING_BOX := Rect2(4, 20, 24, 12)
# Which frames each phase of a pod is drawn with (computah_props.build_mine): 0 just landed and still
# folded, 1-2 the legs coming out with the ring opening dim, 3-4 ARMED on a slow two-frame pulse, 5-6
# the ring breaking up as it expires, 7-8 sprung with the jaws shut.
const MINE_FRAMES := {
	&"flight": [0],
	&"arming": [1, 2],
	&"armed": [3, 4],
	&"fading": [5, 6],
	&"sprung": [7, 8],
}
# SLOW ON PURPOSE. A pulse at a tell's rate would read as a wind-up to answer; this one reads as a
# light on a thing that is simply sitting there.
const MINE_PULSE_TIME := 0.32
const MINE_SPRUNG_FRAME_TIME := 0.09
# The arc a pod is lobbed along, as a fraction of the distance it travels, and how high the sprite
# rides off its shadow at the top of it.
const MINE_ARC_LIFT := 0.35

#THE CANNON'S CHARGE GLOW
# THE FX THE SHIPPED BODIES HAD STRIPPED OFF THEM. It swells at the muzzle over the whole track, so
# the charge is readable off his arm and not only off the aim line, and it snaps to the lock's
# white-hot point when the aim latches. A coded placeholder with its own flag, drawn additively on
# its own node - a baked-in glow could only pop on with a frame.
#
# Where the two drawings put the effect, rather than on the muzzle face: the ball forms just off the
# bore. Both mirror with him, as the muzzle does.
const C_CHARGE_BALL := Vector2(80, 60)
const C_LOCK_BALL := Vector2(79, 55)
const USE_FINAL_CHARGE_GLOW := false
const PLACEHOLDER_CHARGE_GLOW := {
	"points": 16,
	# The drawn ball is 11 texels across the radius, so a full-scale 26 lands on 33 px at SCALE.
	"radii": Vector2(26, 26),
	# The beam's own greens, off the approved frames: the charge is the capacitor's colour, the lock
	# the blown-out one.
	"color": Color(0.31, 0.878, 0.4),
	"locked_color": Color(0.663, 1.0, 0.706),
	# Scale and alpha, track start to lock.
	"from_scale": 0.35,
	"to_scale": 1.25,
	"from_alpha": 0.25,
	"to_alpha": 0.9,
	# What the locked hold sits at: full and steady, no longer growing.
	"locked_scale": 1.35,
}

#THE OVERLOAD'S BLAST
# WHAT A FAILED DPS CHECK LOOKS LIKE: everything he was holding leaves the chest at once and washes
# over the whole mat. It has to read as covering EVERYTHING, because that is the rule of the attack -
# there is nowhere to be - so the ring is sized off the far corner of the ropes from his chest rather
# than off his body. Coded, additive and on its own node, like the charge glow.
const C_CORE := Vector2(37, 57)
const USE_FINAL_OVERLOAD_BURST := false
const PLACEHOLDER_OVERLOAD_BURST := {
	"points": 28,
	"radii": Vector2(120, 120),
	# His beam greens, blown out at the front of the wave.
	"color": Color(0.663, 1.0, 0.706),
	"from_scale": 0.3,
	# 120 x 9.5 is 1140 px of reach: the far corner of the ropes is about 1023 px from his chest.
	"to_scale": 9.5,
	"from_alpha": 0.85,
	"time": 0.34,
}

#THE SLAM'S IMPACT BURST
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


static func computah_anim(anim_name: StringName) -> Dictionary:
	return COMPUTAH_ANIMS[anim_name]


static func juggle() -> Dictionary:
	return FINAL_JUGGLE


# Sprite offset, in texels, that puts an anchor on the sprite's origin.
static func sheet_offset(frame_size: Vector2, anchor: Vector2) -> Vector2:
	return frame_size / 2.0 - anchor


static func computah_offset() -> Vector2:
	return sheet_offset(C_FRAME, C_ANCHOR)


# Screen-px offset from his floor point of a point on his frames. flip_h mirrors the texel column,
# so a measured point follows the pose it was measured on.
static func local(point: Vector2, frame_size: Vector2, anchor: Vector2, flipped: bool) -> Vector2:
	var column: float = (frame_size.x - 1.0 - point.x) if flipped else point.x
	return (Vector2(column, point.y) - anchor) * SCALE


static func computah_local(point: Vector2, flipped := false) -> Vector2:
	return local(point, C_FRAME, C_ANCHOR, flipped)


# A measured box in screen px from his floor point. Mirrored the same way a point is: the flipped
# box's top-left is the mirror of the box's top-RIGHT texel, so it lands on the body it was traced
# off whichever way he faces. Nothing on him is symmetric any more, so nothing may skip this.
static func computah_rect(rect: Rect2, flipped := false) -> Rect2:
	var corner := Vector2(rect.position.x + rect.size.x - 1.0, rect.position.y) if flipped else rect.position
	return Rect2(computah_local(corner, flipped), rect.size * SCALE)


# The hurtbox a held pose stands on.
static func computah_box(anim_name: StringName) -> Rect2:
	return C_POSE_BOXES.get(anim_name, C_BODY_BOX)


# A pod's sprite offset, and the trigger area under it. The trigger is READ OFF THE DRAWN RING and
# has no number of its own, so no redraw can leave the two disagreeing: 24 x 12 texels at SCALE is
# 72 x 36 px, centred on the pod and sitting 15 px above its floor point.
static func mine_offset() -> Vector2:
	return sheet_offset(MINE_FRAME, MINE_ANCHOR)


static func mine_ring() -> Rect2:
	return Rect2(local(MINE_RING_BOX.position, MINE_FRAME, MINE_ANCHOR, false), MINE_RING_BOX.size * SCALE)


# The muzzle of the pose being drawn, by the frame of it being drawn.
static func computah_muzzle(anim_name: StringName, frame: int) -> Vector2:
	var points: Array = C_MUZZLES.get(anim_name, [C_MUZZLE])
	return points[clampi(frame, 0, points.size() - 1)]


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


# A rectangle around the origin.
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
