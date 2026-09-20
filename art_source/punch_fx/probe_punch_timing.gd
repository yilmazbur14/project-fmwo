extends SceneTree

# Read-only measurement of the player's punch in Eric's fight: for each facing, a landed punch and a
# whiff, one line per physics frame with the state, the sheet cell, the hitbox's flags and global
# rect, the time scale and every report the boss's hurtbox makes. Nothing in the player is changed.
#   Godot.exe --headless --fixed-fps 60 --path . --script res://art_source/punch_fx/probe_punch_timing.gd

const SCENE := "res://Scenes/Bosses/EricBossFightScene.tscn"
const BINDINGS := "user://input_bindings_punch_fx_probe.cfg"
const FACING_NAMES := ["DOWN", "UP", "LEFT", "RIGHT"]
# How far the hitbox's far edge is put inside Eric's hurtbox for a landed punch, in px.
const OVERLAP := 6.0

var player: CharacterBody2D
var boss: Node
var sm: Node
var reports: Array = []
var landed: Array = []


func _initialize() -> void:
	_main.call_deferred()


func wait(n: int) -> void:
	for i in n:
		await physics_frame


func punch() -> void:
	var ev := InputEventAction.new()
	ev.action = &"punch"
	ev.pressed = true
	Input.parse_input_event(ev)
	var up := InputEventAction.new()
	up.action = &"punch"
	up.pressed = false
	Input.parse_input_event(up)


func _main() -> void:
	var settings: Node = root.get_node("InputSettings")
	settings.save_path = BINDINGS
	settings.reset_to_defaults()
	change_scene_to_file(SCENE)
	while current_scene == null or current_scene.scene_file_path != SCENE:
		await process_frame
	await wait(3)
	player = current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
	for child in current_scene.get_children():
		if child is CanvasLayer:
			child.queue_free()
	root.get_node("DialogueManager").dialogue_ended.emit(null)
	await wait(2)
	boss = current_scene.get_node("Arena/EricBossScene/CharacterBody2D")
	sm = boss.state_machine
	sm.post_dialogue_pre_fight_timer.stop()
	sm.chain = []
	sm.on_child_transition(sm.current_state, "Idle")
	sm.set_process(false)
	sm.set_physics_process(false)
	for timer in boss.find_children("*", "Timer", true, false):
		timer.stop()
	player.playerHealth = 100
	boss.boss_health = 1000
	# His hurtbox is only live while he is down (or staggered): hold him down for the whole run, with
	# the daze spent so no charged punch can start a finisher.
	sm.downed_state_timer.start(600.0)
	sm.on_child_transition(sm.current_state, "Downed")
	await wait(5)
	boss.daze_used = true
	var hurtbox: Area2D = boss.get_node("Hurtbox")
	hurtbox.area_entered.connect(func(area: Area2D) -> void:
		reports.append([Engine.get_physics_frames(), area.name, area.monitoring, area.monitorable]))
	player.combo.punch_landed.connect(func(_t, dealt, charged) -> void:
		landed.append([Engine.get_physics_frames(), dealt, charged]))

	var shape: CollisionShape2D = hurtbox.get_node("CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	print("PROBE eric hurtbox global %s" % box)
	print("PROBE player scale %s, sprite frame size %s" % [player.global_scale, Vector2(32, 32)])
	var body_shape: CollisionShape2D = player.get_node("CollisionShape2D")
	print("PROBE player body box (local px) %s" % (body_shape.transform * body_shape.shape.get_rect()))
	for f in 4:
		var r: Rect2 = player.PUNCH_HITBOXES[f]
		print("PROBE hitbox %s texels %s -> px from centre %s" % [FACING_NAMES[f], r, Rect2(r.position * 2.0, r.size * 2.0)])

	for f in [player.Facing.UP, player.Facing.DOWN, player.Facing.LEFT, player.Facing.RIGHT]:
		for hit in [true, false]:
			await run_case(f, hit, box)
	DirAccess.remove_absolute(ProjectSettings.globalize_path(BINDINGS))
	quit(0)


# Where the player stands so `facing` points at Eric with the hitbox's far edge OVERLAP px inside his
# hurtbox, or a whiff's worth (60 px) short of it.
func stand_point(facing: int, hit: bool, box: Rect2) -> Vector2:
	var r: Rect2 = player.PUNCH_HITBOXES[facing]
	var px := Rect2(r.position * 2.0, r.size * 2.0)
	var inset := OVERLAP if hit else -60.0
	match facing:
		player.Facing.UP:
			return Vector2(box.get_center().x - px.get_center().x, box.end.y - inset - px.position.y)
		player.Facing.DOWN:
			return Vector2(box.get_center().x - px.get_center().x, box.position.y + inset - px.end.y)
		player.Facing.LEFT:
			return Vector2(box.end.x - inset - px.position.x, box.get_center().y + 20.0 - px.get_center().y)
		_:
			return Vector2(box.position.x + inset - px.end.x, box.get_center().y + 20.0 - px.get_center().y)


func run_case(facing: int, hit: bool, box: Rect2) -> void:
	var at := stand_point(facing, hit, box)
	player.global_position = at
	player.velocity = Vector2.ZERO
	await wait(12)
	player.global_position = at
	await wait(4)
	print("")
	print("PROBE ==== %s %s at %s, facing %s" % [FACING_NAMES[facing], "HIT" if hit else "WHIFF", player.global_position, FACING_NAMES[player.facing]])
	var hb: Area2D = player.get_node("Hitbox")
	var hb_shape: CollisionShape2D = hb.get_node("CollisionShape2D")
	print("PROBE hitbox global rect %s (overlaps hurtbox: %s)" % [hb_shape.global_transform * hb_shape.shape.get_rect(), (hb_shape.global_transform * hb_shape.shape.get_rect()).intersects(box)])
	reports.clear()
	landed.clear()
	var health_before: int = boss.boss_health
	var start := Engine.get_physics_frames()
	punch()
	var last_line := ""
	for i in 40:
		await physics_frame
		var n := Engine.get_physics_frames() - start
		var state: String = player.state_machine.current_state.name
		var cell: Vector2i = player.sprite.frame_coords
		var line := "state %-8s cell %s hitbox mon %-5s able %-5s ts %.2f health %d" % [state, cell, hb.monitoring, hb.monitorable, Engine.time_scale, boss.boss_health]
		var extra := ""
		for rep in reports:
			if rep[0] == Engine.get_physics_frames():
				extra += "  REPORT(%s mon=%s able=%s)" % [rep[1], rep[2], rep[3]]
		for l in landed:
			if l[0] == Engine.get_physics_frames():
				extra += "  LANDED dealt=%d charged=%s" % [l[1], l[2]]
		if line != last_line or extra != "":
			print("PROBE f+%02d %s%s" % [n, line, extra])
			last_line = line
	print("PROBE result: dealt %d, reports at %s, landed at %s (start %d)" % [health_before - boss.boss_health, reports.map(func(r): return r[0] - start), landed.map(func(l): return l[0] - start), start])
	await wait(30)
