extends State

# The Trueshot barrage: after the last cast he teleports to the middle of each side of the ring in turn
# - top, left, bottom, right - and fires a golden wave from each, aimed at the player. One shot, 1.55 s:
#   OUT     0.15 s  he squeezes out where he stands.
#   IN      0.15 s  he reforms on the station, facing in.
#   CHARGE  0.90 s  the red badge for the whole of it, the charge pose, a gold glow at his mouth that
#                   grows, and an aim line of gold dots tracking the player. trueshot_lock_lead before
#                   the release the aim LATCHES: the line and the glow flash white and a ding plays.
#   FIRE    0.35 s  the wave leaves on the release frame and he holds the fire pose.
# Then the next station, and after the right one he goes home to Spent.
#
# THE AIM. The raw angle from his mouth to the player's hurtbox centre, clamped to trueshot_max_turn
# either side of the station's inward normal and snapped to trueshot_step, every heading the wave is
# drawn at. The dead band round each boundary between two steps is trueshot_hysteresis wide, so the line
# doesn't flicker between two headings as the player walks along one. Half of it either side, not all of
# it past the boundary: that would leave the heading a step inside the clamp unable to reach it. The spot
# the wave leaves from slides along the chord, up to trueshot_offset_max, so its path runs through the
# point the aim latched on; the wave's middle starts trueshot_lead ahead of that spot.
#
# THE BURST (R9). The wave flies away from him, so on its own it would never reach a player standing on
# him, hugging him or in the pocket behind him. As it leaves, it also hits his body grown by
# trueshot_burst_margin, stretched back to the rope behind him and on to the wave's first position, for
# trueshot_burst_time - as part of the same shot.
#
# THE COINCIDENCE GUARD (R2): as the aim is about to latch, a live bolt within trueshot_guard_range of the
# player and within trueshot_guard_angle of straight at them holds the latch - and the release -
# trueshot_guard_hold longer, once a shot, with the badge put back up for what is left. A wave and a
# bolt never arrive together.
#
# FREEZE SAFETY: every wait is a Physics_Update accumulator and every effect is node-bound.

const ParryTell := preload("res://Scripts/ParryTell.gd")
const MattArtLayout := preload("res://Scripts/MattArtLayout.gd")
const WAVE_SCENE := preload("res://Scenes/Bosses/MattTrueshotScene.tscn")

const WAVE_ID := &"matt_trueshot"

@export var body : CharacterBody2D

@onready var state_machine = get_parent()

enum Beat { OUT, IN, CHARGE, FIRE }

var beat := Beat.OUT
var beat_clock := 0.0
var station_index := 0
var lock_at := 0.0
var release_at := 0.0
var latched := false
var guard_used := false
# The aim: a snapped heading, its angle, and how far along the chord the wave leaves from.
var aim_angle := 0.0
var aim_heading := Vector2.RIGHT
var aim_lateral := 0.0
var aim_point := Vector2.ZERO
var aim_tracked := false
# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
var glow: Node2D
var aim_line: Node2D
var dots: Array[Node2D] = []
var fx_clock := 0.0
# Every shot this barrage fired, for a test: station, heading, lateral, latched point, spawn, times.
var shots: Array = []


func Enter() -> void:
	released = false
	station_index = 0
	shots.clear()
	body.velocity = Vector2.ZERO
	body.set_hurtbox_active(false)
	_begin_out()


func Exit() -> void:
	release()


# Idempotent: the badge, the charge's hum, the glow, the line, his facing and the HUD go whichever way
# the barrage ended.
func release() -> void:
	if released:
		return
	released = true
	if is_instance_valid(body):
		ParryTell.clear(body)
		body.stop_sfx(&"trueshot_charge")
		body.restore_hud()
	_drop_aim()


func Physics_Update(delta: float) -> void:
	beat_clock += delta
	fx_clock += delta
	match beat:
		Beat.OUT:
			if beat_clock >= state_machine.teleport_out:
				var station: Dictionary = _station()
				beat = Beat.IN
				beat_clock = 0.0
				body.teleport_in(station.feet, station.normal.x < 0.0)
				body.update_hud_fade(_charge_anim())
		Beat.IN:
			if beat_clock >= state_machine.teleport_in:
				_begin_charge()
		Beat.CHARGE:
			if not latched:
				_track()
				if beat_clock >= lock_at:
					_lock()
			_draw_aim()
			if beat_clock >= release_at:
				_release()
		Beat.FIRE:
			if beat_clock >= state_machine.trueshot_after:
				station_index += 1
				if station_index < state_machine.STATIONS.size():
					_begin_out()
				else:
					state_machine.on_child_transition(self, "Spent")


func _station() -> Dictionary:
	return state_machine.STATIONS[station_index]


# The station's own view: the front from the top, the back from the bottom, the side from either side.
func _charge_anim() -> StringName:
	return MattArtLayout.station_anim(_station().name, &"charge")


func _fire_anim() -> StringName:
	return MattArtLayout.station_anim(_station().name, &"fire")


func _begin_out() -> void:
	beat = Beat.OUT
	beat_clock = 0.0
	body.teleport_out()


func _begin_charge() -> void:
	beat = Beat.CHARGE
	beat_clock = 0.0
	latched = false
	guard_used = false
	aim_tracked = false
	lock_at = state_machine.trueshot_charge - state_machine.trueshot_lock_lead
	release_at = state_machine.trueshot_charge
	body.play_anim(_charge_anim())
	body.play_sfx(&"trueshot_charge")
	ParryTell.telegraph(body, WAVE_ID, release_at, _tell_anchor)
	_build_aim()
	_track()
	_draw_aim()


func _tell_anchor() -> Vector2:
	return body.tell_anchor(_charge_anim())


#THE AIM

func _track() -> void:
	var mouth := _mouth()
	aim_point = _player_centre()
	var normal_angle: float = (_station().normal as Vector2).angle()
	var raw := (aim_point - mouth).angle()
	var turn := deg_to_rad(state_machine.trueshot_max_turn)
	var clamped := normal_angle + clampf(angle_difference(normal_angle, raw), -turn, turn)
	var step := deg_to_rad(state_machine.trueshot_step)
	var boundary := step / 2.0 + deg_to_rad(state_machine.trueshot_hysteresis) / 2.0
	if not aim_tracked or absf(angle_difference(aim_angle, clamped)) > boundary:
		aim_angle = normal_angle + snappedf(angle_difference(normal_angle, clamped), step)
		aim_tracked = true
	aim_heading = Vector2.from_angle(aim_angle)
	var across := (aim_point - mouth).dot(aim_heading.orthogonal())
	aim_lateral = clampf(across, -state_machine.trueshot_offset_max, state_machine.trueshot_offset_max)


# The latch, or the guard holding it off for a bolt about to arrive.
func _lock() -> void:
	if not guard_used and _bolt_incoming():
		guard_used = true
		lock_at += state_machine.trueshot_guard_hold
		release_at += state_machine.trueshot_guard_hold
		ParryTell.telegraph(body, WAVE_ID, release_at - beat_clock, _tell_anchor)
		return
	latched = true
	body.play_sfx(&"trueshot_lock")


func _bolt_incoming() -> bool:
	var at := _player_centre()
	var cone := deg_to_rad(state_machine.trueshot_guard_angle)
	for bolt in state_machine.live_bolts():
		var to_player: Vector2 = at - bolt.global_position
		if to_player.length() > state_machine.trueshot_guard_range:
			continue
		if absf((bolt.heading as Vector2).angle_to(to_player)) <= cone:
			return true
	return false


# Where the wave leaves him: his mouth slid along the chord onto the latched point's line.
func _spawn_point() -> Vector2:
	return _mouth() + aim_heading.orthogonal() * aim_lateral


func _release() -> void:
	beat = Beat.FIRE
	beat_clock = 0.0
	ParryTell.clear(body)
	body.stop_sfx(&"trueshot_charge")
	body.play_anim(_fire_anim())
	body.play_sfx(&"trueshot_fire")
	var spawn := _spawn_point()
	var wave: Node2D = WAVE_SCENE.instantiate()
	wave.heading = aim_heading
	wave.speed = state_machine.trueshot_speed
	wave.view_margin = state_machine.trueshot_view_margin
	wave.player = state_machine.get_player()
	wave.burst_zone = burst_zone()
	wave.burst_time = state_machine.trueshot_burst_time
	state_machine.add_hazard(wave, spawn + aim_heading * state_machine.trueshot_lead, body.projectile_layer)
	shots.append({"station": _station().name, "heading": aim_heading, "lateral": aim_lateral,
		"point": aim_point, "spawn": spawn, "mouth": _mouth(), "lock_at": lock_at, "release_at": release_at,
		"guarded": guard_used, "wave": wave, "burst": wave.burst_zone})
	_launch_wisps(spawn)
	_drop_aim()


# The burst, in world px, for the aim as it stands: his body box grown by the margin, stretched back to
# the rope behind him, and hulled with the wave's first position so nothing between him and it is left.
func burst_zone() -> PackedVector2Array:
	var box := MattArtLayout.local_rect(MattArtLayout.BODY_BOX)
	box.position += body.global_position
	box = box.grow(state_machine.trueshot_burst_margin)
	var normal: Vector2 = _station().normal
	var ropes: Rect2 = state_machine.ROPES
	var back := box.get_center()
	if normal.x != 0.0:
		back.x = ropes.position.x if normal.x > 0.0 else ropes.end.x
	if normal.y != 0.0:
		back.y = ropes.position.y if normal.y > 0.0 else ropes.end.y
	box = box.expand(back)
	var points := PackedVector2Array([box.position, Vector2(box.end.x, box.position.y), box.end,
		Vector2(box.position.x, box.end.y)])
	var start: Vector2 = _spawn_point() + aim_heading * state_machine.trueshot_lead
	for point in MattArtLayout.scaled_poly(MattArtLayout.trueshot_hit_poly(), MattArtLayout.SCALE, aim_heading.angle()):
		points.append(start + point)
	var hull := Geometry2D.convex_hull(points)
	# convex_hull closes the loop by repeating its first point.
	hull.remove_at(hull.size() - 1)
	return hull


#WHAT IS DRAWN
# The glow at his mouth and the line of dots, both in the hazard group on the projectile layer.

func _build_aim() -> void:
	_drop_aim()
	var glow_spec := MattArtLayout.fx(&"glow")
	if MattArtLayout.uses_final_fx(&"glow"):
		var sheet := Sprite2D.new()
		sheet.texture = load(glow_spec.texture)
		sheet.hframes = glow_spec.hframes
		sheet.scale = Vector2.ONE * MattArtLayout.SCALE
		glow = sheet
	else:
		var disc := Polygon2D.new()
		disc.polygon = MattArtLayout.circle(1.0, 16)
		disc.color = glow_spec.color
		glow = disc
	state_machine.add_hazard(glow, _mouth(), body.projectile_layer)
	aim_line = Node2D.new()
	state_machine.add_hazard(aim_line, Vector2.ZERO, body.projectile_layer)
	dots.clear()


func _draw_aim() -> void:
	if not is_instance_valid(glow) or not is_instance_valid(aim_line):
		return
	var grown := clampf(beat_clock / maxf(lock_at, 0.0001), 0.0, 1.0)
	var lit := latched and int((beat_clock - lock_at) / _flash_time()) % 2 == 0
	glow.global_position = _mouth().round()
	var glow_spec := MattArtLayout.fx(&"glow")
	if glow is Sprite2D:
		var sheet := glow as Sprite2D
		if latched:
			sheet.frame = glow_spec.lock_frame + (0 if lit else 1)
		else:
			sheet.frame = mini(int(grown * glow_spec.grow_frames), glow_spec.grow_frames - 1)
	else:
		glow.scale = Vector2.ONE * lerpf(glow_spec.from_radius, glow_spec.to_radius, grown)
		(glow as Polygon2D).color = glow_spec.lock_color if latched and lit else glow_spec.color
	var dot_spec := MattArtLayout.fx(&"aim_dot")
	var start := _spawn_point()
	var length := _line_length(start, aim_heading)
	var count := int(length / dot_spec.spacing)
	while dots.size() < count:
		dots.append(_build_dot(dot_spec))
	for i in dots.size():
		var dot := dots[i]
		dot.visible = i < count
		if not dot.visible:
			continue
		dot.global_position = (start + aim_heading * dot_spec.spacing * (i + 1)).round()
		if dot is Sprite2D:
			(dot as Sprite2D).frame = 1 if latched else 0
		else:
			(dot as Polygon2D).color = dot_spec.lit_color if latched else dot_spec.color


func _flash_time() -> float:
	return MattArtLayout.fx(&"glow").flash_time


func _build_dot(spec: Dictionary) -> Node2D:
	var dot: Node2D
	if MattArtLayout.uses_final_fx(&"aim_dot"):
		var sheet := Sprite2D.new()
		sheet.texture = load(spec.texture)
		sheet.hframes = spec.hframes
		sheet.scale = Vector2.ONE * MattArtLayout.SCALE
		dot = sheet
	else:
		var square := Polygon2D.new()
		var half: float = spec.size / 2.0
		square.polygon = PackedVector2Array([Vector2(-half, -half), Vector2(half, -half), Vector2(half, half), Vector2(-half, half)])
		square.color = spec.color
		dot = square
	aim_line.add_child(dot)
	return dot


# From the spot the wave leaves to the ropes, along the heading.
func _line_length(from: Vector2, heading: Vector2) -> float:
	var ropes: Rect2 = state_machine.ROPES
	var reach := INF
	if heading.x > 0.0:
		reach = minf(reach, (ropes.end.x - from.x) / heading.x)
	elif heading.x < 0.0:
		reach = minf(reach, (ropes.position.x - from.x) / heading.x)
	if heading.y > 0.0:
		reach = minf(reach, (ropes.end.y - from.y) / heading.y)
	elif heading.y < 0.0:
		reach = minf(reach, (ropes.position.y - from.y) / heading.y)
	return maxf(reach, 0.0)


func _drop_aim() -> void:
	for node in [glow, aim_line]:
		if is_instance_valid(node):
			node.queue_free()
	glow = null
	aim_line = null
	dots.clear()


# Cyan-white wisps curling back from where the wave left, the Mystic Shot's cyan.
func _launch_wisps(at: Vector2) -> void:
	if MattArtLayout.uses_final_fx(&"launch"):
		var pick: Array = MattArtLayout.wave_art(&"launch", aim_heading)
		var spec: Dictionary = pick[0]
		var sheet := Sprite2D.new()
		sheet.texture = load(spec.texture)
		sheet.hframes = spec.hframes
		sheet.flip_h = pick[2]
		sheet.flip_v = pick[3]
		sheet.scale = Vector2.ONE * MattArtLayout.SCALE
		var first: int = pick[1] * spec.frames_per_heading
		sheet.frame = first
		state_machine.add_hazard(sheet, at, body.projectile_layer)
		var play := sheet.create_tween()
		for i in range(1, spec.frames_per_heading):
			play.tween_interval(spec.frame_time)
			play.tween_callback(sheet.set_frame.bind(first + i))
		play.tween_interval(spec.frame_time)
		play.tween_callback(sheet.queue_free)
		return
	var spec := MattArtLayout.fx(&"launch")
	var wisp := Polygon2D.new()
	wisp.polygon = MattArtLayout.star(spec.points, spec.radius, spec.inner_ratio)
	wisp.color = spec.color
	state_machine.add_hazard(wisp, at, body.projectile_layer)
	var fade := wisp.create_tween().set_parallel()
	fade.tween_property(wisp, "scale", Vector2.ONE * 1.8, spec.time)
	fade.tween_property(wisp, "modulate:a", 0.0, spec.time)
	fade.chain().tween_callback(wisp.queue_free)


#WHERE THINGS ARE

# Where the wave leaves him: his mouth, or on the side and back views the spot the artist drew it
# leaving from, on the fire frame.
func _mouth() -> Vector2:
	return body.mouth_point(_fire_anim())


func _player_centre() -> Vector2:
	var player: Node2D = state_machine.get_player()
	if player == null or not is_instance_valid(player):
		return _mouth() + (_station().normal as Vector2) * 400.0
	return player.hurtBox.get_node("CollisionShape2D").global_position
