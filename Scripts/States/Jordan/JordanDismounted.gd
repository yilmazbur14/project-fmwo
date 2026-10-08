extends State

# Jordan knocked off the kaiju by a parried stomp (JordanStomp), sat dazed on the mat beside the player: his punish
# window on the kaiju, in place of the old taunt. Punchable for `window` seconds from landing: a clean 3-punch chain
# (PunchAllowance), its POW dazes him and the uppercut mash follows, as off a taunt (the user, 2026-10-05: a parried
# stomp pays the uppercut; the breath's opening, JordanRecoil, pays it too since 2026-10-06). Down, he has no flinch, only the
# white flash (JordanScript._hit_feedback). Then he gets back on (JordanRemount).
# JordanStateMachine builds it when the kaiju is on.
#
# A bare transition into it (the tests' way into his window) finds him still riding: it puts him down on a spot of his
# own (JordanKaijuLayout.BARE_KNOCK_OFF) with the kaiju kneeling at home, and opens a working window there.

const KaijuLayout := preload("res://Scripts/JordanKaijuLayout.gd")

# 3.2 in the plan, 4.0 since the user asked for more openings (2026-10-04).
@export var window := 4.0
@export var dazeable := true

var body: CharacterBody2D
var hurtbox: Area2D
var state_machine: Node

var elapsed := 0.0


func Enter() -> void:
	body.hits_this_window = 0
	body.daze_used = false
	if body.mounted:
		state_machine.set_mounted(false)
		body.global_position = KaijuLayout.BARE_KNOCK_OFF
		state_machine.kaiju.play_anim(&"kneel")
	if body.stagger_tween:
		body.stagger_tween.kill()
	body.sprite.rotation = 0.0
	body.state_anim = &"dismount_daze"
	body.play_anim(&"dismount_daze")
	# Sat on the mat: his hurtbox his daze sheet's body, not his standing one.
	var box = body.anchor(&"body_box")
	if box != null:
		body.set_body_box(box)
	body.taunt_sfx_player.play()
	hurtbox.set_deferred("monitoring", true)
	hurtbox.set_deferred("monitorable", true)
	elapsed = 0.0


func Exit() -> void:
	hurtbox.set_deferred("monitoring", false)
	hurtbox.set_deferred("monitorable", false)
	body.restore_body_box()


func Physics_Update(delta: float) -> void:
	elapsed += delta
	if elapsed >= window:
		state_machine.on_child_transition(self, "Remount")
