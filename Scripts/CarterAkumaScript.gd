extends CharacterBody2D

# Carter, boss 5. He has one move: he flashes his eyes, drags the player to the middle of the ring,
# puts the lights out and sends five clones through them one at a time, then stands there open while
# the lights come back. Everything about the sequence itself lives in CarterRagingDemon; this node is
# his body, his health, his art and the darkness it borrows.
# Not to be confused with Scripts/CarterScript.gd, the wrestler Mason calls in - a different
# character with his own art and script.

# A non-looping animation reached the end of its last frame.
signal anim_finished(anim_name: StringName)

const HitStop := preload("res://Scripts/HitStop.gd")
const FightOutro := preload("res://Scripts/FightOutro.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const CarterArtLayout := preload("res://Scripts/CarterArtLayout.gd")
# What he says once the fight is over, under player_won and player_lost.
const OUTRO_DIALOGUE := "res://Dialogue/CarterOutro.dialogue"
const FIGHT_SCENE := "res://Scenes/Bosses/CarterBossFightScene.tscn"

#CONSTANTS
# Josh is 14 and Mason 10; Carter is fight 5 of 7. A perfect round plus three punches and a finisher
# takes 11 of these, a good round plus three punches 5, a sloppy one 2.
@export var max_health := 20
var boss_health := max_health
const MAX_HITS_PER_WINDOW := 3
const PHANTOM_HIT_WINDOW := 0.5
const VIEW_SIZE := Vector2(1920, 1080)

# Three takes of one rush, rotated by clone, so five of them a round don't sound like one sound
# played five times.
const RUSH_SFX := [
	"res://Assets/Audio/SFX/carter_rush_1.wav",
	"res://Assets/Audio/SFX/carter_rush_2.wav",
	"res://Assets/Audio/SFX/carter_rush_3.wav",
]

#UI (built at runtime - no new art needed)
var hud_layer: CanvasLayer
var health_bar: ProgressBar
var name_label: Label
var fill_style: StyleBoxFlat

# The yank's ghosts, its dust and the entrance's ground ring. It sits one px below the top edge of
# the arena floor, so it y-sorts over the mat and under every character wherever its children are put.
@export var floor_layer: Node2D
# The clones, on their own z over the darkness.
@export var clone_layer: Node2D
# The darkness: world-space Node2Ds, never a CanvasLayer. A CanvasLayer would black out the HUD, this
# health bar and the dialogue balloon along with the arena.
@export var dark_stage: Node2D
@export var curtain: Node2D
@export var pool: Node2D
@export var flash_layer: CanvasLayer
@export var flash: ColorRect

@onready var sprite: Sprite2D = $Sprite2D
@onready var aura: Sprite2D = $Aura
@onready var mark_glow: Sprite2D = $MarkGlow
@onready var hurtbox: Area2D = $Hurtbox
@onready var state_machine = $StateManager

#AUDIO
@onready var music_player: AudioStreamPlayer = $MusicPlayer
@onready var hit_sfx_player: AudioStreamPlayer = $HitSfxPlayer
@onready var victory_sfx_player: AudioStreamPlayer = $VictorySfxPlayer
@onready var flash_sfx_player: AudioStreamPlayer = $FlashSfxPlayer
@onready var yank_sfx_player: AudioStreamPlayer = $YankSfxPlayer
@onready var dark_sfx_player: AudioStreamPlayer = $DarkSfxPlayer
@onready var rush_sfx_player: AudioStreamPlayer = $RushSfxPlayer
@onready var strike_sfx_player: AudioStreamPlayer = $StrikeSfxPlayer
@onready var break_sfx_player: AudioStreamPlayer = $BreakSfxPlayer
@onready var feint_sfx_player: AudioStreamPlayer = $FeintSfxPlayer
@onready var finish_sfx_player: AudioStreamPlayer = $FinishSfxPlayer
@onready var recover_sfx_player: AudioStreamPlayer = $RecoverSfxPlayer
@onready var land_sfx_player: AudioStreamPlayer = $LandSfxPlayer

var defeated := false
var hits_this_window := 0
# One finisher daze per recovery; Recover clears it.
var daze_used := false

var fight_clock := 0.0
var last_contact_hit_time := -INF

var sprite_base_position: Vector2
var music_base_db := 0.0
var music_duck: Tween

var aura_clock := 0.0
var mark_clock := 0.0

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
	_apply_art_layout()
	_build_health_bar()
	_build_dark_stage()

	# Placeholder: he has no theme of his own yet. The SFX are his own.
	music_player.stream = load("res://Assets/Audio/Music/boss3_theme.ogg")
	if music_player.stream:
		music_player.stream.loop = true
	music_base_db = music_player.volume_db
	hit_sfx_player.stream = load("res://Assets/Audio/SFX/hit_impact.ogg")
	victory_sfx_player.stream = load("res://Assets/Audio/SFX/victory_fanfare.ogg")
	flash_sfx_player.stream = load("res://Assets/Audio/SFX/carter_eye_flash.wav")
	yank_sfx_player.stream = load("res://Assets/Audio/SFX/carter_warp.wav")
	dark_sfx_player.stream = load("res://Assets/Audio/SFX/carter_dark.wav")
	rush_sfx_player.stream = load(RUSH_SFX[0])
	strike_sfx_player.stream = load("res://Assets/Audio/SFX/carter_strike.wav")
	break_sfx_player.stream = load("res://Assets/Audio/SFX/carter_parry_break.wav")
	feint_sfx_player.stream = load("res://Assets/Audio/SFX/carter_fake_punish.wav")
	finish_sfx_player.stream = load("res://Assets/Audio/SFX/carter_finish.wav")
	recover_sfx_player.stream = load("res://Assets/Audio/SFX/carter_spent.wav")
	land_sfx_player.stream = load("res://Assets/Audio/SFX/wrestler_collision.ogg")


func start_music() -> void:
	if music_player and not music_player.playing:
		music_player.play()


func get_health_ratio() -> float:
	return float(boss_health) / float(max_health)


func _physics_process(delta: float) -> void:
	fight_clock += delta


func _apply_art_layout() -> void:
	var box := CarterArtLayout.local_rect(CarterArtLayout.RECOVER_BODY_BOX)
	var hurtbox_shape: CollisionShape2D = hurtbox.get_node("CollisionShape2D")
	hurtbox_shape.position = box.get_center()
	(hurtbox_shape.shape as RectangleShape2D).size = box.size

	_build_aura()
	_build_mark_glow()


# Behind his sprite and on its own node rather than a child of it: boss.sprite has to stay the body
# sprite, which PlayerFinisher._flash and PlayerCombo._charged_feedback both write to.
func _build_aura() -> void:
	if not CarterArtLayout.USE_FINAL_AURA:
		aura.hide()
		return
	var spec := CarterArtLayout.FINAL_AURA
	aura.texture = load(spec.texture)
	aura.hframes = spec.hframes
	aura.scale = Vector2.ONE * spec.scale
	aura.offset = CarterArtLayout.sheet_offset(spec.frame_size)
	aura.modulate.a = CarterArtLayout.AURA_ALPHA


func _build_mark_glow() -> void:
	mark_glow.hide()
	if not CarterArtLayout.USE_FINAL_MARK_GLOW:
		return
	var spec := CarterArtLayout.FINAL_MARK_GLOW
	mark_glow.texture = load(spec.texture)
	mark_glow.hframes = spec.hframes
	mark_glow.scale = Vector2.ONE * spec.scale
	mark_glow.offset = CarterArtLayout.inset_offset(spec.frame_size, spec.offset)
	mark_glow.material = CarterArtLayout.additive()


#ANIMATION

# A non-looping animation holds its last frame when it ends, unless `next_anim` follows it.
func play_anim(anim_name: StringName, next_anim: StringName = &"") -> void:
	current_anim = anim_name
	anim = CarterArtLayout.anim(anim_name)
	anim_next = next_anim
	anim_step = 0
	anim_clock = 0.0
	anim_done = false
	var sheet: Texture2D = load(anim.sheet)
	var frame_size: Vector2 = anim.get("frame_size", CarterArtLayout.FRAME_SIZE)
	# Back to the first frame before the frame count changes, so the current one can't be out of range.
	sprite.frame = 0
	sprite.texture = sheet
	sprite.hframes = roundi(sheet.get_width() / frame_size.x)
	sprite.offset = CarterArtLayout.sheet_offset(frame_size)
	sprite.rotation_degrees = anim.get("turn", 0.0)
	_show_anim_frame()


func _process(delta: float) -> void:
	_step_effects(delta)
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


func _step_effects(delta: float) -> void:
	if aura.visible and aura.texture:
		aura_clock += delta
		aura.frame = int(aura_clock / CarterArtLayout.FINAL_AURA.frame_time) % aura.hframes
	if mark_glow.visible and mark_glow.texture:
		mark_clock += delta
		mark_glow.frame = int(mark_clock / CarterArtLayout.FINAL_MARK_GLOW.frame_time) % mark_glow.hframes


func _frame_time() -> float:
	var times: Array = anim.times
	return times[mini(anim_step, times.size() - 1)]


func _show_anim_frame() -> void:
	sprite.frame = anim.frames[anim_step]


# The mark on his back flaring: on while the eyes go and through the summon, off once he is gone.
func show_mark_glow(on: bool) -> void:
	if on and not CarterArtLayout.USE_FINAL_MARK_GLOW:
		return
	mark_clock = 0.0
	mark_glow.visible = on


func show_aura(on: bool) -> void:
	if on and not CarterArtLayout.USE_FINAL_AURA:
		return
	aura.visible = on


# Both his body and everything drawn with it, for the beat he is swallowed by the dark.
func show_body(on: bool) -> void:
	sprite.visible = on
	show_aura(on)
	if not on:
		mark_glow.hide()


#EFFECTS

func shake_screen(strength: float, steps: int, step_time: float) -> void:
	ScreenView.shake(get_tree(), strength, steps, step_time)


# Shudders the drawn body in whole pixels; his hitbox stays put.
func shake_sprite(strength: float, steps: int, step_time: float) -> void:
	var tween := sprite.create_tween()
	for i in steps:
		var offset := Vector2(randf_range(-strength, strength), randf_range(-strength, strength)).round()
		tween.tween_callback(func() -> void: sprite.position = sprite_base_position + offset)
		tween.tween_interval(step_time)
	tween.tween_callback(func() -> void: sprite.position = sprite_base_position)


# Node-bound, so a finisher's freeze holds it and the end of the fight takes it away.
func duck_music(db: float, seconds: float) -> void:
	if music_duck:
		music_duck.kill()
	music_duck = music_player.create_tween()
	music_duck.tween_property(music_player, "volume_db", music_base_db + db, seconds)


func restore_music(seconds: float) -> void:
	duck_music(0.0, seconds)


# Nothing may be left holding the music down once the sequence is over, however it ended.
func snap_music_level() -> void:
	if music_duck:
		music_duck.kill()
		music_duck = null
	music_player.volume_db = music_base_db


func play_rush(index: int) -> void:
	rush_sfx_player.stream = load(RUSH_SFX[index % RUSH_SFX.size()])
	rush_sfx_player.play()


#THE DARKNESS

func _build_dark_stage() -> void:
	# Above the floor and the crowd, below the fighters: that is what makes the player and the clones
	# read as lit rather than tinted, and it inverts if these are wrong.
	dark_stage.z_index = CarterArtLayout.DARK_Z
	pool.z_index = CarterArtLayout.POOL_Z - CarterArtLayout.DARK_Z
	clone_layer.z_index = CarterArtLayout.CLONE_Z
	dark_stage.hide()
	curtain.modulate.a = 0.0
	pool.scale = Vector2.ONE * CarterArtLayout.POOL_OPEN_FROM
	pool.modulate.a = 0.0
	_build_pool()
	_build_curtain()


func _build_pool() -> void:
	var spec := CarterArtLayout.spotlight()
	if spec.has("texture"):
		var light := Sprite2D.new()
		light.texture = load(spec.texture)
		light.centered = false
		# The texel that goes on the player's feet, which is where the pool is placed.
		light.offset = -spec.anchor
		light.scale = Vector2.ONE * spec.scale
		light.material = CarterArtLayout.additive()
		pool.add_child(light)
		return
	var glow := Polygon2D.new()
	glow.polygon = CarterArtLayout.ellipse(spec.radii, spec.points)
	glow.color = spec.color
	glow.material = CarterArtLayout.additive()
	pool.add_child(glow)


# The sheet is exactly the view, so the border quads are what a screen shake can pull into frame
# instead of an undarkened strip.
func _build_curtain() -> void:
	var edge := Color(0, 0, 0, 1)
	if CarterArtLayout.USE_FINAL_DARKNESS:
		var spec := CarterArtLayout.FINAL_DARKNESS
		var dark := Sprite2D.new()
		dark.texture = load(spec.texture)
		dark.centered = false
		dark.scale = Vector2.ONE * spec.scale
		curtain.add_child(dark)
		edge.a = spec.edge_alpha
	else:
		var whole := Polygon2D.new()
		whole.polygon = CarterArtLayout.rect_polygon(CarterArtLayout.VIEW_RECT)
		whole.color = CarterArtLayout.PLACEHOLDER_DARKNESS.color
		curtain.add_child(whole)
		edge = CarterArtLayout.PLACEHOLDER_DARKNESS.color
	for piece in CarterArtLayout.border_rects():
		var quad := Polygon2D.new()
		quad.polygon = CarterArtLayout.rect_polygon(piece)
		quad.color = edge
		curtain.add_child(quad)


func darken(seconds: float) -> void:
	dark_stage.show()
	var fade := curtain.create_tween()
	fade.tween_property(curtain, "modulate:a", 1.0, seconds)


func open_pool(seconds: float) -> void:
	var bloom := pool.create_tween().set_parallel()
	bloom.tween_property(pool, "scale", Vector2.ONE, seconds).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	bloom.tween_property(pool, "modulate:a", 1.0, seconds)


func clear_dark(seconds: float) -> void:
	var fade := curtain.create_tween().set_parallel()
	fade.tween_property(curtain, "modulate:a", 0.0, seconds)
	fade.tween_property(pool, "modulate:a", 0.0, seconds)
	fade.chain().tween_callback(dark_stage.hide)


# A parried clone: the dark lifts for a moment so the hit landing reads through it.
func lift_curtain() -> void:
	var rest: float = curtain.modulate.a
	var lifted := maxf(rest - CarterArtLayout.CURTAIN_PARRY_LIFT, 0.0)
	var pulse := curtain.create_tween()
	pulse.tween_property(curtain, "modulate:a", lifted, CarterArtLayout.CURTAIN_PARRY_TIME / 2.0)
	pulse.tween_property(curtain, "modulate:a", rest, CarterArtLayout.CURTAIN_PARRY_TIME / 2.0)


# However the sequence ended, the dark must not survive it: a fight left dark is unplayable and one
# that reached FightOutro would cover the outro's lines.
func snap_dark_clear() -> void:
	curtain.modulate.a = 0.0
	pool.modulate.a = 0.0
	pool.scale = Vector2.ONE * CarterArtLayout.POOL_OPEN_FROM
	dark_stage.hide()
	flash.color.a = 0.0


func place_pool(at: Vector2) -> void:
	pool.global_position = at.round()


# The lights coming back: a bloom in the middle of the ring, with the screen blown out behind it by
# the flash rect rather than by the bloom itself.
func finish_bloom() -> void:
	if not CarterArtLayout.USE_FINAL_FINISH:
		return
	var spec := CarterArtLayout.FINAL_FINISH
	var bloom := Sprite2D.new()
	bloom.texture = load(spec.texture)
	bloom.hframes = spec.hframes
	bloom.scale = Vector2.ONE * spec.scale
	bloom.offset = spec.frame_size / 2.0 - spec.pivot
	bloom.material = CarterArtLayout.additive()
	bloom.z_index = CarterArtLayout.FINISH_Z
	clone_layer.add_child(bloom)
	bloom.global_position = spec.at
	var times: Array = spec.frame_times
	var alphas: Array = spec.flash
	var play := bloom.create_tween()
	for i in spec.hframes:
		var step: int = i
		play.tween_callback(func() -> void:
			bloom.frame = step
			flash.color.a = alphas[step])
		play.tween_interval(times[i])
	play.tween_callback(bloom.hide)
	play.tween_property(flash, "color:a", 0.0, 0.12)
	play.tween_callback(bloom.queue_free)


#THE FEINT PUNISH

# Its own word over his health bar. The PlayerDefense popup set belongs to the defence coder, and a
# word only this fight says doesn't belong in it.
func show_word(text: String) -> void:
	var label := Label.new()
	label.text = text
	label.theme = load("res://Assets/UI/ui_theme.tres")
	label.add_theme_font_size_override("font_size", CarterArtLayout.WORD_FONT_SIZE)
	label.add_theme_color_override("font_color", CarterArtLayout.WORD_COLOR)
	label.add_theme_color_override("font_outline_color", Color(0, 0, 0))
	label.add_theme_constant_override("outline_size", CarterArtLayout.WORD_OUTLINE)
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.size = Vector2(1400, 160)
	label.pivot_offset = label.size / 2.0
	label.position = CarterArtLayout.WORD_CENTRE - label.size / 2.0
	label.scale = Vector2.ONE * CarterArtLayout.WORD_FROM_SCALE
	hud_layer.add_child(label)

	var show := label.create_tween()
	show.tween_property(label, "scale", Vector2.ONE * CarterArtLayout.WORD_TO_SCALE,
		CarterArtLayout.WORD_GROW_TIME).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	show.tween_interval(CarterArtLayout.WORD_TIME - CarterArtLayout.WORD_GROW_TIME)
	show.tween_property(label, "modulate:a", 0.0, 0.3)
	show.tween_callback(label.queue_free)


# Four bands down the edges of the screen, on the flash layer so the darkness can't swallow them.
func edge_pulse() -> void:
	var spec := CarterArtLayout.EDGE_PULSE
	var deep: float = spec.thickness
	var bands := Control.new()
	bands.mouse_filter = Control.MOUSE_FILTER_IGNORE
	flash_layer.add_child(bands)
	var rects: Array[Rect2] = [
		Rect2(0.0, 0.0, VIEW_SIZE.x, deep),
		Rect2(0.0, VIEW_SIZE.y - deep, VIEW_SIZE.x, deep),
		Rect2(0.0, deep, deep, VIEW_SIZE.y - deep * 2.0),
		Rect2(VIEW_SIZE.x - deep, deep, deep, VIEW_SIZE.y - deep * 2.0),
	]
	for rect in rects:
		var band := ColorRect.new()
		band.color = spec.color
		band.mouse_filter = Control.MOUSE_FILTER_IGNORE
		band.position = rect.position
		band.size = rect.size
		bands.add_child(band)
	var fade := bands.create_tween()
	fade.tween_property(bands, "modulate:a", 0.0, spec.time)
	fade.tween_callback(bands.queue_free)


#COMBAT

# Punches only reach him while he is down recovering. The hurtbox keeps its groups the whole fight,
# so the player still faces him while the sequence runs.
func set_hurtbox_active(active: bool) -> void:
	# Deferred: monitoring can't change inside a physics flush.
	hurtbox.set_deferred("monitoring", active)
	hurtbox.set_deferred("monitorable", active)


func _on_hurtbox_entered(area: Area2D) -> void:
	if boss_health <= 0 or not area.is_in_group("player attack"):
		return

	# Same phantom-hit filter as Josh and Mason: a punch that connects as its hitbox switches on is
	# reported again when PlayerPunching switches the hitbox off, which would eat the hit cap.
	if not area.monitorable and fight_clock - last_contact_hit_time < PHANTOM_HIT_WINDOW:
		return
	if area.get_parent().combo.resolve_punch(self) > 0 and area.monitorable:
		last_contact_hit_time = fight_clock


# Punches only land while he stands there getting his breath back.
func take_punch(amount: int) -> int:
	if hits_this_window >= MAX_HITS_PER_WINDOW or not state_machine.is_recovering():
		return 0
	var dealt := _apply_damage(amount)
	if dealt > 0:
		hits_this_window += 1
	return dealt


# No phase floor: he has one move and no transformation, so nothing may hold his health up.
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


# The player's finisher (PlayerFinisher). Only his recovery can be dazed, once per window.
func can_be_dazed() -> bool:
	return not defeated and boss_health > 0 and not daze_used and state_machine.is_recovering()


func enter_daze() -> void:
	daze_used = true


func exit_daze(_finisher_landed: bool) -> void:
	pass


func end_recovery(stagger_time: float) -> bool:
	if defeated or boss_health <= 0 or not state_machine.is_recovering():
		return false
	state_machine.stagger_then_start_cycle(stagger_time)
	return true


# Past the hit cap, which the combo that led to it has used up.
func take_finisher(amount: int) -> int:
	if not state_machine.is_recovering():
		return 0
	return _apply_damage(amount)


func get_max_health() -> int:
	return max_health


func get_daze_anchor() -> Vector2:
	return global_position + CarterArtLayout.DAZE_ANCHOR


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
	name_label.text = GameProgress.boss_name(FIGHT_SCENE)
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
	fill_style.bg_color = Color(0.58, 0.22, 0.42, 1)
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
		fill_style.bg_color = Color(0.85, 0.2, 0.28, 1)
	elif ratio <= 0.66:
		fill_style.bg_color = Color(0.7, 0.2, 0.36, 1)
	else:
		fill_style.bg_color = Color(0.58, 0.22, 0.42, 1)


func _hit_feedback() -> void:
	if not sprite:
		return

	sprite.modulate = Color(3, 3, 3)
	var flash_tween = create_tween()
	flash_tween.tween_property(sprite, "modulate", Color(1, 1, 1), 0.15)
	shake_sprite(5.0, 4, 0.025)

	HitStop.freeze(get_tree(), 0.06)
