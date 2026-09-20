extends RefCounted

# Every number Eric's entrance depends on: how it is drawn, how long each beat runs and what it
# sounds like. EricIntro reads all of it and holds none of its own, so a retimed or redrawn entrance
# only needs this file. Points are in texels on one of his 256x192 frames, origin top-left, the same
# space EricArtLayout measures in.

const EricArtLayout := preload("res://Scripts/EricArtLayout.gd")

#THE SHEET
# eric_entrance.png: frames of 256x192, feet on row 191, body on column 128, front-facing, drawn to
# eric_sheet_v2.png's palette and line weight, and EMPTY-HANDED - the blade he walks up to is the
# one in the mat. The walk is four poses: 0 pass-left, 1 contact-left, 2 pass-right, 3 contact-right,
# looping. Four is enough because he has no drawn limbs to swing - a pauldron and a gauntlet with no
# upper arm between them, and two tasset lobes over a surcoat V with no separated legs anywhere on
# his sheet - so the weight comes from the bob and the timing, not the frame count.
#
# IT SHIPS PARTIAL: the walk is drawn, the grip, heave, pull, raise and point are not, and they
# bring their own frame numbers when they land. So the switch is per pose rather than per sheet -
# the poses that exist come off the real sheet and the rest stay on the stand-in. When the rest
# arrive, their indices join FINAL_ENTRANCE, every value below goes true, `hframes` grows to match,
# and PLACEHOLDER_ENTRANCE and pose()'s two-sheet handling come out; there is no reason to keep a
# path nothing takes.
#
# THE SWORD IS DRAWN FROM THE GRIP FRAME ON. The world sprite hides on it, so that frame's drawn
# sword has to sit exactly where the world sprite stood: PLANT_PIXEL is the one texel the artist and
# this code share.
const USE_FINAL_ENTRANCE_ART := {
	"walk": true,
	"arrive": true,
	"grip": false,
	"heave": false,
	"pull": false,
	"raise": false,
	"point": false,
}
const FINAL_ENTRANCE := {
	"texture": "res://Assets/Characters/Eric/eric_entrance.png",
	# What the sheet holds today. It grows with the poses that are still to be drawn, and their
	# indices are added here with them.
	"hframes": 4,
	"walk": [0, 1, 2, 3],
	# The pose the last plant of the walk lands on, held: the arrival is a stop, not a new frame.
	"arrive": 3,
}
# The poses the real sheet hasn't reached yet come off his own fight sheet: he grips, heaves, pulls
# and points on his sword-throw frames, holding the sword those already draw. He is no longer
# walking in on them - frames 0-8 took that over - so the blade in the mat is the only one on
# screen until he takes it.
const PLACEHOLDER_ENTRANCE := {
	"texture": "res://Assets/Characters/Eric/eric_sheet_v2.png",
	"hframes": EricArtLayout.SHEET_FRAMES,
	"grip": 32,
	"heave": [32, 33],
	"pull": 34,
	"raise": 35,
	"point": [33, 32],
}

#THE PLANTED SWORD
# eric_sword_entrance_planted.png: one frame, native, the blade buried with the hilt at grip height.
# Its own asset - eric_sword_planted_v2.png is how a THROWN blade lands, standing proud of the mat,
# and it keeps doing that job in the fight untouched.
#
# IT IS PLACED BY ITS CONTACT TEXEL, not by a hand-written offset. PLANTED_CONTACT is where the
# blade enters the mat, and planted_offset() works the sprite's own offset out from that and the
# texture's size, so the only thing a redraw can make stale is this one texel - and a redraw that
# only changes the canvas size makes nothing stale at all. The artist has moved this twice.
const PLANTED_SWORD := "res://Assets/Characters/Eric/eric_sword_entrance_planted.png"
const PLANTED_CONTACT := Vector2(32, 46)
# Where that ground contact sits in his frame space: at his boot, on the side he stops beside it. It
# is 32 texels to the VIEWER'S RIGHT of his centreline so he reaches down beside himself rather than
# across his chest - he arrives empty-handed now, so the old reason (his own blade merging with this
# one) no longer applies, but the pose reason does. Burying the blade moved the hilt relative to the
# ground, not the ground itself, so this number did not move with it. Do not revert to 96.
const PLANT_PIXEL := Vector2(160, 186)
# The pose the drawn sword takes the planted one's place on.
const SWORD_HANDOFF_FRAME := "grip"

#THE WALK-IN
# Both fighters are moved by written global_position, so nothing collides and nothing desyncs.
# Eric drops in from this far above his mark; the player rises from this far below theirs.
#
# HE DOES NOT GLIDE IN. He takes WALK_STEPS heavy steps: each one is a push forward and then a plant
# that jolts the ring, with a dwell on the plant before the next. The player's own walk stays a
# plain one - they are the challenger walking up to the ring, not the thing making an entrance.
# The plants get heavier as he closes on the sword: the first lands at WALK_STEP_SHAKE and the last
# one, the one that puts him in reach of the blade, at WALK_STEP_SHAKE_LAST. The thud under it
# ramps the same way, so the arena is loudest and shakiest right before he reaches down.
const WALK_IN_RISE := 420.0
const WALK_STEPS := 6
const WALK_STEP_TIME := 0.26
const WALK_STEP_DWELL := 0.2
const WALK_STEP_SHAKE := 12.0
const WALK_STEP_SHAKE_LAST := 32.0
const WALK_STEP_SHAKE_STEPS := 4
const WALK_STEP_SHAKE_STEP_TIME := 0.03
const WALK_STEP_DB := -9.0
const WALK_STEP_DB_LAST := 1.0
const PLAYER_WALK_DROP := 260.0
const PLAYER_WALK_TIME := 1.6

#BEATS, IN SECONDS
# The ring sits open on the planted sword before anything moves.
const OPEN_BEAT := 0.4
# The player, in the ring, looking at the sword.
const PLAYER_BEAT := 0.5
# After the gates slam, before the first line.
const SETTLE_BEAT := 0.4
# The crowd, through each walk.
const PLAYER_CHEER := 1.6
const ERIC_CHEER := 3.0

#THE PULL
# The beat the whole entrance builds to, so it lands like one of his slams: the crowd goes quiet
# under the heave, and the blade tears out into a dead stop, a hard vertical jolt and a punch-in
# that eases straight back off.
const GRIP_HOLD := 0.35
const HEAVE_TIME := 0.5
const HEAVE_FRAME_TIME := 0.12
const PULL_HOLD := 0.3
const RAISE_HOLD := 0.3
const PULL_HIT_STOP := 0.14
const PULL_SHAKE := 34.0
const PULL_SHAKE_STEPS := 8
const PULL_SHAKE_STEP_TIME := 0.03
const PULL_ZOOM := 1.1
const PULL_ZOOM_TIME := 0.06
const PULL_ZOOM_OUT_TIME := 0.35
const PULL_CHEER := 2.6

#THE POINT
const POINT_HOLD := 0.6
const POINT_FRAME_TIME := 0.5
# The view pushes in on him while he levels the blade, and eases back out when the line ends.
const POINT_ZOOM := 1.12
const POINT_ZOOM_TIME := 0.5
const POINT_ZOOM_OUT_TIME := 0.3
# How far above his origin the push-in is centred. ScreenView clamps the focus inside the arena, so
# a point this high up is pulled back toward the middle anyway; it is a lean, not a framing.
const POINT_FOCUS_RISE := 120.0
const POINT_CHEER := 2.0

#SOUND
# Stand-ins drawn from what the build already has, in EricArtLayout.BREAK_STING_SFX's shape: the
# entrance gets sounds of its own when the sheet does.
const ENTRANCE_SFX := {
	# Its level is the plant's own, ramped across the walk (WALK_STEP_DB): this is the floor.
	"step": {"stream": "res://Assets/Audio/SFX/eric_crash_thud.wav", "pitch": 0.85, "volume_db": -9.0},
	"grip": {"stream": "res://Assets/Audio/SFX/parry_tink_1.wav", "pitch": 0.7, "volume_db": -4.0},
	"heave": {"stream": "res://Assets/Audio/SFX/wrestler_charge.ogg", "pitch": 0.85, "volume_db": -6.0},
	"pull": {"stream": "res://Assets/Audio/SFX/earthquake_slam.ogg", "pitch": 0.95, "volume_db": 0.0},
	"point": {"stream": "res://Assets/Audio/SFX/knight_breaker_sting.wav", "pitch": 1.0, "volume_db": -3.0},
}


# How hard the `step`-th plant of WALK_STEPS lands, 0 first: [shake strength, volume in dB].
static func footfall(step: int) -> Array:
	var weight := float(step) / float(maxi(WALK_STEPS - 1, 1))
	return [lerpf(WALK_STEP_SHAKE, WALK_STEP_SHAKE_LAST, weight), lerpf(WALK_STEP_DB, WALK_STEP_DB_LAST, weight)]


# What a pose is drawn from: the sheet, how many frames it holds, and this pose's frame or frames
# on it. Each pose answers for itself while the real sheet is only partly drawn.
static func pose(key: String) -> Dictionary:
	var final: bool = USE_FINAL_ENTRANCE_ART.get(key, false)
	var spec: Dictionary = FINAL_ENTRANCE if final else PLACEHOLDER_ENTRANCE
	return {"texture": spec.texture, "hframes": spec.hframes, "frames": spec[key], "final": final}



# Screen-px offset from Eric's origin of the spot the sword is planted in.
static func plant_offset() -> Vector2:
	return EricArtLayout.pixel_offset(PLANT_PIXEL)


# The offset that puts the planted sword's ground contact on its own origin, whatever size the art
# is: a centred Sprite2D draws its middle on its position, so the middle has to come back by the
# distance from there to the contact.
static func planted_offset(texture: Texture2D) -> Vector2:
	return texture.get_size() / 2.0 - PLANTED_CONTACT
