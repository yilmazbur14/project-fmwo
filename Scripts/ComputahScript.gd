extends CharacterBody2D

# COMPUTAH, boss 2. One body, one health bar, one node that is both the fighter and the fight: his
# art, his health and his hurtbox, and the HUD, the music and the end of the fight that used to live
# in a separate coordinator when Greyson fought alongside him. Carter's fight is built the same way
# and is the shape this follows.
#
# Greyson is not in this scene: he speaks in the pre-fight lines, and once Computah is beaten he storms the
# ring in a scene of his own (greyson_follows, _hand_to_greyson) and the fight is his from there.
#
# HE MUST STAY IN FightOutro.BOSS_GROUP until that hand-off, when Greyson takes his place in it.
# PlayerHype.is_inert() scans that group for a node with can_be_dazed() and, finding none, silently makes
# hype inert and hides the meter with no error at all.
#
# THE CHARGE STATE IS A FRAME OFFSET, NOT A TINT. computah_idle and computah_run each hold the same
# four-frame cycle three times over, so `frame = charge_state * 4 + cycle_frame` changes how many
# chest cells are lit, what colour they are and how the antenna ball glows, all at once. That
# three-way read is what makes the battery legible at a glance; a colour swap would keep four lit
# cells and lose the count.

# A non-looping animation reached the end of its last frame.
signal anim_finished(anim_name: StringName)

const HitStop := preload("res://Scripts/HitStop.gd")
const FightOutro := preload("res://Scripts/FightOutro.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const Layout := preload("res://Scripts/ComputahArtLayout.gd")
const BossHealthBarUI := preload("res://Scripts/BossHealthBarUI.gd")
const BossBreakGauge := preload("res://Scripts/BossBreakGauge.gd")
const BreakGaugeUI := preload("res://Scripts/BreakGaugeUI.gd")
# What he says once the fight is over, under player_won and player_lost.
const OUTRO_DIALOGUE := "res://Dialogue/ComputahOutro.dialogue"
# This fight's place in the order; GameProgress decides what follows it.
const FIGHT_SCENE := "res://Scenes/Bosses/ComputahBossFightScene.tscn"
# The fight's second half: beaten, he hands the ring to Greyson, who tears off his cannon arm and fights on as
# the real boss of FIGHT 06 (GreysonTakeover). With greyson_follows off, his fight ends where it always has.
const GREYSON_SCENE := "res://Scenes/Bosses/GreysonScene.tscn"
@export var greyson_follows := true
var greyson_scene: PackedScene
# Greyson has torn his cannon arm off.
var armless := false

# FIGHT 06's first half is meant to be easy, the beam alone (ComputahStateMachine.live_attacks), so that Greyson's
# half lands as the surprise (the user, 2026-09-24, at 8: two clean beam openings). The user doubled every boss's
# health on 2026-09-25 (16) and raised it 25% on 2026-09-30, so it is 20: an opening's clean chain takes 4 and the
# finisher its POW earns takes 5 more, so two clean openings with both finishers leave him on 2 and A THIRD ENDS
# IT, and without the finishers it takes FIVE clean chains exactly.
@export var max_health := 20
# What the whole rotation was sized for, which comes back with the mine field and the overload: the overload is a
# DPS check whose threshold has to sit at or under 15% of his health. It predates the doubling (2026-09-25) and
# was left as it was.
const FULL_ROTATION_HEALTH := 48
var boss_health := max_health
const MAX_HITS_PER_WINDOW := 3
# Each opening takes the damage of a clean chain of MAX_HITS_PER_WINDOW punches (PunchAllowance).
const PunchAllowance := preload("res://Scripts/PunchAllowance.gd")
const PHANTOM_HIT_WINDOW := 0.5

#BREAK GAUGE (BossBreakGauge)
# His own numbers, not on the "N reads from empty" rule the later fights share. The parry, dodge, guard
# break and unlock numbers are BossBreakGauge's defaults, which he was tuned on.
# grab_parry_gain: the pounce is the one parry worth it, the only thing in the fight a parry both stops
#   and staggers. Nothing of his takes the plain parry_gain.
# hit_loss: HEAVIER THAN ERIC'S 20, and deliberately applying to the beam and the failed uppercut too:
#   this fight's signature mistake is being caught, and a catch already costs damage and 30 stamina. The
#   gauge is the third of those three, and it is one number in one place - the drain is
#   BossBreakGauge's own, off PlayerDefense.hit_taken, so no attack calls it by hand.
# punch gains: HALF ERIC'S, because this fight is twice as long as the gauge was tuned against. What
#   fills it here is READING him - dodging the beam, parrying the pounce - and punches in a window are
#   the reward that read already earned, not a second one. At Eric's 8/14 a competent player banks
#   about 92 of 100 per beam-and-mine-field pair, of which 60 is punching, and a 48-health fight is
#   about six of those pairs: five Breaks. At 4/7 a pair banks about 62, which is the two or three a
#   fight should hand out. Carter's gauge makes the same cut harder, to zero.
# broken_time: the Break window he was tuned on, battery_window plus parry_stagger_bonus, 3.2 + 0.8 s.
const BREAK := {
	"parry_gain": 15.0,
	"grab_parry_gain": 20.0,
	"perfect_dodge_gain": 12.0,
	"punch_gain": 4.0,
	"charged_punch_gain": 7.0,
	"hit_loss": 30.0,
	"guard_break_loss": 35.0,
	"unlock_delay": 3.0,
	"broken_time": 4.0,
}

# His own theme. Same level as Eric's, so walking from one fight to the next does not jump. The file
# is still named for the pair it was written for; renaming it would mean re-cutting it through the
# recording pipeline, which is not this change.
const THEME := "res://Assets/Audio/Music/greyson_theme.wav"
const THEME_DB := -7.0

@onready var sprite: Sprite2D = $Sprite2D
@onready var aura: Node2D = $Aura
@onready var battery: Node2D = $Battery
@onready var overload: Node2D = $Overload
@onready var hurtbox: Area2D = $Hurtbox
@onready var hurtbox_shape: CollisionShape2D = $Hurtbox/CollisionShape2D
@onready var collision_shape: CollisionShape2D = $CollisionShape2D
@onready var grab_area: Area2D = $GrabArea
@onready var grab_shape: CollisionShape2D = $GrabArea/CollisionShape2D
# Named `state_machine` because that is what the rest of the game reaches for on a boss.
@onready var state_machine = $StateManager

#AUDIO
@onready var music_player: AudioStreamPlayer = $MusicPlayer
@onready var victory_sfx_player: AudioStreamPlayer = $VictorySfxPlayer
@onready var hit_sfx_player: AudioStreamPlayer = $HitSfxPlayer

#UI (BossHealthBarUI and BreakGaugeUI build it at runtime)
var hud_layer: CanvasLayer
var health_bar: Control
# His daze meter (BossBreakGauge). A fight-long one, like Eric's rather than Carter's per-attack one:
# reading this fight fills it and being caught by it drains it, and filling it drops him.
var break_gauge: Node

var music_base_db := 0.0
var music_duck: Tween

var defeated := false
var hits_this_window := 0
var punches := PunchAllowance.new()
# How many punches this window takes: the damage of a clean chain that long (PunchAllowance).
var window_cap := MAX_HITS_PER_WINDOW
# HALF-HEARTS PUT INTO HIM SINCE THE WINDOW OPENED, which is what the overload's DPS check is
# measured in. Written here and read a physics step later by whoever opened the window; deliberately
# never acted on inside take_punch, so the punch that clears a threshold can't also race the
# finisher's deferred start. Damage, not punches: a charged punch is worth two.
var damage_this_window := 0
var daze_used := false

var fight_clock := 0.0
var last_contact_hit_time := -INF

var facing_left := false
# The pose his hurtbox is standing on, kept so a flip can re-hang it on the mirrored body.
var body_pose := &"idle"
var sprite_base_position: Vector2
var aura_clock := 0.0

# 0 full, 1 half, 2 low: the row of computah_idle and computah_run his frames are taken from.
var charge_state := 0
var battery_shell: Polygon2D
var battery_fill: Polygon2D
var battery_flashing := false
var battery_clock := 0.0

# The overload's race gauge: his charge on the top row, the player's damage in cells on the bottom.
var overload_charge_fill: Polygon2D
var overload_cells: Array[Polygon2D] = []
var overload_flashing := false
var overload_clock := 0.0

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
	sprite.scale = Vector2.ONE * Layout.SCALE
	sprite.offset = Layout.computah_offset()
	set_body_box(&"idle")
	_build_aura()
	_build_battery()
	_build_overload()
	# Before the HUD: the HUD builds the gauge's bar, and only if there is a gauge to draw.
	var player: Node = get_tree().current_scene.get_node_or_null(FightOutro.PLAYER_PATH) if get_tree().current_scene else null
	if player:
		_add_break_gauge(player)
	_build_hud()
	play_anim(&"idle")
	if greyson_follows:
		greyson_scene = load(GREYSON_SCENE)

	# "Two Bars", written for this fight - see art_source/music/greyson_theme.rb. One 16-bar cycle
	# cut to the beat, so LOOP_FORWARD runs it end to end with no seam.
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
	# Placeholders: he has no sounds of his own yet.
	victory_sfx_player.stream = load("res://Assets/Audio/SFX/victory_fanfare.ogg")
	hit_sfx_player.stream = load("res://Assets/Audio/SFX/hit_impact.ogg")
	$WindowSfxPlayer.stream = load("res://Assets/Audio/SFX/downed_stinger.ogg")
	$ChaseSfxPlayer.stream = load("res://Assets/Audio/SFX/wrestler_charge.ogg")
	$PounceSfxPlayer.stream = load("res://Assets/Audio/SFX/whirlwind_whoosh.ogg")
	$CatchSfxPlayer.stream = load("res://Assets/Audio/SFX/wrestler_collision.ogg")
	$PunchSfxPlayer.stream = load("res://Assets/Audio/SFX/hit_impact.ogg")
	$BeamChargeSfxPlayer.stream = load("res://Assets/Audio/SFX/laser_charge.ogg")
	$BeamLockSfxPlayer.stream = load("res://Assets/Audio/SFX/break_sting.wav")
	$BeamFireSfxPlayer.stream = load("res://Assets/Audio/SFX/rocket_launch.ogg")


#HIS BREAK GAUGE
# Reading his fight fills it - parries, perfect dodges and punches that land - and being caught by it
# drains it. Full, it drops him where he stands, which is the daze the player's finisher needs.
func _add_break_gauge(player: Node) -> void:
	break_gauge = BossBreakGauge.new()
	break_gauge.name = "BreakGauge"
	break_gauge.boss = self
	break_gauge.player = player
	# Every computah_ attack is his; his ids are regular, so a prefix is the whole test. It is what fills
	# the gauge as well as what drains it, so earns_from stays unset.
	break_gauge.owns_attack = func(id: StringName) -> bool: return str(id).begins_with("computah_")
	var strong: Array[StringName] = [&"computah_chase"]
	break_gauge.strong_parry_ids = strong
	break_gauge.parry_gain = BREAK.parry_gain
	break_gauge.grab_parry_gain = BREAK.grab_parry_gain
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


# BREAKING HIM OUTRIGHT, and the overload's reward is the only thing that does it. It FILLS THE GAUGE
# rather than routing round it: one road to the top, so the sting, the lock and the daze behind it are
# the gauge's own and there is no second kind of Break to keep in step with this one. The player's
# banked progress is not wasted either - the gauge was filling the whole time, including off the
# overload's own punches.
# Returns whether the gauge took it. A locked gauge refuses, which is the pacing gate; a build with no
# gauge at all refuses too, and the caller opens a plain window instead.
func break_now() -> bool:
	if break_gauge == null:
		return false
	return break_gauge.add(break_gauge.max_value)


# BossBreakGauge._physics_process asks this every step, unconditionally, and its wait before it takes
# anything again starts once this goes false. Down is the Break and the juggle it pays out, not every
# open window: counting his vents would hold the gauge shut through the next one that opens, which on
# the beam is 2.6 s after he gets up.
func is_down() -> bool:
	return is_broken() or is_juggled()


func is_broken() -> bool:
	return state_machine != null and state_machine.current_state == state_machine.states.get("Broken")


func is_juggled() -> bool:
	return state_machine != null and state_machine.current_state == state_machine.states.get("Juggled")


func start_music() -> void:
	if music_player and not music_player.playing:
		music_player.play()


func get_health_ratio() -> float:
	return float(boss_health) / float(max_health)


func get_max_health() -> int:
	return max_health


func _physics_process(delta: float) -> void:
	fight_clock += delta


# The hurtbox of the pose he is being left in: his standing chassis, the vent's kneel or the floor.
# The vent and the floor are different bands, so a window that swapped in one box for both would put
# punches through the air over a kneeling robot.
func set_body_box(pose: StringName) -> void:
	body_pose = pose
	_apply_body_box()


func _apply_body_box() -> void:
	var local := Layout.computah_rect(Layout.computah_box(body_pose), facing_left)
	hurtbox_shape.position = local.get_center()
	(hurtbox_shape.shape as RectangleShape2D).size = local.size


# Behind his sprite and on its own node rather than a child of it: boss.sprite has to stay the body
# sprite, which PlayerFinisher._flash and PlayerCombo._charged_feedback both write to.
func _build_aura() -> void:
	var spec := Layout.PLACEHOLDER_AURA
	var glow := Polygon2D.new()
	glow.polygon = Layout.ellipse(Layout.AURA_COMPUTAH.radii, spec.points)
	glow.color = spec.color
	glow.position = Layout.AURA_COMPUTAH.centre
	glow.material = Layout.additive()
	aura.add_child(glow)
	aura.modulate.a = Layout.AURA_ALPHA
	aura.hide()


#ANIMATION

# A non-looping animation holds its last frame when it ends, unless `next_anim` follows it.
func play_anim(anim_name: StringName, next_anim: StringName = &"") -> void:
	current_anim = anim_name
	anim = Layout.computah_anim(anim_name)
	anim_next = next_anim
	anim_step = 0
	anim_clock = 0.0
	anim_done = false
	var sheet: Texture2D = load(anim.sheet)
	sprite.frame = 0
	sprite.texture = sheet
	sprite.hframes = roundi(sheet.get_width() / Layout.C_FRAME.x)
	sprite.vframes = 1
	_show_anim_frame()


func _process(delta: float) -> void:
	if aura.visible:
		aura_clock += delta
		var spec := Layout.PLACEHOLDER_AURA
		var pulse: Array = spec.pulse
		aura.scale = Vector2.ONE * lerpf(pulse[0], pulse[1], absf(sin(aura_clock * PI / spec.pulse_time)))
	if battery.visible and battery_flashing:
		battery_clock += delta
		battery.visible = int(battery_clock / Layout.BATTERY_GAUGE.flash_interval) % 2 == 0
	if overload.visible and overload_flashing:
		overload_clock += delta
		overload_charge_fill.visible = int(overload_clock / Layout.OVERLOAD_GAUGE.flash_interval) % 2 == 0
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
	if anim.get("charge_rows", false):
		frame += charge_state * Layout.CHARGE_CYCLE
	sprite.frame = frame
	sprite.flip_h = anim.get("flips", false) and facing_left


# 0 full, 1 half, 2 low. Only the two sheets drawn three times over follow it.
func set_charge_state(state: int) -> void:
	state = clampi(state, 0, 2)
	if charge_state == state:
		return
	charge_state = state
	if not anim.is_empty():
		_show_anim_frame()


func set_facing(left: bool) -> void:
	if facing_left == left:
		return
	facing_left = left
	_show_anim_frame()
	# His boxes are traced off right-facing frames and he has no symmetric pose left, so they mirror
	# with the drawing.
	_apply_body_box()


func face_toward(point: Vector2) -> void:
	set_facing(point.x < global_position.x)


#THE BATTERY GAUGE
# The chase clock is the battery; his own frames carry the coarse three-way read and this is the
# precise one.

func _build_battery() -> void:
	var spec := Layout.BATTERY_GAUGE
	var size: Vector2 = spec.size
	battery.position = Layout.C_BATTERY_OFFSET
	battery_shell = Polygon2D.new()
	battery_shell.polygon = Layout.centred_rect(size)
	battery_shell.color = spec.shell
	battery.add_child(battery_shell)
	var rim := Line2D.new()
	rim.points = battery_shell.polygon
	rim.closed = true
	rim.width = spec.border
	rim.default_color = spec.edge
	battery.add_child(rim)
	battery_fill = Polygon2D.new()
	battery_fill.polygon = Layout.centred_rect(size - Vector2(spec.border, spec.border) * 2.0)
	battery_fill.color = spec.fills[0]
	battery.add_child(battery_fill)
	battery.hide()


func show_battery(on: bool) -> void:
	battery_flashing = false
	battery_clock = 0.0
	battery.visible = on
	if on:
		set_battery(1.0, false)


# `left` runs 1 to 0 over the chase; the gauge drains, recolours with the charge state and flashes
# over the last seconds.
func set_battery(left: float, flashing: bool) -> void:
	if not battery_fill:
		return
	var spec := Layout.BATTERY_GAUGE
	var inner: Vector2 = Vector2(spec.size) - Vector2(spec.border, spec.border) * 2.0
	var width := inner.x * clampf(left, 0.0, 1.0)
	battery_fill.polygon = PackedVector2Array([
		Vector2(-inner.x / 2.0, -inner.y / 2.0), Vector2(-inner.x / 2.0 + width, -inner.y / 2.0),
		Vector2(-inner.x / 2.0 + width, inner.y / 2.0), Vector2(-inner.x / 2.0, inner.y / 2.0),
	])
	battery_fill.color = spec.fills[charge_state]
	if flashing != battery_flashing:
		battery_flashing = flashing
		battery_clock = 0.0
		if not flashing:
			battery.visible = true


#THE OVERLOAD'S RACE GAUGE
# TWO ROWS, NOT ONE TUG-OF-WAR BAR: his charge on top, the player's damage underneath, and whichever
# fills first wins. The bottom row is one cell per half-heart, so the thing the player actually needs
# - HOW MUCH MORE DAMAGE - is countable rather than implied.

func _build_overload() -> void:
	var spec := Layout.OVERLOAD_GAUGE
	overload.position = Layout.C_OVERLOAD_OFFSET
	_build_overload_row(_overload_row_y(0))
	overload_charge_fill = _overload_fill(_overload_row_y(0), spec.charge_fills[0])
	_build_overload_row(_overload_row_y(1))
	overload.hide()


func _build_overload_row(at_y: float) -> void:
	var spec := Layout.OVERLOAD_GAUGE
	var shell := Polygon2D.new()
	shell.polygon = Layout.centred_rect(spec.size)
	shell.color = spec.shell
	shell.position.y = at_y
	overload.add_child(shell)
	var rim := Line2D.new()
	rim.points = shell.polygon
	rim.closed = true
	rim.width = spec.border
	rim.default_color = spec.edge
	rim.position.y = at_y
	overload.add_child(rim)


func _overload_fill(at_y: float, colour: Color) -> Polygon2D:
	var fill := Polygon2D.new()
	fill.color = colour
	fill.position.y = at_y
	overload.add_child(fill)
	return fill


func _overload_row_y(row: int) -> float:
	var spec := Layout.OVERLOAD_GAUGE
	var step: float = (Vector2(spec.size).y + float(spec.row_gap)) / 2.0
	return -step if row == 0 else step


func _overload_inner() -> Vector2:
	var spec := Layout.OVERLOAD_GAUGE
	return Vector2(spec.size) - Vector2(spec.border, spec.border) * 2.0


# The cells are rebuilt for the threshold it is shown with, so the row always counts in the units
# the check is actually measured in rather than in a fixed number of notches.
func show_overload(on: bool, threshold := 0) -> void:
	overload_flashing = false
	overload_clock = 0.0
	overload.visible = on
	if not on:
		return
	overload_charge_fill.visible = true
	for cell in overload_cells:
		cell.queue_free()
	overload_cells.clear()
	var spec := Layout.OVERLOAD_GAUGE
	var inner := _overload_inner()
	var count: int = maxi(threshold, 1)
	var gap: float = spec.cell_gap
	var width: float = (inner.x - gap * float(count - 1)) / float(count)
	for i in count:
		var cell := _overload_fill(_overload_row_y(1), spec.damage_empty)
		cell.polygon = Layout.centred_rect(Vector2(width, inner.y))
		cell.position.x = -inner.x / 2.0 + width / 2.0 + (width + gap) * float(i)
		overload_cells.append(cell)
	set_overload(0.0, 0)


# `charge` runs 0 to 1 over his clock; `damage` is half-hearts put into him so far.
func set_overload(charge: float, damage: int) -> void:
	if not overload_charge_fill:
		return
	var spec := Layout.OVERLOAD_GAUGE
	var inner := _overload_inner()
	var filled := charge * inner.x
	overload_charge_fill.polygon = PackedVector2Array([
		Vector2(-inner.x / 2.0, -inner.y / 2.0), Vector2(-inner.x / 2.0 + filled, -inner.y / 2.0),
		Vector2(-inner.x / 2.0 + filled, inner.y / 2.0), Vector2(-inner.x / 2.0, inner.y / 2.0),
	])
	overload_charge_fill.color = spec.charge_fills[charge_state]
	for i in overload_cells.size():
		overload_cells[i].color = spec.damage_fill if i < damage else spec.damage_empty
	var flashing: bool = charge >= float(spec.flash_from)
	if flashing != overload_flashing:
		overload_flashing = flashing
		overload_clock = 0.0
		if not flashing:
			overload_charge_fill.visible = true


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


func show_aura(on: bool) -> void:
	aura_clock = 0.0
	aura.visible = on


#WHERE THINGS STAND ON HIM

# Broken, over his head on the mat, where Broken's own stars already circle; otherwise over whichever
# pose the window caught him in.
func get_daze_anchor() -> Vector2:
	if is_broken():
		return state_machine.current_state.head_point()
	return global_position + Layout.C_DAZE_ANCHOR


func tell_anchor() -> Vector2:
	return global_position + Layout.C_TELL_ANCHOR


# A point measured on his frames, in the world. It mirrors with him, because the pose it was
# measured on does.
func frame_point(point: Vector2) -> Vector2:
	return global_position + Layout.computah_local(point, facing_left)


# The muzzle of his cannon arm: where the beam leaves him. The barrel is somewhere different in every
# pose and moves through the recoil, so it is read off the frame on screen rather than fixed.
func muzzle_point() -> Vector2:
	return frame_point(Layout.computah_muzzle(current_anim, sprite.frame))


#MOVEMENT
# He writes his own position while he chases, with his collision shape off, so he neither shoves the
# player nor sticks to them. Eric's lunge does the same.

func set_solid(solid: bool) -> void:
	collision_shape.set_deferred("disabled", not solid)


func set_grab_active(active: bool) -> void:
	grab_area.set_deferred("monitoring", active)


#COMBAT

func set_hurtbox_active(active: bool) -> void:
	# Deferred: monitoring can't change inside a physics flush.
	hurtbox.set_deferred("monitoring", active)
	hurtbox.set_deferred("monitorable", active)


# He is not punchable while he chases, so the player has nothing to auto-face mid-run.
func set_target_active(on: bool) -> void:
	if on and not hurtbox.is_in_group("boss_target"):
		hurtbox.add_to_group("boss_target")
	elif not on and hurtbox.is_in_group("boss_target"):
		hurtbox.remove_from_group("boss_target")


func _on_hurtbox_entered(area: Area2D) -> void:
	if boss_health <= 0 or not area.is_in_group("player attack"):
		return
	# The same phantom-hit filter as Josh and Carter: a punch that connects as its hitbox switches on
	# is reported again when PlayerPunching switches the hitbox off, which would eat the hit cap.
	if not area.monitorable and fight_clock - last_contact_hit_time < PHANTOM_HIT_WINDOW:
		return
	if area.get_parent().combo.resolve_punch(self) > 0 and area.monitorable:
		last_contact_hit_time = fight_clock


func is_open() -> bool:
	return state_machine != null and state_machine.is_open()


# Called as a window opens, before the hurtbox does.
func begin_window(cap := MAX_HITS_PER_WINDOW) -> void:
	hits_this_window = 0
	damage_this_window = 0
	window_cap = cap
	daze_used = false


func take_punch(amount: int) -> int:
	if not is_open():
		return 0
	var allowed := punches.allow(amount, hits_this_window, window_cap)
	if allowed <= 0:
		return 0
	var dealt := _apply_damage(allowed)
	if dealt > 0:
		hits_this_window += 1
		punches.spend(dealt)
	return dealt


# Past the hit cap, which the combo that led to it has used up.
func take_finisher(amount: int) -> int:
	if not is_open():
		return 0
	return _apply_damage(amount)


#THE JUGGLE (PlayerFinisher's tiered finisher, after a Break)
# The Break window alone pays out the three-bar mash and the juggle; every other window pays the
# single-bar finisher. The juggle's shares are fractions of max health, so on every window it would end
# the fight in a handful of them.
func can_be_juggled() -> bool:
	return not defeated and boss_health > 0 and is_broken()


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


# Past the hit cap, as take_finisher, but with no open window behind it: Broken's window closes as the
# first uppercut hands him to Juggled.
func take_juggle_hit(amount: int, pitch: float) -> int:
	return _apply_damage(amount, pitch)


func get_juggle_point() -> Vector2:
	return state_machine.states["Juggled"].air_point()


# A juggle that kills him ends with him still in the air, and the outro's first line would otherwise open
# over him mid-fall.
func outro_line_delay(_player_won: bool) -> float:
	if is_juggled():
		return Layout.juggle().outro_delay
	return 0.0


# The last uppercut's shove (PlayerFinisher._knock_back, level). He moves for real, because what a
# juggle lifts is sprite.offset, the same offset the classic finisher's rock would tween. There is no
# knock_back(), so his single-bar finisher keeps that rock.
func juggle_knock_back(push: Vector2, time: float) -> void:
	var bounds: Rect2 = state_machine.runner_bounds()
	var target := (global_position + push).clamp(bounds.position, bounds.end)
	var player: Node2D = state_machine.get_player()
	# The ropes must never shove him back onto the player.
	if player and target.distance_to(player.global_position) < global_position.distance_to(player.global_position):
		return
	create_tween().tween_property(self, "global_position", target, time).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)


# No floor: he is one body with no transformation, so nothing may hold his health up.
func _apply_damage(amount: int, pitch := 1.0) -> int:
	var dealt := mini(amount, boss_health)
	if dealt <= 0:
		return 0

	boss_health -= dealt
	damage_this_window += dealt
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


func flinch() -> void:
	play_anim(&"hit", &"down")


# The player's finisher (PlayerFinisher). Only an open window can be dazed, once per window, and only
# if the state that opened it allows one: his overload is a punchable window that a finisher must not
# end, because freezing the fight mid-charge would hand out the uppercut for NOT completing the check.
func can_be_dazed() -> bool:
	return (not defeated and boss_health > 0 and not daze_used and is_open()
		and state_machine.allows_daze())


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
	# Crashed from a juggle, he lies a beat before he gets up. Juggled isn't an open window, so it goes
	# first.
	if is_juggled():
		state_machine.current_state.recover(stagger_time)
		return true
	if not is_open():
		return false
	return state_machine.end_window(stagger_time)


func get_finisher_hurtbox() -> Area2D:
	return hurtbox


# Only the pounce can be parried, and only the chase knows whether one is in the air.
func can_parry_stagger(hit: RefCounted) -> bool:
	if defeated or boss_health <= 0:
		return false
	return state_machine != null and state_machine.can_parry_stagger(hit)


func parry_stagger(duration: float) -> void:
	if defeated or boss_health <= 0:
		return
	state_machine.parry_stagger(duration)


func _on_defeated() -> void:
	defeated = true
	set_hurtbox_active(false)
	show_battery(false)
	show_overload(false)
	state_machine.enter_defeated()
	if greyson_follows and greyson_scene != null:
		_hand_to_greyson()
	else:
		_win()


func _win() -> void:
	if music_player.playing:
		music_player.stop()
	victory_sfx_player.play()
	get_tree().call_group("arena_crowd", "cheer", 2.0)
	GameProgress.next_boss_scene = _next_fight()
	FightOutro.finish_fight(get_tree(), true)


#GREYSON'S TAKEOVER

# Beaten, but the fight isn't over: Greyson storms in and takes the cannon, and the fight's end is his from here.
# So Computah leaves the boss group - FightOutro would otherwise play his lines and tell him the player lost - and
# the target group, so the player's punches and facing stop looking for him.
func _hand_to_greyson() -> void:
	if music_player.playing:
		music_player.stop()
	get_tree().call_group("arena_crowd", "cheer", 2.0)
	remove_from_group(FightOutro.BOSS_GROUP)
	set_target_active(false)
	var scene := greyson_scene.instantiate()
	scene.get_node("GreysonCharacterBody").computah = self
	get_parent().add_sibling(scene)


# FIGHT 06's second half on its own, with no fight of his first: already down where his entrance would have stood
# him, on his defeat's last frame, his bar empty, and Greyson's takeover from its first line. The main menu's
# GREYSON row starts here, in place of his entrance (ComputahStateMachine._ready); only with greyson_follows on.
func start_at_greyson() -> void:
	if defeated or greyson_scene == null:
		return
	global_position = state_machine.COMPUTAH_HOME
	set_facing(false)
	defeated = true
	boss_health = 0
	# Down before the first frame is drawn: an empty bar, not a hit draining it.
	if health_bar:
		health_bar.set_value(0, 0, BossHealthBarUI.HIT_SILENT)
	_refresh_health_bar()
	set_hurtbox_active(false)
	show_battery(false)
	show_overload(false)
	state_machine.enter_defeated()
	_hold_last_frame(&"defeat")
	_hand_to_greyson()


# Where the takeover wants him before Greyson touches him: on his own defeat's last frame, off the juggle's KO loop
# if a juggle killed him, since the arm he loses is drawn on his own sheets. A defeat still playing finishes first.
func rest_on_defeat() -> void:
	if armless:
		return
	if _off_the_juggle() or current_anim != &"defeat":
		_hold_last_frame(&"defeat")


# Greyson hauling on the arm, before it tears.
func haul_arm() -> void:
	if armless:
		return
	_off_the_juggle()
	play_anim(&"wrench_haul")


# The arm torn off on the frame it tears, then armless on the mat with the stump sparking. `instant` lands straight
# on the armless loop, for a skipped takeover.
func lose_arm(instant := false) -> void:
	if armless:
		if instant and current_anim != &"armless":
			play_anim(&"armless")
		return
	armless = true
	_off_the_juggle()
	if instant:
		play_anim(&"armless")
		return
	play_anim(&"wrench_tear", &"armless")
	shake_sprite(6.0, 6, 0.03)


# His bar and gauge gone over `time` as Greyson's come up; 0 is at once.
func retire_hud(time: float) -> void:
	if hud_layer == null or not hud_layer.visible:
		return
	var parts: Array[CanvasItem] = []
	for child in hud_layer.get_children():
		if child is CanvasItem:
			parts.append(child)
	if time <= 0.0 or parts.is_empty():
		hud_layer.hide()
		return
	var fade := hud_layer.create_tween().set_parallel()
	for part in parts:
		fade.tween_property(part, "modulate:a", 0.0, time)
	fade.chain().tween_callback(hud_layer.hide)


# Off the juggle's KO loop onto his own sheet. Whether he was on it.
func _off_the_juggle() -> bool:
	var juggled = state_machine.states.get("Juggled")
	if juggled == null or not juggled.lingering:
		return false
	juggled.stop_lingering()
	return true


func _hold_last_frame(anim_name: StringName) -> void:
	play_anim(anim_name)
	anim_step = anim.frames.size() - 1
	anim_done = true
	_show_anim_frame()


# The boss ladder owns the order and skips fights whose scene isn't built yet; "" sends the Victory
# screen back to the menu.
func _next_fight() -> String:
	if GameProgress.has_method("next_fight_after"):
		return GameProgress.next_fight_after(FIGHT_SCENE)
	return ""


# Called by FightOutro when the player loses.
func on_player_defeated() -> void:
	state_machine.enter_player_defeated()


func _hit_feedback() -> void:
	sprite.modulate = Color(3, 3, 3)
	var flash := create_tween()
	flash.tween_property(sprite, "modulate", Color(1, 1, 1), 0.15)
	shake_sprite(5.0, 4, 0.025)
	HitStop.freeze(get_tree(), 0.06)


#MUSIC
# Node-bound, so a finisher's freeze holds it and the end of the fight takes it away.

func duck_music(db: float, seconds: float) -> void:
	if music_duck:
		music_duck.kill()
	music_duck = music_player.create_tween()
	music_duck.tween_property(music_player, "volume_db", music_base_db + db, seconds)


func restore_music(seconds: float) -> void:
	duck_music(0.0, seconds)


# Nothing may be left holding the music down once the fight is over, however it ended.
func snap_music_level() -> void:
	if music_duck:
		music_duck.kill()
		music_duck = null
	music_player.volume_db = music_base_db


#THE HEALTH BAR

func _build_hud() -> void:
	hud_layer = CanvasLayer.new()
	add_child(hud_layer)

	health_bar = BossHealthBarUI.create({
		"rows": [{"key": &"computah", "max": max_health, "value": boss_health}],
		"plate": &"computah",
		"text": GameProgress.boss_name(FIGHT_SCENE),
	})
	hud_layer.add_child(health_bar)

	if break_gauge:
		var gauge_bar := BreakGaugeUI.new()
		gauge_bar.gauge = break_gauge
		hud_layer.add_child(gauge_bar)
		gauge_bar.position = health_bar.break_gauge_anchor()


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


#WORD POPUPS
# His own words over the health bar. The PlayerDefense popup set belongs to the defence coder, and
# words only this fight says don't belong in it.

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
