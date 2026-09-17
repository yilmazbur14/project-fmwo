extends Label

@export var combo : Node

# Pixelify Sans is only crisp at multiples of its 11px design size.
const HIT_FONT_SIZE := 33
const CHARGED_FONT_SIZE := 55
const HIT_OUTLINE := 6
const CHARGED_OUTLINE := 10

const FIRST_HIT_COLOR := Color(1, 1, 1)
const BUILDING_COLOR := Color(1.0, 0.9, 0.5)
const CHARGED_COLOR := Color(1.0, 0.72, 0.1)
# A landed hit shows dimmed; the counter lights up and pops the moment the next press is on the beat.
const WAITING_DIM := 0.45

const WINDOW_POP := 8.0
const CHARGED_POP := 18.0
const POP_TIME := 0.12
const CHARGED_FLASH_TIME := 0.2
const CHARGED_HOLD := 0.6
const FADE_TIME := 0.25

var base_position: Vector2
var tween: Tween
var hit_color := FIRST_HIT_COLOR


func _ready() -> void:
	base_position = position
	modulate.a = 0.0
	combo.combo_changed.connect(_on_combo_changed)
	combo.beat_window_changed.connect(_on_beat_window_changed)


func _on_combo_changed(count: int, charged: bool) -> void:
	_stop_tween()

	if count == 0:
		_new_tween().tween_property(self, "modulate:a", 0.0, FADE_TIME)
		return

	modulate.a = 1.0
	if charged:
		text = "%d POW!" % count
		add_theme_font_size_override("font_size", CHARGED_FONT_SIZE)
		add_theme_constant_override("outline_size", CHARGED_OUTLINE)
		_set_font_color(Color(1, 1, 1))
		_new_tween().set_parallel()
		tween.tween_method(_set_lift, CHARGED_POP, 0.0, POP_TIME).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_QUAD)
		tween.tween_method(_set_font_color, Color(1, 1, 1), CHARGED_COLOR, CHARGED_FLASH_TIME)
		tween.chain().tween_interval(CHARGED_HOLD)
		tween.chain().tween_property(self, "modulate:a", 0.0, FADE_TIME)
	else:
		text = "%d HIT" % count if count == 1 else "%d HITS" % count
		add_theme_font_size_override("font_size", HIT_FONT_SIZE)
		add_theme_constant_override("outline_size", HIT_OUTLINE)
		hit_color = FIRST_HIT_COLOR if count == 1 else BUILDING_COLOR
		_set_font_color(hit_color.darkened(WAITING_DIM))


func _on_beat_window_changed(open: bool) -> void:
	if combo.count == 0:
		return
	_stop_tween()
	if open:
		_set_font_color(hit_color)
		_new_tween().tween_method(_set_lift, WINDOW_POP, 0.0, POP_TIME).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_QUAD)
	else:
		_set_font_color(hit_color.darkened(WAITING_DIM))


func _stop_tween() -> void:
	if tween:
		tween.kill()
	_set_lift(0.0)


func _new_tween() -> Tween:
	# The counter keeps animating through hit-stop.
	tween = create_tween().set_ignore_time_scale(true)
	return tween


# Whole pixels only, so the pixel font doesn't smear mid-pop.
func _set_lift(lift: float) -> void:
	position = base_position - Vector2(0, roundf(lift))


func _set_font_color(color: Color) -> void:
	add_theme_color_override("font_color", color)
