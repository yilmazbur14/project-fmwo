extends Node2D

#REFERENCES
var Projectile = preload("res://Scenes/Bosses/BossProjectileScene.tscn")
const HitStop := preload("res://Scripts/HitStop.gd")
const EricArtLayout := preload("res://Scripts/EricArtLayout.gd")
const EricPacing := preload("res://Scripts/EricPacing.gd")
const BossBreakGauge := preload("res://Scripts/BossBreakGauge.gd")
const PunchAllowance := preload("res://Scripts/PunchAllowance.gd")
const BreakGaugeUI := preload("res://Scripts/BreakGaugeUI.gd")
const BossHealthBarUI := preload("res://Scripts/BossHealthBarUI.gd")
const FightOutro := preload("res://Scripts/FightOutro.gd")
# What he says once the fight is over, under player_won and player_lost.
const OUTRO_DIALOGUE := "res://Dialogue/EricOutro.dialogue"
# This fight's place in the order; GameProgress decides what follows it.
const FIGHT_SCENE := "res://Scenes/Bosses/EricBossFightScene.tscn"

#CONSTANTS
# Where an uppercut may leave him: his body box inside the ring's walls (ArenaScene's
# wallBoundaries), with a margin so he never leans through a rope.
const KNOCKBACK_AREA := Rect2(240, 200, 1440, 570)
@export var max_health := 24
var boss_health := max_health

#THE BREAK GAUGE (BossBreakGauge, V2 only)
# His own numbers since the 2026-10-04 mash, which made a Break's juggle pay 35% of his health at the
# model's mash rate instead of 15%: a Break now takes about two and a half times the reads it did (the
# gauge's defaults, which he was first tuned on, were parry 15, red grab 20, reflect 35, perfect dodge 12,
# punches 8 and 14). The sword flung back keeps the biggest share, since it no longer fires an uppercut of
# its own (EricPacing's reflect_auto_uppercut). The drains are the defaults, so a hit sets a Break back
# further than before. Measured with the experienced-player model bot (tuning round 2026-10-04).
const BREAK := {
	"max_value": 100.0,
	"parry_gain": 5.0,
	"grab_parry_gain": 7.0,
	"reflect_gain": 18.0,
	"perfect_dodge_gain": 4.0,
	"punch_gain": 2.0,
	"charged_punch_gain": 5.0,
	"hit_loss": 20.0,
	"guard_break_loss": 35.0,
	"unlock_delay": 3.0,
}

#UI (BossHealthBarUI builds it at runtime)
var health_bar: Control

@onready var animationPlayer = $AnimationPlayer
@onready var sprite = $Sprite2D
@onready var state_machine = $StateManager
@export var post_dialogue_pre_fight_timer: Timer

#AUDIO
# Eric's theme. -7 dB puts its -15 dBFS master at about -22 dBFS in the fight, the level the
# other fights' music settled on, so his hits and his stingers still sit on top of it.
const THEME := "res://Assets/Audio/Music/eric_theme.wav"
const THEME_DB := -7.0

@onready var music_player: AudioStreamPlayer = $MusicPlayer
@onready var hit_sfx_player: AudioStreamPlayer = $HitSfxPlayer
@onready var victory_sfx_player: AudioStreamPlayer = $VictorySfxPlayer
@onready var downed_sfx_player: AudioStreamPlayer = $DownedSfxPlayer
var defeated := false
# One finisher daze per window (Downed, Broken, Winded, a parry stagger, the hug's stumble), each of which
# clears it as it opens.
var daze_used := false
# V2's earned punish windows - Winded at the end of a chain, a parry stagger (the sword's or the bear hug's)
# and the bear hug's stumble - take a POW's uppercut mash again (the user, 2026-10-05; the hug's, 2026-10-06).
# Off puts V2's finisher back on the Break alone. Caught in the stumble, away from the sword he planted, he
# gets up for it where it stands (EricStateMachine.enter_juggled).
@export var daze_in_windows := true
# Punches that can land while a parry has him staggered: two, or three - a whole POW, like every other window -
# while a stagger's daze is on (daze_in_windows, V2), the parried bear hug's and his own sword's alike (the user,
# 2026-10-06). window_hit_cap() says which applies.
const STAGGER_HIT_CAP := 2
const WINDOW_STAGGER_HIT_CAP := 3
var parry_stagger_hits := 0
# The parry stagger takes the damage of a clean chain of window_hit_cap() punches (PunchAllowance).
var punches := PunchAllowance.new()
# His AnimationPlayer's own process mode while the finisher holds his window on it (hold_window), or -1.
var held_animation_mode := -1
# The reworked fight's Break gauge (EricPacing V2); null in V1.
var break_gauge: Node
var hud_layer: CanvasLayer
var break_sting_players: Array[AudioStreamPlayer] = []

var sprite_base_position: Vector2

# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	add_to_group(FightOutro.BOSS_GROUP)
	var hurtBox = get_node("Hurtbox")
	hurtBox.area_entered.connect(_on_hurtbox_entered)
	_apply_art_layout()
	max_health = EricPacing.value("max_health")
	boss_health = max_health

	sprite_base_position = sprite.position
	var player := get_tree().current_scene.get_node_or_null(FightOutro.PLAYER_PATH)
	if player:
		# The dash cancellable into the guard, this fight and the training room that feeds it for
		# now (PlayerScript.dash_parry).
		player.dash_parry = true
	if player and EricPacing.is_v2():
		_add_break_gauge(player)
	_build_hud()

	# Eric's own theme, "Ride for the King": written for this fight in Sonic Pi and recorded from
	# it, so unlike the placeholder tracks it ships in the repo. One 16-bar cycle at 138 bpm cut on
	# the downbeat, with the reverb tail wrapped over the start, so it loops with no seam. It loops
	# because eric_theme.wav.import sets edit/loop_mode=2 over the whole sample: that importer enum
	# lists Detect From WAV first, so 2 is Forward and 1 would be Disabled. Deliberately nothing is
	# forced here - music_player.stream is the shared imported resource, so setting loop_mode on it
	# would leak onto everything else that loads the same stream this session. A future .ogg cut of
	# the theme needs loop=true in its own .import for the same reason.
	music_player.stream = load(THEME)
	music_player.volume_db = THEME_DB
	hit_sfx_player.stream = load("res://Assets/Audio/SFX/hit_impact.ogg")
	victory_sfx_player.stream = load("res://Assets/Audio/SFX/victory_fanfare.ogg")
	# The cue that his chain is over and the window is open, played by EricStateMachine. Left at the
	# file's own pitch: the hype meter's full cue is this same sting at 1.3, and these two must not
	# read as the same sound.
	downed_sfx_player.stream = load("res://Assets/Audio/SFX/downed_stinger.ogg")


func _add_break_gauge(player: Node) -> void:
	break_gauge = BossBreakGauge.new()
	break_gauge.name = "BreakGauge"
	break_gauge.boss = self
	break_gauge.player = player
	# What the gauge held as constants while it was his alone: every eric_ attack is his, and the red
	# bear hug is the one parry worth grab_parry_gain.
	break_gauge.owns_attack = func(id: StringName) -> bool: return str(id).begins_with("eric_")
	var strong: Array[StringName] = [&"eric_bear_hug_grab_v2"]
	break_gauge.strong_parry_ids = strong
	for key in BREAK:
		break_gauge.set(key, BREAK[key])
	add_child(break_gauge)
	break_gauge.broke.connect(_on_break)
	for sting in EricArtLayout.BREAK_STING_SFX:
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


# Down from a Break or a juggle, until he's up with his sword again.
func is_down() -> bool:
	return is_broken() or state_machine.current_state == state_machine.states.get("Juggled")


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


func start_music() -> void:
	if music_player and not music_player.playing:
		music_player.play()


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	if boss_health <= 0 and not defeated:
		defeated = true
		state_machine.enter_defeated()
		# Downed opens his hurtbox, but the fight is over: punches still on their way mustn't land.
		$Hurtbox.monitoring = false
		$Hurtbox.monitorable = false
		if music_player.playing:
			music_player.stop()
		victory_sfx_player.play()
		get_tree().call_group("arena_crowd", "cheer", 2.0)
		GameProgress.next_boss_scene = GameProgress.next_fight_after(FIGHT_SCENE)
		FightOutro.finish_fight(get_tree(), true)


# Called by FightOutro when the player loses.
func on_player_defeated() -> void:
	state_machine.enter_player_defeated()


func get_health_ratio() -> float:
	return float(boss_health) / float(max_health)


# Global position of the centre of a pixel on Eric's sheet frames.
func frame_point(pixel: Vector2) -> Vector2:
	return to_global(EricArtLayout.frame_local(pixel + Vector2(0.5, 0.5)))


func _apply_art_layout() -> void:
	scale = Vector2(EricArtLayout.SCALE, EricArtLayout.SCALE)
	sprite.hframes = EricArtLayout.SHEET_FRAMES
	sprite.position = EricArtLayout.SORT_POINT
	sprite.offset = EricArtLayout.SPRITE_OFFSET - EricArtLayout.SORT_POINT
	_fit_box($CollisionShape2D, EricArtLayout.BODY_BOX)
	_fit_box($Hurtbox/CollisionShape2D, EricArtLayout.BODY_BOX)
	_fit_box($GrabArea2D/CollisionShape2D, EricArtLayout.GRAB_BOX)
	var whirlwind: CollisionShape2D = $WhirlwindArea2D/CollisionShape2D
	whirlwind.position = EricArtLayout.frame_local(EricArtLayout.WHIRLWIND_CENTRE)
	whirlwind.scale = EricArtLayout.WHIRLWIND_RADII / whirlwind.shape.radius


func _fit_box(shape_node: CollisionShape2D, box: Rect2) -> void:
	shape_node.position = EricArtLayout.frame_local(box.get_center())
	shape_node.shape.size = box.size


func _on_hurtbox_entered(area: Area2D) -> void:
	if area.is_in_group("player attack"):
		area.get_parent().combo.resolve_punch(self)


# The punches a parry stagger takes, in a clean chain (PunchAllowance).
func window_hit_cap() -> int:
	return WINDOW_STAGGER_HIT_CAP if daze_in_windows and EricPacing.is_v2() else STAGGER_HIT_CAP


func take_punch(amount: int) -> int:
	var stagger = state_machine.states.get("ParryStaggered")
	if state_machine.current_state == stagger:
		var allowed := punches.allow(amount, parry_stagger_hits, window_hit_cap())
		if allowed <= 0:
			return 0
		parry_stagger_hits += 1
		var dealt := _take_damage(allowed)
		punches.spend(dealt)
		return dealt
	return _take_damage(amount)


func _take_damage(amount: int, pitch := 1.0) -> int:
	var dealt := mini(amount, boss_health)
	boss_health -= dealt
	print("Boss health: ", boss_health)
	_refresh_health_bar()
	_hit_feedback()
	hit_sfx_player.pitch_scale = pitch
	hit_sfx_player.play()
	return dealt


# The attacks a parry (PlayerDefense) can stagger him out of, and the state each runs in.
const PARRY_STAGGER_STATES := {
	&"eric_thrown_sword": "SwordThrow",
	&"eric_bear_hug_grab": "BearHug",
	&"eric_bear_hug_grab_v2": "BearHug",
}


func can_parry_stagger(hit: RefCounted) -> bool:
	if defeated or boss_health <= 0 or state_machine.defeated:
		return false
	var state_name: String = PARRY_STAGGER_STATES.get(hit.attack_id, "")
	return not state_name.is_empty() and state_machine.current_state == state_machine.states.get(state_name)


# Deferred from the parry, so the conditions are checked again. He picks himself up where the
# interrupted attack started from.
func parry_stagger(duration: float) -> void:
	if defeated or boss_health <= 0 or state_machine.defeated:
		return
	var state = state_machine.current_state
	if state == state_machine.states.get("SwordThrow"):
		# The parried sword flies back first: it staggers him when it reaches him, not now.
		state.reflect(duration)
	elif state == state_machine.states.get("BearHug"):
		state_machine.parry_stagger(duration, state.plant_spot)


# The player's finisher (PlayerFinisher). The Downed window, a Break until he gets up, and the stagger
# his own sword leaves him in when a parry sends it back through him: that one fires the uppercut on
# its own. A parried bear hug isn't one, its stumble is too short.
# With daze_in_windows every opening his punches land in takes the daze (the user, 2026-10-06: 3 hits always
# trigger the uppercut), the whirlwind's throw too while the sword is out of his hands (EricSwordThrow). A daze
# whose mash fizzled or whose uppercut whiffed gives it back (exit_daze): those openings have no punch cap, so a
# second POW can follow.
func can_be_dazed() -> bool:
	if defeated or boss_health <= 0 or daze_used:
		return false
	var state = state_machine.current_state
	if state == state_machine.states.get("Downed"):
		return true
	# Getting his sword back, he's up and no longer open.
	if state == state_machine.states.get("Broken"):
		return not state.retrieving
	if daze_in_windows and EricPacing.is_v2():
		if state == state_machine.states.get("Winded") or state == state_machine.states.get("ParryStaggered"):
			return true
		if state == state_machine.states.get("BearHug"):
			return state.phase == state.Phase.STUMBLE
		if state == state_machine.states.get("SwordThrow"):
			return state.from_whirlwind and get_finisher_hurtbox().monitorable
	return state == state_machine.states.get("ParryStaggered") and state.from_reflect


# The reworked fight's finisher is the tiered one: a mash of up to three bars, then a juggle.
func can_be_juggled() -> bool:
	return EricPacing.is_v2() and not defeated and boss_health > 0


# The finisher draws its own daze stars over Broken's.
func enter_daze() -> void:
	daze_used = true
	if is_broken():
		state_machine.current_state.show_stars(false)


func exit_daze(finisher_landed: bool) -> void:
	if not finisher_landed:
		daze_used = false
	if is_broken() and not finisher_landed:
		state_machine.current_state.show_stars(true)


# PlayerFinisher holds his window from a POW to the daze on his Timers and his state machine. Two of his end on his
# AnimationPlayer instead - the hug's stumble on its held frame, the whirlwind throw on the sword's catch - so in
# those it holds too.
func hold_window(on: bool) -> void:
	if not on:
		if held_animation_mode >= 0:
			animationPlayer.process_mode = held_animation_mode
		held_animation_mode = -1
		return
	var state = state_machine.current_state
	var hug = state_machine.states.get("BearHug")
	var throw = state_machine.states.get("SwordThrow")
	if (state == hug and hug.phase == hug.Phase.STUMBLE) or (state == throw and throw.from_whirlwind):
		held_animation_mode = animationPlayer.process_mode
		animationPlayer.process_mode = Node.PROCESS_MODE_DISABLED


func end_recovery(stagger_time: float) -> bool:
	if defeated or boss_health <= 0:
		return false
	# Crashed from a juggle, he lies a beat before he gets up for his sword.
	if state_machine.current_state == state_machine.states.get("Juggled"):
		state_machine.current_state.recover(stagger_time)
		return true
	# Broken with his sword knocked into the mat, he gets up and calls it back first.
	if is_broken() and state_machine.current_state.recover(stagger_time):
		return true
	state_machine.downed_state_timer.stop()
	state_machine.start_chain(stagger_time)
	# Idle raises his sword, as if he'd shrugged the uppercut off; he stays slumped through the stagger.
	animationPlayer.play("downed")
	return true


# Past the hit cap, as PlayerFinisher's contract says: that cap is for punches thrown in the window,
# and the uppercut the reflect fires is what the window is for.
func take_finisher(amount: int) -> int:
	return _take_damage(amount)


func get_max_health() -> int:
	return max_health


# The tiered finisher's juggle (PlayerFinisher): only the reworked fight has one.
func begin_juggle() -> void:
	state_machine.enter_juggled()


func juggle_lift(px: float) -> void:
	var juggled = state_machine.states["Juggled"]
	if state_machine.current_state == juggled:
		juggled.lift(px)


func juggle_pose(pose: StringName, crater := false) -> void:
	var juggled = state_machine.states["Juggled"]
	if state_machine.current_state == juggled:
		juggled.pose(pose, crater)


# The most he can be lifted and still be seen whole: his top stays inside the arena, which is as far up
# as the view can go.
func juggle_headroom() -> float:
	var ground_y: float = frame_point(Vector2(0, EricArtLayout.FEET_ROW)).y
	var height: float = (EricArtLayout.FEET_ROW - EricArtLayout.juggle().top_row) * EricArtLayout.SCALE
	return ground_y - height - EricArtLayout.JUGGLE_TOP_MARGIN


# Past the hit cap, as take_finisher, with his hit sound pitched up a step each uppercut.
func take_juggle_hit(amount: int, pitch: float) -> int:
	return _take_damage(amount, pitch)


func get_juggle_point() -> Vector2:
	return state_machine.states["Juggled"].air_point()


# A juggle that killed him lets him finish falling and crash before his line.
func outro_line_delay(_player_won: bool) -> float:
	if state_machine.current_state == state_machine.states.get("Juggled"):
		return EricArtLayout.JUGGLE_OUTRO_DELAY
	return 0.0


# The uppercut shoves him back (PlayerFinisher). Each of his attacks takes its own starting spot as it
# begins, and his hazards spawn where he is at the time, so he just fights on from where he lands.
func knock_back(push: Vector2, time: float) -> void:
	var target := (global_position + push).clamp(KNOCKBACK_AREA.position, KNOCKBACK_AREA.end)
	var player := get_tree().current_scene.get_node_or_null(FightOutro.PLAYER_PATH)
	# The ropes must never shove him back onto the player.
	if player and target.distance_to(player.global_position) < global_position.distance_to(player.global_position):
		return
	create_tween().tween_property(self, "global_position", target, time).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)


func get_daze_anchor() -> Vector2:
	if is_broken():
		return state_machine.current_state.head_point()
	return to_global(EricArtLayout.frame_local(EricArtLayout.DAZE_HEAD_PIXEL + Vector2(0.5, 0.5), sprite.flip_h))


func get_finisher_hurtbox() -> Area2D:
	return $Hurtbox


# His bar goes hot in two steps: caution as he drops past 0.6, then the rage chain's own threshold.
func _refresh_health_bar() -> void:
	if not health_bar:
		return
	health_bar.set_value(0, boss_health)
	var ratio := get_health_ratio()
	var heat := 0.0
	if ratio <= EricPacing.value("rage_chain_health_ratio"):
		heat = 1.0
	elif ratio <= 0.6:
		heat = 0.5
	health_bar.set_heat(0, heat)


func _build_hud() -> void:
	hud_layer = CanvasLayer.new()
	add_child(hud_layer)

	health_bar = BossHealthBarUI.create({
		"rows": [{"key": &"eric", "max": max_health, "value": boss_health}],
		"plate": &"eric",
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

	# Flash the boss white for a beat
	sprite.modulate = Color(3, 3, 3)
	var flash_tween = create_tween()
	flash_tween.tween_property(sprite, "modulate", Color(1, 1, 1), 0.15)

	# Small impact shake on the sprite itself (no camera needed)
	var shake_tween = create_tween()
	for i in 4:
		var offset = Vector2(randf_range(-5, 5), randf_range(-5, 5))
		shake_tween.tween_property(sprite, "position", sprite_base_position + offset, 0.025)
	shake_tween.tween_property(sprite, "position", sprite_base_position, 0.025)

	# Brief hit-stop for weight
	HitStop.freeze(get_tree(), 0.06)


func _on_dialogue_ended(dialogue: Object) -> void:
	post_dialogue_pre_fight_timer.start()
