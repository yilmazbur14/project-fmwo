extends Control

# The art is 640x360 texels drawn at 3x. Every position here is in whole street texels, so no texel
# lands between screen pixels.

signal burak_stepped
signal burak_anim_finished

const NEXT_SCENE := "res://Scenes/Core/IntroScene.tscn"
const THOUGHTS := preload("res://Dialogue/IntroCutscene.dialogue")

#TIMING (seconds)
const FADE_IN_SECONDS := 1.0
# From the start of the fade-in to the first thought. He keeps walking while it shows.
const WALK_LINE_DELAY := 1.5
# The whole dip to black between the walk-in and the poster wall.
const CUT_DIP_SECONDS := 0.4
const BEAT_BEFORE_NOTICE := 0.6
const NOTICE_HOLD_SECONDS := 0.3
const READ_SECONDS := 1.5
const CLOSEUP_HOLD_SECONDS := 1.0
const CLOSEUP_AFTER_LINES_SECONDS := 0.5
# Keep this under one read cycle (1.6), so resolve cuts in on read frame 14 (the frame it is drawn to
# follow) instead of racing the loop back to frame 13.
const BEAT_BEFORE_RESOLVE := 1.5
const BEAT_BEFORE_WALK_OFF := 0.4
const FADE_OUT_SECONDS := 1.2

#STAGING (street texels)
const WALK_IN_START_X := 150
const WALK_IN_END_X := 330
const ARRIVAL_START_X := 780
const POSTER_STOP_X := 915
const FADE_OUT_X := 1000
const POSTER_CAM_X := 640
const SKY_PARALLAX := 0.25
const FEET_Y := 262

#BURAK (burak_cutscene.png, 25 frames of 64x64)
const HIP_TEXEL := 30
const FRAME_HEIGHT := 64
# How long each frame shows, and how far his hips move as it appears. The moves match the stride
# drawn on the sheet, so his planted foot stays put.
const FRAME_MS: Array[int] = [150, 150, 150, 150, 150, 150, 150, 150, 160, 420, 300, 380, 650, 800, 800, 240, 360, 220, 900, 120, 120, 120, 120, 120, 120]
const FRAME_ADVANCE: Array[int] = [3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 4, 4, 4, 4]
# [first frame, last frame, loops]. One-shot animations hold their last frame.
const ANIMS := {
	&"walk_gloomy": [0, 7, true],
	&"stop": [8, 9, false],
	&"notice": [10, 12, false],
	&"read": [13, 14, true],
	&"resolve": [15, 18, false],
	&"walk_purpose": [19, 24, true],
}

#AUDIO
const MUSIC_VOLUME_DB := -6.0

@onready var street: Node2D = $Street
@onready var sky: Sprite2D = $Street/Sky
@onready var buildings: Sprite2D = $Street/Buildings
@onready var burak: Sprite2D = $Street/Burak
@onready var foreground: Sprite2D = $Street/Foreground
@onready var poster_closeup: Sprite2D = $PosterCloseup
@onready var fade: ColorRect = $FadeLayer/Fade
@onready var skip_hint: Label = $HintLayer/SkipHint
@onready var music_player: AudioStreamPlayer = $MusicPlayer

var cam_x := 0
var hip_x := 0
var anim_first := 0
var anim_last := 0
var anim_loops := false
var anim_holding := false
var frame_clock := 0.0
# While walking gloomy: the hip x that stop's first frame should land on. -1 when he isn't stopping.
var stop_mark_x := -1

var balloon: Node
var thinking := false
var fade_tween: Tween
var leaving := false


func _ready() -> void:
	DialogueManager.dialogue_ended.connect(_on_dialogue_ended)
	music_player.stream.loop = true
	music_player.play()
	_play_cutscene()


func _input(event: InputEvent) -> void:
	# _input, not _unhandled_input: the dialogue balloon swallows all unhandled input while it is up.
	if event is InputEventKey and event.keycode == KEY_ESCAPE and event.pressed and not event.echo:
		get_viewport().set_input_as_handled()
		_leave()


func _process(delta: float) -> void:
	if anim_holding:
		return
	frame_clock += delta
	while not anim_holding and frame_clock >= FRAME_MS[burak.frame] / 1000.0:
		frame_clock -= FRAME_MS[burak.frame] / 1000.0
		_next_frame()


func _play_cutscene() -> void:
	_set_cam(0)
	_start_burak(&"walk_gloomy", WALK_IN_START_X)
	fade_tween = create_tween().set_parallel()
	fade_tween.tween_property(fade, "color:a", 0.0, FADE_IN_SECONDS)
	fade_tween.tween_property(music_player, "volume_linear", db_to_linear(MUSIC_VOLUME_DB), FADE_IN_SECONDS)
	get_tree().create_timer(WALK_LINE_DELAY).timeout.connect(_think.bind("walk"))
	await _walk_until(WALK_IN_END_X)

	await _fade_screen(1.0, CUT_DIP_SECONDS / 2.0)
	if leaving:
		return
	_set_cam(POSTER_CAM_X)
	# Enter partway into a cycle, so frame 7 (which stop is drawn to follow) lands one step short of the mark.
	var strides: int = (POSTER_STOP_X - FRAME_ADVANCE[8] - ARRIVAL_START_X) / FRAME_ADVANCE[0]
	_start_burak(&"walk_gloomy", ARRIVAL_START_X, posmod(7 - strides, 8))
	stop_mark_x = POSTER_STOP_X
	_fade_screen(0.0, CUT_DIP_SECONDS / 2.0)
	await burak_anim_finished
	await get_tree().create_timer(BEAT_BEFORE_NOTICE).timeout
	_play_burak(&"notice")
	await burak_anim_finished
	await get_tree().create_timer(NOTICE_HOLD_SECONDS).timeout
	_play_burak(&"read")
	await get_tree().create_timer(READ_SECONDS).timeout
	# If the first thought is still up, he keeps reading until the player dismisses it.
	await _thoughts_done()
	if leaving:
		return

	_show_closeup(true)
	await get_tree().create_timer(CLOSEUP_HOLD_SECONDS).timeout
	_think("poster")
	await _thoughts_done()
	await get_tree().create_timer(CLOSEUP_AFTER_LINES_SECONDS).timeout
	if leaving:
		return

	_show_closeup(false)
	_start_burak(&"read", POSTER_STOP_X)
	await get_tree().create_timer(BEAT_BEFORE_RESOLVE).timeout
	_play_burak(&"resolve")
	await burak_anim_finished
	_think("resolve")
	await _thoughts_done()
	await get_tree().create_timer(BEAT_BEFORE_WALK_OFF).timeout
	_play_burak(&"walk_purpose")
	await _walk_until(FADE_OUT_X)
	_leave()


func _set_cam(x: int) -> void:
	cam_x = x
	sky.position.x = -roundi(x * SKY_PARALLAX)
	buildings.position.x = -x
	foreground.position.x = -x
	_place_burak()


func _show_closeup(on: bool) -> void:
	poster_closeup.visible = on
	street.visible = not on


func _start_burak(anim: StringName, at_x: int, start_frame: int = -1) -> void:
	_set_anim(anim)
	hip_x = at_x
	frame_clock = 0.0
	burak.frame = anim_first if start_frame < 0 else start_frame
	_place_burak()


func _play_burak(anim: StringName) -> void:
	_set_anim(anim)
	frame_clock = 0.0
	_show_frame(anim_first)


func _set_anim(anim: StringName) -> void:
	anim_first = ANIMS[anim][0]
	anim_last = ANIMS[anim][1]
	anim_loops = ANIMS[anim][2]
	anim_holding = false


func _next_frame() -> void:
	if burak.frame < anim_last:
		_show_frame(burak.frame + 1)
	elif not anim_loops:
		anim_holding = true
		burak_anim_finished.emit()
	elif stop_mark_x >= 0 and hip_x + FRAME_ADVANCE[8] >= stop_mark_x:
		stop_mark_x = -1
		_set_anim(&"stop")
		_show_frame(anim_first)
	else:
		_show_frame(anim_first)


func _show_frame(index: int) -> void:
	hip_x += FRAME_ADVANCE[index]
	burak.frame = index
	_place_burak()
	burak_stepped.emit()


func _place_burak() -> void:
	burak.position = Vector2(hip_x - cam_x - HIP_TEXEL, FEET_Y - FRAME_HEIGHT + 1)


func _walk_until(x: int) -> void:
	while hip_x < x:
		await burak_stepped


func _think(title: String) -> void:
	if leaving:
		return
	thinking = true
	balloon = DialogueManager.show_dialogue_balloon(THOUGHTS, title)


func _thoughts_done() -> void:
	if thinking:
		await DialogueManager.dialogue_ended


func _on_dialogue_ended(_resource: DialogueResource) -> void:
	thinking = false


func _fade_screen(alpha: float, seconds: float) -> void:
	if leaving:
		return
	if fade_tween:
		fade_tween.kill()
	fade_tween = create_tween()
	fade_tween.tween_property(fade, "color:a", alpha, seconds)
	await fade_tween.finished


func _leave() -> void:
	if leaving:
		return
	leaving = true
	if is_instance_valid(balloon):
		balloon.queue_free()
	if fade_tween:
		fade_tween.kill()
	# A skip during the fade-in or a dip starts from partly black.
	var seconds := FADE_OUT_SECONDS * (1.0 - fade.color.a)
	var tween := create_tween().set_parallel()
	tween.tween_property(fade, "color:a", 1.0, seconds)
	tween.tween_property(skip_hint, "modulate:a", 0.0, seconds)
	tween.tween_property(music_player, "volume_linear", 0.0, seconds)
	await tween.finished
	get_tree().change_scene_to_file(NEXT_SCENE)
