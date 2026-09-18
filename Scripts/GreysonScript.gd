extends CharacterBody2D

# Greyson, the left half of boss 2. He never moves: he taunts while Computah works, throws junk over
# the chase, cranks Computah's battery in his own punish window, and catches a player Computah has
# grabbed to put five punches through them.
# He is one of TWO bodies under one fight-wide machine (Scripts/States/GreysonComputah). This node is
# his body, his health, his art and his half of the boss interface; GreysonComputahScript is the
# coordinator that owns the HUD, the surge and the end of the fight.
# HE JOINS FightOutro.BOSS_GROUP LIKE COMPUTAH DOES. PlayerHype.is_inert() scans that group for a node
# with can_be_dazed() and, finding none, silently makes hype inert and hides the meter with no error.

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
# What a body on the brink is dimmed to, so an unkillable body never looks like a bug.
const BRINK_TINT := Color(0.55, 0.5, 0.6)

# The coordinator; the state machine hangs off it.
@export var fight: Node2D

@onready var sprite: Sprite2D = $Sprite2D
@onready var aura: Node2D = $Aura
@onready var hurtbox: Area2D = $Hurtbox
@onready var hurtbox_shape: CollisionShape2D = $Hurtbox/CollisionShape2D

var defeated := false
var hits_this_window := 0
# How many punches this window takes. His punish windows allow MAX_HITS_PER_WINDOW; the moment he is
# open after a junk throw allows fewer, since it comes around far more often.
var window_cap := MAX_HITS_PER_WINDOW
# One finisher daze per window; the window clears it.
var daze_used := false
# Clamped at 1 HP while Computah is still healthy (GreysonComputahScript.SWAP_GUARD_RATIO).
var on_brink := false

var fight_clock := 0.0
var last_contact_hit_time := -INF

var facing_left := false
var sprite_base_position: Vector2
var aura_shape: Polygon2D
var aura_clock := 0.0

var current_anim := &""
var anim: Dictionary = {}
var anim_step := 0
var anim_clock := 0.0
var anim_next := &""
var anim_done := false


func _ready() -> void:
	add_to_group(FightOutro.BOSS_GROUP)
	hurtbox.area_entered.connect(_on_hurtbox_entered)
	# The exported value is only set after the variable above was initialised.
	boss_health = max_health

	sprite_base_position = sprite.position
	sprite.scale = Vector2.ONE * Layout.SCALE
	sprite.offset = Layout.greyson_offset()
	_apply_hurtbox_box(Layout.G_BODY_BOX)
	_build_aura()
	play_anim(&"idle")


func get_health_ratio() -> float:
	return float(boss_health) / float(max_health)


func get_max_health() -> int:
	return max_health


func _physics_process(delta: float) -> void:
	fight_clock += delta


func _apply_hurtbox_box(box: Rect2) -> void:
	var local := Layout.greyson_rect(box)
	hurtbox_shape.position = local.get_center()
	(hurtbox_shape.shape as RectangleShape2D).size = local.size


# Behind his sprite and on its own node rather than a child of it: boss.sprite has to stay the body
# sprite, which PlayerFinisher._flash and PlayerCombo._charged_feedback both write to.
func _build_aura() -> void:
	var spec := Layout.PLACEHOLDER_AURA
	var glow := Polygon2D.new()
	glow.polygon = Layout.ellipse(Layout.AURA_GREYSON.radii, spec.points)
	glow.color = spec.color
	glow.position = Layout.AURA_GREYSON.centre
	glow.material = Layout.additive()
	aura.add_child(glow)
	aura_shape = glow
	aura.modulate.a = Layout.AURA_ALPHA
	aura.hide()


#ANIMATION

# A non-looping animation holds its last frame when it ends, unless `next_anim` follows it.
func play_anim(anim_name: StringName, next_anim: StringName = &"") -> void:
	current_anim = anim_name
	anim = Layout.greyson_anim(anim_name)
	anim_next = next_anim
	anim_step = 0
	anim_clock = 0.0
	anim_done = false
	var sheet: Texture2D = load(anim.sheet)
	# Back to the first frame before the frame count changes, so the current one can't be out of range.
	sprite.frame = 0
	sprite.texture = sheet
	sprite.hframes = roundi(sheet.get_width() / Layout.G_FRAME.x)
	sprite.vframes = 1
	_show_anim_frame()


func _process(delta: float) -> void:
	if aura.visible:
		aura_clock += delta
		var spec := Layout.PLACEHOLDER_AURA
		var pulse: Array = spec.pulse
		aura.scale = Vector2.ONE * lerpf(pulse[0], pulse[1], absf(sin(aura_clock * PI / spec.pulse_time)))
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
	sprite.frame = anim.frames[anim_step]
	# The mirror axis is the anchor's column, so flipping keeps his boots in place.
	sprite.flip_h = anim.get("flips", false) and facing_left


# Which way his poses face. Only the ones drawn to mirror follow it.
func set_facing(left: bool) -> void:
	if facing_left == left:
		return
	facing_left = left
	_show_anim_frame()


func face_toward(point: Vector2) -> void:
	set_facing(point.x < global_position.x)


#EFFECTS

func shake_screen(strength: float, steps: int, step_time: float) -> void:
	ScreenView.shake(get_tree(), strength, steps, step_time)


# Shudders the drawn body in whole pixels; his hurtbox stays put.
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


# The other body was clamped on the brink: his overcharge flares for a beat.
func flare_aura() -> void:
	if not aura.visible:
		return
	var flare := aura.create_tween()
	flare.tween_property(aura, "modulate:a", minf(Layout.AURA_ALPHA * 2.4, 1.0), 0.12)
	flare.tween_property(aura, "modulate:a", Layout.AURA_ALPHA, 0.35)


#WHERE THINGS STAND ON HIM

func get_daze_anchor() -> Vector2:
	return global_position + Layout.G_DAZE_ANCHOR


func tell_anchor() -> Vector2:
	return global_position + Layout.G_TELL_ANCHOR


func beam_origin() -> Vector2:
	return global_position + Layout.G_BEAM_ORIGIN


func hand_point() -> Vector2:
	return global_position + Layout.greyson_local(Layout.G_HAND_THROW, facing_left)


# Where the held player stands through the five-hit combo: just past the reach of his lead fist, on
# the side he is facing.
func combo_spot() -> Vector2:
	var spot: Vector2 = Layout.COMBO_SPOT
	return global_position + Vector2(-spot.x if facing_left else spot.x, spot.y)


# The knuckles of the hand throwing combo hit `index`, so a burst lands where the punch does.
func combo_fist(index: int) -> Vector2:
	return global_position + Layout.combo_fist(index, facing_left)


#COMBAT

# Punches only reach him while a window of his is open. The hurtbox keeps its groups the whole fight,
# so the player still faces him while Computah works.
func set_hurtbox_active(active: bool) -> void:
	# Deferred: monitoring can't change inside a physics flush.
	hurtbox.set_deferred("monitoring", active)
	hurtbox.set_deferred("monitorable", active)


# A dead body is nothing to turn to any more, so the player faces whoever is left.
func set_target_active(on: bool) -> void:
	if on and not hurtbox.is_in_group("boss_target"):
		hurtbox.add_to_group("boss_target")
	elif not on and hurtbox.is_in_group("boss_target"):
		hurtbox.remove_from_group("boss_target")


func _on_hurtbox_entered(area: Area2D) -> void:
	if boss_health <= 0 or not area.is_in_group("player attack"):
		return
	# The same phantom-hit filter as Josh and Carter: a punch that connects as its hitbox switches on
	# is reported again when PlayerPunching switches the hitbox off, which would eat the hit cap.
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


# Past the hit cap, which the combo that led to it has used up, but not past the clamp.
func take_finisher(amount: int) -> int:
	if not is_open():
		return 0
	return _apply_damage(amount)


# The near-death clamp: he cannot be killed while Computah is still healthy. The killing hit is cut
# down to leave him on 1, and he stays there until Computah drops.
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
		# area_entered fires mid physics flush; deferring keeps the state Exit/Enter code the death
		# beat runs from having to be flush-safe.
		call_deferred("_on_killed")
	return dealt


func flinch() -> void:
	play_anim(&"hit", &"idle")


func _on_killed() -> void:
	defeated = true
	set_hurtbox_active(false)
	if fight:
		fight.on_body_killed(self)


# The player's finisher (PlayerFinisher). Only an open window can be dazed, once per window, and only
# while the finisher could still take health past the clamp.
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


# A parry answers the junk he throws but never staggers him: he is standing still already, and
# Josh's cards set that rule.
func can_parry_stagger(_hit: RefCounted) -> bool:
	return false


func parry_stagger(_duration: float) -> void:
	pass


#THE BRINK

# Called by the coordinator whenever either body's health changes. Returns true the first time he
# goes on the brink, which is the beat the popup and Computah's aura flare belong to.
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


# Called by FightOutro when the player loses; the coordinator stops the fight itself.
func on_player_defeated() -> void:
	pass
