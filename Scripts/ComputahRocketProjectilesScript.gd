extends Node2D

var velocityUp : Vector2 = Vector2.UP * 800
var velocityDown : Vector2 = Vector2.DOWN * 800
var direction = "up"
# var computah_player : CharacterBody2D
var main_player : CharacterBody2D
var tracking_speed = 600.0

@export var animationPlayer : AnimationPlayer
@export var explode_timer : Timer
@export var reverse_rocket_direction_timer : Timer
@export var rocket_hitbox : Area2D
@export var rocket_hitbox_shape : CollisionShape2D

# Called when the node enters the scene tree for the first time.
func _ready() -> void:

	animationPlayer.speed_scale = 2
	animationPlayer.animation_finished.connect(_on_animation_player_animation_finished)
	main_player = get_tree().current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
	reverse_rocket_direction_timer.start()


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _physics_process(delta: float) -> void:
	if direction == "up":
		position += velocityUp * delta
	elif direction == "down":
		var direction_to_player = (main_player.global_position - global_position).normalized()
		position += direction_to_player * tracking_speed * delta

		# Check if close enough to player to explode
		if global_position.distance_to(main_player.global_position) < 300:
			print("Exploding on player!")
			explode_timer.stop()
			animationPlayer.play("explode")

func rocket_down() -> void:
	explode_timer.start()
	direction = "down"


func _on_explode_timer_timeout() -> void:
	animationPlayer.play("explode")

func _on_animation_player_animation_finished(anim_name: String) -> void:
	if anim_name == "explode":
		queue_free()

func _on_reverse_rocket_direction_timer_timeout() -> void:
	rocket_down()

func enable_explode_hitbox() -> void:
	rocket_hitbox_shape.disabled = false
	rocket_hitbox.scale = Vector2(2, 2)
