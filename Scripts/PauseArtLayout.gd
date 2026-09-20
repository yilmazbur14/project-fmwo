extends RefCounted

# Every size, colour and texture the in-fight pause screen is drawn from. Like ControlsArtLayout,
# placeholder and final art go through the same code, so turning USE_FINAL_PAUSE_ART off brings the
# placeholder back. The placeholder is the menus' own kit - the card frame, the menu button and the
# menu's slider - so the screen reads as part of the game while the panel art is being drawn.

const ControlsArtLayout := preload("res://Scripts/ControlsArtLayout.gd")

#PAUSE PANEL ART
# The artist's set, all in Assets/UI/Pause/: the panel and the row are 9-slices, the title is drawn
# whole. Nothing here is loaded while the flag is off.
const USE_FINAL_PAUSE_ART := true
# The _3x files, the resolution the rest of the kit is drawn at: those carry a 9-slice margin of 24,
# where the 1x files beside them carry 8.
# [left, top, right, bottom] for each 9-slice, as texture margins; the content margins are the
# layout's, below, so a row's text sits in the same place whichever art it is drawn on.
const FINAL_PAUSE_ART := {
	"panel": "res://Assets/UI/Pause/pause_panel_3x.png",
	"panel_margins": [24.0, 24.0, 24.0, 24.0],
	"confirm_panel": "res://Assets/UI/Pause/pause_confirm_panel_3x.png",
	"confirm_margins": [24.0, 24.0, 24.0, 24.0],
	"row": "res://Assets/UI/Pause/pause_row_3x.png",
	"row_focus": "res://Assets/UI/Pause/pause_row_focus_3x.png",
	"row_margins": [24.0, 24.0, 24.0, 24.0],
	"title": "res://Assets/UI/Pause/pause_title_3x.png",
}

#PLACEHOLDER
# The card the Controls screen's table sits on, and the main menu's button, at the same 24 px
# margins those screens use.
const PLACEHOLDER_PANEL := {
	"texture": "res://Assets/UI/ui_card_frame_3x.png",
	"margins": [24.0, 24.0, 24.0, 24.0],
}
const PLACEHOLDER_ROW := {
	"normal": "res://Assets/UI/ui_button_3x.png",
	"hover": "res://Assets/UI/ui_button_hover_3x.png",
	"pressed": "res://Assets/UI/ui_button_pressed_3x.png",
	"margins": [24.0, 24.0, 24.0, 24.0],
}

#LAYOUT
# The panel sizes itself around its rows, centred, so the final art can change a row's height
# without moving anything else.
const PANEL_MIN_WIDTH := 672.0
const PANEL_MARGIN := 36
const CONFIRM_MIN_WIDTH := 852.0
const ROW_MIN_SIZE := Vector2(576, 96)
const ROW_SEPARATION := 14
# Between the title, the rows and the footer.
const COLUMN_SEPARATION := 30
# Between the two footer hints, and between a hint's word and its key.
const FOOTER_SEPARATION := 54
const FOOTER_HINT_SEPARATION := 12
const CONFIRM_BUTTON_MIN_SIZE := Vector2(324, 96)
const CONFIRM_BUTTON_SEPARATION := 36
const SLIDER_MIN_SIZE := Vector2(576, 54)
# A row's text sits this far in from the art's edges, whichever art it is.
const ROW_CONTENT_MARGINS := [24.0, 24.0, 24.0, 24.0]

# Pixelify Sans is only crisp at multiples of its 11 px design size.
const TITLE_FONT_SIZE := 99
const ROW_FONT_SIZE := 44
const LABEL_FONT_SIZE := 33
const FOOTER_FONT_SIZE := 33
const FOOTER_KEY_FONT_SIZE := 22
# The footer's glyphs and key caps, the size the rebind table draws its own at.
const FOOTER_KEY_MIN_SIZE := Vector2(64, 64)

#COLOURS
# Black over the whole screen: it is what makes the panel read over a bright arena and over Carter's
# near-black barrage alike, so neither background is ever what the rows are judged against.
const DIM_COLOR := Color(0, 0, 0, 0.55)
const TITLE_COLOR := Color(1, 1, 1)
const ROW_FONT_COLOR := Color(1, 1, 1)
# The wording the other screens use for a caption and a hint.
const LABEL_COLOR := Color(0.60784316, 0.6784314, 0.7176471)
const FOOTER_COLOR := Color(0.60784316, 0.6784314, 0.7176471)
const CONFIRM_MESSAGE_COLOR := Color(1, 1, 1)


static func panel_style() -> StyleBox:
	if USE_FINAL_PAUSE_ART:
		return _nine_slice(FINAL_PAUSE_ART.panel, FINAL_PAUSE_ART.panel_margins)
	return _nine_slice(PLACEHOLDER_PANEL.texture, PLACEHOLDER_PANEL.margins)


static func confirm_panel_style() -> StyleBox:
	if USE_FINAL_PAUSE_ART:
		return _nine_slice(FINAL_PAUSE_ART.confirm_panel, FINAL_PAUSE_ART.confirm_margins)
	return _nine_slice(PLACEHOLDER_PANEL.texture, PLACEHOLDER_PANEL.margins)


# `state` is a Button's stylebox name. The focus ring is drawn outside the row, over no art, so a
# focused row keeps whichever face it is already showing.
static func row_style(state: String) -> StyleBox:
	if state == "focus":
		return ControlsArtLayout.focus_ring()
	if USE_FINAL_PAUSE_ART:
		var art: String = FINAL_PAUSE_ART.row_focus if state == "hover" else FINAL_PAUSE_ART.row
		return _nine_slice(art, FINAL_PAUSE_ART.row_margins, ROW_CONTENT_MARGINS)
	return _nine_slice(PLACEHOLDER_ROW[state], PLACEHOLDER_ROW.margins, ROW_CONTENT_MARGINS)


# The face a focused row wears. PauseMenu puts it in the `normal` stylebox rather than `hover`,
# because a Button only enters DRAW_HOVER under the mouse: a pad player never reaches the `hover`
# box, and the lit row is the only thing on the screen that says which row is selected.
static func row_lit_style() -> StyleBox:
	if USE_FINAL_PAUSE_ART:
		return _nine_slice(FINAL_PAUSE_ART.row_focus, FINAL_PAUSE_ART.row_margins, ROW_CONTENT_MARGINS)
	return _nine_slice(PLACEHOLDER_ROW.hover, PLACEHOLDER_ROW.margins, ROW_CONTENT_MARGINS)


# The drawn title, or null while the placeholder writes it out as a label instead.
static func title_texture() -> Texture2D:
	return load(FINAL_PAUSE_ART.title) if USE_FINAL_PAUSE_ART else null


static func _nine_slice(texture_path: String, texture_margins: Array, content_margins := []) -> StyleBoxTexture:
	var style := StyleBoxTexture.new()
	style.texture = load(texture_path)
	var sides := [SIDE_LEFT, SIDE_TOP, SIDE_RIGHT, SIDE_BOTTOM]
	for i in sides.size():
		style.set_texture_margin(sides[i], texture_margins[i])
		if not content_margins.is_empty():
			style.set_content_margin(sides[i], content_margins[i])
	return style
