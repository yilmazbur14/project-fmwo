extends State

@export var animation_player : AnimationPlayer
@export var squat_sfx_player : AudioStreamPlayer
@export var squat_timer : Timer
@export var release_timer : Timer

const SQUAT_HOLD := 0.5
const RELEASE_HOLD := 0.25

@onready var state_machine = get_parent()


func Enter() -> void:
	state_machine.begin_line()
	animation_player.play("poop")
	squat_sfx_player.play()
	squat_timer.start(SQUAT_HOLD)


func _on_squat_timer_timeout() -> void:
	state_machine.drop_bomb()
	release_timer.start(RELEASE_HOLD)


func _on_release_timer_timeout() -> void:
	state_machine.on_child_transition(self, "Waddle")
