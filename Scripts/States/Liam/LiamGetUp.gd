extends State

# Up out of his window (plan section 4): after `delay` more on the mat (a finisher's stagger, a juggle's lying beat), he
# stands, air-blasts the player back to the bottom middle, slams his staff, and a new pillar rises under him and carries
# him back up to PERCH; there he slams again and the row rises either side of him (ROW), the player's footing goes back
# to the ice if they are standing on it, and the loop goes on with the next attack. Out of a parried lunge's window
# (to_stump) his pillar is still there, sunk to a stump at PERCH: after the blast he teleports onto it (TELEPORT_OUT,
# ARRIVE) and raises it under him (RAISE), and it keeps its hits.

const LiamGust := preload("res://Scripts/LiamGust.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const Layout := preload("res://Scripts/LiamArtLayout.gd")
const LiamElementFx := preload("res://Scripts/LiamElementFx.gd")

enum Beat { DOWN, STAND, BLAST, SLAM, RISE, RIDE, ROW, TELEPORT_OUT, ARRIVE, RAISE }

# slam_rise's impact: its first two frames, raise and overhead.
const SLAM_IMPACT := 0.25
# The slam on his pillar at the top: the row rises from it.
const ROW_SLAM_IMPACT := 0.2
const SLAM_SHAKE := 10.0
const SLAM_SHAKE_STEPS := 5
const SLAM_SHAKE_STEP_TIME := 0.03

var body: CharacterBody2D
var state_machine: Node
# Seconds more on the mat before he stands; set by the state machine before this is entered.
var delay := 0.0
var beat := Beat.DOWN
var clock := 0.0
var fired := false
var ride_from := Vector2.ZERO
var ride_time := 0.0
# Set by the state machine before a parried lunge's window ends (lunge_parried); read and cleared as this is entered.
var to_stump := false
var stump := false


func Enter() -> void:
	clock = 0.0
	fired = false
	stump = to_stump
	to_stump = false
	body.set_hurtbox_active(false)
	beat = Beat.DOWN
	if delay <= 0.0:
		_start(Beat.STAND)
	elif body.current_anim != &"downed":
		body.play_anim(&"downed")


func Physics_Update(delta: float) -> void:
	clock += delta
	var sm: Node = state_machine
	match beat:
		Beat.DOWN:
			if clock >= delay:
				_start(Beat.STAND)
		Beat.STAND:
			if clock >= sm.stand_time:
				_start(Beat.BLAST)
		Beat.BLAST:
			if not fired and clock >= sm.blast_windup:
				fired = true
				LiamGust.burst(body.fx_layer, body.pose_point(&"staff_tip", &"blast"))
				body.play_sfx(&"gust")
				var player: Node2D = sm.get_player()
				if player != null:
					sm.launch_player(sm.launch_spot(player.global_position))
			if fired and not sm.is_launching():
				_start(Beat.TELEPORT_OUT if stump else Beat.SLAM)
		Beat.SLAM:
			if clock >= SLAM_IMPACT:
				_start(Beat.RISE)
		Beat.RISE:
			body.stand_on_pillar()
			if clock >= sm.rise_time:
				_start(Beat.RIDE)
		Beat.RIDE:
			var weight := clampf(clock / ride_time, 0.0, 1.0)
			body.pillar.global_position = ride_from.lerp(sm.PERCH, weight).round()
			body.stand_on_pillar()
			if weight >= 1.0:
				body.pillar.park()
				_start(Beat.ROW)
		Beat.ROW:
			if not fired and clock >= ROW_SLAM_IMPACT:
				fired = true
				body.play_sfx(&"slam")
				ScreenView.shake(get_tree(), SLAM_SHAKE, SLAM_SHAKE_STEPS, SLAM_SHAKE_STEP_TIME)
				body.row.rise(sm.row_rise_time, sm.row_ripple)
			if fired and clock >= ROW_SLAM_IMPACT + sm.row_rise_time:
				body.play_anim(&"perch_idle")
				body.perch()
				_footing_back()
				sm.get_up_finished(self)
		Beat.TELEPORT_OUT:
			if clock >= sm.teleport_time:
				_start(Beat.ARRIVE)
		Beat.ARRIVE:
			body.stand_on_pillar()
			if clock >= sm.teleport_time:
				_start(Beat.RAISE)
		Beat.RAISE:
			body.stand_on_pillar()
			if clock >= sm.rise_time:
				body.play_anim(&"perch_idle")
				body.perch()
				_footing_back()
				sm.get_up_finished(self, false)


# He's back up: a player standing on the ice slides on it again.
func _footing_back() -> void:
	var player: Node2D = state_machine.get_player()
	if player != null and body.flood.is_frozen_at(player.global_position):
		state_machine.set_player_ice(true)


func _start(next: Beat) -> void:
	beat = next
	clock = 0.0
	var sm: Node = state_machine
	match next:
		Beat.STAND:
			body.set_body_box(&"standing")
			body.play_anim(&"stand_up")
		Beat.BLAST:
			body.play_anim(&"blast")
		Beat.SLAM:
			body.play_anim(&"slam_rise")
		Beat.RISE:
			body.play_sfx(&"slam")
			ScreenView.shake(get_tree(), SLAM_SHAKE, SLAM_SHAKE_STEPS, SLAM_SHAKE_STEP_TIME)
			body.set_target_active(false)
			body.shadow.visible = false
			body.pillar.rise(body.global_position, sm.rise_time)
			body.stand_on_pillar()
		Beat.RIDE:
			ride_from = body.pillar.global_position
			ride_time = sm.ride_time_for(ride_from)
			body.play_anim(&"ride")
		Beat.ROW:
			fired = false
			body.play_anim(&"slam")
		Beat.TELEPORT_OUT:
			body.set_target_active(false)
			body.play_anim(&"teleport")
			body.play_sfx(&"teleport_out")
			LiamElementFx.puff(body.fx_layer, body.feet_position())
		Beat.ARRIVE:
			body.shadow.visible = false
			body.stand_on_pillar()
			body.set_facing(false)
			body.play_anim(&"teleport_in")
			body.play_sfx(&"teleport_in")
			LiamElementFx.puff(body.fx_layer, body.feet_position(), true)
		Beat.RAISE:
			body.play_anim(&"ride")
			body.pillar.set_risen_to(1.0, sm.rise_time)
