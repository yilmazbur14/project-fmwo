extends Control

# The hype meter, in the bottom-right corner. It pops on a gain and glows while full. It hides in a
# fight where hype is inert, and fades out while a dialogue balloon or the finisher's prompt wants
# that corner.

const DefenseHypeArtLayout := preload("res://Scripts/DefenseHypeArtLayout.gd")

const BALLOON_SCENE := "res://Scenes/balloon.tscn"

@export var hype: Node
@export var finisher_prompt: Node2D

var bar: Range
var fill_style: StyleBoxFlat
var full_overlay: Sprite2D
var label_sprite: Sprite2D
var label: Label
var clock := 0.0
var lift := 0.0
var pop: Tween


func _ready() -> void:
	var spec := DefenseHypeArtLayout.hype()
	position = DefenseHypeArtLayout.HYPE_METER_POSITION
	size = spec.size
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	modulate.a = 0.0
	_build(spec)
	bar.max_value = hype.max_hype
	_show(hype.hype)
	hype.hype_changed.connect(_on_hype_changed)


func _process(delta: float) -> void:
	visible = not hype.is_inert()
	if not visible:
		return
	# Real seconds: the meter keeps animating through hit-stop and the finisher's freeze.
	var real_delta := delta / maxf(Engine.time_scale, 0.001)
	clock += real_delta
	var wanted := 0.0 if (_dialogue_showing() or _prompt_overlaps()) else 1.0
	modulate.a = move_toward(modulate.a, wanted, real_delta / DefenseHypeArtLayout.HYPE_FADE_TIME)
	var spec := DefenseHypeArtLayout.hype()
	var glow := int(clock / spec.full_frame_time)
	if full_overlay:
		full_overlay.visible = hype.is_full()
		full_overlay.frame = glow % full_overlay.hframes
		label_sprite.frame = 1 if hype.is_full() else 0
	else:
		fill_style.bg_color = spec.full_colors[glow % 2] if hype.is_full() else spec.fill_color
		label.add_theme_color_override("font_color", spec.label_colors[glow % 2] if hype.is_full() else spec.label_colors[0])
	position = (DefenseHypeArtLayout.HYPE_METER_POSITION - Vector2(0, roundf(lift))).round()


func _on_hype_changed(value: float, max_value: float) -> void:
	bar.max_value = max_value
	_show(value)
	if pop:
		pop.kill()
	pop = create_tween().set_ignore_time_scale(true)
	pop.tween_method(func(height: float) -> void: lift = height, DefenseHypeArtLayout.HYPE_POP_TEXELS, 0.0, DefenseHypeArtLayout.HYPE_POP_TIME).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)


# Final art is revealed in whole texels, so the fill's edge never cuts through one.
func _show(value: float) -> void:
	if full_overlay:
		var texels: int = DefenseHypeArtLayout.hype().fill_texels
		value = floorf(value / bar.max_value * texels + 0.001) / texels * bar.max_value
	bar.value = value


func _dialogue_showing() -> bool:
	for child in get_tree().current_scene.get_children():
		if child is CanvasLayer and child.scene_file_path == BALLOON_SCENE and child.visible:
			return true
	return false


func _prompt_overlaps() -> bool:
	if finisher_prompt == null or not finisher_prompt.visible:
		return false
	return Rect2(finisher_prompt.position, finisher_prompt.prompt_size).intersects(Rect2(position, size))


func _build(spec: Dictionary) -> void:
	if DefenseHypeArtLayout.USE_FINAL_HYPE:
		var texture_bar := TextureProgressBar.new()
		texture_bar.texture_under = load(spec.frame)
		texture_bar.texture_progress = load(spec.fill)
		texture_bar.texture_progress_offset = spec.fill_offset
		texture_bar.fill_mode = TextureProgressBar.FILL_LEFT_TO_RIGHT
		bar = texture_bar
		full_overlay = Sprite2D.new()
		full_overlay.texture = load(spec.full)
		full_overlay.hframes = spec.full_hframes
		full_overlay.centered = false
		full_overlay.visible = false
		label_sprite = Sprite2D.new()
		label_sprite.texture = load(spec.label)
		label_sprite.hframes = spec.label_hframes
		label_sprite.centered = false
		label_sprite.position = spec.label_offset
	else:
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
		label = Label.new()
		label.theme = load("res://Assets/UI/ui_theme.tres")
		label.text = spec.text
		label.add_theme_font_size_override("font_size", spec.font_size)
		label.add_theme_constant_override("outline_size", spec.outline)
		label.add_theme_color_override("font_outline_color", Color(0, 0, 0))
		label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		label.position = spec.label_rect.position
		label.size = spec.label_rect.size
		label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	bar.min_value = 0.0
	bar.step = 0.0
	bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bar)
	if full_overlay:
		add_child(full_overlay)
	# Drawn last, over the frame and the glow.
	add_child(label_sprite if label_sprite else label)
