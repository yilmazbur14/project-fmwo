extends State

@export var animation_player : AnimationPlayer

@onready var state_machine = get_parent()

var rested := 0.0


func Enter() -> void:
	animation_player.play("idle")
	rested = 0.0


# The rest only starts once the last swarm is over, so a summon never piles onto the one before.
func Physics_Update(delta: float) -> void:
	if not state_machine.finisher_stagger_timer.is_stopped() or not state_machine.swarm_over():
		return
	rested += delta
	if rested >= state_machine.IDLE_TIME:
		state_machine.on_child_transition(self, "SummonFunkos")
