extends CharacterBody2D

# Matt, boss 4: a loud human Exploud, and his voice is his weapon. His first attack is the Ezreal set -
# a teleporting volley of bouncing bolts, four golden waves from the four sides of the ring, then a
# punish window he may yell his way out of. Each part lives in its own state (MattMysticVolley,
# MattTrueshotBarrage, MattSpent, MattRecover), and this node is his body, his health, his art, his
# sounds and the one tween that throws the player across the ring.
#
# His origin is his feet (MattArtLayout), and `sprite` stays the body sprite whatever he is doing:
# PlayerFinisher and PlayerCombo both write to it, and its offset is never set per animation.

# A non-looping animation reached the end of its last frame.
signal anim_finished(anim_name: StringName)

const HitStop := preload("res://Scripts/HitStop.gd")
const FightOutro := preload("res://Scripts/FightOutro.gd")
const BossHealthBarUI := preload("res://Scripts/BossHealthBarUI.gd")
const BossBreakGauge := preload("res://Scripts/BossBreakGauge.gd")
const BreakGaugeUI := preload("res://Scripts/BreakGaugeUI.gd")
const MattArtLayout := preload("res://Scripts/MattArtLayout.gd")
const ScreenWobble := preload("res://Scripts/ScreenWobble.gd")
# What he says once the fight is over, under player_won and player_lost.
const OUTRO_DIALOGUE := "res://Dialogue/MattOutro.dialogue"
# This fight's place in the order. The final path from the start: it is also the entrance's
# once-per-run key and the name the health bar is looked up under.
const FIGHT_SCENE := "res://Scenes/Bosses/MattBossFightScene.tscn"

#CONSTANTS
# 90 (the user doubled it from 36, 2026-09-25, then raised it 25%, 2026-09-30), one half-heart a punch. Every
# finisher pays a share of max_health, so his length is how many windows and Breaks he gives, not this.
@export var max_health := 90
# A punish window's POW dazes him for the finisher, as every fight's does. Off is Carter's Break-only rule, his for
# a day (2026-10-04) until the user took it out of every fight but Jordan's kaiju (2026-10-05): the knob stays.
@export var daze_in_recover := true
var boss_health := max_health
const MAX_HITS_PER_WINDOW := 3
# Each opening takes the damage of a clean chain of MAX_HITS_PER_WINDOW punches (PunchAllowance).
const PunchAllowance := preload("res://Scripts/PunchAllowance.gd")
const PHANTOM_HIT_WINDOW := 0.5
const HUD_FADE_TIME := 0.25
# The Break gauge, in BossBreakGauge's own names: BREAK_READS clean reads from empty are a Break. 8 before the Echo
# Roars, 23 while a Break was his only finisher; 18 since (2026-10-05), a bonus about once a fight now that an
# Echo instance alone hands a good reader about 18 reads. A parry or a perfect dodge is a read, a punch a quarter and
# a charged one a half, a hit taken one read back and a guard break two. He has no grab and nothing to reflect, so a grab parry is just a read and a reflect
# nothing. broken_time is BossBroken's window.
# BREAK_READ is BossBreakGauge's max_value of 100 over N, given as it is (BREAK_EPSILON).
const BREAK_READS := 18
const BREAK_READ := 100.0 / BREAK_READS
const BREAK := {
	"parry_gain": BREAK_READ,
	"grab_parry_gain": BREAK_READ,
	"reflect_gain": 0.0,
	"perfect_dodge_gain": BREAK_READ,
	"punch_gain": BREAK_READ / 4.0,
	"charged_punch_gain": BREAK_READ / 2.0,
	"hit_loss": BREAK_READ,
	"guard_break_loss": 2.0 * BREAK_READ,
	"unlock_delay": 3.0,
	"broken_time": 3.0,
}
# His attacks whose parries and perfect dodges fill the gauge, one read each (_earns_read). Every attack
# of his drains it. The Glass Row's booms are answered, never parried, and pay hype instead. An Echo ring
# parried, or a BOOMBURST dashed through, is a read; a ghost is never hit and a punish never answered.
const BREAK_READ_IDS: Array[StringName] = [&"matt_mystic_shot", &"matt_trueshot", &"matt_yell", &"matt_echo", &"matt_boomburst"]
# Set on a bolt's, a wave's or a yell ring's hit source once it has paid its read.
const READ_PAID := &"matt_read_paid"

#UI (BossHealthBarUI builds it at runtime)
var hud_layer: CanvasLayer
var health_bar: Control
# His Break gauge's bar, hung under the health bar.
var gauge_bar: Control
var hud_fade: Tween
# Filled by reading him; full, it breaks him (MattStateMachine.enter_broken).
var break_gauge: Node
# The Deafening Yell's wobble over the arena and under the fight HUD, hidden at 0 (ScreenWobble).
var wobble: Node2D

# The optional ground streaks under his bolts, one px below the top of the floor.
@export var floor_layer: Node2D
# His bolts, waves, rings and aim, on their own z over both fighters.
@export var projectile_layer: Node2D

@onready var sprite: Sprite2D = $Sprite2D
@onready var animation_player: AnimationPlayer = $AnimationPlayer
@onready var hurtbox: Area2D = $Hurtbox
@onready var state_machine = $StateManager

#AUDIO
@onready var music_player: AudioStreamPlayer = $MusicPlayer
@onready var hit_sfx_player: AudioStreamPlayer = $HitSfxPlayer
@onready var victory_sfx_player: AudioStreamPlayer = $VictorySfxPlayer
# Built from MattArtLayout.SFX: each key's players, rotated on every play.
var sfx_players := {}
# How many times his theme has been started, for the entrance's skip to prove it is only ever once.
var music_starts := 0

var defeated := false
var hits_this_window := 0
var punches := PunchAllowance.new()
# One finisher daze per recovery; Recover clears it.
var daze_used := false

var fight_clock := 0.0
var last_contact_hit_time := -INF

var sprite_base_position: Vector2
# The yell's throw, and who it is throwing.
var launch: Tween
var launched_player: Node

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
	var player := get_tree().current_scene.get_node_or_null(FightOutro.PLAYER_PATH)
	if player:
		_add_break_gauge(player)
	_build_hud()
	_build_sfx()
	wobble = ScreenWobble.new()
	wobble.name = "Wobble"
	add_child(wobble)

	music_player.stream = load(MattArtLayout.THEME)
	music_player.volume_db = MattArtLayout.THEME_DB
	if music_player.stream is AudioStreamWAV:
		music_player.stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
		music_player.stream.loop_begin = 0
		music_player.stream.loop_end = int(music_player.stream.get_length() * music_player.stream.mix_rate)
	elif music_player.stream and "loop" in music_player.stream:
		music_player.stream.loop = true
	hit_sfx_player.stream = load("res://Assets/Audio/SFX/hit_impact.ogg")
	victory_sfx_player.stream = load("res://Assets/Audio/SFX/victory_fanfare.ogg")


# Once, whoever asks first: the roar in his entrance, the skip past it, or the fight starting.
func start_music() -> void:
	if music_starts > 0 or music_player == null:
		return
	music_starts += 1
	music_player.play()


func get_health_ratio() -> float:
	return float(boss_health) / float(max_health)


func _physics_process(delta: float) -> void:
	fight_clock += delta


func _apply_art_layout() -> void:
	sprite.position = MattArtLayout.FLOOR_POINT
	sprite.offset = MattArtLayout.SPRITE_OFFSET
	var box := MattArtLayout.local_rect(MattArtLayout.BODY_BOX)
	var hurtbox_shape: CollisionShape2D = hurtbox.get_node("CollisionShape2D")
	hurtbox_shape.position = box.get_center()
	(hurtbox_shape.shape as RectangleShape2D).size = box.size


# Built here rather than wired into the scene, the way EricIntro builds its entrance's: the table in
# MattArtLayout is the only place they are named.
func _build_sfx() -> void:
	for key in MattArtLayout.SFX:
		var spec: Dictionary = MattArtLayout.SFX[key]
		var voices: int = MattArtLayout.SFX_VOICES.get(key, 1)
		var players: Array[AudioStreamPlayer] = []
		for i in voices:
			var sfx := AudioStreamPlayer.new()
			sfx.stream = load(MattArtLayout.sfx_stream(key))
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
	sfx.pitch_scale = MattArtLayout.SFX[key].pitch * pitch
	sfx.play()


func stop_sfx(key: StringName) -> void:
	for sfx: AudioStreamPlayer in sfx_players.get(key, []):
		sfx.stop()


#THE BREAK GAUGE (BossBreakGauge)

func _add_break_gauge(player: Node) -> void:
	break_gauge = BossBreakGauge.new()
	break_gauge.name = "BreakGauge"
	break_gauge.boss = self
	break_gauge.player = player
	break_gauge.owns_attack = func(id: StringName) -> bool: return str(id).begins_with("matt_")
	break_gauge.earns_from = _earns_read
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


# One read a bolt, a Trueshot or a yell, however often it comes back through the player: a bolt flies on
# through a parry and can be parried again on every pass. A Trueshot's burst and its wave share a source.
func _earns_read(hit: RefCounted) -> bool:
	if not BREAK_READ_IDS.has(hit.attack_id) or hit.source.has_meta(READ_PAID):
		return false
	hit.source.set_meta(READ_PAID, true)
	return true


# The gauge fills inside physics flushes and his own physics steps, where his states can't switch.
func _on_break() -> void:
	state_machine.enter_broken.call_deferred()


#ANIMATION

# A non-looping animation holds its last frame when it ends, unless `next_anim` follows it. The layout
# picks the frames, and the entry's AnimationPlayer clip plays under them.
func play_anim(anim_name: StringName, next_anim: StringName = &"") -> void:
	_play_spec(anim_name, MattArtLayout.anim(anim_name), next_anim)


# A state's own animation. A one-shot still playing finishes first and hands over to it - a flinch
# into the recover loop - while a loop gives way at once.
func play_state_anim(anim_name: StringName) -> void:
	state_anim = anim_name
	if not anim.is_empty() and not anim.loop and not anim_done:
		anim_next = anim_name
		return
	play_anim(anim_name)


# One of the lines' poses (MattIntro): its mouth flapping while he talks, shut while he doesn't.
func show_talk(pose: StringName, flapping: bool) -> void:
	if current_anim == &"talk" and talk_pose == pose and talk_flapping == flapping:
		return
	talk_pose = pose
	talk_flapping = flapping
	var spec := MattArtLayout.talk(pose)
	var frames: Array = spec.frames if flapping else [spec.frames[0]]
	_play_spec(&"talk", {sheet = spec.sheet, frames = frames, times = [MattArtLayout.TALK_FRAME_TIME],
		loop = true, motion = spec.motion if flapping else &"RESET"})


func _play_spec(anim_name: StringName, spec: Dictionary, next_anim: StringName = &"") -> void:
	current_anim = anim_name
	anim = spec
	anim_next = next_anim
	anim_step = 0
	anim_clock = 0.0
	anim_done = false
	if anim_name != &"talk":
		talk_pose = &""
	var sheet: Texture2D = load(anim.sheet)
	# Back to the first frame before the frame count changes, so the current one can't be out of range.
	sprite.frame = 0
	sprite.texture = sheet
	sprite.hframes = roundi(sheet.get_width() / MattArtLayout.FRAME_SIZE.x)
	animation_player.play(anim.get("motion", &"RESET"))
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
	sprite.frame = anim.frames[anim_step]


# Whole and upright on his feet, facing the way he was drawn: where every teleport and every ending
# leaves his body.
func show_body() -> void:
	sprite.visible = true
	sprite.flip_h = false
	sprite.rotation = 0.0
	sprite.modulate = Color.WHITE


#WHERE THINGS ARE ON HIM

func mouth_point(anim_name := current_anim) -> Vector2:
	return global_position + MattArtLayout.mouth_offset(anim_name, sprite.flip_h)


# Where a badge's tip stands over him in `anim_name`'s pose.
func tell_anchor(anim_name := current_anim) -> Vector2:
	return global_position + MattArtLayout.tell_offset(anim_name, sprite.flip_h)


#THE TELEPORT
# One sheet, split in two: he squeezes out where he is, and reforms where the attack wants him. There
# is no invisible frame between the halves, so a feet point is all a move needs.

func teleport_out() -> void:
	restore_hud()
	play_anim(&"teleport_out")
	play_sfx(&"teleport_out")
	_teleport_burst()


func teleport_in(feet: Vector2, flip := false) -> void:
	global_position = feet.round()
	sprite.flip_h = flip
	play_anim(&"teleport_in")
	play_sfx(&"teleport_in")
	_teleport_burst()


# A lavender and gold column at his feet, in the hazard group so the end of the fight takes it.
func _teleport_burst() -> void:
	var spec := MattArtLayout.fx(&"teleport")
	var burst: Node2D
	if MattArtLayout.uses_final_fx(&"teleport"):
		var sheet := Sprite2D.new()
		sheet.texture = load(spec.texture)
		sheet.hframes = spec.hframes
		sheet.offset = spec.offset
		sheet.scale = Vector2.ONE * MattArtLayout.SCALE
		burst = sheet
		var play := sheet.create_tween()
		for i in range(1, spec.hframes):
			play.tween_interval(spec.frame_time)
			play.tween_callback(sheet.set_frame.bind(i))
		play.tween_interval(spec.frame_time)
		play.tween_callback(sheet.queue_free)
	else:
		burst = Node2D.new()
		var size: Vector2 = spec.size
		var column := Polygon2D.new()
		column.polygon = PackedVector2Array([Vector2(-size.x / 2.0, -size.y), Vector2(size.x / 2.0, -size.y),
			Vector2(size.x / 2.0, 0.0), Vector2(-size.x / 2.0, 0.0)])
		column.color = spec.color
		burst.add_child(column)
		var core := Polygon2D.new()
		core.polygon = PackedVector2Array([Vector2(-size.x / 6.0, -size.y), Vector2(size.x / 6.0, -size.y),
			Vector2(size.x / 6.0, 0.0), Vector2(-size.x / 6.0, 0.0)])
		core.color = spec.accent
		burst.add_child(core)
		var fade := burst.create_tween().set_parallel()
		fade.tween_property(burst, "modulate:a", 0.0, spec.time)
		fade.tween_property(burst, "scale", Vector2(0.2, 1.1), spec.time)
		fade.chain().tween_callback(burst.queue_free)
	state_machine.add_hazard(burst, global_position, projectile_layer)


#THE HUD
# His badge stands over his crown, and from the top of the ring that is inside the boss bar: the bar
# fades while he is there and comes back as he leaves.

func update_hud_fade(anim_name := current_anim) -> void:
	if state_machine.HUD_FADE_RECT.has_point(tell_anchor(anim_name)):
		_fade_hud(state_machine.hud_fade_alpha)
	else:
		_fade_hud(1.0)


func restore_hud() -> void:
	_fade_hud(1.0)


#THE WOBBLE (the Deafening Yell's, over the arena and the HUD)

func set_wobble(amount: float, time: float) -> void:
	if wobble:
		wobble.set_amount(amount, time)


func clear_wobble() -> void:
	if wobble:
		wobble.clear()


func wobble_amount() -> float:
	return wobble.amount if wobble else 0.0


# Bound to the bar itself, so a pause or a finisher's freeze holds it with the fight. The gauge bar is its
# own node on the HUD layer, not a child of the bar, so it fades alongside.
func _fade_hud(alpha: float) -> void:
	if not health_bar:
		return
	if hud_fade:
		hud_fade.kill()
	if is_equal_approx(health_bar.modulate.a, alpha):
		return
	hud_fade = health_bar.create_tween()
	hud_fade.tween_property(health_bar, "modulate:a", alpha, HUD_FADE_TIME)
	if gauge_bar:
		hud_fade.parallel().tween_property(gauge_bar, "modulate:a", alpha, HUD_FADE_TIME)


#THE YELL'S THROW

# Across the ring to `to`, on rails and on his own clock, so a pause or a freeze holds it. The player is
# sealed off and stood still for it and given back where it lands.
func launch_player(player: Node2D, to: Vector2) -> void:
	cancel_launch()
	launched_player = player
	player.lock_actions_sealed()
	player.set_scripted_pose(true)
	var from: Vector2 = player.global_position
	launch = create_tween()
	launch.tween_method(_step_launch.bind(from, to), 0.0, 1.0, state_machine.yell_launch_time) \
		.set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	launch.tween_callback(_land_launch)


# Whole pixels, so the pixel-art body doesn't shimmer in the air.
func _step_launch(weight: float, from: Vector2, to: Vector2) -> void:
	if is_instance_valid(launched_player):
		launched_player.global_position = from.lerp(to, weight).round()


func _land_launch() -> void:
	var player := launched_player
	launched_player = null
	launch = null
	if is_instance_valid(player):
		player.set_scripted_pose(false)
		player.unlock_actions()


# However the fight ends, nobody is left locked in the air.
func cancel_launch() -> void:
	if launch and launch.is_valid():
		launch.kill()
	launch = null
	_land_launch()


func is_launching() -> bool:
	return launch != null and launch.is_valid()


#COMBAT

# Punches only reach him while he is recovering or Broken. The hurtbox keeps its groups the whole fight,
# so the player still faces him while he teleports around.
func set_hurtbox_active(active: bool) -> void:
	# Deferred: monitoring can't change inside a physics flush.
	hurtbox.set_deferred("monitoring", active)
	hurtbox.set_deferred("monitorable", active)


func _on_hurtbox_entered(area: Area2D) -> void:
	if boss_health <= 0 or not area.is_in_group("player attack"):
		return
	# Same phantom-hit filter as Carter: a punch that connects as its hitbox switches on is reported
	# again when PlayerPunching switches the hitbox off, which would eat the hit cap.
	if not area.monitorable and fight_clock - last_contact_hit_time < PHANTOM_HIT_WINDOW:
		return
	if area.get_parent().combo.resolve_punch(self) > 0 and area.monitorable:
		last_contact_hit_time = fight_clock


func take_punch(amount: int) -> int:
	if boss_health <= 0 or not _is_open():
		return 0
	var allowed := punches.allow(amount, hits_this_window, MAX_HITS_PER_WINDOW)
	if allowed <= 0:
		return 0
	var dealt := _apply_damage(allowed)
	if dealt > 0:
		hits_this_window += 1
		punches.spend(dealt)
		state_machine.punch_landed(hits_this_window)
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


# His punish window, or his Break's.
func _is_open() -> bool:
	return state_machine.is_recovering() or is_broken()


func is_broken() -> bool:
	return state_machine.current_state == state_machine.states.get("Broken")


func is_juggled() -> bool:
	return state_machine.current_state == state_machine.states.get("Juggled")


# Down from a Break or a juggle, until he is back on his feet: the gauge waits for this.
func is_down() -> bool:
	return is_broken() or is_juggled()


# The player's finisher (PlayerFinisher): a charged punch in his Break dazes him, once a window. In his recovery
# only with daze_in_recover, and never while he is yelling.
func can_be_dazed() -> bool:
	if defeated or boss_health <= 0 or daze_used:
		return false
	if is_broken():
		return true
	return daze_in_recover and state_machine.is_recovering() and not state_machine.is_yelling()


# The three-bar mash and the juggle are the Break's payout alone; his recovery pays the plain one-bar
# finisher.
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
	if not state_machine.is_recovering():
		return false
	state_machine.stagger_then_start_cycle(stagger_time)
	return true


# Past the hit cap, which the combo that led to it has used up.
func take_finisher(amount: int) -> int:
	if not _is_open():
		return 0
	return _apply_damage(amount)


func get_max_health() -> int:
	return max_health


func get_daze_anchor() -> Vector2:
	return global_position + MattArtLayout.daze_offset(&"recover")


func get_finisher_hurtbox() -> Area2D:
	return hurtbox


#THE JUGGLE (PlayerFinisher's tiered uppercut, drawn by MattJuggled)

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


# A juggle that kills him ends with him still in the air: the outro's first line waits until he has
# landed.
func outro_line_delay(_player_won: bool) -> float:
	if is_juggled():
		return MattArtLayout.juggle().outro_delay
	return 0.0


# The last uppercut's shove, which moves him for real: the classic finisher's rock is on sprite.offset,
# the offset a juggle's lift rewrites every frame. Never out of where he may stand, and never back onto
# the player.
func juggle_knock_back(push: Vector2, time: float) -> void:
	var stand: Rect2 = state_machine.STAND_RECT
	var target := (global_position + push).clamp(stand.position, stand.end).round()
	var player: Node2D = state_machine.get_player()
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
	GameProgress.next_boss_scene = GameProgress.next_fight_after(FIGHT_SCENE)
	FightOutro.finish_fight(get_tree(), true)


# Called by FightOutro when the player loses.
func on_player_defeated() -> void:
	state_machine.enter_player_defeated()
	_clear_hazards()


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
		"rows": [{"key": &"matt", "max": max_health, "value": boss_health}],
		"plate": &"matt",
		"text": GameProgress.boss_name(FIGHT_SCENE),
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
	var flash_tween := create_tween()
	flash_tween.tween_property(sprite, "modulate", Color(1, 1, 1), 0.15)

	var shake_tween := create_tween()
	for i in 4:
		var offset := Vector2(randf_range(-5, 5), randf_range(-5, 5)).round()
		shake_tween.tween_property(sprite, "position", sprite_base_position + offset, 0.025)
	shake_tween.tween_property(sprite, "position", sprite_base_position, 0.025)

	HitStop.freeze(get_tree(), 0.06)
