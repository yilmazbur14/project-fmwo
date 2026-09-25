extends State

# His dizzy spell after a parried headbutt (plan section 6): down from the flip back onto his feet, dazed on
# his recoil's held frame and open to punches for the parry's stagger time - hit_cap of them, and no daze, so
# no finisher here (DannyBossScript.can_be_dazed) - then he shakes himself awake into Idle. A bare transition
# into it opens a working window of stagger_time.

@export var body : CharacterBody2D
# This window's cap (DannyBossScript.window_hit_cap).
@export var hit_cap := 3
# Its length when nothing set `window` before the transition: PlayerDefense's own parry_stagger_time.
@export var stagger_time := 1.2

@onready var state_machine = get_parent()

# The Headbutt sets it just before the transition, to the stagger the parry handed it; used once.
var window := 0.0
# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
var left := 0.0


func Enter() -> void:
	released = false
	left = window if window > 0.0 else stagger_time
	window = 0.0
	body.velocity = Vector2.ZERO
	body.show_body()
	var player: Node2D = state_machine.get_player()
	if player:
		body.face_toward(player.global_position)
	body.set_body_box(&"idle")
	body.hits_this_window = 0
	body.set_hurtbox_active(true)
	body.state_anim = &"hit"
	body.play_anim(&"hit")


func Physics_Update(delta: float) -> void:
	if released:
		return
	left -= delta
	if left > 0.0:
		return
	# Idle lets a wake carry on into its own idle, as the Break's get-up does.
	body.play_anim(&"wake", &"idle")
	state_machine.attack_done(self)


# A punch landed: he flinches and stays dazed.
func flinch() -> void:
	body.play_anim(&"hit")


func Exit() -> void:
	release()


func release() -> void:
	if released:
		return
	released = true
	if not is_instance_valid(body):
		return
	body.set_hurtbox_active(false)
	body.set_body_box(&"idle")


func _exit_tree() -> void:
	released = true
