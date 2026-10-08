extends RefCounted

# The shared arena (ArenaScene) dressed as Jordan's void for his last phase (JordanGodFightScene), so everything that
# finds the player at Arena/MainPlayer/CharacterBody2D - FightOutro, the pause screen, the finisher, the ring bounds,
# the defence suite - works untouched. The ring's art is hidden: the ringside and its crowd, the crowd band, the mat,
# and the ropes and poles on the walls. The fight is drawn at 2/3 (the user's staging option B), so its floor is far
# bigger than the ring: the walls' invisible collision - the four thin walls and the thick backings behind them - is
# moved out to JordanGodLayout.FLOOR, and the player's own clamp to the floor (PlayerScript.ring_origins) is measured
# again off them. Kept: the gates (hidden until an entrance opens them), the VS card (never played here) and the pause
# screen. The crowd's scripts still run on their hidden sprites: they play no sound, so their cheers are harmless.
#
# The void is the finale's (JordanFinaleLayout): the drawn void_bg, or its stand-in colour with motes drifting up
# through it. It is drawn in screen space on a layer under the world (build_void), so it fills the whole of the wider
# view exactly as it filled the finale's; the arena's black backing, which would cover it, is hidden.

const FinaleLayout := preload("res://Scripts/JordanFinaleLayout.gd")
const GodLayout := preload("res://Scripts/JordanGodLayout.gd")

const HIDDEN: Array[String] = ["Ringside", "RingsideCrowd", "Sprite2D", "Mat", "ColorRect"]
const WALLS := "wallBoundaries"
const PLAYER := "MainPlayer/CharacterBody2D"
# The walls' thickness: the thin ones the ring always had, and the backings a body can't be squeezed through.
const THIN := 10.0
const THICK := 210.0
# Under the world's own canvas layer, 0.
const VOID_LAYER := -1


static func dress(arena: Node) -> void:
	for node_name in HIDDEN:
		var node := arena.get_node_or_null(node_name)
		if node is CanvasItem:
			node.visible = false
	var walls := arena.get_node_or_null(WALLS)
	if walls != null:
		for sprite in walls.find_children("*", "Sprite2D", true, false):
			sprite.visible = false
		_move_walls(walls, GodLayout.FLOOR)
	var player := arena.get_node_or_null(PLAYER)
	if player != null:
		player.ring_origins = player._find_ring_origins()


# Every wall's inner face on `floor_rect`'s edge, the thin ones overlapping at the corners and the backings reaching
# THICK past it, as the ring's are laid out round its own floor.
static func _move_walls(walls: Node, floor_rect: Rect2) -> void:
	var middle := floor_rect.get_center()
	var across := floor_rect.size + Vector2(THIN, THIN) * 2.0
	var past := floor_rect.size + Vector2(THICK, THICK) * 2.0
	_place(walls, "topWall", Vector2(middle.x, floor_rect.position.y - THIN / 2.0), Vector2(across.x, THIN))
	_place(walls, "bottomWall", Vector2(middle.x, floor_rect.end.y + THIN / 2.0), Vector2(across.x, THIN))
	_place(walls, "leftWall", Vector2(floor_rect.position.x - THIN / 2.0, middle.y), Vector2(THIN, across.y))
	_place(walls, "rightWall", Vector2(floor_rect.end.x + THIN / 2.0, middle.y), Vector2(THIN, across.y))
	_place(walls, "topWallBacking", Vector2(middle.x, floor_rect.position.y - THICK / 2.0), Vector2(past.x, THICK))
	_place(walls, "bottomWallBacking", Vector2(middle.x, floor_rect.end.y + THICK / 2.0), Vector2(past.x, THICK))
	_place(walls, "leftWallBacking", Vector2(floor_rect.position.x - THICK / 2.0, middle.y), Vector2(THICK, past.y))
	_place(walls, "rightWallBacking", Vector2(floor_rect.end.x + THICK / 2.0, middle.y), Vector2(THICK, past.y))


# A shape of its own: the scene's are shared with every other fight's arena.
static func _place(walls: Node, wall_name: String, at: Vector2, size: Vector2) -> void:
	var wall := walls.get_node_or_null(wall_name) as CollisionShape2D
	if wall == null:
		return
	var box := RectangleShape2D.new()
	box.size = size
	wall.shape = box
	wall.global_position = at


# The void, on a screen-space layer of its own under the world, inside `layer`. The layer.
static func build_void(layer: Node) -> CanvasLayer:
	var screen := CanvasLayer.new()
	screen.name = "VoidScreen"
	screen.layer = VOID_LAYER
	layer.add_child(screen)
	if FinaleLayout.final_void():
		var back := Sprite2D.new()
		back.name = "VoidBg"
		back.texture = load(FinaleLayout.VOID_BG)
		back.centered = false
		back.scale = Vector2.ONE * FinaleLayout.SCALE
		screen.add_child(back)
		return screen
	var spec: Dictionary = FinaleLayout.PLACEHOLDER_VOID
	var back := ColorRect.new()
	back.name = "VoidBg"
	back.color = spec.color
	back.size = FinaleLayout.VIEW_SIZE
	back.mouse_filter = Control.MOUSE_FILTER_IGNORE
	screen.add_child(back)
	var motes := CPUParticles2D.new()
	motes.amount = spec.amount
	motes.lifetime = 6.0
	motes.preprocess = 6.0
	motes.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	motes.emission_rect_extents = FinaleLayout.VIEW_SIZE / 2.0
	motes.position = FinaleLayout.VIEW_SIZE / 2.0
	motes.direction = Vector2.UP
	motes.spread = 20.0
	motes.gravity = Vector2.ZERO
	motes.initial_velocity_min = 12.0
	motes.initial_velocity_max = 30.0
	motes.scale_amount_min = FinaleLayout.SCALE
	motes.scale_amount_max = FinaleLayout.SCALE * 2.0
	motes.color = spec.motes
	var dot := Image.create(1, 1, false, Image.FORMAT_RGBA8)
	dot.fill(Color.WHITE)
	motes.texture = ImageTexture.create_from_image(dot)
	screen.add_child(motes)
	return screen
