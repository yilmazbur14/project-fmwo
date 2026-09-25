extends CharacterBody2D

const HitStop := preload("res://Scripts/HitStop.gd")
const FightOutro := preload("res://Scripts/FightOutro.gd")
const BossHealthBarUI := preload("res://Scripts/BossHealthBarUI.gd")
const BossBreakGauge := preload("res://Scripts/BossBreakGauge.gd")
const BreakGaugeUI := preload("res://Scripts/BreakGaugeUI.gd")
const MasonArtLayout := preload("res://Scripts/MasonArtLayout.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
# What he says once the fight is over, under player_won and player_lost.
const OUTRO_DIALOGUE := "res://Dialogue/MasonOutro.dialogue"
# This fight's place in the order; GameProgress decides what follows it.
const FIGHT_SCENE := "res://Scenes/Bosses/MasonBossFightScene.tscn"

#CONSTANTS
# The tiered finisher's uppercuts each take a share of this, so it is what decides whether a juggle is
# a finisher or an execute. At 48 the three tiers are worth 7, 12 and 19, a supercharged third 24, and
# a 3-punch eat window 4.
@export var max_health := 48
var boss_health := max_health
const PHASE_TWO_RATIO := 0.5
const MAX_HITS_PER_WINDOW := 3
# Each opening takes the damage of a clean chain of MAX_HITS_PER_WINDOW punches (PunchAllowance).
const PunchAllowance := preload("res://Scripts/PunchAllowance.gd")
const PHANTOM_HIT_WINDOW := 0.5
# The finisher's daze stars circle here, from his origin: about 34 px over his hat.
const DAZE_ANCHOR_OFFSET := Vector2(0, -124)

#BREAK GAUGE (BossBreakGauge)
# Not Eric's numbers: his parries arrive in bursts and his damage is a field the player threads rather
# than a read they fluffed, so a parry is worth less and a hit costs less. The guard break is held at
# 1.75x a hit and the grab parry at 1.4x a parry, as Eric's are, and `broken_time` is per-phase, the
# shape the rest of his pacing already uses.
# Measured, not reasoned: art_source/mason_tuning/measure_mason_v2.gd run=parry and run=ceiling. A
# parrying bot breaks him twice, on cycles 1 and 3, and the fight ends in 3 cycles (65 s); one that
# only gets the elbow drops to read (ceiling) breaks him once and finishes with the gauge at 58 of 100.
# So: one or two Breaks a fight. A point higher on parry_gain and the second lands in cycle 2 and ends
# the fight there, at 2 cycles, which is under the pacing this fight is meant to have.
const BREAK := {
	"parry_gain": 12.0,
	"grab_parry_gain": 17.0,
	"hit_loss": 10.0,
	"guard_break_loss": 18.0,
	"broken_time": [3.0, 2.6],
}
# The attacks this fight owns, for the gauge. Deliberately a list rather than a prefix test: Carter's
# elbow drop is Mason's attack and carries no mason_ prefix.
const ATTACK_IDS: Array[StringName] = [&"mason_poo_blast", &"mason_poo_contact", &"mason_nugget", &"carter_elbow_drop"]

#UI (BossHealthBarUI builds it at runtime)
var health_bar: Control
var hud_layer: CanvasLayer
var break_gauge: Node
var break_sting_players: Array[AudioStreamPlayer] = []

@onready var sprite = $Sprite2D
@onready var animation_player: AnimationPlayer = $AnimationPlayer
@onready var hurtbox: Area2D = $Hurtbox
# His body while he lays a poo line (set_contact_live). Its own area rather than the Hurtbox, which is
# only on in his punish windows and is what the player's punches look for.
@onready var contact_hitbox: Area2D = $ContactHitbox
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
var punches := PunchAllowance.new()
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
	contact_hitbox.set_meta(HitInfo.META_ATTACK, &"mason_poo_contact")

	finisher_stagger_timer = Timer.new()
	finisher_stagger_timer.name = "FinisherStaggerTimer"
	finisher_stagger_timer.one_shot = true
	finisher_stagger_timer.timeout.connect(state_machine.start_cycle)
	add_child(finisher_stagger_timer)

	sprite_base_position = sprite.position
	var player := get_tree().current_scene.get_node_or_null(FightOutro.PLAYER_PATH)
	if player:
		_add_break_gauge(player)
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


func _add_break_gauge(player: Node) -> void:
	break_gauge = BossBreakGauge.new()
	break_gauge.name = "BreakGauge"
	break_gauge.boss = self
	break_gauge.player = player
	break_gauge.owns_attack = func(id: StringName) -> bool: return ATTACK_IDS.has(id)
	var strong: Array[StringName] = [&"carter_elbow_drop"]
	break_gauge.strong_parry_ids = strong
	break_gauge.parry_gain = BREAK.parry_gain
	break_gauge.grab_parry_gain = BREAK.grab_parry_gain
	break_gauge.hit_loss = BREAK.hit_loss
	break_gauge.guard_break_loss = BREAK.guard_break_loss
	add_child(break_gauge)
	break_gauge.broke.connect(_on_break)
	for sting in MasonArtLayout.BREAK_STING_SFX:
		var sfx := AudioStreamPlayer.new()
		sfx.stream = load(sting.stream)
		sfx.pitch_scale = sting.pitch
		sfx.volume_db = sting.volume_db
		add_child(sfx)
		break_sting_players.append(sfx)


# The gauge fills inside physics flushes and his own physics steps, where his states can't switch.
func _on_break() -> void:
	state_machine.enter_broken.call_deferred()


func is_broken() -> bool:
	return state_machine.current_state == state_machine.states.get("Broken")


func is_juggled() -> bool:
	return state_machine.current_state == state_machine.states.get("Juggled")


# Down from a Break or a juggle, until he is back on his feet: the gauge waits for this.
func is_down() -> bool:
	return is_broken() or is_juggled()


func play_break_sting() -> void:
	for sfx in break_sting_players:
		sfx.play()


# White over the whole view, fading in real time: it plays out through the Break's hit-stop.
func flash_hud(color: Color, time: float) -> void:
	var flash := ColorRect.new()
	flash.color = color
	flash.mouse_filter = Control.MOUSE_FILTER_IGNORE
	flash.set_anchors_preset(Control.PRESET_FULL_RECT)
	hud_layer.add_child(flash)
	var fade := flash.create_tween().set_ignore_time_scale(true)
	fade.tween_property(flash, "modulate:a", 0.0, time)
	fade.tween_callback(flash.queue_free)


# Global position of the centre of a pixel on Mason's sheet frames.
func frame_point(pixel: Vector2) -> Vector2:
	return to_global(MasonArtLayout.frame_local(pixel + Vector2(0.5, 0.5)))


# The same for a pixel on his juggle sheet, whose frames are bigger than his main sheet's and hang
# lower to keep his feet on the same ground line.
func juggle_point(pixel: Vector2) -> Vector2:
	return to_global(MasonArtLayout.juggle_local(pixel + Vector2(0.5, 0.5)))


func start_music() -> void:
	if music_player and not music_player.playing:
		music_player.play()


func get_health_ratio() -> float:
	return float(boss_health) / float(max_health)


func _physics_process(delta: float) -> void:
	fight_clock += delta
	_touch_player()


# MasonPooSquat and MasonWaddle switch it on as they start and off as they end, so whatever ends a line
# - its last step, a Break, either side winning - leaves through one of their Exit()s and ends it too.
func set_contact_live(live: bool) -> void:
	if live:
		contact_hitbox.add_to_group("enemy projectile")
	else:
		contact_hitbox.remove_from_group("enemy projectile")


# The group only reports a player walking into him. One already in him as a line starts, or still in
# him as the last hit's i-frames run out, has to be looked for, and the i-frames space those hits out.
func _touch_player() -> void:
	if not contact_hitbox.is_in_group("enemy projectile"):
		return
	var player: Node2D = state_machine.get_player()
	if player and player.hurtBox.overlaps_area(contact_hitbox):
		player.receive_hit(HitInfo.from_area(contact_hitbox))


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
	var allowed := punches.allow(amount, hits_this_window, MAX_HITS_PER_WINDOW)
	if allowed <= 0:
		return 0
	var dealt := _apply_damage(allowed)
	if dealt > 0:
		hits_this_window += 1
		punches.spend(dealt)
	return dealt


# Phase two can't be skipped: until Mason crosses the threshold, he can't drop past it. Keyed off
# phase_two, which _apply_damage sets the instant the threshold is crossed, and NOT off the cycle's
# phase, which only catches up at the next start_cycle(): a juggle that reaches the floor mid-flight
# would have its second and third uppercuts deal a literal zero.
# So a supercharged third uppercut from at or under the threshold can now end the fight without a
# phase-two cycle ever running. That is the earned finish it looks like, and is meant.
func _lowest_health() -> int:
	if phase_two:
		return 0
	return floori(max_health * PHASE_TWO_RATIO)


# A hit that would carry past the threshold is cut down to reach it exactly.
func _apply_damage(amount: int, pitch := 1.0) -> int:
	var dealt := mini(amount, boss_health - _lowest_health())
	if dealt <= 0:
		return 0

	boss_health -= dealt
	_refresh_health_bar()
	_hit_feedback()
	hit_sfx_player.pitch_scale = pitch
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


# The player's finisher (PlayerFinisher). Both of his punish windows, and only while the finisher can
# still take health past the phase floor: the eat window he earns by landing hits, and the Break he
# earns by reading the mat.
func can_be_dazed() -> bool:
	if defeated or boss_health <= _lowest_health() or daze_used:
		return false
	var state = state_machine.current_state
	return state == state_machine.states.get("Eat") or state == state_machine.states.get("Broken")


# The three-bar mash and the juggle are the Break's payout alone. The eat window pays the plain
# single-bar finisher. That split is arithmetic, not taste: the juggle's shares are proportional to
# max health, so with it on both windows the fight ends inside two cycles however much health he has.
func can_be_juggled() -> bool:
	return not defeated and boss_health > 0 and is_broken()


# The finisher draws its own daze stars over Broken's.
func enter_daze() -> void:
	daze_used = true
	if is_broken():
		state_machine.current_state.show_stars(false)


func exit_daze(finisher_landed: bool) -> void:
	if is_broken() and not finisher_landed:
		state_machine.current_state.show_stars(true)


func end_recovery(stagger_time: float) -> bool:
	if defeated or boss_health <= 0:
		return false
	# Crashed from a juggle, he lies a beat before he gets up.
	if is_juggled():
		state_machine.current_state.recover(stagger_time)
		return true
	if is_broken():
		state_machine.end_break(stagger_time)
		return true
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


# The tiered finisher's juggle (PlayerFinisher).
func begin_juggle() -> void:
	state_machine.enter_juggled()


func juggle_lift(px: float) -> void:
	if is_juggled():
		state_machine.current_state.lift(px)


func juggle_pose(pose: StringName, crater := false) -> void:
	if is_juggled():
		state_machine.current_state.pose(pose, crater)


# The most he can be lifted and still be seen whole: his top stays inside the arena, which is as far up
# as the view can go. The height is measured on the juggle sheet's own rows; the ground line is his
# either way, because both sheets stand him on it.
func juggle_headroom() -> float:
	var art := MasonArtLayout.juggle()
	var ground_y: float = frame_point(Vector2(0, MasonArtLayout.FEET_ROW)).y
	var height: float = (art.feet.y - art.top_row) * MasonArtLayout.SCALE
	return ground_y - height - MasonArtLayout.JUGGLE_TOP_MARGIN


# Past the hit cap, as take_finisher, with his hit sound pitched up a step each uppercut.
func take_juggle_hit(amount: int, pitch: float) -> int:
	return _apply_damage(amount, pitch)


func get_juggle_point() -> Vector2:
	return state_machine.states["Juggled"].air_point()


# A juggle that kills him ends with him still in the air: the outro's first line would otherwise open
# over a boss mid-fall. Holding it until he has landed is the same fix EricScript makes.
func outro_line_delay(_player_won: bool) -> float:
	if state_machine.current_state == state_machine.states.get("Juggled"):
		return MasonArtLayout.JUGGLE_OUTRO_DELAY
	return 0.0


# The uppercut shoves him back (PlayerFinisher). He has to move for real: a boss left to the fallback
# rocks back on sprite.offset, which is the same offset a juggle's lift rewrites every frame.
func knock_back(push: Vector2, time: float) -> void:
	var target := Vector2(
		clampf(global_position.x + push.x, state_machine.LINE_X_LEFT, state_machine.LINE_X_RIGHT),
		clampf(global_position.y + push.y, state_machine.WALK_Y_MIN, state_machine.WALK_Y_MAX))
	var player := get_tree().current_scene.get_node_or_null(FightOutro.PLAYER_PATH)
	# The walls must never shove him back onto the player.
	if player and target.distance_to(player.global_position) < global_position.distance_to(player.global_position):
		return
	# His next line is laid from the rest point, so it moves with him or he teleports back as it starts.
	state_machine.rest_point = target + state_machine.BOMB_SPAWN_OFFSET
	create_tween().tween_property(self, "global_position", target, time).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)


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
	hud_layer = CanvasLayer.new()
	add_child(hud_layer)

	health_bar = BossHealthBarUI.create({
		"rows": [{"key": &"mason", "max": max_health, "value": boss_health}],
		"plate": &"mason",
		"text": GameProgress.boss_name(FIGHT_SCENE),
	})
	hud_layer.add_child(health_bar)

	if break_gauge:
		var gauge_bar := BreakGaugeUI.new()
		gauge_bar.gauge = break_gauge
		hud_layer.add_child(gauge_bar)
		gauge_bar.position = health_bar.break_gauge_anchor()


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
