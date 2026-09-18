extends State

@export var animation_player : AnimationPlayer
@export var hurtbox : Area2D
@export var downed_sfx_player : AudioStreamPlayer
@export var eat_timer : Timer
@export var body : CharacterBody2D

@onready var state_machine = get_parent()


func Enter() -> void:
	body.hits_this_window = 0
	body.daze_used = false
	animation_player.play("eat")
	downed_sfx_player.play()
	# Eat is entered from the driver scene's signal, which isn't guaranteed to fire
	# outside a physics flush, where direct monitoring changes are rejected.
	hurtbox.set_deferred("monitoring", true)
	hurtbox.set_deferred("monitorable", true)
	eat_timer.start(state_machine.eat_window[state_machine.cycle_phase])


func Exit() -> void:
	hurtbox.set_deferred("monitoring", false)
	hurtbox.set_deferred("monitorable", false)


func _on_eat_timer_timeout() -> void:
	state_machine.start_cycle()
