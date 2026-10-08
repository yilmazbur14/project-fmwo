extends CharacterBody2D

const HitStop := preload("res://Scripts/HitStop.gd")
const FightOutro := preload("res://Scripts/FightOutro.gd")
const BossHealthBarUI := preload("res://Scripts/BossHealthBarUI.gd")
const BossBreakGauge := preload("res://Scripts/BossBreakGauge.gd")
const BreakGaugeUI := preload("res://Scripts/BreakGaugeUI.gd")
const JordanArtLayout := preload("res://Scripts/JordanArtLayout.gd")
const KaijuLayout := preload("res://Scripts/JordanKaijuLayout.gd")
const FunkoThrow := preload("res://Scripts/JordanFunkoThrow.gd")
# What he says once the fight is over, under player_won and player_lost.
const OUTRO_DIALOGUE := "res://Dialogue/JordanOutro.dialogue"
# This fight's place in the order; as the last one, GameProgress finds nothing after it.
const FIGHT_SCENE := "res://Scenes/Bosses/JordanBossFightScene.tscn"

#CONSTANTS
# Phase 1's health, the whole fight's, doubled from 12 by the user (2026-09-25), then raised 25% (2026-09-30).
@export var max_health := 30
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
# half), and nothing decays. His N is 6, not 8: his fight was about two summon cycles long at the 12
# health it was set on, before the user doubled it (2026-09-25), and eight reads would rarely arrive. A
# figure the player punched back into him is two (take_explosion_hit).
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
# On the kaiju (JordanKaijuLayout.USE_KAIJU) the same rule over its own N (JordanKaijuLayout.BREAK_READS), with the stomp's parry worth two reads
# (grab_parry_gain: strong_parry_ids) and a throw's funko parries one between them (earns_from).
const KAIJU_BREAK_READ := 100.0 / KaijuLayout.BREAK_READS
const KAIJU_BREAK := {
	"parry_gain": KAIJU_BREAK_READ,
	"grab_parry_gain": 2.0 * KAIJU_BREAK_READ,
	"reflect_gain": 2.0 * KAIJU_BREAK_READ,
	"perfect_dodge_gain": KAIJU_BREAK_READ,
	"punch_gain": KAIJU_BREAK_READ / 4.0,
	"charged_punch_gain": KAIJU_BREAK_READ / 2.0,
	"hit_loss": KAIJU_BREAK_READ,
	"guard_break_loss": 2.0 * KAIJU_BREAK_READ,
	"unlock_delay": 3.0,
	"broken_time": 3.0,
}
const STOMP_ID := &"jordan_kaiju_stomp"
const KAIJU_ATTACK_IDS: Array[StringName] = [FunkoThrow.ATTACK_ID, &"jordan_kaiju_breath", &"jordan_burn_line", STOMP_ID,
	&"jordan_kaiju_quake", &"jordan_kaiju_tail"]

#UI (BossHealthBarUI builds it at runtime)
var health_bar: Control
var hud_layer: CanvasLayer
var break_gauge: Node
var gauge_bar: Control
var hud_fade: Tween
var hud_alpha := 1.0

@onready var sprite = $Sprite2D
@onready var animation_player: AnimationPlayer = $AnimationPlayer
@onready var hurtbox: Area2D = $Hurtbox
@onready var state_machine = $StateManager

#AUDIO
# His theme and its level are JordanArtLayout.theme(): his original, "The Last Name on the List" (Neo Tokyo is his
# god fight's since 2026-10-06).
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
# On the kaiju's head: it draws him there (JordanKaiju) and his own sprite is hidden.
var mounted := false
# The throws a funko read has been paid for (_earns_read).
var paid_throws := {}


func _ready() -> void:
	add_to_group(FightOutro.BOSS_GROUP)
	hurtbox.area_entered.connect(_on_hurtbox_entered)
	if kaiju_mode():
		max_health = KaijuLayout.MAX_HEALTH
		boss_health = max_health

	_apply_art_layout()
	sprite_base_position = sprite.position
	# Before the HUD, which hangs the gauge's bar under his health bar.
	var scene := get_tree().current_scene
	var player: Node = scene.get_node_or_null(FightOutro.PLAYER_PATH) if scene else null
	if player:
		_add_break_gauge(player)
	_build_hud()

	# Loaded here rather than when the fight starts, so the first play doesn't hitch.
	var theme := JordanArtLayout.theme()
	music_player.stream = theme.stream
	music_player.volume_db = theme.volume_db
	hit_sfx_player.stream = load("res://Assets/Audio/SFX/hit_impact.ogg")
	victory_sfx_player.stream = load("res://Assets/Audio/SFX/victory_fanfare.ogg")
	summon_sfx_player.stream = load("res://Assets/Audio/SFX/whirlwind_whoosh.ogg")
	taunt_sfx_player.stream = load("res://Assets/Audio/SFX/downed_stinger.ogg")


func _add_break_gauge(player: Node) -> void:
	break_gauge = BossBreakGauge.new()
	break_gauge.name = "BreakGauge"
	break_gauge.boss = self
	break_gauge.player = player
	var table: Dictionary = BREAK
	if kaiju_mode():
		table = KAIJU_BREAK
		break_gauge.owns_attack = func(id: StringName) -> bool: return KAIJU_ATTACK_IDS.has(id)
		break_gauge.earns_from = _earns_read
		var strong: Array[StringName] = [STOMP_ID]
		break_gauge.strong_parry_ids = strong
	else:
		# earns_from stays unset: his one attack both fills and drains it.
		break_gauge.owns_attack = func(id: StringName) -> bool: return ATTACK_IDS.has(id)
	break_gauge.parry_gain = table.parry_gain
	break_gauge.grab_parry_gain = table.grab_parry_gain
	break_gauge.reflect_gain = table.reflect_gain
	break_gauge.perfect_dodge_gain = table.perfect_dodge_gain
	break_gauge.punch_gain = table.punch_gain
	break_gauge.charged_punch_gain = table.charged_punch_gain
	break_gauge.hit_loss = table.hit_loss
	break_gauge.guard_break_loss = table.guard_break_loss
	break_gauge.unlock_delay = table.unlock_delay
	add_child(break_gauge)
	break_gauge.broke.connect(_on_break)


# On the kaiju: one read a throw for its funkos, parried or dodged, however many of them were; the rest of his
# attacks fill it every time.
func _earns_read(hit: RefCounted) -> bool:
	if not KAIJU_ATTACK_IDS.has(hit.attack_id):
		return false
	if hit.attack_id != FunkoThrow.ATTACK_ID or not is_instance_valid(hit.source) or not ("throw_id" in hit.source):
		return true
	var throw: int = hit.source.throw_id
	if throw < 0:
		return true
	if paid_throws.has(throw):
		return false
	paid_throws[throw] = true
	return true


func kaiju_mode() -> bool:
	return state_machine.kaiju_mode


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


# His crown as the frame showing has it, or standing.
func crown_point() -> Vector2:
	var crown = anchor(&"crown")
	return global_position + JordanArtLayout.frame_local(crown if crown != null else JordanArtLayout.TAUNT_CROWN)


#HIS SHEETS' ANCHORS (phase 1 on the kaiju: JordanRiderSheets)

# Where `key` is on the frame he shows, or on frame `step` of his animation, as his own sheet's contract has it: a texel,
# or null on a stand-in or a frame without it.
func anchor(key: StringName, step := -1) -> Variant:
	var table := JordanArtLayout.anchors(current_anim)
	if table.is_empty():
		return null
	var frame: int = anim.frames[clampi(step if step >= 0 else anim_step, 0, anim.frames.size() - 1)]
	if frame >= table.size():
		return null
	return table[frame].get(key)


# Where on him the kaiju's seat goes: his ride sheets' SEAT, or his soles on a stand-in.
func seat_local() -> Vector2:
	var seat = anchor(&"seat")
	return JordanArtLayout.frame_local(seat) if seat != null else JordanArtLayout.FLOOR_POINT


# His body put so `key` on the frame he shows is on `point`. False on a stand-in.
func place_anchor(key: StringName, point: Vector2) -> bool:
	var texel = anchor(key)
	if texel == null:
		return false
	global_position = (point - JordanArtLayout.frame_local(texel)).round()
	return true


# His hips (PIVOT) on an arc `apex` px high from where they are with `from_key` of frame `from_step` on `from_point`, to
# where they are with `to_key` of frame `to_step` on `to_point`, `weight` of the way, whichever frame shows: the topple,
# the climb and the buck off go through it. False on a stand-in.
func place_on_arc(from_point: Vector2, from_key: StringName, from_step: int, to_point: Vector2, to_key: StringName,
		to_step: int, weight: float, apex: float) -> bool:
	var p0 = anchor(&"pivot", from_step)
	var k0 = _key_texel(from_key, from_step)
	var p1 = anchor(&"pivot", to_step)
	var k1 = _key_texel(to_key, to_step)
	var now = anchor(&"pivot")
	if p0 == null or k0 == null or p1 == null or k1 == null or now == null:
		return false
	var w := clampf(weight, 0.0, 1.0)
	var start: Vector2 = from_point + JordanArtLayout.frame_local(p0) - JordanArtLayout.frame_local(k0)
	var finish: Vector2 = to_point + JordanArtLayout.frame_local(p1) - JordanArtLayout.frame_local(k1)
	var at := start.lerp(finish, w) - Vector2(0, 4.0 * apex * w * (1.0 - w))
	global_position = (at - JordanArtLayout.frame_local(now)).round()
	return true


# A frame without SOLES of its own still stands on the bottom of its centre column, as all his sheets do.
func _key_texel(key: StringName, step: int) -> Variant:
	var texel = anchor(key, step)
	if texel == null and key == &"soles":
		return JordanArtLayout.ANCHOR + Vector2(0, 1)
	return texel


# His hurtbox the frame's own BODY_BOX (sat on the mat), or back to standing.
func set_body_box(box_texels: Rect2) -> void:
	var box := JordanArtLayout.local_rect(box_texels)
	var hurtbox_shape: CollisionShape2D = hurtbox.get_node("CollisionShape2D")
	hurtbox_shape.position = box.get_center()
	(hurtbox_shape.shape as RectangleShape2D).size = box.size


func restore_body_box() -> void:
	set_body_box(JordanArtLayout.BODY_BOX)


# Where a figure punched back at him goes off on him (FunkoFigureScript): the kaiju's legs while he rides it and it
# stands, nothing while it is in the air, and his own hurtbox otherwise.
func redirect_rect() -> Rect2:
	var kaiju: Node2D = state_machine.kaiju
	if kaiju == null or not mounted:
		return hurtbox_rect()
	return Rect2() if kaiju.lift > 0.0 else kaiju.redirect_rect()


# The bar and the gauge under it fade while any of `points` is under them, and come back as they leave (Danny's).
func update_hud_fade(points: Array[Vector2]) -> void:
	var alpha := 1.0
	for point in points:
		if KaijuLayout.HUD_FADE_RECT.has_point(point):
			alpha = KaijuLayout.HUD_FADE_ALPHA
	_fade_hud(alpha)


# Bound to the bar itself, so a pause or a finisher's freeze holds it with the fight.
func _fade_hud(alpha: float) -> void:
	if not health_bar or is_equal_approx(hud_alpha, alpha):
		return
	hud_alpha = alpha
	if hud_fade:
		hud_fade.kill()
	hud_fade = health_bar.create_tween().set_parallel()
	for bar: Control in [health_bar, gauge_bar]:
		if bar:
			hud_fade.tween_property(bar, "modulate:a", alpha, KaijuLayout.HUD_FADE_TIME)


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
func play_anim(anim_name: StringName, next_anim: StringName = &"", from_step := 0) -> void:
	current_anim = anim_name
	anim = JordanArtLayout.anim(anim_name)
	anim_next = next_anim
	anim_step = mini(from_step, anim.frames.size() - 1)
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


# Frame `step` of his animation, held there until something plays.
func hold_frame(step: int) -> void:
	anim_step = clampi(step, 0, anim.frames.size() - 1)
	anim_done = true
	_show_anim_frame()


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


# Punches only land in his windows: the taunt, or knocked off the kaiju, and a Break.
func take_punch(amount: int) -> int:
	if boss_health <= 0 or not state_machine.is_open():
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
	# On the kaiju its legs flinch for him (_hit_feedback), and down on the mat he takes it where he sits.
	if boss_health > 0 and not kaiju_mode():
		_stagger()
	return dealt


# The player's finisher (see PlayerFinisher): a charged combo punch during the taunt or a Break dazes
# him, and the uppercut that follows ends that window. Phase 1 has no health floor for its damage to
# stop at. On the kaiju each opening says whether its POW dazes him (its dazeable): knocked off by a parried
# stomp it does, and on the lowered head after its breath it does too (the user, 2026-10-06).
func can_be_dazed() -> bool:
	if defeated or boss_health <= 0 or daze_used or not state_machine.is_open():
		return false
	var window: Node = state_machine.current_state
	return window.dazeable if "dazeable" in window else true


# The three-bar mash and the juggle are the Break's payout alone; the taunt pays the plain single-bar
# finisher. With his 24 health the juggle's 50% on every window would end the fight in two.
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
	if mounted:
		return crown_point() + Vector2(0, -JordanArtLayout.DAZE_GAP)
	var stars = anchor(&"stars") if state_machine.is_dismounted() else null
	if stars != null:
		return global_position + JordanArtLayout.frame_local(stars)
	if is_broken() or state_machine.is_dismounted():
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
# landed, as Eric's and Mason's do. On the kaiju, until it has shrunk back into the toy and he has hit the mat.
func outro_line_delay(_player_won: bool) -> float:
	var delay := 0.0
	if is_juggled():
		delay = JordanArtLayout.juggle().outro_delay
	if kaiju_mode():
		delay = maxf(delay, state_machine.states["Defeated"].kaiju_time_left())
	return delay


# The stomp's parry knocks him off the kaiju (JordanStomp): the stagger itself is the stomp's to play out.
func can_parry_stagger(hit: RefCounted) -> bool:
	return hit.attack_id == STOMP_ID and state_machine.current_state == state_machine.states.get("Stomp")


func parry_stagger(_duration: float) -> void:
	pass


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


# FIGHT 10 from his KO with no fight first, the main menu's FINALE row (JordanStateMachine._ready): his bar empty, not
# a hit draining it, and the win that plays his finale.
func start_at_finale() -> void:
	if defeated:
		return
	boss_health = 0
	if health_bar:
		health_bar.set_value(0, 0, BossHealthBarUI.HIT_SILENT)
	_refresh_health_bar()
	_on_defeated()


# FightOutro hands him the won outro: his finale plays in place of the lines and the Victory screen, starting with the
# walk-out (JordanWalkOut), which ends it with FightOutro.leave_to() into his room.
func take_won_outro(outro: Node, line_delay: float) -> void:
	state_machine.begin_walk_out(outro, line_delay)


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
		gauge_bar = BreakGaugeUI.new()
		gauge_bar.gauge = break_gauge
		hud_layer.add_child(gauge_bar)
		gauge_bar.position = health_bar.break_gauge_anchor()


func _hit_feedback() -> void:
	if not sprite:
		return
	# Riding it, the kaiju takes the flinch for him, but for a punch on its lowered head (JordanRecoil), which flashes him.
	if mounted and state_machine.kaiju and not state_machine.is_open():
		state_machine.kaiju.flinch()
		HitStop.freeze(get_tree(), 0.06)
		return

	# Down, he has no hit pose: the kneel holds, and in the air the hit sheet would replace the juggle's. Knocked
	# off the kaiju he sits it out the same way.
	if not is_down() and not state_machine.is_dismounted() and not mounted:
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
