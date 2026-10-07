extends RefCounted

# entrance_hud: his bar comes up with the gates (EricIntro, the playtest of 2026-10-04). It was up from the
# first frame of his entrance and drew over him for the first steps of his walk in from the top gate;
# Captain Burak's and Matt's have always waited for the gates. --fixed-fps 60, a fresh run:
#   watched   the bar is down from the entrance's first frame while the ring is open and the two of them
#             walk in, the whole of his walk included, and up once the gates have slammed, before his first line
#   skipped   cut with skip() mid-walk, the bar is up at once
#   retry     on a second entry, where the walk-in is skipped, the bar is up from the start

const FIGHT := "res://Scenes/Bosses/EricBossFightScene.tscn"
const BODY := "Arena/EricBossScene/CharacterBody2D"


static func run(t) -> void:
	t.log_p("-- watched")
	await t.enter_fight(FIGHT, true)
	var body: Node = t.current_scene.get_node(BODY)
	var intro: Node = t.entrance_state()
	t.check(await t.wait_until(func(): return intro.entered, 60), "his entrance starts")
	await t.wait(1)
	var gates: Node = t.current_scene.get_node("Arena/Gates")
	t.check(gates.is_open() and not body.hud_layer.visible, "the ring is open and his bar is down")
	var shown_while_open := [0]
	var walk_frames := [0]
	var home: Vector2 = intro.home
	var watch := func() -> void:
		if gates.is_open() and body.hud_layer.visible:
			shown_while_open[0] += 1
		if body.global_position.y < home.y - 1.0:
			walk_frames[0] += 1
	t.physics_frame.connect(watch)
	t.check(await t.wait_until(func(): return not gates.is_open(), 900), "the gates slam shut behind them")
	t.check(await t.wait_until(func(): return body.hud_layer.visible, 60), "and his bar comes up with them")
	t.check(await t.wait_until(func(): return t.live_balloon() != null, 300), "before his first line")
	t.physics_frame.disconnect(watch)
	t.log_p("%d frames of his walk watched, %d with the bar up and the ring open" % [walk_frames[0], shown_while_open[0]])
	t.check(walk_frames[0] > 30 and shown_while_open[0] == 0, "never up while the ring stood open, his whole walk included")

	t.log_p("-- skipped mid-walk")
	t.root.get_node("GameProgress").reset_progress()
	await t.enter_fight(FIGHT, true)
	body = t.current_scene.get_node(BODY)
	intro = t.entrance_state()
	await t.wait_until(func(): return intro.entered, 60)
	home = intro.home
	await t.wait_until(func(): return body.global_position.y < home.y - 1.0 and body.global_position.y > home.y - 200.0, 600)
	t.check(not body.hud_layer.visible, "mid-walk, the bar is down")
	intro.skip()
	await t.wait(1)
	t.check(body.hud_layer.visible, "cut with skip(), it is up at once")

	t.log_p("-- the retry")
	t.change_scene_to_file(FIGHT)
	while t.current_scene == null or t.current_scene.scene_file_path != FIGHT or t.current_scene.get_node_or_null(BODY) == body:
		await t.process_frame
	await t.wait(4)
	body = t.current_scene.get_node(BODY)
	intro = t.entrance_state()
	await t.wait_until(func(): return intro.entered, 60)
	await t.wait(1)
	t.check(intro.finished and body.hud_layer.visible, "a second entry skips the walk-in, and the bar is up from the start")
