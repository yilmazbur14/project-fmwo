extends Node2D

# Liam's element effects, drawn: static spawners on his FxLayer in LiamGust's pattern, each its own node that frees
# itself and steps its own clock in _physics_process, so a pause or a finisher's freeze holds it. All cosmetic.
#   downdraft  his cold breath's blow down the ring while it blows: pale streaks falling from his floor line; stop()
#              lets the ones in the air finish, then it frees itself
#   blow_gust  the gust off his mouth that raises the tornados (attack 3)
#   fire_streak  a streak of fire flying from his staff to a tornado's base over `time`, which lights it
#   puff       a poof of steam on his feet (attack 4: his vanish, a whiff, his teleports); `reverse` plays it backward
#   wake       the steam a lunge tears through, swept back behind him from where he started it
#   sky_fire   Bixby's fire pouring down from over the screen onto the impaled player's head and splashing there;
#              stop(tail) lets its tail fall onto them over `tail`, then it frees itself
#   flames     flames on the player while the sky fire burns them; to_embers() when it stops, extinguish() when the
#              water hits them: a hiss of steam and the embers dying, then it frees itself
#   water_jet  his jet from his staff tip to the player, reaching them over `time`, then gone as fast

const Layout := preload("res://Scripts/LiamArtLayout.gd")

# The player's feet off their centre, where the flames stand.
const FEET := Vector2(0, 42)

var kind := &""
var fall_speed := 0.0
var stopping := false
var spawn_left := 0.0
var streaks: Array[Node2D] = []
var ages: Array[float] = []
# Per streak: how long it lives (until its head reaches the bottom rope) and the frame it started on.
var lives: Array[float] = []
var first_frames: Array[int] = []
var random := RandomNumberGenerator.new()
# The player a sky fire, flames or a jet follows, and what it draws with.
var target: Node2D
var clock := 0.0
var sheet_spec := {}
var tiles: Array[Sprite2D] = []
var splash: Node2D
var column: Node2D
var column_mask: Polygon2D
var tail_time := 0.0
var tail_clock := 0.0
var jet_from := Vector2.ZERO
var jet_time := 0.0
var jet_body: Line2D
var jet_core: Line2D


static func downdraft(layer: Node2D, drift_speed: float) -> Node2D:
	var fx := new()
	fx.name = "Downdraft"
	fx.kind = &"downdraft"
	fx.fall_speed = drift_speed * Layout.DOWNDRAFT_SPEED_SCALE
	fx.random.randomize()
	layer.add_child(fx)
	fx.global_position = Vector2.ZERO
	return fx


static func blow_gust(layer: Node2D, mouth: Vector2, facing_left: bool) -> Node2D:
	var fx := new()
	fx.name = "BlowGust"
	layer.add_child(fx)
	fx.global_position = mouth.round()
	var play := fx.create_tween()
	if Layout.final_firestorm(Layout.BLOW_GUST_SHEET):
		var sheet := fx._sheet(Layout.BLOW_GUST_SHEET, Layout.BLOW_GUST_FRAME, Layout.BLOW_GUST_PIVOT)
		sheet.flip_h = facing_left
		for i in sheet.hframes:
			play.tween_callback(sheet.set_frame.bind(i))
			play.tween_interval(Layout.BLOW_GUST_TIME / sheet.hframes)
		play.tween_callback(fx.queue_free)
		return fx
	var look: Dictionary = Layout.PLACEHOLDER_BLOW_GUST
	for i in look.spokes:
		var spoke := Line2D.new()
		var angle: float = PI * (0.2 + 0.6 * float(i) / float(look.spokes - 1))
		spoke.points = PackedVector2Array([Vector2.from_angle(angle) * 12.0, Vector2.from_angle(angle) * look.radius * 2.0])
		spoke.width = 4.0
		spoke.default_color = look.color
		fx.add_child(spoke)
	play.set_parallel()
	play.tween_property(fx, "scale", Vector2.ONE * 1.6, Layout.BLOW_GUST_TIME).from(Vector2.ONE * 0.4)
	play.tween_property(fx, "modulate:a", 0.0, Layout.BLOW_GUST_TIME)
	play.chain().tween_callback(fx.queue_free)
	return fx


static func fire_streak(layer: Node2D, from: Vector2, to: Vector2, time: float) -> Node2D:
	var fx := new()
	fx.name = "FireStreak"
	layer.add_child(fx)
	fx.global_position = from.round()
	fx.rotation = (to - from).angle()
	if Layout.final_firestorm(Layout.FIRE_STREAK_SHEET):
		var sheet := fx._sheet(Layout.FIRE_STREAK_SHEET, Layout.FIRE_STREAK_FRAME, Layout.FIRE_STREAK_PIVOT)
		var cycle := fx.create_tween().set_loops()
		cycle.tween_interval(Layout.FIRE_STREAK_FRAME_TIME)
		cycle.tween_callback(func() -> void: sheet.frame = (sheet.frame + 1) % sheet.hframes)
	else:
		var look: Dictionary = Layout.PLACEHOLDER_FIRE_STREAK
		var line := Line2D.new()
		line.points = PackedVector2Array([Vector2(-look.length, 0), Vector2.ZERO])
		line.width = look.width
		line.default_color = look.color
		fx.add_child(line)
	var fly := fx.create_tween()
	fly.tween_property(fx, "global_position", to.round(), maxf(time, 0.01))
	fly.tween_callback(fx.queue_free)
	return fx


static func puff(layer: Node2D, feet: Vector2, reverse := false) -> Node2D:
	var fx := new()
	fx.name = "SteamPuff"
	layer.add_child(fx)
	fx.global_position = feet.round()
	var spec: Dictionary = Layout.STEAM_PUFF
	var play := fx.create_tween()
	if Layout.final_lunge(spec.sheet):
		var sheet := fx._sheet(spec.sheet, spec.frame, spec.pivot)
		var order := range(sheet.hframes)
		if reverse:
			order.reverse()
		for i in order:
			play.tween_callback(sheet.set_frame.bind(i))
			play.tween_interval(spec.time / sheet.hframes)
		play.tween_callback(fx.queue_free)
		return fx
	var look: Dictionary = Layout.PLACEHOLDER_PUFF
	var cloud := Polygon2D.new()
	cloud.polygon = Layout.ellipse(look.radii)
	cloud.color = look.color
	cloud.position = Vector2(0, -look.radii.y)
	fx.add_child(cloud)
	var small := Vector2.ONE * 0.4
	var big := Vector2.ONE * 1.5
	play.set_parallel()
	play.tween_property(fx, "scale", small if reverse else big, spec.time).from(big if reverse else small)
	play.tween_property(fx, "modulate:a", 1.0 if reverse else 0.0, spec.time).from(0.0 if reverse else 1.0)
	play.chain().tween_callback(fx.queue_free)
	return fx


static func wake(layer: Node2D, from: Vector2, to: Vector2) -> Node2D:
	var fx := new()
	fx.name = "LungeWake"
	layer.add_child(fx)
	fx.global_position = from.round()
	var spec: Dictionary = Layout.LUNGE_WAKE
	var leftward := to.x < from.x
	var play := fx.create_tween()
	if Layout.final_lunge(spec.sheet):
		var sheet := fx._sheet(spec.sheet, spec.frame, spec.pivot)
		if leftward:
			sheet.flip_h = true
			sheet.offset.x = -sheet.offset.x
		for i in sheet.hframes:
			play.tween_callback(sheet.set_frame.bind(i))
			play.tween_interval(spec.time / sheet.hframes)
		play.tween_callback(fx.queue_free)
		return fx
	var look: Dictionary = Layout.PLACEHOLDER_WAKE
	var back := 1.0 if leftward else -1.0
	for i in look.lines:
		var line := Line2D.new()
		var y: float = (float(i) - (look.lines - 1) / 2.0) * 16.0
		line.points = PackedVector2Array([Vector2(0, y), Vector2(back * look.length, y)])
		line.width = look.width
		line.default_color = look.color
		fx.add_child(line)
	play.tween_property(fx, "modulate:a", 0.0, spec.time).from(1.0)
	play.tween_callback(fx.queue_free)
	return fx


static func sky_fire(layer: Node2D, player: Node2D) -> Node2D:
	var fx := new()
	fx.name = "SkyFire"
	fx.kind = &"sky_fire"
	fx.target = player
	layer.add_child(fx)
	fx._build_sky_fire()
	fx._step_sky_fire(0.0)
	return fx


static func flames(layer: Node2D, player: Node2D) -> Node2D:
	var fx := new()
	fx.name = "PlayerFlames"
	fx.kind = &"flames"
	fx.target = player
	layer.add_child(fx)
	fx._show_flames(Layout.PLAYER_FLAMES, Layout.PLACEHOLDER_FLAMES.flame)
	fx._step_flames(0.0)
	return fx


static func water_jet(layer: Node2D, from: Vector2, player: Node2D, time: float) -> Node2D:
	var fx := new()
	fx.name = "WaterJet"
	fx.kind = &"water_jet"
	fx.target = player
	fx.jet_from = from.round()
	fx.jet_time = maxf(time, 0.01)
	layer.add_child(fx)
	fx.global_position = fx.jet_from
	fx._build_jet()
	fx._step_jet(0.0)
	return fx


# A downdraft lets the streaks in the air finish; a sky fire lets its tail fall onto the player over `tail`.
func stop(tail := 0.0) -> void:
	if kind == &"sky_fire":
		if stopping:
			return
		tail_time = maxf(tail, 0.01)
		tail_clock = 0.0
	stopping = true


# The sky fire has stopped: what it left on the player.
func to_embers() -> void:
	if kind == &"flames" and not stopping:
		_show_flames(Layout.PLAYER_EMBERS, Layout.PLACEHOLDER_FLAMES.ember)


# The water hit them: a hiss of steam round their feet, once, then nothing on them.
func extinguish() -> void:
	if kind != &"flames" or stopping:
		return
	stopping = true
	for child in get_children():
		child.queue_free()
	tiles.clear()
	modulate.a = 1.0
	var spec: Dictionary = Layout.EXTINGUISH
	var play := create_tween()
	if Layout.final_lunge(spec.sheet):
		var sheet := _sheet(spec.sheet, spec.frame, spec.pivot)
		for i in sheet.hframes:
			play.tween_callback(sheet.set_frame.bind(i))
			play.tween_interval(spec.time / sheet.hframes)
		play.tween_callback(queue_free)
		return
	var look: Dictionary = Layout.PLACEHOLDER_EXTINGUISH
	var burst := Polygon2D.new()
	burst.polygon = Layout.ellipse(Vector2(look.radius, look.radius * 0.6))
	burst.color = look.color
	burst.position = Vector2(0, -look.radius * 0.6)
	add_child(burst)
	play.set_parallel()
	play.tween_property(self, "scale", Vector2.ONE * 1.6, spec.time).from(Vector2.ONE * 0.6)
	play.tween_property(self, "modulate:a", 0.0, spec.time).from(1.0)
	play.chain().tween_callback(queue_free)


func _sheet(path: String, frame: Vector2, pivot: Vector2) -> Sprite2D:
	var sheet := Sprite2D.new()
	sheet.texture = load(path)
	sheet.hframes = Layout.strip_count(path, frame)
	sheet.scale = Vector2.ONE * Layout.SCALE
	sheet.offset = frame / 2.0 - pivot
	add_child(sheet)
	return sheet


func _physics_process(delta: float) -> void:
	match kind:
		&"downdraft":
			_step_downdraft(delta)
		&"sky_fire":
			_step_sky_fire(delta)
		&"flames":
			_step_flames(delta)
		&"water_jet":
			_step_jet(delta)


func _step_downdraft(delta: float) -> void:
	if not stopping:
		spawn_left -= delta
		while spawn_left <= 0.0:
			spawn_left += Layout.DOWNDRAFT_SPAWN_TIME
			_add_streak()
	for i in range(streaks.size() - 1, -1, -1):
		ages[i] += delta
		var streak := streaks[i]
		streak.position.y += fall_speed * delta
		# Full for the first DOWNDRAFT_SOLID of its life, then out by its end.
		var through := ages[i] / lives[i]
		streak.modulate.a = clampf((1.0 - through) / (1.0 - Layout.DOWNDRAFT_SOLID), 0.0, 1.0)
		var sheet := streak as Sprite2D
		if sheet:
			sheet.frame = (first_frames[i] + int(ages[i] / Layout.DOWNDRAFT_FRAME_TIME)) % sheet.hframes
		if through >= 1.0:
			streak.queue_free()
			streaks.remove_at(i)
			ages.remove_at(i)
			lives.remove_at(i)
			first_frames.remove_at(i)
	if stopping and streaks.is_empty():
		queue_free()


func _add_streak() -> void:
	var at := Vector2(random.randf_range(Layout.DOWNDRAFT_X.x, Layout.DOWNDRAFT_X.y), Layout.DOWNDRAFT_Y)
	var streak: Node2D
	# How far under the streak's node its head is: the sheet hangs its frame from the pivot, the stand-in ends on it.
	var head := 0.0
	var first_frame := 0
	if Layout.final_downdraft():
		var sheet := Sprite2D.new()
		sheet.texture = load(Layout.DOWNDRAFT_SHEET)
		sheet.hframes = Layout.strip_count(Layout.DOWNDRAFT_SHEET, Layout.DOWNDRAFT_FRAME)
		sheet.scale = Vector2.ONE * Layout.SCALE
		sheet.offset = Layout.DOWNDRAFT_FRAME / 2.0 - Layout.DOWNDRAFT_PIVOT
		first_frame = random.randi_range(0, sheet.hframes - 1)
		sheet.frame = first_frame
		head = (Layout.DOWNDRAFT_FRAME.y - Layout.DOWNDRAFT_PIVOT.y) * Layout.SCALE
		streak = sheet
	else:
		var look: Dictionary = Layout.PLACEHOLDER_DOWNDRAFT
		var line := Line2D.new()
		line.points = PackedVector2Array([Vector2(0, -look.length), Vector2.ZERO])
		line.width = look.width
		line.default_color = look.color
		streak = line
	add_child(streak)
	streak.position = to_local(at).round()
	streaks.append(streak)
	ages.append(0.0)
	lives.append(clampf((Layout.DOWNDRAFT_BOTTOM - Layout.DOWNDRAFT_Y - head) / maxf(fall_speed, 1.0), 0.05, Layout.DOWNDRAFT_LIFE))
	first_frames.append(first_frame)


#THE SKY FIRE

# The column's tiles stacked up from the player's head to over the screen, under a mask whose top is the column's
# tail, and the splash on the head; or the stand-in's band of fire.
func _build_sky_fire() -> void:
	column = Node2D.new()
	add_child(column)
	column_mask = Polygon2D.new()
	column_mask.clip_children = CanvasItem.CLIP_CHILDREN_ONLY
	column.add_child(column_mask)
	sheet_spec = Layout.sky_fire_column()
	var look: Dictionary = Layout.PLACEHOLDER_SKY_FIRE
	if sheet_spec.is_empty():
		var band := Polygon2D.new()
		band.polygon = Layout.rect_polygon(Rect2(-look.width / 2.0, -2000.0, look.width, 2000.0))
		band.color = look.edge
		column_mask.add_child(band)
		var core := Polygon2D.new()
		core.polygon = Layout.rect_polygon(Rect2(-look.core_width / 2.0, -2000.0, look.core_width, 2000.0))
		core.color = look.core
		column_mask.add_child(core)
	else:
		var tile_height: float = sheet_spec.frame.y * Layout.SCALE
		for i in ceili(1400.0 / tile_height):
			var tile := Sprite2D.new()
			tile.texture = load(sheet_spec.sheet)
			tile.hframes = Layout.strip_count(sheet_spec.sheet, sheet_spec.frame)
			tile.centered = false
			tile.offset = -sheet_spec.pivot
			tile.scale = Vector2.ONE * Layout.SCALE
			tile.position = Vector2(0, -tile_height * (i + 1))
			column_mask.add_child(tile)
			tiles.append(tile)
	var splash_spec: Dictionary = Layout.SKY_FIRE_SPLASH
	if Layout.final_lunge(splash_spec.sheet):
		splash = _sheet(splash_spec.sheet, splash_spec.frame, splash_spec.pivot)
	else:
		var blot := Polygon2D.new()
		blot.polygon = Layout.ellipse(look.splash)
		blot.color = look.core
		add_child(blot)
		splash = blot


func _step_sky_fire(delta: float) -> void:
	clock += delta
	if not is_instance_valid(target):
		queue_free()
		return
	var head := _head_top()
	global_position = head.round()
	var top := Layout.SKY_FIRE_TOP - global_position.y
	if stopping:
		tail_clock += delta
		if tail_clock >= tail_time:
			queue_free()
			return
		top = lerpf(top, 0.0, tail_clock / tail_time)
	column_mask.polygon = Layout.rect_polygon(Rect2(-200.0, top, 400.0, -top))
	if not tiles.is_empty():
		var step := int(clock / sheet_spec.frame_time)
		for i in tiles.size():
			tiles[i].frame = (step + i) % tiles[i].hframes
	var splash_sheet := splash as Sprite2D
	if splash_sheet:
		splash_sheet.frame = int(clock / Layout.SKY_FIRE_SPLASH.frame_time) % splash_sheet.hframes


# The top of the player's hurtbox over its middle: where the column lands on them.
func _head_top() -> Vector2:
	var shape: CollisionShape2D = target.hurtBox.get_node("CollisionShape2D")
	var half: Vector2 = shape.shape.size * shape.global_scale.abs() / 2.0
	return shape.global_position - Vector2(0, half.y)


#THE FLAMES ON THE PLAYER

func _show_flames(spec: Dictionary, colour: Color) -> void:
	for child in get_children():
		child.queue_free()
	tiles.clear()
	sheet_spec = spec
	if Layout.final_lunge(spec.sheet):
		tiles.append(_sheet(spec.sheet, spec.frame, spec.pivot))
		return
	var look: Dictionary = Layout.PLACEHOLDER_FLAMES
	var glow := Polygon2D.new()
	glow.polygon = Layout.ellipse(look.radii)
	glow.color = colour
	glow.position = Vector2(0, -look.radii.y)
	add_child(glow)


func _step_flames(delta: float) -> void:
	clock += delta
	if stopping:
		return
	if not is_instance_valid(target):
		queue_free()
		return
	global_position = (target.global_position + FEET).round()
	if not tiles.is_empty():
		tiles[0].frame = int(clock / sheet_spec.frame_time) % tiles[0].hframes
	else:
		modulate.a = 0.75 + 0.25 * sin(clock * TAU * 6.0)


#THE WATER JET

# The body tiles laid along x from the tip under a mask the jet's head pulls out, turned onto the player; or the
# stand-in's line.
func _build_jet() -> void:
	column = Node2D.new()
	add_child(column)
	column_mask = Polygon2D.new()
	column_mask.clip_children = CanvasItem.CLIP_CHILDREN_ONLY
	column.add_child(column_mask)
	sheet_spec = Layout.WATER_JET
	if Layout.final_lunge(sheet_spec.sheet):
		var tile_length: float = sheet_spec.frame.x * Layout.SCALE
		for i in ceili(2400.0 / tile_length):
			var tile := Sprite2D.new()
			tile.texture = load(sheet_spec.sheet)
			tile.hframes = Layout.strip_count(sheet_spec.sheet, sheet_spec.frame)
			tile.centered = false
			tile.offset = -sheet_spec.pivot
			tile.scale = Vector2.ONE * Layout.SCALE
			tile.position = Vector2(tile_length * i, 0)
			column_mask.add_child(tile)
			tiles.append(tile)
		return
	var look: Dictionary = Layout.PLACEHOLDER_JET
	jet_body = Line2D.new()
	jet_body.width = look.width
	jet_body.default_color = look.color
	column_mask.add_child(jet_body)
	jet_core = Line2D.new()
	jet_core.width = look.width * 0.35
	jet_core.default_color = look.core
	column_mask.add_child(jet_core)


func _step_jet(delta: float) -> void:
	clock += delta
	if not is_instance_valid(target) or clock >= 3.0 * jet_time:
		queue_free()
		return
	var to: Vector2 = target.global_position
	column.rotation = (to - jet_from).angle()
	var reach := jet_from.distance_to(to)
	# Out to the player over jet_time, held there as long again, then off the tip as fast.
	var end := reach * clampf(clock / jet_time, 0.0, 1.0)
	var start := reach * clampf((clock - 2.0 * jet_time) / jet_time, 0.0, 1.0)
	column_mask.polygon = Layout.rect_polygon(Rect2(start, -40.0, maxf(end - start, 0.0), 80.0))
	if not tiles.is_empty():
		var step := int(clock / sheet_spec.frame_time)
		for i in tiles.size():
			tiles[i].frame = (step + i) % tiles[i].hframes
	else:
		jet_body.points = PackedVector2Array([Vector2(start, 0), Vector2(end, 0)])
		jet_core.points = jet_body.points
