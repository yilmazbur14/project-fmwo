extends Node2D

# The quake ring beast Bixby's pounds send out from under him, and the ones he keeps sending while he spins:
# bixby_quake_wave.png's crest stood upright round an ellipse on his feet, flattened the way the floor is
# drawn, growing slowly out across the floor to the ropes. Only its band hurts, so a player it has passed
# is safe from it, and dashing through it is the dodge. Like Eric's ring it reports its own hits rather
# than joining "enemy projectile", which also hits dashing players. All of it runs in _physics_process, so
# a freeze holds it.

const CombinedLayout := preload("res://Scripts/BixbyCombinedArtLayout.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")

# How fast its radius grows, in px of the floor a second, and the player to hurt: set by the attack before
# the ring is added, on his feet.
var speed := 240.0
var player: CharacterBody2D
# The rest is Bixby's ring unless whoever adds it sets its own (Liam's fire rings): the id its hits carry, its sheet
# (frames across, rows by tangent, each frame frame_size), where its art is shown and where its band hurts.
var attack_id := &"bixby_quake_ring"
var sheet_path := CombinedLayout.RING_SHEET
var frames := CombinedLayout.RING_FRAMES
var rows := CombinedLayout.RING_ROWS
var frame_size := Vector2(40, 32)
var shown_rect := CombinedLayout.RING_ROPE_ART
var hurt_rect := CombinedLayout.RING_HURT_AREA
# At max_radius it stops hurting and dies over die_time: through its dying rows (rows..2 rows - 1) if its sheet has
# them, faded out if not. INF grows on to the ropes, as Bixby's always has.
var max_radius := INF
var die_time := 0.0
var dying := false
var die_clock := 0.0
# Beast Bixby's own rings (his send_quake_ring): born under his claws, so on the frame it is born the band reaches all
# the way in, and a player standing between his claws is caught by the pound itself. Without it they were left inside
# every ring for good: the playtest of 2026-10-04 found his feet a spot no ring of his ever reached.
var hurts_inside_at_birth := false
var born := false

var radius := CombinedLayout.RING_START_RADIUS
var elapsed := 0.0
var tiles: Array[Sprite2D] = []
# The ring art's segments for the count it has now ([floor angle, row, flip], CombinedLayout.ring_segments),
# worked out again only when the count grows.
var segments := []


func _ready() -> void:
	_draw()


func _physics_process(delta: float) -> void:
	elapsed += delta
	if dying:
		die_clock += delta
		_draw()
		if die_clock >= die_time:
			queue_free()
		return
	radius += speed * delta
	if radius >= max_radius:
		radius = max_radius
		extinguish(die_time)
		return
	_draw()
	_damage_player()
	born = true
	if _has_passed_the_floor():
		queue_free()


# Put out where it is: it stops hurting at once and dies over `time`.
func extinguish(time := 0.2) -> void:
	if dying:
		return
	dying = true
	die_time = maxf(time, 0.0)
	die_clock = 0.0
	_draw()


func _draw() -> void:
	if CombinedLayout.USE_FINAL_RING:
		_place_segments()
	else:
		_place_tiles()


# The ring art round the ellipse: each segment standing on its pivot, snapped to the texel grid on screen,
# so it sorts with whoever stands in front of or behind it.
func _place_segments() -> void:
	var count := CombinedLayout.ring_segment_count(radius)
	if count != segments.size():
		segments = CombinedLayout.ring_segments(count)
	if tiles.size() < count:
		var sheet: Texture2D = load(sheet_path)
		while tiles.size() < count:
			var tile := Sprite2D.new()
			tile.texture = sheet
			tile.hframes = frames
			tile.vframes = maxi(roundi(sheet.get_height() / frame_size.y), rows)
			tile.scale = Vector2(CombinedLayout.SCALE, CombinedLayout.SCALE)
			tiles.append(tile)
			add_child(tile)
	var beat := int(elapsed / CombinedLayout.RING_FRAME_TIME)
	var snap := CombinedLayout.RING_SNAP
	# Dying: through its dying rows once if the sheet has them, the living ones faded out if not.
	var dying_rows := dying and not tiles.is_empty() and tiles[0].vframes >= 2 * rows
	var dying_frame := mini(int(die_clock / maxf(die_time, 0.001) * frames), frames - 1)
	if dying and not dying_rows:
		modulate.a = clampf(1.0 - die_clock / maxf(die_time, 0.001), 0.0, 1.0)
	for i in count:
		var tile := tiles[i]
		var theta: float = segments[i][0]
		var row: int = segments[i][1]
		var at := global_position + Vector2(cos(theta), sin(theta) * CombinedLayout.FLOOR_FLATTEN) * radius
		at = (at / snap).round() * snap
		tile.position = at - global_position
		if dying_rows:
			tile.frame = (row + rows) * frames + dying_frame
		else:
			tile.frame = row * frames + (beat + i) % frames
		tile.flip_h = segments[i][2]
		tile.visible = CombinedLayout.ring_segment_shown(at, row, shown_rect)


# The crest tiles round the ellipse, each standing on its ground point so it sorts with whoever stands in
# front of or behind it. Each is a frame on from its neighbour, as the wave's tiles were, so the crest runs
# round the ring.
func _place_tiles() -> void:
	var count := ceili(TAU * radius / CombinedLayout.RING_TILE_SPACING)
	while tiles.size() < count:
		var tile := Sprite2D.new()
		CombinedLayout.dress(tile, CombinedLayout.WAVE_SHEET, CombinedLayout.WAVE_FRAME_SIZE,
			CombinedLayout.WAVE_OFFSET)
		tiles.append(tile)
		add_child(tile)
	var beat := int(elapsed / CombinedLayout.WAVE_FRAME_TIME)
	for i in count:
		var tile := tiles[i]
		var angle := TAU * i / count
		tile.position = (Vector2(cos(angle), sin(angle) * CombinedLayout.FLOOR_FLATTEN) * radius).round()
		tile.frame = (beat + i) % tile.hframes
		tile.visible = CombinedLayout.RING_VISIBLE_AREA.has_point(tile.global_position)


# Whether the band covers the foot of the player's hurtbox, worked out on the floor: the box is stretched
# back out of the flattening, so the ellipse is a circle again.
func _damage_player() -> void:
	if not is_instance_valid(player):
		return
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	var half: Vector2 = shape.shape.size * shape.global_scale.abs() / 2.0
	var foot := CombinedLayout.RING_FOOT_HEIGHT
	var box := Rect2(shape.global_position + Vector2(-half.x, half.y - foot) - global_position, Vector2(half.x * 2.0, foot))
	var on_floor := Rect2(box.position.x, box.position.y / CombinedLayout.FLOOR_FLATTEN,
		box.size.x, box.size.y / CombinedLayout.FLOOR_FLATTEN)
	var nearest := Vector2.ZERO.clamp(on_floor.position, on_floor.end).length()
	var farthest := 0.0
	for corner in _corners(on_floor):
		farthest = maxf(farthest, corner.length())
	var half_width := CombinedLayout.RING_HURT_HALF_WIDTH
	var inner := -INF if hurts_inside_at_birth and not born else radius - half_width
	if nearest > radius + half_width or farthest < inner:
		return
	player.receive_hit(HitInfo.make(attack_id, self, global_position))


func _has_passed_the_floor() -> bool:
	var area := Rect2(hurt_rect.position - global_position, hurt_rect.size)
	for corner in _corners(area):
		if Vector2(corner.x, corner.y / CombinedLayout.FLOOR_FLATTEN).length() > radius - CombinedLayout.RING_HURT_HALF_WIDTH:
			return false
	return true


func _corners(rect: Rect2) -> Array[Vector2]:
	return [rect.position, Vector2(rect.end.x, rect.position.y), Vector2(rect.position.x, rect.end.y), rect.end]
