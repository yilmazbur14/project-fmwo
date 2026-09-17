extends State

@export var body : CharacterBody2D
@export var recover_timer : Timer
@export var recover_sfx_player : AudioStreamPlayer

@onready var state_machine = get_parent()


# The punish window: the only place punches reach him.
func Enter() -> void:
	body.hits_this_window = 0
	body.daze_used = false
	body.fly_velocity = Vector2.ZERO
	body.height = 0.0
	body.place()
	body.hide_glider()
	body.set_air_draw(false)
	body.play_anim(&"recover")
	body.set_hurtbox_active(true)
	recover_sfx_player.play()
	recover_timer.start(state_machine.recover_time)


func Exit() -> void:
	body.set_hurtbox_active(false)


func flinch() -> void:
	body.play_anim(&"hit", &"recover")


func _on_recover_timer_timeout() -> void:
	state_machine.start_cycle()
