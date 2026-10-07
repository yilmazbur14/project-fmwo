extends Control

# The last card of Jordan's finale, and where every skip of the finale lands too (JordanWalkOut, JordanFinaleScript):
# TO BE CONTINUED on black, its three dots one at a time, a hold, and out to the main menu. A press of accept, cancel
# or punch cuts the hold short, but only once INPUT_AFTER real seconds have passed: a key still held or mashed from
# the skip that led here would otherwise go straight through the card.

const ScreenView := preload("res://Scripts/ScreenView.gd")
const HitStop := preload("res://Scripts/HitStop.gd")

const MENU_SCENE := "res://Scenes/Core/MainMenuScene.tscn"
const TEXT := "TO BE CONTINUED"
const DOTS := 3
# Seconds.
const FADE_IN := 1.2
const DOT_STEP := 0.35
const HOLD := 3.0
const FADE_OUT := 1.0
# Real seconds from the card coming up before a press counts.
const INPUT_AFTER := 1.0

@onready var title: Label = $Title

var shown_msec := 0
var leaving := false
var run: Tween


func _ready() -> void:
	# Whatever zoom, shake or hit-stop the finale was in when it was cut short must not carry onto the card.
	ScreenView.reset(get_tree())
	HitStop.clear()
	shown_msec = Time.get_ticks_msec()
	title.text = TEXT + ".".repeat(DOTS)
	title.visible_characters = TEXT.length()
	title.modulate.a = 0.0
	run = create_tween()
	run.tween_property(title, "modulate:a", 1.0, FADE_IN)
	for i in DOTS:
		run.tween_interval(DOT_STEP)
		run.tween_callback(_show_dots.bind(i + 1))
	run.tween_interval(HOLD)
	run.tween_callback(_leave)


func _show_dots(count: int) -> void:
	title.visible_characters = TEXT.length() + count


func _unhandled_input(event: InputEvent) -> void:
	InputSettings.note_device(event)
	if leaving or Time.get_ticks_msec() - shown_msec < INPUT_AFTER * 1000.0:
		return
	if event.is_action_pressed(&"ui_accept") or event.is_action_pressed(&"ui_cancel") or event.is_action_pressed(&"punch"):
		get_viewport().set_input_as_handled()
		_leave()


# The card fades out and the menu comes up. Once, whichever of the hold and a press gets here first.
func _leave() -> void:
	if leaving:
		return
	leaving = true
	if run != null and run.is_valid():
		run.kill()
	var out := create_tween()
	out.tween_property(title, "modulate:a", 0.0, FADE_OUT)
	out.tween_callback(get_tree().change_scene_to_file.bind(MENU_SCENE))
