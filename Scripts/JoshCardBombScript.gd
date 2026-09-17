extends Node2D

# One of the card bombs Josh drops behind him while he rides. It flutters down harmless, lands, lies
# there ticking, then goes off in a small blast the player can block from any facing.
# Its timing runs on _physics_process accumulators, so a finisher's freeze holds it.
# It is never dropped over the third that is warning or slamming: that rule, kept by the state that
# drops it, is what makes a falling card and a floor full of bombs survivable together.

const JoshArtLayout := preload("res://Scripts/JoshArtLayout.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")

enum Phase { FALL, LAND, ARM, BOOM }

const FALL_TIME := 0.35
const BLAST_SHAKE := 5.0
const BLAST_SHAKE_STEPS := 3
const BLAST_SHAKE_STEP_TIME := 0.03
# The placeholder's blast, which has no sheet of its own to time.
const PLACEHOLDER_BOOM_TIME := 0.18
# A bomb in the air is drawn over the ropes; a landed one lies on the floor under the player.
const FALLING_Z := 4
const FLOOR_Z := 0

@export var shadow: Node2D
@export var card: Node2D
@export var hitbox: Area2D
@export var hitbox_shape: CollisionShape2D
@export var blast_sfx: AudioStreamPlayer

# Set by the state that drops it, before it enters the tree.
var fuse := 1.1
var blast_radius := 39.0
# Where the card starts, relative to its floor point: his hand, as the drop frame draws it.
var fall_offset := Vector2(0, -190)

var phase := Phase.FALL
var clock := 0.0
var pulse := 0.0
var boom_step := -1

var card_sprite: Sprite2D
var card_face: Polygon2D
var shadow_shape: Polygon2D


func _ready() -> void:
	hitbox.set_meta(HitInfo.META_ATTACK, &"josh_card_bomb")
	(hitbox_shape.shape as CircleShape2D).radius = blast_radius
	if _final():
		var spec := JoshArtLayout.FINAL_BOMB
		hitbox_shape.position = Vector2(0, -spec.blast_rise_texels * spec.blast_scale)
	_build()
	card.z_index = FALLING_Z
	_place(0.0)


func _physics_process(delta: float) -> void:
	clock += delta
	match phase:
		Phase.FALL:
			_run_fall()
		Phase.LAND:
			_run_land()
		Phase.ARM:
			_run_arm(delta)
		Phase.BOOM:
			_run_boom()


func _run_fall() -> void:
	var along := clampf(clock / FALL_TIME, 0.0, 1.0)
	_place(along)
	if card_sprite:
		var spec := JoshArtLayout.FINAL_BOMB
		var frames: Array = spec.fall_frames
		card_sprite.frame = frames[int(clock / spec.fall_frame_time) % frames.size()]
	else:
		card.rotation = lerpf(-0.9, 0.0, along) * (1.0 - along)
	if along < 1.0:
		return
	clock = 0.0
	card.rotation = 0.0
	shadow.hide()
	if card_sprite:
		card_sprite.frame = JoshArtLayout.FINAL_BOMB.land_frame
		phase = Phase.LAND
	else:
		card_face.color = JoshArtLayout.PLACEHOLDER_BOMB.armed_color
		phase = Phase.ARM
		pulse = 0.0
	card.z_index = FLOOR_Z


func _run_land() -> void:
	if clock >= JoshArtLayout.FINAL_BOMB.land_time:
		phase = Phase.ARM
		clock = 0.0
		pulse = 0.0


# The final sheet ramps its own red glow; the placeholder blinks, tightening as the fuse runs out.
func _run_arm(delta: float) -> void:
	if card_sprite:
		var spec := JoshArtLayout.FINAL_BOMB
		var frames: Array = spec.tick_frames
		card_sprite.frame = frames[int(clock / spec.tick_frame_time) % frames.size()]
	else:
		var left := clampf(1.0 - clock / fuse, 0.0, 1.0)
		pulse += delta / lerpf(JoshArtLayout.BOMB_PULSE_LAST, JoshArtLayout.BOMB_PULSE_FIRST, left)
		card.modulate.a = 1.0 if int(pulse) % 2 == 0 else JoshArtLayout.BOMB_DIM_ALPHA
	if clock >= fuse:
		_blast()


func _blast() -> void:
	phase = Phase.BOOM
	clock = 0.0
	boom_step = -1
	card.modulate.a = 1.0
	hitbox_shape.set_deferred("disabled", false)
	if blast_sfx:
		blast_sfx.play()
	ScreenView.shake(get_tree(), BLAST_SHAKE, BLAST_SHAKE_STEPS, BLAST_SHAKE_STEP_TIME)
	if card_sprite:
		# The explosion is drawn bigger than the card that carried it; the pivot holds it in place.
		card_sprite.scale = Vector2.ONE * JoshArtLayout.FINAL_BOMB.blast_scale
		return

	card.hide()
	var spec := JoshArtLayout.PLACEHOLDER_BOMB_BLAST
	var burst := Polygon2D.new()
	burst.polygon = JoshArtLayout.star(spec.points, blast_radius, spec.inner_ratio)
	burst.color = spec.color
	burst.scale = Vector2.ONE * spec.from_scale
	add_child(burst)
	var grow := burst.create_tween()
	grow.tween_property(burst, "scale", Vector2.ONE * spec.to_scale, PLACEHOLDER_BOOM_TIME)
	grow.parallel().tween_property(burst, "modulate:a", 0.0, PLACEHOLDER_BOOM_TIME)


# The blast only hurts while the fireball is drawn, which is the first frames of the boom.
func _run_boom() -> void:
	if not card_sprite:
		if clock >= PLACEHOLDER_BOOM_TIME:
			queue_free()
		return

	var spec := JoshArtLayout.FINAL_BOMB
	var frames: Array = spec.boom_frames
	var times: Array = spec.boom_times
	var end := 0.0
	var step := frames.size() - 1
	for i in frames.size():
		end += times[i]
		if clock < end:
			step = i
			break
	if step != boom_step:
		boom_step = step
		card_sprite.frame = frames[step]
		if step >= spec.blast_damage_frames:
			hitbox_shape.set_deferred("disabled", true)
	if clock >= end:
		queue_free()


func _place(fall_along: float) -> void:
	var eased := 1.0 - fall_along * fall_along
	card.position = (fall_offset * eased).round()
	shadow_shape.scale = Vector2.ONE * lerpf(0.45, 1.0, fall_along)
	shadow.modulate.a = JoshArtLayout.BOMB_SHADOW_ALPHA * fall_along


func _final() -> bool:
	return JoshArtLayout.USE_FINAL_BOMB


func _build() -> void:
	shadow_shape = Polygon2D.new()
	var width: float = JoshArtLayout.PLACEHOLDER_BOMB.size.x
	shadow_shape.polygon = JoshArtLayout.ellipse(Vector2(width * 0.6, width * 0.22), 16)
	shadow_shape.color = Color(0, 0, 0)
	shadow.add_child(shadow_shape)

	if _final():
		var spec := JoshArtLayout.FINAL_BOMB
		card_sprite = Sprite2D.new()
		card_sprite.texture = load(spec.texture)
		card_sprite.hframes = spec.hframes
		card_sprite.scale = Vector2.ONE * spec.scale
		card_sprite.offset = spec.frame_size / 2.0 - spec.pivot
		card.add_child(card_sprite)
		return

	var placeholder := JoshArtLayout.PLACEHOLDER_BOMB
	card_face = Polygon2D.new()
	card_face.polygon = JoshArtLayout.centred_rect(placeholder.size)
	card_face.color = placeholder.color
	card.add_child(card_face)

	var rim := Line2D.new()
	rim.points = card_face.polygon
	rim.closed = true
	rim.width = placeholder.edge_width
	rim.default_color = placeholder.edge_color
	card.add_child(rim)
