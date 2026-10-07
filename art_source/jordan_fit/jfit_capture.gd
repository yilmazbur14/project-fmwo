extends SceneTree

# The in-game mock for Jordan's fitted tee: his fight at 1920x1080, the same moment shot twice - once on
# the live jordan_idle.png, once with the fitted idle strip (jfit_previews.py's jordan_fit_idle_strip.png)
# swapped onto his Sprite2D at runtime. Nothing in the project is written or imported: the fitted strip
# is read from disk into an ImageTexture, and the two PNGs go to the folder given.
#
#   "C:/Users/theyi/Downloads/Godot_v4.6.3-stable_win64.exe/Godot.exe.exe" --path <project>
#       --resolution 1920x1080 --position 100,100 --audio-driver Dummy --fixed-fps 60
#       --script <this file> -- <out dir> <fitted idle strip png>
#
# Built on the 2026-09-24 v2 capture (scratchpad jordan_fight/shoot_jordan_v2.gd): the fight is
# loaded, its dialogue and VS card skipped, the fight started; then his frame clock and state machine
# are held so both shots are idle frame 0 with the player in the same place.

const FIGHT := "res://Scenes/Bosses/JordanBossFightScene.tscn"

var out_dir := "."
var strip_path := ""
var player: CharacterBody2D
var boss: Node
var sm: Node


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() > 0:
		out_dir = args[0]
	if args.size() > 1:
		strip_path = args[1]
	_main.call_deferred()


func wait(n: int) -> void:
	for i in n:
		await physics_frame


func shoot(name: String) -> void:
	var path := "%s/%s.png" % [out_dir, name]
	await RenderingServer.frame_post_draw
	var err := root.get_texture().get_image().save_png(path)
	print("saved ", path, " err ", err, "  sheet ", boss.sprite.texture.resource_path.get_file(), " frame ", boss.sprite.frame,
		" hframes ", boss.sprite.hframes, " anim ", boss.current_anim)


func _main() -> void:
	change_scene_to_file(FIGHT)
	while current_scene == null or current_scene.scene_file_path != FIGHT:
		await process_frame
	await wait(3)
	player = current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
	boss = current_scene.get_node("Arena/JordanScene/JordanCharacterBody")
	sm = boss.state_machine
	for child in current_scene.get_children():
		if child is CanvasLayer:
			child.queue_free()
	root.get_node("DialogueManager").dialogue_ended.emit(null)
	await wait(1)
	var card: Node = current_scene.get_node_or_null("Arena/VsCard")
	if card and card.is_playing():
		card.skip()
		for i in 60:
			if not card.is_playing():
				break
			await physics_frame
	if card:
		card.grace_until_msec = 0
	await wait(2)
	sm.post_dialogue_pre_fight_timer.stop()
	sm._on_post_dialogue_pre_fight_timer_timeout()
	player.playerHealth = 9999
	player.is_talking = false
	await wait(2)
	player.global_position = Vector2(730, 690)
	await wait(40)
	# hold him on idle frame 0: no frame clock, no state changes
	sm.set_process(false)
	sm.set_physics_process(false)
	boss.set_process(false)
	boss.sprite.frame = 0
	await wait(3)
	await shoot("jordan_fit_ingame_before_1920x1080")
	var img := Image.load_from_file(strip_path)
	var tex := ImageTexture.create_from_image(img)
	boss.sprite.texture = tex
	boss.sprite.hframes = roundi(img.get_width() / 96.0)
	boss.sprite.frame = 0
	await wait(3)
	await shoot("jordan_fit_ingame_1920x1080")
	quit()
