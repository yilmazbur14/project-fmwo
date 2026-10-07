extends RefCounted

# Every number that depends on how Mason is drawn, so a redraw at a new frame size only needs this
# file. Points are in texels on a frame, origin top-left. MasonScript and his states apply them at
# runtime; the values in MasonScene are copies for the editor.
#
# His transform is the opposite of Eric's: his CharacterBody2D is at scale 1 and the 3x lives on his
# Sprite2D. So frame_local() below returns BODY-LOCAL PIXELS, not texels, and nothing may multiply
# its result by SCALE again.

const SCALE := 3.0

#MASON SHEET (mason_sheet.png)
const FRAME_SIZE := Vector2(64, 64)
const SHEET_FRAMES := 19
# Sprite2D.offset in MasonScene: where the frames are drawn relative to his origin, in texels.
const SPRITE_OFFSET := Vector2(0, -32)
# Sprite2D.position in MasonScene, in body px: where his fight y-sorts him, the row his feet stand on.
const SORT_POINT := Vector2(0, 96)
# The row his feet stand on. A flying Mason's shadow is measured from it.
const FEET_ROW := 63.0
# Bottom middle of him, under his feet.
const FEET_PIXEL := Vector2(32, FEET_ROW)

#BROKEN (MasonBroken, a full Break gauge)
# mason_broken.png, when it is drawn: he drops, winded and open, and slumps in a loop. Its dictionary
# takes the same keys as the placeholder plus "texture" and "hframes", and may add "head" and "heads"
# (frame pixels just above his head, where the daze stars circle) once the frames are known. It has no
# "sword": Mason has nothing to drop.
# The placeholder loops his defeated frames 13-14, where he is already down and beaten.
# mason_broken.png (the Nugget Fastball plan, section 3D; shipped 2026-10-04, art_source/mason_pitch/contract.json):
# 7 frames on mason_sheet's canvas. The knockdown 0-3 (reel, totter, sit, bounce) once, then sitting dazed 4-5 in a
# loop; 6 is a twitch the loop doesn't use. It is every Break's pose, the home run's knockdown or not. "heads" are the
# contract's points just over his comb, each less half a texel: MasonBroken reads them through frame_point, which
# adds the half back.
const USE_FINAL_BROKEN := true
const FINAL_BROKEN := {
	"texture": "res://Assets/Characters/Mason/mason_broken.png",
	"hframes": 7,
	"intro": &"broken_knockdown_final",
	"loop": &"broken_dazed_final",
	"intro_frames": [0, 1, 2, 3],
	"intro_times": [0.10, 0.12, 0.14, 0.12],
	"loop_frames": [4, 5],
	"loop_time": 0.35,
	"heads": {0: Vector2(36.0, -2.5), 1: Vector2(26.0, -2.5), 2: Vector2(31.0, 10.5), 3: Vector2(31.0, 6.5),
		4: Vector2(27.0, 10.5), 5: Vector2(35.0, 10.5), 6: Vector2(31.0, 9.5)},
}
const PLACEHOLDER_BROKEN := {"intro": &"", "loop": &"broken"}

#THE PITCH (MasonPitch, the Nugget Fastball)
# mason_pitch.png (shipped 2026-10-04; art_source/mason_pitch/contract.json is the source of truth): 15 frames on
# mason_sheet's canvas (64x64, feet on row 63 at x 32), drawn throwing toward screen-left; the code mirrors it for a
# player on his right. "frames" names the pose each beat shows, "bonk" the three frames a home run's bonk steps
# through on "bonk_times" (they draw no nugget: the bonk's own burst is it breaking up). Anchors are the contract's
# points on an unflipped frame (pitch_local mirrors them, x to 64 - x), one for every frame or a {frame: point}:
# "tell" the badge's and the X's bottom tip, beside him at body +(150, 10) (over his comb it would sit under the boss
# bar at his home spot); "release_hand" where the ball spawns; "hand" the cocked nugget the bite's glow sits on;
# "head_hit" the forehead a home run strikes.
const USE_FINAL_PITCH := true
const FINAL_PITCH := {
	"texture": "res://Assets/Characters/Mason/mason_pitch.png",
	"hframes": 15,
	"frames": {&"ready": 0, &"stretch": 1, &"kick": 2, &"set": 3, &"release": 4, &"follow": 5, &"pump": 6,
		&"pump_hold": 7, &"change_a": 8, &"change_b": 9, &"change_set": 10, &"change_release": 11},
	"bonk": [12, 13, 14],
	"bonk_times": [0.12, 0.15, 0.18],
	"tell": Vector2(82.0, 35.0 + 1.0 / 3.0),
	"release_hand": {4: Vector2(10.5, 56.5), 11: Vector2(11.5, 36.5)},
	"hand": {3: Vector2(53.5, 7.0), 6: Vector2(23.5, 51.5), 7: Vector2(54.5, 27.0)},
	"head_hit": {0: Vector2(32.5, 11.0), 1: Vector2(31.5, 11.0), 2: Vector2(33.5, 11.0), 3: Vector2(34.5, 11.0),
		4: Vector2(26.5, 16.0), 5: Vector2(23.5, 19.0), 6: Vector2(26.5, 16.0), 7: Vector2(32.5, 11.0),
		8: Vector2(38.5, 11.0), 9: Vector2(25.5, 12.0), 10: Vector2(33.5, 11.0), 11: Vector2(29.5, 13.0),
		12: Vector2(37.5, 12.0), 13: Vector2(26.5, 14.0), 14: Vector2(31.5, 11.0)},
}
# On mason_sheet's own frames. Its frames face the viewer, so the changeup's rock reads as a light-blue pulse on
# him instead of a silhouette, and the badge stands on the daze anchor (no "tell").
const PLACEHOLDER_PITCH := {
	"frames": {&"ready": 0, &"stretch": 1, &"kick": 16, &"set": 17, &"release": 18, &"follow": 0, &"pump": 17,
		&"pump_hold": 17, &"change_a": 0, &"change_b": 1, &"change_set": 16, &"change_release": 18},
	"bonk": [12, 12, 12],
	"bonk_times": [0.12, 0.15, 0.18],
	"release_hand": Vector2(10.5, 56.5),
	"hand": Vector2(56.5, 12.5),
	"head_hit": Vector2(32.5, 14.5),
	"changeup_pulse": {"color": Color(0.65, 0.85, 1.4), "time": 0.20},
}
# The badge's top stays this far inside the view: the strong badge stands 108 px over its tip.
const TELL_TOP_MARGIN := 4.0
const TELL_BADGE_HEIGHT := 108.0
const VIEW_RECT := Rect2(0, 0, 1920, 1080)

# The ball (MasonPitchBall), drawn at SCALE and never rotated, on the scheme that shipped ("spin_streaks"): the
# nugget's own spin on nugget_fastball.png, centred, and under it a streak sheet of `directions` headings (e, se, s,
# sw, w, nw, n, ne), frame = direction * 2 + flicker. The changeup is the same nugget at half the spin rate over its own
# trail. The hit radius is the drawn nugget's half-size (6.5 texels, 19.5 px; the artist's 18), on any art.
const BALL_RADIUS := 18.0
const USE_FINAL_BALL := true
const FINAL_BALL := {
	&"fastball": {"scheme": &"spin_streaks", "texture": "res://Assets/Characters/Mason/nugget_fastball.png", "hframes": 4,
		"frame_time": 0.05, "streaks": "res://Assets/Characters/Mason/nugget_fastball_streaks.png",
		"directions": 8, "frames_per_direction": 2, "streak_time": 0.06},
	&"changeup": {"scheme": &"spin_streaks", "texture": "res://Assets/Characters/Mason/nugget_fastball.png", "hframes": 4,
		"frame_time": 0.10, "streaks": "res://Assets/Characters/Mason/nugget_changeup_trail.png",
		"directions": 8, "frames_per_direction": 2, "streak_time": 0.11},
}
# Cream puffs left behind the changeup as it floats, one every PUFF_EVERY, each played once where it was left.
const USE_FINAL_PUFF := true
const FINAL_PUFF := {"texture": "res://Assets/Characters/Mason/nugget_puff.png", "hframes": 3, "scale": SCALE, "frame_time": 0.07}
const PUFF_EVERY := 0.06
const PLACEHOLDER_BALL := {"scheme": &"placeholder", "body": Vector2(11, 8) * SCALE / 2.0,
	"fill": Color(0.83, 0.6, 0.25), "rim": Color(0.25, 0.13, 0.05), "rim_width": 3.0,
	"streak": Color(1.0, 0.95, 0.7, 0.85), "streak_length": 60.0, "streak_width": 8.0,
	"trail": Color(1.0, 0.92, 0.6, 0.55), "trail_width": 6.0, "trail_fade": 0.15}
# The quick pitch is the fastball's art, white-hot; the home run's return is the fastball's, parry-tinted
# (DefenseHypeArtLayout.PARRY_FLASH[0], Eric's reflected sword).
const QUICK_TINT := Color(2.2, 2.1, 1.9)
# How long a missed ball flies on before it is gone, fading.
const BALL_FADE := 0.15

# HOME RUN! (gold, the KNIGHT BREAKER! recipe; the user's pick 2026-10-04) beside his head on the ring-centre side,
# with three streak pips under it. Pivot at its bottom centre; the placeholder is the word in the HUD font.
const USE_FINAL_HOME_RUN := true
const FINAL_HOME_RUN := {"texture": "res://Assets/Characters/Mason/home_run.png", "hframes": 6, "scale": SCALE,
	"frame_size": Vector2(128, 40), "frame_times": [0.05, 0.06, 0.06, 0.30, 0.06, 0.06]}
const PLACEHOLDER_HOME_RUN := {"text": "HOME RUN!", "font_size": 66, "color": Color(1.0, 0.82, 0.2), "outline": 10,
	"box": Vector2(400, 90)}
const HOME_RUN_TIME := 0.9
# A word's near edge stands this far from his middle: his drawn half-width (93 px) and a gap, so it never covers him.
const WORD_BESIDE := 113.0
const USE_FINAL_HOME_RUN_PIPS := true
const FINAL_HOME_RUN_PIPS := {"texture": "res://Assets/Characters/Mason/home_run_pips.png", "hframes": 2, "scale": SCALE}
const PLACEHOLDER_HOME_RUN_PIPS := {"radius": 10.0, "gap": 30.0, "empty": Color(0.2, 0.2, 0.2, 0.8),
	"filled": Color(1.0, 1.0, 1.0), "rim": Color(0, 0, 0)}

# The bonk on HEAD_HIT: the returned nugget bursting into crumbs, a flash star and two cartoon stars. The placeholder
# is a code-drawn star.
const USE_FINAL_BONK := true
const FINAL_BONK := {"texture": "res://Assets/Characters/Mason/nugget_bonk.png", "hframes": 5, "scale": SCALE,
	"frame_time": 0.06}
const PLACEHOLDER_BONK := {"points": 8, "outer": 34.0, "inner": 14.0, "color": Color(1.0, 0.95, 0.55), "time": 0.3}

# A hesitation's pale X: Carter's demon_feint.png as it ships, stepped through ignite and peak to its hold, never
# pulsing or tinted (copied from JoshMonteLayout, with no dependency on Josh's file).
const FEINT_MARK := {texture = "res://Assets/Characters/Carter/Demon/demon_feint.png", hframes = 4,
	frame_size = Vector2(24, 24), pivot = Vector2(12, 12), scale = 3.0, steps = {ignite = 0, peak = 1, hold = 2, fade = 3},
	ignite_time = 0.05, peak_time = 0.04}
const FEINT_RING := {radius = 46.0, width = 11.0, points = 20, color = Color(1.0, 0.85, 0.15)}
const MARK_OUT := 0.05
# A bitten hesitation: his hand burns white, beating (Josh's punish look), until the quick pitch leaves it.
const QUICK_GLOW := {glow = Color(1.0, 1.0, 1.0, 0.55), glow_radius = 36.0, points = 24, beat = [0.82, 1.18],
	beat_time = 0.07}
# FEINT! (Josh's), and HOME RUN!'s placement rules: in view and HUD_CLEARANCE clear of the HUD blocks
# (CarterArtLayout.HUD_KEEP_OUT's rects).
const WORD := {centre = Vector2(960, 300), time = 0.9, font_size = 92, color = Color(1.0, 0.36, 0.3), outline = 10,
	from_scale = 0.7, to_scale = 1.0, grow_time = 0.16, box = Vector2(300, 100)}
const HUD_KEEP_OUT: Array[Rect2] = [
	Rect2(720, 33, 480, 148),
	Rect2(10, 842, 406, 229),
	Rect2(1371, 946, 537, 126),
]
const HUD_CLEARANCE := 12.0

# Stand-ins on the fight's existing streams until the sound pass.
const PITCH_SFX := {
	&"windup": {"stream": "res://Assets/Audio/SFX/wrestler_charge.ogg", "pitch": 1.2, "volume_db": -12.0},
	&"release": {"stream": "res://Assets/Audio/SFX/whirlwind_whoosh.ogg", "pitch": 1.4, "volume_db": -4.0},
	&"changeup": {"stream": "res://Assets/Audio/SFX/whirlwind_whoosh.ogg", "pitch": 0.7, "volume_db": -4.0},
	&"bonk": {"stream": "res://Assets/Audio/SFX/hit_impact.ogg", "pitch": 1.3, "volume_db": 0.0},
}

#JUGGLED (MasonJuggled, under the tiered finisher's uppercuts)
# mason_juggle.png: 12 frames of 128x96, feet at (64, 95). The hit 0-1; a tumble looping 2-6 that opens
# on a long hang at the apex and then spins; the crash 7-9; and him lying breathing 10-11.
# ITS FRAME IS NOT HIS MAIN SHEET'S. 128x96 against 64x64, so the sprite has to hang 16 texels lower
# (offset -48 against -32) to keep his feet on the same ground line, and every point on it is measured
# through juggle_local() rather than frame_local(). What makes that easy to get wrong: his
# CharacterBody2D's origin is his middle, not his feet, which are 94.5 px below it.
# The placeholder threw his hit frame around his waddle frames on the main sheet, so it names no frame
# or offset of its own and falls back to that sheet's, and its top_row counts the whole frame as him.
const USE_FINAL_JUGGLE := true
const FINAL_JUGGLE := {
	"texture": "res://Assets/Characters/Mason/mason_juggle.png",
	"hframes": 12,
	"frame_size": Vector2(128, 96),
	"offset": Vector2(0, -48),
	"feet": Vector2(64, 95),
	# The middle of him in the air, which the finisher's camera follows.
	"tumble_centre": Vector2(64, 52),
	# The highest row anything is drawn on while he's in the air, so his top is this far over his
	# ground line when he isn't lifted.
	"top_row": 9,
	"launch": &"juggle_hit_final",
	"tumble": &"juggle_tumble_final",
	"crash": &"juggle_crash_final",
	"down": &"juggle_down_final",
}
const PLACEHOLDER_JUGGLE := {
	"launch": &"juggle_hit",
	"tumble": &"juggle_tumble",
	"crash": &"juggle_crash",
	"down": &"juggle_down",
	"feet": FEET_PIXEL,
	"tumble_centre": Vector2(32, 36),
	"top_row": 0,
}
# The whole of him stays at least this far below the top of the arena at the top of his flight: the
# finisher scales the juggle's heights down to fit (juggle_headroom).
const JUGGLE_TOP_MARGIN := 12.0
# His shadow on the mat while he's in the air: frame `lift / step` (0 low, 2 high), under his feet. The
# ellipses are drawn solid black; the alpha here is what makes them a shadow.
const JUGGLE_SHADOW := {
	"texture": "res://Assets/Characters/Mason/mason_leap_shadow.png",
	"hframes": 3,
	"scale": 3.0,
	"alpha": 0.35,
	"step": 100.0,
}
# The mark a Knight Breaker crash leaves on the floor. Gated by presence rather than a flag: there is
# no Mason crater art, so this is empty and MasonJuggled skips it. When there is one it takes the same
# keys as EricArtLayout.CRASH_CRATER.
const CRASH_CRATER := {}
# Lying after the crash, before he gets up.
const JUGGLE_LYING_TIME := 0.3
# A juggle that kills him holds the outro's first line this long, so the line does not start over him
# while he is still in the air. Eric's is 1.8 for the same reason; the fall is the finisher's own arc
# and is the dominant term, so his number carries. Mason's crash clip is 0.26 against Eric's 0.30, so
# this has 0.04 more margin than Eric's does rather than less.
const JUGGLE_OUTRO_DELAY := 1.8
# Every crash, whatever the tier: the fight's own impact, pitched down so it reads as weight.
const CRASH_THUD_SFX := {"stream": "res://Assets/Audio/SFX/hit_impact.ogg", "pitch": 0.7, "volume_db": 0.0}

#BREAK (MasonBroken's Break frame)
# The Break's sting, on the Break frame. Its level is baked in.
const BREAK_STING_SFX := [
	{"stream": "res://Assets/Audio/SFX/break_sting.wav", "pitch": 1.0, "volume_db": 0.0},
]

#THE FRY TRAIL (MasonIntro)
# The fries on the floor he is lured into the ring along: one dropped piece per stop he makes on the
# way in, each one left as crumbs once he has reached it.
#
# fry_trail.png: 7 frames of 32x16, drawn at SCALE, in his own six measured colours over his
# pure-black keyline. EVERY PIECE IS CENTRED ON TEXEL (16, 8), so a plain centred Sprite2D drops one
# on the floor point it is given and there is no pivot to keep in step with a redraw. flip_h doubles
# the sheet and is safe; flip_v is not - it puts the drawn contact edge on the far side of the piece
# and it stops sitting on the floor. Its source, and the round-trip check for it, are in
# art_source/mason_intro/.
#   0 one bent fry, the workhorse      3 three and crumbs, a dropped handful
#   1 one steeper, shorter fry         4 one fry in a ketchup drag, the accent
#   2 two crossed, a small drop        5, 6 the residues (FRY_EATEN)
const USE_FINAL_FRY_TRAIL := true
const FINAL_FRY_TRAIL := {
	"texture": "res://Assets/Characters/Mason/fry_trail.png",
	"hframes": 7,
	"scale": SCALE,
}
# The stand-in the beat was built and timed on, before the sheet landed: one piece is a blob of
# ketchup with loose sticks fanned over it, in the same palette. Its sticks are half the drawn ones'
# length, so a trail built from it sits closer together than the numbers below are set for.
# `at` is where a stick sits in the piece and `turn` how far it is rolled over, in turns.
const PLACEHOLDER_FRY_TRAIL := {
	"fry": Vector2(3, 11),
	"tip": Vector2(3, 3),
	"ketchup": Vector2(9, 4),
	"keyline": Color(0, 0, 0),
	"fry_color": Color(0.83137256, 0.8, 0.18039216),
	"tip_color": Color(0.627451, 0.5647059, 0.3137255),
	"ketchup_color": Color(0.6745098, 0.19607843, 0.19607843),
	"scale": SCALE,
	"fries": [
		{"at": Vector2(-4, -1), "turn": -0.16},
		{"at": Vector2(3, -3), "turn": 0.09},
		{"at": Vector2(0, 2), "turn": 0.31},
	],
}
# What a piece becomes once he has eaten it. NOTHING IS EVER TAKEN OFF THE FLOOR: bare mat behind him
# reads as a trail that was always shorter, not one he ate, so the line has to visibly turn to crumbs
# rather than empty. The residues are deliberately quiet - broken bits and crumbs, nothing more - so
# the eye stays on him and on the fries still ahead of him.
const FRY_EATEN := {0: 5, 1: 5, 2: 6, 3: 6, 4: 6}
# The line the pieces sit on, one entry per stop he makes, in order from the far end to his mark:
#   across  px off the centre line, so the trail reads as dropped rather than laid out. He walks to
#           each piece, so it is his weave as well. It stays well inside the 216 px rope doorway
#           (screen x 852..1068) both fighters come through, and the last one is 0 because he has to
#           finish on his mark.
#   frame   which piece of the sheet is dropped here.
#   flip    drawn mirrored (flip_h only, see above).
#
# THE FRAMES ARE NOT IN AN ARBITRARY ORDER. The trail runs down the screen and the pieces are drawn
# in landscape frames, so two tall ones on neighbouring stops touch. Drawn heights are 9, 14, 15, 16
# and 11 texels for frames 0-4, which at this spacing (FRY_TRAIL_SPAN over these stops, 46 px) makes
# 1-3 and 2-3 the pairs that collide: every tall piece here has a short one either side of it.
# Frame 4 is the accent and goes in ONCE. Five yellow stamps in a row on a green mat is a dotted
# line; one red one in the middle of them is a trail.
const FRY_TRAIL := [
	{"across": 15.0, "frame": 3, "flip": false},
	{"across": -21.0, "frame": 0, "flip": false},
	{"across": 8.0, "frame": 2, "flip": true},
	{"across": -13.0, "frame": 0, "flip": true},
	{"across": 19.0, "frame": 4, "flip": false},
	{"across": 0.0, "frame": 1, "flip": false},
]
# How much of his walk in has fries on it: the last FRY_TRAIL_SPAN px of it, with the stops spread
# evenly over them.
#
# THE SPAN IS NOT HIS WHOLE WALK IN (MasonIntro.WALK_IN_RISE), and must stay under it. He fights from
# the top of the ring, so there are only about 260 px of mat between the top rope and his mark: a
# trail any longer than that has its far end out over the crowd band, where a piece is drawn against
# the crowd rather than the floor and the gobble that takes it can't be seen. The span is what is on
# the mat, and the rest of his walk in is the approach he makes to the first piece.
const FRY_TRAIL_SPAN := 276.0
# A stand-in until a gobble has a sound of its own: the fight's own impact, pitched up and dropped to
# where it reads as a bite rather than a hit.
const INTRO_SFX := {
	"gobble": {"stream": "res://Assets/Audio/SFX/hit_impact.ogg", "pitch": 1.75, "volume_db": -17.0},
}


static func broken() -> Dictionary:
	return FINAL_BROKEN if USE_FINAL_BROKEN and ResourceLoader.exists(FINAL_BROKEN.texture) else PLACEHOLDER_BROKEN


# His knockdown and dazed loop on mason_broken.png, added to his library once (PlayerPunching's pattern) when the
# sheet is there: MasonBroken plays whatever broken() names and needs nothing else.
static func build_broken_animations(ap: AnimationPlayer) -> void:
	var library := ap.get_animation_library(&"")
	var art: Dictionary = FINAL_BROKEN
	if not library.has_animation(art.intro):
		var times: Array = art.intro_times
		var intro := Animation.new()
		var track := intro.add_track(Animation.TYPE_VALUE)
		intro.track_set_path(track, ^"Sprite2D:frame")
		intro.value_track_set_update_mode(track, Animation.UPDATE_DISCRETE)
		var at := 0.0
		for i in art.intro_frames.size():
			intro.track_insert_key(track, at, art.intro_frames[i])
			at += times[i]
		intro.length = at
		library.add_animation(art.intro, intro)
	if not library.has_animation(art.loop):
		var loop := Animation.new()
		var track := loop.add_track(Animation.TYPE_VALUE)
		loop.track_set_path(track, ^"Sprite2D:frame")
		loop.value_track_set_update_mode(track, Animation.UPDATE_DISCRETE)
		for i in art.loop_frames.size():
			loop.track_insert_key(track, i * art.loop_time, art.loop_frames[i])
		loop.length = art.loop_frames.size() * art.loop_time
		loop.loop_mode = Animation.LOOP_LINEAR
		library.add_animation(art.loop, loop)


static func pitch() -> Dictionary:
	return FINAL_PITCH if USE_FINAL_PITCH and ResourceLoader.exists(FINAL_PITCH.texture) else PLACEHOLDER_PITCH


# The texel an anchor of pitch() names on `frame`, or null when that art has none.
static func pitch_anchor(anchor: String, frame: int) -> Variant:
	var spot: Variant = pitch().get(anchor)
	if spot is Dictionary:
		return spot.get(frame)
	return spot


# Body-local px of a point on a pitch frame (the contract's points, not texel indices), mirrored for a sheet drawn
# flipped: a point at x is at 64 - x on the mirrored frame.
static func pitch_local(point: Vector2, flipped: bool) -> Vector2:
	if flipped:
		point.x = FRAME_SIZE.x - point.x
	return frame_local(point)


# What draws a ball of `kind` (&"fastball", &"changeup"; the quick pitch is the fastball's): its nugget and its
# streak sheet once both are in, else the code-drawn stand-in.
static func ball(kind: StringName) -> Dictionary:
	var art: Dictionary = FINAL_BALL[&"changeup" if kind == &"changeup" else &"fastball"]
	if USE_FINAL_BALL and ResourceLoader.exists(art.streaks) and ResourceLoader.exists(art.texture):
		return art
	return PLACEHOLDER_BALL


static func puff() -> Dictionary:
	return FINAL_PUFF if USE_FINAL_PUFF and ResourceLoader.exists(FINAL_PUFF.texture) else {}


# The streak sheet's streak direction for `heading`: 0 e, 1 se, 2 s ... 7 ne, clockwise on screen.
static func streak_direction(heading: Vector2, directions: int) -> int:
	return posmod(roundi(heading.angle() / (TAU / directions)), directions)


static func home_run() -> Dictionary:
	return FINAL_HOME_RUN if USE_FINAL_HOME_RUN and ResourceLoader.exists(FINAL_HOME_RUN.texture) else PLACEHOLDER_HOME_RUN


static func home_run_pips() -> Dictionary:
	return FINAL_HOME_RUN_PIPS if USE_FINAL_HOME_RUN_PIPS and ResourceLoader.exists(FINAL_HOME_RUN_PIPS.texture) else PLACEHOLDER_HOME_RUN_PIPS


static func bonk() -> Dictionary:
	return FINAL_BONK if USE_FINAL_BONK and ResourceLoader.exists(FINAL_BONK.texture) else PLACEHOLDER_BONK


# The X once it is there; empty for the ring.
static func feint_mark() -> Dictionary:
	return FEINT_MARK if ResourceLoader.exists(FEINT_MARK.texture) else {}


# `box` centred on `centre`, moved the least way into the view and HUD_CLEARANCE clear of every HUD block: down
# out of the boss bar, up out of the bottom corners.
static func clear_of_hud(centre: Vector2, box: Vector2) -> Vector2:
	var view := VIEW_RECT.grow(-HUD_CLEARANCE)
	var at := centre.clamp(view.position + box / 2.0, view.end - box / 2.0)
	for block in HUD_KEEP_OUT:
		var grown := block.grow(HUD_CLEARANCE)
		if not grown.intersects(Rect2(at - box / 2.0, box)):
			continue
		if grown.get_center().y < VIEW_RECT.get_center().y:
			at.y = grown.end.y + box.y / 2.0
		else:
			at.y = grown.position.y - box.y / 2.0
	return at


static func juggle() -> Dictionary:
	return FINAL_JUGGLE if USE_FINAL_JUGGLE else PLACEHOLDER_JUGGLE


static func crash_crater() -> Dictionary:
	return CRASH_CRATER


# Position in Mason's BODY space, in px, of a point on his frames: the scaling is on his sprite, so it
# is already applied here.
static func frame_local(point: Vector2) -> Vector2:
	return (point - FRAME_SIZE / 2.0 + SPRITE_OFFSET) * SCALE + SORT_POINT


# The same, for a point on the juggle sheet, whose frames are a different size and hang at a different
# offset. Both put his feet on the same body-local row, so a ground line read off either agrees.
static func juggle_local(point: Vector2) -> Vector2:
	var art := juggle()
	var size: Vector2 = art.get("frame_size", FRAME_SIZE)
	var offset: Vector2 = art.get("offset", SPRITE_OFFSET)
	return (point - size / 2.0 + offset) * SCALE + SORT_POINT
