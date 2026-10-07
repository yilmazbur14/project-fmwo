extends Node2D

# The tug-of-war meter over the sumo at 0 HP (DannyBossSumo), in the boss bar's place on the HUD
# (DannyBossArtLayout.METER): the player's red (the heart end) on the left and Danny's beanie blue on the
# right, meeting at the knot, which stands where the rope is. The fills are revealed by cropping their
# regions at their own texel columns, never stretched, so the knit of his stays put under the knot, and both
# step a whole texel at a time. The centre line, the tachiai line, stays put over them.
# The Sumo state pushes the rope in every step (set_rope) and holds `surging` on while Danny surges: his end
# glows through each surge, and the player's end pulses red while the rope is past DANGER_ROPE. Both pulses are
# code-drawn, on copies of the frame's own ends, until they are drawn. PUSH! under it is written out the
# way the finisher prompt writes the words it has no art for.
# THE MASH KEYS stand either side of it (show_keys), as the finisher prompt's stand either side of its meter:
# its key art for the device in use (FinisherArtLayout.keys, the bound button's glyph on a pad), taking turns
# to light until the first press, then the next one to press lit and a pressed one sinking (key_pressed).
# FinisherPromptUI's own logic, copied: it builds a whole prompt, meter and all, round a finisher.
# InputSettings is found in the tree rather than named, so this compiles where autoloads don't exist yet.
# The parts are the _3x copies at scale 1 on whole screen px, like the other HUD meters.

const Layout := preload("res://Scripts/DannyBossArtLayout.gd")
const FinisherArtLayout := preload("res://Scripts/FinisherArtLayout.gd")
# Loaded only where a pad's keys are the placeholder keycaps: it names InputSettings.
const CONTROLS_ART_LAYOUT := "res://Scripts/ControlsArtLayout.gd"

const DANGER_ROPE := -0.6
const PULSE_TIME := 0.1
const DANGER := Color(1.6, 0.5, 0.5)
const GLOW := Color(1.5, 1.5, 1.5)
# PUSH!, centred under the frame, alternating in the mash's own colours at MASH!'s rate, in
# FinisherPromptUI's font size and outline. Its numbers are copied rather than read off it: it names the
# InputSettings autoload, so preloading it would stop this compiling anywhere autoloads don't exist yet.
const WORD := "PUSH!"
const WORD_SIZE := Vector2(192, 60)
const WORD_FRAME_TIME := 0.15
const WORD_FONT_SIZE := 33
const WORD_OUTLINE := 6
# FinisherPromptUI's: the two keys take turns lighting until the first press, and a pressed one shows this long.
const KEY_FLASH_TIME := 0.12
const KEY_PULSE_TIME := 0.08

var rope := 0.0
var surging := false
var clock := 0.0
var spec: Dictionary = Layout.METER
var frame_size := Vector2.ZERO
var player_fill: Sprite2D
var danny_fill: Sprite2D
var player_end: Sprite2D
var danny_end: Sprite2D
var knot: Sprite2D
var word: Label
# The mash keys by action, where each rests, and which pair and device they were built for.
var keys := {}
var key_rest := {}
var key_actions: Array[StringName] = []
var gamepad_keys := false
# The next key to press, empty until the first press; the last pressed, and how long it shows as pressed.
var lit_action := &""
var pressed_action := &""
var pulse_left := 0.0


# Built here rather than in _ready, so the fight can set it up before adding it.
func _init() -> void:
	position = spec.anchor
	var frame := _part(spec.frame, Vector2.ZERO)
	frame_size = frame.texture.get_size()
	var channel: Rect2 = spec.channel
	player_fill = _part(spec.fill_player, channel.position)
	danny_fill = _part(spec.fill_danny, channel.position)
	for fill in [player_fill, danny_fill]:
		fill.region_enabled = true
	var texels := frame.texture.get_size() / Layout.SCALE
	player_end = _end_of(Rect2(0, 0, channel.position.x, texels.y))
	danny_end = _end_of(Rect2(channel.end.x, 0, texels.x - channel.end.x, texels.y))
	_part(spec.centre, spec.centre_at)
	knot = _part(spec.marker, Vector2.ZERO)
	knot.hframes = spec.marker_hframes
	word = _word(frame.texture.get_size())
	set_rope(0.0)
	_pulse()


func _process(delta: float) -> void:
	clock += delta
	knot.frame = int(clock / spec.marker_frame_time) % knot.hframes
	pulse_left = maxf(pulse_left - delta, 0.0)
	_pulse()
	_show_keys()


# The pair the mash runs on (PlayerFinisher.mash_actions), drawn either side of the meter for the device in use.
func show_keys(actions: Array[StringName]) -> void:
	for key in keys.values():
		key.queue_free()
	keys.clear()
	key_rest.clear()
	key_actions = actions.duplicate()
	lit_action = &""
	pressed_action = &""
	pulse_left = 0.0
	if key_actions.size() != 2:
		return
	var settings := get_node_or_null(^"/root/InputSettings")
	gamepad_keys = settings != null and settings.device == settings.Device.GAMEPAD
	var key_spec := FinisherArtLayout.keys(gamepad_keys)
	var key_size := Vector2.ZERO
	for action in key_actions:
		var key: CanvasItem
		if gamepad_keys and not FinisherArtLayout.USE_FINAL_PAD_KEYS:
			# The slot is one key wide, so a name longer than a bumper's drops a size.
			var controls: GDScript = load(CONTROLS_ART_LAYOUT)
			var button_name: String = settings.pad_label_for(action)
			var keycap: Label = controls.keycap(button_name, controls.KEY_FONT_SIZE if button_name.length() <= 2 else controls.KEY_SMALL_FONT_SIZE)
			keycap.size = key_spec.size
			key = keycap
			key_size = key_spec.size
		else:
			var sprite := Sprite2D.new()
			sprite.texture = load(key_spec.texture if gamepad_keys else key_spec[action])
			sprite.hframes = key_spec.hframes
			sprite.vframes = key_spec.get("vframes", 1)
			sprite.centered = false
			sprite.scale = Vector2.ONE * key_spec.scale
			key = sprite
			key_size = Vector2(sprite.texture.get_width() / float(sprite.hframes), sprite.texture.get_height() / float(sprite.vframes)) * key_spec.scale
		add_child(key)
		keys[action] = key
	var y := roundf((frame_size.y - key_size.y) / 2.0)
	key_rest[key_actions[0]] = Vector2(-FinisherArtLayout.PROMPT_KEY_GAP - key_size.x, y)
	key_rest[key_actions[1]] = Vector2(frame_size.x + FinisherArtLayout.PROMPT_KEY_GAP, y)
	_show_keys()


# A counted press of `action`: it sinks, and `next_action` is the one to press next.
func key_pressed(action: StringName, next_action: StringName) -> void:
	pressed_action = action
	lit_action = next_action
	pulse_left = KEY_PULSE_TIME


func _show_keys() -> void:
	if keys.is_empty():
		return
	var key_spec := FinisherArtLayout.keys(gamepad_keys)
	var settings := get_node_or_null(^"/root/InputSettings")
	var flashing := key_actions[0] if int(clock / KEY_FLASH_TIME) % 2 == 0 else key_actions[1]
	for action in keys:
		var look: Array = key_spec.idle
		if lit_action.is_empty():
			if action == flashing:
				look = key_spec.lit
		elif action == pressed_action and pulse_left > 0.0:
			look = key_spec.pressed
		elif action == lit_action:
			look = key_spec.lit
		var key: CanvasItem = keys[action]
		if key is Sprite2D:
			# On the pad sheet the look is a row offset, added to the bound button's own column.
			var column: int = settings.pad_frame_for(action) if gamepad_keys and settings != null else 0
			(key as Sprite2D).frame = column + look[0]
		key.modulate = look[1]
		key.position = key_rest[action] + Vector2(0, look[2])


# From -1, the player out past the bottom rope, to +1, Danny out past the top one.
func set_rope(value: float) -> void:
	rope = clampf(value, -1.0, 1.0)
	var channel: Rect2 = spec.channel
	var column := roundi(spec.marker_x0 + spec.marker_x_per_rope * rope)
	var split := column - int(channel.position.x)
	_reveal(player_fill, 0, split)
	_reveal(danny_fill, split, int(channel.size.x))
	knot.position = (Vector2(column, spec.marker_y) - spec.marker_centre) * Layout.SCALE


# The fill's own texels from `from` to `to` along the channel, where they sit in it.
func _reveal(fill: Sprite2D, from: int, to: int) -> void:
	var channel: Rect2 = spec.channel
	fill.visible = to > from
	fill.region_rect = Rect2(Vector2(from, 0) * Layout.SCALE, Vector2(to - from, channel.size.y) * Layout.SCALE)
	fill.position = (channel.position + Vector2(from, 0)) * Layout.SCALE


func _pulse() -> void:
	var on := int(clock / PULSE_TIME) % 2 == 0
	var danger := DANGER if rope < DANGER_ROPE and on else Color.WHITE
	var glow := GLOW if surging and on else Color.WHITE
	player_fill.modulate = danger
	player_end.modulate = danger
	danny_fill.modulate = glow
	danny_end.modulate = glow
	var colors: Array = FinisherArtLayout.prompt_word(&"mash").colors
	word.add_theme_color_override("font_color", colors[int(clock / WORD_FRAME_TIME) % colors.size()])


# A part at `at`, in texels from the frame's top-left.
func _part(path: String, at: Vector2) -> Sprite2D:
	var part := Sprite2D.new()
	part.texture = load(path)
	part.centered = false
	part.position = at * Layout.SCALE
	add_child(part)
	return part


# A copy of the frame's texels in `ends`, over the frame itself, for the pulse to tint.
func _end_of(ends: Rect2) -> Sprite2D:
	var end := _part(spec.frame, ends.position)
	end.region_enabled = true
	end.region_rect = Rect2(ends.position * Layout.SCALE, ends.size * Layout.SCALE)
	return end


func _word(frame_size: Vector2) -> Label:
	var label := Label.new()
	label.theme = load("res://Assets/UI/ui_theme.tres")
	label.add_theme_font_size_override("font_size", WORD_FONT_SIZE)
	label.add_theme_constant_override("outline_size", WORD_OUTLINE)
	label.add_theme_color_override("font_outline_color", Color(0, 0, 0))
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.text = WORD
	label.size = WORD_SIZE
	label.position = Vector2((frame_size.x - WORD_SIZE.x) / 2.0, frame_size.y)
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(label)
	return label
