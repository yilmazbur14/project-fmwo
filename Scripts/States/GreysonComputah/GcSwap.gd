extends State

# THE SWAP: one of them has gone down, and the other becomes phase two. How strong that phase is is
# exactly the health the survivor had left when it happened - GreysonComputahScript latches it as
# `power` at the kill - so a player who spread their damage meets a weak second phase and one who
# tunnelled on a single body meets a monster. NOTHING HEALS AT THE SWAP, EVER.
#
# The beat itself: a hit-stop and a shake on the kill, the music ducking, the dying body playing its
# defeat where it stands, the survivor raging through it. Its defeat holds on its last frame, and
# that frame is the hand-over: the survivor snaps to its phase-two idle, the overcharge aura comes
# on, and the cycle starts again.
# Neither of them is punchable or dangerous for the whole beat.
#
# FREEZE SAFETY: the beat is a Physics_Update accumulator and the music duck is node-bound.

const HitStop := preload("res://Scripts/HitStop.gd")
const Layout := preload("res://Scripts/GreysonComputahArtLayout.gd")

@export var greyson : CharacterBody2D
@export var computah : CharacterBody2D
@export var swap_sfx_player : AudioStreamPlayer

@onready var state_machine = get_parent()

# Set by GcStateMachine.enter_swap() before the transition.
var dead_body: Node = null

const BEAT := 2.0
const KILL_HIT_STOP := 0.35
const KILL_SHAKE := 24.0
const KILL_SHAKE_STEPS := 8
const KILL_SHAKE_STEP_TIME := 0.035
const MUSIC_DUCK_DB := -9.0
const MUSIC_DUCK_TIME := 0.25
const MUSIC_BACK_TIME := 0.5

var clock := 0.0
var handed_over := false


func Enter() -> void:
	clock = 0.0
	handed_over = false
	var survivor: Node = state_machine.fight.other_body(dead_body)

	for body in state_machine.fight.bodies():
		body.velocity = Vector2.ZERO
		body.set_hurtbox_active(false)
		body.show_aura(false)
	computah.set_grab_active(false)
	computah.show_battery(false)
	computah.set_solid(false)
	_set_targetable(dead_body, false)
	_set_targetable(survivor, true)

	dead_body.play_anim(&"defeat")
	survivor.play_anim(&"rage")

	HitStop.freeze(get_tree(), KILL_HIT_STOP)
	survivor.shake_screen(KILL_SHAKE, KILL_SHAKE_STEPS, KILL_SHAKE_STEP_TIME)
	state_machine.fight.duck_music(MUSIC_DUCK_DB, MUSIC_DUCK_TIME)
	get_tree().call_group("arena_crowd", "cheer", 1.5)
	swap_sfx_player.play()


func Exit() -> void:
	state_machine.fight.restore_music(MUSIC_BACK_TIME)


func Physics_Update(delta: float) -> void:
	clock += delta
	if not handed_over and clock >= _defeat_hold():
		_hand_over()
	if clock >= BEAT:
		state_machine.start_cycle()


# The dying body's defeat holds on its last frame; that frame is what the survivor's phase-two idle
# is drawn to cut from.
func _defeat_hold() -> float:
	var anim: Dictionary = Layout.computah_anim(&"defeat") if dead_body == computah \
		else Layout.greyson_anim(&"defeat")
	return Layout.time_to_step(anim, anim.frames.size() - 1)


func _hand_over() -> void:
	handed_over = true
	var survivor: Node = state_machine.fight.other_body(dead_body)
	survivor.play_anim(&"phase2_idle")
	survivor.show_aura(true)
	if survivor == computah:
		computah.set_solid(true)
		computah.set_charge_state(0)


func _set_targetable(body: Node, on: bool) -> void:
	if body.has_method("set_target_active"):
		body.set_target_active(on)
