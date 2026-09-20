extends RefCounted

# Every number the player's health containers are drawn from. USE_FINAL_PLAYER_HP picks between the
# drawn tray and the placeholder hearts, and both go through the same code in PlayerHealthUIScript,
# so turning the flag off brings the old row back. HUD art uses the _3x copies at scale 1 on whole
# screen px, like the stamina and break frames.
#
# The placeholder is the row exactly as the HBoxContainer laid it out: three 92x92 stretched copies of
# hearttest.png, 4 px apart, standing on the bottom-left corner. It is here rather than in the scene
# so the two looks share one code path.

const DefenseHypeArtLayout := preload("res://Scripts/DefenseHypeArtLayout.gd")

const USE_FINAL_PLAYER_HP := true

#GEOMETRY
# The tray is as wide as the stamina frame and shares its left edge, so the left column reads as one
# object and cannot drift when either moves.
const TRAY_SIZE := Vector2(264, 66)
const TRAY_GAP := 6.0
const TRAY_POSITION := Vector2(DefenseHypeArtLayout.STAMINA_BAR_POSITION.x,
	DefenseHypeArtLayout.STAMINA_BAR_POSITION.y - TRAY_SIZE.y - TRAY_GAP)
# Three containers, six half-hearts.
const CONTAINERS := 3

#TIMING
# Real seconds and screen px.
const BREAK_FRAME_TIME := 0.06
const GAIN_FRAME_TIME := 0.07
const TRAY_SHAKE_PX := 4.0
const TRAY_SHAKE_STEPS := 4
const TRAY_SHAKE_TIME := 0.12
const TRAY_FLASH := Color(2.2, 0.6, 0.6)
const TRAY_GAIN_FLASH := Color(0.7, 2.2, 1.0)
const TRAY_FLASH_TIME := 0.18
# The last container's heartbeat, and the tray's rim pulse behind it.
const LOW_FRAME_TIME := 0.24
const WARN_FRAME_TIME := 0.22
# Half-hearts left at which the warning comes on.
const WARN_AT := 1

# Today's row: an HBoxContainer's three stretched 32x32 placeholders, measured on screen rather than
# assumed, because the container sized them and not the texture.
const PLACEHOLDER_PLAYER_HP := {
	"position": Vector2(0, 952),
	"size": Vector2(284, 92),
	"heart_size": Vector2(92, 92),
	"heart_offsets": [Vector2(0, 0), Vector2(96, 0), Vector2(192, 0)],
	"full": "res://Assets/UI/hearttest.png",
	"half": "res://Assets/UI/hearthalftest.png",
	"empty": "res://Assets/UI/emptyhearttest.png",
}
# Hearts on the 3x grid at last, in a drawn tray. The break sheet is oversized so the shatter spills
# past its container; its own offset puts the container back in the middle of it.
const FINAL_PLAYER_HP := {
	"position": TRAY_POSITION,
	"size": TRAY_SIZE,
	"heart_size": Vector2(54, 48),
	"heart_offsets": [Vector2(24, 9), Vector2(102, 9), Vector2(180, 9)],
	"tray": "res://Assets/UI/player_hp_tray_3x.png",
	"tray_warn": "res://Assets/UI/player_hp_tray_warn_3x.png",
	"tray_warn_hframes": 2,
	"full": "res://Assets/UI/player_hp_heart_full_3x.png",
	"half": "res://Assets/UI/player_hp_heart_half_3x.png",
	"empty": "res://Assets/UI/player_hp_heart_empty_3x.png",
	"break": "res://Assets/UI/player_hp_heart_break_3x.png",
	"break_hframes": 4,
	"break_size": Vector2(90, 84),
	"break_offset": Vector2(-18, -18),
	"gain": "res://Assets/UI/player_hp_heart_gain_3x.png",
	"gain_hframes": 3,
	"low": "res://Assets/UI/player_hp_heart_low_3x.png",
	"low_hframes": 4,
	# The beat is drawn over the container, so the sheet carries a run per container state: a rest
	# frame and a lit one for a whole heart, then the same pair for a half. A container down to its
	# last half beats as a half instead of taking a whole heart's frames over it.
	"low_beat_frames": 2,
	"low_half_frame": 2,
}


static func hearts() -> Dictionary:
	return FINAL_PLAYER_HP if USE_FINAL_PLAYER_HP else PLACEHOLDER_PLAYER_HP


# Where the row's right edge falls. The dialogue box is placed off this rather than off the live
# rect, because its container hasn't sized the row yet when the first line appears.
static func row_right_edge() -> float:
	var spec := hearts()
	return spec.position.x + spec.size.x
