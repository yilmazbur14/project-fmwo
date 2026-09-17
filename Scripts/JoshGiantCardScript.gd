extends Node2D

# One of the three giant cards Josh lays over the arena. Each one covers exactly one third of the
# ropes: its art is drawn at a whole 3x centred on that third, and its hitbox is the third's own rect,
# so what is drawn and what hurts can never drift apart.
# Phase one: a laid card waits off the top of the screen with only its floor shadow marking its third,
# then slides down through its 1.4 s warning and slams - full height, full third, one at a time, and
# lies there afterwards while the next one comes down.
# Phase two: it lies flat on the floor instead, gets shuffled around with the others (slide_to) and is
# turned over at the end (flip_up).
# All of its timing runs on _physics_process accumulators, so a finisher's freeze holds it.

const JoshArtLayout := preload("res://Scripts/JoshArtLayout.gd")
const Arena := preload("res://Scripts/States/JoshCards/JoshCardsStateMachine.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")

signal slammed

enum Mode { AIRBORNE, FLAT }
enum Kind { SAFE, DRAIN, INVERT }
enum Phase { STILL, SHOW, SHOW_SETTLE, WARN, SLAM, SLIDE, FLIP, DISMISS }

# The slam, and how long the hitbox is live inside it.
const SLAM_TIME := 0.25
const SLAM_HIT_TIME := 0.2
# A card that has landed stays where it fell until the storm that dropped it is over, so the arena is
# carpeted in fallen cards by the third slam. It is scenery from the end of the slam: hitbox dead,
# drawn under the player, and dimmed so the bombs on top of it still read.
const LIE_DIM := 0.82
# The phase-two lay-in: how high the placeholder holds a card up, and how long its face takes to turn
# away once he lets go.
const SHOW_HEIGHT := 300.0
const SHOW_SCALE := 0.8
const FACE_SETTLE_TIME := 0.4
const SLAM_SHAKE := 14.0
const SLAM_SHAKE_STEPS := 5
const SLAM_SHAKE_STEP_TIME := 0.03
const SLAM_CHEER := 0.6
# A card on its way down is drawn over the ropes and over everyone; once it has landed it is scenery
# on the floor, under the player and under Josh. Its shadow always stays on the floor.
const FALLING_Z := 4
const FLOOR_Z := 0
# The lock-in glow, on the card's own brightness rather than its size, so it can't fight the drawn scale.
const PULSE_TIME := 0.3
const PULSE_GLOW := Color(1.5, 1.4, 1.1)

@export var shadow: Node2D
@export var card: Node2D
@export var hitbox: Area2D
@export var hitbox_shape: CollisionShape2D
@export var whistle_sfx: AudioStreamPlayer
@export var slam_sfx: AudioStreamPlayer

# Set by the state that lays it, before it enters the tree.
var hover_height := 900.0

var third := 0
var kind := Kind.SAFE
var mode := Mode.AIRBORNE
var face_up := false

var phase := Phase.STILL
var clock := 0.0
var duration := 0.0
var warn_pulse := 0.0

var height := 0.0
var draw_scale := 1.0
var flip_scale := 1.0
var shadow_alpha := 0.0
var shadow_base_alpha := 1.0

var slide_from := Vector2.ZERO
var slide_to_point := Vector2.ZERO
var slide_third := 0
var slide_arc := 0.0

# Final art.
var card_sprite: Sprite2D
var shadow_sprite: Sprite2D
var specials_sprite: Sprite2D
var reveal_sprite: Sprite2D
var card_rest := Vector2.ZERO
# Placeholder art.
var card_face: Polygon2D
var card_border: Polygon2D
var card_label: Label


func _ready() -> void:
	hitbox.set_meta(HitInfo.META_ATTACK, &"josh_card_fall")


# Puts the card over its third, face down, either waiting above the screen or lying on the floor.
func lay(at_third: int, at_mode: int, at_kind: int) -> void:
	third = at_third
	mode = at_mode
	kind = at_kind
	var rect := Arena.third_rect(third)
	global_position = rect.get_center().round()
	_build(rect.size)
	(hitbox_shape.shape as RectangleShape2D).size = rect.size
	# No shadow until this is the third that is coming down: three dark thirds would swallow the mat,
	# and the warning is what tells the player where the danger is.
	shadow_alpha = 0.0
	if mode == Mode.AIRBORNE:
		# Off the top of the screen: three of these hanging in view would hide the whole fight.
		height = hover_height
		draw_scale = JoshArtLayout.GIANT_CARD_HOVER_SCALE if not _final() else 1.0
		card.z_index = FALLING_Z
		if card_sprite:
			card_sprite.hide()
	else:
		height = 0.0
		draw_scale = 1.0
		card.z_index = FLOOR_Z
	_show_back()
	_place()


# Phase two: he holds it up face-out for `seconds`, then it flips face-down and settles onto the floor
# over FACE_SETTLE_TIME. Nothing else may happen to it until that is over.
func show_face(seconds: float) -> void:
	mode = Mode.FLAT
	phase = Phase.SHOW
	clock = 0.0
	duration = seconds
	# The final card already covers its whole third on the floor, so only its face turns over; the
	# placeholder is held up and lowered instead.
	height = 0.0 if _final() else SHOW_HEIGHT
	draw_scale = 1.0 if _final() else SHOW_SCALE
	shadow_alpha = 0.0
	_show_face()
	_place()


# The shuffle. Both cards in a swap run this at once, with opposite arcs.
func slide_to(to_third: int, arc: float, seconds: float) -> void:
	phase = Phase.SLIDE
	clock = 0.0
	duration = maxf(seconds, 0.01)
	slide_from = global_position
	slide_third = to_third
	slide_to_point = Arena.third_centre(to_third)
	slide_arc = arc


# Phase one: it drops into view, warns for `warning` seconds on the way down, then slams.
func drop(warning: float) -> void:
	phase = Phase.WARN
	clock = 0.0
	warn_pulse = 0.0
	duration = maxf(warning, 0.01)
	if card_sprite:
		card_sprite.show()
	if whistle_sfx:
		whistle_sfx.play()


# The reveal: the burst plays over the card and its face appears under it.
func flip_up(seconds: float) -> void:
	phase = Phase.FLIP
	clock = 0.0
	duration = maxf(seconds, 0.01)
	if reveal_sprite:
		reveal_sprite.frame = JoshArtLayout.FINAL_GIANT_CARD.reveal_frames[0]
		reveal_sprite.show()


# The monte's lock-in: the board holds still and glows while the player picks.
func pulse(seconds: float) -> void:
	var glowing: CanvasItem = card_sprite if card_sprite else card_border
	if glowing == null:
		return
	var beats := maxi(roundi(seconds / PULSE_TIME), 1)
	var beat := glowing.create_tween().set_loops(beats)
	beat.tween_property(glowing, "modulate", PULSE_GLOW, PULSE_TIME * 0.5)
	beat.tween_property(glowing, "modulate", Color(1, 1, 1), PULSE_TIME * 0.5)


func dismiss(seconds: float) -> void:
	phase = Phase.DISMISS
	clock = 0.0
	duration = maxf(seconds, 0.01)


func is_busy() -> bool:
	return phase != Phase.STILL


func _physics_process(delta: float) -> void:
	if phase == Phase.STILL:
		return
	clock += delta
	match phase:
		Phase.SHOW:
			_run_show()
		Phase.SHOW_SETTLE:
			_run_show_settle()
		Phase.WARN:
			_run_warn(delta)
		Phase.SLAM:
			_run_slam()
		Phase.SLIDE:
			_run_slide()
		Phase.FLIP:
			_run_flip()
		Phase.DISMISS:
			_run_dismiss()


func _run_show() -> void:
	if clock >= duration:
		phase = Phase.SHOW_SETTLE
		clock = 0.0
		duration = FACE_SETTLE_TIME


# He lets go: it turns face-down as it comes down, and lands flat over its third.
func _run_show_settle() -> void:
	var along := clampf(clock / duration, 0.0, 1.0)
	if not _final():
		height = lerpf(SHOW_HEIGHT, 0.0, along * along)
		draw_scale = lerpf(SHOW_SCALE, 1.0, along)
	flip_scale = absf(1.0 - 2.0 * along)
	if face_up and along >= 0.5:
		_show_back()
	if along >= 1.0:
		flip_scale = 1.0
		phase = Phase.STILL
	_place()


# It slides down into view while the floor under it throbs, the beat tightening as impact nears.
func _run_warn(delta: float) -> void:
	if clock >= duration:
		_slam()
		return
	var along := clampf(clock / duration, 0.0, 1.0)
	height = hover_height * (1.0 - along * along)
	if not _final():
		draw_scale = lerpf(JoshArtLayout.GIANT_CARD_HOVER_SCALE, 1.0, along * along)
	var left := 1.0 - along
	warn_pulse += delta / lerpf(JoshArtLayout.GIANT_CARD_PULSE_LAST, JoshArtLayout.GIANT_CARD_PULSE_FIRST, left)
	var throb: Array = JoshArtLayout.FINAL_GIANT_CARD.shadow_throb
	var beat: float = throb[1] if int(warn_pulse) % 2 == 0 else throb[0]
	# It fades in over the first moment of the warning, throbs, and is gone once the card has landed.
	shadow_alpha = shadow_base_alpha * beat * clampf(along / 0.15, 0.0, 1.0)
	_place()


func _slam() -> void:
	phase = Phase.SLAM
	clock = 0.0
	height = 0.0
	draw_scale = 1.0
	shadow_alpha = shadow_base_alpha
	_place()
	hitbox_shape.set_deferred("disabled", false)
	slammed.emit()
	if slam_sfx:
		slam_sfx.play()
	ScreenView.shake(get_tree(), SLAM_SHAKE, SLAM_SHAKE_STEPS, SLAM_SHAKE_STEP_TIME)
	get_tree().call_group("arena_crowd", "cheer", SLAM_CHEER)
	_impact()


func _run_slam() -> void:
	if clock >= SLAM_HIT_TIME and not hitbox_shape.disabled:
		hitbox_shape.set_deferred("disabled", true)
	if clock >= SLAM_TIME:
		phase = Phase.STILL
		clock = 0.0
		# Scenery from here: under the player, under Josh, no longer a hazard, and dimmed so the
		# bombs lying on top of it still read. The storm dismisses it when it ends.
		card.z_index = FLOOR_Z
		modulate = Color(LIE_DIM, LIE_DIM, LIE_DIM)
		shadow_alpha = 0.0
		_place()


func _run_slide() -> void:
	var along := clampf(clock / duration, 0.0, 1.0)
	var eased := along * along * (3.0 - 2.0 * along)
	global_position = (slide_from.lerp(slide_to_point, eased)
		- Vector2(0, slide_arc * sin(PI * along))).round()
	if along >= 1.0:
		third = slide_third
		global_position = slide_to_point.round()
		phase = Phase.STILL
		_show_back()
		_place()


# The burst is one overlay for every kind; the card's own face appears under it partway through.
func _run_flip() -> void:
	if reveal_sprite:
		var spec := JoshArtLayout.FINAL_GIANT_CARD
		var frames: Array = spec.reveal_frames
		var times: Array = spec.reveal_times
		var step := 0
		var end := 0.0
		for i in frames.size():
			end += times[i]
			step = i
			if clock < end:
				break
		reveal_sprite.frame = frames[step]
		if not face_up and frames[step] >= spec.reveal_swap_frame:
			_show_face()
		if clock >= end:
			reveal_sprite.hide()
	elif not face_up:
		flip_scale = absf(1.0 - 2.0 * clampf(clock / duration, 0.0, 1.0))
		if clock >= duration * 0.5:
			_show_face()
		_place()
	if clock >= duration:
		flip_scale = 1.0
		phase = Phase.STILL
		_place()


func _run_dismiss() -> void:
	modulate.a = clampf(1.0 - clock / duration, 0.0, 1.0)
	if clock >= duration:
		queue_free()


# The plume and the floor cracks the landing kicks up, lined up on the card's near edge.
func _impact() -> void:
	if JoshArtLayout.USE_FINAL_GIANT_IMPACT:
		var spec := JoshArtLayout.FINAL_GIANT_IMPACT
		var plume := Sprite2D.new()
		plume.texture = load(spec.texture)
		plume.hframes = spec.hframes
		plume.centered = false
		plume.scale = Vector2.ONE * spec.scale
		plume.position = card_rest + spec.offset
		add_child(plume)
		var play := plume.create_tween()
		for i in range(1, spec.hframes):
			play.tween_interval(spec.frame_times[i - 1])
			play.tween_callback(func() -> void: plume.frame = i)
		return

	var rect := Arena.third_rect(third)
	var spec := JoshArtLayout.PLACEHOLDER_GIANT_IMPACT
	var dust := Polygon2D.new()
	dust.polygon = JoshArtLayout.centred_rect(Vector2(rect.size.x, spec.height))
	dust.color = spec.color
	dust.position = Vector2(0, rect.size.y / 2.0)
	add_child(dust)
	var puff := dust.create_tween()
	puff.tween_property(dust, "scale", Vector2(1.0, 2.2), spec.time)
	puff.parallel().tween_property(dust, "modulate:a", 0.0, spec.time)
	puff.tween_callback(dust.queue_free)


func _place() -> void:
	card.position = Vector2(0, -roundf(height))
	if _final():
		# A third-sized card is never squashed: only its face badge turns over.
		card.scale = Vector2.ONE
		if specials_sprite:
			var badge: float = JoshArtLayout.FINAL_GIANT_CARD.specials_scale
			specials_sprite.scale = Vector2(badge * flip_scale, badge)
	else:
		card.scale = Vector2(draw_scale * flip_scale, draw_scale)
	shadow.modulate.a = shadow_alpha


func _final() -> bool:
	return JoshArtLayout.USE_FINAL_GIANT_CARD


func _build(size: Vector2) -> void:
	if _final():
		_build_final()
		return
	_build_placeholder(size)


# Both modes draw the same third-sized card, so the third the player is standing on is literally the
# card they can see. Phase one adds the floor shadow it falls out of; phase two adds the face badge.
func _build_final() -> void:
	var spec := JoshArtLayout.FINAL_GIANT_CARD
	shadow_base_alpha = spec.shadow_alpha
	var drawn: Vector2 = spec.frame_size * spec.scale
	card_rest = (-drawn / 2.0).round()

	if mode == Mode.AIRBORNE:
		shadow_sprite = Sprite2D.new()
		shadow_sprite.texture = load(spec.shadow)
		shadow_sprite.centered = false
		shadow_sprite.scale = Vector2.ONE * spec.scale
		shadow_sprite.position = card_rest
		shadow.add_child(shadow_sprite)

	card_sprite = Sprite2D.new()
	card_sprite.texture = load(spec.back)
	card_sprite.centered = false
	card_sprite.scale = Vector2.ONE * spec.scale
	card_sprite.position = card_rest
	card.add_child(card_sprite)
	if mode == Mode.AIRBORNE:
		return

	specials_sprite = _badge(spec)
	reveal_sprite = _badge(spec)
	reveal_sprite.hide()


func _badge(spec: Dictionary) -> Sprite2D:
	var badge := Sprite2D.new()
	badge.texture = load(spec.specials)
	badge.hframes = spec.specials_hframes
	badge.vframes = spec.specials_vframes
	badge.scale = Vector2.ONE * spec.specials_scale
	card.add_child(badge)
	return badge


func _build_placeholder(size: Vector2) -> void:
	var spec := JoshArtLayout.PLACEHOLDER_GIANT_CARD
	shadow_base_alpha = JoshArtLayout.GIANT_CARD_SHADOW_ALPHA

	var floor_mark := Polygon2D.new()
	floor_mark.polygon = JoshArtLayout.centred_rect(size)
	floor_mark.color = JoshArtLayout.GIANT_CARD_SHADOW_COLOR
	shadow.add_child(floor_mark)

	card_border = Polygon2D.new()
	card_border.polygon = JoshArtLayout.centred_rect(size)
	card_border.color = spec.border_color
	card.add_child(card_border)

	card_face = Polygon2D.new()
	card_face.polygon = JoshArtLayout.centred_rect(size - Vector2.ONE * spec.border * 2.0)
	card_face.color = spec.back_color
	card.add_child(card_face)

	card_label = Label.new()
	card_label.theme = load("res://Assets/UI/ui_theme.tres")
	card_label.add_theme_font_size_override("font_size", spec.label_font_size)
	card_label.add_theme_color_override("font_color", spec.label_color)
	card_label.add_theme_color_override("font_outline_color", Color(0, 0, 0))
	card_label.add_theme_constant_override("outline_size", spec.label_outline)
	card_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	card_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	card_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	card_label.size = size
	card_label.position = -size / 2.0
	card.add_child(card_label)


func _show_back() -> void:
	face_up = false
	if specials_sprite:
		specials_sprite.frame = JoshArtLayout.FINAL_GIANT_CARD.back_frame
		# The card art is already a back: the badge only shows when there is a face to show.
		specials_sprite.hide()
	if card_face:
		card_face.color = JoshArtLayout.PLACEHOLDER_GIANT_CARD.back_color
	if card_label:
		card_label.text = ""


func _show_face() -> void:
	face_up = true
	if specials_sprite:
		specials_sprite.frame = kind
		specials_sprite.show()
	if card_face:
		card_face.color = JoshArtLayout.PLACEHOLDER_GIANT_CARD.face_colors[kind]
	if card_label:
		card_label.text = JoshArtLayout.PLACEHOLDER_GIANT_CARD.face_labels[kind]
