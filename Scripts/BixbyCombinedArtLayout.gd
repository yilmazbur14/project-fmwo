extends RefCounted

# Every number for beast Bixby's combined attack that isn't his own body: the quake ring each pound sends
# out, and the sonic beams his heads scream while he spins. His poses are the pound, spin and dizzy entries
# in BixbyBeastArtLayout. The crack, eruption and wave numbers below are the attack's old pound, which
# nothing plays now; BixbyQuakeCrackScript still reads them.
#
# Points and boxes are in texels on a frame, origin top-left, drawn at BixbyBeastArtLayout.SCALE.

const BixbyBeastArtLayout := preload("res://Scripts/BixbyBeastArtLayout.gd")

const SCALE := BixbyBeastArtLayout.SCALE

#CRACK (the marker a pound plants, drawn flat on the floor around its point)
# bixby_quake_crack.png: 4 frames of 48x24, the impact point at texel (24, 13).
const CRACK_SHEET := preload("res://Assets/Characters/Bixby/bixby_quake_crack.png")
const CRACK_FRAME_SIZE := Vector2(48, 24)
const CRACK_OFFSET := Vector2(0, -1)
# It splits open over the first two frames, then throbs between the last two for the rest of the fuse.
const CRACK_OPEN_TIMES := [0.07, 0.07]
const CRACK_THROB_FRAMES := [2, 3]
const CRACK_THROB_TIME := 0.12
# Cracks are planted a pound apart but burn for different lengths, so the throb tightens over the last of
# a fuse: with three of them lit at once, which one is about to go has to be readable.
const CRACK_RUSH_TIME := 0.6
const CRACK_RUSH_THROB_TIME := 0.06

#BURST (the eruption where the crack was)
# bixby_quake_burst.png: 6 frames of 64x64, the ground contact at texel (32, 52).
const BURST_SHEET := preload("res://Assets/Characters/Bixby/bixby_quake_burst.png")
const BURST_FRAME_SIZE := Vector2(64, 64)
const BURST_OFFSET := Vector2(0, -20)
const BURST_TIMES := [0.045, 0.045, 0.05, 0.055, 0.065, 0.09]
# The broken ground it throws up, around its contact point, and the frames that ground is up on.
const BURST_HIT_SIZE := Vector2(168, 45)
const BURST_HIT_FIRST_FRAME := 1
const BURST_HIT_LAST_FRAME := 4
# The wave tears out of it as the flames go up.
const BURST_WAVE_FRAME := 2

#WAVE (the crest of broken ground the eruption sends out)
# bixby_quake_wave.png: 4 frames of 32x32, the ground line at texel y = 24. The tiles have to be laid
# exactly a frame apart for the ridge to run on without a seam.
const WAVE_SHEET := preload("res://Assets/Characters/Bixby/bixby_quake_wave.png")
const WAVE_FRAME_SIZE := Vector2(32, 32)
const WAVE_OFFSET := Vector2(0, -8)
const WAVE_FRAME_TIME := 0.06
const WAVE_SPACING := 96.0
# How many tiles wide the crest is, so it can be walked around the end of.
const WAVE_TILES := 3
# The broken ground that hurts, centred on a tile's ground point.
const WAVE_HIT_SIZE := Vector2(96, 42)

#QUAKE RING (BixbyQuakeRingScript)
# The wave's crest tiles stood upright round an ellipse centred on his feet, flattened by FLOOR_FLATTEN the
# way the floor is drawn, so the ring lies on the floor the beams sweep. Its radius is the ellipse's
# half-width, in px of the floor; the tiles are this far apart along it, a little under a tile's width so
# they overlap the way Eric's ring segments do.
const RING_TILE_SPACING := 84.0
# It starts under the claws his pound lands on, at texels (33, 151) and (158, 151).
const RING_START_RADIUS := 187.0
# The band that hurts, either side of the ellipse, in px of the floor. Broadside that is 3/4 of a tile's
# width; where the ring runs across the screen the floor flattens it with the rest.
const RING_HURT_HALF_WIDTH := 36.0
# What of the player it hurts: the foot of their hurtbox, this many px of it. The ring lies on the floor
# and crosses the screen at a third of its speed, so a band touching the top of the hurtbox is still a
# second away from the player's feet: that far behind them on the floor, it hasn't reached them.
const RING_FOOT_HEIGHT := 12.0
# A tile is drawn only while its whole crest (texel rows 6-28, ground on row 24) stays inside the ropes, but
# the band hurts everywhere up to them, as Eric's does.
const RING_VISIBLE_AREA := Rect2(161, 168, 1596, 784)
const RING_HURT_AREA := Rect2(105, 105, 1710, 870)

# The ring's own art, or with USE_FINAL_RING off the wave's crest tiles above. bixby_quake_ring.png is a
# stretch of the hurt band, broken ground either side of a hellfire crack: 4 frames of 40x32 across, a row
# per screen tangent down (RING_ROW_TANGENTS). Every frame's pivot is its centre, (20, 16), on the crack's
# centre line at floor level, so a centred sprite with no offset stands on the ellipse, sorts by it, and
# flips about it. Neighbouring segments play frames one apart.
const USE_FINAL_RING := true
const RING_SHEET := "res://Assets/Characters/Bixby/bixby_quake_ring.png"
const RING_FRAMES := 4
const RING_ROWS := 7
const RING_FRAME_TIME := 0.08
# Segments are spaced this many px of the ring's SCREEN arc apart, from its front centre, a multiple of 4 of
# them so there is one on the front, the back and both sides. Spaced by floor angle, as the tiles are, they
# bunch up three times closer up the sides, and snapped to the texel grid on screen so neighbours' texels
# line up with each other and the mat's.
const RING_SEGMENT_ARC := 48.0
const RING_SNAP := 3.0
# Rows by the ring's screen tangent, in degrees from level: each row's upper bound, the last taking the
# rest. Rows 1-5 are drawn rising to the right and flipped where it falls to the right; 0 and 6 never are.
const RING_ROW_TANGENTS := [7.0, 20.3, 35.8, 54.2, 69.7, 83.0]
# Each row's ground as [half-width, top, bottom] in px from the pivot, and the top of what its crack throws
# up. A segment is drawn while its ground stays within the rope art at the sides and the bottom, which draws
# over it there, so the ring runs on under the ropes, and while its crest stays under the top rope.
const RING_GROUND_BOXES := [[45, -15, 15], [57, -27, 24], [60, -24, 24], [60, -36, 30], [51, -42, 39],
	[45, -48, 45], [39, -45, 42]]
const RING_CREST_TOPS := [-45, -48, -48, -48, -48, -48, -48]
# The side and bottom ropes' outside edges (their lines are 21 px thick), and the top rope's inside one.
const RING_ROPE_ART := Rect2(92, 114, 1734, 874)
# The screen arc of the unit ellipse, sampled from its front centre, built once for every ring.
const RING_ARC_SAMPLES := 4096

#SONIC BEAMS
# bixby_sonic_beam.png: 4 frames of 128x48 pointing right, a perfect loop, with the mouth at texel (2, 24).
# One beam per head.
const SONIC_BEAMS := 3
const BEAM_SHEET := preload("res://Assets/Characters/Bixby/bixby_sonic_beam.png")
const BEAM_FRAME_SIZE := Vector2(128, 48)
const BEAM_OFFSET := Vector2(62, 0)
const BEAM_FRAME_TIME := 0.045
# How far it reaches past the mouth, and how thick its cone reads halfway along, both in texels.
const BEAM_REACH := 126.0
const BEAM_HIT_THICKNESS := 26.0
# They come out of his maws over his lead-in, and die away over the whole wobble he stops on, following
# his mouths round all the while: the scream trails off rather than being cut.
const BEAM_GROW_TIME := 0.09
const BEAM_FADE_TIME := 0.5

#SONIC LANES (BixbySonicLanesScript)
# The spin's warning: each beam's band laid flat on the floor where it will come out (beam_band),
# BEAM_HIT_THICKNESS across, drawn in code in the shower markers' contract, which is the nugget target's: the
# first two looks a quarter of the warning each, then the last two flashing LANE_FLASH_TIME apart. The beams'
# own blues, going white-hot. Each look is [fill, rim, rim width in px].
const LANE_LOOKS := [
	[Color("#3F3F74", 0.28), Color("#5B6EE1", 0.6), 3.0],
	[Color("#3F3F74", 0.38), Color("#639BFF", 0.9), 3.0],
	[Color("#5FCDE4", 0.35), Color("#FFFFFF", 1.0), 6.0],
	[Color("#3F3F74", 0.38), Color("#5FCDE4", 1.0), 6.0],
]
const LANE_FLASH_TIME := 0.075
# The beams grow out over the bands, and the bands fade out under them as they do.
const LANE_FADE_TIME := BEAM_GROW_TIME

# The beams sweep in the floor plane, which the arena camera sees at a shallow angle: this is how much
# that squashes the sweep on screen, and how long a beam reads once foreshortened, as a multiple of
# BEAM_REACH - longest broadside, shortest pointing at or away from the camera. They reach the ropes now
# (beam_reach), so the length is only what a mouth outside the ropes would fall back to.
const FLOOR_FLATTEN := 0.36
const BEAM_LENGTH_MIN := 0.45
const BEAM_LENGTH_SPAN := 1.55
# Drawn, a beam pointing at the camera is a stub (0.22 here). His maws are 240px above his feet, so that
# stub never even reached the floor in front of him: it is flattened less than the sweep itself.
const BEAM_LENGTH_DEPTH := 0.45
# Every beam is stretched by this on top of that shape, so a broadside one reaches most of the way across
# the arena: drawn at its own length, a corner of the floor would be out of the scream altogether.
const BEAM_REACH_STRETCH := 1.25

# The point his three heads orbit while he spins: the mouths of every loop frame average out on it.
const SPIN_CENTRE := Vector2(84.0, 71.4)

# Each head's mouth on a frame of bixby_spin.png, as [azimuth in degrees, texel x, texel y, near the
# camera]. Frame 0 is the crouch before his maws light up, so it has none; 2-5 are the placeholder loop.
const MOUTH_ANCHORS := {
	1: [[-20.0, 133.7, 66.4, false], [100.0, 72.6, 85.9, true], [220.0, 45.7, 62.0, false]],
	2: [[0.0, 136.0, 71.4, true], [120.0, 55.9, 84.1, true], [240.0, 60.1, 58.7, false]],
	3: [[30.0, 127.8, 78.7, true], [150.0, 37.8, 78.7, true], [270.0, 86.4, 56.7, false]],
	4: [[60.0, 107.9, 84.1, true], [180.0, 32.0, 71.4, true], [300.0, 112.1, 58.7, false]],
	5: [[90.0, 81.6, 86.1, true], [210.0, 40.2, 64.1, false], [330.0, 130.2, 64.1, false]],
	6: [[132.0, 47.4, 82.3, true], [252.0, 70.2, 57.4, false], [12.0, 134.4, 74.5, true]],
	7: [[172.0, 32.2, 73.4, true], [292.0, 105.7, 57.8, false], [52.0, 114.1, 83.0, true]],
}
# The same for bixby_spin_slow.png, whose frame numbers overlap those, from the artist's orbit:
# x = 84 + 52 cos a - 2.4 sin a, y = 71.4 + 14.68 sin a, near while sin a >= 0. Its frames 0, 6, 12 and 18
# are bixby_spin.png's 2, 3, 4 and 5.
const SLOW_MOUTH_ANCHORS := {
	0: [[0.0, 136.0, 71.4, true], [120.0, 55.9, 84.1, true], [240.0, 60.1, 58.7, false]],
	1: [[5.0, 135.6, 72.7, true], [125.0, 52.2, 83.4, true], [245.0, 64.2, 58.1, false]],
	2: [[10.0, 134.8, 73.9, true], [130.0, 48.7, 82.6, true], [250.0, 68.5, 57.6, false]],
	3: [[15.0, 133.6, 75.2, true], [135.0, 45.5, 81.8, true], [255.0, 72.9, 57.2, false]],
	4: [[20.0, 132.0, 76.4, true], [140.0, 42.6, 80.8, true], [260.0, 77.3, 56.9, false]],
	5: [[25.0, 130.1, 77.6, true], [145.0, 40.0, 79.8, true], [265.0, 81.9, 56.8, false]],
	6: [[30.0, 127.8, 78.7, true], [150.0, 37.8, 78.7, true], [270.0, 86.4, 56.7, false]],
	7: [[35.0, 125.2, 79.8, true], [155.0, 35.9, 77.6, true], [275.0, 90.9, 56.8, false]],
	8: [[40.0, 122.3, 80.8, true], [160.0, 34.3, 76.4, true], [280.0, 95.4, 56.9, false]],
	9: [[45.0, 119.1, 81.8, true], [165.0, 33.2, 75.2, true], [285.0, 99.8, 57.2, false]],
	10: [[50.0, 115.6, 82.6, true], [170.0, 32.4, 73.9, true], [290.0, 104.0, 57.6, false]],
	11: [[55.0, 111.9, 83.4, true], [175.0, 32.0, 72.7, true], [295.0, 108.2, 58.1, false]],
	12: [[60.0, 107.9, 84.1, true], [180.0, 32.0, 71.4, true], [300.0, 112.1, 58.7, false]],
	13: [[65.0, 103.8, 84.7, true], [185.0, 32.4, 70.1, false], [305.0, 115.8, 59.4, false]],
	14: [[70.0, 99.5, 85.2, true], [190.0, 33.2, 68.9, false], [310.0, 119.3, 60.2, false]],
	15: [[75.0, 95.1, 85.6, true], [195.0, 34.4, 67.6, false], [315.0, 122.5, 61.0, false]],
	16: [[80.0, 90.7, 85.9, true], [200.0, 36.0, 66.4, false], [320.0, 125.4, 62.0, false]],
	17: [[85.0, 86.1, 86.0, true], [205.0, 37.9, 65.2, false], [325.0, 128.0, 63.0, false]],
	18: [[90.0, 81.6, 86.1, true], [210.0, 40.2, 64.1, false], [330.0, 130.2, 64.1, false]],
	19: [[95.0, 77.1, 86.0, true], [215.0, 42.8, 63.0, false], [335.0, 132.1, 65.2, false]],
	20: [[100.0, 72.6, 85.9, true], [220.0, 45.7, 62.0, false], [340.0, 133.7, 66.4, false]],
	21: [[105.0, 68.2, 85.6, true], [225.0, 48.9, 61.0, false], [345.0, 134.8, 67.6, false]],
	22: [[110.0, 64.0, 85.2, true], [230.0, 52.4, 60.2, false], [350.0, 135.6, 68.9, false]],
	23: [[115.0, 59.8, 84.7, true], [235.0, 56.1, 59.4, false], [355.0, 136.0, 70.1, false]],
}
# The anchors of the sheet his spin loop is drawn on (BixbyBeastArtLayout.SPIN_LOOP).
const LOOP_MOUTH_ANCHORS := SLOW_MOUTH_ANCHORS if BixbyBeastArtLayout.USE_FINAL_SPIN else MOUTH_ANCHORS


# The screen angle a beam fired straight out of a head at this azimuth reads at.
static func beam_angle(azimuth: float) -> float:
	return atan2(sin(azimuth) * FLOOR_FLATTEN, cos(azimuth))


# The azimuth of the head whose beam reads at this screen angle: the other way round beam_angle.
static func floor_azimuth(screen_angle: float) -> float:
	return atan2(sin(screen_angle) / FLOOR_FLATTEN, cos(screen_angle))


# How far it reads along that angle, as a multiple of BEAM_REACH.
static func beam_length(azimuth: float) -> float:
	return BEAM_REACH_STRETCH * (BEAM_LENGTH_MIN
		+ BEAM_LENGTH_SPAN * Vector2(cos(azimuth), sin(azimuth) * BEAM_LENGTH_DEPTH).length())


# How far a beam out of a mouth at `from`, reading at screen angle `angle`, runs before it is over the
# ropes. A mouth already outside them (he is drawn tall, and can stand right against the back rope) is
# left to scream as far as it likes.
static func room_to_ropes(from: Vector2, angle: float, ropes: Rect2) -> float:
	if not ropes.has_point(from):
		return INF
	var along := Vector2.RIGHT.rotated(angle)
	var room := INF
	if absf(along.x) > 0.001:
		room = minf(room, ((ropes.end.x if along.x > 0.0 else ropes.position.x) - from.x) / along.x)
	if absf(along.y) > 0.001:
		room = minf(room, ((ropes.end.y if along.y > 0.0 else ropes.position.y) - from.y) / along.y)
	return room


# How far a full-grown beam out of a mouth at `from`, pointing along screen angle `angle` for a head at
# `azimuth`, runs: right up to the ropes, whichever way it points and wherever he spins (the user, 2026-09-28:
# the spin reaches the full length of the arena). Only a mouth outside the ropes, which his bounds keep from
# happening while he spins, falls back to the drawn length the art reads at (beam_length).
static func beam_reach(azimuth: float, from: Vector2, angle: float, ropes: Rect2) -> float:
	var room := room_to_ropes(from, angle, ropes)
	return room if room < INF else BEAM_REACH * SCALE * beam_length(azimuth)


# The full-grown beam out of `mouth`, in MOUTH_ANCHORS' form, with his feet at `feet`: [where it leaves his
# maw, its screen angle, its length], in px. What the sweep hurts, and what the spin's warning lays down.
static func beam_band(mouth: Array, feet: Vector2, ropes: Rect2) -> Array:
	var azimuth := deg_to_rad(mouth[0])
	var origin := feet + BixbyBeastArtLayout.local(Vector2(mouth[1], mouth[2]))
	var angle := beam_angle(azimuth)
	return [origin, angle, beam_reach(azimuth, origin, angle, ropes)]


# His mouths `into` seconds through step `step` of the spin loop, in MOUTH_ANCHORS' form. Each head glides
# from its maw on that frame to its maw on the next, so the beams turn as smoothly as the rate he spins
# at, not a frame at a time.
static func loop_mouths(step: int, into: float) -> Array:
	var loop: Dictionary = BixbyBeastArtLayout.SPIN_LOOP
	var frames: Array = loop.frames
	var turned := clampf(into / BixbyBeastArtLayout.spin_step_time(), 0.0, 1.0)
	var next_frame: Array = LOOP_MOUTH_ANCHORS[frames[(step + 1) % frames.size()]]
	var mouths := []
	for anchor in LOOP_MOUTH_ANCHORS[frames[step]]:
		var coming: Array = _head_nearest(next_frame, anchor[0] + loop.step_degrees)
		mouths.append([anchor[0] + loop.step_degrees * turned, lerpf(anchor[1], coming[1], turned),
			lerpf(anchor[2], coming[2], turned), anchor[3] if turned < 0.5 else coming[3]])
	return mouths


static var _arc_angles := PackedFloat64Array()
static var _arc_lengths := PackedFloat64Array()


# How many segments a ring this big has: RING_SEGMENT_ARC apart round its screen arc, a multiple of 4.
static func ring_segment_count(radius: float) -> int:
	return 4 * maxi(1, roundi(radius * _ring_perimeter() / (4.0 * RING_SEGMENT_ARC)))


# Each of `count` segments round the ring, evenly spaced along its screen arc from the front centre, as
# [floor angle, sheet row, flip_h]. The same for every ring with that many.
static func ring_segments(count: int) -> Array:
	var out := []
	var perimeter := _ring_perimeter()
	for i in count:
		var theta := _ring_angle_at(perimeter * i / count)
		var tangent := rad_to_deg(atan2(FLOOR_FLATTEN * absf(cos(theta)), absf(sin(theta))))
		var row := RING_ROW_TANGENTS.size()
		for bucket in RING_ROW_TANGENTS.size():
			if tangent < RING_ROW_TANGENTS[bucket]:
				row = bucket
				break
		out.append([theta, row, row >= 1 and row <= RING_ROWS - 2 and sin(theta) * cos(theta) < 0.0])
	return out


# Whether a segment standing at `at` on screen, on sheet row `row`, is drawn (RING_GROUND_BOXES), inside `rope_art`
# (Liam's fire rings pass their own, which starts under his row).
static func ring_segment_shown(at: Vector2, row: int, rope_art := RING_ROPE_ART) -> bool:
	var ground: Array = RING_GROUND_BOXES[row]
	return at.x - ground[0] >= rope_art.position.x and at.x + ground[0] <= rope_art.end.x \
		and at.y + ground[2] <= rope_art.end.y and at.y + RING_CREST_TOPS[row] >= rope_art.position.y


# The unit ellipse's screen perimeter, and the floor angle `length` of its screen arc on from the front centre
# lands on: a table sampled once from PI / 2 round, then searched.
static func _ring_perimeter() -> float:
	_build_ring_arc()
	return _arc_lengths[RING_ARC_SAMPLES]


static func _ring_angle_at(length: float) -> float:
	_build_ring_arc()
	var low := 0
	var high := RING_ARC_SAMPLES
	while high - low > 1:
		var middle := (low + high) / 2
		if _arc_lengths[middle] <= length:
			low = middle
		else:
			high = middle
	var span := maxf(1e-12, _arc_lengths[high] - _arc_lengths[low])
	return lerpf(_arc_angles[low], _arc_angles[high], (length - _arc_lengths[low]) / span)


static func _build_ring_arc() -> void:
	if not _arc_lengths.is_empty():
		return
	var step := TAU / RING_ARC_SAMPLES
	var speed := PackedFloat64Array()
	for i in RING_ARC_SAMPLES + 1:
		var theta := PI / 2.0 + step * i
		_arc_angles.append(theta)
		speed.append(sqrt(pow(sin(theta), 2.0) + pow(FLOOR_FLATTEN * cos(theta), 2.0)))
	_arc_lengths.append(0.0)
	for i in RING_ARC_SAMPLES:
		_arc_lengths.append(_arc_lengths[i] + 0.5 * (speed[i] + speed[i + 1]) * step)


# The head of a frame's anchors whose azimuth is nearest `azimuth`.
static func _head_nearest(anchors: Array, azimuth: float) -> Array:
	var nearest: Array = anchors[0]
	for anchor in anchors:
		if absf(wrapf(anchor[0] - azimuth, -180.0, 180.0)) < absf(wrapf(nearest[0] - azimuth, -180.0, 180.0)):
			nearest = anchor
	return nearest


# Puts a sheet of frames this size on `sprite`, drawn at the fight's scale around `offset`.
static func dress(sprite: Sprite2D, sheet: Texture2D, frame_size: Vector2, offset: Vector2) -> void:
	sprite.texture = sheet
	sprite.hframes = roundi(sheet.get_width() / frame_size.x)
	sprite.offset = offset
	sprite.scale = Vector2(SCALE, SCALE)
