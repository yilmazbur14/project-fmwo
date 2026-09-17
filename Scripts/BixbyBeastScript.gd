extends CharacterBody2D

# A non-looping animation reached the end of its last frame.
signal anim_finished(anim_name: StringName)

const HitStop := preload("res://Scripts/HitStop.gd")
const FightOutro := preload("res://Scripts/FightOutro.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const BixbyBeastArtLayout := preload("res://Scripts/BixbyBeastArtLayout.gd")
# What Liam says once the fight is over, under player_won and player_lost.
const OUTRO_DIALOGUE := "res://Dialogue/LiamOutro.dialogue"
const NEXT_FIGHT_SCENE := "res://Scenes/Bosses/JordanBossFightScene.tscn"

#CONSTANTS
@export var max_health := 16
var boss_health := max_health
const MAX_HITS_PER_WINDOW := 3
const PHANTOM_HIT_WINDOW := 0.5
const VIEW_SIZE := Vector2(1920, 1080)
const HOVER_HEIGHT_PX := BixbyBeastArtLayout.HOVER_HEIGHT * BixbyBeastArtLayout.SCALE
# He eases into and out of every move: his speed never changes faster than FLY_ACCELERATION px/s², and
# over the last stretch he slows down as if FLY_ARRIVE_TIME seconds away.
const FLY_ARRIVE_TIME := 0.25
const FLY_ACCELERATION := 2600.0
# Flying sideways faster than this turns the fly frames to face the way he's going.
const FLY_TURN_SPEED := 60.0

#UI (built at runtime - no new art needed)
var health_bar: ProgressBar
var name_label: Label
var fill_style: StyleBoxFlat

# Kept under a node that y-sorts at the top edge of the arena floor, so it's drawn under every
# character wherever it goes, rather than over the feet of a player standing just behind him.
@export var shadow: Sprite2D
@onready var air: Node2D = $Air
@onready var sprite: Sprite2D = $Air/Sprite2D
@onready var fire_hitbox: Area2D = $Air/FireHitbox
@onready var hurtbox: Area2D = $Air/Hurtbox
@onready var state_machine = $StateManager

#AUDIO
@onready var music_player: AudioStreamPlayer = $MusicPlayer
@onready var hit_sfx_player: AudioStreamPlayer = $HitSfxPlayer
@onready var victory_sfx_player: AudioStreamPlayer = $VictorySfxPlayer
@onready var windup_sfx_player: AudioStreamPlayer = $WindupSfxPlayer
@onready var breath_sfx_player: AudioStreamPlayer = $BreathSfxPlayer
@onready var land_sfx_player: AudioStreamPlayer = $LandSfxPlayer
@onready var recover_sfx_player: AudioStreamPlayer = $RecoverSfxPlayer
@onready var wing_sfx_player: AudioStreamPlayer = $WingSfxPlayer
@onready var slap_sfx_player: AudioStreamPlayer = $SlapSfxPlayer
@onready var growl_sfx_player: AudioStreamPlayer = $GrowlSfxPlayer
@onready var gulp_sfx_player: AudioStreamPlayer = $GulpSfxPlayer
@onready var glow_sfx_player: AudioStreamPlayer = $GlowSfxPlayer
@onready var roar_sfx_player: AudioStreamPlayer = $RoarSfxPlayer
@onready var blast_sfx_player: AudioStreamPlayer = $BlastSfxPlayer
@onready var pound_sfx_player: AudioStreamPlayer = $PoundSfxPlayer
@onready var scream_sfx_player: AudioStreamPlayer = $ScreamSfxPlayer

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

var current_anim := &""
var anim: Dictionary = {}
var anim_step := 0
var anim_clock := 0.0
var anim_next := &""
var anim_done := false
var shadow_sheets: Array[Texture2D] = []
# Fire outline per fire-breath frame.
var fire_shapes := {}


func _ready() -> void:
	add_to_group(FightOutro.BOSS_GROUP)
	hurtbox.area_entered.connect(_on_hurtbox_entered)
	# The exported value is only set after the variable above was initialised.
	boss_health = max_health

	sprite_base_position = sprite.position
	ground_position = global_position
	_apply_art_layout()
	_build_health_bar()

	# Placeholders: beast Bixby has no theme or sounds of his own yet.
	music_player.stream = load("res://Assets/Audio/Music/boss_theme.ogg")
	if music_player.stream:
		music_player.stream.loop = true
	hit_sfx_player.stream = load("res://Assets/Audio/SFX/hit_impact.ogg")
	victory_sfx_player.stream = load("res://Assets/Audio/SFX/victory_fanfare.ogg")
	windup_sfx_player.stream = load("res://Assets/Audio/SFX/laser_charge.ogg")
	breath_sfx_player.stream = load("res://Assets/Audio/SFX/whirlwind_whoosh.ogg")
	land_sfx_player.stream = load("res://Assets/Audio/SFX/earthquake_slam.ogg")
	recover_sfx_player.stream = load("res://Assets/Audio/SFX/downed_stinger.ogg")
	wing_sfx_player.stream = load("res://Assets/Audio/SFX/whirlwind_whoosh.ogg")
	slap_sfx_player.stream = load("res://Assets/Audio/SFX/hit_impact.ogg")
	growl_sfx_player.stream = load("res://Assets/Audio/SFX/wrestler_charge.ogg")
	gulp_sfx_player.stream = load("res://Assets/Audio/SFX/wrestler_collision.ogg")
	glow_sfx_player.stream = load("res://Assets/Audio/SFX/laser_charge.ogg")
	# His own voice: the blast he transforms on, the roar he lands on, and the scream he spins with.
	blast_sfx_player.stream = load("res://Assets/Audio/SFX/bixby_roar_short.wav")
	roar_sfx_player.stream = load("res://Assets/Audio/SFX/bixby_roar.wav")
	scream_sfx_player.stream = load("res://Assets/Audio/SFX/bixby_roar_short.wav")
	pound_sfx_player.stream = load("res://Assets/Audio/SFX/earthquake_slam.ogg")


func start_music() -> void:
	if music_player and not music_player.playing:
		music_player.play()


func get_health_ratio() -> float:
	return float(boss_health) / float(max_health)


func _physics_process(delta: float) -> void:
	fight_clock += delta


func _apply_art_layout() -> void:
	for path in BixbyBeastArtLayout.SHADOW_SHEETS:
		shadow_sheets.append(load(path))
	shadow.texture = shadow_sheets[BixbyBeastArtLayout.Shadow.AIR]
	shadow.hframes = roundi(shadow.texture.get_width() / BixbyBeastArtLayout.SHADOW_FRAME_SIZE.x)
	shadow.offset = BixbyBeastArtLayout.shadow_offset()
	shadow.modulate.a = BixbyBeastArtLayout.SHADOW_ALPHA

	for frame in BixbyBeastArtLayout.FIRE_OUTLINES:
		var shape := CollisionPolygon2D.new()
		shape.polygon = BixbyBeastArtLayout.fire_outline(frame)
		shape.disabled = true
		fire_hitbox.add_child(shape)
		fire_shapes[frame] = shape

	var box := BixbyBeastArtLayout.local_rect(BixbyBeastArtLayout.RECOVER_BODY_BOX)
	var hurtbox_shape: CollisionShape2D = hurtbox.get_node("CollisionShape2D")
	hurtbox_shape.position = box.get_center()
	(hurtbox_shape.shape as RectangleShape2D).size = box.size


#ANIMATION

# A non-looping animation holds its last frame when it ends, unless `next_anim` follows it. A looping one
# can be started part way round, which is how the scream picks the heads it switches on with.
func play_anim(anim_name: StringName, next_anim: StringName = &"", from_step := 0) -> void:
	current_anim = anim_name
	anim = BixbyBeastArtLayout.ANIMS[anim_name]
	anim_next = next_anim
	anim_step = from_step
	anim_clock = 0.0
	anim_done = false
	var sheet: Texture2D = load(anim.sheet)
	var frame_size: Vector2 = anim.get("frame_size", BixbyBeastArtLayout.FRAME_SIZE)
	# Back to the first frame before the frame count changes, so the current one can't be out of range.
	sprite.frame = 0
	sprite.texture = sheet
	sprite.hframes = roundi(sheet.get_width() / frame_size.x)
	sprite.offset = BixbyBeastArtLayout.sheet_offset(frame_size)
	_show_anim_frame()


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
	sprite.frame = frame
	var shadows: Array = anim.shadows
	var shadow_step: Array = shadows[mini(anim_step, shadows.size() - 1)]
	shadow.texture = shadow_sheets[shadow_step[0]]
	shadow.frame = shadow_step[1]
	# The symmetry axis is the anchor's column, so mirroring keeps his feet in place.
	var mirrored: bool = anim.get("flips", false) and flying_left
	sprite.flip_h = mirrored
	shadow.flip_h = mirrored
	# The fire hitbox is always the fire the current frame draws.
	_set_fire_shape(frame if anim.sheet == BixbyBeastArtLayout.FIRE_SHEET else -1)


func _set_fire_shape(frame: int) -> void:
	for shape_frame in fire_shapes:
		# Frames can change inside a physics flush, where shapes can't be switched directly.
		fire_shapes[shape_frame].set_deferred("disabled", shape_frame != frame)


# The frame of `sheet` on screen right now, or -1 if that isn't the sheet he's drawing.
func drawn_frame_of(sheet: String) -> int:
	return sprite.frame if anim.get("sheet", "") == sheet else -1


func fire_touches(area: Area2D) -> bool:
	return fire_hitbox.get_overlapping_areas().has(area)


# Where the full stream's fire meets the floor, in global px.
func fire_ground_contact() -> Rect2:
	var contact := BixbyBeastArtLayout.local_rect(BixbyBeastArtLayout.FIRE_GROUND_CONTACT)
	return Rect2(air.global_position + contact.position, contact.size)


#FLIGHT

# The transformation: he appears where Bixby stood, hovering `at_height` px up if the last frame left him
# in the air.
func appear(feet: Vector2, at_height := 0.0) -> void:
	height = at_height
	var bounds := ground_bounds(height)
	ground_position = feet.clamp(bounds.position, bounds.end)
	fly_velocity = Vector2.ZERO
	place()
	air.show()
	shadow.show()


func feet_position() -> Vector2:
	return ground_position - Vector2(0, height)


# The uppercut shoves him back (PlayerFinisher). He flies, so his floor point simply moves, clamped
# to the same bounds his own flight uses; the fire patches he has already laid stay where they are.
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
	shadow.global_position = global_position


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


# The floor points he can be over with his feet `at_height` px up: his whole shadow inside the ropes and
# his whole sprite on screen.
func ground_bounds(at_height: float) -> Rect2:
	var ropes: Rect2 = state_machine.ROPES
	var shadow_box := BixbyBeastArtLayout.shadow_rect()
	var body_box := BixbyBeastArtLayout.local_rect(BixbyBeastArtLayout.BODY_DRAWN)
	var top_left := Vector2(
		maxf(ropes.position.x - shadow_box.position.x, -body_box.position.x),
		maxf(ropes.position.y - shadow_box.position.y, at_height - body_box.position.y))
	var bottom_right := Vector2(
		minf(ropes.end.x - shadow_box.end.x, VIEW_SIZE.x - body_box.end.x),
		minf(ropes.end.y - shadow_box.end.y, VIEW_SIZE.y - body_box.end.y + at_height))
	return Rect2(top_left, bottom_right - top_left)


# Where his feet go to breathe fire on a player standing at `target`: straight above them, with the player
# breath_aim_depth px below his feet, in the wide lower half of the stream. A player that close to the back
# rope or a side rope is out of reach with his whole sprite on screen, so there he rises or leans past the
# edge of the screen, but only as far as the fire needs to reach them.
func breath_aim(target: Vector2) -> Vector2:
	var fire_box := BixbyBeastArtLayout.local_rect(BixbyBeastArtLayout.FIRE_DRAWN)
	var on_screen_top := -fire_box.position.y
	var y: float = target.y - state_machine.breath_aim_depth
	if y < on_screen_top:
		y = maxf(minf(on_screen_top, target.y + state_machine.breath_mouth_reach), on_screen_top - state_machine.breath_top_overshoot)
	var overshoot: float = state_machine.breath_side_overshoot
	return Vector2(
		clampf(target.x, -fire_box.position.x - overshoot, VIEW_SIZE.x - fire_box.end.x + overshoot),
		minf(y, VIEW_SIZE.y - fire_box.end.y))


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


#COMBAT

# Punches only reach him while he's down on the ground. The hurtbox stays a facing target the whole
# fight, so the player keeps facing him while he flies.
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


func _apply_damage(amount: int) -> int:
	var dealt := mini(amount, boss_health)
	if dealt <= 0:
		return 0
	boss_health -= dealt
	_update_health_bar()
	_hit_feedback()
	hit_sfx_player.play()

	if boss_health > 0:
		state_machine.flinch()
	else:
		# area_entered fires mid physics flush; deferring keeps the state Exit/Enter code the defeat
		# sequence runs from having to be flush-safe.
		call_deferred("_on_defeated")
	return dealt


# The player's finisher (PlayerFinisher). Only his grounded recovery can be dazed, once per landing.
func can_be_dazed() -> bool:
	return not defeated and boss_health > 0 and not daze_used and state_machine.is_recovering()


func enter_daze() -> void:
	daze_used = true


func exit_daze(_finisher_landed: bool) -> void:
	pass


func end_recovery(stagger_time: float) -> bool:
	if defeated or boss_health <= 0 or not state_machine.is_recovering():
		return false
	state_machine.stagger_then_take_off(stagger_time)
	return true


# Past the hit cap. He has no phase floors.
func take_finisher(amount: int) -> int:
	if not state_machine.is_recovering():
		return 0
	return _apply_damage(amount)


func get_max_health() -> int:
	return max_health


func get_daze_anchor() -> Vector2:
	return air.global_position + BixbyBeastArtLayout.local(BixbyBeastArtLayout.DAZE_ANCHOR)


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


# Called by Defeated once the coughed-up Liam has landed, so the win lines come after it.
func finish_victory() -> void:
	GameProgress.next_boss_scene = NEXT_FIGHT_SCENE
	FightOutro.finish_fight(get_tree(), true)


# Called by FightOutro when the player loses.
func on_player_defeated() -> void:
	state_machine.enter_player_defeated()
	_clear_hazards()


# Whoever won, no fire and nothing he's sent out may stay live.
func _clear_hazards() -> void:
	_set_fire_shape(-1)
	for hazard in get_tree().get_nodes_in_group(state_machine.HAZARD_GROUP):
		hazard.queue_free()


func _build_health_bar() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)

	name_label = Label.new()
	name_label.text = "LIAM & BIXBY"
	name_label.position = Vector2(700, 36)
	name_label.theme = load("res://Assets/UI/ui_theme.tres")
	name_label.add_theme_color_override("font_color", Color(1, 1, 1))
	name_label.add_theme_color_override("font_outline_color", Color(0, 0, 0))
	name_label.add_theme_constant_override("outline_size", 6)
	layer.add_child(name_label)

	health_bar = ProgressBar.new()
	health_bar.min_value = 0
	health_bar.max_value = max_health
	health_bar.value = boss_health
	health_bar.show_percentage = false
	health_bar.size = Vector2(460, 22)
	health_bar.position = Vector2(700, 70)

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
	fill_style.bg_color = Color(0.62, 0.12, 0.2, 1)
	fill_style.set_corner_radius_all(3)
	health_bar.add_theme_stylebox_override("fill", fill_style)

	layer.add_child(health_bar)


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
		fill_style.bg_color = Color(0.62, 0.12, 0.2, 1)


func _hit_feedback() -> void:
	if not sprite:
		return

	sprite.modulate = Color(3, 3, 3)
	var flash_tween = create_tween()
	flash_tween.tween_property(sprite, "modulate", Color(1, 1, 1), 0.15)
	shake_sprite(5.0, 4, 0.025)

	HitStop.freeze(get_tree(), 0.06)
