extends RefCounted

# Jordan's attack 2, Captain Burak + Danny's kegs (JordanComboKegs): every number it plays on, so a retune only needs
# this file. The user's own design and sketch (2026-09-28): Burak lays four kegs round the player, one glows at a time,
# and a dash to it and one punch puts it out; Danny butt-slams the middle the player waits in. Eight defuses in all,
# explosions or not, and the eighth keg flies into Burak.
#
# THE FLOOR: the player only ever stands in the centre or at one of the four stations, each on its keg's side of the
# centre and facing it. A station and the centre are soles points (where a player standing there has their soles); a
# keg's point is its floor point (its pivot) and a puppet's is its feet. The player's origin stands SOLES_OVER_ORIGIN
# over their soles (MainPlayer's collision box).
#
# STAGING is the puppeteer pass's option B (art_source/jordan_puppeteer/staging/staging.json): the camera draws the
# fight at 2/3, and every point here is a WORLD px, the world's own scale kept (world = screen x 1.5 + (-480, -6)). The
# kegs and stations keep their offsets round the centre. Everything stays off Jordan's mask (912,189)-(1008,258) and
# core (936,270)-(984,327) and out of the HUD, and Danny rests well clear of Jordan's right hand. The counter is a row of
# Burak's own pips over his hat.

const BurakArtLayout := preload("res://Scripts/BurakBossArtLayout.gd")

#THE FLOOR (px)
const SOLES_OVER_ORIGIN := 42.0
const CENTRE := Vector2(960, 1164)
# Also the order Burak lays them in.
const KEGS: Array[StringName] = [&"n", &"e", &"s", &"w"]
const KEG_POINTS := {&"n": CENTRE + Vector2(0, -230), &"e": CENTRE + Vector2(560, 0), &"s": CENTRE + Vector2(0, 250),
	&"w": CENTRE + Vector2(-560, 0)}
const STATIONS := {&"n": CENTRE + Vector2(0, -160), &"e": CENTRE + Vector2(470, 0), &"s": CENTRE + Vector2(0, 170),
	&"w": CENTRE + Vector2(-470, 0)}
# The way from the centre to each keg, in DirectionPress's and the arrow's names.
const WAYS := {&"n": &"up", &"e": &"right", &"s": &"down", &"w": &"left"}
const WAY_VECTORS := {&"up": Vector2(0, -1), &"right": Vector2(1, 0), &"down": Vector2(0, 1), &"left": Vector2(-1, 0)}
# Danny's seat, rx x ry round the centre: it takes in the centre and none of the four stations.
const SLAM_RADII := Vector2(150, 80)

#THE PAIR (feet, px)
const BURAK_FEET := Vector2(360, 954)
const DANNY_REST := Vector2(1710, 954)
# The counter's middle: DEFUSES of Burak's pips (BurakBossArtLayout's pips, 24 texels tall), their drawn bottom edge
# 24 px (16 on the screen) over his hat, whose crown is y 669 here. It is world-space UI, so under the camera's 2/3 it
# is drawn at JordanGodLayout.ui_scale() (1.5) to read at its own size on the screen, as the arrow and the hint are.
const COUNTER_CENTRE := Vector2(360, 595)
const DEFUSES := 8

#THE BEATS (seconds)
const TELEPORT_TIME := 0.35
# The lay: a keg every LAY_CADENCE, N E S W, each marked on its spot as it leaves his hand and down CARRY_TIME later
# on an ARC_HEIGHT arc; then LAY_SETTLE before the first glow can come.
const LAY_CADENCE := 0.20
const CARRY_TIME := 0.35
const ARC_HEIGHT := 180.0
const LAY_SETTLE := 0.35
# A glow comes GLOW_DELAY after the player lands in the centre, on a standing keg that isn't the last one to glow, and
# blows GLOW_TIME later. A player who stays at a keg after a defuse gets the next one STALL_TIME after it anyway.
# GLOW_TIME was 1.5 until the tuning of 2026-10-04: a practised answer (a reaction, the dash and the punch) lands in
# about 0.5 s, and 1.5 s let a wrong arrow be walked back with time to spare, so the attack cost nothing. At 0.85 a
# right answer still has a third of a second in hand, and a wrong one (out to the wrong keg, back, and over) blows.
const GLOW_DELAY := 0.25
const GLOW_TIME := 0.85
const STALL_TIME := 2.0
# A dash is one instant move this long; the punch pose runs its columns these long each and the fist lands as the last
# starts.
const DASH_TIME := 0.08
const PUNCH_TIMES := [0.03, 0.03, 0.03, 0.06]
# A blast: he re-lays its keg from RELAY_AFTER on (CARRY_TIME's flight), and aims at nothing new until it is down.
const RELAY_AFTER := 0.2
const BLAST_GAP := RELAY_AFTER + CARRY_TIME
# The arrow shows answered or cracked this long before it goes.
const ARROW_HOLD := 0.3

#DANNY'S SLAM
# Once the player has been in the centre DANNY_WAIT and he is at rest: Jordan's right hand yanks, and on the yank's pull
# frame (its frame 1) he leaps to over the centre. His shadow hangs there SHADOW_TIME (the tell), then he drops, sits,
# and hops back to rest.
# The landing's AttackCatalog entry, half a heart: not danny_butt_slam, which is a whole heart in his own fight.
const SLAM_ID := &"jordan_keg_slam"
const DANNY_WAIT := 0.25
const LEAP_TIME := 0.25
const SHADOW_TIME := 0.5
const DROP_TIME := 0.1
const SIT_TIME := 0.2
const HOP_TIME := 0.35
# Hung over the centre he stays under Jordan's core, so the tell never hides his face or core: the highest that keeps
# both clear by 12 px through the leap, the hang and the drop (whose first pose is his tallest) is 414.
const HOVER_HEIGHT := 410.0
const HOP_HEIGHT := 120.0
# DannyBossSlams' landing: its shake, and the cracks it leaves.
const IMPACT_SHAKE := 14.0
const IMPACT_SHAKE_STEPS := 4
const IMPACT_SHAKE_STEP := 0.04
const CRACKS_HOLD := 0.6
const CRACKS_FADE := 0.4

#THE EIGHTH
# The keg flies off its spot into Burak and bursts on him, smaller than a blast and hurting nobody; then the player
# walks to him for the punches. Not the plan's 140 px round his feet: from his side that is outside the uppercut's
# reach (his hurtbox is 108 px wide, grown by PlayerFinisher.uppercut_reach), and the first uppercut would whiff. The
# punches start once the player's origin is inside that reach with REACH_MARGIN to spare.
const LAUNCH_TIME := 0.45
const LAUNCH_ARC := 220.0
const BURST_SCALE := 2.0
const BURST_SHAKE := 8.0
const BURST_SHAKE_STEPS := 4
const BURST_SHAKE_STEP := 0.03
const COUNTER_FADE := 0.3
const REACH_MARGIN := 8.0

#HYPE AND THE HINT
const HYPE_EACH := 4.0
const HYPE_CLEAN := 10.0
# The move's glyph (InputSettings' ARROWS, LEFT STICK or the rebound keys) goes in the brackets.
const HINT := "PRESS (%s) TOWARD THE GLOWING KEG, THEN PUNCH IT!"


static func body_point(soles: Vector2) -> Vector2:
	return soles - Vector2(0, SOLES_OVER_ORIGIN)


static func in_slam_zone(soles: Vector2) -> bool:
	return ((soles - CENTRE) / SLAM_RADII).length_squared() <= 1.0


# The way `vector` points, if it is one of the four; a diagonal or nothing is &"".
static func way_of(vector: Vector2) -> StringName:
	for way: StringName in WAY_VECTORS:
		if WAY_VECTORS[way] == vector:
			return way
	return &""


# The keg a dash `way` from the centre goes to.
static func keg_toward(way: StringName) -> StringName:
	for keg: StringName in WAYS:
		if WAYS[keg] == way:
			return keg
	return &""


# From `keg`'s station, the only way that moves: back to the centre.
static func back_way(keg: StringName) -> StringName:
	return way_of(-WAY_VECTORS[WAYS[keg]])


static func punch_time() -> float:
	var total := 0.0
	for time: float in PUNCH_TIMES:
		total += time
	return total


static func punch_contact() -> float:
	return punch_time() - PUNCH_TIMES[PUNCH_TIMES.size() - 1]


# Pip 0's centre for a row drawn at `scale`, the row running right from it (BurakBossPips) and centred on
# COUNTER_CENTRE.
static func counter_origin(scale: float) -> Vector2:
	var spacing: float = BurakArtLayout.fx(&"pips").spacing * BurakArtLayout.SCALE * scale
	return COUNTER_CENTRE - Vector2((DEFUSES - 1) * spacing / 2.0, 0.0)
