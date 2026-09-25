extends Node2D

# The FX of Greyson's final brawl (GreysonFinalBrawl), each a child of this node, which stands at the origin of
# GreysonScene's FxLayer: the gold arrow over his head, a hook's whoosh or the straight's burst, a landed punch's
# impact and a clean slip's afterimage. None of it is in greyson_hazard, so the main fight's clean-ups never reach
# it; the brawl frees this node and all of it goes with it. Every piece runs on its own node-bound tween, so a pause
# and a finisher's freeze hold it, except a punch strip's step 1, which the brawl puts up itself on the resolve's
# frame (strike) so it can never land a frame late. The sheets are GreysonBrawlLayout.FX's; until each is flagged
# on, a code-drawn stand-in plays its part on the same point and clock. Every z is absolute (GreysonBrawlLayout).

const Layout := preload("res://Scripts/GreysonBrawlLayout.gd")

const ARROW_POP := 0
const ARROW_LIVE := 1
const ARROW_ANSWERED := 2
const ARROW_MISSED := 3
# A strip's `hook`: his LEFT hook, his RIGHT hook, or the straight's burst.
const LEFT_HOOK := 0
const RIGHT_HOOK := 1
const STRAIGHT := -1

var arrow: Node2D
var arrow_right := false
var arrow_live: Tween
# Every arrow still up, the one fading out after its answer included.
var arrows: Array[Node2D] = []
# The punch in the air, up on its step 0 until strike(), and which one it is.
var strip: Node2D
var strip_hook := LEFT_HOOK


#THE ARROW

# Up on `at`, the tell point, on its pop, then live until it is answered or missed. Only one at a time: a new tell
# takes an old arrow still fading out with it.
func show_arrow(right: bool, at: Vector2) -> void:
	clear_arrow()
	arrow_right = right
	arrow = _sheet(&"arrow") if Layout.uses_final_fx(&"arrow") else _stand_in_arrow(right)
	arrow.name = "BrawlArrow"
	arrows.append(arrow)
	_add(arrow, at, Layout.TELL_Z)
	_arrow_state(arrow, ARROW_POP)
	arrow_live = arrow.create_tween()
	arrow_live.tween_interval(Layout.ARROW_POP)
	arrow_live.tween_callback(_arrow_state.bind(arrow, ARROW_LIVE))


# Answered (the slip landed) or missed (the hook did), held a beat, then faded as ParryTell's badges fade.
func answer_arrow(answered: bool) -> void:
	if not is_instance_valid(arrow):
		return
	if arrow_live:
		arrow_live.kill()
	arrow_live = null
	var answered_arrow := arrow
	arrow = null
	_arrow_state(answered_arrow, ARROW_ANSWERED if answered else ARROW_MISSED)
	var fade := answered_arrow.create_tween()
	fade.tween_interval(Layout.ARROW_HOLD)
	fade.tween_property(answered_arrow, "modulate:a", 0.0, Layout.ARROW_FADE)
	fade.tween_callback(answered_arrow.queue_free)


func clear_arrow() -> void:
	for up in arrows:
		if is_instance_valid(up):
			up.queue_free()
	arrows.clear()
	arrow = null
	arrow_live = null


func _arrow_state(which: Node2D, state: int) -> void:
	if not is_instance_valid(which):
		return
	if which is Sprite2D:
		which.frame = (4 if arrow_right else 0) + state
		return
	var look: Dictionary = Layout.PLACEHOLDER_FX[&"arrow"]
	var ring: Line2D = which.get_node("Ring")
	var glyph: Polygon2D = which.get_node("Glyph")
	which.scale = Vector2.ONE * (look.pop_scale if state == ARROW_POP else 1.0)
	match state:
		ARROW_POP:
			ring.default_color = look.answered
			glyph.color = look.answered
		ARROW_LIVE:
			ring.default_color = look.ring_color
			glyph.color = look.glyph
		ARROW_ANSWERED:
			ring.default_color = look.answered
			glyph.color = look.answered
		ARROW_MISSED:
			ring.default_color = look.missed
			glyph.color = look.missed


# The badge the sheet draws: a disc in his darkest purple on its pivot, a gold ring and an arrow the way to slip.
func _stand_in_arrow(right: bool) -> Node2D:
	var look: Dictionary = Layout.PLACEHOLDER_FX[&"arrow"]
	var radius: float = look.radius
	var centre := Vector2(0, -radius)
	var badge := Node2D.new()
	var disc := Polygon2D.new()
	disc.polygon = _circle(centre, radius, 20)
	disc.color = look.disc
	badge.add_child(disc)
	var ring := Line2D.new()
	ring.name = "Ring"
	ring.points = _circle(centre, radius - look.ring / 2.0, 20)
	ring.closed = true
	ring.width = look.ring
	badge.add_child(ring)
	var glyph := Polygon2D.new()
	glyph.name = "Glyph"
	var way := 1.0 if right else -1.0
	var tip := radius * 0.6
	glyph.polygon = PackedVector2Array([
		centre + Vector2(tip * way, 0),
		centre + Vector2(0, -tip),
		centre + Vector2(0, -tip * 0.4),
		centre + Vector2(-tip * way, -tip * 0.4),
		centre + Vector2(-tip * way, tip * 0.4),
		centre + Vector2(0, tip * 0.4),
		centre + Vector2(0, tip),
	])
	badge.add_child(glyph)
	return badge


#THE PUNCHES

# The whoosh of a hook (LEFT_HOOK or RIGHT_HOOK, pivoting on the head at rest) or the straight's burst (STRAIGHT, on
# the parry contact), up on its step 0.
func wind(hook: int, at: Vector2) -> void:
	_free_strip()
	strip_hook = hook
	strip = _make_strip(hook)
	strip.name = "BrawlStrip"
	_add(strip, at, Layout.WHOOSH_Z)
	_strip_step(strip, hook, 0)


# Step 1 on this frame, the resolve's, then the rest of the strip on its own clock. A punch whose answer came too
# late for its step 0 starts here.
func strike(hook: int, at: Vector2) -> void:
	if not is_instance_valid(strip) or strip_hook != hook:
		wind(hook, at)
	var struck := strip
	strip = null
	_strip_step(struck, hook, 1)
	var play := struck.create_tween()
	for step in [2, 3]:
		play.tween_interval(Layout.STRIKE_STEP)
		play.tween_callback(_strip_step.bind(struck, hook, step))
	play.tween_interval(Layout.STRIKE_STEP)
	play.tween_callback(struck.queue_free)


func _free_strip() -> void:
	if is_instance_valid(strip):
		strip.queue_free()
	strip = null


func _make_strip(hook: int) -> Node2D:
	if hook == STRAIGHT:
		if Layout.uses_final_fx(&"straight"):
			return _sheet(&"straight")
		var look: Dictionary = Layout.PLACEHOLDER_FX[&"straight"]
		var burst := Node2D.new()
		var core := Polygon2D.new()
		core.name = "Core"
		core.polygon = _circle(Vector2.ZERO, look.core, 12)
		core.color = look.color
		burst.add_child(core)
		var ring := Line2D.new()
		ring.name = "Ring"
		ring.closed = true
		ring.width = look.width
		ring.default_color = look.color
		burst.add_child(ring)
		return burst
	if Layout.uses_final_fx(&"hook"):
		var sheet := _sheet(&"hook")
		sheet.offset = Layout.FX[&"hook"].offsets[hook]
		return sheet
	var line := Line2D.new()
	line.width = Layout.PLACEHOLDER_FX[&"hook"].width
	line.default_color = Layout.PLACEHOLDER_FX[&"hook"].color
	line.begin_cap_mode = Line2D.LINE_CAP_ROUND
	line.end_cap_mode = Line2D.LINE_CAP_ROUND
	return line


func _strip_step(which: Node2D, hook: int, step: int) -> void:
	if not is_instance_valid(which):
		return
	if which is Sprite2D:
		which.frame = step if hook == STRAIGHT else hook * 4 + step
		return
	if hook == STRAIGHT:
		var look: Dictionary = Layout.PLACEHOLDER_FX[&"straight"]
		(which.get_node("Ring") as Line2D).points = _circle(Vector2.ZERO, look.rings[step], 16)
		which.get_node("Core").visible = step == 1
		which.modulate.a = look.alphas[step]
		return
	# The arc in texels from the pivot, from its tail to its front this step; the right hook's mirrored.
	var look: Dictionary = Layout.PLACEHOLDER_FX[&"hook"]
	var span: Vector2 = look.steps[step]
	var mirror := -1.0 if hook == RIGHT_HOOK else 1.0
	var points := PackedVector2Array()
	for i in 9:
		var x: float = lerpf(span.x, span.y, i / 8.0)
		points.append(Vector2(x * mirror, look.a * x * x + look.b * x) * Layout.SCALE)
	(which as Line2D).points = points
	which.modulate.a = look.alphas[step]


# A punch that lands, burst on `at` from this frame.
func impact(at: Vector2) -> void:
	var burst: Node2D
	var steps: int
	if Layout.uses_final_fx(&"impact"):
		burst = _sheet(&"impact")
		steps = Layout.FX[&"impact"].hframes
	else:
		var look: Dictionary = Layout.PLACEHOLDER_FX[&"impact"]
		var star := Polygon2D.new()
		var polygon := PackedVector2Array()
		for i in look.points * 2:
			var radius: float = look.outer if i % 2 == 0 else look.inner
			polygon.append(Vector2.from_angle(TAU * i / (look.points * 2) - PI / 2.0) * radius)
		star.polygon = polygon
		star.color = look.color
		burst = star
		steps = look.scales.size()
	burst.name = "BrawlImpact"
	_add(burst, at, Layout.IMPACT_Z)
	var play := burst.create_tween()
	for step in steps:
		play.tween_callback(_impact_step.bind(burst, step))
		play.tween_interval(Layout.IMPACT_STEP)
	play.tween_callback(burst.queue_free)


func _impact_step(burst: Node2D, step: int) -> void:
	if burst is Sprite2D:
		burst.frame = step
		return
	var look: Dictionary = Layout.PLACEHOLDER_FX[&"impact"]
	burst.scale = Vector2.ONE * look.scales[step]
	burst.modulate.a = look.alphas[step]


#THE AFTERIMAGE

# Copies of the player's frame as it stands, in the perfect-dodge cyan, from the slip back toward the rest
# position (`slip`, px, the way the head went), under the player, fading out.
func afterimage(sprite: Sprite2D, slip: float) -> void:
	var alphas: Array = Layout.AFTERIMAGE_ALPHAS
	for i in alphas.size():
		var ghost := Sprite2D.new()
		ghost.name = "BrawlAfterimage"
		ghost.texture = sprite.texture
		ghost.hframes = sprite.hframes
		ghost.vframes = sprite.vframes
		ghost.frame = sprite.frame
		ghost.flip_h = sprite.flip_h
		ghost.centered = sprite.centered
		ghost.offset = sprite.offset
		ghost.scale = sprite.global_scale
		ghost.modulate = Layout.AFTERIMAGE_TINT
		ghost.modulate.a = alphas[i]
		_add(ghost, sprite.global_position - Vector2(slip * (i + 1) / (alphas.size() + 1), 0), Layout.WHOOSH_Z)
		var fade := ghost.create_tween()
		fade.tween_property(ghost, "modulate:a", 0.0, Layout.AFTERIMAGE_FADE)
		fade.tween_callback(ghost.queue_free)


#EVERYTHING

func clear() -> void:
	for child in get_children():
		child.queue_free()
	arrows.clear()
	arrow = null
	arrow_live = null
	strip = null


# What is up and not on its way out: the tests' count.
func live_count() -> int:
	return get_children().filter(func(child: Node) -> bool: return not child.is_queued_for_deletion()).size()


func _sheet(key: StringName) -> Sprite2D:
	var spec: Dictionary = Layout.FX[key]
	var sheet := Sprite2D.new()
	sheet.texture = load(spec.texture)
	sheet.hframes = spec.hframes
	sheet.offset = spec.get("offset", Vector2.ZERO)
	sheet.scale = Vector2.ONE * Layout.SCALE
	return sheet


func _add(node: Node2D, at: Vector2, z: int) -> void:
	node.z_as_relative = false
	node.z_index = z
	add_child(node)
	node.global_position = at.round()


static func _circle(centre: Vector2, radius: float, points: int) -> PackedVector2Array:
	var circle := PackedVector2Array()
	for i in points:
		circle.append(centre + Vector2.from_angle(TAU * i / points) * radius)
	return circle
