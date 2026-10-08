extends Node2D

# The water result's wave in Jordan's Elemental Wheel (JordanComboWheel; every number JordanWheelLayout's): LiamWave's
# pattern laid over the god fight's whole floor, and thin (WAVE_H) so a dash carries a player standing in its way through
# it. Its swell shows along the floor's top edge for WAVE_TELL, then it rolls down the floor at WAVE_SPEED and its
# collapse splashes along the bottom edge once its back edge is off the floor (cleared). Drawn as Liam's own wave: his
# crest's WAVE_CREST_ROWS under the last WAVE_BODY_ROWS of his body, which is exactly what hurts.
#
# Its node stands on the band's front edge at the floor's left wall, so it y-sorts with the player by its front. It
# resolves its own hits, LiamWave's way: the player's hurtbox against the band answers once a pass (a HIT latches it),
# a dash's immunity carries them through (DODGED), and the band reaching only a dash's ghost is a near miss, once.
# The attack drives it (drive), so a pause and a finisher's freeze hold it.

const Layout := preload("res://Scripts/JordanWheelLayout.gd")
const LiamArtLayout := preload("res://Scripts/LiamArtLayout.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")

# Set before it enters the tree.
var player: CharacterBody2D
var boss: Node2D
var fx_layer: Node2D

var front_y: float = Layout.FLOOR.position.y
var rolling := false
var clock := 0.0
var latched := false
var dodged := false
var near_missed := false
var splashed := false
# For a test: every result its band resolved to, in order, and when it rolled.
var results: Array[int] = []
var rolled_at := -1.0

var art: Node2D
var tell: Node2D
var crest_tiles: Array[Sprite2D] = []
var body_tiles: Array[Sprite2D] = []
var tell_tiles: Array[Sprite2D] = []
var crest_frames := 1
var body_frames := 1
var tell_frames := 1


func _ready() -> void:
	art = Node2D.new()
	art.name = "Art"
	add_child(art)
	tell = Node2D.new()
	tell.name = "Swell"
	tell.top_level = true
	add_child(tell)
	if LiamArtLayout.final_wave():
		_build_final()
	else:
		_build_placeholder()
	art.visible = false
	_place()


# The band drawn and hurting, world px.
func band() -> Rect2:
	var floor_rect: Rect2 = Layout.FLOOR
	return Rect2(floor_rect.position.x, front_y - Layout.WAVE_H, floor_rect.size.x, Layout.WAVE_H)


# Its back edge is off the floor's bottom edge.
func cleared() -> bool:
	return front_y - Layout.WAVE_H >= Layout.FLOOR.end.y


# `t` seconds from the result's start: the swell until WAVE_TELL, then the roll.
func drive(t: float) -> void:
	clock = t
	if t >= Layout.WAVE_TELL:
		if not rolling:
			rolling = true
			rolled_at = t
			art.visible = true
			tell.visible = false
		front_y = Layout.FLOOR.position.y + (t - Layout.WAVE_TELL) * Layout.WAVE_SPEED
	_place()
	_animate()
	if rolling and not cleared():
		_resolve_hits()
	if cleared() and not splashed:
		splashed = true
		_splash()


func _place() -> void:
	global_position = Vector2(Layout.FLOOR.position.x, front_y).round()
	tell.global_position = Vector2(Layout.FLOOR.position.x, Layout.FLOOR.position.y)


#ITS HITS

func _resolve_hits() -> void:
	if not is_instance_valid(player):
		return
	var water := band()
	if water.intersects(_rect_of(player.hurtBox)):
		if latched:
			return
		var result: int = player.receive_hit(_hit())
		if result == HitInfo.Result.DODGED:
			if not dodged:
				dodged = true
				results.append(result)
			return
		if result != HitInfo.Result.IGNORED:
			results.append(result)
			latched = true
		return
	if not near_missed and player.dodge_ghost_position() != Vector2.INF and water.intersects(_rect_of(player.dodge_ghost)):
		near_missed = true
		player.receive_near_miss(_hit())


func _hit() -> RefCounted:
	var centre: Vector2 = player.hurtBox.get_node("CollisionShape2D").global_position
	return HitInfo.make(Layout.WAVE_ID, self, centre, boss)


func _rect_of(area: Area2D) -> Rect2:
	var shape: CollisionShape2D = area.get_node("CollisionShape2D")
	return shape.global_transform * shape.shape.get_rect()


#WHAT IS DRAWN

# Liam's crest under the last rows of his body, a tile at a time from the left wall, the last cut to the floor's width.
func _build_final() -> void:
	var width: float = Layout.FLOOR.size.x
	var tile_x: float = LiamArtLayout.WAVE_TILE.x
	var crest_rows: float = LiamArtLayout.WAVE_TILE.y - LiamArtLayout.WAVE_BODY_ROWS
	crest_frames = LiamArtLayout.strip_count(LiamArtLayout.WAVE_CREST_SHEET, Vector2(tile_x, crest_rows))
	body_frames = LiamArtLayout.strip_count(LiamArtLayout.WAVE_BODY_SHEET, Vector2(tile_x, LiamArtLayout.WAVE_BODY_ROWS))
	var crest: Texture2D = load(LiamArtLayout.WAVE_CREST_SHEET)
	var body: Texture2D = load(LiamArtLayout.WAVE_BODY_SHEET)
	var crest_px := Layout.WAVE_CREST_ROWS * LiamArtLayout.SCALE
	var covered := 0.0
	while covered < width - 0.5:
		var texels := minf(tile_x, roundf((width - covered) / LiamArtLayout.SCALE))
		var body_tile := _tile(body, Rect2(0, LiamArtLayout.WAVE_BODY_ROWS - Layout.WAVE_BODY_ROWS, texels, Layout.WAVE_BODY_ROWS),
			Vector2(covered, -Layout.WAVE_H))
		art.add_child(body_tile)
		body_tiles.append(body_tile)
		var crest_tile := _tile(crest, Rect2(0, crest_rows - Layout.WAVE_CREST_ROWS, texels, Layout.WAVE_CREST_ROWS),
			Vector2(covered, -crest_px))
		art.add_child(crest_tile)
		crest_tiles.append(crest_tile)
		covered += texels * LiamArtLayout.SCALE
	if ResourceLoader.exists(LiamArtLayout.WAVE_TELL_SHEET):
		var swell: Texture2D = load(LiamArtLayout.WAVE_TELL_SHEET)
		var frame: Vector2 = LiamArtLayout.WAVE_TELL_FRAME
		tell_frames = LiamArtLayout.strip_count(LiamArtLayout.WAVE_TELL_SHEET, frame)
		covered = 0.0
		while covered < width - 0.5:
			var texels := minf(frame.x, roundf((width - covered) / LiamArtLayout.SCALE))
			var piece := _tile(swell, Rect2(0, 0, texels, frame.y), Vector2(covered, -frame.y * LiamArtLayout.SCALE))
			tell.add_child(piece)
			tell_tiles.append(piece)
			covered += texels * LiamArtLayout.SCALE
	else:
		_build_placeholder_tell()


func _tile(texture: Texture2D, region: Rect2, at: Vector2) -> Sprite2D:
	var sprite := Sprite2D.new()
	sprite.texture = texture
	sprite.centered = false
	sprite.region_enabled = true
	sprite.region_rect = region
	sprite.set_meta(&"from_x", region.position.x)
	sprite.scale = Vector2.ONE * LiamArtLayout.SCALE
	sprite.position = at
	return sprite


func _build_placeholder() -> void:
	var look: Dictionary = LiamArtLayout.PLACEHOLDER_WAVE
	var width: float = Layout.FLOOR.size.x
	var water := Polygon2D.new()
	water.polygon = LiamArtLayout.rect_polygon(Rect2(0, -Layout.WAVE_H, width, Layout.WAVE_H))
	water.color = look.body
	art.add_child(water)
	var crest := Polygon2D.new()
	crest.polygon = LiamArtLayout.rect_polygon(Rect2(0, -look.crest_depth, width, look.crest_depth))
	crest.color = look.crest
	art.add_child(crest)
	_build_placeholder_tell()


func _build_placeholder_tell() -> void:
	var look: Dictionary = LiamArtLayout.PLACEHOLDER_WAVE
	var width: float = Layout.FLOOR.size.x
	var swell := Polygon2D.new()
	var points := PackedVector2Array()
	var steps := 48
	for i in steps + 1:
		var along := float(i) / steps
		points.append(Vector2(width * along, -look.tell_height * (0.6 + 0.4 * sin(along * PI * 18.0))))
	points.append(Vector2(width, 0))
	points.append(Vector2(0, 0))
	swell.polygon = points
	swell.color = look.tell
	tell.add_child(swell)


func _animate() -> void:
	var frame := int(clock / LiamArtLayout.WAVE_FRAME_TIME)
	for tile in crest_tiles:
		var region: Rect2 = tile.region_rect
		region.position.x = (frame % crest_frames) * LiamArtLayout.WAVE_TILE.x + float(tile.get_meta(&"from_x"))
		tile.region_rect = region
	for tile in body_tiles:
		var region: Rect2 = tile.region_rect
		region.position.x = (frame % body_frames) * LiamArtLayout.WAVE_TILE.x + float(tile.get_meta(&"from_x"))
		tile.region_rect = region
	for tile in tell_tiles:
		var region: Rect2 = tile.region_rect
		region.position.x = (frame % tell_frames) * LiamArtLayout.WAVE_TELL_FRAME.x + float(tile.get_meta(&"from_x"))
		tile.region_rect = region
	if tell_tiles.is_empty() and tell.visible:
		tell.modulate.a = 0.7 + 0.3 * sin(clock * TAU * 3.0)


# The collapse: splashes along the floor's bottom edge as the back edge leaves it.
func _splash() -> void:
	if fx_layer == null:
		return
	var floor_rect: Rect2 = Layout.FLOOR
	var spacing := floor_rect.size.x / Layout.WAVE_SPLASHES
	for i in Layout.WAVE_SPLASHES:
		var at := Vector2(floor_rect.position.x + spacing * (i + 0.5), floor_rect.end.y).round()
		var fx := Node2D.new()
		fx.name = "WaveSplash"
		fx.add_to_group(Layout.GodLayout.HAZARD_GROUP)
		fx_layer.add_child(fx)
		fx.global_position = at
		if LiamArtLayout.final_wave() and ResourceLoader.exists(LiamArtLayout.WAVE_SPLASH_SHEET):
			var sheet := Sprite2D.new()
			var texture: Texture2D = load(LiamArtLayout.WAVE_SPLASH_SHEET)
			sheet.texture = texture
			sheet.hframes = roundi(texture.get_width() / LiamArtLayout.WAVE_SPLASH_FRAME.x)
			sheet.scale = Vector2.ONE * LiamArtLayout.SCALE
			sheet.offset = LiamArtLayout.WAVE_SPLASH_FRAME / 2.0 - LiamArtLayout.WAVE_SPLASH_PIVOT
			fx.add_child(sheet)
			var play := fx.create_tween()
			var times := LiamArtLayout.spread(LiamArtLayout.WAVE_SPLASH_TIMES, sheet.hframes)
			for k in sheet.hframes:
				play.tween_callback(sheet.set_frame.bind(k))
				play.tween_interval(times[k])
			play.tween_callback(fx.queue_free)
			continue
		var look: Dictionary = LiamArtLayout.PLACEHOLDER_WAVE
		var ring := Line2D.new()
		ring.points = LiamArtLayout.ellipse(Vector2.ONE * look.splash_radius, 16)
		ring.closed = true
		ring.width = 6.0
		ring.default_color = look.splash
		fx.add_child(ring)
		var burst := fx.create_tween().set_parallel()
		burst.tween_property(fx, "scale", Vector2.ONE * 1.8, Layout.WAVE_SPLASH_TIME).from(Vector2.ONE * 0.4)
		burst.tween_property(fx, "modulate:a", 0.0, Layout.WAVE_SPLASH_TIME)
		burst.chain().tween_callback(fx.queue_free)
