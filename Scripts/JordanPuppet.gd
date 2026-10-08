extends CharacterBody2D

# A boss demon-god Jordan has raised as a marionette in his last phase: JordanCombo summons two of them an attack, one
# on each of his hands. A light actor, never an instance of the boss's live fight scene: it is drawn off the boss's own
# approved sheets - the red-and-black twins once they are in, the live sheets under the placeholder recolour until then
# (JordanPuppetLayout) - and plays his animations by name off his own art layout, or his puppet row where his layout has
# none (JordanPuppetLayout.anim). It hangs from Jordan's strings by its
# back (hook_point), lends an attack its boss's hazards by answering what they ask of their owner (play_sfx, stop_sfx,
# sfx_player_for, play_fx, floor_layer, hype), and takes the finisher the way a boss does: three punches
# (JordanCombo.punch_out), then the tiered mash and its boss's own juggle (JordanPuppetJuggled). Every uppercut that
# lands runs up the strings into Jordan for exactly one (JordanGodScript.take_uppercut); a native punch never counts.
# Built in code, never a scene: make(), then added to the god's Stage layer, where it y-sorts with the player by its
# feet. Its origin is its soles.
#
# THE FROZEN CONTRACT (the build plan's section 2): make(), boss, god, sprite, sprite_base_position, current_anim,
# anim_done, anim_next, floor_layer, hype and hype_changed, payoff_done, play(), hook_point(), flinch(),
# set_punchable(), open_for_uppercut(), play_sfx(), sfx_player_for(), play_fx(), take_punch(), PlayerFinisher's
# interface (can_be_dazed ... get_juggle_point) and BossJuggled's host (after_juggle, land_juggled). The rest is its
# own and JordanCombo's.
#
# THE PAYOFF: open_for_uppercut() arms it for one finisher. payoff_done(bars) goes out once that finisher is over: as
# the puppet gets up from its juggle, with the uppercuts that landed, or as the finisher ends with none (a fizzle, a
# whiff, an abort) with 0.

const PuppetLayout := preload("res://Scripts/JordanPuppetLayout.gd")
const JordanPuppetJuggled := preload("res://Scripts/JordanPuppetJuggled.gd")
const Disintegrate := preload("res://Scripts/Disintegrate.gd")
const FightOutro := preload("res://Scripts/FightOutro.gd")
const PlayerScript := preload("res://Scripts/PlayerScript.gd")
const GodLayout := preload("res://Scripts/JordanGodLayout.gd")

const SCALE := PuppetLayout.SCALE
# What the rise and the recall clip him to: everything over his soles' line.
const ABOVE_FLOOR := Rect2(-1200, -2400, 2400, 2400)

signal hype_changed(value: float)
signal payoff_done(bars: int)

var boss: StringName
var god: Node2D
var sprite: Sprite2D
var sprite_base_position := Vector2.ZERO
var current_anim := &""
var anim_done := false
var anim_next := &""
var floor_layer: Node2D
# Greyson's hype meter reads it (GreysonHypeMeterUI): setting it tells the meter.
var hype := 0.0:
	set(value):
		if is_equal_approx(value, hype):
			return
		hype = value
		hype_changed.emit(value)

var face_left := false
var feet := Vector2.ZERO
var layout: GDScript
var spec := {}
var anim := {}
var anim_step := 0
var anim_clock := 0.0
var mask: Polygon2D
var hurtbox: Area2D
var hurt_shape: CollisionShape2D
var juggled: Node
var hooks_table: GDScript
var tint: ShaderMaterial
var juggle_table := {}
# Whether the juggle's sheet is his twin.
var juggle_twin := false
var sfx := {}
# His layout's SFX table (JordanPuppetLayout.sfx), which the players above are built from.
var sfx_table := {}
var hit_sound: AudioStreamPlayer
var flash_tween: Tween
var jolt_tween: Tween
var move_tween: Tween
var dissolve_tween: Tween
var punchable := false
# One finisher's worth: armed by open_for_uppercut(), spent by the payoff.
var armed := false
var dazed := false
var bars := 0


static func make(boss_name: StringName, at_feet: Vector2, facing_left: bool, jordan: Node2D) -> CharacterBody2D:
	var puppet = new()
	puppet.boss = PuppetLayout.key(boss_name)
	puppet.feet = at_feet.round()
	puppet.face_left = facing_left
	puppet.god = jordan
	puppet.floor_layer = jordan.layer(&"floor")
	puppet.name = "Puppet_%s" % puppet.boss
	return puppet


func _ready() -> void:
	collision_layer = 0
	collision_mask = 0
	global_position = feet
	spec = PuppetLayout.spec(boss)
	layout = PuppetLayout.layout(boss)
	hooks_table = PuppetLayout.hooks_table()
	tint = ShaderMaterial.new()
	tint.shader = load(PuppetLayout.TINT_SHADER)
	tint.set_shader_parameter("deep", PuppetLayout.TINT.deep)
	tint.set_shader_parameter("red", PuppetLayout.TINT.red)
	tint.set_shader_parameter("bone", PuppetLayout.TINT.bone)
	tint.set_shader_parameter("keyline", PuppetLayout.TINT.keyline)
	mask = Polygon2D.new()
	mask.name = "Mask"
	add_child(mask)
	sprite = Sprite2D.new()
	sprite.name = "Sprite2D"
	sprite.scale = Vector2.ONE * SCALE
	mask.add_child(sprite)
	sprite_base_position = sprite.position
	_build_juggle_table()
	_build_hurtbox()
	_build_sounds()
	juggled = JordanPuppetJuggled.new()
	juggled.name = "Juggled"
	juggled.body = self
	juggled.hurtbox = hurtbox
	juggled.state_machine = self
	add_child(juggled)
	play(spec.idle)


#ANIMATION

# One of his animations by name (JordanPuppetLayout.anim). A non-looping one holds its last frame when it ends, unless
# `next` follows.
func play(anim_name: StringName, next := &"") -> void:
	var row: Dictionary = PuppetLayout.anim(boss, anim_name)
	current_anim = anim_name
	anim = row
	anim_next = next
	anim_step = 0
	anim_clock = 0.0
	anim_done = false
	var twin := PuppetLayout.twin_path(boss, row.sheet)
	var sheet: Texture2D = load(twin if twin != "" else row.sheet)
	var frame := PuppetLayout.frame_of(boss, row)
	# Back to the first frame before the grid changes, so the current one can't be out of range.
	sprite.frame = 0
	sprite.texture = sheet
	sprite.vframes = maxi(roundi(sheet.get_height() / frame.y), 1)
	sprite.hframes = maxi(roundi(sheet.get_width() / frame.x), 1)
	sprite.offset = PuppetLayout.sheet_offset(boss, row)
	sprite.flip_h = PuppetLayout.flipped(boss, row, face_left)
	use_twin_material(twin != "")
	_show_frame()


func _process(delta: float) -> void:
	if anim.is_empty() or anim_done:
		return
	anim_clock += delta
	while anim_clock >= _frame_time():
		anim_clock -= _frame_time()
		if anim_step < anim.frames.size() - 1:
			anim_step += 1
		elif anim.loop:
			anim_step = 0
		else:
			anim_done = true
			if anim_next != &"":
				play(anim_next)
			return
		_show_frame()


func _physics_process(delta: float) -> void:
	if juggled != null and juggled.drawing:
		juggled.Physics_Update(delta)


func _frame_time() -> float:
	var times: Array = anim.times
	return maxf(float(times[mini(anim_step, times.size() - 1)]), 0.001)


func _show_frame() -> void:
	sprite.frame = mini(int(anim.frames[anim_step]), sprite.hframes * sprite.vframes - 1)


# Turned to face left or right: every sheet that mirrors does, and what a punch reaches with it.
func face(left: bool) -> void:
	face_left = left
	if not anim.is_empty():
		sprite.flip_h = PuppetLayout.flipped(boss, anim, face_left)
	_fit_hurtbox()


# His twin sheets are drawn in their colours already; everything else wears the recolour.
func use_twin_material(twin: bool) -> void:
	sprite.material = null if twin else tint


#WHERE THINGS ARE ON HIM

# World px of a hook on this frame: &"back" (the strings'), &"head", &"wrist_l"/&"wrist_r", &"knee_l"/&"knee_r". The
# back is the twins' measured texel on this sheet's frame when there is one (JordanPuppetLayout.hooks_table), riding
# the sprite - the rise, a flinch, a juggle's lift - exactly as it is drawn; otherwise, up in a juggle and lying after
# one, the juggle table's middle (its tumble_centre), which the finisher's camera follows too, and on his feet a fixed
# texel on his main frame, as every other hook is.
func hook_point(hook: StringName) -> Vector2:
	if hook == &"back":
		var measured = PuppetLayout.measured_back(hooks_table, boss, _sheet_name(), sprite.frame)
		if measured is Vector2:
			return _texel_on_sprite(measured)
		if juggled != null and (juggled.drawing or juggled.lingering):
			return juggled.air_point()
	var texel: Vector2 = spec.hooks.get(hook, spec.hooks[&"back"])
	return _texel_world(texel, spec.frame, PuppetLayout.sheet_offset(boss, {}))


# A texel's centre on a frame of `frame` texels drawn on `offset`, where the sprite draws it now.
func _texel_world(texel: Vector2, frame: Vector2, offset: Vector2) -> Vector2:
	var local := texel + Vector2(0.5, 0.5) - frame / 2.0
	if sprite.flip_h:
		local.x = -local.x
	return mask.to_global(sprite.position + (local + offset) * sprite.scale)


# A texel's centre on the frame the sprite is showing, on its sheet as it is now: its own grid and offset.
func _texel_on_sprite(texel: Vector2) -> Vector2:
	var frame := sprite.texture.get_size() / Vector2(sprite.hframes, sprite.vframes)
	return _texel_world(texel, frame, sprite.offset)


# Whether his strings are drawn over him on this frame: his back is to the camera (JordanPuppetLayout.strings_over).
func strings_over() -> bool:
	return PuppetLayout.strings_over(hooks_table, _sheet_name(), sprite.frame)


# The sheet showing, by its file name with no extension: a twin's is its source's.
func _sheet_name() -> String:
	return sprite.texture.resource_path.get_file().get_basename() if sprite.texture != null else ""


# His layout's crown on the frame showing, or his head hook where it has none.
func _crown_point() -> Vector2:
	if current_anim == &"" or not layout.has_method(&"crown"):
		return _texel_world(spec.hooks[&"head"], spec.frame, PuppetLayout.sheet_offset(boss, {}))
	return _texel_on_sprite(layout.crown(current_anim))


#THE HURTBOX

func _build_hurtbox() -> void:
	hurtbox = Area2D.new()
	hurtbox.name = "Hurtbox"
	hurtbox.collision_layer = 0
	hurtbox.collision_mask = 0
	hurtbox.monitoring = false
	hurtbox.monitorable = false
	hurtbox.add_to_group("enemy")
	hurt_shape = CollisionShape2D.new()
	hurt_shape.name = "CollisionShape2D"
	hurt_shape.shape = RectangleShape2D.new()
	hurtbox.add_child(hurt_shape)
	add_child(hurtbox)
	_fit_hurtbox()


# His layout's body box off his soles, mirrored with him.
func _fit_hurtbox() -> void:
	if hurt_shape == null:
		return
	var box: Rect2 = spec.body_box
	var soles: Vector2 = spec.feet
	var rect := Rect2((box.position.x - soles.x) * SCALE, (box.position.y - soles.y - 1.0) * SCALE,
		box.size.x * SCALE, box.size.y * SCALE)
	if face_left:
		rect.position.x = -rect.end.x
	hurt_shape.position = rect.get_center()
	(hurt_shape.shape as RectangleShape2D).size = rect.size


# A target the player turns to and the punch-out can take, or not: the player faces the nearest one while free.
func set_punchable(on: bool) -> void:
	punchable = on
	if on:
		hurtbox.add_to_group(PlayerScript.BOSS_TARGET_GROUP)
	elif hurtbox.is_in_group(PlayerScript.BOSS_TARGET_GROUP):
		hurtbox.remove_from_group(PlayerScript.BOSS_TARGET_GROUP)


#THE PUNCH-OUT AND THE FINISHER

# One of the punch-out's punches: a flash, a jolt away from the player and the hit.
func flinch() -> void:
	var spec_flinch: Dictionary = PuppetLayout.FLINCH
	if flash_tween != null and flash_tween.is_valid():
		flash_tween.kill()
	sprite.modulate = spec_flinch.flash
	flash_tween = create_tween()
	flash_tween.tween_property(sprite, "modulate", Color.WHITE, spec_flinch.flash_time)
	if jolt_tween != null and jolt_tween.is_valid():
		jolt_tween.kill()
	var away := 1.0 if face_left else -1.0
	sprite.position = sprite_base_position + Vector2(spec_flinch.jolt * away, 0.0)
	jolt_tween = create_tween()
	jolt_tween.tween_property(sprite, "position", sprite_base_position, spec_flinch.jolt_time)
	hit_sound.pitch_scale = PuppetLayout.HIT_SOUND.pitch
	hit_sound.play()


# Armed for one finisher: from here can_be_dazed() and can_be_juggled() answer yes, and its payoff goes out once.
func open_for_uppercut() -> void:
	armed = true
	dazed = false
	bars = 0
	var finisher := _finisher()
	if finisher != null and not finisher.finished.is_connected(_on_finisher_finished):
		finisher.finished.connect(_on_finisher_finished, CONNECT_ONE_SHOT)


# Native punches never count: the punch-out's presses are the combo's own.
func take_punch(_amount: int) -> int:
	return 0


func can_be_dazed() -> bool:
	return armed and not dazed and _god_alive()


func enter_daze() -> void:
	dazed = true


func exit_daze(_finisher_landed: bool) -> void:
	dazed = false


func end_recovery(stagger_time: float) -> bool:
	if not _god_alive():
		return false
	if juggled.drawing:
		juggled.recover(stagger_time)
	return true


# Never reached in the tiered mash; one uppercut into him all the same. The full amount back when it landed, so a
# supercharged one spends the hype as everywhere else.
func take_finisher(amount: int) -> int:
	if not _god_alive():
		return 0
	if god.take_uppercut(self, _finisher().uppercut_count()) <= 0:
		return 0
	bars += 1
	return amount


func get_max_health() -> int:
	return god.get_max_health()


func get_health_ratio() -> float:
	return god.get_health_ratio()


func get_daze_anchor() -> Vector2:
	return _crown_point() + Vector2(0.0, -PuppetLayout.daze_gap(boss))


func get_finisher_hurtbox() -> Area2D:
	return hurtbox


func can_be_juggled() -> bool:
	return armed and _god_alive()


func begin_juggle() -> void:
	if not juggled.drawing:
		juggled.Enter()


func juggle_lift(px: float) -> void:
	if juggled.drawing:
		juggled.lift(px)


func juggle_pose(pose: StringName, crater := false) -> void:
	if juggled.drawing:
		juggled.pose(pose, crater)


func juggle_headroom() -> float:
	return juggled.headroom()


# One off Jordan whatever the finisher's share, and one more for the uppercut a full hype meter boosts
# (PlayerFinisher.uppercut_count), with the hit's pitch; the amount it asked for back, so the supercharged last
# uppercut spends the hype (PlayerFinisher only spends it for damage the supercharge added).
func take_juggle_hit(amount: int, pitch: float) -> int:
	if not _god_alive():
		return 0
	if god.take_uppercut(self, _finisher().uppercut_count(), pitch) <= 0:
		return 0
	bars += 1
	return amount


func get_juggle_point() -> Vector2:
	return juggled.air_point()


func is_juggled() -> bool:
	return juggled != null and juggled.drawing


# BossJuggled's host: up from the juggle after its lying beat, so the finisher is over and the attack goes on.
func after_juggle(_delay: float) -> void:
	juggled.Exit()
	play(spec.idle)
	_pay_out(bars)


# Killed in the air (Jordan's 20th), it lands lying and stays down for his defeat (stay_down).
func land_juggled(_final_state_name: String) -> void:
	juggled.Exit()


# Jordan is down: a juggle still in the air ends lying on its `down` loop rather than getting up.
func stay_down() -> void:
	if juggled.drawing:
		juggled.final_state = "down"


func juggle_art() -> Dictionary:
	return juggle_table


func _build_juggle_table() -> void:
	juggle_table = PuppetLayout.juggle(boss).duplicate()
	var twin := PuppetLayout.twin_path(boss, juggle_table.texture)
	juggle_twin = twin != ""
	if juggle_twin:
		juggle_table.texture = twin


func _on_finisher_finished() -> void:
	if not juggled.drawing:
		_pay_out(bars)


func _pay_out(count: int) -> void:
	if not armed:
		return
	armed = false
	dazed = false
	payoff_done.emit(count)


func _god_alive() -> bool:
	return is_instance_valid(god) and not god.defeated and god.boss_health > 0


func _finisher() -> Node:
	var scene := get_tree().current_scene if is_inside_tree() else null
	var player: Node = scene.get_node_or_null(FightOutro.PLAYER_PATH) if scene else null
	return player.finisher if player else null


#THE RISE, THE RECALL AND HIS DEFEAT

# Under the floor line, clipped to it, ready to rise.
func hide_under_floor() -> void:
	set_clipped(true)
	sprite.position = sprite_base_position + Vector2(0.0, PuppetLayout.rise_px(boss))


func rise(seconds: float) -> Tween:
	set_clipped(true)
	_kill_move()
	move_tween = create_tween()
	move_tween.tween_property(sprite, "position:y", sprite_base_position.y, maxf(seconds, 0.01)) \
		.set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	move_tween.tween_callback(set_clipped.bind(false))
	return move_tween


func sink(seconds: float) -> Tween:
	set_clipped(true)
	_kill_move()
	move_tween = create_tween()
	move_tween.tween_property(sprite, "position:y", sprite_base_position.y + PuppetLayout.rise_px(boss), maxf(seconds, 0.01)) \
		.set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	return move_tween


# Only what is over his soles' line shows, while he rises through the floor or sinks back into it.
func set_clipped(on: bool) -> void:
	if on:
		mask.polygon = PackedVector2Array([ABOVE_FLOOR.position, Vector2(ABOVE_FLOOR.end.x, ABOVE_FLOOR.position.y),
			ABOVE_FLOOR.end, Vector2(ABOVE_FLOOR.position.x, ABOVE_FLOOR.end.y)])
		mask.clip_children = CanvasItem.CLIP_CHILDREN_ONLY
	else:
		mask.clip_children = CanvasItem.CLIP_CHILDREN_DISABLED
		mask.polygon = PackedVector2Array()


func is_clipped() -> bool:
	return mask.clip_children != CanvasItem.CLIP_CHILDREN_DISABLED


# The sprite back on its rest spot, whatever was moving it: the juggle owns it from here.
func settle_sprite() -> void:
	_kill_move()
	if jolt_tween != null and jolt_tween.is_valid():
		jolt_tween.kill()
	set_clipped(false)
	sprite.position = sprite_base_position
	sprite.rotation = 0.0


func _kill_move() -> void:
	if move_tween != null and move_tween.is_valid():
		move_tween.kill()


# His strings cut: he folds, unless a juggle already has him lying.
func crumple() -> void:
	if juggled.drawing or juggled.lingering:
		return
	play(spec.crumple)


# Dissolved texel by texel, the recolour kept to the last: Disintegrate's own shader on a twin, the recolour's copy of
# it on the live sheets. The tween, which hides him at its end.
func dissolve(seconds: float) -> Tween:
	if sprite.material != tint:
		dissolve_tween = Disintegrate.start(self, sprite, seconds)
		return dissolve_tween
	dissolve_tween = create_tween()
	dissolve_tween.tween_method(func(value: float) -> void: tint.set_shader_parameter("progress", value), 0.0, 1.0, seconds)
	dissolve_tween.tween_callback(sprite.hide)
	return dissolve_tween


#SOUND AND FX, FOR THE HAZARDS HE LENDS AN ATTACK

func _build_sounds() -> void:
	hit_sound = AudioStreamPlayer.new()
	hit_sound.name = "HitSfx"
	hit_sound.stream = load(PuppetLayout.HIT_SOUND.stream)
	hit_sound.volume_db = PuppetLayout.HIT_SOUND.volume_db
	add_child(hit_sound)
	sfx_table = PuppetLayout.sfx(boss)
	var voices: Dictionary = layout.get_script_constant_map().get("SFX_VOICES", {})
	for key in sfx_table:
		var variants := _sfx_variants(key)
		if variants.is_empty():
			continue
		var players: Array[AudioStreamPlayer] = []
		for i in maxi(voices.get(key, 1), variants.size()):
			var variant: Dictionary = variants[i % variants.size()]
			var player := AudioStreamPlayer.new()
			player.stream = variant.stream
			player.volume_db = variant.volume_db
			player.pitch_scale = variant.pitch
			player.set_meta(&"base_pitch", variant.pitch)
			player.set_meta(&"base_db", variant.volume_db)
			add_child(player)
			players.append(player)
		sfx[key] = players


# His SFX table's streams for `key`: its own files (or file), or its stand-in where the table has one and they
# aren't in, each with its level and pitch; a looping key gets its own looping copy.
func _sfx_variants(key: StringName) -> Array[Dictionary]:
	var row: Dictionary = sfx_table[key]
	var files: Array = row.get("streams", [row.stream] if row.has("stream") else [])
	var levels: Array = row.get("volume_dbs", [row.get("volume_db", 0.0)])
	var variants: Array[Dictionary] = []
	for i in files.size():
		var stream := _sfx_stream(files[i], row)
		if stream != null:
			variants.append({stream = stream, volume_db = levels[mini(i, levels.size() - 1)], pitch = row.get("pitch", 1.0)})
	if variants.is_empty() and row.has("stand_in"):
		var stand_in := _sfx_stream(row.stand_in, row)
		if stand_in != null:
			variants.append({stream = stand_in, volume_db = row.get("stand_in_db", 0.0), pitch = row.get("stand_in_pitch", 1.0)})
	return variants


func _sfx_stream(path: String, row: Dictionary) -> AudioStream:
	if not ResourceLoader.exists(path):
		return null
	var stream: AudioStream = load(path)
	if stream == null or not row.get("loop", false):
		return stream
	stream = stream.duplicate()
	if stream is AudioStreamWAV:
		stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
		if stream.loop_end <= stream.loop_begin:
			stream.loop_end = int(stream.get_length() * stream.mix_rate)
	elif "loop" in stream:
		stream.loop = true
	return stream


func play_sfx(key: StringName, pitch := 1.0) -> void:
	var players: Array = sfx.get(key, [])
	if players.is_empty():
		return
	var player: AudioStreamPlayer = players.pop_front()
	players.append(player)
	player.pitch_scale = player.get_meta(&"base_pitch") * pitch
	player.play()


func stop_sfx(key: StringName) -> void:
	for player: AudioStreamPlayer in sfx.get(key, []):
		player.stop()


# A player of its own for `key` under `owner`, at the key's level and pitch but not started, for a sound one hazard
# owns and takes with it (GreysonScript.sfx_player_for's contract).
func sfx_player_for(key: StringName, owner: Node) -> AudioStreamPlayer:
	var variants: Array[Dictionary] = _sfx_variants(key) if sfx_table.has(key) else []
	var variant: Dictionary = variants[0] if not variants.is_empty() else {stream = null, volume_db = 0.0, pitch = 1.0}
	var player := AudioStreamPlayer.new()
	player.stream = variant.stream
	player.volume_db = variant.volume_db
	player.pitch_scale = variant.pitch
	player.set_meta(&"base_db", variant.volume_db)
	player.set_meta(&"base_pitch", variant.pitch)
	owner.add_child(player)
	return player


# One of his FX sheets played once at `at` on the god's Fx layer, in the attack's hazard group so its release takes
# it. The sprite, or null for an effect his layout draws in code, or a layout with no fx() at all.
func play_fx(key: StringName, at: Vector2) -> Sprite2D:
	if not layout.has_method(&"fx"):
		return null
	var row: Dictionary = layout.fx(key)
	if not row.has("texture"):
		return null
	var fx := Sprite2D.new()
	fx.texture = load(row.texture)
	fx.hframes = row.get("hframes", 1)
	fx.vframes = row.get("vframes", 1)
	fx.scale = Vector2.ONE * SCALE
	fx.offset = row.get("offset", Vector2.ZERO)
	fx.add_to_group(GodLayout.HAZARD_GROUP)
	var layer: Node2D = god.layer(&"fx")
	fx.position = layer.to_local(at.round())
	layer.add_child(fx)
	var times: Array = row.get("times", [row.get("frame_time", 0.05)])
	var run := fx.create_tween()
	for i in fx.hframes * fx.vframes:
		run.tween_callback(fx.set_frame.bind(i))
		run.tween_interval(times[mini(i, times.size() - 1)])
	run.tween_callback(fx.queue_free)
	return fx
