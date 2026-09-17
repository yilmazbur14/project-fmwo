extends Node2D

# The finisher's mash prompt, on the HUD layer so the zoom doesn't scale it: [punch key] [meter]
# [dodge key] in a row with MASH! under the meter, and FULL! once the meter fills. It sits under the
# player on screen, or over them when there's no room below.

const FinisherArtLayout := preload("res://Scripts/FinisherArtLayout.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")

@export var finisher: Node
@export var player: CharacterBody2D

# Pixelify Sans is only crisp at multiples of its 11px design size (ComboCounterUI's hit text).
const FONT_SIZE := 33
const OUTLINE := 6
# Until the first press the keys take turns lighting up.
const KEY_FLASH_TIME := 0.12
# How long a key shows as pressed.
const PULSE_TIME := 0.08
# px between the prompt and the player's feet or head.
const PLAYER_GAP := 12.0
# The boss health bars are above this line.
const TOP_LIMIT := 100.0
const SCREEN_MARGIN := 8.0
# FULL! stays up this long into the uppercut, then fades.
const FULL_HOLD := 0.35
const FADE_TIME := 0.15

var keys := {}
var key_rest := {}
var meter_bar: Range
var meter_fill_style: StyleBoxFlat
var full_overlay: Sprite2D
var text_label: Label
var text_sprite: Sprite2D
var text_textures := {}
var prompt_size := Vector2.ZERO
# The key to press next; empty until the first press.
var lit_action := &""
var pressed_action := &""
var pulse_left := 0.0
var full := false
var clock := 0.0
var fade: Tween


func _ready() -> void:
	visible = false
	_build()
	finisher.prompt_shown.connect(_on_prompt_shown)
	finisher.meter_changed.connect(_on_meter_changed)
	finisher.charge_ended.connect(_on_charge_ended)
	finisher.finished.connect(_on_finished)


func _process(delta: float) -> void:
	if not visible:
		return
	clock += delta
	pulse_left = maxf(pulse_left - delta, 0.0)
	_refresh()


func _on_prompt_shown() -> void:
	_stop_fade()
	visible = true
	modulate.a = 1.0
	full = false
	lit_action = &""
	pressed_action = &""
	pulse_left = 0.0
	clock = 0.0
	for key in keys.values():
		key.visible = true
	if full_overlay:
		full_overlay.visible = false
	_refresh()


func _on_meter_changed(_meter: float, next_action: StringName) -> void:
	pressed_action = &"dodge" if next_action == &"punch" else &"punch"
	lit_action = next_action
	pulse_left = PULSE_TIME


func _on_charge_ended(filled: bool) -> void:
	_stop_fade()
	fade = create_tween()
	if filled:
		full = true
		clock = 0.0
		for key in keys.values():
			key.visible = false
		if full_overlay:
			full_overlay.visible = true
		fade.tween_interval(FULL_HOLD)
	fade.tween_property(self, "modulate:a", 0.0, FADE_TIME)
	fade.tween_callback(hide)


func _on_finished() -> void:
	_stop_fade()
	visible = false


func _stop_fade() -> void:
	if fade:
		fade.kill()
	fade = null


func _build() -> void:
	var key_spec := FinisherArtLayout.keys()
	var key_size := Vector2.ZERO
	for action in [&"punch", &"dodge"]:
		var key := Sprite2D.new()
		key.texture = load(key_spec[action])
		key.hframes = key_spec.hframes
		key.centered = false
		key.scale = Vector2.ONE * key_spec.scale
		add_child(key)
		keys[action] = key
		key_size = Vector2(key.texture.get_width() / float(key_spec.hframes), key.texture.get_height()) * key_spec.scale
	var meter_spec := FinisherArtLayout.meter()
	var meter_size: Vector2 = meter_spec.size
	var meter_position := Vector2(key_size.x + FinisherArtLayout.PROMPT_KEY_GAP, roundf((key_size.y - meter_size.y) / 2.0))
	key_rest[&"punch"] = Vector2.ZERO
	key_rest[&"dodge"] = Vector2(meter_position.x + meter_size.x + FinisherArtLayout.PROMPT_KEY_GAP, 0.0)
	_build_meter(meter_spec, meter_position)
	var text_spec := FinisherArtLayout.prompt_text()
	var text_size: Vector2 = text_spec.size
	var text_position := Vector2(meter_position.x + roundf((meter_size.x - text_size.x) / 2.0), meter_position.y + meter_size.y)
	_build_text(text_spec, text_position)
	prompt_size = Vector2(key_rest[&"dodge"].x + key_size.x, maxf(key_size.y, text_position.y + text_size.y))


func _build_meter(spec: Dictionary, at: Vector2) -> void:
	if FinisherArtLayout.USE_FINAL_METER:
		var bar := TextureProgressBar.new()
		bar.texture_under = load(spec.frame)
		bar.texture_progress = load(spec.fill)
		bar.texture_progress_offset = spec.fill_offset
		bar.fill_mode = TextureProgressBar.FILL_LEFT_TO_RIGHT
		bar.position = at
		meter_bar = bar
		full_overlay = Sprite2D.new()
		full_overlay.texture = load(spec.full)
		full_overlay.hframes = spec.full_hframes
		full_overlay.centered = false
		full_overlay.position = at
		full_overlay.visible = false
	else:
		# Styled like the boss health bars.
		var bar := ProgressBar.new()
		bar.show_percentage = false
		bar.position = at + spec.bar_rect.position
		bar.size = spec.bar_rect.size
		var background := StyleBoxFlat.new()
		background.bg_color = Color(0.08, 0.08, 0.08, 0.85)
		background.set_corner_radius_all(3)
		background.set_border_width_all(2)
		background.border_color = Color(0, 0, 0)
		bar.add_theme_stylebox_override("background", background)
		meter_fill_style = StyleBoxFlat.new()
		meter_fill_style.bg_color = spec.fill_color
		meter_fill_style.set_corner_radius_all(3)
		bar.add_theme_stylebox_override("fill", meter_fill_style)
		meter_bar = bar
	meter_bar.min_value = 0.0
	meter_bar.max_value = 1.0
	meter_bar.step = 0.0
	meter_bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(meter_bar)
	if full_overlay:
		add_child(full_overlay)


func _build_text(spec: Dictionary, at: Vector2) -> void:
	if FinisherArtLayout.USE_FINAL_PROMPT_TEXT:
		text_textures = {false: load(spec.mash), true: load(spec.full)}
		text_sprite = Sprite2D.new()
		text_sprite.texture = text_textures[false]
		text_sprite.hframes = spec.hframes
		text_sprite.centered = false
		text_sprite.position = at
		add_child(text_sprite)
		return
	text_label = Label.new()
	text_label.theme = load("res://Assets/UI/ui_theme.tres")
	text_label.add_theme_font_size_override("font_size", FONT_SIZE)
	text_label.add_theme_constant_override("outline_size", OUTLINE)
	text_label.add_theme_color_override("font_outline_color", Color(0, 0, 0))
	text_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	text_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	text_label.position = at
	text_label.size = spec.size
	text_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(text_label)


func _refresh() -> void:
	meter_bar.value = 1.0 if full else finisher.meter
	_show_keys()
	_show_text()
	_place()


func _show_keys() -> void:
	var spec := FinisherArtLayout.keys()
	var flashing := &"punch" if int(clock / KEY_FLASH_TIME) % 2 == 0 else &"dodge"
	for action in keys:
		var look: Array = spec.idle
		if lit_action.is_empty():
			if action == flashing:
				look = spec.lit
		elif action == pressed_action and pulse_left > 0.0:
			look = spec.pressed
		elif action == lit_action:
			look = spec.lit
		var key: Sprite2D = keys[action]
		key.frame = look[0]
		key.modulate = look[1]
		key.position = key_rest[action] + Vector2(0, look[2])


func _show_text() -> void:
	var spec := FinisherArtLayout.prompt_text()
	var text_frame := int(clock / (spec.full_frame_time if full else spec.mash_frame_time)) % 2
	if text_sprite:
		text_sprite.texture = text_textures[full]
		text_sprite.frame = text_frame
	else:
		text_label.text = spec.full if full else spec.mash
		text_label.add_theme_color_override("font_color", spec.colors[text_frame])
	var meter_spec := FinisherArtLayout.meter()
	var full_frame := int(clock / meter_spec.full_frame_time) % 2
	if full_overlay:
		full_overlay.frame = full_frame
	else:
		meter_fill_style.bg_color = meter_spec.full_colors[full_frame] if full else meter_spec.fill_color


func _place() -> void:
	var tree := get_tree()
	var screen := get_viewport_rect().size
	var feet := ScreenView.world_to_screen(tree, player.global_position + FinisherArtLayout.PLAYER_FEET)
	var head := ScreenView.world_to_screen(tree, player.global_position + FinisherArtLayout.PLAYER_HEAD)
	var top := feet.y + PLAYER_GAP
	var above := head.y - PLAYER_GAP - prompt_size.y
	if top + prompt_size.y > screen.y - SCREEN_MARGIN and above >= TOP_LIMIT:
		top = above
	var corner := Vector2(feet.x - prompt_size.x / 2.0, top)
	var margin := Vector2(SCREEN_MARGIN, SCREEN_MARGIN)
	position = corner.clamp(margin, screen - prompt_size - margin).round()
