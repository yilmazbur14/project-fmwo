extends CharacterBody2D

const HitStop := preload("res://Scripts/HitStop.gd")
const FightOutro := preload("res://Scripts/FightOutro.gd")
const BossHealthBarUI := preload("res://Scripts/BossHealthBarUI.gd")
const BossBreakGauge := preload("res://Scripts/BossBreakGauge.gd")
const BreakGaugeUI := preload("res://Scripts/BreakGaugeUI.gd")
const JordanArtLayout := preload("res://Scripts/JordanArtLayout.gd")
# What he says once the fight is over, under player_won and player_lost.
const OUTRO_DIALOGUE := "res://Dialogue/JordanOutro.dialogue"
# This fight's place in the order; as the last one, GameProgress finds nothing after it.
const FIGHT_SCENE := "res://Scenes/Bosses/JordanBossFightScene.tscn"

#CONSTANTS
# Phase 1's health.
@export var max_health := 12
var boss_health := max_health
const MAX_HITS_PER_WINDOW := 3
# Each opening takes the damage of a clean chain of MAX_HITS_PER_WINDOW punches (PunchAllowance).
const PunchAllowance := preload("res://Scripts/PunchAllowance.gd")
const PHANTOM_HIT_WINDOW := 0.5
# Blasts from punched figures that can hurt him per summon, apart from the taunt's punches.
const MAX_EXPLOSION_HITS_PER_CYCLE := 2
# A blast that hurts him holds up what he's doing for this long, while he leans back and recovers.
const STAGGER_TIME := 0.4
const STAGGER_LEAN := -0.25
const STAGGER_LEAN_TIME := 0.1

#BREAK GAUGE (BossBreakGauge)
# The rule the fights share: N clean reads from empty is a guaranteed Break. A parry or a perfect dodge
# is a read, a hit costs one and a guard break two, a 3-punch combo is one (a quarter, a quarter and a
# half), and nothing decays. His N is 6, not 8: his fight is about two summon cycles long, and eight
# reads would rarely arrive. A figure the player punched back into him is two (take_explosion_hit).
# BREAK_READ is BossBreakGauge's max_value of 100 over N, given as it is (BREAK_EPSILON).
const BREAK_READS := 6
const BREAK_READ := 100.0 / BREAK_READS
const BREAK := {
	"parry_gain": BREAK_READ,
	"grab_parry_gain": BREAK_READ,
	"reflect_gain": 2.0 * BREAK_READ,
	"perfect_dodge_gain": BREAK_READ,
	"punch_gain": BREAK_READ / 4.0,
	"charged_punch_gain": BREAK_READ / 2.0,
	"hit_loss": BREAK_READ,
	"guard_break_loss": 2.0 * BREAK_READ,
	"unlock_delay": 3.0,
	"broken_time": 3.0,
}
# The attacks this fight owns, for the gauge. His one attack both fills it and drains it.
const ATTACK_IDS: Array[StringName] = [&"funko_blast"]

#UI (BossHealthBarUI builds it at runtime)
var health_bar: Control
var hud_layer: CanvasLayer
var break_gauge: Node

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
var punches := PunchAllowance.new()
var explosion_hits_this_cycle := 0
# The player's finisher can daze him once per taunt.
var daze_used := false

var fight_clock := 0.0
var last_contact_hit_time := -INF

var sprite_base_position: Vector2
var stagger_tween: Tween

var current_anim := &""
var anim: Dictionary = {}
var anim_step := 0
var anim_clock := 0.0
var anim_next := &""
var anim_done := false
# What the state he is in shows, which a flinch hands back to.
var state_anim := &""


func _ready() -> void:
	add_to_group(FightOutro.BOSS_GROUP)
	hurtbox.area_entered.connect(_on_hurtbox_entered)

	_apply_art_layout()
	sprite_base_position = sprite.position
	# Before the HUD, which hangs the gauge's bar under his health bar.
	var scene := get_tree().current_scene
	var player: Node = scene.get_node_or_null(FightOutro.PLAYER_PATH) if scene else null
	if player:
		_add_break_gauge(player)
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


func _add_break_gauge(player: Node) -> void:
	break_gauge = BossBreakGauge.new()
	break_gauge.name = "BreakGauge"
	break_gauge.boss = self
	break_gauge.player = player
	# earns_from stays unset: his one attack both fills and drains it.
	break_gauge.owns_attack = func(id: StringName) -> bool: return ATTACK_IDS.has(id)
	break_gauge.parry_gain = BREAK.parry_gain
	break_gauge.grab_parry_gain = BREAK.grab_parry_gain
	break_gauge.reflect_gain = BREAK.reflect_gain
	break_gauge.perfect_dodge_gain = BREAK.perfect_dodge_gain
	break_gauge.punch_gain = BREAK.punch_gain
	break_gauge.charged_punch_gain = BREAK.charged_punch_gain
	break_gauge.hit_loss = BREAK.hit_loss
	break_gauge.guard_break_loss = BREAK.guard_break_loss
	break_gauge.unlock_delay = BREAK.unlock_delay
	add_child(break_gauge)
	break_gauge.broke.connect(_on_break)


# The gauge fills inside physics flushes and his own physics steps, where his states can't switch.
func _on_break() -> void:
	state_machine.enter_broken.call_deferred()


func start_music() -> void:
	if music_player and not music_player.playing:
		music_player.play()


func get_health_ratio() -> float:
	return float(boss_health) / float(max_health)


func hurtbox_rect() -> Rect2:
	var shape: CollisionShape2D = hurtbox.get_node("CollisionShape2D")
	return shape.global_transform * shape.shape.get_rect()


func is_broken() -> bool:
	return state_machine.current_state == state_machine.states.get("Broken")


func is_juggled() -> bool:
	return state_machine.current_state == state_machine.states.get("Juggled")


# Down from a Break or a juggle, until he is back on his feet: the gauge waits for this.
func is_down() -> bool:
	return is_broken() or is_juggled()


func _physics_process(delta: float) -> void:
	fight_clock += delta


# The offset is set once and never per animation: the finisher's recoil tweens it and settles it back
# to whatever it was.
func _apply_art_layout() -> void:
	sprite.position = JordanArtLayout.FLOOR_POINT
	sprite.offset = JordanArtLayout.SPRITE_OFFSET
	var box := JordanArtLayout.local_rect(JordanArtLayout.BODY_BOX)
	var hurtbox_shape: CollisionShape2D = hurtbox.get_node("CollisionShape2D")
	hurtbox_shape.position = box.get_center()
	(hurtbox_shape.shape as RectangleShape2D).size = box.size


#ANIMATION

# A non-looping animation holds its last frame when it ends, unless `next_anim` follows it. The layout
# picks the frames, and the entry's AnimationPlayer clip plays under them.
func play_anim(anim_name: StringName, next_anim: StringName = &"") -> void:
	current_anim = anim_name
	anim = JordanArtLayout.anim(anim_name)
	anim_next = next_anim
	anim_step = 0
	anim_clock = 0.0
	anim_done = false
	var sheet: Texture2D = load(anim.sheet)
	# Back to the first frame before the frame count changes, so the current one can't be out of range.
	sprite.frame = 0
	sprite.texture = sheet
	sprite.hframes = roundi(sheet.get_width() / JordanArtLayout.FRAME_SIZE.x)
	animation_player.play(anim.get("motion", &"RESET"))
	_show_anim_frame()


# A state's own animation. A one-shot still playing finishes first and hands over to it - the summon's
# pop over the start of the taunt, a flinch into the idle - while a loop gives way at once.
func play_state_anim(anim_name: StringName) -> void:
	state_anim = anim_name
	if not anim.is_empty() and not anim.loop and not anim_done:
		anim_next = anim_name
		return
	play_anim(anim_name)


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
			if anim_next != &"":
				play_anim(anim_next)
			return
		_show_anim_frame()


func _frame_time() -> float:
	var times: Array = anim.times
	return times[mini(anim_step, times.size() - 1)]


func _show_anim_frame() -> void:
	sprite.frame = anim.frames[anim_step]


# A hit plays over whatever he was doing and hands back to what his state shows: a hit on the summon's
# pop, which runs into the taunt window, goes back to the taunt, not the pop.
func _flinch() -> void:
	play_anim(&"hit", state_anim)


func _on_hurtbox_entered(area: Area2D) -> void:
	if boss_health <= 0 or not area.is_in_group("player attack"):
		return

	# Same phantom-hit filter as Mason: a punch that connects as its hitbox switches on is reported
	# again when PlayerPunching switches the hitbox off, which would eat the hit cap.
	if not area.monitorable and fight_clock - last_contact_hit_time < PHANTOM_HIT_WINDOW:
		return
	if area.get_parent().combo.resolve_punch(self) > 0 and area.monitorable:
		last_contact_hit_time = fight_clock


# Punches only land while he taunts, or while a Break has him down.
func take_punch(amount: int) -> int:
	if boss_health <= 0 or not (state_machine.is_taunting() or is_broken()):
		return 0
	var allowed := punches.allow(amount, hits_this_window, MAX_HITS_PER_WINDOW)
	if allowed <= 0:
		return 0
	hits_this_window += 1
	var dealt := _take_damage(allowed)
	punches.spend(dealt)
	return dealt


# A punched figure's blast, which lands whatever he's doing.
func take_explosion_hit(amount: int) -> int:
	if boss_health <= 0 or explosion_hits_this_cycle >= MAX_EXPLOSION_HITS_PER_CYCLE:
		return 0
	explosion_hits_this_cycle += 1
	var dealt := _take_damage(amount)
	if dealt > 0:
		state_machine.get_player().hype.reward_explosion_redirect()
		# Two reads: the blast read and punched away, and the aim that turned it on him.
		if break_gauge:
			break_gauge.add(break_gauge.reflect_gain)
	get_tree().call_group("arena_crowd", "cheer", 1.5)
	if boss_health > 0:
		_stagger()
	return dealt


# The player's finisher (see PlayerFinisher): a charged combo punch during the taunt or a Break dazes
# him, and the uppercut that follows ends that window. Phase 1 has no health floor for its damage to
# stop at.
func can_be_dazed() -> bool:
	return not defeated and boss_health > 0 and not daze_used and (state_machine.is_taunting() or is_broken())


# The three-bar mash and the juggle are the Break's payout alone; the taunt pays the plain single-bar
# finisher. With his 12 health the juggle's 40% on every window would end the fight in two.
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


# Not held to the taunt's hit cap.
func take_finisher(amount: int) -> int:
	if boss_health <= 0:
		return 0
	return _take_damage(amount)


# He stops taunting and idles for `stagger_time` in place of his rest, then summons again once the swarm is over.
func end_recovery(stagger_time: float) -> bool:
	if boss_health <= 0:
		return false
	# Crashed from a juggle, he lies a beat before he gets up.
	if is_juggled():
		state_machine.current_state.recover(stagger_time)
		return true
	if is_broken():
		state_machine.end_break(stagger_time)
		return true
	state_machine.end_taunt(stagger_time)
	return true


func get_max_health() -> int:
	return max_health


func get_daze_anchor() -> Vector2:
	if is_broken():
		return global_position + JordanArtLayout.broken_daze_anchor()
	return global_position + JordanArtLayout.daze_anchor()


func get_finisher_hurtbox() -> Area2D:
	return hurtbox


# The tiered finisher's juggle (PlayerFinisher), drawn by JordanJuggled. He is never shoved: he has no
# knock_back and no juggle_knock_back, and stays rooted to his spot as the training dummy does.
func begin_juggle() -> void:
	state_machine.enter_juggled()


func juggle_lift(px: float) -> void:
	if is_juggled():
		state_machine.current_state.lift(px)


func juggle_pose(pose: StringName, crater := false) -> void:
	if is_juggled():
		state_machine.current_state.pose(pose, crater)


func juggle_headroom() -> float:
	return state_machine.states["Juggled"].headroom()


# Past the hit cap, as take_finisher, with his hit sound pitched up a step each uppercut.
func take_juggle_hit(amount: int, pitch: float) -> int:
	if boss_health <= 0:
		return 0
	return _take_damage(amount, pitch)


func get_juggle_point() -> Vector2:
	return state_machine.states["Juggled"].air_point()


# A juggle that kills him ends with him still in the air: the outro's first line holds until he has
# landed, as Eric's and Mason's do.
func outro_line_delay(_player_won: bool) -> float:
	if is_juggled():
		return JordanArtLayout.juggle().outro_delay
	return 0.0


func _take_damage(amount: int, pitch := 1.0) -> int:
	var dealt := mini(amount, boss_health)
	boss_health -= dealt
	_refresh_health_bar()
	_hit_feedback()
	hit_sfx_player.pitch_scale = pitch
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
	hud_layer = CanvasLayer.new()
	add_child(hud_layer)

	health_bar = BossHealthBarUI.create({
		"rows": [{"key": &"jordan", "max": max_health, "value": boss_health}],
		"plate": &"jordan",
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

	# Down, he has no hit pose: the kneel holds, and in the air the hit sheet would replace the juggle's.
	if not is_down():
		_flinch()
	sprite.modulate = Color(3, 3, 3)
	var flash_tween = create_tween()
	flash_tween.tween_property(sprite, "modulate", Color(1, 1, 1), 0.15)

	var shake_tween = create_tween()
	for i in 4:
		var offset = Vector2(randf_range(-5, 5), randf_range(-5, 5))
		shake_tween.tween_property(sprite, "position", sprite_base_position + offset, 0.025)
	shake_tween.tween_property(sprite, "position", sprite_base_position, 0.025)

	HitStop.freeze(get_tree(), 0.06)
