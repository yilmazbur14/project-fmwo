extends State

@export var body : CharacterBody2D
@export var recover_timer : Timer
@export var recover_sfx_player : AudioStreamPlayer

@onready var state_machine = get_parent()


# The punish window.
func Enter() -> void:
	body.hits_this_window = 0
	body.daze_used = false
	body.play_anim(&"recover")
	body.set_hurtbox_active(true)
	recover_sfx_player.play()
	recover_timer.start(state_machine.recover_time)


func Exit() -> void:
	body.set_hurtbox_active(false)


func flinch() -> void:
	body.play_anim(&"hit", &"recover")


func _on_recover_timer_timeout() -> void:
	state_machine.on_child_transition(self, "Takeoff")
