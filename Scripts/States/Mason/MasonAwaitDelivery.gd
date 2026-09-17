extends State

@export var animation_player : AnimationPlayer
@export var body : CharacterBody2D

const UBER_DRIVER_SCENE := "res://Scenes/Bosses/UberDriverScene.tscn"
const DRIVER_OFFSCREEN_LEFT := -100.0
const DRIVER_OFFSCREEN_RIGHT := 2020.0
const DRIVER_STOP_GAP := 120.0

@onready var state_machine = get_parent()

var driver_called := false


func Enter() -> void:
	animation_player.play("idle")
	driver_called = false


# The driver only sets off once every bomb is gone, so no explosion can still be live
# when the eat window opens, however short his walk turns out to be.
func Update(_delta: float) -> void:
	if driver_called or not state_machine.bombs_cleared():
		return
	driver_called = true

	var x := body.global_position.x
	var y := body.global_position.y
	var start := Vector2(DRIVER_OFFSCREEN_LEFT, y)
	var stop := Vector2(x - DRIVER_STOP_GAP, y)
	if x >= 960:
		start = Vector2(DRIVER_OFFSCREEN_RIGHT, y)
		stop = Vector2(x + DRIVER_STOP_GAP, y)

	var driver = state_machine.spawn_hazard(UBER_DRIVER_SCENE, start)
	driver.delivered.connect(_on_driver_delivered)
	driver.begin_delivery(start, stop, start)


func _on_driver_delivered() -> void:
	state_machine.on_child_transition(self, "Eat")
