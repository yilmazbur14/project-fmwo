extends Node2D

# One of Liam's fire tornados (attack 3, LiamFirestorm), standing on its base point on the mat and sorting with everyone
# (it is added under his scene). It spins up harmless (SPIN), catches fire when his streak reaches it (IGNITE, then the
# FIRE loop) and burns out (OUT, over burn_out's time or its host's interrupt_burnout), then frees itself. While it burns
# its core burns: a player whose feet come inside TORNADO_CORE round its base takes liam_fire_tornado and is flung out
# along the line from the base (its host's carry_player), once until their feet are out past the core grown by
# CORE_LATCH_GROW. With the approved art it forms out of a whirl of spray in place of the fade-in, and spews each ring
# out of its foot (spew, spew_lead) when its switches are on. Everything it times steps in its own _physics_process, so
# a pause and a freeze hold it.

const Layout := preload("res://Scripts/LiamArtLayout.gd")
const FirestormLayout := preload("res://Scripts/LiamFirestormLayout.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")

const TORNADO_ID := &"liam_fire_tornado"

enum Stage { SPIN, IGNITE, FIRE, OUT }

# Set before it enters the tree: the state machine (its knobs and carry_player) and the player it burns.
var host: Node
var player: Node2D

var stage := Stage.SPIN
var stage_clock := 0.0
var clock := 0.0
var out_time := 0.6
var burning := false
var latched := false
var forming := false
var spewing := false
var spew_clock := 0.0
# For a test: every result its core has had.
var results: Array[int] = []

var art: Node2D
var sheet: Sprite2D
var funnel: Polygon2D
var funnel_edge: Line2D
var core: Polygon2D
var swirls: Array[Line2D] = []


func _ready() -> void:
	_build_art()
	forming = sheet != null and Layout.final_tornado_form()
	if not forming:
		art.modulate.a = 0.0
		art.scale = Vector2(0.3, 0.3)
	_show()


# How long before a ring goes out its spew has to start, so the ring leaves on the spew's ring frame: none without it.
static func spew_lead() -> float:
	if not Layout.final_tornado_spew():
		return 0.0
	var times := Layout.spread(Layout.TORNADO_SPEW_TIMES, Layout.strip_count(Layout.TORNADO_SPEW_SHEET, Layout.TORNADO_FRAME))
	var lead := 0.0
	for i in mini(Layout.TORNADO_SPEW_RING_FRAME, times.size() - 1):
		lead += times[i]
	return lead


# A ring on its way out of its foot: the spew once in place of the fire loop, if it has one.
func spew() -> void:
	if stage == Stage.FIRE and sheet != null and Layout.final_tornado_spew():
		spewing = true
		spew_clock = 0.0


# Caught by his streak: its fire from here, and its core burns.
func ignite() -> void:
	if stage != Stage.SPIN:
		return
	stage = Stage.IGNITE
	stage_clock = 0.0
	burning = true
	_show()


# Out over `time`: its core stops burning at once, and it frees itself at the end.
func burn_out(time: float) -> void:
	if stage == Stage.OUT:
		return
	stage = Stage.OUT
	stage_clock = 0.0
	out_time = maxf(time, 0.01)
	burning = false
	spewing = false
	_show()


# Put out by a round's first hit or the end of the fight (LiamStateMachine.stop_everything): burn_out over `time`, or
# its host's interrupt_burnout.
func extinguish(time := -1.0) -> void:
	burn_out(time if time >= 0.0 else host.interrupt_burnout)


func _physics_process(delta: float) -> void:
	clock += delta
	stage_clock += delta
	if forming and clock >= Layout.TORNADO_FADE_IN:
		forming = false
	if spewing:
		spew_clock += delta
		if spew_clock >= _spew_length():
			spewing = false
	if art.modulate.a < 1.0 and stage != Stage.OUT:
		var grown := clampf(clock / Layout.TORNADO_FADE_IN, 0.0, 1.0)
		art.modulate.a = grown
		art.scale = Vector2.ONE * lerpf(0.3, 1.0, grown)
	match stage:
		Stage.IGNITE:
			if stage_clock >= Layout.TORNADO_IGNITE_TIME:
				stage = Stage.FIRE
				stage_clock = 0.0
		Stage.OUT:
			if stage_clock >= out_time:
				queue_free()
				return
	_show()
	if burning:
		_resolve_core()


# The player's feet inside the core: burned and flung out, once until they are clear of it.
func _resolve_core() -> void:
	if not is_instance_valid(player):
		return
	var feet: Vector2 = player.global_position + FirestormLayout.FEET - global_position
	var core_radii := FirestormLayout.TORNADO_CORE
	if latched:
		var grown := core_radii + Vector2.ONE * FirestormLayout.CORE_LATCH_GROW
		if pow(feet.x / grown.x, 2.0) + pow(feet.y / grown.y, 2.0) > 1.0:
			latched = false
		return
	if pow(feet.x / core_radii.x, 2.0) + pow(feet.y / core_radii.y, 2.0) > 1.0:
		return
	latched = true
	var centre: Vector2 = player.hurtBox.get_node("CollisionShape2D").global_position
	results.append(player.receive_hit(HitInfo.make(TORNADO_ID, self, centre, null)))
	var away := feet.normalized() if feet.length() > 0.5 else Vector2.DOWN
	host.carry_player(away * host.tornado_fling, host.tornado_fling_time)


#DRAWING IT

func _build_art() -> void:
	art = Node2D.new()
	art.name = "Art"
	add_child(art)
	if Layout.final_tornado():
		sheet = Sprite2D.new()
		sheet.scale = Vector2.ONE * Layout.SCALE
		sheet.offset = Layout.TORNADO_FRAME / 2.0 - Layout.TORNADO_PIVOT
		art.add_child(sheet)
		return
	var look: Dictionary = Layout.PLACEHOLDER_TORNADO
	core = Polygon2D.new()
	core.polygon = Layout.ellipse(FirestormLayout.TORNADO_CORE)
	core.color = look.core
	art.add_child(core)
	funnel = Polygon2D.new()
	funnel.polygon = PackedVector2Array([Vector2(-look.base_half, 0), Vector2(look.base_half, 0),
		Vector2(look.top_half, -look.height), Vector2(-look.top_half, -look.height)])
	art.add_child(funnel)
	funnel_edge = Line2D.new()
	funnel_edge.points = funnel.polygon
	funnel_edge.closed = true
	funnel_edge.width = 3.0
	art.add_child(funnel_edge)
	for i in 5:
		var swirl := Line2D.new()
		swirl.width = 4.0
		art.add_child(swirl)
		swirls.append(swirl)


func _show() -> void:
	if sheet != null:
		_show_sheet()
		return
	var look: Dictionary = Layout.PLACEHOLDER_TORNADO
	var on_fire := stage == Stage.IGNITE or stage == Stage.FIRE
	funnel.color = look.fire if on_fire else look.spin
	funnel_edge.default_color = look.fire_edge if on_fire else look.spin_edge
	core.visible = on_fire
	if stage == Stage.OUT:
		art.modulate.a = clampf(1.0 - stage_clock / out_time, 0.0, 1.0)
	# Bands spiralling up the funnel, a turn every 0.3 s.
	for i in swirls.size():
		var up: float = float(i + 1) / (swirls.size() + 1)
		var y: float = -look.height * up
		var half: float = lerpf(look.base_half, look.top_half, up)
		var phase := clock * TAU / 0.3 + i
		swirls[i].points = PackedVector2Array([Vector2(-half * cos(phase), y - 8.0), Vector2(half * cos(phase + 1.2), y + 8.0)])
		swirls[i].default_color = look.fire_core if on_fire else look.spin_edge


# Its stage's strip: the loops at TORNADO_LOOP_TIME, the ignite over TORNADO_IGNITE_TIME, the out over its time; the
# form over TORNADO_FADE_IN in place of the first of the spin, and a spew in place of the fire loop.
func _show_sheet() -> void:
	var clip: StringName = [&"spin", &"ignite", &"fire", &"out"][stage]
	var path: String = Layout.TORNADO_SHEETS[clip]
	if forming and stage == Stage.SPIN:
		path = Layout.TORNADO_FORM_SHEET
	elif spewing and stage == Stage.FIRE:
		path = Layout.TORNADO_SPEW_SHEET
	if sheet.texture == null or sheet.texture.resource_path != path:
		sheet.frame = 0
		sheet.texture = load(path)
		sheet.hframes = Layout.strip_count(path, Layout.TORNADO_FRAME)
	var count := sheet.hframes
	if path == Layout.TORNADO_FORM_SHEET:
		sheet.frame = mini(int(clock / Layout.TORNADO_FADE_IN * count), count - 1)
		return
	if path == Layout.TORNADO_SPEW_SHEET:
		sheet.frame = Layout.frame_at(Layout.TORNADO_SPEW_TIMES, count, spew_clock / _spew_length())
		return
	match stage:
		Stage.SPIN, Stage.FIRE:
			sheet.frame = int(stage_clock / Layout.TORNADO_LOOP_TIME) % count
		Stage.IGNITE:
			sheet.frame = mini(int(stage_clock / Layout.TORNADO_IGNITE_TIME * count), count - 1)
		Stage.OUT:
			sheet.frame = mini(int(stage_clock / out_time * count), count - 1)


func _spew_length() -> float:
	var total := 0.0
	for time: float in Layout.TORNADO_SPEW_TIMES:
		total += time
	return total
