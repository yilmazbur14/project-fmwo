extends RefCounted

# Every number for beast Bixby's combined attack that isn't his own body: the crack each pound plants, the
# eruption and the ground wave it breaks into, and the sonic beams his heads scream while he spins. His
# poses are the pound, spin and dizzy entries in BixbyBeastArtLayout.
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

# The beams sweep in the floor plane, which the arena camera sees at a shallow angle: this is how much
# that squashes the sweep on screen, and how long a beam reads once foreshortened, as a multiple of
# BEAM_REACH - longest broadside, shortest pointing at or away from the camera.
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

# Each head's mouth on a frame of the spin sheet, as [azimuth in degrees, texel x, texel y, near the
# camera]. Frame 0 is the crouch before his maws light up, so it has none.
const MOUTH_ANCHORS := {
	1: [[-20.0, 133.7, 66.4, false], [100.0, 72.6, 85.9, true], [220.0, 45.7, 62.0, false]],
	2: [[0.0, 136.0, 71.4, true], [120.0, 55.9, 84.1, true], [240.0, 60.1, 58.7, false]],
	3: [[30.0, 127.8, 78.7, true], [150.0, 37.8, 78.7, true], [270.0, 86.4, 56.7, false]],
	4: [[60.0, 107.9, 84.1, true], [180.0, 32.0, 71.4, true], [300.0, 112.1, 58.7, false]],
	5: [[90.0, 81.6, 86.1, true], [210.0, 40.2, 64.1, false], [330.0, 130.2, 64.1, false]],
	6: [[132.0, 47.4, 82.3, true], [252.0, 70.2, 57.4, false], [12.0, 134.4, 74.5, true]],
	7: [[172.0, 32.2, 73.4, true], [292.0, 105.7, 57.8, false], [52.0, 114.1, 83.0, true]],
}


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


# Puts a sheet of frames this size on `sprite`, drawn at the fight's scale around `offset`.
static func dress(sprite: Sprite2D, sheet: Texture2D, frame_size: Vector2, offset: Vector2) -> void:
	sprite.texture = sheet
	sprite.hframes = roundi(sheet.get_width() / frame_size.x)
	sprite.offset = offset
	sprite.scale = Vector2(SCALE, SCALE)
