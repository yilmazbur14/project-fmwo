extends CharacterBody2D

# Liam, the second half of FIGHT 07: once beast Bixby is beaten and has coughed him up, Liam takes the fight over
# (LiamTakeover), raises an earth pillar and fights from on top of it. BixbyBeastScript hands over by instancing
# LiamScene under the Arena with `bixby` set; LiamTestFightScene starts him on his own (`start_active`), where the
# takeover jumps straight to its end state. Beating Liam himself is the only win of the fight.
#
# This node is his body, his health, his art, his sounds and his HUD. It stands on his floor point and is drawn `height`
# px over it (Air), Bixby's model: on the pillar his floor point is the pillar's floor line and his height the pillar's
# top. `sprite` stays his body sprite whatever he does: PlayerFinisher and PlayerCombo both write to it. His hurtbox is
# only ever a target on the ground or in the cut, never on the pillar, where the pillar is the one the player punches.
#
# His pillar (LiamPillar) and his flood (LiamFlood) are built in code: the pillar just before him in his scene, so it is
# drawn behind him on the y-sort tie, and the flood on his FloorLayer.

signal anim_finished(anim_name: StringName)

const HitStop := preload("res://Scripts/HitStop.gd")
const FightOutro := preload("res://Scripts/FightOutro.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const BossHealthBarUI := preload("res://Scripts/BossHealthBarUI.gd")
const BossBreakGauge := preload("res://Scripts/BossBreakGauge.gd")
const BreakGaugeUI := preload("res://Scripts/BreakGaugeUI.gd")
const PunchAllowance := preload("res://Scripts/PunchAllowance.gd")
const Layout := preload("res://Scripts/LiamArtLayout.gd")
const LiamPillar := preload("res://Scripts/LiamPillar.gd")
const LiamFlood := preload("res://Scripts/LiamFlood.gd")
const LiamRow := preload("res://Scripts/LiamRow.gd")
const LiamSteam := preload("res://Scripts/LiamSteam.gd")
# What he says once the fight is over, under player_won and player_lost. Bixby's LiamOutro stays with Bixby.
const OUTRO_DIALOGUE := "res://Dialogue/LiamPhaseOutro.dialogue"
# His fight is Bixby's, FIGHT 07: what follows it is looked up by it.
const FIGHT_SCENE := "res://Scenes/Bosses/LiamBossFightScene.tscn"
const BAR_NAME := "LIAM"

#CONSTANTS
# 120: 40 until the user raised every boss's 25% (2026-09-30), 50 until the tuning round of 2026-10-04 (difficulty 7).
# A clean window is 4 + the finisher's 30 (48 with full hype); a Break window, at 8.5 presses a second, 4 + the
# juggle's 42: three or four windows.
@export var max_health := 120
var boss_health := max_health
const MAX_HITS_PER_WINDOW := 3
const PHANTOM_HIT_WINDOW := 0.5
const CAUTION_RATIO := 0.6
const HOT_RATIO := 0.34
const HUD_FADE_TIME := 0.25

#THE BREAK GAUGE (BossBreakGauge): the rollout's rule, 8 clean reads from empty. Only his tsunami's and his lunge's
# parries and perfect dodges are reads (BREAK_EARNS); a punch in a window is a quarter of one; the pillar is not him,
# so punching it earns nothing; every liam_ attack that lands drains it. A Break earned on the pillar is banked for his
# fall (LiamStateMachine.break_owed).
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
const BREAK_EARNS: Array[StringName] = [&"liam_tsunami", &"liam_lunge"]
const JUGGLE_ENABLED := true
# His phase gives the player's dash its late-diagonal grace (PlayerScript.dash_diagonal_grace): a corner zip whose second
# arrow lands up to this many frames after the dash still goes diagonal. Every other fight leaves it at 0.
@export var dash_diagonal_grace := 2

# Set by BixbyBeastScript before this enters the tree: the beast who coughed him up. Null in the test scene.
var bixby: Node
# The test scene: no Bixby, no takeover, straight into the takeover's end state and the fight.
@export var start_active := false

# Under everyone: the flood, the ice, the ridges, the cracks, the pillar's shadow, his own shadow.
@export var floor_layer: Node2D
# The waves, over the floor and still under everyone.
@export var wave_layer: Node2D
# Over everyone: the gust, the cold breath, the slam bursts, the splashes.
@export var fx_layer: Node2D

@onready var air: Node2D = $Air
@onready var sprite: Sprite2D = $Air/Sprite2D
@onready var hurtbox: Area2D = $Hurtbox
@onready var hurtbox_shape: CollisionShape2D = $Hurtbox/CollisionShape2D
@onready var state_machine = $StateManager

var pillar: Node2D
# His wall of pillars either side of his own (LiamRow).
var row: Node2D
# The steam over the ring in attacks 3 and 4 (LiamSteam).
var steam: Node2D
var flood: Node2D
var shadow: Node2D
# px over his floor point.
var height := 0.0
var facing_left := false

#AUDIO
var music_player: AudioStreamPlayer
var hit_sfx_player: AudioStreamPlayer
var victory_sfx_player: AudioStreamPlayer
var sfx_players := {}
# How many times his theme has been started, for the tests to prove it is only ever once.
var music_starts := 0

#UI (BossHealthBarUI and BreakGaugeUI build it at the takeover's ride)
var hud_layer: CanvasLayer
var health_bar: Control
var gauge_bar: Control
var hud_fade: Tween
var break_gauge: Node

var defeated := false
var hits_this_window := 0
var punches := PunchAllowance.new()
# One finisher daze per window; each window clears it.
var daze_used := false
var fight_clock := 0.0
var last_contact_hit_time := -INF
var sprite_base_position := Vector2.ZERO
var body_box := &"standing"

var current_anim := &""
var anim: Dictionary = {}
# What it plays (LiamArtLayout.clip): an `all` pose's every frame on its sheet.
var anim_frames: Array = []
var anim_times: Array = []
var anim_loop := false
# A final sheet's offset for his cell and anchor, facing right; mirrored with him.
var sheet_offset := Vector2.ZERO
var sheet_offset_flips := false
var anim_step := 0
var anim_clock := 0.0
var anim_next := &""
var anim_done := false
# A talk pose typing on the stand-in squashes him.
var talking := false
var motion_clock := 0.0
# The stand-in's slimed_sit: the beast's own frame 9 cut round him.
var slimed_texture: Texture2D


func _ready() -> void:
	add_to_group(FightOutro.BOSS_GROUP)
	hurtbox.area_entered.connect(_on_hurtbox_entered)
	# The exported value is only set after the variable above was initialised.
	boss_health = max_health
	sprite_base_position = sprite.position
	hud_layer = CanvasLayer.new()
	add_child(hud_layer)
	var scene := get_tree().current_scene
	var player: Node = scene.get_node_or_null(FightOutro.PLAYER_PATH) if scene else null
	if player:
		_add_break_gauge(player)
		player.dash_diagonal_grace = dash_diagonal_grace
	_build_sounds()
	_build_stage.call_deferred()
	set_body_box(&"standing")
	play_anim(&"perch_idle")
	air.visible = start_active


func _physics_process(delta: float) -> void:
	fight_clock += delta


func get_health_ratio() -> float:
	return float(boss_health) / float(max_health)


func get_max_health() -> int:
	return max_health


# His scene's root is still setting its children up while he readies, so the pillar goes in a step later: before the
# takeover's first beat can ask for it.
func _build_stage() -> void:
	flood = LiamFlood.new()
	flood.name = "Flood"
	floor_layer.add_child(flood)
	shadow = Node2D.new()
	shadow.name = "LiamShadow"
	if Layout.final_shadow():
		var sheet := Sprite2D.new()
		sheet.texture = load(Layout.SHADOW_SHEET)
		sheet.scale = Vector2.ONE * Layout.SCALE
		sheet.modulate.a = Layout.SHADOW_ALPHA
		shadow.add_child(sheet)
	else:
		var shade := Polygon2D.new()
		shade.polygon = Layout.ellipse(Layout.PLACEHOLDER_SHADOW.radii)
		shade.color = Layout.PLACEHOLDER_SHADOW.color
		shadow.add_child(shade)
	shadow.visible = false
	floor_layer.add_child(shadow)
	pillar = LiamPillar.new()
	pillar.name = "Pillar"
	pillar.host = state_machine
	pillar.floor_layer = floor_layer
	get_parent().add_child(pillar)
	get_parent().move_child(pillar, get_index())
	row = LiamRow.new()
	row.name = "Row"
	get_parent().add_child(row)
	steam = LiamSteam.new()
	steam.name = "Steam"
	steam.host = state_machine
	get_parent().add_child(steam)


func _process(delta: float) -> void:
	motion_clock += delta
	_step_anim(delta)
	_show_motion()
	if is_instance_valid(shadow) and shadow.visible:
		shadow.global_position = global_position.round()


#THE BREAK GAUGE

func _add_break_gauge(player: Node) -> void:
	break_gauge = BossBreakGauge.new()
	break_gauge.name = "BreakGauge"
	break_gauge.boss = self
	break_gauge.player = player
	break_gauge.owns_attack = func(id: StringName) -> bool: return str(id).begins_with("liam_")
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


# Down from a Break or a juggle, or owed a Break for his fall: the gauge's lock waits for this.
func is_down() -> bool:
	return is_broken() or is_juggled() or state_machine.break_owed


#WHERE HE STANDS

# His feet `height` px over his floor point, in whole pixels.
func place() -> void:
	global_position = global_position.round()
	air.position = Vector2(0, -roundf(height))


# On the pillar's top wherever it is, as far as it has risen.
func stand_on_pillar() -> void:
	global_position = pillar.global_position
	height = pillar.top_height()
	place()


# On the mat at `point`, his shadow under him and his hurtbox a target.
func stand_on_floor(point: Vector2) -> void:
	global_position = point.round()
	height = 0.0
	place()
	shadow.visible = true
	set_target_active(true)


# On the pillar for the fight: not a target, no shadow of his own, and the boss HUD faded out of his way.
func perch() -> void:
	shadow.visible = false
	set_target_active(false)
	set_hurtbox_active(false)
	set_hud_alpha(state_machine.pillar_hud_fade_alpha)


# Off the pillar by any way out of it: the HUD back.
func leave_perch() -> void:
	set_hud_alpha(1.0)


func feet_position() -> Vector2:
	return global_position - Vector2(0, height)


# A point measured on a pose (LiamArtLayout.point), in the world: on the frame showing when it is the pose he is in.
func pose_point(key: StringName, anim_name := current_anim, frame := -1) -> Vector2:
	if frame < 0 and anim_name == current_anim:
		frame = sprite.frame
	var local := Layout.point(key, anim_name, frame)
	if facing_left:
		local.x = -local.x
	return feet_position() + local


func set_facing(left: bool) -> void:
	facing_left = left
	_show_frame()


#ANIMATION

# A non-looping animation holds its last frame when it ends, unless `next_anim` follows it.
func play_anim(anim_name: StringName, next_anim: StringName = &"") -> void:
	current_anim = anim_name
	anim = Layout.ANIMS[anim_name]
	var clip := Layout.clip(anim_name)
	anim_frames = clip.frames
	anim_times = clip.times
	anim_loop = clip.loop
	anim_next = next_anim
	anim_step = 0
	anim_clock = 0.0
	anim_done = false
	motion_clock = 0.0
	reset_sprite_pose()
	sheet_offset_flips = false
	if Layout.uses_final(anim_name):
		var sheet: Texture2D = load(Layout.sheet_path(anim_name))
		var cell := Layout.cell(anim_name)
		sprite.texture = sheet
		sprite.hframes = roundi(sheet.get_width() / cell.x)
		sheet_offset = cell / 2.0 - Layout.anchor(anim_name)
		sheet_offset_flips = true
		sprite.offset = sheet_offset
	elif anim_name == &"slimed_sit":
		_show_slimed_stand_in()
	else:
		sprite.texture = load(Layout.LIAM_SPRITE)
		sprite.hframes = 1
		sprite.offset = Vector2(0, -Layout.PLACEHOLDER_CELL.y / 2.0)
	_show_frame()


# The sprite as a plain sheet draws it: no stand-in motion, no region, centred.
func reset_sprite_pose() -> void:
	sprite.region_enabled = false
	sprite.centered = true
	sprite.rotation = 0.0
	sprite.scale = Vector2.ONE * Layout.SCALE
	sprite.position = sprite_base_position
	sprite.vframes = 1
	sprite.frame = 0


func _show_slimed_stand_in() -> void:
	if slimed_texture == null:
		slimed_texture = load(Layout.BixbyBeastArtLayout.DEFEAT_SHEET)
	var cut := Layout.defeat_region(Layout.DEFEAT_LIAM_REGION, Layout.DEFEAT_LIAM_FEET + Vector2(0, 1))
	sprite.texture = slimed_texture
	sprite.hframes = 1
	sprite.region_enabled = true
	sprite.region_rect = cut.rect
	sprite.centered = false
	sprite.offset = cut.offset


# A state's talk pose while one of his lines types: the gesture, then its shut pose.
func show_talk(gesture: StringName, typing: bool) -> void:
	var want := gesture if typing else StringName(String(gesture) + "_shut")
	if current_anim != want:
		play_anim(want)
	talking = typing and not Layout.uses_final(want)


func _step_anim(delta: float) -> void:
	if anim.is_empty() or anim_done:
		return
	anim_clock += delta
	var times: Array = anim_times
	while anim_clock >= times[mini(anim_step, times.size() - 1)]:
		anim_clock -= times[mini(anim_step, times.size() - 1)]
		if anim_step < anim_frames.size() - 1:
			anim_step += 1
		elif anim_loop:
			anim_step = 0
		else:
			anim_done = true
			var finished := current_anim
			if anim_next != &"":
				play_anim(anim_next)
			anim_finished.emit(finished)
			return
		_show_frame()


func _show_frame() -> void:
	if anim.is_empty():
		return
	if sprite.hframes > 1:
		sprite.frame = anim_frames[anim_step]
	sprite.flip_h = facing_left
	# flip_h mirrors the picture inside its rect, not the offset: an off-centre anchor is mirrored here.
	if sheet_offset_flips:
		sprite.offset = Vector2(-sheet_offset.x if facing_left else sheet_offset.x, sheet_offset.y)


# The stand-in's motion for the pose he is in (LiamArtLayout.PLACEHOLDER_MOTION), and his squash while he talks. Never
# while the juggle owns his sprite, in the air or lying beaten on its down loop.
func _show_motion() -> void:
	if anim.is_empty() or current_anim == &"" or is_juggled() or state_machine.states["Juggled"].lingering:
		return
	if Layout.uses_final(current_anim) or current_anim == &"slimed_sit":
		return
	var motion: Dictionary = Layout.PLACEHOLDER_MOTION.get(current_anim, {})
	var rot: float = motion.get("rot", 0.0)
	if motion.has("wave"):
		rot += motion.wave[0] * sin(motion_clock * TAU * motion.wave[1])
	var squash: Vector2 = motion.get("squash", Vector2.ONE)
	if talking:
		squash *= Layout.TALK_SQUASH if int(motion_clock / Layout.TALK_SQUASH_TIME) % 2 == 0 else Vector2.ONE
	var lift := Vector2.ZERO
	if motion.has("bob"):
		lift.y = -absf(sin(motion_clock * PI * motion.bob[1])) * motion.bob[0] * Layout.SCALE
	if motion.get("lie", false):
		rot += Layout.PLACEHOLDER_LIE.rotation
		lift += Layout.PLACEHOLDER_LIE.shift
	sprite.rotation = deg_to_rad(-rot if facing_left else rot)
	sprite.scale = squash * Layout.SCALE
	sprite.position = sprite_base_position + lift.round()


#SOUNDS

func _build_sounds() -> void:
	music_player = AudioStreamPlayer.new()
	music_player.name = "MusicPlayer"
	music_player.stream = load(Layout.THEME)
	music_player.volume_db = Layout.THEME_DB
	if music_player.stream is AudioStreamWAV:
		music_player.stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
		music_player.stream.loop_begin = 0
		music_player.stream.loop_end = int(music_player.stream.get_length() * music_player.stream.mix_rate)
	add_child(music_player)
	hit_sfx_player = AudioStreamPlayer.new()
	hit_sfx_player.stream = load("res://Assets/Audio/SFX/hit_impact.ogg")
	add_child(hit_sfx_player)
	victory_sfx_player = AudioStreamPlayer.new()
	victory_sfx_player.stream = load("res://Assets/Audio/SFX/victory_fanfare.ogg")
	add_child(victory_sfx_player)
	for key in Layout.SFX:
		var spec: Dictionary = Layout.SFX[key]
		var player := AudioStreamPlayer.new()
		player.stream = load(spec.stream)
		player.pitch_scale = spec.pitch
		player.volume_db = spec.volume_db
		add_child(player)
		sfx_players[key] = player


func play_sfx(key: StringName) -> void:
	var player: AudioStreamPlayer = sfx_players.get(key)
	if player:
		player.play()


func stop_sfx(key: StringName) -> void:
	var player: AudioStreamPlayer = sfx_players.get(key)
	if player:
		player.stop()


# Once, whoever asks first: the takeover's ride, or its skip.
func start_music() -> void:
	if music_starts > 0:
		return
	music_starts += 1
	music_player.play()


#THE HUD

# His block, swept to full over `time` (0 lands it full): his bar and his Break gauge under it. Once.
func show_hud(time: float) -> void:
	if health_bar != null:
		return
	health_bar = BossHealthBarUI.create({
		"rows": [{"key": &"liam", "max": max_health, "value": 0}],
		"plate": &"liam",
		"text": BAR_NAME,
	})
	hud_layer.add_child(health_bar)
	if break_gauge:
		gauge_bar = BreakGaugeUI.new()
		gauge_bar.gauge = break_gauge
		hud_layer.add_child(gauge_bar)
		gauge_bar.position = health_bar.break_gauge_anchor()
	health_bar.refill_row(0, boss_health, time)


# The whole block to `alpha` over `time`, bound to the bar so a pause or a freeze holds it with the fight.
func set_hud_alpha(alpha: float, time := HUD_FADE_TIME) -> void:
	if not health_bar:
		return
	if hud_fade:
		hud_fade.kill()
	if time <= 0.0:
		for bar: Control in [health_bar, gauge_bar]:
			if bar:
				bar.modulate.a = alpha
		return
	hud_fade = health_bar.create_tween().set_parallel()
	for bar: Control in [health_bar, gauge_bar]:
		if bar:
			hud_fade.tween_property(bar, "modulate:a", alpha, time)


func hud_alpha() -> float:
	return health_bar.modulate.a if health_bar else 0.0


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


#HIS HURTBOX

# One of LiamArtLayout.BODY_BOXES, mirrored as he faces.
func set_body_box(key: StringName) -> void:
	body_box = key
	var box: Rect2 = Layout.BODY_BOXES[key]
	if facing_left:
		box.position.x = -box.end.x
	hurtbox_shape.position = box.get_center()
	(hurtbox_shape.shape as RectangleShape2D).size = box.size


# Punches only reach him in his windows.
func set_hurtbox_active(active: bool) -> void:
	# Deferred: monitoring can't change inside a physics flush.
	hurtbox.set_deferred("monitoring", active)
	hurtbox.set_deferred("monitorable", active)


# Whether the player faces him and aims at him at all: in the cut and on the ground, never on the pillar.
func set_target_active(on: bool) -> void:
	if on and not hurtbox.is_in_group("boss_target"):
		hurtbox.add_to_group("boss_target")
	elif not on and hurtbox.is_in_group("boss_target"):
		hurtbox.remove_from_group("boss_target")


#COMBAT

func _on_hurtbox_entered(area: Area2D) -> void:
	if boss_health <= 0 or not area.is_in_group("player attack"):
		return
	# The phantom-hit filter every boss has: a punch that connects as its hitbox switches on is reported again when
	# PlayerPunching switches the hitbox off, which would eat the hit cap.
	if not area.monitorable and fight_clock - last_contact_hit_time < PHANTOM_HIT_WINDOW:
		return
	if area.get_parent().combo.resolve_punch(self) > 0 and area.monitorable:
		last_contact_hit_time = fight_clock


# A window opening: a fresh hit cap and a fresh daze.
func begin_window() -> void:
	hits_this_window = 0
	daze_used = false


# Punches only land in his punish windows (LiamStateMachine.is_open), all of them on the ground.
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
		# area_entered fires mid physics flush; deferring keeps the state Exit/Enter code the defeat runs from having
		# to be flush-safe.
		call_deferred("_on_defeated")
	return dealt


# The player's finisher (PlayerFinisher): a charged third punch in an open window dazes him, once a window.
func can_be_dazed() -> bool:
	return not defeated and boss_health > 0 and not daze_used and state_machine.is_open()


# The finisher draws its own daze stars over the Break's.
func enter_daze() -> void:
	daze_used = true
	if is_broken():
		state_machine.current_state.show_stars(false)


func exit_daze(finisher_landed: bool) -> void:
	if is_broken() and not finisher_landed:
		state_machine.current_state.show_stars(true)


# Ended by the finisher. Crashed from a juggle, he lies a beat before he gets up; out of any other window he stays
# down, staggered, and gets up after it.
func end_recovery(stagger_time: float) -> bool:
	if defeated or boss_health <= 0:
		return false
	if is_juggled():
		state_machine.current_state.recover(stagger_time)
		return true
	if not state_machine.is_open():
		return false
	state_machine.end_window(stagger_time)
	return true


# Past the hit cap, which the combo that led to it has used up.
func take_finisher(amount: int) -> int:
	if not state_machine.is_open():
		return 0
	return _apply_damage(amount)


func get_daze_anchor() -> Vector2:
	if is_broken():
		return state_machine.current_state.head_point()
	if Layout.LYING.has(current_anim):
		return pose_point(&"daze", &"downed")
	return feet_position() + Layout.HEAD_TOP + Vector2(0, -Layout.DAZE_GAP)


func get_finisher_hurtbox() -> Area2D:
	return hurtbox


# The single-bar uppercut's shove, along the floor, inside where he may stand and never toward the player.
func knock_back(push: Vector2, time: float) -> void:
	var bounds: Rect2 = state_machine.stand_rect()
	var target := (global_position + push).clamp(bounds.position, bounds.end)
	var player: Node2D = state_machine.get_player()
	if player and target.distance_to(player.global_position) < global_position.distance_to(player.global_position):
		return
	create_tween().tween_property(self, "global_position", target, time).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)


#THE JUGGLE (PlayerFinisher's tiered uppercut; only the Break pays it)

func can_be_juggled() -> bool:
	return JUGGLE_ENABLED and not defeated and boss_health > 0 and is_broken()


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


# A juggle that kills him ends with him still in the air, and the outro's first line would otherwise open over him
# mid-fall.
func outro_line_delay(_player_won: bool) -> float:
	if is_juggled():
		return Layout.juggle().outro_delay
	return 0.0


#THE PARRY'S STAGGER: nothing of his staggers him (liam_tsunami has no parry_stagger).

func can_parry_stagger(_hit: RefCounted) -> bool:
	return false


func parry_stagger(_duration: float) -> void:
	pass


#THE END OF THE FIGHT

func _on_defeated() -> void:
	if defeated:
		return
	defeated = true
	set_hurtbox_active(false)
	state_machine.enter_defeated()
	win()


# Beating Liam wins the fight: the fanfare, the crowd, his outro and Victory, and Jordan next.
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
	var flash := create_tween()
	flash.tween_property(sprite, "modulate", Color(1, 1, 1), 0.15)
	HitStop.freeze(get_tree(), 0.06)
