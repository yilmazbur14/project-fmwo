extends SceneTree

# Checks the finished-row latch: once a row is spent, nothing the fight does afterwards repaints it
# or brings its ghost marker back. The two-body fights refresh every row on any change, which is how
# a dead bar used to get its live colour and its white tick painted back over the grey.
#   Godot.exe --headless --fixed-fps 60 --script res://art_source/hud_pass/verify_dead_row.gd

const BossHealthBarUI := preload("res://Scripts/BossHealthBarUI.gd")
const BossBarArtLayout := preload("res://Scripts/BossBarArtLayout.gd")

var layer: CanvasLayer
var pair: Control
var frame := 0
var fails := 0


func _initialize() -> void:
	layer = CanvasLayer.new()
	get_root().add_child(layer)


func check(ok: bool, label: String, detail := "") -> void:
	if ok:
		print("P PASS ", label, "  ", detail)
	else:
		fails += 1
		print("F FAIL ", label, "  ", detail)


func _process(_delta: float) -> bool:
	frame += 1
	if frame == 2:
		pair = BossHealthBarUI.create({
			"rows": [
				{"key": &"greyson", "max": 20, "value": 20},
				{"key": &"computah", "max": 20, "value": 20},
			],
			"plate": &"greyson_pair",
			"text": "GREYSON & COMPUTAH",
		})
		layer.add_child(pair)
		return false

	if frame == 4:
		# Row 0 dies. Row 1 lives on, which is what makes the fight keep refreshing both.
		pair.set_ghost(0, 0.5, true)
		pair.finish_row(0)
		return false

	if frame == 8:
		var spec: Dictionary = pair.rows[0]
		var dead_dim: Color = spec.node.modulate
		var dead_fill := Color.TRANSPARENT
		if spec.has("fill_style"):
			dead_fill = spec.fill_style.bg_color
		check(not spec.ghost.visible, "the dead row's marker is gone once it is finished")
		check(dead_dim.is_equal_approx(BossBarArtLayout.DEAD_DIM),
			"the dead row is dimmed", str(dead_dim))

		# Now do exactly what a two-body fight does on the next hit to the survivor: refresh both
		# rows, re-assert the ghosts, and push heat. None of it may touch row 0.
		pair.set_value(1, 14.0)
		pair.set_value(0, 0.0)
		pair.set_heat(0, 1.0)
		pair.set_heat(1, 0.6)
		pair.set_ghost(0, 0.7, true)
		pair.set_ghost(1, 0.0, true)
		pair.set_max(0, 20.0)
		return false

	if frame == 12:
		var spec: Dictionary = pair.rows[0]
		check(not spec.ghost.visible, "and it stays gone after the fight refreshes every row")
		check(spec.node.modulate.is_equal_approx(BossBarArtLayout.DEAD_DIM),
			"the dead row is still dimmed", str(spec.node.modulate))
		if spec.has("fill_style"):
			check(spec.fill_style.bg_color.is_equal_approx(BossBarArtLayout.DEAD_FILL),
				"the dead row keeps its dead colour through heat and refresh",
				str(spec.fill_style.bg_color))

		var alive: Dictionary = pair.rows[1]
		check(alive.ghost.visible, "the surviving row's marker still works")
		check(not alive.node.modulate.is_equal_approx(BossBarArtLayout.DEAD_DIM),
			"the surviving row is untouched by the latch")

		# A new phase must bring a finished row back.
		pair.refill_row(0, 20.0, 0.1)
		return false

	if frame == 20:
		var spec: Dictionary = pair.rows[0]
		check(not spec.finished, "a refill lifts the latch, so a phase can revive a row")
		pair.set_ghost(0, 0.5, true)
		return false

	if frame == 22:
		check(pair.rows[0].ghost.visible, "and the revived row's marker works again")
		print("RESULT fails=", fails)
		quit(1 if fails > 0 else 0)
	return false
