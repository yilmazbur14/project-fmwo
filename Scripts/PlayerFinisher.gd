extends Node

# The finisher. A charged combo punch that lands in a boss's punish window dazes the boss and stops
# the fight around the player. Alternating punch and dodge fills a meter while the camera closes in,
# and a full meter fires a rising uppercut that takes a chunk of the boss's health and ends the window.
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
# px the boss's hurtbox grows by for the reach check.
@export var uppercut_reach := 48.0
@export var impact_hit_stop := 0.15
@export var impact_shake := 16.0
@export var impact_cheer := 2.0
# Stacks on the boss's own hit flash, which tweens modulate.
@export var impact_flash := Color(4, 3.2, 1.2)
@export var impact_flash_time := 0.45
# A boss the finisher lands on idles this long, hopping, then attacks again.
@export var stagger_time := 0.6
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


func _ready() -> void:
	player.get_node("Combo").charged_hit_landed.connect(_on_charged_hit_landed)


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
			if not prompt_visible and daze_time >= prompt_delay:
				prompt_visible = true
				prompt_shown.emit()
			if daze_time >= prompt_delay + charge_time_limit:
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
	FightFreeze.unfreeze(get_tree())
	_clear_stars()
	if landed:
		boss.take_finisher(maxi(1, roundi(boss.get_max_health() * finisher_damage_ratio)))
		boss.exit_daze(true)
		if boss.get_health_ratio() > 0.0 and boss.end_recovery(stagger_time):
			_hop(boss.sprite)
		_spawn_impact(box)
		HitStop.freeze(get_tree(), impact_hit_stop)
		ScreenView.shake(get_tree(), impact_shake, IMPACT_SHAKE_STEPS, IMPACT_SHAKE_STEP_TIME)
		_flash(boss.sprite)
		get_tree().call_group("arena_crowd", "cheer", impact_cheer)
	elif _boss_valid():
		# A whiff: the punish window carries on with the time it had left.
		boss.exit_daze(false)
	ScreenView.zoom_to(get_tree(), 1.0, ScreenView.focus, zoom_out_time)


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
	dazed = false
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


func _spawn_impact(box: Rect2) -> void:
	var point := _fist_point(_sheet().contact_step) + FinisherArtLayout.mirrored(FinisherArtLayout.IMPACT_OFFSET, flipped)
	point = point.clamp(box.position, box.end).round()
	var spec := FinisherArtLayout.impact()
	if FinisherArtLayout.USE_FINAL_IMPACT:
		var burst := Sprite2D.new()
		burst.texture = load(spec.texture)
		burst.hframes = spec.hframes
		burst.centered = false
		burst.offset = -spec.pivot
		burst.scale = Vector2.ONE * spec.scale
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
	spark.color = spec.color
	spark.scale = Vector2.ONE * spec.from_scale
	fx_layer.add_child(spark)
	spark.global_position = point
	var grow := spark.create_tween().set_parallel()
	grow.tween_property(spark, "scale", Vector2.ONE * spec.to_scale, spec.time)
	grow.tween_property(spark, "modulate:a", 0.0, spec.time)
	grow.chain().tween_callback(spark.queue_free)


func _flash(sprite: CanvasItem) -> void:
	sprite.self_modulate = impact_flash
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
