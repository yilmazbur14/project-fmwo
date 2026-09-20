extends SceneTree

# The training room's dodge geometry, measured rather than assumed. The room's own comments
# (Scripts/TrainingDummyArtLayout.gd) say the in-front standoff is set by SORT_POINT and not by the
# barrel's width, and that LUNGE_BOX.h is the lever for the front reach alone. Both of those are
# claims about px, and both move if the player's size moves, so this walks the player into the dummy
# until collision stops him, then dashes him out of every attack and counts what the swing reached.
#   Godot.exe --headless --fixed-fps 60 --path . \
#     --script res://art_source/player_size/probe_dummy_dodge.gd -- cycles=2
#
# Per attack it records three things, which are not the same question:
#   reach   the strike's hitbox covered the spot the dash left (the near miss the dummy reports).
#           This is the geometry, and the only one of the three LUNGE_BOX moves.
#   dodge   PlayerDefense paid a perfect dodge for it. Fewer, by design: perfect_dodge_cooldown and
#           perfect_dodge_source_lockout hold a second payout off for 1.5 s and 3 s.
#   hit     the player was standing in it, so nothing was dodged at all.

const CONTROLS_SCENE := "res://Scenes/Core/ControlsScene.tscn"
const Layout := preload("res://Scripts/TrainingDummyArtLayout.gd")

var cycles := 2
# Only for the measurement: a draw scale forced on the player, with the dodge ghost (which hangs off
# MainPlayer, not off the body, so it does not ride the body's scale) resized to match. It answers
# what a resize would do to this room without anything in the project moving.
var forced_scale := 0.0
var room: Node2D
var player: CharacterBody2D
var defense: Node
var dummy: CharacterBody2D

# TrainingDummyScript.Phase, read off the live node: preloading that script here pulls FightOutro in
# before the autoloads exist, which fails the first compile.
var phase := {}

var reached := false
var paid := false
var was_hit := false
var rows: Array = []


func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("cycles="):
			cycles = int(arg.substr(7))
		elif arg.begins_with("scale="):
			forced_scale = float(arg.substr(6))
	_main.call_deferred()


func _process(_delta: float) -> bool:
	return false


func wait(n: int) -> void:
	for i in n:
		await physics_frame


func send(events: Array) -> void:
	for ev in events:
		Input.parse_input_event(ev)
	Input.flush_buffered_events()


func key(code: int, pressed: bool) -> InputEventKey:
	var ev := InputEventKey.new()
	ev.physical_keycode = code
	ev.keycode = code
	ev.pressed = pressed
	return ev


func _main() -> void:
	change_scene_to_file(CONTROLS_SCENE)
	while current_scene == null or current_scene.scene_file_path != CONTROLS_SCENE:
		await process_frame
	await wait(3)
	room = current_scene.get_node("Room")
	player = current_scene.get_node("Room/MainPlayer/CharacterBody2D")
	defense = player.get_node("Defense")
	dummy = current_scene.get_node("Room/TrainingDummy")
	phase = dummy.get_script().get_script_constant_map()["Phase"]
	if forced_scale > 0.0:
		var was: float = player.scale.x
		player.scale = Vector2(forced_scale, forced_scale)
		var ghost: CollisionShape2D = player.dodge_ghost.get_node("CollisionShape2D")
		(ghost.shape as RectangleShape2D).size *= forced_scale / was
	root.get_node("DialogueManager").dialogue_ended.emit(null)
	for child in current_scene.get_children():
		if child.has_method(&"rearm_input_lock"):
			child.free()
	await wait(4)

	defense.perfect_dodged.connect(func(_hit: RefCounted) -> void: paid = true)

	print("== dummy dodge probe ==")
	print("player body %s hurtbox %s scale %s" % [_box(player.get_node("CollisionShape2D")),
		_box(player.get_node("Hurtbox/CollisionShape2D")), player.scale])
	print("dummy body %s scale %s  LUNGE_BOX %s SWING_BOX %s" % [_box(dummy.get_node("CollisionShape2D")),
		dummy.scale, Layout.LUNGE_BOX, Layout.SWING_BOX])

	# In front there is only 84 px of floor between the dummy and the wall, so the dash out of the
	# lunge is the sideways one a player would actually take. Beside, it is straight away.
	await _run("in front", Vector2.DOWN, KEY_LEFT)
	await _run("beside", Vector2.RIGHT, KEY_RIGHT)

	print("-- results (reach = the strike covered the spot the dash left) --")
	for row in rows:
		print("  %-9s %-12s standoff %6.1f px   reach %d/%d   dodge %d/%d   hit %d/%d" % [
			row.where, row.attack, row.standoff,
			row.reach, row.thrown, row.paid, row.thrown, row.hit, row.thrown])
	quit(0)


func _box(shape: CollisionShape2D) -> String:
	var rect: Rect2 = shape.global_transform * shape.shape.get_rect()
	return "(%.0fx%.0f)" % [rect.size.x, rect.size.y]


# Walks the player into the dummy from `from_dir` until collision stops him, and reports how far off
# his centre ended up. That is the standoff the room's comments are about. The start is clamped into
# the play band, which is only 84 px deep below the dummy: outside it he would start inside a wall.
func _standoff(from_dir: Vector2) -> float:
	player.global_position = _in_band(dummy.global_position + from_dir * 400.0)
	player.velocity = Vector2.ZERO
	await wait(2)
	for i in 160:
		player.velocity = -from_dir * 600.0
		player.move_and_slide()
		await physics_frame
	player.velocity = Vector2.ZERO
	return player.global_position.distance_to(dummy.global_position)


func _in_band(at: Vector2) -> Vector2:
	var shape: CollisionShape2D = player.get_node("CollisionShape2D")
	var body: Rect2 = shape.global_transform * shape.shape.get_rect()
	var half := body.size * 0.5
	var band: Rect2 = room.PLAY_BAND.grow_individual(-half.x, -half.y, -half.x, -half.y)
	return at.clamp(band.position, band.end)


func _run(where: String, from_dir: Vector2, dash_key: int) -> void:
	dummy.set_sparring(false)
	await wait(4)
	var standoff := await _standoff(from_dir)
	dummy.set_sparring(true)
	var counts := {}
	for i in cycles * 3:
		var attack := await _one_attack(from_dir, standoff, dash_key)
		if attack == "":
			break
		if not counts.has(attack):
			counts[attack] = {where = where, attack = attack, standoff = standoff,
				thrown = 0, reach = 0, paid = 0, hit = 0}
		var row: Dictionary = counts[attack]
		row.thrown += 1
		row.reach += 1 if reached else 0
		row.paid += 1 if paid else 0
		row.hit += 1 if was_hit else 0
	for attack in counts:
		rows.append(counts[attack])
	dummy.set_sparring(false)
	await wait(4)


# One wind-up: park the player back on the standoff, dash him straight out of it three frames before
# the strike, and report what happened to that strike.
func _one_attack(from_dir: Vector2, standoff: float, dash_key: int) -> String:
	player.global_position = dummy.global_position + from_dir * standoff
	player.velocity = Vector2.ZERO
	player.playerHealth = 6
	reached = false
	paid = false
	was_hit = false
	var before: int = player.playerHealth
	if not await _wait_phase(phase.WINDUP, 600):
		return ""
	var attack := String(dummy.attack_id)
	for i in 600:
		if dummy.phase != phase.WINDUP:
			break
		if dummy.phase_length - dummy.phase_time <= 3.0 / 60.0:
			break
		await physics_frame
	var arrow := dash_key
	send([key(arrow, true)])
	await physics_frame
	send([key(KEY_W, true)])
	await physics_frame
	send([key(KEY_W, false), key(arrow, false)])
	for i in 120:
		if dummy.phase == phase.STRIKE and _ghost_in_swing():
			reached = true
		if dummy.phase != phase.WINDUP and dummy.phase != phase.STRIKE:
			break
		await physics_frame
	was_hit = player.playerHealth < before
	return attack


# The strike's own box against the hurtbox copy the dash left behind, which is what the dummy's
# near-miss branch tests and what LUNGE_BOX.h moves.
func _ghost_in_swing() -> bool:
	if not defense.ghost_active:
		return false
	var ghost: CollisionShape2D = player.dodge_ghost.get_node("CollisionShape2D")
	var swing: CollisionShape2D = dummy.get_node("SwingHitbox/CollisionShape2D")
	var ghost_rect: Rect2 = ghost.global_transform * ghost.shape.get_rect()
	var swing_rect: Rect2 = swing.global_transform * swing.shape.get_rect()
	return ghost_rect.intersects(swing_rect)


func _wait_phase(phase: int, frames: int) -> bool:
	for i in frames:
		if dummy.phase == phase:
			return true
		await physics_frame
	return false
