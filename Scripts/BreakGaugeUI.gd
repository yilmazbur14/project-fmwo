extends Control

# A boss's Break gauge (BossBreakGauge): a brass gauge on the top rope, or a thin bar under his
# health bar while the art is off. It pulses as it nears full, shatters under a BREAK! when he
# breaks, and sits dimmed while it takes nothing afterwards. It runs on real seconds, so it plays out
# through the Break's own hit-stop. The fight builds it at runtime, the way it builds the health bar
# above it.
# The shatter and the word run on tweens that ignore the time scale, not on _process: the Break sets
# the hit-stop in the same frame the shatter starts, after that frame's delta was scaled, and dividing
# it by the new time scale would skip most of the shatter.
# Every number it draws with comes from `spec`. A fight that sets none gets Eric's, whose gauge this
# was first, so his and Mason's builds keep working without passing one.

const EricArtLayout := preload("res://Scripts/EricArtLayout.gd")
const HudPlayerFade := preload("res://Scripts/HudPlayerFade.gd")

# Both set by the fight before it is added.
var gauge: Node
# Which boss's gauge to draw: the layout dictionary, resolved once in _ready.
var spec: Dictionary = {}

var bar: Range
var fill_tween: Tween
var clock := 0.0
# The drawn gauge's pulse: the overlay on its brass, and its fill with a hot one for each overlay frame.
var pulse: Sprite2D
var fill: Texture2D
var hot_fills: Array[Texture2D] = []
# The placeholder shatter's shards, each [node, start, velocity, spin].
var shards: Array = []
var shatter: Sprite2D
var shatter_tween: Tween
# The BREAK! word: drawn, or a label until it is.
var word_sheet: Sprite2D
var word_label: Label
var word_tween: Tween


func _ready() -> void:
	if spec.is_empty():
		spec = EricArtLayout.break_gauge()
	position = spec.position
	size = spec.size
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build()
	HudPlayerFade.wrap(self)
	bar.value = _bar_value(gauge.value, gauge.max_value)
	gauge.changed.connect(_on_changed)
	gauge.broke.connect(_on_broke)


# The pulse is a loop, so a frame where the time scale changed only shifts its phase.
func _process(delta: float) -> void:
	clock += delta / maxf(Engine.time_scale, 0.001)
	var hot: bool = not gauge.locked and gauge.value >= gauge.max_value * spec.get("pulse_from", 0.8)
	bar.modulate = spec.locked_modulate if gauge.locked else Color.WHITE
	if pulse:
		pulse.visible = hot
		if hot:
			pulse.frame = _looped_frame(spec.pulse_frame_times, clock)
		(bar as TextureProgressBar).texture_progress = hot_fills[pulse.frame] if hot else fill
	elif hot and int(clock / spec.pulse_time) % 2 == 0:
		bar.modulate = spec.pulse_modulate


func _on_changed(value: float, max_value: float) -> void:
	if fill_tween:
		fill_tween.kill()
	fill_tween = create_tween().set_ignore_time_scale(true)
	fill_tween.tween_property(bar, "value", _bar_value(value, max_value), spec.get("fill_time", 0.15))


# The bar counts in the art's whole texels where it has them, so the fill steps a texel at a time.
func _bar_value(value: float, max_value: float) -> float:
	return value / max_value * bar.max_value


# The bar empties at once: what is left of the fill is the shatter.
func _on_broke() -> void:
	if fill_tween:
		fill_tween.kill()
	bar.value = 0.0
	_play_word()
	if shatter:
		_play_shatter(spec.shatter_frame_times)
		return
	for shard in shards:
		shard[0].queue_free()
	shards.clear()
	var count: int = spec.shards
	for i in count:
		var piece := ColorRect.new()
		piece.color = spec.fill_color
		piece.size = spec.shard_size
		piece.pivot_offset = piece.size / 2.0
		piece.mouse_filter = Control.MOUSE_FILTER_IGNORE
		piece.position = Vector2((i + 0.5) * size.x / count, size.y / 2.0) - piece.size / 2.0
		var up := -1.0 if i % 2 == 0 else 1.0
		var heading := Vector2(randf_range(-0.6, 0.6), up).normalized()
		add_child(piece)
		shards.append([piece, piece.position, heading * randf_range(spec.shard_speed.x, spec.shard_speed.y), randf_range(-12.0, 12.0)])
	if shatter_tween:
		shatter_tween.kill()
	shatter_tween = create_tween().set_ignore_time_scale(true)
	shatter_tween.tween_method(_fly_shards.bind(spec.shatter_time), 0.0, spec.shatter_time, spec.shatter_time)
	shatter_tween.tween_callback(_clear_shards)


func _play_shatter(frame_times: Array) -> void:
	if shatter_tween:
		shatter_tween.kill()
	shatter.frame = 0
	shatter.show()
	shatter_tween = shatter.create_tween().set_ignore_time_scale(true)
	for i in range(1, frame_times.size()):
		shatter_tween.tween_interval(frame_times[i - 1])
		shatter_tween.tween_callback(shatter.set_frame.bind(i))
	shatter_tween.tween_interval(frame_times[-1])
	shatter_tween.tween_callback(shatter.hide)


func _fly_shards(time: float, shatter_time: float) -> void:
	for shard in shards:
		shard[0].position = shard[1] + shard[2] * time
		shard[0].rotation = shard[3] * time
		shard[0].modulate.a = clampf(1.0 - time / shatter_time, 0.0, 1.0)


func _clear_shards() -> void:
	for shard in shards:
		shard[0].queue_free()
	shards.clear()


# It flips its frames or colours, holds, then fades over its last third.
func _play_word() -> void:
	if word_tween:
		word_tween.kill()
	var word := _word()
	word.modulate.a = 1.0
	_pose_word(0.0)
	word.show()
	word_tween = word.create_tween().set_ignore_time_scale(true).set_parallel(true)
	word_tween.tween_method(_pose_word, 0.0, spec.word_time, spec.word_time)
	word_tween.tween_property(word, "modulate:a", 0.0, spec.word_time / 3.0).set_delay(spec.word_time * 2.0 / 3.0)
	word_tween.chain().tween_callback(word.hide)


func _pose_word(time: float) -> void:
	var step := int(time / spec.word_frame_time)
	var rise := Vector2(0, spec.word_rise * time / spec.word_time)
	if word_sheet:
		word_sheet.frame = step % word_sheet.hframes
		word_sheet.position = spec.word_offset - rise
	else:
		word_label.add_theme_color_override("font_color", spec.word_colors[step % spec.word_colors.size()])
		word_label.position = Vector2(0, -spec.word_size.y) - rise


func _word() -> CanvasItem:
	return word_sheet if word_sheet else word_label


func _looped_frame(frame_times: Array, time: float) -> int:
	var loop := 0.0
	for frame_time in frame_times:
		loop += frame_time
	var into := fposmod(time, loop)
	var end := 0.0
	for i in frame_times.size():
		end += frame_times[i]
		if into < end:
			return i
	return frame_times.size() - 1


func _build() -> void:
	if spec.has("frame"):
		var texture_bar := TextureProgressBar.new()
		texture_bar.texture_under = load(spec.frame)
		fill = load(spec.fill)
		texture_bar.texture_progress = fill
		texture_bar.texture_progress_offset = spec.fill_offset
		texture_bar.fill_mode = TextureProgressBar.FILL_LEFT_TO_RIGHT
		texture_bar.max_value = spec.fill_steps
		texture_bar.step = 1.0
		bar = texture_bar
		var hot: Texture2D = load(spec.fill_hot)
		var hot_size := Vector2(hot.get_width() / float(spec.pulse_hframes), hot.get_height())
		for i in spec.pulse_hframes:
			var frame := AtlasTexture.new()
			frame.atlas = hot
			frame.region = Rect2(Vector2(hot_size.x * i, 0), hot_size)
			hot_fills.append(frame)
		pulse = _sheet(spec.pulse, spec.pulse_hframes, spec.pulse_offset)
		shatter = _sheet(spec.shatter, spec.shatter_hframes, spec.shatter_offset)
		word_sheet = _sheet(spec.word_texture, spec.word_hframes, spec.word_offset)
	else:
		var flat_bar := ProgressBar.new()
		flat_bar.show_percentage = false
		flat_bar.size = size
		var background := StyleBoxFlat.new()
		background.bg_color = Color(0.08, 0.08, 0.08, 0.85)
		background.set_border_width_all(2)
		background.border_color = Color(0, 0, 0)
		flat_bar.add_theme_stylebox_override("background", background)
		var fill_style := StyleBoxFlat.new()
		fill_style.bg_color = spec.fill_color
		flat_bar.add_theme_stylebox_override("fill", fill_style)
		flat_bar.max_value = gauge.max_value
		flat_bar.step = 0.0
		bar = flat_bar
		word_label = Label.new()
		word_label.theme = load("res://Assets/UI/ui_theme.tres")
		word_label.text = spec.word
		word_label.size = spec.word_size
		word_label.add_theme_font_size_override("font_size", spec.font_size)
		word_label.add_theme_constant_override("outline_size", spec.outline)
		word_label.add_theme_color_override("font_outline_color", Color(0, 0, 0))
		word_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		word_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		word_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	bar.min_value = 0.0
	bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bar)
	for piece in [pulse, shatter]:
		if piece:
			piece.hide()
			add_child(piece)
	_word().hide()
	add_child(_word())


func _sheet(path: String, hframes: int, at: Vector2) -> Sprite2D:
	var sheet := Sprite2D.new()
	sheet.texture = load(path)
	sheet.hframes = hframes
	sheet.centered = false
	sheet.position = at
	return sheet
