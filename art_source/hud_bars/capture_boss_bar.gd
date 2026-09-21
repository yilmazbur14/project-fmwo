extends SceneTree

# Windowed shots of the drawn boss health block over a real fight, one per state the art has, so the
# HUD can be judged where it is actually seen rather than in a composited preview.
#   Godot.exe --path . --position 100,100 --resolution 1920x1080 --max-fps 60 \
#     --script res://art_source/hud_bars/capture_boss_bar.gd -- fight=eric out=<dir>
# --max-fps 60 is not optional: uncapped, this scene runs frames far faster than the HUD's
# real-seconds feedback plays, and a settled shot catches the chip trail still crossing the bar.
# fight=eric is the single-bar block with its daze meter under it; fight=greyson is the two-bar pair.
# Each shot is the whole 1920x1080 frame plus a crop of the block, and the block's measured geometry
# is printed alongside.

const FIGHTS := {
	"eric": "res://Scenes/Bosses/EricBossFightScene.tscn",
	"greyson": "res://Scenes/Bosses/GreysonBossFightScene.tscn",
}
# The block and its daze meter, with room for the plate above and the crest below.
const CROP := Rect2i(690, 0, 540, 300)

var fight := "eric"
var out_dir := ""
var bar: Control


func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("fight="):
			fight = arg.substr(6)
		elif arg.begins_with("out="):
			out_dir = arg.substr(4)
	_main.call_deferred()


func _process(_delta: float) -> bool:
	return false


func wait(n: int) -> void:
	for i in n:
		await process_frame


# The HUD's feedback runs on real seconds, so a settled shot has to wait real ones.
func settle(seconds: float) -> void:
	var until := Time.get_ticks_msec() + int(seconds * 1000.0)
	while Time.get_ticks_msec() < until:
		await process_frame


func _main() -> void:
	DirAccess.make_dir_recursive_absolute(out_dir)
	change_scene_to_file(FIGHTS[fight])
	while current_scene == null or current_scene.scene_file_path != FIGHTS[fight]:
		await process_frame
	await wait(3)
	var scratch := current_scene.get_node_or_null("ScratchEricDriver")
	if scratch:
		scratch.free()
	await _skip_entrance()
	root.get_node("DialogueManager").dialogue_ended.emit(null)
	# The balloon is a direct child of the fight, the boss HUD is a CanvasLayer under the boss, so
	# dropping the one leaves the other. Without this every shot has a line of dialogue across it.
	for child in current_scene.get_children():
		if child.has_method(&"rearm_input_lock"):
			child.queue_free()
	await wait(2)
	await _skip_vs_card()
	await wait(4)
	bar = _find_bar()
	if bar == null:
		print("no boss health bar in ", fight)
		quit(1)
		return
	_report()
	_fill_daze(55.0)

	# 0.8 s is past CHIP_HOLD + CHIP_DRAIN, so a settled shot shows the empty channel rather than the
	# chip trail still running across it.
	var max_value: float = bar.rows[0].max
	await _shot("full")
	bar.set_value(0, max_value * 0.6)
	await _shot("chip", 2)
	await settle(0.8)
	await _shot("60")
	bar.set_value(0, max_value * 0.45, bar.HIT_NORMAL)
	await _shot("flash_normal", 1)
	await settle(0.8)
	bar.set_value(0, max_value * 0.3, bar.HIT_PUNISH)
	await _shot("flash_punish_spark", 1)
	await settle(0.8)
	bar.set_value(0, max_value * 0.18)
	await settle(0.8)
	await _shot("low")
	bar.set_ghost(0, 0.62, true)
	await _shot("ghost", 2)
	bar.set_heat(0, 1.0)
	_fill_daze(38.0)
	await settle(0.2)
	await _shot("hot_daze_full")
	bar.set_heat(0, 0.0)
	bar.set_ghost(0, 0.62, false)
	bar.refill_row(0, max_value, 0.35)
	await _shot("sweep", 3)
	await settle(0.8)
	if bar.rows.size() > 1:
		bar.set_value(1, bar.rows[1].max * 0.45)
		bar.set_ghost(1, 1.0, true)
		bar.set_ghost(0, 0.45, true)
		await settle(0.8)
		await _shot("pair")
	print("CAPTURE DONE ", fight)
	quit()


# The daze meter shares the bar's look, so every shot has to show them together rather than the bar
# over an empty rail.
func _fill_daze(amount: float) -> void:
	for node in root.find_children("*", "Node", true, false):
		if node.get_script() != null and str(node.get_script().resource_path).ends_with("BossBreakGauge.gd"):
			node.locked = false
			node.add(amount)


func _shot(name: String, frames := 1) -> void:
	await wait(frames)
	await RenderingServer.frame_post_draw
	var img := root.get_texture().get_image()
	img.save_png("%s/boss_bar_%s_%s.png" % [out_dir, fight, name])
	img.get_region(CROP).save_png("%s/boss_bar_%s_%s_crop.png" % [out_dir, fight, name])
	var row: Dictionary = bar.rows[0]
	print("  shot ", name, "  chip=", row.chip.value, " fill=", row.fill.value,
		" flash=", row.flash.visible, " tree_paused=", paused,
		" boss_mode=", bar.get_parent().get_parent().process_mode if bar.get_parent() else -1,
		" can_process=", bar.can_process())


func _report() -> void:
	print("block at ", bar.position, " size ", bar.size, " rows ", bar.rows.size())
	for child in bar.get_children():
		if child is Sprite2D:
			print("  ", child.texture.resource_path.get_file(), " at ", bar.position + child.position)
	for i in bar.rows.size():
		var row: Dictionary = bar.rows[i]
		print("  row ", i, " at ", bar.position + row.node.position, " key=", row.key)
	var gauges := root.find_children("*", "Control", true, false).filter(
		func(c): return c.get_script() != null and str(c.get_script().resource_path).ends_with("BreakGaugeUI.gd"))
	for gauge in gauges:
		print("  daze meter at ", gauge.position, " size ", gauge.size)


func _find_bar() -> Control:
	for node in root.find_children("*", "Control", true, false):
		if node.get_script() != null and str(node.get_script().resource_path).ends_with("BossHealthBarUI.gd"):
			return node
	return null


func _skip_entrance() -> void:
	var intro: Node = null
	for node in current_scene.find_children("*", "Node", true, false):
		if node.has_method(&"finish_entrance"):
			intro = node
			break
	if intro == null:
		return
	for i in 60:
		if intro.entered:
			break
		await process_frame
	if not intro.finished:
		intro.skip()
	await wait(2)


func _skip_vs_card() -> void:
	var card := current_scene.get_node_or_null("Arena/VsCard")
	if card == null:
		return
	if card.is_playing():
		card.skip()
		for i in 60:
			if not card.is_playing():
				break
			await process_frame
	card.grace_until_msec = 0
