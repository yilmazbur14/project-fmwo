extends State

@export var animation_player : AnimationPlayer
@export var phone_sfx_player : AudioStreamPlayer
@export var phone_timer : Timer
@export var body : CharacterBody2D

const CARTER_ELBOW_DROP_SCENE := "res://Scenes/Bosses/CarterElbowDropScene.tscn"
const PHONE_DURATION := 1.2
const ELBOW_DROPS := 3
# Keeps the marker inside the ropes, and Carter's landed pose (147px tall) below the back rope,
# clear of the crowd and the health bar.
const ELBOW_BOUNDS := Rect2(181, 260, 1555, 640)
# Everything Carter draws around his landing spot (pose, dust burst, marker), and Mason's sprite
# around his origin. A landing whose footprint touches Mason's sprite is kept away from him.
const CARTER_FOOTPRINT := Rect2(-90, -147, 200, 201)
const MASON_SPRITE := Rect2(-93, -93, 186, 189)

@onready var state_machine = get_parent()


func Enter() -> void:
	animation_player.play("phone")
	phone_sfx_player.play()
	phone_timer.start(PHONE_DURATION)


func _on_phone_timer_timeout() -> void:
	animation_player.play("idle")

	var player = state_machine.get_player()
	if not player:
		state_machine.on_child_transition(self, "AwaitDelivery")
		return

	var keep_out := Rect2(
		body.global_position + MASON_SPRITE.position - CARTER_FOOTPRINT.end,
		MASON_SPRITE.size + CARTER_FOOTPRINT.size
	)
	var carter = state_machine.spawn_hazard(CARTER_ELBOW_DROP_SCENE, player.global_position)
	carter.finished.connect(_on_carter_finished)
	carter.begin(ELBOW_DROPS, player, ELBOW_BOUNDS, keep_out)


func _on_carter_finished() -> void:
	state_machine.on_child_transition(self, "AwaitDelivery")
