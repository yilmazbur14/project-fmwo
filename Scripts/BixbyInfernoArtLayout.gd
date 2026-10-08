extends RefCounted

# Every number for beast Bixby's Inferno that depends on how it is drawn and isn't his own body: where he
# hangs on the top rope, the fireballs, the flood of fire and the suction streaks. His perch poses are the
# perch entries in BixbyBeastArtLayout.ANIMS.
#
# Points and boxes are in texels on a frame, origin top-left, drawn at BixbyBeastArtLayout.SCALE, unless
# they say px. Until the final art lands the USE_FINAL_* flags stay off and every piece is drawn from the
# PLACEHOLDER_* entries, on the same timing, so the attack plays and reads before any of it exists.

const BixbyBeastArtLayout := preload("res://Scripts/BixbyBeastArtLayout.gd")

const SCALE := BixbyBeastArtLayout.SCALE

#PERCH (bixby_perch.png: 192x160 frames around BixbyBeastArtLayout.ANCHOR, drawn facing down the screen,
# never mirrored)
# The top rope's line on screen: the arena's topWall, and ArenaGate.TOP_AT.
const TOP_ROPE_Y := 100.0
# The texel row of a perch frame the rope's top edge crosses: the white of the rope starts at screen y 100,
# so his feet hang at (960, 445). The arena draws the rope over him, so it is not drawn into the frames.
const PERCH_ROPE_ROW := 36.0
# Nothing on a perch frame may be drawn more rows than this above the rope row, or he leaves the screen.
const PERCH_HEADROOM := 33.0
# EXACTLY the middle of the rope: the art is built around the gate's doorway there (screen x 852..1067).
# His talons grip the rope either side of it, and his middle head rears up through it; anywhere else the
# rope is drawn across his face. The boss bar and its plate over it fade while he is there.
const PERCH_CENTRE_X := 960.0
# The floor layer the flood and the shower's scorches lie on (a burst's from its first frame of scorch),
# like the fights' other floor layers: over the mat (y 99), under anyone standing on it, and under him
# hanging off the rope over it (he sorts at the rope line, y 114).
const FLOOR_LAYER_Y := 101.0
# Where the shower's markers sort. They are its warning, so they lie over him hanging off the rope, where
# the shower follows a player he has dragged onto his belly, but still under anyone standing on the floor
# (a player is never further up it than y 145.5, BixbyBeastStateMachine.PLAYER_FLOOR).
const MARKER_LAYER_Y := 115.0
# His three mouths on each frame of bixby_perch.png: middle, left and right, as the art reports them.
const PERCH_MOUTHS := {
	0: [Vector2(96, 95), Vector2(40, 114), Vector2(151, 114)],
	1: [Vector2(96, 105), Vector2(40, 122), Vector2(151, 122)],
	2: [Vector2(96, 102), Vector2(40, 119), Vector2(151, 119)],
	3: [Vector2(96, 103), Vector2(40, 120), Vector2(151, 120)],
	4: [Vector2(96, 71), Vector2(39, 85), Vector2(152, 85)],
	5: [Vector2(96, 71), Vector2(39, 85), Vector2(152, 85)],
	6: [Vector2(96, 71), Vector2(39, 85), Vector2(152, 85)],
	7: [Vector2(96, 110), Vector2(40, 122), Vector2(151, 122)],
	8: [Vector2(96, 108), Vector2(40, 120), Vector2(151, 120)],
	9: [Vector2(96, 109), Vector2(40, 121), Vector2(151, 121)],
	10: [Vector2(96, 65), Vector2(42, 86), Vector2(149, 86)],
	11: [Vector2(96, 73), Vector2(40, 88), Vector2(151, 88)],
	12: [Vector2(96, 73), Vector2(40, 88), Vector2(151, 88)],
	13: [Vector2(96, 113), Vector2(40, 125), Vector2(151, 125)],
	14: [Vector2(96, 83), Vector2(40, 103), Vector2(151, 103)],
	15: [Vector2(96, 65), Vector2(40, 88), Vector2(151, 88)],
}
# The first inhale frame: the pull and the suction converge on its mouths.
const INHALE_FRAME := 7
# Where the breath's cone comes to a point on the perch_breath frames (11 and 12), above the middle mouth:
# the side maws are drawn sitting on its two edges at the 65 degree half-angle.
const CONE_APEX := Vector2(96, 63)
# The release's last frame is land frame 0's pose drawn this many rows lower, so he drops by it as he lets
# go: the fall starts where the release left him, and land frame 0 stays on screen.
const RELEASE_DROP_ROWS := 2.0

#THE BREATH
# The floor the breath can reach, inside the arena walls. It burns one cone of it, straight down from
# CONE_APEX (BixbyBeastStateMachine.inferno_cone_half_angle), and leaves the upper corners beside him.
const INFERNO_AREA := Rect2(105, 105, 1710, 870)
# The flood fills the cone with tiles on a grid over the whole area: 10x10 beds of 57x29 texels fill it
# exactly, and a tile is laid where its bed's middle is in the cone. A frame is 41 texels tall, the bed in
# its bottom 29 rows and flame tongues allowed into the 12 above. An edge strip runs down both slants,
# mirrored on the left, over the tiles' ragged ends.
const FLOOD_GRID := Vector2i(10, 10)
const FLOOD_TILE := Vector2(57, 29)
const FLOOD_FRAME_SIZE := Vector2(57, 41)
# It catches over its two ignite frames before it hurts, and dies down over its three last ones after.
const FLOOD_IGNITE_TIME := 0.06
const FLOOD_DIE_TIME := 0.45

#FIREBALLS
# Where they come down: anywhere Mason's nuggets can (MasonStateMachine.BOMB_AREA).
const FIREBALL_AREA := Rect2(170, 170, 1580, 720)
# What a landing hurts: the marker's oval around the spot, in px, as the nugget's is.
const FIREBALL_HIT_SIZE := Vector2(132, 66)
const FIREBALL_HIT_POINTS := 32
const FIREBALL_HIT_TIME := 0.1
# The ball is on screen for the last of the warning, falling straight down from just above the screen.
const FIREBALL_FALL_TIME := 0.35
const FIREBALL_FALL_START_Y := -80.0
# The marker's contract is the nugget target's: frames 0 and 1 for a quarter of the warning each, then
# 2 and 3 flashing. Its node sits this far up from the spot and its drawing as far back down, as the
# nugget target's do; where it sorts is MARKER_LAYER_Y.
const MARKER_FLASH_TIME := 0.12
const MARKER_RAISE := 33.0
# The burst it lands in, then the scorch it leaves (bixby_fire_scorch.png, as the fire trail's): lit, then
# fading.
const SCORCH_SMOULDER_TIME := 0.4
const SCORCH_FADE_TIME := 1.0
# The volley's fireballs free themselves once they are this far above the top of the screen.
const RISE_OFF_SCREEN_Y := -60.0

#EMBERS (BixbyEmberScript: bixby_fire_trail.png and bixby_fire_scorch.png, 40x40 frames at 3x around the bed's
# centre, texel (20, 31), on the timings the fire breath's trail had)
const EMBER_SCORCH_SHEET := preload("res://Assets/Characters/Bixby/bixby_fire_scorch.png")
const EMBER_FRAME_WIDTH := 40
# What hurts, centred on the ember: the burning bed, texels (4, 26) to (35, 35).
const EMBER_SIZE := Vector2(96, 30)
const EMBER_IGNITE_FRAMES := [0, 1, 2]
const EMBER_IGNITE_TIMES := [0.07, 0.07, 0.09]
const EMBER_BURN_LOOP_FRAMES := [3, 4, 5, 6]
const EMBER_BURN_LOOP_TIME := 0.11
const EMBER_BURN_OUT_FRAMES := [7, 8, 9]
const EMBER_BURN_OUT_TIMES := [0.12, 0.14, 0.18]
# It hurts from ignite frame 1 until burn-out frame 2 starts.
const EMBER_HURTS_FROM_IGNITE_STEP := 1
const EMBER_HURTS_UNTIL_BURN_OUT_STEP := 2
# The scorch smoulders on frame 0, then fades out on frame 1.
const EMBER_SCORCH_SMOULDER_TIME := 0.4
const EMBER_SCORCH_FADE_TIME := 1.0

#FINAL ART
const USE_FINAL_FIREBALL := true
const USE_FINAL_FLOOD := true
const USE_FINAL_SUCTION := true
# bixby_fireball.png: row 0 rising (trail below), row 1 falling (trail above), 16x24 frames. The ball's
# middle is at (8, 7) rising and (8, 17) falling, so each row's offset puts it on the node.
# bixby_fireball_marker.png: 44x22 frames, the oval filling the frame, exactly the hit oval.
# bixby_fireball_impact.png: 48x40 frames, ground contact at (24, 28); its last two frames sit on the
# scorch's own pixels, so the scorch takes over without a pop. Its flames are drawn over everyone, as the
# falling ball is; from impact_scorch_step on it is the scorch, so it lies on the floor layer with it.
const FINAL_FIREBALL := {
	"ball": "res://Assets/Characters/Bixby/bixby_fireball.png",
	"ball_frame_size": Vector2(16, 24),
	"ball_frames": 4,
	"ball_frame_time": 0.06,
	"rise_offset": Vector2(0, 5),
	"fall_offset": Vector2(0, -5),
	"marker": "res://Assets/Characters/Bixby/bixby_fireball_marker.png",
	"marker_frame_size": Vector2(44, 22),
	"impact": "res://Assets/Characters/Bixby/bixby_fireball_impact.png",
	"impact_frame_size": Vector2(48, 40),
	"impact_frames": [0, 1, 2, 3, 4],
	"impact_scorch_step": 3,
	"impact_times": [0.06],
	"impact_offset": Vector2(0, -8),
}
# bixby_inferno_flood.png: 57x41 frames, smoulder 0-1, ignite 2-3, burn 4-7 (seamless tiled both ways, and
# only unflipped), die-down 8-10. The ignite and die-down frames share FLOOD_IGNITE_TIME and FLOOD_DIE_TIME.
# bixby_inferno_edge.png: 30x48 frames on the flood's phases frame for frame. Drawn for the 65 degree
# half-angle: each piece's edge line drops 14 of its 30 texels, from its pivot at (0, 22), and a 3-5 texel
# band under the line hides where the flood is cut. Pieces are laid unrotated down the right slant from the
# apex, a piece's width apart; the left slant's are flipped, pivot (30, 22). At another half-angle they
# still run down the cone, but their drawn line no longer meets end to end.
# bixby_inferno_burst.png: 64x64 frames, the three streams meeting at (32, 30) - the middle one comes in at
# (32, 0), the side ones at (0, 16) and (63, 16). Ignite 0-1, burn loop 2-4, die 5-6.
const FINAL_FLOOD := {
	"sheet": "res://Assets/Characters/Bixby/bixby_inferno_flood.png",
	"smoulder": [0, 1],
	"ignite": [2, 3],
	"burn": [4, 5, 6, 7],
	"die": [8, 9, 10],
	"frame_time": 0.11,
	# The strong smoulder of the wind-up flickers faster than the faint one, on the same two frames.
	"warn_frame_time": 0.06,
	"faint_alpha": 0.45,
	"edge_sheet": "res://Assets/Characters/Bixby/bixby_inferno_edge.png",
	"edge_frame_size": Vector2(30, 48),
	"edge_pivot": Vector2(0, 22),
	"burst_sheet": "res://Assets/Characters/Bixby/bixby_inferno_burst.png",
	"burst_frame_size": Vector2(64, 64),
	"burst_offset": Vector2(0, 2),
	"burst_ignite": [0, 1],
	"burst_burn": [2, 3, 4],
	"burst_die": [5, 6],
	"burst_ignite_time": 0.03,
	"burst_burn_time": 0.07,
	"burst_die_time": 0.15,
}
# Where the burst's pivot sits from CONE_APEX, in px: on the perch art's apex itself.
const BURST_ANCHOR_OFFSET := Vector2.ZERO
# bixby_suction.png: rows at 0, 45 and 90 degrees (right, down-right, down), 4 frames of 24x24 each around
# (12, 12), every streak flying toward its bright head; the other five directions are flips.
const FINAL_SUCTION := {
	"sheet": "res://Assets/Characters/Bixby/bixby_suction.png",
	"frame_size": Vector2(24, 24),
	"frames": 4,
	"frame_time": 0.05,
}

#PLACEHOLDERS
# The fireball: the fire trail's burning frames falling and igniting, and a yellow oval for the marker,
# drawn in the nugget target's four frames.
const FIRE_TRAIL_SHEET := "res://Assets/Characters/Bixby/bixby_fire_trail.png"
const FIRE_TRAIL_FRAMES := 10
const FIRE_SCORCH_SHEET := "res://Assets/Characters/Bixby/bixby_fire_scorch.png"
const FIRE_SCORCH_FRAMES := 2
const PLACEHOLDER_FIREBALL := {
	"ball_frames": [3, 4, 5, 6],
	"ball_frame_time": 0.06,
	# Rows 11 up from the bed's centre, the same as the fire trail patch's.
	"ball_offset": Vector2(0, -11),
	"impact_frames": [0, 1, 2, 7, 8, 9],
	# The trail's frames 8 and 9 are its burnt-out oval.
	"impact_scorch_step": 4,
	"impact_times": [0.05],
	"impact_offset": Vector2(0, -11),
	# [colour, width in px] per marker frame.
	"marker": [
		[Color(1.0, 0.86, 0.25, 0.35), 3.0],
		[Color(1.0, 0.86, 0.25, 0.65), 3.0],
		[Color(1.0, 0.95, 0.45, 1.0), 4.0],
		[Color(1.0, 0.62, 0.12, 0.6), 4.0],
	],
}
# The flood: the cone laid flat, coloured by what it is doing.
const PLACEHOLDER_FLOOD := {
	"faint": Color(0.85, 0.25, 0.05, 0.12),
	# The wind-up pulses between these two, this many times a second.
	"warn": Color(1.0, 0.45, 0.05, 0.28),
	"warn_peak": Color(1.0, 0.55, 0.1, 0.5),
	"warn_rate": 4.0,
	"ignite": Color(1.0, 0.9, 0.45, 0.85),
	"burn": Color(1.0, 0.42, 0.08, 0.72),
	"burn_peak": Color(1.0, 0.6, 0.15, 0.8),
	"burn_rate": 9.0,
	"die": Color(0.7, 0.2, 0.05, 0.6),
	# The slants, in this colour at the fill's alpha and half again, so the cone's edge is what reads.
	"edge": Color(1.0, 0.85, 0.35),
	"edge_width": 10.0,
	# The burst at his mouth while the fire is out: a ragged ring of spikes.
	"burst": Color(1.0, 0.95, 0.6, 0.95),
	"burst_radius": 60.0,
	"burst_spikes": 9,
}
# A suction streak: a short pale line along the way it flies.
const PLACEHOLDER_SUCTION := {
	"colour": Color(0.95, 0.9, 0.8, 0.8),
	"length": 42.0,
	"width": 3.0,
}


# Where his feet hang on the middle of the rope, in px.
static func perch_point() -> Vector2:
	return Vector2(PERCH_CENTRE_X, TOP_ROPE_Y + (BixbyBeastArtLayout.ANCHOR.y - PERCH_ROPE_ROW) * SCALE)


# Mouth `head` (0 middle, 1 left, 2 right) on perch frame `frame`, as a texel on it.
static func perch_mouth(frame: int, head: int) -> Vector2:
	return PERCH_MOUTHS[frame][head]


# The same mouth on screen, in px, with him on the rope.
static func perch_mouth_point(frame: int, head: int) -> Vector2:
	return perch_point() + BixbyBeastArtLayout.local(perch_mouth(frame, head))


# How far he drops as he lets go of the rope, in px.
static func release_drop() -> float:
	return RELEASE_DROP_ROWS * SCALE


# The cone's tip in px, with him on the rope.
static func cone_apex() -> Vector2:
	return perch_point() + BixbyBeastArtLayout.local(CONE_APEX)


# Whether `point` is inside the cone down from `apex`, `half_angle` radians either side of straight down.
static func point_in_cone(point: Vector2, apex: Vector2, half_angle: float) -> bool:
	return (point.y - apex.y) * tan(half_angle) > absf(point.x - apex.x)


# Whether any of `rect` is inside the cone. Exact, not sampled: the cone opens straight down, so the point
# of a box furthest into it is on its bottom edge, at the x nearest the cone's axis, and that one point
# decides it.
static func rect_hits_cone(rect: Rect2, apex: Vector2, half_angle: float) -> bool:
	return point_in_cone(Vector2(clampf(apex.x, rect.position.x, rect.end.x), rect.end.y), apex, half_angle)


# Whether all of `rect` is inside the cone: the cone is convex, so its four corners decide it.
static func rect_inside_cone(rect: Rect2, apex: Vector2, half_angle: float) -> bool:
	for corner in [rect.position, Vector2(rect.end.x, rect.position.y), rect.end, Vector2(rect.position.x, rect.end.y)]:
		if not point_in_cone(corner, apex, half_angle):
			return false
	return true


# The cone where it lies on INFERNO_AREA, in px.
static func cone_polygon(apex: Vector2, half_angle: float) -> PackedVector2Array:
	var reach := INFERNO_AREA.size.length() * 2.0
	var cone := PackedVector2Array([apex, apex + _slant(half_angle, 1.0) * reach, apex + _slant(half_angle, -1.0) * reach])
	var area := PackedVector2Array([INFERNO_AREA.position, Vector2(INFERNO_AREA.end.x, INFERNO_AREA.position.y),
		INFERNO_AREA.end, Vector2(INFERNO_AREA.position.x, INFERNO_AREA.end.y)])
	var clipped := Geometry2D.intersect_polygons(cone, area)
	return clipped[0] if not clipped.is_empty() else PackedVector2Array()


# Where one of its slanted edges, right (`side` 1) or left (-1), leaves INFERNO_AREA, in px.
static func cone_edge_end(apex: Vector2, half_angle: float, side: float) -> Vector2:
	var way := _slant(half_angle, side)
	var wall_x := INFERNO_AREA.end.x if side > 0.0 else INFERNO_AREA.position.x
	return apex + way * minf((wall_x - apex.x) / way.x, (INFERNO_AREA.end.y - apex.y) / way.y)


static func _slant(half_angle: float, side: float) -> Vector2:
	return Vector2(side * sin(half_angle), cos(half_angle))


# The landing's hit oval, in px around the spot.
static func fireball_oval() -> PackedVector2Array:
	var oval := PackedVector2Array()
	for i in FIREBALL_HIT_POINTS:
		oval.append(Vector2.from_angle(TAU * i / FIREBALL_HIT_POINTS) * FIREBALL_HIT_SIZE / 2.0)
	return oval
