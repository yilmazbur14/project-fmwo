extends CharacterBody2D

# A non-looping animation reached the end of its last frame.
signal anim_finished(anim_name: StringName)

const HitStop := preload("res://Scripts/HitStop.gd")
const FightOutro := preload("res://Scripts/FightOutro.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const JoshArtLayout := preload("res://Scripts/JoshArtLayout.gd")
const JoshMonteLayout := preload("res://Scripts/JoshMonteLayout.gd")
const BossHealthBarUI := preload("res://Scripts/BossHealthBarUI.gd")
const BossBreakGauge := preload("res://Scripts/BossBreakGauge.gd")
const BreakGaugeUI := preload("res://Scripts/BreakGaugeUI.gd")
# What he says once the fight is over, under player_won and player_lost.
const OUTRO_DIALOGUE := "res://Dialogue/JoshOutro.dialogue"
const FIGHT_SCENE := "res://Scenes/Bosses/JoshBossFightScene.tscn"

#CONSTANTS
# The user doubled it from 14 (2026-09-25), raised it 25% (2026-09-30), then to 50 with the tuning round's package
# (2026-10-04).
@export var max_health := 50
var boss_health := max_health
# His phase-two split at half health. Nothing reads it since the Wild Cards rework (2026-09-28) dropped
# the split and the floor that held him above it until a phase-two cycle; kept for the attacks to come.
const PHASE_TWO_RATIO := 0.5
const MAX_HITS_PER_WINDOW := 3
# Each opening takes the damage of a clean chain of MAX_HITS_PER_WINDOW punches (PunchAllowance).
const PunchAllowance := preload("res://Scripts/PunchAllowance.gd")
const PHANTOM_HIT_WINDOW := 0.5
const VIEW_SIZE := Vector2(1920, 1080)
# Over the ropes while he rides, on the floor while he stands.
const AIR_Z := 3
const GROUND_Z := 0

#BREAK GAUGE (BossBreakGauge)
# Twelve clean reads from empty (eight until the tuning round of 2026-10-04) are a guaranteed Break: a parry or
# perfect dodge of his is a read, a hit
# costs one and a guard break two, and a landed punch is a quarter of one (charged, a half), so a 3-punch
# combo is one read. Nothing decays. BREAK_READ is BossBreakGauge's max_value of 100 over N, given as it
# is (BREAK_EPSILON). Nothing of his staggers him on a parry or comes back at him, so there is no strong
# parry or reflect here, and the gauge takes none (_add_break_gauge).
const BREAK_READS := 12
const BREAK_READ := 100.0 / BREAK_READS
const BREAK := {
	"parry_gain": BREAK_READ,
	"perfect_dodge_gain": BREAK_READ,
	"punch_gain": BREAK_READ / 4.0,
	"charged_punch_gain": BREAK_READ / 2.0,
	"hit_loss": BREAK_READ,
	"guard_break_loss": 2.0 * BREAK_READ,
	"unlock_delay": 3.0,
	"broken_time": 3.0,
}
# What fills it: a perfect dodge through his Wild Cards, one read a volley however many of its cards the
# dash goes through (JoshCardsWildCards.pay_read), and a parry or a perfect dodge of each landing of his
# Hand Slam, a read each: every landing is its own source (JoshHandSlamHit); a perfect dodge through a beam of
# his Gun Hands, a read each (JoshGunBeam); and a parry of the real him in his Portal Monte (JoshMonteFigure), not a
# strong parry, since his grab_parry_gain is 0. Every one of his attacks drains it.
const BREAK_EARNS: Array[StringName] = [&"josh_wild_card", &"josh_hand_slam", &"josh_gun_beam", &"josh_monte_strike"]

#UI (BossHealthBarUI builds it at runtime)
var hud_layer: CanvasLayer
var health_bar: Control
var gauge_bar: Control
var break_gauge: Node
# The boss bar and the Break bar under it fade while his hands or a slam's badge are over them (update_hud_fade).
const HUD_FADE_ALPHA := 0.3
const HUD_FADE_TIME := 0.25
var hud_fade: Tween
var hud_fade_to := 1.0

# Kept under a node that y-sorts at the top edge of the arena floor, so it is drawn under every
# character wherever it goes.
@export var shadow: Node2D
# Hazards sort under the player (FloorLayer) or over the ropes (SkyLayer).
@export var floor_layer: Node2D
@export var sky_layer: Node2D
@onready var air: Node2D = $Air
@onready var glider: Node2D = $Air/Glider
@onready var sprite: Sprite2D = $Air/Sprite2D
@onready var hurtbox: Area2D = $Air/Hurtbox
@onready var hurtbox_shape: CollisionShape2D = $Air/Hurtbox/CollisionShape2D
@onready var state_machine = $StateManager

#AUDIO
# His own theme. Same level as the rest of the ladder, so moving between fights does not jump.
const THEME := "res://Assets/Audio/Music/josh_theme.wav"
const THEME_DB := -7.0

@onready var music_player: AudioStreamPlayer = $MusicPlayer
@onready var hit_sfx_player: AudioStreamPlayer = $HitSfxPlayer
@onready var victory_sfx_player: AudioStreamPlayer = $VictorySfxPlayer
@onready var throw_sfx_player: AudioStreamPlayer = $ThrowSfxPlayer
@onready var land_sfx_player: AudioStreamPlayer = $LandSfxPlayer
@onready var recover_sfx_player: AudioStreamPlayer = $RecoverSfxPlayer
@onready var shuffle_sfx_player: AudioStreamPlayer = $ShuffleSfxPlayer
@onready var reveal_sfx_player: AudioStreamPlayer = $RevealSfxPlayer
@onready var card_sfx_player: AudioStreamPlayer = $CardSfxPlayer

var defeated := false
var hits_this_window := 0
var punches := PunchAllowance.new()
# One finisher daze per window; his recovery and his Break each clear it.
var daze_used := false

var fight_clock := 0.0
var last_contact_hit_time := -INF

var sprite_base_position: Vector2

# The player's sprite y-sorts this far over their feet (their body's centre is 42 px over the foot of their hurtbox,
# and every fight scene sets their sprite 13 texels, 39 px, under it), so everything drawn of him sorts on a point as
# far over his: a player whose feet are in front of his is drawn in front of him, where on his own feet he won every
# tie up to 3 px. His floor point, his hurtbox and every point measured off Air stay where they were.
const SORT_LIFT := 3.0
var sort_point: Node2D

# The floor point under him, where his shadow is, and how many px above it his feet are. His node sits
# on the floor point, and everything drawn is snapped to whole pixels.
var ground_position := Vector2.ZERO
var height := 0.0
var fly_velocity := Vector2.ZERO
# Which way he faces: the way he rides in the air, and toward the player on the ground (face_player).
var flying_left := false
# A finisher's shove still sliding his floor point, which a Break stops where it is.
var knock_tween: Tween

var shadow_sprite: Sprite2D
var glider_sprite: Sprite2D
var glider_clock := 0.0

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
	ground_position = global_position
	_lift_sort_point()
	_apply_art_layout()
	var player := get_tree().current_scene.get_node_or_null(FightOutro.PLAYER_PATH)
	if player:
		_add_break_gauge(player)
	_build_hud()
	place()

	# "Three Card Trick", written for this fight - see art_source/music/josh_theme.rb. One 16-bar
	# cycle cut to the beat, so LOOP_FORWARD runs it end to end with no seam.
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
	throw_sfx_player.stream = load("res://Assets/Audio/SFX/whirlwind_whoosh.ogg")
	land_sfx_player.stream = load("res://Assets/Audio/SFX/wrestler_collision.ogg")
	recover_sfx_player.stream = load("res://Assets/Audio/SFX/downed_stinger.ogg")
	shuffle_sfx_player.stream = load("res://Assets/Audio/SFX/whirlwind_whoosh.ogg")
	reveal_sfx_player.stream = load("res://Assets/Audio/SFX/laser_charge.ogg")
	card_sfx_player.stream = load("res://Assets/Audio/SFX/hit_impact.ogg")


func _add_break_gauge(player: Node) -> void:
	break_gauge = BossBreakGauge.new()
	break_gauge.name = "BreakGauge"
	break_gauge.boss = self
	break_gauge.player = player
	break_gauge.owns_attack = func(id: StringName) -> bool: return str(id).begins_with("josh_")
	break_gauge.earns_from = func(hit: RefCounted) -> bool: return BREAK_EARNS.has(hit.attack_id) and state_machine.pay_volley_read(hit)
	break_gauge.parry_gain = BREAK.parry_gain
	break_gauge.perfect_dodge_gain = BREAK.perfect_dodge_gain
	break_gauge.punch_gain = BREAK.punch_gain
	break_gauge.charged_punch_gain = BREAK.charged_punch_gain
	break_gauge.hit_loss = BREAK.hit_loss
	break_gauge.guard_break_loss = BREAK.guard_break_loss
	break_gauge.unlock_delay = BREAK.unlock_delay
	break_gauge.grab_parry_gain = 0.0
	break_gauge.reflect_gain = 0.0
	add_child(break_gauge)
	break_gauge.broke.connect(_on_break)


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
	_build_shadow()
	_build_glider()
	glider.scale = Vector2.ZERO
	glider.hide()

	(hurtbox_shape.shape as RectangleShape2D).size = JoshArtLayout.local_rect(JoshArtLayout.RECOVER_BODY_BOX).size
	_place_hurtbox()


# The box is traced off the recovery pose, so it mirrors with his frames.
func _place_hurtbox() -> void:
	hurtbox_shape.position = JoshArtLayout.local_rect(JoshArtLayout.RECOVER_BODY_BOX, sprite.flip_h).get_center()


func _build_shadow() -> void:
	if JoshArtLayout.USE_FINAL_SHADOW:
		var spec := JoshArtLayout.FINAL_SHADOW
		shadow_sprite = Sprite2D.new()
		shadow_sprite.texture = load(spec.texture)
		shadow_sprite.hframes = spec.hframes
		shadow_sprite.scale = Vector2.ONE * spec.scale
		shadow_sprite.offset = spec.frame_size / 2.0 - spec.pivot
		shadow_sprite.position = spec.offset
		shadow.add_child(shadow_sprite)
		return

	var shadow_shape := Polygon2D.new()
	shadow_shape.polygon = JoshArtLayout.ellipse(
		JoshArtLayout.PLACEHOLDER_SHADOW.radii, JoshArtLayout.PLACEHOLDER_SHADOW.points)
	shadow_shape.color = JoshArtLayout.PLACEHOLDER_SHADOW.color
	shadow.add_child(shadow_shape)
	shadow.modulate.a = JoshArtLayout.SHADOW_ALPHA


# Its own node behind his sprite: the deck hangs below his frame, so nothing sized to that frame may
# own it.
func _build_glider() -> void:
	if JoshArtLayout.USE_FINAL_GLIDER:
		var spec := JoshArtLayout.FINAL_GLIDER
		glider_sprite = Sprite2D.new()
		glider_sprite.texture = load(spec.texture)
		glider_sprite.hframes = spec.hframes
		glider_sprite.scale = Vector2.ONE * spec.scale
		glider_sprite.offset = spec.frame_size / 2.0 - spec.pivot
		glider.add_child(glider_sprite)
		_place_glider()
		return

	var board := Polygon2D.new()
	board.polygon = JoshArtLayout.glider_shape()
	board.color = JoshArtLayout.PLACEHOLDER_GLIDER.color
	glider.add_child(board)
	var rim := Line2D.new()
	rim.points = board.polygon
	rim.closed = true
	rim.width = JoshArtLayout.PLACEHOLDER_GLIDER.edge_width
	rim.default_color = JoshArtLayout.PLACEHOLDER_GLIDER.edge_color
	glider.add_child(rim)


# The deck sits under his soles and mirrors with him.
func _place_glider() -> void:
	if not glider_sprite:
		return
	var spec := JoshArtLayout.FINAL_GLIDER
	glider_sprite.flip_h = flying_left
	glider_sprite.position = Vector2(-spec.offset.x if flying_left else spec.offset.x, spec.offset.y)


#ANIMATION

# A non-looping animation holds its last frame when it ends, unless `next_anim` follows it.
func play_anim(anim_name: StringName, next_anim: StringName = &"") -> void:
	current_anim = anim_name
	anim = JoshArtLayout.anim(anim_name)
	anim_next = next_anim
	anim_step = 0
	anim_clock = 0.0
	anim_done = false
	var sheet: Texture2D = load(anim.sheet)
	var frame_size: Vector2 = anim.get("frame_size", JoshArtLayout.FRAME_SIZE)
	# Back to the first frame before the frame count changes, so the current one can't be out of range.
	sprite.frame = 0
	sprite.texture = sheet
	sprite.hframes = roundi(sheet.get_width() / frame_size.x)
	sprite.offset = JoshArtLayout.sheet_offset(frame_size)
	sprite.rotation_degrees = anim.get("turn", 0.0)
	_show_anim_frame()


func _process(delta: float) -> void:
	if glider_sprite and glider.visible:
		glider_clock += delta
		glider_sprite.frame = int(glider_clock / JoshArtLayout.FINAL_GLIDER.frame_time) % glider_sprite.hframes
		_place_glider()
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
	# The symmetry axis is the anchor's column, so mirroring keeps his feet in place.
	var mirrored: bool = anim.get("flips", false) and flying_left
	if sprite.flip_h != mirrored:
		sprite.flip_h = mirrored
		_place_hurtbox()


#FLIGHT

func feet_position() -> Vector2:
	return ground_position - Vector2(0, height)


# The uppercut shoves him back (PlayerFinisher). His floor point simply moves, clamped to the same
# bounds his own flight uses.
func knock_back(push: Vector2, time: float) -> void:
	var bounds := ground_bounds(height)
	var target := (ground_position + push).clamp(bounds.position, bounds.end)
	if knock_tween:
		knock_tween.kill()
	knock_tween = create_tween()
	knock_tween.tween_method(func(to: Vector2) -> void:
		ground_position = to
		place()
	, ground_position, target, time).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)


# Where his floor point can be for the whole of his juggle frames, twice his width, to be drawn inside the
# ropes, facing the way he does: x from .x to .y. His Break slides him in to it, and the last uppercut's
# shove stops at its edge.
func juggle_x_range() -> Vector2:
	var drawn := JoshArtLayout.JUGGLE_DRAWN
	var middle: float = JoshArtLayout.juggle().frame_size.x / 2.0
	var reach := Vector2(drawn.position.x - middle, drawn.end.x - middle) * JoshArtLayout.SCALE
	if sprite.flip_h:
		reach = Vector2(-reach.y, -reach.x)
	var ropes: Rect2 = state_machine.ROPES
	return Vector2(ropes.position.x - reach.x, ropes.end.x - reach.y)


# The juggle's last uppercut shoves him along his ground line (PlayerFinisher), no further than
# juggle_x_range(). One who is already past its edge stays where he is rather than being pulled back
# toward the player.
func juggle_knock_back(push: Vector2, time: float) -> void:
	var inside := juggle_x_range()
	var x := clampf(ground_position.x + push.x, minf(ground_position.x, inside.x), maxf(ground_position.x, inside.y))
	knock_back(Vector2(x - ground_position.x, 0.0), time)


# Air goes under a node SORT_LIFT over his floor point, which sorts with the player while Air draws with it.
func _lift_sort_point() -> void:
	sort_point = Node2D.new()
	sort_point.name = "SortPoint"
	sort_point.position = Vector2(0, -SORT_LIFT)
	add_child(sort_point)
	air.reparent(sort_point)
	y_sort_enabled = true


func place() -> void:
	global_position = ground_position.round()
	air.position = Vector2(0, SORT_LIFT - roundf(height))
	# The shadow never leaves the floor however high he rides: only which frame it draws changes.
	shadow.global_position = global_position
	var riding_height: float = state_machine.glider_height
	var lift := clampf(height / riding_height, 0.0, 1.0)
	if shadow_sprite:
		shadow_sprite.frame = clampi(ceili(lift * (shadow_sprite.hframes - 1)), 0, shadow_sprite.hframes - 1)
		return
	shadow.scale = Vector2.ONE * lerpf(1.0, JoshArtLayout.SHADOW_AIR_SCALE, lift)
	shadow.modulate.a = JoshArtLayout.SHADOW_ALPHA * lerpf(1.0, JoshArtLayout.SHADOW_AIR_ALPHA, lift)


# On the ground he turns to the player. Set before the pose that uses it, so the pose is drawn toward
# the player from its first frame.
func face_player() -> void:
	var player: Node2D = state_machine.get_player()
	if is_instance_valid(player):
		flying_left = player.global_position.x < global_position.x


# The floor points he can be over with his feet `at_height` px up: his shadow inside the ropes and his
# whole sprite on screen. Only for landing points and knock_back: a pass over the arena aims at an
# unclamped point off the side of the screen.
func ground_bounds(at_height: float) -> Rect2:
	var ropes: Rect2 = state_machine.ROPES
	var shadow_radii: Vector2 = JoshArtLayout.PLACEHOLDER_SHADOW.radii
	var body_box := JoshArtLayout.local_rect(JoshArtLayout.BODY_DRAWN)
	var top_left := Vector2(
		maxf(ropes.position.x + shadow_radii.x, -body_box.position.x),
		maxf(ropes.position.y + shadow_radii.y, at_height - body_box.position.y))
	var bottom_right := Vector2(
		minf(ropes.end.x - shadow_radii.x, VIEW_SIZE.x - body_box.end.x),
		minf(ropes.end.y - shadow_radii.y, VIEW_SIZE.y - body_box.end.y + at_height))
	return Rect2(top_left, bottom_right - top_left)


# Over the ropes while he rides, back on the floor when he lands.
func set_air_draw(up: bool) -> void:
	sprite.z_index = AIR_Z if up else GROUND_Z


func hide_glider() -> void:
	glider.scale = Vector2.ZERO
	glider.hide()


#EFFECTS

func shake_screen(strength: float, steps: int, step_time: float) -> void:
	ScreenView.shake(get_tree(), strength, steps, step_time)


# Shudders the drawn body in whole pixels; his hitboxes and shadow stay put.
func shake_sprite(strength: float, steps: int, step_time: float) -> void:
	var tween := sprite.create_tween()
	for i in steps:
		var offset := Vector2(randf_range(-strength, strength), randf_range(-strength, strength)).round()
		tween.tween_callback(func() -> void: sprite.position = sprite_base_position + offset)
		tween.tween_interval(step_time)
	tween.tween_callback(func() -> void: sprite.position = sprite_base_position)


#COMBAT

# Punches only reach him while he is down, recovering or Broken. The hurtbox keeps its facing groups
# whenever he can be seen (set_target_active), so the player faces him wherever he stands.
func set_hurtbox_active(active: bool) -> void:
	# Deferred: monitoring can't change inside a physics flush.
	hurtbox.set_deferred("monitoring", active)
	hurtbox.set_deferred("monitorable", active)


# Whether the player faces him and aims at him at all: off while he is gone from the screen
# (JoshCardsWildCards), so nothing turns the player toward the spot he left.
func set_target_active(on: bool) -> void:
	if on and not hurtbox.is_in_group("boss_target"):
		hurtbox.add_to_group("boss_target")
	elif not on and hurtbox.is_in_group("boss_target"):
		hurtbox.remove_from_group("boss_target")


func _on_hurtbox_entered(area: Area2D) -> void:
	if boss_health <= 0 or not area.is_in_group("player attack"):
		return

	# Same phantom-hit filter as Mason: a punch that connects as its hitbox switches on is reported
	# again when PlayerPunching switches the hitbox off, which would eat the hit cap.
	if not area.monitorable and fight_clock - last_contact_hit_time < PHANTOM_HIT_WINDOW:
		return
	if area.get_parent().combo.resolve_punch(self) > 0 and area.monitorable:
		last_contact_hit_time = fight_clock


func is_broken() -> bool:
	return state_machine.current_state == state_machine.states.get("Broken")


func is_juggled() -> bool:
	return state_machine.current_state == state_machine.states.get("Juggled")


# Down from a Break or a juggle, until he is back on his feet: the Break gauge waits for this.
func is_down() -> bool:
	return is_broken() or is_juggled()


# His two punish windows, both down on the ground: his recovery, and his Break.
func _in_window() -> bool:
	return state_machine.is_recovering() or is_broken()


# Punches only land while he is down in one of his windows.
func take_punch(amount: int) -> int:
	if not _in_window():
		return 0
	var allowed := punches.allow(amount, hits_this_window, MAX_HITS_PER_WINDOW)
	if allowed <= 0:
		return 0
	var dealt := _apply_damage(allowed)
	if dealt > 0:
		hits_this_window += 1
		punches.spend(dealt)
	return dealt


# A hit that would carry past his last health point is cut down to it.
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


# The player's finisher (PlayerFinisher). His windows can be dazed, once each.
func can_be_dazed() -> bool:
	return not defeated and not daze_used and _in_window() and boss_health > 0


# The three-bar mash and the juggle are the Break's payout alone; his recovery pays the single-bar
# finisher. Arithmetic, not taste: the juggle takes 40% of his health, so with it on every window the
# fight would be over in two.
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
	if not _in_window():
		return 0
	return _apply_damage(amount)


func get_max_health() -> int:
	return max_health


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


# A juggle that kills him ends with him still in the air: the outro's first line would otherwise open
# over him mid-fall.
func outro_line_delay(_player_won: bool) -> float:
	return JoshArtLayout.juggle().outro_delay if is_juggled() else 0.0


# Over his hat as he is drawn, so a Break taken mid-ride has its zoom and its stars on him as he drops,
# not on the floor under him. On the ground the two are the same point.
func get_daze_anchor() -> Vector2:
	return air.global_position + JoshArtLayout.mirrored(JoshArtLayout.DAZE_ANCHOR, sprite.flip_h)


func get_finisher_hurtbox() -> Area2D:
	return hurtbox


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


# Whoever won, nothing he has sent out may stay live.
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
		"rows": [{"key": &"josh", "max": max_health, "value": boss_health}],
		"plate": &"josh",
		"text": "JOSH",
	})
	hud_layer.add_child(health_bar)

	if break_gauge:
		gauge_bar = BreakGaugeUI.new()
		gauge_bar.gauge = break_gauge
		hud_layer.add_child(gauge_bar)
		gauge_bar.position = health_bar.break_gauge_anchor()


# The bars fade while anything in `rects` is over the boss bar block (JoshArtLayout.HUD_KEEP_OUT's first, with its
# clearance), and come back as it leaves.
func update_hud_fade(rects: Array[Rect2]) -> void:
	var block: Rect2 = JoshArtLayout.HUD_KEEP_OUT[0].grow(JoshArtLayout.HUD_CLEARANCE)
	var covered := rects.any(func(rect: Rect2) -> bool: return rect.intersects(block))
	_fade_hud(HUD_FADE_ALPHA if covered else 1.0)


func restore_hud() -> void:
	_fade_hud(1.0)


# Bound to the bar itself, so a pause or a finisher's freeze holds it with the fight. A fade already on its way to
# `alpha` is left to run, so asking for it every step still takes HUD_FADE_TIME. A bar already gone with the scene
# can't make a tween.
func _fade_hud(alpha: float) -> void:
	if not health_bar or not health_bar.is_inside_tree():
		return
	if hud_fade and hud_fade.is_valid() and is_equal_approx(hud_fade_to, alpha):
		return
	if hud_fade:
		hud_fade.kill()
	hud_fade_to = alpha
	if is_equal_approx(health_bar.modulate.a, alpha):
		return
	hud_fade = health_bar.create_tween().set_parallel()
	for bar: Control in [health_bar, gauge_bar]:
		if bar:
			hud_fade.tween_property(bar, "modulate:a", alpha, HUD_FADE_TIME)


func add_player_hype(amount: float) -> void:
	var player: Node = state_machine.get_player()
	var hype: Node = player.get_node_or_null("Hype") if player else null
	if hype:
		hype.add(amount)


# A word across the screen (a bitten fake's "FEINT!"), on his HUD layer, as Carter's: on his spot, or centred on
# `centre` (JoshMonteLayout.word_centre moves it off the marks).
func show_word(text: String, centre: Vector2 = JoshMonteLayout.WORD.centre) -> void:
	var spec: Dictionary = JoshMonteLayout.WORD
	var label := Label.new()
	label.text = text
	label.theme = load("res://Assets/UI/ui_theme.tres")
	label.add_theme_font_size_override("font_size", spec.font_size)
	label.add_theme_color_override("font_color", spec.color)
	label.add_theme_color_override("font_outline_color", Color(0, 0, 0))
	label.add_theme_constant_override("outline_size", spec.outline)
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.size = Vector2(1400, 160)
	label.pivot_offset = label.size / 2.0
	label.position = centre - label.size / 2.0
	label.scale = Vector2.ONE * spec.from_scale
	hud_layer.add_child(label)
	var show := label.create_tween()
	show.tween_property(label, "scale", Vector2.ONE * spec.to_scale, spec.grow_time).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	show.tween_interval(spec.time - spec.grow_time)
	show.tween_property(label, "modulate:a", 0.0, 0.3)
	show.tween_callback(label.queue_free)


func _hit_feedback() -> void:
	if not sprite:
		return

	sprite.modulate = Color(3, 3, 3)
	var flash_tween = create_tween()
	flash_tween.tween_property(sprite, "modulate", Color(1, 1, 1), 0.15)
	shake_sprite(5.0, 4, 0.025)

	HitStop.freeze(get_tree(), 0.06)
