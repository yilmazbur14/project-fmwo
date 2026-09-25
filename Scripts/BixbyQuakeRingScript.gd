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
	radius += speed * delta
	_draw()
	_damage_player()
	if _has_passed_the_floor():
		queue_free()


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
		var sheet: Texture2D = load(CombinedLayout.RING_SHEET)
		while tiles.size() < count:
			var tile := Sprite2D.new()
			tile.texture = sheet
			tile.hframes = CombinedLayout.RING_FRAMES
			tile.vframes = CombinedLayout.RING_ROWS
			tile.scale = Vector2(CombinedLayout.SCALE, CombinedLayout.SCALE)
			tiles.append(tile)
			add_child(tile)
	var beat := int(elapsed / CombinedLayout.RING_FRAME_TIME)
	var snap := CombinedLayout.RING_SNAP
	for i in count:
		var tile := tiles[i]
		var theta: float = segments[i][0]
		var row: int = segments[i][1]
		var at := global_position + Vector2(cos(theta), sin(theta) * CombinedLayout.FLOOR_FLATTEN) * radius
		at = (at / snap).round() * snap
		tile.position = at - global_position
		tile.frame = row * CombinedLayout.RING_FRAMES + (beat + i) % CombinedLayout.RING_FRAMES
		tile.flip_h = segments[i][2]
		tile.visible = CombinedLayout.ring_segment_shown(at, row)


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
	if nearest > radius + half_width or farthest < radius - half_width:
		return
	player.receive_hit(HitInfo.make(&"bixby_quake_ring", self, global_position))


func _has_passed_the_floor() -> bool:
	var area := Rect2(CombinedLayout.RING_HURT_AREA.position - global_position, CombinedLayout.RING_HURT_AREA.size)
	for corner in _corners(area):
		if Vector2(corner.x, corner.y / CombinedLayout.FLOOR_FLATTEN).length() > radius - CombinedLayout.RING_HURT_HALF_WIDTH:
			return false
	return true


func _corners(rect: Rect2) -> Array[Vector2]:
	return [rect.position, Vector2(rect.end.x, rect.position.y), Vector2(rect.position.x, rect.end.y), rect.end]
