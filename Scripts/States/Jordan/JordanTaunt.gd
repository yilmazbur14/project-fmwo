extends State

@export var animation_player : AnimationPlayer
@export var hurtbox : Area2D
@export var taunt_sfx_player : AudioStreamPlayer
@export var body : CharacterBody2D

@onready var state_machine = get_parent()

var elapsed := 0.0


# He stays put and can be punched while his figures chase the player.
func Enter() -> void:
	body.hits_this_window = 0
	body.daze_used = false
	animation_player.play("taunt")
	taunt_sfx_player.play()
	hurtbox.set_deferred("monitoring", true)
	hurtbox.set_deferred("monitorable", true)
	elapsed = 0.0


func Exit() -> void:
	hurtbox.set_deferred("monitoring", false)
	hurtbox.set_deferred("monitorable", false)


func Physics_Update(delta: float) -> void:
	elapsed += delta
	if elapsed >= state_machine.TAUNT_TIME:
		state_machine.on_child_transition(self, "Idle")
