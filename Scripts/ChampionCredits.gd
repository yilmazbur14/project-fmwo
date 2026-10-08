extends Control

# The credits at the end of the champion ending (ChampionEndingScript), built in code over an opaque black: the title
# block centred, fading in and holding; the roll scrolling up at CREDITS_SPEED until it is gone; then THANK YOU FOR
# PLAYING, which `ended` hands back to the ending once its hold is over or a press has cut it short. leave() fades the
# text out. The song is the ending's, and keeps playing under all of it. Every number is ChampionEndingLayout's.
#
# THE TESTS READ: phase (&"title", &"roll", &"thanks", &"leaving") and rendered_lines().

signal ended

const Layout := preload("res://Scripts/ChampionEndingLayout.gd")
const UI_THEME := "res://Assets/UI/ui_theme.tres"
const VIEW_SIZE := Vector2(1920, 1080)

# Whether the ending's own song played, for its line under MUSIC. Set before this enters the tree.
var own_track_played := false
var phase := &"title"
var roll: Control
var thanks: Control
# Every line in the roll and the THANK YOU card, in order: {kind, text}.
var lines: Array[Dictionary] = []
var roll_height := 0.0
var scroll := 0.0
var thanks_shown_msec := 0
var run: Tween


func _ready() -> void:
	theme = load(UI_THEME)
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	var black := ColorRect.new()
	black.color = Color.BLACK
	black.mouse_filter = Control.MOUSE_FILTER_IGNORE
	black.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(black)
	roll = Control.new()
	roll.name = "Roll"
	roll.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(roll)
	_build_roll()
	_build_thanks()
	roll.modulate.a = 0.0
	run = create_tween()
	run.tween_property(roll, "modulate:a", 1.0, Layout.CREDITS_TITLE_FADE)
	run.tween_interval(Layout.CREDITS_TITLE_HOLD)
	run.tween_callback(func() -> void: phase = &"roll")


func rendered_lines() -> Array[Dictionary]:
	return lines


func _process(delta: float) -> void:
	if phase != &"roll":
		return
	scroll += Layout.CREDITS_SPEED * delta
	roll.position.y = -roundf(scroll)
	if roll.position.y + roll_height < 0.0:
		_show_thanks()


func _unhandled_input(event: InputEvent) -> void:
	InputSettings.note_device(event)
	if phase != &"thanks" or Time.get_ticks_msec() - thanks_shown_msec < Layout.CREDITS_PRESS_AFTER * 1000.0:
		return
	if event.is_action_pressed(&"ui_accept") or event.is_action_pressed(&"ui_cancel") or event.is_action_pressed(&"punch"):
		get_viewport().set_input_as_handled()
		_end()


# The text fades out over `seconds`; the black stays.
func leave(seconds: float) -> void:
	phase = &"leaving"
	if run != null and run.is_valid():
		run.kill()
	var out := create_tween()
	out.tween_property(roll, "modulate:a", 0.0, seconds)
	out.parallel().tween_property(thanks, "modulate:a", 0.0, seconds)


#THE ROLL

# The title block first, centred on the screen, and everything else from just under the screen's bottom edge, so the
# title holds alone before the roll brings the rest up.
func _build_roll() -> void:
	var title_block: Array = [[&"title", Layout.CREDITS_GAME], [&"role", Layout.CREDITS_BY], [&"name", Layout.CREDITS_NAME]]
	var title_height := _block_height(title_block)
	var y := roundf((VIEW_SIZE.y - title_height) / 2.0)
	y = _add_block(title_block, y)
	y = maxf(y, VIEW_SIZE.y)
	for role in Layout.CREDITS_ROLES:
		y = _add_block([[&"role", role], [&"name", Layout.CREDITS_NAME]], y) + Layout.CREDITS_BLOCK_GAP
	y = _add_block([[&"section", Layout.CREDITS_CAST_TITLE], [&"small", Layout.CREDITS_CAST_NOTE]],
		y - Layout.CREDITS_BLOCK_GAP + Layout.CREDITS_SECTION_GAP)
	var cast: Array = []
	for member in Layout.CREDITS_CAST:
		cast.append([&"name", member])
	cast.append([&"small", Layout.CREDITS_NEWCOMER_NOTE])
	cast.append([&"name", Layout.CREDITS_NEWCOMER])
	y = _add_block(cast, y)
	var music: Array = []
	for entry in Layout.CREDITS_MUSIC:
		if _shows(entry):
			music.append([&"name", "\"%s\"" % entry.title])
			music.append([&"role", entry.artist])
	if not music.is_empty():
		y = _add_block([[&"section", Layout.CREDITS_MUSIC_TITLE]] + music, y + Layout.CREDITS_SECTION_GAP)
	var tools: Array = [[&"section", Layout.CREDITS_TOOLS_TITLE]]
	for tool in Layout.CREDITS_TOOLS:
		tools.append([&"name", tool])
	y = _add_block(tools, y + Layout.CREDITS_SECTION_GAP)
	var thanked: Array = [[&"section", Layout.CREDITS_THANKS_TITLE]]
	for who in Layout.CREDITS_THANKS:
		thanked.append([&"name", who])
	y = _add_block(thanked, y + Layout.CREDITS_SECTION_GAP)
	var small: Array = []
	for text in Layout.CREDITS_SMALL_PRINT:
		small.append([&"small", text])
	y = _add_block(small, y + Layout.CREDITS_SECTION_GAP)
	roll_height = y


# A music entry: its title and artist filled in and its file there, and the ending's own song only if it played.
func _shows(entry: Dictionary) -> bool:
	if String(entry.title).is_empty() or String(entry.artist).is_empty() or not ResourceLoader.exists(entry.file):
		return false
	return own_track_played or not entry.get("ending_song", false)


# The block's lines one under another from `y`; where the next block can start.
func _add_block(block: Array, y: float) -> float:
	for line in block:
		var label := _label(line[0], line[1])
		label.position = Vector2(0.0, y)
		roll.add_child(label)
		lines.append({"kind": line[0], "text": line[1]})
		y += _line_height(line[0]) + Layout.CREDITS_GAP_AFTER[line[0]]
	return y


func _block_height(block: Array) -> float:
	var height := 0.0
	for i in block.size():
		height += _line_height(block[i][0])
		if i < block.size() - 1:
			height += Layout.CREDITS_GAP_AFTER[block[i][0]]
	return height


func _line_height(kind: StringName) -> float:
	return ceilf(get_theme_default_font().get_height(Layout.CREDITS_STYLES[kind].size))


# A line across the whole screen, centred, in its kind's size and colour.
func _label(kind: StringName, text: String) -> Label:
	var style: Dictionary = Layout.CREDITS_STYLES[kind]
	var label := Label.new()
	label.text = text
	if style.type != &"":
		label.theme_type_variation = style.type
	label.add_theme_font_size_override("font_size", style.size)
	label.add_theme_color_override("font_color", style.color)
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	label.size = Vector2(VIEW_SIZE.x, _line_height(kind))
	return label


#THANK YOU

# THANK YOU FOR PLAYING centred on the black - or, with the still in, the still full screen behind it and the words in
# the dark sky above the champion, outlined.
func _build_thanks() -> void:
	thanks = Control.new()
	thanks.name = "Thanks"
	thanks.mouse_filter = Control.MOUSE_FILTER_IGNORE
	thanks.modulate.a = 0.0
	thanks.hide()
	add_child(thanks)
	var label := _label(&"thanks", Layout.CREDITS_THANK_YOU)
	var top := roundf((VIEW_SIZE.y - _line_height(&"thanks")) / 2.0)
	if Layout.final_credits_art():
		var still := TextureRect.new()
		still.name = "Still"
		still.texture = load(Layout.CREDITS_ART)
		still.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		still.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		still.size = VIEW_SIZE
		still.mouse_filter = Control.MOUSE_FILTER_IGNORE
		thanks.add_child(still)
		top = Layout.CREDITS_THANKS_OVER_ART_Y
		label.add_theme_color_override("font_outline_color", Color.BLACK)
		label.add_theme_constant_override("outline_size", Layout.CREDITS_THANKS_OUTLINE)
	label.position = Vector2(0.0, top)
	thanks.add_child(label)
	lines.append({"kind": &"thanks", "text": Layout.CREDITS_THANK_YOU})


func _show_thanks() -> void:
	phase = &"thanks"
	roll.hide()
	thanks.show()
	thanks_shown_msec = Time.get_ticks_msec()
	run = create_tween()
	run.tween_property(thanks, "modulate:a", 1.0, Layout.CREDITS_THANKS_FADE)
	run.tween_interval(Layout.CREDITS_THANKS_HOLD)
	run.tween_callback(_end)


func _end() -> void:
	if phase != &"thanks":
		return
	if run != null and run.is_valid():
		run.kill()
	ended.emit()
