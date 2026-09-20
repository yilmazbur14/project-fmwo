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
const BOSS_GROUP := "fight_boss"

const PLAYER_PATH := "Arena/MainPlayer/CharacterBody2D"
const VICTORY_SCENE := "res://Scenes/Core/VictoryScene.tscn"
const DEFEAT_SCENE := "res://Scenes/Core/DefeatScene.tscn"
# Above the dialogue balloon and every HUD and health bar.
const FADE_LAYER := 128

var player_won := false
var fade: ColorRect


# The first call decides the fight; later ones are ignored.
static func finish_fight(tree: SceneTree, won: bool) -> void:
	if tree.root.has_node(^"FightOutro"):
		return
	var outro = new()
	outro.name = "FightOutro"
	outro.player_won = won
	tree.root.add_child(outro)


func _ready() -> void:
	layer = FADE_LAYER
	fade = ColorRect.new()
	fade.color = Color(0, 0, 0, 0)
	fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(fade)

	# The outro's dialogue balloon is added to the fight scene, which mustn't still be frozen by a finisher.
	FightFreeze.unfreeze(get_tree())
	get_tree().current_scene.get_node(PLAYER_PATH).end_fight()
	var dialogue: DialogueResource
	var line_delay := LINE_DELAY
	for boss in get_tree().get_nodes_in_group(BOSS_GROUP):
		if not player_won:
			boss.on_player_defeated()
		if "OUTRO_DIALOGUE" in boss:
			dialogue = load(boss.OUTRO_DIALOGUE)
		if boss.has_method("outro_line_delay"):
			line_delay = maxf(line_delay, boss.outro_line_delay(player_won))
	_play(dialogue, line_delay)


func _play(dialogue: DialogueResource, line_delay: float) -> void:
	await get_tree().create_timer(line_delay, false, false, true).timeout
	_settle_screen()
	if dialogue:
		var balloon = DialogueManager.show_dialogue_balloon(dialogue, "player_won" if player_won else "player_lost")
		balloon.input_lock_time = LINE_INPUT_LOCK
		await DialogueManager.dialogue_ended

	var tween := create_tween().set_ignore_time_scale()
	tween.tween_property(fade, "color:a", 1.0, FADE_TIME)
	var sounds: Array = _playing_sounds() if FADE_MUSIC else []
	for sound in sounds:
		tween.parallel().tween_property(sound, "volume_db", SILENT_DB, FADE_TIME)
	await tween.finished
	for sound in sounds:
		# The dialogue balloon frees itself once the lines end, along with any blip still sounding in it.
		if is_instance_valid(sound):
			sound.stop()
	_settle_screen()
	get_tree().change_scene_to_file(VICTORY_SCENE if player_won else DEFEAT_SCENE)
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
