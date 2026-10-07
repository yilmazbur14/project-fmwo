extends Node2D

# The steam over Liam's ring (attacks 3 and 4, addendum 3 B.6): a world overlay at STEAM_Z, over the fighters and the
# ropes and under his FxLayer, the parry badge and the HUD, built by LiamScript as body.steam. One quad over STEAM_RECT
# (so shakes and zooms stay covered) runs liam_steam.gdshader: `density` thick, a clear bubble round the player, and fire
# glowing through it (its host's steam_glow_through). While its wisps are on, puffs rise off the wet floor, most of them
# near wisp_sources (the tornados). Its drift runs on its own clock in _physics_process and its tweens are node-bound,
# so a pause and a finisher's freeze hold it.

const Layout := preload("res://Scripts/LiamArtLayout.gd")
const SHADER := preload("res://Scripts/liam_steam.gdshader")

# Set before it enters the tree: the state machine (the player's hurtbox centre, the knobs, the flood).
var host: Node

var density := 0.0
var bubble := Layout.STEAM_BUBBLE
var clock := 0.0
var wisps_on := false
var wisp_sources: Array[Vector2] = []
var wisp_left := 0.0
var density_tween: Tween
var bubble_tween: Tween
var quad: Polygon2D
var shader_material: ShaderMaterial
var wisps: Array[Node2D] = []
var wisp_ages: Array[float] = []
var random := RandomNumberGenerator.new()


func _ready() -> void:
	z_index = Layout.STEAM_Z
	z_as_relative = false
	global_position = Vector2.ZERO
	random.randomize()
	quad = Polygon2D.new()
	quad.name = "Steam"
	quad.polygon = Layout.rect_polygon(Layout.STEAM_RECT)
	shader_material = ShaderMaterial.new()
	shader_material.shader = SHADER
	quad.material = shader_material
	add_child(quad)
	if Layout.final_steam(Layout.STEAM_TILE_SHEET):
		var tile: Texture2D = load(Layout.STEAM_TILE_SHEET)
		shader_material.set_shader_parameter("steam_tile", tile)
		shader_material.set_shader_parameter("has_tile", true)
		shader_material.set_shader_parameter("tile_frames", float(maxi(roundi(tile.get_width() / Layout.STEAM_TILE_TEXELS), 1)))
		shader_material.set_shader_parameter("tile_px", Layout.STEAM_TILE_TEXELS * Layout.SCALE)
	shader_material.set_shader_parameter("feather", Layout.STEAM_FEATHER)
	shader_material.set_shader_parameter("steam_colour", Layout.STEAM_COLOUR)
	_apply()


# To `to` over `time` (0 at once).
func set_density(to: float, time: float) -> void:
	hold()
	if time <= 0.0:
		_set_density(to)
		return
	density_tween = create_tween()
	density_tween.tween_method(_set_density, density, to, time)


# Wherever it has got to, it stays.
func hold() -> void:
	if density_tween and density_tween.is_valid():
		density_tween.kill()
	density_tween = null


func set_bubble(radius: float, time: float) -> void:
	if bubble_tween and bubble_tween.is_valid():
		bubble_tween.kill()
	if time <= 0.0:
		bubble = radius
		return
	bubble_tween = create_tween()
	bubble_tween.tween_property(self, "bubble", radius, time)


func set_wisps(on: bool) -> void:
	wisps_on = on


func _set_density(value: float) -> void:
	density = value
	_apply()


func _physics_process(delta: float) -> void:
	clock += delta
	_apply()
	_step_wisps(delta)


func _apply() -> void:
	visible = density > 0.001 or not wisps.is_empty()
	quad.visible = density > 0.001
	shader_material.set_shader_parameter("density", density)
	shader_material.set_shader_parameter("bubble_radius", bubble)
	shader_material.set_shader_parameter("drift_a", Layout.STEAM_DRIFT[0] * clock)
	shader_material.set_shader_parameter("drift_b", Layout.STEAM_DRIFT[1] * clock)
	if host != null and host.is_inside_tree():
		shader_material.set_shader_parameter("bubble_centre", host.player_hurtbox_centre())
		shader_material.set_shader_parameter("glow_through", host.steam_glow_through)
		shader_material.set_shader_parameter("layer_gain", host.steam_layer_gain)


#ITS WISPS

func _step_wisps(delta: float) -> void:
	var flood: Node = host.body.flood if host != null else null
	if wisps_on and is_instance_valid(flood) and flood.coverage > 0.0:
		wisp_left -= delta
		while wisp_left <= 0.0:
			wisp_left += 1.0 / Layout.STEAM_WISPS_PER_SECOND
			_add_wisp()
	for i in range(wisps.size() - 1, -1, -1):
		wisp_ages[i] += delta
		var wisp := wisps[i]
		var done := wisp_ages[i] / Layout.STEAM_WISP_TIME
		if done >= 1.0:
			wisp.queue_free()
			wisps.remove_at(i)
			wisp_ages.remove_at(i)
			continue
		var sheet := wisp as Sprite2D
		if sheet:
			sheet.frame = mini(int(done * sheet.hframes), sheet.hframes - 1)
		else:
			wisp.position.y -= Layout.PLACEHOLDER_WISP.rise * delta
			wisp.modulate.a = 1.0 - done


func _add_wisp() -> void:
	var area: Rect2 = Layout.FLOOD_RECT
	var at := Vector2(random.randf_range(area.position.x, area.end.x), random.randf_range(area.position.y, area.end.y))
	if not wisp_sources.is_empty() and random.randf() < Layout.STEAM_WISP_NEAR_SHARE:
		var source: Vector2 = wisp_sources[random.randi_range(0, wisp_sources.size() - 1)]
		at = (source + Vector2.from_angle(random.randf() * TAU) * Layout.STEAM_WISP_NEAR * sqrt(random.randf())).clamp(area.position, area.end)
	var wisp: Node2D
	if Layout.final_steam(Layout.STEAM_WISP_SHEET):
		var sheet := Sprite2D.new()
		sheet.texture = load(Layout.STEAM_WISP_SHEET)
		sheet.hframes = Layout.strip_count(Layout.STEAM_WISP_SHEET, Layout.STEAM_WISP_FRAME)
		sheet.scale = Vector2.ONE * Layout.SCALE
		sheet.offset = Layout.STEAM_WISP_FRAME / 2.0 - Layout.STEAM_WISP_PIVOT
		wisp = sheet
	else:
		var puff := Polygon2D.new()
		puff.polygon = Layout.ellipse(Layout.PLACEHOLDER_WISP.radii)
		puff.color = Layout.PLACEHOLDER_WISP.color
		wisp = puff
	add_child(wisp)
	wisp.position = to_local(at).round()
	wisps.append(wisp)
	wisp_ages.append(0.0)
