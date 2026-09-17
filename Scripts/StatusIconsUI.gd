extends Control

# The status effects on the player (PlayerStatus), as a row of pulsing icons next to the stamina bar,
# each over a bar counting its time down. The row fades away with nothing on it, and out of a
# dialogue balloon's way like the hype meter and the streak badge do.
# DefenseHypeArtLayout's STATUS ICONS section has the numbers.

const DefenseHypeArtLayout := preload("res://Scripts/DefenseHypeArtLayout.gd")

const BALLOON_SCENE := "res://Scenes/balloon.tscn"

@export var status: Node

# kind -> {icon, bar, full}, in the order they started.
var entries := {}
var clock := 0.0


func _ready() -> void:
	position = DefenseHypeArtLayout.STATUS_ICONS_POSITION
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	modulate.a = 0.0
	status.status_started.connect(_on_started)
	status.status_ended.connect(_on_ended)


func _process(delta: float) -> void:
	# Real seconds, like the other HUD pieces: the row keeps fading through a hit-stop.
	var real_delta := delta / maxf(Engine.time_scale, 0.001)
	clock += real_delta
	var wanted := 1.0 if not entries.is_empty() and not _dialogue_showing() else 0.0
	modulate.a = move_toward(modulate.a, wanted, real_delta / DefenseHypeArtLayout.STATUS_FADE_TIME)
	if entries.is_empty():
		return
	var spec := DefenseHypeArtLayout.status_icons()
	# The dim frame is held longer than the lit one, so the pulse beats rather than blinks evenly.
	var cycle: float = spec.frame_times[0] + spec.frame_times[1]
	var look := 0 if fmod(clock, cycle) < spec.frame_times[0] else 1
	for kind in entries:
		var entry: Dictionary = entries[kind]
		if entry.icon is Sprite2D:
			entry.icon.frame_coords.x = look
		else:
			entry.icon.color = spec.colors[kind][look]
		var left: float = status.time_left(kind)
		entry.bar.size.x = roundf(spec.size.x * clampf(left / entry.full, 0.0, 1.0))


func _on_started(kind: StringName, duration: float) -> void:
	if entries.has(kind):
		entries[kind].full = duration
		return
	var spec := DefenseHypeArtLayout.status_icons()
	var slot: Vector2 = Vector2((spec.size.x + DefenseHypeArtLayout.STATUS_ICON_GAP) * entries.size(), 0.0)
	var icon: CanvasItem
	if spec.has("texture"):
		var sprite := Sprite2D.new()
		sprite.texture = load(spec.texture)
		sprite.hframes = spec.hframes
		sprite.vframes = spec.vframes
		sprite.frame_coords = Vector2i(0, spec.rows[kind])
		sprite.centered = false
		sprite.scale = Vector2.ONE * spec.scale
		icon = sprite
	else:
		var square := ColorRect.new()
		square.size = spec.size
		square.color = spec.colors[kind][0]
		square.mouse_filter = Control.MOUSE_FILTER_IGNORE
		icon = square
	icon.position = slot
	add_child(icon)
	var back := ColorRect.new()
	back.color = DefenseHypeArtLayout.STATUS_BAR_BACK
	back.size = Vector2(spec.size.x, DefenseHypeArtLayout.STATUS_BAR_HEIGHT)
	back.position = slot + Vector2(0.0, spec.size.y + DefenseHypeArtLayout.STATUS_BAR_GAP)
	back.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(back)
	var bar := ColorRect.new()
	bar.color = spec.bar_colors[kind]
	bar.size = back.size
	bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	back.add_child(bar)
	entries[kind] = {"icon": icon, "back": back, "full": duration}
	entries[kind].bar = bar


func _on_ended(kind: StringName) -> void:
	if not entries.has(kind):
		return
	var entry: Dictionary = entries[kind]
	entry.icon.queue_free()
	entry.back.queue_free()
	entries.erase(kind)
	_pack()


func _dialogue_showing() -> bool:
	for child in get_tree().current_scene.get_children():
		if child is CanvasLayer and child.scene_file_path == BALLOON_SCENE and child.visible:
			return true
	return false


# The row closes up, so the one left doesn't sit in a gap.
func _pack() -> void:
	var spec := DefenseHypeArtLayout.status_icons()
	var slot := 0
	for kind in entries:
		var entry: Dictionary = entries[kind]
		var at := Vector2((spec.size.x + DefenseHypeArtLayout.STATUS_ICON_GAP) * slot, 0.0)
		entry.icon.position = at
		entry.back.position = at + Vector2(0.0, spec.size.y + DefenseHypeArtLayout.STATUS_BAR_GAP)
		slot += 1
