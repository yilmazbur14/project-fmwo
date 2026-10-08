extends RefCounted

# Josh's card-gate portals and the two card hands that come out of them, in his own fight (the user, 2026-09-29):
# every number that depends on how they are drawn or where they stand, so the approved art only needs this file.
# JoshHandsRig owns the portals (JoshPortal) and the hands (JoshHand); JoshCardsSummon brings them in and
# JoshCardsHandSlam drives the hands. Texel numbers are on a frame, origin top-left; world numbers are px.
#
# THE ART SWITCHES IN ON ITS OWN. Each kind - the portals, the hands, the floor mark - plays its final sheets once
# every sheet it needs is in and imported (final_portal, final_hand, final_mark), and its placeholder until then, so
# a half-drawn set never mixes the two. Shipping the approved sheets IS wiring them: nothing may ship into Assets/
# before the user approves. The art pass's frame sizes, pivots, frame counts and per-frame times are soft: its
# numbers are copied in here (from art_source/josh_hands/approval/contract.json, 2026-09-29). Clip totals, the contact
# frame, the footprint and the file names are the gameplay's. Pivots are in Josh's corner convention: a sprite's
# offset is frame / 2 - pivot.

const JoshArtLayout := preload("res://Scripts/JoshArtLayout.gd")
const AttackCatalog := preload("res://Scripts/AttackCatalog.gd")

const SCALE := 3.0
const SIDES: Array[StringName] = [&"left", &"right"]

#WHERE THEY STAND (world px)
# Off his start spot (959, 700), clear of the boss bar block (x 708-1212 with its clearance), his start rect and the
# skip hint top right. The portals' pivots are the centres of their openings, written once and never moved.
const PORTAL_POINTS := {&"left": Vector2(575, 270), &"right": Vector2(1345, 270)}
# A resting hand's pivot, off its portal's.
const REST_OFFSET := Vector2(0, 170)
# The y-sort points they rest on: after the Mat (99), before the floor layers (101) and every character (148 and
# up), so the lanes and the marks draw over them and everyone stands in front of them. A hand in the air is drawn
# over the ropes (z 1) and under the red badge (z 3); landed, it y-sorts on its floor point with everyone.
const PORTAL_SORT_Y := 100.0
const HAND_REST_SORT_Y := 100.5
const HAND_AIR_Z := 2

#THE PORTALS (JoshPortal)
# Drawn as the right one and mirrored for the left, two layers a sequence: back (the vortex, rim and card ring) and
# glow, drawn additive. The hand is always drawn in front of a portal. Texels; the pivot is the opening's centre, and
# the opening, its gold rim and its ring of cards are circles round it (radii).
const USE_FINAL_PORTAL := true
const PORTAL_DIR := "res://Assets/Characters/Josh/Portals/"
const PORTAL := {frame = Vector2(112, 112), pivot = Vector2(56, 56), opening = 21.0, rim = 25.0, ring = 35.0}
const PORTAL_LAYERS: Array[StringName] = [&"back", &"glow"]
# Seconds a frame. open runs into loop, which is seamless; close ends empty and the portal is freed; feed is its
# flare as a card goes in, the one sequence that may be missing (the placeholder's rim and glow flare instead).
const PORTAL_SEQUENCES := {
	&"open": [0.07, 0.08, 0.08, 0.09, 0.10],
	&"loop": [0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10],
	&"close": [0.07, 0.07, 0.08, 0.08],
	&"feed": [0.05, 0.05],
}
const PORTAL_REQUIRED: Array[StringName] = [&"open", &"loop", &"close"]
# The placeholder: the opening filled with the vortex, a gold rim, an added glow out to the ring and cream card flecks
# circling it between the rim and the ring (texels); grown in over its open, shrunk away over its close, the rim and
# the glow flaring as a card goes in.
const PLACEHOLDER_PORTAL := {points = 32, grown_from = 0.05, flecks = 8, fleck_size = Vector2(4, 6), fleck_orbit = 30.0,
	fleck_turns = 0.5, flare_time = 0.12, flare_glow = 0.5}

#THE HANDS (JoshHand)
# Drawn as the right portal's hand and mirrored for the left about the pivot column (64). The pivot is the centre of
# the flat hand's floor footprint on the impact contact frame; on an air frame, the point that comes down onto it.
const USE_FINAL_HAND := true
const HAND_DIR := "res://Assets/Characters/Josh/Hands/"
const HAND := {frame = Vector2(128, 128), pivot = Vector2(64, 70)}
# What an air frame covers round the pivot, texels, drawn as the right hand: the union of the hover, windup and drop
# sheets and their glow layers, measured off the approval sheets (the art's own air_box_px, without the glow, is
# Rect2(-150, -141, 294, 282)). The HUD fade tests a hand in the air with it, mirrored for the left
# (JoshHand.drawn_rect).
const HAND_AIR_TEXELS := Rect2(-53, -50, 104, 100)
const HAND_AIR_BOX := Rect2(HAND_AIR_TEXELS.position * SCALE, HAND_AIR_TEXELS.size * SCALE)
# Seconds a frame, as many as the sheet has. Their totals are the gameplay's: form 0.60 (its last frame is hover's
# first), windup 0.13 and drop 0.23 (the state machine's hand_lock_time and hand_drop_time, 0.15 and 0.25 until the
# tuning round of 2026-10-04), shatter 0.30 (its last frame empty). impact's first three frames are the pin, and its
# last is held through the last slam's settle, however long its sheet says.
const HAND_CLIPS := {
	&"form": {times = [0.08, 0.08, 0.08, 0.08, 0.08, 0.10, 0.10], loop = false},
	&"hover": {times = [0.10, 0.10, 0.10, 0.10, 0.10, 0.10], loop = true},
	&"windup": {times = [0.06, 0.07], loop = false},
	&"drop": {times = [0.11, 0.12], loop = false},
	&"impact": {times = [0.05, 0.05, 0.05, 0.3], loop = false},
	&"shatter": {times = [0.04, 0.05, 0.05, 0.05, 0.05, 0.06], loop = false},
}
const HAND_CONTACT_FRAME := 0
# Each clip's additive layer, josh_hand_<clip>_glow.png: same frames and pivot, kept in step. Drawn where it is in.
const HAND_GLOW_SUFFIX := "_glow"
# The clips the art may add, each played in its own time once its sheet is in with the final hands, and until then
# what stands in for it: the rise off the floor (drop backwards), the re-form after a parry (form, faster) and the
# dissolve into the portal at his Break (form backwards, faster). The art pass of 2026-09-29 drew none of them.
const HAND_OPTIONAL := {
	&"lift": {times = [0.125, 0.125], loop = false, stand_in = &"drop", reverse = true},
	&"reform": {times = [0.1125, 0.1125, 0.1125, 0.1125], loop = false, stand_in = &"form", reverse = false},
	&"retract": {times = [0.075, 0.075, 0.075, 0.075], loop = false, stand_in = &"form", reverse = true},
}
# The Break's dissolve.
const RETRACT_TIME := 0.30
# The placeholder: a palm-down glove of cards centred on the pivot as the drawn hand is (texels, inside
# HAND_AIR_TEXELS), its rim and three pips, the clips played as transforms of it, and the fan of cards
# (JoshArtLayout.FINAL_CARD_BURST) for form and shatter.
const PLACEHOLDER_HAND: Array[Vector2] = [
	Vector2(-9, -39), Vector2(17, -39), Vector2(18, -26), Vector2(25, -21), Vector2(26, 8), Vector2(26, 29),
	Vector2(23, 32), Vector2(20, 32), Vector2(18, 29), Vector2(18, 13), Vector2(17, 13), Vector2(17, 35),
	Vector2(14, 39), Vector2(10, 39), Vector2(9, 35), Vector2(9, 13), Vector2(8, 13), Vector2(8, 36), Vector2(5, 40),
	Vector2(1, 40), Vector2(0, 36), Vector2(0, 13), Vector2(-1, 13), Vector2(-1, 34), Vector2(-4, 38), Vector2(-8, 38),
	Vector2(-9, 34), Vector2(-9, 10), Vector2(-20, 16), Vector2(-27, 10), Vector2(-25, 4), Vector2(-17, -3),
	Vector2(-17, -21), Vector2(-10, -26),
]
const PLACEHOLDER_PIPS: Array[Vector2] = [Vector2(4, -13), Vector2(-4, -3), Vector2(12, -3)]
const PLACEHOLDER_LOOK := {rim_width = 1.0, pip_radius = 2.0, bob = 2.0, form_from = 0.2, windup_scale = 1.08,
	drop_squash = Vector2(1.06, 0.8), impact_squash = Vector2(1.15, 0.5)}

#THE FOOTPRINT
# The flat hand on the impact contact frame, and the mark's rim on every frame: the hit area, to the pixel. Radii,
# round the pivot, the same whichever art is in. Walking out from the lock (lock + drop less a 0.20 s reaction, at
# 600 px/s) goes 120 px, past both.
const FOOTPRINT_TEXELS := Vector2(28, 19)
const FOOTPRINT := FOOTPRINT_TEXELS * SCALE

#THE MARK (JoshHandMark)
# On the floor under the hand that is coming down: frames 0-1 flicker while it tracks, 2-4 are high, mid and low as
# it drops ([share of its hover height it is over, frame]), 5 is landed. Its rim is the footprint on every frame:
# the edge ring of the texels whose centres are inside the ellipse round the pivot.
const USE_FINAL_MARK := true
const MARK := {texture = "res://Assets/Characters/Josh/Hands/josh_hand_mark.png", frames = 6, frame = Vector2(64, 40),
	pivot = Vector2(32, 20), hover_frames = [0, 1], frame_time = 0.10, height_frames = [[0.75, 2], [0.45, 3], [0.12, 4]],
	land_frame = 5, fade_in = 0.15}
const PLACEHOLDER_MARK := {points = 40, rim_width = 3.0, fill_from = 0.35, flicker_alpha = 0.55}

#THE IMPACT (optional): its own burst on the floor under the hand once it is in, and the fan of cards over the floor
# point until then. Not josh_hand_impact.png: that is the impact clip.
const IMPACT_FX := {texture = "res://Assets/Characters/Josh/Hands/josh_hand_impact_fx.png", frame = Vector2(160, 96),
	pivot = Vector2(80, 48), frame_times = [0.05, 0.06, 0.07, 0.10]}

#THE SUMMON (JoshCardsSummon), seconds from its start
# The flurry: `cards` a portal, a side at a time, card_gap apart, each card_flight long up an arc whose control point
# is arc_rise px over the middle of its chord; it shrinks to shrink_to over the last shrink_share of its flight and
# fades over the last fade_share. The quick one, on a retry in the same run, has no flurry.
const SUMMON := {open = 0.20, flurry = 0.55, cards = 8, card_gap = 0.05, card_flight = 0.40, form = 1.70, idle = 2.30,
	end = 2.50, open_speed = 1.0, form_speed = 1.0, arc_rise = 160.0, shrink_to = 0.4, shrink_share = 0.30,
	fade_share = 0.15, card_z = 2, open_shake = {strength = 4.0, steps = 3, step = 0.03}}
const SUMMON_QUICK := {open = 0.0, form = 0.10, end = 0.60, open_speed = 1.5, form_speed = 1.5,
	open_shake = {strength = 4.0, steps = 3, step = 0.03}}
const SUMMON_SEEN_KEY := "res://Scenes/Bosses/JoshBossFightScene.tscn#summon"
# Where the flurry's cards leave his hands on summon_hold's frames (josh_summon 2 and 3), texels on his 80x80 frames
# drawn facing right, the hand on the frame's left feeding the left portal. Any other frame - his placeholder's -
# throws from frame 2's.
const SUMMON_CARD_ORIGIN := {
	2: {&"left": Vector2(14, 17), &"right": Vector2(66, 17)},
	3: {&"left": Vector2(14, 16), &"right": Vector2(67, 16)},
}

#THE HAND SLAM (JoshCardsHandSlam; its timings are the state machine's hand_* exports)
# Out of the portals, a hand's height swells by FLY_ARC px at the middle of its flight.
const FLY_ARC := 60.0
# The red badge's tip never goes above this, so the badge stays in view over a spot by the top rope.
const BADGE_TOP_MIN := 84.0
# A deck spot's x stays inside this, or the hand waits on the player's other side: the air box's wider half (159) and
# AIR_SIDE_MIN in from either edge of the view, so a waiting hand's box never crosses it.
const DECK_X := Vector2(167, 1753)

#ON SCREEN (JoshHand.place_air; the addendum of 2026-09-29)
# A hand in the air keeps its box this far inside the view: at the back rope its lift is clamped (max_lift), and off a
# side rope it leans in (lean). Its floor point never moves, so neither does the mark, the footprint or the badge, and
# a player at the back is still slammed. Where a hand in the air or on the floor covers the player, the player shows
# through it at XRAY_ALPHA (JoshHand's x-ray mask); Josh gets no x-ray.
const AIR_TOP_MIN := 8.0
const AIR_SIDE_MIN := 8.0
const XRAY_ALPHA := 0.8

#THE GUN HANDS (JoshGunHands, a layer inside Wild Cards; the addendum of 2026-09-29)
# The hands as finger guns at the sides of the ring, drawn as the right-side hand pointing LEFT into the ring (the
# giant's left hand, the approved handedness), the left its mirror, on the hands' own 128x128 frame and pivot. Each
# clip's sheet is josh_hand_gun_<clip>.png with an optional additive _glow; the gun art plays once all four are in
# (final_gun), and until then each clip stands in off an approved hand clip turned a quarter so its fingers point into
# the ring (GUN_TURN; gun_form turns it as it plays, gun_charge holds windup's last frame, gun_fire's recoil is code).
# Totals are the gameplay's: gun_form 0.40 (backwards, it unfolds) and gun_fire 0.35 (its last frame held).
const GUN_CLIPS := {
	&"gun_form": {times = [0.05, 0.06, 0.07, 0.07, 0.07, 0.08], loop = false, stand_in = &"hover"},
	&"gun_idle": {times = [0.10, 0.10, 0.10, 0.10], loop = true, stand_in = &"hover"},
	&"gun_charge": {times = [0.08, 0.08, 0.08, 0.08], loop = true, stand_in = &"windup"},
	&"gun_fire": {times = [0.05, 0.08, 0.10, 0.12], loop = false, stand_in = &"hover"},
}
# Degrees the stand-ins turn, on the hand's own (unmirrored) art: its mirror turns the left hand's the other way.
const GUN_TURN := 90.0
# The stand-in fire's kick back from the muzzle, px, spent over gun_fire.
const GUN_RECOIL := 12.0
# The gun art's numbers (art_source/josh_hands/approval_gun/contract.json, 2026-09-29). The muzzle: the corner point the
# beam leaves from, where the fingertips end, on the pivot's row, so a beam's row is its hand's own y. The gun's box
# round the pivot, texels, every idle, charge and fire frame with its glow: 45 above the muzzle's row, 20 below, the
# muzzle 66 from the cuff's edge. The posts and the rows are worked out from these, never typed in.
const GUN_MUZZLE := Vector2(30, 70)
const GUN_BOX_TEXELS := Rect2(-40, -45, 72, 65)
const GUN_BOX := Rect2(GUN_BOX_TEXELS.position * SCALE, GUN_BOX_TEXELS.size * SCALE)
# gun_form's box on each of its frames, texels round the pivot, glow included: measured off the shipped
# josh_hand_gun_form.png and josh_hand_gun_form_glow.png (2026-09-29), and held to them by josh_guns' art tier. Its first
# frame is the hover hand, the widest; its last is gun_idle's first, inside the gun's box.
const GUN_FORM_BOXES_TEXELS: Array[Rect2] = [
	Rect2(-41, -40, 79, 79), Rect2(-36, -39, 71, 76), Rect2(-29, -33, 58, 64),
	Rect2(-32, -35, 59, 59), Rect2(-34, -41, 63, 60), Rect2(-35, -43, 63, 62),
]
# Each beam runs from its muzzle to the far rope's outer edge (ArenaScene's wallBoundaries), BEAM_HALF either side of
# its row: the beam art's height, 20 texels, is the hit band.
const GUN_FAR_ROPE := {&"left": 1820.0, &"right": 100.0}
const BEAM_HALF := 30.0
# Where the rows are chosen (JoshGunHands.choose_rows): the far hand is the one across the ring's middle from the
# player; the cut-off row goes toward the side with more floor (the ropes' top and bottom); and two bands keep at least
# a band and the player's hurtbox (its size here) apart. The state machine's gun_row_offset leaves more than
# GUN_STAND_ROOM px of rows between two bands for the hurtbox to stand in.
const GUN_RING_MID_X := 959.0
const GUN_FLOOR := Vector2(114, 967)
const PLAYER_HURT := Vector2(36, 81)
const GUN_STAND_ROOM := 40.0
# The beam, drawn pointing left (the left hand's is mirrored), 3 frames of 16x20 texels a piece shimmering: start, its
# right edge on the muzzle's column; a seamless tile repeated to the end; end, its left edge on the far rope; and an
# optional additive glow of 16x32 along all of it. Each piece's pivot (texels) is on its row's centre line. Drawn once
# start, tile and end are all in (final_beam); until then a crimson band with a white core and an added glow. The fade
# is code.
const GUN_BEAM := {start = HAND_DIR + "josh_gun_beam_start.png", tile = HAND_DIR + "josh_gun_beam_tile.png",
	end = HAND_DIR + "josh_gun_beam_end.png", glow = HAND_DIR + "josh_gun_beam_glow.png", frame = Vector2(16, 20),
	frames = 3, frame_time = 0.05, start_pivot = Vector2(16, 10), tile_pivot = Vector2(0, 10), end_pivot = Vector2(0, 10),
	glow_frame = Vector2(16, 32), glow_pivot = Vector2(0, 16)}
const PLACEHOLDER_BEAM := {band = Color("#C2283A"), core = Color(1.0, 1.0, 1.0), core_width = 12.0, glow = Color("#7A1F2B"),
	glow_half = 48.0}
# The muzzle flash as it fires, and the charge effect while it charges, on the muzzle (texels); a star and a pulsing
# added circle until each is in. The charge grows over the charge through whole-number scales, an equal share of it
# each, so its pixels stay square (the user's pick, 2026-09-29), ending on SCALE like everything else.
const GUN_FLASH := {texture = HAND_DIR + "josh_gun_flash.png", frame = Vector2(48, 48), pivot = Vector2(24, 24),
	frame_times = [0.04, 0.05, 0.06, 0.08]}
const GUN_CHARGE_FX := {texture = HAND_DIR + "josh_gun_charge_fx.png", frame = Vector2(32, 32), pivot = Vector2(16, 16),
	frames = 6, frame_time = 0.08}
const PLACEHOLDER_FLASH := {points = 8, outer = 60.0, inner = 24.0, color = Color("#FFF3B0")}
const PLACEHOLDER_CHARGE := {radius = 30.0, pulse_time = 0.25, low = 0.4, color = Color("#E8605A")}
const GUN_CHARGE_SCALES: Array[int] = [1, 2, 3]
# The telegraph, drawn in code so it is the hit band to the pixel: a fill between two rims on the band's edges, in his
# crimson (never the lanes' gold, never the rune blue), ramping over the charge and flashing in its last flash_time.
const GUN_TELL := {fill = Color("#C2283A"), rim = Color("#E8605A"), flash = Color("#FFF3B0"), fill_from = 0.12,
	fill_to = 0.30, flash_alpha = 0.75, flash_time = 0.10, rim_width = 3.0}

#FAIRNESS (invariants): the player's i-frames (PlayerScript's InvincibilityTimer), PlayerDefense.parry_window, and
# how much longer than the dash immunity's cooldown a landing-to-landing beat must be.
const PLAYER_IFRAMES := 1.0
const PARRY_WINDOW := 0.24
const DASH_LEAD := 0.1
# The lock's lead (JoshCardsHandSlam._aim) against the player's walk on each axis (PlayerScript.SPEED), a learned
# reaction and the margin a player keeps clear of the footprint.
const WALK_SPEED := 600.0
const REACTION := 0.20
const ESCAPE_MARGIN := 25.0

#SOUNDS (stand-ins off the shared set, each only if its file is in)
const SOUNDS := {
	&"portal_open": {stream = "res://Assets/Audio/SFX/laser_charge.ogg", pitch = 1.4, volume_db = 0.0, voices = 1},
	&"portal_close": {stream = "res://Assets/Audio/SFX/laser_charge.ogg", pitch = 0.8, volume_db = -6.0, voices = 1},
	&"card_in": {stream = "res://Assets/Audio/SFX/whirlwind_whoosh.ogg", pitch = 2.0, volume_db = -12.0, voices = 3},
	&"hand_form": {stream = "res://Assets/Audio/SFX/whirlwind_whoosh.ogg", pitch = 0.8, volume_db = 0.0, voices = 1},
	&"hand_lock": {stream = "res://Assets/Audio/SFX/whirlwind_whoosh.ogg", pitch = 1.6, volume_db = 0.0, voices = 1},
	&"hand_slam": {stream = "res://Assets/Audio/SFX/earthquake_slam.ogg", pitch = 1.2, volume_db = 0.0, voices = 1},
	&"hand_shatter": {stream = "res://Assets/Audio/SFX/hit_impact.ogg", pitch = 1.4, volume_db = 0.0, voices = 1},
	&"gun_form": {stream = "res://Assets/Audio/SFX/whirlwind_whoosh.ogg", pitch = 1.3, volume_db = 0.0, voices = 1},
	&"gun_charge": {stream = "res://Assets/Audio/SFX/laser_charge.ogg", pitch = 0.9, volume_db = 0.0, voices = 1},
	&"gun_fire": {stream = "res://Assets/Audio/SFX/matt_trueshot_fire.wav", pitch = 1.2, volume_db = 0.0, voices = 1},
	# His Portal Monte (JoshCardsPortalMonte): the dive, a card flicked to each small gate, a figure bursting out, and a
	# bitten fake (Carter's).
	&"monte_dive": {stream = "res://Assets/Audio/SFX/whirlwind_whoosh.ogg", pitch = 0.7, volume_db = 0.0, voices = 1},
	&"monte_deal": {stream = "res://Assets/Audio/SFX/whirlwind_whoosh.ogg", pitch = 2.2, volume_db = -10.0, voices = 3},
	&"monte_burst": {stream = "res://Assets/Audio/SFX/whirlwind_whoosh.ogg", pitch = 1.6, volume_db = -2.0, voices = 2},
	&"monte_feint": {stream = "res://Assets/Audio/SFX/carter_fake_punish.wav", pitch = 1.0, volume_db = 0.0, voices = 1},
}

#THE PLACEHOLDER COLOURS: his card faces, gold borders and red pips; a wine vortex, never the undead puppet's rune blue.
const PLACEHOLDER := {
	card = Color(1.0, 0.95, 0.85), edge = Color(0.45, 0.32, 0.05), pip = Color(0.8, 0.12, 0.15),
	vortex = Color("#2A0F14"), rim = Color("#F2C94C"), glow = Color("#7A1F2B"),
	mark_rim = Color(1.0, 0.3, 0.2), mark_fill = Color(0.0, 0.0, 0.0, 0.35),
}


static func rest_point(side: StringName) -> Vector2:
	return PORTAL_POINTS[side] + REST_OFFSET


static func other_side(side: StringName) -> StringName:
	return &"right" if side == &"left" else &"left"


# Whether `point` is inside the footprint round `centre`.
static func footprint_covers(centre: Vector2, point: Vector2) -> bool:
	return ((point - centre) / FOOTPRINT).length_squared() <= 1.0


#THE PORTALS' SHEETS

static func portal_sheet(sequence: StringName, layer: StringName) -> String:
	return PORTAL_DIR + "josh_portal_%s_%s.png" % [sequence, layer]


static func final_portal() -> bool:
	if not USE_FINAL_PORTAL:
		return false
	for sequence in PORTAL_REQUIRED:
		for layer in PORTAL_LAYERS:
			if not ResourceLoader.exists(portal_sheet(sequence, layer)):
				return false
	return true


static func has_feed() -> bool:
	return PORTAL_LAYERS.all(func(layer: StringName) -> bool: return ResourceLoader.exists(portal_sheet(&"feed", layer)))


static func sequence_time(sequence: StringName) -> float:
	var total := 0.0
	for time: float in PORTAL_SEQUENCES[sequence]:
		total += time
	return total


# The opening's radii, px.
static func opening() -> Vector2:
	return Vector2.ONE * PORTAL.opening * SCALE


#THE HANDS' SHEETS

static func hand_sheet(clip: StringName) -> String:
	return HAND_DIR + "josh_hand_%s.png" % clip


static func hand_glow_sheet(clip: StringName) -> String:
	return HAND_DIR + "josh_hand_%s%s.png" % [clip, HAND_GLOW_SUFFIX]


# What an air frame covers round the pivot, px, for the hand on `side`: the right one's box, mirrored for the left.
static func air_box(side: StringName) -> Rect2:
	if side == &"left":
		return Rect2(-HAND_AIR_BOX.end.x, HAND_AIR_BOX.position.y, HAND_AIR_BOX.size.x, HAND_AIR_BOX.size.y)
	return HAND_AIR_BOX


# The most a hand over a floor point at `floor_y` may be lifted with the top of its box AIR_TOP_MIN inside the view.
static func max_lift(floor_y: float) -> float:
	return maxf(floor_y - AIR_TOP_MIN + HAND_AIR_BOX.position.y, 0.0)


# The least sideways shift, px, that keeps the air box of the hand on `side`, drawn over `pivot_x`, AIR_SIDE_MIN inside
# the view.
static func lean(side: StringName, pivot_x: float) -> float:
	return lean_in(air_box(side), pivot_x)


# The same for any box round the pivot, px.
static func lean_in(box: Rect2, pivot_x: float) -> float:
	var view: Rect2 = JoshArtLayout.VIEW_RECT
	var short_left := view.position.x + AIR_SIDE_MIN - (pivot_x + box.position.x)
	if short_left > 0.0:
		return short_left
	return minf(view.end.x - AIR_SIDE_MIN - (pivot_x + box.end.x), 0.0)


static func final_hand() -> bool:
	if not USE_FINAL_HAND:
		return false
	for clip in HAND_CLIPS:
		if not ResourceLoader.exists(hand_sheet(clip)):
			return false
	return true


static func clip_spec(clip: StringName) -> Dictionary:
	if HAND_CLIPS.has(clip):
		return HAND_CLIPS[clip]
	return GUN_CLIPS[clip] if GUN_CLIPS.has(clip) else HAND_OPTIONAL[clip]


static func clip_time(clip: StringName) -> float:
	var total := 0.0
	for time: float in clip_spec(clip).times:
		total += time
	return total


# What plays `name` on a hand drawn with the final sheets or not: a clip, or an optional one - its own sheet on a
# drawn hand once it is in, and what stands in for it otherwise. {clip, reverse}.
static func motion(name: StringName, final_art: bool) -> Dictionary:
	if HAND_CLIPS.has(name):
		return {clip = name, reverse = false}
	var spec: Dictionary = HAND_OPTIONAL[name]
	if final_art and ResourceLoader.exists(hand_sheet(name)):
		return {clip = name, reverse = false}
	return {clip = spec.stand_in, reverse = spec.reverse}


#THE GUNS

# All four gun sheets are in: a half-drawn set never mixes with the stand-ins.
static func final_gun() -> bool:
	if not final_hand():
		return false
	for clip in GUN_CLIPS:
		if not ResourceLoader.exists(hand_sheet(clip)):
			return false
	return true


static func final_beam() -> bool:
	return [GUN_BEAM.start, GUN_BEAM.tile, GUN_BEAM.end].all(func(path: String) -> bool: return ResourceLoader.exists(path))


# The muzzle, px off the pivot, of the hand on `side` as a gun.
static func gun_muzzle(side: StringName) -> Vector2:
	var offset := (GUN_MUZZLE - HAND.pivot) * SCALE
	return Vector2(-offset.x, offset.y) if side == &"left" else offset


# The gun's box round the pivot, px, for the hand on `side`: the right one's, mirrored for the left.
static func gun_box(side: StringName) -> Rect2:
	if side == &"left":
		return Rect2(-GUN_BOX.end.x, GUN_BOX.position.y, GUN_BOX.size.x, GUN_BOX.size.y)
	return GUN_BOX


# The same for gun_form's frame `frame`.
static func gun_form_box(side: StringName, frame: int) -> Rect2:
	var texels: Rect2 = GUN_FORM_BOXES_TEXELS[frame]
	var box := Rect2(texels.position * SCALE, texels.size * SCALE)
	if side == &"left":
		return Rect2(-box.end.x, box.position.y, box.size.x, box.size.y)
	return box


# Each hand's post, its muzzle's x: the outer (cuff) edge of its box AIR_SIDE_MIN inside the view.
static func gun_posts() -> Dictionary:
	var view: Rect2 = JoshArtLayout.VIEW_RECT
	var right := view.end.x - AIR_SIDE_MIN - gun_box(&"right").end.x + gun_muzzle(&"right").x
	var left := view.position.x + AIR_SIDE_MIN - gun_box(&"left").position.x + gun_muzzle(&"left").x
	return {&"left": left, &"right": right}


# The rows its muzzle may stand on at its post, (top, bottom): its box AIR_TOP_MIN inside the top of the view and clear
# of every HUD block under it, grown by its clearance.
static func gun_row_range(side: StringName) -> Vector2:
	var box := gun_box(side)
	var muzzle := gun_muzzle(side)
	var pivot_x: float = gun_posts()[side] - muzzle.x
	var above := muzzle.y - box.position.y
	var below := box.end.y - muzzle.y
	var view: Rect2 = JoshArtLayout.VIEW_RECT
	var top := view.position.y + AIR_TOP_MIN + above
	var bottom := view.end.y - AIR_TOP_MIN - below
	for block: Rect2 in JoshArtLayout.HUD_KEEP_OUT:
		var grown := block.grow(JoshArtLayout.HUD_CLEARANCE)
		if grown.position.x < pivot_x + box.end.x and grown.end.x > pivot_x + box.position.x and grown.position.y > top:
			bottom = minf(bottom, grown.position.y - below)
	return Vector2(top, bottom)


# Where the pivot of the hand on `side` goes to put its muzzle at its post on `row`.
static func gun_pivot(side: StringName, row: float) -> Vector2:
	return Vector2(gun_posts()[side], row) - gun_muzzle(side)


# Where the beam of the hand on `side`, its muzzle on `row`, hurts: from its muzzle to the far rope's outer edge,
# BEAM_HALF either side of the row. What the telegraph draws, what the hit tests and what the tests measure.
static func gun_band(side: StringName, row: float) -> Rect2:
	var muzzle_x: float = gun_posts()[side]
	var far: float = GUN_FAR_ROPE[side]
	return Rect2(minf(muzzle_x, far), row - BEAM_HALF, absf(far - muzzle_x), 2.0 * BEAM_HALF)


# The lowest centre row the left hand's band still reaches: below it the right hand aims instead.
static func gun_left_reach() -> float:
	return gun_row_range(&"left").y + BEAM_HALF + PLAYER_HURT.y / 2.0


# How far apart two rows must be for a player to stand between their bands.
static func gun_row_gap() -> float:
	return 2.0 * BEAM_HALF + PLAYER_HURT.y


# The charge effect's scale `progress` of the way through the charge.
static func charge_scale(progress: float) -> int:
	var steps := GUN_CHARGE_SCALES.size()
	return GUN_CHARGE_SCALES[clampi(int(progress * steps), 0, steps - 1)]


#THE MARK AND THE IMPACT

static func final_mark() -> bool:
	return USE_FINAL_MARK and ResourceLoader.exists(MARK.texture)


static func final_impact() -> bool:
	return ResourceLoader.exists(IMPACT_FX.texture)


# The burst on a landing, in the shape of JoshArtLayout.FINAL_CARD_BURST, and whether it lies on the floor under the
# hand: its own once it is in, else the fan over the floor point.
static func impact_spec() -> Dictionary:
	if not final_impact():
		return JoshArtLayout.FINAL_CARD_BURST.merged({on_floor = false})
	return {texture = IMPACT_FX.texture, hframes = IMPACT_FX.frame_times.size(), frame_size = IMPACT_FX.frame,
		pivot = IMPACT_FX.pivot, scale = SCALE, frame_times = IMPACT_FX.frame_times, on_floor = true}


#THE SUMMON

# Where the flurry's cards for the portal on `side` leave him, standing at `feet` on sheet frame `frame`: the hand
# drawn on that side, which on a mirrored frame is the frame's other hand.
static func card_origin(side: StringName, feet: Vector2, flipped: bool, frame: int) -> Vector2:
	var hands: Dictionary = SUMMON_CARD_ORIGIN.get(frame, SUMMON_CARD_ORIGIN[2])
	var texel: Vector2 = hands[other_side(side) if flipped else side]
	return feet + JoshArtLayout.local(texel, flipped)


#FAIRNESS

# Landing to landing (a turn) is inside the player's i-frames, so a hit buys the next landing, and a dash's lead over
# the immunity's cooldown, so every landing can be dashed; the badge, lock to landing, outlasts the parry window; a
# landed or parried hand is back on deck before its next turn, and the first track has time to find the player. A
# player walking on through the lock, straight or on the diagonal, lands under the spot, and one who stops a reaction
# after it is ESCAPE_MARGIN clear of the footprint along its wider axis (doubling back or turning only clears it
# further). The
# summon's hands form once its last card is in. The guns reach the top of the ring, their two bands leave room to stand
# between them, and their charge is time enough to step out of a band and longer than their glide onto it.
static func invariants(sm: Node) -> Array[String]:
	var broken: Array[String] = []
	var turn: float = sm.hand_track_time + sm.hand_lock_time + sm.hand_drop_time
	if turn >= PLAYER_IFRAMES:
		broken.append("track + lock + drop (%.2f) is not under the i-frames (%.2f)" % [turn, PLAYER_IFRAMES])
	if turn < AttackCatalog.DASH_IMMUNITY_COOLDOWN + DASH_LEAD - 0.0001:
		broken.append("track + lock + drop (%.2f) is under the dash immunity's cooldown and a lead" % turn)
	if sm.hand_lock_time + sm.hand_drop_time <= PARRY_WINDOW:
		broken.append("lock + drop is not over the parry window")
	if sm.hand_pin_time + sm.hand_rise_time > turn + 0.0001:
		broken.append("pin + rise is longer than a turn")
	if sm.hand_shatter_time + sm.hand_reform_time > turn + 0.0001:
		broken.append("shatter + re-form is longer than a turn")
	if sm.hand_first_track < 0.30 - 0.0001:
		broken.append("the first track is under 0.30 s")
	# A walker at the lock is led by a walk's lead; on the diagonal they walk that on both axes.
	var read: float = sm.hand_lock_time + sm.hand_drop_time
	var led: float = minf(WALK_SPEED * sm.hand_lead_time, sm.hand_lead_max)
	var walked_on := led - WALK_SPEED * read
	if not footprint_covers(Vector2.ZERO, Vector2.ONE * walked_on):
		broken.append("a player walking on through the lock, straight or on the diagonal, lands %.0f px off the spot, outside the footprint" % walked_on)
	var stopped := led - WALK_SPEED * REACTION
	if REACTION >= read or stopped < FOOTPRINT.x + ESCAPE_MARGIN - 0.0001:
		broken.append("a walker stopping a reaction after the lock is %.0f px short of the spot, not %.0f clear of the footprint" % [stopped, ESCAPE_MARGIN])
	var summon: Dictionary = SUMMON
	if summon.form < summon.flurry + (2 * summon.cards - 1) * summon.card_gap + summon.card_flight - 0.0001:
		broken.append("the summon's hands form before its last card is in")
	for side in SIDES:
		var rows := gun_row_range(side)
		if rows.x > rows.y or rows.x > 150.0:
			broken.append("the %s gun's rows %s are empty or don't reach up to y 150" % [side, rows])
	if sm.gun_row_offset <= gun_row_gap() + GUN_STAND_ROOM:
		broken.append("gun_row_offset (%.0f) leaves no room to stand between the bands" % sm.gun_row_offset)
	if sm.gun_charge_time < 0.40 - 0.0001:
		broken.append("the guns' charge is under 0.40 s")
	if sm.gun_glide_time >= sm.gun_charge_time:
		broken.append("the guns' glide onto their rows is not under the charge")
	return broken


static func assert_invariants(sm: Node) -> void:
	var broken := invariants(sm)
	assert(broken.is_empty(), "JoshHandsLayout: %s" % [broken])
