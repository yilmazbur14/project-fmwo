extends State

# An attack is over, by its own end or a round's, and at the start of the fight (plan section 4, addendum 4): the pillar
# is shielded, his staff winds up for blast_windup and his wind throws the player to the bottom middle (RESET_SPOT) on
# rails (LiamStateMachine.launch_player), unhurt. resume_delay after they land, the next attack in the loop. A player
# already within launch_skip of the spot (his water blast leaves them there) gets no gust at all: straight on. The floor
# is left as it is: the ice carries on into attack 3.

const LiamGust := preload("res://Scripts/LiamGust.gd")

var body: CharacterBody2D
var state_machine: Node
var clock := 0.0
var fired := false
# His clock when the player was down again: -1 until then.
var landed_at := -1.0
# The player is already on the spot: no gust, straight on.
var skip := false


func Enter() -> void:
	clock = 0.0
	fired = false
	landed_at = -1.0
	body.pillar.set_shielded(true)
	var player: Node2D = state_machine.get_player()
	skip = player == null or (player.global_position.distance_to(state_machine.RESET_SPOT) <= state_machine.launch_skip \
		and not state_machine.is_launching())
	if not skip:
		body.play_anim(&"blast", &"perch_idle")


func Physics_Update(delta: float) -> void:
	# Not in Enter: this isn't the current state yet there, and blast_finished would be refused.
	if skip:
		state_machine.blast_finished(self)
		return
	clock += delta
	if not fired and clock >= state_machine.blast_windup:
		fired = true
		LiamGust.burst(body.fx_layer, body.pose_point(&"staff_tip", &"blast"))
		body.play_sfx(&"gust")
		var player: Node2D = state_machine.get_player()
		if player == null or not state_machine.launch_player(state_machine.RESET_SPOT):
			landed_at = clock
	if fired and landed_at < 0.0 and not state_machine.is_launching():
		landed_at = clock
	if landed_at >= 0.0 and clock >= landed_at + state_machine.resume_delay:
		state_machine.blast_finished(self)
