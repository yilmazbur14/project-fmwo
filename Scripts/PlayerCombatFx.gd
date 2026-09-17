extends Node

# How the player's defence looks and sounds: bursts where the guard meets an attack, flashes on the
# player's sprite, sounds and hit-stop. PlayerDefense decides every outcome; this only shows them.
# Flashes tween the sprite's self_modulate: the hurt flash and the i-frame flicker tween modulate,
# so the two never fight.

const HitStop := preload("res://Scripts/HitStop.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const AttackCatalog := preload("res://Scripts/AttackCatalog.gd")
const DefenseHypeArtLayout := preload("res://Scripts/DefenseHypeArtLayout.gd")

const SHAKE_STEPS := 6
const SHAKE_STEP_TIME := 0.03

@onready var player: CharacterBody2D = get_parent()
@onready var defense: Node = player.get_node("Defense")
@onready var fx_layer: Node2D = player.get_parent().get_node("FinisherFx")
@onready var sfx_player: AudioStreamPlayer = player.get_node("BlockSfxPlayer")
@onready var hype_sfx_player: AudioStreamPlayer = player.get_node("HypeFullSfxPlayer")
# The tinks ring on: parries in quick succession each need their own voice, and the sting its own.
@onready var sting_player: AudioStreamPlayer = player.get_node("ParryStingPlayer")
var parry_voices: Array[AudioStreamPlayer] = []
var parry_voice := 0

var flash: Tween
var stars: Sprite2D
var stun_clock := 0.0
# Only the newest zoom punch pulls the view back out.
var zoom_punch := 0


func _ready() -> void:
	for i in DefenseHypeArtLayout.PARRY_SFX_VOICES:
		parry_voices.append(player.get_node("ParrySfxPlayer%d" % i))
	defense.blocked.connect(_on_blocked)
	defense.parried.connect(_on_parried)
	defense.perfect_dodged.connect(_on_perfect_dodged)
	defense.guard_broken.connect(_on_guard_broken)
	defense.guard_recovered.connect(_on_guard_recovered)
	player.get_node("Hype").hype_full_changed.connect(_on_hype_full_changed)


func _process(delta: float) -> void:
	if not defense.is_guard_broken:
		return
	stun_clock += delta
	var spec := DefenseHypeArtLayout.guard_break_stars()
	if is_instance_valid(stars):
		stars.frame = int(stun_clock / spec.frame_time) % stars.hframes
		stars.global_position = (player.global_position + spec.offset).round()
	var pose := DefenseHypeArtLayout.guard_break_pose()
	if not pose.flicker.is_empty():
		player.sprite.self_modulate = pose.flicker[int(stun_clock / pose.flicker_time) % pose.flicker.size()]


func _on_blocked(hit: RefCounted, point: Vector2) -> void:
	_spawn_burst(DefenseHypeArtLayout.block_spark(), point)
	_flash_player(DefenseHypeArtLayout.BLOCK_FLASH, DefenseHypeArtLayout.BLOCK_FLASH_TIME)
	_play(DefenseHypeArtLayout.BLOCK_SFX)
	if hit.weight == AttackCatalog.Weight.HEAVY and defense.heavy_block_hit_stop > 0.0:
		HitStop.freeze(get_tree(), defense.heavy_block_hit_stop)


func _on_parried(hit: RefCounted, point: Vector2, _staggered: bool, streak: int) -> void:
	var tier := clampi(streak - 1, 0, 2)
	var spec := DefenseHypeArtLayout.parry_flash(tier)
	var away: Vector2 = point - player.hurtBox.get_node("CollisionShape2D").global_position
	_spawn_burst(spec, point + away.normalized() * spec.push, DefenseHypeArtLayout.PARRY_FLASH_SCALE[tier])
	_flash_player(DefenseHypeArtLayout.PARRY_FLASH[tier], DefenseHypeArtLayout.PARRY_FLASH_TIME[tier])
	_flick_attack(hit, away)
	_play_on(parry_voices[parry_voice], DefenseHypeArtLayout.parry_sfx(tier))
	parry_voice = (parry_voice + 1) % parry_voices.size()
	if tier >= 2:
		# After the tink, so the hit reads before the flourish.
		var sting := get_tree().create_timer(DefenseHypeArtLayout.PARRY_STREAK_STING_DELAY, true, false, true)
		sting.timeout.connect(func() -> void: _play_on(sting_player, DefenseHypeArtLayout.parry_streak_sting()))
	HitStop.freeze(get_tree(), defense.parry_hit_stop)
	_parry_punch(tier, away)
	get_tree().call_group("arena_crowd", "cheer", DefenseHypeArtLayout.PARRY_CHEER[tier])


# The jolt, and from tier 3 a short zoom, both in real time so the parry's hit-stop doesn't stretch
# them. Skipped during a finisher, which owns the zoom, and once the fight is decided.
func _parry_punch(tier: int, away: Vector2) -> void:
	if player.fight_over or player.finisher.is_active():
		return
	ScreenView.shake(get_tree(), DefenseHypeArtLayout.PARRY_SHAKE[tier], DefenseHypeArtLayout.PARRY_SHAKE_STEPS, DefenseHypeArtLayout.PARRY_SHAKE_STEP_TIME, -away, true)
	var zoom: float = DefenseHypeArtLayout.PARRY_ZOOM[tier]
	if zoom <= 1.0:
		return
	var half: float = DefenseHypeArtLayout.PARRY_ZOOM_TIME / 2.0
	zoom_punch += 1
	var punch := zoom_punch
	ScreenView.zoom_to(get_tree(), zoom, player.global_position, half, true)
	var settle := get_tree().create_timer(half, true, false, true)
	settle.timeout.connect(func() -> void:
		# Only the latest punch pulls the view back, so parries in a row can't fight each other.
		if punch == zoom_punch and not player.fight_over and not player.finisher.is_active():
			ScreenView.zoom_to(get_tree(), 1.0, ScreenView.focus, half, true)
	)


# The parried attack reacts: its art flashes, and a projectile's is knocked back a few px before it
# carries on. The boss's own sprite only flashes, and no hitbox ever moves.
func _flick_attack(hit: RefCounted, away: Vector2) -> void:
	var art := _attack_art(hit)
	if art == null:
		return
	art.self_modulate = DefenseHypeArtLayout.PARRY_ATTACK_FLASH
	art.create_tween().tween_property(art, "self_modulate", Color.WHITE, DefenseHypeArtLayout.PARRY_KNOCKBACK_TIME)
	if not (art is Sprite2D) or (is_instance_valid(hit.boss) and art == hit.boss.get("sprite")):
		return
	# The projectile breaks up where it was parried, at its own scale.
	var shatter := DefenseHypeArtLayout.parry_shatter()
	if not shatter.is_empty():
		var sprite_scale: float = (art as Sprite2D).global_scale.x
		_spawn_burst(shatter.merged({"scale": sprite_scale}, true), (art as Node2D).global_position)
	var sprite := art as Sprite2D
	var rest := sprite.offset
	var knock := rest + away.normalized() * DefenseHypeArtLayout.PARRY_KNOCKBACK / sprite.global_scale.x
	var flick := sprite.create_tween()
	flick.tween_property(sprite, "offset", knock, DefenseHypeArtLayout.PARRY_KNOCKBACK_TIME / 2.0)
	flick.tween_property(sprite, "offset", rest, DefenseHypeArtLayout.PARRY_KNOCKBACK_TIME / 2.0)


# Whatever draws the attack: the source itself, its own sprite, or the one beside it.
func _attack_art(hit: RefCounted) -> CanvasItem:
	var source = hit.source
	if not (source is Node) or not is_instance_valid(source):
		return null
	if source is Sprite2D:
		return source
	for parent in [source, source.get_parent()]:
		if parent == null:
			continue
		for child in parent.get_children():
			if child is Sprite2D and child.visible:
				return child
	return null


# No hit-stop: a slowdown inside a dash would eat the immunity, which counts physics frames.
func _on_perfect_dodged(_hit: RefCounted) -> void:
	_spawn_dodge_trail()
	_flash_player(DefenseHypeArtLayout.PERFECT_DODGE_FLASH, DefenseHypeArtLayout.PERFECT_DODGE_FLASH_TIME)
	_play(DefenseHypeArtLayout.PERFECT_DODGE_SFX)
	get_tree().call_group("arena_crowd", "cheer", DefenseHypeArtLayout.PERFECT_DODGE_CHEER)


func _spawn_dodge_trail() -> void:
	var spec := DefenseHypeArtLayout.perfect_dodge_trail()
	var count: int = DefenseHypeArtLayout.PERFECT_DODGE_GHOST_COUNT
	var from: Vector2 = defense.dash_start_position
	var to: Vector2 = player.global_position
	var row: int = player.facing
	for i in count:
		var ghost := Sprite2D.new()
		if spec.has("texture"):
			ghost.texture = load(spec.texture)
			ghost.hframes = spec.hframes
			ghost.vframes = spec.vframes
			ghost.frame_coords = Vector2i(0, row)
			ghost.scale = Vector2.ONE * spec.scale
		else:
			ghost.texture = player.sprite.texture
			ghost.hframes = player.sprite.hframes
			ghost.vframes = player.sprite.vframes
			ghost.frame = player.sprite.frame
			ghost.scale = player.sprite.global_scale
			ghost.modulate = spec.tint
		fx_layer.add_child(ghost)
		ghost.global_position = from.lerp(to, float(i) / count).round()
		var play := ghost.create_tween()
		if spec.has("texture"):
			for step in spec.frame_times.size():
				play.tween_callback(func() -> void: ghost.frame_coords = Vector2i(step, row))
				play.tween_interval(spec.frame_times[step])
		else:
			play.tween_property(ghost, "modulate:a", 0.0, spec.fade_time)
		play.tween_callback(ghost.queue_free)


func _on_guard_broken() -> void:
	if flash:
		flash.kill()
	player.sprite.self_modulate = Color.WHITE
	stun_clock = 0.0
	_clear_stars()
	var spec := DefenseHypeArtLayout.guard_break_stars()
	stars = Sprite2D.new()
	stars.texture = load(spec.texture)
	stars.hframes = spec.hframes
	stars.centered = false
	stars.offset = -spec.pivot
	stars.scale = Vector2.ONE * spec.scale
	fx_layer.add_child(stars)
	stars.global_position = (player.global_position + spec.offset).round()
	HitStop.freeze(get_tree(), defense.guard_break_hit_stop)
	ScreenView.shake(get_tree(), defense.guard_break_shake, SHAKE_STEPS, SHAKE_STEP_TIME)
	_play(DefenseHypeArtLayout.GUARD_BREAK_SFX)


func _on_hype_full_changed(full: bool) -> void:
	if not full:
		return
	_play_on(hype_sfx_player, DefenseHypeArtLayout.HYPE_FULL_SFX)


func _on_guard_recovered() -> void:
	_clear_stars()
	player.sprite.self_modulate = Color.WHITE


func _clear_stars() -> void:
	if is_instance_valid(stars):
		stars.queue_free()
	stars = null


func _flash_player(color: Color, time: float) -> void:
	if flash:
		flash.kill()
	player.sprite.self_modulate = color
	flash = player.sprite.create_tween()
	flash.tween_property(player.sprite, "self_modulate", Color.WHITE, time)


func _play(sound: Dictionary) -> void:
	_play_on(sfx_player, sound)


func _play_on(speaker: AudioStreamPlayer, sound: Dictionary) -> void:
	speaker.stream = load(sound.stream)
	speaker.pitch_scale = sound.pitch
	speaker.volume_db = sound.get("volume_db", 0.0)
	speaker.play()


# A sheet played once, or the placeholder star growing and fading.
func _spawn_burst(spec: Dictionary, point: Vector2, at_scale := 1.0) -> void:
	if spec.has("texture"):
		var burst := Sprite2D.new()
		burst.texture = load(spec.texture)
		burst.hframes = spec.hframes
		burst.centered = false
		burst.offset = -spec.pivot
		burst.scale = Vector2.ONE * spec.scale * at_scale
		fx_layer.add_child(burst)
		burst.global_position = point.round()
		var frames := burst.create_tween()
		for i in spec.frame_times.size():
			frames.tween_callback(burst.set_frame.bind(i))
			frames.tween_interval(spec.frame_times[i])
		frames.tween_callback(burst.queue_free)
		return
	var star := Polygon2D.new()
	var polygon := PackedVector2Array()
	var corners: int = spec.points * 2
	for i in corners:
		var radius: float = spec.outer_radius if i % 2 == 0 else spec.inner_radius
		polygon.append(Vector2.from_angle(TAU * i / corners - PI / 2.0) * radius)
	star.polygon = polygon
	star.color = spec.color
	star.scale = Vector2.ONE * spec.from_scale * at_scale
	fx_layer.add_child(star)
	star.global_position = point.round()
	var grow := star.create_tween().set_parallel()
	grow.tween_property(star, "scale", Vector2.ONE * spec.to_scale * at_scale, spec.time)
	grow.tween_property(star, "modulate:a", 0.0, spec.time)
	grow.chain().tween_callback(star.queue_free)
