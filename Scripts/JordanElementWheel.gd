extends Node2D

# The Elemental Wheel behind Liam in Jordan's attack 5 (JordanComboWheel; every number JordanWheelLayout's): the disc,
# its pointer on the top-right diagonal and the second one on the bottom-right that unfolds for a double, the lit stop,
# and the icon that pops over Liam's head. Its node is the hub, on the Floor layer one z over the floor's own pieces, so
# it stays under the strings: Liam's run over it to his back.
#
# The attack drives it, a physics step at a time (advance), so a pause and a finisher's freeze hold it. A spin runs
# JordanWheelLayout.spin_plan: `ticked` each time a peg passes the pointer, `stopped` as it lands on its quarter turn.
#
# DRAWN: the disc's sub-angle frames, each turned a quarter in code, at one of STEPS_PER_TURN positions; the lit sheet
# at the stop, turned the same quarter; the blur over it while it spins fast; the pointer art; the icons. STAND-IN
# until each is in: a disc of four coloured quadrants on the diagonals, lettered, turned smoothly; triangles for the
# pointers; coloured discs for the icons; a fade and a scale for the forming and the shatter.

const Layout := preload("res://Scripts/JordanWheelLayout.gd")
const UI_THEME := preload("res://Assets/UI/ui_theme.tres")

signal ticked
signal stopped

# Set before it enters the tree: where the icons go, and the point they pop over.
var icon_layer: Node2D
var icon_anchor := Callable()

var rotation_deg := 0.0
var plan := {}
var spin_clock := 0.0
var spinning := false
var omega := 0.0
var last_ticks := 0
var bump_left := 0.0
var double_on := false
var unfold := 0.0
# The element(s) lit at the stop, and how long they have been.
var lit: Array = []
var lit_clock := 0.0
var forming := false
var form_clock := 0.0
var shattering := false
var shatter_clock := 0.0
var drawn := false

var disc: Node2D
var disc_sheet: Sprite2D
var lit_sheet: Sprite2D
var blur_sheet: Sprite2D
var wedges := {}
var pointer_pivots: Array[Node2D] = []
var pointers: Array[Node2D] = []
var effect_sheet: Sprite2D
var icons: Node2D
var icon_clock := 0.0
var icons_fading := false
var icon_fade_clock := 0.0
var icon_parts: Array = []
var textures := {}


func _ready() -> void:
	drawn = Layout.final_wheel()
	if drawn:
		_build_drawn()
	else:
		_build_placeholder()
	for i in 2:
		var pivot := Node2D.new()
		pivot.name = "PointerPivot%d" % i
		pivot.rotation_degrees = 0.0 if i == 0 else Layout.SECOND_POINTER_ANGLE - Layout.POINTER_ANGLE
		add_child(pivot)
		var pointer := _build_pointer()
		pivot.add_child(pointer)
		pointer_pivots.append(pivot)
		pointers.append(pointer)
	pointer_pivots[1].visible = false
	_show()


#WHAT THE ATTACK CALLS

# Drawn in from nothing over FORM_TIME after `delay`.
func form(delay := Layout.FORM_DELAY) -> void:
	forming = true
	form_clock = -delay
	modulate.a = 0.0
	_show_form()


# Spin `k` (0 to 2) to `target`'s stop.
func begin_spin(k: int, target: int) -> Dictionary:
	unlight()
	plan = Layout.spin_plan(k, rotation_deg, target)
	spin_clock = 0.0
	spinning = true
	last_ticks = Layout.ticks_at(rotation_deg)
	return plan


# The second pointer unfolds over UNFOLD_FRAMES steps of the spin-up, or folds away.
func show_double(on: bool) -> void:
	double_on = on
	if not on:
		unfold = 0.0
	pointer_pivots[1].visible = on and unfold > 0.0


# The stop: `elements` lit (the primary, then its neighbour on a double), the pointers lit.
func light(elements: Array) -> void:
	lit = elements.duplicate()
	lit_clock = 0.0
	_show()


func unlight() -> void:
	lit.clear()
	_show()


func position_now() -> int:
	return Layout.position_of(rotation_deg)


# The element under the pointer, and under the second.
func element_under(second := false) -> int:
	return Layout.element_under(rotation_deg, Layout.SECOND_POINTER_ANGLE if second else Layout.POINTER_ANGLE)


# The icons pop over Liam's head: the primary, and on a double a "+" and its neighbour, smaller.
func badge(elements: Array) -> void:
	clear_badge(true)
	if icon_layer == null:
		return
	icons = Node2D.new()
	icons.name = "WheelIcons"
	icons.add_to_group(Layout.GodLayout.HAZARD_GROUP)
	icon_layer.add_child(icons)
	icon_clock = 0.0
	icons_fading = false
	icon_parts.clear()
	if elements.size() == 1:
		icon_parts.append(_icon(elements[0], Vector2.ZERO, 1.0))
	else:
		icon_parts.append(_icon(elements[0], Vector2(-Layout.ICON_PAIR_X, 0), 1.0))
		icons.add_child(_plus())
		icon_parts.append(_icon(elements[1], Vector2(Layout.ICON_PAIR_X, 0), Layout.ICON_SECOND_SCALE))
	_place_icons()


# The icons fade out over ICON_FADE (or go at once).
func clear_badge(now := false) -> void:
	if not is_instance_valid(icons):
		return
	if now:
		icons.queue_free()
		icons = null
		return
	if not icons_fading:
		icons_fading = true
		icon_fade_clock = 0.0


func badge_up() -> bool:
	return is_instance_valid(icons) and not icons_fading


func shatter() -> void:
	shattering = true
	shatter_clock = 0.0
	spinning = false
	clear_badge()
	if Layout.final_shatter():
		_play_effect(Layout.SHATTER_SHEET)


# One physics step.
func advance(delta: float) -> void:
	if forming:
		form_clock += delta
		_show_form()
	if shattering:
		shatter_clock += delta
		_show_shatter()
		return
	if spinning:
		spin_clock += delta
		rotation_deg = Layout.spin_rotation(plan, spin_clock)
		omega = Layout.spin_omega(plan, spin_clock)
		var ticks := Layout.ticks_at(rotation_deg)
		if ticks != last_ticks:
			last_ticks = ticks
			bump_left = Layout.POINTER_BUMP
			ticked.emit()
		if double_on and unfold < 1.0:
			unfold = minf(1.0, spin_clock / Layout.SPIN_UP)
			pointer_pivots[1].visible = unfold > 0.0
		if spin_clock >= plan.time - 0.0001:
			spinning = false
			omega = 0.0
			rotation_deg = fposmod(float(plan.to), 360.0)
			stopped.emit()
	else:
		omega = 0.0
	if bump_left > 0.0:
		bump_left -= delta
	if not lit.is_empty():
		lit_clock += delta
	_step_icons(delta)
	_show()


#DRAWING IT

func _show() -> void:
	if disc == null:
		return
	var showing_lit := not lit.is_empty() and not spinning
	if drawn:
		var p := Layout.position_of(rotation_deg)
		disc_sheet.frame = p % mini(Layout.SUB_FRAMES, disc_sheet.hframes)
		disc_sheet.rotation_degrees = float(p / Layout.SUB_FRAMES) * 90.0
		disc_sheet.visible = not showing_lit
		if is_instance_valid(blur_sheet):
			var phases := roundi(360.0 / Layout.BLUR_STEP)
			var b := posmod(roundi(rotation_deg / Layout.BLUR_STEP), phases)
			var per_quarter := roundi(90.0 / Layout.BLUR_STEP)
			blur_sheet.visible = spinning and omega > Layout.BLUR_OMEGA
			blur_sheet.frame = b % mini(per_quarter, blur_sheet.hframes)
			blur_sheet.rotation_degrees = float(b / per_quarter) * 90.0
		lit_sheet.visible = showing_lit
		if showing_lit:
			lit_sheet.frame = _lit_frame()
			lit_sheet.rotation_degrees = roundf(rotation_deg / 90.0) * 90.0
	else:
		disc.rotation_degrees = rotation_deg
		for element: int in wedges:
			var wedge: Polygon2D = wedges[element]
			wedge.modulate = _wedge_light(element) if showing_lit and lit.has(element) else Color.WHITE
	var unfolded := 0.4 + 0.6 * float(ceili(unfold * Layout.UNFOLD_FRAMES)) / Layout.UNFOLD_FRAMES
	for i in pointers.size():
		_show_pointer(pointers[i], showing_lit and (i == 0 or lit.size() > 1), unfolded if i == 1 else 1.0)


func _lit_frame() -> int:
	if lit.size() > 1:
		for i in Layout.DOUBLES.size():
			if Layout.DOUBLES[i][0] == lit[0] and Layout.DOUBLES[i][1] == lit[1]:
				return Layout.LIT_DOUBLE_FRAMES[i]
	return Layout.LIT_FRAMES[lit[0]]


# The stop's flash on a lit quadrant: white, white-gold, then the lit pulse.
func _wedge_light(_element: int) -> Color:
	var look: Dictionary = Layout.PLACEHOLDER_WHEEL
	var times: Array = Layout.FLASH_TIMES
	if lit_clock < times[0]:
		return look.flash
	if lit_clock < times[0] + times[1]:
		return look.flash_gold
	var on := int((lit_clock - times[0] - times[1]) / Layout.LIT_PULSE) % 2 == 0
	return look.lit if on else look.lit.lerp(Color.WHITE, 0.4)


# Its origin is its tip, so it bumps and unfolds about the rim.
func _show_pointer(pointer: Node2D, lit_now: bool, unfolded: float) -> void:
	var bumped := bump_left > 0.0
	if pointer is Sprite2D:
		(pointer as Sprite2D).frame = 2 if lit_now else (1 if bumped else 0)
		pointer.scale = Vector2.ONE * Layout.WHEEL_SCALE * unfolded
		return
	var look: Dictionary = Layout.PLACEHOLDER_POINTER
	var body: Polygon2D = pointer.get_child(0)
	body.color = look.lit if lit_now else look.colour
	pointer.scale = Vector2.ONE * (look.bump if bumped else 1.0) * unfolded


func _show_form() -> void:
	var t := clampf(form_clock / Layout.FORM_TIME, 0.0, 1.0)
	if form_clock >= Layout.FORM_TIME:
		forming = false
		modulate.a = 1.0
		scale = Vector2.ONE
		if is_instance_valid(effect_sheet):
			effect_sheet.queue_free()
			_hide_disc(false)
		return
	if Layout.final_form():
		modulate.a = 1.0 if form_clock >= 0.0 else 0.0
		if form_clock >= 0.0 and not is_instance_valid(effect_sheet):
			_play_effect(Layout.FORM_SHEET)
		if is_instance_valid(effect_sheet):
			effect_sheet.frame = mini(int(t * effect_sheet.hframes), effect_sheet.hframes - 1)
			_hide_disc(t < 1.0)
		return
	modulate.a = t
	scale = Vector2.ONE * lerpf(0.9, 1.0, t)


func _show_shatter() -> void:
	var t := clampf(shatter_clock / Layout.SHATTER_TIME, 0.0, 1.0)
	if is_instance_valid(effect_sheet):
		effect_sheet.frame = mini(int(t * effect_sheet.hframes), effect_sheet.hframes - 1)
		_hide_disc(true)
	else:
		modulate.a = 1.0 - t
		scale = Vector2.ONE * lerpf(1.0, Layout.SHATTER_SCALE, t)
	if t >= 1.0:
		visible = false


func _hide_disc(hidden: bool) -> void:
	disc.visible = not hidden
	for pivot in pointer_pivots:
		pivot.modulate.a = 0.0 if hidden else 1.0


func _play_effect(path: String) -> void:
	if is_instance_valid(effect_sheet):
		effect_sheet.queue_free()
	var texture := _texture(path)
	effect_sheet = Sprite2D.new()
	effect_sheet.name = "WheelEffect"
	effect_sheet.texture = texture
	effect_sheet.hframes = maxi(roundi(texture.get_width() / float(texture.get_height())), 1)
	effect_sheet.scale = Vector2.ONE * Layout.WHEEL_SCALE
	add_child(effect_sheet)


#THE ICONS

func _step_icons(delta: float) -> void:
	if not is_instance_valid(icons):
		return
	icon_clock += delta
	if icons_fading:
		icon_fade_clock += delta
		icons.modulate.a = 1.0 - clampf(icon_fade_clock / Layout.ICON_FADE, 0.0, 1.0)
		if icon_fade_clock >= Layout.ICON_FADE:
			icons.queue_free()
			icons = null
			return
	var pop := clampf(icon_clock / Layout.ICON_POP, 0.0, 1.0)
	icons.scale = Vector2.ONE * lerpf(Layout.ICON_POP_FROM, 1.0, pop)
	for part in icon_parts:
		if part is Sprite2D and part.has_meta(&"frames"):
			var frames: Array = part.get_meta(&"frames")
			part.frame = frames[0] if pop < 1.0 else frames[1]
	_place_icons()


func _place_icons() -> void:
	if is_instance_valid(icons) and icon_anchor.is_valid():
		icons.global_position = Vector2(icon_anchor.call()).round()


func _icon(element: int, at: Vector2, size: float) -> Node2D:
	var icon: Node2D
	if Layout.final_icons():
		var sheet := Sprite2D.new()
		sheet.texture = _texture(Layout.ICONS_SHEET)
		sheet.hframes = maxi(roundi(sheet.texture.get_width() / Layout.ICON_FRAME.x), 1)
		sheet.scale = Vector2.ONE * Layout.ICON_SCALE * size
		sheet.set_meta(&"frames", Layout.ICON_FRAMES[element])
		sheet.frame = Layout.ICON_FRAMES[element][0]
		icon = sheet
	else:
		var look: Dictionary = Layout.PLACEHOLDER_ICON
		var wheel_look: Dictionary = Layout.PLACEHOLDER_WHEEL
		icon = Node2D.new()
		icon.scale = Vector2.ONE * size
		var face := Polygon2D.new()
		face.polygon = _circle(look.radius, 24)
		face.color = wheel_look.colours[element]
		icon.add_child(face)
		var ring := Line2D.new()
		ring.points = _circle(look.radius, 24)
		ring.closed = true
		ring.width = look.ring_width
		ring.default_color = look.ring
		icon.add_child(ring)
		icon.add_child(_letter(wheel_look.letters[element], look.font_size, wheel_look.letter_colour))
	icon.name = "Icon_%s" % Layout.NAMES[element]
	icon.position = at
	icons.add_child(icon)
	return icon


func _plus() -> Node2D:
	var look: Dictionary = Layout.PLACEHOLDER_ICON
	var holder := _letter("+", look.font_size, look.plus_colour)
	holder.name = "Plus"
	return holder


#BUILDING IT

func _build_drawn() -> void:
	disc = Node2D.new()
	disc.name = "Disc"
	add_child(disc)
	disc_sheet = _sheet(Layout.WHEEL_SHEET)
	disc.add_child(disc_sheet)
	if Layout.final_blur():
		blur_sheet = _sheet(Layout.BLUR_SHEET)
		blur_sheet.visible = false
		disc.add_child(blur_sheet)
	lit_sheet = _sheet(Layout.LIT_SHEET)
	lit_sheet.visible = false
	disc.add_child(lit_sheet)


# Square frames on the hub, the centre corner on it (a quarter turn about it is pixel-exact).
func _sheet(path: String) -> Sprite2D:
	var texture := _texture(path)
	var sprite := Sprite2D.new()
	sprite.texture = texture
	sprite.hframes = maxi(roundi(texture.get_width() / Layout.WHEEL_FRAME.x), 1)
	sprite.scale = Vector2.ONE * Layout.WHEEL_SCALE
	return sprite


func _build_placeholder() -> void:
	var look: Dictionary = Layout.PLACEHOLDER_WHEEL
	var radius := Layout.WHEEL_RADIUS * Layout.WHEEL_SCALE
	disc = Node2D.new()
	disc.name = "Disc"
	add_child(disc)
	for element: int in Layout.CLOCKWISE:
		var middle: float = Layout.ELEMENT_ANGLE[element]
		var wedge := Polygon2D.new()
		wedge.name = "Wedge_%s" % Layout.NAMES[element]
		var points := PackedVector2Array([Vector2.ZERO])
		var steps := 12
		for i in steps + 1:
			points.append(_on_rim(middle - 45.0 + 90.0 * i / steps, radius))
		wedge.polygon = points
		wedge.color = look.colours[element]
		disc.add_child(wedge)
		wedges[element] = wedge
		var letter := _letter(look.letters[element], look.font_size, look.letter_colour)
		letter.position = _on_rim(middle, Layout.ICON_RADIUS * Layout.WHEEL_SCALE)
		disc.add_child(letter)
	for axis in 2:
		var spoke := Line2D.new()
		spoke.points = PackedVector2Array([_on_rim(axis * 90.0, radius), _on_rim(axis * 90.0 + 180.0, radius)])
		spoke.width = look.spoke_width
		spoke.default_color = look.spoke
		disc.add_child(spoke)
	var rim := Line2D.new()
	rim.points = _circle(radius - look.rim_width / 2.0, look.points)
	rim.closed = true
	rim.width = look.rim_width
	rim.default_color = look.rim
	disc.add_child(rim)
	for peg in 4:
		var stud := Polygon2D.new()
		stud.polygon = _circle(look.rim_width * 0.45, 10)
		stud.position = _on_rim(peg * 90.0, radius - look.rim_width / 2.0)
		stud.color = look.hub
		disc.add_child(stud)
	var hub := Polygon2D.new()
	hub.polygon = _circle(Layout.WHEEL_HUB_RADIUS * Layout.WHEEL_SCALE, 24)
	hub.color = look.hub
	disc.add_child(hub)


# The pointer on the top-right diagonal: the drawn one in place round the hub (its own origin there, so it unfolds about
# the hub), the stand-in's tip on the rim pointing in at the hub.
func _build_pointer() -> Node2D:
	var tip := _on_rim(Layout.POINTER_ANGLE, Layout.WHEEL_RADIUS * Layout.WHEEL_SCALE)
	if Layout.final_pointer():
		var sheet := Sprite2D.new()
		sheet.texture = _texture(Layout.POINTER_SHEET)
		sheet.hframes = maxi(roundi(sheet.texture.get_width() / Layout.POINTER_FRAME.x), 1)
		sheet.centered = false
		sheet.offset = -Layout.POINTER_HUB
		sheet.scale = Vector2.ONE * Layout.WHEEL_SCALE
		return sheet
	var look: Dictionary = Layout.PLACEHOLDER_POINTER
	var pointer := Node2D.new()
	pointer.position = tip.round()
	pointer.rotation_degrees = Layout.POINTER_ANGLE
	var size: Vector2 = look.size
	var body := Polygon2D.new()
	body.polygon = PackedVector2Array([Vector2(0, 0), Vector2(-size.x / 2.0, -size.y), Vector2(size.x / 2.0, -size.y)])
	body.color = look.colour
	pointer.add_child(body)
	var edge := Line2D.new()
	edge.points = body.polygon
	edge.closed = true
	edge.width = 4.0
	edge.default_color = look.edge
	pointer.add_child(edge)
	return pointer


func _letter(text: String, font_size: int, colour: Color) -> Node2D:
	var holder := Node2D.new()
	var label := Label.new()
	label.theme = UI_THEME
	label.text = text
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", colour)
	label.size = Vector2(font_size * 2, font_size * 2)
	label.position = -label.size / 2.0
	holder.add_child(label)
	return holder


# A point `radius` out from the hub at `degrees` clockwise from twelve o'clock.
static func _on_rim(degrees: float, radius: float) -> Vector2:
	var a := deg_to_rad(degrees)
	return Vector2(sin(a), -cos(a)) * radius


static func _circle(radius: float, points: int) -> PackedVector2Array:
	var out := PackedVector2Array()
	for i in points:
		out.append(Vector2.from_angle(TAU * i / points) * radius)
	return out


func _texture(path: String) -> Texture2D:
	if not textures.has(path):
		textures[path] = load(path)
	return textures[path]
