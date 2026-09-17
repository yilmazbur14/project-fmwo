extends Control

# The stamina bar under the hearts. A spend drains off it quickly, a refused dash flashes it red, it
# shows its low look below the dash cost, blinks while the guard is broken and dims while holding
# block keeps it from refilling.

const DefenseHypeArtLayout := preload("res://Scripts/DefenseHypeArtLayout.gd")

@export var defense: Node

var bar: Range
var fill_style: StyleBoxFlat
var fill_texture: Texture2D
var low_textures: Array[Texture2D] = []
var broken_overlay: Sprite2D
var target := 0.0
var drop: Tween
var flash: Tween
var clock := 0.0


func _ready() -> void:
	position = DefenseHypeArtLayout.STAMINA_BAR_POSITION
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build(DefenseHypeArtLayout.stamina())
	bar.max_value = defense.max_stamina
	target = defense.stamina
	_show(target)
	defense.stamina_changed.connect(_on_stamina_changed)
	defense.stamina_refused.connect(_on_stamina_refused)


func _process(delta: float) -> void:
	clock += delta
	var spec := DefenseHypeArtLayout.stamina()
	var low: bool = defense.stamina < defense.dash_stamina_cost
	var broken_frame := int(clock / spec.broken_frame_time) % 2
	if broken_overlay:
		var texture_bar := bar as TextureProgressBar
		texture_bar.texture_progress = low_textures[int(clock / spec.low_frame_time) % low_textures.size()] if low else fill_texture
		broken_overlay.visible = defense.is_guard_broken
		broken_overlay.frame = broken_frame
	elif defense.is_guard_broken:
		fill_style.bg_color = spec.broken_colors[broken_frame]
	else:
		fill_style.bg_color = spec.low_color if low else spec.fill_color
	bar.self_modulate = DefenseHypeArtLayout.STAMINA_PAUSED_DIM if defense.is_regen_paused() else Color.WHITE


func _on_stamina_changed(value: float, max_value: float) -> void:
	bar.max_value = max_value
	var dropping := value < target
	target = value
	if drop:
		drop.kill()
	if not dropping:
		_show(value)
		return
	# Keeps draining through hit-stop.
	drop = create_tween().set_ignore_time_scale(true)
	drop.tween_method(_show, bar.value, value, DefenseHypeArtLayout.STAMINA_DROP_TIME)


func _on_stamina_refused() -> void:
	if flash:
		flash.kill()
	modulate = DefenseHypeArtLayout.STAMINA_REFUSED_FLASH
	flash = create_tween().set_ignore_time_scale(true)
	flash.tween_property(self, "modulate", Color.WHITE, DefenseHypeArtLayout.STAMINA_REFUSED_FLASH_TIME)


# Final art is revealed in whole texels, so the fill's edge never cuts through one.
func _show(value: float) -> void:
	if broken_overlay:
		var texels: int = DefenseHypeArtLayout.stamina().fill_texels
		value = floorf(value / bar.max_value * texels + 0.001) / texels * bar.max_value
	bar.value = value


func _build(spec: Dictionary) -> void:
	if DefenseHypeArtLayout.USE_FINAL_STAMINA:
		var texture_bar := TextureProgressBar.new()
		texture_bar.texture_under = load(spec.frame)
		fill_texture = load(spec.fill)
		var strip: Texture2D = load(spec.low)
		var frame_width: float = strip.get_width() / float(spec.low_frames)
		# One frame at a time: the whole strip as the progress texture would reveal both frames.
		for i in spec.low_frames:
			var frame := AtlasTexture.new()
			frame.atlas = strip
			frame.region = Rect2(frame_width * i, 0, frame_width, strip.get_height())
			low_textures.append(frame)
		texture_bar.texture_progress = fill_texture
		texture_bar.texture_progress_offset = spec.fill_offset
		texture_bar.fill_mode = TextureProgressBar.FILL_LEFT_TO_RIGHT
		bar = texture_bar
		broken_overlay = Sprite2D.new()
		broken_overlay.texture = load(spec.broken)
		broken_overlay.hframes = spec.broken_hframes
		broken_overlay.centered = false
		broken_overlay.visible = false
	else:
		# Styled like the boss health bars.
		var flat_bar := ProgressBar.new()
		flat_bar.show_percentage = false
		flat_bar.position = spec.bar_rect.position
		flat_bar.size = spec.bar_rect.size
		var background := StyleBoxFlat.new()
		background.bg_color = Color(0.08, 0.08, 0.08, 0.85)
		background.set_corner_radius_all(3)
		background.set_border_width_all(2)
		background.border_color = Color(0, 0, 0)
		flat_bar.add_theme_stylebox_override("background", background)
		fill_style = StyleBoxFlat.new()
		fill_style.bg_color = spec.fill_color
		fill_style.set_corner_radius_all(3)
		flat_bar.add_theme_stylebox_override("fill", fill_style)
		bar = flat_bar
	bar.min_value = 0.0
	bar.step = 0.0
	bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bar)
	if broken_overlay:
		add_child(broken_overlay)
