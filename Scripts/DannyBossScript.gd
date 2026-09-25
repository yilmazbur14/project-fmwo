extends CharacterBody2D

# Danny, boss 7 ("@helper", FIGHT 07): the training room's tiny helper, who evolves FireRed-style into an
# E. Honda sumo. His loop is a worm spit that leaves puddles to root the player in (DannyBossSpit), then a
# five-slam Sumo Smash string (DannyBossSlams), then a nap that heals him and is the window to punish him in
# (DannyBossSleep). A player his worms root gets his Sumo Headbutt (DannyBossHeadbutt), and a parried one
# leaves him dizzy (DannyBossStaggered). Reads fill his Break gauge, which opens the Break's finisher
# (DannyBossBroken). At 0 HP the fight isn't over: he gets up, blocks the gate and the player has to win a
# sumo push to get past him (DannyBossSumo). This node is his body, his health, his art, his sounds and his
# HUD.
#
# His origin is his feet (DannyBossArtLayout), and `sprite` stays the body sprite whatever he is doing:
# PlayerFinisher and PlayerCombo both write to it. Its offset follows the sheet, never the animation
# (_stand_on), with his lift on top of it (set_lift).

# A non-looping animation reached the end of its last frame.
signal anim_finished(anim_name: StringName)

const HitStop := preload("res://Scripts/HitStop.gd")
const FightOutro := preload("res://Scripts/FightOutro.gd")
const BossHealthBarUI := preload("res://Scripts/BossHealthBarUI.gd")
const BossBreakGauge := preload("res://Scripts/BossBreakGauge.gd")
const BreakGaugeUI := preload("res://Scripts/BreakGaugeUI.gd")
const Layout := preload("res://Scripts/DannyBossArtLayout.gd")
const UI_THEME := preload("res://Assets/UI/ui_theme.tres")
# What he says once the fight is over, under player_won and player_lost.
const OUTRO_DIALOGUE := "res://Dialogue/DannyBossOutro.dialogue"
# This fight's place in the order: it is also the entrance's once-per-run key and the name the health bar
# is looked up under.
const FIGHT_SCENE := "res://Scenes/Bosses/DannyBossFightScene.tscn"
# Flat white for the evolve's flash (set_white), mixed over his own colours without touching their alpha.
const WHITE_SHADER := """shader_type canvas_item;
uniform float white : hint_range(0.0, 1.0) = 0.0;
void fragment() {
	vec4 c = texture(TEXTURE, UV) * COLOR;
	COLOR = vec4(mix(c.rgb, vec3(1.0), white), c.a);
}
"""

#CONSTANTS
# A knob. The single-bar finisher takes 12 and the supercharged one 19, and the juggle 7, 5 and 7.
@export var max_health := 48
var boss_health := max_health
# Every window's cap unless its state has its own `hit_cap` (the Sleep's is 6).
const MAX_HITS_PER_WINDOW := 3
# Each opening takes the damage of a clean chain of MAX_HITS_PER_WINDOW punches (PunchAllowance).
const PunchAllowance := preload("res://Scripts/PunchAllowance.gd")
const PHANTOM_HIT_WINDOW := 0.5
const HUD_FADE_TIME := 0.25
# The bar goes to half heat at this share of his health, and to full at the other.
const CAUTION_RATIO := 0.5
const HOT_RATIO := 0.25

#THE BREAK GAUGE (BossBreakGauge)
# The rollout's rule with N = 8: a read (a parry or a perfect dodge of a slam or a headbutt) is an eighth of
# the gauge, a punch a quarter of a read and a charged one a half, a hit taken one read back and a guard
# break two. He has no grab and nothing to reflect. His quake rings drain it but never fill it (BREAK_EARNS).
# broken_time is DannyBossBroken's window. BREAK_READ is max_value over N, given as it is (BREAK_EPSILON).
const BREAK_READS := 8
const BREAK_READ := 100.0 / BREAK_READS
const BREAK := {
	"max_value": 100.0,
	"unlock_delay": 3.0,
	"broken_time": 3.0,
	"parry_gain": BREAK_READ,
	"grab_parry_gain": 0.0,
	"reflect_gain": 0.0,
	"perfect_dodge_gain": BREAK_READ,
	"punch_gain": BREAK_READ / 4.0,
	"charged_punch_gain": BREAK_READ / 2.0,
	"hit_loss": BREAK_READ,
	"guard_break_loss": 2.0 * BREAK_READ,
}
const BREAK_EARNS: Array[StringName] = [&"danny_butt_slam", &"danny_headbutt"]
# The Break's three-bar mash and juggle, on the shared BossBroken and BossJuggled (DannyBossBroken,
# DannyBossJuggled). Off, a Break pays the plain single-bar finisher.
const JUGGLE_ENABLED := true

#UI (BossHealthBarUI and BreakGaugeUI build it at runtime)
var hud_layer: CanvasLayer
var health_bar: Control
var gauge_bar: Control
var hud_fade: Tween
var break_gauge: Node
# The hints: the live ones by key, and every key shown this fight.
var hints := {}
var hints_shown := {}

# Under both fighters: the puddles, the slam's cracks, the dust.
@export var floor_layer: Node2D
# The quake rings, y-sorted with the fighters.
@export var ring_layer: Node2D
# The globs, the badges' anchors, the impact's burst and the "+N" labels, on their own z over both fighters.
@export var projectile_layer: Node2D

@onready var sprite: Sprite2D = $Sprite2D
@onready var animation_player: AnimationPlayer = $AnimationPlayer
@onready var hurtbox: Area2D = $Hurtbox
@onready var state_machine = $StateManager

#AUDIO
@onready var music_player: AudioStreamPlayer = $MusicPlayer
@onready var hit_sfx_player: AudioStreamPlayer = $HitSfxPlayer
@onready var victory_sfx_player: AudioStreamPlayer = $VictorySfxPlayer
# Built from DannyBossArtLayout.SFX: each key's players, rotated on every play.
var sfx_players := {}
# How many times his theme has been started and restarted, for the tests to prove each is only ever once.
var music_starts := 0
var music_restarts := 0
# His theme's own level, which a duck swings around.
var music_base_db := 0.0
var music_duck: Tween

# Out of the ring for good: only the sumo's end sets it (DannyBossSumo). 0 HP does not.
var defeated := false
var hits_this_window := 0
var punches := PunchAllowance.new()
# One finisher daze per window; the Sleep and the Break clear it.
var daze_used := false

var fight_clock := 0.0
var last_contact_hit_time := -INF

var sprite_base_position: Vector2
# The offset the sheet showing stands his feet on the node with, and how far he is lifted off them in px.
var sheet_offset := Layout.SPRITE_OFFSET
var lift_px := 0.0
var white_material: ShaderMaterial
# Which of Layout.BODY_BOXES his hurtbox is.
var body_box := &"idle"

var current_anim := &""
var anim: Dictionary = {}
var anim_step := 0
var anim_clock := 0.0
var anim_next := &""
var anim_done := false
# What the state he is in shows, which a flinch hands back to.
var state_anim := &""

# His nap's effects, on his own node so they move and flip with him: the Z's at his head, the regen over his
# body, and the "+N" labels still rising.
var zzz: Sprite2D
var regen: Sprite2D
var regen_labels: Array[Node] = []


func _ready() -> void:
	add_to_group(FightOutro.BOSS_GROUP)
	hurtbox.area_entered.connect(_on_hurtbox_entered)
	# The exported value is only set after the variable above was initialised.
	boss_health = max_health

	_apply_art_layout()
	sprite_base_position = sprite.position
	# Before the HUD: the HUD builds the gauge's bar, and only if there is a gauge to draw.
	var scene := get_tree().current_scene
	var player: Node = scene.get_node_or_null(FightOutro.PLAYER_PATH) if scene else null
	if player:
		_add_break_gauge(player)
	_build_hud()
	_build_sfx()
	_load_music()
	hit_sfx_player.stream = load("res://Assets/Audio/SFX/hit_impact.ogg")
	victory_sfx_player.stream = load("res://Assets/Audio/SFX/victory_fanfare.ogg")


func _physics_process(delta: float) -> void:
	fight_clock += delta


func _apply_art_layout() -> void:
	sprite.position = Vector2.ZERO
	sprite.offset = Layout.SPRITE_OFFSET
	sheet_offset = Layout.SPRITE_OFFSET
	set_body_box(&"idle")


func get_health_ratio() -> float:
	return float(boss_health) / float(max_health)


func get_max_health() -> int:
	return max_health


#THE BREAK GAUGE

func _add_break_gauge(player: Node) -> void:
	break_gauge = BossBreakGauge.new()
	break_gauge.name = "BreakGauge"
	break_gauge.boss = self
	break_gauge.player = player
	break_gauge.owns_attack = func(id: StringName) -> bool: return str(id).begins_with("danny_")
	break_gauge.earns_from = func(hit: RefCounted) -> bool: return BREAK_EARNS.has(hit.attack_id)
	break_gauge.max_value = BREAK.max_value
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


func is_broken() -> bool:
	return state_machine.current_state == state_machine.states.get("Broken")


func is_juggled() -> bool:
	return state_machine.current_state == state_machine.states.get("Juggled")


# Down from a Break or a juggle, until he is back on his feet: the gauge's lock waits for this.
func is_down() -> bool:
	return is_broken() or is_juggled()


#MUSIC

func _load_music() -> void:
	var own := ResourceLoader.exists(Layout.THEME)
	music_player.stream = load(Layout.THEME if own else Layout.THEME_FALLBACK)
	music_player.volume_db = Layout.THEME_DB if own else Layout.THEME_FALLBACK_DB
	# His theme loops by its own import; the stand-in has to be told.
	if not own and "loop" in music_player.stream:
		music_player.stream.loop = true
	music_base_db = music_player.volume_db


# Once, whoever asks first: the evolve's landing, the skip past it, or the fight starting.
func start_music() -> void:
	if music_starts > 0 or music_player == null:
		return
	music_starts += 1
	music_player.volume_db = music_base_db
	music_player.play()


# From the top at his own level, once: the sumo's Rise, after the fade at the KO stopped it.
func restart_music() -> void:
	if music_restarts > 0 or music_player == null:
		return
	music_restarts += 1
	if music_duck:
		music_duck.kill()
	music_player.volume_db = music_base_db
	music_player.play(0.0)


# His theme `db` under its own level over `time`, and back with 0. Bound to the player, so a pause holds it.
func duck_music(db: float, time: float) -> void:
	if music_duck:
		music_duck.kill()
	music_duck = music_player.create_tween()
	music_duck.tween_property(music_player, "volume_db", music_base_db + db, time)


# To `db` absolute over `time`, and stopped there when `stop` asks: the KO's fade.
func fade_music(db: float, time: float, stop := false) -> void:
	if music_duck:
		music_duck.kill()
	music_duck = music_player.create_tween()
	music_duck.tween_property(music_player, "volume_db", db, time)
	if stop:
		music_duck.tween_callback(music_player.stop)


#SOUNDS

# Built here rather than wired into the scene: the table in DannyBossArtLayout is the only place they are
# named.
func _build_sfx() -> void:
	for key in Layout.SFX:
		var spec: Dictionary = Layout.SFX[key]
		var stream: AudioStream = load(spec.stream)
		if spec.get("loop", false):
			# Its own copy: the file is shared with fights that play it once.
			stream = stream.duplicate()
			if stream is AudioStreamWAV:
				stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
				stream.loop_end = int(stream.get_length() * stream.mix_rate)
			else:
				stream.loop = true
		var players: Array[AudioStreamPlayer] = []
		for i in Layout.SFX_VOICES.get(key, 1):
			var sfx := AudioStreamPlayer.new()
			sfx.stream = stream
			sfx.volume_db = spec.volume_db
			add_child(sfx)
			players.append(sfx)
		sfx_players[key] = players


func play_sfx(key: StringName, pitch := 1.0) -> void:
	var players: Array = sfx_players.get(key, [])
	if players.is_empty():
		return
	var sfx: AudioStreamPlayer = players.pop_front()
	players.append(sfx)
	sfx.pitch_scale = Layout.SFX[key].pitch * pitch
	sfx.play()


func stop_sfx(key: StringName) -> void:
	for sfx: AudioStreamPlayer in sfx_players.get(key, []):
		sfx.stop()


#ANIMATION

# A non-looping animation holds its last frame when it ends, unless `next_anim` follows it. `loop_time`
# rescales it so one pass over its frames takes that long.
func play_anim(anim_name: StringName, next_anim: StringName = &"", loop_time := 0.0) -> void:
	var spec := Layout.anim(anim_name)
	if loop_time > 0.0:
		spec = Layout.timed(spec, loop_time)
	current_anim = anim_name
	anim = spec
	anim_next = next_anim
	anim_step = 0
	anim_clock = 0.0
	anim_done = false
	var sheet: Texture2D = load(spec.sheet)
	if sheet != sprite.texture:
		# Back to the first frame before the frame count changes, so the current one can't be out of range.
		sprite.frame = 0
		sprite.texture = sheet
		sprite.hframes = roundi(sheet.get_width() / Layout.frame_size(spec).x)
		_stand_on(Layout.sheet_offset(spec))
	animation_player.play(spec.get("motion", &"RESET"))
	_show_anim_frame()


# A state's own animation. A one-shot still playing finishes first and hands over to it - a flinch back
# into the nap - while a loop gives way at once.
func play_state_anim(anim_name: StringName) -> void:
	state_anim = anim_name
	if not anim.is_empty() and not anim.loop and not anim_done:
		anim_next = anim_name
		return
	play_anim(anim_name)


# Only a sheet that stands on a different offset from the one it replaces writes it: the finisher's recoil
# and hop rock sprite.offset and settle it back, and BossJuggled owns it from the juggle's first frame until
# it restores the sheet and offset it found, so a swap between two sheets on the same offset leaves it be.
# His lift rides on whichever offset is showing.
func _stand_on(offset: Vector2) -> void:
	if offset == sheet_offset:
		return
	sheet_offset = offset
	sprite.offset = offset - Vector2(0, lift_px / Layout.SCALE)


# Lifted `px` off his feet, the sprite alone: his node, hurtbox and y-sort stay on the ground under him.
func set_lift(px: float) -> void:
	lift_px = px
	sprite.offset = sheet_offset - Vector2(0, px / Layout.SCALE)


# Flat white by `t`, for the evolve's flash; at 0 the material comes off altogether.
func set_white(t: float) -> void:
	if t <= 0.0:
		sprite.material = null
		return
	if white_material == null:
		var shader := Shader.new()
		shader.code = WHITE_SHADER
		white_material = ShaderMaterial.new()
		white_material.shader = shader
	white_material.set_shader_parameter("white", clampf(t, 0.0, 1.0))
	sprite.material = white_material


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
	sprite.frame = anim.frames[anim_step]


# Whole and upright on his feet, facing the way he was drawn: unlifted, his own colours, on his own z.
func show_body() -> void:
	sprite.visible = true
	sprite.flip_h = false
	sprite.rotation = 0.0
	sprite.modulate = Color.WHITE
	sprite.z_index = 0
	set_white(0.0)
	set_lift(0.0)


# The lines' squash while one of his is typing, on whichever sheet is showing, the small form's included:
# only the AnimationPlayer's clip, so no frame or sheet changes under it. play_anim() puts its own clip back.
func set_talking(talking: bool) -> void:
	var squashing: bool = animation_player.current_animation == "talk"
	if talking and not squashing:
		animation_player.play(&"talk")
	elif not talking and squashing:
		animation_player.play(&"RESET")


# His sheets face screen-right unflipped, the way every flip in this game reads.
func face_toward(point: Vector2) -> void:
	if point.x != global_position.x:
		sprite.flip_h = point.x < global_position.x


#WHERE THINGS ARE ON HIM (world px, mirrored with him, and lifted with him)

func crown_point(anim_name := current_anim) -> Vector2:
	return _drawn(Layout.crown(anim_name), anim_name)


# Where a badge's tip stands over him in `anim_name`'s pose.
func tell_anchor(anim_name := current_anim) -> Vector2:
	return crown_point(anim_name) + Vector2(0, -Layout.TELL_GAP)


# His open mouth on the frame a glob leaves it.
func mouth_point(anim_name := &"spit_fire") -> Vector2:
	return _drawn(Layout.mouth(anim_name), anim_name)


# His rear's contact texel on the slam's impact frame.
func contact_point(anim_name := &"slam_impact") -> Vector2:
	return _drawn(Layout.contact(anim_name), anim_name)


# The front of his head in the headbutt, which is what reaches the player.
func head_point(anim_name := &"headbutt_fly") -> Vector2:
	return _drawn(Layout.head(anim_name), anim_name)


# His hands' contact in the push.
func hand_point(anim_name := &"push_strain") -> Vector2:
	return _drawn(Layout.hand(anim_name), anim_name)


# Where the Z's rise from his sleeping head.
func snore_point(anim_name := &"sleep") -> Vector2:
	return _drawn(Layout.snore(anim_name), anim_name)


func _drawn(texel: Vector2, anim_name: StringName) -> Vector2:
	return global_position + Layout.texel_local(texel, anim_name, sprite.flip_h) - Vector2(0, lift_px)


#HIS HURTBOX

# One of Layout.BODY_BOXES: `idle` standing, `sleep` slumped in his nap, `headbutt` the torpedo in flight.
# Mirrored as he faces now, so a state that turns him sets it again after.
func set_body_box(key: StringName) -> void:
	body_box = key
	var box := _facing_box(key)
	var shape: CollisionShape2D = hurtbox.get_node("CollisionShape2D")
	shape.position = box.get_center()
	(shape.shape as RectangleShape2D).size = box.size


# One of Layout.BODY_BOXES in world px as it would stand on him now, without making it his hurtbox: the box a
# spot beside him is worked out from before the state that sets it has started (the nudge beside his nap).
func body_box_rect(key: StringName) -> Rect2:
	var box := _facing_box(key)
	box.position += global_position
	return box


func _facing_box(key: StringName) -> Rect2:
	var box := Layout.body_rect(key)
	if sprite.flip_h:
		box.position.x = -box.end.x
	return box


# His hurtbox as it stands, in world px.
func hurtbox_rect() -> Rect2:
	var shape: CollisionShape2D = hurtbox.get_node("CollisionShape2D")
	return shape.global_transform * shape.shape.get_rect()


# Punches only reach him in his windows. The hurtbox keeps its groups the whole fight, so the player still
# faces him whatever he is doing.
func set_hurtbox_active(active: bool) -> void:
	# Deferred: monitoring can't change inside a physics flush.
	hurtbox.set_deferred("monitoring", active)
	hurtbox.set_deferred("monitorable", active)


#THE PARRY'S STAGGER (PlayerDefense asks the body; the state he is in answers)

func can_parry_stagger(hit: RefCounted) -> bool:
	var state = state_machine.current_state
	return state != null and state.has_method("can_parry_stagger") and state.can_parry_stagger(hit)


func parry_stagger(duration: float) -> void:
	var state = state_machine.current_state
	if state != null and state.has_method("parry_stagger"):
		state.parry_stagger(duration)


#THE HUD

# A badge over his crown in `anim_name`'s pose, from the top of the ring, is inside the boss bar: the bar and
# the gauge under it fade while it is there and come back as it leaves.
func update_hud_fade(anim_name := current_anim) -> void:
	update_hud_fade_at(tell_anchor(anim_name))


# The same for any point: the badge over a slam's marked spot, or him in the air.
func update_hud_fade_at(point: Vector2) -> void:
	_fade_hud(state_machine.hud_fade_alpha if state_machine.HUD_FADE_RECT.has_point(point) else 1.0)


func restore_hud() -> void:
	_fade_hud(1.0)


# The bar and the gauge gone over `time`: the KO's false victory.
func hide_boss_hud(time: float) -> void:
	_fade_hud(0.0, time)


# His bar drained to empty and greyed out as dead: the KO, before hide_boss_hud() takes it away.
func finish_health_bar() -> void:
	if health_bar:
		health_bar.finish_row(0)


# Bound to the bar itself, so a pause or a finisher's freeze holds it with the fight.
func _fade_hud(alpha: float, time := HUD_FADE_TIME) -> void:
	if not health_bar:
		return
	if hud_fade:
		hud_fade.kill()
	if is_equal_approx(health_bar.modulate.a, alpha):
		return
	hud_fade = health_bar.create_tween().set_parallel()
	for bar: Control in [health_bar, gauge_bar]:
		if bar:
			hud_fade.tween_property(bar, "modulate:a", alpha, time)


# The hint for `key`, bottom centre on his HUD layer. Once a fight, whoever asks again.
func show_hint(key: StringName, text: String) -> void:
	if hints_shown.has(key) or hud_layer == null:
		return
	hints_shown[key] = true
	var spec: Dictionary = Layout.HINT
	var label := Label.new()
	label.theme = UI_THEME
	label.text = text
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.vertical_alignment = VERTICAL_ALIGNMENT_BOTTOM
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.add_theme_font_size_override("font_size", spec.font_size)
	label.add_theme_constant_override("outline_size", spec.outline)
	label.add_theme_color_override("font_color", spec.color)
	label.add_theme_color_override("font_outline_color", spec.outline_color)
	label.size = Vector2(spec.width, spec.font_size * 3.0)
	label.position = Vector2((get_viewport().get_visible_rect().size.x - spec.width) / 2.0, spec.bottom - label.size.y)
	label.modulate.a = 0.0
	hud_layer.add_child(label)
	hints[key] = label
	var fade := label.create_tween()
	fade.tween_property(label, "modulate:a", 1.0, spec.fade)


func hide_hint(key: StringName) -> void:
	# Untyped: a freed label can't be held in a typed variable long enough to ask about it.
	var label = hints.get(key)
	hints.erase(key)
	if not is_instance_valid(label):
		return
	var fade: Tween = label.create_tween()
	fade.tween_property(label, "modulate:a", 0.0, Layout.HINT.fade)
	fade.tween_callback(label.queue_free)


func add_player_hype(amount: float) -> void:
	var player: Node = state_machine.get_player()
	var hype: Node = player.get_node_or_null("Hype") if player else null
	if hype:
		hype.add(amount)


#HIS NAP (DannyBossSleep, and his nap after a win)

# The Z's rising from his head, looping, flipped with him.
func show_zzz(shown: bool) -> void:
	if not shown:
		if is_instance_valid(zzz):
			zzz.queue_free()
		zzz = null
		return
	if is_instance_valid(zzz):
		return
	zzz = _looping_fx(&"sleep_z")
	zzz.position = to_local(snore_point(state_anim if state_anim != &"" else &"sleep"))
	zzz.flip_h = sprite.flip_h
	zzz.offset = Layout.flipped_offset(Layout.fx(&"sleep_z").offset, zzz.flip_h)


# The green regen over his body, on his own frame and feet, while he is healing.
func show_regen(shown: bool) -> void:
	if not shown:
		if is_instance_valid(regen):
			regen.queue_free()
		regen = null
		return
	if is_instance_valid(regen):
		return
	regen = _looping_fx(&"regen")
	regen.flip_h = sprite.flip_h


# `amount` back, whole HP, never past max_health, in silent ticks on the bar. What it actually healed.
func heal(amount: int) -> int:
	var healed := mini(amount, max_health - boss_health)
	if healed <= 0:
		return 0
	boss_health += healed
	_refresh_health_bar()
	return healed


# A green "+N" rising off his crown, freed once it has faded.
func pop_regen_label(amount: int) -> void:
	var spec: Dictionary = Layout.REGEN_LABEL
	var label := Label.new()
	label.theme = UI_THEME
	label.text = "+%d" % amount
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.add_theme_font_size_override("font_size", spec.font_size)
	label.add_theme_constant_override("outline_size", spec.outline)
	label.add_theme_color_override("font_color", spec.color)
	label.add_theme_color_override("font_outline_color", spec.outline_color)
	label.size = Vector2(120, spec.font_size * 1.5)
	projectile_layer.add_child(label)
	var at: Vector2 = crown_point() - Vector2(label.size.x / 2.0, label.size.y + spec.gap)
	label.global_position = at.round()
	for i in range(regen_labels.size() - 1, -1, -1):
		if not is_instance_valid(regen_labels[i]):
			regen_labels.remove_at(i)
	regen_labels.append(label)
	var rise := label.create_tween().set_parallel()
	rise.tween_property(label, "global_position:y", at.y - spec.rise, spec.time)
	rise.tween_property(label, "modulate:a", 0.0, spec.fade).set_delay(spec.time - spec.fade)
	rise.chain().tween_callback(label.queue_free)


# Every nap effect gone at once: a Break, a juggle or the end of the fight.
func clear_nap_fx() -> void:
	show_zzz(false)
	show_regen(false)
	for label in regen_labels:
		if is_instance_valid(label):
			label.queue_free()
	regen_labels.clear()


# One of his FX sheets looping on a sprite of his own, drawn over his body.
func _looping_fx(key: StringName) -> Sprite2D:
	var spec: Dictionary = Layout.fx(key)
	var fx := Sprite2D.new()
	fx.texture = load(spec.texture)
	fx.hframes = spec.hframes
	fx.offset = spec.offset
	fx.scale = Vector2.ONE * Layout.SCALE
	fx.z_index = 1
	add_child(fx)
	var play := fx.create_tween().set_loops()
	for i in spec.hframes:
		play.tween_callback(fx.set_frame.bind(i))
		play.tween_interval(spec.frame_time)
	return fx


#COMBAT

func _on_hurtbox_entered(area: Area2D) -> void:
	if boss_health <= 0 or not area.is_in_group("player attack"):
		return
	# Same phantom-hit filter as Matt: a punch that connects as its hitbox switches on is reported again
	# when PlayerPunching switches the hitbox off, which would eat the hit cap.
	if not area.monitorable and fight_clock - last_contact_hit_time < PHANTOM_HIT_WINDOW:
		return
	if area.get_parent().combo.resolve_punch(self) > 0 and area.monitorable:
		last_contact_hit_time = fight_clock


func take_punch(amount: int) -> int:
	if boss_health <= 0 or not state_machine.is_open():
		return 0
	var allowed := punches.allow(amount, hits_this_window, window_hit_cap())
	if allowed <= 0:
		return 0
	var dealt := _apply_damage(allowed)
	if dealt > 0:
		hits_this_window += 1
		punches.spend(dealt)
	return dealt


# The window he is in: its own `hit_cap` if it has one.
func window_hit_cap() -> int:
	var state = state_machine.current_state
	if state != null and "hit_cap" in state:
		return state.hit_cap
	return MAX_HITS_PER_WINDOW


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
		# area_entered fires mid physics flush; deferring keeps the state Exit/Enter code the sumo's start
		# runs from having to be flush-safe.
		call_deferred("_on_zero_health")
	return dealt


# The player's finisher (PlayerFinisher): a charged third punch in his nap or the Break dazes him, once a
# window. Never in Staggered.
func can_be_dazed() -> bool:
	return not defeated and boss_health > 0 and not daze_used and (state_machine.is_sleeping() or is_broken())


# The finisher draws its own daze stars over the Break's.
func enter_daze() -> void:
	daze_used = true
	_show_break_stars(false)


func exit_daze(finisher_landed: bool) -> void:
	if not finisher_landed:
		_show_break_stars(true)


func _show_break_stars(shown: bool) -> void:
	if is_broken() and state_machine.current_state.has_method("show_stars"):
		state_machine.current_state.show_stars(shown)


func end_recovery(stagger_time: float) -> bool:
	if defeated or boss_health <= 0:
		return false
	# Crashed from a juggle, he lies a beat before he gets up.
	if is_juggled():
		if state_machine.current_state.has_method("recover"):
			state_machine.current_state.recover(stagger_time)
		return true
	if is_broken():
		state_machine.end_break(stagger_time)
		return true
	# The uppercut ends his nap: up, staggered, then his next attack.
	if state_machine.is_sleeping():
		state_machine.stagger_then_start_cycle(stagger_time)
		return true
	return false


# Past the hit cap, which the combo that led to it has used up.
func take_finisher(amount: int) -> int:
	if not state_machine.is_open():
		return 0
	return _apply_damage(amount)


func get_daze_anchor() -> Vector2:
	return crown_point(&"broken" if is_broken() else &"sleep") + Vector2(0, -Layout.DAZE_GAP)


func get_finisher_hurtbox() -> Area2D:
	return hurtbox


#THE JUGGLE (PlayerFinisher's tiered uppercut, Mason's names; only the Break pays it)

func can_be_juggled() -> bool:
	return JUGGLE_ENABLED and not defeated and boss_health > 0 and is_broken()


func begin_juggle() -> void:
	state_machine.enter_juggled()


func juggle_lift(px: float) -> void:
	if is_juggled() and state_machine.current_state.has_method("lift"):
		state_machine.current_state.lift(px)


func juggle_pose(pose: StringName, crater := false) -> void:
	if is_juggled() and state_machine.current_state.has_method("pose"):
		state_machine.current_state.pose(pose, crater)


func juggle_headroom() -> float:
	var juggled: Node = state_machine.states.get("Juggled")
	return juggled.headroom() if juggled and juggled.has_method("headroom") else 0.0


# Past the hit cap, as take_finisher, with his hit sound pitched up a step each uppercut.
func take_juggle_hit(amount: int, pitch: float) -> int:
	return _apply_damage(amount, pitch)


func get_juggle_point() -> Vector2:
	var juggled: Node = state_machine.states.get("Juggled")
	return juggled.air_point() if juggled and juggled.has_method("air_point") else get_daze_anchor()


# The last uppercut's shove, along his ground line, inside his walk area and never toward the player. He has
# no knock_back(), so the nap's single-bar finisher rocks his sprite instead.
func juggle_knock_back(push: Vector2, time: float) -> void:
	var walk: Rect2 = state_machine.WALK_RECT
	var target := (global_position + push).clamp(walk.position, walk.end)
	var player: Node2D = state_machine.get_player()
	if player and target.distance_to(player.global_position) < global_position.distance_to(player.global_position):
		return
	create_tween().tween_property(self, "global_position", target, time).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)


# The fight is only decided at the end of the sumo, long after any juggle has landed.
func outro_line_delay(_player_won: bool) -> float:
	return 0.0


#THE END OF THE FIGHT

# 0 HP is not the end: he gets up and blocks the gate (DannyBossStateMachine.enter_sumo). Nothing here may
# end the fight or set the player's fight_over, which would stop the sumo's poses (PlayerPosed.hold_pose):
# only the sumo's result calls FightOutro.
func _on_zero_health() -> void:
	set_hurtbox_active(false)
	state_machine.enter_sumo()


# Called by FightOutro when the player loses.
func on_player_defeated() -> void:
	state_machine.enter_player_defeated()


# Half heat at CAUTION_RATIO of his health, full at HOT_RATIO.
func _refresh_health_bar() -> void:
	if not health_bar:
		return
	health_bar.set_value(0, boss_health)
	var ratio := get_health_ratio()
	var heat := 0.0
	if ratio <= HOT_RATIO:
		heat = 1.0
	elif ratio <= CAUTION_RATIO:
		heat = 0.5
	health_bar.set_heat(0, heat)


func _build_hud() -> void:
	hud_layer = CanvasLayer.new()
	add_child(hud_layer)
	health_bar = BossHealthBarUI.create({
		"rows": [{"key": &"danny", "max": max_health, "value": boss_health}],
		"plate": &"danny",
		"text": GameProgress.boss_name(FIGHT_SCENE),
	})
	hud_layer.add_child(health_bar)
	if break_gauge:
		gauge_bar = BreakGaugeUI.new()
		gauge_bar.gauge = break_gauge
		hud_layer.add_child(gauge_bar)
		gauge_bar.position = health_bar.break_gauge_anchor()


func _hit_feedback() -> void:
	sprite.modulate = Color(3, 3, 3)
	var flash_tween := create_tween()
	flash_tween.tween_property(sprite, "modulate", Color(1, 1, 1), 0.15)

	var shake_tween := create_tween()
	for i in 4:
		var offset := Vector2(randf_range(-5, 5), randf_range(-5, 5)).round()
		shake_tween.tween_property(sprite, "position", sprite_base_position + offset, 0.025)
	shake_tween.tween_property(sprite, "position", sprite_base_position, 0.025)

	HitStop.freeze(get_tree(), 0.06)
