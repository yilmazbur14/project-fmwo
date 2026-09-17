extends State

# The frames right after a dash, where the player can't move, punch or dash. PlayerDefense times them
# and a parry cuts them short; the guard may still go up, which leaves this state for Blocking.
# There's no drawn recovery pose yet, so he holds a crouched walk frame leaned back along the dash.

const DefenseHypeArtLayout := preload("res://Scripts/DefenseHypeArtLayout.gd")

@export var animation_player : AnimationPlayer
@export var player : CharacterBody2D

var defense : Node
var saved_offset := Vector2.ZERO


func _ready() -> void:
	defense = player.get_node("Defense")


func Enter() -> void:
	animation_player.stop()
	var sprite: Sprite2D = player.sprite
	saved_offset = sprite.offset
	var pose := DefenseHypeArtLayout.DASH_RECOVERY_POSE
	sprite.frame_coords = Vector2i(pose.frame, player.facing)
	sprite.offset = saved_offset - player.direction.normalized().round() * pose.lean_texels


func Exit() -> void:
	player.sprite.offset = saved_offset


func Update(_delta: float) -> void:
	if not defense.is_dash_recovering():
		get_parent().on_child_transition(self, "Idle")


func Physics_Update(_delta: float) -> void:
	player.velocity = Vector2.ZERO
