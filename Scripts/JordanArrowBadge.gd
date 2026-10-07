extends Node2D

# The arrow over the player in Jordan's last phase, shared by his attacks (JordanCombo.arrow): the next step of the
# dark maze's path, the glowing keg to dash to. It is Matt's approved boom arrow (MattArtLayout's boom_arrow, frame =
# direction x 3 + state), live, answered or cracked, riding just over the player's head on the Fx layer, over the
# darkness, drawn 1.5x so it reads at its own size in the fight's 2/3 view (JordanGodLayout.ui_scale, arrow_over).
# Until that sheet's switch is on, his stand-in badge: a disc with the arrow in its own colour.

const MattArtLayout := preload("res://Scripts/MattArtLayout.gd")
const MattBoomScript := preload("res://Scripts/MattBoomScript.gd")
const Layout := preload("res://Scripts/JordanGodLayout.gd")

var player: Node2D
var direction := &"up"
var state := &"live"
var sheet: Sprite2D
var disc: Polygon2D
var arrow_shape: Polygon2D
var cross: Node2D


func _ready() -> void:
	if MattArtLayout.uses_final_fx(&"boom_arrow"):
		var spec := MattArtLayout.fx(&"boom_arrow")
		sheet = Sprite2D.new()
		sheet.texture = load(spec.texture)
		sheet.hframes = spec.hframes
		sheet.scale = Vector2.ONE * MattArtLayout.SCALE
		sheet.offset = spec.offset
		add_child(sheet)
	else:
		var spec := MattArtLayout.fx(&"boom_arrow")
		disc = Polygon2D.new()
		disc.polygon = MattArtLayout.circle(spec.radius, 32)
		disc.color = spec.disc
		add_child(disc)
		arrow_shape = Polygon2D.new()
		add_child(arrow_shape)
		cross = Node2D.new()
		var reach: float = spec.radius * 0.6
		for ends in [[Vector2(-reach, -reach), Vector2(reach, reach)], [Vector2(reach, -reach), Vector2(-reach, reach)]]:
			var line := Line2D.new()
			line.points = PackedVector2Array(ends)
			line.default_color = spec.cross
			line.width = 6.0
			cross.add_child(line)
		add_child(cross)
	_follow()


# `dir` is &"up", &"right", &"down" or &"left"; `arrow_state` &"live", &"answered" or &"cracked".
func show_arrow(dir: StringName, arrow_state := &"live") -> void:
	direction = dir
	state = arrow_state
	visible = true
	var spec := MattArtLayout.fx(&"boom_arrow")
	if sheet != null:
		sheet.frame = spec.directions.find(dir) * spec.states.size() + spec.states.find(arrow_state)
	else:
		var colour: Color = MattArtLayout.ARROW_COLORS.get(dir, Color.WHITE)
		if arrow_state == &"answered":
			colour = spec.answered
		elif arrow_state == &"cracked":
			colour = spec.cracked
		arrow_shape.polygon = MattArtLayout.scaled_poly(MattBoomScript.ARROW_POLY, spec.arrow / 42.0,
			MattBoomScript.ARROW_TURNS.get(dir, 0.0))
		arrow_shape.color = colour
		cross.visible = arrow_state == &"cracked"
	_follow()


func _process(_delta: float) -> void:
	_follow()


func _follow() -> void:
	scale = Vector2.ONE * Layout.ui_scale()
	if is_instance_valid(player):
		global_position = (player.global_position + Layout.arrow_over()).round()
