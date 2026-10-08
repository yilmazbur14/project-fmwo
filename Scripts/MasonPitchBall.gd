extends Node2D

# One of Mason's pitched nuggets (MasonPitch): a fastball, a changeup or the quick pitch after a bitten hesitation.
# It flies an analytic path from his hand to the point the pitch latched, `flight` seconds whatever the distance (the
# changeup on a lob arc), and on past it.
# IT REPORTS ITS OWN HITS, as Captain Burak's balls and Eric's thrown sword do, because the pitch needs the result: a
# parried ball is batted back into his head. It can only hurt from `live_lead` before its contact to `live_tail` after,
# tested swept along its path (it can cross the ring in two frames); the spot a dash left is a near miss (the dodge
# ghost's house rule). The ball itself is the hit's source, so each pitch is its own read.

# PARRIED, BLOCKED or HIT once, as it is answered; IGNORED for a ball that went by.
signal answered(result: int)
# A batted-back ball reaching his head.
signal arrived

const HitInfo := preload("res://Scripts/HitInfo.gd")
const MasonArtLayout := preload("res://Scripts/MasonArtLayout.gd")
const DefenseHypeArtLayout := preload("res://Scripts/DefenseHypeArtLayout.gd")

const HAZARD_GROUP := "mason_hazard"
const IDS := {&"fastball": &"mason_fastball", &"changeup": &"mason_changeup", &"quick": &"mason_quick_pitch"}
const Z_INDEX := 2
# The swept test's step, as a share of the hit radius.
const SUB_STEP := 0.5
const MAX_SUB_STEPS := 64
const RETURN_TINT: Color = DefenseHypeArtLayout.PARRY_FLASH[0]
# A hit or a block breaks it up into crumbs, over this long.
const CRUMB_TIME := 0.2
const CRUMB_COUNT := 7
const CRUMB_SPREAD := 46.0
const CRUMB_COLOR := Color(0.83, 0.6, 0.25)

static var placeholder_texture: ImageTexture

var kind := &"fastball"
var attack_id := &"mason_fastball"
var player: Node2D
var body: Node2D

var from := Vector2.ZERO
var to := Vector2.ZERO
var flight := 0.12
var live_lead := 0.06
var live_tail := 0.14
var radius := 15.0
var arc := 0.0
var heading := Vector2.LEFT
var clock := 0.0
var flying := false
var resolved := false
var result := HitInfo.Result.IGNORED
var fading := false
var fade_left := 0.0
var returning := false
var return_from := Vector2.ZERO
var return_to := Vector2.ZERO
var return_time := 0.16
var return_clock := 0.0

var spec := {}
var sheet: Sprite2D
var streak_sheet: Sprite2D
var streak_line: Line2D
var trail: Line2D
var puff_clock := 0.0


func _ready() -> void:
	z_index = Z_INDEX
	add_to_group(HAZARD_GROUP)


# `lob` lifts the path into an arc that high at its middle, back down on the target.
func launch(start: Vector2, target: Vector2, flight_time: float, lead: float, tail: float, hit_radius: float, lob := 0.0) -> void:
	attack_id = IDS.get(kind, &"mason_fastball")
	from = start
	to = target
	flight = maxf(flight_time, 0.001)
	live_lead = lead
	live_tail = tail
	radius = hit_radius
	arc = lob
	heading = from.direction_to(to) if from.distance_to(to) > 0.5 else Vector2.LEFT
	clock = 0.0
	flying = true
	global_position = from.round()
	_build()
	_place_art()


func _physics_process(delta: float) -> void:
	if returning:
		_fly_back(delta)
		return
	if fading:
		fade_left -= delta
		modulate.a = clampf(fade_left / MasonArtLayout.BALL_FADE, 0.0, 1.0)
		if fade_left <= 0.0:
			queue_free()
			return
	if not flying:
		return
	var before := clock
	clock += delta
	if kind == &"changeup" and not resolved:
		_puff(delta)
	if not resolved:
		_resolve(before, clock)
	if not flying or returning:
		return
	global_position = point_at(clock).round()
	_place_art()
	_draw_trail()
	if not resolved and clock > flight + live_tail:
		resolved = true
		answered.emit(HitInfo.Result.IGNORED)
	if resolved and not fading:
		_start_fade()


# Where it is `t` seconds after leaving his hand: straight at the target, lifted by the lob, and on past it.
func point_at(t: float) -> Vector2:
	var u := t / flight
	var at := from + (to - from) * u
	if arc > 0.0 and u < 1.0:
		at.y -= arc * 4.0 * u * (1.0 - u)
	return at


func contact_time() -> float:
	return flight


# Batted back by a parry: lit in the parry's colour and flown into his head at `target` over `time`. It is the player's
# now, so nothing of his clears it and it can't hurt them.
func bat_back(target: Vector2, time: float) -> void:
	remove_from_group(HAZARD_GROUP)
	returning = true
	flying = false
	fading = false
	modulate.a = 1.0
	return_from = global_position
	return_to = target
	return_time = maxf(time, 0.001)
	return_clock = 0.0
	heading = return_from.direction_to(return_to) if return_from.distance_to(return_to) > 0.5 else -heading
	if is_instance_valid(sheet):
		sheet.modulate = RETURN_TINT
	if is_instance_valid(streak_sheet):
		streak_sheet.modulate = RETURN_TINT
	_place_art()
	_fade_trail()


#THE HIT

# Swept from its last step to this one, inside the live window only: the hurtbox first, else the dodge ghost.
func _resolve(t0: float, t1: float) -> void:
	if not is_instance_valid(player):
		return
	var window_start := flight - live_lead
	var window_end := flight + live_tail
	if t1 < window_start or t0 > window_end:
		return
	var a := maxf(t0, window_start)
	var b := minf(t1, window_end)
	var steps := clampi(ceili(point_at(a).distance_to(point_at(b)) / (radius * SUB_STEP)), 1, MAX_SUB_STEPS)
	var hurt := _rect_of(player.hurtBox)
	var ghost := Rect2()
	var ghost_on: bool = player.defense.ghost_active
	if ghost_on:
		ghost = _rect_of(player.dodge_ghost)
	var near := false
	for i in steps + 1:
		var t := lerpf(a, b, float(i) / steps)
		var at := point_at(t)
		if _touches(at, hurt):
			global_position = at.round()
			var outcome: int = player.receive_hit(_hit())
			match outcome:
				HitInfo.Result.PARRIED, HitInfo.Result.BLOCKED, HitInfo.Result.HIT:
					_answer(outcome)
			return
		if ghost_on and not near and _touches(at, ghost):
			near = true
	if near:
		player.receive_near_miss(_hit())


func _touches(at: Vector2, box: Rect2) -> bool:
	return at.clamp(box.position, box.end).distance_squared_to(at) <= radius * radius


func _rect_of(area: Area2D) -> Rect2:
	var shape: CollisionShape2D = area.get_node("CollisionShape2D")
	return shape.global_transform * shape.shape.get_rect()


# From the player's own hurtbox centre, so any facing answers it: the parry is a timing check, not an aiming one.
func _hit() -> RefCounted:
	var centre: Vector2 = player.hurtBox.get_node("CollisionShape2D").global_position
	return HitInfo.make(attack_id, self, centre, body)


func _answer(outcome: int) -> void:
	resolved = true
	result = outcome
	answered.emit(outcome)
	if returning:
		return
	if outcome == HitInfo.Result.HIT or outcome == HitInfo.Result.BLOCKED:
		_crumbs(global_position)
		flying = false
		_fade_trail()
		queue_free()


func _start_fade() -> void:
	fading = true
	fade_left = MasonArtLayout.BALL_FADE
	_fade_trail()


func _fly_back(delta: float) -> void:
	return_clock = minf(return_clock + delta, return_time)
	global_position = return_from.lerp(return_to, return_clock / return_time).round()
	clock += delta
	_place_art()
	if return_clock >= return_time:
		returning = false
		arrived.emit()
		queue_free()


#WHAT IS DRAWN

func _build() -> void:
	spec = MasonArtLayout.ball(kind)
	match spec.scheme:
		&"spin_streaks":
			streak_sheet = _sheet(spec.streaks, spec.directions * spec.frames_per_direction)
			sheet = _sheet(spec.texture, spec.hframes)
		_:
			streak_line = Line2D.new()
			streak_line.width = spec.streak_width
			streak_line.default_color = spec.streak
			streak_line.begin_cap_mode = Line2D.LINE_CAP_ROUND
			add_child(streak_line)
			sheet = Sprite2D.new()
			sheet.texture = _placeholder_texture()
			add_child(sheet)
	if kind == &"quick":
		sheet.modulate = MasonArtLayout.QUICK_TINT
		if is_instance_valid(streak_sheet):
			streak_sheet.modulate = MasonArtLayout.QUICK_TINT
	if kind != &"changeup" or spec.scheme == &"placeholder":
		trail = Line2D.new()
		trail.name = "PitchTrail"
		trail.width = MasonArtLayout.PLACEHOLDER_BALL.trail_width
		trail.default_color = MasonArtLayout.PLACEHOLDER_BALL.trail
		trail.z_index = Z_INDEX
		trail.add_to_group(HAZARD_GROUP)
		get_parent().add_child(trail)
		trail.global_position = Vector2.ZERO


func _sheet(path: String, frames: int) -> Sprite2D:
	var sprite := Sprite2D.new()
	sprite.texture = load(path)
	sprite.hframes = frames
	sprite.scale = Vector2.ONE * MasonArtLayout.SCALE
	add_child(sprite)
	return sprite


func _place_art() -> void:
	match spec.get("scheme", &""):
		&"spin_streaks":
			var per: int = spec.frames_per_direction
			streak_sheet.frame = MasonArtLayout.streak_direction(heading, spec.directions) * per + int(clock / spec.streak_time) % per
			sheet.frame = int(clock / spec.frame_time) % int(spec.hframes)
		&"placeholder":
			streak_line.points = PackedVector2Array([Vector2.ZERO, -heading * spec.streak_length])


func _draw_trail() -> void:
	if not is_instance_valid(trail) or trail.modulate.a < 1.0:
		return
	var points := PackedVector2Array()
	var samples := 12 if arc > 0.0 else 1
	for i in samples + 1:
		points.append(point_at(clock * i / samples).round())
	trail.points = points


func _fade_trail() -> void:
	if not is_instance_valid(trail) or trail.modulate.a < 1.0:
		return
	trail.modulate.a = 0.99
	var fade := trail.create_tween()
	fade.tween_property(trail, "modulate:a", 0.0, MasonArtLayout.PLACEHOLDER_BALL.trail_fade)
	fade.tween_callback(trail.queue_free)


func _exit_tree() -> void:
	if is_instance_valid(trail) and trail.modulate.a >= 1.0:
		trail.queue_free()


# The code-drawn stand-in: a gold nugget with a dark rim, at the drawn nugget's size.
static func _placeholder_texture() -> ImageTexture:
	if placeholder_texture != null:
		return placeholder_texture
	var look: Dictionary = MasonArtLayout.PLACEHOLDER_BALL
	var half: Vector2 = look.body
	var size := Vector2i(ceili(half.x * 2.0) + 2, ceili(half.y * 2.0) + 2)
	var image := Image.create(size.x, size.y, false, Image.FORMAT_RGBA8)
	var centre := Vector2(size) / 2.0
	for y in size.y:
		for x in size.x:
			var d := ((Vector2(x, y) + Vector2(0.5, 0.5) - centre) / half).length()
			if d <= 1.0:
				var rim: float = 1.0 - look.rim_width / minf(half.x, half.y)
				image.set_pixel(x, y, look.rim if d > rim else look.fill)
	placeholder_texture = ImageTexture.create_from_image(image)
	return placeholder_texture


# The changeup's cream puffs, left where it was and played once (MasonArtLayout.puff, when it is in).
func _puff(delta: float) -> void:
	var look := MasonArtLayout.puff()
	if look.is_empty():
		return
	puff_clock += delta
	if puff_clock < MasonArtLayout.PUFF_EVERY:
		return
	puff_clock -= MasonArtLayout.PUFF_EVERY
	var cloud := Sprite2D.new()
	cloud.name = "PitchPuff"
	cloud.texture = load(look.texture)
	cloud.hframes = look.hframes
	cloud.scale = Vector2.ONE * look.scale
	cloud.z_index = Z_INDEX - 1
	cloud.add_to_group(HAZARD_GROUP)
	get_parent().add_child(cloud)
	cloud.global_position = global_position.round()
	var play := cloud.create_tween()
	for i in range(1, look.hframes):
		play.tween_interval(look.frame_time)
		play.tween_callback(cloud.set_frame.bind(i))
	play.tween_interval(look.frame_time)
	play.tween_callback(cloud.queue_free)


# Breading crumbs flung off where it broke up, then gone.
func _crumbs(at: Vector2) -> void:
	var burst := Node2D.new()
	burst.name = "PitchCrumbs"
	burst.z_index = Z_INDEX
	burst.add_to_group(HAZARD_GROUP)
	get_parent().add_child(burst)
	burst.global_position = at.round()
	var fly := burst.create_tween().set_parallel(true)
	for i in CRUMB_COUNT:
		var crumb := Polygon2D.new()
		crumb.polygon = PackedVector2Array([Vector2(-4, -4), Vector2(4, -4), Vector2(4, 4), Vector2(-4, 4)])
		crumb.color = CRUMB_COLOR
		burst.add_child(crumb)
		var out := Vector2.from_angle(TAU * (i + randf() * 0.5) / CRUMB_COUNT) * CRUMB_SPREAD
		fly.tween_property(crumb, "position", out, CRUMB_TIME)
	fly.tween_property(burst, "modulate:a", 0.0, CRUMB_TIME)
	fly.chain().tween_callback(burst.queue_free)
