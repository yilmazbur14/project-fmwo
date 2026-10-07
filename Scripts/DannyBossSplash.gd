extends Node2D

# The worm splash one of Danny's hops throws out round where it lands (Addendum 1, section A.3). From the latch
# it is drawn as its zone, a dashed outline on the floor in the dodge tell's yellow, so a step off the marked spot
# plainly isn't enough. At the landing, once that landing's own hit has resolved (DannyBossSlams), burst() roots a
# player whose feet are in the zone - the root a puddle springs (DannyBossRoot, then on_player_rooted) - unless a
# dash has them immune, or the i-frames of a hit they just took, or a root may not be sprung now (can_root). It
# does no damage and sends no HitInfo: no hype, gauge or streak comes of it. Then its burst, the artist's worm
# splash on the floor under him or eight of his worm globs flung out over both fighters to the zone's edge, and it
# frees itself.
# The user's open question 2: with `roots` off, the splash hits the feet in it for the hop's own half a heart
# instead, and never roots.

const ROOT_SCRIPT := preload("res://Scripts/DannyBossRoot.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const DashImmunity := preload("res://Scripts/DashImmunity.gd")
const AttackCatalog := preload("res://Scripts/AttackCatalog.gd")
const Layout := preload("res://Scripts/DannyBossArtLayout.gd")

# The glob stand-in flies over both fighters, as a landing's burst does.
const BURST_Z := 2
const OUTLINE_POINTS := 96

# Set before it enters the tree.
var player: Node2D
var body: Node2D
var state_machine: Node
# The zone round its centre, px: a floor circle, flattened.
var radii := Vector2(230, 83)
var roots := true
var hit_id := &"danny_hop_slam"

var bursting := false
var burst_clock := 0.0
var sheet: Sprite2D
var globs: Array[Sprite2D] = []
var glob_ends: Array[Vector2] = []
# For tests: whether the feet were in the zone at the burst, whether it rooted them, and what a hit came to.
var feet_inside := false
var rooted := false
var result := -1


func _draw() -> void:
	if bursting:
		return
	var spec: Dictionary = Layout.fx(&"splash_zone")
	var outline := PackedVector2Array()
	for i in OUTLINE_POINTS + 1:
		var angle := TAU * i / OUTLINE_POINTS
		outline.append(Vector2(cos(angle) * radii.x, sin(angle) * radii.y))
	# Dashes of `dash` px with `gap` px between, walked along the outline.
	var along := 0.0
	var cycle: float = spec.dash + spec.gap
	for i in OUTLINE_POINTS:
		var a: Vector2 = outline[i]
		var b: Vector2 = outline[i + 1]
		var length := a.distance_to(b)
		if fmod(along, cycle) < spec.dash:
			draw_line(a.round(), b.round(), spec.color, spec.width)
		along += length


func covers(point: Vector2) -> bool:
	return ((point - global_position) / radii).length_squared() <= 1.0


# The landing's say on a player in the zone, then the burst. Whether it rooted them.
func burst() -> bool:
	bursting = true
	queue_redraw()
	if is_instance_valid(player) and state_machine != null:
		feet_inside = covers(state_machine.player_feet())
		if feet_inside:
			if roots:
				if not _dodging() and not player.is_invincible and state_machine.can_root():
					_root()
			else:
				result = player.receive_hit(HitInfo.make(hit_id, self, state_machine.player_hurtbox_centre(), body))
	if is_instance_valid(body):
		body.play_sfx(&"worm_splash")
	if Layout.final_fx(&"worm_splash"):
		_play_sheet()
	else:
		_fling_globs()
	return rooted


func _dodging() -> bool:
	return player.is_dodging or DashImmunity.is_immune(player, AttackCatalog.DASH_IMMUNITY_TIME, AttackCatalog.DASH_IMMUNITY_COOLDOWN)


func _root() -> void:
	var root: Node2D = ROOT_SCRIPT.new()
	root.player = player
	root.body = body
	state_machine.add_hazard(root, ROOT_SCRIPT.pivot_of(player), body.projectile_layer)
	state_machine.on_player_rooted(root)
	rooted = true


func _physics_process(delta: float) -> void:
	if not bursting:
		return
	burst_clock += delta
	if is_instance_valid(sheet):
		var spec: Dictionary = Layout.fx(&"worm_splash")
		var frame := int(burst_clock / spec.frame_time)
		if frame >= sheet.hframes:
			queue_free()
			return
		sheet.frame = frame
		return
	var fling: Dictionary = Layout.fx(&"splash_globs")
	var weight := minf(burst_clock / fling.time, 1.0)
	var glob_spec: Dictionary = Layout.fx(&"glob")
	for i in globs.size():
		# Out fast, easing onto the zone's edge.
		var out := 1.0 - (1.0 - weight) * (1.0 - weight)
		globs[i].position = (glob_ends[i] * out).round()
		globs[i].frame = int(burst_clock / glob_spec.frame_time) % globs[i].hframes
	if weight >= 1.0:
		queue_free()


func _play_sheet() -> void:
	var spec: Dictionary = Layout.fx(&"worm_splash")
	sheet = Sprite2D.new()
	sheet.texture = load(spec.texture)
	sheet.hframes = spec.hframes
	sheet.offset = spec.offset
	sheet.scale = Vector2.ONE * Layout.SCALE
	add_child(sheet)


func _fling_globs() -> void:
	var spec: Dictionary = Layout.fx(&"glob")
	var count: int = Layout.fx(&"splash_globs").count
	for i in count:
		var angle := TAU * (i + 0.5) / count
		var glob := Sprite2D.new()
		glob.texture = load(spec.texture)
		glob.hframes = spec.hframes
		glob.offset = spec.offset
		glob.scale = Vector2.ONE * Layout.SCALE
		glob.z_index = BURST_Z
		add_child(glob)
		globs.append(glob)
		glob_ends.append(Vector2(cos(angle) * radii.x, sin(angle) * radii.y))
