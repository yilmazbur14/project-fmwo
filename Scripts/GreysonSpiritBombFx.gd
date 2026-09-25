extends Node2D

# Greyson's spirit bomb (plan section 3.6) on the shipped sheets - GreysonArtLayout's bomb, bomb_orb, bomb_light,
# bomb_screen and player_disintegrate - played by FX_FOR_CODER's rules. GreysonSpiritBomb calls the beats in order -
# gather, launch, blast - or settle() for the hold-to-skip; each runs on this node's physics clock, so FightFreeze
# and the pause screen hold it with the fight.
#
# IT GOES IN THE FLOOR LAYER (body.floor_layer), for the light. The artist's draw order is, bottom to top: the
# arena, the blue light, the fighters (cooled with it), the orbs, the sphere, the blast over the whole view, and
# the player coming apart over the blast so it is seen through it. The floor layer sorts after the mat and before
# anyone standing on it, which is where the light goes, as a plain child here; everything after it is on absolute
# z (LAYOUT.z), over the fighters and the ropes, and the HUD's canvas layers stay over all of it.
#
# PHOTOSENSITIVITY: the blast's only white frames are f0, f3 and f6, 0.4 s apart - 2.5 a second, under the brief's
# cap of 3. Nothing else here flashes.

enum Phase { IDLE, GATHER, HELD, LAUNCH, BLAST, DONE }

const Layout := preload("res://Scripts/GreysonArtLayout.gd")

# The bomb's own numbers; its sheets' are GreysonArtLayout's.
const LAYOUT := {
	z = {orbs = 5, sphere = 5, blast = 90, remains = 100},
	# The sphere's centre's height over the muzzle, px, on the first and the last growth frame: measured off the
	# sheet, which grows evenly between.
	sphere_rise = [33.0, 540.0],
	# How often each orb row - small, medium, large, extra large - is sent: mostly small and medium.
	orb_weights = [0.4, 0.35, 0.18, 0.07],
	orb_rate = 44.0,
	# Seconds from the crowd to the sphere, and how far each rises before it bends in.
	orb_flight = [1.0, 1.6],
	orb_rise = [120.0, 260.0],
	# World px: the stands along the top, ringside down both sides and along the bottom.
	crowd_band = [Rect2(0, 0, 1920, 100), Rect2(0, 100, 100, 880), Rect2(1820, 100, 100, 880), Rect2(0, 985, 1920, 95)],
	# The artist's rules: the blast's white frames, the light and the cooling going out from light_out_from to its
	# end, and the player coming apart from its remains_from.
	blast_whites = [0, 3, 6],
	light_out_from = 7,
	remains_from = 1,
}

var phase := Phase.IDLE
var clock := 0.0
var rng := RandomNumberGenerator.new()

var gather_time := 2.5
var launch_from := Vector2.ZERO
var launch_to := Vector2.ZERO
var launch_time := 0.6
var shimmer_clock := 0.0
var orb_owed := 0.0
# Each [where it set off, the bend of its arc, row, first frame, age, flight time].
var orbs: Array = []
var cooled: Array = []
var light_amount := 0.0

var blast_frame := -1
# The clock at each white frame of the blast, for the tests.
var white_peaks: Array[float] = []
var player_sprite: Sprite2D
var facing_row := 0

var orb_sheet: Texture2D
var screen_sheet: Texture2D
var light: Sprite2D
var orb_layer: Node2D
var sphere: Sprite2D
var blast_layer: Node2D
var remains: Sprite2D


func _init() -> void:
	rng.randomize()
	orb_sheet = load(Layout.fx(&"bomb_orb").texture)
	screen_sheet = load(Layout.fx(&"bomb_screen").texture)
	light = Sprite2D.new()
	light.texture = load(Layout.fx(&"bomb_light").texture)
	light.centered = false
	light.scale = Vector2.ONE * Layout.SCALE
	light.visible = false
	add_child(light)
	orb_layer = _layer(LAYOUT.z.orbs, _draw_orbs)
	sphere = _sheet(Layout.fx(&"bomb"), LAYOUT.z.sphere)
	sphere.offset = Layout.fx(&"bomb").offset
	blast_layer = _layer(LAYOUT.z.blast, _draw_blast)
	remains = _sheet(Layout.fx(&"player_disintegrate"), LAYOUT.z.remains)


# The sphere grows on the muzzle `at` (global px, like every point here) over `seconds`, and its light comes up
# cooling `cool`: the fighters, and anything else standing in it.
func gather(at: Vector2, seconds: float, cool: Array) -> void:
	gather_time = seconds
	cooled = cool
	orb_owed = 0.0
	light.position = to_local(Vector2.ZERO)
	light.visible = true
	sphere.position = to_local(at)
	sphere.visible = true
	_begin(Phase.GATHER)


# Its centre onto `to`.
func launch(to: Vector2, seconds: float) -> void:
	launch_from = sphere.position
	launch_to = to_local(to) + Vector2(0, LAYOUT.sphere_rise[1])
	launch_time = seconds
	_begin(Phase.LAUNCH)


# With the player's sprite, they come apart over the blast in `row`, their facing's (PlayerScript.Facing, which
# the sheet's rows follow); the sheet is drawn from their standing frame, so put them on it first.
func blast(sprite: Sprite2D = null, row := 0) -> void:
	orbs.clear()
	sphere.visible = false
	player_sprite = sprite
	facing_row = row
	white_peaks.clear()
	blast_frame = -1
	_begin(Phase.BLAST)


# Straight to how it ends, for the hold-to-skip: nothing of the bomb left, the light out, and `sprite`, the
# player's if they are going, gone.
func settle(sprite: Sprite2D = null) -> void:
	orbs.clear()
	sphere.visible = false
	remains.visible = false
	blast_frame = -1
	blast_layer.queue_redraw()
	_set_light(0.0)
	light.visible = false
	if sprite != null:
		sprite.visible = false
	phase = Phase.DONE


func sphere_centre() -> Vector2:
	var grown := minf(sphere.frame / float(Layout.fx(&"bomb").grow - 1), 1.0)
	return sphere.position - Vector2(0, lerpf(LAYOUT.sphere_rise[0], LAYOUT.sphere_rise[1], grown))


# Up off the crowd, bending into the sphere, faster as it nears it: gone into it at the end of its flight.
func orb_position(orb: Array) -> Vector2:
	var t: float = orb[4] / orb[5]
	t *= t
	var start: Vector2 = orb[0]
	var bend: Vector2 = orb[1]
	return start.lerp(bend, t).lerp(bend.lerp(sphere_centre(), t), t)


static func blast_length() -> float:
	return blast_start(Layout.fx(&"bomb_screen").times.size())


static func blast_start(frame: int) -> float:
	var times: Array = Layout.fx(&"bomb_screen").times
	var start := 0.0
	for i in frame:
		start += times[i]
	return start


# The blast frame showing `seconds` in, or -1 once it is over.
static func blast_frame_at(seconds: float) -> int:
	var times: Array = Layout.fx(&"bomb_screen").times
	var end := 0.0
	for i in times.size():
		end += times[i]
		if seconds < end:
			return i
	return -1


func _physics_process(delta: float) -> void:
	_step(delta)


func _exit_tree() -> void:
	_set_light(0.0)


func _begin(new_phase: Phase) -> void:
	phase = new_phase
	clock = 0.0
	_step(0.0)


func _step(delta: float) -> void:
	clock += delta
	match phase:
		Phase.GATHER:
			var grow: int = Layout.fx(&"bomb").grow
			var grown := minf(clock / gather_time, 1.0)
			sphere.frame = mini(int(grown * grow), grow - 1)
			_set_light(grown)
			_feed(delta)
			if grown >= 1.0:
				phase = Phase.HELD
		Phase.HELD:
			_shimmer(delta)
			_feed(delta)
		Phase.LAUNCH:
			_shimmer(delta)
			var fall := minf(clock / launch_time, 1.0)
			sphere.position = launch_from.lerp(launch_to, fall * fall)
		Phase.BLAST:
			_step_blast()
	for i in range(orbs.size() - 1, -1, -1):
		orbs[i][4] += delta
		if orbs[i][4] >= orbs[i][5]:
			orbs.remove_at(i)
	orb_layer.queue_redraw()
	blast_layer.queue_redraw()


func _shimmer(delta: float) -> void:
	shimmer_clock += delta
	var bomb := Layout.fx(&"bomb")
	var frames: Array = bomb.shimmer
	sphere.frame = frames[int(shimmer_clock / bomb.shimmer_time) % frames.size()]


func _feed(delta: float) -> void:
	orb_owed += LAYOUT.orb_rate * delta
	while orb_owed >= 1.0:
		orb_owed -= 1.0
		var band: Rect2 = LAYOUT.crowd_band[rng.randi() % LAYOUT.crowd_band.size()]
		var from := to_local(band.position + band.size * Vector2(rng.randf(), rng.randf()))
		var bend := from - Vector2(0, rng.randf_range(LAYOUT.orb_rise[0], LAYOUT.orb_rise[1]))
		var row := rng.rand_weighted(PackedFloat32Array(LAYOUT.orb_weights))
		var first := rng.randi() % int(Layout.fx(&"bomb_orb").hframes)
		orbs.append([from, bend, row, first, 0.0, rng.randf_range(LAYOUT.orb_flight[0], LAYOUT.orb_flight[1])])


func _step_blast() -> void:
	var frame := blast_frame_at(clock)
	if frame != blast_frame and frame in LAYOUT.blast_whites:
		white_peaks.append(clock)
	blast_frame = frame
	var tail := blast_start(LAYOUT.light_out_from)
	if clock >= tail:
		_set_light(1.0 - minf((clock - tail) / (blast_length() - tail), 1.0))
	if player_sprite != null:
		_step_remains(clock - blast_start(LAYOUT.remains_from))
	if frame < 0:
		phase = Phase.DONE


func _step_remains(into: float) -> void:
	var spec := Layout.fx(&"player_disintegrate")
	var frame := int(into / spec.frame_time)
	remains.visible = into >= 0.0 and frame < spec.hframes
	if not remains.visible:
		return
	remains.global_position = player_sprite.global_position
	remains.offset = player_sprite.offset
	remains.global_scale = player_sprite.global_scale
	remains.frame_coords = Vector2i(frame, facing_row)
	if frame >= 1:
		player_sprite.visible = false


func _set_light(amount: float) -> void:
	light_amount = amount
	light.modulate.a = amount
	var tint: Color = Layout.fx(&"bomb_light").fighter_tint
	for item in cooled:
		if is_instance_valid(item):
			item.modulate = Color.WHITE.lerp(tint, amount)


func _draw_orbs() -> void:
	var spec := Layout.fx(&"bomb_orb")
	var size := orb_sheet.get_width() / float(spec.hframes)
	var drawn := Vector2.ONE * size * Layout.SCALE
	for orb in orbs:
		var frame: int = (orb[3] + int(orb[4] / spec.frame_time)) % spec.hframes
		var at := (orb_position(orb) / Layout.SCALE).round() * Layout.SCALE - drawn / 2.0
		orb_layer.draw_texture_rect_region(orb_sheet, Rect2(at, drawn), Rect2(frame * size, orb[2] * size, size, size))


func _draw_blast() -> void:
	if blast_frame < 0:
		return
	var frame_size := Vector2(screen_sheet.get_width() / float(Layout.fx(&"bomb_screen").hframes), screen_sheet.get_height())
	# Pinned to the screen however ScreenView zooms or shakes the world's canvas under it.
	blast_layer.draw_set_transform_matrix(blast_layer.get_global_transform_with_canvas().affine_inverse())
	blast_layer.draw_texture_rect_region(screen_sheet, blast_layer.get_viewport_rect(), Rect2(Vector2(blast_frame * frame_size.x, 0), frame_size))


func _layer(z: int, draw_with: Callable) -> Node2D:
	var layer := Node2D.new()
	layer.z_as_relative = false
	layer.z_index = z
	layer.draw.connect(draw_with)
	add_child(layer)
	return layer


func _sheet(spec: Dictionary, z: int) -> Sprite2D:
	var sheet := Sprite2D.new()
	sheet.texture = load(spec.texture)
	sheet.hframes = spec.hframes
	sheet.vframes = spec.get("vframes", 1)
	sheet.scale = Vector2.ONE * Layout.SCALE
	sheet.z_as_relative = false
	sheet.z_index = z
	sheet.visible = false
	add_child(sheet)
	return sheet
