extends State

const BixbyBeastArtLayout := preload("res://Scripts/BixbyBeastArtLayout.gd")

@export var body : CharacterBody2D
@export var recover_timer : Timer
@export var recover_sfx_player : AudioStreamPlayer

@onready var state_machine = get_parent()

# Placeholder exhaustion, until bixby_beast_recover.png: the hover frame on the ground, darkened, heaving
# by a texel.
const PLACEHOLDER_TINT := Color(0.78, 0.74, 0.74)
const PLACEHOLDER_HEAVE_PX := 3.0
const PLACEHOLDER_HEAVE_TIME := 0.45

var elapsed := 0.0


# The punish window.
func Enter() -> void:
	body.hits_this_window = 0
	body.daze_used = false
	body.play_anim(&"recover")
	body.set_hurtbox_active(true)
	recover_sfx_player.play()
	recover_timer.start(state_machine.recover_time)
	elapsed = 0.0
	if not BixbyBeastArtLayout.uses_final(&"recover"):
		body.air.modulate = PLACEHOLDER_TINT


func Exit() -> void:
	body.set_hurtbox_active(false)
	body.air.modulate = Color.WHITE
	body.bob = 0.0
	body.place()


func Physics_Update(delta: float) -> void:
	if BixbyBeastArtLayout.uses_final(&"recover"):
		return
	elapsed += delta
	body.bob = PLACEHOLDER_HEAVE_PX if int(elapsed / PLACEHOLDER_HEAVE_TIME) % 2 == 1 else 0.0
	body.place()


func flinch() -> void:
	body.play_anim(&"hit", &"recover")


func _on_recover_timer_timeout() -> void:
	state_machine.on_child_transition(self, "Takeoff")
