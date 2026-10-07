extends Node2D

# Greyson's doom orb (the user's 2026-09-30 playtest: players didn't see why he poses, that posing fills his hype
# meter, or that a full meter is the fight lost - and it had to be plain without text). His meter made physical over
# his head, where the player is already looking:
#   - it forms at his first banked cell and grows a stage a cell, throbbing and crackling, the bomb's own light on the
#     floor under it growing with it; stage 6 is his spirit bomb itself: through his arm going up it rides from his
#     head to the cannon's muzzle, and the bomb gathers on from it (hands_to_bomb);
#   - on each bank the crowd's energy streaks into it from the stands and ringside, and it grows as they land; the
#     crowd's cheer a little louder each cell (his cannon's hum already climbs with his meter);
#   - from vignette_from on, a purple vignette creeps in from the screen's edges with a heartbeat, full as the bomb
#     starts;
#   - the meter up top flashes as it grows and throbs with it, so the two read as one thing;
#   - a hit that empties his meter (GreysonScript.hit_resets_hype) bursts it: the pop, the glass, the streaks flung
#     back out to the crowd, the crowd's boo;
#   - the first time it forms in a fight, the view eases in on him for a moment.
# It is a layer of its own in his scene, sorted just over the floor (the zones) and under both fighters, and it fades
# while the player stands over it; the vignette is a canvas layer under the HUD. Each approved sheet is used once its
# file exists (GreysonArtLayout.DOOM_ORB_ART, laid out as DOOM_ORB_FINAL); until then placeholders cut from the spirit
# bomb's own crowd orbs, the hype meter's pop and a code gradient.
# Everything moves on its own physics step and its own node's tweens, so a pause or a finisher's freeze holds it.

const Layout := preload("res://Scripts/GreysonArtLayout.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")

const STAGES := 6
# The placeholder's rows (bomb_orb): the orb's width in texels, row by row.
const ROW_TEXELS := [10.0, 16.0, 26.0, 40.0]
const POP_SHEET := "res://Assets/UI/greyson_hype_pop.png"
const POP_FRAMES := 3
const POP_TEXELS := 14.0

# Set before it enters the tree.
var body: Node
# The approved sheets' textures by DOOM_ORB_ART's keys, loaded from those that exist as it enters the tree unless a
# test has filled it first; the orb's own sheet there is what switches the orb to the final art.
var art: Dictionary = {}

var spec: Dictionary = Layout.DOOM_ORB
var final_spec: Dictionary = Layout.DOOM_ORB_FINAL
var final_art := false
# The stage it shows, and the stage his meter stands at: they differ while a bank's streaks are on their way in.
var stage := 0
var target := 0
# His spirit bomb has it (hands_to_bomb), or the fight is decided: nothing bursts until his meter is empty again.
var handed_off := false
# Riding to the muzzle through his arm going up, from where.
var riding := false
var ride_from := Vector2.ZERO
var nudged := false
var clock := 0.0
var flash := 0.0
var arrival_left := 0.0
var glow: Sprite2D
var orb: Sprite2D
var light: Sprite2D
var burst: Sprite2D
var burst_clock := -1.0
var burst_row := 0
var streaks: Array = []
var bolts: Array = []
var crackle_clock := 0.0
var vignette_layer: CanvasLayer
var vignette: TextureRect
var vignette_alpha := 0.0
var heart_clock := 0.0
var heart_age := INF
var cheer_players: Array = []
var rng := RandomNumberGenerator.new()
# Where its centre and its foot stand now.
var centre := Vector2.ZERO
var foot := Vector2.ZERO
# For tests: how many times it has formed, grown, thumped, burst and nudged the view, and the streaks it has sent in
# and out.
var formed := 0
var grown := 0
var thumps := 0
var bursts := 0
var nudges := 0
var streaks_in := 0
var streaks_out := 0


func _ready() -> void:
	if art.is_empty():
		for key in Layout.DOOM_ORB_ART:
			if ResourceLoader.exists(Layout.DOOM_ORB_ART[key]):
				art[key] = load(Layout.DOOM_ORB_ART[key])
	final_art = art.has("orb")
	# Just over the floor layer in his y-sorted scene: over the zones, under both fighters.
	position = Vector2(0.0, body.floor_layer.position.y + 1.0)
	light = Sprite2D.new()
	light.texture = load(Layout.fx(&"bomb_light").texture)
	light.centered = false
	light.scale = Vector2.ONE * Layout.SCALE
	light.position = -position
	light.modulate.a = 0.0
	add_child(light)
	if final_art:
		# The glow under the orb, on the same frame.
		if art.has("glow"):
			glow = _sheet(art.glow, final_spec.frames, STAGES, final_spec.frame_size, final_spec.pivot)
			var add := CanvasItemMaterial.new()
			add.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
			glow.material = add
			glow.hide()
		orb = _sheet(art.orb, final_spec.frames, STAGES, final_spec.frame_size, final_spec.pivot)
	else:
		var sheet: Dictionary = Layout.fx(&"bomb_orb")
		orb = Sprite2D.new()
		orb.texture = load(sheet.texture)
		orb.hframes = sheet.hframes
		orb.vframes = sheet.vframes
		add_child(orb)
	orb.hide()
	if art.has("burst"):
		burst = _sheet(art.burst, final_spec.burst_frames, final_spec.burst_rows, final_spec.burst_frame_size,
			final_spec.burst_pivot)
	else:
		burst = Sprite2D.new()
		burst.texture = load(POP_SHEET)
		burst.hframes = POP_FRAMES
		add_child(burst)
	burst.hide()
	_build_vignette()
	cheer_players = body.sfx_players.get(&"crowd_cheer", [])
	rng.seed = 20260930
	stage = _stage_of(body.hype)
	target = stage
	body.hype_changed.connect(_on_hype_changed)


func _exit_tree() -> void:
	_tune_cheer(0)


# The diameter in px it shows at `at_stage` (1-6).
func diameter(at_stage: int) -> float:
	if final_art:
		return 2.0 * final_spec.radii[at_stage - 1] * Layout.SCALE
	var step: Array = spec.stages[at_stage - 1]
	return ROW_TEXELS[step[0]] * step[1]


func is_shown() -> bool:
	return orb.visible


# One of the approved sheets at SCALE, centred on its pivot: `columns` frames a row, `rows` rows of `size` texels.
func _sheet(texture: Texture2D, columns: int, rows: int, size: Vector2, pivot: Vector2) -> Sprite2D:
	var sprite := Sprite2D.new()
	sprite.texture = texture
	sprite.hframes = columns
	sprite.vframes = rows
	sprite.offset = size / 2.0 - pivot
	sprite.scale = Vector2.ONE * Layout.SCALE
	add_child(sprite)
	return sprite


func _stage_of(hype: float) -> int:
	return clampi(floori(hype + 0.001), 0, STAGES)


func _on_hype_changed(value: float) -> void:
	var now := _stage_of(value)
	if handed_off:
		if value <= 0.0:
			handed_off = false
			riding = false
			stage = 0
			target = 0
		return
	if now > target:
		target = now
		_tune_cheer(target)
		_send_streaks(true)
		if stage == 0 and not nudged and spec.nudge:
			_nudge()
	elif now < target:
		target = now
		_tune_cheer(target)
		if now == 0 and stage > 0:
			_burst()
		else:
			stage = now


func _physics_process(delta: float) -> void:
	clock += delta
	var sm = body.state_machine
	var over: bool = sm.final_brawl_entered or body.defeated or sm.player_defeated or sm.loss_started
	var bomb = sm.states.get("SpiritBomb")
	if sm.current_state == bomb and not handed_off:
		_to_the_bomb()
	elif over and not handed_off and (stage > 0 or target > 0 or not streaks.is_empty()):
		_let_go()
	# Past the arm by any way - a held skip included - the sphere has it.
	if riding and (sm.current_state != bomb or not (bomb.beat in [bomb.Beat.OUT, bomb.Beat.IN, bomb.Beat.ARM])):
		hands_to_bomb()
	_place(bomb)
	orb.visible = _showing()
	_step_streaks(delta)
	_step_orb(delta)
	_step_light(delta)
	_step_crackle(delta)
	_step_burst(delta)
	_step_vignette(delta, sm.current_state == bomb)
	_step_meter()


# Gone with him through a teleport, the out sheet and the in sheet both: his sprite hides and shows on their FX's
# own frames, between two physics steps, and the orb goes and comes back with the teleport as a whole.
func _showing() -> bool:
	var sm = body.state_machine
	return stage > 0 and body.sprite.visible and not (body.current_anim in [&"teleport_out", &"teleport_in"]) \
		and not (sm.final_brawl_entered or body.defeated or sm.player_defeated)


# Where it stands: its foot gap over his crown, clear of his bar and meter up top and inside the screen (pushed down
# behind his head rather than over the HUD); riding up to the cannon's muzzle through the bomb's ARM beat.
func _place(bomb: Node) -> void:
	var radius := diameter(maxi(stage, 1)) / 2.0
	if riding and bomb != null and bomb.beat == bomb.Beat.ARM:
		var to: Vector2 = body.muzzle_point(&"spirit") + final_spec.handoff_lift
		var weight: float = clampf(1.0 - bomb.beat_left / bomb.arm_time, 0.0, 1.0)
		foot = ride_from.lerp(to, weight * weight * (3.0 - 2.0 * weight)).round()
		centre = foot - Vector2(0.0, radius)
		return
	var at: Vector2 = body.crown_point() + Vector2(0.0, -spec.gap - radius)
	var keep: Rect2 = body.state_machine.HUD_FADE_RECT
	if at.x + radius > keep.position.x and at.x - radius < keep.end.x:
		at.y = maxf(at.y, keep.end.y + radius)
	var screen := ScreenView.VIEW_SIZE
	centre = Vector2(clampf(at.x, radius, screen.x - radius), clampf(at.y, radius, screen.y - radius)).round()
	foot = centre + Vector2(0.0, radius)
	if riding:
		ride_from = foot


func _step_orb(delta: float) -> void:
	flash = maxf(flash - delta * 3.0, 0.0)
	arrival_left = maxf(arrival_left - delta, 0.0)
	var fade: float = spec.player_fade if stage > 0 and _player_over() else 1.0
	if glow:
		glow.visible = orb.visible
	if stage <= 0:
		return
	if final_art:
		# The sheet pulses, crackles and flashes in its own frames, from its pivot on the orb's foot.
		var loop: Array = final_spec.loop_frames
		var column: int = final_spec.flash_frame if arrival_left > 0.0 else loop[int(clock / final_spec.frame_times[stage - 1]) % loop.size()]
		orb.position = to_local(foot)
		orb.frame = (stage - 1) * final_spec.frames + column
		orb.modulate = Color(1.0, 1.0, 1.0, fade)
		if glow:
			glow.position = orb.position
			glow.frame = orb.frame
			glow.modulate.a = fade
		return
	var step: Array = spec.stages[stage - 1]
	var sheet: Dictionary = Layout.fx(&"bomb_orb")
	orb.position = to_local(centre)
	orb.scale = Vector2.ONE * step[1]
	orb.frame = step[0] * sheet.hframes + int(clock / sheet.frame_time) % sheet.hframes
	var bright: float = 1.0 + spec.pulse_bright * _pulse() + flash
	orb.modulate = Color(bright, bright, bright, fade)


# The player's body box over the orb.
func _player_over() -> bool:
	var player: Node2D = body.state_machine.get_player()
	if player == null:
		return false
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	var radius := diameter(maxi(stage, 1)) / 2.0
	return box.intersects(Rect2(centre - Vector2.ONE * radius, Vector2.ONE * 2.0 * radius))


# 0 to 1 over the placeholder's throb, peaking at its start.
func _pulse() -> float:
	var period: float = spec.pulse_times[maxi(stage, 1) - 1]
	return pow(1.0 - fmod(clock, period) / period, 3.0)


func _step_light(delta: float) -> void:
	var want: float = spec.light_alphas[stage - 1] if stage > 0 and orb.visible else 0.0
	light.modulate.a = move_toward(light.modulate.a, want, delta * 0.8)


func _step_crackle(delta: float) -> void:
	for bolt in bolts.duplicate():
		bolt.left -= delta
		if bolt.left <= 0.0:
			bolt.line.queue_free()
			bolts.erase(bolt)
	if final_art or stage < spec.crackle_from or not orb.visible:
		return
	crackle_clock += delta
	if crackle_clock < spec.crackle_every:
		return
	crackle_clock = 0.0
	var radius := diameter(stage) / 2.0
	for i in spec.crackle_bolts:
		var line := Line2D.new()
		line.width = 3.0
		line.default_color = spec.crackle_color
		var angle := rng.randf() * TAU
		var at := centre + Vector2.from_angle(angle) * radius * 0.8
		var reach := radius * rng.randf_range(0.5, 0.9)
		for k in 5:
			var along := Vector2.from_angle(angle) * reach * k / 4.0
			var jag := Vector2.from_angle(angle + PI / 2.0) * rng.randf_range(-10.0, 10.0) if k > 0 else Vector2.ZERO
			line.add_point(to_local(at + along + jag).round())
		add_child(line)
		bolts.append({line = line, left = spec.crackle_time})


# A bank's streaks from the crowd into it (`inward`), or a burst's flung back out to the crowd: the approved streak
# sheet, its row turned to its heading each step, or the placeholder's crowd orb with a trail.
func _send_streaks(inward: bool) -> void:
	for i in spec.streaks:
		var crowd := _crowd_point()
		var line := Line2D.new()
		line.width = spec.streak_width
		var ramp := Gradient.new()
		ramp.set_color(0, Color(spec.streak_color, 0.0))
		ramp.set_color(1, spec.streak_head)
		line.gradient = ramp
		line.begin_cap_mode = Line2D.LINE_CAP_ROUND
		line.end_cap_mode = Line2D.LINE_CAP_ROUND
		line.visible = not art.has("streak")
		add_child(line)
		var head: Sprite2D
		if art.has("streak"):
			head = _sheet(art.streak, final_spec.streak_frames, final_spec.streak_rows, final_spec.streak_frame_size,
				final_spec.streak_pivot)
		else:
			var sheet: Dictionary = Layout.fx(&"bomb_orb")
			head = Sprite2D.new()
			head.texture = load(sheet.texture)
			head.hframes = sheet.hframes
			head.vframes = sheet.vframes
			head.frame = spec.streak_row * sheet.hframes + i % sheet.hframes
			head.scale = Vector2.ONE * Layout.SCALE
			add_child(head)
		head.hide()
		streaks.append({line = line, head = head, crowd = crowd, inward = inward, delay = rng.randf() * spec.streak_spread,
			age = 0.0, bend = rng.randf_range(-1.0, 1.0) * spec.streak_arc, trail = [], last = Vector2.INF})
		if inward:
			streaks_in += 1
		else:
			streaks_out += 1


# A point in the stands across the top of the screen, or ringside down one side.
func _crowd_point() -> Vector2:
	if rng.randf() < 0.6:
		var top: Rect2 = spec.crowd_top
		return Vector2(rng.randf_range(top.position.x, top.end.x), rng.randf_range(top.position.y, top.end.y))
	var sides: Rect2 = spec.crowd_sides
	var x: float = sides.position.x if rng.randf() < 0.5 else sides.end.x
	return Vector2(x, rng.randf_range(sides.position.y, sides.end.y))


func _step_streaks(delta: float) -> void:
	var landing := false
	for streak in streaks.duplicate():
		streak.age += delta
		var t: float = clampf((streak.age - streak.delay) / spec.streak_time, 0.0, 1.0)
		var from: Vector2 = streak.crowd if streak.inward else centre
		var to: Vector2 = centre if streak.inward else streak.crowd
		var eased := t * t if streak.inward else 1.0 - (1.0 - t) * (1.0 - t)
		var side: Vector2 = (to - from).orthogonal().normalized()
		var head: Vector2 = from.lerp(to, eased) + side * streak.bend * 4.0 * eased * (1.0 - eased)
		if streak.age >= streak.delay:
			streak.trail.append(head)
			while streak.trail.size() > 2 and streak.trail[0].distance_to(head) > spec.streak_tail:
				streak.trail.pop_front()
		var points := PackedVector2Array()
		for point in streak.trail:
			points.append(to_local(point).round())
		streak.line.points = points
		var sprite: Sprite2D = streak.head
		sprite.visible = not streak.trail.is_empty()
		sprite.position = to_local(head).round()
		if art.has("streak") and streak.last != Vector2.INF and head != streak.last:
			sprite.frame = heading_row(head - streak.last) * final_spec.streak_frames \
				+ int(streak.age / final_spec.streak_frame_time) % final_spec.streak_frames
		streak.last = head
		if t >= 1.0:
			streak.line.queue_free()
			sprite.queue_free()
			streaks.erase(streak)
			landing = landing or streak.inward
	if landing and streaks.all(func(s): return not s.inward):
		_grow_to(target)


# The approved streak's row for `velocity`: 360/streak_rows degrees a row from row 0 flying right, y down.
func heading_row(velocity: Vector2) -> int:
	var rows: int = final_spec.streak_rows
	return posmod(roundi(atan2(velocity.y, velocity.x) / (TAU / rows)), rows)


func _grow_to(to_stage: int) -> void:
	if to_stage <= stage or handed_off:
		return
	if stage == 0:
		formed += 1
	stage = to_stage
	grown += 1
	flash = 1.0
	arrival_left = final_spec.flash_time


# A hit emptied his meter: the pop where it was, the glass, the energy flung back out, and the crowd's boo if the
# pose's own hasn't come (a hit in his Break).
func _burst() -> void:
	var was := maxi(stage, 1)
	bursts += 1
	burst.position = to_local(centre)
	if art.has("burst"):
		burst_row = 0 if was < final_spec.burst_big_from else 1
	else:
		burst_row = 0
		burst.scale = Vector2.ONE * maxf(3.0, roundf(diameter(was) / POP_TEXELS))
	burst.frame = burst_row * burst.hframes
	burst.show()
	burst_clock = 0.0
	_drop_streaks()
	_send_streaks(false)
	stage = 0
	body.play_sfx(&"orb_burst")
	var sm = body.state_machine
	if sm.current_state != sm.states.get("Pose"):
		sm.crowd(&"boo", 1.5)


func _step_burst(delta: float) -> void:
	if burst_clock < 0.0:
		return
	burst_clock += delta
	var frame := 0
	if art.has("burst"):
		var times: Array = final_spec.burst_frame_times
		var left := burst_clock
		while frame < times.size() and left >= times[frame]:
			left -= times[frame]
			frame += 1
	else:
		frame = int(burst_clock / spec.burst_frame_time)
	if frame >= burst.hframes:
		burst.hide()
		burst_clock = -1.0
		return
	burst.frame = burst_row * burst.hframes + frame


func _drop_streaks() -> void:
	for streak in streaks:
		streak.line.queue_free()
		streak.head.queue_free()
	streaks.clear()


# His meter is full and the bomb has started: the orb shows stage 6 over him through the bomb's teleport, rides to
# the muzzle through his arm going up, and gives way to the bomb's sphere as it gathers (hands_to_bomb).
func _to_the_bomb() -> void:
	handed_off = true
	_drop_streaks()
	_tune_cheer(0)
	stage = STAGES
	target = STAGES
	riding = true
	ride_from = foot


# The bomb's gather begins: the sphere takes over where the orb is. The bomb's frame to gather on from: the one
# stage 6 matches, with the approved art.
func hands_to_bomb() -> int:
	riding = false
	stage = 0
	return final_spec.handoff_bomb_frame if final_art else 0


# The fight is decided some other way: it goes without bursting.
func _let_go() -> void:
	handed_off = true
	riding = false
	stage = 0
	target = 0
	_drop_streaks()
	_tune_cheer(0)


func _nudge() -> void:
	nudged = true
	nudges += 1
	var tree := get_tree()
	var radius := diameter(maxi(target, 1)) / 2.0
	var at: Vector2 = body.crown_point() + Vector2(0.0, -spec.gap - radius)
	ScreenView.zoom_to(tree, spec.nudge_zoom, at, spec.nudge_in)
	var back := create_tween()
	back.tween_interval(spec.nudge_in + spec.nudge_hold)
	back.tween_callback(func() -> void:
		# Only its own nudge: a finisher or a Break that has taken the view since keeps it.
		if is_equal_approx(ScreenView.zoom, spec.nudge_zoom):
			ScreenView.zoom_to(tree, 1.0, ScreenView.base_focus, spec.nudge_out))


func _tune_cheer(cells: int) -> void:
	for cheer in cheer_players:
		if is_instance_valid(cheer):
			cheer.volume_db = cheer.get_meta(&"base_db") + spec.cheer_gain_db * cells


func _build_vignette() -> void:
	vignette_layer = CanvasLayer.new()
	# Over the arena and the fighters, under his HUD and the player's (both on layer 1).
	vignette_layer.layer = 0
	add_child(vignette_layer)
	vignette = TextureRect.new()
	if art.has("vignette"):
		vignette.texture = art.vignette
		vignette.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	else:
		var ramp := Gradient.new()
		ramp.offsets = PackedFloat32Array([0.0, 0.6, 1.0])
		ramp.colors = PackedColorArray([Color(spec.vignette_color, 0.0), Color(spec.vignette_color, 0.0),
			Color(spec.vignette_color, spec.vignette_edge)])
		var texture := GradientTexture2D.new()
		texture.gradient = ramp
		texture.fill = GradientTexture2D.FILL_RADIAL
		texture.fill_from = Vector2(0.5, 0.5)
		texture.fill_to = Vector2(1.0, 0.5)
		texture.width = 256
		texture.height = 256
		vignette.texture = texture
	vignette.stretch_mode = TextureRect.STRETCH_SCALE
	vignette.mouse_filter = Control.MOUSE_FILTER_IGNORE
	vignette.size = ScreenView.VIEW_SIZE
	vignette.modulate.a = 0.0
	vignette_layer.add_child(vignette)


func _step_vignette(delta: float, bombing: bool) -> void:
	var from: int = spec.vignette_from
	var want := 0.0
	if bombing:
		want = spec.bomb_vignette
	elif stage >= from and orb.visible:
		want = spec.vignette_alphas[mini(stage - from, spec.vignette_alphas.size() - 1)]
	if want > 0.0 and not bombing:
		heart_clock += delta
		if heart_clock >= spec.heartbeat_every:
			heart_clock -= spec.heartbeat_every
			heart_age = 0.0
			thumps += 1
			body.play_sfx(&"orb_thump", spec.thump_pitch)
	else:
		heart_clock = 0.0
	heart_age += delta
	var bump := 0.0
	if heart_age < spec.heartbeat_hold:
		bump = spec.heartbeat_bump
	elif heart_age < spec.heartbeat_hold + spec.heartbeat_ease:
		bump = spec.heartbeat_bump * (1.0 - (heart_age - spec.heartbeat_hold) / spec.heartbeat_ease)
	vignette_alpha = move_toward(vignette_alpha, want, delta * (0.6 if want > vignette_alpha else 2.0))
	vignette.modulate.a = clampf(vignette_alpha + (bump if want > 0.0 else 0.0), 0.0, 1.0)


# The meter up top: a flash as the orb grows, and a glow on each throb, so the two read as one thing.
func _step_meter() -> void:
	var meter: Control = body.hype_meter
	if meter == null:
		return
	var amount := flash
	if stage > 0 and orb.visible:
		amount = maxf(amount, 0.35 * _pulse())
	meter.self_modulate = Color.WHITE.lerp(spec.meter_flash, clampf(amount, 0.0, 1.0))
