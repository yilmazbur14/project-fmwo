extends CanvasLayer

# How every boss fight ends, won or lost: the fight freezes, the boss says their outro lines, and
# the screen fades to black into the Victory or Defeat screen. It lives under the root rather than
# in the fight scene, so its black screen still covers the frames between the fight scene going
# away and the next screen being drawn.

const HitStop := preload("res://Scripts/HitStop.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const FightFreeze := preload("res://Scripts/FightFreeze.gd")

# Seconds between the fight being decided and the boss's first line, unless the boss asks for longer
# (outro_line_delay, below).
const LINE_DELAY := 0.7
# Seconds each line stays up before any dialogue input counts, skipping its typing included, so a
# player still mashing as the fight ends sees every line: on a pad, attack is also the dialogue's
# accept. A line whose typing is skipped stays up this long again from the skip (balloon.gd), so a
# mash can't reveal it and move straight on. The same for every input, keyboard included: nobody
# reads a line faster than this anyway.
const LINE_INPUT_LOCK := 1.2
# A loss's lines instead are on the way back to the fight (the 2026-10-07 playtest: each death cost 6 to 9 s before the
# player was back in control, mostly locked lines), so each holds its input this much shorter: past it a fresh press
# finishes a line still typing or moves on one line, as in every balloon, and the last one's press starts the fade to
# Defeat. Every line is still seen.
const LOSS_LINE_INPUT_LOCK := 0.3
# Seconds the fade to black takes after the last line.
const FADE_TIME := 1.75
# Whether every sound still playing in the fight (the boss music after a loss, the victory fanfare's
# tail after a win) fades out with the screen, rather than cutting off at the scene change.
const FADE_MUSIC := true
# Fading in decibels sounds even all the way down; by this level the sound can't be heard.
const SILENT_DB := -60.0

# Every node in this group has on_player_defeated(), which stops its part of the fight when the
# player loses. The node whose lines the outro plays also has OUTRO_DIALOGUE: the path of a
# dialogue file with player_won and player_lost titles.
# A boss with a pose to finish before its line - Carter turning his back, burning his mark and
# looking round at the player - also has outro_line_delay(player_won: bool) -> float, the seconds
# from the fight being decided to its first line. It is asked after on_player_defeated(), since that
# is what starts the pose. It can only lengthen the wait: a boss without it, or one asking for less,
# gets LINE_DELAY exactly as before.
# On a loss that wait is on the way back to the fight as well (the user, 2026-10-07: "make carters pose
# skippable"): past LOSS_LINE_INPUT_LOCK from the fight being decided, a fresh press of a dialogue key
# ends it and the first line comes up. A boss whose wait is a pose of its own also has
# skip_outro_pose(), called on that press, which puts the pose at its end at once. The line then has
# its own lock from the moment it is up, so the press that ended the wait can't move it on too.
# A boss whose win plays out a sequence of its own rather than lines and the Victory screen - Jordan
# storming out of the arena into his finale - has take_won_outro(outro, line_delay), and is handed
# this outro on a win instead of the lines. It ends it with leave_to(), this outro's own fade and
# scene change to wherever it goes. Everything else here still holds for it: the first call decided
# the fight, the pause screen stays shut, and the player has been stopped.
const BOSS_GROUP := "fight_boss"

const PLAYER_PATH := "Arena/MainPlayer/CharacterBody2D"
const VICTORY_SCENE := "res://Scenes/Core/VictoryScene.tscn"
const DEFEAT_SCENE := "res://Scenes/Core/DefeatScene.tscn"
# Above the dialogue balloon and every HUD and health bar.
const FADE_LAYER := 128

signal line_delay_over

var player_won := false
# Real time, as the balloon's locks are, so a hit-stop can't stretch the lock on the wait.
var decided_msec := 0
# A loss's wait before its first line is running and can be pressed through.
var line_delay_skippable := false
# The fight scene this outro decided.
var fight_scene: Node
var fade: ColorRect
# The fade to the next screen has started, and where it goes (leave_to).
var leaving := false
var destination := ""


# The first call decides the fight; later ones are ignored. Only for the fight it decided: an outro left over from a
# scene changed under it would otherwise keep every later fight from ever ending - the player at 0 health and the
# boss still attacking (the 2026-10-04 playtest; no path in the game is known to leave one, the outro frees itself).
static func finish_fight(tree: SceneTree, won: bool) -> void:
	var existing := tree.root.get_node_or_null(^"FightOutro")
	if existing != null:
		if existing.fight_scene == tree.current_scene:
			return
		existing.name = "FightOutroLeftOver"
		existing.queue_free()
	var outro = new()
	outro.name = "FightOutro"
	outro.player_won = won
	outro.fight_scene = tree.current_scene
	tree.root.add_child(outro)


func _ready() -> void:
	decided_msec = Time.get_ticks_msec()
	layer = FADE_LAYER
	fade = ColorRect.new()
	fade.color = Color(0, 0, 0, 0)
	fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(fade)

	# The outro's dialogue balloon is added to the fight scene, which mustn't still be frozen by a finisher.
	FightFreeze.unfreeze(get_tree())
	get_tree().current_scene.get_node(PLAYER_PATH).end_fight()
	# Before on_player_defeated(), while the bosses still say which half of the fight this was.
	if not player_won:
		GameProgress.note_retry(get_tree())
	else:
		GameProgress.note_win(get_tree())
	var dialogue: DialogueResource
	var line_delay := LINE_DELAY
	var taker: Node
	for boss in get_tree().get_nodes_in_group(BOSS_GROUP):
		if not player_won:
			boss.on_player_defeated()
		if "OUTRO_DIALOGUE" in boss:
			dialogue = load(boss.OUTRO_DIALOGUE)
		if boss.has_method("outro_line_delay"):
			line_delay = maxf(line_delay, boss.outro_line_delay(player_won))
		if player_won and boss.has_method("take_won_outro"):
			taker = boss
	if taker != null:
		taker.take_won_outro(self, line_delay)
		return
	_play(dialogue, line_delay)


func _play(dialogue: DialogueResource, line_delay: float) -> void:
	var delay := get_tree().create_timer(line_delay, false, false, true)
	if player_won:
		await delay.timeout
	else:
		delay.timeout.connect(_end_line_delay)
		line_delay_skippable = true
		await line_delay_over
	_settle_screen()
	if dialogue:
		var balloon = DialogueManager.show_dialogue_balloon(dialogue, "player_won" if player_won else "player_lost")
		balloon.input_lock_time = LINE_INPUT_LOCK if player_won else LOSS_LINE_INPUT_LOCK
		await DialogueManager.dialogue_ended
	leave_to(VICTORY_SCENE if player_won else DEFEAT_SCENE)


# _input rather than _unhandled_input, as the pause screen's: nothing the fight leaves up may take the press first. Only a
# fresh press: a key held from the fight, or its repeats, ends nothing.
func _input(event: InputEvent) -> void:
	if not line_delay_skippable or Time.get_ticks_msec() - decided_msec < LOSS_LINE_INPUT_LOCK * 1000.0:
		return
	var clicked: bool = event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed
	if not (clicked or event.is_action_pressed(&"ui_accept") or event.is_action_pressed(&"ui_cancel")):
		return
	# Before it is marked handled: the device tracker is an autoload, and _input reaches autoloads last.
	InputSettings.note_device(event)
	get_viewport().set_input_as_handled()
	for boss in get_tree().get_nodes_in_group(BOSS_GROUP):
		if boss.has_method("skip_outro_pose"):
			boss.skip_outro_pose()
	_end_line_delay()


func _end_line_delay() -> void:
	if not line_delay_skippable:
		return
	line_delay_skippable = false
	line_delay_over.emit()


# The fade to black, every sound fading with it, and the change to `scene_path`. Once: a second call
# while it fades only changes where it goes, so a skip made mid-fade still lands where the skip goes.
func leave_to(scene_path: String, fade_time := FADE_TIME) -> void:
	destination = scene_path
	if leaving:
		return
	leaving = true
	var tween := create_tween().set_ignore_time_scale()
	tween.tween_property(fade, "color:a", 1.0, fade_time)
	var sounds: Array = _playing_sounds() if FADE_MUSIC else []
	for sound in sounds:
		tween.parallel().tween_property(sound, "volume_db", SILENT_DB, fade_time)
	await tween.finished
	for sound in sounds:
		# The dialogue balloon frees itself once the lines end, along with any blip still sounding in it.
		if is_instance_valid(sound):
			sound.stop()
	_settle_screen()
	get_tree().change_scene_to_file(destination)
	await get_tree().scene_changed
	# The next screen's first frame is drawn in the same frame it's added, before its own fade-in
	# has had a frame to run, so that one stays black too.
	await get_tree().process_frame
	queue_free()


func _playing_sounds() -> Array:
	return get_tree().current_scene.find_children("*", "AudioStreamPlayer", true, false).filter(func(sound): return sound.playing)


# A hit-stop or screen shake from the last blows must neither slow the lines and the fade nor carry
# over into the next screen.
func _settle_screen() -> void:
	HitStop.clear()
	ScreenView.reset(get_tree())
