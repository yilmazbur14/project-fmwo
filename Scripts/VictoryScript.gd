extends Control

const SLOT_TEXTURE := preload("res://Assets/UI/Screens/rank_slot.png")
const ICON_TEXTURE := preload("res://Assets/UI/Screens/rank_icons.png")
const LINK_TEXTURE := preload("res://Assets/UI/Screens/rank_link.png")
const ART_SCALE := 3
const SLOT_FRAME_WIDTH := 40
const LINK_FRAME_WIDTH := 8
# rank_icons.png's last frame, after the ten bosses' faces.
const INVITE_ICON := 10
const LADDER_CENTER_X := 960.0
const LADDER_TOP := 702.0
const SLOT_SIZE := 120.0
const SLOT_GAP := 24.0
const PULSE_TIME := 0.4

enum SlotFrame { LOCKED, CLEARED, CURRENT, CURRENT_PULSE, GOAL }
enum LinkFrame { LOCKED, CLEARED, NEXT }

@export var next_boss_button: Button
@export var timestamp_label: Label
@export var message_label: Label
@export var rank_ladder: Node2D
@export var fade_in_time := 0.5

var _current_slot: Sprite2D
# The next fight, loading on threads behind this screen: NEXT BOSS froze it for that load, 0.2 to 0.8 s a
# fight (the 2026-10-04 playtest).
var _prefetching := false
# The path it was requested under, for _exit_tree: GameProgress.next_boss_scene can be changed under the screen.
var _prefetch_path := ""
var _leaving := false

func _ready() -> void:
	if next_boss_button:
		next_boss_button.pressed.connect(_on_next_boss_button_pressed)
		if GameProgress.next_boss_scene == "":
			next_boss_button.text = "MAIN MENU"
		else:
			next_boss_button.text = "NEXT BOSS"
	if GameProgress.next_boss_scene != "":
		_prefetch_path = GameProgress.next_boss_scene
		_prefetching = ResourceLoader.load_threaded_request(_prefetch_path) == OK

	var cleared := GameProgress.record_victory()
	timestamp_label.text = _chat_timestamp()
	message_label.text = _rank_message(cleared)
	_build_rank_ladder(cleared)
	_fade_in()

func _on_next_boss_button_pressed() -> void:
	if _leaving:
		return
	_leaving = true
	if GameProgress.next_boss_scene == "":
		get_tree().change_scene_to_file("res://Scenes/Core/MainMenuScene.tscn")
		return
	var fight: PackedScene = ResourceLoader.load_threaded_get(GameProgress.next_boss_scene) if _prefetching else null
	if fight != null:
		get_tree().change_scene_to_packed(fight)
	else:
		get_tree().change_scene_to_file(GameProgress.next_boss_scene)


# Quitting on this screen with the prefetch still loading tears the engine down under the loader's threads, and the
# half-loaded fight prints parse errors at exit: waiting for it here closes it first. NEXT BOSS has taken it already.
func _exit_tree() -> void:
	if _prefetching and not _leaving:
		ResourceLoader.load_threaded_get(_prefetch_path)


func _rank_message(cleared: int) -> String:
	if GameProgress.fight_index < 0:
		return "@newcomer won the fight!"
	var rank: String = GameProgress.RANKS[cleared - 1]
	# The last fight on the ladder hands over the invite instead of a rank.
	if rank == "":
		return "@newcomer received an invite!"
	return "@newcomer ranked up to %s!" % rank


func _build_rank_ladder(cleared: int) -> void:
	var boss_count := GameProgress.FIGHT_SCENES.size()
	var slot_count := boss_count + 1
	var x := LADDER_CENTER_X - (slot_count * SLOT_SIZE + (slot_count - 1) * SLOT_GAP) / 2.0
	for i in slot_count:
		var state := _slot_frame(i, cleared, boss_count)
		# Locked slot art is opaque, so its icon would never show.
		if state != SlotFrame.LOCKED:
			_add_ladder_sprite(ICON_TEXTURE, SLOT_FRAME_WIDTH, _icon_frame(i, boss_count), x)
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


# A fight's slot shows that boss's own face, wherever the ladder puts him; the goal slot after them shows the invite.
func _icon_frame(index: int, boss_count: int) -> int:
	return GameProgress.BOSSES[index]["icon"] if index < boss_count else INVITE_ICON


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
	# The only button, and nothing takes focus by itself: without this a pad can't press it. Not
	# before the screen is up, though: A punches too, and a player still mashing it as the fight
	# ended would press NEXT BOSS before ever seeing this screen.
	if next_boss_button:
		tween.tween_callback(next_boss_button.grab_focus)
