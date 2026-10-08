extends State

# Greyson's throw (plan section 3.1), the first link of attack 1: six weight plates off the ropes, in two fans of
# three (the user, 2026-09-27: "a few more discs" that "bounce more times"; 2026-09-28: "lets have greysons discs
# bounce 10 times"). He winds up under the red badge, then lets them go 0.28 s apart (2026-09-30, the setup's pace):
# the first at the player's feet as it leaves his hand, the next two 35 degrees either side of that same line; then
# the fourth at the player's feet again, wherever they have got to, turning to them for it, and the fifth and sixth
# 35 degrees either side of its line. Each is its own GreysonPlateScript, ten ropes long, and flies on through his
# slams and his poses until its last rope, the player answers it, or a Break or the fight's end takes it; his next
# throw cuts short any still flying (GreysonStateMachine.plate_wait_cap).
#   0.00  throw, the wind-up (f0), the badge, the parry rearmed
#   0.35  plate 1 on the release frame (f2)
#   0.56  throw_again (f1-f3, played to fit the spacing): plate 2 on its release frame at 0.63
#   0.91, 1.19, 1.47, 1.75  plates 3-6 the same
#   1.80  done
# He can't be hit here.

const ParryTell := preload("res://Scripts/ParryTell.gd")
const PLATE_SCRIPT := preload("res://Scripts/GreysonPlateScript.gd")
const Layout := preload("res://Scripts/GreysonArtLayout.gd")

const PLATE_ID := &"greyson_plate"

@export var body : CharacterBody2D

#KNOBS (seconds, px, degrees)
# When each plate leaves his hand: the throw sheet's release frame. The first is the badge's wind-up, the fight's
# 0.35 s read floor. The rethrow (f1-f3) runs 0.34 s at its own pace, and is played faster to fit a closer spacing.
@export var release_at: Array[float] = [0.35, 0.63, 0.91, 1.19, 1.47, 1.75]
# How long before each release after the first the throw's f1-f3 comes round again, at the sheet's own pace (f1's
# time): sped up with the rethrow.
@export var rethrow_lead := 0.08
# Each plate in turn: whether it takes a fresh line at the player's feet as it leaves (plate 1 always does), and
# how far it turns off the line it goes by. Plates 2 and 3 cover the lanes either side of plate 1; plate 4 goes
# where they have gone since, and plates 5 and 6 cover the lanes either side of it.
@export var fresh_aim: Array[bool] = [true, false, false, true, false, false]
@export var spreads: Array[float] = [0.0, 35.0, -35.0, 0.0, 35.0, -35.0]
# The last plate's follow-through is cut short by the slams' first teleport.
@export var done_at := 1.80
@export var plate_speed := 950.0
# Measured to where its hit circle first touches the player's hurtbox, not to their feet: the box stands over the
# feet and is wide, so a first leg timed to the feet touched them 0.10-0.20 s sooner from 200-260 px.
@export var min_flight := 0.40
# Closer than this to his hand a plate has no flight to give, so it keeps the old timing to the feet and the throw's
# red badge is the read. Making those harmless instead left a safe pocket beside him through the whole throw.
@export var min_contact := 40.0
@export var bounces := 10
# A cap for a plate that never finds its last rope, past the longest flight to it of any plate thrown at a player
# 30 px or more from his hand: 29.5 s, along the ring's length after a first leg slowed to 75 px/s.
@export var plate_life := 30.0

@onready var state_machine = get_parent()

# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
var clock := 0.0
var thrown := 0
# Throw animations started: the first covers plate 1, and each rethrow the next plate.
var wound := 0
# The line the plates go by, latched at the player's feet as plate 1 leaves his hand and again for each fresh aim.
var line := Vector2.RIGHT
# For tests: every plate this throw sent, the fight_clock each left at, where from, the way each went, and the
# player's feet then.
var plates: Array[Node2D] = []
var release_clocks: Array[float] = []
var release_points: Array[Vector2] = []
var headings: Array[Vector2] = []
var aimed_at: Array[Vector2] = []
# For tests: the distance each first leg's speed was set from, and whether it left his hand inside min_contact of them.
var first_legs: Array[float] = []
var point_blank: Array[bool] = []
var entered_count := 0


func Enter() -> void:
	released = false
	entered_count += 1
	clock = 0.0
	thrown = 0
	wound = 1
	plates.clear()
	release_clocks.clear()
	release_points.clear()
	headings.clear()
	aimed_at.clear()
	first_legs.clear()
	point_blank.clear()
	body.velocity = Vector2.ZERO
	body.set_hurtbox_active(false)
	body.show_body()
	_face_player()
	body.play_anim(&"throw")
	ParryTell.telegraph(body, PLATE_ID, release_at[0], body.tell_anchor)
	# ALWAYS, at the throw's tell: a press that whiffed earlier must never lock the first plate out.
	state_machine.rearm_parry()
	body.update_hud_fade(&"throw")


func Physics_Update(delta: float) -> void:
	if released:
		return
	clock += delta
	if thrown < release_at.size() and wound == thrown and clock >= release_at[thrown] - rethrow_lead * _rethrow_pace(thrown):
		wound += 1
		if _aims_afresh(thrown):
			_face_player()
		var pace := _rethrow_pace(thrown)
		body.play_anim(&"throw_again", &"", 0.0 if pace >= 1.0 else Layout.loop_length(Layout.anim(&"throw_again")) * pace)
	if thrown < release_at.size() and clock >= release_at[thrown]:
		_release()
	if clock >= done_at:
		state_machine.chain_next(self)


func Exit() -> void:
	release()


func release() -> void:
	if released:
		return
	released = true
	if is_instance_valid(body):
		ParryTell.clear(body)


# Leaving with his whole scene: the badge is going with it.
func _exit_tree() -> void:
	released = true


func _release() -> void:
	var from: Vector2 = body.release_point(&"throw") + Vector2(0.0, PLATE_SCRIPT.FLIGHT.height)
	var feet: Vector2 = state_machine.player_feet()
	if thrown == 0:
		ParryTell.clear(body)
		body.restore_hud()
	if _aims_afresh(thrown):
		line = feet - from
		if line.length() < 1.0:
			line = Vector2.LEFT if body.facing_left else Vector2.RIGHT
	var plate: Node2D = PLATE_SCRIPT.new()
	plate.max_speed = plate_speed
	plate.min_flight = min_flight
	plate.bounces = bounces
	plate.max_life = plate_life
	plate.ropes = state_machine.ROPES
	plate.player = state_machine.get_player()
	plate.body = body
	var heading: Vector2 = line.rotated(deg_to_rad(spreads[thrown % spreads.size()])).normalized()
	var reach: float = from.distance_to(feet)
	var contact := first_contact(from, heading, reach)
	if contact >= min_contact:
		reach = minf(contact, reach)
	plate.aim(heading, reach)
	state_machine.add_hazard(plate, from, body.hazard_layer)
	body.play_sfx(&"plate_throw")
	plates.append(plate)
	release_clocks.append(body.fight_clock)
	release_points.append(plate.global_position)
	headings.append(plate.heading)
	aimed_at.append(feet)
	first_legs.append(reach)
	point_blank.append(contact >= 0.0 and contact < min_contact)
	thrown += 1


# How far a plate leaving `from` (its shadow, on the floor under his hand) along `heading` goes before its hit circle
# first touches the player's hurtbox where they stand: -1 if it doesn't within `reach` and a little past it.
func first_contact(from: Vector2, heading: Vector2, reach: float) -> float:
	var player: Node2D = state_machine.get_player()
	if player == null:
		return -1.0
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	var lift := Vector2(0.0, -PLATE_SCRIPT.FLIGHT.height)
	var radius: float = Layout.fx(&"plate").radius
	var along := 0.0
	while along <= reach + 2.0 * radius:
		var centre: Vector2 = from + heading * along + lift
		if centre.distance_to(centre.clamp(box.position, box.end)) <= radius:
			return along
		along += 2.0
	return -1.0


func _aims_afresh(index: int) -> bool:
	return index == 0 or fresh_aim[index % fresh_aim.size()]


# How fast plate `index`'s rethrow plays: its own pace, or faster to fit the gap since the plate before it.
func _rethrow_pace(index: int) -> float:
	if index <= 0:
		return 1.0
	var gap: float = release_at[index] - release_at[index - 1]
	return minf(gap / Layout.loop_length(Layout.anim(&"throw_again")), 1.0)


func _face_player() -> void:
	var player: Node2D = state_machine.get_player()
	if player:
		body.face_toward(player.global_position)
