extends Node2D

# One wave of Liam's tsunami (LiamTsunami): a band across half the ring, WAVE height tall, rolling down from the top of
# the screen at `speed`. It resolves its own hits with MattTrueshotScript's latch: the player's hurtbox against the band
# answers once a pass, and a parried wave rolls on whole through them (parry_pass_through). A hit carries the player
# down the ring for `carry_time` (its host's carry_player). The hit's origin is the player's own hurtbox centre, so any
# facing answers it.
#
# Its node stands on the band's front edge (its bottom) at the seam end: x is the band's inner edge, y is `front_y`,
# and it is drawn as the left wave, mirrored for the right. The swell behind the top rope shows while its front is still
# above the rope. It adds its share of water to the flood once (spend), as its front crashes on the bottom rope or as
# it collapses harmlessly short of it (collapse()), and finishes once its top edge is past the bottom rope. Everything
# it times runs in _physics_process.
#
# It hurts WAVE_SEAM_INSET short of its seam end (hit_band; band() is what is drawn). A pass the player dodged and then
# crossed the seam out of, out of this wave's half, counts as answered: no later hit, and while they still touch it
# it drifts them on out sideways (CROSS_DRIFT).

const Layout := preload("res://Scripts/LiamArtLayout.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")

const WAVE_ID := &"liam_tsunami"
# Past this the whole band is off the bottom of the screen and it frees itself.
const SCREEN_BOTTOM := 1080.0
# px/s a crossed pass pushes the player on out toward their new half: 2 frames at most.
const CROSS_DRIFT := 600.0

# Set before it enters the tree.
var side := &"left"
var front_y := 0.0
var height := 360.0
var speed := 600.0
var carry_time := 0.35
var rope_top := 114.0
var rope_bottom := 969.0
var water_share := 1.0 / 12.0
var player: CharacterBody2D
# Its state machine (carry_player) and the flood its water goes to.
var host: Node
var flood: Node
var fx_layer: Node2D

var hitbox: Area2D
var hit_shape: CollisionShape2D
var art: Node2D
var tell: Node2D
var latched := false
# This pass has been dodged once already: logged once, however many frames the dash's immunity covers.
var dodged := false
# This pass was dodged and the player has crossed the seam out of this wave's half: answered, and drifted on out.
var crossed := false
# For a test: passes answered that way.
var crossings := 0
var collapsing := false
var collapse_left := 0.0
var collapse_time := 0.3
var finished := false
var spent := false
var clock := 0.0
# Everything the player's hurtbox said about it, for a test: each resolved result in order.
var results: Array[int] = []

var crest_tiles: Array[Sprite2D] = []
# The crest loop's frames, counted off its sheet.
var crest_frames := Layout.WAVE_CREST_FRAMES
# The body under it, stepping with the crest's frame (fx_v2's shimmer), and its own count.
var body_tiles: Array[Sprite2D] = []
var body_frames := 1
var tell_sheet: Sprite2D
var collapse_sheet: Sprite2D


func _ready() -> void:
	_build_hitbox()
	_build_art()
	_place()


# The band drawn, in world px.
func band() -> Rect2:
	var across := Layout.wave_x(side)
	return Rect2(across.x, front_y - height, across.y - across.x, height)


# The band it hurts: WAVE_SEAM_INSET short of its seam end.
func hit_band() -> Rect2:
	var drawn := band()
	var inset := Layout.WAVE_SEAM_INSET
	return Rect2(drawn.position.x + (inset if side == &"right" else 0.0), drawn.position.y, drawn.size.x - inset, drawn.size.y)


func is_telling() -> bool:
	return not collapsing and front_y < rope_top


# Every wave still rolling collapses harmlessly over `time`: nothing of it can land from this frame on.
func collapse(time: float) -> void:
	if collapsing or finished:
		return
	collapsing = true
	collapse_time = maxf(time, 0.01)
	collapse_left = collapse_time
	hitbox.set_deferred("monitoring", false)
	tell.visible = false
	if collapse_sheet != null:
		art.visible = false
		collapse_sheet.visible = true
		collapse_sheet.frame = 0


func _physics_process(delta: float) -> void:
	clock += delta
	if collapsing:
		collapse_left -= delta
		_show_collapse()
		if collapse_left <= 0.0:
			_spend()
			queue_free()
		return
	front_y += speed * delta
	_place()
	if not spent and front_y >= rope_bottom:
		_spend()
	_animate()
	_resolve_hits()
	if not finished and front_y - height >= rope_bottom:
		finished = true
		hitbox.set_deferred("monitoring", false)
		_spend()
	if front_y - height >= SCREEN_BOTTOM:
		queue_free()


func _place() -> void:
	var across := Layout.wave_x(side)
	var inner: float = across.y if side == &"left" else across.x
	global_position = Vector2(inner, front_y)
	tell.global_position = Vector2(inner, rope_top)
	tell.visible = is_telling()


func _spend() -> void:
	if spent:
		return
	spent = true
	if is_instance_valid(flood):
		flood.add_water(water_share)


#ITS HITS

func _resolve_hits() -> void:
	if not is_instance_valid(player) or finished:
		return
	var touching := false
	var near := false
	for area in hitbox.get_overlapping_areas():
		if area == player.hurtBox:
			touching = true
		elif player.is_dodge_ghost(area):
			near = true
	if touching:
		if crossed:
			player.add_drift(Vector2(-CROSS_DRIFT if side == &"right" else CROSS_DRIFT, 0.0))
			return
		if latched:
			return
		if dodged and _crossed_out():
			latched = true
			crossed = true
			crossings += 1
			player.add_drift(Vector2(-CROSS_DRIFT if side == &"right" else CROSS_DRIFT, 0.0))
			return
		var result: int = player.receive_hit(_hit())
		# A dodge doesn't latch: a wave is taller than a dash can clear, so a player still in it once the dash's
		# immunity is over is hit.
		if result == HitInfo.Result.DODGED:
			if not dodged:
				dodged = true
				results.append(result)
			return
		if result != HitInfo.Result.IGNORED:
			results.append(result)
			latched = true
			if result == HitInfo.Result.HIT and is_instance_valid(host):
				host.carry_player(Vector2(0, speed), carry_time)
			elif result == HitInfo.Result.PARRIED:
				_splash()
		return
	latched = false
	dodged = false
	crossed = false
	if near:
		player.receive_near_miss(_hit())


# The player's middle is over the seam, out of this wave's half.
func _crossed_out() -> bool:
	var centre: float = player.hurtBox.get_node("CollisionShape2D").global_position.x
	return centre < Layout.SEAM_X if side == &"right" else centre > Layout.SEAM_X


func _hit() -> RefCounted:
	var centre: Vector2 = player.hurtBox.get_node("CollisionShape2D").global_position
	return HitInfo.make(WAVE_ID, hitbox, centre, null)


#WHAT IS DRAWN

func _build_hitbox() -> void:
	hitbox = Area2D.new()
	hitbox.name = "Hitbox"
	hitbox.collision_layer = 0
	hitbox.collision_mask = 2
	hitbox.monitorable = false
	hit_shape = CollisionShape2D.new()
	var rect := RectangleShape2D.new()
	var across := Layout.wave_x(side)
	rect.size = Vector2(across.y - across.x - Layout.WAVE_SEAM_INSET, height)
	hit_shape.shape = rect
	# The node is on the band's inner edge, so the band lies to its left, or its right for the right wave; it hurts from
	# WAVE_SEAM_INSET in from that edge.
	var direction := -1.0 if side == &"left" else 1.0
	hit_shape.position = Vector2(direction * (Layout.WAVE_SEAM_INSET + rect.size.x / 2.0), -height / 2.0)
	hitbox.add_child(hit_shape)
	add_child(hitbox)


# Drawn as the left wave, running left from the seam end; the right one is its mirror.
func _build_art() -> void:
	art = Node2D.new()
	art.name = "Art"
	add_child(art)
	tell = Node2D.new()
	tell.name = "Tell"
	tell.top_level = true
	add_child(tell)
	if side == &"right":
		art.scale.x = -1.0
		tell.scale.x = -1.0
	if Layout.final_wave():
		_build_final()
	else:
		_build_placeholder()


func _build_final() -> void:
	var width: float = Layout.wave_x(side).y - Layout.wave_x(side).x
	var tile: Vector2 = Layout.WAVE_TILE * Layout.SCALE
	var body: Texture2D = load(Layout.WAVE_BODY_SHEET)
	var crest: Texture2D = load(Layout.WAVE_CREST_SHEET)
	var crest_rows: float = Layout.WAVE_TILE.y - Layout.WAVE_BODY_ROWS
	crest_frames = Layout.strip_count(Layout.WAVE_CREST_SHEET, Vector2(Layout.WAVE_TILE.x, crest_rows))
	body_frames = Layout.strip_count(Layout.WAVE_BODY_SHEET, Vector2(Layout.WAVE_TILE.x, Layout.WAVE_BODY_ROWS))
	var covered := 0.0
	# Whole tiles from the seam end, then the rest of a tile's last columns at the rope end, so it runs on seamlessly.
	while covered < width - 0.5:
		var texels: float = minf(Layout.WAVE_TILE.x, roundf((width - covered) / Layout.SCALE))
		var from_x: float = Layout.WAVE_TILE.x - texels
		var left := -(covered + texels * Layout.SCALE)
		var body_tile := _tile(body, Rect2(from_x, 0, texels, Layout.WAVE_BODY_ROWS), Vector2(left, -height))
		body_tile.set_meta(&"from_x", from_x)
		art.add_child(body_tile)
		body_tiles.append(body_tile)
		var crest_tile := _tile(crest, Rect2(from_x, 0, texels, crest_rows), Vector2(left, -crest_rows * Layout.SCALE))
		crest_tile.set_meta(&"from_x", from_x)
		art.add_child(crest_tile)
		crest_tiles.append(crest_tile)
		covered += texels * Layout.SCALE
	if ResourceLoader.exists(Layout.WAVE_TELL_SHEET):
		tell_sheet = _strip(Layout.WAVE_TELL_SHEET, Layout.WAVE_TELL_FRAME)
		tell_sheet.offset = Vector2(-Layout.WAVE_TELL_FRAME.x, -Layout.WAVE_TELL_FRAME.y)
		tell.add_child(tell_sheet)
	else:
		_build_placeholder_tell()
	if ResourceLoader.exists(Layout.WAVE_COLLAPSE_SHEET):
		collapse_sheet = _strip(Layout.WAVE_COLLAPSE_SHEET, Layout.WAVE_COLLAPSE_FRAME)
		collapse_sheet.offset = Vector2(-Layout.WAVE_COLLAPSE_FRAME.x, -Layout.WAVE_COLLAPSE_FRAME.y)
		collapse_sheet.scale.x *= -1.0 if side == &"right" else 1.0
		collapse_sheet.visible = false
		add_child(collapse_sheet)


func _tile(texture: Texture2D, region: Rect2, at: Vector2) -> Sprite2D:
	var sprite := Sprite2D.new()
	sprite.texture = texture
	sprite.centered = false
	sprite.region_enabled = true
	sprite.region_rect = region
	sprite.scale = Vector2.ONE * Layout.SCALE
	sprite.position = at
	return sprite


# A strip of frames standing on its bottom-right corner (the seam end, drawn as the left wave).
func _strip(path: String, frame: Vector2) -> Sprite2D:
	var sprite := Sprite2D.new()
	var texture: Texture2D = load(path)
	sprite.texture = texture
	sprite.hframes = roundi(texture.get_width() / frame.x)
	sprite.centered = false
	sprite.scale = Vector2.ONE * Layout.SCALE
	return sprite


func _build_placeholder() -> void:
	var look: Dictionary = Layout.PLACEHOLDER_WAVE
	var width: float = Layout.wave_x(side).y - Layout.wave_x(side).x
	var water := Polygon2D.new()
	water.polygon = Layout.rect_polygon(Rect2(-width, -height, width, height))
	water.color = look.body
	art.add_child(water)
	var crest := Polygon2D.new()
	crest.polygon = Layout.rect_polygon(Rect2(-width, -look.crest_depth, width, look.crest_depth))
	crest.color = look.crest
	art.add_child(crest)
	var foam_x: float = -width + look.foam_spacing / 2.0
	while foam_x < 0.0:
		var foam := Polygon2D.new()
		foam.polygon = Layout.ellipse(Vector2(look.foam_size * 2.0, look.foam_size), 12)
		foam.position = Vector2(foam_x, -look.crest_depth - look.foam_size)
		foam.color = look.foam
		art.add_child(foam)
		foam_x += look.foam_spacing
	_build_placeholder_tell()


func _build_placeholder_tell() -> void:
	var look: Dictionary = Layout.PLACEHOLDER_WAVE
	var width: float = Layout.wave_x(side).y - Layout.wave_x(side).x
	var swell := Polygon2D.new()
	var points := PackedVector2Array()
	var steps := 24
	for i in steps + 1:
		var along := float(i) / steps
		points.append(Vector2(-width * along, -look.tell_height * (0.6 + 0.4 * sin(along * PI * 6.0))))
	points.append(Vector2(-width, 0))
	points.append(Vector2(0, 0))
	swell.polygon = points
	swell.color = look.tell
	tell.add_child(swell)


func _animate() -> void:
	var frame := int(clock / Layout.WAVE_FRAME_TIME) % crest_frames
	for tile in crest_tiles:
		var region: Rect2 = tile.region_rect
		region.position.x = frame * Layout.WAVE_TILE.x + float(tile.get_meta(&"from_x"))
		tile.region_rect = region
	for tile in body_tiles:
		var region: Rect2 = tile.region_rect
		region.position.x = (frame % body_frames) * Layout.WAVE_TILE.x + float(tile.get_meta(&"from_x"))
		tile.region_rect = region
	if tell_sheet != null and tell.visible:
		tell_sheet.frame = int(clock / Layout.WAVE_FRAME_TIME) % tell_sheet.hframes
	elif tell.visible:
		tell.modulate.a = 0.7 + 0.3 * sin(clock * TAU * 3.0)


func _show_collapse() -> void:
	var done := 1.0 - collapse_left / collapse_time
	if collapse_sheet != null:
		collapse_sheet.frame = mini(int(done * collapse_sheet.hframes), collapse_sheet.hframes - 1)
		return
	art.scale.y = maxf(1.0 - done, 0.05)
	art.modulate.a = 1.0 - done


func _splash() -> void:
	if fx_layer == null:
		return
	var at: Vector2 = player.hurtBox.get_node("CollisionShape2D").global_position
	var fx := Node2D.new()
	fx_layer.add_child(fx)
	fx.global_position = at.round()
	if ResourceLoader.exists(Layout.WAVE_SPLASH_SHEET) and Layout.final_wave():
		var sheet := Sprite2D.new()
		var texture: Texture2D = load(Layout.WAVE_SPLASH_SHEET)
		sheet.texture = texture
		sheet.hframes = roundi(texture.get_width() / Layout.WAVE_SPLASH_FRAME.x)
		sheet.scale = Vector2.ONE * Layout.SCALE
		sheet.offset = Layout.WAVE_SPLASH_FRAME / 2.0 - Layout.WAVE_SPLASH_PIVOT
		fx.add_child(sheet)
		var play := fx.create_tween()
		var times := Layout.spread(Layout.WAVE_SPLASH_TIMES, sheet.hframes)
		for i in sheet.hframes:
			play.tween_callback(sheet.set_frame.bind(i))
			play.tween_interval(times[i])
		play.tween_callback(fx.queue_free)
		return
	var look: Dictionary = Layout.PLACEHOLDER_WAVE
	var ring := Line2D.new()
	ring.points = Layout.ellipse(Vector2.ONE * look.splash_radius, 16)
	ring.closed = true
	ring.width = 6.0
	ring.default_color = look.splash
	fx.add_child(ring)
	var burst := fx.create_tween().set_parallel()
	burst.tween_property(fx, "scale", Vector2.ONE * 1.8, 0.26).from(Vector2.ONE * 0.4)
	burst.tween_property(fx, "modulate:a", 0.0, 0.26)
	burst.chain().tween_callback(fx.queue_free)
