extends Node2D

# Eric's thrown greatsword. The node sits on the ground under the sword, where the shadow is
# drawn; the spinning sword is drawn `height` px above that. Planted, the node is where the
# blade enters the ground.
# It reports its own hits rather than letting the player's hurtbox find it, because the throw needs
# the result: a parried sword stops dead and is flung back at Eric instead of finishing its arc. The
# dodge-ghost branch is mandatory, or the sword would silently eat perfect dodges.
# The outgoing throw only resolves anything - damage, parry or near miss - from `hot_from`, the
# progress its floor mark lights its commit frame on: what the mark promises is where and when it
# lands, and a blade that could hurt them somewhere else on the way in would be a tell that lies.

signal landed
signal returned
# The flung-back sword reaching Eric.
signal struck_thrower

const EricArtLayout := preload("res://Scripts/EricArtLayout.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const DefenseHypeArtLayout := preload("res://Scripts/DefenseHypeArtLayout.gd")
const EricSwordMark := preload("res://Scripts/EricSwordMark.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")

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
# How finely the contact scan steps through a flight, as a fraction of it.
const CONTACT_STEP := 1.0 / 240.0
# A flung-back sword is lit in the parry's own colour, so it reads as the player's the whole way in.
const REFLECT_TINT: Color = DefenseHypeArtLayout.PARRY_FLASH[0]

# Along its drawn path, in px/s; set by the throw.
var speed := 1400.0
# Both set by the throw, before the sword is added to the tree.
var player: Node2D
var thrower: Node2D
# A thrown sword plants itself in the mat. A spin release (EricWhirlwind) skips off it instead and is
# recalled straight away, and its return leg passes through the player: running in to punch the man
# who just let go of it is the read there, and a hit on the way back would punish it.
var plants := true
var returns_harmless := false

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
# The flight progress from which the outgoing throw's blade may hurt the player: the mark's commit
# frame, which is what the player is reading. Before it the blade is only passing through. 0 on the
# recall and the flung-back sword, which are aimed at Eric and have no mark to keep faith with.
var hot_from := 0.0
# The floor mark under the landing spot, while the outgoing throw is in the air.
var mark: Node2D


func _ready() -> void:
	for sprite in [shadow, sword, planted]:
		sprite.scale = Vector2(EricArtLayout.SCALE, EricArtLayout.SCALE)
	sword.hframes = EricArtLayout.SPIN_FRAMES
	planted.hframes = EricArtLayout.PLANTED_FRAMES
	planted.offset = EricArtLayout.PLANTED_OFFSET
	hitbox.get_node("CollisionShape2D").shape.radius = EricArtLayout.SWORD_HITBOX_RADIUS
	hitbox.set_meta(HitInfo.META_ATTACK, &"eric_thrown_sword")


# In a y-sorted fight the sword sorts among the fighters at its ground point, but its shadow lies on
# the floor: it goes on the floor layer, under everyone, and follows the sword from there.
func lay_shadow_on(layer: Node2D) -> void:
	if layer == get_parent():
		return
	shadow.reparent(layer)
	shadow.global_position = global_position


func _exit_tree() -> void:
	if is_instance_valid(shadow) and shadow.get_parent() != self:
		shadow.queue_free()
	# It is on the floor layer, not under the sword, so it would outlive it.
	if is_instance_valid(mark):
		mark.queue_free()


# `hand` is the sword's centre as it leaves his hand; `ground_y` is the floor line under Eric.
func throw(hand: Vector2, ground_y: float, target: Vector2) -> void:
	sword.flip_h = false
	_fly(Vector2(hand.x, ground_y), ground_y - hand.y, target, PLANTED_HEIGHT, EricArtLayout.SPIN_LANDING_FRAME)


# The mark on the floor under where this throw is going to land. It is built after throw(), since
# only then is `to_ground` known, and only for the outgoing throw: a recall and a flung-back sword
# are aimed at Eric, not at the player. It is handed back rather than parented here, so the state can
# put it on the fight's floor layer with everything else he throws.
func mark_landing() -> Node2D:
	mark = EricSwordMark.new()
	mark.name = "SwordMark"
	# The ring goes hot on the frame the blade does, because they are the same number: the throw sets
	# it in _fly() and the mark only borrows it.
	mark.commit_at = hot_from
	return mark


# The parry tell's own aura, on the blade rather than on this node's ground point: from release the
# sword itself is the only warning the player gets, on the way out and on the way back.
func glow_as_parryable() -> void:
	ParryTell.glow(sword, &"eric_thrown_sword", EricArtLayout.SWORD_GLOW_SCALE)


# Flies back into his hand and arrives as the sword on his catch frame: centred on `centre`, the
# upright catch spin frame turned `lean` radians. `mirrored` plays the spin forward flipped, which
# keeps the trail behind the blade on the way back. It starts `from_height` px over its ground point:
# where it planted itself, unless it was planted some other way (EricBroken).
func recall(centre: Vector2, ground_y: float, lean: float, mirrored: bool, from_height := PLANTED_HEIGHT) -> void:
	returning = true
	catch_lean = lean
	sword.flip_h = mirrored
	_fly(global_position, from_height, Vector2(centre.x, ground_y), ground_y - centre.y, EricArtLayout.SPIN_CATCH_FRAME)


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
	# A flung-back sword is the player's: it mustn't hurt them on its way out. Monitoring then stays on
	# for the whole of a leg that can hurt anyone; the outgoing throw's hot window is a test on the
	# flight's own clock rather than a switch here, because an Area2D takes a physics flush to start
	# reporting overlaps again and the window opens on the one frame that can't afford to be deaf.
	hitbox.monitoring = not reflecting and not (returning and returns_harmless)
	hot_from = _commit_progress() if not returning and not reflecting else 0.0
	_place()


func _physics_process(delta: float) -> void:
	if flying:
		elapsed = minf(elapsed + delta, duration)
		var t := _place()
		# The same t the mark was just given, so the blade goes hot on the frame the ring does and
		# neither can drift from the other. Until then the throw is only a tell, whatever it is
		# passing through: the dodge ghost included, since there is nothing there to dodge yet.
		if hitbox.monitoring and t >= hot_from:
			_resolve_hits()
		# A parry stops it where it was caught, so it may not be flying any more.
		if flying and elapsed >= duration:
			flying = false
			hitbox.monitoring = false
			if reflecting:
				struck_thrower.emit()
			elif returning:
				returned.emit()
			elif plants:
				_plant()
			else:
				_skip()
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
				if is_instance_valid(mark):
					mark.cancel()
				mark = null
			return
		if player.is_dodge_ghost(area):
			near_miss = true
	# Only where the player isn't: the sword passing the spot a dash left is a perfect dodge.
	if near_miss:
		player.receive_near_miss(_hit())


func _hit() -> RefCounted:
	return HitInfo.make(&"eric_thrown_sword", hitbox, hitbox.global_position, thrower)


func _place() -> float:
	var t := _progress()
	global_position = from_ground.lerp(to_ground, t)
	# The mark runs off this same clock, so the ring closing on it can't drift from the blade.
	if is_instance_valid(mark):
		mark.set_progress(t)
	# Only the outward throw dives: a recall is a catch and a flung-back sword is aimed at Eric's
	# body, so both keep the plain lob.
	var diving := not returning and not reflecting
	var dive := _dive_progress(global_position) if diving else 0.0
	var height := _thrown_height(t, dive) if diving else lerpf(from_height, to_height, t) + ARC_HEIGHT * 4.0 * t * (1.0 - t)
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
	if shadow.get_parent() != self:
		shadow.global_position = global_position
	return t


# The fraction of the flight the blade goes hot at, and the one the mark lights its commit frame on.
# It is a parry window's worth of flight before the blade reaches the player, so a press on the ring
# always has a blade to catch, and nothing before it: the throw promises a spot and a moment, and a
# blade that clipped them on the way in would be breaking that promise wherever their read said to
# press. A window, not a fraction: the flight is as long as the throw is (duration), so the window is
# whatever share of it PlayerDefense.parry_window comes to.
# Timed off when the blade reaches them rather than off the end of the flight: the two are the same
# thing from across the ring, but the blade is 108 px across and dives in tip first, so a throw from
# close up touches them with a third of its flight still to run. 0 if it arrives inside a window of
# the release, which is the truth there: press at once, and the blade is hot from the moment it
# leaves his hand.
func _commit_progress() -> float:
	return maxf(_contact_progress() - player.defense.parry_window / duration, 0.0)


# The fraction of the flight at which the blade first reaches the player standing where this throw is
# aimed, or 1 if it never does. Stepped rather than solved, the way EricWhirlwind's re-aim steps its
# lunges: it is the same curve _place() draws.
func _contact_progress() -> float:
	var body: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	var rect: Rect2 = body.global_transform * body.shape.get_rect()
	var radius: float = hitbox.get_node("CollisionShape2D").shape.radius
	var t := 0.0
	while t <= 1.0:
		var at := _blade_at(t)
		if at.clamp(rect.position, rect.end).distance_squared_to(at) <= radius * radius:
			return t
		t += CONTACT_STEP
	return 1.0


# Where the hitbox is `t` of the way through this throw, as _place() puts it: the blade rides down
# from the sword's centre to where the tip enters the ground over the dive.
func _blade_at(t: float) -> Vector2:
	var ground := from_ground.lerp(to_ground, t)
	var dive := _dive_progress(ground)
	return ground + Vector2(0, -(_thrown_height(t, dive) - PLANTED_HEIGHT * dive))


# How far into the dive a throw over `at` is: 0 while it is still cruising, 1 as it plants.
func _dive_progress(at: Vector2) -> float:
	return clampf(1.0 - at.distance_to(to_ground) / (DIVE_TIME * speed), 0.0, 1.0)


# The thrown sword's height over its ground point: the lob, given back over the dive.
func _thrown_height(t: float, dive: float) -> float:
	return lerpf(from_height, to_height, t) + THROW_LOB * sqrt(t) * (1.0 - dive)


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


# A spin release: it skips off the mat and stays out, spinning, for the recall that follows it.
func _skip() -> void:
	if is_instance_valid(mark):
		mark.land()
	mark = null
	landed.emit()


func _plant() -> void:
	sword.visible = false
	shadow.visible = false
	planted.visible = true
	planted.frame = 0
	planted_time = 0.0
	if is_instance_valid(mark):
		mark.land()
	mark = null
	landed.emit()
