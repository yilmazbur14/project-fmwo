extends Node2D

# A stone pillar of the earth result in Jordan's Elemental Wheel (JordanComboWheel): Liam's own pillar sheet
# (LiamArtLayout's), driven lightly - it rises out of the floor (frames 0-4) with dust, stands, and crumbles (11-16)
# when Bixby slams it, then it is gone. Never solid and never punchable, so nothing can pen a dash in. Its node sits on
# its floor line on the Stage, so it y-sorts with the player. Until the sheet is in, Liam's stand-in column, slid up
# through the floor. It runs on physics steps, so a pause and a finisher's freeze hold it.

const LiamArtLayout := preload("res://Scripts/LiamArtLayout.gd")

enum Phase { DOWN, RISING, STANDING, CRUMBLING }

var phase := Phase.DOWN
var clock := 0.0
var time := 0.0
var sheet: Sprite2D
var column: Node2D
var mask: Polygon2D


func _ready() -> void:
	if LiamArtLayout.final_pillar():
		sheet = _sheet_sprite(LiamArtLayout.PILLAR_SHEET)
		add_child(sheet)
	else:
		_build_placeholder()
	visible = false


func rise(seconds: float) -> void:
	phase = Phase.RISING
	clock = 0.0
	time = maxf(seconds, 0.01)
	visible = true
	_puff()
	_show()


func crumble(seconds: float) -> void:
	if phase == Phase.CRUMBLING:
		return
	phase = Phase.CRUMBLING
	clock = 0.0
	time = maxf(seconds, 0.01)
	_puff()
	_show()


func _physics_process(delta: float) -> void:
	if phase == Phase.DOWN or phase == Phase.STANDING:
		return
	clock += delta
	if clock >= time:
		if phase == Phase.RISING:
			phase = Phase.STANDING
		else:
			queue_free()
			return
	_show()


func _show() -> void:
	var through := clampf(clock / time, 0.0, 1.0)
	if sheet != null:
		match phase:
			Phase.RISING:
				var frames: Array = LiamArtLayout.PILLAR_RISE_FRAMES
				sheet.frame = frames[mini(int(through * frames.size()), frames.size() - 1)]
			Phase.STANDING:
				sheet.frame = LiamArtLayout.PILLAR_STAND_FIRST
			Phase.CRUMBLING:
				var frames: Array = LiamArtLayout.PILLAR_CRUMBLE_FRAMES
				sheet.frame = frames[mini(int(through * frames.size()), frames.size() - 1)]
		return
	var risen := through if phase == Phase.RISING else (1.0 - through if phase == Phase.CRUMBLING else 1.0)
	column.position.y = roundf((1.0 - risen) * 58.0 * LiamArtLayout.SCALE)
	mask.position.y = -column.position.y


func _sheet_sprite(path: String) -> Sprite2D:
	var sprite := Sprite2D.new()
	var texture: Texture2D = load(path)
	sprite.texture = texture
	sprite.hframes = roundi(texture.get_width() / LiamArtLayout.PILLAR_FRAME.x)
	sprite.scale = Vector2.ONE * LiamArtLayout.SCALE
	sprite.offset = LiamArtLayout.PILLAR_FRAME / 2.0 - LiamArtLayout.PILLAR_PIVOT
	return sprite


# The column and its slab under a mask that ends on the floor line, so it comes up out of the floor.
func _build_placeholder() -> void:
	var look: Dictionary = LiamArtLayout.PLACEHOLDER_PILLAR
	var s := LiamArtLayout.SCALE
	column = Node2D.new()
	add_child(column)
	mask = Polygon2D.new()
	mask.polygon = LiamArtLayout.rect_polygon(Rect2(-40 * s, -80 * s, 80 * s, 80 * s))
	mask.clip_children = CanvasItem.CLIP_CHILDREN_ONLY
	column.add_child(mask)
	var half: float = look.width / 2.0 * s
	var face := Polygon2D.new()
	face.polygon = LiamArtLayout.rect_polygon(Rect2(-half, -46 * s, half * 2.0, 46 * s))
	face.color = look.stone
	mask.add_child(face)
	var cap_half: float = look.cap_width / 2.0 * s
	var cap := Polygon2D.new()
	cap.polygon = LiamArtLayout.rect_polygon(Rect2(-cap_half, -58 * s, cap_half * 2.0, look.cap_height * s))
	cap.color = look.cap
	mask.add_child(cap)
	for outline_of: Polygon2D in [face, cap]:
		var outline := Line2D.new()
		outline.points = outline_of.polygon
		outline.closed = true
		outline.width = s
		outline.default_color = look.edge
		mask.add_child(outline)


# Dust at the base: its sheet once in, puffs until then.
func _puff() -> void:
	if LiamArtLayout.final_pillar_dust():
		var dust := _sheet_sprite(LiamArtLayout.PILLAR_DUST_SHEET)
		add_child(dust)
		var play := dust.create_tween().set_process_mode(Tween.TWEEN_PROCESS_PHYSICS)
		for i in dust.hframes:
			play.tween_callback(dust.set_frame.bind(i))
			play.tween_interval(LiamArtLayout.PILLAR_DUST_FRAME_TIME)
		play.tween_callback(dust.queue_free)
		return
	for side: float in [-1.0, 1.0]:
		var puff := Polygon2D.new()
		puff.polygon = LiamArtLayout.ellipse(Vector2(30, 14))
		puff.color = LiamArtLayout.PLACEHOLDER_PILLAR.dust
		puff.position = Vector2(side * 50.0, -6.0)
		add_child(puff)
		var drift := puff.create_tween().set_parallel()
		drift.tween_property(puff, "position", Vector2(side * 110.0, -24.0), 0.4)
		drift.tween_property(puff, "modulate:a", 0.0, 0.4)
		drift.chain().tween_callback(puff.queue_free)
