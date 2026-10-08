extends CanvasLayer

# The boss select's INVINCIBLE toggle (GameProgress.playtest_invincible) said in every fight while it is on, so a story
# run can't be played invincible by accident (the 2026-10-07 playtest). Small, in the top left corner over the crowd, out
# of the way of the boss bar and the hearts, in the look of the skip hint (BossEntrance) that comes up in the other top
# corner. GameProgress adds one to each fight scene as it comes up.

const BossEntrance := preload("res://Scripts/BossEntrance.gd")

const TEXT := "INVINCIBLE"
# Pixelify Sans is only crisp at multiples of its 11 px design size: two thirds of the hint's.
const FONT_SIZE := 22
const SHADOW_OFFSET := 2
const PADDING := 8.0


func _init() -> void:
	name = "InvincibleBadge"


func _ready() -> void:
	var badge := Label.new()
	badge.name = "Badge"
	badge.theme = load(BossEntrance.UI_THEME)
	badge.text = TEXT
	badge.mouse_filter = Control.MOUSE_FILTER_IGNORE
	badge.add_theme_font_size_override("font_size", FONT_SIZE)
	badge.add_theme_color_override("font_color", BossEntrance.HINT_COLOR)
	badge.add_theme_color_override("font_shadow_color", BossEntrance.HINT_SHADOW_COLOR)
	badge.add_theme_constant_override("shadow_offset_x", SHADOW_OFFSET)
	badge.add_theme_constant_override("shadow_offset_y", SHADOW_OFFSET)
	var backing := StyleBoxFlat.new()
	backing.bg_color = BossEntrance.HINT_BACKING
	backing.set_content_margin_all(PADDING)
	badge.add_theme_stylebox_override("normal", backing)
	badge.position = BossEntrance.HINT_MARGIN
	add_child(badge)
