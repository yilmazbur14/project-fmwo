extends Control

const ControlsArtLayout := preload("res://Scripts/ControlsArtLayout.gd")

const MOVE_TITLE_ARROWS := "Classic arrow key movement"
const MOVE_TITLE_KEYS := "Movement"
const MOVE_TITLE_PAD := "Left stick or D-pad"

@onready var ReadyButton: Button = %ReadyButton
@onready var move_title: Label = %MoveTitle
@onready var glyphs := {
	InputSettings.MOVE: %MoveGlyph,
	&"punch": %AttackGlyph,
	&"dodge": %DashGlyph,
	&"block": %BlockGlyph,
}

# The hand-drawn keys the scene ships with, put back whenever the keyboard is on its defaults, so the
# approved screen stays exactly as it was drawn.
var keyboard_art := {}
# One per card, next to its glyph in the card's CenterContainer: shown instead of the glyph whenever
# there is no art for what the card has to say.
var keycaps := {}


func _ready() -> void:
	for action in glyphs:
		var glyph: TextureRect = glyphs[action]
		keyboard_art[action] = glyph.texture
		var keycap := ControlsArtLayout.keycap("")
		glyph.get_parent().add_child(keycap)
		keycaps[action] = keycap
	_show_controls()
	# Plugging a pad in, or touching the keyboard again, repaints every card on the spot.
	InputSettings.device_changed.connect(_show_controls.unbind(1))
	InputSettings.bindings_changed.connect(_show_controls)

	_set_ready_button_locked(true)
	DialogueManager.show_dialogue_balloon(load("res://Dialogue/ControlsSceneDialogue.dialogue"), "start")
	DialogueManager.dialogue_ended.connect(_on_dialogue_ended)

	ReadyButton.pressed.connect(_on_ready_button_pressed)


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	pass

func _on_ready_button_pressed() -> void:
	get_tree().change_scene_to_file("res://Scenes/Bosses/EricBossFightScene.tscn")

func _on_dialogue_ended(dialogue: Object) -> void:
	# get_tree().change_scene_to_file("res://Scenes/ArenaScene.tscn")
	_set_ready_button_locked(false)

func _set_ready_button_locked(locked: bool) -> void:
	ReadyButton.disabled = locked
	ReadyButton.focus_mode = Control.FOCUS_NONE if locked else Control.FOCUS_ALL
	# Nothing else on the screen takes focus, so without this a pad has nothing to press.
	if not locked:
		ReadyButton.grab_focus()


func _show_controls() -> void:
	var gamepad := InputSettings.device == InputSettings.Device.GAMEPAD
	for action in glyphs:
		var glyph: TextureRect = glyphs[action]
		var keycap: Label = keycaps[action]
		var art := _art(action, gamepad)
		glyph.visible = art != null
		if art:
			glyph.texture = art
		keycap.visible = art == null
		if action == InputSettings.MOVE:
			keycap.text = InputSettings.move_name
		else:
			ControlsArtLayout.paint_keycap(keycap, action, gamepad)
	if gamepad:
		move_title.text = MOVE_TITLE_PAD
	elif InputSettings.is_default(InputSettings.MOVE, false):
		move_title.text = MOVE_TITLE_ARROWS
	else:
		move_title.text = MOVE_TITLE_KEYS


# The drawn art for a card, or null when the keycap has to say it instead.
func _art(action: StringName, gamepad: bool) -> Texture2D:
	if not gamepad:
		return keyboard_art[action] if InputSettings.is_default(action, false) else null
	if action == InputSettings.MOVE:
		return ControlsArtLayout.pad_move() if ControlsArtLayout.USE_FINAL_PAD_MOVE else null
	if ControlsArtLayout.USE_FINAL_PAD_GLYPHS and InputSettings.is_bound(action, true):
		return ControlsArtLayout.pad_glyph(action)
	return null
