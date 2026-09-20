extends CharacterBody2D

# The sparring dummy in the controls room. It satisfies every contract a boss does - the punch, the
# finisher's daze and its juggle, the parry stagger - so that what the player practises on it is the
# real system rather than a mock-up, and then it breaks the one rule a boss has: it has no health.
# take_punch() always reports the full damage back, so every combo charges and every charged punch
# can daze it, and get_health_ratio() never leaves 1.0, so nothing can ever kill it.
# It hits back only while it is sparring (TrainingRoomScript's mode post), on one loop of red, red,
# yellow: the padded arm to parry or block, then the torso lunge to dash through.
# It is bolted to the floor. Nothing ever moves its body - the lunge and every knockback move the
# sprite alone - so the player can always back out of range and nothing can shove them into a corner.

const Layout := preload("res://Scripts/TrainingDummyArtLayout.gd")
const AttackCatalog := preload("res://Scripts/AttackCatalog.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")
const FightOutro := preload("res://Scripts/FightOutro.gd")
const HitStop := preload("res://Scripts/HitStop.gd")

# What the finisher takes its share of damage from. Nothing spends it; it is only here so the
# uppercut and each juggle hit are worth what they are worth in a fight.
const MAX_HEALTH := 20

#PACING
# It only winds up while the player is this close: walking away is the safe corner, and a player
# feeling out the movement is never ambushed from across the room.
const ENGAGE_RANGE := 360.0
const ATTACK_GAP := 1.2
# Red, red, yellow, repeating.
const PATTERN: Array[StringName] = [&"dummy_swing", &"dummy_swing", &"dummy_lunge"]
const TIMINGS := {
	&"dummy_swing": {tell = 0.9, strike = 0.18, recover = 0.7},
	&"dummy_lunge": {tell = 0.8, strike = 0.25, recover = 0.9},
}

# A punch that makes contact the moment its hitbox switches on is reported again, as a phantom, when
# PlayerPunching switches the hitbox off. Game time, so hit-stop can't stretch the gap.
const PHANTOM_HIT_WINDOW := 0.5

enum Phase { READY, WINDUP, STRIKE, RECOVER, STAGGERED, DOWN }

@onready var sprite: Sprite2D = $Sprite2D
@onready var body_shape: CollisionShape2D = $CollisionShape2D
@onready var hurtbox: Area2D = $Hurtbox
@onready var hurtbox_shape: CollisionShape2D = $Hurtbox/CollisionShape2D
@onready var swing_hitbox: Area2D = $SwingHitbox
@onready var swing_shape: CollisionShape2D = $SwingHitbox/CollisionShape2D
@onready var hit_sfx_player: AudioStreamPlayer = $HitSfxPlayer
@onready var swing_sfx_player: AudioStreamPlayer = $SwingSfxPlayer

# Set by the room.
var player: CharacterBody2D

var sparring := false
var phase := Phase.READY
var phase_time := 0.0
var phase_length := 0.0
var attack_index := 0
var attack_id := &"dummy_swing"
# Set once a strike has been answered, so a hitbox live for eleven physics frames only resolves once.
var strike_spent := false
var lift := 0.0

var clock := 0.0
var last_contact_hit_time := -INF

var sprite_base_position: Vector2
var rest_offset: Vector2
# The stand-in's pieces while USE_FINAL_DUMMY is off; null once the sheet lands.
var placeholder: Node2D
var placeholder_figure: Node2D
var placeholder_arm: Node2D

var current_anim := &""
var anim := {}
var anim_next := &""
var anim_step := 0
var anim_clock := 0.0
var anim_done := false


func _ready() -> void:
	add_to_group(FightOutro.BOSS_GROUP)
	hurtbox.area_entered.connect(_on_hurtbox_entered)

	rest_offset = Layout.SPRITE_OFFSET - Layout.SORT_POINT
	sprite.position = Layout.SORT_POINT
	sprite.offset = rest_offset
	if Layout.USE_FINAL_DUMMY:
		sprite.texture = load(Layout.SHEET)
		sprite.hframes = Layout.SHEET_FRAMES
	else:
		_build_placeholder()
	sprite_base_position = sprite.position

	(body_shape.shape as RectangleShape2D).size = Layout.BODY_BOX.size
	body_shape.position = Layout.frame_texel(Layout.BODY_BOX.get_center())
	(hurtbox_shape.shape as RectangleShape2D).size = Layout.HURT_BOX.size
	hurtbox_shape.position = Layout.frame_texel(Layout.HURT_BOX.get_center())

	hit_sfx_player.stream = load("res://Assets/Audio/SFX/hit_impact.ogg")
	swing_sfx_player.stream = load("res://Assets/Audio/SFX/whirlwind_whoosh.ogg")

	_play(&"idle")
	_enter_phase(Phase.READY, ATTACK_GAP)


func _physics_process(delta: float) -> void:
	clock += delta
	phase_time += delta
	if is_instance_valid(player) and phase != Phase.DOWN and phase != Phase.STRIKE:
		_face_player()
	match phase:
		Phase.READY:
			if phase_time >= phase_length and _can_start_attack():
				_start_attack()
		Phase.WINDUP:
			if phase_time >= phase_length:
				_start_strike()
		Phase.STRIKE:
			_resolve_hits()
			if phase_time >= phase_length:
				_end_strike()
		Phase.RECOVER, Phase.STAGGERED:
			if phase_time >= phase_length:
				_play(&"idle")
				_enter_phase(Phase.READY, ATTACK_GAP)
		Phase.DOWN:
			pass


func _process(delta: float) -> void:
	_advance_anim(delta)
	# Every path that shoves the sprite writes its offset - the lunge here, the finisher's hop, its
	# knockback - so mirroring the offset is what makes all of them move the stand-in too.
	if placeholder:
		placeholder.position = sprite.offset - Layout.SPRITE_OFFSET


#THE ATTACK LOOP

# Walked into, the mode post flips this. Off, anything already wound up is dropped on the spot.
func set_sparring(on: bool) -> void:
	if sparring == on:
		return
	sparring = on
	if on:
		return
	ParryTell.clear(self)
	_disable_hitbox()
	if phase == Phase.WINDUP or phase == Phase.STRIKE:
		_play(&"idle")
		_enter_phase(Phase.READY, ATTACK_GAP)


func is_sparring() -> bool:
	return sparring


func _can_start_attack() -> bool:
	if not sparring or not is_instance_valid(player):
		return false
	if player.fight_over or player.is_finishing or player.is_talking:
		return false
	return global_position.distance_to(player.global_position) <= ENGAGE_RANGE


func _start_attack() -> void:
	attack_id = PATTERN[attack_index % PATTERN.size()]
	attack_index += 1
	var timing: Dictionary = TIMINGS[attack_id]
	_play(&"windup_red" if attack_id == &"dummy_swing" else &"windup_yellow")
	ParryTell.telegraph(self, attack_id, timing.tell, _tell_anchor)
	_enter_phase(Phase.WINDUP, timing.tell)


func _start_strike() -> void:
	ParryTell.clear(self)
	strike_spent = false
	var box: Rect2 = Layout.SWING_BOX if attack_id == &"dummy_swing" else Layout.LUNGE_BOX
	var aim := _aim()
	(swing_shape.shape as RectangleShape2D).size = box.size
	swing_hitbox.position = aim * box.get_center().x
	swing_hitbox.monitoring = true
	swing_hitbox.monitorable = true
	if attack_id == &"dummy_swing":
		_play(&"swing")
	else:
		_play(&"lunge")
		# Only the drawing leans; the body stays bolted down, so a lunge never shoves the player.
		sprite.offset = rest_offset + aim * Layout.LUNGE_PUSH
	swing_sfx_player.play()
	_enter_phase(Phase.STRIKE, TIMINGS[attack_id].strike)


func _end_strike() -> void:
	_disable_hitbox()
	sprite.offset = rest_offset
	_play(&"idle")
	_enter_phase(Phase.RECOVER, TIMINGS[attack_id].recover)


func _enter_phase(next: int, length: float) -> void:
	phase = next
	phase_time = 0.0
	phase_length = length


func _disable_hitbox() -> void:
	swing_hitbox.set_deferred("monitoring", false)
	swing_hitbox.set_deferred("monitorable", false)


# The near-miss branch is mandatory: without it the swing would silently eat perfect dodges.
func _resolve_hits() -> void:
	if strike_spent or not is_instance_valid(player):
		return
	var near_miss := false
	for area in swing_hitbox.get_overlapping_areas():
		if area == player.hurtBox:
			strike_spent = player.receive_hit(_hit()) != HitInfo.Result.IGNORED
			return
		if player.is_dodge_ghost(area):
			near_miss = true
	# Only where the player isn't: a swing passing the spot a dash left is a perfect dodge.
	if near_miss:
		player.receive_near_miss(_hit())


func _hit() -> RefCounted:
	return HitInfo.make(attack_id, swing_hitbox, swing_hitbox.global_position, self)


# A unit vector toward the player in the dummy's own texels, so the swing reaches whichever side
# they are standing on.
func _aim() -> Vector2:
	if not is_instance_valid(player):
		return Vector2.RIGHT
	var to_player := player.global_position - global_position
	return to_player.normalized() if to_player != Vector2.ZERO else Vector2.RIGHT


func _face_player() -> void:
	_set_flipped(player.global_position.x < global_position.x)


func _tell_anchor() -> Vector2:
	return global_position + Layout.TELL_ANCHOR_OFFSET


#THE BOSS CONTRACT (PlayerCombo, PlayerFinisher, PlayerDefense)

func _on_hurtbox_entered(area: Area2D) -> void:
	if not area.is_in_group("player attack"):
		return
	# A punch reported again as a phantom when the hitbox switches off ~0.4 s later; a genuine next
	# punch only reports from a switched-off hitbox two full swings after the contact.
	if not area.monitorable and clock - last_contact_hit_time < PHANTOM_HIT_WINDOW:
		return
	if area.get_parent().combo.resolve_punch(self) > 0 and area.monitorable:
		last_contact_hit_time = clock


# Always the full amount: nothing here has health, so every combo charges and the third punch is
# always the charged one that can daze it.
func take_punch(amount: int) -> int:
	_take_hit_feedback()
	if phase == Phase.READY or phase == Phase.RECOVER:
		_play(&"recoil", &"idle")
	return amount


func get_health_ratio() -> float:
	return 1.0


func get_max_health() -> int:
	return MAX_HEALTH


# Any punch that reaches it, unless the finisher already has it. Practising the mash is half the
# reason the room exists, so nothing else gates the daze.
func can_be_dazed() -> bool:
	return phase != Phase.DOWN


func enter_daze() -> void:
	ParryTell.clear(self)
	_disable_hitbox()
	sprite.offset = rest_offset
	_play(&"daze")
	_enter_phase(Phase.DOWN, 0.0)


func exit_daze(finisher_landed: bool) -> void:
	if finisher_landed:
		return
	# A whiffed uppercut: it is on its feet again with nothing owed.
	_play(&"idle")
	_enter_phase(Phase.READY, ATTACK_GAP)


func end_recovery(stagger_time: float) -> bool:
	# Crashed from a juggle it stays flat where it landed, and rights itself as the stagger runs out.
	if current_anim != &"crash":
		_play(&"stagger")
	_enter_phase(Phase.STAGGERED, stagger_time)
	return true


func take_finisher(amount: int) -> int:
	_take_hit_feedback()
	return amount


func get_daze_anchor() -> Vector2:
	return global_position + Layout.DAZE_ANCHOR_OFFSET


func get_finisher_hurtbox() -> Area2D:
	return hurtbox


# Bolted to the floor: the uppercut cannot send it anywhere. Having the method at all is what keeps
# PlayerFinisher from sliding the sprite instead, which would fight the juggle's own lift.
func knock_back(_push: Vector2, _time: float) -> void:
	pass


# Called by FightOutro if the player ever loses. They can't in here (TrainingRoomScript floors their
# health), but the group's contract asks for it.
func on_player_defeated() -> void:
	pass


#THE JUGGLE (PlayerFinisher's tiered mash, which only a juggleable boss gets)

func can_be_juggled() -> bool:
	return true


func begin_juggle() -> void:
	_enter_phase(Phase.DOWN, 0.0)


func juggle_lift(px: float) -> void:
	lift = px
	sprite.offset = rest_offset - Vector2(0, px / Layout.SCALE)


func juggle_pose(pose: StringName, _crater := false) -> void:
	_play(pose)


func juggle_headroom() -> float:
	return Layout.JUGGLE_HEADROOM


func take_juggle_hit(amount: int, pitch: float) -> int:
	_take_hit_feedback(pitch)
	return amount


func get_juggle_point() -> Vector2:
	return global_position + Layout.JUGGLE_POINT_OFFSET * Layout.SCALE - Vector2(0, lift)


#THE PARRY STAGGER (PlayerDefense)

# A parried arm is left hanging out: the punish window the whole red-tell read is for.
func can_parry_stagger(hit: RefCounted) -> bool:
	return hit.attack_id == &"dummy_swing" and phase != Phase.DOWN


func parry_stagger(duration: float) -> void:
	if phase == Phase.DOWN:
		return
	ParryTell.clear(self)
	_disable_hitbox()
	sprite.offset = rest_offset
	_play(&"stagger")
	_enter_phase(Phase.STAGGERED, duration)


#FEEDBACK

func _take_hit_feedback(pitch := 1.0) -> void:
	sprite.modulate = Color(3, 3, 3)
	var flash := create_tween()
	flash.tween_property(sprite, "modulate", Color(1, 1, 1), 0.15)

	var shake := create_tween()
	for i in 4:
		var offset := Vector2(randf_range(-5, 5), randf_range(-5, 5))
		shake.tween_property(sprite, "position", sprite_base_position + offset, 0.025)
	shake.tween_property(sprite, "position", sprite_base_position, 0.025)

	hit_sfx_player.pitch_scale = pitch
	hit_sfx_player.play()
	HitStop.freeze(get_tree(), 0.06)


#ANIMATION

# A non-looping animation holds its last frame when it ends, unless `next_anim` follows it.
func _play(anim_name: StringName, next_anim := &"") -> void:
	current_anim = anim_name
	anim = Layout.anim(anim_name)
	anim_next = next_anim
	anim_step = 0
	anim_clock = 0.0
	anim_done = false
	_show_frame(anim.frames[0])


func _advance_anim(delta: float) -> void:
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
				_play(anim_next)
			return
		_show_frame(anim.frames[anim_step])


func _frame_time() -> float:
	var times: Array = anim.times
	return times[mini(anim_step, times.size() - 1)]


func _show_frame(index: int) -> void:
	if sprite.texture:
		sprite.frame = index
	if placeholder:
		_pose_placeholder(Layout.PLACEHOLDER_POSES[index])


func _set_flipped(flipped: bool) -> void:
	sprite.flip_h = flipped
	if placeholder:
		placeholder.scale.x = -1.0 if flipped else 1.0


#THE STAND-IN

func _build_placeholder() -> void:
	var parts: Dictionary = Layout.PLACEHOLDER_PARTS
	var colours: Dictionary = Layout.PLACEHOLDER_COLOURS
	placeholder = Node2D.new()
	placeholder.name = "Placeholder"
	sprite.add_child(placeholder)

	_add_piece(placeholder, parts.base, colours.base, Vector2.ZERO)
	_add_piece(placeholder, parts.base_foot, colours.base_rim, Vector2.ZERO)

	placeholder_figure = Node2D.new()
	placeholder_figure.name = "Figure"
	placeholder.add_child(placeholder_figure)
	var pivot: Vector2 = Layout.PLACEHOLDER_PIVOT
	_add_piece(placeholder_figure, parts.post, colours.post, pivot)
	_add_piece(placeholder_figure, parts.torso, colours.torso, pivot)
	_add_piece(placeholder_figure, parts.torso_band, colours.torso_band, pivot)
	_add_piece(placeholder_figure, parts.face, colours.face, pivot)
	_add_piece(placeholder_figure, parts.face_lit, colours.face_lit, pivot)

	placeholder_arm = Node2D.new()
	placeholder_arm.name = "Arm"
	placeholder_arm.position = Layout.PLACEHOLDER_SHOULDER - pivot
	placeholder_figure.add_child(placeholder_arm)
	var shoulder: Vector2 = Layout.PLACEHOLDER_SHOULDER
	_add_piece(placeholder_arm, parts.arm, colours.arm, shoulder)
	_add_piece(placeholder_arm, parts.arm_pad, colours.arm_pad, shoulder)


# `box` is in texels from the dummy's origin; `from` is where the parent node sits in those texels.
func _add_piece(parent: Node2D, box: Rect2, colour: Color, from: Vector2) -> void:
	var piece := Polygon2D.new()
	piece.polygon = Layout.rect_polygon(Rect2(box.position - from, box.size))
	piece.color = colour
	parent.add_child(piece)


func _pose_placeholder(pose: Dictionary) -> void:
	placeholder_figure.position = Layout.PLACEHOLDER_PIVOT + Vector2(pose.lean, 0.0)
	placeholder_figure.rotation_degrees = pose.tip
	placeholder_arm.rotation_degrees = pose.arm
