extends CanvasLayer

# The versus card a fight opens on: a Pokemon-Platinum-style banner over the darkened arena, the
# player's bust on the left, the boss's on the right and the VS landing on the seam between them.
# It rides in ArenaScene, so every fight has one, and it plays between the pre-fight lines and the
# fight itself - each boss's _on_dialogue_ended hands over through play_intro() and gets its fight
# back from `finished`.
#
# NOTHING IN A FIGHT MAY START UNDER IT. play() holds the player where the lines left them, and the
# fight's own start is hung off `finished`, so the boss's first attack and the player's control both
# begin once the card is gone. The pause screen refuses to open while it plays (PauseMenu.can_open),
# the way it refuses during an outro.
#
# Its clock is a _physics_process accumulator and every beat is interpolated from it, so the card is
# a pure function of that clock: skipping is moving the clock to the flash-out, and a freeze, a
# hit-stop or a pause can't run it on its own the way get_tree().create_timer() or a tree-level
# tween would.

signal finished

const VsCardArtLayout := preload("res://Scripts/VsCardArtLayout.gd")

# Where the card sits in a fight scene, from the scene's root.
const CARD_PATH := ^"Arena/VsCard"

# Real seconds after the card during which the presses that could leak into the fight are eaten -
# the same grace the pause screen gives a resume, and for the same reason: the press that skipped
# the card is marked handled, but a mash lands the next one a frame or two later. Real, not game
# time, and `pause` is deliberately not in the list: the fight is the player's the moment the card
# is gone, and so is the pause screen.
const INPUT_GRACE := 0.15
const GRACE_ACTIONS: Array[StringName] = [
	&"punch", &"dodge", &"block", &"mash_left", &"mash_right", &"ui_accept", &"ui_cancel",
]

@onready var back: Control = $Back
@onready var card: Control = $Card
@onready var flash: ColorRect = $Flash

var playing := false
var clock := 0.0
var grace_until_msec := 0

# Rebuilt per play() from the fight's own row of the table.
var left_half: Node2D
var right_half: Node2D
var seam_flash: Node2D
var writing: Node2D
var name_art: CanvasItem
var win_art: CanvasItem
var burst: Node2D
var vs: Node2D
# Where the two pieces that slide in from the right end up.
var name_home := Vector2.ZERO
var win_home := Vector2.ZERO


# The one place a fight hands over from its pre-fight lines to the card and back. `start_fight` runs
# when the card is done, whether it played out or was skipped; a scene with no card in it starts its
# fight straight away, so nothing is ever left waiting on a card that isn't there.
static func play_intro(fight_node: Node, boss_key: String, start_fight: Callable) -> void:
	var intro := in_fight(fight_node.get_tree())
	if intro == null:
		start_fight.call()
		return
	intro.finished.connect(start_fight, CONNECT_ONE_SHOT)
	intro.play(boss_key)


static func in_fight(tree: SceneTree) -> Node:
	if tree == null or tree.current_scene == null:
		return null
	return tree.current_scene.get_node_or_null(CARD_PATH)


func _ready() -> void:
	$Back/Dim.color = VsCardArtLayout.DIM_COLOR
	var strips := [
		[$Back/Letterbox/Top, VsCardArtLayout.LETTERBOX_TOP[0], VsCardArtLayout.LETTERBOX_COLOR],
		[$Back/Letterbox/TopRule, VsCardArtLayout.LETTERBOX_TOP[1], VsCardArtLayout.LETTERBOX_RULE_COLOR],
		[$Back/Letterbox/Bottom, VsCardArtLayout.LETTERBOX_BOTTOM[0], VsCardArtLayout.LETTERBOX_COLOR],
		[$Back/Letterbox/BottomRule, VsCardArtLayout.LETTERBOX_BOTTOM[1], VsCardArtLayout.LETTERBOX_RULE_COLOR],
	]
	for strip in strips:
		var rect: ColorRect = strip[0]
		rect.position = strip[1].position
		rect.size = strip[1].size
		rect.color = strip[2]
	flash.color = Color(VsCardArtLayout.FLASH_COLOR, 0.0)
	visible = false
	set_physics_process(false)
	set_process_input(false)


func play(boss_key: String) -> void:
	if playing:
		return
	playing = true
	clock = 0.0
	_build(boss_key)
	_frame(0.0)
	visible = true
	set_physics_process(true)
	set_process_input(true)
	# Deferred: the player clears is_talking on the same dialogue_ended this is played from, and the
	# two handlers run in tree order. By the end of the frame the hold is the card's either way, and
	# the next frame's input hasn't been read yet.
	_hold_player.call_deferred(true)


func is_playing() -> bool:
	return playing


# Any press ends the card early. It jumps to the flash rather than vanishing, so the fight still
# starts behind a wipe instead of appearing mid-animation.
func skip() -> void:
	if not playing or clock >= VsCardArtLayout.HOLD_END:
		return
	clock = VsCardArtLayout.HOLD_END
	_frame(clock)


func _physics_process(delta: float) -> void:
	clock += delta
	_frame(clock)
	if clock >= VsCardArtLayout.CARD_END:
		_end()


func _input(event: InputEvent) -> void:
	if playing:
		if _is_press(event):
			InputSettings.note_device(event)
			get_viewport().set_input_as_handled()
			skip()
		return
	if _in_grace():
		_eat_grace_press(event)
		return
	set_process_input(false)


# The whole card as a function of its clock: every beat is read off `t`, so the same call draws the
# frame the accumulator asked for and the frame a skip jumped to.
func _frame(t: float) -> void:
	var art := VsCardArtLayout
	var drive := clampf(t / art.DRIVE_IN, 0.0, 1.0)
	var driven := _ease_out(drive)
	back.modulate.a = driven
	left_half.position.x = -art.DRIVE_OFFSET * (1.0 - driven)
	right_half.position.x = art.DRIVE_OFFSET * (1.0 - driven)

	var since_meet := t - art.DRIVE_IN
	seam_flash.visible = since_meet >= 0.0 and since_meet < art.SEAM_FLASH_HOLD + art.SEAM_FLASH_FADE
	if seam_flash.visible:
		seam_flash.modulate.a = clampf(1.0 - (since_meet - art.SEAM_FLASH_HOLD) / art.SEAM_FLASH_FADE, 0.0, 1.0)

	vs.visible = since_meet >= 0.0
	var drop := clampf(since_meet / (art.VS_LAND - art.DRIVE_IN), 0.0, 1.0)
	vs.scale = Vector2.ONE * lerpf(art.VS_FROM_SCALE, 1.0, _ease_out(drop))

	var since_land := t - art.VS_LAND
	burst.visible = since_land >= 0.0 and since_land < art.BURST_FADE
	if burst.visible:
		burst.modulate.a = 1.0 - since_land / art.BURST_FADE

	var written := clampf(since_land / (art.WRITING_IN - art.VS_LAND), 0.0, 1.0)
	writing.modulate.a = written
	var slide := art.SLIDE_IN * (1.0 - _ease_out(written))
	if name_art != null:
		name_art.position.x = name_home.x + slide
	if win_art != null:
		win_art.position.x = win_home.x + slide

	card.position = _knock(t)

	var lit := clampf((t - art.HOLD_END) / (art.FLASH_PEAK - art.HOLD_END), 0.0, 1.0)
	var faded := clampf((t - art.FLASH_PEAK) / (art.CARD_END - art.FLASH_PEAK), 0.0, 1.0)
	flash.color.a = lit * (1.0 - faded)
	# Under the white, so the card and the darkening can simply go: what is behind them is the fight.
	var covered := t >= art.FLASH_PEAK
	back.visible = not covered
	card.visible = not covered


# The knock the VS lands with, two physics frames a step. Read off the clock rather than counted in
# frames, so a skip past it lands on the settled offset.
func _knock(t: float) -> Vector2:
	var art := VsCardArtLayout
	if t < art.DRIVE_IN:
		return Vector2.ZERO
	var step_time := float(art.SLAM_SHAKE_FRAMES) / float(Engine.physics_ticks_per_second)
	var step := int((t - art.DRIVE_IN) / step_time)
	if step >= art.SLAM_SHAKE.size():
		return Vector2.ZERO
	return art.SLAM_SHAKE[step]


func _end() -> void:
	playing = false
	set_physics_process(false)
	visible = false
	grace_until_msec = Time.get_ticks_msec() + roundi(INPUT_GRACE * 1000.0)
	_hold_player(false)
	finished.emit()


#THE BUILD

func _build(boss_key: String) -> void:
	for child in card.get_children():
		card.remove_child(child)
		child.queue_free()
	name_art = null
	win_art = null
	var art := VsCardArtLayout
	var data := art.card(boss_key)

	left_half = Node2D.new()
	card.add_child(left_half)
	var left_art := art.frame_art("band_left")
	if left_art != null:
		left_half.add_child(_pixel_sprite(left_art, art.BAND_AT))
	else:
		_build_placeholder_half(left_half, art.Side.LEFT, art.PLACEHOLDER_PLAYER_RAMP,
			art.placeholder_player_bust(), art.PLACEHOLDER_PLAYER_BUST.at, art.PLACEHOLDER_PLAYER_BUST.scale)

	right_half = Node2D.new()
	card.add_child(right_half)
	var right_art := art.band_right(boss_key)
	if right_art != null:
		right_half.add_child(_pixel_sprite(right_art, art.BAND_AT))
	else:
		_build_placeholder_half(right_half, art.Side.RIGHT, data["ramp"],
			art.placeholder_bust(boss_key), art.PLACEHOLDER_BUST_AT, art.PLACEHOLDER_BUST_SCALE)

	# The rules run the whole width of the band, so they belong to neither half. The drawn halves
	# carry their own; only a card with a half still drawn in code needs them.
	if left_art == null or right_art == null:
		_build_rules()

	seam_flash = _build_seam_flash()
	card.add_child(seam_flash)

	writing = Node2D.new()
	card.add_child(writing)
	_build_writing(boss_key, data)

	burst = _build_burst()
	card.add_child(burst)

	vs = _build_vs()
	card.add_child(vs)


func _build_placeholder_half(host: Node2D, side: int, ramp: Array, bust: Texture2D, bust_at: Vector2, bust_scale: float) -> void:
	var art := VsCardArtLayout
	var block := Polygon2D.new()
	block.polygon = _scaled(art.half_points(side))
	block.vertex_colors = art.half_colors(ramp, side)
	block.position = art.BAND_AT
	host.add_child(block)
	if side == art.Side.RIGHT:
		for rule in art.PLACEHOLDER_SEAM:
			host.add_child(_seam_rule(rule[0], rule[1], rule[2]))
	if bust == null:
		return
	var sprite := Sprite2D.new()
	sprite.texture = bust
	sprite.centered = false
	sprite.scale = Vector2.ONE * bust_scale * art.ART_SCALE
	# Its bottom centre stands on bust_at, so art of any size hangs from the same spot.
	var size := bust.get_size() * bust_scale
	sprite.position = art.BAND_AT + (bust_at - Vector2(size.x * 0.5, size.y)) * art.ART_SCALE
	host.add_child(sprite)


func _build_rules() -> void:
	var art := VsCardArtLayout
	for rule in art.PLACEHOLDER_RULES:
		for edge in [rule[0], art.BAND_SIZE.y - rule[0] - rule[1]]:
			var bar := ColorRect.new()
			bar.color = rule[2]
			bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
			bar.position = art.BAND_AT + Vector2(0, edge) * art.ART_SCALE
			bar.size = Vector2(art.BAND_SIZE.x, rule[1]) * art.ART_SCALE
			card.add_child(bar)


func _build_seam_flash() -> Node2D:
	var art := VsCardArtLayout
	var drawn := art.frame_art("seam_flash")
	if drawn != null:
		return _pixel_sprite(drawn, art.BAND_AT)
	return _seam_rule(0.0, art.PLACEHOLDER_SEAM_FLASH_WIDTH * 2.0, art.FLASH_COLOR)


func _build_burst() -> Node2D:
	var art := VsCardArtLayout
	var drawn := art.frame_art("burst")
	if drawn != null:
		return _centred_sprite(drawn, art.VS_CENTRE)
	var spec: Dictionary = art.PLACEHOLDER_BURST
	var host := Node2D.new()
	host.position = art.VS_CENTRE
	var star := Polygon2D.new()
	star.polygon = art.burst_points()
	star.color = spec.color
	host.add_child(star)
	var ring := Line2D.new()
	var points := PackedVector2Array()
	for i in 33:
		var angle := TAU * float(i) / 32.0
		points.append(Vector2(cos(angle), sin(angle)) * spec.ring_radius)
	ring.points = points
	ring.width = spec.ring_width
	ring.default_color = spec.color
	host.add_child(ring)
	return host


func _build_vs() -> Node2D:
	var art := VsCardArtLayout
	var drawn := art.frame_art("vs")
	if drawn != null:
		return _centred_sprite(drawn, art.VS_CENTRE)
	var host := Node2D.new()
	host.position = art.VS_CENTRE
	var label := _label("VS", art.VS_FONT_SIZE, art.NAME_COLOR, Vector2.ZERO, HORIZONTAL_ALIGNMENT_CENTER)
	label.position = -label.size * 0.5
	host.add_child(label)
	return host


# The fight number and the epithet fade in where they are; the name and the WIN plate slide in from
# the right as well, so their homes are kept for _frame() to slide them back to.
func _build_writing(boss_key: String, data: Dictionary) -> void:
	var art := VsCardArtLayout

	var fight_art := art.fight_plate(boss_key)
	if fight_art != null:
		writing.add_child(_plate_sprite(fight_art, art.FIGHT_AT))
	elif int(data["number"]) > 0:
		writing.add_child(_label("FIGHT %02d" % int(data["number"]), art.LINE_FONT_SIZE,
			art.FIGHT_COLOR, art.FIGHT_AT, HORIZONTAL_ALIGNMENT_LEFT))

	var epithet_art := art.epithet_plate(boss_key)
	if epithet_art != null:
		writing.add_child(_plate_sprite(epithet_art, art.EPITHET_AT))
	elif data["epithet"] != "":
		writing.add_child(_label(data["epithet"], art.LINE_FONT_SIZE, art.EPITHET_COLOR,
			art.EPITHET_AT, HORIZONTAL_ALIGNMENT_LEFT))

	var name_plate := art.name_plate(boss_key)
	if name_plate != null:
		name_art = _plate_sprite(name_plate, _from_right(art.NAME_TOP_RIGHT, name_plate.get_width()))
	else:
		name_art = _label(data["name"], art.NAME_FONT_SIZE, art.NAME_COLOR,
			art.NAME_TOP_RIGHT, HORIZONTAL_ALIGNMENT_RIGHT)
	writing.add_child(name_art)
	name_home = name_art.position

	# The last fight hands over an invite rather than a rank, so it shows neither WIN nor a badge.
	var win_plate := art.win_plate(boss_key)
	if win_plate != null:
		win_art = _plate_sprite(win_plate, _from_right(art.WIN_TOP_RIGHT, win_plate.get_width()))
	elif data["rank"] != "":
		win_art = _label("WIN %s" % data["rank"], art.LINE_FONT_SIZE, art.WIN_COLOR,
			art.WIN_TOP_RIGHT, HORIZONTAL_ALIGNMENT_RIGHT)
	if win_art != null:
		writing.add_child(win_art)
		win_home = win_art.position

	var badge := art.badge_plate(boss_key)
	if badge != null:
		writing.add_child(_pixel_sprite(badge, art.BADGE_AT))
	elif data["rank"] != "":
		for piece in art.placeholder_badge(boss_key):
			writing.add_child(_pixel_sprite(piece, art.BADGE_AT))


#PIECES

# Pixel art, authored at 640x360 and drawn at the scale the rest of the game renders at.
func _pixel_sprite(texture: Texture2D, at: Vector2) -> Sprite2D:
	var sprite := Sprite2D.new()
	sprite.texture = texture
	sprite.centered = false
	sprite.scale = Vector2.ONE * VsCardArtLayout.ART_SCALE
	sprite.position = at
	return sprite


# Lettering, baked at screen resolution and drawn 1:1.
func _plate_sprite(texture: Texture2D, at: Vector2) -> Sprite2D:
	var sprite := Sprite2D.new()
	sprite.texture = texture
	sprite.centered = false
	sprite.position = at
	return sprite


func _centred_sprite(texture: Texture2D, at: Vector2) -> Sprite2D:
	var sprite := Sprite2D.new()
	sprite.texture = texture
	sprite.position = at
	return sprite


# A line parallel to the seam, `offset` texels along the band's top row from it.
func _seam_rule(offset: float, width: float, colour: Color) -> Line2D:
	var art := VsCardArtLayout
	var line := Line2D.new()
	line.points = _scaled(art.seam_line(offset))
	line.width = width * art.ART_SCALE
	line.default_color = colour
	line.position = art.BAND_AT
	return line


# Written text, while the plate that will replace it is still being drawn. The box is fixed and wide
# enough for any of the names, so a line can be right-aligned on its anchor without measuring it.
func _label(text: String, size: int, colour: Color, at: Vector2, align: int) -> Label:
	var art := VsCardArtLayout
	var label := Label.new()
	label.text = text
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	label.horizontal_alignment = align
	label.vertical_alignment = VERTICAL_ALIGNMENT_TOP
	label.add_theme_font_size_override("font_size", size)
	label.add_theme_color_override("font_color", colour)
	label.add_theme_color_override("font_shadow_color", art.NAME_SHADOW_COLOR)
	label.add_theme_constant_override("shadow_offset_x", 3)
	label.add_theme_constant_override("shadow_offset_y", 3)
	label.size = Vector2(art.LABEL_BOX_WIDTH, size * 1.5)
	label.position = at
	if align == HORIZONTAL_ALIGNMENT_RIGHT:
		label.position.x = at.x - art.LABEL_BOX_WIDTH
	return label


func _from_right(top_right: Vector2, width: float) -> Vector2:
	return Vector2(top_right.x - width, top_right.y)


func _scaled(points: PackedVector2Array) -> PackedVector2Array:
	var out := PackedVector2Array()
	for point in points:
		out.append(point * VsCardArtLayout.ART_SCALE)
	return out


func _ease_out(weight: float) -> float:
	return 1.0 - pow(1.0 - weight, 3.0)


#INPUT AND THE PLAYER

# Any press: a key, a pad button, a mouse button. Not a stick and not the mouse moving - a pad left
# resting off centre would skip the card before it was ever seen.
func _is_press(event: InputEvent) -> bool:
	if event is InputEventKey:
		return event.pressed and not event.echo
	if event is InputEventJoypadButton or event is InputEventMouseButton:
		return event.pressed
	return false


func _in_grace() -> bool:
	return Time.get_ticks_msec() < grace_until_msec


# Only presses: a guard or a direction held through the card has to carry straight on into the
# fight, and both of those are polled rather than read from the event.
func _eat_grace_press(event: InputEvent) -> void:
	for action in GRACE_ACTIONS:
		if event.is_action_pressed(action):
			InputSettings.note_device(event)
			get_viewport().set_input_as_handled()
			return


# The flag the pre-fight lines already hold the player with: it stops movement, punches, the guard
# and the dash alike, so the card simply keeps holding it.
func _hold_player(held: bool) -> void:
	var player := _player()
	if player != null:
		player.is_talking = held


func _player() -> Node:
	var arena := get_parent()
	return arena.get_node_or_null(^"MainPlayer/CharacterBody2D") if arena != null else null
