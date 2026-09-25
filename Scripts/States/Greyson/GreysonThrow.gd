extends State

# Greyson's throw (plan section 3.1), the first link of attack 1: four weight plates off the ropes. He winds up
# under the red badge, then lets them go 0.35 s apart: the first at the player's feet as it leaves his hand, the
# next two 35 degrees either side of that same line, and the fourth at the player's feet again, wherever they have
# got to, turning to them for it. Each is its own GreysonPlateScript and flies on while he goes on to his slams.
#   0.00  throw, the wind-up (f0), the badge, the parry rearmed
#   0.35  plate 1 on the release frame (f2)
#   0.62  throw_again (f1-f3): plate 2 on its release frame at 0.70
#   0.97  throw_again: plate 3 at 1.05
#   1.32  throw_again: plate 4 at 1.40
#   1.75  done
# He can't be hit here.

const ParryTell := preload("res://Scripts/ParryTell.gd")
const PLATE_SCRIPT := preload("res://Scripts/GreysonPlateScript.gd")

const PLATE_ID := &"greyson_plate"

@export var body : CharacterBody2D

#KNOBS (seconds, px, degrees)
# When each plate leaves his hand: the throw sheet's release frame. The rethrow (f1-f3) runs 0.34 s, so keep them
# at least that far apart.
@export var release_at: Array[float] = [0.35, 0.70, 1.05, 1.40]
# How long before each release after the first the throw's f1-f3 comes round again.
@export var rethrow_lead := 0.08
# Each plate in turn: whether it takes a fresh line at the player's feet as it leaves (plate 1 always does), and
# how far it turns off the line it goes by. Plates 2 and 3 cover the lanes either side of plate 1; plate 4 goes
# where they have gone since.
@export var fresh_aim: Array[bool] = [true, false, false, true]
@export var spreads: Array[float] = [0.0, 35.0, -35.0, 0.0]
@export var done_at := 1.75
@export var plate_speed := 950.0
@export var min_flight := 0.40
@export var bounces := 3
@export var plate_life := 8.0

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
	if thrown < release_at.size() and wound == thrown and clock >= release_at[thrown] - rethrow_lead:
		wound += 1
		if _aims_afresh(thrown):
			_face_player()
		body.play_anim(&"throw_again")
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
	plate.aim(line.rotated(deg_to_rad(spreads[thrown % spreads.size()])), from.distance_to(feet))
	state_machine.add_hazard(plate, from, body.hazard_layer)
	body.play_sfx(&"plate_throw")
	plates.append(plate)
	release_clocks.append(body.fight_clock)
	release_points.append(plate.global_position)
	headings.append(plate.heading)
	aimed_at.append(feet)
	thrown += 1


func _aims_afresh(index: int) -> bool:
	return index == 0 or fresh_aim[index % fresh_aim.size()]


func _face_player() -> void:
	var player: Node2D = state_machine.get_player()
	if player:
		body.face_toward(player.global_position)
