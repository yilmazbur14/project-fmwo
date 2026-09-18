extends Node

# The finisher. A charged combo punch that lands in a boss's punish window dazes the boss and stops
# the fight around the player. Alternating punch and dodge fills a meter while the camera closes in,
# and a full meter fires a rising uppercut that takes a chunk of the boss's health and ends the window.
# A fight can also hand the whole thing out at once with begin_auto(), for a read the player has
# already earned: the same daze, no prompt, and the uppercut fires itself.
# A boss takes part by implementing:
#     can_be_dazed() -> bool             alive, in its punish window, not dazed in it yet, and the
#                                        finisher could still deal damage past any phase floor
#     enter_daze()                       at the freeze
#     exit_daze(finisher_landed: bool)   once, whenever the daze ends
#     end_recovery(stagger_time: float) -> bool
#                                        leave the window now, idle stagger_time, then attack again;
#                                        false when that doesn't apply (dead, changing phase)
#     take_finisher(amount: int) -> int  past the hit cap, but not past a phase floor
#     get_max_health() -> int
#     get_daze_anchor() -> Vector2       where the stars circle, about 34 px above the head
#     get_finisher_hurtbox() -> Area2D   with its shape in a child named CollisionShape2D
# besides the `sprite` and get_health_ratio() every boss has.

signal prompt_shown
signal meter_changed(meter: float, next_action: StringName)
signal charge_ended(filled: bool)
signal finished

const FightFreeze := preload("res://Scripts/FightFreeze.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const HitStop := preload("res://Scripts/HitStop.gd")
const FinisherArtLayout := preload("res://Scripts/FinisherArtLayout.gd")

enum Phase { OFF, SETTLE, DAZED, CHARGING, UPPERCUT, FIZZLE }

# Seconds are game time unless noted.
# Time for the charged punch's hit-stop, flash and shake to play out before the fight stops.
@export var daze_settle_time := 0.2
# From the freeze until the prompt shows and presses count.
@export var prompt_delay := 0.1
@export var charge_time_limit := 3.0
# At r alternating presses a second the meter fills in about 1 / (r * gain - drain) seconds: 2 s at 7
# presses a second, 2.95 s at 5.5, never below 2.3. Mashing one key only counts its first press.
@export var meter_gain_per_press := 0.107
@export var meter_drain_per_second := 0.25
# Real seconds: Q and W pressed together arrive in the same input flush however long the frame took,
# and count once.
@export var min_press_interval := 0.03
@export var zoom := 1.5
@export var zoom_in_time := 0.25
@export var zoom_out_time := 0.3
# The zoom centres on the player, pulled this far toward the daze anchor.
@export var focus_boss_weight := 0.35
# Of the boss's max health, at least 1.
@export var finisher_damage_ratio := 0.25
# The same, for an uppercut supercharged by a full hype meter (PlayerHype). Every dial on the
# supercharged contact is bigger than the normal one: that gap is the point.
@export var supercharged_damage_ratio := 0.40
@export var super_impact_hit_stop := 0.35
@export var super_impact_shake := 34.0
@export var super_impact_shake_steps := 10
# Multiplies the view at contact, snapped to, held, then eased back out. Real seconds: the punch
# plays out during the hit-stop.
@export var super_impact_zoom := 1.25
@export var super_impact_zoom_in_time := 0.03
@export var super_impact_zoom_hold := 0.12
@export var super_impact_zoom_out_time := 0.45
@export var super_impact_flash := Color(2.6, 2.2, 0.9)
@export var super_impact_cheer := 4.0
# On the player as the uppercut launches.
@export var super_launch_flash := Color(2.0, 1.6, 0.6)
# How far the uppercut shoves the boss away from the player, and how long the shove takes.
@export var uppercut_knockback := 120.0
@export var super_uppercut_knockback := 240.0
@export var uppercut_knockback_time := 0.3
# px the boss's hurtbox grows by for the reach check.
@export var uppercut_reach := 48.0
@export var impact_hit_stop := 0.15
@export var impact_shake := 16.0
@export var impact_cheer := 2.0
# Stacks on the boss's own hit flash, which tweens modulate.
@export var impact_flash := Color(2.2, 1.9, 1.3)
@export var impact_flash_time := 0.35
# A boss the finisher lands on idles this long, hopping, then attacks again: long enough for the
# player to back off and read what comes next.
@export var stagger_time := 1.2
@export var super_stagger_time := 1.8
@export var stagger_hop_texels := 10
@export var fizzle_time := 0.25
# After the finisher, punch and dodge presses are swallowed for this long, so leftover mashing can't
# throw a punch or spend the next dash's immunity.
@export var post_input_lock := 0.2

# Straight above or below the boss's middle, the player keeps the side they were facing.
const SIDE_DEAD_ZONE := 8.0
const IMPACT_SHAKE_STEPS := 6
const IMPACT_SHAKE_STEP_TIME := 0.03
# The stagger hop: up, down, then a small bounce, stagger_time in all.
const HOP_UP_TIME := 0.18
const HOP_DOWN_TIME := 0.22
const HOP_BOUNCE_TEXELS := 2
const HOP_BOUNCE_TIME := 0.1
# Summed frame deltas land a hair short of a step's start, which would hold a 3-frame step a frame long.
const STEP_TOLERANCE := 0.001

@onready var player: CharacterBody2D = get_parent()
@onready var fx_layer: Node2D = player.get_parent().get_node("FinisherFx")
@onready var super_sfx_player: AudioStreamPlayer = player.get_node("SuperUppercutSfxPlayer")

var phase := Phase.OFF
var boss: Node
var phase_time := 0.0
# From the freeze, through the prompt and the charge.
var daze_time := 0.0
var dazed := false
var prompt_visible := false
var meter := 0.0
var last_action := &""
var last_press_usec := 0
var zoomed := false
var charge_clock := 0.0
var charge_step := 0
var uppercut_step := 0
var flipped := false
var stars: Sprite2D
var stars_clock := 0.0
var input_lock_left := 0.0
# Set by begin_auto(): the charge is already made, so the dazed beat runs on its own clock and no
# press is ever counted.
var auto := false
var auto_hold := 0.0
# Decided when the daze starts: nothing can hit the player during the finisher, so the hype it needs
# can't drain in between. PlayerFinishing reads it for the recoloured sheet.
var supercharged := false


func _ready() -> void:
	player.get_node("Combo").charged_hit_landed.connect(_on_charged_hit_landed)
	# Loaded up front: the local sound is an MP3, and the first supercharged uppercut of a fight must
	# not wait on a decoder to warm up.
	var impact := FinisherArtLayout.super_impact_sfx()
	super_sfx_player.stream = load(impact.stream)
	super_sfx_player.pitch_scale = impact.pitch
	super_sfx_player.volume_db = impact.volume_db


func is_active() -> bool:
	return phase != Phase.OFF


func is_input_locked() -> bool:
	return input_lock_left > 0.0


func charge_time_left() -> float:
	if phase != Phase.DAZED and phase != Phase.CHARGING:
		return 0.0
	return maxf(prompt_delay + charge_time_limit - daze_time, 0.0)


# The freeze and the zoom are static, so they'd outlive the fight scene.
func _exit_tree() -> void:
	if phase != Phase.OFF:
		FightFreeze.unfreeze(get_tree())
		ScreenView.reset(get_tree())


func _input(event: InputEvent) -> void:
	var action := &""
	if event.is_action_pressed("punch"):
		action = &"punch"
	elif event.is_action_pressed("dodge"):
		action = &"dodge"
	if action.is_empty() or (phase == Phase.OFF and not is_input_locked()):
		return
	# Before the event is marked handled: the autoload's device tracker sits below this node in the
	# propagation order and would never see the presses that drive the mash.
	InputSettings.note_device(event)
	get_viewport().set_input_as_handled()
	if (phase == Phase.DAZED and prompt_visible) or phase == Phase.CHARGING:
		_press(action)


# The hit is reported inside a physics flush, where collision can't be taken out of physics.
func _on_charged_hit_landed(target: Node) -> void:
	_try_begin.call_deferred(target)


func _try_begin(target: Node) -> void:
	if phase != Phase.OFF or not is_instance_valid(target) or not target.has_method("can_be_dazed"):
		return
	if player.fight_over or player.playerHealth <= 0 or player.is_grabbed or player.is_talking:
		return
	if not target.can_be_dazed():
		return
	boss = target
	dazed = false
	player.begin_finisher()
	player.combo.reset()
	_set_phase(Phase.SETTLE)


# A fight hands the player the finisher outright, for something they have already earned: the boss is
# dazed, the prompt never shows and the uppercut fires on its own after `hold` seconds of the dazed
# pose, which is the beat that makes it read as "he is reeling, and then you hit him". Everything
# else is the hand-driven path: the same entry guards, the freeze, the supercharge decision, the
# contact, the knockback, the kill rule and the outro. Returns whether it started.
func begin_auto(target: Node, hold := 0.35) -> bool:
	if phase != Phase.OFF:
		return false
	auto = true
	auto_hold = maxf(hold, 0.0)
	_try_begin(target)
	if phase == Phase.OFF:
		auto = false
		return false
	return true


func _process(delta: float) -> void:
	if phase == Phase.OFF:
		input_lock_left = maxf(input_lock_left - delta, 0.0)
		return
	phase_time += delta
	# The uppercut always plays out to its landing, even past a kill.
	if phase != Phase.UPPERCUT and (player.fight_over or not _boss_valid()):
		_abort()
		return
	match phase:
		Phase.SETTLE:
			if phase_time >= daze_settle_time and player.state_machine.current_state.name != "Punching" and not player.combo.report_pending():
				_begin_daze()
		Phase.DAZED:
			daze_time += delta
			if auto:
				# No prompt, no presses and no time limit: the beat is the boss reeling, and then the
				# uppercut, which the charging phase fires on the next frame from a full meter.
				if daze_time >= auto_hold:
					meter = 1.0
					_start_charging()
			elif not prompt_visible and daze_time >= prompt_delay:
				prompt_visible = true
				prompt_shown.emit()
			elif daze_time >= prompt_delay + charge_time_limit:
				_start_fizzle()
		Phase.CHARGING:
			# Before the drain, so the press that filled the meter counts.
			if meter >= 1.0:
				_start_uppercut()
			else:
				daze_time += delta
				meter = maxf(meter - meter_drain_per_second * delta, 0.0)
				_animate_charge(delta)
				if daze_time >= prompt_delay + charge_time_limit:
					_start_fizzle()
		Phase.UPPERCUT:
			_advance_uppercut()
		Phase.FIZZLE:
			if phase_time >= fizzle_time:
				_end_fizzle()
	if phase == Phase.OFF:
		return
	_animate_stars(delta)
	# Every frame, so a shake written straight to the canvas by another script can't linger.
	ScreenView.apply(get_tree())


func _set_phase(new_phase: Phase) -> void:
	phase = new_phase
	phase_time = 0.0


func _begin_daze() -> void:
	# The window can close during the beat.
	if not boss.can_be_dazed():
		player.end_finisher(false)
		_finish()
		return
	boss.enter_daze()
	dazed = true
	supercharged = player.hype.is_full()
	FightFreeze.freeze(get_tree(), [player.get_parent()])
	player.enter_finisher_pose()
	flipped = _boss_on_left()
	_show_pose(_sheet().ready)
	_spawn_stars(boss.get_daze_anchor())
	get_tree().call_group("arena_crowd", "cheer", 1.0)
	daze_time = 0.0
	prompt_visible = false
	meter = 0.0
	last_action = &""
	last_press_usec = 0
	_set_phase(Phase.DAZED)
	if auto:
		# The view closes in over the held beat instead of over a mash, so the uppercut lands on a
		# camera that has already arrived.
		zoomed = true
		ScreenView.zoom_to(get_tree(), zoom, player.global_position.lerp(boss.get_daze_anchor(), focus_boss_weight), zoom_in_time)


func _press(action: StringName) -> void:
	var now := Time.get_ticks_usec()
	if action == last_action or now - last_press_usec < roundi(min_press_interval * 1000000.0):
		return
	last_action = action
	last_press_usec = now
	meter = minf(meter + meter_gain_per_press, 1.0)
	meter_changed.emit(meter, &"dodge" if action == &"punch" else &"punch")
	get_tree().call_group("arena_crowd", "cheer", 0.4)
	if phase == Phase.DAZED:
		_start_charging()


func _start_charging() -> void:
	_set_phase(Phase.CHARGING)
	charge_clock = 0.0
	charge_step = 0
	_show_pose(_sheet().charge[0])
	zoomed = true
	ScreenView.zoom_to(get_tree(), zoom, player.global_position.lerp(boss.get_daze_anchor(), focus_boss_weight), zoom_in_time)


func _animate_charge(delta: float) -> void:
	var frame_times: Array = _sheet().charge_frame_time
	charge_clock += delta
	var frame_time := lerpf(frame_times[0], frame_times[1], meter)
	if charge_clock < frame_time:
		return
	charge_clock -= frame_time
	charge_step = (charge_step + 1) % _sheet().charge.size()
	_show_pose(_sheet().charge[charge_step])


func _start_uppercut() -> void:
	charge_ended.emit(true)
	if supercharged:
		_flash(player.sprite, super_launch_flash)
	_set_phase(Phase.UPPERCUT)
	uppercut_step = -1
	_advance_uppercut()


func _advance_uppercut() -> void:
	var steps: Array = _sheet().uppercut
	var starts := FinisherArtLayout.uppercut_step_starts()
	while uppercut_step + 1 < steps.size() and phase_time + STEP_TOLERANCE >= starts[uppercut_step + 1]:
		uppercut_step += 1
		_show_pose(steps[uppercut_step])
		if uppercut_step == _sheet().contact_step:
			_contact()
	if phase_time + STEP_TOLERANCE >= starts[-1]:
		_land()


# The fight starts again at contact, before any damage, so a killing blow goes through the boss's own
# defeat and FightOutro as a punch would, and the outro never meets a frozen scene.
func _contact() -> void:
	var landed := _boss_valid() and _in_reach()
	var box := _hurtbox_rect() if landed else Rect2()
	var super_applied := false
	FightFreeze.unfreeze(get_tree())
	_clear_stars()
	if landed:
		var max_health: int = boss.get_max_health()
		var normal := maxi(1, roundi(max_health * finisher_damage_ratio))
		var dealt: int = boss.take_finisher(maxi(1, roundi(max_health * supercharged_damage_ratio)) if supercharged else normal)
		# A phase floor or a nearly dead boss can clip it: hype is only spent for damage it added.
		super_applied = supercharged and dealt > normal
		if super_applied:
			player.hype.spend()
		boss.exit_daze(true)
		var stagger: float = super_stagger_time if super_applied else stagger_time
		# A killing blow leaves him where he stands: his defeat and the outro play from that spot.
		if boss.get_health_ratio() > 0.0:
			var rocked := _knock_back(super_uppercut_knockback if super_applied else uppercut_knockback, stagger)
			# A boss rocking back on his sprite is already reeling; a hop on the same offset would fight it.
			if boss.end_recovery(stagger) and not rocked:
				_hop(boss.sprite)
		_spawn_impact(box, super_applied)
		if super_applied:
			# On the contact frame with the freeze, the shake and the burst, so the hit is one event.
			# Audio runs on its own clock, so the hit-stop neither chops it nor bends its pitch.
			super_sfx_player.play()
			_super_contact_extras(box)
		HitStop.freeze(get_tree(), super_impact_hit_stop if super_applied else impact_hit_stop)
		ScreenView.shake(get_tree(), super_impact_shake if super_applied else impact_shake, super_impact_shake_steps if super_applied else IMPACT_SHAKE_STEPS, IMPACT_SHAKE_STEP_TIME)
		_flash(boss.sprite, super_impact_flash if super_applied else impact_flash)
		get_tree().call_group("arena_crowd", "cheer", super_impact_cheer if super_applied else impact_cheer)
	elif _boss_valid():
		# A whiff: the punish window carries on with the time it had left.
		boss.exit_daze(false)
	if super_applied:
		# The punch owns the view from here: it snaps in, holds, then eases out over the freeze.
		_super_zoom_punch()
	else:
		ScreenView.zoom_to(get_tree(), 1.0, ScreenView.focus, zoom_out_time)


# The shove away from the player. A boss who can take it moves for real, clamped to his own ground;
# the rest rock back on their sprite and settle through the stagger, so nothing anchored to their
# position moves with them. Returns true when the sprite is what moved.
func _knock_back(distance: float, settle_time: float) -> bool:
	if distance <= 0.0 or not _boss_valid():
		return false
	var push := (_hurtbox_rect().get_center() - player.global_position).normalized()
	if push == Vector2.ZERO:
		push = Vector2.UP
	if boss.has_method("knock_back"):
		boss.knock_back(push * distance, uppercut_knockback_time)
		return false
	var sprite: Sprite2D = boss.sprite
	var rest := sprite.offset
	# The offset is in the sheet's texels, so the px shove is divided by what the sprite is drawn at.
	var slide: Vector2 = rest + push * distance / sprite.global_scale
	var recoil := sprite.create_tween()
	recoil.tween_property(sprite, "offset", slide, uppercut_knockback_time).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	recoil.tween_property(sprite, "offset", rest, maxf(settle_time - uppercut_knockback_time, 0.1)).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	return true


# The supercharged extras: a shock ring rolling out along the floor and speed lines across the
# screen. Both ignore hit-stop, so they play out during the longer freeze.
func _super_contact_extras(box: Rect2) -> void:
	var point := box.get_center() if box.has_area() else player.global_position
	# The ring rolls out along the floor, so it starts at the boss's feet rather than his chest.
	_spawn_shock_ring(Vector2(point.x, box.end.y) if box.has_area() else point)
	_spawn_speedlines(point)


# Snapped in on the contact frame and eased back out, in real time so it reads through the hit-stop.
func _super_zoom_punch() -> void:
	ScreenView.zoom_to(get_tree(), ScreenView.zoom * super_impact_zoom, ScreenView.focus, super_impact_zoom_in_time, true)
	var settle := get_tree().create_timer(super_impact_zoom_in_time + super_impact_zoom_hold, true, false, true)
	# A method rather than a closure: the timer outlives a scene change, the connection doesn't.
	settle.timeout.connect(_ease_out_super_zoom)


func _ease_out_super_zoom() -> void:
	if not player.fight_over:
		ScreenView.zoom_to(get_tree(), 1.0, ScreenView.focus, super_impact_zoom_out_time, true)


func _spawn_shock_ring(point: Vector2) -> void:
	var spec := FinisherArtLayout.super_shock_ring()
	if spec.has("texture"):
		var sheet := _make_sheet(spec, spec.scale)
		_ground_layer().add_child(sheet)
		sheet.global_position = point.round()
		_play_sheet(sheet, spec)
		return
	var ring := Line2D.new()
	ring.width = spec.width
	ring.default_color = spec.color
	ring.closed = true
	var points := PackedVector2Array()
	for i in spec.points:
		points.append(Vector2.from_angle(TAU * i / spec.points))
	ring.points = points
	ring.scale = Vector2.ONE * spec.radius
	fx_layer.add_child(ring)
	ring.global_position = point
	var grow := ring.create_tween().set_parallel().set_ignore_time_scale(true)
	grow.tween_property(ring, "scale", Vector2.ONE * spec.to_radius, spec.time).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	grow.tween_property(ring, "modulate:a", 0.0, spec.time)
	grow.chain().tween_callback(ring.queue_free)


func _spawn_speedlines(point: Vector2) -> void:
	var spec := FinisherArtLayout.super_speedlines()
	if spec.has("texture"):
		var screen_point: Vector2 = get_viewport().get_canvas_transform() * point
		var middle := get_viewport().get_visible_rect().size / 2.0
		var lines_scale: float = spec.off_centre_scale if screen_point.distance_to(middle) > spec.off_centre else spec.scale
		var sheet := _make_sheet(spec, lines_scale)
		var hud: CanvasLayer = player.get_parent().get_node("CanvasLayer")
		hud.add_child(sheet)
		# First on the HUD layer: over the arena, under every readout.
		hud.move_child(sheet, 0)
		sheet.position = screen_point.round()
		_play_sheet(sheet, spec)
		return
	var lines := Node2D.new()
	fx_layer.add_child(lines)
	lines.global_position = point
	for i in spec.rays:
		var ray := Polygon2D.new()
		var out := Vector2.from_angle(TAU * i / spec.rays)
		var side: Vector2 = out.orthogonal() * spec.width / 2.0
		ray.polygon = PackedVector2Array([out * spec.inner_radius + side, out * spec.length, out * spec.inner_radius - side])
		ray.color = spec.color
		lines.add_child(ray)
	var fade := lines.create_tween().set_ignore_time_scale(true)
	fade.tween_property(lines, "modulate:a", 0.0, spec.time)
	fade.tween_callback(lines.queue_free)


func _make_sheet(spec: Dictionary, sheet_scale: float) -> Sprite2D:
	var sheet := Sprite2D.new()
	sheet.texture = load(spec.texture)
	sheet.hframes = spec.hframes
	sheet.centered = false
	sheet.offset = -spec.pivot
	sheet.scale = Vector2.ONE * sheet_scale
	return sheet


func _play_sheet(sheet: Sprite2D, spec: Dictionary) -> void:
	var frames := sheet.create_tween().set_ignore_time_scale(true)
	for i in spec.frame_times.size():
		frames.tween_callback(sheet.set_frame.bind(i))
		frames.tween_interval(spec.frame_times[i])
	frames.tween_callback(sheet.queue_free)


# A layer in the arena drawn before the player and the boss, for effects that belong on the floor.
func _ground_layer() -> Node2D:
	var stage: Node2D = player.get_parent()
	var arena: Node = stage.get_parent()
	var layer: Node2D = arena.get_node_or_null("GroundFx")
	if layer == null:
		layer = Node2D.new()
		layer.name = "GroundFx"
		arena.add_child(layer)
		arena.move_child(layer, stage.get_index())
	return layer


func _land() -> void:
	player.end_finisher(true)
	_lock_input()
	_finish()


func _start_fizzle() -> void:
	charge_ended.emit(false)
	_show_pose(_sheet().ready)
	if zoomed:
		ScreenView.zoom_to(get_tree(), 1.0, ScreenView.focus, zoom_out_time)
	_set_phase(Phase.FIZZLE)


func _end_fizzle() -> void:
	FightFreeze.unfreeze(get_tree())
	_clear_stars()
	boss.exit_daze(false)
	player.end_finisher(true)
	_lock_input()
	_finish()


func _abort() -> void:
	FightFreeze.unfreeze(get_tree())
	ScreenView.reset(get_tree())
	_clear_stars()
	if dazed and _boss_valid():
		boss.exit_daze(false)
	player.end_finisher(false)
	_finish()


func _finish() -> void:
	phase = Phase.OFF
	boss = null
	auto = false
	dazed = false
	supercharged = false
	prompt_visible = false
	zoomed = false
	finished.emit()


func _lock_input() -> void:
	input_lock_left = post_input_lock


func _boss_valid() -> bool:
	return is_instance_valid(boss) and boss.is_inside_tree() and not boss.is_queued_for_deletion()


func _sheet() -> Dictionary:
	return FinisherArtLayout.player_sheet()


func _show_pose(pose: Array) -> void:
	player.state_machine.states["Finishing"].show_frame(pose[0], pose[1], flipped)


func _hurtbox_rect() -> Rect2:
	var shape: CollisionShape2D = boss.get_finisher_hurtbox().get_node("CollisionShape2D")
	return shape.global_transform * shape.shape.get_rect()


func _boss_on_left() -> bool:
	var dx := _hurtbox_rect().get_center().x - player.global_position.x
	if absf(dx) < SIDE_DEAD_ZONE:
		return player.facing == player.Facing.LEFT
	return dx < 0.0


func _fist_point(step: int) -> Vector2:
	return player.global_position + FinisherArtLayout.mirrored(_sheet().fists[step], flipped)


func _in_reach() -> bool:
	var reach := _hurtbox_rect().grow(uppercut_reach)
	if reach.has_point(player.global_position):
		return true
	for step in _sheet().reach_steps:
		if reach.has_point(_fist_point(step)):
			return true
	return false


func _spawn_stars(anchor: Vector2) -> void:
	var spec := FinisherArtLayout.stars()
	stars = Sprite2D.new()
	stars.texture = load(spec.texture)
	stars.hframes = spec.hframes
	stars.centered = false
	stars.offset = -spec.pivot
	stars.scale = Vector2.ONE * spec.scale
	fx_layer.add_child(stars)
	stars.global_position = anchor.round()
	stars_clock = 0.0


func _animate_stars(delta: float) -> void:
	if not is_instance_valid(stars):
		return
	stars_clock += delta
	stars.frame = int(stars_clock / FinisherArtLayout.stars().frame_time) % stars.hframes


func _clear_stars() -> void:
	if is_instance_valid(stars):
		stars.queue_free()
	stars = null


func _spawn_impact(box: Rect2, super_burst: bool) -> void:
	var point := _fist_point(_sheet().contact_step) + FinisherArtLayout.mirrored(FinisherArtLayout.IMPACT_OFFSET, flipped)
	point = point.clamp(box.position, box.end).round()
	var spec := FinisherArtLayout.super_impact() if super_burst else FinisherArtLayout.impact()
	if spec.has("texture"):
		var burst := Sprite2D.new()
		burst.texture = load(spec.texture)
		burst.hframes = spec.hframes
		burst.centered = false
		burst.offset = -spec.pivot
		burst.scale = Vector2.ONE * spec.scale
		# The placeholder supercharged burst is the normal one, tinted.
		burst.self_modulate = spec.get("tint", Color.WHITE)
		fx_layer.add_child(burst)
		burst.global_position = point
		var frames := burst.create_tween()
		for i in spec.frame_times.size():
			frames.tween_callback(burst.set_frame.bind(i))
			frames.tween_interval(spec.frame_times[i])
		frames.tween_callback(burst.queue_free)
		return
	var spark := Polygon2D.new()
	var polygon := PackedVector2Array()
	var corners: int = spec.points * 2
	for i in corners:
		var radius: float = spec.outer_radius if i % 2 == 0 else spec.inner_radius
		polygon.append(Vector2.from_angle(TAU * i / corners - PI / 2.0) * radius)
	spark.polygon = polygon
	spark.color = spec.color * spec.get("tint", Color.WHITE)
	spark.scale = Vector2.ONE * spec.from_scale
	fx_layer.add_child(spark)
	spark.global_position = point
	var grow := spark.create_tween().set_parallel()
	grow.tween_property(spark, "scale", Vector2.ONE * spec.to_scale, spec.time)
	grow.tween_property(spark, "modulate:a", 0.0, spec.time)
	grow.chain().tween_callback(spark.queue_free)


func _flash(sprite: CanvasItem, color: Color) -> void:
	sprite.self_modulate = color
	get_tree().create_tween().tween_property(sprite, "self_modulate", Color(1, 1, 1), impact_flash_time)


# The offset rather than the position: hit shakes, frame_point() and y-sorting all use the position.
func _hop(sprite: Sprite2D) -> void:
	var base_y := sprite.offset.y
	var lift := func(texels: float) -> void:
		sprite.offset.y = base_y - roundi(texels)
	var hop := sprite.create_tween()
	hop.tween_method(lift, 0.0, float(stagger_hop_texels), HOP_UP_TIME).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	hop.tween_method(lift, float(stagger_hop_texels), 0.0, HOP_DOWN_TIME).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	hop.tween_method(lift, 0.0, float(HOP_BOUNCE_TEXELS), HOP_BOUNCE_TIME).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	hop.tween_method(lift, float(HOP_BOUNCE_TEXELS), 0.0, HOP_BOUNCE_TIME).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
