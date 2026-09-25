extends Label

# The combo count, over the player's head so the eye never has to leave them. It is on the HUD layer, so
# the finisher's zoom doesn't scale it: every frame it is placed bottom-centre over their head, or under
# their feet where there's no room above, the way the word popups are (CombatPopupUI, which stack their
# words over it), pixel-snapped and kept whole on the screen.
# It is only up while the player is in their own hands: never through lines, a fight's lock (every pose
# is inside one), the finisher's mash prompt or the fight's end.

const DefenseHypeArtLayout := preload("res://Scripts/DefenseHypeArtLayout.gd")
const FinisherArtLayout := preload("res://Scripts/FinisherArtLayout.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")

@export var combo : Node

# Pixelify Sans is only crisp at multiples of its 11px design size. A size smaller than the corner's 33
# and 55, since it sits right by the sprite.
const HIT_FONT_SIZE := 22
const CHARGED_FONT_SIZE := 33
const HIT_OUTLINE := 4
const CHARGED_OUTLINE := 6

const FIRST_HIT_COLOR := Color(1, 1, 1)
const BUILDING_COLOR := Color(1.0, 0.9, 0.5)
const CHARGED_COLOR := Color(1.0, 0.72, 0.1)
# A landed hit shows dimmed; the counter lights up and pops the moment the next press is on the beat.
const WAITING_DIM := 0.45

const WINDOW_POP := 6.0
const CHARGED_POP := 12.0
const POP_TIME := 0.12
const CHARGED_FLASH_TIME := 0.2
const CHARGED_HOLD := 0.6
const FADE_TIME := 0.25

var tween: Tween
var hit_color := FIRST_HIT_COLOR
# How far a pop has it over its place, in whole px.
var lift := 0.0
var player: CharacterBody2D
var finisher: Node


func _ready() -> void:
	# Placed by hand every frame from the screen's top-left, at the size of its text.
	set_anchors_preset(Control.PRESET_TOP_LEFT)
	horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	vertical_alignment = VERTICAL_ALIGNMENT_BOTTOM
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	modulate.a = 0.0
	player = combo.get_parent()
	finisher = player.get_node("Finisher")
	combo.combo_changed.connect(_on_combo_changed)
	combo.beat_window_changed.connect(_on_beat_window_changed)


func _process(_delta: float) -> void:
	visible = not _hidden()
	if visible:
		_place()


# The room it takes over the player's head right now, which CombatPopupUI stacks its words above.
func overhead_room() -> float:
	if not visible or modulate.a <= 0.0 or text.is_empty():
		return 0.0
	return size.y + DefenseHypeArtLayout.POPUP_GAP


func _hidden() -> bool:
	if player.fight_over or player.is_talking or player.is_action_locked:
		return true
	return finisher.is_active() and (finisher.prompt_visible or finisher.is_charging())


func _place() -> void:
	size = get_combined_minimum_size()
	var tree := get_tree()
	var gap := DefenseHypeArtLayout.POPUP_GAP
	var head := ScreenView.world_to_screen(tree, player.global_position + FinisherArtLayout.PLAYER_HEAD)
	var top: float = head.y - gap - size.y - lift
	if head.y - gap - size.y - CHARGED_POP < DefenseHypeArtLayout.POPUP_TOP_LIMIT:
		var feet := ScreenView.world_to_screen(tree, player.global_position + FinisherArtLayout.PLAYER_FEET)
		top = feet.y + gap - lift
	var margin := Vector2.ONE * DefenseHypeArtLayout.POPUP_SCREEN_MARGIN
	position = Vector2(head.x - size.x / 2.0, top).clamp(margin, get_viewport_rect().size - size - margin).round()


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
func _set_lift(value: float) -> void:
	lift = roundf(value)
	if visible and is_inside_tree() and player != null:
		_place()


func _set_font_color(color: Color) -> void:
	add_theme_color_override("font_color", color)
