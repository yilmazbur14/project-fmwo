extends Node

# Autoload singleton. Set by a boss just before it transitions to the
# shared VictoryScene.tscn, so that scene knows which fight comes next.
# Empty string means "no next boss configured yet" - the Victory screen
# falls back to returning to the Main Menu.
var next_boss_scene: String = ""

# The story's fights in order. "" marks a fight that isn't built yet.
const FIGHT_SCENES: Array[String] = [
	"res://Scenes/Bosses/EricBossFightScene.tscn",
	"res://Scenes/Bosses/GreysonBossFightScene.tscn",
	"res://Scenes/Bosses/CarterAndJoshBossFightScene.tscn",
	"res://Scenes/Bosses/LiamBossFightScene.tscn",
	"res://Scenes/Bosses/JordanBossFightScene.tscn",
]

# The result screens report on the fight that led to them, so arriving at one
# must not overwrite fight_index.
const RESULT_SCENES: Array[String] = [
	"res://Scenes/Core/VictoryScene.tscn",
	"res://Scenes/Core/DefeatScene.tscn",
]

# Index into FIGHT_SCENES of the fight the player is in (or just left for a
# result screen); -1 for anything outside the order, e.g. Mason.
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


func _on_scene_changed() -> void:
	var scene := get_tree().current_scene
	if scene == null or scene.scene_file_path in RESULT_SCENES:
		return
	var path := scene.scene_file_path
	fight_index = FIGHT_SCENES.find(path) if path != "" else -1
