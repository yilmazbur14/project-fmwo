extends State

const JordanArtLayout := preload("res://Scripts/JordanArtLayout.gd")
const KaijuLayout := preload("res://Scripts/JordanKaijuLayout.gd")

# Where his box lies by his soles on the defeat's kneel, for the toy kaiju to hop back into.
const BOX_BY_SOLES := Vector2(51, 0)

@export var body : CharacterBody2D

# On the kaiju (JordanKaijuLayout.USE_KAIJU): it shrinks back into the toy, which hops into his fallen box; killed
# riding it, he is bucked off onto the mat and lands on the defeat's last frame, which the walk-out gets up from.
@export var shrink_time := 0.88
@export var toy_hop_time := 0.5
@export var toy_hop_apex := 60.0
@export var buck_time := 0.6
@export var buck_arc := 140.0
@export var butt_land_time := 0.14
# His butt-land sheet's frames after the arc, f2 to f4, before it holds the defeat's last frame.
@export var butt_land_rest := 0.36
# His hips over his seat as he is bucked off (the topple sheet's first frame: hips 6 texels over the seat).
const BUCK_HIPS := Vector2(0, -18)

@onready var state_machine = get_parent()

# Set by the state machine when a juggle killed him (JordanStateMachine.land_juggled): he stays lying
# where he crashed, on the juggle's `down` loop (JordanJuggled lingers on it), and never kneels.
var lying := false
var bucked := false
var kaiju_done_at := -INF


# At once, cutting the killing blow's flinch: the defeat opens on the same reel, and letting the flinch
# finish would flash the idle stance between the two.
func Enter() -> void:
	if state_machine.kaiju_mode and state_machine.kaiju != null:
		_kaiju_out()
	if lying or bucked:
		return
	body.play_anim(&"defeat")


# What is left of the kaiju's shrink and his fall off it, for the outro's first line to wait out.
func kaiju_time_left() -> float:
	return maxf(kaiju_done_at - body.fight_clock, 0.0)


func _kaiju_out() -> void:
	var kaiju: Node2D = state_machine.kaiju
	kaiju.set_walls(false)
	kaiju.light_spines(0)
	kaiju.set_charge(0.0)
	kaiju.set_lift(0.0)
	kaiju.play_anim(&"shrink", &"toy")
	var total := shrink_time + toy_hop_time
	var landing: Vector2 = body.to_global(JordanArtLayout.FLOOR_POINT)
	if body.mounted:
		bucked = true
		var seat: Vector2 = kaiju.seat_point()
		state_machine.set_mounted(false)
		landing = KaijuLayout.DEFEAT_LANDING
		var buck := create_tween()
		if not JordanArtLayout.anchors(&"butt_land").is_empty():
			# His butt-land sheet: its two air frames on the arc, then down on its soles from its third.
			body.play_anim(&"butt_land")
			body.hold_frame(0)
			buck.tween_method(_buck_drawn.bind(seat + BUCK_HIPS, landing), 0.0, 1.0, buck_time)
			buck.tween_callback(_land_drawn.bind(landing))
			total = maxf(total, buck_time + butt_land_rest)
		else:
			body.play_anim(&"topple")
			buck.tween_method(_buck.bind(body.to_global(JordanArtLayout.FLOOR_POINT), landing), 0.0, 1.0, buck_time)
			buck.tween_callback(body.play_anim.bind(&"butt_land"))
			total = maxf(total, buck_time + butt_land_time)
	var hop := create_tween()
	hop.tween_interval(shrink_time)
	hop.tween_method(_hop_toy.bind(kaiju.feet_point(), landing + BOX_BY_SOLES), 0.0, 1.0, toy_hop_time)
	hop.tween_callback(kaiju.puff_at.bind(landing + BOX_BY_SOLES))
	hop.tween_callback(kaiju.hide)
	kaiju_done_at = body.fight_clock + total


func _buck(weight: float, from: Vector2, to: Vector2) -> void:
	var soles := from.lerp(to, weight) - Vector2(0, 4.0 * buck_arc * weight * (1.0 - weight))
	body.global_position = (soles - JordanArtLayout.FLOOR_POINT).round()


func _hop_toy(weight: float, from: Vector2, to: Vector2) -> void:
	var kaiju: Node2D = state_machine.kaiju
	kaiju.place(from.lerp(to, weight))
	kaiju.set_lift(4.0 * toy_hop_apex * weight * (1.0 - weight))


func _buck_drawn(weight: float, hips: Vector2, landing: Vector2) -> void:
	body.hold_frame(0 if weight * buck_time < 0.06 else 1)
	body.place_on_arc(hips, &"pivot", 0, landing, &"soles", 1, weight, buck_arc)


func _land_drawn(landing: Vector2) -> void:
	body.play_anim(&"butt_land", &"", 2)
	body.global_position = (landing - JordanArtLayout.FLOOR_POINT).round()
