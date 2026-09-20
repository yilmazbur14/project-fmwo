extends CharacterBody2D

const HitStop := preload("res://Scripts/HitStop.gd")
const FightOutro := preload("res://Scripts/FightOutro.gd")
const BossHealthBarUI := preload("res://Scripts/BossHealthBarUI.gd")
# What he says once the fight is over, under player_won and player_lost.
const OUTRO_DIALOGUE := "res://Dialogue/MasonOutro.dialogue"
# This fight's place in the order; GameProgress decides what follows it.
const FIGHT_SCENE := "res://Scenes/Bosses/MasonBossFightScene.tscn"

#CONSTANTS
@export var max_health := 10
var boss_health := max_health
const PHASE_TWO_RATIO := 0.5
const MAX_HITS_PER_WINDOW := 3
const PHANTOM_HIT_WINDOW := 0.5
# The finisher's daze stars circle here, from his origin: about 34 px over his hat.
const DAZE_ANCHOR_OFFSET := Vector2(0, -124)

#UI (BossHealthBarUI builds it at runtime)
var health_bar: Control

@onready var sprite = $Sprite2D
@onready var animation_player: AnimationPlayer = $AnimationPlayer
@onready var hurtbox: Area2D = $Hurtbox
@onready var state_machine = $StateManager

#MUSIC
# His theme is the user's own track, kept in Assets/Audio/SFX/local/, which is gitignored: those rights
# aren't ours and the repo is public. A fresh clone doesn't have it, so it falls back to the shared boss
# theme and the fight still has music.
const MUSIC_LOCAL := "res://Assets/Audio/SFX/local/mason_theme_local.mp3"
# "Snack Run", written for this fight - see art_source/music/mason_theme.rb. One 16-bar cycle cut
# to the beat. This is what a fresh clone hears, and it is ours, unlike the local reference above.
const MUSIC_FALLBACK := "res://Assets/Audio/Music/mason_theme.wav"
# Measured through a capture bus (art_source/mason_tuning/measure_mason_theme.gd), not guessed: the track
# runs -14.5 to -15.8 dBFS RMS with peaks near -1. At -7 dB it sits around -22, where Carter's fight
# settled for music under constant sound and about 5 dB under where the placeholder sat, so the squat
# before every poo line, Carter's slams and the nugget and bomb impacts (the same hit at -10 dB) stay on
# top of it. The fallback keeps the level it has always had.
const MUSIC_LOCAL_DB := -7.0
const MUSIC_FALLBACK_DB := -7.0
# The track fades out over its last five seconds and ends in silence: looped end to start, that is a
# six-second hole on every pass, and this fight often runs past its 1:46. So it loops early instead. It is
# 115 BPM on a steady grid from its first beat (Godot strips the MP3's encoder delay, so that is the
# start of the file), and after 192 beats, the 48th bar line and the last before the fade (100.17 s), the
# stream goes straight back to the top. Found and checked offline by
# art_source/mason_tuning/loop_mason_theme.gd. Only for the file it was measured on: a different track
# dropped in at this path loops end to start rather than being cut at this one's bar line.
const MUSIC_LOCAL_BPM := 115.0
const MUSIC_LOCAL_LOOP_BEATS := 192
const MUSIC_LOCAL_LENGTH := 106.43

#AUDIO
@onready var music_player: AudioStreamPlayer = $MusicPlayer
@onready var hit_sfx_player: AudioStreamPlayer = $HitSfxPlayer
@onready var victory_sfx_player: AudioStreamPlayer = $VictorySfxPlayer
@onready var squat_sfx_player: AudioStreamPlayer = $SquatSfxPlayer
@onready var phone_sfx_player: AudioStreamPlayer = $PhoneSfxPlayer
@onready var downed_sfx_player: AudioStreamPlayer = $DownedSfxPlayer
@onready var toss_sfx_player: AudioStreamPlayer = $TossSfxPlayer

var phase_two := false
var defeated := false
var hits_this_window := 0
# One finisher daze per eat window; Eat clears it.
var daze_used := false
# Runs the stagger after a landed finisher, straight into the next cycle.
var finisher_stagger_timer: Timer

var fight_clock := 0.0
var last_contact_hit_time := -INF

var sprite_base_position: Vector2


func _ready() -> void:
	add_to_group(FightOutro.BOSS_GROUP)
	hurtbox.area_entered.connect(_on_hurtbox_entered)

	finisher_stagger_timer = Timer.new()
	finisher_stagger_timer.name = "FinisherStaggerTimer"
	finisher_stagger_timer.one_shot = true
	finisher_stagger_timer.timeout.connect(state_machine.start_cycle)
	add_child(finisher_stagger_timer)

	sprite_base_position = sprite.position
	_build_hud()

	# Loaded here rather than when the fight starts, so the first play doesn't hitch.
	var own_theme := ResourceLoader.exists(MUSIC_LOCAL)
	music_player.stream = load(MUSIC_LOCAL if own_theme else MUSIC_FALLBACK)
	music_player.volume_db = MUSIC_LOCAL_DB if own_theme else MUSIC_FALLBACK_DB
	if music_player.stream is AudioStreamWAV:
		# Our own theme: a WAV cut to one whole cycle, so it loops by sample range and needs none
		# of the beat bookkeeping below - the seam is the bar line.
		music_player.stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
		music_player.stream.loop_begin = 0
		music_player.stream.loop_end = int(music_player.stream.get_length() * music_player.stream.mix_rate)
	elif music_player.stream:
		music_player.stream.loop = true
		# Only on his local reference track, which is the one with a measured grid to line up to.
		if own_theme and absf(music_player.stream.get_length() - MUSIC_LOCAL_LENGTH) < 0.1:
			music_player.stream.bpm = MUSIC_LOCAL_BPM
			music_player.stream.beat_count = MUSIC_LOCAL_LOOP_BEATS
	hit_sfx_player.stream = load("res://Assets/Audio/SFX/hit_impact.ogg")
	victory_sfx_player.stream = load("res://Assets/Audio/SFX/victory_fanfare.ogg")
	squat_sfx_player.stream = load("res://Assets/Audio/SFX/wrestler_charge.ogg")
	phone_sfx_player.stream = load("res://Assets/Audio/SFX/laser_charge.ogg")
	downed_sfx_player.stream = load("res://Assets/Audio/SFX/downed_stinger.ogg")
	toss_sfx_player.stream = load("res://Assets/Audio/SFX/whirlwind_whoosh.ogg")


func start_music() -> void:
	if music_player and not music_player.playing:
		music_player.play()


func get_health_ratio() -> float:
	return float(boss_health) / float(max_health)


func _physics_process(delta: float) -> void:
	fight_clock += delta


func _on_hurtbox_entered(area: Area2D) -> void:
	if boss_health <= 0 or not area.is_in_group("player attack"):
		return

	# A punch that makes contact the moment its hitbox switches on is reported again, as a
	# phantom, when PlayerPunching switches the hitbox off ~0.4s later. A genuine next punch
	# only reports from a switched-off hitbox at the end of its own swing, two full swings
	# (~0.65s) after that contact. Game time, so hit-stop and frame hitches can't stretch the gap.
	if not area.monitorable and fight_clock - last_contact_hit_time < PHANTOM_HIT_WINDOW:
		return
	if area.get_parent().combo.resolve_punch(self) > 0 and area.monitorable:
		last_contact_hit_time = fight_clock


func take_punch(amount: int) -> int:
	if hits_this_window >= MAX_HITS_PER_WINDOW:
		return 0
	var dealt := _apply_damage(amount)
	if dealt > 0:
		hits_this_window += 1
	return dealt


# Phase two can't be skipped: until a phase-two cycle starts, Mason can't drop past the threshold.
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
	_refresh_health_bar()
	_hit_feedback()
	hit_sfx_player.play()

	if state_machine.current_state.name == "Eat":
		animation_player.play("hit")
		animation_player.queue("eat")

	if not phase_two and get_health_ratio() <= PHASE_TWO_RATIO:
		phase_two = true

	if boss_health <= 0:
		# area_entered fires mid physics flush; deferring keeps the state Exit/Enter
		# code the defeat sequence runs from having to be flush-safe.
		call_deferred("_on_defeated")
	return dealt


# The player's finisher (PlayerFinisher). Only the eat window can be dazed, and only while the
# finisher can still take health past the phase floor.
func can_be_dazed() -> bool:
	return not defeated and boss_health > _lowest_health() and not daze_used and state_machine.current_state == state_machine.states.get("Eat")


func enter_daze() -> void:
	daze_used = true


func exit_daze(_finisher_landed: bool) -> void:
	pass


func end_recovery(stagger_time: float) -> bool:
	if defeated or boss_health <= 0:
		return false
	state_machine.eat_timer.stop()
	state_machine.on_child_transition(state_machine.current_state, "Idle")
	# Held on the recoil frame through the stagger instead of the idle loop Idle starts.
	animation_player.play("hit")
	finisher_stagger_timer.start(stagger_time)
	return true


# Past the hit cap, which the combo that led to it has used up, but not past the phase floor.
func take_finisher(amount: int) -> int:
	return _apply_damage(amount)


func get_max_health() -> int:
	return max_health


func get_daze_anchor() -> Vector2:
	return global_position + DAZE_ANCHOR_OFFSET


func get_finisher_hurtbox() -> Area2D:
	return hurtbox


func _on_defeated() -> void:
	finisher_stagger_timer.stop()
	defeated = true
	hurtbox.set_deferred("monitoring", false)
	hurtbox.set_deferred("monitorable", false)
	state_machine.enter_defeated()

	# Any bomb, Carter or driver that outlives Mason could still hurt the player after the win.
	for hazard in get_tree().get_nodes_in_group("mason_hazard"):
		hazard.queue_free()

	if music_player.playing:
		music_player.stop()
	victory_sfx_player.play()
	get_tree().call_group("arena_crowd", "cheer", 2.0)
	GameProgress.next_boss_scene = GameProgress.next_fight_after(FIGHT_SCENE)
	FightOutro.finish_fight(get_tree(), true)


# Called by FightOutro when the player loses.
func on_player_defeated() -> void:
	finisher_stagger_timer.stop()
	state_machine.enter_player_defeated()
	# As after a win, nothing he's sent out may stay live.
	for hazard in get_tree().get_nodes_in_group("mason_hazard"):
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
		"rows": [{"key": &"mason", "max": max_health, "value": boss_health}],
		"plate": &"mason",
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
