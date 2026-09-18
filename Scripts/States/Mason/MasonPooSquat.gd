extends State

@export var animation_player : AnimationPlayer
@export var squat_sfx_player : AudioStreamPlayer
@export var squat_timer : Timer
@export var release_timer : Timer

# How long he holds the squat before the bomb drops, and the beat after it before he sets off.
@export var squat_hold := 0.3
@export var release_hold := 0.14

# The authored length of the "poop" animation, which is played at whatever speed fits the squat, so
# every frame of it still shows however fast the line is meant to come out.
const POOP_ANIMATION_TIME := 0.75

@onready var state_machine = get_parent()


func Enter() -> void:
	state_machine.begin_line()
	animation_player.play("poop", -1, POOP_ANIMATION_TIME / maxf(squat_hold + release_hold, 0.01))
	squat_sfx_player.play()
	squat_timer.start(squat_hold)


func _on_squat_timer_timeout() -> void:
	state_machine.drop_bomb()
	release_timer.start(release_hold)


func _on_release_timer_timeout() -> void:
	state_machine.on_child_transition(self, "Waddle")
