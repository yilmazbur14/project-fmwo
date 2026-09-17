extends Node

# Autoload singleton. Set by a boss just before it transitions to the
# shared VictoryScene.tscn, so that scene knows which fight comes next.
# Empty string means "no next boss configured yet" - the Victory screen
# falls back to returning to the Main Menu.
var next_boss_scene: String = ""

# The story's fights in order: the scene each one loads, the name the screens
# show it under, and the rank its win promotes the player to. Beating the last
# one hands over the invite instead of a rank, so its rank is empty.
# Fights whose scene hasn't been built yet stay in the table - next_fight_after()
# skips them until their scene exists, so the ladder can show the whole order.
const BOSSES: Array[Dictionary] = [
	{"scene": "res://Scenes/Bosses/EricBossFightScene.tscn", "name": "ERIC", "rank": "@member"},
	{"scene": "res://Scenes/Bosses/GreysonBossFightScene.tscn", "name": "GREYSON & COMPUTAH", "rank": "@regular"},
	{"scene": "res://Scenes/Bosses/MasonBossFightScene.tscn", "name": "MASON", "rank": "@veteran"},
	{"scene": "res://Scenes/Bosses/JoshBossFightScene.tscn", "name": "JOSH", "rank": "@trusted"},
	{"scene": "res://Scenes/Bosses/CarterBossFightScene.tscn", "name": "CARTER", "rank": "@moderator"},
	{"scene": "res://Scenes/Bosses/LiamBossFightScene.tscn", "name": "LIAM & BIXBY", "rank": "@admin"},
	{"scene": "res://Scenes/Bosses/JordanBossFightScene.tscn", "name": "JORDAN", "rank": ""},
]

# Just the fight scenes, in the same order.
static var FIGHT_SCENES: Array[String] = _collect_fight_scenes()

# The result screens report on the fight that led to them, so arriving at one
# must not overwrite fight_index.
const RESULT_SCENES: Array[String] = [
	"res://Scenes/Core/VictoryScene.tscn",
	"res://Scenes/Core/DefeatScene.tscn",
]

# Index into FIGHT_SCENES of the fight the player is in (or just left for a
# result screen); -1 for anything outside the order.
var fight_index := -1
var bosses_cleared := 0


func _ready() -> void:
	get_tree().scene_changed.connect(_on_scene_changed)
	# scene_changed doesn't fire for the scene the game boots into.
	_on_scene_changed.call_deferred()


func reset_progress() -> void:
	fight_index = -1
	bosses_cleared = 0


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


# The name the screens and the fight's own health bar show `fight_scene` under.
func boss_name(fight_scene: String) -> String:
	var index := FIGHT_SCENES.find(fight_scene)
	return BOSSES[index]["name"] if index >= 0 else ""


func _on_scene_changed() -> void:
	var scene := get_tree().current_scene
	if scene == null or scene.scene_file_path in RESULT_SCENES:
		return
	var path := scene.scene_file_path
	fight_index = FIGHT_SCENES.find(path) if path != "" else -1


static func _collect_fight_scenes() -> Array[String]:
	var scenes: Array[String] = []
	for boss in BOSSES:
		scenes.append(boss["scene"])
	return scenes
