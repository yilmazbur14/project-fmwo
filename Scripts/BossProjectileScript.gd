extends Area2D


# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	$DespawnTimer.start()


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	position += Vector2.DOWN * 500 * delta


func _on_despawn_timer_timeout() -> void:
	queue_free()


func _on_body_entered(body: Node2D) -> void:
	#do damage TODO
	queue_free()

