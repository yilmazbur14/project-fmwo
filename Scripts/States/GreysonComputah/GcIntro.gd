extends State

# The pair boot up in their corners and the dialogue runs. Every wait is a node-bound tween, so a
# freeze holds it.

@export var greyson : CharacterBody2D
@export var computah : CharacterBody2D

@onready var state_machine = get_parent()

const BOOT_BEAT := 0.5
const BEAT_AFTER := 0.4


func Enter() -> void:
	greyson.global_position = state_machine.GREYSON_HOME
	computah.global_position = state_machine.COMPUTAH_HOME
	greyson.set_facing(true)
	computah.set_facing(false)
	greyson.play_anim(&"idle")
	computah.set_charge_state(0)
	computah.play_anim(&"idle")
	_play()


# The dialogue is handed over by the machine on the first frame; this is only the pose under it.
func _play() -> void:
	get_tree().call_group("arena_crowd", "hush")
	await _pause(BOOT_BEAT)
	greyson.play_anim(&"taunt")
	await _pause(BEAT_AFTER)
	greyson.play_anim(&"idle")


func _pause(seconds: float) -> void:
	var tween := create_tween()
	tween.tween_interval(seconds)
	await tween.finished
