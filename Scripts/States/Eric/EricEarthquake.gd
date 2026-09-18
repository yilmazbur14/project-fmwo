extends State


@export var earthquake_animation : String = "earthquake"
@export var recover_animation : String = "recover"
@export var animation_player : AnimationPlayer
@export var character_body : CharacterBody2D
@export var eric_state_machine : Node
var EarthquakeAreas = preload("res://Scenes/Bosses/EarthquakeAreasScene.tscn")
const EricArtLayout := preload("res://Scripts/EricArtLayout.gd")

# Slams per attack, at full health and at none.
@export var slams := 2
@export var rage_slams := 3
@export var animation_speed := 1.6
# Capped so the raised sword is up long enough to be read: his waves radiate from where he stands,
# so anyone in the slam is hit with no travel at all and the animation is the only warning they get.
# `earthquake` calls enable_hitbox 0.667 s in, which at 1.85x leaves 0.36 s of wind-up, comfortably
# past PlayerDefense.parry_window. Raising this back toward 2.1 takes that below it.
@export var rage_animation_speed := 1.85
# On-screen projectile speed in px/s.
@export var projectile_speed := 1150.0
@export var rage_projectile_speed := 1400.0

var slams_left := 0
var projectile_speed_now := 0.0
# Slams alternate patterns, carrying on from one attack to the next.
var tilted_next := false

func Enter() -> void:
	var rage: float = eric_state_machine.rage
	slams_left = roundi(lerpf(slams, rage_slams, rage))
	projectile_speed_now = lerpf(projectile_speed, rage_projectile_speed, rage)
	animation_player.speed_scale = lerpf(animation_speed, rage_animation_speed, rage)
	animation_player.play(earthquake_animation)

func Exit() -> void:
	animation_player.speed_scale = 1.0  # Reset back to normal for other animations

# Called by the earthquake animation on frame 7.
func enable_hitbox():
	var spawned_earthquake_areas = EarthquakeAreas.instantiate()
	spawned_earthquake_areas.tilted = tilted_next
	tilted_next = not tilted_next
	# The art is drawn at Eric's scale, one texel per hitbox unit.
	spawned_earthquake_areas.scale = character_body.scale
	spawned_earthquake_areas.move_speed = projectile_speed_now / character_body.scale.x
	eric_state_machine.add_hazard(spawned_earthquake_areas, character_body.frame_point(EricArtLayout.SLAM_PIXEL))
	spawned_earthquake_areas.enable_earthquake_areas()

	var sfx = character_body.get_node_or_null("EarthquakeSfxPlayer")
	if sfx:
		if not sfx.stream:
			sfx.stream = load("res://Assets/Audio/SFX/earthquake_slam.ogg")
		sfx.play()

func _on_animation_player_animation_finished(anim_name: StringName) -> void:
	if eric_state_machine.current_state != self:
		return
	if anim_name == earthquake_animation:
		animation_player.play(recover_animation)
	elif anim_name == recover_animation:
		slams_left -= 1
		if slams_left > 0:
			animation_player.play(earthquake_animation)
		else:
			eric_state_machine.attack_finished()
