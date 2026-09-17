extends Node2D

signal arrived
signal delivered

const WALK_SPEED := 380.0

@export var sprite: Sprite2D
@export var animation_player: AnimationPlayer
@export var handoff_timer: Timer
@export var arrive_sfx: AudioStreamPlayer

var exit_x := 0.0


func _ready() -> void:
	handoff_timer.timeout.connect(_on_handoff_timer_timeout)


func begin_delivery(start: Vector2, stop: Vector2, exit: Vector2) -> void:
	global_position = start
	exit_x = exit.x
	_walk_to(stop.x).tween_callback(_on_reached_stop)


func _walk_to(target_x: float) -> Tween:
	sprite.flip_h = target_x < global_position.x
	animation_player.play("walk")
	var tween := create_tween()
	tween.tween_property(self, "global_position:x", target_x, absf(target_x - global_position.x) / WALK_SPEED)
	return tween


func _on_reached_stop() -> void:
	arrived.emit()
	arrive_sfx.play()
	animation_player.play("deliver")
	handoff_timer.start()


func _on_handoff_timer_timeout() -> void:
	delivered.emit()
	_walk_to(exit_x).tween_callback(queue_free)
