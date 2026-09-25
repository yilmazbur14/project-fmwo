extends State

# After the last Trueshot he teleports home to the middle of the ring and stands there spent - one hand
# up, "hold on" - and NOT punchable. It lasts at least spent_min and until nothing he fired is still
# flying, up to spent_max; a bolt still going then fizzles where it is. This is R3: the window, and the
# yell inside it, never open while a projectile is alive.

@export var body : CharacterBody2D

@onready var state_machine = get_parent()

enum Beat { OUT, IN, WAIT }

var beat := Beat.OUT
var beat_clock := 0.0
# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
# How long the last wait lasted and whether it hit the cap, for a test.
var waited := 0.0
var capped := false


func Enter() -> void:
	released = false
	beat = Beat.OUT
	beat_clock = 0.0
	waited = 0.0
	capped = false
	body.velocity = Vector2.ZERO
	body.set_hurtbox_active(false)
	body.teleport_out()


func Exit() -> void:
	release()


func release() -> void:
	if released:
		return
	released = true
	if is_instance_valid(body):
		body.restore_hud()


func Physics_Update(delta: float) -> void:
	beat_clock += delta
	match beat:
		Beat.OUT:
			if beat_clock >= state_machine.teleport_out:
				beat = Beat.IN
				beat_clock = 0.0
				body.teleport_in(state_machine.HOME)
				body.update_hud_fade(&"spent")
		Beat.IN:
			if beat_clock >= state_machine.teleport_in:
				beat = Beat.WAIT
				beat_clock = 0.0
				body.play_state_anim(&"spent")
		Beat.WAIT:
			var clear: bool = state_machine.live_projectiles().is_empty()
			if beat_clock >= state_machine.spent_min and clear:
				_open_window()
			elif beat_clock >= state_machine.spent_max:
				capped = true
				for bolt in state_machine.live_bolts():
					bolt.fizzle()
				for wave in state_machine.live_waves():
					wave.queue_free()
				_open_window()


func _open_window() -> void:
	waited = beat_clock
	state_machine.on_child_transition(self, "Recover")
