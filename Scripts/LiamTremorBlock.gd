extends Node2D

# One tremor ridge of Liam's walls (LiamTremors, the stream LiamTremorPatterns lays out), flat on his FloorLayer. Its
# node stands on its footprint's top-left corner. It cracks on his first slam - its crack line racing out to it from the
# pillar's base, its footprint glowing - and heaves on his second: a StaticBody2D on layer 1 from then on, which nothing
# passes, a dash included (a CharacterBody2D's motion is swept), and an Area2D REACH px past it that hurts to touch.
#
# Its hits: MattTrueshotScript's latch on the player's hurtbox, the origin their hurtbox centre, liam_tremor's flags (no
# answer, no badge, no PERFECT DODGE). On ice a touch bounces the player off the nearest face at `bounce` px/s. A ridge
# that heaves under the player (their body UNDER_MARGIN px or less from its footprint) hurts them once and pushes them
# straight down out of it at PUSH_SPEED, never through it toward the pillar, and only turns solid once they are clear.
# It crumbles at once as far as the fight goes (crumble), then frees itself. Everything it times steps in its own
# _physics_process, so a pause and a finisher's freeze hold it.
#
# Its march (march): a step straight down on each of his slams. A step never drives it solid into the player: one that
# would come down on them goes the heave-under way (one hit, pushed down, solid again once clear), and one that would
# come down on a player pinned against the bottom hurts them once and crumbles (or stops above them, pinned_crumbles
# off). A ridge whose bottom reaches floor_y sinks there, on the frame it does. A ridge that has pushed the player, by heave or step, holds its
# hit until they are PUSH_CLEAR px away from it, so a player it keeps stepping onto pays one hit, not one a step; any hit
# does the same, and holds the hits of the rest of its wall (siblings) too, so one wall costs one hit a contact.

const Layout := preload("res://Scripts/LiamArtLayout.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")

const TREMOR_ID := &"liam_tremor"
const REACH := 6.0
const UNDER_MARGIN := 4.0
const PUSH_SPEED := 900.0
# A push leaves the player under 19 px from it (UNDER_MARGIN plus a frame's 15 px at PUSH_SPEED), past REACH, and the
# next step closes up to 27 px of that; its hit waits until they are clear of all of it.
const PUSH_CLEAR := 48.0
# Its crack line fades this long from the first step: its segments would otherwise slide down with it.
const CRACK_FADE_TIME := 0.3

enum Phase { WAITING, TELL, RISEN, CRUMBLE }

# Set before it enters the tree: its footprint (world px), who it hurts and how hard a touch bounces them on ice.
var rect := Rect2()
var player: CharacterBody2D
var bounce := 300.0
# Set by the state for the march: the bottom wall it sinks at, how close to it counts as the player pinned, and what a
# step onto a pinned player does.
var floor_y := 975.0
var pinned_margin := 8.0
var pinned_crumbles := true

var phase := Phase.WAITING
var solid := false
var damaging := false
# Heaved under the player: pushing them out before it turns solid.
var pushing := false
var hit_latched := false
var touch_latched := false
# It has pushed the player: hit_latched holds until they are PUSH_CLEAR px away.
var push_latched := false
# A step's push: not solid while it pushes, it keeps a player under it at its face, so a dash's last frames can't carry
# them into it. A heave's push starts with them inside, and only pushes.
var push_keeps_face := false
# For a test: every resolved result, and whether the heave caught the player under it.
var results: Array[int] = []
# The other blocks of its wall (LiamTremors sets them): a hit from any one holds all their hits too, so a wall costs
# the player one hit however many of its overlapping blocks they are under.
var siblings: Array = []
var heaved_under := false

var body: StaticBody2D
var body_shape: CollisionShape2D
var damage: Area2D
var art: Node2D
var sheet: Sprite2D
var rock: Polygon2D
var glow: Polygon2D
var edge: Line2D
var clip := &""
var clip_step := 0
var clip_clock := 0.0
# What `clip` plays: its own strip's every frame (fx_v2's liam_tremor_block_<clip>.png, its length kept), or the
# combined sheet's TREMOR_CLIPS entry.
var clip_spec: Dictionary = {}
var combined_sheet: Texture2D
var clip_strips := {}
var crumble_clock := 0.0

# The step under way: rect.position.y from march_from_y to march_to_y over march_time.
var marching := false
var march_clock := 0.0
var march_time := 0.15
var march_from_y := 0.0
var march_to_y := 0.0
var march_eased := true
# Seconds since the first step, which fades the crack out, or below 0.
var crack_fade := -1.0

# Its crack: from `crack_from` toward its footprint's nearest point, growing at `crack_speed` px/s from the first slam.
var crack_from := Vector2.ZERO
var crack_speed := 0.0
var crack_length := 0.0
var crack_reach := 0.0
var crack_clock := 0.0
var crack: Node2D
var crack_line: Line2D
var crack_core: Line2D
var crack_segments: Array[Sprite2D] = []


func _ready() -> void:
	_build_body()
	_build_damage()
	_build_art()
	_build_crack()


func footprint() -> Rect2:
	return rect


#ITS LIFE

# Its tell, a slam before it heaves (his crack, for the opening walls): its crack races out to it from `from` at `speed`.
func tell(from: Vector2, speed: float) -> void:
	phase = Phase.TELL
	crack_from = from
	crack_speed = speed
	crack_reach = from.distance_to(from.clamp(rect.position, rect.end))
	crack_length = 0.0
	crack.visible = true
	art.visible = true
	_play(&"tell")


# His second slam: up, hurting from here, and solid unless the player is under it.
func heave() -> void:
	if phase == Phase.CRUMBLE:
		return
	phase = Phase.RISEN
	_play(&"heave")
	damaging = true
	damage.set_deferred("monitoring", true)
	if _player_under():
		heaved_under = true
		pushing = true
		push_keeps_face = false
		touch_latched = true
		if not hit_latched:
			_hurt()
		push_latched = true
		hit_latched = true
		return
	_set_solid(true)


# The slams after the heave: a pulse through it, and nothing more.
func pulse() -> void:
	if phase == Phase.RISEN:
		_play(&"pulse")


# A slam once the march is on: `step` px straight down over `time`, eased out unless `eased` is off. A step that finds
# the last one still under way carries on from where the ridge is to that one's end plus `step`, so steps chain without
# drifting.
func march(step: float, time: float, eased := true) -> void:
	if phase != Phase.RISEN:
		return
	if crack_fade < 0.0:
		crack_fade = 0.0
	march_to_y = (march_to_y if marching else rect.position.y) + step
	march_from_y = rect.position.y
	march_time = maxf(time, 0.001)
	march_clock = 0.0
	march_eased = eased
	marching = true
	_play(&"pulse")


# Gone as far as the fight goes, from this frame: nothing solid and nothing hurting. It crumbles away and frees itself.
func crumble() -> void:
	if phase == Phase.CRUMBLE:
		return
	phase = Phase.CRUMBLE
	pushing = false
	damaging = false
	_set_solid(false)
	damage.set_deferred("monitoring", false)
	crumble_clock = 0.0
	_play(&"crumble")


func is_solid() -> bool:
	return solid


func _physics_process(delta: float) -> void:
	_step_clip(delta)
	_step_crack(delta)
	if phase == Phase.CRUMBLE:
		crumble_clock += delta
		var fade_from: float = Layout.clip_length(&"crumble")
		if crumble_clock >= fade_from:
			modulate.a = clampf(1.0 - (crumble_clock - fade_from) / maxf(Layout.CRUMBLE_TIME - fade_from, 0.01), 0.0, 1.0)
		if crumble_clock >= Layout.CRUMBLE_TIME:
			queue_free()
		return
	if marching:
		_step_march(delta)
		if phase == Phase.CRUMBLE:
			return
	if pushing:
		if _player_under():
			if push_keeps_face:
				_keep_at_face()
			player.add_drift(Vector2(0, PUSH_SPEED))
			return
		pushing = false
		_set_solid(true)
	if damaging:
		_resolve_hits()


# One frame of a step, judged before it moves: coming down on the player it stops being solid and pushes them down out
# of the way, hurting once; coming down on a player pinned against the bottom it hurts them once and crumbles, or stops
# above them. A step that ends with its bottom at floor_y or past it sinks it.
func _step_march(delta: float) -> void:
	march_clock += delta
	var weight := clampf(march_clock / march_time, 0.0, 1.0)
	var eased := 1.0 - (1.0 - weight) * (1.0 - weight) if march_eased else weight
	var next_y := lerpf(march_from_y, march_to_y, eased)
	var next := Rect2(Vector2(rect.position.x, next_y), rect.size)
	if is_instance_valid(player) and _player_box().grow(UNDER_MARGIN).intersects(next):
		if _player_box().end.y >= floor_y - pinned_margin:
			if not pinned_crumbles:
				marching = false
				return
			if not hit_latched:
				_hurt()
			crumble()
			return
		if not pushing:
			pushing = true
			push_latched = true
			push_keeps_face = true
			touch_latched = true
			_set_solid(false)
			if not hit_latched:
				_hurt()
	position.y += next_y - rect.position.y
	rect.position.y = next_y
	# Sinking the moment it gets there, not at its step's end: a glide chained slam to slam may never reach one.
	if rect.end.y >= floor_y:
		marching = false
		crumble()
		return
	if weight >= 1.0:
		marching = false


#ITS HITS

func _resolve_hits() -> void:
	if not is_instance_valid(player):
		return
	var touching := false
	var near := false
	for area in damage.get_overlapping_areas():
		if area == player.hurtBox:
			touching = true
		elif player.is_dodge_ghost(area):
			near = true
	if not touching:
		touch_latched = false
		if not push_latched or not _player_box().grow(PUSH_CLEAR).intersects(rect):
			push_latched = false
			hit_latched = false
		if near:
			player.receive_near_miss(_hit())
		return
	if not touch_latched:
		touch_latched = true
		if player.on_ice:
			_bounce()
	if not hit_latched:
		_hurt()


# A hit holds this block's hits, and its wall's, until the player is PUSH_CLEAR px clear of each: a touch that bounces
# them off on the ice and the pin that follows are one hit, as a push and its pin are.
func _hurt() -> void:
	var result: int = player.receive_hit(_hit())
	if result != HitInfo.Result.IGNORED:
		results.append(result)
		for block in siblings + [self]:
			if is_instance_valid(block):
				block.hit_latched = true
				block.push_latched = true


func _hit() -> RefCounted:
	var centre: Vector2 = player.hurtBox.get_node("CollisionShape2D").global_position
	return HitInfo.make(TREMOR_ID, damage, centre, null)


# Off the face nearest the player's middle: their speed along it kept, their speed away from it at least `bounce`.
func _bounce() -> void:
	var centre: Vector2 = _player_box().get_center()
	var away := centre - centre.clamp(rect.position, rect.end)
	var normal := Vector2.DOWN
	if away != Vector2.ZERO:
		normal = Vector2(signf(away.x), 0.0) if absf(away.x) > absf(away.y) else Vector2(0.0, signf(away.y))
	var along: Vector2 = player.velocity - normal * player.velocity.dot(normal)
	player.velocity = along + normal * maxf(player.velocity.dot(normal), bounce)


# A player under it who has come up past its face is put back on it, straight down.
func _keep_at_face() -> void:
	var box := _player_box()
	if box.position.y < rect.end.y and box.end.y > rect.end.y and box.position.x < rect.end.x and box.end.x > rect.position.x:
		player.global_position.y += rect.end.y - box.position.y


func _player_under() -> bool:
	return is_instance_valid(player) and _player_box().grow(UNDER_MARGIN).intersects(rect)


func _player_box() -> Rect2:
	var shape: CollisionShape2D = player.get_node("CollisionShape2D")
	return shape.global_transform * shape.shape.get_rect()


func _set_solid(on: bool) -> void:
	solid = on
	# Deferred: this can run inside a physics flush.
	body_shape.set_deferred("disabled", not on)


#BUILDING IT

func _build_body() -> void:
	body = StaticBody2D.new()
	body.name = "Ridge"
	body.collision_layer = 1
	body.collision_mask = 0
	body_shape = CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = rect.size
	body_shape.shape = shape
	body_shape.position = rect.size / 2.0
	body_shape.disabled = true
	body.add_child(body_shape)
	add_child(body)


func _build_damage() -> void:
	damage = Area2D.new()
	damage.name = "Damage"
	damage.collision_layer = 0
	damage.collision_mask = 2
	damage.monitorable = false
	damage.monitoring = false
	var shape := CollisionShape2D.new()
	var box := RectangleShape2D.new()
	box.size = rect.size + Vector2.ONE * REACH * 2.0
	shape.shape = box
	shape.position = rect.size / 2.0
	damage.add_child(shape)
	add_child(damage)


func _build_art() -> void:
	art = Node2D.new()
	art.name = "Art"
	art.visible = false
	add_child(art)
	if Layout.final_tremor():
		sheet = Sprite2D.new()
		combined_sheet = load(Layout.TREMOR_SHEET)
		for clip_name: StringName in Layout.TREMOR_CLIPS:
			if ResourceLoader.exists(Layout.tremor_clip_sheet(clip_name)):
				clip_strips[clip_name] = load(Layout.tremor_clip_sheet(clip_name))
		sheet.texture = combined_sheet
		sheet.hframes = roundi(combined_sheet.get_width() / Layout.TREMOR_FRAME.x)
		sheet.centered = false
		sheet.scale = Vector2.ONE * Layout.SCALE
		sheet.position = Vector2(0, -Layout.TREMOR_FOOTPRINT_TOP * Layout.SCALE)
		art.add_child(sheet)
		return
	var look: Dictionary = Layout.PLACEHOLDER_TREMOR
	var local := Rect2(Vector2.ZERO, rect.size)
	glow = Polygon2D.new()
	glow.polygon = Layout.rect_polygon(local)
	glow.color = look.glow
	art.add_child(glow)
	rock = Polygon2D.new()
	rock.polygon = PackedVector2Array([Vector2(0, -look.jut), Vector2(local.size.x, -look.jut), local.end, Vector2(0, local.size.y)])
	rock.color = look.rock
	art.add_child(rock)
	var top := Polygon2D.new()
	top.polygon = Layout.rect_polygon(Rect2(0, -look.jut, local.size.x, look.jut))
	top.color = look.rock_top
	rock.add_child(top)
	edge = Line2D.new()
	edge.points = Layout.rect_polygon(local)
	edge.closed = true
	edge.width = look.edge_width
	edge.default_color = look.glow_edge
	art.add_child(edge)


func _build_crack() -> void:
	crack = Node2D.new()
	crack.name = "Crack"
	crack.visible = false
	add_child(crack)
	if Layout.final_crack():
		return
	var look: Dictionary = Layout.PLACEHOLDER_TREMOR
	crack_line = Line2D.new()
	crack_line.width = look.crack_width
	crack_line.default_color = look.crack
	crack.add_child(crack_line)
	crack_core = Line2D.new()
	crack_core.width = 2.0
	crack_core.default_color = look.crack_core
	crack.add_child(crack_core)


#DRAWING IT

func _play(clip_name: StringName) -> void:
	clip = clip_name
	clip_step = 0
	clip_clock = 0.0
	clip_spec = _clip_spec(clip_name)
	_show_clip()


# The clip on its own strip when fx_v2 drew one (a one-shot spread over its frames, a loop at its frame time), put up on
# the sprite; otherwise the combined sheet's entry.
func _clip_spec(clip_name: StringName) -> Dictionary:
	var spec: Dictionary = Layout.TREMOR_CLIPS[clip_name]
	if sheet == null:
		return spec
	# Back to the first frame before the frame count changes, so the current one can't be out of range.
	sheet.frame = 0
	if not clip_strips.has(clip_name):
		sheet.texture = combined_sheet
		sheet.hframes = roundi(combined_sheet.get_width() / Layout.TREMOR_FRAME.x)
		return spec
	var strip: Texture2D = clip_strips[clip_name]
	var count := maxi(roundi(strip.get_width() / Layout.TREMOR_FRAME.x), 1)
	sheet.texture = strip
	sheet.hframes = count
	var times: Array = Layout.TREMOR_STRIP_TIMES.get(clip_name, [])
	if times.size() != count:
		times = []
		if spec.loop:
			for i in count:
				times.append(spec.times[0])
		else:
			times = Layout.spread(spec.times, count)
	return {frames = range(count), times = times, loop = spec.loop}


func _step_clip(delta: float) -> void:
	if clip == &"":
		return
	var spec: Dictionary = clip_spec
	var times: Array = spec.times
	clip_clock += delta
	while clip_clock >= times[clip_step]:
		clip_clock -= times[clip_step]
		if clip_step < times.size() - 1:
			clip_step += 1
		elif spec.loop:
			clip_step = 0
		elif clip == &"heave" or clip == &"pulse":
			_play(&"active")
			return
		else:
			break
	_show_clip()


func _show_clip() -> void:
	if sheet != null:
		sheet.frame = clip_spec.frames[clip_step]
		return
	var look: Dictionary = Layout.PLACEHOLDER_TREMOR
	var into: float = clip_clock / maxf(Layout.TREMOR_CLIPS[clip].times[clip_step], 0.001)
	match clip:
		&"tell":
			glow.visible = true
			rock.visible = false
			glow.modulate.a = 0.5 + 0.5 * absf(sin((clip_step + into) * PI / 2.0))
			edge.default_color = look.glow_edge
		&"heave":
			glow.visible = false
			rock.visible = true
			var risen: float = (clip_step + into) / Layout.TREMOR_CLIPS[&"heave"].frames.size()
			rock.scale = Vector2(1.0, lerpf(0.3, 1.0, clampf(risen, 0.0, 1.0)))
			rock.position = Vector2(0, rect.size.y * (1.0 - rock.scale.y))
			edge.default_color = look.edge
		&"active":
			glow.visible = false
			rock.visible = true
			rock.scale = Vector2.ONE
			rock.position = Vector2.ZERO
			rock.modulate = Color.WHITE
			edge.default_color = look.edge
		&"pulse":
			rock.modulate = look.pulse
		&"crumble":
			rock.scale = Vector2(1.0, maxf(1.0 - (clip_step + into) / 4.0, 0.1))
			rock.position = Vector2(0, rect.size.y * (1.0 - rock.scale.y))
			edge.visible = false


func _step_crack(delta: float) -> void:
	if not crack.visible:
		return
	crack_clock += delta
	if crack_fade >= 0.0:
		crack_fade += delta
		if crack_fade >= CRACK_FADE_TIME:
			crack.visible = false
			return
		crack.modulate.a = minf(crack.modulate.a, 1.0 - crack_fade / CRACK_FADE_TIME)
	if phase == Phase.CRUMBLE:
		crack.modulate.a = minf(crack.modulate.a, clampf(1.0 - crumble_clock / Layout.CRUMBLE_TIME, 0.0, 1.0))
	crack_length = minf(crack_length + crack_speed * delta, crack_reach)
	var start := crack_from - global_position
	var toward := (crack_from.clamp(rect.position, rect.end) - crack_from).normalized()
	var head := start + toward * crack_length
	if crack_line != null:
		crack_line.points = PackedVector2Array([start, head])
		crack_core.points = crack_line.points
		return
	# Segments laid end to end from the pillar's base, each shown once the crack's head has passed its start.
	var length := Layout.TREMOR_CRACK_FRAME.x * Layout.SCALE
	var needed := ceili(crack_reach / length)
	while crack_segments.size() < needed:
		var segment := Sprite2D.new()
		var texture: Texture2D = load(Layout.TREMOR_CRACK_SHEET)
		segment.texture = texture
		segment.hframes = roundi(texture.get_width() / Layout.TREMOR_CRACK_FRAME.x)
		segment.centered = false
		segment.offset = -Layout.TREMOR_CRACK_PIVOT
		segment.scale = Vector2.ONE * Layout.SCALE
		segment.rotation = toward.angle()
		segment.position = (start + toward * length * crack_segments.size()).round()
		crack.add_child(segment)
		crack_segments.append(segment)
	var frame := int(crack_clock / Layout.TREMOR_CRACK_FRAME_TIME)
	for i in crack_segments.size():
		var segment := crack_segments[i]
		segment.visible = length * i < crack_length
		segment.frame = frame % segment.hframes
