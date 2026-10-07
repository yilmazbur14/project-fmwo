extends Node2D

# Liam's air blast, drawn: the burst on his staff tip as it goes off (burst), opening down at the player, and the trail
# on the launched player's feet for as long as the launch lasts (trail): the gust's, or with `kind` &"water" the water
# blast's (attack 4). Each is its own node on his FxLayer and frees itself; its times are node-bound tweens, so a pause
# or a finisher's freeze holds it.

const Layout := preload("res://Scripts/LiamArtLayout.gd")

# The player a trail follows.
var target: Node2D


static func burst(layer: Node2D, at: Vector2) -> Node2D:
	var gust := new()
	gust.name = "GustBurst"
	layer.add_child(gust)
	gust.global_position = at.round()
	gust._play_burst()
	return gust


static func trail(layer: Node2D, player: Node2D, time: float, kind := &"gust") -> Node2D:
	var gust := new()
	gust.name = "GustTrail" if kind == &"gust" else "WaterTrail"
	gust.target = player
	layer.add_child(gust)
	if kind == &"water":
		gust._play_water_trail(time)
	else:
		gust._play_trail(time)
	return gust


func _process(_delta: float) -> void:
	if target == null:
		return
	if not is_instance_valid(target):
		queue_free()
		return
	global_position = target.global_position.round() + Vector2(0, 42)


func _play_burst() -> void:
	var play := create_tween()
	if Layout.final_gust():
		var sheet := _sheet(Layout.GUST_BURST_SHEET, Layout.GUST_BURST_FRAME, Layout.GUST_BURST_PIVOT)
		var times := Layout.spread(Layout.GUST_BURST_TIMES, sheet.hframes)
		for i in sheet.hframes:
			play.tween_callback(sheet.set_frame.bind(i))
			play.tween_interval(times[i])
		play.tween_callback(queue_free)
		return
	var look: Dictionary = Layout.PLACEHOLDER_GUST
	var ring := Line2D.new()
	ring.points = Layout.ellipse(Vector2.ONE * look.radius, 20)
	ring.closed = true
	ring.width = 6.0
	ring.default_color = look.ring
	add_child(ring)
	for i in look.spokes:
		var spoke := Line2D.new()
		var angle: float = PI * (0.15 + 0.7 * float(i) / float(look.spokes - 1))
		spoke.points = PackedVector2Array([Vector2.from_angle(angle) * 20.0, Vector2.from_angle(angle) * look.radius * 1.6])
		spoke.width = 4.0
		spoke.default_color = look.burst
		add_child(spoke)
	play.set_parallel()
	play.tween_property(self, "scale", Vector2.ONE * 1.4, 0.3).from(Vector2.ONE * 0.5)
	play.tween_property(self, "modulate:a", 0.0, 0.3)
	play.chain().tween_callback(queue_free)


func _play_trail(time: float) -> void:
	_process(0.0)
	var play := create_tween()
	if Layout.final_gust():
		var sheet := _sheet(Layout.GUST_TRAIL_SHEET, Layout.GUST_TRAIL_FRAME, Layout.GUST_TRAIL_PIVOT)
		var steps := maxi(ceili(time / Layout.GUST_TRAIL_FRAME_TIME), 1)
		for i in steps:
			play.tween_callback(sheet.set_frame.bind(i % sheet.hframes))
			play.tween_interval(Layout.GUST_TRAIL_FRAME_TIME)
		play.tween_callback(queue_free)
		return
	var look: Dictionary = Layout.PLACEHOLDER_GUST
	for i in look.trail_lines:
		var line := Line2D.new()
		var x: float = (float(i) - (look.trail_lines - 1) / 2.0) * 18.0
		line.points = PackedVector2Array([Vector2(x, -100.0), Vector2(x, -100.0 - look.trail_length)])
		line.width = 5.0
		line.default_color = look.trail
		add_child(line)
	play.tween_property(self, "modulate:a", 0.0, time).from(1.0)
	play.tween_callback(queue_free)


func _play_water_trail(time: float) -> void:
	_process(0.0)
	var play := create_tween()
	var spec: Dictionary = Layout.WATER_TRAIL
	if Layout.final_lunge(spec.sheet):
		var sheet := _sheet(spec.sheet, spec.frame, spec.pivot)
		var steps := maxi(ceili(time / spec.frame_time), 1)
		for i in steps:
			play.tween_callback(sheet.set_frame.bind(i % sheet.hframes))
			play.tween_interval(spec.frame_time)
		play.tween_callback(queue_free)
		return
	var look: Dictionary = Layout.PLACEHOLDER_WATER_TRAIL
	for i in look.lines:
		var line := Line2D.new()
		var x: float = (float(i) - (look.lines - 1) / 2.0) * 18.0
		line.points = PackedVector2Array([Vector2(x, -90.0), Vector2(x, -90.0 - look.length)])
		line.width = 6.0
		line.default_color = look.color
		add_child(line)
	play.tween_property(self, "modulate:a", 0.0, time).from(1.0)
	play.tween_callback(queue_free)


func _sheet(path: String, frame: Vector2, pivot: Vector2) -> Sprite2D:
	var sheet := Sprite2D.new()
	var texture: Texture2D = load(path)
	sheet.texture = texture
	sheet.hframes = roundi(texture.get_width() / frame.x)
	sheet.scale = Vector2.ONE * Layout.SCALE
	sheet.offset = frame / 2.0 - pivot
	add_child(sheet)
	return sheet
