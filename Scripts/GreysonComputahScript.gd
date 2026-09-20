extends Node2D

# GREYSON & COMPUTAH, boss 2: one boss with two bodies and two health bars. Whichever survives the
# other's death becomes a second phase whose strength is exactly the health it had left, so the fight
# teaches "hurt them equally" through its structure rather than through a tutorial.
#
# This node is the coordinator. It owns the health panel both bars live in, the surge that warns the
# player when the two are drifting apart, the `power` the swap latches, the music and the end of the
# fight. The bodies (GreysonScript, ComputahScript) own their own health, art and hurtbox; the
# fight-wide state machine under here drives both of them.
#
# BOTH BODIES AND THIS NODE ARE IN FightOutro.BOSS_GROUP. Only this node declares OUTRO_DIALOGUE, but
# the bodies have to be in the group too: PlayerHype.is_inert() scans it for a node with
# can_be_dazed() and, finding none, makes hype inert and hides the meter with no error at all.

const FightOutro := preload("res://Scripts/FightOutro.gd")
const Layout := preload("res://Scripts/GreysonComputahArtLayout.gd")
const BossHealthBarUI := preload("res://Scripts/BossHealthBarUI.gd")
# What the two of them say once the fight is over, under player_won and player_lost.
const OUTRO_DIALOGUE := "res://Dialogue/GreysonAndComputahOutro.dialogue"
# This fight's place in the order; GameProgress decides what follows it.
const FIGHT_SCENE := "res://Scenes/Bosses/GreysonBossFightScene.tscn"
# Whose fill each row carries, in bodies() order: Greyson on top, Computah under him.
const BAR_KEYS: Array[StringName] = [&"greyson", &"computah"]

#THE SURGE
# The visible warning while both live. The gap between the two health ratios past SURGE_FLOOR ramps
# to full over SURGE_SPAN; the healthier body's bar goes hot, its aura comes on, and its attack
# intervals tighten. INTERVALS ONLY, NEVER TELEGRAPHS: a read that gets shorter as the fight goes
# wrong is a coin flip, not a difficulty curve.
const SURGE_FLOOR := 0.20
const SURGE_SPAN := 0.40
const SURGE_INTERVAL_SCALE := 0.78
# The one word, the first time the gap gets serious.
const SURGE_WORD_AT := 0.5
const SURGE_WORD := "OVERCLOCKING"
# The aura comes on as soon as the gap is doing anything at all.
const SURGE_AURA_AT := 0.05

#THE NEAR-DEATH CLAMP
# A body cannot be killed while the other is still above this: the killing hit is cut down to leave
# it on 1 HP and it stays there, visibly on the brink, until the other drops. It is the fight's
# biggest fairness lever - without it, killing one early is unrecoverable - and it costs the player
# exactly one wasted hit.
const SWAP_GUARD_RATIO := 0.75
const BRINK_WORD := "ON THE BRINK"

# Their own theme. Same level as Eric's, so walking from one fight to the next does not jump.
const THEME := "res://Assets/Audio/Music/greyson_theme.wav"
const THEME_DB := -7.0

@export var greyson: CharacterBody2D
@export var computah: CharacterBody2D

@onready var state_machine: Node = $StateManager
@onready var music_player: AudioStreamPlayer = $MusicPlayer
@onready var victory_sfx_player: AudioStreamPlayer = $VictorySfxPlayer
@onready var hit_sfx_player: AudioStreamPlayer = $HitSfxPlayer

#UI (BossHealthBarUI builds it at runtime)
var hud_layer: CanvasLayer
var health_panel: Control

var music_base_db := 0.0
var music_duck: Tween

# Latched once, when the first body dies: the survivor's health ratio at that moment. No healing, ever.
var power := 0.0
var swapped := false
var surge := 0.0
var surge_word_shown := false


func _ready() -> void:
	add_to_group(FightOutro.BOSS_GROUP)
	greyson.fight = self
	computah.fight = self
	_build_health_panel()
	_refresh_bars()

	# "Two Bars", written for this fight - see art_source/music/greyson_theme.rb. One 16-bar cycle
	# cut to the beat, so LOOP_FORWARD runs it end to end with no seam. Replaces boss2_theme.ogg,
	# which was a shared placeholder three fights were using.
	music_player.stream = load(THEME)
	music_player.volume_db = THEME_DB
	if music_player.stream is AudioStreamWAV:
		music_player.stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
		music_player.stream.loop_begin = 0
		music_player.stream.loop_end = int(music_player.stream.get_length() * music_player.stream.mix_rate)
	elif music_player.stream and "loop" in music_player.stream:
		music_player.stream.loop = true
	# Captured after the theme's own level is set, so ducking still swings around the right base.
	music_base_db = music_player.volume_db
	# Placeholders: the pair have no sounds of their own yet.
	victory_sfx_player.stream = load("res://Assets/Audio/SFX/victory_fanfare.ogg")
	hit_sfx_player.stream = load("res://Assets/Audio/SFX/hit_impact.ogg")
	$WindowSfxPlayer.stream = load("res://Assets/Audio/SFX/downed_stinger.ogg")
	$ChaseSfxPlayer.stream = load("res://Assets/Audio/SFX/wrestler_charge.ogg")
	$PounceSfxPlayer.stream = load("res://Assets/Audio/SFX/whirlwind_whoosh.ogg")
	$ThrowSfxPlayer.stream = load("res://Assets/Audio/SFX/whirlwind_whoosh.ogg")
	$CatchSfxPlayer.stream = load("res://Assets/Audio/SFX/wrestler_collision.ogg")
	$PunchSfxPlayer.stream = load("res://Assets/Audio/SFX/hit_impact.ogg")
	$SwapSfxPlayer.stream = load("res://Assets/Audio/SFX/earthquake_slam.ogg")
	$LaserSfxPlayer.stream = load("res://Assets/Audio/SFX/laser_charge.ogg")


func start_music() -> void:
	if music_player and not music_player.playing:
		music_player.play()


func bodies() -> Array:
	return [greyson, computah]


func other_body(body: Node) -> Node:
	return computah if body == greyson else greyson


func is_alive(body: Node) -> bool:
	return is_instance_valid(body) and not body.defeated and body.boss_health > 0


func both_alive() -> bool:
	return is_alive(greyson) and is_alive(computah)


# The one still standing once the other has gone, or null while both live.
func survivor() -> Node:
	if swapped:
		return greyson if is_alive(greyson) else computah
	return null


#THE STATE MACHINE'S SIDE OF THE BOSS INTERFACE
# The bodies ask through here so neither of them needs to know the machine exists.

func is_open_to(body: Node) -> bool:
	return state_machine.is_open_to(body)


func end_window(body: Node, stagger_time: float) -> bool:
	return state_machine.end_window(body, stagger_time)


func flinch(body: Node) -> void:
	state_machine.flinch(body)


func can_parry_stagger(body: Node, hit: RefCounted) -> bool:
	return state_machine.can_parry_stagger(body, hit)


func parry_stagger(body: Node, duration: float) -> void:
	state_machine.parry_stagger(body, duration)


#THE SURGE AND THE CLAMP

# The gap between the two, 0 to 1, and which body it is working for. Once one of them is gone there
# is nothing to be out of balance with, so it resets and never stacks with `power`.
func _recompute_surge() -> void:
	if not both_alive():
		_set_surge(0.0)
		return
	var gap := absf(greyson.get_health_ratio() - computah.get_health_ratio())
	_set_surge(clampf((gap - SURGE_FLOOR) / SURGE_SPAN, 0.0, 1.0))


func _set_surge(value: float) -> void:
	surge = value
	var hot := surging_body()
	for body in bodies():
		if is_alive(body):
			body.show_aura(body == hot or (swapped and body == survivor()))
	# Only the body the player is neglecting beats, and only while the gap is open: the bar puts
	# itself back when its beat goes to nothing.
	for row in bodies().size():
		health_panel.set_beat(row, surge if bodies()[row] == hot else 0.0)
	if surge >= SURGE_WORD_AT and not surge_word_shown:
		surge_word_shown = true
		show_word(SURGE_WORD)


# The healthier of the two while the gap is open: whoever the player has been neglecting.
func surging_body() -> Node:
	if surge < SURGE_AURA_AT or not both_alive():
		return null
	return greyson if greyson.get_health_ratio() > computah.get_health_ratio() else computah


# What every attack interval is multiplied by. Telegraphs never see this.
func interval_scale(body: Node) -> float:
	var scale := 1.0
	if body == surging_body():
		scale *= lerpf(1.0, SURGE_INTERVAL_SCALE, surge)
	if swapped:
		scale *= lerpf(1.0, 0.62, power)
	return scale


# How long a punish window stays open. Phase two shrinks it toward the floor the plan settled on;
# raising that floor is the safest correction if high-power phase two ever feels like a wall.
func window_scale() -> float:
	return 1.0 if not swapped else lerpf(3.0, 1.8, power) / 3.0


# Whether `body` is being held off death by the other one still being healthy.
func clamps(body: Node) -> bool:
	if swapped or not is_instance_valid(body):
		return false
	var other := other_body(body)
	if not is_alive(other):
		return false
	return other.get_health_ratio() > SWAP_GUARD_RATIO


#WHAT THE BODIES REPORT

# The surge is recomputed BEFORE the bars, or the hot colour would always be one hit behind the gap
# that earned it.
func on_body_damaged(_body: Node) -> void:
	hit_sfx_player.play()
	_recompute_surge()
	_refresh_bars()
	_refresh_brinks()


# The clamp can land on the body that was hit, and can lift off the other one when this hit drops
# the healthy body under the guard ratio.
func _refresh_brinks() -> void:
	for body in bodies():
		if not is_instance_valid(body):
			continue
		if body.refresh_brink():
			show_word(BRINK_WORD)
			var other := other_body(body)
			if is_alive(other):
				other.flare_aura()


func on_body_killed(body: Node) -> void:
	_refresh_bars()
	_refresh_brinks()
	if both_dead():
		state_machine.enter_defeated()
		_win()
		return
	# The first death: the survivor's health right now is exactly how strong phase two is.
	swapped = true
	power = other_body(body).get_health_ratio()
	surge_word_shown = false
	_recompute_surge()
	_refresh_bars()
	_grey_out_bar(body)
	state_machine.enter_swap(body)


func both_dead() -> bool:
	return not is_alive(greyson) and not is_alive(computah)


func _win() -> void:
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


#MUSIC
# Node-bound, so a finisher's freeze holds it and the end of the fight takes it away.

func duck_music(db: float, seconds: float) -> void:
	if music_duck:
		music_duck.kill()
	music_duck = music_player.create_tween()
	music_duck.tween_property(music_player, "volume_db", music_base_db + db, seconds)


func restore_music(seconds: float) -> void:
	duck_music(0.0, seconds)


func snap_music_level() -> void:
	if music_duck:
		music_duck.kill()
		music_duck = null
	music_player.volume_db = music_base_db


#THE HEALTH PANEL
# One framed panel, one name, two stacked bars joined by a bracket: they have to read as one boss.
# Each bar carries a ghost marker at the OTHER body's ratio, so the gap between a bar's fill edge and
# its marker is the imbalance itself. BossHealthBarUI draws all of that; this node only tells it what
# the two bodies are doing.

func _build_health_panel() -> void:
	hud_layer = CanvasLayer.new()
	add_child(hud_layer)

	var rows: Array = []
	for row in bodies().size():
		var body: Node = bodies()[row]
		rows.append({"key": BAR_KEYS[row], "max": body.max_health, "value": body.boss_health})
	health_panel = BossHealthBarUI.create({
		"rows": rows,
		"plate": &"greyson_pair",
		"text": GameProgress.boss_name(FIGHT_SCENE),
	})
	hud_layer.add_child(health_panel)


func _refresh_bars() -> void:
	for row in bodies().size():
		var body: Node = bodies()[row]
		var other := other_body(body)
		health_panel.set_value(row, body.boss_health)
		health_panel.set_ghost(row, other.get_health_ratio(), is_alive(other))
		health_panel.set_heat(row, _heat_for(body))


# How far this body's bar is pushed toward hot: the gap it is winning, or the power a swap latched.
func _heat_for(body: Node) -> float:
	if body == surging_body():
		return surge
	if swapped and body == survivor():
		return power
	return 0.0


func _grey_out_bar(body: Node) -> void:
	health_panel.finish_row(bodies().find(body))


#WORD POPUPS
# Their own words over the health panel. The PlayerDefense popup set belongs to the defence coder,
# and words only this fight says don't belong in it.

func show_word(text: String) -> void:
	var label := Label.new()
	label.text = text
	label.theme = load("res://Assets/UI/ui_theme.tres")
	label.add_theme_font_size_override("font_size", Layout.WORD_FONT_SIZE)
	label.add_theme_color_override("font_color", Layout.WORD_COLOR)
	label.add_theme_color_override("font_outline_color", Color(0, 0, 0))
	label.add_theme_constant_override("outline_size", Layout.WORD_OUTLINE)
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.size = Vector2(1400, 160)
	label.pivot_offset = label.size / 2.0
	label.position = Layout.WORD_CENTRE - label.size / 2.0
	label.scale = Vector2.ONE * Layout.WORD_FROM_SCALE
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hud_layer.add_child(label)

	var show := label.create_tween()
	show.tween_property(label, "scale", Vector2.ONE,
		Layout.WORD_GROW_TIME).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	show.tween_interval(Layout.WORD_TIME - Layout.WORD_GROW_TIME)
	show.tween_property(label, "modulate:a", 0.0, 0.3)
	show.tween_callback(label.queue_free)
