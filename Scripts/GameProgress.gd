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
# FIGHT 06's second half is fought in the fight's own scene, so only his script on a boss tells it apart.
const GREYSON_SCRIPT := "res://Scripts/GreysonScript.gd"

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
# A playtest toggle from MainMenuScript's boss select: the player takes no health damage, so a whole
# fight can be watched end to end. Deliberately NOT cleared by reset_progress() - it is a setting the
# user leaves on while they look at a boss, not run state, so starting a new run must not silently turn
# it off.
var playtest_invincible := false
# Where the fight just lost starts again, for the Defeat screen's RETRY (note_retry()): noted as it is lost, because the
# fight scene is gone by the time that screen is up. "" when there is none - the screen was reached some other way -
# and RETRY isn't offered. Any scene but a result screen forgets it.
var retry_scene := ""
var retry_at_greyson := false


func _ready() -> void:
	get_tree().scene_changed.connect(_on_scene_changed)
	# scene_changed doesn't fire for the scene the game boots into.
	_on_scene_changed.call_deferred()


func reset_progress() -> void:
	fight_index = -1
	bosses_cleared = 0
	entrances_seen.clear()
	start_at_greyson = false
	start_at_finale = false
	start_at_liam = false


# Returns how many bosses the Victory screen's ladder should show as beaten.
func record_victory() -> int:
	if fight_index < 0:
		return bosses_cleared
	bosses_cleared = maxi(bosses_cleared, fight_index + 1)
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
	if scene == null or scene.scene_file_path in RESULT_SCENES:
		return
	var path := scene.scene_file_path
	fight_index = FIGHT_SCENES.find(PHASE_SCENES.get(path, path)) if path != "" else -1
	retry_scene = ""
	retry_at_greyson = false


# Notes where starting the fight being played in `tree` over begins. The pause screen's RESTART FIGHT and the Defeat
# screen's RETRY both start it there, through arm_retry(), so the two can't drift apart: the same scene - Jordan's
# Puppet Master, a scene of its own, included, and Liam's half from Bixby's - and in Greyson's half of FIGHT 06 that
# half again, the way the menu's GREYSON row opens it (reloading the scene alone played Computah's intro and his
# fight, already won, over again: the 2026-10-04 playtest).
func note_retry(tree: SceneTree) -> void:
	var path := tree.current_scene.scene_file_path
	retry_scene = path if is_fight_scene(path) else ""
	retry_at_greyson = false
	for boss in tree.get_nodes_in_group(FightOutro.BOSS_GROUP):
		var script: Script = boss.get_script()
		if script != null and script.resource_path == GREYSON_SCRIPT:
			retry_at_greyson = true


# Asks the fight note_retry() noted to open where it was noted, and returns its scene: "" for none.
func arm_retry() -> String:
	start_at_greyson = retry_at_greyson
	return retry_scene


# A scene the fight's pause screen answers in: a fight in the order, or a later phase of one (PHASE_SCENES).
func is_fight_scene(path: String) -> bool:
	return FIGHT_SCENES.has(path) or PHASE_SCENES.has(path)


static func _collect_fight_scenes() -> Array[String]:
	var scenes: Array[String] = []
	for boss in BOSSES:
		scenes.append(boss["scene"])
	return scenes
