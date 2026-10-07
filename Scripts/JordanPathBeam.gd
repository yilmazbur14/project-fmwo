extends Node2D

# Greyson's beam down the dark maze (JordanComboMaze), on the god's Fx layer: Computah's laser - Greyson's cannon arm
# is Computah's - tiled along a Line2D at the Computah beam's on-screen thickness, from Greyson's muzzle into the goal
# and back down the path's corners to the player's block. Its two stacked frames alternate for the shimmer, as his
# does, with the emitter's flare on the muzzle and another on the beam's head. It only draws: the combo times the
# trace and deals the damage.
#
# The laser sheet stacks its two frames, and a Line2D tiles the whole texture across its width, so each frame is cut
# out into a texture of its own as the beam is built.

const Layout := preload("res://Scripts/JordanMazeLayout.gd")

# The line's corners in world px, and how far along it each one is.
var route := PackedVector2Array()
var along: Array[float] = []
var total := 0.0
var progress := 0.0
var line: Line2D
var frames: Array[Texture2D] = []
var muzzle_flare: Sprite2D
var head_flare: Sprite2D
var clock := 0.0


# Along `points`, world px, nothing of it drawn yet. Once it is in the tree.
func setup(points: PackedVector2Array) -> void:
	route = points
	along = [0.0]
	for i in range(1, route.size()):
		along.append(along[i - 1] + route[i - 1].distance_to(route[i]))
	total = along[along.size() - 1]
	var spec := Layout.BEAM_ART
	frames = _cut_frames(spec)
	line = Line2D.new()
	line.width = spec.frame.y * spec.scale
	line.texture = frames[0]
	line.texture_mode = Line2D.LINE_TEXTURE_TILE
	line.texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
	line.joint_mode = Line2D.LINE_JOINT_SHARP
	add_child(line)
	muzzle_flare = _flare()
	head_flare = _flare()
	trace(0.0)


# Drawn from the muzzle to `share` of the way along.
func trace(share: float) -> void:
	progress = clampf(share, 0.0, 1.0)
	var reach := total * progress
	var points := PackedVector2Array([to_local(route[0])])
	for i in range(1, route.size()):
		if along[i] <= reach:
			points.append(to_local(route[i]))
			continue
		var span := along[i] - along[i - 1]
		var weight := (reach - along[i - 1]) / span if span > 0.0 else 1.0
		points.append(to_local(route[i - 1].lerp(route[i], weight)))
		break
	if points.size() < 2:
		points.append(points[0])
	line.points = points
	muzzle_flare.position = points[0].round()
	head_flare.position = points[points.size() - 1].round()


# Where the beam's head is, world px.
func head() -> Vector2:
	return to_global(line.points[line.points.size() - 1])


func is_through() -> bool:
	return progress >= 1.0


func _process(delta: float) -> void:
	clock += delta
	var shimmer := int(clock / Layout.BEAM_ART.shimmer_time) % 2
	line.texture = frames[shimmer]
	muzzle_flare.frame = shimmer
	head_flare.frame = 1 - shimmer


func _cut_frames(spec: Dictionary) -> Array[Texture2D]:
	var sheet := (load(spec.texture) as Texture2D).get_image()
	var size: Vector2i = spec.frame
	var cut: Array[Texture2D] = []
	for k in spec.frames:
		cut.append(ImageTexture.create_from_image(sheet.get_region(Rect2i(Vector2i(0, size.y * k), size))))
	return cut


# Kept upright on its pixel grid: it is round, so it never turns with the line.
func _flare() -> Sprite2D:
	var spec := Layout.BEAM_ART
	var flare := Sprite2D.new()
	flare.texture = load(spec.flare)
	flare.hframes = spec.flare_hframes
	flare.scale = Vector2.ONE * spec.scale
	add_child(flare)
	return flare
