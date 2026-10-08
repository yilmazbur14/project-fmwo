extends Node

# Autoload singleton. Set by a boss just before it transitions to the
# shared VictoryScene.tscn, so that scene knows which fight comes next.
# Empty string means "no next boss configured yet" - the Victory screen
# falls back to returning to the Main Menu.
var next_boss_scene: String = ""

# The story's fights in order (the user's ladder of 2026-10-06, by difficulty): the scene each one loads, the name the
# screens show it under, and its face on the Victory screen's ladder - its frame of rank_icons.png, a strip drawn in the
# order of 2026-09-17, so the frame belongs to the boss and not to his place. Reordering the ladder is moving rows here.
# Fights whose scene hasn't been built yet stay in the table - next_fight_after()
# skips them until their scene exists, so the ladder can show the whole order.
const BOSSES: Array[Dictionary] = [
	{"scene": "res://Scenes/Bosses/BurakBossFightScene.tscn", "name": "BURAK", "icon": 0},
	{"scene": "res://Scenes/Bosses/MasonBossFightScene.tscn", "name": "MASON", "icon": 4},
	{"scene": "res://Scenes/Bosses/JoshBossFightScene.tscn", "name": "JOSH", "icon": 5},
	{"scene": "res://Scenes/Bosses/EricBossFightScene.tscn", "name": "ERIC", "icon": 1},
	{"scene": "res://Scenes/Bosses/DannyBossFightScene.tscn", "name": "DANNY", "icon": 6},
	{"scene": "res://Scenes/Bosses/ComputahBossFightScene.tscn", "name": "COMPUTAH", "icon": 2},
	{"scene": "res://Scenes/Bosses/LiamBossFightScene.tscn", "name": "LIAM & BIXBY", "icon": 8},
	{"scene": "res://Scenes/Bosses/CarterBossFightScene.tscn", "name": "CARTER", "icon": 7},
	{"scene": "res://Scenes/Bosses/MattBossFightScene.tscn", "name": "MATT", "icon": 3},
	{"scene": "res://Scenes/Bosses/JordanBossFightScene.tscn", "name": "JORDAN", "icon": 9},
]

# What a win at each place on the ladder promotes the player to, by place and not by boss: the ranks climb from @member
# to @admin whoever holds them. Beating the last fight hands over the invite instead of a rank, so its rank is empty.
const RANKS: Array[String] = ["@member", "@regular", "@active", "@veteran", "@trusted", "@vip", "@helper", "@moderator", "@admin", ""]

# Just the fight scenes, in the same order.
static var FIGHT_SCENES: Array[String] = _collect_fight_scenes()

# A fight's later phase that is a scene of its own, and the fight in the order it belongs to: Jordan's Puppet Master is
# FIGHT 10 still, so the pause screen opens in it and a loss there reads #arena-10.
const PHASE_SCENES := {
	"res://Scenes/Bosses/JordanGodFightScene.tscn": "res://Scenes/Bosses/JordanBossFightScene.tscn",
}

# The result screens report on the fight that led to them, so arriving at one
# must not overwrite fight_index.
const RESULT_SCENES: Array[String] = [
	"res://Scenes/Core/VictoryScene.tscn",
	"res://Scenes/Core/DefeatScene.tscn",
]

const FightOutro := preload("res://Scripts/FightOutro.gd")
# FIGHT 06's second half is fought in the fight's own scene, so only his script on a boss tells it apart. FIGHT 07's is
# the same, with Liam's.
const GREYSON_SCRIPT := "res://Scripts/GreysonScript.gd"
const LIAM_SCRIPT := "res://Scripts/LiamScript.gd"
# Added to every fight scene while playtest_invincible is on.
const INVINCIBLE_BADGE := "res://Scripts/InvincibleBadge.gd"
# The main menu and its CONTROLS screen, the two screens the menu's theme plays across (carry_music).
const MENU_SCENE := "res://Scenes/Core/MainMenuScene.tscn"
const CONTROLS_SETTINGS_SCENE := "res://Scenes/Core/ControlsSettingsScene.tscn"

#THE SAVE
# The story run's progress, kept across launches (the user, 2026-10-07: "lets add progress saving"), and the master
# volume with it. One ConfigFile: [meta] version; [progress] checkpoint, phase, cleared, finished; [settings] volume;
# [unlocks] beaten (2026-10-08, still version 1: a file without it reads as one written before it).
const SAVE_PATH := "user://save.cfg"
const SAVE_VERSION := 1
# Whether the fights beaten stay beaten through NEW GAME and START OVER: a record of what the player has done, apart from
# the run's checkpoint. False makes a new run lock them again.
const UNLOCKS_SURVIVE_NEW_GAME := true
# The master volume with none kept yet - a first run, or a save that can't be read (the user, 2026-10-08: "lets lower
# the default volume, maybe start it at half by default"). A volume the player has set always wins.
const DEFAULT_VOLUME := 0.5
# A fight's second half that is taken over inside the fight's own scene, and that scene: CONTINUE opens it with the
# request the boss select's row of the same name makes (start_at_greyson, start_at_liam).
const PHASE_GREYSON := "greyson"
const PHASE_LIAM := "liam"
const PHASE_FIGHTS := {
	PHASE_GREYSON: "res://Scenes/Bosses/ComputahBossFightScene.tscn",
	PHASE_LIAM: "res://Scenes/Bosses/LiamBossFightScene.tscn",
}
# Jordan's room between his kaiju and his last phase: no fight, but a checkpoint, so a run that has beaten the kaiju
# never has to again.
const FINALE_ROOM_SCENE := "res://Scenes/Core/JordanFinaleScene.tscn"
# The champion ending: reaching it finishes the run.
const ENDING_SCENE := "res://Scenes/Core/ChampionEndingScene.tscn"

# Index into FIGHT_SCENES of the fight the player is in (or just left for a
# result screen); -1 for anything outside the order.
var fight_index := -1
var bosses_cleared := 0
# Fight scenes whose boss entrance has already played this run (BossEntrance.already_seen). It lives
# here because this is an autoload: a retry after a loss reloads the fight scene, and nobody wants to
# watch the same walk-in twice in a row.
var entrances_seen := {}
# A playtest shortcut from MainMenuScript's boss select: FIGHT 06 opens on Greyson's takeover, Computah already
# down, rather than at its start. Cleared by the fight when it takes it (ComputahStateMachine), so a retry and the
# ladder never see it.
var start_at_greyson := false
# The same for the FINALE row: FIGHT 10 opens at Jordan's KO, the win already the player's, so the whole finale plays
# from his walk-out. Cleared by the fight when it takes it (JordanStateMachine).
var start_at_finale := false
# The same for the LIAM row: FIGHT 07 opens on Liam's takeover, Bixby already down, so Liam's own phase plays from the
# cough-up. Cleared by the fight when it takes it (BixbyBeastStateMachine).
var start_at_liam := false
# The editor, which is also the playtest build (the user, 2026-10-08: "just need the editor build (which is also the
# playtest build) and the normal build"): the main menu's full boss select and its INVINCIBLE toggle. Every exported
# build is a normal one, whose boss select lists only the fights the player has beaten and which is never invincible.
# A var, so a headless check (which runs on the editor) can stand in for a normal build.
var playtest_build := OS.has_feature("editor")
# A playtest toggle from MainMenuScript's boss select: the player takes no health damage, so a whole
# fight can be watched end to end. Deliberately NOT cleared by reset_progress() - it is a setting the
# user leaves on while they look at a boss, not run state, so starting a new run must not silently turn
# it off. Never on outside the playtest build, whatever sets it.
var playtest_invincible := false:
	get:
		return playtest_invincible and playtest_build
# Where the fight just lost starts again, for the Defeat screen's RETRY (note_retry()): noted as it is lost, because the
# fight scene is gone by the time that screen is up. "" when there is none - the screen was reached some other way -
# and RETRY isn't offered. Any scene but a result screen forgets it.
var retry_scene := ""
var retry_at_greyson := false
var retry_at_liam := false
# RETRY and RESTART FIGHT go straight back to the fight (the 2026-10-07 playtest: a retry replayed every pre-fight line
# and the VS card): the scene arm_retry() opens, whose first BossEntrance takes it (take_intro_skip) and skips the way a
# held ui_cancel does - the entrance, the lines and the card's build-up, or Greyson's or Liam's takeover. "" when none is
# owed, so a fight entered any other way plays all of it; any other scene coming up drops it.
var intro_skip_scene := ""
# The main menu's theme while its CONTROLS screen is up, playing on under this node (the 2026-10-07 playtest: the screen
# was silent, and Back started the theme over from the top). The menu takes it back when it comes up again.
var carried_music: AudioStreamPlayer
# Whether this run is the one the save follows: NEW GAME and CONTINUE start it, and the boss select's fights are
# practice that must never write over it. reset_progress() turns it off, so a boss select row starts practice.
var saving_run := false
# SAVE_PATH, except in the headless checks, which point this elsewhere (and load_save() again) so that no test run can
# ever read or overwrite the save of the person playtesting from the same checkout.
var save_path := SAVE_PATH
# What the save holds, as last read or written. The checkpoint is the scene CONTINUE opens, "" for none - a first run,
# a finished one, or a file that couldn't be used - and its phase one of PHASE_FIGHTS' keys or "" for the scene's
# start. Cleared is bosses_cleared, put back by CONTINUE so the Victory screen's ladder carries on where it was.
# Finished is the player's for good once the ending has played: a new run doesn't take it back.
var saved_checkpoint := ""
var saved_phase := ""
var saved_cleared := 0
var saved_finished := false
# The fights the player has beaten, for a normal build's boss select (the user, 2026-10-08: "only if theyve beat the
# boss"): each a scene of FIGHT_SCENES, or of PHASE_SCENES for Jordan's last phase, won in the story run (note_win). In
# the save's [unlocks] section, as a record of what the player has done rather than of the run.
var beaten: Array[String] = []


func _ready() -> void:
	# Borderless full screen rather than exclusive, so alt-tab behaves.
	if wants_fullscreen():
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
	load_save()
	get_tree().scene_changed.connect(_on_scene_changed)
	# scene_changed doesn't fire for the scene the game boots into.
	_on_scene_changed.call_deferred()


# An exported build opens full screen (the user, 2026-10-08: "lets have the game start in full screen"); the editor, where
# the playtest runs and every check and capture window is opened, keeps the window the project gives it.
func wants_fullscreen() -> bool:
	return not playtest_build


func reset_progress() -> void:
	fight_index = -1
	bosses_cleared = 0
	entrances_seen.clear()
	start_at_greyson = false
	start_at_finale = false
	start_at_liam = false
	saving_run = false


# Returns how many bosses the Victory screen's ladder should show as beaten.
func record_victory() -> int:
	if fight_index < 0:
		return bosses_cleared
	bosses_cleared = maxi(bosses_cleared, fight_index + 1)
	# The win moves the checkpoint on at once, so a player who stops on the Victory screen keeps it.
	if next_boss_scene != "":
		_save_checkpoint(next_boss_scene, "")
	return fight_index + 1


# The fight that follows `fight_scene`, for the boss that just won to hand to
# the Victory screen. Fights whose scene doesn't exist yet are skipped, so the
# run never dead-ends on one that is still being built; "" means the run ends
# here (the last fight, or a fight that is no longer part of the order).
func next_fight_after(fight_scene: String) -> String:
	var index := FIGHT_SCENES.find(fight_scene)
	if index < 0:
		return ""
	for i in range(index + 1, BOSSES.size()):
		var scene: String = BOSSES[i]["scene"]
		if ResourceLoader.exists(scene):
			return scene
	return ""


# The first fight of the order that is built: where the controls room and the training room send a new
# run. A fight still being built is skipped, as next_fight_after() skips it.
func first_fight() -> String:
	for boss in BOSSES:
		var scene: String = boss["scene"]
		if ResourceLoader.exists(scene):
			return scene
	return ""


# The name the screens and the fight's own health bar show `fight_scene` under.
func boss_name(fight_scene: String) -> String:
	var index := FIGHT_SCENES.find(fight_scene)
	return BOSSES[index]["name"] if index >= 0 else ""


func _on_scene_changed() -> void:
	var scene := get_tree().current_scene
	if scene == null:
		return
	var path := scene.scene_file_path
	if path != intro_skip_scene:
		intro_skip_scene = ""
	# Anywhere but the two screens it plays across, it stops, as it did before it was carried.
	if carried_music != null and path != CONTROLS_SETTINGS_SCENE and path != MENU_SCENE:
		carried_music.queue_free()
		carried_music = null
	if path in RESULT_SCENES:
		return
	fight_index = FIGHT_SCENES.find(PHASE_SCENES.get(path, path)) if path != "" else -1
	retry_scene = ""
	retry_at_greyson = false
	retry_at_liam = false
	if playtest_invincible and is_fight_scene(path):
		scene.add_child(load(INVINCIBLE_BADGE).new())
	if path == ENDING_SCENE:
		_save_finished()
	# Not the checkpoint's own scene again: a retry, a restart or CONTINUE itself reloads it, and in Greyson's or Liam's
	# half that would put the checkpoint back to the fight's start.
	elif is_checkpoint_scene(path) and path != saved_checkpoint:
		_save_checkpoint(path, "")


# A scene the run is saved on entering: every fight in the order, a later phase of one (PHASE_SCENES) and Jordan's room.
func is_checkpoint_scene(path: String) -> bool:
	return is_fight_scene(path) or path == FINALE_ROOM_SCENE


# NEW GAME: a fresh run, saved from its first fight on. What the save had goes at once - the menu has asked first - all
# but saved_finished.
func start_new_run() -> void:
	reset_progress()
	saving_run = true
	if not UNLOCKS_SURVIVE_NEW_GAME:
		beaten.clear()
	_save_checkpoint("", "")


# A fight won (FightOutro), in the story run: beaten for good. A practice win from the boss select doesn't count - in a
# normal build it can only be a fight already beaten.
func note_win(tree: SceneTree) -> void:
	var path := tree.current_scene.scene_file_path
	if not saving_run or not is_fight_scene(path) or beaten.has(path):
		return
	beaten.append(path)
	_write_save()


func has_beaten(fight_scene: String) -> bool:
	return beaten.has(fight_scene)


# Whether CONTINUE has a run to pick up.
func has_resume() -> bool:
	return saved_checkpoint != ""


# CONTINUE: the saved run picked up at its checkpoint, the way the boss select's rows open each half, with the fights
# it had cleared. Returns the scene to open; the fight's intro plays as it would on arriving there.
func continue_run() -> String:
	reset_progress()
	saving_run = true
	bosses_cleared = saved_cleared
	start_at_greyson = saved_phase == PHASE_GREYSON
	start_at_liam = saved_phase == PHASE_LIAM
	return saved_checkpoint


# What CONTINUE says it resumes at.
func resume_label() -> String:
	match saved_phase:
		PHASE_GREYSON:
			return "VS GREYSON"
		PHASE_LIAM:
			return "VS LIAM"
	if saved_checkpoint == FINALE_ROOM_SCENE:
		return "THE FINALE"
	if PHASE_SCENES.has(saved_checkpoint):
		return "VS GOD JORDAN"
	return "VS %s" % boss_name(saved_checkpoint)


# Greyson's or Liam's takeover has begun (ComputahScript, BixbyBeastScript): the run's checkpoint is that half now.
func reach_phase(phase: String) -> void:
	_save_checkpoint(PHASE_FIGHTS[phase], phase)


# The slider's 0 to 1 on the Master bus, 0 muted, written to the save at once. The main menu's and the pause screen's
# sliders both set it here.
func set_volume(value: float) -> void:
	_apply_volume(value)
	_write_save()


func volume() -> float:
	var bus := AudioServer.get_bus_index("Master")
	return 0.0 if AudioServer.is_bus_mute(bus) else db_to_linear(AudioServer.get_bus_volume_db(bus))


# Reads the save into saved_* and puts its volume on the Master bus, DEFAULT_VOLUME when it keeps none. Missing is a
# first run. A file that won't parse, or was written by a version this doesn't know, is no save at all, and is written
# over by the next checkpoint; a checkpoint this build can't open - a scene renamed since, a phase it doesn't know - is
# no run to continue.
func load_save() -> void:
	saved_checkpoint = ""
	saved_phase = ""
	saved_cleared = 0
	saved_finished = false
	beaten.clear()
	# A check that never reads a save leaves the bus as it found it.
	if not _save_reachable():
		return
	_apply_volume(DEFAULT_VOLUME)
	if not FileAccess.file_exists(save_path):
		return
	var cfg := ConfigFile.new()
	var version = cfg.get_value("meta", "version", -1) if cfg.load(save_path) == OK else -1
	# Typed first: comparing a hand-edited "1" with an int is a script error, not a mismatch.
	if typeof(version) != TYPE_INT or version != SAVE_VERSION:
		push_warning("GameProgress: %s could not be read; treated as no save." % save_path)
		return
	var finished = cfg.get_value("progress", "finished", false)
	saved_finished = finished if typeof(finished) == TYPE_BOOL else false
	var checkpoint = cfg.get_value("progress", "checkpoint", "")
	var phase = cfg.get_value("progress", "phase", "")
	var cleared = cfg.get_value("progress", "cleared", 0)
	if typeof(checkpoint) == TYPE_STRING and typeof(phase) == TYPE_STRING and typeof(cleared) == TYPE_INT and _resumable(checkpoint, phase):
		saved_checkpoint = checkpoint
		saved_phase = phase
		saved_cleared = clampi(cleared, 0, BOSSES.size())
	var won = cfg.get_value("unlocks", "beaten", [])
	# A save from before the unlocks were kept: its run had beaten the fights it cleared, in the ladder's order, and a
	# finished one all of them.
	if not cfg.has_section_key("unlocks", "beaten"):
		won = FIGHT_SCENES.slice(0, BOSSES.size() if saved_finished else saved_cleared)
		if saved_finished:
			won.append_array(PHASE_SCENES.keys())
	if typeof(won) == TYPE_ARRAY:
		for scene in won:
			if typeof(scene) == TYPE_STRING and is_fight_scene(scene) and not beaten.has(scene):
				beaten.append(scene)
	var stored_volume = cfg.get_value("settings", "volume", -1.0)
	if (typeof(stored_volume) == TYPE_FLOAT or typeof(stored_volume) == TYPE_INT) and stored_volume >= 0.0 and stored_volume <= 1.0:
		_apply_volume(stored_volume)


func _apply_volume(value: float) -> void:
	var bus := AudioServer.get_bus_index("Master")
	AudioServer.set_bus_mute(bus, value <= 0.001)
	if value > 0.001:
		AudioServer.set_bus_volume_db(bus, linear_to_db(value))


func _resumable(checkpoint: String, phase: String) -> bool:
	if checkpoint == "" or not ResourceLoader.exists(checkpoint):
		return false
	if phase == "":
		return is_checkpoint_scene(checkpoint)
	return PHASE_FIGHTS.get(phase, "") == checkpoint


func _save_checkpoint(checkpoint: String, phase: String) -> void:
	if not saving_run:
		return
	saved_checkpoint = checkpoint
	saved_phase = phase
	saved_cleared = bosses_cleared
	_write_save()


func _save_finished() -> void:
	if not saving_run:
		return
	saved_finished = true
	_save_checkpoint("", "")


# Synchronous, on every change, as InputSettings writes the controls: a crash must never cost the player a fight won.
func _write_save() -> void:
	if not _save_reachable():
		return
	var cfg := ConfigFile.new()
	cfg.set_value("meta", "version", SAVE_VERSION)
	cfg.set_value("progress", "checkpoint", saved_checkpoint)
	cfg.set_value("progress", "phase", saved_phase)
	cfg.set_value("progress", "cleared", saved_cleared)
	cfg.set_value("progress", "finished", saved_finished)
	cfg.set_value("settings", "volume", volume())
	cfg.set_value("unlocks", "beaten", beaten)
	var error := cfg.save(save_path)
	if error != OK:
		push_warning("GameProgress: %s could not be written (%s)." % [save_path, error_string(error)])


# The headless checks and captures (art_source) each run as a --script SceneTree of their own, and plenty of them press
# NEW GAME, play the ladder through or move a volume slider without knowing this file exists: under one, the player's
# own save is never read or written. A check that wants a save points save_path at a scratch file of its own.
func _save_reachable() -> bool:
	return save_path != SAVE_PATH or get_tree().get_script() == null


# Notes where starting the fight being played in `tree` over begins. The pause screen's RESTART FIGHT and the Defeat
# screen's RETRY both start it there, through arm_retry(), so the two can't drift apart: the same scene - Jordan's
# Puppet Master, a scene of its own, included - and in Greyson's half of FIGHT 06 that half again, the way the menu's
# GREYSON row opens it (reloading the scene alone played Computah's intro and his fight, already won, over again: the
# 2026-10-04 playtest). Liam's half of FIGHT 07 the same way, as the LIAM row opens it (it went back to Bixby's: the
# 2026-10-07 playtest).
func note_retry(tree: SceneTree) -> void:
	var path := tree.current_scene.scene_file_path
	retry_scene = path if is_fight_scene(path) else ""
	retry_at_greyson = false
	retry_at_liam = false
	for boss in tree.get_nodes_in_group(FightOutro.BOSS_GROUP):
		var script: Script = boss.get_script()
		if script != null and script.resource_path == GREYSON_SCRIPT:
			retry_at_greyson = true
		if script != null and script.resource_path == LIAM_SCRIPT:
			retry_at_liam = true


# Asks the fight note_retry() noted to open where it was noted, with its intro skipped, and returns its scene: "" for
# none. Jordan's Puppet Master has no intro to skip - his own opening lets go of the player in a second - so his isn't
# asked for: left owed, it would skip the first entrance his fight ever began.
func arm_retry() -> String:
	start_at_greyson = retry_at_greyson
	start_at_liam = retry_at_liam
	intro_skip_scene = "" if PHASE_SCENES.has(retry_scene) else retry_scene
	return retry_scene


# Whether the BossEntrance beginning in `tree` is the first of the scene arm_retry() opened, and so skips straight to
# the fight. Taken once.
func take_intro_skip(tree: SceneTree) -> bool:
	if intro_skip_scene == "" or tree.current_scene == null or tree.current_scene.scene_file_path != intro_skip_scene:
		return false
	intro_skip_scene = ""
	return true


# The menu's theme handed over before the menu goes to its CONTROLS screen, still playing.
func carry_music(player: AudioStreamPlayer) -> void:
	player.reparent(self)
	carried_music = player


# The theme carry_music() took, for the menu to play on, or null.
func take_carried_music() -> AudioStreamPlayer:
	var player := carried_music
	carried_music = null
	return player


# A scene the fight's pause screen answers in: a fight in the order, or a later phase of one (PHASE_SCENES).
func is_fight_scene(path: String) -> bool:
	return FIGHT_SCENES.has(path) or PHASE_SCENES.has(path)


static func _collect_fight_scenes() -> Array[String]:
	var scenes: Array[String] = []
	for boss in BOSSES:
		scenes.append(boss["scene"])
	return scenes
