extends Node2D

# One of Captain Burak's pistol shots: a ball flying straight from his muzzle at the point his aim
# latched onto, and on past it.
#
# IT REPORTS ITS OWN HITS, as Matt's bolts do, because it needs the result: a parried ball breaks up, a
# blocked one bursts on the guard, one that lands is spent, and nothing else stops it. Its hitbox is on
# no layer and in no "enemy projectile" group, so nothing else ever resolves it.
# The ball itself is the hit's source, so each shot is its own read: PlayerDefense keeps what it absorbs
# per source. burak_shot lands inside the i-frames, so a hit from the first shot never swallows the
# second, or its parry.

# PARRIED, BLOCKED or HIT, once, as it goes.
signal answered(result: int)

const HitInfo := preload("res://Scripts/HitInfo.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")
const Layout := preload("res://Scripts/BurakBossArtLayout.gd")

const SHOT_ID := &"burak_shot"
# The ropes grown by this much are off the screen, so a ball that missed goes once it is out of sight.
const OUT_OF_PLAY_MARGIN := 160.0
# A shot from close up is slowed to its minimum flight and can still be crossing the ring at this age.
const MAX_LIFE := 3.0

@export var hitbox: Area2D
@export var hitbox_shape: CollisionShape2D
# A shot that is no read at all (his warning shot, the volley's shots at the kegs): no hit, no glow, and
# it goes at its target rather than flying on.
@export var harmless := false

# Set before it enters the tree, aim() last: it reads these, and _ready draws the heading it sets.
var max_speed := 750.0
var min_flight := 0.40
var hit_radius := 12.0
# The fight's ROPES.
var ropes := Rect2()
var player: Node2D
var body: Node2D

var heading := Vector2.RIGHT
var speed := 0.0
var target := Vector2.ZERO
var life := 0.0
var spent := false
var heading_index := 0
var sheet: Sprite2D


# Never arriving in under min_flight, so a shot from close up still leaves the parry something to read.
func aim(from: Vector2, to: Vector2) -> void:
	target = to
	heading = from.direction_to(to)
	speed = minf(max_speed, from.distance_to(to) / min_flight)


func _ready() -> void:
	(hitbox_shape.shape as CircleShape2D).radius = hit_radius
	_build()
	if not harmless:
		ParryTell.glow(self, SHOT_ID)


func _physics_process(delta: float) -> void:
	if spent:
		return
	life += delta
	global_position += heading * speed * delta
	if harmless:
		# Half a pixel short is there: its summed steps fall a hair short of the target in floating point.
		if heading.dot(target - global_position) < 0.5:
			global_position = target
			_free_now()
			return
	elif life >= MAX_LIFE or not ropes.grow(OUT_OF_PLAY_MARGIN).has_point(global_position):
		_free_now()
		return
	_step_art()
	if not harmless:
		_resolve_hits()


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
		var result: int = player.receive_hit(_hit())
		match result:
			HitInfo.Result.PARRIED:
				clash_at(get_parent(), global_position)
				_stop(result)
			HitInfo.Result.BLOCKED, HitInfo.Result.HIT:
				_stop(result)
		return
	# Only where the player isn't: a ball passing the spot a dash left is a perfect dodge.
	if near:
		player.receive_near_miss(_hit())


# Its origin is the player's own hurtbox centre, so any facing answers it: the parry is a timing check,
# not an aiming one.
func _hit() -> RefCounted:
	var centre: Vector2 = player.hurtBox.get_node("CollisionShape2D").global_position
	return HitInfo.make(SHOT_ID, self, centre, body)


func _stop(result: int) -> void:
	answered.emit(result)
	_free_now()


func _free_now() -> void:
	spent = true
	hitbox_shape.set_deferred("disabled", true)
	queue_free()


#WHAT IS DRAWN

# Straight off the ball, beside its hitbox: that is where PlayerCombatFx looks for a parried
# projectile's art, to flash it and leave the shared parry shatter where it broke up.
# Never rotated: the other quadrants are the drawn headings' flips.
func _build() -> void:
	var spec := Layout.fx(&"ball")
	sheet = Sprite2D.new()
	sheet.texture = load(spec.texture)
	sheet.hframes = spec.hframes
	sheet.scale = Vector2.ONE * Layout.SCALE
	add_child(sheet)
	var pick: Array = Layout.art_frame(heading, spec.headings)
	heading_index = pick[0]
	sheet.flip_h = pick[1]
	sheet.flip_v = pick[2]
	sheet.offset = Layout.flipped_offset(spec.offset, pick[1], pick[2])
	_step_art()


func _step_art() -> void:
	var spec := Layout.fx(&"ball")
	var per: int = spec.frames_per_heading
	var frame_time: float = spec.frame_time
	sheet.frame = heading_index * per + int(life / frame_time) % per


# The parry's burst for a shot and a swing alike (FX_FOR_CODER). Left on `layer`, so it plays out after
# whatever was parried is gone.
static func clash_at(layer: Node, at: Vector2) -> void:
	var spec := Layout.fx(&"clash")
	var clash := Sprite2D.new()
	clash.texture = load(spec.texture)
	clash.hframes = spec.hframes
	clash.scale = Vector2.ONE * Layout.SCALE
	clash.offset = spec.offset
	layer.add_child(clash)
	clash.global_position = at.round()
	var frame_time: float = spec.frame_time
	var play := clash.create_tween()
	for i in range(1, clash.hframes):
		play.tween_interval(frame_time)
		play.tween_callback(clash.set_frame.bind(i))
	play.tween_interval(frame_time)
	play.tween_callback(clash.queue_free)
