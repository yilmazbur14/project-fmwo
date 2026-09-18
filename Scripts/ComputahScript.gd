extends CharacterBody2D

# Computah, the right half of boss 2. He fires the twin laser sweep, and he is the one who moves: he
# runs the player down, pounces at them, and hands whoever he catches to Greyson. His battery is the
# chase clock, and running it flat is what opens his punish window.
# He is one of TWO bodies under one fight-wide machine (Scripts/States/GreysonComputah). This node is
# his body, his health, his art and his half of the boss interface; GreysonComputahScript is the
# coordinator that owns the HUD, the surge and the end of the fight.
# HE JOINS FightOutro.BOSS_GROUP LIKE GREYSON DOES. PlayerHype.is_inert() scans that group for a node
# with can_be_dazed() and, finding none, silently makes hype inert and hides the meter with no error.
#
# THE CHARGE STATE IS A FRAME OFFSET, NOT A TINT. computah_idle and computah_run each hold the same
# four-frame cycle three times over, so `frame = charge_state * 4 + cycle_frame` changes how many
# chest cells are lit, what colour they are and how the antenna ball glows, all at once. That
# three-way read is what makes the battery legible at a glance; a colour swap would keep four lit
# cells and lose the count.

# A non-looping animation reached the end of its last frame.
signal anim_finished(anim_name: StringName)

const HitStop := preload("res://Scripts/HitStop.gd")
const FightOutro := preload("res://Scripts/FightOutro.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const Layout := preload("res://Scripts/GreysonComputahArtLayout.gd")

@export var max_health := 10
var boss_health := max_health
const MAX_HITS_PER_WINDOW := 3
const PHANTOM_HIT_WINDOW := 0.5
const BRINK_TINT := Color(0.55, 0.5, 0.6)

# The coordinator; the state machine hangs off it.
@export var fight: Node2D

@onready var sprite: Sprite2D = $Sprite2D
@onready var aura: Node2D = $Aura
@onready var battery: Node2D = $Battery
@onready var hurtbox: Area2D = $Hurtbox
@onready var hurtbox_shape: CollisionShape2D = $Hurtbox/CollisionShape2D
@onready var collision_shape: CollisionShape2D = $CollisionShape2D
@onready var grab_area: Area2D = $GrabArea
@onready var grab_shape: CollisionShape2D = $GrabArea/CollisionShape2D

var defeated := false
var hits_this_window := 0
# How many punches this window takes; his battery windows allow MAX_HITS_PER_WINDOW.
var window_cap := MAX_HITS_PER_WINDOW
var daze_used := false
var on_brink := false

var fight_clock := 0.0
var last_contact_hit_time := -INF

var facing_left := false
var sprite_base_position: Vector2
var aura_clock := 0.0

# 0 full, 1 half, 2 low: the row of computah_idle and computah_run his frames are taken from.
var charge_state := 0
var battery_shell: Polygon2D
var battery_fill: Polygon2D
var battery_flashing := false
var battery_clock := 0.0

var current_anim := &""
var anim: Dictionary = {}
var anim_step := 0
var anim_clock := 0.0
var anim_next := &""
var anim_done := false


func _ready() -> void:
	add_to_group(FightOutro.BOSS_GROUP)
	hurtbox.area_entered.connect(_on_hurtbox_entered)
	boss_health = max_health

	sprite_base_position = sprite.position
	sprite.scale = Vector2.ONE * Layout.SCALE
	sprite.offset = Layout.computah_offset()
	set_down_box(false)
	_build_aura()
	_build_battery()
	play_anim(&"idle")


func get_health_ratio() -> float:
	return float(boss_health) / float(max_health)


func get_max_health() -> int:
	return max_health


func _physics_process(delta: float) -> void:
	fight_clock += delta


# His standing chassis, or the collapsed pose the battery window opens on.
func set_down_box(down: bool) -> void:
	var local := Layout.computah_rect(Layout.C_DOWN_BODY_BOX if down else Layout.C_BODY_BOX)
	hurtbox_shape.position = local.get_center()
	(hurtbox_shape.shape as RectangleShape2D).size = local.size


func _build_aura() -> void:
	var spec := Layout.PLACEHOLDER_AURA
	var glow := Polygon2D.new()
	glow.polygon = Layout.ellipse(Layout.AURA_COMPUTAH.radii, spec.points)
	glow.color = spec.color
	glow.position = Layout.AURA_COMPUTAH.centre
	glow.material = Layout.additive()
	aura.add_child(glow)
	aura.modulate.a = Layout.AURA_ALPHA
	aura.hide()


#ANIMATION

func play_anim(anim_name: StringName, next_anim: StringName = &"") -> void:
	current_anim = anim_name
	anim = Layout.computah_anim(anim_name)
	anim_next = next_anim
	anim_step = 0
	anim_clock = 0.0
	anim_done = false
	var sheet: Texture2D = load(anim.sheet)
	sprite.frame = 0
	sprite.texture = sheet
	sprite.hframes = roundi(sheet.get_width() / Layout.C_FRAME.x)
	sprite.vframes = 1
	_show_anim_frame()


func _process(delta: float) -> void:
	if aura.visible:
		aura_clock += delta
		var spec := Layout.PLACEHOLDER_AURA
		var pulse: Array = spec.pulse
		aura.scale = Vector2.ONE * lerpf(pulse[0], pulse[1], absf(sin(aura_clock * PI / spec.pulse_time)))
	if battery.visible and battery_flashing:
		battery_clock += delta
		battery.visible = int(battery_clock / Layout.BATTERY_GAUGE.flash_interval) % 2 == 0
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
			var finished := current_anim
			if anim_next != &"":
				play_anim(anim_next)
			anim_finished.emit(finished)
			return
		_show_anim_frame()


func _frame_time() -> float:
	var times: Array = anim.times
	return times[mini(anim_step, times.size() - 1)]


func _show_anim_frame() -> void:
	var frame: int = anim.frames[anim_step]
	if anim.get("charge_rows", false):
		frame += charge_state * Layout.CHARGE_CYCLE
	sprite.frame = frame
	sprite.flip_h = anim.get("flips", false) and facing_left


# 0 full, 1 half, 2 low. Only the two sheets drawn three times over follow it.
func set_charge_state(state: int) -> void:
	state = clampi(state, 0, 2)
	if charge_state == state:
		return
	charge_state = state
	if not anim.is_empty():
		_show_anim_frame()


func set_facing(left: bool) -> void:
	if facing_left == left:
		return
	facing_left = left
	_show_anim_frame()


func face_toward(point: Vector2) -> void:
	set_facing(point.x < global_position.x)


#THE BATTERY GAUGE
# The chase clock is the battery; his own frames carry the coarse three-way read and this is the
# precise one.

func _build_battery() -> void:
	var spec := Layout.BATTERY_GAUGE
	var size: Vector2 = spec.size
	battery.position = Layout.C_BATTERY_OFFSET
	battery_shell = Polygon2D.new()
	battery_shell.polygon = Layout.centred_rect(size)
	battery_shell.color = spec.shell
	battery.add_child(battery_shell)
	var rim := Line2D.new()
	rim.points = battery_shell.polygon
	rim.closed = true
	rim.width = spec.border
	rim.default_color = spec.edge
	battery.add_child(rim)
	battery_fill = Polygon2D.new()
	battery_fill.polygon = Layout.centred_rect(size - Vector2(spec.border, spec.border) * 2.0)
	battery_fill.color = spec.fills[0]
	battery.add_child(battery_fill)
	battery.hide()


func show_battery(on: bool) -> void:
	battery_flashing = false
	battery_clock = 0.0
	battery.visible = on
	if on:
		set_battery(1.0, false)


# `left` runs 1 to 0 over the chase; the gauge drains, recolours with the charge state and flashes
# over the last seconds.
func set_battery(left: float, flashing: bool) -> void:
	if not battery_fill:
		return
	var spec := Layout.BATTERY_GAUGE
	var inner: Vector2 = Vector2(spec.size) - Vector2(spec.border, spec.border) * 2.0
	var width := inner.x * clampf(left, 0.0, 1.0)
	battery_fill.polygon = PackedVector2Array([
		Vector2(-inner.x / 2.0, -inner.y / 2.0), Vector2(-inner.x / 2.0 + width, -inner.y / 2.0),
		Vector2(-inner.x / 2.0 + width, inner.y / 2.0), Vector2(-inner.x / 2.0, inner.y / 2.0),
	])
	battery_fill.color = spec.fills[charge_state]
	if flashing != battery_flashing:
		battery_flashing = flashing
		battery_clock = 0.0
		if not flashing:
			battery.visible = true


#EFFECTS

func shake_screen(strength: float, steps: int, step_time: float) -> void:
	ScreenView.shake(get_tree(), strength, steps, step_time)


func shake_sprite(strength: float, steps: int, step_time: float) -> void:
	var tween := sprite.create_tween()
	for i in steps:
		var offset := Vector2(randf_range(-strength, strength), randf_range(-strength, strength)).round()
		tween.tween_callback(func() -> void: sprite.position = sprite_base_position + offset)
		tween.tween_interval(step_time)
	tween.tween_callback(func() -> void: sprite.position = sprite_base_position)


func show_aura(on: bool) -> void:
	aura_clock = 0.0
	aura.visible = on


func flare_aura() -> void:
	if not aura.visible:
		return
	var flare := aura.create_tween()
	flare.tween_property(aura, "modulate:a", minf(Layout.AURA_ALPHA * 2.4, 1.0), 0.12)
	flare.tween_property(aura, "modulate:a", Layout.AURA_ALPHA, 0.35)


#WHERE THINGS STAND ON HIM

func get_daze_anchor() -> Vector2:
	return global_position + Layout.C_DAZE_ANCHOR


func tell_anchor() -> Vector2:
	return global_position + Layout.C_TELL_ANCHOR


func beam_origin() -> Vector2:
	return global_position + Layout.C_BEAM_ORIGIN


#MOVEMENT
# He writes his own position while he chases, with his collision shape off, so he neither shoves the
# player nor sticks to them. Eric's lunge does the same.

func set_solid(solid: bool) -> void:
	collision_shape.set_deferred("disabled", not solid)


func set_grab_active(active: bool) -> void:
	grab_area.set_deferred("monitoring", active)


#COMBAT

func set_hurtbox_active(active: bool) -> void:
	hurtbox.set_deferred("monitoring", active)
	hurtbox.set_deferred("monitorable", active)


# He is not punchable while he chases, so the player can line up on Greyson instead. The old boss
# script did the same when the mech formed.
func set_target_active(on: bool) -> void:
	if on and not hurtbox.is_in_group("boss_target"):
		hurtbox.add_to_group("boss_target")
	elif not on and hurtbox.is_in_group("boss_target"):
		hurtbox.remove_from_group("boss_target")


func _on_hurtbox_entered(area: Area2D) -> void:
	if boss_health <= 0 or not area.is_in_group("player attack"):
		return
	if not area.monitorable and fight_clock - last_contact_hit_time < PHANTOM_HIT_WINDOW:
		return
	if area.get_parent().combo.resolve_punch(self) > 0 and area.monitorable:
		last_contact_hit_time = fight_clock


func is_open() -> bool:
	return fight != null and fight.is_open_to(self)


# Called as a window opens, before the hurtbox does.
func begin_window(cap := MAX_HITS_PER_WINDOW) -> void:
	hits_this_window = 0
	window_cap = cap
	daze_used = false


func take_punch(amount: int) -> int:
	if hits_this_window >= window_cap or not is_open():
		return 0
	var dealt := _apply_damage(amount)
	if dealt > 0:
		hits_this_window += 1
	return dealt


func take_finisher(amount: int) -> int:
	if not is_open():
		return 0
	return _apply_damage(amount)


# The near-death clamp: he cannot be killed while Greyson is still healthy.
func _lowest_health() -> int:
	return 1 if fight != null and fight.clamps(self) else 0


func _apply_damage(amount: int) -> int:
	var dealt := mini(amount, boss_health - _lowest_health())
	if dealt <= 0:
		return 0

	boss_health -= dealt
	_hit_feedback()
	if fight:
		fight.on_body_damaged(self)

	if boss_health > 0:
		if fight:
			fight.flinch(self)
	else:
		call_deferred("_on_killed")
	return dealt


func flinch() -> void:
	play_anim(&"hit", &"down")


func _on_killed() -> void:
	defeated = true
	set_hurtbox_active(false)
	show_battery(false)
	if fight:
		fight.on_body_killed(self)


func can_be_dazed() -> bool:
	return not defeated and boss_health > _lowest_health() and not daze_used and is_open()


func enter_daze() -> void:
	daze_used = true


func exit_daze(_finisher_landed: bool) -> void:
	pass


func end_recovery(stagger_time: float) -> bool:
	if defeated or boss_health <= 0 or not is_open():
		return false
	return fight.end_window(self, stagger_time)


func get_finisher_hurtbox() -> Area2D:
	return hurtbox


# Only the pounce can be parried, and only the chase knows whether one is in the air.
func can_parry_stagger(hit: RefCounted) -> bool:
	if defeated or boss_health <= 0:
		return false
	return fight != null and fight.can_parry_stagger(self, hit)


func parry_stagger(duration: float) -> void:
	if defeated or boss_health <= 0:
		return
	if fight:
		fight.parry_stagger(self, duration)


#THE BRINK

func refresh_brink() -> bool:
	var clamped: bool = boss_health <= 1 and fight != null and fight.clamps(self)
	if clamped == on_brink:
		return false
	on_brink = clamped
	sprite.modulate = BRINK_TINT if on_brink else Color(1, 1, 1)
	return on_brink


func _hit_feedback() -> void:
	sprite.modulate = Color(3, 3, 3)
	var flash := create_tween()
	flash.tween_property(sprite, "modulate", BRINK_TINT if on_brink else Color(1, 1, 1), 0.15)
	shake_sprite(5.0, 4, 0.025)
	HitStop.freeze(get_tree(), 0.06)


func on_player_defeated() -> void:
	pass
