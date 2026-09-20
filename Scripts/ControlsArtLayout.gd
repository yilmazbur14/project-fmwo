extends RefCounted

# Every number that depends on how a control is drawn on screen: the gamepad's glyphs, the blank key
# a rebound key's name is written on, and the stick-and-d-pad cluster the Controls screen shows for
# movement. Each asset has its own USE_FINAL_* flag; placeholder and final art go through the same
# code, so turning a flag off brings the placeholder back. The placeholders are built in code, a
# name written on a key, so nothing here waits on art.

const UI_THEME := "res://Assets/UI/ui_theme.tres"

#PAD GLYPHS
# One sheet, 14 columns of 96x96: InputSettings.pad_frame_for() gives the column, whose order is ours
# and not Godot's JoyButton order. Row 0 is the button at rest, row 1 lit, drawn gold and 2 px down
# rather than modulated. Column 12 is the generic "?" every unrecognised button draws as; 13 is Start.
const USE_FINAL_PAD_GLYPHS := true
const FINAL_PAD_GLYPHS := {
	"texture": "res://Assets/UI/Pad/pad_buttons_3x.png",
	"hframes": 14,
	"vframes": 2,
}

#DIALOGUE GLYPHS
# The pad's buttons drawn inline in a dialogue line: 11 px cells at 3x, the same pixel grain as the
# dialogue's Pixelify Sans, in the sheet's column order. A RichTextLabel counts an inline image as one
# character, typed as a space, so the letter-by-letter typing and its voice blips carry on over it.
const USE_FINAL_INLINE_GLYPHS := true
const FINAL_INLINE_GLYPHS := {
	"texture": "res://Assets/UI/Pad/pad_buttons_inline_3x.png",
	"cell": 33,
}
# LB, RB, LT and RT don't read in the dialogue box at 11 px, where R and B are a pixel apart, so those
# come from the 32 px sheet at 1:1 instead: a finer grain than the text, but legible.
const INLINE_FALLBACK_COLUMNS: Array[int] = [4, 5, 6, 7]
const FINAL_INLINE_FALLBACK := {
	"texture": "res://Assets/UI/Pad/pad_buttons.png",
	"cell": 32,
}

#PAD MOVE CLUSTER
# The stick and the d-pad together, the same 96x64 as key_arrows.png, which the Move card draws at
# 3x, so it drops straight in.
const USE_FINAL_PAD_MOVE := true
const FINAL_PAD_MOVE := "res://Assets/UI/Pad/pad_move.png"

#BLANK KEY
# key_q.png's body with the letter wiped, stretched sideways for a long key name such as SPACE: one
# asset draws any key a player can rebind to.
const USE_FINAL_KEY_BLANK := true
# [left, top, right, bottom]. The bottom margin takes the whole 27 px lip, so however tall or short
# the key is drawn only flat face is ever stretched. The text sits on that face: under its 9 px top
# edge and over the lip.
const FINAL_KEY_BLANK := {
	"texture": "res://Assets/UI/Pad/key_blank_3x.png",
	"texture_margins": [24.0, 24.0, 24.0, 27.0],
	"content_margins": [21.0, 9.0, 21.0, 27.0],
}
# The skip hint's colours, so a placeholder key reads as part of the same kit.
const PLACEHOLDER_KEY := {
	"bg": Color(0.13333334, 0.1254902, 0.20392157),
	"border": Color(0.8509804, 0.627451, 0.4),
	"border_width": 6,
	"corner_radius": 6,
	"content_margin": Vector2(21, 12),
}

# Every key and glyph is at least a 3x key_q.png, so a short name doesn't shrink the key under it.
const KEY_MIN_SIZE := Vector2(96, 96)
# The rebind table's rows are too short for that: its glyphs are a 2x key_q.png, and its keys at
# least that, however tall key_blank's edges and the text make them.
const SMALL_KEY_MIN_SIZE := Vector2(64, 64)
# Pixelify Sans is only crisp at multiples of its 11px design size.
const KEY_FONT_SIZE := 33
const KEY_SMALL_FONT_SIZE := 22
const KEY_FONT_COLOR := Color(1, 1, 1)
const KEY_SHADOW_COLOR := Color(0.078431375, 0.07058824, 0.12941177)
# An unbound action draws in this.
const UNBOUND_COLOR := Color(1.0, 0.45, 0.35)

# The UI kit's buttons draw no focus, which suits a mouse; a pad or the keyboard needs to see where
# it is. An outline in the kit's border colour, drawn outside the button so it covers no art.
const FOCUS_RING := {
	"color": Color(0.8509804, 0.627451, 0.4),
	"width": 6,
	"expand": 6.0,
}
# A slider can't draw a focus box, only its highlight art: tinted by this, that art shows focus.
const FOCUS_TINT := Color(1.4, 1.25, 0.8)


# A key with `text` written on it, at least `min_size` and as wide as the name needs. The theme is
# set here because some of these hang off a Node2D, which passes no theme down.
static func keycap(text: String, font_size := KEY_FONT_SIZE, min_size := KEY_MIN_SIZE) -> Label:
	var label := Label.new()
	label.theme = load(UI_THEME)
	label.text = text
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.custom_minimum_size = min_size
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", KEY_FONT_COLOR)
	label.add_theme_color_override("font_shadow_color", KEY_SHADOW_COLOR)
	label.add_theme_constant_override("shadow_offset_x", 3)
	label.add_theme_constant_override("shadow_offset_y", 3)
	label.add_theme_stylebox_override("normal", key_style())
	return label


static func key_style() -> StyleBox:
	if USE_FINAL_KEY_BLANK:
		var art := StyleBoxTexture.new()
		art.texture = load(FINAL_KEY_BLANK.texture)
		var sides := [SIDE_LEFT, SIDE_TOP, SIDE_RIGHT, SIDE_BOTTOM]
		for i in sides.size():
			art.set_texture_margin(sides[i], FINAL_KEY_BLANK.texture_margins[i])
			art.set_content_margin(sides[i], FINAL_KEY_BLANK.content_margins[i])
		return art
	var flat := StyleBoxFlat.new()
	flat.bg_color = PLACEHOLDER_KEY.bg
	flat.border_color = PLACEHOLDER_KEY.border
	flat.set_border_width_all(PLACEHOLDER_KEY.border_width)
	flat.set_corner_radius_all(PLACEHOLDER_KEY.corner_radius)
	flat.anti_aliasing = false
	flat.content_margin_left = PLACEHOLDER_KEY.content_margin.x
	flat.content_margin_right = PLACEHOLDER_KEY.content_margin.x
	flat.content_margin_top = PLACEHOLDER_KEY.content_margin.y
	flat.content_margin_bottom = PLACEHOLDER_KEY.content_margin.y
	return flat


# Paints `label` as the key for `action` on one side: its name, or the unbound dash in warning red.
static func paint_keycap(label: Label, action: StringName, gamepad: bool) -> void:
	var bound: bool = InputSettings.is_bound(action, gamepad)
	label.text = (InputSettings.pad_label_for(action) if gamepad else InputSettings.key_label_for(action)) if bound else InputSettings.UNBOUND_LABEL
	label.add_theme_color_override("font_color", KEY_FONT_COLOR if bound else UNBOUND_COLOR)


# The final sheet's cell for `action`'s gamepad button, at rest. Only for the final art: the
# placeholder is a keycap, which has no texture.
static func pad_glyph(action: StringName) -> AtlasTexture:
	return pad_glyph_frame(InputSettings.pad_frame_for(action))


# A column of the sheet on its own, for a prompt that names a button no action is bound to - the
# pause screen's Start and B. Row 0 is the button at rest, row 1 lit.
static func pad_glyph_frame(column: int, lit := false) -> AtlasTexture:
	var sheet: Texture2D = load(FINAL_PAD_GLYPHS.texture)
	var cell := Vector2(sheet.get_width() / float(FINAL_PAD_GLYPHS.hframes), sheet.get_height() / float(FINAL_PAD_GLYPHS.vframes))
	var glyph := AtlasTexture.new()
	glyph.atlas = sheet
	glyph.region = Rect2(Vector2(column, 1 if lit else 0) * cell, cell)
	return glyph


static func pad_move() -> Texture2D:
	return load(FINAL_PAD_MOVE)


# BBCode drawing the pad button in `column` of the sheets, for a line of dialogue.
static func inline_glyph(column: int) -> String:
	var spec: Dictionary = FINAL_INLINE_FALLBACK if INLINE_FALLBACK_COLUMNS.has(column) else FINAL_INLINE_GLYPHS
	var cell: int = spec.cell
	return "[img region=%d,0,%d,%d]%s[/img]" % [column * cell, cell, cell, spec.texture]


static func focus_ring() -> StyleBoxFlat:
	var ring := StyleBoxFlat.new()
	ring.draw_center = false
	ring.border_color = FOCUS_RING.color
	ring.set_border_width_all(FOCUS_RING.width)
	ring.set_expand_margin_all(FOCUS_RING.expand)
	ring.anti_aliasing = false
	return ring
