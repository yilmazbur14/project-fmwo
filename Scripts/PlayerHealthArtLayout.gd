extends RefCounted

# Every number the player's health containers are drawn from. USE_FINAL_PLAYER_HP picks between the
# drawn tray and the placeholder hearts, and both go through the same code in PlayerHealthUIScript,
# so turning the flag off brings the old row back. HUD art uses the _3x copies at scale 1 on whole
# screen px, like the stamina and break frames.
#
# The placeholder is the row as the HBoxContainer laid it out: 92x92 stretched copies of hearttest.png,
# 4 px apart, standing on the bottom-left corner. It is here rather than in the scene so the two looks
# share one code path.

const DefenseHypeArtLayout := preload("res://Scripts/DefenseHypeArtLayout.gd")

const USE_FINAL_PLAYER_HP := true

#GEOMETRY
# The drawn tray has DRAWN_CONTAINERS cells, CONTAINER_PITCH apart like the hearts in them. Any other count
# is cut from its own pixels at runtime (tray_texture) rather than redrawn: its left cap and first cell,
# then the divider and cell starting at TRAY_UNIT_X once per container after the first, then the trail
# after the last cell and the right cap.
const DRAWN_TRAY_SIZE := Vector2(264, 66)
const DRAWN_CONTAINERS := 3
const CONTAINER_PITCH := 78
const TRAY_UNIT_X := 84
# Four containers, eight half-hearts: the player's full health (PlayerScript.playerHealth). Three and six
# until the user raised it (2026-09-30).
const CONTAINERS := 4
# The tray shares the stamina frame's left edge, so the left column reads as one object and cannot drift
# when either moves. At three containers it was exactly as wide as the frame; each one more runs a
# CONTAINER_PITCH past its right end.
const TRAY_SIZE := Vector2(DRAWN_TRAY_SIZE.x + CONTAINER_PITCH * (CONTAINERS - DRAWN_CONTAINERS), DRAWN_TRAY_SIZE.y)
const TRAY_GAP := 6.0
const TRAY_POSITION := Vector2(DefenseHypeArtLayout.STAMINA_BAR_POSITION.x,
	DefenseHypeArtLayout.STAMINA_BAR_POSITION.y - TRAY_SIZE.y - TRAY_GAP)

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
# assumed, because the container sized them and not the texture. The fourth follows at the same pitch.
const PLACEHOLDER_PLAYER_HP := {
	"position": Vector2(0, 952),
	"size": Vector2(380, 92),
	"heart_size": Vector2(92, 92),
	"heart_offsets": [Vector2(0, 0), Vector2(96, 0), Vector2(192, 0), Vector2(288, 0)],
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
	"heart_offsets": [Vector2(24, 9), Vector2(102, 9), Vector2(180, 9), Vector2(258, 9)],
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


# The drawn tray sheet at `path`, `hframes` frames side by side, cut to CONTAINERS cells a frame: every
# cell, divider and border texel for texel the drawn one's. At DRAWN_CONTAINERS it is the drawn sheet.
static func tray_texture(path: String, hframes: int) -> Texture2D:
	var drawn: Image = (load(path) as Texture2D).get_image()
	var drawn_width := int(DRAWN_TRAY_SIZE.x)
	var width := int(TRAY_SIZE.x)
	var height := drawn.get_height()
	var tail_x := TRAY_UNIT_X + CONTAINER_PITCH * (DRAWN_CONTAINERS - 1)
	var tail_width := drawn_width - tail_x
	var built := Image.create_empty(width * hframes, height, false, drawn.get_format())
	for f in hframes:
		var from := f * drawn_width
		var to := f * width
		built.blit_rect(drawn, Rect2i(from, 0, TRAY_UNIT_X, height), Vector2i(to, 0))
		for i in CONTAINERS - 1:
			built.blit_rect(drawn, Rect2i(from + TRAY_UNIT_X, 0, CONTAINER_PITCH, height),
				Vector2i(to + TRAY_UNIT_X + CONTAINER_PITCH * i, 0))
		built.blit_rect(drawn, Rect2i(from + tail_x, 0, tail_width, height), Vector2i(to + width - tail_width, 0))
	return ImageTexture.create_from_image(built)


# Where the row's right edge falls. The dialogue box is placed off this rather than off the live
# rect, because its container hasn't sized the row yet when the first line appears.
static func row_right_edge() -> float:
	var spec := hearts()
	return spec.position.x + spec.size.x
