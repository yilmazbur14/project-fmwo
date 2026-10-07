extends State

const KaijuLayout := preload("res://Scripts/JordanKaijuLayout.gd")

@export var body : CharacterBody2D

@onready var state_machine = get_parent()

var rested := 0.0
# On the kaiju: what is left of the roar into Phase B.
var roar_left := 0.0


func Enter() -> void:
	if state_machine.kaiju_mode:
		rested = 0.0
		roar_left = 0.0
		body.play_state_anim(&"ride_taunt" if body.mounted else &"idle")
		return
	# Out of his intro he is idling already, and restarting the loop would jump him a frame as the
	# fight starts.
	if body.current_anim != &"idle":
		body.play_state_anim(&"idle")
	rested = 0.0


# The rest only starts once the last swarm is over, so a summon never piles onto the one before.
func Physics_Update(delta: float) -> void:
	if state_machine.kaiju_mode:
		_kaiju_turns(delta)
		return
	if not state_machine.finisher_stagger_timer.is_stopped() or not state_machine.swarm_over():
		return
	rested += delta
	if rested >= state_machine.IDLE_TIME:
		state_machine.on_child_transition(self, "SummonFunkos")


# On the kaiju: its rest, the roar into Phase B the first time he is down to half, then its next turn. Its figures
# need no waiting out: every fuse is out well before the next turn throws again.
func _kaiju_turns(delta: float) -> void:
	if not state_machine.finisher_stagger_timer.is_stopped():
		return
	var kaiju: Node2D = state_machine.kaiju
	if roar_left > 0.0:
		roar_left -= delta
		if roar_left <= 0.0:
			state_machine.phase_b = true
			kaiju.light_spines(0)
			kaiju.play_anim(&"idle")
		return
	if not state_machine.phase_b and body.get_health_ratio() <= KaijuLayout.PHASE_B_AT:
		roar_left = state_machine.phase_roar
		kaiju.play_anim(&"roar")
		kaiju.light_spines(8)
		state_machine.play_sfx(&"roar")
		return
	rested += delta
	if rested >= (state_machine.rest_b if state_machine.phase_b else state_machine.rest_a):
		state_machine.on_child_transition(self, state_machine.next_turn())
