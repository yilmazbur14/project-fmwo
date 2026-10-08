extends CharacterBody2D

# A non-looping animation reached the end of its last frame.
signal anim_finished(anim_name: StringName)

const HitStop := preload("res://Scripts/HitStop.gd")
const FightOutro := preload("res://Scripts/FightOutro.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const BixbyBeastArtLayout := preload("res://Scripts/BixbyBeastArtLayout.gd")
const BossHealthBarUI := preload("res://Scripts/BossHealthBarUI.gd")
const BossBreakGauge := preload("res://Scripts/BossBreakGauge.gd")
const BreakGaugeUI := preload("res://Scripts/BreakGaugeUI.gd")
# What Liam says once the fight is over, under player_won and player_lost.
const OUTRO_DIALOGUE := "res://Dialogue/LiamOutro.dialogue"
# His fight's place in the order; GameProgress decides what follows it.
const FIGHT_SCENE := "res://Scenes/Bosses/LiamBossFightScene.tscn"
# The fight's second half: beaten, he coughs Liam up and Liam takes the fight over in a scene of his own (LiamTakeover),
# whose end is the fight's. With liam_follows off, it ends at his defeat as it always has.
const LIAM_SCENE := "res://Scenes/Bosses/LiamScene.tscn"
# Where the boss select's LIAM row finds him down (start_at_liam).
const LIAM_START_FEET := Vector2(882, 770)
@export var liam_follows := true

#CONSTANTS
# The user doubled it from 16 (2026-09-25), then raised it 25% (2026-09-30); 70 in the tuning round of 2026-10-04
# (difficulty 7): with the finisher a share of it, four windows, two loops of his attacks.
@export var max_health := 70
var boss_health := max_health
const MAX_HITS_PER_WINDOW := 3
# Each opening takes the damage of a clean chain of MAX_HITS_PER_WINDOW punches (PunchAllowance).
const PunchAllowance := preload("res://Scripts/PunchAllowance.gd")
const PHANTOM_HIT_WINDOW := 0.5
const VIEW_SIZE := Vector2(1920, 1080)
const HOVER_HEIGHT_PX := BixbyBeastArtLayout.HOVER_HEIGHT * BixbyBeastArtLayout.SCALE
# He eases into and out of every move: his speed never changes faster than FLY_ACCELERATION px/s², and
# over the last stretch he slows down as if FLY_ARRIVE_TIME seconds away.
const FLY_ARRIVE_TIME := 0.25
const FLY_ACCELERATION := 2600.0
# Flying sideways faster than this turns the fly frames to face the way he's going.
const FLY_TURN_SPEED := 60.0

#BREAK GAUGE (BossBreakGauge, and BossBroken's window)
# The rule every fight after Mason's is on: 8 clean reads from empty are a guaranteed Break. A parry or a
# perfect dodge is one read, a hit taken costs one and a guard break two, and a landed punch is a quarter of
# one, a charged one half, so a 3-punch combo is one read. Nothing of his is a grab or comes back at him, so
# the grab and reflect gains are the plain read and never paid. BREAK_READ is BossBreakGauge's max_value of
# 100 over N, given as it is (BREAK_EPSILON).
const BREAK_READS := 8
const BREAK_READ := 100.0 / BREAK_READS
const BREAK := {
	"parry_gain": BREAK_READ,
	"grab_parry_gain": BREAK_READ,
	"reflect_gain": BREAK_READ,
	"perfect_dodge_gain": BREAK_READ,
	"punch_gain": BREAK_READ / 4.0,
	"charged_punch_gain": BREAK_READ / 2.0,
	"hit_loss": BREAK_READ,
	"guard_break_loss": 2.0 * BREAK_READ,
	"unlock_delay": 3.0,
	"broken_time": 3.0,
}
# What fills it: not the Inferno's fireballs, too many to a shower for each to be a read, nor its embers or
# the floor his Flyby leaves burning, which lie still. Anything of his that lands drains it.
const BREAK_EARNING_IDS: Array[StringName] = [&"bixby_flyby_breath", &"bixby_sonic_beam", &"bixby_quake_ring", &"bixby_inferno"]

#UI (BossHealthBarUI builds it at runtime)
var health_bar: Control
var hud_layer: CanvasLayer
var break_gauge: Node
var gauge_bar: Control
# How long the bar takes to fade as he takes the rope, and to come back as he leaves it.
const HUD_FADE_TIME := 0.25
var hud_fade: Tween

# Kept under a node that y-sorts at the top edge of the arena floor, so it's drawn under every
# character wherever it goes, rather than over the feet of a player standing just behind him.
@export var shadow: Sprite2D
@onready var air: Node2D = $Air
@onready var sprite: Sprite2D = $Air/Sprite2D
@onready var hurtbox: Area2D = $Air/Hurtbox
@onready var state_machine = $StateManager

#AUDIO
# His own theme. Same level as the rest of the ladder, so moving between fights does not jump.
const THEME := "res://Assets/Audio/Music/liam_theme.wav"
const THEME_DB := -7.0

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
@onready var inhale_sfx_player: AudioStreamPlayer = $InhaleSfxPlayer
@onready var spit_sfx_player: AudioStreamPlayer = $SpitSfxPlayer
@onready var rope_sfx_player: AudioStreamPlayer = $RopeSfxPlayer

var defeated := false
var hits_this_window := 0
var punches := PunchAllowance.new()
# One finisher daze per recovery; Recover clears it.
var daze_used := false

var fight_clock := 0.0
var last_contact_hit_time := -INF

var sprite_base_position: Vector2
# The last shudder started (shake_sprite).
var sprite_shake: Tween

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


func _ready() -> void:
	add_to_group(FightOutro.BOSS_GROUP)
	hurtbox.area_entered.connect(_on_hurtbox_entered)
	# The exported value is only set after the variable above was initialised.
	boss_health = max_health

	sprite_base_position = sprite.position
	ground_position = global_position
	_apply_art_layout()
	var player := get_tree().current_scene.get_node_or_null(FightOutro.PLAYER_PATH)
	if player:
		_add_break_gauge(player)
	_build_hud()

	# "Carried In, Swallowed Whole", written for this fight - see art_source/music/liam_theme.rb.
	# One 16-bar cycle cut to the beat, so LOOP_FORWARD runs it end to end with no seam.
	music_player.stream = load(THEME)
	music_player.volume_db = THEME_DB
	if music_player.stream is AudioStreamWAV:
		music_player.stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
		music_player.stream.loop_begin = 0
		music_player.stream.loop_end = int(music_player.stream.get_length() * music_player.stream.mix_rate)
	elif music_player.stream:
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
	# The Inferno's placeholders. The inhale loops, and load() hands back the one whoosh the breath and the
	# wings play as well, so it loops on a copy of its own.
	var inhale: AudioStreamOggVorbis = load("res://Assets/Audio/SFX/whirlwind_whoosh.ogg").duplicate()
	inhale.loop = true
	inhale_sfx_player.stream = inhale
	spit_sfx_player.stream = load("res://Assets/Audio/SFX/rocket_launch.ogg")
	rope_sfx_player.stream = load("res://Assets/Audio/SFX/wrestler_collision.ogg")


func _add_break_gauge(player: Node) -> void:
	break_gauge = BossBreakGauge.new()
	break_gauge.name = "BreakGauge"
	break_gauge.boss = self
	break_gauge.player = player
	break_gauge.owns_attack = func(id: StringName) -> bool: return String(id).begins_with("bixby_")
	break_gauge.earns_from = _earns_break
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


func _earns_break(hit: RefCounted) -> bool:
	return BREAK_EARNING_IDS.has(hit.attack_id)


# The gauge fills inside physics flushes and his own physics steps, where his states can't switch.
func _on_break() -> void:
	state_machine.enter_broken.call_deferred()


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
	_fit_hurtbox(BixbyBeastArtLayout.RECOVER_BODY_BOX)


# The hurtbox on `texel_box` of his frames: the one the player punches in his windows, and faces the rest
# of the time.
func _fit_hurtbox(texel_box: Rect2) -> void:
	var box := BixbyBeastArtLayout.local_rect(texel_box)
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


# The frame of `sheet` on screen right now, or -1 if that isn't the sheet he's drawing.
func drawn_frame_of(sheet: String) -> int:
	return sprite.frame if anim.get("sheet", "") == sheet else -1


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
# to the same bounds his own flight uses.
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


# The Inferno: on the middle of the top rope with his feet at `feet`, facing down over the ring. His floor
# point goes up to the rope line, so he sorts behind everyone on the mat, which puts his feet below it: his
# height is negative, and there is no floor under him to cast a shadow on. The boss bar, its plate and its
# Break gauge sit over the middle of the rope, so they fade while he is there.
func perch_on_rope(feet: Vector2) -> void:
	var rope_y: float = state_machine.ROPES.position.y
	ground_position = Vector2(feet.x, rope_y)
	height = rope_y - feet.y
	fly_velocity = Vector2.ZERO
	shadow.hide()
	place()
	_fit_hurtbox(BixbyBeastArtLayout.PERCH_BODY_BOX)
	_fade_hud(state_machine.inferno_hud_fade_alpha)


# He lets go of the rope, dropping `drop` px: hovering at his usual height over the floor under his feet,
# the HUD and his grounded hurtbox back. Every way out of the Inferno comes through here (its Exit()), so
# nothing leaves the HUD faded.
func leave_rope(drop := 0.0) -> void:
	var feet := feet_position() + Vector2(0, drop)
	height = HOVER_HEIGHT_PX
	ground_position = feet + Vector2(0, height)
	shadow.show()
	place()
	_fit_hurtbox(BixbyBeastArtLayout.RECOVER_BODY_BOX)
	_fade_hud(1.0)


# The Flyby (BixbyBeastFlyby): on a pass along the top of the ring with his feet, his anchor, at `anchor`. His floor
# point goes up to the rope line, as on the perch, so he sorts behind everyone on the mat with a negative height, and
# there is no floor under him for a shadow.
func place_on_pass(anchor: Vector2) -> void:
	var rope_y: float = state_machine.ROPES.position.y
	ground_position = Vector2(anchor.x, rope_y)
	height = rope_y - anchor.y
	fly_velocity = Vector2.ZERO
	shadow.hide()
	place()


# Off a pass, or off the top of the screen: hovering at his usual height with his feet where they are, his shadow and
# the HUD back. Every way out of the Flyby comes through here (its release()), so nothing leaves them faded.
func end_pass() -> void:
	var feet := feet_position()
	height = HOVER_HEIGHT_PX
	ground_position = feet + Vector2(0, height)
	shadow.modulate.a = BixbyBeastArtLayout.SHADOW_ALPHA
	shadow.show()
	place()
	set_hud_faded(false)


func set_hud_faded(faded: bool) -> void:
	_fade_hud(state_machine.inferno_hud_fade_alpha if faded else 1.0)


# Bound to the bar itself, so a pause or a finisher's freeze holds it with the fight.
func _fade_hud(alpha: float) -> void:
	if not health_bar:
		return
	if hud_fade:
		hud_fade.kill()
	hud_fade = health_bar.create_tween().set_parallel()
	hud_fade.tween_property(health_bar, "modulate:a", alpha, HUD_FADE_TIME)
	if gauge_bar:
		hud_fade.tween_property(gauge_bar, "modulate:a", alpha, HUD_FADE_TIME)


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


#EFFECTS

func shake_screen(strength: float, steps: int, step_time: float) -> void:
	ScreenView.shake(get_tree(), strength, steps, step_time)


# Shudders the drawn body in whole pixels; his hitboxes and shadow stay put.
func shake_sprite(strength: float, steps: int, step_time: float) -> void:
	var tween := sprite.create_tween()
	sprite_shake = tween
	for i in steps:
		var offset := Vector2(randf_range(-strength, strength), randf_range(-strength, strength)).round()
		tween.tween_callback(func() -> void: sprite.position = sprite_base_position + offset)
		tween.tween_interval(step_time)
	tween.tween_callback(func() -> void: sprite.position = sprite_base_position)


# A Break cuts a shudder short, so nothing jitters the pose it cuts to.
func stop_sprite_shake() -> void:
	if sprite_shake:
		sprite_shake.kill()
	sprite.position = sprite_base_position


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


# Punches only land in his punish windows (BixbyBeastStateMachine.is_recovering), all of them on the ground.
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


# The player's finisher (PlayerFinisher). Only a punish window can be dazed, once per window.
func can_be_dazed() -> bool:
	return not defeated and boss_health > 0 and not daze_used and state_machine.is_recovering()


# The finisher draws its own daze stars over Broken's.
func enter_daze() -> void:
	daze_used = true
	if is_broken():
		state_machine.current_state.show_stars(false)


func exit_daze(finisher_landed: bool) -> void:
	if is_broken() and not finisher_landed:
		state_machine.current_state.show_stars(true)


# Ended by the finisher. Crashed from a juggle, he lies a beat before he gets up; out of any other window
# he stays down, staggered, and takes off after it.
func end_recovery(stagger_time: float) -> bool:
	if defeated or boss_health <= 0:
		return false
	if is_juggled():
		state_machine.current_state.recover(stagger_time)
		return true
	if not state_machine.is_recovering():
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


func is_broken() -> bool:
	return state_machine.current_state == state_machine.states.get("Broken")


func is_juggled() -> bool:
	return state_machine.current_state == state_machine.states.get("Juggled")


# Down from a Break or a juggle, until he is back up: the gauge waits for this.
func is_down() -> bool:
	return is_broken() or is_juggled()


# The three-bar mash and the juggle are the Break's payout alone: the juggle's shares of his 40 health
# would end the fight inside two ordinary windows.
func can_be_juggled() -> bool:
	return not defeated and boss_health > 0 and is_broken()


# The tiered finisher's juggle (PlayerFinisher).
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


# A juggle that kills him ends with him still in the air. His own outro waits for Liam to be coughed up
# anyway (Defeated), long after he has landed, so this only matters if that ever changes.
func outro_line_delay(_player_won: bool) -> float:
	if is_juggled():
		return BixbyBeastArtLayout.juggle().outro_delay
	return 0.0


func _on_defeated() -> void:
	defeated = true
	set_hurtbox_active(false)
	state_machine.enter_defeated()
	clear_hazards()

	if music_player.playing:
		music_player.stop()
	victory_sfx_player.play()
	get_tree().call_group("arena_crowd", "cheer", 2.0)


# Called by Defeated once the coughed-up Liam has landed, so the win lines come after it - or, with Liam taking the
# fight over, his takeover.
func finish_victory() -> void:
	if liam_follows and ResourceLoader.exists(LIAM_SCENE):
		_hand_to_liam()
		return
	GameProgress.next_boss_scene = GameProgress.next_fight_after(FIGHT_SCENE)
	FightOutro.finish_fight(get_tree(), true)


#LIAM'S TAKEOVER

# Beaten, but the fight isn't over: Liam takes it over, and its end is his from here. So Bixby leaves the boss group -
# FightOutro would otherwise play his lines and tell him the player lost - and the target group, so the player's
# punches and facing stop looking for him.
func _hand_to_liam() -> void:
	remove_from_group(FightOutro.BOSS_GROUP)
	hurtbox.remove_from_group("boss_target")
	var scene: Node = load(LIAM_SCENE).instantiate()
	scene.get_node("LiamCharacterBody").bixby = self
	get_parent().add_sibling(scene)
	GameProgress.reach_phase(GameProgress.PHASE_LIAM)


# The main menu's LIAM row (GameProgress.start_at_liam, taken by BixbyBeastStateMachine._ready): the fight opens with
# him already beaten, on his defeat's last frame with Liam coughed up, and Liam takes it over from there. His intro is
# never entered, so the defeat comes on from no state at all. outro_started keeps Defeated from handing over a second
# time when it sees the frame Liam lands on.
func start_at_liam() -> void:
	appear(LIAM_START_FEET)
	defeated = true
	boss_health = 0
	# Down before the first frame is drawn: an empty bar, not a hit draining it.
	if health_bar:
		health_bar.set_value(0, 0, BossHealthBarUI.HIT_SILENT)
	_refresh_health_bar()
	set_hurtbox_active(false)
	state_machine.enter_defeated()
	state_machine.states["Defeated"].outro_started = true
	play_anim(&"defeat", &"", BixbyBeastArtLayout.ANIMS[&"defeat"].frames.size() - 1)
	_hand_to_liam()


# Called by FightOutro when the player loses.
func on_player_defeated() -> void:
	state_machine.enter_player_defeated()
	clear_hazards()


# Whoever won, or once he's Broken, no fire and nothing he's sent out may stay live.
func clear_hazards() -> void:
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


# The gulp in his entrance (BixbyBeastIntro): from here on the bar carries the beast rather than the
# man who was riding him, so the name stays a pair and the fill changes hands.
func swallow_liam() -> void:
	if health_bar:
		health_bar.set_accent(0, &"bixby")


func _build_hud() -> void:
	hud_layer = CanvasLayer.new()
	add_child(hud_layer)

	health_bar = BossHealthBarUI.create({
		"rows": [{"key": &"liam", "max": max_health, "value": boss_health}],
		"plate": &"liam_pair",
		"text": "LIAM & BIXBY",
	})
	hud_layer.add_child(health_bar)

	if break_gauge:
		gauge_bar = BreakGaugeUI.new()
		gauge_bar.gauge = break_gauge
		hud_layer.add_child(gauge_bar)
		gauge_bar.position = health_bar.break_gauge_anchor()


func _hit_feedback() -> void:
	if not sprite:
		return

	sprite.modulate = Color(3, 3, 3)
	var flash_tween = create_tween()
	flash_tween.tween_property(sprite, "modulate", Color(1, 1, 1), 0.15)
	shake_sprite(5.0, 4, 0.025)

	HitStop.freeze(get_tree(), 0.06)
