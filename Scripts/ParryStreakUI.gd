extends Control

# The parry-streak badge, left of the hype meter: a looping badge whose row is the tier (x1, x2, x3
# and up) with the running count laid over it. It pops on each parry and fades out when the streak
# lapses (PlayerDefense's parry_streak_timeout) or a hit breaks it, and it keeps out of the way of a
# dialogue balloon like the hype meter does.

const DefenseHypeArtLayout := preload("res://Scripts/DefenseHypeArtLayout.gd")

const BALLOON_SCENE := "res://Scenes/balloon.tscn"
# Row 0 of the badge is the first parry, so it shows from the very first one.
const SHOW_FROM := 1

@export var defense: Node

var badge: Sprite2D
var digits: Array[Sprite2D] = []
var label: Label
var streak := 0
# The last tier shown, so the badge keeps its look while it fades out.
var shown_tier := 0
var clock := 0.0
var lift := 0.0
var pop: Tween


func _ready() -> void:
	position = DefenseHypeArtLayout.STREAK_COUNTER_POSITION
	size = DefenseHypeArtLayout.STREAK_COUNTER_SIZE
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	modulate.a = 0.0
	_build(DefenseHypeArtLayout.streak_counter())
	defense.parry_streak_changed.connect(_on_streak_changed)


func _process(delta: float) -> void:
	# Real seconds: the badge keeps animating through a parry's hit-stop.
	var real_delta := delta / maxf(Engine.time_scale, 0.001)
	clock += real_delta
	var wanted := 1.0 if streak >= SHOW_FROM and not _dialogue_showing() else 0.0
	modulate.a = move_toward(modulate.a, wanted, real_delta / DefenseHypeArtLayout.STREAK_COUNTER_FADE_TIME)
	if modulate.a <= 0.0:
		return
	var spec := DefenseHypeArtLayout.streak_counter()
	if badge:
		badge.frame_coords = Vector2i(int(clock / spec.frame_time) % spec.hframes, shown_tier)
	else:
		label.add_theme_color_override("font_color", spec.colors[int(clock / spec.frame_time) % 2])
	position = (DefenseHypeArtLayout.STREAK_COUNTER_POSITION - Vector2(0, roundf(lift))).round()


func _on_streak_changed(to_streak: int) -> void:
	streak = to_streak
	if streak < SHOW_FROM:
		return
	shown_tier = mini(streak - 1, DefenseHypeArtLayout.streak_counter().get("vframes", 1) - 1)
	_show_count()
	if pop:
		pop.kill()
	pop = create_tween().set_ignore_time_scale(true)
	pop.tween_method(func(height: float) -> void: lift = height, DefenseHypeArtLayout.STREAK_COUNTER_POP, 0.0, DefenseHypeArtLayout.STREAK_COUNTER_POP_TIME).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)


# One digit sits centred on the badge, two side by side.
func _show_count() -> void:
	var spec := DefenseHypeArtLayout.streak_counter()
	if not badge:
		label.text = spec.text % streak
		return
	var shown := str(mini(streak, 99))
	var places: Array = spec.digit_offsets[shown.length() - 1]
	for i in digits.size():
		var used := i < shown.length()
		digits[i].visible = used
		if used:
			digits[i].frame = shown.unicode_at(i) - 48
			digits[i].position = places[i]


func _dialogue_showing() -> bool:
	for child in get_tree().current_scene.get_children():
		if child is CanvasLayer and child.scene_file_path == BALLOON_SCENE and child.visible:
			return true
	return false


func _build(spec: Dictionary) -> void:
	if spec.has("texture"):
		badge = Sprite2D.new()
		badge.texture = load(spec.texture)
		badge.hframes = spec.hframes
		badge.vframes = spec.vframes
		badge.centered = false
		add_child(badge)
		for i in 2:
			var digit := Sprite2D.new()
			digit.texture = load(spec.digits)
			digit.hframes = spec.digit_hframes
			digit.centered = false
			digit.visible = false
			add_child(digit)
			digits.append(digit)
		return
	label = Label.new()
	label.theme = load("res://Assets/UI/ui_theme.tres")
	label.add_theme_font_size_override("font_size", spec.font_size)
	label.add_theme_constant_override("outline_size", spec.outline)
	label.add_theme_color_override("font_outline_color", Color(0, 0, 0))
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	label.size = size
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(label)
