extends Node2D

# Eric's thrown greatsword. The node sits on the ground under the sword, where the shadow is
# drawn; the spinning sword is drawn `height` px above that. Planted, the node is where the
# blade enters the ground.

signal landed
signal returned

const EricArtLayout := preload("res://Scripts/EricArtLayout.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")

const SPIN_FRAME_TIME := 0.05
# Flights end or start with the spinning sword's centre where the planted sword's centre is, so
# the two line up.
const PLANTED_HEIGHT := -EricArtLayout.PLANTED_OFFSET.y * EricArtLayout.SCALE
const ARC_HEIGHT := 60.0
const MIN_FLIGHT_TIME := 0.15
# A caught sword stops spinning and eases to a stop in his hand over this long, so the last frame
# it's drawn on already matches his catch frame, which replaces it on arrival. Shorter than
# MIN_FLIGHT_TIME.
const CATCH_SETTLE_TIME := 0.1
# Height above planted height per step of the shadow shrinking; frame 0 is low, frame 2 high.
const SHADOW_STEP := 70.0
const SHADOW_FRAMES := 3
const PLANTED_DUST_TIME := 0.1

# Along its drawn path, in px/s; set by the throw.
var speed := 1400.0

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


func _fly(start_ground: Vector2, start_height: float, end_ground: Vector2, end_height: float, end_frame: int) -> void:
	from_ground = start_ground
	to_ground = end_ground
	from_height = start_height
	to_height = end_height
	var path_length := (start_ground - Vector2(0, start_height)).distance_to(end_ground - Vector2(0, end_height))
	duration = maxf(path_length / speed, MIN_FLIGHT_TIME)
	arrival_frame = end_frame
	elapsed = 0.0
	flying = true
	planted_time = -1.0
	sword.visible = true
	shadow.visible = true
	planted.visible = false
	hitbox.monitorable = true
	_place()


func _physics_process(delta: float) -> void:
	if flying:
		elapsed = minf(elapsed + delta, duration)
		_place()
		if elapsed >= duration:
			flying = false
			hitbox.monitorable = false
			if returning:
				returned.emit()
			else:
				_plant()
	elif planted_time >= 0.0:
		planted_time += delta
		planted.frame = 0 if planted_time < PLANTED_DUST_TIME else 1


func _place() -> void:
	var t := _progress()
	global_position = from_ground.lerp(to_ground, t)
	var height := lerpf(from_height, to_height, t) + ARC_HEIGHT * 4.0 * t * (1.0 - t)
	sword.position = Vector2(0, -height)
	hitbox.position = sword.position
	var spin_left := duration - elapsed
	if returning:
		var settle := clampf(1.0 - spin_left / CATCH_SETTLE_TIME, 0.0, 1.0)
		sword.rotation = catch_lean * (1.0 - pow(1.0 - settle, 3.0))
		spin_left -= CATCH_SETTLE_TIME
	# Counted back from the arrival, so the last spin frame drawn is the one it lands or is caught on.
	sword.frame = posmod(arrival_frame + 1 - maxi(ceili(spin_left / SPIN_FRAME_TIME), 1), EricArtLayout.SPIN_FRAMES)
	shadow.frame = clampi(int((height - PLANTED_HEIGHT) / SHADOW_STEP), 0, SHADOW_FRAMES - 1)


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
