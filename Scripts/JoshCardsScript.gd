extends CharacterBody2D

# A non-looping animation reached the end of its last frame.
signal anim_finished(anim_name: StringName)

const HitStop := preload("res://Scripts/HitStop.gd")
const FightOutro := preload("res://Scripts/FightOutro.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const JoshArtLayout := preload("res://Scripts/JoshArtLayout.gd")
# What he says once the fight is over, under player_won and player_lost.
const OUTRO_DIALOGUE := "res://Dialogue/JoshOutro.dialogue"
const FIGHT_SCENE := "res://Scenes/Bosses/JoshBossFightScene.tscn"

#CONSTANTS
@export var max_health := 14
var boss_health := max_health
const PHASE_TWO_RATIO := 0.5
const MAX_HITS_PER_WINDOW := 3
const PHANTOM_HIT_WINDOW := 0.5
const VIEW_SIZE := Vector2(1920, 1080)
# He eases into and out of every move, the way beast Bixby does: his speed never changes faster than
# FLY_ACCELERATION px/s², and over the last stretch he slows as if FLY_ARRIVE_TIME seconds away.
const FLY_ACCELERATION := 3000.0
const FLY_ARRIVE_TIME := 0.25
# Riding sideways faster than this turns his frames to face the way he's going.
const FLY_TURN_SPEED := 60.0
# Over the ropes while he rides, on the floor while he stands.
const AIR_Z := 3
const GROUND_Z := 0

#UI (built at runtime - no new art needed)
var hud_layer: CanvasLayer
var health_bar: ProgressBar
var name_label: Label
var fill_style: StyleBoxFlat

# Kept under a node that y-sorts at the top edge of the arena floor, so it is drawn under every
# character wherever it goes.
@export var shadow: Node2D
# Hazards sort under the player (FloorLayer) or over the ropes (SkyLayer).
@export var floor_layer: Node2D
@export var sky_layer: Node2D
@onready var air: Node2D = $Air
@onready var glider: Node2D = $Air/Glider
@onready var sprite: Sprite2D = $Air/Sprite2D
@onready var hurtbox: Area2D = $Air/Hurtbox
@onready var state_machine = $StateManager

#AUDIO
@onready var music_player: AudioStreamPlayer = $MusicPlayer
@onready var hit_sfx_player: AudioStreamPlayer = $HitSfxPlayer
@onready var victory_sfx_player: AudioStreamPlayer = $VictorySfxPlayer
@onready var glide_sfx_player: AudioStreamPlayer = $GlideSfxPlayer
@onready var throw_sfx_player: AudioStreamPlayer = $ThrowSfxPlayer
@onready var land_sfx_player: AudioStreamPlayer = $LandSfxPlayer
@onready var recover_sfx_player: AudioStreamPlayer = $RecoverSfxPlayer
@onready var shuffle_sfx_player: AudioStreamPlayer = $ShuffleSfxPlayer
@onready var reveal_sfx_player: AudioStreamPlayer = $RevealSfxPlayer
@onready var card_sfx_player: AudioStreamPlayer = $CardSfxPlayer

var phase_two := false
var defeated := false
var hits_this_window := 0
# One finisher daze per recovery; Recover clears it.
var daze_used := false

var fight_clock := 0.0
var last_contact_hit_time := -INF

var sprite_base_position: Vector2

# The floor point under him, where his shadow is, and how many px above it his feet are. His node sits
# on the floor point, and everything drawn is snapped to whole pixels.
var ground_position := Vector2.ZERO
var height := 0.0
var fly_velocity := Vector2.ZERO
var flying_left := false

var shadow_sprite: Sprite2D
var glider_sprite: Sprite2D
var glider_clock := 0.0

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
	ground_position = global_position
	_apply_art_layout()
	_build_health_bar()
	place()

	# Placeholders: Josh has no theme or sounds of his own yet.
	music_player.stream = load("res://Assets/Audio/Music/boss_theme.ogg")
	if music_player.stream:
		music_player.stream.loop = true
	hit_sfx_player.stream = load("res://Assets/Audio/SFX/hit_impact.ogg")
	victory_sfx_player.stream = load("res://Assets/Audio/SFX/victory_fanfare.ogg")
	glide_sfx_player.stream = load("res://Assets/Audio/SFX/whirlwind_whoosh.ogg")
	throw_sfx_player.stream = load("res://Assets/Audio/SFX/whirlwind_whoosh.ogg")
	land_sfx_player.stream = load("res://Assets/Audio/SFX/wrestler_collision.ogg")
	recover_sfx_player.stream = load("res://Assets/Audio/SFX/downed_stinger.ogg")
	shuffle_sfx_player.stream = load("res://Assets/Audio/SFX/whirlwind_whoosh.ogg")
	reveal_sfx_player.stream = load("res://Assets/Audio/SFX/laser_charge.ogg")
	card_sfx_player.stream = load("res://Assets/Audio/SFX/hit_impact.ogg")


func start_music() -> void:
	if music_player and not music_player.playing:
		music_player.play()


func get_health_ratio() -> float:
	return float(boss_health) / float(max_health)


func _physics_process(delta: float) -> void:
	fight_clock += delta


func _apply_art_layout() -> void:
	_build_shadow()
	_build_glider()
	glider.scale = Vector2.ZERO
	glider.hide()

	var box := JoshArtLayout.local_rect(JoshArtLayout.RECOVER_BODY_BOX)
	var hurtbox_shape: CollisionShape2D = hurtbox.get_node("CollisionShape2D")
	hurtbox_shape.position = box.get_center()
	(hurtbox_shape.shape as RectangleShape2D).size = box.size


func _build_shadow() -> void:
	if JoshArtLayout.USE_FINAL_SHADOW:
		var spec := JoshArtLayout.FINAL_SHADOW
		shadow_sprite = Sprite2D.new()
		shadow_sprite.texture = load(spec.texture)
		shadow_sprite.hframes = spec.hframes
		shadow_sprite.scale = Vector2.ONE * spec.scale
		shadow_sprite.offset = spec.frame_size / 2.0 - spec.pivot
		shadow_sprite.position = spec.offset
		shadow.add_child(shadow_sprite)
		return

	var shadow_shape := Polygon2D.new()
	shadow_shape.polygon = JoshArtLayout.ellipse(
		JoshArtLayout.PLACEHOLDER_SHADOW.radii, JoshArtLayout.PLACEHOLDER_SHADOW.points)
	shadow_shape.color = JoshArtLayout.PLACEHOLDER_SHADOW.color
	shadow.add_child(shadow_shape)
	shadow.modulate.a = JoshArtLayout.SHADOW_ALPHA


# Its own node behind his sprite: the deck hangs below his frame, so nothing sized to that frame may
# own it.
func _build_glider() -> void:
	if JoshArtLayout.USE_FINAL_GLIDER:
		var spec := JoshArtLayout.FINAL_GLIDER
		glider_sprite = Sprite2D.new()
		glider_sprite.texture = load(spec.texture)
		glider_sprite.hframes = spec.hframes
		glider_sprite.scale = Vector2.ONE * spec.scale
		glider_sprite.offset = spec.frame_size / 2.0 - spec.pivot
		glider.add_child(glider_sprite)
		_place_glider()
		return

	var board := Polygon2D.new()
	board.polygon = JoshArtLayout.glider_shape()
	board.color = JoshArtLayout.PLACEHOLDER_GLIDER.color
	glider.add_child(board)
	var rim := Line2D.new()
	rim.points = board.polygon
	rim.closed = true
	rim.width = JoshArtLayout.PLACEHOLDER_GLIDER.edge_width
	rim.default_color = JoshArtLayout.PLACEHOLDER_GLIDER.edge_color
	glider.add_child(rim)


# The deck sits under his soles and mirrors with him.
func _place_glider() -> void:
	if not glider_sprite:
		return
	var spec := JoshArtLayout.FINAL_GLIDER
	glider_sprite.flip_h = flying_left
	glider_sprite.position = Vector2(-spec.offset.x if flying_left else spec.offset.x, spec.offset.y)


#ANIMATION

# A non-looping animation holds its last frame when it ends, unless `next_anim` follows it.
func play_anim(anim_name: StringName, next_anim: StringName = &"") -> void:
	current_anim = anim_name
	anim = JoshArtLayout.anim(anim_name)
	anim_next = next_anim
	anim_step = 0
	anim_clock = 0.0
	anim_done = false
	var sheet: Texture2D = load(anim.sheet)
	var frame_size: Vector2 = anim.get("frame_size", JoshArtLayout.FRAME_SIZE)
	# Back to the first frame before the frame count changes, so the current one can't be out of range.
	sprite.frame = 0
	sprite.texture = sheet
	sprite.hframes = roundi(sheet.get_width() / frame_size.x)
	sprite.offset = JoshArtLayout.sheet_offset(frame_size)
	sprite.rotation_degrees = anim.get("turn", 0.0)
	_show_anim_frame()


func _process(delta: float) -> void:
	if glider_sprite and glider.visible:
		glider_clock += delta
		glider_sprite.frame = int(glider_clock / JoshArtLayout.FINAL_GLIDER.frame_time) % glider_sprite.hframes
		_place_glider()
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
	# The symmetry axis is the anchor's column, so mirroring keeps his feet in place.
	sprite.flip_h = anim.get("flips", false) and flying_left


#FLIGHT

func feet_position() -> Vector2:
	return ground_position - Vector2(0, height)


# The uppercut shoves him back (PlayerFinisher). His floor point simply moves, clamped to the same
# bounds his own flight uses.
func knock_back(push: Vector2, time: float) -> void:
	var bounds := ground_bounds(height)
	var target := (ground_position + push).clamp(bounds.position, bounds.end)
	var slide := create_tween()
	slide.tween_method(func(to: Vector2) -> void:
		ground_position = to
		place()
	, ground_position, target, time).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)


func place() -> void:
	global_position = ground_position.round()
	air.position = Vector2(0, -roundf(height))
	# The shadow never leaves the floor however high he rides: only which frame it draws changes.
	shadow.global_position = global_position
	var riding_height: float = state_machine.glider_height
	var lift := clampf(height / riding_height, 0.0, 1.0)
	if shadow_sprite:
		shadow_sprite.frame = clampi(ceili(lift * (shadow_sprite.hframes - 1)), 0, shadow_sprite.hframes - 1)
		return
	shadow.scale = Vector2.ONE * lerpf(1.0, JoshArtLayout.SHADOW_AIR_SCALE, lift)
	shadow.modulate.a = JoshArtLayout.SHADOW_ALPHA * lerpf(1.0, JoshArtLayout.SHADOW_AIR_ALPHA, lift)


# Moves his floor point toward `target` and returns how far off it still is.
func fly_toward(target: Vector2, max_speed: float, delta: float) -> float:
	var to_target := target - ground_position
	var distance := to_target.length()
	var desired := Vector2.ZERO
	if distance > 0.0:
		# Never faster than he can brake from at half his acceleration, so he doesn't overshoot.
		var speed := minf(max_speed, minf(sqrt(FLY_ACCELERATION * distance), distance / FLY_ARRIVE_TIME))
		desired = to_target / distance * speed
	fly_velocity = fly_velocity.move_toward(desired, FLY_ACCELERATION * delta)
	ground_position += fly_velocity * delta
	place()
	if absf(fly_velocity.x) > FLY_TURN_SPEED and (fly_velocity.x < 0.0) != flying_left:
		flying_left = fly_velocity.x < 0.0
		if anim.get("flips", false):
			_show_anim_frame()
	return ground_position.distance_to(target)


# The floor points he can be over with his feet `at_height` px up: his shadow inside the ropes and his
# whole sprite on screen. Only for landing points and knock_back: a pass over the arena aims at an
# unclamped point off the side of the screen.
func ground_bounds(at_height: float) -> Rect2:
	var ropes: Rect2 = state_machine.ROPES
	var shadow_radii: Vector2 = JoshArtLayout.PLACEHOLDER_SHADOW.radii
	var body_box := JoshArtLayout.local_rect(JoshArtLayout.BODY_DRAWN)
	var top_left := Vector2(
		maxf(ropes.position.x + shadow_radii.x, -body_box.position.x),
		maxf(ropes.position.y + shadow_radii.y, at_height - body_box.position.y))
	var bottom_right := Vector2(
		minf(ropes.end.x - shadow_radii.x, VIEW_SIZE.x - body_box.end.x),
		minf(ropes.end.y - shadow_radii.y, VIEW_SIZE.y - body_box.end.y + at_height))
	return Rect2(top_left, bottom_right - top_left)


# Over the ropes while he rides, back on the floor when he lands.
func set_air_draw(up: bool) -> void:
	sprite.z_index = AIR_Z if up else GROUND_Z


# The card he rides grows under his feet as he steps on, and shrinks away when he drops off.
func grow_glider(seconds: float) -> void:
	glider_clock = 0.0
	_place_glider()
	glider.show()
	var grow := glider.create_tween()
	grow.tween_property(glider, "scale", Vector2.ONE, seconds).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)


func shrink_glider(seconds: float) -> void:
	var shrink := glider.create_tween()
	shrink.tween_property(glider, "scale", Vector2.ZERO, seconds).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	shrink.tween_callback(glider.hide)


func hide_glider() -> void:
	glider.scale = Vector2.ZERO
	glider.hide()


#EFFECTS

func shake_screen(strength: float, steps: int, step_time: float) -> void:
	ScreenView.shake(get_tree(), strength, steps, step_time)


# Shudders the drawn body in whole pixels; his hitboxes and shadow stay put.
func shake_sprite(strength: float, steps: int, step_time: float) -> void:
	var tween := sprite.create_tween()
	for i in steps:
		var offset := Vector2(randf_range(-strength, strength), randf_range(-strength, strength)).round()
		tween.tween_callback(func() -> void: sprite.position = sprite_base_position + offset)
		tween.tween_interval(step_time)
	tween.tween_callback(func() -> void: sprite.position = sprite_base_position)


# The call the three-card monte's reveal makes, over his health bar.
func show_banner(text: String) -> void:
	var label := Label.new()
	label.text = text
	label.theme = load("res://Assets/UI/ui_theme.tres")
	label.add_theme_font_size_override("font_size", JoshArtLayout.BANNER_FONT_SIZE)
	label.add_theme_color_override("font_color", JoshArtLayout.BANNER_COLOR)
	label.add_theme_color_override("font_outline_color", Color(0, 0, 0))
	label.add_theme_constant_override("outline_size", JoshArtLayout.BANNER_OUTLINE)
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.size = Vector2(1400, 160)
	label.pivot_offset = label.size / 2.0
	label.position = JoshArtLayout.BANNER_CENTRE - label.size / 2.0
	label.scale = Vector2.ONE * JoshArtLayout.BANNER_FROM_SCALE
	hud_layer.add_child(label)

	var show := label.create_tween()
	show.tween_property(label, "scale", Vector2.ONE * JoshArtLayout.BANNER_TO_SCALE,
		JoshArtLayout.BANNER_GROW_TIME).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	show.tween_interval(JoshArtLayout.BANNER_TIME - JoshArtLayout.BANNER_GROW_TIME)
	show.tween_property(label, "modulate:a", 0.0, 0.3)
	show.tween_callback(label.queue_free)


#COMBAT

# Punches only reach him while he is down recovering. The hurtbox keeps its facing groups the whole
# fight, so the player still faces him while he rides and his thrown cards land inside the guarded arc.
func set_hurtbox_active(active: bool) -> void:
	# Deferred: monitoring can't change inside a physics flush.
	hurtbox.set_deferred("monitoring", active)
	hurtbox.set_deferred("monitorable", active)


func _on_hurtbox_entered(area: Area2D) -> void:
	if boss_health <= 0 or not area.is_in_group("player attack"):
		return

	# Same phantom-hit filter as Mason: a punch that connects as its hitbox switches on is reported
	# again when PlayerPunching switches the hitbox off, which would eat the hit cap.
	if not area.monitorable and fight_clock - last_contact_hit_time < PHANTOM_HIT_WINDOW:
		return
	if area.get_parent().combo.resolve_punch(self) > 0 and area.monitorable:
		last_contact_hit_time = fight_clock


# Punches only land while he recovers on the ground.
func take_punch(amount: int) -> int:
	if hits_this_window >= MAX_HITS_PER_WINDOW or not state_machine.is_recovering():
		return 0
	var dealt := _apply_damage(amount)
	if dealt > 0:
		hits_this_window += 1
	return dealt


# Phase two can't be skipped: until a phase-two cycle starts, he can't drop past the threshold.
func _lowest_health() -> int:
	if state_machine.cycle_phase == 0:
		return floori(max_health * PHASE_TWO_RATIO)
	return 0


# A hit that would carry past the threshold is cut down to reach it exactly.
func _apply_damage(amount: int) -> int:
	var dealt := mini(amount, boss_health - _lowest_health())
	if dealt <= 0:
		return 0

	boss_health -= dealt
	_update_health_bar()
	_hit_feedback()
	hit_sfx_player.play()

	if not phase_two and get_health_ratio() <= PHASE_TWO_RATIO:
		phase_two = true

	if boss_health > 0:
		state_machine.flinch()
	else:
		# area_entered fires mid physics flush; deferring keeps the state Exit/Enter code the defeat
		# sequence runs from having to be flush-safe.
		call_deferred("_on_defeated")
	return dealt


# The player's finisher (PlayerFinisher). Only his grounded recovery can be dazed, once per window,
# and only while the finisher can still take health past the phase floor.
func can_be_dazed() -> bool:
	return not defeated and boss_health > _lowest_health() and not daze_used and state_machine.is_recovering()


func enter_daze() -> void:
	daze_used = true


func exit_daze(_finisher_landed: bool) -> void:
	pass


func end_recovery(stagger_time: float) -> bool:
	if defeated or boss_health <= 0 or not state_machine.is_recovering():
		return false
	state_machine.stagger_then_start_cycle(stagger_time)
	return true


# Past the hit cap, which the combo that led to it has used up, but not past the phase floor.
func take_finisher(amount: int) -> int:
	if not state_machine.is_recovering():
		return 0
	return _apply_damage(amount)


func get_max_health() -> int:
	return max_health


func get_daze_anchor() -> Vector2:
	return global_position + JoshArtLayout.DAZE_ANCHOR


# Where a parry tell stands while he winds up a throw: over his head at whatever height he is.
func tell_anchor() -> Vector2:
	return air.global_position + JoshArtLayout.TELL_ANCHOR


func get_finisher_hurtbox() -> Area2D:
	return hurtbox


func _on_defeated() -> void:
	defeated = true
	set_hurtbox_active(false)
	state_machine.enter_defeated()
	_clear_hazards()

	if music_player.playing:
		music_player.stop()
	victory_sfx_player.play()
	get_tree().call_group("arena_crowd", "cheer", 2.0)
	GameProgress.next_boss_scene = _next_fight()
	FightOutro.finish_fight(get_tree(), true)


# The boss ladder owns the order and skips fights whose scene isn't built yet; "" sends the Victory
# screen back to the menu.
func _next_fight() -> String:
	if GameProgress.has_method("next_fight_after"):
		return GameProgress.next_fight_after(FIGHT_SCENE)
	return ""


# Called by FightOutro when the player loses.
func on_player_defeated() -> void:
	state_machine.enter_player_defeated()
	_clear_hazards()


# Whoever won, nothing he has sent out may stay live.
func _clear_hazards() -> void:
	for hazard in get_tree().get_nodes_in_group(state_machine.HAZARD_GROUP):
		hazard.queue_free()


func _build_health_bar() -> void:
	hud_layer = CanvasLayer.new()
	add_child(hud_layer)

	name_label = Label.new()
	name_label.text = "JOSH"
	name_label.position = Vector2(820, 36)
	name_label.theme = load("res://Assets/UI/ui_theme.tres")
	name_label.add_theme_color_override("font_color", Color(1, 1, 1))
	name_label.add_theme_color_override("font_outline_color", Color(0, 0, 0))
	name_label.add_theme_constant_override("outline_size", 6)
	hud_layer.add_child(name_label)

	health_bar = ProgressBar.new()
	health_bar.min_value = 0
	health_bar.max_value = max_health
	health_bar.value = boss_health
	health_bar.show_percentage = false
	health_bar.size = Vector2(380, 22)
	health_bar.position = Vector2(820, 70)

	var bg := StyleBoxFlat.new()
	bg.bg_color = Color(0.08, 0.08, 0.08, 0.85)
	bg.set_corner_radius_all(3)
	bg.border_width_left = 2
	bg.border_width_right = 2
	bg.border_width_top = 2
	bg.border_width_bottom = 2
	bg.border_color = Color(0, 0, 0)
	health_bar.add_theme_stylebox_override("background", bg)

	fill_style = StyleBoxFlat.new()
	fill_style.bg_color = Color(0.95, 0.75, 0.15, 1)
	fill_style.set_corner_radius_all(3)
	health_bar.add_theme_stylebox_override("fill", fill_style)

	hud_layer.add_child(health_bar)


func _update_health_bar() -> void:
	if not health_bar:
		return
	var tween = create_tween()
	tween.tween_property(health_bar, "value", boss_health, 0.2)

	var ratio := get_health_ratio()
	if ratio <= 0.34:
		fill_style.bg_color = Color(1.0, 0.55, 0.0, 1)
	elif ratio <= 0.6:
		fill_style.bg_color = Color(0.95, 0.75, 0.1, 1)
	else:
		fill_style.bg_color = Color(0.95, 0.75, 0.15, 1)


func _hit_feedback() -> void:
	if not sprite:
		return

	sprite.modulate = Color(3, 3, 3)
	var flash_tween = create_tween()
	flash_tween.tween_property(sprite, "modulate", Color(1, 1, 1), 0.15)
	shake_sprite(5.0, 4, 0.025)

	HitStop.freeze(get_tree(), 0.06)
