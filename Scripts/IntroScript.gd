extends Control

const CONTROLS_SCENE := "res://Scenes/Core/ControlsScene.tscn"

# The controls room, loading on threads while Danny's line is up: loaded as the line ended, it froze the
# line on screen for about a second (the 2026-10-04 playtest).
var prefetching := false


# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	prefetching = ResourceLoader.load_threaded_request(CONTROLS_SCENE) == OK
	DialogueManager.show_dialogue_balloon(load("res://Dialogue/DannyIntro.dialogue"), "start")
	DialogueManager.dialogue_ended.connect(_on_dialogue_ended)


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	pass

func _on_dialogue_ended(dialogue: Object) -> void:
	var room: PackedScene = ResourceLoader.load_threaded_get(CONTROLS_SCENE) if prefetching else null
	prefetching = false
	if room != null:
		get_tree().change_scene_to_packed(room)
	else:
		get_tree().change_scene_to_file(CONTROLS_SCENE)


# Quitting during the line with the room still loading tears the engine down under the loader's threads, and the
# half-loaded room prints parse errors at exit: waiting for it here closes it first.
func _exit_tree() -> void:
	if prefetching:
		ResourceLoader.load_threaded_get(CONTROLS_SCENE)
