extends RefCounted

# Jordan's attack 3, Josh + Eric's portals (JordanComboPortals): every number it plays on, so a retune only needs this
# file. The user's own design (2026-09-28): Josh opens a portal between them and Eric plunges his greatsword into it;
# Josh's floor portals then shoot the blade up round the player as fast spikes while Eric, portalled from spot to spot,
# spams his full-screen bear hug for PHASE_TIME; then both recover for the punches and the three-bar mash. The player
# is free all through it: walking, the parry and the dash.
#
# STAGING is option B's world px (JordanGodLayout's 2/3 view: world = screen x 1.5 + (-480, -6)). Josh stands left
# facing right and Eric right, never flipped (his hug frames, the held player, the toss and the planted sword are all
# drawn one way round), so the sword's portal goes between them. Texel points are on Eric's 256x192 frames, where his
# soles are the bottom edge of row 191 (FEET_ANCHOR), and every one of his sheets stands on that point.
#
# THE SWORD'S BASE is where the planted prop's blade meets its dirt, edge (63, 185) on eric_bearhug_planted_sword_v2
# (the portal artist's measure): the sword portal's anchor. Everything from row 185 down is the prop's dirt, which
# never shows: the prop is clipped there, and so are Eric's own frames while they draw the planted sword (NOTCHES).
# eric_winded's sword stands on edge (88, 185), so his recovery spot puts it back in the same portal.

const GodLayout := preload("res://Scripts/JordanGodLayout.gd")

const SCALE := 3.0

#THE USER'S OPEN QUESTIONS (built on the defaults, each a knob)
# Q1, the feint: &"lunge" re-routes him mid-lunge (the default, hard but reactable), &"charge" during the charge (easier:
# the badge never clears early, so nothing false is promised). A static var so the defence suite can play both.
static var FEINT_MODE := &"lunge"
# Q2, his sword-less charge: the drawn one (twin only, JordanPuppetLayout's eric `charge`) once it is in and imported;
# until then his empty wait (`empty`) under the badge.
const USE_PORTAL_CHARGE := true
const PORTAL_CHARGE := "res://Assets/Characters/Jordan/Puppets/eric/eric_portal_charge.png"
# Q3, a caught grab: this many squeezes of half a heart each.
const SQUEEZES := 3

#THE STAGING (world px)
const SOLES_OVER_ORIGIN := 42.0
const FEET_ANCHOR := Vector2(128, 192)
const SWORD_BASE_TEXEL := Vector2(63, 185)
const WINDED_SWORD_TEXEL := Vector2(88, 185)
const SWORD_PORTAL := Vector2(960, 909)
const JOSH_FEET := Vector2(560, 930)
const ERIC_FEET := SWORD_PORTAL - (SWORD_BASE_TEXEL - FEET_ANCHOR) * SCALE
const ERIC_RECOVERY := SWORD_PORTAL - (WINDED_SWORD_TEXEL - FEET_ANCHOR) * SCALE
# His first arrival, attack 2's centre.
const STAGE_CENTRE := Vector2(960, 1164)
# Where his feet may land on a hop or a feint's exit.
const HOP_BAND := Rect2(180, 700, 1560, 740)
const HOP_RANGE := Vector2(420, 720)
const HOP_CLEAR := 220.0
# How far spikes stay off where he comes up: a hop lands no nearer a spike up, and an exit showing (a hop's or a feint's)
# has the spikes still in their tell round it called off, and none new opened there.
const HOP_SPIKE_CLEAR := 150.0
# THE START: the spec has no warp, so a player standing clear stays put. One standing where a puppet would cover them,
# or where Eric's grabs round them would land on Josh, is warped (JordanCombo.warp_player) to the nearest clear spot on
# the floor beside or in front of the puppets, never up behind them, facing up at them, and let go as the summon starts
# (JordanPortalSpikes.start_spot). What is kept clear, world px, measured off the sheets: Josh's drawn body on his mark
# (idle, throw, recovery) - clear of Eric's whole grab round the player too, rush to toss (bear-hug frames 3-12, his feet
# at the player's soles + (-9, 67.5)), since Josh stands there all attack; and clear of the player's own drawn box, Eric
# on his mark (idle, plunge and plant right of the sword, empty wait), the planted sword with its portal, and Eric
# coming up charging at the centre.
const JOSH_BODY := Rect2(449, 702, 231, 228)
const ERIC_BODY := Rect2(993, 681, 330, 249)
const SWORD_BODY := Rect2(864, 642, 192, 303)
const PLAYER_BOX := Rect2(-18, -78, 36, 78)
const GRAB_REACH := Rect2(-183, -236, 339, 304)
# With nowhere clear nearer: the bottom centre.
const START_FALLBACK := Vector2(960, 1400)
# The nearest clear spot is looked for on half rings (level, through straight down, to level) START_STEP apart,
# START_ANGLES + 1 spots a half ring, START_RINGS out.
const START_STEP := 10.0
const START_RINGS := 90
const START_ANGLES := 32
# The warp's blink, before the summon.
const WARP_TIME := 0.35
# What has to stay out from under the HUD wherever he lands: his charging body off his soles (the empty wait's and the
# drawn charge's widest, aura and dust in), and the strong badge off its anchor, drawn at ui_scale (48 x 36 at 4.5).
const ERIC_DRAWN := Rect2(-165, -300, 335, 300)
const BADGE_DRAWN := Rect2(-90, -162, 185, 162)

#THE KEEP-CLEARS (the kegs attack's): Jordan's mask and core in world px, and the HUD blocks in screen px with their
# clearance. No spike's telegraph sits under one, and a blade that would reach into one comes up short of it.
const MASK := Rect2(912, 189, 96, 69)
const CORE := Rect2(936, 270, 48, 57)
const HUD_KEEP_OUT: Array[Rect2] = [Rect2(720, 33, 480, 148), Rect2(10, 842, 406, 229), Rect2(1371, 946, 537, 126)]
const HUD_CLEARANCE := 12.0
# The no-stand walls' overlap past their zones, px: the walls' collision margin lets a body pressed on them a fraction
# of a pixel in.
const NO_STAND_MARGIN := 2.0

#THE OPENING (seconds from the summon's end)
# Josh's cast (josh_throw 0-3): its release, frame 1, opens the sword portal. Eric's plunge, and its frame 13, where the
# blade goes into the portal. The spikes start, then Josh ports Eric to the centre.
const CAST_RELEASE := 0.25
const PLUNGE_AT := 0.55
const PLUNGE_ENTER := 0.18
const SPIKES_AT := 1.20
const TO_CENTRE_AT := 1.80
const PLUNGE_SHAKE := {strength = 6.0, steps = 4, step = 0.03}

#THE HOPS
# A body portal opens under him, he sinks through it, the exit opens at his new spot (the tell), and he rises out of it:
# charging, on every hop but the one home. The phase clock starts as he starts to rise at the centre.
const HOP := {open = 0.15, sink = 0.20, tell = 0.20, rise = 0.20}
const TO_CENTRE := {open = 0.15, sink = 0.25, tell = 0.30, rise = 0.20}
const HOME := {open = 0.15, sink = 0.20, tell = 0.20, rise = 0.20}
# Deep enough that nothing he hops in shows over the floor: the tallest is the drawn charge's aura, row 94.
const HOP_DEPTH := 100.0 * SCALE

#THE PHASE
# 7.0 until the tuning of 2026-10-04 (the god fight to the user's 9/10 under the new mash): 13 s holds about eight of
# his rushes where 7 held four, each one the attack's parry check.
const PHASE_TIME := 13.0

#THE GRAB (EricPacing V2 and EricScene's hug clips, copied, so his own fight can change without this one)
# The charge is the red strong badge; as it clears the rush homes his grab box on the player's hurtbox centre and
# reaches it RUSH_TIME later from anywhere, and his arms are live for RUSH_HOT there.
const GRAB_ID := &"eric_bear_hug_grab_v2"
const SQUEEZE_ID := &"eric_bear_hug_squeeze"
const CHARGE_TIME := 0.50
const RUSH_TIME := 0.30
const RUSH_HOT := 0.05
# EricArtLayout.GRAB_BOX (texels 102, 120, 58 x 72) off his soles, and its centre.
const GRAB_BOX := Rect2(-78, -216, 174, 216)
const GRAB_OFFSET := Vector2(9, -108)
# A parry knocks him back as he whiffs; a miss stumbles him longer.
const WHIFF_TIME := 0.14
const PARRY_RECOIL := 36.0
const STUMBLE_PARRIED := 0.20
const STUMBLE_IGNORED := 0.30
# The hold: the grab frame, SQUEEZES squeezes (the damage on each one's first frame), the toss, its end.
const GRAB_TIME := 0.28
const SQUEEZE_TIME := 0.42
const TOSS_TIME := 0.20
const TOSS_END_TIME := 0.30
const TOSS_DIRECTION := Vector2(0.7071, -0.7071)
# EricBearHug.TELL_HEAD_PIXEL, over his head on the (drawn) charge frames; the stand-in's is 8 texels over the empty
# wait's crown (row 118), as that one is over the charge's.
const TELL_HEAD := Vector2(150, 114)
const TELL_HEAD_STAND_IN := Vector2(131, 110)
# The badge clears itself only on the attack's word: the charge can be paused by a re-route.
const BADGE_HOLD := 10.0

#THE FEINT
# Josh may pull Eric out of his own lunge and put him somewhere closer: FEINT_CHANCE a rush, never the phase's first,
# never twice running, at most FEINTS_MAX a phase. From the rush's start (the badge clearing): the entry portal opens on
# his path at FEINT_ENTRY_OPEN (at twice speed), he dives into it at FEINT_ENTER; the exit opens EXIT_RANGE off the player
# on a new side (EXIT_TURN or more off his approach) with the badge over it for EXIT_TELL; then the badge clears and he
# bursts out rushing, and it lands RUSH_TIME later - so the badge clearing always means the grab lands RUSH_TIME later.
const FEINT_CHANCE := 0.35
const FEINTS_MAX := 2
const FEINT_ENTRY_OPEN := 0.05
const FEINT_ENTER := 0.15
const FEINT_DIVE := 0.06
const EXIT_TELL := 0.35
const FEINT_RISE := 0.06
const FEINT_TOTAL := FEINT_ENTER + EXIT_TELL + RUSH_TIME
const EXIT_RANGE := Vector2(200, 260)
const EXIT_TURN := 90.0
# THE REARM: at the promised contact the parry lockout is wiped (PlayerDefense.rearm_parry), so a press made on the
# promised timing still leaves the real grab parryable with a second press. PARRY_WINDOW is PlayerDefense.parry_window.
const REARM_AT := RUSH_TIME
const PARRY_WINDOW := 0.24
# FEINT_MODE &"charge": the re-route REROUTE.at into the charge - a fast portal under him, the sink, the exit's tell under
# the badge, his rise - the charge's clock held until he rises.
const REROUTE := {at = 0.25, open = 0.10, sink = 0.10, tell = 0.35, rise = 0.20}

#THE SPIKES
# Its portal shows SPIKE_TELL before the blade (the whole opening readable by SPIKE_READABLE), then the blade shoots up
# BLADE_ROWS over SPIKE_RISE, holds, is sucked back (harmless) and the portal closes. Live (it hurts) through the rise
# and the hold. A wave every WAVE_EVERY, MAX_LIVE up at once.
const SPIKE_TELL := 0.40
const SPIKE_READABLE := 0.12
const SPIKE_RISE := 0.06
const SPIKE_HOLD := 0.14
const SPIKE_SUCK := 0.12
const SPIKE_CLOSE := 0.12
const WAVE_EVERY := 0.45
const MAX_LIVE := 5
const HIT_ID := &"jordan_portal_spike"
# The hurt ellipse is exactly the drawn opening (36 x 14 texels); the player's soles box is tested against it.
const SPIKE_OPENING := Vector2(54, 21)
const SOLES_BOX := Rect2(-18, -6, 36, 12)
# The patterns ("on the side of the player"): the pincer, a flank either side PINCER_RANGE off; aimed and flank, one on
# the soles now and one a random side FLANK_RANGE off. Flanks sit within FLANK_TILT of level.
const PATTERNS: Array[StringName] = [&"pincer", &"aimed"]
const PINCER_RANGE := Vector2(170, 230)
const FLANK_RANGE := Vector2(150, 260)
const FLANK_TILT := 25.0
# The fairness rules the director keeps (the build plan's a-e): an aimed spike only with AIM_FREE_WAYS of the eight ways
# out of it clear of every other ellipse for AIM_ESCAPE; flanks FLANK_MIN off the soles and portals PORTAL_SPACING
# apart; no aimed live window inside AIM_CLEAR (before, after) of a grab's contact; nothing aimed, and nothing new
# within HELD_CLEAR, while the player is held.
const AIM_FREE_WAYS := 2
const AIM_ESCAPE := 130.0
const ESCAPE_STEP := 6.0
const FLANK_MIN := 150.0
const PORTAL_SPACING := 100.0
# Its after-margin (y) was 0.10 until the playtest of 2026-10-04: a guard press holds the player in the parry stance for
# the whole of PARRY_WINDOW, so a grab landing up to 0.30 s into an aimed spike's tell rooted them in it through a good
# parry, and the blade rose under them. The stance's length is added, the 0.10 to step out kept.
const AIM_CLEAR := Vector2(0.30, PARRY_WINDOW + 0.10)
const HELD_CLEAR := 300.0
const PLACE_TRIES := 24
const HOP_TRIES := 60

#THE BLADE
# Eric's greatsword, point up, coming out of the floor: the artist's cleaned blade (point row 0, its centre on edge x
# 17) once it is in; until then eric_thrown_sword_v2 frame 6 cropped to the blade, its spin trail's pure white taken
# out (point row 5, centre on edge x 80). Clipped at the floor line: only its top `rows` show.
const BLADE_ROWS := 70
const SPIKE_BLADE := "res://Assets/Characters/Jordan/Portals/eric_sword_spike_up.png"
const SPIKE_BLADE_POINT_X := 17.0
const BLADE_STAND_IN := {sheet = "res://Assets/Characters/Eric/eric_thrown_sword_v2.png", region = Rect2i(1027, 5, 26, 70),
	point_x = 13.0}
# The optional smear behind the blade (3 frames of 32 x 96: rising, full, retracting), its anchor (16, 95) - an edge
# point, as the portals' are - on the floor line.
const USE_SPIKE_SMEAR := true
const SPIKE_SMEAR := "res://Assets/Characters/Jordan/Portals/portal_spike_smear.png"
const SMEAR := {frames = 3, size = Vector2(32, 96), anchor = Vector2(16, 95)}

#THE PLANTED SWORD
const PLANTED_SWORD := "res://Assets/Characters/Eric/eric_bearhug_planted_sword_v2.png"
# The prop's drawn rect above its dirt (texels): hilt to blade.
const PLANTED_REGION := Rect2(35, 96, 53, 89)
# Where his own frames draw the planted sword, cut out of his clip while they show (bottom-edge outlines, texels, from
# right to left): `floor`, the dirt under the floor line; `collar`, the blade up to the drawn portal's front collar as
# well (rows 175-184, which every plunge and loop front frame covers whole), as it covers the prop, so the blade reads
# halfway in.
const NOTCHES := {
	&"plant": {
		floor = [Vector2(91, 192), Vector2(91, 185), Vector2(33, 185), Vector2(33, 192)],
		collar = [Vector2(91, 192), Vector2(91, 185), Vector2(76, 185), Vector2(76, 175), Vector2(50, 175), Vector2(50, 185),
			Vector2(33, 185), Vector2(33, 192)],
	},
	&"winded": {
		floor = [Vector2(100, 192), Vector2(100, 189), Vector2(104, 189), Vector2(104, 185), Vector2(58, 185), Vector2(58, 192)],
		collar = [Vector2(100, 192), Vector2(100, 189), Vector2(104, 189), Vector2(104, 185), Vector2(101, 185), Vector2(101, 175),
			Vector2(75, 175), Vector2(75, 185), Vector2(58, 185), Vector2(58, 192)],
	},
}

#THE PORTALS (JordanPortal)
# The drawn ones (Josh's, in their approval pass): three synced layers each - back on the Floor, front and an additive
# glow on the Stage a pixel below the anchor - per kind and sequence at PORTAL_DIR/portal_<kind>_<sequence>_<layer>.png,
# a frame each step. Each opening is an ellipse centred on its anchor (texels, edge points). A kind plays once all its
# sheets are in and imported (final_portal); until then the placeholder below.
const USE_FINAL_PORTALS := true
const PORTAL_DIR := "res://Assets/Characters/Jordan/Portals/"
const PORTAL_LAYERS: Array[StringName] = [&"back", &"front", &"glow"]
const PORTALS := {
	&"spike": {frame = Vector2(48, 24), anchor = Vector2(24, 16), opening = Vector2(36, 14)},
	&"body": {frame = Vector2(112, 40), anchor = Vector2(56, 26), opening = Vector2(88, 24)},
	&"sword": {frame = Vector2(64, 40), anchor = Vector2(32, 28), opening = Vector2(44, 14)},
}
# Each kind's sequences, seconds a frame: `open` into its `loop`; the spike's `burst` (its blade) and the sword's
# `plunge` back into the loop; the spike's `suck` held on its last frame; `close`, and it is gone. The body portal's
# open plays at twice speed for a feint's entry.
const PORTAL_SEQUENCES := {
	&"spike": {&"open": [0.06, 0.06, 0.08, 0.10, 0.10], &"burst": [0.03, 0.03], &"hold": [0.07, 0.07], &"suck": [0.06, 0.06],
		&"close": [0.04, 0.04, 0.04]},
	&"body": {&"open": [0.04, 0.04, 0.06, 0.06], &"hold": [0.08, 0.08], &"close": [0.05, 0.05, 0.05]},
	&"sword": {&"open": [0.05, 0.05, 0.06, 0.07, 0.07], &"plunge": [0.05, 0.05, 0.05], &"loop": [0.10, 0.10, 0.10, 0.10],
		&"close": [0.05, 0.05, 0.05, 0.05]},
}
const PORTAL_LOOPS := {&"spike": &"hold", &"body": &"hold", &"sword": &"loop"}
const PORTAL_BURSTS := {&"spike": &"burst", &"sword": &"plunge"}
# Until they are in: JordanRift's placeholder in rune blue - the dark of the hole, a rim, an added glow - sized off the
# opening, with bone card flecks rising off it, grown in over its open (the spike's over SPIKE_READABLE) and shrunk away
# over its close. The spike's rim flares as its blade bursts.
const PLACEHOLDER_PORTAL := {depth = Color("#0B1726"), rim = Color("#66C6EC"), rim_width = 6.0, glow = Color("#17385A"),
	glow_scale = 1.25, points = 32, flare = Color("#D2F6FF"), flare_time = 0.06, flecks = 8, fleck_color = Color("#E8D8C8"),
	fleck_size = Vector2(2, 3), fleck_speed = Vector2(40, 110), fleck_life = 0.7}

#SOUNDS (stand-ins off the shared set, each only if its file is in)
const SOUNDS := {
	&"portal": {stream = "res://Assets/Audio/SFX/laser_charge.ogg", pitch = 1.6, volume_db = 0.0, voices = 3},
	&"spike_burst": {stream = "res://Assets/Audio/SFX/whirlwind_whoosh.ogg", pitch = 1.8, volume_db = 0.0, voices = 3},
	&"spike_suck": {stream = "res://Assets/Audio/SFX/whirlwind_whoosh.ogg", pitch = 0.8, volume_db = -10.0, voices = 3},
	&"plunge": {stream = "res://Assets/Audio/SFX/earthquake_slam.ogg", pitch = 1.2, volume_db = 0.0, voices = 1},
	&"rush": {stream = "res://Assets/Audio/SFX/whirlwind_whoosh.ogg", pitch = 1.1, volume_db = 0.0, voices = 2},
	&"squeeze": {stream = "res://Assets/Audio/SFX/hit_impact.ogg", pitch = 0.7, volume_db = 0.0, voices = 2},
	&"toss": {stream = "res://Assets/Audio/SFX/wrestler_collision.ogg", pitch = 1.0, volume_db = 0.0, voices = 1},
	&"hop": {stream = "res://Assets/Audio/SFX/carter_dark.wav", pitch = 1.4, volume_db = 0.0, voices = 2},
}

#THE PAYOFF
# A phase with no hit taken pays this hype; the punches start once the player's origin is inside a puppet's uppercut
# reach (its hurtbox grown PlayerFinisher.uppercut_reach) with REACH_MARGIN to spare.
const HYPE_CLEAN := 10.0
const REACH_MARGIN := 8.0


# The anim his charge plays: the drawn sword-less one, or his empty wait until it is in.
static func charge_anim() -> StringName:
	return &"charge" if USE_PORTAL_CHARGE and ResourceLoader.exists(PORTAL_CHARGE) else &"empty"


# His badge's point off his soles, px, for the charge in use.
static func tell_offset() -> Vector2:
	var head: Vector2 = TELL_HEAD if charge_anim() == &"charge" else TELL_HEAD_STAND_IN
	return (head + Vector2(0.5, 0.5) - FEET_ANCHOR) * SCALE


# Where the player's soles may not be as the attack starts: each kept-clear body grown by what must stay off it, and the
# no-stand zones.
static func start_zones() -> Array[Rect2]:
	var zones: Array[Rect2] = [_grown(JOSH_BODY, GRAB_REACH)]
	for body: Rect2 in [ERIC_BODY, SWORD_BODY, Rect2(STAGE_CENTRE + ERIC_DRAWN.position, ERIC_DRAWN.size)]:
		zones.append(_grown(body, PLAYER_BOX))
	zones.append_array(no_stand_zones())
	return zones


# Where the soles would put a spike's telegraph under a keep-clear (playtest 2026-10-04): no spike can open on or beside
# a player there - under the HUD's blocks or his mask and core, or along their edges - so standing still there was safe
# from every one, and under the HUD the player is drawn behind it. The attack walls the player's body out of them
# (no_stand_walls), and a player standing in one as it starts is warped out with the rest of start_zones().
static func no_stand_zones() -> Array[Rect2]:
	var spec: Dictionary = PORTALS[&"spike"]
	var telegraph := Rect2(-spec.anchor * SCALE, spec.frame * SCALE)
	var zones: Array[Rect2] = []
	for keep: Rect2 in keep_outs():
		zones.append(Rect2(keep.position - telegraph.end, keep.size + telegraph.size))
	return zones


# `soles` moved out of every no-stand zone by the shortest way that keeps them in `origins` (the player's soles' floor),
# clear of the walls' margin: where the attack itself puts the player (Eric's hold and his toss, 250 px over his feet)
# must never be inside a wall, which would hold them there for good.
static func out_of_no_stand(soles: Vector2, origins: Rect2) -> Vector2:
	var out := soles
	for pass_index in 2:
		for zone in no_stand_zones():
			if not zone.has_point(out):
				continue
			var clear := NO_STAND_MARGIN + 1.0
			var best := out
			var least := INF
			for exit: Vector2 in [Vector2(zone.position.x - clear, out.y), Vector2(zone.end.x + clear, out.y),
					Vector2(out.x, zone.position.y - clear), Vector2(out.x, zone.end.y + clear)]:
				if origins.has_area() and not origins.has_point(exit):
					continue
				if exit.distance_to(out) < least:
					least = exit.distance_to(out)
					best = exit
			out = best
	return out


# The walls that keep a body whose collision box is `body` (off its soles) out of the no-stand zones, NO_STAND_MARGIN
# over: its box touches one only with its soles inside the zone.
static func no_stand_walls(body: Rect2) -> Array[Rect2]:
	var walls: Array[Rect2] = []
	for zone in no_stand_zones():
		var wall := Rect2(zone.position + body.end, zone.size - body.size).grow(NO_STAND_MARGIN)
		if wall.has_area():
			walls.append(wall)
	return walls


# The soles that put `box` (off the soles) over `body`.
static func _grown(body: Rect2, box: Rect2) -> Rect2:
	return Rect2(body.position - box.end, body.size + box.size)


# Him charging at `feet`, and his badge: what the HUD must not cover.
static func eric_rects(feet: Vector2) -> Array[Rect2]:
	return [Rect2(feet + ERIC_DRAWN.position, ERIC_DRAWN.size),
		Rect2(feet + tell_offset() + BADGE_DRAWN.position, BADGE_DRAWN.size)]


static func portal_sheet(kind: StringName, sequence: StringName, layer: StringName) -> String:
	return PORTAL_DIR + "portal_%s_%s_%s.png" % [kind, sequence, layer]


static func final_portal(kind: StringName) -> bool:
	if not USE_FINAL_PORTALS:
		return false
	for sequence in PORTAL_SEQUENCES[kind]:
		for layer in PORTAL_LAYERS:
			if not ResourceLoader.exists(portal_sheet(kind, sequence, layer)):
				return false
	return true


static func sequence_time(kind: StringName, sequence: StringName) -> float:
	var total := 0.0
	for time: float in PORTAL_SEQUENCES[kind][sequence]:
		total += time
	return total


# An opening's radii, px.
static func opening(kind: StringName) -> Vector2:
	return PORTALS[kind].opening * SCALE / 2.0


static func final_blade() -> bool:
	return ResourceLoader.exists(SPIKE_BLADE)


static func final_smear() -> bool:
	return USE_SPIKE_SMEAR and ResourceLoader.exists(SPIKE_SMEAR)


# The keep-clears as world rects: the mask and the core, and the HUD blocks (with their clearance) through the fight's
# own base view.
static func keep_outs() -> Array[Rect2]:
	var out: Array[Rect2] = [MASK, CORE]
	var zoom: float = GodLayout.VIEW_ZOOM
	for block: Rect2 in HUD_KEEP_OUT:
		var grown := block.grow(HUD_CLEARANCE)
		out.append(Rect2((grown.position - GodLayout.VIEW_SIZE / 2.0) / zoom + GodLayout.VIEW_FOCUS, grown.size / zoom))
	return out


# The feint's timing has to leave a press made on the promised contact, once rearmed, a whole parry window before the
# real one; and a spike's tell has to cover a reaction and a step out of it.
static func invariants() -> Array[String]:
	var broken: Array[String] = []
	if FEINT_ENTER + EXIT_TELL + RUSH_TIME < RUSH_TIME + PARRY_WINDOW:
		broken.append("FEINT_ENTER + EXIT_TELL + RUSH_TIME < RUSH_TIME + PARRY_WINDOW")
	if REARM_AT >= FEINT_TOTAL - PARRY_WINDOW:
		broken.append("the rearm comes after the real grab's parry window opens")
	if FEINT_ENTRY_OPEN >= FEINT_ENTER:
		broken.append("the entry portal opens after he dives")
	if SPIKE_READABLE >= SPIKE_TELL:
		broken.append("a spike's opening isn't readable before its blade")
	return broken


static func assert_invariants() -> void:
	var broken := invariants()
	assert(broken.is_empty(), "JordanPortalsLayout: %s" % [broken])
