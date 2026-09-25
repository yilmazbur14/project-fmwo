extends State

# The punish window after every keg volley: he stands at HOME blowing the smoke off his muzzle, cocky and
# wide open. taunt_time on TauntTimer, plus the bonus a clean run of the kegs earned; three punches at
# most, and a charged third dazes him once for the single-bar finisher (BurakBossScript.can_be_dazed). A
# flinch plays his hit and hands back to the taunt. Enter() needs nothing from the state before it, so a
# bare transition into it opens a working window.

@export var body : CharacterBody2D
@export var taunt_timer : Timer

@onready var state_machine = get_parent()

# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true


func Enter() -> void:
	released = false
	body.velocity = Vector2.ZERO
	body.show_body()
	var player: Node2D = state_machine.get_player()
	if player:
		body.face_toward(player.global_position)
	body.hits_this_window = 0
	body.daze_used = false
	body.play_state_anim(&"taunt")
	body.set_hurtbox_active(true)
	body.play_sfx(&"taunt")
	taunt_timer.paused = false
	taunt_timer.start(state_machine.taunt_time + state_machine.take_taunt_bonus())


func Exit() -> void:
	release()


func release() -> void:
	if released:
		return
	released = true
	taunt_timer.stop()
	if is_instance_valid(body):
		body.set_hurtbox_active(false)


func flinch() -> void:
	body.play_anim(&"hit", &"taunt")


func _on_taunt_timer_timeout() -> void:
	state_machine.on_child_transition(self, "Idle")
