extends RefCounted

# Jordan's attack 1, Greyson + Matt's dark maze (JordanComboMaze): every number and rule it plays on, so a retune only
# needs this file. The user's own design and sketch (2026-09-28), snapped to a grid of floor blocks.
#
# THE GRID: block (c, r) is BLOCK px (32x20 texels, a 3/4 floor tile), rows counting up the screen. Its soles point -
# its centre, where a player standing on it has their soles - is ORIGIN + (96c, -60r). The player's origin stands
# SOLES_OVER_ORIGIN over their soles (MainPlayer's collision box).
#
# THE ROUTE is new every time the attack starts (the user, 2026-09-28: "the same amount of blocks to move each time, but
# the path should be randomized"): ROUTE_STEPS unit steps from START, bottom centre, to GOAL, under Greyson, drawn off
# the maze's rng (generate()). Every route keeps route_problems()'s rules:
#   - a self-avoiding walk of exactly ROUTE_STEPS steps from START to GOAL, the goal only at its end;
#   - inside ROUTE_COLUMNS x ROUTE_ROWS, which keeps it off the back glass's row and keeps it and its walls inside the
#     floor, clear of the player's HUD in the bottom corners and below Jordan's mask and core (jordan_face());
#   - the corridor never touches itself: two cells of it that aren't neighbours along it are never side by side, and
#     unless DIAGONAL_CONTACT, not corner to corner either except across one of its own turns, so there is always a
#     wall between two runs of it, as in the drawn path;
#   - no wall lands on NO_WALL, Matt's footprint (Greyson's cell and the back glass are never walls by the wall rule).
# ROUTE_TRIES searches of ROUTE_BUDGET moves each find one; should they all fail, DRAWN_PATH stands in: the sketch's
# corridor (up 1, right 2, up 4, left 6, up 2, right 3) re-snapped to this grid's goal in the same 18 steps (up 1,
# right 2, up 5, left 6, up 2, right 2). The arrow on each block is the step off it, so there is one fewer arrow than
# there are blocks. BACK_GLASS, the block under the start, is glass from the start, so a wrong first press lands on
# glass too.
#
# THE WALLS are purely visual, and the arrow is the answer: a wrong press is any direction but the arrow's, which
# covers stepping into a wall. Every block that touches the route (8-adjacent) and is not on it is a wall, except
# Greyson's, the goal's open top edge, and the back glass. The upper corridors are flatter than the sketch's: Greyson
# is 258 px tall and his meter sits over his head.
#
# STAGING is the user's option B (2026-09-28, art_source/jordan_puppeteer/staging/staging.json): the fight is viewed at
# 2/3 (JordanGodLayout.VIEW_ZOOM) and the maze keeps its world scale, 96x60 blocks and 3x sprites, well below Jordan
# with his puppets hanging between: Greyson one block over the goal, two left of centre, and Matt off to the right,
# where his yell's ring stays clear of Greyson. Every px here is world px. Greyson's meter is world-space UI, grown by
# the fight's ui_scale() to read at its own size.

const GodLayout := preload("res://Scripts/JordanGodLayout.gd")
const GreysonArtLayout := preload("res://Scripts/GreysonArtLayout.gd")

const SCALE := 3.0

#THE GRID (px)
const BLOCK := Vector2(96, 60)
const ORIGIN := Vector2(960, 1410)
const SOLES_OVER_ORIGIN := 42.0
const START := Vector2i(0, 0)
const GOAL := Vector2i(-2, 8)
const BACK_GLASS := Vector2i(0, -1)
const GREYSON_CELL := Vector2i(-2, 9)
# DirectionPress's names, and the step each takes on the grid.
const STEPS := {&"up": Vector2i(0, 1), &"right": Vector2i(1, 0), &"down": Vector2i(0, -1), &"left": Vector2i(-1, 0)}

#THE ROUTE
const ROUTE_STEPS := 18
const ROUTE_COLUMNS := Vector2i(-5, 4)
const ROUTE_ROWS := Vector2i(0, 8)
const DIAGONAL_CONTACT := false
# Matt's cells, his feet and either side of them, on his row.
const NO_WALL: Array[Vector2i] = [Vector2i(3, 9), Vector2i(4, 9), Vector2i(5, 9)]
const ROUTE_TRIES := 5
const ROUTE_BUDGET := 20000
# His mask and his chest core, which nothing of the maze may reach: texels on his 320x224 frame, placed as he is
# drawn (jordan_face()), since his size and point are his own knobs.
const JORDAN_MASK_TEXELS := Rect2(144, 86, 32, 23)
const JORDAN_CORE_TEXELS := Rect2(152, 113, 16, 19)
# The sketch's corridor on this grid: the fallback, and what a test pins to play the user's own drawing.
const DRAWN_PATH: Array[Vector2i] = [
	Vector2i(0, 0), Vector2i(0, 1), Vector2i(1, 1), Vector2i(2, 1), Vector2i(2, 2), Vector2i(2, 3), Vector2i(2, 4),
	Vector2i(2, 5), Vector2i(2, 6), Vector2i(1, 6), Vector2i(0, 6), Vector2i(-1, 6), Vector2i(-2, 6), Vector2i(-3, 6),
	Vector2i(-4, 6), Vector2i(-4, 7), Vector2i(-4, 8), Vector2i(-3, 8), Vector2i(-2, 8),
]

#THE PAIR (feet, px)
# Greyson in the goal's open top edge facing down, on Jordan's left hand; Matt off to the right facing left, on his
# right.
const GREYSON_FEET := Vector2(768, 870)
const MATT_FEET := Vector2(1344, 870)
# Greyson's meter centred over his head: its bottom edge METER_GAP screen px over his crown, which is GREYSON_CROWN
# px over his feet (the design sheet's crown row, 26).
const GREYSON_CROWN := 258.0
const METER_GAP := 12.0

#THE BEATS (seconds)
# Jordan's flick as the player is warped to the start.
const TELEPORT_TIME := 0.35
# The walls rise on Jordan's second yank (his summon's rise beat, JordanGodLayout.summon_beats), rippling out from the
# start, one block this long after the one before it, nearest first; each rises over WALL_RISE and all of them stand
# lit WALL_SHOW once the last is up.
const WALL_STAGGER := 0.02
const WALL_RISE := 0.35
const WALL_SHOW := 1.5
# The dark falls over DARK_FALL as the walls go and the HUD fades, then holds DARK_STILL before Matt's first yell.
const DARK_FALL := 0.3
const DARK_STILL := 0.3
# A step: Matt's yell tell, then the arrow live with his roar until the first direction press. A right one shows
# answered, then the hop; a wrong one shows cracked, then the knock onto the glass behind, the glass pose held, and
# back to the block for the same arrow again. The tell, the answer and the hop are half what they were (the user,
# 2026-09-28: "snappier steps", with the meter at 10 s): 0.17 s a step on top of reading the arrow, so a quick player
# (0.3 s an arrow) reaches Greyson at about 8.5 s and a slower one (0.4 s) just misses. A wrong press keeps its cost.
const YELL_TELL := 0.05
const ANSWERED_TIME := 0.04
const HOP_TIME := 0.08
const HOP_HEIGHT := 12.0
const KNOCK_TIME := 0.12
const GLASS_HOLD := 0.30
const BACK_TIME := 0.20
# How long Matt's roar holds after an answer before he settles.
const ROAR_HOLD := 0.2
# Two shards fall on the block left behind as the hop starts; it turns to glass as they land.
const SHARDS_PER_BLOCK := 2
const SHARD_FALL := 0.25
const SHARD_DRIFT := 16.0
const SHARD_INSET := Vector2(18, 12)
# The glass shows at this alpha while the dark is down: it glints faintly behind the player (Q2d).
const GLASS_DARK_ALPHA := 0.45
const GLASS_CLEAR_TIME := 0.5
# The screen's kick as the shout throws the player onto the glass.
const KNOCK_SHAKE := 8.0
const KNOCK_SHAKE_STEPS := 4
const KNOCK_SHAKE_STEP := 0.03

#GREYSON'S METER
# Starts with the first arrow and fills over METER_TIME: six poses A B C A B C, each banking a cell as it ends.
# Reaching the goal stops it; filling it fires the beam. 10 s by the user (2026-09-28: "make it 10 seconds"; it was 20),
# so each pose is 1.67 s, which still holds his 1.5 s strike and hold.
const METER_TIME := 10.0
const METER_CELLS := 6
const POSES: Array[StringName] = [&"pose_a", &"pose_b", &"pose_c", &"pose_a", &"pose_b", &"pose_c"]
# GreysonPose's: the flex's pitch on an empty meter and a full one.
const FLEX_PITCH := Vector2(1.0, 1.3)
# The meter fades out as the lights come up at the goal, so the juggle has the space over his head.
const METER_FADE := 0.3

#THE BEAM (full meter)
# Any knock under way finishes first. His spirit raise and the cannon's glow, the trace from his muzzle into the goal
# and back down the path to the player's block (its damage as it arrives), the hold, the fade and the lights.
const BEAM_CHARGE := 0.6
const BEAM_TRACE := 0.45
const BEAM_HOLD := 0.3
const BEAM_FADE := 0.3
const LIGHTS_UP := 0.4
# The beam runs this far over the path's floor line, through the player's middle.
const BEAM_HEIGHT := 40.0
# The glow on his muzzle through the charge: GreysonArtLayout's cannon_glow, stepped up its alphas and grown by this.
const GLOW_GROWTH := 1.6

#THE BEAM, V2 (the user, 2026-09-29: "the beam that hits the player should look much scarier and should travel much
# faster through the maze, impress me with this one")
# The switch: off, the beam is V1's, above. A static var so a test can play either. The beats are V1's in the same
# order - the charge, the trace, the hold, then FADE, which V2 plays as the beam breaking up - and the damage and its
# test hooks are the same. The charge_time() to fade_time() helpers below read whichever is on.
static var BEAM_V2 := true
# Seconds: the charge's dread; the head's race from the muzzle to the player's block, a fixed time whatever the route's
# length, so the race always reads and always lands as the head arrives; the crackling hold; the break into embers.
const BEAM_V2_CHARGE := 0.8
const BEAM_V2_TRACE := 0.16
const BEAM_V2_HOLD := 0.35
const BEAM_V2_DISSIPATE := 0.6
# THE CHARGE. The dark closes in on the player: a vignette over everything the lights-out lifted, under the Fx layer's
# effects, its clear radius round the player shrinking `from` to `to` px (eased in), another round the muzzle, the dark
# at `strength` in `bands` steps on the texel grid. It opens again as the beam breaks up.
const BEAM_V2_VIGNETTE := {from = 1500.0, to = 250.0, muzzle = 150.0, softness = 210.0, strength = 0.9, bands = 6.0}
# Streaks of light drawn in off a ring round the muzzle, `rate` a second rising through the charge, each crossing it in
# `life` s faster as it nears. The core there: a white heart, a red one and a faint glow, each growing from its `x` px
# to its `y`, pulsing from `pulse.x` Hz to `pulse.y`, and rings collapsing into it from `ring` px, one every
# `ring_every.x` s at first and `ring_every.y` at the end. The camera rumbles every `step` s, from `strength.x` px to
# `strength.y`. Greyson's meter goes as the charge begins: it has said its piece.
const BEAM_V2_SPARKS := {rate = Vector2(50, 230), ring = Vector2(140, 300), life = Vector2(0.22, 0.36),
	size = Vector2(3, 12), colors = [Color("#FFF1D8"), Color("#FF6A3C"), Color("#E02A2A")]}
const BEAM_V2_CORE := {heart = Vector2(6, 15), inner = Vector2(9, 27), glow = Vector2(18, 45), pulse = Vector2(5, 18),
	depth = 0.25, ring = Vector2(78, 12), ring_every = Vector2(0.3, 0.09), ring_time = 0.2, white = Color("#FFF4E8"),
	red = Color("#FF2A2A"), glow_color = Color(0.9, 0.05, 0.1, 0.35), ring_color = Color("#FF5A3C")}
# The launch, off the thrown cannon's muzzle as the head leaves it: a white star and a red disc, a ring out, sparks.
const BEAM_V2_LAUNCH := {star = 57.0, disc = 36.0, ring = Vector2(18, 105), time = 0.16, sparks = 14}
const BEAM_V2_RUMBLE := {step = 0.08, strength = Vector2(1.0, 9.0), steps = 3, step_time = 0.025, launch = 12.0}
# THE TRACE. A hellfire band BODY px wide behind the head (its cross-section drawn in code on the texel grid, `frames`
# of it swapped every `shimmer` s), a red glow round it and a white-hot core down it. `afterimages` copies of the head
# trail it a step apart. Each corner it turns throws sparks and a ring; each wall along the path it passes lights red
# `lead` px before the head reaches it, holds, and falls dark again.
const BEAM_V2_BODY := {width = 48.0, glow = 90.0, core = 9.0, frames = 3, shimmer = 0.035, jitter = 6.0,
	colors = [Color("#1A0508"), Color("#5A0E14"), Color("#B3202A"), Color("#FF5A3C"), Color("#FFF1D8")],
	glow_color = Color(0.85, 0.06, 0.08, 0.45), core_color = Color("#FFF8F0")}
const BEAM_V2_HEAD := {aura = 42.0, flare = Vector2(96, 42), heart = 15.0, pulse = 0.14, afterimages = 6,
	ghost_alpha = 0.6, aura_color = Color(0.95, 0.12, 0.08, 0.55), flare_color = Color("#FF6A3C"), rays = 3}
const BEAM_V2_CORNER := {sparks = 14, speed = Vector2(260, 780), life = Vector2(0.18, 0.34), drag = 5.0,
	ring = Vector2(12, 90), ring_time = 0.2, star = 36.0, star_time = 0.08}
const BEAM_V2_WALLS := {color = Color(2.6, 0.45, 0.4), lead = 48.0, hold = 0.1, fade = 0.5}
# THE IMPACT, as the head reaches the player: a hit-stop; the screen red for `red_time` then white for `white_time`,
# real seconds, since a hit-stop runs on them; a heavy shake through the stop; the blast and a shockwave off the player;
# the colours kicked `px` apart and settling over `time`, real seconds too; and the player thrown `px` back along the
# beam, dazed, and back onto the block as it breaks up.
const BEAM_V2_HIT_STOP := 0.12
# A tween steps the frame it is made, so 0.02 s is one frame of each at 60 fps, clear of both edges.
const BEAM_V2_FLASH := {red = Color(1.0, 0.1, 0.08, 0.85), white = Color(1.0, 0.97, 0.92, 0.9), red_time = 0.02,
	white_time = 0.02}
const BEAM_V2_SHAKE := {strength = 28.0, steps = 12, step_time = 0.03}
# The blast: a white burst `disc` px for `disc_time`, then its stars growing out and burning off, and sparks; the
# shockwave, and a red echo behind it.
const BEAM_V2_BLAST := {radius = 150.0, time = 0.4, disc = 84.0, disc_time = 0.07, sparks = 40,
	speed = Vector2(300, 1000), life = Vector2(0.2, 0.55)}
const BEAM_V2_SHOCKWAVE := {from = 24.0, to = 330.0, time = 0.36, width = Vector2(21, 3), color = Color("#FFD8C8"),
	echo_to = 220.0, echo_time = 0.55, echo_color = Color("#E02A2A")}
const BEAM_V2_CHROMA := {px = 9.0, time = 0.22}
const BEAM_V2_KNOCKBACK := {px = 36.0, time = 0.12}
# THE HOLD crackles: the band's width jitters, arcs jump off it and sparks pop. Then it breaks into pieces `segment` px
# long that burn out one by one over the dissipation's first `spread` of it, each in `burn` s, shedding embers that
# drift up and a puff of black smoke. The path is scorched behind the head, glowing and cooling over `cool` s, until
# the lights come up.
const BEAM_V2_CRACKLE := {arc_every = 0.05, arc_length = Vector2(24, 72), arc_life = 0.05, arc_width = 3.0,
	pop_every = 0.04}
const BEAM_V2_BREAK := {segment = 48.0, spread = 0.65, burn = 0.18, embers = 4, smoke = 1, glow_fade = 0.35}
const BEAM_V2_EMBERS := {rise = Vector2(40, 150), drift = 36.0, life = Vector2(0.45, 0.9),
	colors = [Color("#FFB070"), Color("#FF5A3C"), Color("#B3202A")]}
# Black smoke on the dark is grey smoke, lit red from under by the embers.
const BEAM_V2_SMOKE := {radius = Vector2(27, 72), rise = 60.0, life = Vector2(0.8, 1.3), color = Color(0.24, 0.2, 0.23, 0.55),
	lit = Color(0.5, 0.12, 0.07, 0.4)}
const BEAM_V2_SCORCH := {width = 30.0, char = Color(0.1, 0.03, 0.03, 0.8), glow_width = 12.0,
	glow = Color(1.0, 0.42, 0.16, 0.9), cool = 0.7, splat = Vector2(60, 27)}
# SOUND: stand-ins off the project's own set, layered, each played only if its file is in. A layer with `to_pitch` and
# `to_db` ramps to them over the charge.
const BEAM_V2_SOUNDS := {
	&"charge": [
		{stream = "res://Assets/Audio/SFX/carter_dark.wav", pitch = 0.7, volume_db = -2.0},
		{stream = "res://Assets/Audio/SFX/greyson_eruption_rumble.wav", pitch = 0.6, volume_db = -18.0, to_pitch = 0.9,
			to_db = -3.0},
		{stream = "res://Assets/Audio/SFX/laser_charge.ogg", pitch = 1.2, volume_db = -16.0, to_pitch = 2.2, to_db = -4.0},
		{stream = "res://Assets/Audio/SFX/greyson_spirit_charge.wav", pitch = 1.8, volume_db = -8.0},
	],
	&"launch": [
		{stream = "res://Assets/Audio/SFX/greyson_spirit_launch.wav", pitch = 1.3, volume_db = 0.0},
		{stream = "res://Assets/Audio/SFX/matt_trueshot_fire.wav", pitch = 0.7, volume_db = -2.0},
		{stream = "res://Assets/Audio/SFX/dash_whoosh.wav", pitch = 0.55, volume_db = -3.0},
	],
	&"corner": [{stream = "res://Assets/Audio/SFX/greyson_spark.wav", pitch = 1.5, volume_db = -10.0}],
	&"impact": [
		{stream = "res://Assets/Audio/SFX/greyson_spirit_explosion.wav", pitch = 1.15, volume_db = 2.0},
		{stream = "res://Assets/Audio/SFX/burak_blast.wav", pitch = 0.8, volume_db = 0.0},
		{stream = "res://Assets/Audio/SFX/eric_crash_thud.wav", pitch = 0.75, volume_db = 0.0},
		{stream = "res://Assets/Audio/SFX/hit_impact.ogg", pitch = 0.6, volume_db = -2.0},
	],
	&"crackle": [
		{stream = "res://Assets/Audio/SFX/matt_mystic_fizzle.wav", pitch = 0.7, volume_db = -6.0},
		{stream = "res://Assets/Audio/SFX/greyson_spark.wav", pitch = 0.9, volume_db = -9.0},
	],
	&"dissipate": [{stream = "res://Assets/Audio/SFX/matt_mystic_fizzle.wav", pitch = 0.45, volume_db = -4.0}],
}

#THE PAYOFF AND THE WRAP
const HYPE_EACH := 4.0
const HYPE_CLEAN := 10.0
const HINT := "FOLLOW MATT'S ARROWS TO GREYSON!"
# The hint goes once this many steps are answered and it has been up HINT_MIN_TIME, or at the goal or the beam.
const HINT_STEPS := 3
const HINT_MIN_TIME := 1.5

#ATTACK IDS (AttackCatalog: the glass half a heart, the beam a heart and a half, both through the i-frames)
const GLASS_ID := &"jordan_maze_glass"
const BEAM_ID := &"jordan_maze_beam"

#MATT'S YELL (MattStateMachine's yell numbers: MattYellRingScript blown with no target, harmless)
const YELL_RING := {start_radius = 60.0, end_radius = 270.0, band = 15.0, expand_time = 0.18, landing_time = 0.05}

#ART
# The wall block, approved 2026-09-28 (the lower take): 8 frames of 32x30 texels, a 32x20 top face over a 10-row front,
# its anchor (16,29) - the front edge's centre - on the block's bottom edge. Rise frames 0-3 (3 the lock flare), stand
# 4, vanish 5-7, then hidden. Each frame cuts the block at the floor line itself, so no mask. It is drawn from its
# top-left, `offset` texels off the wall's node, and the node stands on the cell's soles line less SOLES_OVER_ORIGIN:
# a wall sorts by its soles against the player's soles, the way the player's origin sorts. The switch is on; until the
# file is in and imported, the code block stands in, its top face and front the same size with a rune-blue edge.
const USE_FINAL_WALL := true
const WALL := {texture = "res://Assets/Environment/Void/void_wall.png", hframes = 8, frame = Vector2(32, 30),
	anchor = Vector2(16, 29), offset = Vector2(-16, -6), rise = [0, 1, 2, 3], rise_times = [0.07, 0.07, 0.09, 0.12],
	stand = 4, vanish = [5, 6, 7], vanish_times = [0.10, 0.10, 0.10]}
# His runes' blues (jordan_god_runes.png): #66C6EC for the top face's edge, #2B6C99 for the front's. `height` is the
# front's, the drawn block's 10 rows.
const PLACEHOLDER_WALL := {top = Color("#1A1420"), front = Color("#0D0A12"), top_edge = Color("#66C6EC"),
	front_edge = Color("#2B6C99"), edge_width = 3.0, height = 30.0}
# Computah's laser (his cannon arm is Computah's), at his beam's on-screen thickness: the rig's scale of 2 on the
# 23-texel beam. Two frames stacked, alternated for the shimmer, and the emitter's flare.
const BEAM_ART := {texture = "res://Assets/Characters/Computah/computah_laser_beam.png", frame = Vector2i(16, 23),
	frames = 2, scale = 2.0, shimmer_time = 0.06,
	flare = "res://Assets/Characters/Computah/computah_laser_fx.png", flare_hframes = 2}
# Greyson's V2 beam as drawn (art_source/jordan_maze_beam/approval/contract.json: two takes with the same sizes,
# pivots and frames). Each piece switches in on its own once its sheet is in and imported (beam_final()), and its
# additive glow under it once that is too; until then the code draws it. Sizes and pivots are texels at SCALE, every
# sheet a horizontal strip. The beats stay V2's own, above, and the art is stretched to them: the charge's three
# stages spread over BEAM_V2_CHARGE, each looping its frames, and the dissipate's frames over BEAM_V2_DISSIPATE.
const BEAM_V2_ART_PATH := "res://Assets/Environment/Void/maze_beam_%s.png"
# For a test only: a path with a %s for the sheet, read unimported off the disk in place of BEAM_V2_ART_PATH's.
static var BEAM_ART_OVERRIDE := ""
const USE_FINAL_BEAM := {&"charge": true, &"release": true, &"body": true, &"head": true, &"corner": true,
	&"impact": true, &"ring": true, &"dissipate": true, &"ember": true, &"smoke": true, &"scorch": true,
	&"overlay": true}
const BEAM_V2_ART := {
	# On the raised muzzle.
	&"charge": {frame = Vector2(80, 80), frames = 12, frame_time = 0.04, pivot = Vector2(40, 40), stages = 3,
		glow = true},
	# Once off the thrown muzzle as the trace starts, unturned: drawn firing down, as the first run always nearly is.
	&"release": {frame = Vector2(80, 80), frames = 6, frame_time = 0.03, pivot = Vector2(40, 40), glow = true},
	# The line's texture a frame at a time, its content flowing on from the muzzle; the glow line's frames are
	# `glow_frame`, in step. Left-going runs show it upside down, as a Line2D draws it.
	&"body": {frame = Vector2(96, 32), frames = 8, frame_time = 0.04, glow_frame = Vector2(96, 48), glow = true},
	# On the line's end, turned the way it runs and flipped upright on runs going left.
	&"head": {frame = Vector2(64, 48), frames = 6, frame_time = 0.03, pivot = Vector2(34, 24), glow = true},
	# Once on each joint as the head passes. Drawn for a turn right then down, its splash thrown up-right: flipped to
	# throw it the way the turn's outside is.
	&"corner": {frame = Vector2(64, 64), frames = 6, frame_time = 0.03, pivot = Vector2(32, 32), glow = true},
	&"impact": {frame = Vector2(112, 112), frames = 10, frame_time = 0.04, pivot = Vector2(56, 56), glow = true},
	# On the player's soles, under the impact.
	&"ring": {frame = Vector2(128, 48), frames = 8, frame_time = 0.035, pivot = Vector2(64, 24)},
	# The line's texture swapped to these, once, as it dissipates, its glow line off.
	&"dissipate": {frame = Vector2(96, 32), frames = 8, frame_time = 0.075},
	# Thrown off the line as it dissipates: `count` in every `every` px of it (smoke: one, in `chance` of them) up to
	# `within` px off it, over the first `spread` s; each flies straight at its speed, its frames over its life.
	&"ember": {frame = Vector2(8, 8), frames = 6, pivot = Vector2(4, 4), every = 26.0, count = 2, within = 30.0,
		spread = 0.25, speed_x = Vector2(-40, 40), speed_y = Vector2(-200, -90), life = Vector2(0.3, 0.55)},
	&"smoke": {frame = Vector2(16, 16), frames = 6, pivot = Vector2(8, 8), every = 26.0, chance = 0.55, within = 24.0,
		spread = 0.25, speed_x = Vector2(-15, 15), speed_y = Vector2(-80, -40), life = Vector2(0.45, 0.7)},
	# Laid on the floor line as the beam dissipates, each frame from its second of that, the last held.
	&"scorch": {frame = Vector2(96, 16), frames = 4, starts = [0.0, 0.15, 0.35, 0.6]},
	# Over his spirit sheet texel for texel, his eyes and his barrel lit: by the frame he shows there, the charge's
	# stage on it, then the throw's two frames every `flicker` s; gone as the beam dissipates. No code stand-in.
	&"overlay": {frame = Vector2(112, 112), frames = 8, over = "greyson_spirit.png",
		poses = {0: [0, 1, 2], 1: [3, 4, 5], 3: [6, 7]}, flicker = 0.05},
}


static func soles(cell: Vector2i) -> Vector2:
	return ORIGIN + Vector2(BLOCK.x * cell.x, -BLOCK.y * cell.y)


static func block_rect(cell: Vector2i) -> Rect2:
	return Rect2(soles(cell) - BLOCK / 2.0, BLOCK)


# Where the player's origin stands on `cell`.
static func body_point(cell: Vector2i) -> Vector2:
	return soles(cell) - Vector2(0, SOLES_OVER_ORIGIN)


static func goal() -> Vector2i:
	return GOAL


static func step_count() -> int:
	return ROUTE_STEPS


# The arrow on the route's block `step`: the way to the next one.
static func arrow(route: Array[Vector2i], step: int) -> StringName:
	var way := route[step + 1] - route[step]
	for dir: StringName in STEPS:
		if STEPS[dir] == way:
			return dir
	return &""


# The glass a wrong press at `step` throws the player back onto: the block they came from, or the back glass.
static func behind(route: Array[Vector2i], step: int) -> Vector2i:
	return route[step - 1] if step > 0 else BACK_GLASS


# Every block that touches the route and isn't on it, but Greyson's and the back glass.
static func walls(route: Array[Vector2i]) -> Array[Vector2i]:
	var out: Array[Vector2i] = []
	for cell in route:
		for dr in range(-1, 2):
			for dc in range(-1, 2):
				var next := cell + Vector2i(dc, dr)
				if route.has(next) or next == GREYSON_CELL or next == BACK_GLASS or out.has(next):
					continue
				out.append(next)
	return out


# The walls in the order they rise: out from the start, nearest first, ties left to right then bottom to top.
static func walls_by_distance(route: Array[Vector2i]) -> Array[Vector2i]:
	var out := walls(route)
	var start := soles(START)
	out.sort_custom(func(a: Vector2i, b: Vector2i) -> bool:
		var da := soles(a).distance_squared_to(start)
		var db := soles(b).distance_squared_to(start)
		if da != db:
			return da < db
		if a.x != b.x:
			return a.x < b.x
		return a.y < b.y
	)
	return out


# The beam's line in world px: from `muzzle` into the goal, then back down the route's corners to block `step`, all
# BEAM_HEIGHT over the floor line.
static func beam_points(route: Array[Vector2i], muzzle: Vector2, step: int) -> PackedVector2Array:
	var lift := Vector2(0, -BEAM_HEIGHT)
	var points := PackedVector2Array([muzzle])
	var last := route.size() - 1
	for i in range(last, step - 1, -1):
		if i != last and i != step and route[i + 1] - route[i] == route[i] - route[i - 1]:
			continue
		points.append(soles(route[i]) + lift)
	return points


#THE ROUTE

# A new route off `rng`, or the drawn path should every search fail.
static func generate(rng: RandomNumberGenerator) -> Array[Vector2i]:
	var route := try_generate(rng)
	if not route.is_empty():
		return route
	if OS.is_debug_build():
		push_warning("JordanMazeLayout: no route in %d searches; the drawn path stands in" % ROUTE_TRIES)
	return DRAWN_PATH.duplicate()


# ROUTE_TRIES depth-first searches from START in an order `rng` shuffles at every block, each giving up after
# ROUTE_BUDGET moves tried: the first route found, or empty.
static func try_generate(rng: RandomNumberGenerator) -> Array[Vector2i]:
	for attempt in ROUTE_TRIES:
		var route: Array[Vector2i] = [START]
		var budget := [ROUTE_BUDGET]
		if _extend(route, rng, budget):
			return route
	return []


static func _extend(route: Array[Vector2i], rng: RandomNumberGenerator, budget: Array) -> bool:
	var at: Vector2i = route[route.size() - 1]
	var left := ROUTE_STEPS - (route.size() - 1)
	if left == 0:
		return at == GOAL
	if absi(at.x - GOAL.x) + absi(at.y - GOAL.y) > left:
		return false
	var ways: Array = STEPS.values()
	for i in range(ways.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var held = ways[i]
		ways[i] = ways[j]
		ways[j] = held
	for way: Vector2i in ways:
		var next := at + way
		if next == GOAL and left != 1:
			continue
		budget[0] -= 1
		if budget[0] < 0:
			return false
		if _fits(route, next):
			route.append(next)
			if _extend(route, rng, budget):
				return true
			route.pop_back()
	return false


# Whether `next` may follow the route so far: inside the box, not on it, no wall of it on NO_WALL, and touching none of
# the route's blocks but its own neighbours along it (and the one across a turn, corner to corner).
static func _fits(route: Array[Vector2i], next: Vector2i) -> bool:
	if next.x < ROUTE_COLUMNS.x or next.x > ROUTE_COLUMNS.y or next.y < ROUTE_ROWS.x or next.y > ROUTE_ROWS.y:
		return false
	if route.has(next):
		return false
	for cell in NO_WALL:
		if absi(cell.x - next.x) <= 1 and absi(cell.y - next.y) <= 1:
			return false
	for i in route.size() - 2:
		var dx := absi(route[i].x - next.x)
		var dy := absi(route[i].y - next.y)
		if dx + dy == 1 or (not DIAGONAL_CONTACT and dx == 1 and dy == 1):
			return false
	return true


# Every rule `route` breaks, in words: none for a route the maze may play.
static func route_problems(route: Array[Vector2i]) -> Array[String]:
	var problems: Array[String] = []
	if route.size() != ROUTE_STEPS + 1:
		problems.append("%d steps, not %d" % [route.size() - 1, ROUTE_STEPS])
	if route.is_empty() or route[0] != START or route[route.size() - 1] != GOAL:
		problems.append("not from the start to the goal")
		return problems
	var so_far: Array[Vector2i] = [route[0]]
	for i in range(1, route.size()):
		var step := route[i] - route[i - 1]
		if absi(step.x) + absi(step.y) != 1:
			problems.append("step %d is not one block up, down, left or right" % i)
		if not _fits(so_far, route[i]):
			problems.append("block %d %s breaks the box, repeats, touches the corridor or walls Matt" % [i, route[i]])
		so_far.append(route[i])
	for cell in walls(route):
		if cell == GREYSON_CELL or cell == BACK_GLASS or NO_WALL.has(cell):
			problems.append("a wall on %s" % cell)
	return problems


# His mask and his chest core in world px, wherever and however big he is drawn.
static func jordan_face() -> Array[Rect2]:
	var out: Array[Rect2] = []
	for texels: Rect2 in [JORDAN_MASK_TEXELS, JORDAN_CORE_TEXELS]:
		out.append(Rect2(GodLayout.GOD_POINT + (texels.position - GodLayout.ANCHOR) * GodLayout.GOD_SCALE,
			texels.size * GodLayout.GOD_SCALE))
	return out


# Greyson's meter in world px at `ui_scale` (JordanGodLayout.ui_scale()): its size grown by it, centred over his head.
static func meter_rect(ui_scale: float) -> Rect2:
	var size: Vector2 = GreysonArtLayout.HYPE_METER.size * ui_scale
	var bottom := GREYSON_FEET.y - GREYSON_CROWN - METER_GAP * ui_scale
	return Rect2(Vector2(GREYSON_FEET.x - size.x / 2.0, bottom - size.y), size)


static func uses_final_wall() -> bool:
	return USE_FINAL_WALL and ResourceLoader.exists(WALL.texture)


# A piece of the V2 beam's final art, on, in and imported; its glow sheet, in as well.
static func beam_final(piece: StringName) -> bool:
	return BEAM_V2 and USE_FINAL_BEAM.get(piece, false) and beam_art_in(String(piece))


static func beam_glow_final(piece: StringName) -> bool:
	return beam_final(piece) and BEAM_V2_ART[piece].get("glow", false) and beam_art_in(String(piece) + "_glow")


static func beam_art_path(sheet: String) -> String:
	return (BEAM_ART_OVERRIDE if BEAM_ART_OVERRIDE != "" else BEAM_V2_ART_PATH) % sheet


static func beam_art_in(sheet: String) -> bool:
	var path := beam_art_path(sheet)
	return FileAccess.file_exists(path) if BEAM_ART_OVERRIDE != "" else ResourceLoader.exists(path)


static func beam_texture(sheet: String) -> Texture2D:
	var path := beam_art_path(sheet)
	if BEAM_ART_OVERRIDE != "":
		return ImageTexture.create_from_image(Image.load_from_file(path))
	return load(path)


# The beam's beats, seconds, off whichever beam is on.
static func charge_time() -> float:
	return BEAM_V2_CHARGE if BEAM_V2 else BEAM_CHARGE


static func trace_time() -> float:
	return BEAM_V2_TRACE if BEAM_V2 else BEAM_TRACE


static func hold_time() -> float:
	return BEAM_V2_HOLD if BEAM_V2 else BEAM_HOLD


static func fade_time() -> float:
	return BEAM_V2_DISSIPATE if BEAM_V2 else BEAM_FADE
