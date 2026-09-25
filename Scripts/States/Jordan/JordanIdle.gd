extends State

@export var body : CharacterBody2D

@onready var state_machine = get_parent()

var rested := 0.0


func Enter() -> void:
	# Out of his intro he is idling already, and restarting the loop would jump him a frame as the
	# fight starts.
	if body.current_anim != &"idle":
		body.play_state_anim(&"idle")
	rested = 0.0


# The rest only starts once the last swarm is over, so a summon never piles onto the one before.
func Physics_Update(delta: float) -> void:
	if not state_machine.finisher_stagger_timer.is_stopped() or not state_machine.swarm_over():
		return
	rested += delta
	if rested >= state_machine.IDLE_TIME:
		state_machine.on_child_transition(self, "SummonFunkos")
