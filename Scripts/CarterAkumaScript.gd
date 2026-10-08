extends CharacterBody2D

# Carter, boss 5. He has three moves. The Raging Demon: he flashes his eyes, drags the player to the
# middle of the ring, puts the lights out and sends eighteen clones through them one at a time, then
# stands there open while the lights come back. The Beam Rush: four clones at the top of the ring
# charge beams, lock them onto the player and fire them, three volleys to be escaped rather than
# parried, and once in it he teleports in beside the player and strikes. The Messatsu: he puts the
# lights out, reappears across the ring charging a beam locked onto the player, and fires it as the
# lights come back on - six hits, each its own parry.
# Every parry of all three fills his fight-long Break gauge, and fourteen clean ones from empty break
# him. A Break ends whatever attack is running on the spot, into his Recover cashed from it - open at
# once - which pays the tiered finisher's juggle (CarterJuggled).
# Each sequence lives in its own state - CarterRagingDemon, CarterBeamRush, CarterMessatsu - and this
# node is his body, his health, his art and the darkness the sequences borrow.
# Not to be confused with Scripts/CarterScript.gd, the wrestler Mason calls in - a different
# character with his own art and script.

# A non-looping animation reached the end of its last frame.
signal anim_finished(anim_name: StringName)

const HitStop := preload("res://Scripts/HitStop.gd")
const FightOutro := preload("res://Scripts/FightOutro.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const CarterArtLayout := preload("res://Scripts/CarterArtLayout.gd")
const BossHealthBarUI := preload("res://Scripts/BossHealthBarUI.gd")
const BossBreakGauge := preload("res://Scripts/BossBreakGauge.gd")
const BreakGaugeUI := preload("res://Scripts/BreakGaugeUI.gd")
# What he says once the fight is over, under player_won and player_lost.
const OUTRO_DIALOGUE := "res://Dialogue/CarterOutro.dialogue"
const FIGHT_SCENE := "res://Scenes/Bosses/CarterBossFightScene.tscn"

#CONSTANTS
# 125, doubled from 50 by the user with every boss's (2026-09-25) and raised 25% with them (2026-09-30):
# Josh is 35 and Mason 120; Carter is fight 5 of 7, and he has three attacks rather than one.
# Every finisher pays a share of max_health - the plain one 25%, the juggle 25/35/50% for one, two or
# three bars, x1.6 with full hype, which a parry fight fills inside its first barrage - so this number
# doesn't set his length: how many finisher windows he hands out does. That is his move set's job.
@export var max_health := 125
# Only a Break's window dazes him (can_be_dazed). Off by the user's call (2026-10-05): "lets remove this
# rule except for jordan on the kaiju". On (2026-10-04 to 10-05), every window he earns without a Break
# pays its banked damage and three punches and nothing more.
@export var break_only_finisher := false
var boss_health := max_health
const MAX_HITS_PER_WINDOW := 3
# Each opening takes the damage of a clean chain of MAX_HITS_PER_WINDOW punches (PunchAllowance).
const PunchAllowance := preload("res://Scripts/PunchAllowance.gd")
const PHANTOM_HIT_WINDOW := 0.5
const VIEW_SIZE := Vector2(1920, 1080)
# Fading in decibels sounds even all the way down; by this level nothing can be heard.
const SILENT_DB := -60.0

# Three takes of one rush, rotated by clone, so fifteen of them a round don't sound like one sound
# played fifteen times.
const RUSH_SFX := [
	"res://Assets/Audio/SFX/carter_rush_1.wav",
	"res://Assets/Audio/SFX/carter_rush_2.wav",
	"res://Assets/Audio/SFX/carter_rush_3.wav",
]

# His Break gauge, on the rule every fight's is on: this many clean reads from empty is a Break. The
# user's 8 from 2026-09-27 ("if the player can parry 8 in a row, that should be enough to break
# carter"), 14 on 2026-10-04 and 18 since 2026-10-05: one whole first barrage read clean, all eighteen
# reds. With his attacks chained (CarterStateMachine.chain_attacks) a Break is the one way to open him
# mid-combo, and at 14 the first barrage and the strike after it broke him so often that two finishers
# had him down in about 40 s. Every parry is one read - a red clone, his strike, a hit of his Messatsu -
# a hit taken costs one back and a guard break two. 100 / 18 isn't exact in floating point, and
# eighteen of it sum a hair under 100: BossBreakGauge's BREAK_EPSILON is what lands the last on it. His
# is a parry fight: a perfect dodge earns nothing (the Messatsu's skips its whole string, and the Beam
# Rush's beams can only be dodged) and neither does a punch. No grabs and nothing of his to fling back,
# so no grab or reflect gain.
const BREAK_READS := 18
const BREAK_READ := 100.0 / BREAK_READS
const BREAK := {
	"parry_gain": BREAK_READ,
	"perfect_dodge_gain": 0.0,
	"punch_gain": 0.0,
	"charged_punch_gain": 0.0,
	"hit_loss": BREAK_READ,
	"guard_break_loss": 2.0 * BREAK_READ,
	# His Break IS his punish window, so the wait is only the breath after it.
	"unlock_delay": 0.5,
	# The shortest his Break window may be. He has no Broken state: a Break is his Recover, for the
	# longer of this and what the attack earned.
	"broken_time": 5.0,
}

#UI (BossHealthBarUI and BreakGaugeUI build it at runtime)
var hud_layer: CanvasLayer
var health_bar: Control
# His Break gauge (BossBreakGauge), fight-long and always on screen, and the bar that draws it. The
# bar is on the HUD layer, so its BREAK! reads over the dark.
var break_gauge: Node
var break_gauge_bar: Control

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
# Pure black over the whole world, for the KO only. Built in code, hidden until then.
var blackout: Polygon2D
# The spotlight that comes back up on him at the end of the KO. Built in code, hidden until then.
var ko_light: Node2D
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
@onready var ko_sfx_player: AudioStreamPlayer = $KoSfxPlayer
@onready var charge_sfx_player: AudioStreamPlayer = $ChargeSfxPlayer
@onready var fire_sfx_player: AudioStreamPlayer = $FireSfxPlayer
@onready var lights_sfx_player: AudioStreamPlayer = $LightsSfxPlayer
var break_sting_player: AudioStreamPlayer

var defeated := false
var hits_this_window := 0
var punches := PunchAllowance.new()
# One finisher daze per recovery; Recover clears it.
var daze_used := false

var fight_clock := 0.0
var last_contact_hit_time := -INF

var sprite_base_position: Vector2
var music_base_db := 0.0
var music_start := 0.0
var music_duck: Tween
# The dark coming in or going out. Kept so the next ramp, or a snap, can stop it: a ramp left running
# under a snap would carry on and bring the dark back after the lights were put on.
var curtain_fade: Tween

var aura_clock := 0.0
var mark_clock := 0.0
# The frames the mark's glow cycles through; empty for all of them.
var mark_frames: Array = []

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
	# Before the HUD: the HUD builds the gauge's bar, and only if there is a gauge to draw.
	var player: Node = get_tree().current_scene.get_node_or_null(FightOutro.PLAYER_PATH) if get_tree().current_scene else null
	if player:
		_add_break_gauge(player)
	_build_hud()
	_build_dark_stage()
	_build_ko_light()

	# Loaded here rather than when the fight starts: it is a 4 MB MP3 and reading it off disk on the
	# first bar would hitch.
	var theme := CarterArtLayout.theme()
	music_player.stream = load(theme.stream)
	if music_player.stream is AudioStreamWAV:
		# Our own theme is a WAV cut to one whole cycle, and a WAV loops by sample range rather
		# than by a `loop` flag, so it takes the other branch entirely.
		music_player.stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
		music_player.stream.loop_begin = 0
		music_player.stream.loop_end = int(music_player.stream.get_length() * music_player.stream.mix_rate)
	elif music_player.stream:
		music_player.stream.loop = true
		if theme.loop_offset > 0.0:
			music_player.stream.loop_offset = theme.loop_offset
	# Before music_base_db is taken, since every duck and fade in the fight is relative to it.
	music_player.volume_db = theme.volume_db
	music_base_db = music_player.volume_db
	music_start = theme.start
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
	# Loaded here rather than at the kill: it has to land on the exact frame the emblem lights, and
	# an MP3 read from disk on first play would miss it.
	var ko := CarterArtLayout.ko_ding()
	ko_sfx_player.stream = load(ko.stream)
	ko_sfx_player.volume_db = ko.volume_db
	charge_sfx_player.stream = load(CarterArtLayout.messatsu_sfx(&"charge"))
	fire_sfx_player.stream = load(CarterArtLayout.messatsu_sfx(&"fire"))
	lights_sfx_player.stream = load(CarterArtLayout.messatsu_sfx(&"lights_on"))
	# Built here, not in the scene: nothing here edits his scene.
	var sting := CarterArtLayout.BREAK_STING_SFX
	break_sting_player = AudioStreamPlayer.new()
	break_sting_player.stream = load(sting.stream)
	break_sting_player.pitch_scale = sting.pitch
	break_sting_player.volume_db = sting.volume_db
	add_child(break_sting_player)


#HIS BREAK GAUGE
# Fight-long, on BREAK: every parry of his three attacks earns a read, and every hit of his costs one -
# the feint's punish clone and the Beam Rush's beams included, though neither can be parried, so the
# Beam Rush's one read is his strike. It never resets between attacks, so what one attack leaves in it
# the next starts from.
const BREAK_EARNS: Array[StringName] = [&"carter_clone_rush", &"carter_teleport_strike", &"carter_messatsu_beam"]
const BREAK_DRAINS: Array[StringName] = [&"carter_clone_rush", &"carter_teleport_strike", &"carter_messatsu_beam",
	&"carter_clone_punish", &"carter_rush_beam"]


func _add_break_gauge(player: Node) -> void:
	break_gauge = BossBreakGauge.new()
	break_gauge.name = "BreakGauge"
	break_gauge.boss = self
	break_gauge.player = player
	break_gauge.owns_attack = func(id: StringName) -> bool: return BREAK_DRAINS.has(id)
	break_gauge.earns_from = func(hit: RefCounted) -> bool: return BREAK_EARNS.has(hit.attack_id)
	break_gauge.parry_gain = BREAK.parry_gain
	break_gauge.perfect_dodge_gain = BREAK.perfect_dodge_gain
	break_gauge.punch_gain = BREAK.punch_gain
	break_gauge.charged_punch_gain = BREAK.charged_punch_gain
	break_gauge.hit_loss = BREAK.hit_loss
	break_gauge.guard_break_loss = BREAK.guard_break_loss
	break_gauge.unlock_delay = BREAK.unlock_delay
	add_child(break_gauge)
	break_gauge.broke.connect(_on_break)


# The gauge fills inside a physics flush, where states can't switch.
func _on_break() -> void:
	state_machine.on_break.call_deferred()


# BossBreakGauge._physics_process asks this every step. Down, for him, is the punish window and the
# juggle that can follow it, and a Break owed before them: that is what a Break buys, and the wait
# before the gauge takes anything again starts when they end.
func is_down() -> bool:
	return state_machine.is_recovering() or is_juggled() or state_machine.break_owed


func is_juggled() -> bool:
	return state_machine.current_state == state_machine.states.get("Juggled")


func play_break_sting() -> void:
	break_sting_player.play()


func start_music() -> void:
	if music_player and not music_player.playing:
		# Past the silence his track opens on, so the fight starts on the music and not on four
		# seconds of nothing.
		music_player.play(music_start)


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
		var step := int(mark_clock / CarterArtLayout.FINAL_MARK_GLOW.frame_time)
		if mark_frames.is_empty():
			mark_glow.frame = step % mark_glow.hframes
		else:
			mark_glow.frame = mark_frames[step % mark_frames.size()]


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


# All the way out, for the KO: the arena is black and the bell is the only thing left, so the track
# bows out under it rather than ducking and coming back. Faded, never cut - a 4 minute mastered piece
# stopping dead is its own kind of wrong.
func fade_music_out(seconds: float) -> void:
	if music_duck:
		music_duck.kill()
	music_duck = music_player.create_tween()
	music_duck.tween_property(music_player, "volume_db", SILENT_DB, seconds)
	music_duck.tween_callback(music_player.stop)


# Nothing may be left holding the music down once the sequence is over, however it ended.
func snap_music_level() -> void:
	if music_duck:
		music_duck.kill()
		music_duck = null
	music_player.volume_db = music_base_db


# The bell on the emblem catching. Nothing stops it afterwards - the ring is the point.
func play_ko_ding() -> void:
	ko_sfx_player.play()


func play_rush(index: int, pitch := 1.0) -> void:
	rush_sfx_player.stream = load(RUSH_SFX[index % RUSH_SFX.size()])
	rush_sfx_player.pitch_scale = pitch
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
	_build_blackout()


# Over every fighter, hazard and burst in the world, which the Demon's darkness deliberately is not.
# Only the KO ever shows it.
func _build_blackout() -> void:
	blackout = Polygon2D.new()
	blackout.polygon = CarterArtLayout.rect_polygon(CarterArtLayout.DARK_BORDER)
	blackout.color = Color(0, 0, 0)
	blackout.z_index = CarterArtLayout.KO_BLACK_Z
	blackout.modulate.a = 0.0
	blackout.hide()
	dark_stage.add_child(blackout)


func _build_pool() -> void:
	pool.add_child(_make_spotlight())


# The Demon's spotlight, drawn as light, with its anchor texel on the origin of whatever it is added
# to: the player's feet for the Demon's pool, his own for the KO.
func _make_spotlight() -> Node2D:
	var spec := CarterArtLayout.spotlight()
	if spec.has("texture"):
		var light := Sprite2D.new()
		light.texture = load(spec.texture)
		light.centered = false
		light.offset = -spec.anchor
		light.scale = Vector2.ONE * spec.scale
		light.material = CarterArtLayout.additive()
		return light
	var glow := Polygon2D.new()
	glow.polygon = CarterArtLayout.ellipse(spec.radii, spec.points)
	glow.color = spec.color
	glow.material = CarterArtLayout.additive()
	return glow


# The same light again for the end of the KO, on his feet rather than the player's. It was authored
# to sit under someone standing at centre stage, and he is: 558 px of cone above his feet against his
# 243 px, so it frames the whole of him and runs off the top of the screen the way a light from above
# should. A child of him, so wherever the teleport put him, it is on him.
func _build_ko_light() -> void:
	ko_light = _make_spotlight()
	ko_light.z_index = CarterArtLayout.KO_LIGHT_Z
	ko_light.modulate.a = 0.0
	ko_light.hide()
	add_child(ko_light)


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
	if curtain_fade:
		curtain_fade.kill()
	curtain_fade = curtain.create_tween()
	curtain_fade.tween_property(curtain, "modulate:a", 1.0, seconds)


func open_pool(seconds: float) -> void:
	var bloom := pool.create_tween().set_parallel()
	bloom.tween_property(pool, "scale", Vector2.ONE, seconds).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	bloom.tween_property(pool, "modulate:a", 1.0, seconds)


func clear_dark(seconds: float) -> void:
	if curtain_fade:
		curtain_fade.kill()
	curtain_fade = curtain.create_tween().set_parallel()
	curtain_fade.tween_property(curtain, "modulate:a", 0.0, seconds)
	curtain_fade.tween_property(pool, "modulate:a", 0.0, seconds)
	curtain_fade.chain().tween_callback(dark_stage.hide)


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
	if curtain_fade:
		curtain_fade.kill()
		curtain_fade = null
	curtain.modulate.a = 0.0
	pool.modulate.a = 0.0
	pool.scale = Vector2.ONE * CarterArtLayout.POOL_OPEN_FROM
	blackout.modulate.a = 0.0
	blackout.hide()
	dark_stage.hide()
	flash.color.a = 0.0


# The KO: the arena goes all the way to black, spotlight and all. Nothing in the world survives it
# except the emblem, which is drawn above it. It comes down OVER whatever darkness is already up -
# the barrage's curtain and the fallen player's pool stay where they are beneath it - so the room
# only ever gets darker from the kill to the ignition.
func ko_blackout(seconds: float) -> void:
	dark_stage.show()
	blackout.show()
	var fade := blackout.create_tween()
	fade.tween_property(blackout, "modulate:a", 1.0, seconds)


# Over the barrage's darkness, so his dissolve and his reforming in the middle of the ring read in the
# dark, and under the KO's blackout, so it still swallows him when it comes down.
func lift_for_teleport() -> void:
	sprite.z_index = CarterArtLayout.KO_TELEPORT_Z
	aura.z_index = CarterArtLayout.KO_TELEPORT_Z - 1


# The spotlight comes back on and he comes up out of the black with it: the light is drawn on the
# blackout and he is drawn on the light, so the arena stays gone around him. His emblem settles back
# to its own size and strength on his back, since twice-size was for burning alone and would be
# bigger than his torso on a lit body. Node-bound tweens, all of them: nothing here touches audio,
# so the bell rings on through it.
func ko_light_up(seconds: float) -> void:
	ko_light.show()
	var light := ko_light.create_tween()
	light.tween_property(ko_light, "modulate:a", 1.0, seconds)

	for part: CanvasItem in [aura, sprite]:
		if not part.visible:
			continue
		var rest: float = CarterArtLayout.AURA_ALPHA if part == aura else 1.0
		part.modulate.a = 0.0
		part.z_index = CarterArtLayout.KO_BODY_Z - (1 if part == aura else 0)
		var reveal := part.create_tween()
		reveal.tween_property(part, "modulate:a", rest, seconds)

	# Its peak frames spread a wash over his whole upper back, which is what the dark hold wants and
	# exactly what this beat doesn't: it is here to show the body. The frame jump hides inside the
	# resize and the light coming up.
	mark_frames = CarterArtLayout.FINAL_MARK_GLOW.lit_frames
	mark_clock = 0.0
	var mark := mark_glow.create_tween().set_parallel()
	mark.tween_property(mark_glow, "scale", Vector2.ONE * CarterArtLayout.FINAL_MARK_GLOW.scale, seconds)
	mark.tween_property(mark_glow, "position", Vector2.ZERO, seconds)
	mark.tween_property(mark_glow, "modulate:a", CarterArtLayout.KO_LIT_MARK_ALPHA, seconds)


# The one lit thing left. Lifted above the blackout and drawn at twice its size, scaled about its own
# centre so it stays between his shoulders rather than sliding up off them.
func ignite_ko_mark() -> void:
	show_mark_glow(true)
	# Straight in at the brightest frame of the cycle: this is a snap to full burn, and the bell is
	# landing on this exact frame.
	var spec := CarterArtLayout.FINAL_MARK_GLOW
	mark_clock = spec.peak_frame * spec.frame_time
	mark_glow.frame = spec.peak_frame
	mark_glow.z_index = CarterArtLayout.KO_MARK_Z
	var scaled: float = CarterArtLayout.KO_MARK_SCALE
	mark_glow.scale = Vector2.ONE * CarterArtLayout.FINAL_MARK_GLOW.scale * scaled
	mark_glow.position = CarterArtLayout.mark_centre() * (1.0 - scaled)


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


# The flash rect popped to `peak` and let fall over `seconds`, for the Messatsu's lights slamming back
# on. Node-bound, so a freeze holds it.
func pop_flash(peak: float, seconds: float) -> void:
	flash.color.a = peak
	var fade := flash.create_tween()
	fade.tween_property(flash, "color:a", 0.0, seconds)


# CarterCloneScript._burst, for the hits that have no clone to leave it: the parry break for a hit
# that was stopped, the strike for one that landed, drawn as light over everything on the clone layer.
# Its first frame is drawn the moment it is added, which is the frame the hit resolved on.
func spawn_burst(stopped: bool, at: Vector2) -> void:
	var spec: Dictionary = CarterArtLayout.clone_shatter() if stopped else CarterArtLayout.clone_hit()
	if spec.has("texture"):
		var sheet := Sprite2D.new()
		sheet.texture = load(spec.texture)
		sheet.hframes = spec.hframes
		sheet.scale = Vector2.ONE * spec.scale
		sheet.offset = spec.frame_size / 2.0 - spec.pivot
		sheet.z_index = CarterArtLayout.BURST_Z
		if spec.get("additive", false):
			sheet.material = CarterArtLayout.additive()
		state_machine.add_hazard(sheet, at, clone_layer)
		var times: Array = spec.frame_times
		var play := sheet.create_tween()
		for i in range(1, spec.hframes):
			play.tween_interval(times[i - 1])
			play.tween_callback(func() -> void: sheet.frame = i)
		play.tween_interval(times[times.size() - 1])
		play.tween_callback(sheet.queue_free)
		return

	var burst := Polygon2D.new()
	if stopped:
		burst.polygon = CarterArtLayout.star(spec.points, spec.radius, spec.inner_ratio)
	else:
		burst.polygon = CarterArtLayout.ellipse(spec.radii, spec.points)
	burst.color = spec.color
	burst.scale = Vector2.ONE * spec.from_scale
	burst.z_index = CarterArtLayout.BURST_Z
	state_machine.add_hazard(burst, at, clone_layer)
	var play := burst.create_tween()
	play.tween_property(burst, "scale", Vector2.ONE * spec.to_scale, spec.time)
	play.parallel().tween_property(burst, "modulate:a", 0.0, spec.time)
	play.tween_callback(burst.queue_free)


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
	if not state_machine.is_recovering():
		return 0
	var allowed := punches.allow(amount, hits_this_window, MAX_HITS_PER_WINDOW)
	if allowed <= 0:
		return 0
	var dealt := _apply_damage(allowed)
	if dealt > 0:
		hits_this_window += 1
		punches.spend(dealt)
	return dealt


# No phase floor: he has one move and no transformation, so nothing may hold his health up. `pitch` is
# the juggle's, a step up each uppercut.
func _apply_damage(amount: int, pitch := 1.0) -> int:
	var dealt := mini(amount, boss_health)
	if dealt <= 0:
		return 0

	boss_health -= dealt
	_refresh_health_bar()
	_hit_feedback()
	hit_sfx_player.pitch_scale = pitch
	hit_sfx_player.play()

	if boss_health > 0:
		state_machine.flinch()
	else:
		# area_entered fires mid physics flush; deferring keeps the state Exit/Enter code the defeat
		# sequence runs from having to be flush-safe.
		call_deferred("_on_defeated")
	return dealt


# The player's finisher (PlayerFinisher). Only his recovery can be dazed, once per window, and with
# break_only_finisher only a Break's.
func can_be_dazed() -> bool:
	return not defeated and boss_health > 0 and not daze_used and state_machine.is_recovering() \
		and (not break_only_finisher or state_machine.current_state.from_break)


# The three-bar mash and the juggle are a Break's payout alone: a window cashed from one. Every other
# window pays the plain single-bar finisher.
func can_be_juggled() -> bool:
	return not defeated and boss_health > 0 and state_machine.is_recovering() and state_machine.current_state.from_break


func enter_daze() -> void:
	daze_used = true


func exit_daze(_finisher_landed: bool) -> void:
	pass


func end_recovery(stagger_time: float) -> bool:
	if defeated or boss_health <= 0:
		return false
	# Crashed from a juggle, he lies a beat before he gets up.
	if is_juggled():
		state_machine.current_state.recover(stagger_time)
		return true
	if not state_machine.is_recovering():
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


# The tiered finisher's juggle (PlayerFinisher, CarterJuggled).
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
	return _apply_damage(amount, pitch)


func get_juggle_point() -> Vector2:
	return state_machine.states["Juggled"].air_point()


# The last uppercut's shove. His feet really move - the classic finisher's rock is on sprite.offset,
# the offset the juggle's lift rewrites - and stay inside the ropes, and never back onto the player.
func juggle_knock_back(push: Vector2, time: float) -> void:
	var bounds: Rect2 = state_machine.ROPES.grow(-state_machine.BREAK_ROPE_MARGIN)
	var target := (global_position + push).clamp(bounds.position, bounds.end)
	var player := get_tree().current_scene.get_node_or_null(FightOutro.PLAYER_PATH)
	if player and target.distance_to(player.global_position) < global_position.distance_to(player.global_position):
		return
	create_tween().tween_property(self, "global_position", target, time).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)


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


# Asked by FightOutro before his line, after on_player_defeated() has started his pose. When he has
# won, the line waits for the whole of it - the burn, the light coming back, the look over his
# shoulder - so it lands after the pose like a win quote instead of the fade eating the head turn.
# When he has lost there is no pose, so it asks for nothing and the line comes at the usual time -
# unless a juggle killed him, when the line waits for him to finish falling.
func outro_line_delay(player_won: bool) -> float:
	if player_won:
		return CarterArtLayout.juggle().outro_delay if is_juggled() else 0.0
	return state_machine.states["Victory"].pose_length()


# Asked by FightOutro when the player presses through that wait: the pose ends at once, where it would have.
func skip_outro_pose() -> void:
	var victory = state_machine.states["Victory"]
	if state_machine.current_state == victory:
		victory.finish_pose()


# Whoever won, nothing he has sent out may stay live.
func _clear_hazards() -> void:
	for hazard in get_tree().get_nodes_in_group(state_machine.HAZARD_GROUP):
		hazard.queue_free()


# The bar goes hot in two steps: caution under 0.66 of his health, then the last third.
func _refresh_health_bar() -> void:
	if not health_bar:
		return
	health_bar.set_value(0, boss_health)
	var ratio := get_health_ratio()
	var heat := 0.0
	if ratio <= 0.34:
		heat = 1.0
	elif ratio <= 0.66:
		heat = 0.5
	health_bar.set_heat(0, heat)


func _build_hud() -> void:
	hud_layer = CanvasLayer.new()
	add_child(hud_layer)

	health_bar = BossHealthBarUI.create({
		"rows": [{"key": &"carter", "max": max_health, "value": boss_health}],
		"plate": &"carter",
		"text": GameProgress.boss_name(FIGHT_SCENE),
	})
	hud_layer.add_child(health_bar)

	if break_gauge:
		break_gauge_bar = BreakGaugeUI.new()
		break_gauge_bar.gauge = break_gauge
		# Set before it is added: BreakGaugeUI reads it in _ready and falls back to Eric's otherwise.
		break_gauge_bar.spec = CarterArtLayout.break_gauge()
		hud_layer.add_child(break_gauge_bar)
		break_gauge_bar.position = health_bar.break_gauge_anchor()


func _hit_feedback() -> void:
	if not sprite:
		return

	sprite.modulate = Color(3, 3, 3)
	var flash_tween = create_tween()
	flash_tween.tween_property(sprite, "modulate", Color(1, 1, 1), 0.15)
	shake_sprite(5.0, 4, 0.025)

	HitStop.freeze(get_tree(), 0.06)
