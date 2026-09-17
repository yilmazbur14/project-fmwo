extends State

@export var animation_player : AnimationPlayer
@export var rocket_volley : State

# A rocket that never reaches the player frees itself 4.5s after launch (1s climb, 3s fuse,
# 0.5s explosion), and the last volley launches just before this state starts. So this cap only
# removes rockets that got stuck, instead of popping ones still on their way, and the loop can't stall.
const MAX_WAIT := 4.5

var elapsed := 0.0

@onready var state_machine = get_parent()


func Enter() -> void:
	animation_player.play("idle")
	elapsed = 0.0


# The ground pound only starts once every rocket is gone, so none can still be flying while
# the shockwave expands or the mech is overheated. Removed stragglers are only gone a frame
# after queue_free, so the check runs again next frame rather than transitioning straight away.
func Physics_Update(delta: float) -> void:
	if rocket_volley.rockets_cleared():
		state_machine.on_child_transition(self, "GroundPound")
		return
	elapsed += delta
	if elapsed >= MAX_WAIT:
		rocket_volley.clear_rockets()
