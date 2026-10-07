extends Node2D

# The strings from demon-god Jordan's fingertips to the puppets he works in his last phase (JordanCombo): a rig a
# puppet, two strings by default, from a pair of the fingertips of the hand that works it (STRING_PAIRS, or the
# generated table's own) to its back hook. They are drawn the way the approved art draws them (the user's blue take,
# art_source/jordan_puppeteer/jp_strings.py), on the 640x360-texel grid, every frame after the god and the puppets
# have stepped (process_priority) so they never trail a frame behind: each a quadratic from the fingertip to the hook
# whose middle sags (1 - tension) x SAG_OF_SPAN of its span, rastered a texel wide in the core colour; a texel of glow
# ADDED either side of it, one band where strings run side by side and dark between two; and at each fingertip its
# knot. pulse() runs a hot bead up them into his hand; snap() parts them.
#
# This is JordanGodScene's Strings layer, at z -2: over the god and the floor, under the puppets, whose backs the
# strings vanish into, and under the player.

const Layout := preload("res://Scripts/JordanGodLayout.gd")

const TEXEL := 3.0
const NEIGHBOURS: Array[Vector2i] = [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]

var god: Node2D
# One a puppet: {puppet, hand, hooks, tips (fingertip indices), tension, tension_tween, snap, bead}. `snap` and `bead`
# are -1, or how far a snap or a pulse has got, 0 to 1.
var rigs: Array[Dictionary] = []
var glow_canvas: Node2D
var core_canvas: Node2D
var knot_sprites: Array[Sprite2D] = []
var knot_texture: Texture2D
var add_material: CanvasItemMaterial
# This frame's texels, by colour: what the glow canvas adds and what the core canvas draws.
var added := {}
var drawn := {}
# Canvases over a puppet whose back is to the camera, by puppet: {glow, core, added, drawn}.
var over := {}


func _ready() -> void:
	process_priority = 100
	god = get_parent().get_node("God")
	add_material = CanvasItemMaterial.new()
	add_material.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	glow_canvas = Node2D.new()
	glow_canvas.name = "Glow"
	glow_canvas.material = add_material
	add_child(glow_canvas)
	glow_canvas.draw.connect(_draw_texels.bind(glow_canvas, added))
	core_canvas = Node2D.new()
	core_canvas.name = "Core"
	add_child(core_canvas)
	core_canvas.draw.connect(_draw_texels.bind(core_canvas, drawn))
	if Layout.final_knot():
		knot_texture = load(Layout.STRING_KNOT)


# `count` strings from `hand`'s fingertips (the pair its puppet takes) to `hooks` in turn (JordanPuppet.hook_point),
# slack until a yank.
func attach(puppet: Node2D, hand: StringName, hooks: Array = [&"back"], count := 2) -> void:
	detach(puppet)
	var pair: Array = god.string_pair(puppet.boss)
	var tips: Array[int] = []
	for i in maxi(count, 1):
		tips.append(int(pair[i % pair.size()]) if i < pair.size() else i)
	rigs.append({puppet = puppet, hand = hand, hooks = hooks if not hooks.is_empty() else [&"back"], tips = tips,
		tension = Layout.TENSION_LIMP, tension_tween = null, snap = -1.0, bead = -1.0})
	_rebuild()


func detach(puppet: Node2D) -> void:
	for rig in rigs.duplicate():
		if rig.puppet == puppet:
			_drop(rig)
	_rebuild()


func detach_all() -> void:
	for rig in rigs.duplicate():
		_drop(rig)
	_rebuild()


func is_attached(puppet: Node2D) -> bool:
	return rigs.any(func(rig: Dictionary) -> bool: return rig.puppet == puppet)


# Every string still up, for a test.
func line_count() -> int:
	var total := 0
	for rig in rigs:
		total += rig.tips.size()
	return total


# From 1 (a yank, taut) down to 0 (slack), over `seconds`. His drawn frames carry their own, which win.
func set_tension(puppet: Node2D, tension: float, seconds := Layout.TENSION_TIME) -> void:
	var rig := _rig(puppet)
	if rig.is_empty():
		return
	if rig.tension_tween != null and rig.tension_tween.is_valid():
		rig.tension_tween.kill()
	if seconds <= 0.0:
		rig.tension = tension
		return
	var tween := create_tween()
	tween.tween_method(func(value: float) -> void: rig.tension = value, rig.tension, tension, seconds)
	rig.tension_tween = tween


# The damage going up: a hot bead from the hook to the fingertip on each of the puppet's strings, over PULSE_TIME.
# Its tween, or null with no strings on it.
func pulse(puppet: Node2D) -> Tween:
	var rig := _rig(puppet)
	if rig.is_empty() or rig.snap >= 0.0:
		return null
	var tween := create_tween()
	tween.tween_method(func(value: float) -> void: rig.bead = value, 0.0, 1.0, Layout.PULSE_TIME)
	tween.tween_callback(func() -> void: rig.bead = -1.0)
	return tween


# His defeat: each string parts at the hook and whips up into his hand, and the rig is gone.
func snap(puppet: Node2D) -> Tween:
	var rig := _rig(puppet)
	if rig.is_empty():
		return null
	if rig.tension_tween != null and rig.tension_tween.is_valid():
		rig.tension_tween.kill()
	rig.bead = -1.0
	var tween := create_tween()
	tween.tween_method(func(value: float) -> void: rig.snap = value, 0.0, 1.0, Layout.SNAP_TIME).set_ease(Tween.EASE_IN)
	tween.tween_callback(func() -> void:
		_drop(rig)
		_rebuild()
	)
	return tween


func _process(_delta: float) -> void:
	for rig in rigs.duplicate():
		if not is_instance_valid(rig.puppet) or not rig.puppet.is_inside_tree():
			_drop(rig)
	_rebuild()


# This frame's strings, knots and beads onto the texel grid, and the canvases redrawn: this layer's, under the puppets,
# and over each puppet whose back is to the camera (JordanPuppet.strings_over), for his strings alone.
func _rebuild() -> void:
	added.clear()
	drawn.clear()
	var under: Array = []
	var over_rigs := {}
	for rig in rigs:
		if not is_instance_valid(rig.puppet):
			continue
		if rig.puppet.strings_over():
			if not over_rigs.has(rig.puppet):
				over_rigs[rig.puppet] = []
			over_rigs[rig.puppet].append(rig)
		else:
			under.append(rig)
	var tips: Array[Vector2i] = []
	_fill(under, added, drawn, tips)
	for puppet in over.keys():
		if not is_instance_valid(puppet) or not over_rigs.has(puppet):
			_drop_over(puppet)
	for puppet in over_rigs:
		var canvas := _over_canvas(puppet)
		canvas.added.clear()
		canvas.drawn.clear()
		_fill(over_rigs[puppet], canvas.added, canvas.drawn, tips)
		canvas.glow.queue_redraw()
		canvas.core.queue_redraw()
	_place_knots(tips)
	glow_canvas.queue_redraw()
	core_canvas.queue_redraw()


# `group`'s strings onto the grid: their cores into `to_draw`, their glow into `to_add`, their fingertips onto `tips`.
func _fill(group: Array, to_add: Dictionary, to_draw: Dictionary, tips: Array[Vector2i]) -> void:
	var cores: Array = []
	var beads: Array[Vector2i] = []
	for rig in group:
		var tension: float = god.hand_tension(rig.hand, rig.tension)
		for i in rig.tips.size():
			var tip: Vector2 = _to_texels(god.fingertip(rig.hand, rig.tips[i]))
			var hook_at: Vector2 = rig.puppet.hook_point(rig.hooks[i % rig.hooks.size()])
			# While he rises through his rift or sinks back into it, the string goes into the floor over him: it
			# ends on his soles' line, not on the part of him still under it.
			if rig.puppet.is_clipped():
				hook_at.y = minf(hook_at.y, rig.puppet.global_position.y)
			var hook: Vector2 = _to_texels(hook_at)
			if rig.snap >= 0.0:
				hook = hook.lerp(tip, rig.snap)
			var line := _raster(_curve(tip, hook, tension))
			cores.append(line)
			tips.append(line[0])
			if rig.bead >= 0.0 and not line.is_empty():
				beads.append(line[roundi((1.0 - rig.bead) * (line.size() - 1))])
	var owners := {}
	for i in cores.size():
		for texel in cores[i]:
			if not owners.has(texel):
				owners[texel] = {}
			owners[texel][i] = true
	var colours: Dictionary = Layout.STRING_COLORS
	for texel in owners:
		for step in NEIGHBOURS:
			var near: Vector2i = texel + step
			if owners.has(near) or to_add.has(near):
				continue
			var strings := {}
			for around in NEIGHBOURS:
				for i in owners.get(near + around, {}):
					strings[i] = true
			if strings.size() < 2:
				to_add[near] = colours.glow
		to_draw[texel] = colours.core
	for bead in beads:
		for dx in range(-1, 2):
			for dy in range(-1, 2):
				to_add[bead + Vector2i(dx, dy)] = colours.knot
		for step in NEIGHBOURS:
			if owners.has(bead + step):
				to_draw[bead + step] = colours.bright
		to_draw[bead] = colours.hot


# A pair of canvases over `puppet`, his own children a z step over his sprite, for the strings that tie on to his back
# when it is to the camera.
func _over_canvas(puppet: Node2D) -> Dictionary:
	if over.has(puppet):
		return over[puppet]
	var canvas := {added = {}, drawn = {}}
	canvas.glow = Node2D.new()
	canvas.glow.name = "StringsOverGlow"
	canvas.glow.material = add_material
	canvas.glow.z_index = 1
	puppet.add_child(canvas.glow)
	canvas.glow.draw.connect(_draw_texels.bind(canvas.glow, canvas.added))
	canvas.core = Node2D.new()
	canvas.core.name = "StringsOverCore"
	canvas.core.z_index = 1
	puppet.add_child(canvas.core)
	canvas.core.draw.connect(_draw_texels.bind(canvas.core, canvas.drawn))
	over[puppet] = canvas
	return canvas


func _drop_over(puppet: Node2D) -> void:
	var canvas: Dictionary = over.get(puppet, {})
	over.erase(puppet)
	for part in [canvas.get("glow"), canvas.get("core")]:
		if is_instance_valid(part):
			part.queue_free()


# The knot at each fingertip: its drawn sprite, or the same diamond in code - the hot texel, the knot round it, the
# glow round that, all but the hot one added.
func _place_knots(tips: Array[Vector2i]) -> void:
	if knot_texture == null:
		var colours: Dictionary = Layout.STRING_COLORS
		for tip in tips:
			for dx in range(-2, 3):
				for dy in range(-2, 3):
					var d := absi(dx) + absi(dy)
					if d == 1:
						added[tip + Vector2i(dx, dy)] = colours.knot
					elif d == 2 and not added.has(tip + Vector2i(dx, dy)):
						added[tip + Vector2i(dx, dy)] = colours.glow
			drawn[tip] = colours.hot
		return
	while knot_sprites.size() < tips.size():
		var knot := Sprite2D.new()
		knot.texture = knot_texture
		knot.scale = Vector2.ONE * TEXEL
		knot.material = add_material
		add_child(knot)
		knot_sprites.append(knot)
	for i in knot_sprites.size():
		knot_sprites[i].visible = i < tips.size()
		if i < tips.size():
			knot_sprites[i].position = (Vector2(tips[i]) + Vector2(0.5, 0.5)) * TEXEL


func _draw_texels(canvas: Node2D, texels: Dictionary) -> void:
	for texel in texels:
		canvas.draw_rect(Rect2(canvas.to_local(to_global(Vector2(texel) * TEXEL)), Vector2(TEXEL, TEXEL)), texels[texel])


# A world point in texels, a texel's centre landing on its whole coordinates.
func _to_texels(point: Vector2) -> Vector2:
	return to_local(point) / TEXEL - Vector2(0.5, 0.5)


# The hanging string's points, in texels: a quadratic from the fingertip to the hook, its control point sagging
# (1 - tension) x SAG_OF_SPAN of the span below the middle.
func _curve(from: Vector2, to: Vector2, tension: float) -> PackedVector2Array:
	var span := maxf(from.distance_to(to), 1.0)
	var control := from.lerp(to, 0.5) + Vector2(0.0, (1.0 - clampf(tension, 0.0, 1.0)) * Layout.SAG_OF_SPAN * span)
	var steps := maxi(8, int(span / 2.0))
	var points := PackedVector2Array()
	for i in steps + 1:
		var t := float(i) / steps
		points.append((1.0 - t) * (1.0 - t) * from + 2.0 * (1.0 - t) * t * control + t * t * to)
	return points


# The 1-texel line through the points, 8-connected, with the doubled L-corners dropped.
func _raster(points: PackedVector2Array) -> Array[Vector2i]:
	var line: Array[Vector2i] = []
	for point in points:
		var texel := Vector2i(floori(point.x + 0.5), floori(point.y + 0.5))
		if line.is_empty():
			line.append(texel)
			continue
		var last: Vector2i = line[-1]
		while last != texel:
			last += _step_toward(last, texel)
			line.append(last)
	var out: Array[Vector2i] = []
	for i in line.size():
		if i > 0 and i < line.size() - 1:
			var a: Vector2i = line[i - 1]
			var b: Vector2i = line[i + 1]
			var p: Vector2i = line[i]
			if absi(a.x - b.x) == 1 and absi(a.y - b.y) == 1 and (a.x == p.x or a.y == p.y):
				continue
		out.append(line[i])
	return out


# One texel along the straightest 8-connected way from `at` toward `to`.
func _step_toward(at: Vector2i, to: Vector2i) -> Vector2i:
	var d := to - at
	if absi(d.x) > 2 * absi(d.y):
		return Vector2i(signi(d.x), 0)
	if absi(d.y) > 2 * absi(d.x):
		return Vector2i(0, signi(d.y))
	return Vector2i(signi(d.x), signi(d.y))


func _rig(puppet: Node2D) -> Dictionary:
	for rig in rigs:
		if rig.puppet == puppet:
			return rig
	return {}


func _drop(rig: Dictionary) -> void:
	if rig.tension_tween != null and rig.tension_tween.is_valid():
		rig.tension_tween.kill()
	rigs.erase(rig)
