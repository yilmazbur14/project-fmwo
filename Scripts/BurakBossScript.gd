extends CharacterBody2D

# Captain Burak, boss 1 and the tutorial: the real Burak fused with Gangplank, cocky and forgiving. Each of
# his three attacks teaches one answer, and each lives in its own state: a pistol pair that teaches the
# parry (BurakBossShots), five powder kegs to punch before he has loaded (BurakBossBarrels), and a cutlass
# string only a parry or a timed dash answers (BurakBossCutlass). After the kegs he taunts, which is his
# punish window (BurakBossTaunt). Parries fill his Break gauge, which opens the Break's finisher
# (BurakBossBroken). This node is his body, his health, his art, his sounds, his HUD and his bullet timer.
#
# His origin is his feet (BurakBossArtLayout), and `sprite` stays the body sprite whatever he is doing:
# PlayerFinisher and PlayerCombo both write to it. Its offset follows the sheet, never the animation
# (_stand_on).

# A non-looping animation reached the end of its last frame.
signal anim_finished(anim_name: StringName)

const HitStop := preload("res://Scripts/HitStop.gd")
const FightOutro := preload("res://Scripts/FightOutro.gd")
const BossHealthBarUI := preload("res://Scripts/BossHealthBarUI.gd")
const BossBreakGauge := preload("res://Scripts/BossBreakGauge.gd")
const BreakGaugeUI := preload("res://Scripts/BreakGaugeUI.gd")
const Layout := preload("res://Scripts/BurakBossArtLayout.gd")
const BurakBossPips := preload("res://Scripts/BurakBossPips.gd")
const UI_THEME := preload("res://Assets/UI/ui_theme.tres")
# What he says once the fight is over, under player_won and player_lost.
const OUTRO_DIALOGUE := "res://Dialogue/BurakBossOutro.dialogue"
# This fight's place in the order: it is also the entrance's once-per-run key and the name the health bar
# is looked up under.
const FIGHT_SCENE := "res://Scenes/Bosses/BurakBossFightScene.tscn"

#CONSTANTS
# 75 (the user doubled it from 30, 2026-09-25, then raised it 25%, 2026-09-30), half a heart a punch and
# three punches a window: a player who never parries but finishes every Taunt deals 23 a window (1 + 1 + 2
# from the punches, 19 from the finisher), so the kegs are met four times: at the bottom of their ramp,
# 0.38 and 0.77 of the way up it, and at the top.
@export var max_health := 75
var boss_health := max_health
const MAX_HITS_PER_WINDOW := 3
# Each opening takes the damage of a clean chain of MAX_HITS_PER_WINDOW punches (PunchAllowance).
const PunchAllowance := preload("res://Scripts/PunchAllowance.gd")
const PHANTOM_HIT_WINDOW := 0.5
const HUD_FADE_TIME := 0.25
# The bar goes to half heat at this share of his health, and to full at the ramp's cap
# (BurakBossStateMachine.CAP_RATIO).
const CAUTION_RATIO := 0.6

#THE BREAK GAUGE (BossBreakGauge)
# A parry counter. A parried shot is exactly half of it and a parried swing exactly a third, so two parried
# shots, or three parried swings, in a row always Break him: 30 + 30 and 20 + 20 + 20 are exact in floats.
# Those gains come through his own Defense.parried connection (PARRY_GAINS), since they differ per attack,
# and every gain of the gauge's own is 0. Being hit costs one swing's worth and a guard break two, through
# the gauge's own drains, so a hit between two parries breaks up the pair: the user's rule for every fight.
# broken_time is BurakBossBroken's window.
const BREAK := {
	"max_value": 60.0,
	"unlock_delay": 1.0,
	"broken_time": 3.0,
	"parry_gain": 0.0,
	"grab_parry_gain": 0.0,
	"reflect_gain": 0.0,
	"perfect_dodge_gain": 0.0,
	"punch_gain": 0.0,
	"charged_punch_gain": 0.0,
	"hit_loss": 20.0,
	"guard_break_loss": 40.0,
}
const PARRY_GAINS := {&"burak_shot": 30.0, &"burak_cutlass": 20.0}
# The attacks this fight owns, for the gauge's drains.
const ATTACK_IDS: Array[StringName] = [&"burak_shot", &"burak_barrel_blast", &"burak_cutlass"]
# The Break's three-bar mash and juggle, on the shared BossBroken and BossJuggled (BurakBossBroken,
# BurakBossJuggled). Off, a Break pays the plain single-bar finisher.
const JUGGLE_ENABLED := true

#UI (BossHealthBarUI and BreakGaugeUI build it at runtime)
var hud_layer: CanvasLayer
var health_bar: Control
var gauge_bar: Control
var hud_fade: Tween
var break_gauge: Node
# His bullet timer, on his projectile layer (BurakBossPips).
var pips: Node2D
# The tutorial's hints: the live ones by key, and every key shown this fight.
var hints := {}
var hints_shown := {}

# The keg's landing dust and the debris, one px below the top of the floor, under both fighters.
@export var floor_layer: Node2D
# The kegs, y-sorted with the fighters.
@export var barrel_layer: Node2D
# His balls, blasts, slashes and pips, on their own z over both fighters.
@export var projectile_layer: Node2D

@onready var sprite: Sprite2D = $Sprite2D
@onready var animation_player: AnimationPlayer = $AnimationPlayer
@onready var hurtbox: Area2D = $Hurtbox
@onready var state_machine = $StateManager

#AUDIO
@onready var music_player: AudioStreamPlayer = $MusicPlayer
@onready var hit_sfx_player: AudioStreamPlayer = $HitSfxPlayer
@onready var victory_sfx_player: AudioStreamPlayer = $VictorySfxPlayer
# Built from BurakBossArtLayout.SFX: each key's players, rotated on every play.
var sfx_players := {}
# How many times his theme has been started, for the entrance's skip to prove it is only ever once.
var music_starts := 0
# His theme's own level, which a duck swings around.
var music_base_db := 0.0
var music_duck: Tween

var defeated := false
var hits_this_window := 0
var punches := PunchAllowance.new()
# One finisher daze per window; the Taunt and the Break clear it.
var daze_used := false

var fight_clock := 0.0
var last_contact_hit_time := -INF

var sprite_base_position: Vector2
# The offset the sheet showing stands his feet on the node with.
var sheet_offset := Layout.SPRITE_OFFSET

var current_anim := &""
var anim: Dictionary = {}
var anim_step := 0
var anim_clock := 0.0
var anim_next := &""
var anim_done := false
# What the state he is in shows, which a flinch hands back to.
var state_anim := &""
var talk_pose := &""
var talk_flapping := false


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
	_build_pips()
	_load_music()
	hit_sfx_player.stream = load("res://Assets/Audio/SFX/hit_impact.ogg")
	victory_sfx_player.stream = load("res://Assets/Audio/SFX/victory_fanfare.ogg")


func _physics_process(delta: float) -> void:
	fight_clock += delta


func _apply_art_layout() -> void:
	sprite.position = Vector2.ZERO
	sprite.offset = Layout.SPRITE_OFFSET
	sheet_offset = Layout.SPRITE_OFFSET
	var box := Layout.body_rect()
	var hurtbox_shape: CollisionShape2D = hurtbox.get_node("CollisionShape2D")
	hurtbox_shape.position = box.get_center()
	(hurtbox_shape.shape as RectangleShape2D).size = box.size


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
	break_gauge.owns_attack = func(id: StringName) -> bool: return ATTACK_IDS.has(id)
	break_gauge.max_value = BREAK.max_value
	break_gauge.unlock_delay = BREAK.unlock_delay
	break_gauge.parry_gain = BREAK.parry_gain
	break_gauge.grab_parry_gain = BREAK.grab_parry_gain
	break_gauge.reflect_gain = BREAK.reflect_gain
	break_gauge.perfect_dodge_gain = BREAK.perfect_dodge_gain
	break_gauge.punch_gain = BREAK.punch_gain
	break_gauge.charged_punch_gain = BREAK.charged_punch_gain
	break_gauge.hit_loss = BREAK.hit_loss
	break_gauge.guard_break_loss = BREAK.guard_break_loss
	add_child(break_gauge)
	break_gauge.broke.connect(_on_break)
	player.get_node("Defense").parried.connect(_on_parried)


# A parried shot or swing is worth its exact share (PARRY_GAINS); the parry that fills the gauge breaks
# him, mid-attack if need be.
func _on_parried(hit: RefCounted, _contact_point: Vector2, _staggered: bool, _streak: int) -> void:
	if break_gauge:
		break_gauge.add(PARRY_GAINS.get(hit.attack_id, 0.0))


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


# Once, whoever asks first: his warning shot, the skip past it, or the fight starting.
func start_music() -> void:
	if music_starts > 0 or music_player == null:
		return
	music_starts += 1
	music_player.play()


# His theme `db` under its own level over `time`, and back with 0. Bound to the player, so a pause holds it.
func duck_music(db: float, time: float) -> void:
	if music_duck:
		music_duck.kill()
	music_duck = music_player.create_tween()
	music_duck.tween_property(music_player, "volume_db", music_base_db + db, time)


#SOUNDS

# Built here rather than wired into the scene: the table in BurakBossArtLayout is the only place they are
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
# rescales it so one pass over its frames takes that long: one bullet of `load`, at the attack's pace.
func play_anim(anim_name: StringName, next_anim: StringName = &"", loop_time := 0.0) -> void:
	var spec := Layout.anim(anim_name)
	if loop_time > 0.0:
		spec = Layout.timed(spec, loop_time)
	_play_spec(anim_name, spec, next_anim)


# A state's own animation. A one-shot still playing finishes first and hands over to it - a flinch back
# into the taunt - while a loop gives way at once.
func play_state_anim(anim_name: StringName) -> void:
	state_anim = anim_name
	if not anim.is_empty() and not anim.loop and not anim_done:
		anim_next = anim_name
		return
	play_anim(anim_name)


# One of the lines' poses: its mouth flapping while he talks, shut while he doesn't.
func show_talk(pose: StringName, flapping: bool) -> void:
	if current_anim == &"talk" and talk_pose == pose and talk_flapping == flapping:
		return
	talk_pose = pose
	talk_flapping = flapping
	var spec := Layout.talk(pose)
	var frames: Array = spec.frames if flapping else [spec.frames[0]]
	_play_spec(&"talk", {sheet = spec.sheet, frames = frames, times = [Layout.TALK_FRAME_TIME], loop = true,
		motion = spec.motion if flapping else &"RESET"})


func _play_spec(anim_name: StringName, spec: Dictionary, next_anim: StringName = &"") -> void:
	current_anim = anim_name
	anim = spec
	anim_next = next_anim
	anim_step = 0
	anim_clock = 0.0
	anim_done = false
	if anim_name != &"talk":
		talk_pose = &""
	var sheet: Texture2D = load(spec.sheet)
	if sheet != sprite.texture:
		# Back to the first frame before the frame count changes, so the current one can't be out of range.
		sprite.frame = 0
		sprite.texture = sheet
		sprite.hframes = roundi(sheet.get_width() / Layout.frame_size(spec).x)
		_stand_on(Layout.sheet_offset(spec))
	animation_player.play(spec.get("motion", &"RESET"))
	_show_anim_frame()


# Only a sheet that stands on a different offset from the one it replaces writes it: the finisher's recoil
# and hop rock sprite.offset and settle it back, and BossJuggled owns it from the juggle's first frame until
# it restores the sheet and offset it found, so a swap between two sheets on the same offset leaves it be.
func _stand_on(offset: Vector2) -> void:
	if offset == sheet_offset:
		return
	sheet_offset = offset
	sprite.offset = offset


func _process(delta: float) -> void:
	fade_hints_over_player()
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


# Whole and upright on his feet, facing the way he was drawn.
func show_body() -> void:
	sprite.visible = true
	sprite.flip_h = false
	sprite.rotation = 0.0
	sprite.modulate = Color.WHITE


# His sheets face screen-right unflipped, the way every flip in this game reads.
func face_toward(point: Vector2) -> void:
	if point.x != global_position.x:
		sprite.flip_h = point.x < global_position.x


#WHERE THINGS ARE ON HIM (world px, mirrored with him)

func crown_point(anim_name := current_anim) -> Vector2:
	return global_position + Layout.texel_local(Layout.crown(anim_name), anim_name, sprite.flip_h)


# Where a badge's tip stands over him in `anim_name`'s pose.
func tell_anchor(anim_name := current_anim) -> Vector2:
	return crown_point(anim_name) + Vector2(0, -Layout.TELL_GAP)


# The pistol's muzzle on the frame the ball leaves on.
func muzzle_point(anim_name := &"fire") -> Vector2:
	return global_position + Layout.texel_local(Layout.muzzle(anim_name), anim_name, sprite.flip_h)


# His hand on the frame a keg leaves it.
func release_point(anim_name := &"throw") -> Vector2:
	return global_position + Layout.texel_local(Layout.release(anim_name), anim_name, sprite.flip_h)


# What swing k (0 side, 1 backhand, 2 overhead) hits, in world px, facing the way he does.
func slash_box(k: int) -> Rect2:
	var box: Rect2 = Layout.SLASH_BOXES[k]
	if sprite.flip_h:
		box.position.x = -box.end.x
	box.position += global_position
	return box


#THE HUD

# His badge stands over his crown, and from the top of the ring that is inside the boss bar: the bar and
# the gauge under it fade while he is there and come back as he leaves.
func update_hud_fade(anim_name := current_anim) -> void:
	if state_machine.HUD_FADE_RECT.has_point(tell_anchor(anim_name)):
		_fade_hud(state_machine.hud_fade_alpha)
	else:
		_fade_hud(1.0)


func restore_hud() -> void:
	_fade_hud(1.0)


# Bound to the bar itself, so a pause or a finisher's freeze holds it with the fight.
func _fade_hud(alpha: float) -> void:
	if not health_bar:
		return
	if hud_fade:
		hud_fade.kill()
	if is_equal_approx(health_bar.modulate.a, alpha):
		return
	hud_fade = health_bar.create_tween().set_parallel()
	for bar: Control in [health_bar, gauge_bar]:
		if bar:
			hud_fade.tween_property(bar, "modulate:a", alpha, HUD_FADE_TIME)


# The tutorial's hint for `key`, bottom centre on his HUD layer. Once a fight, whoever asks again.
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


# The hints sit across the bottom of the ring, right where the player starts the fight and the parry hint
# comes up: while the player is under one it goes see-through, as his bar does over his badge, so it never
# hides them (playtest 2026-10-04). self_modulate, so the show and hide fades on modulate run as they were.
func fade_hints_over_player() -> void:
	if hints.is_empty():
		return
	var player: Node2D = state_machine.get_player()
	if player == null:
		return
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	var body: Rect2 = get_viewport().get_canvas_transform() * (shape.global_transform * shape.shape.get_rect())
	for label in hints.values():
		if is_instance_valid(label):
			label.self_modulate.a = state_machine.hud_fade_alpha if label.get_global_rect().intersects(body) else 1.0


#THE BULLET TIMER (BurakBossPips)

func _build_pips() -> void:
	pips = BurakBossPips.new()
	pips.name = "Pips"
	projectile_layer.add_child(pips)
	pips.global_position = state_machine.HOME + Layout.PIPS_OFFSET


func show_pips(count: int) -> void:
	pips.show_pips(count)


func load_pip(index: int) -> void:
	pips.load_pip(index)


func spend_pip() -> void:
	pips.spend_pip()


func fade_pips() -> void:
	pips.fade_pips()


func hide_pips() -> void:
	pips.hide_pips()


func add_player_hype(amount: float) -> void:
	var player: Node = state_machine.get_player()
	var hype: Node = player.get_node_or_null("Hype") if player else null
	if hype:
		hype.add(amount)


#COMBAT

# Punches only reach him in his windows. The hurtbox keeps its groups the whole fight, so the player still
# faces him whatever he is doing.
func set_hurtbox_active(active: bool) -> void:
	# Deferred: monitoring can't change inside a physics flush.
	hurtbox.set_deferred("monitoring", active)
	hurtbox.set_deferred("monitorable", active)


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


# The player's finisher (PlayerFinisher): a charged third punch in the Taunt or the Break dazes him, once
# a window.
func can_be_dazed() -> bool:
	return not defeated and boss_health > 0 and not daze_used and state_machine.is_open()


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
	if state_machine.is_taunting():
		state_machine.stagger_then_start_cycle(stagger_time)
		return true
	return false


# Past the hit cap, which the combo that led to it has used up.
func take_finisher(amount: int) -> int:
	if not state_machine.is_open():
		return 0
	return _apply_damage(amount)


func get_daze_anchor() -> Vector2:
	return crown_point(&"broken" if is_broken() else &"taunt") + Vector2(0, -Layout.DAZE_GAP)


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


# The last uppercut's shove, along his ground line, inside his walk area and never toward the player. He
# has no knock_back(), so the Taunt's single-bar finisher rocks his sprite instead.
func juggle_knock_back(push: Vector2, time: float) -> void:
	var walk: Rect2 = state_machine.WALK_RECT
	var target := (global_position + push).clamp(walk.position, walk.end)
	var player: Node2D = state_machine.get_player()
	if player and target.distance_to(player.global_position) < global_position.distance_to(player.global_position):
		return
	create_tween().tween_property(self, "global_position", target, time).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)


# A juggle that kills him ends with him still in the air: the outro's first line waits until he has landed.
func outro_line_delay(_player_won: bool) -> float:
	return Layout.juggle().outro_delay if is_juggled() else 0.0


#THE END OF THE FIGHT

func _on_defeated() -> void:
	defeated = true
	set_hurtbox_active(false)
	state_machine.enter_defeated()
	if music_player.playing:
		music_player.stop()
	victory_sfx_player.play()
	get_tree().call_group("arena_crowd", "cheer", 2.0)
	GameProgress.next_boss_scene = GameProgress.next_fight_after(FIGHT_SCENE)
	FightOutro.finish_fight(get_tree(), true)


# Called by FightOutro when the player loses.
func on_player_defeated() -> void:
	state_machine.enter_player_defeated()


# Half heat at CAUTION_RATIO of his health, full at the ramp's cap.
func _refresh_health_bar() -> void:
	if not health_bar:
		return
	health_bar.set_value(0, boss_health)
	var ratio := get_health_ratio()
	var heat := 0.0
	if ratio <= state_machine.CAP_RATIO:
		heat = 1.0
	elif ratio <= CAUTION_RATIO:
		heat = 0.5
	health_bar.set_heat(0, heat)


func _build_hud() -> void:
	hud_layer = CanvasLayer.new()
	add_child(hud_layer)
	health_bar = BossHealthBarUI.create({
		"rows": [{"key": &"burak", "max": max_health, "value": boss_health}],
		"plate": &"burak",
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
