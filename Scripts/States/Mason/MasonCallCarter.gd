extends State

@export var animation_player : AnimationPlayer
@export var phone_sfx_player : AudioStreamPlayer
@export var phone_timer : Timer

const CARTER_ELBOW_DROP_SCENE := "res://Scenes/Bosses/CarterElbowDropScene.tscn"
const PHONE_DURATION := 1.2
const ELBOW_DROPS := 3
const ELBOW_BOUNDS := Rect2(180, 180, 1560, 720)

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

	var carter = state_machine.spawn_hazard(CARTER_ELBOW_DROP_SCENE, player.global_position)
	carter.finished.connect(_on_carter_finished)
	carter.begin(ELBOW_DROPS, player, ELBOW_BOUNDS)


func _on_carter_finished() -> void:
	state_machine.on_child_transition(self, "AwaitDelivery")
