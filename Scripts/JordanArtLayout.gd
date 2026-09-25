extends RefCounted

# Every number that depends on how Jordan is drawn, so a redraw only needs this file. Points and boxes
# are in texels on one of his frames, origin top-left.
#
# His scene is built like Mason's, not like Josh's or Carter's: his CharacterBody2D's origin is not his
# floor point. His Sprite2D stands FLOOR_POINT below it at SCALE, and that point is where his soles are
# and what his fight y-sorts him by. So frame_local() returns BODY-LOCAL PIXELS from his origin, and
# nothing may multiply its result by SCALE again. JordanScript applies this file at runtime; the values
# in JordanScene are copies for the editor.
#
# Each animation has its own USE_FINAL_ANIMS flag: placeholder and final art go through the same code,
# so the fight is playable before the sheets land and turning a flag off brings the placeholder back.
# Every flag is on: the artist's full set landed on 2026-09-23 and was redrawn in the approved v2 look,
# thin and frail, on 2026-09-24, with the same frames, timings and poses. The numbers below are v2's.
# The placeholders are cut from the first approved sheet, jordan_redesign.png.

const SCALE := 3.0

#JORDAN (horizontal strips of 96x96 frames, soles on row 95, x = 48 his centre line)
const FRAME_SIZE := Vector2(96, 96)
# The texel his soles stand on, bottom-middle of the frame.
const ANCHOR := Vector2(48, 95)
# Stands the bottom edge of ANCHOR's row on the sprite's origin, so his soles are ON the floor point
# rather than a texel under it - where his old 64x64 frame stood them at (0, -32). Comes to (0, -48).
const SPRITE_OFFSET := Vector2(FRAME_SIZE.x / 2.0 - ANCHOR.x, FRAME_SIZE.y / 2.0 - ANCHOR.y - 1.0)
# Sprite2D.position, in body px: the floor point. His origin is 96 px over it, level with row 64, the
# lower half of his shirt.
const FLOOR_POINT := Vector2(0, 96)
# The approved sheet: frame 0 the idle, slouched with a hand on his hip and a gold collector box held
# up; frame 1 his signature fist-pump, a pink puff and a gold star off the fist. Every placeholder
# below is one of those two.
const REDESIGN_SHEET := "res://Assets/Characters/Jordan/jordan_redesign.png"

# What the player can punch and turns to face: the taunt's body, the union of all four frames, measured
# off the shipped sheet (art_source/jordan_anims/janim_measure.py). Rows 6 to 95 are the tip of his
# quiff to his soles, and columns 29 to 68 run from the elbow of the arm on his hip to the forearm raised
# under the box. It holds the idle's body, Rect2(29, 9, 37, 87), so one box serves both, and the taunt
# is the only window a punch lands in. The collector box is left out wherever he holds it (hoisted on the
# taunt at columns 65 to 79, rows 2 to 24), as Computah's cannon is: punching a prop reads oddly.
# 120 x 270 px, against the 96 x 180 box the old 64x64 sprite had.
const BODY_BOX := Rect2(29, 6, 40, 90)

# His crown on the taunt, the only window the finisher can daze him in: the quiff's tip on row 6 over
# his head's centre column, 47. It bobs to row 7 on frames 1 and 3.
const TAUNT_CROWN := Vector2(47, 6)
# Where the finisher's daze stars circle: over TAUNT_CROWN, a little under PlayerFinisher's "about 34 px
# above the head", because there is no more room. He stands at (960, 410), the user's call, and the Break
# gauge under his health block hangs to y = 180 across his whole width: at 34 the stars' top three rows
# went behind it. At 30 they are 1 px under it, 1 px clear of the hoisted box and its glint and 3 px over
# his quiff - every star frame checked against every taunt frame and the HUD, pixel by pixel - and those
# 55 px between the gauge and his quiff leave no other gap that clears all three.
# The charged punch that dazes him flinches him first, and the fight freezes on that flinch, so the pose
# under the stars is the hit's. Its crown is seven or eight rows lower, which leaves 24 to 27 px of air.
const DAZE_GAP := 30.0
# His crown on the summon's wind-up (frame 0), the one pose he holds before something happens: row 10
# over column 51.
const WINDUP_CROWN := Vector2(51, 10)
# Where a parry tell's tip would stand over him: four rows over WINDUP_CROWN, as Josh's is over his hat.
# None of his attacks telegraph yet - the funko blast's badge stands over each figure
# (FunkoFigureScript._tell_anchor), not over him - so nothing reads it. The standard badge reaches
# 72 px over its tip, which from here at his spot is up to 17 px behind the Break gauge under his health
# block: an attack that telegraphs over him needs its badge moved.
const TELL_GAP := 12.0
# His crown kneeling in a Break (the `broken` pose, defeat frame 4), measured as TAUNT_CROWN was: the
# quiff's tip on row 34 over his bowed head's centre column, 56 (the head spans 42 to 68). The Break's
# stars circle DAZE_GAP over it: 84 px lower than the taunt's, so at his spot they clear the Break gauge
# by 85 px, and they keep 6 px of air over his hair.
const BROKEN_CROWN := Vector2(56, 34)

#ANIMATIONS
# name: sheet, frames in order, seconds on each (the last value repeats) and whether it loops.
# Optional: motion, the AnimationPlayer clip in JordanScene that moves the whole sprite under the
# frames - squash, stretch or the keel-over. The placeholders are single frames and those clips are all
# the life they have; the final sheets draw their own, so they name none and he rests at SCALE,
# upright (the RESET clip). The final sheets are 96x96 strips with his soles on row 95, so ANCHOR and
# SPRITE_OFFSET hold for all of them. Turn a flag on only once its sheet is in Assets/Characters/Jordan:
# nothing loads a final sheet while its flag is off.
const USE_FINAL_ANIMS := {
	&"idle": true,
	&"summon": true,
	&"summon_pop": true,
	&"taunt": true,
	&"hit": true,
	&"defeat": true,
	&"broken": true,
}

const PLACEHOLDER_ANIMS := {
	&"idle": {sheet = REDESIGN_SHEET, frames = [0], times = [1.0], loop = true, motion = &"idle"},
	&"summon": {sheet = REDESIGN_SHEET, frames = [1], times = [0.8], loop = false, motion = &"summon"},
	&"summon_pop": {sheet = REDESIGN_SHEET, frames = [1], times = [0.42], loop = false},
	# The fist-pump, not the idle, so the punish window has a look of its own. He is celebrating with
	# his arm in the air and his front wide open, and the fist coming down is the window closing: on
	# frame 0 the taunt and the idle he drops into after it would look the same.
	&"taunt": {sheet = REDESIGN_SHEET, frames = [1], times = [1.0], loop = true, motion = &"taunt"},
	&"hit": {sheet = REDESIGN_SHEET, frames = [0], times = [0.22], loop = false},
	# His idle keeled over by the `defeated` clip.
	&"defeat": {sheet = REDESIGN_SHEET, frames = [0], times = [1.0], loop = false, motion = &"defeated"},
	# His idle, standing: the redesign has no kneel.
	&"broken": {sheet = REDESIGN_SHEET, frames = [0], times = [1.0], loop = true},
}

# The artist's timings, except the summon's wind-up.
const FINAL_ANIMS := {
	&"idle": {sheet = "res://Assets/Characters/Jordan/jordan_idle.png",
		frames = [0, 1, 2, 3], times = [0.2, 0.16, 0.2, 0.16], loop = true},
	# The crouch and the punch up. The artist holds the crouch 0.3 s, but the figures pop in at
	# JordanStateMachine.SUMMON_WINDUP and the telegraph stays that long, so the crouch is held until
	# these two add up to it. A spawn a frame late only holds the punch up a frame longer.
	&"summon": {sheet = "res://Assets/Characters/Jordan/jordan_summon.png",
		frames = [0, 1], times = [0.72, 0.08], loop = false},
	# The pop and the "yes!", played by SummonFunkos on the frame the figures pop in, so it lands on them
	# whatever the frame timing. It plays on over the start of the taunt, which waits for it.
	&"summon_pop": {sheet = "res://Assets/Characters/Jordan/jordan_summon.png",
		frames = [2, 3], times = [0.26, 0.16], loop = false},
	# The box hoisted overhead, laughing.
	&"taunt": {sheet = "res://Assets/Characters/Jordan/jordan_taunt.png",
		frames = [0, 1, 2, 3], times = [0.13, 0.11, 0.13, 0.11], loop = true},
	# In the idle stance, so a hit on the taunt brings the box down from overhead for its 0.22 s.
	&"hit": {sheet = "res://Assets/Characters/Jordan/jordan_hit.png",
		frames = [0, 1], times = [0.08, 0.14], loop = false},
	# Down on one knee by the box he dropped. Never advances past frame 5, and he never vanishes.
	&"defeat": {sheet = "res://Assets/Characters/Jordan/jordan_defeat.png",
		frames = [0, 1, 2, 3, 4, 5], times = [0.14, 0.12, 0.10, 0.14, 0.20, 1.0], loop = false},
	# A Break: the defeat's kneel by the fallen box, held. There is no Broken art of his own.
	&"broken": {sheet = "res://Assets/Characters/Jordan/jordan_defeat.png",
		frames = [4], times = [1.0], loop = true},
}

#JUGGLED (JordanJuggled, a BossJuggled, under the tiered finisher's uppercuts)
# jordan_juggle.png: 12 frames of 192x144 with his soles on row 143, the artist's. The hit 0-1, a tumble
# looping 2-6 that opens on a hang at the apex, the crash 7-9, and him lying 10-11. ITS FRAME IS NOT HIS
# MAIN SHEET'S: offset (0, -72) stands row 143 on the floor point as SPRITE_OFFSET stands row 95, and
# BossJuggled.texel_point() measures it, never frame_local(). Timings are the artist's.
const USE_FINAL_JUGGLE := true
const FINAL_JUGGLE := {
	"texture": "res://Assets/Characters/Jordan/jordan_juggle.png",
	"hframes": 12,
	"frame_size": Vector2(192, 144),
	"offset": Vector2(0, -72),
	"feet": Vector2(96, 143),
	# The middle of him in the air, which the finisher's camera follows.
	"tumble_centre": Vector2(96, 93),
	# The highest row anything is drawn on while he's in the air.
	"top_row": 40,
	"clips": {
		&"launch": {"frames": [0, 1], "times": [0.06, 0.08], "loop": false},
		&"tumble": {"frames": [2, 3, 4, 5, 6], "times": [0.14, 0.07, 0.07, 0.07, 0.07], "loop": true},
		&"crash": {"frames": [7, 8, 9], "times": [0.06, 0.08, 0.12], "loop": false},
		&"down": {"frames": [10, 11], "times": [0.4, 0.4], "loop": true},
	},
	"shadow": {
		"texture": "res://Assets/Characters/Jordan/jordan_leap_shadow.png",
		"hframes": 3, "scale": 3.0, "alpha": 0.35, "step": 100.0, "offset": Vector2.ZERO,
	},
	"lying_time": 0.3,
	"outro_delay": 1.8,
	"crash_sfx": {"stream": "res://Assets/Audio/SFX/hit_impact.ogg", "pitch": 0.7, "volume_db": 0.0},
}


static func juggle() -> Dictionary:
	return FINAL_JUGGLE


static func anim(anim_name: StringName) -> Dictionary:
	if USE_FINAL_ANIMS.get(anim_name, false):
		return FINAL_ANIMS[anim_name]
	return PLACEHOLDER_ANIMS[anim_name]


# Position in his BODY space, in px, of a point on his frames: the scaling is on his sprite, so it is
# already applied here.
static func frame_local(point: Vector2) -> Vector2:
	return (point - FRAME_SIZE / 2.0 + SPRITE_OFFSET) * SCALE + FLOOR_POINT


static func local_rect(rect: Rect2) -> Rect2:
	return Rect2(frame_local(rect.position), rect.size * SCALE)


static func daze_anchor() -> Vector2:
	return frame_local(TAUNT_CROWN) + Vector2(0, -DAZE_GAP)


static func broken_daze_anchor() -> Vector2:
	return frame_local(BROKEN_CROWN) + Vector2(0, -DAZE_GAP)


static func tell_anchor() -> Vector2:
	return frame_local(WINDUP_CROWN) + Vector2(0, -TELL_GAP)
