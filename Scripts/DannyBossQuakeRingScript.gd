extends Node2D

# The quake ring every landing of Danny's Sumo Smash (DannyBossSlams) sends rolling out from under him:
# BixbyQuakeRingScript's ring, copied with Danny's own art (DannyBossArtLayout's quake_ring, the mat itself
# lifted in a ridge and torn along a crack), that art's visibility boxes, and his numbers. The rest is Bixby's
# ring, read off BixbyCombinedArtLayout: the ellipse on his feet flattened the way the floor is drawn, the
# segments spaced round its screen arc and snapped to the texel grid, the band that hurts, and the ropes it
# runs on under. Like Bixby's it reports its own hits rather than joining "enemy projectile", which also hits
# dashing players, and all of it runs in _physics_process, so a freeze holds it.
# It is born inside his seated footprint and hurts nobody for its first ARM_TIME, so it can't land in the
# same breath as its slam: it reaches a player at least that long after the impact, and a dash goes through
# it. It never hurts the player whose feet were inside its own slam's footprint at the impact (`spared`: the
# slam itself answered them), nor a player whose actions are locked (rooted by his worms, or held in a cut).

const CombinedLayout := preload("res://Scripts/BixbyCombinedArtLayout.gd")
const Layout := preload("res://Scripts/DannyBossArtLayout.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")

const RING_ID := &"danny_quake_ring"
# Each row's ground as [half-width, top, bottom] in px from the pivot, and the top of what its crack throws
# up, off Danny's sheet (the FX artist's): CombinedLayout.ring_segment_shown() reads Bixby's.
const RING_GROUND_BOXES := [[45, -18, 9], [48, -27, 18], [42, -30, 27], [42, -36, 39], [42, -45, 42],
	[36, -42, 45], [30, -42, 45]]
const RING_CREST_TOPS := [-42, -45, -45, -45, -45, -45, -45]
# Under his rear, well inside the footprint's 198 px either side.
const START_RADIUS := 92.0
const ARM_TIME := 0.25

# Set by the attack before the ring is added on the landing's contact point.
var speed := 240.0
var player: CharacterBody2D
var spared := false

var radius := START_RADIUS
var elapsed := 0.0
var spec: Dictionary = Layout.fx(&"quake_ring")
var tiles: Array[Sprite2D] = []
# The ring art's segments for the count it has now ([floor angle, row, flip], CombinedLayout.ring_segments),
# worked out again only when the count grows.
var segments := []


# Its segments sort with whoever stands in front of or behind them, as Bixby's scene has it.
func _init() -> void:
	y_sort_enabled = true


func _ready() -> void:
	_place_segments()


func _physics_process(delta: float) -> void:
	elapsed += delta
	radius += speed * delta
	_place_segments()
	if elapsed >= ARM_TIME:
		_damage_player()
	if _has_passed_the_floor():
		queue_free()


# The ring art round the ellipse: each segment standing on its pivot, snapped to the texel grid on screen,
# so it sorts with whoever stands in front of or behind it.
func _place_segments() -> void:
	var count := CombinedLayout.ring_segment_count(radius)
	if count != segments.size():
		segments = CombinedLayout.ring_segments(count)
	if tiles.size() < count:
		var sheet: Texture2D = load(spec.texture)
		while tiles.size() < count:
			var tile := Sprite2D.new()
			tile.texture = sheet
			tile.hframes = spec.hframes
			tile.vframes = spec.vframes
			tile.scale = Vector2.ONE * Layout.SCALE
			tiles.append(tile)
			add_child(tile)
	var frames: int = spec.hframes
	var beat := int(elapsed / spec.frame_time)
	var snap := CombinedLayout.RING_SNAP
	for i in count:
		var tile := tiles[i]
		var theta: float = segments[i][0]
		var row: int = segments[i][1]
		var at := global_position + Vector2(cos(theta), sin(theta) * CombinedLayout.FLOOR_FLATTEN) * radius
		at = (at / snap).round() * snap
		tile.position = at - global_position
		tile.frame = row * frames + (beat + i) % frames
		tile.flip_h = segments[i][2]
		tile.offset = Layout.flipped_offset(spec.offset, tile.flip_h)
		tile.visible = segment_shown(at, row)


# Whether a segment standing at `at` on screen, on sheet row `row`, is drawn: its ground inside the rope art
# at the sides and the bottom, which draws over it there, and its crest under the top rope.
static func segment_shown(at: Vector2, row: int) -> bool:
	var ground: Array = RING_GROUND_BOXES[row]
	var ropes := CombinedLayout.RING_ROPE_ART
	return at.x - ground[0] >= ropes.position.x and at.x + ground[0] <= ropes.end.x \
		and at.y + ground[2] <= ropes.end.y and at.y + RING_CREST_TOPS[row] >= ropes.position.y


# Whether the band covers the foot of the player's hurtbox, worked out on the floor: the box is stretched
# back out of the flattening, so the ellipse is a circle again.
func _damage_player() -> void:
	if spared or not is_instance_valid(player) or player.is_action_locked:
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
	player.receive_hit(HitInfo.make(RING_ID, self, global_position))


func _has_passed_the_floor() -> bool:
	var area := Rect2(CombinedLayout.RING_HURT_AREA.position - global_position, CombinedLayout.RING_HURT_AREA.size)
	for corner in _corners(area):
		if Vector2(corner.x, corner.y / CombinedLayout.FLOOR_FLATTEN).length() > radius - CombinedLayout.RING_HURT_HALF_WIDTH:
			return false
	return true


func _corners(rect: Rect2) -> Array[Vector2]:
	return [rect.position, Vector2(rect.end.x, rect.position.y), Vector2(rect.position.x, rect.end.y), rect.end]
