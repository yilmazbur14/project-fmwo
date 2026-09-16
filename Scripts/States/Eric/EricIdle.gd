extends State

@export var animation_player : AnimationPlayer
@export var post_dialogue_pre_fight_timer: Timer
@export var pause_between_earthquakes_timer: Timer
var start_pause_between_earthquakes_timer = false
@export var EricStateMachine: Node
@export var hurtbox : Area2D


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	pass

func Enter() -> void:
	# DialogueManager.show_dialogue_balloon(load("res://Dialogue/EricPreFight.dialogue"), "start")
	# DialogueManager.dialogue_ended.connect(_on_dialogue_ended)
	# if start_pause_between_earthquakes_timer:
	# 	# print("Starting pause between earthquakes timer")
	# 	pause_between_earthquakes_timer.start()
	animation_player.play("idle")
	hurtbox.monitoring = false
	hurtbox.monitorable = false

# func Exit() -> void:
# 	pause_between_earthquakes_timer.stop()

# func _on_dialogue_ended(dialogue: Object) -> void:
# 	print("timer", post_dialogue_pre_fight_timer)
# 	post_dialogue_pre_fight_timer.start()
# 	pass


# func _on_post_dialogue_pre_fight_timer_timeout() -> void:
# 	print("timer done")
# 	start_pause_between_earthquakes_timer = true
# 	# get_parent().on_child_transition(self, "Earthquake")
# 	EricStateMachine.loop_earthquake_cycle()
