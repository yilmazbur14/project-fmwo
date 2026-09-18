extends Node2D

# Eric's thrown greatsword. The node sits on the ground under the sword, where the shadow is
# drawn; the spinning sword is drawn `height` px above that. Planted, the node is where the
# blade enters the ground.
# It reports its own hits rather than letting the player's hurtbox find it, because the throw needs
# the result: a parried sword stops dead and is flung back at Eric instead of finishing its arc. The
# dodge-ghost branch is mandatory, or the sword would silently eat perfect dodges.

signal landed
signal returned
# The flung-back sword reaching Eric.
signal struck_thrower

const EricArtLayout := preload("res://Scripts/EricArtLayout.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const DefenseHypeArtLayout := preload("res://Scripts/DefenseHypeArtLayout.gd")

const SPIN_FRAME_TIME := 0.05
# Flights end or start with the spinning sword's centre where the planted sword's centre is, so
# the two line up.
const PLANTED_HEIGHT := -EricArtLayout.PLANTED_OFFSET.y * EricArtLayout.SCALE
const ARC_HEIGHT := 60.0
const MIN_FLIGHT_TIME := 0.15
# A throw at someone almost on top of him covers so little ground that it would otherwise arrive in
# MIN_FLIGHT_TIME, before they could answer it. This floor keeps a short throw hanging in the air
# instead, so the toss is always something to read. A recall and a flung-back sword keep
# MIN_FLIGHT_TIME: neither is the player's problem.
const THROW_MIN_FLIGHT := 0.72
# A caught sword stops spinning and eases to a stop in his hand over this long, so the last frame
# it's drawn on already matches his catch frame, which replaces it on arrival. Shorter than
# MIN_FLIGHT_TIME.
const CATCH_SETTLE_TIME := 0.1
# The throw is lobbed this far above the straight line between his hand and the landing spot, and
# gives all of it back over the last DIVE_TIME of the flight: the sword cruises in high, then comes
# down into the ground instead of sliding in flat.
# The dive is a duration, not a distance, so it keeps its length as his throws speed up with his
# rage. It has to outlast PlayerDefense.parry_window, or the window would open while the sword was
# still cruising and the parry could be pressed before there was anything to read.
const THROW_LOB := 130.0
const DIVE_TIME := 0.32
# Height above planted height per step of the shadow shrinking; frame 0 is low, frame 2 high.
const SHADOW_STEP := 70.0
const SHADOW_FRAMES := 3
const PLANTED_DUST_TIME := 0.1
# A flung-back sword is lit in the parry's own colour, so it reads as the player's the whole way in.
const REFLECT_TINT: Color = DefenseHypeArtLayout.PARRY_FLASH[0]

# Along its drawn path, in px/s; set by the throw.
var speed := 1400.0
# Both set by the throw, before the sword is added to the tree.
var player: Node2D
var thrower: Node2D

@onready var shadow: Sprite2D = $Shadow
@onready var sword: Sprite2D = $Sword
@onready var planted: Sprite2D = $Planted
@onready var hitbox: Area2D = $Hitbox

var from_ground: Vector2
var to_ground: Vector2
var from_height := 0.0
var to_height := 0.0
var duration := 0.0
var elapsed := 0.0
var arrival_frame := 0
var flying := false
var returning := false
var reflecting := false
var catch_lean := 0.0
var planted_time := -1.0


func _ready() -> void:
	for sprite in [shadow, sword, planted]:
		sprite.scale = Vector2(EricArtLayout.SCALE, EricArtLayout.SCALE)
	sword.hframes = EricArtLayout.SPIN_FRAMES
	planted.hframes = EricArtLayout.PLANTED_FRAMES
	planted.offset = EricArtLayout.PLANTED_OFFSET
	hitbox.get_node("CollisionShape2D").shape.radius = EricArtLayout.SWORD_HITBOX_RADIUS
	hitbox.set_meta(HitInfo.META_ATTACK, &"eric_thrown_sword")


# `hand` is the sword's centre as it leaves his hand; `ground_y` is the floor line under Eric.
func throw(hand: Vector2, ground_y: float, target: Vector2) -> void:
	sword.flip_h = false
	_fly(Vector2(hand.x, ground_y), ground_y - hand.y, target, PLANTED_HEIGHT, EricArtLayout.SPIN_LANDING_FRAME)


# Flies back into his hand and arrives as the sword on his catch frame: centred on `centre`, the
# upright catch spin frame turned `lean` radians. `mirrored` plays the spin forward flipped, which
# keeps the trail behind the blade on the way back.
func recall(centre: Vector2, ground_y: float, lean: float, mirrored: bool) -> void:
	returning = true
	catch_lean = lean
	sword.flip_h = mirrored
	_fly(global_position, PLANTED_HEIGHT, Vector2(centre.x, ground_y), ground_y - centre.y, EricArtLayout.SPIN_CATCH_FRAME)


# Flung back at Eric after a parry: from where the player stopped it, spinning the other way and lit
# up, straight at `centre` on his body. It never plants and can't touch the player on the way.
# Either leg of the throw can be parried, so the catch's ease and lean are dropped here.
func reflect(centre: Vector2, ground_y: float, back_speed: float) -> void:
	reflecting = true
	returning = false
	speed = back_speed
	sword.flip_h = not sword.flip_h
	sword.rotation = 0.0
	sword.modulate = REFLECT_TINT
	_fly(global_position, -sword.position.y, Vector2(centre.x, ground_y), ground_y - centre.y, EricArtLayout.SPIN_LANDING_FRAME)


func _fly(start_ground: Vector2, start_height: float, end_ground: Vector2, end_height: float, end_frame: int) -> void:
	from_ground = start_ground
	to_ground = end_ground
	from_height = start_height
	to_height = end_height
	var path_length := (start_ground - Vector2(0, start_height)).distance_to(end_ground - Vector2(0, end_height))
	var floor_time := MIN_FLIGHT_TIME if returning or reflecting else THROW_MIN_FLIGHT
	duration = maxf(path_length / speed, floor_time)
	arrival_frame = end_frame
	elapsed = 0.0
	flying = true
	planted_time = -1.0
	sword.visible = true
	shadow.visible = true
	planted.visible = false
	# A flung-back sword is the player's: it mustn't hurt them on its way out.
	hitbox.monitoring = not reflecting
	_place()


func _physics_process(delta: float) -> void:
	if flying:
		elapsed = minf(elapsed + delta, duration)
		_place()
		if hitbox.monitoring:
			_resolve_hits()
		# A parry stops it where it was caught, so it may not be flying any more.
		if flying and elapsed >= duration:
			flying = false
			hitbox.monitoring = false
			if reflecting:
				struck_thrower.emit()
			elif returning:
				returned.emit()
			else:
				_plant()
	elif planted_time >= 0.0:
		planted_time += delta
		planted.frame = 0 if planted_time < PLANTED_DUST_TIME else 1


func _resolve_hits() -> void:
	if not is_instance_valid(player):
		return
	var near_miss := false
	for area in hitbox.get_overlapping_areas():
		if area == player.hurtBox:
			# A parry catches the sword in the air; the throw flings it back from there.
			if player.receive_hit(_hit()) == HitInfo.Result.PARRIED:
				flying = false
				hitbox.monitoring = false
			return
		if player.is_dodge_ghost(area):
			near_miss = true
	# Only where the player isn't: the sword passing the spot a dash left is a perfect dodge.
	if near_miss:
		player.receive_near_miss(_hit())


func _hit() -> RefCounted:
	return HitInfo.make(&"eric_thrown_sword", hitbox, hitbox.global_position, thrower)


func _place() -> void:
	var t := _progress()
	global_position = from_ground.lerp(to_ground, t)
	# Only the outward throw dives: a recall is a catch and a flung-back sword is aimed at Eric's
	# body, so both keep the plain lob.
	var diving := not returning and not reflecting
	var dive := _dive_progress() if diving else 0.0
	var height := lerpf(from_height, to_height, t)
	if diving:
		height += THROW_LOB * sqrt(t) * (1.0 - dive)
	else:
		height += ARC_HEIGHT * 4.0 * t * (1.0 - t)
	sword.position = Vector2(0, -height)
	# The blade goes in tip first, so on the way down the hitbox rides from the sword's centre to
	# where that tip enters the ground. It is the only part of the dive that reaches a player
	# standing on the landing spot: the sword's own centre passes PLANTED_HEIGHT over their head.
	hitbox.position = Vector2(0, -(height - PLANTED_HEIGHT * dive))
	var spin_left := duration - elapsed
	if returning:
		var settle := clampf(1.0 - spin_left / CATCH_SETTLE_TIME, 0.0, 1.0)
		sword.rotation = catch_lean * (1.0 - pow(1.0 - settle, 3.0))
		spin_left -= CATCH_SETTLE_TIME
	# Counted back from the arrival, so the last spin frame drawn is the one it lands or is caught on.
	sword.frame = posmod(arrival_frame + 1 - maxi(ceili(spin_left / SPIN_FRAME_TIME), 1), EricArtLayout.SPIN_FRAMES)
	shadow.frame = clampi(int((height - PLANTED_HEIGHT) / SHADOW_STEP), 0, SHADOW_FRAMES - 1)


# How far into the dive the throw is: 0 while it is still cruising, 1 as it plants.
func _dive_progress() -> float:
	return clampf(1.0 - global_position.distance_to(to_ground) / (DIVE_TIME * speed), 0.0, 1.0)


# Fraction of the path covered. A catch eases out over the settle, so the rest of that flight runs
# a little faster to arrive on time.
func _progress() -> float:
	var t := elapsed / duration
	if not returning:
		return t
	var settle := CATCH_SETTLE_TIME / duration
	var speed_up := 1.0 / (1.0 - settle * 2.0 / 3.0)
	if t <= 1.0 - settle:
		return t * speed_up
	return 1.0 - speed_up / (3.0 * settle * settle) * pow(1.0 - t, 3.0)


func _plant() -> void:
	sword.visible = false
	shadow.visible = false
	planted.visible = true
	planted.frame = 0
	planted_time = 0.0
	landed.emit()
