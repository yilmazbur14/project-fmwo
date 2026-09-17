extends State

@export var animation_player : AnimationPlayer
@export var mech : Node2D
@export var hurtbox : Area2D
@export var downed_sfx_player : AudioStreamPlayer
@export var vulnerable_timer : Timer

# Long enough to dash back through the shockwave, reach the mech and land the hit cap.
const DURATION := 3.5

@onready var state_machine = get_parent()


func Enter() -> void:
	mech.hits_this_window = 0
	mech.daze_used = false
	animation_player.play("vulnerable")
	downed_sfx_player.play()
	hurtbox.set_deferred("monitoring", true)
	hurtbox.set_deferred("monitorable", true)
	vulnerable_timer.start(DURATION)


func Exit() -> void:
	vulnerable_timer.stop()
	# A hit queues the vulnerable loop behind the hit frame; it mustn't outlive the window.
	animation_player.clear_queue()
	hurtbox.set_deferred("monitoring", false)
	hurtbox.set_deferred("monitorable", false)


func _on_vulnerable_timer_timeout() -> void:
	state_machine.start_cycle()
