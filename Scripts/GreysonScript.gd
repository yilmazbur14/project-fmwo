extends CharacterBody2D

# Greyson, the second half of FIGHT 06 (Computah's fight). When Computah falls, his gym partner storms the ring,
# tears off Computah's cannon arm, straps it on and takes over the fight (GreysonTakeover). ComputahScript hands
# over by instancing GreysonScene under the Arena, with `computah` set; GreysonTestFightScene starts him on his own
# (`start_active`), where the takeover jumps straight to its end state.
#
# His attack 1 is a chain (GreysonStateMachine.ATTACKS): plates thrown off the ropes (GreysonThrow), five
# teleport slams that plant delayed eruptions (GreysonSlams), then six poses to the crowd that fill HIS hype meter
# (GreysonPose). A full meter fires the spirit bomb, a loss (GreysonSpiritBomb). Parried and perfect-dodged plates
# fill his Break gauge. At 0 HP the fight isn't over: it hands to the final brawl (GreysonFinalBrawl), and only
# the brawl's end calls win().
#
# This node is his body, his health, his hype, his art, his sounds and his HUD. His origin is his feet
# (GreysonArtLayout), and `sprite` stays the body sprite whatever he is doing: PlayerFinisher and PlayerCombo both
# write to it. Its offset follows the sheet, never the animation (_stand_on).
#
# IN THE FINAL BRAWL his whole combat and finisher contract is the brawl's: every call below hands to the
# FinalBrawl state if it has that method, and is inert otherwise. boss_health stays 0 there; the brawl keeps its
# own count.

# A non-looping animation reached the end of its last frame.
signal anim_finished(anim_name: StringName)
# His hype meter moved: 0 to HYPE_MAX, in half cells.
signal hype_changed(value: float)

const HitStop := preload("res://Scripts/HitStop.gd")
const FightOutro := preload("res://Scripts/FightOutro.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const BossHealthBarUI := preload("res://Scripts/BossHealthBarUI.gd")
const BossBreakGauge := preload("res://Scripts/BossBreakGauge.gd")
const BreakGaugeUI := preload("res://Scripts/BreakGaugeUI.gd")
const HypeMeterUI := preload("res://Scripts/GreysonHypeMeterUI.gd")
const DoomOrb := preload("res://Scripts/GreysonDoomOrb.gd")
const Layout := preload("res://Scripts/GreysonArtLayout.gd")
const UI_THEME := preload("res://Assets/UI/ui_theme.tres")
# What he says once the fight is over, under player_won and player_lost.
const OUTRO_DIALOGUE := "res://Dialogue/GreysonOutro.dialogue"
# His fight is Computah's, FIGHT 06: what follows it is looked up by it.
const FIGHT_SCENE := "res://Scenes/Bosses/ComputahBossFightScene.tscn"
# The name on his bar.
const BAR_NAME := "GREYSON"

#CONSTANTS
# The plan's H, 30, doubled by the user (2026-09-25) and raised 25% (2026-09-30). The pose window's
# single-bar finisher takes 19 (30 supercharged), and the juggle 19, 8 and 11.
@export var max_health := 75
var boss_health := max_health
# Every window's cap unless its state has its own `hit_cap` (the Pose's is 8).
const MAX_HITS_PER_WINDOW := 3
# Each opening takes the damage of a clean chain of MAX_HITS_PER_WINDOW punches (PunchAllowance).
const PunchAllowance := preload("res://Scripts/PunchAllowance.gd")
const PHANTOM_HIT_WINDOW := 0.5
# The bar goes to half heat at this share of his health, and to full at the other.
const CAUTION_RATIO := 0.5
const HOT_RATIO := 0.25

#HIS HYPE (the spirit bomb's clock, plan section 3.5)
# Cells, in half-cell steps. Each unhit pose banks GreysonPose.bank; it carries across cycles, and a full meter fires
# the spirit bomb.
const HYPE_MAX := 6.0
const HYPE_STEP := 0.5
# Any hit that lands on him, in any window, the finisher's and the juggle's included, empties the meter at once (the
# user, 2026-09-30: "if he gets hit he goes back to 0"). Off, a spoiled pose drains GreysonPose.spoil instead.
@export var hit_resets_hype := true

#THE BREAK GAUGE (BossBreakGauge)
# The rollout's rule with the house N = 8: a read (a parry, or a perfect dodge, of a plate) is an eighth of the
# gauge, a punch a quarter of a read and a charged one a half, a hit taken one read back and a guard break two. Only
# plates earn (BREAK_EARNS): his eruptions drain it but never fill it. broken_time is GreysonBroken's window.
# BREAK_READ is max_value over N. A Break skips that cycle's poses, the part of his fight the retune made harder, so
# it shouldn't come every throw: of his six plates four or five come at a player who stands their ground and reads
# them, so 8 reads take them about two throws, and one who gets to all six a throw and a third.
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
const BREAK_EARNS: Array[StringName] = [&"greyson_plate"]
# The Break's three-bar mash and juggle, on the shared BossBroken and BossJuggled (greyson_juggle.png). Off, a
# Break pays the single-bar finisher.
const JUGGLE_ENABLED := true

# Set by ComputahScript before this enters the tree: the robot whose cannon he takes. Null in the test scene.
var computah: Node
# The test scene: no Computah, no takeover, straight into the takeover's end state and the fight.
@export var start_active := false
# With start_active, on into the final brawl at once, his bar empty: for iterating on the brawl and its tests.
@export var start_in_brawl := false

# Under both fighters: the eruption zones and their cracks.
@export var floor_layer: Node2D
# The plates, y-sorted with the fighters.
@export var hazard_layer: Node2D
# Over both fighters: bursts, the teleport columns, the spirit bomb.
@export var fx_layer: Node2D

@onready var sprite: Sprite2D = $Sprite2D
@onready var animation_player: AnimationPlayer = $AnimationPlayer
@onready var hurtbox: Area2D = $Hurtbox
@onready var state_machine = $StateManager

#AUDIO
@onready var music_player: AudioStreamPlayer = $MusicPlayer
@onready var hit_sfx_player: AudioStreamPlayer = $HitSfxPlayer
@onready var victory_sfx_player: AudioStreamPlayer = $VictorySfxPlayer
# Built from GreysonArtLayout.SFX: each key's players, rotated on every play.
var sfx_players := {}
# How many times his theme has been started, for the tests to prove it is only ever once.
var music_starts := 0
var music_base_db := 0.0
var music_duck: Tween

#UI (BossHealthBarUI, BreakGaugeUI and GreysonHypeMeterUI build it at the bar swap)
var hud_layer: CanvasLayer
var health_bar: Control
var gauge_bar: Control
var hype_meter: Control
# His meter made physical over his head (GreysonDoomOrb), with the meter from the bar swap on.
var doom_orb: Node2D
var hud_fade: Tween
var break_gauge: Node
var hints := {}
var hints_shown := {}

# Beaten for good: only greyson_beaten() sets it, at the end of the final brawl. 0 HP does not.
var defeated := false
var hits_this_window := 0
var punches := PunchAllowance.new()
# One finisher daze per window; each window and the Break clear it.
var daze_used := false
var hype := 0.0
# The final brawl holds his meter where 0 HP left it.
var hype_frozen := false
# Each teleport_out() and teleport_in() starts a new one: their sheets only hide and show him for their own.
var teleport_serial := 0
# He wears Computah's cannon: from the takeover's attach on, and in the test scene from the start.
var has_cannon := false

var fight_clock := 0.0
var last_contact_hit_time := -INF

var sprite_base_position: Vector2
# The offset the sheet showing stands his feet on the node with, and whether someone else has drawn on his sprite
# since (halt_anim), so the next animation must put the whole sheet back.
var sheet_offset := Layout.SPRITE_OFFSET
var sheet_dirty := false
# Mirrored from his drawn right, on the rows that flip.
var facing_left := false
# Which of Layout.BODY_BOXES his hurtbox is.
var body_box := &"idle"
var cannon_glow: Polygon2D

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
	# The exported value is only set after the variable above was initialised.
	boss_health = max_health

	sprite.position = Vector2.ZERO
	sprite.offset = Layout.SPRITE_OFFSET
	sheet_offset = Layout.SPRITE_OFFSET
	sprite_base_position = sprite.position
	set_body_box(&"idle")
	_build_cannon_glow()
	hud_layer = CanvasLayer.new()
	add_child(hud_layer)
	var scene := get_tree().current_scene
	var player: Node = scene.get_node_or_null(FightOutro.PLAYER_PATH) if scene else null
	if player:
		_add_break_gauge(player)
	_build_sfx()
	_load_music()
	hit_sfx_player.stream = load("res://Assets/Audio/SFX/hit_impact.ogg")
	victory_sfx_player.stream = load("res://Assets/Audio/SFX/victory_fanfare.ogg")
	play_anim(&"idle")


func _physics_process(delta: float) -> void:
	fight_clock += delta


func get_health_ratio() -> float:
	if state_machine.in_final_brawl():
		return _brawl_call(&"get_health_ratio", [], 0.0)
	return float(boss_health) / float(max_health)


func get_max_health() -> int:
	if state_machine.in_final_brawl():
		return _brawl_call(&"get_max_health", [], max_health)
	return max_health


#THE BREAK GAUGE

func _add_break_gauge(player: Node) -> void:
	break_gauge = BossBreakGauge.new()
	break_gauge.name = "BreakGauge"
	break_gauge.boss = self
	break_gauge.player = player
	break_gauge.owns_attack = func(id: StringName) -> bool: return str(id).begins_with("greyson_")
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


#HIS HYPE

# `delta` cells onto his meter, in half cells, never under 0 or over HYPE_MAX. The meter as it now stands.
func add_hype(delta: float) -> float:
	if hype_frozen:
		return hype
	var to := clampf(snappedf(hype + delta, HYPE_STEP), 0.0, HYPE_MAX)
	if to != hype:
		hype = to
		_on_hype_changed()
	return hype


func hype_full() -> bool:
	return hype >= HYPE_MAX


func reset_hype() -> void:
	if hype == 0.0:
		return
	hype = 0.0
	_on_hype_changed()


func _on_hype_changed() -> void:
	_show_cannon_glow()
	_tune_cannon_hum()
	hype_changed.emit(hype)


#MUSIC

func _load_music() -> void:
	music_player.stream = load(Layout.THEME)
	music_player.volume_db = Layout.THEME_DB
	music_base_db = music_player.volume_db


# Once, whoever asks first: the takeover's bar swap, or its skip.
func start_music() -> void:
	if music_starts > 0 or music_player == null:
		return
	music_starts += 1
	music_player.volume_db = music_base_db
	music_player.play()


# His theme `db` under its own level over `time`, and back with 0. Bound to the player, so a pause holds it.
func duck_music(db: float, time: float) -> void:
	if music_duck:
		music_duck.kill()
	music_duck = music_player.create_tween()
	music_duck.tween_property(music_player, "volume_db", music_base_db + db, time)


func snap_music_level() -> void:
	if music_duck:
		music_duck.kill()
		music_duck = null
	music_player.volume_db = music_base_db


#SOUNDS

# Built here rather than wired into the scene: GreysonArtLayout.SFX is the only place they are named. Each key
# plays its approved file once it has shipped, and its stand-in until then.
func _build_sfx() -> void:
	for key in Layout.SFX:
		var variants := _sfx_variants(key)
		if variants.is_empty():
			continue
		var players: Array[AudioStreamPlayer] = []
		var voices: int = maxi(Layout.SFX_VOICES.get(key, 1), variants.size())
		for i in voices:
			var variant: Dictionary = variants[i % variants.size()]
			var sfx := AudioStreamPlayer.new()
			sfx.stream = variant.stream
			sfx.volume_db = variant.volume_db
			sfx.pitch_scale = variant.pitch
			sfx.set_meta(&"base_db", variant.volume_db)
			sfx.set_meta(&"base_pitch", variant.pitch)
			add_child(sfx)
			players.append(sfx)
		sfx_players[key] = players


# The streams `key` plays, each with its level and pitch: its approved file (or files), or its stand-in. A file
# that won't load - shipped but not imported yet - counts as not there. Empty if nothing loads at all.
func _sfx_variants(key: StringName) -> Array[Dictionary]:
	var spec: Dictionary = Layout.SFX[key]
	var shipped: Array = spec.get("streams", [spec.stream] if spec.has("stream") else [])
	var levels: Array = spec.get("volume_dbs", [spec.get("volume_db", 0.0)])
	var variants: Array[Dictionary] = []
	for i in shipped.size():
		var stream := _sfx_stream(shipped[i], spec)
		if stream != null:
			variants.append({stream = stream, volume_db = levels[mini(i, levels.size() - 1)], pitch = 1.0})
	if variants.is_empty():
		var stand_in := _sfx_stream(spec.stand_in, spec)
		if stand_in != null:
			variants.append({stream = stand_in, volume_db = spec.stand_in_db, pitch = spec.stand_in_pitch})
	return variants


func _sfx_stream(path: String, spec: Dictionary) -> AudioStream:
	if not ResourceLoader.exists(path):
		return null
	var stream: AudioStream = load(path)
	if stream == null or not spec.get("loop", false):
		return stream
	# Its own copy: the file is shared with fights that play it once. The approved loops carry their own points.
	stream = stream.duplicate()
	if stream is AudioStreamWAV:
		stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
		if stream.loop_end <= stream.loop_begin:
			stream.loop_end = int(stream.get_length() * stream.mix_rate)
	elif "loop" in stream:
		stream.loop = true
	return stream


func play_sfx(key: StringName, pitch := 1.0) -> void:
	var players: Array = sfx_players.get(key, [])
	if players.is_empty():
		return
	var sfx: AudioStreamPlayer = players.pop_front()
	players.append(sfx)
	sfx.pitch_scale = sfx.get_meta(&"base_pitch") * pitch
	sfx.play()


func stop_sfx(key: StringName) -> void:
	for sfx: AudioStreamPlayer in sfx_players.get(key, []):
		sfx.stop()


# A player of its own for `key` under `host`, at the key's level and pitch but not started, for a sound one hazard
# owns and takes with it: a plate's spin, or a pending zone's rumble. Its volume_db and pitch_scale start at the
# key's own (its "base_db" and "base_pitch" metas), for a caller that ramps them.
func sfx_player_for(key: StringName, host: Node) -> AudioStreamPlayer:
	var variants := _sfx_variants(key)
	var variant: Dictionary = variants[0] if not variants.is_empty() else {stream = null, volume_db = 0.0, pitch = 1.0}
	var sfx := AudioStreamPlayer.new()
	sfx.stream = variant.stream
	sfx.volume_db = variant.volume_db
	sfx.pitch_scale = variant.pitch
	sfx.set_meta(&"base_db", variant.volume_db)
	sfx.set_meta(&"base_pitch", variant.pitch)
	host.add_child(sfx)
	return sfx


#ANIMATION

# A non-looping animation holds its last frame when it ends, unless `next_anim` follows it. `loop_time` rescales it
# so one pass over its frames takes that long.
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
	if sheet_dirty or sheet != sprite.texture:
		# Back to the first frame before the frame count changes, so the current one can't be out of range.
		sprite.frame = 0
		sprite.texture = sheet
		sprite.vframes = 1
		sprite.hframes = roundi(sheet.get_width() / Layout.frame_size(spec).x)
		if sheet_dirty:
			sheet_offset = Vector2.INF
			sheet_dirty = false
		_stand_on(Layout.sheet_offset(spec))
	animation_player.play(spec.get("motion", &"RESET"))
	_show_anim_frame()


# His own animation stops where it is, frame and all, so another state can draw on his sprite (the final brawl
# does). The next play_anim() puts his sheet back whole: texture, frames and offset.
func halt_anim() -> void:
	anim_done = true
	anim_next = &""
	sheet_dirty = true


# A state's own animation. A one-shot still playing finishes first and hands over to it - a flinch back into the
# pose - while a loop gives way at once.
func play_state_anim(anim_name: StringName) -> void:
	state_anim = anim_name
	if not anim.is_empty() and not anim.loop and not anim_done:
		anim_next = anim_name
		return
	play_anim(anim_name)


# Only a sheet that stands on a different offset from the one it replaces writes it: the finisher's recoil rocks
# sprite.offset and settles it back, and BossJuggled owns it from the juggle's first frame until it restores the
# sheet and offset it found.
func _stand_on(offset: Vector2) -> void:
	if offset == sheet_offset:
		return
	sheet_offset = offset
	sprite.offset = offset


func _process(delta: float) -> void:
	# Every frame rather than on his own frames alone: a teleport hides him between them, and the juggle's sheet
	# and the brawl's clips draw him with none of them.
	_place_cannon_glow()
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
	sprite.flip_h = anim.get("flips", false) and facing_left != anim.get("drawn_left", false)
	_place_cannon_glow()


# Whole and upright on his feet: visible even if a teleport was cut off mid-sheet, his own colours, on his own z.
func show_body() -> void:
	sprite.visible = true
	sprite.rotation = 0.0
	sprite.modulate = Color.WHITE
	sprite.self_modulate = Color.WHITE
	sprite.z_index = 0
	sprite.position = sprite_base_position


# The lines' squash while one of his is typing, on whichever sheet is showing: only the AnimationPlayer's clip,
# so no frame or sheet changes under it. play_anim() puts its own clip back.
func set_talking(talking: bool) -> void:
	var squashing: bool = animation_player.current_animation == "talk"
	if talking and not squashing:
		animation_player.play(&"talk")
	elif not talking and squashing:
		animation_player.play(&"RESET")


func set_facing(left: bool) -> void:
	if facing_left == left:
		return
	facing_left = left
	_show_anim_frame()
	set_body_box(body_box)


func face_toward(point: Vector2) -> void:
	if point.x != global_position.x:
		set_facing(point.x < global_position.x)


#WHERE THINGS ARE ON HIM (world px, mirrored with him)

# Each on the frame showing when asked about the animation playing, and on the animation's first frame otherwise.
func crown_point(anim_name := current_anim) -> Vector2:
	return _drawn(Layout.crown(anim_name, _frame_of(anim_name)), anim_name)


# Where a badge's tip stands over him in `anim_name`'s pose.
func tell_anchor(anim_name := current_anim) -> Vector2:
	return crown_point(anim_name) + Vector2(0, -Layout.TELL_GAP)


# Where a plate leaves his hand.
func release_point(anim_name := &"throw") -> Vector2:
	return _drawn(Layout.release(anim_name, _frame_of(anim_name)), anim_name)


# Where the barbell meets the mat.
func impact_point(anim_name := &"slam") -> Vector2:
	return _drawn(Layout.impact(anim_name, _frame_of(anim_name)), anim_name)


# The cannon's muzzle.
func muzzle_point(anim_name := current_anim) -> Vector2:
	return _drawn(Layout.muzzle(anim_name, _frame_of(anim_name)), anim_name)


func hand_point(anim_name := current_anim) -> Vector2:
	return _drawn(Layout.hand(anim_name, _frame_of(anim_name)), anim_name)


# His mouth on the roar, where its FX sits.
func roar_mouth_point() -> Vector2:
	return _drawn(Layout.ROAR_MOUTH, &"roar")


func _frame_of(anim_name: StringName) -> int:
	return sprite.frame if anim_name == current_anim and not anim.is_empty() else -1


func _drawn(texel: Vector2, anim_name: StringName) -> Vector2:
	return global_position + Layout.texel_local(texel, anim_name, Layout.mirrored(anim_name, facing_left))


#THE CANNON'S GLOW (a code-drawn stand-in: one step a level of his meter)

func _build_cannon_glow() -> void:
	var spec := Layout.fx(&"cannon_glow")
	cannon_glow = Polygon2D.new()
	var polygon := PackedVector2Array()
	for i in spec.points:
		polygon.append(Vector2.from_angle(TAU * i / spec.points) * spec.radius)
	cannon_glow.polygon = polygon
	cannon_glow.color = spec.color
	var additive := CanvasItemMaterial.new()
	additive.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	cannon_glow.material = additive
	cannon_glow.z_index = 1
	cannon_glow.visible = false
	add_child(cannon_glow)


func _show_cannon_glow() -> void:
	if cannon_glow == null:
		return
	cannon_glow.modulate.a = Layout.fx(&"cannon_glow").alphas[_glow_level()]
	_place_cannon_glow()


# On his muzzle only while one of his own sheets draws him, lit, and in sight. The juggle's sheet and the brawl's
# clips have no muzzle points of his, so under them it would hang where his last frame left it: it is off in the
# juggle, and from the brawl's start to the fight's end.
func _place_cannon_glow() -> void:
	if cannon_glow == null:
		return
	cannon_glow.visible = has_cannon and sprite.visible and _glow_level() > 0 and not is_juggled() \
		and not state_machine.final_brawl_entered
	if cannon_glow.visible:
		cannon_glow.position = (muzzle_point() - global_position).round()


func _glow_level() -> int:
	return clampi(floori(hype), 0, Layout.fx(&"cannon_glow").alphas.size() - 1)


# He wears the cannon from here (the takeover's attach, or the test scene's start).
func put_on_cannon() -> void:
	has_cannon = true
	_show_cannon_glow()
	_start_cannon_hum()


#THE CANNON'S HUM (the glow's sound: a loop from the attach on, stepping up with his meter)

func _cannon_hum() -> AudioStreamPlayer:
	var players: Array = sfx_players.get(&"cannon_hum", [])
	return players[0] if not players.is_empty() else null


# Once: the takeover's attach and its skip both put the cannon on.
func _start_cannon_hum() -> void:
	var hum := _cannon_hum()
	if hum == null or hum.playing or state_machine.final_brawl_entered:
		return
	_tune_cannon_hum()
	hum.play()


# Its level and pitch for his meter: CANNON_HUM's ramp up to the key's own level on a full one.
func _tune_cannon_hum() -> void:
	var hum := _cannon_hum()
	if hum == null:
		return
	var fill: float = hype / HYPE_MAX
	hum.volume_db = hum.get_meta(&"base_db") - Layout.CANNON_HUM.quieter_empty * (1.0 - fill)
	hum.pitch_scale = hum.get_meta(&"base_pitch") * lerpf(Layout.CANNON_HUM.pitch.x, Layout.CANNON_HUM.pitch.y, fill)


# Out as the brawl starts: its staging has a mix of its own, and his meter is gone from it, as his glow is.
func stop_cannon_hum() -> void:
	var hum := _cannon_hum()
	if hum == null or not hum.playing:
		return
	var fade := hum.create_tween()
	fade.tween_property(hum, "volume_db", hum.volume_db - 30.0, Layout.HUD_FADE_TIME)
	fade.tween_callback(hum.stop)


#HIS HURTBOX

# One of Layout.BODY_BOXES, mirrored as he faces now.
func set_body_box(key: StringName) -> void:
	body_box = key
	var box := _facing_box(key)
	var shape: CollisionShape2D = hurtbox.get_node("CollisionShape2D")
	shape.position = box.get_center()
	(shape.shape as RectangleShape2D).size = box.size


# One of Layout.BODY_BOXES in world px as it would stand on him now, without making it his hurtbox.
func body_box_rect(key: StringName) -> Rect2:
	var box := _facing_box(key)
	box.position += global_position
	return box


func _facing_box(key: StringName) -> Rect2:
	var box := Layout.body_rect(key)
	if facing_left:
		box.position.x = -box.end.x
	return box


# His hurtbox as it stands, in world px.
func hurtbox_rect() -> Rect2:
	var shape: CollisionShape2D = hurtbox.get_node("CollisionShape2D")
	return shape.global_transform * shape.shape.get_rect()


# Punches only reach him in his windows. The hurtbox keeps its groups, so the player still faces him.
func set_hurtbox_active(active: bool) -> void:
	# Deferred: monitoring can't change inside a physics flush.
	hurtbox.set_deferred("monitoring", active)
	hurtbox.set_deferred("monitorable", active)


# Whether the player faces him and aims at him at all: off until he has walked into the ring, and off for good
# once he is beaten.
func set_target_active(on: bool) -> void:
	if on and not hurtbox.is_in_group("boss_target"):
		hurtbox.add_to_group("boss_target")
	elif not on and hurtbox.is_in_group("boss_target"):
		hurtbox.remove_from_group("boss_target")


#THE TELEPORT (Matt's pattern: out where he is, in where the attack wants him)

# His sprite shows under the out sheet's first frame and is gone from its hide_from frame. The caller times it.
func teleport_out() -> void:
	restore_hud()
	set_hurtbox_active(false)
	play_anim(&"teleport_out")
	play_sfx(&"teleport_out")
	teleport_serial += 1
	play_fx(&"teleport_out", global_position, fx_layer, false, _hide_from_frame.bind(Layout.fx(&"teleport_out").hide_from, teleport_serial))


# His feet on `at`, and his sprite back from the in sheet's show_from frame.
func teleport_in(at: Vector2) -> void:
	global_position = at.round()
	sprite.visible = false
	play_anim(&"teleport_in")
	play_sfx(&"teleport_in")
	teleport_serial += 1
	play_fx(&"teleport_in", global_position, fx_layer, false, _show_from_frame.bind(Layout.fx(&"teleport_in").show_from, teleport_serial))


# `serial` is the teleport the sheet belongs to: a sheet still playing out after the next teleport has begun (a
# teleport shorter than the sheet) leaves him to that one.
func _hide_from_frame(frame: int, from: int, serial := -1) -> void:
	if frame >= from and (serial < 0 or serial == teleport_serial):
		sprite.visible = false


func _show_from_frame(frame: int, from: int, serial := -1) -> void:
	if frame >= from and (serial < 0 or serial == teleport_serial):
		sprite.visible = true


#FX

# One of his FX sheets (GreysonArtLayout.fx) played once at `at` on `layer`, his fx_layer unless one is given, and
# freed after its last frame. A screen layer (`screen` in its row) is drawn from the view's top-left instead, and
# `at` is ignored. It goes in the hazard group, so a Break or the end of the fight takes it, unless `hazard` is off
# for a cut that clears its own; `on_frame` is called with each frame as it shows.
func play_fx(key: StringName, at: Vector2, layer: Node2D = null, flip := false, on_frame := Callable(), hazard := true) -> Sprite2D:
	var spec := Layout.fx(key)
	var fx := Sprite2D.new()
	fx.texture = load(spec.texture)
	fx.hframes = spec.hframes
	fx.vframes = spec.get("vframes", 1)
	fx.scale = Vector2.ONE * Layout.SCALE
	fx.flip_h = flip
	if spec.get("screen", false):
		fx.centered = false
		at = Vector2.ZERO
	else:
		fx.offset = Layout.flipped_offset(spec.get("offset", Vector2.ZERO), flip)
	var into: Node2D = layer if layer != null else fx_layer
	if hazard:
		state_machine.add_hazard(fx, at, into)
	else:
		fx.position = into.to_local(at.round())
		into.add_child(fx)
	var times: Array = spec.get("times", [spec.get("frame_time", 0.05)])
	var play := fx.create_tween()
	for i in fx.hframes * fx.vframes:
		play.tween_callback(_show_fx_frame.bind(fx, i, on_frame))
		play.tween_interval(times[mini(i, times.size() - 1)])
	play.tween_callback(fx.queue_free)
	return fx


func _show_fx_frame(fx: Sprite2D, frame: int, on_frame: Callable) -> void:
	fx.frame = frame
	if on_frame.is_valid():
		on_frame.call(frame)


#THE HUD

# His block, built at the takeover's bar swap and swept to full over `time` (0 lands it full): his bar, his Break
# gauge under it, and his hype meter beside it. Once.
func show_hud(time: float) -> void:
	if health_bar != null:
		return
	health_bar = BossHealthBarUI.create({
		"rows": [{"key": &"greyson", "max": max_health, "value": 0}],
		"plate": &"greyson",
		"text": BAR_NAME,
	})
	hud_layer.add_child(health_bar)
	if break_gauge:
		gauge_bar = BreakGaugeUI.new()
		gauge_bar.gauge = break_gauge
		hud_layer.add_child(gauge_bar)
		gauge_bar.position = health_bar.break_gauge_anchor()
	hype_meter = HypeMeterUI.new()
	hype_meter.body = self
	hud_layer.add_child(hype_meter)
	hype_meter.position = Layout.HYPE_METER.at
	if Layout.USE_DOOM_ORB:
		doom_orb = DoomOrb.new()
		doom_orb.body = self
		get_parent().add_child(doom_orb)
	health_bar.refill_row(0, boss_health, time)


# A badge over his crown in `anim_name`'s pose, from the top of the ring, is inside the boss bar: the bar and
# everything under it fade while it is there and come back as it leaves.
func update_hud_fade(anim_name := current_anim) -> void:
	update_hud_fade_at(tell_anchor(anim_name))


# The same for any point.
func update_hud_fade_at(point: Vector2) -> void:
	_fade_hud(state_machine.hud_fade_alpha if state_machine.HUD_FADE_RECT.has_point(point) else 1.0)


func restore_hud() -> void:
	_fade_hud(1.0)


# His bar, his gauge and his meter gone over `time`: the final brawl takes his bar away.
func hide_boss_hud(time: float) -> void:
	_fade_hud(0.0, time)


# Bound to the bar itself, so a pause or a finisher's freeze holds it with the fight.
func _fade_hud(alpha: float, time := Layout.HUD_FADE_TIME) -> void:
	if not health_bar:
		return
	if hud_fade:
		hud_fade.kill()
	if is_equal_approx(health_bar.modulate.a, alpha):
		return
	hud_fade = health_bar.create_tween().set_parallel()
	for bar: Control in [health_bar, gauge_bar, hype_meter]:
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
	var player_hype: Node = player.get_node_or_null("Hype") if player else null
	if player_hype:
		player_hype.add(amount)


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


#COMBAT

func _on_hurtbox_entered(area: Area2D) -> void:
	if not area.is_in_group("player attack"):
		return
	if boss_health <= 0 and not state_machine.in_final_brawl():
		return
	# The phantom-hit filter every boss has: a punch that connects as its hitbox switches on is reported again
	# when PlayerPunching switches the hitbox off, which would eat the hit cap.
	if not area.monitorable and fight_clock - last_contact_hit_time < PHANTOM_HIT_WINDOW:
		return
	if area.get_parent().combo.resolve_punch(self) > 0 and area.monitorable:
		last_contact_hit_time = fight_clock


func take_punch(amount: int) -> int:
	if state_machine.in_final_brawl():
		return _brawl_call(&"take_punch", [amount], 0)
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


# A window opening: a fresh hit cap and a fresh daze.
func begin_window() -> void:
	hits_this_window = 0
	daze_used = false


func _apply_damage(amount: int, pitch := 1.0) -> int:
	var dealt := mini(amount, boss_health)
	if dealt <= 0:
		return 0
	boss_health -= dealt
	_refresh_health_bar()
	_hit_feedback()
	hit_sfx_player.pitch_scale = pitch
	hit_sfx_player.play()
	# Before the flinch, so the pose it spoils finds the meter already empty.
	if hit_resets_hype:
		reset_hype()
	if boss_health > 0:
		state_machine.flinch()
	else:
		# area_entered fires mid physics flush; deferring keeps the state Exit/Enter code the brawl's start runs
		# from having to be flush-safe.
		call_deferred("_on_zero_health")
	return dealt


func flinch() -> void:
	if state_machine.in_final_brawl():
		_brawl_call(&"flinch", [], null)
		return
	state_machine.flinch()


# The player's finisher (PlayerFinisher): a charged third punch in an open window dazes him, once a window, if
# the state that opened it allows one. A daze whose mash fizzled or whose uppercut whiffed gives it back
# (exit_daze): his poses take 8 punches, room for a second POW, and a POW must always daze (the user, 2026-10-06).
func can_be_dazed() -> bool:
	if state_machine.in_final_brawl():
		return _brawl_call(&"can_be_dazed", [], false)
	return (not defeated and boss_health > 0 and not daze_used and state_machine.is_open()
		and state_machine.allows_daze())


# The finisher draws its own daze stars over the Break's.
func enter_daze() -> void:
	if state_machine.in_final_brawl():
		_brawl_call(&"enter_daze", [], null)
		return
	daze_used = true
	_show_break_stars(false)


func exit_daze(finisher_landed: bool) -> void:
	if state_machine.in_final_brawl():
		_brawl_call(&"exit_daze", [finisher_landed], null)
		return
	if not finisher_landed:
		daze_used = false
		_show_break_stars(true)


func _show_break_stars(shown: bool) -> void:
	if is_broken() and state_machine.current_state.has_method("show_stars"):
		state_machine.current_state.show_stars(shown)


func end_recovery(stagger_time: float) -> bool:
	if state_machine.in_final_brawl():
		return _brawl_call(&"end_recovery", [stagger_time], false)
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
	# The pose window's uppercut ends the whole phase: up, staggered, then the next cycle.
	if state_machine.is_open():
		state_machine.end_window(stagger_time)
		return true
	return false


# Past the hit cap, which the combo that led to it has used up.
func take_finisher(amount: int) -> int:
	if state_machine.in_final_brawl():
		return _brawl_call(&"take_finisher", [amount], 0)
	if not state_machine.is_open():
		return 0
	return _apply_damage(amount)


func get_daze_anchor() -> Vector2:
	if state_machine.in_final_brawl():
		return _brawl_call(&"get_daze_anchor", [], crown_point() + Vector2(0, -Layout.DAZE_GAP))
	return crown_point(&"broken" if is_broken() else current_anim) + Vector2(0, -Layout.DAZE_GAP)


func get_finisher_hurtbox() -> Area2D:
	if state_machine.in_final_brawl():
		return _brawl_call(&"get_finisher_hurtbox", [], hurtbox)
	return hurtbox


#THE PARRY'S STAGGER (PlayerDefense asks the body; the state he is in answers)

func can_parry_stagger(hit: RefCounted) -> bool:
	if state_machine.in_final_brawl():
		return _brawl_call(&"can_parry_stagger", [hit], false)
	var state = state_machine.current_state
	return state != null and state.has_method("can_parry_stagger") and state.can_parry_stagger(hit)


func parry_stagger(duration: float) -> void:
	if state_machine.in_final_brawl():
		_brawl_call(&"parry_stagger", [duration], null)
		return
	var state = state_machine.current_state
	if state != null and state.has_method("parry_stagger"):
		state.parry_stagger(duration)


#THE JUGGLE (PlayerFinisher's tiered uppercut, Mason's names; only the Break pays it)

func can_be_juggled() -> bool:
	if state_machine.in_final_brawl():
		return _brawl_call(&"can_be_juggled", [], false)
	return JUGGLE_ENABLED and not defeated and boss_health > 0 and is_broken()


func begin_juggle() -> void:
	if state_machine.in_final_brawl():
		_brawl_call(&"begin_juggle", [], null)
		return
	state_machine.enter_juggled()


func juggle_lift(px: float) -> void:
	if state_machine.in_final_brawl():
		_brawl_call(&"juggle_lift", [px], null)
		return
	if is_juggled() and state_machine.current_state.has_method("lift"):
		state_machine.current_state.lift(px)


func juggle_pose(pose: StringName, crater := false) -> void:
	if state_machine.in_final_brawl():
		_brawl_call(&"juggle_pose", [pose, crater], null)
		return
	if is_juggled() and state_machine.current_state.has_method("pose"):
		state_machine.current_state.pose(pose, crater)


func juggle_headroom() -> float:
	if state_machine.in_final_brawl():
		return _brawl_call(&"juggle_headroom", [], 0.0)
	var juggled: Node = state_machine.states.get("Juggled")
	return juggled.headroom() if juggled and juggled.has_method("headroom") else 0.0


# Past the hit cap, as take_finisher, with his hit sound pitched up a step each uppercut.
func take_juggle_hit(amount: int, pitch: float) -> int:
	if state_machine.in_final_brawl():
		return _brawl_call(&"take_juggle_hit", [amount, pitch], 0)
	return _apply_damage(amount, pitch)


func get_juggle_point() -> Vector2:
	if state_machine.in_final_brawl():
		return _brawl_call(&"get_juggle_point", [], get_daze_anchor())
	var juggled: Node = state_machine.states.get("Juggled")
	return juggled.air_point() if juggled and juggled.has_method("air_point") else get_daze_anchor()


# The last uppercut's shove.
func juggle_knock_back(push: Vector2, time: float) -> void:
	if state_machine.in_final_brawl():
		_brawl_call(&"juggle_knock_back", [push, time], null)
		return
	_shove(push, time)


# The single-bar uppercut's shove, as Mason's and Eric's are, in place of a rock of his sprite: the brawl draws on
# his sprite, so the finisher must never tween its offset there, and it only stops doing so for a boss with this.
func knock_back(push: Vector2, time: float) -> void:
	if state_machine.in_final_brawl():
		_brawl_call(&"knock_back", [push, time], null)
		return
	_shove(push, time)


# Along `push`, inside where he may stand and never toward the player.
func _shove(push: Vector2, time: float) -> void:
	var bounds: Rect2 = state_machine.STAND_RECT
	var target := (global_position + push).clamp(bounds.position, bounds.end)
	var player: Node2D = state_machine.get_player()
	if player and target.distance_to(player.global_position) < global_position.distance_to(player.global_position):
		return
	create_tween().tween_property(self, "global_position", target, time).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)


# A juggle that kills him ends with him still in the air, and the outro's first line would otherwise open over him
# mid-fall.
func outro_line_delay(_player_won: bool) -> float:
	if is_juggled():
		return Layout.juggle().outro_delay
	return 0.0


# The FinalBrawl state's own answer to `method`, or `fallback` if it has none.
func _brawl_call(method: StringName, args: Array, fallback: Variant) -> Variant:
	var brawl: Node = state_machine.current_state
	if brawl != null and brawl.has_method(method):
		return brawl.callv(method, args)
	return fallback


#THE END OF THE FIGHT

# 0 HP is not the end: the final brawl takes over (GreysonStateMachine.enter_final_brawl). Nothing here may end the
# fight or set `defeated`: only the brawl's end does, through greyson_beaten().
func _on_zero_health() -> void:
	set_hurtbox_active(false)
	state_machine.enter_final_brawl()


# start_in_brawl's way there: his bar emptied, then the brawl, as 0 HP would.
func skip_to_brawl() -> void:
	boss_health = 0
	_refresh_health_bar()
	_on_zero_health()


# The brawl is won (GreysonStateMachine.greyson_beaten): the fanfare, the crowd, and the outro into Victory.
func win() -> void:
	if music_player.playing:
		music_player.stop()
	victory_sfx_player.play()
	get_tree().call_group("arena_crowd", "cheer", 2.0)
	GameProgress.next_boss_scene = GameProgress.next_fight_after(FIGHT_SCENE)
	FightOutro.finish_fight(get_tree(), true)


# Called by FightOutro when the player loses.
func on_player_defeated() -> void:
	state_machine.enter_player_defeated()


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
