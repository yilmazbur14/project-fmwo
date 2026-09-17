extends Control

const SLOT_TEXTURE := preload("res://Assets/UI/Screens/rank_slot.png")
const ICON_TEXTURE := preload("res://Assets/UI/Screens/rank_icons.png")
const LINK_TEXTURE := preload("res://Assets/UI/Screens/rank_link.png")
const ART_SCALE := 3
const SLOT_FRAME_WIDTH := 40
const LINK_FRAME_WIDTH := 8
const LADDER_CENTER_X := 960.0
const LADDER_TOP := 702.0
const SLOT_SIZE := 120.0
const SLOT_GAP := 24.0
const PULSE_TIME := 0.4
const RANKS := ["@member", "@regular", "@veteran", "@trusted", "@moderator"]

enum SlotFrame { LOCKED, CLEARED, CURRENT, CURRENT_PULSE, GOAL }
enum LinkFrame { LOCKED, CLEARED, NEXT }

@export var next_boss_button: Button
@export var timestamp_label: Label
@export var message_label: Label
@export var rank_ladder: Node2D
@export var fade_in_time := 0.5

var _current_slot: Sprite2D

func _ready() -> void:
	if next_boss_button:
		next_boss_button.pressed.connect(_on_next_boss_button_pressed)
		if GameProgress.next_boss_scene == "":
			next_boss_button.text = "MAIN MENU"
		else:
			next_boss_button.text = "NEXT BOSS"

	var cleared := GameProgress.record_victory()
	timestamp_label.text = _chat_timestamp()
	message_label.text = _rank_message(cleared)
	_build_rank_ladder(cleared)
	_fade_in()

func _on_next_boss_button_pressed() -> void:
	if GameProgress.next_boss_scene != "":
		get_tree().change_scene_to_file(GameProgress.next_boss_scene)
	else:
		get_tree().change_scene_to_file("res://Scenes/Core/MainMenuScene.tscn")


func _rank_message(cleared: int) -> String:
	if GameProgress.fight_index < 0:
		return "@newcomer won the fight!"
	if cleared >= GameProgress.FIGHT_SCENES.size():
		return "@newcomer received an invite!"
	return "@newcomer ranked up to %s!" % RANKS[cleared - 1]


func _build_rank_ladder(cleared: int) -> void:
	var boss_count := GameProgress.FIGHT_SCENES.size()
	var slot_count := boss_count + 1
	var x := LADDER_CENTER_X - (slot_count * SLOT_SIZE + (slot_count - 1) * SLOT_GAP) / 2.0
	for i in slot_count:
		var state := _slot_frame(i, cleared, boss_count)
		# Locked slot art is opaque, so its icon would never show.
		if state != SlotFrame.LOCKED:
			_add_ladder_sprite(ICON_TEXTURE, SLOT_FRAME_WIDTH, i, x)
		var slot := _add_ladder_sprite(SLOT_TEXTURE, SLOT_FRAME_WIDTH, state, x)
		if state == SlotFrame.CURRENT:
			_current_slot = slot
		if i < slot_count - 1:
			_add_ladder_sprite(LINK_TEXTURE, LINK_FRAME_WIDTH, _link_frame(i, cleared), x + SLOT_SIZE)
		x += SLOT_SIZE + SLOT_GAP

	var pulse_timer := Timer.new()
	pulse_timer.wait_time = PULSE_TIME
	pulse_timer.timeout.connect(_on_pulse_timer_timeout)
	add_child(pulse_timer)
	pulse_timer.start()


func _slot_frame(index: int, cleared: int, boss_count: int) -> SlotFrame:
	if index == boss_count:
		return SlotFrame.CURRENT if cleared >= boss_count else SlotFrame.GOAL
	if index < cleared:
		return SlotFrame.CLEARED
	if index == cleared:
		return SlotFrame.CURRENT
	return SlotFrame.LOCKED


# Link `index` joins slot `index` to the slot after it.
func _link_frame(index: int, cleared: int) -> LinkFrame:
	if index < cleared - 1:
		return LinkFrame.CLEARED
	if index == cleared - 1:
		return LinkFrame.NEXT
	return LinkFrame.LOCKED


func _add_ladder_sprite(texture: Texture2D, frame_width: int, frame: int, x: float) -> Sprite2D:
	var sprite := Sprite2D.new()
	sprite.texture = texture
	@warning_ignore("integer_division")
	sprite.hframes = texture.get_width() / frame_width
	sprite.frame = frame
	sprite.centered = false
	sprite.scale = Vector2(ART_SCALE, ART_SCALE)
	sprite.position = Vector2(x, LADDER_TOP)
	rank_ladder.add_child(sprite)
	return sprite


func _on_pulse_timer_timeout() -> void:
	_current_slot.frame = SlotFrame.CURRENT_PULSE if _current_slot.frame == SlotFrame.CURRENT else SlotFrame.CURRENT


func _chat_timestamp() -> String:
	var now := Time.get_time_dict_from_system()
	var hour: int = now.hour % 12
	if hour == 0:
		hour = 12
	return "Today at %d:%02d %s" % [hour, now.minute, "AM" if now.hour < 12 else "PM"]


func _fade_in() -> void:
	var fade := ColorRect.new()
	fade.color = Color.BLACK
	fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(fade)
	var tween := create_tween()
	tween.tween_property(fade, "color:a", 0.0, fade_in_time)
	tween.tween_callback(fade.queue_free)
