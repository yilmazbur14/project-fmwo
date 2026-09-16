extends State


@export var earthquake_animation : String = "earthquake"
# @export var speed_threshold : float = 0.1
@export var animation_player : AnimationPlayer
var EarthquakeAreas = preload("res://Scenes/Bosses/EarthquakeAreasScene.tscn")

#FIGHTING GAME NUMPAD NOTATIONS FOR DIRECTIONS
@export var earthquake_collision_4: Area2D
@export var earthquake_collision_1: Area2D
@export var earthquake_collision_2: Area2D
@export var earthquake_collision_3: Area2D
@export var earthquake_collision_6: Area2D
@export var move_speed : float = 100.0

# @export var post_dialogue_pre_fight_timer: Timer

func Enter() -> void:
	# Ramp up intensity as Eric's health drops - the fight gets faster near the end.
	var ratio := 1.0
	var boss = get_tree().current_scene.get_node_or_null("Arena/EricBossScene/CharacterBody2D")
	if boss and boss.has_method("get_health_ratio"):
		ratio = boss.get_health_ratio()
	var low_end = lerp(1.5, 2.3, 1.0 - ratio)
	var high_end = lerp(3.5, 5.0, 1.0 - ratio)
	animation_player.speed_scale = randf_range(low_end, high_end)
	animation_player.play(earthquake_animation)

func Exit() -> void:
	animation_player.speed_scale = 1.0  # Reset back to normal for other animations

func Physics_Update(_delta: float):
	pass

func enable_hitbox():
	# print("Enabling hitbox")
	var spawned_earthquake_areas = EarthquakeAreas.instantiate()
	# print("tree current scene:", get_tree().current_scene.get_node("Arena/MainPlayer/CharacterBody2D"))
	var boss = get_tree().current_scene.get_node("Arena/EricBossScene/CharacterBody2D")
	boss.add_child(spawned_earthquake_areas)
	spawned_earthquake_areas.enable_earthquake_areas()

	var sfx = boss.get_node_or_null("EarthquakeSfxPlayer")
	if sfx:
		if not sfx.stream:
			sfx.stream = load("res://Assets/Audio/SFX/earthquake_slam.ogg")
		sfx.play()

