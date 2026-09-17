extends State

# Eric throws his sword at where the player stands. It sticks in the ground and sends out an
# earthquake ring, then flies back to his hand.

@export var animation_player : AnimationPlayer
@export var character_body : CharacterBody2D
@export var eric_state_machine : Node

# Sword speed in px/s both ways, ring growth in px/s and how long the sword stays planted before
# he recalls it, at full health and at none.
@export var flight_speed := 1400.0
@export var rage_flight_speed := 1700.0
@export var ring_speed := 950.0
@export var rage_ring_speed := 1200.0
@export var planted_time := 0.7
@export var rage_planted_time := 0.45

const SWORD_SCENE := preload("res://Scenes/Bosses/EricThrownSwordScene.tscn")
const IMPACT_SCENE := preload("res://Scenes/Bosses/EricQuakeImpactScene.tscn")
const RING_SCENE := preload("res://Scenes/Bosses/EricQuakeRingScene.tscn")
const EricArtLayout := preload("res://Scripts/EricArtLayout.gd")

@onready var player = get_tree().current_scene.get_node("Arena/MainPlayer/CharacterBody2D")

var sword: Node2D
var planted_left := -1.0


func Enter() -> void:
	planted_left = -1.0
	animation_player.play("throw_windup")


func Exit() -> void:
	planted_left = -1.0
	if is_instance_valid(sword):
		sword.queue_free()
	sword = null


func Physics_Update(delta: float) -> void:
	if planted_left < 0.0:
		return
	planted_left -= delta
	if planted_left <= 0.0:
		planted_left = -1.0
		animation_player.play("recall_reach")
		var flipped: bool = character_body.sprite.flip_h
		var lean := deg_to_rad(EricArtLayout.THROW_CATCH_ANGLE)
		var catch_centre: Vector2 = character_body.to_global(EricArtLayout.frame_local(EricArtLayout.THROW_CATCH_CENTRE, flipped))
		sword.recall(catch_centre, _ground_y(), -lean if flipped else lean, not flipped)
		_play_whoosh()


func _ground_y() -> float:
	return character_body.frame_point(Vector2(0, EricArtLayout.FEET_ROW)).y


# Called by the throw_release animation on frame 35: frame 34 still draws the sword leaving his
# hands.
func release_sword() -> void:
	var rage: float = eric_state_machine.rage
	sword = SWORD_SCENE.instantiate()
	sword.speed = lerpf(flight_speed, rage_flight_speed, rage)
	sword.landed.connect(_on_sword_landed)
	sword.returned.connect(_on_sword_returned)
	var hand: Vector2 = character_body.frame_point(EricArtLayout.THROW_RELEASE_PIXEL)
	eric_state_machine.add_hazard(sword, Vector2(hand.x, _ground_y()))
	sword.throw(hand, _ground_y(), player.global_position)
	_play_whoosh()


func _on_sword_landed() -> void:
	var rage: float = eric_state_machine.rage
	var contact: Vector2 = sword.global_position
	eric_state_machine.add_hazard(IMPACT_SCENE.instantiate(), contact)
	var ring = RING_SCENE.instantiate()
	ring.speed = lerpf(ring_speed, rage_ring_speed, rage)
	ring.player = player
	eric_state_machine.add_hazard(ring, contact)
	planted_left = lerpf(planted_time, rage_planted_time, rage)

	var sfx = character_body.get_node_or_null("EarthquakeSfxPlayer")
	if sfx:
		if not sfx.stream:
			sfx.stream = load("res://Assets/Audio/SFX/earthquake_slam.ogg")
		sfx.play()


func _on_sword_returned() -> void:
	sword.queue_free()
	sword = null
	animation_player.play("recall_catch")


func _play_whoosh() -> void:
	var sfx = character_body.get_node_or_null("WhirlwindSfxPlayer")
	if sfx:
		if not sfx.stream:
			sfx.stream = load("res://Assets/Audio/SFX/whirlwind_whoosh.ogg")
		sfx.play()


func _on_animation_player_animation_finished(anim_name: StringName) -> void:
	if eric_state_machine.current_state != self:
		return
	match anim_name:
		&"throw_windup":
			animation_player.play("throw_release")
		&"throw_release":
			animation_player.play("empty_wait")
		&"recall_catch":
			eric_state_machine.attack_finished()
