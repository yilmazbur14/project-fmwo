extends Node2D

# The mark on the floor under the hand that is coming down in Josh's Hand Slam (JoshCardsHandSlam), DannyBossSlamMark's
# shape: josh_hand_mark.png (JoshHandsLayout.MARK) once it is in, or until then a rim that is exactly the footprint -
# the hit area, to the pixel - and a shadow inside it that grows as the hand comes down. While the hand tracks, its
# two smallest frames flicker; as it drops, how high the hand is picks the frame; landed, the last. It knows nothing
# of the hand: the attack places it and pushes the height in every step (hover() or set_height()), and the flicker
# and the fade-in run on its own physics clock, so a freeze or the pause screen holds them. It lies on the fight's
# floor layer, in the hazard group, and whoever made it frees it.

const Layout := preload("res://Scripts/JoshHandsLayout.gd")

# The lift the frames are measured against: the hand's hover height.
var full_height := 210.0
var hovering := false
var landed := false
var hover_clock := 0.0
var fade_time := 0.0
var fade_clock := 0.0
# The frame showing, the drawn mark's or the one the placeholder stands in for.
var frame := 0
var drawn := false
var sprite: Sprite2D
var rim: Line2D
var fill: Polygon2D


# Built here rather than in _ready, so the attack can set it up before adding it.
func _init() -> void:
	drawn = Layout.final_mark()
	if drawn:
		var spec: Dictionary = Layout.MARK
		sprite = Sprite2D.new()
		sprite.texture = load(spec.texture)
		sprite.hframes = spec.frames
		sprite.offset = spec.frame / 2.0 - spec.pivot
		sprite.scale = Vector2.ONE * Layout.SCALE
		add_child(sprite)
	else:
		var look: Dictionary = Layout.PLACEHOLDER_MARK
		var colours: Dictionary = Layout.PLACEHOLDER
		fill = Polygon2D.new()
		fill.name = "Shadow"
		fill.polygon = _ellipse(Layout.FOOTPRINT, look.points)
		fill.color = colours.mark_fill
		add_child(fill)
		rim = Line2D.new()
		rim.name = "Rim"
		rim.points = _ellipse(Layout.FOOTPRINT, look.points)
		rim.closed = true
		rim.width = look.rim_width
		rim.default_color = colours.mark_rim
		add_child(rim)
	set_height(full_height)


# It comes up from nothing over `seconds`.
func fade_in(seconds: float) -> void:
	fade_time = seconds
	fade_clock = 0.0
	modulate.a = 0.0


# The hand is tracking or locked. A mark already flickering carries on where it was.
func hover() -> void:
	if hovering:
		return
	hovering = true
	landed = false
	hover_clock = 0.0
	_show(Layout.MARK.hover_frames[0], 0.0)


# The hand is `px` over the floor, dropping or rising.
func set_height(px: float) -> void:
	hovering = false
	landed = false
	var shown: int = Layout.MARK.land_frame
	for step in Layout.MARK.height_frames:
		if px > step[0] * full_height:
			shown = step[1]
			break
	_show(shown, clampf(1.0 - px / full_height, 0.0, 1.0))


func land() -> void:
	hovering = false
	landed = true
	_show(Layout.MARK.land_frame, 1.0)


func _physics_process(delta: float) -> void:
	if fade_time > 0.0 and fade_clock < fade_time:
		fade_clock += delta
		modulate.a = clampf(fade_clock / fade_time, 0.0, 1.0)
	if not hovering:
		return
	hover_clock += delta
	var frames: Array = Layout.MARK.hover_frames
	var step := int(hover_clock / Layout.MARK.frame_time) % frames.size()
	_show(frames[step], 0.0)


# `down` is how far down the hand has come, 0 at its hover to 1 landed: the placeholder's shadow grows with it, and
# its rim flickers on the second hover frame.
func _show(shown: int, down: float) -> void:
	frame = shown
	if drawn:
		sprite.frame = shown
		return
	var look: Dictionary = Layout.PLACEHOLDER_MARK
	fill.scale = Vector2.ONE * lerpf(look.fill_from, 1.0, down)
	rim.modulate.a = look.flicker_alpha if shown == Layout.MARK.hover_frames[-1] and hovering else 1.0


func _ellipse(radii: Vector2, points: int) -> PackedVector2Array:
	var out := PackedVector2Array()
	for i in points:
		out.append(Vector2.from_angle(TAU * i / points) * radii)
	return out
