extends Node2D

# One of Josh's card-gate portals in his own fight, of either kind:
#   gate   one of his two big gates (JoshHandsRig builds the pair), opened by his Summon and there for the rest of the
#          fight, at JoshHandsLayout.PORTAL_POINTS. A backdrop, never a hazard: the node sits on the y-sort point
#          every big gate shares (PORTAL_SORT_Y) and its Draw child is put down at the pivot, mirrored for the left.
#   small  one of the three his Portal Monte deals round the player (JoshCardsPortalMonte), a hazard, its node on the
#          floor point it sorts on and its Draw child JoshMonteLayout.SMALL_FLOOR_DROP over it, upright and never
#          mirrored; its sheets and numbers are JoshMonteLayout's.
# It plays on game time, a physics step at a time: open() into its loop, feed() as a card goes in (a big gate), burst()
# as a figure comes out (a small one), close(), and it is gone.
#
# The drawn one (once every required sheet is in and imported, JoshHandsLayout.final_portal or
# JoshMonteLayout.final_small_portal): back and an additive glow, synced. Until then the placeholder: the opening filled
# with the vortex, a rim, an added glow round it and his cream cards circling it, grown in and shrunk away on physics
# tweens bound to the node.

const Layout := preload("res://Scripts/JoshHandsLayout.gd")
const Monte := preload("res://Scripts/JoshMonteLayout.gd")

var side := &"right"
var kind := &"gate"
var drawn := false
var art: Node2D
var sprites := {}
var sequence := &""
var step := 0
var clock := 0.0
var speed := 1.0
var closing := false
var rim: Line2D
var glow: Polygon2D
var flecks: Array[Polygon2D] = []
var fleck_clock := 0.0
var grow: Tween
var flare: Tween


# A small one is put on its floor point by whoever adds it.
static func make(portal_side: StringName, portal_kind := &"gate") -> Node2D:
	var portal = new()
	portal.side = portal_side
	portal.kind = portal_kind
	if portal_kind == &"small":
		portal.name = "JoshSmallPortal"
		return portal
	portal.name = "JoshPortal_%s" % portal_side
	var pivot: Vector2 = Layout.PORTAL_POINTS[portal_side]
	portal.position = Vector2(pivot.x, Layout.PORTAL_SORT_Y)
	return portal


func _ready() -> void:
	art = Node2D.new()
	art.name = "Draw"
	if _small():
		art.position = Vector2(0.0, -Monte.small_drop())
	else:
		var pivot: Vector2 = Layout.PORTAL_POINTS[side]
		art.position = Vector2(0.0, pivot.y - Layout.PORTAL_SORT_Y)
	add_child(art)
	drawn = Monte.final_small_portal() if _small() else Layout.final_portal()
	if drawn:
		_build_drawn()
	else:
		_build_placeholder()
	_set_grown(_placeholder().grown_from if not drawn else 1.0)
	visible = false


# Open, then its loop, at `at_speed`. The seconds the opening takes.
func open(at_speed := 1.0) -> float:
	closing = false
	visible = true
	_play(&"open")
	speed = at_speed
	var seconds := _sequence_time(&"open") / speed
	if not drawn:
		_grow_in(seconds)
	return seconds


# Straight to its loop, fully open: where a summon cut short leaves it.
func loop_now() -> void:
	if closing:
		return
	visible = true
	_play(&"loop")
	if not drawn:
		_kill(grow)
		_set_grown(1.0)
		modulate.a = 1.0


# A card of the flurry going in: the feed sequence if it is drawn, else the rim and the glow flare.
func feed() -> void:
	if closing or sequence == &"":
		return
	if drawn:
		if Layout.has_feed() and sequence == &"loop":
			_play(&"feed")
		return
	_flare()


# A figure bursting out of a small one: its burst sequence, back into its loop, if it is drawn, else the flare.
func burst() -> void:
	if closing or sequence == &"":
		return
	if drawn:
		_play(&"burst")
		return
	_flare()


# Played out and gone. The seconds that takes.
func close() -> float:
	if closing:
		return _left()
	closing = true
	visible = true
	_play(&"close")
	var seconds := _sequence_time(&"close")
	if not drawn:
		_shrink_away(seconds)
	return seconds


# The centre of its opening, where it stands in the world.
func pivot_point() -> Vector2:
	return art.global_position


func _physics_process(delta: float) -> void:
	if not drawn:
		_turn_flecks(delta)
	if sequence == &"":
		return
	var times: Array = _sequences()[sequence]
	clock += delta * speed
	while clock >= float(times[step]):
		clock -= float(times[step])
		if step < times.size() - 1:
			step += 1
		elif sequence == &"close":
			queue_free()
			return
		elif sequence == &"loop":
			step = 0
		else:
			var carry := clock
			_play(&"loop")
			clock = carry
			return
		_show_step()


func _play(next: StringName) -> void:
	sequence = next
	step = 0
	clock = 0.0
	speed = 1.0
	if not drawn:
		return
	var frames: int = _sequences()[next].size()
	for layer in _layers():
		var sheet: Sprite2D = sprites[layer]
		sheet.frame = 0
		sheet.texture = load(_sheet(next, layer))
		sheet.hframes = frames
	_show_step()


func _show_step() -> void:
	if not drawn:
		return
	for layer in _layers():
		sprites[layer].frame = step


# What is left of the sequence playing, in seconds.
func _left() -> float:
	var times: Array = _sequences().get(sequence, [])
	if times.is_empty():
		return 0.0
	var left := maxf(float(times[step]) - clock, 0.0)
	for i in range(step + 1, times.size()):
		left += float(times[i])
	return left / speed


#ITS KIND

func _small() -> bool:
	return kind == &"small"


func _shape() -> Dictionary:
	return Monte.SMALL_PORTAL if _small() else Layout.PORTAL


func _sequences() -> Dictionary:
	return Monte.SMALL_PORTAL_SEQUENCES if _small() else Layout.PORTAL_SEQUENCES


func _layers() -> Array[StringName]:
	return Monte.SMALL_PORTAL_LAYERS if _small() else Layout.PORTAL_LAYERS


func _sheet(next: StringName, layer: StringName) -> String:
	return Monte.small_portal_sheet(next, layer) if _small() else Layout.portal_sheet(next, layer)


func _placeholder() -> Dictionary:
	return Monte.PLACEHOLDER_SMALL_PORTAL if _small() else Layout.PLACEHOLDER_PORTAL


func _colours() -> Dictionary:
	return Monte.SMALL_COLOURS if _small() else Layout.PLACEHOLDER


func _sequence_time(name: StringName) -> float:
	var total := 0.0
	for time: float in _sequences()[name]:
		total += time
	return total


#WHAT IS DRAWN

func _build_drawn() -> void:
	var spec := _shape()
	for layer in _layers():
		var sheet := Sprite2D.new()
		sheet.name = String(layer).capitalize()
		sheet.scale = Vector2.ONE * Layout.SCALE
		sheet.offset = spec.frame / 2.0 - spec.pivot
		if layer == &"glow":
			var added := CanvasItemMaterial.new()
			added.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
			sheet.material = added
		art.add_child(sheet)
		sprites[layer] = sheet


func _build_placeholder() -> void:
	var spec := _placeholder()
	var shape := _shape()
	var colours := _colours()
	var added := CanvasItemMaterial.new()
	added.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	glow = Polygon2D.new()
	glow.name = "Glow"
	glow.polygon = _ellipse(Vector2.ONE * shape.ring * Layout.SCALE, spec.points)
	glow.color = colours.glow
	glow.material = added
	art.add_child(glow)
	var vortex := Polygon2D.new()
	vortex.name = "Vortex"
	vortex.polygon = _ellipse(Vector2.ONE * shape.opening * Layout.SCALE, spec.points)
	vortex.color = colours.vortex
	art.add_child(vortex)
	rim = Line2D.new()
	rim.name = "Rim"
	rim.points = _ellipse(Vector2.ONE * (shape.opening + shape.rim) / 2.0 * Layout.SCALE, spec.points)
	rim.closed = true
	rim.width = (shape.rim - shape.opening) * Layout.SCALE
	rim.default_color = colours.rim
	art.add_child(rim)
	var size: Vector2 = spec.fleck_size * Layout.SCALE / 2.0
	for i in spec.flecks:
		var fleck := Polygon2D.new()
		fleck.name = "Fleck%d" % i
		fleck.polygon = PackedVector2Array([Vector2(-size.x, -size.y), Vector2(size.x, -size.y), Vector2(size.x, size.y), Vector2(-size.x, size.y)])
		fleck.color = colours.card
		art.add_child(fleck)
		flecks.append(fleck)
	_turn_flecks(0.0)


# His cards circling the rim, a whole number of px out.
func _turn_flecks(delta: float) -> void:
	var spec := _placeholder()
	fleck_clock += delta
	var radii: Vector2 = Vector2.ONE * spec.fleck_orbit * Layout.SCALE
	for i in flecks.size():
		var angle: float = TAU * (float(i) / flecks.size() + fleck_clock * spec.fleck_turns)
		flecks[i].position = (Vector2.from_angle(angle) * radii).round()
		flecks[i].rotation = angle + PI / 2.0


# The placeholder's scale, mirrored for the big left gate. The drawn one only mirrors; a small one never does.
func _set_grown(amount: float) -> void:
	var mirror := -1.0 if side == &"left" and not _small() else 1.0
	art.scale = Vector2(mirror * amount, amount)


# The placeholder's own tweens run on physics, with its sequence clock.
func _grow_in(seconds: float) -> void:
	_kill(grow)
	modulate.a = 1.0
	grow = create_tween().set_process_mode(Tween.TWEEN_PROCESS_PHYSICS)
	grow.tween_method(_set_grown, _placeholder().grown_from, 1.0, maxf(seconds, 0.01)).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)


func _shrink_away(seconds: float) -> void:
	_kill(grow)
	grow = create_tween().set_process_mode(Tween.TWEEN_PROCESS_PHYSICS).set_parallel()
	grow.tween_method(_set_grown, absf(art.scale.y), _placeholder().grown_from, maxf(seconds, 0.01)).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	grow.tween_property(self, "modulate:a", 0.0, maxf(seconds, 0.01))


func _flare() -> void:
	var spec := _placeholder()
	var colours := _colours()
	_kill(flare)
	rim.default_color = colours.card
	glow.color = colours.glow.lightened(spec.flare_glow)
	flare = create_tween().set_process_mode(Tween.TWEEN_PROCESS_PHYSICS).set_parallel()
	flare.tween_property(rim, "default_color", colours.rim, spec.flare_time)
	flare.tween_property(glow, "color", colours.glow, spec.flare_time)


func _kill(tween: Tween) -> void:
	if tween != null and tween.is_valid():
		tween.kill()


func _ellipse(radii: Vector2, points: int) -> PackedVector2Array:
	var out := PackedVector2Array()
	for i in points:
		out.append(Vector2.from_angle(TAU * i / points) * radii)
	return out
