extends CharacterBody2D

const HitStop := preload("res://Scripts/HitStop.gd")
const FightOutro := preload("res://Scripts/FightOutro.gd")
const BossHealthBarUI := preload("res://Scripts/BossHealthBarUI.gd")
# What he says once the fight is over, under player_won and player_lost.
const OUTRO_DIALOGUE := "res://Dialogue/JordanOutro.dialogue"
# This fight's place in the order; as the last one, GameProgress finds nothing after it.
const FIGHT_SCENE := "res://Scenes/Bosses/JordanBossFightScene.tscn"

#CONSTANTS
# Phase 1's health.
@export var max_health := 12
var boss_health := max_health
const MAX_HITS_PER_WINDOW := 3
const PHANTOM_HIT_WINDOW := 0.5
# Blasts from punched figures that can hurt him per summon, apart from the taunt's punches.
const MAX_EXPLOSION_HITS_PER_CYCLE := 2
# A blast that hurts him holds up what he's doing for this long, while he leans back and recovers.
const STAGGER_TIME := 0.4
const STAGGER_LEAN := -0.25
const STAGGER_LEAN_TIME := 0.1
# Where the finisher's daze stars circle, from his origin: just above his cap.
const DAZE_ANCHOR_OFFSET := Vector2(0, -92)

#UI (BossHealthBarUI builds it at runtime)
var health_bar: Control

@onready var sprite = $Sprite2D
@onready var animation_player: AnimationPlayer = $AnimationPlayer
@onready var hurtbox: Area2D = $Hurtbox
@onready var state_machine = $StateManager

#AUDIO
# His own theme. Same level as Eric's and the pair's, so the ladder does not jump between fights.
const THEME := "res://Assets/Audio/Music/jordan_theme.wav"
const THEME_DB := -7.0

@onready var music_player: AudioStreamPlayer = $MusicPlayer
@onready var hit_sfx_player: AudioStreamPlayer = $HitSfxPlayer
@onready var victory_sfx_player: AudioStreamPlayer = $VictorySfxPlayer
@onready var summon_sfx_player: AudioStreamPlayer = $SummonSfxPlayer
@onready var taunt_sfx_player: AudioStreamPlayer = $TauntSfxPlayer

var defeated := false
var hits_this_window := 0
var explosion_hits_this_cycle := 0
# The player's finisher can daze him once per taunt.
var daze_used := false

var fight_clock := 0.0
var last_contact_hit_time := -INF

var sprite_base_position: Vector2
var stagger_tween: Tween


func _ready() -> void:
	add_to_group(FightOutro.BOSS_GROUP)
	hurtbox.area_entered.connect(_on_hurtbox_entered)

	sprite_base_position = sprite.position
	_build_hud()

	# Placeholder: Jordan has no theme of his own yet.
	# "The Last Name on the List", written for this fight - see art_source/music/jordan_theme.rb.
	# One 16-bar cycle cut to the beat, so LOOP_FORWARD runs it end to end with no seam.
	music_player.stream = load(THEME)
	music_player.volume_db = THEME_DB
	if music_player.stream is AudioStreamWAV:
		music_player.stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
		music_player.stream.loop_begin = 0
		music_player.stream.loop_end = int(music_player.stream.get_length() * music_player.stream.mix_rate)
	elif music_player.stream and "loop" in music_player.stream:
		music_player.stream.loop = true
	hit_sfx_player.stream = load("res://Assets/Audio/SFX/hit_impact.ogg")
	victory_sfx_player.stream = load("res://Assets/Audio/SFX/victory_fanfare.ogg")
	summon_sfx_player.stream = load("res://Assets/Audio/SFX/whirlwind_whoosh.ogg")
	taunt_sfx_player.stream = load("res://Assets/Audio/SFX/downed_stinger.ogg")


func start_music() -> void:
	if music_player and not music_player.playing:
		music_player.play()


func get_health_ratio() -> float:
	return float(boss_health) / float(max_health)


func hurtbox_rect() -> Rect2:
	var shape: CollisionShape2D = hurtbox.get_node("CollisionShape2D")
	return shape.global_transform * shape.shape.get_rect()


func _physics_process(delta: float) -> void:
	fight_clock += delta


func _on_hurtbox_entered(area: Area2D) -> void:
	if boss_health <= 0 or not area.is_in_group("player attack"):
		return

	# Same phantom-hit filter as Mason: a punch that connects as its hitbox switches on is reported
	# again when PlayerPunching switches the hitbox off, which would eat the hit cap.
	if not area.monitorable and fight_clock - last_contact_hit_time < PHANTOM_HIT_WINDOW:
		return
	if area.get_parent().combo.resolve_punch(self) > 0 and area.monitorable:
		last_contact_hit_time = fight_clock


# Punches only land while he taunts.
func take_punch(amount: int) -> int:
	if boss_health <= 0 or not state_machine.is_taunting() or hits_this_window >= MAX_HITS_PER_WINDOW:
		return 0
	hits_this_window += 1
	return _take_damage(amount)


# A punched figure's blast, which lands whatever he's doing.
func take_explosion_hit(amount: int) -> int:
	if boss_health <= 0 or explosion_hits_this_cycle >= MAX_EXPLOSION_HITS_PER_CYCLE:
		return 0
	explosion_hits_this_cycle += 1
	var dealt := _take_damage(amount)
	if dealt > 0:
		state_machine.get_player().hype.reward_explosion_redirect()
	get_tree().call_group("arena_crowd", "cheer", 1.5)
	if boss_health > 0:
		_stagger()
	return dealt


# The player's finisher (see PlayerFinisher): a charged combo punch during the taunt dazes him, and the
# uppercut that follows ends the taunt. Phase 1 has no health floor for its damage to stop at.
func can_be_dazed() -> bool:
	return not defeated and boss_health > 0 and not daze_used and state_machine.is_taunting()


func enter_daze() -> void:
	daze_used = true


func exit_daze(_finisher_landed: bool) -> void:
	pass


# Not held to the taunt's hit cap.
func take_finisher(amount: int) -> int:
	if boss_health <= 0:
		return 0
	return _take_damage(amount)


# He stops taunting and idles for `stagger_time` in place of his rest, then summons again once the swarm is over.
func end_recovery(stagger_time: float) -> bool:
	if boss_health <= 0:
		return false
	state_machine.end_taunt(stagger_time)
	return true


func get_max_health() -> int:
	return max_health


func get_daze_anchor() -> Vector2:
	return global_position + DAZE_ANCHOR_OFFSET


func get_finisher_hurtbox() -> Area2D:
	return hurtbox


func _take_damage(amount: int) -> int:
	var dealt := mini(amount, boss_health)
	boss_health -= dealt
	_refresh_health_bar()
	_hit_feedback()
	hit_sfx_player.play()

	# Runs once: at 0 the take_ functions turn every hit away, even a second blast on the same frame.
	# area_entered fires mid physics flush; deferring keeps the state Exit/Enter code the defeat
	# sequence runs from having to be flush-safe.
	if boss_health <= 0:
		call_deferred("_on_defeated")
	return dealt


func _stagger() -> void:
	state_machine.stagger(STAGGER_TIME)
	if stagger_tween:
		stagger_tween.kill()
	stagger_tween = create_tween()
	stagger_tween.tween_property(sprite, "rotation", STAGGER_LEAN, STAGGER_LEAN_TIME).set_ease(Tween.EASE_OUT)
	stagger_tween.tween_property(sprite, "rotation", 0.0, STAGGER_TIME - STAGGER_LEAN_TIME).set_ease(Tween.EASE_IN_OUT)


func _on_defeated() -> void:
	defeated = true
	hurtbox.set_deferred("monitoring", false)
	hurtbox.set_deferred("monitorable", false)
	# The defeat animation turns the sprite over itself.
	if stagger_tween:
		stagger_tween.kill()
	sprite.rotation = 0.0
	state_machine.enter_defeated()
	_clear_hazards()

	if music_player.playing:
		music_player.stop()
	victory_sfx_player.play()
	get_tree().call_group("arena_crowd", "cheer", 2.0)
	GameProgress.next_boss_scene = GameProgress.next_fight_after(FIGHT_SCENE)
	FightOutro.finish_fight(get_tree(), true)


# Called by FightOutro when the player loses.
func on_player_defeated() -> void:
	state_machine.enter_player_defeated()
	_clear_hazards()


# Whoever won, nothing he's summoned may stay live: a figure that outlives the fight could still hurt the player.
func _clear_hazards() -> void:
	for hazard in get_tree().get_nodes_in_group(state_machine.HAZARD_GROUP):
		hazard.queue_free()


# The bar goes hot in two steps: caution under 0.6 of his health, then the last third.
func _refresh_health_bar() -> void:
	if not health_bar:
		return
	health_bar.set_value(0, boss_health)
	var ratio := get_health_ratio()
	var heat := 0.0
	if ratio <= 0.34:
		heat = 1.0
	elif ratio <= 0.6:
		heat = 0.5
	health_bar.set_heat(0, heat)


func _build_hud() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)

	health_bar = BossHealthBarUI.create({
		"rows": [{"key": &"jordan", "max": max_health, "value": boss_health}],
		"plate": &"jordan",
		"text": GameProgress.boss_name(FIGHT_SCENE),
	})
	layer.add_child(health_bar)


func _hit_feedback() -> void:
	if not sprite:
		return

	sprite.modulate = Color(3, 3, 3)
	var flash_tween = create_tween()
	flash_tween.tween_property(sprite, "modulate", Color(1, 1, 1), 0.15)

	var shake_tween = create_tween()
	for i in 4:
		var offset = Vector2(randf_range(-5, 5), randf_range(-5, 5))
		shake_tween.tween_property(sprite, "position", sprite_base_position + offset, 0.025)
	shake_tween.tween_property(sprite, "position", sprite_base_position, 0.025)

	HitStop.freeze(get_tree(), 0.06)
