extends Node2D

# One of Greyson's weight plates (plan section 3.1), thrown flat across the ring a little over its own shadow:
# off the ropes `bounces` times, a perfect reflection off their inner edge less its radius, and gone in its vanish
# puff at the next contact.
#
# IT REPORTS ITS OWN HITS, as Matt's bolts and Captain Burak's balls do, because it needs the result: a
# parried plate is knocked down, one that lands drops, and one dashed through flies on through the player.
# Its hitbox is on no layer and in no "enemy projectile" group, so nothing else ever resolves it, and each
# plate is its own hit source, so PlayerDefense's per-source absorb keeps a throw's six apart. The latch
# keeps it off the player for the rest of the pass it was answered on.
# GONE STILL FLYING - off its last rope, or fizzled by a Break, the fight's end or its cap - it takes itself from
# under any parry press still open, and that press owes nothing for it (the user, 2026-09-28): the plate it was
# pressed for never came.
# Its origin is the player's own hurtbox centre, so any facing parries it, a plate coming back off a rope
# included. Parry-only: it isn't blockable, so a held guard is simply hit.
# Its sheet hangs under an `art` node rather than straight off the plate, so PlayerCombatFx neither flashes
# nor shatters it on a parry: it is knocked down instead, while the shared parry flash goes off as ever.

# Whatever the player's answer was, each time it is asked.
signal answered(result: int)

const HitInfo := preload("res://Scripts/HitInfo.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")
const Layout := preload("res://Scripts/GreysonArtLayout.gd")

const PLATE_ID := &"greyson_plate"
# The player's layer, where their hurtbox and dodge ghost are.
const PLAYER_LAYER := 2
# What wasn't drawn: how far over its shadow it flies (its art and its hit circle both), the shadow, a code
# ellipse on the floor under it, and the drop, knocked back along its way with a little hop onto the floor.
const FLIGHT := {
	height = 24.0,
	shadow_radii = Vector2(21, 7),
	shadow_color = Color(0, 0, 0, 0.3),
	drop_back = 30.0,
	drop_hop = 16.0,
}

# Set before it enters the tree, aim() last.
var max_speed := 760.0
var min_flight := 0.40
var bounces := 3
var max_life := 8.0
# The fight's ROPES; it turns off them pulled in by its radius.
var ropes := Rect2()
var player: Node2D
var body: Node2D

var spec: Dictionary = Layout.fx(&"plate")
var radius: float = spec.radius
var heading := Vector2.RIGHT
var speed := 0.0
var life := 0.0
var reflections := 0
var latched := false
# Knocked down and falling; gone in its puff.
var down := false
var drop_clock := 0.0
var drop_from := Vector2.ZERO
var spent := false
var hitbox: Area2D
var art: Node2D
var sheet: Sprite2D
var shadow: Polygon2D
var spin: AudioStreamPlayer
# For tests: each rope contact it turned at, with the heading it left on, and each answer the player gave.
var turns: Array = []
var results: Array[int] = []


# Its heading, and a first leg at a speed that never brings it the `reach` px to the player in under
# min_flight. After its first rope, it flies at max_speed.
func aim(toward: Vector2, reach: float) -> void:
	heading = toward.normalized()
	speed = minf(max_speed, reach / min_flight)


func _ready() -> void:
	var lift := Vector2(0.0, -FLIGHT.height)
	shadow = Polygon2D.new()
	shadow.polygon = _ellipse(FLIGHT.shadow_radii, 16)
	shadow.color = FLIGHT.shadow_color
	add_child(shadow)
	art = Node2D.new()
	art.position = lift
	add_child(art)
	sheet = Sprite2D.new()
	sheet.texture = load(spec.texture)
	sheet.hframes = spec.hframes
	sheet.offset = spec.offset
	sheet.scale = Vector2.ONE * Layout.SCALE
	art.add_child(sheet)
	hitbox = Area2D.new()
	hitbox.position = lift
	hitbox.collision_layer = 0
	hitbox.collision_mask = PLAYER_LAYER
	hitbox.monitorable = false
	var shape := CollisionShape2D.new()
	var circle := CircleShape2D.new()
	circle.radius = radius
	shape.shape = circle
	hitbox.add_child(shape)
	add_child(hitbox)
	ParryTell.glow(art, PLATE_ID)
	if is_instance_valid(body):
		spin = body.sfx_player_for(&"plate_spin", self)
		spin.play()


func _physics_process(delta: float) -> void:
	if spent:
		return
	life += delta
	sheet.frame = int(life / spec.frame_time) % sheet.hframes
	if down:
		_step_drop(delta)
		return
	global_position += heading * speed * delta
	if life >= max_life:
		fizzle()
		return
	if _off_the_ropes():
		return
	_resolve_hits()


# A rope contact: the component that went past the rope is mirrored back inside it, and a corner that took
# both at once is still one contact. The one after the last bounce is the end of it, in its vanish puff.
func _off_the_ropes() -> bool:
	var inner := ropes.grow(-radius)
	var at := global_position
	var turned := heading
	var met := false
	if at.x < inner.position.x or at.x > inner.end.x:
		var wall := inner.position.x if at.x < inner.position.x else inner.end.x
		at.x = 2.0 * wall - at.x
		turned.x = -turned.x
		met = true
	if at.y < inner.position.y or at.y > inner.end.y:
		var wall := inner.position.y if at.y < inner.position.y else inner.end.y
		at.y = 2.0 * wall - at.y
		turned.y = -turned.y
		met = true
	if not met:
		return false
	var contact := global_position.clamp(inner.position, inner.end)
	if reflections >= bounces:
		global_position = contact
		_vanish()
		return true
	reflections += 1
	heading = turned
	speed = max_speed
	global_position = at
	turns.append({"at": contact, "heading": heading})
	if is_instance_valid(body):
		body.play_fx(&"plate_bounce", contact + art.position)
		body.play_sfx(&"plate_bounce")
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
		var result: int = player.receive_hit(_hit())
		results.append(result)
		answered.emit(result)
		if result == HitInfo.Result.PARRIED or result == HitInfo.Result.HIT:
			_knock_down(result)
		else:
			latched = true
		return
	latched = false
	if near:
		player.receive_near_miss(_hit())


func _hit() -> RefCounted:
	var centre: Vector2 = player.hurtBox.get_node("CollisionShape2D").global_position
	return HitInfo.make(PLATE_ID, self, centre, body)


# Out of time, never having found its last rope: it vanishes where it is. A Break or the end of the fight takes a
# plate still flying the same way.
func fizzle() -> void:
	if spent or down:
		return
	_vanish()


# Parried or landed: no threat any more, it is knocked back along its way and falls to the floor with a hop, and
# vanishes there. A parry rings off it; one that landed just drops.
func _knock_down(result: int) -> void:
	down = true
	drop_clock = 0.0
	drop_from = global_position
	hitbox.get_child(0).set_deferred("disabled", true)
	if is_instance_valid(spin):
		spin.stop()
	if is_instance_valid(body):
		body.play_sfx(&"plate_parry" if result == HitInfo.Result.PARRIED else &"plate_drop")


func _step_drop(delta: float) -> void:
	drop_clock += delta
	var t := minf(drop_clock / spec.drop_time, 1.0)
	global_position = (drop_from - heading * FLIGHT.drop_back * t).round()
	art.position.y = roundf(-FLIGHT.height * (1.0 - t) - 4.0 * FLIGHT.drop_hop * t * (1.0 - t))
	if t >= 1.0:
		_vanish()


# Its puff where it is drawn, and the plate itself gone at once.
func _vanish() -> void:
	if not down and is_instance_valid(player):
		player.defense.whiff_owed = false
	spent = true
	hitbox.get_child(0).set_deferred("disabled", true)
	if is_instance_valid(body):
		body.play_fx(&"plate_vanish", global_position + art.position)
	queue_free()


static func _ellipse(radii: Vector2, points: int) -> PackedVector2Array:
	var polygon := PackedVector2Array()
	for i in points:
		polygon.append(Vector2.from_angle(TAU * i / points) * radii)
	return polygon
