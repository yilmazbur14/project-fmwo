extends Node2D

# Greyson's beam, V2 (JordanComboMaze; the user, 2026-09-29: "much scarier ... much faster through the maze"), on the
# god's Fx layer over the dark. The combo times every beat; this only draws them:
#   charge()     the charge on his raised muzzle, and the overlay on him lighting his eyes and his barrel;
#   fire()       the release off the thrown cannon's muzzle as the head snaps out of it;
#   trace()      the head races the route, into the goal and back down the corridor to the player's block, turning
#                every corner: the body laid behind it, a splash at each corner;
#   impact()     the impact off its end and a ring round the player's soles;
#   crackling    the hold;
#   dissipate()  the line dissipates into embers and smoke, and the path is left scorched;
#   cool()       the scorch cools.
# Each piece is its final sheet once that is in (JordanMazeLayout.beam_final()), and drawn in code until then, snapped
# to the texel grid so it sits with the pixel art: streaks drawn into a pulsing core, a launch burst, a band with a glow
# and a white-hot core and afterimages trailing the head, sparks and rings off the corners and the blast, arcs off the
# band through the hold, the band breaking into pieces that burn out, and the scorch laid behind the head. The overlay
# has no stand-in. Everything moves on _process, so a pause, a freeze and a hit-stop hold it. The scorch is drawn on
# the floor node fire() is handed, lifted over the dark and under the player.

const Layout := preload("res://Scripts/JordanMazeLayout.gd")

const TEXEL := 3.0
# Where each part draws, over the Fx layer's own z.
const Z_GLOW := 0
const Z_BODY := 1
const Z_SMOKE := 2
const Z_CORE := 3
const Z_GHOST := 3
const Z_HEAD := 4
const Z_SPARKS := 5
const Z_BLAST := 6
# The band's cross-section, top to bottom, as indices into BEAM_V2_BODY.colors: outline, deep, red, hot, white.
const PROFILE := [0, 1, 1, 2, 2, 3, 3, 4, 4, 3, 3, 2, 2, 1, 1, 0]

var rng := RandomNumberGenerator.new()
var additive := CanvasItemMaterial.new()
# Which final pieces are in, and their sheets, looked up once a beam.
var finals := {}
var textures := {}
# Final pieces stepping through their own frames: {node, age, time, frames, loop}.
var playing: Array[Dictionary] = []

#THE CHARGE
var charging := false
var charge_share := 0.0
var muzzle_at := Vector2.ZERO
var spawn_owed := 0.0
var core: Node2D
var core_glow: Polygon2D
var core_red: Polygon2D
var core_heart: Polygon2D
var core_sheet: Node2D
var core_clock := 0.0
var ring_clock := 0.0
var collapsing: Array[Node2D] = []
var inbound: Array[Dictionary] = []
var puppet: Sprite2D
var overlay: Sprite2D
var overlay_clock := 0.0

#THE BEAM
var route := PackedVector2Array()
var along: Array[float] = []
var total := 0.0
var progress := 0.0
var tip := Vector2.ZERO
var heading := 0.0
var going_left := false
var glow_line: Line2D
var body_line: Line2D
var core_line: Line2D
var frames: Array[Texture2D] = []
var glow_frames: Array[Texture2D] = []
var shimmer_clock := 0.0
var shimmer_step := 0
var head_node: Node2D
var head_sheet: Node2D
var head_rays: Array[Polygon2D] = []
var ghosts: Array[Node2D] = []
var trail: Array[Dictionary] = []
var corners: Array[Dictionary] = []
var corners_done := 0
var crackling := false
var arc_clock := 0.0
var pop_clock := 0.0
var dissipating := false
var pieces: Array[Dictionary] = []
var dissolve_frames: Array[Texture2D] = []
var dissolve_clock := -1.0
# The final dissipate's embers and smoke, waiting for their times: {time, kind, at}.
var due: Array[Dictionary] = []
# Everything thrown off it: sparks, embers and smoke that fly on their own; rings and flashes that grow and fade.
var flying: Array[Dictionary] = []
var fading: Array[Dictionary] = []

#THE SCORCH
var scorch: Node2D
var scorch_route := PackedVector2Array()
var scorch_along: Array[float] = []
var air := 0.0
var scorch_char: Line2D
var scorch_glow: Line2D
var scorch_line: Line2D
var scorch_frames: Array[Texture2D] = []
var scorch_clock := -1.0


func _init() -> void:
	rng.randomize()
	additive.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	# After the puppets' own _process, so the overlay matches the frame Greyson shows this frame, not the last.
	process_priority = 1


# The overlay is on Greyson's sprite, not under this.
func _exit_tree() -> void:
	_drop_overlay()


#THE CHARGE

# The charge on the muzzle, which charge() grows, and the overlay on `greyson_sprite`.
func begin_charge(greyson_sprite: Sprite2D) -> void:
	charging = true
	puppet = greyson_sprite
	var spec := Layout.BEAM_V2_CORE
	core = Node2D.new()
	core.name = "Core"
	core.z_index = Z_CORE
	add_child(core)
	if _final(&"charge"):
		core_sheet = _sheet(&"charge", core, Vector2.ZERO)
	else:
		core_glow = _circle(1.0, 16, spec.glow_color, true)
		core_red = _circle(1.0, 12, spec.red, true)
		core_heart = _diamond(1.0, spec.white)
		for part in [core_glow, core_red, core_heart]:
			core.add_child(part)
	if _final(&"overlay") and is_instance_valid(puppet):
		overlay = Sprite2D.new()
		overlay.name = "MazeBeamOverlay"
		overlay.texture = _texture("overlay")
		overlay.hframes = Layout.BEAM_V2_ART[&"overlay"].frames
		puppet.add_child(overlay)
		_place_overlay()
	_cut_sheets()
	_show_core(0.0)


# The lines' frames, cut now rather than as the beam fires: cutting a sheet reads it back off the GPU.
func _cut_sheets() -> void:
	frames = _body_frames()
	if _glow(&"body"):
		var body: Dictionary = Layout.BEAM_V2_ART[&"body"]
		glow_frames = _frames_of("body_glow", body.glow_frame, body.frames)
	if _final(&"dissipate"):
		var art: Dictionary = Layout.BEAM_V2_ART[&"dissipate"]
		dissolve_frames = _frames_of("dissipate", art.frame, art.frames)
	if _final(&"scorch"):
		var art: Dictionary = Layout.BEAM_V2_ART[&"scorch"]
		scorch_frames = _frames_of("scorch", art.frame, art.frames)


# `share` of the way charged, the muzzle where it is now, world px. The final charge shows its stage's frames on a
# loop, each stage an equal share of the charge however long it is.
func charge(share: float, muzzle: Vector2) -> void:
	charge_share = clampf(share, 0.0, 1.0)
	muzzle_at = to_local(muzzle)
	core.position = _snap(muzzle_at)
	if core_sheet != null:
		var art: Dictionary = Layout.BEAM_V2_ART[&"charge"]
		var per: int = art.frames / art.stages
		var stage := _charge_stage()
		var into: float = (charge_share - float(stage) / art.stages) * Layout.charge_time()
		_show_frame(core_sheet, stage * per + int(into / art.frame_time) % per)
	_place_overlay()


func _charge_stage() -> int:
	var stages: int = Layout.BEAM_V2_ART[&"charge"].stages
	return mini(int(charge_share * stages), stages - 1)


func _show_core(pulse: float) -> void:
	if core_sheet != null:
		return
	var spec := Layout.BEAM_V2_CORE
	var beat: float = 1.0 + spec.depth * pulse
	var lit := minf(charge_share * 4.0, 1.0)
	core_glow.scale = Vector2.ONE * maxf(lerpf(spec.glow.x, spec.glow.y, charge_share) * beat * lit, 0.01)
	core_red.scale = Vector2.ONE * maxf(lerpf(spec.inner.x, spec.inner.y, charge_share) * (1.0 + spec.depth * 0.6 * pulse) * lit, 0.01)
	core_heart.scale = Vector2.ONE * maxf(_snap_len(lerpf(spec.heart.x, spec.heart.y, charge_share) * (1.0 + spec.depth * 0.3 * pulse)) * lit, 0.01)


# The overlay on his sprite as it is drawn now, with its centring, offset and mirror: through the charge, the frame
# drawn for the one he shows at the charge's stage; then the throw's frames flickering. Off any other sheet or frame.
func _place_overlay() -> void:
	if not is_instance_valid(overlay) or not is_instance_valid(puppet):
		return
	var art: Dictionary = Layout.BEAM_V2_ART[&"overlay"]
	var on_sheet: bool = puppet.texture != null and puppet.texture.resource_path.get_file() == art.over
	var poses: Array = art.poses.get(puppet.frame, []) if on_sheet else []
	overlay.visible = not poses.is_empty()
	if not overlay.visible:
		return
	overlay.centered = puppet.centered
	overlay.offset = puppet.offset
	overlay.flip_h = puppet.flip_h
	if charging:
		overlay.frame = poses[mini(_charge_stage(), poses.size() - 1)]
	else:
		overlay.frame = poses[int(overlay_clock / art.flicker) % poses.size()]


func _drop_overlay() -> void:
	if is_instance_valid(overlay):
		overlay.queue_free()
	overlay = null


#THE TRACE

# The charge goes out, the release bursts off the thrown cannon's muzzle and the head snaps out of it: `points` world px
# from the muzzle, the scorch drawn on `floor_node`.
func fire(points: PackedVector2Array, floor_node: Node2D) -> void:
	charging = false
	core.visible = false
	for ring in collapsing:
		if is_instance_valid(ring):
			ring.visible = false
	collapsing.clear()
	route = PackedVector2Array()
	for point in points:
		route.append(to_local(point))
	along = [0.0]
	for i in range(1, route.size()):
		along.append(along[i - 1] + route[i - 1].distance_to(route[i]))
	total = along[along.size() - 1]
	air = along[1] if along.size() > 1 else 0.0
	for i in range(1, route.size() - 1):
		var outer := (route[i] - route[i - 1]).normalized() - (route[i + 1] - route[i]).normalized()
		corners.append({at = route[i], along = along[i], done = false, outer = outer})
	_build_body()
	_build_head()
	scorch = floor_node
	_build_scorch(points)
	if _final(&"release"):
		var release := _sheet(&"release", self, route[0])
		release.z_index = Z_BLAST
		_play(release, &"release", false)
	else:
		_launch_burst(route[0])
	_place_overlay()
	trace(0.0)


# Drawn from the muzzle to `share` of the way along; the px the head has come.
func trace(share: float) -> float:
	progress = clampf(share, 0.0, 1.0)
	var reach := total * progress
	var points := _line_to(route, along, reach)
	for line in [glow_line, body_line, core_line]:
		line.points = points
	tip = points[points.size() - 1]
	var way := _way_at(reach)
	if way != Vector2.ZERO:
		heading = way.angle()
		# The run's own x, not cos(heading): the float angle of a run straight down or up has a cosine a hair under 0.
		going_left = way.x < 0.0
	head_node.position = _snap(tip)
	head_node.rotation = heading
	if head_sheet != null:
		_flip(head_sheet, false, going_left)
	trail.push_front({at = tip, heading = heading})
	if trail.size() > ghosts.size() + 1:
		trail.pop_back()
	for k in ghosts.size():
		var ghost := ghosts[k]
		ghost.visible = k + 1 < trail.size()
		if ghost.visible:
			ghost.position = _snap(trail[k + 1].at)
			ghost.rotation = trail[k + 1].heading
	for corner in corners:
		if not corner.done and reach >= corner.along:
			corner.done = true
			corners_done += 1
			_corner_burst(corner)
	_scorch_to(reach - air)
	return reach


func head() -> Vector2:
	return to_global(tip)


func is_through() -> bool:
	return progress >= 1.0


#THE IMPACT

# Off the beam's end as the head arrives, the head spent in it: the impact, and under it the ring round the player's
# soles, BEAM_HEIGHT under the end.
func impact() -> void:
	head_node.visible = false
	for ghost in ghosts:
		ghost.visible = false
	var at := tip
	if _final(&"impact"):
		var blast := _sheet(&"impact", self, at)
		blast.z_index = Z_BLAST
		_play(blast, &"impact", false)
	else:
		_blast(at)
	if _final(&"ring"):
		# Under the impact but over the lifted walls: on the floor node the corridor's walls hid all of it.
		var ring := _sheet(&"ring", self, at + Vector2(0, Layout.BEAM_HEIGHT))
		ring.z_index = Z_BLAST - 1
		_play(ring, &"ring", false)
	else:
		_shockwave(at)
	if not _final(&"scorch"):
		_splat()


#THE HOLD AND THE DISSIPATION

# The drawn band crackles through the hold; the final one's own frames carry it.
func set_crackling(on: bool) -> void:
	crackling = on and not _final(&"body")
	arc_clock = 0.0
	pop_clock = 0.0


# `share` of the way through. As it starts the overlay goes and the scorch is laid; then the final line runs its
# dissipate frames on its own clock, or the drawn band breaks into pieces that burn out one by one over the first
# BREAK.spread of it.
func dissipate(share: float) -> void:
	if not dissipating:
		dissipating = true
		set_crackling(false)
		head_node.visible = false
		_drop_overlay()
		if _final(&"scorch"):
			_lay_scorch()
		if _final(&"dissipate"):
			_dissolve()
		else:
			_break_up()
	if dissolve_clock >= 0.0:
		return
	var fade_by: float = Layout.BEAM_V2_BREAK.glow_fade
	glow_line.modulate.a = 1.0 - clampf(share / fade_by, 0.0, 1.0)
	core_line.modulate.a = 1.0 - clampf(share / (fade_by * 0.6), 0.0, 1.0)
	var spread: float = Layout.BEAM_V2_BREAK.spread
	for piece in pieces:
		if not piece.burning and share >= piece.start * spread:
			_burn(piece)


# The drawn scorch's glow going out, `share` of the way; the final one cools in its own frames.
func cool(share: float) -> void:
	if is_instance_valid(scorch_glow):
		scorch_glow.modulate.a = 1.0 - clampf(share, 0.0, 1.0)


# The final dissipate: the line's texture swapped to its frames, its glow and core lines off, and the embers and smoke
# it throws off waiting for their times.
func _dissolve() -> void:
	var art: Dictionary = Layout.BEAM_V2_ART[&"dissipate"]
	dissolve_clock = 0.0
	body_line.texture = dissolve_frames[0]
	body_line.width = art.frame.y * Layout.SCALE
	glow_line.visible = false
	core_line.visible = false
	for kind in [&"ember", &"smoke"]:
		var spec: Dictionary = Layout.BEAM_V2_ART[kind]
		var from := 0.0
		while from < total:
			var to := minf(from + spec.every, total)
			var count: int = spec.count if spec.has("count") else (1 if rng.randf() < spec.chance else 0)
			for n in count:
				due.append({time = rng.randf() * spec.spread, kind = kind,
					at = _off_line(rng.randf_range(from, to), spec.within)})
			from = to
	due.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return a.time < b.time)


func _dissolving(delta: float) -> void:
	dissolve_clock += delta
	var art: Dictionary = Layout.BEAM_V2_ART[&"dissipate"]
	var frame := int(dissolve_clock / art.frame_time)
	body_line.visible = frame < art.frames
	if body_line.visible:
		body_line.texture = dissolve_frames[frame]
	while not due.is_empty() and due[0].time <= dissolve_clock:
		var bit: Dictionary = due.pop_front()
		if bit.kind == &"ember":
			_ember(bit.at)
		else:
			_smoke(bit.at)


# The drawn band goes into its pieces at once, looking the same; its glow and white core fade out over the first
# BREAK.glow_fade of the dissipation, so the break has no pop.
func _break_up() -> void:
	body_line.visible = false
	var segment: float = Layout.BEAM_V2_BREAK.segment
	var from := 0.0
	while from < total - 0.5:
		var to := minf(from + segment, total)
		var piece := Line2D.new()
		piece.points = _line_between(from, to)
		piece.width = body_line.width
		piece.texture = frames[rng.randi_range(0, frames.size() - 1)]
		piece.texture_mode = Line2D.LINE_TEXTURE_TILE
		piece.texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
		piece.joint_mode = Line2D.LINE_JOINT_SHARP
		piece.z_index = Z_BODY
		add_child(piece)
		pieces.append({line = piece, start = rng.randf(), burning = false, age = 0.0, width = piece.width,
			middle = _point_at((from + to) / 2.0), from = from, to = to})
		from = to


func _burn(piece: Dictionary) -> void:
	piece.burning = true
	var spec := Layout.BEAM_V2_BREAK
	for n in spec.embers:
		_ember(_point_at(rng.randf_range(piece.from, piece.to)))
	for n in spec.smoke:
		_smoke(piece.middle)


#EVERY FRAME

func _process(delta: float) -> void:
	core_clock += delta
	if charging:
		var spec := Layout.BEAM_V2_CORE
		_show_core(sin(core_clock * lerpf(spec.pulse.x, spec.pulse.y, charge_share) * TAU))
		if core_sheet == null:
			_draw_in(delta)
		_collapse_rings(delta)
	elif is_instance_valid(overlay):
		overlay_clock += delta
	_place_overlay()
	_move_inbound(delta)
	if is_instance_valid(body_line):
		_shimmer(delta)
	if is_instance_valid(head_node) and head_node.visible and head_sheet == null:
		_flicker_head()
	if crackling:
		_crackle(delta)
	if dissolve_clock >= 0.0:
		_dissolving(delta)
	if scorch_clock >= 0.0 and is_instance_valid(scorch_line):
		_cool_scorch(delta)
	_step_playing(delta)
	_move_flying(delta)
	_move_fading(delta)
	_burn_pieces(delta)


# More sparks drawn in the further the charge has come.
func _draw_in(delta: float) -> void:
	var spec := Layout.BEAM_V2_SPARKS
	spawn_owed += lerpf(spec.rate.x, spec.rate.y, charge_share) * delta
	while spawn_owed >= 1.0:
		spawn_owed -= 1.0
		var from := muzzle_at + Vector2.from_angle(rng.randf() * TAU) * rng.randf_range(spec.ring.x, spec.ring.y)
		var colors: Array = spec.colors
		var spark := _streak(spec.size, colors[rng.randi_range(0, colors.size() - 1)])
		spark.z_index = Z_SPARKS
		spark.modulate.a = 0.0
		add_child(spark)
		inbound.append({node = spark, from = from, age = 0.0, life = rng.randf_range(spec.life.x, spec.life.y)})


# Each drawn in faster as it nears, and gone into the muzzle.
func _move_inbound(delta: float) -> void:
	for i in range(inbound.size() - 1, -1, -1):
		var spark: Dictionary = inbound[i]
		spark.age += delta
		var t := clampf(spark.age / spark.life, 0.0, 1.0)
		var node: Node2D = spark.node
		node.position = _snap(spark.from.lerp(muzzle_at, t * t))
		node.modulate.a = minf(t * 4.0, 1.0)
		node.rotation = (muzzle_at - spark.from).angle()
		if t >= 1.0:
			node.queue_free()
			inbound.remove_at(i)


# Rings collapsing into the core, closer together as it fills.
func _collapse_rings(delta: float) -> void:
	var spec := Layout.BEAM_V2_CORE
	if core_sheet != null or charge_share <= 0.0:
		return
	ring_clock += delta
	var every := lerpf(spec.ring_every.x, spec.ring_every.y, charge_share)
	while ring_clock >= every:
		ring_clock -= every
		var ring := _ring(spec.ring.x, 24, spec.ring_color, TEXEL)
		ring.position = _snap(muzzle_at)
		ring.z_index = Z_CORE
		ring.modulate.a = 0.0
		add_child(ring)
		collapsing.append(ring)
		fading.append({node = ring, age = 0.0, life = spec.ring_time, ring = spec.ring, width = Vector2(TEXEL, TEXEL * 2.0),
			fade_in = true})


# Off the thrown cannon's muzzle as the head leaves it: a white star over a red disc, a ring out and sparks.
func _launch_burst(at: Vector2) -> void:
	var spec := Layout.BEAM_V2_LAUNCH
	var disc := _circle(spec.disc, 16, Color("#FF2A2A"), true)
	var star := _star(8, spec.star, 0.3, Color("#FFF4E8"), false)
	for part in [disc, star]:
		part.position = _snap(at)
		part.z_index = Z_BLAST
		add_child(part)
		fading.append({node = part, age = 0.0, life = spec.time, grow = Vector2(0.5, 1.3)})
	var ring := _ring(spec.ring.x, 24, Color("#FF6A3C"), 9.0)
	ring.position = _snap(at)
	ring.z_index = Z_BLAST
	add_child(ring)
	fading.append({node = ring, age = 0.0, life = spec.time * 1.4, ring = spec.ring, width = Vector2(9, 3)})
	for n in spec.sparks:
		_spark(at, Vector2.from_angle(rng.randf() * TAU) * rng.randf_range(260.0, 700.0), rng.randf_range(0.12, 0.3), 5.0, 400.0)


# The line's frames, and the drawn band's jitter.
func _shimmer(delta: float) -> void:
	if dissolve_clock >= 0.0:
		return
	var body_final := _final(&"body")
	var every: float = Layout.BEAM_V2_ART[&"body"].frame_time if body_final else Layout.BEAM_V2_BODY.shimmer
	shimmer_clock += delta
	if shimmer_clock < every:
		return
	shimmer_clock = fmod(shimmer_clock, every)
	shimmer_step += 1
	body_line.texture = frames[shimmer_step % frames.size()]
	if not glow_frames.is_empty():
		glow_line.texture = glow_frames[shimmer_step % glow_frames.size()]
	for piece in pieces:
		if not piece.burning:
			piece.line.texture = frames[(shimmer_step + piece.line.get_index()) % frames.size()]
	if body_final:
		return
	var spec := Layout.BEAM_V2_BODY
	var jitter: float = spec.jitter if crackling else spec.jitter / 3.0
	glow_line.width = spec.glow + _snap_len(rng.randf_range(-jitter, jitter) * 2.0)
	core_line.width = maxf(spec.core + _snap_len(rng.randf_range(-jitter, jitter)), TEXEL)


func _flicker_head() -> void:
	var spec := Layout.BEAM_V2_HEAD
	head_node.scale = Vector2.ONE * (1.0 + spec.pulse * (1.0 if shimmer_step % 2 == 0 else -1.0))
	for ray in head_rays:
		ray.rotation = rng.randf() * TAU
		ray.scale = Vector2(rng.randf_range(0.5, 1.3), 1.0)


# Arcs jumping off the band and sparks popping from it.
func _crackle(delta: float) -> void:
	var spec := Layout.BEAM_V2_CRACKLE
	arc_clock += delta
	pop_clock += delta
	while arc_clock >= spec.arc_every:
		arc_clock -= spec.arc_every
		_arc()
	while pop_clock >= spec.pop_every:
		pop_clock -= spec.pop_every
		var reach := rng.randf() * total
		var normal := _way_at(reach).orthogonal() * (1.0 if rng.randf() < 0.5 else -1.0)
		_spark(_point_at(reach), normal.rotated(rng.randf_range(-0.6, 0.6)) * rng.randf_range(200.0, 520.0),
			rng.randf_range(0.12, 0.26), 5.0, 600.0)


func _arc() -> void:
	var spec := Layout.BEAM_V2_CRACKLE
	var reach := rng.randf() * total
	var way := _way_at(reach)
	var normal := way.orthogonal()
	var length := rng.randf_range(spec.arc_length.x, spec.arc_length.y)
	var start := _point_at(reach) + normal * rng.randf_range(-12.0, 12.0)
	var arc := Line2D.new()
	var kinks := 5
	for k in kinks + 1:
		var point := start + way * length * k / kinks
		if k > 0 and k < kinks:
			point += normal * rng.randf_range(-18.0, 18.0)
		arc.add_point(_snap(point))
	arc.width = spec.arc_width
	arc.default_color = Color("#FFF4E8") if rng.randf() < 0.5 else Color("#FF5A3C")
	arc.material = additive
	arc.z_index = Z_SPARKS
	add_child(arc)
	fading.append({node = arc, age = 0.0, life = spec.arc_life})


# The final scorch's frames, each from its second of the dissipation, the last held.
func _cool_scorch(delta: float) -> void:
	scorch_clock += delta
	var starts: Array = Layout.BEAM_V2_ART[&"scorch"].starts
	var k := 0
	while k + 1 < starts.size() and scorch_clock >= starts[k + 1]:
		k += 1
	if scorch_line.texture != scorch_frames[k]:
		scorch_line.texture = scorch_frames[k]


# The final pieces' own frames: once through and gone, or on a loop.
func _step_playing(delta: float) -> void:
	for i in range(playing.size() - 1, -1, -1):
		var run: Dictionary = playing[i]
		if not is_instance_valid(run.node):
			playing.remove_at(i)
			continue
		var node: Node2D = run.node
		run.age += delta
		var frame := int(run.age / run.time)
		if frame >= run.frames and not run.loop:
			node.queue_free()
			playing.remove_at(i)
			continue
		_show_frame(node, frame % run.frames)


func _move_flying(delta: float) -> void:
	for i in range(flying.size() - 1, -1, -1):
		var bit: Dictionary = flying[i]
		bit.age += delta
		var node: Node2D = bit.node
		if bit.age >= bit.life:
			node.queue_free()
			flying.remove_at(i)
			continue
		bit.velocity *= maxf(1.0 - bit.drag * delta, 0.0)
		bit.velocity.y += bit.gravity * delta
		bit.at += bit.velocity * delta
		node.position = _snap(bit.at)
		var t: float = bit.age / bit.life
		if bit.has("frames"):
			_show_frame(node, mini(int(t * bit.frames), bit.frames - 1))
			continue
		node.modulate.a = 1.0 - t * t
		if bit.has("grow"):
			node.scale = Vector2.ONE * lerpf(bit.grow.x, bit.grow.y, t)
		elif bit.velocity.length() > 1.0:
			node.rotation = bit.velocity.angle()
		if bit.has("colors") and int(bit.age / 0.05) % 2 == 1:
			(node as Polygon2D).color = bit.colors[int(bit.age / 0.05) % bit.colors.size()]


func _move_fading(delta: float) -> void:
	for i in range(fading.size() - 1, -1, -1):
		var bit: Dictionary = fading[i]
		bit.age += delta
		var node: Node2D = bit.node
		var t := clampf(bit.age / bit.life, 0.0, 1.0)
		var eased := 1.0 - (1.0 - t) * (1.0 - t)
		if bit.has("ring"):
			var line := node as Line2D
			line.points = _circle_points(lerpf(bit.ring.x, bit.ring.y, eased), 32)
			line.width = lerpf(bit.width.x, bit.width.y, t)
		if bit.has("grow"):
			node.scale = Vector2.ONE * lerpf(bit.grow.x, bit.grow.y, eased)
		if bit.has("spin"):
			node.rotation += bit.spin * delta
		node.modulate.a = minf(t * 3.0, 1.0) if bit.has("fade_in") else 1.0 - t * t
		if t >= 1.0:
			node.queue_free()
			fading.remove_at(i)


func _burn_pieces(delta: float) -> void:
	var burn: float = Layout.BEAM_V2_BREAK.burn
	for i in range(pieces.size() - 1, -1, -1):
		var piece: Dictionary = pieces[i]
		if not piece.burning:
			continue
		piece.age += delta
		var t := clampf(piece.age / burn, 0.0, 1.0)
		var line: Line2D = piece.line
		line.width = maxf(_snap_len(piece.width * (1.0 - t)), 0.0)
		line.modulate = Color(1.0, 1.0 - t * 0.6, 1.0 - t * 0.7, 1.0 - t * t)
		if t >= 1.0:
			line.queue_free()
			pieces.remove_at(i)


#WHAT IS DRAWN

# The line: the body, a glow line under it and a white-hot core line down it. The final body's glow line is its glow
# sheet's, in step with it, or none; the final body carries its own core.
func _build_body() -> void:
	var spec := Layout.BEAM_V2_BODY
	if _final(&"body"):
		var art: Dictionary = Layout.BEAM_V2_ART[&"body"]
		glow_line = _line(art.glow_frame.y * Layout.SCALE, Color.WHITE, Z_GLOW, true)
		if glow_frames.is_empty():
			glow_line.visible = false
		else:
			_tile(glow_line, glow_frames[0])
	else:
		glow_line = _line(spec.glow, spec.glow_color, Z_GLOW, true)
	body_line = _line(_body_width(), Color.WHITE, Z_BODY, false)
	_tile(body_line, frames[0])
	core_line = _line(spec.core, spec.core_color, Z_CORE, true)
	core_line.visible = not _final(&"body")


func _body_width() -> float:
	if _final(&"body"):
		return Layout.BEAM_V2_ART[&"body"].frame.y * Layout.SCALE
	return Layout.BEAM_V2_BODY.width


# The band's frames: the drawn body's, cut apart so the line tiles one at a time, or drawn here on the texel grid,
# PROFILE across it with its hot rows wandering and flecks of heat and char, a frame apiece.
func _body_frames() -> Array[Texture2D]:
	if _final(&"body"):
		var art: Dictionary = Layout.BEAM_V2_ART[&"body"]
		return _frames_of("body", art.frame, art.frames)
	var out: Array[Texture2D] = []
	var spec := Layout.BEAM_V2_BODY
	var colors: Array = spec.colors
	var rows := PROFILE.size()
	for f in spec.frames:
		var image := Image.create(16, rows, false, Image.FORMAT_RGBA8)
		for x in 16:
			var wander := rng.randi_range(-1, 1) if rng.randf() < 0.45 else 0
			for y in rows:
				var shade: int = PROFILE[clampi(y - wander, 1, rows - 2)] if y > 0 and y < rows - 1 else PROFILE[y]
				if shade == 2 and rng.randf() < 0.14:
					shade = 3
				elif shade == 1 and rng.randf() < 0.1:
					shade = 0
				elif shade == 4 and rng.randf() < 0.12:
					shade = 3
				image.set_pixel(x, y, colors[shade])
		out.append(ImageTexture.create_from_image(image))
	return out


# The head: the final sheet on the line's end, or the drawn one with its afterimages trailing it.
func _build_head() -> void:
	var spec := Layout.BEAM_V2_HEAD
	head_node = Node2D.new()
	head_node.name = "Head"
	head_node.z_index = Z_HEAD
	add_child(head_node)
	if _final(&"head"):
		head_sheet = _sheet(&"head", head_node, Vector2.ZERO)
		_play(head_sheet, &"head", true)
		return
	head_node.add_child(_circle(spec.aura, 16, spec.aura_color, true))
	for n in spec.rays:
		var ray := Polygon2D.new()
		ray.polygon = PackedVector2Array([Vector2(0, -TEXEL), Vector2(spec.aura * 1.4, 0), Vector2(0, TEXEL)])
		ray.color = Color("#FFD8B0")
		ray.material = additive
		head_node.add_child(ray)
		head_rays.append(ray)
	head_node.add_child(_flare(spec.flare, spec.flare_color, true))
	head_node.add_child(_diamond(spec.heart, Color("#FFFFFF")))
	for k in spec.afterimages:
		var ghost := Node2D.new()
		ghost.name = "Afterimage%d" % k
		ghost.z_index = Z_GHOST
		add_child(ghost)
		ghost.add_child(_flare(spec.flare * (1.0 - 0.08 * (k + 1)), spec.flare_color, true))
		ghost.add_child(_diamond(spec.heart * 0.6, Color("#FFE0C8")))
		ghost.modulate.a = spec.ghost_alpha * (1.0 - float(k) / spec.afterimages)
		ghost.visible = false
		ghosts.append(ghost)


# A corner turned: the final splash, mirrored to throw it out of the turn, or drawn sparks, a ring and a star flash.
func _corner_burst(corner: Dictionary) -> void:
	var at: Vector2 = corner.at
	if _final(&"corner"):
		var splash := _sheet(&"corner", self, at)
		splash.z_index = Z_SPARKS
		_flip(splash, corner.outer.x < 0.0, corner.outer.y > 0.0)
		_play(splash, &"corner", false)
		return
	var spec := Layout.BEAM_V2_CORNER
	var star := _star(4, spec.star, 0.25, Color("#FFF4E8"), true)
	star.position = _snap(at)
	star.z_index = Z_SPARKS
	add_child(star)
	fading.append({node = star, age = 0.0, life = spec.star_time, grow = Vector2(0.6, 1.4)})
	var ring := _ring(spec.ring.x, 24, Color("#FF6A3C"), 9.0)
	ring.position = _snap(at)
	ring.z_index = Z_SPARKS
	add_child(ring)
	fading.append({node = ring, age = 0.0, life = spec.ring_time, ring = spec.ring, width = Vector2(9, 3)})
	for n in spec.sparks:
		_spark(at, Vector2.from_angle(rng.randf() * TAU) * rng.randf_range(spec.speed.x, spec.speed.y),
			rng.randf_range(spec.life.x, spec.life.y), spec.drag, 500.0)


# The drawn blast: its stars, a white burst and sparks everywhere.
func _blast(at: Vector2) -> void:
	var blast := Layout.BEAM_V2_BLAST
	for layer in [[12, 1.0, Color("#B3202A")], [10, 0.72, Color("#FF6A3C")], [8, 0.45, Color("#FFF4E8")]]:
		var star := _star(layer[0], blast.radius * layer[1], 0.45, layer[2], layer[2] != Color("#FFF4E8"))
		star.position = _snap(at)
		star.z_index = Z_BLAST
		star.rotation = rng.randf() * TAU
		add_child(star)
		fading.append({node = star, age = 0.0, life = blast.time, grow = Vector2(0.25, 1.0), spin = rng.randf_range(-2.0, 2.0)})
	var disc := _star(16, blast.disc, 0.78, Color("#FFF8F0"), false)
	disc.position = _snap(at)
	disc.z_index = Z_BLAST
	add_child(disc)
	fading.append({node = disc, age = 0.0, life = blast.disc_time, grow = Vector2(0.7, 1.15)})
	for n in blast.sparks:
		_spark(at, Vector2.from_angle(rng.randf() * TAU) * rng.randf_range(blast.speed.x, blast.speed.y),
			rng.randf_range(blast.life.x, blast.life.y), 4.0, 900.0)


# The drawn shockwave, and a red echo behind it.
func _shockwave(at: Vector2) -> void:
	var wave := Layout.BEAM_V2_SHOCKWAVE
	var ring := _ring(wave.from, 32, wave.color, wave.width.x)
	ring.position = _snap(at)
	ring.z_index = Z_BLAST
	add_child(ring)
	fading.append({node = ring, age = 0.0, life = wave.time, ring = Vector2(wave.from, wave.to), width = wave.width})
	var echo := _ring(wave.from, 32, wave.echo_color, wave.width.x)
	echo.position = _snap(at)
	echo.z_index = Z_BLAST
	add_child(echo)
	fading.append({node = echo, age = 0.0, life = wave.echo_time, ring = Vector2(wave.from, wave.echo_to), width = wave.width})


func _spark(at: Vector2, velocity: Vector2, life: float, drag: float, gravity: float) -> void:
	var colors := [Color("#FFF4E8"), Color("#FFB070"), Color("#FF5A3C")]
	var spark := Polygon2D.new()
	spark.polygon = PackedVector2Array([Vector2(-TEXEL * 1.5, -TEXEL / 2.0), Vector2(TEXEL * 1.5, -TEXEL / 2.0),
		Vector2(TEXEL * 1.5, TEXEL / 2.0), Vector2(-TEXEL * 1.5, TEXEL / 2.0)])
	spark.color = colors[rng.randi_range(0, colors.size() - 1)]
	spark.material = additive
	spark.z_index = Z_SPARKS
	add_child(spark)
	flying.append({node = spark, at = at, velocity = velocity, drag = drag, gravity = gravity, age = 0.0, life = life})


func _ember(at: Vector2) -> void:
	if _final(&"ember"):
		_particle(&"ember", at, Z_SPARKS)
		return
	var spec := Layout.BEAM_V2_EMBERS
	var colors: Array = spec.colors
	var ember := _square(TEXEL * (2.0 if rng.randf() < 0.4 else 1.0), colors[rng.randi_range(0, colors.size() - 1)], true)
	ember.z_index = Z_SPARKS
	add_child(ember)
	flying.append({node = ember, at = at, velocity = Vector2(rng.randf_range(-spec.drift, spec.drift),
		-rng.randf_range(spec.rise.x, spec.rise.y)), drag = 1.5, gravity = -20.0, age = 0.0,
		life = rng.randf_range(spec.life.x, spec.life.y), colors = colors})


func _smoke(at: Vector2) -> void:
	if _final(&"smoke"):
		_particle(&"smoke", at, Z_SMOKE)
		return
	var spec := Layout.BEAM_V2_SMOKE
	var puff := Node2D.new()
	puff.z_index = Z_SMOKE
	for n in 3:
		var blob := _circle(rng.randf_range(0.55, 0.85), 10, spec.color, false)
		blob.position = Vector2(rng.randf_range(-0.5, 0.5), rng.randf_range(-0.35, 0.2))
		puff.add_child(blob)
	var lit := _circle(0.5, 10, spec.lit, true)
	lit.position = Vector2(0, 0.35)
	puff.add_child(lit)
	add_child(puff)
	var radius := rng.randf_range(spec.radius.x, spec.radius.y)
	flying.append({node = puff, at = at, velocity = Vector2(rng.randf_range(-12.0, 12.0), -spec.rise), drag = 0.5,
		gravity = 0.0, age = 0.0, life = rng.randf_range(spec.life.x, spec.life.y), grow = Vector2(radius * 0.4, radius)})


# A final particle: its sheet's frames over its life, flying straight at its speed.
func _particle(kind: StringName, at: Vector2, z: int) -> void:
	var spec: Dictionary = Layout.BEAM_V2_ART[kind]
	var bit := _sheet(kind, self, at)
	bit.z_index = z
	flying.append({node = bit, at = at, velocity = Vector2(rng.randf_range(spec.speed_x.x, spec.speed_x.y),
		rng.randf_range(spec.speed_y.x, spec.speed_y.y)), drag = 0.0, gravity = 0.0, age = 0.0,
		life = rng.randf_range(spec.life.x, spec.life.y), frames = spec.frames})


# The scorch's floor line, BEAM_HEIGHT under the beam's from the goal on, in the floor node's px; the drawn scorch
# follows the head down it.
func _build_scorch(points: PackedVector2Array) -> void:
	var lift := Vector2(0, Layout.BEAM_HEIGHT)
	scorch_route = PackedVector2Array()
	for i in range(1, points.size()):
		scorch_route.append(scorch.to_local(points[i] + lift))
	scorch_along = [0.0]
	for i in range(1, scorch_route.size()):
		scorch_along.append(scorch_along[i - 1] + scorch_route[i - 1].distance_to(scorch_route[i]))
	if _final(&"scorch"):
		return
	var spec := Layout.BEAM_V2_SCORCH
	scorch_char = Line2D.new()
	scorch_char.width = spec.width
	scorch_char.default_color = spec.char
	scorch_char.joint_mode = Line2D.LINE_JOINT_SHARP
	scorch.add_child(scorch_char)
	scorch_glow = Line2D.new()
	scorch_glow.width = spec.glow_width
	scorch_glow.default_color = spec.glow
	scorch_glow.joint_mode = Line2D.LINE_JOINT_SHARP
	scorch_glow.material = additive
	scorch.add_child(scorch_glow)


func _scorch_to(length: float) -> void:
	if not is_instance_valid(scorch_char) or scorch_route.size() < 2 or length <= 0.0:
		return
	var points := _line_to(scorch_route, scorch_along, length)
	scorch_char.points = points
	scorch_glow.points = points


# The final scorch, laid whole on the floor line as the beam dissipates.
func _lay_scorch() -> void:
	if not is_instance_valid(scorch) or scorch_route.size() < 2:
		return
	var art: Dictionary = Layout.BEAM_V2_ART[&"scorch"]
	scorch_line = Line2D.new()
	scorch_line.name = "Scorch"
	scorch_line.points = scorch_route
	scorch_line.width = art.frame.y * Layout.SCALE
	scorch_line.joint_mode = Line2D.LINE_JOINT_SHARP
	_tile(scorch_line, scorch_frames[0])
	scorch.add_child(scorch_line)
	scorch_clock = 0.0


func _splat() -> void:
	if not is_instance_valid(scorch) or scorch_route.is_empty():
		return
	var spec := Layout.BEAM_V2_SCORCH
	var splat := Polygon2D.new()
	var points := PackedVector2Array()
	for i in 16:
		points.append(_snap(Vector2.from_angle(TAU * i / 16.0) * spec.splat * rng.randf_range(0.75, 1.0)))
	splat.polygon = points
	splat.color = spec.char
	splat.position = scorch_route[scorch_route.size() - 1]
	scorch.add_child(splat)


#THE FINAL ART

# A final piece on `parent` at `at` (its local px), its pivot there: the sheet over its glow, if that is in, both
# stepped by _show_frame() and mirrored by _flip() together.
func _sheet(piece: StringName, parent: Node2D, at: Vector2) -> Node2D:
	var art: Dictionary = Layout.BEAM_V2_ART[piece]
	var holder := Node2D.new()
	holder.name = String(piece).to_pascal_case()
	holder.position = _snap(at)
	parent.add_child(holder)
	if _glow(piece):
		holder.add_child(_sprite(String(piece) + "_glow", art, true))
	holder.add_child(_sprite(String(piece), art, false))
	return holder


func _sprite(sheet: String, art: Dictionary, glowing: bool) -> Sprite2D:
	var sprite := Sprite2D.new()
	sprite.texture = _texture(sheet)
	sprite.hframes = art.frames
	sprite.centered = false
	sprite.offset = -art.pivot
	sprite.scale = Vector2.ONE * Layout.SCALE
	if glowing:
		sprite.material = additive
	return sprite


func _play(node: Node2D, piece: StringName, loop: bool) -> void:
	var art: Dictionary = Layout.BEAM_V2_ART[piece]
	playing.append({node = node, age = 0.0, time = art.frame_time, frames = art.frames, loop = loop})


func _show_frame(holder: Node2D, frame: int) -> void:
	for sprite: Sprite2D in holder.get_children():
		sprite.frame = frame


func _flip(holder: Node2D, h: bool, v: bool) -> void:
	for sprite: Sprite2D in holder.get_children():
		sprite.flip_h = h
		sprite.flip_v = v


func _tile(line: Line2D, texture: Texture2D) -> void:
	line.texture = texture
	line.texture_mode = Line2D.LINE_TEXTURE_TILE
	line.texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED


func _final(piece: StringName) -> bool:
	if not finals.has(piece):
		finals[piece] = Layout.beam_final(piece)
	return finals[piece]


func _glow(piece: StringName) -> bool:
	var key := StringName(String(piece) + "_glow")
	if not finals.has(key):
		finals[key] = Layout.beam_glow_final(piece)
	return finals[key]


func _texture(sheet: String) -> Texture2D:
	if not textures.has(sheet):
		textures[sheet] = Layout.beam_texture(sheet)
	return textures[sheet]


# A strip's frames cut apart, for a line to tile one at a time.
func _frames_of(sheet: String, size: Vector2, count: int) -> Array[Texture2D]:
	var image := _texture(sheet).get_image()
	var out: Array[Texture2D] = []
	for k in count:
		out.append(ImageTexture.create_from_image(image.get_region(Rect2i(Vector2i(int(size.x) * k, 0), Vector2i(size)))))
	return out


#SHAPES (px, on the texel grid)

func _line(width: float, color: Color, z: int, glowing: bool) -> Line2D:
	var line := Line2D.new()
	line.width = width
	line.default_color = color
	line.joint_mode = Line2D.LINE_JOINT_SHARP
	line.z_index = z
	if glowing:
		line.material = additive
	add_child(line)
	return line


func _circle(radius: float, points: int, color: Color, glowing: bool) -> Polygon2D:
	var shape := Polygon2D.new()
	shape.polygon = _circle_points(radius, points)
	shape.color = color
	if glowing:
		shape.material = additive
	return shape


func _circle_points(radius: float, points: int) -> PackedVector2Array:
	var out := PackedVector2Array()
	for i in points:
		out.append(Vector2.from_angle(TAU * i / points) * radius)
	return out


func _ring(radius: float, points: int, color: Color, width: float) -> Line2D:
	var ring := Line2D.new()
	ring.points = _circle_points(radius, points)
	ring.closed = true
	ring.width = width
	ring.default_color = color
	ring.material = additive
	return ring


func _square(size: float, color: Color, glowing := false) -> Polygon2D:
	var half := size / 2.0
	var shape := Polygon2D.new()
	shape.polygon = PackedVector2Array([Vector2(-half, -half), Vector2(half, -half), Vector2(half, half),
		Vector2(-half, half)])
	shape.color = color
	if glowing:
		shape.material = additive
	return shape


# A streak `size.y` px long and `size.x` across, along +x, glowing.
func _streak(size: Vector2, color: Color) -> Polygon2D:
	var shape := Polygon2D.new()
	shape.polygon = PackedVector2Array([Vector2(-size.y / 2.0, -size.x / 2.0), Vector2(size.y / 2.0, -size.x / 2.0),
		Vector2(size.y / 2.0, size.x / 2.0), Vector2(-size.y / 2.0, size.x / 2.0)])
	shape.color = color
	shape.material = additive
	return shape


func _diamond(radius: float, color: Color) -> Polygon2D:
	var shape := Polygon2D.new()
	shape.polygon = PackedVector2Array([Vector2(-radius, 0), Vector2(0, -radius), Vector2(radius, 0), Vector2(0, radius)])
	shape.color = color
	return shape


func _star(points: int, radius: float, inner: float, color: Color, glowing: bool) -> Polygon2D:
	var shape := Polygon2D.new()
	var out := PackedVector2Array()
	for i in points * 2:
		out.append(_snap(Vector2.from_angle(TAU * i / (points * 2)) * (radius if i % 2 == 0 else radius * inner)))
	shape.polygon = out
	shape.color = color
	if glowing:
		shape.material = additive
	return shape


# The head's flare, pointing along +x: a spearhead with its tail streaming back.
func _flare(size: Vector2, color: Color, glowing: bool) -> Polygon2D:
	var shape := Polygon2D.new()
	var length := size.x
	var half := size.y / 2.0
	shape.polygon = PackedVector2Array([Vector2(length * 0.5, 0), Vector2(length * 0.28, -half * 0.55),
		Vector2(-length * 0.06, -half), Vector2(-length * 0.5, -half * 0.4), Vector2(-length * 0.62, 0),
		Vector2(-length * 0.5, half * 0.4), Vector2(-length * 0.06, half), Vector2(length * 0.28, half * 0.55)])
	shape.color = color
	if glowing:
		shape.material = additive
	return shape


#ALONG THE ROUTE (local px)

func _line_to(points: PackedVector2Array, lengths: Array[float], reach: float) -> PackedVector2Array:
	var out := PackedVector2Array([points[0]])
	for i in range(1, points.size()):
		if lengths[i] <= reach:
			out.append(points[i])
			continue
		var span := lengths[i] - lengths[i - 1]
		var weight := (reach - lengths[i - 1]) / span if span > 0.0 else 1.0
		out.append(points[i - 1].lerp(points[i], weight))
		break
	if out.size() < 2:
		out.append(out[0])
	return out


func _line_between(from: float, to: float) -> PackedVector2Array:
	var out := PackedVector2Array([_point_at(from)])
	for i in range(1, route.size()):
		if along[i] > from and along[i] < to:
			out.append(route[i])
	out.append(_point_at(to))
	return out


func _point_at(reach: float) -> Vector2:
	for i in range(1, route.size()):
		if reach <= along[i]:
			var span := along[i] - along[i - 1]
			return route[i - 1].lerp(route[i], (reach - along[i - 1]) / span if span > 0.0 else 1.0)
	return route[route.size() - 1]


# A point up to `within` px off the line either side, `reach` px along it.
func _off_line(reach: float, within: float) -> Vector2:
	return _point_at(reach) + _way_at(reach).orthogonal() * rng.randf_range(-within, within)


func _way_at(reach: float) -> Vector2:
	for i in range(1, route.size()):
		if reach <= along[i]:
			return (route[i] - route[i - 1]).normalized()
	return (route[route.size() - 1] - route[route.size() - 2]).normalized() if route.size() > 1 else Vector2.ZERO


func _snap(point: Vector2) -> Vector2:
	return (point / TEXEL).round() * TEXEL


func _snap_len(length: float) -> float:
	return roundf(length / TEXEL) * TEXEL
