extends CanvasLayer

# The final beam's mash on the screen (JordanGodFinalBeam): five code-drawn bars in the hidden boss bar's spot with the
# mash keys either side, built as FinisherPromptUI builds them, MASH! under them until the first bar; and the shout.
# The shout is the artist's drawn words once they are in - one word at a time, hung off the player so it rides the zoom
# (FinalBeamLayout.FINAL_SHOUT) - or, until then, a line of text building up a syllable a bar at the top. Under the
# pause screen's layer, and paused with the fight.

const Layout := preload("res://Scripts/FinalBeamLayout.gd")
const FinisherArtLayout := preload("res://Scripts/FinisherArtLayout.gd")
const ControlsArtLayout := preload("res://Scripts/ControlsArtLayout.gd")
const MashInput := preload("res://Scripts/MashInput.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")

const UI_THEME := "res://Assets/UI/ui_theme.tres"
const SCREEN := Vector2(1920, 1080)

var player: CharacterBody2D
var meter: RefCounted
var staging: Dictionary
var actions: Array[StringName] = []
var gamepad_keys := false
var block: Node2D
var keys := {}
var key_rest := {}
var fills: Array[ColorRect] = []
var flashes: Array[ColorRect] = []
var flash_left: Array[float] = [0.0, 0.0, 0.0, 0.0, 0.0]
var mash_text: CanvasItem
var lit_action := &""
var pressed_action := &""
var pulse_left := 0.0
var clock := 0.0
var failed := false
# The drawn words, and which shows (-1 for none) off which anchor; or the text line and the stamp.
var drawn_words := false
var word_sprite: Sprite2D
var word_inks: Array[Rect2] = []
var word := -1
var word_released := false
var word_pop := 1.0
var word_tween: Tween
var shout: Label
var final_label: Label
var line := ""


func setup(p: CharacterBody2D) -> void:
	layer = Layout.UI_LAYER
	player = p
	staging = Layout.staging()
	gamepad_keys = InputSettings.device == InputSettings.Device.GAMEPAD
	actions = MashInput.actions(player)
	block = Node2D.new()
	block.name = "Meter"
	block.visible = false
	add_child(block)
	_build_slots()
	_build_keys()
	_build_mash_text()
	drawn_words = Layout.has_piece(Layout.FINAL_SHOUT.sheet)
	if drawn_words:
		_build_words()
	else:
		shout = _label(Layout.SHOUT_SIZE, Layout.SHOUT_CENTER, 80.0)
		final_label = _label(Layout.FINAL_SIZE, Layout.FINAL_CENTER, 140.0)


func _meter_rect() -> Rect2:
	var width := Layout.SLOT_SIZE.x * Layout.BARS + Layout.SLOT_GAP * (Layout.BARS - 1)
	return Rect2(Layout.METER_CENTER - Vector2(width, Layout.SLOT_SIZE.y) / 2.0, Vector2(width, Layout.SLOT_SIZE.y))


func _rect(at: Vector2, size: Vector2, color: Color) -> ColorRect:
	var rect := ColorRect.new()
	rect.position = at
	rect.size = size
	rect.color = color
	rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	block.add_child(rect)
	return rect


func _build_slots() -> void:
	var meter_rect := _meter_rect()
	var border := Vector2.ONE * Layout.SLOT_BORDER
	for i in Layout.BARS:
		var at := meter_rect.position + Vector2((Layout.SLOT_SIZE.x + Layout.SLOT_GAP) * i, 0)
		_rect(at - border, Layout.SLOT_SIZE + border * 2.0, Layout.SLOT_EDGE)
		_rect(at, Layout.SLOT_SIZE, Layout.SLOT_BG)
		fills.append(_rect(at, Vector2(0, Layout.SLOT_SIZE.y), Layout.BANK_COLORS[i]))
		var flash := _rect(at, Layout.SLOT_SIZE, Color.WHITE)
		flash.visible = false
		flashes.append(flash)


# As FinisherPromptUI builds them: the drawn keys, or on a pad its drawn buttons or keycaps with the button's name.
func _build_keys() -> void:
	var spec := FinisherArtLayout.keys(gamepad_keys)
	var key_size := Vector2.ZERO
	for action in actions:
		var key: CanvasItem
		if gamepad_keys and not FinisherArtLayout.USE_FINAL_PAD_KEYS:
			var button_name: String = InputSettings.pad_label_for(action)
			var keycap := ControlsArtLayout.keycap(button_name, ControlsArtLayout.KEY_FONT_SIZE if button_name.length() <= 2 else ControlsArtLayout.KEY_SMALL_FONT_SIZE)
			keycap.size = spec.size
			key = keycap
			key_size = spec.size
		else:
			var sprite := Sprite2D.new()
			sprite.texture = load(spec.texture if gamepad_keys else spec[action])
			sprite.hframes = spec.hframes
			sprite.vframes = spec.get("vframes", 1)
			sprite.centered = false
			sprite.scale = Vector2.ONE * spec.scale
			key = sprite
			key_size = Vector2(sprite.texture.get_width() / float(sprite.hframes), sprite.texture.get_height() / float(sprite.vframes)) * spec.scale
		block.add_child(key)
		keys[action] = key
	var meter_rect := _meter_rect()
	var top := roundf(Layout.METER_CENTER.y - key_size.y / 2.0)
	key_rest[actions[0]] = Vector2(meter_rect.position.x - FinisherArtLayout.PROMPT_KEY_GAP - key_size.x, top)
	key_rest[actions[1]] = Vector2(meter_rect.end.x + FinisherArtLayout.PROMPT_KEY_GAP, top)


func _build_mash_text() -> void:
	var spec := FinisherArtLayout.prompt_text()
	var meter_rect := _meter_rect()
	var at := Vector2(roundf(Layout.METER_CENTER.x - spec.size.x / 2.0), meter_rect.end.y + Layout.SLOT_BORDER * 2.0)
	if FinisherArtLayout.USE_FINAL_PROMPT_TEXT:
		var sprite := Sprite2D.new()
		sprite.texture = load(spec.mash)
		sprite.hframes = spec.hframes
		sprite.centered = false
		sprite.position = at
		mash_text = sprite
	else:
		var label := Label.new()
		label.theme = load(UI_THEME)
		label.text = spec.mash
		label.size = spec.size
		label.position = at
		label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		label.add_theme_font_size_override("font_size", 33)
		label.add_theme_constant_override("outline_size", 6)
		label.add_theme_color_override("font_outline_color", Color(0, 0, 0))
		label.mouse_filter = Control.MOUSE_FILTER_IGNORE
		mash_text = label
	block.add_child(mash_text)


# Each word's ink, read off the sheet: a word is centred on its ink, not its cell.
func _build_words() -> void:
	var spec: Dictionary = Layout.FINAL_SHOUT
	word_sprite = Sprite2D.new()
	word_sprite.name = "Shout"
	word_sprite.texture = load(spec.sheet)
	word_sprite.hframes = spec.frames
	word_sprite.centered = false
	word_sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	word_sprite.visible = false
	add_child(word_sprite)
	var image := word_sprite.texture.get_image()
	if image != null and image.is_compressed():
		image.decompress()
	for i in spec.frames:
		var cell := Rect2i(Vector2i(i * int(spec.frame.x), 0), Vector2i(spec.frame))
		var ink := Rect2(image.get_region(cell).get_used_rect()) if image != null and not image.is_empty() else Rect2(Vector2.ZERO, spec.frame)
		word_inks.append(ink if ink.has_area() else Rect2(Vector2.ZERO, spec.frame))


func _label(font_size: int, center: Vector2, height: float) -> Label:
	var label := Label.new()
	label.theme = load(UI_THEME)
	label.size = Vector2(SCREEN.x - 120.0, height)
	label.position = center - label.size / 2.0
	label.pivot_offset = label.size / 2.0
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_constant_override("outline_size", Layout.TEXT_OUTLINE)
	label.add_theme_color_override("font_outline_color", Layout.TEXT_OUTLINE_COLOR)
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	label.visible = false
	add_child(label)
	return label


#WHAT THE BEAM CALLS

func show_meter(tier_meter: RefCounted) -> void:
	meter = tier_meter
	block.visible = true
	block.modulate.a = 1.0
	block.position = Vector2.ZERO
	mash_text.visible = true
	for rect in fills:
		rect.size.x = 0.0


func pressed(action: StringName) -> void:
	pressed_action = action
	lit_action = actions[1] if action == actions[0] else actions[0]
	pulse_left = Layout.KEY_PULSE


func bank(count: int) -> void:
	var index := count - 1
	if index >= 0 and index < flashes.size():
		flash_left[index] = Layout.BANK_FLASH
	mash_text.visible = false
	if count > Layout.SYLLABLES.size():
		return
	if drawn_words:
		_show_word(index, false)
		return
	line = " ".join(Layout.SYLLABLES.slice(0, count))
	shout.text = line
	shout.visible = true
	_stamp(shout)


# All five banked: KEN!!!! stamped, the meter going a beat later.
func release_won() -> void:
	if drawn_words:
		_show_word(Layout.FINAL_SHOUT.final, true)
		_fade_word_after(Layout.FINAL_HOLD)
	else:
		final_label.text = Layout.FINAL_WORD
		final_label.visible = true
		_stamp(final_label)
	_fade(block, Layout.UI_FADE, 0.4)


# The mash ran out: the meter flashes red and falls away, and the shout deflates.
func release_failed() -> void:
	failed = true
	if drawn_words:
		_show_word(Layout.FINAL_SHOUT.fail, true)
		_fade_word_after(Layout.FINAL_HOLD + 0.3)
	else:
		line = (line + " " + Layout.FAIL_WORD).strip_edges()
		shout.text = line
		shout.visible = true
		_drop(shout)
	_drop(block)


# The shout and anything left of the meter, gone.
func fade_all() -> void:
	_fade(block, Layout.UI_FADE, 0.0)
	if drawn_words:
		_fade(word_sprite, Layout.UI_FADE, 0.0)
	else:
		_fade(shout, Layout.UI_FADE, 0.0)
		_fade(final_label, Layout.UI_FADE, 0.0)


func _show_word(index: int, released: bool) -> void:
	word = index
	word_released = released
	word_sprite.frame = index
	word_sprite.visible = true
	word_sprite.modulate.a = 1.0
	if word_tween != null and word_tween.is_valid():
		word_tween.kill()
	word_pop = Layout.FINAL_SHOUT.pop
	word_tween = create_tween().set_ignore_time_scale(true)
	word_tween.tween_property(self, "word_pop", 1.0, Layout.FINAL_SHOUT.pop_time)
	_place_word()


func _fade_word_after(seconds: float) -> void:
	word_tween.tween_interval(seconds)
	word_tween.tween_property(word_sprite, "modulate:a", 0.0, Layout.UI_FADE)
	word_tween.tween_callback(word_sprite.hide)


# Centred on its ink at its anchor off the player, on screen this frame, kept inside the edges.
func _place_word() -> void:
	if word < 0 or not is_instance_valid(player):
		return
	var spec: Dictionary = Layout.FINAL_SHOUT
	var offset: Vector2 = staging.ken if word_released else staging.shout
	var anchor := ScreenView.world_to_screen(get_tree(), player.global_position + offset)
	var scale_px: float = spec.scales[clampi(word, 0, spec.scales.size() - 1)] * word_pop
	var ink: Rect2 = word_inks[clampi(word, 0, word_inks.size() - 1)]
	var size := ink.size * scale_px
	var margin: Vector2 = Vector2.ONE * spec.margin
	var top_left := (anchor - size / 2.0).clamp(margin, SCREEN - size - margin)
	word_sprite.scale = Vector2.ONE * scale_px
	word_sprite.position = (top_left - ink.position * scale_px).round()


func _stamp(label: Label) -> void:
	label.modulate.a = 1.0
	label.scale = Vector2.ONE * Layout.STAMP.from
	var stamp := label.create_tween().set_ignore_time_scale(true)
	stamp.tween_property(label, "scale", Vector2.ONE, Layout.STAMP.time)


func _fade(item: CanvasItem, seconds: float, after: float) -> void:
	if item == null:
		return
	var fade := item.create_tween().set_ignore_time_scale(true)
	fade.tween_interval(after)
	fade.tween_property(item, "modulate:a", 0.0, seconds)
	fade.tween_callback(item.hide)


func _drop(item: CanvasItem) -> void:
	var spec: Dictionary = Layout.FAIL_TEXT
	item.modulate = Layout.FAIL_RED
	var drop := item.create_tween().set_ignore_time_scale(true)
	drop.tween_interval(spec.flash)
	drop.tween_property(item, "position:y", item.position.y + spec.drop, spec.time).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	drop.parallel().tween_property(item, "modulate:a", 0.0, spec.time)
	drop.tween_callback(item.hide)


#EVERY FRAME

func _process(delta: float) -> void:
	clock += delta
	pulse_left = maxf(pulse_left - delta, 0.0)
	if block.visible:
		_show_fills(delta)
		_show_keys()
		_show_mash_text()
	if drawn_words and word_sprite.visible:
		_place_word()
	var step := int(clock / Layout.TEXT_FRAME) % 2
	for label in [shout, final_label]:
		if label != null and label.visible and not failed:
			label.add_theme_color_override("font_color", Layout.TEXT_COLORS[step])


func _show_fills(delta: float) -> void:
	if meter == null:
		return
	var banked: int = meter.banked
	var share := clampf(meter.meter - banked, 0.0, 1.0)
	for i in fills.size():
		var full := i < banked
		fills[i].size.x = Layout.SLOT_SIZE.x * (1.0 if full else (share if i == banked else 0.0))
		fills[i].color.a = 1.0 if full else Layout.FILL_ALPHA
		flash_left[i] = maxf(flash_left[i] - delta, 0.0)
		flashes[i].visible = flash_left[i] > 0.0


func _show_keys() -> void:
	var spec := FinisherArtLayout.keys(gamepad_keys)
	var flashing := actions[0] if int(clock / Layout.KEY_FLASH_TIME) % 2 == 0 else actions[1]
	for action in keys:
		var look: Array = spec.idle
		if lit_action.is_empty():
			if action == flashing:
				look = spec.lit
		elif action == pressed_action and pulse_left > 0.0:
			look = spec.pressed
		elif action == lit_action:
			look = spec.lit
		var key: CanvasItem = keys[action]
		if key is Sprite2D:
			(key as Sprite2D).frame = (InputSettings.pad_frame_for(action) if gamepad_keys else 0) + look[0]
		key.modulate = look[1]
		key.position = key_rest[action] + Vector2(0, look[2])


func _show_mash_text() -> void:
	if not mash_text.visible:
		return
	var spec := FinisherArtLayout.prompt_text()
	var step := int(clock / spec.mash_frame_time) % 2
	if mash_text is Sprite2D:
		(mash_text as Sprite2D).frame = step
	else:
		(mash_text as Label).add_theme_color_override("font_color", spec.colors[step])
