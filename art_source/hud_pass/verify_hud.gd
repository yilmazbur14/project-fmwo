extends SceneTree

# Dumps every HUD node a fight builds, so the boss-bar/hearts refactor can be proved to change
# nothing on screen: run it before the change, run it after, diff the two files.
#   Godot.exe --headless --fixed-fps 60 --script res://art_source/hud_pass/verify_hud.gd -- fight=eric
# With no fight= it walks every fight in SCENES. flat=1 drops the tree and the node names and prints
# only what actually draws, in global screen px and sorted, so a diff survives the HUD being rebuilt
# out of different nodes.

const SCENES := {
	"eric": "res://Scenes/Bosses/EricBossFightScene.tscn",
	"greyson": "res://Scenes/Bosses/GreysonBossFightScene.tscn",
	"carter": "res://Scenes/Bosses/CarterBossFightScene.tscn",
	"josh": "res://Scenes/Bosses/JoshBossFightScene.tscn",
	"mason": "res://Scenes/Bosses/MasonBossFightScene.tscn",
	"jordan": "res://Scenes/Bosses/JordanBossFightScene.tscn",
	"liam": "res://Scenes/Bosses/LiamBossFightScene.tscn",
	"carter_josh": "res://Scenes/Bosses/CarterAndJoshBossFightScene.tscn",
}

var queue: Array = []
var frame := 0
var settle_frames := 12
var flat := false
var lines: Array = []


func _initialize() -> void:
	var only := ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("frames="):
			settle_frames = int(arg.substr(7))
		if arg.begins_with("fight="):
			only = arg.substr(6)
		if arg == "flat=1":
			flat = true
	for key in SCENES:
		if only == "" or only == key:
			queue.append(key)
	_load_next()


func _load_next() -> void:
	if queue.is_empty():
		quit(0)
		return
	var key: String = queue.front()
	change_scene_to_file(SCENES[key])
	frame = 0


func _process(_delta: float) -> bool:
	if queue.is_empty():
		return true
	frame += 1
	if frame < settle_frames:
		return false
	var key: String = queue.pop_front()
	print("=== %s ===" % key)
	lines.clear()
	for layer in _canvas_layers(current_scene):
		_dump(layer, 0)
	if flat:
		lines.sort()
		for line in lines:
			print(line)
	_load_next()
	return false


func _canvas_layers(node: Node) -> Array:
	var out: Array = []
	if node == null:
		return out
	if node is CanvasLayer:
		out.append(node)
	for child in node.get_children():
		out.append_array(_canvas_layers(child))
	return out


func _dump(node: Node, depth: int) -> void:
	var bits := PackedStringArray()
	var draws := false
	if node is Control:
		var c := node as Control
		bits.append("at=%s size=%s" % [_v(_where(c)), _v(c.size)])
		bits.append("shown=%s mod=%s" % [c.is_visible_in_tree(), _c(_tint(c))])
	if node is Label:
		var l := node as Label
		draws = true
		bits.append("text=%s" % l.text)
		bits.append("font=%d outline=%d" % [l.get_theme_font_size("font_size"), l.get_theme_constant("outline_size")])
		bits.append("colour=%s" % _c(l.get_theme_color("font_color")))
	if node is Range:
		var r := node as Range
		bits.append("value=%.3f/%.3f" % [r.value, r.max_value])
	if node is ProgressBar:
		var p := node as ProgressBar
		draws = true
		bits.append("pct=%s" % p.show_percentage)
		for part in ["background", "fill"]:
			var box := p.get_theme_stylebox(part)
			if box is StyleBoxFlat:
				var f := box as StyleBoxFlat
				bits.append("%s bg=%s radius=%d border=%d/%s" % [part, _c(f.bg_color),
					f.corner_radius_top_left, f.border_width_left, _c(f.border_color)])
	if node is TextureProgressBar:
		var t := node as TextureProgressBar
		draws = true
		bits.append("fill=%s at=%s" % [t.texture_progress.resource_path if t.texture_progress else "-",
			_v(t.texture_progress_offset)])
	if node is Panel:
		draws = true
		var box := (node as Panel).get_theme_stylebox("panel")
		if box is StyleBoxFlat:
			var f := box as StyleBoxFlat
			bits.append("panel bg=%s radius=%d border=%d/%s" % [_c(f.bg_color),
				f.corner_radius_top_left, f.border_width_left, _c(f.border_color)])
	if node is ColorRect:
		draws = true
		bits.append("rect colour=%s" % _c((node as ColorRect).color))
	if node is TextureRect:
		var t := node as TextureRect
		draws = true
		bits.append("tex=%s expand=%d stretch=%d" % [t.texture.resource_path if t.texture else "-",
			t.expand_mode, t.stretch_mode])
	if node is Sprite2D:
		var s := node as Sprite2D
		draws = true
		bits.append("tex=%s frame=%d/%d at=%s shown=%s mod=%s" % [s.texture.resource_path if s.texture else "-",
			s.frame, s.hframes * s.vframes, _v(_where(s)), s.is_visible_in_tree(), _c(_tint(s))])
	if flat:
		if draws:
			lines.append(" | ".join(bits))
	else:
		print("  ".repeat(depth) + " | ".join(PackedStringArray([node.name, node.get_class()]) + bits))
	for child in node.get_children():
		_dump(child, depth + 1)


# Screen px, so a piece that moved into a wrapper still lands in the same place.
func _where(item: CanvasItem) -> Vector2:
	return item.get_global_transform().origin


# Every modulate down the branch, which is what a dimmed row actually looks like.
func _tint(item: CanvasItem) -> Color:
	var tint: Color = item.modulate
	var parent := item.get_parent()
	while parent is CanvasItem:
		tint *= (parent as CanvasItem).modulate
		parent = parent.get_parent()
	return tint


func _v(v: Vector2) -> String:
	return "(%.1f,%.1f)" % [v.x, v.y]


func _c(c: Color) -> String:
	return "#%02x%02x%02x%02x" % [roundi(c.r * 255), roundi(c.g * 255), roundi(c.b * 255), roundi(c.a * 255)]
