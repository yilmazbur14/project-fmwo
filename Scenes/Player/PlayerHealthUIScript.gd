extends Control

@export var heart_containers_ui : Array[TextureRect]
@export var full_heart : Texture2D
@export var half_heart : Texture2D
@export var empty_heart : Texture2D



# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	pass # Replace with function body.


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	pass

func update_health(current_health: int) -> void:
	if current_health == 6:
		heart_containers_ui[0].texture = full_heart
		heart_containers_ui[1].texture = full_heart
		heart_containers_ui[2].texture = full_heart
	elif current_health == 5:
		heart_containers_ui[0].texture = full_heart
		heart_containers_ui[1].texture = full_heart
		heart_containers_ui[2].texture = half_heart
	elif current_health == 4:
		heart_containers_ui[0].texture = full_heart
		heart_containers_ui[1].texture = full_heart
		heart_containers_ui[2].texture = empty_heart
	elif current_health == 3:
		heart_containers_ui[0].texture = full_heart
		heart_containers_ui[1].texture = half_heart
		heart_containers_ui[2].texture = empty_heart
	elif current_health == 2:
		heart_containers_ui[0].texture = full_heart
		heart_containers_ui[1].texture = empty_heart
		heart_containers_ui[2].texture = empty_heart
	elif current_health == 1:
		heart_containers_ui[0].texture = half_heart
		heart_containers_ui[1].texture = empty_heart
		heart_containers_ui[2].texture = empty_heart
	elif current_health == 0:
		for heart in heart_containers_ui:
			heart.texture = empty_heart

