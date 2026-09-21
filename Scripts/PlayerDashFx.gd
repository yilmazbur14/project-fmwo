extends Node

# How the dash looks and sounds in a fight on the player's feel_v2: afterimages left along
# the path, a puff of dust where it kicked off, and a whoosh. With feel_v2 off none of it happens.
# Everything is drawn beside the player rather than on him, as siblings of MainPlayer just before it.
# A fight that doesn't y-sort draws them over the mat and under him. In one that does they sort at
# their own depth but never ahead of him, and nowhere he can stand sorts as high as the floor layers
# at y 101, so they stay over those too. Being outside his branch also lets a finisher's freeze hold
# them with the rest of the fight, and every fade is a tween on the effect itself, so a hit-stop holds
# them too.

const DefenseHypeArtLayout := preload("res://Scripts/DefenseHypeArtLayout.gd")

# In a y-sorted fight an effect never sorts closer than this many px behind the player's sprite.
const SORT_BEHIND := 1.0

@onready var player: CharacterBody2D = get_parent()
@onready var sfx_player: AudioStreamPlayer = player.get_node("DashSfxPlayer")

# Every live effect as [node, where it is drawn, the y it would sort at on its own, its base offset].
var drawn: Array = []
# Along the current dash: px covered, where the next afterimage falls and how many have.
var travelled := 0.0
var next_ghost := 0.0
var ghosts := 0
# His sprite as the dash kicked off. Every afterimage copies it: the dash's last step lands after he
# has already dropped into his landing pose, and a copy of that would show him crouched and leaned.
var pose := {}

static var dust_sheet: ImageTexture
static var dust_origin := Vector2i.ZERO


func _ready() -> void:
	player.dash_stepped.connect(_on_dash_stepped)
	var sound := DefenseHypeArtLayout.DASH_WHOOSH_SFX
	sfx_player.stream = load(sound.stream)
	sfx_player.pitch_scale = sound.pitch
	sfx_player.volume_db = sound.volume_db


# The player moves in physics, so this is where the sort catches up with him before the frame is drawn.
func _process(_delta: float) -> void:
	var player_sort: float = player.sprite.global_position.y
	for i in range(drawn.size() - 1, -1, -1):
		if not is_instance_valid(drawn[i][0]):
			drawn.remove_at(i)
			continue
		_place(drawn[i], player_sort)


func _on_dash_stepped(from: Vector2, to: Vector2, kick_off: bool) -> void:
	if not player.feel_v2:
		return
	if kick_off:
		travelled = 0.0
		next_ghost = 0.0
		ghosts = 0
		pose = _pose()
		_spawn_dust(from, player.direction)
		sfx_player.play()
	var count := DefenseHypeArtLayout.DASH_GHOST_COUNT
	var spacing: float = player.DODGE_SPEED * player.dodge_time / count
	var step := from.distance_to(to)
	while ghosts < count and next_ghost < travelled + step:
		_spawn_ghost(from.lerp(to, (next_ghost - travelled) / step), ghosts)
		ghosts += 1
		next_ghost += spacing
	travelled += step


# His sprite's frame, and where it draws and sorts from his body origin.
func _pose() -> Dictionary:
	var source: Sprite2D = player.sprite
	var body := player.global_position
	return {
		"texture": source.texture,
		"hframes": source.hframes,
		"vframes": source.vframes,
		"frame": source.frame,
		"flip_h": source.flip_h,
		"flip_v": source.flip_v,
		"centered": source.centered,
		"scale": source.global_scale,
		"drawn_from": source.global_position + source.offset * source.global_scale - body,
		"sorts_from": source.global_position.y - body.y,
	}


# His sprite as the dash kicked off, drawn and sorted as it would be with his body at `at`.
func _spawn_ghost(at: Vector2, index: int) -> void:
	var ghost := Sprite2D.new()
	ghost.texture = pose.texture
	ghost.hframes = pose.hframes
	ghost.vframes = pose.vframes
	ghost.frame = pose.frame
	ghost.flip_h = pose.flip_h
	ghost.flip_v = pose.flip_v
	ghost.centered = pose.centered
	ghost.scale = pose.scale
	var alpha := DefenseHypeArtLayout.DASH_GHOST_ALPHA
	var count := DefenseHypeArtLayout.DASH_GHOST_COUNT
	ghost.modulate = DefenseHypeArtLayout.DASH_GHOST_TINT
	ghost.modulate.a = lerpf(alpha.x, alpha.y, clampf(float(index) / maxi(count - 1, 1), 0.0, 1.0))
	_add_beside_player(ghost, (at + pose.drawn_from).round(), at.y + pose.sorts_from, Vector2.ZERO)
	var fade := ghost.create_tween()
	fade.tween_property(ghost, "modulate:a", 0.0, DefenseHypeArtLayout.DASH_GHOST_FADE_TIME)
	fade.tween_callback(ghost.queue_free)


func _spawn_dust(at: Vector2, heading: Vector2) -> void:
	var spec := DefenseHypeArtLayout.DASH_DUST
	var dust := Sprite2D.new()
	dust.texture = _dust_sheet(spec)
	dust.hframes = spec.frames.size()
	dust.centered = false
	dust.scale = Vector2.ONE * spec.scale
	dust.modulate.a = spec.alpha
	var shape: CollisionShape2D = player.get_node("CollisionShape2D")
	var feet := Vector2(at.x, at.y + (shape.global_transform * shape.shape.get_rect()).end.y - player.global_position.y)
	if heading != Vector2.ZERO:
		feet -= heading.normalized() * spec.push * spec.scale
	_add_beside_player(dust, feet.round(), feet.y, -Vector2(dust_origin))
	var total: float = spec.frame_time * spec.frames.size()
	var play := dust.create_tween().set_parallel()
	play.tween_property(dust, "modulate:a", 0.0, total).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	for i in range(1, spec.frames.size()):
		play.tween_callback(dust.set_frame.bind(i)).set_delay(spec.frame_time * i)
	play.chain().tween_callback(dust.queue_free)


func _add_beside_player(node: Sprite2D, drawn_at: Vector2, own_sort: float, base_offset: Vector2) -> void:
	var stage: Node2D = player.get_parent()
	var holder := stage.get_parent()
	holder.add_child(node)
	holder.move_child(node, stage.get_index())
	var entry := [node, drawn_at, own_sort, base_offset]
	drawn.append(entry)
	_place(entry, player.sprite.global_position.y)


# Sorted at its own depth unless that would put it ahead of the player, and drawn where it belongs
# whatever it sorts at: the offset takes up the difference.
func _place(entry: Array, player_sort: float) -> void:
	var node: Sprite2D = entry[0]
	var drawn_at: Vector2 = entry[1]
	var sort_y := minf(entry[2], player_sort - SORT_BEHIND)
	node.global_position = Vector2(drawn_at.x, sort_y)
	node.offset = entry[3] + Vector2(0.0, (drawn_at.y - sort_y) / node.scale.y)


# The puff's frames side by side, built once from the layout's blobs.
static func _dust_sheet(spec: Dictionary) -> ImageTexture:
	if dust_sheet:
		return dust_sheet
	var reach := Rect2()
	for frame in spec.frames:
		for blob in frame:
			reach = reach.merge(Rect2(blob[0] - blob[2], blob[1] - blob[2], blob[2] * 2.0, blob[2] * 2.0))
	var origin := Vector2i(ceili(-reach.position.x), ceili(-reach.position.y))
	var size := origin + Vector2i(ceili(reach.end.x), ceili(reach.end.y))
	var image := Image.create_empty(size.x * spec.frames.size(), size.y, false, Image.FORMAT_RGBA8)
	for index in spec.frames.size():
		for y in size.y:
			for x in size.x:
				var texel := Vector2(x + 0.5 - origin.x, y + 0.5 - origin.y)
				for blob in spec.frames[index]:
					var centre := Vector2(blob[0], blob[1])
					if texel.distance_squared_to(centre) <= blob[2] * blob[2]:
						image.set_pixel(index * size.x + x, y, spec.shade if texel.y > centre.y else spec.color)
	dust_sheet = ImageTexture.create_from_image(image)
	dust_origin = origin
	return dust_sheet
