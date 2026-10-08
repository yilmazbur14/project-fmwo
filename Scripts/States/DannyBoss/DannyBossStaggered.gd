extends State

# His dizzy spell after a parried headbutt (plan section 6): down from the flip back onto his feet, dazed on
# his recoil's held frame and open to punches for the parry's stagger time - hit_cap of them, the third the POW,
# which dazes him for the single-bar finisher (DannyBossScript.can_be_dazed; the user, 2026-10-06: 3 hits always
# trigger the uppercut), whose uppercut ends the spell - then he shakes himself awake into Idle. A bare transition
# into it opens a working window of stagger_time.

@export var body : CharacterBody2D
# This window's cap (DannyBossScript.window_hit_cap).
@export var hit_cap := 3
# Its length when nothing set `window` before the transition: PlayerDefense's own parry_stagger_time.
@export var stagger_time := 1.2
# Added to a stagger the bump or the headbutt hands over. Both throw him about 180 px back off the parry (the bump's
# rebound, the headbutt's flip), 0.32 s of walking, and three punches take 1.02 s from the first press to the third
# landing (0.37 s apart, each landing 0.28 s after its press): in the parry's own 1.2 s a player reacting to his dizzy
# spell got two hits in and no POW (the 2026-10-06 tuning). This leaves a 0.2 s reaction its three with 0.15 s spare.
@export var walk_in := 0.5

@onready var state_machine = get_parent()

# The Headbutt sets it just before the transition, to the stagger the parry handed it; used once.
var window := 0.0
# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
var left := 0.0


func Enter() -> void:
	released = false
	left = window + walk_in if window > 0.0 else stagger_time
	window = 0.0
	body.velocity = Vector2.ZERO
	body.show_body()
	var player: Node2D = state_machine.get_player()
	if player:
		body.face_toward(player.global_position)
	body.set_body_box(&"idle")
	body.hits_this_window = 0
	body.daze_used = false
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
