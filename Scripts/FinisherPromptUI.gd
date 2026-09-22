extends Node2D

# The finisher's mash prompt, on the HUD layer so the zoom doesn't scale it: [punch key] [meter]
# [dodge key] in a row with MASH! under the meter, and FULL! once the meter fills. It sits under the
# player on screen, or over them when there's no room below.
# A tiered mash (PlayerFinisher.tiered) draws its meter in three bars instead: each banked bar glints and
# bursts as it banks, a stamp takes MASH!'s place under it, 1!, 2!! then 3!!!, the meter flashes FULL
# with the third, and KNIGHT BREAKER! goes up on the HUD over the fight until the third uppercut lands.

const FinisherArtLayout := preload("res://Scripts/FinisherArtLayout.gd")
const ControlsArtLayout := preload("res://Scripts/ControlsArtLayout.gd")
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
# MASH! is drawn; a finisher asking for any other word (PlayerFinisher.prompt_key) gets this label in
# the drawn word's place. Only built where the drawn one is.
var word_label: Label
var text_textures := {}
var prompt_size := Vector2.ZERO
# The key to press next; empty until the first press.
var lit_action := &""
var pressed_action := &""
var pulse_left := 0.0
var full := false
var clock := 0.0
var fade: Tween
# Which device the keys were last built for, and which pair: attack and dash, or a feel_v2 fight's own
# mash keys (PlayerFinisher.mash_actions).
var gamepad_keys := false
var actions: Array[StringName] = []
# A device switch or a rebind that landed while the prompt was up, applied once it has gone.
var rebuild_pending := false
# The tiered meter's pieces, when that's what was built.
var tiered_built := false
var banked_glints: Array[CanvasItem] = []
var bank_flash: Sprite2D
var bank_flash_clock := -1.0
var tier_full: CanvasItem
var stamp: CanvasItem
var stamp_textures: Array = []
var shown_tier := 0
var knight_breaker: CanvasItem
var knight_breaker_fade: Tween


func _ready() -> void:
	visible = false
	_build()
	_build_knight_breaker()
	finisher.prompt_shown.connect(_on_prompt_shown)
	finisher.meter_changed.connect(_on_meter_changed)
	finisher.charge_ended.connect(_on_charge_ended)
	finisher.finished.connect(_on_finished)
	finisher.tier_banked.connect(_on_tier_banked)
	finisher.juggle_hit.connect(_on_juggle_hit)
	InputSettings.device_changed.connect(_on_controls_changed.unbind(1))
	InputSettings.bindings_changed.connect(_on_controls_changed)


func _process(delta: float) -> void:
	_step_knight_breaker(delta)
	if not visible:
		return
	clock += delta
	pulse_left = maxf(pulse_left - delta, 0.0)
	_refresh()


func _on_prompt_shown() -> void:
	# A fight turns feel_v2 on in its own _ready, which can come after this prompt was built.
	if finisher.mash_actions() != actions or finisher.tiered != tiered_built:
		_rebuild()
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
	if tiered_built:
		bank_flash_clock = -1.0
		bank_flash.visible = false
		tier_full.visible = false
		# A full hype meter banks bar 1 before the first press.
		_show_stamp(finisher.tier_meter.banked)
	_refresh()


func _on_meter_changed(_meter: float, next_action: StringName) -> void:
	pressed_action = actions[0] if next_action == actions[1] else actions[1]
	lit_action = next_action
	pulse_left = PULSE_TIME


func _on_charge_ended(filled: bool) -> void:
	_stop_fade()
	fade = create_tween()
	if filled:
		# A tiered mash keeps its stamp and its bars as they are: FULL is bar 3's alone.
		full = not tiered_built
		clock = 0.0
		for key in keys.values():
			key.visible = false
		if full_overlay:
			full_overlay.visible = true
		fade.tween_interval(FULL_HOLD)
	fade.tween_property(self, "modulate:a", 0.0, FADE_TIME)
	fade.tween_callback(hide)


func _on_tier_banked(tier: int) -> void:
	if not tiered_built:
		return
	bank_flash_clock = 0.0
	bank_flash.visible = true
	_show_stamp(tier)
	if tier == 3:
		tier_full.visible = true
		_show_knight_breaker()


# The third uppercut has landed: KNIGHT BREAKER! holds a beat longer, then goes.
func _on_juggle_hit(index: int, _last: bool) -> void:
	if index == 2:
		_fade_knight_breaker(FinisherArtLayout.knight_breaker().hold_after_hit)


func _on_finished() -> void:
	_stop_fade()
	visible = false
	# One that never got its third uppercut, a kill or a whiff before it, goes with the finisher.
	if knight_breaker.visible and not knight_breaker_fade:
		_fade_knight_breaker(0.0)
	if rebuild_pending:
		_rebuild()


func _stop_fade() -> void:
	if fade:
		fade.kill()
	fade = null


# Mid-mash the keys stay as they are: swapping them under a player who is hammering them would only
# throw them. The swap waits until the prompt has gone.
func _on_controls_changed() -> void:
	if visible:
		rebuild_pending = true
		return
	_rebuild()


# The whole prompt, not just the keys: the meter and the text are laid out around the keys' size.
func _rebuild() -> void:
	rebuild_pending = false
	for child in get_children():
		remove_child(child)
		child.queue_free()
	keys.clear()
	key_rest.clear()
	full_overlay = null
	meter_fill_style = null
	text_label = null
	text_sprite = null
	word_label = null
	text_textures = {}
	banked_glints.clear()
	bank_flash = null
	tier_full = null
	stamp = null
	stamp_textures = []
	_build()


func _build() -> void:
	gamepad_keys = InputSettings.device == InputSettings.Device.GAMEPAD
	actions = finisher.mash_actions()
	tiered_built = finisher.tiered
	var key_spec := FinisherArtLayout.keys(gamepad_keys)
	var key_size := Vector2.ZERO
	for action in actions:
		var key: CanvasItem
		if gamepad_keys and not FinisherArtLayout.USE_FINAL_PAD_KEYS:
			# The slot is one key wide, so a name longer than a bumper's drops a size.
			var button_name: String = InputSettings.pad_label_for(action)
			var keycap := ControlsArtLayout.keycap(button_name, ControlsArtLayout.KEY_FONT_SIZE if button_name.length() <= 2 else ControlsArtLayout.KEY_SMALL_FONT_SIZE)
			keycap.size = key_spec.size
			key = keycap
			key_size = key_spec.size
		else:
			var sprite := Sprite2D.new()
			sprite.texture = load(key_spec.texture if gamepad_keys else key_spec[action])
			sprite.hframes = key_spec.hframes
			sprite.vframes = key_spec.get("vframes", 1)
			sprite.centered = false
			sprite.scale = Vector2.ONE * key_spec.scale
			key = sprite
			key_size = Vector2(sprite.texture.get_width() / float(sprite.hframes), sprite.texture.get_height() / float(sprite.vframes)) * key_spec.scale
		add_child(key)
		keys[action] = key
	var meter_spec := FinisherArtLayout.meter()
	var meter_size: Vector2 = meter_spec.size
	var meter_position := Vector2(key_size.x + FinisherArtLayout.PROMPT_KEY_GAP, roundf((key_size.y - meter_size.y) / 2.0))
	key_rest[actions[0]] = Vector2.ZERO
	key_rest[actions[1]] = Vector2(meter_position.x + meter_size.x + FinisherArtLayout.PROMPT_KEY_GAP, 0.0)
	if tiered_built:
		_build_tier_meter(FinisherArtLayout.tier_meter(), meter_position)
	else:
		_build_meter(meter_spec, meter_position)
	var text_spec := FinisherArtLayout.prompt_text()
	var text_size: Vector2 = text_spec.size
	var text_position := Vector2(meter_position.x + roundf((meter_size.x - text_size.x) / 2.0), meter_position.y + meter_size.y)
	_build_text(text_spec, text_position)
	if tiered_built:
		_build_stamp(FinisherArtLayout.tier_stamps(), meter_position)
	prompt_size = Vector2(key_rest[actions[1]].x + key_size.x, maxf(key_size.y, text_position.y + text_size.y))


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


# The same slot as the single meter. The fill is one bar across all three: bar k (from 0) shows once the
# bars before it are banked, and fills to the meter's share of it.
func _build_tier_meter(spec: Dictionary, at: Vector2) -> void:
	if spec.has("frame"):
		var bar := TextureProgressBar.new()
		bar.texture_under = load(spec.frame)
		bar.texture_progress = load(spec.fill)
		bar.texture_progress_offset = spec.fill_offset
		bar.fill_mode = TextureProgressBar.FILL_LEFT_TO_RIGHT
		bar.max_value = spec.bar_stride * 2.0 + spec.bar_length
		bar.position = at
		meter_bar = bar
		for i in 3:
			var glint := _sheet_sprite(spec.banked, spec.banked_hframes, spec.banked_vframes, at)
			glint.frame = i * spec.banked_hframes
			banked_glints.append(glint)
		bank_flash = _sheet_sprite(spec.flash, spec.flash_hframes, spec.flash_vframes, at + spec.flash_offset)
		tier_full = _sheet_sprite(spec.full, spec.full_hframes, 1, at)
	else:
		# One strip across the three slots; banked slots are painted over it in their own colours.
		var bar := ProgressBar.new()
		bar.show_percentage = false
		var first: Rect2 = spec.bars[0]
		var last: Rect2 = spec.bars[2]
		bar.position = at + first.position
		bar.size = Vector2(last.end.x - first.position.x, first.size.y)
		bar.max_value = last.end.x - first.position.x
		var background := StyleBoxFlat.new()
		background.bg_color = spec.slot_color
		bar.add_theme_stylebox_override("background", background)
		meter_fill_style = StyleBoxFlat.new()
		meter_fill_style.bg_color = spec.fill_color
		bar.add_theme_stylebox_override("fill", meter_fill_style)
		meter_bar = bar
		for i in 3:
			var slot := ColorRect.new()
			slot.position = at + spec.bars[i].position
			slot.size = spec.bars[i].size
			slot.color = spec.banked_colors[i]
			slot.mouse_filter = Control.MOUSE_FILTER_IGNORE
			banked_glints.append(slot)
		bank_flash = Sprite2D.new()
		var full_rect := ColorRect.new()
		full_rect.position = at
		full_rect.size = spec.size
		full_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
		tier_full = full_rect
	meter_bar.min_value = 0.0
	meter_bar.step = 0.0
	meter_bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(meter_bar)
	for piece in banked_glints + [bank_flash, tier_full]:
		piece.visible = false
		add_child(piece)


func _sheet_sprite(path: String, hframes: int, vframes: int, at: Vector2) -> Sprite2D:
	var sprite := Sprite2D.new()
	sprite.texture = load(path)
	sprite.hframes = hframes
	sprite.vframes = vframes
	sprite.centered = false
	sprite.position = at
	return sprite


func _build_stamp(spec: Dictionary, meter_at: Vector2) -> void:
	if spec.has("textures"):
		stamp_textures = spec.textures.map(func(path: String) -> Texture2D: return load(path))
		var sheet := Sprite2D.new()
		sheet.texture = stamp_textures[0]
		sheet.hframes = spec.hframes
		sheet.centered = false
		stamp = sheet
	else:
		var label := Label.new()
		label.theme = load("res://Assets/UI/ui_theme.tres")
		label.add_theme_font_size_override("font_size", FONT_SIZE)
		label.add_theme_constant_override("outline_size", OUTLINE)
		label.add_theme_color_override("font_outline_color", Color(0, 0, 0))
		label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		label.size = spec.size
		label.mouse_filter = Control.MOUSE_FILTER_IGNORE
		stamp = label
	stamp.position = meter_at + spec.offset
	stamp.visible = false
	add_child(stamp)


# The newest bar's stamp, in MASH!'s place, until the next bar banks; none before the first.
func _show_stamp(tier: int) -> void:
	shown_tier = tier
	stamp.visible = tier > 0
	if tier == 0:
		return
	if stamp is Sprite2D:
		(stamp as Sprite2D).texture = stamp_textures[tier - 1]
	else:
		(stamp as Label).text = FinisherArtLayout.tier_stamps().texts[tier - 1]


# On the HUD layer the prompt sits on, but not in the prompt: it stays centred over the fight.
func _build_knight_breaker() -> void:
	var spec := FinisherArtLayout.knight_breaker()
	if spec.has("texture"):
		var sheet := Sprite2D.new()
		sheet.texture = load(spec.texture)
		sheet.hframes = spec.hframes
		sheet.centered = false
		knight_breaker = sheet
	else:
		var label := Label.new()
		label.theme = load("res://Assets/UI/ui_theme.tres")
		label.text = spec.text
		label.size = spec.size
		label.add_theme_font_size_override("font_size", spec.font_size)
		label.add_theme_constant_override("outline_size", spec.outline)
		label.add_theme_color_override("font_outline_color", Color(0, 0, 0))
		label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		label.mouse_filter = Control.MOUSE_FILTER_IGNORE
		knight_breaker = label
	knight_breaker.position = spec.position
	knight_breaker.visible = false
	get_parent().add_child.call_deferred(knight_breaker)


func _show_knight_breaker() -> void:
	if knight_breaker_fade:
		knight_breaker_fade.kill()
	knight_breaker_fade = null
	knight_breaker.modulate.a = 1.0
	knight_breaker.visible = true


func _fade_knight_breaker(after: float) -> void:
	if not knight_breaker.visible:
		return
	if knight_breaker_fade:
		knight_breaker_fade.kill()
	knight_breaker_fade = knight_breaker.create_tween().set_ignore_time_scale(true)
	knight_breaker_fade.tween_interval(after)
	knight_breaker_fade.tween_property(knight_breaker, "modulate:a", 0.0, FinisherArtLayout.knight_breaker().fade_time)
	knight_breaker_fade.tween_callback(knight_breaker.hide)


func _step_knight_breaker(delta: float) -> void:
	if not knight_breaker.visible:
		return
	var spec := FinisherArtLayout.knight_breaker()
	var step := int(Time.get_ticks_msec() / 1000.0 / spec.frame_time) % 2
	if knight_breaker is Sprite2D:
		(knight_breaker as Sprite2D).frame = step
	else:
		(knight_breaker as Label).add_theme_color_override("font_color", spec.colors[step])


func _build_text(spec: Dictionary, at: Vector2) -> void:
	if FinisherArtLayout.USE_FINAL_PROMPT_TEXT:
		text_textures = {false: load(spec.mash), true: load(spec.full)}
		text_sprite = Sprite2D.new()
		text_sprite.texture = text_textures[false]
		text_sprite.hframes = spec.hframes
		text_sprite.centered = false
		text_sprite.position = at
		add_child(text_sprite)
		word_label = _text_label(spec, at)
		word_label.visible = false
		add_child(word_label)
		return
	text_label = _text_label(spec, at)
	add_child(text_label)


func _text_label(spec: Dictionary, at: Vector2) -> Label:
	var label := Label.new()
	label.theme = load("res://Assets/UI/ui_theme.tres")
	label.add_theme_font_size_override("font_size", FONT_SIZE)
	label.add_theme_constant_override("outline_size", OUTLINE)
	label.add_theme_color_override("font_outline_color", Color(0, 0, 0))
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.position = at
	label.size = spec.size
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return label


func _refresh() -> void:
	if tiered_built:
		_show_tier_meter()
	else:
		meter_bar.value = 1.0 if full else finisher.meter
	_show_keys()
	_show_text()
	_place()


func _show_tier_meter() -> void:
	var spec := FinisherArtLayout.tier_meter()
	var banked: int = mini(int(floor(finisher.meter + 1e-6)), 3)
	var share: float = clampf(finisher.meter - banked, 0.0, 1.0)
	if spec.has("frame"):
		meter_bar.value = spec.bar_stride * banked + spec.bar_length * share if banked < 3 else meter_bar.max_value
		var glint_times: Array = spec.banked_frame_times
		for i in 3:
			var glint: Sprite2D = banked_glints[i]
			glint.visible = i < banked
			glint.frame = i * spec.banked_hframes + _looped_step(glint_times, clock)
		if bank_flash_clock >= 0.0:
			var step := _once_step(spec.flash_frame_times, bank_flash_clock)
			bank_flash.visible = step >= 0
			if step >= 0:
				bank_flash.frame = (shown_tier - 1) * spec.flash_hframes + step
			else:
				bank_flash_clock = -1.0
			bank_flash_clock += get_process_delta_time()
		(tier_full as Sprite2D).frame = int(clock / spec.full_frame_time) % spec.full_hframes
	else:
		var first: Rect2 = spec.bars[0]
		meter_bar.value = (spec.bars[banked].position.x - first.position.x + spec.bars[banked].size.x * share) if banked < 3 else meter_bar.max_value
		for i in 3:
			banked_glints[i].visible = i < banked
		(tier_full as ColorRect).color = spec.full_colors[int(clock / spec.full_frame_time) % 2]
		(tier_full as ColorRect).color.a = 0.5
	var stamps := FinisherArtLayout.tier_stamps()
	if stamp.visible:
		var stamp_step := int(clock / stamps.frame_time) % 2
		if stamp is Sprite2D:
			(stamp as Sprite2D).frame = stamp_step
		else:
			(stamp as Label).add_theme_color_override("font_color", stamps.colors[stamp_step])


# The step `time` into a looping run of frames.
func _looped_step(frame_times: Array, time: float) -> int:
	var loop := 0.0
	for frame_time in frame_times:
		loop += frame_time
	var step := _once_step(frame_times, fposmod(time, loop))
	return maxi(step, 0)


# The step `time` into a run of frames played once, or -1 once it's over.
func _once_step(frame_times: Array, time: float) -> int:
	var end := 0.0
	for i in frame_times.size():
		end += frame_times[i]
		if time < end:
			return i
	return -1


func _show_keys() -> void:
	var spec := FinisherArtLayout.keys(gamepad_keys)
	var flashing := actions[0] if int(clock / KEY_FLASH_TIME) % 2 == 0 else actions[1]
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
			# On the pad sheet the look is a row offset, added to the bound button's own column.
			(key as Sprite2D).frame = (InputSettings.pad_frame_for(action) if gamepad_keys else 0) + look[0]
		key.modulate = look[1]
		key.position = key_rest[action] + Vector2(0, look[2])


func _show_text() -> void:
	var spec := FinisherArtLayout.prompt_text()
	var text_frame := int(clock / (spec.full_frame_time if full else spec.mash_frame_time)) % 2
	# A stamp takes MASH!'s place.
	var text_node: CanvasItem = text_sprite if text_sprite else text_label
	text_node.visible = not (tiered_built and stamp.visible)
	if tiered_built:
		if text_sprite:
			text_sprite.texture = text_textures[false]
			text_sprite.frame = text_frame
		else:
			text_label.text = spec.mash
			text_label.add_theme_color_override("font_color", spec.colors[text_frame])
		return
	# MASH! is the drawn word: a finisher asking for any other one has it written out in its place,
	# until the meter fills and FULL! takes over as it always does.
	var key := _prompt_key()
	var written := key != &"mash" and not full
	if word_label:
		word_label.visible = written
	if written:
		var word := FinisherArtLayout.prompt_word(key)
		var label: Label = word_label if word_label else text_label
		label.text = word.text
		label.add_theme_color_override("font_color", word.colors[text_frame])
	if text_sprite:
		text_sprite.visible = text_node.visible and not written
		text_sprite.texture = text_textures[full]
		text_sprite.frame = text_frame
	elif not written:
		text_label.text = spec.full if full else spec.mash
		text_label.add_theme_color_override("font_color", spec.colors[text_frame])
	var meter_spec := FinisherArtLayout.meter()
	var full_frame := int(clock / meter_spec.full_frame_time) % 2
	if full_overlay:
		full_overlay.frame = full_frame
	else:
		meter_fill_style.bg_color = meter_spec.full_colors[full_frame] if full else meter_spec.fill_color


# Which word the finisher wants. A build whose finisher has no prompt_key at all, or one asking for a
# word nobody has written, still shows MASH!.
func _prompt_key() -> StringName:
	var key: Variant = finisher.get(&"prompt_key")
	return key if key is StringName and FinisherArtLayout.PROMPT_WORDS.has(key) else &"mash"


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
