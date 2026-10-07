extends State

# Jordan back on the kaiju after a knock-off, a Break or a juggle: up off the mat and a backflip onto its seat - on its
# kneel after a knock-off, which then stands; or, down after a Break, it gets up and bows its head for him, and lifts it
# again once he is on - then, if it is away from home, it hops back there with him riding
# (JordanStateMachine.step_return). His climb sheet arcs his hips from his soles to its seat (place_on_arc), then sits
# its SEAT on the seat. The finisher's stagger, where one ended his window (end_taunt), holds him here on
# its seat until it runs out, so the next turn waits for it as the old Idle did. JordanStateMachine builds it when the
# kaiju is on.

const JordanArtLayout := preload("res://Scripts/JordanArtLayout.gd")

enum Beat { GETUP, CLIMB, STAND, RETURN, HOLD }

@export var getup_time := 0.3
@export var climb_time := 0.6
@export var climb_arc := 140.0
# His climb sheet's frames before its seat frames: the arc's length.
@export var climb_arc_time := 0.4
# The longest the kaiju takes to stand or lift its head again once he is on.
@export var stand_time := 0.45

var body: CharacterBody2D
var hurtbox: Area2D
var state_machine: Node

var beat := Beat.GETUP
var beat_clock := 0.0
var from_soles := Vector2.ZERO
var return_from := Vector2.ZERO


func Enter() -> void:
	beat_clock = 0.0
	if body.mounted:
		_stand()
		return
	beat = Beat.GETUP
	body.play_anim(&"getup")
	var kaiju: Node2D = state_machine.kaiju
	if kaiju.current_anim != &"kneel":
		kaiju.play_anim(&"stand", &"bow")


func Physics_Update(delta: float) -> void:
	beat_clock += delta
	var kaiju: Node2D = state_machine.kaiju
	match beat:
		Beat.GETUP:
			if beat_clock >= getup_time:
				beat = Beat.CLIMB
				beat_clock = 0.0
				from_soles = body.to_global(JordanArtLayout.FLOOR_POINT)
				body.play_anim(&"climb")
		Beat.CLIMB:
			var w := minf(beat_clock / climb_time, 1.0)
			var seat: Vector2 = kaiju.seat_point()
			if not body.place_anchor(&"seat", seat) and not body.place_on_arc(from_soles, &"soles", 0, seat, &"seat", 4,
					beat_clock / climb_arc_time, climb_arc):
				var soles: Vector2 = from_soles.lerp(seat, w) - Vector2(0, 4.0 * climb_arc * w * (1.0 - w))
				body.global_position = (soles - JordanArtLayout.FLOOR_POINT).round()
			if w >= 1.0:
				state_machine.set_mounted(true)
				_stand()
		Beat.STAND:
			if beat_clock >= stand_time or kaiju.anim_done or kaiju.current_anim == &"idle":
				if kaiju.current_anim != &"idle":
					kaiju.play_anim(&"idle")
				beat_clock = 0.0
				return_from = kaiju.feet_point()
				beat = Beat.HOLD if kaiju.is_home() else Beat.RETURN
		Beat.RETURN:
			if state_machine.step_return(beat_clock, return_from):
				beat = Beat.HOLD
		Beat.HOLD:
			if state_machine.finisher_stagger_timer.is_stopped():
				state_machine.on_child_transition(self, "Idle")


func _stand() -> void:
	beat = Beat.STAND
	beat_clock = 0.0
	body.play_anim(&"ride_idle")
	var kaiju: Node2D = state_machine.kaiju
	if kaiju.current_anim == &"bow":
		kaiju.play_anim(&"bow", &"idle", true)
	else:
		kaiju.play_anim(&"stand")
