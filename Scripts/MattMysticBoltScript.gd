extends Node2D

# One of Matt's Mystic Shots: an icy bolt that flies on a 22.5 degree lattice, comes back off the
# ropes `bounces` times (MattStateMachine.mystic_bounces) and bursts on the next contact.
#
# IT REPORTS ITS OWN HITS, as Josh's thrown cards do, because it needs the result: a hit bursts it, and
# a parry, a block or a dash lets it fly on through the player, whole (AttackCatalog's
# parry_pass_through). Its hitbox is on no layer and in no "enemy projectile" group, so nothing else
# ever resolves it. The latch keeps it off the player for the rest of the pass it was answered on,
# and PlayerDefense's per-source absorb is the backstop behind that.
#
# THE LATTICE IS WHAT KEEPS IT FAIR: a reflection only ever flips one component of a lattice heading,
# so every heading it will ever have is 22.5, 45 or 67.5 degrees off an axis - it never skims a rope,
# and its life is bounded by its bounces.

const HitInfo := preload("res://Scripts/HitInfo.gd")
const MattArtLayout := preload("res://Scripts/MattArtLayout.gd")

const SHOT_ID := &"matt_mystic_shot"
# Nothing should outlive its bounces; this is the floor under a bolt that somehow never reaches a rope.
const SAFETY_LIFE := 12.0
# Answered and flying on: the art flickers so the pass reads as survived.
const FLICKER_TIME := 0.2
const FLICKER_HZ := 30.0
const FLICKER_ALPHA := 0.35

@export var art: Node2D
@export var hitbox: Area2D
@export var hitbox_shape: CollisionShape2D

# Set before it enters the tree.
var heading := Vector2.RIGHT
var speed := 850.0
var bounces := 5
var hit_radius := 12.0
# ROPES pulled in by the hit circle's own radius: where the bolt's core turns.
var bounds := Rect2()
var player: Node2D
var body: Node2D

var reflections := 0
var life := 0.0
var latched := false
var flicker_left := 0.0
var spent := false
# Every reflection it made, for a test that has to see them: where, and the heading it left with.
var turns: Array = []
var fx_clock := 0.0
var sheet: Sprite2D
# The faint streak under it on the floor, which lives and dies with it.
var streak: Sprite2D


func _ready() -> void:
	(hitbox_shape.shape as CircleShape2D).radius = hit_radius
	_build()
	_face()


func _physics_process(delta: float) -> void:
	if spent:
		return
	life += delta
	fx_clock += delta
	global_position += heading * speed * delta
	if _off_the_ropes():
		return
	if life >= SAFETY_LIFE:
		fizzle()
		return
	_step_art(delta)
	_resolve_hits()


# A rope contact: the component that went past the rope is mirrored back inside it, and a corner that
# took both at once is still one bounce. The contact after the last bounce is the end of it.
func _off_the_ropes() -> bool:
	var at := global_position
	var rope := &""
	if at.x < bounds.position.x or at.x > bounds.end.x:
		rope = &"left" if at.x < bounds.position.x else &"right"
		var wall := bounds.position.x if at.x < bounds.position.x else bounds.end.x
		at.x = 2.0 * wall - at.x
		heading.x = -heading.x
	if at.y < bounds.position.y or at.y > bounds.end.y:
		var wall := bounds.position.y if at.y < bounds.position.y else bounds.end.y
		if rope == &"":
			rope = &"top" if at.y < bounds.position.y else &"bottom"
		at.y = 2.0 * wall - at.y
		heading.y = -heading.y
	if rope == &"":
		return false
	var contact := global_position.clamp(bounds.position, bounds.end)
	if reflections >= bounces:
		_spark(contact, rope, false)
		_free_now()
		return true
	reflections += 1
	global_position = at
	turns.append({"at": contact, "heading": heading})
	_face()
	_spark(contact, rope, true)
	if is_instance_valid(body):
		body.play_sfx(&"mystic_bounce", 1.0 + randf_range(-MattArtLayout.BOUNCE_PITCH_JITTER, MattArtLayout.BOUNCE_PITCH_JITTER))
	return false


# The latch: one answer per pass. Touching the player unlatched asks them; touching them latched does
# nothing; off them it lets go, and a touch on the dodge ghost alone is a near miss.
func _resolve_hits() -> void:
	if not is_instance_valid(player):
		return
	var touching := false
	var near := false
	for area in hitbox.get_overlapping_areas():
		if area == player.hurtBox:
			touching = true
		elif player.is_dodge_ghost(area):
			near = true
	if touching:
		if latched:
			return
		match player.receive_hit(_hit()):
			HitInfo.Result.HIT:
				_spark(global_position, &"", false)
				_free_now()
			HitInfo.Result.PARRIED, HitInfo.Result.BLOCKED, HitInfo.Result.DODGED:
				latched = true
				flicker_left = FLICKER_TIME
		return
	latched = false
	if near:
		player.receive_near_miss(_hit())


# Its origin is the player's own hurtbox centre, so any facing answers it: it comes back off the ropes
# from every side. No boss: a parry negates it and pays hype, but staggers nothing.
func _hit() -> RefCounted:
	var centre: Vector2 = player.hurtBox.get_node("CollisionShape2D").global_position
	return HitInfo.make(SHOT_ID, hitbox, centre, null)


# Out of time, or out of the Spent wait's patience: it goes where it is, with the long spark.
func fizzle() -> void:
	if spent:
		return
	_spark(global_position, &"", false)
	if is_instance_valid(body):
		body.play_sfx(&"mystic_fizzle")
	_free_now()


func _free_now() -> void:
	spent = true
	hitbox_shape.set_deferred("disabled", true)
	queue_free()


func _exit_tree() -> void:
	if is_instance_valid(streak):
		streak.queue_free()
	streak = null


#WHAT IS DRAWN

# The drawn sheet hangs straight off the bolt, beside its hitbox: that is where PlayerCombatFx looks
# for a parried projectile's art to flash.
func _build() -> void:
	if MattArtLayout.uses_final_fx(&"streak") and is_instance_valid(body) and body.floor_layer != null:
		var streak_spec := MattArtLayout.fx(&"streak")
		streak = Sprite2D.new()
		streak.texture = load(streak_spec.texture)
		streak.hframes = streak_spec.hframes
		streak.scale = Vector2.ONE * MattArtLayout.SCALE
		streak.modulate.a = streak_spec.alpha
		body.floor_layer.add_child(streak)
		streak.global_position = (global_position + Vector2(0, streak_spec.drop)).round()
	if MattArtLayout.uses_final_fx(&"bolt"):
		var spec := MattArtLayout.fx(&"bolt")
		sheet = Sprite2D.new()
		sheet.texture = load(spec.texture)
		sheet.hframes = spec.hframes
		sheet.scale = Vector2.ONE * MattArtLayout.SCALE
		add_child(sheet)
		return
	var spec := MattArtLayout.fx(&"bolt")
	var trail := Line2D.new()
	trail.points = PackedVector2Array([Vector2(-spec.trail_length, 0.0), Vector2.ZERO])
	trail.width = spec.trail_width
	trail.width_curve = Curve.new()
	trail.width_curve.add_point(Vector2(0.0, 0.25))
	trail.width_curve.add_point(Vector2(1.0, 1.0))
	trail.default_color = spec.trail_color
	art.add_child(trail)
	var head := Polygon2D.new()
	var half: float = spec.head_width / 2.0
	head.polygon = PackedVector2Array([Vector2(spec.head_length * 0.7, 0.0), Vector2(-spec.head_length * 0.3, -half),
		Vector2(-spec.head_length * 0.15, 0.0), Vector2(-spec.head_length * 0.3, half)])
	head.color = spec.head_color
	art.add_child(head)
	var core := Polygon2D.new()
	core.polygon = MattArtLayout.circle(spec.core_radius, 10)
	core.color = spec.core_color
	art.add_child(core)


# The stand-in turns with it; the drawn one - and the streak under it - picks its heading's frames and
# flips instead, its offset turned with the flips so the core stays on the bolt.
func _face() -> void:
	var pick: Array = MattArtLayout.art_frame(heading, MattArtLayout.BOLT_ART_ANGLES)
	if is_instance_valid(streak):
		streak.flip_h = pick[1]
		streak.flip_v = pick[2]
		streak.offset = MattArtLayout.flipped_offset(MattArtLayout.fx(&"bolt").offsets[pick[0]], pick[1], pick[2])
		streak.set_meta(&"heading_index", pick[0])
	if sheet == null:
		art.rotation = heading.angle()
		return
	var spec := MattArtLayout.fx(&"bolt")
	sheet.flip_h = pick[1]
	sheet.flip_v = pick[2]
	sheet.offset = MattArtLayout.flipped_offset(spec.offsets[pick[0]], pick[1], pick[2])
	sheet.set_meta(&"heading_index", pick[0])


func _step_art(delta: float) -> void:
	if is_instance_valid(streak):
		var streak_spec := MattArtLayout.fx(&"streak")
		var pair: int = streak_spec.frames_per_heading
		streak.frame = int(streak.get_meta(&"heading_index")) * pair + int(fx_clock / streak_spec.frame_time) % pair
		streak.global_position = (global_position + Vector2(0, streak_spec.drop)).round()
	if sheet != null:
		var spec := MattArtLayout.fx(&"bolt")
		var per: int = spec.frames_per_heading
		sheet.frame = int(sheet.get_meta(&"heading_index")) * per + int(fx_clock / spec.frame_time) % per
	if flicker_left > 0.0:
		flicker_left -= delta
		var dim := int(flicker_left * FLICKER_HZ * 2.0) % 2 == 1
		modulate.a = FLICKER_ALPHA if dim and flicker_left > 0.0 else 1.0


# Left on the layer the bolt flies in, so it plays out after the bolt is gone. `rope` is the one it met -
# the side one if it met two at once - or none, for a burst in the air.
func _spark(at: Vector2, rope: StringName, bounce: bool) -> void:
	var parent := get_parent()
	if parent == null:
		return
	var spec := MattArtLayout.fx(&"spark")
	if MattArtLayout.uses_final_fx(&"spark"):
		var spark := Sprite2D.new()
		spark.texture = load(spec.texture)
		spark.hframes = spec.hframes
		spark.scale = Vector2.ONE * MattArtLayout.SCALE
		spark.flip_h = rope == &"right"
		spark.flip_v = rope == &"bottom"
		var first: int = spec.side_first if rope == &"left" or rope == &"right" else 0
		var count: int = spec.bounce_frames if bounce else spec.fizzle_frames
		spark.frame = first
		parent.add_child(spark)
		spark.global_position = at.round()
		var play := spark.create_tween()
		for i in range(1, count):
			play.tween_interval(spec.frame_time)
			play.tween_callback(spark.set_frame.bind(first + i))
		play.tween_interval(spec.frame_time)
		play.tween_callback(spark.queue_free)
		return
	var burst := Polygon2D.new()
	burst.polygon = MattArtLayout.star(spec.points, spec.radius, spec.inner_ratio)
	burst.color = spec.color
	burst.scale = Vector2.ONE * spec.from_scale
	parent.add_child(burst)
	burst.global_position = at.round()
	var time: float = spec.bounce_time if bounce else spec.fizzle_time
	var play := burst.create_tween().set_parallel()
	play.tween_property(burst, "scale", Vector2.ONE * spec.to_scale, time)
	play.tween_property(burst, "modulate:a", 0.0, time)
	play.chain().tween_callback(burst.queue_free)
