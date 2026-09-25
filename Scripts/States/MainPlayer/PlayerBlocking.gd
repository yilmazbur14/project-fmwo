extends State

# The guard. PlayerScript still moves the player while it's up, at block_move_speed_ratio. With
# blocking switched off (PlayerDefense.BLOCKING_ENABLED) it is only the parry's stance, and drops once
# the press's parry window is over even with the key still held.

@export var blocking_animation : String = "blocking"
@export var animation_player : AnimationPlayer

var player : Node
var defense : Node

func _ready() -> void:
	player = get_parent().get_parent()
	animation_player = player.get_node("AnimationPlayer")
	defense = player.get_node("Defense")

func Enter() -> void:
	animation_player.play(blocking_animation)
	defense.on_guard_raised()

func Exit() -> void:
	defense.on_guard_lowered()

func Update(delta: float) -> void:
	# Exit block when button is released
	if !Input.is_action_pressed("block") or not defense.can_raise_guard() or not defense.guard_holds():
		get_parent().on_child_transition(self, "Idle")
		return