extends SceneTree

# Drives the HUD the way a fight does and prints what it ends up looking like: the boss bar under
# damage and heat, the two-body panel's ghosts, beat and grey-out, and the player's containers at
# every half-heart. Compare against what the old inline bars did.
#   Godot.exe --headless --fixed-fps 60 --script res://art_source/hud_pass/verify_hud_live.gd

const BossHealthBarUI := preload("res://Scripts/BossHealthBarUI.gd")
const BossBarArtLayout := preload("res://Scripts/BossBarArtLayout.gd")
const PlayerHealthArtLayout := preload("res://Scripts/PlayerHealthArtLayout.gd")
const Balloon := preload("res://Scripts/balloon.gd")

var layer: CanvasLayer
var eric: Control
var pair: Control
var hearts: Control
var frame := 0


func _initialize() -> void:
	layer = CanvasLayer.new()
	get_root().add_child(layer)


# Built a frame in, so the components' _ready has run before anything is asked of them.
func _build() -> void:
	eric = BossHealthBarUI.create({
		"rows": [{"key": &"eric", "max": 24, "value": 24}],
		"plate": &"eric", "text": "ERIC"})
	layer.add_child(eric)

	pair = BossHealthBarUI.create({
		"rows": [{"key": &"greyson", "max": 10, "value": 10}, {"key": &"computah", "max": 10, "value": 10}],
		"plate": &"greyson_pair", "text": "GREYSON & COMPUTAH"})
	layer.add_child(pair)

	hearts = load("res://Scenes/Player/PlayerHealthScene.tscn").instantiate()
	layer.add_child(hearts)

	print("dialogue offset_left: %.1f (was 300.0)" % (PlayerHealthArtLayout.row_right_edge() + Balloon.FIGHT_PANEL_GAP))

	print("-- eric heat ladder --")
	for pair_of in [[24.0, 0.0], [14.0, 0.5], [6.0, 1.0]]:
		eric.set_value(0, pair_of[0])
		eric.set_heat(0, pair_of[1])
		print("  value %.0f heat %.1f -> fill %s bar %.2f/%.2f" % [pair_of[0], pair_of[1],
			_hex(eric.rows[0].fill_style.bg_color), eric.rows[0].bar.value, eric.rows[0].bar.max_value])

	print("-- pair --")
	pair.set_value(0, 8.0)
	pair.set_ghost(0, 1.0, true)
	pair.set_ghost(1, 0.8, true)
	pair.set_heat(1, 0.6)
	pair.set_beat(1, 0.6)
	_report_pair()
	print("-- greyson row low (ratio 0.2) --")
	pair.set_value(0, 2.0)
	pair.set_heat(0, 0.0)
	print("  row0 fill %s (BAR_FILL_LOW[0] was #eb6b70)" % _hex(pair.rows[0].fill_style.bg_color))
	print("-- computah finished --")
	pair.set_value(1, 0.0)
	pair.finish_row(1)
	print("  row1 fill %s dim %s ghost %s" % [_hex(pair.rows[1].fill_style.bg_color),
		_hex(pair.rows[1].node.modulate), pair.rows[1].ghost.visible])

	print("-- player containers --")
	for health in [6, 5, 4, 3, 2, 1, 0]:
		hearts.update_health(health)
		var names := PackedStringArray()
		for rect in hearts.containers:
			names.append(rect.texture.resource_path.get_file().get_basename())
		print("  %d -> %s" % [health, ", ".join(names)])


# A few frames of the beat, to prove the loop runs and puts the row back when it stops.
func _process(_delta: float) -> bool:
	frame += 1
	if frame == 1:
		_build()
		print("-- beat --")
	if frame <= 24 and frame % 8 == 0:
		print("  frame %d row1 alpha %.3f" % [frame, pair.rows[1].node.modulate.a])
	if frame == 25:
		pair.set_beat(1, 0.0)
		print("  beat off -> row1 alpha %.3f" % pair.rows[1].node.modulate.a)
		quit(0)
	return false


func _report_pair() -> void:
	for i in 2:
		var row: Dictionary = pair.rows[i]
		print("  row%d bar %.2f/%.2f at %s size %s fill %s ghost x %.1f shown %s" % [i,
			row.bar.value, row.bar.max_value, _v(row.bar.get_global_transform().origin),
			_v(row.bar.size), _hex(row.fill_style.bg_color),
			row.ghost.get_global_transform().origin.x, row.ghost.visible])


func _v(v: Vector2) -> String:
	return "(%.1f,%.1f)" % [v.x, v.y]


func _hex(c: Color) -> String:
	return "#%02x%02x%02x" % [roundi(c.r * 255), roundi(c.g * 255), roundi(c.b * 255)]
